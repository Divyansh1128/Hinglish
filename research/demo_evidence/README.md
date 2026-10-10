# Returned demo archives - software evidence only

These are byte-for-byte copies of the two user-returned Colab exports. `checksums.sha256` records archive hashes; each ZIP also contains its own exported-file checksums.

- `demo-v1_results.zip`: six synthetic generations using a fake backend. The fixture scores verify software plumbing, not model reasoning.
- `demo-qwen-gpu-v1_results.zip`: six real Qwen3-4B generations on short excluded demo fixtures on a Tesla T4, plus recorded format-smoke material. Loading/inference succeeded. Original automatic scores are 0/6 due to invalid units, despite the six extracted numeric values matching proposed fixture gold. See the [scoring and GPU audit](../test1_gpu_smoke_audit_2026-10-10/README.md).

Neither archive is a reviewed research pilot, human review record, fine-tuning result or confirmatory evidence. Demo-v2 corrects count-fixture unit metadata in the current software; the v1 archives and original scores are deliberately preserved. Do not resume these v1 runs using changed data/code.

The teammate guide and current status explain the limits of the measurements. Raw generated text and reported environment are available here for teammates to inspect. No executed notebook was reliably included in either returned ZIP; versioned delivered v1 notebooks are in `test1_pilot/archive/` at the repository root.
