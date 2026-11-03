# Colab notebooks

Upload a notebook to https://colab.research.google.com (File → Upload notebook), choose **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. A results ZIP downloads at the end; send it to the team.

## The real experiment (pilot)

`test1_pilot/Hinglish_Math_Test1_Pilot_Colab.ipynb` runs the reviewed pilot. **Run it only after the human-reviewed dataset is frozen.** Set `MODE='reviewed'`, `BACKEND='huggingface'`, and run once per model with its own `RUN_NAME`: `MODEL_ID='Qwen/Qwen3-4B'` (primary) `MODEL_ID='Qwen/Qwen3-8B'` (second, decision D030) and `MODEL_ID='meta-llama/Llama-3.2-3B-Instruct'` (third, cross-family, decision D032; needs the HF token secret).

## Pilot-B evaluation (`pilot_b_eval/`), ready now

The real evaluation on the frozen, human-reviewed Pilot-B set (70 families × E/R/C = 210 prompts), pre-registered in `pilot_b/PREREGISTRATION.md`. Self-contained, with nothing to upload. About 25–35 minutes each.

| Notebook | Model | Note |
|---|---|---|
| `PilotB_Qwen3-4B.ipynb` | Qwen3-4B | Primary; run first |
| `PilotB_Qwen3-8B.ipynb` | Qwen3-8B | Scaling comparison |
| `PilotB_Llama-3.2-3B.ipynb` | Llama-3.2-3B | Cross-family; needs your HF token |

## Phase 2 (`phase2/`), D043 and `phase2/PREREGISTRATION.md` with Amendments 1 and 2

Before the first run, commit `phase2/EXPOSURE_ORDER.json` and `phase2/IMPLEMENTATION_MANIFEST.md` (Amendment 1 items 9 and 14). Every notebook embeds the manifest and refuses to run if any embedded code, data or pinned tokenizer/config file differs from it. Every notebook also refuses any stack other than the exact §2 stack (torch 2.11.0+cu130 included) on a T4; there is no override (Amendment 2 item 3).

Run in this order, each on a fresh T4 runtime with **Run all**. Drive is on by default (`MyDrive/Hinglish_Phase2/`); the baseline, the adapters and the attempt log stay there. Each notebook downloads a ZIP with `SHA256SUMS.txt`; send it unchanged. If a runtime was killed during an evaluation and a re-run stops with "Run lock exists", confirm that no other Colab session is running it, set `RECOVER_STALE_LOCK = True`, re-run all, then set it back (the recovery is logged; stored outputs are never regenerated; Amendment 2 item 5).

1. **`Phase2_Baseline_DEV.ipynb`**, once, before any training: the unchanged Qwen3-4B on DEV (120 generations, about 15–20 min). It prints "high unchanged-DEV accuracy (ceiling-risk proxy)" with k/40 and its Wilson 95% interval (fires at DEV C ≥ 38/40; item 7) and records `baseline_dev/base_baseline_record.json` (results-ZIP and implementation-manifest SHA-256). The trainer refuses every attempt without it (Amendment 2 item 6).
2. **`Phase2_Train.ipynb`**, once per run, with **nothing to set**: the append-only `train/ATTEMPT_LOG.jsonl` picks the next pending run (Amendment 2 item 4): slot 11, then 22, then 33; arms EC, then ER, then EE; a slot is fully settled before the next one starts; reserves 44, then 55. The trainer consults the plan itself, refuses a configuration or implementation that differs from earlier attempts, and verifies the manifest, the TRAIN bytes and the exposure order at its entry point. Infrastructure failures are only: disconnect/kill, CUDA OOM, a Drive/filesystem `OSError`, a network/Hub download error, a failed checkpoint write; they allow one fresh attempt from scratch, and after a second one the whole slot moves to the next unused reserve seed automatically. A numerical failure or any other error (protocol, including e.g. a `TypeError`) halts the study and the notebook refuses all further training. Each valid run has exactly 60 successful optimizer steps (item 10), then the DEV sanity evaluation. `RESUME_AFTER_DISCONNECT = True` is engineering-only; a resumed run is never valid.
3. When every slot is complete or exhausted, generate the ```json block of `phase2/ADAPTERS_FROZEN.md` with `python3 -B t4_smoke/phase2_eval.py freeze-manifest --train-root <copy of MyDrive/Hinglish_Phase2/train> --baseline-dir <copy of MyDrive/Hinglish_Phase2/baseline_dev>` (it rechecks the implementation manifest against this repository and every start event, records the retained seeds, S, the attempt-log hash and the baseline results-ZIP hash; S = 1–2 is marked descriptive-only, S = 0 is refused; item 12) and commit it. Then rebuild to create **`Phase2_FinalTest.ipynb`**: the unchanged model plus the 3S retained adapters on FINAL_TEST, **sealed** (it prints only completion, checksum and infrastructure status; items 13–14).

Rebuild with `python3 -B colab_notebooks/build_phase2_notebooks.py` (`--check` verifies them) after `python3 -B phase2/build_implementation_manifest.py` (`--check` verifies the manifest). Until `phase2/ADAPTERS_FROZEN.md` exists, the builder skips the FinalTest notebook and prints why. Handoffs: `../handoffs/2026-11-03_amendment1_pipeline.md`, `../handoffs/2026-11-04_sol_findings_training_fixes.md`.

## Training smoke test (`training_smoke/`), decision D021

`TrainSmoke_Qwen3-4B.ipynb`: 6 QLoRA updates per arm (E+E, E+R, E+C) on 16 TRAIN families, checkpoint reload, a 32-update E+C stability probe, and the pre-declared go/no-go timing verdict. Never touches DEV or FINAL_TEST. About 40–120 minutes on a T4. Rebuild with `python3 -B colab_notebooks/build_training_smoke_notebook.py`.

## Model screening (`model_screening/`)

Each notebook runs the same 36 excluded practice prompts with the frozen prompt, decoding and scorer. A model joins the pilot only with ≤3/36 format failures (decision D028).

| Notebook | Result | Status |
|---|---|---|
| `ModelTest_Qwen3-4B.ipynb` | 0/36 failures | ✅ Done: primary pilot model |
| `ModelTest_Qwen3-8B.ipynb` | 0/36 failures | ✅ Done: second pilot model |
| `ModelTest_Qwen3-1.7B.ipynb` | 36/36 (copies the instruction) | ✅ Done: excluded |
| `ModelTest_Phi-4-mini.ipynb` | 14/36 (inline answer, R looping) | ✅ Done: excluded |
| `ModelTest_Granite-3.3-2B.ipynb` | 36/36 (remarks after answer) | ✅ Done: excluded |
| `ModelTest_Gemma-3-4B.ipynb` | GPU crash under FP16 | ✅ Done: excluded |
| `ModelTest_Llama-3.2-3B.ipynb` | 2/36 failures; E 12, R 9, C 9 | ✅ Done: third pilot model |

Results and analyses: `research/fmt2_*`. Rebuild these notebooks with `python3 -B secondary_analysis/build_format_notebook.py`.
