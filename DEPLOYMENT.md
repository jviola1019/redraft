# Deployment and operations

## November 12 portable source delivery

The authorized source repository is https://github.com/jviola1019/redraft . Local play uses Node 24, pinned pnpm, a production build and Wrangler's local D1 emulator; exact commands are in INSTALL.md. The loopback-only development sign-in is not public authentication. Do not expose it to a network interface or treat it as multi-user account security.

The current source is a research alpha, not a newly deployed or statistically cleared public release. A GitHub source ZIP is installable code and data, not a prebuilt native application. Raw downloads, dependencies and local saves are excluded. Actual build/API/Chromium/WebKit checks passed in [hosted run 43323677851](https://github.com/jviola1019/redraft/actions/runs/43323677851); this does not clear failed statistical gates or certify a deployed Site. Preserve dated audit reports and immutable source commits. Existing Site deployment status is separate from repository delivery.

Preserve the existing Site project identity in `.openai/hosting.json`. The restored source must be committed/pushed early and the final archive built from the exact deployed commit. Do not recreate a Site merely because transient source is absent. Deployment success is not statistical validation.

## Reproduce

The README records the current dependency/test commands. Ingestion needs provider network access; model fitting needs the pinned analytics Python requirements. Current source/model hash manifests must accompany results. Secret values stay in runtime configuration, never source or logs.

The actual runtime schema is `db/schema.ts` plus generated `drizzle/*.sql`. The separate `docs/warehouse/001_analytical_schema.sql` is an analytical target; do not apply it over runtime tables with the same names. Append migrations; do not modify already applied history. Apply pending runtime migrations to local preview before integration checks, and let the Sites deployment workflow apply production migrations.

## Hosted identity and recovery

Private hosted requests use platform identity. Every game/read/write/score path checks the authenticated owner. Development identity fixtures must never authorize anonymous production writes. Persist expected revision, request receipt, finalized daily configuration and scoring result. Retry uncertain requests with the same request ID or reload after conflict. A failed simulation cannot destroy a completed draft.

Private public-ID maps are sensitive game state: never expose them in browser exports or debug endpoints. Retain disclosure versions and avoid showing new-model predictions under old-run provenance. A closed challenge must not accept a new official score unless its completion policy explicitly permits it.

## Release steps

1. Re-run relevant checks on current source; inspect outputs and build artifacts.
2. Commit/push exact source with existing Site credential workflow.
3. Package the corresponding Worker/static output with its manifest.
4. Save/deploy the matching version to the existing audience.
5. Verify the terminal native deployment result and preserve commit/version/URL.
6. Record what browser and statistical validation was actually completed.

Monitoring, load/abuse testing, backup retention and a tested restoration runbook, vulnerability audit, privacy/retention policy and public-production operations remain unqualified unless separately evidenced.

## 2026-11-02 version migration
New runtime redraft-research-0.5-empirical pins the five-year donor artifact. Prior version saves remain review-only; daily challenge configuration is not rewritten mid-day. A previously initialized daily challenge using the earlier engine may be unavailable for new scored attempts until next UTC rollover. Source helper produces the exact pushed commit and matching deployment archive; preserve owner-private access.

## 2026-11-04 update
Engine0.6 pins prior2017 context and pre2018 trailing-three-year scoring calibration. Retired saves remain review-only; existing daily configurations are immutable and cannot silently adopt the new model mid-day. Production build succeeded;9clientJS chunks total848,483bytes. Targeted client-bundle check found no two tested prospect names or private donor-artifact marker; this is not exhaustive security certification.
