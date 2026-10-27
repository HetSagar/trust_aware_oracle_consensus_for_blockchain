"""The 14 hand-checkable edge cases from the Phase 2 Model Specification (E1-E14).

Expected values were computed with exact fractions before any code was written.
"""
import pytest

from landval.model import (ALT_AUTHORITY, CHECKS, DEFAULT_AUTHORITY, MECHANISMS, ORACLES,
                           Params, TrustStore, validate)
from landval.sim import Feedback, run
from landval.world import Scenario, World

P = Params()
A = DEFAULT_AUTHORITY


def reps(own=None, deed=None, restr=None):
    """Reports as (R, S, J) tuples per check: 1, -1 or None. Omitted check = all None."""
    out = {}
    for k, vals in (("own", own), ("deed", deed), ("restr", restr)):
        vals = vals or (None, None, None)
        for i, v in zip(ORACLES, vals):
            out[(i, k)] = v
    return out


def store(default, **overrides):
    s = TrustStore(default)
    for key, val in overrides.items():
        i, k = key.split("_")
        s.T[(i, k)] = val
    return s


def decide(name, r, s, authority=A, p=P):
    return validate(r, s, authority, MECHANISMS[name], p)


ALL_PASS = (1, 1, 1)


def test_E1_clean_transfer_commits_everywhere():
    r = reps(ALL_PASS, ALL_PASS, ALL_PASS)
    for m in MECHANISMS:
        d = decide(m, r, store(0.5))
        assert d.commit, m
    d = decide("P", r, store(0.5))
    assert all(abs(q - 1) < 1e-12 and abs(s - 1) < 1e-12 for q, s in d.detail.values())


def test_E2_parcel_123_pending_proceeding():
    r = reps(ALL_PASS, ALL_PASS, (1, 1, -1))
    s = store(0.9)
    assert decide("P", r, s).reasons == ("RESTRICTION_REPORTED",)
    for m in ("P-V", "B2"):
        d = decide(m, r, s)
        assert not d.commit and d.reasons == ("restr:LOW_SUPPORT",), m
    assert decide("P-V", r, s).detail["restr"][1] == pytest.approx(0.36 / 1.26)   # 0.286
    assert decide("B2", r, s).detail["restr"][1] == pytest.approx(0.4 / 1.4)
    for m in ("B3", "B1"):
        assert decide(m, r, s).commit, m


def test_E3_veto_matters_only_with_alternative_matrix():
    r = reps(ALL_PASS, ALL_PASS, (1, 1, -1))
    s = store(0.95, J_restr=0.6)
    d_pv = decide("P-V", r, s, authority=ALT_AUTHORITY)
    assert d_pv.commit
    assert d_pv.detail["restr"][1] == pytest.approx(1.14 / 1.74)   # 0.655
    assert decide("P", r, s, authority=ALT_AUTHORITY).reasons == ("RESTRICTION_REPORTED",)


def test_E4_guard_blocks_veto_but_weighted_rule_still_escalates():
    r = reps(ALL_PASS, ALL_PASS, (1, 1, -1))
    s = store(0.9, J_restr=0.5)
    for m in ("P", "P-V"):
        d = decide(m, r, s)
        assert d.reasons == ("restr:LOW_SUPPORT",), m
        assert d.detail["restr"][1] == pytest.approx(0.36 / 0.86)    # 0.419


def test_E5_no_evidence():
    for m in MECHANISMS:
        d = decide(m, reps(), store(0.5))
        assert not d.commit and "NO_EVIDENCE" in d.reasons[0], m


def test_E6_lone_source_cannot_commit():
    r = reps((1, None, None), (1, None, None), (1, None, None))
    d = decide("P", r, store(0.5))
    assert d.reasons == ("deed:LOW_COVERAGE", "restr:LOW_COVERAGE")
    assert d.detail["own"][0] == pytest.approx(0.5)                 # exactly at q_min: passes
    assert d.detail["deed"][0] == pytest.approx(0.3)
    assert d.detail["restr"][0] == pytest.approx(0.2 / 1.4)
    assert decide("B1", r, store(0.5)).reasons == (
        "own:LOW_COVERAGE", "deed:LOW_COVERAGE", "restr:LOW_COVERAGE")


def test_E7_others_cover_for_revenue():
    r = reps((None, 1, 1), (None, 1, 1), (None, 1, 1))
    d = decide("P", r, store(0.5))
    assert d.commit
    assert [round(d.detail[k][0], 3) for k in CHECKS] == [0.5, 0.7, 0.857]


