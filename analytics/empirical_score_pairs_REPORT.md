# Historical joint score-pair donor experiment

Research only. Do not adopt. Work was isolated in `/tmp/redraft-score-pairs`; the main checkout was not edited.

Before executing outcomes, the implementation fixed a ten-season donor window, Gaussian bandwidth six points on lagged-strength expected margin, and 4,096 predictive draws per game. No bandwidth or recency alternatives were tried. Each test season refits the comparator only through the preceding season; donor weights use preceding-season point differential, never current-season outcomes. Canonical franchise aliases and 1999 prior-season context are retained. Every draw is an actual historical home/away score pair, preserving discrete score support, score dependence and shutouts. This is feasible as an experiment, but finite historical support is not a generative model of football scoring.

The predefined acceptance criteria require candidate CRPS no worse for total, margin, home score and away score in each of 2014–15 and 2016–17; corresponding MAEs at most 1% worse; shutout Brier no worse; and each 90% coverage error no more than one percentage point worse. Shared team-season dependence must also be validated before adoption. These are experiment acceptance rules, not universal scientific thresholds. All assessment years were previously examined in this project, so passing would still not establish untouched validation.

| Assessment | Metric | Historical normal | Joint score pairs |
|---|---|---:|---:|
| 2014–15 | Total CRPS | 7.7895 | 7.7957 |
| 2014–15 | Margin CRPS | 8.0496 | 8.2384 |
| 2014–15 | Home score CRPS | 5.7782 | 5.8540 |
| 2014–15 | Away score CRPS | 5.4192 | 5.4872 |
| 2014–15 | Shutout Brier | 0.01783 | 0.01733 |
| 2016–17 | Total CRPS | 7.7539 | 7.7468 |
| 2016–17 | Margin CRPS | 7.4958 | 7.6057 |
| 2016–17 | Home score CRPS | 5.5328 | 5.5757 |
| 2016–17 | Away score CRPS | 5.3033 | 5.3342 |
| 2016–17 | Shutout Brier | 0.02680 | 0.02673 |

Both windows fail the margin and individual-team score CRPS/MAE requirements. The 2016–17 margin 90% coverage rises from 91.4% to 93.9%, also failing its coverage gate. Better shutout calibration does not compensate for those failures. Effective donor counts exceed 1,759 in every matchup; sparse donor weights are not the immediate bottleneck. Kernel smoothing weakens conditioning on team strengths, a plausible contributor to worse margin forecasts; that explanation is an inference, not an identified cause.

A descriptive 1,000-season simulation uses the known 2017 schedule and strengths based on observed 2016 PF/PA. The comparator decomposes residual variance into game noise and shared team-season shocks using scores only through 2016. The candidate independently samples each game's donor pair, with no additional shock (adding the comparator shock would double-count unseparated donor variability).

| Simulated league statistic | Normal with shared shocks | Independent score-pair donors |
|---|---:|---:|
| Mean within-team season-win SD | 2.790 | 1.975 |
| Pooled wins 5th / median / 95th percentile | 3 / 8 / 13 | 5 / 8 / 11 |
| Probability any team wins at least 14 games | 61.7% | 6.0% |
| Probability any team wins at most 2 games | 63.8% | 6.1% |
| Mean within-team season-points SD | 53.89 | 40.40 |

This identifies a material integration failure: independent donor draws compress season outcomes and cannot replace a score kernel while discarding shared team-season variation. These are simulated comparisons, not calibration against repeated observed leagues. No postseason, draft impact, regenerated schedule or five-year simulated path is modeled. The normal comparator's extreme-season probabilities are not asserted to be correct.

Commands:

```bash
cd /tmp/redraft-score-pairs
python analytics/empirical_score_pairs.py /workspace/scratch/781ed5af9c46/redraft/data/raw/games.csv > /tmp/empirical-score-pairs.log
cd analytics
REDRAFT_GAMES_CSV=/workspace/scratch/781ed5af9c46/redraft/data/raw/games.csv python -m unittest test_empirical_score_pairs -v
```

The adjacent JSON contains source SHA-256, fitted parameters, all metrics and individual acceptance-gate outcomes. Support and chronology checks passed: generated pairs belong to the donor support; shutouts have positive support; poisoning all 2014+ scores leaves the 2014 donor set and expected-margin weights unchanged.

CRPS and Brier follow the existing audited evaluation implementation. The empirical donor algorithm is an explicit computational hypothesis, not a claim of a scientifically established NFL score law. No statistical significance or adoption claim is made. A future candidate would need a separate latent-team and conditional joint-score decomposition plus genuinely withheld validation; no such change was attempted after these results.
