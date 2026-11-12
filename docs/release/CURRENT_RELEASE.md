# Current release evidence — November 12, 2026

**Research alpha. Full release criteria remain unmet.** This report supersedes older current-status claims; historical reports remain retained.

Production source and scenario/model files were recovered from uploaded Git objects. The recovered tree was cloned and tested afresh. One missing test file was replaced, reviewed and executed; it is clearly marked as a replacement. Original unavailable report files were not fabricated. The immutable recovery manifest documents historical omissions; new checks below supply fresh evidence.

Tested implementation: `d170418d520f815805b07ae702e634f1d05547ab`; tree `7910d022c56382b531817011b1fbf7ad39279ad9` matches the local implementation tree. The gauntlet source hashes include the refreshed input metadata. Its recorded local checkpoint preceded that metadata-only commit; all recorded source hashes remained unchanged during the run.

| Check | Fresh result | Scope |
|---|---|---|
| Frozen gauntlet | Structural PASS; zero drift; exit 2 | Statistical failure retained |
| All classes 2018–2026 | 864 full drafts; 1728 paired replicates; 288 replays; all PASS | 32 teams × 3 fixed seeds per class |
| League invariants | 17,280 seasons; 4,663,296 regular games; 222,336 playoff games | Generated checks, not independent historical samples |
| Domain | 76 passed | Includes restored year contract tests |
| API | 16 cases; 445 requests; 0 failures | Auth, persistence, all classes, UTC rollover, disclosure and server scoring |
| Data / context / warehouse | 15 / 5 / 20 passed | Source snapshots and implemented constraints |
| Model / development / statistical integrity | 15 / 7 / 8 passed | Reproducibility and metric implementation |
| Playoff backtest | 2018–2025: eight completed seasons PASS | Qualification, first-round matchups and divisional reseeding/home teams |
| All-year distribution diagnostic | 9 classes × 128 paired replicates; no drift | 30 completed comparison cells; 15 incomplete/future cells retain null actuals |
| Install, typecheck, build | Passed on Linux / Node 24.22.1 | Other operating systems unverified |
| Local HTTP | Passed sign-in, API, scout and save/reload | Browser interaction not implied |
| Dependency audit | Zero known advisories | Point-in-time audit only |
| Hosted browsers | Chromium and WebKit: desktop + iPhone-sized viewport PASS | Scouting, dialog dismissal, save/reload, overflow and runtime errors; no physical-iPhone certification |

Hosted [workflow 43323677851](https://github.com/jviola1019/redraft/actions/runs/43323677851) passed all implementation steps on browser-test revision `091cf5f5acee31c39ace48b77b23962bde73f023`. Runtime/model source is unchanged from the implementation above. [Retained browser receipts](../../tests/results/hosted-browser/43323677851/receipt.json) preserve the job and downloaded-artifact digest. Chromium and WebKit each passed desktop and iPhone-sized viewport checks for scouting, dialog bounds/focus, keyboard dismissal, save/reload, completed entry animations, horizontal overflow and runtime errors.

Four [viewport captures were visually inspected](../../tests/results/hosted-browser/43323677851/review.json). Draft text is opaque after entry; dialog controls fit the phone viewport. The phone board requires scrolling, and transient scouting feedback overlays some lower content. This is a limited review, not an approved visual-regression baseline, physical-device test, novice usability study, complete accessibility audit or full seven-round browser journey. The first capture set had entry-timing/full-page artifacts; its original receipt and the local launch failure remain retained.

## Statistical disposition

33 gates passed; 9 failed; 7 unsupported; 0 stale. Rank-weight sensitivity changed the top policy in 2 settings; minimum rank correlation 0.8. No tolerance was relaxed and no failing seed was replaced.

QB upper-tail support, scoring/shutout distributions and decision-score sensitivity remain unresolved. The strict QB donor pool has 15 trajectories and only three rookie-role-positive donors. Four of sixteen observed holdout totals exceed its maximum. The official 2012 snap file remains header-only; documented loader coverage does not supply missing observations. Candidate QB and score-distribution experiments were retained rather than presented as proven fixes.

Exact draft-day rosters, historical schemes, complete future individual personnel/draft/contract policies, full tiebreak details, specialist quality and causal snaps-to-wins effects remain unsupported. Later classes use a frozen pre-2018 role predictor; model reproduction does not prove later-class calibration. Incomplete and future actual outcomes remain null.

## Evidence and reproduction

- [Frozen gauntlet](../../tests/results/gauntlet/2026-11-12T22-36-08-824Z-recovered-checkout-50ecaff6/REPORT.md)
- [All-class matrix](../../tests/results/recovered-year-matrix/summary.json)
- [All-year distributions](../../tests/results/all-year-distributions-2026-11-12.md)
- [API evidence](../../tests/results/api-integration.json)
- [Machine-readable release status](../../tests/results/RECOVERED_RELEASE.json)
- [Install instructions](../../INSTALL.md)

Repository: https://github.com/jviola1019/redraft . Source download is an installable web application, not a prebuilt native app. Repository delivery does not update the separate live Site.