def test_E8_restriction_unconfirmed_without_judiciary():
    r = reps((1, 1, None), (1, 1, None), (1, 1, None))
    for m in ("P", "P-V", "B2"):
        d = decide(m, r, store(0.5))
        assert d.reasons == ("restr:LOW_COVERAGE",), m
    assert decide("P", r, store(0.5)).detail["restr"][0] == pytest.approx(0.4 / 1.4)
    for m in ("B1", "B3"):
        assert decide(m, r, store(0.5)).commit, m


def test_E9_exactly_at_threshold_passes():
    r = reps((1, -1, -1), ALL_PASS, ALL_PASS)
    s = store(0.5, R_own=0.65, S_own=0.25, J_own=0.5)
    d = decide("P", r, s)
    assert d.commit
    assert d.detail["own"][1] == pytest.approx(0.65)
    assert decide("B2", r, s).reasons == ("own:LOW_SUPPORT",)
    assert decide("B3", r, s).reasons == ("own:LOW_SUPPORT",)
    assert decide("B1", r, s).reasons == ("own:NO_MAJORITY",)


def test_E10_majority_tie_and_multiple_reasons():
    r = reps((1, -1, None), (1, 1, None), (1, 1, None))
    d = decide("P", r, store(0.5))
    assert d.reasons == ("own:LOW_SUPPORT", "restr:LOW_COVERAGE")
    assert d.detail["own"][1] == pytest.approx(0.625)
    assert decide("B1", r, store(0.5)).reasons == ("own:NO_MAJORITY",)


def test_E11_trust_discounts_degraded_revenue():
    r = reps((-1, 1, 1), ALL_PASS, ALL_PASS)
    s_low = store(0.9, R_own=0.3)
    d = decide("P", r, s_low)
    assert d.commit and d.detail["own"][1] == pytest.approx(0.75)
    d2 = decide("B2", r, s_low)
    assert d2.reasons == ("own:LOW_SUPPORT",) and d2.detail["own"][1] == pytest.approx(0.5)
    s_mid = store(0.9, R_own=0.5)
    d3 = decide("P", r, s_mid)
    assert d3.reasons == ("own:LOW_SUPPORT",)
    assert d3.detail["own"][1] == pytest.approx(0.81 / 1.26)        # 0.643
    assert decide("B3", r, s_mid).commit


def test_E12_update_rule_and_silence():
    s = TrustStore(0.5)
    r = reps(deed=(1, -1, None))
    s.update(r, {"own": 1, "deed": 1, "restr": 1}, alpha=0.1)
    assert s.T[("R", "deed")] == pytest.approx(0.55)
    assert s.T[("S", "deed")] == pytest.approx(0.45)
    assert s.T[("J", "deed")] == 0.5
    assert s.n_labels[("J", "deed")] == 0


def _tiny_world(n):
    sc = Scenario("tiny", n=n)
    truth = [{k: 1 for k in CHECKS} for _ in range(n)]
    reports = [reps(ALL_PASS, ALL_PASS, ALL_PASS) for _ in range(n)]
    import numpy as np
    return World(sc, 0, truth, reports, np.zeros(n))   # every commit audited


def test_E13_delayed_label_queue():
    w = _tiny_world(70)
    recs = run(w, MECHANISMS["P"], P, Feedback("F1", audit=1.0, delay=50))
    # 0-based index 60 is transfer 61: labels of transfers 1..10 applied
    assert recs[60].labels_applied_before == 10
    assert all(recs[j].labels_applied_before == 0 for j in range(0, 51))
    # Under F0 the label of transfer t is applied before transfer t + 1
    recs0 = run(w, MECHANISMS["P"], P, Feedback("F0"))
    assert [r.labels_applied_before for r in recs0[:4]] == [0, 1, 2, 3]


def test_E14_above_chance_transform_breaks_cold_start():
    p = Params(trust_transform="above_chance", min_labels=0)
    r = reps(ALL_PASS, ALL_PASS, ALL_PASS)
    d = validate(r, TrustStore(0.5), A, MECHANISMS["P"], p)
    assert d.reasons == ("own:NO_EVIDENCE", "deed:NO_EVIDENCE", "restr:NO_EVIDENCE")
    # With a minimum label count, raw trust is used until then
    p2 = Params(trust_transform="above_chance", min_labels=5)
    assert validate(r, TrustStore(0.5), A, MECHANISMS["P"], p2).commit
