# Empirical five-year participation forecast

Executed2026-11-02. The installed forecast now samples actual five-year participation trajectories. It does not establish causal player value or causal changes in team wins.

## Strict2018 runtime

`five_year_strict_2018.json` contains 310 identified2013 combine participants and their2013–2017 annual scrimmage snaps and games with recorded snaps. All labels were complete before April2018.2012 is unavailable/header-only and is not interpreted as zero.22 unknown IDs are excluded. The runtime samples within broad position and rookie-role stratum using the shared-profile pooled rookie probability; one whole vector preserves observed within-person trajectory correlation. Games count positive recorded offensive, defensive or special-teams snaps, not official starts.

There is only one admissible donor cohort. A pre2018 internal chronological validation split is impossible. QB support is especially weak:15 donors, only3 with at least200 rookie scrimmage snaps. Donor resampling cannot create high-end career shapes absent from this small source cohort. ST donors measure participation and must not be treated as specialist quality predictions.

## Exact frozen2018 gameplay-probability holdout

This evaluates the same frozen2018 shared-profile pooled probabilities and conditional2013 donors on 287 identified nonspecialist2018 prospects, using outcomes2018–2022 only for evaluation. No2018 outcome enters the fit. It evaluates participation **before** the runtime's roster-opportunity adjustment, games cap, starts proxy or snaps-to-wins conversion. Those later mappings remain separate unvalidated assumptions.

- Total five-year snaps MAE: 1177.17; position-only donor baseline 1207.80.
- Total five-year snaps RMSE: 1467.80; baseline 1514.18.
-80% predictive interval coverage: 86.8%, mean width 3237.7 snaps.
-95% predictive interval coverage: 93.7%, mean width 4051.1 snaps.

Intervals are wide, and aggregate coverage does not establish subgroup calibration. QB95% coverage is75% on16 held-out cases, a material failure. The model is a measured empirical forecast with substantial limitations, not a fully validated five-year talent engine. Games-with-snaps arrays are source-backed but do not yet have a separate probability/interval calibration report.

| Position | Test N | Total-snap RMSE |95% interval coverage |
|---|---:|---:|---:|
| DB | 58 | 1525.59 | 91.4% |
| DL | 36 | 1169.72 | 97.2% |
| LB | 48 | 1523.30 | 87.5% |
| OL | 46 | 1808.89 | 97.8% |
| QB | 16 | 1981.38 | 75.0% |
| RB | 28 | 798.88 | 100.0% |
| TE | 16 | 1285.14 | 100.0% |
| WR | 39 | 1291.71 | 97.4% |

## Retrospective candidate comparison

Cohorts2013–2015 train (N906),2016 validates (N307),2017–2018 tests (N593). Five-year labels overlap forecast calendar dates, so this cohort split is explicitly retrospective and is not presented as a strict2017 model. Compare position-wide empirical donors, rookie-role-conditional donors, and regularized log1p multioutput ridge with correlated residual-trajectory sampling. Hyperparameters and method selection use validation total RMSE. Selected method: roleConditionalDonors; ridge alpha1000.0.400 predictive samples per person, fixed seeds. All candidates remain in the registry.

| Held-out method | Total-snap MAE | RMSE |80% coverage |95% coverage |
|---|---:|---:|---:|---:|
| positionDonors | 1207.62 | 1460.84 | 86.8% | 96.5% |
| roleConditionalDonors | 1151.52 | 1414.03 | 85.8% | 97.0% |
| log1pRidge | 1162.71 | 1432.36 | 75.4% | 90.9% |

Ridge complexity did not beat conditional donors on the stated validation criterion. Residual intervals are empirical approximations, not distribution-free coverage guarantees. Annual role-probability Brier scores, subgroup diagnostics and trajectory correlation matrices are in `five_year_research.json`.

## Label-available rolling-origin checks

For draft yearY, donor cohorts end atY−5, so their full five-year labels are observable by the draft. The separate rookie classifier only uses completed first-year outcomes throughY−1. These rolling experiments use unpooled probabilities and therefore must not be substituted for the exact pooled2018 gameplay holdout above.

| Forecast draft | Donor cohorts | Test N | Total-snap RMSE |95% coverage |
|---|---|---:|---:|---:|
| 2018 | 2013 | 287 | 1473.49 | 93.4% |
| 2019 | 2013,2014 | 325 | 1406.73 | 94.8% |
| 2020 | 2013,2014,2015 | 325 | 1367.03 | 97.5% |
| 2021 | 2013,2014,2015,2016 | 329 | 1315.74 | 97.9% |

Known-ID selection bias, original-publication archive gaps, era shifts, historical roster opportunities and limited support remain. Recent incomplete five-year cohorts are excluded rather than filled with fictitious seasons.2013–2025 snap sources match every completed regular-season schedule game; canceled games are not invented.

## Verification and reproduction

Seven focused checks pass in `five_year_test_results.txt`: cutoff availability, donor/observed-vector equality, unavailable2012 handling, rolling-origin cutoffs, frozen metric recomputation, retrospective disclosure and visible QB support failure. The strict runtime artifact SHA remained unchanged during the final benchmark work.

```sh
python analytics/five_year.py
python analytics/five_year_tests.py
```

Pinned Python dependencies are in `analytics/requirements.txt`. Research output includes private outcome/identifier tables; do not import those outcome stores into pre-draft clients. Only the strict2013 donor artifact is imported by the runtime simulation.
