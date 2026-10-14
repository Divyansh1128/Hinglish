import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from secondary_analysis.report_secondary import LABEL, _digest, analyze
from test1_pilot.hinglish_pilot.scorer_v1 import score_response


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gold = dict(value="19", unit="", aliases=[], conversions={},
                         unit_omission_allowed=True, rounding_rule="exact")
        self.dataset = dict(families=[dict(family_id=f"FAKE-{n}", gold=self.gold,
                            forms={form: dict(rendering_id=f"FAKE-{n}-{form}", text="Synthetic placeholder")
                                   for form in ("E", "R", "C")}) for n in (1, 2)])
        self.order = [f"FAKE-{n}-{form}" for n in (1, 2) for form in ("E", "R", "C")]
        self.manifest = dict(run_id="synthetic-run", label="FAKE — SOFTWARE TEST ONLY", status="COMPLETE",
                             scorer_version="1.0.0", expected=6, completed=6, evaluation_order=self.order,
                             dataset_sha256=_digest(self.dataset), config_sha256="synthetic-config")
        responses = ["FINAL: 19", "FINAL: **19**", "FINAL: 20", "FINAL: 19\nNote.", "No answer", "FINAL: 19 parts"]
        self.journal = []
        for rid, response in zip(self.order, responses):
            row = dict(run_id="synthetic-run", config_sha256="synthetic-config", rendering_id=rid,
                       family_id=rid.rsplit("-", 1)[0], form=rid[-1], gold=copy.deepcopy(self.gold),
                       attempt_id=rid+"-attempt", attempt_number=1, status="generated", raw_response=response,
                       truncated=False, refusal=False, **score_response(response, self.gold))
            self.journal.append(row)
        retry = dict(self.journal[0], attempt_id="infrastructure-first", status="infrastructure_failure",
                     correct=None, raw_response=None, invalid_reason=None)
        self.journal[0]["attempt_number"] = 2
        self.journal.insert(0, retry)
        self.save()
        (self.root / "metrics.json").write_text("original primary metrics")
        (self.root / "summary.md").write_text("original primary summary")

    def save(self):
        write_json(self.root / "run_manifest.json", self.manifest)
        write_json(self.root / "dataset.json", self.dataset)
        with (self.root / "generation_attempts.jsonl").open("w", encoding="utf-8") as stream:
            for row in reversed(self.journal):  # selection must not rely on file order
                body = {k: v for k, v in row.items() if k != "record_sha256"}
                stream.write(json.dumps(dict(body, record_sha256=_digest(body))) + "\n")

    def test_report_accuracy_cross_tab_retry_and_preservation(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        metrics, dest = analyze(self.root)
        self.assertEqual(metrics["label"], LABEL)
        self.assertEqual(metrics["completed"], 6)
        self.assertEqual(metrics["journal_attempts"], 7)
        self.assertEqual(metrics["by_form"]["E"]["strict_accuracy"], .5)
        self.assertEqual(metrics["by_form"]["E"]["numeric_accuracy"], 1)
        self.assertEqual(metrics["by_form"]["R"]["strict_accuracy"], 0)
        self.assertEqual(metrics["by_form"]["R"]["numeric_accuracy"], .5)
        self.assertEqual(metrics["by_form"]["C"]["strict_accuracy"], 0)
        self.assertEqual(metrics["by_form"]["C"]["numeric_accuracy"], .5)
        self.assertEqual(metrics["by_form"]["C"]["strict_invalid_by_numeric"],
                         dict(strict_valid=dict(numeric_correct=0, numeric_incorrect=1),
                              strict_invalid=dict(numeric_correct=1, numeric_incorrect=0)))
        self.assertEqual(metrics["by_form"]["C"]["unknown_units"], {"parts": 1})
        self.assertEqual(metrics["by_form"]["E"]["invalid_reason_breakdown"],
                         {"final_not_terminal_line": {"count": 1, "numeric_correct": 1}})
        self.assertEqual(json.loads((dest / "secondary_metrics.json").read_text()), metrics)
        self.assertIn(LABEL, (dest / "secondary_summary.md").read_text())
        self.assertEqual(dest.parent, self.root)
        for name, blob in before.items():
            self.assertEqual((self.root / name).read_bytes(), blob)
            if name in metrics["source_sha256"]:
                self.assertEqual(hashlib.sha256(blob).hexdigest(), metrics["source_sha256"][name])
        first = {p.name: p.read_bytes() for p in dest.iterdir()}
        _, second = analyze(self.root)
        self.assertNotEqual(dest, second)
        self.assertEqual(first, {p.name: p.read_bytes() for p in dest.iterdir()})

    def test_stored_strict_boolean_is_copied_without_rescore(self):
        self.journal[-1]["correct"] = True  # deliberately inconsistent sentinel
        self.save()
        metrics, _ = analyze(self.root)
        self.assertEqual(metrics["by_form"]["C"]["strict_correct"], 1)
        self.assertTrue(next(row for row in metrics["renderings"] if row["rendering_id"] == "FAKE-2-C")["strict_correct"])

    def test_refusal_hit_does_not_veto_but_truncation_fails(self):
        self.journal[-1].update(raw_response="I cannot use that shortcut.\nFINAL: 19", truncated=False, refusal=True)
        self.save()
        metrics, _ = analyze(self.root)
        row = next(row for row in metrics["renderings"] if row["rendering_id"] == "FAKE-2-C")
        self.assertTrue(row["numeric"]["correct"])
        self.assertTrue(row["refusal"])
        self.journal[-1].update(truncated=True)
        self.save()
        metrics, _ = analyze(self.root)
        row = next(row for row in metrics["renderings"] if row["rendering_id"] == "FAKE-2-C")
        self.assertFalse(row["numeric"]["correct"])
        self.assertEqual(row["numeric"]["status"], "truncated")
        self.assertTrue(row["truncated"])

    def assert_rejected_without_folder(self):
        before = set(self.root.iterdir())
        with self.assertRaises(ValueError):
            analyze(self.root)
        self.assertEqual(set(self.root.iterdir()), before)

    def test_reject_incomplete(self):
        self.manifest["status"] = "INCOMPLETE"
        self.save()
        self.assert_rejected_without_folder()

    def test_reject_active_writer(self):
        (self.root / "RUNNING.lock").touch()
        self.assert_rejected_without_folder()

    def test_reject_missing_generated_response(self):
        self.journal[-1]["status"] = "infrastructure_failure"
        self.save()
        self.assert_rejected_without_folder()

    def test_reject_multiple_generated_attempts(self):
        row = dict(self.journal[-1], attempt_id="duplicate-generated", attempt_number=2)
        self.journal.append(row)
        self.save()
        self.assert_rejected_without_folder()

    def test_reject_retry_after_generation(self):
        row = dict(self.journal[-1], attempt_id="forbidden-retry", attempt_number=2, status="infrastructure_failure")
        self.journal.append(row)
        self.save()
        self.assert_rejected_without_folder()

    def test_reject_checksum_corruption(self):
        path = self.root / "generation_attempts.jsonl"
        path.write_text(path.read_text().replace('"FINAL: 20"', '"FINAL: 21"'))
        self.assert_rejected_without_folder()

    def test_reject_dataset_corruption(self):
        write_json(self.root / "dataset.json", dict(self.dataset, unexpected=True))
        self.assert_rejected_without_folder()

    def test_reject_mismatched_gold_identity_scorer(self):
        for field, value in [("gold", dict(self.gold, value="20")), ("form", "E"),
                             ("run_id", "foreign"), ("scorer_version", "1.1.0"), ("correct", "false")]:
            with self.subTest(field=field):
                old = self.journal[-1][field]
                self.journal[-1][field] = value
                self.save()
                self.assert_rejected_without_folder()
                self.journal[-1][field] = old

    def test_cli(self):
        result = subprocess.run([sys.executable, "-B", "-m", "secondary_analysis.report_secondary", str(self.root)],
                                capture_output=True, text=True, check=True)
        self.assertTrue((Path(result.stdout.strip()) / "secondary_metrics.json").is_file())


if __name__ == "__main__":
    unittest.main()
