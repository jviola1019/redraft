# REDRAFT QC run 2026-11-04T20-33-22-463Z-rollover-playoff-648ccb60

Executed 2026-11-04T20:33:22.463Z through 2026-11-04T20:35:47.417Z. Source commit: 6174556e47603f430df7645c7ad0a911f27396cd.

Structural/execution status: **passed**. Statistical status: **not-passed**. Exit code: **2**.

| Step | Type | Result | Seconds | Log |
|---|---|---|---:|---|
| data | structural | passed | 1.60 | [stdout](01-data.stdout.log) · [stderr](01-data.stderr.log) |
| team-context | structural | passed | 0.17 | [stdout](02-team-context.stdout.log) · [stderr](02-team-context.stderr.log) |
| warehouse | structural | passed | 0.10 | [stdout](03-warehouse.stdout.log) · [stderr](03-warehouse.stderr.log) |
| domain | structural | passed | 2.00 | [stdout](04-domain.stdout.log) · [stderr](04-domain.stderr.log) |
| model | structural | passed | 2.56 | [stdout](05-model.stdout.log) · [stderr](05-model.stderr.log) |
| five-year-model | structural | passed | 0.29 | [stdout](06-five-year-model.stdout.log) · [stderr](06-five-year-model.stderr.log) |
| forecast-audit | diagnostic | passed | 0.51 | [stdout](07-forecast-audit.stdout.log) · [stderr](07-forecast-audit.stderr.log) |
| scoring-backtest | diagnostic | passed | 0.44 | [stdout](08-scoring-backtest.stdout.log) · [stderr](08-scoring-backtest.stderr.log) |
| typecheck | structural | passed | 2.34 | [stdout](09-typecheck.stdout.log) · [stderr](09-typecheck.stderr.log) |
| api | structural | passed | 36.25 | [stdout](10-api.stdout.log) · [stderr](10-api.stderr.log) |
| league-matrix | structural | passed | 42.02 | [stdout](11-league-matrix.stdout.log) · [stderr](11-league-matrix.stderr.log) |
| distribution-cle | diagnostic | passed | 9.89 | [stdout](12-distribution-cle.stdout.log) · [stderr](12-distribution-cle.stderr.log) |
| distribution-ne | diagnostic | passed | 10.21 | [stdout](13-distribution-ne.stdout.log) · [stderr](13-distribution-ne.stderr.log) |
| distribution-kc | diagnostic | passed | 9.39 | [stdout](14-distribution-kc.stdout.log) · [stderr](14-distribution-kc.stderr.log) |
| distribution-sf | diagnostic | passed | 9.53 | [stdout](15-distribution-sf.stdout.log) · [stderr](15-distribution-sf.stderr.log) |
| score-sensitivity | diagnostic | passed | 16.21 | [stdout](16-score-sensitivity.stdout.log) · [stderr](16-score-sensitivity.stderr.log) |
| statistical-integrity-tests | structural | passed | 0.81 | [stdout](17-statistical-integrity-tests.stdout.log) · [stderr](17-statistical-integrity-tests.stderr.log) |
| statistical-gates | statistical | failed | 0.34 | [stdout](18-statistical-gates.stdout.log) · [stderr](18-statistical-gates.stderr.log) |

Source changes during run: none detected in the recorded input set.

Warnings retained: 6. Inspect [machine-readable report](report.json), [manifest](manifest.json) and [all-team structural matrix](league-matrix.json).

This fixed finite audit covers implementation behavior. It does not establish causal counterfactual accuracy, complete historical reconstruction, human recognition resistance, WebKit/iPhone behavior or production load limits. Statistical distribution flags and score instability remain adverse evidence when unit tests pass. No failed seed is replaced and every step runs at most once.
