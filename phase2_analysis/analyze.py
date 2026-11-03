"""Phase-2 pre-registered analysis: phase2/PREREGISTRATION.md sections 6-8, exactly.

Standard library only (plus this repository's own pure-Python modules: the frozen
``numeric_literal_v1``, ``numeric_literal_v2`` and the safe ZIP reader).

Inputs are the 10 engine runs (9 adapters = arms EE/ER/EC x 3 seeds, plus the unchanged
model), each given as an engine run directory or its ``*_results.zip`` export (an outer ZIP
holding exactly one ``*_results.zip`` is also accepted), and the frozen dataset file the
runs were made from. The dataset file must have the SHA-256 of FINAL_TEST
(``phase2/final_test.v3.json``) or DEV (``phase2/dev.v2.json``) from section 1; anything
else is refused, and every run's dataset snapshot must match that file family by family.
DEV is accepted so the script can be tested before FINAL_TEST access (section 11).

Usage (from the repository root):

    python3 -B -m phase2_analysis.analyze --dataset phase2/final_test.v3.json \
        --unchanged RUN --run EE:11=RUN --run ER:11=RUN --run EC:11=RUN ... \
        --ceiling-flag not_fired --out NEW_DIR [--holm]

Writes ``NEW_DIR/phase2_analysis.json`` and ``NEW_DIR/phase2_analysis.md``.
"""

import argparse
import hashlib
import json
import math
import random
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

ANALYSIS_VERSION = "phase2_analysis 1.0.0"
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

FORMS = ("E", "R", "C")
ARMS = ("EE", "ER", "EC")
UNCHANGED = "unchanged"
SEEDS = (11, 22, 33)
RESERVE_SEEDS = (44, 55)
ENDPOINTS = ("strict", "numeric_literal_v1", "numeric_literal_v2")
BOOTSTRAP_SEED = 101
RESAMPLES = 10000
ALPHA = Fraction(5, 100)
Z95 = 1.959963984540054
PP = Fraction(1, 100)  # one percentage point as a proportion

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
PER_SEED = ("delta_C", "ret_E_EC_EE", "T_R", "delta_R")
HOLM_FAMILY = ("ret_E_EC_EE", "T_R", "S3")


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
    complete = manifest.get("status") == "COMPLETE" and len(selected) == len(order)
    return dict(path=str(path), kind=kind, manifest=manifest, config=config, dataset=dataset,
                selected=selected, complete=complete, expected=len(order), completed=len(selected),
                attempts=len(journal), archive_sha256=sha256(Path(path).read_bytes()) if kind == "zip" else None)


def check_config(config, role):
    for key, value in FROZEN_CONFIG.items():
        require(config.get(key) == value, f"Refused: run config {key}={config.get(key)!r}, pre-registered {value!r}")
    require(config.get("max_infrastructure_retries") in (0, 1), "Refused: more than one infrastructure retry")
    if role == "FINAL_TEST" and config.get("model_id") == QWEN_ID:
        require(config.get("model_revision") == QWEN_REVISION and config.get("tokenizer_revision") == QWEN_REVISION,
                f"Refused: FINAL_TEST runs must use the pinned Qwen3-4B revision {QWEN_REVISION}")


