# Model experiments — executed results

## November 12 additions

`analytics/project_scenarios.py` reconstructs the frozen pre-2018 1,519-row logistic fit and checks parity against 324 canonical 2018 predictions (zero mismatches at saved precision), then emits scenario-hashed artifacts for 2019–2026. This validates reproduction, not later-cohort calibration. Missing-all-measurements and unsupported source-position categories use explicitly marked position priors. H-back maps to TE for gameplay but is unseen by the frozen predictor; two-way positions are not a two-way development model.

New executed/rejected experiments: `analytics/qb_uncertainty_REPORT.md` and `analytics/score_distribution.md`. The 2018 strict QB pool has only 15 trajectories and three rookie-role positives; four of sixteen observed holdout QB totals exceed the donor maximum. A four-origin QB comparison favors a position-only baseline on pooled Brier/MAE/RMSE, but does not establish adequate tail support. The scoring hurdle candidate has mixed proper-score results on the reserved pre-2018 test; it was not silently adopted to improve an already-examined diagnostic. Full release remains blocked.

Rebuilt and rerun 2026-11-02 from freshly downloaded sources. Artifact `analytics/model.json`; seed 20180426; frozen feature/label cutoff 2018-04-26T00:00:00Z. Research alpha: the five-year modeling release gate has not passed.

## Rookie role target

Target: at least 200 regular-season offensive plus defensive snaps in the rookie season among identifiable combine participants, excluding specialists. This is not starter probability, talent, elite probability or five-year career value.

Training 2013–2014; tuning 2015; held-out 2016–2017. Final runtime fit 2013–2017, with labels complete before the 2018 draft. Final N=1519; unknown identities excluded=77. Zero snaps is assigned only for known identifiers absent from a source covering all 256 regular-season games. Unknown identifiers are not zero; their exclusion creates selection bias. Unique exact normalized-name repairs are audited in the artifact.

Height, weight and combine measurements plus position are the only predictors. Names, college, actual draft slot/team/round and future career results are excluded. Imputation, scaling and one-hot encoding fit within the training fold. Feature and outcome stores are separate under `analytics/features` and `analytics/outcomes`. Original publication timestamps are unavailable and recorded as unknown, not backfilled with invented dates.

| Held-out method | N | Brier↓ | Log loss↓ | ROC-AUC↑ |
|---|---:|---:|---:|---:|
| globalBaseline | 613 | 0.23369 | 0.66017 | 0.5000 |
| positionBaseline | 613 | 0.23356 | 0.65985 | 0.5297 |
| logistic | 613 | 0.22312 | 0.63743 | 0.6263 |
| histGradientBoosting | 613 | 0.22672 | 0.64618 | 0.6068 |

Selected: logistic, logistic C=10.0, based only on 2015 Brier score. Gradient boosting was tested and rejected on validation. Experiments retain all settings and losses. Held-out calibration intercept -0.010, slope 0.887. Reliability bins are in the artifact; extreme bins have few cases. Descriptive Brier bootstrap 95% interval [0.21079568275105284, 0.23473329656767147], 500 individual resamples. It is conditional on observed cohorts and omits between-era uncertainty. No test-set recalibration was performed.

| Subgroup | N | Brier | ROC-AUC |
|---|---:|---:|---:|
| position / DB | 115 | 0.2361 | 0.641 |
| position / DL | 110 | 0.2483 | 0.607 |
| position / LB | 73 | 0.2055 | 0.637 |
| position / OL | 92 | 0.2145 | 0.632 |
| position / QB | 32 | 0.1933 | 0.562 |
| position / RB | 59 | 0.2151 | 0.641 |
| position / TE | 34 | 0.1977 | 0.769 |
| position / WR | 98 | 0.2242 | 0.554 |
| year / 2016 | 307 | 0.2168 | 0.665 |
| year / 2017 | 306 | 0.2294 | 0.593 |
| measurement_missingness / complete | 304 | 0.2235 | 0.664 |
| measurement_missingness / missing_one_or_more | 309 | 0.2228 | 0.590 |

