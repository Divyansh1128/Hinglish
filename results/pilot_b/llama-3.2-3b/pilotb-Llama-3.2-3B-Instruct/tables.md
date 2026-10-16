# PILOT-B EVALUATION — single-reviewer frozen data

Source: `PilotB_results_Llama-3.2-3B-Instruct.zip!pilotb-Llama-3.2-3B-Instruct_results.zip`  
Run ID: `pilot_b-7ed6648488b4418d97e0467c57e3d88f`  
Status: **COMPLETE**; 210/210 renderings completed; 70 families.

Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring.
All 20 checksums.sha256 entries verified.

## Consistency with stored report.py outputs

- predictions.csv correct/attempt_id: match
- metrics.json status: match
- metrics.json accuracy + Wilson: match
- metrics.json paired bootstrap: match

**Strict accuracy by form (PILOT-B EVALUATION — single-reviewer frozen data; 70 families)**

| Form | Correct / families | Accuracy (%) | Wilson 95% CI (%) |
| --- | ---: | ---: | ---: |
| E | 66/70 | 94.3 | [86.2, 97.8] |
| R | 40/70 | 57.1 | [45.5, 68.1] |
| C | 49/70 | 70.0 | [58.5, 79.5] |

_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._
_One rendering per form per family; families are the unit of analysis._

**Paired family differences in strict accuracy (PILOT-B EVALUATION — single-reviewer frozen data; 70 families)**

| Contrast | Difference (pp) | Bootstrap 95% interval (pp) | Only first correct | Only second correct | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E−R | +37.1 | [+24.3, +50.0] | 28 | 2 | 38 | 2 |
| E−C | +24.3 | [+11.4, +37.1] | 21 | 4 | 45 | 0 |
| R−C | −12.9 | [−27.1, +1.4] | 10 | 19 | 30 | 11 |

_Descriptive paired family bootstrap: 10,000 resamples, seed 101, identical to report.py. Discordant counts are families. No significance claim._
_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._

**Stored invalid reasons by form (PILOT-B EVALUATION — single-reviewer frozen data)**

| Invalid reason | E | R | C | Total |
| --- | ---: | ---: | ---: | ---: |
| invalid_numeric_grouping | 1 | 0 | 1 | 2 |
| invalid_unit | 0 | 1 | 0 | 1 |
| missing_final | 0 | 0 | 1 | 1 |
| truncated | 0 | 5 | 2 | 7 |
| **All invalid** | 1 | 6 | 4 | 11 |
| Completed renderings | 70 | 70 | 70 | 210 |

_Counts of stored scorer v1.0.0 invalid_reason over completed renderings._
_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._

**Median tokens and generation latency by form (PILOT-B EVALUATION — single-reviewer frozen data)**

| Form | Completed | Median input tokens | Median output tokens | Median latency (s) |
| --- | ---: | ---: | ---: | ---: |
| E | 70 | 124 | 99 | 5.95 |
| R | 70 | 138 | 119.5 | 7.14 |
| C | 70 | 134.5 | 96.5 | 5.75 |

_Token count kind: actual tokenizer. Latency excludes model load and tokenization._

**Strict endpoint beside secondary numeric_literal_v1 (PILOT-B EVALUATION — single-reviewer frozen data)**

| Form | Strict correct | Strict (%) | Numeric match | Numeric (%) | Disagreements |
| --- | ---: | ---: | ---: | ---: | ---: |
| E | 66/70 | 94.3 | 66/70 | 94.3 | 0 |
| R | 40/70 | 57.1 | 40/70 | 57.1 | 0 |
| C | 49/70 | 70.0 | 49/70 | 70.0 | 0 |

_numeric_literal_v1 is the pre-registered secondary endpoint (D018): exact FINAL-line literal, no unit conversion. Strict scorer v1.0.0 remains primary._

## Figures

- `figures/accuracy_by_form.pdf`
- `figures/accuracy_by_form.png`
- `figures/family_heatmap.pdf`
- `figures/family_heatmap.png`
