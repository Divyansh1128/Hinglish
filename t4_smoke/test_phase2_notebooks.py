"""The Phase-2 notebooks: current, compilable, self-contained, data-separated, manifest-verified (Amendment 1 item 14),
attempt-logged (item 11), sealed and gated FinalTest (items 12-14), no second backbone (item 15); exact stack only,
plan-chosen runs, stale-lock recovery and baseline first (Amendment 2 items 3-6)."""
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
from t4_smoke.test_train_phase2 import write_baseline
from t4_smoke import train_phase2 as tp
from t4_smoke import train_smoke as ts

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "colab_notebooks"))
import build_phase2_notebooks as builder  # noqa: E402

OLD_PREREGISTRATION_SHA256 = "74be23282ce9e53e3a69456bebf89f9cd71d3859b80090692e4548ef34182840"
AMENDMENT_1_PREREGISTRATION_SHA256 = "37ef68bfcb7cfa0bb530bfbecbf2082d18e916c0217370085d4180e8ea759ada"
AMENDMENT_2_PREREGISTRATION_SHA256 = "b2e6df8f552dfe5756cfde9308880f06de0685d7d1d40de57c5e71cc41260396"
SUPERSEDED = (OLD_PREREGISTRATION_SHA256, AMENDMENT_1_PREREGISTRATION_SHA256, AMENDMENT_2_PREREGISTRATION_SHA256)


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
                self.assertIn("any other build refuses every study run", requirements)
                self.assertNotIn("inputs/phase2_train.json", names)  # the trainer builds the families from the raw bytes
                self.assertEqual(("inputs/EXPOSURE_ORDER.json" in names), kind == "train")
                self.assertEqual(("inputs/train_A.v2.json" in names), kind == "train")
        with payload_of(self.texts["train"]) as archive:
            for name in ts.TRAIN_FILES:
                self.assertEqual(archive.read("inputs/" + Path(name).name), (ROOT / name).read_bytes())
            self.assertEqual(archive.read("inputs/EXPOSURE_ORDER.json"), (ROOT / tp.EXPOSURE_ORDER_PATH).read_bytes())

    def test_notebooks_check_t4_use_drive_and_zip_with_checksums(self):
        for kind, text in self.texts.items():
            source = "\n".join(code_cells(text))
            for needle in ("'T4' in gpu", "requirements-phase2.txt", "USE_DRIVE = True", "SHA256SUMS.txt", "files.download",
                           "process.kill()", "attempts.jsonl", "HUB_CHECK", "STACK_MISMATCHES",
                           "assert not STACK_MISMATCHES", "RECOVER_STALE_LOCK = False", "'--recover-stale-lock'"):
                self.assertIn(needle, source, kind)
            self.assertNotIn("ALLOW_STACK_MISMATCH", text, kind)  # Amendment 2 item 3: no override on any study path
            self.assertNotIn("allow-stack-mismatch", text, kind)
            self.assertEqual(json.loads(text)["metadata"]["accelerator"], "GPU")

    def test_gpu_cell_refuses_a_stack_mismatch(self):
        """Amendment 2 item 3 (R5): the shared GPU cell (Baseline, Train, FinalTest) asserts STACK_MISMATCHES is empty."""
        gpu = code_cells(self.texts["baseline"])[1]
        self.assertEqual(gpu, code_cells(self.texts["train"])[1])
        check = next(line for line in gpu.splitlines() if line.startswith("assert not STACK_MISMATCHES"))
        exec(check, {"STACK_MISMATCHES": []})
        with self.assertRaisesRegex(AssertionError, "Amendment 2 item 3"):
            exec(check, {"STACK_MISMATCHES": ["torch 2.11.0+cu130 expected (Colab build), found 2.5.1+cu121"]})
        self.assertLess(gpu.index("'T4' in gpu"), gpu.index("assert not STACK_MISMATCHES"))
        for path in ("t4_smoke/train_phase2.py", "t4_smoke/phase2_eval.py", "colab_notebooks/build_phase2_notebooks.py"):
            self.assertNotIn("allow_stack_mismatch", (ROOT / path).read_text().lower(), path)

    def test_eval_notebooks_offer_logged_stale_lock_recovery(self):
        """Amendment 2 item 5 (R7)."""
        for kind, text in self.texts.items():
            settings = code_cells(text)[0].split("os.environ")[0]
            self.assertIn("RECOVER_STALE_LOCK = False", settings, kind)
            self.assertIn("no other Colab session", settings, kind)
            self.assertIn("RECOVER_STALE_LOCK = True", json.loads(text)["cells"][0]["source"], kind)
        baseline = code_cells(self.texts["baseline"])[2]
        self.assertIn("*(['--recover-stale-lock'] if RECOVER_STALE_LOCK else [])", baseline)

    def test_baseline_prints_the_ceiling_risk_proxy_with_wilson_interval(self):
        """Amendment 1 item 7."""
        baseline = "\n".join(code_cells(self.texts["baseline"]))
        self.assertIn("'evaluate', '--split', 'dev'", baseline)
        self.assertIn("flag['wilson95']", baseline)
        self.assertIn("{flag['k']}/{flag['n']}", baseline)
        self.assertNotIn("CEILING FLAG", baseline)
        self.assertIn("high unchanged-DEV accuracy (ceiling-risk proxy)", json.loads(self.texts["baseline"])["cells"][0]["source"])
        namespace = {"json": json, "Path": Path, "RECOVER_STALE_LOCK": False, "MANIFEST_SHA256": "m" * 64}
        cell = code_cells(self.texts["baseline"])[2]
        self.assertIn("'--implementation-manifest', INPUTS / 'IMPLEMENTATION_MANIFEST.md'", cell)  # Amendment 2 item 6
        flag = pe.ceiling_flag({"accuracy": {"C": {"correct": 39, "denominator": 40}}})
        calls = []
        with tempfile.TemporaryDirectory() as folder:
            store = Path(folder)
            (store / "baseline_dev").mkdir()
            (store / "baseline_dev" / "base_ceiling_flag.json").write_text(json.dumps(flag))
            namespace.update(STORE=store, INPUTS=store, step=lambda *args: calls.append(args) or 0)
            with self.assertRaisesRegex(AssertionError, "incomplete"):  # no baseline record yet
                exec(cell, dict(namespace))
            (store / "baseline_dev" / "base_baseline_record.json").write_text(json.dumps(
                {"implementation_manifest_sha256": "m" * 64, "results_zip": "base_results.zip", "results_zip_sha256": "z" * 64}))
            with mock.patch("sys.stdout", io.StringIO()) as out:
                exec(cell, dict(namespace))
            with self.assertRaises(AssertionError), mock.patch("sys.stdout", io.StringIO()):
                exec(cell, dict(namespace, MANIFEST_SHA256="0" * 64))
            with mock.patch("sys.stdout", io.StringIO()):
                exec(cell, dict(namespace, RECOVER_STALE_LOCK=True))
        self.assertIn("high unchanged-DEV accuracy (ceiling-risk proxy): FIRES — unchanged DEV C 39/40 (Wilson 95%", out.getvalue())
        self.assertIn("baseline recorded for training (Amendment 2 item 6): base_results.zip " + "z" * 64, out.getvalue())
        self.assertNotIn("--recover-stale-lock", calls[0])
        self.assertIn("--recover-stale-lock", calls[-1])

    def test_train_notebook_has_no_run_choice_and_follows_the_plan(self):
        """Amendment 2 item 4 (R6): no ARM/SEED/SLOT setting; the plan picks the next pending run."""
        cells = code_cells(self.texts["train"])
        self.assertTrue(cells[0].startswith("import os"))
        settings = cells[0].split("os.environ")[0]
        for needle in ("RESUME_AFTER_DISCONNECT = False", "USE_DRIVE = True", "RECOVER_STALE_LOCK = False",
                       "RECOVER_STALE_WRITER = False"):  # Amendment 3 item 2
            self.assertIn(needle, settings)
        for forbidden in ("ARM =", "SEED =", "SLOT =", "ALLOW_STACK_MISMATCH"):
            self.assertNotIn(forbidden, settings)
        source = "\n".join(cells)
        self.assertNotIn("tp.reconcile(", source)  # Amendment 3 item 2: never an automatic close
        self.assertLess(source.index("tp.recover_stale_writer(TRAIN_ROOT, confirmed_no_other_session=True)"),
                        source.index("PLAN = tp.plan("))
        for needle in ("'train_phase2.py'", "'--resume'", "tp.next_run(PLAN)", "if RECOVER_STALE_WRITER:", "tp.resume_target", "'--train-root'",
                       "'--inputs'", "'--baseline-dir'", "tp.HALT_MESSAGE", "'dev_eval'", "never overwritten",
                       "'--implementation-manifest'", "ARM, SEED, SLOT, ATTEMPT, RESUME = ACTION['arm'], ACTION['seed'], ACTION['slot']"):
            self.assertIn(needle, source)
        for gone in ("tp.next_action", "tp.log_event", "'--exposure-order'", "'--implementation-manifest-sha256'", "'--data'"):
            self.assertNotIn(gone, source)  # the trainer itself logs, verifies and consults the plan
        self.assertLess(source.index("assert not STACK_MISMATCHES, 'D021 stack mismatch (no attempt was opened)"),
                        source.index("step(ATTEMPT_DIR, 'train_phase2.py'"))
        markdown = json.loads(self.texts["train"])["cells"][0]["source"]
        for needle in ("the study halts", "60 successful optimizer steps", "44, then 55", "never valid", "ATTEMPT_LOG.jsonl",
                       "seed slot 11, then 22, then 33", "the arms EC, then ER, then EE", "fully settled",
                       "Phase2_Baseline_DEV", "TypeError", "no override", "RECOVER_STALE_WRITER = True",
                       "no other Colab session", "WRITER.lock"):
            self.assertIn(needle, markdown)

    def test_no_second_backbone_in_any_phase2_notebook(self):
        """Amendment 1 item 15."""
        for kind, text in self.texts.items():
            self.assertNotIn("llama", text.lower(), kind)
            self.assertNotIn("MODEL_ID =", text, kind)
        self.assertNotIn("llama", (ROOT / "colab_notebooks" / "build_phase2_notebooks.py").read_text().lower())

    def test_current_preregistration_hash_with_amendment_3(self):
        digest = hashlib.sha256((ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()).hexdigest()
        self.assertEqual(builder.PREREGISTRATION_SHA256, digest)
        self.assertEqual(pe.PREREGISTRATION_SHA256, digest)
        for old in SUPERSEDED:
            self.assertNotEqual(builder.PREREGISTRATION_SHA256, old)
        text = (ROOT / "phase2" / "PREREGISTRATION.md").read_text()
        for amendment in ("## Amendment 1", "## Amendment 2", "## Amendment 3"):
            self.assertIn(amendment, text)
        self.assertEqual(builder.manifest_module().parse(builder.implementation_manifest()[0])["preregistration"]["sha256"], digest)
        for kind, text in self.texts.items():
            self.assertIn(digest, code_cells(text)[0], kind)
            for old in SUPERSEDED:
                self.assertNotIn(old, text, kind)

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
        self.assertEqual(document["dependencies"]["torch_build"], ts.TORCH_BUILD)
        self.assertEqual(document["dependencies"]["evaluation"]["torch"], ts.TORCH_BUILD)
        self.assertEqual(document["training"]["run_order"]["arms"], ["EC", "ER", "EE"])
        self.assertEqual(set(document["training"]["failure_classes"]["infrastructure"]), set(tp.INFRASTRUCTURE_KINDS))
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
    """Execute the Train notebook's setup and control cells with a stub trainer (no GPU). The stub logs the way the
    trainer does: start (with identity) and finish; nothing when it refuses."""

    @classmethod
    def setUpClass(cls):
        cls.text = builder.render_train()

    def run_control(self, work, outcomes, resume=False, recover=False):
        cells = code_cells(self.text)
        settings = cells[0]
        if resume:
            settings = settings.replace("RESUME_AFTER_DISCONNECT = False", "RESUME_AFTER_DISCONNECT = True")
        if recover:
            settings = settings.replace("RECOVER_STALE_WRITER = False", "RECOVER_STALE_WRITER = True")
        stub = textwrap.dedent(f'''
            STACK_MISMATCHES = []
            OUTCOMES = {outcomes!r}
            CALLS = []
            def step(log_dir, script, *args):
                outcome = OUTCOMES.pop(0)
                CALLS.append(args)
                get = lambda flag: args[args.index(flag) + 1]
                if outcome == 'refused':
                    return 2
                arm, seed, slot, attempt, resume = get('--arm'), int(get('--seed')), int(get('--slot')), int(get('--attempt')), '--resume' in args
                root = Path(get('--train-root'))
                writer = tp.WriterLock(root, heartbeat_seconds=0).acquire()  # as the trainer: one writer per root
                out = tp.attempt_dir(root, arm, seed, attempt)
                out.mkdir(parents=True, exist_ok=True)
                keys = dict(arm=arm, seed=seed, slot=slot, attempt=attempt)
                tp.log_event(root / tp.ATTEMPT_LOG, 'resume_start' if resume else 'start', **keys,
                             identity={{'implementation_manifest_sha256': MANIFEST_SHA256}})
                status = 'COMPLETE' if outcome == 'valid' else ('STARTED' if outcome == 'disconnect' else 'FAILED')
                (out / 'train_report.json').write_text(json.dumps({{'status': status, 'failure_class': None if status != 'FAILED' else outcome,
                                                                   'error': 'Traceback\\nX: ' + outcome}}))
                if outcome == 'disconnect':
                    (out / 'checkpoint').mkdir(exist_ok=True)
                    return None  # killed: no finish is logged and WRITER.lock stays behind
                if outcome == 'valid':
                    (out / 'final_adapter.json').write_text(json.dumps({{'status': 'COMPLETE', 'updates': 60, 'arm': arm, 'slot': slot,
                        'seed': seed, 'attempt': attempt, 'steps': {{'windows': 60, 'attempted': 60, 'successful': 60, 'cursor': 960}},
                        'scaler_skips': 0, 'saved_parameters_finite': True, 'resumed': resume, 'valid_for_gate': not resume,
                        'adapter_model_sha256': 'a', 'adapter_config_sha256': 'b', 'initial_adapter_sha256': 'i', 'order_sha256': 'o',
                        'baseline_dev_results_zip_sha256': 'z'}}))
                result, detail = tp.attempt_outcome(out)
                tp.log_event(root / tp.ATTEMPT_LOG, 'resume_finish' if resume else 'finish', **keys, outcome=result, detail=detail)
                writer.release()
                return 0 if outcome == 'valid' else 1
        ''')
        return run_python(settings + "\n" + stub + "\n" + cells[2], work)

    def test_plan_drives_retry_reserve_refusal_and_halt(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "work"
            work.mkdir()
            log = work / "hinglish_phase2" / "runs" / "train" / tp.ATTEMPT_LOG
            result = self.run_control(work, ["infrastructure"])
            self.assertIn("Next run from the plan: EC seed 11 (slot 11): attempt 1", result.stdout)
            self.assertIn("Infrastructure failure", result.stderr)
            result = self.run_control(work, ["disconnect"])  # second attempt: from scratch, then the runtime is killed
            self.assertIn("from-scratch retry", result.stdout)
            self.assertIn("no recorded outcome", result.stderr)
            result = self.run_control(work, ["valid"])  # Amendment 3 item 2: the open attempt is never closed by itself
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RECOVER_STALE_WRITER = True", result.stderr)
            self.assertIn("HELD by session", result.stdout)
            self.assertEqual(len(tp.read_log(log)), 3)
            result = self.run_control(work, ["valid"], recover=True)  # confirmed -> seed 11 retired -> reserve 44, EC first
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("RECOVER_STALE_WRITER: closed EC-s11 attempt 2 -> infrastructure", result.stdout)
            self.assertTrue((log.parent / tp.WRITER_RECOVERIES).exists())
            self.assertIn("Next run from the plan: EC seed 44 (slot 11, reserve): attempt 1", result.stdout)
            self.assertEqual(tp.plan(tp.read_log(log))["slots"][11]["chain"], [11, 44])
            result = self.run_control(work, ["refused"])
            self.assertIn("refused before opening an attempt", result.stderr)
            result = self.run_control(work, ["valid"])  # the plan, not the operator, moves on to ER
            self.assertIn("Next run from the plan: ER seed 44 (slot 11, reserve): attempt 1", result.stdout)
            self.assertTrue((tp.attempt_dir(log.parent, "EC", 11, 1) / "train_report.json").exists())  # never overwritten
            result = self.run_control(work, ["numerical"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NUMERICAL FAILURE", result.stdout)
            self.assertIn("THE STUDY HALTS", result.stdout)
            result = self.run_control(work, ["valid"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("StudyHalted", result.stderr)
            outcomes = [(e["event"], e["arm"], e["seed"], e.get("outcome")) for e in tp.read_log(log)]
            self.assertEqual(outcomes, [("start", "EC", 11, None), ("finish", "EC", 11, "infrastructure"),
                                        ("start", "EC", 11, None), ("finish", "EC", 11, "infrastructure"),
                                        ("start", "EC", 44, None), ("finish", "EC", 44, "valid"),
                                        ("start", "ER", 44, None), ("finish", "ER", 44, "valid"),
                                        ("start", "EE", 44, None), ("finish", "EE", 44, "numerical")])

    def test_trainer_receives_the_plan_choice_and_the_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "work"
            work.mkdir()
            result = self.run_control(work, ["valid"])
            self.assertEqual(result.returncode, 0, result.stderr)
        cell = code_cells(self.text)[2]
        self.assertIn("BASELINE_DIR = STORE / 'baseline_dev'", cell)
        self.assertIn("'--arm', ARM, '--seed', SEED, '--slot', SLOT, '--attempt', ATTEMPT", cell)

    def test_resume_is_logged_and_never_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "work"
            work.mkdir()
            log = work / "hinglish_phase2" / "runs" / "train" / tp.ATTEMPT_LOG
            self.run_control(work, ["disconnect"])
            result = self.run_control(work, ["valid"], resume=True, recover=True)
            self.assertIn("RESUMING attempt 1", result.stdout)
            self.assertIn("never valid", result.stderr)
            current = tp.plan(tp.read_log(log))
            self.assertEqual(current["attempts"]["EC-s11"][0]["resume_outcome"], "resumed_invalid")
            self.assertEqual(tp.next_run(current)["attempt"], 2)


class FinalTestGateNotebookTests(unittest.TestCase):
    """Execute the FinalTest notebook's setup and gate cells (model-free) in a fresh interpreter."""

    @classmethod
    def setUpClass(cls):
        # The rendered notebook is only a gate fixture. Never package real test bytes
        # before freeze; all gate mechanics work with a DEV payload under that name.
        original_read = Path.read_bytes
        dev_bytes = (ROOT / "phase2" / "dev.v2.json").read_bytes()

        def fixture_read(path):
            if path.resolve() == (ROOT / "phase2" / "final_test.v3.json").resolve():
                return dev_bytes
            return original_read(path)

        cls.fixture_bytes = dev_bytes
        cls.read_patch = mock.patch.object(Path, "read_bytes", fixture_read)
        cls.read_patch.start()
        cls.addClassCleanup(cls.read_patch.stop)
        cls.prereg = (ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()
        cls.manifest = builder.implementation_manifest()
        cls.store = tempfile.TemporaryDirectory()
        cls.baseline = Path(cls.store.name) / "baseline_dev"
        baseline_sha = write_baseline(cls.baseline, cls.manifest[1])  # realistic synthetic unchanged-DEV run (Amendment 3 item 3)
        cls.trees = {}
        with mock.patch.object(fixtures, "MANIFEST_SHA", cls.manifest[1]), \
                mock.patch.object(fixtures, "MANIFEST_PATH", ROOT / "phase2" / "IMPLEMENTATION_MANIFEST.md"), \
                mock.patch.object(fixtures, "BASELINE_SHA", baseline_sha), \
                mock.patch.object(fixtures, "DATA_SHA", tp.phase2_dataset(ROOT)["families_sha256"]):
            for name, slots in (("full", (11, 22, 33)), ("reduced", (11, 22))):
                train = Path(cls.store.name) / name
                fixtures.complete_slots(train, slots=slots)
                if name == "reduced":
                    fixtures.exhaust_slot(train, 33)
                frozen = fixtures.freeze(train, baseline_dir=cls.baseline)
                cls.trees[name] = (train, frozen, "# Adapters frozen (TEST FIXTURE)\n\n```json\n" + json.dumps(frozen, indent=1) + "\n```\n")
        cls.text = builder.render_final_test(cls.prereg, cls.trees["full"][2])

    @classmethod
    def tearDownClass(cls):
        cls.store.cleanup()

    def run_gate(self, text, tree="full", mutate=None, baseline=True):
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
            if baseline:
                shutil.copytree(self.baseline, work / "hinglish_phase2" / "runs" / "baseline_dev")
                if callable(baseline):
                    baseline(work / "hinglish_phase2" / "runs" / "baseline_dev")
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

    def test_refuses_without_the_frozen_unchanged_dev_baseline(self):
        """Amendment 2 item 6 (R8): the gate requires the baseline the attempts were started with."""
        result = self.run_gate(self.text, baseline=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unchanged-DEV baseline", result.stderr)
        result = self.run_gate(self.text, baseline=lambda folder: (folder / "base_results.zip").write_bytes(b"rerun"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unchanged-DEV baseline", result.stderr)
        self.assertNotIn("GATE PASSED", result.stdout)

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
            self.assertEqual(archive.read("inputs/final_test.v3.json"), self.fixture_bytes)
        self.assertIn(builder.PREREGISTRATION_SHA256, code_cells(self.text)[1])
        self.assertNotIn(OLD_PREREGISTRATION_SHA256, self.text)
        evaluation = code_cells(self.text)[3]
        self.assertIn("'--sealed'", evaluation)
        self.assertIn("'--baseline-dir', BASELINE_DIR", evaluation)
        self.assertIn("*(['--recover-stale-lock'] if RECOVER_STALE_LOCK else [])", evaluation)
        self.assertIn("RECOVER_STALE_LOCK = False", code_cells(self.text)[0])
        self.assertIn("assert not STACK_MISMATCHES", code_cells(self.text)[2])
        for old in SUPERSEDED:
            self.assertNotIn(old, self.text)
        for leak in ("summary", "accuracy", "predictions", "metrics", "correct", "raw_response"):
            self.assertNotIn(leak, evaluation.lower())
        self.assertIn("Sealed", json.loads(self.text)["cells"][0]["source"])
        self.assertNotIn("llama", self.text.lower())


if __name__ == "__main__":
    unittest.main()
