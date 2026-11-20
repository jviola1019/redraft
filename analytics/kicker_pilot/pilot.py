"""Repeat the frozen NFL field-goal forecasting pilot."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import LogisticRegression

YEARS = range(2001, 2018)
TEST_YEARS = range(2014, 2018)
COLUMNS = [
    "game_id", "play_id", "season_type", "field_goal_attempt",
    "field_goal_result", "kick_distance", "kicker_player_id",
]


def read_attempts(directory):
    seasons = []
    audit = {}
    for year in YEARS:
        path = directory / f"{year}.parquet"
        frame = pd.read_parquet(path, columns=COLUMNS)
        attempts = frame.loc[
            frame["field_goal_attempt"].eq(1) & frame["season_type"].eq("REG")
        ].copy()
        unique = attempts.drop_duplicates(["game_id", "play_id"])
        outcomes = unique.loc[unique["field_goal_result"].isin(["made", "missed", "blocked"])]
        distances = outcomes.loc[outcomes["kick_distance"].between(17, 75)]
        valid = distances.loc[distances["kicker_player_id"].notna()].copy()
        valid["made"] = valid["field_goal_result"].eq("made").astype(int)
        valid["season"] = year
        seasons.append(valid)
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        audit[year] = {
            "sha256": digest,
            "recorded_regular_season_attempts": len(attempts),
            "duplicate": len(attempts) - len(unique),
            "invalid_result": len(unique) - len(outcomes),
            "invalid_distance": len(outcomes) - len(distances),
            "missing_kicker_id": len(distances) - len(valid),
            "retained": len(valid),
        }
    return pd.concat(seasons, ignore_index=True), audit


def distance_terms(attempts):
    distance = attempts["kick_distance"].to_numpy()
    return np.column_stack([
        (distance - 40) / 10,
        *[np.maximum(distance - hinge, 0) / 10 for hinge in (35, 45, 55)],
    ])


def kicker_offset(history, year):
    weights = 0.8 ** (year - history["season"].to_numpy() - 1)
    logits = history["baseline_logit"].to_numpy()
    outcomes = history["made"].to_numpy()
    precision = 1 / 0.45**2
    offset = 0.0
    for _ in range(50):
        probability = expit(logits + offset)
        score = weights @ (outcomes - probability) - precision * offset
        information = weights @ (probability * (1 - probability)) + precision
        step = score / information
        offset += step
        if abs(step) < 1e-10:
            return offset
    raise RuntimeError("Kicker offset failed to converge")


def predict(attempts):
    past = []
    forecasts = []
    for year in range(2005, 2018):
        train = attempts.loc[attempts["season"].between(year - 4, year - 1)]
        current = attempts.loc[attempts["season"].eq(year)].copy()
        baseline = LogisticRegression(C=10, solver="lbfgs").fit(
            distance_terms(train), train["made"],
        )
        current["baseline_logit"] = baseline.decision_function(distance_terms(current))
        if year in TEST_YEARS:
            history = pd.concat(past)
            offsets = {
                kicker: kicker_offset(rows, year)
                for kicker, rows in history.groupby("kicker_player_id")
            }
            offset = current["kicker_player_id"].map(offsets)
            current["seen"] = offset.notna()
            current["candidate_logit"] = current["baseline_logit"] + offset.fillna(0)
            forecasts.append(current)
        past.append(current)

    predictions = pd.concat(forecasts, ignore_index=True)
    for model in ("baseline", "candidate"):
        logits = predictions[f"{model}_logit"]
        predictions[model] = expit(logits)
        predictions[f"{model}_loss"] = np.logaddexp(0, logits) - predictions["made"] * logits
        predictions[f"{model}_brier"] = (predictions[model] - predictions["made"]) ** 2
    predictions["paired_loss"] = predictions["candidate_loss"] - predictions["baseline_loss"]
    return predictions


def metrics(rows):
    names = [
        "made", "baseline", "candidate", "baseline_loss", "candidate_loss",
        "paired_loss", "baseline_brier", "candidate_brier",
    ]
    result = rows[names].mean().to_dict()
    result["attempts"] = len(rows)
    result["kickers"] = rows["kicker_player_id"].nunique()
    return result


def report(predictions):
    clusters = predictions.groupby("kicker_player_id")["paired_loss"].agg(["sum", "count"])
    rng = np.random.default_rng(2018)
    draws = rng.integers(len(clusters), size=(5000, len(clusters)))
    bootstrap = clusters["sum"].to_numpy()[draws].sum(axis=1)
    bootstrap /= clusters["count"].to_numpy()[draws].sum(axis=1)
    interval = np.quantile(bootstrap, [0.025, 0.975]).tolist()
    seasons = {year: metrics(rows) for year, rows in predictions.groupby("season")}
    buckets = pd.cut(
        predictions["kick_distance"], [16, 29, 39, 49, 59, 75],
        labels=["17–29", "30–39", "40–49", "50–59", "60–75"],
    )
    improved = sum(year["paired_loss"] < 0 for year in seasons.values())
    return {
        "all": metrics(predictions),
        "seasons": seasons,
        "distance_buckets": {
            bucket: metrics(rows) for bucket, rows in predictions.groupby(buckets, observed=True)
        },
        "history": {
            "prior_attempts" if seen else "no_prior_attempts": metrics(rows)
            for seen, rows in predictions.groupby("seen")
        },
        "paired_log_loss_kicker_cluster_95_percent_interval": interval,
        "improved_seasons": improved,
        "advance_research_candidate": interval[1] < 0 and improved >= 3,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    attempts, exclusions = read_attempts(args.archive)
    result = report(predict(attempts))
    result["source_audit"] = exclusions
    result["protocol_sha256"] = hashlib.sha256(Path(__file__).with_name("PROTOCOL.md").read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
