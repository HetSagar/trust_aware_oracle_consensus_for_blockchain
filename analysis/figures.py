"""Table 1, Fig. 1 and Fig. 2 from saved runs (protocol, Planned exhibits).

    python analysis/figures.py results/final/runs.csv analysis/out

Palette: reference categorical slots 1-4, validated (CVD PASS; two slots under 3:1
contrast, so every series also gets its own marker, line style and direct label).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).parent))
from stats import add_rates  # noqa: E402

SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, GRID = "#1f1f1e", "#5f5e58", "#e6e5e0"
MECH_LABEL = {"B1": "B1 Majority", "B2": "B2 Authority-only", "B3": "B3 Trust-only",
              "P-V": "P−V Hybrid, no veto", "P": "P Hybrid + veto", "EQ": "Equal weights"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "savefig.dpi": 300,
})


def ci(x: pd.Series) -> float:
    x = x.dropna()
    return st.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


def table1(d: pd.DataFrame, out: Path) -> pd.DataFrame:
    core = d[(d.experiment == "core") & (d.window == "all") & d.scenario.isin(["S1", "S2", "S3", "S4"])]
    g = core.groupby(["mechanism", "scenario"])[["FCR", "VCC", "ER", "FAR"]].agg(["mean", "std"])
    g.to_csv(out / "table1_full.csv")
    order = ["B1", "B2", "B3", "P-V", "P"]
    rows = []
    for m in order:
        row = {"Mechanism": MECH_LABEL[m]}
        for s in ["S1", "S2", "S3", "S4"]:
            for metric in ("FCR", "VCC"):
                row[f"{s} {metric}"] = f"{g.loc[(m, s), (metric, 'mean')]:.2f} ({g.loc[(m, s), (metric, 'std')]:.2f})"
        rows.append(row)
    t1 = pd.DataFrame(rows)
    t1.to_csv(out / "table1.csv", index=False)
    er = core.groupby(["mechanism", "scenario"]).ER.mean().unstack().loc[order].round(1)
    er.to_csv(out / "escalation_rates.csv")
    return t1


def fig1(d: pd.DataFrame, out: Path) -> None:
    th = d[(d.experiment == "theta") & (d.window == "all")]
    m = th.groupby(["mechanism", "theta"])[["FCR", "VCC"]].mean().reset_index()
    # P and P-V are identical in S2 (no blind offices): verified, drawn as one series.
    assert np.allclose(m[m.mechanism == "P"].FCR.values, m[m.mechanism == "P-V"].FCR.values)
    series = [("EQ", "Equal weights", "o", "-"), ("B2", "B2 Authority-only", "s", "--"),
              ("B3", "B3 Trust-only", "^", "-."), ("P-V", "P−V and P (identical)", "D", "-")]
    fig, ax = plt.subplots(figsize=(4.8, 3.3))
    for (mech, label, mk, ls), color in zip(series, SLOTS):
        s = m[m.mechanism == mech].sort_values("theta")
        ax.plot(s.VCC, s.FCR, ls, color=color, lw=1.6, marker=mk, ms=4.5,
                mec="white", mew=0.8, label=label, zorder=3)
        if mech == "P-V":
            for _, r in s.iterrows():
                if any(np.isclose(r.theta, v) for v in (0.5, 0.65, 0.8, 0.9)):
                    ax.annotate(f"θ={r.theta:.2f}", (r.VCC, r.FCR), textcoords="offset points",
                                xytext=(-2, -13) if np.isclose(r.theta, 0.9) else (5, 4),
                                fontsize=7, color=INK2)
    ax.set_xlabel("Valid-commit coverage, VCC (%)  → better")
    ax.set_ylabel("False-commit rate, FCR (%)  ← better")
    ax.set_title("Fig. 1  Commit threshold trade-off after Revenue degrades (S2)",
                 fontsize=8.5, color=INK, loc="left")
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.text(0.99, 0.02, "Means over 100 seeds; θ from 0.50 to 0.90 in steps of 0.05",
            transform=ax.transAxes, ha="right", fontsize=6.5, color=INK2)
    fig.tight_layout()
    fig.savefig(out / "fig1_threshold_tradeoff.png")
    fig.savefig(out / "fig1_threshold_tradeoff.pdf")
    plt.close(fig)
    m.to_csv(out / "fig1_data.csv", index=False)


def fig2(d: pd.DataFrame, out: Path) -> None:
    f = d[(d.experiment == "feedback") & (d.window == "all") & (d.mechanism == "P")]
    f0 = f[f.regime == "F0"].FCR
    f1 = f[f.regime == "F1"]
    rows = []
    fig, ax = plt.subplots(figsize=(4.8, 3.1))
    ax.axhspan(f0.mean() - ci(f0), f0.mean() + ci(f0), color=GRID, alpha=0.7, lw=0, zorder=1)
    ax.axhline(f0.mean(), color=INK2, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.text(0.287, f0.mean() - 0.012, "F0 (ideal)", ha="right", va="top", fontsize=7, color=INK2)
    offsets = {0: -0.004, 50: 0.0, 200: 0.004}
    for (delay, mk, ls), color in zip(((0, "o", "-"), (50, "s", "--"), (200, "^", "-.")), SLOTS):
        s = f1[f1.delay == delay].groupby("audit").FCR
        mean, err = s.mean(), s.apply(ci)
        x = mean.index.values + offsets[delay]
        ax.errorbar(x, mean.values, yerr=err.values, color=color, lw=1.6, ls=ls, marker=mk,
                    ms=4.5, mec="white", mew=0.8, capsize=2.5, elinewidth=1, zorder=3,
                    label=f"delay d = {delay} transfers")
        for a, mu, e in zip(mean.index, mean.values, err.values):
            rows.append(dict(delay=delay, audit=a, FCR_mean=mu, ci95=e))
    rows.append(dict(delay="F0", audit=np.nan, FCR_mean=f0.mean(), ci95=ci(f0)))
    ax.set_xticks([0, 0.05, 0.2])
    ax.set_xticklabels(["0", "0.05", "0.20"])
    ax.set_xlim(-0.015, 0.29)
    ax.set_xlabel("Audit rate of committed transfers, a")
    ax.set_ylabel("False-commit rate of P, FCR (%)")
    ax.set_title("Fig. 2  P under realistic feedback (F1) in S2, 100 seeds",
                 fontsize=8.5, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "fig2_feedback.png")
    fig.savefig(out / "fig2_feedback.pdf")
    plt.close(fig)
    pd.DataFrame(rows).to_csv(out / "fig2_data.csv", index=False)


def main(runs_csv: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    d = add_rates(pd.read_csv(runs_csv))
    print(table1(d, out).to_string(index=False))
    fig1(d, out)
    fig2(d, out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
