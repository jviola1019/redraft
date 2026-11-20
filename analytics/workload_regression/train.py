"""Train and evaluate the REDRAFT veteran workload projection."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, SplineTransformer, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
FIRST_SNAP_SEASON = 2013
LAST_SNAP_SEASON = 2025
FIRST_DRAFT = 2018
LAST_DRAFT = 2026
THRESHOLD = 500
VERSION = 'veteran-nfl-workload-v1'
NUMERIC = ['logSnaps', 'games', 'logPreviousSnaps', 'previousGames', 'logSnapChange', 'recentShare']
BASE_NUMERIC = ['logSnaps']
CANDIDATE = 'positionTrajectoryCurve'


def read_data():
    raw = ROOT / 'data/raw'
    schedule = pd.read_csv(raw / 'games.csv', usecols=[
        'game_id', 'season', 'game_type', 'gameday', 'home_score', 'away_score',
    ])
    schedule = schedule[(schedule.game_type == 'REG') & schedule.home_score.notna() & schedule.away_score.notna()]
    columns = ['game_id', 'season', 'game_type', 'pfr_player_id', 'position', 'team',
               'offense_snaps', 'defense_snaps']
    yearly = []
    audit = {}
    for year in range(FIRST_SNAP_SEASON, LAST_SNAP_SEASON + 1):
        path = raw / f'snap_counts_{year}.csv'
        snaps = pd.read_csv(path, usecols=columns)
        snaps = snaps[snaps.game_type == 'REG']
        games = schedule[schedule.season == year][['game_id', 'gameday']]
        if not (snaps.season == year).all() or set(games.game_id) != set(snaps.game_id):
            raise ValueError(f'Regular season {year} does not match the completed schedule')
        if snaps.duplicated(['game_id', 'pfr_player_id']).any():
            raise ValueError(f'Unexpected duplicate player/game rows in {year}')
        if snaps[['pfr_player_id', 'team', 'offense_snaps', 'defense_snaps']].isna().any().any():
            raise ValueError(f'Broken player, team, or workload identity in {year}')
        if snaps[['offense_snaps', 'defense_snaps']].lt(0).any().any():
            raise ValueError(f'Negative snaps in {year}')
        audit[year] = {'regularGames': len(games), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        yearly.append(snaps.merge(games, on='game_id', validate='many_to_one'))
    return pd.concat(yearly, ignore_index=True), audit


def summarize(snaps):
    ordered = snaps.sort_values(['season', 'pfr_player_id', 'gameday', 'game_id']).copy()
    keys = ['season', 'pfr_player_id']
    # Include listed special-teams appearances in games played if the player
    # also qualifies for the cohort through offensive or defensive work.
    order_from_end = ordered.groupby(keys).cumcount(ascending=False)
    ordered['recentOffense'] = ordered.offense_snaps.where(order_from_end < 4, 0)
    ordered['recentDefense'] = ordered.defense_snaps.where(order_from_end < 4, 0)
    summary = ordered.groupby(keys).agg(
        offense=('offense_snaps', 'sum'), defense=('defense_snaps', 'sum'), games=('game_id', 'size'),
        recentOffense=('recentOffense', 'sum'), recentDefense=('recentDefense', 'sum'),
    )
    last = ordered.drop_duplicates(keys, keep='last').set_index(keys)[['position', 'team', 'gameday']]
    summary['snaps'] = summary[['offense', 'defense']].max(axis=1)
    recent_snaps = np.where(summary.offense >= summary.defense, summary.recentOffense, summary.recentDefense)
    summary['recentShare'] = np.divide(recent_snaps, summary.snaps, out=np.zeros(len(summary)),
                                       where=summary.snaps > 0)
    return summary.join(last).reset_index()


def cohort(summary, year, cutoff, include_outcome=False):
    """Build one year's forecast features and, for historical evaluation, labels."""
    last = summary[(summary.season == year - 1) & (summary.snaps > 0)].copy()
    previous = summary[summary.season == year - 2]
    if last.empty or previous.empty or last.gameday.max() >= cutoff or previous.gameday.max() >= cutoff:
        raise ValueError(f'Missing or post-cutoff source history for draft {year}')
    last = last.merge(previous[['pfr_player_id', 'snaps', 'games']], on='pfr_player_id', how='left',
                      suffixes=('', '_previous'), validate='one_to_one')
    last['position'] = last.position.fillna('UNKNOWN')
    last['logSnaps'] = np.log1p(last.snaps)
    last['logPreviousSnaps'] = np.log1p(last.snaps_previous.fillna(0))
    last['previousGames'] = last.games_previous.fillna(0).astype(int)
    last['logSnapChange'] = last.logSnaps - last.logPreviousSnaps
    if include_outcome:
        following = summary[summary.season == year]
        if following.empty:
            raise ValueError(f'No complete target season for draft {year}')
        next_snaps = following.set_index('pfr_player_id').snaps
        last['outcome'] = last.pfr_player_id.map(next_snaps).fillna(0).ge(THRESHOLD).astype(int)
        last.attrs['latestOutcomeDate'] = following.gameday.max()
    return last


