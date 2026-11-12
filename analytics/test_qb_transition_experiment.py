import hashlib,json,unittest
import numpy as np
import pandas as pd
import qb_transition_experiment as q

class TransitionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((q.A/'qb_transition_experiment.json').read_text())
        cls.panel=pd.read_csv(q.A/'qb_transition_panel.csv')
        cls.pairs=pd.read_csv(q.A/'qb_transition_pairs.csv')

    def test_cutoff_and_absence_semantics(self):
        self.assertEqual(self.pairs.year.max(),2017)
        self.assertTrue((pd.to_datetime(self.pairs.labelAvailableBy,utc=True)<pd.Timestamp('2018-04-26',tz='UTC')).all())
        absent=self.panel[self.panel.sourcePresence=='known-id-absent-complete-season']
        self.assertGreater(len(absent),0)
        self.assertTrue(absent.snaps.eq(0).all())
        self.assertTrue(absent.games.eq(0).all())
        self.assertGreater(self.report['data']['zeroToPositiveTransitions'],0)

    def test_selection_ignores_assessment_outcomes(self):
        original=q.fit_choice(self.pairs)
        poison=self.pairs.copy();poison.loc[poison.year>=2016,'next']=1000000
        self.assertEqual(q.fit_choice(poison),original)

    def test_distribution_weights_and_states(self):
        for experience in range(1,5):
            for prior in [0,1,199,200,599,600,1200]:
                for variant in [('state',0),('state+experience',5),('state',20)]:
                    w=q.transition_weights(self.pairs,prior,experience,variant)
                    self.assertAlmostEqual(w.sum(),1)
                    self.assertTrue((w>=0).all())
        self.assertEqual([q.state(n) for n in [0,1,199,200,599,600]],[0,1,1,2,2,3])

    def test_annual_metrics_recompute(self):
        d=pd.read_csv(q.A/'qb_transition_assessment_predictions.csv')
        stored=self.report['annualAssessment']['selected']
        self.assertAlmostEqual(d.crps.mean(),stored['meanCrps'],places=10)
        self.assertAlmostEqual(np.sqrt(np.mean((d.actual-d['mean'])**2)),stored['rmse'],places=10)
        self.assertTrue(d.year.isin([2016,2017]).all())

    def test_recombined_paths_have_only_empirical_annual_values(self):
        variant=tuple(self.report['selection']['candidates'][self.report['selection']['selected']]['variant'])
        paths=q.simulate_paths(self.panel,self.pairs,variant,.4,123)
        self.assertEqual(paths.shape,(q.DRAWS,5))
        self.assertTrue(np.isin(paths[:,0],self.panel[self.panel.experience==0].snaps).all())
        self.assertTrue(np.isin(paths[:,1:],self.pairs.next).all())
        np.testing.assert_equal(paths,q.simulate_paths(self.panel,self.pairs,variant,.4,123))

    def test_no_runtime_promotion_and_hashes_current(self):
        self.assertFalse(self.report['runtimeChanged'])
        self.assertIn('Research only',self.report['decision'])
        for name,expected in self.report['sourceHashes'].items():
            self.assertEqual(hashlib.sha256((q.ROOT/name).read_bytes()).hexdigest(),expected)

if __name__=='__main__':unittest.main(verbosity=2)
