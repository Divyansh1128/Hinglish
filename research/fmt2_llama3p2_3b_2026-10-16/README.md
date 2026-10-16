# FMT2 screening — Llama-3.2-3B-Instruct, 16 October 2026

**Development evidence only** (decision D028). `meta-llama/Llama-3.2-3B-Instruct` at revision `0cb88a4f764b7a12671c53f0838cd831a0843b95`, with the chat-template date pinned to 15 Oct 2026. Frozen prompt `test1-english-final-v2`, greedy decoding, NF4/FP16 recipe and scorer v1.0.0; user-executed on a Colab T4 after two earlier attempts failed at download (token not reaching the notebook, fixed in commit 1993924). Both parts COMPLETE, 36/36. Checksums were verified by `paper_analysis/`. Returned ZIP SHA-256 `ea7977e6f00cc10ce12b96f7e715af37d5aa0d1eaac7f4b79786f28107fd60d0`. Per-rendering data: `per_rendering.csv`.

| Form | Strict correct | numeric_literal_v1 match | Strict invalid |
|---|---:|---:|---:|
| E | 12/12 | 12/12 | 0 |
| R | 9/12 | 9/12 | 1 (truncated) |
| C | 9/12 | 9/12 | 1 (missing FINAL) |

**Result: PASSES the D028 inclusion rule (2/36 strict-invalid).**

Errors are mostly mathematical/comprehension, not format:
- FMT2-006-R → 20: the same "kitna bhinn istemaal hua" misreading (remaining count instead of fraction used) that Qwen3-4B made, now in a second model family.
- FMT2-006-C → 1/3 (wrong simplification of 7/27); FMT2-001-C → 504 (fee applied per plate); FMT2-012-R → 122.
- FMT2-005-R looped to the token cap; FMT2-005-C gave the right fraction without a FINAL line.

E is perfect while R and C each lose 3/12 — the language-form gap the study targets, here on 12 excluded fixtures only (indicative, not an estimate).
