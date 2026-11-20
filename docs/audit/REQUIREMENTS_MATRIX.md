# REDRAFT 2.0 acceptance ledger

| Area | Disposition | Evidence and remaining acceptance criterion |
|---|---|---|
| Historical integrity | PARTIAL | Independent history-poisoning audit covers all nine draft boards. Obtain dated eligibility, ownership and roster snapshots to settle outstanding archive gaps. |
| Seven-round mechanics | PASS for tested matrix | See frozen gauntlet for all-team/year/seed results. |
| CPU drafting | PARTIAL | 108 drafts compared with recorded round-position shares and trade activity. Severe first-round QB underselection persists. Franchise strategy calibration needs league-wide evidence. |
| Trades | PARTIAL | Domain and API tests cover current selections. Future rights require ownership and settlement across years. |
| Player forecasts | PARTIAL | Measure empirical coverage, widths and errors on mature careers. Three exposure-sensitive subgroup gates improved on the reused cohort. |
| QB projections | FAIL | Upper-tail coverage remains below the declared criterion. Require time-ordered five-year improvement over a persistence baseline with credible tail support. |
| Scoring | FAIL | Four team scenarios share the same historical baseline. Require held-out scoring and shutout fit before adopting a replacement. |
| Future personnel | PARTIAL | Aggregate strength evolves. Individual future roster moves and rookie intake require coherent membership, eligibility, opportunity and roster turnover checks. |
| League rules | PARTIAL | Eight completed seasons provide observed playoff checks. Net touchdown tiebreaks, overtime and some schedule details remain approximate. |
| Alternate histories | PARTIAL | Paired worlds reconcile standings. The causal mapping from drafted talent to wins remains unsupported. |
| Daily challenge | PARTIAL | Server-side scoring, UTC rollover, ties and disclosure tested. Ranking sensitivity and real participant recognition remain open. |
| Mobile and UX | PARTIAL | Eight hosted engine/viewport selection, scouting and save/reload journeys passed. Both modes also completed the full 390px Chromium journey. See BROWSER_QA.md. A physical iPhone and novice usability study remain outstanding. |
| Accessibility | PARTIAL | Focus and reduced-motion checks cover part of the applicable criteria. Complete keyboard and screen-reader journeys remain open. |
| Security | PARTIAL | See SECURITY.md for 92 rows and residual risks. Hosted identity trust, retention, restore and operational controls require verification. |
| Performance | PARTIAL | Simulation timings apply to this host. Production p75 web vitals require representative traffic. |
| Engineering | PARTIAL | Version-pinned installation, tests, builds and local D1 checked. Hosted evidence belongs to the specific tested commit. |
| Delivery | PARTIAL | Review branch and draft PR. Production deployment needs a separate decision. |

## Priority after this review

1. Reconcile the 2021 invite and historical pick identity maps. Require dated or stable-ID evidence for each merge, audit school aliases and retain same-name different-person controls. Rebuild the baseline and repeat comparisons before attributing changes to user decisions.
2. Benchmark CPU choice against pre-draft positional value and opportunity. Require better first-round position distributions on chronologically held-out classes while retaining meaningful team and seed diversity.
3. Acquire dated older QB participation records or establish five-year predictive improvement over persistence on additional mature cohorts. Report coverage and interval width together.
4. Evaluate a discrete football scoring model on historical forecast origins. Require held-out team-score and margin performance and a league-wide shared-season test before promotion.
5. Model future personnel using immutable annual memberships and hypothetical draft identities. Verify roster conservation and test turnover distributions before showing individual future transactions.
6. Repeat the full lifecycle on physical iPhone Safari, then validate recovery, edge identity and load at staging before production review.
