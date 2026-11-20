import csv
import json
import unittest
from pathlib import Path

from benchmark import GAME_SOURCE, calibrated_probabilities, forecast_origin


class BenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with GAME_SOURCE.open(newline="") as source:
            cls.games = list(csv.DictReader(source))

    def test_post_origin_games_cannot_change_fitted_model_or_forecasts(self):
        origin = 2020
        truncated = [row for row in self.games if int(row["season"]) < origin]
        poisoned = [
            row if int(row["season"]) < origin else
            {**row, "gameday": "1910-01-01", "home_score": "broken", "away_team": "XX", "game_type": "SB"}
            for row in self.games
        ]
        self.assertEqual(forecast_origin(truncated, origin, [1, 5]), forecast_origin(poisoned, origin, [1, 5]))

    def test_future_playoff_expansion_is_only_in_sensitivity(self):
        forecasts, metadata = forecast_origin(self.games, 2018, [1, 5])
        for horizon, expected_aligned in ((1, 12), (5, 14)):
            rows = list(forecasts[horizon].values())
            self.assertAlmostEqual(sum(row["benchmarkProbability"] for row in rows), 12)
            self.assertAlmostEqual(sum(row["realizedFormatProbability"] for row in rows), expected_aligned)
            self.assertEqual(metadata[horizon]["trainingTargetYears"][-1], 2017)
            self.assertLess(metadata[horizon]["latestSourceGameDate"], "2018-04-01")

    def test_calibration_preserves_logit_order_and_slots(self):
        probabilities = calibrated_probabilities([-4, -1, 2, 6], 2)
        self.assertEqual(probabilities, sorted(probabilities))
        self.assertAlmostEqual(sum(probabilities), 2)

    def test_results_retain_all_rows_and_whole_season_blocks(self):
        path = Path(__file__).with_name("results.json")
        results = json.loads(path.read_text())
        self.assertEqual(results["overall"]["rows"], 960)
        self.assertEqual(results["overall"]["distinctActualTeamSeasons"], 256)
        for horizon, forecast_count in enumerate((256, 224, 192, 160, 128), 1):
            group = results["byHorizon"][str(horizon)]
            self.assertEqual(group["rows"], forecast_count)
            self.assertEqual(len(group["blockSensitivity"]["1"]["byOmittedBlock"]), forecast_count // 32)
            self.assertEqual(len(group["blockSensitivity"]["2"]["byOmittedBlock"]), forecast_count // 32 - 1)


if __name__ == "__main__":
    unittest.main()
