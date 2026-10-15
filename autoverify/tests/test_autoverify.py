import copy
import csv
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autoverify._common import DEFAULT_SEED, FORMS, SOLVERS, exact
from autoverify.compare import FLAG_REASONS, REVIEW_COLUMNS, compare
from autoverify.make_solver_tasks import make_solver_tasks

ROOT = Path(__file__).resolve().parents[2]


def family(fid="fixture-00", value="1/3"):
    """Intentionally synthetic: metadata sentinels expose accidental leakage."""
    return dict(
        family_id=fid, gold=dict(value=value, unit="litres", aliases=["L"]),
        reference_equation="SECRET_EQUATION", reference_solution_en="SECRET_SOLUTION",
        provenance="SECRET_PROVENANCE", status="DRAFT", review={"secret": "SECRET_REVIEW"},
        forms={form: dict(rendering_id=f"{fid}-{form}",
                          text=f"Synthetic {form} question {fid}: share 1 litre among 3 bottles.",
                          creator_type="SECRET_CREATOR", generation_or_edit_history="SECRET_HISTORY")
               for form in FORMS})


def solver_rows(families):
    return [dict(rendering_id=f["forms"][form]["rendering_id"], final_answer=f["gold"]["value"],
                 unit=f["gold"]["unit"],
                 extraction=dict(quantities=["1", "3"], entities=["water", "bottles"],
                                 asked_for="water per bottle"))
            for f in families for form in FORMS]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.families_path = self.root / "families.json"
        self.paths = {solver: self.root / f"{solver}_outputs.jsonl" for solver in SOLVERS}
        self.families = [family()]
        self.rows = {solver: solver_rows(self.families) for solver in SOLVERS}

    def write_inputs(self, *, wrapped=False):
        self.families_path.write_text(json.dumps(
            {"families": self.families} if wrapped else self.families), encoding="utf-8")
        for solver, path in self.paths.items():
            path.write_text("".join(json.dumps(row) + "\n" for row in self.rows[solver]), encoding="utf-8")

    def run_compare(self, *, seed=DEFAULT_SEED, directory="review", wrapped=False):
        self.write_inputs(wrapped=wrapped)
        return compare(self.families_path, self.paths["claude"], self.paths["gpt"],
                       self.root / directory, seed)

    def test_exact_fraction_and_decimal_notation(self):
        for i, row in enumerate(self.rows["gpt"]):
            row["final_answer"] = ["2/6", "10/30", "-1/-3"][i]
            row["extraction"]["quantities"] = [3, "2/2"]
            row["extraction"]["asked_for"] = "  WATER   per bottle  "
        report = self.run_compare()
        self.assertEqual(report["families"][0]["flag_reasons"], [])
        for rendering in report["families"][0]["renderings"]:
            self.assertTrue(rendering["solvers_agree"])
            self.assertTrue(all(s["answer_equals_gold"] for s in rendering["solvers"].values()))
        # JSON numeric decimals must never go through a binary float.
        self.families[0]["gold"]["value"] = "1/10"
        for rows in self.rows.values():
            for row in rows:
                row["final_answer"] = 0.1
        report = self.run_compare()
        self.assertFalse(report["families"][0]["flagged"])
        self.assertEqual(report["families"][0]["renderings"][0]["solvers"]["gpt"]["normalized_answer"], "1/10")
        on_disk = json.loads((self.root / "review/verification_report.json").read_text())
        self.assertEqual(on_disk, report)

    def test_truncated_fraction_is_not_exact(self):
        self.rows["gpt"][0]["final_answer"] = "0.3333333333333333333333333333"
        report = self.run_compare()
        self.assertEqual(report["families"][0]["flag_reasons"],
                         ["solver_gold_mismatch", "solver_disagreement"])

    def test_same_wrong_answers_agree_but_mismatch_gold(self):
        for rows in self.rows.values():
            for row in rows:
                row["final_answer"] = "7"
        result = self.run_compare()["families"][0]
        self.assertEqual(result["flag_reasons"], ["solver_gold_mismatch"])
        self.assertTrue(result["renderings"][0]["solvers_agree"])

    def test_quantity_multiset_preserves_multiplicity(self):
        self.rows["claude"][1]["extraction"]["quantities"] = ["1", "3", "3"]
        result = self.run_compare()["families"][0]
        self.assertEqual(result["flag_reasons"], ["cross_form_quantity_mismatch"])
        self.assertFalse(result["cross_form"]["claude"]["quantities_consistent"])
        self.assertTrue(result["cross_form"]["claude"]["asked_for_consistent"])
        self.assertEqual(result["cross_form"]["claude"]["quantity_multisets"]["R"], {"1": 1, "3": 2})

    def test_asked_for_mismatch_independently_flags(self):
        self.rows["gpt"][2]["extraction"]["asked_for"] = "number of bottles"
        result = self.run_compare()["families"][0]
        self.assertEqual(result["flag_reasons"], ["cross_form_quantity_mismatch"])
        self.assertTrue(result["cross_form"]["gpt"]["quantities_consistent"])
        self.assertFalse(result["cross_form"]["gpt"]["asked_for_consistent"])

    def test_cross_form_checks_are_per_solver(self):
        for row in self.rows["gpt"]:
            row["extraction"]["quantities"] = ["99"]
            row["extraction"]["asked_for"] = "volume per container"
        self.assertEqual(self.run_compare()["families"][0]["flag_reasons"], [])

    def test_ambiguity_note(self):
        self.rows["gpt"][1]["ambiguity_note"] = "Owner of the bottles is unclear."
        result = self.run_compare()["families"][0]
        self.assertEqual(result["flag_reasons"], ["ambiguity_noted"])
        self.assertEqual(result["renderings"][1]["flag_reasons"], ["ambiguity_noted"])
        self.rows["gpt"][1]["ambiguity_note"] = " \t "
        self.assertFalse(self.run_compare()["families"][0]["flagged"])

    def test_missing_output_is_unknown_not_disagreement(self):
        self.rows["gpt"].pop(0)
        result = self.run_compare()["families"][0]
        self.assertEqual(result["flag_reasons"], ["missing_output"])
        rendering = result["renderings"][0]
        self.assertIsNone(rendering["solvers_agree"])
        self.assertEqual(rendering["solvers"]["gpt"], dict(present=False, answer_equals_gold=None))
        self.assertFalse(result["cross_form"]["gpt"]["complete"])
        self.assertTrue(result["cross_form"]["gpt"]["quantities_consistent"])

    def test_missing_forms_still_compare_available_pair(self):
        self.rows["gpt"].pop(0)
        self.rows["gpt"][0]["extraction"]["quantities"] = ["4"]
        result = self.run_compare()["families"][0]
        self.assertEqual(result["flag_reasons"], ["cross_form_quantity_mismatch", "missing_output"])
        self.rows["gpt"].pop(0)
        result = self.run_compare()["families"][0]
        self.assertIsNone(result["cross_form"]["gpt"]["quantities_consistent"])
        self.assertIsNone(result["cross_form"]["gpt"]["asked_for_consistent"])

    def test_empty_outputs_flag_every_family_and_are_not_sampled(self):
        self.rows = {solver: [] for solver in SOLVERS}
        report = self.run_compare()
        self.assertEqual(report["families"][0]["flag_reasons"], ["missing_output"])
        self.assertEqual(report["sampling"]["sampled_family_ids"], [])
        self.assertEqual(report["summary"]["review_families"], 1)

    def test_all_flags_are_reported_together(self):
        self.rows["claude"][0]["final_answer"] = "2"
        self.rows["claude"][0]["ambiguity_note"] = "Two readings possible."
        self.rows["claude"][1]["extraction"]["quantities"] = ["8"]
        self.rows["gpt"].pop(2)
        report = self.run_compare()
        self.assertEqual(report["families"][0]["flag_reasons"], list(FLAG_REASONS))
        self.assertEqual(report["summary"]["flag_counts"], dict.fromkeys(FLAG_REASONS, 1))

    def test_blind_files_only_whitelisted_fields_and_seeded(self):
        self.families = [family(f"fixture-{i:02}", "987654321/7") for i in range(10)]
        self.write_inputs()
        before = self.families_path.read_bytes()
        paths = make_solver_tasks(self.families_path, self.root / "tasks")
        expected = {(f["family_id"], form, f["forms"][form]["rendering_id"], f["forms"][form]["text"])
                    for f in self.families for form in FORMS}
        saved = {}
        for solver, path in paths.items():
            saved[solver] = path.read_bytes()
            data = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(data), len(expected))
            for task in data:
                self.assertEqual(set(task), {"family_id", "rendering_id", "form", "text"})
            self.assertEqual({(r["family_id"], r["form"], r["rendering_id"], r["text"]) for r in data}, expected)
            self.assertNotIn(b"SECRET", saved[solver])
            self.assertNotIn(b"987654321", saved[solver])
        self.assertNotEqual(saved["claude"], saved["gpt"])
        self.families.reverse()
        self.write_inputs(wrapped=True)
        paths2 = make_solver_tasks(self.families_path, self.root / "tasks2")
        for solver in SOLVERS:
            self.assertEqual(saved[solver], paths2[solver].read_bytes())
        paths3 = make_solver_tasks(self.families_path, self.root / "tasks3", seed=44)
        self.assertNotEqual(saved["claude"], paths3["claude"].read_bytes())
        # The first generation did not change its input.
        self.assertEqual(json.loads(before), list(reversed(self.families)))

    def test_blind_generation_does_not_require_or_read_gold_fields(self):
        del self.families[0]["gold"]
        self.write_inputs()
        paths = make_solver_tasks(self.families_path, self.root / "tasks")
        self.assertEqual(len(paths["claude"].read_text().splitlines()), 3)

    def test_seeded_sampling_flags_first_and_blank_review_columns(self):
        self.families = [family(f"fixture-{i:02}") for i in range(29)]
        self.rows = {solver: solver_rows(self.families) for solver in SOLVERS}
        self.rows["gpt"][0]["ambiguity_note"] = "Review fixture."
        self.rows["gpt"][6]["final_answer"] = "5"
        report = self.run_compare(seed=11)
        unflagged = [f["family_id"] for f in self.families if f["family_id"] not in ("fixture-00", "fixture-02")]
        expected_sample = random.Random(11).sample(unflagged, 6)
        self.assertEqual(report["sampling"]["sampled_family_ids"], expected_sample)
        expected_ids = ["fixture-00", "fixture-02"] + expected_sample
        self.assertEqual(report["review_family_ids"], expected_ids)
        with (self.root / "review/review_sheet.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, list(REVIEW_COLUMNS))
            self.assertEqual(reader.fieldnames[-1], "gold_after_review")
            rows = list(reader)
        self.assertEqual([row["family_id"] for row in rows], expected_ids)
        self.assertEqual(len(set(expected_ids)), len(rows))
        for i, row in enumerate(rows):
            self.assertEqual(row["review_selection"], "flagged" if i < 2 else "sample")
            self.assertTrue(all(row[col] == "" for col in REVIEW_COLUMNS[6:-1]))
            self.assertEqual(json.loads(row["gold_after_review"]), {"value": "1/3", "unit": "litres"})
            self.assertEqual(row["E_text"], next(f for f in self.families if f["family_id"] == row["family_id"])["forms"]["E"]["text"])
        self.assertEqual(len(report["families"]), 29)

    def test_sampling_rounding_for_small_populations(self):
        for count in (1, 4, 5, 6, 10):
            with self.subTest(count=count):
                self.families = [family(f"fixture-{i:02}") for i in range(count)]
                self.rows = {solver: solver_rows(self.families) for solver in SOLVERS}
                self.assertEqual(self.run_compare()["summary"]["sampled_unflagged_families"], (count + 4) // 5)

    def test_reports_are_byte_deterministic_and_input_order_independent(self):
        self.families = [family(f"fixture-{i:02}") for i in range(31)]
        self.rows = {solver: solver_rows(self.families) for solver in SOLVERS}
        self.run_compare(seed=83, directory="first")
        snapshots = {path: path.read_bytes() for path in (self.families_path, *self.paths.values())}
        compare(self.families_path, *self.paths.values(), self.root / "repeat", seed=83)
        for path, data in snapshots.items():
            self.assertEqual(path.read_bytes(), data)
        self.families.reverse()
        for rows in self.rows.values():
            random.Random(4).shuffle(rows)
        self.run_compare(seed=83, directory="second", wrapped=True)
        for name in ("verification_report.json", "review_sheet.csv"):
            self.assertEqual((self.root / "first" / name).read_bytes(), (self.root / "repeat" / name).read_bytes())
            self.assertEqual((self.root / "first" / name).read_bytes(), (self.root / "second" / name).read_bytes())
        self.run_compare(seed=84, directory="third")
        self.assertNotEqual((self.root / "first/review_sheet.csv").read_bytes(), (self.root / "third/review_sheet.csv").read_bytes())

    def test_multiline_unicode_text_round_trips_csv(self):
        self.families[0]["forms"]["R"]["text"] = 'Synthetic, "question"\nपानी कितना?'
        self.run_compare()
        with (self.root / "review/review_sheet.csv").open(newline="", encoding="utf-8") as handle:
            row = next(csv.DictReader(handle))
        self.assertEqual(row["R_text"], self.families[0]["forms"]["R"]["text"])

    def test_invalid_solver_schema_rejected_before_writing(self):
        mutations = [
            lambda row: row.update(final_answer=True),
            lambda row: row.update(final_answer="1/0"),
            lambda row: row.update(final_answer="NaN"),
            lambda row: row.update(final_answer="FINAL: 1/3 litres"),
            lambda row: row.pop("unit"),
            lambda row: row.update(ambiguity_note=None),
            lambda row: row.update(extraction=[]),
            lambda row: row["extraction"].update(quantities="1,3"),
            lambda row: row["extraction"].update(quantities=["1/0"]),
            lambda row: row["extraction"].update(entities=[4]),
            lambda row: row["extraction"].update(asked_for="  "),
        ]
        baseline = copy.deepcopy(self.rows)
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.rows = copy.deepcopy(baseline)
                mutate(self.rows["gpt"][0])
                with self.assertRaises(ValueError):
                    self.run_compare()
                self.assertFalse((self.root / "review").exists())

    def test_duplicate_unknown_and_malformed_solver_rows_rejected(self):
        self.rows["gpt"].append(copy.deepcopy(self.rows["gpt"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate rendering_id"):
            self.run_compare()
        self.rows["gpt"][-1]["rendering_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unknown or missing"):
            self.run_compare()
        self.paths["gpt"].write_text("not-json\n")
        with self.assertRaisesRegex(ValueError, ":1:"):
            compare(self.families_path, *self.paths.values(), self.root / "review")
        self.assertFalse((self.root / "review").exists())

    def test_invalid_family_identity_or_missing_forms_rejected(self):
        baseline = copy.deepcopy(self.families)
        variants = [[], [family(), family()], [family("another"), family()]]
        variants[-1][0]["forms"]["E"]["rendering_id"] = "fixture-00-E"
        missing_form = copy.deepcopy(baseline)
        del missing_form[0]["forms"]["C"]
        variants.append(missing_form)
        for families in variants:
            with self.subTest(families=families):
                self.families = families
                with self.assertRaises(ValueError):
                    self.run_compare()

    def test_blank_solver_lines_and_integer_json_answers(self):
        self.families[0]["gold"]["value"] = "8"
        for rows in self.rows.values():
            for row in rows:
                row["final_answer"] = 8
        self.write_inputs()
        for path in self.paths.values():
            path.write_text("\n" + path.read_text() + "  \n")
        report = compare(self.families_path, *self.paths.values(), self.root / "review")
        self.assertFalse(report["families"][0]["flagged"])

    def test_cli_direct_and_module_entrypoints(self):
        self.write_inputs()
        for invocation in ([str(ROOT / "autoverify/make_solver_tasks.py")],
                           ["-m", "autoverify.make_solver_tasks"]):
            result = subprocess.run([sys.executable, "-B", *invocation, str(self.families_path),
                                     "--out-dir", str(self.root / "tasks")], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        for invocation in ([str(ROOT / "autoverify/compare.py")], ["-m", "autoverify.compare"]):
            result = subprocess.run([sys.executable, "-B", *invocation, str(self.families_path),
                                     "--claude", str(self.paths["claude"]), "--gpt", str(self.paths["gpt"]),
                                     "--out-dir", str(self.root / "review")], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.paths["gpt"].write_text('{"rendering_id":"unknown"}\n')
        result = subprocess.run([sys.executable, "-B", "-m", "autoverify.compare", str(self.families_path),
                                 "--claude", str(self.paths["claude"]), "--gpt", str(self.paths["gpt"]),
                                 "--out-dir", str(self.root / "bad")], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown or missing rendering_id", result.stderr)
        self.assertFalse((self.root / "bad").exists())

    def test_exact_parser_rejects_binary_floats(self):
        for value in (0.1, True, None, "1/0", "NaN", "2 metres"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exact(value)


if __name__ == "__main__":
    unittest.main()
