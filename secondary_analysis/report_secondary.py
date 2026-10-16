"""Read completed Test 1 exports; write only a new secondary-report folder."""

import argparse
import hashlib
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .numeric_endpoint import evaluate_numeric

LABEL = "SECONDARY DIAGNOSTIC — strict v1.0.0 endpoint remains primary"
FORMS = ("E", "R", "C")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def _load_run(root):
    _require(not (root / "RUNNING.lock").exists(), "Stop the run writer before secondary analysis")
    names = ("run_manifest.json", "dataset.json", "generation_attempts.jsonl")
    blobs = {name: (root / name).read_bytes() for name in names}
    manifest = json.loads(blobs[names[0]])
    dataset = json.loads(blobs[names[1]])
    journal = [json.loads(line) for line in blobs[names[2]].splitlines() if line.strip()]
    _require(manifest.get("status") == "COMPLETE", "A completed run is required")
    _require(manifest.get("scorer_version") == "1.0.0", "Expected strict scorer v1.0.0")
    if "dataset_sha256" in manifest:
        _require(_digest(dataset) == manifest["dataset_sha256"], "Dataset snapshot corruption")
    renderings = {}
    families = set()
    for family in dataset["families"]:
        fid = family["family_id"]
        _require(fid not in families, "Duplicate dataset family")
        families.add(fid)
        _require(set(family["forms"]) == set(FORMS), "Expected E/R/C for each family")
        for form in FORMS:
            rendering = family["forms"][form]
            rid = rendering["rendering_id"]
            _require(rid not in renderings, "Duplicate dataset rendering")
            renderings[rid] = dict(family_id=fid, form=form, gold=family["gold"])
    _require(bool(renderings), "Empty dataset")
    order = manifest["evaluation_order"]
    _require(len(order) == len(set(order)) and set(order) == set(renderings), "Evaluation order mismatch")
    _require(manifest.get("expected") == manifest.get("completed") == len(renderings), "Run completion mismatch")
    grouped, attempt_ids = {}, set()
    for attempt in journal:
        if "record_sha256" in attempt:
            _require(attempt["record_sha256"] == _digest({k: v for k, v in attempt.items() if k != "record_sha256"}),
                     "Attempt checksum corruption")
        _require(attempt["run_id"] == manifest["run_id"], "Foreign run attempt")
        if "config_sha256" in manifest:
            _require(attempt.get("config_sha256") == manifest["config_sha256"], "Foreign config attempt")
        rid = attempt["rendering_id"]
        _require(rid in renderings, "Unknown rendering in attempts")
        _require(attempt["attempt_id"] not in attempt_ids, "Duplicate attempt ID")
        attempt_ids.add(attempt["attempt_id"])
        grouped.setdefault(rid, []).append(attempt)
    done = []
    for rid in order:
        history = sorted(grouped.get(rid, []), key=lambda row: row["attempt_number"])
        _require([row["attempt_number"] for row in history] == list(range(1, len(history)+1)), "Attempt sequence corruption")
        successful = [row for row in history if row["status"] == "generated"]
        _require(len(successful) == 1 and successful[0] is history[-1], "Need exactly one terminal generated attempt per rendering")
        row = successful[0]
        source = renderings[rid]
        _require(row["family_id"] == source["family_id"] and row["form"] == source["form"], "Attempt/dataset identity mismatch")
        if "gold" in row:
            _require(row["gold"] == source["gold"], "Attempt/dataset gold mismatch")
        _require(type(row["correct"]) is bool and isinstance(row["raw_response"], str), "Malformed stored score/response")
        _require(row.get("scorer_version") == "1.0.0", "Attempt scorer version mismatch")
        _require(row["invalid_reason"] is None or isinstance(row["invalid_reason"], str), "Malformed stored invalid reason")
        done.append((row, source["gold"]))
    hashes = {name: hashlib.sha256(blob).hexdigest() for name, blob in blobs.items()}
    return manifest, done, hashes, len(journal)


