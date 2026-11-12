"""Synthetic-only tests for Phase-3 evaluation, sealing and baseline equivalence."""
import ast
import copy
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from t4_smoke import phase3_eval as ev, phase3_contract as c, train_phase2 as p2
from colab_notebooks import build_phase3_step2_notebooks as nb
from phase2_analysis import analyze as core


def bridge_fixture():
    implementation = dict(final_test_config_sha256=c.FINAL_CONFIG_SHA, max_infrastructure_retries=1,
        engine_sources={'scorer_v1.py': core.SCORER_SHA256}, engine_code_sha256='a' * 64,
        chat_template_sha256='b' * 64, package_pins=dict(core.STACK_PINS))
    shards = {'synthetic.safetensors': 'c' * 64}
    backend = dict(backend='huggingface', hardware='Tesla T4 (SIMULATED CPU fixture)', capability=[7, 5], gpu_verified=True,
        attention=core.PRESCRIBED_ATTENTION, compute_dtype='float16', quantization=dict(core.PRESCRIBED_QUANTIZATION),
        model_revision=core.QWEN_REVISION, tokenizer_revision=core.QWEN_REVISION, chat_template_sha256='b' * 64,
        adapter=None, base_weight_shards_sha256=shards)
    environment = dict(packages=dict(core.STACK_PINS), fixture='synthetic, no GPU execution')
    run = dict(config=ev.config_for('final_test'), sources=implementation['engine_sources'], attempt_budget=2,
        complete=True, expected=300, completed=300, unresolved=0, environment=environment,
        manifest=dict(mode='phase2_final_test', run_id=c.FINAL_RUN_ID, code_sha256='a' * 64, backend=backend,
            sessions=[dict(backend=backend, environment=environment)],
            execution_sha256=core.digest(dict(backend=backend, environment=environment))))
    return run, implementation, dict(unchanged=dict(base_weight_shards_sha256=shards))


class BridgeTests(unittest.TestCase):
    def test_accept_original_config_and_environment(self):
        run, implementation, binding = bridge_fixture()
        self.assertIs(ev.validate_reused_run(run, implementation, binding), run)

    def test_reject_config_mismatch(self):
        run, implementation, binding = bridge_fixture()
        with self.assertRaisesRegex(ValueError, 'configuration differs'):
            ev.validate_reused_run(run, implementation, binding, '0' * 64)
        run['config']['max_new_tokens'] = 512
        with self.assertRaises(ValueError):
            ev.validate_reused_run(run, implementation, binding)

    def test_reject_foreign_adapter_run(self):
        run, implementation, binding = bridge_fixture()
        run['config']['adapter'] = {'arm': 'EC'}
        with self.assertRaisesRegex(ValueError, 'adapter loaded'):
            ev.validate_reused_run(run, implementation, binding)

    def test_reject_wrong_run_or_incomplete(self):
        for field, bad in [('run_id', 'foreign'), ('complete', False), ('unresolved', 1), ('completed', 299), ('expected', 299)]:
            run, implementation, binding = bridge_fixture()
            (run['manifest'] if field == 'run_id' else run)[field] = bad
            with self.assertRaises(ValueError):
                ev.validate_reused_run(run, implementation, binding)

    def test_reject_environment_shards_and_source_mismatch(self):
        for mutation in ('packages', 'shards', 'source', 'sessions', 'hardware'):
            run, implementation, binding = bridge_fixture()
            if mutation == 'packages':
                run['environment']['packages']['torch'] = 'wrong'
            elif mutation == 'shards':
                binding['unchanged']['base_weight_shards_sha256'] = {'wrong': 'd' * 64}
            elif mutation == 'source':
                run['sources'] = {}
            elif mutation == 'sessions':
                run['manifest']['sessions'] = []
            else:
                run['manifest']['backend']['hardware'] = 'CPU'
            with self.assertRaises(ValueError):
                ev.validate_reused_run(run, implementation, binding)

    def test_phase3_config_digests_are_phase2_exact(self):
        self.assertEqual(core.digest(ev.config_for('final_test')), c.FINAL_CONFIG_SHA)
        self.assertEqual(core.digest(ev.config_for('dev')), c.DEV_CONFIG_SHA)
        with mock.patch.object(ev.old, 'config_for', return_value=dict(mode='changed')):
            with self.assertRaisesRegex(p2.ProtocolError, 'amendment'):
                ev.config_for('final_test')

    def test_byte_binding_hashes_without_json_decoding(self):
        inner = nb.pack({'run_manifest.json': b'{synthetic, deliberately not JSON}',
                         'generation_attempts.jsonl': b'not JSON', 'environment.json': b'private bytes'})
        outer = nb.pack({'nested/base_results.zip': inner})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic.zip'
            path.write_bytes(outer)
            with mock.patch.object(ev.json, 'loads', side_effect=AssertionError('semantic access')):
                result = ev.archive_byte_binding(path, c.sha(outer))
            self.assertEqual(result['inner_members_sha256']['nested/base_results.zip']['environment.json'], c.sha(b'private bytes'))
            with self.assertRaisesRegex(p2.ProtocolError, 'hash mismatch'):
                ev.archive_byte_binding(path, '0' * 64)


