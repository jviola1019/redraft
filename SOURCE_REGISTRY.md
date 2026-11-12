# Source registry

The substantive registry is [research/SOURCE_REGISTRY.md](research/SOURCE_REGISTRY.md), verified **2026-11-02 UTC**. It records source URLs, publisher lineage, fields and units, access requirements, historical-availability limitations, license observations, and dataset dispositions.

Machine-readable downloaded-input provenance: [data/clean/source_manifest.json](data/clean/source_manifest.json). Feasibility and release coverage: [research/FEASIBILITY.md](research/FEASIBILITY.md), [data/clean/coverage_matrix.json](data/clean/coverage_matrix.json). All raw snapshots remain private and gitignored.

Attribution: NFL data transformed from nflverse releases, with underlying combine/draft/snap records attributed to Pro Football Reference and schedule lineage to Lee Sharpe/nfldata. The nflverse release license statement identifies **CC BY 4.0**, excluding FTN; no FTN data is used. See [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and the linked registry for upstream rights qualifications. Official NFL/team pages support factual ownership, eligibility, and chart verification. No NFL affiliation, logo, photograph, or article license is implied.

## November 12 supplemental rule and tooling references
| Source | Use | Coverage / access | Rights and limitations |
|---|---|---|---|
| NFL, https://www.nfl.com/standings/tie-breaking-procedures | Ordered playoff and schedule tiebreak criteria | Current official reference, checked 2026-11-12; unauthenticated HTML | Referenced rules; no copied media. Current wording is not an archived annual snapshot. |
| NFL Football Operations, https://operations.nfl.com/media/4414/2020-nfl-record-and-fact-book-1.pdf | 2020 playoff expansion, byes and reseeding | Official PDF; checked 2026-11-12 | Reference only; PDF is not bundled. |
| NFL Football Operations, https://operations.nfl.com/calendar-events/nfl-schedule/making-the-schedule | Standings-dependent opponent generation | Current official HTML; checked 2026-11-12 | Rotation/week/home approximations remain disclosed. |
| Playwright, https://playwright.dev/docs/emulation and https://playwright.dev/docs/browsers | Browser/device test design | Official documentation; checked 2026-11-12 | Emulation does not establish physical-device behavior. |

Older quarterback player-stat access and unresolved rights are recorded in analytics/qb_legacy_source_feasibility_REPORT.md. No unacquired older observation is part of a model.
