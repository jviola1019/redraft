> **Current status:** source recovery is complete, including a tested replacement for the missing year-contract suite. Fresh structural checks pass; full statistical release is blocked. See [current evidence](docs/release/CURRENT_RELEASE.md). Earlier recovery notices below describe the interruption.

> **Recovery checkpoint:** This branch preserves critical source and season data but omits some test evidence. The original frozen checkout could not be fully recovered byte-for-byte. See [recovery status](docs/security/RECOVERY_STATUS_2026-11-12.md).

# REDRAFT — The NFL Draft Time Machine

Draft the past. Rewrite the future.

REDRAFT is a playable **research alpha**, with exactly two modes: historical drafting and a shared UTC daily challenge. Both use the same seven-round draft, scouting, trade and five-season simulation engine. It is not a completed or statistically cleared production release.

## Run locally

Use Node 24 and pnpm 11.25.0. No paid API key or Cloudflare account is required for local play.

```sh
git clone https://github.com/jviola1019/redraft.git
cd redraft
pnpm install --frozen-lockfile
pnpm run build
pnpm run db:local-init
pnpm run dev:local
```

Open `http://127.0.0.1:5173/signin-with-chatgpt?return_to=%2F`. This is a loopback-only development identity. Local saves stay in the local D1 emulator. See [INSTALL.md](INSTALL.md) for setup, tests, research dependencies and deployment limits.

## What is implemented

- Real recorded prospects and draft slots, with explicit per-year source/cutoff metadata.
- Anonymous shared scouting profiles, explanations for beginners, and post-draft identity disclosure. Daily identities remain hidden until the challenge closes at midnight UTC.
- CPU selections, current-year pick trading, persistent saves and reproducible keyed random streams.
- Paired historical-baseline and alternate five-season league simulations, plus completed actual-history comparisons. Unobserved actual outcomes remain null.
- Historical 12/14-team playoff formats, reseeding and score-level tiebreak criteria.
- Original SVG pixel football graphics driven by application state, with reduced-motion styling.

The app lists enabled scenarios; [the coverage manifest](data/processed/scenario-coverage.json) records source limitations. A dataset existing on disk is not a claim that its forecasts are calibrated.

## What is not cleared

The original release criteria remain unmet. Quarterback tail uncertainty, scoring distribution, score-weight sensitivity, exact draft-day rosters, historical schemes and individual future roster/draft management need further work. Five-year snaps are sampled from a limited empirical donor model; their conversion to team strength is an assumption. Later classes use a frozen pre-2018 rookie-role model, with unsupported cases labeled as fallback priors. No causal alternate-history accuracy is claimed.

Eligibility is restricted to verified/source-recorded combine participants or invitees, not every draft-eligible player. The actual historical baseline includes additional reference-only players. These unequal pools limit decision comparisons. Original publication timestamps are incomplete. Full net-touchdown tiebreaks, detailed overtime, contracts and future-pick trades are not implemented.

Browser checks have a runnable test and CI job, but the local Chromium attempt was blocked by environment socket restrictions. HTTP/server tests do not certify mobile Safari, accessibility compliance or visual quality. No approved visual-regression baseline or human recognition study exists.

## Reproduce checks

```sh
pnpm test
pnpm exec tsc --noEmit
pnpm run test:api
pnpm run test:playoffs
node tests/all-years.mjs
python3 tests/warehouse_test.py
node tests/local-http.mjs
# On a machine that permits browser execution:
pnpm exec playwright install --with-deps chromium webkit
pnpm run test:browser
REDRAFT_BROWSER=webkit pnpm run test:browser
```

The full research audit needs Python dependencies and raw source downloads:

```sh
node scripts/setup.mjs --python
. .venv/bin/activate
python research/ingest.py
node scripts/gauntlet.mjs --label independent-check
```

Exit 2 means adverse statistical evidence remains. Repeating the audit until it happens to pass is not validation. Source hashes, logs, finite seed matrices, rejected experiments and limitations are retained.

## Architecture and documentation

`app/` contains the interface and authoritative API; `lib/` holds the draft/simulation contracts; `drizzle/` contains runtime D1 migrations; `research/` and `analytics/` contain reproducible data/model work; `tests/` contains software and analytical checks. The normalized analytical warehouse is separate from the runtime schema.

Start with [the release plan](docs/release/PLAN_2026-11-12.md), [test evidence](TEST_RESULTS.md), [known limitations](KNOWN_LIMITATIONS.md), [source registry](SOURCE_REGISTRY.md) and [deployment instructions](DEPLOYMENT.md). The remaining required project reports are maintained at the repository root.

No official NFL affiliation is implied. Source-specific data rights and attribution are documented separately. Official logos and athlete photographs are not bundled.
