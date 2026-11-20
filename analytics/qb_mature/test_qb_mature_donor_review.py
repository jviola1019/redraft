"""RD_ROOT=/repo RD_QB_OUT=/result python this_file"""
from pathlib import Path
import os,sys,json,hashlib,unittest
import numpy as np
OUT=Path(os.environ.get('RD_QB_OUT',Path(__file__).parent));ROOT=Path(os.environ['RD_ROOT'])
sys.path.insert(0,str(Path(__file__).parent));import qb_mature_donor_review as m
sys.path.insert(0,str(ROOT/'analytics'));from forecast_audit import summarize

class MatureChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((OUT/'qb_mature_donor_review.json').read_text())
        cls.rows=json.loads((OUT/'qb_mature_donor_predictions.json').read_text())
    def test_cutoffs(self):
        for x in self.r['origins']:
            self.assertLessEqual(max(x['donorCohorts']),x['origin']-5)
            self.assertLess(x['lastFitLabelAvailableBy'],x['informationCutoff'])
            self.assertEqual(x['lastFitOutcomeSeason'],x['origin']-1)
        self.assertTrue(self.r['futureCohortPoisoningPassed'])
    def test_coverage(self):
        self.assertEqual(len(self.r['sourceCoverage']),13)
        for x in self.r['sourceCoverage'].values():self.assertEqual(x['expectedGames'],x['observedGames'])
        self.assertEqual(len(self.rows),50)
        self.assertEqual(len({x['pfrId'] for x in self.rows}),50)
    def test_saved_metrics(self):
        for k in ['candidate','baseline']:self.assertEqual(summarize([r[k] for r in self.rows]),self.r['overall'][k])
        self.assertEqual(m.paired(self.rows),self.r['overall']['pairedCrps'])
    def test_unscaled_actuals(self):
        for x in self.rows:
            self.assertEqual(sum(x['actualAnnual']),x['candidate']['actual'])
            self.assertEqual(x['candidate']['actual'],x['baseline']['actual'])
    def test_sources_and_no_promotion(self):
        self.assertFalse(self.r['runtimeChanged'])
        self.assertEqual(hashlib.sha256((OUT/'PROTOCOL.md').read_bytes()).hexdigest(),self.r['protocolSha256'])
        self.assertEqual(hashlib.sha256((OUT/'qb_mature_donor_review.py').read_bytes()).hexdigest(),self.r['scriptSha256'])
        for path,sha in self.r['sourceHashes'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha)

if __name__=='__main__':unittest.main(verbosity=2)
