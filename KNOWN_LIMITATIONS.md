# Known limitations and release acceptance

## Current verified checkpoint

The recovered 2018–2026 research-alpha implementation was freshly tested. Structural checks passed; statistical release remains blocked (33 pass, 9 fail, 7 unsupported). See [current evidence](docs/release/CURRENT_RELEASE.md) for the authoritative scope and links. Older dated entries below are historical records.

## Current coverage — November 12, 2026

The application now enables **2018–2026** as research-alpha scenarios. Later sections retain dated historical findings; older 2018-only coverage descriptions are superseded. All years remain unsupported as a full release. Source limitations differ by year: see `data/processed/scenario-coverage.json` and `research/SCENARIO_LIMITATIONS.md`. Eligibility does not include every draft-eligible player; 2021 includes 323 verified invitees, 144 with all measurement fields unavailable. Exact-match identity reconciliation can leave the same person separately represented in the alternate eligible pool and actual baseline reference pool.

The full nine-year structural matrix passed 864 drafts / 1,728 paired replicates / 288 replays, with no input drift. This does not clear forecasting. QB upper-tail support, score-distribution mismatch and scoring-weight sensitivity remain unresolved. Verified draft-day rosters, historical schemes, named future personnel/rookies, contracts and awards are not fully implemented. Browser execution is blocked locally, but hosted Chromium/WebKit desktop and emulated-phone smoke tests passed. Physical iPhone behavior, the full browser gameplay journey and approved visual regression remain unverified. See [current release evidence](docs/release/CURRENT_RELEASE.md) for final test and security results.

**Research alpha. The complete requested production/scientific acceptance gate is not passed.** Fresh evidence is linked above; older dated results are historical records.

## Material gaps

- **Eligibility:** in 2018, 336 combine participants are playable; 39 additional historical draftees are baseline-only. This removes a known future-derived membership addition but omits other eligible prospects. Actual-baseline and playable pools differ, so comparisons are not attributable solely to user choice.
- **Historical publication:** modern archives and later-revised pages do not prove every original availability timestamp. Correct-looking order and measurement facts are weaker than immutable pre-draft snapshots.
- **Coverage:** complete college production, verified injury histories, exact April rosters, contracts/cap, coaching and contemporary scouting are not reconstructed. Missing facts remain unavailable.
- **Identity recognition:** names and IDs can be masked, but college, year, position, rare traits, missingness, cumulative scouting, probabilities and outside searches may identify players. No human recognition study has been executed; no anonymity or competitive-fairness guarantee is justified.
- **Player models:** rookie 200+snap probability is not five-year value, pure talent or starting probability. Unsupported specialists require unavailable outputs or explicitly internal game priors.
- **Five-year dynamics:** growth, injury-like availability, retention, opportunity, draft-to-team impact and future personnel behavior are assumptions. Named future rosters, cap decisions, subsequent draft intake and trades are not fully modeled.
- **League rules:** future opponent generation, week/home assignments, common bye,17th opponent rotation, full tiebreak chain, overtime and score distributions remain approximations. Internal consistency does not prove NFL fidelity.
- **Trade/CPU realism:** current-pick ownership/transactions work; future/conditional picks, historical roster-based policies and sophisticated acceptance calibration remain incomplete. Frequency matching alone does not validate trade behavior.
- **Awards:** draft-class star picks/MVP concern the modeled draft cohort. They are not a league-wide NFL MVP forecast. Later named transactions cannot be invented for narrative.
- **Uncertainty/scoring:**256 paired samples reduce Monte Carlo error but cannot correct misspecification. Conditional intervals omit full parameter/model uncertainty. Composite weights are product assumptions; exploratory sensitivity is not validated GM skill.
- **Engineering:** the normalized warehouse is a tested design, not a fully acquired/loaded production database. Public abuse/load/backup tests, physical-iPhone verification, full browser journeys and complete WCAG/visual-regression certification remain incomplete.

## Acceptance matrix — November 12, 2026

| Requirement | Verified status | Remaining gap |
|---|---|---|
| Real 2018–2026 draft classes | All nine source-backed scenario datasets enabled; data/context checks pass | Unequal playable/reference pools, missing fields and annual source limitations |
| Strict historical information set | Feature/outcome separation and cutoff tests pass | Complete eligible pools, publication timestamps, draft-day rosters/contracts/schemes |
| Seven-round draft and transactions | 864 all-team/year/seed drafts pass structural checks | Future/conditional picks and empirical CPU/trade calibration |
| Identity hiding | Server disclosure and client-artifact checks pass | Recognition study and anonymity guarantee unavailable |
| Trained models | Reproducible fitting/artifacts and metric tests pass | 9 failed and 7 unsupported statistical gates; later-class calibration unproven |
| Five-season simulation | 17,280 seasons pass league/replay invariants | Distribution fit, full player/roster dynamics and causal impact mapping |
| Actual/baseline/alternate | Paired comparisons and incomplete/future null actuals tested | Pool mismatch and conditional uncertainty limit interpretation |
| Daily leaderboard | Server scoring, immutable configuration, UTC rollover and disclosure tested in API suite | Composite validity, ranking sensitivity, public concurrency/abuse coverage |
| Save/resume | API, local HTTP and hosted browser roundtrips pass | Production recovery and cross-device account synchronization |
| Responsive frontend | Chromium/WebKit desktop and phone smoke tests pass | Physical device, full UI journey, novice study and approved visual baselines |
| Analytical ERDs/schema | 52-table design; 20 constraint checks pass | Not a fully acquired and populated production warehouse |
| Public production/security | Input/auth controls and point-in-time dependency audit implemented/tested | Hosted authorization, abuse/load, retention and restore audits |
| Source delivery | GitHub source, frozen install/build and local startup verified | Native live Site deployment is separate and unchanged |

See [current release evidence](docs/release/CURRENT_RELEASE.md) for source commits and reports. Disclosure does not make an unmet criterion complete.

## Empirical forecast / guided interface update (2026-11-02)
Five-year player participation now samples complete observed2013 trajectories, conditional on broad position and pooled rookie-role probability. Only one complete donor cohort was available before2018;2012 source is header-only. Donor variation is not full model uncertainty. Snaps-to-team-strength, inferred starts, future aggregate roster management and score weights remain assumptions.2018-only scenarios, incomplete depth charts/contracts/college production and noncombine playable coverage are unchanged. New rolling forecasts are retrospective evaluations of date-valid fits, not new gameplay information.

The simplified pixel UI has desktop browser interaction checks, not completed iPhone/WebKit, visual regression or novice usability validation. Equal leaderboard scores have completion-time ordinal ordering. Older model-version saves are review-only and existing daily configurations remain immutable until UTC rollover.

## 2026-11-04 audit status
Historical context now includes2017 contributors and prior coaches for32teams. It remains a reconstructed prior-season snapshot:2018draft-day membership, contracts, coaching continuity and verified scheme assignments are unavailable. CPU utility uses a capped±0.035 historical utilization adjustment; its coefficient is a design assumption, not an estimated causal effect. Full future roster evolution remains aggregate.

Exact donor-distribution audit retains QB/LB coverage failures and thin support. Statistical thresholds are diagnostic rules declared after earlier review, not preregistered. Reused2018 evaluations are not untouched tests. Pre2018-only scoring recalibration changes the mean environment; it does not solve score-distribution or causal-win identification problems.

Current browser verification blocked by preview/browser infrastructure and URL policy. Type checks/static rendering do not certify mobile/Safari behavior.
