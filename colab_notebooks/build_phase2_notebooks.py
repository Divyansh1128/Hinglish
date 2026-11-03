"""Build the Phase-2 notebooks (D043; binding plan phase2/PREREGISTRATION.md with Amendment 1) into colab_notebooks/phase2/.

- Phase2_Baseline_DEV.ipynb: unchanged Qwen3-4B on DEV; prints "high unchanged-DEV accuracy (ceiling-risk proxy)"
  with k/40 and its Wilson interval (Amendment 1 item 7).
- Phase2_Train.ipynb: one notebook for all runs (ARM and seed SLOT at the top). The append-only attempt log decides
  the seed (reserves 44/55 automatically), the attempt and whether training is allowed at all (Amendment 1 item 11);
  trains 60 updates under the item-10 numerical contract, then a DEV sanity evaluation; downloads a ZIP.
- Phase2_FinalTest.ipynb: unchanged model + the 3S frozen adapters on FINAL_TEST, sealed (completion, checksum and
  infrastructure status only). Built only when phase2/PREREGISTRATION.md matches PREREGISTRATION_SHA256 below, the
  implementation manifest is current and phase2/ADAPTERS_FROZEN.md exists and records it (§11, items 12-14).

Every notebook is self-contained (code and data embedded, nothing to upload) and embeds
phase2/IMPLEMENTATION_MANIFEST.md with its SHA-256: it refuses to run if any embedded code differs from the manifest.
The builder therefore requires a current manifest (python3 -B phase2/build_implementation_manifest.py). Training
notebooks never contain FINAL_TEST data. No Phase-2 notebook offers a second backbone (Amendment 1 item 15).
Usage from the repository root:
  python3 -B colab_notebooks/build_phase2_notebooks.py          # build
  python3 -B colab_notebooks/build_phase2_notebooks.py --check  # verify the committed notebooks are current
"""
import base64
import hashlib
import io
import json
import sys
import textwrap
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'colab_notebooks' / 'phase2'
STAMP = (2026, 11, 3, 0, 0, 0)
NAMES = {'baseline': 'Phase2_Baseline_DEV.ipynb', 'train': 'Phase2_Train.ipynb', 'final_test': 'Phase2_FinalTest.ipynb'}
PREREGISTRATION = ROOT / 'phase2' / 'PREREGISTRATION.md'
# SHA-256 of the committed pre-registration WITH Amendment 1 (commit b4fb956, D045). The original 74be2328... (commit
# 58d330d) is superseded. Any further edit needs an amendment and a new constant (§13).
PREREGISTRATION_SHA256 = '37ef68bfcb7cfa0bb530bfbecbf2082d18e916c0217370085d4180e8ea759ada'
ADAPTERS_FROZEN = ROOT / 'phase2' / 'ADAPTERS_FROZEN.md'
MANIFEST_BUILDER = ROOT / 'phase2' / 'build_implementation_manifest.py'
T4_CODE = ('train_smoke.py', 'labels.py', 'protocol.py', 'train_phase2.py', 'phase2_eval.py')
# The secondary modules embedded in the Pilot-B notebooks (numeric_literal_v1 etc.); later additions need a rebuild.
SECONDARY = ('__init__.py', 'cmi.py', 'numeric_endpoint.py', 'report_secondary.py')
DRIVE = 'Hinglish_Phase2'

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'test1_pilot'))
from t4_smoke import phase2_eval, train_phase2, train_smoke  # noqa: E402


def payload_sources(kind):
    """{payload member: repository path} for every member whose bytes the implementation manifest hashes."""
    sources = {'hinglish_pilot/' + p.name: 'test1_pilot/hinglish_pilot/' + p.name
               for p in sorted((ROOT / 'test1_pilot' / 'hinglish_pilot').glob('*.py'))}
    sources.update({'secondary_analysis/' + name: 'secondary_analysis/' + name for name in SECONDARY})
    sources.update({'t4_smoke/' + name: 't4_smoke/' + name for name in T4_CODE})
    if kind in ('baseline', 'train'):
        sources['inputs/dev.v2.json'] = phase2_eval.FROZEN['dev'][0]
    if kind == 'train':
        sources['inputs/EXPOSURE_ORDER.json'] = train_phase2.EXPOSURE_ORDER_PATH
    return sources


