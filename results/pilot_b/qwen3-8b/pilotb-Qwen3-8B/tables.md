# PILOT-B EVALUATION — single-reviewer frozen data

Source: `PilotB_results_Qwen3-8B.zip!pilotb-Qwen3-8B_results.zip`  
Run ID: `pilot_b-7fe1dbdf12ea44e9b508cd5fa3ef9e23`  
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
| E | 69/70 | 98.6 | [92.3, 99.7] |
| R | 64/70 | 91.4 | [82.5, 96.0] |
| C | 69/70 | 98.6 | [92.3, 99.7] |

_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._
_One rendering per form per family; families are the unit of analysis._

**Paired family differences in strict accuracy (PILOT-B EVALUATION — single-reviewer frozen data; 70 families)**

| Contrast | Difference (pp) | Bootstrap 95% interval (pp) | Only first correct | Only second correct | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E−R | +7.1 | [0.0, +14.3] | 6 | 1 | 63 | 0 |
| E−C | 0.0 | [−4.3, +4.3] | 1 | 1 | 68 | 0 |
| R−C | −7.1 | [−14.3, 0.0] | 1 | 6 | 63 | 0 |

_Descriptive paired family bootstrap: 10,000 resamples, seed 101, identical to report.py. Discordant counts are families. No significance claim._
_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._

**Stored invalid reasons by form (PILOT-B EVALUATION — single-reviewer frozen data)**

| Invalid reason | E | R | C | Total |
| --- | ---: | ---: | ---: | ---: |
| invalid_unit | 1 | 1 | 0 | 2 |
| **All invalid** | 1 | 1 | 0 | 2 |
| Completed renderings | 70 | 70 | 70 | 210 |

_Counts of stored scorer v1.0.0 invalid_reason over completed renderings._
_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._

**Median tokens and generation latency by form (PILOT-B EVALUATION — single-reviewer frozen data)**

| Form | Completed | Median input tokens | Median output tokens | Median latency (s) |
| --- | ---: | ---: | ---: | ---: |
| E | 70 | 109 | 72.5 | 7.33 |
| R | 70 | 123 | 73.5 | 7.32 |
| C | 70 | 119 | 72.5 | 7.40 |

_Token count kind: actual tokenizer. Latency excludes model load and tokenization._

**Strict endpoint beside secondary numeric_literal_v1 (PILOT-B EVALUATION — single-reviewer frozen data)**

| Form | Strict correct | Strict (%) | Numeric match | Numeric (%) | Disagreements |
| --- | ---: | ---: | ---: | ---: | ---: |
| E | 69/70 | 98.6 | 59/70 | 84.3 | 12 |
| R | 64/70 | 91.4 | 52/70 | 74.3 | 12 |
| C | 69/70 | 98.6 | 56/70 | 80.0 | 13 |

_numeric_literal_v1 is the pre-registered secondary endpoint (D018): exact FINAL-line literal, no unit conversion. Strict scorer v1.0.0 remains primary._

## Figures

- `figures/accuracy_by_form.pdf`
- `figures/accuracy_by_form.png`
- `figures/family_heatmap.pdf`
- `figures/family_heatmap.png`
