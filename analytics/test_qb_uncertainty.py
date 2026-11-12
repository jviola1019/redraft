import json
import hashlib
import unittest
from pathlib import Path

from analytics import qb_uncertainty as qu


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "analytics" / "qb_uncertainty.json"
FEASIBILITY = ROOT / "analytics" / "qb_legacy_source_feasibility.json"


class QBUncertaintyChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(RESULT.read_text())

    def test_strict_support_is_visible(self):
        s = self.data["support"]
        self.assertEqual((s["QBDonors"], s["donorCohorts"]), (15, 1))
        self.assertEqual(s["rookieRoleDonors_ge200Snaps"], 3)
        self.assertEqual(s["holdoutQBs"], 16)
        self.assertEqual(s["holdoutOutcomesAboveEveryDonorTrajectory"], 4)

    def test_rolling_cutoffs_exclude_future_labels(self):
        origins = self.data["strictRollingOrigins"]["years"]
        self.assertEqual([r["draftYear"] for r in origins], [2018, 2019, 2020, 2021])
        for row in origins:
            self.assertLessEqual(max(row["donorCohorts"]), row["draftYear"] - 5)
            self.assertLess(max(row["rookieModelCohorts"]), row["draftYear"])
            self.assertGreater(row["rolePositiveDonors"], 0)
            self.assertGreater(row["roleNegativeDonors"], 0)

    def test_cutoff_prior_is_screening_candidate_not_claimed_release(self):
        pooled = self.data["strictRollingOrigins"]["pooledAcrossFourDraftClasses"]
        self.assertLess(pooled["precutoffQBRoleRate"]["rookieRoleBrier"],
                        pooled["pooledRoleModel"]["rookieRoleBrier"])
        self.assertFalse(self.data["decision"]["productionChangeRecommended"])
        self.assertEqual(self.data["decision"]["uncertaintyStatus"],
                         "unsupported-for-high-end-QB-tails")

    def test_weighted_quantile_does_not_extrapolate(self):
        values = __import__("numpy").array([0.0, 100.0, 1000.0])
        weights = __import__("numpy").array([0.8, 0.15, 0.05])
        self.assertEqual(qu.weighted_quantile(values, weights, 0.95), 100.0)
        self.assertEqual(qu.weighted_quantile(values, weights, 0.99), 1000.0)

    def test_legacy_source_is_not_mislabeled_as_acquired(self):
        data = json.loads(FEASIBILITY.read_text())
        self.assertFalse(data["findings"]["acquisition"]["dataRetrieved"])
        self.assertFalse(data["findings"]["licensing"]["redistributionCleared"])
        cohort = data["findings"]["localCombineSupport"]
        self.assertEqual(cohort["qbCombineRows"], 154)
        self.assertEqual(cohort["qbRowsWithPfrId"] + cohort["qbRowsMissingPfrId"], 154)
        actual = hashlib.sha256((ROOT / cohort["file"]).read_bytes()).hexdigest()
        self.assertEqual(actual, cohort["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