Age, college-strength and injury subgroups are unsupported. No universal individual confidence interval is claimed.

## Game model

Predict home-minus-away score using prior-season realized scoring-margin difference and home-field indicator. Training 2000–2013; tuning 2014–2015; test 2016–2017. Selected ridge alpha=1000. Held-out RMSE=13.462 points versus constant baseline 13.743. Its 95% normal residual interval coverage=95.508%, width=56.56 points. These wide errors limit predictive use.

Final pre-2018 strength coefficient=0.4013; home effect=2.081; total-score mean=43.549. Method-of-moments residual decomposition over 573 historical team-seasons gives season-shock SD=4.699 and independent game SD=12.679. Two team-shock variances plus game-noise variance equal the marginal residual variance. Approximate opponent independence is a limitation.

Runtime applies the strength coefficient once to previous realized scoring margins, then adds season shocks and independent game noise. Next year's prior comes from simulated realized standings. The separate diagnostic annual persistence estimate must not be applied again; doing so double-shrinks the fitted signal.

## Boundaries

Only 336 combine participants are playable. The 39 retrospectively identified noncombine draftees are baseline-only. No five-year development, future roster transactions, injuries, NFL-wide MVP forecast or causal draft-to-wins mapping has been validated. Historical source revisions and incomplete original-publication archives prevent a claim of archive-perfect reconstruction. Later research is not represented as 2018 GM knowledge.

## Reproduce

```sh
python -m pip install -r analytics/requirements.txt
python analytics/train_models.py
python analytics/pooling_validation.py
python analytics/test_models.py
python analytics/render_reports.py
python analytics/plot_diagnostics.py
```

Raw ingestion is a prerequisite. Artifact records source SHA-256 hashes, environment and runtime. Complete training runtime=1.499s in `{"python": "3.12.14", "platform": "Linux-6.18.57-x86_64-with-glibc2.39", "numpy": "2.3.5", "pandas": "2.2.3", "scikitLearn": "1.8.0"}`; this is not hosted simulation latency.

## Runtime display policy

The raw trained model is wrapped by `blind-g5-v1` for both playable modes. Shared-profile probability pooling has a separate held-out utility evaluation: Brier0.222904 versus raw0.223124. See `analytics/BLIND_SCOUTING_EXPERIMENT.md`. This is not a validated five-year model or an anonymity guarantee.

## Five-year participation benchmark (2026-11-02)
New reproducible experiment:analytics/five_year.py; metrics:analytics/five_year_research.json; individual predictions saved separately. Frozen2018 production-policy holdout covers287 known-ID nonspecialists observed2018–2022. Five-year total-snap RMSE1467.80 vs1514.18 for position-only donors; MAE1177.17 vs1207.80. Nominal95% interval coverage93.73%,nominal80% coverage87.46%. These point improvements do not establish statistically significant superiority. QB interval coverage is75% on16 players; uncertainty is poorly captured in that subgroup. Targets are participation before game opportunity/strength transformations, not talent or causal team wins.

## November4 validation remediation

See `analytics/VALIDATION_REMEDIATION.md` for the full audit. A pre2018 recency comparison selected a trailing3-season unconditional scoring mean using2005–2012 forecast-origin losses. Later2013–2017 mean-score RMSE is1.3453 versus2.4684 for an expanding mean. The runtime override is44.87109375 points/game; original `model.json` remains immutable and the override has a separate version suffix. Future-score and assessment-selection poisoning tests pass. This development was motivated by earlier inspected post2017 failures; the2018 backtest is reused, not untouched.

Exact donor integration gives five-year snap RMSE1469.44 and nominal95% coverage93.73% across2872018 prospects. QB coverage remains75% (n16, only3 positive2013 donors); LB coverage87.5% (n48). CRPS improvement versus position donors has bootstrap95% interval[−66.11,+6.20], so superiority is unsupported. Games-with-snaps metrics are now evaluated separately. Sixteen fixed256-draw seed checks and all-position support/coverage gates retain failures. Eight new numerical/leakage/gate tests pass. The strict2018 forecast still lacks an independent pre2018 five-year chronological test.
