from types import SimpleNamespace
import unittest

import numpy as np
import pandas as pd

from compare_pace import bootstrap, features, fixture_losses, observations


class ScoringPaceTest(unittest.TestCase):
    def test_drive_start_has_only_points_from_earlier_play_rows(self):
        game = SimpleNamespace(game_id="g", home_team="KC", away_team="DEN")
        drives = [(0, 0, 3598, 7, 0), (1, 0, 3500, 3, 0), (0, 0, 3400, 0, 0)]
        plays = pd.DataFrame({
            "play_id": [1, 2, 3, 4], "qtr": [1, 1, 1, 1], "fixed_drive": [1, 1, 2, 3],
            "posteam": ["DEN", "KC", "DEN", "KC"], "play_type": ["kickoff", "pass", "pass", "pass"],
            "total_home_score": [0, 7, 7, 100], "total_away_score": [0, 0, 3, 3],
            "game_seconds_remaining": [3600, 3598, 3500, 3400],
        })
        want = [(3598, 0, 2), (3500, -7, 1), (3400, 4, 0)]
        self.assertEqual(list(observations(plays, game, drives)), want)

    def test_candidate_contains_same_clock_columns_and_exact_score_bounds(self):
        minutes = [0, 150, 300, 3600]
        baseline = features(minutes)
        full = features(minutes, [-8, -7, 7, 8])
        ref, trailing, leading = np.split(full, 3, axis=1)
        np.testing.assert_array_equal(ref, baseline)
        np.testing.assert_array_equal(baseline.sum(axis=1), [1, 1, 1, 1])
        np.testing.assert_array_equal(trailing.sum(axis=1), [1, 0, 0, 0])
        np.testing.assert_array_equal(leading.sum(axis=1), [0, 0, 0, 1])
        np.testing.assert_array_equal(baseline[1, :2], [.5, .5])

    def test_losses_average_drives_before_games(self):
        prediction = pd.DataFrame({"game_id": ["g", "g", "h"], "week": [1, 1, 2],
                                   "remaining": [1, 0, 0], "baseline": [1, 2, 0],
                                   "candidate": [2, 0, 3]})
        np.testing.assert_array_equal(fixture_losses(prediction).baselineMse, [2, 0])
        np.testing.assert_array_equal(fixture_losses(prediction).candidateMae, [.5, 3])

    def test_bootstrap_preserves_week_membership(self):
        loss = pd.DataFrame({"week": [1, 1, 2], "baselineMse": [2, 2, 0],
                             "baselineMae": [2, 2, 0], "candidateMse": [0, 4, 3],
                             "candidateMae": [0, 4, 2]})
        self.assertEqual(bootstrap([loss], 11), {"mse": [0., 3.], "mae": [0., 2.]})


if __name__ == "__main__":
    unittest.main()
