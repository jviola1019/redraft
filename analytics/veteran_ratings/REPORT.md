# Madden overall ratings and veteran participation

Madden overall ratings improved forecasts of which already-active NFL veterans would play at least 500 offensive or defensive snaps the next regular season. The strongest available evaluation uses the 2024 draft cutoff. The Feb. 15, 2024 rating snapshot was uploaded to GitHub on Feb. 16, ahead of the Apr. 25 draft. The model was fitted on 3,417 observations from the 2022 and 2023 cohorts. This is evidence for a veteran playing-time prior in the matched population. Release needs additional pre-draft-published cohorts and authorization for production use of the data.

| Draft cutoff | Evaluation | N | Brier baseline → OVR | Brier difference (95% interval) | Log loss baseline → OVR | Log loss difference (95% interval) | AUC baseline → OVR |
|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | Primary | 1,689 | .16547 → .15271 | −.01276 [−.01777, −.00787] | .50638 → .46810 | −.03828 [−.05276, −.02430] | .81902 → .84368 |
| 2023 | Retrospective archive sensitivity | 1,685 | .15888 → .14333 | −.01555 [−.01996, −.01127] | .49311 → .44782 | −.04529 [−.05810, −.03246] | .83355 → .86071 |

The 2024 cohort covered 87.5% of 1,931 eligible veteran players and included 611 who reached 500 snaps. Of the eligible players, 224 had no normalized-name match, 16 had ambiguous snap identities and 2 had ambiguous archive matches. Exact normalized names can still link the wrong person or miss a player whose name changed. The 2024 archive had 1,992 rows, consistent with a snapshot restricted to a subset of NFL personnel. The sample omits veterans with zero offense and defense snaps in the prior season and special-teams-only players, including kickers. Changing teams, getting injured, retiring and competing for playing time all affect the outcome. The baseline uses prior position, snap volume and games played, so the gain is incremental to those inputs. A stronger baseline with pre-draft transactions, age, injuries, depth charts and contracts could absorb some of the gain.

The QB subgroup had 81 observations in 2024 and 27 positive outcomes. The pooled model's Brier improved from .15693 to .10788 in that subgroup. This is descriptive evidence on veteran QB playing time. The study provides no validation for incoming QB forecasts, rookie evaluation, need weights, win forecasts or score forecasts. The intervals resample players within each holdout year. They do not quantify year-to-year variation.

## Source eligibility

| Source | Observed access and timing | Research status |
|---|---|---|
| EA Madden NFL ratings | The official public webpage returned HTTP 200 and displayed Madden NFL 27 week-specific ratings. EA's July 31, 2026 reveal says the ratings were published during training camp, after the 2026 draft. | Public lookup with verifiable edition and release context. A production bulk API and historical version guarantees were not verified. |
| Historical EA JSON endpoint | A community GitHub file lists `ratings-api.ea.com/v2/entities/madden-nfl-21`. Single HEAD checks on the 21 route and a corresponding 27 route both returned HTTP 500 from this environment. | Legacy route reported by a third party. A failed HEAD probe does not establish what methods are supported or whether the route is available elsewhere. |
| nflscraPy MaddenRatings GitHub release | All three CSV assets downloaded successfully. Their labelled Super Bowl snapshots were 2022-02-15, 2023-02-15 and 2024-02-15. GitHub first hosted the 2021 and 2022 assets on 2023-05-07. It first hosted the 2023 asset on 2024-02-16. | Best available archive for the study. The 2023 hindcast uses a dated snapshot whose GitHub upload occurred after the draft, and remains a retrospective sensitivity. The MIT repository license refers to the software and associated documentation. Separate upstream authorization for EA data redistribution was not verified. |
| theedgepredictor/nfl-madden-data | GitHub tree API returned HTTP 200 with edition-indexed CSVs and Parquet. README attributes data to MaddenRatings on Weebly and describes soft imputation in processing. GitHub repository metadata did not identify a license. | No verified snapshot-level publication provenance from the inspected documentation. This archive was not used. |
| nflverse/PFR snap counts | Already available in REDRAFT's tracked source setup for 2020–2024. The nflreadr documentation identifies these as game-level Pro Football Reference snap counts. | Baseline and outcome data. Filtered to regular season. |

Sources

- [EA ratings database](https://www.ea.com/games/madden-nfl/ratings), [EA Madden 27 ratings reveal](https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-27-ratings-overview), [EA user agreement](https://www.ea.com/legal/user-agreement)
- [Community reference to the legacy EA endpoint](https://github.com/BAD-AL/MaddenConverter/blob/master/MaddenJSONData2021/index.html)
- [nflscraPy archive](https://github.com/blnkpagelabs/nflscraPy/releases/tag/MaddenRatings), [GitHub asset timestamps](https://api.github.com/repos/blnkpagelabs/nflscraPy/releases/tags/MaddenRatings), [nflscraPy repository license](https://github.com/blnkpagelabs/nflscraPy/blob/main/LICENSE)
- [Other archive documentation](https://github.com/theedgepredictor/nfl-madden-data), [official NFL draft dates](https://static.www.nfl.com/league/apps/league-site/media-guides/2024/2024-Record-and-Fact-Book.pdf), [nflverse/PFR snap-count documentation](https://nflreadr.nflverse.com/reference/load_snap_counts.html)

## Reproduction

Place the three public GitHub release attachments outside the project as `2021.csv`, `2022.csv` and `2023.csv`. The evaluator verifies the full SHA-256 of each input before reading the specified snapshot. From the project root and with the dependencies pinned in `analytics/requirements.txt` available, run:

```bash
sha256sum -c analytics/veteran_ratings/protocol.sha256
python analytics/veteran_ratings/evaluate.py --ratings-dir /path/to/ratings
python -m unittest discover -s analytics/veteran_ratings -v
```

The result file contains aggregate metrics and hashes. The experiment uses name matching, regular-season NFL participation in both preceding years as features, and no post-draft rookie Madden features.
