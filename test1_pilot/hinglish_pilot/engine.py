"""Append-only attempt journal, safe resume and fixed final-answer scoring."""
import csv
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import random
import re
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .data import DEMO_LABEL, digest, records, require, validate
from .scorer_v1 import SCORER_VERSION, score_response

# v1 is retained for the record. v2 (decision D020, 14 October 2026) replaced it before any
# reviewed pilot generation, after the excluded FMT2 development run showed v1 eliciting
# unit words such as 'unitless' after dimensionless answers and non-English explanations.
INSTRUCTION_V1 = ('Solve the problem. Give a short explanation in English. End with exactly one '
                  'line: FINAL: <number or fraction> <unit when applicable>.')
INSTRUCTION = ('Solve the problem. Give a short explanation in English, even if the question is not '
               'in English. End with exactly one line: FINAL: <number or fraction>, followed by its '
               'unit in English only if the answer has a unit; write nothing after a pure number or fraction.')
PROMPT_VERSION = 'test1-english-final-v2'
PACKAGES = ('torch', 'transformers', 'accelerate', 'bitsandbytes', 'huggingface-hub',
            'tokenizers', 'safetensors', 'numpy', 'matplotlib', 'nbformat')


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in rows), encoding='utf-8')


def csvfile(path, rows, fields):
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        out = csv.DictWriter(stream, fields, extrasaction='ignore')
        out.writeheader()
        for row in rows:
            # Prevent spreadsheet formula execution when opening user/model text.
            safe = {k: ("'" + v if isinstance(v, str) and v[:1] in '=+-@' else v)
                    for k, v in row.items()}
            out.writerow(safe)


def code_hash():
    root = Path(__file__).parent
    return digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob('*.py'))})


def environment():
    packages = {}
    for name in PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {'python': platform.python_version(), 'platform': platform.system(),
            'machine': platform.machine(), 'packages': packages}


def default_config(mode='demo'):
    return {'mode': mode, 'model_id': 'Qwen/Qwen3-4B', 'model_revision': None,
            'tokenizer_revision': None, 'seed': 11, 'bootstrap_seed': 101,
            'bootstrap_resamples': 10000, 'max_new_tokens': 1024, 'context_limit': 2048,
            'thinking': False, 'do_sample': False, 'num_beams': 1,
            'quantization': 'nf4', 'double_quantization': True, 'compute_dtype': 'float16',
            'attention_backend': 'sdpa_math', 'max_infrastructure_retries': 1,
            'prompt_version': PROMPT_VERSION, 'instruction': INSTRUCTION,
            'decode_policy_note': 'Greedy non-thinking fixed pilot policy; differs from model-card sampling recommendation.'}


def validate_config(config):
    require(set(config) == set(default_config()), 'Unknown/missing config fields')
    require(config['mode'] in ('demo', 'reviewed'), 'Bad config mode')
    require(config['model_id'] == 'Qwen/Qwen3-4B', 'Test 1 supports Qwen/Qwen3-4B only')
    for key in ('model_revision', 'tokenizer_revision'):
        require(isinstance(config[key], str) and re.fullmatch('[0-9a-f]{40}', config[key]), 'Resolve immutable model/tokenizer SHAs before running')
    require(config['thinking'] is False and config['do_sample'] is False and config['num_beams'] == 1,
            'This protocol requires non-thinking greedy decoding')
    require(config['instruction'] == INSTRUCTION and config['prompt_version'] == PROMPT_VERSION, 'Frozen prompt changed')
    for key in ('seed', 'bootstrap_seed'):
        require(type(config[key]) is int and 0 <= config[key] < 2**32, 'Seed must be a nonnegative 32-bit integer')
    require(config['bootstrap_resamples'] == 10000, 'Use 10,000 family resamples')
    require(type(config['context_limit']) is int and type(config['max_new_tokens']) is int and 1 <= config['max_new_tokens'] < config['context_limit'] <= 32768,
            'Invalid token/context limits')
    require(config['quantization'] == 'nf4' and config['double_quantization'] is True and
            config['compute_dtype'] == 'float16' and config['attention_backend'] == 'sdpa_math', 'Unsupported inference recipe')
    require(type(config['max_infrastructure_retries']) is int and config['max_infrastructure_retries'] in (0, 1), 'At most one infrastructure retry')


