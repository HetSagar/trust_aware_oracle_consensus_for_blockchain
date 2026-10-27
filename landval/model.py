"""Core definitions and the pure validation rule (Phase 2 spec, Algorithm 1 bundle).

This module has no randomness and no simulation state. Given one transfer's
reports, the current trust scores and a mechanism, it returns a decision.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

ORACLES: Tuple[str, ...] = ("R", "S", "J")          # Revenue, Sub-Registrar, Judiciary
CHECKS: Tuple[str, ...] = ("own", "deed", "restr")  # ownership, deed, restriction
HOME = {"R": "own", "S": "deed", "J": "restr"}

PASS, FAIL = 1, -1          # a report or truth: +1 pass/clear, -1 fail/restricted
EPS = 1e-9                  # tolerance so a value of exactly theta is not lost to rounding

Key = Tuple[str, str]       # (oracle, check)
Reports = Dict[Key, Optional[int]]   # None = no response

# Draft v1 authority matrix A(i, k) [PARAM]
DEFAULT_AUTHORITY: Dict[Key, float] = {
    ("R", "own"): 1.0, ("S", "own"): 0.6, ("J", "own"): 0.4,
    ("R", "deed"): 0.6, ("S", "deed"): 1.0, ("J", "deed"): 0.4,
    ("R", "restr"): 0.2, ("S", "restr"): 0.2, ("J", "restr"): 1.0,
}

# S5b alternative matrix: R and S carry real weight on restrictions [PARAM, P5]
ALT_AUTHORITY: Dict[Key, float] = {**DEFAULT_AUTHORITY, ("R", "restr"): 0.6, ("S", "restr"): 0.6}


@dataclass(frozen=True)
class Params:
    theta: float = 0.65          # commit threshold
    q_min: float = 0.5           # coverage floor
    t_min: float = 0.6           # trust guard for the restriction veto
    alpha: float = 0.1           # trust learning rate
    t0: float = 0.5              # starting trust
    trust_transform: Optional[str] = None   # None or "above_chance" (D08, sensitivity only)
    min_labels: int = 0          # labels a score needs before the transform applies


@dataclass(frozen=True)
class Mechanism:
    name: str
    weight: str        # "equal" | "authority" | "trust" | "hybrid"
    rule: str          # "majority" (>50% of responders) | "threshold" (S_k >= theta)
    coverage: str      # "count2" (>=2 of 3 responded) | "weighted" (Q_k >= q_min) | "none" (A1)
    veto: bool         # restriction veto (P only)
    learns: bool       # trust updated from labels


MECHANISMS: Dict[str, Mechanism] = {
    "B1": Mechanism("B1", "equal", "majority", "count2", veto=False, learns=False),
    "B2": Mechanism("B2", "authority", "threshold", "weighted", veto=False, learns=False),
    "B3": Mechanism("B3", "trust", "threshold", "weighted", veto=False, learns=True),
    "P-V": Mechanism("P-V", "hybrid", "threshold", "weighted", veto=False, learns=True),
    "P": Mechanism("P", "hybrid", "threshold", "weighted", veto=True, learns=True),
}
# Equal weights compared at each theta in the theta sweep (protocol, Sensitivity sweeps)
EQUAL_AT_THETA = Mechanism("EQ", "equal", "threshold", "weighted", veto=False, learns=False)


class TrustStore:
    """One trust score per oracle per check (D15), plus availability counters (D10)."""

    def __init__(self, t0: float = 0.5):
        self.T: Dict[Key, float] = {(i, k): t0 for i in ORACLES for k in CHECKS}
        self.n_labels: Dict[Key, int] = {(i, k): 0 for i in ORACLES for k in CHECKS}
        self.requests: Dict[str, int] = {i: 0 for i in ORACLES}
        self.responses: Dict[str, int] = {i: 0 for i in ORACLES}

    def raw(self, i: str, k: str) -> float:
        return self.T[(i, k)]

    def effective(self, i: str, k: str, p: Params) -> float:
        """Trust used in weights. The above-chance transform is a sensitivity variant only."""
        t = self.T[(i, k)]
        if p.trust_transform == "above_chance" and self.n_labels[(i, k)] >= p.min_labels:
            return max(0.0, 2.0 * t - 1.0)
        return t

    def update(self, reports: Reports, truth: Dict[str, int], alpha: float) -> None:
        """EMA update from a VERIFIED label. Silent oracles are left unchanged."""
        for i in ORACLES:
            for k in CHECKS:
                r = reports.get((i, k))
                if r is None:
                    continue
                correct = 1.0 if r == truth[k] else 0.0
                self.T[(i, k)] = (1.0 - alpha) * self.T[(i, k)] + alpha * correct
                self.n_labels[(i, k)] += 1

    def record_availability(self, reports: Reports) -> None:
        for i in ORACLES:
            self.requests[i] += 1
            if any(reports.get((i, k)) is not None for k in CHECKS):
                self.responses[i] += 1


@dataclass
class Decision:
    commit: bool
    reasons: Tuple[str, ...]
    detail: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # k -> (Q_k, S_k)

    @property
    def label(self) -> str:
        return "COMMIT" if self.commit else "ESCALATE"


def _weight(mech: Mechanism, i: str, k: str, authority: Dict[Key, float],
            store: TrustStore, p: Params) -> float:
    if mech.weight == "equal":
        return 1.0
    if mech.weight == "authority":
        return authority[(i, k)]
    t = store.effective(i, k, p)
    if mech.weight == "trust":
        return t
    if mech.weight == "hybrid":
        return authority[(i, k)] * t
    raise ValueError(f"unknown weight mode {mech.weight}")


def validate(reports: Reports, store: TrustStore, authority: Dict[Key, float],
             mech: Mechanism, p: Params) -> Decision:
    """Algorithm 1 (bundle). Commits only if all three checks pass; never rejects."""
    # 1. No evidence at all
    if all(reports.get((i, k)) is None for i in ORACLES for k in CHECKS):
        return Decision(False, ("NO_EVIDENCE",))

    # 2. Restriction veto (P only): a trusted report of a pending proceeding
    if (mech.veto and reports.get(("J", "restr")) == FAIL
            and store.raw("J", "restr") >= p.t_min - EPS):
        return Decision(False, ("RESTRICTION_REPORTED",))

    # 3. Every check, no early stop
    reasons = []
    detail: Dict[str, Tuple[float, float]] = {}
    for k in CHECKS:
        responders = [i for i in ORACLES if reports.get((i, k)) is not None]

        if mech.rule == "majority":
            if not responders:
                reasons.append(f"{k}:NO_EVIDENCE")
                continue
            if mech.coverage == "count2" and len(responders) < 2:
                reasons.append(f"{k}:LOW_COVERAGE")
                continue
            n_pass = sum(1 for i in responders if reports[(i, k)] == PASS)
            if not 2 * n_pass > len(responders):          # strict majority; ties fail
                reasons.append(f"{k}:NO_MAJORITY")
            continue

        w = {i: _weight(mech, i, k, authority, store, p) for i in ORACLES}
        total = sum(w[i] for i in responders)
        if not responders or total <= 0.0:
            reasons.append(f"{k}:NO_EVIDENCE")
            continue
        q = total / sum(w.values())
        s = sum(w[i] for i in responders if reports[(i, k)] == PASS) / total
        detail[k] = (q, s)
        if mech.coverage == "count2":
            low_cov = len(responders) < 2
        elif mech.coverage == "none":            # addendum A1 only
            low_cov = False
        elif mech.coverage == "weighted":
            low_cov = q < p.q_min - EPS
        else:
            raise ValueError(f"unknown coverage mode {mech.coverage}")
        if low_cov:
            reasons.append(f"{k}:LOW_COVERAGE")
            continue
        if s < p.theta - EPS:
            reasons.append(f"{k}:LOW_SUPPORT")

    return Decision(not reasons, tuple(reasons), detail)
