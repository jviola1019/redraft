"""Chronological experiment from reconciled nflverse fixed drive segments."""
import argparse
from collections import Counter
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from scipy.special import ndtri, expit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import score_marginal as historical
import score_distribution as scores

SOURCE_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.parquet"
COLUMNS = ["game_id", "play_id", "season_type", "qtr", "fixed_drive", "posteam",
           "play_type", "total_home_score", "total_away_score"]
DRIVE_PLAYS = {"run", "pass", "punt", "field_goal", "qb_kneel", "qb_spike"}


def game_drives(plays, game):
    plays = plays.sort_values("play_id", kind="stable").copy()
    score_cols = ["total_home_score", "total_away_score"]
    plays[score_cols] = plays[score_cols].ffill().fillna(0)
    if tuple(plays[score_cols].iloc[-1]) != (game.home_score, game.away_score):
        return None, "final_score_mismatch"
    for key in ("fixed_drive", "qtr"):
        plays[key] = plays[key].ffill().bfill()
    if plays[["fixed_drive", "qtr"]].isna().any(axis=None):
        return None, "missing_drive_or_quarter"
    prev = np.zeros(2, dtype=int)
    rows = []
    for (_, overtime), segment in plays.groupby(["fixed_drive", plays.qtr.gt(4)], sort=False):
        end = segment[score_cols].iloc[-1].to_numpy(dtype=int)
        credit = end - prev
        prev = end
        if (credit < 0).any():
            return None, "nonmonotone_score"
        if overtime:
            continue
        teams = segment.posteam.replace(scores.ALIASES)
        valid = teams.isin((game.home_team, game.away_team))
        drive_teams = teams[valid & segment.play_type.isin(DRIVE_PLAYS)]
        if drive_teams.empty:
            drive_teams = teams[valid]
        if drive_teams.empty:
            if credit.any():
                return None, "scoring_segment_without_team"
            continue
        side = int(drive_teams.iloc[0] == game.away_team)
        rows.append((side, int(credit[side]), int(credit[1 - side])))
    if {row[0] for row in rows} != {0, 1}:
        return None, "missing_possession_side"
    return rows, None


def read_drives(games, directory):
    audits, history = {}, {}
    for year in range(2001, 2018):
        path = directory / f"{year}.parquet"
        plays = pd.read_parquet(path, columns=COLUMNS)
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
            "url": SOURCE_URL.format(year), "sha256": scores.sha(path), "bytes": path.stat().st_size,
            "scheduled": len(schedule), "valid": len(valid), "losses": dict(rejects),
        }
    return history, audits


def fit_drives(history, year):
    prior = [game for season in range(year - 3, year) for game in history[season]]
    pace = np.array([[sum(row[0] == side for row in game) for side in (0, 1)] for game in prior])
    laws = []
    for side in (0, 1):
        categories, counts = np.unique(
            [row[1:] for game in prior for row in game if row[0] == side], axis=0, return_counts=True
        )
        laws.append((categories, counts / counts.sum()))
    return pace, laws


def tilt(categories, base, target):
    own = categories[:, 0]
    target = np.clip(target, own.min() + .05, own.max() - .05)
    low, high = np.full(len(target), -20.), np.full(len(target), 20.)
    for _ in range(29):
        theta = (low + high) / 2
        log_mass = np.log(base)[None, :] + theta[:, None] * own
        mass = np.exp(log_mass - log_mass.max(axis=1, keepdims=True))
        probs = mass / mass.sum(axis=1, keepdims=True)
        undershoot = np.sum(probs * own, axis=1) < target
        low = np.where(undershoot, theta, low)
        high = np.where(undershoot, high, theta)
    return probs


def sample_credits(counts, target, law, rng):
    categories, base = law
    cdf = np.cumsum(tilt(categories, base, target), axis=1)[:, :-1]
    uniforms = rng.random((len(target), counts.max()))
    # Enumerating the support avoids an array with dimensions draws x counts x categories.
    index = np.zeros(uniforms.shape, dtype=np.uint8)
    for bound in cdf.T:
        index += uniforms > bound[:, None]
    credit = categories[index]
    active = np.arange(counts.max())[None, :] < counts[:, None]
    return (credit * active[:, :, None]).sum(axis=1).T


