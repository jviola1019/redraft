# Statistical release gates

The research release is **blocked**. This is a statistical evidence decision, separate from software test success.

Counts: 33 pass; 9 fail; 7 unsupported; 0 stale.

The criteria are disclosed engineering tolerances chosen after earlier results were reviewed. They are not a preregistered hypothesis test. The 2018 outcomes are reused backtests.

| Gate | Status | Requirement |
|---|---|---|
| frozen_metrics_recompute | pass | Saved predictions reproduce metrics |
| strict_label_cutoff | pass | Every five-season donor label complete before draft cutoff |
| strict_independent_chronological_validation | unsupported | An independent pre2018 five-year chronological test |
| forecast_source_analytics/five_year_strict_2018.json | pass | Exact audit matches source artifact |
| forecast_source_analytics/five_year_frozen_2018_predictions.csv | pass | Exact audit matches source artifact |
| forecast_source_analytics/model.json | pass | Exact audit matches source artifact |
| conditional_support_DB | pass | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_DB_snaps | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_DB_games | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| conditional_support_DL | pass | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_DL_snaps | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_DL_games | fail | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| conditional_support_LB | pass | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_LB_snaps | fail | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_LB_games | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| conditional_support_OL | pass | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_OL_snaps | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_OL_games | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| conditional_support_QB | unsupported | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_QB_snaps | fail | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_QB_games | fail | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| conditional_support_RB | unsupported | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_RB_snaps | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_RB_games | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| conditional_support_TE | unsupported | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_TE_snaps | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_TE_games | fail | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| conditional_support_WR | pass | At least10 donors in each conditional stratum; minimum screening rule, not proof of validity |
| coverage95_WR_snaps | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| coverage95_WR_games | pass | Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes |
| specialist_quality | unsupported | Position-appropriate validated specialist quality target |
| forecast_distribution_skill | unsupported | Paired CRPS improvement confidence interval excludes zero on independent evidence; reused cohort only supports an audit |
| counterfactual_snaps_to_wins | unsupported | Validated effect mapping with sensitivity and identification limitations |
| simulation_fresh_CLE | pass | Diagnostic hashes match every current runtime dependency |
| simulation_replicates_CLE | pass | At least256 paired five-season replicates |
| simulation_precision_CLE | pass | Win-difference MCSE≤.25 wins and improvement-probability MCSE≤.032 |
| simulation_distribution_CLE | fail | Observed2018–22 summary inside conditional simulated2.5–97.5% range; diagnostic, not calibrated model-uncertainty interval |
| simulation_fresh_KC | pass | Diagnostic hashes match every current runtime dependency |
| simulation_replicates_KC | pass | At least256 paired five-season replicates |
| simulation_precision_KC | pass | Win-difference MCSE≤.25 wins and improvement-probability MCSE≤.032 |
| simulation_distribution_KC | fail | Observed2018–22 summary inside conditional simulated2.5–97.5% range; diagnostic, not calibrated model-uncertainty interval |
| simulation_fresh_NE | pass | Diagnostic hashes match every current runtime dependency |
| simulation_replicates_NE | pass | At least256 paired five-season replicates |
| simulation_precision_NE | pass | Win-difference MCSE≤.25 wins and improvement-probability MCSE≤.032 |
| simulation_distribution_NE | fail | Observed2018–22 summary inside conditional simulated2.5–97.5% range; diagnostic, not calibrated model-uncertainty interval |
| simulation_fresh_SF | pass | Diagnostic hashes match every current runtime dependency |
| simulation_replicates_SF | pass | At least256 paired five-season replicates |
| simulation_precision_SF | pass | Win-difference MCSE≤.25 wins and improvement-probability MCSE≤.032 |
| simulation_distribution_SF | fail | Observed2018–22 summary inside conditional simulated2.5–97.5% range; diagnostic, not calibrated model-uncertainty interval |

Full measurements, subgroup uncertainty, source hashes and fixed seeds are in `statistical_gates.json` and `forecast_audit.json`.

Run `python analytics/forecast_audit.py` then `python analytics/statistical_gates.py`. Exit2 means the audit completed and retained adverse or unsupported evidence. Exit1 means execution failed. `--report-only` never changes the report status.
