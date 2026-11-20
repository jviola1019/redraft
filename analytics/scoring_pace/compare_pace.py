"""Chronological comparison of remaining regulation possession forecasts."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from scoring_game_state.compare_state import CLOCK_COLUMN, game_drives
from scoring_possessions.compare import COLUMNS, DRIVE_PLAYS, SOURCE_URL, historical, scores

KNOTS = np.arange(0, 3601, 300)
BANDS = (0, 300, 600, 1800, 3601)


def observations(plays, game, drives):
    """Label the retained drive anchors, using the scoreboard strictly before each anchor."""
    plays = plays.sort_values("play_id", kind="stable").reset_index(drop=True)
    scoreboard = plays[["total_home_score", "total_away_score"]].ffill().fillna(0).shift(1, fill_value=0)
    difference = scoreboard.total_home_score - scoreboard.total_away_score
    for key in ("fixed_drive", "qtr"):
        plays[key] = plays[key].ffill().bfill()
    teams = plays.posteam.replace(scores.ALIASES)
    valid = teams.isin((game.home_team, game.away_team))
    # An eligible scrimmage or kick play takes priority over the segment fallback.
    plays["anchorPriority"] = np.where(plays.play_type.isin(DRIVE_PLAYS), 0, 1)
    anchors = (plays[valid & plays.qtr.le(4)].sort_values("anchorPriority", kind="stable")
               .drop_duplicates("fixed_drive").sort_index())
    if len(anchors) != len(drives):
        raise ValueError(f"Drive anchor count disagrees with reconciled extraction for {game.game_id}")
    signs = np.where(teams.loc[anchors.index].eq(game.home_team), 1, -1)
    anchor_keys = Counter(zip(anchors[CLOCK_COLUMN], signs))
    expected_keys = Counter((drive[2], 1 - 2 * drive[0]) for drive in drives)
    if anchor_keys != expected_keys:
        raise ValueError(f"Drive anchors disagree with reconciled extraction for {game.game_id}")
    return zip(anchors[CLOCK_COLUMN].astype(int), signs * difference.loc[anchors.index],
               range(len(anchors) - 1, -1, -1))


def read_seasons(games, archive):
    seasons, audit = {}, {}
    for year in range(2010, 2018):
        schedule = games[games.season.eq(year)]
        path = archive / f"{year}.parquet"
        plays = pd.read_parquet(path, columns=[*COLUMNS, CLOCK_COLUMN])
        by_game = plays[plays.season_type.eq("REG")].groupby("game_id", sort=False)
        losses, records = Counter(), []
        lengths = []
        for game in schedule.itertuples():
            if game.game_id in by_game.indices:
                game_plays = by_game.get_group(game.game_id)
                rows, reason = game_drives(game_plays, game)
            else:
                rows, reason = None, "missing_game"
            if reason:
                losses[reason] += 1
                continue
            lengths.append(len(rows))
            records.extend((game.game_id, game.week, clock, diff, remaining, 1 / len(rows))
                           for clock, diff, remaining in observations(game_plays, game, rows))
        seasons[year] = pd.DataFrame(records, columns=["game_id", "week", "clock", "diff", "remaining", "weight"])
        audit[year] = {"url": SOURCE_URL.format(year), "sha256": scores.sha(path),
                       "scheduled": len(schedule), "valid": len(lengths), "losses": dict(losses),
                       "drives": sum(lengths)}
        print(f"Read {year}: {len(lengths)}/{len(schedule)} games", flush=True)
    return seasons, audit


def features(clock, diff=None):
    clock = np.asarray(clock)
    clock_basis = np.maximum(0, 1 - np.abs(clock[:, None] - KNOTS) / 300)
    if diff is None:
        return clock_basis
    diff = np.asarray(diff)
    return np.hstack([clock_basis, clock_basis * (diff <= -8)[:, None],
                      clock_basis * (diff >= 8)[:, None]])


def fit_model(training, score_state):
    basis = features(training.clock, training["diff"] if score_state else None)
    penalty = np.full(basis.shape[1], 2.)
    penalty[:len(KNOTS)] = .001
    weighted = basis.T * training.weight.to_numpy()
    return np.linalg.solve(weighted @ basis + np.diag(penalty), weighted @ training.remaining)


def predict(coefficients, clock, diff=None):
    return np.maximum(0, features(clock, diff) @ coefficients)


def fixture_losses(predictions):
    columns = ["baselineMse", "candidateMse", "baselineMae", "candidateMae"]
    loss = predictions[["game_id", "week"]].copy()
    for arm in ("baseline", "candidate"):
        residual = predictions[arm] - predictions.remaining
        loss[arm + "Mse"] = residual ** 2
        loss[arm + "Mae"] = residual.abs()
    return loss.groupby(["game_id", "week"], sort=False)[columns].mean().reset_index()


def summary(loss):
    values = loss[["baselineMse", "candidateMse", "baselineMae", "candidateMae"]].mean()
    return {arm: {"mse": float(values[arm + "Mse"]),
                  "rmse": float(np.sqrt(values[arm + "Mse"])), "mae": float(values[arm + "Mae"])}
            for arm in ("baseline", "candidate")}


def assess(seasons, origin):
    training = pd.concat([seasons[year] for year in range(origin - 3, origin)], ignore_index=True)
    test = seasons[origin].copy()
    baseline, state = (fit_model(training, enabled) for enabled in (False, True))
    test["baseline"] = predict(baseline, test.clock)
    test["candidate"] = predict(state, test.clock, test["diff"])
    contrasts = []
    for seconds in (300, 600, 1800):
        reference = predict(state, [seconds], [0])[0]
        contrasts.append({"seconds": seconds, "reference": float(reference),
                          "trailing": float(predict(state, [seconds], [-8])[0] - reference),
                          "leading": float(predict(state, [seconds], [8])[0] - reference)})
    test["origin"] = origin
    return test, contrasts


def bootstrap(origins, seed):
    rng = np.random.default_rng(seed)
    totals, counts = np.zeros((2000, 2)), np.zeros(2000)
    for origin in origins:
        difference = pd.DataFrame({"week": origin.week,
                                   "mse": origin.candidateMse - origin.baselineMse,
                                   "mae": origin.candidateMae - origin.baselineMae})
        weeks = difference.groupby("week")
        sums, size = weeks[["mse", "mae"]].sum().to_numpy(), weeks.size().to_numpy()
        sampled = rng.integers(len(size), size=(len(counts), len(size)))
        totals += sums[sampled].sum(axis=1)
        counts += size[sampled].sum(axis=1)
    bounds = np.quantile(totals / counts[:, None], [.025, .975], axis=0)
    return {key: values.tolist() for key, values in zip(("mse", "mae"), bounds.T)}


def describe_bands(predictions):
    result = []
    for start, end in zip(BANDS, BANDS[1:]):
        band = predictions[predictions.clock.ge(start) & predictions.clock.lt(end)]
        cells = {"trailing": band["diff"].le(-8), "close": band["diff"].abs().le(7),
                 "leading": band["diff"].ge(8)}
        result.append({"clockSeconds": [start, end - 1], "games": int(band.game_id.nunique()),
                       "drives": len(band), "stateDrives": {k: int(v.sum()) for k, v in cells.items()},
                       **summary(fixture_losses(band))})
    return result


def evaluate_window(predictions, window):
    origins = [fixture_losses(predictions[year]) for year in window]
    interval = bootstrap(origins, historical.SEED + window.start)
    metrics = summary(pd.concat(origins))
    delta = {key: metrics["candidate"][key] - metrics["baseline"][key] for key in ("mse", "rmse", "mae")}
    return {"years": list(window), "games": sum(map(len, origins)), **metrics, "delta": delta,
            "pairedWeekBootstrap95": interval,
            "clockBands": describe_bands(pd.concat([predictions[year] for year in window])),
            "passes": bool(interval["mse"][1] < 0 and metrics["candidate"]["mae"] <= 1.01 * metrics["baseline"]["mae"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--games", type=Path, default=scores.RAW)
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    games = historical.load(args.games)
    seasons, audits = read_seasons(games, args.archive)
    result = {"protocolSha256": scores.sha(HERE / "PROTOCOL.md"), "gamesSha256": scores.sha(args.games),
              "source": audits, "bootstrapSeed": historical.SEED}
    if any(audit["valid"] / audit["scheduled"] < .95 for audit in audits.values()):
        result["decision"] = "Archive completeness gate failed."
    else:
        results = {year: assess(seasons, year) for window in historical.WINDOWS for year in window}
        schedules = {year: prediction for year, (prediction, _) in results.items()}
        result["windows"] = [evaluate_window(schedules, window) for window in historical.WINDOWS]
        result["byYear"] = {year: {"games": prediction.game_id.nunique(), "drives": len(prediction),
                                 **summary(fixture_losses(prediction)), "stateVsClose": contrasts}
                            for year, (prediction, contrasts) in results.items()}
        result["decision"] = ("Replicated predictive gain for the retained-drive target."
                              if all(w["passes"] for w in result["windows"])
                              else "Reproducible gain did not meet the fixed evidence threshold.")
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(result["decision"], flush=True)


if __name__ == "__main__":
    main()
