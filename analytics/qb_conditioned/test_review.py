"""Focused checks for cutoff exclusion, production parity and score outputs."""
import json
import math
import unittest

import numpy as np
import pandas as pd

import review


class ConditionedReviewTest(unittest.TestCase):
    def test_maturity_boundary_and_poisoning(self):
        frame = pd.DataFrame({"season": [2014, 2015], "pfr_id": ["eligible", "immature"]})
        baseline = [{"snaps": [0] * 5, "games": [0] * 5, "rookieRole": False}]
        annual = {(2014, "eligible"): {"snaps": 200, "games": 9},
                  (2015, "immature"): {"snaps": 99999, "games": 99999}}
        before, _ = review.donor_pool(baseline, frame, "2019-02-28T23:59:59Z", annual)
        after, manifest = review.donor_pool(baseline, frame, "2019-03-01T00:00:00Z", annual)
        self.assertEqual(before, baseline)
        self.assertEqual(after[1]["snaps"], [200, 0, 0, 0, 0])
        self.assertEqual([row["cohort"] for row in manifest], [2013, 2014])

    def test_runtime_mixture_and_exposure(self):
        donor = lambda snaps, games: {"snaps": snaps, "games": games, "rookieRole": snaps[0] >= 200}
        donors = [donor([0] * 5, [0] * 5), donor([200] * 5, [8] * 5)]
        actual = donors[0]
        score = review.score_player(actual, {"baseline": donors}, {"production": [17] * 5}, .25)
        self.assertEqual(score["production"]["baseline"]["games"]["total"]["mean"], 11.25)
        self.assertEqual(score["production"]["baseline"]["snaps"]["total"]["crps"], 1062.5 * .25**2)

    def test_outputs(self):
        result = json.loads((review.HERE / "results.json").read_text())
        predictions = json.loads((review.HERE / "predictions.json").read_text())
        self.assertEqual([row["candidateDonors"] for row in result["origins"]], [33, 45, 62])
        self.assertTrue(all(row["baselineExposureParity"] and row["futureDataPoisoningPassed"]
                            for row in result["origins"]))
        self.assertEqual(len({(p["cohort"], p["pfrId"]) for p in predictions}), len(predictions))
        previous = json.loads((review.HERE.parent / "qb_mature/qb_mature_donor_predictions.json").read_text())
        previous_snaps = {(p["cohort"], p["pfrId"]): p["actualAnnual"] for p in previous}
        for player in predictions:
            self.assertEqual(player["actual"]["snaps"], previous_snaps[player["cohort"], player["pfrId"]])
        self.assertFalse(result["runtimeChanged"])
        for schedule in ("production", "draftTime"):
            for kind, entries in result["metrics"][schedule]["overall"].items():
                differences = [p["scores"][schedule]["candidate"][kind]["total"]["crps"]
                               - p["scores"][schedule]["baseline"][kind]["total"]["crps"]
                               for p in predictions]
                self.assertTrue(math.isclose(entries["pairedCrps"]["difference"], np.mean(differences)))
        for path, sha in result["sourceHashes"].items():
            self.assertEqual(review.digest(review.ROOT / path), sha)


if __name__ == "__main__":
    unittest.main()
