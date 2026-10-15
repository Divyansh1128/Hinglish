import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from protocol import INSTRUCTION, INSTRUCTION_V1, encode_record, main, validate_data, validate_final


class TargetTests(unittest.TestCase):
    def test_instruction_byte_equality_with_evaluation(self):
        from test1_pilot.hinglish_pilot.engine import INSTRUCTION as evaluation
        from test1_pilot.hinglish_pilot.engine import INSTRUCTION_V1 as historical
        self.assertEqual(INSTRUCTION.encode("utf-8"), evaluation.encode("utf-8"))
        self.assertEqual(INSTRUCTION_V1.encode("utf-8"), historical.encode("utf-8"))
        self.assertNotEqual(INSTRUCTION, INSTRUCTION_V1)

    def test_bare_numbers_and_fractions(self):
        for answer in ("8", "7/27", "-1.25", "+.125", "3 / 8", "1,41,150", "141,150"):
            with self.subTest(answer=answer):
                validate_final("English explanation.\nFINAL: " + answer, unit="")

    def test_english_units(self):
        for unit in ("rupees", "INR", "Rs", "kg", "L", "minutes", "beads", "marbles", "pieces", "%"):
            with self.subTest(unit=unit):
                validate_final("English explanation.\nFINAL: 19 " + unit, unit=unit)

    def test_reject_suffixes_for_dimensionless_targets(self):
        for number in ("8", "7/27"):
            for suffix in ("unitless", "unit", "positions", "whole", "fraction", "part", ".", "(no unit)", "kg"):
                with self.subTest(number=number, suffix=suffix), self.assertRaises(ValueError):
                    validate_final("FINAL: " + number + " " + suffix, unit="")

    def test_reject_non_english_and_unknown_units(self):
        for unit in ("rupaye", "moti", "kanche", "minat", "kilomitar", "किलो", "inventedunit"):
            with self.subTest(unit=unit), self.assertRaisesRegex(ValueError, "English unit"):
                validate_final("FINAL: 19 " + unit)

    def test_invalid_or_nonterminal_final(self):
        for text in ("No marker", "FINAL: 8\nFINAL: 8", "Reason: FINAL: 8", "FINAL: 8\nNote.",
                     "FINAL: **8**", "FINAL: 8.", "FINAL: 7/0", "FINAL: 1,23", "FINAL: INR 19", "FINAL: 8 unitless"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_final(text)
        with self.assertRaisesRegex(ValueError, "unit presence"):
            validate_final("FINAL: 8", unit="kg")

    def test_encode_uses_v2_and_checks_before_tokenization(self):
        class Tokenizer:
            all_special_tokens = []
            eos_token_id = 7
            pad_token_id = 7

            def apply_chat_template(self, messages, **settings):
                self.messages = messages
                return [8, 9]

            def encode(self, text, **settings):
                return [20 + ord(char) for char in text]

        family = dict(family_id="fixture", forms={"E": "Existing contract fixture"}, completion="FINAL: 7/27")
        tokenizer = Tokenizer()
        encode_record(tokenizer, family, "E")
        self.assertEqual(tokenizer.messages[0]["content"], INSTRUCTION)
        family["completion"] = "FINAL: 7/27 unitless"
        with self.assertRaises(ValueError):
            encode_record(object(), family, "E")
        family["completion"] = "FINAL: 7/27"
        family["reference_solution_en"] = "Explanation.\nFINAL: 7/27 fraction"
        with self.assertRaises(ValueError):
            encode_record(object(), family, "E")

    def test_data_preflight_validates_both_targets(self):
        # All cases fail at the first existing contract fixture, before the
        # split identities are needed. These are not training data families.
        family = dict(family_id="fixture", source_family_id="source", split_role="SMOKE_TRAIN",
                      provenance="contract fixture", source_license="fixture", completion="FINAL: 8",
                      reference_solution_en="Explanation.\nFINAL: 8")
        manifest = dict(audit=dict(approved=True, reviewer="fixture", unresolved_matches=0))
        for field in ("completion", "reference_solution_en"):
            for target in ("FINAL: 8 unitless", "FINAL: 8 moti"):
                altered = dict(family, **{field: target})
                with self.subTest(field=field, target=target), self.assertRaisesRegex(ValueError, "English unit"):
                    validate_data(dict(version="fixture", families=[altered] * 16), manifest)
        family.update(gold=dict(unit=""), completion="FINAL: 8 kg")
        with self.assertRaisesRegex(ValueError, "unit presence"):
            validate_data(dict(version="fixture", families=[family] * 16), manifest)


class PreflightTests(unittest.TestCase):
    def invoke(self, arguments):
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                main(arguments)
            except SystemExit as error:
                return error.code, output.getvalue(), errors.getvalue()
        return 0, output.getvalue(), errors.getvalue()

    def test_self_check(self):
        code, output, errors = self.invoke(["self-check"])
        self.assertEqual(code, 0)
        self.assertIn("PASS: model-free", output)
        self.assertEqual(errors, "")

    def test_input_preflight(self):
        families = [{
            "family_id": f"smoke-{index}", "source_family_id": f"source-{index}",
            "split_role": "SMOKE_TRAIN", "provenance": "synthetic test fixture, not research data",
            "source_license": "fixture", "completion": "FINAL: 1",
            "forms": {form: f"{form} fixture {index}" for form in ("E", "R", "C")},
        } for index in range(16)]
        pilot = [{"family_id": f"pilot-{index}", "source_family_id": f"pilot-source-{index}"}
                 for index in range(30)]
        data = {"version": "fixture", "families": families}
        manifest = {
            "audit": {"approved": True, "reviewer": "fixture", "unresolved_matches": 0},
            "PILOT_EVAL": pilot, "RETIRED_DRAFT": [], "CONFIRM_TRAIN": [], "FINAL_TEST": [],
            "development_exclusion_ids": [record[field] for record in families + pilot
                                          for field in ("family_id", "source_family_id")],
        }
        with tempfile.TemporaryDirectory() as directory:
            inputs = Path(directory) / "inputs.json"
            splits = Path(directory) / "splits.json"
            inputs.write_text(json.dumps(data))
            splits.write_text(json.dumps(manifest))
            arguments = ["validate", "--inputs", str(inputs), "--splits", str(splits),
                         "--revision", "a" * 40]
            code, output, errors = self.invoke(arguments)
            self.assertEqual(code, 0)
            report = json.loads(output)
            self.assertEqual(report["status"], "input_contracts_passed")
            self.assertEqual(report["smoke_families"], 16)
            self.assertEqual(len(report["inputs_sha256"]), 64)
            self.assertTrue(report["not_verified"])
            self.assertEqual(errors, "")
            manifest["audit"]["approved"] = False
            splits.write_text(json.dumps(manifest))
            code, output, errors = self.invoke(arguments)
            self.assertEqual(code, 1)
            self.assertEqual(output, "")
            self.assertIn("Human split audit required", errors)
            inputs.write_text("{")
            code, output, errors = self.invoke(arguments)
            self.assertEqual(code, 1)
            self.assertIn("Preflight failed", errors)

    def test_mutable_revision_rejected_before_reading(self):
        code, output, errors = self.invoke([
            "validate", "--inputs", "unused.json", "--splits", "unused.json", "--revision", "main",
        ])
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("immutable 40-hex commit SHA", errors)

    def test_example_data_cannot_pass(self):
        root = Path(__file__).resolve().parent
        code, output, errors = self.invoke([
            "validate", "--inputs", str(root / "inputs.example.json"),
            "--splits", str(root / "splits.example.json"), "--revision", "a" * 40,
        ])
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("Exactly 16 smoke families required", errors)


if __name__ == "__main__":
    unittest.main()