class FakeBackend:
    """Software fixture only: no language/model inference evidence."""
    metadata = {'backend': 'fake', 'hardware': 'none', 'model_revision': '0' * 40,
                'tokenizer_revision': '0' * 40, 'gpu_verified': False}

    def prepare(self, text, config):
        prompt = config['instruction'] + '\nUSER: ' + text + '\nASSISTANT:'
        require(len(prompt.split()) + config['max_new_tokens'] <= config['context_limit'], 'Overlength fixture')
        return {'rendered_prompt': prompt, 'input_tokens': len(prompt.split()), 'token_count_kind': 'FAKE whitespace count'}

    def generate(self, prepared, config, seed):
        # Never uses supplied gold; intentionally exercises wrong, missing and valid answers.
        q = prepared['rendered_prompt']
        answer = 'FINAL: 5' if 'DEMO-ADD' in q else ('FINAL: 0.5' if 'DEMO-HALF' in q else 'No marked answer')
        return {'raw_response': answer, 'output_tokens': len(answer.split()), 'latency_seconds': 0.001,
                'truncated': False, 'finish_reason': 'fake', 'memory': {'measurement_scope': 'fake; no GPU measurement'}}


@contextmanager
def lock(root):
    target = root / 'RUNNING.lock'
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Run lock exists. Stop any active writer; use recover_lock only after a disconnected runtime.') from None
    try:
        os.write(fd, utc().encode())
        os.close(fd)
        yield
    finally:
        target.unlink(missing_ok=True)


def recover_lock(root, confirmed_no_active_writer=False):
    require(confirmed_no_active_writer is True, 'Confirm no active writer before recovering a stale lock')
    Path(root, 'RUNNING.lock').unlink(missing_ok=True)


def attempts(root):
    result = []
    for path in sorted(Path(root, 'journal').glob('*.json')):
        item = read(path)
        require(item['record_sha256'] == digest({k: v for k, v in item.items() if k != 'record_sha256'}), 'Attempt journal corruption')
        result.append(item)
    return result


def selected(root):
    manifest = read(Path(root, 'run_manifest.json'))
    journal = attempts(root)
    grouped = {}
    for item in journal:
        require(item['run_id'] == manifest['run_id'] and item['config_sha256'] == manifest['config_sha256'], 'Foreign journal record')
        grouped.setdefault(item['rendering_id'], []).append(item)
    output = []
    for rid in manifest['evaluation_order']:
        history = sorted(grouped.get(rid, []), key=lambda x: x['attempt_number'])
        require([x['attempt_number'] for x in history] == list(range(1, len(history) + 1)), 'Attempt sequence corrupt')
        successful = [x for x in history if x['status'] == 'generated']
        require(len(successful) <= 1, 'Multiple scored attempts forbidden')
        require(not successful or successful[0] == history[-1], 'Cannot retry a generated response')
        if successful:
            output.append(successful[0])
    require(set(grouped) <= set(manifest['evaluation_order']), 'Unexpected rendering in journal')
    return journal, output