def manifest_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location('build_implementation_manifest', MANIFEST_BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def implementation_manifest():
    """(text, sha256) of phase2/IMPLEMENTATION_MANIFEST.md; refuses a missing or stale manifest."""
    module = manifest_module()
    path = module.MANIFEST
    if not path.is_file():
        raise SystemExit(f'{path} is missing: run python3 -B phase2/build_implementation_manifest.py first')
    text = path.read_text(encoding='utf-8')
    if text != module.current_text():
        raise SystemExit(f'{path} is stale: run python3 -B phase2/build_implementation_manifest.py, then rebuild')
    return text, hashlib.sha256(text.encode('utf-8')).hexdigest()


def requirements():
    return ('# D021 stack (training and evaluation). Colab supplies torch ' + train_smoke.TORCH_BUILD
            + '; it is recorded, not replaced.\n' + ''.join(f'{n}=={v}\n' for n, v in train_smoke.PINS.items()))


def payload(kind, prereg=None, frozen_text=None):
    """ZIP bytes for one notebook kind; ``prereg``/``frozen_text`` only for the FinalTest notebook."""
    buffer = io.BytesIO()

    def put(archive, name, content):
        info = zipfile.ZipInfo(name, date_time=STAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content)

    identities = phase2_eval.split_identities(ROOT)  # identity triples only; FINAL_TEST is not read here
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / 'test1_pilot' / 'hinglish_pilot').glob('*.py')):
            put(archive, 'hinglish_pilot/' + path.name, path.read_bytes())
        for name in SECONDARY:
            put(archive, 'secondary_analysis/' + name, (ROOT / 'secondary_analysis' / name).read_bytes())
        for name in T4_CODE:
            put(archive, 't4_smoke/' + name, (ROOT / 't4_smoke' / name).read_bytes())
        put(archive, 'requirements-phase2.txt', requirements())
        put(archive, 'inputs/identities.json', json.dumps(identities, indent=1) + '\n')
        if kind in ('baseline', 'train'):
            put(archive, 'inputs/dev.v2.json', (ROOT / phase2_eval.FROZEN['dev'][0]).read_bytes())
        if kind == 'train':
            put(archive, 'inputs/phase2_train.json', json.dumps(train_phase2.phase2_dataset(ROOT), indent=1, ensure_ascii=False) + '\n')
            put(archive, 'inputs/EXPOSURE_ORDER.json', (ROOT / train_phase2.EXPOSURE_ORDER_PATH).read_bytes())
        if kind == 'final_test':
            put(archive, 'inputs/final_test.v3.json', (ROOT / phase2_eval.FROZEN['final_test'][0]).read_bytes())
            put(archive, 'inputs/PREREGISTRATION.md', prereg)
            put(archive, 'inputs/ADAPTERS_FROZEN.md', frozen_text.encode('utf-8'))
    return buffer.getvalue()


