"""Turn Test 1 results ZIPs into paper-ready Markdown/LaTeX tables, a CSV and figures.

Reports stored scores only: strict correctness is the stored ``correct`` of the
sole terminal generated attempt; nothing is rescored. Aggregates use the same
formulas as test1_pilot/hinglish_pilot/report.py (Wilson interval, family
bootstrap in report.py's RNG order) and are cross-checked against the
metrics.json stored in each ZIP.

Usage (from the repository root):
    python3 -B -m paper_analysis.build_tables RUN_results.zip [...] --out NEW_DIR
    python3 -B -m paper_analysis.build_tables FMT2_format_test_results.zip --out NEW_DIR
"""

import argparse
import csv
import hashlib
import importlib
import io
import json
import math
import random
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "paper_analysis"

from . import __version__  # noqa: E402
from .safezip import ExpansionBudget, UnsafeArchive, read_zip, verify_checksums  # noqa: E402

FORMS = ("E", "R", "C")
# report.py consumes one RNG in this order; the order is fixed so intervals match exactly.
REPORT_PAIR_ORDER = (("E", "C"), ("E", "R"), ("R", "C"))
DISPLAY_PAIR_ORDER = (("E", "R"), ("E", "C"), ("R", "C"))
PREDICTION_FIELDS = ("rendering_id", "attempt_id", "correct")
# Files written at the output root; run folders must never take these names.
TOP_LEVEL_OUTPUTS = ("README.md", "per_rendering.csv")
REQUIRED = ("run_manifest.json", "experiment_config.json", "dataset.json", "generation_attempts.jsonl")
REPO_ROOT = Path(__file__).resolve().parents[1]
STORED_SCORE_NOTE = ("Stored scores only: strict correctness is the stored automatic `correct` "
                     "(scorer v1.0.0); this tool adds no new scoring.")
CSV_FIELDS = ["source", "run_slug", "run_id", "label", "mode", "run_status", "family_id", "topic", "form",
              "rendering_id", "selected_attempt_id", "attempts", "status", "correct", "invalid_reason",
              "refusal", "truncated", "extracted_final", "normalized_value", "normalized_unit",
              "input_tokens", "output_tokens", "latency_seconds", "numeric_endpoint", "numeric_status",
              "numeric_correct", "numeric_value", "numeric_suffix", "numeric_unvalidated_suffix"]


class AnalysisError(ValueError):
    """The run content is inconsistent or cannot be reported."""


def _require(condition, message):
    if not condition:
        raise AnalysisError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _no_constants(token):
    raise AnalysisError(f"Non-finite JSON constant {token} rejected")


def _json(blob, name):
    try:
        return json.loads(blob.decode("utf-8"), parse_constant=_no_constants)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AnalysisError(f"{name}: invalid JSON ({type(error).__name__})") from None


# ---------------------------------------------------------------- statistics (copied from report.py)

def wilson(k, n):
    z = 1.959963984540054
    p = k/n
    center = (p + z*z/(2*n))/(1+z*z/n)
    radius = z * math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [max(0, center-radius), min(1, center+radius)]


def quantile(xs, p):
    position = (len(xs)-1)*p
    low = math.floor(position)
    high = math.ceil(position)
    return xs[low] + (xs[high]-xs[low])*(position-low)


def paired(values, a, b, rng, resamples):
    diffs = [int(f[a])-int(f[b]) for f in values]
    n = len(diffs)
    draws = sorted(sum(diffs[rng.randrange(n)] for _ in range(n))/n for _ in range(resamples))
    return {'difference': sum(diffs)/n, 'bootstrap_95_interval': [quantile(draws, .025), quantile(draws, .975)],
            'both_correct': sum(f[a] and f[b] for f in values),
            'both_wrong': sum(not f[a] and not f[b] for f in values),
            'a_correct_b_wrong': sum(f[a] and not f[b] for f in values),
            'a_wrong_b_correct': sum(not f[a] and f[b] for f in values), 'families': n}


def _median(values):
    clean = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return statistics.median(clean) if clean else None


# ---------------------------------------------------------------- secondary endpoint (optional)

