"""Synthetic worlds: hidden truths, oracle reports, outages and audit draws.

Each seed produces four independent random streams (protocol, Seeds and pairing):
truths, reports, outages and audit draws. All random numbers are drawn for every
transfer up front, so changing one parameter never shifts any other draw.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .model import (CHECKS, DEFAULT_AUTHORITY, FAIL, HOME, ORACLES, PASS, Key, Reports)


@dataclass(frozen=True)
class Scenario:
    name: str
    n: int = 1000
    q: Tuple[float, float, float] = (0.12, 0.12, 0.08)     # failure rate per check (D17)
    acc_home: float = 0.95
    acc_other: float = 0.75
    outage: float = 0.03
    degrade_oracle: Optional[str] = None                   # S2
    degrade_from: Optional[int] = None                     # 0-based index of first degraded transfer
    degrade_acc: float = 0.5
    acc_override: Tuple[Tuple[Key, float], ...] = ()       # S3
    blind_restr: Tuple[str, ...] = ()                      # S5: oracles that always report "clear"
    authority: Tuple[Tuple[Key, float], ...] = tuple(DEFAULT_AUTHORITY.items())
    shared_rho: float = 0.0                                # A2/R2: R and S wrong together

    def authority_dict(self) -> Dict[Key, float]:
        return dict(self.authority)

    def accuracy(self, i: str, k: str, t: int) -> float:
        if (self.degrade_oracle == i and self.degrade_from is not None
                and t >= self.degrade_from):
            return self.degrade_acc
        for key, acc in self.acc_override:
            if key == (i, k):
                return acc
        return self.acc_home if HOME[i] == k else self.acc_other


@dataclass
class World:
    scenario: Scenario
    seed: int
    truth: List[Dict[str, int]]          # per transfer: check -> +1 / -1
    reports: List[Reports]               # per transfer: (oracle, check) -> +1 / -1 / None
    audit_u: np.ndarray                  # per transfer: uniform draw for the audit sample
    label_u: np.ndarray = None           # per transfer x check: uniform draw for label noise (A2/R3)

    def valid(self, t: int) -> bool:
        return all(v == PASS for v in self.truth[t].values())


def make_world(sc: Scenario, seed: int) -> World:
    ss = np.random.SeedSequence(seed)
    # Children are indexed, so the first four streams are identical to the main study's
    # spawn(4); streams 5 and 6 are new for addendum A2.
    s_truth, s_report, s_outage, s_audit, s_shared, s_label = ss.spawn(6)
    u_truth = np.random.default_rng(s_truth).random((sc.n, len(CHECKS)))
    u_report = np.random.default_rng(s_report).random((sc.n, len(ORACLES), len(CHECKS)))
    u_outage = np.random.default_rng(s_outage).random((sc.n, len(ORACLES)))
    u_audit = np.random.default_rng(s_audit).random(sc.n)
    u_shared = np.random.default_rng(s_shared).random((sc.n, len(CHECKS)))
    u_label = np.random.default_rng(s_label).random((sc.n, len(CHECKS)))

    truth, reports = [], []
    for t in range(sc.n):
        g = {k: (FAIL if u_truth[t, ki] < sc.q[ki] else PASS) for ki, k in enumerate(CHECKS)}
        truth.append(g)
        r: Reports = {}
        for ii, i in enumerate(ORACLES):
            down = u_outage[t, ii] < sc.outage          # per oracle per transfer
            for ki, k in enumerate(CHECKS):
                if down:
                    r[(i, k)] = None
                elif k == "restr" and i in sc.blind_restr:
                    r[(i, k)] = PASS                    # cannot see pending proceedings
                elif i in ("R", "S") and u_shared[t, ki] < sc.shared_rho:
                    r[(i, k)] = -g[k]                   # A2/R2: one stale record, copied by both
                else:
                    correct = u_report[t, ii, ki] < sc.accuracy(i, k, t)
                    r[(i, k)] = g[k] if correct else -g[k]
        reports.append(r)
    return World(sc, seed, truth, reports, u_audit, u_label)


# ---- Scenario registry (protocol, Scenarios; values approved as P3-P5) ----
SCENARIOS: Dict[str, Scenario] = {
    "S1": Scenario("S1"),
    "S2": Scenario("S2", degrade_oracle="R", degrade_from=250, degrade_acc=0.50),
    "S3": Scenario("S3", acc_override=((("R", "own"), 0.75), (("S", "own"), 0.95))),
    "S4": Scenario("S4", outage=0.25),
    "S5a": Scenario("S5a", blind_restr=("R", "S")),
    "S5b": Scenario("S5b", blind_restr=("R", "S"), authority=tuple({
        **DEFAULT_AUTHORITY, ("R", "restr"): 0.6, ("S", "restr"): 0.6}.items())),
}
