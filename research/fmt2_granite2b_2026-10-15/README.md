# FMT2 load and format test — Granite-3.3-2B-Instruct, 15 October 2026

**Development evidence only** (decision D025). Same 36 excluded FMT2-0.2.0 prompts, frozen prompt `test1-english-final-v2`, greedy decoding, NF4/FP16 recipe and scorer v1.0.0 as the Qwen3-4B and Phi-4-mini runs. Not pilot data.

Run: `ibm-granite/granite-3.3-2b-instruct` at revision `707f574c62054322f6b5b04b6d075f0a8f05e0f0`, user-executed on a Colab T4. Load took 138 s; the 4-bit footprint was 1.42 GB. Both parts COMPLETE (36/36), no truncation. Checksums were verified by `paper_analysis/`. Returned ZIP SHA-256 `4f70e015e426f74d6123b29794713777282b122ac1124236d6638f2445091366`. Per-rendering data: `per_rendering.csv`.

| Form | Strict correct | numeric_literal_v1 match | Strict invalid | Truncated |
|---|---:|---:|---:|---:|
| E | 0/12 | 0/12 | 12 | 0 |
| R | 0/12 | 0/12 | 12 | 0 |
| C | 0/12 | 1/12 | 12 | 0 |

**Finding:** almost every output **comments on the unit instruction after the answer**, e.g. `FINAL: 3.75 kg. (No unit needed as it's already in kilograms.)`, `FINAL: 24, (units: none)`, `FINAL: \\(\\frac{11}{17}\\) (no unit, as it's a fraction)`. Some outputs used `Final answer: \\boxed{8}` or put a `Unit: …` line after FINAL. Most final values look numerically right, but both frozen endpoints reject the trailing commentary, so this run measures instruction-echo formatting, not mathematics. Unlike Phi-4-mini, Granite neither truncated nor drifted into Hindi on R inputs.

## Cross-model summary (FMT2 development runs, same frozen protocol)

| Model | Strict E / R / C (of 12) | Dominant failure |
|---|---|---|
| Qwen3-4B | 12 / 10 / 12 | Two R misreadings of operation words |
| Phi-4-mini-instruct | 6 / 4 / 11 | Inline FINAL; repetition collapse on R |
| Granite-3.3-2B-instruct | 0 / 0 / 0 | Commentary appended after FINAL |

**Methodological point for the paper:** compliance with a strict final-answer format is strongly model-specific. One frozen prompt and scorer cannot be applied across model families without the format confound dominating. A multi-model comparison would need either model-specific prompts validated on excluded data before any pilot run, or LLM-free lenient extraction plus a manual audit. Both are outside the frozen pilot protocol.
