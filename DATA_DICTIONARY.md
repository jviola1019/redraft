# Data dictionary

`lib/types.ts` is the current domain contract. The browser response contract must be separately whitelisted because the internal `Prospect` includes a real name and canonical ID. Do not spread the internal object into a masked response.

| Entity / field group | Meaning | Units and constraints |
|---|---|---|
| Team | canonical franchise ID, historical display identity, conference/division | stable IDs; names follow time where explicitly implemented |
| Prior team record | prior wins/losses/ties and points for/against | observed season facts; not an exact pre-draft roster |
| Prospect | canonical ID, name, position, college, eligibility evidence |336 combine participants playable;39 later-identified non-combine draftees baseline-only |
| Measurements | height, weight, forty, bench, vertical/broad jump, cone, shuttle | inches, pounds, seconds, repetitions; null never implies zero |
| `availableBy` | reconstructed upper availability bound | not proof of original per-field publication timestamp |
| Projection | roleProbability, supported/fallback, target, modelVersion, uncertainty |200+ rookie snaps; null for unsupported specialist target; no invented individual confidence interval |
| DraftPick | overall, round, owner, compensatory flag | real selection inventory; branch ownership after trades |
| Selection | overall, round, team, prospectId | one prospect per run, valid available pick owner |
| Trade | from/to, give/receive, atPick, CPU flag | current available selection assets; not later player trades |
| Scouting | scouted IDs, point balance, ranked board | reveals information; never changes actual talent |
| GameState | run/mode/team/year/seed/status/revision and versions | server authoritative; public response removes hidden seed/mappings |
| Simulation game | home/away, season/week/type, scores | generated outcome; determines records and points totals |
| Player season | contribution, games, starts, team | modeled contribution is not official AV or a box-score statistic |
| Comparison | mean/median delta, interval, improvement share, MCSE, sample count | paired alternate-minus-baseline; conditional simulation variability |
| Score component | value, weight, explanation | transparent game rubric; not established real GM ability |
| Public prospect ID | random opaque identifier scoped to run | no unkeyed canonical/name hash; stable only within saved run |
| Disclosure version | allowed/coarsened/suppressed field rules | immutable for scored daily attempts |

## Normalized analytical families

Governance: data_sources, source_documents, dataset_versions, data_quality_issues, fact_provenance. Identity/time: teams, team_identities, seasons, team_seasons, players, player_identifiers, colleges. College: college_player_seasons, college_statistics. Draft/history: draft_classes, prospects, historical_draft_picks, draft_pick_ownership, historical_trades, trade_assets, combine_results, injury_events, scouting_reports, roster_memberships, contracts, coaching_staff. Outcomes: historical_games, historical_player_seasons, historical_team_seasons. Modeling: feature_definitions, feature_values, model_versions, model_predictions. Gameplay exports: users, game_runs, game_pick_assets, game_draft_picks, game_trades, game_trade_assets, game_scouting_actions, game_saves. Disclosure: disclosure_policies, game_public_prospect_ids, game_reveal_events. Simulation: simulation_runs, simulation_games, simulation_player_seasons, simulation_team_seasons, historical_comparisons. Daily: daily_challenges, daily_attempts, daily_leaderboard_entries.

No achievements table exists without a defined feature. The target schema’s existence is not a claim that missing college/injury/contract facts have been acquired.

## Time, missingness and lineage

Instants are ISO 8601 UTC; dates alone must not be promoted to invented exact times. Validity is `[valid_from,valid_to)` with null end open. Missing reasons distinguish unknown, not applicable, not measured, not reported, source unavailable, failed ingestion and incomplete season. Every real numeric zero remains a value. Identity reconciliation uses exact or audited manual rules; no unreviewed fuzzy match.

Generalized display bands contain the true observed value. Suppression is labeled as withheld/unavailable and does not fabricate a measurement. Missingness itself may identify an athlete, so daily disclosure audits use cumulative visible fields including absence patterns.
