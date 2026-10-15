#!/usr/bin/env python3
"""Compare independent solver JSONL and write a report plus human review CSV."""

import argparse
import csv
import json
import random
from collections import Counter
from decimal import Decimal
from pathlib import Path

if __package__:
    from ._common import (DEFAULT_SEED, FORMS, SOLVERS, exact, json_text,
                          load_families, normalized_text)
else:
    from _common import (DEFAULT_SEED, FORMS, SOLVERS, exact, json_text,
                         load_families, normalized_text)

FLAG_REASONS = ("solver_gold_mismatch", "solver_disagreement",
                "cross_form_quantity_mismatch", "ambiguity_noted", "missing_output")
REVIEW_COLUMNS = ("family_id", "review_selection", "flag_reasons", "E_text", "R_text", "C_text",
                  "equivalence_ok", "naturalness_R (1-5)", "naturalness_C (1-5)",
                  "decision (ACCEPT/REVISE/REJECT)", "notes", "gold_after_review")


def load_solver_outputs(path, expected_ids):
    """Reject malformed, duplicate and unknown rows rather than silently scoring them."""
    outputs = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, parse_float=Decimal)
            if not isinstance(row, dict):
                raise ValueError("output row must be an object")
            rid = row.get("rendering_id")
            if not isinstance(rid, str) or rid not in expected_ids:
                raise ValueError("unknown or missing rendering_id")
            if rid in outputs:
                raise ValueError(f"duplicate rendering_id: {rid}")
            exact(row.get("final_answer"))
            if not isinstance(row.get("unit"), str):
                raise ValueError("unit must be a string (empty for dimensionless)")
            extraction = row.get("extraction")
            if not isinstance(extraction, dict):
                raise ValueError("extraction must be an object")
            quantities = extraction.get("quantities")
            if not isinstance(quantities, list):
                raise ValueError("extraction.quantities must be a list")
            for quantity in quantities:
                exact(quantity)
            entities = extraction.get("entities")
            if not isinstance(entities, list) or not all(
                    isinstance(entity, str) and entity.strip() for entity in entities):
                raise ValueError("extraction.entities must be a list of nonblank strings")
            asked_for = extraction.get("asked_for")
            if not isinstance(asked_for, str) or not asked_for.strip():
                raise ValueError("extraction.asked_for must be a nonblank string")
            if not isinstance(row.get("ambiguity_note", ""), str):
                raise ValueError("ambiguity_note must be a string when present")
            outputs[rid] = row
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from None
    return outputs


def _flags(reasons):
    return [reason for reason in FLAG_REASONS if reason in reasons]


