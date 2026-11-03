"""Phase-2 QLoRA training for Qwen3-4B (D043; binding plan phase2/PREREGISTRATION.md §3 with Amendment 1).

Reuses the GPU-verified D021 smoke code (train_smoke.py: labels, model load, digests, memory sampler) without
modifying it. New here: the frozen exposure order (Amendment 1 item 9), the learning-rate schedule, the run seed,
the numerical-failure contract and pinned GradScaler (item 10), failure classes and the append-only attempt log
with the seed/reserve plan (item 11), checkpoints and the final adapter.

  python3 t4_smoke/train_phase2.py exposure-order --root . [--check]     # write / verify phase2/EXPOSURE_ORDER.json
  python3 t4_smoke/train_phase2.py train --arm EC --seed 11 --slot 11 --attempt 1 --data phase2_train.json \
      --exposure-order EXPOSURE_ORDER.json --out RUN_DIR [--implementation-manifest-sha256 SHA]
  python3 t4_smoke/train_phase2.py train ... --resume      # engineering only: a resumed run is never valid (item 11)
  python3 t4_smoke/train_phase2.py plan --train-root TRAIN_ROOT       # attempt log, seed slots and reserves
  python3 t4_smoke/train_phase2.py pairing --train-root TRAIN_ROOT

Training reads only the two frozen TRAIN files (hash-checked) or the data file built from them, plus the frozen
exposure order. It never reads DEV or FINAL_TEST. Model-free parts use the standard library only; torch,
transformers, bitsandbytes and PEFT are imported lazily inside the GPU commands.
"""
import argparse
import json
import math
import os
import random
import shutil
import sys
import time
import traceback
from pathlib import Path

try:
    from . import train_smoke as ts
except ImportError:  # run as a script: python3 t4_smoke/train_phase2.py
    import train_smoke as ts

ARMS = ts.ARMS  # EE/ER/EC -> second rendering; the first is always E
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
EXPOSURE_SCHEMA = "phase2-exposure-order-1"
FAILURE_CLASSES = ("infrastructure", "numerical", "protocol")
OUTCOMES = ("valid", "resumed_invalid") + FAILURE_CLASSES
EXIT_CODES = {"refused": 2, "infrastructure": 1, "numerical": 3, "protocol": 4}
ATTEMPT_LOG = "ATTEMPT_LOG.jsonl"
HALT_MESSAGE = ("THE STUDY HALTS (PREREGISTRATION Amendment 1 items 10-11): this run is INVALID. No retry and no "
                "reserve seed. Send the ZIP; any repair needs a dated amendment before any further training.")

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


class ProtocolFailure(Exception):
    """Hash, data, exposure-order, label or step-count assertion failure (Amendment 1 item 11)."""


class StudyHalted(Exception):
    """A numerical or protocol failure was logged: no further training, no reserve (Amendment 1 item 11)."""


class Refused(Exception):
    """The attempt log does not allow this training run."""


def require(condition, message):
    ts.require(condition, message)


def protocol(condition, message):
    if not condition:
        raise ProtocolFailure(message)


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


def save_checkpoint(torch, trainer, out, completed, probe_example, report):
    """train_smoke.save, generalised to any update; written atomically, only the latest is kept."""
    bad = nonfinite_tensors(torch, trainer.trainable)
    if bad:
        raise NumericalFailure(f"non-finite adapter parameter(s) after update {completed}: {bad[:3]}")
    temporary, folder, old = out / "checkpoint.tmp", out / "checkpoint", out / "checkpoint.old"
    shutil.rmtree(temporary, ignore_errors=True)
    temporary.mkdir(parents=True)
    probe = trainer.probe(probe_example)
    trainer.model.save_pretrained(temporary / "adapter", save_embedding_layers=False)
    state = {"adapter": {name: parameter.detach().cpu().clone() for name, parameter in trainer.trainable},
             "optimizer": trainer.optimizer.state_dict(), "scaler": trainer.scaler.state_dict(),
             "rng_torch": torch.get_rng_state(), "rng_cuda": torch.cuda.get_rng_state(), "probe_logits": probe}
    torch.save(state, temporary / "state.pt")
    meta = checkpoint_meta(trainer, completed, report)
    meta.update(probe_item=f"{probe_example['family_id']}-{probe_example['form']}",
                digests=ts.state_digests(torch, trainer.trainable, trainer.optimizer, trainer.scaler))
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
    """train_smoke.restore, generalised: fresh model, then state, exact digests and the saved probe logits."""
    folder = out / "checkpoint"
    meta = ts.read_json(folder / "meta.json")
    for key in ("recipe_sha256", "data_sha256", "arm", "seed", "attempt", "order_sha256", "initial_adapter_sha256"):
        expected = ts.digest(RECIPE) if key == "recipe_sha256" else report[key]
        require(meta[key] == expected, f"Checkpoint was made with a different {key}")
    require(meta["parameter_names"] == [name for name, _ in trainer.trainable], "Adapter parameter order changed")
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

