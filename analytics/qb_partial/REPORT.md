# QB participation forecasts through the 2025 season

The mature-donor expansion improved second-season forecasts, but the advantage weakened at later follow-up. Among the 13 verified-ID 2022 QBs with four complete seasons, cumulative games CRPS worsened by 0.248, with a paired 95% interval of [0.046, 0.487]. Cumulative 95% interval coverage reached 13/13 on both outcomes as intervals widened. Fifth-season and full five-season results await complete 2026 regular-season snap data.

## Cohorts and cutoffs

Both approaches use the same production pooled rookie-role probabilities and the same two strata split at 200 rookie snaps. Both retain paired whole snap and games trajectories. Production uses 15 QB donors from 2013, three in the 200-plus stratum. The candidate adds cohorts available by the cutoff, using March 1 after a donor's fifth season as the availability date. Donor seasons through 2020 scale from 16 to 17 scheduled games. Donor seasons from 2021 use their existing 17-game scale. Games are rounded and capped at 17. Production exposure is reproduced exactly.

| Origin cutoff, UTC | Candidate cohorts | Candidate donors | 200+ rookie snap donors | Matched board | Primary sample | Complete seasons |
|---|---|---:|---:|---:|---:|---:|
| 2022-04-28 23:59 | 2013–2017 | 77 | 17 | 15 | 13 | 4 |
| 2023-04-27 23:59 | 2013–2018 | 93 | 22 | 15 | 15 | 3 |
| 2024-04-25 23:59 | 2013–2019 | 110 | 27 | 14 | 14 | 2 |
| 2025-04-24 23:59 | 2013–2020 | 127 | 31 | 15 | 15 | 1 |

The frozen prediction board includes all 59 playable scenario QBs with exact unique normalized name-and-school combine matches. The frozen raw combine snapshot lacks three PFR IDs. Tyson Bagent's PFR identity was independently confirmed. Cole Kelley and EJ Perry match the official 2022 invitee list, with no PFR ID available in the combine file and no corresponding normalized name in regular-season snap records through 2025. The primary analysis excludes both. The 59-player sensitivity assumes zero snaps and games for their first four seasons. Both 2022 prospects retain prospect-level frozen distributions for future identity and participation adjudication.

[Official NFL invitee list](https://www.nfl.com/_amp/2022-nfl-scouting-combine-invited-prospects-by-position) · [PFR Tyson Bagent profile](https://www.pro-football-reference.com/players/B/BageTy00.htm)

Regular-season snap sources match scored schedule games exactly. There are 271 completed games in 2022 and 272 in each of 2023, 2024 and 2025. A verified player absent from a fully covered season receives zero observed snaps and games. Games counts mean games with recorded snaps. The scoring step opened no 2026 QB snap records.

## Distribution scores

Negative CRPS differences favor the expansion. Intervals are 5,000 paired player bootstrap resamples stratified by cohort, with fixed predictive distributions. Numbers of eligible players fall with the observation horizon. Annual and cumulative year one are identical.

| Target | Year | QBs | Snaps CRPS difference [95% interval] | Games CRPS difference [95% interval] |
|---|---:|---:|---:|---:|
| Annual | 1 | 57 | -1.49 [-4.99, 2.32] | 0.033 [-0.082, 0.156] |
| Annual | 2 | 42 | -21.44 [-38.85, -5.19] | -0.218 [-0.384, -0.062] |
| Annual | 3 | 28 | 0.84 [-22.23, 18.86] | 0.035 [-0.237, 0.254] |
| Annual | 4 | 13 | 9.65 [-0.63, 18.08] | 0.064 [-0.038, 0.174] |
| Cumulative | 1 | 57 | -1.49 [-4.99, 2.32] | 0.033 [-0.082, 0.156] |
| Cumulative | 2 | 42 | -13.46 [-26.17, -1.53] | -0.079 [-0.162, 0.003] |
| Cumulative | 3 | 28 | -8.85 [-45.52, 20.49] | -0.009 [-0.270, 0.223] |
| Cumulative | 4 | 13 | 6.78 [-42.31, 39.85] | 0.248 [0.046, 0.487] |

The cumulative interval table compares production with the mature expansion. The machine-readable results include both nominal coverage levels, proper interval scores, empirical support misses, RMSE and every origin and subgroup score.

| Year | Target | MAE | Covered at 95% nominal | Mean 95% width | Mean 95% interval score |
|---|---|---:|---:|---:|---:|
| 1 | Snaps | 262.82 → 260.92 | 53/57 → 53/57 | 1,046.56 → 1,081.62 | 1,155.16 → 1,172.33 |
| 1 | Games | 4.70 → 4.71 | 57/57 → 57/57 | 17.00 → 17.00 | 17.00 → 17.00 |
| 2 | Snaps | 557.53 → 567.22 | 39/42 → 40/42 | 1,913.56 → 2,128.72 | 2,630.05 → 2,397.77 |
| 2 | Games | 9.45 → 9.42 | 40/42 → 41/42 | 32.00 → 33.29 | 35.81 → 35.19 |
| 3 | Snaps | 599.27 → 640.72 | 25/28 → 28/28 | 1,982.62 → 3,223.28 | 4,758.52 → 3,223.28 |
| 3 | Games | 10.92 → 10.74 | 25/28 → 28/28 | 33.00 → 49.11 | 80.14 → 49.11 |
| 4 | Snaps | 614.29 → 627.50 | 12/13 → 13/13 | 2,017.69 → 4,233.82 | 4,535.57 → 4,233.82 |
| 4 | Games | 12.51 → 12.42 | 12/13 → 13/13 | 48.00 → 63.69 | 51.08 → 63.69 |

Cumulative year-two snaps CRPS improves across all three eligible origins. The differences are −7.49 in 2022, −7.50 in 2023 and −25.40 in 2024. In year three, the lowest predicted profile improves by 68.62 snaps CRPS across 10 QBs, while the other 18 QBs worsen by 24.35. The observed rookie role also separates performance in year three. The expansion worsens cumulative snaps CRPS by 37.79 in the 16 QBs below 200 rookie snaps and improves by 71.03 in the 12 QBs at or above 200. Observed role is a descriptive subgroup available only after the draft.

The 59-player sensitivity still finds cumulative year-two snaps CRPS improvement, −11.69 [−23.72, −0.26], and four-year games deterioration, +0.295 [0.104, 0.516]. Its cumulative year-four snaps difference of +16.07 [−26.92, 46.65] is larger than in the primary sample and remains uncertain.

## Pending follow-up

The 2022 forecast artifact contains weighted empirical distributions and summaries for both 2026 alone and the 2022–2026 cumulative outcome. Both forecasts use only information valid at the 2022 origin, with no update on first-four-year results. Its SHA-256 was recorded before scores were computed. Once the full 2026 regular-season snap source is reconciled, score those two targets using the frozen artifact, with any unresolved player identity adjudication recorded separately.

The current assessment uses previously accessible outcomes and repeated, overlapping horizon comparisons. The paired intervals are descriptive and unadjusted for multiple comparisons. Each successive pooled horizon changes its mix of cohorts, and year four is a single cohort. Bootstrap intervals hold the candidate's donor distribution fixed. Historical timestamps, opportunity and selection effects further limit interpretation. The independent full five-year confirmation remains pending. Production is unchanged.

## Reproduction

Run from the repository root, using a fresh output directory for forecasts and scores.

```sh
python analytics/qb_partial/study.py predict --out /tmp/qb-partial-reproduction
python analytics/qb_partial/study.py score --out /tmp/qb-partial-reproduction
python analytics/qb_partial/test_study.py
python analytics/qb_partial/plot.py
```
