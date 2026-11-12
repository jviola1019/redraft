# Research log

## 2026-11-02 — restoration and fresh verification

The previous transient workspace had been cleared. All data claims in this checkpoint were rechecked from fresh downloads; old runs are not presented as current evidence. Source contents and digests are recorded in `data/clean/source_manifest.json`.

- Retrieved 19 raw sources: draft selections, combine measurements, schedules, 2017 roster, six snap releases, official draft order/invitees/trades, two trade corrections, Raiders pre-draft release, 2014 Johnson chart, and nflverse license declaration. Public downloads succeeded. The 2012 snap source is header-only and excluded.
- Rebuilt the 2018 scenario: 32 teams, 256 selections, 32 compensatory picks, 375 canonical prospects. Only the 336 combine participants are playable; 39 non-combine actual draftees are baseline/reference-only.
- Independently resolved every playable participant against the February 6 official Saints/NFL invitee list. All 336 match uniquely using exact IDs/names and audited, college-constrained aliases. This improves eligibility evidence beyond relying on retrospective draft membership.
- Reconstructed initial ownership by reversing all grouped draft-day asset transfers. Corrected omitted pick 255 in trade 1288 using independent Bucs and Bills reports and reversed the erroneous pick 154 direction in trade 1291 using the NFL tracker. All 256 slots now agree with the official pre-draft list; Oakland's eleven initial picks match the April 20 PDF.
- Extracted 224 original Johnson chart values from the 49ers' 2014 article. Retained decimals. Picks 225–256 have no quoted Johnson value; the separately labeled one-point gameplay tail is an assumption.
- Recomputed current-year-pick-only draft-day trade counts: 19, 19, 17, 16, 29 in 2013–2017 (mean 20). The 2018 holdout has 29. These are transaction counts, not changes in final selecting franchise, and exclude deals involving future picks or veteran players.
- Recomputed coverage for 2013–2021. Only 2018 has initial ownership reconstructed. No year satisfies every requested release-quality data gate. This remains a research alpha.
- Inspected missingness and position-specific distributions. Retained all 24 robust outlier flags; zero broad physical-domain failures. Unknown measurements remain null. The observed increase in missing combine tests across years is visible in the coverage report and needs consideration in modeling.
- Measured identity leakage on the 336-person playable cohort. College + position uniquely identifies 265 prospects (78.9%); exact position/body measurements identify 285 (84.8%). All eight measurements plus position identify 334 (99.4%). Coarse body bins reduce uniqueness but do not prove anonymity. Root's masking workstream received this evidence and the warning that deterministic name/college hash IDs remain dictionary-matchable.
- Rechecked nflverse licensing and CollegeFootballData terms. nflverse data releases except FTN are identified as CC BY 4.0, with attribution and upstream-rights qualifications. CFBD allows application/model use but restricts raw redistribution; no key was available, so no college production was invented or imported. Raw nfldata trade-repository licensing remains unverified; raw source stays private.
- Executed 14 data tests: all passed in 0.198 seconds. Results are in `data/clean/data-test-output.txt`. This does not establish the full product's acceptance criteria.

## Research decisions retained

Use historical observations as facts, derived team context as transformations, forecasts as estimates, and development/trade/schedule assumptions as assumptions. Never move later career statistics into pre-draft features. Keep actual selected prospects distinct from eligible playable membership. Do not mistake final pick owner for initial owner or model fit for causal proof.

The source registry, coverage matrix, feasibility report, and model reports are the handoff documents. Remaining work includes complete college/roster/contract snapshots, original availability timestamps, stronger five-year player models, expanded eligible populations, and dataset-specific commercial rights review where necessary. No background research process is claimed.

## 2026-11-02 — five-year label coverage extension

- Downloaded and hashed eight additional snap-count files, 2018–2025, for the five-year modeling workstream. Reproducible ingestion now covers 2012–2025 (27 source files total).
- Verified exact game-ID equality between snap records and completed regular-season schedules for every season 2013–2025. Regular-game counts for 2018–2025 are 256, 256, 256, 272, 271, 272, 272, and 272. The cancelled 2022 BUF–CIN game is not invented. Across these files there are no missing PFR IDs or duplicate game/player/team rows.
- The 2012 file remains header-only, with none of its 256 expected games observed, and must not supply zero-valued player labels.
- A strict 2018 five-year forecast can train only on the fully observed 2013 combine cohort under this source coverage. A simple train/test split by draft cohort does not automatically solve label-availability leakage when five-year windows overlap. Later snap files support frozen-model evaluation and rolling-origin tests; they must not inform strict 2018 fitting.
- Added an executable source-coverage test. The current data suite has 15 tests; the latest execution log is `data/clean/data-test-output.txt`. Completeness at the game level does not itself prove every player's identity resolution or causal interpretation.

## 2026-11-04 — recovered checkout and roster-context reconstruction

Recovered source commit 81c6e3e retained the prior data artifacts but not the raw cache or uncommitted context work. Re-downloaded the full raw corpus and reconstructed `team_context_2018.json` from fresh 2017 snaps, roster observations, and schedule coaching fields. Additional depth-chart and dictionary sources were inspected and hashed. No source-access failures occurred in this run.

The context covers 32 teams, 256 regular games, 512 team-game observations, and 2,080 team/player observations. All scrimmage snaps reconcile to source totals, and all positions are classified. There are 1,091 exact PFR roster joins, 901 unique normalized-name/team joins, and 88 unresolved observations retained as null. Source roster status never becomes an assertion of April 2018 membership.

Depth-chart `formation` only identifies Offense, Defense, or Special Teams. The current dictionary differs from the 2017 schema and the old file contains REG week 18 rows. Consequently no scheme or draft-day roster claim is derived from it. `draftDayRoster`, `draftDayCoaches`, `scheme`, and `rosterContinuity` remain null for every team.

The pipeline writes an exact artifact SHA-256 sidecar for runtime version pinning. Five new context tests passed in 0.134 seconds. Full-product regression is handled by the independent QA workstream; the older test logs are not treated as fresh Nov4 executions. Detailed evidence and reproduction commands are in `research/TEAM_CONTEXT.md`.
