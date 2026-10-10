# Returned Colab demo audit — 10 October 2026

Input: user-returned `demo-v1_results.zip` (original local archive retained).

PASS: all 21 exported-file checksums; dataset/split/config/source fingerprints; six unique attempt-record hashes; automatic scores independently recomputed with the existing scorer.

Run COMPLETE: six outputs, two synthetic families, fake backend, zero unresolved failures and empty errors.jsonl. The 100% fixture scores are software checks only. No real model was loaded and no GPU feasibility evidence was produced. No executed notebook was included.

Recorded runtime: Python 3.13.15, torch 2.11.0+cu130, Transformers 4.51.3, bitsandbytes 0.45.5. Dependency installation alone is not a compatibility test; verify the actual GPU stack before real inference.

Next research prerequisite: prepare and independently review the 30-family E/R/C dataset and split manifest. An actual-model run on software fixtures can separately test GPU loading, but must remain labeled as demo.
