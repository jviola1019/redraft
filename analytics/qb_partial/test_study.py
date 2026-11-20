"""Verify frozen forecast provenance and partial-horizon scoring."""
from pathlib import Path
import unittest

import numpy as np

import study


class PartialQBStudyTest(unittest.TestCase):
    def test_exposure_changes_with_donor_source_era(self):
        rows = [{"snaps": [160] * 5, "games": [16] * 5, "rookieRole": False}] * 2
        manifest = [{"cohort": 2016, "count": 1}, {"cohort": 2017, "count": 1}]
        before, after = study.project(rows, manifest)
        self.assertEqual(before["snaps"], [170] * 5)
        self.assertEqual(before["games"], [17] * 5)
        self.assertEqual(after["snaps"], [170] * 4 + [160])
        self.assertEqual(after["games"], [17] * 4 + [16])

    def test_future_outcome_never_enters_scores(self):
        player = {"cohort": 2025, "pfrId": "qb", "probability": .5}
        pools = dict.fromkeys(study.ARMS, [{"rookieRole": False, "snaps": [10] * 5, "games": [1] * 5}])
        annual = {(2025, "qb"): {"snaps": 100, "games": 2}}
        expected = study.score_player(player, pools, annual)
        self.assertEqual(expected["actual"], {"snaps": [100], "games": [2]})
        self.assertEqual(study.score_player(player, pools, {
            **annual, (2026, "qb"): {"snaps": 999999, "games": 19}}), expected)
        self.assertEqual(expected["scores"]["baseline"]["snaps"]["cumulative"][0]["crps"], 90)

    def test_saved_scores_and_frozen_forecasts(self):
        folder = Path(__file__).resolve().parent
        forecasts = study.read(folder / "partial_forecasts.json")
        prospective = study.read(folder / "prospective_2022.json")
        results = study.read(folder / "results.json")
        self.assertEqual(results["sampleSize"], 57)
        self.assertEqual(results["forecastBoardSize"], 59)
        self.assertEqual(set(results["unresolvedPfrIdentities"]), {"Cole Kelley", "EJ Perry"})
        self.assertEqual([len(f["players"]) for f in forecasts["origins"]], [15, 15, 14, 15])
        self.assertEqual(set(results["sourceCoverage"]), {"2022", "2023", "2024", "2025"})
        self.assertEqual({name: study.digest(folder / name) for name in study.FROZEN},
                         results["forecastHashes"])
        for age, n in enumerate((57, 42, 28, 13), 1):
            for target in ("annual", "cumulative"):
                self.assertEqual(results["metrics"][target][str(age)]["overall"]["n"], n)
        self.assertEqual(prospective["targets"]["annual5"]["season"], 2026)
        for p in prospective["forecasts"]:
            for arm, entry in p["arms"].items():
                self.assertNotIn("actual", p)
                mass = entry["massInDonorOrder"]
                donors = prospective["origin"]["pools"][arm]
                self.assertAlmostEqual(sum(mass), 1)
                for kind in study.KINDS:
                    values = np.asarray([d[kind] for d in donors])
                    self.assertAlmostEqual(entry["annual5"][kind]["mean"], values[:, 4] @ mass)
                    self.assertAlmostEqual(entry["cumulative5"][kind]["mean"], values.sum(axis=1) @ mass)


if __name__ == "__main__":
    unittest.main()
