"""Fig. R: FCR by mechanism across robustness levels (addendum A2, exploratory)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # validated categorical slots 1-4
INK, INK2, GRID = "#1f1f1e", "#5f5e58", "#e6e5e0"
SERIES = [("B1", "B1 Majority", "o", "-"), ("B2", "B2 Authority-only", "s", "--"),
          ("B3", "B3 Trust-only", "^", "-."), ("P-V", "Hybrid (P−V = P)", "D", "-")]
PANELS = [("R1a_acc_other", "S1", "Off-home accuracy (S1)", "accuracy", 0.75),
          ("R2_shared_rho", "S1", "Shared R+S error rate ρ (S1)", "ρ", 0.0),
          ("R3_label_noise_F1", "S2", "Label noise, realistic feedback (S2)", "e", 0.0)]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "xtick.color": INK2,
                     "ytick.color": INK2, "savefig.dpi": 300})


def main(res_dir, out_dir):
    a = pd.read_csv(Path(res_dir) / "addendum_A2_runs.csv")
    a = a[a.window == "all"]
    a["FCR"] = 100 * a.false_commits / a.commits
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6))
    for ax, (test, sc, title, xl, main_lvl) in zip(axes, PANELS):
        q = a[(a.test == test) & (a.scenario == sc)].groupby(["mechanism", "level"]).FCR.mean().reset_index()
        for (m, lab, mk, ls), c in zip(SERIES, SLOTS):
            s = q[q.mechanism == m].sort_values("level")
            ax.plot(s.level, s.FCR, ls, color=c, lw=1.5, marker=mk, ms=4, mec="white", mew=0.7, label=lab)
        ax.axvline(main_lvl, color=INK2, lw=0.8, ls=":")
        ax.set_title(title, fontsize=8, color=INK, loc="left")
        ax.set_xlabel(xl)
        ax.set_ylim(bottom=0)
    axes[0].set_ylabel("False-commit rate, FCR (%)")
    axes[0].text(0.76, 0.55, "main study", fontsize=6.5, color=INK2, rotation=90, va="bottom",
                 transform=axes[0].get_xaxis_transform())
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Fig. R  Robustness (exploratory, 100 seeds): weighting beats majority at every level tested",
                 x=0.01, ha="left", fontsize=8.5, color=INK)
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(Path(out_dir) / "figR_robustness.png")
    fig.savefig(Path(out_dir) / "figR_robustness.pdf")


if __name__ == "__main__":
    main(*sys.argv[1:3])
