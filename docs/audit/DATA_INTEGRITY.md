# Data integrity and historical eligibility audit

Audit date: 2026-11-20. Scope: repository-local 2018–2026 scenarios, frozen model artifacts, training tables, CPU selection code and historical-reference separation. This is independent diagnostic code, not independent acquisition of the underlying NFL facts. No network verification or original archival publication reconstruction was performed.

**Verdict:** All nine classes are executable with explicitly restricted pools. The independent diagnostic found no declared cutoff violations, duplicate prospect IDs, broken baseline references, or CPU dependence on the tested retrospective fields. This does **not** establish a complete historically eligible population, archival point-in-time features, or validated five-year counterfactual outcomes.

## Reproduction and evidence

Run `node research/independent_integrity_audit.mjs` from the repository root. It writes `docs/audit/data_integrity_results.json` and exits nonzero on an integrity failure. The diagnostic uses `analytics/runtime_loader.mjs` only to load the authoritative registry and engine; all assertions and mutation checks are new. The checked-in JSON records runtime/scenario/model hashes. The final run completed with **zero failures, nine classes and 18 paired complete-draft comparisons** (36 complete drafts, two seeds per class). Runtime edits made elsewhere during this audit are outside this work's ownership; the recorded hashes identify the actual tested inputs.

Checks cover unique IDs and 32 franchises; contiguous overall slots; enough playable prospects to finish; valid historical references; playable metadata counts; declared availability at/before cutoff; suspicious retrospective fields; complete playable projection coverage; minimum five-candidate initial blind groups; training-season boundaries; and paired-history poisoning. For each seed, actual selections are reordered/reassigned, draft-year and later scores changed to 999–0, and invented draft-pick/round/career-value/rookie-snap fields injected into prospects. Selections **and CPU trades** remain identical. Every resulting draft fills all slots exclusively from the playable pool. This experiment is deliberately narrower than proving noninterference for all possible inputs or seeds; it does not refit the model or rebuild policy on poisoned source data.

The independent CSV checks find 1,519 unique feature/label identities from 2013–2017, exact one-to-one feature/label membership, target agreement with the 200-snap threshold and all declared label availability before the frozen April 2018 cutoff. These verify generated tables, not the correctness of every raw identity or snap observation. No training-feature row has an original archived publication timestamp.

## Class coverage

“Draftees playable” means the historical selections whose prospect IDs belong to the playable pool. Reference-only prospects are retrospectively identified non-pool draftees, excluded from user and CPU drafting. Missing cells cover the eight measurement fields; they are retained as missing, not zero. All classes have zero late/invalid **declared** playable availability dates.

| Class | Playable | Reference only | Slots | Draftees playable | All 8 measurements missing | Missing cells / possible cells |
|---|---:|---:|---:|---:|---:|---:|
| 2018 | 336 | 39 | 256 | 217 | 0 | 613 / 2,688 |
| 2019 | 336 | 35 | 254 | 219 | 0 | 554 / 2,688 |
| 2020 | 337 | 25 | 255 | 230 | 0 | 736 / 2,696 |
| 2021 | 323 | 83 | 259 | 176 | 144 | 1,429 / 2,584 |
| 2022 | 324 | 39 | 262 | 223 | 0 | 1,002 / 2,592 |
| 2023 | 319 | 42 | 259 | 217 | 0 | 954 / 2,552 |
| 2024 | 321 | 31 | 257 | 226 | 0 | 1,018 / 2,568 |
| 2025 | 329 | 19 | 257 | 238 | 0 | 1,141 / 2,632 |
| 2026 | 319 | 34 | 257 | 223 | 0 | 1,204 / 2,552 |

The denominator is possible measurement cells, including missing cells.

The 2021 scenario is an important exception to the combine-participant label: its pool is the complete stored 323-name official **invitee** roster, not attendance at a centralized combine. Of these, 182 have an exact name/school provider measurement-row match and 141 lack such a row; three joined rows also lack all eight measurements, explaining the independent total of 144. `eligibilitySource='combine-participant'` is therefore a gameplay discriminator, not a literal attendance guarantee in 2021. Source: `research/build_scenarios.py`, scenario metadata and `data/clean/additional_order_sources.json`.

2018 has a stored 336-of-336 official invitee/name-school reconciliation (`data/clean/eligibility_audit_2018.json`). The 2026 metadata records matching official/provider **counts** of 319 but explicitly no individual name/school join. Equality of counts is not proof of population identity. The other years' recorded combine pools are not complete eligible populations either.

## Feature and CPU information flow

