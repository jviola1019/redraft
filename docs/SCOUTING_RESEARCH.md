# Blind scouting: college, statistics, and recognition

Verified execution date: **2026-11-02 (UTC)**. Policy: `blind-g5-v1`. This is a research release for the verified 2018 combine pool, not a completed validation of the full product specification.

The design question is: **“Is the college worth showing on the draft boards, other stats or will people automatically know ‘Hey that guy is Tom Brady lets draft him first’?”**

The supported answer is to **withhold college and individual exact statistics on the blind draft board**. Hiding names alone is insufficient. College, position, draft year, measurements, missing-test patterns, and exact prediction probabilities can jointly act as identity clues. This is a measured linkage risk in our data; it is not proof that all users recognize all players. Tom Brady is an illustration of the concern, not a tested 2018 participant or an empirical estimate of recognition.

## What we actually measured

`python analytics/identity_audit.py` reads the installed production data and executes the production TypeScript disclosure policy. It writes `analytics/identity_audit.json`, including file hashes. The population is **336 verified 2018 combine participants**. The 39 additional prospects identified through the eventual draft are historical-reference-only and excluded from these counts and gameplay eligibility.

| Joint information released | Candidates with a unique profile | Fraction |
|---|---:|---:|
| College + exact position | 265 / 336 | 78.9% |
| Exact position + exact height + exact weight | 285 / 336 | 84.8% |
| Exact position + 40-yard time + vertical + broad jump | 297 / 336 | 88.4% |
| Exact position + college + height + weight + 40-yard time | 336 / 336 | 100.0% |
| Exact position + all eight exact measurements | 334 / 336 | 99.4% |
| Exact position + all eight individually coarsened measurements | 328 / 336 | 97.6% |
| Full cumulative evidence released by the shared-profile policy | 0 / 336 | 0.0% |

Individually coarsened widths are 3 inches for height, 15 pounds for weight, 0.2 seconds for the 40-yard dash/cone/shuttle, 5 reps for bench, 5 inches for vertical and 10 inches for broad jump. The exploratory comparison uses nearest-band indices. Null values remain their own category, because missingness itself can identify a record. The implemented group ranges instead round the group's observed minima downward and maxima upward.

These are exact descriptive counts in a finite cohort, so a sampling confidence interval on them would be misleading. They measure matching uniqueness, **not human recognition probability**. Most importantly, broadening each field separately did not solve the joint-disclosure problem.

## Evidence and inference

