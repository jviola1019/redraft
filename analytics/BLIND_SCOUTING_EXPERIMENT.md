# Blind scouting: information-loss experiment

Executed 2026-11-02. This tests candidate coarsening of measurements and displayed probabilities. It does not establish anonymity, equal human decision quality or optimal band widths. Root's separate uniqueness analysis measures how easily fields identify a prospect within the installed pool.

Training 2013–2014, tuning 2015, test 2016–2017 (613 identifiable combine participants). Raw and coarse logistic hyperparameters are independently selected using only 2015 Brier loss. Missing values stay missing. Fixed candidate widths: height 3in, weight 15lb, forty 0.2s, bench 5 repetitions, vertical 5in, broad jump 10in, cone/shuttle 0.2s. Measurements map to the nearest fixed-width center. Probability-display compression is evaluated at midpoints of 10-percentage-point bands; this does not require changing hidden runtime probabilities.

| Variant | Brier↓ | Log loss↓ | ROC-AUC↑ |
|---|---:|---:|---:|
| raw_measurement_logistic | 0.22312 | 0.63743 | 0.6263 |
| coarse_measurement_logistic | 0.22576 | 0.64243 | 0.6095 |
| raw_with_10point_display_midpoint | 0.22563 | 0.64307 | 0.6124 |
| coarse_with_10point_display_midpoint | 0.22439 | 0.63897 | 0.6135 |

| Difference against raw logistic | Brier difference | Paired within-cohort bootstrap 95% interval |
|---|---:|---:|
| coarse_measurement_logistic | +0.00264 | [-0.00053, +0.00606] |
| raw_with_10point_display_midpoint | +0.00251 | [+0.00048, +0.00454] |
| coarse_with_10point_display_midpoint | +0.00127 | [-0.00252, +0.00519] |

Intervals use 1000 resamples within each test cohort, seed 20180426. This estimates conditional sampling uncertainty within two cohorts, not future-era uncertainty. The coarse model's small point-estimate deterioration and interval containing zero do not prove equivalence; no equivalence margin was prespecified. The probability-band results also show that apparently minor display compression can change proper scoring metrics.

College is not a model predictor, so this experiment cannot establish whether college labels help human scouting. Verified pre-draft college production is unavailable; its predictive and recognition trade-offs cannot be tested here. Keep proposed production fields marked unavailable until real data is obtained. Do not fabricate statistics, change real athletic attributes, or claim removing names prevents recognition.

Practical inference: coarse descriptors are a plausible candidate for a recognition-resistant daily interface, provided uniqueness/linkage tests and actual user testing support them. This is an inference, not an empirically established optimum. Standard historical play may preserve exact source-backed information if it is explicitly name-hidden rather than anonymous. The two display policies can share the same two game modes and engine.

Relevant foundations: [NIST SP 800-188](https://csrc.nist.gov/pubs/sp/800/188/final) recommends measuring re-identification risk when transforming quasi-identifiers; it does not certify this football interface. [Combine performance research](https://pubmed.ncbi.nlm.nih.gov/32459737/) motivates skepticism about physical measurements as a complete talent signal. See `research/MODELING_RESEARCH.md` for evidence and limitations.

## Shared-profile pooling selected for further testing

The runtime policy now groups candidates within broad position, sorts frozen model probabilities, chunks five and merges a short final tail. It shares the arithmetic mean probability and the same measurement ranges. Runtime model version adds `+blind-g5-v1`; CPU choices, scoring and simulation use the pooled probabilities too. This removes individual fine-resolution probabilities from CPU decisions. The UI still shows a ten-point band while CPU/scoring use the exact pooled mean, so their numerical precision is not identical. All human participants receive the same profile policy. The raw trained artifact remains separately available for reproducibility.

The independent held-out utility test groups all 635 nonspecialist combine participants within each of 2016 and 2017 before joining outcomes. Only 613 have identified labels; 22 unlabeled candidates affect the groups but do not become invented zero outcomes. Every group has at least 5 candidates. Canonical ID order breaks exact probability ties; no outcome label is used.

| Held-out variant | Brier | Log loss | ROC-AUC |
|---|---:|---:|---:|
| raw | 0.223124 | 0.637433 | 0.62635 |
| pooledMean | 0.222904 | 0.637529 | 0.62916 |
| pooledTenPointDisplayMidpoint | 0.222892 | 0.637866 | 0.62665 |

Pooled-minus-raw Brier difference=-0.000221; paired within-cohort bootstrap95% interval [-0.002285, +0.001675]. This small point-estimate difference is compatible with modest benefit or harm. It does not prove equivalence, equal human scouting quality, or anonymity. Utility is measured for rookie participation only. See `analytics/pooling_validation.json` and `analytics/outcomes/pooling_test_predictions.csv`.

The earlier fixed measurement bands alone did not establish sufficient ambiguity; root's separate within-pool uniqueness audit should be consulted. Shared profiles protect against exact matching of the released profile within the initial pool, subject to the measured group-size condition. They cannot guarantee protection against elimination, auxiliary knowledge, collusion or recognition after repeated play. College and exact individual measurements remain hidden during blind scouting; underlying historical facts are never falsified.
