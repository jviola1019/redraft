"""Fixed retrospective experiment described in score_marginal_protocol.md."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr, ndtri

import score_distribution as scores

SEED = 20261120
DRAWS = 4096
WINDOWS = [range(2013, 2016), range(2016, 2018)]
SCORE_TYPES = ("total", "margin", "home", "away")
GRID = np.linspace(-100, 160, 1041)


def load(source):
    games = pd.read_csv(source, low_memory=False)
    games = games[games.game_type.eq("REG") & games.season.between(1999, 2017)]
    games = games.dropna(subset=["home_score", "away_score"]).copy()
    for side in ("home", "away"):
        games[side + "_team"] = games[side + "_team"].replace(scores.ALIASES)
        games[side + "_score"] = games[side + "_score"].astype(int)
    return scores.add_prior_context(games)


def fit(games, year):
    law = scores.fit_score_law(games, year - 1)
    train = games[games.season.between(2000, year - 1)]
    recent = train[train.season.ge(year - 3)]
    law["meanTotal"] = float(recent.total.mean())
    residual = train.margin.to_numpy() - scores.expected_margin(train, law)
    signed = pd.DataFrame(
        {
            "team": np.r_[train.home_team, train.away_team],
            "season": np.r_[train.season, train.season],
            "residual": np.r_[residual, -residual],
        }
    ).groupby(["season", "team"]).residual.agg(["mean", "size"])
    signed = signed[signed["size"].ge(14)]
    reciprocal_games = np.mean(1 / signed["size"])
    residual_variance = float(np.var(residual, ddof=2))
    team_variance = (signed["mean"].var() - residual_variance * reciprocal_games) / (1 - reciprocal_games)
    team_variance = float(np.clip(team_variance, 0, 0.49 * residual_variance))
    law["marginSd"] = np.sqrt(residual_variance - 2 * team_variance)
    law["seasonShockSd"] = np.sqrt(team_variance)
    calibrations = []
    for side, sign in (("home", 1), ("away", -1)):
        centers = (law["meanTotal"] + sign * scores.expected_margin(recent, law)) / 2
        covariance = law["rho"] * law["marginSd"] * law["totalSd"]
        sd = np.sqrt(law["totalSd"] ** 2 + residual_variance + 2 * sign * covariance) / 2
        cdf = ndtr((GRID[:, None] - centers) / sd).mean(axis=1)
        support, count = np.unique(recent[side + "_score"], return_counts=True)
        support, count = support[support != 1], count[support != 1]
        calibrations.append((cdf, support, np.cumsum(count) / count.sum()))
    return law, calibrations


def map_score(latent, calibration):
    latent_cdf, support, empirical_cdf = calibration
    p = np.interp(latent, GRID, latent_cdf)
    return support[np.searchsorted(empirical_cdf, p, side="left")]


def draw(games, year, law, calibrations, draws):
    rng = np.random.default_rng(np.random.SeedSequence([SEED, year]))
    teams = sorted(set(games.home_team) | set(games.away_team))
    team_index = {team: index for index, team in enumerate(teams)}
    shocks = rng.normal(0, law["seasonShockSd"], size=(len(teams), draws))
    for game, expected in zip(games.itertuples(), scores.expected_margin(games, law)):
        home, away = team_index[game.home_team], team_index[game.away_team]
        z_margin, z_total, tie, winner = rng.random((4, draws))
        z_margin, z_total = ndtri(z_margin), ndtri(z_total)
        margin = expected + shocks[home] - shocks[away] + law["marginSd"] * z_margin
        rho = law["rho"]
        total = law["meanTotal"] + law["totalSd"] * (rho * z_margin + np.sqrt(1 - rho * rho) * z_total)
        baseline = scores.nfl_scores(np.maximum(6, total), margin, tie, winner)
        h = map_score((total + margin) / 2, calibrations[0])
        a = map_score((total - margin) / 2, calibrations[1])
        overtime = (h == a) & (tie > 0.12)
        home_win = winner < 1 / (1 + np.exp(-margin / 8))
        candidate = (h + 3 * (overtime & home_win), a + 3 * (overtime & ~home_win))
        yield game, home, away, expected, baseline, candidate


def metrics(h, a, game):
    result = {}
    forecast = (h + a, h - a, h, a)
    observed = (game.total, game.margin, game.home_score, game.away_score)
    for key, draws, actual in zip(SCORE_TYPES, forecast, observed):
        lo, hi = np.quantile(draws, [0.05, 0.95])
        mean_error = float(draws.mean() - actual)
        result[key] = {
            "crps": scores.crps(draws, actual),
            "mae": abs(mean_error),
            "bias": mean_error,
            "coverage": float(lo <= actual <= hi),
        }
    p = float(np.mean((h == 0) | (a == 0)))
    result["shutouts"] = {"brier": (p - game.shutout) ** 2, "predicted": p, "observed": float(game.shutout)}
    return result


def assess(games, year, draws):
    law, calibrations = fit(games, year)
    schedule = games[games.season.eq(year)]
    team_count = len(set(schedule.home_team) | set(schedule.away_team))
    rows = [{}, {}]
    for result in rows:
        result["metrics"] = []
        result["wins"] = np.zeros((team_count, draws))
        result["points"] = np.zeros((team_count, draws))
        result["residual"] = np.zeros((team_count, draws))
        result["residual_squared"] = np.zeros((team_count, draws))
    count = np.zeros(team_count)
    for game, hi, ai, expected, baseline, candidate in draw(schedule, year, law, calibrations, draws):
        for result, (h, a) in zip(rows, (baseline, candidate)):
            result["metrics"].append(metrics(h, a, game))
            residual = h - a - expected
            result["wins"][hi] += (h > a) + .5 * (h == a)
            result["wins"][ai] += (a > h) + .5 * (h == a)
            result["points"][hi] += h
            result["points"][ai] += a
            result["residual"][hi] += residual
            result["residual"][ai] -= residual
            result["residual_squared"][hi] += residual ** 2
            result["residual_squared"][ai] += residual ** 2
        count[hi] += 1
        count[ai] += 1
    output = []
    for result in rows:
        residual, square = result["residual"], result["residual_squared"]
        paired_product = np.sum(residual ** 2 - square, axis=0) / np.sum(count * (count - 1))
        residual_variance = np.sum(square, axis=0) / count.sum()
        output.append({
            "games": result["metrics"],
            "season": {
                "meanTeamWinsSd": float(np.std(result["wins"], axis=1).mean()),
                "meanTeamPointsSd": float(np.std(result["points"], axis=1).mean()),
                "sameTeamResidualCorrelation": float(paired_product.mean() / residual_variance.mean()),
            },
        })
    return output


def average(rows):
    return {key: float(np.mean([row[key] for row in rows])) for key in rows[0]}


def summarize(results):
    result = {}
    for index, model in enumerate(("baseline", "candidate")):
        games = [metrics for year in results for metrics in year[index]["games"]]
        result[model] = {
            "score": {key: average([row[key] for row in games]) for key in games[0]},
            "season": average([year[index]["season"] for year in results]),
        }
    baseline, candidate = (result[key]["score"] for key in ("baseline", "candidate"))
    bs, cs = (result[key]["season"] for key in ("baseline", "candidate"))
    result["criteria"] = {
        "totalCrpsImproves": candidate["total"]["crps"] < baseline["total"]["crps"],
        "shutoutBrierImproves": candidate["shutouts"]["brier"] < baseline["shutouts"]["brier"],
        "otherCrps": {key: candidate[key]["crps"] <= 1.01 * baseline[key]["crps"] for key in SCORE_TYPES[1:]},
        "mae": {key: candidate[key]["mae"] <= 1.01 * baseline[key]["mae"] for key in SCORE_TYPES},
        "coverage": {
            key: abs(candidate[key]["coverage"] - .9) <= abs(baseline[key]["coverage"] - .9) + .01
            for key in SCORE_TYPES
        },
        "dispersion": {
            key: abs(cs[key] / bs[key] - 1) <= .05
            for key in ("meanTeamWinsSd", "meanTeamPointsSd")
        },
        "positiveSharedDependence": cs["sameTeamResidualCorrelation"] > 0,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=scores.RAW)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".json"))
    args = parser.parse_args()
    games = load(args.source)
    results = {year: assess(games, year, DRAWS) for window in WINDOWS for year in window}
    output = {
        "sourceSha256": scores.sha(args.source),
        "seed": SEED,
        "drawsPerSeason": DRAWS,
        "windows": [
            {"years": list(window), **summarize([results[year] for year in window])} for window in WINDOWS
        ],
        "byYear": {year: summarize([result]) for year, result in results.items()},
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
