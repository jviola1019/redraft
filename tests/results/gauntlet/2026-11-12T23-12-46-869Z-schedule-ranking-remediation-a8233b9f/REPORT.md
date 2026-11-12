# REDRAFT QC run 2026-11-12T23-12-46-869Z-schedule-ranking-remediation-a8233b9f

Executed 2026-11-12T23:12:46.869Z through 2026-11-12T23:18:02.349Z. Source commit: ea235b1fca8d0dd2f7498fe9343f80d14a287251.

Structural/execution status: **passed**. Statistical status: **not-passed**. Exit code: **2**.

| Step | Type | Result | Seconds | Log |
|---|---|---|---:|---|
| data | structural | passed | 1.66 | [stdout](01-data.stdout.log) · [stderr](01-data.stderr.log) |
| team-context | structural | passed | 0.23 | [stdout](02-team-context.stdout.log) · [stderr](02-team-context.stderr.log) |
| warehouse | structural | passed | 0.11 | [stdout](03-warehouse.stdout.log) · [stderr](03-warehouse.stderr.log) |
| domain | structural | passed | 2.27 | [stdout](04-domain.stdout.log) · [stderr](04-domain.stderr.log) |
| model | structural | passed | 2.40 | [stdout](05-model.stdout.log) · [stderr](05-model.stderr.log) |
| five-year-model | structural | passed | 0.27 | [stdout](06-five-year-model.stdout.log) · [stderr](06-five-year-model.stderr.log) |
| forecast-audit | diagnostic | passed | 0.47 | [stdout](07-forecast-audit.stdout.log) · [stderr](07-forecast-audit.stderr.log) |
| scoring-backtest | diagnostic | passed | 0.44 | [stdout](08-scoring-backtest.stdout.log) · [stderr](08-scoring-backtest.stderr.log) |
| typecheck | structural | passed | 2.94 | [stdout](09-typecheck.stdout.log) · [stderr](09-typecheck.stderr.log) |
| api | structural | passed | 45.22 | [stdout](10-api.stdout.log) · [stderr](10-api.stderr.log) |
| league-matrix | structural | passed | 39.11 | [stdout](11-league-matrix.stdout.log) · [stderr](11-league-matrix.stderr.log) |
| all-year-matrix | structural | passed | 99.37 | [stdout](12-all-year-matrix.stdout.log) · [stderr](12-all-year-matrix.stderr.log) |
| playoff-backtest | structural | passed | 0.62 | [stdout](13-playoff-backtest.stdout.log) · [stderr](13-playoff-backtest.stderr.log) |
| all-year-distributions | diagnostic | passed | 48.07 | [stdout](14-all-year-distributions.stdout.log) · [stderr](14-all-year-distributions.stderr.log) |
| distribution-cle | diagnostic | passed | 11.95 | [stdout](15-distribution-cle.stdout.log) · [stderr](15-distribution-cle.stderr.log) |
| distribution-ne | diagnostic | passed | 12.40 | [stdout](16-distribution-ne.stdout.log) · [stderr](16-distribution-ne.stderr.log) |
| distribution-kc | diagnostic | passed | 12.19 | [stdout](17-distribution-kc.stdout.log) · [stderr](17-distribution-kc.stderr.log) |
| distribution-sf | diagnostic | passed | 11.90 | [stdout](18-distribution-sf.stdout.log) · [stderr](18-distribution-sf.stderr.log) |
| rank-sensitivity-tests | structural | passed | 0.07 | [stdout](19-rank-sensitivity-tests.stdout.log) · [stderr](19-rank-sensitivity-tests.stderr.log) |
| score-sensitivity | diagnostic | passed | 22.29 | [stdout](20-score-sensitivity.stdout.log) · [stderr](20-score-sensitivity.stderr.log) |
| statistical-integrity-tests | structural | passed | 0.66 | [stdout](21-statistical-integrity-tests.stdout.log) · [stderr](21-statistical-integrity-tests.stderr.log) |
| statistical-gates | statistical | failed | 0.28 | [stdout](22-statistical-gates.stdout.log) · [stderr](22-statistical-gates.stderr.log) |

Source changes during run: none detected in the recorded input set.

Warnings retained: 19. Inspect [machine-readable report](report.json), [manifest](manifest.json) and [all-team structural matrix](league-matrix.json).

This fixed finite audit covers implementation behavior. It does not establish causal counterfactual accuracy, complete historical reconstruction, human recognition resistance, WebKit/iPhone behavior or production load limits. Statistical distribution flags and score instability remain adverse evidence when unit tests pass. No failed seed is replaced and every step runs at most once.
