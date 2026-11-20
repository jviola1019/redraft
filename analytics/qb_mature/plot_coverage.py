"""Show observed five-year QB participation and cutoff-specific predictive intervals."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

directory = Path(__file__).resolve().parent
records = json.loads((directory / "qb_mature_donor_predictions.json").read_text())
fig, axes = plt.subplots(3, 1, figsize=(8, 5.3), sharex=True)
for axis, year in zip(axes, (2019, 2020, 2021)):
    cohort = [row for row in records if row["cohort"] == year]
    for label, color, y in (("candidate", "#377365", .72), ("baseline", "#8798a5", .46)):
        low, high = (cohort[0][label][field] for field in ("lower95", "upper95"))
        assert all(row[label]["lower95"] == low and row[label]["upper95"] == high for row in cohort)
        axis.barh(y, high - low, left=low, height=.18, color=color)
    # Separate nearby observations vertically. Each dot corresponds to an observed player.
    lanes = []
    for row in sorted(cohort, key=lambda r: r["candidate"]["actual"]):
        observed = row["candidate"]["actual"]
        lane = next((i for i, last in enumerate(lanes) if observed-last >= 105), len(lanes))
        if lane == len(lanes):
            lanes.append(observed)
        lanes[lane] = observed
        axis.plot(observed, -.16 - .11*lane, "o", ms=4.1, color="#a63f25")
    axis.set_ylim(min(-1, -.35 - .11*len(lanes)), 1)
    axis.set_xlim(left=-80)
    axis.set_ylabel(f"{year}\nn = {len(cohort)}", rotation=0, labelpad=30, va="center")
    axis.set_yticks([])
    axis.spines[["top","left","right"]].set_visible(False)
    axis.grid(axis="x", alpha=.14)
axes[-1].set_xlabel("Recorded or projected snaps over five NFL seasons")
fig.suptitle("Later eligible QB careers widen the forecast range", x=.12, ha="left", weight="bold")
fig.legend(handles=[Patch(color="#377365", label="All mature donors · 95% interval"),
                    Patch(color="#8798a5", label="2013 donors · 95% interval"),
                    Line2D([], [], color="#a63f25", marker="o", linestyle="", label="Observed QB")],
           loc="upper left", bbox_to_anchor=(.107,.925), ncol=3, fontsize=8, frameon=False)
fig.subplots_adjust(left=.13, right=.97, top=.81, bottom=.13, hspace=.22)
fig.savefig(directory / "five-year-qb-coverage.png", dpi=145)
