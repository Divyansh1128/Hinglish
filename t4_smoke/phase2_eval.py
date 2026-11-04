"""Phase-2 evaluation through the frozen Test 1 engine (phase2/PREREGISTRATION.md §4, §5, §11 with Amendments 1-3).

  python3 t4_smoke/phase2_eval.py evaluate --split dev --inputs INPUTS_DIR --run-dir RUN [--adapter-dir D --adapter-record R]
      [--implementation-manifest M] [--sealed] [--recover-stale-lock]
  python3 t4_smoke/phase2_eval.py gate --frozen adapters_frozen.json --train-root TRAIN_ROOT [--baseline-dir B]
  python3 t4_smoke/phase2_eval.py freeze-manifest --train-root TRAIN_ROOT --baseline-dir B [--manifest M --root R]

The unchanged-model DEV run started with --implementation-manifest writes ``base_baseline_record.json`` (results-ZIP
SHA-256 and manifest SHA-256) once it is complete; the trainer refuses the first attempt without it (Amendment 2
item 6). --recover-stale-lock removes a RUNNING.lock left by a killed runtime, after the operator confirmed that no
other session is running this evaluation, and logs a timestamped record; stored outputs are never regenerated
(Amendment 2 item 5).

FINAL_TEST evaluations are always sealed (Amendment 1 item 14): the operator sees only completion, checksum and
infrastructure status; scored records go into the results ZIP and are never printed.

Prompt v2, greedy non-thinking decoding, NF4 + FP16, scorer v1.0.0, engine seed 11 and the engine's journal,
resume and export are unchanged; a trained adapter is loaded unmerged on the same NF4 base. Data are the frozen
DEV / FINAL_TEST files, hash-checked. Model-free helpers (inputs, gate, manifests) use the standard library only.
"""
import argparse
import contextlib
import hashlib
import importlib.util
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

import hinglish_pilot.engine as engine_module  # noqa: E402
from hinglish_pilot import hf_backend as hf_backend_module  # noqa: E402
from hinglish_pilot.data import digest, validate  # noqa: E402
from hinglish_pilot.engine import code_hash, default_config, read, recover_lock, run, utc, write  # noqa: E402
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
FROZEN_SCHEMA = "phase2-adapters-frozen-3"  # 3: + baseline_dev_results_zip_sha256 (Amendment 2 item 6)
ENGINE_SEED = 11
# SHA-256 of phase2/PREREGISTRATION.md with Amendments 1-3 (commit 7e84654, D047); supersedes b2e6df8f... (Amendment 2),
# 37ef68bf... (Amendment 1) and 74be2328... (original)
PREREGISTRATION_SHA256 = "a22c81fb33b4d3339770a2b28c51d8d3706af2b5dd038d46aa89fbb56139714d"
SHA256 = re.compile("[0-9a-f]{64}")


def require(condition, message):
    """Hash, identity and data assertions raise the dedicated ProtocolError (a ValueError; Amendment 2 item 2)."""
    if not condition:
        raise tp.ProtocolError(message)


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
    for key in ("implementation_manifest_sha256", "exposure_order_file_sha256", "attempt_log_sha256",
                "baseline_dev_results_zip_sha256"):
        require(SHA256.fullmatch(str(frozen.get(key))), f"{key} must be a SHA-256")
    logs = frozen.get("training_logs_sha256")
    require(isinstance(logs, dict) and logs, "Freeze must include training_logs_sha256")
    for name, checksum in logs.items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and SHA256.fullmatch(str(checksum)),
                "Invalid training log path or SHA-256")
    shards = frozen.get("base_weight_shards_sha256")
    require(isinstance(shards, dict) and shards and all(SHA256.fullmatch(str(v)) for v in shards.values()),
            "Freeze must include base_weight_shards_sha256")
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


def verify_manifest_against(manifest_path, root):
    """Amendment 1 item 14 / Amendment 2 item 7: recheck IMPLEMENTATION_MANIFEST.md against the real files under
    ``root`` (every hashed file must exist with that SHA-256). Returns (document, manifest SHA-256)."""
    raw = Path(manifest_path).read_bytes()
    document = tp.parse_manifest(raw.decode("utf-8"))
    files = document.get("files")
    require(isinstance(files, dict) and files, "Implementation manifest lists no files")
    root = Path(root)
    bad = [path for path, expected in sorted(files.items())
           if not (root / path).is_file() or ts.file_sha256(root / path) != expected]
    require(not bad, "Implementation manifest differs from the real implementation: " + ", ".join(bad))
    prereg = document.get("preregistration") or {}
    if prereg.get("path") and (root / prereg["path"]).is_file():
        require(ts.file_sha256(root / prereg["path"]) == prereg.get("sha256"), "Implementation manifest records another PREREGISTRATION.md")
    return document, sha256(raw)


