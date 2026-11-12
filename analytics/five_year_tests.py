import json,unittest
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];A=R/'analytics'
class FiveYearChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.strict=json.loads((A/'five_year_strict_2018.json').read_text());cls.research=json.loads((A/'five_year_research.json').read_text())
 def test_strict_labels_complete_by_cutoff(self):
  d=pd.read_csv(A/'five_year_strict_labels.csv');self.assertEqual(sorted(d.season.unique()),[2013]);self.assertTrue((pd.to_datetime(d.labelAvailableBy,utc=True)<pd.Timestamp(self.strict['cutoff'])).all());self.assertEqual(sorted(map(int,self.strict['sourceCoverage'])),list(range(2013,2018)))
 def test_donors_are_real_label_vectors(self):
  d=pd.read_csv(A/'five_year_strict_labels.csv');self.assertEqual(len(d),len(self.strict['donors']))
  for r,p in zip(d.itertuples(),self.strict['donors']):
   self.assertEqual(p['snaps'],[getattr(r,f'snaps{i}') for i in range(1,6)]);self.assertEqual(p['games'],[getattr(r,f'games{i}') for i in range(1,6)]);self.assertEqual(p['rookieRole'],p['snaps'][0]>=200)
 def test_missing_2012_not_used_as_zero(self):
  self.assertNotIn(2012,self.strict['cohorts']);self.assertFalse(self.strict['validation']['chronologicallyValidatedFor2018']);self.assertIn('header-only',self.strict['validation']['reason'])
 def test_rolling_label_availability(self):
  for row in self.research['rollingOriginTests']:
   self.assertLessEqual(max(row['donorCohorts']),row['forecastDraftYear']-5);self.assertLess(max(row['rookieClassifierCohorts']),row['forecastDraftYear'])
 def test_frozen_metrics_recompute(self):
  d=pd.read_csv(A/'five_year_frozen_2018_predictions.csv');actual=d[[f'snaps{i}' for i in range(1,6)]].sum(axis=1);r=self.research['frozen2018ProductionModel'];self.assertEqual(len(d),r['nTest']);self.assertIn('blind-g5-v1',r['rookieModelVersion']);self.assertAlmostEqual(np.sqrt(np.mean((actual-d.predictedTotalSnaps)**2)),r['metrics']['totalRMSE'],places=9);self.assertAlmostEqual(np.mean((actual>=d.lower80)&(actual<=d.upper80)),r['metrics']['totalInterval80']['coverage'],places=12)
 def test_retrospective_not_mislabeled_historical(self):self.assertIn('NOT a strict2017',self.research['cohortSplit']['warning'])
 def test_qb_support_limit_visible(self):self.assertEqual(self.strict['supportByPosition']['QB']['rookieRole'],3);self.assertTrue(any(x['position']=='QB' and x['metrics']['totalInterval95']['coverage']<.95 for x in self.research['frozen2018ProductionModel']['subgroups']))
if __name__=='__main__':unittest.main(verbosity=2)
