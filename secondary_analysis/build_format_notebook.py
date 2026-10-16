"""Build the FMT2 format-compliance Colab notebook (decision D019).

Runs the 12 EXCLUDED FMT2 fixture families (36 prompts) through the unchanged
Test 1 engine, frozen prompt and Qwen3-4B T4 recipe, then reports scorer
v1.0.0 beside numeric_literal_v1. Development evidence only, never pilot data.
The engine's demo mode accepts 1-6 families, so fixtures run as two parts.

Usage from the repository root: python3 -B secondary_analysis/build_format_notebook.py
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
HERE = Path(__file__).resolve().parent
OUT_DIR = ROOT / 'colab_notebooks' / 'model_screening'
# One self-contained Colab notebook per model: same excluded fixtures, prompt, decoding and scorer.
NOTEBOOKS = {'Qwen/Qwen3-4B': 'ModelTest_Qwen3-4B.ipynb',
             'Qwen/Qwen3-8B': 'ModelTest_Qwen3-8B.ipynb',
             'Qwen/Qwen3-1.7B': 'ModelTest_Qwen3-1.7B.ipynb',
             'microsoft/Phi-4-mini-instruct': 'ModelTest_Phi-4-mini.ipynb',
             'ibm-granite/granite-3.3-2b-instruct': 'ModelTest_Granite-3.3-2B.ipynb',
             'google/gemma-3-4b-it': 'ModelTest_Gemma-3-4B.ipynb',
             'meta-llama/Llama-3.2-3B-Instruct': 'ModelTest_Llama-3.2-3B.ipynb'}
NAME = NOTEBOOKS['Qwen/Qwen3-4B']
GATED = {'google/gemma-3-4b-it', 'meta-llama/Llama-3.2-3B-Instruct'}
FIXTURES = HERE / 'format_fixtures.json'
PART_SIZE = 6
STAMP = (2026, 10, 14, 0, 0, 0)

sys.path.insert(0, str(ROOT / 'test1_pilot'))


def demo_parts(fixtures=None):
    """Convert the fixture container into two test1-1 demo datasets + splits."""
    fixtures = fixtures or json.loads(FIXTURES.read_text(encoding='utf-8'))
    families = fixtures['families']
    parts = []
    for index in range(0, len(families), PART_SIZE):
        chunk = families[index:index + PART_SIZE]
        name = 'fmt2-part-' + 'ab'[index // PART_SIZE]
        converted = [dict(
            family_id=f['family_id'], source_family_id=f['source_family_id'],
            template_group_id=f['template_group_id'], topic=f['topic'], split_role='DEMO',
            version=fixtures['version'], authoring_origin=f['authoring_origin'],
            provenance=f['provenance'] + ' EXCLUDED_FORMAT_FIXTURE run through demo mode.',
            source_license='Synthetic fixture; no external source; release terms not assigned.',
            reference_equation=f['reference_equation'],
            reference_solution_en='Format fixture; reference equation only.',
            status='DEMO', gold=f['gold'],
            forms={form: dict(rendering_id=r['rendering_id'], text=r['text'], creator_type='AI_SYNTHETIC_UNREVIEWED',
                              generation_or_edit_history='Authored by Sol (AI) 14 October 2026; unreviewed.',
                              switching_roles=[])
                   for form, r in f['forms'].items()},
            review={'reviewers': [], 'adjudication': None}) for f in chunk]
        ids = sorted({f[k] for f in chunk for k in ('family_id', 'source_family_id', 'template_group_id')})
        dataset = dict(schema_version='test1-1', version=fixtures['version'] + '-' + name, kind='demo',
                       borrowing_policy='EXCLUDED FORMAT FIXTURE; ' + fixtures['borrowing_policy'], families=converted)
        splits = dict(schema_version='test1-1', version=dataset['version'], kind='demo', audit=None,
                      PILOT_EVAL=[], SMOKE_TRAIN=[], RETIRED_DRAFT=[], CONFIRM_TRAIN=[], FINAL_TEST=[],
                      development_exclusion_ids=ids)
        parts.append((name, dataset, splits))
    return parts


def payload():
    import build_gpu_smoke
    buffer = io.BytesIO()

    def put(archive, name, content):
        info = zipfile.ZipInfo(name, date_time=STAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content)

    with zipfile.ZipFile(io.BytesIO(build_gpu_smoke.embedded_payload())) as old, \
            zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as new:
        for name in old.namelist():
            put(new, name, old.read(name))
        for path in sorted(HERE.glob('*.py')):
            if path.name != Path(__file__).name:
                put(new, 'secondary_analysis/' + path.name, path.read_bytes())
        put(new, 'secondary_analysis/format_fixtures.json', FIXTURES.read_bytes())
        for name, dataset, splits in demo_parts():
            put(new, f'fmt2/{name}_dataset.json', json.dumps(dataset, indent=2, ensure_ascii=False) + '\n')
            put(new, f'fmt2/{name}_splits.json', json.dumps(splits, indent=2, ensure_ascii=False) + '\n')
    return buffer.getvalue()


def build(model_id='Qwen/Qwen3-4B'):
    name = NOTEBOOKS[model_id]
    blob = payload()
    cells = []

    def add(kind, source):
        source = textwrap.dedent(source).strip() + '\n'
        cell = {'cell_type': kind, 'id': f'fmt2-cell-{len(cells):02d}', 'metadata': {}, 'source': source}
        if kind == 'code':
            cell.update(outputs=[], execution_count=None)
        cells.append(cell)

    add('markdown', f'''
        # FMT2 format-compliance test — {model_id} on T4
        **Development evidence only. Not research evidence and not pilot data.** Runs 12 AI-authored, unreviewed, permanently EXCLUDED fixture families (36 E/R/C prompts) through the unchanged Test 1 engine, frozen English instruction and inference recipe.
        It measures how often correct-looking answers break the strict FINAL format, and reports scorer v1.0.0 beside the proposed secondary `numeric_literal_v1` (decision D019).
        **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. Model download and loading take several minutes. At the end a ZIP downloads: send it to the team.
        Never tune the prompt on these outputs and then reuse them as evidence; any prompt change is a new protocol version.''')
    add('code', f'''
        import os, sys, json, base64, io, zipfile, hashlib, subprocess, traceback
        MODEL_ID = {model_id!r}
        if {model_id in GATED!r}:
            # Gated model: accept its licence on huggingface.co, then add a Colab secret named HF_TOKEN (key icon, left sidebar).
            try:
                from google.colab import userdata
                os.environ['HF_TOKEN'] = userdata.get('HF_TOKEN')
                print('HF_TOKEN read from Colab secret')
            except Exception as error:
                print('HF_TOKEN Colab secret not available (' + type(error).__name__ + '). Paste your Hugging Face read token below.')
                import getpass
                os.environ['HF_TOKEN'] = getpass.getpass('Hugging Face token: ').strip()
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'huggingface-hub==0.30.2'], check=True)
            from huggingface_hub import auth_check
            auth_check(MODEL_ID, token=os.environ['HF_TOKEN'])  # raises with a clear message if access is missing
            print('Access to', MODEL_ID, 'confirmed for this token')
        from pathlib import Path
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        PACKAGE = Path('/content/hinglish_fmt2') if Path('/content').exists() else Path.cwd() / 'hinglish_fmt2'
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
        RUNS = PACKAGE / 'runs'
        RUNS.mkdir(exist_ok=True)
        STATUS = {{'label': 'FMT2 FORMAT TEST — DEVELOPMENT EVIDENCE ONLY', 'started_at': utc(), 'stages': {{}}}}
        def note(stage, ok, error=None):
            STATUS['stages'][stage] = {{'ok': ok, 'exception_class': type(error).__name__ if error else None}}
            write(RUNS / 'fmt2_status.json', STATUS)
        PARTS = [(n, read(PACKAGE / f'fmt2/{{n}}_dataset.json'), read(PACKAGE / f'fmt2/{{n}}_splits.json'))
                 for n in ('fmt2-part-a', 'fmt2-part-b')]
        for name, dataset, splits in PARTS:
            print(name, validate(dataset, splits, 'demo')['prompts'], 'prompts validated')''')
    add('code', '''
        GPU_READY = False
        try:
            import torch
            assert torch.cuda.is_available(), 'Select a T4 GPU runtime'
            print('GPU:', torch.cuda.get_device_name(0), 'CUDA:', torch.version.cuda)
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(PACKAGE / 'requirements-colab.txt')], check=True)
            GPU_READY = True
            note('dependencies', True)
        except Exception as error:
            note('dependencies', False, error); traceback.print_exc()
        write(RUNS / 'fmt2_environment.json', environment())''')
    add('code', '''
        backend = None
        CONFIG = default_config('demo', MODEL_ID)
        if GPU_READY:
            try:
                from hinglish_pilot.hf_backend import resolve_config, HFBackend
                CONFIG = resolve_config(CONFIG)
                backend = HFBackend(CONFIG)
                write(RUNS / 'fmt2_model_load_report.json', backend.load_report)
                print('Model loaded on', backend.metadata['hardware'], 'in', round(backend.load_report['load_seconds']), 's')
                note('model_load', True)
            except Exception as error:
                note('model_load', False, error); traceback.print_exc()
        write(RUNS / 'fmt2_config.json', CONFIG)''')
    add('code', '''
        RESULTS = []
        if backend is not None:
            for name, dataset, splits in PARTS:
                try:
                    progress = lambda done, total, item: print(f'{name} {done}/{total}: {item["rendering_id"]} {item["latency_seconds"]:.1f}s', flush=True)
                    manifest = run(RUNS / name, dataset, splits, CONFIG, backend, progress=progress)
                    analyze(RUNS / name)
                    metrics, folder = analyze_secondary(RUNS / name)
                    print((folder / 'secondary_summary.md').read_text())
                    RESULTS.append((name, manifest['status']))
                    note(name, manifest['status'] == 'COMPLETE')
                except Exception as error:
                    note(name, False, error); traceback.print_exc()''')
    add('markdown', '''
        ## Download
        Run this even if something failed: it packages whatever exists. Also keep the executed notebook (File → Download → Download .ipynb).''')
    add('code', '''
        STATUS['finished_at'] = utc()
        write(RUNS / 'fmt2_status.json', STATUS)
        archive = PACKAGE / ('FMT2_format_test_results' + ('' if MODEL_ID == 'Qwen/Qwen3-4B' else '_' + MODEL_ID.split('/')[-1]) + '.zip')
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, _, _ in PARTS:
                if (RUNS / name / 'run_manifest.json').exists():
                    try:
                        z.write(export(RUNS / name), f'{name}_results.zip')
                    except Exception as error:
                        note(f'{name}_export', False, error); traceback.print_exc()
            for path in sorted(RUNS.rglob('*')):
                if path.is_file() and ('secondary_diagnostic_' in str(path) or path.name.startswith('fmt2_')):
                    z.write(path, str(path.relative_to(RUNS)))
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
