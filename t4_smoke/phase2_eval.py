"""Phase-2 evaluation through the frozen Test 1 engine (phase2/PREREGISTRATION.md §4, §5, §11 with Amendment 1).

  python3 t4_smoke/phase2_eval.py evaluate --split dev --inputs INPUTS_DIR --run-dir RUN [--adapter-dir D --adapter-record R] [--sealed]
  python3 t4_smoke/phase2_eval.py gate --frozen adapters_frozen.json --train-root TRAIN_ROOT
  python3 t4_smoke/phase2_eval.py freeze-manifest --train-root TRAIN_ROOT   # reads ATTEMPT_LOG.jsonl and the retained runs

FINAL_TEST evaluations are always sealed (Amendment 1 item 14): the operator sees only completion, checksum and
infrastructure status; scored records go into the results ZIP and are never printed.

Prompt v2, greedy non-thinking decoding, NF4 + FP16, scorer v1.0.0, engine seed 11 and the engine's journal,
resume and export are unchanged; a trained adapter is loaded unmerged on the same NF4 base. Data are the frozen
DEV / FINAL_TEST files, hash-checked. Model-free helpers (inputs, gate, manifests) use the standard library only.
"""
import argparse
import contextlib
import hashlib
import io
import json
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent, HERE.parent / "test1_pilot"):  # notebook payload root, or the repository
    if (candidate / "hinglish_pilot").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from hinglish_pilot.data import validate  # noqa: E402
from hinglish_pilot.engine import default_config, read, run, write  # noqa: E402
from hinglish_pilot.hf_backend import adapter_digests  # noqa: E402
from hinglish_pilot.report import wilson  # noqa: E402

try:
    from . import train_phase2 as tp
    from . import train_smoke as ts
except ImportError:
    import train_phase2 as tp
    import train_smoke as ts

ARMS, RECIPE, SEEDS, RESERVE_SEEDS = tp.ARMS, tp.RECIPE, tp.SLOTS, tp.RESERVE_QUEUE
run_name, attempt_dir = tp.run_name, tp.attempt_dir

MODEL_ID = ts.MODEL_ID
MODEL_REVISION = ts.MODEL_REVISION
FROZEN = {  # phase2/TRAIN_DEV_FROZEN.md, phase2/FINAL_TEST_FROZEN.md, PREREGISTRATION §1
    "dev": ("phase2/dev.v2.json", "e741c1652f5b3dcaebc78d9dd9d7c31fdf4417306fbb2f0862149f27f858f28b", "DEV", 40),
    "final_test": ("phase2/final_test.v3.json", "da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46",
                   "FINAL_TEST", 100),
}
MODES = {"dev": "phase2_dev", "final_test": "phase2_final_test"}
CEILING_CORRECT = 38  # §5: unchanged DEV C >= 95% of 40
CEILING_NAME = "high unchanged-DEV accuracy (ceiling-risk proxy)"  # Amendment 1 item 7
PHASE2_MODEL = "Qwen/Qwen3-4B"  # Amendment 1 item 15: Llama-3.2-3B (or any second backbone) is excluded
BORROWING_POLICY = ("Phase-2 policy (D033): R = Hindi phrasing in Roman script with established English loan nouns; "
                    "C = insertional Hinglish with English lexical material beyond R's borrowings. Frozen data, unchanged.")
