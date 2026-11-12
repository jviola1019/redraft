import importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss,mean_squared_error
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('redraft_models',ROOT/'analytics/train_models.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ModelValidation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.a=json.loads((ROOT/'analytics/model.json').read_text())
 def test_metrics_recomputed_from_holdout(self):
  p=pd.read_csv(ROOT/'analytics/outcomes/prospect_test_predictions.csv');self.assertEqual(sorted(p.season.unique()),[2016,2017]);self.assertAlmostEqual(brier_score_loss(p.y,p.selected_probability),self.a['prospect']['selectedTestMetrics']['brier'],places=12)
  t=pd.read_csv(ROOT/'analytics/outcomes/team_test_predictions.csv');key=self.a['team']['validation']['selected'];self.assertAlmostEqual(np.sqrt(mean_squared_error(t.margin,t.prediction)),self.a['team']['validation']['metrics'][key]['rmse'],places=12)
 def test_completed_label_availability(self):
  d=pd.read_csv(ROOT/'analytics/outcomes/rookie_snap_labels.csv');self.assertTrue((pd.to_datetime(d.label_available_by,utc=True)<pd.Timestamp(self.a['cutoff'])).all());self.assertLessEqual(d.season.max(),2017);self.assertEqual(int(d.y.sum()),int(d.snaps.ge(200).sum()))
 def test_feature_outcome_separation(self):
  d=pd.read_csv(ROOT/'analytics/features/combine_model_features.csv')
  for x in ['draft_year','draft_round','draft_ovr','draft_team','games','car_av','w_av','snaps','y']:self.assertNotIn(x,d.columns);self.assertNotIn(x,self.a['prospect']['features'])
 def test_chronological_partitions(self):
  p=self.a['prospect'];self.assertLess(p['trainCohorts'][1],p['validationCohorts'][0]);self.assertLess(p['validationCohorts'][1],p['testCohorts'][0]);self.assertLess(p['finalFitCohorts'][1],2018)
 def test_probabilities_ids_specialists(self):
  ps=self.a['prospect']['projections'];self.assertEqual(len(ps),375);self.assertEqual(len({p['prospectId'] for p in ps}),len(ps))
  for p in ps:
   if p['supported']:self.assertTrue(0<=p['roleProbability']<=1)
   else:self.assertIsNone(p['roleProbability'])
 def test_snap_coverage_before_zero_labels(self):
  for r in self.a['prospect']['snapCoverage'].values():self.assertEqual(r['gamesExpected'],256);self.assertEqual(r['gamesObserved'],256)
 def test_future_games_do_not_change_fit(self):
  read=pd.read_csv
  def poisoned(path,*args,**kwargs):
   d=read(path,*args,**kwargs)
   if Path(path).name=='games.csv':d.loc[d.season>=2018,['home_score','away_score']]=999999
   return d
  with patch.object(m.pd,'read_csv',side_effect=poisoned):t=m.fit_teams()
  for k in ['homeAdvantage','strengthCoefficient','meanTotal','seasonShockSd','gameMarginSd','initialStrength']:self.assertEqual(t[k],self.a['team'][k])
 def test_future_prospect_and_career_poisoning(self):
  read=pd.read_csv
  def poisoned(path,*args,**kwargs):
   d=read(path,*args,**kwargs)
   if Path(path).name=='combine.csv':d.loc[d.season>=2019,['wt','forty','bench','vertical']]=999999;d['career_mvp_awards']=999999
   return d
  with patch.object(m.pd,'read_csv',side_effect=poisoned):p=m.fit_prospects()
  self.assertEqual(p['selectedTestMetrics'],self.a['prospect']['selectedTestMetrics'])
  expected={(p['name'],p.get('school')):p for p in self.a['prospect']['projections'] if p['projectionSource']=='combine model'}
  for p in p['projections']:self.assertEqual(p['roleProbability'],expected[(p['name'],p['school'])]['roleProbability'])
 def test_residual_variance_identity(self):
  t=self.a['team'];self.assertAlmostEqual(2*t['seasonShockSd']**2+t['gameMarginSd']**2,t['residualMarginSd']**2,places=10);self.assertIn('do not apply persistence',t['simulationTransition'])
 def test_original_publication_unknown_is_explicit(self):
  d=pd.read_csv(ROOT/'analytics/features/combine_model_features.csv');self.assertTrue(d.original_available_at.isna().all());self.assertTrue(d.availability_status.str.contains('not archived').all())
 def test_coarsening_preserves_missingness_and_units(self):
  d=pd.DataFrame({'height':[72.,np.nan],'wt':[220.,np.nan],'forty':[4.41,np.nan],'bench':[22.,np.nan],'vertical':[34.,np.nan],'broad_jump':[121.,np.nan],'cone':[6.93,np.nan],'shuttle':[4.18,np.nan]});b=m.band(d);self.assertTrue(b.isna().equals(d.isna()));self.assertEqual(b.loc[0,'height'],72);self.assertEqual(b.loc[0,'wt'],225);self.assertAlmostEqual(b.loc[0,'forty'],4.4)
 def test_coarsening_metrics_recomputed(self):
  d=pd.read_csv(ROOT/'analytics/outcomes/coarsening_test_predictions.csv');c=json.loads((ROOT/'analytics/coarsening_comparison.json').read_text())
  for k,v in c['variants'].items():self.assertAlmostEqual(brier_score_loss(d.y,d[k]),v['brier'],places=12)
  self.assertEqual(c['test'],[2016,2017]);self.assertEqual(c['validation'],[2015,2015])
 def test_pooling_groups_use_features_only(self):
  d=pd.read_csv(ROOT/'analytics/features/pooling_candidates.csv');self.assertNotIn('y',d.columns);self.assertNotIn('snaps',d.columns)
  for _,g in d.groupby('pool_key'):
   self.assertGreaterEqual(len(g),5);self.assertEqual(g.season.nunique(),1);self.assertEqual(g.position.nunique(),1);self.assertAlmostEqual(np.round(g.raw_probability,6).mean(),g.pool_probability.iloc[0],places=12)
 def test_pooling_metrics_recomputed(self):
  d=pd.read_csv(ROOT/'analytics/outcomes/pooling_test_predictions.csv');r=json.loads((ROOT/'analytics/pooling_validation.json').read_text())
  self.assertEqual(len(d),613);self.assertAlmostEqual(brier_score_loss(d.y,d.pool_probability),r['metrics']['pooledMean']['brier'],places=12);self.assertFalse(r['groupingUsesLabels'])
 def test_pooling_unknowns_grouped_but_not_scored(self):
  r=json.loads((ROOT/'analytics/pooling_validation.json').read_text());self.assertGreater(r['allCandidatesGrouped'],r['evaluatedWithKnownLabels']);self.assertEqual(r['minimumGroupSize'],5)
if __name__=='__main__':unittest.main(verbosity=2)