def assemble(dataset_path, checkpoints):
    """checkpoints: {(arm, seed) or (UNCHANGED, None): path}. Returns the verified study."""
    role, data_sha, families = load_frozen_dataset(dataset_path)
    keys = list(checkpoints)
    require(sum(k[0] == UNCHANGED for k in keys) == 1, "Exactly one unchanged-model run is required")
    seeds = sorted({k[1] for k in keys if k[0] != UNCHANGED})
    require(1 <= len(seeds) <= 3 and all(s in SEEDS + RESERVE_SEEDS for s in seeds),
            f"Seeds must be 1-3 of {SEEDS + RESERVE_SEEDS}")
    require(set(keys) == {(a, s) for a in ARMS for s in seeds} | {(UNCHANGED, None)},
            "Every seed needs all three arms (paired triplets; section 10)")
    require(len({str(Path(p).resolve()) for p in checkpoints.values()}) == len(keys), "The same input was given twice")
    runs = {key: load_run(path) for key, path in checkpoints.items()}
    require(len({r["manifest"]["run_id"] for r in runs.values()}) == len(runs), "Two inputs share one run_id")
    snapshot = {r["manifest"]["dataset_sha256"] for r in runs.values()}
    require(len(snapshot) == 1, "Refused: runs were made from different dataset snapshots (pairing broken)")
    configs = set()
    for run in runs.values():
        check_snapshot(run["dataset"], families, role)
        check_config(run["config"], role)
        configs.add((run["config"].get("model_id"), run["config"].get("prompt_version"), run["config"].get("instruction")))
    require(len(configs) == 1, "Refused: runs differ in base model or prompt")
    warnings = []
    if seeds != list(SEEDS):
        warnings.append(f"Seeds analysed: {seeds} (pre-registered 11/22/33; S = {len(seeds)}).")
    model_id = next(iter(configs))[0]
    if role == "FINAL_TEST" and model_id != QWEN_ID:
        warnings.append(f"Backbone {model_id} is not the primary Qwen3-4B (secondary backbone, section 5).")
    if role == "DEV":
        warnings.append("DEV runs: software and sanity check only; labels on DEV are not results (sections 5 and 11).")
    return dict(role=role, dataset_sha256=data_sha, families=families, runs=runs, seeds=seeds,
                model_id=model_id, warnings=warnings)


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
    """One index sequence shared by every estimand: random.Random(seed), n draws per resample."""
    rng = random.Random(seed)
    return [[rng.randrange(n) for _ in range(n)] for _ in range(resamples)]


def resample_sums(numerators, indices):
    get = numerators.__getitem__
    return [sum(map(get, draw)) for draw in indices]


def quantile(sorted_values, p):
    """Linear-interpolation percentile (the engine's report.quantile), exact in Fractions."""
    position = (len(sorted_values) - 1) * p
    low, high = math.floor(position), math.ceil(position)
    return Fraction(sorted_values[low]) + (sorted_values[high] - sorted_values[low]) * (position - low)


def wilson(k, n):
    p = k / n
    center = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    radius = Z95 * math.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return [max(0.0, center - radius), min(1.0, center + radius)]


def hoeffding_radius(n, width, alpha=0.05):
    """Two-sided Hoeffding radius for a mean of n independent values bounded in an interval of the given width."""
    return width * math.sqrt(math.log(2 / alpha) / (2 * n))


def mcnemar_exact(first_only, second_only):
    n = first_only + second_only
    if n == 0:
        return Fraction(1)
    tail = sum(math.comb(n, k) for k in range(min(first_only, second_only) + 1))
    return min(Fraction(1), Fraction(2 * tail, 2 ** n))


def _pp(value):
    return float(value * 100)


def interval_summary(numerators, denominator, indices, width):
    """Point, 95% percentile bootstrap, Wald and Hoeffding intervals for mean_i(n_i / denominator)."""
    n = len(numerators)
    scale = denominator * n
    sums = resample_sums(numerators, indices)
    ordered = sorted(sums)
    lower = quantile(ordered, Fraction(25, 1000)) / scale
    upper = quantile(ordered, Fraction(975, 1000)) / scale
    point = Fraction(sum(numerators), scale)
    d = [x / denominator for x in numerators]
    sd = statistics.stdev(d) if n > 1 else 0.0
    half = Z95 * sd / math.sqrt(n)
    radius = hoeffding_radius(n, width)
    distinct = len(set(numerators))
    return dict(
        estimate=point, lower=lower, upper=upper,
        estimate_pp=_pp(point), bootstrap_95_pp=[_pp(lower), _pp(upper)],
        exact=dict(estimate=str(point), lower=str(lower), upper=str(upper)),
        wald_95_pp=[100 * (float(point) - half), 100 * (float(point) + half)],
        hoeffding_95_pp=[100 * (float(point) - radius), 100 * (float(point) + radius)],
        hoeffding_radius_pp=100 * radius,
        distinct_family_values=distinct, degenerate=distinct == 1 or lower == upper,
        families=n, _sums=sums, _scale=scale)


