import base64
import copy
import hashlib
import io
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from t4_smoke import train_smoke as ts
from t4_smoke.protocol import CONFIG, INSTRUCTION
from t4_smoke.test_labels import FakeTokenizer

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "colab_notebooks" / "training_smoke" / "TrainSmoke_Qwen3-4B.ipynb"


def synthetic_source(name, count, role="CONFIRM_TRAIN", prefix="X"):
    families = [{
        "family_id": f"{prefix}{index:03d}", "source_family_id": f"{prefix}{index:03d}-source",
        "template_group_id": f"{prefix}{index:03d}-template", "topic": "ratios", "split_role": role,
        "version": "v1", "reference_solution_en": f"Add {index} and 1.\nFINAL: {index + 1}",
        "forms": {form: {"rendering_id": f"{prefix}{index:03d}-{form}-v1", "text": f"{form} question {index}?"}
                  for form in ("E", "R", "C")},
    } for index in range(count)]
    raw = json.dumps(families).encode()
    return (name, raw), hashlib.sha256(raw).hexdigest()


def synthetic_sources(**overrides):
    (a, hash_a) = synthetic_source("a.json", 12, prefix="A", **overrides)
    (b, hash_b) = synthetic_source("b.json", 12, prefix="B")
    return [a, b], {"a.json": hash_a, "b.json": hash_b}


class RecipeTests(unittest.TestCase):
    def test_recipe_agrees_with_protocol_on_shared_settings(self):
        shared = set(CONFIG) & set(ts.RECIPE)
        self.assertGreaterEqual(len(shared), 30)
        for key in sorted(shared):
            with self.subTest(key=key):
                self.assertEqual(ts.RECIPE[key], CONFIG[key])
        self.assertEqual(ts.INSTRUCTION, INSTRUCTION)

    def test_d021_settings(self):
        recipe = ts.RECIPE
        self.assertEqual((recipe["rank"], recipe["alpha"], recipe["dropout"]), (16, 32, 0.05))
        self.assertEqual(recipe["targets"], ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
        self.assertEqual((recipe["microbatch"], recipe["accumulation"], recipe["sequence_length"]), (1, 16, 1024))
        self.assertEqual((recipe["updates"], recipe["measurement_warmup_updates"], recipe["resume_after_update"],
                          recipe["probe_updates"]), (6, 2, 4, 32))
        self.assertEqual((recipe["lr"], recipe["adapter_dtype"], recipe["compute_dtype"]), (1e-4, "float32", "float16"))
        self.assertEqual(ts.PINS["transformers"], "4.51.3")
        self.assertEqual(ts.PINS["bitsandbytes"], "0.50.2")
        self.assertEqual(ts.PINS["peft"], "0.15.2")
        self.assertEqual(ts.TORCH_BUILD, "2.11.0+cu130")
        self.assertRegex(ts.MODEL_REVISION, r"^[0-9a-f]{40}$")

    def test_trainable_parameter_count_from_qwen3_4b_shapes(self):
        hidden, query, kv, mlp, layers, rank = 2560, 32 * 128, 8 * 128, 9728, 36, 16
        shapes = [(hidden, query), (hidden, kv), (hidden, kv), (query, hidden), (hidden, mlp), (hidden, mlp), (mlp, hidden)]
        self.assertEqual(layers * sum(rank * (a + b) for a, b in shapes), ts.RECIPE["trainable_parameters"])
        self.assertEqual(layers * len(shapes), ts.RECIPE["quantized_linear_modules"])

    def test_stack_mismatch_reporting(self):
        found = dict(ts.PINS, torch=ts.TORCH_BUILD)
        self.assertEqual(ts.stack_mismatches(found), [])
        found.update(peft="0.21.2", torch="2.12.0+cu130")
        self.assertEqual(len(ts.stack_mismatches(found)), 2)


class SelectionTests(unittest.TestCase):
    def test_real_selection_is_deterministic_and_train_only(self):
        first = ts.select_families(ts.load_train_sources(ROOT))
        second = ts.select_families(list(reversed(ts.load_train_sources(ROOT))))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertEqual([f["family_id"] for f in first], sorted(f["family_id"] for f in first))
        self.assertEqual(sum(f["source_file"] == "phase2/train_A.v2.json" for f in first), 8)
        self.assertEqual(sum(f["source_file"] == "phase2/train_B.v2.json" for f in first), 8)
        for family in first:
            self.assertEqual(family["split_role"], "CONFIRM_TRAIN")
            self.assertRegex(family["family_id"], r"^TR[AB][0-9]{3}$")
            self.assertEqual(set(family["forms"]), {"E", "R", "C"})
        data = ts.smoke_dataset(ROOT)
        self.assertEqual(ts.validate_dataset(data), first)
        self.assertEqual(data["sources"], ts.TRAIN_FILES)

    def test_selection_follows_the_recorded_hash_rule(self):
        sources = ts.load_train_sources(ROOT)
        expected = []
        for _, raw in sources:
            ids = sorted((hashlib.sha256(f"D021-smoke-2026-10-27:{f['family_id']}".encode()).hexdigest(), f["family_id"])
                         for f in json.loads(raw))
            expected += [family_id for _, family_id in ids[:8]]
        self.assertEqual([f["family_id"] for f in ts.select_families(sources)], sorted(expected))
        self.assertIn("sha256('D021-smoke-2026-10-27:' + family_id)", ts.SELECTION_RULE)

    def test_only_the_two_frozen_train_files_are_read(self):
        read = []
        original = Path.read_bytes

        def spy(path):
            read.append(path.resolve())
            return original(path)

        with mock.patch.object(Path, "read_bytes", spy):
            ts.smoke_dataset(ROOT)
        self.assertEqual(sorted(read), sorted((ROOT / name).resolve() for name in ts.TRAIN_FILES))
        self.assertEqual(sorted(ts.TRAIN_FILES), ["phase2/train_A.v2.json", "phase2/train_B.v2.json"])

    def test_non_train_role_is_refused(self):
        for role in ("FINAL_TEST", "DEV", "PILOT_EVAL", None):
            sources, hashes = synthetic_sources(role=role)
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, "not a TRAIN family"):
                ts.select_families(sources, expected=hashes)

    def test_hash_mismatch_and_unexpected_files_are_refused(self):
        sources, hashes = synthetic_sources()
        self.assertEqual(len(ts.select_families(sources, expected=hashes)), 16)
        tampered = [(sources[0][0], sources[0][1].replace(b"question", b"Question")), sources[1]]
        with self.assertRaisesRegex(ValueError, "frozen SHA-256"):
            ts.select_families(tampered, expected=hashes)
        with self.assertRaisesRegex(ValueError, "exactly the frozen TRAIN files"):
            ts.select_families(sources + [("extra.json", b"[]")], expected=hashes)
        with self.assertRaisesRegex(ValueError, "exactly the frozen TRAIN files"):
            ts.select_families(sources[:1], expected=hashes)

    def test_dataset_tampering_is_detected(self):
        data = ts.smoke_dataset(ROOT)
        altered = copy.deepcopy(data)
        altered["families"][0]["completion"] += " "
        with self.assertRaisesRegex(ValueError, "changed after selection"):
            ts.validate_dataset(altered)
        altered = copy.deepcopy(data)
        altered["families"].pop()
        with self.assertRaisesRegex(ValueError, "Exactly 16"):
            ts.validate_dataset(altered)


