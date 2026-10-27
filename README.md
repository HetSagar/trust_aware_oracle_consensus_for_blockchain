# landval — transfer-bundle validator simulation

Plain-Python simulator for *Trust-Weighted Multi-Oracle Validation for Conflicting Land Records*.
It implements the Phase 2 Model Specification and the Phase 3 Experiment Protocol (P1–P9 approved 26 Oct 2026).

AI-assisted working code. Review it, run it yourself, and describe it in your own words in the paper.

## Layout

| Path | What it is |
| --- | --- |
| `landval/model.py` | Constants, authority matrices, mechanisms, `TrustStore`, and the pure `validate()` rule (Algorithm 1, bundle) |
| `landval/world.py` | Scenarios S1–S5b and `make_world()`: truths, reports, outages, audit draws from four independent seeded streams |
| `landval/sim.py` | `run()`: one mechanism over one world, with F0 or F1 feedback and the delayed-label queue |
| `landval/metrics.py` | Counts and rates with explicit denominators (FCR, FAR, VCC, ER, breaches) |
| `config/frozen.json` | Every parameter, scenario, sweep and seed list. `frozen: false` until the freeze |
| `run_experiments.py` | Runs core scenarios and all sweeps; writes `results/<seedset>/` and appends to `RUN_LOG.md` |
| `tests/` | 25 tests: the 14 spec edge cases plus 11 structural checks |

## Run

```bash
pip install numpy pytest        # Python 3.10+; tested on 3.13, numpy 2.5
python -m pytest -q             # must show 25 passed
python run_experiments.py --seeds debug   # debug seeds 9001–9010; ~30 s
```

Final runs (Phase 5), in this order:

1. Set `"frozen": true` and `"frozen_on": "<date>"` in `config/frozen.json`.
2. Commit the repository and write the commit hash in `RUN_LOG.md`.
3. `python run_experiments.py --seeds final` (seeds 1–30). The script refuses to run final seeds while the config is unfrozen.
4. If the stopping rule triggers: `--n-final 40`, then 50, … up to 100.

## Outputs (`results/<seedset>/`)

- `runs.csv`: one row per experiment × scenario × seed × mechanism × setting × window, with raw counts and reason-code counts. S2 rows appear twice: window `all` and window `post250` (transfers 251–1000).
- `transfers_core.csv`: every core-scenario decision (transfer numbers are 1-based).
- `trust_core.csv`: all nine trust scores after each transfer, core scenarios, learning mechanisms only.

## Test cases

| Test | Spec case | Checks |
| --- | --- | --- |
| `test_E1` | E1 | Clean transfer commits under every mechanism |
| `test_E2` | E2 | Pending proceeding: P vetoes; P−V and B2 escalate (support 0.286); B3 and B1 commit |
| `test_E3` | E3 | Alternative matrix: P−V commits at 0.655, P vetoes |
| `test_E4` | E4 | Trust guard blocks the veto; weighted rule still escalates (0.419) |
| `test_E5` | E5 | No responses: NO_EVIDENCE |
| `test_E6` | E6 | Lone Revenue: coverage 0.50 / 0.30 / 0.143; ownership passes exactly at q_min |
| `test_E7` | E7 | Revenue down: S and J cover (0.50, 0.70, 0.857) |
| `test_E8` | E8 | Judiciary down: restriction LOW_COVERAGE (0.286) |
| `test_E9` | E9 | Support exactly 0.65 commits; float tolerance |
| `test_E10` | E10 | Majority 1–1 tie fails; two reason codes |
| `test_E11` | E11a/b | Low trust in Revenue lets others outvote it; at 0.5 it does not |
| `test_E12` | E12 | EMA update 0.5 → 0.55 / 0.45; silent oracle unchanged |
| `test_E13` | E13 | Delay 50: label of transfer 10 applied before transfer 61 |
| `test_E14` | E14 | Above-chance transform at cold start: NO_EVIDENCE on all checks |
| `test_same_seed_same_world` | — | Reproducibility |
| `test_scenarios_share_truths_and_audit_draws` | — | Common random numbers across scenarios |
| `test_s2_degrades_only_revenue_after_transfer_250` | — | S2 changes only Revenue, only from transfer 251 |
| `test_s5_blind_offices_always_report_clear` | — | S5 stress test |
| `test_outage_silences_all_three_checks` | — | Outage is per oracle per transfer |
| `test_truth_rates_close_to_spec` | — | Invalid share ≈ 0.288 |
| `test_non_learning_mechanisms_ignore_feedback_regime` | — | B1, B2 identical under F0 and F1 |
| `test_s5a_veto_never_changes_a_decision` | — | Protocol's deterministic check (0.4 bound) |
| `test_trust_never_learns_from_own_decision` | — | No labels → trust stays at 0.5 |
| `test_f1_labels_escalations_and_audited_commits_only` | — | F1 label selection |
| `test_f0_rejects_delay` | — | F0 means immediate feedback |