def run_model(train, forecast, numeric, flexible=False):
    features = [('position', OneHotEncoder(handle_unknown='ignore'), ['position'])]
    if flexible:
        snap_knots = np.log1p(np.array([0, 30, 100, 300, 500, 700, 1000, 1300])).reshape(-1, 1)
        features.append(('snapCurve', SplineTransformer(knots=snap_knots, degree=2), ['logSnaps']))
        numeric = [field for field in numeric if field != 'logSnaps']
    if numeric:
        features.append(('numeric', StandardScaler(), numeric))
    transformers = ColumnTransformer(features)
    model = make_pipeline(transformers, LogisticRegression(C=1, max_iter=1000))
    model.fit(train, train.outcome)
    return model.predict_proba(forecast)[:, 1]


def historical_rate(train, forecast, field):
    rates = train.groupby(field).outcome.agg(['sum', 'size'])
    smoothed = (rates['sum'] + 0.5) / (rates['size'] + 1)
    return forecast[field].map(smoothed).fillna(train.outcome.mean()).to_numpy()


def metrics(predictions, outcome):
    return {
        'brier': round(brier_score_loss(outcome, predictions), 6),
        'logLoss': round(log_loss(outcome, predictions, labels=[0, 1]), 6),
        'auc': round(roc_auc_score(outcome, predictions), 6),
        'predictedRate': round(float(predictions.mean()), 6),
        'observedRate': round(float(outcome.mean()), 6),
    }


def reliability(predictions, outcome):
    table = pd.DataFrame({'predictions': predictions, 'outcome': outcome})
    table['range'] = pd.cut(table.predictions, np.linspace(0, 1, 11), include_lowest=True)
    bins = []
    for bounds, group in table.groupby('range', observed=False):
        if group.empty:
            continue
        bins.append({
            'upperBound': round(float(bounds.right), 1),
            'players': len(group),
            'meanProbability': round(float(group.predictions.mean()), 6),
            'observedRate': round(float(group.outcome.mean()), 6),
        })
    return bins


def by_team(forecast, teams):
    """Group forecasts by prior affiliation. These groups are never roster assignments."""
    output = []
    aliases = {'OAK': 'LV', 'SD': 'LAC', 'STL': 'LAR', 'LA': 'LAR', 'LV': 'OAK'}
    for prior_team, rows in forecast.groupby('team'):
        team = prior_team if prior_team in teams else aliases.get(prior_team)
        if team not in teams:
            raise ValueError(f'Unknown prior team code {prior_team}')
        positions = {}
        for position, group in rows.groupby('position'):
            positions[position] = [len(group), round(float(group.probability.sum()), 3)]
        high_usage = rows.loc[rows.prior500]
        output.append({
            'teamId': team, 'lastObservedTeamCode': prior_team, 'positions': positions,
            'priorHighUsage': len(high_usage),
            'expectedHighUsageAnywhere': round(float(high_usage.probability.sum()), 3),
        })
    if len({item['teamId'] for item in output}) != len(teams):
        raise ValueError('Team mismatch in workload projection')
    return sorted(output, key=lambda item: item['teamId'])


def write_json(filename, result, compact=False):
    options = {'separators': (',', ':')} if compact else {'indent': 2}
    (OUTPUT / filename).write_text(json.dumps(result, allow_nan=False, **options) + '\n')


