"""The Phase-2 additions (modes phase2_dev/phase2_final_test, optional LoRA adapter) must not change v1 behaviour."""
import copy
import hashlib
import importlib.util
import inspect
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from hinglish_pilot import data as live_data
from hinglish_pilot import engine as live_engine
from hinglish_pilot import hf_backend
from hinglish_pilot import report as live_report

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'frozen_engine' / 'v1'
OLD_MODES = ('demo', 'reviewed', 'pilot_b', 'pilot_adjudicated')


def load_v1():
    """The frozen v1 engine as a separate package, so both versions can run side by side."""
    name = 'hinglish_pilot_v1_snapshot'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, SNAPSHOT / 'hinglish_pilot' / '__init__.py',
                                                      submodule_search_locations=[str(SNAPSHOT / 'hinglish_pilot')])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return {part: importlib.import_module(f'{name}.{part}') for part in ('data', 'engine', 'report')}


import importlib  # noqa: E402


def fixture():
    read = live_engine.read
    return read(ROOT / 'fixtures/demo_dataset.json'), read(ROOT / 'fixtures/demo_splits.json')


class SnapshotTests(unittest.TestCase):
    def test_snapshot_is_intact_and_is_what_legacy_notebooks_embed(self):
        for line in (SNAPSHOT / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertEqual(hashlib.sha256((SNAPSHOT / name).read_bytes()).hexdigest(), digest, name)
        sys.path.insert(0, str(ROOT))
        import build_notebook
        with zipfile.ZipFile(io.BytesIO(build_notebook.payload())) as archive:
            engine = sorted(n for n in archive.namelist() if n.startswith('hinglish_pilot/'))
            self.assertEqual(engine, sorted('hinglish_pilot/' + p.name for p in (SNAPSHOT / 'hinglish_pilot').glob('*.py')))
            for name in engine:
                self.assertEqual(archive.read(name), (SNAPSHOT / name).read_bytes())
        # The unchanged modules are byte-identical to v1.
        for name in ('scorer_v1.py', '__init__.py'):
            self.assertEqual((ROOT / 'hinglish_pilot' / name).read_bytes(), (SNAPSHOT / 'hinglish_pilot' / name).read_bytes())


class BackwardCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v1 = load_v1()

    def test_default_configs_unchanged_for_v1_modes(self):
        for mode in OLD_MODES:
            for model in live_engine.MODELS:
                self.assertEqual(live_engine.default_config(mode, model), self.v1['engine'].default_config(mode, model))
        self.assertEqual(live_engine.default_config(), self.v1['engine'].default_config())
        self.assertEqual(live_engine.INSTRUCTION, self.v1['engine'].INSTRUCTION)
        self.assertEqual(live_engine.PROMPT_VERSION, self.v1['engine'].PROMPT_VERSION)

    def test_v1_modes_reject_an_adapter_field_and_phase2_modes_require_it(self):
        config = live_engine.default_config('pilot_b')
        config.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
        live_engine.validate_config(config)
        with self.assertRaises(ValueError):
            live_engine.validate_config(dict(config, adapter=None))
        phase2 = live_engine.default_config('phase2_dev')
        phase2.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
        live_engine.validate_config(phase2)
        with self.assertRaises(ValueError):
            live_engine.validate_config({k: v for k, v in phase2.items() if k != 'adapter'})
        good = {'arm': 'EC', 'seed': 11, 'attempt': 1, 'adapter_model_sha256': 'a' * 64, 'adapter_config_sha256': 'b' * 64}
        live_engine.validate_config(dict(phase2, adapter=good))
        for bad in (dict(good, arm='EX'), dict(good, adapter_model_sha256='xyz'), dict(good, extra=1), 'path/to/adapter'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                live_engine.validate_config(dict(phase2, adapter=bad))

    def test_phase2_modes_are_qwen3_4b_only_and_v1_modes_keep_every_model(self):
        """Amendment 1 item 15: no second backbone (Llama or other) in Phase-2 modes; v1 modes unchanged."""
        for model in live_engine.MODELS:
            v1 = live_engine.default_config('pilot_b', model)
            v1.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
            live_engine.validate_config(v1)
            for mode in ('phase2_dev', 'phase2_final_test'):
                config = live_engine.default_config(mode, model)
                config.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
                if model == 'Qwen/Qwen3-4B':
                    live_engine.validate_config(config)
                else:
                    with self.subTest(model=model, mode=mode), self.assertRaisesRegex(ValueError, 'Amendment 1 item 15'):
                        live_engine.validate_config(config)

    def test_validation_unchanged_for_v1_fixtures(self):
        dataset, splits = fixture()
        self.assertEqual(live_data.validate(dataset, splits, 'demo'), self.v1['data'].validate(dataset, splits, 'demo'))
        with self.assertRaises(ValueError):
            live_data.validate(dataset, splits, 'phase2_dev')

    def test_demo_run_identical_to_v1_except_code_hash(self):
        dataset, splits = fixture()
        results = {}
        for name, modules in (('live', {'engine': live_engine, 'report': live_report}), ('v1', self.v1)):
            with tempfile.TemporaryDirectory() as folder:
                config = modules['engine'].default_config()
                config.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
                root = Path(folder) / 'demo'
                manifest = modules['engine'].run(root, dataset, splits, config, modules['engine'].FakeBackend())
                modules['report'].analyze(root)
                predictions = [(x['rendering_id'], x['correct'], x['raw_response']) for x in modules['engine'].selected(root)[1]]
                results[name] = ({k: manifest[k] for k in ('config_sha256', 'dataset_sha256', 'split_sha256', 'label',
                                                           'warnings', 'evaluation_order', 'status', 'deviations', 'backend')},
                                 predictions, (root / 'summary.md').read_text())
        self.assertEqual(results['live'], results['v1'])

    def test_hf_backend_adapter_path_is_optional_and_checked_before_any_gpu_import(self):
        parameter = inspect.signature(hf_backend.HFBackend.__init__).parameters['adapter_path']
        self.assertIsNone(parameter.default)
        config = live_engine.default_config('pilot_b')
        config.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
        with self.assertRaisesRegex(ValueError, 'exactly when'):
            hf_backend.HFBackend(config, adapter_path='/tmp/adapter')
        phase2 = live_engine.default_config('phase2_final_test')
        phase2.update(model_revision='0' * 40, tokenizer_revision='0' * 40,
                      adapter={'arm': 'EE', 'seed': 22, 'attempt': 1, 'adapter_model_sha256': 'a' * 64, 'adapter_config_sha256': 'b' * 64})
        with self.assertRaisesRegex(ValueError, 'exactly when'):
            hf_backend.HFBackend(phase2)
        self.assertEqual(hf_backend.PINS, {'transformers': '4.51.3', 'bitsandbytes': '0.50.2', 'accelerate': '1.6.0',
                                           'huggingface-hub': '0.30.2', 'tokenizers': '0.21.1', 'safetensors': '0.5.3'})

    def test_adapter_file_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / 'adapter_model.safetensors').write_bytes(b'weights')
            (folder / 'adapter_config.json').write_text(json.dumps({'peft_type': 'LORA'}))
            found = hf_backend.adapter_digests(folder)
            adapter = {'arm': 'EC', 'seed': 11, 'attempt': 1, **found}
            self.assertEqual(hf_backend.verify_adapter(folder, adapter), found)
            self.assertEqual(found['adapter_model_sha256'], hashlib.sha256(b'weights').hexdigest())
            with self.assertRaisesRegex(ValueError, 'SHA-256 differs'):
                hf_backend.verify_adapter(folder, dict(adapter, adapter_model_sha256='0' * 64))
            (folder / 'adapter_model.safetensors').unlink()
            with self.assertRaisesRegex(ValueError, 'missing'):
                hf_backend.verify_adapter(folder, adapter)
            with self.assertRaisesRegex(ValueError, 'not found'):
                hf_backend.adapter_digests(folder / 'absent')


if __name__ == '__main__':
    unittest.main()
