"""Run with RD_ROOT=/path/to/repo RD_QB_OUT=/path/to/results python this_file."""
from pathlib import Path
import os,json,unittest,sys,hashlib
import numpy as np

OUT=Path(os.environ.get('RD_QB_OUT',Path(__file__).parent))
ROOT=Path(os.environ['RD_ROOT'])
sys.path.insert(0,str(Path(__file__).parent))
import qb_five_year_hindcast as h
sys.path.insert(0,str(ROOT/'analytics'))
from forecast_audit import summarize,evaluate_distribution

class HindcastChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((OUT/'qb_five_year_hindcast.json').read_text())
        cls.rows=json.loads((OUT/'qb_five_year_hindcast_predictions.json').read_text())
    def test_scoring_equivalence(self):
        x=np.array([0.,200.,200.,900.,1050.])
        for actual in [0.,100.,2300.]:
            a=h.distribution(x,actual);b=evaluate_distribution(x,np.ones(len(x))/len(x),actual)
            for key in a:self.assertAlmostEqual(a[key],b[key])
    def test_cutoffs_and_selection(self):
        self.assertEqual(self.report['protocol']['selectionLabels'],2015)
        self.assertTrue(self.report['protocol']['selectionPoisoningPassed'])
        for r in self.report['origins']:
            self.assertEqual(r['latestFitOutcomeSeason'],r['cohort']-1)
            self.assertLess(r['latestFitLabelAvailableBy'],r['informationCutoff'])
            self.assertTrue(r['futureOutcomePoisoningPassed'])
            self.assertEqual(r['outcomeSeasons'],[r['cohort'],r['cohort']+4])
    def test_metrics_and_bootstrap_recompute(self):
        self.assertEqual(len(self.rows),32)
        self.assertEqual(len({r['pfrId'] for r in self.rows}),32)
        for kind in ['transition','persistence']:
            self.assertEqual(summarize([r[kind] for r in self.rows]),self.report['overall'][kind])
        self.assertEqual(h.bootstrap(self.rows),self.report['overall']['pairedCrps'])
    def test_actuals_are_unscaled_recorded_counts(self):
        for r in self.rows:
            self.assertEqual(r['transition']['actual'],sum(r['actualAnnual']))
            self.assertEqual(r['persistence']['actual'],sum(r['actualAnnual']))
            self.assertTrue(all(isinstance(x,int) for x in r['actualAnnual']))
    def test_no_promotion_and_hashes(self):
        self.assertFalse(self.report['runtimeChanged'])
        for path,sha in self.report['sourceHashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha)
        self.assertEqual(hashlib.sha256((OUT/'qb_five_year_hindcast.py').read_bytes()).hexdigest(),self.report['scriptSha256'])

if __name__=='__main__':unittest.main(verbosity=2)
