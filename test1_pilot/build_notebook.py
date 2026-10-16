"""Build self-contained Colab notebook and portable ZIP from maintained sources."""
import base64
import hashlib
import io
import json
from pathlib import Path
import textwrap
import uuid
import zipfile

ROOT = Path(__file__).parent
NAME = 'Hinglish_Math_Test1_Pilot_Colab.ipynb'

def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def gold(value, unit='', aliases=None, conversions=None):
    return {'value': value, 'unit': unit, 'aliases': aliases or [], 'conversions': conversions or {},
            'unit_omission_allowed': True, 'rounding_rule': 'exact'}

def fixtures():
    rows = []
    for i, (marker, forms, answer, topic) in enumerate([
        ('DEMO-ADD', ['There are 2 red and 3 blue counters. How many counters?',
         '2 laal aur 3 neele ginte ke tukde hain. Kul kitne tukde hain?',
         '2 red aur 3 blue counters hain. How many counters in total?'], '5', 'comparison_remaining'),
        ('DEMO-HALF', ['What fraction is 1 out of 2 equal parts?',
         '2 baraabar hisson mein se 1 hissa kul ka kitna bhaag hai?',
         '2 equal parts mein se 1 part total ka kitna fraction hai?'], '1/2', 'fractions_percentages')]):
        fid = f'demo-{i+1}'
        rows.append({'family_id': fid, 'source_family_id': fid+'-source', 'template_group_id': fid+'-template',
                     'topic': topic, 'split_role': 'DEMO', 'version': 'demo-v2',
                     'authoring_origin': 'AI_SOFTWARE_FIXTURE', 'provenance': 'Synthetic software fixture; no human validation',
                     'source_license': 'CC0 synthetic fixture', 'reference_equation': '2+3=5' if i == 0 else '1/2',
                     'reference_solution_en': 'Software fixture only.', 'status': 'DEMO',
                     'gold': gold(answer, 'counters', ['counter', 'tukde', 'tukda']) if i == 0 else gold(answer),
                     'forms': {f: {'rendering_id': fid+'-'+f, 'text': marker+': '+forms[j],
                        'creator_type': 'AI_SOFTWARE_FIXTURE', 'generation_or_edit_history': 'Generated for software checks, not research.',
                        'switching_roles': ['requested_answer'] if f == 'C' else []} for j, f in enumerate(('E','R','C'))},
                     'review': {'reviewers': [], 'adjudication': None}})
    dataset = {'schema_version': 'test1-1', 'version': 'demo-v2', 'kind': 'demo',
               'borrowing_policy': 'DEMO ONLY; language judgments unvalidated', 'families': rows}
    manifest = {'schema_version': 'test1-1', 'version': 'demo-v2', 'kind': 'demo', 'audit': None,
                **{role: [] for role in ('PILOT_EVAL','SMOKE_TRAIN','RETIRED_DRAFT','CONFIRM_TRAIN','FINAL_TEST')},
                'development_exclusion_ids': [x[k] for x in rows for k in ('family_id','source_family_id','template_group_id')]}
    dump(ROOT/'fixtures/demo_dataset.json', dataset)
    dump(ROOT/'fixtures/demo_splits.json', manifest)
    smoke = {'family_id':'test1-format-smoke-v1', 'source_family_id':'test1-format-smoke-source-v1',
             'template_group_id':'test1-format-smoke-template-v1',
             'label':'DEMO — NOT RESEARCH EVIDENCE',
             'text':'A box has 7 pencils. You add 2 pencils. How many pencils are now in the box?'}
    dump(ROOT/'fixtures/format_smoke.json', smoke)
    blank = json.loads(json.dumps(rows[0]))
    blank.update(family_id='REPLACE-family', source_family_id='REPLACE-source', template_group_id='REPLACE-template',
                 split_role='PILOT_EVAL', status='DRAFT', version='draft-v1', authoring_origin='REPLACE',
                 provenance='REPLACE with source record; no names/emails', source_license='REPLACE', reference_equation='', reference_solution_en='')
    blank['gold'] = gold('0')
    for f in ('E','R','C'):
        blank['forms'][f].update(rendering_id='REPLACE-'+f, text='', creator_type='REPLACE', generation_or_edit_history='REPLACE')
    assessment = {'text_sha256':'', 'equation':'', 'answer':'', 'unit':'', 'semantic_equivalence':False,
                  'ambiguity_resolved':False, 'classification':'', 'naturalness':0, 'readability':0, 'disposition':'PENDING'}
    blank['review'] = {'reviewers': [{'reviewer_id':'', 'independent_solve_before_gold':False,
                      'forms':{f:dict(assessment) for f in ('E','R','C')}} for _ in range(2)],
                      'adjudication':{'adjudicator_id':'', 'status':'PENDING', 'unresolved_issues':None, 'reviewed_at':''}}
    dump(ROOT/'templates/pilot_dataset.template.json', {'schema_version':'test1-1', 'version':'draft-v1', 'kind':'reviewed',
         'borrowing_policy':'REPLACE with frozen policy', 'families':[blank]})
    sm = {k:smoke[k] for k in ('family_id','source_family_id','template_group_id')}
    dump(ROOT/'templates/split_manifest.template.json', {'schema_version':'test1-1','version':'draft-v1','kind':'reviewed',
         'audit':{'approved':False,'reviewer_id':'','unresolved_matches':None,'audited_at':''},
         'PILOT_EVAL':[], 'SMOKE_TRAIN':[sm], 'RETIRED_DRAFT':[], 'CONFIRM_TRAIN':[], 'FINAL_TEST':[],
         'development_exclusion_ids':list(sm.values())})


