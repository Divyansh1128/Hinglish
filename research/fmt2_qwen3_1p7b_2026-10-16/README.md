# FMT2 screening — Qwen3-1.7B, 16 October 2026

**Development evidence only** (decision D028). Same 36 excluded FMT2-0.2.0 prompts, frozen prompt `test1-english-final-v2`, greedy decoding, NF4/FP16 recipe and scorer v1.0.0. Not pilot data.

`Qwen/Qwen3-1.7B` at revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, user-executed on a Colab T4. Both parts COMPLETE, 36/36, no truncation. Checksums were verified by `paper_analysis/`. Returned ZIP SHA-256 `b0c0fc63c1b7fa719dafd50df591a2bfac462d45ecaeab08b72b9b27487d977a`. Per-rendering data: `per_rendering.csv`.

| Form | Strict correct | numeric_literal_v1 match | Strict invalid |
|---|---:|---:|---:|
| E | 0/12 | 0/12 | 12 |
| R | 0/12 | 0/12 | 12 |
| C | 0/12 | 0/12 | 12 |

**Result: FAILS the D028 inclusion rule (36/36 strict-invalid, limit ≤3).**

**Failure mode — instruction echo.** The model copies the instruction's own wording onto the FINAL line, e.g. `FINAL: 8, followed by its unit in English only if the answer has a unit; write n…`, `FINAL: <number or fraction>, …` and `FINAL: <4.30>,kg`. It also produces duplicate FINAL lines and inline markers. Several outputs show genuine arithmetic errors too (e.g. 72 instead of 59 minutes; 123650 and 217400 instead of 141150). Under the frozen protocol, its E/R/C contrasts would measure instruction-following capacity, not language form.

**Scaling note for the paper:** within the Qwen3 family, the 4B model follows prompt v2 cleanly (0/36 invalid) while the 1.7B model echoes it (36/36 invalid). Format-instruction following, not mathematics, is the first thing that breaks at small scale.