def bootstrap_p_values(summary):
    sums, scale, R = summary["_sums"], summary["_scale"], len(summary["_sums"])
    below_margin = sum(1 for s in sums if Fraction(s, scale) <= -2 * PP)
    at_or_below = sum(1 for s in sums if s <= 0)
    at_or_above = sum(1 for s in sums if s >= 0)
    return dict(one_sided_vs_minus2pp=Fraction(below_margin, R),
                two_sided_vs_0=min(Fraction(1), Fraction(2 * min(at_or_below, at_or_above), R)))


def holm(p_values, alpha=ALPHA):
    """Holm step-down at alpha; returns {name: (adjusted p, rejected)}."""
    names = sorted(p_values, key=lambda k: (p_values[k], k))
    m, out, running, stopped = len(names), {}, Fraction(0), False
    for rank, name in enumerate(names):
        running = max(running, min(Fraction(1), (m - rank) * p_values[name]))
        reject = not stopped and p_values[name] <= alpha / (m - rank)
        stopped = stopped or not reject
        out[name] = (running, reject)
    return out


# ------------------------------------------------------------------ labels (section 8)

USEFUL, SUPPORT, NULL, HARM, INCONCLUSIVE = ("Useful support", "Support", "Informative null", "Harm", "Inconclusive")


def decision_label(lower, upper, ceiling=False):
    """Section 8 label from the unrounded strict bootstrap bounds (proportions, not pp)."""
    L, U = lower / PP, upper / PP  # exact pp
    if L > 5:
        label = USEFUL
    elif 0 < L <= 5:
        label = SUPPORT
    elif U < 0:
        label = HARM
    elif L <= 0 and U >= 5:
        label = INCONCLUSIVE
    else:
        require(L <= 0 <= U < 5, "label rules not exhaustive")  # unreachable
        label = NULL
    return label + (" (ceiling-limited)" if ceiling else "")


def retention_label(lower, upper, primary_label):
    """Section 8 English-retention label (margin −2 pp, never widened).

    Precedence (the rules overlap): 'retained' (L > −2) first; then 'retention trade-off'
    (Δ_C Support/Useful support and U < −2), which would otherwise be unreachable because
    U < −2 implies the 'degraded' condition U < 0; then 'degraded'; else 'not established'."""
    L, U = lower / PP, upper / PP
    if L > -2:
        return "retained"
    if primary_label.split(" (")[0] in (SUPPORT, USEFUL) and U < -2:
        return "retention trade-off"
    if U < 0:
        return "degraded"
    return "retention not established"


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

