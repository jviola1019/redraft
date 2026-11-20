# QB five-year chronological hindcast — 20 November 2026

The annual-transition candidate does not demonstrate a reliable five-year CRPS improvement over persistence. The paired estimate is −2.88 snaps, with a cohort-stratified player-bootstrap 95% interval [−38.36, 29.61]. Production, gates, and thresholds remain unchanged. These cohorts were previously exposed in other research; this is a reconstructed historical forecast, not a new untouched test.

## Forecast boundaries

| Draft origin | Cutoff (UTC) | Last fitted outcome | Conservative label availability | Panel / transition rows | Rookie QBs | Assessed QBs | Five-year outcome window | Full label availability |
|---|---|---:|---|---:|---:|---:|---|---|
| 2016 | 2016-04-28T00:00:00Z | 2015 | 2016-03-01 | 227 / 122 | 45 | 17 | 2016–2020 | 2021-03-01 |
| 2017 | 2017-04-27T00:00:00Z | 2016 | 2017-03-01 | 303 / 181 | 62 | 15 | 2017–2021 | 2022-03-01 |

Use the existing state-only, zero-shrinkage transition candidate, selected by exact next-year CRPS on 2015 outcomes from transitions ending by 2014. Those selection labels are conservatively available by 1 March 2016, before both origins. Refit using transitions ending by 2015 or 2016 respectively. No 2016+ assessment outcome enters parameter selection. Poisoning later outcomes leaves both selection and origin-specific draws invariant.

Both candidates begin with the same sampled rookie snap counts drawn from known-ID QB rookie seasons available at the origin: 45 rookie QBs for 2016, 62 for 2017. The initialization is unconditional within QB, with empirical role rates 20.00% and 20.97%. It does not borrow the combine classifier selected at a later date. Persistence repeats that sampled rookie count across five seasons; it never conditions on a target’s actual rookie snaps. The transition candidate propagates the existing four-state empirical annual rule. Each origin uses 8,192 paired paths.

Scale both candidates’ annual snaps by target schedule length / 16; only the 2021 season in the 2017 horizon changes. Actual recorded snaps are never scaled. Evaluation files are loaded separately from the filtered fit tables.

## Five-year total results

| Cohort | Forecast | n | CRPS | MAE | RMSE | 80% coverage / mean width | 95% coverage / mean width |
|---|---|---:|---:|---:|---:|---|---|
| Combined | transition | 32 | 745.65 | 1187.91 | 1588.17 | 26/32 / 3127.47 | 32/32 / 4871.59 |
| Combined | persistence | 32 | 748.53 | 1187.61 | 1589.02 | 29/32 / 4234.67 | 32/32 / 5213.65 |
| 2016 | transition | 17 | 808.97 | 1254.14 | 1722.77 | 14/17 / 3097.00 | 17/17 / 4843.00 |
| 2016 | persistence | 17 | 815.97 | 1248.21 | 1724.23 | 14/17 / 4210.00 | 17/17 / 4945.00 |
| 2017 | transition | 15 | 673.90 | 1112.86 | 1420.29 | 12/15 / 3162.00 | 15/15 / 4904.00 |
| 2017 | persistence | 15 | 672.11 | 1118.92 | 1420.31 | 15/15 / 4262.62 | 15/15 / 5518.12 |

The combined MAEs are nearly identical. Transition intervals are narrower at 95%, but both cover all 32 cases; these small-sample rates do not establish calibration. At 80%, transition covers 26/32 and persistence 29/32. The interval scores, annual-age metrics, cohort-level paired bootstrap intervals, three additional fixed-seed diagnostics, and observed versus simulated annual correlation matrices are in the JSON. Lower CRPS is preferable; the bootstrap estimates condition on these empirical fits and resample players within each of the two origins 5,000 times. It cannot measure uncertainty across eras or refitting uncertainty.

## Interpretation and limits

The gain from annual conditional forecasting did not transfer convincingly to the full five-year rookie target under this initialization. A small average CRPS difference with a bootstrap interval crossing zero does not justify promotion. Persistence is a serious baseline here because it retains perfect path dependence, while first-order state transitions recombine different people and discard persistent latent ability and team context. Correlation matrices are diagnostics, not joint-calibration proofs.

All 32 cases are identifiable combine participants: 17 from 2016, 15 from 2017. Unknown-ID targets are explicitly listed in the JSON; known IDs absent from fully reconciled annual files have zero recorded NFL snaps. This does not imply retirement, injury, or exclusion from all football. Source-season coverage reconciles all regular games. Original publication timestamps are unavailable; March 1 label dates and pre-draft combine availability are reconstructed. Selection bias remains.

A fair completed five-year donor comparison is unavailable at these origins: even the 2013 cohort is incomplete before 2018. Using its completed trajectories would supply future labels. This experiment does not add a causal wins model or support personalized rookie forecasts. No production model or acceptance threshold is changed.

## Reproduction and checks

```bash
python analytics/qb_five_year_hindcast.py --root "$PWD" --out analytics
RD_ROOT="$PWD" RD_QB_OUT="$PWD/analytics" python analytics/test_qb_five_year_hindcast.py
```

Five regression checks pass: efficient empirical CRPS equals the pairwise finite-mixture formula; chronological cutoffs and executed poisoning checks; saved metrics and bootstrap reconstruct; actual totals retain unscaled integer counts; no promotion and current source/script hashes. The script writes only to its explicit output directory. Its source hashes cover the existing transition implementation, cohort/source loader, scorer, combine, schedules, and 2013–2021 snap files.

Methodological context: Jackson (2011), https://www.jstatsoft.org/article/view/v038i08, motivates explicit Markov assumptions; Gneiting and Raftery (2007), https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf, supports proper probabilistic scoring. Neither source validates this NFL forecast.
