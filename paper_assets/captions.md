# Captions

Numbering matches the 10-page Final Working Draft (Figs. 1–3, Tables 1–8 in the paper; Fig. S1 and
Tables S1–S4 in the supplementary material).

LNCS rules: figure captions go **below** the figure, table captions go **above** the table, both in 9 pt.
A caption that is not a full sentence takes no final period. Label style: **Fig. 1.** / **Table 1.**
(the LNCS LaTeX class and Word template apply this automatically).

## Figures (caption below)

| Fig. | File | Section | Caption |
| --- | --- | --- | --- |
| 1 | figures/fig1_system | 3 Model | Validation loop. Three offices report on three checks, the validator commits a request only when all three checks pass and otherwise escalates it, and verified labels update trust. |
| 2 | figures/fig2_threshold_tradeoff | 5 Results, RQ2 | Commit-threshold trade-off after Revenue degrades (S2): false-commit rate against valid-commit coverage as θ varies from 0.50 to 0.90 in steps of 0.05 (means over 100 seeds, ideal feedback) |
| 3 | figures/fig3_robustness | 5.4 Exploratory analyses | Exploratory robustness study A2 (100 seeds): false-commit rate by mechanism as (a) off-home accuracy, (b) the shared error rate of Revenue and Sub-Registrar and (c) label noise vary; dotted lines mark the main-study settings |
| S1 | figures/figS1_feedback | Supplementary | False-commit rate of P under realistic feedback F1 in S2, by audit rate and label delay; whiskers are between-seed 95% CIs, the dashed line and band show ideal feedback F0 |

## Tables (caption above)

The table captions are already inside each `tables/tab*.tex` file and in `tables/tables_for_word.docx`.

| Table | File | Section | Caption |
| --- | --- | --- | --- |
| 1 | tab01_related | 2 Related Work | Comparison with related work |
| 2 | tab02_authority | 3 Model | Claim-specific authority A(i,k) (modelling assumption) |
| 3 | tab03_example | 3 Model | Worked example: request 123 in S5a, seed 1, with a pending proceeding visible only to the Judiciary |
| 4 | tab04_scenarios | 4 Experimental Setup | Scenarios; each changes one setting from S1 |
| 5 | tab05_mechanisms | 4 Experimental Setup | Mechanisms compared |
| 6 | tab06_main | 5 Results | False-commit rate (FCR) and valid-commit coverage (VCC), %, mean over 100 seeds, ideal feedback |
| 7 | tab07_primary | 5 Results | Pre-specified paired comparisons (100 seeds; percentage points; breaches per 1,000 requests) |
| 8 | tab08_robustness | 5.4 Exploratory analyses | Exploratory robustness study A2: levels at which each main conclusion holds, with the range of FCR differences in points |
| S1 | tabS1_normalisation | Supplementary | Illustrative meaning of each simulated report (+1 / −1; ∅ = no response) |
| S2 | tabS2_ablation | Supplementary | Exploratory coverage-gate ablation A1 (paired 95% CIs, 100 seeds, percentage points) |
| S3 | tabS3_status | Supplementary | Status of every result |
| S4 | tabS4_notes | Supplementary | Analysis choices not covered by the frozen protocol (accepted by the supervisor) |
