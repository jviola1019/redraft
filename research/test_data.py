import unittest,json,csv,collections,io,contextlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DataTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=json.loads((ROOT/'data/processed/scenario-2018.json').read_text())
 def test_independent_order_reconciliation(self):
  import reconcile_order
  with contextlib.redirect_stdout(io.StringIO()):reconcile_order.main()
  r=json.loads((ROOT/'data/clean/order_reconciliation.json').read_text());self.assertEqual(r['matchedSlots'],256);self.assertEqual(r['assetOwnershipErrors'],[])
 def test_original_round_lengths_and_compensatory(self):
  self.assertEqual(list(collections.Counter(p['round'] for p in self.d['picks']).values()),[32,32,36,37,37,44,38]);self.assertEqual(sum(p['compensatory'] for p in self.d['picks']),32)
 def test_outcomes_absent_from_prospect_schema(self):
  forbidden={'draft_ovr','draft_team','draft_round','w_av','games','probowls','allpro','to','pick','round','team','pfr_id','pfrId'};self.assertTrue(all(not forbidden.intersection(p) for p in self.d['prospects']))
 def test_same_name_players_remain_distinct(self):
  j=[p for p in self.d['prospects'] if p['name']=='Jordan Thomas'];self.assertEqual(len(j),2);self.assertEqual({p['college'] for p in j},{'Oklahoma','Mississippi State'});self.assertEqual(len({p['id'] for p in j}),2)
 def test_historical_name(self):
  self.assertEqual(sum(p['name']=='Darius Leonard' for p in self.d['prospects']),1);self.assertFalse(any(p['name']=='Shaquille Leonard' for p in self.d['prospects']))
 def test_initial_owner_not_actual_selection_owner(self):
  self.assertEqual(next(p['owner'] for p in self.d['picks'] if p['overall']==7),'TB');self.assertEqual(next(p['team'] for p in self.d['actualPicks'] if p['overall']==7),'BUF')
 def test_actual_reference_keys(self):
  ids={p['id'] for p in self.d['prospects']};actual=[p['prospectId'] for p in self.d['actualPicks']];self.assertEqual(len(actual),256);self.assertEqual(len(set(actual)),256);self.assertTrue(set(actual)<=ids)
 def test_actual_season_game_counts(self):
  for year in range(2017,2023):
   games=[g for g in self.d['games'] if g['season']==year and g['type']=='REG'];self.assertEqual(len(games),271 if year==2022 else 272 if year==2021 else 256);self.assertEqual(len({g['id'] for g in games}),len(games))
 def test_original_chart_tail_is_explicit_assumption(self):
  x=json.loads((ROOT/'data/processed/trade-values.json').read_text());self.assertEqual(len(x['values']),256);self.assertEqual(x['values'][0]['johnson'],3000);self.assertEqual(x['values'][223]['johnson'],2);self.assertIsNone(x['values'][224]['johnson']);self.assertEqual(x['values'][224]['basis'],'gameplay-tail-extension')
 def test_header_only_source_not_treated_as_training_rows(self):
  self.assertEqual(len(list(csv.DictReader(io.StringIO((ROOT/'data/raw/snap_counts_2012.csv').read_text())))),0)
 def test_snap_labels_cover_exact_completed_games_2013_to_2025(self):
  schedule=list(csv.DictReader(io.StringIO((ROOT/'data/raw/games.csv').read_text())))
  for year in range(2013,2026):
   with self.subTest(season=year):
    rows=list(csv.DictReader(io.StringIO((ROOT/f'data/raw/snap_counts_{year}.csv').read_text())))
    expected={r['game_id'] for r in schedule if r['season']==str(year) and r['game_type']=='REG' and r['home_score']!='' and r['away_score']!=''}
    self.assertEqual({r['game_id'] for r in rows if r['game_type']=='REG'},expected)
    self.assertTrue(all(r['pfr_player_id'] for r in rows))
    self.assertEqual(len({(r['game_id'],r['pfr_player_id'],r['team']) for r in rows}),len(rows))
 def test_noncombine_actuals_not_playable(self):
  ref=[p for p in self.d['prospects'] if p['eligibilitySource']=='retrospective-draft-record'];self.assertEqual(len(ref),39);self.assertFalse(any(p['playable'] for p in ref));self.assertEqual(sum(p['playable'] for p in self.d['prospects']),336)
 def test_all_playable_eligibility_independently_verified(self):
  import verify_invitees
  with contextlib.redirect_stdout(io.StringIO()):verify_invitees.main()
  r=json.loads((ROOT/'data/clean/eligibility_audit_2018.json').read_text());self.assertEqual(r['matched'],336);self.assertEqual(r['unmatched'],[])
 def test_no_duplicate_official_invitee_resolution(self):
  r=json.loads((ROOT/'data/clean/eligibility_audit_2018.json').read_text());self.assertEqual(len({(m['combineName'],m['combineCollege']) for m in r['matches']}),336)
 def test_identity_risk_recomputes_from_playable_population(self):
  from identity_risk import audit
  ps=[p for p in self.d['prospects'] if p['playable']];r=audit(ps,['position','college']);self.assertEqual(r['singletonProspects'],265);self.assertEqual(r['groups'],299)
if __name__=='__main__':unittest.main(verbosity=2)
