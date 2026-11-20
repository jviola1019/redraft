"""Reconcile public discovery evidence without persisting source tables."""

import csv
import hashlib
import io
from collections import Counter
from pathlib import Path
from urllib.request import urlopen

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
RELEASE = (
    "https://github.com/blnkpagelabs/nflscraPy/releases/download/"
    "SnapCounts/Snapcounts-2012.csv"
)
TEAM_ALIASES_2012 = {"LA": "STL", "JAC": "JAX", "LV": "OAK", "LAC": "SD"}
RELEASE_SHA256 = "960b78273fff475d3382b9708021860f9408136a68bef10ed6bddf8c86934eed"


def read_csv(filename):
    with (RAW / filename).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pfr_slug(url):
    return url.rsplit("/", 1)[-1].removesuffix(".htm")


def phases(row, fields):
    values = tuple(int(row[field]) for field in fields)
    assert all(value >= 0 for value in values), values
    return values


def main():
    schedule = read_csv("games.csv")
    completed = [
        game for game in schedule
        if game["season"] == "2012" and game["away_score"] and game["home_score"]
    ]
    regular_games = {game["pfr"]: game for game in completed if game["game_type"] == "REG"}
    postseason = {game["pfr"] for game in completed if game["game_type"] not in {"PRE", "REG"}}
    assert len(regular_games) == 256

    with urlopen(RELEASE, timeout=20) as response:
        contents = response.read()
    assert hashlib.sha256(contents).hexdigest() == RELEASE_SHA256
    data = list(csv.DictReader(io.StringIO(contents.decode("utf-8-sig"))))
    assert {row["season"] for row in data} == {"2012"}
    games = {pfr_slug(row["boxscore_stats_link"]) for row in data}
    assert games == regular_games.keys() | postseason
    print(f"2012 public release SHA-256 {RELEASE_SHA256}")
    print(f"2012 public release {len(data)} rows, {len(games)} games")

    historical = {}
    phase_fields = ("snap_count_offense", "snap_count_defense", "snap_count_special_teams")
    team_counts = Counter()
    all_dated_teams = set()
    unidentified = 0
    for row in data:
        pfr_game = pfr_slug(row["boxscore_stats_link"])
        if pfr_game not in regular_games:
            continue
        game = regular_games[pfr_game]
        player = pfr_slug(row["player_href"])
        team = TEAM_ALIASES_2012.get(row["alias"], row["alias"])
        assert row["event_date"] == game["gameday"], (pfr_game, player)
        assert team in {game["away_team"], game["home_team"]}, (pfr_game, team)
        team_counts[team] += 1
        all_dated_teams.add((game["game_id"], team))
        counts = phases(row, phase_fields)
        if not player:
            assert row["position"] == "LB"
            unidentified += 1
            continue
        row_key = (game["game_id"], team, player)
        assert row_key not in historical, row_key
        historical[row_key] = counts
    assert len(all_dated_teams) == 512
    print(
        f"2012 schedule match {len(regular_games)} regular-season and {len(postseason)} "
        f"postseason games; {len(historical) + unidentified} regular-season rows, {len(team_counts)} "
        f"franchises, {len(all_dated_teams)} team-games; {len(historical)} unique identified rows, "
        f"{unidentified} anonymous linebacker rows"
    )
    # Discrete comparison facts from public NFL gamebooks cited in the memo.
    # Empty DNP and inactive keys remain absence, not observed data.
    samples = {
        ("2012_01_IND_CHI", "IND", "LuckAn00"): (66, 0, 0),
        ("2012_01_SF_GB", "SF", "SmitAl03"): (65, 0, 0),
        ("2012_01_SF_GB", "SF", "KaepCo00"): (1, 0, 0),
        ("2012_01_IND_CHI", "IND", "StanDr00"): None,
        ("2012_01_IND_CHI", "IND", "HarnCh00"): None,
    }
    for key, expected in samples.items():
        assert historical.get(key) == expected, (key, expected, historical.get(key))
    print("2012 official comparisons: 3 positive player-game matches, 2 expected absent keys")

    cohort = [
        row for row in read_csv("combine.csv") if row["season"] == "2012" and row["pos"] == "QB"
    ]
    observed = {key[2] for key, counts in historical.items() if sum(counts) > 0}
    identified = {row["pfr_id"] for row in cohort if row["pfr_id"]}
    print(
        f"2012 combine QBs: {len(cohort)} rows, {len(identified)} existing IDs, "
        f"{len(observed & identified)} existing IDs with positive 2012 source observations"
    )

    overlap = {row["pfr_player_id"]: row for row in read_csv("snap_counts_2013.csv")
               if row["game_id"] == "2013_13_TEN_IND"}
    controls = {
        "LuckAn00": (65, 0, 0),
        "FitzRy00": (75, 0, 0),
        "BethAn20": (0, 75, 0),
        "PollBe20": (0, 65, 7),
        "McAfPa44": (0, 0, 17),
        "HarvMa00": (2, 2, 22),
    }
    for player, expected in controls.items():
        counts = phases(overlap[player], ("offense_snaps", "defense_snaps", "st_snaps"))
        assert counts == expected, (player, expected, counts)
    print("2013 official overlap: 6 players matched exactly on all three phases")


if __name__ == "__main__":
    main()
