#!/usr/bin/env python3
"""Build the D036 comparison reference independently from six raw source files.

Run from any directory: python3 pilot_original/independent_expected.py
Use --check to verify the saved JSON without writing it. Standard library only;
no official converter, generated dataset, or project parser is imported or read.
This is an evidence inventory, not runnable reviewed data or a human attestation.
"""

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).with_name("independent_expected.json")
DATASET = "pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json"
REVIEWS = "pilot/reviews_v2_round2"
REVIEWERS = ("R01", "R02")
FORMS = ("E", "R", "C")
SEMANTIC_CHECKS = (
    "quantities", "entities", "units", "relations_rates", "time_conditions",
    "requested_unknown", "explicit_assumptions",
)
STATUS = "A01_status (ACCEPT/REVISE/EXCLUDE)"
REPAIRS = "A01_proposed_text_repairs (form: new text)"
GOLD_OK = "A01_gold_and_units_ok (yes/no)"

# Numeric equality deliberately ignores the separately recorded unit. Currency
# words/symbols may occur in the answer itself; arbitrary prose is not stripped.
CURRENCY = re.compile(r"(?<!\w)(?:INR|Rs\.?|rupees?|rupaye|rupaya)(?!\w)", re.I)
NUMBER = re.compile(
    r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:\s*/\s*[+-]?\d+)?\Z"
)
GROUPED_INTEGER = re.compile(r"[+-]?\d{1,3}(?:,\d{3})+\Z|[+-]?\d{1,2}(?:,\d{2})*,\d{3}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def numeric_literal(raw):
    """Parse one exact literal, allowing currency, grouped digits and slash spaces."""
    value = CURRENCY.sub("", raw).replace("₹", "").strip()
    value = re.sub(r"\s*/\s*", "/", value)
    # A comma is a thousands separator only in valid Western/Indian grouping.
    for part in re.split(r"[/\.]", value):
        if "," in part and not GROUPED_INTEGER.fullmatch(part):
            raise ValueError("invalid grouped digits")
    value = value.replace(",", "")
    if not NUMBER.fullmatch(value):
        raise ValueError("not a single exact numeric literal")
    if "/" in value:
        numerator, denominator = value.split("/")
        return Fraction(numerator) / int(denominator)
    return Fraction(value)


def parse_answer(raw):
    """Return an auditable exact value; never extract an arbitrary digit substring.

    A single labelled equality may supply its RHS (e.g. '1 pen ki cost = INR 19').
    Inequalities are not answers to a maximum question. Multiple lines must all
    supply the same exact value; a truncated decimal makes that test fail. Exact
    values found on separate lines remain available as diagnostic candidates.
    """
    candidates = []
    rules = []
    errors = []
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    for line in lines:
        expression = line
        rule = "numeric_literal_with_optional_currency_and_separators"
        if any(symbol in line for symbol in ("<", ">", "≤", "≥", "≠")):
            errors.append("inequality is not an exact scalar answer")
            continue
        if "=" in line:
            if line.count("=") != 1:
                errors.append("multiple equality signs")
                continue
            label, expression = line.split("=")
            if not label.strip() or not expression.strip():
                errors.append("empty side of labelled equality")
                continue
            rule = "right_hand_side_of_labelled_equality"
        try:
            candidates.append(numeric_literal(expression))
            rules.append(rule)
        except (ValueError, ZeroDivisionError) as exc:
            errors.append(str(exc))
    if not lines:
        errors.append("empty answer")
    if len(set(candidates)) > 1:
        errors.append("conflicting exact values")
    exact = candidates[0] if candidates and not errors else None
    return {
        "exact_value": str(exact) if exact is not None else None,
        "parse_rule": (rules[0] if len(lines) == 1 else "all_lines_same_exact_value")
        if exact is not None else None,
        "exact_candidates": sorted({str(value) for value in candidates}),
        "parse_errors": errors,
    }


def index_unique(rows, key, context):
    result = {}
    for row in rows:
        identity = key(row)
        require(identity not in result, f"{context}: duplicate {identity}")
        result[identity] = row
    return result


def build_reference():
    source_hashes = {}

    def read_raw(relative):
        raw = (ROOT / relative).read_bytes()
        source_hashes[relative] = sha256(raw)
        return raw

    def read_json(relative):
        return json.loads(read_raw(relative))

    dataset = read_json(DATASET)
    require(dataset["schema_version"] == "test1-1", "Unexpected draft schema")
    families = index_unique(dataset["families"], lambda f: f["family_id"], DATASET)
    require(len(families) == 30, "Expected 30 original candidate families")
    expected_keys = {(fid, form) for fid in families for form in FORMS}
    submissions = {}
    reviewer_metadata = {}
    for reviewer in REVIEWERS:
        reviewer_metadata[reviewer] = {}
        for stage in (1, 2):
            relative = f"{REVIEWS}/{reviewer}_stage{stage}_responses.json"
            submission = read_json(relative)
            require(submission["reviewer_id"] == reviewer, f"{relative}: reviewer mismatch")
            require(submission["stage"] == stage, f"{relative}: stage mismatch")
            require(submission["schema_version"] == "annotation-draft-1", f"{relative}: schema mismatch")
            require(submission["dataset_version"] == dataset["version"], f"{relative}: version mismatch")
            require(submission["independent_solve_before_gold"] is True,
                    f"{relative}: solve-before-gold attestation missing")
            rows = index_unique(submission["rows"],
                                lambda row: (row["family_id"], row["intended_form"]), relative)
            require(set(rows) == expected_keys, f"{relative}: missing/unexpected family forms")
            submissions[reviewer, stage] = rows
            reviewer_metadata[reviewer][f"stage{stage}"] = {
                key: value for key, value in submission.items() if key != "rows"
            }
            if stage == 2:
                require(submission["stage1_submission_sha256"] ==
                        source_hashes[f"{REVIEWS}/{reviewer}_stage1_responses.json"],
                        f"{relative}: stage1 submission hash mismatch")

    a01_raw = read_raw(f"{REVIEWS}/A01_worksheet_returned.csv").decode("utf-8-sig")
    a01 = index_unique(csv.DictReader(io.StringIO(a01_raw, newline="")),
                       lambda row: row["family_id"], "A01")
    require(set(a01) == set(families), "A01 family coverage mismatch")
    records = []
    for fid, family in sorted(families.items()):
        adjudication = a01[fid]
        require(adjudication["topic"] == family["topic"], f"{fid}: A01 topic mismatch")
        require(adjudication[STATUS] in ("ACCEPT", "REVISE", "EXCLUDE"), f"{fid}: bad A01 status")
        require(adjudication[GOLD_OK].strip().lower() in ("yes", "no"), f"{fid}: bad gold-ok flag")
        status = adjudication[STATUS]
        repair = adjudication[REPAIRS]
        in_cohort = status == "ACCEPT" and not repair.strip() and fid != "PIL010"
        exclusion_reasons = []
        if status != "ACCEPT":
            exclusion_reasons.append(f"A01 status {status}")
        if repair.strip():
            exclusion_reasons.append("proposed repair lacks independent re-review under D036")
        if fid == "PIL010":
            exclusion_reasons.append("D036 near-duplicate exclusion")
        gold = Fraction(family["gold"]["value"])
        record = {
            "family_id": fid,
            "topic": family["topic"],
            "in_cohort": in_cohort,
            "exclusion_reasons": exclusion_reasons,
            "gold": family["gold"],
            "forms": {},
            "a01": {
                "status": status,
                "final_answer": adjudication["A01_final_answer"],
                "final_unit": adjudication["A01_final_unit"],
                "gold_and_units_ok_raw": adjudication[GOLD_OK],
                "gold_and_units_ok": adjudication[GOLD_OK].strip().lower() == "yes",
                "reason": adjudication["A01_decision_reason"],
                "proposed_text_repairs": repair,
            },
        }
        for form in FORMS:
            rendering = family["forms"][form]
            text_hash = sha256(rendering["text"].encode("utf-8"))
            require(adjudication[f"{form}_text"] == rendering["text"], f"{fid}-{form}: A01 text mismatch")
            form_record = {
                "rendering_id": rendering["rendering_id"],
                "text_sha256": text_hash,
                "reviewers": {},
            }
            for reviewer in REVIEWERS:
                first = submissions[reviewer, 1][fid, form]
                second = submissions[reviewer, 2][fid, form]
                for stage, row in ((1, first), (2, second)):
                    require(row["rendering_id"] == rendering["rendering_id"],
                            f"{fid}-{form}/{reviewer} stage{stage}: rendering ID mismatch")
                    require(row["text_sha256"] == text_hash,
                            f"{fid}-{form}/{reviewer} stage{stage}: text hash mismatch")
                for field in ("independent_answer", "independent_unit", "independent_equation",
                              "independent_reasoning", "solved_at_utc"):
                    require(first[field] == second[field], f"{fid}-{form}/{reviewer}: stage1 {field} changed")
                checks = second["semantic_checks"]
                require(set(checks) == set(SEMANTIC_CHECKS) and
                        all(type(value) is bool for value in checks.values()),
                        f"{fid}-{form}/{reviewer}: invalid semantic checks")
                parsed = parse_answer(first["independent_answer"])
                record_first = {
                    "raw_answer": first["independent_answer"],
                    "raw_unit": first["independent_unit"],
                    **parsed,
                    "equals_gold_exactly": parsed["exact_value"] == str(gold),
                    "contains_gold_exact_candidate": str(gold) in parsed["exact_candidates"],
                }
                form_record["reviewers"][reviewer] = {
                    "stage1": record_first,
                    "stage2": {**{key: second[key] for key in (
                        "disposition", "classification", "naturalness", "readability",
                        "ambiguity_flag", "issue_notes", "reviewed_at_utc")},
                        "semantic_checks": checks,
                        "failed_semantic_checks": [key for key in SEMANTIC_CHECKS if not checks[key]],
                    },
                }
            record["forms"][form] = form_record
        records.append(record)

    def summarize(selected):
        comparisons = [(f"{family['family_id']}-{form}", family["forms"][form]["reviewers"])
                       for family in selected for form in FORMS]
        answer_matches = []
        disposition_matches = []
        for key, reviews in comparisons:
            left, right = (reviews[reviewer] for reviewer in REVIEWERS)
            left_value, right_value = (x["stage1"]["exact_value"] for x in (left, right))
            if left_value is not None and left_value == right_value:
                answer_matches.append(key)
            if left["stage2"]["disposition"] == right["stage2"]["disposition"]:
                disposition_matches.append(key)

        def agreement(matches):
            return {
                "agree": len(matches), "total": len(comparisons),
                "disagree_or_unparseable": [key for key, _ in comparisons if key not in matches],
            }

        return {
            "family_count": len(selected),
            "form_count": len(comparisons),
            "per_topic_counts": dict(sorted(Counter(f["topic"] for f in selected).items())),
            "a01_status_counts": dict(sorted(Counter(f["a01"]["status"] for f in selected).items())),
            "reviewer_answer_agreement": agreement(answer_matches),
            "disposition_agreement": agreement(disposition_matches),
            "reviewers": {
                reviewer: {
                    "answers_equal_gold_exactly": sum(r[reviewer]["stage1"]["equals_gold_exactly"]
                                                      for _, r in comparisons),
                    "answers_not_equal_gold_or_unparseable": [key for key, r in comparisons
                        if not r[reviewer]["stage1"]["equals_gold_exactly"]],
                    "unparseable_answers": [key for key, r in comparisons
                        if r[reviewer]["stage1"]["exact_value"] is None],
                    "stage2_disposition_counts": dict(sorted(Counter(
                        r[reviewer]["stage2"]["disposition"] for _, r in comparisons).items())),
                } for reviewer in REVIEWERS
            },
        }

    cohort = [record for record in records if record["in_cohort"]]
    return {
        "schema_version": "independent-original-pilot-reference-1",
        "decision": "D036",
        "cohort_rule": "A01 ACCEPT with empty proposed-text-repairs field; PIL010 excluded",
        "comparison_policy": {
            "numeric_equality": "Fraction equality; separately recorded units are not scored or corrected",
            "accepted_syntax": "Exact integers, decimals, rationals, slash whitespace, grouped digits, currency words/symbol; one labelled equality uses its RHS",
            "multiple_lines": "All nonempty lines must parse to the same exact value; truncated decimals fail even alongside a correct exact fraction",
            "inequalities": "Not exact scalar answers; no inferred maximum",
            "agreement": "Exact numeric values must both parse and agree; units ignored; disposition agreement compares raw stage2 disposition",
            "human_evidence": "Raw ratings, flags, checks and adjudication are retained; A01 does not rewrite independent answers or reviews",
        },
        "source_sha256": dict(sorted(source_hashes.items())),
        "reviewer_metadata": reviewer_metadata,
        "summary": {
            "cohort_size": len(cohort),
            "cohort_ids": [record["family_id"] for record in cohort],
            "excluded_ids": [record["family_id"] for record in records if not record["in_cohort"]],
            "all_candidates": summarize(records),
            "cohort": summarize(cohort),
        },
        "families": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify existing output bytes without writing")
    args = parser.parse_args()
    reference = build_reference()
    serialized = (json.dumps(reference, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if args.check:
        require(OUTPUT.read_bytes() == serialized, "Saved independent_expected.json is stale")
    else:
        OUTPUT.write_bytes(serialized)
    print(json.dumps(reference["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
