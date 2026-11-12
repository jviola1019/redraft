# REDRAFT quality gates

The gauntlet is a finite, reproducible audit. It does not prove that every possible game is correct or that the counterfactual model is causally valid.

Run from the repository root after installing JavaScript and pinned Python dependencies and restoring source data:

```sh
node scripts/gauntlet.mjs --label final-audit
```

Each invocation creates a new directory under `tests/results/gauntlet/` with an execution manifest, source hashes before and after, command arguments, exit codes, timestamps, individual stdout/stderr logs, copies of fresh diagnostic reports, and a readable `REPORT.md`. Existing run directories are never reused. Completed evidence files are write-protected; version control provides durable history. Local write protection is not cryptographic tamper-proof storage.

## Fixed coverage

| Check | Coverage |
|---|---|
| Data | Historical order reconciliation, eligible population, identity collisions, actual game coverage, observed snap coverage and feature/outcome boundaries |
| Warehouse | Relational, temporal, ownership, disclosure and simulated-version constraints |
| Domain | Draft/scouting/trading, time cutoffs, deterministic streams, schedules, five-year vectors and independent game/record reconciliation |
| Model | Existing chronological split/metric recomputation, missingness and future-data poisoning tests |
| Five-year model | Label availability, real joint donor vectors, frozen forecasts and retrospective-versus-strict distinction |
| Forecast and scoring audits | Recompute finite-donor forecast diagnostics and the pre-2018 chronological scoring-window comparison, including future-outcome poisoning |
| Typecheck | Actual project TypeScript configuration |
| API | Actual route/auth functions through an isolated SQLite D1 adapter, including authoritative state, daily attempt ownership and completion |
| All-team structural matrix | Every one of 32 teams, three prespecified draft seeds, two paired five-season replicates per case; one full draft and paired-world replay per team |
| Distribution diagnostics | 256 paired replicates each for CLE, NE, KC and SF, retaining distribution flags and Monte Carlo error |
| Score sensitivity | Four prespecified policies, 128 paired replicates per policy and 11 weight settings |
| Statistical aggregation | Position-specific support, forecast coverage, source/version freshness and unfavorable findings when the statistical gate script is present |

The structural matrix checks 96 complete drafts and 192 paired replicates, representing 384 five-season world executions. The 32 replay checks are additional deterministic repeats. Common seed families are reused across franchises, so these are not 384 independent statistical trials; historical-baseline worlds repeat under shared random numbers. Every regular-season record and points total is recomputed from actual generated games. The audit checks player and asset conservation, divisional opponents and venues, no duplicate weekly games, playoff counts and seeds, champion consistency, cohort availability/role capacities, and five-year headline reconciliation. It uses the production pooled model and context policy provided by `analytics/runtime_loader.mjs`.

## Outcomes and exit codes

| Exit | Interpretation |
|---|---|
| `0` | Executed implemented checks found no adverse result; unsupported product acceptance criteria still remain |
| `1` | A structural/execution check failed, a required fresh artifact is absent, the run was interrupted, or recorded source inputs changed during the run |
| `2` | Execution completed, but statistical diagnostics found adverse evidence or calibration remains unsupported |

Software passes do not override bad forecast coverage, distribution discrepancies, or score rank instability. Distribution flags are descriptive predictive checks, not multiplicity-corrected hypothesis tests. Score-weight sensitivity measures the tested policies and assumptions; it cannot establish that small leaderboard differences reflect GM skill. Monte Carlo standard errors describe simulation sampling variability, not uncertainty about model correctness.

## Loop discipline

Each step executes once. Seeds, teams and replicate counts are fixed in source before outcome inspection. A failure stays in the report. Fix an identified defect, explain the change, and run a new recorded audit. Never discard a failed seed, change a threshold after seeing the result, or repeat samples until a favorable outcome appears.

Historical 2018 outcomes have already been examined during development. Any tuning motivated by those outcomes is development evidence and cannot be relabeled as an untouched 2018 test. Strict historical gameplay may only use pre-cutoff model inputs; later retrospective evaluation must be identified separately.

## Remaining release gates

This runner does not perform production Cloudflare load/abuse testing, real iPhone or Safari/WebKit validation, human identity-recognition experiments, a full visual regression approval process, licensing clearance, full historical roster/contract reconstruction, or complete NFL tiebreaker validation. The normalized analytical schema is not the runtime D1 storage implementation. Report these limits separately from the checks actually executed.

## Frozen audit — 2026-11-04

The [complete run report](../tests/results/gauntlet/2026-11-04T20-10-00-917Z-frozen-nov4-4f1691a8/REPORT.md) records the 20:10:00–20:12:26 UTC execution. All structural/execution checks passed, and no recorded source inputs changed. The process returned `2` because statistical requirements did not pass. Evidence files were inspected and write-protected after completion.

Fresh checks: 15 data, 5 historical-context, 20 warehouse, 48 domain/scouting/context, 15 model, 7 five-year, and 8 statistical-integrity tests passed. These counts overlap where the domain runner invokes the warehouse suite; they must not be summed as independent evidence. API integration passed 15 cases and 304 actual route calls using its isolated SQLite/platform adapter. The all-team matrix completed all 96 drafts, 192 paired replicates and 32 replays. Its 1,920 season executions reconciled 503,808 regular-season games.

The statistical aggregation retained 33 passed, 9 failed, 7 unsupported and 0 stale gates. Quarterback nominal 95% snap intervals covered 12 of 16 reused 2018 outcomes (75%); only three pre-cutoff QB donors had the positive rookie-role label. League baseline mean total scoring remained 45.046 versus 46.290 observed, and zero-score frequency remained too high. Four scenario reports reuse the same baseline random numbers, so their repeated distribution failures are not four independent findings. Maximum measured paired-win MCSE was 0.209 wins; probability MCSE was 3.125 percentage points. Those measure sampling precision only. The best-ranked policy changed under 2 of 11 score-weight settings, with minimum rank correlation 0.8.

These retained findings block a claim of full statistical validation. They remain visible in the [statistical evidence](../tests/results/gauntlet/2026-11-04T20-10-00-917Z-frozen-nov4-4f1691a8/artifacts/analytics/statistical_gates.json), alongside the measured improvements and structural passes.
