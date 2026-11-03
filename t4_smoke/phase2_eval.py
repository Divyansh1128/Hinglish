"""Phase-2 evaluation through the frozen Test 1 engine (phase2/PREREGISTRATION.md §4, §5, §11).

  python3 t4_smoke/phase2_eval.py evaluate --split dev --inputs INPUTS_DIR --run-dir RUN [--adapter-dir D --adapter-record R]
  python3 t4_smoke/phase2_eval.py gate --frozen adapters_frozen.json --train-root TRAIN_ROOT
  python3 t4_smoke/phase2_eval.py freeze-manifest --train-root FOLDER_WITH_final_adapter.json_FILES

Prompt v2, greedy non-thinking decoding, NF4 + FP16, scorer v1.0.0, engine seed 11 and the engine's journal,
resume and export are unchanged; a trained adapter is loaded unmerged on the same NF4 base. Data are the frozen
DEV / FINAL_TEST files, hash-checked. Model-free helpers (inputs, gate, manifests) use the standard library only.
"""
import argparse
import hashlib
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

try:
    from .train_phase2 import ARMS, RECIPE, RESERVE_SEEDS, SEEDS
    from . import train_smoke as ts
except ImportError:
    from train_phase2 import ARMS, RECIPE, RESERVE_SEEDS, SEEDS
    import train_smoke as ts

MODEL_ID = ts.MODEL_ID
MODEL_REVISION = ts.MODEL_REVISION
FROZEN = {  # phase2/TRAIN_DEV_FROZEN.md, phase2/FINAL_TEST_FROZEN.md, PREREGISTRATION §1
    "dev": ("phase2/dev.v2.json", "e741c1652f5b3dcaebc78d9dd9d7c31fdf4417306fbb2f0862149f27f858f28b", "DEV", 40),
    "final_test": ("phase2/final_test.v3.json", "da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46",
                   "FINAL_TEST", 100),
}
MODES = {"dev": "phase2_dev", "final_test": "phase2_final_test"}
CEILING_CORRECT = 38  # §5: unchanged DEV C >= 95% of 40
BORROWING_POLICY = ("Phase-2 policy (D033): R = Hindi phrasing in Roman script with established English loan nouns; "
                    "C = insertional Hinglish with English lexical material beyond R's borrowings. Frozen data, unchanged.")
IDENTITY = ("family_id", "source_family_id", "template_group_id")
FROZEN_SCHEMA = "phase2-adapters-frozen-1"
ENGINE_SEED = 11


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
    config = default_config(MODES[split], MODEL_ID)
    config.update(model_revision=MODEL_REVISION, tokenizer_revision=MODEL_REVISION, adapter=adapter)
    require(config["seed"] == ENGINE_SEED, "Engine seed must stay 11")
    return config


def ceiling_flag(metrics):
    c = metrics["accuracy"]["C"]
    return {"C_correct": c["correct"], "denominator": c["denominator"], "threshold_correct": CEILING_CORRECT,
            "flag": c["denominator"] == 40 and c["correct"] >= CEILING_CORRECT,
            "rule": "PREREGISTRATION §5: unchanged-model DEV C strict accuracy >= 95% (>= 38/40)"}


# ---------------------------------------------------------------- freeze manifest and FinalTest gate (model-free)

def parse_frozen(text):
    """The first ```json block of phase2/ADAPTERS_FROZEN.md, validated."""
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.S)
    require(match is not None, "ADAPTERS_FROZEN.md has no ```json block")
    frozen = json.loads(match.group(1))
    require(frozen.get("schema") == FROZEN_SCHEMA, f"Freeze manifest schema must be {FROZEN_SCHEMA}")
    require(frozen.get("base_model") == MODEL_ID and frozen.get("base_revision") == MODEL_REVISION, "Base model/revision mismatch")
    adapters = frozen.get("adapters")
    require(isinstance(adapters, list) and len(adapters) == 9, "The freeze manifest must list exactly 9 adapters")
    seeds = sorted({a["seed"] for a in adapters})
    require(len(seeds) == 3 and set(seeds) <= set(SEEDS + RESERVE_SEEDS), "Exactly three seeds from 11/22/33/44/55")
    require(sorted((a["seed"], a["arm"]) for a in adapters) == sorted((s, arm) for s in seeds for arm in ARMS),
            "Each seed needs exactly one EE, ER and EC adapter")
    for adapter in adapters:
        require(set(adapter) == {"arm", "seed", "attempt", "adapter_model_sha256", "adapter_config_sha256"}, "Adapter entry fields")
        require(type(adapter["attempt"]) is int and adapter["attempt"] >= 1, "Attempt must be a positive integer")
        for key in ("adapter_model_sha256", "adapter_config_sha256"):
            require(re.fullmatch("[0-9a-f]{64}", str(adapter[key])), f"{key} must be a SHA-256")
    return frozen


def run_name(arm, seed):
    return f"{arm}-s{seed}"


