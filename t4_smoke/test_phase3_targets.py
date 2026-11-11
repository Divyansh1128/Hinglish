"""CPU-only synthetic/TRAIN fixtures. No held-out file parsing or model downloads."""
import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from t4_smoke import phase3_targets as pt


class Tokenizer:
    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(tokenize=False, add_generation_prompt=True, enable_thinking=False)
        return 'prompt ' + messages[-1]['content']

    def encode(self, text, **kwargs):
        assert kwargs == dict(add_special_tokens=False, truncation=False)
        if text.endswith('<|im_end|>'):
            return [ord(c) for c in text[:-10]] + [151645]
        return [ord(c) for c in text]


def family(index=0):
    return dict(family_id=f'TRAIN{index:03d}', source_family_id=f'SRC{index:03d}', template_group_id=f'TPL{index:03d}',
                split_role='CONFIRM_TRAIN', gold=dict(value='2', unit='', aliases=[], unit_omission_allowed=True),
                forms={f: dict(text=f'{f} question {index}', rendering_id=f'TRAIN{index:03d}_{f}') for f in 'ERC'})


def output(f, text='FINAL: 2', **kwargs):
    return dict(family_id=f['family_id'], rendering_id=f['forms']['E']['rendering_id'], form='E', status='generated',
                raw_response=text, truncated=False, **kwargs)


class Backend:
    metadata = dict(backend='fixture', model_revision=pt.REVISION)

    def __init__(self, failures=()):
        self.failures = list(failures)
        self.calls = []

    def prepare(self, text, config):
        return dict(rendered_prompt=text, input_tokens=12)

    def generate(self, prepared, config, seed):
        self.calls.append((prepared, config, seed))
        if self.failures:
            error = self.failures.pop(0)
            if error:
                raise error
        return dict(raw_response='FINAL: 2', raw_response_with_special_tokens='FINAL: 2<|im_end|>',
                    raw_token_ids=[1, 2, 151645], truncated=False, output_tokens=3)


