"""Build or check phase2/IMPLEMENTATION_MANIFEST.md (PREREGISTRATION Amendment 1 item 14).

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

from hinglish_pilot import engine, hf_backend  # noqa: E402
from t4_smoke import phase2_eval, protocol, train_phase2, train_smoke  # noqa: E402

# Values fixed in PREREGISTRATION §1/§4; the manifest refuses to describe files that differ from them.
PREREGISTERED = {
    "test1_pilot/hinglish_pilot/scorer_v1.py": "c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc",
    "secondary_analysis/numeric_endpoint.py": "ce70aefd1f4c03ffe80bbd06d4df025abe92fc0865732b6d2e6db13504ed883f",
}
# Files of Qwen/Qwen3-4B at the pinned revision (SHA-256 of the bytes served by the Hub at that revision, measured
# 3 Nov 2026; the four tokenizer files also match the local Hub cache). The notebooks re-download and verify them.
HUB_FILES = {
    "config.json": "8ba006f74fecfaaeb392872a60f4a480e7ec9860153d2e1b769ec81f9a147f8a",
    "generation_config.json": "2325da0f15bb848e018c5ae071b7943332e9f871d6b60e2ed22ca97d4cb993d2",
    "merges.txt": "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5",
    "model.safetensors.index.json": "6dc0981b8829fead746441f68f38f24c5ca4a3a66351f652c26c6df0efc43ab2",
    "tokenizer.json": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
    "tokenizer_config.json": "d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
}
CHAT_TEMPLATE = {  # tokenizer_config.json["chat_template"] at the pinned revision (4,168 characters)
    "source": "tokenizer_config.json at the pinned revision (no chat_template.jinja exists there)",
    "digest": "41d5929bf73796beb66809ac700b2cf3ff81694f933e5c14d52b7fd6963c947d",
    "digest_definition": "train_smoke.digest(template) = SHA-256 of json.dumps(template) in UTF-8; recorded at run time "
                         "as chat_template_sha256 by the trainer and by the engine backend",
    "utf8_sha256": "a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8",
    "kwargs": {"enable_thinking": False, "add_generation_prompt": True},
}
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
    hub_cache_check()
    builder = load_notebook_builder()
    configs = {split: phase2_eval.config_for(split) for split in phase2_eval.FROZEN}
    decoding_keys = ("model_id", "seed", "max_new_tokens", "context_limit", "thinking", "do_sample", "num_beams",
                     "quantization", "double_quantization", "compute_dtype", "attention_backend",
                     "max_infrastructure_retries", "prompt_version")
    return {
        "schema": SCHEMA,
        "preregistration": {"path": "phase2/PREREGISTRATION.md", "sha256": sha256_file("phase2/PREREGISTRATION.md"),
                            "includes": "Amendment 1 (D045)"},
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
        "eos_stopping": EOS_STOPPING,
        "dtype_preparation": DTYPE_PREPARATION,
        "training": {"recipe_sha256": train_smoke.digest(train_phase2.RECIPE), "grad_scaler": train_phase2.SCALER,
                     "valid_run": train_phase2.RECIPE["valid_run"], "failure_policy": train_phase2.RECIPE["failure_policy"]},
        "dependencies": {"python": "recorded per run (Colab default)", "torch": train_smoke.TORCH_BUILD + " (Colab build; recorded, not installed)",
                         "train": train_smoke.PINS, "evaluation": hf_backend.PINS, "adapter_evaluation": hf_backend.ADAPTER_PINS},
    }


def render(document):
    return (
        "# Phase-2 implementation manifest (PREREGISTRATION Amendment 1 item 14)\n\n"
        "Generated by `python3 -B phase2/build_implementation_manifest.py`; verify with `--check`. Do not edit by hand.\n\n"
        "- Commit this file **before the first Phase-2 DEV generation**. The DEV-baseline and Train notebooks embed it "
        "with its SHA-256 and refuse to run if any embedded code or data differs from it.\n"
        "- It is rechecked at adapter freeze: every retained run records this file's SHA-256, and "
        "`phase2/ADAPTERS_FROZEN.md` and the FinalTest gate require it.\n"
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
