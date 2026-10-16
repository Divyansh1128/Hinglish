import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "test1_pilot"))

from hinglish_pilot.data import validate  # noqa: E402
from hinglish_pilot.engine import FakeBackend, default_config, run  # noqa: E402
from hinglish_pilot.report import analyze, export  # noqa: E402

spec = importlib.util.spec_from_file_location("pb_builder", ROOT / "colab_notebooks" / "build_pilot_b_notebooks.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PilotBNotebookTests(unittest.TestCase):
    def test_frozen_data_unchanged_and_valid_in_pilot_b_mode(self):
        frozen = (ROOT / "pilot_b" / "FROZEN.md").read_text()
        self.assertIn(hashlib.sha256(builder.DATA.read_bytes()).hexdigest(), frozen)
        dataset, splits = builder.pilot_b_inputs()
        self.assertEqual(validate(dataset, splits, "pilot_b")["prompts"], 210)
        original = json.loads(builder.DATA.read_text())
        for before, after in zip(original, dataset["families"]):
            self.assertEqual({k: v for k, v in before.items() if k != "review"},
                             {k: v for k, v in after.items() if k != "review"})

    def test_pilot_b_mode_rejects_missing_reviewer_and_wrong_mode(self):
        dataset, splits = builder.pilot_b_inputs()
        bad = json.loads(json.dumps(dataset))
        bad["families"][0]["review"] = {"reviewers": [], "adjudication": None}
        with self.assertRaises(ValueError):
            validate(bad, splits, "pilot_b")
        with self.assertRaises(ValueError):
            validate(dataset, splits, "reviewed")

    def test_pipeline_runs_end_to_end_with_fake_backend(self):
        dataset, splits = builder.pilot_b_inputs()
        config = default_config("pilot_b", "Qwen/Qwen3-4B")
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)

        class LabelledFake(FakeBackend):
            metadata = dict(FakeBackend.metadata, backend="huggingface")  # engine forbids 'fake' outside demo

        with tempfile.TemporaryDirectory() as directory:
            manifest = run(Path(directory) / "pb", dataset, splits, config, LabelledFake())
            self.assertEqual((manifest["status"], manifest["expected"]), ("COMPLETE", 210))
            self.assertTrue(manifest["label"].startswith("PILOT-B"))
            metrics, _ = analyze(Path(directory) / "pb")
            self.assertEqual(metrics["accuracy"]["E"]["denominator"], 70)
            self.assertTrue(export(Path(directory) / "pb").is_file())

    def test_built_notebooks_are_current_and_compile(self):
        digest = hashlib.sha256(builder.payload()).hexdigest()
        for model_id, name in builder.NOTEBOOKS.items():
            with self.subTest(model=model_id):
                notebook = json.loads((builder.OUT_DIR / name).read_text(encoding="utf-8"))
                sources = [cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "code"]
                for index, source in enumerate(sources):
                    compile(source, f"cell-{index}", "exec")
                self.assertIn(digest, sources[0], "Notebook is stale: rerun build_pilot_b_notebooks.py")
                self.assertIn(f"MODEL_ID = {model_id!r}", sources[0])


if __name__ == "__main__":
    unittest.main()
