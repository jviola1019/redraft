"""Research-only QB usage hindcast with draft-date exposure and frozen comparators."""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
import pandas as pd

import five_year as fy
from forecast_audit import donor_total, evaluate_distribution, summarize, weights
from qb_five_year_hindcast import distribution

ORIGINS = range(2016, 2022)
TARGETS = ('snaps', 'games')
DRAWS = 8192
SEED = 20261120
A = Path(__file__).resolve().parent


def scheduled_games(year):
    return 17 if year >= 2021 else 16


def origin_games(cohort, realized):
    return np.array([scheduled_games(cohort + age if realized else cohort)
                     for age in range(5)])


def fit_slice(panel, cohort):
    return panel.loc[panel.year < cohort].copy()


def rank_paths(fit):
    percentiles = (np.arange(DRAWS) + 0.5) / DRAWS
    ages = []
    for age in range(5):
        rows = fit.loc[fit.age == age].sort_values(['snaps', 'games', 'pfrId'])
        if rows.empty:
            raise ValueError(f'No annual donor observations at career age {age}')
        values = rows[list(TARGETS)].to_numpy(float)
        values *= (16 / rows.year.map(scheduled_games).to_numpy())[:, None]
        ages.append(values[(percentiles * len(rows)).astype(int)])
    return np.stack(ages, axis=1)


def panel_for(cohorts, annual, final_year):
    records = []
    for player in cohorts.itertuples():
        for year in range(max(2013, player.season), min(final_year, player.season + 4) + 1):
            outcome = annual.get((year, player.pfr_id), {'snaps': 0, 'games': 0})
            records.append({'pfrId': player.pfr_id, 'cohort': player.season, 'year': year,
                            'age': year - player.season, **{k: outcome[k] for k in TARGETS}})
    return pd.DataFrame(records)


def comparison_paths(fit, cohort, candidate):
    if cohort < 2018:
        return np.repeat(candidate[:, :1], 5, axis=1)
    complete = fit.loc[fit.cohort.between(2013, cohort - 5)]
    ordered = complete.sort_values(['cohort', 'pfrId', 'age'])
    if not ordered.groupby(['cohort', 'pfrId']).age.nunique().eq(5).all():
        raise ValueError('Incomplete history entered complete-donor comparison')
    paths = ordered[list(TARGETS)].to_numpy(float).reshape(-1, 5, len(TARGETS))
    years = ordered.year.to_numpy().reshape(-1, 5)
    return paths * (16 / np.where(years >= 2021, 17, 16))[..., None]


def score(path, exposure, total, kind):
    totals = (path[:, :, TARGETS.index(kind)] * (exposure / 16)).sum(axis=1)
    return distribution(totals, total)


def paired_bootstrap(rows, target):
    rng = np.random.default_rng(SEED)
    groups = []
    for cohort in sorted({r['cohort'] for r in rows}):
        groups.append(np.array([r['ageRank'][target]['crps'] - r['comparison'][target]['crps']
                                for r in rows if r['cohort'] == cohort]))
    samples = [group[rng.integers(len(group), size=(5000, len(group)))] for group in groups]
    return {'difference': float(np.concatenate(groups).mean()),
            'playerBootstrap95': np.quantile(np.concatenate(samples, axis=1).mean(axis=1),
                                              [.025, .975]).tolist()}


def evaluate(rows):
    return {**{method: {target: summarize([row[method][target] for row in rows])
                        for target in TARGETS} for method in ('ageRank', 'comparison')},
            'pairedCrps': {target: paired_bootstrap(rows, target) for target in TARGETS}}