def joint_draw(schedule, year, law, drive_law, draws):
    rng = np.random.default_rng(np.random.SeedSequence([historical.SEED, year]))
    rng_drive = np.random.default_rng(np.random.SeedSequence([historical.SEED, year, 9352]))
    teams = sorted(set(schedule.home_team) | set(schedule.away_team))
    team_index = {team: index for index, team in enumerate(teams)}
    shock = rng.normal(0, law["seasonShockSd"], size=(len(teams), draws))
    pace, laws = drive_law
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
        counts_home, counts_away = pace[rng_drive.integers(len(pace), size=draws)].T
        home_target = ((law["meanTotal"] + latent_margin) / 2 - opposite[1]) / mean_pace[0]
        away_target = ((law["meanTotal"] - latent_margin) / 2 - opposite[0]) / mean_pace[1]
        home_own, home_opponent = sample_credits(counts_home, home_target, laws[0], rng_drive)
        away_own, away_opponent = sample_credits(counts_away, away_target, laws[1], rng_drive)
        h, a = home_own + away_opponent, away_own + home_opponent
        overtime = (h == a) & (tie > .12)
        home_win = winner < expit(margin / 8)
        candidate = h + 3 * (overtime & home_win), a + 3 * (overtime & ~home_win)
        yield game, hi, ai, expected, baseline, candidate


def energy(h, a, actual_home, actual_away):
    n = len(h) // 2
    return float(np.hypot(h - actual_home, a - actual_away).mean()
                 - .5 * np.hypot(h[:n] - h[n:], a[:n] - a[n:]).mean())


def assess(games, drive_law, year, draws):
    law, _ = historical.fit(games, year)
    schedule = games[games.season.eq(year)]
    team_count = len(set(schedule.home_team) | set(schedule.away_team))
    rows = [
        {"metrics": [], "wins": np.zeros((team_count, draws)), "points": np.zeros((team_count, draws)),
         "residual": np.zeros((team_count, draws)), "square": np.zeros((team_count, draws))}
        for _ in range(2)
    ]
    count = np.zeros(team_count)
    for game, hi, ai, expected, baseline, candidate in joint_draw(schedule, year, law, drive_law, draws):
        for result, (h, a) in zip(rows, (baseline, candidate)):
            metric = historical.metrics(h, a, game)
            metric["joint"] = {
                "energy": energy(h, a, game.home_score, game.away_score),
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
    return output


def summarize(origins):
    result = historical.summarize(origins)
    baseline, candidate = (result[arm]["score"] for arm in ("baseline", "candidate"))
    result["criteria"]["jointEnergyImproves"] = candidate["joint"]["energy"] < baseline["joint"]["energy"]
    result["criteria"]["shutoutBrierNoWorse"] = candidate["shutouts"]["brier"] <= baseline["shutouts"]["brier"]
    del result["criteria"]["shutoutBrierImproves"]
    values = [all(gate.values()) if isinstance(gate, dict) else gate for gate in result["criteria"].values()]
    result["passes"] = all(values)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--games", type=Path, default=scores.RAW)
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    games = historical.load(args.games)
    history, audit = read_drives(games, args.archive)
    out = {"protocolSha256": scores.sha(HERE / "PROTOCOL.md"), "gamesSha256": scores.sha(args.games),
           "source": audit, "draws": historical.DRAWS, "seed": historical.SEED}
    training = {y for window in historical.WINDOWS for year in window for y in range(year - 3, year)}
    if any(audit[y]["valid"] / audit[y]["scheduled"] < .95 for y in training):
        out["decision"] = "Aborted at the predeclared archive completeness gate."
    else:
        results, fit_summary = {}, {}
        for window in historical.WINDOWS:
            for year in window:
                pace, laws = fit_drives(history, year)
                results[year] = assess(games, (pace, laws), year, historical.DRAWS)
                fit_summary[year] = {
                    "donorGames": len(pace), "meanPace": pace.mean(axis=0).tolist(),
                    "paceCorrelation": float(np.corrcoef(pace.T)[0, 1]),
                    "driveCredits": [{"points": categories.tolist(), "probabilities": base.tolist()}
                                     for categories, base in laws],
                }
        out["fitByYear"] = fit_summary
        out["windows"] = [{"years": list(window), **summarize([results[y] for y in window])}
                          for window in historical.WINDOWS]
        out["byYear"] = {year: summarize([rows]) for year, rows in results.items()}
        out["decision"] = ("Fresh validation required." if all(w["passes"] for w in out["windows"])
                           else "Research only. Do not adopt.")
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(out["decision"], flush=True)


if __name__ == "__main__":
    main()
