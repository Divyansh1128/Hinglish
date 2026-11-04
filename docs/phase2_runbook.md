# Phase-2 Colab runbook (operator guide)

> Written on 4 November 2026 by **Claude, standing in for Astra**. Astra (GPT) could not run the brief `handoffs/2026-11-04_claude_to_astra.md` because Codex's login was revoked. Every statement below comes from `colab_notebooks/build_phase2_notebooks.py`, `t4_smoke/train_phase2.py`, `t4_smoke/phase2_eval.py`, `colab_notebooks/README.md`, `phase2/PREREGISTRATION.md` (Amendments 1–3) and `handoffs/2026-11-04_b2_b3_b4_fixes.md`, as of commit `ea8990d`. Text in "quotes" is printed by the code word for word; `…` marks a part the code fills in. If a notebook ever says something different from this page, **the notebook is right**: stop and tell Claude.

## 0. Safety rules (read these first)

1. **One Colab session at a time.** Never open a Phase-2 notebook in two tabs, two browsers or two accounts at once. The study has a single writer (Amendment 3 item 2).
2. **Never edit cells.** You may only change the `True`/`False` flags in the first code cell, and only when this page tells you to. Each notebook checks its own code against the embedded `IMPLEMENTATION_MANIFEST.md` and refuses to run if anything differs.
3. **Never set `RECOVER_STALE_LOCK` or `RECOVER_STALE_WRITER` to True while another Colab tab or session might still be running.** Check **Runtime → Manage sessions** first. Set the flag back to False straight after the recovery run.
4. **Never set `RESUME_AFTER_DISCONNECT = True`.** It is for engineering only: "a resumed run is NEVER valid for the FinalTest gate".
5. **Never open FINAL_TEST.** Do not open `final_test*.json`, the FinalTest notebook's embedded data, the `MyDrive/Hinglish_Phase2/final_test/` files or `Phase2_FinalTest_results.zip`. Pass them on unopened (Amendment 1 items 13–14).
6. **Never delete, move or rename anything in `MyDrive/Hinglish_Phase2/`.** The baseline, the adapters and the append-only `train/ATTEMPT_LOG.jsonl` live there.
7. Send every ZIP **unchanged** (do not unzip and re-zip it). Paste the SHA-256 that the Download cell prints after "Return:".

## 1. Order of runs

| Step | Notebook | How many times |
|---|---|---|
| 1 | `colab_notebooks/phase2/Phase2_Baseline_DEV.ipynb` | **Once**, before any training |
| 2 | `colab_notebooks/phase2/Phase2_Train.ipynb` | Once per run: 9 runs if nothing fails. The notebook picks the next run itself; you set nothing |
| 3 | Freeze (done by Claude, see §5) | — |
| 4 | `colab_notebooks/phase2/Phase2_FinalTest.ipynb` | **Once.** This notebook does not exist yet; the builder creates it only after the freeze |

## 2. How to run any Phase-2 notebook

1. Open https://colab.research.google.com → **File → Upload notebook** → choose the `.ipynb` file from the repository.
2. **Runtime → Change runtime type → T4 GPU** → Save.
3. **Runtime → Run all.**
4. **Drive:** when Colab asks, allow access to Google Drive with the account you always use. `USE_DRIVE = True` is the default; leave it on. All results are stored in `MyDrive/Hinglish_Phase2/`.
5. An optional Colab secret `HF_TOKEN` only avoids anonymous Hub rate limits. If you have none, the notebook prints "No HF_TOKEN Colab secret (…); downloading anonymously." This is fine.
6. The first cells print "Implementation manifest verified: …", then "GPU: Tesla T4, …", the package versions, "D021 stack mismatches: none" and "Pinned Hub files match the implementation manifest: …". If any of these is missing, see §4.
7. **Run all stops at the first error.** The ZIP is then not created automatically: scroll to the **Download** cell and run it by hand (click its ▶ button). The Train notebook says: "Run this cell even after a failure or a refusal".

## 3. Each notebook

### 3.1 `Phase2_Baseline_DEV.ipynb` (once)
- **What it does:** runs the unchanged Qwen3-4B on DEV (40 families × E/R/C = 120 generations). No FINAL_TEST data is in this notebook.
- **Time:** "about 15–20 minutes".
- **Success prints:**
  - "Run status: COMPLETE 120 / 120";
  - "high unchanged-DEV accuracy (ceiling-risk proxy): FIRES" or "… does not fire — unchanged DEV C k/40 (Wilson 95% …; threshold >= 38/40)". Either result is fine: it is a report, not a pass/fail;
  - "Unchanged-DEV baseline recorded for training (Amendment 2 item 6): base_results.zip <SHA-256>".
