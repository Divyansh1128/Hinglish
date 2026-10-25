import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "test1_pilot"))

from hinglish_pilot.data import ADJUDICATED_LABEL, DEMO_LABEL, validate  # noqa: E402
from hinglish_pilot.engine import FakeBackend, default_config, run  # noqa: E402
from hinglish_pilot.report import analyze, export  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cohort = load("po_cohort", ROOT / "pilot_original" / "build_cohort.py")
builder = load("po_builder", ROOT / "colab_notebooks" / "build_pilot_original_notebooks.py")
pilot_tests = load("po_test1_pilot_tests", ROOT / "test1_pilot" / "tests" / "test_pilot.py")
pb_builder = load("pb_builder_for_po", ROOT / "colab_notebooks" / "build_pilot_b_notebooks.py")
EXPECTED_COHORT = ["PIL001", "PIL002", "PIL003", "PIL004", "PIL005", "PIL006", "PIL007", "PIL008", "PIL011", "PIL012",
                   "PIL013", "PIL014", "PIL016", "PIL017", "PIL018", "PIL021", "PIL022", "PIL023", "PIL025", "PIL026",
                   "PIL027", "PIL028", "PIL029", "PIL030"]


class PilotOriginalTests(unittest.TestCase):
    def setUp(self):
        self.dataset, self.splits = builder.cohort_inputs()

    def invalid(self, mutate, mode="pilot_adjudicated"):
        dataset = copy.deepcopy(self.dataset)
        mutate(dataset)
        with self.assertRaises(ValueError):
            validate(dataset, self.splits, mode)

    def test_frozen_cohort_validates_and_matches_raw_sources(self):
        frozen = (ROOT / "pilot_original" / "FROZEN.md").read_text()
        for path in (builder.DATASET, builder.SPLITS):
            self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), frozen)
        summary = validate(self.dataset, self.splits, "pilot_adjudicated")
        self.assertEqual((summary["families"], summary["prompts"]), (24, 72))
        self.assertTrue(summary["status"].startswith(ADJUDICATED_LABEL))
        rebuilt, rebuilt_splits, _, _ = cohort.build()
        self.assertEqual((rebuilt, rebuilt_splits), (self.dataset, self.splits), "Frozen cohort is stale: rerun build_cohort.py")
        self.assertEqual([f["family_id"] for f in self.dataset["families"]], EXPECTED_COHORT)
        self.assertEqual(len(self.splits["development_exclusion_ids"]), 90)

    def test_texts_and_gold_unchanged_from_draft(self):
        draft = {f["family_id"]: f for f in json.loads(cohort.DRAFT.read_text())["families"]}
        for family in self.dataset["families"]:
            before = draft[family["family_id"]]
            self.assertEqual({k: v for k, v in before.items() if k not in ("status", "review")},
                             {k: v for k, v in family.items() if k not in ("status", "review")})

    def test_raw_disagreements_preserved_not_required_to_match_gold(self):
        entries = [(f["family_id"], form, r["reviewer_id"], r["forms"][form]) for f in self.dataset["families"]
                   for r in f["review"]["reviewers"] for form in "ERC"]
        mismatched = {(fid, form, rid) for fid, form, rid, e in entries if not e["answer_matches_gold"]}
        self.assertEqual(mismatched, {("PIL001", "R", "R01"), ("PIL011", "R", "R01"), ("PIL011", "C", "R01"),
                                      ("PIL018", "E", "R01"), ("PIL018", "R", "R01"), ("PIL018", "C", "R01")})
        self.assertTrue(any(e["naturalness"] < 4 or e["readability"] < 4 for *_, e in entries))
        self.assertTrue(any(e["disposition"] == "REVISE" for *_, e in entries))

    def test_tampered_text_hash_fails(self):
        def mutate(d):
            d["families"][3]["review"]["reviewers"][1]["forms"]["R"]["text_sha256"] = "0" * 64
        self.invalid(mutate)

        def edit_text(d):
            d["families"][0]["forms"]["C"]["text"] += " Edited."
        self.invalid(edit_text)

    def test_missing_or_duplicate_reviewers_fail(self):
        self.invalid(lambda d: d["families"][0]["review"]["reviewers"].pop())
        self.invalid(lambda d: d["families"][0]["review"].update(reviewers=[]))

        def duplicate(d):
            reviewers = d["families"][0]["review"]["reviewers"]
            reviewers[1]["reviewer_id"] = reviewers[0]["reviewer_id"]
        self.invalid(duplicate)

        def third(d):
            reviewers = d["families"][0]["review"]["reviewers"]
            reviewers.append(dict(copy.deepcopy(reviewers[0]), reviewer_id="R03"))
        self.invalid(third)

    def test_adjudication_rules(self):
        self.invalid(lambda d: d["families"][0]["review"]["adjudication"].update(adjudicator_id="R01"))
        self.invalid(lambda d: d["families"][0]["review"]["adjudication"].update(adjudicator_id="R02"))
        self.invalid(lambda d: d["families"][0]["review"]["adjudication"].update(status="REVISE"))
        self.invalid(lambda d: d["families"][0]["review"]["adjudication"].update(gold_confirmed=False))
        self.invalid(lambda d: d["families"][0]["review"].update(adjudication=None))
        self.invalid(lambda d: d["families"][0]["review"]["reviewers"][0].update(independent=False))
        self.invalid(lambda d: d["families"][0]["review"]["reviewers"][0]["forms"]["E"].update(answer_matches_gold="yes"))
        self.invalid(lambda d: d["families"][0]["forms"]["C"].update(switching_roles=[]))
        self.invalid(lambda d: d["families"][0].update(split_role="PILOT_B_EVAL"))

    def test_other_modes_unaffected(self):
        for mode in ("demo", "reviewed", "pilot_b"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate(self.dataset, self.splits, mode)
        pb_dataset, pb_splits = pb_builder.pilot_b_inputs()
        self.assertEqual(validate(pb_dataset, pb_splits, "pilot_b")["prompts"], 210)
        with self.assertRaises(ValueError):
            validate(pb_dataset, pb_splits, "pilot_adjudicated")
        self.assertEqual(validate(*pilot_tests.fixture(), "demo")["status"], DEMO_LABEL)
        reviewed = validate(*pilot_tests.reviewed_fixture(), "reviewed")
        self.assertEqual((reviewed["prompts"], reviewed["status"]),
                         (90, "REVIEW METADATA PASSED — human judgments not machine verified"))
        with self.assertRaises(ValueError):
            validate(*pilot_tests.reviewed_fixture(), "pilot_adjudicated")

    def test_pipeline_runs_end_to_end_with_fake_backend(self):
        config = default_config("pilot_adjudicated", "Qwen/Qwen3-4B")
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)

        class LabelledFake(FakeBackend):
            metadata = dict(FakeBackend.metadata, backend="huggingface")  # engine forbids 'fake' outside demo

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run(Path(directory) / "fake", self.dataset, self.splits, config, FakeBackend())
            manifest = run(Path(directory) / "po", self.dataset, self.splits, config, LabelledFake())
            self.assertEqual((manifest["status"], manifest["expected"]), ("COMPLETE", 72))
            self.assertEqual(manifest["label"], ADJUDICATED_LABEL)
            metrics, _ = analyze(Path(directory) / "po")
            self.assertEqual(metrics["accuracy"]["E"]["denominator"], 24)
            self.assertTrue(export(Path(directory) / "po").is_file())

    def test_built_notebooks_are_current_and_compile(self):
        digest = hashlib.sha256(builder.payload()).hexdigest()
        for model_id, name in builder.NOTEBOOKS.items():
            with self.subTest(model=model_id):
                notebook = json.loads((builder.OUT_DIR / name).read_text(encoding="utf-8"))
                sources = [cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "code"]
                for index, source in enumerate(sources):
                    compile(source, f"cell-{index}", "exec")
                self.assertIn(digest, sources[0], "Notebook is stale: rerun build_pilot_original_notebooks.py")
                self.assertIn(f"MODEL_ID = {model_id!r}", sources[0])
                self.assertIn("RUN_NAME = 'pilotorig-", sources[0])
                self.assertIn("'pilot_adjudicated'", sources[0])
                self.assertIn(f"PilotOrig_results_{model_id.split('/')[-1]}.zip", sources[-1])
                gated = model_id in builder.GATED
                self.assertIn(f"if {gated!r}:", sources[0])
                for marker in ("login(token=token", "auth_check(MODEL_ID", "while not token.startswith('hf_')"):
                    self.assertIn(marker, sources[0])


if __name__ == "__main__":
    unittest.main()