SETUP = '''
import os, sys, json, base64, io, zipfile, hashlib, subprocess, time
from pathlib import Path
%SETTINGS%
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
os.environ['PYTHONHASHSEED'] = '0'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'  # download bars would become thousands of streamed lines
PACKAGE = Path('/content/hinglish_phase2') if Path('/content').exists() else Path.cwd() / 'hinglish_phase2'
PACKAGE.mkdir(parents=True, exist_ok=True)
blob = base64.b64decode(%BLOB%)
assert hashlib.sha256(blob).hexdigest() == %DIGEST%
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(PACKAGE)
INPUTS = PACKAGE / 'inputs'
# Implementation manifest (PREREGISTRATION Amendment 1 item 14): refuse to run if the embedded code differs from it.
MANIFEST_TEXT = base64.b64decode(%MANIFEST%).decode('utf-8')
MANIFEST_SHA256 = %MANIFEST_SHA%
assert hashlib.sha256(MANIFEST_TEXT.encode('utf-8')).hexdigest() == MANIFEST_SHA256, 'Embedded IMPLEMENTATION_MANIFEST.md was changed: refusing to run'
MANIFEST = json.loads(MANIFEST_TEXT.split('```json\\n', 1)[1].split('\\n```', 1)[0])
assert MANIFEST['preregistration']['sha256'] == %PREREG_SHA%, 'Manifest is for another PREREGISTRATION.md: refusing to run'
%PAYLOAD_CHECK%
for member, source in %SOURCES%.items():
    assert hashlib.sha256((PACKAGE / member).read_bytes()).hexdigest() == MANIFEST['files'][source], f'{member} differs from the implementation manifest: refusing to run'
(INPUTS / 'IMPLEMENTATION_MANIFEST.md').write_text(MANIFEST_TEXT, encoding='utf-8')
print('Implementation manifest verified:', MANIFEST_SHA256)
if USE_DRIVE and Path('/content').exists():  # Drive only inside Colab
    from google.colab import drive
    drive.mount('/content/drive')
    STORE = Path('/content/drive/MyDrive/%DRIVE%')
else:
    STORE = PACKAGE / 'runs'
STORE.mkdir(parents=True, exist_ok=True)
try:  # Qwen3-4B is ungated; a token only avoids anonymous rate limits.
    from google.colab import userdata
    os.environ['HF_TOKEN'] = (userdata.get('HF_TOKEN') or '').strip() or os.environ.get('HF_TOKEN', '')
except Exception as error:
    print('No HF_TOKEN Colab secret (' + type(error).__name__ + '); downloading anonymously.')
if not os.environ.get('HF_TOKEN'):
    os.environ.pop('HF_TOKEN', None)

def step(log_dir, script, *args):
    """Run one phase in a fresh Python process, stream its output and log the attempt."""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-u', str(PACKAGE / 't4_smoke' / script), *map(str, args)]
    started, returncode = time.time(), None
    try:
        with open(log_dir / 'log.txt', 'a') as log, subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                                     text=True, errors='replace') as process:
            try:
                for line in process.stdout:
                    print(line, end='', flush=True)
                    log.write(line)
            except BaseException:  # interrupt: never leave a phase running on the GPU behind the notebook
                process.kill()
                process.wait()
                log.write('[notebook] interrupted; phase process killed\\n')
                raise
        returncode = process.returncode
    finally:
        with open(log_dir / 'attempts.jsonl', 'a') as attempts:
            attempts.write(json.dumps({'script': script, 'args': list(map(str, args)), 'returncode': returncode,
                                       'started': started, 'seconds': time.time() - started}) + '\\n')
    return returncode

def zip_results(folder, archive, prefix):
    """All small files under ``folder``; weights, optimizer state and per-attempt journals stay out (hashes listed)."""
    files, large = [], {}
    for path in sorted(Path(folder).rglob('*')):
        if not path.is_file() or 'journal' in path.relative_to(folder).parts or path.name.endswith('.lock'):
            continue
        if path.suffix in ('.pt', '.safetensors'):
            large[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            files.append(path)
    sums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(folder)}\\n' for p in files)
    sums += ''.join(f'{digest}  {name}  (not included)\\n' for name, digest in large.items())
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, str(Path(prefix) / path.relative_to(folder)))
        z.writestr(str(Path(prefix) / 'SHA256SUMS.txt'), sums)
    print(sums)
    print('Return:', archive, 'SHA-256', hashlib.sha256(Path(archive).read_bytes()).hexdigest())
    try:
        from google.colab import files as colab_files
        colab_files.download(str(archive))
    except ImportError:
        print('Local: ZIP saved on disk.')
'''

GPU = '''
try:
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()
except FileNotFoundError:  # CPU runtime: no nvidia-smi at all
    gpu = ''
print('GPU:', gpu or 'none')
assert 'T4' in gpu, 'Select Runtime → Change runtime type → T4 GPU'
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(PACKAGE / 'requirements-phase2.txt')], check=True)
# A fresh interpreter sees the installed versions; this kernel never imports torch.
STACK = json.loads(subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import train_smoke as t, json; '
                                   'v = t.versions(); print(json.dumps({"versions": v, "mismatches": t.stack_mismatches(v)}))',
                                   str(PACKAGE / 't4_smoke')], capture_output=True, text=True, check=True).stdout)
print(json.dumps(STACK['versions'], indent=1))
STACK_MISMATCHES = STACK['mismatches']
print('D021 stack mismatches:', STACK_MISMATCHES or 'none')
# Tokenizer, chat template and config files at the pinned revision must match the implementation manifest.
HUB_CHECK = """
import hashlib, json, os, sys
from huggingface_hub import hf_hub_download
model = json.loads(sys.argv[1])
for name, expected in sorted(model['hub_files'].items()):
    path = hf_hub_download(model['id'], name, revision=model['revision'], token=os.environ.get('HF_TOKEN') or None)
    actual = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    assert actual == expected, f'{name} at the pinned revision has SHA-256 {actual}, manifest {expected}: refusing to run'
print('Pinned Hub files match the implementation manifest:', ', '.join(sorted(model['hub_files'])))
"""
print(subprocess.run([sys.executable, '-c', HUB_CHECK, json.dumps(MANIFEST['model'])], capture_output=True, text=True, check=True).stdout)
'''

PROTOCOL = ('Frozen protocol (PREREGISTRATION §4): prompt `test1-english-final-v2`, greedy non-thinking decoding, NF4 + FP16, '
            'SDPA math, output cap 1,024 tokens, scorer v1.0.0, engine seed 11. **Do not change any setting.**')


