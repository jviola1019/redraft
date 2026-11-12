"""Fresh executable analytical-schema checks. All fixture data is synthetic, test-only."""
import pathlib,sqlite3,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class WarehouseTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');self.db.executescript((ROOT/'docs/warehouse/001_analytical_schema.sql').read_text())
  self.db.executescript("""
  INSERT INTO data_sources VALUES('src','test','https://example.invalid','test-only','permitted','2026-11-02');
  INSERT INTO source_documents VALUES('doc','src','https://example.invalid','2018-04-01','2026-11-02','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','verified');
  INSERT INTO dataset_versions VALUES('d1','2026-11-02','h','v1','passed'),('d2','2026-11-02','h2','v1','passed');
  INSERT INTO teams VALUES('A','A'),('B','B'); INSERT INTO colleges VALUES('C','Test College');
  INSERT INTO players VALUES('P','Test Player',NULL),('Q','Baseline Player',NULL);
  INSERT INTO draft_classes VALUES(2018,'2018-04-26','2018-04-25','d1');
  INSERT INTO prospects VALUES('p','P',2018,'C','QB','2018-01-01','test-only',1),('q','Q',2018,'C','WR',NULL,'baseline-only',0);
  INSERT INTO historical_draft_picks VALUES('pick1',2018,1,1,'A',NULL,NULL,0,0,NULL),('pick2',2018,1,2,'B',NULL,NULL,0,0,NULL);
  INSERT INTO model_versions VALUES('m1','d1','2018-04-01','2018-01-01','h','test-only');
  INSERT INTO users VALUES('u','2026-11-02');
  INSERT INTO disclosure_policies VALUES('blind-v1','historical','{}','2026-11-02');
  INSERT INTO game_runs VALUES('g','u','historical',2018,'A','seed','d1','m1','engine1','blind-v1','{}',NULL,0,'drafting');
  INSERT INTO game_pick_assets VALUES('g','pick1','A'),('g','pick2','B');
  INSERT INTO feature_definitions VALUES('forty','v1','forty time','seconds','raw');
  """)
 def reject(self,sql,args=()):
  with self.assertRaises(sqlite3.IntegrityError):self.db.execute(sql,args)
 def test_foreign_key_integrity(self):self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_unknown_player_reference(self):self.reject("INSERT INTO player_identifiers VALUES('x','y','missing','exact')")
 def test_round_bounds(self):self.reject("INSERT INTO historical_draft_picks VALUES('bad',2018,8,3,'A',NULL,NULL,0,0,NULL)")
 def test_unique_pick(self):self.reject("INSERT INTO historical_draft_picks VALUES('dup',2018,1,1,'A',NULL,NULL,0,0,NULL)")
 def test_ownership_intervals(self):
  self.db.execute("INSERT INTO draft_pick_ownership VALUES('pick1','2018-01-01','2018-02-01','A','doc')");self.db.execute("INSERT INTO draft_pick_ownership VALUES('pick1','2018-02-01',NULL,'B','doc')");self.reject("INSERT INTO draft_pick_ownership VALUES('pick1','2018-01-15','2018-02-15','B','doc')")
 def test_ownership_update(self):
  self.db.execute("INSERT INTO draft_pick_ownership VALUES('pick1','2018-01-01','2018-02-01','A','doc')");self.db.execute("INSERT INTO draft_pick_ownership VALUES('pick1','2018-02-01',NULL,'B','doc')");self.reject("UPDATE draft_pick_ownership SET valid_to='2018-02-02' WHERE valid_from='2018-01-01'")
 def test_future_feature(self):self.reject("INSERT INTO feature_values VALUES('p','forty','v1','d1',4.4,NULL,'2018-03-01','2019-01-01','2018-04-25','doc')")
 def test_future_training_label(self):self.reject("INSERT INTO model_versions VALUES('bad','d1','2018-04-01','2019-01-01','h','test-only')")
 def test_model_training_cutoff(self):self.reject("INSERT INTO model_predictions VALUES('pred','m1','p','2017-04-01','role',0.5,0.2,0.8)")
 def test_missing_distinct_from_zero(self):
  self.db.execute("INSERT INTO combine_results VALUES('p','forty',NULL,'seconds','not_measured',NULL,NULL,'doc')");self.reject("INSERT INTO combine_results VALUES('p','bench',0,'reps','not_reported',NULL,NULL,'doc')")
 def test_duplicate_selected_player(self):
  self.db.execute("INSERT INTO game_draft_picks VALUES('g','pick1','A','p','2018-04-26')");self.reject("INSERT INTO game_draft_picks VALUES('g','pick2','B','p','2018-04-26')")
 def test_wrong_owner(self):self.reject("INSERT INTO game_draft_picks VALUES('g','pick1','B','p','2018-04-26')")
 def test_baseline_only_not_selectable(self):self.reject("INSERT INTO game_draft_picks VALUES('g','pick1','A','q','2018-04-26')")
 def test_selected_asset_locked(self):
  self.db.execute("INSERT INTO game_draft_picks VALUES('g','pick1','A','p','2018-04-26')");self.reject("UPDATE game_pick_assets SET owner_team_id='B' WHERE pick_id='pick1'")
 def test_simulation_version_link(self):self.reject("INSERT INTO simulation_runs VALUES('s','g','alternate',0,'seed','m1','d2','{}','pending')")
 def test_replicate_unique(self):
  self.db.execute("INSERT INTO simulation_runs VALUES('s','g','alternate',0,'seed','m1','d1','{}','pending')");self.reject("INSERT INTO simulation_runs VALUES('s2','g','alternate',0,'seed','m1','d1','{}','pending')")
 def test_daily_fixed_and_unique(self):
  self.db.execute("INSERT INTO daily_challenges VALUES('2026-11-02','{}','d1','m1','e1','blind-v1','hash','s1',256,'now')");self.reject("UPDATE daily_challenges SET scenario_json='changed'")
  self.db.execute("INSERT INTO daily_attempts VALUES('2026-11-02','u','g',NULL)");self.reject("INSERT INTO daily_attempts VALUES('2026-11-02','u','g',NULL)")
  self.db.execute("INSERT INTO daily_leaderboard_entries VALUES('2026-11-02','u',50,'{}','s1','hash')");self.reject("UPDATE daily_leaderboard_entries SET score=100")
 def test_public_id_mapping_one_to_one(self):
  self.db.execute("INSERT INTO game_public_prospect_ids VALUES('g','random-public','p')");self.reject("INSERT INTO game_public_prospect_ids VALUES('g','random-public','q')");self.reject("INSERT INTO game_public_prospect_ids VALUES('g','another-public','p')")
 def test_disclosure_policy_fixed(self):self.reject("UPDATE disclosure_policies SET field_rules_json='changed'")
 def test_no_self_transfer(self):self.reject("INSERT INTO game_trades VALUES('t','g','A','A',1,'2018-04-26')")
if __name__=='__main__':unittest.main(verbosity=2)