class GateTests(unittest.TestCase):
    def check_candidate(self, text='FINAL: 2', **kwargs):
        f = kwargs.pop('family', family())
        return pt.candidate(f, output(f, text), Tokenizer(), **kwargs)

    def test_strict_scorer_and_terminal(self):
        self.assertTrue(self.check_candidate()['accepted'])
        self.assertEqual(self.check_candidate('FINAL: 3')['failure_reasons'], ['strict_incorrect'])
        for text in ('No answer', 'FINAL: 2\nDone', 'FINAL: 2\nFINAL: 2', 'FINAL: nonsense', 'FINAL: 2 apples'):
            self.assertIn('invalid_terminal_final', self.check_candidate(text)['failure_reasons'])

    def test_truncation_is_separate(self):
        f = family()
        out = output(f)
        out['truncated'] = True
        row = pt.candidate(f, out, Tokenizer())
        self.assertEqual(row['failure_reasons'], ['strict_incorrect', 'truncated'])

    def test_devanagari_all_three_blocks(self):
        for char in ('ह', '\ua8e0', '\U00011b00'):
            self.assertIn('devanagari', self.check_candidate(char + '\nFINAL: 2')['failure_reasons'])

    def test_word_list_exact(self):
        self.assertEqual(pt.flagged_words('the do hair chair nahiX'), [])
        self.assertEqual(pt.flagged_words('HAI, (hai); aur-hain'), ['aur', 'hai', 'hain'])
        self.assertEqual(len(pt.HINDI_WORDS), 31)
        self.assertEqual(pt.flagged_words(' '.join(pt.HINDI_WORDS)), sorted(pt.HINDI_WORDS))

    def test_language_decisions(self):
        for decision, reason in ((None, 'language_review_pending'), ('fail', 'language_fail'), ('uncertain', 'language_uncertain')):
            self.assertIn(reason, self.check_candidate('hai\nFINAL: 2', review=decision)['failure_reasons'])
        self.assertTrue(self.check_candidate('Hai is a name.\nFINAL: 2', review='pass')['accepted'])

    def test_all_form_length_overlaps_other_failures(self):
        f = family()
        f['forms']['R']['text'] = 'R' * 1024
        f['forms']['C']['text'] = 'C' * 1024
        reasons = self.check_candidate('FINAL: 3', family=f)['failure_reasons']
        self.assertEqual(reasons, ['strict_incorrect', 'overlength_R', 'overlength_C'])

    def test_length_boundary(self):
        f = family()
        target_len = len(Tokenizer().encode('FINAL: 2<|im_end|>', add_special_tokens=False, truncation=False))
        f['forms']['E']['text'] = 'x' * (1024 - len('prompt ') - target_len)
        self.assertTrue(self.check_candidate(family=f)['accepted'])
        f['forms']['E']['text'] += 'x'
        self.assertIn('overlength_E', self.check_candidate(family=f)['failure_reasons'])

    def test_exact_text_and_target_hash(self):
        text = '  There are two items.\nFINAL: 2\n\n'
        row = self.check_candidate(text)
        self.assertEqual(row['candidate_output'], text)
        self.assertEqual(row['target_token_ids_sha256'], pt.digest(Tokenizer().encode(text + '<|im_end|>', add_special_tokens=False, truncation=False)))
        self.assertEqual(row['text_sha256'], pt.sha(text.encode()))

    def test_bad_terminal_id_is_protocol_error(self):
        class BadTokenizer(Tokenizer):
            def encode(self, text, **kwargs):
                return [3]
        with self.assertRaisesRegex(ValueError, '151645'):
            pt.candidate(family(), output(family()), BadTokenizer())

    def test_target_identity_assertion(self):
        with mock.patch.object(pt.labels, 'assert_matched_targets', side_effect=AssertionError('different')):
            with self.assertRaises(AssertionError):
                self.check_candidate()

    def test_explanation_status_descriptive_only(self):
        for text, status in [('FINAL: 2', 'answer only'), ('Total: 1+1=2\nFINAL: 2', 'labelled equations only'),
                             ('There are two items.\nFINAL: 2', 'explanatory proposition')]:
            row = self.check_candidate(text)
            self.assertEqual(row['explanation_status'], status)
            self.assertTrue(row['accepted'])

    def test_q_threshold_and_pending(self):
        families = [family(i) for i in range(160)]
        for good, branch in ((119, 'halt'), (120, 'proceed'), (160, 'proceed')):
            selection, sheet = pt.select_records(families, [output(f, 'FINAL: 2' if i < good else 'FINAL: 3') for i, f in enumerate(families)], Tokenizer())
            self.assertEqual((selection['Q'], selection['branch']), (good, branch))
            self.assertEqual(len(selection['families']), 160)
            self.assertEqual(sheet, [])
        selection, sheet = pt.select_records([family()], [output(family(), 'hai\nFINAL: 2')], Tokenizer())
        self.assertEqual(selection['Q_status'], 'provisional_lower_bound')
        self.assertEqual(list(sheet[0]), pt.REVIEW_FIELDS)
        self.assertNotIn('gold', sheet[0])

    def test_incomplete_foreign_and_duplicate_generations_refused(self):
        for outputs in ([], [output(family()), output(family())], [output(family(1))]):
            with self.assertRaises(ValueError):
                pt.select_records([family()], outputs, Tokenizer())

    def test_flagged_sheet_contains_only_flags_including_other_failures(self):
        families = [family(i) for i in range(3)]
        _, sheet = pt.select_records(families, [output(families[0]), output(families[1], 'hai\nFINAL: 3'), output(families[2], 'ह hai\nFINAL: 2')], Tokenizer())
        self.assertEqual([r['family_id'] for r in sheet], [families[1]['family_id']])


