"""Addendum A1: the three coverage gates behave as specified."""
from dataclasses import replace

import pytest

from landval.model import DEFAULT_AUTHORITY, MECHANISMS, ORACLES, Params, TrustStore, validate

P = Params()


def lone_revenue_all_pass():
    r = {}
    for k in ("own", "deed", "restr"):
        for i in ORACLES:
            r[(i, k)] = 1 if i == "R" else None
    return r


def gate(name, cov):
    return replace(MECHANISMS[name], coverage=cov)


def test_review_example_lone_revenue_passes_weighted_gate_on_ownership():
    d = validate(lone_revenue_all_pass(), TrustStore(0.5), DEFAULT_AUTHORITY, MECHANISMS["P-V"], P)
    assert d.detail["own"][0] == pytest.approx(0.5)
    assert "own:LOW_COVERAGE" not in d.reasons


def test_count_gate_rejects_lone_revenue_for_weighted_mechanism():
    d = validate(lone_revenue_all_pass(), TrustStore(0.5), DEFAULT_AUTHORITY, gate("P-V", "count2"), P)
    assert d.reasons == ("own:LOW_COVERAGE", "deed:LOW_COVERAGE", "restr:LOW_COVERAGE")


def test_no_gate_commits_on_one_source():
    for m in ("B1", "B2", "P-V"):
        d = validate(lone_revenue_all_pass(), TrustStore(0.5), DEFAULT_AUTHORITY, gate(m, "none"), P)
        assert d.commit, m


def test_unknown_gate_is_refused():
    with pytest.raises(ValueError):
        validate(lone_revenue_all_pass(), TrustStore(0.5), DEFAULT_AUTHORITY, gate("P-V", "bogus"), P)
