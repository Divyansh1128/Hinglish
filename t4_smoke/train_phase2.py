"""Phase-2 QLoRA training for Qwen3-4B (D043; binding plan phase2/PREREGISTRATION.md §3 with Amendments 1-3).

Reuses the GPU-verified D021 smoke code (train_smoke.py: labels, model load, digests, memory sampler) without
modifying it. New here: the frozen exposure order (Amendment 1 item 9), the learning-rate schedule, the run seed,
the numerical-failure contract and pinned GradScaler (item 10), failure classes and the append-only attempt log
with the seed/reserve plan (item 11; typed classes per Amendment 2 item 2), checkpoints and the final adapter.

  python3 t4_smoke/train_phase2.py exposure-order --root . [--check]     # write / verify phase2/EXPOSURE_ORDER.json
  python3 t4_smoke/train_phase2.py train --train-root TRAIN_ROOT --inputs INPUTS_DIR --baseline-dir BASELINE_DIR \
      [--arm EC --seed 11 --slot 11 --attempt 1]   # the plan chooses the run; the optional four only assert it
  python3 t4_smoke/train_phase2.py train ... --resume      # engineering only: a resumed run is never valid (item 11)
  python3 t4_smoke/train_phase2.py train ... --recover-stale-writer  # only after confirming no other session runs
  python3 t4_smoke/train_phase2.py plan --train-root TRAIN_ROOT       # attempt log, seed slots, reserves, next run
  python3 t4_smoke/train_phase2.py pairing --train-root TRAIN_ROOT

INPUTS_DIR holds IMPLEMENTATION_MANIFEST.md, EXPOSURE_ORDER.json and the two frozen TRAIN files (phase2/ in the
repository; inputs/ in the Train notebook). Before any attempt is opened the trainer consults the attempt plan
(Amendment 2 item 4), requires a complete unchanged-model DEV run under the same implementation manifest (item 6),
refuses a configuration or implementation that differs from earlier attempts (item 7) and refuses any stack other
than the exact §2 stack on a T4 (item 3). Inside the attempt it verifies the implementation manifest against the
running code, the TRAIN bytes against their frozen hashes and the exposure order against its frozen hash, then the
downloaded Hub tokenizer/config files and the loaded chat template against the manifest (Amendment 3 / B2); a
mismatch is a protocol failure. The baseline prerequisite validates the actual results ZIP: frozen DEV, registered
configuration, execution and environment, engine identity and exactly 120 resolved generations (Amendment 3 item 3).
One session at a time writes a training root (WRITER.lock with session ID and heartbeat; Amendment 3 item 2): an
attempt left open is never closed automatically, only by --recover-stale-writer after the operator's confirmation. Training never reads DEV or FINAL_TEST. Model-free parts use the standard library
only; torch, transformers, bitsandbytes and PEFT are imported lazily inside the GPU commands.
"""
import argparse
import contextlib
import hashlib
import json
import math
import os
import random
import re
import shutil
import socket
import sys
import threading
import time
import traceback
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import train_smoke as ts
except ImportError:  # run as a script: python3 t4_smoke/train_phase2.py
    import train_smoke as ts

ARMS = ts.ARMS  # EE/ER/EC -> second rendering; the first is always E
ARM_ORDER = ("EC", "ER", "EE")  # Amendment 2 item 4: arms within a slot run in this order
SLOTS = (11, 22, 33)  # original seeds; each is a slot that a reserve can take over (Amendment 1 item 11)
RESERVE_QUEUE = (44, 55)  # global queue; each reserve is used at most once, never reused
SEEDS, RESERVE_SEEDS = SLOTS, RESERVE_QUEUE
MAX_ATTEMPTS = 2  # per arm and seed: one from-scratch retry, infrastructure failures only
FAMILIES_PER_FILE = 80
ORDER_PREFIX = "phase2-D043"
ORDER_RULE = (
    "For seed s and pass p in {1,2,3}: sort the 160 TRAIN families ascending by the SHA-256 hex digest of the UTF-8 "
    "bytes of 'phase2-D043:{s}:{p}:{family_id}' (s and p in decimal, no quotes, no newline), ties broken by "
    "family_id; each family contributes its E example and then the arm's second example, consecutively; each update "
    "takes the next 16 examples (8 families, the effective content batch). Identical across arms within a seed "
    "(Amendment 1 item 9)."
)
SCHEDULE_RULE = "lr(u) = 1e-4*u/6 for u <= 6; otherwise 1e-4*[0.1 + 0.9*0.5*(1 + cos(pi*(u-6)/54))]; lr(60) = 1e-5"
# Amendment 1 item 10: frozen GradScaler settings. With 60 steps and growth interval 2000 the scale can only change
# on a skipped step, and any skip is a numerical failure.
SCALER = {"init_scale": 65536.0, "growth_factor": 2.0, "backoff_factor": 0.5, "growth_interval": 2000}
EXPOSURE_ORDER_PATH = "phase2/EXPOSURE_ORDER.json"
# Frozen hashes (Amendment 2 item 7): EXPOSURE_ORDER.json as committed in 535b1e9, and the 160 TRAIN families built
# from the two frozen TRAIN files (train_smoke.TRAIN_FILES) by phase2_dataset().
EXPOSURE_ORDER_SHA256 = "adf43e50c80c59ffa831071558785469b1eda89880c18eefb4f89a9adeb5afb6"
TRAIN_FAMILIES_SHA256 = "db1bee2ce2b41c12ae8ed600355a24d6dc8985ee1181c1e86e22ffc723a467fc"
EXPOSURE_SCHEMA = "phase2-exposure-order-1"
MANIFEST_NAME = "IMPLEMENTATION_MANIFEST.md"
MANIFEST_SCHEMA = "phase2-implementation-manifest-1"
TRAINER_CODE = ("train_phase2.py", "train_smoke.py", "labels.py", "protocol.py")  # what this process executes
# Amendment 2 item 6: the unchanged-model DEV run (Phase2_Baseline_DEV: STORE/baseline_dev/base) and its record.
BASELINE_RUN = "base"
BASELINE_RECORD = f"{BASELINE_RUN}_baseline_record.json"
BASELINE_SCHEMA = "phase2-baseline-dev-1"
BASELINE_PROMPTS = 120
BASELINE_MODE = "phase2_dev"
# Amendment 3 item 3 (B3): the frozen DEV inputs of that run as the engine digests them (hinglish_pilot.data.digest of
# the dataset and split manifest phase2_eval.inputs builds from the frozen DEV file). The trainer never reads DEV: it
# only compares a baseline archive with these; the tests and the manifest builder recompute them from the file.
DEV_DATASET_SHA256 = "83e83f67769fb122cf8b899d7e08a3b5a045695c6a6a806dd10f34b782e0be27"
DEV_SPLIT_SHA256 = "ac3e4a4620da80da6f0d599bb684476ee765c2ec2063c6757368f08665416964"
ENGINE_PREFIX = "test1_pilot/hinglish_pilot/"
# Members of a complete engine export (hinglish_pilot.report.export) besides source/*.py; a baseline ZIP must hold all.
BASELINE_MEMBERS = ("run_manifest.json", "environment.json", "experiment_config.json", "dataset_snapshot.jsonl",
                    "dataset.json", "split_manifest.json", "generation_attempts.jsonl", "predictions.csv",
                    "family_comparisons.csv", "metrics.json", "summary.md", "manual_audit.csv", "errors.jsonl",
                    "evaluation_order.json", "checksums.sha256")
# Files of Qwen/Qwen3-4B at the pinned revision (SHA-256 of the bytes served by the Hub at that revision, measured
# 3 Nov 2026; the tokenizer files also match the local Hub cache). Amendment 3 / B2: the trainer re-downloads and
# verifies them at its executable boundary, and compares the loaded chat template with CHAT_TEMPLATE.
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
# §2/§4 execution facts every Phase-2 engine archive records in run_manifest.json["backend"] and every session
# (Amendment 3 item 3); hinglish_pilot.hf_backend.HFBackend.metadata writes exactly these keys.
T4_CAPABILITY = [7, 5]
EXECUTION = {"backend": "huggingface", "gpu_verified": True, "attention": "sdpa with math kernel only",
             "compute_dtype": "float16"}
QUANTIZATION = {"load_in_4bit": True, "bnb_4bit_quant_type": "nf4", "bnb_4bit_use_double_quant": True,
                "bnb_4bit_compute_dtype": "float16"}
# Amendment 3 item 2 (B4): one writer per training root.
WRITER_LOCK = "WRITER.lock"
WRITER_SCHEMA = "phase2-writer-lock-1"
WRITER_RECOVERIES = "WRITER_RECOVERIES.jsonl"
HEARTBEAT_SECONDS = 30
FAILURE_CLASSES = ("infrastructure", "numerical", "protocol")
OUTCOMES = ("valid", "resumed_invalid") + FAILURE_CLASSES
EXIT_CODES = {"refused": 2, "infrastructure": 1, "numerical": 3, "protocol": 4}
ATTEMPT_LOG = "ATTEMPT_LOG.jsonl"
HALT_MESSAGE = ("THE STUDY HALTS (PREREGISTRATION Amendment 1 items 10-11, Amendment 2 item 2): this run is INVALID. "
                "No retry and no reserve seed. Send the ZIP; any repair needs a dated amendment before any further "
                "training.")

# D021 recipe (train_smoke.RECIPE) with the D043 schedule. Keys shared with the smoke recipe keep its values.
RECIPE = {key: value for key, value in ts.RECIPE.items()
          if key not in ("seed", "families", "updates", "measurement_warmup_updates", "resume_after_update",
                         "probe_updates", "lr_schedule", "data_order")}
RECIPE.update(
    study="phase2-D043", families=160, examples_per_arm=320, passes=3, updates_per_pass=20, updates=60,
    lr_schedule=SCHEDULE_RULE, warmup_updates=6, min_lr_ratio=0.1, data_order=ORDER_RULE,
    content_batch_families=8, exposure_order_file=EXPOSURE_ORDER_PATH,
    seeds=list(SLOTS), reserve_seeds=list(RESERVE_QUEUE), checkpoint_every=10,
    seeding="random, torch and CUDA seeded with the run seed before the adapter is created and before training",
    pairing_scope="pairing controls the initial adapter tensors and the exposure order, not dropout draws",
    grad_scaler=SCALER,
    valid_run=("exactly 60 accumulation windows and 60 successful optimizer steps over exactly 3 passes; lr(u) is set "
               "before step u; gradients are unscaled before clipping; any GradScaler skip, non-finite loss or "
               "gradient, or non-finite saved parameter is a numerical failure (Amendment 1 item 10)"),
    failure_policy="Amendment 1 item 11: infrastructure -> one from-scratch retry; numerical/protocol -> study halts",
    evaluated_checkpoint="adapter after update 60",
)


class NumericalFailure(Exception):
    """Amendment 1 item 10. ``record`` is the partial log of the failing update, if any."""

    def __init__(self, message, record=None):
        super().__init__(message)
        self.record = record


class ProtocolError(ValueError):
    """A hash, identity, label, data, exposure-order or step-count assertion failed (Amendment 2 item 2): the study
    halts. Subclasses ValueError so model-free callers that expect a refusal keep working."""


ProtocolFailure = ProtocolError  # earlier name


class InfrastructureFailure(Exception):
    """Base of the typed infrastructure failures raised by this module (Amendment 2 item 2)."""


class CheckpointWriteError(InfrastructureFailure):
    """Writing a checkpoint or the final adapter failed (Amendment 2 item 2: a failed checkpoint write)."""


class StudyHalted(Exception):
    """A numerical or protocol failure was logged: no further training, no reserve (Amendment 1 item 11)."""


class Refused(Exception):
    """The attempt plan, the baseline, the stack or the attempt history does not allow this training run; no attempt
    is opened and nothing is logged."""


def require(condition, message):
    """Protocol assertion: raises ProtocolError (the study halts if it fires inside an attempt)."""
    if not condition:
        raise ProtocolError(message)


protocol = require


@contextlib.contextmanager
def protocol_assertions(context):
    """Re-raise a plain ValueError/AssertionError from the reused smoke code (hash, label or data checks) as a
    ProtocolError at the point of detection; every other exception passes through unchanged."""
    try:
        yield
    except ProtocolError:
        raise
    except (ValueError, AssertionError) as error:
        raise ProtocolError(f"{context}: {error}") from error


def lr_at(update, *, peak=1e-4, warmup=6, total=60, floor=0.1):
    """Learning rate used by 1-based optimizer update ``update`` (§3)."""
    require(1 <= update <= total, f"Update must be in 1..{total}")
    if update <= warmup:
        return peak * update / warmup
    return peak * (floor + (1 - floor) * 0.5 * (1 + math.cos(math.pi * (update - warmup) / (total - warmup))))


