"""Build the Phase-2 notebooks (D043; binding plan phase2/PREREGISTRATION.md) into colab_notebooks/phase2/.

- Phase2_Baseline_DEV.ipynb: unchanged Qwen3-4B on DEV, the §5 ceiling check (flag fires at C >= 38/40).
- Phase2_Train.ipynb: one notebook for all 9 runs (ARM and SEED at the top); trains 60 updates, then a DEV sanity
  evaluation; downloads a ZIP with the adapter hashes, training log and DEV results (weights stay on Drive).
- Phase2_FinalTest.ipynb: unchanged model + the 9 frozen adapters on FINAL_TEST. Built only when
  phase2/PREREGISTRATION.md matches PREREGISTRATION_SHA256 below AND phase2/ADAPTERS_FROZEN.md exists (§11);
  otherwise skipped with a message. At run time it refuses unless both embedded hashes match and every adapter
  on Drive matches the freeze manifest.

Every notebook is self-contained (code and data embedded, nothing to upload). Training notebooks never contain
FINAL_TEST data. Usage from the repository root:
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
# SHA-256 of the committed pre-registration (commit 58d330d). Any edit needs an amendment and a new constant (§13).
PREREGISTRATION_SHA256 = '74be23282ce9e53e3a69456bebf89f9cd71d3859b80090692e4548ef34182840'
ADAPTERS_FROZEN = ROOT / 'phase2' / 'ADAPTERS_FROZEN.md'
T4_CODE = ('train_smoke.py', 'labels.py', 'protocol.py', 'train_phase2.py', 'phase2_eval.py')
# The secondary modules embedded in the Pilot-B notebooks (numeric_literal_v1 etc.); later additions need a rebuild.
SECONDARY = ('__init__.py', 'cmi.py', 'numeric_endpoint.py', 'report_secondary.py')
DRIVE = 'Hinglish_Phase2'

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'test1_pilot'))
from t4_smoke import phase2_eval, train_phase2, train_smoke  # noqa: E402


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
print(subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import train_smoke as t, json; '
                      'v = t.versions(); print(json.dumps(v, indent=1)); print("D021 stack mismatches:", t.stack_mismatches(v) or "none")',
                      str(PACKAGE / 't4_smoke')], capture_output=True, text=True, check=True).stdout)
'''

PROTOCOL = ('Frozen protocol (PREREGISTRATION §4): prompt `test1-english-final-v2`, greedy non-thinking decoding, NF4 + FP16, '
            'SDPA math, output cap 1,024 tokens, scorer v1.0.0, engine seed 11. **Do not change any setting.**')


def cells_for(kind, blob, settings, body):
    cells = []

    def add(cell_kind, source):
        source = textwrap.dedent(source).strip() + '\n'
        cell = {'cell_type': cell_kind, 'id': f'p2-{kind}-{len(cells):02d}', 'metadata': {}, 'source': source}
        if cell_kind == 'code':
            cell.update(outputs=[], execution_count=None)
        cells.append(cell)

    setup = (SETUP.replace('%SETTINGS%', textwrap.dedent(settings).strip())
             .replace('%BLOB%', repr(base64.b64encode(blob).decode())).replace('%DIGEST%', repr(hashlib.sha256(blob).hexdigest()))
             .replace('%DRIVE%', DRIVE))
    for cell_kind, source in body(setup):
        add(cell_kind, source)
    return cells


def notebook(name, cells):
    return json.dumps({'nbformat': 4, 'nbformat_minor': 5, 'cells': cells,
                       'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                                    'language_info': {'name': 'python'}, 'colab': {'name': name}, 'accelerator': 'GPU'}},
                      indent=2, ensure_ascii=False) + '\n'


def render_baseline():
    blob = payload('baseline')

    def body(setup):
        yield 'markdown', f'''
            # Phase 2 — unchanged Qwen3-4B on DEV (ceiling check, PREREGISTRATION §5)
            Run this **once, before any training run**. 40 DEV families × E/R/C = 120 generations with the unchanged model.
            {PROTOCOL}
            The D040 ceiling flag fires if DEV C strict accuracy is ≥ 95% (≥ 38/40); the result is printed at the end. DEV is a sanity set: it never selects anything. No FINAL_TEST data is in this notebook.
            **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all** (about 15–20 minutes). Drive is on by default so a disconnect resumes (re-run all; finished prompts are kept). A results ZIP with checksums downloads at the end; send it unchanged.'''
        yield 'code', setup
        yield 'code', GPU
        yield 'code', '''
            RUN_DIR = STORE / 'baseline_dev' / 'base'
            step(RUN_DIR.parent, 'phase2_eval.py', 'evaluate', '--split', 'dev', '--inputs', INPUTS, '--run-dir', RUN_DIR)
            FLAG = RUN_DIR.parent / 'base_ceiling_flag.json'
            assert FLAG.exists(), 'Evaluation incomplete (see above): re-run all to resume, then download'
            flag = json.loads(FLAG.read_text())
            print('\\nCEILING FLAG (C >= 38/40):', 'FIRES' if flag['flag'] else 'does not fire', f"— DEV C {flag['C_correct']}/{flag['denominator']}")'''
        yield 'markdown', '## Download\nIf the run stopped early, re-run all cells first. Then run this cell.'
        yield 'code', "zip_results(STORE / 'baseline_dev', PACKAGE / 'Phase2_Baseline_DEV_results.zip', 'baseline_dev')"

    return notebook(NAMES['baseline'], cells_for('baseline', blob, "USE_DRIVE = True  # resume after a disconnect", body))


def render_train():
    blob = payload('train')
    settings = '''
        ARM = 'EC'   # 'EE', 'ER' or 'EC'
        SEED = 11    # 11, 22, 33; reserve seeds 44 then 55 only under PREREGISTRATION §10
        USE_DRIVE = True  # adapters and checkpoints live on Drive; keep this on
        RESUME_AFTER_DISCONNECT = False  # True continues a started attempt, but §10 then treats the run as failed
        ALLOW_STACK_MISMATCH = False
        assert ARM in ('EE', 'ER', 'EC') and SEED in (11, 22, 33, 44, 55)'''

    def body(setup):
        yield 'markdown', f'''
            # Phase 2 — QLoRA training run (D043) + DEV sanity check
            One notebook for all 9 runs: set **ARM** and **SEED** in the next cell (E+E/E+R/E+C × seeds 11/22/33) and run all. Each run: all 160 TRAIN families, 320 examples, **60 updates** of 16 examples (3 passes), AdamW lr 1e-4 with 6 warm-up updates then cosine decay to 1e-5, the D021 recipe otherwise (NF4 + FP16, LoRA r16/α32/dropout 0.05 on all 7 projections, fp32 adapter). Family order and LoRA initialisation are identical across arms within a seed. About 25 minutes of training plus about 15 minutes of DEV evaluation on a T4.
            After update 60 the adapter is saved to Drive with the SHA-256 of `adapter_model.safetensors` and `adapter_config.json`; then the adapter is evaluated **on DEV as a sanity report only** (never used for selection). {PROTOCOL} No FINAL_TEST data is in this notebook.
            **Disconnects (PREREGISTRATION §10):** a disconnect, crash or OOM is an infrastructure failure. Re-running the notebook starts a **fresh attempt from scratch** with the same seed (checkpoints every 10 updates are kept only so that `RESUME_AFTER_DISCONNECT = True` can finish a run for engineering use; the manifest then records the resume and the FinalTest gate refuses that adapter). If the rerun also fails, switch this seed to reserve seed 44 (then 55) **for all three arms**.
            **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. A ZIP (adapter hashes, training log, DEV results; weights stay on Drive) downloads at the end; send it unchanged.'''
        yield 'code', setup
        yield 'code', GPU
        yield 'code', '''
            RUN_ROOT = STORE / 'train' / f'{ARM}-s{SEED}'
            RUN_ROOT.mkdir(parents=True, exist_ok=True)
            def train_status(folder):
                report = folder / 'train_report.json'
                return json.loads(report.read_text()).get('status') if report.exists() else None
            attempts = sorted(RUN_ROOT.glob('attempt-*'))
            done = [a for a in attempts if train_status(a) == 'COMPLETE' and (a / 'final_adapter.json').exists()]
            RESUME = False
            if done:
                ATTEMPT_DIR = done[0]
                print('Already trained:', ATTEMPT_DIR.name)
            elif attempts and RESUME_AFTER_DISCONNECT:
                ATTEMPT_DIR, RESUME = attempts[-1], True
                print('RESUMING', ATTEMPT_DIR.name, '— recorded as resumed; §10 treats this run as failed and the FinalTest gate refuses it')
            else:
                if attempts:
                    print('Earlier attempt(s) did not complete:', [a.name for a in attempts], '— §10: fresh rerun from scratch')
                assert len(attempts) < 2, (f'{ARM} seed {SEED} already failed twice. PREREGISTRATION §10: replace seed {SEED} by reserve '
                                           'seed 44 (then 55) for ALL THREE arms; do not evaluate this seed.')
                ATTEMPT_DIR = RUN_ROOT / f'attempt-{len(attempts) + 1:02d}'
            ATTEMPT = int(ATTEMPT_DIR.name.split('-')[1])
            if not done:
                args = ['train', '--arm', ARM, '--seed', SEED, '--attempt', ATTEMPT, '--data', INPUTS / 'phase2_train.json', '--out', ATTEMPT_DIR]
                step(ATTEMPT_DIR, 'train_phase2.py', *args, *(['--resume'] if RESUME else []), *(['--allow-stack-mismatch'] if ALLOW_STACK_MISMATCH else []))
            FINAL = ATTEMPT_DIR / 'final_adapter.json'
            assert FINAL.exists(), 'Training did not complete (error above). Run the Download cell, send the ZIP, then re-run all for a fresh attempt.'
            final = json.loads(FINAL.read_text())
            print(json.dumps({k: final[k] for k in ('arm', 'seed', 'attempt', 'adapter_model_sha256', 'adapter_config_sha256', 'initial_adapter_sha256', 'resumed')}, indent=1))'''
        yield 'code', '''
            # DEV sanity report only (PREREGISTRATION §5): never selects checkpoints, arms or reruns.
            DEV_RUN = ATTEMPT_DIR / 'dev_eval'
            step(ATTEMPT_DIR, 'phase2_eval.py', 'evaluate', '--split', 'dev', '--inputs', INPUTS, '--run-dir', DEV_RUN,
                 '--adapter-dir', ATTEMPT_DIR / 'final_adapter', '--adapter-record', FINAL)'''
        yield 'markdown', '## Download\nRun this cell even after a failure: the ZIP carries the error and the logs.'
        yield 'code', "zip_results(ATTEMPT_DIR, PACKAGE / f'Phase2_Train_{ARM}-s{SEED}_{ATTEMPT_DIR.name}.zip', f'{ARM}-s{SEED}/{ATTEMPT_DIR.name}')"

    return notebook(NAMES['train'], cells_for('train', blob, settings, body))


def final_test_inputs():
    """(prereg bytes, freeze-manifest text) if the FinalTest notebook may be built, else (None, reason)."""
    if not PREREGISTRATION.exists():
        return None, 'phase2/PREREGISTRATION.md does not exist'
    prereg = PREREGISTRATION.read_bytes()
    if hashlib.sha256(prereg).hexdigest() != PREREGISTRATION_SHA256:
        return None, 'phase2/PREREGISTRATION.md does not match PREREGISTRATION_SHA256 (amend §13 and update the constant)'
    if not ADAPTERS_FROZEN.exists():
        return None, 'phase2/ADAPTERS_FROZEN.md (the §11 freeze manifest of the 9 trained adapters) does not exist yet'
    text = ADAPTERS_FROZEN.read_text(encoding='utf-8')
    try:
        phase2_eval.parse_frozen(text)
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        return None, f'phase2/ADAPTERS_FROZEN.md is not a valid freeze manifest: {error}'
    return prereg, text


def render_final_test(prereg, frozen_text, prereg_sha256=PREREGISTRATION_SHA256):
    blob = payload('final_test', prereg, frozen_text)
    frozen_sha = hashlib.sha256(frozen_text.encode('utf-8')).hexdigest()
    train_sha = train_phase2.phase2_dataset(ROOT)['families_sha256']

    def body(setup):
        yield 'markdown', f'''
            # Phase 2 — FINAL_TEST: unchanged Qwen3-4B + the 9 frozen adapters (PREREGISTRATION §11)
            **Confirmatory evaluation. Run once.** 10 checkpoints × 100 families × E/R/C = 3,000 generations (about 6–7 T4-hours; it resumes across sessions from Drive: re-run all, finished prompts are never regenerated).
            The gate below refuses to run unless (1) the embedded `phase2/PREREGISTRATION.md` has SHA-256 `{prereg_sha256}`, (2) the embedded freeze manifest `phase2/ADAPTERS_FROZEN.md` is intact, and (3) all 9 adapters on Drive (`MyDrive/{DRIVE}/train/`) are complete, not resumed, paired within each seed and hash-identical to the manifest.
            {PROTOCOL} Adapters are loaded unmerged on the same NF4 base. Only completeness and checksum checks happen here; the analysis script runs afterwards, unchanged.
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
            CHECKPOINTS = [('base', None, None)] + [(phase2_eval.run_name(a['arm'], a['seed']), a, folder)
                                                     for a, folder in phase2_eval.gate(FROZEN, STORE / 'train', expected_data_sha256=TRAIN_DATA_SHA256)]
            assert len(CHECKPOINTS) == 10
            GATE_PASSED = True
            (STORE / 'final_test').mkdir(parents=True, exist_ok=True)
            (STORE / 'final_test' / 'gate.json').write_text(json.dumps({{'preregistration_sha256': PREREG_SHA256, 'freeze_manifest_sha256': FROZEN_SHA256,
                'checkpoints': [[name, adapter] for name, adapter, _ in CHECKPOINTS], 'passed_at': time.time()}}, indent=1))
            print('GATE PASSED:', [name for name, _, _ in CHECKPOINTS])'''
        yield 'code', GPU
        yield 'code', '''
            assert GATE_PASSED, 'Gate did not pass'
            for name, adapter, folder in CHECKPOINTS:
                run_dir = STORE / 'final_test' / name
                args = ['evaluate', '--split', 'final_test', '--inputs', INPUTS, '--run-dir', run_dir]
                if adapter is not None:
                    record = run_dir.parent / f'{name}_adapter_record.json'
                    record.write_text(json.dumps(adapter, indent=1))
                    args += ['--adapter-dir', folder, '--adapter-record', record]
                step(run_dir.parent, 'phase2_eval.py', *args)
            status = {name: json.loads((STORE / 'final_test' / name / 'run_manifest.json').read_text())['status']
                      if (STORE / 'final_test' / name / 'run_manifest.json').exists() else 'NOT STARTED' for name, _, _ in CHECKPOINTS}
            print(json.dumps(status, indent=1))
            assert all(value == 'COMPLETE' for value in status.values()), 'Incomplete: re-run all to resume (finished prompts are kept)'
            '''
        yield 'markdown', '## Download\nIf a run is incomplete, re-run all first; then run this cell.'
        yield 'code', "zip_results(STORE / 'final_test', PACKAGE / 'Phase2_FinalTest_results.zip', 'final_test')"

    return notebook(NAMES['final_test'], cells_for('final_test', blob, "USE_DRIVE = True  # the adapters are on Drive; required", body))


def renders():
    """{kind: notebook text or None}; None means skipped, with the reason in SKIPPED."""
    result = {'baseline': render_baseline(), 'train': render_train()}
    prereg, reason = final_test_inputs()
    result['final_test'] = render_final_test(prereg, reason) if prereg is not None else None
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
