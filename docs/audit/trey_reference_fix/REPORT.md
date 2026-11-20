# Trey Lance reference identity correction

Implemented in an isolated worktree from `2c632fb`; no main-workspace or published deployment changes.

The 2021 historical selection at overall 3 now references the existing eligible Trey Lance record `p2021-4a3e07404f`. The duplicate reference-only record `p2021-ref-e9aacb6df1` is removed. This is the sole audited alias; other suggested matches remain unresolved. The 323 eligible records, all their scouting features, all other historical picks and reference records, 2021 teams/ownership/games, and every other draft-year dataset/model remain unchanged. Reference-only count drops from 83 to 82.

`research/reference_aliases.py` applies the exact reviewed PFR/GSIS/name/school/position/pick/franchise join at the postdraft-reference boundary of `research/build_scenarios.py`, after ordinary identity lookup and before creating a reference-only supplement. It requires the canonical eligible record to exist and rejects changed identity guards. It never broadens the school matching rule, creates eligible players, fills measurements or changes prediction values. The only source evidence admitted is the audited 49ers/NDSU case in `data/clean/audited_postdraft_reference_aliases.json`.

The corrected versions are `nflverse-2021-combine-pool-v2-trey-reference` and `redraft-2021-pre2018-logistic-C10-v2-trey-reference`. The 2021 model removes only the obsolete reference fallback and updates scenario provenance, counts and version strings; all remaining numerical projections are identical. A fresh frozen-fit `project_scenario` call produces exactly the checked-in model artifact. `data/clean/reference_identity_corrections_2021.json` pins old/new scenario and model hashes, alias provenance and unchanged-section hashes.

Existing API compatibility checks make prior 2021 saves review-only and reject mutations with HTTP409; a new 2021 run uses the new bundle. An existing daily challenge pinned to the retired 2021 bundle remains frozen until the next UTC challenge, as existing policy requires. No saved-run or leaderboard values are rewritten.

## Reconstruction diagnosis

A full rebuild from current raw files is deliberately **not** substituted for the old snapshot. Two original 2021 order/invitee webtext captures are absent. Current raw files also differ from source pins stored in the original scenario: the current games add 14 records (no existing game changes), and the current draft file has a newer whole-file hash. Full rebuilding would refresh source hashes and verification dates unrelated to this correction. Those facts/hashes are preserved instead.

`research/regenerate_trey_reference.py` therefore derives the exact correction from the immutable `2c632fb` scenario/model, guarded by the audited original scenario hash, reviewed raw-draft hash and existing canonical identity. This is a reproducible reference correction, not a claim that the complete old source capture was recovered. The builder itself also applies the alias correctly when original sources are available; its reference/prospect arrays are regression checked separately using retained missing-capture pins without inventing files.

## Reproduction and validation

With dependencies/raw inputs available and commit `2c632fb` in local history:

```bash
python research/regenerate_trey_reference.py
python research/regenerate_trey_reference.py --check
python -m unittest discover -s research -p test_reference_aliases.py -v
node tests/run.mjs
node tests/api.integration.mjs --quick
```

Validation completed:

- 89 TypeScript unit tests pass, including corrected slot3, complete normal 2021 production-registry entry, unique eligible picks, exact feature/numeric-projection preservation and unchanged other-year file hashes.
- Three Python reference-boundary tests pass, including rejection of changed school/pick/franchise/GSIS guards and absence of a canonical target; other years return no aliases.
- 14 real-route integration cases pass (262 requests, zero failures, stable source hashes). The all-year route matrix checks corrected2021 creation, old2021 review-only behavior and HTTP409 mutation rejection, then completes/reloads the new2021 draft and bounded simulation.
- TypeScript typecheck (`tsc --noEmit`) passes.
- Guarded regeneration `--check` passes; independent fresh model projection output exactly equals the corrected artifact.

Evidence logs and the API integration report are retained alongside this report. These checks do not claim browser coverage or a full recreation of the missing archival source material.
