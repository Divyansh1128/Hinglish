"""Phase-3 TRAIN only. Uses the frozen Phase-2 trainer, numerics, locks and attempt planner.

python -m t4_smoke.train_phase3 exposure-lists
python -m t4_smoke.train_phase3 train --train-root DRIVE/train --arm EC --seed 11
No partial resume; successful attempts must receive DEV sanity before further training.
"""
import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path
import sys
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from t4_smoke import train_phase2 as p2, train_smoke as ts, labels, protocol
from t4_smoke import phase3_contract as c

require = c.require
RECIPE = dict(p2.RECIPE, study='phase3-self-distillation', families=158, examples_per_arm=316,
              exposure_order_file='phase3/EXPOSURE_ORDER.json',
              data_order='concatenate SHA-256 passes; first 480 visits',
              valid_run='60 successful optimizer steps over 480 visits; no scaler skips or nonfinite values',
              passes=None, updates_per_pass=None,
              family_visits=480, exposure_rule='concatenate SHA-256 passes; first 480 visits')
DRIVE_ROOT = 'Hinglish_Phase3'


def visits(families, seed):
    ids = [f['family_id'] if isinstance(f, dict) else f for f in families]
    require(ids and len(ids) == len(set(ids)), 'Empty or duplicate family list')
    stream, number = [], 1
    while len(stream) < 480:
        stream.extend(p2.pass_order(ids, seed, number))
        number += 1
    return stream[:480]


def run_sequence(families, arm, seed):
    require(arm in p2.ARMS, 'Unknown arm')
    return [(fid, form) for fid in visits(families, seed) for form in ('E', p2.ARMS[arm])]


def exposure_document(root=c.ROOT):
    targets = c.load_targets(root)
    return dict(schema='phase3-exposure-order-1', targets_sha256=c.TARGET_SHA,
                families=sorted(targets), family_visits=480, visits_per_update=8, updates=60,
                rule=RECIPE['exposure_rule'], seeds={str(s): dict(visits=visits(targets, s),
                    counts=dict(sorted(Counter(visits(targets, s)).items())),
                    order_sha256=ts.digest(visits(targets, s))) for s in p2.SLOTS + p2.RESERVE_QUEUE})


def load_data(root=c.ROOT):
    original = p2.phase2_dataset(root)
    targets = c.load_targets(root)
    families = [f for f in original['families'] if f['family_id'] in targets]
    require(len(families) == 158 and {f['family_id'] for f in families} == set(targets), 'TRAIN inclusion mismatch')
    return families, targets


def question(family, form):
    value = family['forms'][form]
    return value['text'] if isinstance(value, dict) else value


def mask_families(families, targets):
    return [dict(f, completion=targets[f['family_id']]['candidate_output'],
                 forms={form: question(f, form) for form in 'ERC'}) for f in families]


def prepare_examples(tokenizer, families, targets):
    examples = {}
    with p2.protocol_assertions('Phase-3 labels'):
        for family in families:
            fid = family['family_id']
            row = targets[fid]
            built = {form: labels.build_example(tokenizer, protocol.INSTRUCTION,
                     question(family, form), row['candidate_output']) for form in ('E', 'R', 'C')}
            labels.assert_matched_targets(built)
            ids = built['E']['labels'][built['E']['boundary_index']:]
            require(ids[-1] == 151645 and len(ids) == row['target_tokens'], 'Terminal/target count mismatch')
            require(p2.engine_digest(ids) == row['target_token_ids_sha256'], 'Frozen target IDs changed')
            require({form: len(e['input_ids']) for form, e in built.items()} == row['lengths'], 'All-form length mismatch')
            duplicate = labels.build_example(tokenizer, protocol.INSTRUCTION, question(family, 'E'), row['candidate_output'])
            require(duplicate == built['E'], 'EE copy mismatch')
            examples[fid] = built
    return examples


def run_name(arm, seed):
    return f'Phase3_Train_{arm}-s{seed}'


def attempt_dir(root, arm, seed, attempt):
    return Path(root) / run_name(arm, seed) / f'attempt-{attempt:02d}'


