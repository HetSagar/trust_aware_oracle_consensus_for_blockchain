"""Transfer-level metrics with explicit denominators (Phase 2 spec, Metrics)."""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from .sim import TransferRecord


def counts(records: List[TransferRecord], start: int = 0, end: Optional[int] = None) -> Dict:
    """Raw counts over transfers with start <= t < end (0-based). S2 window: start=250."""
    rs = [r for r in records if r.t >= start and (end is None or r.t < end)]
    c = Counter()
    reasons = Counter()
    for r in rs:
        c["transfers"] += 1
        c["valid"] += r.valid
        c["invalid"] += not r.valid
        c["restricted"] += r.restricted
        if r.commit:
            c["commits"] += 1
            c["false_commits"] += not r.valid
            c["valid_commits"] += r.valid
            c["breaches"] += r.restricted
        else:
            c["escalations"] += 1
            if len(r.reasons) > 1:
                c["multi_reason"] += 1
            for code in r.reasons:
                reasons[code] += 1
    out = {k: c.get(k, 0) for k in ("transfers", "valid", "invalid", "restricted", "commits",
                                    "false_commits", "valid_commits", "breaches",
                                    "escalations", "multi_reason")}
    out["reasons"] = dict(reasons)
    return out


def rates(c: Dict) -> Dict[str, Optional[float]]:
    """Percentages. FCR is None (undefined) when nothing commits."""
    def pct(num, den):
        return None if den == 0 else 100.0 * num / den
    return {
        "FCR": pct(c["false_commits"], c["commits"]),
        "FAR": pct(c["false_commits"], c["invalid"]),
        "VCC": pct(c["valid_commits"], c["valid"]),
        "ER": pct(c["escalations"], c["transfers"]),
        "breaches_per_1000": 1000.0 * c["breaches"] / c["transfers"] if c["transfers"] else None,
    }
