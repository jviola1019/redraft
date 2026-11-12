# Simulation validation — executed diagnostics

## November 12 implementation audit

The current engine is `redraft-research-0.7-multiyear-playoffs`. All registered classes 2018–2026 pass the same finite structural matrix: 864 full drafts, 1,728 baseline/alternate replicate pairs, 288 deterministic replays, 17,280 simulated seasons, 4,663,296 regular-season games and 222,336 playoff games. These counts exclude repeated deterministic replay inspections and are not independent real-world observations. Reports: `tests/results/year-matrix-2026-11-12/`.

A separate recorded-season backtest reproduces qualifiers, wild-card matchups/home teams and divisional reseeding/home teams for 2018–2025 (`tests/results/playoff-backtest.json`). It tests rule implementation, not playoff probability calibration. Future schedules now respond to alternate standings; full net-touchdown tiebreak criteria, schedule week/home placement and 17th-opponent rotation remain approximations. Dynamic actual-history boundaries leave incomplete 2026 and future actual values unavailable. Fresh statistical gauntlet results are reported separately; earlier dated numbers below are historical evidence only.

Rebuilt 2026-11-02; engine redraft-research-0.4-r1. Full statistical release gate **not passed**. JSON reports retain exact source/model hashes. Simulations use the actual TypeScript engine via a temporary transpilation loader.

Game predictor alignment fixes double shrinkage: the prior-season coefficient is applied once, and next state uses simulated realized margins. Team-year shocks preserve within-season correlation. Directional home/away random keys prevent repeated divisional games sharing identical residuals. Rounded 1-point scores map to 2; the score model is still a continuous approximation.

## League distributions

Actual 2018–2022 data is evaluation-only, not used to tune parameters after the historical cutoff. Recorded completed games=1311; a full simulated schedule has 1312. Rates are normalized by games/team-seasons.

| Metric | Recorded | Simulated mean | Across-replicate 2.5–97.5% range |
|---|---:|---:|---:|
| totalScoreMean | 46.2899 | 43.7565 | [42.9329, 44.7477] |
| totalScoreSd | 14.0697 | 13.9370 | [13.3736, 14.4548] |
| marginMean | 1.1777 | 2.0644 | [1.1692, 2.8735] |
| marginSd | 14.2881 | 14.5438 | [13.8289, 15.2806] |
| homeWinRate | 0.5362 | 0.5543 | [0.5259, 0.5800] |
| tieRate | 0.0053 | 0.0034 | [0.0008, 0.0069] |
| teamWinSd | 3.0984 | 3.0690 | [2.7674, 3.3229] |
| zeroScoreRate | 0.0103 | 0.0188 | [0.0133, 0.0252] |
| onePointScoreRate | 0.0000 | 0.0000 | [0.0000, 0.0000] |

Conditional distribution flags:

- totalScoreMean: recorded 46.2899, simulated 43.7565.
- zeroScoreRate: recorded0.0103, simulated0.0188.

These failures remain disclosed. Fixed pre-2018 scoring misses later regime changes; shutout behavior is imperfect. Matching marginal win variance does not validate player careers, league rosters, CPU strategy, awards or draft effects. Intervals omit parameter and model-structure uncertainty.

## Ensemble convergence

| Team | Replicates | Mean paired five-year wins | Mean MCSE | P(improvement) | Probability MCSE |
|---|---:|---:|---:|---:|---:|
| CLE | 32 | -0.844 | 0.601 | 0.375 | 0.086 |
| CLE | 64 | -0.781 | 0.416 | 0.359 | 0.060 |
| CLE | 128 | -0.828 | 0.312 | 0.367 | 0.043 |
| CLE | 256 | -0.648 | 0.203 | 0.359 | 0.030 |
| KC | 32 | 0.531 | 0.559 | 0.531 | 0.088 |
| KC | 64 | 1.219 | 0.433 | 0.594 | 0.061 |
| KC | 128 | 1.016 | 0.315 | 0.578 | 0.044 |
| KC | 256 | 1.113 | 0.230 | 0.559 | 0.031 |
| NE | 32 | -1.281 | 0.694 | 0.219 | 0.073 |
| NE | 64 | -1.250 | 0.456 | 0.266 | 0.055 |
| NE | 128 | -1.039 | 0.300 | 0.297 | 0.040 |
| NE | 256 | -1.074 | 0.211 | 0.320 | 0.029 |
| SF | 32 | 0.281 | 0.506 | 0.500 | 0.088 |
| SF | 64 | 0.703 | 0.437 | 0.531 | 0.062 |
| SF | 128 | 0.773 | 0.300 | 0.531 | 0.044 |
| SF | 256 | 0.605 | 0.210 | 0.500 | 0.031 |

