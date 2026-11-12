from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'analytics'
m=json.loads((A/'model.json').read_text());p=m['prospect'];t=m['team'];c=json.loads((A/'coarsening_comparison.json').read_text())
rows='\n'.join(f"| {k} | {v['n']} | {v['brier']:.5f} | {v['logLoss']:.5f} | {v['rocAuc']:.4f} |" for k,v in p['metrics'].items())
sub='\n'.join(f"| {v['group']} / {v['value']} | {v['n']} | {v['brier']:.4f} | {v['rocAuc']:.3f} |" for v in p['subgroupTestMetrics'])
text=f'''# Model experiments — executed results

Rebuilt and rerun 2026-11-02 from freshly downloaded sources. Artifact `analytics/model.json`; seed {m['seed']}; frozen feature/label cutoff {m['cutoff']}. Research alpha: the five-year modeling release gate has not passed.

## Rookie role target

Target: at least200 regular-season offensive plus defensive snaps in the rookie season among identifiable combine participants, excluding specialists. This is not starter probability, talent, elite probability or five-year career value.

Training2013–2014; tuning2015; held-out2016–2017. Final runtime fit2013–2017, with labels complete before the2018 draft. Final N={p['trainingRows']}; unknown identities excluded={p['excludedUnknownIdentities']}. Zero snaps is assigned only for known identifiers absent from a source covering all256 regular-season games. Unknown identifiers are not zero; their exclusion creates selection bias. Unique exact normalized-name repairs are audited in the artifact.

Height, weight and combine measurements plus position are the only predictors. Names, college, actual draft slot/team/round and future career results are excluded. Imputation, scaling and one-hot encoding fit within the training fold. Feature and outcome stores are separate under `analytics/features` and `analytics/outcomes`. Original publication timestamps are unavailable and recorded as unknown, not backfilled with invented dates.

| Held-out method | N | Brier↓ | Log loss↓ | ROC-AUC↑ |
|---|---:|---:|---:|---:|
{rows}

Selected: {p['selected']}, logistic C={p['logisticC']}, based only on2015 Brier score. Gradient boosting was tested and rejected on validation. Experiments retain all settings and losses. Held-out calibration intercept {p['selectedTestMetrics']['calibrationIntercept']:.3f}, slope {p['selectedTestMetrics']['calibrationSlope']:.3f}. Reliability bins are in the artifact; extreme bins have few cases. Descriptive Brier bootstrap95% interval {p['selectedTestMetrics']['brierBootstrap95']},500 individual resamples. It is conditional on observed cohorts and omits between-era uncertainty. No test-set recalibration was performed.

| Subgroup | N | Brier | ROC-AUC |
|---|---:|---:|---:|
{sub}

Age, college-strength and injury subgroups are unsupported. No universal individual confidence interval is claimed.

## Game model

Predict home-minus-away score using prior-season realized scoring-margin difference and home-field indicator. Training2000–2013; tuning2014–2015; test2016–2017. Selected ridge alpha={t['validation']['ridgeAlpha']}. Held-out RMSE={t['validation']['metrics']['ridge']['rmse']:.3f} points versus constant baseline {t['validation']['metrics']['baseline']['rmse']:.3f}. Its95% normal residual interval coverage={t['validation']['margin95IntervalCoverage']:.3%}, width={t['validation']['margin95IntervalWidth']:.2f} points. These wide errors limit predictive use.

Final pre2018 strength coefficient={t['strengthCoefficient']:.4f}; home effect={t['homeAdvantage']:.3f}; total-score mean={t['meanTotal']:.3f}. Method-of-moments residual decomposition over {t['residualDecomposition']['teamSeasonRows']} historical team-seasons gives season-shock SD={t['seasonShockSd']:.3f} and independent game SD={t['gameMarginSd']:.3f}. Two team-shock variances plus game-noise variance equal the marginal residual variance. Approximate opponent independence is a limitation.

Runtime applies the strength coefficient once to previous realized scoring margins, then adds season shocks and independent game noise. Next year's prior comes from simulated realized standings. The separate diagnostic annual persistence estimate must not be applied again; doing so double-shrinks the fitted signal.

## Boundaries

Only336 combine participants are playable. The39 retrospectively identified noncombine draftees are baseline-only. No five-year development, future roster transactions, injuries, NFL-wide MVP forecast or causal draft-to-wins mapping has been validated. Historical source revisions and incomplete original-publication archives prevent a claim of archive-perfect reconstruction. Later research is not represented as2018 GM knowledge.

## Reproduce

```sh
python -m pip install -r analytics/requirements.txt
python analytics/train_models.py
python analytics/pooling_validation.py
python analytics/test_models.py
python analytics/render_reports.py
python analytics/plot_diagnostics.py
```

Raw ingestion is a prerequisite. Artifact records source SHA-256 hashes, environment and runtime. Complete training runtime={m['runtimeSeconds']:.3f}s in `{json.dumps(m['environment'])}`; this is not hosted simulation latency.
'''
for a,b in [('least200','least 200'),('Training2013','Training 2013'),('tuning2015','tuning 2015'),('held-out2016','held-out 2016'),('fit2013','fit 2013'),('the2018','the 2018'),('all256','all 256'),('on2015','on 2015'),('bootstrap95%','bootstrap 95%'),(',500',', 500'),('Training2000','Training 2000'),('tuning2014','tuning 2014'),('test2016','test 2016'),('Its95%','Its 95%'),('pre2018','pre-2018'),('Only336','Only 336'),('The39','The 39'),('as2018','as 2018')]:text=text.replace(a,b)
(ROOT/'MODEL_EXPERIMENTS.md').write_text(text)
rows='\n'.join(f"| {k} | {v['brier']:.5f} | {v['logLoss']:.5f} | {v['rocAuc']:.4f} |" for k,v in c['variants'].items())
comparison='\n'.join(f"| {k} | {v['brierDifference']:+.5f} | [{v['withinCohortBootstrap95'][0]:+.5f}, {v['withinCohortBootstrap95'][1]:+.5f}] |" for k,v in c['comparisonsVsRaw'].items())
(A/'BLIND_SCOUTING_EXPERIMENT.md').write_text(f'''# Blind scouting: information-loss experiment

Executed2026-11-02. This tests candidate coarsening of measurements and displayed probabilities. It does not establish anonymity, equal human decision quality or optimal band widths. Root's separate uniqueness analysis measures how easily fields identify a prospect within the installed pool.

Training2013–2014, tuning2015, test2016–2017 (613 identifiable combine participants). Raw and coarse logistic hyperparameters are independently selected using only2015 Brier loss. Missing values stay missing. Fixed candidate widths: height3in, weight15lb, forty0.2s, bench5 repetitions, vertical5in, broad jump10in, cone/shuttle0.2s. Measurements map to the nearest fixed-width center. Probability-display compression is evaluated at midpoints of10-percentage-point bands; this does not require changing hidden runtime probabilities.

| Variant | Brier↓ | Log loss↓ | ROC-AUC↑ |
|---|---:|---:|---:|
{rows}

| Difference against raw logistic | Brier difference | Paired within-cohort bootstrap95% interval |
|---|---:|---:|
{comparison}

Intervals use1000 resamples within each test cohort, seed20180426. This estimates conditional sampling uncertainty within two cohorts, not future-era uncertainty. The coarse model's small point-estimate deterioration and interval containing zero do not prove equivalence; no equivalence margin was prespecified. The probability-band results also show that apparently minor display compression can change proper scoring metrics.

College is not a model predictor, so this experiment cannot establish whether college labels help human scouting. Verified pre-draft college production is unavailable; its predictive and recognition trade-offs cannot be tested here. Keep proposed production fields marked unavailable until real data is obtained. Do not fabricate statistics, change real athletic attributes, or claim removing names prevents recognition.

Practical inference: coarse descriptors are a plausible candidate for a recognition-resistant daily interface, provided uniqueness/linkage tests and actual user testing support them. This is an inference, not an empirically established optimum. Standard historical play may preserve exact source-backed information if it is explicitly name-hidden rather than anonymous. The two display policies can share the same two game modes and engine.

Relevant foundations: [NIST SP800-188](https://csrc.nist.gov/pubs/sp/800/188/final) recommends measuring re-identification risk when transforming quasi-identifiers; it does not certify this football interface. [Combine performance research](https://pubmed.ncbi.nlm.nih.gov/32459737/) motivates skepticism about physical measurements as a complete talent signal. See `research/MODELING_RESEARCH.md` for evidence and limitations.
''')
reports=[]
for team in ['CLE','KC','NE','SF']:
 path=A/('simulation_diagnostics'+('' if team=='CLE' else '_'+team)+'.json')
 if path.exists():reports.append(json.loads(path.read_text()))