Sweeney's 2002 peer-reviewed work formalizes groups sharing the same released quasi-identifiers. We borrow the idea of checking the entire released profile, rather than checking each field independently. Our chosen minimum of five is a practical engineering policy; the paper does not establish that five is sufficient for this game. [Sweeney, 2002](https://doi.org/10.1142/S0218488502001648), [author's institutional record](https://www.hks.harvard.edu/publications/k-anonymity-model-protecting-privacy).

Narayanan and Shmatikov demonstrate that auxiliary knowledge and cross-dataset matching can reidentify records after names are removed, including when data is imprecise. Their experiment concerns movie ratings, not NFL prospects. The inference for REDRAFT is that removing names or rounding measurements cannot be treated as a recognition guarantee; the installed NFL cohort needs its own audit. [Narayanan & Shmatikov, IEEE Symposium on Security and Privacy, 2008](https://www.cs.cornell.edu/~shmat/shmat_oak08netflix.pdf).

A 2023 systematic review retained 68 studies on NFL combine predictive validity and reported mixed evidence for predicting future success. That supports caution about a combine-only universal talent rating. It does not tell us which disclosure policy is most enjoyable or how accurately users recognize prospects. [Rishis, Johnston & Baker, 2023](https://pubmed.ncbi.nlm.nih.gov/37150872/).

All three sources were checked on 2026-11-02. Published research can guide the design; it cannot substitute for this application's empirical tests.

## Implemented policy

`lib/scouting.ts` is a server-side transformation with a browser-field whitelist.

1. Group eligible candidates into QB, RB, WR, TE, OL, DL, LB, DB and ST. ST combines kickers, punters and long snappers; exact position subtypes remain hidden.
2. Within each position, sort by the frozen pre-draft rookie-role model probability, breaking ties with canonical IDs. Partition into five-member groups and merge a final short group into its predecessor. A position with fewer than five candidates fails closed. The installed data produces **63 groups, each with 5–9 members**.
3. Give every group member the same outward-rounded ranges derived from known real group measurements. These are **group summaries, not invented individual measurements**. The same explanatory note appears on every card. A range does not assert that this particular candidate completed the test.
4. One scouting action spends one credit and reveals the entire shared group profile, including the group mean predicted probability in a 10-percentage-point band. Attempting to spend again on an already unlocked group is rejected by the API. The bar midpoint is a rendering aid, not a precise individual prediction or a confidence interval. The target is **at least 200 rookie-season offensive or defensive snaps**, not becoming a starter, being elite, or five-year talent. Specialists have no supported probability for that target.
5. CPU decisions, draft scoring and simulated development inputs use the same pooled probabilities. Grouping does not grant the CPU individual model estimates withheld from the player. The simulator still contains assumptions beyond the measured rookie target; pooling does not validate those assumptions.
6. Browser IDs use HMAC-SHA256 with a private persisted salt. They are stable within a saved run and unrelated across historical runs. Human-readable labels are assigned from those aliases, not source order or real-name order. Reference-only prospects cannot alter playable labels. Private salts and canonical IDs remain server-side.
7. Historical runs reveal identity after draft completion. Daily runs additionally embargo identity until the next UTC calendar date, including when ready, simulating or complete. Before identity reveal, do not send college, real names, canonical IDs, exact measurements, individual source links, individual measurement counts, availability timestamps, missingness fingerprints, or precise probabilities. The frontend cannot recover these from hidden HTML or the prospect response.

The policy version is appended to the base model version, and simulation diagnostics must identify the pooled version. Fully scouted cumulative evidence—not just the initial card—passes the minimum-five audit. No drafting algorithm may introduce actual selection order or future careers into the grouping.

## Predictive information retained

`analytics/pooling_validation.py` evaluates the transformation on separate held-out 2016 and 2017 cohorts. The rookie model trains on 2013–2014 and tunes on 2015. Each test cohort is grouped independently by position using pre-draft predictions before outcome labels are joined. All 635 available nonspecialist candidates enter grouping; 613 have known labels for evaluation. Unknown outcomes are excluded from scoring, not converted to zero.

| Held-out measure | Individual model | Shared mean | Display-band midpoint |
|---|---:|---:|---:|
| Brier score, lower is better | 0.223124 | 0.222904 | 0.222892 |
| ROC-AUC | 0.626350 | 0.629158 | 0.626646 |
| Log loss, lower is better | 0.637433 | 0.637529 | 0.637866 |

The paired mean-pooling Brier difference is −0.000221, with a within-cohort bootstrap 95% interval of **−0.002285 to +0.001675**. The display-midpoint difference is −0.000233, interval **−0.003066 to +0.002609**. These intervals are conditional on two test cohorts and do not represent era-to-era uncertainty.

The measured change is small in this experiment. This is **not an equivalence or noninferiority result**: no acceptable-loss margin was preregistered, the test cohorts are limited, and predictive scoring is not human draft quality. College and verified college production were not predictors in this model, so the experiment cannot establish that hiding them costs no useful information.

## Which information is worth showing

| Information | Current treatment | Rationale and condition for expansion |
|---|---|---|
| Broad position | Show | Needed for roster allocation; subtype withheld when identifying |
| College name | Withhold until reveal | High observed matching uniqueness; untested incremental decision benefit |
| Athletic testing | Show shared group ranges | Real source measurements summarized without unique individual fingerprints |
| Rookie-role projection | Scout for shared 10pp band | Tested narrow target; label and calibration limits remain visible |
| Individual missingness | Withhold | Can fingerprint an athlete; never turn unknown into zero |
| College production | Unavailable in this release | Do not invent; ingest licensed point-in-time, position-specific usage and efficiency first |
| Competition context | Unavailable in this release | Broad tiers may be useful, but must be audited jointly with all other fields |
| Injuries, awards, comparables | No invented reports | Requires dated verified sources; named comparables and distinctive injuries may identify the candidate |
| Historical names and exact facts | Reveal after the permitted reveal boundary | Education and outcome interpretation, not a pre-draft projection input |

A future expansion should prefer contextualized, position-specific college production with denominators and uncertainty over a single universal rating. Any additional field must pass a fresh **cumulative** profile audit and chronological predictive evaluation. Simply calling it a percentile does not make it safe: many precise percentiles are unique.

## Limits that remain

- Five matching profiles initially do not guarantee five plausible identities throughout the draft. Eliminations, public pool knowledge, group inference and informed football memory can narrow possibilities.
- A small fixed historical pool can be learned over repeated play. No truthful-data interface can promise that experts forget history.
- Shared daily aliases plus immediate completion reveals would enable one player to publish a full alias dictionary. This implementation embargoes identities until the next UTC date. Unit tests cover ready, simulating and complete states around rollover; the API and result payloads still require integration checks. This blocks an immediate direct alias dictionary, not inference or repeated-play learning.
- Grouped scouting deliberately removes distinctions between some prospects. Those selections may become indistinguishable under the current model. This reduces analytical detail and requires playtesting for enjoyment and strategy.
- Candidate labels, scouting interactions, CPU reactions, result payloads, bundles and exports require integration-level inspection, not merely a prospect DTO test.
- Actual future careers are not used to make a famous player's simulated path inevitable. Familiarity can still change selection preferences; counterfactual outcomes remain model-dependent.

## Human validation still required

No human recognition or usability experiment has been run. A defensible next study should preregister four disclosure conditions: college plus exact measurements; no college plus exact measurements; individually coarsened measurements; and shared profiles. Use casual, regular and expert football participants; randomize disjoint candidate subsets so one person never sees the same athlete twice across conditions. Separate unaided memory from permitted external lookup.

Measure correct free-response identity, candidate-set size, confidence, response time, college-reveal requests, draft decisions and usability. Evaluate subgroup differences and cluster uncertainty by both participant and prospect. A pilot should estimate variance and set the subsequent sample size and a decision-relevant equivalence margin. Model-based expected utility may assess decisions, but must not be called true causal five-year value. Log recognition claims and wrong guesses rather than scoring only correct famous-player recollections.

Test on held-out prospects and future cohorts before asserting generality. Run an adversarial API and browser audit for precise measurements, canonical hashes, source URLs, ordering clues and cross-run leakage. Test the daily reveal boundary and rollover explicitly. A published profile-count audit is necessary evidence for this release, not a substitute for these unfinished studies.
