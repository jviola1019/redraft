"""Exact finite-donor forecast audit; does not refit or change production forecasts.

All 2018 labels here are evaluation-only. They were already examined before this
audit: these results are reused historical backtests, not a new untouched test.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'analytics'
SEEDS = list(range(2026110400, 2026110416))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(k, n, z=1.959963984540054):
    """Descriptive binomial interval; independence across players is approximate."""
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0., center - half), min(1., center + half)]


def weights(donors, probability=None):
    result = np.ones(len(donors)) / len(donors)
    positive = np.array([d['rookieRole'] for d in donors])
    if probability is not None and positive.any() and (~positive).any():
        result = np.where(positive, probability / positive.sum(),
                          (1 - probability) / (~positive).sum())
    assert np.isclose(result.sum(), 1) and (result >= 0).all()
    return result


def weighted_quantile(values, w, probability):
    order = np.argsort(values, kind='stable')
    cumulative = np.cumsum(w[order])
    return float(values[order[min(np.searchsorted(cumulative, probability), len(values) - 1)]])


def evaluate_distribution(values, w, actual):
    """CRPS = E|X-y| - .5 E|X-X'|, exactly for the finite donor mixture."""
    result = {'actual': float(actual), 'mean': float(values @ w),
              'crps': float(np.abs(values - actual) @ w -
                            .5 * (w[:, None] * w[None, :] *
                                  np.abs(values[:, None] - values[None, :])).sum()),
              'outsideSupport': bool(actual < values.min() or actual > values.max())}
    for nominal in [.8, .95]:
        alpha = 1 - nominal
        lo = weighted_quantile(values, w, alpha / 2)
        hi = weighted_quantile(values, w, 1 - alpha / 2)
        result[f'lower{int(nominal*100)}'] = lo
        result[f'upper{int(nominal*100)}'] = hi
        result[f'intervalScore{int(nominal*100)}'] = float(
            hi - lo + 2 / alpha * max(lo - actual, 0) + 2 / alpha * max(actual - hi, 0))
    return result


def summarize(rows):
    actual = np.array([r['actual'] for r in rows])
    prediction = np.array([r['mean'] for r in rows])
    result = {'n': len(rows), 'mae': float(np.abs(actual-prediction).mean()),
              'rmse': float(np.sqrt(np.mean((actual-prediction)**2))),
              'meanCrps': float(np.mean([r['crps'] for r in rows])),
              'outsideDonorSupport': int(sum(r['outsideSupport'] for r in rows))}
    for level in [80, 95]:
        covered = np.array([r[f'lower{level}'] <= r['actual'] <= r[f'upper{level}'] for r in rows])
        result[f'interval{level}'] = {'coverage': float(covered.mean()),
            'covered': int(covered.sum()), 'wilson95': wilson(int(covered.sum()), len(rows)),
            'meanWidth': float(np.mean([r[f'upper{level}']-r[f'lower{level}'] for r in rows])),
            'meanIntervalScore': float(np.mean([r[f'intervalScore{level}'] for r in rows]))}
    return result