if reports:
 d=reports[0];rows='\n'.join(f"| {k} | {d['observed2018Through2022'][k]:.4f} | {v['mean']:.4f} | [{v['p025']:.4f}, {v['p975']:.4f}] |" for k,v in d['simulatedBaseline'].items());conv='\n'.join(f"| {r['configuration']['team']} | {v['replicates']} | {v['pairedMeanWinDifference']:.3f} | {v['pairedStandardError']:.3f} | {v['probabilityImprovement']:.3f} | {v['probabilityMcse']:.3f} |" for r in reports for v in r['convergence'] if v['replicates']>=32);flags='\n'.join(f"- {f['metric']}: recorded{f['observed']:.4f}, simulated{f['simulatedMean']:.4f}." for f in d['distributionFlags']);perf='\n'.join(f"| {r['configuration']['team']} | {r['replicates']} | {r['performance']['simulationMilliseconds']/1000:.3f}s | {r['performance']['millisecondsPerPairedFiveSeasonReplicate']:.2f}ms |" for r in reports)
 score='Not yet executed.';sp=A/'score_sensitivity.json'
 if sp.exists():
  ss=json.loads(sp.read_text());sr='\n'.join(f"| {p['name']} | {p['decisionScore']} | {p['pairedSummary']['mean']:.3f} | {p['pairedSummary']['standardError']:.3f} |" for p in ss['policies']);score=f"Four prespecified policies, same CLE scenario and seed family;128 paired replicates per policy. Each score weight is multiplied by0.5 or1.5 then renormalized. Top rank changes={ss['topRankChanges']} of{len(ss['weightPerturbations'])} settings; minimum rank correlation={ss['minRankCorrelation']:.3f}. This small exploratory exercise does not validate GM skill or user-trade strategy.\n\n| Policy | Score | Mean paired wins | MCSE |\n|---|---:|---:|---:|\n{sr}"
 (ROOT/'SIMULATION_VALIDATION.md').write_text(f'''# Simulation validation — executed diagnostics

Rebuilt2026-11-02; engine {d['configuration']['engineVersion']}. Full statistical release gate **not passed**. JSON reports retain exact source/model hashes. Simulations use the actual TypeScript engine via a temporary transpilation loader.

Game predictor alignment fixes double shrinkage: the prior-season coefficient is applied once, and next state uses simulated realized margins. Team-year shocks preserve within-season correlation. Directional home/away random keys prevent repeated divisional games sharing identical residuals. Rounded1-point scores map to2; the score model is still a continuous approximation.

## League distributions

Actual2018–2022 data is evaluation-only, not used to tune parameters after the historical cutoff. Recorded completed games={d['observed2018Through2022']['games']}; a full simulated schedule has1312. Rates are normalized by games/team-seasons.

| Metric | Recorded | Simulated mean | Across-replicate2.5–97.5% range |
|---|---:|---:|---:|
{rows}

Conditional distribution flags:

{flags}

These failures remain disclosed. Fixed pre2018 scoring misses later regime changes; shutout behavior is imperfect. Matching marginal win variance does not validate player careers, league rosters, CPU strategy, awards or draft effects. Intervals omit parameter and model-structure uncertainty.

## Ensemble convergence

| Team | Replicates | Mean paired five-year wins | Mean MCSE | P(improvement) | Probability MCSE |
|---|---:|---:|---:|---:|---:|
{conv}

A256-replicate standard is a practical precision/latency choice informed by these results. Probability MCSE is bounded by0.03125 at256 independent replicates. More simulations reduce sampling noise; they cannot repair causal/model misspecification. Small leaderboard differences should not be interpreted as statistically established skill differences.

## Score sensitivity

{score}

## Local performance

| Team | Replicates | Paired five-season time | Per paired replicate |
|---|---:|---:|---:|
{perf}

These concurrent container runs include CPU contention and are not hosted Worker/network/iPhone benchmarks. Hardware: `{json.dumps(d['performance']['hardware'])}`. Draft time logged separately.

## Tests and limitations

`analytics/test_models.py` runs12 meaningful checks covering chronological partitions, completed labels, exact metric recomputation, leakage via poisoned future records, probability/ID constraints, source coverage, residual variance conservation, missingness-preserving coarsening and measured coarsening metrics. Source publication timestamps remain explicitly unknown. Engine structural tests are documented separately.

Only336 combine participants are playable;39 noncombine actual draftees are baseline-only. Source snapshots and initial ownership are not archive-perfect. Future roster transactions, individual injuries, validated player development and NFL-wide awards are unsupported. Cohort awards are model summaries. Scoring and draft-impact functions are assumptions, not causal evidence.

## Reproduce

```sh
python analytics/train_models.py
python analytics/pooling_validation.py
python analytics/test_models.py
node analytics/simulation_diagnostics.mjs 256 CLE
node analytics/simulation_diagnostics.mjs 256 KC
node analytics/simulation_diagnostics.mjs 256 NE
node analytics/simulation_diagnostics.mjs 256 SF
node analytics/score_sensitivity.mjs
python analytics/render_reports.py
python analytics/plot_diagnostics.py
```
''')
# Normalize generated prose spacing only; code/metric values unchanged.
for path in [A/'BLIND_SCOUTING_EXPERIMENT.md',ROOT/'SIMULATION_VALIDATION.md']:
 if not path.exists():continue
 s=path.read_text()
 import re
 
 for a,b in [('Executed2026','Executed 2026'),('Training2013','Training 2013'),('tuning2015','tuning 2015'),('test2016','test 2016'),('only2015','only 2015'),('height3in','height 3in'),('weight15lb','weight 15lb'),('forty0.2s','forty 0.2s'),('bench5','bench 5'),('vertical5in','vertical 5in'),('jump10in','jump 10in'),('shuttle0.2s','shuttle 0.2s'),('of10-','of 10-'),('bootstrap95%','bootstrap 95%'),('use1000','use 1000'),('seed20180426','seed 20180426'),('SP800','SP 800'),('Rebuilt2026','Rebuilt 2026'),('Rounded1-','Rounded 1-'),('to2;','to 2;'),('Actual2018','Actual 2018'),('has1312','has 1312'),('Across-replicate2.5','Across-replicate 2.5'),('recorded46','recorded 46'),('simulated43','simulated 43'),('pre2018','pre-2018'),('A256','A 256'),('by0.03125 at256','by 0.03125 at 256'),(';128','; 128'),('by0.5 or1.5','by 0.5 or 1.5'),('of11','of 11'),('runs12','runs 12'),('Only336','Only 336'),(';39','; 39')]:s=s.replace(a,b)
 path.write_text(s)