def payload():
    buf = io.BytesIO()
    paths = sorted(ROOT.glob('hinglish_pilot/*.py')) + sorted(ROOT.glob('fixtures/*.json')) + sorted(ROOT.glob('templates/*.json'))
    paths += [ROOT/'requirements-colab.txt']
    for extra in ('README.md', 'DATA_CONTRACT.md', 'VERIFICATION.md'):
        if (ROOT/extra).exists():
            paths.append(ROOT/extra)
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            info = zipfile.ZipInfo(str(path.relative_to(ROOT)), date_time=(2026,10,10,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return buf.getvalue()


def build():
    fixtures()
    embedded = payload()
    cells = []
    def add(kind, source):
        lines = source.strip().splitlines()
        source = lines[0] + ('\n' + textwrap.dedent('\n'.join(lines[1:])) if len(lines) > 1 else '')
        cell = {'cell_type':kind, 'id':f'cell-{len(cells):02d}', 'metadata':{}, 'source':source+'\n'}
        if kind == 'code':
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    md = lambda s: add('markdown', s)
    code = lambda s: add('code', s)
    md('''# Hinglish maths — Test 1 unchanged-model pilot
    This notebook evaluates paired E/R/C inputs. It performs no training and cannot establish a training effect.
    Start in **demo mode** to verify the software. Reviewed mode requires 30 accepted families (90 prompts), two independent reviews per rendering, adjudication, and a split audit. No reviewed dataset is supplied.
    This notebook embeds its helper package; no Mac paths or repository cloning are needed.
    **Before a real run:** Runtime → Change runtime type → T4 GPU. Downloads require internet; no paid APIs are called.
    GPU fit and inference speed remain unverified until you run this notebook.''')
    code('''import os, sys, json, base64, io, zipfile, hashlib, subprocess
    from pathlib import Path
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    PACKAGE = Path('/content/hinglish_test1') if Path('/content').exists() else Path.cwd() / 'hinglish_test1'
    PACKAGE.mkdir(parents=True, exist_ok=True)
    ''')
    code(f'''# Extract only the embedded, checksummed package (never an uploaded arbitrary ZIP).
    blob = base64.b64decode({base64.b64encode(embedded).decode()!r})
    assert hashlib.sha256(blob).hexdigest() == {hashlib.sha256(embedded).hexdigest()!r}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in z.namelist():
            p = Path(name)
            assert not p.is_absolute() and '..' not in p.parts
        z.extractall(PACKAGE)
    sys.path.insert(0, str(PACKAGE))
    print('Helper package ready. No model has been loaded.')''')
    md('''## Central settings — edit only this cell
    Use `MODE="demo"` and `BACKEND="fake"` first. For real reviewed data set `MODE="reviewed"`, `BACKEND="huggingface"`.
    A stable `RUN_NAME` resumes that run. To change data, prompt budget, precision or model settings, choose a new name and version; never overwrite the old run.
    Optional Drive storage survives Colab disconnects. If you keep storage under /content, download results before the runtime disappears.
    `RECOVER_STALE_LOCK` is only for a disconnected writer; never enable while another notebook is running the same directory.''')
    code('''MODE = 'demo'                     # 'demo' or 'reviewed'
    BACKEND = 'fake'                  # 'fake' or 'huggingface'
    RUN_NAME = 'demo-v2'              # e.g. pilot-reviewed-v1 (keep stable to resume)
    USE_DRIVE = False
    RECOVER_STALE_LOCK = False
    DATASET_FILENAME = 'pilot_dataset.json'
    SPLITS_FILENAME = 'split_manifest.json'
    MANUAL_OVERLAY_FILENAME = None    # optional uploaded completed manual_audit.csv
    EXECUTED_NOTEBOOK_FILENAME = None # optional uploaded downloaded .ipynb
    MODEL_ID = 'Qwen/Qwen3-4B'        # primary; second pilot backbone: 'Qwen/Qwen3-8B' (decision D030). Use a separate RUN_NAME per model.
    from hinglish_pilot.engine import default_config
    CONFIG = default_config(MODE, MODEL_ID)
    # Optional immutable model/tokenizer SHAs. None resolves once and reuses saved SHAs on resume.
    CONFIG['max_new_tokens'] = 1024
    CONFIG['context_limit'] = 2048
    CONFIG['seed'] = 11
    assert MODE in ('demo', 'reviewed') and BACKEND in ('fake', 'huggingface')
    assert MODE == 'demo' or BACKEND == 'huggingface', 'Reviewed mode requires actual model inference'
    assert RUN_NAME.startswith('demo-') if MODE == 'demo' else RUN_NAME.startswith('pilot-')
    assert all(c.isalnum() or c in '-_.' for c in RUN_NAME) and '..' not in RUN_NAME''')
    md('''## Environment and dependency setup
    Fake demo uses only Python's standard library. Real GPU runs install the pinned inference stack below. Colab supplies PyTorch; its actual build is recorded and must remain unchanged for resume.
    If you previously imported another Transformers/bitsandbytes version, restart the session after installation and rerun from the top. Do not work around install failures by changing individual versions mid-run.''')
    code('''if BACKEND == 'huggingface':
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(PACKAGE/'requirements-colab.txt')], check=True)
        import torch
        assert torch.cuda.is_available(), 'Select a T4 GPU runtime, then rerun'
        print('GPU:', torch.cuda.get_device_name(0), 'VRAM GiB:', torch.cuda.get_device_properties(0).total_memory/2**30)
    else:
        print('DEMO — NOT RESEARCH EVIDENCE. GPU dependencies skipped.')
    from hinglish_pilot.engine import environment
    print(json.dumps(environment(), indent=2))''')
    md('''## Persistent storage and inputs
    This is the only Drive mount step. Uploaded JSON must follow DATA_CONTRACT.md (included with the package).
    Fill templates after actual independent review. Do not mark fields accepted merely to make validation pass.
    Reviewed mode uploads `pilot_dataset.json` and `split_manifest.json` on the first run; saved immutable snapshots are reused on resume.
    To inspect/download the templates before annotation, use the download cell below. Stop here if you still need reviewed data.''')
    code('''if USE_DRIVE:
        from google.colab import drive
        drive.mount('/content/drive')
        STORAGE = Path('/content/drive/MyDrive/Hinglish_Test1')
    else:
        STORAGE = PACKAGE/'runs'
    RUN_DIR = STORAGE/MODE/RUN_NAME
    RUN_DIR.parent.mkdir(parents=True, exist_ok=True)
    from hinglish_pilot.engine import read, write
    if MODE == 'demo':
        DATASET = read(PACKAGE/'fixtures/demo_dataset.json')
        SPLITS = read(PACKAGE/'fixtures/demo_splits.json')
    elif (RUN_DIR/'run_manifest.json').exists():
        DATASET = read(RUN_DIR/'dataset.json')
        SPLITS = read(RUN_DIR/'split_manifest.json')
        print('Using saved input snapshots for resume:', RUN_DIR)
    else:
        from google.colab import files
        uploaded = files.upload()
        assert DATASET_FILENAME in uploaded and SPLITS_FILENAME in uploaded, 'Upload both named JSON files'
        DATASET = json.loads(uploaded[DATASET_FILENAME])
        SPLITS = json.loads(uploaded[SPLITS_FILENAME])
        del uploaded
    print('Storage:', RUN_DIR)''')
    code('''# Optional: set True to download blank templates and schema instructions, then fill them offline.
    DOWNLOAD_TEMPLATES = False
    if DOWNLOAD_TEMPLATES:
        template_zip = PACKAGE/'review_templates.zip'
        with zipfile.ZipFile(template_zip, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted((PACKAGE/'templates').glob('*.json')):
                z.write(p, p.name)
            z.write(PACKAGE/'DATA_CONTRACT.md', 'DATA_CONTRACT.md')
        from google.colab import files
        files.download(str(template_zip))''')
    md('''## Validate frozen input and exclusions
    IDs and review hashes can be checked mechanically; semantic equivalence, naturalness, hidden numerical siblings and truthful reviews require human judgment.
    The excluded format-only fixture must be listed in the reviewed split manifest. No prompt tuning using pilot accuracy.''')
    code('''from hinglish_pilot.data import validate, digest
    VALIDATION = validate(DATASET, SPLITS, MODE)
    print(json.dumps(VALIDATION, indent=2))
    SMOKE = read(PACKAGE/'fixtures/format_smoke.json')
    if MODE == 'reviewed':
        smoke_ids = {k:SMOKE[k] for k in ('family_id','source_family_id','template_group_id')}
        assert smoke_ids in SPLITS['SMOKE_TRAIN'], 'Retain format fixture identity in SMOKE_TRAIN and permanent exclusions'
        assert set(smoke_ids.values()) <= set(SPLITS['development_exclusion_ids'])
        assert all(SMOKE['text'].strip().casefold() != r['text'].strip().casefold()
                   for f in DATASET['families'] for r in f['forms'].values()), 'Smoke text cannot be a pilot question' ''')
    md('''## Software demo — independent of the research run
    This small fake backend never reads gold answers to generate its responses. It tests bookkeeping, scoring and export; token counts are fake whitespace counts. Output is permanently labeled as demo.''')
    code('''from hinglish_pilot.engine import FakeBackend, run
    from hinglish_pilot.report import analyze, export
    demo_config = default_config('demo')
    demo_config['model_revision'] = demo_config['tokenizer_revision'] = '0'*40
    DEMO_DIR = PACKAGE/'software_check'/'demo-check-v2'
    run(DEMO_DIR, read(PACKAGE/'fixtures/demo_dataset.json'), read(PACKAGE/'fixtures/demo_splits.json'), demo_config, FakeBackend())
    demo_metrics, _ = analyze(DEMO_DIR)
    print('DEMO — NOT RESEARCH EVIDENCE', demo_metrics['status'], demo_metrics['completed'], 'outputs')
    print('Software export:', export(DEMO_DIR))''')
    md('''## Load the unchanged model
    Real runs use NF4 double quantization, FP16 compute, one CUDA device, SDPA math kernel, no adapters, no CPU offload, and thinking disabled.
    The fixed greedy policy differs from Qwen's suggested sampling settings. We measure this explicitly capped, quantized configuration.
    OOM: stop, export the incomplete run, and document a new protocol/configuration with a new run name. Do not silently shorten questions or substitute models.''')
    code('''if BACKEND == 'fake':
        CONFIG['model_revision'] = CONFIG['tokenizer_revision'] = '0'*40
        backend = FakeBackend()
    else:
        from hinglish_pilot.hf_backend import resolve_config, HFBackend
        CONFIG = resolve_config(CONFIG, RUN_DIR)
        backend = HFBackend(CONFIG)
    print('Resolved revisions:', CONFIG['model_revision'], CONFIG['tokenizer_revision'])
    print(json.dumps(backend.metadata, indent=2))''')
    md('''## Format-only smoke inference
    One excluded software fixture checks formatting and records load/inference feasibility. It is not part of the pilot, human-validated data, or mathematical accuracy evidence.
    Inspect its output for technical failures only. Changing the instruction requires a new protocol version.''')
    code('''RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not (RUN_DIR/'format_smoke.json').exists():
        prepared = backend.prepare(SMOKE['text'], CONFIG)
        smoke_output = backend.generate(prepared, CONFIG, CONFIG['seed'])
        write(RUN_DIR/'format_smoke.json', dict(SMOKE, prepared=prepared, output=smoke_output,
               config_sha256=digest(CONFIG), label='DEMO — NOT RESEARCH EVIDENCE'))
    else:
        assert read(RUN_DIR/'format_smoke.json')['config_sha256'] == digest(CONFIG), 'Smoke configuration mismatch: new run required'
    if BACKEND == 'huggingface' and not (RUN_DIR/'model_load_report.json').exists():
        write(RUN_DIR/'model_load_report.json', backend.load_report)
    print(read(RUN_DIR/'format_smoke.json')['label'])
    print(read(RUN_DIR/'format_smoke.json')['output']['raw_response'])''')
    md('''## Execute or resume
    Stop the cell to interrupt cleanly. Re-run it to skip all completed generations. Incorrect, refused, invalid and truncated model responses are completed scored attempts and are never retried.
    A generation infrastructure failure receives at most one retry under unchanged settings; OOM stops immediately. A runtime killed during generation preserves an in-progress attempt without a scored response; its next attempt consumes the single retry.
    After a hard disconnect, mount the same Drive folder, select the original RUN_NAME, reload the same stack, and recover a stale lock only after checking no writer remains.''')
    code('''import time
    from hinglish_pilot.engine import recover_lock
    if RECOVER_STALE_LOCK:
        recover_lock(RUN_DIR, confirmed_no_active_writer=True)
    durations = []
    def progress(completed, total, item):
        durations.append(item['latency_seconds'])
        eta = (sum(durations)/len(durations))*(total-completed)
        print(f'{completed}/{total} completed; ETA {eta/60:.1f} min; {item["rendering_id"]}', flush=True)
    RUN_MANIFEST = run(RUN_DIR, DATASET, SPLITS, CONFIG, backend, progress=progress)
    print(RUN_MANIFEST['label'], RUN_MANIFEST['status'], 'unresolved:', RUN_MANIFEST['unresolved'])''')
    md('''## Paired analysis and manual scoring audit
    Accuracy is suppressed until all expected items resolve. Wilson intervals and 10,000 paired FAMILY bootstrap resamples are descriptive; 90 renderings are 30 independent mathematical families.
    Independently audit all 90 stored responses. Download manual_audit.csv, fill reviewer_id/manual_correct/reason/category/reviewed_at, and upload it here (set MANUAL_OVERLAY_FILENAME above). Use pseudonyms; no names/emails.
    Manual overlays create a separate versioned analysis. Automatic scores and raw generations remain preserved. Do not change scoring rules to favor a form.''')
    code('''METRICS, ANALYSIS_DIR = analyze(RUN_DIR)
    if MANUAL_OVERLAY_FILENAME:
        from google.colab import files
        uploaded = files.upload()
        assert MANUAL_OVERLAY_FILENAME in uploaded
        OVERLAY = PACKAGE/'manual_overlay_uploaded.csv'
        OVERLAY.write_bytes(uploaded[MANUAL_OVERLAY_FILENAME])
        del uploaded
        METRICS, ANALYSIS_DIR = analyze(RUN_DIR, OVERLAY)
    print((ANALYSIS_DIR/'summary.md').read_text())
    print(json.dumps(METRICS['failure_diagnostics'], indent=2))''')
    code('''DOWNLOAD_MANUAL_AUDIT = False
    if DOWNLOAD_MANUAL_AUDIT:
        from google.colab import files
        files.download(str(RUN_DIR/'manual_audit.csv'))''')
    md('''## Plot (optional)
    Demo charts are software fixtures. Reviewed-pilot charts show family sample size and Wilson intervals; topic results remain small-sample descriptive.''')
    code('''if BACKEND == 'huggingface':
        from hinglish_pilot.report import plot
        fig = plot(ANALYSIS_DIR)
        if fig is not None:
            display(fig)
    else:
        print('Demo plot skipped; JSON and Markdown reports are available.')''')
    md('''## Export ONE results ZIP
    The export includes raw attempts, immutable input snapshots, model settings, actual package versions, scoring tables, resource summaries, manual-audit material and SHA256 checksums.
    Credentials and email-like text cause export to stop. Review free text before sharing; pseudonymous IDs are required.
    To include an executed notebook, first use Colab File → Download → Download .ipynb, then set EXECUTED_NOTEBOOK_FILENAME and upload it here. Otherwise return that downloaded notebook separately.''')
    code('''notebook_path = None
    if EXECUTED_NOTEBOOK_FILENAME:
        from google.colab import files
        uploaded = files.upload()
        assert EXECUTED_NOTEBOOK_FILENAME in uploaded
        notebook_path = PACKAGE/'executed_notebook.ipynb'
        notebook_path.write_bytes(uploaded[EXECUTED_NOTEBOOK_FILENAME])
        del uploaded
    RESULTS_ZIP = export(RUN_DIR, notebook=notebook_path)
    print('Return this archive:', RESULTS_ZIP)
    try:
        from google.colab import files
        files.download(str(RESULTS_ZIP))
    except ImportError:
        print('Local execution: archive saved on disk.')''')
    md('''## Return for research analysis
    Send the `*_results.zip` from the reviewed run and the executed `.ipynb` (inside the ZIP or separately). Send incomplete runs too when troubleshooting; they will not be interpreted as complete research results.
    The next research decision will use the review trail, paired differences, invalid outputs, difficulty, and actual GPU cost. No fine-tuning benefit or publication acceptance is assumed.''')
    notebook = {'nbformat':4, 'nbformat_minor':5, 'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
               'language_info':{'name':'python','version':'3.11'}, 'colab':{'name':NAME}, 'accelerator':'GPU'}, 'cells':cells}
    dump(ROOT/NAME, notebook)
    with zipfile.ZipFile(ROOT/'Hinglish_Test1_Portable.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and p.suffix not in ('.zip','.pyc') and not any(x in p.parts for x in ('__pycache__','local_demo','runs','.venv','archive')):
                z.write(p, str(p.relative_to(ROOT)))
    print('Built', ROOT/NAME)

if __name__ == '__main__':
    build()
