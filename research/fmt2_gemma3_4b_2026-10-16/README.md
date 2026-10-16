# FMT2 screening — Gemma-3-4B-it, 16 October 2026

**Development evidence only** (decision D028). `google/gemma-3-4b-it` at revision `093f9f388b31de276ce2de164bdc2081324b9767`, user-executed on a Colab T4 with the unchanged NF4 + FP16 recipe, prompt v2 and scorer v1.0.0. Returned ZIP SHA-256 `f20b481dd98951567de55ca551df75ae0749ee3a04f06118d7ddf265139b58b3`.

- First attempt: the load failed with `AttributeError` (our loader read the context length from the top-level config; fixed in commit 6eb5ff2).
- This run: the model **loaded**, but **every generation attempt failed** with `AcceleratorError` (36 renderings × 2 attempts, including the single permitted infrastructure retry; 0 outputs). Both parts INCOMPLETE.
- Likely cause (not confirmed, because exception messages are deliberately not stored): numerical overflow of Gemma-3 under FP16 compute, a known Gemma-3 issue. The T4 has no bf16, and the first CUDA fault leaves the device context unusable, so later attempts fail too.

**Result: excluded** (D031). Making Gemma run would require changing the frozen compute recipe for one model (e.g. FP32 compute), which D028 does not allow.