def build_report(families, outputs, seed=DEFAULT_SEED):
    results = []
    for family in sorted(families, key=lambda family: family["family_id"]):
        gold = exact(family["gold"]["value"])
        reasons, renderings = set(), []
        for form in FORMS:
            rid = family["forms"][form]["rendering_id"]
            rendering_reasons, solver_results, answers = set(), {}, {}
            for solver in SOLVERS:
                row = outputs[solver].get(rid)
                if row is None:
                    solver_results[solver] = dict(present=False, answer_equals_gold=None)
                    rendering_reasons.add("missing_output")
                    continue
                answer = exact(row["final_answer"])
                answers[solver] = answer
                solver_results[solver] = dict(
                    present=True, final_answer=str(row["final_answer"]),
                    normalized_answer=str(answer), unit=row["unit"],
                    answer_equals_gold=(answer == gold), extraction=row["extraction"],
                    ambiguity_note=row.get("ambiguity_note", ""))
                if answer != gold:
                    rendering_reasons.add("solver_gold_mismatch")
                if row.get("ambiguity_note", "").strip():
                    rendering_reasons.add("ambiguity_noted")
            agree = answers["claude"] == answers["gpt"] if len(answers) == 2 else None
            if agree is False:
                rendering_reasons.add("solver_disagreement")
            reasons.update(rendering_reasons)
            renderings.append(dict(rendering_id=rid, form=form, solvers=solver_results,
                                   solvers_agree=agree, flag_reasons=_flags(rendering_reasons)))

        cross_form = {}
        for solver in SOLVERS:
            available = {form: outputs[solver][family["forms"][form]["rendering_id"]]["extraction"]
                         for form in FORMS if family["forms"][form]["rendering_id"] in outputs[solver]}
            # Counter preserves repeated quantities; order and numeric notation do not matter.
            quantities = {form: Counter(str(exact(q)) for q in extraction["quantities"])
                          for form, extraction in available.items()}
            asked = {form: normalized_text(extraction["asked_for"])
                     for form, extraction in available.items()}
            quantities_ok = (all(q == next(iter(quantities.values())) for q in quantities.values())
                             if len(available) >= 2 else None)
            asked_ok = len(set(asked.values())) == 1 if len(available) >= 2 else None
            cross_form[solver] = dict(
                available_forms=list(available), complete=len(available) == len(FORMS),
                quantity_multisets={form: dict(sorted(counts.items())) for form, counts in quantities.items()},
                asked_for=asked, quantities_consistent=quantities_ok, asked_for_consistent=asked_ok)
            # The prescribed flag covers both extraction checks; details distinguish them.
            if quantities_ok is False or asked_ok is False:
                reasons.add("cross_form_quantity_mismatch")
        results.append(dict(family_id=family["family_id"], gold=dict(value=str(gold), unit=family["gold"]["unit"]),
                            flagged=bool(reasons), flag_reasons=_flags(reasons),
                            renderings=renderings, cross_form=cross_form))

    flagged = [family["family_id"] for family in results if family["flagged"]]
    unflagged = [family["family_id"] for family in results if not family["flagged"]]
    sample_count = (len(unflagged) + 4) // 5  # ceil(20%); no sample when there are none
    sampled = random.Random(seed).sample(unflagged, sample_count)
    return dict(
        schema_version="autoverify-1", seed=seed,
        comparison_policy="exact numeric Fraction equality; units retained without conversion or validation",
        sampling=dict(fraction="1/5", rounding="ceiling", population="unflagged families",
                      sampled_family_ids=sampled),
        summary=dict(families=len(results), renderings=len(results) * len(FORMS),
                     flagged_families=len(flagged), sampled_unflagged_families=len(sampled),
                     review_families=len(flagged) + len(sampled),
                     flag_counts={reason: sum(reason in f["flag_reasons"] for f in results)
                                  for reason in FLAG_REASONS}),
        review_family_ids=flagged + sampled, families=results)


def compare(families_path, claude_path, gpt_path, out_dir, seed=DEFAULT_SEED):
    families = load_families(families_path, require_gold=True)
    expected_ids = {family["forms"][form]["rendering_id"] for family in families for form in FORMS}
    outputs = {solver: load_solver_outputs(path, expected_ids)
               for solver, path in zip(SOLVERS, (claude_path, gpt_path))}
    report = build_report(families, outputs, seed)
    destination = Path(out_dir)
    report_path, review_path = destination / "verification_report.json", destination / "review_sheet.csv"
    if {Path(p).resolve() for p in (families_path, claude_path, gpt_path)} & {
            report_path.resolve(), review_path.resolve()}:
        raise ValueError("output would overwrite an input file")
    destination.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json_text(report), encoding="utf-8")
    by_id = {family["family_id"]: family for family in families}
    result_by_id = {family["family_id"]: family for family in report["families"]}
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for fid in report["review_family_ids"]:
            family, result = by_id[fid], result_by_id[fid]
            row = dict(family_id=fid, review_selection="flagged" if result["flagged"] else "sample",
                       flag_reasons=";".join(result["flag_reasons"]),
                       gold_after_review=json.dumps(result["gold"], ensure_ascii=False, sort_keys=True))
            row.update({f"{form}_text": family["forms"][form]["text"] for form in FORMS})
            writer.writerow(row)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("families", type=Path)
    parser.add_argument("--claude", type=Path, required=True, help="Claude solver output JSONL")
    parser.add_argument("--gpt", type=Path, required=True, help="GPT solver output JSONL")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)
    try:
        report = compare(args.families, args.claude, args.gpt, args.out_dir, args.seed)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    counts = report["summary"]
    print(f"{counts['families']} families: {counts['flagged_families']} flagged; "
          f"{counts['sampled_unflagged_families']} unflagged sampled for review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
