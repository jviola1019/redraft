# Discrete score marginal recalibration

The candidate remains research-only. It improved combined-score CRPS in both chronological windows and retained joint-season dependence. It failed the predeclared 2016–2017 shutout Brier criterion. The engine and all release gates retain their existing versions and thresholds.

## Fresh runtime baseline

Each of CLE, KC, NE and SF ran 256 paired five-season replicates through the production runtime loader. The baseline branch is shared across those four runs, so the identical league distributions are one scoring result repeated across four gate rows.

| Diagnostic | Observed 2018–2022 | Simulated mean | Central simulated 95% range |
|---|---:|---:|---:|
| Points per game, both teams | 46.290 | 45.051 | 44.273–45.985 |
| Team scores of zero | 1.030% | 1.610% | 1.105%–2.210% |

The baseline measures the proportion of team scores of zero. The chronological research measures a different denominator, the proportion of games with a shutout. Each baseline configuration, seed, simulated metric, flag, precision result and source hash is saved in the accompanying baseline JSON.

## Rolling-origin comparison

The fixed protocol ran 4,096 joint season draws at each origin. The score law refits through the preceding season only. Both arms share the same latent margin, total and per-team season shocks. The recalibration ranks each latent side score in a model-implied mixture of normal distributions over recent prior matchups, then maps its rank to a discrete empirical side score from the previous three seasons. The overtime rule is shared. The plausible score support follows observations, with one-point team scores omitted and the upper support limited by the short history. The rolling comparator refits the runtime score structure with historical least squares. The separate 2018–2022 baseline uses the unmodified production model artifacts.

| Window | Metric | Rounded normal | Discrete marginals |
|---|---|---:|---:|
| 2013–2015 | Combined CRPS | 7.87445 | 7.87029 |
| 2013–2015 | Signed margin CRPS | 7.95435 | 7.95485 |
| 2013–2015 | Home CRPS | 5.82441 | 5.81818 |
| 2013–2015 | Away CRPS | 5.39237 | 5.38839 |
| 2013–2015 | Shutout Brier | 0.015708 | 0.015459 |
| 2013–2015 | Predicted shutouts, observed 1.563% | 3.206% | 1.965% |
| 2013–2015 | Same-team signed margin residual correlation | 0.1122 | 0.1111 |
| 2016–2017 | Combined CRPS | 7.77349 | 7.75749 |
| 2016–2017 | Signed margin CRPS | 7.49386 | 7.48672 |
| 2016–2017 | Home CRPS | 5.54358 | 5.53344 |
| 2016–2017 | Away CRPS | 5.30207 | 5.29140 |
| 2016–2017 | Shutout Brier | 0.026638 | 0.026765 |
| 2016–2017 | Predicted shutouts, observed 2.734% | 2.947% | 1.527% |
| 2016–2017 | Same-team signed margin residual correlation | 0.1104 | 0.1094 |

All MAE, interval coverage and team-season dispersion guardrails passed. Mean signed margin bias moved from +0.123 to +0.316 in the earlier window and from −0.043 to −0.223 later. Bias, MAE, coverage and joint-season dispersion are available for every origin in the results JSON. The shutout criterion blocks promotion, so the candidate did not run the secondary five-season release replay. These are previously examined years, and the results cannot establish future scoring calibration.

The fixture suite checks that changing origin and later scores leaves the fit and forecast unchanged. It checks shared team shocks, distinct directional fixture innovations, plausible integer output, positive shutout support, identity under paired forecast reruns, and hand-computed metric arithmetic.

```bash
python analytics/score_marginal.py
python -m unittest discover -s analytics -p test_score_marginal.py -v
node analytics/simulation_diagnostics.mjs 256 CLE
node analytics/simulation_diagnostics.mjs 256 KC
node analytics/simulation_diagnostics.mjs 256 NE
node analytics/simulation_diagnostics.mjs 256 SF
```
