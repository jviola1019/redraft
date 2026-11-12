# REDRAFT QC run 2026-11-04T20-10-00-917Z-frozen-nov4-4f1691a8

Executed 2026-11-04T20:10:00.917Z through 2026-11-04T20:12:26.835Z. Source commit: e91cb416b374bf1e6831330d8e2a5a71962b2a63.

Structural/execution status: **passed**. Statistical status: **not-passed**. Exit code: **2**.

| Step | Type | Result | Seconds | Log |
|---|---|---|---:|---|
| data | structural | passed | 2.29 | [stdout](01-data.stdout.log) · [stderr](01-data.stderr.log) |
| team-context | structural | passed | 0.26 | [stdout](02-team-context.stdout.log) · [stderr](02-team-context.stderr.log) |
| warehouse | structural | passed | 0.12 | [stdout](03-warehouse.stdout.log) · [stderr](03-warehouse.stderr.log) |
| domain | structural | passed | 2.39 | [stdout](04-domain.stdout.log) · [stderr](04-domain.stderr.log) |
| model | structural | passed | 2.91 | [stdout](05-model.stdout.log) · [stderr](05-model.stderr.log) |
| five-year-model | structural | passed | 0.34 | [stdout](06-five-year-model.stdout.log) · [stderr](06-five-year-model.stderr.log) |
| forecast-audit | diagnostic | passed | 0.58 | [stdout](07-forecast-audit.stdout.log) · [stderr](07-forecast-audit.stderr.log) |
| scoring-backtest | diagnostic | passed | 0.55 | [stdout](08-scoring-backtest.stdout.log) · [stderr](08-scoring-backtest.stderr.log) |
| typecheck | structural | passed | 4.25 | [stdout](09-typecheck.stdout.log) · [stderr](09-typecheck.stderr.log) |
| api | structural | passed | 34.41 | [stdout](10-api.stdout.log) · [stderr](10-api.stderr.log) |
| league-matrix | structural | passed | 38.73 | [stdout](11-league-matrix.stdout.log) · [stderr](11-league-matrix.stderr.log) |
| distribution-cle | diagnostic | passed | 9.49 | [stdout](12-distribution-cle.stdout.log) · [stderr](12-distribution-cle.stderr.log) |
| distribution-ne | diagnostic | passed | 9.52 | [stdout](13-distribution-ne.stdout.log) · [stderr](13-distribution-ne.stderr.log) |
| distribution-kc | diagnostic | passed | 9.94 | [stdout](14-distribution-kc.stdout.log) · [stderr](14-distribution-kc.stderr.log) |
| distribution-sf | diagnostic | passed | 9.90 | [stdout](15-distribution-sf.stdout.log) · [stderr](15-distribution-sf.stderr.log) |
| score-sensitivity | diagnostic | passed | 18.43 | [stdout](16-score-sensitivity.stdout.log) · [stderr](16-score-sensitivity.stderr.log) |
| statistical-integrity-tests | structural | passed | 0.79 | [stdout](17-statistical-integrity-tests.stdout.log) · [stderr](17-statistical-integrity-tests.stderr.log) |
| statistical-gates | statistical | failed | 0.38 | [stdout](18-statistical-gates.stdout.log) · [stderr](18-statistical-gates.stderr.log) |

Source changes during run: none detected in the recorded input set.

Warnings retained: 6. Inspect [machine-readable report](report.json), [manifest](manifest.json) and [all-team structural matrix](league-matrix.json).

This fixed finite audit covers implementation behavior. It does not establish causal counterfactual accuracy, complete historical reconstruction, human recognition resistance, WebKit/iPhone behavior or production load limits. Statistical distribution flags and score instability remain adverse evidence when unit tests pass. No failed seed is replaced and every step runs at most once.
