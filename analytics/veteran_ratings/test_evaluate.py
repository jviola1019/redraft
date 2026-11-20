import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

import evaluate


def player(name, offense=0, defense=0):
    return {"name": name, "position": "QB", "offense": offense, "defense": defense, "games": 1}


class VeteranRatingsTest(unittest.TestCase):
    def test_match_requires_prior_nfl_participation_and_unique_names(self):
        prior = {
            "a": player("José St. Brown Jr.", offense=120),
            "b": player("Alex Adams", offense=100),
            "c": player("Alex Adams II", defense=100),
            "d": player("John Doe", offense=100),
            "e": player("Missing Player", defense=100),
            "f": player("Special Teams"),
        }
        ratings = {
            "josestbrown": ["80"],
            "alexadams": ["71"],
            "johndoe": ["78", "82"],
            "specialteams": ["75"],
            "incomingrookie": ["85"],
        }
        rows, counts = evaluate.join_features(prior, {}, ratings)
        self.assertEqual([row["player_id"] for row in rows], ["a"])
        self.assertEqual(rows[0]["older_games"], 0)
        self.assertEqual(counts["ambiguous_snap_name"], 2)
        self.assertEqual(counts["ambiguous_archive_name"], 1)
        self.assertEqual(counts["unmatched"], 1)
        self.assertEqual(counts["special_teams_only"], 1)

    def test_labels_use_larger_side_and_only_feature_population(self):
        rows = [{"player_id": identifier} for identifier in ("a", "b", "c")]
        later = {
            "a": player("A", offense=300, defense=200),
            "b": player("B", defense=500),
            "incoming": player("New", offense=999),
        }
        outcomes = evaluate.attach_outcomes(rows, later)
        self.assertEqual([row["role"] for row in outcomes], [0, 1, 0])
        self.assertNotIn("role", rows[0])

    def test_missing_checksum_fails_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "2023.csv"
            path.write_text("invalid file")
            with self.assertRaisesRegex(ValueError, "checksum"):
                evaluate.read_ratings(path, 2024)

    def test_good_probabilities_improve_both_metrics(self):
        y = np.array([0, 1, 0, 1])
        result = evaluate.compare(y, np.full(4, 0.5), np.array([0.1, 0.9, 0.1, 0.9]))
        self.assertTrue(result["passes_statistical_screen"])
        self.assertLess(result["metrics"]["brier"]["augmented_minus_baseline"], 0)

    def test_manifest_and_output_support_temporal_claims(self):
        manifest = evaluate.MANIFEST["snapshot_metadata"]
        results = json.loads((evaluate.HERE / "results.json").read_text())
        for origin, evaluation in results["evaluation"].items():
            self.assertTrue(all(str(year) < origin for year in evaluation["train_origins"]))
            self.assertLess(manifest[origin]["rating_date"], manifest[origin]["draft_start"])
        self.assertLess(manifest["2024"]["asset_updated"][:10], manifest["2024"]["draft_start"])
        self.assertGreater(manifest["2023"]["asset_uploaded"][:10], manifest["2023"]["draft_start"])
        self.assertEqual(results["protocol_sha256"], evaluate.sha256(evaluate.HERE / "PROTOCOL.md"))


if __name__ == "__main__":
    unittest.main()
