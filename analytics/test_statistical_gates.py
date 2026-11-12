"""Numerical and leakage checks for the Nov4 analytical audit."""
import contextlib
import io
import json
import unittest
import numpy as np
import pandas as pd
import forecast_audit as fa
import scoring_recalibration as sr
import statistical_gates as gates


class StatisticalAuditChecks(unittest.TestCase):
    def test_exact_crps_point_forecast(self):
        result=fa.evaluate_distribution(np.array([10.]),np.array([1.]),14.)
        self.assertEqual(result['mean'],10.)
        self.assertEqual(result['crps'],4.)
        self.assertAlmostEqual(result['intervalScore80'],40.)
        self.assertTrue(result['outsideSupport'])

    def test_exact_mixture_against_enumeration(self):
        values=np.array([0.,10.,20.]); w=np.array([.2,.3,.5]); y=8.
        result=fa.evaluate_distribution(values,w,y)
        independent=sum(w[i]*abs(x-y) for i,x in enumerate(values))-.5*sum(
            w[i]*w[j]*abs(x-z) for i,x in enumerate(values) for j,z in enumerate(values))
        self.assertAlmostEqual(result['crps'],independent)
        self.assertEqual(result['mean'],13.)
        self.assertEqual(fa.weighted_quantile(values,w,.5),10.)

    def test_coverage_interval_includes_uncertainty(self):
        lo,hi=fa.wilson(12,16)
        self.assertLess(lo,.75)
        self.assertGreater(hi,.75)
        self.assertLess(hi,.95)
        self.assertGreater(fa.wilson(16,16)[0],.8)

    def test_conditioning_conserves_probability(self):
        donors=[{'rookieRole':True},{'rookieRole':True},{'rookieRole':False}]
        np.testing.assert_allclose(fa.weights(donors,.4),[.2,.2,.6])
        np.testing.assert_allclose(fa.weights(donors[:2],.4),[.5,.5])

    def test_no_future_scores_in_candidate(self):
        raw=pd.read_csv(sr.ROOT/'data/raw/games.csv',low_memory=False)
        original=sr.fit(raw)
        raw.loc[raw.season>=2018,['home_score','away_score']]=999999
        self.assertEqual(original,sr.fit(raw))
        stored=json.loads((sr.A/'scoring_recalibration.json').read_text())
        self.assertEqual(original['candidateMeanTotal2018'],stored['proposedOverride']['meanTotal'])

    def test_method_selection_does_not_use_assessment_scores(self):
        raw=pd.read_csv(sr.ROOT/'data/raw/games.csv',low_memory=False)
        first=sr.fit(raw)
        raw.loc[raw.season>=2013,['home_score','away_score']]=999999
        changed=sr.fit(raw)
        self.assertEqual(first['selected'],changed['selected'])
        for name in first['methods']:
            self.assertEqual(first['methods'][name]['selection2005Through2012RMSE'],
                             changed['methods'][name]['selection2005Through2012RMSE'])

    def test_release_failure_cannot_be_hidden_by_metric_success(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result=gates.run()
        statuses={row['id']:row['status'] for row in result['gates']}
        self.assertEqual(statuses['frozen_metrics_recompute'],'pass')
        self.assertEqual(statuses['strict_label_cutoff'],'pass')
        self.assertEqual(statuses['strict_independent_chronological_validation'],'unsupported')
        self.assertEqual(statuses['coverage95_QB_snaps'],'fail')
        self.assertEqual(statuses['coverage95_LB_snaps'],'fail')
        self.assertEqual(result['releaseStatus'],'blocked')

    def test_exact_forecast_metrics_from_saved_rows(self):
        data=pd.read_csv(fa.A/'forecast_audit_predictions.csv')
        report=json.loads((fa.A/'forecast_audit.json').read_text())
        self.assertEqual(len(data),report['overall']['snaps']['n'])
        self.assertAlmostEqual(np.sqrt(np.mean((data.snaps_actual-data.snaps_mean)**2)),
                               report['overall']['snaps']['rmse'],places=10)
        self.assertAlmostEqual(data.snaps_crps.mean(),report['overall']['snaps']['meanCrps'],places=10)
        self.assertEqual(report['subgroups']['QB']['snaps']['outsideDonorSupport'],4)
        self.assertEqual(len(report['finiteEnsembleSeeds']),16)


if __name__=='__main__':
    unittest.main(verbosity=2)
