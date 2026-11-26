# Draft Room Edition acceptance plan

The decision under review is whether a player can run a historically situated draft, discover real selections immediately, and explore one coherent five-year timeline. Production requires every critical gate below. This branch starts at e51e69061215dcb4ddbf66d29643335798b8920c, the head of the existing audit PR. Main separately maintains the Pages landing site. The implementation branch targets the audit branch for review.

| Workstream | Acceptance evidence | Independent challenge |
|---|---|---|
| Draft setup and tracker | Select/randomize year and franchise, price visible scouting choices, inspect every committed pick, enforce permissions and restore saved state | Inspect actual HTTP responses, tabs, traded and accelerated selections, and the separate Daily UTC embargo |
| Football rules | Replay all four postseason rounds from prior winners, 2018–2025. Reconcile recorded OTs through the last available 2026 game. Exercise simulated regular/postseason OT for every season through 2030 | Separate synthetic boundary tests, PBP/schedules comparison and deterministic legacy saves |
| CPU and development | Evaluate historical top-32/top-100 overlap, slot errors, exposure, tail errors and interval width against registered baselines | Preserve failed candidate results. Leave prospective QB year five sealed |
| Five-year experience | Saved season progression, simple results, full league standings, inspectable playoff games, player careers and franchise legacy | Cross-check UI with the persisted canonical replicate. Qualify every cohort-only statistic or award |
| Visual and accessible interaction | Three design directions, 12 surface references, responsive game screens, keyboard focus, touch and reduced motion | Real browser journeys and actual screenshots. Physical-device sign-off remains separate |
| Data and disclosure | Versioned prospect universes, source dates and missingness. Every new eligible prospect has contemporaneous source evidence | Recompute source joins without actual selections and compare old-save digests against the source commit |
| Security and operations | Owner isolation, server authority, bounded jobs, duplicate handling, client-asset inspection, least privilege | Verify deployment-specific controls, backups, rollback and hosting before authorization |

## Verification sequence

1. Freeze an untouched checkout, inventory the repository, compare branches and reproduce baseline errors.
2. Implement guarded changes with dated source records. Maintain the original ranked Daily identity policy and all supported old engine versions.
3. Run unit tests, analytical and API checks, real D1, browser journeys, full year/team matrix and diagnostic gate ledger. Record adverse and unsupported outcomes.
4. Check the final Git tree and hosted Actions conclusion on the candidate. The staging and deployment decisions require separate evidence.

## Time and performance budgets

Before the final candidate run, retain the existing 1,800,000-byte serialized state guard and four paired replicates per request. Set local regression thresholds of 30 seconds for a draft action to become actionable, 15 minutes for the full 256-pair browser simulation, and zero offscreen modal edges beyond a one-pixel rounding allowance. These intentionally broad smoke-test thresholds detect broken journeys. They do not establish acceptable production latency. Measure mobile load, server CPU, D1 and field interaction on target infrastructure before setting a production SLO.

## Production blockers

No NFL-wide award or leader can be inferred from one rookie cohort. A label, unsupported rank or generated narrative cannot satisfy this gate. Predictions about future rules, actual future seasons or alternate outcomes must retain their simulated status. Closed chronological benchmarks, hosted software checks and physical-device evidence are separate requirements.
