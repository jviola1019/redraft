"""Regression fixtures and independent checks of saved QB research scores."""
import hashlib
import json
import unittest

import numpy as np
import pandas as pd

import qb_rank_hindcast as q


class RankHindcastTest(unittest.TestCase):
    def test_rank_paths_preserve_row_pairing_age_and_zeros(self):
        rows = [{'age': age, 'year': 2013, 'pfrId': str(i), 'snaps': value,
                 'games': games}
                for age in range(5)
                for i, (value, games) in enumerate([(0, 0), (100 + age, 3), (100 + age, 7)])]
        paths = q.rank_paths(pd.DataFrame(rows))
        np.testing.assert_array_equal(paths[0], np.zeros((5, 2)))
        np.testing.assert_array_equal(paths[q.DRAWS // 2, :, 0], np.arange(100, 105))
        np.testing.assert_array_equal(paths[q.DRAWS // 2, :, 1], np.full(5, 3))
        np.testing.assert_array_equal(paths[-1, :, 1], np.full(5, 7))

    def test_cutoff_and_schedules(self):
        before = pd.DataFrame([{'year': 2015, 'snaps': 20, 'games': 1}])
        after = pd.DataFrame([{'year': 2016, 'snaps': 99999, 'games': 99999}])
        pd.testing.assert_frame_equal(q.fit_slice(pd.concat([before, after]), 2016), before)
        for origin, realized, expected in [
            (2017, False, [16] * 5),
            (2017, True, [16, 16, 16, 16, 17]),
            (2018, True, [16, 16, 16, 17, 17]),
            (2021, False, [17] * 5),
        ]:
            np.testing.assert_array_equal(q.origin_games(origin, realized), expected)
        path = np.tile([400, 16], (1, 5, 1))
        result = q.score(path, q.origin_games(2017, True), 70, 'games')
        self.assertEqual(result['mean'], 81)
        self.assertEqual(result['actual'], 70)

    def test_scoring_reconstructs_and_freeze_holds(self):
        report = json.loads((q.A / 'qb_rank_hindcast.json').read_text())
        saved = json.loads((q.A / 'qb_rank_hindcast_predictions.json').read_text())
        for key, rows in saved.items():
            for cohort in q.ORIGINS:
                group = [r for r in rows if r['cohort'] == cohort]
                self.assertEqual(q.evaluate(group), report[key]['byCohort'][str(cohort)])
                for row in group:
                    for target in q.TARGETS:
                        self.assertEqual(sum(row['actualAnnual'][target]), row['ageRank'][target]['actual'])
                        self.assertTrue(all(isinstance(value, int) for value in row['actualAnnual'][target]))
        for key in ('sourceHashes',):
            for relative, expected in report[key].items():
                self.assertEqual(hashlib.sha256((q.fy.R / relative).read_bytes()).hexdigest(), expected)
        for year, source in report['sourceCoverage'].items():
            self.assertEqual(source['expectedGames'], source['observedGames'])
            self.assertEqual(hashlib.sha256((q.fy.RAW / f'snap_counts_{year}.csv').read_bytes())
                             .hexdigest(), source['sha256'])
        self.assertTrue(all(row['poisoningPassed'] for row in report['fits'].values()))
        self.assertEqual(report['frozen2018Baseline']['snaps']['interval95']['covered'], 12)
        self.assertEqual(report['frozen2018Baseline']['games']['interval95']['covered'], 13)
        self.assertFalse(report['decision']['advance'])
        self.assertFalse(report['decision']['promote'])


if __name__ == '__main__':
    unittest.main()
