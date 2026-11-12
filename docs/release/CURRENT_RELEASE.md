# Current release evidence — November 12, 2026

**Research alpha. Full release criteria remain unmet.** This report supersedes prior current-status summaries; prior evidence remains in Git and dated audit directories.

## Corrections

- Fixed future same-place schedule opponents to use prior simulated division tiebreaks, including head-to-head outcomes. A regression failed before the fix and passed after it. Recorded initial schedules remain unchanged. Missing prior game records retain an explicitly disclosed point-differential fallback.
- Corrected sensitivity analysis to use rounded official scores, shared ranks, tied-rank Spearman correlation and complete tied-leader sets. Undefined correlations and duplicate identities are handled explicitly. Scoring weights and acceptance thresholds are unchanged.
- Expanded the single frozen gauntlet to include all registered draft classes, recorded playoff backtests and all-class distribution diagnostics. Adverse findings propagate into its final disposition.

Runtime source: `c0ae3640a03c941315d9ab17d0d1c1896e48ddc5` (local equivalent `ea235b1`), engine `0.8-schedule-tiebreaks`.

## Executed evidence

| Check | Result | Scope |
|---|---|---|
| Expanded frozen gauntlet | 22 steps completed; structural PASS; zero drift; exit 2 | Statistical failure retained |
| Domain | 77 passed | Includes demonstrated schedule regression |
| Rank calculations | 9 passed | Integer scores, ties, constant ranks and identity rejection |
| QB transition research | 6 passed | Data, cutoff, metric and sampling checks; no gameplay promotion |
| All classes 2018–2026 | 864 drafts, 1728 paired replicates, 288 replays PASS | Structural consistency, not calibration; default-class audit also runs separately |
| Recorded playoff backtest | Eight completed seasons 2018–2025 PASS | Qualification/matchups/reseeding, not predictive probability accuracy |
| All-year distributions | All nine classes evaluated; adverse findings retained | Incomplete/future actuals remain null |
| TypeScript and API | Passed | Current authoritative API and persistence tests |
| Hosted build/browser follow-up | Pending run 43327098570 | Prior browser smoke tests passed; physical device and full UI journey remain unverified |

## Statistical disposition

**33 passed, 9 failed, 7 unsupported, 0 stale.** The corrected official-score sensitivity analysis finds 7 leader-set changes and minimum tied-rank correlation 0.4. Raw exploratory ranks retain 2 changes. These are different ranking definitions, not directly comparable improvement statistics. Model misspecification and heuristic weights remain unresolved.

QB tail support, subgroup interval coverage, scoring/shutout distributions, specialist targets and causal snaps-to-wins effects remain inadequate. Complete draft-day rosters, verified schemes, individual future personnel/draft/contract policies and full historical rules remain incomplete. Later classes still use frozen pre-2018 role estimates; reproduction does not prove their calibration.

The new pre-cutoff QB annual-transition candidate improves annual CRPS versus an unconditional transition baseline (147.67 to 78.10 in 121 assessed player-year cases). Its exposed five-year 2018 check covers 15/16 QB totals but uses wider intervals and worsens MAE. Annual accuracy does not establish five-year validity; the candidate is **not adopted**. The existing shutout experiment also omits the current scoring-mean override, so it is a research approximation rather than exact runtime replay.

## Evidence

- [Expanded gauntlet](../../tests/results/gauntlet/2026-11-12T23-12-46-869Z-schedule-ranking-remediation-a8233b9f/REPORT.md)
- [All-class matrix](../../tests/results/gauntlet/2026-11-12T23-12-46-869Z-schedule-ranking-remediation-a8233b9f/all-years/summary.json)
- [Statistical gates](../../analytics/STATISTICAL_GATES.md)
- [QB research and limitations](../../analytics/qb_transition_experiment_REPORT.md)
- [Installation](../../INSTALL.md)

Repository source delivery does not update the separate live Site. Public deployment, physical-iPhone checks, approved visual regression, full browser journeys and complete production security/operations remain open.
