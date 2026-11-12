"""Screen candidate years for reconstructable ownership and complete outcomes."""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from clean import TEAMS, tid

ROOT = Path(__file__).resolve().parents[1]
DRAFT_DATES = {
    2018: ('04-26', '04-28'), 2019: ('04-25', '04-27'),
    2020: ('04-23', '04-25'), 2021: ('04-29', '05-01'),
    2022: ('04-28', '04-30'), 2023: ('04-27', '04-29'),
    2024: ('04-25', '04-27'), 2025: ('04-24', '04-26'),
}

def read(name):
    with (ROOT / 'data/raw' / name).open(newline='') as source:
        return list(csv.DictReader(source))

def reverse_ownership(year, picks, transactions):
    owners = {int(row['pick']): tid(row['team']) for row in picks}
    legal_teams = {team[0] for team in TEAMS}
    first, last = (f'{year}-{day}' for day in DRAFT_DATES[year])
    trades = defaultdict(list)
    issues = []
    for row in transactions:
        if first <= row['trade_date'] <= last and row['pick_season'] == str(year):
            trades[row['trade_date'], int(row['trade_id'])].append(row)
    for trade, assets in sorted(trades.items(), reverse=True):
        seen = set()
        for asset in assets:
            number = asset['pick_number']
            giver, receiver = tid(asset['gave']), tid(asset['received'])
            if not number.isdigit() or int(number) not in owners:
                issues.append({'trade': trade, 'pick': number, 'reason': 'unresolved pick'})
                continue
            pick = int(number)
            if pick in seen or giver not in legal_teams or receiver not in legal_teams or giver == receiver:
                issues.append({'trade': trade, 'pick': pick, 'reason': 'invalid asset transfer'})
                continue
            seen.add(pick)
            if owners[pick] != receiver:
                issues.append({'trade': trade, 'pick': pick, 'reason': 'receiver mismatch',
                               'recordedOwner': owners[pick], 'receiver': receiver})
            owners[pick] = giver
    return {'tradeGroups': len(trades), 'issues': issues,
            'candidateOwnerCounts': dict(sorted(Counter(owners.values()).items())),
            'candidateOwners': dict(sorted(owners.items()))}

TRADE_TRACKER_2025 = ('https://www.nfl.com/news/2025-nfl-draft-trade-tracker-'
                      'full-details-on-every-draft-related-move-since-start-of-new-league-year')
# Keys identify an asset row, including the player ID to distinguish reused pick numbers.
CORRECTIONS_2025 = {
    ('1918', '216', 'GordOl00'): {'pick_number': '179'},
    ('1925', '62', 'TrapOz00'): {'pick_number': '56'},
    ('1947', '209', 'McCoKy00'): {'pick_number': '181'},
    ('1949', '202', 'KingKo00'): {'pick_number': '201'},
    ('1952', '257', 'AshbJu00'): {'pick_number': '251'},
    ('1935', '130', 'RobiTy02'): {'pick_number': '111'},
    ('1938', '127', 'HuntJa03'): {'pick_number': '117'},
    ('1938', '127', 'TravJa00'): {'gave': 'LA', 'received': 'IND'},
    ('1938', '190', 'SmitTi02'): {'gave': 'LA', 'received': 'IND'},
}

