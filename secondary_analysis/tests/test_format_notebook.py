import hashlib
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
from secondary_analysis import build_format_notebook as builder  # noqa: E402
from secondary_analysis.report_secondary import analyze as analyze_secondary  # noqa: E402


class FormatNotebookTests(unittest.TestCase):
    def test_parts_cover_all_fixtures_and_pass_demo_validation(self):
        parts = builder.demo_parts()
        self.assertEqual([name for name, _, _ in parts], ["fmt2-part-a", "fmt2-part-b"])
        ids = [f["family_id"] for _, dataset, _ in parts for f in dataset["families"]]
        self.assertEqual(ids, [f"FMT2-{i:03d}" for i in range(1, 13)])
        for _, dataset, splits in parts:
            self.assertEqual(validate(dataset, splits, "demo")["prompts"], 18)
            self.assertTrue(all(f["review"] == {"reviewers": [], "adjudication": None} for f in dataset["families"]))

    def test_pipeline_runs_end_to_end_with_fake_backend(self):
        config = default_config("demo")
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
        with tempfile.TemporaryDirectory() as directory:
            for name, dataset, splits in builder.demo_parts():
                root = Path(directory) / name
                manifest = run(root, dataset, splits, config, FakeBackend())
                self.assertEqual(manifest["status"], "COMPLETE")
                analyze(root)
                metrics, folder = analyze_secondary(root)
                self.assertTrue((folder / "secondary_summary.md").is_file())
                self.assertEqual(sum(form["denominator"] for form in metrics["by_form"].values()), 18)
                self.assertTrue(export(root).is_file())

    def test_built_notebooks_are_current_and_compile(self):
        digest = hashlib.sha256(builder.payload()).hexdigest()
        for model_id, name in builder.NOTEBOOKS.items():
            with self.subTest(model=model_id):
                notebook = json.loads((builder.OUT_DIR / name).read_text(encoding="utf-8"))
                sources = [cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "code"]
                for index, source in enumerate(sources):
                    compile(source, f"cell-{index}", "exec")
                self.assertIn(digest, sources[0], "Notebook is stale: rerun build_format_notebook.py")
                self.assertIn(f"MODEL_ID = {model_id!r}", sources[0])

    def test_second_backbone_config_runs_with_fake_backend(self):
        config = default_config("demo", "microsoft/Phi-4-mini-instruct")
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
        name, dataset, splits = builder.demo_parts()[0]
        with tempfile.TemporaryDirectory() as directory:
            manifest = run(Path(directory) / name, dataset, splits, config, FakeBackend())
            self.assertEqual(manifest["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