def analyze(root):
    """Return (metrics, new_folder). Never rescore or overwrite stored strict scores.

    Infrastructure retries are excluded; the sole terminal generated response
    per rendering is used. Truncated outputs fail numeric_literal_v1; refusal
    regex hits do not veto extraction. Preserved flags support manual audit.
    """
    root = Path(root)
    manifest, done, hashes, journal_count = _load_run(root)
    rows = []
    for attempt, gold in done:
        rows.append(dict(rendering_id=attempt["rendering_id"], family_id=attempt["family_id"],
                         form=attempt["form"], attempt_id=attempt["attempt_id"],
                         strict_correct=attempt["correct"], strict_invalid_reason=attempt["invalid_reason"],
                         truncated=attempt.get("truncated", False), refusal=attempt.get("refusal", False),
                         numeric=evaluate_numeric(attempt["raw_response"], gold, attempt.get("truncated", False))))
    by_form = {}
    for form in FORMS:
        group = [row for row in rows if row["form"] == form]
        n = len(group)
        strict = sum(row["strict_correct"] for row in group)
        numeric = sum(row["numeric"]["correct"] for row in group)
        cross = {validity: {"numeric_correct": 0, "numeric_incorrect": 0}
                 for validity in ("strict_valid", "strict_invalid")}
        for row in group:
            validity = "strict_invalid" if row["strict_invalid_reason"] is not None else "strict_valid"
            outcome = "numeric_correct" if row["numeric"]["correct"] else "numeric_incorrect"
            cross[validity][outcome] += 1
        reasons = {}
        for reason in sorted({row["strict_invalid_reason"] for row in group if row["strict_invalid_reason"] is not None}):
            bad = [row for row in group if row["strict_invalid_reason"] == reason]
            reasons[reason] = dict(count=len(bad), numeric_correct=sum(row["numeric"]["correct"] for row in bad))
        by_form[form] = dict(denominator=n, strict_correct=strict, strict_accuracy=strict/n,
                             numeric_correct=numeric, numeric_accuracy=numeric/n,
                             strict_invalid_by_numeric=cross, invalid_reason_breakdown=reasons,
                             extraction_paths=dict(Counter(row["numeric"]["extraction_path"] for row in group)),
                             numeric_status=dict(Counter(row["numeric"]["status"] for row in group)),
                             strict_correct_by_numeric_match={f"strict_{a}_numeric_{b}": sum(
                                 bool(row["strict_correct"]) is a and row["numeric"]["correct"] is b for row in group)
                                 for a in (True, False) for b in (True, False)},
                             unknown_units=dict(Counter(row["numeric"]["unknown_unit"] for row in group
                                                        if row["numeric"]["unknown_unit"] is not None)))
    metrics = dict(label=LABEL, adoption_status="ADOPTED_SECONDARY_D018", secondary_version=__version__,
                   primary_scorer_version="1.0.0", run_id=manifest["run_id"], source_label=manifest.get("label"),
                   created_at=datetime.now(timezone.utc).isoformat(), source_sha256=hashes,
                   completed=len(rows), journal_attempts=journal_count,
                   policy=dict(strict="stored correct and invalid_reason copied unchanged; no rescore",
                               numeric="numeric_literal_v1: exact literal on the sole FINAL line; no unit conversion; unvalidated suffixes flagged",
                               multiple_final="multiple_finals; never select a value", no_final="missing_final; no recovery from other lines",
                               refusal_truncation="truncated fails; refusal regex hits do not veto; original flags retained"),
                   by_form=by_form, renderings=rows)
    lines = [f"# {LABEL}", "", "Pre-registered SECONDARY endpoint (decision D018); strict v1.0.0 remains primary.", "",
             "Strict accuracy copies stored `correct` unchanged. Numeric accuracy (numeric_literal_v1) checks only the sole FINAL line's literal value against gold, with no unit conversion or unit validation.",
             "Truncated outputs fail; refusal regex hits do not veto extraction. This is not semantic accuracy, a human-reviewed score or a training-benefit result.", "",
             f"Run: `{manifest['run_id']}`; completed renderings: {len(rows)}.", "",
             "| Form | N | Strict correct | Strict accuracy | Numeric correct | Numeric accuracy |",
             "|---|---:|---:|---:|---:|---:|"]
    for form, stats in by_form.items():
        lines.append(f"| {form} | {stats['denominator']} | {stats['strict_correct']} | {stats['strict_accuracy']:.1%} | {stats['numeric_correct']} | {stats['numeric_accuracy']:.1%} |")
    lines += ["", "Cross-tab (strict invalid means stored `invalid_reason` is non-null):", "",
              "| Form | Strict valid / numeric correct | Strict valid / numeric incorrect | Strict invalid / numeric correct | Strict invalid / numeric incorrect |",
              "|---|---:|---:|---:|---:|"]
    for form, stats in by_form.items():
        cross = stats["strict_invalid_by_numeric"]
        cells = [cross[validity][outcome] for validity in ("strict_valid", "strict_invalid")
                 for outcome in ("numeric_correct", "numeric_incorrect")]
        lines.append(f"| {form} | " + " | ".join(map(str, cells)) + " |")
    lines += ["", "Stored invalid-reason breakdown:", "",
              "| Form | Strict invalid reason | Count | Numeric correct |", "|---|---|---:|---:|"]
    for form, stats in by_form.items():
        for reason, counts in stats["invalid_reason_breakdown"].items():
            safe_reason = reason.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {form} | {safe_reason} | {counts['count']} | {counts['numeric_correct']} |")
    lines += ["", "Per-rendering extraction paths, statuses, suffixes and original flags are in `secondary_metrics.json`.",
              "All input files are preserved; each invocation creates a new report directory."]
    # All validation and serialization happen before creating the output folder.
    content = json.dumps(metrics, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    # Detect source changes during analysis; the lock also guards a live writer.
    _require(not (root / "RUNNING.lock").exists(), "Run writer started during analysis")
    _require(all(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items()),
             "Run source changed during analysis")
    dest = root / ("secondary_diagnostic_" + uuid.uuid4().hex)
    dest.mkdir(exist_ok=False)
    with (dest / "secondary_metrics.json").open("x", encoding="utf-8") as stream:
        stream.write(content)
    with (dest / "secondary_summary.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return metrics, dest


def main():
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    _, dest = analyze(args.run_directory)
    print(dest)


if __name__ == "__main__":
    main()
