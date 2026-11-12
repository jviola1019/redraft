# Blind scouting: identity disclosure and validation

## Product finding

Hiding the player’s name does not make an NFL prospect anonymous. Draft year, college, position and an unusual statistical or athletic profile can identify a player to a knowledgeable fan or an external search. Exact missingness patterns and model probabilities can become fingerprints too. Blind scouting should be described as **reduced identity disclosure**, not anonymity or proven prevention of hindsight advantage.

This is an inference for REDRAFT from primary re-identification research, not a measured NFL recognition rate. Sweeney’s k-anonymity framework treats combinations of attributes that link to outside information as quasi-identifiers; generalization and suppression can increase ambiguity. Narayanan and Shmatikov demonstrate linkage attacks using auxiliary information against sparse records, including imperfect matches. Neither paper measured NFL fans, combine records, draft-game fairness, or this application. Population re-identification percentages from health/voter or Netflix studies must never be transplanted into a football claim.

## Primary references

1. Sweeney, L. (2002). *k-Anonymity: A Model for Protecting Privacy*. International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 10(5), 557–570. [Publisher DOI](https://doi.org/10.1142/S0218488502001648); [author research page](https://dataprivacylab.org/people/sweeney/kanonymity.html). Mechanism: a record shares released quasi-identifier values with at least k−1 other records under the specified threat model. This is not a universal guarantee against arbitrary auxiliary knowledge.
2. Sweeney, L. (2002). *Achieving k-Anonymity Privacy Protection Using Generalization and Suppression*. Same journal, 10(5), 571–588. [University-hosted original paper](https://ics.uci.edu/~projects/295d/papers/achieving-k-anonymity-privacy-protection-using-generalization-and-suppression.pdf). Mechanism: less-specific but semantically consistent values and field suppression; usefulness can be lost through overgeneralization.
3. Narayanan, A., & Shmatikov, V. (2008). *Robust De-anonymization of Large Sparse Datasets*. IEEE Symposium on Security and Privacy, 111–125. [Author-hosted paper](https://www.cs.cornell.edu/~shmat/shmat_oak08netflix.pdf); [publisher DOI](https://doi.org/10.1109/SP.2008.33). Mechanism: record linkage can tolerate partial background information and imperfect matches. It does not establish that every sparse record is identifiable.

Sources were retrieved during the reconstruction session. Their publication dates are above; their findings are interpreted conservatively for game design.

## Threat model

The protected property is competitive resistance to recognizing future NFL careers. The athletes’ source records are public sports facts; this document does not claim a private medical-data protection system.

| Attacker capability | Example | Mitigation | Residual limitation |
|---|---|---|---|
| Read browser/API payload | Canonical ID embeds a surname or provider slug | Server-issued random per-run public ID; private lookup server-side | Any exposed canonical bridge defeats this |
| Inspect bundle/network | Hidden name shipped in JSON/CSS/DOM | Explicit whitelisted response DTO; no client outcome/catalog imports | Build artifact inspection and response tests required |
| Remember football history | Year + college + QB | Daily disclosure omits college and other highly identifying detail | Some athletes remain distinctive by position/measurements |
| Search exact stats | Height, weight, forty time, college-season line | Show true coarse bands or rounded percentiles, not exact values | Coarse combinations can remain unique |
| Compare absent fields | Unique combination of missing drills/injury entries | Group completeness labels rather than all per-field flags in daily | Suppression must not imply a measurement exists |
| Sort/fingerprint records | Alphabetic order, actual-pick order, stable rank IDs | Seeded independent ordering and opaque IDs | CPU sequence itself may carry information |
| Match model output | Exact six-decimal projection uniquely matches a public model | Banded projection display; do not ship hidden precision | A band may still isolate a small group |
| Combine scouting actions | Separate reveals jointly identify a player | Audit the cumulative disclosed feature set, not each action alone | Strong scouting information and identity resistance conflict |
| Follow source links | Player-specific URL contains name/slug | Pre-draft source-family links; exact record lineage server-side and after reveal | Broad sources can still be searched manually |
| Cross-run linkage | Same prospect ID/order repeated daily and historical | Distinct public ID maps and ordering per run | Repeated true attribute vectors can still be linked |
| Create multiple accounts | Open practice run, identify daily cohort | No claim that ID randomization prevents this | Authentication limits scored attempts, not outside knowledge |
| Query/compare errors | Guess internal IDs, receive revealing error text | Accept only public IDs owned by that run; generic failures | Rate limiting is a supplement, not the main defense |
| Observe latency/cache | One known prospect triggers different request pattern | Uniform DTO shape and bounded response behavior where feasible | No timing side-channel certification is claimed |

Per-run IDs must be generated from cryptographic randomness or a secret-keyed mapping, not an unkeyed hash of a name, PFR ID, or stable player key. A deterministic hash of a public identifier can be precomputed. A secret-keyed deterministic mapping is still linkable within its scope; the intended scope is one run. The public ID map must never be included in the response.

## Two modes, two disclosure policies

These are settings within the two existing modes, not additional game modes.

### Historical draft

Favor learning and historical context. Default name-hidden scouting can show source-backed college/position and available evidence with a clear recognition warning. If stronger identity masking is offered, describe which details are withheld. An explicit reveal should end any claim that the run measures blind decision quality. Save the disclosure-policy version and reveal events with the game.

### Daily challenge

Use one frozen disclosure policy for all participants. Names, colleges, exact dates/ages, provider IDs, player-specific URLs, exact measurement vectors, precise projection probabilities, retrospective outcome fields and deterministic alphabetical order must not appear in pre-draft client payloads. Generalized bands must be genuine ranges containing the observed value; do not invent measurements or change the player’s attributes.

The same pre-draft decisions remain available to all participants. Scouting can unlock genuinely useful coarse evidence while respecting the cumulative-disclosure budget. Do not count scouting points as proof of talent or of successful concealment. Publish the disclosure policy, information loss and residual recognition limitation alongside daily scoring.

## Executable audit to run before a release

1. Capture every actual API response for new/load/scout/compare/board/trade/advance/save/error and unfinished simulation flows in both modes.
2. Assert a strict property allowlist and no names, private IDs, provider slugs, player source URLs, exact future data or hidden precision where prohibited.
3. Assert public ID uniqueness within a run, different IDs across runs, stable IDs on save/reload, rejection of another run’s public IDs, and no client-visible mapping.
4. Check response order and public ID creation do not depend on name, actual draft order or future career values. Poison those fields and compare the public pre-draft behavior.
5. For each cumulative disclosure state, form equivalence classes under **the actual released fields**, including missingness, probabilities and every previously revealed field. Report fraction unique, minimum/median class size, and class-size distribution by position.
6. Run exact and tolerance-based matching against the publicly available candidate universe and document the matching rule, data date, false matches and uncovered candidates. Candidate-universe incompleteness means a small observed equivalence class is a diagnostic, not a population anonymity theorem.
7. Inspect compiled client assets, accessibility labels, links, analytics events, error logs, exports and notifications for identifiers. A visibly hidden name that ships in an aria-label or JSON is still disclosed.
8. Save the response fixture hashes, disclosure-policy version, dataset/model/engine versions, scripts and actual results. Do not label these checks passed merely because the design exists.

A k value computed on only the playable pool is a within-pool ambiguity measure. Do not market it as k-anonymity over all real prospects, search results, or an adversary’s background knowledge. Numerical uniqueness and human recognition are different outcomes.

## Executed within-source uniqueness audit

`python3 docs/identity_linkage_audit.py` evaluated the actual 336 documented combine participants in the current scenario and saved the dataset hash and results to `docs/identity_linkage_audit.json`.

| Released attributes | Records with a unique exact profile | Fraction |
|---|---:|---:|
| Position only | 1 / 336 | 0.3% |
| College + position | 265 / 336 | 78.9% |
| College + position + height + weight | 334 / 336 | 99.4% |
| Position + all eight exact combine measurements | 334 / 336 | 99.4% |

This measures uniqueness **within this source cohort**, with nulls treated as part of the matching pattern. It does not measure whether a human recognizes that player, how long recognition takes, or whether all eligible players are covered. An external table linking the same profile to a name makes exact matching feasible; no population percentage is borrowed from the cited privacy studies. The runtime grouped/sanitized response is a different object and requires its own cumulative-disclosure audit. A published minimum group size must be scoped to initial non-ID profiles, not advertised as protection against elimination, external information or collusion.

## Human recognition study — proposed, not executed

No human participants have been tested in this reconstruction. No recognition accuracy, search time, fairness improvement or expert-skill reduction has been measured. The following is a preregistrable study plan.

### Design

Recruit participants across prospect-history knowledge levels, measured with a separate baseline assessment and self-reported viewing/scouting experience. Randomize disclosure policy at the participant-profile level, stratifying by knowledge. Compare (A) name hidden, exact college/measurements; (B) college suppressed, genuine coarse measurement/projection bands; and (C) a more general position-specific percentile treatment. These are experimental display conditions, not product modes.

Use matched prospect blocks across positions, prominence and missingness. No participant sees the same player in multiple conditions, including via practice tasks; otherwise learning contaminates recognition. Counterbalance order, hold available browsing time and scouting budget constant, and separate memory-only and permitted-search tasks. Keep training examples out of the evaluation set. Analyze repeated participant and prospect observations rather than assuming every answer is independent.

### Primary outcomes

| Outcome | Definition | Analysis |
|---|---|---|
| Recognition accuracy | Correct free-text player identification at a prespecified time limit; audited aliases accepted | Difference in proportions with participant/prospect clustering or a crossed-effects logistic model |
| Time to correct identification | Time from profile disclosure to first correct identification; nonrecognition censored at limit | Survival/time-to-event analysis; also report recognized fraction at fixed times |
| Mean recognition time | Conditional mean among correctly recognized profiles, clearly labeled | Secondary descriptive value only; not a substitute for censored analysis |
| Confidence calibration | Stated probability that guessed identity is correct | Reliability plot and proper scoring rule, with sample uncertainty |
| Hindsight advantage | Association of identity recognition/history knowledge with draft selection after controlling for available pre-draft evidence | Prespecified analysis; observational mediation is not proof of mechanism |
| Decision-quality skill gap | Expert-minus-novice difference in a frozen pre-draft evaluation rubric under each disclosure policy | Interaction estimate with interval; do not use one simulated championship as quality |
| Usability/information cost | Task completion, errors, decision time and perceived usefulness | Prespecified comparisons and qualitative error review |

Sample size must follow a pilot variance/recognition estimate and a prespecified practically relevant difference; do not pick a convenient sample and retroactively declare adequate power. Multiple outcomes and subgroup analyses require a declared hierarchy and multiplicity treatment. Keep withdrawals, missing responses and exclusions in the report.

### Information-loss benchmark

Compare full permitted pre-draft predictors, generalized predictors, and suppressed predictors on identical chronological train/validation/test partitions. All normalization, bin thresholds and model selection must fit training data only. For five-year targets, labels must be complete by the applicable training cutoff. Evaluate target-appropriate held-out error, calibration, interval coverage, subgroup sample sizes and ranking quality. The current rookie-role target does not validate all draft skills or five-year talent.

Benchmark two distinct questions: (1) how much useful evidence users lose through display masking; (2) how much performance a model loses when restricted to the same displayed evidence. A hidden full-feature CPU model can still run if this is an explicit product rule, but its advantage must not be mistaken for fair symmetric information. Exact full-feature model outputs returned to users can undo the intended masking.

### Mode-specific interpretation

Historical-mode success may tolerate recognition in exchange for contextual learning. Daily-mode success requires a reduction in recognition advantage **and** acceptable decision usefulness. Do not set or claim an arbitrary universal anonymity threshold. Freeze practical acceptance thresholds before the confirmatory study; publish effect sizes, uncertainty, residual recognizability and subgroup results. If evidence cannot support competitive fairness, label the daily leaderboard a research/game ranking rather than a controlled blind scouting experiment.
