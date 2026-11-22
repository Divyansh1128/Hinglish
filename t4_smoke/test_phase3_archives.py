"""Synthetic journal and archived ER-s22 interruption regression tests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from t4_smoke import phase3_eval as ev, phase3_archives as a, phase3_contract as c, train_phase2 as p2, train_phase3 as train
from colab_notebooks import build_phase3_step2_notebooks as nb
from phase2_analysis import analyze as core

INCIDENT = c.ROOT / 'results/phase3/train/incidents/ER-s22_dev'


def signed(row):
    row = dict(row)
    row['record_sha256'] = p2.engine_digest({k: v for k, v in row.items() if k != 'record_sha256'})
    return row


class RecoveryTests(unittest.TestCase):
    def fixture(self):
        config = dict(mode='phase2_dev', max_infrastructure_retries=1)
        run = dict(run_id='synthetic', config_sha256=p2.engine_digest(config), attempts=2)
        common = dict(run_id=run['run_id'], config_sha256=run['config_sha256'], rendering_id='SYN-E')
        first = signed(dict(common, attempt_number=1, status='in_progress', infrastructure_failure=True,
                            error_code='interrupted_before_commit', raw_response=None))
        last = signed(dict(common, attempt_number=2, status='generated', raw_response='FINAL: 2', correct=True,
                           model_revision=p2.ts.MODEL_REVISION, mode=config['mode']))
        return run, config, [first, last], [first], ['SYN-E']

    def test_synthetic_acceptance_does_not_mutate_records(self):
        args = self.fixture()
        original = copy.deepcopy(args)
        with mock.patch.object(p2, 'BASELINE_PROMPTS', 1):
            self.assertEqual(a.generation_problems(*args), [])
            self.assertTrue(p2.generation_problems(*args))
        self.assertEqual(args, original)

    def test_narrow_predicate_and_attempt_rules(self):
        for mutation in ('code', 'flag', 'raw', 'missing_raw', 'digest', 'mirror', 'last', 'gap', 'budget', 'foreign', 'retried'):
            with self.subTest(mutation=mutation):
                run, config, journal, errors, order = self.fixture()
                first, last = journal
                if mutation == 'code': first.pop('error_code')
                elif mutation == 'flag': first['infrastructure_failure'] = 1
                elif mutation == 'raw': first['raw_response'] = ''
                elif mutation == 'missing_raw': first.pop('raw_response')
                elif mutation == 'mirror': errors = []
                elif mutation == 'last': journal.pop(); run['attempts'] = 1
                elif mutation == 'gap': last['attempt_number'] = 3
                elif mutation == 'budget': config['max_infrastructure_retries'] = 0
                elif mutation == 'foreign': first['run_id'] = 'foreign'
                elif mutation == 'retried': last.update(status='in_progress', infrastructure_failure=True, error_code='interrupted_before_commit', raw_response=None)
                journal = [signed(r) for r in journal]
                errors = [signed(r) for r in errors]
                if mutation == 'digest': journal[0]['record_sha256'] = '0' * 64
                with mock.patch.object(p2, 'BASELINE_PROMPTS', 1):
                    self.assertTrue(a.generation_problems(run, config, journal, errors, order))

    def test_final_test_loader_requires_300_resolved_with_same_recovery_rule(self):
        run, config, interrupted, errors, _ = self.fixture()
        config['mode'] = 'phase2_final_test'
        run.update(config_sha256=p2.engine_digest(config), attempts=301)
        journal = [signed(dict(interrupted[0], config_sha256=run['config_sha256']))]
        for i in range(300):
            journal.append(signed(dict(interrupted[1], rendering_id=f'SYN-{i}' if i else 'SYN-E',
                attempt_number=1 if i else 2, mode=config['mode'], config_sha256=run['config_sha256'])))
        order = [r['rendering_id'] for r in journal[1:]]
        def members():
            return {name: json.dumps(value).encode() for name, value in [
                ('run_manifest.json', run), ('experiment_config.json', config), ('evaluation_order.json', order)]} | {
                'generation_attempts.jsonl': ''.join(json.dumps(r) + '\n' for r in journal).encode(),
                'errors.jsonl': (json.dumps(journal[0]) + '\n').encode()}
        with mock.patch.object(core, 'load_run', return_value={'complete': True}), \
             mock.patch.object(core, 'read_run_members', side_effect=lambda _: (members(), 'zip')):
            self.assertTrue(a.load_run('synthetic')['complete'])
            journal.pop(1)
            run['attempts'] -= 1
            with self.assertRaises(ValueError):
                a.load_run('synthetic')

    def test_real_incident(self):
        path = INCIDENT / 'dev_eval_results.zip'
        members, _ = core.read_run_members(path)
        args = a.journal_inputs(members)
        manifest = c.block((c.ROOT / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
        final = json.loads((INCIDENT / 'final_adapter.json').read_bytes())
        from t4_smoke import phase2_eval as old
        self.assertEqual(len(p2.baseline_archive_problems(path, args[0], manifest, adapter=old.adapter_record(final))), 2)
        self.assertEqual(a.baseline_archive_problems(path, args[0], manifest, adapter=old.adapter_record(final)), [])
        self.assertTrue(a.load_run(path)['complete'])
        for mutation in ('code', 'last', 'mirror', 'checksum'):
            changed = dict(members)
            run, config, journal, errors, order = copy.deepcopy(args)
            interrupted = next(r for r in journal if r['status'] == 'in_progress')
            if mutation == 'code': interrupted.pop('error_code')
            if mutation == 'last':
                journal = [r for r in journal if not (r['rendering_id'] == interrupted['rendering_id'] and r['status'] == 'generated')]
                run['attempts'] = len(journal)
            journal = [signed(r) for r in journal]
            errors = [r for r in journal if r['status'] != 'generated']
            if mutation == 'mirror': errors = []
            for name, value in [('run_manifest.json', run), ('generation_attempts.jsonl', journal), ('errors.jsonl', errors)]:
                changed[name] = (''.join(json.dumps(r) + '\n' for r in value) if name.endswith('.jsonl') else json.dumps(value)).encode()
            changed['checksums.sha256'] = ''.join(c.sha(blob) + '  ' + name + '\n' for name, blob in sorted(changed.items()) if name != 'checksums.sha256').encode()
            if mutation == 'checksum': changed['environment.json'] += b' '
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / 'changed.zip'
                target.write_bytes(nb.pack(changed))
                self.assertTrue(a.baseline_archive_problems(target, run, manifest, adapter=old.adapter_record(final)))
                with self.assertRaises(ValueError): a.load_run(target)


class ContinuityTests(unittest.TestCase):
    def test_adapter_accepts_only_predecessor_and_amended_release(self):
        final = json.loads((INCIDENT / 'final_adapter.json').read_bytes())
        digests = {k: final[k] for k in ('adapter_model_sha256', 'adapter_config_sha256')}
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(p2, 'attempt_outcome', return_value=('valid', 'fixture')), \
             mock.patch.object(ev.old, 'adapter_digests', return_value=digests):
            folder = Path(tmp)
            for checksum in sorted(c.accepted_implementations()):
                final['implementation_manifest_sha256'] = checksum
                (folder / 'final_adapter.json').write_text(json.dumps(final))
                self.assertEqual(ev.verify_adapter(folder, c.ROOT), final)
            final['implementation_manifest_sha256'] = '0' * 64
            (folder / 'final_adapter.json').write_text(json.dumps(final))
            with self.assertRaisesRegex(ValueError, 'implementation differs'):
                ev.verify_adapter(folder, c.ROOT)

    def test_immutable_trainer_accepts_existing_log_identity(self):
        doc, training_sha = c.verify_implementation()
        _, release_sha = c.verify_implementation(release=True)
        entries = p2.read_log(INCIDENT / 'ATTEMPT_LOG.jsonl')
        identity = train.attempt_identity(c.ROOT, dict(sha256=c.DEV_SHA))
        self.assertEqual(identity, p2.plan(entries)['identity'])
        self.assertEqual(training_sha, doc['training_continuity']['predecessor_sha256'])
        self.assertEqual(release_sha, c.file_sha(c.ROOT / 'phase3/IMPLEMENTATION_MANIFEST.md'))
        self.assertNotEqual(training_sha, release_sha)
        self.assertEqual(c.accepted_implementations(), {training_sha, release_sha})
        self.assertEqual(p2.next_run(p2.plan(entries))['arm'], 'EE')
        self.assertEqual(p2.next_run(p2.plan(entries))['seed'], 22)
        proof = doc['training_continuity']
        for path, checksum in proof['unchanged_files'].items():
            self.assertEqual(c.file_sha(c.ROOT / path), checksum)
        modified = copy.deepcopy(doc)
        modified['files']['t4_smoke/train_phase3.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'continuity broken'):
            c.verify_continuity(c.ROOT, modified)
