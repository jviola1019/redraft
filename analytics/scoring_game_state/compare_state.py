"""Rolling-origin NFL score simulation with clock- and margin-conditioned credits."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.special import expit, ndtri

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from scoring_possessions import compare as prior
from scoring_possessions.compare import historical, scores

CLOCK_COLUMN = "game_seconds_remaining"
BOOTSTRAP_METRICS = (("joint", "energy"), ("total", "crps"), ("margin", "crps"),
                     ("shutouts", "brier"), ("total", "coverage"), ("margin", "coverage"))


def game_drives(plays, game):
    plays = plays.sort_values("play_id", kind="stable").reset_index(drop=True)
    score_cols = ["total_home_score", "total_away_score"]
    plays[score_cols] = plays[score_cols].ffill().fillna(0)
    if tuple(plays[score_cols].iloc[-1]) != (game.home_score, game.away_score):
        return None, "final_score_mismatch"
    for key in ("fixed_drive", "qtr"):
        plays[key] = plays[key].ffill().bfill()
    if plays[["fixed_drive", "qtr"]].isna().any(axis=None):
        return None, "missing_drive_or_quarter"
    previous = np.zeros(2, dtype=int)
    rows = []
    for (_, overtime), segment in plays.groupby(["fixed_drive", plays.qtr.gt(4)], sort=False):
        end = segment[score_cols].iloc[-1].to_numpy(dtype=int)
        credit = end - previous
        previous = end
        if (credit < 0).any():
            return None, "nonmonotone_score"
        if overtime:
            continue
        teams = segment.posteam.replace(scores.ALIASES)
        valid = teams.isin((game.home_team, game.away_team))
        anchors = teams[valid & segment.play_type.isin(prior.DRIVE_PLAYS)]
        if anchors.empty:
            anchors = teams[valid]
        if anchors.empty:
            if credit.any():
                return None, "scoring_segment_without_team"
            continue
        side = int(anchors.iloc[0] == game.away_team)
        anchor = segment.loc[anchors.index[0]]
        clock = anchor[CLOCK_COLUMN]
        if pd.isna(clock) or not 0 <= clock <= 3600 or (rows and clock > rows[-1][2]):
            return None, "invalid_clock"
        period = int(clock <= 600) + int(anchor.qtr >= 3)
        rows.append((side, period, int(clock), int(credit[side]), int(credit[1 - side])))
    if {row[0] for row in rows} != {0, 1}:
        return None, "missing_possession_side"
    return rows, None


def read_drives(games, directory, years):
    audits, history = {}, {}
    for year in years:
        path = directory / f"{year}.parquet"
        plays = pd.read_parquet(path, columns=[*prior.COLUMNS, CLOCK_COLUMN])
        schedule = games.loc[games.season.eq(year)]
        by_game = plays[plays.season_type.eq("REG")].groupby("game_id", sort=False)
        rejects, valid = Counter(), []
        for game in schedule.itertuples():
            if game.game_id not in by_game.indices:
                rejects["missing_game"] += 1
                continue
            rows, reason = game_drives(by_game.get_group(game.game_id), game)
            if reason:
                rejects[reason] += 1
            else:
                valid.append(rows)
        history[year] = valid
        audits[year] = {
            "url": prior.SOURCE_URL.format(year), "sha256": scores.sha(path), "bytes": path.stat().st_size,
            "scheduled": len(schedule), "valid": len(valid), "losses": dict(rejects),
        }
        print(f"Read {year}: {len(valid)}/{len(schedule)} valid", flush=True)
    return history, audits


def state_index(period, differential):
    return 3 * period + 1 + (differential >= 8).astype(int) - (differential <= -8)


def fit_state(history, year):
    training = [game for season in range(year - 3, year) for game in history[season]]
    templates = np.full((len(training), max(map(len, training)), 2), -1, dtype=int)
    outcomes = [[], []]
    pace = []
    for index, game in enumerate(training):
        score, counts = np.zeros(2, dtype=int), np.zeros(2, dtype=int)
        for step, (side, period, _, own, opponent) in enumerate(game):
            templates[index, step] = side, period
            state = state_index(period, score[side] - score[1 - side])
            outcomes[side].append((state, own, opponent))
            counts[side] += 1
            score[side] += own
            score[1 - side] += opponent
        pace.append(counts)
    laws = []
    for rows in outcomes:
        rows = np.asarray(rows)
        categories, index, counts = np.unique(rows[:, 1:], axis=0, return_inverse=True, return_counts=True)
        base = counts / counts.sum()
        cells = np.zeros((9, len(categories)))
        np.add.at(cells, (rows[:, 0], index), 1)
        state_count = cells.sum(axis=1)
        state_mass = (cells + 100 * base) / (state_count[:, None] + 100)
        laws.append((categories, base, state_mass, state_count))
    return templates, np.asarray(pace), laws


def state_cdfs(law, target):
    categories, base, state_mass, _ = law
    tilted = prior.tilt(categories, base, target)
    # Dividing out the unconditional mass transfers the same exponential tilt to each cell.
    mass = tilted[:, None, :] * (state_mass / base)[None, :, :]
    return np.cumsum(mass / mass.sum(axis=2, keepdims=True), axis=2)[:, :, :-1]


def simulate(templates, laws, targets, rng):
    draws = len(templates)
    cdfs = [state_cdfs(law, target) for law, target in zip(laws, targets)]
    uniforms = rng.random(templates.shape[:2])
    run = np.arange(draws)
    points = np.zeros((draws, 2), dtype=int)
    for step, (sides, periods) in enumerate(templates.transpose(1, 2, 0)):
        for side, (law, cdf) in enumerate(zip(laws, cdfs)):
            idx = run[sides == side]
            state = state_index(periods[idx], points[idx, side] - points[idx, 1 - side])
            category = (uniforms[idx, step, None] > cdf[idx, state]).sum(axis=1)
            credit = law[0][category]
            points[idx, side] += credit[:, 0]
            points[idx, 1 - side] += credit[:, 1]
    return points.T


def joint_draw(schedule, year, law, model, draws):
    rng = np.random.default_rng(np.random.SeedSequence([historical.SEED, year]))
    rng_state = np.random.default_rng(np.random.SeedSequence([historical.SEED, year, 9353]))
    teams = sorted(set(schedule.home_team) | set(schedule.away_team))
    team_index = {team: index for index, team in enumerate(teams)}
    shock = rng.normal(0, law["seasonShockSd"], size=(len(teams), draws))
    templates, pace, laws = model
    mean_pace = pace.mean(axis=0)
    opposite = [mean_pace[j] * np.dot(laws[j][0][:, 1], laws[j][1]) for j in (0, 1)]
    for game, expected in zip(schedule.itertuples(), scores.expected_margin(schedule, law)):
        hi, ai = team_index[game.home_team], team_index[game.away_team]
        z_margin, z_total, tie, winner = rng.random((4, draws))
        z_margin, z_total = ndtri(z_margin), ndtri(z_total)
        latent_margin = expected + shock[hi] - shock[ai]
        margin = latent_margin + law["marginSd"] * z_margin
        rho = law["rho"]
        total = law["meanTotal"] + law["totalSd"] * (rho * z_margin + np.sqrt(1 - rho * rho) * z_total)
        baseline = scores.nfl_scores(np.maximum(6, total), margin, tie, winner)
        targets = [((law["meanTotal"] + sign * latent_margin) / 2 - opposite[1 - side]) / mean_pace[side]
                   for side, sign in enumerate((1, -1))]
        sampled = templates[rng_state.integers(len(templates), size=draws)]
        h, a = simulate(sampled, laws, targets, rng_state)
        overtime = (h == a) & (tie > .12)
        home_win = winner < expit(margin / 8)
        candidate = h + 3 * (overtime & home_win), a + 3 * (overtime & ~home_win)
        yield game, hi, ai, expected, baseline, candidate


def assess(games, model, year, draws):
    law, _ = historical.fit(games, year)
    schedule = games[games.season.eq(year)]
    team_count = len(set(schedule.home_team) | set(schedule.away_team))
    rows = [{"metrics": [], **{key: np.zeros((team_count, draws))
             for key in ("wins", "points", "residual", "square")}} for _ in range(2)]
    count = np.zeros(team_count)
    weeks = []
    for game, hi, ai, expected, baseline, candidate in joint_draw(schedule, year, law, model, draws):
        weeks.append(game.week)
        for result, (h, a) in zip(rows, (baseline, candidate)):
            metric = historical.metrics(h, a, game)
            metric["joint"] = {
                "energy": prior.energy(h, a, game.home_score, game.away_score),
                "tieRate": float(np.mean(h == a)), "observedTieRate": float(game.home_score == game.away_score),
                "onePointTeamRate": float((np.mean(h == 1) + np.mean(a == 1)) / 2),
            }
            result["metrics"].append(metric)
            residual = h - a - expected
            result["wins"][hi] += (h > a) + .5 * (h == a)
            result["wins"][ai] += (a > h) + .5 * (h == a)
            result["points"][hi] += h
            result["points"][ai] += a
            result["residual"][hi] += residual
            result["residual"][ai] -= residual
            result["square"][hi] += residual ** 2
            result["square"][ai] += residual ** 2
        count[[hi, ai]] += 1
    output = []
    for result in rows:
        pair_product = np.sum(result["residual"] ** 2 - result["square"], axis=0) / np.sum(count * (count - 1))
        residual_variance = np.sum(result["square"], axis=0) / count.sum()
        output.append({"games": result["metrics"], "season": {
            "meanTeamWinsSd": float(np.std(result["wins"], axis=1).mean()),
            "meanTeamPointsSd": float(np.std(result["points"], axis=1).mean()),
            "sameTeamResidualCorrelation": float(pair_product.mean() / residual_variance.mean()),
        }})
    return output, np.asarray(weeks)


def intervals(origins, weeks, seed):
    rng = np.random.default_rng(seed)
    replications = 2000
    numerators = np.zeros((replications, len(BOOTSTRAP_METRICS)))
    denominators = np.zeros(replications)
    original = []
    for (baseline, candidate), origin_weeks in zip(origins, weeks):
        deltas = np.array([[c[key][metric] - b[key][metric] for key, metric in BOOTSTRAP_METRICS]
                           for b, c in zip(baseline["games"], candidate["games"])])
        original.append(deltas)
        week_values = np.unique(origin_weeks)
        week_sums = np.stack([deltas[origin_weeks == week].sum(axis=0) for week in week_values])
        week_sizes = np.array([(origin_weeks == week).sum() for week in week_values])
        sample = rng.integers(len(week_values), size=(replications, len(week_values)))
        numerators += week_sums[sample].sum(axis=1)
        denominators += week_sizes[sample].sum(axis=1)
    estimate = np.concatenate(original).mean(axis=0)
    bounds = np.quantile(numerators / denominators[:, None], [.025, .975], axis=0)
    return {f"{key}.{metric}": {"delta": float(center), "interval95": interval.tolist()}
            for (key, metric), center, interval in zip(BOOTSTRAP_METRICS, estimate, bounds.T)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--games", type=Path, default=scores.RAW)
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    games = historical.load(args.games)
    training = sorted({y for window in historical.WINDOWS for year in window for y in range(year - 3, year)})
    history, audit = read_drives(games, args.archive, training)
    out = {"protocolSha256": scores.sha(HERE / "PROTOCOL.md"), "gamesSha256": scores.sha(args.games),
           "source": audit, "draws": historical.DRAWS, "seed": historical.SEED}
    if any(audit[y]["valid"] / audit[y]["scheduled"] < .95 for y in training):
        out["decision"] = "Aborted at the predeclared archive completeness gate."
    else:
        results, weeks, fits = {}, {}, {}
        for window in historical.WINDOWS:
            for year in window:
                model = fit_state(history, year)
                _, pace, laws = model
                fits[year] = {
                    "donorGames": len(pace), "meanPace": pace.mean(axis=0).tolist(),
                    "stateCounts": [count.astype(int).tolist() for _, _, _, count in laws],
                    "expectedStatePoints": [(mass @ categories[:, 0]).tolist()
                                            for categories, _, mass, _ in laws],
                }
                results[year], weeks[year] = assess(games, model, year, historical.DRAWS)
                print(f"Assessed {year}", flush=True)
        out["fitByYear"] = fits
        out["windows"] = []
        for window in historical.WINDOWS:
            values = [results[year] for year in window]
            blocks = [weeks[year] for year in window]
            out["windows"].append({
                "years": list(window), "games": sum(map(len, blocks)), **prior.summarize(values),
                "pairedWeekBootstrap": intervals(values, blocks, historical.SEED + window.start),
            })
        out["byYear"] = {year: prior.summarize([rows]) for year, rows in results.items()}
        out["decision"] = ("Fresh validation required." if all(w["passes"] for w in out["windows"])
                           else "Research only. Do not adopt.")
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(out["decision"], flush=True)


if __name__ == "__main__":
    main()
