"""D021 T4 training-feasibility smoke test for Qwen3-4B QLoRA (no TRL).

Model-free parts (family selection, arm construction, schedule, summaries and
the go/no-go rule) use the standard library only. GPU commands import torch,
transformers, bitsandbytes and PEFT lazily, so the unit tests never need them.

Every GPU phase runs in its own process, so the reload after update 4 starts
from a new model load with nothing left in memory from the saving process:

  python3 t4_smoke/train_smoke.py preflight --data smoke_data.json --out OUT
  python3 t4_smoke/train_smoke.py run --phase first  --arm EE --data smoke_data.json --out OUT
  python3 t4_smoke/train_smoke.py run --phase resume --arm EE --data smoke_data.json --out OUT
  python3 t4_smoke/train_smoke.py run --phase probe  --arm EC --data smoke_data.json --out OUT
  python3 t4_smoke/train_smoke.py decide --out OUT

Smoke-trained adapters are engineering artifacts: never evaluate them or
report their answers as evidence of a research effect.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

try:
    from .labels import assert_matched_targets, build_example
    from .protocol import INSTRUCTION
except ImportError:  # run as a script: python3 t4_smoke/train_smoke.py
    from labels import assert_matched_targets, build_example
    from protocol import INSTRUCTION

MODEL_ID = "Qwen/Qwen3-4B"
# Immutable revision used by the verified T4 inference runs (docs/PROJECT_STATUS.md).
MODEL_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
# D021 stack. Colab supplies torch; it is recorded and checked, never reinstalled.
TORCH_BUILD = "2.11.0+cu130"
PINS = {
    "transformers": "4.51.3", "bitsandbytes": "0.50.2", "peft": "0.15.2",
    "accelerate": "1.6.0", "huggingface-hub": "0.30.2", "tokenizers": "0.21.1",
    "safetensors": "0.5.3", "nvidia-ml-py": "12.570.86",
}
RECORDED = ("torch", "numpy", "psutil")

# Frozen TRAIN files (phase2/TRAIN_DEV_FROZEN.md). Nothing else is ever read.
TRAIN_FILES = {
    "phase2/train_A.v2.json": "b9656a8c41af2a795bce9c131efc6a5efc652df78368d14fb7720fd985883666",
    "phase2/train_B.v2.json": "c975fe12459df6160effc5aeb0087f94666ba0b49778c3d827a67bb923ff35bd",
}
TRAIN_ROLE = "CONFIRM_TRAIN"
SELECTION_SEED = "D021-smoke-2026-10-27"
PER_FILE = 8
SELECTION_RULE = (
    "From each frozen TRAIN file (hash-checked), rank families by "
    "sha256('D021-smoke-2026-10-27:' + family_id) as hex ascending and keep the first 8; "
    "the 16 families are then ordered by family_id. Every family must have split_role "
    "CONFIRM_TRAIN. No other file is read."
)
ARMS = {"EE": "E", "ER": "R", "EC": "C"}  # second rendering per family; the first is always E
PROBE_ARM = "EC"

RECIPE = {
    "model": MODEL_ID, "model_revision": MODEL_REVISION, "seed": 11,
    "sequence_length": 1024, "families": 16, "forms_per_arm": 2,
    "microbatch": 1, "accumulation": 16, "updates": 6,
    "measurement_warmup_updates": 2, "resume_after_update": 4, "probe_updates": 32,
    "rank": 16, "alpha": 32, "dropout": 0.05,
    "targets": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "trainable_parameters": 33030144, "quantized_linear_modules": 252,
    "quantization": "nf4", "double_quantization": True,
    "compute_dtype": "float16", "adapter_dtype": "float32",
    "optimizer": "torch.optim.AdamW", "optimizer_dtype": "float32",
    "lr": 1e-4, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0,
    "clip": 1.0, "lr_schedule": "constant_smoke_only", "grad_scaler_init_scale": 65536.0,
    "attention": "sdpa_math_only", "gradient_checkpointing": "non_reentrant",
    "use_cache": False, "thinking": False, "packing": False,
    "loss_reduction": "mean over each example's supervised tokens, divided by accumulation (examples weighted equally)",
    "data_order": "per family in family_id order: E, then the arm's second form; cyclic over the 32 examples",
    "probe_atol": 1e-3, "probe_rtol": 1e-3,
}
THRESHOLDS = {"colab_max_seconds": 56.0, "kaggle_max_seconds": 150.0, "min_headroom_bytes": 2 * 1024**3}
DECISIONS = {
    "COLAB": "GO: stay on Colab T4 (median <= 56 s/update for every arm)",
    "KAGGLE_2xT4": "GO on Kaggle 2xT4: two independent single-GPU runs (56-150 s/update)",
    "FALLBACK_QWEN3_1_7B": "NO-GO for Qwen3-4B: fall back to Qwen3-1.7B, pre-declared in D021 (>150 s/update)",
    "NO_GO_INTEGRITY": "NO-GO: an integrity gate failed; see failed_checks (one fix attempt, then the D021 fallback)",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


# ---------------------------------------------------------------- data and arms

def load_train_sources(root):
    """Read only the two frozen TRAIN files, as (relative name, raw bytes)."""
    return [(name, (Path(root) / name).read_bytes()) for name in sorted(TRAIN_FILES)]


def rank_key(family_id, seed=SELECTION_SEED):
    return sha256(f"{seed}:{family_id}".encode("utf-8"))


def select_families(sources, *, expected=TRAIN_FILES, seed=SELECTION_SEED, per_file=PER_FILE):
    """Apply the fixed selection rule to hash-checked TRAIN sources."""
    require(sorted(name for name, _ in sources) == sorted(expected), "Selection needs exactly the frozen TRAIN files")
    selected = []
    for name, raw in sorted(sources):
        require(sha256(raw) == expected[name], f"{name} does not match its frozen SHA-256")
        families = json.loads(raw)
        require(isinstance(families, list) and len(families) >= per_file, f"{name}: too few families")
        for family in families:
            require(family.get("split_role") == TRAIN_ROLE, f"{family.get('family_id')}: not a TRAIN family")
            require(set(family["forms"]) >= {"E", "R", "C"}, f"{family['family_id']}: missing E/R/C")
        ranked = sorted(families, key=lambda family: rank_key(family["family_id"], seed))
        selected += [slim(family, name) for family in ranked[:per_file]]
    identities = [identity for family in selected for identity in (family["family_id"], family["source_family_id"])]
    require(len(identities) == len(set(identities)), "Repeated family identity in the selection")
    return sorted(selected, key=lambda family: family["family_id"])


def slim(family, source):
    """Keep only what training needs: renderings and the shared English solution."""
    completion = family["reference_solution_en"]
    require(isinstance(completion, str) and completion.strip(), f"{family['family_id']}: empty English solution")
    return {
        "family_id": family["family_id"], "source_family_id": family["source_family_id"],
        "template_group_id": family["template_group_id"], "topic": family["topic"],
        "split_role": family["split_role"], "version": family["version"], "source_file": source,
        "completion": completion,
        "forms": {form: family["forms"][form]["text"] for form in ("E", "R", "C")},
        "rendering_ids": {form: family["forms"][form]["rendering_id"] for form in ("E", "R", "C")},
    }


def smoke_dataset(root):
    sources = load_train_sources(root)
    families = select_families(sources)
    data = {
        "schema": "d021-smoke-data-1", "purpose": "T4 training-feasibility smoke only; not evaluation data",
        "selection_rule": SELECTION_RULE, "selection_seed": SELECTION_SEED,
        "sources": {name: sha256(raw) for name, raw in sources}, "families": families,
    }
    data["families_sha256"] = digest(families)
    return data


def validate_dataset(data):
    families = data["families"]
    require(len(families) == RECIPE["families"], "Exactly 16 smoke families required")
    require(data["families_sha256"] == digest(families), "Smoke data changed after selection")
    require(data["sources"] == TRAIN_FILES, "Smoke data must come from the frozen TRAIN files only")
    for family in families:
        require(family["split_role"] == TRAIN_ROLE and family["source_file"] in TRAIN_FILES, "Non-TRAIN family")
    return families


def arm_sequence(families, arm):
    """One matched exposure cycle: (family_id, form) per microbatch."""
    second = ARMS[arm]
    return [(family["family_id"], form) for family in families for form in ("E", second)]


def update_cursors(update, accumulation=RECIPE["accumulation"]):
    """Global microbatch cursor positions used by 1-based ``update``."""
    require(update >= 1, "Updates are 1-based")
    return list(range((update - 1) * accumulation, update * accumulation))


def build_examples(tokenizer, families, *, max_length=RECIPE["sequence_length"]):
    """Labelled E/R/C examples per family; targets asserted identical across forms."""
    special = [token for token in getattr(tokenizer, "all_special_tokens", []) if token]
    examples = {}
    for family in families:
        for text in [family["completion"], *family["forms"].values()]:
            require(not any(token in text for token in special), f"{family['family_id']}: literal special token")
        built = {
            form: build_example(tokenizer, INSTRUCTION, family["forms"][form], family["completion"], max_length=max_length)
            for form in ("E", "R", "C")
        }
        assert_matched_targets(built)
        examples[family["family_id"]] = built
    return examples


def arm_examples(examples, families, arm):
    return [dict(examples[family_id][form], family_id=family_id, form=form)
            for family_id, form in arm_sequence(families, arm)]


def mask_audit(tokenizer, examples, families):
    """Decode supervised spans and prompt endings; returns a JSON-safe report."""
    think = "<think>\n\n</think>\n\n"
    rows, failures = [], []
    for family in families:
        family_id = family["family_id"]
        for form, example in examples[family_id].items():
            boundary = example["boundary_index"]
            target = example["labels"][boundary:]
            prompt_text = tokenizer.decode(example["input_ids"][:boundary])
            target_text = tokenizer.decode(target)
            row = {
                "family_id": family_id, "form": form, "input_tokens": len(example["input_ids"]),
                "prompt_tokens": boundary, "supervised_tokens": len(target),
                "prompt_masked": example["labels"][:boundary] == [-100] * boundary,
                "prompt_ends_with_empty_think": prompt_text.endswith(think),
                "target_decodes_to_solution": target_text == family["completion"] + "<|im_end|>",
                "target_sha256": digest(target),
            }
            row["joint_tokenization_roundtrip"] = tokenizer.encode(
                tokenizer.decode(example["input_ids"]), add_special_tokens=False, truncation=False) == example["input_ids"]
            rows.append(row)
            for check in ("prompt_masked", "prompt_ends_with_empty_think", "target_decodes_to_solution"):
                if not row[check]:
                    failures.append(f"{family_id}-{form}: {check}")
    arms = {}
    for arm in ARMS:
        sequence = arm_examples(examples, families, arm)
        arms[arm] = {"examples": len(sequence), "input_tokens_per_cycle": sum(len(e["input_ids"]) for e in sequence),
                     "supervised_tokens_per_cycle": sum(len(e["labels"]) - e["boundary_index"] for e in sequence)}
    return {"passed": not failures, "failures": failures, "rows": rows, "arms": arms,
            "max_input_tokens": max(row["input_tokens"] for row in rows),
            "note": "joint_tokenization_roundtrip is informational: training uses separately encoded prompt and target"}


# ---------------------------------------------------------------- summaries and decision

def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def json_float(value):
    """JSON-safe float: non-finite values become 'nan'/'inf' strings, which finite() rejects."""
    value = float(value)
    return value if math.isfinite(value) else str(value)


def summarize_updates(updates, *, warmup=RECIPE["measurement_warmup_updates"],
                      resume_after=RECIPE["resume_after_update"]):
    """Summarize per-update records from one or more phase reports."""
    ordered = sorted(updates, key=lambda record: record["update"])
    timed = [record["seconds"] for record in ordered if record["update"] > warmup]
    return {
        "updates": [record["update"] for record in ordered],
        "median_seconds": statistics.median(timed) if timed else None,
        "timed_updates": [record["update"] for record in ordered if record["update"] > warmup],
        "losses_finite": all(finite(loss) for record in ordered for loss in record["microbatch_losses"]),
        "scaler_skips": sum(record["skipped"] for record in ordered),
        "scaler_skips_after_resume_point": sum(record["skipped"] for record in ordered if record["update"] > resume_after),
        "grad_norms_finite_after_resume_point": all(
            finite(record["grad_norm"]) for record in ordered if record["update"] > resume_after),
        "min_free_bytes": min((record["min_free_bytes"] for record in ordered), default=None),
        "peak_allocated_bytes": max((record["peak_allocated_bytes"] for record in ordered), default=None),
        "peak_reserved_bytes": max((record["peak_reserved_bytes"] for record in ordered), default=None),
        "input_tokens_per_update": [record["input_tokens"] for record in ordered],
        "supervised_tokens_per_update": [record["supervised_tokens"] for record in ordered],
    }


def summarize_arm(first, resume):
    """Combine the saving and the reloaded phase of one arm."""
    reports = [report for report in (first, resume) if report is not None]
    summary = summarize_updates([record for report in reports for record in report.get("updates", [])])
    summary.update(
        complete=all(report is not None and report.get("status") == "COMPLETE" for report in (first, resume)),
        oom=any(report.get("oom") for report in reports),
        reload_ok=bool(resume and resume.get("reload_check", {}).get("passed")),
        min_free_bytes=min([value for value in [summary["min_free_bytes"],
                            *(report.get("load_min_free_bytes") for report in reports)] if value is not None],
                           default=None),
    )
    return summary


def summarize_probe(report):
    summary = summarize_updates(report.get("updates", []) if report else [])
    summary.update(complete=bool(report and report.get("status") == "COMPLETE"
                                 and summary["updates"] == list(range(1, RECIPE["probe_updates"] + 1))),
                   oom=bool(report and report.get("oom")))
    return summary


def decide(arms, probe, *, preflight_passed, paired_initialization=True, thresholds=THRESHOLDS):
    """Apply the D021 go/no-go rule. ``arms`` maps EE/ER/EC to summarize_arm output."""
    failed = []
    if not preflight_passed:
        failed.append("preflight: mask/target audit did not pass")
    if not paired_initialization:
        failed.append("paired design: initial adapters differ across arms or were not recorded")
    for arm in ARMS:
        summary = arms.get(arm)
        if summary is None:
            failed.append(f"{arm}: no results")
            continue
        failed += [f"{arm}: {message}" for message in integrity_failures(summary, thresholds)]
        if summary.get("updates") != list(range(1, RECIPE["updates"] + 1)):
            failed.append(f"{arm}: did not record updates 1-{RECIPE['updates']}")
        if not summary.get("reload_ok"):
            failed.append(f"{arm}: reloaded state or probe did not match the saved state")
    failed += [f"probe {PROBE_ARM}: {message}" for message in integrity_failures(probe or {}, thresholds)]
    medians = {arm: (arms.get(arm) or {}).get("median_seconds") for arm in ARMS}
    timed = [value for value in medians.values() if finite(value)]
    worst = max(timed) if len(timed) == len(ARMS) else None
    if worst is None:
        tier = None
        failed.append("timing: a median is missing for at least one arm")
    elif worst <= thresholds["colab_max_seconds"]:
        tier = "COLAB"
    elif worst <= thresholds["kaggle_max_seconds"]:
        tier = "KAGGLE_2xT4"
    else:
        tier = "FALLBACK_QWEN3_1_7B"
    decision = tier if tier == "FALLBACK_QWEN3_1_7B" or not failed else "NO_GO_INTEGRITY"
    return {"decision": decision, "message": DECISIONS[decision], "time_tier": tier,
            "worst_median_seconds": worst, "median_seconds": medians, "failed_checks": failed,
            "thresholds": thresholds,
            "projected_hours_2304_updates_x1.4": (
                round(3 * 256 * sum(medians.values()) / 3600 * 1.4, 2) if worst is not None else None),
            "rule": "D021: worst-arm median over timed updates 3-6; <=56 Colab, 56-150 Kaggle 2xT4, >150 Qwen3-1.7B; "
                    "plus no OOM, >=2 GiB minimum free device memory, finite losses, no scaler skips after update 4, "
                    "reload state/probe within atol=rtol=1e-3, complete 32-update E+C probe"}


def integrity_failures(summary, thresholds=THRESHOLDS):
    failures = []
    if not summary.get("complete"):
        failures.append("incomplete run")
    if summary.get("oom"):
        failures.append("CUDA out of memory")
    free = summary.get("min_free_bytes")
    if free is None or free < thresholds["min_headroom_bytes"]:
        failures.append(f"minimum free device memory {free} below {thresholds['min_headroom_bytes']} bytes")
    if not summary.get("losses_finite"):
        failures.append("non-finite loss")
    if summary.get("scaler_skips_after_resume_point", 1) != 0:
        failures.append("GradScaler skipped an update after update 4")
    if not summary.get("grad_norms_finite_after_resume_point", False):
        failures.append("non-finite gradient norm after update 4")
    return failures


# ---------------------------------------------------------------- GPU runtime (lazy imports)

def versions():
    found = {}
    for name in (*PINS, *RECORDED):
        try:
            found[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            found[name] = None
    return found


def stack_mismatches(found):
    mismatches = [f"{name}=={pin} expected, found {found.get(name)}" for name, pin in PINS.items() if found.get(name) != pin]
    if found.get("torch") != TORCH_BUILD:
        mismatches.append(f"torch {TORCH_BUILD} expected (Colab build), found {found.get('torch')}")
    return mismatches


def gpu_setup(allow_stack_mismatch):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch
    require(torch.cuda.is_available(), "GPU required: Runtime > Change runtime type > T4 GPU")
    torch.cuda.set_device(0)
    name = torch.cuda.get_device_name(0)
    require("T4" in name and tuple(torch.cuda.get_device_capability(0)) == (7, 5), f"Tesla T4 required, found {name}")
    mismatches = stack_mismatches(versions())
    require(allow_stack_mismatch or not mismatches, "D021 stack mismatch: " + "; ".join(mismatches))
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_cudnn_sdp(False)
    torch.backends.cuda.enable_math_sdp(True)
    torch.use_deterministic_algorithms(True, warn_only=True)
    return torch, mismatches


def environment(torch, mismatches):
    properties = torch.cuda.get_device_properties(0)
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    driver = None
    try:
        import pynvml
        pynvml.nvmlInit()
        driver = pynvml.nvmlSystemGetDriverVersion()
        driver = driver.decode() if isinstance(driver, bytes) else driver
    except Exception:
        pass
    return {"python": platform.python_version(), "packages": versions(), "torch_cuda": torch.version.cuda,
            "gpu": properties.name, "gpu_total_bytes": properties.total_memory,
            "capability": list(torch.cuda.get_device_capability(0)), "driver": driver,
            "pip_freeze_sha256": sha256(freeze.encode()), "pip_freeze": freeze.splitlines(),
            "stack_mismatches": mismatches, "stack_matches_d021": not mismatches,
            "sdpa": {"flash": torch.backends.cuda.flash_sdp_enabled(),
                     "mem_efficient": torch.backends.cuda.mem_efficient_sdp_enabled(),
                     "math": torch.backends.cuda.math_sdp_enabled()},
            "deterministic_algorithms": "requested with warn_only=True"}


class MemorySampler:
    """Background NVML sampling of whole-device free memory (~4 Hz)."""

    def __init__(self, interval=0.25):
        self.interval, self.minimum, self.samples = interval, None, 0
        self.lock, self.stop_event, self.thread, self.error = threading.Lock(), threading.Event(), None, None
        try:
            import pynvml
            pynvml.nvmlInit()
            self.pynvml, self.handle = pynvml, pynvml.nvmlDeviceGetHandleByIndex(torch_device_index())
        except Exception as error:  # recorded, the per-microbatch torch samples remain
            self.pynvml, self.error = None, f"{type(error).__name__}: {error}"

    def start(self):
        if self.pynvml:
            self.thread = threading.Thread(target=self.loop, daemon=True)
            self.thread.start()
        return self

    def loop(self):
        while not self.stop_event.is_set():
            free = self.pynvml.nvmlDeviceGetMemoryInfo(self.handle).free
            with self.lock:
                self.samples += 1
                self.minimum = free if self.minimum is None else min(self.minimum, free)
            self.stop_event.wait(self.interval)

    def take(self):
        """Return and reset the minimum since the previous call."""
        with self.lock:
            value, self.minimum = self.minimum, None
        return value

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()


def torch_device_index():
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")[0].strip()
    return int(visible) if visible.isdigit() else 0


def seed_everything(torch, seed):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def hf_token():
    return os.environ.get("HF_TOKEN") or None


def load_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION, trust_remote_code=False, token=hf_token())


def load_model(torch):
    """Fresh NF4 base model plus a seeded fp32 LoRA adapter; returns (model, facts)."""
    import bitsandbytes
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    start = time.perf_counter()
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                               bnb_4bit_compute_dtype=torch.float16)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, trust_remote_code=False, torch_dtype=torch.float16,
        quantization_config=quant, device_map={"": 0}, attn_implementation="sdpa", low_cpu_mem_usage=True,
        token=hf_token())
    require(model.config.model_type == "qwen3", "Unexpected architecture")
    require(all(str(device) in ("0", "cuda:0") for device in model.hf_device_map.values()), "CPU/disk offload forbidden")
    quantized = sum(isinstance(module, bitsandbytes.nn.Linear4bit) for module in model.modules())
    require(quantized == RECIPE["quantized_linear_modules"], f"Expected 252 NF4 linear modules, found {quantized}")
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
                                            gradient_checkpointing_kwargs={"use_reentrant": False})
    seed_everything(torch, RECIPE["seed"])  # identical adapter initialization in every arm and phase
    lora = LoraConfig(r=RECIPE["rank"], lora_alpha=RECIPE["alpha"], lora_dropout=RECIPE["dropout"],
                      target_modules=RECIPE["targets"], bias="none", task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)
    for _, parameter in model.named_parameters():
        if parameter.requires_grad and parameter.dtype != torch.float32:
            parameter.data = parameter.data.float()
    trainable = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
    count = sum(parameter.numel() for _, parameter in trainable)
    require(count == RECIPE["trainable_parameters"], f"Expected 33,030,144 trainable parameters, found {count}")
    require(all("lora_" in name and parameter.dtype == torch.float32 for name, parameter in trainable),
            "Only fp32 LoRA parameters may train")
    model.config.use_cache = False
    model.train()
    inner = model.get_base_model().model
    checkpoint = getattr(inner, "_gradient_checkpointing_func", None)
    keywords = dict(getattr(checkpoint, "keywords", {}) or {})
    require(getattr(inner, "gradient_checkpointing", False), "Gradient checkpointing is not active")
    require(keywords.get("use_reentrant") is False, f"Checkpointing must be non-reentrant, found {keywords}")
    import inspect
    keep = "logits_to_keep" in inspect.signature(type(model.get_base_model()).forward).parameters
    torch.cuda.synchronize()
    embedding = model.get_base_model().get_input_embeddings().weight
    facts = {"load_seconds": time.perf_counter() - start, "quantized_linear_modules": quantized,
             "trainable_parameters": count, "embedding_dtype": str(embedding.dtype),
             "lm_head_dtype": str(model.get_base_model().lm_head.weight.dtype),
             "tied_embeddings": model.get_base_model().lm_head.weight.data_ptr() == embedding.data_ptr(),
             "gradient_checkpointing_kwargs": {key: str(value) for key, value in keywords.items()},
             "loss_logits": "logits_to_keep (supervised positions only)" if keep else "full logits sliced",
             "model_memory_bytes": model.get_memory_footprint()}
    return model, trainable, keep, facts


def tensor_bytes(tensor):
    import torch
    return tensor.detach().cpu().contiguous().view(-1).view(torch.uint8).numpy().tobytes()


def tensors_digest(named):
    checksum = hashlib.sha256()
    for name, tensor in named:
        checksum.update(f"{name}|{tensor.dtype}|{tuple(tensor.shape)}|".encode())
        checksum.update(tensor_bytes(tensor))
    return checksum.hexdigest()


def optimizer_tensors(state_dict):
    state = state_dict["state"]
    return [(f"{index}.{key}", value) for index in sorted(state) for key, value in sorted(state[index].items())
            if hasattr(value, "dtype")]


def state_digests(torch, trainable, optimizer, scaler):
    return {"adapter": tensors_digest(trainable), "optimizer": tensors_digest(optimizer_tensors(optimizer.state_dict())),
            "optimizer_groups": digest(optimizer.state_dict()["param_groups"]), "scaler": digest(scaler.state_dict()),
            "rng_python": digest(list_state(random.getstate())),
            "rng_torch": sha256(torch.get_rng_state().numpy().tobytes()),
            "rng_cuda": sha256(torch.cuda.get_rng_state().numpy().tobytes())}


def list_state(state):
    return [state[0], list(state[1]), state[2]]


class Trainer:
    def __init__(self, torch, model, trainable, keep, sequence, sampler):
        self.torch, self.model, self.keep, self.sequence, self.sampler = torch, model, keep, sequence, sampler
        self.trainable = trainable
        self.parameters = [parameter for _, parameter in trainable]
        self.optimizer = torch.optim.AdamW(self.parameters, lr=RECIPE["lr"], betas=tuple(RECIPE["betas"]),
                                           eps=RECIPE["eps"], weight_decay=RECIPE["weight_decay"])
        require({id(p) for group in self.optimizer.param_groups for p in group["params"]} == {id(p) for p in self.parameters},
                "Optimizer membership must equal the adapter set")
        self.scaler = torch.amp.GradScaler("cuda", init_scale=RECIPE["grad_scaler_init_scale"])
        self.cursor = 0

    def logits(self, example):
        torch = self.torch
        ids = torch.tensor([example["input_ids"]], device="cuda")
        boundary = example["boundary_index"]
        supervised = len(example["input_ids"]) - boundary
        with torch.autocast("cuda", dtype=torch.float16):
            if self.keep:
                out = self.model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False,
                                 logits_to_keep=supervised + 1).logits[0, :-1]
            else:
                out = self.model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits[0, boundary - 1:-1]
        require(out.shape[0] == supervised, "Causal-shift slice has the wrong length")
        return out

    def loss(self, example):
        torch = self.torch
        targets = torch.tensor(example["input_ids"][example["boundary_index"]:], device="cuda")
        return torch.nn.functional.cross_entropy(self.logits(example).float(), targets, reduction="mean")

    def update(self, number):
        torch = self.torch
        require(self.cursor == update_cursors(number)[0], "Data cursor out of step with the update number")
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        self.sampler.take()
        scale_before = self.scaler.get_scale()
        start = time.perf_counter()
        losses, free, input_tokens, supervised_tokens, items = [], [], 0, 0, []
        for _ in range(RECIPE["accumulation"]):
            example = self.sequence[self.cursor % len(self.sequence)]
            loss = self.loss(example)
            self.scaler.scale(loss / RECIPE["accumulation"]).backward()
            losses.append(loss.detach())
            free.append(torch.cuda.mem_get_info()[0])
            input_tokens += len(example["input_ids"])
            supervised_tokens += len(example["input_ids"]) - example["boundary_index"]
            items.append(f"{example['family_id']}-{example['form']}")
            self.cursor += 1
        self.scaler.unscale_(self.optimizer)
        grad_norm = torch.nn.utils.clip_grad_norm_(self.parameters, RECIPE["clip"])
        self.scaler.step(self.optimizer)
        self.scaler.update()
        self.optimizer.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        nvml = self.sampler.take()
        scale_after = self.scaler.get_scale()
        record = {
            "update": number, "seconds": seconds, "microbatch_losses": [json_float(value) for value in torch.stack(losses).cpu()],
            "grad_norm": json_float(grad_norm), "scale_before": scale_before, "scale_after": scale_after,
            "skipped": scale_after < scale_before, "input_tokens": input_tokens, "supervised_tokens": supervised_tokens,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(), "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
            "min_free_torch_bytes": min(free), "min_free_nvml_bytes": nvml, "cursor_after": self.cursor, "items": items,
        }
        record["loss"] = json_float(sum(float(value) for value in record["microbatch_losses"]) / RECIPE["accumulation"])
        record["min_free_bytes"] = min(value for value in (record["min_free_torch_bytes"], nvml) if value is not None)
        print(f"update {number}: loss {record['loss']} grad_norm {record['grad_norm']} "
              f"scale {scale_before:g}->{scale_after:g} {seconds:.1f}s tokens {input_tokens} "
              f"min_free {record['min_free_bytes'] / 2**30:.2f} GiB", flush=True)
        return record

    def probe(self, example):
        """Fixed-input fp32 logits on the supervised positions, dropout off, no RNG use."""
        torch = self.torch
        self.model.eval()
        with torch.no_grad():
            values = self.logits(example).float().cpu()
        self.model.train()
        return values


def run_phase(arguments):
    torch, mismatches = gpu_setup(arguments.allow_stack_mismatch)
    phase, arm = arguments.phase, arguments.arm
    require(arm in ARMS, "Unknown arm")
    require(phase != "probe" or arm == PROBE_ARM, "The 32-update stability probe is for E+C only")
    out = Path(arguments.out) / arm
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / f"{phase}_report.json"
    data = read_json(arguments.data)
    families = validate_dataset(data)
    report = {"phase": phase, "arm": arm, "status": "STARTED", "oom": False, "recipe": RECIPE,
              "recipe_sha256": digest(RECIPE), "data_sha256": data["families_sha256"], "updates": [],
              "environment": environment(torch, mismatches)}
    sampler = MemorySampler().start()
    report["nvml_sampler_error"] = sampler.error
    try:
        tokenizer = load_tokenizer()
        sequence = arm_examples(build_examples(tokenizer, families), families, arm)
        seed_everything(torch, RECIPE["seed"])
        torch.cuda.reset_peak_memory_stats()
        model, trainable, keep, report["model"] = load_model(torch)
        report["load_min_free_bytes"] = min(value for value in (sampler.take(), torch.cuda.mem_get_info()[0])
                                            if value is not None)
        report["load_peak_reserved_bytes"] = torch.cuda.max_memory_reserved()
        report["initial_adapter_sha256"] = tensors_digest(trainable)
        trainer = Trainer(torch, model, trainable, keep, sequence, sampler)
        probe_example = sequence[0]  # first family's E rendering: identical in every arm
        checkpoint = out / "checkpoint"
        if phase == "first":
            first, last = 1, RECIPE["resume_after_update"]
        elif phase == "resume":
            first, last = RECIPE["resume_after_update"] + 1, RECIPE["updates"]
            restore(torch, trainer, checkpoint, report)
        else:
            first, last = 1, RECIPE["probe_updates"]
        for number in range(first, last + 1):
            report["updates"].append(trainer.update(number))
            write_json(report_path, report)
        if phase == "first":
            save(torch, trainer, checkpoint, probe_example, report)
        report["status"] = "COMPLETE"
    except Exception as error:
        report["status"] = "FAILED"
        report["oom"] = isinstance(error, torch.cuda.OutOfMemoryError) or "out of memory" in str(error).lower()
        report["error"] = traceback.format_exc()
        print(report["error"], file=sys.stderr, flush=True)
    finally:
        sampler.stop()
        report["nvml_samples"] = sampler.samples
        report["summary"] = summarize_updates(report["updates"])
        write_json(report_path, report)
    print(f"{arm} {phase}: {report['status']}", flush=True)
    return 0 if report["status"] == "COMPLETE" else 1


def save(torch, trainer, folder, probe_example, report):
    folder.mkdir(parents=True, exist_ok=True)
    probe = trainer.probe(probe_example)
    trainer.model.save_pretrained(folder / "adapter")
    state = {"adapter": {name: parameter.detach().cpu().clone() for name, parameter in trainer.trainable},
             "optimizer": trainer.optimizer.state_dict(), "scaler": trainer.scaler.state_dict(),
             "rng_torch": torch.get_rng_state(), "rng_cuda": torch.cuda.get_rng_state(), "probe_logits": probe}
    torch.save(state, folder / "state.pt")
    meta = {"cursor": trainer.cursor, "completed_updates": RECIPE["resume_after_update"],
            "rng_python": list_state(random.getstate()), "recipe_sha256": digest(RECIPE),
            "data_sha256": report["data_sha256"], "parameter_names": [name for name, _ in trainer.trainable],
            "probe_item": f"{probe_example['family_id']}-{probe_example['form']}",
            "digests": state_digests(torch, trainer.trainable, trainer.optimizer, trainer.scaler)}
    write_json(folder / "meta.json", meta)
    report["checkpoint"] = {"state_sha256": file_sha256(folder / "state.pt"), "meta": meta["digests"],
                            "cursor": trainer.cursor}


def restore(torch, trainer, folder, report):
    """Load the saved state into a freshly loaded model and verify it."""
    meta = read_json(folder / "meta.json")
    require(meta["recipe_sha256"] == digest(RECIPE) and meta["data_sha256"] == report["data_sha256"],
            "Checkpoint was made with a different recipe or data")
    require(meta["parameter_names"] == [name for name, _ in trainer.trainable], "Adapter parameter order changed")
    state = torch.load(folder / "state.pt", map_location="cpu", weights_only=True)
    with torch.no_grad():
        for name, parameter in trainer.trainable:
            parameter.copy_(state["adapter"][name].to(parameter.device))
    trainer.optimizer.load_state_dict(state["optimizer"])
    trainer.scaler.load_state_dict(state["scaler"])
    trainer.cursor = meta["cursor"]
    version, internal, gauss = meta["rng_python"]
    random.setstate((version, tuple(internal), gauss))
    torch.set_rng_state(state["rng_torch"])
    torch.cuda.set_rng_state(state["rng_cuda"])
    live = state_digests(torch, trainer.trainable, trainer.optimizer, trainer.scaler)
    tolerance = {"atol": RECIPE["probe_atol"], "rtol": RECIPE["probe_rtol"]}
    saved_optimizer = dict(optimizer_tensors(state["optimizer"]))
    close = {
        "adapter": all(torch.allclose(parameter.detach().cpu(), state["adapter"][name], **tolerance)
                       for name, parameter in trainer.trainable),
        "optimizer": all(torch.allclose(value.detach().cpu().float(), saved_optimizer[name].float(), **tolerance)
                         for name, value in optimizer_tensors(trainer.optimizer.state_dict())),
        "scaler": trainer.scaler.state_dict() == state["scaler"],
        "rng": live["rng_torch"] == meta["digests"]["rng_torch"] and live["rng_cuda"] == meta["digests"]["rng_cuda"]
               and live["rng_python"] == meta["digests"]["rng_python"],
        "cursor": trainer.cursor == update_cursors(RECIPE["resume_after_update"] + 1)[0],
    }
    probe = trainer.probe(trainer.sequence[0])
    saved_probe = state["probe_logits"]
    close["probe"] = probe.shape == saved_probe.shape and torch.allclose(probe, saved_probe, **tolerance)
    result = {"allclose": close, "exact_digests": {key: live[key] == meta["digests"][key] for key in live},
              "probe_max_abs_diff": json_float((probe - saved_probe).abs().max()) if probe.shape == saved_probe.shape else None,
              "tolerance": tolerance, "checkpoint_state_sha256": file_sha256(folder / "state.pt")}
    result["passed"] = all(close.values())
    report["reload_check"] = result
    print("reload check:", json.dumps(result["allclose"]), "probe max abs diff", result["probe_max_abs_diff"], flush=True)
    require(result["passed"], "Reloaded state does not match the saved state: " + json.dumps(close))
    return result


def file_sha256(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            checksum.update(block)
    return checksum.hexdigest()


def run_preflight(arguments):
    torch, mismatches = gpu_setup(arguments.allow_stack_mismatch)
    data = read_json(arguments.data)
    families = validate_dataset(data)
    report = {"status": "STARTED", "environment": environment(torch, mismatches), "recipe": RECIPE,
              "recipe_sha256": digest(RECIPE), "data_sha256": data["families_sha256"],
              "selection_rule": data["selection_rule"], "families": [family["family_id"] for family in families]}
    try:
        tokenizer = load_tokenizer()
        report["chat_template_sha256"] = digest(tokenizer.chat_template)
        report["im_end_id"] = tokenizer.convert_tokens_to_ids("<|im_end|>")
        examples = build_examples(tokenizer, families)
        report["mask_audit"] = mask_audit(tokenizer, examples, families)
        last_ok = all(example["labels"][-1] == report["im_end_id"] for built in examples.values() for example in built.values())
        report["mask_audit"]["last_target_is_im_end"] = last_ok
        report["passed"] = report["mask_audit"]["passed"] and last_ok
        report["status"] = "COMPLETE"
    except Exception:
        report.update(status="FAILED", passed=False, error=traceback.format_exc())
        print(report["error"], file=sys.stderr, flush=True)
    write_json(Path(arguments.out) / "preflight_report.json", report)
    print("preflight:", report["status"], "mask audit passed:", report.get("passed"), flush=True)
    return 0 if report.get("passed") else 1


def run_decide(arguments):
    out = Path(arguments.out)

    def load(path):
        return read_json(path) if path.exists() else None

    preflight = load(out / "preflight_report.json")
    arms = {arm: summarize_arm(load(out / arm / "first_report.json"), load(out / arm / "resume_report.json"))
            for arm in ARMS}
    probe = summarize_probe(load(out / PROBE_ARM / "probe_report.json"))
    initial = {(load(out / arm / phase) or {}).get("initial_adapter_sha256")
               for arm in ARMS for phase in ("first_report.json", "resume_report.json")}
    initial |= {(load(out / PROBE_ARM / "probe_report.json") or {}).get("initial_adapter_sha256")}
    paired = len(initial - {None}) == 1
    result = decide(arms, probe, preflight_passed=bool(preflight and preflight.get("passed")),
                    paired_initialization=paired)
    result.update(arms=arms, probe=probe, initial_adapter_sha256=sorted(initial - {None}),
                  stack_matches_d021=bool(preflight and preflight["environment"]["stack_matches_d021"]))
    write_json(out / "decision.json", result)
    print(json.dumps({key: result[key] for key in ("decision", "message", "worst_median_seconds", "median_seconds",
                                                   "failed_checks", "stack_matches_d021")}, indent=2))
    for arm, summary in arms.items():
        print(f"{arm}: median {summary['median_seconds']} s/update; peak reserved {summary['peak_reserved_bytes']}; "
              f"min free {summary['min_free_bytes']}; tokens/update {summary['input_tokens_per_update']}")
    print(f"probe {PROBE_ARM}: median {probe['median_seconds']} s/update over {len(probe['updates'])} updates; "
          f"skips {probe['scaler_skips']}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="D021 T4 QLoRA training-feasibility smoke test")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "run"):
        command = commands.add_parser(name)
        command.add_argument("--data", type=Path, required=True)
        command.add_argument("--out", type=Path, required=True)
        command.add_argument("--allow-stack-mismatch", action="store_true",
                             help="Record but do not stop on a stack that differs from D021")
    commands.choices["run"].add_argument("--arm", choices=sorted(ARMS), required=True)
    commands.choices["run"].add_argument("--phase", choices=("first", "resume", "probe"), required=True)
    decide_command = commands.add_parser("decide")
    decide_command.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args(argv)
    handler = {"preflight": run_preflight, "run": run_phase, "decide": run_decide}[arguments.command]
    return handler(arguments)


if __name__ == "__main__":
    sys.exit(main())
