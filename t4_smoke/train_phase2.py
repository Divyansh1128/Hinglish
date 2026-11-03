"""Phase-2 QLoRA training for Qwen3-4B (D043; binding plan phase2/PREREGISTRATION.md §3, §10).

Reuses the GPU-verified D021 smoke code (train_smoke.py: labels, model load, Trainer, digests, memory sampler);
only the data order, learning-rate schedule, run seed, checkpoint cadence and the final adapter are new here.

  python3 t4_smoke/train_phase2.py train --arm EC --seed 11 --attempt 1 --data phase2_train.json --out RUN_DIR
  python3 t4_smoke/train_phase2.py train ... --resume      # continue after a disconnect (recorded; see §10)
  python3 t4_smoke/train_phase2.py pairing --train-root TRAIN_ROOT

Training reads only the two frozen TRAIN files (hash-checked) or the data file built from them. It never reads DEV
or FINAL_TEST. Model-free parts use the standard library only; torch, transformers, bitsandbytes and PEFT are
imported lazily inside the GPU commands.
"""
import argparse
import json
import math
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
SEEDS = (11, 22, 33)
RESERVE_SEEDS = (44, 55)  # §10: replace a seed (for all three arms) only after a failed from-scratch rerun
FAMILIES_PER_FILE = 80
ORDER_PREFIX = "phase2-D043"
ORDER_RULE = (
    "For seed s and pass p in {1,2,3}: sort the 160 TRAIN families by the SHA-256 hex of "
    "f'phase2-D043:{s}:{p}:{family_id}' ascending; each family contributes its E example and then the arm's second "
    "example, consecutively; each update takes the next 16 examples (8 families). Identical across arms within a seed."
)
SCHEDULE_RULE = "lr(u) = 1e-4*u/6 for u <= 6; otherwise 1e-4*[0.1 + 0.9*0.5*(1 + cos(pi*(u-6)/54))]; lr(60) = 1e-5"

# D021 recipe (train_smoke.RECIPE) with the D043 schedule. Keys shared with the smoke recipe keep its values.
RECIPE = {key: value for key, value in ts.RECIPE.items()
          if key not in ("seed", "families", "updates", "measurement_warmup_updates", "resume_after_update",
                         "probe_updates", "lr_schedule", "data_order")}
RECIPE.update(
    study="phase2-D043", families=160, examples_per_arm=320, passes=3, updates_per_pass=20, updates=60,
    lr_schedule=SCHEDULE_RULE, warmup_updates=6, min_lr_ratio=0.1, data_order=ORDER_RULE,
    seeds=list(SEEDS), reserve_seeds=list(RESERVE_SEEDS), checkpoint_every=10,
    seeding="random, torch and CUDA seeded with the run seed before the adapter is created and before training",
    evaluated_checkpoint="adapter after update 60",
)


def require(condition, message):
    ts.require(condition, message)


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


def order_key(seed, number, family_id):
    return ts.sha256(f"{ORDER_PREFIX}:{seed}:{number}:{family_id}".encode("utf-8"))


def pass_order(families, seed, number):
    """Family IDs for pass ``number`` (1-based) of ``seed``; does not depend on the arm."""
    return [family["family_id"] for family in sorted(families, key=lambda f: order_key(seed, number, f["family_id"]))]


def run_sequence(families, arm, seed):
    """(family_id, form) for all 960 microbatches of one run: 3 passes x 160 families x (E, second)."""
    require(arm in ARMS, "Unknown arm")
    require(isinstance(seed, int), "Seed must be an integer")
    second = ARMS[arm]
    sequence = [(family_id, form) for number in range(1, RECIPE["passes"] + 1)
                for family_id in pass_order(families, seed, number) for form in ("E", second)]
    require(len(sequence) == RECIPE["updates"] * RECIPE["accumulation"], "Sequence does not fill 60 updates")
    return sequence


def order_sha256(families, seed):
    """Arm-independent fingerprint of a seed's family order (equal across arms by construction)."""
    return ts.digest([pass_order(families, seed, number) for number in range(1, RECIPE["passes"] + 1)])


def run_examples(examples, families, arm, seed):
    return [dict(examples[family_id][form], family_id=family_id, form=form)
            for family_id, form in run_sequence(families, arm, seed)]


