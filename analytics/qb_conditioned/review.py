"""Compare a cutoff-safe QB donor expansion with the production QB forecast."""
import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "analytics"))
import five_year as fy
from forecast_audit import evaluate_distribution, summarize, weights

KINDS = ("snaps", "games")
ARMS = ("baseline", "candidate")
SEED = 20261120
BOOTSTRAPS = 5000
START_YEAR = 2013
END_YEAR = 2025


def identity(name, school):
    def normalize(value):
        return re.sub(r"[^a-z0-9]", "", str(value).lower())
    school = str(school).replace(" St.", " State").replace("Southern California", "USC")
    return normalize(name), normalize(school.replace("Louisiana-Lafayette", "Louisiana"))


def available_by(cohort):
    return date(cohort + 5, 3, 1)


def cutoff_date(cutoff):
    return datetime.fromisoformat(cutoff.replace("Z", "+00:00")).date()


def donor_pool(baseline, cohorts, cutoff, annual):
    eligible = cohorts[cohorts.season.map(available_by) <= cutoff_date(cutoff)]
    donors = list(baseline)
    manifest = [{"cohort": START_YEAR, "count": len(baseline),
                 "rookieRole": sum(row["rookieRole"] for row in baseline),
                 "labelAvailableBy": available_by(START_YEAR).isoformat()}]
    for year, group in eligible.groupby("season"):
        year = int(year)
        careers = [career(annual, year, row.pfr_id) for row in group.itertuples()]
        donors.extend(careers)
        manifest.append({"cohort": year, "count": len(careers),
                         "rookieRole": sum(row["rookieRole"] for row in careers),
                         "labelAvailableBy": available_by(year).isoformat()})
    return donors, manifest


def career(annual, year, pfr_id):
    years = [annual.get((year + age, pfr_id), {"snaps": 0, "games": 0}) for age in range(5)]
    return {**{kind: [data[kind] for data in years] for kind in KINDS},
            "rookieRole": years[0]["snaps"] >= 200}


def exposure(donors, schedule):
    snaps = np.asarray([d["snaps"] for d in donors]) * np.array(schedule) / 16
    games = np.minimum(schedule, np.floor(
        np.asarray([d["games"] for d in donors]) * np.array(schedule) / 16 + .5))
    return {"snaps": snaps, "games": games}


def score_player(actual, pools, schedules, probability):
    result = {}
    for name, schedule in schedules.items():
        result[name] = {}
        for arm, donors in pools.items():
            values = exposure(donors, schedule)
            mass = weights(donors, probability)
            result[name][arm] = {
                kind: {
                    "total": evaluate_distribution(values[kind].sum(axis=1), mass, sum(actual[kind])),
                    "annual": [evaluate_distribution(values[kind][:, age], mass, actual[kind][age])
                               for age in range(5)],
                } for kind in KINDS}
    return result


def paired(deltas, cohorts):
    rng = np.random.default_rng(SEED)
    groups = [deltas[cohorts == year] for year in np.unique(cohorts)]
    resampled_sums = [group[rng.integers(len(group), size=(BOOTSTRAPS, len(group)))].sum(axis=1)
                      for group in groups]
    draws = np.sum(resampled_sums, axis=0) / len(deltas)
    return {"difference": float(deltas.mean()),
            "bootstrap95": np.quantile(draws, [.025, .975]).tolist(),
            "resamples": BOOTSTRAPS}


def metrics(rows, schedule, age=None, bootstrap=False):
    output = {}
    for kind in KINDS:
        def arm_scores(arm):
            forecasts = [row["scores"][schedule][arm][kind] for row in rows]
            return [f["total"] if age is None else f["annual"][age] for f in forecasts]
        a, b = (arm_scores(arm) for arm in ARMS)
        entry = {"baseline": summarize(a), "candidate": summarize(b)}
        if bootstrap:
            entry["pairedCrps"] = paired(np.array([y["crps"] - x["crps"] for x, y in zip(a, b)]),
                                         np.array([row["cohort"] for row in rows]))
        output[kind] = entry
    return output


def role_metrics(rows):
    observed = np.array([row["actual"]["rookieRole"] for row in rows])
    predicted = np.array([row["probability"] for row in rows])
    return {"n": len(rows), "observedFrequency": float(observed.mean()),
            "meanPrediction": float(predicted.mean()), "brier": float(np.mean((observed - predicted)**2))}


