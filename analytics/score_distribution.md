# Shutout hurdle score distribution experiment

> **Current-runtime comparison limitation (12 November 2026):** The retrospective `runtime_score_law()` reads the base `model.json` total-score mean43.54895, omitting the application’s recency override44.87109 and team-season shocks. Its alias normalization also differs from the canonical runtime. Consequently, the label `currentCorrelatedNormal` below means a research approximation, not an exact replay of the current application. Mixed/small gains from this experiment do not justify production adoption. The source and parameters were not changed during the fixed gauntlet.

## Protocol

The shutout rate window was selected on 2014–15 (training through 2013): **trailing3** by lowest Brier score. The frozen pre-2018 test is 2016–17 (fit through 2015). After that test, selected parameters are refit through 2017 for a known-exposed retrospective check on 2018–25. The 2026 season is incomplete and excluded.

The candidate uses an intercept-only empirical shutout probability estimated from the selected pre-cutoff window. It then draws from the existing correlated normal score model conditional on that branch: zero scores for the shutout branch, two positive scores for the other branch. This makes an explicit, empirically estimated hurdle without clipping or forcing a desired shutout rate.

## Hurdle form validation (2014–15)

| Form | Brier | Log loss | Predicted rate | Observed rate |
|---|---:|---:|---:|---:|
| expanding | 0.01743 | 0.09168 | 3.027% | 1.758% |
| trailing3 | 0.01727 | 0.08847 | 1.823% | 1.758% |
| trailing5 | 0.01730 | 0.08928 | 2.344% | 1.758% |
| trailing10 | 0.01734 | 0.08996 | 2.578% | 1.758% |

## Frozen final pre-2018 test (2016–17)

| Model | Games | Total MAE | Margin MAE | Total CRPS | Margin CRPS | Shutout Brier | Predicted / observed shutouts | 90% total coverage | 90% margin coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| currentCorrelatedNormal | 512 | 10.938 | 10.405 | 7.755 | 7.512 | 0.02677 | 3.910% / 2.734% | 90.6% | 92.0% |
| twoPartHurdle | 512 | 10.881 | 10.411 | 7.723 | 7.497 | 0.02673 | 1.562% / 2.734% | 89.6% | 91.0% |

Shutout probability-only Brier: 0.02673; log loss: 0.12904.

## Known-exposed retrospective diagnostic (2018–25)

| Model | Games | Total MAE | Margin MAE | Total CRPS | Margin CRPS | Shutout Brier | Predicted / observed shutouts | 90% total coverage | 90% margin coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| currentCorrelatedNormal | 2127 | 11.009 | 10.720 | 7.867 | 7.745 | 0.02031 | 2.723% / 2.069% | 91.2% | 86.0% |
| twoPartHurdle | 2127 | 10.999 | 10.720 | 7.853 | 7.747 | 0.02026 | 2.083% / 2.069% | 91.0% | 85.9% |

Shutout probability-only Brier: 0.02026; log loss: 0.10070.

## Gameplay parameters

The proposed runtime parameters are recorded in `score_distribution.json`: the current score-law parameters fitted through 2017 plus a shutout rate of 2.083% estimated from 2015–17. Sampling uses one keyed Bernoulli shutout decision, then draws from the current bivariate normal score law conditional on the selected branch. In exact engine form, reject and redraw score-law samples until either one team scores zero (shutout branch) or both score positive (non-shutout branch). The evaluation uses Monte Carlo draws; no runtime changes are included here.

## Decision and limits

The three-season intercept-only hurdle wins 2014–15 Brier selection. On the 2016–17 final test its shutout Brier is slightly better but log loss is worse than the normal law; the exposed 2018–25 diagnostic improves shutout probability scores and lowers predicted shutouts toward observed frequency. Score-distribution gains are small/mixed, and this known-exposed diagnostic is not independent evidence. Keep it a candidate for review; no adoption claim.

NFL score forecasting research models scoring events because multiple football scoring outcomes produce a discrete score distribution ([Baker & McHale, 2013](https://doi.org/10.1016/j.ijforecast.2012.07.002)). Two-part count models separate threshold probability from the conditional positive distribution ([Mullahy, 1986](https://doi.org/10.1016/0304-4076(86)90002-3)). Proper scoring rules support evaluating event probabilities with Brier/log loss and outcome distributions with CRPS and interval coverage ([Gneiting & Raftery, 2007](https://doi.org/10.1198/016214506000001437)).

The post-2017 results are retrospective because they have already been examined elsewhere in this project. The final pre-2018 test contains only two seasons and 14 shutouts. In 2018–25, the source has 2,127 regular-season games because the 2022 Bills–Bengals game was canceled and not replayed. Neither test proves future calibration, causality, or alternate-history accuracy. No release threshold was changed.
