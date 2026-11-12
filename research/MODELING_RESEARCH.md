# Modeling research and evidence limits

Reviewed 2026-11-02. Later publications inform present-day methodology; they are not asserted to be information available to a 2018 NFL decision-maker. No article text is reproduced.

| Source | Design implication |
|---|---|
| Kuzmits & Adams (2008), [NFL combine and performance](https://pubmed.ncbi.nlm.nih.gov/18841077/) | Physical testing did not consistently predict the studied NFL outcomes across positions. Athletic percentiles must not be labeled talent ratings. |
| Cook et al. (2020), [Combine and game performance](https://pubmed.ncbi.nlm.nih.gov/32459737/) | The studied combine-to-performance relationships were weak. The REDRAFT model needs its own outcome-specific evaluation. |
| 2023 [systematic review of combine predictive validity](https://pubmed.ncbi.nlm.nih.gov/37150872/) | Mixed findings do not support a general claim that combine tests reliably identify future stars. |
| Massey & Thaler (2013), [The Loser's Curse](https://faculty.wharton.upenn.edu/wp-content/uploads/2013/08/massey---thaler---losers-curse---management-science-july-2013.pdf) | Pick-market prices and player surplus are different quantities. Do not mix trade-chart scales or interpret market value as causal player contribution. |
| Hyndman & Athanasopoulos, [time-series cross-validation](https://otexts.com/fpp3/tscv.html) | Fit transformations and model choices only using earlier observations; labels must be available by the forecast origin. |
| Van Calster et al. (2019), [Calibration](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/) | Examine calibration directly; discrimination alone is insufficient. Reliability plots, slope/intercept and proper scoring rules are complementary diagnostics. |
| NIST SP800-188 (2023), [De-identifying government datasets](https://csrc.nist.gov/pubs/sp/800/188/final) | Removing direct identifiers does not establish resistance to linkage. Evaluate combinations of quasi-identifiers and the information/utility trade-off. Applied here as a game-recognition design principle, not a claim that privacy law governs public NFL records. |

## Models actually trained

A constant probability, position-shrunk baseline, logistic models at four regularization settings, and histogram gradient boosting were trained for the same rookie snap target. Game-margin linear and ridge regressions were compared against a constant baseline. The Nov2 extension independently tunes a coarsened-measurement logistic model on the same historical validation cohort and evaluates probability-band midpoints.

## Models not implemented

Hierarchical development, survival/multistate career models and possession models require annual verified roles, opportunity, production and censoring. They were not substituted with unexplained ratings. No deep-learning model was added without a demonstrated benefit for this small tabular dataset.

## What the evidence cannot establish

The measured rookie participation target is neither underlying talent nor five-year success. Team context, selection and injury affect observed opportunity. An observational model cannot establish the causal result of drafting a particular athlete onto a different team. The simulation's development/roster mechanisms require explicit assumption labels. Predictive performance preserved by coarsening does not prove that users retain equal decision quality or cannot recognize famous prospects. Real pre-draft college-production coverage is unavailable, so no experiment validates its proposed inclusion or masking.