def cells_for(kind, blob, settings, body, manifest):
    cells = []

    def add(cell_kind, source):
        source = textwrap.dedent(source).strip() + '\n'
        cell = {'cell_type': cell_kind, 'id': f'p2-{kind}-{len(cells):02d}', 'metadata': {}, 'source': source}
        if cell_kind == 'code':
            cell.update(outputs=[], execution_count=None)
        cells.append(cell)

    text, digest = manifest
    if kind in ('baseline', 'train'):  # the manifest hashes these payloads; FinalTest is built later and checks members
        payload_check = (f"assert MANIFEST['notebook_payloads'][{NAMES[kind]!r}] == hashlib.sha256(blob).hexdigest(), "
                         "'Notebook payload differs from the implementation manifest: refusing to run'")
    else:
        payload_check = '# FinalTest payload: every code member is checked below; the gate checks ADAPTERS_FROZEN.md.'
    setup = (SETUP.replace('%SETTINGS%', textwrap.dedent(settings).strip())
             .replace('%BLOB%', repr(base64.b64encode(blob).decode())).replace('%DIGEST%', repr(hashlib.sha256(blob).hexdigest()))
             .replace('%DRIVE%', DRIVE).replace('%MANIFEST%', repr(base64.b64encode(text.encode('utf-8')).decode()))
             .replace('%MANIFEST_SHA%', repr(digest)).replace('%PREREG_SHA%', repr(PREREGISTRATION_SHA256))
             .replace('%PAYLOAD_CHECK%', payload_check).replace('%SOURCES%', repr(payload_sources(kind))))
    for cell_kind, source in body(setup):
        add(cell_kind, source)
    return cells


