# Frozen engine snapshots

`v1/hinglish_pilot/` is a byte-identical copy (3 Nov 2026, `v1/SHA256SUMS`) of the engine that is embedded in every
notebook built before Phase 2: Test 1, the GPU smoke, the format screening, Pilot-B and the original-pilot notebooks.
`build_notebook.payload()` embeds this snapshot, so those notebooks stay byte-identical while the live
`../hinglish_pilot/` gains the backward-compatible Phase-2 modes (`phase2_dev`, `phase2_final_test`) and the optional
LoRA adapter. Never edit this snapshot.
