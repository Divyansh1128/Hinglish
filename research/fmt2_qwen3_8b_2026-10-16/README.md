# FMT2 screening — Qwen3-8B, 16 October 2026

**Development evidence only** (decision D028). Same 36 excluded FMT2-0.2.0 prompts, frozen prompt `test1-english-final-v2`, greedy decoding, NF4/FP16 recipe and scorer v1.0.0. Not pilot data.

`Qwen/Qwen3-8B` at revision `b968826d9c46dd6066d109eabc6255188de91218`, user-executed on a Colab T4. Load took 306 s; the 4-bit footprint was 5.96 GB. Both parts COMPLETE, 36/36, no truncation, median latency about 5 s per prompt. Checksums were verified by `paper_analysis/`. Returned ZIP SHA-256 `62ea5158d6ac90bba5bce0a266dce639090e93a05a5fddaf5dcbaad9284f3faa`. Per-rendering data: `per_rendering.csv`.

| Form | Strict correct | numeric_literal_v1 match | Strict invalid |
|---|---:|---:|---:|
| E | 12/12 | 12/12 | 0 |
| R | 12/12 | 12/12 | 0 |
| C | 12/12 | 12/12 | 0 |

**Result: PASSES the D028 inclusion rule (0/36 strict-invalid).** One R output contained Devanagari, to be checked by the English-compliance audit.

Observation (n=2, anecdotal): the two R items Qwen3-4B misread under prompt v2 (FMT2-005-R "bhaag dekar", FMT2-006-R "kitna bhinn") are answered correctly by Qwen3-8B. The reviewed pilot, not these fixtures, will show whether Romanized-Hindi operation-word errors decrease with scale.

## Qwen3 scaling summary on FMT2 (prompt v2)

| Model | Strict-invalid | Strict correct E / R / C |
|---|---:|---|
| Qwen3-1.7B | 36/36 | 0 / 0 / 0 (instruction echo) |
| Qwen3-4B | 0/36 | 12 / 10 / 12 |
| Qwen3-8B | 0/36 | 12 / 12 / 12 |
