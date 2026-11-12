"""Compare pre-season scoring and shutout forecasts with forward-only data."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/raw/games.csv'

def season_data(as_of):
    seasons = defaultdict(list)
    bowls = set()
    with SOURCE.open(newline='') as source:
        for row in csv.DictReader(source):
            if not row['home_score'] or not row['away_score'] or row['gameday'] > as_of.isoformat():
                continue
            year = int(row['season'])
            if row['game_type'] == 'SB':
                bowls.add(year)
            if row['game_type'] == 'REG':
                seasons[year].append((int(row['home_score']), int(row['away_score'])))
    return {year: games for year, games in seasons.items() if year in bowls}

def moments(games):
    return {
        'pointsPerGame': mean(home + away for home, away in games),
        'zeroScoreRate': mean(score == 0 for game in games for score in game),
    }

def evaluate(seasons, years, window):
    rows = []
    for year in years:
        if year not in seasons:
            continue
        training = [y for y in sorted(seasons) if y < year]
        if window:
            training = training[-window:]
        if not training:
            raise ValueError(f'No completed training seasons before {year}')
        historical_games = [game for y in training for game in seasons[y]]
        forecast, actual = moments(historical_games), moments(seasons[year])
        rows.append({'year': year, 'fitSeasons': training,
                     'forecast': forecast, 'actual': actual, 'games': len(seasons[year])})
    return rows

def errors(rows):
    return {key: mean(abs(row['forecast'][key] - row['actual'][key]) for row in rows)
            for key in ('pointsPerGame', 'zeroScoreRate')}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', type=date.fromisoformat, required=True)
    args = parser.parse_args()
    seasons = season_data(args.as_of)
    windows = [3, 5, 10, None]
    selection = {window: errors(evaluate(seasons, range(2005, 2013), window)) for window in windows}
    choices = {target: min(windows, key=lambda window: selection[window][target])
               for target in ('pointsPerGame', 'zeroScoreRate')}
    assessment = {str(window): errors(evaluate(seasons, range(2013, 2018), window)) for window in windows}
    audits = {str(window): evaluate(seasons, range(2018, 2026), window) for window in windows}
    print(json.dumps({
        'asOf': args.as_of.isoformat(),
        'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'method': 'Game-weighted empirical rates from completed prior seasons. MAE across season origins.',
        'selection2005Through2012': {str(window): values for window, values in selection.items()},
        'selectedWindows': choices,
        'assessment2013Through2017': assessment,
        'reusedEvaluation2018Through2025': audits,
        'reusedEvaluationMAE': {window: errors(records) for window, records in audits.items()},
        'limitations': 'Aggregate benchmarks only. Runtime team/game distributions, player uncertainty, ranking sensitivity and causal validity require separate evidence.',
    }, indent=2))

if __name__ == '__main__':
    main()
