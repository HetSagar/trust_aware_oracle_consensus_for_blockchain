"""Paired statistics for the pre-specified hypotheses (protocol, Statistical analysis).

    python analysis/stats.py results/final/runs.csv analysis/out

Writes table2_primary.csv and stopping_rule.json. Nothing here is hand-tuned:
comparisons, windows, Delta and wording rules are copied from the frozen protocol.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DELTA = {"FCR": 0.5, "VCC": 0.5, "breaches_per_1000": 1.0}   # P7
ALPHA = 0.05

# (id, rq, experiment-filter, window, mech A, mech B, metric, direction)
# direction: "lower" = A expected lower than B; "higher"; "two-sided" (H1b, in the Holm family);
# "none" (H3: descriptive trade-off, outside the Holm family, per protocol)
HYPOTHESES = [
    ("H1a", "RQ1", dict(experiment="core", scenario="S1"), "all", "P-V", "B1", "FCR", "lower"),
    ("H1b", "RQ1", dict(experiment="core", scenario="S1"), "all", "P-V", "B2", "FCR", "two-sided"),
    ("H2a", "RQ2", dict(experiment="core", scenario="S2"), "post250", "P-V", "B2", "FCR", "lower"),
    ("H2b", "RQ2", dict(experiment="core", scenario="S2"), "post250", "P-V", "B3", "VCC", "higher"),
    ("H2c", "RQ2", dict(experiment="core", scenario="S3"), "all", "P-V", "B2", "FCR", "lower"),
    ("H3", "RQ3", dict(experiment="core", scenario="S4"), "all", "P-V", "B1", "VCC", "none"),
    ("H4", "RQ4", dict(experiment="core", scenario="S5b"), "all", "P", "P-V", "breaches_per_1000", "lower"),
]


def add_rates(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["FCR"] = np.where(d.commits > 0, 100 * d.false_commits / d.commits.where(d.commits > 0), np.nan)
    d["FAR"] = 100 * d.false_commits / d.invalid
    d["VCC"] = 100 * d.valid_commits / d.valid
    d["ER"] = 100 * d.escalations / d.transfers
    d["breaches_per_1000"] = 1000 * d.breaches / d.transfers
    return d


def paired(a: pd.Series, b: pd.Series, direction: str) -> dict:
    diff = (a - b).dropna()
    n = len(diff)
    mean, sd = diff.mean(), diff.std(ddof=1)
    if sd == 0 or n < 2:
        # Identical in every seed: no sampling variation, interval is the point.
        return dict(n=n, mean_diff=mean, ci_low=mean, ci_high=mean, half_width=0.0, d_z=np.nan,
                    p_t=1.0 if mean == 0 else 0.0, p_wilcoxon=np.nan, identical=bool((diff == 0).all()))
    tcrit = stats.t.ppf(0.975, n - 1)
    hw = tcrit * sd / np.sqrt(n)
    alt = {"lower": "less", "higher": "greater"}.get(direction, "two-sided")
    p_t = stats.ttest_1samp(diff, 0.0, alternative=alt).pvalue
    try:
        p_w = stats.wilcoxon(diff, alternative=alt).pvalue
    except ValueError:
        p_w = np.nan
    return dict(n=n, mean_diff=mean, ci_low=mean - hw, ci_high=mean + hw, half_width=hw,
                d_z=mean / sd, p_t=p_t, p_wilcoxon=p_w, identical=False)


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for rank, (k, p) in enumerate(items):
        adj = min(1.0, (m - rank) * p)
        running = max(running, adj)
        out[k] = running
    return out


def wording(row: dict, metric: str) -> str:
    """Protocol wording rules, plus two cases the protocol table did not cover (logged)."""
    delta = DELTA[metric]
    lo, hi = row["ci_low"], row["ci_high"]
    if row.get("identical"):
        return "identical in every seed"
    side = "lower" if hi < 0 else "higher" if lo > 0 else None
    within = -delta < lo and hi < delta
    if row["direction"] == "none":                      # H3: descriptive, unadjusted CI
        return f"{side} (descriptive)" if side else "no clear difference (descriptive)"
    expected = row["direction"]
    if expected in ("lower", "higher") and side and side != expected:
        return f"opposite to hypothesis: {side}"         # one-sided test cannot detect this
    sig = row["p_holm"] < ALPHA and side is not None
    if sig and within:
        return f"{side}, but smaller than Delta"         # both protocol rows apply
    if sig:
        return side
    if within:
        return "no meaningful difference"
    return "no clear difference"


def main(runs_csv: str, out_dir: str, n_seeds: int | None = None, quiet: bool = False) -> pd.DataFrame:
    d = add_rates(pd.read_csv(runs_csv))
    if n_seeds is not None:
        d = d[d.seed <= n_seeds]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []

    def series(filt, window, mech, metric, extra=None):
        q = d[(d.window == window) & (d.mechanism == mech)]
        for k, v in {**filt, **(extra or {})}.items():
            q = q[q[k] == v]
        return q.set_index("seed")[metric].sort_index()

    for hid, rq, filt, window, a, b, metric, direction in HYPOTHESES:
        sa, sb = series(filt, window, a, metric), series(filt, window, b, metric)
        r = paired(sa, sb, direction)
        rows.append(dict(id=hid, rq=rq, scenario=filt["scenario"], window=window,
                         comparison=f"{a} - {b}", metric=metric, direction=direction,
                         mean_a=sa.mean(), mean_b=sb.mean(), **r))

    # H5: same mechanism (P), S2, F1 (a=0.05, d=50) minus F0, paired by seed
    base = dict(experiment="feedback", scenario="S2")
    f1 = series(base, "all", "P", "FCR", dict(regime="F1", audit=0.05, delay=50))
    f0 = series(base, "all", "P", "FCR", dict(regime="F0"))
    rows.append(dict(id="H5", rq="RQ5", scenario="S2", window="all",
                     comparison="P under F1(a=0.05,d=50) - P under F0", metric="FCR",
                     direction="higher", mean_a=f1.mean(), mean_b=f0.mean(),
                     **paired(f1, f0, "higher")))

    family = {r["id"]: r["p_t"] for r in rows if r["direction"] != "none"}   # seven: all but H3
    adj = holm(family)
    for r in rows:
        r["p_holm"] = adj.get(r["id"], np.nan)
        r["wording"] = wording(r, r["metric"])
        r["precision_ok"] = r["half_width"] <= DELTA[r["metric"]] / 2
    t2 = pd.DataFrame(rows)
    t2.to_csv(out / "table2_primary.csv", index=False)

    stop = {"seeds": int(t2.n.max()),
            "all_precise": bool(t2.precision_ok.all()),
            "too_wide": t2.loc[~t2.precision_ok, ["id", "half_width"]].to_dict("records")}
    (out / "stopping_rule.json").write_text(json.dumps(stop, indent=2))

    if quiet:
        return t2
    pd.set_option("display.width", 200)
    print(t2[["id", "comparison", "metric", "mean_a", "mean_b", "mean_diff", "ci_low", "ci_high",
              "half_width", "d_z", "p_t", "p_holm", "p_wilcoxon", "wording"]].round(3).to_string(index=False))
    print(json.dumps(stop, indent=2))
    return t2


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
