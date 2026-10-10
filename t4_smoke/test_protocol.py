import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from protocol import main


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