def _numeric_evaluator():
    """Return secondary_analysis.numeric_endpoint (module) if importable from the repo root."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.append(str(REPO_ROOT))
    try:
        from secondary_analysis import numeric_endpoint
    except ImportError:
        return None
    return numeric_endpoint


# ---------------------------------------------------------------- loading

def _expand_inputs(paths):
    """Yield (source_label, members) for each results ZIP, expanding outer ZIPs one level."""
    runs, notes = [], []
    # One budget for every archive expanded here: all expanded runs are retained in memory together.
    budget = ExpansionBudget()
    for path in paths:
        path = Path(path)
        _require(path.is_file(), f"Input ZIP not found: {path}")
        members = read_zip(path.read_bytes(), path.name, budget)
        if "run_manifest.json" in members:
            runs.append((path.name, members))
            continue
        inner = sorted(name for name in members if name.endswith("_results.zip"))
        _require(inner, f"{path.name}: neither a results ZIP nor an outer ZIP of *_results.zip files")
        ignored = sorted(set(members) - set(inner))
        if ignored:
            notes.append(f"{path.name}: {len(ignored)} non-results member(s) ignored (not checksummed by the outer ZIP).")
        for name in inner:
            label = f"{path.name}!{name}"
            runs.append((label, read_zip(members[name], label, budget)))
    return runs, notes


def _select(manifest, journal):
    """Mirror engine.selected(): the sole terminal generated attempt per rendering."""
    grouped = {}
    ids = set()
    for item in journal:
        _require(isinstance(item, dict), "Malformed attempt record")
        _require(item.get("record_sha256") == _digest({k: v for k, v in item.items() if k != "record_sha256"}),
                 "Attempt record checksum (record_sha256) mismatch")
        _require(item.get("run_id") == manifest["run_id"] and item.get("config_sha256") == manifest["config_sha256"],
                 "Foreign journal record")
        _require(item.get("attempt_id") not in ids, "Duplicate attempt ID")
        ids.add(item.get("attempt_id"))
        grouped.setdefault(item["rendering_id"], []).append(item)
    _require(set(grouped) <= set(manifest["evaluation_order"]), "Unexpected rendering in journal")
    selected, history_count = {}, {}
    for rid in manifest["evaluation_order"]:
        history = sorted(grouped.get(rid, []), key=lambda x: x["attempt_number"])
        _require([x["attempt_number"] for x in history] == list(range(1, len(history) + 1)), "Attempt sequence corrupt")
        successful = [x for x in history if x["status"] == "generated"]
        _require(len(successful) <= 1, "Multiple scored attempts forbidden")
        _require(not successful or successful[0] is history[-1], "Cannot retry a generated response")
        history_count[rid] = len(history)
        if successful:
            row = successful[0]
            _require(type(row.get("correct")) is bool, f"Stored correct is not boolean for {rid}")
            _require(row.get("invalid_reason") is None or isinstance(row["invalid_reason"], str),
                     f"Malformed stored invalid_reason for {rid}")
            _require(isinstance(row.get("raw_response"), str), f"Missing raw response for {rid}")
            selected[rid] = row
    return selected, history_count


def load_run(source, members):
    """Validate one verified results ZIP; return a dict describing the run (no scoring)."""
    checksums = verify_checksums(members, source)
    for name in REQUIRED:
        _require(name in members, f"{source}: missing {name}")
    manifest = _json(members["run_manifest.json"], "run_manifest.json")
    config = _json(members["experiment_config.json"], "experiment_config.json")
    dataset = _json(members["dataset.json"], "dataset.json")
    try:
        lines = members["generation_attempts.jsonl"].decode("utf-8").splitlines()
    except UnicodeDecodeError:
        raise AnalysisError(f"{source}: generation_attempts.jsonl is not UTF-8") from None
    try:
        journal = [json.loads(line, parse_constant=_no_constants) for line in lines if line.strip()]
    except json.JSONDecodeError:
        raise AnalysisError(f"{source}: generation_attempts.jsonl is not valid JSON lines") from None
    _require(_digest(config) == manifest.get("config_sha256"), f"{source}: config snapshot does not match manifest")
    _require(_digest(dataset) == manifest.get("dataset_sha256"), f"{source}: dataset snapshot does not match manifest")
    if "split_manifest.json" in members:
        _require(_digest(_json(members["split_manifest.json"], "split_manifest.json")) == manifest.get("split_sha256"),
                 f"{source}: split snapshot does not match manifest")
    _require(manifest.get("scorer_version") == "1.0.0", f"{source}: expected stored scorer v1.0.0")
    families = dataset.get("families")
    _require(isinstance(families, list) and families, f"{source}: dataset has no families")
    renderings = {}
    for family in families:
        _require(set(family["forms"]) == set(FORMS), f"{source}: family without exactly E/R/C")
        for form in FORMS:
            rid = family["forms"][form]["rendering_id"]
            _require(rid not in renderings, f"{source}: duplicate rendering {rid}")
            renderings[rid] = (family, form)
    order = manifest.get("evaluation_order")
    _require(isinstance(order, list) and len(order) == len(set(order)) and set(order) == set(renderings),
             f"{source}: evaluation order does not match dataset")
    _require(manifest.get("expected") == len(renderings), f"{source}: expected count does not match dataset")
    try:
        selected, history_count = _select(manifest, journal)
    except AnalysisError as error:
        raise AnalysisError(f"{source}: {error}") from None
    except (KeyError, TypeError) as error:
        raise AnalysisError(f"{source}: malformed attempt record ({type(error).__name__}: {error})") from None
    for rid, row in selected.items():
        family, form = renderings[rid]
        _require(row.get("family_id") == family["family_id"] and row.get("form") == form,
                 f"{source}: attempt/dataset identity mismatch for {rid}")
        if "gold" in row:
            _require(row["gold"] == family["gold"], f"{source}: attempt/dataset gold mismatch for {rid}")
    _require(len(selected) == manifest.get("completed", 0),
             f"{source}: manifest/journal completion mismatch")
    complete = len(selected) == manifest["expected"]
    _require(complete == (manifest.get("status") == "COMPLETE"), f"{source}: manifest status contradicts journal")
    metrics = _json(members["metrics.json"], "metrics.json") if "metrics.json" in members else None
    predictions = None
    if "predictions.csv" in members:
        csv.field_size_limit(64 * 1024 * 1024)
        try:
            reader = csv.DictReader(io.StringIO(members["predictions.csv"].decode("utf-8"), newline=""))
            header = reader.fieldnames or []
            predictions = list(reader)
        except (UnicodeDecodeError, csv.Error) as error:
            raise AnalysisError(f"{source}: predictions.csv is unreadable ({type(error).__name__})") from None
        missing = [field for field in PREDICTION_FIELDS if field not in header]
        _require(not missing, f"{source}: predictions.csv lacks required column(s) {missing}")
    return dict(source=source, manifest=manifest, config=config, dataset=dataset, selected=selected,
                history_count=history_count, complete=complete, metrics=metrics, predictions=predictions,
                checksums=checksums, renderings=renderings)


# ---------------------------------------------------------------- computation

def compute(run, numeric_module):
    """Aggregate stored scores. Headline results only when the run is complete."""
    manifest, dataset, config, selected = run["manifest"], run["dataset"], run["config"], run["selected"]
    rows = []
    for family in dataset["families"]:
        for form in FORMS:
            rid = family["forms"][form]["rendering_id"]
            attempt = selected.get(rid)
            row = dict(family_id=family["family_id"], topic=family.get("topic"), form=form, rendering_id=rid,
                       attempts=run["history_count"].get(rid, 0), attempt=attempt, numeric=None)
            if attempt is not None and numeric_module is not None:
                row["numeric"] = numeric_module.evaluate_numeric(attempt["raw_response"], family["gold"],
                                                                 bool(attempt.get("truncated", False)))
            rows.append(row)
    done = [r for r in rows if r["attempt"] is not None]
    result = dict(run_id=manifest["run_id"], label=manifest.get("label"), mode=manifest.get("mode"),
                  status="COMPLETE" if run["complete"] else "INCOMPLETE", expected=manifest["expected"],
                  completed=len(done), families=len(dataset["families"]),
                  bootstrap_seed=config["bootstrap_seed"], bootstrap_resamples=config["bootstrap_resamples"],
                  accuracy=None, paired=None, numeric=None, rows=rows)
    reasons = sorted({r["attempt"]["invalid_reason"] for r in done if r["attempt"]["invalid_reason"]})
    result["invalid_reasons"] = {reason: {form: sum(r["form"] == form and r["attempt"]["invalid_reason"] == reason
                                                    for r in done) for form in FORMS} for reason in reasons}
    result["completed_by_form"] = {form: sum(r["form"] == form for r in done) for form in FORMS}
    result["resources"] = {form: {field: _median([r["attempt"].get(field) for r in done if r["form"] == form])
                                  for field in ("input_tokens", "output_tokens", "latency_seconds")} for form in FORMS}
    result["token_count_kinds"] = sorted({str(r["attempt"].get("token_count_kind")) for r in done
                                          if r["attempt"].get("token_count_kind")})
    if not run["complete"]:
        return result
    by_family = {f["family_id"]: {"family_id": f["family_id"]} for f in dataset["families"]}
    for r in done:
        by_family[r["family_id"]][r["form"]] = bool(r["attempt"]["correct"])
    family_rows = list(by_family.values())
    n = len(family_rows)
    result["family_rows"] = family_rows
    result["accuracy"] = {form: {"correct": sum(f[form] for f in family_rows), "denominator": n,
                                 "accuracy": sum(f[form] for f in family_rows)/n,
                                 "wilson_95_interval": wilson(sum(f[form] for f in family_rows), n)} for form in FORMS}
    rng = random.Random(config["bootstrap_seed"])
    result["paired"] = {a+"-"+b: paired(family_rows, a, b, rng, config["bootstrap_resamples"])
                        for a, b in REPORT_PAIR_ORDER}
    if numeric_module is not None:
        result["numeric"] = {form: {"denominator": sum(r["form"] == form for r in done),
                                    "strict_correct": sum(r["form"] == form and r["attempt"]["correct"] for r in done),
                                    "numeric_correct": sum(r["form"] == form and r["numeric"]["correct"] for r in done),
                                    "disagreements": sum(r["form"] == form and r["numeric"]["correct"] != r["attempt"]["correct"]
                                                         for r in done)}
                             for form in FORMS}
        result["numeric_endpoint"] = getattr(numeric_module, "ENDPOINT_VERSION", "numeric_literal_v1")
    return result


def consistency(run, result):
    """Compare recomputed aggregates and per-rendering scores with what report.py stored."""
    checks = []
    predictions = run["predictions"]
    if predictions is None:
        checks.append(("predictions.csv correct/attempt_id", "not available"))
    else:
        stored = {p["rendering_id"]: p for p in predictions}
        ok = len(stored) == len(predictions) == len(run["selected"]) and all(
            rid in stored and stored[rid]["attempt_id"] == row["attempt_id"] and stored[rid]["correct"] == str(row["correct"])
            for rid, row in run["selected"].items())
        checks.append(("predictions.csv correct/attempt_id", "match" if ok else "MISMATCH"))
    metrics = run["metrics"]
    if metrics is None:
        checks.append(("metrics.json", "not available"))
        return checks
    checks.append(("metrics.json status", "match" if metrics.get("status") == result["status"] else "MISMATCH"))
    if result["accuracy"] is not None:
        checks.append(("metrics.json accuracy + Wilson", "match" if metrics.get("accuracy") == result["accuracy"] else "MISMATCH"))
        checks.append(("metrics.json paired bootstrap", "match" if metrics.get("paired") == result["paired"] else "MISMATCH"))
    return checks


# ---------------------------------------------------------------- rendering

class Cell:
    """A cell with distinct Markdown and LaTeX text (LaTeX already escaped)."""

    def __init__(self, md, tex):
        self.md, self.tex = md, tex


_TEX = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "—": "---", "–": "--", "−": "$-$", "`": ""}


def tex_escape(text):
    return "".join(_TEX.get(ch, ch) for ch in str(text))


def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def num(text):
    """Numeric cell: Unicode minus in Markdown, math minus in LaTeX."""
    text = str(text)
    return Cell(text.replace("-", "−"), tex_escape(text).replace("-", "$-$"))


def form_diff(a, b):
    return Cell(f"{a}−{b}", f"{a}$-${b}")


def pct(x):
    return f"{100*x:.1f}"


def pp(x):
    return f"{100*x:+.1f}" if x else "0.0"


class Table:
    def __init__(self, key, caption, headers, aligns, rows, notes=()):
        self.key, self.caption, self.headers, self.aligns, self.rows, self.notes = key, caption, headers, aligns, rows, list(notes)

    def markdown(self):
        def cell(value):
            return value.md if isinstance(value, Cell) else md_escape(value)
        sep = ["---:" if a == "r" else ("---" if a == "l" else ":---:") for a in self.aligns]
        lines = [f"**{md_escape(self.caption)}**", "",
                 "| " + " | ".join(cell(h) for h in self.headers) + " |", "| " + " | ".join(sep) + " |"]
        lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in self.rows]
        lines += [""] + [f"_{md_escape(note)}_" for note in self.notes]
        return "\n".join(lines).rstrip() + "\n"

    def latex(self, label_prefix):
        def cell(value):
            return value.tex if isinstance(value, Cell) else tex_escape(value)
        lines = [r"\begin{table}[t]", r"\centering", r"\small",
                 rf"\caption{{{tex_escape(self.caption)}}}", rf"\label{{tab:{label_prefix}-{self.key}}}",
                 rf"\begin{{tabular}}{{{''.join(self.aligns)}}}", r"\toprule",
                 " & ".join(cell(h) for h in self.headers) + r" \\", r"\midrule"]
        lines += [" & ".join(cell(v) for v in row) + r" \\" for row in self.rows]
        lines += [r"\bottomrule", r"\end{tabular}"]
        if self.notes:
            lines += [r"\par\smallskip", r"\parbox{\linewidth}{\footnotesize " +
                      " ".join(tex_escape(n) for n in self.notes) + "}"]
        lines += [r"\end{table}"]
        return "\n".join(lines) + "\n"


def build_tables(result):
    label = result["label"] or "unlabelled run"
    n = result["families"]
    tables = []
    if result["accuracy"] is not None:
        rows = []
        for form in FORMS:
            a = result["accuracy"][form]
            lo, hi = a["wilson_95_interval"]
            rows.append([form, f"{a['correct']}/{a['denominator']}", num(pct(a["accuracy"])), num(f"[{pct(lo)}, {pct(hi)}]")])
        tables.append(Table("accuracy", f"Strict accuracy by form ({label}; {n} families)",
                            ["Form", "Correct / families", "Accuracy (%)", "Wilson 95% CI (%)"], "lrrr", rows,
                            [STORED_SCORE_NOTE, "One rendering per form per family; families are the unit of analysis."]))
        rows = []
        for a, b in DISPLAY_PAIR_ORDER:
            p = result["paired"][f"{a}-{b}"]
            lo, hi = p["bootstrap_95_interval"]
            rows.append([form_diff(a, b), num(pp(p["difference"])), num(f"[{pp(lo)}, {pp(hi)}]"),
                         p["a_correct_b_wrong"], p["a_wrong_b_correct"], p["both_correct"], p["both_wrong"]])
        tables.append(Table("paired", f"Paired family differences in strict accuracy ({label}; {n} families)",
                            ["Contrast", "Difference (pp)", "Bootstrap 95% interval (pp)", "Only first correct",
                             "Only second correct", "Both correct", "Both wrong"], "lrrrrrr", rows,
                            [f"Descriptive paired family bootstrap: {result['bootstrap_resamples']:,} resamples, seed "
                             f"{result['bootstrap_seed']}, identical to report.py. Discordant counts are families. "
                             "No significance claim.", STORED_SCORE_NOTE]))
    completed = result["completed_by_form"]
    rows = [[reason] + [counts[f] for f in FORMS] + [sum(counts.values())]
            for reason, counts in result["invalid_reasons"].items()]
    invalid = {f: sum(c[f] for c in result["invalid_reasons"].values()) for f in FORMS}
    rows.append([Cell("**All invalid**", r"\textbf{All invalid}")] + [invalid[f] for f in FORMS] + [sum(invalid.values())])
    rows.append(["Completed renderings"] + [completed[f] for f in FORMS] + [sum(completed.values())])
    tables.append(Table("invalid", f"Stored invalid reasons by form ({label})", ["Invalid reason", *FORMS, "Total"],
                        "lrrrr", rows, ["Counts of stored scorer v1.0.0 invalid_reason over completed renderings.",
                                        STORED_SCORE_NOTE]))
    res = result["resources"]

    def med(value, digits):
        return "n/a" if value is None else (f"{value:.{digits}f}" if digits else f"{value:g}")
    rows = [[form, completed[form], med(res[form]["input_tokens"], 0), med(res[form]["output_tokens"], 0),
             med(res[form]["latency_seconds"], 2)] for form in FORMS]
    kinds = ", ".join(result["token_count_kinds"]) or "not recorded"
    tables.append(Table("resources", f"Median tokens and generation latency by form ({label})",
                        ["Form", "Completed", "Median input tokens", "Median output tokens", "Median latency (s)"],
                        "lrrrr", rows, [f"Token count kind: {kinds}. Latency excludes model load and tokenization."]))
    if result["numeric"] is not None:
        rows = []
        for form in FORMS:
            s = result["numeric"][form]
            d = s["denominator"]
            rows.append([form, f"{s['strict_correct']}/{d}", num(pct(s["strict_correct"]/d)),
                         f"{s['numeric_correct']}/{d}", num(pct(s["numeric_correct"]/d)), s["disagreements"]])
        tables.append(Table("numeric", f"Strict endpoint beside secondary {result['numeric_endpoint']} ({label})",
                            ["Form", "Strict correct", "Strict (%)", "Numeric match", "Numeric (%)", "Disagreements"],
                            "lrrrrr", rows,
                            ["numeric_literal_v1 is the pre-registered secondary endpoint (D018): exact FINAL-line literal, "
                             "no unit conversion. Strict scorer v1.0.0 remains primary."]))
    return tables


def csv_rows(run, result, slug):
    out = []
    for r in result["rows"]:
        a, nm = r["attempt"] or {}, r["numeric"] or {}
        row = dict(source=run["source"], run_slug=slug, run_id=result["run_id"], label=result["label"],
                   mode=result["mode"], run_status=result["status"], family_id=r["family_id"], topic=r["topic"],
                   form=r["form"], rendering_id=r["rendering_id"], selected_attempt_id=a.get("attempt_id"),
                   attempts=r["attempts"], status="generated" if a else "unresolved", correct=a.get("correct"),
                   invalid_reason=a.get("invalid_reason"), refusal=a.get("refusal"), truncated=a.get("truncated"),
                   extracted_final=a.get("extracted_final"), normalized_value=a.get("normalized_value"),
                   normalized_unit=a.get("normalized_unit"), input_tokens=a.get("input_tokens"),
                   output_tokens=a.get("output_tokens"), latency_seconds=a.get("latency_seconds"),
                   numeric_endpoint=nm.get("endpoint"), numeric_status=nm.get("status"),
                   numeric_correct=nm.get("correct"), numeric_value=nm.get("value"), numeric_suffix=nm.get("suffix"),
                   numeric_unvalidated_suffix=nm.get("unvalidated_suffix"))
        # Spreadsheet formula protection, as in the pilot exporter.
        out.append({k: ("'" + v if isinstance(v, str) and v and v[0] in "=+-@" else v) for k, v in row.items()})
    return out


def _slug(source, used):
    """Allocate a run folder name unique among runs and top-level outputs.

    Comparison is case-insensitive, since output directories may be on a case-insensitive filesystem.
    """
    base = source.split("!")[-1].rsplit("/", 1)[-1]
    base = re.sub(r"(_results)?\.zip$", "", base)
    base = re.sub(r"[^A-Za-z0-9_.-]+", "-", base).strip(".-") or "run"
    reserved = {name.casefold() for name in TOP_LEVEL_OUTPUTS}
    slug, index = base, 2
    while slug.casefold() in used or slug.casefold() in reserved:
        slug, index = f"{base}-{index}", index + 1
    used.add(slug.casefold())
    return slug


def _json_ready(result):
    return {k: v for k, v in result.items() if k not in ("rows",)}


def build(paths, out, figures=True):
    """Validate all inputs fully, then write outputs into the new directory ``out``."""
    out = Path(out)
    _require(not out.exists() or (out.is_dir() and not any(out.iterdir())),
             f"Refusing to write into existing non-empty path: {out}")
    runs, notes = _expand_inputs(paths)
    numeric_module = _numeric_evaluator()
    if numeric_module is None:
        notes.append("secondary_analysis not importable: numeric_literal_v1 table skipped.")
    used, prepared = set(), []
    for source, members in runs:
        try:
            run = load_run(source, members)
            result = compute(run, numeric_module)
            checks = consistency(run, result)
        except (KeyError, TypeError, AttributeError, ValueError) as error:
            if isinstance(error, (AnalysisError, UnsafeArchive)):
                raise
            raise AnalysisError(f"{source}: malformed run content ({type(error).__name__}: {error})") from None
        prepared.append((run, result, _slug(source, used), checks))
    # All validation is finished; only now touch the filesystem.
    out.mkdir(parents=True, exist_ok=True)
    figure_note = None
    plotting = None
    if figures:
        try:
            plotting = importlib.import_module(__package__ + ".figures")
        except ImportError:
            figure_note = "matplotlib not available: figures skipped."
    elif figures is False:
        figure_note = "Figures disabled (--no-figures)."
    all_rows, index, mismatched = [], [], False
    for run, result, slug, checks in prepared:
        folder = out / slug
        (folder / "tables").mkdir(parents=True)
        tables = build_tables(result)
        for table in tables:
            (folder / "tables" / f"{table.key}.md").write_text(table.markdown(), encoding="utf-8")
            (folder / "tables" / f"{table.key}.tex").write_text(table.latex(slug), encoding="utf-8")
        (folder / "tables.tex").write_text("% Requires \\usepackage{booktabs}\n" +
                                           "\n".join(t.latex(slug) for t in tables), encoding="utf-8")
        made = []
        if plotting is not None and result["accuracy"] is not None:
            made = plotting.make_figures(result, folder / "figures")
        lines = [f"# {result['label']}", "", f"Source: `{run['source']}`  ", f"Run ID: `{result['run_id']}`  ",
                 f"Status: **{result['status']}**; {result['completed']}/{result['expected']} renderings completed; "
                 f"{result['families']} families.", "", STORED_SCORE_NOTE,
                 f"All {len(run['checksums'])} checksums.sha256 entries verified.", ""]
        if not run["complete"]:
            lines += ["**INCOMPLETE RUN: headline accuracy, paired comparisons, the numeric endpoint table and "
                      "figures are suppressed** (matching report.py). Diagnostic tables only.", ""]
        lines += ["## Consistency with stored report.py outputs", ""]
        lines += [f"- {name}: {state}" for name, state in checks] + [""]
        mismatched |= any(state == "MISMATCH" for _, state in checks)
        lines += [t.markdown() for t in tables]
        if made:
            lines += ["## Figures", ""] + [f"- `figures/{p.name}`" for p in made] + [""]
        (folder / "tables.md").write_text("\n".join(lines), encoding="utf-8")
        (folder / "summary.json").write_text(json.dumps(dict(_json_ready(result), consistency=dict(checks),
                                             source=run["source"]), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                                             encoding="utf-8")
        all_rows += csv_rows(run, result, slug)
        index.append(f"| `{slug}` | {md_escape(result['label'])} | {result['status']} | "
                     f"{result['completed']}/{result['expected']} | "
                     f"{'MISMATCH' if any(s == 'MISMATCH' for _, s in checks) else 'ok'} |")
    with (out / TOP_LEVEL_OUTPUTS[1]).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)
    if figure_note:
        notes.append(figure_note)
    inputs = [(Path(p).name, hashlib.sha256(Path(p).read_bytes()).hexdigest()) for p in paths]
    readme = [f"# Paper tables (paper_analysis {__version__})", "",
              f"Generated {datetime.now(timezone.utc).isoformat()}. {STORED_SCORE_NOTE}", "",
              "Inputs (SHA-256):", ""] + [f"- `{name}` `{digest}`" for name, digest in inputs] + [
              "", "| Run | Label | Status | Completed | Consistency |", "|---|---|---|---:|---|"] + index + [
              "", "Combined per-rendering rows: `per_rendering.csv`.", ""] + [f"- {n}" for n in notes]
    (out / TOP_LEVEL_OUTPUTS[0]).write_text("\n".join(readme) + "\n", encoding="utf-8")
    return dict(out=out, runs=[(slug, result["status"]) for _, result, slug, _ in prepared],
                mismatch=mismatched, notes=notes)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Results ZIP(s) -> paper-ready tables (stored scores only).")
    parser.add_argument("zips", nargs="+", type=Path, help="results ZIP(s) or an outer ZIP of *_results.zip files")
    parser.add_argument("--out", required=True, type=Path, help="new (or empty) output directory")
    parser.add_argument("--no-figures", action="store_true", help="skip matplotlib figures")
    args = parser.parse_args(argv)
    try:
        summary = build(args.zips, args.out, figures=not args.no_figures)
    except (AnalysisError, UnsafeArchive) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for slug, status in summary["runs"]:
        print(f"{slug}: {status}")
    for note in summary["notes"]:
        print(f"NOTE: {note}")
    if summary["mismatch"]:
        print("WARNING: recomputed values differ from stored report.py outputs; see README.md", file=sys.stderr)
        return 3
    print(f"Wrote {summary['out']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
