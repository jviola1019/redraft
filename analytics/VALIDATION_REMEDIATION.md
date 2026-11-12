# Validation remediation — 4 November 2026

The scoring mean now uses a defensible pre-draft recency estimate. The five-year forecast still fails important support and subgroup-calibration checks. A passing software suite is not evidence that those limitations have disappeared.

## Changes and chronology

`scoring_recalibration.py` compares an expanding score average with trailing3,5 and10-season means. Candidate choice uses one-season forecast origins2005–2012; each estimate sees only earlier seasons. The selected trailing3 rule is then assessed at later2013–2017 origins and at a frozen2013 five-season forecast. All numerical fitting, selection and assessment rows end in2017. Poisoning every2018+ score with999999 leaves the artifact unchanged. A separate test poisons2013+ scores and confirms that candidate choice remains unchanged.

| Scoring-mean assessment | Expanding average | Selected trailing3 |
|---|---:|---:|
| Selection2005–2012 annual-mean RMSE | 1.7213 | 1.2717 |
| Assessment2013–2017 annual-mean RMSE | 2.4684 | 1.3453 |
| Frozen2013 forecast of five annual means, RMSE | 2.7236 | 1.2816 |

The resulting2018 estimate is44.87109375 combined points/game, fitted on2015–2017. The original `model.json` remains unchanged; `scoring_recalibration.json` supplies an explicit runtime override and `+scoring-trailing3-v1` version suffix. Conditional margin and noise coefficients are unchanged. The runtime loader reproduces the application policy, verifies the team-context manifest hash, and records all ten runtime dependency hashes.

This is a development correction motivated by previously observed2018–2022 failures. The fact that its numerical fit is pre2018 does not make this a newly untouched post2017 test. Only five later pre2018 annual assessment observations and one frozen five-season window are available. The recency correction does not repair the discretized normal score distribution, prove future era stability, or identify player effects on wins. Fresh integrated simulation diagnostics remain necessary.

## Exact forecast audit

`forecast_audit.py` integrates the frozen weighted donor distribution exactly, eliminating Monte Carlo approximation error from these analytical predictions. No production forecast, donor, or role probability is refitted. The same2013 position/rookie-role mixture is evaluated against the already examined287 identifiable nonspecialist2018 prospects. Forecasts are assessed before runtime opportunity, capacity and snaps-to-wins transformations.

| Target | MAE | RMSE | Mean CRPS | Nominal95% coverage |
|---|---:|---:|---:|---:|
| Five-season total scrimmage snaps | 1175.78 | 1469.44 | 788.25 | 269/287 =93.73% |
| Five-season total games with recorded snaps | 25.04 | 28.27 | 16.32 | 269/287 =93.73% |

These exact-mixture metrics differ slightly from the earlier400-draw benchmark because finite-draw integration is removed. The earlier benchmark remains retained. Games with recorded snaps are not official appearances or starts.

The paired mean CRPS difference against unconditional position donors is−28.93; a2000-resample player bootstrap95% interval is[−66.11,+6.20]. This does not establish a distributional skill improvement. The bootstrap conditions on one cohort and does not account for between-era uncertainty or team clustering.

| Position | Donors | Rookie-role-positive donors | Evaluated2018 players | Exact95% snap coverage | Actual totals beyond donor support |
|---|---:|---:|---:|---:|---:|
| DB | 57 | 26 | 58 | 91.38% | 3 |
| DL | 49 | 19 | 36 | 97.22% | 1 |
| LB | 38 | 12 | 48 | 87.50% | 4 |
| OL | 53 | 14 | 46 | 97.83% | 0 |
| QB | 15 | 3 | 16 | 75.00% | 4 |
| RB | 34 | 7 | 28 | 100.00% | 0 |
| TE | 18 | 7 | 16 | 100.00% | 0 |
| WR | 37 | 15 | 39 | 97.44% | 0 |

QB95% coverage has a descriptive Wilson interval of[50.50%,89.82%]. The QB games-with-snaps interval covers81.25%. LB snap coverage has a Wilson interval of[75.30%,94.14%]. These subgroup intervals assume approximate independence and are not a multiple-testing-adjusted population assertion. Wide intervals or100% empirical coverage in small groups do not prove good calibration; width and proper interval scores are retained too.

The QB ceiling cannot be corrected by running more seeds. Four2018 QB totals exceed every2013 donor. Inflating those tails until2018 coverage passes would tune directly to examined outcomes. Cross-position tail pooling would introduce a new football assumption without an independent strict chronological test. Neither was silently introduced.2012 snap data remains unavailable;2013 is the only complete five-year donor cohort at the2018 cutoff. Specialist skill remains unsupported.

Sixteen fixed seeds,2026110400–2026110415, each produce256 draws per prospect. Their per-position numerical errors and interval coverages are retained in `forecast_audit.json`. This measures finite-ensemble precision, not new information about talent, injury, or causal team outcomes.

## Executable release gates

Run:

```sh
python analytics/forecast_audit.py
python analytics/scoring_recalibration.py
python analytics/test_statistical_gates.py
python analytics/statistical_gates.py
```

Eight analytical tests passed. Tests cover exact finite-mixture scoring, point-mass limits, probability conservation, coverage uncertainty, metric recomputation, both temporal poisoning checks, and retention of known release blockers.

The gates check the cutoff, metric reconstruction, independent chronological evidence, conditional donor counts, all eight position subgroups for snaps and games, specialist support, distributional skill, causal-effect support, four current simulation configurations,256-replicate precision, and source-hash freshness. Default exit2 means the audit completed with adverse, unsupported or stale evidence; exit1 means execution failed. `--report-only` changes only exit handling, never the recorded result.

Thresholds are explicit engineering screening rules established after previous findings were seen. They are not preregistered statistical significance criteria. Current thresholds require at least10 donors per conditional stratum; at least90% coverage for nominal95% subgroup intervals; at most.25 wins and.032 probability Monte Carlo standard error; and256 replicates per declared scenario. These rules cannot certify causal validity or guarantee performance in new eras. Full production-validation claims remain blocked while independent strict chronology, thin donor groups, QB/LB coverage, specialist quality or causal mappings remain unsupported.

Fresh integrated results are generated by the coordinated QA gauntlet and archived there. Old diagnostics with mismatched model, context or source hashes are explicitly stale and cannot count as current evidence. No threshold is relaxed to erase a failed result.

## Methods references

- Gneiting and Raftery,2007, *Strictly Proper Scoring Rules, Prediction, and Estimation*, Journal of the American Statistical Association. CRPS and interval scores assess distributions with sharpness and missed outcomes jointly. [Author-hosted paper](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).
- NIST/SEMATECH, *Confidence intervals for proportions*. Wilson score intervals provide a descriptive uncertainty summary for observed coverage. [NIST handbook](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
- Hyndman and Athanasopoulos, *Forecasting: Principles and Practice*, time-series cross-validation. Forecast-origin evaluation uses only prior observations for each estimate. [Textbook chapter](https://otexts.com/fpp3/tscv.html).

References support the procedures, not the adequacy of this particular NFL model. All measurements above come from executed repository analyses.
