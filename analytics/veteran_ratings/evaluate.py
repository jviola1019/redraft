"""Walk-forward veteran Madden OVR participation study with aggregate-only output."""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).resolve().parent
DEFAULT_SNAP_DIR = HERE.parent.parent / "data/raw"
MANIFEST = json.loads((HERE / "source_manifest.json").read_text())
NUMERIC = ["log_snaps", "log_older_snaps", "games", "older_games"]


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def name_key(name):
    normalized = unicodedata.normalize("NFKD", name.casefold())
    tokens = " ".join("".join(c for c in normalized if not unicodedata.combining(c)).split()).split()
    if tokens and tokens[-1].rstrip(".") in {"jr", "sr", "ii", "iii", "iv", "v"}:
        tokens.pop()
    return "".join(c for c in "".join(tokens) if c.isalnum())


def load_season(path, year):
    """Aggregate valid regular-season player-game rows before the cross-source join."""
    players = {}
    seen = set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if int(row["season"]) != year or row["game_type"] != "REG":
                continue
            player_id = row["pfr_player_id"]
            key = (player_id, row["game_id"])
            if not player_id or not row["game_id"] or key in seen:
                raise ValueError(f"Missing or duplicate player-game identity in {path}")
            seen.add(key)
            values = players.setdefault(
                player_id, {"offense": 0, "defense": 0, "games": 0, "week": 0}
            )
            values["offense"] += int(row["offense_snaps"])
            values["defense"] += int(row["defense_snaps"])
            values["games"] += 1
            if int(row["week"]) >= values["week"]:
                values.update(week=int(row["week"]), name=row["player"], position=row["position"])
    if not players:
        raise ValueError(f"No regular-season snap rows in {path}")
    return players


def read_ratings(path, origin):
    """Read the pre-draft archive snapshot and preserve duplicates for ambiguity checks."""
    snapshot = MANIFEST["snapshot_metadata"][str(origin)]
    if sha256(path) != snapshot["sha256"]:
        raise ValueError(f"Unexpected rating archive checksum for {path}")
    if snapshot["rating_date"] >= snapshot["draft_start"]:
        raise ValueError("Rating snapshot must strictly precede draft")
    rows = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (
                row["iteration_date"] != snapshot["rating_date"]
                or row["iteration"] != "super-bowl"
                or int(row["season"]) != snapshot["rating_season"]
            ):
                continue
            rows[name_key(row["player_full_name"])].append(row["overall_rating"])
    if not rows:
        raise ValueError(f"Frozen rating snapshot missing: {path}")
    return rows


def side_snaps(player):
    return max(player.get("offense", 0), player.get("defense", 0))


def join_features(previous, older, ratings):
    counts = Counter()
    rows = []
    identity_names = Counter(name_key(v["name"]) for v in previous.values())
    for player_id, record in previous.items():
        previous_snaps = side_snaps(record)
        if previous_snaps == 0:
            counts["special_teams_only"] += 1
            continue
        counts["eligible"] += 1
        name = name_key(record["name"])
        choices = ratings.get(name, [])
        if not name or identity_names[name] != 1:
            counts["ambiguous_snap_name"] += 1
            continue
        if len(choices) != 1:
            counts["ambiguous_archive_name" if choices else "unmatched"] += 1
            continue
        if not choices[0].isdigit() or not 1 <= int(choices[0]) <= 99:
            counts["invalid_rating"] += 1
            continue
        older_record = older.get(player_id, {})
        rows.append({
            "player_id": player_id,
            "position": record["position"],
            "log_snaps": np.log1p(previous_snaps),
            "log_older_snaps": np.log1p(side_snaps(older_record)),
            "games": record["games"],
            "older_games": older_record.get("games", 0),
            "ovr": int(choices[0]),
        })
        counts["matched"] += 1
    return rows, counts


def attach_outcomes(rows, next_season):
    return [
        {**row, "role": int(side_snaps(next_season.get(row["player_id"], {})) >= 500)}
        for row in rows
    ]


def predict(train, holdout, augmented):
    numeric = NUMERIC + (["ovr"] if augmented else [])
    transform = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("position", OneHotEncoder(handle_unknown="ignore"), ["position"]),
    ])
    model = make_pipeline(transform, LogisticRegression(C=1, max_iter=1000))
    model.fit(train, train["role"])
    return model.predict_proba(holdout)[:, 1]


def losses(target, probs):
    safe = np.clip(probs, 1e-15, 1 - 1e-15)
    return np.column_stack(((target - probs) ** 2, -(target * np.log(safe) + (1 - target) * np.log1p(-safe))))


def compare(target, baseline, augmented):
    base_loss, aug_loss = losses(target, baseline), losses(target, augmented)
    delta = aug_loss - base_loss
    rng = np.random.default_rng(33519)
    draws = rng.integers(0, len(target), size=(2000, len(target)))
    ci = np.quantile(delta[draws].mean(axis=1), [0.025, 0.975], axis=0)
    return {
        "count": len(target),
        "positive_count": int(target.sum()),
        "metrics": {
            name: {
                "baseline": float(base_loss[:, i].mean()),
                "augmented": float(aug_loss[:, i].mean()),
                "augmented_minus_baseline": float(delta[:, i].mean()),
                "player_bootstrap_95_interval": ci[:, i].tolist(),
            }
            for i, name in enumerate(("brier", "log_loss"))
        },
        "auc": {
            "baseline": float(roc_auc_score(target, baseline)),
            "augmented": float(roc_auc_score(target, augmented)),
        },
        "passes_statistical_screen": bool((ci[1] < 0).all()),
    }


def run(ratings_dir, snap_dir):
    snap_paths = {y: snap_dir / f"snap_counts_{y}.csv" for y in range(2020, 2025)}
    snaps = {y: load_season(path, y) for y, path in snap_paths.items()}
    cohorts = {}
    panels = {}
    for origin in (2022, 2023, 2024):
        archive = read_ratings(ratings_dir / f"{origin - 1}.csv", origin)
        features, counts = join_features(snaps[origin - 1], snaps[origin - 2], archive)
        panels[origin] = pd.DataFrame(attach_outcomes(features, snaps[origin]))
        cohorts[origin] = {
            "archive_snapshot_rows": sum(map(len, archive.values())),
            "matched_fraction": counts["matched"] / counts["eligible"],
            "cohort_counts": dict(sorted(counts.items())),
        }
    result = {
        "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "snap_sha256": {year: sha256(path) for year, path in snap_paths.items()},
        "cohorts": cohorts,
        "evaluation": {},
    }
    for origin in (2023, 2024):
        train_years = [year for year in panels if year < origin]
        train = pd.concat([panels[year] for year in train_years], ignore_index=True)
        test = panels[origin]
        baseline, augmented = (predict(train, test, use_ovr) for use_ovr in (False, True))
        result["evaluation"][origin] = {
            "status": "primary" if origin == 2024 else "retrospective_archive_sensitivity",
            "train_origins": train_years,
            "train_count": len(train),
            "overall": compare(test["role"].to_numpy(), baseline, augmented),
            "qb_descriptive": compare(
                test.loc[test["position"].eq("QB"), "role"].to_numpy(),
                baseline[test["position"].eq("QB")],
                augmented[test["position"].eq("QB")],
            ),
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ratings-dir", required=True, type=Path)
    parser.add_argument("--snap-dir", type=Path, default=DEFAULT_SNAP_DIR)
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    args.output.write_text(json.dumps(run(args.ratings_dir, args.snap_dir), indent=2) + "\n")