# ---------------------------------------------------------------- data, order and arms (model-free)

def phase2_dataset(root):
    """All 160 frozen TRAIN families (hash-checked by train_smoke.select_families); nothing else is read."""
    sources = ts.load_train_sources(root)
    for name, raw in sources:
        require(len(json.loads(raw)) == FAMILIES_PER_FILE, f"{name}: expected {FAMILIES_PER_FILE} families")
    families = ts.select_families(sources, per_file=FAMILIES_PER_FILE)
    data = {"schema": "phase2-train-data-1", "purpose": "Phase-2 TRAIN (D043); all 160 families",
            "sources": {name: ts.sha256(raw) for name, raw in sources}, "families": families}
    data["families_sha256"] = ts.digest(families)
    return data


def validate_phase2_data(data):
    families = data["families"]
    require(len(families) == RECIPE["families"], "Exactly 160 TRAIN families required")
    require(data["families_sha256"] == ts.digest(families), "TRAIN data changed after it was built")
    require(data["sources"] == ts.TRAIN_FILES, "TRAIN data must come from the frozen TRAIN files only")
    require(len({family["family_id"] for family in families}) == len(families), "Duplicate family")
    for family in families:
        require(family["split_role"] == ts.TRAIN_ROLE and family["source_file"] in ts.TRAIN_FILES, "Non-TRAIN family")
    return families


def order_input(seed, number, family_id):
    """Exact hash input (Amendment 1 item 9): UTF-8 bytes, seed and pass in decimal, no quotes or newline."""
    require(type(seed) is int and seed >= 0, "Seed must be a non-negative int (decimal in the hash input)")
    require(type(number) is int and number >= 1, "Pass must be a positive int (decimal in the hash input)")
    require(isinstance(family_id, str) and family_id, "family_id must be a non-empty string")
    return f"{ORDER_PREFIX}:{seed:d}:{number:d}:{family_id}".encode("utf-8")


def order_key(seed, number, family_id):
    return ts.sha256(order_input(seed, number, family_id))


def pass_order(families, seed, number):
    """Family IDs for pass ``number`` (1-based) of ``seed``; ties on the hash are broken by family ID."""
    ids = [family["family_id"] if isinstance(family, dict) else family for family in families]
    return sorted(ids, key=lambda family_id: (order_key(seed, number, family_id), family_id))


def exposure_passes(families, seed):
    return [pass_order(families, seed, number) for number in range(1, RECIPE["passes"] + 1)]


def order_sha256(families, seed):
    """Arm-independent fingerprint of a seed's exposure list (equal across arms by construction)."""
    return ts.digest(exposure_passes(families, seed))


def exposure_document(data):
    """phase2/EXPOSURE_ORDER.json: the frozen per-seed exposure lists (originals and reserves)."""
    families = validate_phase2_data(data)
    seeds = {}
    for seed in SLOTS + RESERVE_QUEUE:
        passes = exposure_passes(families, seed)
        seeds[str(seed)] = {"role": "original" if seed in SLOTS else "reserve", "passes": passes,
                            "order_sha256": ts.digest(passes)}
    return {"schema": EXPOSURE_SCHEMA, "rule": ORDER_RULE,
            "hash_input": "UTF-8 bytes of phase2-D043:{s}:{p}:{family_id}; s and p in decimal; no quotes; no newline",
            "tie_break": "family_id ascending", "passes": RECIPE["passes"], "examples_per_window": RECIPE["accumulation"],
            "content_batch_families": RECIPE["content_batch_families"], "train_files": dict(ts.TRAIN_FILES),
            "families_sha256": data["families_sha256"],
            "order_sha256_definition": "train_smoke.digest(passes): SHA-256 of json.dumps(passes, sort_keys=True, "
                                       "ensure_ascii=False) in UTF-8", "seeds": seeds}


def exposure_text(data):
    return json.dumps(exposure_document(data), indent=1, ensure_ascii=False) + "\n"


def check_exposure(document, data, seed):
    """The frozen exposure list for ``seed`` must equal the recomputed one; returns its order_sha256."""
    families = data["families"]
    protocol(document.get("schema") == EXPOSURE_SCHEMA, "EXPOSURE_ORDER.json has the wrong schema")
    protocol(document.get("families_sha256") == data["families_sha256"], "EXPOSURE_ORDER.json is for other TRAIN data")
    entry = document.get("seeds", {}).get(str(seed))
    protocol(entry is not None, f"EXPOSURE_ORDER.json has no list for seed {seed}")
    passes = exposure_passes(families, seed)
    protocol(entry["passes"] == passes, f"Frozen exposure list for seed {seed} differs from the recomputed order")
    protocol(entry["order_sha256"] == ts.digest(passes), f"Exposure order hash for seed {seed} is wrong")
    return entry["order_sha256"]


# ---------------------------------------------------------------- authenticated inputs (Amendment 2 item 7; R4)

def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_verified_train(inputs):
    """The 160 TRAIN families built from the frozen TRAIN bytes in ``inputs`` (basenames of train_smoke.TRAIN_FILES).

    The bytes must match their frozen SHA-256s and the built families the frozen TRAIN_FAMILIES_SHA256; a mismatch is
    a ProtocolError. A read error (Drive) is an OSError and stays an infrastructure failure."""
    sources = []
    for name, expected in sorted(ts.TRAIN_FILES.items()):
        raw = (Path(inputs) / Path(name).name).read_bytes()
        require(ts.sha256(raw) == expected, f"{name} does not match its frozen SHA-256 {expected}")
        sources.append((name, raw))
    with protocol_assertions("TRAIN data"):
        for name, raw in sources:
            require(len(json.loads(raw)) == FAMILIES_PER_FILE, f"{name}: expected {FAMILIES_PER_FILE} families")
        families = ts.select_families(sources, per_file=FAMILIES_PER_FILE)
    data = {"schema": "phase2-train-data-1", "purpose": "Phase-2 TRAIN (D043); all 160 families",
            "sources": {name: ts.sha256(raw) for name, raw in sources}, "families": families}
    data["families_sha256"] = ts.digest(families)
    require(data["families_sha256"] == TRAIN_FAMILIES_SHA256,
            f"TRAIN families SHA-256 {data['families_sha256']} differs from the frozen {TRAIN_FAMILIES_SHA256}")
    validate_phase2_data(data)
    return data


def verify_exposure(inputs, data, seed):
    """EXPOSURE_ORDER.json must have its frozen SHA-256, be for the frozen TRAIN families, and its list for ``seed``
    must equal the recomputed order. Returns (order_sha256, file SHA-256)."""
    raw = (Path(inputs) / Path(EXPOSURE_ORDER_PATH).name).read_bytes()
    actual = ts.sha256(raw)
    require(actual == EXPOSURE_ORDER_SHA256, f"EXPOSURE_ORDER.json SHA-256 {actual} differs from the frozen {EXPOSURE_ORDER_SHA256}")
    with protocol_assertions("EXPOSURE_ORDER.json"):
        document = json.loads(raw)
    require(document.get("families_sha256") == TRAIN_FAMILIES_SHA256, "EXPOSURE_ORDER.json is for other TRAIN data")
    return check_exposure(document, data, seed), actual


def parse_manifest(text):
    """The JSON block of IMPLEMENTATION_MANIFEST.md (ProtocolError if absent or malformed)."""
    with protocol_assertions("IMPLEMENTATION_MANIFEST.md"):
        start = text.index("```json\n") + len("```json\n")
        document = json.loads(text[start:text.index("\n```", start)])
    require(isinstance(document, dict) and document.get("schema") == MANIFEST_SCHEMA,
            f"IMPLEMENTATION_MANIFEST.md must have schema {MANIFEST_SCHEMA}")
    return document


def engine_digest(value):
    """hinglish_pilot.data.digest (compact, sorted JSON): the engine's config/dataset/split/code/record identities."""
    return ts.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                separators=(",", ":")).encode("utf-8"))


def manifest_constant_problems(manifest):
    """Registered entries of IMPLEMENTATION_MANIFEST.md that this module fixes itself (empty list: all agree)."""
    files = manifest.get("files")
    if not isinstance(files, dict):
        return ["files (none listed)"]
    problems = [f"Implementation manifest records another {name}" for name, expected in ts.TRAIN_FILES.items()
                if files.get(name) != expected]
    if files.get(EXPOSURE_ORDER_PATH) != EXPOSURE_ORDER_SHA256:
        problems.append("Implementation manifest records another EXPOSURE_ORDER.json")
    with protocol_assertions("IMPLEMENTATION_MANIFEST.md"):
        model, training, dependencies = manifest["model"], manifest["training"], manifest["dependencies"]
        checks = {
            "exposure order": manifest["exposure_order"]["sha256"] == EXPOSURE_ORDER_SHA256,
            "recipe": training["recipe_sha256"] == ts.digest(RECIPE),
            "GradScaler": training["grad_scaler"] == SCALER,
            "model": (model["id"], model["revision"]) == (ts.MODEL_ID, ts.MODEL_REVISION),
            "tokenizer revision": model.get("tokenizer_revision") == ts.MODEL_REVISION,
            "Hub files": model.get("hub_files") == HUB_FILES,  # B2: the loaded tokenizer/config files
            "chat template": model.get("chat_template") == CHAT_TEMPLATE,
            "training dependencies": dependencies["train"] == ts.PINS,
            "torch build": dependencies["torch_build"] == ts.TORCH_BUILD,
            "baseline DEV identities": (manifest.get("baseline_dev") or {}).get("dataset_sha256") == DEV_DATASET_SHA256
                                       and manifest["baseline_dev"].get("split_sha256") == DEV_SPLIT_SHA256,
        }
    bad = [name for name, ok in checks.items() if not ok]
    if bad:
        problems.append("Implementation manifest differs from the trainer in: " + ", ".join(bad))
    return problems


def verify_implementation(inputs, code_dir=None):
    """Recheck IMPLEMENTATION_MANIFEST.md against what this process actually runs and reads (Amendment 2 item 7).

    Checks the trainer's own source files, the frozen TRAIN and exposure-order hashes, the recipe, GradScaler,
    model and tokenizer revision, the Hub tokenizer/config hashes and chat template it registers (B2; the downloaded
    bytes are verified by verify_hub_files and the loaded template by verify_chat_template inside the attempt), the
    baseline DEV identities and the exact dependency stack. Returns (manifest document, manifest SHA-256)."""
    raw = (Path(inputs) / MANIFEST_NAME).read_bytes()
    with protocol_assertions("IMPLEMENTATION_MANIFEST.md"):
        text = raw.decode("utf-8")
    manifest = parse_manifest(text)
    files = manifest.get("files")
    require(isinstance(files, dict), "IMPLEMENTATION_MANIFEST.md lists no files")
    code_dir = Path(code_dir or Path(__file__).resolve().parent)
    for name in TRAINER_CODE:
        actual = file_sha256(code_dir / name)
        require(files.get(f"t4_smoke/{name}") == actual,
                f"t4_smoke/{name} (SHA-256 {actual}) differs from the implementation manifest")
    problems = manifest_constant_problems(manifest)
    require(not problems, "; ".join(problems))
    return manifest, ts.sha256(raw)


def verify_hub_files(manifest):
    """B2 (Amendment 2 item 7 at the executable boundary): download the tokenizer, config and generation files of the
    pinned revision (the cache the tokenizer and model load from) and compare their bytes with the manifest, which
    verify_implementation has already compared with HUB_FILES. A download error stays a network/Hub infrastructure
    failure; a differing file is a ProtocolError. Returns {file: SHA-256}."""
    hub_files = manifest["model"]["hub_files"]
    require(hub_files == HUB_FILES, "Implementation manifest registers other Hub files than the trainer")
    from huggingface_hub import hf_hub_download
    found = {}
    for name, expected in sorted(hub_files.items()):
        path = hf_hub_download(ts.MODEL_ID, name, revision=ts.MODEL_REVISION, token=ts.hf_token())
        actual = ts.file_sha256(path)
        require(actual == expected, f"{name} at the pinned revision has SHA-256 {actual}, implementation manifest {expected}")
        found[name] = actual
    return found


def verify_chat_template(tokenizer, manifest):
    """B2: the chat template of the tokenizer this process loaded must be the manifest's (digest and UTF-8 bytes)."""
    template = getattr(tokenizer, "chat_template", None)
    require(isinstance(template, str) and template, "The loaded tokenizer has no chat template")
    registered = manifest["model"]["chat_template"]
    require(registered == CHAT_TEMPLATE, "Implementation manifest registers another chat template than the trainer")
    actual = ts.digest(template)
    require(actual == registered["digest"] and ts.sha256(template.encode("utf-8")) == registered["utf8_sha256"],
            f"Loaded chat template (digest {actual}) differs from the implementation manifest {registered['digest']}")
    return actual