class JournalTests(unittest.TestCase):
    def run_fake(self, folder, backend, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return pt.generate_run(folder, [family(i) for i in range(3)], backend, 'binding', **kwargs)

    def test_resume_never_regenerates_success(self):
        with tempfile.TemporaryDirectory() as temp:
            backend = Backend()
            first = self.run_fake(temp, backend, max_items=1)
            self.assertEqual(first['completed'], 1)
            record = next((Path(temp) / 'journal').glob('*.json')).read_bytes()
            second = self.run_fake(temp, backend)
            self.assertEqual((second['completed'], len(backend.calls)), (3, 3))
            self.assertIn(record, [p.read_bytes() for p in (Path(temp) / 'journal').glob('*.json')])
            self.run_fake(temp, backend)
            self.assertEqual(len(backend.calls), 3)
            self.assertEqual(len((Path(temp) / 'process_launches.jsonl').read_text().splitlines()), 3)

    def test_one_infrastructure_retry_max(self):
        with tempfile.TemporaryDirectory() as temp:
            backend = Backend([OSError(), OSError()])
            manifest = self.run_fake(temp, backend)
            self.assertEqual(manifest['status'], 'INCOMPLETE')
            self.assertEqual(len(backend.calls), 4)  # failed twice plus two resolved
            self.run_fake(temp, backend)
            self.assertEqual(len(backend.calls), 4)

    def test_oom_never_retries(self):
        class OutOfMemoryError(RuntimeError):
            pass
        with tempfile.TemporaryDirectory() as temp:
            backend = Backend([OutOfMemoryError()])
            self.run_fake(temp, backend)
            self.run_fake(temp, backend)
            self.assertEqual(len(backend.calls), 3)  # first OOM plus other two

    def test_protocol_failure_halts_and_cannot_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            backend = Backend([TypeError('bug')])
            with self.assertRaises(TypeError):
                self.run_fake(temp, backend)
            with self.assertRaisesRegex(ValueError, 'Prior protocol'):
                self.run_fake(temp, backend)
            self.assertEqual(len(backend.calls), 1)

    def test_lock_and_explicit_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = Path(temp) / 'RUNNING.lock'
            lock.write_text('old')
            with self.assertRaises(ValueError):
                self.run_fake(temp, Backend())
            self.run_fake(temp, Backend(), recover=True)
            self.assertIn('stale_lock_recovered', (Path(temp) / 'process_launches.jsonl').read_text())
            self.assertFalse(lock.exists())

    def test_corrupt_journal_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            self.run_fake(temp, Backend())
            path = next((Path(temp) / 'journal').glob('*.json'))
            row = json.loads(path.read_bytes())
            row['raw_response'] = 'changed'
            path.write_text(json.dumps(row))
            with self.assertRaises(ValueError):
                self.run_fake(temp, Backend())

    def test_snapshot_changes_refuse_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            self.run_fake(temp, Backend())
            (Path(temp) / 'e_inputs.json').write_text('[]')
            with self.assertRaises(ValueError):
                self.run_fake(temp, Backend())

    def test_sealed_export_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'run'
            self.run_fake(folder, Backend())
            with contextlib.redirect_stdout(io.StringIO()):
                archive = pt.sealed_export(folder)
            with zipfile.ZipFile(archive) as z:
                checks = z.read('checksums.sha256').decode().splitlines()
                for line in checks:
                    expected, member = line.split('  ', 1)
                    self.assertEqual(pt.sha(z.read(member)), expected)
                self.assertEqual(len(z.namelist()), len(checks) + 1)


class FreezeTests(unittest.TestCase):
    def selection(self, good=160):
        families = [family(i) for i in range(160)]
        selection, _ = pt.select_records(families, [output(f, 'FINAL: 2' if i < good else 'FINAL: 3') for i, f in enumerate(families)], Tokenizer())
        selection.update(runtime_contract_sha256='binding', run_manifest_sha256='run')
        return selection

    def test_freeze_q_refusal_and_pending(self):
        for selection in (self.selection(119), dict(self.selection(), pending_human_review=1)):
            with self.assertRaises(ValueError):
                pt.freeze(selection, '/unused', review_path='/unused', folder='/unused')

    def test_review_missing_decision_reason_changed_candidate_duplicates(self):
        expected = dict(zip(pt.REVIEW_FIELDS, ['TRAIN000', 'E', 'hai\nFINAL: 2', 'hai', '', '']))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sheet.csv'
            variants = [expected, dict(expected, YOUR_reason='reason'),
                        dict(expected, **{pt.REVIEW_FIELDS[4]: 'pass'}),
                        dict(expected, candidate_output='changed', **{pt.REVIEW_FIELDS[4]: 'pass'}, YOUR_reason='reason')]
            for row in variants:
                pt.write_csv(path, [row], pt.REVIEW_FIELDS)
                with self.assertRaises(ValueError):
                    pt.read_review(path, {'TRAIN000': expected})
            valid = dict(expected, **{pt.REVIEW_FIELDS[4]: 'uncertain'}, YOUR_reason='reason')
            pt.write_csv(path, [valid], pt.REVIEW_FIELDS)
            self.assertEqual(pt.read_review(path, {'TRAIN000': expected}), {'TRAIN000': 'uncertain'})
            pt.write_csv(path, [valid, valid], pt.REVIEW_FIELDS)
            with self.assertRaises(ValueError):
                pt.read_review(path, {'TRAIN000': expected})

    def test_freeze_exact_targets_hashes_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'run'
            folder.mkdir()
            sheet = folder / 'human_return.csv'
            pt.write_csv(sheet, [], pt.REVIEW_FIELDS)
            selection = self.selection(120)
            with contextlib.redirect_stdout(io.StringIO()):
                pt.freeze(selection, root / 'phase3', review_path=sheet, folder=folder)
            raw = (root / 'phase3/targets.v1.json').read_bytes()
            frozen = pt.parse_manifest((root / 'phase3/TARGETS_FROZEN.md').read_bytes())
            self.assertEqual(frozen['targets_sha256'], pt.sha(raw))
            self.assertEqual(len(json.loads(raw)['families']), 120)
            with self.assertRaises(ValueError):
                pt.freeze(selection, root / 'phase3', review_path=sheet, folder=folder)


class PayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('phase3_nb_test', pt.ROOT / 'colab_notebooks/build_phase3_notebooks.py')
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)

    def test_train_hashes_and_e_order(self):
        families = pt.load_train(pt.ROOT)
        self.assertEqual(len(families), 160)
        self.assertEqual({i['form'] for i in pt.e_inputs(families)}, {'E'})
        self.assertEqual(len(set(pt.evaluation_order(families))), 160)
        self.assertEqual(pt.evaluation_order(families), pt.evaluation_order(list(reversed(families))))

    def test_nontrain_and_bad_hash_rejected(self):
        f = family()
        f['split_role'] = 'DEV'
        with self.assertRaises(ValueError):
            pt.e_inputs([f])
        with mock.patch.object(Path, 'read_bytes', return_value=b'[]'):
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                pt.load_train('/fixture')

    def test_payload_allowlist_and_no_heldout_access(self):
        original = Path.read_bytes
        reads = []
        def guarded(path):
            reads.append(str(path))
            self.assertNotIn('/dev.v2.json', str(path))
            self.assertNotIn('/final_test.v3.json', str(path))
            return original(path)
        with mock.patch.object(Path, 'read_bytes', guarded):
            raw = self.builder.payload()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertEqual(set(z.namelist()), set(self.builder.sources()) | {'phase3/runtime_contract.json'})
            self.assertFalse(any('dev.v2.json' in n or 'final_test' in n.lower() for n in z.namelist()))
            data_files = [n for n in z.namelist() if n.startswith('phase2/') and n.endswith('.json')]
            self.assertEqual(set(data_files), set(pt.TRAIN_FILES))
        self.assertTrue(reads)

    def test_notebook_current_and_code_syntax(self):
        self.assertTrue(self.builder.build(check=True))
        nb = json.loads(self.builder.render())
        self.assertEqual(len(nb['cells']), 3)
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                compile(''.join(cell['source']), '<notebook>', 'exec')
        text = self.builder.render().decode()
        for marker in ('Hinglish_Phase3', 'RECOVER_STALE_LOCK', '2.11.0+cu130', 'generate', 'select'):
            self.assertIn(marker, text)

    def test_contract_verifies_and_tampering_refused(self):
        pt.verify_contract(pt.ROOT)
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b'\n' if str(path).endswith('labels.py') else raw
        with mock.patch.object(Path, 'read_bytes', changed):
            with self.assertRaises(ValueError):
                pt.verify_contract(pt.ROOT)

    def test_backend_configuration_matches_frozen_values(self):
        config = pt.backend_config()
        self.assertEqual((config['seed'], config['max_new_tokens'], config['context_limit']), (11, 1024, 2048))
        self.assertEqual(config['model_revision'], pt.REVISION)
        self.assertFalse(config['thinking'])
        self.assertFalse(config['do_sample'])
        self.assertEqual(config['attention_backend'], 'sdpa_math')
        self.assertEqual(config['adapter'], None)

    def test_token_recorder_is_transparent(self):
        tokenizer = mock.Mock()
        tokenizer.decode.return_value = 'unchanged'
        proxy = pt.TokenRecorder(tokenizer)
        self.assertEqual(proxy.decode([1, 2, 151645], skip_special_tokens=True), 'unchanged')
        self.assertEqual(proxy.ids, [1, 2, 151645])
        tokenizer.decode.assert_called_once_with([1, 2, 151645], skip_special_tokens=True)


if __name__ == '__main__':
    unittest.main()