def assess(rows):
    report = {}
    for schedule in ("production", "draftTime"):
        report[schedule] = {
            "overall": metrics(rows, schedule, bootstrap=True),
            "byCohort": {str(year): metrics([r for r in rows if r["cohort"] == year], schedule,
                                           bootstrap=True)
                         for year in sorted({r["cohort"] for r in rows})},
            "byAge": {str(age + 1): metrics(rows, schedule, age=age) for age in range(5)},
            "byPredictedProfile": {
                profile: metrics([r for r in rows if r["profileTier"] == profile], schedule)
                for profile in ("lowest", "other")},
            "byObservedRookieRole": {
                role: metrics([r for r in rows if r["actual"]["rookieRole"] == value], schedule)
                for role, value in (("under200", False), ("atLeast200", True))},
        }
    return report


def match_targets(eligible, prospects):
    lookup = {}
    for prospect in prospects:
        key = identity(prospect["name"], prospect["school"])
        lookup.setdefault(key, []).append(prospect)
    counts = Counter(identity(r.player_name, r.school) for r in eligible.itertuples())
    excluded, matches = [], []
    for row in eligible.itertuples():
        key = identity(row.player_name, row.school)
        linked = lookup.get(key, [])
        if pd.isna(row.pfr_id) or counts[key] != 1 or len(linked) != 1:
            excluded.append({"name": row.player_name,
                             "pfrId": None if pd.isna(row.pfr_id) else row.pfr_id,
                             "reason": "unknownPfrIdentity" if pd.isna(row.pfr_id)
                             else "noUniqueExactScenarioMatch"})
            continue
        matches.append((row, linked[0]))
    assert len({r.pfr_id for r, _ in matches}) == len(matches)
    used = {prospect["id"] for _, prospect in matches}
    absent = [p["name"] for p in prospects if p["id"] not in used]
    return matches, excluded, absent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(out):
    runtime = json.loads(subprocess.check_output(["node", HERE / "runtime.mjs"], cwd=ROOT))
    annual, coverage, names = fy.load_annual(START_YEAR, END_YEAR)
    combine = pd.read_csv(ROOT / "data/raw/combine.csv", low_memory=False)
    # build_cohorts uses the same identity repair as the strict production artifact.
    oldest = max(origin["year"] - 5 for origin in runtime["origins"])
    donor_frame, _, repairs = fy.build_cohorts(range(START_YEAR + 1, oldest + 1), annual, names)
    donor_frame = donor_frame[donor_frame.position.eq("QB")]
    baseline = runtime["baseline"]
    rows, origins = [], []
    for origin in runtime["origins"]:
        year, cutoff = origin["year"], origin["cutoff"]
        frozen = json.loads((ROOT / f"analytics/model-{year}.json").read_text())
        assert available_by(START_YEAR).isoformat() < runtime["strictCutoff"] < cutoff
        assert frozen["fitThroughSeason"] <= 2017
        assert frozen["fitLabelCutoff"] < cutoff == frozen["scenarioInformationCutoff"]
        assert all(prospect["availableBy"] <= cutoff for prospect in origin["prospects"])
        candidate, manifest = donor_pool(baseline, donor_frame, cutoff, annual)
        # Alter all ineligible-season outcome values and require identical fitted donor arrays.
        poisoned = {key: value if key[0] < year else {"snaps": 999999, "games": 999999}
                    for key, value in annual.items()}
        assert donor_pool(baseline, donor_frame, cutoff, poisoned) == (candidate, manifest)
        assert all(int(group["cohort"]) + 4 < year for group in manifest)
        # Also exclude immature cohorts already present in the input donor frame.
        possibly_future = donor_frame[donor_frame.season.map(available_by) > cutoff_date(cutoff)]
        future_pids = set(possibly_future.pfr_id)
        assert not set(donor_frame[donor_frame.season.map(available_by) <= cutoff_date(cutoff)].pfr_id) & future_pids
        only_mature = donor_frame[~donor_frame.pfr_id.isin(future_pids)]
        assert donor_pool(baseline, only_mature, cutoff, annual) == (candidate, manifest)
        schedule = {"production": [17 if year + age >= 2021 else 16 for age in range(5)],
                    "draftTime": [17 if year >= 2021 else 16] * 5}
        projected = exposure(baseline, schedule["production"])
        for kind in KINDS:
            runtime_values = np.asarray([[v[kind] for v in ages] for ages in origin["baselineExposure"]])
            np.testing.assert_array_equal(projected[kind], runtime_values)

        eligible = combine[combine.season.eq(year) & combine.pos.eq("QB")]
        targets, excluded, absent = match_targets(eligible, origin["prospects"])
        origins.append({"cohort": year, "cutoff": cutoff, "modelVersion": origin["modelVersion"],
                        "rookieModelFitThroughSeason": frozen["fitThroughSeason"],
                        "rookieFitLabelCutoff": frozen["fitLabelCutoff"],
                        "donorCohorts": manifest, "baselineDonors": len(baseline),
                        "candidateDonors": len(candidate),
                        "candidateRoleDonors": sum(d["rookieRole"] for d in candidate),
                        "assessmentLabelAvailableBy": available_by(year).isoformat(),
                        "runtimePlayableQbs": len(origin["prospects"]), "evaluatedQbs": len(targets),
                        "sourceExclusions": excluded, "runtimeProspectsOutsideSample": absent,
                        "schedules": schedule, "baselineExposureParity": True,
                        "futureDataPoisoningPassed": True})
        for row, prospect in targets:
            actual = career(annual, year, row.pfr_id)
            rows.append({"cohort": year, "pfrId": row.pfr_id, "prospectId": prospect["id"],
                         "probability": prospect["probability"], "profile": prospect["profile"],
                         "profileTier": "lowest" if prospect["profile"] == "QB-0" else "other",
                         "actual": actual, "scores": score_player(actual,
                         {"baseline": baseline, "candidate": candidate}, schedule, prospect["probability"])})
    assessment = assess(rows)
    gate = {}
    for kind, values in assessment["production"]["overall"].items():
        gate[kind] = {"pairedCrpsUpperBelowZero": values["pairedCrps"]["bootstrap95"][1] < 0,
                      "coverage95AtLeast90Percent": values["candidate"]["interval95"]["coverage"] >= .9,
                      "interval95ScoreNonWorsening": values["candidate"]["interval95"]["meanIntervalScore"] <=
                      values["baseline"]["interval95"]["meanIntervalScore"]}
    paths = [HERE / name for name in ["review.py", "runtime.ts", "runtime.mjs", "PROTOCOL.md"]]
    paths += [ROOT / path for path in (
        "lib/server-data.ts", "lib/scouting.ts", "lib/engine.ts", "lib/simulation.ts",
        "analytics/model.json", "analytics/five_year.py", "analytics/train_models.py",
        "analytics/forecast_audit.py", "analytics/five_year_strict_2018.json",
        "data/raw/combine.csv", "data/raw/games.csv")]
    for year in (2019, 2020, 2021):
        paths += [ROOT / f"data/processed/scenario-{year}.json", ROOT / f"analytics/model-{year}.json"]
    report = {"version": "production-conditioned-qb-donors-v1", "runtimeChanged": False,
              "evaluationStatus": "Previously studied historical cohorts",
              "sourceHashes": {str(p.relative_to(ROOT)): digest(p) for p in paths},
              "sourceCoverage": coverage, "qbDonorIdentityRepairs": [
                  repair for repair in repairs if repair["pfrId"] in set(donor_frame.pfr_id)],
              "origins": origins, "metrics": assessment,
              "rookieRoleCalibration": {"overall": role_metrics(rows), **{
                  profile: role_metrics([r for r in rows if r["profileTier"] == profile])
                  for profile in ("lowest", "other")}},
              "researchGate": gate,
              "advanceToIndependentConfirmation": all(all(check.values()) for check in gate.values())}
    out.mkdir(parents=True, exist_ok=True)
    for filename, value in (("results.json", report), ("predictions.json", rows)):
        (out / filename).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE)
    arguments = parser.parse_args()
    result = run(arguments.out)
    print(json.dumps({"origins": result["origins"], "researchGate": result["researchGate"]}, indent=2))
