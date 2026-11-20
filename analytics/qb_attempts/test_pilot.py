"""Checks for scoring, unknown identities, and information availability."""
import argparse
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from pilot import labels, load_attempts, predict, score

ROOT = Path(__file__).resolve().parents[2]


class AttemptsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = ROOT / "data/raw"
        attempts, cls.audit = load_attempts(ARGS.archive, raw / "games.csv")
        cls.sample, cls.excluded = labels(raw / "draft_picks.csv", attempts)

    def test_crps_matches_pairwise_definition(self):
        draws = np.array([0, 1, 2, 7])
        expected = np.abs(draws - 2).mean() - np.abs(draws[:, None] - draws).mean() / 2
        self.assertAlmostEqual(score(pd.Series(draws), 2)["crps"], expected)

    def test_cutoff_excludes_donors_with_late_fifth_season(self):
        changed = self.sample.copy()
        changed.loc[changed["season"].ge(2014), "actual"] += 100_000
        before = [row for row in predict(self.sample) if row["origin"] == 2018]
        after = [row for row in predict(changed) if row["origin"] == 2018]
        for original, poisoned in zip(before, after, strict=True):
            self.assertEqual(original["latest_donor_season"], 2017)
            self.assertNotEqual(original["actual"], poisoned["actual"])
            for model in ("benchmark", "candidate"):
                for key in ("median", "lower_80", "upper_80", "donors"):
                    self.assertEqual(original[model][key], poisoned[model][key])

    def test_unknown_is_distinct_from_covered_zero(self):
        excluded = {row["pfr_player_id"] for row in self.excluded}
        self.assertIn("BoydTa00", excluded)
        self.assertFalse(self.sample["pfr_player_id"].isin(excluded).any())
        self.assertTrue(self.sample["actual"].eq(0).any())
        self.assertTrue(all(self.audit[year]["unattributed_attempts"] == 0 for year in range(2011, 2023)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    ARGS = parser.parse_args()
    unittest.main(argv=[__file__])