def attempt_dir(train_root, arm, seed, attempt):
    return Path(train_root) / run_name(arm, seed) / f"attempt-{attempt:02d}"


def gate(frozen, train_root, *, expected_data_sha256=None):
    """Refuse FINAL_TEST unless all 9 frozen adapters are present, complete, not resumed and hash-identical."""
    problems, found = [], []
    for entry in sorted(frozen["adapters"], key=lambda a: (a["seed"], a["arm"])):
        folder = attempt_dir(train_root, entry["arm"], entry["seed"], entry["attempt"])
        label = f"{run_name(entry['arm'], entry['seed'])} attempt {entry['attempt']}"
        record_path = folder / "final_adapter.json"
        if not record_path.is_file():
            problems.append(f"{label}: final_adapter.json not found at {record_path}")
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        checks = {
            "complete": record.get("status") == "COMPLETE" and record.get("updates") == RECIPE["updates"],
            "not resumed (§10)": record.get("resumed") is False,
            "recipe": record.get("recipe_sha256") == ts.digest(RECIPE),
            "identity": (record.get("arm"), record.get("seed"), record.get("attempt")) == (entry["arm"], entry["seed"], entry["attempt"]),
            "recorded hashes": all(record.get(k) == entry[k] for k in ("adapter_model_sha256", "adapter_config_sha256")),
            "base revision": record.get("base_revision") == MODEL_REVISION,
        }
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
    if problems or len(found) != 9:
        raise ValueError("FINAL_TEST gate REFUSED:\n- " + "\n- ".join(problems or ["fewer than 9 adapters found"]))
    return [(adapter_record(record), folder) for _, record, folder in found]


def check_preregistration(text_bytes, expected_sha256):
    actual = sha256(text_bytes)
    require(expected_sha256 is not None and actual == expected_sha256,
            f"PREREGISTRATION.md SHA-256 {actual} does not match the recorded {expected_sha256}: FINAL_TEST refused")
    return actual


def freeze_manifest(records):
    """JSON block for phase2/ADAPTERS_FROZEN.md from 9 final_adapter.json records (operator aid)."""
    complete = [r for r in records if r.get("status") == "COMPLETE" and r.get("resumed") is False]
    frozen = {"schema": FROZEN_SCHEMA, "base_model": MODEL_ID, "base_revision": MODEL_REVISION,
              "base_weight_shards_sha256": sorted({json.dumps(r.get("base_weight_shards_sha256"), sort_keys=True) for r in complete}),
              "adapters": [adapter_record(r) for r in sorted(complete, key=lambda r: (r["seed"], r["arm"], r["attempt"]))]}
    parse_frozen("```json\n" + json.dumps(frozen) + "\n```")
    return frozen


# ---------------------------------------------------------------- GPU evaluation (lazy imports)

def run_evaluate(arguments):
    split, run_dir = arguments.split, Path(arguments.run_dir)
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
        progress = lambda done, total, item: print(f"{done}/{total}: {item['rendering_id']} {item['latency_seconds']:.1f}s", flush=True)  # noqa: E731
        manifest = run(run_dir, dataset, splits, config, backend, progress=progress)
        print("Run status:", manifest["status"], manifest["completed"], "/", manifest["expected"], flush=True)
    from hinglish_pilot.report import analyze, export
    metrics, _ = analyze(run_dir)
    print((run_dir / "summary.md").read_text(), flush=True)
    if metrics["status"] == "COMPLETE":
        try:
            from secondary_analysis.report_secondary import analyze as analyze_secondary
            analyze_secondary(run_dir)
        except Exception:  # secondary endpoints never block the primary export
            print("Secondary analysis failed (primary unaffected):\n" + traceback.format_exc(), flush=True)
        if split == "dev" and adapter is None:
            flag = ceiling_flag(metrics)
            write(run_dir.parent / f"{run_dir.name}_ceiling_flag.json", flag)
            print(f"D040 CEILING FLAG (C >= 38/40): {'FIRES' if flag['flag'] else 'does not fire'} — "
                  f"unchanged DEV C {flag['C_correct']}/{flag['denominator']}", flush=True)
    archive = export(run_dir)
    print("Export:", archive, sha256(archive.read_bytes()), flush=True)
    return 0 if metrics["status"] == "COMPLETE" else 1


def run_gate(arguments):
    frozen = json.loads(Path(arguments.frozen).read_text(encoding="utf-8"))
    parse_frozen("```json\n" + json.dumps(frozen) + "\n```")
    for adapter, folder in gate(frozen, arguments.train_root):
        print(run_name(adapter["arm"], adapter["seed"]), adapter["adapter_model_sha256"], folder)
    return 0


def run_freeze_manifest(arguments):
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(arguments.train_root).rglob("final_adapter.json"))]
    print("```json\n" + json.dumps(freeze_manifest(records), indent=2) + "\n```")
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
