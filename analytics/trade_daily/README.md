# Daily trade policy audit

Both scripted policies found and executed a legal offer on **6 of 6** frozen Daily fixtures. Compared with keeping the original picks, trading up lowered the decision score and mean simulated five-year wins on every fixture. Trading down raised both metrics on five fixtures each, with the sixth result differing by metric.

## Offer feasibility

The two searches used the same blind probability board and scouting allocation as the no-user-trade control. The trade-up policy chose the largest eligible move before the first selection. The trade-down policy chose the smallest eligible move when the user was first on the clock. Each executed at most one trade. The CPU trade process ran in all three arms. See the [frozen protocol](PROTOCOL.md) for the 32-position window, package constraints and 1.35 ratio cap.

| Policy | Structural packages | Within ratio cap | Accepted within cap | Declined within cap | Dates with a qualifying offer |
| --- | ---: | ---: | ---: | ---: | ---: |
| Trade up | 2,872 | 2,794 | 291 | 2,503 | 6/6 |
| Trade down | 4,913 | 2,819 | 1,081 | 1,738 | 6/6 |

The package counts describe the enumerated offers. Many share assets, and they are evaluated individually from the same state on a given date. Among the 4,241 declined quotes within the cap, the engine offered a counter for 2,787 and cited insufficient available compensation for 1,454. The strategies kept their original package constraints and did not accept off-policy counters.

Twelve local integration checks exercised the authoritative Daily POST handler with the frozen dates and a migrated SQLite database. Each checked that quoting left the saved state unchanged, a representative declined commit returned HTTP 400 without mutating the draft, and the chosen offer committed with the expected revision, pick ownership, selection history and ledger. The audit separately checked pick conservation and historical baseline integrity.

## Score and simulated wins

Score and win changes below are relative to the no-user-trade arm. Wins compare alternate five-season totals on the same 256 replica indices. The table gives their paired mean and the empirical 10th–90th percentile range of individual path differences.

| UTC date / team / draft | Control score | Up: slots | Up: score change | Up: wins [p10, p90] | Down: slots | Down: score change | Down: wins [p10, p90] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Nov 1 / CIN / 2026 | 57 | 17 | −11 | −1.949 [−6, 2] | 4 | +2 | +0.641 [−2, 3] |
| Nov 2 / KC / 2020 | 53 | 12 | −5 | −1.070 [−4.5, 2] | 8 | +1 | +0.500 [−2, 3] |
| Nov 3 / DEN / 2025 | 62 | 10 | −9 | −1.496 [−6, 2] | 2 | +1 | −0.129 [−3, 3] |
| Nov 4 / CLE / 2025 | 70 | 1 | −4 | −0.594 [−3.5, 2] | 1 | +3 | +1.078 [−2, 4] |
| Nov 5 / DET / 2025 | 56 | 11 | −6 | −1.309 [−5, 2] | 2 | 0 | +0.035 [−3, 3] |
| Nov 6 / HOU / 2021 | 68 | 9 | −7 | −0.527 [−4, 3] | 4 | +4 | +0.309 [−2, 3] |
| Six-date mean | 61 | — | **−7.000** | **−1.158** | — | **+1.833** | **+0.406** |

Trading down tied the score in DET and lowered mean wins in DEN. The result across all dates equals the result across executed trades because every fixture supported both policies.

| Score component | Up: mean weighted point difference | Down: mean weighted point difference |
| --- | ---: | ---: |
| Projected class value | −4.81 | +2.08 |
| Draft-class balance | +0.83 | −0.22 |
| Trade capital | −1.03 | −0.69 |
| Paired five-year difference | −2.03 | +0.71 |
| Scouting coverage | 0.00 | 0.00 |

Component contributions precede rounding. The runtime accepts offers only above chart parity, so either direction costs capital under the same chart used by the rubric. Projected class value sums rookie-role probabilities. Gaining or losing selections can therefore move the score through volume alone. The policies also differ in aggressiveness. The up policy moved 1–17 slots and the down policy moved 1–8.

All up effects kept their negative score and win signs in both 128-draw halves. Down's mean win sign differed across halves for DEN and DET. DEN's decision-score gain was a tie in the first half. Every policy-date path range crossed zero, and per-date simulation standard errors for the paired mean ranged from 0.126 to 0.210 wins. These describe uncertainty conditional on the simulator and the fixed drafts. The dates come from one six-day local frame and include three teams in the 2025 class. The package rules, board, heuristic acceptance premium, CPU reactions and model of five-year development all constrain the result.

## Reproduce

Run from the repository root with Node.js 24 and installed dependencies.

```sh
node analytics/trade_daily/audit.mjs --markets-only
node analytics/trade_daily/audit.mjs
node --test analytics/trade_daily/*.test.mjs
```

[feasibility.json](feasibility.json) contains offer counts, reason totals and example quotes. [results.json](results.json) records the paired path differences, score components, draft selections by slot, half checks and input hashes. The test suite passed all 15 checks.