def pass_of(update):
    return (update - 1) // RECIPE["updates_per_pass"] + 1


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


def set_lr(trainer, update):
    value = lr_at(update)
    for group in trainer.optimizer.param_groups:
        group["lr"] = value
    return value


def checkpoint_meta(trainer, completed, report):
    return {"cursor": trainer.cursor, "completed_updates": completed, "rng_python": ts.list_state(random.getstate()),
            "recipe_sha256": ts.digest(RECIPE), "data_sha256": report["data_sha256"], "arm": report["arm"],
            "seed": report["seed"], "attempt": report["attempt"], "order_sha256": report["order_sha256"],
            "initial_adapter_sha256": report["initial_adapter_sha256"],
            "parameter_names": [name for name, _ in trainer.trainable]}


def save_checkpoint(torch, trainer, out, completed, probe_example, report):
    """train_smoke.save, generalised to any update; written atomically, only the latest is kept."""
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
    """Adapter after update 60; the saved tensors must equal the trained ones exactly."""
    folder = out / "final_adapter"
    shutil.rmtree(folder, ignore_errors=True)
    trainer.model.save_pretrained(folder, save_embedding_layers=False)
    from safetensors.torch import load_file
    saved = load_file(str(folder / "adapter_model.safetensors"))
    live = {name.replace(".default.", "."): parameter.detach().cpu() for name, parameter in trainer.trainable}
    require(sorted(saved) == sorted(live), "Saved adapter tensor names differ from the trained adapter")
    require(all(torch.equal(saved[name], live[name]) for name in live), "Saved adapter differs from the trained adapter")
    return {"adapter_model_sha256": ts.file_sha256(folder / "adapter_model.safetensors"),
            "adapter_config_sha256": ts.file_sha256(folder / "adapter_config.json"),
            "adapter_tensors_sha256": ts.tensors_digest(trainer.trainable), "tensors": len(saved)}


