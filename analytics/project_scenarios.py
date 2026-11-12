"""Build frozen scenario-year rookie-role projections from the pre-2018 pipeline.

The script first requires exact canonical-ID prediction parity against the
stored 2018 model. It never joins players by name and never reads post-2017
labels as training outcomes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "analytics"
SCENARIO_2018 = ROOT / "data" / "clean" / "scenario_2018.json"
RAW_COMBINE = ROOT / "data" / "raw" / "combine.csv"
MODEL_2018 = ANALYTICS / "model.json"
FEATURE_FILE = ANALYTICS / "features" / "combine_model_features.csv"
LABEL_FILE = ANALYTICS / "outcomes" / "rookie_snap_labels.csv"
TRAINER_FILE = ANALYTICS / "train_models.py"
CUTOFF = "2018-04-26T00:00:00Z"
LOGISTIC_C = 10.0
TOLERANCE = 1e-6


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_trainer():
    sys.path.insert(0, str(ANALYTICS))
    spec = importlib.util.spec_from_file_location("redraft_frozen_trainer", TRAINER_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the frozen model trainer.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def position_group(position: str, trainer) -> str:
    # Match the engine's gameplay convention: first listed dual role; SAF joins DB;
    # EDGE is grouped as LB for runtime fallback policy.
    source = position.split("/", 1)[0].strip()
    if source.upper() == "SAF":
        source = "S"
    if source.upper().replace("-", "").replace(" ", "") == "HBACK":
        return "TE"
    group = trainer.pos_group(source)
    return "LB" if group == "EDGE" else group


def model_position_feature(position: str, trainer) -> str:
    # SAF is a source alias for safety and maps to the trained DB class. EDGE has
    # no audited pre-2018 feature mapping and remains an unknown one-hot category.
    source = position.split("/", 1)[0].strip()
    if source.upper() == "SAF":
        source = "S"
    return trainer.pos_group(source)


def scenario_features(prospects: list[dict], trainer) -> pd.DataFrame:
    rows = []
    for prospect in prospects:
        rows.append({
            "prospectId": prospect["id"],
            "sourcePosition": prospect.get("position", ""),
            "dualPosition": "/" in str(prospect.get("position", "")),
            "height": prospect.get("heightIn"),
            "wt": prospect.get("weightLb"),
            "forty": prospect.get("forty"),
            "bench": prospect.get("bench"),
            "vertical": prospect.get("verticalIn"),
            "broad_jump": prospect.get("broadJumpIn"),
            "cone": prospect.get("cone"),
            "shuttle": prospect.get("shuttle"),
            "position": model_position_feature(str(prospect.get("position", "")), trainer),
        })
    frame = pd.DataFrame(rows)
    if frame.prospectId.duplicated().any():
        raise ValueError("Scenario contains duplicate canonical prospect IDs.")
    return frame


def load_fit(trainer):
    features = pd.read_csv(FEATURE_FILE)
    labels = pd.read_csv(LABEL_FILE)
    expected_features = ["season", "pfr_id", *trainer.FEATURES]
    if list(features.columns[:len(expected_features)]) != expected_features:
        raise ValueError("Feature file schema changed; refusing to reinterpret it.")
    if not {"season", "pfr_id", "y", "label_available_by"}.issubset(labels.columns):
        raise ValueError("Outcome file lacks required year, ID, target, or availability fields.")
    joined = features.merge(labels[["season", "pfr_id", "y", "label_available_by"]],
                            on=["season", "pfr_id"], validate="one_to_one")
    if len(joined) != len(features) or len(joined) != len(labels):
        raise ValueError("Feature and outcome rows do not form an exact one-to-one ID join.")
    if joined.season.isna().any() or not joined.season.between(2013, 2017).all():
        raise ValueError("The frozen training rows must be restricted to 2013–2017.")
    available = pd.to_datetime(joined.label_available_by, utc=True, errors="coerce")
    cutoff = pd.Timestamp(CUTOFF)
    if available.isna().any() or not (available <= cutoff).all():
        raise ValueError("A training label was not available by the frozen cutoff.")
    if not joined.y.isin([0, 1]).all():
        raise ValueError("Unexpected target encoding in outcomes.")
    if joined.pfr_id.isna().any() or joined.duplicated(["season", "pfr_id"]).any():
        raise ValueError("Training observations require unique exact canonical PFR IDs.")
    return joined, trainer.logistic(LOGISTIC_C).fit(joined[trainer.FEATURES], joined.y)


def validate_2018_parity(model, trainer) -> dict:
    scenario = json.loads(SCENARIO_2018.read_text())
    frozen = json.loads(MODEL_2018.read_text())
    if scenario["metadata"].get("draftYear") != 2018:
        raise ValueError("The parity scenario is not the 2018 class.")
    expected = {p["prospectId"]: p for p in frozen["prospect"]["projections"]
                if p.get("projectionSource") == "combine model" and p.get("roleProbability") is not None}
    playable = [p for p in scenario["prospects"] if p.get("eligibilitySource") == "combine-participant"]
    frame = scenario_features(playable, trainer)
    if set(expected) - set(frame.prospectId):
        raise ValueError("Frozen model contains 2018 canonical IDs absent from the parity scenario.")
    supported = [p for p in playable if p.get("position") not in {"K", "P", "LS"}]
    if len(expected) != len(supported):
        raise ValueError(f"Exact-ID parity population differs: frozen={len(expected)}, scenario-supported={len(supported)}.")
    predictions = model.predict_proba(frame[trainer.FEATURES])[:, 1]
    predicted = dict(zip(frame.prospectId, predictions))
    differences = []
    for prospect_id, baseline in expected.items():
        rounded = round(float(predicted[prospect_id]), 6)
        if abs(rounded - float(baseline["roleProbability"])) > TOLERANCE:
            differences.append({"prospectId": prospect_id, "reconstructed": rounded,
                                "stored": baseline["roleProbability"]})
    if differences:
        raise ValueError(f"Frozen 2018 prediction parity failed: {differences[:3]}")
    return {
        "status": "passed",
        "joinKey": "prospectId exact canonical ID",
        "matchedSupportedProspects": len(expected),
        "omittedSpecialists": len(playable) - len(supported),
        "storedModelVersion": frozen["version"],
        "toleranceAfterSixDecimalRounding": TOLERANCE,
        "mismatchCount": 0,
    }


def discover_scenarios() -> list[tuple[int, Path, dict]]:
    discovered = []
    for path in sorted((ROOT / "data" / "processed").glob("scenario-[0-9][0-9][0-9][0-9].json")):
        source = json.loads(path.read_text())
        metadata = source.get("metadata", {})
        year = metadata.get("draftYear")
        if not isinstance(year, int) or year <= 2018:
            continue
        if path.stem != f"scenario-{year}" or metadata.get("version") != f"nflverse-{year}-combine-pool-v1":
            raise ValueError(f"Scenario {path.name} does not match the audited year/version contract.")
        if not any(row.get("path") == "data/raw/combine.csv" and row.get("sha256") == sha256(RAW_COMBINE)
                   for row in metadata.get("sourceFiles", [])):
            raise ValueError(f"Scenario {year} does not pin the current combine source bytes.")
        discovered.append((year, path, source))
    if not discovered:
        raise ValueError("No audited post-2018 scenario artifacts were found.")
    return discovered


def project_scenario(model, trainer, parity: dict, training_positions: set[str], year: int, scenario_path: Path, source: dict) -> dict:
    if source["metadata"].get("draftYear") != year:
        raise ValueError(f"The {year} scenario has the wrong draft year.")
    version = f"redraft-{year}-pre2018-logistic-C10-v1"
    playable = [p for p in source["prospects"] if p.get("playable") is True]
    nonplayable = [p for p in source["prospects"] if p.get("playable") is not True]
    if len(playable) != int(source["metadata"].get("playableProspectCount", -1)):
        raise ValueError("Scenario playable pool size contradicts its metadata.")
    frame = scenario_features(playable, trainer)
    probabilities = model.predict_proba(frame[trainer.FEATURES])[:, 1]
    by_id = dict(zip(frame.prospectId, probabilities))
    base = json.loads(MODEL_2018.read_text())["prospect"]
    priors = base["positionPriors"]
    global_prior = base["globalPrior"]
    projections = []
    for p in playable:
        position = position_group(str(p.get("position", "")), trainer)
        specialist = position in {"K", "P", "LS"}
        dual_position = "/" in str(p.get("position", ""))
        model_position = str(frame.loc[frame.prospectId == p["id"], "position"].iloc[0])
        unseen_position = model_position not in training_positions
        raw_probability = round(float(by_id[p["id"]]), 6)
        missing = sum(p.get(key) is None for key in
                      ("heightIn", "weightLb", "forty", "bench", "verticalIn", "broadJumpIn", "cone", "shuttle"))
        all_measurements_missing = missing == 8
        unsupported = dual_position or unseen_position or all_measurements_missing
        runtime_probability = None if specialist else priors.get(position, global_prior) if unsupported else raw_probability
        projections.append({
            "prospectId": p["id"],
            "name": p.get("name"),
            "sourcePosition": p.get("position", ""),
            "positionGroup": position,
            "modelPositionFeature": model_position,
            "roleProbability": runtime_probability,
            "rawModelProbability": raw_probability if unsupported and not specialist and not all_measurements_missing else None,
            "target": base["target"],
            "supported": not specialist and not unsupported,
            "fallback": specialist or unsupported,
            "dualPosition": dual_position,
            "unseenModelPosition": unseen_position,
            "allMeasurementsMissing": all_measurements_missing,
            "missingMeasurements": missing,
            "projectionSource": "all measurements missing; runtime uses position prior" if all_measurements_missing else "unsupported dual-position model diagnostic; runtime uses position prior" if dual_position else "unsupported unseen-position model diagnostic; runtime uses position prior" if unseen_position else f"frozen pre-2018 logistic model on {year} scenario measurements",
            "modelVersion": version,
        })
    for p in nonplayable:
        position = position_group(str(p.get("position", "")), trainer)
        specialist = position in {"K", "P", "LS"}
        dual_position = "/" in str(p.get("position", ""))
        model_position = model_position_feature(str(p.get("position", "")), trainer)
        unseen_position = model_position not in training_positions
        probability = None if specialist else priors.get(position, global_prior)
        projections.append({
            "prospectId": p["id"],
            "name": p.get("name"),
            "sourcePosition": p.get("position", ""),
            "positionGroup": position,
            "modelPositionFeature": model_position,
            "roleProbability": probability,
            "rawModelProbability": None,
            "target": base["target"],
            "supported": False,
            "fallback": True,
            "dualPosition": dual_position,
            "unseenModelPosition": unseen_position,
            "allMeasurementsMissing": True,
            "missingMeasurements": 8,
            "projectionSource": "2018 pre-2018-fit position prior; no player-specific measurement model",
            "modelVersion": version + ":position-prior-fallback",
        })
    if len({p["prospectId"] for p in projections}) != len(source["prospects"]):
        raise ValueError("Output projections are not a one-to-one mapping to scenario IDs.")
    return {
        "version": version,
        "scenarioYear": year,
        "scenarioVersion": source["metadata"]["version"],
        "scenarioInformationCutoff": source["metadata"]["informationCutoff"],
        "fitThroughSeason": 2017,
        "fitLabelCutoff": CUTOFF,
        "model": {
            "algorithm": "sklearn Pipeline: train_models.prepare + LogisticRegression",
            "selectedHyperparameterSource": "analytics/model.json, frozen selected logistic C=10.0",
            "logisticC": LOGISTIC_C,
            "features": trainer.FEATURES,
            "trainingCohorts": [2013, 2017],
            "trainingRows": 1519,
            "trainingRule": "Exact one-to-one (season, pfr_id) join of frozen feature and label tables; labels available on or before 2018-04-26.",
        },
        "reconstruction2018Parity": parity,
        "projections": projections,
        "counts": {
            "scenarioProspects": len(source["prospects"]),
            "playableProspects": len(playable),
            "measurementRows": sum(sum(p.get(key) is not None for key in
                                        ("heightIn", "weightLb", "forty", "bench", "verticalIn", "broadJumpIn", "cone", "shuttle")) > 0
                                   for p in playable),
            "playerSpecificSupported": sum(p["supported"] for p in projections),
            "specialistsUnavailable": sum(p["positionGroup"] in {"K", "P", "LS"} for p in projections),
            "dualPositionUnsupported": sum(p["dualPosition"] for p in projections),
            "unseenModelPositionUnsupported": sum(p["unseenModelPosition"] for p in projections),
            "allMeasurementsMissingUnsupported": sum(p["allMeasurementsMissing"] for p in projections[:len(playable)]),
            "referenceOnlyPositionFallbacks": len(nonplayable),
        },
        "scenarioProvenance": {
            "artifact": str(scenario_path.relative_to(ROOT)),
            "sourceFiles": source["metadata"].get("sourceFiles", []),
            "identityPolicy": "Scenario prospectId is the only output join key; scenario features are consumed from exact canonical-ID records, with no name matching.",
        },
        "sourceHashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (TRAINER_FILE, FEATURE_FILE, LABEL_FILE, MODEL_2018, SCENARIO_2018, scenario_path, RAW_COMBINE)
        },
        "limitations": [
            "Predictions target at least 200 rookie-season regular-season scrimmage snaps, an opportunity/availability outcome rather than talent, starter probability, or career value.",
            "The frozen model was trained only on identifiable 2013–2017 combine participants; cohort and identity selection bias remain.",
            f"{year} is an extrapolation of a pre-2018 model to a later cohort, not a {year}-calibrated model; no {year} labels were used for fit or tuning.",
            f"{year} scenario measurements have reconstructed availability; exact original publication timestamps are unavailable.",
            "Position categories absent from the 2013–2017 training data are ignored by the frozen one-hot encoder; EDGE has no audited pre-2018 mapping, so its raw score is diagnostic-only and runtime uses the engine LB prior. SAF is treated as the trained safety/DB alias.",
            "Playable scenario rows with all eight combine measurements missing receive the position prior and are flagged unsupported; their names/eligibility can remain in the scenario without inventing measurement evidence.",
            "The scenario includes combine participants only as playable prospects. Non-combine historical references receive constant 2018 position priors and are unsupported player-specific forecasts.",
            "Dual-position prospects retain their raw source position and name. The first listed role is a gameplay grouping convention; the frozen score is exposed only as an unsupported diagnostic, and runtime receives the corresponding position prior.",
            "Kicker, punter, and long-snapper probabilities are unavailable.",
            "The five-year development and causal draft-impact models are not validated by these rookie-role probabilities.",
        ],
    }


def main() -> None:
    trainer = load_trainer()
    features, model = load_fit(trainer)
    if len(features) != 1519:
        raise ValueError(f"Frozen fit row count changed: {len(features)}")
    parity = validate_2018_parity(model, trainer)
    built = []
    for year, path, source in discover_scenarios():
        training_positions = set(features.position.dropna().astype(str).unique())
        artifact = project_scenario(model, trainer, parity, training_positions, year, path, source)
        output = ANALYTICS / f"model-{year}.json"
        output.write_text(json.dumps(artifact, indent=2) + "\n")
        built.append({"output": str(output.relative_to(ROOT)), "version": artifact["version"],
                      "scenarioYear": year, "fitRows": len(features), "parity": artifact["reconstruction2018Parity"],
                      "counts": artifact["counts"], "sourceHashes": artifact["sourceHashes"]})
    print(json.dumps({"reconstructed2018Parity": parity, "artifacts": built}, indent=2))


if __name__ == "__main__":
    main()
