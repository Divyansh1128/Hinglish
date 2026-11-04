# Phase-2 unchanged-model DEV baseline (pre-registration §5; Amendment 1 item 7)

Run 4 November 2026 on a Colab Tesla T4 (capability 7.5, GPU verified). The stack matches §2: torch 2.11.0+cu130, transformers 4.51.3, bitsandbytes 0.50.2, peft 0.15.2, accelerate 1.6.0. The run used implementation manifest `726241c5…` (D048).

- Outer ZIP: `Phase2_Baseline_DEV_results.zip`, SHA-256 `1c0d260971a8e185c827809fd2e053e0d4e70add2f7632e490f183e351faffef`. All files match its `SHA256SUMS.txt`.
- Inner results ZIP: `base_results.zip`, SHA-256 `a8194ac29cb17711d8e8e526835daacc368fdc4b5265f51d41f96edff347171a`. This is the hash that training attempts and the freeze record. It passes `train_phase2.verify_baseline` against the committed manifest.
- 120/120 generations, 0 unresolved, one attempt.

**DEV is sanity data only. It is never used to select checkpoints, hyperparameters, arms or reruns.**

| Form | Strict correct | Accuracy | Wilson 95% |
|---|---:|---:|---:|
| E | 33/40 | 82.5% | [68.1, 91.3] |
| R | 19/40 | 47.5% | [32.9, 62.5] |
| C | 24/40 | 60.0% | [44.6, 73.7] |

- **Ceiling-risk proxy:** k = 24/40 (Wilson [44.6, 73.7]). The flag (≥ 38/40) **did not fire**, and the observed DEV C headroom is 40 pp. The planning rerun (`research/phase2_power/phase2_power_dev_rerun_v1.py`, k = 24) is archived separately.
- **Strict-invalid outputs:** 12/120, all format or unit failures: invalid_unit E 4 / R 3 / C 1; percent_requires_dimensionless 1 per form; invalid_answer C 1. This is a descriptive observation. Under the pre-registration the prompt and scorer do not change.
- **Comparison with Pilot-B:** the unchanged model is far less accurate on these GPT-drafted DEV families than on the Claude-drafted Pilot-B (C 60% vs 94%). This is consistent with the author/style shift listed as a limitation in §1. It is descriptive only, and it is not pooled with Pilot-B.
