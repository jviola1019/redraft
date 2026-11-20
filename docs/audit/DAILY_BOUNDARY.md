# Daily boundary review — 2026-11-20

## Scope and fixes

This bounded defensive review covers server disclosure consistency, UTC rollover, saved-run reconstruction and HTTP/data cache boundaries. It changes no daily assignment selection, scoring, historical data, models, quotas, remote settings or production deployment.

`view()` previously called the clock separately for its `identityRevealed` flag, seed visibility and `prospectViews()`. A response computed across midnight could therefore disagree about whether identities were sealed. A new `prospectDisclosure()` helper captures one timestamp and supplies it to both the flag and the field whitelist. The route uses that single decision for seed visibility, historical mappings and completed-result masking. Timestamp comparisons follow the existing UTC-normalized reveal policy, including failing closed on invalid timestamps.

New-run issuance now captures one timestamp before asynchronous daily configuration/database work. That same timestamp chooses the challenge date and sets the run creation date. Previously a request straddling midnight could bind yesterday's challenge to tomorrow's creation date, delaying reveal by a day. Requests remain assigned to the date on which issuance starts; this does not make a late in-flight request eligible to modify a closed challenge.

## Defensive test evidence

- `tests/daily-disclosure.test.ts`: exact 23:59:59.999 / 00:00:00.000 UTC boundary, a clock that advances over midnight between reads, deterministic reconnect from serialized saved state, opaque alias stability, hidden names/colleges/source/availability/exact measurements before reveal, exact source values after reveal, and invalid/offset/future timestamps.
- `node tests/run.mjs`: **86 passed, 0 failed**, including the four new cases.
- `pnpm exec tsc --noEmit`: passed.
- `node tests/api.integration.mjs --quick`: **14 passed, 0 failed; 259 route requests**, with `sourceChangedDuringRun: false`. Existing normal integration cases cover daily shared assignments, persisted recovery, old-attempt closure, UTC reveal, bundle reload and `no-store` response policy. This uses isolated SQLite and header-context adapters rather than production Cloudflare.

The async issuance-date change was inspected and covered by ordinary creation/rollover integration flows; a delayed D1 operation spanning midnight was not separately simulated. No production concurrency or edge-cache guarantee is claimed.

## Data and cache findings

The route returns `Cache-Control: private, no-store` and uses `force-dynamic`. Its response is reconstructed from saved state and current server time rather than persisted masked/revealed response bytes. Module-level scenario bundles contain shared server data and disclosure policies, not user responses. Scouting responses retain a whitelist; no source record spreading was introduced. Cache headers were already appropriate and remain unchanged.

Application headers do not prove that every external CDN/proxy honors them. Production identity-header trust, origin access, CDN configuration, deployed clock correctness and distributed D1 behavior remain operator verification requirements. Shared statistical profiles mitigate straightforward fingerprinting; they do not guarantee identity anonymity against historical auxiliary knowledge.

Changes were prepared in `/tmp/redraft-security-next-patch` on branch `redraft-daily-boundary`; no remote actions were performed. The branch starts after the separately verified Next.js dependency patch, but this commit contains only the Daily changes and this evidence document.
