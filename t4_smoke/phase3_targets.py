"""Phase-3 TRAIN-only self-distillation (§3, §5, §10–11; D053).

No engine globals or validators are patched. HFBackend receives the frozen Phase-2
backend configuration; our run manifest is explicitly phase3_targets, never a
Phase-2 archive. The orchestration uses the engine's lock, selected, attempts,
atomic write, seed-11 shuffle and two-attempt budget. An in-flight record consumes
an attempt, as in Phase 2. No scored response is regenerated; OOM is terminal.

Explanation heuristic (descriptive only): remove FINAL lines; no remaining text
=> answer only; a line containing >=3 ASCII words and one fixed proposition verb
(is/are/was/were/has/have/gives/leaves/remains/need/needs/get/gets) => explanatory
proposition; everything else => labelled equations only. It is not a quality gate.
Token-ID hashes use engine.data.digest on the integer list. Text is never stripped.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import random
import re
import sys
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for parent in (ROOT, ROOT / 'test1_pilot'):
    if (parent / 'hinglish_pilot').is_dir():
        sys.path.insert(0, str(parent))
from hinglish_pilot import engine as eng
from hinglish_pilot import hf_backend as hf
from hinglish_pilot.data import digest, require, validate_gold
from hinglish_pilot.scorer_v1 import score_response, SCORER_VERSION
try:
    from . import labels, protocol
except ImportError:
    import labels
    import protocol

TRAIN_FILES = {
    'phase2/train_A.v2.json': 'b9656a8c41af2a795bce9c131efc6a5efc652df78368d14fb7720fd985883666',
    'phase2/train_B.v2.json': 'c975fe12459df6160effc5aeb0087f94666ba0b49778c3d827a67bb923ff35bd',
}
REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
HINDI_WORDS = tuple('hai hain ka ki ke ko mein aur se kitne kitna kitni bacha bache liye paas waala waali wale nahi kya toh yeh woh usne uske unke isliye kul rupaye rupye'.split())
FLAG_RULE = 'lowercase; split on [^a-z]+; intersect HINDI_WORDS; sorted unique hits'
EXPLANATION_RULE = 'Non-FINAL lines: empty => answer only; >=3 ASCII words plus is/are/was/were/has/have/gives/leaves/remains/need/needs/get/gets => explanatory proposition; otherwise labelled equations only. Descriptive, never a gate.'
REVIEW_FIELDS = ['family_id', 'e_text', 'candidate_output', 'flagged_words', 'YOUR_decision pass/fail/uncertain', 'YOUR_reason']
SOURCE = 'unchanged-Qwen3-4B-E-self-distillation'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_manifest(raw):
    return json.loads(raw.decode().split('```json\n', 1)[1].split('\n```', 1)[0])


def load_train(root):
    families = []
    for path, expected in TRAIN_FILES.items():
        raw = (Path(root) / path).read_bytes()
        require(sha(raw) == expected, f'TRAIN hash mismatch: {path}')
        batch = json.loads(raw)
        require(len(batch) == 80, 'Expected 80 families per TRAIN file')
        families += batch
    require(len(families) == 160, 'Expected 160 TRAIN families')
    seen = set()
    for family in families:
        require(family['split_role'] == 'CONFIRM_TRAIN', 'Non-TRAIN payload forbidden')
        require(set(family['forms']) == {'E', 'R', 'C'}, 'Missing TRAIN forms')
        validate_gold(family['gold'])
        for key in ('family_id', 'source_family_id', 'template_group_id'):
            value = family[key]
            require(value not in seen, 'Repeated TRAIN identity')
            seen.add(value)
        require(not re.search(r'<\|[^>]+\|>|/no_think|/think', family['forms']['E']['text']), 'Control marker in E')
    return sorted(families, key=lambda f: f['family_id'])


def e_inputs(families):
    require(all(f['split_role'] == 'CONFIRM_TRAIN' for f in families), 'Only TRAIN permitted')
    return [{'family_id': f['family_id'], 'rendering_id': f['forms']['E']['rendering_id'],
             'form': 'E', 'input_text': f['forms']['E']['text']} for f in families]


def evaluation_order(families):
    order = sorted(x['rendering_id'] for x in e_inputs(families))
    random.Random(11).shuffle(order)
    return order


def backend_config():
    # Transport configuration only; this does not authorize engine.run on TRAIN.
    config = eng.default_config('phase2_dev', 'Qwen/Qwen3-4B')
    config.update(model_revision=REVISION, tokenizer_revision=REVISION)
    eng.validate_config(config)
    return config


def verify_contract(root):
    root = Path(root)
    raw = (root / 'phase3/runtime_contract.json').read_bytes()
    contract = json.loads(raw)
    require(contract['schema'] == 'phase3-target-runtime-1', 'Wrong runtime contract')
    require(contract['backend_config'] == backend_config(), 'Generation configuration changed')
    require(contract['word_list'] == list(HINDI_WORDS) and contract['flag_rule'] == FLAG_RULE
            and contract['explanation_rule'] == EXPLANATION_RULE, 'Selection rules changed')
    for path, expected in contract['files'].items():
        require(not Path(path).is_absolute() and '..' not in Path(path).parts, 'Unsafe contract path')
        require(sha((root / path).read_bytes()) == expected, f'Runtime file changed: {path}')
    old = parse_manifest((root / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
    # Authenticate the frozen code against its original manifest without opening held-out files.
    for path, expected in old['files'].items():
        if path.startswith(('test1_pilot/hinglish_pilot/', 't4_smoke/labels.py', 't4_smoke/protocol.py')):
            require(sha((root / path).read_bytes()) == expected, f'Phase-2 code changed: {path}')
    return contract, sha(raw), old


def verify_model_files(old):
    from huggingface_hub import hf_hub_download
    found = {}
    for name, expected in old['model']['hub_files'].items():
        path = hf_hub_download('Qwen/Qwen3-4B', name, revision=REVISION, token=os.environ.get('HF_TOKEN') or None)
        found[name] = hf.file_sha256(path)
        require(found[name] == expected, f'Pinned model file mismatch: {name}')
    return found


def verify_tokenizer(tokenizer, old):
    template = tokenizer.chat_template
    require(sha(template.encode()) == old['model']['chat_template']['utf8_sha256'], 'Chat template changed')
    require(tokenizer.pad_token_id == 151643, 'PAD changed')


class TokenRecorder:
    """Transparent tokenizer proxy recording the IDs already passed to decode."""
    def __init__(self, tokenizer):
        self.inner = tokenizer
        self.ids = None

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def __call__(self, *args, **kwargs):
        return self.inner(*args, **kwargs)

    def decode(self, ids, **kwargs):
        self.ids = list(ids)
        return self.inner.decode(ids, **kwargs)


class RecordingBackend(hf.HFBackend):
    def generate(self, prepared, config, seed):
        tokenizer = self.tokenizer
        recorder = TokenRecorder(tokenizer)
        self.tokenizer = recorder
        try:
            result = super().generate(prepared, config, seed)
            require(recorder.ids is not None, 'Missing raw generated IDs')
            result['raw_token_ids'] = recorder.ids
            return result
        finally:
            self.tokenizer = tokenizer


def append_event(folder, event):
    with (Path(folder) / 'process_launches.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(at=eng.utc(), **event), sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def generate_run(folder, families, backend, binding, *, recover=False, max_items=None, evidence=None):
    """CPU-testable orchestration; production entry validates backend and runtime first."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if recover and (folder / 'RUNNING.lock').exists():
        created = (folder / 'RUNNING.lock').read_text()
        eng.recover_lock(folder, confirmed_no_active_writer=True)
        append_event(folder, {'event': 'stale_lock_recovered', 'lock_created_at': created,
                              'operator_confirmed_no_active_writer': True})
    config = backend_config()
    items = {i['rendering_id']: i for i in e_inputs(families)}
    gold = {f['forms']['E']['rendering_id']: f['gold'] for f in families}
    order = evaluation_order(families)
    identity = dict(config_sha256=digest(config), train_sha256=digest(families),
                    implementation_sha256=binding, code_sha256=eng.code_hash(),
                    execution_sha256=digest({'backend': backend.metadata, 'environment': eng.environment(eng.PHASE2_PACKAGES)}))
    with eng.lock(folder):
        append_event(folder, {'event': 'process_launch', 'session_id': uuid.uuid4().hex})
        for name, raw in (evidence or {}).items():
            target = folder / 'frozen_source' / name
            require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe evidence path')
            if target.exists():
                require(target.read_bytes() == raw, 'Runtime evidence changed')
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        if (folder / 'run_manifest.json').exists():
            manifest = eng.read(folder / 'run_manifest.json')
            require(all(manifest[k] == v for k, v in identity.items()), 'Resume identity changed')
            require(manifest['evaluation_order'] == order == eng.read(folder / 'evaluation_order.json'), 'Order changed')
            require(eng.read(folder / 'e_inputs.json') == list(items.values()), 'E input snapshot changed')
        else:
            require(not (folder / 'journal').exists(), 'Orphan journal')
            manifest = dict(identity, schema='phase3-target-run-1', mode='phase3_targets', run_id='phase3_targets-' + uuid.uuid4().hex,
                            created_at=eng.utc(), evaluation_order=order, expected=len(order), backend=backend.metadata,
                            backend_config_note='Frozen Phase-2 backend transport config; TRAIN-only orchestration, not a Phase-2 evaluation',
                            status='INCOMPLETE')
            eng.write(folder / 'run_manifest.json', manifest)
            eng.write(folder / 'evaluation_order.json', order)
            eng.write(folder / 'e_inputs.json', list(items.values()))
            eng.write(folder / 'experiment_config.json', config)
            eng.write(folder / 'environment.json', eng.environment(eng.PHASE2_PACKAGES))
        require(eng.read(folder / 'experiment_config.json') == config, 'Stored configuration changed')
        prepared = {rid: backend.prepare(items[rid]['input_text'], config) for rid in order}
        journal, done = eng.selected(folder)
        complete = {x['rendering_id'] for x in done}
        new = 0
        try:
            for index, rid in enumerate(order):
                if rid in complete:
                    continue
                if max_items is not None and new >= max_items:
                    break
                history = [x for x in journal if x['rendering_id'] == rid]
                require(len(history) <= 2, 'Attempt budget exceeded')
                require(not any(x['status'] == 'protocol_failure' for x in history), 'Prior protocol failure: halt for amendment')
                require(all(x['status'] in ('in_progress', 'infrastructure_failure') for x in history), 'Unresolved non-infrastructure history')
                if history and history[-1].get('error_code') == 'out_of_memory':
                    continue
                while len(history) < 2:
                    number = len(history) + 1
                    record = dict(items[rid], **prepared[rid], run_id=manifest['run_id'], config_sha256=identity['config_sha256'],
                                  attempt_number=number, generation_seed=11 + index, started_at=eng.utc(),
                                  status='in_progress', error_code='interrupted_before_commit', infrastructure_failure=True,
                                  retry_reason=None if number == 1 else 'previous_infrastructure_failure')
                    path = folder / 'journal' / f'{rid}.{number:02d}.json'
                    def commit():
                        eng.write(path, dict(record, record_sha256=digest(record)))
                    commit()
                    stop = False
                    protocol_error = None
                    try:
                        result = backend.generate(prepared[rid], config, 11 + index)
                        require(isinstance(result['raw_response'], str) and type(result['truncated']) is bool, 'Backend output contract')
                        require(isinstance(result['raw_token_ids'], list), 'Raw token record required')
                        record.update(result, status='generated', infrastructure_failure=False, error_code=None)
                        record.update(score_response(result['raw_response'], gold[rid], result['truncated']))
                    except BaseException as error:
                        oom = 'OutOfMemory' in type(error).__name__
                        infrastructure = isinstance(error, (OSError, ConnectionError, TimeoutError, KeyboardInterrupt)) or oom
                        protocol_error = None if infrastructure else error
                        record.update(status='infrastructure_failure' if infrastructure else 'protocol_failure',
                                      error_code='out_of_memory' if oom else ('generation_failed' if infrastructure else 'protocol_failure'),
                                      exception_class=type(error).__name__, infrastructure_failure=infrastructure)
                        stop = oom or isinstance(error, KeyboardInterrupt) or not infrastructure
                    record['finished_at'] = eng.utc()
                    commit()
                    journal.append(dict(record, record_sha256=digest(record)))
                    history.append(record)
                    if protocol_error is not None:
                        raise protocol_error
                    if record['status'] == 'generated':
                        complete.add(rid)
                        new += 1
                        print(f'Generated {len(complete)}/{len(order)}', flush=True)
                        break
                    if stop:
                        return manifest
        finally:
            journal, done = eng.selected(folder)
            manifest.update(status='COMPLETE' if len(done) == len(order) else 'INCOMPLETE', completed=len(done),
                            unresolved=len(order) - len(done), attempts=len(journal), updated_at=eng.utc())
            eng.write(folder / 'run_manifest.json', manifest)
            eng.jsonl(folder / 'generation_attempts.jsonl', journal)
            eng.jsonl(folder / 'outputs.jsonl', done)
    return manifest


