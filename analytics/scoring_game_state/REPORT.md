# NFL score forecasts with simulated game state

**Decision: retain the rounded-normal benchmark.** The clock- and score-conditioned drive model worsened joint energy and total CRPS in both windows. Its 90% intervals covered too many observed scores, and its team-season point totals were too dispersed relative to the benchmark.

1,752 of 1,792 archived games passed reconciliation and clock checks. The exclusions comprised 28 final-score mismatches, 11 invalid clocks, and one nonmonotone scoring sequence. The lowest season coverage was 248/256. All 1,280 scheduled fixtures in the five origins were assessed with 4,096 draws per model. The rounded-normal benchmark reproduced all previously published results exactly across the two windows and five individual origins.

| Metric | 2013–2015 baseline | 2013–2015 game state | 2016–2017 baseline | 2016–2017 game state |
|---|---:|---:|---:|---:|
| Joint energy | 8.80070 | 8.85283 | 8.49770 | 8.53993 |
| Total CRPS | 7.87445 | 7.89042 | 7.77349 | 7.78091 |
| Margin CRPS | 7.95435 | 8.02813 | 7.49386 | 7.56406 |
| Home CRPS | 5.82441 | 5.85242 | 5.54358 | 5.56685 |
| Away CRPS | 5.39237 | 5.42791 | 5.30207 | 5.31888 |
| Total MAE | 11.189 | 11.194 | 10.939 | 10.959 |
| Margin MAE | 11.041 | 11.057 | 10.385 | 10.382 |
| Home MAE | 8.174 | 8.186 | 7.744 | 7.742 |
| Away MAE | 7.643 | 7.644 | 7.458 | 7.472 |
| Shutout Brier | 0.015708 | 0.015604 | 0.026638 | 0.026643 |
| Predicted shutout rate | 3.206% | 2.809% | 2.947% | 2.462% |
| Observed shutout rate | 1.562% | 1.562% | 2.734% | 2.734% |
| Total 90% coverage | 91.67% | 94.01% | 90.04% | 91.80% |
| Margin 90% coverage | 90.23% | 93.62% | 91.41% | 94.73% |
| Home 90% coverage | 89.19% | 93.49% | 91.60% | 93.95% |
| Away 90% coverage | 92.45% | 95.83% | 92.38% | 95.31% |
| Mean team-season wins SD | 2.776 | 2.707 | 2.778 | 2.697 |
| Mean team-season points SD | 54.526 | 60.620 | 54.035 | 58.503 |
| Same-team residual dependence | 0.1122 | 0.0946 | 0.1104 | 0.0935 |
| Predicted tie rate | 0.320% | 0.409% | 0.319% | 0.397% |
| Observed tie rate | 0.260% | 0.260% | 0.391% | 0.391% |
| Predicted team score of one point | 0.0000% | 0.0026% | 0.0000% | 0.0018% |

## Paired differences by assessment window

Differences are candidate minus baseline. Coverage changes are in percentage points. Brackets show the conditional 95% paired week-bootstrap intervals.

| Metric | 2013–2015 difference [interval] | 2016–2017 difference [interval] |
|---|---:|---:|
| Joint energy | +0.0521 [+0.0252, +0.0821] | +0.0422 [+0.0180, +0.0660] |
| Total CRPS | +0.0160 [-0.0104, +0.0418] | +0.0074 [-0.0141, +0.0302] |
| Margin CRPS | +0.0738 [+0.0416, +0.1057] | +0.0702 [+0.0505, +0.0902] |
| Shutout Brier | -0.000104 [-0.000186, -0.000010] | +0.000004 [-0.000136, +0.000160] |
| Total coverage | +2.34 [+1.17, +3.64] | +1.76 [+0.79, +2.75] |
| Margin coverage | +3.39 [+2.23, +4.54] | +3.32 [+2.14, +4.54] |

## Adoption checks

Joint energy and margin CRPS worsened in both windows, with paired intervals above zero. Total CRPS worsened at the point estimates, with both intervals spanning zero. The shutout Brier score improved in the early window and narrowly missed the no-worse gate in the late window. All four 90% coverage guardrails failed in both windows. The candidate's mean team-season points SD rose 11.2% in 2013–2015 and 8.3% in 2016–2017, exceeding the 5% tolerance. Wins SD fell 2.5% and 2.9%, within tolerance, and same-team residual dependence stayed positive. All non-total CRPS and MAE changes met the 1% guardrails. There were no observed one-point team totals.

The previous unconditional drive candidate also missed the joint energy, coverage, and points dispersion gates. This pilot changes both the drive template and the credit law. A matched comparison with the same templates and an unconditional credit law would be needed to isolate the effect of allowing the score to feed back into subsequent credits. Annual metrics, fit counts, source hashes, and individual checks are in `results.json`. Six state-model tests, five prior drive tests, and four rounded-normal benchmark tests passed.

## Model and limits

Each rolling origin used the preceding three seasons of reconciled nflverse play-by-play. A simulated game sampled an ordered historical drive template containing the possession side and clock period. On each drive, the simulator used the possession side's current lead or deficit, computed from earlier simulated drives. The fitted credit law distinguished the first half, second half before the final ten minutes, and final ten minutes. Within each period it distinguished a deficit of eight or more, a margin within seven, and a lead of eight or more. Partial pooling added 100 pseudo-drives from the side's unconditional distribution. The base matchup adjustment, shared team-season shocks, and approximate overtime treatment followed the earlier drive comparison. [nflverse play-by-play data documentation](https://nflreadr.nflverse.com/reference/load_pbp.html) · [nflfastR drive construction](https://github.com/nflverse/nflfastR/blob/master/R/helper_add_fixed_drives.R)

Historical templates provide the possession order and coarse clock independently of the simulated scores. The pilot therefore evaluates score feedback in drive point credits only. Teams cannot run down the clock or change the simulated possession sequence in response to the score. The drive state tables can also pick up persistent team strength, so differences between the cells do not establish a causal effect of leading or trailing. A corrected drive segment can include extra points and defensive or special-teams credits. Season dispersion measures are predictive standard deviations across simulated seasons on the observed schedules. The adoption screen compares those standard deviations with the established benchmark.

The paired intervals resample entire scheduled weeks within each origin season. They measure variation over the observed weeks conditional on the fitted model and simulation draws. They omit uncertainty from training data, dependence across weeks, and variation across unseen seasons. The two assessment windows were previously inspected and are not a fresh validation sample. CRPS and energy score use a loss convention with lower scores preferred. [Gneiting and Raftery, 2007](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)

## Reproduce

Run from the repository root with Python, NumPy, pandas, SciPy, and PyArrow installed.

```bash
archive_dir=$(mktemp -d)
for year in $(seq 2010 2016); do
  curl --fail --location --retry 2 \
    "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_${year}.parquet" \
    --output "${archive_dir}/${year}.parquet"
done
python analytics/scoring_game_state/compare_state.py "$archive_dir"
python -m unittest discover -s analytics/scoring_game_state -v
python -m unittest discover -s analytics/scoring_possessions -v
python -m unittest discover -s analytics -p test_score_marginal.py -v
```
