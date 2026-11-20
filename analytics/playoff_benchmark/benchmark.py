"""Paired retrospective benchmark for the fixed historical simulator audit."""
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GAME_SOURCE = ROOT / "data/raw/games.csv"
AUDIT_SOURCE = HERE.parent / "playoff_forecast_results.json"
PROTOCOL = HERE / "protocol.json"
ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LAR", "LA": "LAR"}


def franchise(team):
    return ALIASES.get(team, team)


def slots(year):
    return 12 if year < 2020 else 14


def completed_seasons(games, origin):
    """Filter before looking at scores, franchise identities or qualification."""
    cutoff = f"{origin}-04-01"
    grouped = defaultdict(list)
    for game in games:
        year = int(game["season"])
        if 2002 <= year < origin and game["gameday"] < cutoff:
            if game["home_score"] and game["away_score"]:
                grouped[year].append(game)

    seasons = {}
    for year, season_games in sorted(grouped.items()):
        scores = defaultdict(list)
        qualifiers = set()
        game_types = Counter()
        for game in season_games:
            home = franchise(game["home_team"])
            away = franchise(game["away_team"])
            margin = int(game["home_score"]) - int(game["away_score"])
            game_type = game["game_type"]
            game_types[game_type] += 1
            if game_type == "REG":
                scores[home].append(margin)
                scores[away].append(-margin)
            else:
                qualifiers.update((home, away))
        expected_regular = 256 if year < 2021 else 272 - (year == 2022)
        expected_types = {
            "REG": expected_regular, "WC": slots(year) - 8, "DIV": 4, "CON": 2, "SB": 1
        }
        if (game_types != expected_types or len(scores) != 32
                or len(qualifiers) != slots(year) or not qualifiers <= scores.keys()):
            raise ValueError(f"Incomplete or invalid source season {year} at origin {origin}")
        seasons[year] = {
            "strength": {team: mean(games) / 7 for team, games in sorted(scores.items())},
            "qualified": qualifiers,
            "maxGameDate": max(game["gameday"] for game in season_games),
        }
    if sorted(seasons) != list(range(2002, origin)):
        raise ValueError(f"Missing source seasons at origin {origin}")
    return seasons


def sigmoid(value):
    numerator = math.exp(-abs(value))
    return 1 / (1 + numerator) if value >= 0 else numerator / (1 + numerator)


def calibrated_probabilities(logits, slot_count):
    low, high = -max(logits) - 30, -min(logits) + 30
    for _ in range(38):
        intercept = (low + high) / 2
        if sum(sigmoid(value + intercept) for value in logits) < slot_count:
            low = intercept
        else:
            high = intercept
    return [sigmoid(value + (low + high) / 2) for value in logits]


def fit_slope(pairs):
    """Solve the derivative of the profiled penalized logistic log likelihood."""
    def derivative(slope):
        gradient = slope
        for strengths, outcomes in pairs:
            predicted = calibrated_probabilities([slope * x for x in strengths], sum(outcomes))
            gradient += sum(x * (p - y) for x, p, y in zip(strengths, predicted, outcomes))
        return gradient

    low, high = -1.0, 1.0
    while derivative(low) > 0:
        low *= 2
    while derivative(high) < 0:
        high *= 2
    for _ in range(30):
        slope = (low + high) / 2
        if derivative(slope) < 0:
            low = slope
        else:
            high = slope
    return (low + high) / 2


def forecast_origin(games, origin, horizons):
    seasons = completed_seasons(games, origin)
    metadata, forecasts = {}, {}
    strengths = seasons[origin - 1]["strength"]
    for horizon in horizons:
        pairs = []
        for season in range(2002, origin - horizon):
            old_strength = seasons[season]["strength"]
            qualified = seasons[season + horizon]["qualified"]
            pairs.append((list(old_strength.values()), [int(team in qualified) for team in old_strength]))
        slope = fit_slope(pairs)
        year = origin + horizon - 1
        logits = [slope * strength for strength in strengths.values()]
        available = calibrated_probabilities(logits, slots(origin))
        aligned = calibrated_probabilities(logits, slots(year))
        forecasts[horizon] = {
            team: {"benchmarkProbability": p, "realizedFormatProbability": q}
            for team, p, q in zip(strengths, available, aligned)
        }
        metadata[horizon] = {
            "slope": slope, "trainingTargetYears": list(range(2002 + horizon, origin)),
            "trainingRows": 32 * len(pairs), "latestFeatureSeason": origin - 1,
            "latestSourceGameDate": seasons[origin - 1]["maxGameDate"],
        }
    return forecasts, metadata


