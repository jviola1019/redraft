# Historical playoff forecast benchmark

The simulator scored a Brier loss of **0.24016** across the locked historical forecasts. A benchmark built from each franchise’s prior-year regular-season point margin scored **0.23775**, a difference of **0.00242** in the benchmark’s favor. The simulator’s estimated finite-draw correction reverses this small overall gap. The four-season horizon is the only horizon where the benchmark leads after the horizon-level correction and in every raw comparison omitting one season or two adjacent seasons.

## Paired Brier comparison

Lower Brier is better. The paired gap is simulator loss minus benchmark loss, so a positive gap favors the benchmark. The raw scores are primary. The adjusted gap and Monte Carlo standard error are reported separately.

| Seasons ahead | Forecasts | Actual seasons | Simulator | Benchmark | Paired gap | Adjusted gap | Simulator MC SE |
|---|---:|---:|---:|---:|---:|---:|---:|
| Overall | 960 | 8 | 0.24016 | 0.23775 | +0.00242 | −0.00130 | 0.00211 |
| 1 | 256 | 8 | 0.22521 | 0.22569 | −0.00048 | −0.00395 | 0.00363 |
| 2 | 224 | 7 | 0.23530 | 0.23593 | −0.00062 | −0.00438 | 0.00407 |
| 3 | 192 | 6 | 0.24662 | 0.24616 | +0.00047 | −0.00335 | 0.00485 |
| 4 | 160 | 5 | 0.25788 | 0.24347 | +0.01441 | +0.01057 | 0.00519 |
| 5 | 128 | 4 | 0.24672 | 0.24526 | +0.00146 | −0.00237 | 0.00567 |

When both models use the realized playoff format, the benchmark’s overall Brier is 0.23690 and the raw gap is +0.00326. The four-season gap increases to +0.01591. The original comparison against realized slot prevalence (Brier 0.24492) therefore gives a more favorable impression of the simulator’s predictive value than this strength benchmark.

## Stability across actual seasons

An entire actual season is removed at once, including every franchise and every forecast targeting that season. The 960 rows cover only 256 distinct franchise-season outcomes. Adjacent-pair omissions retain the chronology of each omitted block. These ranges describe sensitivity to the observed seasons. Generalization uncertainty remains unquantified.

| Seasons ahead | Drop any one season | Drop any adjacent two seasons |
|---|---:|---:|
| Overall | +0.00054 to +0.00629 | −0.00227 to +0.00492 |
| 1 | −0.00291 to +0.00368 | −0.00428 to +0.00481 |
| 2 | −0.00511 to +0.00897 | −0.00988 to +0.01231 |
| 3 | −0.00107 to +0.00423 | −0.00254 to +0.00509 |
| 4 | +0.00929 to +0.02402 | +0.00136 to +0.03012 |
| 5 | −0.00693 to +0.00883 | −0.00805 to +0.00300 |

| Actual season | Overall gap | Horizon 1 | Horizon 2 | Horizon 3 | Horizon 4 | Horizon 5 |
|---|---:|---:|---:|---:|---:|---:|
| 2018 | +0.00749 | +0.00749 | — | — | — | — |
| 2019 | +0.00552 | −0.00503 | +0.01608 | — | — | — |
| 2020 | +0.01237 | +0.00999 | +0.02632 | +0.00080 | — | — |
| 2021 | +0.00017 | −0.00540 | +0.01872 | −0.01834 | +0.00570 | — |
| 2022 | −0.00340 | +0.01655 | −0.02017 | +0.00611 | −0.02401 | +0.00454 |
| 2023 | +0.01182 | +0.00529 | +0.02061 | +0.00482 | +0.03306 | −0.00469 |
| 2024 | +0.01176 | −0.00314 | −0.00773 | +0.00814 | +0.03491 | +0.02663 |
| 2025 | −0.01695 | −0.02957 | −0.05821 | +0.00128 | +0.02240 | −0.02063 |

The overall result weights each eligible forecast equally, so actual seasons with five origins receive more weight than seasons with one origin. Horizons also cover different actual seasons. The four-season result reflects five target seasons, with 2022 favoring the simulator.

## Information cutoff and reproduction

The frozen protocol fits a ridge logistic slope separately for every origin and horizon. Its sole predictor is average regular-season point differential from the season immediately before a draft. Training starts with the 2002 strength season and uses only completed training targets and recorded game dates before the origin. Historical postseason participation defines those training labels. Forecast probabilities total the approved NFL playoff slots as of April 1 of each origin. The 14-team format was approved March 31, 2020. The realized-format sensitivity uses that format for all forecast targets from 2020 onward, including those forecast from earlier origins. [NFL announcement](https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961)

The simulator inputs retain the retrospective conditions documented in the original audit, including recorded final draft allocations and starting-season scheduling. Its 64 seeds contribute simulation error distinct from season-to-season forecasting error. The finite-draw adjustment and Monte Carlo SE come from the original path-aware audit. The comparison covers already exposed historical outcomes and addresses playoff qualification forecasts. Draft intervention effects remain untested. [Original simulator audit](../playoff_forecast_REPORT.md)

Run from the repository root with the existing archived nflverse schedule snapshot available in `data/raw/games.csv`.

```bash
python analytics/playoff_benchmark/benchmark.py
python -m unittest discover -s analytics/playoff_benchmark -v
```

The script checks every locked label against the complete observed postseason, including participation by teams with first-round byes. Four tests cover origin cutoff poisoning, forecast slot counts around the expansion, probability order, and season-block coverage. The archived raw schedule snapshot is gitignored. The output records its SHA-256, the source audit hash, and all fitted slopes and training years. [Protocol](protocol.json) · [Results](results.json) · [Paired predictions](predictions.csv)
