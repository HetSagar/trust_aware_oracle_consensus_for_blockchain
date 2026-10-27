"""Run the core scenarios and sweeps defined in config/frozen.json.

    python run_experiments.py --seeds debug           # Phase 4: allowed any time
    python run_experiments.py --seeds final           # Phase 5: refused unless frozen=true

Writes results/<seedset>/runs.csv (counts per run), transfers_core.csv and trust_core.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from landval.metrics import counts
from landval.model import EQUAL_AT_THETA, MECHANISMS, Params
from landval.sim import Feedback, run
from landval.world import SCENARIOS, make_world

ROOT = Path(__file__).parent
COUNT_COLS = ["transfers", "valid", "invalid", "restricted", "commits", "false_commits",
              "valid_commits", "breaches", "escalations", "multi_reason"]


def mech(name):
    return EQUAL_AT_THETA if name == "EQ" else MECHANISMS[name]


def seed_list(cfg, which, n_final):
    if which == "debug":
        return cfg["seeds"]["debug"]
    lo, hi = cfg["seeds"]["final"]
    return list(range(lo, max(hi, n_final) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", choices=["debug", "final"], required=True)
    ap.add_argument("--n-final", type=int, default=30, help="raise only via the stopping rule")
    ap.add_argument("--config", default=str(ROOT / "config" / "frozen.json"))
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    if args.seeds == "final" and not cfg.get("frozen"):
        sys.exit("Refusing to run final seeds: config is not frozen (Protocol, Run procedure step 3).")
    if args.n_final > cfg["seeds"]["extra_max"]:
        sys.exit("n-final exceeds the protocol maximum.")

    base = Params(**cfg["params"])
    post = cfg["windows"]["S2_post"]
    seeds = seed_list(cfg, args.seeds, args.n_final)
    out_dir = ROOT / "results" / args.seeds
    out_dir.mkdir(parents=True, exist_ok=True)

    run_rows, transfer_rows, trust_rows = [], [], []

    def record(exp, sc_name, seed, m, p, fb, recs, keep_transfers=False):
        windows = [("all", 0)] + ([("post250", post)] if sc_name == "S2" else [])
        for wname, start in windows:
            c = counts(recs, start=start)
            run_rows.append({
                "experiment": exp, "scenario": sc_name, "seed": seed, "mechanism": m,
                "theta": p.theta, "q_min": p.q_min, "alpha": p.alpha,
                "regime": fb.regime, "audit": fb.audit, "delay": fb.delay, "window": wname,
                **{k: c[k] for k in COUNT_COLS}, "reasons": json.dumps(c["reasons"]),
            })
        if keep_transfers:
            for r in recs:
                transfer_rows.append({"scenario": sc_name, "seed": seed, "mechanism": m,
                                      "t": r.t + 1, "decision": "COMMIT" if r.commit else "ESCALATE",
                                      "reasons": "|".join(r.reasons), "valid": int(r.valid),
                                      "restricted": int(r.restricted), "labelled": int(r.labelled)})
                if r.trust is not None:
                    trust_rows.append({"scenario": sc_name, "seed": seed, "mechanism": m,
                                       "t": r.t + 1, **r.trust})

    for seed in seeds:
        # Core
        for sc_name in cfg["core"]["scenarios"]:
            w = make_world(SCENARIOS[sc_name], seed)
            for m in cfg["core"]["mechanisms"]:
                fb = Feedback("F0")
                recs = run(w, mech(m), base, fb, keep_trust=True)
                record("core", sc_name, seed, m, base, fb, recs, keep_transfers=True)
        # Theta sweep
        sw = cfg["sweeps"]["theta"]
        w = make_world(SCENARIOS[sw["scenario"]], seed)
        for th in sw["values"]:
            p = replace(base, theta=th)
            for m in sw["mechanisms"]:
                record("theta", sw["scenario"], seed, m, p, Feedback("F0"), run(w, mech(m), p))
        # q_min sweep
        sw = cfg["sweeps"]["q_min"]
        w = make_world(SCENARIOS[sw["scenario"]], seed)
        for qm in sw["values"]:
            p = replace(base, q_min=qm)
            for m in sw["mechanisms"]:
                record("q_min", sw["scenario"], seed, m, p, Feedback("F0"), run(w, mech(m), p))
        # Feedback sweep (F0 reference + F1 grid)
        sw = cfg["sweeps"]["feedback"]
        w = make_world(SCENARIOS[sw["scenario"]], seed)
        for m in sw["mechanisms"]:
            record("feedback", sw["scenario"], seed, m, base, Feedback("F0"),
                   run(w, mech(m), base, Feedback("F0")))
            for a in sw["audit"]:
                for d in sw["delay"]:
                    fb = Feedback("F1", audit=a, delay=d)
                    record("feedback", sw["scenario"], seed, m, base, fb, run(w, mech(m), base, fb))
        # Alpha sweep
        sw = cfg["sweeps"]["alpha"]
        w = make_world(SCENARIOS[sw["scenario"]], seed)
        for al in sw["values"]:
            p = replace(base, alpha=al)
            for m in sw["mechanisms"]:
                record("alpha", sw["scenario"], seed, m, p, Feedback("F0"), run(w, mech(m), p))
        print(f"seed {seed} done", flush=True)

    for name, rows in (("runs.csv", run_rows), ("transfers_core.csv", transfer_rows),
                       ("trust_core.csv", trust_rows)):
        with open(out_dir / name, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            wr.writeheader()
            wr.writerows(rows)

    log = (f"\n## {datetime.now(timezone.utc).isoformat(timespec='seconds')} — {args.seeds} seeds\n"
           f"- seeds: {seeds[0]}–{seeds[-1]} ({len(seeds)})\n- config frozen: {cfg.get('frozen')}\n"
           f"- python {platform.python_version()}, numpy {np.__version__}\n"
           f"- command: python run_experiments.py --seeds {args.seeds}"
           f"{' --n-final ' + str(args.n_final) if args.seeds == 'final' else ''}\n"
           f"- rows: runs {len(run_rows)}, transfers {len(transfer_rows)}, trust {len(trust_rows)}\n")
    with open(ROOT / "RUN_LOG.md", "a") as f:
        f.write(log)
    print(log)


if __name__ == "__main__":
    main()