class ArmTests(unittest.TestCase):
    def setUp(self):
        sources, hashes = synthetic_sources()
        self.families = ts.select_families(sources, expected=hashes)

    def test_arm_sequences(self):
        for arm, second in (("EE", "E"), ("ER", "R"), ("EC", "C")):
            sequence = ts.arm_sequence(self.families, arm)
            self.assertEqual(len(sequence), 32)
            self.assertEqual(sequence[0::2], [(f["family_id"], "E") for f in self.families])
            self.assertEqual(sequence[1::2], [(f["family_id"], second) for f in self.families])

    def test_update_cursors_cover_cycles(self):
        self.assertEqual(ts.update_cursors(1), list(range(16)))
        self.assertEqual(ts.update_cursors(5), list(range(64, 80)))
        covered = [cursor % 32 for update in range(1, 7) for cursor in ts.update_cursors(update)]
        self.assertEqual(covered, list(range(32)) * 3)
        probe = [cursor % 32 for update in range(1, 33) for cursor in ts.update_cursors(update)]
        self.assertEqual(probe, list(range(32)) * 16)
        with self.assertRaises(ValueError):
            ts.update_cursors(0)

    def test_arm_examples_share_targets_and_differ_in_prompts(self):
        tokenizer = FakeTokenizer()
        examples = ts.build_examples(tokenizer, self.families)
        arms = {arm: ts.arm_examples(examples, self.families, arm) for arm in ts.ARMS}
        for index in range(32):
            targets = {arm: [t for t in arms[arm][index]["labels"] if t != -100] for arm in arms}
            self.assertEqual(targets["EE"], targets["ER"])
            self.assertEqual(targets["EE"], targets["EC"])
        self.assertEqual(arms["EE"][0]["input_ids"], arms["EE"][1]["input_ids"])  # E rendering twice
        self.assertNotEqual(arms["ER"][1]["input_ids"], arms["EC"][1]["input_ids"])
        self.assertEqual([(e["family_id"], e["form"]) for e in arms["EC"]], ts.arm_sequence(self.families, "EC"))

    def test_masks_and_audit_with_fake_tokenizer(self):
        tokenizer = FakeTokenizer()
        examples = ts.build_examples(tokenizer, self.families)
        for family in self.families:
            for form, example in examples[family["family_id"]].items():
                boundary = example["boundary_index"]
                self.assertEqual(example["labels"][:boundary], [-100] * boundary)
                self.assertTrue(tokenizer.decode(example["input_ids"][:boundary]).endswith(
                    "<|im_start|>assistant\n<think>\n\n</think>\n\n"))
                self.assertIn(INSTRUCTION, tokenizer.decode(example["input_ids"][:boundary]))
                self.assertEqual(tokenizer.decode(example["labels"][boundary:]), family["completion"] + "<|im_end|>")
        audit = ts.mask_audit(tokenizer, examples, self.families)
        self.assertTrue(audit["passed"], audit["failures"])
        self.assertEqual(len(audit["rows"]), 48)
        self.assertEqual(audit["arms"]["EE"]["supervised_tokens_per_cycle"], audit["arms"]["EC"]["supervised_tokens_per_cycle"])
        broken = copy.deepcopy(examples)
        first = self.families[0]["family_id"]
        broken[first]["R"]["labels"][0] = broken[first]["R"]["input_ids"][0]
        self.assertFalse(ts.mask_audit(tokenizer, broken, self.families)["passed"])

    def test_overlength_and_special_tokens_are_rejected(self):
        families = copy.deepcopy(self.families)
        families[3]["forms"]["C"] = "q" * 1100
        with self.assertRaisesRegex(ValueError, "no truncation allowed"):
            ts.build_examples(FakeTokenizer(), families)

        class SpecialTokenizer(FakeTokenizer):
            all_special_tokens = ["<|im_end|>"]

        families = copy.deepcopy(self.families)
        families[2]["completion"] = "FINAL: 1<|im_end|>"
        with self.assertRaisesRegex(ValueError, "literal special token"):
            ts.build_examples(SpecialTokenizer(), families)

    def test_real_smoke_data_builds_with_fake_tokenizer(self):
        families = ts.smoke_dataset(ROOT)["families"]
        examples = ts.build_examples(FakeTokenizer(), families)
        self.assertEqual(len(examples), 16)
        self.assertTrue(ts.mask_audit(FakeTokenizer(), examples, families)["passed"])