def run(root, dataset, splits, config, backend, max_items=None, progress=None):
    """Each committed attempt is atomic. Interrupted in-flight generation is rerun,
    not scored. Successful outputs (even incorrect/truncated) are never retried."""
    validate(dataset, splits, config['mode'])
    validate_config(config)
    require(config['mode'] == 'demo' or backend.metadata['backend'] == 'huggingface', 'Reviewed research forbids fake backend')
    for key in ('model_revision', 'tokenizer_revision'):
        require(backend.metadata[key] == config[key], 'Backend revision mismatch')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    frozen_env = environment()
    identity = {'config_sha256': digest(config), 'dataset_sha256': digest(dataset), 'split_sha256': digest(splits),
                'code_sha256': code_hash(), 'execution_sha256': digest({'backend': backend.metadata, 'environment': frozen_env})}
    items = records(dataset)
    by_id = {x['rendering_id']: x for x in items}
    with lock(root):
        manifest_path = root / 'run_manifest.json'
        if manifest_path.exists():
            manifest = read(manifest_path)
            require(all(manifest[k] == v for k, v in identity.items()), 'Resume rejected: data/config/code/environment/backend changed. Use a new run.')
            require(manifest['evaluation_order'] == read(root / 'evaluation_order.json'), 'Evaluation-order file changed')
            require(digest(read(root / 'experiment_config.json')) == identity['config_sha256'] and
                    digest(read(root / 'dataset.json')) == identity['dataset_sha256'] and
                    digest(read(root / 'split_manifest.json')) == identity['split_sha256'], 'Frozen input snapshot changed')
        else:
            require(not (root / 'journal').exists(), 'Orphan journal: choose an empty run directory')
            order = sorted(by_id)
            random.Random(config['seed']).shuffle(order)
            manifest = dict(identity, run_id=config['mode'] + '-' + uuid.uuid4().hex,
                mode=config['mode'], label=DEMO_LABEL if config['mode'] == 'demo' else 'REVIEWED PILOT — metadata attested',
                created_at=utc(), status='INCOMPLETE', expected=len(order), evaluation_order=order,
                backend=backend.metadata, scorer_version=SCORER_VERSION,
                warnings=['Human review/semantic equivalence cannot be machine certified.',
                          'Greedy decoding is not a guarantee of identical outputs across hardware/software.',
                          'Quantized, capped, non-thinking pilot; no training-effect evidence.'],
                deviations=[config['decode_policy_note']], sessions=[])
            write(root / 'experiment_config.json', config)
            write(root / 'environment.json', frozen_env)
            write(root / 'dataset.json', dataset)
            write(root / 'split_manifest.json', splits)
            write(root / 'evaluation_order.json', order)
            for source in Path(__file__).parent.glob('*.py'):
                snapshot = root / 'source' / source.name
                snapshot.parent.mkdir(exist_ok=True)
                snapshot.write_bytes(source.read_bytes())
            write(manifest_path, manifest)
        # Tokenize all before the first scored generation; fail rather than truncate.
        prepared = {rid: backend.prepare(by_id[rid]['input_text'], config) for rid in manifest['evaluation_order']}
        journal, done = selected(root)
        completed = {x['rendering_id'] for x in done}
        session = {'started_at': utc(), 'environment': frozen_env, 'backend': backend.metadata}
        manifest['sessions'].append(session)
        write(manifest_path, manifest)
        new = 0
        stop = False
        try:
            for rid in manifest['evaluation_order']:
                if rid in completed:
                    continue
                if max_items is not None and new >= max_items:
                    break
                history = [x for x in journal if x['rendering_id'] == rid]
                if history and history[-1]['error_code'] == 'out_of_memory':
                    continue
                allowed = 1 + config['max_infrastructure_retries']
                while len(history) < allowed:
                    number = len(history) + 1
                    item = by_id[rid]
                    base = dict(item, **prepared[rid], run_id=manifest['run_id'], mode=config['mode'], label=manifest['label'],
                        config_sha256=identity['config_sha256'], attempt_id=uuid.uuid4().hex, attempt_number=number,
                        retry_reason=None if number == 1 else 'previous_infrastructure_failure',
                        model_revision=config['model_revision'], tokenizer_revision=config['tokenizer_revision'],
                        generation_seed=config['seed'] + manifest['evaluation_order'].index(rid), started_at=utc())
                    attempt_path = root / 'journal' / f'{rid}.{number:02d}.json'
                    base.update(status='in_progress', infrastructure_failure=True,
                        error_code='interrupted_before_commit', raw_response=None, output_tokens=None,
                        correct=None, invalid_reason=None, extracted_final=None, normalized_value=None,
                        normalized_unit=None, scorer_version=SCORER_VERSION, refusal=False,
                        truncated=False, latency_seconds=None,
                        memory={'measurement_scope': 'in-flight; no committed telemetry'})
                    base['record_sha256'] = digest(base)
                    write(attempt_path, base)
                    base.pop('record_sha256')
                    start = time.monotonic()
                    try:
                        generated = backend.generate(prepared[rid], config, base['generation_seed'])
                        require(isinstance(generated['raw_response'], str) and type(generated['truncated']) is bool, 'Backend output contract')
                        base.update(generated)
                        base.update(score_response(base['raw_response'], item['gold'], base['truncated']))
                        base.update(status='generated', infrastructure_failure=False, error_code=None,
                                    refusal=base['invalid_reason'] == 'refusal')
                    except KeyboardInterrupt:
                        stop = True
                        base.update(status='infrastructure_failure', error_code='keyboard_interrupt',
                                    latency_seconds=time.monotonic() - start)
                    except Exception as error:
                        # Do not serialize arbitrary exception messages: they may contain credentials.
                        name = type(error).__name__
                        oom = 'OutOfMemory' in name
                        base.update(status='infrastructure_failure', infrastructure_failure=True,
                            error_code='out_of_memory' if oom else 'generation_failed', exception_class=name,
                            latency_seconds=time.monotonic() - start, raw_response=None, output_tokens=None,
                            correct=None, invalid_reason=None, extracted_final=None, normalized_value=None,
                            normalized_unit=None, scorer_version=SCORER_VERSION, refusal=False, truncated=False,
                            memory={'measurement_scope': 'failure; no reliable per-attempt peak'})
                        # OOM requires an explicit new configuration/new run; never retry it automatically.
                        if oom:
                            stop = True
                    base['finished_at'] = utc()
                    base['record_sha256'] = digest(base)
                    write(attempt_path, base)
                    journal.append(base)
                    history.append(base)
                    if base['status'] == 'generated':
                        completed.add(rid)
                        new += 1
                        if progress:
                            progress(len(completed), len(by_id), base)
                        break
                    if stop:
                        break
                if stop:
                    break
        finally:
            journal, done = selected(root)
            session['finished_at'] = utc()
            manifest.update(status='COMPLETE' if len(done) == len(by_id) else 'INCOMPLETE',
                            completed=len(done), unresolved=len(by_id) - len(done), attempts=len(journal), updated_at=utc())
            write(manifest_path, manifest)
            jsonl(root / 'generation_attempts.jsonl', journal)
            jsonl(root / 'errors.jsonl', [x for x in journal if x['status'] != 'generated'])
        return manifest
