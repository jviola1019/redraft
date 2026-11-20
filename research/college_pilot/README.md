# College production feasibility pilot

**Status as of 2026-11-20.** CFBD authenticated coverage remains unmeasured. An independently sourced four-row game sample exercised the historical date and identity joins. No college features entered REDRAFT gameplay, draft eligibility or model training.

## Provider access

- The protected 2017 Oklahoma player season endpoint returned HTTP **401** in a real request. This workspace had no configured `CFBD_API_KEY`. The gated CLI also exits locally before a credentialed fetch when there is no key. [CFBD authentication](https://api.collegefootballdata.com/authentication) · [Status interpretation](https://api.collegefootballdata.com/usage-and-access)
- Provider terms effective August 12, 2026 permit private caching, historical analysis, model training, derived outputs and reasonable factual display within a larger product. They restrict redistribution of standalone or bulk API data, customer programmatic access to stored responses, and credential transfer. Downloadable data packs have their own included licenses. The pilot writes aggregate diagnostics only. [CFBD Terms of Use, sections 2 and 4–7](https://collegefootballdata.com/terms)
- The publicly listed cfbfastR-data player-stat and roster releases expressly derive from CFBD. The archive documentation reviewed did not provide an upstream grant authorizing this ingestion route. The provider catalog lists paid resources with included product-specific licenses. Neither route was used for the pilot. [cfbfastR-data provenance](https://github.com/sportsdataverse/cfbfastR-data) · [Provider pack catalog](https://radsportsanalytics.com/data-packs/)

## Independently sourced historical check

The Oklahoma athletics archive hosts the detailed final box score for Oklahoma–Kansas on November 18, 2017. The archive shows signs of later migration. AP coverage that day independently corroborates the yardage and touchdown portion of the sampled passing line. The other fields use the recorded event date as a reconstruction proxy. The parser reads selected numeric fields from the local PDF and emits only aggregates. [University game archive and participation report](https://soonersports.com/sports/2019/8/7/2138589) · [Official game PDF](https://s3.us-east-2.amazonaws.com/sidearm.nextgen.sites/soonersports.com/documents/2017/11/28/5462974.pdf?timestamp=20190624105857) · [Contemporaneous AP report](https://www.foxsports.com/stories/other/mayfield-snubbed-as-no-3-sooners-roll-41-3-win-over-kansas)

Four selected rows spanning QB, TE, RB/FB and EDGE each joined exactly one eligible 2018 prospect by name and school after manual abbreviation review. Official participation and roster records corroborate the Oklahoma fullback alias. Contemporary AP reporting identifies the Kansas edge player and school. The sample excludes unselected rows. Treat 4/4 as a pilot check on these joins independently of full cohort coverage. [Oklahoma roster](https://soonersports.com/sports/football/roster/dimitri-flowers/3318) · [Contemporaneous AP report](https://www.foxsports.com/stories/other/mayfield-snubbed-as-no-3-sooners-roll-41-3-win-over-kansas)

| Diagnostic | Result |
|---|---:|
| Selected rows with a unique eligible name-and-school join | 4 of 4 |
| Selected rows admitted by the scenario event-date gate | 4 of 4 |
| Selected rows admitted by the same-day cutoff control | 0 of 4 |
| Sampled prospects unique by exact position alone | 0 of 4 |
| Sampled prospects unique by position plus school | 4 of 4 |
| Sampled prospects unique by position plus individual sample profile | 4 of 4 |
| Whole eligible pool unique by position alone | 1 of 336 |
| Whole eligible pool unique by position plus school | 265 of 336 |

Sparse disclosure produces a presence fingerprint. All other prospects have absent sample profiles by construction, so the sample cannot estimate what class-wide historical production would disclose. These are exact matching counts, with human recognition and predictive usefulness still unmeasured. The scenario uses a reconstructed **2018-04-26 23:59 UTC** cutoff. The tested game falls well before that date. Original publication times for every numeric field remain unverified.

## Reproduce

From the repository root, use Python 3.11 or newer and Poppler's `pdftotext` for the public check.

```bash
curl -fL 'https://s3.us-east-2.amazonaws.com/sidearm.nextgen.sites/soonersports.com/documents/2017/11/28/5462974.pdf?timestamp=20190624105857' -o /tmp/redraft-ou-box.pdf
python3 research/college_pilot/pilot.py public-box --pdf /tmp/redraft-ou-box.pdf
python3 -m unittest discover -s research/college_pilot -p 'test_*.py' -v
```

Using an organization-authorized key already configured in the environment, run the probe followed by the three-endpoint pilot.

```bash
python3 research/college_pilot/pilot.py probe
python3 research/college_pilot/pilot.py cfbd --year 2017 --team Oklahoma --scenario-team Oklahoma
```

The CFBD pilot reads the prior season's schedule, roster and player game box scores in memory. The schedule gate uses regular or postseason game IDs and rejects unknown or incomplete kickoff records. It requires the cutoff UTC date to be at least two calendar dates after the game's UTC kickoff date. This is a conservative event-date heuristic with original publication unverified. Historical corrections can still have been applied later. Candidate linkage uses a unique normalized roster name and school to obtain a provisional provider athlete ID, then joins box scores through that ID and the gated game ID. Ambiguous links and conflicting duplicate values are quarantined. Transfers, name variants, missing games and potential roster collisions require manual review. Authenticated schemas and historical coverage still need a real authorized run. [Games and player box score schemas](https://api.collegefootballdata.com/api/games) · [Roster schema](https://api.collegefootballdata.com/api/teams) · [Provider coverage](https://api.collegefootballdata.com/data-availability)

College production should remain outside the blind policy until authenticated coverage, audited crosswalks, source-date quality and cumulative disclosure are measured across classes. Before considering adoption, test incremental held-out decision value by position with meaningful denominators and separately measure human recognition. The four-row case does not validate those uses.
