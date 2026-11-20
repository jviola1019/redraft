# One cutoff-safe CPU positional-policy candidate

**Decision: do not adopt in production. Retain as research only.** One simple change improves leaguewide first-round position shares but worsens franchise allocation and reduces diversity in every evaluated class. No tuning or second candidate was attempted.

## Isolated implementation

Worktree: `/tmp/redraft-cpu-policy`, detached from commit `550375d`. Main workspace runtime is untouched. The candidate adds an opt-in `positionRoundPrior` branch to `cpuPick` in this worktree only. It samples one available position group using its empirical frequency in the current round of the **2013–2017** drafts, then ranks candidates within that group with the existing player utility. Sampling uses deterministic seeded Gumbel-max draws. Historical zero-frequency groups remain zero; if all available groups have zero prior weight, the unchanged unrestricted ranking is the fallback. Counts are renormalized over available positive-weight groups by the sampling rule.

The sole empirical input is 1,272 recorded 2013–2017 selections in `data/raw/draft_picks.csv`, using only season, round and position. Actual pick number, player identity, career outcomes and 2018–2026 selections do not fit the prior. All five observed drafts precede the earliest April 2018 cutoff. This is event-time safety, not proof of an original archived source snapshot. No model was retrained. The unchanged base probability remains the frozen pre-2018 rookie-participation model.

The candidate is intentionally a round-position propensity baseline, not a team-needs model. Sampling position before applying player utility makes the existing within-franchise positional-balance term constant within the chosen group. It therefore loses that term's ability to influence which position a team drafts. This is a structural tradeoff, not a newly discovered safe parameter setting.

## Bounded comparison

Current and candidate policies each completed 108 drafts: 12 identical fixed seeds per class, 2018–2026, with rotating designated user franchises and unchanged trade rules. Every draft filled all slots with unique playable candidates. The report separates early exposed classes 2018–2021 from later exposed classes 2022–2026. Every evaluation class had already been inspected in the prior audit; none is an untouched holdout, even though the fitted prior contains no evaluation-class selections.

TV is half the sum of absolute position-share differences; lower describes closer aggregate shares. Diversity is exp(Shannon entropy of each franchise's selected position shares); its closeness to the actual value is descriptive, not player value. All values below are between-seed means; raw per-run evidence, per-round counts and per-franchise distributions are in `current.json` and `candidate.json`.

| Class | Exposure | Round-one TV current → candidate | Mean first-round QBs current → candidate (actual) | Franchise diversity current → candidate (actual) | Franchise TV current → candidate |
|---|---|---:|---:|---:|---:|
| 2018 | Early | 0.341 → 0.211 | 0.00 → 2.83 (5) | 5.43 → 4.57 (5.17) | 0.408 → 0.482 |
| 2019 | Early | 0.424 → 0.258 | 0.00 → 2.83 (3) | 5.28 → 4.44 (5.21) | 0.396 → 0.478 |
| 2020 | Early | 0.438 → 0.203 | 0.00 → 2.83 (4) | 5.39 → 4.45 (4.90) | 0.427 → 0.486 |
| 2021 | Early | 0.396 → 0.201 | 0.00 → 2.83 (5) | 5.09 → 4.43 (5.15) | 0.364 → 0.465 |
| 2022 | Later | 0.385 → 0.198 | 0.00 → 2.83 (1) | 5.47 → 4.57 (5.07) | 0.411 → 0.470 |
| 2023 | Later | 0.538 → 0.220 | 0.08 → 2.83 (3) | 5.39 → 4.51 (5.31) | 0.393 → 0.460 |
| 2024 | Later | 0.594 → 0.294 | 0.00 → 2.83 (6) | 5.06 → 4.46 (5.07) | 0.384 → 0.457 |
| 2025 | Later | 0.552 → 0.208 | 0.00 → 2.83 (2) | 5.41 → 4.55 (5.31) | 0.396 → 0.473 |
| 2026 | Later | 0.625 → 0.250 | 0.00 → 2.83 (2) | 5.26 → 4.51 (5.31) | 0.379 → 0.454 |

Round-one positional TV improves in all nine classes. First-round QBs recover from nearly none to 2.83 per draft in this sample; that identical class mean reflects shared seeds and the same historical round prior, not a class-aware quarterback valuation. The candidate removes the most extreme OL concentration but still cannot reproduce unusually QB-heavy classes such as 2024. Leaguewide round shares improve partly by construction because position timing is supplied directly from historical selection frequencies.

The opposing result is decisive: franchise-level positional TV worsens in all nine classes, and mean effective diversity moves below the actual baseline in all nine. Whole-draft position TV also worsens in six of nine classes. Trade counts remain exactly unchanged for every paired seed, consistent with the current chart/arrival-based trading rule being separate from player choice. A better first-round histogram is insufficient evidence to replace the current policy.

## Reproduction and invariant evidence

Use a disposable checkout with the archived raw data and installed dependencies. The following commands apply the research-only candidate there.

```bash
git apply docs/audit/cpu_candidate/candidate.patch
node research/cpu_behavior_audit.mjs --output /tmp/cpu_current_paired.json
node research/cpu_behavior_audit.mjs --candidate --output /tmp/cpu_candidate_paired.json
node docs/audit/cpu_candidate/cpu_candidate_invariants.mjs
```

`cpu_candidate_invariants.mjs` compares all 108 current-policy selection digests against the prior committed production backtest, replays 18 candidate seeds and poisons actual picks, post-cutoff scores and injected retrospective prospect fields in 18 paired candidate drafts. Results are in `invariants.json`; source hashes and fit counts are recorded in the full outputs. The research patch is `docs/audit/cpu_candidate/candidate.patch`; it is not applied to main. No publication or deployment was performed.

The actual baselines retain the documented eligibility/identity-fragmentation caveats. The transaction source ends April 17, 2026, so the 2026 trade comparator remains unavailable. Twelve seeds quantify limited Monte Carlo variation only; there is no independent historical validation or causal player-to-wins evidence.

## Adoption rationale

Keep this candidate as an explanatory research baseline. It shows that the rookie-snap-probability ordering causes a leaguewide positional-timing problem that can be reduced with genuinely pre-cutoff information. It also shows why a forced marginal distribution is insufficient: team-level behavior degrades. A production successor needs a clear draft-value objective and team-conditional choice policy, reviewed semantic identity joins and evaluation on genuinely unexposed classes. That is additional research, not authorization to tune current runtime coefficients from these nine exposed classes.
