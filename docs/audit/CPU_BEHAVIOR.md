# CPU draft behavior backtest

Audit date: 2026-11-20. This is a bounded, descriptive backtest of the legacy CPU policy. The current engine and its paired comparison are documented in the [team-conditional choice experiment](cpu_team_prior/REPORT.md).

**Finding:** Completing drafts legally does not make the CPU behavior historically plausible. Across 108 complete auto-drafts (12 fixed seeds for each class, 2018–2026), the CPU selected **one first-round quarterback in total**. Actual drafts selected 31 across the nine classes. The round-one position mix strongly favors offensive linemen, especially in recent classes. Whole-draft aggregate shares hide this concentration.

## Method and reproduction

Run `node research/cpu_behavior_audit.mjs --legacy-engine --output /tmp/cpu_behavior_legacy.json`. The script loads the production scenario registry and engine through `analytics/runtime_loader.mjs`, performs all comparisons independently and records hashes of runtime/model/scenario inputs and raw trades. All 108 drafts filled their class's slots with unique playable candidates; eligibility failures were zero.

The 12 seeds are fixed before examining results. The designated user franchise rotates through 12 franchises; `autoComplete` applies the CPU picking policy to that franchise too, but `maybeCpuTrade` excludes it from CPU trades. Thus this measures a production auto-completed session, not a hypothetical 32-team symmetric trading league. No user board changes or user trade proposals are included.

Positions use `engine.positionGroup`, including its first-listed-role convention. Total variation (TV) is half the summed absolute difference in position shares: 0 means equal shares, 1 means disjoint shares. The table below averages TV computed separately for each simulated draft; the JSON also provides pooled mean-position shares, per-round counts, per-run ranges/SD/Monte Carlo SE and comparisons with actual playable-only picks. Monte Carlo SE describes between-seed sampling error only. These are no tests of player quality or causal wins.

## Position by round

| Class | Mean whole-draft TV | Mean round-one TV | Mean CPU round-one QBs | Actual round-one QBs | Mean CPU round-one OL | Actual round-one OL |
|---|---:|---:|---:|---:|---:|---:|
| 2018 | 0.052 | 0.341 | 0.00 | 5 | 13.17 | 6 |
| 2019 | 0.074 | 0.424 | 0.00 | 3 | 15.50 | 6 |
| 2020 | 0.062 | 0.438 | 0.00 | 4 | 17.42 | 7 |
| 2021 | 0.051 | 0.396 | 0.00 | 5 | 11.67 | 5 |
| 2022 | 0.069 | 0.385 | 0.00 | 1 | 14.42 | 9 |
| 2023 | 0.090 | 0.538 | 0.08 | 3 | 20.42 | 5 |
| 2024 | 0.074 | 0.594 | 0.00 | 6 | 25.83 | 9 |
| 2025 | 0.094 | 0.552 | 0.00 | 2 | 19.33 | 8 |
| 2026 | 0.046 | 0.625 | 0.00 | 2 | 20.08 | 9 |

2023 has 31 actual first-round slots; other classes have 32. The sole simulated first-round QB occurs in one 2023 seed. In 2024, the mean offensive-line count is 25.83 of 32 first-round picks. In 2026, offensive and defensive linemen together account for 31 of 32 first-round picks on average. The specialist count is also systematically low: each class's mean CPU K/P/LS count is below its actual count (per-class details in JSON).

The frozen projection target is 200+ rookie scrimmage snaps, which measures opportunity and participation, not draft asset value. The engine adds a fixed QB premium, position premiums, within-class positional balance and noise. The observed selections demonstrate that this particular utility has the wrong ordering for historical draft imitation. They do not establish which coefficient should change, and fitting nine actual classes blindly would overfit a descriptive target. The 2021 roster and measurement gaps, grouping policy, specialist fallback and position-specific value all require separate design decisions.

## Trade frequency

Actual comparisons group asset rows by distinct `trade_id` inside inclusive draft-date windows. CPU trades support only current-year picks. The closer actual comparator therefore contains only transactions whose every asset is a current-year pick; the all-pick-related count also includes deals with future picks and players. Date-only source windows can include off-clock transactions. Neither comparator proves source completeness.

