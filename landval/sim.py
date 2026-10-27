"""Run one mechanism over one world, with ideal (F0) or realistic (F1) feedback."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

from .model import CHECKS, FAIL, ORACLES, Mechanism, Params, TrustStore, validate
from .world import World


@dataclass(frozen=True)
class Feedback:
    regime: str = "F0"     # "F0": every transfer labelled; "F1": escalations + audit sample
    audit: float = 0.0     # audit rate a for committed transfers (F1)
    delay: int = 0         # label delay d in transfers

    def __post_init__(self):
        if self.regime not in ("F0", "F1"):
            raise ValueError("regime must be F0 or F1")
        if self.regime == "F0" and self.delay != 0:
            raise ValueError("F0 is immediate feedback; delay must be 0")


@dataclass
class TransferRecord:
    t: int
    commit: bool
    reasons: tuple
    valid: bool
    restricted: bool
    labelled: bool
    labels_applied_before: int
    trust: Optional[Dict[str, float]]   # snapshot after the transfer (learning mechanisms only)


def run(world: World, mech: Mechanism, p: Params = Params(),
        fb: Feedback = Feedback(), keep_trust: bool = False) -> List[TransferRecord]:
    authority = world.scenario.authority_dict()
    store = TrustStore(p.t0)
    queue: deque = deque()            # (available_at, transfer index), in arrival order
    applied = 0
    out: List[TransferRecord] = []

    for t in range(world.scenario.n):
        # Apply every label whose arrival time has passed. Label of t is available
        # before transfer t + d + 1 is decided (spec edge case E13).
        while queue and queue[0][0] <= t:
            _, j = queue.popleft()
            if mech.learns:
                store.update(world.reports[j], world.truth[j], p.alpha)
            applied += 1

        reports = world.reports[t]
        store.record_availability(reports)
        d = validate(reports, store, authority, mech, p)

        if fb.regime == "F0":
            labelled = True
        else:
            labelled = (not d.commit) or (world.audit_u[t] < fb.audit)
        if labelled:
            queue.append((t + fb.delay + 1, t))   # never the decision itself, only the truth

        out.append(TransferRecord(
            t=t, commit=d.commit, reasons=d.reasons, valid=world.valid(t),
            restricted=world.truth[t]["restr"] == FAIL, labelled=labelled,
            labels_applied_before=applied,
            trust=({f"{i}_{k}": store.raw(i, k) for i in ORACLES for k in CHECKS}
                   if keep_trust and mech.learns else None),
        ))
    return out
