"""Run with historical games CSV path supplied through REDRAFT_GAMES_CSV."""
import os
import unittest
from pathlib import Path
import numpy as np
import empirical_score_pairs as e

class DonorChecks(unittest.TestCase):
    def test_support_and_cutoff(self):
        e.SOURCE=Path(os.environ['REDRAFT_GAMES_CSV'])
        g=e.load();law=e.sd.fit_score_law(g,2013);d,dm=e.donors(g,2014,law)
        h,a,_=e.draw_pairs(d,dm,0,np.random.default_rng(42),10000)
        support=set(zip(d.home_score,d.away_score))
        self.assertTrue(all((x,y) in support for x,y in zip(h,a)))
        self.assertTrue(((h==0)|(a==0)).any())
        poisoned=g.copy()
        poisoned.loc[poisoned.season>=2014,['home_score','away_score','margin','total']]=999999
        pd,pdm=e.donors(poisoned,2014,e.sd.fit_score_law(poisoned,2013))
        self.assertTrue(d.equals(pd));np.testing.assert_array_equal(dm,pdm)

if __name__=='__main__':unittest.main()
