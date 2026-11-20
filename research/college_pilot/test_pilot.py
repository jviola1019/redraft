from datetime import datetime
import unittest

from pilot import audit_boxes, conservative_eligibility, disclosure_counts, roster_crosswalk


class PilotGateTests(unittest.TestCase):
    def test_cutoff_rejects_same_day_future_unknown_and_wrong_season(self):
        cutoff = datetime.fromisoformat("2018-04-26T23:59:00+00:00")
        schedule = {
            "season": 2017,
            "seasonType": "postseason",
            "homeTeam": "Oklahoma",
            "awayTeam": "Georgia",
            "completed": True,
            "startTimeTBD": False,
            "startDate": "2018-01-01T22:00:00Z",
        }
        cases = [
            ({}, "eligible_reconstruction"),
            ({"startDate": "2018-04-26T07:00:00Z"}, "too_close_or_after_cutoff"),
            ({"startDate": "2018-04-27T07:00:00Z"}, "too_close_or_after_cutoff"),
            ({"startDate": "2018-04-25T07:00:00Z"}, "too_close_or_after_cutoff"),
            ({"startTimeTBD": True}, "no_confirmed_game"),
            ({"completed": False}, "no_confirmed_game"),
            ({"startDate": "2018-01-01T22:00:00"}, "no_timezone"),
            ({"season": 2018}, "wrong_season"),
            ({"homeTeam": "Clemson"}, "wrong_team"),
        ]
        for fields, expected in cases:
            with self.subTest(fields=fields):
                self.assertEqual(
                    conservative_eligibility(schedule | fields, cutoff, 2017, "oklahoma"),
                    expected,
                )

    def test_crosswalk_abstains_on_namesakes_and_duplicate_ids(self):
        # Synthetic schema fixtures for failure-path testing only.
        roster = [
            {"id": "1", "firstName": "A", "lastName": "Test", "team": "Team"},
            {"id": "2", "firstName": "B", "lastName": "Test", "team": "Team"},
            {"id": "3", "firstName": "B", "lastName": "Test", "team": "Team"},
            {"id": "4", "firstName": "C", "lastName": "Test", "team": "Team"},
            {"id": "4", "firstName": "D", "lastName": "Test", "team": "Team"},
            {"id": "5", "firstName": "E", "lastName": "Test", "team": "Rival"},
        ]
        prospects = [
            {"id": f"p{i}", "name": f"{letter} Test", "college": "Scenario team"}
            for i, letter in enumerate("ABCDE", 1)
        ]
        mapping, status = roster_crosswalk(roster, prospects, "Team", "Scenario team")
        self.assertEqual(mapping, {"1": "p1"})
        self.assertEqual(status, {"provisional_name_team": 1, "ambiguous": 3, "unmatched": 1})

    def test_observations_require_a_date_gated_game_and_conflicts_are_quarantined(self):
        def box(game, stat):
            return {
                "id": game,
                "teams": [{"team": "Team", "categories": [{
                    "name": "passing",
                    "types": [{"name": "YDS", "athletes": [{"id": "1", "stat": stat}]}],
                }]}],
            }

        status, profiles = audit_boxes(
            [box(10, "12"), box(10, "12"), box(11, "7"), box(11, "9"), box(12, "7"), box(13, None)],
            {10, 11, 13},
            "Team",
            {"1": "prospect"},
        )
        self.assertEqual(status["usable_observations"], 1)
        self.assertEqual(status["conflicting_observations"], 1)
        self.assertEqual(status["box_outside_date_gate"], 1)
        self.assertEqual(status["missing_values"], 1)
        self.assertEqual(profiles, {"prospect": {(10, "passing", "YDS", "12")}})

    def test_sparse_individual_disclosure_can_create_singletons(self):
        pool = [{"id": str(i), "position": "QB", "college": "Team"} for i in range(3)]
        result = disclosure_counts(pool, {"0": ("4",), "1": ("4",)})
        self.assertEqual(result["position_exact_sample_profile_singletons"], 1)
        self.assertEqual(result["profile_bearing_exact_profile_singletons"], 0)


if __name__ == "__main__":
    unittest.main()