A 256-replicate standard is a practical precision/latency choice informed by these results. Probability MCSE is bounded by 0.03125 at 256 independent replicates. More simulations reduce sampling noise; they cannot repair causal/model misspecification. Small leaderboard differences should not be interpreted as statistically established skill differences.

## Score sensitivity

Four prespecified policies, same CLE scenario and seed family; 128 paired replicates per policy. Each score weight is multiplied by 0.5 or 1.5 then renormalized. Top rank changes=2 of 11 settings; minimum rank correlation=0.600. This small exploratory exercise does not validate GM skill or user-trade strategy.

| Policy | Score | Mean paired wins | MCSE |
|---|---:|---:|---:|
| CPU utility policy | 51 | -0.359 | 0.320 |
| Highest rookie-role probability | 55 | 0.180 | 0.327 |
| Quarterback priority | 55 | 0.953 | 0.312 |
| Line priority | 50 | -0.281 | 0.317 |

## Local performance

| Team | Replicates | Paired five-season time | Per paired replicate |
|---|---:|---:|---:|
| CLE | 256 | 10.588s | 41.36ms |
| KC | 256 | 9.556s | 37.33ms |
| NE | 256 | 9.828s | 38.39ms |
| SF | 256 | 9.828s | 38.39ms |

These concurrent container runs include CPU contention and are not hosted Worker/network/iPhone benchmarks. Hardware: `{"platform": "linux", "arch": "x64", "cpu": "AMD EPYC 9V74 80-Core Processor", "logicalCpus": 9, "memoryBytes": 10451427328, "node": "v24.22.1"}`. Draft time logged separately.

## Tests and limitations

`analytics/test_models.py` runs 15 meaningful checks covering chronological partitions, completed labels, exact metric recomputation, leakage via poisoned future records, probability/ID constraints, source coverage, residual variance conservation, missingness-preserving coarsening and measured coarsening metrics. Source publication timestamps remain explicitly unknown. Engine structural tests are documented separately.

Only 336 combine participants are playable; 39 noncombine actual draftees are baseline-only. Source snapshots and initial ownership are not archive-perfect. Future roster transactions, individual injuries, validated player development and NFL-wide awards are unsupported. Cohort awards are model summaries. Scoring and draft-impact functions are assumptions, not causal evidence.

## Reproduce

```sh
python analytics/train_models.py
python analytics/pooling_validation.py
python analytics/test_models.py
node analytics/simulation_diagnostics.mjs 256 CLE
node analytics/simulation_diagnostics.mjs 256 KC
node analytics/simulation_diagnostics.mjs 256 NE
node analytics/simulation_diagnostics.mjs 256 SF
node analytics/score_sensitivity.mjs
python analytics/render_reports.py
python analytics/plot_diagnostics.py
```

## Pooled runtime configuration

Final simulation diagnostics use model version `redraft-2018-model-v1+blind-g5-v1` through `lib/scouting.ts` in the same runtime loader as the application. Unpooled experiments are retained under `analytics/pilots/unpooled-2026-11-02`. Source hashes distinguish the executions. The pooling utility experiment is a separate first-season predictive check, not validation of simulated five-year causal effects.

## Empirical development revision (2026-11-02)
Runtime replaces the fixed five-year growth curve with310 complete2013 participation donor trajectories, retaining within-player annual correlations and zero-participation paths. Rookie role and donor streams are keyed by player and shared across baseline/alternate allocations.39 domain tests and full API integration passed. Current256-pair Cleveland diagnostics:mean alternate-minus-baseline wins0.5234,Monte Carlo SE0.2237,improvement probability0.5234(MCSE0.0312); these illustrate convergence, not causal accuracy.

Scoring model still underpredicts held-out average combined points43.756 vs46.290 and overproduces shutouts0.01895 vs0.01030. Do not describe this as league-wide calibration passing. Other-team diagnostic artifacts from earlier versions remain pilot evidence, not current-version verification.

## November4 runtime and statistical gates

The runtime now carries an explicit pre2018 scoring-recency override (`+scoring-trailing3-v1`) and prior-utilization context policy. `analytics/runtime_loader.mjs` mirrors those policies and hashes the context, manifest, recency artifact, server loader and all prior model dependencies. Earlier simulation files without those hashes are stale until the QA gauntlet regenerates them; they cannot support current calibration claims.

`analytics/statistical_gates.py` requires all four current256-replicate diagnostics and retains adverse distribution or Monte Carlo precision flags. It also blocks a statistically validated-production claim for absent strict chronological five-year evidence, thin donor strata, known QB/LB undercoverage, unsupported specialists, and unvalidated snaps-to-wins effects. Gates are post-review diagnostic engineering thresholds, not preregistered significance tests. See `analytics/STATISTICAL_GATES.md`, `analytics/statistical_gates.json` and `analytics/VALIDATION_REMEDIATION.md` for exact current measurements and limitations. Successful software tests do not override these blockers.
