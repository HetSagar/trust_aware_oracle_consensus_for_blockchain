"""Addendum A2 analysis (exploratory). See docs/addendum_A2_robustness.md.

    python analysis/addendum_A2.py results/final analysis/out
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

# (id, label, scenario, window, mech A, mech B, main-study sign of A - B)
CONCLUSIONS = [
    ("C1-S1", "Hybrid beats majority (S1)", "S1", "all", "P-V", "B1", -1),
    ("C1-S2", "Hybrid beats majority (S2)", "S2", "all", "P-V", "B1", -1),
    ("C2", "Hybrid beats authority-only after degradation", "S2", "post250", "P-V", "B2", -1),
    ("C3", "Trust-only has lower FCR than hybrid (S2)", "S2", "all", "B3", "P-V", -1),
]
MAIN_LEVEL = {"R1a_acc_other": 0.75, "R1b_acc_home": 0.95, "R2_shared_rho": 0.0,
              "R3_label_noise_F0": 0.0, "R3_label_noise_F1": 0.0}


def rates(d):
    d = d.copy()
    d["FCR"] = 100 * d.false_commits / d.commits.where(d.commits > 0)
    d["VCC"] = 100 * d.valid_commits / d.valid
    d["ER"] = 100 * d.escalations / d.transfers
    return d


def ci(diff):
    diff = diff.dropna()
    n, m, s = len(diff), diff.mean(), diff.std(ddof=1)
    hw = st.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    return m, m - hw, m + hw


def verdict(lo, hi, sign):
    if (sign < 0 and hi < 0) or (sign > 0 and lo > 0):
        return "holds"
    if (sign < 0 and lo > 0) or (sign > 0 and hi < 0):
        return "reverses"
    return "weakens"


def main(res_dir, out_dir):
    res, out = Path(res_dir), Path(out_dir)
    a = rates(pd.read_csv(res / "addendum_A2_runs.csv"))

    # Check: main-study levels reproduce the main results (S1/S2 core, F0)
    main = rates(pd.read_csv(res / "runs.csv"))
    core = main[main.experiment == "core"]
    for test, lvl in MAIN_LEVEL.items():
        if test == "R3_label_noise_F1":
            continue
        q = a[(a.test == test) & (a.level == lvl)]
        j = q.merge(core, on=["scenario", "seed", "mechanism", "window"], suffixes=("", "_m"))
        assert len(j) == len(q) and (j.false_commits == j.false_commits_m).all() \
            and (j.valid_commits == j.valid_commits_m).all(), test
    fb = main[(main.experiment == "feedback") & (main.regime == "F1") & (main.audit == 0.05) & (main.delay == 50)]
    q = a[(a.test == "R3_label_noise_F1") & (a.level == 0.0) & a.mechanism.isin(["B3", "P-V", "P"])]
    j = q.merge(fb, on=["scenario", "seed", "mechanism", "window"], suffixes=("", "_m"))
    assert len(j) == len(q) and (j.false_commits == j.false_commits_m).all(), "R3 F1"
    print("Main-study levels reproduce the main results exactly: True")

    rows = []
    for test in a.test.unique():
        for lvl in sorted(a[a.test == test].level.unique()):
            for cid, label, sc, win, ma, mb, sign in CONCLUSIONS:
                q = a[(a.test == test) & (a.level == lvl) & (a.scenario == sc) & (a.window == win)]
                if q.empty:
                    continue
                sa = q[q.mechanism == ma].set_index("seed").sort_index()
                sb = q[q.mechanism == mb].set_index("seed").sort_index()
                m, lo, hi = ci(sa.FCR - sb.FCR)
                vm, vlo, vhi = ci(sa.VCC - sb.VCC)
                rows.append(dict(test=test, level=lvl, main_level=lvl == MAIN_LEVEL[test], conclusion=cid,
                                 label=label, fcr_a=sa.FCR.mean(), fcr_b=sb.FCR.mean(),
                                 fcr_diff=m, fcr_lo=lo, fcr_hi=hi, verdict=verdict(lo, hi, sign),
                                 vcc_diff=vm, vcc_lo=vlo, vcc_hi=vhi))
    t = pd.DataFrame(rows)
    t.to_csv(out / "A2_conclusions.csv", index=False)
    means = a[a.window == "all"].groupby(["test", "level", "scenario", "mechanism"])[["FCR", "VCC", "ER"]].mean()
    means.round(2).to_csv(out / "A2_means.csv")
    pd.set_option("display.width", 220)
    print(t[["test", "level", "conclusion", "fcr_a", "fcr_b", "fcr_diff", "fcr_lo", "fcr_hi", "verdict",
             "vcc_diff"]].round(2).to_string(index=False))
    print("\nVerdict counts:\n", t.groupby(["conclusion", "verdict"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main(*sys.argv[1:3])
