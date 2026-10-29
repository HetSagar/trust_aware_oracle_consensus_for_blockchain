"""Build every figure and table for the LNCS paper from saved results.

    python paper_assets/build_assets.py

Outputs (paper_assets/):
  figures/  figN_*.pdf (vector, fonts embedded), .eps, .svg, and .png at 1200 dpi
  tables/   tabNN_*.tex (booktabs, for LaTeX) and tables_for_word.docx (all tables, Word)
LNCS rules applied (Springer Guidelines for Authors of Proceedings): vector figures preferred,
raster line art >= 800 dpi (1200 used), lettering >= 6 pt (7-8 pt used), legible in grayscale,
figure captions below / table captions above (captions are in captions.md, not in the images),
no colour in tables. Figures are sized for the LNCS text width of 122 mm.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))
from landval.model import CHECKS, DEFAULT_AUTHORITY, MECHANISMS, ORACLES, Params, validate  # noqa: E402
from traces import trace  # noqa: E402

OUT = ROOT / "paper_assets"
FIG, TAB = OUT / "figures", OUT / "tables"
RES, AOUT = ROOT / "results" / "final", ROOT / "analysis" / "out"
MM = 1 / 25.4
TEXTWIDTH = 122 * MM

# Validated categorical slots 1-4 (CVD PASS); every series also has its own marker and dash.
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, GRID = "#000000", "#4a4a4a", "#dddddd"

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8,
    "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.edgecolor": INK2, "axes.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.4,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "lines.linewidth": 1.2, "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})
SERIES = [("B1", "B1 Majority", "o", "-"), ("B2", "B2 Authority-only", "s", "--"),
          ("B3", "B3 Trust-only", "^", "-."), ("P-V", "Hybrid (P−V = P)", "D", ":")]


def save(fig, name):
    for ext in ("pdf", "eps", "svg"):
        fig.savefig(FIG / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(FIG / f"{name}.png", dpi=1200, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rates(d):
    d = d.copy()
    d["FCR"] = 100 * d.false_commits / d.commits.where(d.commits > 0)
    d["VCC"] = 100 * d.valid_commits / d.valid
    return d


def fmt(x):
    """+0.00 style, with a third decimal when two would round a nonzero value to 0.00."""
    return f"{x:+.3f}" if abs(x) < 0.005 and x != 0 else f"{x:+.2f}"


def ci_half(x):
    x = x.dropna()
    return st.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


# ------------------------------------------------------------------ figures
def fig1_system():
    fig, ax = plt.subplots(figsize=(119 * MM, 60.5 * MM))
    ax.set_position([0, 0, 1, 1]); ax.set_xlim(0, 122); ax.set_ylim(0, 62); ax.axis("off")

    def box(x, y, w, h, lines, bold_first=True, fill="white", lw=0.7):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.5",
                                    fc=fill, ec=INK, lw=lw))
        n = len(lines)
        for j, s in enumerate(lines):
            yy = y + h / 2 + (n - 1) * 1.9 - j * 3.8
            ax.text(x + w / 2, yy, s, ha="center", va="center", fontsize=7 if j else 7.5,
                    fontweight="bold" if (j == 0 and bold_first) else "normal", color=INK)

    def arrow(x0, y0, x1, y1, dashed=False):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=0.7, color=INK, mutation_scale=7,
                                    linestyle=(0, (3, 2)) if dashed else "-", shrinkA=0, shrinkB=0))

    # Units are millimetres (axis 122 x 62 in a 122 x 62 mm figure). Box widths are sized for
    # 7-7.5 pt Times (about 1.3-1.6 mm per character), with margin.
    box(0.5, 47, 32, 9, ["Revenue (R)", "home check: own"])
    box(0.5, 35, 32, 9, ["Sub-Registrar (S)", "home check: deed"])
    box(0.5, 23, 32, 9, ["Judiciary (J)", "home check: restr"])
    ax.text(0.5, 19.2, "Reports: +1, −1 or ∅", fontsize=7, color=INK2, va="center")
    ax.text(0.5, 16.2, "on every check (Table 2)", fontsize=7, color=INK2, va="center")
    box(39, 22, 50, 36, ["Validator", "Per check: support $S_k$, coverage $Q_k$",
                         "Commit only if all three pass", "P only: proceedings veto",
                         "Never rejects; never decides title"])
    for y in (51.5, 39.5, 27.5):
        arrow(32.5, y, 39, y)
    box(95, 45, 24, 10, ["ESCALATE", "to a person"])
    box(95, 26, 24, 10, ["COMMIT", "write to ledger"], fill="#e8e8e8", lw=1.1)
    arrow(89, 50, 95, 50)
    arrow(89, 31, 95, 31)
    box(39, 1, 80, 14, ["Verified labels (after delay d)", "every escalation, after review",
                        "committed requests audited at rate a"])
    ax.plot([119, 121.3, 121.3], [50, 50, 8], color=INK, lw=0.7)
    arrow(121.3, 8, 119.1, 8)
    arrow(107, 26, 107, 15.1, dashed=True)
    ax.text(108.5, 20.5, "audit", fontsize=7, color=INK2, va="center")
    arrow(55, 15, 55, 22)
    ax.text(56.5, 18.5, "update $T_{ik}$", fontsize=7, color=INK2, va="center")
    save(fig, "fig1_system")


def fig2_threshold():
    d = rates(pd.read_csv(RES / "runs.csv"))
    th = d[(d.experiment == "theta") & (d.window == "all")]
    m = th.groupby(["mechanism", "theta"])[["FCR", "VCC"]].mean().reset_index()
    fig, ax = plt.subplots(figsize=(TEXTWIDTH, 72 * MM))
    series = [("EQ", "Equal weights", "o", "-"), ("B2", "B2 Authority-only", "s", "--"),
              ("B3", "B3 Trust-only", "^", "-."), ("P-V", "Hybrid (P−V = P)", "D", ":")]
    for (mech, lab, mk, ls), col in zip(series, C):
        s = m[m.mechanism == mech].sort_values("theta")
        ax.plot(s.VCC, s.FCR, ls, color=col, marker=mk, ms=3.6, mec="black", mew=0.4, label=lab)
        if mech == "P-V":
            for _, r in s.iterrows():
                for v, off in ((0.5, (4, 3)), (0.65, (-30, 6)), (0.8, (4, 3)), (0.9, (-2, -10))):
                    if np.isclose(r.theta, v):
                        ax.annotate(f"θ = {v:.2f}", (r.VCC, r.FCR), textcoords="offset points",
                                    xytext=off, fontsize=7, color=INK2)
    ax.set_xlabel("Valid-commit coverage, VCC (%)")
    ax.set_ylabel("False-commit rate, FCR (%)")
    ax.set_xlim(left=0); ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "fig2_threshold_tradeoff")


def fig3_feedback():
    d = rates(pd.read_csv(RES / "runs.csv"))
    f = d[(d.experiment == "feedback") & (d.window == "all") & (d.mechanism == "P")]
    f0 = f[f.regime == "F0"].FCR
    f1 = f[f.regime == "F1"]
    fig, ax = plt.subplots(figsize=(TEXTWIDTH, 62 * MM))
    ax.axhspan(f0.mean() - ci_half(f0), f0.mean() + ci_half(f0), color="#eeeeee", lw=0, zorder=0)
    ax.axhline(f0.mean(), color=INK2, lw=0.8, ls=(0, (4, 3)))
    ax.text(0.125, f0.mean() - 0.012, "ideal feedback F0 (band: 95% CI)", ha="center", va="top",
            fontsize=7, color=INK2)
    for (dl, mk, ls, off), col in zip(((0, "o", "-", -0.004), (50, "s", "--", 0), (200, "^", "-.", 0.004)), C):
        s = f1[f1.delay == dl].groupby("audit").FCR
        mean, err = s.mean(), s.apply(ci_half)
        ax.errorbar(mean.index.values + off, mean.values, yerr=err.values, color=col, ls=ls, marker=mk,
                    ms=3.6, mec="black", mew=0.4, capsize=2, elinewidth=0.7, label=f"F1, delay d = {dl}")
    ax.set_xticks([0, 0.05, 0.2]); ax.set_xticklabels(["0", "0.05", "0.20"])
    ax.set_xlim(-0.015, 0.29)
    ax.set_xlabel("Audit rate of committed requests, a")
    ax.set_ylabel("False-commit rate of P, FCR (%)")
    ax.legend(frameon=False, loc="lower right")
    save(fig, "figS1_feedback")


def fig4_robustness():
    a = pd.read_csv(RES / "addendum_A2_runs.csv")
    a = a[a.window == "all"].copy()
    a["FCR"] = 100 * a.false_commits / a.commits
    panels = [("R1a_acc_other", "S1", "(a) Off-home accuracy, S1", "accuracy", 0.75),
              ("R2_shared_rho", "S1", "(b) Shared R+S errors, S1", "shared error rate ρ", 0.0),
              ("R3_label_noise_F1", "S2", "(c) Label noise, F1, S2", "label noise rate e", 0.0)]
    fig, axes = plt.subplots(1, 3, figsize=(TEXTWIDTH, 50 * MM))
    for ax, (test, sc, title, xl, ml) in zip(axes, panels):
        q = a[(a.test == test) & (a.scenario == sc)].groupby(["mechanism", "level"]).FCR.mean().reset_index()
        for (mech, lab, mk, ls), col in zip(SERIES, C):
            s = q[q.mechanism == mech].sort_values("level")
            ax.plot(s.level, s.FCR, ls, color=col, marker=mk, ms=3.2, mec="black", mew=0.4, label=lab)
        ax.axvline(ml, color=INK2, lw=0.6, ls=(0, (1, 1.5)))
        ax.set_title(title, fontsize=7.5, loc="left", color=INK)
        ax.set_xlabel(xl, fontsize=7.5)
        ax.set_ylim(bottom=0)
    axes[0].set_ylabel("FCR (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.08, 1, 1), w_pad=0.8)
    save(fig, "fig3_robustness")


# ------------------------------------------------------------------ tables
TABLES = []   # (number, label, caption, header, rows, colspec, notes)


def tex_escape(s: str) -> str:
    s = str(s)
    math = {"A(i,k)": "$A(i,k)$", "T_ik": "$T_{ik}$", "S_k": "$S_k$", "Q_k": "$Q_k$", "q_min": "$q_{\\min}$"}
    keep = {}
    for n, (a, b) in enumerate(math.items()):          # protect math before escaping underscores
        key = f"@@M{n}@@"
        s = s.replace(a, key)
        keep[key] = b
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        s = s.replace(a, b)
    s = (s.replace("\u2212", "$-$").replace("\u2264", r"$\leq$").replace("\u2265", r"$\geq$")
          .replace("\u2205", r"$\varnothing$").replace("\u03b8", r"$\theta$").replace("\u0394", r"$\Delta$")
          .replace("\u00b7", r"$\cdot$").replace("\u03c1", r"$\rho$").replace("\u2013", "--")
          .replace("\u2014", "---").replace("\u2020", r"$^\dagger$").replace("\u2021", r"$^\ddagger$")
          .replace("\u2248", r"$\approx$").replace("\u00b1", r"$\pm$").replace("\u2018", "`").replace("\u2019", "'")
          .replace(">", r"$>$"))
    for k, v in keep.items():
        s = s.replace(k, v)
    return s


RL = r">{\raggedright\arraybackslash}"


def add(num, label, caption, header, rows, colspec, notes=None, tex_header=None):
    TABLES.append((num, label, caption, header, rows, colspec, notes, tex_header))


def build_tables():
    # Table 1 related work (cells: verified sources only; '?' = full text not yet read)
    add("1", "tab:related", "Comparison with related work",
        ["Work", "Land records", "Multi-source", "Per-claim authority", "Learned trust",
         "Pre-commit conflict check", "Escalates", "Ground truth"],
        [["Thakur et al. [1]", "yes", "yes (nodes)", "no", "no", "no (deferred)", "manual", "no"],
         ["Soner et al. [5]†", "yes", "yes", "?", "?", "?", "?", "?"],
         ["Shuaib et al. [6]†", "yes", "?", "?", "?", "?", "?", "?"],
         ["Sahai, Pandey [7]†", "yes", "?", "?", "?", "?", "?", "?"],
         ["Khanna et al. [15]‡", "yes", "yes (6 roles)", "role-based", "n.s.", "n.s.", "n.s.", "n.s."],
         ["Chainlink [10]", "no", "yes (nodes)", "no", "reput.", "aggreg.", "no", "no"],
         ["Truth discovery [13]", "no", "yes", "no", "yes (unsup.)", "yes", "no", "—"],
         ["DecenTruth [14]‡", "no", "yes", "no", "yes (unsup.)", "yes", "n.s.", "sim."],
         ["This work", "synthetic", "yes (3)", "yes", "yes (labels)", "yes", "yes", "yes"]],
        "@{}" + RL + "p{2.0cm}*{7}{" + RL + "X}@{}",
        "† Full text not yet read; ? = not determined. ‡ Compared at abstract level only. "
        "n.s. = not stated in the abstract; unsup. = estimated without labels; reput. = reputation; aggreg. = aggregation of node reports; sim. = simulation; — = not applicable to a survey.")
    # Table 2 evidence normalisation
    add("S1", "tab:normalisation", "Illustrative meaning of each simulated report (+1 / −1; ∅ = no response)",
        ["Office", "own: seller is recorded holder", "deed: deed registered, matching", "restr: no pending proceeding"],
        [["Revenue", "Home. +1 record of rights names the seller; −1 names another", "+1 mutation file cites a matching deed; −1 no match",
          "+1 no pending revenue proceeding noted; −1 one is noted"],
         ["Sub-Registrar", "+1 earlier registered documents consistent with seller; −1 not", "Home. +1 deed registered, parties and parcel match; −1 not",
          "+1 no notice of a pending suit noted; −1 one is noted"],
         ["Judiciary", "+1 no court record contradicts the holding; −1 a decree names another holder", "+1 no case challenges the deed; −1 one does",
          "Home. +1 nothing pending in any forum covered; −1 a proceeding is pending"]],
        "@{}" + RL + "p{1.5cm}*{3}{" + RL + "X}@{}",
        "Simulated signals only; not claims about the records real offices hold or certify.")
    # Table 3 authority
    add("2", "tab:authority", "Claim-specific authority A(i,k) (modelling assumption)",
        ["Check", "Revenue", "Sub-Registrar", "Judiciary"],
        [[k] + [f"{DEFAULT_AUTHORITY[(i, k)]:.1f}" for i in ORACLES] for k in CHECKS], "@{}lccc@{}")
    # Table 4 worked example (computed from the frozen model)
    f = lambda d, w, t: w.truth[t]["restr"] == -1 and d["B1"].commit and not d["P"].commit
    w, t, dec, stores = trace("S5a", 1, f)
    pv = validate(w.reports[t], stores["P-V"], DEFAULT_AUTHORITY, MECHANISMS["P-V"], Params())
    sym = {1: "+1", -1: "−1", None: "∅"}
    rep = "; ".join(f"{i}: " + " ".join(sym[w.reports[t][(i, k)]] for k in CHECKS) for i in ORACLES)
    rows = []
    for m, lab in (("B1", "B1 Majority"), ("B2", "B2 Authority-only"), ("B3", "B3 Trust-only"),
                   ("P-V", "P−V Hybrid"), ("P", "P Hybrid + veto")):
        dd = dec[m]
        sup = ("2 of 3 clear" if m == "B1" else "veto first" if m == "P"
               else f"{(pv if m == 'P-V' else dd).detail['restr'][1]:.3f}")
        nice = {"restr:LOW_SUPPORT": "restr: low support", "RESTRICTION_REPORTED": "veto: proceeding reported"}
        rows.append([lab, sup, dd.label, ", ".join(nice.get(x, x) for x in dd.reasons) or "\u2014",
                     "false commit" if dd.commit else "escalated"])
    add("3", "tab:example", f"Worked example: request {t + 1} in S5a, seed 1, with a pending proceeding visible only to the Judiciary",
        ["Mechanism", "Support for\n‘clear’ on restr", "Decision", "Reason code", "Outcome"], rows,
        "@{}lcl" + RL + "Xl@{}",
        f"Truth: own pass, deed pass, restr pending (request invalid). Reports (own, deed, restr): {rep}. "
        "Trust under ideal feedback at that point: R, S and J on restr ≈ 1.00; θ = 0.65.")
    # Table 5 scenarios
    add("4", "tab:scenarios", "Scenarios; each changes one setting from S1",
        ["Scenario", "Change from S1", "RQ"],
        [["S1 Aligned", "None: authority matches each office’s most accurate check", "1"],
         ["S2 Degraded", "From request 251, Revenue accuracy 0.50 on all checks", "2"],
         ["S3 Misaligned", "On own, Revenue 0.75 and Sub-Registrar 0.95; authority unchanged", "2"],
         ["S4 Low availability", "Outage probability 0.25 per office per request", "3"],
         ["S5a Proceedings stress", "Revenue and Sub-Registrar always report ‘clear’ on restr", "4"],
         ["S5b Alt. authority", "As S5a, with A(R, restr) = A(S, restr) = 0.6", "4"]],
        "@{}l" + RL + "Xc@{}")
    # Table 6 mechanisms
    add("5", "tab:mechanisms", "Mechanisms compared",
        ["Mechanism", "Weight", "Pass rule per check", "Coverage gate", "Veto", "Learns"],
        [["B1 Majority", "1", "> half of responders", "≥ 2 of 3 responded", "no", "no"],
         ["B2 Authority-only", "A(i,k)", "S_k ≥ θ", "Q_k ≥ 0.5", "no", "no"],
         ["B3 Trust-only", "T_ik", "S_k ≥ θ", "Q_k ≥ 0.5", "no", "yes"],
         ["P−V Hybrid", "A(i,k)·T_ik", "S_k ≥ θ", "Q_k ≥ 0.5", "no", "yes"],
         ["P Hybrid + veto", "A(i,k)·T_ik", "S_k ≥ θ", "Q_k ≥ 0.5", "yes", "yes"]],
        "@{}ll" + RL + "X" + RL + "Xcc@{}")
    # Table 7 main results (computed); SDs in the note to fit the text width
    t1 = pd.read_csv(AOUT / "table1_full.csv", header=[0, 1], index_col=[0, 1])
    rows = []
    for m, lab in (("B1", "B1 Majority"), ("B2", "B2 Authority-only"), ("B3", "B3 Trust-only"), ("P-V", "Hybrid (P−V = P)")):
        r = [lab]
        for s in ("S1", "S2", "S3", "S4"):
            r += [f"{t1.loc[(m, s), ('FCR', 'mean')]:.2f}", f"{t1.loc[(m, s), ('VCC', 'mean')]:.1f}"]
        rows.append(r)
    fsd = t1.xs("std", axis=1, level=1)
    sel = fsd.loc[[i for i in fsd.index if i[0] in ("B1", "B2", "B3", "P-V") and i[1] in ("S1", "S2", "S3", "S4")]]
    add("6", "tab:main", "False-commit rate (FCR) and valid-commit coverage (VCC), %, mean over 100 seeds, ideal feedback",
        ["Mechanism", "S1 FCR", "S1 VCC", "S2 FCR", "S2 VCC", "S3 FCR", "S3 VCC", "S4 FCR", "S4 VCC"], rows,
        "@{}l*{8}{c}@{}",
        f"Between-seed SD: FCR {sel.FCR.min():.2f}–{sel.FCR.max():.2f}, VCC {sel.VCC.min():.1f}–{sel.VCC.max():.1f}. "
        "P and P−V made identical decisions in every run of S1–S4.",
        tex_header=[r" & \multicolumn{2}{c}{S1 Aligned} & \multicolumn{2}{c}{S2 Degraded} & "
                    r"\multicolumn{2}{c}{S3 Misaligned} & \multicolumn{2}{c}{S4 Low avail.} \\",
                    r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(l){8-9}",
                    r"Mechanism & FCR & VCC & FCR & VCC & FCR & VCC & FCR & VCC \\"])
    # Table 8 primary comparisons (computed)
    t2 = pd.read_csv(AOUT / "table2_primary.csv")
    names = {"H1a": "FCR: P−V − B1 (S1)", "H1b": "FCR: P−V − B2 (S1)",
             "H2a": "FCR: P−V − B2 (S2, 251–1000)", "H2b": "VCC: P−V − B3 (S2, 251–1000)",
             "H2c": "FCR: P−V − B2 (S3)", "H3": "VCC: P−V − B1 (S4)",
             "H4": "Breaches: P − P−V (S5b)", "H5": "FCR: P under F1 − F0 (S2)"}
    reading = {"lower": "lower", "lower, but smaller than Delta": "lower, < Δ",
               "no clear difference": "no clear diff.", "lower (descriptive)": "lower (descr.)",
               "identical in every seed": "identical", "opposite to hypothesis: lower": "not supported"}
    rows = []
    for _, r in t2.iterrows():
        thr = 0.5 if r.metric == "breaches_per_1000" else 0.25
        hw = f"{r.half_width:.2f}" + ("†" if r.half_width > thr else "")
        diff = "0" if r.identical else f"{fmt(r.mean_diff)} [{fmt(r.ci_low)}, {fmt(r.ci_high)}]"
        p = "—" if r.id == "H3" else ("<0.001" if r.p_holm < 0.001 else f"{r.p_holm:.2f}")
        rows.append([r.id, names[r.id], diff.replace("-", "−"), hw, p, reading.get(r.wording, r.wording)])
    add("7", "tab:primary", "Pre-specified paired comparisons (100 seeds; percentage points; breaches per 1,000 requests)",
        ["ID", "Metric: comparison (scenario)", "Difference [95% CI]", "Half-width", "Holm p", "Reading"], rows,
        "@{}l" + RL + "Xccc" + RL + "p{1.55cm}@{}",
        "† Above the precision target Δ/2 at the 100-seed cap. H3 is descriptive. H5 was one-sided (F1 higher).")
    # Table 9 coverage ablation (computed), one row per comparison and scenario
    a1 = pd.read_csv(AOUT / "A1_comparisons.csv")
    lab = {"P-V minus B1 under G0_none": "Hybrid − majority, no gate (G0)",
           "P-V minus B1 under G1_count2": "Hybrid − majority, common count gate (G1)",
           "P-V: weighted gate (G2) minus count gate (G1)": "Hybrid: weighted gate − count gate"}
    rows = []
    for comp in lab:
        for sc in ("S1", "S4"):
            r = [lab[comp], sc]
            for met in ("FCR", "VCC"):
                x = a1[(a1.comparison == comp) & (a1.scenario == sc) & (a1.metric == met)].iloc[0]
                r.append(f"{fmt(x.mean_diff)} [{fmt(x.ci_low)}, {fmt(x.ci_high)}]".replace("-", "−"))
            rows.append(r)
    add("S2", "tab:ablation", "Exploratory coverage-gate ablation A1 (paired 95% CIs, 100 seeds, percentage points)",
        ["Comparison", "Scenario", "FCR difference", "VCC difference"], rows, "@{}" + RL + "Xccc@{}")
    # Table 10 robustness summary (computed); two-line cells
    a2 = pd.read_csv(AOUT / "A2_conclusions.csv")
    tests = [("R1a_acc_other", "Off-home accuracy 0.60–0.85"), ("R1b_acc_home", "Home accuracy 0.85–0.95"),
             ("R2_shared_rho", "Shared R+S errors ρ = 0–0.20"), ("R3_label_noise_F0", "Label noise e = 0–0.10, F0"),
             ("R3_label_noise_F1", "Label noise e = 0–0.10, F1")]
    rows = []
    for tk, tl in tests:
        r = [tl]
        for ck in ("C1-S1", "C1-S2", "C2", "C3"):
            q = a2[(a2.test == tk) & (a2.conclusion == ck)]
            if q.empty:
                r.append("—")
                continue
            held = (q.verdict == "holds").sum()
            r.append(f"{held}/{len(q)}\n({q.fcr_diff.min():+.1f} to {q.fcr_diff.max():+.1f})".replace("-", "−"))
        rows.append(r)
    add("8", "tab:robustness", "Exploratory robustness study A2: levels at which each main conclusion holds, with the range of FCR differences in points",
        ["Factor varied", "C1 (S1)", "C1 (S2)", "C2", "C3"], rows, "@{}" + RL + "Xcccc@{}",
        "C1: hybrid below majority. C2: hybrid below authority-only after degradation (requests 251–"
        "1000). C3: trust-only below hybrid (S2). Holds: the 95% CI excludes 0 with the main-study sign. No conclusion reversed.")
    # Appendix tables
    add("S3", "tab:status", "Status of every result",
        ["Result", "Status"],
        [["Tables 6–7; Fig. 2; Fig. S1; q_min sweep", "Pre-specified (frozen protocol); five analysis choices in Table S4"],
         ["Veto bound (Sect. 3)", "Analytic, derived before the protocol freeze"],
         ["Counts per 1,000 requests; quoted trust values", "Descriptive re-expression of pre-specified runs"],
         ["Two-sided test for H5", "Exploratory, added after results were seen"],
         ["Table S2 (A1); Table 8 and Fig. 3 (A2)", "Exploratory; addenda committed before running"]],
        "@{}" + RL + "p{4.8cm}" + RL + "X@{}")
    add("S4", "tab:notes", "Analysis choices not covered by the frozen protocol (accepted by the supervisor)",
        ["#", "Situation", "Choice"],
        [["1", "H4 has zero variance", "Interval is the point 0; p = 1.0 in the Holm family"],
         ["2", "H1b has no direction", "Two-sided test inside the Holm family of seven"],
         ["3", "Significant and inside ±Δ (H1b)", "Worded ‘lower, but smaller than Δ’"],
         ["4", "CI opposite a one-sided hypothesis (H5)", "‘Not supported’; two-sided CI and exploratory test reported"],
         ["5", "H3 has no direction", "Worded from its unadjusted CI; labelled descriptive"]],
        "@{}c" + RL + "p{4.2cm}" + RL + "X@{}")


def tex_cell(c):
    parts = str(c).split("\n")
    if len(parts) == 1:
        return tex_escape(parts[0])
    return r"\makecell{" + r" \\ ".join(tex_escape(x) for x in parts) + "}"


def write_tex():
    for num, label, cap, header, rows, spec, notes, tex_header in TABLES:
        use_x = "X" in spec
        env = "tabularx" if use_x else "tabular"
        open_env = rf"\begin{{tabularx}}{{\textwidth}}{{{spec}}}" if use_x else rf"\begin{{tabular}}{{{spec}}}"
        body = [r"% Auto-generated by paper_assets/build_assets.py from saved results -- do not edit numbers by hand.",
                r"% Preamble needs: \usepackage{booktabs,array,tabularx,makecell}",
                r"\begin{table}[tb]", r"\centering", rf"\caption{{{tex_escape(cap)}}}\label{{{label}}}",
                r"\small" if num == "2" else r"\footnotesize", r"\setlength{\tabcolsep}{%s}" % ("2pt" if num == "1" else "3pt"),
                r"\renewcommand{\arraystretch}{1.1}", open_env, r"\toprule"]
        body += tex_header if tex_header else [" & ".join(tex_cell(h) for h in header) + r" \\"]
        body += [r"\midrule"]
        body += [" & ".join(tex_cell(c) for c in r) + r" \\" for r in rows]
        body += [r"\bottomrule", rf"\end{{{env}}}"]
        if notes:
            body += [r"\par\smallskip", rf"\parbox{{\textwidth}}{{\scriptsize {tex_escape(notes)}}}"]
        body += [r"\end{table}"]
        (TAB / f"tab{num.zfill(2)}_{label.split(':')[1]}.tex").write_text("\n".join(body) + "\n")


DOCX_WIDTHS_MM = {   # column widths per table, each row summing to <= 122 mm (LNCS text width)
    "1": [20] + [14.5] * 7, "S1": [17, 35, 35, 35], "2": [22, 24, 26, 24], "3": [25, 21, 16, 37, 21],
    "4": [32, 80, 10], "5": [26, 20, 25, 27, 11, 13], "6": [26] + [12] * 8, "7": [9, 45, 32, 13, 11, 12],
    "S2": [52, 14, 28, 28], "8": [32, 22.5, 22.5, 22.5, 22.5], "S3": [52, 70], "S4": [6, 46, 70]}
SUBS = {"S_k": ("S", "k"), "Q_k": ("Q", "k"), "T_ik": ("T", "ik"), "q_min": ("q", "min")}


def write_docx():
    import re
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(44)          # 210 - 2 x 44 = 122 mm text width
    sec.top_margin = sec.bottom_margin = Mm(52)          # 297 - 2 x 52 = 193 mm text height
    st_ = doc.styles["Normal"]
    st_.font.name, st_.font.size = "Times New Roman", Pt(9)
    st_.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    pat = re.compile("(" + "|".join(re.escape(k) for k in SUBS) + ")")

    def runs(par, text, size, bold=False):
        for piece in pat.split(str(text)):
            if piece in SUBS:
                base, sub = SUBS[piece]
                r = par.add_run(base); r.font.size, r.bold, r.italic = size, bold, True
                r = par.add_run(sub); r.font.size, r.bold = size, bold; r.font.subscript = True; r.italic = True
            elif piece:
                for k, line in enumerate(piece.split("\n")):
                    r = par.add_run(line); r.font.size, r.bold = size, bold
                    if k < len(piece.split("\n")) - 1:
                        r.add_break()

    def border(cell, sides):
        tcPr = cell._tc.get_or_add_tcPr()
        b = OxmlElement("w:tcBorders")
        for side, sz in sides.items():
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:val"), "single" if sz else "nil")
            e.set(qn("w:sz"), str(sz or 0))
            e.set(qn("w:color"), "000000")
            b.append(e)
        tcPr.append(b)

    def no_split(row):
        trPr = row._tr.get_or_add_trPr()
        e = OxmlElement("w:cantSplit"); trPr.append(e)

    def repeat_header(row):
        trPr = row._tr.get_or_add_trPr()
        e = OxmlElement("w:tblHeader"); trPr.append(e)

    intro = doc.add_paragraph()
    r = intro.add_run("Tables for the LNCS paper, Word version. Text width 122 mm; captions above tables, 9 pt; "
                      "table text 8 pt Times; horizontal rules only (top, below header, bottom). Copy each table "
                      "into the Springer LNCS Word template and apply its table-caption style. Numbers are "
                      "generated from the saved results; do not retype them.")
    r.italic, r.font.size = True, Pt(8)
    order = sorted(TABLES, key=lambda t: (t[0].startswith("S"), int(t[0].lstrip("S"))))
    for num, label, cap, header, rows, spec, notes, _th in order:
        if num == "S1":
            sp = doc.add_paragraph(); sr = sp.add_run("Supplementary tables (not counted in the 10 pages)"); sr.bold = True
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf = p.paragraph_format
        pf.space_before, pf.space_after, pf.keep_with_next = Pt(12), Pt(4), True
        b = p.add_run(f"Table {num}. "); b.bold, b.font.size = True, Pt(9)
        runs(p, cap, Pt(9))
        widths = DOCX_WIDTHS_MM[num]
        tb = doc.add_table(rows=len(rows) + 1, cols=len(header))
        tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        tb.autofit = False
        size = Pt(9) if num == "2" else (Pt(7.5) if num == "1" else Pt(8))
        for ri, data in enumerate([header] + rows):
            row = tb.rows[ri]
            no_split(row)
            if ri == 0:
                repeat_header(row)
            for ci, val in enumerate(data):
                cell = row.cells[ci]
                cell.width = Mm(widths[ci])
                par = cell.paragraphs[0]
                par.paragraph_format.space_before = par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.keep_with_next = ri < len(rows)
                runs(par, val, size, bold=(ri == 0))
                sides = {"left": 0, "right": 0, "top": 0, "bottom": 0}
                if ri == 0:
                    sides.update(top=8, bottom=4)
                if ri == len(rows):
                    sides.update(bottom=8)
                border(cell, sides)
        for ci, wmm in enumerate(widths):
            tb.columns[ci].width = Mm(wmm)
        if notes:
            n = doc.add_paragraph()
            n.paragraph_format.space_before = Pt(2)
            runs(n, notes, Pt(7))
    doc.save(TAB / "tables_for_word.docx")


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    fig1_system(); fig2_threshold(); fig3_feedback(); fig4_robustness()
    build_tables(); write_tex(); write_docx()
    print("figures:", sorted(p.name for p in FIG.iterdir()))
    print("tables:", sorted(p.name for p in TAB.iterdir()))


if __name__ == "__main__":
    main()
