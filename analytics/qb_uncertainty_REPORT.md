# QB uncertainty research

Executed 2026-11-12 from the frozen analytical artifacts. This is a bounded diagnostic; it does not change the runtime model.

## Evidence and cutoff

The strict donor pool contains 15 identified QBs from the 2013 cohort, whose five annual labels were available by 2018-03-01. Only 3 donors crossed 200 rookie scrimmage snaps. The frozen 2018 holdout has 16 QBs and was evaluated on 2018–2022 outcomes. There is no second fully observable pre-2018 QB cohort in the strict artifact, so between-cohort uncertainty cannot be estimated.

Donor five-year total snaps range from 0 to 1965. 4 of 16 holdout QBs exceed the highest donor total. That is a support failure; changing an interval multiplier cannot supply missing career trajectories.

## Candidate results

All candidates use the same real 2013 QB vectors. The empirical role-rate candidate uses 3/15=0.20 as the probability of drawing from the three rookie-role donors; this equals the unconditional empirical QB donor distribution. Intervals use the discrete weighted donor CDF, with no extrapolation.
The Wilson coverage intervals treat the 16 QBs as independent Bernoulli cases and do not account for their shared draft-class context; they are descriptive only.

| Candidate | Total MAE | Total RMSE | 80% coverage (Wilson 95% CI) | 80% width | 95% coverage (Wilson 95% CI) | 95% width | Rookie-role Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| Current pooled probabilities | 1233.9 | 1979.7 | 75.0% (50.5%, 89.8%) | 1387 | 75.0% (50.5%, 89.8%) | 1965 | 0.233 |
| Pre-cutoff QB role rate (3/15) | 1240.8 | 1967.0 | 75.0% (50.5%, 89.8%) | 1485 | 75.0% (50.5%, 89.8%) | 1965 | 0.228 |
| Unconditional QB donors | 1240.8 | 1967.0 | 75.0% (50.5%, 89.8%) | 1485 | 75.0% (50.5%, 89.8%) | 1965 | 0.228 |

On this single 2018 holdout, the 3/15 base rate has slightly lower rookie-role Brier (0.228 vs 0.233) and total RMSE (1967.0 vs 1979.7), but worse total MAE (1240.8 vs 1233.9). With 16 quarterbacks in one test class, this is not enough evidence to select a change. Its total distribution is identical to unconditional QB donor resampling because the base rate matches the donor stratum share.

## Strict rolling-origin comparison

The expanded experiment uses recovered raw snap and combine files. For each draft year 2018–2021, five-year donor classes end at draftYear−5; the QB rookie-role classifier uses first-year outcomes only through the prior class. Compare position-only donors, the cutoff QB donor role rate, pooled role probabilities, and a fixed 50% shrinkage sensitivity. No held-out target outcomes enter fitting.

| Draft year | QB donors / role-positive | Test QBs | Position-only RMSE | Cutoff role-rate RMSE | Pooled role-model RMSE | Half-shrink RMSE | Role Brier: rate / model |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 15 / 3 | 16 | 1967.0 | 1967.0 | 2041.1 | 1998.0 | 0.228 / 0.313 |
| 2019 | 33 / 7 | 17 | 1348.1 | 1348.1 | 1482.3 | 1403.0 | 0.214 / 0.285 |
| 2020 | 45 / 9 | 17 | 1981.7 | 1981.7 | 1845.2 | 1903.4 | 0.181 / 0.163 |
| 2021 | 62 / 13 | 16 | 1563.7 | 1563.7 | 1594.6 | 1560.1 | 0.225 / 0.244 |
| **Pooled** | — | 66 | 1735.0 | 1735.0 | 1751.9 | 1731.5 | 0.212 / 0.250 |

Across four origin classes, the simple QB donor role rate beats the individual QB logistic model on pooled Brier (0.212 vs 0.250), MAE (1206.6 vs 1290.1), and RMSE (1735.0 vs 1751.9). It is not best in every year and remains based on only four inspected classes. No later complete five-year holdout exists yet: draft year 2022 needs 2026 outcomes, which are not complete. Treat this as the next candidate for an untouched evaluation, not as a release-ready change. Class-level coverage, widths, and donor support are in the JSON.

## Failed approaches and disposition

- Widening intervals to target nominal coverage is not evidence-based and does not address the missing upper-tail trajectories.
- A QB-only hierarchy, regularized model, or cohort bootstrap cannot be learned from one strict cohort. Resampling the 15 player rows would understate the between-cohort uncertainty that matters here.
- Borrowing RB/WR or all-position trajectories to create QB ceilings has no evaluated evidence that their tails transfer to quarterbacks.
- The available holdout supports no production change. Retain the empirical donor mechanism while marking QB high-end uncertainty unsupported; collect additional time-available cohorts and reserve untouched later classes before reconsidering.

## Reproduction

```sh
python analytics/qb_uncertainty.py
python -m unittest analytics.test_qb_uncertainty -v
```

Input SHA-256 hashes are recorded in `qb_uncertainty.json`.