def flagged_words(text):
    return sorted(set(re.split('[^a-z]+', text.lower())) & set(HINDI_WORDS))


def explanation_status(text):
    lines = [line for line in text.splitlines() if line.strip() and not re.match(r'^\s*FINAL\s*:', line, re.I)]
    if not lines:
        return 'answer only'
    verbs = set('is are was were has have gives leaves remains need needs get gets'.split())
    if any(len(words := re.findall('[a-z]+', line.lower())) >= 3 and set(words) & verbs for line in lines):
        return 'explanatory proposition'
    return 'labelled equations only'


def candidate(family, output, tokenizer, review=None):
    text = output['raw_response']
    truncated = output['truncated']
    strict = score_response(text, family['gold'], truncated)
    terminal = score_response(text, family['gold'], False)['invalid_reason'] is None
    failures = []
    if not strict['correct']:
        failures.append('strict_incorrect')
    if truncated:
        failures.append('truncated')
    if not terminal:
        failures.append('invalid_terminal_final')
    devanagari = bool(re.search('[\u0900-\u097f\ua8e0-\ua8ff\U00011b00-\U00011b5f]', text))
    if devanagari:
        failures.append('devanagari')
    flags = [] if devanagari else flagged_words(text)
    decision = review or ''
    if flags and decision != 'pass':
        failures.append({'fail': 'language_fail', 'uncertain': 'language_uncertain'}.get(decision, 'language_review_pending'))
    # Build without truncation to measure every form even if another gate failed.
    examples = {form: labels.build_example(tokenizer, protocol.INSTRUCTION, family['forms'][form]['text'], text,
                                           max_length=sys.maxsize) for form in ('E', 'R', 'C')}
    labels.assert_matched_targets(examples)
    target_ids = [t for t in examples['E']['labels'] if t != -100]
    require(target_ids and target_ids[-1] == 151645, 'Last supervised ID must be 151645')
    ee_copy = labels.build_example(tokenizer, protocol.INSTRUCTION, family['forms']['E']['text'], text, max_length=sys.maxsize)
    require(ee_copy['labels'] == examples['E']['labels'], 'E+E target mismatch')
    lengths = {form: len(example['input_ids']) for form, example in examples.items()}
    for form, length in lengths.items():
        if length > 1024:
            failures.append('overlength_' + form)
    return dict(family_id=family['family_id'], candidate_output=text, text_sha256=sha(text.encode()),
                target_token_ids_sha256=digest(target_ids), target_tokens=len(target_ids), lengths=lengths,
                strict_correct=strict['correct'], scorer_invalid_reason=strict['invalid_reason'],
                flagged_words=flags, explanation_status=explanation_status(text), failure_reasons=failures,
                accepted=not failures, source=SOURCE)