IDENTITY = ("family_id", "source_family_id", "template_group_id")
FROZEN_SCHEMA = "phase2-adapters-frozen-2"
ENGINE_SEED = 11
SHA256 = re.compile("[0-9a-f]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def identity_records(families):
    return [{key: family[key] for key in IDENTITY} for family in families]


def split_identities(root):
    """Identity triples only (no texts or gold) of TRAIN and DEV, hash-checked; FINAL_TEST is not read."""
    train = []
    for name, raw in ts.load_train_sources(root):
        require(sha256(raw) == ts.TRAIN_FILES[name], f"{name} does not match its frozen SHA-256")
        train += identity_records(json.loads(raw))
    path, expected, _, _ = FROZEN["dev"]
    raw = (Path(root) / path).read_bytes()
    require(sha256(raw) == expected, f"{path} does not match its frozen SHA-256")
    return {"CONFIRM_TRAIN": sorted(train, key=lambda r: r["family_id"]),
            "DEV": sorted(identity_records(json.loads(raw)), key=lambda r: r["family_id"])}


def inputs(raw, split, identities):
    """Engine (dataset, splits) for the frozen file bytes ``raw``; the families are passed through unchanged."""
    require(split in FROZEN, "Split must be dev or final_test")
    path, expected, role, count = FROZEN[split]
    require(sha256(raw) == expected, f"{path} does not match its frozen SHA-256 {expected}")
    families = json.loads(raw)
    require(len(families) == count and all(f["split_role"] == role for f in families), f"{path}: expected {count} {role} families")
    mode = MODES[split]
    version = f"{Path(path).stem}-{expected[:12]}"
    dataset = {"schema_version": "test1-1", "version": version, "kind": mode, "borrowing_policy": BORROWING_POLICY,
               "families": families}
    ids = lambda records: [r[k] for r in records for k in IDENTITY]  # noqa: E731
    splits = {"schema_version": "test1-1", "version": version, "kind": mode, "audit": None, "PILOT_EVAL": [],
              "SMOKE_TRAIN": [], "RETIRED_DRAFT": [], "CONFIRM_TRAIN": identities["CONFIRM_TRAIN"],
              "FINAL_TEST": identity_records(families) if split == "final_test" else [],
              "development_exclusion_ids": ids(identities["DEV"])}
    validate(dataset, splits, mode)
    return dataset, splits


def adapter_record(final):
    """Engine config ``adapter`` entry from a training run's final_adapter.json."""
    return {key: final[key] for key in ("arm", "seed", "attempt", "adapter_model_sha256", "adapter_config_sha256")}


def config_for(split, adapter=None):
    require(MODEL_ID == PHASE2_MODEL, "Phase 2 evaluates Qwen3-4B only (Amendment 1 item 15)")
    config = default_config(MODES[split], MODEL_ID)
    config.update(model_revision=MODEL_REVISION, tokenizer_revision=MODEL_REVISION, adapter=adapter)
    require(config["seed"] == ENGINE_SEED, "Engine seed must stay 11")
    return config


def ceiling_flag(metrics):
    """Amendment 1 item 7: the renamed DEV flag with k/40, its Wilson interval and the observed DEV headroom."""
    c = metrics["accuracy"]["C"]
    k, n = c["correct"], c["denominator"]
    low, high = wilson(k, n)
    return {"name": CEILING_NAME, "k": k, "n": n, "C_correct": k, "denominator": n, "threshold_correct": CEILING_CORRECT,
            "flag": n == 40 and k >= CEILING_CORRECT, "wilson95": [low, high], "observed_dev_headroom": (n - k) / n,
            "rule": "PREREGISTRATION §5 with Amendment 1 item 7: unchanged-model DEV C strict accuracy >= 38/40",
            "note": "A ceiling-risk proxy only: no trained-arm ceiling is asserted; Delta_C and its precision stay first "
                    "in the report whatever this flag; S2 stays descriptive; design and labels never change."}


def ceiling_line(flag):
    low, high = flag["wilson95"]
    return (f"{flag['name']}: {'FIRES' if flag['flag'] else 'does not fire'} — unchanged DEV C {flag['k']}/{flag['n']} "
            f"= {100 * flag['k'] / flag['n']:.1f}% (Wilson 95% {100 * low:.1f}–{100 * high:.1f}%), threshold >= "
            f"{flag['threshold_correct']}/40")


# ---------------------------------------------------------------- freeze manifest and FinalTest gate (model-free)

def parse_frozen(text):
    """The first ```json block of phase2/ADAPTERS_FROZEN.md, validated (Amendment 1 item 12)."""
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.S)
    require(match is not None, "ADAPTERS_FROZEN.md has no ```json block")
    frozen = json.loads(match.group(1))
    require(frozen.get("schema") == FROZEN_SCHEMA, f"Freeze manifest schema must be {FROZEN_SCHEMA}")
    require(frozen.get("base_model") == MODEL_ID and frozen.get("base_revision") == MODEL_REVISION, "Base model/revision mismatch")
    for key in ("implementation_manifest_sha256", "exposure_order_file_sha256", "attempt_log_sha256"):
        require(SHA256.fullmatch(str(frozen.get(key))), f"{key} must be a SHA-256")
    retained = frozen.get("retained_seeds")
    require(isinstance(retained, list), "retained_seeds must be a list of {slot, seed}")
    S = len(retained)
    require(frozen.get("S") == S, "S must equal the number of retained seeds")
    require(S >= 1, "S = 0: no complete seed triplet, so FINAL_TEST is never accessed (Amendment 1 item 12)")
    require(S <= 3, "At most three seed triplets")
    slots = [entry.get("slot") for entry in retained]
    seeds = [entry.get("seed") for entry in retained]
    require(all(set(entry) == {"slot", "seed"} for entry in retained), "retained_seeds entries are {slot, seed}")
    require(len(set(slots)) == S and set(slots) <= set(SEEDS), "Each retained slot is one of 11/22/33, once")
    require(len(set(seeds)) == S and all(seed == slot or seed in RESERVE_SEEDS for slot, seed in zip(slots, seeds)),
            "Each retained seed is its own slot or a reserve (44/55), used once")
    if S == 3:
        require(frozen.get("confirmatory") is True and frozen.get("descriptive_only") is False,
                "S = 3: confirmatory true and descriptive_only false")
    else:
        require(frozen.get("descriptive_only") is True and frozen.get("confirmatory") is False,
                f"S = {S}: the manifest must carry an explicit descriptive_only: true flag (reduced-S report, no "
                "confirmatory label; Amendment 1 item 12)")
    adapters = frozen.get("adapters")
    require(isinstance(adapters, list) and len(adapters) == 3 * S, f"The freeze manifest must list exactly {3 * S} adapters")
    require(sorted((a["seed"], a["arm"]) for a in adapters) == sorted((s, arm) for s in seeds for arm in ARMS),
            "Each retained seed needs exactly one EE, ER and EC adapter")
    for adapter in adapters:
        require(set(adapter) == {"arm", "seed", "attempt", "adapter_model_sha256", "adapter_config_sha256"}, "Adapter entry fields")
        require(type(adapter["attempt"]) is int and 1 <= adapter["attempt"] <= tp.MAX_ATTEMPTS, "Attempt must be 1 or 2")
        for key in ("adapter_model_sha256", "adapter_config_sha256"):
            require(SHA256.fullmatch(str(adapter[key])), f"{key} must be a SHA-256")
    return frozen