def analyze(study, ceiling_flag, holm_requested=False):
    require(ceiling_flag in ("fired", "not_fired"), "ceiling flag must be 'fired' or 'not_fired'")
    ceiling = ceiling_flag == "fired"
    runs, seeds = study["runs"], study["seeds"]
    family_ids = [f["family_id"] for f in study["families"]]
    N, S = len(family_ids), len(seeds)
    result = dict(
        analysis_version=ANALYSIS_VERSION, preregistration="phase2/PREREGISTRATION.md sections 6-8",
        dataset_role=study["role"], dataset_sha256=study["dataset_sha256"], families=N, seeds=seeds,
        model_id=study["model_id"], ceiling_flag=ceiling_flag, holm_requested=holm_requested,
        warnings=list(study["warnings"]),
        code_sha256={"phase2_analysis/analyze.py": sha256(Path(__file__).read_bytes()),
                     "secondary_analysis/numeric_endpoint.py": sha256(Path(numeric_v1.__file__).read_bytes()),
                     "secondary_analysis/numeric_literal_v2.py": sha256(Path(numeric_v2.__file__).read_bytes())},
        bootstrap=dict(seed=BOOTSTRAP_SEED, resamples=RESAMPLES, generator="random.Random(101).randrange(N), N per resample",
                       shared_index_sequence=True, interval="95% percentile, linear interpolation",
                       note="Approximate interval conditional on the trained checkpoints; does not cover training-seed variance."),
        inputs=[dict(checkpoint=checkpoint_name(k), path=r["path"], kind=r["kind"], run_id=r["manifest"]["run_id"],
                     archive_sha256=r["archive_sha256"], manifest_dataset_sha256=r["manifest"]["dataset_sha256"],
                     config_sha256=r["manifest"]["config_sha256"], model_revision=r["config"].get("model_revision"),
                     status="COMPLETE" if r["complete"] else "INCOMPLETE", completed=r["completed"],
                     expected=r["expected"], attempts=r["attempts"]) for k, r in sorted(runs.items(), key=_order)])
    require(sha256(Path(numeric_v1.__file__).read_bytes()) == NUMERIC_V1_SHA256,
            "numeric_literal_v1 source differs from the pre-registered SHA-256")
    if not all(r["complete"] for r in runs.values()):
        result["status"] = "INCOMPLETE"
        result["note"] = ("At least one checkpoint run is incomplete: headline numbers are suppressed and the primary "
                          "analysis is reported as incomplete (section 10). No complete-case removal.")
        return result
    result["status"] = "COMPLETE"
    y = outcomes(study)
    indices = bootstrap_indices(N)
    by_family = {f["family_id"]: f for f in study["families"]}
    result["endpoints"] = {}
    for endpoint in ENDPOINTS:
        yy = y[endpoint]
        nums = family_numerators(yy, family_ids, seeds)
        estimands = {}
        for name, form, first, second, text in DIFFERENCES + ((S3[0], "", "", "", S3[1]),):
            width = 4 if name == "S3" else 2
            estimands[name] = dict(interval_summary(nums[name], S, indices, width), description=text)
        block = dict(estimands=estimands)
        # Per seed (section 7): own paired bootstrap (same settings, same index sequence) + exact McNemar.
        per_seed = {}
        for name in PER_SEED:
            _, form, first, second, text = next(d for d in DIFFERENCES if d[0] == name)
            rows = {}
            for s in seeds:
                a = [yy[(first, s)][fid][form] for fid in family_ids]
                b = [yy[(second, s)][fid][form] for fid in family_ids]
                summary = interval_summary([x - z for x, z in zip(a, b)], 1, indices, 2)
                first_only = sum(1 for x, z in zip(a, b) if x and not z)
                second_only = sum(1 for x, z in zip(a, b) if z and not x)
                p = mcnemar_exact(first_only, second_only)
                rows[str(s)] = dict(summary, first_only=first_only, second_only=second_only,
                                    mcnemar_exact_p=float(p), mcnemar_exact_p_exact=str(p))
            points = [rows[str(s)]["estimate"] for s in seeds]
            per_seed[name] = dict(description=text, seeds=rows, range_pp=[_pp(min(points)), _pp(max(points))],
                                  signs=dict(positive=sum(p > 0 for p in points), zero=sum(p == 0 for p in points),
                                             negative=sum(p < 0 for p in points)),
                                  note="Sign consistency is described, never used as a test.")
        block["per_seed"] = per_seed
        # Absolute accuracy per checkpoint, Wilson 95%.
        accuracy = {}
        for key in sorted(runs, key=_order):
            accuracy[checkpoint_name(key)] = {}
            for form in FORMS:
                k = sum(yy[key][fid][form] for fid in family_ids)
                accuracy[checkpoint_name(key)][form] = dict(correct=k, n=N, accuracy=k / N, wilson_95=wilson(k, N))
        block["accuracy"] = accuracy
        block["arm_mean_accuracy"] = {arm: {form: sum(yy[(arm, s)][fid][form] for s in seeds for fid in family_ids) / (N * S)
                                            for form in FORMS} for arm in ARMS}
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
        if endpoint == "strict":
            primary = estimands["delta_C"]
            label = decision_label(primary["lower"], primary["upper"], ceiling)
            block["decision_label"] = label
            block["decision_bounds_exact"] = dict(L=str(primary["lower"]), U=str(primary["upper"]))
            block["retention_labels"] = {name: retention_label(estimands[name]["lower"], estimands[name]["upper"], label)
                                         for name in RETENTION}
            block["holm"] = None
            if holm_requested:
                ps = {"ret_E_EC_EE": bootstrap_p_values(estimands["ret_E_EC_EE"])["one_sided_vs_minus2pp"],
                      "T_R": bootstrap_p_values(estimands["T_R"])["two_sided_vs_0"],
                      "S3": bootstrap_p_values(estimands["S3"])["two_sided_vs_0"]}
                block["holm"] = {name: dict(p=float(ps[name]), p_exact=str(ps[name]), holm_adjusted_p=float(adj),
                                            rejected_at_05=rej) for name, (adj, rej) in holm(ps).items()}
        else:
            block["decision_label"] = None
            block["note"] = "Secondary endpoint: same analysis; decision labels use strict only."
        result["endpoints"][endpoint] = block
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