def notebook(name, cells):
    return json.dumps({'nbformat': 4, 'nbformat_minor': 5, 'cells': cells,
                       'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                                    'language_info': {'name': 'python'}, 'colab': {'name': name}, 'accelerator': 'GPU'}},
                      indent=2, ensure_ascii=False) + '\n'


def render_baseline(manifest=None):
    manifest = manifest or implementation_manifest()
    blob = payload('baseline')

    def body(setup):
        yield 'markdown', f'''
            # Phase 2 — unchanged Qwen3-4B on DEV (PREREGISTRATION §5 with Amendment 1)
            Run this **once, before any training run**. 40 DEV families × E/R/C = 120 generations with the unchanged model.
            {PROTOCOL}
            The notebook embeds `phase2/IMPLEMENTATION_MANIFEST.md` (SHA-256 `{manifest[1]}`) and refuses to run if any embedded code or data differs from it, or if the pinned tokenizer/config files differ (Amendment 1 item 14).
            At the end it prints **high unchanged-DEV accuracy (ceiling-risk proxy)** with k/40 and its Wilson 95% interval; the flag fires at C ≥ 38/40 (Amendment 1 item 7). It is a proxy only: Δ_C stays first in the report whatever it shows. DEV is a sanity set: it never selects anything. No FINAL_TEST data is in this notebook.
            **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all** (about 15–20 minutes). Drive is on by default so a disconnect resumes (re-run all; finished prompts are kept, never regenerated). A results ZIP with checksums downloads at the end; send it unchanged.'''
        yield 'code', setup
        yield 'code', GPU
        yield 'code', '''
            RUN_DIR = STORE / 'baseline_dev' / 'base'
            step(RUN_DIR.parent, 'phase2_eval.py', 'evaluate', '--split', 'dev', '--inputs', INPUTS, '--run-dir', RUN_DIR)
            FLAG = RUN_DIR.parent / 'base_ceiling_flag.json'
            assert FLAG.exists(), 'Evaluation incomplete (see above): re-run all to resume, then download'
            flag = json.loads(FLAG.read_text())
            low, high = flag['wilson95']
            print(f"\\n{flag['name']}: {'FIRES' if flag['flag'] else 'does not fire'} — unchanged DEV C {flag['k']}/{flag['n']}"
                  f" (Wilson 95% {100 * low:.1f}–{100 * high:.1f}%; threshold >= 38/40)")'''
        yield 'markdown', '## Download\nIf the run stopped early, re-run all cells first. Then run this cell.'
        yield 'code', "zip_results(STORE / 'baseline_dev', PACKAGE / 'Phase2_Baseline_DEV_results.zip', 'baseline_dev')"

    return notebook(NAMES['baseline'], cells_for('baseline', blob, "USE_DRIVE = True  # resume after a disconnect", body, manifest))


def render_train(manifest=None):
    manifest = manifest or implementation_manifest()
    blob = payload('train')
    settings = '''
        ARM = 'EC'   # 'EE', 'ER' or 'EC'
        SLOT = 11    # seed slot 11, 22 or 33; the attempt log assigns reserve seed 44, then 55, when Amendment 1 item 11 requires it
        USE_DRIVE = True  # adapters, checkpoints and the attempt log live on Drive; keep this on
        RESUME_AFTER_DISCONNECT = False  # engineering only: a resumed run is NEVER valid for the FinalTest gate
        ALLOW_STACK_MISMATCH = False
        assert ARM in ('EE', 'ER', 'EC') and SLOT in (11, 22, 33)'''

    def body(setup):
        yield 'markdown', f'''
            # Phase 2 — QLoRA training run (D043, Amendment 1) + DEV sanity check
            One notebook for all runs: set **ARM** and the seed **SLOT** (11, 22 or 33) in the next cell and run all. Each run: all 160 TRAIN families, 320 examples, **exactly 60 accumulation windows with 60 successful optimizer steps** of 16 examples (8 families) over 3 passes, AdamW lr 1e-4 with 6 warm-up updates then cosine decay to 1e-5 (lr set before each step, gradients unscaled before clipping), GradScaler init 65,536 / growth 2.0 / backoff 0.5 / interval 2,000, the D021 recipe otherwise (NF4 + FP16, LoRA r16/α32/dropout 0.05 on all 7 projections, fp32 adapter). The exposure order is the frozen `phase2/EXPOSURE_ORDER.json`; it and the LoRA initialisation are identical across arms within a seed. About 25 minutes of training plus about 15 minutes of DEV evaluation on a T4.
            The notebook embeds `phase2/IMPLEMENTATION_MANIFEST.md` (SHA-256 `{manifest[1]}`) and refuses to run if any embedded code or data differs from it (Amendment 1 item 14). After update 60 the adapter is saved to Drive with its SHA-256s; then it is evaluated **on DEV as a sanity report only** (never used for selection). {PROTOCOL} No FINAL_TEST data is in this notebook.
            **Failures (Amendment 1 items 10–11).** Every attempt is recorded in the append-only `MyDrive/{DRIVE}/train/ATTEMPT_LOG.jsonl` (hash-chained, never overwritten) and the plan is printed before training.
            - *Infrastructure* (disconnect, crash, OOM, failed save or reload): re-run all — one fresh attempt from scratch with the same seed. After a second infrastructure failure of any arm the whole seed triplet is replaced by the next unused reserve (44, then 55, filling slots in order 11, 22, 33); just keep the same SLOT and the notebook switches seed. Reserves get the same two-attempt limit and are never reused.
            - *Numerical* (GradScaler skip, non-finite loss, gradient or saved parameter) or *protocol* (hash, data, exposure-order, label or step-count assertion): the run is invalid and **the study halts** — no retry, no reserve. The notebook then refuses all further training. Send the ZIP.
            - A run continued with `RESUME_AFTER_DISCONNECT = True` is never valid for the FinalTest gate.
            **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. A ZIP (adapter hashes, training log, attempt log, DEV results; weights stay on Drive) downloads at the end; send it unchanged.'''
        yield 'code', setup
        yield 'code', GPU
        yield 'code', '''
            sys.path.insert(0, str(PACKAGE / 't4_smoke'))
            import train_phase2 as tp
            TRAIN_ROOT = STORE / 'train'
            LOG = TRAIN_ROOT / tp.ATTEMPT_LOG
            for entry in tp.reconcile(TRAIN_ROOT):  # attempts left open by a disconnect are closed from their own reports
                print('Recorded an attempt left open earlier:', entry['arm'], 'seed', entry['seed'], 'attempt', entry['attempt'], '->', entry['outcome'])
            PLAN = tp.plan(tp.read_log(LOG))
            print(tp.describe_plan(PLAN))
            ACTION = tp.next_action(PLAN, ARM, SLOT)  # refuses after a numerical/protocol failure (study halted) or an exhausted slot
            SEED = ACTION['seed']
            RESUME = False
            if ACTION['kind'] == 'done':
                ATTEMPT = ACTION['attempt']
                print(f'Already trained (valid): {ARM} seed {SEED} attempt {ATTEMPT}')
            else:
                history = PLAN['slots'][SLOT]['arms'][ARM]['attempts']
                last = history[-1] if history else None
                if RESUME_AFTER_DISCONNECT and last and last['outcome'] == 'infrastructure' and not last['resumed'] \\
                        and (tp.attempt_dir(TRAIN_ROOT, ARM, SEED, last['attempt']) / 'checkpoint').is_dir():
                    ATTEMPT, RESUME = last['attempt'], True
                    print('RESUMING attempt', ATTEMPT, 'for engineering use only: a resumed run is NEVER valid for the FinalTest gate')
                else:
                    ATTEMPT = ACTION['attempt']
                    print(f"{ARM} seed {SEED} (slot {SLOT}{', reserve' if ACTION['reserve'] else ''}): attempt {ATTEMPT}"
                          + (' — from-scratch retry after an infrastructure failure' if ACTION['retry'] else ''))
                assert not STACK_MISMATCHES or ALLOW_STACK_MISMATCH, ('D021 stack mismatch (no attempt was opened): ' + '; '.join(STACK_MISMATCHES))
            ATTEMPT_DIR = tp.attempt_dir(TRAIN_ROOT, ARM, SEED, ATTEMPT)
            if ACTION['kind'] == 'train':
                assert RESUME or not ATTEMPT_DIR.exists(), f'{ATTEMPT_DIR} already exists: attempts are never overwritten'
                ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)
                tp.log_event(LOG, 'resume_start' if RESUME else 'start', arm=ARM, seed=SEED, slot=SLOT, attempt=ATTEMPT,
                             implementation_manifest_sha256=MANIFEST_SHA256)
                args = ['train', '--arm', ARM, '--seed', SEED, '--slot', SLOT, '--attempt', ATTEMPT, '--data', INPUTS / 'phase2_train.json',
                        '--exposure-order', INPUTS / 'EXPOSURE_ORDER.json', '--out', ATTEMPT_DIR, '--implementation-manifest-sha256', MANIFEST_SHA256]
                returncode = step(ATTEMPT_DIR, 'train_phase2.py', *args, *(['--resume'] if RESUME else []),
                                  *(['--allow-stack-mismatch'] if ALLOW_STACK_MISMATCH else []))
                OUTCOME, DETAIL = tp.attempt_outcome(ATTEMPT_DIR)
                tp.log_event(LOG, 'resume_finish' if RESUME else 'finish', arm=ARM, seed=SEED, slot=SLOT, attempt=ATTEMPT,
                             outcome=OUTCOME, detail=DETAIL, returncode=returncode, report_sha256=tp.report_sha(ATTEMPT_DIR))
                PLAN = tp.plan(tp.read_log(LOG))
                print('\\n' + tp.describe_plan(PLAN))
                if OUTCOME in ('numerical', 'protocol'):
                    print('\\n' + '!' * 100 + f'\\n{OUTCOME.upper()} FAILURE — {DETAIL}\\n' + tp.HALT_MESSAGE + '\\n' + '!' * 100)
                assert OUTCOME == 'valid', {
                    'infrastructure': f'Infrastructure failure ({DETAIL}). Run the Download cell, send the ZIP, then re-run all: the plan above decides the retry or the reserve seed.',
                    'resumed_invalid': 'Resumed run finished but is never valid. Set RESUME_AFTER_DISCONNECT = False and re-run all for a fresh attempt if one is left.',
                }.get(OUTCOME, f'{OUTCOME} failure: the study halts. Run the Download cell and send the ZIP.')
            FINAL = ATTEMPT_DIR / 'final_adapter.json'
            final = json.loads(FINAL.read_text())
            print(json.dumps({k: final[k] for k in ('arm', 'seed', 'slot', 'attempt', 'steps', 'adapter_model_sha256', 'adapter_config_sha256',
                                                    'initial_adapter_sha256', 'order_sha256', 'resumed', 'valid_for_gate')}, indent=1))'''
        yield 'code', '''
            # DEV sanity report only (PREREGISTRATION §5): never selects checkpoints, arms or reruns.
            DEV_RUN = ATTEMPT_DIR / 'dev_eval'
            step(ATTEMPT_DIR, 'phase2_eval.py', 'evaluate', '--split', 'dev', '--inputs', INPUTS, '--run-dir', DEV_RUN,
                 '--adapter-dir', ATTEMPT_DIR / 'final_adapter', '--adapter-record', FINAL)'''
        yield 'markdown', '## Download\nRun this cell even after a failure or a refusal: the ZIP carries the error, the logs and a snapshot of the attempt log.'
        yield 'code', '''
            import shutil
            if 'ATTEMPT_DIR' in globals() and ATTEMPT_DIR.exists():
                if LOG.exists():
                    shutil.copyfile(LOG, ATTEMPT_DIR / 'ATTEMPT_LOG.snapshot.jsonl')
                zip_results(ATTEMPT_DIR, PACKAGE / f'Phase2_Train_{ARM}-s{SEED}_{ATTEMPT_DIR.name}.zip', f'{ARM}-s{SEED}/{ATTEMPT_DIR.name}')
            else:  # refused before an attempt was opened (e.g. study halted): send the whole training log tree
                zip_results(STORE / 'train', PACKAGE / f'Phase2_Train_slot{SLOT}_{ARM}_logs.zip', 'train')'''

    return notebook(NAMES['train'], cells_for('train', blob, settings, body, manifest))


def final_test_inputs():
    """(prereg bytes, freeze-manifest text) if the FinalTest notebook may be built, else (None, reason)."""
    if not PREREGISTRATION.exists():
        return None, 'phase2/PREREGISTRATION.md does not exist'
    prereg = PREREGISTRATION.read_bytes()
    if hashlib.sha256(prereg).hexdigest() != PREREGISTRATION_SHA256:
        return None, 'phase2/PREREGISTRATION.md does not match PREREGISTRATION_SHA256 (amend §13 and update the constant)'
    if not ADAPTERS_FROZEN.exists():
        return None, 'phase2/ADAPTERS_FROZEN.md (the §11 freeze manifest of the retained adapters) does not exist yet'
    text = ADAPTERS_FROZEN.read_text(encoding='utf-8')
    try:
        frozen = phase2_eval.parse_frozen(text)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        return None, f'phase2/ADAPTERS_FROZEN.md is not a valid freeze manifest: {error}'
    _, manifest_sha = implementation_manifest()
    if frozen['implementation_manifest_sha256'] != manifest_sha:
        return None, 'ADAPTERS_FROZEN.md records another IMPLEMENTATION_MANIFEST.md (recheck at adapter freeze failed)'
    return prereg, text


def render_final_test(prereg, frozen_text, prereg_sha256=PREREGISTRATION_SHA256, manifest=None):
    manifest = manifest or implementation_manifest()
    blob = payload('final_test', prereg, frozen_text)
    frozen_sha = hashlib.sha256(frozen_text.encode('utf-8')).hexdigest()
    train_sha = train_phase2.phase2_dataset(ROOT)['families_sha256']

    def body(setup):
        yield 'markdown', f'''
            # Phase 2 — FINAL_TEST: unchanged Qwen3-4B + the frozen adapters (PREREGISTRATION §11 with Amendment 1)
            **Run once.** 1 + 3S checkpoints × 100 families × E/R/C (3,000 generations at S = 3; it resumes across sessions from Drive: re-run all; generated responses are never regenerated or retried).
            The gate below refuses to run unless (1) the embedded `phase2/PREREGISTRATION.md` (with Amendment 1) has SHA-256 `{prereg_sha256}`, (2) the embedded freeze manifest `phase2/ADAPTERS_FROZEN.md` is intact, records the embedded implementation manifest and at least one complete seed triplet, and (3) every retained adapter on Drive (`MyDrive/{DRIVE}/train/`) is a valid run (60/60 successful steps, not resumed), paired within its seed, hash-identical to the manifest, and the attempt log still yields the frozen seeds. S = 3 is confirmatory; S = 1 or 2 runs only as a **descriptive-only reduced-S report**; S = 0 never reaches this notebook.
            **Sealed (Amendment 1 item 14):** this notebook prints only completion, checksum and infrastructure status. Answers, scores and accuracy are never shown; the scored records stay in the results ZIP until every evaluation is complete. {PROTOCOL} Adapters are loaded unmerged on the same NF4 base. The analysis script runs afterwards, unchanged.
            **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. A results ZIP with checksums downloads at the end; send it unchanged.'''
        yield 'code', setup
        yield 'code', f'''
            # GATE (model-free): refuse before any model is loaded.
            sys.path.insert(0, str(PACKAGE / 't4_smoke'))
            import phase2_eval
            GATE_PASSED = False
            PREREG_SHA256 = {prereg_sha256!r}
            FROZEN_SHA256 = {frozen_sha!r}
            TRAIN_DATA_SHA256 = {train_sha!r}  # the 160 frozen TRAIN families every adapter must have been trained on
            phase2_eval.check_preregistration((INPUTS / 'PREREGISTRATION.md').read_bytes(), PREREG_SHA256)
            frozen_text = (INPUTS / 'ADAPTERS_FROZEN.md').read_text(encoding='utf-8')
            assert hashlib.sha256(frozen_text.encode('utf-8')).hexdigest() == FROZEN_SHA256, 'Embedded freeze manifest changed: FINAL_TEST refused'
            FROZEN = phase2_eval.parse_frozen(frozen_text)
            assert FROZEN['implementation_manifest_sha256'] == MANIFEST_SHA256, 'Adapters were frozen under another implementation manifest: FINAL_TEST refused'
            S = FROZEN['S']
            CHECKPOINTS = [('base', None, None)] + [(phase2_eval.run_name(a['arm'], a['seed']), a, folder)
                                                     for a, folder in phase2_eval.gate(FROZEN, STORE / 'train', expected_data_sha256=TRAIN_DATA_SHA256)]
            assert len(CHECKPOINTS) == 1 + 3 * S
            MODE = 'CONFIRMATORY (S = 3)' if FROZEN['confirmatory'] else f'DESCRIPTIVE-ONLY reduced-S report (S = {{S}}): no confirmatory label'
            GATE_PASSED = True
            (STORE / 'final_test').mkdir(parents=True, exist_ok=True)
            (STORE / 'final_test' / 'gate.json').write_text(json.dumps({{'preregistration_sha256': PREREG_SHA256, 'freeze_manifest_sha256': FROZEN_SHA256,
                'implementation_manifest_sha256': MANIFEST_SHA256, 'S': S, 'confirmatory': FROZEN['confirmatory'],
                'descriptive_only': FROZEN['descriptive_only'], 'checkpoints': [[name, adapter] for name, adapter, _ in CHECKPOINTS],
                'passed_at': time.time()}}, indent=1))
            print('GATE PASSED:', MODE, [name for name, _, _ in CHECKPOINTS])'''
        yield 'code', GPU
        yield 'code', '''
            assert GATE_PASSED, 'Gate did not pass'
            for name, adapter, folder in CHECKPOINTS:  # sealed: phase2_eval prints completion/checksum/infrastructure only
                run_dir = STORE / 'final_test' / name
                args = ['evaluate', '--split', 'final_test', '--sealed', '--inputs', INPUTS, '--run-dir', run_dir]
                if adapter is not None:
                    record = run_dir.parent / f'{name}_adapter_record.json'
                    if not record.exists():
                        record.write_text(json.dumps(adapter, indent=1))
                    args += ['--adapter-dir', folder, '--adapter-record', record]
                step(run_dir.parent, 'phase2_eval.py', *args)
            def sealed(name):
                path = STORE / 'final_test' / f'{name}_status.json'
                return json.loads(path.read_text()) if path.exists() else {'run': name, 'status': 'NOT STARTED'}
            STATUS = [sealed(name) for name, _, _ in CHECKPOINTS]
            for item in STATUS:
                print(json.dumps({k: item.get(k) for k in ('run', 'status', 'completed', 'expected', 'unresolved', 'attempts',
                                                           'infrastructure_failures', 'results_zip_sha256')}))
            assert all(item['status'] == 'COMPLETE' for item in STATUS), 'Incomplete: re-run all to resume (generated responses are kept, never retried)'
            print('All', len(STATUS), 'FINAL_TEST runs complete.', MODE)'''
        yield 'markdown', '## Download\nIf a run is incomplete, re-run all first; then run this cell. The ZIP holds the sealed scored records; do not open them before every run is complete.'
        yield 'code', "zip_results(STORE / 'final_test', PACKAGE / 'Phase2_FinalTest_results.zip', 'final_test')"

    return notebook(NAMES['final_test'], cells_for('final_test', blob, "USE_DRIVE = True  # the adapters are on Drive; required", body, manifest))


def renders():
    """{kind: notebook text or None}; None means skipped, with the reason in SKIPPED."""
    manifest = implementation_manifest()
    result = {'baseline': render_baseline(manifest), 'train': render_train(manifest)}
    prereg, reason = final_test_inputs()
    result['final_test'] = render_final_test(prereg, reason, manifest=manifest) if prereg is not None else None
    if prereg is None:
        SKIPPED['final_test'] = reason
    return result


SKIPPED = {}


def build(check=False):
    ok = True
    for kind, text in renders().items():
        target = OUT_DIR / NAMES[kind]
        if text is None:
            print(f'SKIPPED {NAMES[kind]}: {SKIPPED[kind]}')
            continue
        if check:
            current = target.exists() and target.read_text(encoding='utf-8') == text
            print(target, 'is current' if current else 'is STALE: rebuild it')
            ok &= current
        else:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
            print(target)
    return ok


if __name__ == '__main__':
    sys.exit(0 if build(check='--check' in sys.argv[1:]) else 1)