def gate(frozen, train_root, *, expected_data_sha256=None):
    """Refuse FINAL_TEST unless every frozen adapter is present, valid (60/60 steps, not resumed), hash-identical,
    built by the frozen implementation and exposure order, and the attempt log still yields the frozen seeds."""
    problems, found = [], []
    log_path = Path(train_root) / tp.ATTEMPT_LOG
    if not log_path.is_file() or ts.file_sha256(log_path) != frozen["attempt_log_sha256"]:
        problems.append(f"attempt log {log_path} missing or changed since the freeze")
    else:
        current = tp.plan(tp.read_log(log_path))
        if current["halted"] or [list(pair) for pair in current["retained"]] != [[e["slot"], e["seed"]] for e in frozen["retained_seeds"]]:
            problems.append("attempt log does not yield the frozen retained seeds")
    for entry in sorted(frozen["adapters"], key=lambda a: (a["seed"], a["arm"])):
        folder = attempt_dir(train_root, entry["arm"], entry["seed"], entry["attempt"])
        label = f"{run_name(entry['arm'], entry['seed'])} attempt {entry['attempt']}"
        record_path = folder / "final_adapter.json"
        if not record_path.is_file():
            problems.append(f"{label}: final_adapter.json not found at {record_path}")
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        checks = {
            "valid run (60/60 steps, finite, not resumed; Amendment 1 items 10-11)": not tp.valid_run_problems(record),
            "recipe": record.get("recipe_sha256") == ts.digest(RECIPE),
            "identity": (record.get("arm"), record.get("seed"), record.get("attempt")) == (entry["arm"], entry["seed"], entry["attempt"]),
            "recorded hashes": all(record.get(k) == entry[k] for k in ("adapter_model_sha256", "adapter_config_sha256")),
            "base revision": record.get("base_revision") == MODEL_REVISION,
            "implementation manifest": record.get("implementation_manifest_sha256") == frozen["implementation_manifest_sha256"],
            "exposure order file": record.get("exposure_order_file_sha256") == frozen["exposure_order_file_sha256"],
        }
        if "base_weight_shards_sha256" in frozen:
            checks["base weight shards"] = record.get("base_weight_shards_sha256") == frozen["base_weight_shards_sha256"]
        if expected_data_sha256 is not None:
            checks["TRAIN data"] = record.get("data_sha256") == expected_data_sha256
        on_disk = adapter_digests(folder / "final_adapter") if (folder / "final_adapter").is_dir() else {}
        checks["files match the frozen hashes"] = all(on_disk.get(k) == entry[k] for k in ("adapter_model_sha256", "adapter_config_sha256"))
        problems += [f"{label}: {name} check failed" for name, ok in checks.items() if not ok]
        found.append((entry, record, folder / "final_adapter"))
    for seed in sorted({entry["seed"] for entry, _, _ in found}):
        group = [record for entry, record, _ in found if entry["seed"] == seed]
        for key in ("initial_adapter_sha256", "order_sha256"):
            if len({record.get(key) for record in group}) != 1:
                problems.append(f"seed {seed}: arms differ in {key} (pairing broken)")
    if problems or len(found) != 3 * frozen["S"]:
        raise ValueError("FINAL_TEST gate REFUSED:\n- " + "\n- ".join(problems or ["adapters missing"]))
    return [(adapter_record(record), folder) for _, record, folder in found]