| Class | Mean CPU trades | CPU range | Actual current-year-picks-only | Actual pick-related |
|---|---:|---:|---:|---:|
| 2018 | 22.67 | 18–30 | 29 | 38 |
| 2019 | 22.83 | 19–29 | 32 | 40 |
| 2020 | 23.00 | 18–31 | 17 | 29 |
| 2021 | 23.25 | 19–30 | 21 | 28 |
| 2022 | 22.75 | 17–29 | 28 | 37 |
| 2023 | 23.17 | 17–30 | 28 | 43 |
| 2024 | 23.00 | 19–30 | 20 | 29 |
| 2025 | 22.58 | 18–29 | 24 | 35 |
| 2026 | 23.17 | 19–28 | Unavailable | Unavailable |

The raw transaction file ends April 17, 2026, before the April 23–25 draft. Its zero observed 2026 draft-window transactions mean **unavailable coverage**, not no trades. The diagnostic records null actual comparator counts for that year.

The CPU trade arrival threshold defaults to 0.10 each eligible on-clock pick; the engine then seeks bundles with chart value between 1.1 and 1.8 times the seller's current pick. This rate is an explicit gameplay assumption. CPU means remain near 23 trades across all classes while actual same-year-only counts vary. In 2020 the CPU exceeds the closer actual comparator (23 versus 17); in 2019 it falls below it (22.83 versus 32). A single comparison with all real transactions would confound policy behavior with the game's restricted asset vocabulary. No empirical trade-rate calibration is established here.

## Franchise and baseline heterogeneity

The JSON includes all 32 franchises per class: actual pick counts, reference-only selections, actual position counts, actual effective position diversity, CPU pick-count/diversity distributions and CPU-versus-actual position TV. Effective diversity is exp(Shannon entropy); it describes positional variety, not roster need. Aggregate mean diversity alone conceals which franchises receive which positions.

Across classes, actual mean franchise diversity ranges roughly 4.90–5.31 effective groups, versus CPU class means 5.09–5.47. Yet mean franchise-level position TV remains 0.36–0.43. A superficially similar leaguewide diversity score does not reproduce team allocation. Draft-capital differences and simulated trades also change denominators, so franchise TV is descriptive and should not be treated as a pure policy error score.

Every historical baseline contains reference-only actual selections unavailable for gameplay. More seriously, spot inspection found semantic identity fragmentation: six 2021 first-round selections appear as reference-only records despite corresponding playable invitees. Examples include Trey Lance (North Dakota St./North Dakota State), Justin Fields (Ohio St./Ohio State), Micah Parsons (Penn St./Penn State), Jaelan Phillips (Miami FL/Miami), Gregory/Greg Rousseau and Odafe/Jayson Oweh. Exact-ID completeness tests cannot detect these separate IDs for the same person. Normalized-name candidates also exist in other classes, but name equality alone is unsafe: David Long from Michigan and David Long from West Virginia are different candidates.

Consequently, the all-actual versus playable-only comparison is a sensitivity analysis of the stored dataset, not a verified reconstruction of true invitee membership. The observed first-round QB failure remains visible in both universes: most actual first-round QBs are playable, and the difference is far larger than the identified reference-only fraction.

## Prioritized follow-up

1. Reconcile semantic prospect identities before interpreting baseline gaps. Use validated school aliases and documented name changes with human-reviewable exceptions; preserve genuinely distinct same-name players. Rebuild exact-ID baselines and rerun the diagnostic after repairs.
2. Separate rookie participation forecasts from draft utility. Define an explicit gameplay objective that accounts for position-dependent value and uncertainty, then evaluate it on held-out classes and by round. Do not label this policy realistic before the round-one concentration issue is addressed.
3. Treat trade frequency as uncalibrated. Compare like asset scopes, restore 2026 source coverage, and evaluate a candidate rate on held-out transactions before changing coefficients.
4. Retain per-round and per-franchise diagnostics as acceptance evidence. Whole-draft position shares and legal completion alone miss the dominant behavioral failure.

This work supplies evidence and priorities; it makes no runtime changes and offers no claim of calibrated GM behavior, player value, or counterfactual team quality.
