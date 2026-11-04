"""Build or check phase2/IMPLEMENTATION_MANIFEST.md (PREREGISTRATION Amendment 1 item 14, Amendment 2 items 2-7, Amendment 3).

The manifest hashes every executable choice of the Phase-2 study: trainer, label builder, prompt text, chat template
and tokenizer/config files (by pinned revision), generation configuration, engine, scorer v1, numeric_literal_v1 and
numeric_literal_v2, the analysis code, the notebook builders and the notebook payloads, and EXPOSURE_ORDER.json. It
also pins dependency versions, EOS/stopping behaviour and the train vs evaluation dtype preparation.

The Phase-2 notebooks embed this file and its SHA-256 and refuse to run if any embedded code differs from it. The
manifest hashes the notebook *payloads* (code + data ZIP) and the builder that renders the cells, not the .ipynb
files, because each .ipynb in turn embeds this manifest. Regenerate it after any change to a hashed file, then
rebuild the notebooks (python3 -B colab_notebooks/build_phase2_notebooks.py).

  python3 -B phase2/build_implementation_manifest.py           # write
  python3 -B phase2/build_implementation_manifest.py --check   # exit 1 if missing or stale
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "phase2" / "IMPLEMENTATION_MANIFEST.md"
SCHEMA = "phase2-implementation-manifest-1"
for entry in (ROOT, ROOT / "test1_pilot"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from hinglish_pilot import data as engine_data, engine, hf_backend  # noqa: E402
from t4_smoke import phase2_eval, protocol, train_phase2, train_smoke  # noqa: E402

# Values fixed in PREREGISTRATION §1/§4; the manifest refuses to describe files that differ from them.
PREREGISTERED = {
    "test1_pilot/hinglish_pilot/scorer_v1.py": "c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc",
    "secondary_analysis/numeric_endpoint.py": "ce70aefd1f4c03ffe80bbd06d4df025abe92fc0865732b6d2e6db13504ed883f",
}
# Files of Qwen/Qwen3-4B at the pinned revision and its chat template: one source, t4_smoke/train_phase2.py, which
# verifies them at its executable boundary (Sol re-review B2). The notebooks re-download and verify them too.
HUB_FILES = train_phase2.HUB_FILES
CHAT_TEMPLATE = train_phase2.CHAT_TEMPLATE
EOS_STOPPING = {
    "training_target": "reference_solution_en + '<|im_end|>' (id 151645), encoded separately from the prompt; the "
                       "last supervised token is asserted to be <|im_end|>",
    "generation_eos_token_id": [151645, 151643],
    "generation_eos_source": "model.generation_config.eos_token_id from generation_config.json at the pinned revision "
                             "(<|im_end|> 151645, <|endoftext|> 151643); pad_token_id = tokenizer pad <|endoftext|> 151643",
    "stopping": "greedy decoding stops at the first generated EOS id or after max_new_tokens = 1024 new tokens",
    "truncated": "no EOS among the generated ids and 1024 tokens generated; scored 0 by scorer v1",
    "decoding_of_response": "tokenizer.decode(ids, skip_special_tokens=True); the raw form with special tokens is also stored",
    "prompt": "chat template with system = frozen instruction, user = rendering, add_generation_prompt=True, "
              "enable_thinking=False (empty <think></think> block); identical at training and evaluation",
}
DTYPE_PREPARATION = {
    "train": ["AutoModelForCausalLM.from_pretrained(torch_dtype=float16, BitsAndBytesConfig nf4, double quant, "
              "compute float16), sdpa attention, device_map {'': 0}",
              "peft.prepare_model_for_kbit_training(use_gradient_checkpointing=True, use_reentrant=False): casts the "
              "non-quantized parameters (norms, tied embedding/lm_head) to float32",
              "LoRA r16/alpha32/dropout 0.05 on q/k/v/o/gate/up/down; trainable parameters forced to float32",
              "forward under torch.autocast('cuda', float16); loss in float32; AdamW state float32; GradScaler "
              "init 65536, growth 2.0, backoff 0.5, interval 2000; SDPA math kernel only; use_cache False"],
    "evaluation": ["AutoModelForCausalLM.from_pretrained(torch_dtype=float16, BitsAndBytesConfig nf4, double quant, "
                   "compute float16), sdpa attention, model.eval(), no prepare_model_for_kbit_training (norms and "
                   "embeddings stay float16)",
                   "PeftModel.from_pretrained(base, adapter, is_trainable=False): the float32 LoRA weights are loaded "
                   "unmerged (no merge, no re-quantization); no autocast",
                   "inference_mode, SDPA math kernel only, use_cache True, batch 1, deterministic algorithms"],
    "difference": "training upcasts norms/embeddings to float32 and runs under float16 autocast; evaluation keeps the "
                  "frozen engine's float16 base. Standard QLoRA practice, fixed before any Phase-2 output.",
}


def load_notebook_builder():
    spec = importlib.util.spec_from_file_location("build_phase2_notebooks", ROOT / "colab_notebooks" / "build_phase2_notebooks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def groups():
    return {
        "trainer": ["t4_smoke/train_phase2.py", "t4_smoke/train_smoke.py"],
        "label_builder": ["t4_smoke/labels.py"],
        "prompt": ["t4_smoke/protocol.py"],
        "evaluation_driver": ["t4_smoke/phase2_eval.py"],
        "engine": [f"test1_pilot/hinglish_pilot/{p.name}" for p in sorted((ROOT / "test1_pilot" / "hinglish_pilot").glob("*.py"))],
        "scorer_v1": ["test1_pilot/hinglish_pilot/scorer_v1.py"],
        "numeric_literal_v1": ["secondary_analysis/numeric_endpoint.py"],
        "numeric_literal_v2": ["secondary_analysis/numeric_literal_v2.py"],
        "secondary_report": ["secondary_analysis/__init__.py", "secondary_analysis/cmi.py", "secondary_analysis/report_secondary.py"],
        "analysis": [f"phase2_analysis/{p.name}" for p in sorted((ROOT / "phase2_analysis").glob("*.py"))]
                    + ["paper_analysis/safezip.py"],
        "notebook_builders": ["colab_notebooks/build_phase2_notebooks.py", "phase2/build_implementation_manifest.py"],
        "exposure_order": [train_phase2.EXPOSURE_ORDER_PATH],
        "frozen_data": sorted(train_smoke.TRAIN_FILES) + [phase2_eval.FROZEN["dev"][0]],
    }


def hub_cache_check():
    """Compare HUB_FILES with any copy in the local Hub cache at the pinned revision (best effort, offline)."""
    snapshot = Path.home() / ".cache" / "huggingface" / "hub" / "models--Qwen--Qwen3-4B" / "snapshots" / train_smoke.MODEL_REVISION
    checked = {}
    for name, expected in HUB_FILES.items():
        path = snapshot / name
        if path.is_file():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f"Local Hub cache {name} at the pinned revision has SHA-256 {actual}, not {expected}")
            checked[name] = True
    return checked


def build():
    files_by_group = groups()
    files = {path: sha256_file(path) for paths in files_by_group.values() for path in paths}
    for path, expected in PREREGISTERED.items():
        if files[path] != expected:
            raise ValueError(f"{path} SHA-256 {files[path]} differs from the pre-registered {expected}")
    for path, expected in list(train_smoke.TRAIN_FILES.items()) + [phase2_eval.FROZEN["dev"][:2]]:
        if files[path] != expected:
            raise ValueError(f"{path} does not match its frozen SHA-256")
    if protocol.INSTRUCTION != engine.INSTRUCTION:
        raise ValueError("Training and evaluation prompt texts differ")
    exposure = json.loads((ROOT / train_phase2.EXPOSURE_ORDER_PATH).read_text(encoding="utf-8"))
    if (ROOT / train_phase2.EXPOSURE_ORDER_PATH).read_text(encoding="utf-8") != train_phase2.exposure_text(train_phase2.phase2_dataset(ROOT)):
        raise ValueError("phase2/EXPOSURE_ORDER.json is stale: python3 -B t4_smoke/train_phase2.py exposure-order")
    if files[train_phase2.EXPOSURE_ORDER_PATH] != train_phase2.EXPOSURE_ORDER_SHA256:
        raise ValueError("phase2/EXPOSURE_ORDER.json differs from its frozen SHA-256 (train_phase2.EXPOSURE_ORDER_SHA256)")
    if train_phase2.phase2_dataset(ROOT)["families_sha256"] != train_phase2.TRAIN_FAMILIES_SHA256:
        raise ValueError("TRAIN families differ from train_phase2.TRAIN_FAMILIES_SHA256")
    hub_cache_check()
    dev_dataset, dev_splits = phase2_eval.inputs((ROOT / phase2_eval.FROZEN["dev"][0]).read_bytes(), "dev",
                                                  phase2_eval.split_identities(ROOT))
    if (engine_data.digest(dev_dataset), engine_data.digest(dev_splits)) != (train_phase2.DEV_DATASET_SHA256,
                                                                             train_phase2.DEV_SPLIT_SHA256):
        raise ValueError("Frozen DEV engine identities differ from train_phase2.DEV_DATASET_SHA256/DEV_SPLIT_SHA256")
    builder = load_notebook_builder()
    configs = {split: phase2_eval.config_for(split) for split in phase2_eval.FROZEN}
    decoding_keys = ("model_id", "seed", "max_new_tokens", "context_limit", "thinking", "do_sample", "num_beams",
                     "quantization", "double_quantization", "compute_dtype", "attention_backend",
                     "max_infrastructure_retries", "prompt_version")
    return {
        "schema": SCHEMA,
        "preregistration": {"path": "phase2/PREREGISTRATION.md", "sha256": sha256_file("phase2/PREREGISTRATION.md"),
                            "includes": "Amendments 1 (D045), 2 (D046) and 3 (D047)"},
        "groups": files_by_group,
        "files": dict(sorted(files.items())),
        "preregistered_hashes_verified": PREREGISTERED,
        "notebook_payloads": {builder.NAMES[kind]: hashlib.sha256(builder.payload(kind)).hexdigest()
                              for kind in ("baseline", "train")},
        "notebook_payload_note": "SHA-256 of the code+data ZIP embedded in each notebook; the cells are rendered by "
                                 "colab_notebooks/build_phase2_notebooks.py (hashed above). Phase2_FinalTest.ipynb is "
                                 "built only after ADAPTERS_FROZEN.md, from the same builder, and verifies this manifest.",
        "exposure_order": {"path": train_phase2.EXPOSURE_ORDER_PATH, "sha256": files[train_phase2.EXPOSURE_ORDER_PATH],
                           "order_sha256": {seed: entry["order_sha256"] for seed, entry in exposure["seeds"].items()}},
        "prompt": {"version": engine.PROMPT_VERSION, "instruction_sha256": hashlib.sha256(engine.INSTRUCTION.encode("utf-8")).hexdigest(),
                   "identical_in": ["t4_smoke/protocol.py", "test1_pilot/hinglish_pilot/engine.py"]},
        "model": {"id": train_smoke.MODEL_ID, "revision": train_smoke.MODEL_REVISION,
                  "tokenizer_revision": train_smoke.MODEL_REVISION, "hub_files": HUB_FILES, "chat_template": CHAT_TEMPLATE,
                  "trust_remote_code": False, "second_backbone": "none (Amendment 1 item 15: Llama-3.2-3B excluded)"},
        "generation_config": {
            "engine_config_sha256": {split: train_smoke.digest(config) for split, config in configs.items()},
            "decoding": {key: configs["dev"][key] for key in decoding_keys},
            "hf_generation_config": {"max_new_tokens": 1024, "do_sample": False, "num_beams": 1, "use_cache": True,
                                     "eos_token_id": "model.generation_config.eos_token_id", "pad_token_id": 151643,
                                     "repetition_penalty": 1.0, "temperature": 1.0, "top_p": 1.0, "top_k": 50},
            "engine_seed": phase2_eval.ENGINE_SEED, "retry_policy": "at most one unchanged-configuration "
            "infrastructure retry per prompt; a successfully generated response is never retried; OOM never retried",
            "final_test_output": "sealed: completion, checksum and infrastructure status only (Amendment 1 item 14)"},
        "baseline_dev": {
            "record": train_phase2.BASELINE_RECORD, "results_zip": f"{train_phase2.BASELINE_RUN}_results.zip",
            "prompts": train_phase2.BASELINE_PROMPTS, "mode": train_phase2.BASELINE_MODE,
            "dev_file": {"path": phase2_eval.FROZEN["dev"][0], "sha256": phase2_eval.FROZEN["dev"][1]},
            "dataset_sha256": train_phase2.DEV_DATASET_SHA256, "split_sha256": train_phase2.DEV_SPLIT_SHA256,
            "config_sha256": engine_data.digest(configs["dev"]), "engine_code_sha256": engine.code_hash(),
            "digest_definition": "hinglish_pilot.data.digest (compact sorted JSON), as run_manifest.json records them",
            "required_members": list(train_phase2.BASELINE_MEMBERS) + ["source/*.py (the engine group above)"],
            "rule": "Amendment 3 item 3: the trainer's prerequisite, the freeze and the FinalTest gate validate the actual "
                    "results ZIP: complete export with consistent checksums, engine source equal to the engine group, "
                    "recomputed config/dataset/split/code digests equal to these, the registered execution and "
                    "environment (archive_environment) and exactly 120 resolved generations; the evaluation driver "
                    "authenticates its running code against this manifest before binding a run"},
        "archive_environment": {
            "rule": "Amendment 3 item 3: every Phase-2 engine archive records these; the trainer (baseline) and the "
                    "analysis check them against this manifest and PREREGISTRATION §2/§4",
            "fields": {"backend": "run_manifest.json['backend'] and every run_manifest.json['sessions'][i]['backend'] "
                                  "(hinglish_pilot.hf_backend.HFBackend.metadata)",
                       "hardware": "backend['hardware'] (CUDA device name; must contain 'T4')",
                       "capability": "backend['capability'] (list, must be [7, 5])",
                       "gpu_verified": "backend['gpu_verified'] (must be true)",
                       "attention": "backend['attention']", "dtype": "backend['compute_dtype']",
                       "quantization": "backend['quantization'] (BitsAndBytesConfig.to_dict())",
                       "packages": "environment.json['packages'] and every sessions[i]['environment']['packages'] "
                                   "(hinglish_pilot.engine.environment(PHASE2_PACKAGES), which includes peft)",
                       "execution_digest": "run_manifest.json['execution_sha256'] = digest({'backend', 'environment'})"},
            "hardware_contains": "T4", "capability": train_phase2.T4_CAPABILITY, "execution": train_phase2.EXECUTION,
            "quantization": train_phase2.QUANTIZATION,
            "packages": dict(hf_backend.PINS, **hf_backend.ADAPTER_PINS),
            "recorded_packages": list(engine.PHASE2_PACKAGES)},
        "eos_stopping": EOS_STOPPING,
        "dtype_preparation": DTYPE_PREPARATION,
        "training": {"recipe_sha256": train_smoke.digest(train_phase2.RECIPE), "grad_scaler": train_phase2.SCALER,
                     "valid_run": train_phase2.RECIPE["valid_run"], "failure_policy": train_phase2.RECIPE["failure_policy"],
                     "train_families_sha256": train_phase2.TRAIN_FAMILIES_SHA256,
                     "trainer_code_verified_at_entry": ["t4_smoke/" + name for name in train_phase2.TRAINER_CODE],
                     "failure_classes": {
                         "infrastructure": list(train_phase2.INFRASTRUCTURE_KINDS),
                         "protocol": "every ProtocolError (hash, identity, label or data assertion, wherever detected, "
                                     "including at reload) and every other exception, e.g. TypeError",
                         "numerical": "GradScaler skip, non-finite loss, gradient or saved parameter",
                         "rule": "Amendment 2 item 2: unknown errors never earn a retry or a reserve"},
                     "run_order": {"slots": list(train_phase2.SLOTS), "arms": list(train_phase2.ARM_ORDER),
                                   "reserve_queue": list(train_phase2.RESERVE_QUEUE),
                                   "rule": "Amendment 2 item 4: the attempt plan chooses the next pending run; a slot is "
                                           "fully settled before the next slot starts"},
                     "baseline_first": {"record": train_phase2.BASELINE_RECORD, "prompts": train_phase2.BASELINE_PROMPTS,
                                        "rule": "Amendment 2 item 6: no training attempt without a complete unchanged-model "
                                                "DEV run under this manifest; its results-ZIP SHA-256 is in every start "
                                                "event and in ADAPTERS_FROZEN.md"},
                     "identical_across_attempts": "Amendment 2 item 7: configuration and implementation identity in "
                                                  "every start event; a different one is refused",
                     "executable_boundary": "Sol re-review B2: inside every attempt the trainer re-verifies this manifest "
                                            "against its code and registered values, re-downloads model.hub_files at the "
                                            "pinned revision and compares their bytes, and compares the loaded chat "
                                            "template with model.chat_template; a mismatch is a protocol failure",
                     "writer_ownership": {"lock": train_phase2.WRITER_LOCK, "schema": train_phase2.WRITER_SCHEMA,
                                          "heartbeat_seconds": train_phase2.HEARTBEAT_SECONDS,
                                          "recoveries": train_phase2.WRITER_RECOVERIES,
                                          "rule": "Amendment 3 item 2: one writer per training root, with a session ID "
                                                  "and heartbeat; the STARTED report is written before model loading; an "
                                                  "open attempt is never closed automatically; only RECOVER_STALE_WRITER "
                                                  "= True (operator confirmed no other session) logs the recovery, closes "
                                                  "the open attempt as infrastructure and releases the lock"}},
        "dependencies": {"python": "recorded per run (Colab default)",
                         "torch": train_smoke.TORCH_BUILD + " (Colab build; never installed; required exactly)",
                         "torch_build": train_smoke.TORCH_BUILD,
                         "stack_policy": "Amendment 2 item 3: the exact stack on a Tesla T4, checked before any attempt "
                                         "opens and in the Baseline/FinalTest notebooks; a mismatch means no study run",
                         "train": train_smoke.PINS, "evaluation": hf_backend.PINS, "adapter_evaluation": hf_backend.ADAPTER_PINS},
    }


def render(document):
    return (
        "# Phase-2 implementation manifest (PREREGISTRATION Amendment 1 item 14, Amendments 2 and 3)\n\n"
        "Generated by `python3 -B phase2/build_implementation_manifest.py`; verify with `--check`. Do not edit by hand.\n\n"
        "- Commit this file **before the first Phase-2 DEV generation**. The DEV-baseline and Train notebooks embed it "
        "with its SHA-256 and refuse to run if any embedded code or data differs from it.\n"
        "- The trainer rechecks it against the running code and the frozen TRAIN/exposure files before every attempt, "
        "and refuses an attempt whose manifest differs from earlier attempts or from the unchanged-DEV baseline's.\n"
        "- It is rechecked at adapter freeze against the real files, the current builder (every non-file entry and the "
        "required file set) and every start event: every retained run records "
        "this file's SHA-256, and `phase2/ADAPTERS_FROZEN.md` and the FinalTest gate require it.\n"
        "- Any change to a hashed file needs a regenerated manifest and rebuilt notebooks before use.\n\n"
        "```json\n" + json.dumps(document, indent=1, ensure_ascii=False) + "\n```\n"
    )


def parse(text):
    start = text.index("```json\n") + len("```json\n")
    return json.loads(text[start:text.index("\n```", start)])


def current_text():
    return render(build())


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text = current_text()
    if "--check" in argv:
        if not MANIFEST.is_file():
            print(MANIFEST, "is MISSING: run python3 -B phase2/build_implementation_manifest.py")
            return 1
        old = MANIFEST.read_text(encoding="utf-8")
        if old == text:
            print(MANIFEST, "is current", hashlib.sha256(old.encode("utf-8")).hexdigest())
            return 0
        try:
            before, after = parse(old).get("files", {}), parse(text)["files"]
            changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        except ValueError:
            changed = ["(unparseable manifest)"]
        print(MANIFEST, "is STALE; changed files:", ", ".join(changed) or "(non-file entries)")
        return 1
    MANIFEST.write_text(text, encoding="utf-8")
    print(MANIFEST, hashlib.sha256(text.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