def read_review(path, expected):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == REVIEW_FIELDS, 'Review columns changed')
        rows = list(reader)
    require(len(rows) == len(expected) and len({r['family_id'] for r in rows}) == len(rows), 'Missing/duplicate review rows')
    result = {}
    for row in rows:
        fid = row['family_id']
        require(fid in expected, 'Unexpected review family')
        for key in REVIEW_FIELDS[:4]:
            require(row[key] == expected[fid][key], 'Review candidate changed: ' + fid)
        decision = row[REVIEW_FIELDS[4]].strip()
        require(decision in ('pass', 'fail', 'uncertain') and row['YOUR_reason'].strip(), 'Every flagged row needs decision and reason')
        result[fid] = decision
    return result


def write_csv(path, rows, fields):
    # csv quoting preserves exact text, including newlines and leading whitespace.
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def select_records(families, outputs, tokenizer, reviews=None):
    require(len(outputs) == len(families) and len({o['family_id'] for o in outputs}) == len(outputs), 'Unresolved/duplicate generation')
    by_id = {o['family_id']: o for o in outputs}
    require(set(by_id) == {f['family_id'] for f in families}, 'Foreign output family')
    require(all(o['status'] == 'generated' and o['form'] == 'E' for o in outputs), 'Only resolved E generations qualify')
    ledger, sheet = [], []
    for family in families:
        output = by_id[family['family_id']]
        require(output['rendering_id'] == family['forms']['E']['rendering_id'], 'Rendering identity mismatch')
        row = candidate(family, output, tokenizer, (reviews or {}).get(family['family_id']))
        ledger.append(row)
        if row['flagged_words']:
            sheet.append(dict(zip(REVIEW_FIELDS, [family['family_id'], family['forms']['E']['text'], output['raw_response'],
                                                 ' '.join(row['flagged_words']), '', ''])))
    q = sum(row['accepted'] for row in ledger)
    pending = sum('language_review_pending' in row['failure_reasons'] for row in ledger)
    return dict(schema='phase3-selection-1', Q=q, branch='proceed' if q >= 120 else 'halt',
                pending_human_review=pending, Q_status='provisional_lower_bound' if pending else 'final', families=ledger), sheet


