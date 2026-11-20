# NFL field-goal pilot

Kicker history reduced 2014–2017 log loss from 0.373507 to 0.372782 over 4,010 regular-season attempts from 56 kickers. It helped in all four evaluation seasons, but the paired kicker-cluster 95% interval for the difference was [−0.003308, +0.001706]. The pilot misses its frozen advancement criterion. Brier score moved from 0.116405 to 0.116182.

| Season | Attempts | Change in log loss |
| --- | ---: | ---: |
| 2014 | 987 | −0.000744 |
| 2015 | 987 | −0.000263 |
| 2016 | 1,009 | −0.000272 |
| 2017 | 1,027 | −0.001594 |

The audit retained 16,531 of 16,532 recorded regular-season attempts across 2001–2017. One attempt had no eligible distance. The candidate fell back to the distance-only probability on 591 attempts with no prior eligible kicker history. In that group, observed conversion was 81.22% and predicted conversion was 84.82%. Across all evaluation attempts, observed conversion was 84.26%, the baseline predicted 84.11%, and the candidate predicted 85.42%.

Recorded attempts represent team decisions about when and from where to try a kick. The result reflects the kicker, protection, snap, hold, conditions and other game context. A shared season shock can affect several kicker clusters, and the bootstrap conditions on these four seasons. The target supports assessing historical attempt forecasts only. Prospect translation requires a linked prospect sample and separate evaluation. Keep runtime and specialist ratings unchanged based on this pilot.

Use Python 3.12 with pandas, NumPy, SciPy, scikit-learn and pyarrow. Download the [nflverse play-by-play release](https://github.com/nflverse/nflverse-data/releases/tag/pbp) assets for 2001–2017 into a folder, naming each asset `YEAR.parquet`. Source field definitions appear in the [nflfastR data manual](https://nflverse.r-universe.dev/nflfastR/doc/manual.html). Per-file SHA-256 values are included in `results.json` to identify the data snapshot.

From this directory run:

```sh
sha256sum -c protocol.sha256
python pilot.py /path/to/archive results.json
python test_pilot.py /path/to/archive
```
