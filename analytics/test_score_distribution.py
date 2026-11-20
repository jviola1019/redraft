"""Regression checks for the deployed scoring-law comparator and chronology."""
import unittest
from types import SimpleNamespace
import numpy as np
import pandas as pd
from score_distribution import (nfl_scores, runtime_score_law, base_draw,
                                fit_score_law, fit_hurdle, add_prior_context, ALIASES)


class ScoreDistributionTests(unittest.TestCase):
    def test_overtime_uses_independent_winner_uniform(self):
        # Equal rounded scores with a slightly positive latent margin: either team
        # must still be able to win when the tie-resolution draw is held fixed.
        h,a=nfl_scores(np.array([40.,40.]),np.array([.2,.2]),
                       np.array([.99,.99]),np.array([0.,1.]))
        np.testing.assert_array_equal(h,[23,20])
        np.testing.assert_array_equal(a,[20,23])

    def test_runtime_override_and_shock_marginal(self):
        law=runtime_score_law()
        self.assertEqual(law['meanTotal'],44.87109375)
        self.assertGreater(law['seasonShockSd'],0)
        # Disable clipping/tie/rounding effects with a high total. Per-game margin
        # variance must include both team-season shocks as well as game noise.
        law=dict(law,meanTotal=1000,totalSd=0)
        h,a=base_draw(SimpleNamespace(home_prior=0,away_prior=0),law,
                      np.random.default_rng(20261120),200000)
        expected=law['marginSd']**2+2*law['seasonShockSd']**2
        self.assertAlmostEqual(float(np.var(h-a))/expected,1,delta=.02)

    def test_aliases_preserve_prior_year_context(self):
        g=pd.DataFrame({'season':[2015,2016], 'home_team':['STL','LA'],
                        'away_team':['WSH','WAS'],'home_score':[30,20],
                        'away_score':[10,21]})
        for col in ['home_team','away_team']: g[col]=g[col].replace(ALIASES)
        g=add_prior_context(g)
        self.assertEqual(g.iloc[1].home_prior,20)
        self.assertEqual(g.iloc[1].away_prior,-20)

    def test_fit_does_not_use_future_outcomes(self):
        rng=np.random.default_rng(3)
        g=pd.DataFrame({'season':np.repeat(np.arange(2000,2019),20),
                        'home_prior':rng.normal(size=380),'away_prior':rng.normal(size=380),
                        'margin':rng.normal(size=380),'total':rng.normal(44,10,380),
                        'shutout':rng.random(380)<.03})
        law=fit_score_law(g,2015)
        hurdle=fit_hurdle(g[g.season<=2015],3)
        poisoned=g.copy()
        poisoned.loc[poisoned.season>2015,['margin','total']]=999999
        poisoned.loc[poisoned.season>2015,'shutout']=True
        self.assertEqual(law,fit_score_law(poisoned,2015))
        self.assertEqual(hurdle,fit_hurdle(poisoned[poisoned.season<=2015],3))


if __name__=='__main__': unittest.main()