PROTOCOL_STAGES = ("arguments", "data", "labels")
DETERMINISTIC_STAGES = ("model", "training")  # a plain assertion here is a protocol failure, not a transient one


def classify_failure(error, stage):
    """'numerical', 'protocol' or 'infrastructure' for an exception raised in ``stage`` of a training run."""
    if isinstance(error, NumericalFailure):
        return "numerical"
    if isinstance(error, ProtocolFailure) or stage in PROTOCOL_STAGES:
        return "protocol"
    if stage in DETERMINISTIC_STAGES and isinstance(error, (ValueError, AssertionError)):
        return "protocol"
    return "infrastructure"  # disconnect/crash, OOM, download, failed save or reload


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
        return (failure if failure in FAILURE_CLASSES else "infrastructure"), detail[0][:300]
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


def plan(entries):
    """Seed slots, reserves and attempt states from the attempt log (Amendment 1 items 11-12)."""
    attempts = {}  # (seed, arm) -> [{"attempt", "slot", "outcome", "resumed", "detail"}]
    recorded_slot = {}  # reserve seed -> slot it was trained for

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

    for entry in entries:
        event, arm, seed, slot, number = (entry.get(k) for k in ("event", "arm", "seed", "slot", "attempt"))
        protocol(arm in ARMS and seed in SLOTS + RESERVE_QUEUE and slot in SLOTS, f"Attempt log entry {entry.get('n')}: bad arm/seed/slot")
        history = attempts.setdefault((seed, arm), [])
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
            raise ProtocolFailure(f"Attempt log entry {entry['n']}: unknown event {event!r}")

    halt_reasons = [f"{run_name(arm, seed)} attempt {a['attempt']}: {cls} failure ({a.get('detail') or 'see report'})"
                    for (seed, arm), history in sorted(attempts.items()) for a in history
                    for cls in (a["outcome"], a.get("resume_outcome")) if cls in ("numerical", "protocol")]

    slots, assigned = {}, {}
    for slot in SLOTS:
        chain, status = [slot], None
        while retired(chain[-1]):
            reserve = next((r for r in RESERVE_QUEUE if recorded_slot.get(r) == slot and r not in chain), None)
            if reserve is None:
                reserve = next((r for r in RESERVE_QUEUE if r not in recorded_slot and r not in assigned), None)
            if reserve is None:
                status = "exhausted"
                break
            assigned[reserve] = slot
            chain.append(reserve)
        seed = None if status == "exhausted" else chain[-1]
        arms = {arm: arm_state(seed, arm) for arm in ARMS} if seed is not None else {}
        if status is None:
            status = "complete" if all(state["valid_attempt"] is not None for state in arms.values()) else "open"
        slots[slot] = {"chain": chain, "seed": seed, "status": status, "arms": arms}
    for reserve, slot in recorded_slot.items():
        protocol(reserve in slots[slot]["chain"], f"Reserve seed {reserve} was trained for slot {slot} out of order")
    retained = [(slot, info["seed"]) for slot, info in slots.items() if info["status"] == "complete"]
    final = all(info["status"] in ("complete", "exhausted") for info in slots.values())
    return {"halted": bool(halt_reasons), "halt_reasons": halt_reasons, "slots": slots,
            "reserves_assigned": {r: s for r, s in sorted({**assigned, **recorded_slot}.items())},
            "retained": retained, "final": final, "S": len(retained) if final else None,
            "attempts": {f"{run_name(arm, seed)}": history for (seed, arm), history in sorted(attempts.items())}}


