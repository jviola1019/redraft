# Five-year QB participation with production rookie-role conditioning

The mature-donor expansion clears the frozen gate for independent confirmation on 44 matched quarterbacks from the 2019–2021 scenarios. Five-year CRPS and proper interval scores improve on both targets, with gains concentrated among QBs who reached 200 rookie snaps. The cohorts were previously studied, and production adoption remains unsupported.

## Forecasts and eligibility

A TypeScript adapter calls the production server scenario, pooled probability and donor exposure functions directly. Both arms receive the same frozen rookie-role probabilities. The baseline uses the 15 deployed QB donor careers from 2013. The candidate adds whole five-year careers that reached the March 1 label-availability date by each scenario cutoff. It selects the rookie-role stratum with the production probability and weights its trajectories equally. The rookie probability models remain frozen through the 2017 season.

| Scenario cutoff, UTC | Candidate cohorts | Candidate donors | Donors with 200+ rookie snaps | Evaluated QBs |
|---|---|---:|---:|---:|
| 2019-04-25 23:59 | 2013–2014 | 33 | 7 | 17/17 |
| 2020-04-15 23:59 | 2013–2015 | 45 | 9 | 17/17 |
| 2021-04-29 23:59 | 2013–2016 | 62 | 13 | 10/13 |

The baseline contains three donors with 200 or more rookie snaps. The additional donors use the same identifiable raw-combine QB population and unique rookie-season name-position repair rule as the 2013 production artifact. No additional QB required repair. The latest candidate fit labels are dated March 1 of each origin year. The evaluation horizons end in 2023, 2024 and 2025.

The 2021 scenario uses the NFL invitee list recorded as published March 4, 2021, before the April 29 scenario cutoff. QB eligibility and pooled profiles come from the pre-draft scenario artifact. The raw combine provider snapshot has no archived per-measurement or per-ID publication timestamps. PFR identity links are retrospective evaluation joins. This narrower 2021 sample limits comparability with the earlier unconditional 50-player review.

| Raw 2021 QB with known PFR ID excluded by the frozen match | Reason |
|---|---|
| Jamie Newman | Present in both pools. Raw combine lists Georgia and the official invitee entry lists Wake Forest. |
| Peyton Ramsey | Absent from the production playable QB pool. |
| Zach Smith | Absent from the production playable QB pool. |
| Zac Thomas | Absent from the production playable QB pool. |
| Kevin Thomson | Absent from the production playable QB pool. |
| Brady White | Absent from the production playable QB pool. |

Brady Davis and David Moore also lack raw PFR IDs. Kellen Mond and Shane Buechele appear on the official list but have no raw combine QB row. A post-draft 2021 draft record links Mond to PFR ID `MondKe00` with the same name and school. The 2025 snap file contains Buechele's name and ID `BuecSh00` (January 4, 2026 game). The invitee reconciliation records no exact source match for either or for Newman. These checks document possible evaluation linkage work. None changes the frozen assessment or enters the forecasts. The March 4 source is linked below.

[Official 2021 combine invitee list](https://www.giants.com/news/2021-nfl-scouting-combine-list-of-invited-prospects-new-format-nfl-draft)

## Results

All differences are candidate minus production. The 95% intervals for paired CRPS are player bootstraps stratified by cohort. Coverage uses the observed five-year total.

| Target | Mean CRPS, production → candidate | Paired CRPS difference [95% interval] | Nominal-95% covered | 95% mean width | 95% mean interval score | Outside support |
|---|---:|---:|---:|---:|---:|---:|
| Snaps | 967.44 → 891.16 | −76.27 [−136.71, −24.39] | 33/44 → 43/44 | 2,020.54 → 5,198.58 | 20,517.41 → 5,262.79 | 11 → 1 |
| Games with recorded snaps | 15.65 → 15.02 | −0.63 [−1.20, −0.15] | 39/44 → 44/44 | 63.84 → 79.80 | 106.57 → 79.80 | 5 → 0 |

At nominal 80%, coverage rises from 31/44 to 36/44 for snaps and from 30/44 to 36/44 for games. The interval scores improve from 7,787.16 to 5,801.68 for snaps and from 111.07 to 91.32 for games. Mean-based snaps MAE increases from 1,183.53 to 1,265.25, while snaps RMSE falls from 1,840.69 to 1,739.44. Games MAE increases from 21.21 to 21.58 and games RMSE falls from 28.68 to 27.82. Nominal-80% mean widths grow from 1,525.65 to 2,487.99 snaps and from 35.84 to 50.86 games. Assuming the schedule known at draft time persists, the pooled CRPS gains hold, with paired intervals of [−135.68, −25.83] for snaps and [−1.19, −0.17] for games. In that sensitivity, 43 of 44 outcomes fall in each candidate 95% interval.

| Cohort | Snaps CRPS, production → candidate | Games CRPS, production → candidate |
|---|---:|---:|
| 2019 | 712.55 → 690.85 | 11.22 → 11.23 |
| 2020 | 1,034.23 → 936.85 | 15.72 → 14.93 |
| 2021 | 1,287.20 → 1,154.04 | 23.07 → 21.60 |

Each cohort-specific snaps CRPS interval crosses zero. The 2021 games interval is below zero, but the other games intervals cross zero. Both targets improve on average in both production profile tiers. Among the 30 QBs below 200 rookie snaps, snaps CRPS worsens from 188.89 to 215.22 and games CRPS worsens from 5.89 to 6.05. This realized-role split is descriptive and cannot be used to assign pre-draft forecasts.

| Subgroup | QBs | Snaps outside support, production → candidate | Games outside support, production → candidate |
|---|---:|---:|---:|
| Lowest production profile | 15 | 2 → 0 | 2 → 0 |
| Other production profiles | 29 | 9 → 1 | 3 → 0 |
| Under 200 rookie snaps | 30 | 1 → 0 | 0 → 0 |
| At least 200 rookie snaps | 14 | 10 → 1 | 5 → 0 |

The common rookie-role probabilities average 20.9%, versus 31.8% observed, with a Brier score of 0.2413. In the lowest predicted profile tier, the mean is 13.3% against 33.3% observed (15 players). The comparison isolates donor support and leaves that probability calibration error in both arms.

## Decision and limits

Advance the expanded donor pool to independent chronological confirmation for later scenarios. The 2018 cutoff still admits only the 2013 donors. The 2022 cohort requires complete 2026 outcomes before it can serve as a five-year assessment. The bootstrap holds the donor distributions fixed and does not quantify donor-fit uncertainty or transfer to new eras. Historical measurement publication times and label dates are reconstructed. Participation is measured before roster-capacity adjustments and team-strength conversion. No runtime, release gate or deployment changed.

## Reproduction

From the repository root, run:

```sh
python analytics/qb_conditioned/review.py
python analytics/qb_conditioned/test_review.py
```

The run reconciles recorded snap games from 2013 through 2025, matches production exposure exactly and tests whether poisoning ineligible seasons changes the donor arrays. The three tests additionally verify the March 1 maturity boundary, exact mixture scores, unchanged snap actuals, paired CRPS reconstruction and hashes. `results.json` includes detailed age, cohort and subgroup scores. `predictions.json` includes paired player-level forecasts and actuals.
