> The [statistical clearance review](../audit/CLEARANCE_REVIEW.md) reproduces the 40/6/7 decision, documents the evidence behind each blocker and repairs three permissive audit checks.

> The [latest fixture and Pages review](FIXTURE_REVIEW.md) supersedes the earlier CPU, test and delivery status below.

# REDRAFT review · November 19, 2026, Chicago

**Research alpha. Production and scientific clearance withheld.** The review build covers the 2018 through 2026 draft classes. It has two playable modes. Observed records are restricted to completed seasons. Each draft forecasts five seasons, so recent classes include future projections.

[Review pull request](https://github.com/jviola1019/redraft/pull/1) · [Install](../../INSTALL.md) · [Acceptance matrix and roadmap](../audit/REQUIREMENTS_MATRIX.md) · [Nine original failures](../audit/FAILURE_REGISTER.md) · [November 12 checkpoint](REVIEW_2026-11-12.md)

## What changed in gameplay

- Career donors now retain their per-scheduled-game participation when moving from 16-game seasons into 17-game seasons. The engine and model compatibility identifiers changed. Recorded outcomes and gate tolerances stayed fixed. Implementation lives in `lib/engine.ts`, `lib/server-data.ts` and `lib/simulation.ts`.
- The phone draft room shows the pixel field, gives instructions the full column, and connects scouting, comparison and the final selection. The board offers group-level evidence. See [phone comparison and browser scope](../audit/BROWSER_QA.md).
- Daily issuance, reveal flags, individual fields, historical mappings and seed disclosure now share one authoritative timestamp per relevant operation. Exact boundary and reconnect cases are in [the boundary report](../audit/DAILY_BOUNDARY.md).
- The request body reader rejects ambiguous content types and malformed UTF-8 within its existing byte limit. The framework was patched to Next.js 16.4.5. The dependency scan fell from seven moderate findings to zero at the reviewed snapshot. See [threat review](../audit/SECURITY.md) and [dependency verification](../audit/DEPENDENCY_PATCH.md).

## Statistical decision

| Checkpoint | Pass | Fail | Unsupported | Meaning |
|---|---:|---:|---:|---|
| November 12 | 33 | 9 | 7 | Previous 49 checks |
| November 19 local / November 20 UTC | 40 | 6 | 7 | Three original subgroup coverage checks improved, four additional checks verify source hashes |

The failed QB intervals covered 12/16 observed snap totals and 13/16 games totals in the reused 2018 subgroup. The Cleveland, Kansas City, New England and San Francisco league checks share one historical baseline. It averaged 45.05 points against 46.29 observed and a 1.61% team shutout rate against 1.03% observed. These discrepancies survive increased simulation replication. Seven alternative rubric configurations changed the set of leaders in the ranking sensitivity study. The minimum rank correlation was 0.4.

### Candidate decisions

| Experiment and evaluation | Baseline → candidate | Decision |
|---|---|---|
| QB annual states → five-year snaps. Historical origins 2016/17, 32 QBs and 8,192 paired paths per origin. | Persistence CRPS 748.53 → 745.65. Paired difference −2.88, 95% player-bootstrap interval [−38.36, 29.61]. | Research only. Five-year advantage uncertain. [Hindcast](../../analytics/qb_five_year_hindcast_REPORT.md) |
| Fixed 2013 versus all fully mature earlier QB cohorts. Origins 2019–21, 50 QBs. | CRPS 862.21 → 800.14. Difference −62.07 [−115.85, −12.39]. 95% coverage 39/50 → 49/50. Mean width 2,029 → 5,217 snaps and point MAE increased. | Useful later-origin reference. Additional careers were unavailable in April 2018. Only three assessment cohorts, known IDs, no independent new test or player conditioning. [Mature QB experiment](../../analytics/qb_mature/qb_mature_donor_review_REPORT.md) |
| Hurdle score model. Historical origins evaluated in 2016/17. | Total CRPS 7.747 → 7.739. Margin CRPS 7.499 → 7.501. | Research only. Mixed effects. [Results](../../analytics/score_distribution.md) |
| Historical exact score pairs. Two historical evaluation windows and a 1,000-season diagnostic. | 2016/17 margin CRPS 7.496 → 7.606. Team-win variability compressed. | Rejected. Worsened margins and individual team scores. [Score-pair experiment](../../analytics/empirical_score_pairs_REPORT.md) |
| CPU position prior from 1,272 selections in 2013–17. Nine later classes, 108 drafts per policy. | Round-one position mix improved in every class. Franchise allocation worsened in every class. | Rejected. The existing CPU selected just one round-one QB in 108 drafts. [Paired CPU experiment](../audit/cpu_candidate/REPORT.md) |

CRPS measures error in a forecast distribution. Lower is better. Intervals shown above condition on the studied cohorts. Independently verified causal effects of alternative choices and calibrated future player-to-wins effects remain unsupported.

## Would college give away the player?

Among 2,944 eligible records across the nine drafts, position alone singled out seven. College and position singled out 2,140 (72.7%). Exact position, height and weight singled out 2,358 (80.1%). These are within-class matches on the recorded fields. Human recognition rates have not been measured. Keep college and exact measurements sealed on competitive boards. Reveal the historical identity after completion in historical mode and after the UTC embargo in Daily. [Per-class counts and hashes](../audit/college_board_risk.json)

## Release evidence and outstanding work

[Baseline and source inventory](../audit/BASELINE.md) · [Data and historical integrity](../audit/DATA_INTEGRITY.md) · [Dependency graph](../audit/DEPENDENCY_GRAPH.md) · [Normalized and runtime schemas](../../ARCHITECTURE.md) · [Gate definitions](../../analytics/STATISTICAL_GATES.md)

The original nine failures, further high-severity findings, acceptance criteria and research requirements are recorded in the [failure register](../audit/FAILURE_REGISTER.md). Missing evidence includes complete draft-day rosters, schemes, cap details, individual simulated future personnel movements, stable managerial rankings, physical-device and production performance, edge identity and operational recovery. Production deployment has not occurred.

## Verification record

- Frozen engine and API source `25be24769f5b425f664298209baedab0ad677395`. The 22-step run finished with zero source drift. Structural checks passed. Exit 2 preserves the failed scientific release decision. [Full per-step receipt](../audit/runs/verified-report.json) · [logs, per-year cases and artifacts](../audit/runs/2026-11-20T02-13-40-005Z-release-review-8dc7c1bf.zip)
- 89 domain tests and 16 API integration cases passed. The API suite made 458 requests across historical and Daily lifecycles. All nine classes completed the structural matrix of 864 full drafts, 1,728 paired simulation replicates and 288 replay checks. Eight recorded seasons passed the playoff reconstruction. These checks establish mechanical consistency and historical bracket reconstruction. Forecasting future playoff teams is a separate unresolved validation question.
- [Hosted lifecycle run 44656085644](https://github.com/jviola1019/redraft/actions/runs/44656085644) passed both complete historical and Daily journeys at 390 CSS pixels. The browser finished 256 historical picks and 259 Daily picks, displayed five seasons per mode and confirmed the official Daily result in the leaderboard. The shorter journeys also passed Chromium and WebKit at desktop, tablet, iPhone-emulation and narrow-phone sizes.
- [Performance breakdown](../audit/PERFORMANCE_REPORT.md) · [92-item security register](../audit/SECURITY_REGISTER.md) · [dependency scan receipts](../audit/dependency-evidence/) · [branch and CI](https://github.com/jviola1019/redraft/pull/1/checks)

## Reproduction

Use Node 24, pnpm 11.25.0 and the frozen lockfile. Install and play using INSTALL.md. Raw research inputs require separate acquisition and are enumerated in SOURCE_REGISTRY.md.

```sh
node tests/run.mjs
node tests/api.integration.mjs
node scripts/gauntlet.mjs --label independent-review
RD_ROOT="$PWD" RD_QB_OUT="$PWD/analytics" python analytics/test_qb_five_year_hindcast.py
RD_ROOT="$PWD" python analytics/qb_mature/test_qb_mature_donor_review.py
REDRAFT_GAMES_CSV="$PWD/data/raw/games.csv" python analytics/test_empirical_score_pairs.py
python research/college_board_risk.py
```

For full UI tests, first build, initialize the local database and install Playwright Chromium/WebKit. Run `node tests/browser-full-run.mjs --start-server` using a fresh local Daily identity. Its actions submit a real local score. The hosted configuration is recorded in .github/workflows/ci.yml.

The exposure correction conditions each simulated season on its historical schedule length. Applying a future rule change to a five-year world is a scenario assumption. The league's later adoption of 17 games could not have informed an April 2018 GM. The draft boards do not receive these future rules as prospect traits. The resulting research forecasts must be interpreted conditional on the schedule regime.

## Forecasting playoff qualification

Eight completed drafts, 64 simulations per origin and all 32 franchises produced 960 evaluable forecasts over 256 distinct observed team-seasons. Overall Brier score was 0.24016 against 0.24492 for assigning every team its season's playoff-slot prevalence. The first-year forecast did better (0.22521 against 0.24316). At year four it did worse (0.25788 against 0.24609). Year five was close to the prevalence benchmark. The report separates Monte Carlo error from generalization uncertainty and describes the retrospective schedule and rule assumptions. Incomplete seasons never receive a historical qualification label. [Prediction audit by year and horizon](../../analytics/playoff_forecast_REPORT.md)

The corrected 2021 baseline assigns San Francisco’s third pick to Trey Lance’s existing eligible record. All 323 eligible profiles and their numerical projections are preserved. Older 2021 saves stay available for review. The API rejects attempts to modify them under the new dataset version. [Correction, provenance and tests](../audit/trey_reference_fix/REPORT.md)

The source package installer passed all 89 domain tests. The production build was also served locally with Wrangler. Its homepage returned HTTP 200 and the anonymous game API returned HTTP 401. Separate authenticated local HTTP tests exercised D1, scouting and persistent reload. [Build inspection](../audit/BUILD_INSPECTION.json)

## Delivery

Review branch `redraft-2-audit`. [Hosted runtime revision e67a981](https://github.com/jviola1019/redraft/commit/e67a9812b2817226575f3ff366efadb1a96d5997) matches the full tree of local source `25be247`. [Hosted checks for this exact revision](https://github.com/jviola1019/redraft/actions/runs/44659458459). The downloadable review source includes the build, install instructions, processed scenarios, compact model artifacts, test scripts and frozen audit receipts. Dependency installation is required. Raw research downloads are governed separately. The pull request is open for review. Main and production have not been promoted.
