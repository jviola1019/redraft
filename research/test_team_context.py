"""Source-conservation and historical-boundary tests for prior usage context."""
from pathlib import Path
import collections, csv, hashlib, json, unittest
from clean import tid
ROOT=Path(__file__).resolve().parents[1]

class ContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context=json.loads((ROOT/'data/clean/team_context_2018.json').read_text())
        with (ROOT/'data/raw/snap_counts_2017.csv').open() as f:
            cls.snaps=[r for r in csv.DictReader(f) if r['season']=='2017' and r['game_type']=='REG']

    def test_exact_artifact_and_input_hashes(self):
        manifest=json.loads((ROOT/'data/clean/team_context_source_manifest.json').read_text())
        self.assertEqual(manifest['artifactSha256'],hashlib.sha256((ROOT/manifest['artifact']).read_bytes()).hexdigest())
        for row in manifest['sources']:
            self.assertEqual(row['sha256'],hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest())

    def test_all_32_teams_reconcile_source_snap_totals(self):
        expected=collections.Counter()
        for row in self.snaps:
            expected[tid(row['team'])]+=int(row['offense_snaps'])+int(row['defense_snaps'])
        self.assertEqual({t['teamId'] for t in self.context['teams']},set(expected))
        self.assertEqual(len(expected),32)
        for team in self.context['teams']:
            self.assertEqual(sum(g['totalScrimmageSnaps'] for g in team['groups']),expected[team['teamId']])
            self.assertEqual(team['totalKnownScrimmageSnaps'],expected[team['teamId']])
            self.assertEqual(team['unclassifiedScrimmageSnaps'],0)
            self.assertTrue(all(g['complete'] for g in team['groups']))

    def test_contributor_stats_preserve_team_specific_sources(self):
        totals=collections.Counter();games=collections.defaultdict(set)
        for row in self.snaps:
            key=(tid(row['team']),row['pfr_player_id'])
            totals[key]+=int(row['offense_snaps'])+int(row['defense_snaps'])
            if sum(int(row[k]) for k in ['offense_snaps','defense_snaps','st_snaps'])>0:
                games[key].add(row['game_id'])
        for team in self.context['teams']:
            for group in team['groups']:
                for player in group['topContributors']:
                    key=(team['teamId'],player['playerId'])
                    self.assertEqual(player['scrimmageSnaps'],totals[key])
                    self.assertEqual(player['games'],len(games[key]))
                    self.assertLessEqual(player['games'],16)

    def test_missing_draft_day_facts_not_inferred(self):
        for team in self.context['teams']:
            for field in ['draftDayRoster','draftDayCoaches','scheme','rosterContinuity']:
                self.assertIsNone(team[field])
            self.assertEqual(team['observedThrough'],'2017-12-31')
            self.assertEqual(sum(c['games'] for c in team['priorHeadCoaches']),16)
            self.assertFalse(next(g for g in team['groups'] if g['group']=='ST')['policySupported'])
        self.assertIn('unavailable',self.context['metadata']['originalAvailability'])

    def test_depth_chart_units_are_not_schemes(self):
        quality=json.loads((ROOT/'data/clean/team_context_quality.json').read_text())
        self.assertEqual(set(quality['depthChartAudit']['formations']),{'Offense','Defense','Special Teams'})
        self.assertEqual(sum(quality['rosterJoinCounts'].values()),quality['teamPlayerObservations'])
        self.assertGreater(quality['rosterJoinCounts']['unresolved'],0)
        self.assertFalse(any('fuzzy' in j['method'] for j in quality['joins']))

if __name__=='__main__':unittest.main(verbosity=2)