def summarize(rows):
    def brier(column):
        return mean((row[column] - row["actual"]) ** 2 for row in rows)

    raw = brier("probability")
    benchmark = brier("benchmarkProbability")
    aligned = brier("realizedFormatProbability")
    prevalence = brier("slotPrevalence")
    return {"rows": len(rows), "actualSeasons": sorted({row["year"] for row in rows}),
            "distinctActualTeamSeasons": len({(row["year"], row["team"]) for row in rows}),
            "simulatorBrier": raw, "benchmarkBrier": benchmark, "realizedFormatBrier": aligned,
            "realizedPrevalenceBrier": prevalence, "pairedGap": raw - benchmark,
            "realizedFormatPairedGap": raw - aligned, "simulatorSkillVersusBenchmark": 1 - raw / benchmark}


def block_sensitivity(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["year"]].append(row)
    years = sorted(groups)
    differences = {}
    for size in (1, 2):
        excluded_blocks = [years[start:start + size] for start in range(len(years) - size + 1)]
        omitted = {
            "-".join(map(str, block)): summarize([row for year in years if year not in block for row in groups[year]])["pairedGap"]
            for block in excluded_blocks
        }
        differences[str(size)] = {
            "minPairedGap": min(omitted.values()), "maxPairedGap": max(omitted.values()), "byOmittedBlock": omitted
        }
    return differences


def compare(rows, simulator_metrics):
    result = summarize(rows)
    assert abs(result["simulatorBrier"] - simulator_metrics["brier"]) < 1e-12
    adjusted = simulator_metrics["biasAdjustedBrier"]
    return {**result, "simulatorAdjustedBrier": adjusted,
            "simulatorAdjustedPairedGap": adjusted - result["benchmarkBrier"],
            "simulatorMonteCarloSE": simulator_metrics["deltaMethodMonteCarloSE"],
            "blockSensitivity": block_sensitivity(rows),
            "byActualYear": {year: summarize([row for row in rows if row["year"] == year])
                             for year in result["actualSeasons"]}}


def run():
    protocol = json.loads(PROTOCOL.read_text())
    with GAME_SOURCE.open(newline="") as source:
        games = list(csv.DictReader(source))
    predictions = {}
    fits = {}
    for origin in protocol["origins"]:
        horizons = [h for h in protocol["horizons"] if origin + h - 1 <= 2025]
        forecasts, fits[origin] = forecast_origin(games, origin, horizons)
        for horizon, teams in forecasts.items():
            predictions.update({(origin, horizon, team): p for team, p in teams.items()})

    audit = json.loads(AUDIT_SOURCE.read_text())
    observed = completed_seasons(games, 2026)
    rows = []
    keys = set()
    for simulator in audit["rows"]:
        origin, horizon, year, team = (simulator[key] for key in ("origin", "horizon", "year", "team"))
        key = (origin, horizon, franchise(team))
        assert key not in keys and year == origin + horizon - 1
        assert simulator["actual"] == int(franchise(team) in observed[year]["qualified"])
        keys.add(key)
        rows.append({k: v for k, v in simulator.items() if k != "draws"} | predictions[key])
    assert len(rows) == 960 and keys == predictions.keys()
    report = {
        "protocol": protocol,
        "sourceHashes": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (Path(__file__), PROTOCOL, GAME_SOURCE, AUDIT_SOURCE)},
        "fitMetadata": fits,
        "overall": compare(rows, audit["overall"]),
        "byHorizon": {h: compare([row for row in rows if row["horizon"] == h], audit["byHorizon"][str(h)])
                      for h in protocol["horizons"]},
    }
    (HERE / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    with (HERE / "predictions.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run()
