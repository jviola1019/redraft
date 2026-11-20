# QB age-rank hindcast protocol

## Fixture plan

Use complete regular-season snap sources and known-ID combine QB cases. Freeze 2016–2017 as the early-origin assessment, and 2018–2021 as the later-origin assessment. These cohorts have previously been examined. Fit tables contain annual observations ending strictly before the draft year, using the March 1 availability convention. Keep each player's five-season outcome vector together when resampling assessment losses. Unknown target IDs are recorded as exclusions. No post-2025 actuals enter the analysis.

Synthetic fixture checks cover paired snaps and games, ties, zero participation, changing age marginals, adverse later-outcome poisoning, schedule multipliers and raw actual preservation. The 2018 production-policy baseline must independently reproduce the exact QB snap and games gate results using the unchanged audit. Compare early origins against paired persistence since complete histories were unavailable. Compare later origins with expanding complete-donor baselines and, in 2018, the frozen production weighting. Publish 80% and 95% coverage and width, interval score, CRPS, and support exceedances for each target.

## Model specification

Draw a single latent percentile on an equally spaced midpoint grid. Within each age, select the observed annual QB row at that percentile ordered by snap counts, then games and stable identifier. Carry that row's snaps and games together. The percentile persists across ages. This is a parameter-free empirical model of strong persistent usage rank, with age-specific marginals constructed from incomplete careers as well as complete ones. Its main vulnerability is overdependence across seasons. All known annual observations in the first five career years, including players from older cohorts with truncated observations, are eligible if date-valid. Do not adjust rank dependence, quantiles, predictor set or cohorts based on assessment results.

Normalize annual training values to a 16-game schedule based on league scheduled games. For the draft-time forecast, use 16 for origins before the 17-game schedule was announced in March 2021, and 17 thereafter (in the 2021 case). This treats the then-current schedule as persisting through the horizon. Also run the identical forecasts with the realized future schedule as a separately labeled retrospective sensitivity. Game totals can be fractional after exposure scaling, and actuals remain integer counts. The strike-like 2022 Buffalo/Cincinnati cancellation does not change the league schedule exposure away from 17.

## Blind evaluation prompt

Given only the protocol, chronological fixtures and masked candidate keys, verify that training and schedule assumptions respect the origin, that outcomes are excluded from model selection, and that summaries can be recomputed from paired person-level scores. Report paired CRPS differences, cohort-specific scores, coverage, width and interval scores for five-year snaps and games. Evaluate each key against the frozen decision criteria before reading its identity. Flag leakage, cohort reuse, weak support and overdispersion. Do not fit or select a variant from assessment outcomes. This is a reproducible prompt for an independent reviewer. Previously published outcomes prevent a genuinely blind holdout claim here.

## Decision criteria

Advance to independent QB validation only if the candidate improves pooled CRPS over the applicable comparison in both era groups for both targets, with the upper bound of the cohort-stratified player-bootstrap 95% interval below zero. Require at least 90% 95%-interval coverage for both targets in the frozen 2018 audit and a mean 95% interval score no worse than the frozen production baseline. Apply the decision to the draft-time schedule only. Treat a threshold miss as evidence against advancement under this protocol. Production adoption additionally requires an independently untouched chronological cohort and satisfaction of the existing published release gates. More fitted annual rows do not fulfill the release gate that requires complete conditional donors.