def sealed_export(folder):
    folder = Path(folder)
    paths = sorted(p for p in folder.rglob('*') if p.is_file() and p.name not in ('RUNNING.lock', 'checksums.sha256') and not p.name.endswith('.zip'))
    checksums = ''.join(f'{sha(p.read_bytes())}  {p.relative_to(folder).as_posix()}\n' for p in paths)
    (folder / 'checksums.sha256').write_text(checksums)
    archive = folder.parent / 'Phase3_Targets_results.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in paths + [folder / 'checksums.sha256']:
            z.write(path, path.relative_to(folder).as_posix())
    print('SEALED export:', archive.name, 'SHA-256', sha(archive.read_bytes()))
    return archive


def selection_from_run(root, folder, tokenizer, review_path=None):
    families = load_train(root)
    _, binding, _ = verify_contract(root)
    manifest = eng.read(Path(folder) / 'run_manifest.json')
    require(manifest['status'] == 'COMPLETE' and manifest['implementation_sha256'] == binding, 'Incomplete or foreign run')
    require(manifest['train_sha256'] == digest(families) and manifest['config_sha256'] == digest(backend_config()), 'Run inputs changed')
    require(manifest['evaluation_order'] == evaluation_order(families), 'Run order changed')
    _, outputs = eng.selected(folder)
    selection, sheet = select_records(families, outputs, tokenizer)
    if review_path:
        reviews = read_review(review_path, {r['family_id']: r for r in sheet})
        selection, sheet = select_records(families, outputs, tokenizer, reviews)
    selection['run_manifest_sha256'] = sha((Path(folder) / 'run_manifest.json').read_bytes())
    selection['runtime_contract_sha256'] = binding
    return selection, sheet


