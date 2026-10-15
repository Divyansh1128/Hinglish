# FMT2 load and format test — Phi-4-mini-instruct, 15 October 2026

**Development evidence only** (decision D024). Same 36 excluded FMT2-0.2.0 fixture prompts, frozen prompt `test1-english-final-v2`, greedy decoding, NF4/FP16 recipe and scorer v1.0.0 as the Qwen3-4B v2 run. Not pilot data. 12 prompts per form.

Run: `microsoft/Phi-4-mini-instruct` at revision `cfbefacb99257ffa30c83adab238a50856ac3083`, user-executed on a Colab T4. Model load took 131 s; the 4-bit model footprint was 2.84 GB. Both parts COMPLETE (36/36, no infrastructure failures). All checksums were verified by `paper_analysis/`, and the tables reproduce the stored metrics. Returned ZIP SHA-256 `28ef08ae6ff4efbe74f910e274c5cb7c8a50ba5dc25fedbef303f90b53c416fa`. Per-rendering data: `per_rendering.csv`.

| Form | Strict correct | numeric_literal_v1 match | Strict invalid | Truncated at 1,024 tokens | Median output tokens | Median latency |
|---|---:|---:|---:|---:|---:|---:|
| E | 6/12 | 6/12 | 6 | 0 | 53 | 3.4 s |
| R | 4/12 | 4/12 | 8 | 6 | 1,024 | 64.7 s |
| C | 11/12 | 11/12 | 0 | 0 | 72 | 4.6 s |

Compare Qwen3-4B on the same prompts and protocol: E 12/12, R 10/12, C 12/12, 0 invalid.

## What happened

1. **Inline FINAL markers (E, and 1 R).** In 7 outputs Phi wrote `… so x = 8. FINAL: 8.` at the end of a paragraph, not on its own line. Strict v1.0.0 rejects these (`final_not_terminal_line`), and so does numeric_literal_v1 (`unsupported_marker`), because both require the marker at the start of a line. One E output used `\(\frac{11}{17}\)`. Most of these answers look numerically right, but neither frozen endpoint credits them. That is why C (11/12) appears to beat E (6/12) — a formatting artifact, not a language effect.
2. **Degenerate repetition on Romanized Hindi.** 6 of 12 R outputs hit the 1,024-token cap. In 4 of them Phi echoed the Hindi question over and over (17–40 repeats of the same passage) under greedy decoding. Non-truncated R outputs explained in romanized Hindi, and at least one contained a reasoning error (22.5 kg instead of 3.75 kg). No Devanagari appeared.
3. **C is handled well:** 11/12, with a terminal FINAL line. The one error (FMT2-012-C, 144 vs 109) is a genuine value error.

## Implications

- Under the frozen protocol, Phi's E/R/C differences would mostly measure inline-marker formatting (E) and repetition collapse (R), not mathematical comprehension. Changing the scorer or prompt for one model after seeing its outputs would be a post-hoc, model-specific protocol change, which is not acceptable.
- The R collapse is itself a qualitative observation worth one sentence in the paper's discussion: a math-strong model without listed Hindi support degenerates on Romanized Hindi under greedy decoding. It is development evidence only.
- Decision D025 records the consequence for the pilot.
