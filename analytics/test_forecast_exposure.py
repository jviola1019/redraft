"""Regression checks for the runtime-matched finite donor exposure audit."""
import unittest
import numpy as np
from forecast_audit import donor_total, evaluate_distribution


class ExposureTests(unittest.TestCase):
    def test_unchanged_sixteen_game_horizon(self):
        donor = {'snaps': [800] * 5, 'games': [16] * 5}
        self.assertEqual(donor_total(donor, 'snaps', 2013), 4000)
        self.assertEqual(donor_total(donor, 'games', 2013), 80)

    def test_mixed_schedule_and_rounding_matches_runtime(self):
        donor = {'snaps': [800] * 5, 'games': [8] * 5}
        self.assertEqual(donor_total(donor, 'snaps'), 4100)
        self.assertEqual(donor_total(donor, 'games'), 42)
        self.assertEqual(donor_total({'games': [16] * 5}, 'games'), 82)
        self.assertEqual(donor_total({'snaps': [0] * 5}, 'snaps'), 0)

    def test_exposure_changes_predictions_without_scaling_actual(self):
        donor = {'snaps': [800] * 5}
        result = evaluate_distribution(np.array([donor_total(donor, 'snaps')]), np.array([1.]), 3900)
        self.assertEqual(result['actual'], 3900)
        self.assertEqual(result['mean'], 4100)
        self.assertEqual(result['crps'], 200)


if __name__ == '__main__':
    unittest.main()
