# Does the score improve remaining-possession forecasts?

**The score improved forecasts in the late window and in the final minutes of both windows. The full-game result fell short of the predeclared replication threshold.** No runtime change followed.

The corrected play-by-play extraction kept 2,000 of 2,048 scheduled games and 46,726 regulation drive segments in 2010–2017. It excluded 35 games for final-score disagreements, 12 for clock failures, and one for a nonmonotone score. The weakest seasonal coverage was 248/256 games (96.9%). The five held-out origins included 1,248 games and 29,046 drive starts.

| Window | Games | Clock-only MSE | Clock plus score MSE | MSE change [95% interval] | MAE change [95% interval] |
|---|---:|---:|---:|---:|---:|
| 2013–2015 | 748 | 5.57235 | 5.57315 | +0.00080 [−0.01208, +0.01487] | −0.00087 [−0.00406, +0.00262] |
| 2016–2017 | 500 | 4.77840 | 4.76638 | −0.01203 [−0.02262, −0.00109] | −0.00427 [−0.00746, −0.00109] |

Changes are candidate minus baseline. The late window's MSE gain was 0.25%. Across individual origins, MSE changes were +0.00684, +0.01407, −0.01848, −0.00634 and −0.01780 from 2013 to 2017. The early window missed the requirement that its MSE interval be entirely below zero.

| Time remaining at drive start | 2013–2015 MSE, clock → clock plus score | 2016–2017 MSE, clock → clock plus score |
|---|---:|---:|
| Under 5 minutes | 0.6126 → 0.5609 | 0.6348 → 0.6092 |
| 5 to under 10 minutes | 1.4913 → 1.4635 | 1.5665 → 1.5292 |
| 10 to under 30 minutes | 3.5213 → 3.5229 | 3.3403 → 3.3248 |
| 30 to 60 minutes | 8.3600 → 8.3710 | 7.0239 → 7.0202 |

The final-five-minute MSE reduction was 8.4% early and 4.0% late. These clock-band results are descriptive. At exactly five minutes, fitted forecasts for a possession side leading by at least eight were 0.39–0.50 drives below the within-seven reference across the five origins. A deficit of at least eight was associated with 0.18–0.25 fewer drives. The 30-minute differences changed sign across origins.

The initial approximation produced MSE changes of +0.00073 [−0.01231, +0.01480] in 2013–2015 and −0.01235 [−0.02287, −0.00149] in 2016–2017. The pre-play scoreboard audit found 95 discrepancies across 46,726 drive starts, 23 of which crossed one of the model's score-band boundaries. Correcting the predictor left the evidence decision unchanged. Four targeted tests passed.

## What the test measures

The outcome was the count of later retained regulation drive segments after the first eligible possession play in each segment. The clock-only model had a piecewise linear curve with knots every five minutes. The candidate added smooth differences for the possession side trailing or leading by at least eight. It used the cumulative scoreboard carried forward from the rows strictly before the eligible possession play. Both models gave each game equal total weight. Each 2013–2017 forecast used the prior three seasons for training. The two windows had already been used to evaluate score forecasts.

The first analysis approximated the drive-start score by accumulating credits from completed corrected segments. The alignment check found occasional differences between segment credits and the live pre-play scoreboard. The code was amended to read the preceding play rows and count later anchors in play order. Both analyses use the same windows, fitted model, and decision thresholds. The corrected rerun evaluates the same holdouts. The original protocol and figures are preserved in `BOUNDARY_APPROXIMATION_PROTOCOL.md` and `boundary_approximation_results.json`.

The results apply to games that passed the reconciliation checks. They use the data provider's corrected fixed-drive grouping, which may include kneel-only or end-of-half segments. The pace measure is a count of later retained segments. It provides no estimate of how long a particular possession will last or what would happen under a different clock-management policy. The paired week intervals retain within-week dependence but omit dependence across weeks and uncertainty about future seasons. [nflreadr play-by-play documentation](https://nflreadr.nflverse.com/reference/load_pbp.html) · [nflfastR drive construction](https://github.com/nflverse/nflfastR/blob/master/R/helper_add_fixed_drives.R)

## Reproduce

Run from the repository root with NumPy, pandas and PyArrow installed.

```bash
archive_dir=$(mktemp -d)
for year in $(seq 2010 2017); do
  curl --fail --location --retry 2 \
    "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_${year}.parquet" \
    --output "${archive_dir}/${year}.parquet"
done
python analytics/scoring_pace/compare_pace.py "$archive_dir"
python -m unittest discover -s analytics/scoring_pace -v
```
