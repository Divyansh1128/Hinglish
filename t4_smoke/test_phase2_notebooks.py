"""The Phase-2 notebooks: current, compilable, self-contained, data-separated, manifest-verified (Amendment 1 item 14),
attempt-logged (item 11), sealed and gated FinalTest (items 12-14), no second backbone (item 15)."""
import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from t4_smoke import phase2_eval as pe
from t4_smoke import test_phase2_eval as fixtures
from t4_smoke import train_phase2 as tp
from t4_smoke import train_smoke as ts

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "colab_notebooks"))
import build_phase2_notebooks as builder  # noqa: E402

OLD_PREREGISTRATION_SHA256 = "74be23282ce9e53e3a69456bebf89f9cd71d3859b80090692e4548ef34182840"


def code_cells(text):
    return [cell["source"] for cell in json.loads(text)["cells"] if cell["cell_type"] == "code"]


def payload_of(text):
    source = code_cells(text)[0]
    blob = base64.b64decode(re.search(r"b64decode\('([^']+)'\)", source).group(1))
    assert hashlib.sha256(blob).hexdigest() in source
    return zipfile.ZipFile(io.BytesIO(blob))


def run_python(source, cwd, timeout=180):
    path = Path(cwd).parent / "cells.py"
    path.write_text(source)
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    return subprocess.run([sys.executable, "-I", str(path)], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


class BuiltNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = builder.implementation_manifest()
        cls.texts = {"baseline": builder.render_baseline(cls.manifest), "train": builder.render_train(cls.manifest)}

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
                for member, source in builder.payload_sources(kind).items():
                    self.assertEqual(archive.read(member), (ROOT / source).read_bytes(), member)
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
                self.assertEqual(("inputs/EXPOSURE_ORDER.json" in names), kind == "train")
        with payload_of(self.texts["train"]) as archive:
            self.assertEqual(json.loads(archive.read("inputs/phase2_train.json")), tp.phase2_dataset(ROOT))
            self.assertEqual(archive.read("inputs/EXPOSURE_ORDER.json"), (ROOT / tp.EXPOSURE_ORDER_PATH).read_bytes())

    def test_notebooks_check_t4_use_drive_and_zip_with_checksums(self):
        for kind, text in self.texts.items():
            source = "\n".join(code_cells(text))
            for needle in ("'T4' in gpu", "requirements-phase2.txt", "USE_DRIVE = True", "SHA256SUMS.txt", "files.download",
                           "process.kill()", "attempts.jsonl", "HUB_CHECK", "STACK_MISMATCHES"):
                self.assertIn(needle, source, kind)
            self.assertEqual(json.loads(text)["metadata"]["accelerator"], "GPU")

    def test_baseline_prints_the_ceiling_risk_proxy_with_wilson_interval(self):
        """Amendment 1 item 7."""
        baseline = "\n".join(code_cells(self.texts["baseline"]))
        self.assertIn("'evaluate', '--split', 'dev'", baseline)
        self.assertIn("flag['wilson95']", baseline)
        self.assertIn("{flag['k']}/{flag['n']}", baseline)
        self.assertNotIn("CEILING FLAG", baseline)
        self.assertIn("high unchanged-DEV accuracy (ceiling-risk proxy)", json.loads(self.texts["baseline"])["cells"][0]["source"])
        namespace = {"json": json, "Path": Path}
        cell = code_cells(self.texts["baseline"])[2]
        flag = pe.ceiling_flag({"accuracy": {"C": {"correct": 39, "denominator": 40}}})
        with tempfile.TemporaryDirectory() as folder:
            store = Path(folder)
            (store / "baseline_dev").mkdir()
            (store / "baseline_dev" / "base_ceiling_flag.json").write_text(json.dumps(flag))
            namespace.update(STORE=store, INPUTS=store, step=lambda *args: 0)
            with mock.patch("sys.stdout", io.StringIO()) as out:
                exec(cell, namespace)
        self.assertIn("high unchanged-DEV accuracy (ceiling-risk proxy): FIRES — unchanged DEV C 39/40 (Wilson 95%", out.getvalue())

    def test_train_notebook_settings_and_item_11(self):
        cells = code_cells(self.texts["train"])
        self.assertTrue(cells[0].startswith("import os"))
        settings = cells[0].split("os.environ")[0]
        for needle in ("ARM = 'EC'", "SLOT = 11", "RESUME_AFTER_DISCONNECT = False", "(11, 22, 33)"):
            self.assertIn(needle, settings)
        self.assertNotIn("SEED =", settings)
        source = "\n".join(cells)
        for needle in ("'train_phase2.py'", "'--resume'", "tp.next_action", "tp.reconcile", "tp.log_event", "tp.attempt_outcome",
                       "'--exposure-order'", "'--implementation-manifest-sha256'", "tp.HALT_MESSAGE", "'--slot'", "'dev_eval'",
                       "never overwritten"):
            self.assertIn(needle, source)
        markdown = json.loads(self.texts["train"])["cells"][0]["source"]
        for needle in ("the study halts", "60 successful optimizer steps", "44, then 55", "never valid", "ATTEMPT_LOG.jsonl"):
            self.assertIn(needle, markdown)

    def test_no_second_backbone_in_any_phase2_notebook(self):
        """Amendment 1 item 15."""
        for kind, text in self.texts.items():
            self.assertNotIn("llama", text.lower(), kind)
            self.assertNotIn("MODEL_ID =", text, kind)
        self.assertNotIn("llama", (ROOT / "colab_notebooks" / "build_phase2_notebooks.py").read_text().lower())

    def test_current_preregistration_hash_with_amendment_1(self):
        digest = hashlib.sha256((ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()).hexdigest()
        self.assertEqual(builder.PREREGISTRATION_SHA256, digest)
        self.assertNotEqual(builder.PREREGISTRATION_SHA256, OLD_PREREGISTRATION_SHA256)
        self.assertIn("## Amendment 1", (ROOT / "phase2" / "PREREGISTRATION.md").read_text())
        for kind, text in self.texts.items():
            self.assertIn(digest, code_cells(text)[0], kind)
            self.assertNotIn(OLD_PREREGISTRATION_SHA256, text, kind)

    def test_final_test_is_skipped_until_the_freeze_manifest_exists(self):
        prereg, reason = builder.final_test_inputs()
        if (ROOT / "phase2" / "ADAPTERS_FROZEN.md").exists():
            self.assertIsNotNone(prereg, reason)
            self.assertEqual((builder.OUT_DIR / builder.NAMES["final_test"]).read_text(encoding="utf-8"),
                             builder.render_final_test(prereg, reason))
        else:
            self.assertIsNone(prereg)
            self.assertIn("ADAPTERS_FROZEN.md", reason)


class ManifestEmbeddingTests(unittest.TestCase):
    """Amendment 1 item 14: the notebooks embed the manifest and refuse to run if the code differs."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = builder.implementation_manifest()

    def run_setup(self, text):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "work"
            work.mkdir()
            return run_python(code_cells(text)[0], work)

    def test_manifest_is_current_and_embedded(self):
        module = builder.manifest_module()
        self.assertEqual(module.main(["--check"]), 0)
        text, digest = self.manifest
        document = module.parse(text)
        for kind in ("baseline", "train"):
            notebook = getattr(builder, f"render_{kind}")(self.manifest)
            setup = code_cells(notebook)[0]
            self.assertIn(repr(digest), setup)
            self.assertIn(base64.b64encode(text.encode()).decode(), setup)
            self.assertEqual(document["notebook_payloads"][builder.NAMES[kind]], hashlib.sha256(builder.payload(kind)).hexdigest())
            self.assertIn(digest, json.loads(notebook)["cells"][0]["source"])
            result = self.run_setup(notebook)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Implementation manifest verified: " + digest, result.stdout)

    def test_refuses_when_code_differs_from_the_manifest(self):
        text, _ = self.manifest
        document = builder.manifest_module().parse(text)
        changed = copy_document = json.loads(json.dumps(document))
        changed["files"]["t4_smoke/train_phase2.py"] = "0" * 64
        tampered = text.replace(json.dumps(document, indent=1, ensure_ascii=False), json.dumps(copy_document, indent=1, ensure_ascii=False))
        self.assertNotEqual(tampered, text)
        result = self.run_setup(builder.render_train((tampered, hashlib.sha256(tampered.encode()).hexdigest())))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("differs from the implementation manifest: refusing to run", result.stderr)
        payload = json.loads(json.dumps(document))
        payload["notebook_payloads"][builder.NAMES["baseline"]] = "0" * 64
        tampered = text.replace(json.dumps(document, indent=1, ensure_ascii=False), json.dumps(payload, indent=1, ensure_ascii=False))
        result = self.run_setup(builder.render_baseline((tampered, hashlib.sha256(tampered.encode()).hexdigest())))
        self.assertIn("Notebook payload differs from the implementation manifest", result.stderr)
        result = self.run_setup(builder.render_baseline((text, "0" * 64)))
        self.assertIn("IMPLEMENTATION_MANIFEST.md was changed", result.stderr)

    def test_manifest_covers_every_item_14_component(self):
        document = builder.manifest_module().parse(self.manifest[0])
        files = document["files"]
        for path in ("t4_smoke/train_phase2.py", "t4_smoke/train_smoke.py", "t4_smoke/labels.py", "t4_smoke/protocol.py",
                     "t4_smoke/phase2_eval.py", "test1_pilot/hinglish_pilot/engine.py", "test1_pilot/hinglish_pilot/hf_backend.py",
                     "test1_pilot/hinglish_pilot/scorer_v1.py", "secondary_analysis/numeric_endpoint.py",
                     "secondary_analysis/numeric_literal_v2.py", "colab_notebooks/build_phase2_notebooks.py",
                     "phase2/build_implementation_manifest.py", "phase2/EXPOSURE_ORDER.json"):
            self.assertEqual(files[path], hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), path)
        for path in sorted((ROOT / "phase2_analysis").glob("*.py")):
            self.assertEqual(files[f"phase2_analysis/{path.name}"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(files["test1_pilot/hinglish_pilot/scorer_v1.py"], "c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc")
        self.assertEqual(files["secondary_analysis/numeric_endpoint.py"], "ce70aefd1f4c03ffe80bbd06d4df025abe92fc0865732b6d2e6db13504ed883f")
        self.assertEqual(document["preregistration"]["sha256"], builder.PREREGISTRATION_SHA256)
        self.assertEqual(document["model"]["revision"], ts.MODEL_REVISION)
        self.assertEqual(set(document["model"]["hub_files"]), {"config.json", "generation_config.json", "tokenizer.json",
                                                                "tokenizer_config.json", "vocab.json", "merges.txt", "model.safetensors.index.json"})
        self.assertIn("digest", document["model"]["chat_template"])
        self.assertEqual(document["eos_stopping"]["generation_eos_token_id"], [151645, 151643])
        self.assertEqual(set(document["dtype_preparation"]), {"train", "evaluation", "difference"})
        self.assertEqual(document["dependencies"]["train"], ts.PINS)
        self.assertEqual(document["generation_config"]["decoding"]["max_new_tokens"], 1024)
        self.assertEqual(document["training"]["grad_scaler"], tp.SCALER)
        self.assertEqual(document["exposure_order"]["sha256"], files["phase2/EXPOSURE_ORDER.json"])

    def test_check_mode_detects_a_stale_manifest(self):
        module = builder.manifest_module()
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "IMPLEMENTATION_MANIFEST.md"
            text, _ = self.manifest
            target.write_text(text.replace(hashlib.sha256((ROOT / "t4_smoke" / "labels.py").read_bytes()).hexdigest(), "0" * 64))
            with mock.patch.object(module, "MANIFEST", target), mock.patch("sys.stdout", io.StringIO()) as out:
                self.assertEqual(module.main(["--check"]), 1)
            self.assertIn("STALE", out.getvalue())
            self.assertIn("t4_smoke/labels.py", out.getvalue())
            target.unlink()
            with mock.patch.object(module, "MANIFEST", target), mock.patch("sys.stdout", io.StringIO()) as out:
                self.assertEqual(module.main(["--check"]), 1)
            self.assertIn("MISSING", out.getvalue())


class TrainNotebookFlowTests(unittest.TestCase):
    """Execute the Train notebook's setup and control cells with a stub training step (no GPU)."""

    @classmethod
    def setUpClass(cls):
        cls.text = builder.render_train()

    def run_control(self, work, outcomes, arm="EC", slot=11, resume=False):
        cells = code_cells(self.text)
        settings = cells[0].replace("ARM = 'EC'", f"ARM = {arm!r}").replace("SLOT = 11", f"SLOT = {slot}")
        if resume:
            settings = settings.replace("RESUME_AFTER_DISCONNECT = False", "RESUME_AFTER_DISCONNECT = True")
        stub = textwrap.dedent(f'''
            STACK_MISMATCHES = []
            OUTCOMES = {outcomes!r}
            def step(log_dir, script, *args):
                outcome = OUTCOMES.pop(0)
                out = Path(args[args.index('--out') + 1])
                out.mkdir(parents=True, exist_ok=True)
                status = 'COMPLETE' if outcome == 'valid' else ('STARTED' if outcome == 'disconnect' else 'FAILED')
                (out / 'train_report.json').write_text(json.dumps({{'status': status, 'failure_class': None if status != 'FAILED' else outcome,
                                                                   'error': 'Traceback\\nX: ' + outcome}}))
                if outcome == 'disconnect':
                    (out / 'checkpoint').mkdir(exist_ok=True)
                if outcome == 'valid':
                    (out / 'final_adapter.json').write_text(json.dumps({{'status': 'COMPLETE', 'updates': 60, 'arm': ARM, 'slot': SLOT,
                        'seed': int(args[args.index('--seed') + 1]), 'attempt': int(args[args.index('--attempt') + 1]),
                        'steps': {{'windows': 60, 'attempted': 60, 'successful': 60, 'cursor': 960}}, 'scaler_skips': 0,
                        'saved_parameters_finite': True, 'resumed': '--resume' in args, 'valid_for_gate': '--resume' not in args,
                        'adapter_model_sha256': 'a', 'adapter_config_sha256': 'b', 'initial_adapter_sha256': 'i', 'order_sha256': 'o'}}))
                return 0 if outcome == 'valid' else 1
        ''')
        return run_python(settings + "\n" + stub + "\n" + cells[2], work)

    def test_attempt_log_retry_reserve_and_halt(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "work"
            work.mkdir()
            log = work / "hinglish_phase2" / "runs" / "train" / tp.ATTEMPT_LOG
            result = self.run_control(work, ["infrastructure"])
            self.assertIn("Infrastructure failure", result.stderr)
            result = self.run_control(work, ["disconnect"])  # second attempt: from scratch, then a disconnect
            self.assertIn("from-scratch retry", result.stdout)
            current = tp.plan(tp.read_log(log))
            self.assertEqual(current["slots"][11]["chain"], [11, 44])
            result = self.run_control(work, ["valid"], arm="EE")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("EE seed 44 (slot 11, reserve): attempt 1", result.stdout)
            result = self.run_control(work, [], arm="EE")
            self.assertIn("Already trained (valid): EE seed 44 attempt 1", result.stdout)
            self.assertTrue((tp.attempt_dir(log.parent, "EC", 11, 1) / "train_report.json").exists())  # never overwritten
            result = self.run_control(work, ["numerical"], arm="ER")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NUMERICAL FAILURE", result.stdout)
            self.assertIn("THE STUDY HALTS", result.stdout)
            for arm, slot in (("EC", 11), ("EE", 22)):
                result = self.run_control(work, ["valid"], arm=arm, slot=slot)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("StudyHalted", result.stderr)
            outcomes = [(e["event"], e["arm"], e["seed"], e.get("outcome")) for e in tp.read_log(log)]
            self.assertEqual(outcomes, [("start", "EC", 11, None), ("finish", "EC", 11, "infrastructure"),
                                        ("start", "EC", 11, None), ("finish", "EC", 11, "infrastructure"),
                                        ("start", "EE", 44, None), ("finish", "EE", 44, "valid"),
                                        ("start", "ER", 44, None), ("finish", "ER", 44, "numerical")])

    def test_resume_is_logged_and_never_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "work"
            work.mkdir()
            log = work / "hinglish_phase2" / "runs" / "train" / tp.ATTEMPT_LOG
            self.run_control(work, ["disconnect"])
            result = self.run_control(work, ["valid"], resume=True)
            self.assertIn("RESUMING attempt 1", result.stdout)
            self.assertIn("never valid", result.stderr)
            current = tp.plan(tp.read_log(log))
            self.assertEqual(current["attempts"]["EC-s11"][0]["resume_outcome"], "resumed_invalid")
            self.assertEqual(tp.next_action(current, "EC", 11)["attempt"], 2)


class FinalTestGateNotebookTests(unittest.TestCase):
    """Execute the FinalTest notebook's setup and gate cells (model-free) in a fresh interpreter."""

    @classmethod
    def setUpClass(cls):
        cls.prereg = (ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()
        cls.manifest = builder.implementation_manifest()
        cls.store = tempfile.TemporaryDirectory()
        cls.trees = {}
        with mock.patch.object(fixtures, "MANIFEST_SHA", cls.manifest[1]), \
                mock.patch.object(fixtures, "DATA_SHA", tp.phase2_dataset(ROOT)["families_sha256"]):
            for name, slots in (("full", (11, 22, 33)), ("reduced", (11, 22))):
                train = Path(cls.store.name) / name
                fixtures.complete_slots(train, slots=slots)
                if name == "reduced":
                    fixtures.exhaust_slot(train, 33)
                frozen = pe.freeze_manifest(train)
                cls.trees[name] = (train, frozen, "# Adapters frozen (TEST FIXTURE)\n\n```json\n" + json.dumps(frozen, indent=1) + "\n```\n")
        cls.text = builder.render_final_test(cls.prereg, cls.trees["full"][2])

    @classmethod
    def tearDownClass(cls):
        cls.store.cleanup()

    def run_gate(self, text, tree="full", mutate=None):
        cells = code_cells(text)
        self.assertIn("GATE", cells[1])
        self.assertIn("assert GATE_PASSED", cells[3])  # evaluations refuse to start without the gate
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "work"
            work.mkdir()
            if tree is not None:
                shutil.copytree(self.trees[tree][0], work / "hinglish_phase2" / "runs" / "train")
                if mutate:
                    mutate(work / "hinglish_phase2" / "runs" / "train")
            return run_python(cells[0] + "\n" + cells[1], work)

    def test_refuses_without_adapters(self):
        result = self.run_gate(self.text, tree=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FINAL_TEST gate REFUSED", result.stderr)
        self.assertNotIn("GATE PASSED", result.stdout)

    def test_refuses_with_a_wrong_hash_or_a_resumed_run(self):
        def tamper(train):
            (pe.attempt_dir(train, "ER", 22, 1) / "final_adapter" / "adapter_model.safetensors").write_text("tampered")

        result = self.run_gate(self.text, mutate=tamper)
        self.assertIn("ER-s22 attempt 1: files match the frozen hashes check failed", result.stderr)

        def resumed(train):
            path = pe.attempt_dir(train, "EC", 33, 1) / "final_adapter.json"
            record = json.loads(path.read_text())
            record.update(resumed=True, valid_for_gate=False)
            path.write_text(json.dumps(record))

        result = self.run_gate(self.text, mutate=resumed)
        self.assertIn("EC-s33 attempt 1: valid run", result.stderr)

    def test_refuses_when_the_preregistration_hash_differs(self):
        for digest in ("0" * 64, OLD_PREREGISTRATION_SHA256):
            text = builder.render_final_test(self.prereg, self.trees["full"][2], prereg_sha256=digest)
            result = self.run_gate(text)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refus", result.stderr)

    def test_refuses_adapters_frozen_under_another_manifest(self):
        frozen = json.loads(json.dumps(self.trees["full"][1]))
        frozen["implementation_manifest_sha256"] = "0" * 64
        text = builder.render_final_test(self.prereg, "```json\n" + json.dumps(frozen) + "\n```\n")
        result = self.run_gate(text)
        self.assertIn("another implementation manifest", result.stderr)

    def test_passes_with_three_triplets_confirmatory(self):
        result = self.run_gate(self.text)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GATE PASSED: CONFIRMATORY (S = 3)", result.stdout)

    def test_reduced_s_runs_descriptive_only_and_requires_the_flag(self):
        text = builder.render_final_test(self.prereg, self.trees["reduced"][2])
        result = self.run_gate(text, tree="reduced")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GATE PASSED: DESCRIPTIVE-ONLY reduced-S report (S = 2)", result.stdout)
        frozen = json.loads(json.dumps(self.trees["reduced"][1]))
        frozen["descriptive_only"] = False
        text = builder.render_final_test(self.prereg, "```json\n" + json.dumps(frozen) + "\n```\n")
        result = self.run_gate(text, tree="reduced")
        self.assertIn("descriptive_only", result.stderr)

    def test_final_test_notebook_is_sealed_and_embeds_the_current_preregistration(self):
        for index, source in enumerate(code_cells(self.text)):
            compile(source, f"final-{index}", "exec")
        with payload_of(self.text) as archive:
            self.assertEqual(archive.read("inputs/PREREGISTRATION.md"), self.prereg)
            self.assertNotIn("inputs/phase2_train.json", archive.namelist())
            self.assertEqual(hashlib.sha256(archive.read("inputs/final_test.v3.json")).hexdigest(), pe.FROZEN["final_test"][1])
        self.assertIn(builder.PREREGISTRATION_SHA256, code_cells(self.text)[1])
        self.assertNotIn(OLD_PREREGISTRATION_SHA256, self.text)
        evaluation = code_cells(self.text)[3]
        self.assertIn("'--sealed'", evaluation)
        for leak in ("summary", "accuracy", "predictions", "metrics", "correct", "raw_response"):
            self.assertNotIn(leak, evaluation.lower())
        self.assertIn("Sealed", json.loads(self.text)["cells"][0]["source"])
        self.assertNotIn("llama", self.text.lower())


if __name__ == "__main__":
    unittest.main()
