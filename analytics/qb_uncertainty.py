"""Re-evaluate strict QB uncertainty without refitting on held-out outcomes.

Inputs are the frozen 2013 strict donor labels and 2018 frozen forecast table.
This is a bounded, one-cohort diagnostic, not a production model fit.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import five_year as fy

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "analytics"
DONOR_FILE = ANALYTICS / "five_year_strict_labels.csv"
TEST_FILE = ANALYTICS / "five_year_frozen_2018_predictions.csv"
OUTPUT = ANALYTICS / "qb_uncertainty.json"
REPORT = ANALYTICS / "qb_uncertainty_REPORT.md"
SNAPS = [f"snaps{i}" for i in range(1, 6)]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values, kind="stable")
    x = values[order]
    w = weights[order]
    # Inverse empirical CDF; no interpolation beyond observed donor support.
    return float(x[min(np.searchsorted(np.cumsum(w), q, side="left"), len(x) - 1)])


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    p = successes / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [float(center - half), float(center + half)]


def distribution_metrics(actual_paths: np.ndarray, donor_paths: np.ndarray,
                         weights: np.ndarray) -> dict:
    totals = actual_paths.sum(axis=1)
    donor_totals = donor_paths.sum(axis=1)
    means = weights @ donor_paths
    total_means = means.sum(axis=1)
    result = {
        "n": int(len(actual_paths)),
        "annualMAE": float(np.abs(actual_paths - means).mean()),
        "annualRMSE": float(np.sqrt(np.square(actual_paths - means).mean())),
        "totalMAE": float(np.abs(totals - total_means).mean()),
        "totalRMSE": float(np.sqrt(np.square(totals - total_means).mean())),
        "rookieRoleBrier": float(np.mean((weights @ (donor_paths[:, 0] >= 200) - (actual_paths[:, 0] >= 200)) ** 2)),
        "anyCareerRoleBrier": float(np.mean((weights @ (donor_paths.max(axis=1) >= 200) - (actual_paths.max(axis=1) >= 200)) ** 2)),
        "totalIntervals": {},
    }
    for nominal in (0.8, 0.95):
        tail = (1 - nominal) / 2
        lows = np.array([weighted_quantile(donor_totals, w, tail) for w in weights])
        highs = np.array([weighted_quantile(donor_totals, w, 1 - tail) for w in weights])
        inside = (totals >= lows) & (totals <= highs)
        hits = int(inside.sum())
        result["totalIntervals"][str(int(nominal * 100))] = {
            "coverage": hits / len(totals),
            "coverageWilson95": wilson(hits, len(totals)),
            "meanWidth": float(np.mean(highs - lows)),
            "below": int(np.sum(totals < lows)),
            "above": int(np.sum(totals > highs)),
        }
    return result


def rolling_origin_qb() -> dict:
    """Strict draft-year replay; all choices are fixed before each test class."""
    # Use only complete 5-year classes supported by the recovered source archive.
    annual, coverage, names = fy.load_annual(2013, 2025)
    all_data, excluded, _ = fy.build_cohorts(range(2013, 2022), annual, names)
    data = all_data[all_data.position.eq("QB")].copy()
    origins = []
    for year in range(2018, 2022):
        donors = data[data.season <= year - 5]
        target = data[data.season == year]
        first, _, _ = fy.build_cohorts(range(2013, year), annual, names)
        first = first[first.position.eq("QB")]
        if donors.empty or target.empty:
            continue
        cutoff = pd.Timestamp(f"{year}-04-01", tz="UTC")
        if not (pd.to_datetime(donors.labelAvailableBy, utc=True) < cutoff).all():
            raise ValueError(f"Future five-year label entered {year} donor pool")
        if int(first.season.max()) >= year:
            raise ValueError(f"Future rookie-role label entered {year} role model")
        # Freeze classifier before test outcomes; it uses only each QB's rookie snaps.
        p_model = fy.role_predictions(first, target)
        role = (donors.snaps1.to_numpy() >= 200)
        n_pos = int(role.sum())
        if n_pos == 0 or n_pos == len(donors):
            raise ValueError(f"Role-stratum support absent at {year} cutoff")
        p_prior = np.full(len(target), n_pos / len(donors))
        methods = {
            "positionOnly": np.full(len(target), 0.0),
            "precutoffQBRoleRate": p_prior,
            "pooledRoleModel": p_model,
            "halfShrinkToQBRate": 0.5 * p_model + 0.5 * p_prior,
        }
        donor_paths = donors[SNAPS].to_numpy(dtype=float)
        actual_paths = target[SNAPS].to_numpy(dtype=float)
        candidate_metrics = {}
        for name, probs in methods.items():
            if name == "positionOnly":
                weights = np.full((len(target), len(donors)), 1 / len(donors))
            else:
                weights = np.where(role[None, :], probs[:, None] / n_pos,
                                   (1 - probs[:, None]) / (len(donors) - n_pos))
                weights = weights / weights.sum(axis=1, keepdims=True)
            candidate_metrics[name] = distribution_metrics(actual_paths, donor_paths, weights)
        origins.append({
            "draftYear": year,
            "cutoff": f"{year}-04-01",
            "donorCohorts": sorted(map(int, donors.season.unique())),
            "nDonors": int(len(donors)),
            "rolePositiveDonors": n_pos,
            "roleNegativeDonors": int(len(donors) - n_pos),
            "rookieModelCohorts": sorted(map(int, first.season.unique())),
            "nTestQBs": int(len(target)),
            "metrics": candidate_metrics,
        })
    # Aggregate only exact sums of per-person losses/counts; no claim of iid years.
    pooled = {}
    for method in (origins[0]["metrics"] if origins else {}):
        pooled[method] = _aggregate_origin_metrics(origins, method)
    return {
        "policy": "Expanding origins; full five-year donor labels end by draftYear-5; rookie role fit uses only cohorts through draftYear-1; fixed C=10 logistic and fixed half-shrink sensitivity.",
        "years": origins,
        "pooledAcrossFourDraftClasses": pooled,
        "sourceCoverage": {k: v for k, v in coverage.items() if int(k) >= 2013},
        "excludedUnknownIds": {str(k): int(v) for k, v in excluded.items()},
    }


def _aggregate_origin_metrics(origins: list[dict], method: str) -> dict:
    rows = [(o["metrics"][method], o["nTestQBs"]) for o in origins]
    n = sum(size for _, size in rows)
    result = {"n": n, "draftClasses": len(rows)}
    # Pool squared/absolute point losses and interval hit counts from exact
    # per-class means. Aggregate intervals are a descriptive pooled test, not CIs.
    for metric in ("annualMAE", "totalMAE", "rookieRoleBrier", "anyCareerRoleBrier"):
        result[metric] = float(sum(m[metric] * size for m, size in rows) / n)
    for metric in ("annualRMSE", "totalRMSE"):
        result[metric] = float(np.sqrt(sum(m[metric] ** 2 * size for m, size in rows) / n))
    result["totalIntervals"] = {}
    for level in ("80", "95"):
        result["totalIntervals"][level] = {
            "coverage": float(sum(m["totalIntervals"][level]["coverage"] * size for m, size in rows) / n),
            "meanWidth": float(sum(m["totalIntervals"][level]["meanWidth"] * size for m, size in rows) / n),
            "below": sum(m["totalIntervals"][level]["below"] for m, _ in rows),
            "above": sum(m["totalIntervals"][level]["above"] for m, _ in rows),
        }
    return result


def run() -> dict:
    donors = pd.read_csv(DONOR_FILE)
    donors = donors[donors.position.eq("QB")].copy()
    test = pd.read_csv(TEST_FILE)
    test = test[test.position.eq("QB")].copy()
    if donors.season.nunique() != 1 or donors.season.iloc[0] != 2013:
        raise ValueError("Expected only strict pre-2018 QB donor cohort 2013")
    if test.season.nunique() != 1 or test.season.iloc[0] != 2018:
        raise ValueError("Expected frozen 2018 QB holdout")
    if len(donors) != 15 or len(test) != 16:
        raise ValueError("Input row counts differ from the frozen evidence contract")

    donor_paths = donors[SNAPS].to_numpy(dtype=float)
    actual_paths = test[SNAPS].to_numpy(dtype=float)
    donor_role = donor_paths[:, 0] >= 200
    n_role = int(donor_role.sum())
    donor_totals = donor_paths.sum(axis=1)
    # Current profile probabilities, versus the pre-cutoff cohort empirical role
    # fraction. With 3/15 positives this equals the unconditional QB donor mix.
    p_current = test.pooledRookieProbability.to_numpy(dtype=float)
    p_cohort = np.full(len(test), n_role / len(donors))

    def role_weights(p: np.ndarray) -> np.ndarray:
        w = np.where(donor_role[None, :], p[:, None] / n_role,
                     (1 - p[:, None]) / (len(donors) - n_role))
        return w / w.sum(axis=1, keepdims=True)

    # For p=3/15, these stratum weights exactly reduce to equal weight per donor.
    candidate_specs = {
        "currentPooledRookieProbability": role_weights(p_current),
        "precutoffQBRoleRate_3of15": role_weights(p_cohort),
        "unconditionalQBDonors": np.full((len(test), len(donors)), 1 / len(donors)),
    }
    candidates = {
        name: distribution_metrics(actual_paths, donor_paths, weights)
        for name, weights in candidate_specs.items()
    }
    rookie_actual = (actual_paths[:, 0] >= 200).astype(float)
    briers = {
        "currentPooledRookieProbability": float(np.mean((p_current - rookie_actual) ** 2)),
        "precutoffQBRoleRate_3of15": float(np.mean((p_cohort - rookie_actual) ** 2)),
    }
    unsupported_high = int(np.sum(actual_paths.sum(axis=1) > donor_totals.max()))
    result = {
        "version": "qb-uncertainty-one-cohort-diagnostic-v1",
        "scope": "Static re-evaluation only; no runtime code changed and no held-out outcomes used for fitting.",
        "inputs": {
            DONOR_FILE.name: {"sha256": sha256(DONOR_FILE), "rows": int(len(donors))},
            TEST_FILE.name: {"sha256": sha256(TEST_FILE), "rows": int(len(test))},
        },
        "cutoffs": {"donorCohort": 2013, "donorLabelsAvailableBy": "2018-03-01", "forecastDraft": 2018,
                    "holdoutOutcomeSeasons": [2018, 2022]},
        "support": {
            "QBDonors": int(len(donors)), "donorCohorts": 1,
            "rookieRoleDonors_ge200Snaps": n_role,
            "noRookieRoleDonors": int(len(donors) - n_role),
            "donorTotalSnapMin": float(donor_totals.min()),
            "donorTotalSnapMedian": float(np.median(donor_totals)),
            "donorTotalSnapMax": float(donor_totals.max()),
            "holdoutQBs": int(len(test)),
            "holdoutOutcomesAboveEveryDonorTrajectory": unsupported_high,
            "holdoutRookieRoleCount": int(rookie_actual.sum()),
            "holdoutAnyCareerRoleCount": int(np.sum(actual_paths.max(axis=1) >= 200)),
        },
        "candidates": candidates,
        "rookieRoleBrierComparison": briers,
        "strictRollingOrigins": rolling_origin_qb(),
        "decision": {
            "productionChangeRecommended": False,
            "recommendedNextCandidate": "Use the expanding pre-cutoff QB donor role rate in place of player-specific QB rookie-role probabilities, then evaluate on an untouched later set of draft classes.",
            "reason": "Across four strict rolling origins (66 QBs), the donor-rate baseline has lower pooled rookie-role Brier and total-snap MAE/RMSE than the individual QB logistic role model, and modestly better aggregate interval coverage. This is screening evidence from four inspected classes, not a final deployment decision. As of 2026-11-12, no 2022+ test class has complete five-season outcomes (2026 is incomplete). All candidates share a one-cohort 2018 support ceiling, and a material fraction of 2018 outcomes exceeds every donor trajectory; the evidence cannot identify a better tail model.",
            "uncertaintyStatus": "unsupported-for-high-end-QB-tails",
            "recommendedHandling": "Consider the simple pre-cutoff QB role-rate baseline as a candidate for an untouched evaluation. Keep source-backed donor trajectories and label QB high-end uncertainty unsupported; do not inflate intervals or synthesize unsupported career paths.",
        },
        "failedApproaches": [
            {"approach": "Replace player-specific pooled rookie-role probabilities with the pre-cutoff 3/15 QB role rate", "result": "On the 2018 holdout it improves rookie-role Brier and total RMSE slightly, but worsens total MAE; N=16 gives no stable selection evidence."},
            {"approach": "Widen percentile intervals until nominal coverage is reached", "result": "Rejected: it changes width without adding empirical upper-tail support; no donor exceeds the 2013 maximum trajectory."},
            {"approach": "Fit a QB-only hierarchical or regularized model and cohort bootstrap", "result": "Not estimable from one complete strict donor cohort. Repeated player resampling would not represent between-cohort parameter uncertainty."},
            {"approach": "Borrow non-QB trajectories to create QB career ceilings", "result": "Rejected: position transfer has no evaluated conditional exchangeability evidence in the available artifacts."},
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    render_report(result)
    return result


def render_report(r: dict) -> None:
    c = r["candidates"]
    lines = [
        "# QB uncertainty research",
        "",
        "Executed 2026-11-12 from the frozen analytical artifacts. This is a bounded diagnostic; it does not change the runtime model.",
        "",
        "## Evidence and cutoff",
        "",
        "The strict donor pool contains 15 identified QBs from the 2013 cohort, whose five annual labels were available by 2018-03-01. Only 3 donors crossed 200 rookie scrimmage snaps. The frozen 2018 holdout has 16 QBs and was evaluated on 2018–2022 outcomes. There is no second fully observable pre-2018 QB cohort in the strict artifact, so between-cohort uncertainty cannot be estimated.",
        "",
        f"Donor five-year total snaps range from {r['support']['donorTotalSnapMin']:.0f} to {r['support']['donorTotalSnapMax']:.0f}. {r['support']['holdoutOutcomesAboveEveryDonorTrajectory']} of 16 holdout QBs exceed the highest donor total. That is a support failure; changing an interval multiplier cannot supply missing career trajectories.",
        "",
        "## Candidate results",
        "",
        "All candidates use the same real 2013 QB vectors. The empirical role-rate candidate uses 3/15=0.20 as the probability of drawing from the three rookie-role donors; this equals the unconditional empirical QB donor distribution. Intervals use the discrete weighted donor CDF, with no extrapolation.",
        "The Wilson coverage intervals treat the 16 QBs as independent Bernoulli cases and do not account for their shared draft-class context; they are descriptive only.",
        "",
        "| Candidate | Total MAE | Total RMSE | 80% coverage (Wilson 95% CI) | 80% width | 95% coverage (Wilson 95% CI) | 95% width | Rookie-role Brier |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    briers = r["rookieRoleBrierComparison"]
    names = [("currentPooledRookieProbability", "Current pooled probabilities"),
             ("precutoffQBRoleRate_3of15", "Pre-cutoff QB role rate (3/15)"),
             ("unconditionalQBDonors", "Unconditional QB donors")]
    for key, label in names:
        m = c[key]
        i80, i95 = m["totalIntervals"]["80"], m["totalIntervals"]["95"]
        ci80 = ", ".join(f"{v:.1%}" for v in i80["coverageWilson95"])
        ci95 = ", ".join(f"{v:.1%}" for v in i95["coverageWilson95"])
        br = briers.get(key, m["rookieRoleBrier"])
        lines.append(f"| {label} | {m['totalMAE']:.1f} | {m['totalRMSE']:.1f} | {i80['coverage']:.1%} ({ci80}) | {i80['meanWidth']:.0f} | {i95['coverage']:.1%} ({ci95}) | {i95['meanWidth']:.0f} | {br:.3f} |")
    lines += [
        "",
        f"On this single 2018 holdout, the 3/15 base rate has slightly lower rookie-role Brier ({r['rookieRoleBrierComparison']['precutoffQBRoleRate_3of15']:.3f} vs {r['rookieRoleBrierComparison']['currentPooledRookieProbability']:.3f}) and total RMSE ({c['precutoffQBRoleRate_3of15']['totalRMSE']:.1f} vs {c['currentPooledRookieProbability']['totalRMSE']:.1f}), but worse total MAE ({c['precutoffQBRoleRate_3of15']['totalMAE']:.1f} vs {c['currentPooledRookieProbability']['totalMAE']:.1f}). With 16 quarterbacks in one test class, this is not enough evidence to select a change. Its total distribution is identical to unconditional QB donor resampling because the base rate matches the donor stratum share.",
        "",
        "## Strict rolling-origin comparison",
        "",
        "The expanded experiment uses recovered raw snap and combine files. For each draft year 2018–2021, five-year donor classes end at draftYear−5; the QB rookie-role classifier uses first-year outcomes only through the prior class. Compare position-only donors, the cutoff QB donor role rate, pooled role probabilities, and a fixed 50% shrinkage sensitivity. No held-out target outcomes enter fitting.",
        "",
        "| Draft year | QB donors / role-positive | Test QBs | Position-only RMSE | Cutoff role-rate RMSE | Pooled role-model RMSE | Half-shrink RMSE | Role Brier: rate / model |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    rolling = r["strictRollingOrigins"]
    for origin in rolling["years"]:
        mm = origin["metrics"]
        lines.append(f"| {origin['draftYear']} | {origin['nDonors']} / {origin['rolePositiveDonors']} | {origin['nTestQBs']} | {mm['positionOnly']['totalRMSE']:.1f} | {mm['precutoffQBRoleRate']['totalRMSE']:.1f} | {mm['pooledRoleModel']['totalRMSE']:.1f} | {mm['halfShrinkToQBRate']['totalRMSE']:.1f} | {mm['precutoffQBRoleRate']['rookieRoleBrier']:.3f} / {mm['pooledRoleModel']['rookieRoleBrier']:.3f} |")
    pooled = rolling["pooledAcrossFourDraftClasses"]
    lines.append(f"| **Pooled** | — | {pooled.get('pooledRoleModel', {}).get('n', 0)} | {pooled.get('positionOnly', {}).get('totalRMSE', float('nan')):.1f} | {pooled.get('precutoffQBRoleRate', {}).get('totalRMSE', float('nan')):.1f} | {pooled.get('pooledRoleModel', {}).get('totalRMSE', float('nan')):.1f} | {pooled.get('halfShrinkToQBRate', {}).get('totalRMSE', float('nan')):.1f} | {pooled.get('precutoffQBRoleRate', {}).get('rookieRoleBrier', float('nan')):.3f} / {pooled.get('pooledRoleModel', {}).get('rookieRoleBrier', float('nan')):.3f} |")
    lines += [
        "",
        f"Across four origin classes, the simple QB donor role rate beats the individual QB logistic model on pooled Brier ({pooled['precutoffQBRoleRate']['rookieRoleBrier']:.3f} vs {pooled['pooledRoleModel']['rookieRoleBrier']:.3f}), MAE ({pooled['precutoffQBRoleRate']['totalMAE']:.1f} vs {pooled['pooledRoleModel']['totalMAE']:.1f}), and RMSE ({pooled['precutoffQBRoleRate']['totalRMSE']:.1f} vs {pooled['pooledRoleModel']['totalRMSE']:.1f}). It is not best in every year and remains based on only four inspected classes. No later complete five-year holdout exists yet: draft year 2022 needs 2026 outcomes, which are not complete. Treat this as the next candidate for an untouched evaluation, not as a release-ready change. Class-level coverage, widths, and donor support are in the JSON.",
        "",
        "## Failed approaches and disposition",
        "",
        "- Widening intervals to target nominal coverage is not evidence-based and does not address the missing upper-tail trajectories.",
        "- A QB-only hierarchy, regularized model, or cohort bootstrap cannot be learned from one strict cohort. Resampling the 15 player rows would understate the between-cohort uncertainty that matters here.",
        "- Borrowing RB/WR or all-position trajectories to create QB ceilings has no evaluated evidence that their tails transfer to quarterbacks.",
        "- The available holdout supports no production change. Retain the empirical donor mechanism while marking QB high-end uncertainty unsupported; collect additional time-available cohorts and reserve untouched later classes before reconsidering.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python analytics/qb_uncertainty.py",
        "python -m unittest analytics.test_qb_uncertainty -v",
        "```",
        "",
        "Input SHA-256 hashes are recorded in `qb_uncertainty.json`.",
        "",
    ]
    REPORT.write_text("\n".join(lines))


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
