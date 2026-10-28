"""Addendum A2: new streams leave main-study worlds unchanged; R2 and R3 behave as specified."""
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from landval.metrics import counts
from landval.model import CHECKS, MECHANISMS, Params
from landval.sim import Feedback, run
from landval.world import SCENARIOS, make_world

RUNS = Path(__file__).resolve().parents[1] / "results" / "final" / "runs.csv"


@pytest.mark.skipif(not RUNS.exists(), reason="final results not present")
def test_main_study_results_reproduce_exactly():
    main = pd.read_csv(RUNS)
    for sc, seed in (("S1", 1), ("S2", 37), ("S4", 100)):
        w = make_world(SCENARIOS[sc], seed)
        for m in ("B1", "P"):
            c = counts(run(w, MECHANISMS[m], Params(), Feedback("F0")))
            row = main[(main.experiment == "core") & (main.window == "all") & (main.scenario == sc)
                       & (main.seed == seed) & (main.mechanism == m)].iloc[0]
            for k in ("commits", "false_commits", "valid_commits", "escalations"):
                assert c[k] == row[k], (sc, seed, m, k)


def test_rho_zero_is_the_main_world():
    a = make_world(SCENARIOS["S1"], 5)
    b = make_world(replace(SCENARIOS["S1"], shared_rho=0.0), 5)
    assert a.reports == b.reports and a.truth == b.truth


def test_shared_errors_hit_revenue_and_subregistrar_together_only():
    base = make_world(SCENARIOS["S1"], 6)
    w = make_world(replace(SCENARIOS["S1"], shared_rho=0.2), 6)
    both_wrong = 0
    for t in range(1000):
        for k in CHECKS:
            assert w.reports[t][("J", k)] == base.reports[t][("J", k)]   # Judiciary untouched
            r, s, g = w.reports[t][("R", k)], w.reports[t][("S", k)], w.truth[t][k]
            if r is not None and s is not None and r == s == -g:
                both_wrong += 1
    # 0.2 shared + 0.25*0.05-ish independent co-errors; well above the base rate
    assert both_wrong / 3000 > 0.18


def test_label_noise_changes_trust_but_not_truth_or_non_learners():
    w = make_world(SCENARIOS["S2"], 7)
    clean = run(w, MECHANISMS["P"], Params(), Feedback("F0"), keep_trust=True)
    noisy = run(w, MECHANISMS["P"], Params(), Feedback("F0", label_noise=0.1), keep_trust=True)
    assert clean[-1].trust != noisy[-1].trust
    assert [r.valid for r in clean] == [r.valid for r in noisy]          # metrics use the truth
    for m in ("B1", "B2"):
        a = [r.commit for r in run(w, MECHANISMS[m], Params(), Feedback("F0"))]
        b = [r.commit for r in run(w, MECHANISMS[m], Params(), Feedback("F0", label_noise=0.1))]
        assert a == b, m


def test_label_noise_flip_rate():
    w = make_world(SCENARIOS["S1"], 8)
    assert (w.label_u < 0.05).mean() == pytest.approx(0.05, abs=0.01)
