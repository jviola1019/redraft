# Fresh testing evidence

## Current verified checkpoint

Hosted [implementation workflow 43323677851](https://github.com/jviola1019/redraft/actions/runs/43323677851) passed Chromium and WebKit desktop/phone smoke tests on the recorded source. Receipt and per-browser reports: [hosted browser evidence](tests/results/hosted-browser/43323677851/receipt.json). Local launch failures remain retained. The follow-up also passed entry completion and dialog bounds/focus checks; four captures were visually inspected. No approved visual-regression baseline or physical-device test is implied.

The recovered 2018–2026 research-alpha implementation was freshly tested. Structural checks passed; statistical release remains blocked (33 pass, 9 fail, 7 unsupported). See [current evidence](docs/release/CURRENT_RELEASE.md) for the authoritative scope and links. Older dated entries below are historical records.

Earlier session counts are not evidence for the reconstructed checkout. This report is updated only from current files and executions. Synthetic fixtures stay test-only.

| Check | Fresh result | Scope |
|---|---|---|
| `python3 tests/warehouse_test.py` |20 passed |52-table analytical schema; FK, temporal, missingness, ownership, duplicate selection, baseline-only eligibility, replicate uniqueness, immutable daily/disclosure and public-ID mapping constraints |
| Domain engine | Owner reports 20 freshly passing tests; independent rerun pending | Source must remain unchanged or be rerun before final release claim |
| Runtime D1/API | Pending rebuilt service/migrations | Analytical schema tests do not substitute for runtime/HTTP tests |
| Historical data/model checks | Workstream artifacts pending final inspection | No earlier counts copied forward |
| Browser/visual/accessibility | Pending current build | No WebKit/real-iPhone/visual-regression certification inferred |
| `python3 docs/identity_linkage_audit.py` | Exact-match uniqueness computed on336 actual combine rows |265 unique college+position profiles;334 unique after height/weight; not human recognition rates |
| Human recognition/fairness study | Not executed | Protocol in docs/PROSPECT_IDENTITY.md is a plan, not evidence of reduced recognition |

The analytical SQL tests use Python SQLite. They establish local constraint behavior, not hosted D1 latency, platform authentication, all runtime JSON invariants or data-source historical truth. Model/simulation validation is separate from software correctness.

## 2026-11-02 — pixel interface update
Fresh reruns:14/14 data tests,15/15 model checks,36/36 domain/scouting/QA tests. API integration script217 assertions passed, including two complete256-pick drafts and256 paired simulations per mode, persistence, group unlocks, authentication, ownership rejection, stale revisions, daily identity embargo, and authoritative leaderboard insertion. The harness invokes the actual route with SQLite and a platform-identity fixture; it does not establish Cloudflare dispatch behavior or full race/replay coverage. Browser preview returned ERR_CONNECTION_REFUSED despite daemon running. Browser interaction, iPhone/WebKit, visual regression and human recognition testing remain unverified. Reduced-motion CSS is implemented but not browser-verified.

## 2026-11-02 — empirical five-season and guided UI verification
This section supersedes the earlier preview-blocked status. Full integration:15 cases,302 actual route requests,zero failures,82.3 seconds on Node24.22.1 / Intel Xeon Platinum8573C. Three complete drafts and768 paired replicates exercised historical and two identical daily participants. Runtime hashes remained unchanged. Evidence:tests/results/api-integration.json.39 domain tests and15 data tests passed. TypeScript passed after guided UI changes.

Browser at terminal.local:4173: landing rendered; saved Cleveland draft resumed; scouting reduced budget12→11 and opened group forecast; review dialog selected a prospect; draft advanced to pick2 then jump-to-user reached pick4; trade desk opened with eligible assets; save action completed without visible error. Desktop screenshot inspected. This is not WebKit/iPhone certification, full browser end-to-end simulation, automated visual regression, or a novice usability study. The cloud browser has no viewport-emulation capability.

Largest integration response:1,837,229 bytes. Local timings do not establish hosted Worker/iPhone performance. Equal leaderboard scores currently receive ordinal positions ordered by completion time; this is not evidence of different decision quality.

Browser save/reload follow-up confirmed pick4,11scouting credits and8remaining Cleveland picks persisted. Guided layout duplicate field removed and compact stadium visually rechecked.

Production build completed successfully after final UI fixes. Inspected emitted Worker entrypoint/wrangler manifest and9 client chunks(841,240 bytes uncompressed). Spot-check found neither two known prospect names nor the private five-year donor artifact marker in client JS; this is a targeted leakage check, not a complete security audit.

Five-year forecast checks:7/7 passed; evidence analytics/five_year_test_results.txt and analytics/five_year_REPORT.md. Includes metric recomputation, original trajectory equality and label-availability checks.

## 2026-11-04 final frozen gauntlet
Run:tests/results/gauntlet/2026-11-04T20-10-00-917Z-frozen-nov4-4f1691a8/REPORT.md. Structural/execution PASSED; statistical NOT PASSED(exit2); no source drift.15data,5context,20warehouse,48domain,15model,7five-year and8statistical-integrity checks passed.15APIcases/304requests passed.96drafts,192pairedreplicates,32deterministicreplays,1,920seasons and503,808regular-season games reconciled. Four256-pair distribution ensembles and four128-pair score policies executed.

Remaining statistical failures are retained; do not represent this as full model validation. Cleveland scoring mean45.0457 versus observed46.2899; shutout rate0.0161 versus0.0103. Build passed and client artifact spot-check passed; browser/mobile verification blocked. New UI static rendering36cases andTypeScript passed.

## November 4 rollover and playoff audit
The rollover-playoff gauntlet under tests/results/gauntlet ran 18 steps with
zero input drift. All structural checks passed, including 304 real API
requests, 96 drafts, 192 paired replicates and 32 deterministic replays.
Added checks for wild-card seed pairings, divisional reseeding, conference
host order and title-game winners across 1,920 simulated seasons. Statistical
gates returned exit 2. Scoring bias, shutouts, QB coverage and ranking
sensitivity remain open. The 2018–2026 recorded draft audit passed, including
observed bracket progression in 2018–2025. Later classes are not playable.

Desktop Chrome opened a real Cleveland draft and unlocked a scouting report.
The local D1 schema was initialized before testing. Native iPhone Safari was
unavailable. Final field art and card border changes were applied after the
gauntlet and passed the final TypeScript and production build checks.

## Guided scouting review

The guided board recommends one unopened report, preferring a position absent
from the current draft class. The recommendation uses visible board state.
Desktop Chrome showed one recommendation in a Cleveland draft. TypeScript and
the production build passed. Native iPhone Safari remains unverified.

The source package includes the 2025 ownership reconstruction and the rolling
scoring audit. The recorded-data audit covers 2018–2026. Playable scenarios
remain restricted to 2018, and the statistical release criteria remain in
analytics/statistical_gates.json.

## November 12 follow-up remediation

Schedule tiebreak and tied-score audit defects corrected. Expanded 22-step gauntlet completed with structural PASS and zero drift; statistical gates remain 33 pass / 9 fail / 7 unsupported. Corrected official-score sensitivity reports 7 leader-set changes and minimum correlation 0.4. QB annual-transition research remains unpromoted. See [current release evidence](docs/release/CURRENT_RELEASE.md) and `tests/results/gauntlet/2026-11-12T23-12-46-869Z-schedule-ranking-remediation-a8233b9f`.
