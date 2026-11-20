# Historical baseline playoff-qualification prediction audit

The simulated zero-intervention historical baseline has Brier 0.24016, versus 0.24492 for season-specific slot prevalence (skill 1.9%). Near-term predictions improve on that constant benchmark; later horizons show weak or negative skill. This is prediction scoring, not reconstruction of recorded playoff brackets, and does not validate draft intervention effects.

## Fixed protocol

At source commit `5e93390`, before running results, `playoff_forecast_protocol.json` fixed 64 seeds for each draft origin 2018–2025. For every origin, all 32 franchises are scored for each available completed season within its five-year horizon. There are 960 origin/team/season predictions, but only 256 distinct actual team-seasons (eight actual seasons). Every origin uses its authoritative runtime scenario/model; only the baseline world with recorded final actual draft allocations and zero trades is scored. The API also computes an alternate world solely because it requires a completed draft; that alternate world is discarded.

Labels are membership in any recorded postseason game, including division-round entrants with wildcard byes. A season must pass the authoritative full regular-season and postseason completeness check. Actual outcomes after 2025, incomplete actuals, and future actuals are excluded, rather than coded as nonqualification. Label data are pooled separately from simulation inputs. The comparison is a constant 12/32 probability for 2018–19 and 14/32 for 2020 onward.

Brier is the mean squared probability error; lower is better. Skill is 1 minus Brier divided by benchmark Brier. The overall score gives equal weight to every available origin/team/season prediction, so completed years with more available origins receive more weight. By-year and by-horizon results expose this weighting. This is an already-exposed retrospective audit with no tuning or gameplay changes.

## Results by horizon

| Horizon | Forecast rows | Brier | Prevalence Brier | Skill | MC SE | Estimated finite-seed bias |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 256 | 0.22521 | 0.24316 | 7.4% | 0.00363 | 0.00347 |
| 2 | 224 | 0.23530 | 0.24442 | 3.7% | 0.00407 | 0.00376 |
| 3 | 192 | 0.24662 | 0.24609 | -0.2% | 0.00485 | 0.00382 |
| 4 | 160 | 0.25788 | 0.24609 | -4.8% | 0.00519 | 0.00384 |
| 5 | 128 | 0.24672 | 0.24609 | -0.3% | 0.00567 | 0.00383 |

## Results by actual season

Forecasts from multiple origins are retained separately; each year still has only 32 distinct actual franchise outcomes.

| Actual season | Forecast rows | Brier | Prevalence Brier | Skill | MC SE |
|---|---:|---:|---:|---:|---:|
| 2018 | 32 | 0.20644 | 0.23438 | 11.9% | 0.00916 |
| 2019 | 64 | 0.21552 | 0.23438 | 8.0% | 0.00700 |
| 2020 | 96 | 0.24616 | 0.24609 | -0.0% | 0.00692 |
| 2021 | 128 | 0.24063 | 0.24609 | 2.2% | 0.00564 |
| 2022 | 160 | 0.24204 | 0.24609 | 1.6% | 0.00493 |
| 2023 | 160 | 0.24145 | 0.24609 | 1.9% | 0.00519 |
| 2024 | 160 | 0.25261 | 0.24609 | -2.6% | 0.00491 |
| 2025 | 160 | 0.23717 | 0.24609 | 3.6% | 0.00483 |

## Monte Carlo and evidence limits

Overall delta-method seed Monte Carlo SE is 0.00211. The estimated upward Brier bias from using only 64 draws is 0.00372; subtracting it gives 0.23645. Raw Brier is the primary result. Per-team probability estimates have increments of 1/64 and a maximum binomial Monte Carlo SE of 6.25 percentage points. These estimates are not sufficiently precise for fine team rankings.

The Brier bias estimate is mean p-hat(1−p-hat)/(64−1). Monte Carlo SE uses the first-order Brier influence 2(p-hat−actual)(qualification draw−p-hat), summed within an entire origin/seed path before estimating variance across seeds. This retains within-path dependence among franchises and horizons and treats different origin seed streams as independent under the simulator. The first-order SE is approximate; it does not include generalization error, uncertain parameters, unmodeled roster changes, or uncertainty in the draft-to-strength conversion. Estimated finite-seed bias is shown separately, rather than hidden in the MC SE.

Overlapping horizons repeatedly score the same actual team-season; they are not independent evidence. Different horizons also have different origin/year composition, so their differences cannot be interpreted purely as horizon decay. Only eight actual seasons are available, all previously exposed. No significance test or confidence interval for real-world forecast generalization is claimed. Aggregate predicted prevalence exactly matches actual prevalence because each simulated season fills the fixed playoff slots; that arithmetic equality does not establish team-level calibration.

## Historical information and schedule assumptions

Runtime team-score coefficients and total-score recalibration are fit through 2017. Later origins initialize strengths from their known preceding regular season; five-year participation trajectories use pre-cutoff 2013-cohort donors. Recorded final actual draft allocations are replayed: these allocations were not fully known at the draft-opening timestamp, so this is a conditional actual-draft baseline, not a forecast available before those picks. Snaps-to-strength conversion, other roster changes, and multi-year roster evolution remain model assumptions.

The runtime preserves a complete recorded starting-season schedule, including home assignments and weeks. Such a schedule can incorporate information published after the scenario draft timestamp; this audit conditions on that hindsight schedule. Later seasons regenerate standings-dependent opponents using simulated standings, not future recorded scores. A complete 2022 observed regular season contains the canceled BUF–CIN exception (271 games); the schedule generator requires 272 fixtures and therefore generates the 2022 starting schedule instead of replaying that incomplete fixture list. The actual 2022 label still passes the documented canceled-game completeness exception. The runtime also applies the realized 2020 playoff expansion and 2021 17-game calendar to future horizons, even for origins before those changes were announced. These are retrospective structural assumptions. No observed post-origin game scores feed simulated standings or strength updates.

The executed poisoning check replaces every recorded origin-and-later game score with 999–998 and confirms identical seed-0 baseline worlds for all eight origins. This directly checks the runtime score-input path; it does not prove that every historical feature has an original-publication timestamp or erase known hindsight from schedules and final draft allocations.

## Reproduction and tests

```bash
cd redraft
node analytics/playoff_forecast.mjs > /tmp/playoff-forecast.log
node analytics/test_playoff_forecast.mjs
```

Dependencies are the same as the source checkout. The results JSON records runtime input hashes, model versions, per-origin and grouped summaries, every franchise forecast, and its 64 qualification draws. The protocol, implementation, tests and results remain isolated; no gameplay code changed. Tests pass for all-year labels including byes, exact 12/14 qualifier counts, exclusion of incomplete and future outcomes, future-score poisoning invariance, complete 960-row coverage, 256 unique actual team-seasons, probability bounds, 64 draws per row, and exact simulated slot totals.

The result provides modest near-term predictive evidence relative to a weak prevalence benchmark. It does not establish strong five-year playoff forecasting, scientific accuracy of the alternate-history model, or causal value of user draft choices.

The fixed protocol was rerun at gameplay revision 25be247 after correcting the 2021 historical pick identity. Source hashes, fitted model versions and updated scores are in playoff_forecast_results.json.