def differences(found, expected, prefix=""):
    """Dotted paths at which two JSON values differ (for refusal messages)."""
    if isinstance(found, dict) and isinstance(expected, dict):
        paths = []
        for key in sorted(set(found) | set(expected), key=str):
            if key not in found or key not in expected:
                paths.append(f"{prefix}{key} ({'missing' if key not in found else 'unexpected'})")
            else:
                paths += differences(found[key], expected[key], f"{prefix}{key}.")
        return paths
    return [] if found == expected else [prefix.rstrip(".") or "(value)"]


def current_manifest_document(root):
    """The implementation manifest the current builder derives from the repository at ``root``."""
    path = Path(root) / "phase2" / "build_implementation_manifest.py"
    spec = importlib.util.spec_from_file_location("phase2_manifest_builder_for_freeze", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module.build()
    except (OSError, ValueError, KeyError) as error:
        raise tp.ProtocolError(f"Cannot re-derive the implementation manifest from {path}: {error}") from error


def manifest_currency_problems(document, root):
    """Sol re-review B2: every entry of ``document`` (non-file choices — dependency pins, recipe, settings — and the
    required file set) must equal what the current builder derives; empty list if it does."""
    expected = current_manifest_document(root)
    problems = []
    found_files, wanted_files = set(document.get("files") or {}), set(expected["files"])
    if found_files != wanted_files:
        problems.append(f"file set differs from the required one (missing {sorted(wanted_files - found_files)[:5]}, "
                        f"unexpected {sorted(found_files - wanted_files)[:5]})")
    for path in differences(document, expected):
        if not path.startswith("files."):
            problems.append(f"{path} differs from the current builder")
    return problems


def verify_manifest_current(manifest_path, root):
    """Complete manifest-currency check at freeze: the hashed files (verify_manifest_against), the required file set
    and every non-file entry re-derived by the current builder. Returns (document, manifest SHA-256)."""
    document, manifest_sha = verify_manifest_against(manifest_path, root)
    problems = manifest_currency_problems(document, root)
    require(not problems, "Implementation manifest is not current (recheck at adapter freeze failed): " + "; ".join(problems[:10]))
    return document, manifest_sha


def running_code():
    """{manifest path: local file} of every source file this evaluation process executes."""
    files = {f"t4_smoke/{name}": HERE / name for name in ("phase2_eval.py",) + tp.TRAINER_CODE}
    engine_dir = Path(engine_module.__file__).resolve().parent
    files.update({tp.ENGINE_PREFIX + path.name: path for path in sorted(engine_dir.glob("*.py"))})
    spec = importlib.util.find_spec("secondary_analysis")
    if spec is not None and spec.submodule_search_locations:
        folder = Path(list(spec.submodule_search_locations)[0])
        files.update({f"secondary_analysis/{path.name}": path for path in sorted(folder.glob("*.py"))})
    return files


def verify_running_implementation(manifest_path):
    """Sol re-review B3: authenticate the implementation an evaluation runs under, not just record a supplied hash.

    Every source file this process executes (driver, trainer modules, every engine file, the secondary endpoints)
    must have its manifest SHA-256, the engine file set must equal the manifest's, and the non-file entries the
    evaluation depends on (prompt, model, DEV/FINAL_TEST configuration digests, decoding, evaluation pins, chat
    template, frozen identities) must equal what this code derives. Returns (document, manifest SHA-256, files)."""
    raw = Path(manifest_path).read_bytes()
    document = tp.parse_manifest(raw.decode("utf-8"))
    files, groups = document.get("files") or {}, document.get("groups") or {}
    running = running_code()
    engine_running = sorted(path for path in running if path.startswith(tp.ENGINE_PREFIX))
    require(engine_running == sorted(groups.get("engine") or []),
            "The running engine's files differ from the implementation manifest's engine group")
    bad = sorted(path for path, local in running.items()
                 if (path in files or not path.startswith("secondary_analysis/")) and file_sha(local) != files.get(path))
    require(not bad, "Running code differs from the implementation manifest: " + ", ".join(bad))
    problems = tp.manifest_constant_problems(document)
    with tp.protocol_assertions("IMPLEMENTATION_MANIFEST.md"):
        generation = document["generation_config"]
        configs = {split: config_for(split) for split in FROZEN}
        checks = {
            "prompt": (document["prompt"]["version"], document["prompt"]["instruction_sha256"]) == (
                engine_module.PROMPT_VERSION, sha256(engine_module.INSTRUCTION.encode("utf-8"))),
            "engine configurations": generation["engine_config_sha256"] == {s: ts.digest(c) for s, c in configs.items()},
            "decoding": all(configs["dev"][key] == value for key, value in generation["decoding"].items()),
            "engine seed": generation["engine_seed"] == ENGINE_SEED,
            "evaluation dependencies": document["dependencies"]["evaluation"] == hf_backend_module.PINS,
            "adapter dependencies": document["dependencies"]["adapter_evaluation"] == hf_backend_module.ADAPTER_PINS,
            "engine code": document["baseline_dev"]["engine_code_sha256"] == code_hash(),
        }
    problems += [f"non-file entry {name} differs from the running evaluation code" for name, ok in checks.items() if not ok]
    require(not problems, "Implementation manifest does not describe this evaluation: " + "; ".join(problems))
    return document, sha256(raw), {path: files[path] for path in sorted(running) if path in files}


def file_sha(path):
    return ts.file_sha256(path) if Path(path).is_file() else None


def started_identities(entries):
    """The configuration identity of every start/resume_start event of the attempt log."""
    return [entry.get("identity") for entry in entries if entry.get("event") in ("start", "resume_start")]


def baseline_problem(baseline_dir, manifest_path, expected_zip_sha256):
    """None if the unchanged-model DEV run on disk validates (complete registered run under the manifest file at
    ``manifest_path``; Amendment 3 item 3) and has the expected ZIP."""
    try:
        actual = tp.verify_baseline(baseline_dir, manifest_path)
    except tp.Refused as error:
        return str(error)
    return None if actual == expected_zip_sha256 else f"baseline results ZIP {actual} differs from the frozen {expected_zip_sha256}"


def gate(frozen, train_root, *, expected_data_sha256=None, baseline_dir=None, manifest_path=None):
    """Refuse FINAL_TEST unless every frozen adapter is present, valid (60/60 steps, not resumed), hash-identical,
    built by the frozen implementation and exposure order after the frozen unchanged-DEV baseline, and the attempt
    log still yields the frozen seeds with one configuration identity throughout."""
    problems, found, current = [], [], None
    log_path = Path(train_root) / tp.ATTEMPT_LOG
    if not log_path.is_file() or ts.file_sha256(log_path) != frozen["attempt_log_sha256"]:
        problems.append(f"attempt log {log_path} missing or changed since the freeze")
    else:
        entries = tp.read_log(log_path)
        current = tp.plan(entries)
        if current["halted"] or not current["final"] or [list(pair) for pair in current["retained"]] != [[e["slot"], e["seed"]] for e in frozen["retained_seeds"]]:
            problems.append("attempt log does not yield the frozen retained seeds")
        for identity in started_identities(entries):
            identity = identity or {}
            if identity.get("implementation_manifest_sha256") != frozen["implementation_manifest_sha256"]:
                problems.append("an attempt was started under another implementation manifest")
            if identity.get("baseline_dev_results_zip_sha256") != frozen["baseline_dev_results_zip_sha256"]:
                problems.append("an attempt was started without the frozen unchanged-DEV baseline (Amendment 2 item 6)")
    if baseline_dir is not None:  # the archive is validated against the frozen implementation manifest file
        if manifest_path is None or not Path(manifest_path).is_file() or \
                ts.file_sha256(manifest_path) != frozen["implementation_manifest_sha256"]:
            problems.append("unchanged-DEV baseline: the frozen implementation manifest file is needed to validate it")
        else:
            problem = baseline_problem(baseline_dir, manifest_path, frozen["baseline_dev_results_zip_sha256"])
            if problem:
                problems.append("unchanged-DEV baseline: " + problem)
    logs = frozen.get("training_logs_sha256", {})
    for name, checksum in logs.items():
        path = Path(train_root) / name
        if not path.is_file() or ts.file_sha256(path) != checksum:
            problems.append(f"training log {name} missing or changed since the freeze")
    for entry in sorted(frozen["adapters"], key=lambda a: (a["seed"], a["arm"])):
        folder = attempt_dir(train_root, entry["arm"], entry["seed"], entry["attempt"])
        label = f"{run_name(entry['arm'], entry['seed'])} attempt {entry['attempt']}"
        record_path = folder / "final_adapter.json"
        if not record_path.is_file():
            problems.append(f"{label}: final_adapter.json not found at {record_path}")
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        report_name = str((folder / "train_report.json").relative_to(train_root))
        if report_name not in logs:
            problems.append(f"{label}: training report not frozen")
        if current is not None:
            slot = next((e["slot"] for e in frozen["retained_seeds"] if e["seed"] == entry["seed"]), None)
            state = current["slots"][slot]["arms"].get(entry["arm"], {})
            if state.get("valid_attempt") != entry["attempt"]:
                problems.append(f"{label}: attempt is not the valid attempt in the frozen log")
        checks = {
            "valid run (60/60 steps, finite, not resumed; Amendment 1 items 10-11)": not tp.valid_run_problems(record),
            "recipe": record.get("recipe_sha256") == ts.digest(RECIPE),
            "identity": (record.get("arm"), record.get("seed"), record.get("attempt")) == (entry["arm"], entry["seed"], entry["attempt"]),
            "recorded hashes": all(record.get(k) == entry[k] for k in ("adapter_model_sha256", "adapter_config_sha256")),
            "base revision": record.get("base_revision") == MODEL_REVISION,
            "implementation manifest": record.get("implementation_manifest_sha256") == frozen["implementation_manifest_sha256"],
            "exposure order file": record.get("exposure_order_file_sha256") == frozen["exposure_order_file_sha256"],
            "baseline DEV run": record.get("baseline_dev_results_zip_sha256") == frozen["baseline_dev_results_zip_sha256"],
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
        raise tp.ProtocolError("FINAL_TEST gate REFUSED:\n- " + "\n- ".join(dict.fromkeys(problems or ["adapters missing"])))
    return [(adapter_record(record), folder) for _, record, folder in found]


def freeze_manifest(train_root, *, manifest_path=None, root=None, baseline_dir=None):
    """JSON block for phase2/ADAPTERS_FROZEN.md from the attempt log and the retained valid runs (operator aid).

    Rechecks the implementation manifest against the real files under ``root`` (default: this repository), re-derives
    every non-file entry and the required file set with the current builder (Sol re-review B2), and checks it
    against every start event of the attempt log (Amendment 2 item 7), records the unchanged-DEV baseline ZIP hash
    that every attempt was started with (item 6; checked on disk when ``baseline_dir`` is given), and refuses while
    the study is halted, while any slot is still open, and when S = 0 (Amendment 1 item 12)."""
    train_root = Path(train_root)
    root = Path(root) if root is not None else HERE.parent
    manifest_path = Path(manifest_path) if manifest_path is not None else root / "phase2" / tp.MANIFEST_NAME
    _, manifest_sha = verify_manifest_current(manifest_path, root)
    log_path = train_root / tp.ATTEMPT_LOG
    entries = tp.read_log(log_path)
    current = tp.plan(entries)
    require(not current["halted"], "Study halted: no freeze and no FINAL_TEST access")
    require(current["final"], "Some seed slot is still open: finish or exhaust every slot before the freeze")
    require(current["S"] >= 1, "S = 0: no complete seed triplet, so FINAL_TEST is never accessed (Amendment 1 item 12)")
    identities = started_identities(entries)
    require(identities and all(identity == identities[0] for identity in identities), "Attempts differ in configuration identity")
    identity = identities[0]
    require(identity.get("implementation_manifest_sha256") == manifest_sha,
            "Attempts were started under another implementation manifest than the current one (recheck at freeze failed)")
    baseline = identity.get("baseline_dev_results_zip_sha256")
    require(SHA256.fullmatch(str(baseline)), "Attempts carry no unchanged-DEV baseline ZIP hash (Amendment 2 item 6)")
    if baseline_dir is not None:
        problem = baseline_problem(baseline_dir, manifest_path, baseline)
        require(problem is None, f"Unchanged-DEV baseline: {problem}")
    records = []
    for slot, seed in current["retained"]:
        for arm in sorted(ARMS):
            attempt = current["slots"][slot]["arms"][arm]["valid_attempt"]
            record = ts.read_json(attempt_dir(train_root, arm, seed, attempt) / "final_adapter.json")
            require(not tp.valid_run_problems(record), f"{run_name(arm, seed)} attempt {attempt} is not a valid run")
            require(tp.attempt_outcome(attempt_dir(train_root, arm, seed, attempt))[0] == "valid",
                    f"{run_name(arm, seed)} attempt {attempt}: training report does not confirm a valid run")
            records.append(record)
    shared = {}
    for key in ("implementation_manifest_sha256", "exposure_order_file_sha256", "base_weight_shards_sha256",
                "baseline_dev_results_zip_sha256"):
        values = {json.dumps(r.get(key), sort_keys=True) for r in records}
        require(len(values) == 1 and records[0].get(key) is not None, f"Retained runs differ in (or lack) {key}")
        shared[key] = records[0][key]
    require(shared["implementation_manifest_sha256"] == manifest_sha, "Retained runs were trained under another implementation manifest")
    require(shared["exposure_order_file_sha256"] == identity.get("exposure_order_file_sha256"), "Retained runs differ from the logged exposure order")
    require(shared["baseline_dev_results_zip_sha256"] == baseline, "Retained runs differ from the logged unchanged-DEV baseline")
    S = current["S"]
    logs = {}
    for record in records:
        folder = attempt_dir(train_root, record["arm"], record["seed"], record["attempt"])
        require((folder / "train_report.json").is_file(), f"{folder}: training report missing")
        for name in ("train_report.json", "log.txt", "attempts.jsonl"):
            path = folder / name
            if path.is_file():
                logs[str(path.relative_to(train_root))] = ts.file_sha256(path)
    frozen = {"schema": FROZEN_SCHEMA, "base_model": MODEL_ID, "base_revision": MODEL_REVISION, **shared,
              "attempt_log_sha256": ts.file_sha256(log_path),
              "training_logs_sha256": logs,
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

def authorize_final_test(arguments):
    """Enforce the complete freeze before the executable entry point reads test bytes."""
    require(arguments.train_root is not None, "FINAL_TEST refused: --train-root is required for the freeze gate")
    require(getattr(arguments, "baseline_dir", None) is not None,
            "FINAL_TEST refused: --baseline-dir (the frozen unchanged-DEV run, Amendment 2 item 6) is required")
    folder = Path(arguments.inputs)
    check_preregistration((folder / "PREREGISTRATION.md").read_bytes(), PREREGISTRATION_SHA256)
    frozen = parse_frozen((folder / "ADAPTERS_FROZEN.md").read_text(encoding="utf-8"))
    require(ts.file_sha256(folder / "IMPLEMENTATION_MANIFEST.md") == frozen["implementation_manifest_sha256"],
            "FINAL_TEST refused: implementation manifest differs from the freeze")
    authorized = gate(frozen, arguments.train_root, baseline_dir=arguments.baseline_dir,
                      manifest_path=folder / "IMPLEMENTATION_MANIFEST.md")
    if arguments.adapter_record is not None:
        record = adapter_record(ts.read_json(arguments.adapter_record))
        require(any(record == item and Path(arguments.adapter_dir).resolve() == path.resolve()
                    for item, path in authorized), "FINAL_TEST refused: adapter is outside the frozen set")
    return frozen


def sealed_status(run_dir, manifest, archive):
    """Completion, checksum and infrastructure status only (no answers, no accuracy)."""
    errors = run_dir / "errors.jsonl"
    infrastructure = sum(1 for line in errors.read_text(encoding="utf-8").splitlines() if line.strip()) if errors.exists() else 0
    return {"run": run_dir.name, "status": manifest.get("status"), "completed": manifest.get("completed"),
            "expected": manifest.get("expected"), "unresolved": manifest.get("unresolved"),
            "attempts": manifest.get("attempts"), "infrastructure_failures": infrastructure,
            "results_zip": archive.name, "results_zip_sha256": sha256(archive.read_bytes()),
            "checksums_sha256": sha256((run_dir / "checksums.sha256").read_bytes())}


def recover_stale_lock(run_dir):
    """Amendment 2 item 5: remove a RUNNING.lock left by a killed runtime (the operator has confirmed that no other
    session is running this evaluation) and append a timestamped record; stored outputs are kept and never
    regenerated. Returns the record, or None when there is no lock."""
    run_dir = Path(run_dir)
    lock = run_dir / "RUNNING.lock"
    if not lock.exists():
        print(f"RECOVER_STALE_LOCK: {run_dir.name} has no RUNNING.lock; nothing to recover", flush=True)
        return None
    created = lock.read_text(encoding="utf-8", errors="replace")[:64]
    kept = sorted(p.name for p in (run_dir / "journal").glob("*.json")) if (run_dir / "journal").is_dir() else []
    recover_lock(run_dir, confirmed_no_active_writer=True)
    record = {"event": "stale_lock_recovered", "at": utc(), "run": run_dir.name, "lock_created_at": created,
              "operator_confirmed_no_active_writer": True, "journal_records_kept": len(kept),
              "journal_sha256": sha256(json.dumps(kept).encode("utf-8")),
              "rule": "PREREGISTRATION Amendment 2 item 5: the lock is removed; stored outputs are kept and never "
                      "regenerated; generation resumes from the journal"}
    path = run_dir.parent / f"{run_dir.name}_lock_recoveries.jsonl"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"RECOVER_STALE_LOCK: removed the stale RUNNING.lock of {run_dir.name} (recorded in {path.name}); "
          f"{len(kept)} stored journal records kept, nothing regenerated", flush=True)
    return record


def bind_implementation(run_dir, manifest_path):
    """Authenticate the running implementation against the manifest (verify_running_implementation; Sol re-review
    B3), then record it (first session) or check it (every later session) for the run."""
    run_dir = Path(run_dir)
    _, actual, verified = verify_running_implementation(manifest_path)
    path = run_dir.parent / f"{run_dir.name}_implementation.json"
    if path.is_file():
        bound = read(path)["implementation_manifest_sha256"]
        require(bound == actual, f"{run_dir.name} was started under implementation manifest {bound}, not {actual}: "
                                 "refusing to mix implementations in one run")
    else:
        require(not (run_dir / "run_manifest.json").exists(),
                f"{run_dir.name} was started without a recorded implementation manifest: use a new run directory")
        write(path, {"run": run_dir.name, "implementation_manifest_sha256": actual, "bound_at": utc(),
                     "running_code_verified_sha256": verified})
    return actual


def baseline_record(run_dir, manifest, archive, implementation_sha256, config, dataset):
    """Amendment 2 item 6: the record of a complete unchanged-model DEV run the trainer requires."""
    return {"schema": tp.BASELINE_SCHEMA, "run": Path(run_dir).name, "split": "dev", "mode": manifest.get("mode"),
            "adapter": config["adapter"], "model_id": config["model_id"], "model_revision": config["model_revision"],
            "implementation_manifest_sha256": implementation_sha256, "run_id": manifest.get("run_id"),
            "config_sha256": digest(config), "dataset_sha256": digest(dataset), "code_sha256": code_hash(),
            "split_sha256": manifest.get("split_sha256"), "dev_file_sha256": FROZEN["dev"][1],
            "status": manifest.get("status"), "completed": manifest.get("completed"), "expected": manifest.get("expected"),
            "unresolved": manifest.get("unresolved"), "results_zip": archive.name,
            "results_zip_sha256": sha256(archive.read_bytes()), "recorded_at": utc()}


def run_evaluate(arguments):
    split, run_dir = arguments.split, Path(arguments.run_dir)
    sealed = split == "final_test" or arguments.sealed  # FINAL_TEST can never be unsealed (Amendment 1 item 14)
    frozen = authorize_final_test(arguments) if split == "final_test" else None
    folder = Path(arguments.inputs)
    dataset, splits = inputs((folder / Path(FROZEN[split][0]).name).read_bytes(), split,
                             json.loads((folder / "identities.json").read_text(encoding="utf-8")))
    adapter = None
    if arguments.adapter_record:
        adapter = adapter_record(json.loads(Path(arguments.adapter_record).read_text(encoding="utf-8")))
    config = config_for(split, adapter)
    if getattr(arguments, "recover_stale_lock", False):
        recover_stale_lock(run_dir)
    implementation = None
    if getattr(arguments, "implementation_manifest", None) is not None:
        implementation = bind_implementation(run_dir, arguments.implementation_manifest)
    record_path = run_dir.parent / f"{run_dir.name}_baseline_record.json"
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists() and read(manifest_path).get("status") == "COMPLETE":
        manifest = read(manifest_path)
        require(all(manifest.get(key) == value for key, value in {
            "config_sha256": digest(config), "dataset_sha256": digest(dataset),
            "split_sha256": digest(splits), "code_sha256": code_hash(),
        }.items()), "Completed run identity differs: data/config/code changed; refusing to relabel stored outputs")
        print(run_dir.name, "already COMPLETE; nothing regenerated", flush=True)
        if record_path.is_file():  # the recorded baseline ZIP is never rewritten (its hash is in the attempt log)
            record = read(record_path)
            archive = run_dir.parent / record["results_zip"]
            require(archive.is_file() and sha256(archive.read_bytes()) == record["results_zip_sha256"],
                    f"{archive.name} differs from {record_path.name}")
            require(implementation in (None, record["implementation_manifest_sha256"]), "Baseline record is for another implementation manifest")
            print(f"Unchanged-DEV baseline record kept: {archive.name} SHA-256 {record['results_zip_sha256']}", flush=True)
            return 0
    else:
        from hinglish_pilot.hf_backend import HFBackend
        backend = HFBackend(config, adapter_path=arguments.adapter_dir)
        if frozen is not None:
            require(backend.metadata.get("base_weight_shards_sha256") == frozen["base_weight_shards_sha256"],
                    "FINAL_TEST refused: loaded base shards differ from the freeze")
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
    if split == "dev" and adapter is None and implementation is not None and metrics["status"] == "COMPLETE":
        record = baseline_record(run_dir, read(manifest_path), archive, implementation, config, dataset)
        write(record_path, record)
        try:  # Amendment 3 item 3: the recorded archive must itself validate as the registered baseline
            tp.verify_baseline(record_path.parent, arguments.implementation_manifest)
        except tp.Refused as error:
            record_path.rename(record_path.with_name(record_path.name + ".INVALID"))
            raise tp.ProtocolError(f"The completed unchanged-DEV run does not validate as the registered baseline: {error}")
        print(f"Unchanged-DEV baseline recorded (Amendment 2 item 6): {archive.name} SHA-256 {record['results_zip_sha256']}, "
              f"implementation manifest {implementation}", flush=True)
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
    for adapter, folder in gate(frozen, arguments.train_root, baseline_dir=arguments.baseline_dir,
                                manifest_path=arguments.manifest):
        print(run_name(adapter["arm"], adapter["seed"]), adapter["adapter_model_sha256"], folder)
    return 0


def run_freeze_manifest(arguments):
    frozen = freeze_manifest(arguments.train_root, manifest_path=arguments.manifest, root=arguments.root,
                             baseline_dir=arguments.baseline_dir)
    print("```json\n" + json.dumps(frozen, indent=2) + "\n```")
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
    evaluate.add_argument("--train-root", type=Path, help="Required for FINAL_TEST: recheck the complete adapter freeze")
    evaluate.add_argument("--sealed", action="store_true", help="Print only completion/checksum/infrastructure status")
    evaluate.add_argument("--implementation-manifest", type=Path,
                          help="IMPLEMENTATION_MANIFEST.md this run is made under (bound at the first session)")
    evaluate.add_argument("--baseline-dir", type=Path, help="Required for FINAL_TEST: the frozen unchanged-DEV run")
    evaluate.add_argument("--recover-stale-lock", action="store_true",
                          help="Only after confirming no other session runs this evaluation (Amendment 2 item 5)")
    gate_command = commands.add_parser("gate")
    gate_command.add_argument("--frozen", type=Path, required=True)
    gate_command.add_argument("--train-root", type=Path, required=True)
    gate_command.add_argument("--baseline-dir", type=Path)
    gate_command.add_argument("--manifest", type=Path, help="The frozen IMPLEMENTATION_MANIFEST.md (needed with --baseline-dir)")
    freeze = commands.add_parser("freeze-manifest")
    freeze.add_argument("--train-root", type=Path, required=True)
    freeze.add_argument("--baseline-dir", type=Path, required=True)
    freeze.add_argument("--manifest", type=Path, help="Default: phase2/IMPLEMENTATION_MANIFEST.md of this repository")
    freeze.add_argument("--root", type=Path, help="Repository root the manifest is rechecked against")
    arguments = parser.parse_args(argv)
    if arguments.command == "evaluate":
        require((arguments.adapter_dir is None) == (arguments.adapter_record is None), "Give --adapter-dir with --adapter-record")
    return {"evaluate": run_evaluate, "gate": run_gate, "freeze-manifest": run_freeze_manifest}[arguments.command](arguments)


if __name__ == "__main__":
    sys.exit(main())
