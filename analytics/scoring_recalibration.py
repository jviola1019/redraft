"""Train-only total-score recency comparison; no runtime artifact writes.

2018+ results have already been seen in this project. Candidate construction was
motivated by that audit, so this is retrospective development even though every
numerical fit and candidate choice is restricted to pre-2018 observations.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
A = ROOT/'analytics'
WINDOWS = [None,3,5,10]


def training_rows(games, origin, window):
    rows = games[games.season < origin]
    if window is not None:
        rows = rows[rows.season >= origin-window]
    if rows.empty:
        raise ValueError('No pre-origin training scores')
    assert int(rows.season.max()) < origin
    return rows


def fit(games):
    # Filtering occurs BEFORE any statistics, fitting, method choice, or evaluation.
    g = games[(games.season>=2000)&(games.season<=2017)&(games.game_type=='REG')].dropna(subset=['home_score','away_score']).copy()
    g['total'] = g.home_score+g.away_score
    annual = g.groupby('season').total.mean()
    methods = {}
    for window in WINDOWS:
        key = 'expanding' if window is None else f'trailing{window}'
        rows = []
        for origin in range(2005,2018):
            prior = training_rows(g,origin,window)
            prediction = float(prior.total.mean())
            observed = float(annual[origin])
            rows.append({'origin':origin,'trainFirstSeason':int(prior.season.min()),
                         'trainLastSeason':int(prior.season.max()),'trainGames':len(prior),
                         'predictedMeanTotal':prediction,'observedMeanTotal':observed,
                         'squaredError':(prediction-observed)**2})
        methods[key] = {'window':window,'origins':rows,
            'selection2005Through2012RMSE':float(np.sqrt(np.mean([r['squaredError'] for r in rows if r['origin']<=2012]))),
            'assessment2013Through2017RMSE':float(np.sqrt(np.mean([r['squaredError'] for r in rows if r['origin']>=2013])))}
    selected = min(methods,key=lambda k:methods[k]['selection2005Through2012RMSE'])
    final = training_rows(g,2018,methods[selected]['window'])
    # A genuinely frozen five-season forecast from the 2013 origin, selected using
    # only 2005-12 one-season losses. No future annual means enter its prediction.
    five = {}
    for method in ['expanding',selected]:
        prediction = float(training_rows(g,2013,methods[method]['window']).total.mean())
        actual = np.array([annual[y] for y in range(2013,2018)])
        five[method]={'origin':2013,'futureSeasons':[2013,2017],
                      'frozenPrediction':prediction,'observedAnnualMeans':list(map(float,actual)),
                      'fiveSeasonMeanError':float(prediction-actual.mean()),
                      'annualMeanRMSE':float(np.sqrt(np.mean((prediction-actual)**2)))}
    before = methods['expanding']['assessment2013Through2017RMSE']
    after = methods[selected]['assessment2013Through2017RMSE']
    return {'selected':selected,'selectionCriterion':'Minimum RMSE of annual mean total at one-season origins 2005–2012',
        'assessment':'2013–2017 one-season rolling origins; only earlier seasons fit each forecast',
        'methods':methods,'frozenFiveSeasonAssessment':five,
        'candidateMeanTotal2018':float(final.total.mean()),
        'candidateTrainingSeasons':[int(final.season.min()),int(final.season.max())],
        'improvementOnLaterPre2018Origins':after<before,
        'improvementOnFrozenFiveSeason2013':five[selected]['annualMeanRMSE']<five['expanding']['annualMeanRMSE']}


def run():
    source = ROOT/'data/raw/games.csv'
    raw = pd.read_csv(source,low_memory=False)
    result = fit(raw)
    # Executed poisoning check: future outcomes cannot alter this candidate.
    poisoned = raw.copy()
    poisoned.loc[poisoned.season>=2018,['home_score','away_score']] = 999999
    assert result == fit(poisoned)
    runtime = json.loads((A/'model.json').read_text())
    result.update({'version':'scoring-recalibration-pre2018-v1','asOf':'2026-11-04',
        'cutoff':'2018-04-26T00:00:00Z','fitThroughSeason':2017,
        'currentMeanTotal':runtime['team']['meanTotal'],
        'proposedOverride':{'meanTotal':result['candidateMeanTotal2018']},
        'runtimeArtifactChanged':False,'futureOutcomePoisoningTest':'passed',
        'sourceHash':hashlib.sha256(source.read_bytes()).hexdigest(),
        'decision':'Candidate supported for recency of unconditional total only; requires integrated simulation validation before adoption.',
        'limitations':['Design responds to already examined post2017 scoring failures; no new untouched test claim.',
            'Only five later pre2018 annual assessment observations and one frozen five-season window.',
            'One-season rolling losses and five-season frozen forecasts answer different questions; both shown.',
            'This mean update does not fix the discretized normal low-score distribution or identify draft effects.',
            'No new variance, home advantage or player effect fit. No guarantee against post2017 era shift.',
            'Forecast-origin samples overlap in training; conventional independent-origin significance is not asserted.']})
    (A/'scoring_recalibration.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['selected','currentMeanTotal','candidateMeanTotal2018','frozenFiveSeasonAssessment','futureOutcomePoisoningTest']},indent=2))
    return result


if __name__=='__main__':
    run()