def next_action(current, arm, slot):
    """What the Train notebook may do for ``arm`` in seed slot ``slot``: train (seed, attempt) or done."""
    require(arm in ARMS and slot in SLOTS, "ARM must be EE/ER/EC and SLOT one of 11/22/33")
    if current["halted"]:
        raise StudyHalted(HALT_MESSAGE + "\n- " + "\n- ".join(current["halt_reasons"]))
    info = current["slots"][slot]
    if info["status"] == "exhausted":
        raise Refused(f"Slot {slot}: seeds {info['chain']} each lost an arm after two infrastructure failures and no "
                      "reserve is left; this slot is dropped (S < 3, descriptive-only report, Amendment 1 item 12).")
    seed, state = info["seed"], info["arms"][arm]
    if state["valid_attempt"] is not None:
        return {"kind": "done", "seed": seed, "attempt": state["valid_attempt"]}
    if state["open"]:
        raise Refused(f"{run_name(arm, seed)} has an attempt without a recorded outcome; run reconcile first.")
    number = len(state["attempts"]) + 1
    require(number <= MAX_ATTEMPTS, "Attempt limit reached without retirement (log inconsistent)")
    return {"kind": "train", "seed": seed, "attempt": number, "retry": number > 1, "reserve": seed in RESERVE_QUEUE}


def reconcile(train_root):
    """Close every started attempt that has no outcome yet (e.g. after a runtime disconnect), from its folder."""
    log = Path(train_root) / ATTEMPT_LOG
    closed = []
    for name, history in plan(read_log(log))["attempts"].items():
        for item in history:
            arm, seed = name.split("-s")[0], int(name.split("-s")[1])
            folder = attempt_dir(train_root, arm, seed, item["attempt"])
            if item["outcome"] is None:
                outcome, detail = attempt_outcome(folder)
                closed.append(log_event(log, "finish", arm=arm, seed=seed, slot=item["slot"], attempt=item["attempt"],
                                        outcome=outcome, detail="reconciled: " + detail, report_sha256=report_sha(folder)))
            elif item["resumed"] and item.get("resume_outcome") is None:
                outcome, detail = attempt_outcome(folder)
                closed.append(log_event(log, "resume_finish", arm=arm, seed=seed, slot=item["slot"], attempt=item["attempt"],
                                        outcome=outcome, detail="reconciled: " + detail, report_sha256=report_sha(folder)))
    return closed


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
    return "\n".join(lines)


# ---------------------------------------------------------------- training run

def fail_report(report, report_path, error, stage):
    report.update(status="FAILED", failure_stage=stage, failure_class=classify_failure(error, stage),
                  error="".join(traceback.format_exception(error)), valid_for_gate=False)
    if report["failure_class"] == "numerical":
        report["study_halt"] = True
    print(report["error"], file=sys.stderr, flush=True)
    ts.write_json(report_path, report)
    return report


def announce(report):
    cls = report.get("failure_class")
    if cls in ("numerical", "protocol"):
        print(f"\n{cls.upper()} FAILURE. " + HALT_MESSAGE, file=sys.stderr, flush=True)
    elif cls == "infrastructure":
        print("\nINFRASTRUCTURE FAILURE: at most one from-scratch retry with the same seed (Amendment 1 item 11).",
              file=sys.stderr, flush=True)
    return EXIT_CODES[cls] if cls else 0


