# NFL scoring from historical drive segments

**Do not adopt.** The drive candidate improved the shutout Brier score in both windows. It worsened the joint energy score in both windows, failed every coverage guardrail, and overstated team-season scoring dispersion relative to the established baseline.

Of 4,344 archived games, 4,295 passed reconciliation. The 49 exclusions were 47 final-score mismatches and two nonmonotone boundary-score sequences. The lowest training-season coverage was 249/256 (97.3%), above the 95% gate. The holdout score comparison used all 768 games in 2013–2015 and all 512 in 2016–2017 from the project games table. At five rolling origins, the fitted drive histories contained 751–757 games and averaged 11.55–11.86 modeled drive segments per side. Home and away drive counts had correlations of 0.806–0.832.

| Metric | 2013–2015 baseline | 2013–2015 drives | 2016–2017 baseline | 2016–2017 drives |
|---|---:|---:|---:|---:|
| Joint energy score | 8.80070 | 8.83965 | 8.49770 | 8.52372 |
| Total CRPS | 7.87445 | 7.89374 | 7.77349 | 7.76930 |
| Margin CRPS | 7.95435 | 8.00325 | 7.49386 | 7.56550 |
| Home CRPS | 5.82441 | 5.83679 | 5.54358 | 5.55891 |
| Away CRPS | 5.39237 | 5.42341 | 5.30207 | 5.31234 |
| Shutout Brier | 0.015708 | 0.015521 | 0.026638 | 0.026598 |
| Predicted games with a shutout | 3.206% | 2.392% | 2.947% | 2.202% |
| Observed games with a shutout | 1.562% | 1.562% | 2.734% | 2.734% |
| Total MAE | 11.189 | 11.184 | 10.939 | 10.931 |
| Margin MAE | 11.041 | 11.047 | 10.385 | 10.362 |
| Home MAE | 8.174 | 8.177 | 7.744 | 7.741 |
| Away MAE | 7.643 | 7.651 | 7.458 | 7.449 |
| Total 90% coverage | 91.67% | 94.01% | 90.04% | 91.99% |
| Margin 90% coverage | 90.23% | 92.84% | 91.41% | 94.34% |
| Home 90% coverage | 89.19% | 92.84% | 91.60% | 94.34% |
| Away 90% coverage | 92.45% | 95.57% | 92.38% | 95.31% |
| Mean team-season wins SD | 2.776 | 2.706 | 2.778 | 2.706 |
| Mean team-season points SD | 54.526 | 59.160 | 54.035 | 58.559 |
| Same-team residual dependence | 0.1122 | 0.0954 | 0.1104 | 0.0938 |
| Predicted tie rate | 0.320% | 0.425% | 0.319% | 0.398% |
| Observed tie rate | 0.260% | 0.260% | 0.391% | 0.391% |
| Predicted team score of one | 0.0000% | 0.0046% | 0.0000% | 0.0013% |

The candidate missed the early total CRPS gate and passed it in the late window. The margin, home and away CRPS and every MAE met the 1% tolerances. Mean team-season wins SD fell 2.5–2.6%, within tolerance, and same-team signed margin residual dependence stayed positive in both windows. The measure is a standardized cross-game residual product. Mean team-season points SD rose 8.50% and 8.37%, above the predeclared 5% cap. The candidate overpredicted early shutouts and underpredicted late shutouts. No assessment game featured a one-point team total. A small simulated mass at one point reflects the unconditional resampling of rare single-point segment credits. Coverage rose to 91.99–95.57% for nominal 90% intervals. The higher coverage and inflated points SD coexist with worse multivariate predictive accuracy.

The annual metrics, including score bias and individual screen outcomes, are in `results.json`. The candidate was fitted once per origin under the frozen protocol. The numerical rounded-normal results match the previously published baseline exactly wherever both experiments record the same metric. Five experiment tests and four established baseline tests passed.

## Method

The experiment compares rounded-normal score draws with a compound drive-segment model. Each simulated game samples a historical pair of regulation drive counts. Each side samples paired points credited to the possession team and its opponent from separate home and away category laws. The law tilts toward the existing expected matchup margin and uses the same persistent team-season shocks as the baseline. Both arms use the same simulated tie-decision uniforms and the existing approximate overtime rule. The comparator is the refitted chronological baseline used by the discrete-marginal experiment.

The source is the archived nflverse play-by-play parquet for 2001–2017. The extraction uses the producer's corrected drive identifiers and cumulative scoring fields, reconciled to the project games table. The archived input SHA-256 values and loss counts are in `results.json`. Rolling-origin forecasts condition on the actual preceding season and assess known regular-season schedules. The two test windows were previously examined.

A drive point pair can include PATs, defensive or special-teams points, and possibly multiple events depending on the producer's segment boundaries. A valid reconciliation certifies the total score, while the team-of-possession assignment still depends on the segment convention. The model assumes independence between segments conditional on the sampled pace, matchup strength and shared team shocks. It has no game clock, drive sequence, field position or game-state policy. The fitted margin shock is the comparator's approximation. Season-win and point SDs describe predictive variability on the historical schedules. The experiment does not evaluate simulated playoff or draft paths.

The approach is motivated by published NFL score modeling using discrete scoring events. The categorical tilt and paired pace sampler are specific to this experiment. Joint energy score and univariate CRPS have proper-scoring-rule foundations. [Baker and McHale, 2013](https://doi.org/10.1016/j.ijforecast.2012.07.002) · [Gneiting and Raftery, 2007](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf) · [nflverse loader](https://nflreadr.nflverse.com/reference/load_pbp.html) · [nflfastR drive construction](https://github.com/nflverse/nflfastR/blob/master/R/helper_add_fixed_drives.R)

## Reproduce

From the repository root, with NumPy, pandas, SciPy and PyArrow available:

```bash
archive_dir=$(mktemp -d)
for year in $(seq 2001 2017); do
  curl --fail --location --retry 2 \
    "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_${year}.parquet" \
    --output "${archive_dir}/${year}.parquet"
done
python analytics/scoring_possessions/compare.py "$archive_dir"
python -m unittest discover -s analytics/scoring_possessions -v
```

## Candidate divided by baseline

| Metric | 2013–2015 | 2016–2017 |
|---|---:|---:|
| Joint energy | 1.00443 | 1.00306 |
| Total CRPS | 1.00245 | 0.99946 |
| Margin CRPS | 1.00615 | 1.00956 |
| Home CRPS | 1.00212 | 1.00277 |
| Away CRPS | 1.00576 | 1.00194 |
| Total MAE | 0.99954 | 0.99927 |
| Margin MAE | 1.00058 | 0.99780 |
| Home MAE | 1.00040 | 0.99966 |
| Away MAE | 1.00099 | 0.99878 |
| meanTeamWinsSd | 0.97460 | 0.97419 |
| meanTeamPointsSd | 1.08498 | 1.08372 |
| Shutout Brier | 0.98811 | 0.99848 |

Each rolling origin uses only earlier seasons. A previously scored season can enter training at a later origin once its outcomes are available.
