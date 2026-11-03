"""The Phase-2 notebooks: current, compilable, self-contained, data-separated, and the FinalTest gate refuses."""
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

from t4_smoke import phase2_eval as pe
from t4_smoke import train_phase2 as tp
from t4_smoke import train_smoke as ts

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "colab_notebooks"))
import build_phase2_notebooks as builder  # noqa: E402


def code_cells(text):
    return [cell["source"] for cell in json.loads(text)["cells"] if cell["cell_type"] == "code"]


def payload_of(text):
    source = code_cells(text)[0]
    blob = base64.b64decode(re.search(r"b64decode\('([^']+)'\)", source).group(1))
    assert hashlib.sha256(blob).hexdigest() in source
    return zipfile.ZipFile(io.BytesIO(blob))


def fake_frozen():
    adapters = [{"arm": arm, "seed": seed, "attempt": 1, "adapter_model_sha256": hashlib.sha256(f"w{arm}{seed}".encode()).hexdigest(),
                 "adapter_config_sha256": hashlib.sha256(json.dumps({"peft_type": "LORA"}).encode()).hexdigest()}
                for seed in (11, 22, 33) for arm in tp.ARMS]
    frozen = {"schema": pe.FROZEN_SCHEMA, "base_model": pe.MODEL_ID, "base_revision": pe.MODEL_REVISION, "adapters": adapters}
    return "# Adapters frozen (TEST FIXTURE)\n\n```json\n" + json.dumps(frozen, indent=1) + "\n```\n", frozen


class BuiltNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = {"baseline": builder.render_baseline(), "train": builder.render_train()}

    def test_committed_notebooks_are_current_and_deterministic(self):
        for kind, text in self.texts.items():
            with self.subTest(kind=kind):
                path = builder.OUT_DIR / builder.NAMES[kind]
                self.assertEqual(path.read_text(encoding="utf-8"), text, "Rebuild: python3 -B colab_notebooks/build_phase2_notebooks.py")
        self.assertEqual(builder.render_train(), self.texts["train"])

    def test_cells_compile_without_shell_magics(self):
        for kind, text in self.texts.items():
            for index, source in enumerate(code_cells(text)):
                with self.subTest(kind=kind, cell=index):
                    compile(source, f"{kind}-{index}", "exec")
                    self.assertNotRegex(source, r"(?m)^\s*[!%]")

    def test_payloads_are_self_contained_current_and_never_hold_final_test(self):
        for kind, text in self.texts.items():
            with self.subTest(kind=kind), payload_of(text) as archive:
                names = archive.namelist()
                for name in names:
                    if name.endswith(".py"):
                        source = {"hinglish_pilot": ROOT / "test1_pilot" / name, "secondary_analysis": ROOT / name,
                                  "t4_smoke": ROOT / name}[name.split("/")[0]]
                        self.assertEqual(archive.read(name), source.read_bytes(), name)
                self.assertNotIn("inputs/final_test.v3.json", names)
                self.assertEqual(archive.read("inputs/dev.v2.json"), (ROOT / "phase2" / "dev.v2.json").read_bytes())
                for name in names:
                    if name.startswith("inputs/"):
                        self.assertNotIn(b"FT0", archive.read(name), name)
                requirements = archive.read("requirements-phase2.txt").decode()
                for package, version in ts.PINS.items():
                    self.assertIn(f"{package}=={version}\n", requirements)
                self.assertNotIn("torch==", requirements)
                self.assertEqual(("inputs/phase2_train.json" in names), kind == "train")
        with payload_of(self.texts["train"]) as archive:
            self.assertEqual(json.loads(archive.read("inputs/phase2_train.json")), tp.phase2_dataset(ROOT))

    def test_notebooks_check_t4_use_drive_and_zip_with_checksums(self):
        for kind, text in self.texts.items():
            source = "\n".join(code_cells(text))
            for needle in ("'T4' in gpu", "requirements-phase2.txt", "USE_DRIVE = True", "SHA256SUMS.txt", "files.download",
                           "process.kill()", "attempts.jsonl"):
                self.assertIn(needle, source, kind)
            self.assertEqual(json.loads(text)["metadata"]["accelerator"], "GPU")
        baseline = "\n".join(code_cells(self.texts["baseline"]))
        self.assertIn("'evaluate', '--split', 'dev'", baseline)
        self.assertIn("CEILING FLAG (C >= 38/40)", baseline)

    def test_train_notebook_settings_and_section_10(self):
        cells = code_cells(self.texts["train"])
        self.assertTrue(cells[0].startswith("import os"))
        settings = cells[0].split("os.environ")[0]
        for needle in ("ARM = 'EC'", "SEED = 11", "RESUME_AFTER_DISCONNECT = False", "(11, 22, 33, 44, 55)"):
            self.assertIn(needle, settings)
        source = "\n".join(cells)
        for needle in ("'train_phase2.py'", "'--resume'", "len(attempts) < 2", "reserve", "'--adapter-dir'", "'dev_eval'"):
            self.assertIn(needle, source)
        markdown = json.loads(self.texts["train"])["cells"][0]["source"]
        self.assertIn("§10", markdown)
        self.assertIn("fresh attempt from scratch", markdown)

    def test_final_test_is_skipped_until_the_freeze_manifest_exists(self):
        prereg, reason = builder.final_test_inputs()
        self.assertEqual(hashlib.sha256((ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()).hexdigest(),
                         builder.PREREGISTRATION_SHA256)
        if (ROOT / "phase2" / "ADAPTERS_FROZEN.md").exists():
            self.assertIsNotNone(prereg, reason)
            self.assertEqual((builder.OUT_DIR / builder.NAMES["final_test"]).read_text(encoding="utf-8"),
                             builder.render_final_test(prereg, reason))
        else:
            self.assertIsNone(prereg)
            self.assertIn("ADAPTERS_FROZEN.md", reason)


class FinalTestGateNotebookTests(unittest.TestCase):
    """Execute the FinalTest notebook's setup and gate cells (model-free) in a fresh interpreter."""

    @classmethod
    def setUpClass(cls):
        cls.prereg = (ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()
        cls.frozen_text, cls.frozen = fake_frozen()
        cls.text = builder.render_final_test(cls.prereg, cls.frozen_text)

    def run_gate(self, text, adapters=()):
        cells = code_cells(text)
        self.assertIn("GATE", cells[1])
        self.assertIn("assert GATE_PASSED", cells[3])  # evaluations refuse to start without the gate
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            work = folder / "work"
            train = work / "hinglish_phase2" / "runs" / "train"
            for adapter, changes in adapters:
                path = pe.attempt_dir(train, adapter["arm"], adapter["seed"], adapter["attempt"])
                (path / "final_adapter").mkdir(parents=True)
                (path / "final_adapter" / "adapter_model.safetensors").write_text(f"w{adapter['arm']}{adapter['seed']}")
                (path / "final_adapter" / "adapter_config.json").write_text(json.dumps({"peft_type": "LORA"}))
                record = dict(adapter, status="COMPLETE", updates=60, resumed=False, recipe_sha256=ts.digest(tp.RECIPE),
                              base_revision=pe.MODEL_REVISION, initial_adapter_sha256=f"i{adapter['seed']}",
                              order_sha256=f"o{adapter['seed']}", data_sha256=tp.phase2_dataset(ROOT)["families_sha256"])
                record.update(changes)
                (path / "final_adapter.json").write_text(json.dumps(record))
            (folder / "cells.py").write_text(cells[0] + "\n" + cells[1])
            env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
            return subprocess.run([sys.executable, "-I", str(folder / "cells.py")], cwd=work if work.exists() else self.mkdir(work),
                                  env=env, capture_output=True, text=True, timeout=120)

    @staticmethod
    def mkdir(path):
        path.mkdir(parents=True)
        return path

    def test_refuses_without_adapters(self):
        result = self.run_gate(self.text)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FINAL_TEST gate REFUSED", result.stderr)
        self.assertNotIn("GATE PASSED", result.stdout)

    def test_refuses_with_a_wrong_hash_or_a_resumed_run(self):
        adapters = [(a, {}) for a in self.frozen["adapters"]]
        adapters[4] = (adapters[4][0], {"adapter_model_sha256": "0" * 64})
        result = self.run_gate(self.text, adapters)
        self.assertIn("recorded hashes check failed", result.stderr)
        adapters[4] = (adapters[4][0], {"resumed": True})
        result = self.run_gate(self.text, adapters)
        self.assertIn("not resumed", result.stderr)

    def test_refuses_when_the_preregistration_hash_differs(self):
        text = builder.render_final_test(self.prereg, self.frozen_text, prereg_sha256="0" * 64)
        result = self.run_gate(text, [(a, {}) for a in self.frozen["adapters"]])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FINAL_TEST refused", result.stderr)

    def test_passes_with_all_nine_frozen_adapters(self):
        result = self.run_gate(self.text, [(a, {}) for a in self.frozen["adapters"]])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GATE PASSED", result.stdout)

    def test_final_test_notebook_compiles_and_embeds_final_test_and_preregistration(self):
        for index, source in enumerate(code_cells(self.text)):
            compile(source, f"final-{index}", "exec")
        with payload_of(self.text) as archive:
            self.assertEqual(archive.read("inputs/final_test.v3.json"), (ROOT / "phase2" / "final_test.v3.json").read_bytes())
            self.assertEqual(archive.read("inputs/PREREGISTRATION.md"), self.prereg)
            self.assertNotIn("inputs/phase2_train.json", archive.namelist())
        self.assertIn(builder.PREREGISTRATION_SHA256, code_cells(self.text)[1])


if __name__ == "__main__":
    unittest.main()
