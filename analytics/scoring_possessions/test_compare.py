from types import SimpleNamespace
import unittest

import numpy as np
import pandas as pd

import compare


class DriveComparisonTests(unittest.TestCase):
    def test_drive_credits_reconcile_and_overtime_excluded(self):
        plays = pd.DataFrame([
            [1, 1, 1, "BUF", "run", 0, 0],
            [2, 1, 1, "BUF", "pass", 0, 6],
            [3, 1, 1, "MIA", "extra_point", 0, 7],
            [4, 2, 4, "MIA", "pass", 7, 7],
            [5, 3, 5, "BUF", "field_goal", 10, 7],
        ], columns=["play_id", "fixed_drive", "qtr", "posteam", "play_type",
                    "total_home_score", "total_away_score"])
        game = SimpleNamespace(home_team="BUF", away_team="MIA", home_score=10, away_score=7)
        self.assertEqual(compare.game_drives(plays, game), ([(0, 0, 7), (1, 0, 7)], None))
        game.home_score = 13
        self.assertEqual(compare.game_drives(plays, game), (None, "final_score_mismatch"))

    def test_data_from_origin_and_future_do_not_change_fit(self):
        game = [(0, 7, 0), (0, 0, 0), (1, 3, 0), (1, 0, 0)]
        history = {year: [game] for year in range(2010, 2015)}
        pace, laws = compare.fit_drives(history, 2013)
        history[2013] = history[2014] = [[(0, 100, 0), (1, 100, 0)]]
        other_pace, other_laws = compare.fit_drives(history, 2013)
        np.testing.assert_array_equal(pace, other_pace)
        for (scores, probabilities), (other_scores, other_probabilities) in zip(laws, other_laws):
            np.testing.assert_array_equal(scores, other_scores)
            np.testing.assert_array_equal(probabilities, other_probabilities)

    def test_tilt_matches_target_and_keeps_joint_atoms(self):
        categories = np.array([[0, 0], [0, 2], [3, 0], [7, 0]])
        base = np.array([.6, .05, .15, .2])
        target = np.array([.5, 2.0, 4.5])
        result = compare.tilt(categories, base, target)
        np.testing.assert_allclose(result @ categories[:, 0], target, atol=1e-6)
        np.testing.assert_allclose(result[:, 0] / result[:, 1], 12.0)
        np.testing.assert_allclose(result.sum(axis=1), 1.0)

    def test_joint_energy_arithmetic(self):
        self.assertAlmostEqual(compare.energy(np.array([0, 3]), np.array([0, 4]), 0, 0), 0)
        self.assertAlmostEqual(compare.energy(np.array([3, 3]), np.array([4, 4]), 0, 0), 5)

    def test_baseline_uses_identical_draws(self):
        games = compare.historical.load(compare.scores.RAW)
        year = 2013
        law, calibration = compare.historical.fit(games, year)
        schedule = games[games.season.eq(year)].iloc[:12]
        pace = np.array([[10, 12], [15, 12]])
        credit = np.array([[0, 0], [0, 7], [3, 0], [7, 0]])
        law_pair = (credit, np.array([.6, .01, .15, .24]))
        new = list(compare.joint_draw(schedule, year, law, (pace, [law_pair] * 2), 64))
        old = list(compare.historical.draw(schedule, year, law, calibration, 64))
        for actual, expected in zip(new, old):
            np.testing.assert_array_equal(actual[4], expected[4])
            self.assertTrue(np.all(np.array(actual[5]) >= 0))
        self.assertTrue(any(np.any(np.array(game[5]) == 0) for game in new))


if __name__ == "__main__":
    unittest.main()
