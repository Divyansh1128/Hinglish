"""Phase-3 CPU tests: synthetic families, targets, attempts and tokenizers only."""
import copy
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock
from t4_smoke import train_phase3 as train, train_phase2 as p2, phase3_contract as c
from t4_smoke.test_phase3_targets import Tokenizer, family
from t4_smoke import labels, protocol


def target(f, text='  Working.\nFINAL: 2\n\n'):
    built = {form: labels.build_example(Tokenizer(), protocol.INSTRUCTION, f['forms'][form]['text'], text) for form in 'ERC'}
    ids = [v for v in built['E']['labels'] if v != -100]
    return dict(family_id=f['family_id'], candidate_output=text, text_sha256=c.sha(text.encode()),
                target_token_ids_sha256=p2.engine_digest(ids), target_tokens=len(ids),
                lengths={form: len(e['input_ids']) for form, e in built.items()})


class ExposureTests(unittest.TestCase):
    def test_480_balanced_visits_all_seeds(self):
        for n in (120, 121, 158, 159, 160):
            for seed in p2.SLOTS + p2.RESERVE_QUEUE:
                counts = Counter(train.visits([f'F{i:03d}' for i in range(n)], seed))
                self.assertEqual(sum(counts.values()), 480)
                self.assertEqual(len(counts), n)
                self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_matches_phase2_for_160(self):
        families = [f'F{i:03d}' for i in range(160)]
        for s in p2.SLOTS + p2.RESERVE_QUEUE:
            for arm in p2.ARMS:
                self.assertEqual(train.run_sequence(families, arm, s), p2.run_sequence(families, arm, s))

    def test_identical_across_arms_and_exact_pairs(self):
        families = [f'F{i:03d}' for i in range(158)]
        streams = [train.run_sequence(families, arm, 11) for arm in p2.ARMS]
        for arm, stream in zip(p2.ARMS, streams):
            self.assertEqual(len(stream), 960)
            self.assertEqual([fid for fid, _ in stream[::2]], train.visits(families, 11))
            self.assertTrue(all(a == (fid, 'E') and b == (fid, p2.ARMS[arm])
                                for a, b, fid in zip(stream[::2], stream[1::2], train.visits(families, 11))))
        self.assertEqual([fid for fid, _ in streams[0]], [fid for fid, _ in streams[2]])

    def test_partial_pass_crosses_update_boundary(self):
        ids = [f'F{i}' for i in range(158)]
        visits = train.visits(ids, 22)
        self.assertEqual(visits[158:316], p2.pass_order(ids, 22, 2))
        self.assertEqual(visits[474:], p2.pass_order(ids, 22, 4)[:6])
        self.assertEqual(len(visits[152:160]), 8)

    def test_empty_duplicate_and_bad_arm_refused(self):
        for ids in ([], ['x', 'x']):
            with self.assertRaises(p2.ProtocolError):
                train.visits(ids, 11)
        with self.assertRaises(p2.ProtocolError):
            train.run_sequence(['x'], 'XX', 11)

    def test_exposure_freezes_five_lists(self):
        with mock.patch.object(c, 'load_targets', return_value={f'F{i}' : {} for i in range(158)}):
            doc = train.exposure_document()
        self.assertEqual(set(doc['seeds']), {'11', '22', '33', '44', '55'})
        for seed, entry in doc['seeds'].items():
            self.assertEqual(entry['order_sha256'], p2.ts.digest(entry['visits']))
            self.assertEqual(entry['counts'], dict(Counter(entry['visits'])))


class TargetTests(unittest.TestCase):
    def test_exact_text_target_ids_and_ee(self):
        f = family()
        row = target(f)
        built = train.prepare_examples(Tokenizer(), [f], {f['family_id']: row})[f['family_id']]
        self.assertEqual(built['E']['labels'][built['E']['boundary_index']:],
                         Tokenizer().encode(row['candidate_output'] + '<|im_end|>', add_special_tokens=False, truncation=False))
        self.assertEqual(built['E']['labels'][-1], 151645)
        labels.assert_matched_targets(built)

    def test_target_identity_and_length_tampering_refused(self):
        f = family()
        for field, bad in [('target_token_ids_sha256', '0' * 64), ('target_tokens', 0), ('lengths', dict(E=1, R=1, C=1))]:
            row = target(f)
            row[field] = bad
            with self.assertRaises(p2.ProtocolError):
                train.prepare_examples(Tokenizer(), [f], {f['family_id']: row})

    def test_no_truncation(self):
        f = family()
        row = target(f)
        f['forms']['C']['text'] = 'x' * 1100
        with self.assertRaises(p2.ProtocolError):
            train.prepare_examples(Tokenizer(), [f], {f['family_id']: row})

    def test_target_loader_hashes_before_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'phase3').mkdir()
            (root / 'phase3/targets.v1.json').write_bytes(b'not json')
            with self.assertRaisesRegex(p2.ProtocolError, 'SHA-256'):
                c.load_targets(root)

    def test_synthetic_frozen_loader_and_archive_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'phase3').mkdir()
            (root / 'results/phase3/targets').mkdir(parents=True)
            rows = [target(family(i)) for i in range(158)]
            raw = json.dumps(dict(Q=158, families=rows, terminal_marker='<|im_end|>', terminal_id=151645)).encode()
            (root / 'phase3/targets.v1.json').write_bytes(raw)
            archive = root / 'results/phase3/targets/Phase3_Targets_frozen.zip'
            archive.write_bytes(b'synthetic journals and review')
            freeze = dict(targets_sha256=c.sha(raw), Q=158, archive_sha256=c.file_sha(archive))
            (root / 'phase3/TARGETS_FROZEN.md').write_text('```json\n' + json.dumps(freeze) + '\n```')
            with mock.patch.object(c, 'TARGET_SHA', c.sha(raw)):
                self.assertEqual(len(c.load_targets(root)), 158)
                archive.write_bytes(b'edited')
                with self.assertRaisesRegex(p2.ProtocolError, 'archive'):
                    c.load_targets(root)


