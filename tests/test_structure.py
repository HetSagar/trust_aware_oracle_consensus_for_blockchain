"""Structural checks required by Plan Phase 4 beyond the 14 edge cases."""
import numpy as np
import pytest

from landval.model import CHECKS, MECHANISMS, ORACLES, Params
from landval.sim import Feedback, run
from landval.world import SCENARIOS, Scenario, make_world

DEBUG_SEEDS = range(9001, 9011)


def test_same_seed_same_world():
    a, b = make_world(SCENARIOS["S1"], 9001), make_world(SCENARIOS["S1"], 9001)
    assert a.truth == b.truth and a.reports == b.reports
    assert np.array_equal(a.audit_u, b.audit_u)


def test_scenarios_share_truths_and_audit_draws():
    """Common random numbers: a scenario change never shifts truths or audit draws."""
    base = make_world(SCENARIOS["S1"], 9002)
    for name in ("S2", "S3", "S4", "S5a", "S5b"):
        w = make_world(SCENARIOS[name], 9002)
        assert w.truth == base.truth, name
        assert np.array_equal(w.audit_u, base.audit_u), name


def test_s2_degrades_only_revenue_after_transfer_250():
    s1, s2 = make_world(SCENARIOS["S1"], 9003), make_world(SCENARIOS["S2"], 9003)
    assert s1.reports[:250] == s2.reports[:250]
    for t in range(250, 1000):
        for k in CHECKS:
            for i in ("S", "J"):
                assert s1.reports[t][(i, k)] == s2.reports[t][(i, k)]


def test_s5_blind_offices_always_report_clear():
    w = make_world(SCENARIOS["S5a"], 9004)
    for r in w.reports:
        for i in ("R", "S"):
            assert r[(i, "restr")] in (1, None)


def test_outage_silences_all_three_checks():
    w = make_world(Scenario("x", outage=0.5), 9005)
    for r in w.reports:
        for i in ORACLES:
            vals = [r[(i, k)] for k in CHECKS]
            assert all(v is None for v in vals) or all(v is not None for v in vals)


def test_truth_rates_close_to_spec():
    sc = Scenario("big", n=20000)
    w = make_world(sc, 9006)
    invalid = sum(not w.valid(t) for t in range(sc.n)) / sc.n
    assert invalid == pytest.approx(0.288, abs=0.01)


def test_non_learning_mechanisms_ignore_feedback_regime():
    w = make_world(SCENARIOS["S2"], 9007)
    for m in ("B1", "B2"):
        a = [r.commit for r in run(w, MECHANISMS[m], Params(), Feedback("F0"))]
        b = [r.commit for r in run(w, MECHANISMS[m], Params(), Feedback("F1", 0.05, 50))]
        assert a == b, m


def test_s5a_veto_never_changes_a_decision():
    """Deterministic check from the protocol: the 0.4 bound makes P and P-V identical."""
    for seed in DEBUG_SEEDS:
        w = make_world(SCENARIOS["S5a"], seed)
        a = [r.commit for r in run(w, MECHANISMS["P"])]
        b = [r.commit for r in run(w, MECHANISMS["P-V"])]
        assert a == b, seed


def test_trust_never_learns_from_own_decision():
    """With no labels at all, trust stays at its starting value."""
    w = make_world(SCENARIOS["S1"], 9008)
    recs = run(w, MECHANISMS["P"], Params(), Feedback("F1", audit=0.0, delay=10_000),
               keep_trust=True)
    assert all(v == 0.5 for v in recs[-1].trust.values())


def test_f1_labels_escalations_and_audited_commits_only():
    w = make_world(SCENARIOS["S1"], 9009)
    recs = run(w, MECHANISMS["P"], Params(), Feedback("F1", audit=0.05, delay=0))
    for r in recs:
        expect = (not r.commit) or (w.audit_u[r.t] < 0.05)
        assert r.labelled == expect


def test_f0_rejects_delay():
    with pytest.raises(ValueError):
        Feedback("F0", delay=5)
