# Prior-season team context

The **2026-11-04** reconstruction produces `data/clean/team_context_2018.json` from fresh downloads. It provides observed 2017 regular-season usage for the 2018 scenario. It does not establish the April 2018 roster, returning players, contracts, draft-day coaching staff, or schemes. Those fields remain null.

## What the source records establish

[nflverse roster documentation](https://nflreadr.nflverse.com/reference/load_rosters.html) describes a season-level roster dataset. Its [roster dictionary](https://raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_rosters.csv) defines `week` as the most recent week that season in which the player appeared on the roster. The 2017 file contains 3,082 rows, including active, cut, reserve, and practice-squad statuses. It is not a single dated roster snapshot. There are 1,860 missing PFR identifiers and 476 missing birth dates. Birth dates, headshots, and draft-result fields are not imported into this context artifact.

The [2017 snap release](https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2017.csv) supplies player participation recorded by Pro Football Reference and distributed by nflverse. Its regular-game IDs match all 256 completed games in the schedule release. This yields 512 team-game observations and 2,080 team/player observations, all before the draft cutoff. A player who changed teams can have a separate observation for each team; only that team's snaps enter its context.

The roster link uses exact PFR IDs when unique (1,091 team/player observations) or unique normalized names and matching teams (901). The other 88 remain unresolved. No fuzzy matching, guessed membership, or numerical identity-confidence probabilities are used. Missing roster matches do not remove the player's observed snaps. A PFR identity can link to another last-observed team after a transaction; the source team is preserved explicitly.

Prior head coaches are counted from the home/away coach fields in completed 2017 games. These are historical observations of who coached those games. They do not establish the coaching staff at the 2018 draft, and do not support a scheme inference.

## Depth-chart audit

The [loader documentation](https://nflreadr.nflverse.com/reference/load_depth_charts.html) advertises weekly depth charts back to 2001. The freshly downloaded 2017 file contains 36,620 rows, including 34,545 marked regular season, with all 32 teams represented. Its `formation` values are exclusively **Offense**, **Defense**, and **Special Teams**. These identify units, not schemes such as zone blocking, spread offense, or a 3–4 defense.

The current depth-chart dictionary describes a newer timestamp-based schema, while the 2017 snapshot has season/week fields. The older file also contains records marked `REG` in week 18, although the 2017 regular season had 17 weeks. These issues are retained in `team_context_quality.json`; depth charts are evidence of the source's limits and are not used to reconstruct April membership or to invent schemes.

## Metrics and their limits

Each team has nine broad groups: QB, RB, WR, TE, OL, DL, LB, DB, and ST. A team/player is assigned to its source position with the largest snap-weighted row total; position changes are not separately modeled. All source positions are classified, and unclassified scrimmage snaps equal zero.

- `totalScrimmageSnaps` sums offensive plus defensive **player-snaps**, not team plays.
- `players200Plus` counts team/player pairs with at least 200 such snaps. The threshold is a transparent descriptive convention, not a validated indicator of player quality or roster need.
- `positiveSnapPlayers` counts players with positive offensive or defensive snaps.
- `largestPlayerShare` divides the largest individual contribution by its group total. This measures concentration within the group, not player quality or the share of all team plays.
- `topContributors` lists four leading contributors per group. ST ranks by special-teams snaps; all other groups rank by scrimmage snaps.
- `totalKnownScrimmageSnaps` includes all classified groups. The ST group is excluded from CPU policy support. Within-unit utilization policies should normalize offense and defense separately, since defensive/offensive play volume can differ.

Low contributor counts may reflect healthy established starters. High counts may reflect rotation, injuries, or transactions. Neither statistic identifies a vacancy without dated roster and contract evidence. Any CPU utility adjustment using these observations remains a declared policy assumption requiring independent evaluation.

## Availability and rights

The information cutoff is `2018-04-26T23:59:00Z`. Usage observations end December 31, 2017. Linked annual-roster observations may refer to later weeks of the 2017 postseason; they retain their original week and game-type fields and are not presented as December 31 membership. The current releases lack original per-row publication timestamps, so this is retrospective reconstruction of historical observations rather than an immutable contemporary feature archive.

nflverse's [licensing declaration](https://github.com/nflverse#licensing), rechecked November 4, identifies its data releases except FTN as CC BY 4.0, with provider attribution and no warranty of upstream rights. Attribute nflverse and PFR for snaps; the roster dictionary attributes roster fields to NFL.com and birth dates to Sleeper (birth dates are not used here). No photographs, marks, or article prose are imported. Source files remain private; URLs, sizes, retrieval times, and SHA-256 digests are retained.

## Reproduction and verification

```bash
python research/team_context.py --download
python research/test_team_context.py
```

The pipeline uses the Python standard library. Without `--download`, it reuses the raw cache. The sidecar `data/clean/team_context_source_manifest.json` records `artifactSha256` for the exact JSON bytes plus source digests; it is regenerated after artifact writes so runtime model pinning can use the same digest.

Five tests passed on November 4 in 0.134 seconds: artifact/source hash integrity, team snap-total conservation, player contribution conservation across teams, unavailable draft-day facts, and correct interpretation of depth-chart units. The results are in `data/clean/team_context_test_output.txt`. These checks establish the specified data properties, not a complete historical roster or calibrated roster-need model.