# ---------------------------------------------------------------- the unchanged-model DEV baseline (Amendment 2 item 6, Amendment 3 item 3; B3)

def execution_problems(run, environment, manifest, adapter=None):
    """Why an engine run's recorded execution is not the registered one (empty list: it is). Amendment 3 item 3:

    run_manifest.json["backend"] (and every entry of ["sessions"]) must record a Tesla T4 with capability [7, 5],
    gpu_verified True, the registered attention/dtype/NF4 settings, the pinned model and tokenizer revision, the
    manifest's chat template, the expected adapter and the base shard hashes; environment.json["packages"] must equal
    the manifest's evaluation pins plus PEFT; the recorded execution digest must recompute."""
    problems = []
    backend = run.get("backend") if isinstance(run.get("backend"), dict) else {}
    hardware = backend.get("hardware")
    if not (isinstance(hardware, str) and "T4" in hardware):
        problems.append(f"backend hardware {hardware!r} is not a Tesla T4")
    if backend.get("capability") != T4_CAPABILITY:
        problems.append(f"backend capability {backend.get('capability')!r}, registered {T4_CAPABILITY}")
    for key, value in EXECUTION.items():
        if backend.get(key) != value:
            problems.append(f"backend {key} {backend.get(key)!r}, registered {value!r}")
    quantization = backend.get("quantization") if isinstance(backend.get("quantization"), dict) else {}
    for key, value in QUANTIZATION.items():
        if quantization.get(key) != value:
            problems.append(f"quantization {key} {quantization.get(key)!r}, registered {value!r}")
    for key in ("model_revision", "tokenizer_revision"):
        if backend.get(key) != ts.MODEL_REVISION:
            problems.append(f"backend {key} {backend.get(key)!r} is not the pinned revision")
    if backend.get("chat_template_sha256") != manifest["model"]["chat_template"]["digest"]:
        problems.append("backend chat template differs from the implementation manifest")
    if backend.get("adapter", "missing") != adapter:
        problems.append(f"backend adapter {backend.get('adapter', 'missing')!r}, expected {adapter!r}")
    shards = backend.get("base_weight_shards_sha256")
    if not (isinstance(shards, dict) and shards and all(re.fullmatch("[0-9a-f]{64}", str(v)) for v in shards.values())):
        problems.append("backend records no base weight shard hashes")
    pins = dict(manifest["dependencies"]["evaluation"], **manifest["dependencies"]["adapter_evaluation"])
    packages = (environment or {}).get("packages") if isinstance((environment or {}).get("packages"), dict) else {}
    wrong = [f"{name} {packages.get(name)!r} (registered {pin})" for name, pin in sorted(pins.items()) if packages.get(name) != pin]
    if wrong:
        problems.append("environment packages differ from the registered stack: " + ", ".join(wrong))
    sessions = run.get("sessions")
    if not (isinstance(sessions, list) and sessions):
        problems.append("no recorded session")
    else:
        for number, session in enumerate(sessions, 1):
            if not isinstance(session, dict) or session.get("environment") != environment or session.get("backend") != backend:
                problems.append(f"session {number} recorded another environment or backend")
    if run.get("execution_sha256") != engine_digest({"backend": backend, "environment": environment}):
        problems.append("execution digest does not recompute from the recorded backend and environment")
    return problems


def generation_problems(run, config, journal, errors, order):
    """Why the journal of a complete engine run does not hold exactly one resolved generation per evaluated rendering
    (empty list: it does). Every record's own digest must recompute, belong to this run and configuration, follow
    the engine's attempt rules (consecutive attempts, at most the configured retries, a generated response is final
    and never retried) and be a scored generation of the pinned model."""
    problems, by_rendering = [], {}
    for number, item in enumerate(journal, 1):
        if not isinstance(item, dict) or item.get("record_sha256") != engine_digest({k: v for k, v in item.items() if k != "record_sha256"}):
            problems.append(f"journal record {number} was edited (record digest does not recompute)")
            continue
        if item.get("run_id") != run.get("run_id") or item.get("config_sha256") != run.get("config_sha256"):
            problems.append(f"journal record {number} belongs to another run or configuration")
            continue
        by_rendering.setdefault(item.get("rendering_id"), []).append(item)
    unexpected = sorted(set(by_rendering) - set(order), key=str)
    if unexpected:
        problems.append(f"journal holds renderings outside the evaluation order: {unexpected[:3]}")
    allowed = 1 + config.get("max_infrastructure_retries", 0)
    resolved = 0
    for rendering in order:
        history = sorted(by_rendering.get(rendering, []), key=lambda item: item.get("attempt_number", 0))
        numbers = [item.get("attempt_number") for item in history]
        if numbers != list(range(1, len(history) + 1)) or len(history) > allowed:
            problems.append(f"{rendering}: attempts {numbers} break the engine's attempt rules")
            continue
        if any(item.get("status") not in ("generated", "infrastructure_failure") for item in history):
            problems.append(f"{rendering}: an attempt has an unfinished or unknown status")
            continue
        generated = [item for item in history if item["status"] == "generated"]
        if not generated:
            continue
        final = generated[0]
        if len(generated) > 1 or final is not history[-1]:
            problems.append(f"{rendering}: a generated response was retried")
        elif not (isinstance(final.get("raw_response"), str) and type(final.get("correct")) is bool
                  and final.get("model_revision") == ts.MODEL_REVISION and final.get("mode") == config.get("mode")):
            problems.append(f"{rendering}: the generated record is not a scored generation of the pinned model")
        else:
            resolved += 1
    if resolved != len(order) or len(order) != BASELINE_PROMPTS:
        problems.append(f"{resolved} resolved generations over {len(order)} renderings; exactly {BASELINE_PROMPTS} required")
    if run.get("attempts") != len(journal):
        problems.append("run_manifest.json attempts differ from the journal")
    if errors != [item for item in journal if isinstance(item, dict) and item.get("status") != "generated"]:
        problems.append("errors.jsonl differs from the journal")
    return problems


def baseline_archive_problems(archive, record, manifest, adapter=None):
    """Why the baseline results ZIP is not the complete registered unchanged-model DEV run (empty list: it is).

    Validates the actual archive, not its metadata: the complete engine export with consistent checksums; the
    engine source snapshot against the manifest's engine files; the recomputed config, dataset, split and code
    digests against the run manifest, the record, the frozen DEV identities and the registered DEV configuration;
    the evaluation order; the registered execution settings and environment (execution_problems); and exactly 120
    resolved generations in the journal (generation_problems)."""
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(set(names)) != len(names) or any(name.startswith("/") or ".." in Path(name).parts for name in names):
            return ["results ZIP has duplicate or unsafe member names"]
        members = {name: z.read(name) for name in names}
    missing = [name for name in BASELINE_MEMBERS if name not in members]
    if missing:
        return ["results ZIP is not a complete engine export; it lacks " + ", ".join(missing)]
    problems = []
    listed = {}
    for line in members["checksums.sha256"].decode("utf-8").splitlines():
        checksum, _, name = line.partition("  ")
        listed[name] = checksum
    if set(listed) != set(members) - {"checksums.sha256"}:
        problems.append("checksums.sha256 does not list exactly the archive members")
    changed = sorted(name for name, checksum in listed.items() if name in members and ts.sha256(members[name]) != checksum)
    if changed:
        problems.append("members differ from checksums.sha256: " + ", ".join(changed[:5]))
    load = lambda name: json.loads(members[name])  # noqa: E731
    rows = lambda name: [json.loads(line) for line in members[name].decode("utf-8").splitlines() if line.strip()]  # noqa: E731
    run, config, dataset, splits, environment, order = (load(name) for name in (
        "run_manifest.json", "experiment_config.json", "dataset.json", "split_manifest.json", "environment.json",
        "evaluation_order.json"))
    files, groups = manifest["files"], manifest.get("groups") or {}
    # engine identity: the source snapshot the run executed equals the manifest's engine files
    expected_sources = {path[len(ENGINE_PREFIX):]: files.get(path) for path in groups.get("engine", [])
                        if path.startswith(ENGINE_PREFIX)}
    sources = {name[len("source/"):]: ts.sha256(content) for name, content in members.items() if name.startswith("source/")}
    if not expected_sources or sources != expected_sources:
        problems.append("engine source snapshot differs from the implementation manifest's engine files")
    code = engine_digest(sources)
    if not (run.get("code_sha256") == code == record.get("code_sha256") == engine_digest(expected_sources)):
        problems.append("engine code identity does not match the implementation manifest")
    # configuration: recomputed digest, and the registered DEV configuration
    generation = manifest["generation_config"]
    if not (engine_digest(config) == run.get("config_sha256") == record.get("config_sha256")):
        problems.append("config digest does not recompute from experiment_config.json")
    if engine_digest(dict(config, adapter=None)) != generation["engine_config_sha256"]["dev"]:
        problems.append("experiment_config.json is not the registered DEV configuration")
    wrong = sorted(key for key, value in generation["decoding"].items() if config.get(key) != value)
    if wrong:
        problems.append("execution settings differ from the registered decoding: " + ", ".join(wrong))
    if (config.get("mode"), config.get("adapter", "missing"), config.get("model_id"), config.get("model_revision"),
            config.get("tokenizer_revision")) != (BASELINE_MODE, adapter, ts.MODEL_ID, ts.MODEL_REVISION, ts.MODEL_REVISION):
        problems.append("not an unchanged-model DEV configuration of the pinned model")
    if (ts.sha256(str(config.get("instruction")).encode("utf-8")), config.get("prompt_version")) != (
            manifest["prompt"]["instruction_sha256"], manifest["prompt"]["version"]):
        problems.append("prompt differs from the registered instruction")
    # frozen DEV data and its source snapshot
    baseline_dev = manifest.get("baseline_dev") or {}
    if not (engine_digest(dataset) == run.get("dataset_sha256") == record.get("dataset_sha256") == DEV_DATASET_SHA256
            == baseline_dev.get("dataset_sha256")):
        problems.append("dataset is not the frozen DEV dataset")
    if not (engine_digest(splits) == run.get("split_sha256") == DEV_SPLIT_SHA256 == baseline_dev.get("split_sha256")):
        problems.append("split manifest is not the frozen DEV split")
    families = dataset.get("families") if isinstance(dataset.get("families"), list) else []
    snapshot = [dict(family, dataset_version=dataset.get("version"), schema_version=dataset.get("schema_version"),
                     kind=dataset.get("kind"), borrowing_policy=dataset.get("borrowing_policy")) for family in families]
    if rows("dataset_snapshot.jsonl") != snapshot:
        problems.append("dataset_snapshot.jsonl differs from dataset.json")
    renderings = sorted(family["forms"][form]["rendering_id"] for family in families for form in ("E", "R", "C"))
    shuffled = list(renderings)
    random.Random(config.get("seed")).shuffle(shuffled)
    if not (order == run.get("evaluation_order") == shuffled):
        problems.append("evaluation order is not the engine-seed order of the DEV renderings")
    # completeness, execution and the generations themselves
    if (run.get("status"), run.get("mode"), run.get("expected"), run.get("completed"), run.get("unresolved")) != (
            "COMPLETE", BASELINE_MODE, BASELINE_PROMPTS, BASELINE_PROMPTS, 0):
        problems.append("run_manifest.json is not a COMPLETE 120/120 unchanged-model DEV run")
    if run.get("run_id") != record.get("run_id"):
        problems.append("record and archive name different runs")
    problems += execution_problems(run, environment, manifest, adapter=adapter)
    problems += generation_problems(run, config, rows("generation_attempts.jsonl"), rows("errors.jsonl"), order)
    return problems