class GateTests(unittest.TestCase):
    def test_final_refuses_before_semantic_input_loading(self):
        args = SimpleNamespace(root=Path('/synthetic'), run_dir=Path('/synthetic/run'), split='final_test',
             train_root=Path('/synthetic/train'), adapter_record=Path('/synthetic/train/a/attempt-01/final_adapter.json'),
             adapter_dir=Path('/synthetic/train/a/attempt-01/final_adapter'))
        final = dict(arm='EC', seed=11, attempt=1, adapter_model_sha256='a' * 64, adapter_config_sha256='b' * 64)
        with mock.patch.object(ev.registry, 'locked', return_value=__import__('contextlib').nullcontext()), mock.patch.object(c, 'verify_implementation'), mock.patch.object(ev, 'verify_adapter', return_value=final), \
             mock.patch.object(ev, 'gate', side_effect=p2.ProtocolError('no freeze')), mock.patch.object(ev.old, 'inputs') as loader, \
             mock.patch.object(ev, 'load_reused_baseline') as baseline:
            with self.assertRaisesRegex(p2.ProtocolError, 'no freeze'):
                ev.run_evaluate(args)
            loader.assert_not_called()
            baseline.assert_not_called()

    def test_unfinished_training_cannot_freeze(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(c, 'verify_implementation', return_value=({}, 'a' * 64)):
            with self.assertRaisesRegex(p2.ProtocolError, 'Unsettled'):
                ev.freeze_manifest(tmp, tmp)

    def test_dev_sanity_uses_original_validator(self):
        with mock.patch.object(ev, 'verify_adapter', side_effect=p2.ProtocolError('bad adapter')):
            self.assertIn('bad adapter', ev.dev_sanity_problem('/synthetic', '/synthetic'))

    def test_no_baseline_generation_cli(self):
        with self.assertRaises(SystemExit):
            ev.main(['evaluate', '--split', 'final_test', '--run-dir', '/synthetic'])


class NotebookTests(unittest.TestCase):
    def test_source_inventory_train_dev_targets_no_final(self):
        sources = nb.sources()
        self.assertIn('phase2/dev.v2.json', sources)
        self.assertIn('phase3/targets.v1.json', sources)
        self.assertIn('phase2/train_A.v2.json', sources)
        self.assertFalse(any('final_test' in p.lower() for p in sources))

    def test_payload_uses_synthetic_file_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = ['phase2/dev.v2.json', 'phase3/targets.v1.json', 'phase2/train_A.v2.json']
            for path in files:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes(b'synthetic fixture only')
            with mock.patch.object(nb, 'sources', return_value=files), mock.patch.object(nb, 'contract_bytes', return_value=b'{}'):
                payload = nb.payload('train', root=root)
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                self.assertEqual(set(z.namelist()), set(files + [nb.RUNTIME]))

    def test_final_payload_gate_precedes_test_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(nb, 'sources', return_value=[]), mock.patch.object(nb, 'contract_bytes', return_value=b'{}'), \
                 mock.patch.object(ev, 'gate', side_effect=p2.ProtocolError('no freeze')):
                with self.assertRaisesRegex(p2.ProtocolError, 'no freeze'):
                    nb.payload('final_test', root=root, train_root='/synthetic')

    def test_final_payload_contents_synthetic_after_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = ['phase2/final_test.v3.json', ev.FINAL_ARCHIVE, ev.FROZEN_PATH, 'phase3/IMPLEMENTATION_MANIFEST.md']
            for path in paths:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes(b'synthetic fixture only')
            with mock.patch.object(nb, 'sources', return_value=[]), mock.patch.object(nb, 'contract_bytes', return_value=b'{}'), \
                 mock.patch.object(ev, 'gate', return_value={'S': 3}):
                raw = nb.payload('final_test', root=root, train_root='/synthetic')
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                self.assertEqual(set(z.namelist()), set(paths + [nb.RUNTIME]))

    def test_fixed_final_launcher_syntax_and_flags(self):
        doc = json.loads(nb.render_final())
        code = '\n'.join(''.join(cell['source']) for cell in doc['cells'] if cell['cell_type'] == 'code')
        ast.parse(code)
        for text in ('RECOVER_STALE_LOCK', 'ev.gate', 'load_reused_baseline', 'files.download', 'ADAPTERS_FROZEN.md'):
            self.assertIn(text, code)
        self.assertNotIn('raw_response', code)
        self.assertIn("'train/EVALUATION_REGISTRY.jsonl'", code)

    def test_training_companion_hash_checked_before_setup_cost(self):
        with mock.patch.object(nb, 'payload', return_value=b'synthetic ZIP'):
            doc = json.loads(nb.render_train())
        code = ''.join(doc['cells'][1]['source'])
        check = code.index('assert companion.is_file()')
        self.assertLess(code.index('drive.mount('), check)
        self.assertLess(check, code.index("importlib.metadata.version('torch')"))
        self.assertLess(code.index('== EXPECTED_IMPLEMENTATION_SHA256'), code.index("'pip', 'install'"))
        self.assertIn('MyDrive/Hinglish_Phase3/IMPLEMENTATION_MANIFEST.md', code)

    def test_fixed_training_syntax_and_operator_flags(self):
        with mock.patch.object(nb, 'payload', return_value=b'synthetic ZIP'):
            doc = json.loads(nb.render_train())
        code = '\n'.join(''.join(cell['source']) for cell in doc['cells'] if cell['cell_type'] == 'code')
        ast.parse(code)
        self.assertIn("if pending['kind'] == 'complete':", code)
        for text in ("ARM = pending['arm']", "SEED = pending['seed']", 'Pending plan', 'Evaluation registry lock', 'RECOVER_STALE_WRITER', 'RECOVER_STALE_LOCK', 'run_dev_sanity', 'files.download'):
            self.assertIn(text, code)

class FreezeIntegrationTests(unittest.TestCase):
    def fixture(self, root):
        from t4_smoke import train_phase3 as train
        train_root = root / 'train'
        log = train_root / p2.ATTEMPT_LOG
        (root / 'phase3').mkdir()
        (root / 'phase2').mkdir()
        (root / 'phase3/TARGETS_FROZEN.md').write_text('synthetic target freeze')
        (root / 'phase3/EXPOSURE_ORDER.json').write_text('synthetic order')
        (root / 'phase2/final_test.v3.json').write_text('synthetic test, hash only')
        identity = dict(implementation_manifest_sha256='a'*64, targets_sha256=c.TARGET_SHA,
                       exposure_order_file_sha256=c.file_sha(root / 'phase3/EXPOSURE_ORDER.json'))
        for _ in range(9):
            spec = p2.next_run(p2.plan(p2.read_log(log)))
            keys = {k: spec[k] for k in ('arm', 'seed', 'slot', 'attempt')}
            folder = train.attempt_dir(train_root, spec['arm'], spec['seed'], spec['attempt'])
            adapter = folder / 'final_adapter'
            adapter.mkdir(parents=True)
            (adapter / 'adapter_model.safetensors').write_bytes(b'synthetic adapter ' + str(keys).encode())
            (adapter / 'adapter_config.json').write_bytes(b'{}')
            final = dict(**keys, **identity, **ev.old.adapter_digests(adapter), status='COMPLETE', updates=60,
                steps=dict(windows=60, attempted=60, successful=60, cursor=960), scaler_skips=0,
                saved_parameters_finite=True, resumed=False, valid_for_gate=True,
                base_weight_shards_sha256={'synthetic': 'b'*64}, order_sha256=str(spec['seed']), initial_adapter_sha256='c'*64)
            (folder / 'final_adapter.json').write_text(json.dumps(final))
            (folder / 'train_report.json').write_text(json.dumps(dict(status='COMPLETE')))
            p2.log_event(log, 'start', **keys, identity=identity)
            p2.log_event(log, 'finish', **keys, outcome='valid', detail='synthetic fixture')
        return train_root, identity

    def test_freeze_gate_rechecks_nine_adapters_and_logs(self):
        from t4_smoke import train_phase3 as train
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train_root, identity = self.fixture(root)
            with mock.patch.object(c, 'verify_implementation', return_value=({'base_weight_shards_sha256': {'synthetic': 'b'*64}}, 'a'*64)), \
                 mock.patch.object(ev, 'require_dev_sanity') as sanity, \
                 mock.patch.object(ev, 'verify_dev_bridge', return_value={'sha256': 'd'*64}), \
                 mock.patch.object(train, 'attempt_identity', return_value=identity), \
                 mock.patch.object(ev, 'archive_byte_binding', return_value={'synthetic': 'hashes only'}):
                frozen = ev.freeze_manifest(train_root, root)
                self.assertEqual(frozen['S'], 3)
                self.assertEqual(len(frozen['adapters']), 9)
                self.assertTrue(frozen['confirmatory'])
                self.assertTrue(sanity.called)
                path = root / ev.FROZEN_PATH
                path.write_text('```json\n' + json.dumps(frozen) + '\n```')
                self.assertEqual(ev.gate(root, train_root), frozen)
                folder = train.attempt_dir(train_root, 'EC', 11, 1)
                (folder / 'final_adapter/adapter_model.safetensors').write_bytes(b'tampered')
                with self.assertRaisesRegex(p2.ProtocolError, 'bytes differ'):
                    ev.gate(root, train_root)



class PreflightIntegrationTests(unittest.TestCase):
    def exercise(self, split, missing_peft=False):
        from hinglish_pilot import engine, hf_backend, report
        original = c.block((c.ROOT / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
        pins = dict(original['dependencies']['evaluation'], **original['dependencies']['adapter_evaluation'])
        def version(name):
            if missing_peft and name == 'peft':
                raise engine.importlib.metadata.PackageNotFoundError(name)
            return pins.get(name, 'synthetic installed dependency')
        with tempfile.TemporaryDirectory() as tmp:
            train_root = Path(tmp) / 'train'
            folder = ev.train.attempt_dir(train_root, 'EC', 11, 1)
            final = dict(arm='EC', seed=11, attempt=1, adapter_model_sha256='a'*64,
                         adapter_config_sha256='b'*64, implementation_manifest_sha256='c'*64)
            adapter = ev.old.adapter_record(final)
            _, _, baseline = bridge_fixture()
            backend = bridge_fixture()[0]['manifest']['backend']
            backend.update(adapter=adapter, chat_template_sha256=original['model']['chat_template']['digest'],
                base_weight_shards_sha256=c.block((c.ROOT / 'phase2/ADAPTERS_FROZEN.md').read_bytes())['base_weight_shards_sha256'])
            run_dir = (folder / 'dev_eval' if split == 'dev' else Path(tmp) / 'final_test' / ev.train.run_name('EC', 11))
            args = SimpleNamespace(root=c.ROOT, train_root=train_root, run_dir=run_dir, split=split,
                adapter_record=folder / 'final_adapter.json', adapter_dir=folder / 'final_adapter', recover_stale_lock=False)
            def run(*args, **kwargs):
                return dict(run_id='synthetic-engine-id', attempts=0, status='COMPLETE')
            with mock.patch.object(c, 'verify_implementation'), mock.patch.object(ev, 'verify_adapter', return_value=final), \
                 mock.patch.object(ev, 'gate', return_value=dict(adapters=[adapter])), mock.patch.object(ev, 'load_reused_baseline'), \
                 mock.patch.object(c, 'file_sha', return_value='c'*64), mock.patch.object(p2, 'check_stack'), \
                 mock.patch.object(ev.old, 'inputs', return_value=({}, {})), mock.patch.object(ev.old, 'split_identities'), \
                 mock.patch.object(ev, 'bind_implementation'), mock.patch.object(p2, 'verify_hub_files'), \
                 mock.patch.object(p2, 'verify_chat_template'), mock.patch.object(hf_backend, 'HFBackend', return_value=SimpleNamespace(metadata=backend, tokenizer=None)), \
                 mock.patch.object(engine.importlib.metadata, 'version', side_effect=version), \
                 mock.patch.object(p2, 'execution_problems', wraps=p2.execution_problems) as check, \
                 mock.patch.object(engine, 'run', side_effect=run) as generate, \
                 mock.patch.object(report, 'analyze', return_value=({'status': 'COMPLETE'}, None)), \
                 mock.patch.object(report, 'export', return_value=run_dir.parent / 'synthetic.zip'), \
                 mock.patch.object(ev.old, 'sealed_status', return_value={'status': 'COMPLETE'}):
                if missing_peft:
                    with self.assertRaisesRegex(p2.ProtocolError, 'peft'):
                        ev.run_evaluate(args)
                    generate.assert_not_called()
                else:
                    self.assertEqual(ev.run_evaluate(args), 0)
                    self.assertEqual(check.call_count, 1)
                    self.assertEqual(p2.execution_problems(*check.call_args.args, **check.call_args.kwargs), [])
                    self.assertEqual(check.call_args.args[1]['packages']['peft'], '0.15.2')
                    self.assertEqual(generate.call_args_list[0].kwargs['max_items'], 0)
                    self.assertIsNotNone(ev.registry.records(train_root)[0]['engine_run_id'])

    def test_real_preflight_dev_and_final_with_peft(self):
        for split in ('dev', 'final_test'):
            with self.subTest(split=split):
                self.exercise(split)

    def test_real_preflight_dev_and_final_refuse_missing_peft(self):
        for split in ('dev', 'final_test'):
            with self.subTest(split=split):
                self.exercise(split, missing_peft=True)


class RunningAuthenticationTests(unittest.TestCase):
    def test_modified_executing_copy_cannot_authenticate_pristine_root(self):
        import shutil
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in nb.sources():
                if name.endswith('.py'):
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(c.ROOT / name, target)
            with (root / 't4_smoke/phase3_contract.py').open('a') as stream:
                stream.write('\n# modified executing copy\n')
            command = 'from t4_smoke import phase3_eval as ev; ev.c.verify_implementation(' + repr(str(c.ROOT)) + ')'
            result = subprocess.run([sys.executable, '-B', '-c', command], cwd=root, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('--root differs from executing tree', result.stderr)

    def test_imported_module_outside_tree_refused(self):
        from t4_smoke import labels
        contract = json.loads((c.ROOT / nb.RUNTIME).read_bytes())
        manifest = c.block((c.ROOT / 'phase3/IMPLEMENTATION_MANIFEST.md').read_bytes())
        with mock.patch.object(labels, '__file__', '/tmp/foreign/labels.py'):
            with self.assertRaisesRegex(p2.ProtocolError, 'outside executing tree'):
                c.verify_running_sources(c.ROOT, contract, manifest)

    def test_complete_engine_inventory_required(self):
        contract = json.loads((c.ROOT / nb.RUNTIME).read_bytes())
        del contract['files']['test1_pilot/hinglish_pilot/scorer_v1.py']
        manifest = c.block((c.ROOT / 'phase3/IMPLEMENTATION_MANIFEST.md').read_bytes())
        with self.assertRaisesRegex(p2.ProtocolError, 'inventory differs'):
            c.verify_running_sources(c.ROOT, contract, manifest)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        from t4_smoke import phase3_registry
        self.r = phase3_registry
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.study = Path(self.temp.name)
        self.train_root = self.study / 'train'
        self.adapter = dict(arm='EC', seed=11, attempt=1, adapter_model_sha256='a'*64, adapter_config_sha256='b'*64)
        self.run_dir = self.study / 'final_test' / ev.train.run_name('EC', 11)
        self.freeze_sha = 'f'*64
        self.frozen = dict(adapters=[self.adapter])

    def reserve(self, path=None):
        return self.r.reserve(self.train_root, path or self.run_dir, self.adapter, 'final_test', self.freeze_sha)

    def history(self):
        entry = self.reserve()
        self.run_dir.mkdir(parents=True)
        manifest = dict(run_id='synthetic-id', status='INCOMPLETE', attempts=0,
                        config_sha256='c'*64, evaluation_order=['SYN_E'])
        (self.run_dir / 'run_manifest.json').write_text(json.dumps(manifest))
        (self.run_dir / 'generation_attempts.jsonl').write_bytes(b'')
        self.r.bind(self.train_root, entry, self.run_dir, manifest)
        record = dict(run_id=manifest['run_id'], config_sha256=manifest['config_sha256'],
                      rendering_id='SYN_E', attempt_number=1, status='generated')
        record['record_sha256'] = core.digest(record)
        (self.run_dir / 'journal').mkdir()
        (self.run_dir / 'journal/001.json').write_text(json.dumps(record))
        manifest.update(status='COMPLETE', attempts=1)
        (self.run_dir / 'run_manifest.json').write_text(json.dumps(manifest))
        (self.run_dir / 'generation_attempts.jsonl').write_text(json.dumps(record) + '\n')
        members = {n: (self.run_dir / n).read_bytes() for n in ('run_manifest.json', 'generation_attempts.jsonl')}
        members['checksums.sha256'] = ''.join(c.sha(b) + '  ' + n + '\n' for n, b in members.items()).encode()
        self.archive = self.run_dir.parent / (self.run_dir.name + '_results.zip')
        self.archive.write_bytes(nb.pack(members))
        return manifest

    def reconcile(self):
        return self.r.reconcile(self.train_root, self.run_dir.parent, self.frozen, self.freeze_sha)

    def test_second_directory_same_adapter_split_refused(self):
        with self.r.locked(self.train_root):
            self.reserve()
            with self.assertRaisesRegex(p2.ProtocolError, 'another directory'):
                self.reserve(self.study / 'different')

    def test_recovery_reuses_registered_journal(self):
        manifest = self.history()
        with self.r.locked(self.train_root):
            self.assertEqual(self.reserve()['engine_run_id'], manifest['run_id'])
            (self.run_dir / 'journal/001.json').unlink()
            with self.assertRaisesRegex(p2.ProtocolError, 'lost attempts'):
                self.reserve()

    def test_recovery_rejects_missing_or_substituted_run(self):
        for substitute in (False, True):
            with self.subTest(substitute=substitute):
                if not (self.train_root / self.r.NAME).exists():
                    manifest = self.history()
                path = self.run_dir / 'run_manifest.json'
                if substitute:
                    path.write_text(json.dumps(dict(manifest, run_id='replacement')))
                else:
                    path.unlink()
                with self.assertRaisesRegex(p2.ProtocolError, 'reuse the registered journal'):
                    self.reserve()

    def test_lock_excludes_second_evaluator(self):
        with self.r.locked(self.train_root):
            with self.assertRaisesRegex(p2.Refused, 'locked'):
                with self.r.locked(self.train_root):
                    self.fail('second writer entered')

    def test_bind_refuses_unregistered_prior_generations(self):
        entry = self.reserve()
        with self.assertRaisesRegex(p2.ProtocolError, 'Unbound generation'):
            self.r.bind(self.train_root, entry, self.run_dir, dict(run_id='x', attempts=1))

    def test_analysis_reconciles_all_registered_histories(self):
        self.history()
        rows = self.reconcile()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['engine_run_id'], 'synthetic-id')
        self.assertEqual(rows[0]['freeze_sha256'], self.freeze_sha)

    def test_analysis_refuses_abandoned_registered_history(self):
        self.history()
        adapter = dict(self.adapter, arm='ER')
        folder = ev.train.attempt_dir(self.train_root, 'ER', 11, 1) / 'dev_eval'
        self.r.reserve(self.train_root, folder, adapter, 'dev', 'd'*64)
        with self.assertRaisesRegex(p2.ProtocolError, 'Unresolved registered'):
            self.reconcile()

    def test_analysis_refuses_unregistered_history(self):
        self.history()
        extra = self.study / 'abandoned'
        extra.mkdir()
        (extra / 'run_manifest.json').write_text('{}')
        with self.assertRaisesRegex(p2.ProtocolError, 'Unregistered or extra evaluation history'):
            self.reconcile()

    def test_analysis_refuses_orphan_journal(self):
        self.history()
        (self.study / 'orphan/journal').mkdir(parents=True)
        with self.assertRaisesRegex(p2.ProtocolError, 'Unregistered or extra evaluation history'):
            self.reconcile()

    def test_analysis_refuses_extra_export(self):
        self.history()
        (self.study / 'extra_results.zip').write_bytes(b'not selected by operator')
        with self.assertRaisesRegex(p2.ProtocolError, 'extra evaluation export'):
            self.reconcile()

    def test_analysis_refuses_export_omitting_journal_attempt(self):
        self.history()
        (self.run_dir / 'generation_attempts.jsonl').write_bytes(b'')
        with self.assertRaisesRegex(p2.ProtocolError, 'omits registered attempts'):
            self.reconcile()

    def test_freeze_change_and_unregistered_existing_directory_refused(self):
        self.reserve()
        with self.assertRaisesRegex(p2.ProtocolError, 'freeze differs'):
            self.r.reserve(self.train_root, self.run_dir, self.adapter, 'final_test', 'wrong')
        other = dict(self.adapter, arm='ER')
        folder = self.study / 'final_test' / ev.train.run_name('ER', 11)
        folder.mkdir(parents=True)
        with self.assertRaisesRegex(p2.ProtocolError, 'Unregistered evaluation history'):
            self.r.reserve(self.train_root, folder, other, 'final_test', self.freeze_sha)


if __name__ == '__main__':
    unittest.main()
