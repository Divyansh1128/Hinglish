# Phase-3 training runs: log of returned ZIPs

Adapter weights and checkpoints stay on Drive (`MyDrive/Hinglish_Phase3/train/`); the repo keeps each ZIP without `checkpoint/` and `*.safetensors`, with adapter hashes recorded here. From ER-s11 on, each returned ZIP is the whole training root so far. Original full-ZIP hashes are listed for traceability. **DEV numbers are sanity checks only** (PREREGISTRATION; D056). They never select checkpoints, hyperparameters, arms or reruns.

Runs use the launcher `colab_notebooks/phase3/Phase3_Train_Launcher.ipynb` (D057) on Colab runtime version 2026.10 (`release-colab-external-images_20261027-060057_RC00`), which provides the registered torch 2.11.0+cu130. The default "Latest" image was refused by the frozen torch check before any attempt was opened; nothing was logged.

| Run | Attempt | Full ZIP SHA-256 | Valid for gate | Steps / skips | Median s/update | Adapter model SHA-256 | DEV E / R / C (of 40) | DEV invalid | Mean / median output tokens |
|---|---|---|---|---|---|---|---|---|---|
| EC-s11 | 1 | `847a8252…2ce7` | yes | 60/60, 0 | 19.99 | `99561453…0570` | 35 / 20 / 22 | 16/120 | 122.6 / 114 |
| ER-s11 | 1 | `36b79f72…077d` | yes | 60/60, 0 | 20.17 | `5a4240e8…3657` | 34 / 18 / 23 | 18/120 | 120.8 / 118 |
| *Unchanged baseline (reused, Phase 2)* | – | `1c0d2609…ffef` | – | – | – | – | 33 / 19 / 24 | 12/120 | 121 |
| *Phase-2 EC-s11, for reference* | – | – | – | – | – | – | 24 / 13 / 19 | 23/120 | 43 |

## Notes

- **EC-s11 (21 Nov 2026):** COMPLETE, implementation manifest `ad61099a…`, baseline DEV `a8194ac2…`, recipe `a36e8732…`, exposure order file `576e5e6f…`, cursor 960 (480 family visits), finite losses and grad norms, not resumed. DEV 120/120, 0 infrastructure failures. Seed-11 data order `8b89e82a…`, initial adapter `0bbfaad4…` (ER-s11 and EE-s11 must match both).
- **ER-s11 (22 Nov 2026):** COMPLETE, same manifest, recipe and baseline; not resumed; DEV 120/120, 0 infrastructure failures. **Pairing check:** data order `8b89e82a…` and initial adapter `0bbfaad4…` match EC-s11. The returned ZIP holds the whole training root; the EC-s11 adapter hash in it is unchanged.
- Descriptive only: the self-distilled EC-s11 adapter keeps the unchanged model's output length on DEV (mean 122.6 vs 121 tokens), unlike Phase-2 EC-s11 (43). No decision is taken from DEV.
