# Bounded QB annual-transition experiment — 12 November 2026

The annual transition model improves probabilistic next-season forecasting in its pre-2018 assessment and reaches real annual usage levels absent from the 2013 whole-career donor sample. This is useful evidence for further research. It does not establish calibrated five-year rookie careers, so the production model and all failed gates remain unchanged.

## Frozen comparison protocol

Fit transitions ending in 2014; select the configuration using 2015 next-year CRPS. Then fit the selected rule on transitions ending in 2015 and assess annual outcomes in 2016–2017. Candidate states were fixed as zero, 1–199, 200–599 and 600+ scrimmage snaps. Candidates use the prior state alone or prior state plus second-season versus third-through-fifth-season experience, with shrinkage pseudo-counts 0, 5 or 20. Selection chose **state only, no shrinkage**. These thresholds are declared research choices; they were not optimized against 2018 outcomes.

The final research fit uses annual observations through 2017 only. Each annual label carries a conservative March 1 availability date in the following year. An executed poisoning check replaces all 2016–2017 assessment outcomes and confirms candidate selection is unchanged. The 2018 outcome table is loaded only after selection and the pre-2018 annual assessment. Its later evaluation is explicitly an already exposed backtest.

## Source, survival and absence audit

Complete regular-game coverage is reconciled against schedules for every 2013–2017 source year. The panel contains 380 player-years and 243 adjacent-year transitions from 106 quarterbacks within their first five seasons. It includes known-ID combine QBs from cohorts 2009–2017 where the required annual observations fall in the source window. Unknown PFR identities are excluded and listed in the JSON. No name-only fuzzy joins are added.

In 208 panel rows, a known player ID is absent from the fully covered annual snap file. These are zero **recorded NFL snaps**, not imputed roster membership, retirement, injury or failure to play elsewhere. The observed transition table includes 21 zero-to-positive transitions; zero therefore is not an absorbing retirement state. This panel cannot distinguish reasons for absence, and the model makes no survival-cause claim. Source hashes and coverage counts are retained.

The final rookie source has 77 quarterbacks across 2013–2017, including 17 with at least 200 rookie snaps. This broadens first-year evidence without borrowing non-QB outcomes. Later-year draws use actual QB successor-year snap counts in the selected state. Full simulated paths recombine annual records across people; they are model estimates and must never be presented as historical career records.

## Annual assessment

| Forecast | Player-year cases | MAE | RMSE | CRPS | 95% coverage | Mean 95% width |
|---|---:|---:|---:|---:|---:|---:|
| Selected transition | 121 | 123.05 | 213.94 | 78.10 | 94.21% | 575.37 |
| Unconditional transition baseline | 121 | 269.98 | 343.94 | 147.67 | 96.69% | 1058.00 |
| Persistence point forecast | 121 | 98.52 | 201.82 | 98.52 | 46.28% | 0.00 |

The paired CRPS difference against unconditional transitions is -69.57, with player-cluster bootstrap 95% interval [-108.84, -32.96]. The assessment has 121 player-years but only 76 unique players; 47 also appear in training. This is a known-player next-season forecast conditional on observed prior-year usage. Player clustering addresses repeated people, but not shared season/team variation. Only two assessment seasons are available.

The point-persistence baseline has lower MAE and RMSE but substantially worse distributional CRPS and interval coverage. That mixed outcome does not by itself reject a probabilistic transition model. It means the target and loss function matter; annual conditional prediction and five-year rookie forecasting are distinct tasks.

## Exposed 2018 five-year diagnostic

Use the frozen 2018 pooled rookie-role probabilities, pre-2018 annual observations and the selected transition rule. Sample 8,192 paths per quarterback; three additional fixed seeds check numerical stability. No 2018 label selects the transition state definition, smoothing or outcome draws.

| Measure | Result |
|---|---:|
| Five-year total MAE | 1338.98 |
| Five-year total RMSE | 1845.13 |
| Five-year CRPS | 917.12 |
| 80% interval coverage / width | 75.00% / 2950.94 |
| 95% interval coverage / width | 93.75% / 4724.12 |
| Cases outside sampled support | 0 / 16 |

The higher 95% coverage comes with a much wider interval than the former 2013 donor interval (approximately 4,724 versus 1,965 snaps), and five-year MAE is worse than that prior diagnostic. All 16 quarterbacks were already examined. This result is insufficient for promotion; it is neither an untouched test nor proof that the longer trajectory is calibrated.

## Dependence and target limitations

The transition model retains dependence on the previous annual usage state. It does not retain a single person’s latent ability, persistent coaching context, team opportunity, injury mechanism, or higher-order career dependence. Pooling within state can create unrealistic sequences even though every annual sampled value was observed. The research does not supply contracts, starts, causal wins or specialist forecasts. The binomial coverage intervals remain descriptive; repeated-player annual rates are not independent Bernoulli trials.

## Deferred next experiment

After the fixed gauntlet finishes, generate chronological five-year forecasts for the 2016 and 2017 QB cohorts, with annual-transition observations ending in 2015 and 2016 respectively. Hyperparameters selected on 2015 are available before those forecasts. Compare total and annual CRPS, 80%/95% coverage and width, trajectory dependence, and a frozen annual-persistence baseline. This isolates whether the annual gain transfers to the requested full career target.

A strict full-five-year donor comparator is unavailable at those early cutoffs: the first complete 2013 donor cohort only becomes available in 2018. Importing those finished careers into a 2016/2017 baseline would leak future labels. An older-donor comparison must therefore either obtain independent earlier records or be labeled a retrospective reference with a later information set. Do not present it as a contemporaneous fair baseline. These cohorts have appeared in other research, so they must not be advertised as newly untouched.

## Scoring and rank audit findings

The existing shutout-hurdle experiment has mixed, small gains. Its retrospective `runtime_score_law()` reads the base `model.json` mean (43.54895), omits the runtime recency override (44.87109), and uses independent game margin noise without integrating team-season shocks. Its team aliases also differ from the canonical runtime. Thus its `currentCorrelatedNormal` label describes a research approximation, not an exact replay of the current application. That experiment cannot alone justify a production hurdle correction.

The score sensitivity calculation did contain a repairable defect. It previously ranked raw composites while production rounds scores to integers, then used a no-ties Spearman formula. The updated analysis reports shared official ranks, Spearman as Pearson correlation of average tied ranks, and the whole set of tied leaders. Raw rankings remain separately labeled exploratory. All-equal scores yield an explicit undefined-correlation status, and duplicate policy identities are rejected. Runtime scoring weights and gate thresholds are unchanged.

## Verification and references

Six transition checks pass: conservative label availability and absence semantics; assessment-label poisoning; state/mixture validity; metric reconstruction; deterministic paths using only empirical annual values; and source hashes with no runtime promotion. Nine ranking checks pass, including ties, constant ranks and duplicate rejection.

- Jackson (2011), [Multi-State Models for Panel Data](https://www.jstatsoft.org/article/view/v038i08), explains the Markov assumption and the need to assess it. This experiment is a discrete annual empirical transition model, not an implementation or validation of that paper’s clinical examples.
- Gneiting and Raftery (2007), [Strictly Proper Scoring Rules, Prediction, and Estimation](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf), supports CRPS and joint evaluation of interval width and misses.

The sources justify the statistical procedures, not the accuracy of this NFL counterfactual. Results are reproducible from `qb_transition_experiment.py`, its JSON, saved panel/pair/prediction tables and tests. No gate was relaxed.
