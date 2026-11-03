"""Phase-2 pre-registered analysis: phase2/PREREGISTRATION.md sections 6-8 as amended by Amendments 1 and 2.

Amendment 1 (commit b4fb956, D045) governs where it differs from sections 6-8: degenerate
intervals override every label (item 2); fixed bootstrap mechanics (item 4); no inferential
secondaries and no Holm (item 5); independent English-retention flags (item 6); the DEV
ceiling-risk proxy (item 7); attrition and unresolved items (item 12). Amendment 2 item 7
(commit 17986d4) binds the FINAL_TEST inputs: checkpoints, retained seeds, S and adapter hashes
come from ``phase2/ADAPTERS_FROZEN.md``, never from operator-supplied labels, and every run must
match the frozen backbone, mode, instruction, implementation manifest and attempt budget.

Standard library only (plus this repository's own pure-Python modules: the frozen
``numeric_literal_v1``, ``numeric_literal_v2`` and the safe ZIP reader).

Inputs are the 10 engine runs (9 adapters = arms EE/ER/EC x 3 seeds, plus the unchanged
model), each given as an engine run directory or its ``*_results.zip`` export (an outer ZIP
holding exactly one ``*_results.zip`` is also accepted), and the frozen dataset file the
runs were made from. The dataset file must have the SHA-256 of FINAL_TEST
(``phase2/final_test.v3.json``) or DEV (``phase2/dev.v2.json``) from section 1; anything
else is refused, and every run's dataset snapshot must match that file family by family.
DEV is accepted so the script can be tested before FINAL_TEST access (section 11).

Two separate routes:

* FINAL_TEST (the only route that produces results):

    python3 -B -m phase2_analysis.analyze --dataset phase2/final_test.v3.json \
        --frozen phase2/ADAPTERS_FROZEN.md --implementation-manifest phase2/IMPLEMENTATION_MANIFEST.md \
        --unchanged RUN --run EE:11=RUN --run ER:11=RUN --run EC:11=RUN ... \
        --ceiling-risk-proxy-k K --out NEW_DIR

  ``--frozen`` and ``--implementation-manifest`` are required. The retained seeds, S, the
  confirmatory flag and each slot's adapter identity and hashes are read from the freeze; the
  supplied ``--run`` set must be exactly the frozen set, and each run's recorded adapter must
  equal its frozen slot (a swapped, missing, extra or substituted run, or a trained label
  without an adapter, is refused). Each run must use Qwen/Qwen3-4B at the pinned revision,
  mode ``phase2_final_test``, the frozen instruction, the engine sources, configuration and
  backend recorded in the implementation manifest, and at most the configured number of
  attempts per prompt.

* DEV fixture / sanity route (``--dataset phase2/dev.v2.json``, no freeze): software check
  only. Its output is labelled "not results" and is never a Phase-2 result.

K is the unchanged model's DEV C strict count out of 40 (section 5 / Amendment 1 item 7).
With S = 3 retained seeds in the freeze the analysis is confirmatory; with S = 1 or 2 it is a
descriptive reduced-S report without decision or retention labels (Amendment 1 item 12).

Writes ``NEW_DIR/phase2_analysis.json`` and ``NEW_DIR/phase2_analysis.md``.
"""

import argparse
import hashlib
import json
import math
import platform
import random
import re
import statistics
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paper_analysis.safezip import read_zip, verify_checksums  # noqa: E402
from secondary_analysis import numeric_endpoint as numeric_v1  # noqa: E402
from secondary_analysis import numeric_literal_v2 as numeric_v2  # noqa: E402

ANALYSIS_VERSION = "phase2_analysis 3.0.0 (Amendments 1 and 2)"
DATASET_SHA256 = {
    "FINAL_TEST": "da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46",
    "DEV": "e741c1652f5b3dcaebc78d9dd9d7c31fdf4417306fbb2f0862149f27f858f28b",
}
SCORER_SHA256 = "c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc"
NUMERIC_V1_SHA256 = "ce70aefd1f4c03ffe80bbd06d4df025abe92fc0865732b6d2e6db13504ed883f"
QWEN_ID = "Qwen/Qwen3-4B"
QWEN_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
FROZEN_CONFIG = {"prompt_version": "test1-english-final-v2", "max_new_tokens": 1024, "context_limit": 2048,
                 "seed": 11, "thinking": False, "do_sample": False, "num_beams": 1, "quantization": "nf4",
                 "double_quantization": True, "compute_dtype": "float16", "attention_backend": "sdpa_math"}

# The frozen prompt test1-english-final-v2 (test1_pilot/hinglish_pilot/engine.py INSTRUCTION, D020).
FROZEN_INSTRUCTION = ("Solve the problem. Give a short explanation in English, even if the question is not "
                      "in English. End with exactly one line: FINAL: <number or fraction>, followed by its "
                      "unit in English only if the answer has a unit; write nothing after a pure number or fraction.")
FROZEN_INSTRUCTION_SHA256 = "3d0b516c9fb5978755e12bdd2a8b3c1742b605e2c3edc2e39fc2c53115dc7d63"
FINAL_TEST_MODE = "phase2_final_test"
FROZEN_SCHEMAS = ("phase2-adapters-frozen-3",)  # t4_smoke/phase2_eval.py FROZEN_SCHEMA (3: + DEV baseline ZIP hash)
IMPLEMENTATION_SCHEMA = "phase2-implementation-manifest-1"  # phase2/build_implementation_manifest.py SCHEMA
ENGINE_DIR = "test1_pilot/hinglish_pilot/"
MAX_ADAPTER_ATTEMPTS = 2  # t4_smoke/train_phase2.py MAX_ATTEMPTS (one from-scratch retry)
ADAPTER_FIELDS = ("arm", "seed", "attempt", "adapter_model_sha256", "adapter_config_sha256")
SHA256_HEX = re.compile("[0-9a-f]{64}")

FORMS = ("E", "R", "C")
ARMS = ("EE", "ER", "EC")
UNCHANGED = "unchanged"
SEEDS = (11, 22, 33)
RESERVE_SEEDS = (44, 55)
ENDPOINTS = ("strict", "numeric_literal_v1", "numeric_literal_v2")
BOOTSTRAP_SEED = 101
RESAMPLES = 10000
QUANTILES = (Fraction(25, 1000), Fraction(975, 1000))
# SHA-256 of the 10,000 x 100 matrix for N = 100 (see matrix_sha256); checked whenever N = 100.
FINAL_TEST_MATRIX_SHA256 = "33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1"
Z95 = 1.959963984540054
HOEFFDING_LOG = math.log(40)  # log(2 / alpha), alpha = .05
PP = Fraction(1, 100)  # one percentage point as a proportion
DIFFERENCE_BOUNDS = (-1, 1)  # family contrasts of accuracies
S3_BOUNDS = (-2, 2)  # family contrasts of differences (S3)
CONFIRMATORY_S = 3
RETENTION_MARGIN_PP = -2
USEFUL_MARGIN_PP = 5
DEV_FAMILIES = 40
CEILING_PROXY_THRESHOLD = 38  # >= 38/40 unchanged DEV C strict
CEILING_PROXY_NAME = "high unchanged-DEV accuracy (ceiling-risk proxy)"

# (name, form, first, second, description). second may be UNCHANGED.
DIFFERENCES = (
    ("delta_C", "C", "EC", "ER", "Primary: E+C − E+R on C"),
    ("ret_E_EC_EE", "E", "EC", "EE", "S1 English retention: E+C − E+E on E"),
    ("ret_E_EC_unchanged", "E", "EC", UNCHANGED, "S1: E+C − unchanged on E"),
    ("ret_E_ER_EE", "E", "ER", "EE", "S1: E+R − E+E on E"),
    ("ret_E_ER_unchanged", "E", "ER", UNCHANGED, "S1: E+R − unchanged on E"),
    ("ret_E_EE_unchanged", "E", "EE", UNCHANGED, "S1: E+E − unchanged on E"),
    ("T_R", "R", "ER", "EE", "S2 R transfer: E+R − E+E on R"),
    ("delta_R", "R", "EC", "ER", "S2: E+C − E+R on R"),
)
S3 = ("S3", "Δ_C − Δ_R per family (specificity)")
ESTIMAND_ORDER = tuple(d[0] for d in DIFFERENCES) + ("S3",)
RETENTION = ("ret_E_EC_EE", "ret_E_EC_unchanged", "ret_E_ER_EE", "ret_E_ER_unchanged", "ret_E_EE_unchanged")
TRADE_OFF_CONTRASTS = ("ret_E_EC_EE", "ret_E_EC_unchanged")
PER_SEED = ("delta_C", "ret_E_EC_EE", "T_R", "delta_R")


class AnalysisError(ValueError):
    """An input violates the pre-registered analysis contract."""


def require(condition, message):
    if not condition:
        raise AnalysisError(message)


