# Release blockers and dispositions

November 19, 2026 (Chicago). The numbered rows below account for the nine failed November 12 statistical checks. Severity refers to the requested release claims. The original thresholds and observed outcomes have been retained.

| Prior failed check | Mechanism and evidence | Disposition | Required verification |
|---|---|---|---|
| 1. Defensive line games | A 16-game donor season was transferred unchanged to 17-game seasons. Schedule-adjusted exposure raised coverage from 32/36 to 34/36. | Pass on reused 2018 cohort | Replicate on additional fully observed cohorts. |
| 2. Linebacker snaps | Same exposure defect. Coverage rose from 42/48 to 44/48. | Pass on reused cohort | Check coverage and width prospectively. |
| 3. Tight end games | Same exposure defect. Coverage rose from 13/16 to 15/16. | Pass on reused cohort | Check coverage and width prospectively. |
| 4. QB snaps | One fully mature pre-2018 combine donor class gives poor upper-tail support. | Failed | Improve five-year distributional score, coverage and interval width using earlier evidence. |
| 5. QB games | Conditional strata contain too few QB career paths. Existing opportunity model misses outcomes. | Failed | Independently evaluate role persistence and participation with more mature labels. |
| 6. Cleveland score distribution | Combined scoring too low and shutouts too frequent over the observed 2018–22 reference window. | Failed | Validate game- and season-level distributions at historical forecast origins. |
| 7. Kansas City distribution | Same paired league baseline produces the same aggregate discrepancy. | Failed | Same as Cleveland. |
| 8. New England distribution | Same paired league baseline. | Failed | Same as Cleveland. |
| 9. San Francisco distribution | Same paired league baseline. | Failed | Same as Cleveland. |

The four league checks describe one shared league baseline. Counting four failures does not make these four independent experiments. Four additional provenance checks validate source hashes. They carry no information about predictive skill.

## Further findings outside those nine gates

| Priority and subsystem | Evidence | Remediation and acceptance |
|---|---|---|
| High · CPU drafting | 108 complete drafts produced one round-one quarterback. A pre-2018 position prior improved round-one shares but worsened team allocation across all nine classes. | Test a team-conditional utility against both dimensions and retain seed diversity. See CPU_BEHAVIOR.md and cpu_candidate/REPORT.md. |
| High · identity | 53 same-name cross-pool groups require review. The two David Long records in 2019 demonstrate why name-only merges would corrupt data. | Require audited source IDs or dated corroboration for each candidate. See DATA_INTEGRITY.md. |
| High · personnel | Draft-day contracts, coaching schemes and full rosters remain unavailable. Subsequent personnel changes are represented only partially. | Verify dated snapshots, annual membership exclusivity, role opportunity and turnover before making player-specific claims. |
| High · Daily rankings | Seven changes to the set of leaders under alternative weights, minimum rank correlation 0.4 in the four-policy sensitivity experiment. | Validate across challenges, report uncertainty, and assess whether standings distinguish useful decisions. |
| High · historical inference | Eligibility covers selected pools. Some future schedule information is retrospectively reconstructed. | Audit availability separately from event dates and validate equivalent intervention and baseline populations. |
| High · production assurance | Edge identity, operational restore, field web vitals and physical iPhone behavior lack evidence. | Complete staging tests and restore exercise with operator access. |
| Medium · midnight | A response could cross midnight between two reads and disagree about which fields to reveal. | Fixed. See DAILY_BOUNDARY.md for exact-millisecond and reconnect tests. |
