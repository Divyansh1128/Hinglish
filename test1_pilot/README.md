# Hinglish mathematical reasoning — Test 1 pilot software

Open **Hinglish_Math_Test1_Pilot_Colab.ipynb** in Google Colab (File > Upload notebook). It embeds all helper code, demo fixtures, input templates and documentation. No GitHub repository or Mac path is needed. Hinglish_Test1_Portable.zip contains the editable package, tests, and notebook for archival use; you do not need to upload that ZIP to run the notebook.

## Run it

1. Start with the default MODE='demo', BACKEND='fake', RUN_NAME='demo-v2'. Run all cells. This needs no GPU or model downloads and produces a labeled software results ZIP.
2. Prepare actual reviewed data using DATA_CONTRACT.md and the template JSON files. The reviewed study needs 30 accepted independent families, all 90 E/R/C renderings, two independent reviews and adjudication, and a completed human split audit. This package does not supply a reviewed dataset.
3. In Colab select Runtime > Change runtime type > T4 GPU. In the central settings cell set MODE='reviewed', BACKEND='huggingface', RUN_NAME='pilot-reviewed-v1'. Set USE_DRIVE=True for persistence through runtime disconnects. Keep other protocol settings frozen unless creating a documented new version.
4. Run from the top. Installation pins Transformers/bitsandbytes/Accelerate and associated inference dependencies; Colab's installed CUDA PyTorch is retained and recorded. If those libraries were already imported at other versions, restart the session after installation and rerun. No CUDA dependencies are installed locally on the Mac.
5. Upload pilot_dataset.json and split_manifest.json when prompted. Retain the format-smoke fixture exclusions. Validation must pass before research inference. Download the optional template ZIP if inputs are not ready.
6. Inspect the excluded format-only smoke output, then run the 90-item inference cell. Each question has a fresh context. Progress/ETA update after each completed output. Tokenization of the entire pilot is checked before scored generation; no question truncation is allowed.
7. Inspect summary, errors, paired results, and the manual audit CSV. Independently review all responses. For an overlay, fill manual_correct=true/false plus pseudonymous reviewer_id, reason, category and reviewed_at, upload it via the optional audit cell. Automatic scores remain intact; revised results are archived separately.
8. Download the final *_results.zip. Also use File > Download > Download .ipynb for the executed notebook. You can upload that notebook in the optional export cell to put it inside the ZIP, or return it separately.

Return the reviewed run's ZIP and executed notebook to the research assistant. Incomplete runs are useful for troubleshooting but do not supply a full pilot accuracy result.

## Resume and errors

Use the same RUN_NAME and persistent folder. The notebook reuses frozen input snapshots and immutable model/tokenizer revisions. It refuses changes to data, config, code, backend facts or package environment. Each committed attempt is an atomic JSON file; resume skips successful generations even if wrong, refused, malformed or truncated. There is at most one infrastructure retry, with unchanged settings and a preserved record. OOM stops immediately and is not automatically retried; use a documented new protocol/run for a different memory recipe. Exhausted failures keep the run incomplete.

Clean cell interruption releases the lock and preserves completed outputs and the interrupted attempt. A hard runtime loss may leave RUNNING.lock. Only after confirming that no notebook is actively writing, set RECOVER_STALE_LOCK=True, resume, then set it back to False. An in-flight generation is journaled before it starts; a killed attempt has no scored response and its next attempt consumes the one infrastructure retry. Storage on Drive improves recovery but is not a transactional database; take downloads/backups. Never run two writers in one run directory.

Do not silently lower the output cap, change precision, offload to CPU, enable thinking or replace the model. Missing/duplicate/conflicting finals, refusal and truncation count incorrect. Infrastructure failure is unresolved rather than an incorrect mathematical prediction. The analysis suppresses headline accuracy until all required outputs complete.

## Frozen inference candidate

Qwen/Qwen3-4B; immutable model/tokenizer SHA resolved on first load; NF4 + double quantization; FP16; single CUDA device; SDPA math kernel; no adapters or weight updates; non-thinking greedy decoding; generation seed 11 and deterministic per-item seed; 1,024 new-token cap; total context preflight cap 2,048; batch 1. Bootstrap seed 101 and 10,000 paired family resamples follow pilot_review_packet.md. Actual GPU name, memory, CUDA/PyTorch and installed dependency versions are recorded. The returned smoke run verifies short-input inference on T4; full-pilot and training feasibility remain unverified.

The model card supports explicit enable_thinking=False and requires Transformers >=4.51.0. Greedy decoding is the packet's fixed choice and differs from the card's suggested sampling. See [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B). Hardware support and quantization mechanisms are documented in [Hugging Face bitsandbytes](https://huggingface.co/docs/transformers/quantization/bitsandbytes); workload fit is not guaranteed. Chat text is tokenized with add_special_tokens=False after applying the template, per [chat-template documentation](https://huggingface.co/docs/transformers/main/en/chat_templating). Official documentation checked 10 October 2026; pinned stack is a candidate, not a claimed GPU-tested stack.

Resource measurement: generation latency includes synchronized generation, excludes model download/load and prompt tokenization. Per-attempt PyTorch allocated/reserved peaks include the loaded model baseline; device free memory is an endpoint sample, not a continuously monitored minimum. Model load telemetry is recorded separately. Quantization and output cap are part of the measured condition. No cross-hardware bitwise reproducibility guarantee is made.

## Local verification

```sh
python3 -B build_notebook.py
python3 -B -m unittest discover -s tests -v
python3 -B run_demo.py --output /path/to/demo-run
```

The copied scorer_v1.py is byte-for-byte the existing pilot/scripts/scorer.py (version 1.0.0), preserving strict final-answer policy. Existing project tests remain usable. The builder embeds maintained source files in the notebook; rebuild after any source edit. Future code/scorer changes invalidate an old inference resume: analyze stored outputs in a separately versioned workflow rather than mixing implementations mid-run.

Results include manifests, exact input snapshots and prompts, attempt records, automatic predictions, per-family comparisons, metrics/summary, errors, audit CSV, optional overlay revisions/notebook/chart and SHA256 checksums. Export uses a fixed allowlist and rejects common credential/email patterns; inspect arbitrary user/model free text before sharing. CSV cells beginning with spreadsheet formula characters receive a protective apostrophe; JSONL preserves exact raw text.

No training is implemented. This pilot cannot establish an E+C versus E+R training benefit, causal internal mechanism, or publication novelty. See VERIFICATION.md for what was actually tested.

## Returned GPU smoke evidence and demo-v2 correction

The returned real-model smoke archive completed six short Qwen3-4B generations on a Tesla T4 with bitsandbytes 0.50.2 and torch 2.11.0+cu130. This dependency pin is now used by the main pilot candidate. Seven short outputs including the format fixture establish limited inference feasibility, not 90-item research completion or training fit.

Demo-v2 repairs the count fixture: canonical counters with equivalent count aliases, while keeping unit omission allowed. The fraction fixture remains dimensionless with strict suffix rejection; no arbitrary trailing words are accepted. All originals and the user's ZIP are preserved. The original automatic 0/6 score was dominated by invalid-unit outputs, despite six numerically correct finals. The change is a transparent software repair, not a new experimental result. Existing demo-v1 runs must not be resumed with revised data. Original delivered notebooks/bundle are in archive/.