class PolicyTests(unittest.TestCase):
    def test_run_paths(self):
        self.assertEqual(str(train.attempt_dir('/tmp/train', 'EC', 11, 1)), '/tmp/train/Phase3_Train_EC-s11/attempt-01')
        self.assertEqual(train.DRIVE_ROOT, 'Hinglish_Phase3')

    def test_numerics_and_schedule_reused(self):
        self.assertTrue(issubclass(train.Phase3Trainer, p2.Phase2Trainer))
        for key in ('accumulation', 'updates', 'lr', 'betas', 'eps', 'weight_decay', 'clip'):
            self.assertEqual(train.RECIPE[key], p2.RECIPE[key])

    def test_recovery_requires_explicit_confirmation(self):
        with self.assertRaises(p2.Refused):
            train.recover_stale_writer('/tmp/unused-phase3-test')

    def test_plan_retries_and_reserves_whole_triplet(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / p2.ATTEMPT_LOG
            def finish(outcome):
                action = p2.next_run(p2.plan(p2.read_log(log)))
                keys = {k: action[k] for k in ('arm', 'seed', 'slot', 'attempt')}
                p2.log_event(log, 'start', **keys, identity={'fixture': True})
                p2.log_event(log, 'finish', **keys, outcome=outcome, detail='synthetic')
            finish('valid')  # EC 11 successful, later discarded with entire triplet
            finish('infrastructure')
            action = p2.next_run(p2.plan(p2.read_log(log)))
            self.assertEqual((action['arm'], action['seed'], action['attempt']), ('ER', 11, 2))
            finish('infrastructure')
            action = p2.next_run(p2.plan(p2.read_log(log)))
            self.assertEqual((action['arm'], action['seed'], action['slot']), ('EC', 44, 11))

    def test_numerical_protocol_halt(self):
        for outcome in ('numerical', 'protocol'):
            with tempfile.TemporaryDirectory() as tmp:
                log = Path(tmp) / p2.ATTEMPT_LOG
                fields = dict(arm='EC', seed=11, slot=11, attempt=1)
                p2.log_event(log, 'start', **fields, identity={'fixture': True})
                p2.log_event(log, 'finish', **fields, outcome=outcome, detail='synthetic')
                with self.assertRaises(p2.StudyHalted):
                    p2.next_run(p2.plan(p2.read_log(log)))

    def test_recovery_preserves_protocol_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / p2.ATTEMPT_LOG
            fields = dict(arm='EC', seed=11, slot=11, attempt=1)
            p2.log_event(log, 'start', **fields, identity={'fixture': True})
            folder = train.attempt_dir(tmp, 'EC', 11, 1)
            folder.mkdir(parents=True)
            (folder / 'train_report.json').write_text(json.dumps(dict(status='FAILED', failure_class='protocol', error='synthetic')))
            train.recover_stale_writer(tmp, confirmed_no_other_session=True)
            self.assertTrue(p2.plan(p2.read_log(log))['halted'])
            self.assertTrue((Path(tmp) / p2.WRITER_RECOVERIES).exists())

class EntryGateTests(unittest.TestCase):
    def test_normalized_phase2_training_shape(self):
        f = family()
        row = target(f)
        normalized = dict(f, forms={form: f['forms'][form]['text'] for form in 'ERC'}, completion='old target')
        built = train.prepare_examples(Tokenizer(), [normalized], {f['family_id']: row})
        self.assertEqual(built[f['family_id']]['E']['labels'][-1], 151645)
        self.assertEqual(train.mask_families([normalized], {f['family_id']: row})[0]['completion'], row['candidate_output'])

    def test_missing_dev_evidence_opens_no_attempt(self):
        from types import SimpleNamespace
        from t4_smoke import phase3_eval as ev
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = SimpleNamespace(root=root, train_root=root / 'train', arm='EC', seed=11, recover_stale_writer=False)
            with mock.patch.object(ev, 'verify_dev_bridge', side_effect=p2.Refused('no original DEV evidence')), \
                 mock.patch.object(p2, 'check_stack') as stack:
                with self.assertRaisesRegex(p2.Refused, 'no original DEV'):
                    train.run_train(args)
            stack.assert_not_called()
            self.assertFalse((args.train_root / p2.ATTEMPT_LOG).exists())
            self.assertFalse((args.train_root / p2.WRITER_LOCK).exists())

    def test_stack_refusal_opens_no_attempt(self):
        from types import SimpleNamespace
        from t4_smoke import phase3_eval as ev
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = SimpleNamespace(root=root, train_root=root / 'train', arm='EC', seed=11, recover_stale_writer=False)
            with mock.patch.object(ev, 'verify_dev_bridge', return_value={'sha256': 'x'}), \
                 mock.patch.object(train, 'attempt_identity', return_value={'synthetic': True}), \
                 mock.patch.object(p2, 'check_stack', side_effect=p2.Refused('wrong stack')):
                with self.assertRaisesRegex(p2.Refused, 'wrong stack'):
                    train.run_train(args)
            self.assertFalse((args.train_root / p2.ATTEMPT_LOG).exists())


if __name__ == '__main__':
    unittest.main()
