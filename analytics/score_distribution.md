# Shutout hurdle score distribution experiment

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
| currentCorrelatedNormal | 512 | 10.893 | 10.371 | 7.747 | 7.499 | 0.02678 | 3.882% / 2.734% | 91.0% | 91.6% |
| twoPartHurdle | 512 | 10.894 | 10.401 | 7.739 | 7.501 | 0.02673 | 1.562% / 2.734% | 89.8% | 90.6% |

Shutout probability-only Brier: 0.02673; log loss: 0.12904.

## Known-exposed retrospective diagnostic (2018–25)

| Model | Games | Total MAE | Margin MAE | Total CRPS | Margin CRPS | Shutout Brier | Predicted / observed shutouts | 90% total coverage | 90% margin coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| currentCorrelatedNormal | 2127 | 10.994 | 10.719 | 7.818 | 7.744 | 0.02039 | 3.169% / 2.069% | 91.3% | 90.4% |
| twoPartHurdle | 2127 | 10.993 | 10.715 | 7.800 | 7.748 | 0.02026 | 2.083% / 2.069% | 91.2% | 90.2% |

Shutout probability-only Brier: 0.02026; log loss: 0.10070.

## Gameplay parameters

The research-only parameters are recorded in `score_distribution.json`. The deployed comparator uses the 44.87109375 mean-total override, independent team-season shocks, and independent tie-resolution and overtime-winner draws. Historical assessment laws are refitted using only scores through the stated cutoff. Sampling uses one keyed Bernoulli shutout decision, then draws from the current bivariate normal score law conditional on the selected branch. In exact engine form, reject and redraw score-law samples until either one team scores zero (shutout branch) or both score positive (non-shutout branch). The evaluation uses Monte Carlo draws; no runtime changes are included here.

## Decision and limits

Candidate remains research-only. Compare the frozen 2016–17 metrics below; known-exposed 2018–25 results cannot justify adoption. The retrospective comparator now uses the runtime total override, independent season shocks, and independent tie-resolution/winner draws. No runtime or threshold changes.

NFL score forecasting research models scoring events because multiple football scoring outcomes produce a discrete score distribution ([Baker & McHale, 2013](https://doi.org/10.1016/j.ijforecast.2012.07.002)). Two-part count models separate threshold probability from the conditional positive distribution ([Mullahy, 1986](https://doi.org/10.1016/0304-4076(86)90002-3)). Proper scoring rules support evaluating event probabilities with Brier/log loss and outcome distributions with CRPS and interval coverage ([Gneiting & Raftery, 2007](https://doi.org/10.1198/016214506000001437)).

The post-2017 results are retrospective because they have already been examined elsewhere in this project. The final pre-2018 test contains only two seasons and few shutouts. In 2018–25, the source has 2,127 regular-season games because the 2022 Bills–Bengals game was canceled and not replayed. Neither test proves future calibration, causality, or alternate-history accuracy. No release threshold was changed.

Additional limits:

- The candidate has no team/season shutout covariates and no position or draft treatment effect.
- Per-game prior-strength forecasts condition on the actual preceding season, not a frozen five-year simulated path; season-shared dependence does not affect these marginal game metrics.
- Pre-2018 assessment uses a historically refitted residual-normal comparator; the exposed diagnostic uses the deployed runtime score law with team-season shocks integrated out.
- Post-2017 outcomes have been inspected in prior project diagnostics; chronology prevents leakage but does not make them an untouched test.
- The 2016–17 assessment was previously reported; this comparator repair is a rerun of a time-separated test, not a new untouched holdout. It has only two seasons and low shutout counts.
- Conditional distributions inherit the existing normal score model and its limitations.
- A fit to 2000–2017 assumes the shutout relationship is stable; future NFL scoring regimes may differ.
- No causal draft effect or alternate-history truth is identified.
