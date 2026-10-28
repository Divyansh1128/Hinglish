"""Build the D021 T4 training-feasibility smoke notebook for Qwen3-4B.

The notebook is self-contained: t4_smoke/train_smoke.py, labels.py and
protocol.py (frozen prompt v2), the 16 smoke families selected from the frozen
TRAIN files by the fixed rule in train_smoke.SELECTION_RULE, and the D021 pins.
Nothing to upload. Each training phase runs in a fresh Python process, so the
reload after update 4 is a new model load.

Usage from the repository root: python3 -B colab_notebooks/build_training_smoke_notebook.py
Check that the committed notebook is current without writing: add --check.
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
OUT_DIR = ROOT / 'colab_notebooks' / 'training_smoke'
NAME = 'TrainSmoke_Qwen3-4B.ipynb'
STAMP = (2026, 10, 27, 0, 0, 0)
CODE = ('train_smoke.py', 'labels.py', 'protocol.py')

sys.path.insert(0, str(ROOT))
from t4_smoke import train_smoke  # noqa: E402


def requirements():
    return ('# D021 training stack. Colab supplies torch ' + train_smoke.TORCH_BUILD + '; it is recorded, not replaced.\n'
            + ''.join(f'{name}=={version}\n' for name, version in train_smoke.PINS.items()))


def payload():
    buffer = io.BytesIO()

    def put(archive, name, content):
        info = zipfile.ZipInfo(name, date_time=STAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content)

    data = train_smoke.smoke_dataset(ROOT)
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in CODE:
            put(archive, 't4_smoke/' + name, (ROOT / 't4_smoke' / name).read_bytes())
        put(archive, 'smoke/smoke_data.json', json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        put(archive, 'requirements-train.txt', requirements())
    return buffer.getvalue(), data


def render():
    blob, data = payload()
    ids = ', '.join(family['family_id'] for family in data['families'])
    cells = []

    def add(kind, source):
        source = textwrap.dedent(source).strip() + '\n'
        cell = {'cell_type': kind, 'id': f'ts-cell-{len(cells):02d}', 'metadata': {}, 'source': source}
        if kind == 'code':
            cell.update(outputs=[], execution_count=None)
        cells.append(cell)

    add('markdown', f'''
        # T4 training-feasibility smoke test — Qwen3-4B QLoRA (decision D021)
        **Engineering test only.** It measures whether the Phase-2 training recipe fits and how fast it runs on a free T4. Its adapters are thrown away: never evaluate them or report their answers.
        Recipe: NF4 double-quant, FP16 compute, LoRA r16/alpha32/dropout 0.05 on all 7 projections (fp32 adapters), AdamW lr 1e-4, microbatch 1 × accumulation 16, sequence cap 1024, no packing, non-reentrant gradient checkpointing, SDPA math, completion-only labels. Project-owned loop, no TRL.
        Data: 16 TRAIN families ({ids}), chosen by a fixed seeded rule (below). No DEV or FINAL_TEST data is included.
        Per arm (E+E, E+R, E+C): updates 1–4, save adapter/optimizer/scaler/RNG, reload in a **new process** (new model load), check the restored state, run updates 5–6. Then a 32-update E+C stability probe.
        **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. Expect roughly 40–120 minutes. A results ZIP with checksums downloads at the end; send it unchanged.
        Drive is on by default (`USE_DRIVE = True`) so a disconnect can resume; allow access when asked (re-run all; completed phases are skipped).''')
    add('markdown', f'''
        **Selection rule:** {train_smoke.SELECTION_RULE}
        **Go/no-go (D021, decided before results):** worst-arm median over timed updates 3–6 ≤ 56 s/update → stay on Colab; 56–150 → Kaggle 2×T4; > 150 → fall back to Qwen3-1.7B. Also required: no OOM, ≥ 2 GiB minimum free device memory, finite losses, no GradScaler skips after update 4, reloaded state and probe within atol = rtol = 1e-3.''')
    add('code', f'''
        import os, sys, json, base64, io, zipfile, hashlib, subprocess, time
        from pathlib import Path
        RUN_NAME = 'trainsmoke-Qwen3-4B'
        USE_DRIVE = True  # resume after a disconnect; set False to keep everything in the runtime
        ALLOW_STACK_MISMATCH = False  # True only to measure anyway on a changed Colab image; the result is then flagged
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        os.environ['PYTHONHASHSEED'] = '0'
        os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'  # download bars would become thousands of streamed lines
        PACKAGE = Path('/content/hinglish_trainsmoke') if Path('/content').exists() else Path.cwd() / 'hinglish_trainsmoke'
        PACKAGE.mkdir(parents=True, exist_ok=True)
        blob = base64.b64decode({base64.b64encode(blob).decode()!r})
        assert hashlib.sha256(blob).hexdigest() == {hashlib.sha256(blob).hexdigest()!r}
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
            z.extractall(PACKAGE)
        DATA = PACKAGE / 'smoke/smoke_data.json'
        data = json.loads(DATA.read_text())
        assert len(data['families']) == 16 and all(f['split_role'] == 'CONFIRM_TRAIN' for f in data['families'])
        print('Smoke families:', ', '.join(f['family_id'] for f in data['families']))
        print('Data SHA-256:', data['families_sha256'])
        if USE_DRIVE and Path('/content').exists():  # Drive only inside Colab
            from google.colab import drive
            drive.mount('/content/drive')
            OUT = Path('/content/drive/MyDrive/Hinglish_TrainSmoke') / RUN_NAME
        else:
            OUT = PACKAGE / 'runs' / RUN_NAME
        OUT.mkdir(parents=True, exist_ok=True)
        try:  # Qwen3-4B is ungated; a token only avoids anonymous rate limits.
            from google.colab import userdata
            os.environ['HF_TOKEN'] = (userdata.get('HF_TOKEN') or '').strip() or os.environ.get('HF_TOKEN', '')
        except Exception as error:
            print('No HF_TOKEN Colab secret (' + type(error).__name__ + '); downloading anonymously.')
        if not os.environ.get('HF_TOKEN'):
            os.environ.pop('HF_TOKEN', None)

        def complete(path):
            return path.exists() and json.loads(path.read_text()).get('status') == 'COMPLETE'

        def step(*args):
            """Run one phase in a fresh Python process, stream its output and log the attempt."""
            command = [sys.executable, '-u', str(PACKAGE / 't4_smoke/train_smoke.py'), *args, '--out', str(OUT)]
            if args[0] != 'decide':
                command += ['--data', str(DATA)] + (['--allow-stack-mismatch'] if ALLOW_STACK_MISMATCH else [])
            started, returncode = time.time(), None
            try:
                with open(OUT / 'log.txt', 'a') as log, subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
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
                with open(OUT / 'attempts.jsonl', 'a') as attempts:
                    attempts.write(json.dumps({{'args': list(args), 'returncode': returncode, 'started': started, 'seconds': time.time() - started}}) + '\\n')
            return returncode''')
    add('code', '''
        try:
            gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()
        except FileNotFoundError:  # CPU runtime: no nvidia-smi at all
            gpu = ''
        print('GPU:', gpu or 'none')
        assert 'T4' in gpu, 'Select Runtime → Change runtime type → T4 GPU'
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(PACKAGE / 'requirements-train.txt')], check=True)
        # A fresh interpreter sees the installed versions; this kernel never imports torch.
        print(subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import train_smoke as t, json; '
                              'v = t.versions(); print(json.dumps(v, indent=1)); print("D021 stack mismatches:", t.stack_mismatches(v) or "none")',
                              str(PACKAGE / 't4_smoke')], capture_output=True, text=True, check=True).stdout)''')
    add('code', '''
        # Tokenizer-only preflight: completion-only masks and identical E/R/C targets for all 16 families.
        if not complete(OUT / 'preflight_report.json'):
            step('preflight')
        PREFLIGHT = OUT / 'preflight_report.json'
        assert PREFLIGHT.exists() and json.loads(PREFLIGHT.read_text()).get('passed'), 'Preflight failed (error printed above): run the Download cell and send the ZIP'
        print(json.dumps(json.loads(PREFLIGHT.read_text())['mask_audit']['arms'], indent=1))''')
    add('code', '''
        # Six updates per arm: 1-4 in one process, save; 5-6 in a new process after a fresh model load and state check.
        for arm in ('EE', 'ER', 'EC'):
            folder = OUT / arm
            if complete(folder / 'resume_report.json'):
                print(arm, 'already complete')
                continue
            if not complete(folder / 'first_report.json') or not (folder / 'checkpoint' / 'state.pt').exists():
                step('run', '--phase', 'first', '--arm', arm)
            if complete(folder / 'first_report.json'):
                step('run', '--phase', 'resume', '--arm', arm)''')
    add('code', '''
        # 32-update E+C stability probe at the real learning rate (fp16 overflow can appear only as the adapter moves).
        if not complete(OUT / 'EC' / 'probe_report.json'):
            step('run', '--phase', 'probe', '--arm', 'EC')''')
    add('code', '''
        step('decide')
        decision = json.loads((OUT / 'decision.json').read_text())
        print('\\nDECISION:', decision['decision'], '—', decision['message'])''')
    add('markdown', '''
        ## Download
        If a phase failed or the runtime disconnected, re-run all cells: completed phases are skipped and every attempt is logged. Then run this cell. Large checkpoint tensors stay out of the ZIP; their SHA-256 is listed.''')
    add('code', '''
        archive = PACKAGE / 'TrainSmoke_results_Qwen3-4B.zip'
        files, large = [], {}
        for path in sorted(OUT.rglob('*')):
            if path.is_file():
                if path.suffix in ('.pt', '.safetensors'):
                    large[str(path.relative_to(OUT))] = hashlib.sha256(path.read_bytes()).hexdigest()
                else:
                    files.append(path)
        sums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT)}\\n' for p in files)
        sums += ''.join(f'{digest}  {name}  (not included)\\n' for name, digest in large.items())
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in files:
                z.write(path, str(Path(RUN_NAME) / path.relative_to(OUT)))
            z.writestr(str(Path(RUN_NAME) / 'SHA256SUMS.txt'), sums)
        print(sums)
        print('Return:', archive, 'SHA-256', hashlib.sha256(archive.read_bytes()).hexdigest())
        try:
            from google.colab import files as colab_files
            colab_files.download(str(archive))
        except ImportError:
            print('Local: ZIP saved on disk.')''')
    notebook = {'nbformat': 4, 'nbformat_minor': 5, 'cells': cells,
                'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                             'language_info': {'name': 'python'}, 'colab': {'name': NAME}, 'accelerator': 'GPU'}}
    return json.dumps(notebook, indent=2, ensure_ascii=False) + '\n'


def build(check=False):
    target = OUT_DIR / NAME
    text = render()
    if check:
        current = target.exists() and target.read_text(encoding='utf-8') == text
        print(target, 'is current' if current else 'is STALE: rebuild it')
        return current
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    print(target)
    return target


if __name__ == '__main__':
    result = build(check='--check' in sys.argv[1:])
    sys.exit(0 if result else 1)
