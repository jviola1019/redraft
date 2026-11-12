"""Build factual 2017 usage context. No April 2018 roster or scheme is inferred."""
from pathlib import Path
import argparse, collections, concurrent.futures, csv, datetime, hashlib, json, re, statistics
from clean import tid
from ingest import fetch

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ['QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'DB', 'ST']
SOURCE_FILES = {
    'snap_counts_2017.csv': 'https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2017.csv',
    'roster_2017.csv': 'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2017.csv',
    'games.csv': 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv',
    'depth_charts_2017.csv': 'https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_2017.csv',
    'dictionary_rosters.csv': 'https://raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_rosters.csv',
    'dictionary_depth_charts.csv': 'https://raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_depth_charts.csv',
}
REQUIRED = {
    'snap_counts_2017.csv': {'season','game_type','game_id','team','pfr_player_id','player','position','offense_snaps','defense_snaps','st_snaps'},
    'roster_2017.csv': {'season','team','pfr_id','full_name','position','week','game_type','status','birth_date'},
    'games.csv': {'season','game_type','game_id','gameday','home_score','away_score','home_team','away_team','home_coach','away_coach'},
    'depth_charts_2017.csv': {'season','game_type','week','formation','gsis_id','club_code'},
}

def read(name):
    with (ROOT/'data/raw'/name).open() as f:
        reader = csv.DictReader(f)
        missing = REQUIRED.get(name, set()) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{name}: missing required fields {sorted(missing)}')
        return list(reader)

def norm(value):
    return re.sub('[^a-z0-9]', '', value.lower())

def position_group(position):
    groups = {'OL':['C','G','T','OG','OT','OL'], 'DL':['DE','DT','NT','DL'],
              'LB':['LB','ILB','OLB','EDGE'], 'DB':['CB','FS','SS','S','DB'],
              'RB':['RB','FB'], 'ST':['K','P','LS']}
    for key, values in groups.items():
        if position in values:
            return key
    return position if position in GROUPS else None

def main(download=False):
    if download:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            manifest = list(executor.map(fetch, SOURCE_FILES.items()))
        (ROOT/'data/clean/team_context_source_manifest.json').write_text(json.dumps(manifest, indent=2))
    games = [g for g in read('games.csv') if g['season']=='2017' and g['game_type']=='REG' and g['home_score'] and g['away_score']]
    expected = {g['game_id'] for g in games}
    observed_through = max(g['gameday'] for g in games)
    assert observed_through=='2017-12-31' and len(expected)==256
    snaps = [r for r in read('snap_counts_2017.csv') if r['season']=='2017' and r['game_type']=='REG']
    assert {r['game_id'] for r in snaps} == expected
    assert len({(r['game_id'], r['pfr_player_id'], r['team']) for r in snaps}) == len(snaps)
    roster = read('roster_2017.csv')
    assert all(r['season']=='2017' for r in roster)
    depth = read('depth_charts_2017.csv')
    roster_by_id, roster_by_name = collections.defaultdict(list), collections.defaultdict(list)
    for row in roster:
        if row['pfr_id']:
            roster_by_id[row['pfr_id']].append(row)
        roster_by_name[(tid(row['team']), norm(row['full_name']))].append(row)
    players, team_games = {}, collections.defaultdict(set)
    for row in snaps:
        team = tid(row['team'])
        team_games[team].add(row['game_id'])
        key = (team, row['pfr_player_id'])
        assert row['pfr_player_id']
        player = players.setdefault(key, {'playerId':row['pfr_player_id'], 'name':row['player'], 'team':team,
            'games':set(), 'scrimmageSnaps':0, 'offenseSnaps':0, 'defenseSnaps':0,
            'specialTeamsSnaps':0, 'positions':collections.Counter()})
        offense, defense, special = (int(row[field]) for field in ['offense_snaps','defense_snaps','st_snaps'])
        assert min(offense, defense, special) >= 0
        if offense+defense+special > 0:
            player['games'].add(row['game_id'])
        player['scrimmageSnaps'] += offense+defense
        player['offenseSnaps'] += offense
        player['defenseSnaps'] += defense
        player['specialTeamsSnaps'] += special
        player['positions'][row['position']] += max(1, offense+defense+special)
    audit, match_counts, unknown = [], collections.Counter(), set()
    for player in players.values():
        player['position'] = player.pop('positions').most_common(1)[0][0]
        player['group'] = position_group(player['position'])
        player['games'] = len(player['games'])
        if player['group'] is None:
            unknown.add(player['position'])
        candidates, method = roster_by_id[player['playerId']], 'exact_pfr_id'
        if len(candidates) != 1:
            candidates = roster_by_name[(player['team'], norm(player['name']))]
            method = 'exact_normalized_name_and_team'
        if len(candidates) == 1:
            row = candidates[0]
            player['annualRosterObservation'] = {'sourcePlayerName':row['full_name'], 'sourceTeam':tid(row['team']),
                'sourcePosition':row['position'], 'lastObservedWeek':int(row['week']) if row['week'] else None,
                'lastObservedGameType':row['game_type'] or None, 'rawStatus':row['status'] or None, 'joinMethod':method}
        else:
            player['annualRosterObservation'], method = None, 'unresolved'
        match_counts[method] += 1
        audit.append({'team':player['team'], 'playerId':player['playerId'], 'name':player['name'], 'method':method, 'candidateCount':len(candidates)})
    result = []
    for team in sorted(team_games):
        own = [p for p in players.values() if p['team']==team]
        own_games = [g for g in games if tid(g['home_team'])==team or tid(g['away_team'])==team]
        assert len(own_games)==len(team_games[team])==16
        coaches = collections.Counter(g['home_coach'] if tid(g['home_team'])==team else g['away_coach'] for g in own_games)
        groups = []
        for key in GROUPS:
            members = [p for p in own if p['group']==key]
            total = sum(p['scrimmageSnaps'] for p in members)
            rank_field = 'specialTeamsSnaps' if key=='ST' else 'scrimmageSnaps'
            ranked = sorted(members, key=lambda p:(-p[rank_field],p['playerId']))
            groups.append({'group':key, 'totalScrimmageSnaps':total,
                'totalSpecialTeamsSnaps':sum(p['specialTeamsSnaps'] for p in members),
                'players200Plus':sum(p['scrimmageSnaps']>=200 for p in members),
                'positiveSnapPlayers':sum(p['scrimmageSnaps']>0 for p in members),
                'positiveSpecialTeamsPlayers':sum(p['specialTeamsSnaps']>0 for p in members),
                'largestPlayerShare':max((p['scrimmageSnaps'] for p in members),default=0)/total if total else None,
                'topContributors':[{k:v for k,v in p.items() if k not in ['team','group']} for p in ranked[:4]],
                'complete':True, 'policySupported':key!='ST' and bool(members), 'observedSeason':2017,
                'observedThrough':observed_through, 'source':SOURCE_FILES['snap_counts_2017.csv']})
        result.append({'teamId':team, 'priorSeason':2017, 'observedThrough':observed_through, 'regularGames':16,
            'observedPlayers':len(own), 'groups':groups,
            'totalKnownScrimmageSnaps':sum(p['scrimmageSnaps'] for p in own if p['group'] is not None),
            'unclassifiedScrimmageSnaps':sum(p['scrimmageSnaps'] for p in own if p['group'] is None),
            'priorHeadCoaches':[{'name':name or None,'games':count,'source':SOURCE_FILES['games.csv']} for name,count in coaches.most_common()],
            'annualRosterRows':sum(tid(r['team'])==team for r in roster), 'draftDayRoster':None,
            'draftDayCoaches':None, 'scheme':None, 'rosterContinuity':None, 'complete':True})
    assert len(result)==32 and not unknown
    references = {}
    for key in GROUPS:
        values = [g['players200Plus'] for t in result for g in t['groups'] if g['group']==key and g['policySupported']]
        references[key] = {'teamCount':len(values), 'medianPlayers200Plus':statistics.median(values) if values else None,
            'meanPlayers200Plus':statistics.mean(values) if values else None, 'minPlayers200Plus':min(values) if values else None,
            'maxPlayers200Plus':max(values) if values else None,
            'interpretation':'Observed 2017 usage depth; not April 2018 need, ability, scheme, or return probability.'}
    metadata = {'version':'prior-usage-2017-v1', 'verifiedDate':datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        'scenarioYear':2018, 'observedSeason':2017, 'observedThrough':observed_through,
        'informationCutoff':'2018-04-26T23:59:00Z',
        'originalAvailability':'Original per-row publication timestamps unavailable; historical observations reconstructed from current source releases.',
        'availabilityBasis':'Games and participation occurred in 2017; current releases lack original per-row publication timestamps. Retrospectively reconstructed prior-season observations, not a draft-day roster.',
        'sources':SOURCE_FILES, 'sourceHashes':{name:hashlib.sha256((ROOT/'data/raw'/name).read_bytes()).hexdigest() for name in SOURCE_FILES},
        'metrics':{
            'players200Plus':'Distinct team/player pairs with at least 200 regular-season offensive plus defensive snaps. A descriptive role threshold, not validated player quality.',
            'positiveSnapPlayers':'Distinct team/player pairs with positive offensive or defensive snaps.',
            'largestPlayerShare':'Largest individual scrimmage total divided by the position-group total, not share of team plays.',
            'totalKnownScrimmageSnaps':'Sum of offensive plus defensive player-snaps for all classified position groups, including any specialist scrimmage snaps. This counts player participation, not team plays. All 2017 source positions are classified; unclassified snaps are zero.',
            'positionGroup':'Each team/player is assigned to the position with the largest observed snap-weighted row total. All that team/player contribution is then grouped consistently; position changes are not modeled as separate roles.',
            'topContributors':'Four largest group contributors. Traded players can appear for multiple teams, with only each team contribution counted.',
            'annualRosterObservation':'Latest roster observation during the 2017 season; this does not establish April 2018 membership. A PFR identity can link a different last-observed team after a trade.'},
        'limitations':['No reconstructed April 2018 roster, free-agent departures, contracts, or roster continuity.',
            'No supported scheme inference; depth-chart formation labels are only Offense, Defense, and Special Teams.',
            'Prior head coaches are derived from 2017 games, not 2018 draft-day appointments.',
            'A small contributor count may reflect healthy entrenched starters rather than roster need.',
            'The 200-snap threshold is a descriptive convention; no empirical optimality is claimed.',
            'Roster joins use exact PFR IDs or unique normalized names and matching team. Unresolved matches remain null.',
            'Original publication times for retrospectively distributed rows are unavailable.']}
    artifact_path = ROOT/'data/clean/team_context_2018.json'
    artifact_path.write_text(json.dumps({'metadata':metadata,'teams':result,'leagueGroupReferences':references}, indent=2))
    manifest_path = ROOT/'data/clean/team_context_source_manifest.json'
    prior_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    sources_manifest = prior_manifest['sources'] if isinstance(prior_manifest, dict) else prior_manifest
    manifest_path.write_text(json.dumps({'artifact':'data/clean/team_context_2018.json',
        'artifactSha256':hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        'artifactVersion':metadata['version'], 'verifiedDate':metadata['verifiedDate'],
        'sources':sources_manifest}, indent=2))
    depth_regular = [r for r in depth if r['game_type']=='REG']
    quality = {'version':metadata['version'], 'verifiedDate':metadata['verifiedDate'], 'teams':len(result), 'regularGames':len(expected),
        'teamGameObservations':sum(t['regularGames'] for t in result), 'teamPlayerObservations':len(players),
        'unclassifiedPositions':sorted(unknown), 'rosterRows':len(roster),
        'rosterMissingPfrIds':sum(not r['pfr_id'] for r in roster), 'rosterMissingBirthDates':sum(not r['birth_date'] for r in roster),
        'rosterJoinCounts':dict(match_counts), 'rosterStatusCounts':dict(collections.Counter(r['status'] for r in roster)),
        'depthChartAudit':{'rows':len(depth), 'regularRows':len(depth_regular), 'formations':dict(collections.Counter(r['formation'] for r in depth)),
            'regularWeeks':sorted({int(r['week']) for r in depth_regular if r['week']}),
            'teams':len({tid(r['club_code']) for r in depth_regular}), 'missingGsisIds':sum(not r['gsis_id'] for r in depth),
            'warning':'Formation describes units only. REG week 18 records occur despite the 17-week 2017 season. Current dictionary describes a newer schema than this snapshot. Not used for scheme or April roster.'}, 'joins':audit}
    (ROOT/'data/clean/team_context_quality.json').write_text(json.dumps(quality, indent=2))
    print(json.dumps({k:v for k,v in quality.items() if k!='joins'}, indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--download', action='store_true')
    main(parser.parse_args().download)
