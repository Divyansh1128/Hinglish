# Phase-3 training runs: log of returned ZIPs

Adapter weights and checkpoints stay on Drive (`MyDrive/Hinglish_Phase3/train/`); the repo keeps each ZIP without `checkpoint/` and `*.safetensors`, with adapter hashes recorded here. From ER-s11 on, each returned ZIP is the whole training root so far. Original full-ZIP hashes are listed for traceability. **DEV numbers are sanity checks only** (PREREGISTRATION; D056). They never select checkpoints, hyperparameters, arms or reruns.

Runs use the launcher `colab_notebooks/phase3/Phase3_Train_Launcher.ipynb` (D057) on Colab runtime version 2026.10 (`release-colab-external-images_20261027-060057_RC00`), which provides the registered torch 2.11.0+cu130. The default "Latest" image was refused by the frozen torch check before any attempt was opened; nothing was logged.

| Run | Attempt | Full ZIP SHA-256 | Valid for gate | Steps / skips | Median s/update | Adapter model SHA-256 | DEV E / R / C (of 40) | DEV invalid | Mean / median output tokens |
|---|---|---|---|---|---|---|---|---|---|
| EC-s11 | 1 | `847a8252…2ce7` | yes | 60/60, 0 | 19.99 | `99561453…0570` | 35 / 20 / 22 | 16/120 | 122.6 / 114 |
| ER-s11 | 1 | `36b79f72…077d` | yes | 60/60, 0 | 20.17 | `5a4240e8…3657` | 34 / 18 / 23 | 18/120 | 120.8 / 118 |
| EE-s11 | 1 | `a1a7fe07…db5a` | yes | 60/60, 0 | 19.64 | `bee8d26c…e8a9` | 36 / 23 / 23 | 9/120 | 121.1 / 112.5 |
| EC-s22 | 1 | `e9b81adb…4ff5` | yes | 60/60, 0 | 19.65 | `55f9d94a…0935` | 37 / 24 / 23 | 13/120 | 122.7 / 113 |
| ER-s22 | 1 | *Drive record; see incidents/ER-s22_dev* | yes | 60/60, 0 | 20.25 | `0fa1c1cd…dcaa` | 33 / 18 / 22 | 21/120 | 126.6 / 113.5 |
| EE-s22 | 1 | *in EC-s33 ZIP (whole root)* | yes | 60/60, 0 | 20.17 | `e3a346c2…6354` | 34 / 22 / 23 | 11/120 | 120.3 / 112 |
| EC-s33 | 1 | `eb617b1e…2de7` | yes | 60/60, 0 | 19.99 | `ebda8424…648e` | 35 / 22 / 20 | 17/120 | 125.3 / 117 |
| ER-s33 | 1 | `64bbb4bc…9c24` | yes | 60/60, 0 | 20.31 | `ed958de1…d73a` | 33 / 19 / 21 | 21/120 | 128.3 / 114 |
| EE-s33 | 1 | `621ed613…9560` | yes | 60/60, 0 | 20.03 | `f6536098…8627` | 34 / 23 / 23 | 12/120 | 133.6 / 116 |
| *Unchanged baseline (reused, Phase 2)* | – | `1c0d2609…ffef` | – | – | – | – | 33 / 19 / 24 | 12/120 | 121 |
| *Phase-2 EC-s11, for reference* | – | – | – | – | – | – | 24 / 13 / 19 | 23/120 | 43 |

## Notes