def run_train(arguments):
    arm, seed, attempt = arguments.arm, arguments.seed, arguments.attempt
    out = Path(arguments.out)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "train_report.json"
    if report_path.exists() and ts.read_json(report_path).get("status") == "COMPLETE":
        print(f"{arm} seed {seed} attempt {attempt}: already COMPLETE", flush=True)
        return 0
    previous = ts.read_json(report_path) if report_path.exists() else None
    if previous is not None and not arguments.resume:
        print("This attempt already started and did not complete. Per PREREGISTRATION §10 a disconnect or crash is an "
              "infrastructure failure: start a fresh attempt (rerun from scratch). --resume continues it but marks the "
              "run as resumed, and the FinalTest gate refuses resumed adapters.", file=sys.stderr, flush=True)
        return 2
    report = {"status": "STARTED", "arm": arm, "seed": seed, "attempt": attempt, "oom": False, "recipe": RECIPE,
              "recipe_sha256": ts.digest(RECIPE), "order_rule": ORDER_RULE, "schedule_rule": SCHEDULE_RULE,
              "updates": [], "checkpoints": [], "resumes": [], "events": []}
    if previous is not None:  # --resume: keep the history, drop updates after the restored checkpoint later
        report.update({key: previous[key] for key in ("updates", "checkpoints", "resumes", "events") if key in previous})
    report["events"].append({"event": "process_start", "resume": bool(previous), "at": time.time()})
    try:
        require(arm in ARMS and seed in SEEDS + RESERVE_SEEDS, "Arm must be EE/ER/EC and seed one of 11/22/33/44/55")
        torch, mismatches = ts.gpu_setup(arguments.allow_stack_mismatch)
        data = ts.read_json(arguments.data)
        families = validate_phase2_data(data)
        report.update(data_sha256=data["families_sha256"], order_sha256=order_sha256(families, seed),
                      environment=ts.environment(torch, mismatches))
    except Exception:
        return ts.setup_failure(report, report_path)
    sampler = ts.MemorySampler().start()
    report["nvml_sampler_error"] = sampler.error
    try:
        tokenizer = ts.load_tokenizer()
        examples = ts.build_examples(tokenizer, families)  # asserts identical E/R/C targets; no truncation
        audit = ts.mask_audit(tokenizer, examples, families)
        im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
        audit["last_target_is_im_end"] = all(e["labels"][-1] == im_end for built in examples.values() for e in built.values())
        require(audit["passed"] and audit["last_target_is_im_end"], "Mask/target audit failed: " + "; ".join(audit["failures"][:5]))
        report["mask_audit"] = {key: audit[key] for key in ("passed", "arms", "max_input_tokens", "last_target_is_im_end")}
        report["chat_template_sha256"] = ts.digest(tokenizer.chat_template)
        sequence = run_examples(examples, families, arm, seed)
        ts.seed_everything(torch, seed)
        torch.cuda.reset_peak_memory_stats()
        model, trainable, keep, report["model"] = load_model(torch, seed)
        report["base_weight_shards_sha256"] = weight_shard_hashes()
        report["load_min_free_bytes"] = min(v for v in (sampler.take(), torch.cuda.mem_get_info()[0]) if v is not None)
        initial = ts.tensors_digest(trainable)
        require(report.get("initial_adapter_sha256", initial) == initial, "Initial adapter differs from the first process")
        report["initial_adapter_sha256"] = initial
        trainer = ts.Trainer(torch, model, trainable, keep, sequence, sampler)
        probe_example = sequence[0]
        completed = 0
        if previous is not None:
            completed, check = restore_checkpoint(torch, trainer, out, report)
            report["resumes"].append(check)
            report["updates"] = [record for record in report["updates"] if record["update"] <= completed]
        for number in range(completed + 1, RECIPE["updates"] + 1):
            lr = set_lr(trainer, number)
            record = trainer.update(number)
            record.update(lr=lr, pass_number=pass_of(number))
            report["updates"].append(record)
            require(all(ts.finite(loss) for loss in record["microbatch_losses"]), f"Non-finite loss at update {number}")
            if number % RECIPE["checkpoint_every"] == 0 and number < RECIPE["updates"]:
                save_checkpoint(torch, trainer, out, number, probe_example, report)
            ts.write_json(report_path, report)
        final = save_final_adapter(torch, trainer, out)
        final.update(arm=arm, seed=seed, attempt=attempt, status="COMPLETE", updates=RECIPE["updates"],
                     recipe_sha256=report["recipe_sha256"], data_sha256=report["data_sha256"],
                     order_sha256=report["order_sha256"], initial_adapter_sha256=initial,
                     resumed=bool(report["resumes"]), base_model=ts.MODEL_ID, base_revision=ts.MODEL_REVISION,
                     base_weight_shards_sha256=report["base_weight_shards_sha256"])
        report["final_adapter"] = final
        ts.write_json(out / "final_adapter.json", final)
        shutil.rmtree(out / "checkpoint", ignore_errors=True)  # optimizer state is not needed after update 60
        report["status"] = "COMPLETE"
        print(f"final adapter SHA-256 {final['adapter_model_sha256']} (config {final['adapter_config_sha256']})", flush=True)
    except Exception as error:
        report["status"] = "FAILED"
        report["oom"] = isinstance(error, torch.cuda.OutOfMemoryError) or "out of memory" in str(error).lower()
        report["error"] = traceback.format_exc()
        print(report["error"], file=sys.stderr, flush=True)
    finally:
        sampler.stop()
        report["summary"] = ts.summarize_updates(report["updates"], warmup=0, resume_after=0)
        report["events"].append({"event": "process_end", "status": report["status"], "at": time.time()})
        ts.write_json(report_path, report)
    print(f"{arm} seed {seed} attempt {attempt}: {report['status']}", flush=True)
    return 0 if report["status"] == "COMPLETE" else 1


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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Phase-2 QLoRA training (D043)")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train")
    train.add_argument("--arm", choices=sorted(ARMS), required=True)
    train.add_argument("--seed", type=int, choices=SEEDS + RESERVE_SEEDS, required=True)
    train.add_argument("--attempt", type=int, required=True)
    train.add_argument("--data", type=Path, required=True)
    train.add_argument("--out", type=Path, required=True)
    train.add_argument("--resume", action="store_true", help="Continue a started attempt from its checkpoint (recorded)")
    train.add_argument("--allow-stack-mismatch", action="store_true")
    commands.add_parser("pairing").add_argument("--train-root", type=Path, required=True)
    arguments = parser.parse_args(argv)
    return {"train": run_train, "pairing": run_pairing}[arguments.command](arguments)


if __name__ == "__main__":
    sys.exit(main())