def freeze_manifest(train_root):
    """JSON block for phase2/ADAPTERS_FROZEN.md from the attempt log and the retained valid runs (operator aid).

    Refuses while the study is halted, while any slot is still open, and when S = 0 (Amendment 1 item 12)."""
    train_root = Path(train_root)
    log_path = train_root / tp.ATTEMPT_LOG
    current = tp.plan(tp.read_log(log_path))
    require(not current["halted"], "Study halted: no freeze and no FINAL_TEST access")
    require(current["final"], "Some seed slot is still open: finish or exhaust every slot before the freeze")
    require(current["S"] >= 1, "S = 0: no complete seed triplet, so FINAL_TEST is never accessed (Amendment 1 item 12)")
    records = []
    for slot, seed in current["retained"]:
        for arm in sorted(ARMS):
            attempt = current["slots"][slot]["arms"][arm]["valid_attempt"]
            record = ts.read_json(attempt_dir(train_root, arm, seed, attempt) / "final_adapter.json")
            require(not tp.valid_run_problems(record), f"{run_name(arm, seed)} attempt {attempt} is not a valid run")
            records.append(record)
    shared = {}
    for key in ("implementation_manifest_sha256", "exposure_order_file_sha256", "base_weight_shards_sha256"):
        values = {json.dumps(r.get(key), sort_keys=True) for r in records}
        require(len(values) == 1 and records[0].get(key) is not None, f"Retained runs differ in (or lack) {key}")
        shared[key] = records[0][key]
    S = current["S"]
    frozen = {"schema": FROZEN_SCHEMA, "base_model": MODEL_ID, "base_revision": MODEL_REVISION, **shared,
              "attempt_log_sha256": ts.file_sha256(log_path),
              "retained_seeds": [{"slot": slot, "seed": seed} for slot, seed in current["retained"]], "S": S,
              "confirmatory": S == 3, "descriptive_only": S < 3,
              "adapters": [adapter_record(r) for r in sorted(records, key=lambda r: (r["seed"], r["arm"]))]}
    parse_frozen("```json\n" + json.dumps(frozen) + "\n```")
    return frozen


def check_preregistration(text_bytes, expected_sha256):
    actual = sha256(text_bytes)
    require(expected_sha256 is not None and actual == expected_sha256,
            f"PREREGISTRATION.md SHA-256 {actual} does not match the recorded {expected_sha256}: FINAL_TEST refused")
    return actual


# ---------------------------------------------------------------- GPU evaluation (lazy imports)

def sealed_status(run_dir, manifest, archive):
    """Completion, checksum and infrastructure status only (no answers, no accuracy)."""
    errors = run_dir / "errors.jsonl"
    infrastructure = sum(1 for line in errors.read_text(encoding="utf-8").splitlines() if line.strip()) if errors.exists() else 0
    return {"run": run_dir.name, "status": manifest.get("status"), "completed": manifest.get("completed"),
            "expected": manifest.get("expected"), "unresolved": manifest.get("unresolved"),
            "attempts": manifest.get("attempts"), "infrastructure_failures": infrastructure,
            "results_zip": archive.name, "results_zip_sha256": sha256(archive.read_bytes()),
            "checksums_sha256": sha256((run_dir / "checksums.sha256").read_bytes())}


