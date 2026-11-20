import json
import unittest

import pandas as pd

from train import OUTPUT, by_team, cohort, summarize


class WorkloadTest(unittest.TestCase):
    def setUp(self):
        self.snaps = pd.DataFrame([
            (2022, '2022-12-20', '2022_a', 'p', 'TE', 'NYG', 200, 0),
            (2023, '2023-09-20', '2023_a', 'p', 'TE', 'NYG', 250, 25),
            (2023, '2023-12-20', '2023_b', 'p', 'FB', 'BUF', 250, 25),
            (2023, '2023-12-20', '2023_c', 'q', 'WR', 'NYG', 100, 0),
            (2023, '2023-12-20', '2023_c', 'r', 'K', 'NYG', 0, 0),
            (2023, '2023-12-20', '2023_c', 's', 'LB', 'NYG', 1, 300),
            (2024, '2024-09-20', '2024_a', 'p', 'FB', 'CAR', 500, 0),
            (2024, '2024-09-20', '2024_a', 's', 'LB', 'CAR', 200, 400),
        ], columns=['season', 'gameday', 'game_id', 'pfr_player_id', 'position', 'team',
                    'offense_snaps', 'defense_snaps'])

    def test_target_follows_player_and_uses_primary_side(self):
        results = cohort(summarize(self.snaps), 2024, '2024-04-25', include_outcome=True)
        players = results.set_index('pfr_player_id')
        self.assertEqual(list(players.index), ['p', 'q', 's'])
        self.assertEqual(list(players.outcome), [1, 0, 0])
        self.assertEqual(players.loc['p', 'team'], 'BUF')
        self.assertEqual(players.loc['p', 'position'], 'FB')
        self.assertEqual(players.loc['p', 'snaps'], 500)
        self.assertEqual(players.loc['p', 'previousGames'], 1)
        self.assertEqual(players.loc['q', 'previousGames'], 0)

    def test_features_independent_of_next_season(self):
        cutoff = '2024-04-25'
        features = cohort(summarize(self.snaps), 2024, cutoff)
        prior = cohort(summarize(self.snaps[self.snaps.season < 2024]), 2024, cutoff)
        self.assertNotIn('outcome', features)
        pd.testing.assert_frame_equal(features, prior)
        with self.assertRaisesRegex(ValueError, 'post-cutoff'):
            cohort(summarize(self.snaps), 2024, '2023-12-20')

    def test_high_usage_group_uses_last_observed_team(self):
        forecast = cohort(summarize(self.snaps), 2024, '2024-04-25')
        forecast['probability'] = [0.6, 0.2, 0.4]
        forecast['prior500'] = forecast.snaps.ge(500)
        buffalo, giants = by_team(forecast, {'BUF', 'NYG'})
        self.assertEqual(buffalo['teamId'], 'BUF')
        self.assertEqual(buffalo['priorHighUsage'], 1)
        self.assertEqual(buffalo['expectedHighUsageAnywhere'], 0.6)
        self.assertEqual(giants['expectedHighUsageAnywhere'], 0)

    def test_artifact_covers_each_draft_and_only_prior_training(self):
        with (OUTPUT / 'projections.json').open() as source:
            projection = json.load(source)
        self.assertEqual(set(projection['drafts']), {str(year) for year in range(2018, 2027)})
        for year, draft in projection['drafts'].items():
            self.assertEqual(draft['trainedThroughOutcomeSeason'], int(year) - 1)
            self.assertLess(draft['latestRegularSeasonGame'], draft['informationCutoff'][:10])
            self.assertEqual(len({team['teamId'] for team in draft['teams']}), 32)
            for team in draft['teams']:
                self.assertGreaterEqual(team['priorHighUsage'], team['expectedHighUsageAnywhere'])
                self.assertGreaterEqual(team['expectedHighUsageAnywhere'], 0)


if __name__ == '__main__':
    unittest.main()
