"""Targeted checks of chronology and cold-start behavior on the pilot data."""
import unittest
from pathlib import Path
from sys import argv

import numpy as np

from pilot import predict, read_attempts, report


class KickerPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.attempts, cls.audit = read_attempts(Path(argv.pop(1)))
        cls.predictions = predict(cls.attempts)

    def test_held_out_labels_do_not_enter_same_year_forecast(self):
        changed = self.attempts.copy()
        test_years = changed["season"].ge(2014)
        changed.loc[test_years, "made"] = 1 - changed.loc[test_years, "made"]
        altered = predict(changed)
        first = self.predictions["season"].eq(2014)
        columns = ["baseline_logit", "candidate_logit"]
        np.testing.assert_allclose(self.predictions.loc[first, columns], altered.loc[first, columns])

    def test_unknown_kickers_get_distance_only_prediction(self):
        unknown = self.predictions.loc[~self.predictions["seen"]]
        self.assertGreater(len(unknown), 0)
        np.testing.assert_array_equal(unknown["baseline"], unknown["candidate"])

    def test_report_covers_all_evaluation_attempts(self):
        result = report(self.predictions)
        count = sum(self.audit[year]["retained"] for year in range(2014, 2018))
        self.assertEqual(count, result["all"]["attempts"])
        self.assertEqual(count, sum(group["attempts"] for group in result["distance_buckets"].values()))


if __name__ == "__main__":
    unittest.main(argv=argv[:1])
