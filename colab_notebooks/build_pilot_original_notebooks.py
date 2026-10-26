"""Build the original-pilot evaluation notebooks (decision D036), one per pilot backbone.

Same structure as the Pilot-B builder (build_pilot_b_notebooks.py): the unchanged Test 1
engine, scorer and frozen prompt, the secondary-analysis module, and the frozen original-pilot
cohort (24 families, 72 prompts; pilot_original/FROZEN.md) in the engine's `pilot_adjudicated`
mode. Nothing to upload.

Usage from the repository root: python3 -B colab_notebooks/build_pilot_original_notebooks.py
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
OUT_DIR = ROOT / 'colab_notebooks' / 'pilot_original_eval'
DATASET = ROOT / 'pilot_original' / 'cohort_dataset.json'
SPLITS = ROOT / 'pilot_original' / 'cohort_splits.json'
STAMP = (2026, 10, 26, 0, 0, 0)
NOTEBOOKS = {'Qwen/Qwen3-4B': 'PilotOrig_Qwen3-4B.ipynb',
             'Qwen/Qwen3-8B': 'PilotOrig_Qwen3-8B.ipynb',
             'meta-llama/Llama-3.2-3B-Instruct': 'PilotOrig_Llama-3.2-3B.ipynb'}
GATED = {'meta-llama/Llama-3.2-3B-Instruct'}

sys.path.insert(0, str(ROOT / 'test1_pilot'))
sys.path.insert(0, str(ROOT / 'secondary_analysis'))


def cohort_inputs():
    """Return the frozen (dataset, splits) built by pilot_original/build_cohort.py, unchanged."""
    return json.loads(DATASET.read_text(encoding='utf-8')), json.loads(SPLITS.read_text(encoding='utf-8'))


def payload():
    import build_gpu_smoke
    buffer = io.BytesIO()

    def put(archive, name, content):
        info = zipfile.ZipInfo(name, date_time=STAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content)

    dataset, splits = cohort_inputs()
    with zipfile.ZipFile(io.BytesIO(build_gpu_smoke.embedded_payload())) as old, \
            zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as new:
        for name in old.namelist():
            put(new, name, old.read(name))
        for path in sorted((ROOT / 'secondary_analysis').glob('*.py')):
            if path.name != 'build_format_notebook.py':
                put(new, 'secondary_analysis/' + path.name, path.read_bytes())
        put(new, 'pilot_original/dataset.json', DATASET.read_bytes())
        put(new, 'pilot_original/splits.json', SPLITS.read_bytes())
    return buffer.getvalue()


def build(model_id):
    name = NOTEBOOKS[model_id]
    short = model_id.split('/')[-1]
    blob = payload()
    cells = []

    def add(kind, source):
        source = textwrap.dedent(source).strip() + '\n'
        cell = {'cell_type': kind, 'id': f'po-cell-{len(cells):02d}', 'metadata': {}, 'source': source}
        if kind == 'code':
            cell.update(outputs=[], execution_count=None)
        cells.append(cell)

    add('markdown', f'''
        # Original-pilot evaluation — {model_id}
        **Real evaluation run** on the frozen original-pilot cohort: 24 families accepted by an adjudicator after two independent reviews × E/R/C = 72 prompts. Pre-registered plan: `pilot_original/PREREGISTRATION.md` (decision D036). Reported separately from Pilot-B.
        Frozen protocol: prompt v2, greedy non-thinking decoding, NF4 + FP16, scorer v1.0.0. **Do not change any setting.**
        **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. Takes about 10–15 minutes. A results ZIP downloads at the end; send it unchanged.
        Optional: set `USE_DRIVE = True` in the next cell so a disconnect can resume (re-run all with the same settings).''')
    add('code', f'''
        import os, sys, json, base64, io, zipfile, hashlib, subprocess, traceback
        from pathlib import Path
        MODEL_ID = {model_id!r}
        RUN_NAME = 'pilotorig-{short}'
        USE_DRIVE = False
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        PACKAGE = Path('/content/hinglish_pilotorig') if Path('/content').exists() else Path.cwd() / 'hinglish_pilotorig'
        PACKAGE.mkdir(parents=True, exist_ok=True)
        blob = base64.b64decode({base64.b64encode(blob).decode()!r})
        assert hashlib.sha256(blob).hexdigest() == {hashlib.sha256(blob).hexdigest()!r}
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
            z.extractall(PACKAGE)
        sys.path.insert(0, str(PACKAGE))
        from hinglish_pilot.engine import default_config, environment, read, write, run, utc
        from hinglish_pilot.data import validate
        from hinglish_pilot.report import analyze, export
        from secondary_analysis.report_secondary import analyze as analyze_secondary
        DATASET, SPLITS = read(PACKAGE / 'pilot_original/dataset.json'), read(PACKAGE / 'pilot_original/splits.json')
        print(json.dumps(validate(DATASET, SPLITS, 'pilot_adjudicated'), indent=1))
        if USE_DRIVE:
            from google.colab import drive
            drive.mount('/content/drive')
            RUNS = Path('/content/drive/MyDrive/Hinglish_PilotOrig')
        else:
            RUNS = PACKAGE / 'runs'
        RUN_DIR = RUNS / RUN_NAME
        RUNS.mkdir(parents=True, exist_ok=True)
        if {model_id in GATED!r}:
            # Gated model: needs a Hugging Face read token (Colab secret HF_TOKEN, or paste when asked).
            token = ''
            try:
                from google.colab import userdata
                token = (userdata.get('HF_TOKEN') or '').strip()
                print('HF_TOKEN read from Colab secret')
            except Exception as error:
                print('HF_TOKEN Colab secret not available (' + type(error).__name__ + '): turn on Notebook access for it in the key sidebar, or paste the token now.')
            import getpass
            while not token.startswith('hf_'):
                raw = getpass.getpass('Paste your Hugging Face read token (starts with hf_): ')
                if isinstance(raw, dict):  # Colab can return the widget payload instead of text
                    raw = raw.get('value') or raw.get('text') or ''
                token = str(raw or '').strip()
                if not token.startswith('hf_'):
                    print('That does not look like a token (it should start with hf_). Try again.')
            os.environ['HF_TOKEN'] = token
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'huggingface-hub==0.30.2'], check=True)
            from huggingface_hub import login, auth_check
            login(token=token, add_to_git_credential=False)
            auth_check(MODEL_ID, token=token)  # clear error if this token lacks access
            print('Access to', MODEL_ID, 'confirmed')''')
    add('code', '''
        import torch
        assert torch.cuda.is_available(), 'Select Runtime → Change runtime type → T4 GPU'
        print('GPU:', torch.cuda.get_device_name(0), 'CUDA:', torch.version.cuda)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(PACKAGE / 'requirements-colab.txt')], check=True)
        write(RUNS / f'{RUN_NAME}_environment.json', environment())''')
    add('code', '''
        from hinglish_pilot.hf_backend import resolve_config, HFBackend
        CONFIG = resolve_config(default_config('pilot_adjudicated', MODEL_ID), RUN_DIR)
        backend = HFBackend(CONFIG)
        write(RUNS / f'{RUN_NAME}_model_load_report.json', backend.load_report)
        print('Model loaded on', backend.metadata['hardware'], 'revision', CONFIG['model_revision'])''')
    add('code', '''
        progress = lambda done, total, item: print(f'{done}/{total}: {item["rendering_id"]} {item["latency_seconds"]:.1f}s', flush=True)
        manifest = run(RUN_DIR, DATASET, SPLITS, CONFIG, backend, progress=progress)
        print('Run status:', manifest['status'], manifest['completed'], '/', manifest['expected'])
        metrics, _ = analyze(RUN_DIR)
        print((RUN_DIR / 'summary.md').read_text())
        if manifest['status'] == 'COMPLETE':
            _, folder = analyze_secondary(RUN_DIR)
            print((folder / 'secondary_summary.md').read_text())''')
    add('markdown', '''
        ## Download
        If the run stopped early, re-run all cells with the same settings: completed prompts are kept and only missing ones run. Then run this cell.''')
    add('code', f'''
        results = export(RUN_DIR)
        archive = PACKAGE / 'PilotOrig_results_{short}.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(results, results.name)
            for path in sorted(RUN_DIR.rglob('*')):
                if path.is_file() and 'secondary_diagnostic_' in str(path):
                    z.write(path, str(path.relative_to(RUN_DIR)))
            for path in sorted(RUNS.glob(f'{{RUN_NAME}}_*.json')):
                z.write(path, path.name)
        print('Return:', archive)
        try:
            from google.colab import files
            files.download(str(archive))
        except ImportError:
            print('Local: ZIP saved on disk.')''')
    notebook = {'nbformat': 4, 'nbformat_minor': 5, 'cells': cells,
                'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                             'language_info': {'name': 'python'}, 'colab': {'name': name}, 'accelerator': 'GPU'}}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / name
    target.write_text(json.dumps(notebook, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(target)
    return target


if __name__ == '__main__':
    for model in NOTEBOOKS:
        build(model)
