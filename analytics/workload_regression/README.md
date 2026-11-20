# Veteran workload projection

The model estimates whether a prior-season offensive or defensive contributor reaches 500 regular-season primary-side snaps in the following season, anywhere in the NFL. For each season, primary-side snaps are the larger of total offensive and total defensive snaps across all teams. League-wide player identity is the Pro Football Reference ID. A player who appears in the prior season but records zero snaps or disappears from a fully covered following season is a below-threshold outcome. A missed target can reflect retirement, injury, unemployment, demotion, or other changes in opportunity. The model estimates realized playing time rather than ability or the cause of a change.

## Method

- Cohorts include players with a positive offensive or defensive snap count in the last completed regular season. Position and previous affiliation come from the player's final listed regular-season appearance. The latest team labels remain historical affiliations even when the player subsequently signs elsewhere, remains unsigned, or retires. This corpus cannot independently identify those statuses at each draft. Players listed exclusively for special teams without offensive or defensive snaps fall outside the cohort.
- Features include position, the last two seasons' primary-side snaps and listed games, log snap change, and the fraction of the prior season's primary-side snaps recorded over the last four listed appearances. The previous-season rather than the draft-year position is used. Zero prior-history snaps reflect no observed workload in the relevant complete source season. Age, draft-year outcomes, rookie data, depth chart, free agency, contracts, injuries and EA ratings are excluded. The local annual roster file covers 2017 only.
- Each 2018–2025 heldout draft has a separate expanding training cohort beginning in 2015 and ending at the preceding outcome season. Data from completed regular-season games are checked against the source schedule. The scenario cutoff date must be later than the final game feeding the features or fitted outcomes. Raw releases were retrieved retrospectively and lack original row publication times. Only seasons 2013–2025 enter the model. The 2012 release has no player observations.
- Benchmark probabilities use Jeffreys-smoothed training proportions by position or by the prior 500-snap indicator. The linear logistic benchmarks use a position one-hot and a standardized log of prior snaps, with the trajectory model adding the remainder of the features. The exploratory alternatives add a degree-two spline over prior snaps at 0, 30, 100, 300, 500, 700, 1,000 and 1,300 snaps. All logistic models use fixed L2 regularization with C=1 and train-only feature fitting. The curved variants were investigated after the linear diagnostics and share the same evaluation seasons.

## Results

| Model | Brier ↓ | Log loss ↓ | AUC ↑ | Calibration error ↓ |
| --- | ---: | ---: | ---: | ---: |
| Position historical rate | .211464 | .612095 | .601193 | .017718 |
| Prior 500-snap historical rate | .156132 | .485320 | .776137 | .009973 |
| Position and last snaps, linear logit | .146737 | .453414 | .846928 | .034692 |
| Position and trajectory, linear logit | .145816 | .451700 | .848938 | .037605 |
| Position and last snaps, spline logit | .142795 | .441172 | .850930 | .009708 |
| Position and trajectory, spline logit | .141737 | .438930 | .852490 | .011082 |

Metrics pool 15,444 player-seasons across eight heldouts. Calibration error is the weighted absolute rate gap using ten equal-width probability bins. The exploratory spline trajectory candidate improved Brier and log loss against the spline last-season-only model in all eight years. The pooled overall forecast averaged 32.06% with 31.99% observed. Within 5,545 heldout prior 500-snap contributors, it averaged 63.78% with 65.14% observed, Brier .209685 and log loss .608253. The strongest simple benchmark and trajectory candidate are close, and the trajectory model remains less calibrated by pooled bin error than the last-snaps spline. Repeated player identities, the 17-game schedule transition, and shared team and season effects limit inference from pooled metrics. This is exploratory evidence from exposed validation years. A prospective full-season holdout is needed before using the candidate as a decision rule. League-wide calibration cannot establish individual position or team calibration.

## Staging integration

`projections.json` carries version `veteran-nfl-workload-v1` and an evidence-status field. Its `drafts` cover 2018–2026 and each contains 32 previous-affiliation team groups. The 2026 projection uses outcomes through 2025 and is unevaluated here. Every group uses the most recent prior team attribution across all its eligible players. Differences between provider and scenario franchise codes are resolved for display and the original code remains recorded.

- `priorHighUsage` counts contributors with 500 or more primary-side snaps in the previous regular season whose final appearance was for that team. `expectedHighUsageAnywhere` sums their forecast probabilities for again reaching 500 snaps anywhere in the NFL.
- `positions` provides a broader last-observed-position breakdown in the order declared by `positionValueOrder`. It includes players with lower prior snap totals alongside prior high-usage contributors. Missing positions mean no observed contributors in the cohort for that team and position. Estimates for rare position or team cells are descriptive.
- A sum of probabilities is an expected contributor count. For the 2025 Cleveland group, the model projects 12.6 of 21 prior high-usage players to reach the threshold across the league. The group may include players who have departed or are unsigned. Display it as prior-season workload context, distinct from separately verified draft-day personnel facts. Avoid interpreting the sum as expected roster retention, replacement needs, or a CPU draft score.

## Reproduce

Run `python analytics/workload_regression/train.py` from the repository root using `analytics/requirements.txt`. Then run `python -m unittest discover -s analytics/workload_regression`. The pipeline reads existing local snapshots and exports aggregate JSON with no player names, scores, or proprietary ratings. Raw data are identified by SHA-256 in `results.json` and the repository source manifest. Attribution and input definitions are documented in the project registry.

[NFLverse snap count documentation](https://nflreadr.nflverse.com/reference/load_snap_counts.html) · [Project source registry](../../research/SOURCE_REGISTRY.md) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
