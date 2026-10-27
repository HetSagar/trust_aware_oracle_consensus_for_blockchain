# Run log

Appended automatically by run_experiments.py. Record the git commit hash by hand at the freeze.

## 2026-10-26T17:24:30+00:00 — debug seeds
- seeds: 9001–9010 (10)
- config frozen: False
- python 3.13.17, numpy 2.5.3
- command: python run_experiments.py --seeds debug
- rows: runs 2190, transfers 300000, trust 180000

## 2026-10-27 — protocol frozen
- freeze commit: c0922c3304888da4467c8beece0b3c5462721e7a
- config/frozen.json frozen=true, frozen_on=2026-10-27

## 2026-10-27T09:35:05+00:00 — final seeds
- seeds: 1–30 (30)
- config frozen: True
- python 3.13.17, numpy 2.5.3
- command: python run_experiments.py --seeds final --n-final 30
- rows: runs 6570, transfers 900000, trust 540000

## 2026-10-27T09:41:03+00:00 — final seeds
- seeds: 1–100 (100)
- config frozen: True
- python 3.13.17, numpy 2.5.3
- command: python run_experiments.py --seeds final --n-final 100
- rows: runs 21900, transfers 3000000, trust 1800000

## 2026-10-27 — Phase 5 analysis
- Ran seeds 1–30, then seeds 1–100 (`--n-final 100`). Seeds are deterministic: the first 30 seeds of the 100-seed run are byte-identical to the 30-seed run (checked), so one run evaluated block by block equals adding blocks of 10.
- Stopping rule (half-width ≤ Δ/2), first n where all primary CIs are precise:
  - n=30: too wide H2a 0.379, H2b 0.853, H3 0.551
  - n=40: H2a 0.315, H2b 0.751, H3 0.430
  - n=50: H2a 0.293, H2b 0.653, H3 0.366
  - n=60: H2a 0.260, H2b 0.554, H3 0.348
  - n=70: H2b 0.528, H3 0.323
  - n=80: H2b 0.485, H3 0.305
  - n=90: H2b 0.450, H3 0.290
  - n=100 (cap): H2b 0.422, H3 0.282 — still wider than Δ/2; reported as such.
- Final analysis uses seeds 1–100: `python analysis/stats.py results/final/runs.csv analysis/out`, `python analysis/figures.py results/final/runs.csv analysis/out`, `python analysis/traces.py analysis/out/traces.md`.

### Analysis decisions not covered by the protocol (logged, not deviations from it)
1. H4 has zero variance (P and P−V identical in every seed); the interval is the point 0 and p is set to 1.0 inside the Holm family.
2. H1b is two-sided inside the Holm family of seven (the protocol's "all except H3").
3. Wording when both protocol rows apply (significant AND CI inside ±Δ): "lower/higher, but smaller than Δ" (H1b).
4. Wording when the CI excludes 0 opposite to a one-sided hypothesis: "opposite to hypothesis" (H5). The one-sided test cannot detect this, so the CI is reported.
5. H3 (no direction, outside the Holm family) is worded from its unadjusted CI and labelled descriptive.

## 2026-10-27 — addendum A1 committed before running
- commit: e650d775d246687b230a6bb8a887aca2aff32417 (docs/addendum_A1_coverage.md); exploratory coverage-gate ablation
- A1 run: `python run_addendum_coverage.py` (seeds 1–100, S1–S4, gates G0/G1/G2, F0); analysis: `python analysis/addendum_A1.py results/final analysis/out`.
- Regression check passed: gate G2 reproduces the main-study counts exactly (2,000 runs).
- Diagnostic: no weighted mechanism committed any transfer with a single-responder check under G2 (outages remove an office from all three checks, so a lone responder always fails coverage on another check).
