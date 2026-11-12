# REDRAFT — project specification

The NFL draft time machine. Draft the past. Rewrite the future.

## Scope

Exactly two playable modes share the same domain engine: historical draft plus five-season simulation, and a UTC daily challenge. The user controls scouting, draft selections and draft-pick trades, not a separate franchise-management game. No fantasy, trivia, betting, on-field gameplay or extra playable modes.

The intended full product has historically accurate information sets, coherent league simulation, evaluated forecasts, secure daily scoring and responsive professional interaction. The current implementation is a **2018 research alpha**; the complete production acceptance gate is not claimed. `KNOWN_LIMITATIONS.md` records missing evidence and incomplete systems.

## Current reconstruction

The earlier transient checkout was unavailable when work resumed. This checkout is rebuilt and must earn fresh test/build/deployment evidence. Earlier reported test counts and timings are historical session notes, not proof of this code. Versions distinguish restored source from earlier variants. Source checkpoints and exact deployment commit linkage are required.

2018 is selected for accessible draft/combine/game coverage and a completed five-season historical window. It is a practical initial scope, not a scientific conclusion that the year is uniquely optimal. Gameplay includes 336 documented combine participants.39 non-combine historical draftees remain actual-baseline references only; they cannot enter user or CPU selections, scouting or board ranking. The incomplete eligible universe and baseline-pool mismatch remain material limitations.

## Identity and evidence

Name hiding is not anonymity: college, year, position, measurements, missingness and probabilities can identify prospects. Historical and daily disclosure policies must be explicit, frozen for scored challenges, and enforced in server response DTOs. Private canonical IDs and source identity maps never belong in pre-draft browser responses. See `docs/PROSPECT_IDENTITY.md` for primary literature, threat model and the proposed, unexecuted human recognition study.

Every displayed item is a historical fact, transformed observation, derived statistic, estimate, simulation outcome, assumption or unavailable item. No fake injuries, college production or forecasts. No retrospective draft position or career outcome enters pre-draft evaluation. A rookie participation probability is not a starter probability or five-year talent estimate.

## Experience contract

Random assignment is the default; supported team/year/seed controls are available. Drafting covers the real seven-round structure and current-pick transfers. Scouting improves disclosed information without changing talent. Saving is authoritative and durable. Results separate actual history, simulated actual-selection baseline and alternate selections, with paired uncertainty and explicit cohort-only star/award summaries. Daily attempts use the same engine, fixed configuration and server-derived scoring.

Reference windows are draft year through draft year+4. The actual present-day boundary must use runtime time and verified season completion; never invent future actuals. Daily rollover uses UTC. This 2018 window is entirely historical, so future-boundary behavior requires separate tests.
