# Team-conditional CPU choice experiment

**Decision: promote the candidate as a versioned gameplay heuristic.** It cleared all predeclared gates and improved first-round and whole-draft position shares while retaining most of the existing team-level fit. Rookie participation remains the forecasting target. The historical classes were already exposed, and franchise errors and persistent QB underselection remain material.

## Fixed test and candidate

The [fixture plan](FIXTURE_PLAN.md) specifies the frozen cohorts, seeds, thresholds and coefficients. The baseline fixture failed with one first-round QB in 108 legal drafts against its floor of nine. Each policy replayed the same 12 seeds for every class from 2018 through 2026. Immediately before each choice, the candidate's additive score combined the following terms.

- Half the existing rookie participation score and half its midrank percentile within the prospect's playable position group. Midranks include tied scores and use the full playable class as a fixed reference. Specialists retain their existing internal fallback score.
- An adjustment of 0.12 times the log ratio of the position's smoothed share in the current round to its smoothed overall share. This captures where the league historically spent round capital. All eligible prospects remain in competition for each selection.
- The existing positional balance from this franchise's draft selections, position premium, seeded franchise style and prospect noise. Available prior-use context remains additive for 2018. After 2018, team conditioning consists of the current simulated draft composition and seeded style. There is no verified roster-needs input for those classes.

The adjustment uses 1,272 archived 2013–2017 selections and only their season, round and position. One pseudocount per position per round keeps the adjustments finite. The fit excludes subsequent classes, player identity and career outcomes. A retrospective source archive alone cannot prove what its contents were on a historical date. Improved position timing or composition offers no evidence of better player value or counterfactual wins. In particular, a high within-position percentile can occur in a weak class at that position.

## Paired results

TV is total variation between positional shares. Lower TV is closer to the recorded position mix. The franchise diversity error is the mean across franchises of the absolute error between the recorded effective position count and its mean simulated value. Effective position count is exp(Shannon entropy).

| Year | First-round QB current / team / forced / actual | First-round TV current / team / forced | Franchise TV current / team / forced |
|---|---:|---:|---:|
| 2018 | 0.00 / 0.33 / 2.83 / 5 | .341 / .281 / .211 | .408 / .428 / .482 |
| 2019 | 0.00 / 0.67 / 2.83 / 3 | .424 / .393 / .258 | .396 / .405 / .478 |
| 2020 | 0.00 / 0.58 / 2.83 / 4 | .438 / .279 / .203 | .427 / .422 / .486 |
| 2021 | 0.00 / 0.25 / 2.83 / 5 | .396 / .344 / .201 | .364 / .387 / .465 |
| 2022 | 0.00 / 0.75 / 2.83 / 1 | .385 / .201 / .198 | .411 / .405 / .470 |
| 2023 | 0.08 / 1.58 / 2.83 / 3 | .538 / .347 / .220 | .393 / .393 / .460 |
| 2024 | 0.00 / 0.08 / 2.83 / 6 | .594 / .422 / .294 | .384 / .376 / .457 |
| 2025 | 0.00 / 0.67 / 2.83 / 2 | .552 / .341 / .208 | .396 / .394 / .473 |
| 2026 | 0.00 / 1.08 / 2.83 / 2 | .625 / .362 / .250 | .379 / .383 / .454 |

Production selected 1 first-round QB, the candidate 72 and the forced comparator 306 across 108 drafts each. The nine observed drafts selected 31, equivalent to 372 selections across twelve repeats. The candidate had one first-round QB across all twelve 2024 runs against six in that historical draft. Both exposure windows cleared the predeclared quantitative gates. In 2018–2021, mean franchise TV rose from .399 to .411 and franchise diversity error rose from .877 to .953 effective positions. In 2022–2026, franchise TV fell from .393 to .390 and diversity error moved from .865 to .867. Whole-draft TV improved in eight classes and worsened in 2021. The candidate beat the forced comparator on franchise TV in every class and lost on round-one TV every time.

The [results](results.json) record all seven rounds, class-level and exposure-window summaries, cutoff fit, input SHA-256 values and replay evidence. The three policies filled all slots with unique playable prospects in 324 drafts. Trade ledgers matched exactly for each of the 108 paired seeds. For each year's first seed, the candidate replayed identically after reversing and changing actual pick records, altering post-cutoff scores and injecting retrospective fields into prospects. Historical identity fragmentation, eligibility differences and actual trades limit the franchise comparisons. Fixed-seed comparisons describe the tested policies. No untouched historical holdout is available in this evaluation.

## Runtime and compatibility

New games use `redraft-research-0.10-team-cpu-prior`. Saved games with the immediately preceding engine version continue on their existing CPU policy when their scenario, scoring and scouting pins still match. A daily challenge already pinned to the preceding version can accept new starts on that same version until the UTC rollover. Other retired engine versions retain the existing compatibility checks. The [runtime verification](runtime-verification.json) compares the integrated engine against the research implementation and the legacy policy against the baseline. Both comparisons matched selection digests in all 108 drafts. Exact trade ledgers matched both policies. Type checking and all 89 domain tests passed. The route suite passed 17 cases over 462 requests, including a frozen legacy daily start and reload followed by an exact legacy advance.

## Reproduction

Use a disposable checkout at or based on 9157a87 with the archived raw files and installed dependencies. Run the unchanged audit first and evaluate the QB floor.

```bash
node research/cpu_behavior_audit.mjs --output /tmp/team-prior-baseline.json
node -e 'const a=require("/tmp/team-prior-baseline.json"); const qb=a.classes.flatMap(c=>c.runs).reduce((n,r)=>n+r.firstRoundQb,0); console.log({drafts:a.totalDrafts,qb}); if(qb<9) process.exitCode=1'
```

The failing floor is expected. Apply the archived patch to run all three policies.

```bash
git apply docs/audit/cpu_team_prior/candidate.patch
node research/cpu_behavior_audit.mjs --output /tmp/team-prior-current.json
node research/cpu_behavior_audit.mjs --team-candidate --output /tmp/team-prior-candidate.json
node research/cpu_behavior_audit.mjs --candidate --output /tmp/team-prior-forced.json
node docs/audit/cpu_team_prior/compare.mjs
```

The patch's policy identifier is `pre2018-team-choice-prior-v1`. After collecting the archived comparator files, use the integrated checkout and the same output directory to verify production reproducibility.

```bash
node research/cpu_behavior_audit.mjs --output /tmp/team-prior-runtime.json
node research/cpu_behavior_audit.mjs --legacy-engine --output /tmp/team-prior-legacy.json
node docs/audit/cpu_team_prior/verify-runtime.mjs
```