def main():
    snaps, audit = read_data()
    summary = summarize(snaps)
    completed = {}
    annual = {}
    all_predictions = []
    projections = {}
    for year in range(FIRST_SNAP_SEASON + 2, LAST_DRAFT + 1):
        scenario = ROOT / f'data/processed/scenario-{year}.json'
        metadata = json.loads(scenario.read_text()) if scenario.exists() else None
        cutoff = metadata['metadata']['informationCutoff'][:10] if metadata else f'{year}-03-01'
        forecast = cohort(summary, year, cutoff, include_outcome=False)
        forecast['prior500'] = forecast.snaps.ge(THRESHOLD)
        if year >= FIRST_DRAFT:
            if metadata is None:
                raise ValueError(f'Missing draft scenario {year}')
            if any(rows.attrs['latestOutcomeDate'] >= cutoff for rows in completed.values()):
                raise ValueError(f'Targets unavailable at draft cutoff {cutoff}')
            train = pd.concat(completed.values(), ignore_index=True)
            p = {
                'positionRate': historical_rate(train, forecast, 'position'),
                'prior500Rate': historical_rate(train, forecast, 'prior500'),
                'positionLastSnaps': run_model(train, forecast, BASE_NUMERIC),
                'positionTrajectory': run_model(train, forecast, NUMERIC),
                'positionLastSnapsCurve': run_model(train, forecast, BASE_NUMERIC, flexible=True),
                'positionTrajectoryCurve': run_model(train, forecast, NUMERIC, flexible=True),
            }
            forecast['probability'] = p[CANDIDATE]
            projections[year] = {
                'informationCutoff': metadata['metadata']['informationCutoff'],
                'latestRegularSeasonGame': forecast.gameday.max(),
                'trainedThroughOutcomeSeason': max(completed),
                'population': 'Prior-season offense/defense contributors across all teams',
                'memberships': 'Prior-season team groups; draft-day membership unverified',
                'teams': by_team(forecast, {team['id'] for team in metadata['teams']}),
            }
        if year <= LAST_SNAP_SEASON:
            labeled = cohort(summary, year, cutoff, include_outcome=True)
            labeled['prior500'] = labeled.snaps.ge(THRESHOLD)
            if year >= FIRST_DRAFT:
                if not forecast.pfr_player_id.equals(labeled.pfr_player_id):
                    raise ValueError('Forecast/label identity mismatch')
                outcome = labeled.outcome.to_numpy()
                annual[year] = {
                    'trainingRows': len(train), 'evaluationRows': len(forecast),
                    'models': {name: metrics(probabilities, outcome) for name, probabilities in p.items()},
                }
                all_predictions.append(pd.DataFrame({**p, 'outcome': outcome, 'position': forecast.position, 'prior500': forecast.prior500}))
            completed[year] = labeled
    pooled = pd.concat(all_predictions, ignore_index=True)
    model_metrics = {model: metrics(pooled[model], pooled.outcome) for model in p}
    model_reliability = {model: reliability(pooled[model], pooled.outcome) for model in p}
    for model, bins in model_reliability.items():
        model_metrics[model]['expectedCalibrationError'] = round(sum(
            b['players'] * abs(b['meanProbability'] - b['observedRate']) for b in bins
        ) / len(pooled), 6)
    high_usage = pooled[pooled.prior500]
    write_json('results.json', {
        'version': VERSION, 'heldoutRows': len(pooled), 'heldoutYears': list(annual),
        'yearlyResults': annual, 'pooledResults': model_metrics, 'reliability': model_reliability,
        'curvedModelsExploratory': True,
        'priorHighUsageRows': len(high_usage),
        'priorHighUsageResults': {model: metrics(high_usage[model], high_usage.outcome) for model in p},
        'priorHighUsageReliability': reliability(high_usage[CANDIDATE], high_usage.outcome),
        'inputAudit': audit,
        'scheduleSha256': hashlib.sha256((ROOT / 'data/raw/games.csv').read_bytes()).hexdigest(),
    })
    write_json('projections.json', {
        'version': VERSION, 'method': CANDIDATE, 'thresholdPrimarySideSnaps': THRESHOLD,
        'evidenceStatus': 'Exploratory chronological evaluation; staging preview',
        'scope': 'Projected across all NFL teams. Draft-day roster status unverified.',
        'positionValueOrder': ['priorSeasonContributors', 'expectedContributorsReachingThresholdAnywhere'],
        'drafts': projections,
    }, compact=True)


if __name__ == '__main__':
    main()
