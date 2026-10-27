"""Addendum A1 analysis (exploratory). See docs/addendum_A1_coverage.md.

    python analysis/addendum_A1.py results/final analysis/out
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st


def rates(d):
    d = d.copy()
    d["FCR"] = 100 * d.false_commits / d.commits.where(d.commits > 0)
    d["VCC"] = 100 * d.valid_commits / d.valid
    d["ER"] = 100 * d.escalations / d.transfers
    return d


def paired(a, b):
    diff = (a - b).dropna()
    n, m, s = len(diff), diff.mean(), diff.std(ddof=1)
    hw = st.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    return dict(n=n, mean_diff=m, ci_low=m - hw, ci_high=m + hw)


def main(res_dir, out_dir):
    res, out = Path(res_dir), Path(out_dir)
    a = rates(pd.read_csv(res / "addendum_A1_runs.csv"))

    # Regression check: G2 reproduces the main study's counts exactly
    main_runs = pd.read_csv(res / "runs.csv")
    m = main_runs[(main_runs.experiment == "core") & (main_runs.window == "all")
                  & main_runs.scenario.isin(["S1", "S2", "S3", "S4"])]
    keys = ["scenario", "seed", "mechanism"]
    cols = ["commits", "false_commits", "valid_commits", "escalations"]
    j = a[a.gate == "G2_main"].merge(m, on=keys, suffixes=("", "_main"))
    ok = all((j[c] == j[c + "_main"]).all() for c in cols) and len(j) == 2000
    print("G2 reproduces main study exactly:", ok)
    assert ok

    summ = a.groupby(["gate", "scenario", "mechanism"])[["FCR", "VCC", "ER"]].mean().round(2)
    summ.to_csv(out / "A1_summary.csv")
    print(summ.unstack(0).to_string())

    s = lambda g, sc, mech, met: a[(a.gate == g) & (a.scenario == sc) & (a.mechanism == mech)].set_index("seed")[met].sort_index()
    rows = []
    for sc in ("S1", "S4"):
        for met in ("FCR", "VCC"):
            for g in ("G0_none", "G1_count2"):
                rows.append(dict(comparison=f"P-V minus B1 under {g}", scenario=sc, metric=met,
                                 **paired(s(g, sc, "P-V", met), s(g, sc, "B1", met))))
            rows.append(dict(comparison="P-V: weighted gate (G2) minus count gate (G1)", scenario=sc,
                             metric=met, **paired(s("G2_main", sc, "P-V", met), s("G1_count2", sc, "P-V", met))))
    comp = pd.DataFrame(rows)
    comp.to_csv(out / "A1_comparisons.csv", index=False)
    print(comp.round(3).to_string(index=False))

    diag = (a[(a.gate == "G2_main") & a.mechanism.isin(["B2", "B3", "P-V", "P"])]
            .groupby(["scenario", "mechanism"]).commits_with_single_responder_check.mean().round(2).unstack())
    diag.to_csv(out / "A1_single_responder_commits.csv")
    print("Mean commits per run with a single-responder check (G2):\n", diag.to_string())


if __name__ == "__main__":
    main(*sys.argv[1:3])
