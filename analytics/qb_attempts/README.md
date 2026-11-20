# Five-year NFL passing attempts for drafted quarterbacks

Grouping by official draft round improved mean CRPS from 465.37 to 316.84 attempts over 92 linked quarterbacks drafted in 2011–2018. The paired difference was −148.53 attempts, with a conditional 95% interval of [−218.98, −80.55]. All eight origin years improved, passing the frozen post-draft research gate.

| Metric | Pooled drafted QBs | Draft-round groups |
| --- | ---: | ---: |
| CRPS, lower is better | 465.37 | 316.84 |
| Mean absolute error of forecast median | 650.02 | 433.61 |
| 80% interval coverage | 80.43% | 73.91% |
| Outcomes outside empirical support | 5 | 13 |

For the 2018 origin, 13 quarterbacks were linked. Donor five-year labels ended by 2017. CRPS improved by 277.54 attempts for that cohort. The forecast origin is after official picks are known. The round signal can reflect team investment and resulting opportunity, along with player selection. The data support a workload benchmark among linked drafted QBs. A blind forecast or an inference about football ability would require a different design and sample. The candidate's more frequent misses outside its historical support also limit its usefulness as a standalone predictive distribution.

We verified every 2001–2022 season against completed regular-season schedule game IDs. Passing attempts are credited play-by-play events, excluding sacks and conversion plays. All 2011–2022 seasons had zero unattributed eligible attempts. Eighteen of the 92 linked evaluations recorded zero attempts. One 2014 evaluation identity and 17 earlier identities lacked a usable link and were excluded. All 18 exclusions were picked in rounds 3–7, so link availability can bias the historical donor distributions, particularly the later rounds. The displayed interval conditions on the historical shared environment and fitted donor pools. Workload remains in raw attempt units across changes in schedule length. No snaps conversions or runtime edits were made.

Use Python 3.12 with pandas, NumPy and pyarrow. Obtain `play_by_play_YEAR.parquet` for 2001–2022 from the [nflverse release](https://github.com/nflverse/nflverse-data/releases/tag/pbp), rename each to `YEAR.parquet`, and put them in one directory. See the [nflfastR data manual](https://nflverse.r-universe.dev/nflfastR/doc/manual.html) for field definitions and `results.json` for input hashes, coverage, exclusions and individual predictions.

```sh
sha256sum -c protocol.sha256
python pilot.py /path/to/archive results.json
python test_pilot.py /path/to/archive
```