def digest(value):
    """The engine's canonical JSON digest (test1_pilot/hinglish_pilot/data.py)."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------ frozen dataset

def load_frozen_dataset(path):
    """Return (role, sha256, families) or refuse a file that is not FINAL_TEST or DEV."""
    raw = Path(path).read_bytes()
    actual = sha256(raw)
    roles = [role for role, expected in DATASET_SHA256.items() if expected == actual]
    require(roles, f"Refused: dataset SHA-256 {actual} is neither the pre-registered FINAL_TEST nor the DEV hash")
    families = json.loads(raw)
    require(isinstance(families, list) and families, "Frozen dataset must be a non-empty list of families")
    ids = [f["family_id"] for f in families]
    require(len(ids) == len(set(ids)), "Duplicate family in frozen dataset")
    return roles[0], actual, families


CONTENT_FIELDS = ("family_id", "source_family_id", "template_group_id", "topic", "version", "provenance",
                  "reference_equation", "reference_solution_en", "gold")


def check_snapshot(dataset, families, role):
    """Every family's content in the run snapshot equals the frozen file (wrapper fields aside)."""
    require(isinstance(dataset, dict) and isinstance(dataset.get("families"), list), "Run dataset snapshot malformed")
    frozen = {f["family_id"]: f for f in families}
    snap = {f.get("family_id"): f for f in dataset["families"]}
    require(len(snap) == len(dataset["families"]) and set(snap) == set(frozen),
            f"Refused: run families differ from the frozen {role} families")
    for fid, family in frozen.items():
        other = snap[fid]
        for field in CONTENT_FIELDS:
            require(other.get(field) == family.get(field), f"Refused: {fid} {field} differs from the frozen {role} file")
        require(set(other.get("forms", {})) == set(FORMS), f"Refused: {fid} lacks E/R/C")
        for form in FORMS:
            for field in ("rendering_id", "text"):
                require(other["forms"][form].get(field) == family["forms"][form].get(field),
                        f"Refused: {fid} {form} {field} differs from the frozen {role} file")


# ------------------------------------------------------------------ engine runs

def _json(blob, name):
    try:
        return json.loads(blob)
    except (ValueError, UnicodeDecodeError):
        raise AnalysisError(f"{name} is not valid JSON") from None


def read_run_members(path):
    """{name: bytes} for an engine run directory or its results ZIP (checksums verified)."""
    path = Path(path)
    if path.is_dir():
        require(not (path / "RUNNING.lock").exists(), f"{path}: stop the run writer before analysis")
        members = {}
        for name in ("run_manifest.json", "experiment_config.json", "dataset.json", "generation_attempts.jsonl"):
            require((path / name).is_file(), f"{path}: missing {name}")
            members[name] = (path / name).read_bytes()
        for source in sorted((path / "source").glob("*.py")):
            members["source/" + source.name] = source.read_bytes()
        journal = sorted((path / "journal").glob("*.json"))
        if journal:  # the authoritative per-attempt files; generation_attempts.jsonl is a summary
            members["generation_attempts.jsonl"] = b"".join(
                json.dumps(_json(p.read_bytes(), p.name), ensure_ascii=False).encode() + b"\n" for p in journal)
        return members, "directory"
    require(path.is_file(), f"Input not found: {path}")
    members = read_zip(path.read_bytes(), path.name)
    if "run_manifest.json" not in members:
        inner = sorted(name for name in members if name.endswith("_results.zip"))
        require(len(inner) == 1, f"{path.name}: expected a results ZIP or an outer ZIP with exactly one *_results.zip")
        members = read_zip(members[inner[0]], f"{path.name}!{inner[0]}")
    verify_checksums(members, path.name)
    return members, "zip"


def load_run(path):
    """Verify one engine run and return its identity, completeness and selected attempts."""
    members, kind = read_run_members(path)
    for name in ("run_manifest.json", "experiment_config.json", "dataset.json", "generation_attempts.jsonl"):
        require(name in members, f"{path}: missing {name}")
    manifest = _json(members["run_manifest.json"], "run_manifest.json")
    config = _json(members["experiment_config.json"], "experiment_config.json")
    dataset = _json(members["dataset.json"], "dataset.json")
    require(digest(config) == manifest.get("config_sha256"), f"{path}: config snapshot does not match manifest")
    require(digest(dataset) == manifest.get("dataset_sha256"), f"{path}: dataset snapshot does not match manifest")
    require(manifest.get("scorer_version") == "1.0.0", f"{path}: strict scorer must be v1.0.0")
    scorer = members.get("source/scorer_v1.py")
    require(scorer is not None and sha256(scorer) == SCORER_SHA256,
            f"{path}: engine source snapshot lacks the frozen scorer_v1.py (SHA-256 {SCORER_SHA256})")
    journal = [_json(line, "generation_attempts.jsonl") for line in members["generation_attempts.jsonl"].splitlines()
               if line.strip()]
    order = manifest.get("evaluation_order")
    renderings = {}
    for family in dataset["families"]:
        for form in FORMS:
            renderings[family["forms"][form]["rendering_id"]] = (family["family_id"], form, family["gold"])
    require(isinstance(order, list) and len(order) == len(set(order)) and set(order) == set(renderings),
            f"{path}: evaluation order does not match the dataset snapshot")
    retries = config.get("max_infrastructure_retries")
    require(type(retries) is int and retries in (0, 1), f"{path}: max_infrastructure_retries must be 0 or 1")
    budget = 1 + retries  # attempts per prompt allowed by the run's own configuration
    grouped, attempt_ids = {}, set()
    for attempt in journal:
        require(attempt.get("record_sha256") == digest({k: v for k, v in attempt.items() if k != "record_sha256"}),
                f"{path}: attempt checksum corruption")
        require(attempt.get("run_id") == manifest["run_id"] and attempt.get("config_sha256") == manifest["config_sha256"],
                f"{path}: foreign attempt record")
        require(attempt.get("rendering_id") in renderings, f"{path}: unknown rendering in attempts")
        require(attempt["attempt_id"] not in attempt_ids, f"{path}: duplicate attempt id")
        attempt_ids.add(attempt["attempt_id"])
        grouped.setdefault(attempt["rendering_id"], []).append(attempt)
    selected = {}
    for rid in order:
        history = sorted(grouped.get(rid, []), key=lambda row: row["attempt_number"])
        require([row["attempt_number"] for row in history] == list(range(1, len(history) + 1)),
                f"{path}: attempt sequence corrupt")
        require(len(history) <= budget, f"Refused: {path}: rendering {rid} has {len(history)} attempts, above the "
                                        f"configured budget of {budget} (1 + {retries} infrastructure retry)")
        generated = [row for row in history if row["status"] == "generated"]
        require(len(generated) <= 1 and (not generated or generated[0] is history[-1]),
                f"{path}: a rendering has more than one scored attempt")
        if generated:
            row = generated[0]
            fid, form, gold = renderings[rid]
            require((row["family_id"], row["form"]) == (fid, form) and row.get("gold", gold) == gold,
                    f"{path}: attempt/dataset identity mismatch")
            require(type(row["correct"]) is bool and isinstance(row["raw_response"], str)
                    and type(row["truncated"]) is bool and row.get("scorer_version") == "1.0.0",
                    f"{path}: malformed stored strict score")
            selected[rid] = row
    # A generated response is resolved whatever its answer (missing/invalid answers score 0).
    # A rendering without a generated attempt (absent, or infrastructure retries exhausted) is unresolved.
    complete = manifest.get("status") == "COMPLETE" and len(selected) == len(order)
    sources = {name[len("source/"):]: sha256(blob) for name, blob in members.items() if name.startswith("source/")}
    return dict(path=str(path), kind=kind, manifest=manifest, config=config, dataset=dataset,
                selected=selected, complete=complete, expected=len(order), completed=len(selected),
                unresolved=len(order) - len(selected), sources=sources, attempt_budget=budget,
                attempts=len(journal), archive_sha256=sha256(Path(path).read_bytes()) if kind == "zip" else None)


def check_config(config, role):
    for key, value in FROZEN_CONFIG.items():
        require(config.get(key) == value, f"Refused: run config {key}={config.get(key)!r}, pre-registered {value!r}")
    require(config.get("instruction") == FROZEN_INSTRUCTION,
            "Refused: run instruction is not the frozen test1-english-final-v2 text")
    require(config.get("max_infrastructure_retries") in (0, 1), "Refused: more than one infrastructure retry")
    if role == "FINAL_TEST":
        # Amendment 1 item 15 / Amendment 2 item 7: any other backbone (Llama-3.2-3B included) is an error.
        require(config.get("model_id") == QWEN_ID,
                f"Refused: FINAL_TEST model {config.get('model_id')!r} is not {QWEN_ID}; every other backbone, "
                "Llama-3.2-3B included, is excluded from this registration (Amendment 1 item 15)")
        require(config.get("model_revision") == QWEN_REVISION and config.get("tokenizer_revision") == QWEN_REVISION,
                f"Refused: FINAL_TEST runs must use the pinned Qwen3-4B revision {QWEN_REVISION}")
        require(config.get("mode") == FINAL_TEST_MODE,
                f"Refused: FINAL_TEST run mode {config.get('mode')!r}, required {FINAL_TEST_MODE!r}")


