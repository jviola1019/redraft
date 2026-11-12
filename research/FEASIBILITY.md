# Historical data feasibility report

As of November 2, 2026, the data supports a **2018 research-alpha scenario**, not the complete release promised in the master specification. Earlier workspace contents were lost; the files and results below were downloaded and rerun in the current session. The actual execution date, not the requested October reference date, controls present-day comparisons. The entire 2018–2022 window is in recorded history.

## Evidence supporting the narrow scope

The clean scenario contains all 32 historical franchises, 256 slots over seven rounds, 32 compensatory picks, 336 independently verified playable combine participants, and 39 reference-only actual draftees. The seven rounds have 32, 32, 36, 37, 37, 44, and 38 selections. Actual selecting teams are stored separately from pre-draft owners. Reversing draft-day transactions reproduces all 256 official initial owners, after two documented source corrections. Oakland's eleven initial slots additionally match its April 20 official release.

The official Saints/NFL combine invitee list, published before the draft, resolves uniquely to all 336 combine rows. Exact school-aware aliases are audited; no fuzzy match is silently accepted. Two Jordan Thomas prospects remain separate (Oklahoma CB and Mississippi State TE). The 2018 Darius Leonard identity is preserved rather than replacing his historical name with a later preferred name. PFR identifiers resolve 212 actual draftees directly, three more by exact normalized name and college, and two through explicit aliases. The other 39 actual selections are non-combine reference entries.

The season reference contains 1,639 completed games for 2017–2022. Regular-season counts are 256 through 2020, 272 in 2021, and 271 completed games in 2022. The cancelled Buffalo–Cincinnati game is excluded from completed outcomes. Team wins, losses, ties, and points for the 2017 context are derived from games, not independent synthetic records.

## Empirical year coverage

The full machine-readable comparison is `data/clean/coverage_matrix.json`. Counts below were recomputed from the fetched releases.

| Draft year | Combine rows | Actual draft selections | Missing forty times | Initial ownership reconstructed | Full release quality |
| --- | ---: | ---: | ---: | --- | --- |
| 2013 | 332 | 254 | 0 | No | No |
| 2014 | 333 | 256 | 7 | No | No |
| 2015 | 322 | 256 | 1 | No | No |
| 2016 | 332 | 253 | 1 | No | No |
| 2017 | 327 | 253 | 57 | No | No |
| 2018 | 336 | 256 | 66 | Yes, independently reconciled | No |
| 2019 | 336 | 254 | 75 | No | No |
| 2020 | 337 | 255 | 70 | No | No |
| 2021 | 464 | 259 | 68 | No | No |

A row called “combine” is a provider classification, not proof that every year represents the same in-person measurement process. The exceptional 2021 cohort is not silently treated as equivalent. Counts establish availability, not measurement comparability or model accuracy.

In 2018 the playable measurements are complete for height and weight. Missing counts are forty 66, bench 93, vertical 79, broad jump 83, cone 152, and shuttle 140. Reasons are generally unknown. The diagnostics identify 24 robust outlier flags and zero broad physical-domain failures; all observations are retained. Rare values are not errors merely because they are unusual.

## Historical cutoff

The scenario cutoff is 2018-04-26T23:59:00Z, immediately before the first round at 8 p.m. Eastern. Feature inputs contain college, position, and combine measurements; future selection slot, eventual franchise, current career aggregates, awards, and later injuries are excluded. Actual selections and games occupy separate reference fields and must be stripped from pre-draft API responses. A canonical ID derived from public name/college can be dictionary-matched, so the API must issue unrelated per-run browser IDs.

Combine measurement availability is reconstructed as no later than after the March combine for game purposes; original per-value publication timestamps have not been recovered. Official pages now report 2023 revisions. Therefore the project does not meet a strict immutable, historically published feature-store standard. Later transaction evidence reconstructs past ownership facts, but does not become scouting ability information or knowledge available to CPU agents.

## College masking evidence

Within the 336 playable prospects, college + position produces 299 groups and uniquely identifies 265 people (78.9%). Every such group has fewer than five members. Position alone has one singleton; exact position + height + weight uniquely identifies 285 people (84.8%), and position plus all eight measurements uniquely identifies 334 (99.4%). Hiding only names or only colleges therefore provides weak protection from recognition.

Truthful coarsening reduces uniqueness: position with three-inch height bins and twenty-pound weight bins has 31 singleton prospects (9.2%); adding a 0.2-second forty bin raises this to 95 (28.3%). These are descriptive equivalence classes, not a privacy guarantee or a measured human recognition rate. The full calculations and bin conventions are in `data/clean/identity_risk_2018.json`. Model utility under coarsening is a separate experiment owned by the modeling workstream.

## Unmet data gates

1. Full 2018 eligible population, including non-combine undrafted players, is unavailable. The playable pool is deliberately limited to verified combine participants. The baseline includes 39 actual non-combine draftees, producing a pool asymmetry that must be disclosed.
2. College production, age, competition strength, verified injury history, historical scouting reports, and complete contract/coaching context have not been ingested. Do not display invented values or pretend combine-only predictions measure all prospect quality.
3. The annual 2017 roster is not an April 2018 active roster. Full pre-draft roster, contracts, and granular positional needs remain unsupported. Team context from 2017 scores is much narrower.
4. Current combine and official-page snapshots lack strict original publication timestamps. Temporal model partitions prevent future labels in fitting, but cannot establish perfect historical publication reconstruction.
5. Snap observations now cover every completed regular-season game from 2013 through 2025; the 2012 file is empty. Five-season snap/appearance labels can be constructed, but only the 2013 combine cohort has a complete five-year label observable before the 2018 draft. Later observed outcomes belong in evaluation or later-origin training. These labels measure realized playing opportunity, not causal player value; see the separate modeling experiment registry for actual fitted-model performance.
6. Public source availability does not grant every commercial or redistribution right. nflverse release licenses and official factual extracts are documented; raw trade repository licensing remains unresolved and raw data is kept private.

Additional draft years should not be enabled merely because their combine and draft rows exist. Each needs its own initial ownership reconstruction, prospect eligibility audit, historical snapshot, and appropriate time-ordered model validation.

## Reproduction

Run from the repository root with Python 3. These data scripts use only the Python standard library:

```bash
python research/ingest.py
python research/clean.py
python research/trades.py
python research/reconcile_order.py
python research/verify_invitees.py
python research/identity_risk.py
python research/diagnostics.py
python research/test_data.py
```

The raw source cache is immutable by default. To acquire a changed source, deliberately retain/version the prior snapshot and review changes before regeneration. Fifteen data tests passed on November 2; see `data/clean/data-test-output.txt`. That result covers the specified data invariants, not the whole application's scientific, security, or production acceptance criteria.
