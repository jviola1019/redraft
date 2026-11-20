# Five-year QB uncertainty hindcast

The age-rank candidate covered all 16 reused 2018 QB outcomes for both snaps and games. It did so with substantially wider intervals. Its paired CRPS confidence intervals crossed zero for both targets in both origin groups. The frozen protocol rejects advancement. The production QB snap and game coverage gates still fail, and the conditional donor-support gate remains unsupported.

## Frozen policy and chronological comparisons

The unchanged statistical gate audit completed with 40 passes, 6 failures, 7 unsupported gates, and zero stale artifacts. The frozen 2018 QB scores reconstructed exactly from the donor artifacts and player probabilities. Rerunning the existing 2016–2017 transition hindcast also reproduced its saved JSON byte-for-byte.

The [protocol](qb_rank_hindcast_PROTOCOL.md) was committed before implementing or evaluating this candidate. Use a shared latent percentile across career ages to permit strong persistence while estimating a separate usage distribution at each age. Pair each age's snaps and games from the same observed row. The earlier baselines repeat a sampled rookie year's usage across ages. The later chronology baselines sample complete five-year histories already available at the origin. Draft-time forecasts assume the schedule in force at the origin persists, with a separately reported realized-schedule sensitivity. The 2021 expansion was [approved March 30, 2021](https://www.nfl.com/news/nfl-owners-approve-enhanced-schedule-with-17-regular-season-games-per-team).

| Origins | Target | QBs | Candidate CRPS | Comparison CRPS | Paired difference, 95% player-bootstrap interval |
|---|---|---:|---:|---:|---:|
| 2016–2017 | Snaps | 32 | 737.30 | 747.59 | −10.30 [−46.73, 21.17] |
| 2016–2017 | Games | 32 | 12.06 | 12.21 | −0.15 [−0.65, 0.33] |
| 2018–2021 | Snaps | 66 | 802.42 | 853.89 | −51.47 [−116.46, 6.68] |
| 2018–2021 | Games | 66 | 13.78 | 14.24 | −0.46 [−1.17, 0.19] |

| 2018 target | Frozen 95% coverage | Candidate 95% coverage | Frozen / candidate mean width | Frozen / candidate mean interval score | Frozen / candidate support exceedances |
|---|---:|---:|---:|---:|---:|
| Snaps | 12/16 | 16/16 | 1971.19 / 5387.00 | 24814.31 / 5387.00 | 4 / 0 |
| Games | 13/16 | 16/16 | 63 / 80 | 138 / 80 | 3 / 0 |

The candidate passes the reused 2018 coverage and interval-score checks. Its 2018 draft-time 95% game interval spans the entire five-season schedule, [0, 80] games. Changing to the realized schedule gives 16/16 coverage for both and widens the respective upper ends to roughly 5,520 snaps and 82 games. The paired CRPS intervals still cross zero. The age-rank model can assemble a persistent sequence across unrelated players and so can expand support without observing similar whole careers. Conditional support in the frozen 2018 donor pool remains 3 rookie-role and 12 no-rookie-role careers.

The cohorts were previously exposed and the model uses unconditional QB usage rather than player-specific information. The percentile construction may overstate persistence. Coverage in a 16-player subgroup and the player-stratified bootstrap over six cohorts cannot establish population calibration across eras. Original label publication dates were unavailable. Resampling conditions on each fitted empirical distribution and omits model, team, and refit uncertainty.

## Earlier source checks

The official nflverse 2012 snap CSV returned HTTP 200 and 154 bytes, one header and zero records, with SHA-256 `802475aec59f0b125de85a6c35eb69e289a512bcf62d6be007d385ea8d613ebd`. The analogous 2011 asset returned HTTP 404. nflverse's [on-field player participation loader](https://nflreadr.nflverse.com/reference/load_participation.html) begins in 2016.

An indexed [2012 Indianapolis Colts snap table](https://www.pro-football-reference.com/teams/clt/2012-snap-counts.htm) shows 1,169 offensive snaps for Andrew Luck and references game-by-game counts. His [player page](https://www.pro-football-reference.com/players/L/LuckAn00.htm) lists snap coverage beginning in 2012; its 1,048 offensive snaps for 2013 agree with the local game-level annual aggregate. Direct access to the Sports Reference team page returned HTTP 403. The indexed entry supports a 2012 source lead but cannot establish league-wide game coverage, zero-snap games, reconciled identifiers, or data-use rights. The 2012 combine class has 19 QB entries, 14 with PFR IDs. An auditable extension requires reconciling game coverage and positive-snap appearance rules against the existing 2013 files before extending the source. [Sports Reference data use](https://www.sports-reference.com/data_use.html)

Three official historical regular-season player-stat CSVs and the player registry were acquired for a local source feasibility sample. Match candidate combine PFR IDs to the registry's GSIS ID and then to the annual stats `player_id`. Distinct mapped IDs and matched stats rows differ, and unobserved stats rows cannot establish zero snaps. This updates the earlier source report's acquisition status. The stats can support a separate passing-volume study and were excluded from snap and game modeling. [nflreadr stats schema](https://nflreadr.nflverse.com/articles/dictionary_player_stats.html)

| Sample season | Combine QB rows | PFR IDs present | PFR-to-GSIS matches | Stats matches | Total stats rows |
|---|---:|---:|---:|---:|---:|
| 2000 | 18 | 12 | 12 | 10 | 1647 |
| 2012 | 19 | 14 | 14 | 9 | 1811 |
| 2013 | 16 | 15 | 13 | 5 | 1792 |

| Official release asset | SHA-256 |
|---|---|
| [Player registry CSV](https://github.com/nflverse/nflverse-data/releases/download/players/players.csv) | `390fadc2fcc17e1fde080b75160e79487fd71fb13c5aff3f0cbe8c6766e2398f` |
| [2000 regular-season statistics](https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_reg_2000.csv) | `98ea435ba8ad8faaec27d1ffab39cc787f40ad664464ac480513b940f72f412d` |
| [2012 regular-season statistics](https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_reg_2012.csv) | `b3d2ab75ec5b6c6d030068cbc0e5242b30c329dedae3ce7c675a8f64d669262e` |
| [2013 regular-season statistics](https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_reg_2013.csv) | `14658000dbdb0b627dc1f4b2872349d9150718e4960b99cc282d054af98aebae` |

## Reproduction

```bash
python analytics/qb_rank_hindcast.py --out /tmp/qb-rank-hindcast
cmp /tmp/qb-rank-hindcast/qb_rank_hindcast.json analytics/qb_rank_hindcast.json
cmp /tmp/qb-rank-hindcast/qb_rank_hindcast_predictions.json analytics/qb_rank_hindcast_predictions.json
python analytics/test_qb_rank_hindcast.py
```

The report JSON includes source hashes, game reconciliation, date cutoffs, fit rows by age, unknown-ID exclusions, metrics by cohort, and explicit decision checks. The saved prediction JSON includes both exposure policies and paired person-level losses.
