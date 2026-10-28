"""Addendum A2 (exploratory): robustness study. See docs/addendum_A2_robustness.md.

    python run_addendum_robustness.py

Writes results/final/addendum_A2_runs.csv. Frozen parameters, seeds 1-100.
"""
from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

from landval.metrics import counts
from landval.model import MECHANISMS, Params
from landval.sim import Feedback, run
from landval.world import SCENARIOS, make_world

ROOT = Path(__file__).parent
COLS = ["transfers", "valid", "invalid", "commits", "false_commits", "valid_commits", "escalations"]


def settings():
    for sc in ("S1", "S2"):
        for v in (0.60, 0.70, 0.75, 0.85):
            yield "R1a_acc_other", v, replace(SCENARIOS[sc], acc_other=v), Feedback("F0")
        for v in (0.85, 0.90, 0.95):
            yield "R1b_acc_home", v, replace(SCENARIOS[sc], acc_home=v), Feedback("F0")
        for v in (0.0, 0.05, 0.10, 0.20):
            yield "R2_shared_rho", v, replace(SCENARIOS[sc], shared_rho=v), Feedback("F0")
    for v in (0.0, 0.02, 0.05, 0.10):
        yield "R3_label_noise_F0", v, SCENARIOS["S2"], Feedback("F0", label_noise=v)
        yield "R3_label_noise_F1", v, SCENARIOS["S2"], Feedback("F1", audit=0.05, delay=50, label_noise=v)


def main():
    cfg = json.loads((ROOT / "config" / "frozen.json").read_text())
    assert cfg["frozen"], "A2 runs only under the frozen config"
    p = Params(**cfg["params"])
    rows = []
    for seed in range(1, 101):
        for test, level, sc, fb in settings():
            w = make_world(sc, seed)
            for m, mech in MECHANISMS.items():
                recs = run(w, mech, p, fb)
                for wname, start in [("all", 0)] + ([("post250", 250)] if sc.name == "S2" else []):
                    c = counts(recs, start=start)
                    rows.append({"test": test, "level": level, "scenario": sc.name, "seed": seed,
                                 "mechanism": m, "window": wname, **{k: c[k] for k in COLS}})
        if seed % 20 == 0:
            print(f"seed {seed} done", flush=True)
    out = ROOT / "results" / "final" / "addendum_A2_runs.csv"
    with open(out, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