print('Reports generated from executed artifacts.')
pp=A/'pooling_validation.json'
if pp.exists():
 q=json.loads(pp.read_text());rows='\n'.join(f"| {k} | {v['brier']:.6f} | {v['logLoss']:.6f} | {v['rocAuc']:.5f} |" for k,v in q['metrics'].items());diff=q['pairedDifferencesVsRaw']['pooledMean'];addition=f'''\n## Shared-profile pooling selected for further testing\n\nThe runtime policy now groups candidates within broad position, sorts frozen model probabilities, chunks five and merges a short final tail. It shares the arithmetic mean probability and the same measurement ranges. Runtime model version adds `+blind-g5-v1`; CPU choices, scoring and simulation use the pooled probabilities too. This removes individual fine-resolution probabilities from CPU decisions. The UI still shows a ten-point band while CPU/scoring use the exact pooled mean, so their numerical precision is not identical. All human participants receive the same profile policy. The raw trained artifact remains separately available for reproducibility.\n\nThe independent held-out utility test groups all {q['allCandidatesGrouped']} nonspecialist combine participants within each of 2016 and 2017 before joining outcomes. Only {q['evaluatedWithKnownLabels']} have identified labels; {q['unknownLabelsExcluded']} unlabeled candidates affect the groups but do not become invented zero outcomes. Every group has at least {q['minimumGroupSize']} candidates. Canonical ID order breaks exact probability ties; no outcome label is used.\n\n| Held-out variant | Brier | Log loss | ROC-AUC |\n|---|---:|---:|---:|\n{rows}\n\nPooled-minus-raw Brier difference={diff['brierDifference']:+.6f}; paired within-cohort bootstrap95% interval [{diff['withinCohortBootstrap95'][0]:+.6f}, {diff['withinCohortBootstrap95'][1]:+.6f}]. This small point-estimate difference is compatible with modest benefit or harm. It does not prove equivalence, equal human scouting quality, or anonymity. Utility is measured for rookie participation only. See `analytics/pooling_validation.json` and `analytics/outcomes/pooling_test_predictions.csv`.\n\nThe earlier fixed measurement bands alone did not establish sufficient ambiguity; root's separate within-pool uniqueness audit should be consulted. Shared profiles protect against exact matching of the released profile within the initial pool, subject to the measured group-size condition. They cannot guarantee protection against elimination, auxiliary knowledge, collusion or recognition after repeated play. College and exact individual measurements remain hidden during blind scouting; underlying historical facts are never falsified.\n'''
 path=A/'BLIND_SCOUTING_EXPERIMENT.md';path.write_text(path.read_text()+addition)
 path=ROOT/'MODEL_EXPERIMENTS.md';path.write_text(path.read_text()+f"\n## Runtime display policy\n\nThe raw trained model is wrapped by `blind-g5-v1` for both playable modes. Shared-profile probability pooling has a separate held-out utility evaluation: Brier{q['metrics']['pooledMean']['brier']:.6f} versus raw{q['metrics']['raw']['brier']:.6f}. See `analytics/BLIND_SCOUTING_EXPERIMENT.md`. This is not a validated five-year model or an anonymity guarantee.\n")
 path=ROOT/'SIMULATION_VALIDATION.md'
 if path.exists():
  text=path.read_text().replace('runs12','runs 15').replace('runs 12','runs 15');text+=f"\n## Pooled runtime configuration\n\nFinal simulation diagnostics use model version `{d['configuration']['modelVersion']}` through `lib/scouting.ts` in the same runtime loader as the application. Unpooled experiments are retained under `analytics/pilots/unpooled-2026-11-02`. Source hashes distinguish the executions. The pooling utility experiment is a separate first-season predictive check, not validation of simulated five-year causal effects.\n";path.write_text(text)
