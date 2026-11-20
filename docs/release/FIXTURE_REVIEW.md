# Fixture validation and Pages release

The Jekyll project is the public entry to REDRAFT. It links to the existing access-controlled game and an installable review archive. Pages serves two allowlisted files. The signed-in game API, stored drafts and authoritative Daily leaderboard run on the existing application host. A Pages deployment does not deploy the review branch to that host.

[Public entry](https://jviola1019.github.io/redraft/) · [Application host](https://redraft-time-machine.daddyjoev.chatgpt.site) · [Validation plan and independent reviewer prompt](../audit/FIXTURE_PLAN.md)

## Repairs

| Finding | Change | Evidence |
|---|---|---|
| The earlier site served repository contents from the Pages origin | Build from a dedicated Jekyll directory and verify the publication artifact before upload | The first repaired deployment contained index.html and site.css only. Former project/data paths returned 404. [Deployment](https://github.com/jviola1019/redraft/actions/runs/44664669216) |
| Passing summary counts could mask a receipt with zero case rows | Verify the named release classes, all expected franchises and seeds, distinct world hashes, two replicate indices, required replays, totals and source/version pins | All nine previous genuine receipts passed the validator. Negative fixtures for missing and duplicated cases, stale versions, drift and malformed hashes were rejected. |
| CPU teams almost never selected first-round QBs | Use an empirical pre-2018 round-position adjustment and within-position role estimates for new runs. Compatible existing runs keep their previous CPU behavior. | First-round QB picks rose from 1 to 72 in 108 paired drafts. The nine observed drafts had 31 in total, equivalent to 372 across twelve repeats. First-round position fit improved in all nine classes, while early-class team allocation worsened within the declared bounds. [Candidate, criteria and exceptions](../audit/cpu_team_prior/REPORT.md) |
| A single score concealed rubric sensitivity | Show the stored official result and the range when each weight is independently halved or increased by half and normalized | The reference score of 53 ranged from 50 to 55. Legacy runs with insufficient components display the saved score and no invented range. Official scoring and saved leaderboard results are preserved. |
| QB intervals undercovered on 2018 outcomes | Ran a new model against the frozen baseline and earlier chronological comparisons | The candidate covered 16/16 after widening the games interval across the full schedule. Its proper-score comparisons did not establish an improvement. [Decision](../../analytics/qb_rank_hindcast_REPORT.md) |
| Scoring and shutout distributions diverged | Evaluated discrete score recalibration while retaining shared team-season dependence | Held-out shutout Brier worsened from 0.026638 to 0.026765. The replacement failed its adoption criterion. [Decision](../../analytics/score_marginal_REPORT.md) |

## Reproduction

Run the following from an installed review checkout with the raw historical inputs available as documented in SOURCE_REGISTRY.md.

```sh
node tests/run.mjs
node scripts/gauntlet.mjs --label fixture-verification
python analytics/test_qb_rank_hindcast.py
python analytics/test_score_marginal.py
```

The gauntlet writes its full manifest and logs before returning exit 2 for failed statistical criteria. Keep that exit visible when running the research checks. GitHub Actions separately exercises the software build, API and browser journeys.

## Integrated release receipt

Runtime revision [ba16c45](https://github.com/jviola1019/redraft/commit/ba16c452ca60a584f4b0e3df0fa755b5aa848710) matches local source 54dc227. The 22-step run passed all structural checks with zero source drift. Nine classes contributed 864 full drafts, 1,728 paired simulations and 288 deterministic replay checks. The API passed 17 cases across 462 requests. Recomputing all 960 playoff forecasts reproduced every probability and outcome from the prior historical-baseline evaluation. Statistical release remains blocked. The score-weight sensitivity check measured 2 leader-set changes and a minimum rank correlation of 0.333 under the current CPU policy.

A research fixture initially rejected the combined checkout because its recorded source digest described the old engine. Rerunning its complete experiment regenerated the provenance record. The saved predictions matched byte-for-byte and all three regression tests passed. The four discrete score recalibration fixtures also passed. No scientific tolerance changed.

[Complete zipped run, logs and per-class receipts](../audit/runs/2026-11-20T03-03-11-858Z-fixture-release-1456faa2.zip) · [Hosted build and browser journeys](https://github.com/jviola1019/redraft/actions/runs/44665229630) · [Statistical gate ledger](../../analytics/STATISTICAL_GATES.md)
