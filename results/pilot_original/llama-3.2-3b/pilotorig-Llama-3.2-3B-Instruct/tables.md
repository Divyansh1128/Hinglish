# ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families)

Source: `PilotOrig_results_Llama-3.2-3B-Instruct.zip!pilotorig-Llama-3.2-3B-Instruct_results.zip`  
Run ID: `pilot_adjudicated-0ce371a322ab432785ae43d3311a8997`  
Status: **COMPLETE**; 72/72 renderings completed; 24 families.

Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring.
All 20 checksums.sha256 entries verified.

## Consistency with stored report.py outputs

- predictions.csv correct/attempt_id: match
- metrics.json status: match
- metrics.json accuracy + Wilson: match
- metrics.json paired bootstrap: match

**Strict accuracy by form (ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families); 24 families)**

| Form | Correct / families | Accuracy (%) | Wilson 95% CI (%) |
| --- | ---: | ---: | ---: |
| E | 21/24 | 87.5 | [69.0, 95.7] |
| R | 15/24 | 62.5 | [42.7, 78.8] |
| C | 22/24 | 91.7 | [74.2, 97.7] |

_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._
_One rendering per form per family; families are the unit of analysis._

**Paired family differences in strict accuracy (ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families); 24 families)**

| Contrast | Difference (pp) | Bootstrap 95% interval (pp) | Only first correct | Only second correct | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E−R | +25.0 | [+4.2, +45.8] | 7 | 1 | 14 | 2 |
| E−C | −4.2 | [−16.7, +8.3] | 1 | 2 | 20 | 1 |
| R−C | −29.2 | [−45.8, −12.5] | 0 | 7 | 15 | 2 |

_Descriptive paired family bootstrap: 10,000 resamples, seed 101, identical to report.py. Discordant counts are families. No significance claim._
_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._

**Stored invalid reasons by form (ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families))**

| Invalid reason | E | R | C | Total |
| --- | ---: | ---: | ---: | ---: |
| **All invalid** | 0 | 0 | 0 | 0 |
| Completed renderings | 24 | 24 | 24 | 72 |

_Counts of stored scorer v1.0.0 invalid_reason over completed renderings._
_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._

**Median tokens and generation latency by form (ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families))**

| Form | Completed | Median input tokens | Median output tokens | Median latency (s) |
| --- | ---: | ---: | ---: | ---: |
| E | 24 | 128.5 | 97 | 6.01 |
| R | 24 | 150 | 128 | 7.95 |
| C | 24 | 135.5 | 105 | 6.47 |

_Token count kind: actual tokenizer. Latency excludes model load and tokenization._

**Strict endpoint beside secondary numeric_literal_v1 (ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families))**

| Form | Strict correct | Strict (%) | Numeric match | Numeric (%) | Disagreements |
| --- | ---: | ---: | ---: | ---: | ---: |
| E | 21/24 | 87.5 | 21/24 | 87.5 | 0 |
| R | 15/24 | 62.5 | 15/24 | 62.5 | 0 |
| C | 22/24 | 91.7 | 22/24 | 91.7 | 0 |

_numeric_literal_v1 is the pre-registered secondary endpoint (D018): exact FINAL-line literal, no unit conversion. Strict scorer v1.0.0 remains primary._

## Figures

- `figures/accuracy_by_form.pdf`
- `figures/accuracy_by_form.png`
- `figures/family_heatmap.pdf`
- `figures/family_heatmap.png`
