"""Audit recorded draft and playoff files, separately from playable scenarios."""
import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def rows(name):
    with (ROOT / 'data' / 'raw' / name).open(newline='') as source:
        return list(csv.DictReader(source))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    drafts, schedules = rows('draft_picks.csv'), rows('games.csv')
    records, failures = [], []
    for year in range(2018, args.as_of.year + 1):
        picks = [r for r in drafts if r['season'] == str(year)]
        numbers = sorted(int(r['pick']) for r in picks)
        if not numbers or numbers != list(range(1, len(numbers) + 1)):
            failures.append(f'{year}: missing or duplicate overall selections')
        if {int(r['round']) for r in picks} != set(range(1, 8)):
            failures.append(f'{year}: incomplete rounds')
        games = [r for r in schedules if r['season'] == str(year)
                 and date.fromisoformat(r['gameday']) <= args.as_of
                 and r['home_score'] and r['away_score']]
        postseason = [r for r in games if r['game_type'] in ('WC', 'DIV', 'CON', 'SB')]
        counts = Counter(r['game_type'] for r in postseason)
        champions = [r for r in postseason if r['game_type'] == 'SB']
        complete = len(champions) == 1
        if year < args.as_of.year and not complete:
            failures.append(f'{year}: missing completed Super Bowl')
        if complete:
            expected = {'WC': 6 if year >= 2020 else 4, 'DIV': 4, 'CON': 2, 'SB': 1}
            if counts != expected:
                failures.append(f'{year}: postseason round totals differ from format')
            previous_winners = set()
            for stage in ('WC', 'DIV', 'CON', 'SB'):
                round_games = [r for r in postseason if r['game_type'] == stage]
                teams = [r[side] for r in round_games for side in ('home_team', 'away_team')]
                if len(set(teams)) != len(teams) or (stage != 'WC' and not previous_winners <= set(teams)):
                    failures.append(f'{year} {stage}: invalid bracket progression')
                if stage in ('CON', 'SB') and previous_winners != set(teams):
                    failures.append(f'{year} {stage}: unexpected advancing teams')
                previous_winners = set()
                for game in round_games:
                    home, away = int(game['home_score']), int(game['away_score'])
                    if home == away:
                        failures.append(f"{game['game_id']}: postseason tie")
                    previous_winners.add(game['home_team'] if home > away else game['away_team'])
        records.append({
            'draftYear': year, 'recordedPicks': len(picks), 'scenarioDatasetAvailable': (ROOT / 'data/processed' / f'scenario-{year}.json').exists(),
            'recordedRegularGames': sum(r['game_type'] == 'REG' for r in games),
            'recordedPostseason': dict(counts),
            'fiveYearWindow': [{'season': season, 'status': (
                'completed' if any(r['season'] == str(season) and r['game_type'] == 'SB'
                    and r['home_score'] and date.fromisoformat(r['gameday']) <= args.as_of
                    for r in schedules)
                else 'incomplete' if season <= args.as_of.year else 'future')
                } for season in range(year, year + 5)],
        })
    print(json.dumps({'asOf': str(args.as_of), 'scope': 'Recorded files and observed bracket advancement',
                      'classes': records, 'failures': failures}, indent=2))
    return bool(failures)

if __name__ == '__main__':
    raise SystemExit(main())
