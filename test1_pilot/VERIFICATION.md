# Verification status

Implementation and local verification: 10 October 2026.

- 22 new model-free test methods passed, including multiple malformed review/split/gold rejection cases, exact numeric/unit scoring, invalid/truncated outputs, paired family bootstrap and discordance, bounded infrastructure retries, clean interruption, simulated lost in-flight generation, stale-lock recovery, incompatible resumes, journal corruption, versioned manual overlays, secret detection and ZIP checksums.
- Existing scorer: all 3 test methods passed (including 60 balanced answer cases).
- Existing training-smoke protocol: all 4 test methods and its model-free self-check passed; no training runner was executed.
- Notebook validated with nbformat 5.10.4; every Python cell parsed successfully.
- Entire notebook demo executed in a fresh Jupyter kernel using nbclient. Embedded helpers and fixtures worked without Mac project paths or model downloads.
- Completed demo export checksums passed. The chart helper produced a labeled demo chart, visually inspected for legibility.
- The delivered scorer copy matches the original scorer byte-for-byte.

The fresh Jupyter kernel requires localhost ports; sandbox denied those ports on the initial attempt. The same local verification was rerun with permission outside the sandbox. No external model inference or paid service was used.

No real Qwen inference, T4 loading, GPU memory measurement, reviewed-data evaluation or training was performed locally. The Mac has no local CUDA PyTorch stack. Candidate dependency compatibility, 4-bit loading, actual T4 runtime/memory and model output behavior remain unverified until the Colab run. Review metadata cannot certify truthful annotation or semantic equivalence.

Run artifacts under local_demo are labeled SOFTWARE DEMO only, and are excluded from the portable source bundle. Their fake perfect answers are not experimental results. Notebook build embeds current source/docs; verify_notebook.py records the notebook hash for each verified build in local_demo/notebook_verification.json.

Returned user GPU run: demo-qwen-gpu-v1_results.zip passed all 25 exported-file checksums and fingerprint/journal audits. Qwen3-4B loaded on Tesla T4 with bitsandbytes 0.50.2; six short outputs completed, no infrastructure errors/truncation. This is externally executed smoke evidence, not locally executed research. The version-1 count fixture's gold unit was incorrectly blank; corrected in version-2. Three fraction outputs violate the strict dimensionless suffix policy. Original scores and archive are unchanged. See research/test1_gpu_smoke_audit_2026-10-10.
