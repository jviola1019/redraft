# Measured performance

The immutable November 20 UTC run used Linux x64, Node 24.22.3, an AMD EPYC 9V74 and nine visible logical CPUs. Results reflect local execution under the available shared-host load. Raw timings and hashes are in runs/verified-report.json and the accompanying ZIP.

| Workload | Result | Interpretation |
|---|---|---|
| Cleveland 2018, 256 paired five-season replicates | 11.42 seconds of simulation, 44.59 ms per pair on average | Simulation compute only. Excludes Worker invocations, state transport and D1 persistence. |
| 96 cases in the 2018 draft class across all 32 franchises | Median 324 ms, empirical 95th percentile 606 ms per case | Fixed three seeds per franchise. Includes draft, paired replicates and scheduled replay checks. |
| Full authoritative API integration | 455 requests, maximum serialized response 1,953,102 bytes | Large result payloads remain a mobile transport cost. |
| Expanded hosted selection/scouting/reload journeys | All eight engine/viewport combinations passed. Local reload load-event timings ranged from 92 to 258 ms. | Measured on Actions against the hosted runner's loopback development server. No physical iPhone or network profile. |

Cold production LCP, field INP, CLS, production load capacity and deployment p75 are unmeasured. Prioritize measuring result payload and simulation persistence time on staging before promising a faster end-to-end experience.
