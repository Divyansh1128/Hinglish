# D021 training smoke test, Qwen3-4B QLoRA on a Colab T4 (28 October 2026)

Engineering test only: 16 TRAIN families (D041), adapters discarded, never evaluated. Notebook `colab_notebooks/training_smoke/TrainSmoke_Qwen3-4B.ipynb` (after the 28 Oct code review). Results ZIP `TrainSmoke_results_Qwen3-4B.zip`, SHA-256 `49928487767d69b2bf5a83585d53fb1e7a7e3e8495c3415b9595c56ce0a501ae`; all 20 included files match `SHA256SUMS.txt` (checkpoint tensors excluded by design, hashes listed).

**Verdict: GO, stay on Colab T4** (`decision.json`; no failed checks; stack matches D021: torch 2.11.0+cu130, transformers 4.51.3, bitsandbytes 0.50.2, PEFT 0.15.2).

| Arm | Median s/update (updates 3–6) | Peak allocated | Min free | Scaler skips | Reload check |
|---|---|---|---|---|---|
| E+E | 19.8 | 5.02 GB | 10.1 GB | 0 | exact (probe diff 0.0) |
| E+R | 20.4 | 5.03 GB | 10.1 GB | 0 | exact (probe diff 0.0) |
| E+C | 20.6 | 5.03 GB | 10.1 GB | 0 | exact (probe diff 0.0) |

- 32-update E+C probe: median 19.8 s/update, no OOM, finite losses, no scaler skips.
- Every update supervises the same 732–814 English target tokens in all three arms (inputs 2.6–2.8k tokens per update of 16 examples).
- Losses fall from about 2.55 to 0.32–0.41 within 6 updates; in the 32-update probe the training loss reaches about 0.00 by update 24. **The 16 smoke families are memorised within about 1.5 passes**, so the full study's update count (256 over 160 families ≈ 13 passes, about 1.5 h per arm and seed at 20.6 s) carries a real over-fitting risk and must be fixed before any training (D042).
- Timing caveat (code review): updates 5–6 run in a fresh process and include start-up cost, so the median is slightly pessimistic. Examples are at most about 207 tokens; timings hold for data of this length.