def run(out):
    annual, coverage, _ = fy.load_annual(2013, 2025)
    combine = pd.read_csv(fy.RAW / 'combine.csv', low_memory=False)
    qbs = combine.loc[combine.pos.eq('QB') & combine.season.between(2009, 2021)]
    known = qbs.loc[qbs.pfr_id.notna()]
    if known.duplicated('pfr_id').any():
        raise ValueError('Ambiguous QB identity')
    panel = panel_for(known, annual, 2025)
    frozen = pd.read_csv(A / 'five_year_frozen_2018_predictions.csv').query("position == 'QB'")
    donors = [d for d in json.loads((A / 'five_year_strict_2018.json').read_text())['donors']
              if d['position'] == 'QB']
    frozen_rows = {r['pfr_id']: r for r in frozen.to_dict('records')}
    baseline_reference = json.loads((A / 'forecast_audit.json').read_text())['subgroups']['QB']
    rows = {'draftTime': [], 'realizedSensitivity': []}
    fits = {}
    for cohort in ORIGINS:
        fit = fit_slice(panel, cohort)
        paths = rank_paths(fit)
        poisoned = panel.copy()
        poisoned.loc[poisoned.year >= cohort, list(TARGETS)] = 999999
        np.testing.assert_array_equal(paths, rank_paths(fit_slice(poisoned, cohort)))
        comparisons = comparison_paths(fit, cohort, paths)
        np.testing.assert_array_equal(comparisons,
                                      comparison_paths(fit_slice(poisoned, cohort), cohort, paths))
        fits[str(cohort)] = {'lastFitYear': int(fit.year.max()),
                             'labelAvailableBy': f'{cohort}-03-01',
                             'observationsByAge': fit.groupby('age').size().to_dict(),
                             'comparison': 'persistence' if cohort < 2018 else 'complete donors',
                             'comparisonPaths': len(comparisons),
                             'poisoningPassed': True}
        for pid, labels in panel.loc[panel.cohort == cohort].groupby('pfrId'):
            assert len(labels) == 5
            actual = labels.sort_values('age')[list(TARGETS)].to_dict('list')
            for name, realized in [('draftTime', False), ('realizedSensitivity', True)]:
                exposure = origin_games(cohort, realized)
                row = {'cohort': cohort, 'pfrId': pid, 'actualAnnual': actual,
                       'ageRank': {t: score(paths, exposure, sum(actual[t]), t) for t in TARGETS},
                       'comparison': {t: score(comparisons, exposure, sum(actual[t]), t) for t in TARGETS}}
                if cohort == 2018:
                    frozen_row = frozen_rows[pid]
                    for target in TARGETS:
                        assert actual[target] == [frozen_row[f'{target}{age}'] for age in range(1, 6)]
                    row['frozen2018'] = {
                        t: evaluate_distribution(np.array([donor_total(d, t) for d in donors]),
                                                 weights(donors, frozen_row['pooledRookieProbability']),
                                                 sum(actual[t]))
                        for t in TARGETS}
                rows[name].append(row)
    report = {'protocolCommit': 'e586b0e', 'draws': DRAWS, 'bootstrapResamples': 5000,
              'sourceCoverage': coverage, 'fits': fits,
              'sourceHashes': {p.relative_to(fy.R).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [Path(__file__).resolve(), fy.RAW / 'combine.csv', fy.RAW / 'games.csv',
                                         A / 'five_year_strict_2018.json', A / 'five_year_frozen_2018_predictions.csv',
                                         A / 'forecast_audit.json', A / 'forecast_audit.py',
                                         A / 'qb_five_year_hindcast.py', A / 'five_year.py',
                                         A / 'qb_rank_hindcast_PROTOCOL.md']},
              'unknownTargetIds': qbs.loc[qbs.pfr_id.isna() & qbs.season.isin(ORIGINS),
                                         ['season', 'player_name']].to_dict('records')}
    for name, assessed in rows.items():
        early = [r for r in assessed if r['cohort'] < 2018]
        later = [r for r in assessed if r['cohort'] >= 2018]
        report[name] = {'early': evaluate(early), 'later': evaluate(later),
                        'byCohort': {str(c): evaluate([r for r in assessed if r['cohort'] == c])
                                     for c in ORIGINS}}
    frozen_assessed = [r for r in rows['draftTime'] if r['cohort'] == 2018]
    assert set(frozen_rows) == {r['pfrId'] for r in frozen_assessed}
    report['frozen2018Baseline'] = {t: summarize([r['frozen2018'][t] for r in frozen_assessed])
                                    for t in TARGETS}
    for target in TARGETS:
        assert report['frozen2018Baseline'][target] == baseline_reference[target]
    checks = {}
    for target in TARGETS:
        for era in ('early', 'later'):
            checks[f'{era}{target}Crps'] = report['draftTime'][era]['pairedCrps'][target]['playerBootstrap95'][1] < 0
        candidate = report['draftTime']['byCohort']['2018']['ageRank'][target]['interval95']
        baseline = report['frozen2018Baseline'][target]['interval95']
        checks[f'2018{target}Coverage'] = candidate['coverage'] >= .90
        checks[f'2018{target}IntervalScore'] = candidate['meanIntervalScore'] <= baseline['meanIntervalScore']
    report['decision'] = {'criteria': checks, 'advance': all(checks.values()), 'promote': False}
    out.mkdir(exist_ok=True, parents=True)
    for filename, value in [('qb_rank_hindcast.json', report), ('qb_rank_hindcast_predictions.json', rows)]:
        (out / filename).write_text(json.dumps(value, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
