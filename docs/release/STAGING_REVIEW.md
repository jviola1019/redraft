# REDRAFT staging review | November 20, 2026

This build adds a veteran playing-time outlook to each of the nine draft classes and 32 franchise snapshots per class. Its original regression uses prior snaps and position. The estimate concerns the following regular season across the whole NFL. The display identifies the prior team and separates the observed contributor count from the expected future count. A projected 12.6 of 21 for Cleveland entering 2025 includes veterans who may reach the threshold with another team.

## EA research and staging decision

The official Madden ratings page and dated nflscraPy releases were examined. The 2024 pre-draft matched veteran sample had 1,689 players. Adding the archived overall rating improved next-season 500-snap Brier loss from 0.16547 to 0.15271. This result applies to matched veteran participation only. A supported EA bulk API, redistribution grant, and EA's internal progression formula were not verified. Raw EA ratings are excluded from the source and staging build. [Archive study](../../analytics/veteran_ratings/REPORT.md)

The EA-free staging regression was assessed across eight chronological seasons and 15,444 player-seasons. The curved trajectory model scored 0.14174 Brier versus 0.14280 for a flexible last-season usage baseline; the initial straight-line trajectory scored 0.14582. The flexible comparison followed review of the original results and uses already examined holdouts. Staging presents an exploratory informational outlook. It has no effect on draft decisions, official scoring or the five-year simulation. Missing age or membership is never inferred from a rating. [Model, subgroup results and caveats](../../analytics/workload_regression/README.md)

## Historical and design changes

- Official sources establish 32 compensatory slots for 2019 and 37 for 2021. A verified sidecar classifies the slots in the loaded scenarios and preserves their flags through trades. The 2020 setup still uses the April 15 order. Its coverage notes identify the April 21 picks 139/241 transaction before the April 23 draft opening. An opening-day reconstruction requires a separate scenario/version. [Historical evidence](../../data/clean/historical_compensatory_slots.json)
- Cleveland's 2025 team snapshot links eight dated personnel and coaching facts and separates roster moves, expected availability, observed participation and reported strategy. The snapshot does not establish all team rosters, contracts or scheme assignments. [Personnel research](../../research/PRE_DRAFT_PERSONNEL_2025_CLEVELAND.md)
- The landing, setup and draft-room screens share original pixel stadium artwork with current pick and trade feedback. The novice board distinguishes research from selection, and reduced-motion preferences are respected.
- The draft-class results allow inspection of a selected player's five modeled seasons, including games, starts, start share and contribution. The view identifies the detailed simulation replicate. Missing measurements are preserved. Daily player-specific trajectories unlock only after reveal.
- Staging uses a separate private Site and database from the existing live game. The portable source checkout continues to identify the existing live Site. Dated research reports and saved versions refer to their own source hashes.