# ------------------------------------------------------------------ freeze and implementation manifest

def _json_block(text, name):
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.S)
    require(match is not None, f"{name} has no ```json block")
    try:
        value = json.loads(match.group(1))
    except ValueError:
        raise AnalysisError(f"{name}: the ```json block is not valid JSON") from None
    require(isinstance(value, dict), f"{name}: the ```json block must be an object")
    return value


def _is_sha(value):
    return isinstance(value, str) and SHA256_HEX.fullmatch(value) is not None


def parse_frozen(text):
    """Checkpoint binding from phase2/ADAPTERS_FROZEN.md (schema of t4_smoke/phase2_eval.py freeze_manifest).

    Returns the retained seeds (sorted), S, the slot of each seed, the confirmatory flag, the frozen
    adapter entry of every (arm, seed) and the unchanged-model entry (base model, revision, shard hashes)."""
    frozen = _json_block(text, "ADAPTERS_FROZEN.md")
    require(frozen.get("schema") in FROZEN_SCHEMAS, f"Freeze schema must be one of {FROZEN_SCHEMAS}")
    require(frozen.get("base_model") == QWEN_ID and frozen.get("base_revision") == QWEN_REVISION,
            f"Freeze base must be {QWEN_ID} at {QWEN_REVISION}")
    for field in ("implementation_manifest_sha256", "baseline_dev_results_zip_sha256"):
        require(_is_sha(frozen.get(field)), f"Freeze {field} must be a SHA-256")
    shards = frozen.get("base_weight_shards_sha256")
    require(isinstance(shards, dict) and shards and all(_is_sha(v) for v in shards.values()),
            "Freeze must include base_weight_shards_sha256")
    retained = frozen.get("retained_seeds")
    require(isinstance(retained, list) and all(isinstance(e, dict) and set(e) == {"slot", "seed"} for e in retained),
            "Freeze retained_seeds must be a list of {slot, seed}")
    S = len(retained)
    require(frozen.get("S") == S, "Freeze S must equal the number of retained seeds")
    require(S >= 1, "S = 0: no complete seed triplet, so FINAL_TEST is never accessed (Amendment 1 item 12)")
    require(S <= 3, "At most three retained seed triplets")
    slots = [e["slot"] for e in retained]
    seeds = [e["seed"] for e in retained]
    require(all(type(x) is int for x in slots + seeds), "Freeze slots and seeds must be integers")
    require(len(set(slots)) == S and set(slots) <= set(SEEDS), "Each retained slot is one of 11/22/33, once")
    require(len(set(seeds)) == S and all(seed == slot or seed in RESERVE_SEEDS for slot, seed in zip(slots, seeds)),
            "Each retained seed is its own slot or a reserve (44/55), used once")
    confirmatory = S == CONFIRMATORY_S
    require(frozen.get("confirmatory") is confirmatory and frozen.get("descriptive_only") is (not confirmatory),
            f"S = {S}: freeze must carry confirmatory {confirmatory} and descriptive_only {not confirmatory}")
    adapters = frozen.get("adapters")
    require(isinstance(adapters, list) and len(adapters) == 3 * S, f"The freeze must list exactly {3 * S} adapters")
    entries = {}
    for entry in adapters:
        require(isinstance(entry, dict) and set(entry) == set(ADAPTER_FIELDS), "Freeze adapter entry fields")
        require(entry["arm"] in ARMS and entry["seed"] in seeds, "Freeze adapter arm/seed outside the retained set")
        require(type(entry["attempt"]) is int and 1 <= entry["attempt"] <= MAX_ADAPTER_ATTEMPTS, "Attempt must be 1 or 2")
        require(_is_sha(entry["adapter_model_sha256"]) and _is_sha(entry["adapter_config_sha256"]),
                "Freeze adapter hashes must be SHA-256")
        key = (entry["arm"], entry["seed"])
        require(key not in entries, f"Freeze lists {key[0]}:{key[1]} twice")
        entries[key] = dict(entry)
    require(set(entries) == {(a, s) for a in ARMS for s in seeds}, "Each retained seed needs exactly one EE, ER and EC adapter")
    return dict(seeds=sorted(seeds), S=S, slot_of={seed: slot for slot, seed in zip(slots, seeds)},
                confirmatory=confirmatory, adapters=entries,
                unchanged=dict(model_id=QWEN_ID, model_revision=QWEN_REVISION, adapter=None,
                               base_weight_shards_sha256=dict(shards)),
                implementation_manifest_sha256=frozen["implementation_manifest_sha256"],
                baseline_dev_results_zip_sha256=frozen["baseline_dev_results_zip_sha256"])


