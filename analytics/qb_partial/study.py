"""Freeze and score the production-conditioned partial QB study."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ANALYTICS = HERE.parent
ROOT = ANALYTICS.parent
sys.path[:0] = [str(ANALYTICS), str(ANALYTICS / "qb_conditioned")]
from review import (KINDS, ARMS, available_by, cutoff_date, digest, donor_pool,
                    fy, identity, match_targets, paired)
from forecast_audit import evaluate_distribution, summarize, weighted_quantile, weights

LAST_OBSERVED = 2025
ORIGINS = range(2022, 2026)
FROZEN = ("partial_forecasts.json", "prospective_2022.json")


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def read(path):
    return json.loads(path.read_text())


def project(donors, manifest):
    years = np.repeat([row["cohort"] for row in manifest], [row["count"] for row in manifest])
    assert len(years) == len(donors)
    denominator = np.where(years[:, None] + np.arange(5) >= 2021, 17, 16)
    snaps = np.asarray([d["snaps"] for d in donors]) * 17 / denominator
    games = np.minimum(17, np.floor(np.asarray([d["games"] for d in donors]) * 17 / denominator + .5))
    return [{**{key: row[key] for key in ("rookieRole",)}, "cohort": int(year),
             "snaps": s.tolist(), "games": g.tolist()}
            for row, year, s, g in zip(donors, years, snaps, games)]


def predict(out):
    if any((out / name).exists() for name in (*FROZEN, "forecast.sha256", "results.json")):
        raise FileExistsError("Use a fresh output directory to reproduce the frozen forecasts.")
    runtime = json.loads(subprocess.check_output(["node", HERE / "runtime.mjs"], cwd=ROOT))
    combine = pd.read_csv(ROOT / "data/raw/combine.csv", low_memory=False)
    baseline = runtime["baseline"]
    links = read(HERE / "identity_links.json")
    paths = [HERE / name for name in ("study.py", "runtime.ts", "runtime.mjs", "PROTOCOL.md", "identity_links.json")]
    paths += [ANALYTICS / "qb_conditioned/review.py", ANALYTICS / "forecast_audit.py",
              ANALYTICS / "five_year.py", ANALYTICS / "train_models.py",
              ANALYTICS / "five_year_strict_2018.json", ANALYTICS / "model.json",
              ROOT / "lib/server-data.ts", ROOT / "lib/scouting.ts", ROOT / "lib/engine.ts",
              ROOT / "lib/simulation.ts", ROOT / "data/raw/combine.csv", ROOT / "data/raw/games.csv"]
    common_hashes = {str(path.relative_to(ROOT)): digest(path) for path in paths}
    forecasts = []
    for origin in runtime["origins"]:
        year, cutoff = origin["year"], origin["cutoff"]
        latest_mature = max(y for y in range(2013, year) if available_by(y) <= cutoff_date(cutoff))
        annual, coverage, names = fy.load_annual(2013, latest_mature + 4)
        donor_frame, _, repairs = fy.build_cohorts(range(2014, latest_mature + 1), annual, names)
        donor_frame = donor_frame[donor_frame.position.eq("QB")]
        candidate, manifest = donor_pool(baseline, donor_frame, cutoff, annual)
        assert max(int(season) for season in coverage) < year
        assert all(group["labelAvailableBy"] <= cutoff_date(cutoff).isoformat() for group in manifest)
        assert all(p["availableBy"] <= cutoff for p in origin["prospects"])
        pools = {"baseline": project(baseline, manifest[:1]), "candidate": project(candidate, manifest)}
        for kind in KINDS:
            expected = np.asarray([[v[kind] for v in ages] for ages in origin["baselineExposure"]])
            np.testing.assert_array_equal([d[kind] for d in pools["baseline"]], expected)
        model_path = ANALYTICS / f"model-{year}.json"
        scenario_path = ROOT / f"data/processed/scenario-{year}.json"
        model = read(model_path)
        assert model["fitThroughSeason"] <= 2017
        assert model["fitLabelCutoff"] < cutoff == model["scenarioInformationCutoff"]
        eligible = combine[combine.season.eq(year) & combine.pos.eq("QB")].copy()
        for ix, row in eligible[eligible.pfr_id.isna()].iterrows():
            link = links.get(f"{year}:{row.player_name}")
            if link:
                assert identity(row.player_name, row.school) == identity(link["name"], link["school"])
                eligible.loc[ix, "pfr_id"] = link["pfrId"] or f"unassigned:{row.player_name}"
        targets, excluded, absent = match_targets(eligible, origin["prospects"])
        players = [{"cohort": year, "pfrId": None if row.pfr_id.startswith("unassigned:") else row.pfr_id,
                    "identitySource": "identity_links.json" if f"{year}:{row.player_name}" in links else "combine",
                    "prospectId": p["id"], "name": p["name"], "school": p["school"],
                    "probability": p["probability"], "profile": p["profile"],
                    "profileTier": "lowest" if p["profile"] == "QB-0" else "other"}
                   for row, p in targets]
        forecasts.append({"year": year, "cutoff": cutoff, "modelVersion": origin["modelVersion"],
                          "rookieModelFitThroughSeason": model["fitThroughSeason"],
                          "rookieFitLabelCutoff": model["fitLabelCutoff"],
                          "sourceHashes": {str(p.relative_to(ROOT)): digest(p) for p in
                                           (model_path, scenario_path)},
                          "donorSourceCoverage": coverage, "donorManifest": manifest,
                          "qbDonorIdentityRepairs": [
                              r for r in repairs if r["pfrId"] in set(donor_frame.pfr_id)],
                          "pools": pools, "baselineExposureParity": True,
                          "sourceExclusions": excluded, "runtimeProspectsOutsideSample": absent,
                          "runtimePlayableQbs": len(origin["prospects"]), "players": players})
    assert [len(f["players"]) for f in forecasts] == [15, 15, 14, 15]
    out.mkdir(parents=True, exist_ok=True)
    p2022 = forecasts[0]
    pending = {
        "evaluationStatus": "Pending complete and reconciled 2026 regular-season snap outcomes",
        "targets": {"annual5": {"season": 2026}, "cumulative5": {"seasons": list(range(2022, 2027))}},
        "scoreDefinitions": "Frozen in PROTOCOL.md; keep 2026 and five-season assessments out until complete.",
        "commonSourceHashes": common_hashes,
        "origin": {k: v for k, v in p2022.items() if k != "players"},
        "forecasts": [{**p, "arms": prospective(p2022["pools"], p["probability"])}
                      for p in p2022["players"]],
    }
    write(out / FROZEN[1], pending)
    write(out / FROZEN[0], {"commonSourceHashes": common_hashes, "origins": forecasts})
    (out / "forecast.sha256").write_text("".join(f"{digest(out / name)}  {name}\n" for name in FROZEN))
    print([(f["year"], len(f["players"]), f["runtimePlayableQbs"]) for f in forecasts])


def prospective(pools, probability):
    result = {}
    for arm, donors in pools.items():
        mass = weights(donors, probability)
        entry = {"massInDonorOrder": mass.tolist()}
        for kind in KINDS:
            values = np.asarray([row[kind] for row in donors])
            for target, outcome in (("annual5", values[:, 4]), ("cumulative5", values.sum(axis=1))):
                entry.setdefault(target, {})[kind] = {
                    "mean": float(outcome @ mass),
                    "interval80": [weighted_quantile(outcome, mass, q) for q in (.1, .9)],
                    "interval95": [weighted_quantile(outcome, mass, q) for q in (.025, .975)],
                }
        result[arm] = entry
    return result


def actual_through(annual, year, pid):
    records = [annual.get((season, pid), {"snaps": 0, "games": 0})
               for season in range(year, LAST_OBSERVED + 1)]
    return {kind: [record[kind] for record in records] for kind in KINDS}


def score_player(player, pools, annual):
    actual = actual_through(annual, player["cohort"], player["pfrId"])
    scores = {}
    for arm, donors in pools.items():
        mass = weights(donors, player["probability"])
        scores[arm] = {}
        for kind in KINDS:
            values = np.asarray([donor[kind] for donor in donors])
            scores[arm][kind] = {
                "annual": [evaluate_distribution(values[:, ix], mass, y)
                           for ix, y in enumerate(actual[kind])],
                "cumulative": [evaluate_distribution(values[:, :ix + 1].sum(axis=1), mass,
                                                      sum(actual[kind][:ix + 1]))
                               for ix in range(len(actual[kind]))],
            }
    return {**player, "actual": actual, "observedRookieRole": actual["snaps"][0] >= 200, "scores": scores}


def metrics(rows, target, age):
    if not rows:
        return {"n": 0}
    result = {"n": len(rows)}
    for kind in KINDS:
        a, b = ([p["scores"][arm][kind][target][age - 1] for p in rows] for arm in ARMS)
        result[kind] = {"baseline": summarize(a), "candidate": summarize(b),
                        "pairedCrps": paired(np.array([y["crps"] - x["crps"] for x, y in zip(a, b)]),
                                             np.array([p["cohort"] for p in rows]))}
    return result


def assess(rows):
    output = {}
    for target in ("annual", "cumulative"):
        output[target] = {}
        for age in range(1, 5):
            eligible = [p for p in rows if p["cohort"] + age - 1 <= LAST_OBSERVED]
            output[target][str(age)] = {
                "overall": metrics(eligible, target, age),
                "byOrigin": {str(year): metrics([p for p in eligible if p["cohort"] == year], target, age)
                             for year in sorted({p["cohort"] for p in eligible})},
                "byPredictedProfile": {
                    tier: metrics([p for p in eligible if p["profileTier"] == tier], target, age)
                    for tier in ("lowest", "other")},
                "byObservedRookieRole": {
                    tier: metrics([p for p in eligible if p["observedRookieRole"] is role], target, age)
                    for tier, role in (("under200", False), ("atLeast200", True))},
            }
    return output


def score(out):
    expected = {name: checksum for checksum, name in
                (line.split() for line in (out / "forecast.sha256").read_text().splitlines())}
    assert set(expected) == set(FROZEN)
    assert all(digest(out / name) == expected[name] for name in FROZEN)
    frozen = read(out / FROZEN[0])
    prospective_2022 = read(out / FROZEN[1])
    assert prospective_2022["commonSourceHashes"] == frozen["commonSourceHashes"]
    assert all(digest(ROOT / path) == checksum for path, checksum in frozen["commonSourceHashes"].items())
    annual, coverage, _ = fy.load_annual(min(ORIGINS), LAST_OBSERVED)
    unresolved = {identity(p["name"], p["school"])[0]
                  for f in frozen["origins"] for p in f["players"] if p["pfrId"] is None}
    for season in ORIGINS:
        source = pd.read_csv(ROOT / f"data/raw/snap_counts_{season}.csv", usecols=["game_type", "player"])
        names = {identity(name, "")[0] for name in source.loc[source.game_type.eq("REG"), "player"]}
        if unresolved & names:
            raise ValueError(f"Adjudicate unassigned PFR names from season {season}: {unresolved & names}")
    rows = [score_player(p, f["pools"], annual) for f in frozen["origins"] for p in f["players"]]
    primary = [p for p in rows if p["pfrId"] is not None]
    result = {"evaluationStatus": "Retrospective partial assessment; observed outcomes previously accessible.",
              "observedThrough": LAST_OBSERVED, "prospective2022Status": prospective_2022["evaluationStatus"],
              "runtimeChanged": False, "forecastHashes": expected, "sourceCoverage": coverage,
              "sampleSize": len(primary), "forecastBoardSize": len(rows),
              "unresolvedPfrIdentities": [p["name"] for p in rows if p["pfrId"] is None],
              "origins": [{**{k: v for k, v in f.items() if k not in
                  ("pools", "players")}, "matchedQbs": len(f["players"]),
                  "primaryQbs": sum(p["pfrId"] is not None for p in f["players"]),
                  "baselineDonors": len(f["pools"]["baseline"]),
                  "candidateDonors": len(f["pools"]["candidate"])} for f in frozen["origins"]],
              "metrics": assess(primary),
              "zeroAssumptionSensitivity": {"n": len(rows), "metrics": assess(rows)}}
    write(out / "results.json", result)
    write(out / "player_scores.json", [{**p, "includedInPrimary": p["pfrId"] is not None}
                                      for p in rows])
    print(json.dumps({"sampleSize": len(primary), "forecastBoardSize": len(rows), "observedThrough": LAST_OBSERVED}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("predict", "score"))
    parser.add_argument("--out", default=HERE, type=Path)
    args = parser.parse_args()
    {"predict": predict, "score": score}[args.stage](args.out)
