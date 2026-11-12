# Architecture

A modular monolith uses React/Vinext for the interface, authenticated server actions through `/api/game`, Cloudflare D1 for durable records, pure TypeScript domain functions, and Python offline ingestion/model fitting. The host supports Worker execution; the runtime imports compact model artifacts rather than trying to run a Python training service in the Worker.

## Boundaries

| Layer | Authoritative contents | Restriction |
|---|---|---|
| Raw sources | downloaded bytes, provider metadata, hashes | no raw outcome-rich catalog sent to browser |
| Clean historical data | normalized IDs, measurements, picks and games | original availability uncertainty retained |
| Features | pre-cutoff measured/derived predictors | no actual selection order or later careers |
| Outcome/reference store | actual selections and observed results | training only after labels observable, or post-draft references |
| Model artifact | version, target, training window, coefficients/priors | no unsupported starter/career claims |
| Domain engine | selections, asset ledger, simulations | no arbitrary client-submitted scores |
| API | identity, permissions, revisions, public-ID mapping, DTO | canonical IDs and hidden fields must stay server-side |
| Browser | presentation and user choices | no authority over state, random seed or daily score |

The runtime’s aggregate JSON schema is defined by `db/schema.ts` and generated `drizzle/*.sql`. It is distinct from the 52-table normalized analytical target in `docs/warehouse/001_analytical_schema.sql`. The analytical schema is executable and tested, but does not imply every table has historical data or is wired into runtime ETL.

## Historical time and model target

Use both effective date and original availability date. An old observed event in a recently retrieved file does not prove when the information became public. Later revisions and uncertain publication timestamps require explicit metadata. Training label availability must precede the model’s historical training cutoff, including the entire horizon of multiyear outcomes.

The current empirical player target is 200+ rookie offensive/defensive snaps. It captures observed opportunity/participation, not pure talent, starting probability or five-year value. Specialist outputs without an appropriate target remain unavailable rather than falsely scored. Five-year role/growth/retention/impact mappings are separate structural assumptions.

## Determinism and state

Run identity pins dataset, model, engine, scoring, disclosure and ensemble configuration. Game/season/player/matchup/replicate keys separate random streams; scouting requests do not consume a mutable league RNG. Home/away meeting direction distinguishes reciprocal games. Baseline and alternate worlds share defensible keyed shocks. Both derive records from games; user choices are never independent random win totals.

Server persistence uses an authenticated-owner predicate, expected revision and atomic compare-and-swap transition. Idempotency receipts bind request ID to owner/run/request digest and successful state. Trade assets transfer in one state transaction after ownership validation. A failed simulation request leaves the last valid draft/replicate intact. Review of older runs must not compute current predictions while labeling them as an older model.

## Identity disclosure boundary

The private catalog includes canonical IDs, names and exact source facts. The browser receives a whitelist DTO keyed by random per-run public identifiers. Store the inverse map only in authoritative private state. Names/canonical IDs must not leak through `selections`, board, scouted arrays, player results, errors, source URLs, sorted order or compiled client assets. Daily and historical policies differ only in permitted presentation; no prospect attributes are fabricated. Exact full-feature probabilities can themselves defeat masking.

A sanitized DTO protects against direct payload leakage, not all external recognition. Equivalence-class audits and human identification tests are separate from access-control tests. `docs/PROSPECT_IDENTITY.md` defines those limits and the proposed empirical plan.

## Analytical schema

Stable teams/players/colleges have namespaced identifiers; time-varying identity/roster/ownership rows have half-open validity intervals. Features and outcome labels are separate. Provenance attaches source/version/transformation/value-kind. Game and simulation exports never overwrite actual facts. Unique selections and assets, cutoff constraints, immutable daily/disclosure versions and per-run public-ID mappings are explicit.

The generic `fact_provenance(entity_type,entity_id)` lineage index needs ETL reconciliation because SQL cannot enforce a polymorphic entity FK. All concrete document/dataset references are foreign-key checked. The schema’s source/public-ID protections do not automatically enforce the aggregate runtime JSON contract; both require tests.

Index class/position/eligibility, feature cutoff/name, team/roster intervals, season/type, owner/state and daily score. Aggregate JSON is appropriate for a small alpha; larger detailed ensembles need normalized exports/summary accumulators rather than unbounded row rewriting.

## Multi-year runtime registry (November 12)

`lib/server-data.ts` registers immutable dataset/model/scouting bundles for 2018–2026. Every API transition resolves the stored game year through `getScenario`; creation validates requested years against the registry. Daily configuration pins its selected year and versions once per UTC date. Later classes use a reproduced pre-2018 role predictor, explicitly retaining unsupported fallbacks; that architecture does not imply later-class calibration. `analytics/runtime_loader.mjs` imports this same registry for engine diagnostics to avoid an inconsistent research-only scenario constructor.

Local play uses a loopback-bound Vite server, local D1 and the documented development sign-in; public deployment still requires appropriate production identity and durable services. Source delivery and live Site deployment are distinct operations.