- **ZIP to send:** `Phase2_Baseline_DEV_results.zip`.
- **Never rerun it after it completes.** If it is run again, it prints "base already COMPLETE; nothing regenerated", but do not rely on that.

### 3.2 `Phase2_Train.ipynb` (once per run)
- **What it does:** prints the attempt plan, then "Next run from the plan: EC seed 11 (slot 11): attempt 1". It then trains 60 QLoRA updates on all 160 TRAIN families, saves the adapter to Drive and runs a DEV sanity check (a report only; it never selects anything).
- **Time:** "about 25 minutes of training plus about 15 minutes of DEV evaluation on a T4". The 60 updates alone take about 21 min (D042 rate, `handoffs/2026-11-03_phase2_pipeline.md`); checkpoint writes and hashing make up the rest. Plan for roughly 45–50 minutes per session, including installation and model download.
- **Success prints:**
  - "Training-root writer lock acquired: session … (heartbeat every 30 s)";
  - per-update lines "update n: loss … grad_norm … lr …";
  - "EC-s11 attempt 1 (slot 11): valid — COMPLETE: 60/60 successful steps, cursor 960";
  - a JSON block with `"valid_for_gate": true` and `"resumed": false`;
  - the DEV sanity run, ending "Run status: COMPLETE 120 / 120" and "Export: …".
- **ZIP to send:** `Phase2_Train_<ARM>-s<SEED>_attempt-<NN>.zip`, for example `Phase2_Train_EC-s11_attempt-01.zip`. It holds adapter hashes, logs, the training report, an attempt-log snapshot and the DEV results; the weights stay on Drive. If the run was refused before an attempt opened, the ZIP is `Phase2_Train_logs.zip` instead.
- **When everything is done**, it prints "Every seed slot is settled (S = 3): nothing left to train. Next: the adapter freeze (ADAPTERS_FROZEN.md)." Stop and tell Claude.

### 3.3 `Phase2_FinalTest.ipynb` (once, after the freeze)
- **What it does:** evaluates the unchanged model plus the 3S frozen adapters on FINAL_TEST: 1 + 3S checkpoints, 3,000 generations at S = 3. Before loading any model it runs a gate that prints "GATE PASSED: CONFIRMATORY (S = 3) […]". With S = 1 or 2 the gate prints "DESCRIPTIVE-ONLY reduced-S report (S = …)" instead.
- **Sealed:** it prints only progress ("…: n/total generated"), "SEALED (Amendment 1 item 14) — completion/checksum/infrastructure only: …" and statuses. You will never see answers or scores, and you must not look for them.
- **Time:** about 25 × the DEV baseline (3,000 vs 120 generations). That is many hours over several sessions. It "resumes across sessions from Drive: re-run all; generated responses are never regenerated or retried".
- **Success prints:** "All 10 FINAL_TEST runs complete. CONFIRMATORY (S = 3)".
- **ZIP to send:** `Phase2_FinalTest_results.zip`. **Do not open it.** If a run is incomplete, the notebook prints "Incomplete: re-run all to resume (generated responses are kept, never retried)": re-run all, and send the ZIP only when the notebook reports complete.

## 4. Failure messages and what to do

