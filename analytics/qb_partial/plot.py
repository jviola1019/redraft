"""Render paired distribution scores and cumulative interval coverage."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

HERE = Path(__file__).resolve().parent
results = json.loads((HERE / "results.json").read_text())["metrics"]
plt.rcParams.update({"font.size": 11, "axes.spines.right": False, "axes.spines.top": False,
                     "axes.labelcolor": "#293747", "text.color": "#162433"})
ages = ("1", "2", "3", "4")
labels = [f"{age}\n(n={results['annual'][age]['overall']['n']})" for age in ages]
x = range(1, 5)
baseline_color, candidate_color = "#6a7180", "#137c72"

fig, ax = plt.subplots(2, 2, figsize=(10, 6.6), sharex=True, constrained_layout=True)
fig.suptitle("QB forecast accuracy by observed horizon", x=.02, ha="left", fontsize=21, weight="bold")
for row, kind in enumerate(("snaps", "games")):
    for col, target in enumerate(("annual", "cumulative")):
        axis = ax[row, col]
        paired = [results[target][age]["overall"][kind]["pairedCrps"] for age in ages]
        delta = [p["difference"] for p in paired]
        bounds = list(zip(*[p["bootstrap95"] for p in paired]))
        axis.errorbar(x, delta, [[d - lo for d, lo in zip(delta, bounds[0])],
                                [hi - d for d, hi in zip(delta, bounds[1])]],
                      color=candidate_color, marker="o", capsize=4)
        axis.axhline(0, lw=1, color=baseline_color, ls="--")
        axis.grid(axis="y", alpha=.16)
        axis.set_ylabel("CRPS difference · " + kind)
        if row == 0:
            axis.set_title("Season alone" if target == "annual" else "Cumulative through season")
        if row == 1:
            axis.set_xticks(list(x), labels)
            axis.set_xlabel("Career season")
fig.supxlabel("Candidate minus production. Negative favors the candidate. Bars show paired 95% bootstrap intervals.",
             x=.02, ha="left", fontsize=10)
fig.savefig(HERE / "partial-qb-crps.png", dpi=170)

fig, ax = plt.subplots(2, 2, figsize=(10, 6.6), sharex=True, constrained_layout=True)
fig.suptitle("Coverage and width of cumulative QB forecasts", x=.02, ha="left", fontsize=21, weight="bold")
for row, kind in enumerate(("snaps", "games")):
    for col, (metric, label) in enumerate((("coverage", "Observed coverage"), ("meanWidth", "Mean width"))):
        axis = ax[row, col]
        for arm, color in (("baseline", baseline_color), ("candidate", candidate_color)):
            values = [results["cumulative"][age]["overall"][kind][arm]["interval95"][metric]
                      for age in ages]
            axis.plot(x, values, color=color, marker="o",
                      label="Production" if arm == "baseline" else "Mature expansion")
        if metric == "coverage":
            axis.axhline(.95, color="#242f41", ls="--", lw=1, label="95% nominal")
            axis.yaxis.set_major_formatter(PercentFormatter(xmax=1))
            axis.set_ylim(.45, 1.02)
        axis.set_ylabel(kind.title())
        axis.grid(axis="y", alpha=.16)
        if row == 0:
            axis.set_title(label)
        if row == 1:
            axis.set_xticks(list(x), labels)
            axis.set_xlabel("Career seasons observed")
ax[0, 0].legend(frameon=False, loc="lower left", fontsize=9)
fig.savefig(HERE / "partial-qb-coverage.png", dpi=170)
