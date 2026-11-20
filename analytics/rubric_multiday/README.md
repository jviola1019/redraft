# Multi-day daily leaderboard sensitivity

The audit compares four draft policies on six official daily configurations generated locally by the game's GET route for November 1–6, 2026. The isolated database uses the runtime migration, a frozen clock, and a test identity. This design captures the real assignment algorithm and its persisted version pins without querying player data. The frozen snapshot contains only tokens minted for these closed-date local fixtures. It contains no live seeds, salts, accounts, or results.

## Results

The official rounded first-place set changed in **12 of 60** weight comparisons and on **five of six** dates. The unrounded diagnostic changed in 5 of 60 comparisons. Minimum tied-rank Spearman was 0.632 and the mean was 0.962, with all 60 correlations defined. Detroit had the only tie for first place under the default weights.

| UTC date | Franchise | Draft class | Default first place | Changes out of 10 |
|---|---|---:|---|---:|
| 2026-11-01 | CIN | 2026 | Line priority, 59 | 3 |
| 2026-11-02 | KC | 2020 | Scouted probability, 53 | 1 |
| 2026-11-03 | DEN | 2025 | Line priority, 63 | 1 |
| 2026-11-04 | CLE | 2025 | Line priority, 74 | 0 |
| 2026-11-05 | DET | 2025 | Line priority and Scouted probability, 56 | 5 |
| 2026-11-06 | HOU | 2021 | Scouted probability, 68 | 2 |

Draft-class balance accounted for five changes, projected class value for four, and the paired five-year difference for three. Trade capital was invariant among policies on every date. Scouting coverage varied, and neither of its two weight changes moved the first-place set in this sample.

The 128-draw halves disagreed with the 256-draw comparison about whether a perturbation changed first place in 12 and 6 of 60 cases, respectively. Default first-place sets differed from the full ensemble on two dates for the first half and zero for the second half. Some of the observed winner changes are sensitive to simulation draw count as well as rubric weights.

## Method and limitations

The full ensemble uses 256 draws per policy and the same replica indices across all four policies on each date. Each perturbation only changes how the resulting five score components are weighted. For each of the five components, multiply its weight by 0.5 or 1.5 and renormalize. Use the runtime score rounding and competition ranks, with Spearman calculated from average ranks for ties. Count a leader-set change whenever any policy enters or leaves first place. A half-ensemble diagnostic measures how often the smaller draws change a baseline leader set or a perturbation's change call.

The CPU utility benchmark takes engine fallback choices and spends no scouting points. The three scripted policies use shared blind scouting disclosures plus a position preference. Variation in coverage partly reflects this design. Policies do not initiate trades. The date frame is small, the ten perturbations per date reuse policy outcomes, and classes are unevenly represented. The results describe this frame and these policies. The half-ensemble check describes simulation variability only. The underlying model's assumptions, uncertainty, and applicability to player skill require separate validation.

## Reproduce

Run from the repository root on Node 24 with the project dependencies installed.

```sh
node analytics/rubric_multiday/audit.mjs
node --test analytics/rubric_multiday/audit.test.mjs analytics/test_rank_sensitivity.mjs
```

The audit replays the frozen `fixtures.json`. A new capture uses `node analytics/rubric_multiday/capture.mjs` and requires an absent fixture file. It draws fresh random challenge tokens, so that capture creates a different experiment. The checked-in result includes protocol, fixture, source and dataset hashes, policy components, paired win summaries and all full and half-ensemble rankings.