| You see | Meaning | What to do |
|---|---|---|
| "Implementation manifest verified" is missing; or "Embedded IMPLEMENTATION_MANIFEST.md was changed: refusing to run"; "… differs from the implementation manifest: refusing to run"; "Notebook payload differs from the implementation manifest: refusing to run"; "Manifest is for another PREREGISTRATION.md: refusing to run" | The notebook file is edited, old or wrong | Stop. Upload a fresh copy of the notebook from the repository. If the message stays, send a screenshot to Claude |
| "Select Runtime → Change runtime type → T4 GPU", or "Tesla T4 required (Amendment 2 item 3), found …; no attempt was opened." | You got no GPU, or a non-T4 GPU (an A100 or L4 is refused too) | Runtime → Disconnect and delete runtime, select T4, Run all. If Colab gives no T4, try later. Nothing was logged |
| "D021 stack mismatch: no study run until a dated amendment (Amendment 2 item 3): …" (for example "torch 2.11.0+cu130 expected (Colab build), found …") | Colab changed its preinstalled packages. There is no override | **Stop. Do not pip-install anything.** Send the printed version list to Claude. Training waits for a dated amendment |
| "… at the pinned revision has SHA-256 …, manifest …: refusing to run" | A tokenizer or config file on the Hub differs from the pinned one | Stop and send the output to Claude |
| A Hub or network download error before training starts | Temporary network problem; no attempt opened | Run all again later |
| "Run lock exists. Stop any active writer; use recover_lock only after a disconnected runtime.", followed by "Evaluation incomplete (see above): re-run all to resume, then download" | **Stale evaluation lock.** A runtime was killed during an evaluation and left `RUNNING.lock` | Confirm in Runtime → Manage sessions, and in your other tabs and devices, that no other session runs this notebook. Then set `RECOVER_STALE_LOCK = True` and Run all. It prints "RECOVER_STALE_LOCK: removed the stale RUNNING.lock of … (recorded in …_lock_recoveries.jsonl); n stored journal records kept, nothing regenerated". Afterwards set the flag back to **False** |
| "Training-root writer lock HELD by session … (host …, pid …) since …; last heartbeat … (n s ago). Only one session may write a training root …" | **Stale writer** (Train notebook). A session holds `train/WRITER.lock`. It refreshes its heartbeat every 30 s while alive, and "A lock never expires by itself, whatever its heartbeat age" | If another session may still be running, **wait**. A heartbeat only seconds old means it is alive. Only once you are sure **no** other session runs the trainer, set `RECOVER_STALE_WRITER = True` and Run all |
| "… has a start without a recorded outcome. Another session may still be loading or training it …", or "The attempt has no recorded outcome (runtime killed?). Make sure no other session is running, then set RECOVER_STALE_WRITER = True and re-run all." | **Open attempt.** A runtime was killed mid-training (a disconnect) | Same as the stale-writer row: confirm, then set `RECOVER_STALE_WRITER = True` and Run all |
| After `RECOVER_STALE_WRITER = True` it prints "RECOVER_STALE_WRITER = True: the operator confirmed …", "RECOVER_STALE_WRITER: closed EC-s11 attempt 1 -> infrastructure", "RECOVER_STALE_WRITER: recovery logged in WRITER_RECOVERIES.jsonl; stale lock of session … released.", then "Training-root writer lock: free …" | The recovery worked. It is logged, the open attempt counts as an infrastructure failure, and the plan continues in the same session with the retry | Let the run finish. Then set the flag back to **False**. Tell Claude a recovery happened. If it says "-> numerical" or "-> protocol" instead, the attempt's own report already recorded a halting failure: treat it as the HALT row below |
| "INFRASTRUCTURE FAILURE (CUDA out-of-memory): at most one from-scratch retry with the same seed (Amendment 1 item 11)." and "Infrastructure failure (…). Run the Download cell, send the ZIP, then re-run all: the plan above decides the retry or the reserve seed." | **Infrastructure failure**, the only retryable kind: disconnect or kill, CUDA OOM, Drive/filesystem `OSError`, network/Hub error, failed checkpoint write | Run the Download cell and send the ZIP. Then use a fresh runtime (Disconnect and delete runtime) and Run all. The plan gives **one** from-scratch retry ("attempt 2 — from-scratch retry after an infrastructure failure"). After a second infrastructure failure of any arm, the plan moves the whole slot to reserve seed 44, then 55, by itself. Add those runs to the table in §6 |
| "NUMERICAL FAILURE. …" or "PROTOCOL FAILURE — …" between "!!!!" lines, ending "THE STUDY HALTS (PREREGISTRATION Amendment 1 items 10-11, Amendment 2 item 2): this run is INVALID. No retry and no reserve seed. Send the ZIP; any repair needs a dated amendment before any further training." | **The study halts.** Causes: a GradScaler skip, a non-finite value, a hash/identity/label check, or *any* other error such as a `TypeError` | **Stop.** Run the Download cell, send the ZIP and the full cell output to Claude. Do not re-run: every later Train run refuses to start and raises "StudyHalted: THE STUDY HALTS …". Also stop on "PROTOCOL ERROR before any attempt was opened: …" |
| "REFUSED (no attempt was opened): No unchanged-model DEV run record (base_baseline_record.json) in …: run Phase2_Baseline_DEV to completion first …", then "The trainer refused before opening an attempt (exit 2; see its message above). Nothing was logged." | **Baseline missing** (or "not a complete baseline", or "made under implementation manifest …") | Run `Phase2_Baseline_DEV.ipynb` to completion first. If the baseline was already done, do **not** rerun it: send the output to Claude |
| "Configuration or implementation differs from earlier attempts (Amendment 2 item 7): …" or "… already holds attempt evidence: attempts are never overwritten." | The notebook was rebuilt mid-study, or the Drive folder is unexpected | Stop and send the output to Claude |
| "WRITER LOCK LOST: … its outcome is NOT logged again. Send the ZIP." | Another session recovered the training root while this one ran; rule 1 or 3 was broken | Stop all sessions, send the ZIP, tell Claude |
| "Resumed run finished but is never valid. …" | `RESUME_AFTER_DISCONNECT` was True | Set it to False and Run all; tell Claude |
| The runtime dies **during the DEV sanity step**, after the "valid" line was printed | The adapter is valid and logged. The next Train run completes unfinished DEV reports before training anything else, including after adapter 9 | Confirm no other session is running; set `RECOVER_STALE_LOCK = True` if the engine reports a stale evaluation lock, then re-run all. Stored generations are kept |

