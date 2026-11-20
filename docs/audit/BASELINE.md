# November 19 integration baseline

GitHub main and HEAD both resolved to cff1f1eb9b43b5d778b45ed42c6c68a6a4dcbca7, with 881 tracked paths. The November 12 release report records 33 passing, 9 failing and 7 unsupported statistical gates. The interrupted exposure revision was absent from the remote. Node v24.22.3 and pnpm 11.25.0 installed the frozen lockfile.

## Integration plan

Inspect the baseline → repair the participation unit mismatch and score comparator → validate the API version and request contracts → improve phone drafting → execute frozen structural, statistical and browser checks. Each workstream owns an isolated file set. Revert its commit to roll back. Gate passage requires executed evidence against unchanged actual outcomes.

## Source inventory at baseline

- `.github/workflows/ci.yml`
- `analytics/additional_order_sources.py`
- `analytics/all_year_diagnostics.mjs`
- `analytics/five_year.py`
- `analytics/five_year_tests.py`
- `analytics/forecast_audit.py`
- `analytics/identity_audit.py`
- `analytics/plot_diagnostics.py`
- `analytics/pooling_validation.py`
- `analytics/project_scenarios.py`
- `analytics/qb_transition_experiment.py`
- `analytics/qb_uncertainty.py`
- `analytics/rank_sensitivity.mjs`
- `analytics/render_reports.py`
- `analytics/runtime_loader.mjs`
- `analytics/score_distribution.py`
- `analytics/score_sensitivity.mjs`
- `analytics/scoring_origin_audit.py`
- `analytics/scoring_recalibration.py`
- `analytics/simulation_diagnostics.mjs`
- `analytics/statistical_gates.py`
- `analytics/test_models.py`
- `analytics/test_qb_transition_experiment.py`
- `analytics/test_qb_uncertainty.py`
- `analytics/test_rank_sensitivity.mjs`
- `analytics/test_statistical_gates.py`
- `analytics/train_models.py`
- `app/api/game/route.ts`
- `app/chatgpt-auth.ts`
- `app/globals.css`
- `app/layout.tsx`
- `app/page.tsx`
- `components/redraft/draft-console.tsx`
- `components/redraft/guided-board.tsx`
- `components/redraft/methodology.tsx`
- `components/redraft/pixel-field.tsx`
- `components/redraft/primitives.tsx`
- `components/redraft/results.tsx`
- `components/redraft/stadium.tsx`
- `components/redraft/team-context.tsx`
- `components/redraft/types.ts`
- `db/index.ts`
- `db/schema.ts`
- `drizzle/0000_spotty_patriot.sql`
- `drizzle/meta/0000_snapshot.json`
- `drizzle/meta/_journal.json`
- `lib/connector-context.ts`
- `lib/connector-contract.mts`
- `lib/connector-errors.mts`
- `lib/connector-preview.d.ts`
- `lib/connectors.ts`
- `lib/engine.ts`
- `lib/scouting.ts`
- `lib/server-data.ts`
- `lib/simulation.ts`
- `lib/types.ts`
- `lib/utils.ts`
- `research/audit_class_coverage.py`
- `research/audit_expansion.py`
- `research/build_scenarios.py`
- `research/clean.py`
- `research/diagnostics.py`
- `research/identity_risk.py`
- `research/ingest.py`
- `research/reconcile_order.py`
- `research/team_context.py`
- `research/test_data.py`
- `research/test_team_context.py`
- `research/trades.py`
- `research/verify_invitees.py`
- `tests/all-years.mjs`
- `tests/api.integration.mjs`
- `tests/api.smoke.mjs`
- `tests/architecture.test.ts`
- `tests/browser.mjs`
- `tests/calibrate-trades.ts`
- `tests/context-policy.test.ts`
- `tests/engine.test.ts`
- `tests/five-year.test.ts`
- `tests/league-matrix.mjs`
- `tests/local-http.mjs`
- `tests/playoff-backtest.mjs`
- `tests/playoff-rules.test.ts`
- `tests/qa-simulation.test.ts`
- `tests/run.mjs`
- `tests/scenario-data.test.ts`
- `tests/scouting.test.ts`
- `tests/warehouse_test.py`
- `tests/year-contract.test.ts`

See ../erd/ for the conceptual, logical and physical diagrams, and ../../ARCHITECTURE.md for service boundaries.
