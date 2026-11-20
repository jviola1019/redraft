# Historical snap extract specification

## Scope

Supply the 2011 and 2012 NFL regular seasons, with 256 completed games in each. Include one 2013 validation sample drawn from several games and teams, with a one-snap quarterback, a backup with zero snaps, a special-teams-only participant and a player with recorded counts in all three phases. The December 1, 2013 Titans–Colts game is the fixed overlap control. A 2012-only response is independently useful. Draft or roster position alone cannot define the player filter. The lower-volume option follows the 2011 and 2012 combine identities across every roster, including play at other positions. The project records 18 and 19 combine quarterbacks respectively, with seven unresolved identifiers across both classes.

## Delivery

Use UTF-8 CSVs with headers or equivalent typed Parquet tables. Deliver a schema, source/version/revision metadata, data provenance, coverage exceptions and the applicable written usage grant with the extract or sample.

| Table and key | Fields |
| --- | --- |
| `games` keyed by provider game ID | `season`, `season_type`, `week`, `game_date`, `provider_game_id`, `gsis_game_id` or `pfr_game_id` where available, `away_franchise`, `home_franchise`, `game_status`, `participation_coverage`, `source_record_id` |
| `player_games` keyed by provider game ID, provider player ID and team | `provider_game_id`, `provider_player_id`, `team_on_date`, `game_position` where recorded, `participation_status`, `offense_snaps`, `defense_snaps`, `special_teams_snaps`, `source_record_id` |
| `player_ids` keyed by provider player ID | `provider_player_id`, `player_name`, `name_aliases` where available, `pfr_player_id` or `gsis_player_id` if licensed, `college` and `draft_year` or other available public identity keys |
| `roster_membership` keyed by provider player ID, team and effective interval if nonparticipants are omitted | `provider_player_id`, `team`, `start_date`, `end_date`, `roster_status`, `source_record_id` |
| `sources` keyed by source record ID | `source_record_id`, `origin`, `source_locator`, `source_version`, `source_published_at` or earliest known availability, `source_corrected_at` where known, `extract_generated_at` |

Snap counts are nonnegative integers. Supply phase assignment and counting rules for nullified plays, penalties, tries, kneels, overtime and other provider-specific exceptions. Explain whether phase columns left blank on a present player row mean zero. Use null when the source did not measure a phase. A season sum, game box-score plays, starting status and rounded participation percentages cannot recover the required counts.

`participation_coverage` distinguishes complete, partial and unavailable frames per game. Supply or document how to derive these player dispositions with supporting evidence.

| Disposition | Interpretation |
| --- | --- |
| `played` | One or more verified positive counts across the three phases. Each phase must be known to compute both targets. |
| `active_dnp` | Explicitly active and did not play, or an equivalent confirmed zero supported by documented complete roster and participation coverage. |
| `inactive` | Explicitly inactive for the team-game. |
| `not_rostered` | Identity resolved and exhaustive dated roster/transaction evidence excludes the player for the team-game or league window. |
| `unknown` | Coverage, identity, roster disposition or phase counts are unresolved. Counts stay null where unavailable. |

A positive-only extract can establish observed participation. For zero or absence conclusions, supply a separate authoritative roster/game-status source or document why an exhaustive, verified feed includes the entire relevant participation universe, with identified exceptions. Track split-team seasons through team-game records. Bench quarterbacks with no credited statistical action can still have positive counts.

## Acceptance

1. Record the authorized dataset/version and retained copy digest. Record permitted access, internal storage, reproducibility, training, aggregate reporting and public simulator deployment. Confirm whether trained weights, calibrated tables and narrow sample figures can be distributed, along with any attribution, deletion, or renewal requirements. Raw data can stay private.
2. Match all completed REG game IDs and both period-correct franchises to the project schedule. Validate unique keys, game date, membership of the game teams, allowed statuses and integer phases. Exclude postseason, preseason and byes.
3. For each relevant combine identity, map IDs deterministically and audit missing or conflicting IDs using independently documented aliases and bio details. Preserve sources and time windows for both positive participation and confirmed nonparticipation. Exclude an athlete’s unresolved window from complete-target counts.
4. Compare the provider’s 2013 sample to project nflverse rows and to official NFL books. Check all three phases, both teams, full and partial participation, zero/did-not-play, and special-teams-only cases. Record disagreement and decide whether the sources are definitionally compatible before mixing cohorts. The six-player fixed control is a smoke test and has no league-wide implications.
5. Reconstruct the exact target for seasons 2011–2015 and 2012–2016. Sum `offense_snaps + defense_snaps` over eligible REG player-games. Separately count distinct REG games in which any phase is positive, including special-teams-only appearances. One unresolved game or phase can invalidate a complete label. Record whether the source version and corrections can support the historical forecast cutoff. Only validated complete donors may enter a rerun of the strict 2018 model.
