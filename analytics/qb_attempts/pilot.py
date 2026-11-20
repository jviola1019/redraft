"""Five-year credited passing attempts backtest on drafted QB cohorts."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = range(2001, 2023)
ORIGINS = range(2011, 2019)
COLS = ["game_id", "play_id", "season_type", "play_type", "pass_attempt",
        "sack", "two_point_attempt", "passer_player_id"]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_attempts(archive, schedule):
    games = pd.read_csv(schedule, usecols=["season", "game_type", "game_id", "home_score", "away_score"])
    games = games.loc[games["game_type"].eq("REG") & games[["home_score", "away_score"]].notna().all(axis=1)]
    observed, audit = {}, {}
    for year in YEARS:
        path = archive / f"{year}.parquet"
        frame = pd.read_parquet(path, columns=COLS)
        attempts = frame.loc[
            frame["season_type"].eq("REG") & frame["pass_attempt"].eq(1)
            & frame["play_type"].isin(["pass", "qb_spike"]) & frame["sack"].eq(0)
            & frame["two_point_attempt"].eq(0)
        ]
        expected = set(games.loc[games["season"].eq(year), "game_id"])
        actual = set(attempts["game_id"])
        if not expected or expected != actual or attempts.duplicated(["game_id", "play_id"]).any():
            raise ValueError(f"Unexpected attempt coverage in {year}. Missing {expected - actual}, extra {actual - expected}")
        known = attempts["passer_player_id"].str.fullmatch(r"00-\d{7}", na=False)
        observed[year] = attempts.loc[known, "passer_player_id"].value_counts().to_dict()
        audit[year] = {
            "sha256": digest(path), "games": len(actual), "attempts": len(attempts),
            "unattributed_attempts": int((~known).sum()),
        }
    return observed, audit


def labels(draft, attempts):
    columns = ["season", "position", "round", "pick", "gsis_id", "pfr_player_id", "pfr_player_name"]
    drafted = pd.read_csv(draft, usecols=columns)
    drafted = drafted.loc[drafted["season"].between(2001, 2018)].copy()
    known = (
        drafted["gsis_id"].str.fullmatch(r"00-\d{7}", na=False)
        & drafted["pfr_player_id"].notna()
        & ~drafted["gsis_id"].duplicated(keep=False)
        & ~drafted["pfr_player_id"].duplicated(keep=False)
    )
    qb = drafted["position"].eq("QB") & drafted["round"].between(1, 7)
    excluded = drafted.loc[qb & ~known, columns].astype(object).where(pd.notna(drafted), None)
    sample = drafted.loc[qb & known].copy()
    sample["bin"] = pd.cut(sample["round"], [0, 1, 3, 7], labels=["round_1", "rounds_2_3", "rounds_4_7"])
    for age in range(5):
        sample[f"year_{age + 1}"] = [
            attempts[season + age].get(gsis, 0)
            for season, gsis in zip(sample["season"], sample["gsis_id"])
        ]
    sample["actual"] = sample[[f"year_{age + 1}" for age in range(5)]].sum(axis=1)
    return sample, excluded.to_dict("records")


def score(donors, actual):
    draws = np.sort(donors.to_numpy())
    n = len(draws)
    crps = np.abs(draws - actual).mean() - ((2 * np.arange(1, n + 1) - n - 1) @ draws) / n**2
    low, high = np.quantile(draws, [0.1, 0.9], method="inverted_cdf")
    median = np.median(draws)
    return {
        "crps": float(crps), "median": float(median), "absolute_error": float(abs(median - actual)),
        "lower_80": int(low), "upper_80": int(high), "covered_80": bool(low <= actual <= high),
        "below_support": bool(actual < draws[0]), "above_support": bool(actual > draws[-1]),
        "donors": n,
    }


def predict(sample):
    predictions = []
    for origin in ORIGINS:
        eligible = sample.loc[sample["season"] + 4 < origin]
        origin_rows = sample.loc[sample["season"].eq(origin)]
        for row in origin_rows.itertuples():
            same_bin = eligible.loc[eligible["bin"].eq(row.bin)]
            pool = same_bin if len(same_bin) >= 5 else eligible
            predictions.append({
                "origin": origin, "gsis_id": row.gsis_id, "pfr_id": row.pfr_player_id,
                "player": row.pfr_player_name, "round": row.round, "pick": row.pick,
                "actual_annual": [getattr(row, f"year_{age + 1}") for age in range(5)],
                "actual": row.actual, "candidate_uses_benchmark": len(same_bin) < 5,
                "latest_donor_season": int(eligible["season"].max()) + 4,
                "benchmark": score(eligible["actual"], row.actual),
                "candidate": score(pool["actual"], row.actual),
            })
    return predictions


def summary(rows):
    result = {"players": len(rows), "zeros": sum(row["actual"] == 0 for row in rows)}
    for model in ("benchmark", "candidate"):
        result[model] = {
            key: float(np.mean([row[model][key] for row in rows]))
            for key in ("crps", "absolute_error", "covered_80")
        }
        result[model].update({
            key: sum(row[model][key] for row in rows)
            for key in ("below_support", "above_support")
        })
    result["paired_crps"] = result["candidate"]["crps"] - result["benchmark"]["crps"]
    return result


def summarize(predictions, audit):
    groups = {
        origin: [row for row in predictions if row["origin"] == origin]
        for origin in ORIGINS
    }
    cohorts = {}
    rng = np.random.default_rng(2018)
    resampled = np.zeros(5000)
    for origin, rows in groups.items():
        cohorts[origin] = summary(rows)
        cohorts[origin]["window_unattributed_attempts"] = sum(
            audit[year]["unattributed_attempts"] for year in range(origin, origin + 5)
        )
        paired = np.array([row["candidate"]["crps"] - row["benchmark"]["crps"] for row in rows])
        resampled += rng.choice(paired, size=(5000, len(paired))).sum(axis=1)
    interval = np.quantile(resampled / len(predictions), [0.025, 0.975]).tolist()
    improved = sum(group["paired_crps"] < 0 for group in cohorts.values())
    return {
        "all": summary(predictions), "origins": cohorts, "improved_origins": improved,
        "conditional_paired_crps_95_interval": interval,
        "advance_post_draft_research": interval[1] < 0 and improved >= 6,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    data = args.root / "data/raw"
    draft, schedule = data / "draft_picks.csv", data / "games.csv"
    attempts, audit = load_attempts(args.archive, schedule)
    sample, exclusions = labels(draft, attempts)
    predictions = predict(sample)
    result = summarize(predictions, audit)
    result.update({
        "eligible_qbs_by_cohort": sample.groupby("season").size().to_dict(),
        "excluded_unknown_identity": exclusions, "season_coverage": audit,
        "source_sha256": {path.name: digest(path) for path in (draft, schedule, Path(__file__).with_name("PROTOCOL.md"))},
        "predictions": predictions,
    })
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