- **EC-s11 (21 Nov 2026):** COMPLETE, implementation manifest `ad61099a…`, baseline DEV `a8194ac2…`, recipe `a36e8732…`, exposure order file `576e5e6f…`, cursor 960 (480 family visits), finite losses and grad norms, not resumed. DEV 120/120, 0 infrastructure failures. Seed-11 data order `8b89e82a…`, initial adapter `0bbfaad4…` (ER-s11 and EE-s11 must match both).
- **ER-s11 (22 Nov 2026):** COMPLETE, same manifest, recipe and baseline; not resumed; DEV 120/120, 0 infrastructure failures. **Pairing check:** data order `8b89e82a…` and initial adapter `0bbfaad4…` match EC-s11. The returned ZIP holds the whole training root; the EC-s11 adapter hash in it is unchanged.
- **EE-s11 (22 Nov 2026):** COMPLETE, same manifest, recipe and baseline; not resumed; DEV 120/120, 0 infrastructure failures. **Pairing check (seed 11):** EC, ER and EE share data order `8b89e82a…` and initial adapter `0bbfaad4…`. EC-s11 and ER-s11 adapter hashes in the returned root are unchanged. Seed slot 11 is complete.
- **EC-s22 (22 Nov 2026):** COMPLETE, same manifest, recipe and baseline; not resumed; DEV 120/120, 0 infrastructure failures. Seed-22 data order `461d2e60…`, initial adapter `f7d105a8…` (ER-s22 and EE-s22 must match both). All seed-11 adapter hashes in the returned root are unchanged.
- **ER-s22 (22 Nov 2026):** training COMPLETE, valid, not resumed; pairing with EC-s22 verified (order `461d2e60…`, initial adapter `f7d105a8…`). The session died during DEV at ~15:50 UTC; registered recoveries at 16:40 (stale writer, no open attempt; stale engine lock, 112 records kept); DEV then completed 120/120 with 1 infrastructure failure (DV039-R, interrupted before commit, regenerated as attempt 2). The legacy DEV validator rejected that record; fixed by implementation amendment D058 (release `82467191…`, training identity unchanged `ad61099a…`). Evidence in `incidents/ER-s22_dev/`. Runs from EE-s22 on execute under the amended release.
- **EE-s22 (23 Nov 2026):** COMPLETE, valid, not resumed, run under the amended release (D058); DEV 120/120, 0 infrastructure failures. Its own end-of-session ZIP was not saved; the run is archived inside the EC-s33 ZIP, which holds the whole training root. **Pairing check (seed 22):** EC, ER and EE share data order `461d2e60…` and initial adapter `f7d105a8…`. Seed slot 22 is complete.
- **EC-s33 (25 Nov 2026):** COMPLETE, same manifest identity `ad61099a…`, recipe and baseline; not resumed; DEV 120/120, 0 infrastructure failures. Run from a second Google account with Editor access to the shared folder. Seed-33 data order `afc3bde1…`, initial adapter `997ff788…` (ER-s33 and EE-s33 must match both). All six earlier adapter hashes in the returned root are unchanged; no new writer recoveries.
- **ER-s33 (26 Nov 2026):** COMPLETE, same manifest identity, recipe and baseline; not resumed; DEV 120/120, 0 infrastructure failures. **Pairing check (seed 33):** data order `afc3bde1…` and initial adapter `997ff788…` match EC-s33. All seven earlier adapter hashes unchanged; no new writer recoveries. The browser auto-extracted the download; the full-ZIP hash is from the original ZIP (5,276,980,964 bytes, same as Drive), and the archive here was built from the extracted root.
- **EE-s33 (26 Nov 2026):** COMPLETE, same manifest identity, recipe and baseline; not resumed; DEV 120/120, 0 infrastructure failures. **Pairing check (seed 33):** EC, ER and EE share data order `afc3bde1…` and initial adapter `997ff788…`. All eight earlier adapter hashes unchanged; no new writer recoveries. **All nine Phase-3 training runs are complete and valid for the gate (attempt 1 each, no resumes).**
- **Snapshot ZIP named `Phase3_Train_EE-s22.zip` (23 Nov, SHA-256 `49bdb3ba…64bb`):** written by the notebook's `finally` block after the refused session; contains no EE-s22 attempt. Not archived as a run.
- Descriptive only: the self-distilled EC-s11 adapter keeps the unchanged model's output length on DEV (mean 122.6 vs 121 tokens), unlike Phase-2 EC-s11 (43). No decision is taken from DEV.

## Adapter freeze (26 Nov 2026)

`phase3_eval freeze-manifest` on the complete training root (from the EE-s33 ZIP, all nine attempts with weights) wrote `phase3/ADAPTERS_FROZEN.md` (`0de03896…4406`; S=3, confirmatory). `phase3_eval gate` verified it: 3 complete triplets, 2,700 new FINAL_TEST generations. `build_phase3_step2_notebooks.py --finalize` then wrote `phase3/FINAL_EVAL_MANIFEST.md` and `phase3/FINAL_EVAL_PAYLOAD.zip` (`89e57905…f1f9`, 8.8 MB). The payload contains FINAL_TEST and is kept out of git (`.gitignore`); it goes to Drive only. FinalTest notebook `488f1fa7…6ca1`.
