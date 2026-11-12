# Older QB data source feasibility

Checked 2026-11-12 after the strict QB uncertainty experiment. This is a source and identifier feasibility review; it does not add older observations to the forecast or supersede `qb_uncertainty_REPORT.md`.

## Feasibility

The official nflreadr loader supports regular-season player summaries and its current source code constructs `stats_player_reg_YEAR.csv` URLs for seasons starting in 1999. The documented player stat schema includes passing attempts, completions, yards, touchdowns, interceptions and sacks, keyed by a GSIS `player_id`. The nflverse player registry documents GSIS as its primary key and contains PFR IDs and draft information. Those fields provide a plausible join for QB-only historical usage/production trajectories.

The recovered [combine source](../data/raw/combine.csv) contains 154 QB rows for draft cohorts 2000–2013. 142 have PFR IDs; 12 do not. Actual stats-to-player join coverage remains unknown. If 1999–2013 release files exist and the identifiers resolve, the 2000–2013 combine classes could contribute up to 14 strictly completed five-season QB cohorts before the 2018 cutoff. For 2013 prospects, outcome seasons end in 2017. This could address the *number of QB histories* available for an additional QB-specific model.

This source does not supply the missing old snap vectors. Passing attempts and yards are a different target from scrimmage snaps and games. A future experiment must report a separate QB passing volume/production distribution; it must not put passing attempts or yards into snap totals, infer starts from attempts, or use them as a synthetic extension of the existing donor vectors. A joint snap/passing model would need direct same-player overlap years and separate calibration.

## Acquisition and rights

The historical CSV asset URL follows the loader's official URL template. An attempt to retrieve the 2013 asset timed out in the local environment, and the web retrieval service rejected direct GitHub release-asset requests. No older file was acquired, so there are no source-data hashes, row counts, or empirical join-coverage claims for these stats.

The `nflverse-data` repository has a CC BY 4.0 license file. However, nflreadr's published terms also say NFL data accessed by the package belong to their respective owners and are governed by those owners' terms. The available pages do not resolve a stats-player-specific downstream redistribution grant for NFL-derived historical records. Do not bundle the stats CSVs until source-specific redistribution rights and required attribution are confirmed.

## Local candidate cohort counts

| Draft cohort range | Combine QB rows | PFR ID present | PFR ID missing |
|---|---:|---:|---:|
| 2000–2013 | 154 | 142 | 12 |

Input SHA-256 for `data/raw/combine.csv`: `5648886b1bb9de8a0c42b05ee7b1d9cbe58897676caaa2f6a4a3d3c9228235bb`.

## Source references

- [nflreadr `load_player_stats` reference](https://nflreadr.nflverse.com/reference/load_player_stats.html) documents the regular-season summary option and stats contract.
- [nflreadr `load_stats.R`](https://github.com/nflverse/nflreadr/blob/main/R/load_stats.R) enforces season >=1999 and constructs the `stats_player_reg_YEAR` URL.
- [Player stats dictionary](https://nflreadr.nflverse.com/articles/dictionary_player_stats.html) defines `player_id` as GSIS and documents attempts/yards/touchdowns fields.
- [Player registry reference](https://nflreadr.nflverse.com/reference/load_players.html) describes the GSIS-primary crosswalk and PFR/draft fields.
- [nflverse-data license file](https://github.com/nflverse/nflverse-data/blob/main/LICENSE.md) states CC BY 4.0 for repository material.
- [nflreadr terms](https://nflreadr.nflverse.com/) state that NFL data are governed by their respective owners' terms.

The machine-readable findings, attempted URL, acquisition status, local candidate cohort count and rights caveat are in `qb_legacy_source_feasibility.json`.