def read_manifest(manifest):
    """(document, SHA-256) of the IMPLEMENTATION_MANIFEST.md file at ``manifest``. A bare SHA-256 is refused: a hash
    alone cannot validate an archive (Sol re-review B3)."""
    if isinstance(manifest, str) and re.fullmatch("[0-9a-f]{64}", manifest) and not Path(manifest).exists():
        raise Refused("Validating the unchanged-model DEV baseline needs the implementation manifest file, not only its "
                      "SHA-256 (Amendment 3 item 3); no attempt was opened.")
    raw = Path(manifest).read_bytes()
    try:
        document = parse_manifest(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise Refused(f"Unreadable implementation manifest {manifest}: {error}; no attempt was opened.") from None
    return document, ts.sha256(raw)


def verify_baseline(baseline_dir, manifest):
    """Amendment 2 item 6 with Amendment 3 item 3 (B3): the validated complete unchanged-model DEV run under the
    implementation manifest file ``manifest``.

    The record must describe a complete run under that manifest and name the results ZIP by its SHA-256, and the ZIP
    itself must be the complete registered 120-generation run (baseline_archive_problems). Returns the ZIP's SHA-256;
    raises Refused otherwise (nothing is opened or logged)."""
    folder = Path(baseline_dir) if baseline_dir is not None else None
    if folder is None or not (folder / BASELINE_RECORD).is_file():
        raise Refused(f"No unchanged-model DEV run record ({BASELINE_RECORD}) in {folder}: run Phase2_Baseline_DEV to "
                      "completion first (PREREGISTRATION §5, Amendment 2 item 6). No attempt was opened.")
    document, manifest_sha256 = read_manifest(manifest)
    try:
        record = json.loads((folder / BASELINE_RECORD).read_text(encoding="utf-8"))
        expected = {"schema": BASELINE_SCHEMA, "run": BASELINE_RUN, "split": "dev", "mode": BASELINE_MODE, "adapter": None,
                    "model_id": ts.MODEL_ID, "model_revision": ts.MODEL_REVISION, "status": "COMPLETE",
                    "completed": BASELINE_PROMPTS, "expected": BASELINE_PROMPTS, "unresolved": 0,
                    "results_zip": f"{BASELINE_RUN}_results.zip"}
        wrong = sorted(key for key, value in expected.items() if record.get(key) != value)
        if wrong:
            raise Refused(f"The unchanged-model DEV run is not a complete baseline ({', '.join(wrong)}); no attempt was opened.")
        if record.get("implementation_manifest_sha256") != manifest_sha256:
            raise Refused(f"The unchanged-model DEV run was made under implementation manifest "
                          f"{record.get('implementation_manifest_sha256')}, not {manifest_sha256} (Amendment 2 item 6).")
        archive = folder / record["results_zip"]
        actual = file_sha256(archive) if archive.is_file() else None
        if actual is None or actual != record.get("results_zip_sha256"):
            raise Refused(f"{archive} is missing or differs from its recorded SHA-256; no attempt was opened.")
        problems = baseline_archive_problems(archive, record, document)
    except (KeyError, IndexError, TypeError, AttributeError, ValueError, zipfile.BadZipFile) as error:
        raise Refused(f"Unreadable unchanged-model DEV baseline ({type(error).__name__}: {error}); no attempt was opened.") from None
    if problems:
        raise Refused("The baseline results ZIP is not a complete unchanged-model DEV run as registered (Amendment 3 "
                      "item 3); no attempt was opened:\n- " + "\n- ".join(problems[:12]))
    return actual


def attempt_identity(inputs, baseline_zip_sha256, code_dir=None):
    """Configuration and implementation identity of a training attempt; identical across all attempts (Amendment 2
    item 7). Computed from the bytes actually present, before the attempt opens."""
    code_dir = Path(code_dir or Path(__file__).resolve().parent)
    return {
        "implementation_manifest_sha256": file_sha256(Path(inputs) / MANIFEST_NAME),
        "trainer_code_sha256": {name: file_sha256(code_dir / name) for name in TRAINER_CODE},
        "train_files_sha256": {name: file_sha256(Path(inputs) / Path(name).name) for name in sorted(ts.TRAIN_FILES)},
        "exposure_order_file_sha256": file_sha256(Path(inputs) / Path(EXPOSURE_ORDER_PATH).name),
        "recipe_sha256": ts.digest(RECIPE), "model_id": ts.MODEL_ID, "model_revision": ts.MODEL_REVISION,
        "stack": dict(ts.PINS, torch=ts.TORCH_BUILD), "gpu": "Tesla T4",
        "baseline_dev_results_zip_sha256": baseline_zip_sha256,
    }


def gpu_name():
    """(name, capability) of CUDA device 0, or (None, None) without a GPU."""
    try:
        import torch
    except ImportError:
        return None, None
    if not torch.cuda.is_available():
        return None, None
    return torch.cuda.get_device_name(0), tuple(torch.cuda.get_device_capability(0))


def check_stack():
    """Amendment 2 item 3: the exact §2 stack on a T4, checked before any attempt opens (Refused otherwise)."""
    mismatches = ts.stack_mismatches(ts.versions())
    if mismatches:
        raise Refused("D021 stack mismatch (Amendment 2 item 3): no study run takes place until a dated amendment; "
                      "no attempt was opened: " + "; ".join(mismatches))
    name, capability = gpu_name()
    if not name or "T4" not in name or capability != (7, 5):
        raise Refused(f"Tesla T4 required (Amendment 2 item 3), found {name}; no attempt was opened.")
    return name


def run_sequence(families, arm, seed):
    """(family_id, form) for all 960 microbatches of one run: 3 passes x 160 families x (E, second)."""
    require(arm in ARMS, "Unknown arm")
    require(isinstance(seed, int), "Seed must be an integer")
    second = ARMS[arm]
    sequence = [(family_id, form) for number in range(1, RECIPE["passes"] + 1)
                for family_id in pass_order(families, seed, number) for form in ("E", second)]
    require(len(sequence) == RECIPE["updates"] * RECIPE["accumulation"], "Sequence does not fill 60 updates")
    return sequence


def run_examples(examples, families, arm, seed):
    return [dict(examples[family_id][form], family_id=family_id, form=form)
            for family_id, form in run_sequence(families, arm, seed)]


def pass_of(update):
    return (update - 1) // RECIPE["updates_per_pass"] + 1


def run_name(arm, seed):
    return f"{arm}-s{seed}"


def attempt_dir(train_root, arm, seed, attempt):
    return Path(train_root) / run_name(arm, seed) / f"attempt-{attempt:02d}"


# ---------------------------------------------------------------- numerics (Amendment 1 item 10)

def make_scaler(torch):
    return torch.amp.GradScaler("cuda", **SCALER)


def set_lr(trainer, update):
    value = lr_at(update)
    for group in trainer.optimizer.param_groups:
        group["lr"] = value
    return value


def nonfinite_tensors(torch, named):
    return [name for name, tensor in named if not bool(torch.isfinite(tensor).all())]


class Phase2Trainer(ts.Trainer):
    """train_smoke.Trainer with the pinned GradScaler and the item-10 step contract.

    Each call of ``update(u)`` is one accumulation window and must end in one successful optimizer step: lr(u) is
    set first, the 16 microbatch losses must be finite, gradients are unscaled before clipping, the gradient norm
    must be finite and the scaler must not skip. Otherwise NumericalFailure is raised (never replayed or skipped).
    """

    def __init__(self, torch, model, trainable, keep, sequence, sampler):
        super().__init__(torch, model, trainable, keep, sequence, sampler)
        require(len(sequence) == RECIPE["updates"] * RECIPE["accumulation"], "Exactly 960 microbatches per run")
        self.scaler = make_scaler(torch)
        self.attempted_steps = 0
        self.successful_steps = 0

    def steps(self):
        return {"windows": RECIPE["updates"], "attempted": self.attempted_steps, "successful": self.successful_steps,
                "cursor": self.cursor}

    def update(self, number):
        torch = self.torch
        require(self.cursor == ts.update_cursors(number)[0], "Data cursor out of step with the update number")
        require(self.successful_steps == number - 1, "Successful steps out of step with the update number")
        lr = set_lr(self, number)  # before step u
        cursor_before = self.cursor
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        self.sampler.take()
        scale_before = self.scaler.get_scale()
        self.attempted_steps += 1
        start = time.perf_counter()
        record = {"update": number, "attempted_step": self.attempted_steps, "cursor_before": cursor_before, "lr": lr,
                  "pass_number": pass_of(number), "scale_before": scale_before, "microbatch_losses": []}
        free, input_tokens, supervised_tokens, items = [], 0, 0, []

        def fail(reason):
            record.update(reason=reason, cursor_at_failure=self.cursor, items=items)
            return NumericalFailure(f"NUMERICAL FAILURE at update {number}: {reason}", record)

        for _ in range(RECIPE["accumulation"]):
            example = self.sequence[self.cursor]  # never wraps: exactly 60 windows over exactly 3 passes
            loss = self.loss(example)
            value = float(loss.detach())
            record["microbatch_losses"].append(ts.json_float(value))
            items.append(f"{example['family_id']}-{example['form']}")
            self.cursor += 1
            if not math.isfinite(value):
                raise fail(f"non-finite loss {value} on {items[-1]}")
            self.scaler.scale(loss / RECIPE["accumulation"]).backward()
            free.append(torch.cuda.mem_get_info()[0])
            input_tokens += len(example["input_ids"])
            supervised_tokens += len(example["input_ids"]) - example["boundary_index"]
        self.scaler.unscale_(self.optimizer)  # unscale before clipping
        grad_norm = float(torch.nn.utils.clip_grad_norm_(self.parameters, RECIPE["clip"]))
        record["grad_norm"] = ts.json_float(grad_norm)
        if not math.isfinite(grad_norm):
            raise fail(f"non-finite gradient norm {grad_norm}")
        self.scaler.step(self.optimizer)
        self.scaler.update()
        scale_after = self.scaler.get_scale()
        record["scale_after"] = scale_after
        self.optimizer.zero_grad(set_to_none=True)
        if scale_after != scale_before:
            record["skipped"] = scale_after < scale_before
            raise fail(f"GradScaler skipped the step (scale {scale_before:g} -> {scale_after:g})")
        self.successful_steps += 1
        torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        nvml = self.sampler.take()
        record.update(
            successful_step=self.successful_steps, cursor_after=self.cursor, seconds=seconds, skipped=False,
            input_tokens=input_tokens, supervised_tokens=supervised_tokens, items=items,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            min_free_torch_bytes=min(free), min_free_nvml_bytes=nvml)
        record["loss"] = ts.json_float(sum(record["microbatch_losses"]) / RECIPE["accumulation"])
        record["min_free_bytes"] = min(value for value in (record["min_free_torch_bytes"], nvml) if value is not None)
        print(f"update {number}: loss {record['loss']} grad_norm {record['grad_norm']} lr {lr:.3e} "
              f"scale {scale_before:g} {seconds:.1f}s tokens {input_tokens} steps {self.successful_steps}/"
              f"{self.attempted_steps} cursor {self.cursor} min_free {record['min_free_bytes'] / 2**30:.2f} GiB", flush=True)
        return record


# ---------------------------------------------------------------- GPU runtime (lazy imports via train_smoke)

def load_model(torch, seed):
    """train_smoke.load_model with the run seed: it seeds random/torch/CUDA immediately before get_peft_model."""
    original = ts.seed_everything

    def seeded(torch_module, _smoke_seed):
        original(torch_module, seed)

    ts.seed_everything = seeded
    try:
        return ts.load_model(torch)
    finally:
        ts.seed_everything = original


def weight_shard_hashes():
    """SHA-256 of each downloaded base-weight shard (local Hub cache), pinned revision."""
    from huggingface_hub import hf_hub_download
    kwargs = {"revision": ts.MODEL_REVISION, "token": ts.hf_token()}
    index = hf_hub_download(ts.MODEL_ID, "model.safetensors.index.json", **kwargs)
    shards = sorted(set(json.loads(Path(index).read_text())["weight_map"].values()))
    return {name: ts.file_sha256(hf_hub_download(ts.MODEL_ID, name, **kwargs)) for name in shards}


def prepare_examples(tokenizer, families):
    """Labelled examples (identical E/R/C targets asserted, no truncation) and the mask audit; protocol stage."""
    with protocol_assertions("labels"):
        examples = ts.build_examples(tokenizer, families)
        audit = ts.mask_audit(tokenizer, examples, families)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    audit["last_target_is_im_end"] = all(e["labels"][-1] == im_end for built in examples.values() for e in built.values())
    protocol(audit["passed"] and audit["last_target_is_im_end"], "Mask/target audit failed: " + "; ".join(audit["failures"][:5]))
    return examples, audit


def checkpoint_meta(trainer, completed, report):
    return {"cursor": trainer.cursor, "completed_updates": completed, "rng_python": ts.list_state(random.getstate()),
            "attempted_steps": trainer.attempted_steps, "successful_steps": trainer.successful_steps,
            "recipe_sha256": ts.digest(RECIPE), "data_sha256": report["data_sha256"], "arm": report["arm"],
            "seed": report["seed"], "attempt": report["attempt"], "order_sha256": report["order_sha256"],
            "initial_adapter_sha256": report["initial_adapter_sha256"],
            "parameter_names": [name for name, _ in trainer.trainable]}


def is_write_failure(error):
    """Typed write failures: filesystem/Drive OSError, safetensors write errors and torch.save stream-writer errors."""
    if isinstance(error, OSError):
        return True
    if any(cls.__name__ == "SafetensorError" for cls in type(error).__mro__):
        return True
    return isinstance(error, RuntimeError) and any(marker in str(error) for marker in ("PytorchStreamWriter", "inline_container"))


@contextlib.contextmanager
def checkpoint_write(what):
    """Amendment 2 item 2: a failed checkpoint/adapter write is infrastructure; anything else passes through."""
    try:
        yield
    except Exception as error:
        if is_write_failure(error):
            raise CheckpointWriteError(f"failed {what} write: {type(error).__name__}: {error}") from error
        raise


def save_checkpoint(torch, trainer, out, completed, probe_example, report):
    """train_smoke.save, generalised to any update; written atomically, only the latest is kept."""
    bad = nonfinite_tensors(torch, trainer.trainable)
    if bad:
        raise NumericalFailure(f"non-finite adapter parameter(s) after update {completed}: {bad[:3]}")
    temporary, folder, old = out / "checkpoint.tmp", out / "checkpoint", out / "checkpoint.old"
    probe = trainer.probe(probe_example)
    state = {"adapter": {name: parameter.detach().cpu().clone() for name, parameter in trainer.trainable},
             "optimizer": trainer.optimizer.state_dict(), "scaler": trainer.scaler.state_dict(),
             "rng_torch": torch.get_rng_state(), "rng_cuda": torch.cuda.get_rng_state(), "probe_logits": probe}
    meta = checkpoint_meta(trainer, completed, report)
    meta.update(probe_item=f"{probe_example['family_id']}-{probe_example['form']}",
                digests=ts.state_digests(torch, trainer.trainable, trainer.optimizer, trainer.scaler))
    with checkpoint_write("checkpoint"):
        shutil.rmtree(temporary, ignore_errors=True)
        temporary.mkdir(parents=True)
        trainer.model.save_pretrained(temporary / "adapter", save_embedding_layers=False)
        torch.save(state, temporary / "state.pt")
        ts.write_json(temporary / "meta.json", meta)
        if folder.exists():
            folder.rename(old)
        temporary.rename(folder)
        shutil.rmtree(old, ignore_errors=True)
    record = {"update": completed, "state_sha256": ts.file_sha256(folder / "state.pt"), "digests": meta["digests"]}
    report["checkpoints"].append(record)
    print(f"checkpoint after update {completed} saved", flush=True)
    return record


def restore_checkpoint(torch, trainer, out, report):
    """train_smoke.restore, generalised: fresh model, then state, exact digests and the saved probe logits.

    Every identity and digest comparison raises ProtocolError (Amendment 2 item 2: detected at reload, still protocol)."""
    folder = out / "checkpoint"
    meta = ts.read_json(folder / "meta.json")
    for key in ("recipe_sha256", "data_sha256", "arm", "seed", "attempt", "order_sha256", "initial_adapter_sha256"):
        expected = ts.digest(RECIPE) if key == "recipe_sha256" else report[key]
        require(meta.get(key) == expected, f"Checkpoint was made with a different {key}")
    require(meta.get("parameter_names") == [name for name, _ in trainer.trainable], "Adapter parameter order changed")
    completed = meta["completed_updates"]
    state = torch.load(folder / "state.pt", map_location="cpu", weights_only=True)
    with torch.no_grad():
        for name, parameter in trainer.trainable:
            parameter.copy_(state["adapter"][name].to(parameter.device))
    trainer.optimizer.load_state_dict(state["optimizer"])
    trainer.scaler.load_state_dict(state["scaler"])
    trainer.cursor = meta["cursor"]
    trainer.attempted_steps, trainer.successful_steps = meta["attempted_steps"], meta["successful_steps"]
    version, internal, gauss = meta["rng_python"]
    random.setstate((version, tuple(internal), gauss))
    torch.set_rng_state(state["rng_torch"])
    torch.cuda.set_rng_state(state["rng_cuda"])
    live = ts.state_digests(torch, trainer.trainable, trainer.optimizer, trainer.scaler)
    tolerance = {"atol": RECIPE["probe_atol"], "rtol": RECIPE["probe_rtol"]}
    probe = trainer.probe(trainer.sequence[0])
    saved = state["probe_logits"]
    exact = {key: live[key] == meta["digests"][key] for key in live}
    close = {"state_digests_exact": all(exact.values()),
             "cursor": trainer.cursor == ts.update_cursors(completed + 1)[0],
             "probe": probe.shape == saved.shape and torch.allclose(probe, saved, **tolerance)}
    result = {"from_update": completed, "allclose": close, "exact_digests": exact, "tolerance": tolerance,
              "probe_max_abs_diff": ts.json_float((probe - saved).abs().max()) if probe.shape == saved.shape else None,
              "checkpoint_state_sha256": ts.file_sha256(folder / "state.pt"), "at": time.time()}
    result["passed"] = all(close.values())
    print("reload check:", json.dumps(close), "probe max abs diff", result["probe_max_abs_diff"], flush=True)
    require(result["passed"], "Reloaded state does not match the saved state: " + json.dumps(close))
    return completed, result


def save_final_adapter(torch, trainer, out):
    """Adapter after update 60; saved tensors must be finite and equal to the trained ones exactly."""
    folder = out / "final_adapter"
    with checkpoint_write("final adapter"):
        shutil.rmtree(folder, ignore_errors=True)
        trainer.model.save_pretrained(folder, save_embedding_layers=False)
    from safetensors.torch import load_file
    saved = load_file(str(folder / "adapter_model.safetensors"))
    bad = nonfinite_tensors(torch, sorted(saved.items()))
    if bad:
        raise NumericalFailure(f"non-finite saved parameter(s): {bad[:3]}")
    live = {name.replace(".default.", "."): parameter.detach().cpu() for name, parameter in trainer.trainable}
    require(sorted(saved) == sorted(live), "Saved adapter tensor names differ from the trained adapter")
    require(all(torch.equal(saved[name], live[name]) for name in live), "Saved adapter differs from the trained adapter")
    return {"adapter_model_sha256": ts.file_sha256(folder / "adapter_model.safetensors"),
            "adapter_config_sha256": ts.file_sha256(folder / "adapter_config.json"),
            "adapter_tensors_sha256": ts.tensors_digest(trainer.trainable), "tensors": len(saved),
            "saved_parameters_finite": True}


# ---------------------------------------------------------------- failure classes (Amendment 1 item 11)

INFRASTRUCTURE_KINDS = (  # Amendment 2 item 2: the complete, typed list
    "runtime disconnect or kill", "CUDA out-of-memory", "Drive or filesystem OSError",
    "network or Hub download error", "failed checkpoint write")
NETWORK_MODULES = ("requests", "urllib3", "httpx", "http.client", "socket", "ssl")


def is_cuda_oom(error):
    return any(cls.__name__ == "OutOfMemoryError" and cls.__module__.split(".")[0] == "torch" for cls in type(error).__mro__)


def infrastructure_kind(error):
    """The Amendment 2 item 2 infrastructure kind of ``error``, or None (then it is a protocol failure)."""
    if isinstance(error, (KeyboardInterrupt, SystemExit)):
        return "runtime disconnect or kill"
    if isinstance(error, CheckpointWriteError):
        return "failed checkpoint write"
    if is_cuda_oom(error):
        return "CUDA out-of-memory"
    modules = {cls.__module__.split(".")[0] for cls in type(error).__mro__} | {
        ".".join(cls.__module__.split(".")[:2]) for cls in type(error).__mro__}
    if modules & set(NETWORK_MODULES) or any(m.startswith("huggingface_hub") for m in modules) and isinstance(error, OSError):
        return "network or Hub download error"
    if isinstance(error, OSError):
        return "Drive or filesystem OSError"
    return None


def classify_failure(error, stage=None):
    """'numerical', 'protocol' or 'infrastructure' for an exception raised during a training attempt.

    Amendment 2 item 2: infrastructure only for the typed list above (wherever it occurs, including a Drive read
    at the data stage); every ProtocolError and every other exception (TypeError, a plain AssertionError, an
    unexpected CUDA error, ...) is protocol and halts the study. ``stage`` is recorded but never decides the class."""
    if isinstance(error, NumericalFailure):
        return "numerical"
    if isinstance(error, ProtocolError):
        return "protocol"
    return "infrastructure" if infrastructure_kind(error) else "protocol"


def valid_run_problems(final):
    """Why a final_adapter.json record is not a valid run (empty list: valid). A resumed run is never valid."""
    problems = []
    if final.get("status") != "COMPLETE" or final.get("updates") != RECIPE["updates"]:
        problems.append("not COMPLETE with 60 updates")
    steps = final.get("steps") or {}
    expected = {"windows": RECIPE["updates"], "attempted": RECIPE["updates"], "successful": RECIPE["updates"],
                "cursor": RECIPE["updates"] * RECIPE["accumulation"]}
    if steps != expected:
        problems.append(f"steps {steps} != {expected}")
    if final.get("scaler_skips") != 0:
        problems.append("GradScaler skips recorded")
    if final.get("saved_parameters_finite") is not True:
        problems.append("saved parameters not verified finite")
    if final.get("resumed") is not False:
        problems.append("resumed (never valid for the gate)")
    if final.get("valid_for_gate") is not True:
        problems.append("not marked valid_for_gate")
    return problems


def attempt_outcome(folder):
    """(outcome, detail) of a finished or abandoned attempt folder, from its own report files."""
    folder = Path(folder)
    report_path = folder / "train_report.json"
    if not report_path.is_file():
        return "infrastructure", "no train_report.json: crash or disconnect before the run started"
    report = ts.read_json(report_path)
    status = report.get("status")
    if status == "COMPLETE":
        final_path = folder / "final_adapter.json"
        if not final_path.is_file():
            return "infrastructure", "final_adapter.json missing (failed save)"
        final = ts.read_json(final_path)
        if final.get("resumed"):
            return "resumed_invalid", "completed after a resume from a checkpoint: never valid for the gate"
        problems = valid_run_problems(final)
        if problems:
            return "protocol", "; ".join(problems)
        return "valid", "COMPLETE: 60/60 successful steps, cursor 960"
    if status == "FAILED":
        failure = report.get("failure_class")
        detail = (report.get("error") or "").strip().splitlines()[-1:] or [""]
        return (failure if failure in FAILURE_CLASSES else "protocol"), detail[0][:300]  # unknown never earns a retry
    return "infrastructure", f"run did not finish (status {status}): runtime disconnect or crash"


# ---------------------------------------------------------------- append-only attempt log and seed plan

def _entry_digest(entry):
    return ts.digest({key: value for key, value in entry.items() if key != "entry_sha256"})


def read_log(path):
    """Entries of the hash-chained attempt log; refuses an edited, reordered or truncated-in-the-middle log."""
    path = Path(path)
    if not path.exists():
        return []
    entries, previous = [], None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        entry = json.loads(line)
        protocol(entry.get("n") == len(entries) + 1, f"Attempt log line {number}: sequence number broken")
        protocol(entry.get("prev_sha256") == previous, f"Attempt log line {number}: hash chain broken (log was edited)")
        protocol(entry.get("entry_sha256") == _entry_digest(entry), f"Attempt log line {number}: entry was edited")
        entries.append(entry)
        previous = entry["entry_sha256"]
    return entries


def log_event(path, event, **fields):
    """Append one entry (never rewrites earlier lines)."""
    path = Path(path)
    entries = read_log(path)
    entry = {"n": len(entries) + 1, "event": event, "at": time.time(), **fields,
             "prev_sha256": entries[-1]["entry_sha256"] if entries else None}
    entry["entry_sha256"] = _entry_digest(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return entry


def _replay(entries):
    """Attempt histories, slot chains and reserves from log entries (structure checks; no run-order check)."""
    attempts = {}  # (seed, arm) -> [{"attempt", "slot", "outcome", "resumed", "detail"}]
    recorded_slot = {}  # reserve seed -> slot it was trained for
    identity = None

    def arm_state(seed, arm):
        history = attempts.get((seed, arm), [])
        valid = [a["attempt"] for a in history if a["outcome"] == "valid"]
        failed = [a["attempt"] for a in history if a["outcome"] in ("infrastructure", "resumed_invalid")]
        return {"attempts": history, "valid_attempt": valid[0] if valid else None, "failed": len(failed),
                "open": any(a["outcome"] is None for a in history)}

    def retired(seed):
        """A seed is retired once any of its arms failed twice without a valid run (the whole triplet goes)."""
        return any(arm_state(seed, arm)["failed"] >= MAX_ATTEMPTS and arm_state(seed, arm)["valid_attempt"] is None
                   for arm in ARMS)

    def halted():
        return any(a.get("outcome") in ("numerical", "protocol") or a.get("resume_outcome") in ("numerical", "protocol")
                   for prior in attempts.values() for a in prior)

    for entry in entries:
        event, arm, seed, slot, number = (entry.get(k) for k in ("event", "arm", "seed", "slot", "attempt"))
        protocol(arm in ARMS and seed in SLOTS + RESERVE_QUEUE and slot in SLOTS, f"Attempt log entry {entry.get('n')}: bad arm/seed/slot")
        history = attempts.setdefault((seed, arm), [])
        if event in ("start", "resume_start"):
            protocol(not halted(), f"Attempt log entry {entry['n']}: new training after the study halted")
            claimed = entry.get("identity")
            protocol(isinstance(claimed, dict) and claimed,
                     f"Attempt log entry {entry['n']}: training started without a configuration identity")
            identity = claimed if identity is None else identity
            protocol(claimed == identity, f"Attempt log entry {entry['n']}: configuration or implementation differs from "
                                          "earlier attempts (Amendment 2 item 7)")
        if event == "start":
            protocol(number == len(history) + 1 and number <= MAX_ATTEMPTS,
                     f"Attempt log entry {entry['n']}: {run_name(arm, seed)} attempt {number} is not the next allowed attempt")
            protocol(not history or history[-1]["outcome"] is not None, f"Attempt log entry {entry['n']}: previous attempt still open")
            protocol(not any(a["outcome"] == "valid" for a in history), f"Attempt log entry {entry['n']}: arm already valid")
            protocol(seed in SLOTS and seed == slot or seed in RESERVE_QUEUE, f"Attempt log entry {entry['n']}: seed {seed} is not slot {slot}")
            protocol(not retired(seed), f"Attempt log entry {entry['n']}: seed {seed} is retired (replaced by a reserve)")
            if seed in RESERVE_QUEUE:
                protocol(recorded_slot.setdefault(seed, slot) == slot, f"Reserve seed {seed} reused for another slot")
            history.append({"attempt": number, "slot": slot, "outcome": None, "resumed": False, "detail": None})
            continue
        current = next((a for a in history if a["attempt"] == number), None)
        protocol(current is not None, f"Attempt log entry {entry['n']}: unknown attempt")
        if event == "finish":
            protocol(current["outcome"] is None and entry.get("outcome") in OUTCOMES, f"Attempt log entry {entry['n']}: bad finish")
            current.update(outcome=entry["outcome"], detail=entry.get("detail"))
        elif event == "resume_start":
            protocol(current["outcome"] == "infrastructure" and not current["resumed"], f"Attempt log entry {entry['n']}: bad resume")
            current.update(resumed=True, resume_outcome=None)
        elif event == "resume_finish":
            protocol(current["resumed"] and entry.get("outcome") in OUTCOMES, f"Attempt log entry {entry['n']}: bad resume finish")
            outcome = entry["outcome"]
            current["resume_outcome"] = "resumed_invalid" if outcome == "valid" else outcome
        else:
            raise ProtocolError(f"Attempt log entry {entry['n']}: unknown event {event!r}")

    halt_reasons = [f"{run_name(arm, seed)} attempt {a['attempt']}: {cls} failure ({a.get('detail') or 'see report'})"
                    for (seed, arm), history in sorted(attempts.items()) for a in history
                    for cls in (a["outcome"], a.get("resume_outcome")) if cls in ("numerical", "protocol")]

    # Amendment 2 item 4: slots settle in the order 11, 22, 33, so reserves are taken from the queue [44, 55] in
    # that same order; a reserve is never reused.
    slots, used = {}, []
    for slot in SLOTS:
        chain, status = [slot], None
        while retired(chain[-1]):
            reserve = next((r for r in RESERVE_QUEUE if r not in used), None)
            if reserve is None:
                status = "exhausted"
                break
            used.append(reserve)
            chain.append(reserve)
        seed = None if status == "exhausted" else chain[-1]
        arms = {arm: arm_state(seed, arm) for arm in ARM_ORDER} if seed is not None else {}
        if status is None:
            status = "complete" if all(state["valid_attempt"] is not None for state in arms.values()) else "open"
        slots[slot] = {"chain": chain, "seed": seed, "status": status, "arms": arms}
    for reserve, slot in recorded_slot.items():
        protocol(reserve in slots[slot]["chain"], f"Reserve seed {reserve} was trained for slot {slot} out of the "
                                                  "registered order (Amendment 2 item 4)")
    retained = [(slot, info["seed"]) for slot, info in slots.items() if info["status"] == "complete"]
    final = all(info["status"] in ("complete", "exhausted") for info in slots.values())
    return {"halted": bool(halt_reasons), "halt_reasons": halt_reasons, "slots": slots,
            "reserves_assigned": {seed: slot for slot, info in slots.items() for seed in info["chain"][1:]},
            "retained": retained, "final": final, "S": len(retained) if final else None, "identity": identity,
            "attempts": {f"{run_name(arm, seed)}": history for (seed, arm), history in sorted(attempts.items())}}


def plan(entries):
    """Seed slots, reserves and attempt states from the attempt log (Amendment 1 items 11-12, Amendment 2 items 4, 7).

    Besides the structure checks, every start must be exactly the run the plan authorised at that point (slot order
    11 -> 22 -> 33, arms EC -> ER -> EE, reserves 44 then 55), and every attempt must carry the same configuration
    and implementation identity. Anything else is a ProtocolError."""
    for index, entry in enumerate(entries):
        if entry.get("event") not in ("start", "resume_start"):
            continue
        before = _replay(entries[:index])
        protocol(not before["halted"], f"Attempt log entry {entry.get('n')}: new training after the study halted")
        try:
            expected = next_run(before)
        except Refused as error:
            raise ProtocolError(f"Attempt log entry {entry.get('n')}: no run was authorised ({error})") from None
        protocol(expected["kind"] == "train", f"Attempt log entry {entry.get('n')}: every slot was already settled")
        attempt = expected["attempt"] - (1 if entry["event"] == "resume_start" else 0)
        protocol((entry.get("arm"), entry.get("seed"), entry.get("slot"), entry.get("attempt")) ==
                 (expected["arm"], expected["seed"], expected["slot"], attempt),
                 f"Attempt log entry {entry.get('n')}: {entry.get('event')} {entry.get('arm')} seed {entry.get('seed')} "
                 f"slot {entry.get('slot')} attempt {entry.get('attempt')} is out of the registered order; the plan "
                 f"authorised {expected['arm']} seed {expected['seed']} slot {expected['slot']} (Amendment 2 item 4)")
    return _replay(entries)


def next_run(current):
    """Amendment 2 item 4: the next pending run of the plan, never the operator's choice.

    Slots 11 -> 22 -> 33, arms EC -> ER -> EE within a slot; a slot is fully settled (complete, or exhausted after
    its reserves) before the next starts. Returns {"kind": "train", ...} or {"kind": "complete", ...}; raises
    StudyHalted after a numerical/protocol failure and Refused while an attempt is still open."""
    if current["halted"]:
        raise StudyHalted(HALT_MESSAGE + "\n- " + "\n- ".join(current["halt_reasons"]))
    for slot in SLOTS:
        info = current["slots"][slot]
        if info["status"] in ("complete", "exhausted"):
            continue
        seed = info["seed"]
        for arm in ARM_ORDER:
            state = info["arms"][arm]
            if state["valid_attempt"] is not None:
                continue
            if state["open"]:
                raise Refused(open_attempt_message(open_attempts(current)))
            number = len(state["attempts"]) + 1
            protocol(number <= MAX_ATTEMPTS, "Attempt limit reached without retirement (log inconsistent)")
            return {"kind": "train", "slot": slot, "seed": seed, "arm": arm, "attempt": number, "retry": number > 1,
                    "reserve": seed in RESERVE_QUEUE}
    return {"kind": "complete", "S": current["S"], "retained": current["retained"]}


def resume_target(current, action, train_root):
    """Engineering-only resume (never valid): the previous, infrastructure-failed attempt of the pending run, if it
    left a checkpoint and was not resumed before; otherwise None."""
    if action.get("kind") != "train" or action["attempt"] < 2:
        return None
    state = current["slots"][action["slot"]]["arms"][action["arm"]]
    last = state["attempts"][-1]
    if last["outcome"] != "infrastructure" or last["resumed"]:
        return None
    if not (attempt_dir(train_root, action["arm"], action["seed"], last["attempt"]) / "checkpoint").is_dir():
        return None
    return last["attempt"]


# ---------------------------------------------------------------- single writer per training root (Amendment 3 item 2; B4)

def utc():
    return datetime.now(timezone.utc).isoformat()


def read_writer_lock(train_root):
    """The WRITER.lock content of ``train_root`` (dict), {"unreadable": ...} if it cannot be parsed, or None."""
    path = Path(train_root) / WRITER_LOCK
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        content = json.loads(text)
        return content if isinstance(content, dict) else {"unreadable": text[:200]}
    except ValueError:
        return {"unreadable": text[:200]}


def heartbeat_age(holder):
    """Seconds since the holder's last heartbeat, or None (informational only: a lock never expires by age)."""
    try:
        return max(0.0, (datetime.now(timezone.utc) - datetime.fromisoformat(holder["heartbeat_at"])).total_seconds())
    except (KeyError, TypeError, ValueError):
        return None


def describe_writer(train_root):
    holder = read_writer_lock(train_root)
    if holder is None:
        return "Training-root writer lock: free (no session is writing this training root)."
    age = heartbeat_age(holder)
    return (f"Training-root writer lock HELD by session {holder.get('session_id')} (host {holder.get('host')}, pid "
            f"{holder.get('pid')}) since {holder.get('acquired_at')}; last heartbeat {holder.get('heartbeat_at')}"
            + (f" ({age:.0f} s ago)" if age is not None else "") + ".")


def writer_held_message(train_root):
    return (describe_writer(train_root) + " Only one session may write a training root (PREREGISTRATION Amendment 3 "
            "item 2); no attempt was opened. If another Colab session is still loading or training, wait for it. A lock "
            "never expires by itself, whatever its heartbeat age. Only after confirming that NO other session is running "
            "the trainer, set RECOVER_STALE_WRITER = True (CLI: --recover-stale-writer) and re-run: the recovery is "
            "logged, any open attempt is closed as an infrastructure failure and the lock is released.")


class WriterLock:
    """The single writer of a training root (Amendment 3 item 2). ``WRITER.lock`` is created exclusively and records
    the session ID, host, pid and a heartbeat that a background thread refreshes every ``heartbeat_seconds`` while
    the session runs. Another session's lock is never taken over or expired automatically: only
    recover_stale_writer(), with the operator's confirmation, removes it. Limitation: the exclusive create is atomic
    on one filesystem; across two Colab VMs sharing Drive it is cooperative (Drive sync is eventual), which is why
    the heartbeat is shown to the operator and recovery needs an explicit confirmation."""

    def __init__(self, train_root, session_id=None, heartbeat_seconds=HEARTBEAT_SECONDS):
        self.root = Path(train_root)
        self.path = self.root / WRITER_LOCK
        self.session_id = session_id or uuid.uuid4().hex
        self.heartbeat_seconds = heartbeat_seconds
        self.heartbeat_error = None
        self.content = None
        self._stop = threading.Event()
        self._thread = None

    def acquire(self):
        self.root.mkdir(parents=True, exist_ok=True)
        now = utc()
        content = {"schema": WRITER_SCHEMA, "session_id": self.session_id, "host": socket.gethostname(),
                   "pid": os.getpid(), "acquired_at": now, "heartbeat_at": now, "heartbeats": 0,
                   "rule": "PREREGISTRATION Amendment 3 item 2: one writer per training root"}
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            raise Refused(writer_held_message(self.root)) from None
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(content, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.content = content
        if self.heartbeat_seconds:
            self._thread = threading.Thread(target=self._beat_forever, name="writer-heartbeat", daemon=True)
            self._thread.start()
        return self

    def owned(self):
        holder = read_writer_lock(self.root)
        return holder is not None and holder.get("session_id") == self.session_id

    def beat(self):
        """Refresh the heartbeat; False (and no write) once the lock is no longer this session's."""
        if self.content is None or not self.owned():
            return False
        content = dict(self.content, heartbeat_at=utc(), heartbeats=self.content["heartbeats"] + 1)
        temporary = self.path.with_name(f"{WRITER_LOCK}.{self.session_id}.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(content, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)
        self.content = content
        return True

    def _beat_forever(self):
        while not self._stop.wait(self.heartbeat_seconds):
            try:
                if not self.beat():
                    return
            except OSError as error:  # a Drive hiccup: keep the lock, report it
                self.heartbeat_error = f"{type(error).__name__}: {error}"

    def release(self):
        """Stop the heartbeat and remove the lock if (and only if) it is still this session's."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        if self.content is not None and self.owned():
            self.path.unlink(missing_ok=True)
            return True
        return False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
        return False


def open_attempts(current):
    """[(arm, seed, slot, attempt, closing event)] of every start/resume_start without a recorded outcome."""
    pending = []
    for name, history in current["attempts"].items():
        arm, seed = name.split("-s")[0], int(name.split("-s")[1])
        for item in history:
            if item["outcome"] is None:
                pending.append((arm, seed, item["slot"], item["attempt"], "finish"))
            elif item["resumed"] and item.get("resume_outcome") is None:
                pending.append((arm, seed, item["slot"], item["attempt"], "resume_finish"))
    return pending


def open_attempt_message(pending):
    names = ", ".join(f"{run_name(arm, seed)} attempt {attempt}" for arm, seed, _, attempt, _ in pending)
    return (f"{names} has a start without a recorded outcome. Another session may still be loading or training it: an "
            "open attempt is never treated as abandoned automatically (PREREGISTRATION Amendment 3 item 2). Only after "
            "confirming that no other Colab session is running the trainer, set RECOVER_STALE_WRITER = True (CLI: "
            "--recover-stale-writer) and re-run; the attempt is then closed as an infrastructure failure.")


def reconcile(train_root, *, confirmed_no_other_session=False, session_id=None, stale_session=None):
    """Close the attempts left open (start without finish) — only with the operator's confirmation that no other
    session is running (Amendment 3 item 2); without it, any open attempt is refused, never closed.

    A confirmed open attempt is closed as an infrastructure failure (runtime disconnect or kill), unless its own
    report already records a numerical or protocol failure: that class is kept, so a recovery can never turn a
    halting failure into a retry. Returns the appended entries (empty when nothing is open)."""
    log = Path(train_root) / ATTEMPT_LOG
    pending = open_attempts(plan(read_log(log)))
    if not pending:
        return []
    if confirmed_no_other_session is not True:
        raise Refused(open_attempt_message(pending))
    closed = []
    for arm, seed, slot, attempt, event in pending:
        folder = attempt_dir(train_root, arm, seed, attempt)
        reported, detail = attempt_outcome(folder)
        outcome = reported if reported in ("numerical", "protocol") else "infrastructure"
        note = (f"the attempt's own report records a {reported} failure, which keeps its class ({detail})"
                if outcome != "infrastructure" else f"runtime disconnect or kill; report on disk: {detail}")
        closed.append(log_event(log, event, arm=arm, seed=seed, slot=slot, attempt=attempt, outcome=outcome,
                                detail="stale-writer recovery confirmed by the operator (no other session running): " + note,
                                report_sha256=report_sha(folder),
                                recovery={"recovering_session": session_id, "stale_session": stale_session}))
    return closed


def recover_stale_writer(train_root, *, confirmed_no_other_session=False, session_id=None):
    """Amendment 3 item 2: after a killed runtime, with the operator's confirmation that no other session is running
    (RECOVER_STALE_WRITER = True): log the recovery (WRITER_RECOVERIES.jsonl, timestamped), close every open attempt
    (reconcile), then release the stale lock. Returns the record, or None when there is nothing to recover."""
    if confirmed_no_other_session is not True:
        raise Refused("Recovering a stale writer needs the operator's explicit confirmation that no other session is "
                      "running (RECOVER_STALE_WRITER = True); nothing was changed.")
    root = Path(train_root)
    holder = read_writer_lock(root)
    pending = open_attempts(plan(read_log(root / ATTEMPT_LOG)))
    if holder is None and not pending:
        print("RECOVER_STALE_WRITER: no writer lock and no open attempt; nothing to recover.", flush=True)
        return None
    session_id = session_id or uuid.uuid4().hex
    record = {"event": "stale_writer_recovered", "at": utc(), "recovering_session": session_id,
              "host": socket.gethostname(), "pid": os.getpid(), "operator_confirmed_no_other_session": True,
              "stale_lock": holder, "stale_heartbeat_age_seconds": heartbeat_age(holder) if holder else None,
              "open_attempts": [f"{run_name(arm, seed)} attempt {attempt}" for arm, seed, _, attempt, _ in pending],
              "rule": "PREREGISTRATION Amendment 3 item 2: logged, the open attempt closed as an infrastructure "
                      "failure, then the stale lock released; no retry or reserve rule changes"}
    root.mkdir(parents=True, exist_ok=True)
    with (root / WRITER_RECOVERIES).open("a", encoding="utf-8") as stream:  # logged first
        stream.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    closed = reconcile(root, confirmed_no_other_session=True, session_id=session_id,
                       stale_session=(holder or {}).get("session_id"))
    (root / WRITER_LOCK).unlink(missing_ok=True)  # released last
    for entry in closed:
        print(f"RECOVER_STALE_WRITER: closed {run_name(entry['arm'], entry['seed'])} attempt {entry['attempt']} -> "
              f"{entry['outcome']}", flush=True)
    print(f"RECOVER_STALE_WRITER: recovery logged in {WRITER_RECOVERIES}; stale lock "
          f"{'of session ' + str(holder.get('session_id')) + ' ' if holder else ''}released.", flush=True)
    return dict(record, closed=closed)


def report_sha(folder):
    path = Path(folder) / "train_report.json"
    return ts.file_sha256(path) if path.is_file() else None


def describe_plan(current):
    """Plain-text attempt log and slot table for the notebook (no model outputs involved)."""
    lines = ["Attempt log (Amendment 1 item 11):"]
    for name, history in current["attempts"].items():
        for a in history:
            resumed = f", resumed -> {a.get('resume_outcome')}" if a["resumed"] else ""
            lines.append(f"  {name} attempt {a['attempt']} (slot {a['slot']}): {a['outcome'] or 'OPEN'}{resumed}"
                         + (f" — {a['detail']}" if a.get("detail") else ""))
    if len(lines) == 1:
        lines.append("  (no attempts yet)")
    lines.append("Seed slots:")
    for slot, info in current["slots"].items():
        arms = ", ".join(f"{arm} {'valid #' + str(s['valid_attempt']) if s['valid_attempt'] else str(s['failed']) + ' failed'}"
                         for arm, s in info["arms"].items())
        lines.append(f"  slot {slot}: seeds {info['chain']} -> {info['status']}" + (f" ({arms})" if arms else ""))
    if current["halted"]:
        lines.append("STUDY HALTED: " + "; ".join(current["halt_reasons"]))
    elif current["final"]:
        lines.append(f"All slots settled: S = {current['S']} retained seeds {[seed for _, seed in current['retained']]}")
    else:
        try:
            action = next_run(current)
            lines.append(f"Next run (Amendment 2 item 4): {action['arm']} seed {action['seed']} (slot {action['slot']}"
                         f"{', reserve' if action['reserve'] else ''}) attempt {action['attempt']}")
        except Refused as error:
            lines.append(f"Next run: none while an attempt is open ({error})")
    return "\n".join(lines)


# ---------------------------------------------------------------- training run

def fail_report(report, report_path, error, stage):
    cls = classify_failure(error, stage)
    report.update(status="FAILED", failure_stage=stage, failure_class=cls,
                  failure_kind=infrastructure_kind(error) if cls == "infrastructure" else None,
                  error_type=f"{type(error).__module__}.{type(error).__qualname__}",
                  error="".join(traceback.format_exception(error)), valid_for_gate=False)
    if cls in ("numerical", "protocol"):
        report["study_halt"] = True
    print(report["error"], file=sys.stderr, flush=True)
    try:
        ts.write_json(report_path, report)
    except OSError as write_error:  # the attempt log still records the class from memory
        print(f"Could not write {report_path}: {write_error}", file=sys.stderr, flush=True)
    return report


def announce(report):
    cls = report.get("failure_class")
    if cls in ("numerical", "protocol"):
        print(f"\n{cls.upper()} FAILURE. " + HALT_MESSAGE, file=sys.stderr, flush=True)
    elif cls == "infrastructure":
        print(f"\nINFRASTRUCTURE FAILURE ({report.get('failure_kind')}): at most one from-scratch retry with the same "
              "seed (Amendment 1 item 11).", file=sys.stderr, flush=True)
    return EXIT_CODES[cls] if cls else 0


def report_outcome(report):
    """(outcome, detail) of an attempt from its in-memory report (the same rules as attempt_outcome)."""
    status = report.get("status")
    if status == "COMPLETE":
        final = report.get("final_adapter")
        if not final:
            return "infrastructure", "final adapter record missing (failed save)"
        if final.get("resumed"):
            return "resumed_invalid", "completed after a resume from a checkpoint: never valid for the gate"
        problems = valid_run_problems(final)
        return ("protocol", "; ".join(problems)) if problems else ("valid", "COMPLETE: 60/60 successful steps, cursor 960")
    if status == "FAILED":
        failure = report.get("failure_class")
        detail = (report.get("error") or "").strip().splitlines()[-1:] or [""]
        return (failure if failure in FAILURE_CLASSES else "protocol"), detail[0][:300]
    return "infrastructure", f"run did not finish (status {status}): runtime disconnect or crash"


def preflight(arguments):
    """Everything that must hold before an attempt opens; nothing is logged here. The caller holds the writer lock.

    An attempt left open is never closed here (Amendment 3 item 2): next_run refuses until the operator confirmed a
    stale-writer recovery. Returns (spec, out, identity, resume) or {"kind": "complete"}; raises StudyHalted,
    Refused, ProtocolError or OSError."""
    train_root, inputs = Path(arguments.train_root), Path(arguments.inputs)
    log = train_root / ATTEMPT_LOG
    current = plan(read_log(log))
    print(describe_plan(current), flush=True)
    action = next_run(current)  # Amendment 2 item 4: the plan, never the operator, chooses the run
    if action["kind"] == "complete":
        return action
    resume, attempt = bool(arguments.resume), action["attempt"]
    if resume:
        attempt = resume_target(current, action, train_root)
        if attempt is None:
            raise Refused(f"No infrastructure-failed attempt of {run_name(action['arm'], action['seed'])} with a checkpoint "
                          "can be resumed; start a fresh attempt instead.")
    spec = dict(action, attempt=attempt)
    given = (arguments.arm, arguments.seed, arguments.slot, arguments.attempt)
    authorised = (spec["arm"], spec["seed"], spec["slot"], attempt)
    if any(value is not None and value != expected for value, expected in zip(given, authorised)):
        raise Refused(f"The attempt plan authorises {spec['arm']} seed {spec['seed']} slot {spec['slot']} attempt {attempt}, "
                      f"not {given} (Amendment 2 item 4).")
    out = attempt_dir(train_root, spec["arm"], spec["seed"], attempt)
    if not resume and any((out / name).exists() for name in ("train_report.json", "final_adapter.json", "final_adapter", "checkpoint")):
        raise Refused(f"{out} already holds attempt evidence: attempts are never overwritten.")
    baseline = verify_baseline(arguments.baseline_dir, inputs / MANIFEST_NAME)  # Amendment 2 item 6, Amendment 3 item 3
    identity = attempt_identity(inputs, baseline)
    if current["identity"] is not None and current["identity"] != identity:  # Amendment 2 item 7
        changed = sorted(key for key in set(identity) | set(current["identity"]) if identity.get(key) != current["identity"].get(key))
        raise Refused("Configuration or implementation differs from earlier attempts (Amendment 2 item 7): " + ", ".join(changed))
    check_stack()  # Amendment 2 item 3: exact stack on a T4, before the attempt opens
    return spec, out, identity, resume


def run_train(arguments):
    """One training session: the single writer of the training root (Amendment 3 item 2) from before the plan is
    read until after the outcome is logged."""
    writer = None
    try:
        if getattr(arguments, "recover_stale_writer", False):
            print("RECOVER_STALE_WRITER: the operator confirmed that no other session is running the trainer.", flush=True)
            recover_stale_writer(arguments.train_root, confirmed_no_other_session=True)
        writer = WriterLock(arguments.train_root).acquire()
        print(f"Training-root writer lock acquired: session {writer.session_id} (heartbeat every {HEARTBEAT_SECONDS} s)",
              flush=True)
        return _train_as_writer(arguments, writer)
    except Refused as error:
        print("REFUSED (no attempt was opened): " + str(error), file=sys.stderr, flush=True)
        return EXIT_CODES["refused"]
    except ProtocolError as error:  # e.g. an edited attempt log met during a recovery
        print("PROTOCOL ERROR before any attempt was opened: " + str(error) + "\n" + HALT_MESSAGE, file=sys.stderr, flush=True)
        return EXIT_CODES["protocol"]
    except OSError as error:
        print(f"Infrastructure error before any attempt was opened (writer lock or recovery; re-run): "
              f"{type(error).__name__}: {error}", file=sys.stderr, flush=True)
        return EXIT_CODES["infrastructure"]
    finally:
        if writer is not None:
            writer.release()


def _train_as_writer(arguments, writer):
    try:
        prepared = preflight(arguments)
    except StudyHalted as error:
        print(str(error), file=sys.stderr, flush=True)
        return EXIT_CODES["refused"]
    except Refused as error:
        print("REFUSED (no attempt was opened): " + str(error), file=sys.stderr, flush=True)
        return EXIT_CODES["refused"]
    except ProtocolError as error:
        print("PROTOCOL ERROR before any attempt was opened: " + str(error) + "\n" + HALT_MESSAGE, file=sys.stderr, flush=True)
        return EXIT_CODES["protocol"]
    except OSError as error:
        print(f"Infrastructure error before any attempt was opened (nothing was logged; re-run): {type(error).__name__}: "
              f"{error}", file=sys.stderr, flush=True)
        return EXIT_CODES["infrastructure"]
    if isinstance(prepared, dict):
        print(f"Every seed slot is settled: S = {prepared['S']}; nothing to train.", flush=True)
        return 0
    spec, out, identity, resume = prepared
    log = Path(arguments.train_root) / ATTEMPT_LOG
    keys = {key: spec[key] for key in ("arm", "seed", "slot", "attempt")}
    out.mkdir(parents=True, exist_ok=True)
    log_event(log, "resume_start" if resume else "start", **keys, identity=identity, writer_session=writer.session_id)
    report = train_attempt(spec, out, Path(arguments.inputs), identity, resume, writer_session=writer.session_id)
    outcome, detail = report_outcome(report)
    if not writer.owned():  # another session recovered this root meanwhile: never append a conflicting outcome
        print(f"WRITER LOCK LOST: the training root no longer belongs to session {writer.session_id} (a stale-writer "
              "recovery closed this attempt); its outcome is NOT logged again. Send the ZIP.", file=sys.stderr, flush=True)
        return EXIT_CODES["infrastructure"]
    log_event(log, "resume_finish" if resume else "finish", **keys, outcome=outcome, detail=detail,
              report_sha256=report_sha(out))
    print(f"{run_name(spec['arm'], spec['seed'])} attempt {spec['attempt']} (slot {spec['slot']}): {outcome} — {detail}", flush=True)
    return 0 if report["status"] == "COMPLETE" else announce(report)


def train_attempt(spec, out, inputs, identity, resume, writer_session=None):
    """One opened attempt. Never raises for a training failure: it returns the report with the failure class.

    The STARTED report is persisted first, before any verification or model loading (Amendment 3 item 2)."""
    arm, seed, slot, attempt = spec["arm"], spec["seed"], spec["slot"], spec["attempt"]
    report_path = out / "train_report.json"
    previous = (ts.read_json(report_path) if report_path.is_file() else {}) if resume else None
    report = {"status": "STARTED", "arm": arm, "seed": seed, "slot": slot, "attempt": attempt, "oom": False,
              "recipe": RECIPE, "recipe_sha256": ts.digest(RECIPE), "order_rule": ORDER_RULE,
              "schedule_rule": SCHEDULE_RULE, "identity": identity,
              "implementation_manifest_sha256": identity["implementation_manifest_sha256"],
              "baseline_dev_results_zip_sha256": identity["baseline_dev_results_zip_sha256"],
              "failure_class": None, "valid_for_gate": False, "updates": [], "checkpoints": [], "resumes": [],
              "events": [], "steps": {"windows": RECIPE["updates"], "attempted": 0, "successful": 0, "cursor": 0},
              "writer_session": writer_session}
    if previous:  # --resume: keep the history, drop updates after the restored checkpoint later
        report.update({key: previous[key] for key in ("updates", "checkpoints", "resumes", "events") if key in previous})
        report["initial_adapter_sha256"] = previous.get("initial_adapter_sha256")
    report["events"].append({"event": "process_start", "resume": previous is not None, "at": time.time()})
    stage = "start"
    try:
        ts.write_json(report_path, report)  # Amendment 3 item 2: STARTED is on disk before anything is loaded
        stage = "verify"
        manifest, manifest_sha = verify_implementation(inputs)  # Amendment 2 item 7, at the executable boundary
        require(manifest_sha == identity["implementation_manifest_sha256"], "Implementation manifest changed after the attempt opened")
        stage = "data"
        data = load_verified_train(inputs)
        families = data["families"]
        order, exposure_sha = verify_exposure(inputs, data, seed)
        require(exposure_sha == identity["exposure_order_file_sha256"], "EXPOSURE_ORDER.json changed after the attempt opened")
        report.update(data_sha256=data["families_sha256"], order_sha256=order, exposure_order_file_sha256=exposure_sha,
                      implementation_verified={"manifest_sha256": manifest_sha, "trainer_code": list(TRAINER_CODE),
                                               "train_files": dict(ts.TRAIN_FILES), "exposure_order_sha256": exposure_sha})
        stage = "setup"
        torch, mismatches = ts.gpu_setup(False)  # Amendment 2 item 3: no override exists
        require(not mismatches, "D021 stack mismatch inside the attempt: " + "; ".join(mismatches))
        report["environment"] = ts.environment(torch, mismatches)
    except (Exception, KeyboardInterrupt, SystemExit) as error:
        fail_report(report, report_path, error, stage)
        return report
    sampler = ts.MemorySampler().start()
    report["nvml_sampler_error"] = sampler.error
    trainer = None
    try:
        stage = "hub"
        report["hub_files_sha256"] = verify_hub_files(manifest)  # B2: the downloaded tokenizer/config bytes
        stage = "tokenizer"
        tokenizer = ts.load_tokenizer()
        report["chat_template_sha256"] = verify_chat_template(tokenizer, manifest)  # B2: the loaded template
        stage = "labels"
        examples, audit = prepare_examples(tokenizer, families)
        report["mask_audit"] = {key: audit[key] for key in ("passed", "arms", "max_input_tokens", "last_target_is_im_end")}
        sequence = run_examples(examples, families, arm, seed)
        stage = "model"
        ts.seed_everything(torch, seed)
        torch.cuda.reset_peak_memory_stats()
        model, trainable, keep, report["model"] = load_model(torch, seed)
        report["base_weight_shards_sha256"] = weight_shard_hashes()
        report["load_min_free_bytes"] = min(v for v in (sampler.take(), torch.cuda.mem_get_info()[0]) if v is not None)
        initial = ts.tensors_digest(trainable)
        protocol(report.get("initial_adapter_sha256") in (None, initial), "Initial adapter differs from the first process")
        report["initial_adapter_sha256"] = initial
        trainer = Phase2Trainer(torch, model, trainable, keep, sequence, sampler)
        report["grad_scaler"] = {"settings": SCALER, "state": trainer.scaler.state_dict()}
        probe_example = sequence[0]
        completed = 0
        if previous is not None:
            stage = "reload"
            completed, check = restore_checkpoint(torch, trainer, out, report)
            report["resumes"].append(check)
            report["updates"] = [record for record in report["updates"] if record["update"] <= completed]
        for number in range(completed + 1, RECIPE["updates"] + 1):
            stage = "training"
            try:
                record = trainer.update(number)
            except NumericalFailure as failure:
                report["failed_update"] = failure.record
                raise
            finally:
                report["steps"] = trainer.steps()
            report["updates"].append(record)
            if number % RECIPE["checkpoint_every"] == 0 and number < RECIPE["updates"]:
                stage = "checkpoint"
                save_checkpoint(torch, trainer, out, number, probe_example, report)
            with checkpoint_write("training report"):
                ts.write_json(report_path, report)
        stage = "final"
        steps = trainer.steps()
        protocol(steps == {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960},
                 f"A valid run needs 60 windows, 60 attempted and 60 successful steps and cursor 960; found {steps}")
        final = save_final_adapter(torch, trainer, out)
        resumed = bool(report["resumes"])
        final.update(arm=arm, seed=seed, slot=slot, attempt=attempt, status="COMPLETE", updates=RECIPE["updates"],
                     steps=steps, scaler_skips=0, recipe_sha256=report["recipe_sha256"], data_sha256=report["data_sha256"],
                     order_sha256=report["order_sha256"], exposure_order_file_sha256=report["exposure_order_file_sha256"],
                     initial_adapter_sha256=initial, resumed=resumed, valid_for_gate=not resumed,
                     implementation_manifest_sha256=identity["implementation_manifest_sha256"],
                     baseline_dev_results_zip_sha256=identity["baseline_dev_results_zip_sha256"],
                     identity_sha256=ts.digest(identity), base_model=ts.MODEL_ID, base_revision=ts.MODEL_REVISION,
                     base_weight_shards_sha256=report["base_weight_shards_sha256"])
        report["final_adapter"] = final
        with checkpoint_write("final adapter record"):
            ts.write_json(out / "final_adapter.json", final)
        shutil.rmtree(out / "checkpoint", ignore_errors=True)  # optimizer state is not needed after update 60
        report["status"] = "COMPLETE"
        report["valid_for_gate"] = not resumed
        print(f"final adapter SHA-256 {final['adapter_model_sha256']} (config {final['adapter_config_sha256']})", flush=True)
        if resumed:
            print("This run was RESUMED: it is never valid for the FinalTest gate (Amendment 1 item 11).", flush=True)
    except (Exception, KeyboardInterrupt, SystemExit) as error:
        report["oom"] = is_cuda_oom(error)
        fail_report(report, report_path, error, stage)
    finally:
        sampler.stop()
        if trainer is not None:
            report["steps"] = trainer.steps()
        report["summary"] = ts.summarize_updates(report["updates"], warmup=0, resume_after=0)
        report["events"].append({"event": "process_end", "status": report["status"], "at": time.time()})
        try:
            ts.write_json(report_path, report)
        except OSError as error:
            print(f"Could not write {report_path}: {error}", file=sys.stderr, flush=True)
    print(f"{arm} seed {seed} attempt {attempt}: {report['status']} — steps {report['steps']}", flush=True)
    return report


# ---------------------------------------------------------------- pairing check (model-free)

def pairing(records):
    """``records``: final_adapter.json dicts. Within each seed, all arms must share order and initial adapter."""
    by_seed = {}
    for record in records:
        by_seed.setdefault(record["seed"], []).append(record)
    result = {}
    for seed, group in sorted(by_seed.items()):
        result[seed] = {"arms": sorted(r["arm"] for r in group),
                        "same_order": len({r["order_sha256"] for r in group}) == 1,
                        "same_initial_adapter": len({r["initial_adapter_sha256"] for r in group}) == 1}
    return result


def run_pairing(arguments):
    records = [ts.read_json(path) for path in sorted(Path(arguments.train_root).glob("*-s*/attempt-*/final_adapter.json"))]
    result = pairing(records)
    print(json.dumps(result, indent=2))
    return 0 if all(r["same_order"] and r["same_initial_adapter"] for r in result.values()) else 1


def run_exposure_order(arguments):
    root = Path(arguments.root)
    text = exposure_text(phase2_dataset(root))
    target = root / EXPOSURE_ORDER_PATH
    if arguments.check:
        current = target.is_file() and target.read_text(encoding="utf-8") == text
        print(target, "is current" if current else "is MISSING or STALE: regenerate it before training")
        return 0 if current else 1
    target.write_text(text, encoding="utf-8")
    print(target, ts.sha256(text.encode("utf-8")))
    return 0


def run_plan(arguments):
    print(describe_plan(plan(read_log(Path(arguments.train_root) / ATTEMPT_LOG))))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Phase-2 QLoRA training (D043, Amendments 1 and 2)")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Run the next pending run of the attempt plan (Amendment 2 item 4)")
    train.add_argument("--train-root", type=Path, required=True, help="Folder of ATTEMPT_LOG.jsonl and the attempt folders")
    train.add_argument("--inputs", type=Path, required=True,
                       help="Folder with IMPLEMENTATION_MANIFEST.md, EXPOSURE_ORDER.json and the frozen TRAIN files")
    train.add_argument("--baseline-dir", type=Path, required=True,
                       help="Folder of the complete unchanged-model DEV run (Amendment 2 item 6)")
    train.add_argument("--arm", choices=sorted(ARMS), help="Optional: assert the run the plan authorises")
    train.add_argument("--seed", type=int, choices=SLOTS + RESERVE_QUEUE)
    train.add_argument("--slot", type=int, choices=SLOTS)
    train.add_argument("--attempt", type=int)
    train.add_argument("--resume", action="store_true", help="Engineering only: continue from the checkpoint; never valid")
    train.add_argument("--recover-stale-writer", action="store_true",
                       help="Only after confirming that no other session runs the trainer (Amendment 3 item 2): log the "
                            "recovery, close an open attempt as infrastructure and release the stale writer lock")
    commands.add_parser("pairing").add_argument("--train-root", type=Path, required=True)
    commands.add_parser("plan").add_argument("--train-root", type=Path, required=True)
    exposure = commands.add_parser("exposure-order")
    exposure.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    exposure.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    return {"train": run_train, "pairing": run_pairing, "plan": run_plan,
            "exposure-order": run_exposure_order}[arguments.command](arguments)


if __name__ == "__main__":
    sys.exit(main())
