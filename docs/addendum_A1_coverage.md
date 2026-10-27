# Protocol addendum A1 — coverage-gate ablation (exploratory)

Written 27 Oct 2026, **after** the main results were seen and **before** this analysis was run.
Committed before any A1 run; the commit hash is recorded in RUN_LOG.md.
Everything in A1 is **exploratory**. It does not change, replace or re-test any pre-specified hypothesis (H1a–H5).

## Why

The Draft v2 review (27 Oct 2026, item 2) noted that the main study does not apply one coverage rule to every mechanism:

- B1 (majority) requires at least 2 of 3 offices to respond on a check;
- the weighted mechanisms (B2, B3, P−V, P) require normalised coverage Q_k ≥ q_min = 0.5.

These gates accept different evidence. Example: on the ownership check, a lone Revenue report has Q = 1.0 / (1.0 + 0.6 + 0.4) = 0.5, so it passes the weighted gate but fails B1's 2-of-3 gate. Comparisons of B1 with the weighted mechanisms therefore mix the effect of aggregation with the effect of the gate.

## Design

Same frozen model, parameters, scenarios and seeds as the main study. Only the coverage gate varies:

| Gate | Rule applied to every mechanism on every check |
| --- | --- |
| G0 None | No coverage requirement (B1: majority of whoever responded; weighted: q_min = 0) |
| G1 Common count | At least 2 of 3 offices responded |
| G2 Main study | B1: at least 2 of 3; weighted: Q_k ≥ 0.5 (as in the main results) |

- Mechanisms: B1, B2, B3, P−V, P. Scenarios: S1, S2, S3, S4. Feedback F0. Seeds 1–100. Window: all transfers.
- Metrics: FCR, VCC, ER (definitions as in the main protocol).
- Comparisons (descriptive, paired by seed, 95% t-interval, no multiplicity adjustment, no stopping rule):
  - P−V minus B1 under G0 and under G1, for FCR and VCC, in S1 and S4.
  - Within P−V: G2 minus G1 (the effect of switching from the count gate to the weighted gate), FCR and VCC, in S1 and S4.
- Diagnostic: number of transfers committed by each weighted mechanism under G2 in which at least one check had a single responder.

## Reporting

Results go in a clearly labelled exploratory subsection with this addendum cited. The main-study tables are not changed. If A1 contradicts a main-study conclusion, the paper says so.
