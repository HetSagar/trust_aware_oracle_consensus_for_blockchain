# Captions

LNCS rules: figure captions go **below** the figure, table captions go **above** the table, both in 9 pt.
A caption that is not a full sentence takes no final period. Label style: **Fig. 1.** / **Table 1.**
(the LNCS LaTeX class and Word template apply this automatically).

## Figures (caption below)

| Fig. | File | Section | Caption |
| --- | --- | --- | --- |
| 1 | figures/fig1_system | 3 Model | Validation loop. Three offices report on three checks, the validator commits a request only when all three checks pass and otherwise escalates it, and verified labels update trust. |
| 2 | figures/fig2_threshold_tradeoff | 5.2 RQ2 | Commit-threshold trade-off after Revenue degrades (S2): false-commit rate against valid-commit coverage as θ varies from 0.50 to 0.90 in steps of 0.05 (means over 100 seeds, ideal feedback) |
| 3 | figures/fig3_feedback | 5.5 RQ5 | False-commit rate of P under realistic feedback F1 in S2, by audit rate and label delay; whiskers are between-seed 95% CIs, the dashed line and band show ideal feedback F0 |
| 4 | figures/fig4_robustness | 5.7 Robustness | Exploratory robustness study A2 (100 seeds): false-commit rate by mechanism as (a) off-home accuracy, (b) the shared error rate of Revenue and Sub-Registrar and (c) label noise vary; dotted lines mark the main-study settings |

## Tables (caption above)

The table captions are already inside each `tables/tabNN_*.tex` file and in `tables/tables_for_word.docx`.

| Table | File | Section | Caption |
| --- | --- | --- | --- |
| 1 | tab01_related | 2 Related Work | Comparison with related work |
| 2 | tab02_normalisation | 3.2 | Illustrative meaning of each simulated report (+1 / −1; ∅ = no response) |
| 3 | tab03_authority | 3.3 | Claim-specific authority A(i,k) (modelling assumption) |
| 4 | tab04_example | 3.7 Worked example | Worked example: request 123 in S5a, seed 1, with a pending proceeding visible only to the Judiciary |
| 5 | tab05_scenarios | 4.2 | Scenarios; each changes one setting from S1 |
| 6 | tab06_mechanisms | 4.3 | Mechanisms compared |
| 7 | tab07_main | 5 Results | False-commit rate (FCR) and valid-commit coverage (VCC), %, mean (SD) over 100 seeds, ideal feedback |
| 8 | tab08_primary | 5 Results | Pre-specified paired comparisons (100 seeds; percentage points, breaches per 1,000 requests for H4) |
| 9 | tab09_ablation | 5.6 | Exploratory coverage-gate ablation A1 (paired 95% CIs, 100 seeds, percentage points) |
| 10 | tab10_robustness | 5.7 | Exploratory robustness study A2: levels at which each main conclusion holds (range of FCR differences, points) |
| 11 | tab11_status | Appendix A | Status of every result |
| 12 | tab12_notes | Appendix A | Analysis choices not covered by the frozen protocol (accepted by the supervisor) |
