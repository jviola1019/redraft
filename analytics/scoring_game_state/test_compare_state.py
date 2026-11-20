from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from compare_state import game_drives, fit_state, intervals, simulate, state_cdfs, state_index


class ScoreStateTest(unittest.TestCase):
    def test_state_boundaries(self):
        differential = np.array([-9, -8, -7, 0, 7, 8, 9])
        np.testing.assert_array_equal(state_index(2, differential), [6, 6, 7, 7, 7, 8, 8])

    def test_drive_anchor_and_credit(self):
        game = SimpleNamespace(home_team="KC", away_team="DEN", home_score=7, away_score=3)
        plays = pd.DataFrame({
            "play_id": [1, 2, 3, 4, 5], "qtr": [1, 1, 1, 4, 4],
            "fixed_drive": [1, 1, 1, 2, 2], "posteam": ["DEN", "KC", "KC", "DEN", "DEN"],
            "play_type": ["kickoff", "pass", "run", "pass", "field_goal"],
            "total_home_score": [0, 0, 7, 7, 7], "total_away_score": [0, 0, 0, 0, 3],
            "game_seconds_remaining": [3600, 3591, 3500, 600, 490],
        })
        self.assertEqual(game_drives(plays, game), ([(0, 0, 3591, 7, 0), (1, 2, 600, 3, 0)], None))
        plays.loc[3, "game_seconds_remaining"] = np.nan
        self.assertEqual(game_drives(plays, game), (None, "invalid_clock"))

    def test_origin_does_not_read_current_season(self):
        drive = [(0, 0, 3500, 7, 0), (1, 1, 900, 3, 0)]
        history = {2020: [drive], 2021: [drive], 2022: [drive], 2023: None}
        templates, _, laws = fit_state(history, 2023)
        np.testing.assert_array_equal(templates, [[[0, 0], [1, 1]]] * 3)
        self.assertEqual(laws[0][3][1], 3)
        self.assertEqual(laws[1][3][4], 3)

    def test_simulated_earlier_score_controls_next_outcome(self):
        templates = np.array([[[0, 0], [1, 2], [-1, -1]], [[-1, -1], [1, 2], [-1, -1]]])
        categories = np.array([[0, 0], [8, 0]])
        home_cdf = np.ones((2, 9, 1))
        home_cdf[:, 1] = 0
        away_cdf = np.ones((2, 9, 1))
        away_cdf[:, 6] = 0
        with patch("compare_state.state_cdfs", side_effect=(home_cdf, away_cdf)):
            points = simulate(templates, [(categories,), (categories,)], [None, None], np.random.default_rng(1))
        np.testing.assert_array_equal(points, [[8, 0], [8, 0]])

    def test_state_cdfs_preserve_tilt_when_cells_equal_base(self):
        categories = np.array([[0, 0], [7, 0]])
        base = np.array([.7, .3])
        mass = np.tile(base, (9, 1))
        result = state_cdfs((categories, base, mass, None), np.array([2.1, 3.5]))
        np.testing.assert_allclose(result[:, :, 0], np.tile([[.7], [.5]], (1, 9)), atol=1e-6)

    def test_week_bootstrap_keeps_games_in_each_week_together(self):
        def row(value):
            return {key: {metric: value for metric in ("energy", "crps", "brier", "coverage")}
                    for key in ("joint", "total", "margin", "shutouts")}
        baseline = {"games": [row(0), row(0), row(0)]}
        candidate = {"games": [row(0), row(2), row(3)]}
        output = intervals([(baseline, candidate)], [np.array([1, 1, 2])], 100)
        self.assertEqual(output["joint.energy"], {"delta": 5 / 3, "interval95": [1.0, 3.0]})


if __name__ == "__main__":
    unittest.main()