def corrected_2025(transactions):
    repaired, found = [], set()
    for row in transactions:
        key = row['trade_id'], row['pick_number'], row['pfr_id']
        if key in CORRECTIONS_2025:
            if key in found:
                raise ValueError(f'Ambiguous correction: {key}')
            found.add(key)
            row = {**row, **CORRECTIONS_2025[key]}
        repaired.append(row)
    if found != CORRECTIONS_2025.keys():
        raise ValueError('Trade source changed. Recheck the 2025 corrections.')
    # Philadelphia sent two current picks back to Kansas City for No. 31.
    for number in ('32', '164'):
        if any(r['trade_id'] == '1922' and r['pick_number'] == number for r in repaired):
            raise ValueError(f'Source already contains trade 1922 pick {number}')
        repaired.append({'trade_id': '1922', 'trade_date': '2025-04-24',
                         'pick_season': '2025', 'pick_number': number,
                         'gave': 'PHI', 'received': 'KC'})
    return repaired

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', required=True, type=date.fromisoformat)
    parser.add_argument('--order-2025', type=Path, help='NFL order article JSON-LD snapshot')
    args = parser.parse_args()
    drafts, trades, combine, games = (read(f) for f in ('draft_picks.csv','trades.csv','combine.csv','games.csv'))
    complete = {int(row['season']) for row in games if row['game_type'] == 'SB'
                and row['home_score'] and row['away_score'] and row['gameday'] <= args.as_of.isoformat()}
    report = []
    for year in DRAFT_DATES:
        picks = [row for row in drafts if row['season'] == str(year)]
        window = list(range(year, year + 5))
        report.append({'draftYear': year, 'selections': len(picks),
                       'measurementRows': sum(row['season'] == str(year) for row in combine),
                       'rawOwnershipScreen': reverse_ownership(year, picks, trades),
                       'playable': year == 2018,
                       'completedOutcomeSeasons': [y for y in window if y in complete],
                       'unobservedOutcomeSeasons': [y for y in window if y not in complete]})
    picks_2025 = [row for row in drafts if row['season'] == '2025']
    repaired_trades = corrected_2025(trades)
    report[-1]['correctedOwnershipScreen'] = {
        'source': TRADE_TRACKER_2025,
        **reverse_ownership(2025, picks_2025, repaired_trades),
    }
    if args.order_2025:
        article = json.loads(args.order_2025.read_text())
        team_names = {name: team for team, name, *_ in TEAMS}
        team_names.update({'Las Vegas Raiders': 'OAK', 'Washington Commanders': 'WAS'})
        official = {}
        for number, label in re.findall(r'^\s*(\d+)\) ([^\n]+)', article['articleBody'], re.M):
            name = re.split(r' \(|\*', label.strip())[0].strip()
            if int(number) in official:
                raise ValueError(f'Duplicate official pick {number}')
            official[int(number)] = team_names[name]
        candidate = report[-1]['correctedOwnershipScreen']['candidateOwners']
        if candidate.keys() != official.keys():
            raise ValueError('Official snapshot pick coverage differs from reconstruction.')
        differences = [{'pick': pick, 'official': official[pick], 'replayed': owner}
                       for pick, owner in candidate.items() if owner != official[pick]]
        # The revised article reflects the four current picks from the Browns–Texans deal.
        snapshot_state = candidate.copy()
        for asset in repaired_trades:
            if asset['trade_id'] == '1918' and asset['pick_season'] == '2025':
                pick = int(asset['pick_number'])
                if snapshot_state[pick] != tid(asset['gave']):
                    raise ValueError(f'Unexpected starting owner for pick {pick}')
                snapshot_state[pick] = tid(asset['received'])
        report[-1]['orderSnapshotComparison'] = {
            'source': 'https://www.nfl.com/news/2025-nfl-draft-order-for-all-seven-rounds',
            'published': article.get('datePublished'), 'modified': article.get('dateModified'),
            'matches': len(official) - len(differences), 'differences': differences,
            'matchesAfterApplyingTrade1918': sum(snapshot_state[pick] == owner for pick, owner in official.items()),
        }
    print(json.dumps({'asOf': str(args.as_of), 'classes': report,
                      'limitations': [
                          'Raw reversal is a diagnostic and requires independent comparison with pre-draft orders.',
                          '2018 shipped with independently audited corrections excluded from this raw screen.',
                          'Measurement rows do not establish pre-draft eligibility. 2021 requires its official invite list.',
                          'A complete five-season outcome window does not establish causal validity.',
                      ]}, indent=2))

if __name__ == '__main__':
    main()