def load_frozen(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise AnalysisError(f"{path} is not UTF-8") from None
    return dict(parse_frozen(text), path=str(path), sha256=sha256(raw))


def parse_implementation_manifest(text):
    """The engine sources, execution configuration, prompt and backend identity recorded in
    phase2/IMPLEMENTATION_MANIFEST.md (phase2/build_implementation_manifest.py)."""
    doc = _json_block(text, "IMPLEMENTATION_MANIFEST.md")
    require(doc.get("schema") == IMPLEMENTATION_SCHEMA, f"Implementation manifest schema must be {IMPLEMENTATION_SCHEMA}")
    files, groups = doc.get("files"), doc.get("groups")
    require(isinstance(files, dict) and isinstance(groups, dict) and isinstance(groups.get("engine"), list)
            and groups["engine"], "Implementation manifest lacks the engine file group")
    engine = {}
    for path in groups["engine"]:
        require(isinstance(path, str) and path.startswith(ENGINE_DIR) and "/" not in path[len(ENGINE_DIR):]
                and _is_sha(files.get(path)), f"Implementation manifest engine entry {path!r} malformed")
        engine[path[len(ENGINE_DIR):]] = files[path]
    require(engine.get("scorer_v1.py") == SCORER_SHA256, "Implementation manifest scorer_v1.py is not the frozen scorer")
    prompt = doc.get("prompt") or {}
    require(prompt.get("version") == FROZEN_CONFIG["prompt_version"] and prompt.get("instruction_sha256") == FROZEN_INSTRUCTION_SHA256,
            "Refused: the implementation manifest records an instruction other than the frozen test1-english-final-v2 text")
    model = doc.get("model") or {}
    require(model.get("id") == QWEN_ID and model.get("revision") == QWEN_REVISION
            and model.get("tokenizer_revision") == QWEN_REVISION,
            f"Refused: the implementation manifest model is not {QWEN_ID} at {QWEN_REVISION}")
    template = (model.get("chat_template") or {}).get("digest")
    require(_is_sha(template), "Implementation manifest lacks the chat-template digest")
    generation = doc.get("generation_config") or {}
    config_sha = (generation.get("engine_config_sha256") or {}).get("final_test")
    require(_is_sha(config_sha), "Implementation manifest lacks the FINAL_TEST engine configuration hash")
    retries = (generation.get("decoding") or {}).get("max_infrastructure_retries")
    require(type(retries) is int and retries in (0, 1), "Implementation manifest lacks max_infrastructure_retries")
    return dict(engine_sources=engine, engine_code_sha256=digest(engine), chat_template_sha256=template,
                final_test_config_sha256=config_sha, max_infrastructure_retries=retries)


def load_implementation_manifest(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise AnalysisError(f"{path} is not UTF-8") from None
    return dict(parse_implementation_manifest(text), path=str(path), sha256=sha256(raw))


def check_final_test_run(key, run, binding, implementation):
    """Amendment 2 item 7: bind one FINAL_TEST run to its frozen slot and to the implementation manifest."""
    name = checkpoint_name(key)
    config, manifest = run["config"], run["manifest"]
    check_config(config, "FINAL_TEST")
    require(manifest.get("mode") == FINAL_TEST_MODE, f"Refused: {name}: run manifest mode {manifest.get('mode')!r}")
    # Checkpoint identity from the freeze, never from the operator's label.
    adapter = config.get("adapter", "missing")
    if key[0] == UNCHANGED:
        require(adapter is None, f"Refused: {name}: the unchanged-model run has an adapter loaded")
    else:
        require(isinstance(adapter, dict), f"Refused: {name}: no adapter loaded under a trained-arm label")
        frozen = binding["adapters"][key]
        require(adapter == frozen,
                f"Refused: {name}: run adapter {adapter.get('arm')}:{adapter.get('seed')} attempt {adapter.get('attempt')} "
                f"(model {str(adapter.get('adapter_model_sha256'))[:12]}…, config {str(adapter.get('adapter_config_sha256'))[:12]}…) "
                f"is not the frozen slot {frozen['arm']}:{frozen['seed']} attempt {frozen['attempt']} "
                f"(model {frozen['adapter_model_sha256'][:12]}…, config {frozen['adapter_config_sha256'][:12]}…)")
    # Execution configuration, engine sources and backend from the implementation manifest.
    require(digest(dict(config, adapter=None)) == implementation["final_test_config_sha256"],
            f"Refused: {name}: execution configuration differs from the implementation manifest")
    require(config.get("max_infrastructure_retries") == implementation["max_infrastructure_retries"]
            and run["attempt_budget"] == 1 + implementation["max_infrastructure_retries"],
            f"Refused: {name}: attempt budget differs from the implementation manifest")
    sources, expected = run["sources"], implementation["engine_sources"]
    differ = sorted(n for n in set(sources) | set(expected) if sources.get(n) != expected.get(n))
    require(not differ, f"Refused: {name}: engine source snapshot differs from the implementation manifest: {', '.join(differ)}")
    require(manifest.get("code_sha256") == implementation["engine_code_sha256"],
            f"Refused: {name}: engine code hash differs from the implementation manifest")
    backend = manifest.get("backend")
    require(isinstance(backend, dict) and backend.get("backend") == "huggingface",
            f"Refused: {name}: backend is not the Hugging Face backend")
    require(backend.get("model_revision") == QWEN_REVISION and backend.get("tokenizer_revision") == QWEN_REVISION,
            f"Refused: {name}: backend revision differs from the pinned revision")
    require(backend.get("chat_template_sha256") == implementation["chat_template_sha256"],
            f"Refused: {name}: backend chat template differs from the implementation manifest")
    require(backend.get("adapter", "missing") == config.get("adapter"), f"Refused: {name}: backend adapter differs from config")
    require(backend.get("base_weight_shards_sha256") == binding["unchanged"]["base_weight_shards_sha256"],
            f"Refused: {name}: base weight shards differ from the freeze")
    sessions = manifest.get("sessions") or []
    require(all(isinstance(s, dict) and s.get("backend") == backend for s in sessions),
            f"Refused: {name}: a resumed session ran on a different backend")


def _load_runs(checkpoints):
    require(len({str(Path(p).resolve()) for p in checkpoints.values()}) == len(checkpoints), "The same input was given twice")
    runs = {key: load_run(path) for key, path in checkpoints.items()}
    require(len({r["manifest"]["run_id"] for r in runs.values()}) == len(runs), "Two inputs share one run_id")
    require(len({r["manifest"]["dataset_sha256"] for r in runs.values()}) == 1,
            "Refused: runs were made from different dataset snapshots (pairing broken)")
    return runs


def _common_model(runs, families, role):
    configs = set()
    for run in runs.values():
        check_snapshot(run["dataset"], families, role)
        check_config(run["config"], role)
        configs.add((run["config"].get("model_id"), run["config"].get("prompt_version"), run["config"].get("instruction")))
    require(len(configs) == 1, "Refused: runs differ in base model or prompt")
    return next(iter(configs))[0]


def assemble_final_test(data_sha, families, checkpoints, frozen, implementation_manifest):
    """FINAL_TEST route: denominators, seeds and checkpoint identities come from the freeze (Amendment 2 item 7)."""
    require(frozen is not None, "Refused: FINAL_TEST analysis requires --frozen phase2/ADAPTERS_FROZEN.md "
                                "(Amendment 2 item 7)")
    require(implementation_manifest is not None, "Refused: FINAL_TEST analysis requires --implementation-manifest "
                                                 "phase2/IMPLEMENTATION_MANIFEST.md (Amendment 2 item 7)")
    binding = load_frozen(frozen)
    implementation = load_implementation_manifest(implementation_manifest)
    require(implementation["sha256"] == binding["implementation_manifest_sha256"],
            "Refused: the implementation manifest is not the one recorded in the freeze")
    expected = {(a, s) for a in ARMS for s in binding["seeds"]} | {(UNCHANGED, None)}
    supplied = set(checkpoints)
    missing = sorted(map(checkpoint_name, expected - supplied))
    extra = sorted(map(checkpoint_name, supplied - expected))
    require(not missing and not extra,
            f"Refused: supplied runs differ from the frozen checkpoint set (retained seeds {binding['seeds']}, "
            f"S = {binding['S']}): missing {missing or 'none'}; extra or substituted {extra or 'none'}")
    runs = _load_runs(checkpoints)
    for key, run in runs.items():
        check_final_test_run(key, run, binding, implementation)
    model_id = _common_model(runs, families, "FINAL_TEST")
    seeds, S = binding["seeds"], binding["S"]
    warnings = []
    if seeds != list(SEEDS):
        mapping = ", ".join(f"{binding['slot_of'][s]}→{s}" for s in seeds)
        warnings.append(f"Retained seeds from the freeze: {seeds} (slot→seed {mapping}; S = {S}).")
    if not binding["confirmatory"]:
        warnings.append(f"S = {S} < 3 in the freeze: descriptive reduced-S report only (1/S averaging); no decision or "
                        "retention label (Amendment 1 item 12).")
    analysis_type = (f"confirmatory (S = {S}, retained seeds from the freeze)" if binding["confirmatory"] else
                     f"descriptive reduced-S report (S = {S}, from the freeze); no labels")
    freeze = dict(path=binding["path"], sha256=binding["sha256"], retained_seeds=[
        dict(slot=binding["slot_of"][s], seed=s) for s in seeds], S=S, confirmatory=binding["confirmatory"],
        baseline_dev_results_zip_sha256=binding["baseline_dev_results_zip_sha256"],
        implementation_manifest=dict(path=implementation["path"], sha256=implementation["sha256"]))
    return dict(role="FINAL_TEST", dataset_sha256=data_sha, families=families, runs=runs, seeds=seeds,
                model_id=model_id, warnings=warnings, labels=binding["confirmatory"], analysis_type=analysis_type,
                freeze=freeze)


DEV_NOT_RESULTS = ("DEV fixture route: software and sanity check only; nothing from this route is a Phase-2 result, "
                   "labels on DEV are not results (sections 5 and 11). It is not bound to the adapter freeze.")


def assemble_dev(data_sha, families, checkpoints):
    """DEV fixture route (kept separate from FINAL_TEST): operator-labelled runs, never results."""
    keys = list(checkpoints)
    require(sum(k[0] == UNCHANGED for k in keys) == 1, "Exactly one unchanged-model run is required")
    seeds = sorted({k[1] for k in keys if k[0] != UNCHANGED})
    require(seeds, "Refused: S = 0 (no complete trained seed triplet); FINAL_TEST is not accessed (Amendment 1 item 12)")
    require(len(seeds) <= 3 and all(s in SEEDS + RESERVE_SEEDS for s in seeds),
            f"Seeds must be 1-3 of {SEEDS + RESERVE_SEEDS}")
    require(set(keys) == {(a, s) for a in ARMS for s in seeds} | {(UNCHANGED, None)},
            "Every seed needs all three arms (paired triplets; section 10)")
    runs = _load_runs(checkpoints)
    model_id = _common_model(runs, families, "DEV")
    S = len(seeds)
    warnings = [DEV_NOT_RESULTS]
    if seeds != list(SEEDS):
        warnings.append(f"Seeds analysed: {seeds} (pre-registered 11/22/33; S = {S}).")
    if S < CONFIRMATORY_S:
        warnings.append(f"S = {S} < 3: reduced-S report (1/S averaging); no decision or retention label "
                        "(Amendment 1 item 12).")
    analysis_type = (f"not results: DEV fixture route (S = {S}; label code exercised)" if S == CONFIRMATORY_S else
                     f"not results: DEV fixture route, reduced-S (S = {S}); no labels")
    return dict(role="DEV", dataset_sha256=data_sha, families=families, runs=runs, seeds=seeds, model_id=model_id,
                warnings=warnings, labels=S == CONFIRMATORY_S, analysis_type=analysis_type, freeze=None)


def assemble(dataset_path, checkpoints, frozen=None, implementation_manifest=None):
    """checkpoints: {(arm, seed) or (UNCHANGED, None): path}. Returns the verified study.

    FINAL_TEST requires ``frozen`` (phase2/ADAPTERS_FROZEN.md) and ``implementation_manifest``;
    DEV is the separate fixture route and refuses both."""
    role, data_sha, families = load_frozen_dataset(dataset_path)
    if role == "FINAL_TEST":
        return assemble_final_test(data_sha, families, checkpoints, frozen, implementation_manifest)
    require(frozen is None and implementation_manifest is None,
            "Refused: --frozen/--implementation-manifest bind FINAL_TEST only; the DEV fixture route is separate")
    return assemble_dev(data_sha, families, checkpoints)


# ------------------------------------------------------------------ outcomes

def outcomes(study):
    """y[endpoint][checkpoint][family_id][form] in {0, 1}; strict = stored scorer v1.0.0."""
    gold = {f["family_id"]: f["gold"] for f in study["families"]}
    y = {e: {} for e in ENDPOINTS}
    for key, run in study["runs"].items():
        for e in ENDPOINTS:
            y[e][key] = {fid: {} for fid in gold}
        for row in run["selected"].values():
            fid, form = row["family_id"], row["form"]
            y["strict"][key][fid][form] = int(row["correct"])
            y["numeric_literal_v1"][key][fid][form] = int(
                numeric_v1.evaluate_numeric(row["raw_response"], gold[fid], row["truncated"])["correct"])
            y["numeric_literal_v2"][key][fid][form] = int(
                numeric_v2.evaluate_numeric(row["raw_response"], gold[fid], row["truncated"])["correct"])
    return y


def family_numerators(y, family_ids, seeds):
    """Integer numerators n_i with d_i = n_i / S for every estimand (seed-averaged per family)."""
    S = len(seeds)
    out = {}
    for name, form, first, second, _ in DIFFERENCES:
        values = []
        for fid in family_ids:
            a = sum(y[(first, s)][fid][form] for s in seeds)
            b = S * y[(UNCHANGED, None)][fid][form] if second == UNCHANGED else sum(y[(second, s)][fid][form] for s in seeds)
            values.append(a - b)
        out[name] = values
    out["S3"] = [c - r for c, r in zip(out["delta_C"], out["delta_R"])]
    return out


# ------------------------------------------------------------------ inference

def bootstrap_indices(n, resamples=RESAMPLES, seed=BOOTSTRAP_SEED):
    """The shared resampling matrix (Amendment 1 item 4).

    A fresh random.Random(seed) fills `resamples` rows of n draws rng.randrange(n) in row-major
    order. With FINAL_TEST (N = 100) this is the pre-registered 10,000 x 100 matrix; it is
    reused for every endpoint, contrast and per-seed interval. Row j of the matrix applies to
    the records sorted by family ID."""
    rng = random.Random(seed)
    return [[rng.randrange(n) for _ in range(n)] for _ in range(resamples)]


def matrix_sha256(indices):
    """SHA-256 of the matrix as UTF-8 text: one line per row, decimal indices joined by ',', '\n' after every row."""
    h = hashlib.sha256()
    for row in indices:
        h.update((",".join(map(str, row)) + "\n").encode())
    return h.hexdigest()


def resample_sums(numerators, indices):
    get = numerators.__getitem__
    return [sum(map(get, draw)) for draw in indices]


def quantile(sorted_values, p):
    """Linear quantile: h = (R - 1) p (= 9999 p for R = 10,000), interpolating sorted entries floor(h) and ceil(h)."""
    position = (len(sorted_values) - 1) * p
    low, high = math.floor(position), math.ceil(position)
    return Fraction(sorted_values[low]) + (sorted_values[high] - sorted_values[low]) * (position - low)


def wilson(k, n):
    p = k / n
    center = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    radius = Z95 * math.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return [max(0.0, center - radius), min(1.0, center + radius)]


def hoeffding_radius(n, width):
    """Two-sided 95% Hoeffding radius (b - a) sqrt(log(40) / (2N)) for a mean of n values in [a, b]."""
    return width * math.sqrt(HOEFFDING_LOG / (2 * n))


def hoeffding_interval(point, n, bounds):
    """Hoeffding interval intersected with [a, b] (Amendment 1 item 4)."""
    a, b = bounds
    radius = hoeffding_radius(n, b - a)
    return [max(float(a), float(point) - radius), min(float(b), float(point) + radius)], radius


def wald_interval(values):
    """Wald 95% on the family values: sample SD (ddof 1), z = 1.959963984540054."""
    n = len(values)
    mean = statistics.fmean(values)
    half = Z95 * statistics.stdev(values) / math.sqrt(n) if n > 1 else 0.0
    return [mean - half, mean + half]


def mcnemar_exact(first_only, second_only):
    n = first_only + second_only
    if n == 0:
        return Fraction(1)
    tail = sum(math.comb(n, k) for k in range(min(first_only, second_only) + 1))
    return min(Fraction(1), Fraction(2 * tail, 2 ** n))


def _pp(value):
    return float(value * 100)


def bootstrap_tails(sums, scale, reference_pp):
    """Both bootstrap tails at a reference value (descriptive counts, never p-values)."""
    threshold = Fraction(reference_pp) * PP * scale
    return dict(reference_pp=reference_pp, resamples=len(sums), at_or_below=sum(1 for s in sums if s <= threshold),
                at_or_above=sum(1 for s in sums if s >= threshold))


def interval_summary(numerators, denominator, indices, bounds=DIFFERENCE_BOUNDS, references=(0,), sums=None):
    """Point, 95% percentile bootstrap, Wald and clipped Hoeffding intervals for mean_i(n_i / denominator).

    `sums` may be given precomputed (they must equal resample_sums(numerators, indices));
    phase2_analysis/calibrate.py uses this to simulate the identical procedure faster."""
    n = len(numerators)
    scale = denominator * n
    if sums is None:
        sums = resample_sums(numerators, indices)
    ordered = sorted(sums)
    lower = quantile(ordered, QUANTILES[0]) / scale
    upper = quantile(ordered, QUANTILES[1]) / scale
    point = Fraction(sum(numerators), scale)
    hoeffding, radius = hoeffding_interval(point, n, bounds)
    wald = wald_interval([x / denominator for x in numerators])
    distinct = len(set(numerators))
    return dict(
        estimate=point, lower=lower, upper=upper,
        estimate_pp=_pp(point), bootstrap_95_pp=[_pp(lower), _pp(upper)],
        exact=dict(estimate=str(point), lower=str(lower), upper=str(upper)),
        wald_95_pp=[100 * wald[0], 100 * wald[1]],
        hoeffding_95_pp=[100 * hoeffding[0], 100 * hoeffding[1]], hoeffding_radius_pp=100 * radius,
        hoeffding_bounds=list(bounds),
        distinct_family_values=distinct, nonzero_family_contrasts=sum(1 for x in numerators if x),
        all_contrasts_identical=distinct == 1, zero_width=lower == upper,
        degenerate=distinct == 1 or lower == upper,
        bootstrap_tails=[bootstrap_tails(sums, scale, r) for r in references],
        families=n, _sums=sums, _scale=scale)


# ------------------------------------------------------------------ labels (section 8 + Amendment 1)

USEFUL, SUPPORT, NULL, HARM, INCONCLUSIVE = ("Useful support", "Support", "Informative null", "Harm", "Inconclusive")
DEGENERATE = "inconclusive—degenerate empirical interval"
NULL_MEANING = ("'Informative null' rules out gains of 5 pp or more under the approximate sampling model; it does "
                "not establish equality or exclude harm.")
WITHIN, LOSS, BEYOND, TRADE_OFF = ("within-margin criterion met", "loss detected", "loss beyond margin",
                                   "retention trade-off")
NOT_ESTABLISHED = "no retention criterion met"


def decision_label(lower, upper, degenerate=False):
    """Section 8 label from the unrounded strict bootstrap bounds (proportions, not pp).

    Amendment 1 item 2: a degenerate interval (all family contrasts identical, or zero width)
    is labelled DEGENERATE before the table is consulted."""
    if degenerate or lower == upper:
        return DEGENERATE
    L, U = lower / PP, upper / PP  # exact pp
    if L > USEFUL_MARGIN_PP:
        return USEFUL
    if 0 < L <= USEFUL_MARGIN_PP:
        return SUPPORT
    if U < 0:
        return HARM
    if L <= 0 and U >= USEFUL_MARGIN_PP:
        return INCONCLUSIVE
    require(L <= 0 <= U < USEFUL_MARGIN_PP, "label rules not exhaustive")  # unreachable
    return NULL


def retention_flags(lower, upper, degenerate, primary_label, trade_off_eligible):
    """Amendment 1 item 6: independent descriptive flags for one English contrast (margin −2 pp).

    within-margin criterion met iff L > −2; loss detected iff U < 0; loss beyond margin iff
    U < −2; retention trade-off (EC − EE and EC − unchanged only) iff the primary label is
    Support or Useful support and U < −2. Equality never satisfies a strict inequality. The
    degeneracy override (item 2) takes precedence and suppresses every flag."""
    if degenerate or lower == upper:
        return dict(override=DEGENERATE, within_margin_criterion_met=False, loss_detected=False,
                    loss_beyond_margin=False, retention_trade_off=False if trade_off_eligible else None,
                    flags=[DEGENERATE])
    L, U = lower / PP, upper / PP
    within, loss, beyond = L > RETENTION_MARGIN_PP, U < 0, U < RETENTION_MARGIN_PP
    trade = (primary_label in (SUPPORT, USEFUL) and U < RETENTION_MARGIN_PP) if trade_off_eligible else None
    flags = [name for name, on in ((WITHIN, within), (LOSS, loss), (BEYOND, beyond), (TRADE_OFF, trade)) if on]
    return dict(override=None, within_margin_criterion_met=within, loss_detected=loss, loss_beyond_margin=beyond,
                retention_trade_off=trade, flags=flags or [NOT_ESTABLISHED])


# ------------------------------------------------------------------ descriptive

def stratum(provenance):
    """Operation-word stratum from frozen provenance: keep / switch / none (else unclassified)."""
    # Phrasings used by the GPT-drafted DEV/FINAL_TEST style, the Claude-drafted TRAIN style and Pilot-B.
    p = provenance.casefold()
    hits = set()
    if any(s in p for s in ("c kept this operation word", "c keeps it", "c keeps them", "c kept the hindi operation word")):
        hits.add("keep")
    if any(s in p for s in ("c replaced this operation word", "c switches it to english", "c switches them to english",
                            "c switched them to english", "c switched this operation word")):
        hits.add("switch")
    if any(s in p for s in ("no focal lexicon operation word", "no lexicon operation word in r",
                            "r uses no lexicon operation", "no hindi operation word")):
        hits.add("none")
    return hits.pop() if len(hits) == 1 else "unclassified"


def _stats(values):
    clean = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if not clean:
        return dict(n=0)
    return dict(n=len(clean), mean=statistics.fmean(clean), median=statistics.median(clean),
                min=min(clean), max=max(clean), sum=sum(clean))


def checkpoint_name(key):
    return UNCHANGED if key[0] == UNCHANGED else f"{key[0]}:{key[1]}"


# ------------------------------------------------------------------ analysis

def ceiling_risk_proxy(k):
    """Amendment 1 item 7: unchanged-model DEV C strict count k/40, its Wilson interval and DEV headroom."""
    require(type(k) is int and 0 <= k <= DEV_FAMILIES,
            f"ceiling-risk proxy must be the unchanged DEV C strict count, an integer 0-{DEV_FAMILIES}")
    return dict(name=CEILING_PROXY_NAME, correct=k, n=DEV_FAMILIES, accuracy=k / DEV_FAMILIES,
                wilson_95=wilson(k, DEV_FAMILIES), dev_headroom=1 - k / DEV_FAMILIES,
                threshold=f">= {CEILING_PROXY_THRESHOLD}/{DEV_FAMILIES}", fired=k >= CEILING_PROXY_THRESHOLD,
                note="A proxy from the unchanged model on DEV; it does not establish a ceiling for the trained "
                     "comparator. Δ_C stays first in the report and S2 stays descriptive.")


def analyze(study, ceiling_proxy_k):
    proxy = ceiling_risk_proxy(ceiling_proxy_k)
    runs, seeds = study["runs"], study["seeds"]
    family_ids = sorted(f["family_id"] for f in study["families"])  # records sorted by family ID (item 4)
    N, S = len(family_ids), len(seeds)
    require(S >= 1, "S = 0: no analysis (Amendment 1 item 12)")
    labelled = study["labels"]  # FINAL_TEST: the freeze's confirmatory flag; DEV: S = 3 (code exercised, not results)
    require(not labelled or S == CONFIRMATORY_S, "labels need S = 3")
    result = dict(
        analysis_version=ANALYSIS_VERSION,
        preregistration="phase2/PREREGISTRATION.md sections 6-8 as amended by Amendment 1 (b4fb956, D045) and "
                        "Amendment 2 (17986d4, D046)",
        dataset_role=study["role"], dataset_sha256=study["dataset_sha256"], families=N, seeds=seeds, S=S,
        analysis_type=study["analysis_type"], results=study["role"] == "FINAL_TEST",
        freeze=study["freeze"], model_id=study["model_id"], ceiling_risk_proxy=proxy,
        warnings=list(study["warnings"]),
        python_version=platform.python_version(), python_implementation=platform.python_implementation(),
        code_sha256={"phase2_analysis/analyze.py": sha256(Path(__file__).read_bytes()),
                     "secondary_analysis/numeric_endpoint.py": sha256(Path(numeric_v1.__file__).read_bytes()),
                     "secondary_analysis/numeric_literal_v2.py": sha256(Path(numeric_v2.__file__).read_bytes())},
        inputs=[dict(checkpoint=checkpoint_name(k), path=r["path"], kind=r["kind"], run_id=r["manifest"]["run_id"],
                     archive_sha256=r["archive_sha256"], manifest_dataset_sha256=r["manifest"]["dataset_sha256"],
                     config_sha256=r["manifest"]["config_sha256"], model_revision=r["config"].get("model_revision"),
                     adapter=r["config"].get("adapter"),
                     status="COMPLETE" if r["complete"] else "INCOMPLETE", completed=r["completed"],
                     unresolved=r["unresolved"], expected=r["expected"], attempts=r["attempts"])
                for k, r in sorted(runs.items(), key=_order)])
    require(sha256(Path(numeric_v1.__file__).read_bytes()) == NUMERIC_V1_SHA256,
            "numeric_literal_v1 source differs from the pre-registered SHA-256")
    if not all(r["complete"] for r in runs.values()):
        result["status"] = "INCOMPLETE"
        result["unresolved_items"] = sum(r["unresolved"] for r in runs.values())
        result["note"] = ("At least one required evaluation item is unresolved (absent, or infrastructure retries "
                          "exhausted): the primary analysis and its decision label are suppressed (section 10, "
                          "Amendment 1 item 12). No complete-case analysis is made.")
        return result
    result["status"] = "COMPLETE"
    y = outcomes(study)
    indices = bootstrap_indices(N)
    if N == 100:
        require(matrix_sha256(indices) == FINAL_TEST_MATRIX_SHA256,
                f"Bootstrap matrix differs from the pinned 10,000 x 100 matrix (Python {platform.python_version()})")
    result["bootstrap"] = dict(
        seed=BOOTSTRAP_SEED, resamples=RESAMPLES, families=N,
        generator=f"fresh random.Random({BOOTSTRAP_SEED}); {RESAMPLES} rows x {N} draws of rng.randrange({N}), row-major",
        matrix_sha256=matrix_sha256(indices),
        matrix_hash_encoding="UTF-8 text, one line per row, indices joined by ',', newline after every row",
        record_order="family ID, sorted lexicographically", shared_matrix=True,
        interval="95% percentile, linear quantile h = (R - 1) p at p = .025/.975",
        wald="sample SD (ddof 1), z = 1.959963984540054",
        hoeffding="(b - a) sqrt(log(40)/(2N)) intersected with [a, b]: [-1, 1] for differences, [-2, 2] for S3",
        crossed_family_seed_resampling="not run (Amendment 1 item 4)",
        note=("Approximate interval conditional on the trained checkpoints; does not cover training-seed variance. "
              "The 100-family mean is a finite-set descriptive quantity; intervals describe hypothetical independent "
              "families from this fixed authoring and review process (template and author dependence is a "
              "limitation). Δ_C is the effect of the complete training-rendering recipe, not an isolated effect of "
              "code-switching (Amendment 1 item 3)."))
    by_family = {f["family_id"]: f for f in study["families"]}
    result["endpoints"] = {}
    for endpoint in ENDPOINTS:
        yy = y[endpoint]
        nums = family_numerators(yy, family_ids, seeds)
        estimands = {}
        for name, form, first, second, text in DIFFERENCES + ((S3[0], "", "", "", S3[1]),):
            bounds = S3_BOUNDS if name == "S3" else DIFFERENCE_BOUNDS
            references = (0, USEFUL_MARGIN_PP) if name == "delta_C" else \
                (0, RETENTION_MARGIN_PP) if name in RETENTION else (0,)
            estimands[name] = dict(interval_summary(nums[name], S, indices, bounds, references), description=text)
        block = dict(estimands=estimands)
        # Per seed (section 7): own paired bootstrap on the same matrix + exact McNemar (descriptive only).
        per_seed = {}
        for name in PER_SEED:
            _, form, first, second, text = next(d for d in DIFFERENCES if d[0] == name)
            rows = {}
            for s in seeds:
                a = [yy[(first, s)][fid][form] for fid in family_ids]
                b = [yy[(second, s)][fid][form] for fid in family_ids]
                summary = interval_summary([x - z for x, z in zip(a, b)], 1, indices, DIFFERENCE_BOUNDS)
                first_only = sum(1 for x, z in zip(a, b) if x and not z)
                second_only = sum(1 for x, z in zip(a, b) if z and not x)
                p = mcnemar_exact(first_only, second_only)
                rows[str(s)] = dict(summary, first_only=first_only, second_only=second_only,
                                    mcnemar_exact_p=float(p), mcnemar_exact_p_exact=str(p))
            points = [rows[str(s)]["estimate"] for s in seeds]
            per_seed[name] = dict(description=text, seeds=rows, range_pp=[_pp(min(points)), _pp(max(points))],
                                  signs=dict(positive=sum(p > 0 for p in points), zero=sum(p == 0 for p in points),
                                             negative=sum(p < 0 for p in points)),
                                  note="Descriptive: McNemar p-values and sign consistency are never used as tests.")
        block["per_seed"] = per_seed
        # Absolute accuracy per checkpoint, Wilson 95% over that checkpoint's N outcomes (never pooled seed rows).
        accuracy = {}
        for key in sorted(runs, key=_order):
            accuracy[checkpoint_name(key)] = {}
            for form in FORMS:
                k = sum(yy[key][fid][form] for fid in family_ids)
                accuracy[checkpoint_name(key)][form] = dict(correct=k, n=N, accuracy=k / N, wilson_95=wilson(k, N))
        block["accuracy"] = accuracy
        block["arm_mean_accuracy"] = {arm: {form: sum(yy[(arm, s)][fid][form] for s in seeds for fid in family_ids) / (N * S)
                                            for form in FORMS} for arm in ARMS}
        block["ER_C_headroom"] = 1 - block["arm_mean_accuracy"]["ER"]["C"]
        # Operation-word strata (descriptive, counts and percentages only).
        strata = {}
        for fid, n_c in zip(family_ids, nums["delta_C"]):
            st = strata.setdefault(stratum(by_family[fid]["provenance"]), dict(families=0, delta_C_numerator=0,
                                    C_correct={**{a: 0 for a in ARMS}, UNCHANGED: 0}))
            st["families"] += 1
            st["delta_C_numerator"] += n_c
            for arm in ARMS:
                st["C_correct"][arm] += sum(yy[(arm, s)][fid]["C"] for s in seeds)
            st["C_correct"][UNCHANGED] += yy[(UNCHANGED, None)][fid]["C"]
        for st in strata.values():
            n = st["families"]
            st["delta_C_pp"] = 100 * st.pop("delta_C_numerator") / (n * S)
            st["C_accuracy_pct"] = {arm: 100 * st["C_correct"][arm] / (n * S) for arm in ARMS}
            st["C_accuracy_pct"][UNCHANGED] = 100 * st["C_correct"][UNCHANGED] / n
            st["C_denominators"] = dict(arms=n * S, unchanged=n)
        block["strata"] = dict(sorted(strata.items()))
        block["decision_label"] = None
        block["retention_flags"] = None
        if endpoint != "strict":
            block["note"] = "Secondary endpoint: same analysis, descriptive only; labels use strict only."
        elif not labelled:
            block["note"] = (f"Reduced-S report (S = {S}): descriptive only; no decision or retention label "
                             "(Amendment 1 item 12).")
        else:
            primary = estimands["delta_C"]
            label = decision_label(primary["lower"], primary["upper"], primary["degenerate"])
            block["decision_label"] = label
            block["decision_bounds_exact"] = dict(L=str(primary["lower"]), U=str(primary["upper"]))
            block["retention_flags"] = {
                name: retention_flags(estimands[name]["lower"], estimands[name]["upper"], estimands[name]["degenerate"],
                                      label, name in TRADE_OFF_CONTRASTS) for name in RETENTION}
            if label == NULL:
                block["null_meaning"] = NULL_MEANING
        result["endpoints"][endpoint] = block
    result["secondaries"] = ("All secondary contrasts, numeric endpoints and per-seed McNemar p-values are descriptive; "
                             "no Holm or other inferential secondary analysis (Amendment 1 item 5).")
    # Strict-invalid reasons, tokens and latency per checkpoint and form.
    diagnostics = {}
    for key in sorted(runs, key=_order):
        rows = list(runs[key]["selected"].values())
        diagnostics[checkpoint_name(key)] = {form: dict(
            invalid_reasons=dict(Counter(r["invalid_reason"] for r in rows if r["form"] == form and r["invalid_reason"])),
            truncated=sum(r["truncated"] for r in rows if r["form"] == form),
            input_tokens=_stats([r.get("input_tokens") for r in rows if r["form"] == form]),
            output_tokens=_stats([r.get("output_tokens") for r in rows if r["form"] == form]),
            latency_seconds=_stats([r.get("latency_seconds") for r in rows if r["form"] == form])) for form in FORMS}
    result["diagnostics"] = diagnostics
    if any("unclassified" in result["endpoints"][e]["strata"] for e in ENDPOINTS):
        result["warnings"].append("Some families have provenance that matches no operation-word stratum ('unclassified').")
    return result


def _order(item):
    key = item[0] if isinstance(item, tuple) and isinstance(item[0], tuple) else item
    return (1, 0, 0) if key[0] == UNCHANGED else (0, ARMS.index(key[0]), key[1])


# ------------------------------------------------------------------ output

def to_json(result):
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if not k.startswith("_") and k not in ("estimate", "lower", "upper")}
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, Fraction):
            return str(value)
        return value
    return json.dumps(clean(result), indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def _f(x, digits=1):
    return f"{x:+.{digits}f}"


def _interval(summary):
    lo, hi = summary["bootstrap_95_pp"]
    return f"{_f(summary['estimate_pp'], 2)} pp [{_f(lo, 2)}, {_f(hi, 2)}]"


def _tails(summary):
    return "; ".join(f"≤ {t['reference_pp']:+g} pp: {t['at_or_below']}/{t['resamples']}, "
                     f"≥ {t['reference_pp']:+g} pp: {t['at_or_above']}/{t['resamples']}" for t in summary["bootstrap_tails"])


def markdown(result):
    role = result["dataset_role"]
    proxy = result["ceiling_risk_proxy"]
    lines = [f"# Phase-2 pre-registered analysis — {role}", ""]
    if role == "DEV":
        lines += ["**DEV RUNS — NOT RESULTS. DEV fixture route: software and sanity check only, not bound to the "
                  "adapter freeze. Nothing here is a Phase-2 result; labels on DEV are printed only to exercise the "
                  "code (sections 5 and 11).**", ""]
    lines += [f"Analysis `{result['analysis_version']}`; plan `{result['preregistration']}`.",
              f"Dataset SHA-256 `{result['dataset_sha256']}` ({role}); {result['families']} families; seeds "
              f"{', '.join(map(str, result['seeds']))} (S = {result['S']}); base `{result['model_id']}`.",
              f"Status: **{result['status']}**. Analysis type: **{result['analysis_type']}**. "
              f"Python {result['python_version']}.", ""]
    if result.get("freeze"):
        fz = result["freeze"]
        lines += [f"Checkpoints, retained seeds and S from `{fz['path']}` (SHA-256 `{fz['sha256']}`): slot→seed "
                  + ", ".join(f"{e['slot']}→{e['seed']}" for e in fz["retained_seeds"]) + f"; S = {fz['S']}; "
                  f"confirmatory {fz['confirmatory']}. Implementation manifest `{fz['implementation_manifest']['path']}` "
                  f"(SHA-256 `{fz['implementation_manifest']['sha256']}`); unchanged-DEV baseline results ZIP "
                  f"`{fz['baseline_dev_results_zip_sha256']}`. Every run's adapter and hashes, model, mode, "
                  "instruction, engine sources, configuration, backend and attempt budget were checked against them "
                  "(Amendment 2 item 7).", ""]
    lines += [f"- Warning: {w}" for w in result["warnings"]]
    lines += ["", "## Inputs", "", "| Checkpoint | Run ID | Status | Completed | Unresolved | Attempts | Source |",
              "|---|---|---|---:|---:|---:|---|"]
    for i in result["inputs"]:
        lines.append(f"| {i['checkpoint']} | `{i['run_id']}` | {i['status']} | {i['completed']}/{i['expected']} | "
                     f"{i['unresolved']} | {i['attempts']} | {i['kind']} |")
    if result["status"] != "COMPLETE":
        lines += ["", result["note"], ""]
        return "\n".join(lines) + "\n"
    strict = result["endpoints"]["strict"]
    est = strict["estimands"]
    primary = est["delta_C"]
    boot = result["bootstrap"]
    label = strict["decision_label"]
    # Δ_C always comes first (Amendment 1 item 7).
    lines += ["", "## Primary: Δ_C (strict, E+C − E+R on C)", "",
              f"- Δ_C = {_interval(primary)} (95% paired family bootstrap, {boot['resamples']:,} resamples, seed "
              f"{boot['seed']}; matrix SHA-256 `{boot['matrix_sha256']}`).",
              f"- Precision: bootstrap half-width {(primary['bootstrap_95_pp'][1] - primary['bootstrap_95_pp'][0]) / 2:.2f} pp.",
              f"- E+R C headroom (1 − mean y_ER,C): {100 * strict['ER_C_headroom']:.2f} pp.",
              (f"- **Decision label: {label}** (from unrounded bounds L = {primary['exact']['lower']}, "
               f"U = {primary['exact']['upper']} as proportions)." if label is not None else
               f"- No decision label: {strict['note']}"),
              f"- Wald 95%: [{_f(primary['wald_95_pp'][0], 2)}, {_f(primary['wald_95_pp'][1], 2)}] pp; Hoeffding 95% "
              f"(clipped to [−1, 1]): [{_f(primary['hoeffding_95_pp'][0], 2)}, {_f(primary['hoeffding_95_pp'][1], 2)}] pp "
              f"(radius {primary['hoeffding_radius_pp']:.1f} pp).",
              f"- Non-zero family contrasts: {primary['nonzero_family_contrasts']}/{primary['families']}; distinct d_i "
              f"values: {primary['distinct_family_values']}; degenerate: {primary['degenerate']}.",
              f"- Bootstrap tails: {_tails(primary)}.", ""]
    if strict.get("null_meaning"):
        lines += [strict["null_meaning"], ""]
    lines += [f"{proxy['name'][0].upper() + proxy['name'][1:]}: unchanged DEV C {proxy['correct']}/{proxy['n']} "
              f"({100 * proxy['accuracy']:.1f}%; Wilson 95% {100 * proxy['wilson_95'][0]:.1f}–{100 * proxy['wilson_95'][1]:.1f}; "
              f"DEV headroom {100 * proxy['dev_headroom']:.1f} pp); threshold {proxy['threshold']}: "
              f"**{'fired' if proxy['fired'] else 'not fired'}**. {proxy['note']}", "",
              boot["note"], ""]
    lines += ["## S2: R transfer (descriptive)", "",
              f"- T_R (E+R − E+E on R) = {_interval(est['T_R'])}",
              f"- Δ_R (E+C − E+R on R) = {_interval(est['delta_R'])}", ""]
    lines += ["## S1: English retention (descriptive flags; margin −2 pp)", "",
              "| Estimand | Estimate [95% bootstrap] | Non-zero | Flags |", "|---|---|---:|---|"]
    for name in RETENTION:
        flags = strict["retention_flags"][name]["flags"] if strict["retention_flags"] else ["(no flags: reduced S)"]
        lines.append(f"| {est[name]['description']} | {_interval(est[name])} | {est[name]['nonzero_family_contrasts']} | "
                     f"{'; '.join(flags)} |")
    lines += ["", "Flags are independent descriptive criteria, not multiplicity-controlled non-inferiority.", "",
              "## S3: specificity (descriptive)", "", f"- Δ_C − Δ_R per family = {_interval(est['S3'])} "
              f"(Hoeffding radius {est['S3']['hoeffding_radius_pp']:.1f} pp for values in [−2, 2], clipped)", "",
              result["secondaries"], ""]
    lines += ["## All estimands, all endpoints", "",
              "| Estimand | strict | numeric_literal_v1 | numeric_literal_v2 |", "|---|---|---|---|"]
    for name in ESTIMAND_ORDER:
        cells = [_interval(result["endpoints"][e]["estimands"][name]) for e in ENDPOINTS]
        lines.append(f"| {est[name]['description']} | " + " | ".join(cells) + " |")
    lines += ["", "| Estimand (strict) | Non-zero families | Degenerate | Wald 95% | Hoeffding 95% | Bootstrap tails |",
              "|---|---:|---|---|---|---|"]
    for name in ESTIMAND_ORDER:
        e = est[name]
        lines.append(f"| {e['description']} | {e['nonzero_family_contrasts']} | {e['degenerate']} | "
                     f"[{_f(e['wald_95_pp'][0], 2)}, {_f(e['wald_95_pp'][1], 2)}] | "
                     f"[{_f(e['hoeffding_95_pp'][0], 2)}, {_f(e['hoeffding_95_pp'][1], 2)}] | {_tails(e)} |")
    lines += ["", "Decision and retention labels use strict only.", "", "## Per seed (strict, descriptive)", "",
              "| Estimand | Seed | Estimate [95% bootstrap] | First only | Second only | Exact McNemar p |",
              "|---|---:|---|---:|---:|---:|"]
    for name, block in strict["per_seed"].items():
        for seed, row in block["seeds"].items():
            lines.append(f"| {block['description']} | {seed} | {_interval(row)} | {row['first_only']} | "
                         f"{row['second_only']} | {row['mcnemar_exact_p']:.4g} |")
    lines += ["", "Range across seeds and signs (descriptive, never a test):", ""]
    for name, block in strict["per_seed"].items():
        lines.append(f"- {block['description']}: range [{_f(block['range_pp'][0])}, {_f(block['range_pp'][1])}] pp; "
                     f"positive/zero/negative seeds {block['signs']['positive']}/{block['signs']['zero']}/{block['signs']['negative']}")
    lines += ["", "Crossed family × seed resampling is not run (Amendment 1 item 4).", ""]
    for endpoint in ENDPOINTS:
        block = result["endpoints"][endpoint]
        lines += [f"## Accuracy by checkpoint — {endpoint} (Wilson 95% over N per checkpoint)", "",
                  "| Checkpoint | E | R | C |", "|---|---|---|---|"]
        for name, forms in block["accuracy"].items():
            lines.append(f"| {name} | " + " | ".join(
                f"{a['correct']}/{a['n']} ({100 * a['accuracy']:.1f}%; {100 * a['wilson_95'][0]:.1f}–{100 * a['wilson_95'][1]:.1f})"
                for a in forms.values()) + " |")
        lines.append("")
    lines += ["## Operation-word strata (strict; descriptive counts and percentages)", "",
              "| Stratum | Families | Δ_C (pp) | C acc EE | C acc ER | C acc EC | C acc unchanged |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, st in strict["strata"].items():
        c = st["C_accuracy_pct"]
        lines.append(f"| {name} | {st['families']} | {_f(st['delta_C_pp'])} | "
                     + " | ".join(f"{st['C_correct'][k]} ({c[k]:.1f}%)" for k in (*ARMS, UNCHANGED)) + " |")
    lines += ["", "## Strict-invalid reasons, tokens and latency", "",
              "| Checkpoint | Form | Invalid reasons | Truncated | Median output tokens | Median latency (s) |",
              "|---|---|---|---:|---:|---:|"]
    for name, forms in result["diagnostics"].items():
        for form, d in forms.items():
            reasons = ", ".join(f"{k} {v}" for k, v in sorted(d["invalid_reasons"].items())) or "none"
            lines.append(f"| {name} | {form} | {reasons} | {d['truncated']} | {d['output_tokens'].get('median')} | "
                         f"{d['latency_seconds'].get('median')} |")
    lines += ["", "Code SHA-256: " + "; ".join(f"`{k}` `{v}`" for k, v in result["code_sha256"].items()), ""]
    return "\n".join(lines) + "\n"


def parse_checkpoints(unchanged, runs):
    checkpoints = {(UNCHANGED, None): unchanged}
    for spec in runs:
        head, sep, path = spec.partition("=")
        arm, colon, seed = head.partition(":")
        require(sep and colon and arm in ARMS and seed.isdigit(), f"--run must look like EC:11=PATH, got {spec!r}")
        key = (arm, int(seed))
        require(key not in checkpoints, f"Duplicate checkpoint {head}")
        checkpoints[key] = path
    return checkpoints


def run_analysis(dataset, checkpoints, ceiling_proxy_k, out, frozen=None, implementation_manifest=None):
    out = Path(out)
    require(not out.exists() or not any(out.iterdir()), f"Output directory {out} must be new or empty")
    study = assemble(dataset, checkpoints, frozen, implementation_manifest)
    result = analyze(study, ceiling_proxy_k)
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase2_analysis.json").write_text(to_json(result), encoding="utf-8")
    (out / "phase2_analysis.md").write_text(markdown(result), encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dataset", required=True, help="frozen FINAL_TEST or DEV JSON file the runs were made from")
    parser.add_argument("--unchanged", required=True, help="unchanged-model run directory or results ZIP")
    parser.add_argument("--run", action="append", default=[], help="ARM:SEED=PATH for each adapter run (ARM in EE/ER/EC)")
    parser.add_argument("--ceiling-risk-proxy-k", required=True, type=int, metavar="K",
                        help=f"unchanged-model DEV C strict count out of {DEV_FAMILIES}; "
                             f"'{CEILING_PROXY_NAME}' fires at >= {CEILING_PROXY_THRESHOLD}")
    parser.add_argument("--frozen", help="FINAL_TEST (required): phase2/ADAPTERS_FROZEN.md; checkpoints, retained "
                                         "seeds, S and adapter hashes are taken from it. Not accepted for DEV.")
    parser.add_argument("--implementation-manifest", help="FINAL_TEST (required): phase2/IMPLEMENTATION_MANIFEST.md, "
                                                          "the one recorded in the freeze. Not accepted for DEV.")
    parser.add_argument("--out", required=True, help="new output directory")
    args = parser.parse_args(argv)
    try:
        result = run_analysis(args.dataset, parse_checkpoints(args.unchanged, args.run), args.ceiling_risk_proxy_k,
                              args.out, args.frozen, args.implementation_manifest)
    except (AnalysisError, ValueError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    label = result["endpoints"]["strict"]["decision_label"] if result["status"] == "COMPLETE" else None
    print(f"{result['dataset_role']} {result['status']} {result['analysis_type']}" + (f": {label}" if label else ""))
    return 0 if result["status"] == "COMPLETE" else 3


if __name__ == "__main__":
    sys.exit(main())
