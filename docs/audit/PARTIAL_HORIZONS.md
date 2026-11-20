# QB follow-up, scouting and data access

November 20, 2026. The partial-career comparison used the previously frozen production and mature-donor methods. All evaluated NFL snap outcomes end with the 2025 regular season. The separate 2022 fifth-year forecast is a historical reconstruction locked before the completion of the 2026 season. Its eventual test will use both 2026-only and five-year cumulative outcomes.

| Draft origin | Forecasts | Verified identities scored | Completed horizons |
|---|---:|---:|---:|
| 2022 | 15 | 13 | 4 |
| 2023 | 15 | 15 | 3 |
| 2024 | 14 | 14 | 2 |
| 2025 | 15 | 15 | 1 |

**Decision:** keep the current gameplay model. The expanded donor pool improved second-season forecasts. Compared with production, snap CRPS fell 21.44 (95% conditional bootstrap interval 5.19 to 38.85 in the direction of improvement). At four years, cumulative games CRPS worsened by 0.248 (interval 0.046 to 0.487) in 13 verified 2022 QBs. Two unresolved identities appear only in a separate 59-player sensitivity analysis. It reached the same directional conclusion. The four-year snaps interval covered one additional player while its mean width increased from 2,018 to 4,234 snaps. Existing cohorts have informed earlier research. A player bootstrap conditions on these cohorts and forecasts.

[Protocol, metrics and plots](../../analytics/qb_partial/REPORT.md) · [Frozen 2022 distribution](../../analytics/qb_partial/prospective_2022.json) · [SHA-256 receipt](../../analytics/qb_partial/forecast.sha256)

## Studies completed

| Question | Result | Evidence |
|---|---|---|
| Is the 2012 snap history recoverable? | A public archive covered all 256 regular games and 512 team-games. Three sampled 2012 entries matched official gamebooks. Fourteen of the 19 combine QBs had existing IDs. Rookie-season participation was recorded for nine of those 14. Full prospect coverage, complete trajectories and permission for public reuse are outstanding. | [Audit](../../research/snap_access/README.md) · [Specification](../../research/snap_access/DATA_SPEC.md) · [Unsent licensing requests](../../research/snap_access/REQUESTS.md) |
| Can college statistics be joined and safely displayed? | The unauthenticated CFBD request returned HTTP 401. The gated pilot accepts a locally configured key and emits aggregate diagnostics. A separate real Oklahoma–Kansas 2017 box-score sample linked four players. All four were distinguishable by school and position in the sampled records. This pilot does not establish general model lift or recognition by humans. | [Verified pilot and instructions](../../research/college_pilot/README.md) |
| Does college change recognition or scouting choices? | A volunteer study is ready to administer using two counterbalanced forms. Both use the same 16 prospects and production group measurements. Identity answers are separate from the participant forms. No volunteer responses have been collected. | [Download facilitator kit](../../research/recognition_trial/facilitator-kit.zip) · [Protocol](../../research/recognition_trial/PROTOCOL.md) |
| Does aggressive trading dominate the game? | Fixed trade-up and trade-down policies each executed one legal deal in all six isolated challenges. Against no user trade, up averaged −7.00 rubric points and −1.158 simulated wins over five years; down averaged +1.83 points and +0.406 wins. The down-policy win difference changed sign in two dates' half-ensemble checks. The policies selected different trade targets and distances. | [Study and official route tests](../../analytics/trade_daily/README.md) |
| Do sequential scoring distributions fit better? | Conditioning drive points on score differential and clock worsened joint energy loss in both chronological windows over 1,280 games. Team-season scoring dispersion rose 11.2% and 8.3%. This candidate used historical clock/possession templates. | [State-dependent scoring experiment](../../analytics/scoring_game_state/REPORT.md) |
| Can clock and score predict remaining possessions? | Across 1,248 held-out games, adding the current score to clock time improved game-weighted mean squared error by 0.01203 in the later window but worsened it by 0.00080 in the early window. The effect did not satisfy both-window replication. | [Pace study](../../analytics/scoring_pace/REPORT.md) |
| Can a specialist outcome be tested? | For 4,010 field-goal attempts, adding a historical kicker effect to the distance model improved log loss from 0.373507 to 0.372782, with the paired interval spanning zero. The target measures success conditional on attempting the kick. | [Kicker pilot](../../analytics/kicker_pilot/README.md) |
| Is an older QB opportunity target feasible? | Five-year NFL pass attempts for 92 linked drafted QBs could be scored chronologically. Grouping already-drafted QBs by draft round improved average CRPS from 465.37 to 316.84. Coverage of the nominal 80% interval fell to 73.91%. All 18 missing links came from rounds 3–7. The actual draft round is post-selection information. | [Post-draft attempts benchmark](../../analytics/qb_attempts/README.md) |

## Verification and release scope

An independent reviewer rebuilt all four QB forecast/score outputs byte for byte and recomputed every scored player-level CRPS directly. The reviewer reproduced the real college and 2012 archive receipts. Sampled source matches do not certify every historical measurement. The formal statistical ledger remains 40 passing, six failing, seven unsupported, zero stale. All 96 domain tests passed locally. Human-response collection, provider authentication, and grant of data rights are external dependencies. No credentials, PBP archives, source college box scores, or third-party snap rows are distributed by this study.
