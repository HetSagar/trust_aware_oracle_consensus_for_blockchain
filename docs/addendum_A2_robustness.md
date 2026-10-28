# Protocol addendum A2 — robustness study (exploratory)

Written 28 Oct 2026, after the main results and addendum A1 were seen, and **before** any A2 run.
Committed before any A2 run; the commit hash is recorded in RUN_LOG.md.
Everything in A2 is **exploratory**. It does not change, replace or re-test any pre-specified hypothesis.

## Reporting commitment

Agreed by the author on 28 Oct 2026: **all A2 results will be reported in the paper, whatever they show.** All outputs are committed to the repository as well.

## Why

The main study assumes fixed oracle accuracies, independent errors and error-free reviews (Draft v3, threats to validity). A2 asks whether the main conclusions still hold when each assumption is relaxed, one at a time.

## Tests (one factor at a time; all other settings as in the frozen config)

| Test | Factor | Levels | Scenarios | Feedback |
| --- | --- | --- | --- | --- |
| R1a | Accuracy on non-home checks | 0.60, 0.70, 0.75 (main), 0.85 | S1, S2 | F0 |
| R1b | Accuracy on the home check | 0.85, 0.90, 0.95 (main) | S1, S2 | F0 |
| R2 | Shared error rate ρ | 0 (main), 0.05, 0.10, 0.20 | S1, S2 | F0 |
| R3 | Label noise rate e | 0 (main), 0.02, 0.05, 0.10 | S2 | F0 and F1 (a = 0.05, d = 50) |

**Shared error (R2).** For each request and each check, with probability ρ, Revenue and Sub-Registrar both report the wrong value on that check, as if both copied one stale record. This overrides their independent draws for that check. Offices that are down still return ∅. The Judiciary is unaffected.

**Label noise (R3).** When a verified label is applied to trust, the recorded truth of each check is flipped independently with probability e. Metrics always use the true state. B1 and B2 do not learn, so they are unaffected by R3 (a sanity check).

**Random streams.** R2 and R3 use two new streams per seed (the 5th and 6th children of the seed's SeedSequence). The first four streams, and therefore every main-study world, stay identical. A test checks this.

- Mechanisms: B1, B2, B3, P−V, P. Seeds 1–100. Metrics: FCR, VCC, ER.
- Windows: all requests; for S2 also requests 251–1000.

## Questions and how "holds" is judged

For each test and level, paired by seed, 95% t-interval, no multiplicity adjustment, no stopping rule:

| Conclusion from the main study | Comparison | Scenario (window) | Metric |
| --- | --- | --- | --- |
| C1 Hybrid beats majority | P−V minus B1 | S1 (all) and S2 (all) | FCR |
| C2 Hybrid beats authority-only after degradation | P−V minus B2 | S2 (251–1000) | FCR |
| C3 Trust-only has lower FCR than the hybrid after degradation | B3 minus P−V | S2 (all) | FCR |

A conclusion **holds** at a level if the interval excludes 0 with the same sign as in the main study. It **weakens** if the interval includes 0. It **reverses** if the interval excludes 0 with the opposite sign. VCC differences for the same pairs are reported alongside.