def recover_stale_writer(root, *, confirmed_no_other_session=False):
    # Reuse lock ownership and log format; resolve Phase-3 folders explicitly.
    if confirmed_no_other_session is not True:
        raise p2.Refused('RECOVER_STALE_WRITER requires confirmation no other session is active')
    root = Path(root)
    holder = p2.read_writer_lock(root)
    pending = p2.open_attempts(p2.plan(p2.read_log(root / p2.ATTEMPT_LOG)))
    root.mkdir(parents=True, exist_ok=True)
    record = dict(event='stale_writer_recovered', at=p2.utc(), stale_lock=holder,
                  operator_confirmed_no_other_session=True, open_attempts=pending)
    with (root / p2.WRITER_RECOVERIES).open('a') as stream:
        stream.write(json.dumps(record, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    for arm, seed, slot, attempt, event in pending:
        folder = attempt_dir(root, arm, seed, attempt)
        reported, detail = p2.attempt_outcome(folder)
        outcome = reported if reported in ('numerical', 'protocol') else 'infrastructure'
        p2.log_event(root / p2.ATTEMPT_LOG, event, arm=arm, seed=seed, slot=slot, attempt=attempt,
                     outcome=outcome, detail='confirmed stale writer: ' + detail, report_sha256=p2.report_sha(folder), recovery=record)
    (root / p2.WRITER_LOCK).unlink(missing_ok=True)


class Phase3Trainer(p2.Phase2Trainer):
    def update(self, number):
        record = super().update(number)
        # Phase-2 pass metadata assumes 160. Preserve the computation, correct the descriptive cursor metadata.
        start, end = record['cursor_before'] // 2, record['cursor_after'] // 2
        record.pop('pass_number', None)
        record['family_visit_range'] = [start, end]
        record['pass_numbers'] = sorted({i // 158 + 1 for i in range(start, end)})
        return record


def attempt_identity(root, baseline):
    _, manifest_sha = c.verify_implementation(root)
    families, _ = load_data(root)
    expected = exposure_document(root)
    actual = json.loads((Path(root) / 'phase3/EXPOSURE_ORDER.json').read_bytes())
    require(actual == expected, 'Frozen exposure lists changed')
    return dict(implementation_manifest_sha256=manifest_sha, targets_sha256=c.TARGET_SHA,
                target_freeze_sha256=c.file_sha(Path(root) / 'phase3/TARGETS_FROZEN.md'),
                exposure_order_file_sha256=c.file_sha(Path(root) / 'phase3/EXPOSURE_ORDER.json'),
                baseline_dev_results_zip_sha256=baseline['sha256'], phase2_manifest_sha256=c.OLD_MANIFEST_SHA,
                recipe_sha256=ts.digest(RECIPE), families_sha256=ts.digest(families),
                model_id=ts.MODEL_ID, model_revision=ts.MODEL_REVISION,
                stack=dict(ts.PINS, torch=ts.TORCH_BUILD))


def train_attempt(spec, out, root, identity, writer_session=None):
    out, root = Path(out), Path(root)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / 'train_report.json'
    report = dict(status='STARTED', **{k: spec[k] for k in ('arm', 'seed', 'slot', 'attempt')},
                  identity=identity, recipe=RECIPE, recipe_sha256=ts.digest(RECIPE), updates=[], events=[], checkpoints=[], resumes=[],
                  steps=dict(windows=60, attempted=0, successful=0, cursor=0), valid_for_gate=False,
                  writer_session=writer_session, **{k: identity[k] for k in ('implementation_manifest_sha256', 'baseline_dev_results_zip_sha256')})
    sampler, trainer, stage = None, None, 'start'
    try:
        ts.write_json(report_path, report)  # durable STARTED before loading anything
        stage = 'verify'
        doc, actual = c.verify_implementation(root)
        require(actual == identity['implementation_manifest_sha256'], 'Manifest changed after attempt start')
        require(attempt_identity(root, dict(sha256=identity['baseline_dev_results_zip_sha256'])) == identity, 'Attempt identity changed')
        old = c.block((root / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
        families, targets = load_data(root)
        report.update(data_sha256=ts.digest(families), order_sha256=ts.digest(visits(families, spec['seed'])),
                      exposure_order_file_sha256=identity['exposure_order_file_sha256'])
        stage = 'setup'
        torch, mismatches = ts.gpu_setup(False)
        require(not mismatches, 'Stack mismatch inside attempt')
        report['environment'] = ts.environment(torch, mismatches)
        sampler = ts.MemorySampler().start()
        report['nvml_sampler_error'] = sampler.error
        stage = 'hub'
        report['hub_files_sha256'] = p2.verify_hub_files(old)
        tokenizer = ts.load_tokenizer()
        report['chat_template_sha256'] = p2.verify_chat_template(tokenizer, old)
        stage = 'labels'
        examples = prepare_examples(tokenizer, families, targets)
        report['mask_audit'] = ts.mask_audit(tokenizer, examples, mask_families(families, targets))
        require(report['mask_audit']['passed'], 'Completion-only mask audit failed')
        sequence = [dict(examples[fid][form], family_id=fid, form=form) for fid, form in run_sequence(families, spec['arm'], spec['seed'])]
        stage = 'model'
        ts.seed_everything(torch, spec['seed'])
        torch.cuda.reset_peak_memory_stats()
        model, trainable, keep, report['model'] = p2.load_model(torch, spec['seed'])
        shards = p2.weight_shard_hashes()
        require(shards == doc['base_weight_shards_sha256'], 'Loaded weight shards differ')
        report['base_weight_shards_sha256'] = shards
        report['load_min_free_bytes'] = min(v for v in (sampler.take(), torch.cuda.mem_get_info()[0]) if v is not None)
        initial = ts.tensors_digest(trainable)
        report['initial_adapter_sha256'] = initial
        trainer = Phase3Trainer(torch, model, trainable, keep, sequence, sampler)
        report['grad_scaler'] = dict(settings=p2.SCALER, state=trainer.scaler.state_dict())
        for u in range(1, 61):
            stage = 'training'
            try:
                report['updates'].append(trainer.update(u))
            except p2.NumericalFailure as error:
                report['failed_update'] = error.record
                raise
            finally:
                report['steps'] = trainer.steps()
            # Preserve Phase-2 checkpoint writes for diagnostics; checkpoints cannot resume training.
            if u % p2.RECIPE['checkpoint_every'] == 0 and u < 60:
                stage = 'checkpoint'
                p2.save_checkpoint(torch, trainer, out, u, sequence[0], report)
            with p2.checkpoint_write('training report'):
                ts.write_json(report_path, report)
        stage = 'final'
        require(trainer.steps() == dict(windows=60, attempted=60, successful=60, cursor=960), 'Invalid final step count')
        final = p2.save_final_adapter(torch, trainer, out)
        final.update(**{k: spec[k] for k in ('arm', 'seed', 'slot', 'attempt')}, status='COMPLETE', updates=60,
                     steps=trainer.steps(), scaler_skips=0, resumed=False, valid_for_gate=True,
                     initial_adapter_sha256=initial, base_model=ts.MODEL_ID, base_revision=ts.MODEL_REVISION,
                     base_weight_shards_sha256=shards, identity_sha256=ts.digest(identity),
                     **identity, order_sha256=report['order_sha256'], data_sha256=report['data_sha256'])
        ts.write_json(out / 'final_adapter.json', final)
        report.update(status='COMPLETE', valid_for_gate=True, final_adapter=final)
    except (Exception, KeyboardInterrupt, SystemExit) as error:
        p2.fail_report(report, report_path, error, stage)
    finally:
        if sampler is not None:
            sampler.stop()
        report['summary'] = ts.summarize_updates(report['updates'], warmup=0, resume_after=0)
        report['events'].append(dict(event='process_end', at=time.time(), status=report['status']))
        ts.write_json(report_path, report)
    return report


def run_train(args):
    from t4_smoke import phase3_eval as ev
    root, train_root = Path(args.root), Path(args.train_root)
    if (root / 'phase3/ADAPTERS_FROZEN.md').exists():
        raise p2.Refused('Adapters already frozen: further training refused')
    if args.recover_stale_writer:
        recover_stale_writer(train_root, confirmed_no_other_session=True)
    with p2.WriterLock(train_root) as writer:
        current = p2.plan(p2.read_log(train_root / p2.ATTEMPT_LOG))
        action = p2.next_run(current)
        if action['kind'] == 'complete':
            return 0
        if (args.arm, args.seed) != (action['arm'], action['seed']):
            raise p2.Refused(f"Plan requires {action['arm']} seed {action['seed']} slot {action['slot']} attempt {action['attempt']}")
        ev.require_dev_sanity(train_root, root)
        baseline = ev.verify_dev_bridge(root)
        identity = attempt_identity(root, baseline)
        require(current['identity'] in (None, identity), 'Configuration differs from prior attempts')
        p2.check_stack()
        out = attempt_dir(train_root, action['arm'], action['seed'], action['attempt'])
        require(not out.exists(), 'Attempt evidence cannot be overwritten')
        keys = {k: action[k] for k in ('arm', 'seed', 'slot', 'attempt')}
        p2.log_event(train_root / p2.ATTEMPT_LOG, 'start', **keys, identity=identity, writer_session=writer.session_id)
        report = train_attempt(action, out, root, identity, writer.session_id)
        require(writer.owned(), 'Writer ownership lost; stale recovery owns outcome')
        outcome, detail = p2.report_outcome(report)
        p2.log_event(train_root / p2.ATTEMPT_LOG, 'finish', **keys, outcome=outcome, detail=detail, report_sha256=p2.report_sha(out))
        return 0 if outcome == 'valid' else p2.EXIT_CODES.get(outcome, 4)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('exposure-lists', 'train', 'plan'):
        sub = commands.add_parser(name)
        sub.add_argument('--root', type=Path, default=c.ROOT)
        if name in ('train', 'plan'):
            sub.add_argument('--train-root', type=Path, required=True)
        if name == 'train':
            sub.add_argument('--arm', choices=list(p2.ARMS), required=True)
            sub.add_argument('--seed', type=int, required=True)
            sub.add_argument('--recover-stale-writer', action='store_true')
    args = parser.parse_args(argv)
    if args.command == 'exposure-lists':
        path = args.root / 'phase3/EXPOSURE_ORDER.json'
        raw = json.dumps(exposure_document(args.root), indent=2) + '\n'
        require(not path.exists() or path.read_text() == raw, 'Exposure freeze already exists and differs')
        path.write_text(raw)
        print(path, c.file_sha(path))
        return 0
    if args.command == 'plan':
        print(p2.describe_plan(p2.plan(p2.read_log(args.train_root / p2.ATTEMPT_LOG))))
        return 0
    try:
        return run_train(args)
    except (p2.Refused, p2.StudyHalted) as error:
        print('REFUSED:', error)
        return 2
    except p2.ProtocolError as error:
        print('PROTOCOL HALT:', error)
        return 4


if __name__ == '__main__':
    raise SystemExit(main())