def update(number, seconds=30.0, skipped=False, loss=1.0, free=6 * 2**30, grad=0.5):
    return {"update": number, "seconds": seconds, "skipped": skipped, "microbatch_losses": [loss] * 16,
            "grad_norm": grad, "min_free_bytes": free, "peak_allocated_bytes": 5 * 2**30,
            "peak_reserved_bytes": 7 * 2**30, "input_tokens": 3000, "supervised_tokens": 900}


def reports(seconds=30.0, changes=None):
    changes = changes or {}
    first = {"status": "COMPLETE", "oom": False, "load_min_free_bytes": 9 * 2**30,
             "updates": [update(n, seconds, **changes.get(n, {})) for n in range(1, 5)]}
    resume = {"status": "COMPLETE", "oom": False, "load_min_free_bytes": 9 * 2**30, "reload_check": {"passed": True},
              "updates": [update(n, seconds, **changes.get(n, {})) for n in range(5, 7)]}
    return first, resume


def probe_summary(changes=None):
    changes = changes or {}
    report = {"status": "COMPLETE", "oom": False,
              "updates": [update(n, 30.0, **changes.get(n, {})) for n in range(1, 33)]}
    return ts.summarize_probe(report)


class DecisionTests(unittest.TestCase):
    def arms(self, seconds=30.0, **per_arm):
        return {arm: ts.summarize_arm(*per_arm.get(arm, reports(seconds))) for arm in ts.ARMS}

    def decide(self, arms=None, probe=None, **settings):
        return ts.decide(arms or self.arms(), probe or probe_summary(), preflight_passed=settings.pop("preflight", True),
                         **settings)

    def test_time_tiers_and_boundaries(self):
        for seconds, decision in ((8.0, "COLAB"), (56.0, "COLAB"), (56.01, "KAGGLE_2xT4"), (150.0, "KAGGLE_2xT4"),
                                  (150.5, "FALLBACK_QWEN3_1_7B"), (400.0, "FALLBACK_QWEN3_1_7B")):
            with self.subTest(seconds=seconds):
                result = self.decide(self.arms(seconds))
                self.assertEqual(result["decision"], decision)
                self.assertEqual(result["worst_median_seconds"], seconds)
                self.assertEqual(result["failed_checks"], [])

    def test_worst_arm_median_over_timed_updates_decides(self):
        fast = reports(20.0)
        slow_er = reports(20.0)
        for record in slow_er[0]["updates"][2:] + slow_er[1]["updates"]:
            record["seconds"] = 70.0
        slow_er[0]["updates"][0]["seconds"] = 999.0  # warm-up updates are not timed
        result = self.decide(self.arms(EE=fast, ER=slow_er, EC=fast))
        self.assertEqual(result["decision"], "KAGGLE_2xT4")
        self.assertEqual(result["median_seconds"], {"EE": 20.0, "ER": 70.0, "EC": 20.0})

    def test_median_uses_updates_three_to_six(self):
        first, resume = reports(10.0)
        for record, seconds in zip(first["updates"] + resume["updates"], (500, 500, 10, 20, 30, 40)):
            record["seconds"] = float(seconds)
        summary = ts.summarize_arm(first, resume)
        self.assertEqual(summary["timed_updates"], [3, 4, 5, 6])
        self.assertEqual(summary["median_seconds"], 25.0)
        self.assertEqual(summary["input_tokens_per_update"], [3000] * 6)

    def test_integrity_failures_block_go(self):
        cases = {
            "oom": lambda first, resume: first.update(oom=True, status="FAILED"),
            "headroom": lambda first, resume: resume["updates"][0].update(min_free_bytes=2 * 2**30 - 1),
            "load headroom": lambda first, resume: first.update(load_min_free_bytes=2**30),
            "nan loss": lambda first, resume: first["updates"][1]["microbatch_losses"].__setitem__(3, float("nan")),
            "late skip": lambda first, resume: resume["updates"][1].update(skipped=True, grad_norm=float("inf")),
            "reload": lambda first, resume: resume.update(reload_check={"passed": False}),
            "incomplete": lambda first, resume: resume.update(status="FAILED", updates=resume["updates"][:1]),
        }
        for name, mutate in cases.items():
            first, resume = reports(30.0)
            mutate(first, resume)
            with self.subTest(case=name):
                result = self.decide(self.arms(EC=(first, resume)))
                self.assertEqual(result["decision"], "NO_GO_INTEGRITY")
                self.assertTrue(any(check.startswith("EC:") for check in result["failed_checks"]))

    def test_early_skips_are_counted_not_failed(self):
        first, resume = reports(30.0, {1: {"skipped": True, "grad": float("inf")}, 2: {"skipped": True}})
        summary = ts.summarize_arm(first, resume)
        self.assertEqual((summary["scaler_skips"], summary["scaler_skips_after_resume_point"]), (2, 0))
        self.assertEqual(self.decide(self.arms(EE=(first, resume)))["decision"], "COLAB")

    def test_missing_arm_preflight_probe_and_pairing(self):
        arms = self.arms()
        del arms["ER"]
        self.assertEqual(self.decide(arms)["decision"], "NO_GO_INTEGRITY")
        self.assertEqual(self.decide(preflight=False)["decision"], "NO_GO_INTEGRITY")
        self.assertEqual(self.decide(paired_initialization=False)["decision"], "NO_GO_INTEGRITY")
        self.assertEqual(self.decide(probe=probe_summary({20: {"skipped": True}}))["decision"], "NO_GO_INTEGRITY")
        self.assertEqual(self.decide(probe=ts.summarize_probe(None))["decision"], "NO_GO_INTEGRITY")
        short = {"status": "COMPLETE", "oom": False, "updates": [update(n) for n in range(1, 10)]}
        self.assertEqual(self.decide(probe=ts.summarize_probe(short))["decision"], "NO_GO_INTEGRITY")

    def test_fallback_is_kept_even_with_other_failures(self):
        first, resume = reports(200.0)
        first["updates"][2]["microbatch_losses"][0] = float("inf")
        result = self.decide(self.arms(200.0, EC=(first, resume)))
        self.assertEqual(result["decision"], "FALLBACK_QWEN3_1_7B")
        self.assertTrue(result["failed_checks"])

    def test_non_finite_values_stay_json_safe_and_fail(self):
        self.assertEqual([ts.json_float(v) for v in (1.5, float("nan"), float("inf"))], [1.5, "nan", "inf"])
        first, resume = reports(30.0)
        first["updates"][0]["microbatch_losses"][0] = ts.json_float(float("nan"))
        resume["updates"][0]["grad_norm"] = ts.json_float(float("inf"))
        json.dumps(first, allow_nan=False)
        summary = ts.summarize_arm(first, resume)
        self.assertFalse(summary["losses_finite"])
        self.assertFalse(summary["grad_norms_finite_after_resume_point"])

    def test_projection_formula(self):
        result = self.decide(self.arms(30.0))
        self.assertAlmostEqual(result["projected_hours_2304_updates_x1.4"], round(3 * 256 * 90 / 3600 * 1.4, 2))
        json.dumps(result, allow_nan=False)


class NotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "colab_notebooks"))
        import build_training_smoke_notebook as builder
        cls.builder = builder
        cls.text = builder.render()
        cls.notebook = json.loads(cls.text)

    def test_committed_notebook_is_current(self):
        self.assertEqual(NOTEBOOK.read_text(encoding="utf-8"), self.text, "Rebuild: python3 -B colab_notebooks/build_training_smoke_notebook.py")
        self.assertEqual(self.builder.render(), self.text)  # deterministic

    def test_code_cells_compile(self):
        cells = [cell for cell in self.notebook["cells"] if cell["cell_type"] == "code"]
        self.assertGreaterEqual(len(cells), 6)
        for index, cell in enumerate(cells):
            with self.subTest(cell=index):
                compile(cell["source"], f"cell-{index}", "exec")
                self.assertNotRegex(cell["source"], r"(?m)^\s*[!%]")

    def payload(self):
        source = self.notebook["cells"][2]["source"]
        blob = base64.b64decode(re.search(r"b64decode\('([^']+)'\)", source).group(1))
        self.assertIn(hashlib.sha256(blob).hexdigest(), source)
        return zipfile.ZipFile(io.BytesIO(blob))

    def test_payload_is_self_contained_and_current(self):
        with self.payload() as archive:
            self.assertEqual(sorted(archive.namelist()), sorted(
                ["t4_smoke/train_smoke.py", "t4_smoke/labels.py", "t4_smoke/protocol.py",
                 "smoke/smoke_data.json", "requirements-train.txt"]))
            for name in ("train_smoke.py", "labels.py", "protocol.py"):
                self.assertEqual(archive.read("t4_smoke/" + name), (ROOT / "t4_smoke" / name).read_bytes())
                compile(archive.read("t4_smoke/" + name), name, "exec")
            data = json.loads(archive.read("smoke/smoke_data.json"))
            self.assertEqual(data, ts.smoke_dataset(ROOT))
            self.assertEqual(len(data["families"]), 16)
            requirements = archive.read("requirements-train.txt").decode()
            for name, version in ts.PINS.items():
                self.assertIn(f"{name}=={version}\n", requirements)
            self.assertNotIn("torch==", requirements)
            self.assertNotIn("trl", requirements)
            embedded = json.dumps(data)
            for marker in ("DV0", "FT0", "PB0", "PIL0", '"gold"', "reference_equation"):
                self.assertNotIn(marker, embedded)

    def test_notebook_checks_t4_runs_all_phases_and_downloads_checksums(self):
        source = "\n".join(cell["source"] for cell in self.notebook["cells"])
        for needle in ("'T4' in gpu", "requirements-train.txt", "step('preflight')", "'--phase', 'first'",
                       "'--phase', 'resume'", "'--phase', 'probe', '--arm', 'EC'", "step('decide')",
                       "SHA256SUMS.txt", "files.download", "attempts.jsonl"):
            self.assertIn(needle, source)
        self.assertEqual(self.notebook["metadata"]["accelerator"], "GPU")


if __name__ == "__main__":
    unittest.main()