- `analytics/train_models.py` whitelists eight combine measurements plus grouped position. Draft round, overall pick, drafted team, names and outcomes are excluded from model features. Final prospect fit uses 2013–2017; `analytics/project_scenarios.py` applies that frozen fit to subsequent classes with exact-ID 2018 prediction parity. The 2016–2017 test cohorts become final-fit rows, so the stored test score evaluates the earlier fitting procedure, not an untouched test of the final refit.
- `lib/server-data.ts` checks scenario-year/version/cutoff contracts and constructs per-class pooled profiles. Its team-strength initialization for later classes uses the completed preceding regular season. The 2018 positional-usage heuristic uses 2017; later classes explicitly disable it instead of reusing old roster context. None has complete draft-day roster, cap, scheme or injury reconstruction.
- `lib/engine.ts` restricts the draft board, selection and CPU pool to the eligibility discriminator and checks availability on selection. CPU utility uses pooled role probability, selections already made by that franchise, explicit position premiums, seeded style/noise and optional capped prior-usage adjustment. This is a disclosed strategy heuristic; it is not an estimate of actual historical GM behavior or verified roster need. Trade acceptance uses the same utility and pick-value assumptions.
- `lib/scouting.ts` groups playable candidates by broad position and frozen probability, releases shared measurement ranges and probability bands, with minimum initial group size five. Grouping is not a complete anonymity guarantee. Non-playable baseline prospects remain excluded during drafting.
- `app/api/game/route.ts` constructs public prospect views through a whitelist and releases historical selections only when identity is revealed. This audit inspected this boundary but did not run browser/API penetration tests.
- `lib/simulation.ts` uses actual selections for the historical baseline and scoring comparison. Because 19–83 actual draftees per class are unavailable to the player, “beats actual draft” comparisons do not share an equal candidate universe. Five-year development draws on one complete pre-cutoff 2013 donor cohort; available data cannot validate a causal player-to-wins conversion.

## Actionable findings and limits

| Priority | Finding | Consequence and recommended action |
|---|---|---|
| High | Feature dates are reconstructed, not archived originals. Later class measurements are commonly assigned the scenario cutoff itself. | Passing timestamp checks demonstrates internal consistency only. Retain research-alpha wording and obtain dated per-measurement/source snapshots before claiming strict historical information sets. |
| High | Simulation schedule look-ahead is explicitly present. `generateSchedule` uses a complete recorded starting-year schedule and infers future fixed division rotations from recorded fixtures; it does not consult a dated schedule-release manifest. | CPU score/history poisoning passes do not cover this fixture information. Label simulations as conditioned on later known fixtures, or gate fixtures by publication date and generate unknown fixtures from rules known at cutoff. Do not describe the entire simulation as having zero post-cutoff inputs. |
| High | Pool and actual-history universes differ in every class. | Keep retrospective draftees reference-only, expose counts, and avoid interpreting baseline score as a fair full-population GM skill test. Reconstruct complete eligible/undrafted populations before that claim. |
| Medium | 2021 invitee cohort is unusually sparse; 144/323 have no measurements, with projections subject to missing-feature fallback policy. | Explicitly display cohort quality and distinguish measured candidates from prior/fallback-driven projections after reveal; never equate invitee membership with measured combine participation. |
| Medium | 2026 individual invitee reconciliation is absent; count agreement alone is weak evidence. | Store deterministic name/school matches and unresolved cases with raw-page hashes. Preserve the present caveat until complete. |
| Medium | Order evidence quality varies. 2019 and 2021 rely on reversal of transactions rather than a complete strict archived primary-order snapshot; 2018 primary page was modified later. | Retain year-specific ownership warnings. Acquire dated primary snapshots. For 2020 the source table says April 15 but the press release is April 16, while scenario cutoff is April 15; publication availability is not proved by the table's “as of” date. |
| Medium | Complete draft-day team context exists for no class; 2018 offers audited prior-season use, later years mark context unavailable. | Continue to call CPU needs a selection-balance/position-preference heuristic. Add dated roster evidence before claiming roster-aware needs. |

## Outcomes and calendar coverage

Local raw games contain complete postseason records through the 2025 season, and 150 completed 2026 regular-season games through November 16; no completed 2026 postseason exists. Thus observed complete five-season windows exist for draft classes **2018–2021** only. Class 2022 has four complete seasons; 2023 three; 2024 two; 2025 one; 2026 zero. The remaining seasons are incomplete or future, not negative outcomes. All nine classes having playable JSON does not imply all nine have five-year ground truth. These counts were independently read from `data/raw/games.csv`; scenario-level per-season regular-game counts are recorded in the diagnostic JSON. The diagnostic does not independently validate full postseason bracket advancement, source licensing, every raw identity, archival source truth, or model calibration.

A [source-by-source identity review](identity_review/REVIEW.md) classifies the 53 same-name candidate groups. It records evidence for one alias and two distinct-person groups. The other 50 remain unverified.