def run_evaluate(arguments):
    split, run_dir = arguments.split, Path(arguments.run_dir)
    sealed = split == "final_test" or arguments.sealed  # FINAL_TEST can never be unsealed (Amendment 1 item 14)
    folder = Path(arguments.inputs)
    dataset, splits = inputs((folder / Path(FROZEN[split][0]).name).read_bytes(), split,
                             json.loads((folder / "identities.json").read_text(encoding="utf-8")))
    adapter = None
    if arguments.adapter_record:
        adapter = adapter_record(json.loads(Path(arguments.adapter_record).read_text(encoding="utf-8")))
    config = config_for(split, adapter)
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists() and read(manifest_path).get("status") == "COMPLETE":
        print(run_dir.name, "already COMPLETE; nothing regenerated", flush=True)
    else:
        from hinglish_pilot.hf_backend import HFBackend
        backend = HFBackend(config, adapter_path=arguments.adapter_dir)
        write(run_dir.parent / f"{run_dir.name}_model_load_report.json", backend.load_report)
        if sealed:
            def progress(done, total, item):
                if done % 25 == 0 or done == total:
                    print(f"{run_dir.name}: {done}/{total} generated", flush=True)
        else:
            def progress(done, total, item):
                print(f"{done}/{total}: {item['rendering_id']} {item['latency_seconds']:.1f}s", flush=True)
        manifest = run(run_dir, dataset, splits, config, backend, progress=progress)
        print("Run status:", manifest["status"], manifest["completed"], "/", manifest["expected"], flush=True)
    from hinglish_pilot.report import analyze, export
    quiet = io.StringIO()
    with contextlib.redirect_stdout(quiet) if sealed else contextlib.nullcontext():
        metrics, _ = analyze(run_dir)
    if not sealed:
        print((run_dir / "summary.md").read_text(), flush=True)
    if metrics["status"] == "COMPLETE":
        try:
            from secondary_analysis.report_secondary import analyze as analyze_secondary
            with contextlib.redirect_stdout(quiet) if sealed else contextlib.nullcontext():
                analyze_secondary(run_dir)
        except Exception:  # secondary endpoints never block the primary export
            print("Secondary analysis failed (primary unaffected):\n" + (traceback.format_exc() if not sealed else
                  "details are in the results ZIP"), flush=True)
        if split == "dev" and adapter is None and not sealed:
            flag = ceiling_flag(metrics)
            write(run_dir.parent / f"{run_dir.name}_ceiling_flag.json", flag)
            print(ceiling_line(flag), flush=True)
    with contextlib.redirect_stdout(quiet) if sealed else contextlib.nullcontext():
        archive = export(run_dir)
    if sealed:
        status = sealed_status(run_dir, read(manifest_path), archive)
        write(run_dir.parent / f"{run_dir.name}_status.json", status)
        print("SEALED (Amendment 1 item 14) — completion/checksum/infrastructure only:", json.dumps(status), flush=True)
    else:
        print("Export:", archive, sha256(archive.read_bytes()), flush=True)
    return 0 if metrics["status"] == "COMPLETE" else 1


def run_gate(arguments):
    frozen = json.loads(Path(arguments.frozen).read_text(encoding="utf-8"))
    parse_frozen("```json\n" + json.dumps(frozen) + "\n```")
    for adapter, folder in gate(frozen, arguments.train_root):
        print(run_name(adapter["arm"], adapter["seed"]), adapter["adapter_model_sha256"], folder)
    return 0


def run_freeze_manifest(arguments):
    print("```json\n" + json.dumps(freeze_manifest(arguments.train_root), indent=2) + "\n```")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Phase-2 evaluation through the frozen engine")
    commands = parser.add_subparsers(dest="command", required=True)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--split", choices=sorted(FROZEN), required=True)
    evaluate.add_argument("--inputs", type=Path, required=True)
    evaluate.add_argument("--run-dir", type=Path, required=True)
    evaluate.add_argument("--adapter-dir", type=Path)
    evaluate.add_argument("--adapter-record", type=Path)
    evaluate.add_argument("--sealed", action="store_true", help="Print only completion/checksum/infrastructure status")
    gate_command = commands.add_parser("gate")
    gate_command.add_argument("--frozen", type=Path, required=True)
    gate_command.add_argument("--train-root", type=Path, required=True)
    commands.add_parser("freeze-manifest").add_argument("--train-root", type=Path, required=True)
    arguments = parser.parse_args(argv)
    if arguments.command == "evaluate":
        require((arguments.adapter_dir is None) == (arguments.adapter_record is None), "Give --adapter-dir with --adapter-record")
    return {"evaluate": run_evaluate, "gate": run_gate, "freeze-manifest": run_freeze_manifest}[arguments.command](arguments)


if __name__ == "__main__":
    sys.exit(main())
