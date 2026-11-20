"""Fixture checks for the fixed discrete marginal experiment."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import score_marginal as marginal
import score_distribution as scores


def fixture():
    return pd.DataFrame([
        {
            "season": year,
            "home_team": ("A", "B")[week % 2],
            "away_team": ("B", "A")[week % 2],
            "home_score": (0, 1, 21, 24, 27, 10, 17)[(year + week) % 7],
            "away_score": (0, 14, 20, 23, 6)[(year + week) % 5],
        }
        for year in range(1999, 2006)
        for week in range(16)
    ])


class ScoreMarginalTests(unittest.TestCase):
    def test_fitted_law_and_origin_forecasts_ignore_outcomes_from_origin_forward(self):
        rows = fixture()
        control = scores.add_prior_context(rows)
        rows.loc[rows.season.ge(2004), ["home_score", "away_score"]] = [100, 200]
        poisoned = scores.add_prior_context(rows)
        origin = 2004
        law, calibration = marginal.fit(control, origin)
        changed_law, changed_calibration = marginal.fit(poisoned, origin)
        self.assertEqual(law, changed_law)
        for old, new in zip(calibration, changed_calibration):
            for actual, expected in zip(old, new):
                np.testing.assert_array_equal(actual, expected)
        first = list(marginal.draw(control[control.season.eq(origin)], origin, law, calibration, 64))
        second = list(marginal.draw(poisoned[poisoned.season.eq(origin)], origin, changed_law, changed_calibration, 64))
        for one, two in zip(first, second):
            np.testing.assert_array_equal(one[4:], two[4:])

    def test_empirical_scores_are_monotonic_whole_and_support_shutouts(self):
        _, calibrations = marginal.fit(scores.add_prior_context(fixture()), 2004)
        for calibration in calibrations:
            output = marginal.map_score(marginal.GRID, calibration)
            self.assertTrue((np.diff(output) >= 0).all())
            self.assertTrue(np.issubdtype(output.dtype, np.integer))
            self.assertTrue((output >= 0).all())
            self.assertTrue((output > 0).any())
            self.assertTrue((output == 0).any())
            self.assertFalse((output == 1).any())

    def test_shared_latent_shocks_and_separate_fixture_innovations(self):
        games = scores.add_prior_context(fixture())
        schedule = games[games.season.eq(2004)].iloc[:3]
        law, calibration = marginal.fit(games, 2004)
        draws = 4
        margins = []
        original = scores.nfl_scores

        def capture(total, margin, tie, winner):
            margins.append(margin)
            return original(total, margin, tie, winner)

        with patch.object(scores, "nfl_scores", side_effect=capture):
            output = list(marginal.draw(schedule, 2004, law, calibration, draws))
        rng = np.random.default_rng(np.random.SeedSequence([marginal.SEED, 2004]))
        shock_a, shock_b = rng.normal(0, law["seasonShockSd"], size=(2, draws))
        for (game, _, _, expected, _, _), margin in zip(output, margins):
            z_margin, _, _, _ = rng.random((4, draws))
            signed_shock = (shock_a - shock_b) * (1 if game.home_team == "A" else -1)
            np.testing.assert_allclose(margin, expected + signed_shock + law["marginSd"] * marginal.ndtri(z_margin))
        self.assertFalse(np.array_equal(margins[0], margins[2]))

    def test_metric_arithmetic(self):
        score = marginal.metrics(
            np.array([0, 6]), np.array([3, 3]),
            SimpleNamespace(total=5, margin=1, home_score=3, away_score=2, shutout=False),
        )
        self.assertEqual(score["total"], {"crps": 1.5, "mae": 1.0, "bias": 1.0, "coverage": 1.0})
        self.assertEqual(score["shutouts"], {"brier": .25, "predicted": .5, "observed": 0.0})


if __name__ == "__main__":
    unittest.main()