def freeze(selection, output_dir, *, review_path, folder):
    require(selection['pending_human_review'] == 0, 'Flagged rows lack decisions')
    require(selection['Q'] >= 120 and selection['branch'] == 'proceed', 'Q < 120: halt before training')
    output_dir = Path(output_dir)
    require(not (output_dir / 'targets.v1.json').exists() and not (output_dir / 'TARGETS_FROZEN.md').exists(), 'Targets already frozen')
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = dict(schema='phase3-targets-1', Q=selection['Q'], source=SOURCE,
                   terminal_marker='<|im_end|>', terminal_id=151645,
                   families=[{key: row[key] for key in ('family_id', 'candidate_output', 'text_sha256', 'target_token_ids_sha256',
                                                       'target_tokens', 'source', 'explanation_status', 'lengths')}
                             for row in selection['families'] if row['accepted']])
    raw = (json.dumps(targets, indent=2, ensure_ascii=False) + '\n').encode()
    (output_dir / 'targets.v1.json').write_bytes(raw)
    archive = sealed_export(folder)
    binding = dict(targets_sha256=sha(raw), selection_sha256=digest(selection), human_return_sha256=sha(Path(review_path).read_bytes()),
                   archive_sha256=sha(archive.read_bytes()), runtime_contract_sha256=selection['runtime_contract_sha256'],
                   run_manifest_sha256=selection['run_manifest_sha256'], frozen_at=eng.utc(), Q=selection['Q'],
                   text_policy='candidate_output is exact decoded text; append terminal_marker once at training; hashes exclude marker for text and include marker for IDs')
    (output_dir / 'TARGETS_FROZEN.md').write_text('# Phase-3 targets frozen\n\n```json\n' + json.dumps(binding, indent=2) + '\n```\n')