def run():
    strict = json.loads((A / 'five_year_strict_2018.json').read_text())
    frame = pd.read_csv(A / 'five_year_frozen_2018_predictions.csv')
    records, baseline_records, pools = [], [], []
    for player in frame.to_dict('records'):
        pool = [d for d in strict['donors'] if d['position'] == player['position']]
        w = weights(pool, player['pooledRookieProbability'])
        baseline_w = weights(pool)
        record = {'prospectId': player['prospectId'], 'position': player['position']}
        base = dict(record)
        for kind in ['snaps', 'games']:
            values = np.array([sum(d[kind]) for d in pool], dtype=float)
            actual = sum(player[f'{kind}{i}'] for i in range(1, 6))
            record[kind] = evaluate_distribution(values, w, actual)
            base[kind] = evaluate_distribution(values, baseline_w, actual)
        records.append(record)
        baseline_records.append(base)
        pools.append((np.array([sum(d['snaps']) for d in pool], dtype=float), w))
    by_position = {}
    for pos in sorted(frame.position.unique()):
        indices = [i for i, r in enumerate(records) if r['position'] == pos]
        by_position[pos] = {'support': strict['supportByPosition'][pos],
            **{kind: summarize([records[i][kind] for i in indices]) for kind in ['snaps', 'games']}}
    # No stochastic error in the exact audit. Separately measure finite-ensemble
    # approximation error across a fixed, disclosed seed family.
    finite = []
    exact_means = np.array([r['snaps']['mean'] for r in records])
    actual = frame[[f'snaps{i}' for i in range(1,6)]].sum(axis=1).to_numpy()
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        draws = np.array([rng.choice(v, size=256, p=w) for v,w in pools])
        predicted = draws.mean(axis=1)
        lo, hi = np.quantile(draws, [.025,.975], axis=1)
        groups = {}
        for pos in sorted(frame.position.unique()):
            mask = frame.position.eq(pos).to_numpy()
            groups[pos] = {'n': int(mask.sum()),
                'coverage95': float(np.mean((actual[mask]>=lo[mask])&(actual[mask]<=hi[mask]))),
                'rmsMeanApproximationError': float(np.sqrt(np.mean((predicted[mask]-exact_means[mask])**2)))}
        finite.append({'seed': seed, 'drawsPerProspect': 256,
            'rmsMeanApproximationError': float(np.sqrt(np.mean((predicted-exact_means)**2))),
            'subgroups': groups})
    delta = np.array([r['snaps']['crps']-b['snaps']['crps'] for r,b in zip(records,baseline_records)])
    rng = np.random.default_rng(20261104)
    bootstrap = [delta[rng.integers(0,len(delta),len(delta))].mean() for _ in range(2000)]
    result = {'version': 'exact-donor-audit-v1', 'asOf': '2026-11-04',
        'evaluationStatus': 'Reused 2018 historical backtest; no new untouched test claim.',
        'runtimeArtifactChanged': False, 'cohort': 2018, 'outcomeSeasons': [2018,2022],
        'strictCutoff': strict['cutoff'], 'donorCohorts': strict['cohorts'],
        'methods': {'quantiles': 'left inverse of exact weighted empirical CDF',
                    'distributionScore': 'CRPS, exact finite mixture; lower is better',
                    'intervalScore': 'proper interval score includes misses and width; lower is better',
                    'coverageUncertainty': 'Wilson 95%; descriptive, approximate independent-player assumption'},
        'overall': {kind:summarize([r[kind] for r in records]) for kind in ['snaps','games']},
        'positionBaseline': {kind:summarize([r[kind] for r in baseline_records]) for kind in ['snaps','games']},
        'pairedCrpsVsPositionBaseline': {'difference': float(delta.mean()),
            'playerBootstrap95': list(map(float,np.quantile(bootstrap,[.025,.975]))),
            'resamples':2000,'note':'One cohort; does not measure between-era or team clustering uncertainty.'},
        'subgroups': by_position, 'finiteEnsembleSeeds': finite,
        'specialists': {'status':'unsupported quality target; no specialist outcome coverage claim',
                        'support':strict['supportByPosition']['ST']},
        'sourceHashes': {str(p.relative_to(ROOT)):sha(p) for p in [A/'five_year_strict_2018.json',A/'five_year_frozen_2018_predictions.csv',A/'model.json']},
        'limitations': ['2013 is the only fully observed strict donor cohort; no independent pre2018 five-year chronological validation exists.',
            'Exact integration removes Monte Carlo noise from this audit; it does not broaden donor support or fix undercoverage.',
            'Games means games with recorded snaps, not official appearances or starts.',
            'Forecasts precede capacity/opportunity transformations and are not validated causal wins.',
            'A 17-game future season changes exposure; strict donors all come from 16-game seasons.',
            'No parameter, source revision, selection bias, or counterfactual model uncertainty is captured.']}
    (A/'forecast_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    pd.DataFrame([{**{'prospectId':r['prospectId'],'position':r['position']},
                   **{f'{kind}_{k}':v for kind in ['snaps','games'] for k,v in r[kind].items()}}
                  for r in records]).to_csv(A/'forecast_audit_predictions.csv',index=False)
    print(json.dumps({'overall':result['overall'],'QB':by_position['QB'],
                      'pairedCrps':result['pairedCrpsVsPositionBaseline']},indent=2))
    return result


if __name__ == '__main__':
    run()