## 5. After the 9 runs, before FinalTest (done by Claude)

1. When the Train notebook prints "Every seed slot is settled …", send Claude a copy of the Drive folders `MyDrive/Hinglish_Phase2/train` and `MyDrive/Hinglish_Phase2/baseline_dev`. Use Drive → Download; Claude will say if weights can be left out.
2. Claude runs `python3 -B t4_smoke/phase2_eval.py freeze-manifest --train-root <copy of train> --baseline-dir <copy of baseline_dev>`. It refuses if the study is halted, if a slot is still open or if S = 0 ("S = 0: no complete seed triplet, so FINAL_TEST is never accessed"). It rechecks the implementation manifest against the repository and records the retained seeds, S, every adapter hash, the attempt-log hash and the baseline ZIP hash. S = 3 is confirmatory; S = 1–2 is "descriptive-only".
3. Claude commits `phase2/ADAPTERS_FROZEN.md`, together with the analysis code (§11.1), and pushes it. Then Claude rebuilds with `python3 -B colab_notebooks/build_phase2_notebooks.py`. Until the freeze exists, the builder prints "SKIPPED Phase2_FinalTest.ipynb: …".
4. Claude gives you `Phase2_FinalTest.ipynb`. Run it as in §3.3, on the same Drive account. The gate rechecks every adapter and the baseline ZIP on Drive, so nothing in `MyDrive/Hinglish_Phase2/` may have been touched.

## 6. Training checklist (fill in as you go)

The plan's order (Amendment 2 item 4) is slot 11 (EC, ER, EE), then slot 22, then slot 33. A slot is fully settled before the next one starts. The notebook's "Next run from the plan" line must match the row you are on. If a retry or a reserve seed (44, then 55) appears, write it in the Notes column of the row it replaces and add rows below.

| # | Slot | Arm | Seed | Expected ZIP | Done ☐ | Outcome (valid / infra / HALT) | ZIP SHA-256 (from "Return:") | Notes (date, retry, reserve, recovery) |
|---|---|---|---|---|---|---|---|---|
| 0 | — | Baseline | — | `Phase2_Baseline_DEV_results.zip` | ☐ | | | |
| 1 | 11 | EC | 11 | `Phase2_Train_EC-s11_attempt-01.zip` | ☐ | | | |
| 2 | 11 | ER | 11 | `Phase2_Train_ER-s11_attempt-01.zip` | ☐ | | | |
| 3 | 11 | EE | 11 | `Phase2_Train_EE-s11_attempt-01.zip` | ☐ | | | |
| 4 | 22 | EC | 22 | `Phase2_Train_EC-s22_attempt-01.zip` | ☐ | | | |
| 5 | 22 | ER | 22 | `Phase2_Train_ER-s22_attempt-01.zip` | ☐ | | | |
| 6 | 22 | EE | 22 | `Phase2_Train_EE-s22_attempt-01.zip` | ☐ | | | |
| 7 | 33 | EC | 33 | `Phase2_Train_EC-s33_attempt-01.zip` | ☐ | | | |
| 8 | 33 | ER | 33 | `Phase2_Train_ER-s33_attempt-01.zip` | ☐ | | | |
| 9 | 33 | EE | 33 | `Phase2_Train_EE-s33_attempt-01.zip` | ☐ | | | |
| — | — | Freeze | — | (Claude) `phase2/ADAPTERS_FROZEN.md` committed | ☐ | | | |
| 10 | — | FinalTest | — | `Phase2_FinalTest_results.zip` (do not open) | ☐ | | | |
