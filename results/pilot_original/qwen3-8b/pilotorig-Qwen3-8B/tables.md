# ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families)

Source: `PilotOrig_results_Qwen3-8B.zip!pilotorig-Qwen3-8B_results.zip`  
Run ID: `pilot_adjudicated-c8e9a75e60734d99ab30274066d5cb89`  
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
| E | 24/24 | 100.0 | [86.2, 100.0] |
| R | 23/24 | 95.8 | [79.8, 99.3] |
| C | 24/24 | 100.0 | [86.2, 100.0] |

_Stored scores only: strict correctness is the stored automatic `correct` (scorer v1.0.0); this tool adds no new scoring._
_One rendering per form per family; families are the unit of analysis._

**Paired family differences in strict accuracy (ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families); 24 families)**

| Contrast | Difference (pp) | Bootstrap 95% interval (pp) | Only first correct | Only second correct | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E−R | +4.2 | [0.0, +12.5] | 1 | 0 | 23 | 0 |
| E−C | 0.0 | [0.0, 0.0] | 0 | 0 | 24 | 0 |
| R−C | −4.2 | [−12.5, 0.0] | 0 | 1 | 23 | 0 |

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
| E | 24 | 111.5 | 72 | 6.97 |
| R | 24 | 133.5 | 75 | 7.27 |
| C | 24 | 118 | 69.5 | 7.09 |

_Token count kind: actual tokenizer. Latency excludes model load and tokenization._

**Strict endpoint beside secondary numeric_literal_v1 (ORIGINAL PILOT — two independent human solvers; language review by one human reviewer + adjudicator (24 accepted families))**

| Form | Strict correct | Strict (%) | Numeric match | Numeric (%) | Disagreements |
| --- | ---: | ---: | ---: | ---: | ---: |
| E | 24/24 | 100.0 | 24/24 | 100.0 | 0 |
| R | 23/24 | 95.8 | 23/24 | 95.8 | 0 |
| C | 24/24 | 100.0 | 24/24 | 100.0 | 0 |

_numeric_literal_v1 is the pre-registered secondary endpoint (D018): exact FINAL-line literal, no unit conversion. Strict scorer v1.0.0 remains primary._

## Figures

- `figures/accuracy_by_form.pdf`
- `figures/accuracy_by_form.png`
- `figures/family_heatmap.pdf`
- `figures/family_heatmap.png`
