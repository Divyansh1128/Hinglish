#!/usr/bin/env python3
"""EXPLORATORY — not pre-registered; does not change the confirmatory result (Harm, D052).

Read the sealed FINAL_TEST ZIP without extraction or network access. Only the
two derived error_analysis artifacts in the output directory may be written.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import statistics
import sys
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from secondary_analysis import numeric_literal_v2 as numeric  # noqa: E402

LABEL = "EXPLORATORY — not pre-registered; does not change the confirmatory result (Harm, D052)"
FORMS = ("E", "R", "C")
SEEDS = (11, 22, 33)
CHECKPOINTS = ("unchanged",) + tuple(f"{a}:{s}" for a in ("EE", "ER", "EC") for s in SEEDS)
CATEGORIES = ("strict_correct", "numeric_correct_strict_wrong", "numeric_mismatch", "numeric_unscored_strict_wrong")
BINS = (("0–32", 0, 32), ("33–48", 33, 48), ("49–64", 49, 64),
        ("65–96", 65, 96), ("97–128", 97, 128), ("129+", 129, float("inf")))
NUMBER = re.compile(r"[+−-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)(?:\s*/\s*[+−-]?\d[\d,]*)?")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def boolean(value):
    require(value in ("True", "False"), "Malformed CSV boolean")
    return value == "True"


def pct(k, n):
    return 100 * k / n if n else None


def rate(k, n):
    return {"count": k, "denominator": n, "percent": pct(k, n)}


def count_map(values):
    return dict(sorted(Counter(values).items()))


def redact(text):
    # All emitted answer displays are model text, with numeric literals hidden.
    return " ".join(NUMBER.sub("[NUM]", text).split())


def member_bytes(archive, name):
    require(archive.namelist().count(name) == 1, f"Missing/duplicate archive member: {name}")
    return archive.read(name)


def verify_checksums(archive):
    entries = member_bytes(archive, "checksums.sha256").decode().splitlines()
    checked = set()
    for line in entries:
        digest, name = line.split("  ", 1)
        require(name not in checked and sha(member_bytes(archive, name)) == digest,
                f"Inner ZIP checksum mismatch: {name}")
        checked.add(name)
    required = {"predictions.csv", "dataset.json", "dataset_snapshot.jsonl", "run_manifest.json",
                "experiment_config.json", "source/scorer_v1.py"}
    require(required <= checked, "Required files missing from checksum manifest")
    return len(checked)


def load_rows(archive_path):
    blob = archive_path.read_bytes()
    rows, runs, snapshots, scorer_hashes = [], [], [], set()
    with zipfile.ZipFile(io.BytesIO(blob)) as outer:
        names = sorted(n for n in outer.namelist() if n.endswith("_results.zip"))
        expected = {"base"} | {f"{a}-s{s}" for a in ("EE", "ER", "EC") for s in SEEDS}
        require(len(names) == 10, "Expected exactly ten inner results ZIPs")
        require({Path(n).name.removesuffix("_results.zip") for n in names} == expected,
                "Unexpected checkpoint names")
        for name in names:
            run_blob = member_bytes(outer, name)
            slug = Path(name).name.removesuffix("_results.zip")
            checkpoint = "unchanged" if slug == "base" else slug.replace("-s", ":")
            with zipfile.ZipFile(io.BytesIO(run_blob)) as inner:
                checked = verify_checksums(inner)
                manifest = json.loads(member_bytes(inner, "run_manifest.json"))
                config = json.loads(member_bytes(inner, "experiment_config.json"))
                require(manifest["status"] == "COMPLETE" and manifest["scorer_version"] == "1.0.0",
                        "Expected a complete run using strict scorer 1.0.0")
                require(config["model_id"] == "Qwen/Qwen3-4B", "Unexpected backbone")
                if checkpoint != "unchanged":
                    arm, seed = checkpoint.split(":")
                    require((config["adapter"]["arm"], config["adapter"]["seed"]) == (arm, int(seed)),
                            "Adapter identity disagrees with archive filename")
                snapshot = member_bytes(inner, "dataset_snapshot.jsonl")
                snapshots.append(sha(snapshot))
                families = [json.loads(line) for line in snapshot.splitlines() if line.strip()]
                family_map = {f["family_id"]: f for f in families}
                require(len(families) == len(family_map) == 100, "Expected 100 unique families")
                dataset = json.loads(member_bytes(inner, "dataset.json"))
                dataset_map = {f["family_id"]: f for f in dataset["families"]}
                require(set(dataset_map) == set(family_map), "Dataset/snapshot family sets disagree")
                for fid, family in dataset_map.items():
                    require(all(key in family_map[fid] and value == family_map[fid][key]
                                for key, value in family.items()), "Dataset and snapshot content disagree")
                scorer_hashes.add(sha(member_bytes(inner, "source/scorer_v1.py")))
                predictions = member_bytes(inner, "predictions.csv")
                duplicate = str(Path(name).with_name(slug) / "predictions.csv")
                if duplicate in outer.namelist():
                    require(predictions == member_bytes(outer, duplicate), "Outer/inner predictions differ")
                current = list(csv.DictReader(io.StringIO(predictions.decode("utf-8-sig"))))
                require(len(current) == 300, "Expected 300 predictions per run")
                seen = set()
                for row in current:
                    fid, form = row["family_id"], row["form"]
                    require(fid in family_map and form in FORMS, "Unknown family/form")
                    require((fid, form) not in seen, "Duplicate family/form")
                    seen.add((fid, form))
                    require(row["rendering_id"] == family_map[fid]["forms"][form]["rendering_id"],
                            "Rendering identity mismatch")
                    require(row["run_id"] == manifest["run_id"] and row["status"] == "generated",
                            "Foreign or unresolved prediction")
                    gold = family_map[fid]["gold"]
                    strict = boolean(row["correct"])
                    truncated = boolean(row["truncated"])
                    result = numeric.evaluate_numeric(row["raw_response"], gold, truncated)
                    require(not (strict and result["status"] == "mismatch"),
                            "Strict-correct numeric mismatch needs a conversion-aware audit")
                    if strict:
                        category = "strict_correct"
                    elif result["correct"]:
                        category = "numeric_correct_strict_wrong"
                    elif result["status"] == "mismatch":
                        category = "numeric_mismatch"
                    else:
                        category = "numeric_unscored_strict_wrong"
                    # Retain only booleans/metadata about gold, never its answer values.
                    body_lines = [line.strip() for line in row["raw_response"].splitlines()
                                  if line.strip() and not re.search(r"\bFINAL\b", line, re.I)]
                    rows.append({
                        "checkpoint": checkpoint, "arm": checkpoint.split(":")[0], "family": fid,
                        "form": form, "strict": strict, "numeric": result["correct"],
                        "numeric_status": result["status"], "category": category,
                        "reason": row["invalid_reason"] or "none", "tokens": int(row["output_tokens"]),
                        "truncated": truncated, "final": row["extracted_final"],
                        "response_prefix": row["raw_response"][:200],
                        "body_lines": len(body_lines), "equals": "\n".join(body_lines).count("="),
                        "gold_dimensionless": not bool((gold["unit"] or "").strip()),
                    })
                require(seen == {(fid, form) for fid in family_map for form in FORMS}, "Incomplete pairing")
                runs.append({"checkpoint": checkpoint, "run_id": manifest["run_id"],
                             "inner_member": name, "inner_sha256": sha(run_blob),
                             "predictions_sha256": sha(predictions), "verified_checksum_entries": checked})
    require(len(set(snapshots)) == 1 and len(scorer_hashes) == 1, "Dataset/scorer drift across runs")
    require(len(rows) == 3000, "Unexpected total row count")
    return rows, {"archive_sha256": sha(blob), "dataset_snapshot_sha256": snapshots[0],
                  "archived_strict_scorer_sha256": next(iter(scorer_hashes)),
                  "runs": sorted(runs, key=lambda r: CHECKPOINTS.index(r["checkpoint"]))}


def summarize(rows):
    n = len(rows)
    categories = {c: rate(sum(r["category"] == c for r in rows), n) for c in CATEGORIES}
    require(sum(x["count"] for x in categories.values()) == n, "Partition failed")
    return {"n": n, "categories": categories,
            "numeric_correct": rate(sum(r["numeric"] for r in rows), n),
            "numeric_scored": rate(sum(r["numeric_status"] in ("match", "mismatch") for r in rows), n),
            "strict_correct_numeric_unscored": sum(r["strict"] and not r["numeric"] for r in rows),
            "rescued_by_invalid_reason": count_map(r["reason"] for r in rows
                                                    if r["category"] == "numeric_correct_strict_wrong"),
            "numeric_mismatch_by_invalid_reason": count_map(r["reason"] for r in rows
                                                           if r["category"] == "numeric_mismatch"),
            "unscored_strict_wrong_by_numeric_status": count_map(r["numeric_status"] for r in rows
                                                                 if r["category"] == "numeric_unscored_strict_wrong"),
            "unscored_strict_wrong_by_invalid_reason": count_map(r["reason"] for r in rows
                                                                 if r["category"] == "numeric_unscored_strict_wrong"),
            "all_invalid_reasons": count_map(r["reason"] for r in rows if r["reason"] != "none")}


def length_stats(rows):
    tokens = [r["tokens"] for r in rows]
    return {"n": len(rows), "median_tokens": statistics.median(tokens) if rows else None,
            "mean_tokens": statistics.mean(tokens) if rows else None,
            "strict": rate(sum(r["strict"] for r in rows), len(rows)),
            "numeric": rate(sum(r["numeric"] for r in rows), len(rows)),
            "mean_nonfinal_lines": statistics.mean(r["body_lines"] for r in rows) if rows else None,
            "median_nonfinal_lines": statistics.median(r["body_lines"] for r in rows) if rows else None,
            "zero_nonfinal_lines": rate(sum(r["body_lines"] == 0 for r in rows), len(rows)),
            "at_most_one_nonfinal_line": rate(sum(r["body_lines"] <= 1 for r in rows), len(rows)),
            "no_equals_in_nonfinal_text": rate(sum(r["equals"] == 0 for r in rows), len(rows)),
            "two_or_more_equals_in_nonfinal_text": rate(sum(r["equals"] >= 2 for r in rows), len(rows))}


def length_detail(rows):
    return {"all": length_stats(rows),
            "by_category": {c: length_stats([r for r in rows if r["category"] == c]) for c in CATEGORIES},
            "strict_correct": length_stats([r for r in rows if r["strict"]]),
            "strict_wrong": length_stats([r for r in rows if not r["strict"]]),
            "bins": {label: length_stats([r for r in rows if lo <= r["tokens"] <= hi])
                     for label, lo, hi in BINS},
            "short_le48": length_stats([r for r in rows if r["tokens"] <= 48]),
            "long_gt48": length_stats([r for r in rows if r["tokens"] > 48])}


def decompose(base, trained):
    """Exact partition identity; gaps positive when unchanged is better."""
    b, t = summarize(base), summarize(trained)
    gap = b["categories"]["strict_correct"]["percent"] - t["categories"]["strict_correct"]["percent"]
    components = {c: t["categories"][c]["percent"] - b["categories"][c]["percent"] for c in CATEGORIES[1:]}
    require(abs(sum(components.values()) - gap) < 1e-10, "Gap decomposition failed")
    numeric_gap = b["numeric_correct"]["percent"] - t["numeric_correct"]["percent"]
    # Numeric is not a superset of strict: include strict-only successes explicitly.
    correction = pct(b["strict_correct_numeric_unscored"], b["n"]) - pct(t["strict_correct_numeric_unscored"], t["n"])
    require(abs(numeric_gap + components["numeric_correct_strict_wrong"] + correction - gap) < 1e-10,
            "Nonnested-endpoint identity failed")
    return {"base_n": b["n"], "trained_n": t["n"], "strict_gap_pp": gap,
            "components_pp": components,
            "components_as_percent_of_strict_gap": {c: pct(value, gap) for c, value in components.items()},
            "numeric_endpoint_gap_pp": numeric_gap, "strict_only_correction_pp": correction}


def contrast(pairs):
    n = len(pairs)
    strict_ec, strict_er = sum(a["strict"] for a, b in pairs), sum(b["strict"] for a, b in pairs)
    numeric_ec, numeric_er = sum(a["numeric"] for a, b in pairs), sum(b["numeric"] for a, b in pairs)
    return {"paired_items": n, "strict_EC": rate(strict_ec, n), "strict_ER": rate(strict_er, n),
            "numeric_EC": rate(numeric_ec, n), "numeric_ER": rate(numeric_er, n),
            "strict_delta_C_pp": pct(strict_ec - strict_er, n),
            "numeric_delta_C_pp": pct(numeric_ec - numeric_er, n),
            "numeric_EC_only_correct": sum(a["numeric"] and not b["numeric"] for a, b in pairs),
            "numeric_ER_only_correct": sum(b["numeric"] and not a["numeric"] for a, b in pairs)}


def delta_analysis(rows):
    index = {(r["checkpoint"], r["family"]): r for r in rows if r["form"] == "C"}
    families = sorted({r["family"] for r in rows})
    all_pairs, scored_pairs, per_seed = [], [], {}
    scored = lambda r: r["numeric_status"] in ("match", "mismatch")
    common = [f for f in families if all(scored(index[(f"{a}:{s}", f)])
                                        for a in ("ER", "EC") for s in SEEDS)]
    common_pairs = []
    for seed in SEEDS:
        pairs = [(index[(f"EC:{seed}", f)], index[(f"ER:{seed}", f)]) for f in families]
        restricted = [(a, b) for a, b in pairs if scored(a) and scored(b)]
        all_pairs.extend(pairs)
        scored_pairs.extend(restricted)
        common_pairs.extend((index[(f"EC:{seed}", f)], index[(f"ER:{seed}", f)]) for f in common)
        per_seed[str(seed)] = {"all_items": contrast(pairs), "both_numeric_scored": contrast(restricted)}
    result = {"all_items": contrast(all_pairs), "both_numeric_scored_pooled": contrast(scored_pairs),
              "common_all_six_checkpoints": dict(contrast(common_pairs), families=len(common)),
              "per_seed": per_seed,
              "restricted_equal_seed_mean_numeric_delta_C_pp": statistics.mean(
                  x["both_numeric_scored"]["numeric_delta_C_pp"] for x in per_seed.values())}
    return result


def invalid_units(rows):
    invalid = [r for r in rows if r["checkpoint"] != "unchanged" and r["reason"] == "invalid_unit"]
    groups = defaultdict(list)
    for row in invalid:
        groups[redact(row["final"])].append(row)
    patterns = []
    for pattern, group in sorted(groups.items(), key=lambda x: (-len(x[1]), x[0])):
        patterns.append({"redacted_final_answer": pattern, "count": len(group),
                         "numeric_correct": sum(r["numeric"] for r in group),
                         "numeric_mismatch": sum(r["numeric_status"] == "mismatch" for r in group),
                         "numeric_unscored": sum(r["numeric_status"] not in ("match", "mismatch") for r in group),
                         "by_form": count_map(r["form"] for r in group),
                         "by_arm": count_map(r["arm"] for r in group),
                         "distinct_families": len({r["family"] for r in group}),
                         "gold_dimensionless_count": sum(r["gold_dimensionless"] for r in group)})
    # At most three actual response prefixes, never an appended gold/reference.
    # Hide all title-case words conservatively (including names) and all numbers.
    examples = []
    for i, pattern in enumerate(patterns[:3]):
        source = groups[pattern["redacted_final_answer"]][0]["response_prefix"]
        source = re.sub(r"\b(?:FT|DEV|PILOT)[A-Z0-9_-]*\b", "[ITEM]", source)
        source = re.sub(r"\b[A-Z][a-z]+\b", "[WORD]", source)
        examples.append({"example": i + 1, "snippet": redact(source)[:200]})
    return {"n": len(invalid), "by_form": count_map(r["form"] for r in invalid),
            "numeric_correct": sum(r["numeric"] for r in invalid),
            "numeric_mismatch": sum(r["numeric_status"] == "mismatch" for r in invalid),
            "numeric_unscored": sum(r["numeric_status"] not in ("match", "mismatch") for r in invalid),
            "gold_dimensionless_count": sum(r["gold_dimensionless"] for r in invalid),
            "distinct_families": len({r["family"] for r in invalid}),
            "patterns": patterns, "examples": examples}


def validate_published(rows, text):
    # Check all 60 published checkpoint × form endpoint counts, without importing
    # the confirmatory analysis (which would expose an unrelated inference path).
    for endpoint, heading in (("strict", "strict"), ("numeric", "numeric_literal_v2")):
        section = text.split(f"## Accuracy by checkpoint — {heading} (", 1)[1].split("\n## ", 1)[0]
        parsed = {}
        for line in section.splitlines():
            cells = [x.strip() for x in line.split("|")[1:-1]]
            if cells and cells[0] in CHECKPOINTS:
                parsed[cells[0]] = [int(re.match(r"(\d+)/100", x).group(1)) for x in cells[1:]]
        require(set(parsed) == set(CHECKPOINTS), "Published accuracy table incomplete")
        for checkpoint in CHECKPOINTS:
            actual = [sum(r[endpoint] for r in rows if r["checkpoint"] == checkpoint and r["form"] == f)
                      for f in FORMS]
            require(parsed[checkpoint] == actual, f"Published {endpoint} counts disagree: {checkpoint}")
    require("**Decision label: Harm**" in text, "Unexpected confirmatory decision context")
    return {"published_checkpoint_form_endpoint_counts_matched": 60, "confirmatory_decision": "Harm (D052)"}


def analyze(rows, provenance, published):
    subsets = {c: {f: [r for r in rows if r["checkpoint"] == c and r["form"] == f] for f in FORMS}
               for c in CHECKPOINTS}
    arm_rows = {a: {f: [r for r in rows if r["arm"] == a and r["form"] == f] for f in FORMS}
                for a in ("EE", "ER", "EC")}
    checkpoint_form = {c: {f: summarize(subsets[c][f]) for f in FORMS} for c in CHECKPOINTS}
    group_rows = {"unchanged": [r for r in rows if r["checkpoint"] == "unchanged"],
                  "trained": [r for r in rows if r["checkpoint"] != "unchanged"]}
    matched = {}
    base_index = {(r["family"], r["form"]): r for r in group_rows["unchanged"]}
    for arm in ("EE", "ER", "EC"):
        matched[arm] = {}
        for form in FORMS:
            groups = defaultdict(list)
            for r in arm_rows[arm][form]:
                b = base_index[(r["family"], form)]
                key = ("both_strict_correct" if b["strict"] and r["strict"] else
                       "base_correct_trained_wrong" if b["strict"] else
                       "trained_correct_base_wrong" if r["strict"] else "both_strict_wrong")
                groups[key].append(r["tokens"] - b["tokens"])
                groups["all"].append(r["tokens"] - b["tokens"])
            matched[arm][form] = {key: {"n": len(values), "mean_trained_minus_base_tokens": statistics.mean(values),
                                       "median_trained_minus_base_tokens": statistics.median(values)}
                                  for key, values in sorted(groups.items())}
    result = {"label": LABEL, "schema_version": 1,
              "provenance": provenance, "validation": validate_published(rows, published),
              "methods": {
                  "numeric_endpoint": "Repository secondary_analysis.numeric_literal_v2.evaluate_numeric; no conversions",
                  "partition": "strict correct; else numeric match; else numeric mismatch; else unscored. All denominators include every generated row.",
                  "gap": "unchanged strict accuracy minus trained strict accuracy = excess rescued format/unit errors + excess literal mismatches + excess unscored strict errors (trained minus unchanged). This is accounting, not causal attribution.",
                  "nonnested": "Strict success need not be numeric success: endpoint suffix grammar is narrower. Numeric gap + excess rescue + base-minus-trained strict-only success = strict gap.",
                  "pooling": "Arms pool 3 fixed checkpoints, 300 observations per form over the same 100 families. Unchanged has 100/form and is not 3 independent baselines. No independence-based inference.",
                  "length": "Post hoc fixed bins and short <=48 tokens. Nonfinal lines exclude blank lines and lines containing FINAL. Equals counts are descriptive layout proxies, not counts of valid reasoning steps.",
                  "delta_restriction": "Use identical C family items for EC and ER within each seed where BOTH endpoint statuses are match/mismatch. Report pooled pairs and equal-seed mean; also a fixed family subset parseable in all six EC/ER checkpoints. Selection depends on outputs.",
                  "privacy": "No gold answers or complete raw responses saved. Numeric literals in final-answer patterns are replaced by [NUM]; whitespace is collapsed, unit wording/case retained. At most 3 anonymised response-prefix excerpts: take first 200 source characters, mask numbers/item IDs/title-case words, collapse whitespace, then cap at 200 characters. Pattern counts combine scalar variants.",
                  "uncertainty": "Counts and percentages only; no resampling or significance tests.",
              },
              "overall": {g: summarize(rs) for g, rs in group_rows.items()},
              "checkpoint_form": checkpoint_form,
              "arm_form": {a: {f: summarize(rs) for f, rs in by_form.items()} for a, by_form in arm_rows.items()},
              "gap_by_checkpoint_form": {c: {f: decompose(subsets["unchanged"][f], subsets[c][f]) for f in FORMS}
                                         for c in CHECKPOINTS if c != "unchanged"},
              "gap_by_arm_form": {a: {f: decompose(subsets["unchanged"][f], arm_rows[a][f]) for f in FORMS}
                                  for a in arm_rows},
              "gap_all_trained_by_form": {f: decompose(subsets["unchanged"][f],
                                                      [r for r in group_rows["trained"] if r["form"] == f]) for f in FORMS},
              "length": {
                  "by_group": {g: length_detail(rs) for g, rs in group_rows.items()},
                  "by_group_form": {g: {f: length_detail([r for r in rs if r["form"] == f]) for f in FORMS}
                                    for g, rs in group_rows.items()},
                  "by_checkpoint_form": {c: {f: length_detail(subsets[c][f]) for f in FORMS} for c in CHECKPOINTS},
                  "matched_token_differences": matched,
                  "truncated": sum(r["truncated"] for r in rows),
              }, "invalid_units_trained": invalid_units(rows), "delta_C": delta_analysis(rows)}
    return result


def fnum(value, decimals=2):
    return "—" if value is None else f"{value:.{decimals}f}"


def cell_rate(value):
    return f"{value['count']}/{value['denominator']} ({fnum(value['percent'], 1)}%)"


def reasons(mapping):
    return ", ".join(f"{k}: {v}" for k, v in mapping.items()) or "none"


def table(headers, records):
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return ["| " + " | ".join(map(escape, headers)) + " |",
            "| " + " | ".join("---" for _ in headers) + " |"] + [
                "| " + " | ".join(map(escape, row)) + " |" for row in records]


def report(data):
    lines = [f"# {LABEL}", "", "Phase-2 FINAL_TEST error analysis. Counts are descriptive, post hoc, and conditional on these fixed checkpoints and families.", "",
             "## Main findings", ""]
    lines.extend(f"- {s}" for s in summary(data)[1:])
    lines += ["", "## Inputs and validation", "",
              "Only the ten inner `*_results.zip` predictions were scored; duplicate outer copies were checked, not counted. Inner checksums, complete unique pairing, identical dataset snapshots and strict-scorer sources were verified. All 60 strict/numeric checkpoint × form counts match the supplied confirmatory report. Strict scores were copied unchanged.", "",
              f"Outer archive SHA-256: `{data['provenance']['archive_sha256']}`.",
              f"Confirmatory report SHA-256: `{data['provenance']['confirmatory_report_sha256']}`.",
              "Source and inner-member hashes are in JSON. No generated timestamp or absolute path enters the outputs.", "",
              "## Error partition by checkpoint and form", "",
              "S = stored strict-correct; F = numeric-correct but strict-wrong; M = numeric literal mismatch among strict-wrong; U = numerically unscored and strict-wrong. S+F+M+U=N. Numeric endpoints require an extractable FINAL scalar and do not convert units. M is evidence of a wrong declared literal, not a diagnosis of arithmetic versus reasoning or semantic quantity accuracy. U cannot be labelled a reasoning error. F establishes a strict unit/format failure; it does not validate dimensional meaning.", ""]
    records = []
    for c in CHECKPOINTS:
        for form in FORMS:
            s = data["checkpoint_form"][c][form]
            records.append([c, form] + [cell_rate(s["categories"][k]) for k in CATEGORIES]
                           + [cell_rate(s["numeric_correct"]), s["strict_correct_numeric_unscored"], reasons(s["rescued_by_invalid_reason"])])
    lines += table(["Checkpoint", "Form", "S strict", "F rescued", "M numeric wrong", "U unscored wrong", "Numeric correct", "Strict-only successes", "F by invalid_reason"], records)
    lines += ["", "Strict-only successes are retained in S even when the numeric parser rejects their suffix syntax. They prevent treating numeric accuracy as a simple superset of strict accuracy. Full mismatch-by-invalid-reason, U statuses and reasons are in JSON.", "",
              "Numeric mismatches by strict invalid_reason, pooled across forms (these are components of M, not additional errors):", ""]
    lines += table(["Group", "No strict format/unit failure", "invalid_unit", "percent_requires_dimensionless", "Total M", "Strict-only successes"], [
        [group, d["numeric_mismatch_by_invalid_reason"].get("none", 0),
         d["numeric_mismatch_by_invalid_reason"].get("invalid_unit", 0),
         d["numeric_mismatch_by_invalid_reason"].get("percent_requires_dimensionless", 0),
         d["categories"]["numeric_mismatch"]["count"], d["strict_correct_numeric_unscored"]]
        for group, d in data["overall"].items()])
    lines += ["", "A mismatch with an invalid unit can have both a number and a unit problem. The endpoint cannot isolate those mechanisms. Percent literals are scaled by 1/100 by the numeric endpoint; invalid percentage-unit combinations can thus also be literal mismatches. The no-format/unit-failure column confirms that the trained deficit includes wrong values even when strict answer syntax and units are accepted.", "",
              "## Trained-versus-unchanged gap decomposition", "",
              "Positive gaps mean unchanged is better. For each form, **strict gap = excess F + excess M + excess U**, where excess is the trained error rate minus the unchanged error rate. Each row is an exact disjoint accounting identity. An invalid_unit answer with a wrong literal belongs to M, so the F component is a conservative count of demonstrably number-correct strict failures, not all unit-invalid answers. The mechanism of an individual failure is not identified.", "",
              "Arm rows pool three seeds (300 outputs/form); unchanged is 100 outputs/form. The same families and baseline are reused, without treating observations as independent.", ""]
    gap_records = []
    for arm, forms in list(data["gap_by_arm_form"].items()) + [("All trained", data["gap_all_trained_by_form"])]:
        for form, g in forms.items():
            components = g["components_pp"]
            gap_records.append([arm, form, fnum(g["strict_gap_pp"])] + [
                f"{fnum(components[k])} ({fnum(g['components_as_percent_of_strict_gap'][k], 1)}%)" for k in CATEGORIES[1:]]
                + [fnum(g["numeric_endpoint_gap_pp"]), fnum(g["strict_only_correction_pp"])])
    lines += table(["Arm", "Form", "Strict gap pp", "F pp (% gap)", "M pp (% gap)", "U pp (% gap)", "Numeric endpoint gap pp", "Strict-only correction pp"], gap_records)
    lines += ["", "The nonnested endpoint identity is also checked: strict gap = numeric endpoint gap + excess F + (unchanged strict-only success rate − trained strict-only success rate). Consequently strict-minus-numeric gap reduction alone is not an exact count of added unit failures.", "",
              "Checkpoint-level decomposition (all entries in percentage points):", ""]
    lines += table(["Checkpoint", "Form", "Strict gap", "F", "M", "U"], [
        [c, f, fnum(g["strict_gap_pp"])] + [fnum(g["components_pp"][k]) for k in CATEGORIES[1:]]
        for c, forms in data["gap_by_checkpoint_form"].items() for f, g in forms.items()])
    lines += ["", "## Length, correctness and visible working", "",
              "Bins and the ≤48-token short threshold were chosen after seeing the length distribution. Token counts come from the stored generation metadata. Within-bin rates compare different items; difficulty, form and checkpoint can confound them. No causal effect of length is estimated.", ""]
    lines += table(["Group", "Form", "N", "Median tokens all / S / F / M / U", "Mean nonfinal lines", "≤1 nonfinal line", "≥2 '=' signs"], [
        [g, f, d["all"]["n"], " / ".join(fnum(d["all"]["median_tokens"], 1) if k == "all" else fnum(d["by_category"][k]["median_tokens"], 1)
                                          for k in ("all",) + CATEGORIES),
         fnum(d["all"]["mean_nonfinal_lines"]), cell_rate(d["all"]["at_most_one_nonfinal_line"]),
         cell_rate(d["all"]["two_or_more_equals_in_nonfinal_text"])]
        for g, forms in data["length"]["by_group_form"].items() for f, d in forms.items()])
    lines += ["", "All forms pooled, then within each form:", ""]
    bin_records = []
    for group, detail in data["length"]["by_group"].items():
        for scope, d in [("all", detail)] + list(data["length"]["by_group_form"][group].items()):
            for label, s in d["bins"].items():
                bin_records.append([group, scope, label, s["n"], cell_rate(s["strict"]), cell_rate(s["numeric"])])
    lines += table(["Group", "Form", "Tokens", "N", "Strict", "Numeric"], bin_records)
    lines += ["", "Same-family, same-form token differences (trained − unchanged), averaged across each arm's seeds:", ""]
    lines += table(["Arm", "Form", "All N; mean Δ tokens", "Both strict-correct N; mean Δ tokens", "Base correct / trained wrong N; mean Δ tokens"], [
        [a, f] + [f"{g[k]['n']}; {fnum(g[k]['mean_trained_minus_base_tokens'], 1)}" if k in g else "0; —"
                  for k in ("all", "both_strict_correct", "base_correct_trained_wrong")]
        for a, forms in data["length"]["matched_token_differences"].items() for f, g in forms.items()])
    short = data["length"]["by_group"]["trained"]["short_le48"]
    long = data["length"]["by_group"]["trained"]["long_gt48"]
    lines += ["", f"Among trained outputs, ≤48-token answers have numeric accuracy {cell_rate(short['numeric'])}, versus {cell_rate(long['numeric'])} for >48 tokens; strict accuracy is {cell_rate(short['strict'])} versus {cell_rate(long['strict'])}. The shorter group is more accurate in this descriptive comparison, so a simple within-trained length-deficit story is unsupported.", "",
              "Trained answers use fewer separate lines, while the table shows that multiple '=' signs remain common: visible equations are often compressed into a single line. A single line may contain several operations and a long response may repeat errors. Nonfinal-line and '=' counts are layout proxies, not a semantic step audit. The data do not establish that omitted steps caused the numeric loss. Full checkpoint × form length strata and all four paired outcome cells are in JSON.",
              f"No output was truncated ({data['length']['truncated']}/3000), so the observed brevity is not an output-token-cap failure.", "",
              "## Trained invalid_unit answer strings", ""]
    unit = data["invalid_units_trained"]
    lines += [f"There are {unit['n']} invalid_unit outputs across {unit['distinct_families']} distinct families: {unit['numeric_correct']} numeric matches, {unit['numeric_mismatch']} mismatches, {unit['numeric_unscored']} unscored. {unit['gold_dimensionless_count']} occur on items whose canonical unit is empty. Counts are outputs, with repeated forms/seeds, not independent failures.", "",
              "Strict scorer 1.0.0 accepts the canonical unit, supplied aliases and declared conversions (plus its currency rules); otherwise it returns invalid_unit. An added count noun on an item with an empty canonical unit can therefore fail. A rejected real unit can also reflect wording or scale; numeric_literal_v2 neither validates nor converts it.", "",
              "Top 25 emitted final-answer strings after replacing numeric literals with `[NUM]` and collapsing whitespace. Different scalar values are pooled; unit wording/case is preserved. Only model-emitted text is displayed, with no gold answer values. All patterns, form/arm counts and distinct-family counts are in JSON.", ""]
    lines += table(["Literal-redacted final answer", "Count", "Numeric match", "Mismatch", "Unscored", "Empty canonical unit"], [
        [p["redacted_final_answer"], p["count"], p["numeric_correct"], p["numeric_mismatch"], p["numeric_unscored"], p["gold_dimensionless_count"]]
        for p in unit["patterns"][:25]])
    lines += ["", "Three anonymised response snippets only, one representative per leading unit pattern (first 200 source characters, then capped at 200 after redaction). Numbers are `[NUM]`; all title-case words are conservatively hidden as `[WORD]` to remove names. No item IDs, question text, or gold answers are included:", ""]
    lines.extend(f"- Example {e['example']}: `{e['snippet']}`" for e in unit["examples"])
    lines += ["", "## Δ_C on numerically scored items", "",
              "Δ_C is EC − ER on C. 'Numerically scored' means an endpoint status of match or mismatch, including both successes and failures. Both arms must be scored on the identical family within a seed; independently filtering each arm would break pairing. We also use the same family subset across all six EC/ER checkpoints. Output-dependent filtering changes the estimand and is descriptive only.", ""]
    delta = data["delta_C"]
    delta_rows = []
    for label, key in (("All C outputs", "all_items"), ("Both parseable within seed (pooled)", "both_numeric_scored_pooled"),
                       ("Common families, all six checkpoints", "common_all_six_checkpoints")):
        c = delta[key]
        delta_rows.append([label, c["paired_items"], cell_rate(c["numeric_EC"]), cell_rate(c["numeric_ER"]),
                           fnum(c["strict_delta_C_pp"]), fnum(c["numeric_delta_C_pp"])])
    for seed, strata in delta["per_seed"].items():
        c = strata["both_numeric_scored"]
        delta_rows.append([f"Seed {seed}, both parseable", c["paired_items"], cell_rate(c["numeric_EC"]), cell_rate(c["numeric_ER"]),
                           fnum(c["strict_delta_C_pp"]), fnum(c["numeric_delta_C_pp"])])
    lines += table(["Subset", "Pairs", "EC numeric", "ER numeric", "Strict Δ_C pp", "Numeric Δ_C pp"], delta_rows)
    lines += ["", f"Equal-seed mean of within-seed restricted numeric contrasts: {fnum(delta['restricted_equal_seed_mean_numeric_delta_C_pp'])} pp. Common all-six subset: {delta['common_all_six_checkpoints']['families']} families. No uncertainty interval or significance test is attached to these filtered contrasts.", "",
              "## Interpretation limits", "",
              "The trained deficit contains both extra number-correct unit failures and a larger wrong-literal component. Brevity and added answer nouns are consistent with a changed response style, but these outputs alone cannot identify the training cause, distinguish arithmetic from comprehension failures, or show that longer reasoning would repair the errors. Unit-blind literal matching is not a replacement primary scorer. Pooling repeats the same authored families across forms and seeds; it does not increase the number of independent families. The confirmatory strict Harm decision (D052) is unchanged.", "",
              LABEL, ""]
    return "\n".join(lines)


def summary(data):
    b, t = data["overall"]["unchanged"], data["overall"]["trained"]
    gaps = data["gap_all_trained_by_form"]
    lengths = data["length"]["by_group"]
    u, d = data["invalid_units_trained"], data["delta_C"]
    return [LABEL,
            "Validated 10 complete runs, 3,000 outputs and all 60 published strict/numeric checkpoint × form counts.",
            f"Strict: trained {cell_rate(t['categories']['strict_correct'])}; unchanged {cell_rate(b['categories']['strict_correct'])}.",
            f"Numeric literal: trained {cell_rate(t['numeric_correct'])}; unchanged {cell_rate(b['numeric_correct'])}.",
            "Pooled strict deficits E/R/C: " + "/".join(fnum(gaps[f]["strict_gap_pp"]) for f in FORMS) + " pp.",
            "Excess number-correct unit failures explain E/R/C: " + "/".join(fnum(gaps[f]["components_pp"]["numeric_correct_strict_wrong"]) for f in FORMS) + " pp of those deficits.",
            "Excess numeric mismatches explain E/R/C: " + "/".join(fnum(gaps[f]["components_pp"]["numeric_mismatch"]) for f in FORMS) + " pp; residual unscored errors are separate.",
            f"Median output tokens: trained {fnum(lengths['trained']['all']['median_tokens'], 1)} vs unchanged {fnum(lengths['unchanged']['all']['median_tokens'], 1)}; omitted reasoning is not established causally.",
            f"Trained invalid_unit: {u['n']} outputs, {u['numeric_correct']} numeric matches; most common pattern {u['patterns'][0]['redacted_final_answer']} ({u['patterns'][0]['count']}).",
            f"Numeric Δ_C stays negative: all {fnum(d['all_items']['numeric_delta_C_pp'])} pp; paired scored {fnum(d['both_numeric_scored_pooled']['numeric_delta_C_pp'])} pp ({d['both_numeric_scored_pooled']['paired_items']} pairs); all-six common {fnum(d['common_all_six_checkpoints']['numeric_delta_C_pp'])} pp."]


def main():
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("--archive", type=Path, default=ROOT / "results/phase2/final_test/Phase2_FinalTest_results.zip")
    parser.add_argument("--confirmatory-report", type=Path, default=ROOT / "results/phase2/final_test/phase2_analysis.md")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--check", action="store_true", help="Compare regenerated artifacts byte-for-byte; write nothing")
    args = parser.parse_args()
    rows, provenance = load_rows(args.archive)
    published = args.confirmatory_report.read_bytes()
    provenance["confirmatory_report_sha256"] = sha(published)
    provenance["code_sha256"] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (
        Path(__file__).resolve(), ROOT / "secondary_analysis/numeric_literal_v2.py", ROOT / "secondary_analysis/numeric_endpoint.py")}
    data = analyze(rows, provenance, published.decode())
    artifacts = {"error_analysis.json": json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                 "error_analysis.md": report(data)}
    # Refuse to overwrite unrelated existing files. --check performs zero writes.
    for name in artifacts:
        path = args.output_dir / name
        if path.exists():
            require(LABEL in path.read_text(), f"Refusing to overwrite an unrelated artifact: {name}")
    if args.check:
        for name, content in artifacts.items():
            path = args.output_dir / name
            require(path.is_file() and path.read_bytes() == content.encode(), f"Reproduction mismatch: {name}")
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in artifacts.items():
            (args.output_dir / name).write_bytes(content.encode())
    print("\n".join(summary(data)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        sys.exit(f"{LABEL}\nAnalysis failed: {error}")