def run_train(arguments):
    arm, seed, attempt, slot = arguments.arm, arguments.seed, arguments.attempt, arguments.slot
    out = Path(arguments.out)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "train_report.json"
    if report_path.exists() and ts.read_json(report_path).get("status") == "COMPLETE":
        print(f"{arm} seed {seed} attempt {attempt}: already COMPLETE", flush=True)
        return 0
    previous = ts.read_json(report_path) if report_path.exists() else None
    if previous is not None and not arguments.resume:
        print("This attempt already started and did not complete. Amendment 1 item 11: a disconnect or crash is an "
              "infrastructure failure; start a fresh attempt from scratch (never overwrite this one). --resume "
              "continues it for engineering use only: a resumed run is never valid for the gate.", file=sys.stderr, flush=True)
        return EXIT_CODES["refused"]
    report = {"status": "STARTED", "arm": arm, "seed": seed, "slot": slot, "attempt": attempt, "oom": False,
              "recipe": RECIPE, "recipe_sha256": ts.digest(RECIPE), "order_rule": ORDER_RULE,
              "schedule_rule": SCHEDULE_RULE, "implementation_manifest_sha256": arguments.implementation_manifest_sha256,
              "failure_class": None, "valid_for_gate": False, "updates": [], "checkpoints": [], "resumes": [],
              "events": [], "steps": {"windows": RECIPE["updates"], "attempted": 0, "successful": 0, "cursor": 0}}
    if previous is not None:  # --resume: keep the history, drop updates after the restored checkpoint later
        report.update({key: previous[key] for key in ("updates", "checkpoints", "resumes", "events") if key in previous})
    report["events"].append({"event": "process_start", "resume": bool(previous), "at": time.time()})
    stage = "arguments"
    try:
        protocol(arm in ARMS and seed in SLOTS + RESERVE_QUEUE and slot in SLOTS, "Arm EE/ER/EC, seed 11/22/33/44/55, slot 11/22/33")
        protocol(seed == slot or seed in RESERVE_QUEUE, "An original seed trains only in its own slot")
        protocol(1 <= attempt <= MAX_ATTEMPTS, "At most two attempts per arm and seed (Amendment 1 item 11)")
        stage = "setup"
        torch, mismatches = ts.gpu_setup(arguments.allow_stack_mismatch)
        stage = "data"
        data = ts.read_json(arguments.data)
        families = validate_phase2_data(data)
        exposure_raw = Path(arguments.exposure_order).read_bytes()
        order = check_exposure(json.loads(exposure_raw), data, seed)
        report.update(data_sha256=data["families_sha256"], order_sha256=order,
                      exposure_order_file_sha256=ts.sha256(exposure_raw), environment=ts.environment(torch, mismatches))
    except Exception as error:
        fail_report(report, report_path, error, stage)
        return announce(report)
    sampler = ts.MemorySampler().start()
    report["nvml_sampler_error"] = sampler.error
    trainer = None
    try:
        stage = "tokenizer"
        tokenizer = ts.load_tokenizer()
        stage = "labels"
        examples, audit = prepare_examples(tokenizer, families)
        report["mask_audit"] = {key: audit[key] for key in ("passed", "arms", "max_input_tokens", "last_target_is_im_end")}
        report["chat_template_sha256"] = ts.digest(tokenizer.chat_template)
        sequence = run_examples(examples, families, arm, seed)
        stage = "model"
        ts.seed_everything(torch, seed)
        torch.cuda.reset_peak_memory_stats()
        model, trainable, keep, report["model"] = load_model(torch, seed)
        report["base_weight_shards_sha256"] = weight_shard_hashes()
        report["load_min_free_bytes"] = min(v for v in (sampler.take(), torch.cuda.mem_get_info()[0]) if v is not None)
        initial = ts.tensors_digest(trainable)
        protocol(report.get("initial_adapter_sha256", initial) == initial, "Initial adapter differs from the first process")
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
                     implementation_manifest_sha256=arguments.implementation_manifest_sha256,
                     base_model=ts.MODEL_ID, base_revision=ts.MODEL_REVISION,
                     base_weight_shards_sha256=report["base_weight_shards_sha256"])
        report["final_adapter"] = final
        ts.write_json(out / "final_adapter.json", final)
        shutil.rmtree(out / "checkpoint", ignore_errors=True)  # optimizer state is not needed after update 60
        report["status"] = "COMPLETE"
        report["valid_for_gate"] = not resumed
        print(f"final adapter SHA-256 {final['adapter_model_sha256']} (config {final['adapter_config_sha256']})", flush=True)
        if resumed:
            print("This run was RESUMED: it is never valid for the FinalTest gate (Amendment 1 item 11).", flush=True)
    except Exception as error:
        report["oom"] = isinstance(error, torch.cuda.OutOfMemoryError) or "out of memory" in str(error).lower()
        fail_report(report, report_path, error, stage)
    finally:
        sampler.stop()
        if trainer is not None:
            report["steps"] = trainer.steps()
        report["summary"] = ts.summarize_updates(report["updates"], warmup=0, resume_after=0)
        report["events"].append({"event": "process_end", "status": report["status"], "at": time.time()})
        ts.write_json(report_path, report)
    print(f"{arm} seed {seed} attempt {attempt}: {report['status']} — steps {report['steps']}", flush=True)
    return announce(report) if report["status"] != "COMPLETE" else 0


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
    parser = argparse.ArgumentParser(description="Phase-2 QLoRA training (D043, Amendment 1)")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train")
    train.add_argument("--arm", choices=sorted(ARMS), required=True)
    train.add_argument("--seed", type=int, choices=SLOTS + RESERVE_QUEUE, required=True)
    train.add_argument("--slot", type=int, choices=SLOTS, required=True)
    train.add_argument("--attempt", type=int, required=True)
    train.add_argument("--data", type=Path, required=True)
    train.add_argument("--exposure-order", type=Path, required=True)
    train.add_argument("--out", type=Path, required=True)
    train.add_argument("--implementation-manifest-sha256")
    train.add_argument("--resume", action="store_true", help="Engineering only: continue from the checkpoint; never valid")
    train.add_argument("--allow-stack-mismatch", action="store_true")
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
