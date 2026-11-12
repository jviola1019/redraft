# REDRAFT — The NFL Draft Time Machine

Draft the past. Rewrite the future.

Two modes share one historical drafting and simulation engine: a 2018 historical draft and a standardized UTC daily challenge. This is a research alpha, not a completed or causally validated NFL counterfactual model.

The reconstructed checkout uses real source records, actual fitted model artifacts and fresh tests. Old session tests do not certify this code. Current evidence and unfinished acceptance gates are in `TEST_RESULTS.md` and `KNOWN_LIMITATIONS.md`.

## Scope and limitations

32 franchises, the real seven-round 256-selection structure and 336 documented combine participants form the playable scenario. Another 39 actual historical draftees are baseline-only because using later selections to define the playable universe would introduce future-derived membership information. The eligible universe remains incomplete, and the actual baseline uses a broader pool than the user.

Scouting, current-pick trades, CPU decisions and paired five-season worlds are implemented as inspectable domain functions. Historical facts, model baseline and alternate outcomes remain separate. Rookie role estimates concern 200+ rookie snaps, not pure talent or validated five-year value. Individual future rosters/contracts, full NFL rules and five-year causal effects remain incomplete or assumption-dependent.

Name hiding is not anonymity. College, year, position, measurements and precise model outputs can identify an athlete. Server DTOs and random per-run IDs reduce direct leakage; the threat model and proposed human recognition study are in `docs/PROSPECT_IDENTITY.md`. No human recognition/fairness result is claimed.

## Repository map

| Path | Purpose |
|---|---|
| `app/` | interface, platform identity and authoritative API |
| `lib/engine.ts`, `lib/simulation.ts`, `lib/types.ts` | pure domain functions and contracts |
| `db/schema.ts`, `drizzle/` | actual runtime D1 schema/migrations |
| `research/`, `data/` | acquisition, sources, cleaning, snapshots and quality |
| `analytics/` | chronological fitting, predictions, diagnostics and pinned Python requirements |
| `tests/` | current domain, SQL and application checks |
| `docs/warehouse/` | separate normalized analytical target; not the runtime schema |
| `docs/erd/` | editable Mermaid and deterministic vector ERDs |

## Reproduce research and checks

Use the repository lockfile/package manager and the Sites skill’s dependency helper in the managed environment. Python dependencies are pinned under `analytics/requirements.txt`.

```sh
python3 -m pip install -r analytics/requirements.txt
python3 research/ingest.py
python3 research/clean.py
python3 analytics/train_models.py
python3 analytics/test_models.py
node tests/run.mjs
python3 tests/warehouse_test.py
python3 docs/erd/render_diagrams.py
```

Run only existing current scripts; additional data diagnostics and route-test commands are documented in their workstream reports. Network access is required for uncached provider downloads. No unsupported CollegeFootballData key is implied. Preserve source hashes and provenance.

`tests/run.mjs` bundles TypeScript test entries with installed esbuild into a temporary directory and executes Node’s test runner. The analytical SQL suite uses standard Python SQLite. An API adapter test, when present, does not replace actual hosted authentication/network tests.

## Run and build

```sh
npm run dev
npm run build
```

Managed preview uses `sites-preview start /workspace/sites/redraft` instead of a competing server. Production platform identity is distinct from any local test fixture. Durable state requires configured D1 and applied runtime migrations.

Generate a new runtime migration with `npm run db:generate`, inspect the SQL, and apply only unapplied migrations. After a build has generated `dist/server/wrangler.json`, the local D1 command shape is:

```sh
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/ACTUAL_PENDING_MIGRATION.sql
```

Replace the filename with the actual pending migration. Applied migrations are immutable. The analytical schema has overlapping conceptual names and must not be applied over runtime aggregate tables.

The Sites workflow preserves the existing Site ID, commits/pushes exact source, builds/packages its artifacts and deploys the saved matching version. Only a verified terminal result establishes publication. See `DEPLOYMENT.md`.

## Documentation

Read `PROJECT_SPEC.md`, `MASTER_PLAN.md`, `RESEARCH_LOG.md`, `SOURCE_REGISTRY.md`, `ARCHITECTURE.md`, `DATA_DICTIONARY.md`, `MODEL_EXPERIMENTS.md`, `SIMULATION_VALIDATION.md`, `DESIGN_SYSTEM.md`, `DECISIONS.md`, `TEST_RESULTS.md`, `PROGRESS.md`, `KNOWN_LIMITATIONS.md` and `DEPLOYMENT.md`.

Data attribution and redistribution restrictions are dataset-specific in the source registry. Original typography/vector graphics avoid copied logos and athlete photographs. No official NFL affiliation is implied.

## November 4 downloadable release

Use Node 22.13+ and the pnpm version in package.json. Install with
`pnpm install --frozen-lockfile`, then run `pnpm run build`. Apply the
included D1 migration before local play as described above. The source
archive excludes credentials, local saves, installed dependencies and raw
provider downloads. To reproduce the data audits, fetch the source files
with `python3 research/ingest.py`.

Run `python3 research/audit_class_coverage.py --as-of 2026-11-04` to audit
the recorded 2018–2026 draft files and completed playoff brackets. Only
2018 is playable. A five-season window can include completed, incomplete,
and future seasons. The report labels them individually and uses only
recorded scores through the requested date.

Run `node scripts/gauntlet.mjs --label local-audit` for the fixed regression
matrix. Exit 2 records statistical gate failures after structural checks
complete. The daily challenge uses midnight UTC. Completed draft identities
automatically refresh after closure in an open results view, with retries
on network errors and a refresh when the tab becomes visible.