def load_tokenizer(root):
    _, _, old = verify_contract(root)
    verify_model_files(old)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', revision=REVISION, trust_remote_code=False)
    verify_tokenizer(tokenizer, old)
    return tokenizer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('generate', 'select', 'freeze'):
        p = sub.add_parser(name)
        p.add_argument('--root', type=Path, default=ROOT)
        p.add_argument('--run-dir', type=Path, required=True)
        if name == 'generate':
            p.add_argument('--recover-stale-lock', action='store_true', help='Operator confirms no other evaluator is active')
        if name == 'freeze':
            p.add_argument('--human-check', type=Path, required=True)
            p.add_argument('--output-dir', type=Path, default=ROOT / 'phase3')
    args = parser.parse_args(argv)
    families = load_train(args.root)
    _, binding, old = verify_contract(args.root)
    if args.command == 'generate':
        from t4_smoke import train_smoke as ts
        require(not ts.stack_mismatches(ts.versions()), 'D021 stack mismatch')
        files = verify_model_files(old)
        backend = RecordingBackend(backend_config())
        verify_tokenizer(backend.tokenizer, old)
        require(backend.model.generation_config.eos_token_id == [151645, 151643], 'EOS changed')
        expected_shards = json.loads((args.root / 'phase3/runtime_contract.json').read_bytes())['base_weight_shards_sha256']
        require(backend.metadata['base_weight_shards_sha256'] == expected_shards, 'Base shard hashes changed')
        backend.metadata['verified_hub_files'] = files
        contract_raw = (args.root / 'phase3/runtime_contract.json').read_bytes()
        contract = json.loads(contract_raw)
        evidence = {path: (args.root / path).read_bytes() for path in contract['files']}
        evidence['phase3/runtime_contract.json'] = contract_raw
        backend.metadata['all_package_versions'] = ts.versions()
        manifest = generate_run(args.run_dir, families, backend, binding, recover=args.recover_stale_lock, evidence=evidence)
        sealed_export(args.run_dir)
        return 0 if manifest['status'] == 'COMPLETE' else 1
    tokenizer = load_tokenizer(args.root)
    with eng.lock(args.run_dir):
        selection, sheet = selection_from_run(args.root, args.run_dir, tokenizer, getattr(args, 'human_check', None))
        eng.write(args.run_dir / 'ledger.json', selection)
        flat = [{**r, 'lengths': json.dumps(r['lengths']), 'failure_reasons': ';'.join(r['failure_reasons']),
                 'flagged_words': ' '.join(r['flagged_words'])} for r in selection['families']]
        write_csv(args.run_dir / 'ledger.csv', flat, list(flat[0]))
        if args.command == 'select':
            write_csv(args.run_dir / 'human_check.csv', sheet, REVIEW_FIELDS)
            sealed_export(args.run_dir)
        else:
            # Preserve the exact human return in the frozen archive.
            (args.run_dir / 'human_return.csv').write_bytes(args.human_check.read_bytes())
            freeze(selection, args.output_dir, review_path=args.human_check, folder=args.run_dir)
    print(json.dumps({k: selection[k] for k in ('Q', 'branch', 'pending_human_review', 'Q_status')}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
