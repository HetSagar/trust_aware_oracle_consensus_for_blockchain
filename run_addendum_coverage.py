"""Addendum A1 (exploratory): coverage-gate ablation. See docs/addendum_A1_coverage.md.

    python run_addendum_coverage.py

Writes results/final/addendum_A1_runs.csv. Uses the frozen config's parameters and seeds 1-100.
"""
from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

from landval.metrics import counts
from landval.model import CHECKS, MECHANISMS, ORACLES, Params
from landval.sim import Feedback, run
from landval.world import SCENARIOS, make_world

ROOT = Path(__file__).parent
GATES = {
    "G0_none": {m: "none" for m in MECHANISMS},
    "G1_count2": {m: "count2" for m in MECHANISMS},
    "G2_main": {m: MECHANISMS[m].coverage for m in MECHANISMS},
}
COLS = ["transfers", "valid", "invalid", "commits", "false_commits", "valid_commits", "escalations"]


def main():
    cfg = json.loads((ROOT / "config" / "frozen.json").read_text())
    assert cfg["frozen"], "A1 runs only under the frozen config"
    p = Params(**cfg["params"])
    rows = []
    for seed in range(1, 101):
        for sc in ("S1", "S2", "S3", "S4"):
            w = make_world(SCENARIOS[sc], seed)
            # transfers where at least one check had exactly one responder
            single = [any(sum(w.reports[t][(i, k)] is not None for i in ORACLES) == 1 for k in CHECKS)
                      for t in range(w.scenario.n)]
            for gname, modes in GATES.items():
                for m, mech in MECHANISMS.items():
                    recs = run(w, replace(mech, coverage=modes[m]), p, Feedback("F0"))
                    c = counts(recs)
                    rows.append({"gate": gname, "scenario": sc, "seed": seed, "mechanism": m,
                                 **{k: c[k] for k in COLS},
                                 "commits_with_single_responder_check":
                                     sum(1 for r in recs if r.commit and single[r.t])})
        if seed % 20 == 0:
            print(f"seed {seed} done", flush=True)
    out = ROOT / "results" / "final" / "addendum_A1_runs.csv"
    with open(out, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