def markdown(result):
    role = result["dataset_role"]
    lines = [f"# Phase-2 pre-registered analysis — {role}", ""]
    if role == "DEV":
        lines += ["**DEV RUNS — software and sanity check only. Nothing here is a Phase-2 result; labels on DEV are "
                  "printed only to exercise the code (sections 5 and 11).**", ""]
    lines += [f"Analysis `{result['analysis_version']}`; plan `{result['preregistration']}`.",
              f"Dataset SHA-256 `{result['dataset_sha256']}` ({role}); {result['families']} families; seeds "
              f"{', '.join(map(str, result['seeds']))}; base `{result['model_id']}`.",
              f"Status: **{result['status']}**. Ceiling flag: **{result['ceiling_flag']}**.", ""]
    lines += [f"- Warning: {w}" for w in result["warnings"]]
    lines += ["", "## Inputs", "", "| Checkpoint | Run ID | Status | Completed | Attempts | Source |", "|---|---|---|---:|---:|---|"]
    for i in result["inputs"]:
        lines.append(f"| {i['checkpoint']} | `{i['run_id']}` | {i['status']} | {i['completed']}/{i['expected']} | "
                     f"{i['attempts']} | {i['kind']} |")
    if result["status"] != "COMPLETE":
        lines += ["", result["note"], ""]
        return "\n".join(lines) + "\n"
    strict = result["endpoints"]["strict"]
    est = strict["estimands"]
    primary = est["delta_C"]
    precision = (f"Precision: the 95% paired family bootstrap interval for Δ_C has half-width "
                 f"{(primary['bootstrap_95_pp'][1] - primary['bootstrap_95_pp'][0]) / 2:.2f} pp.")
    label_lines = ["## Primary: Δ_C (strict, E+C − E+R on C)", "",
                   f"- Δ_C = {_interval(primary)} (95% paired family bootstrap, {RESAMPLES:,} resamples, seed {BOOTSTRAP_SEED}).",
                   f"- **Decision label: {strict['decision_label']}** (from unrounded bounds L = {primary['exact']['lower']}, "
                   f"U = {primary['exact']['upper']} as proportions).",
                   f"- Wald 95%: [{_f(primary['wald_95_pp'][0], 2)}, {_f(primary['wald_95_pp'][1], 2)}] pp; Hoeffding 95%: "
                   f"[{_f(primary['hoeffding_95_pp'][0], 2)}, {_f(primary['hoeffding_95_pp'][1], 2)}] pp "
                   f"(radius {primary['hoeffding_radius_pp']:.1f} pp); distinct d_i values: {primary['distinct_family_values']}; "
                   f"degenerate: {primary['degenerate']}.", ""]
    s2_lines = ["## S2: R transfer (descriptive)", "",
                f"- T_R (E+R − E+E on R) = {_interval(est['T_R'])}",
                f"- Δ_R (E+C − E+R on R) = {_interval(est['delta_R'])}", ""]
    if result["ceiling_flag"] == "fired":
        lines += ["", "## Ceiling-limited", "", "The unchanged-model DEV ceiling flag fired (section 5): Δ_C is "
                  "pre-declared ceiling-limited.", "", precision, ""] + s2_lines + label_lines
    else:
        lines += [""] + label_lines + [precision, ""] + s2_lines
    lines += ["## S1: English retention (descriptive; margin −2 pp)", "",
              "| Estimand | Estimate [95% bootstrap] | Retention label |", "|---|---|---|"]
    for name in RETENTION:
        lines.append(f"| {est[name]['description']} | {_interval(est[name])} | {strict['retention_labels'][name]} |")
    lines += ["", "## S3: specificity (descriptive)", "", f"- Δ_C − Δ_R per family = {_interval(est['S3'])} "
              f"(Hoeffding radius {est['S3']['hoeffding_radius_pp']:.1f} pp for values in [−2, 2])", ""]
    if strict["holm"] is not None:
        lines += ["## Holm (requested)", "", "| Secondary | Bootstrap p | Holm-adjusted p | Rejected at .05 |", "|---|---:|---:|---|"]
        for name, h in strict["holm"].items():
            lines.append(f"| {name} | {h['p']:.4f} | {h['holm_adjusted_p']:.4f} | {h['rejected_at_05']} |")
        lines.append("")
    else:
        lines += ["Holm correction not requested: secondaries are descriptive with unadjusted 95% intervals.", ""]
    lines += ["## All estimands, all endpoints", "",
              "| Estimand | strict | numeric_literal_v1 | numeric_literal_v2 |", "|---|---|---|---|"]
    for name in ESTIMAND_ORDER:
        cells = [_interval(result["endpoints"][e]["estimands"][name]) for e in ENDPOINTS]
        lines.append(f"| {est[name]['description']} | " + " | ".join(cells) + " |")
    lines += ["", "Decision and retention labels use strict only.", "", "## Per seed (strict)", "",
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
    lines += ["", "Crossed family × seed resampling (optional labelled sensitivity analysis, section 7) is not run.", ""]
    for endpoint in ENDPOINTS:
        block = result["endpoints"][endpoint]
        lines += [f"## Accuracy by checkpoint — {endpoint} (Wilson 95%)", "", "| Checkpoint | E | R | C |", "|---|---|---|---|"]
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


def run_analysis(dataset, checkpoints, ceiling_flag, out, holm_requested=False):
    out = Path(out)
    require(not out.exists() or not any(out.iterdir()), f"Output directory {out} must be new or empty")
    study = assemble(dataset, checkpoints)
    result = analyze(study, ceiling_flag, holm_requested)
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase2_analysis.json").write_text(to_json(result), encoding="utf-8")
    (out / "phase2_analysis.md").write_text(markdown(result), encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dataset", required=True, help="frozen FINAL_TEST or DEV JSON file the runs were made from")
    parser.add_argument("--unchanged", required=True, help="unchanged-model run directory or results ZIP")
    parser.add_argument("--run", action="append", default=[], help="ARM:SEED=PATH for each adapter run (ARM in EE/ER/EC)")
    parser.add_argument("--ceiling-flag", required=True, choices=("fired", "not_fired"),
                        help="section 5 outcome of the unchanged-model DEV check (C strict >= 38/40)")
    parser.add_argument("--holm", action="store_true", help="apply Holm to {S1, S2, S3} (only if claimed inferentially)")
    parser.add_argument("--out", required=True, help="new output directory")
    args = parser.parse_args(argv)
    try:
        result = run_analysis(args.dataset, parse_checkpoints(args.unchanged, args.run), args.ceiling_flag,
                              args.out, args.holm)
    except (AnalysisError, ValueError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    print(f"{result['dataset_role']} {result['status']}" + (
        f": {result['endpoints']['strict']['decision_label']}" if result["status"] == "COMPLETE" else ""))
    return 0 if result["status"] == "COMPLETE" else 3


if __name__ == "__main__":
    sys.exit(main())
