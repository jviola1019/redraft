# Follow-up forecast studies

November 19, 2026, Chicago. Source gameplay matches published revision 25f8f5d. Each study defines its own comparison and acceptance rule. A separate reviewer checked saved measurements and regression tests. The formal release evaluator returned exit 2 with 40 passed, six failed, seven unsupported and zero stale checks. Each conclusion below is limited to the tested population and target.

| Study | Evidence | Decision |
|---|---|---|
| [Five-year QB snaps and games](../../analytics/qb_conditioned/REPORT.md) | Uses the deployed role probabilities and the same eligible evaluation QBs in both arms. On 44 linked players, snap CRPS fell from 967.44 to 891.16 and games CRPS from 15.65 to 15.02. Absolute error increased on both outcomes. Rookie-role probabilities averaged 20.9% versus 31.8% observed. Among 30 low-usage rookies both distribution scores worsened. | Freeze this candidate for independent confirmation. The cohorts were previously studied. Six 2021 quarterbacks in the earlier research sample did not satisfy this study's production eligibility and linkage rules. The 2018 cutoff supplies no additional mature donors. |
| [Possession-based scoring](../../analytics/scoring_possessions/REPORT.md) | Obtained 17 seasons of nflverse play-by-play. A total of 4,295 games passed reconciliation. Both the 768-game early and 512-game later assessment windows showed better shutout Brier, worse joint energy score and excess team-season scoring dispersion. | Reject this replacement. Further scoring work needs to represent how teams change pace and play when leading or trailing. Compare total score, shutouts and season dependence together. |
| [Playoff strength benchmark](../../analytics/playoff_benchmark/REPORT.md) | Prior-season margin produced Brier 0.23775 compared with simulator 0.24016. Finite-draw correction reversed the small overall difference. The benchmark led at horizon four after the horizon-level correction and in every raw one-season and adjacent two-season omission. | Eight observed seasons support a descriptive comparison. Reserve fresh outcomes before tuning to this finding. |
| [Daily score sensitivity](../../analytics/rubric_multiday/README.md) | Six isolated, route-generated daily setups across six teams, four classes and four strategies. All 24 official scores reconciled. Changing one weight at a time changed the first-place set in 12/60 comparisons, across five dates. Trade capital stayed constant. | Retain sensitivity disclosure. These tests establish the scoring contract and reveal ranking instability. Human decision quality and trade-heavy strategies require distinct evidence. |
| [Earlier participation sources](../../research/QB_SNAP_ARCHIVE.md) | PFR lists 2012 team snap coverage for all 32 franchises. Sampled original NFL gamebooks confirm exact counts in 2011 and 2012. The empty nflverse 2012 CSV therefore describes a provider-specific gap. | Use these as leads for a permissioned historical reconstruction. Coverage of every eligible QB, including nonparticipants, source conflicts, and terms of reuse still require resolution. |

## Results-screen correction

The old footer labeled the entire five-year span recorded history. The results view now labels each season from its saved evidence state, shows partial history as incomplete, and withholds ensemble means when a required team record is absent. A recorded zero-win season stays zero. The results headline describes simulated wins. Tests cover all four display states and matching by season and franchise. The real historical browser fixture uses Cleveland in 2025 and directly compares the five displayed labels with the server response. The local browser binary encountered a socket permission error. Consult GitHub Actions on the review branch for hosted browser status.

## Reproduce

Use the specific commands and acquisition steps in each linked study. Within each folder the protocol predates fitting. Frozen inputs and detailed results are committed. The large source play-by-play archives are retrieved separately. Use the Python requirements from the repository plus a parquet reader for the scoring study. Run the following from an installed checkout for the game and release checks.

```sh
node tests/run.mjs
pnpm exec tsc --noEmit
pnpm run build
python analytics/statistical_gates.py
```

[One-page decision brief](FORECAST_DECISIONS.pdf) · [Formal clearance criteria and remaining blockers](CLEARANCE_REVIEW.md)
