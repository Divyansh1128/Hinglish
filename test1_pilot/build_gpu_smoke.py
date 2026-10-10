"""Create a separate real-model smoke notebook; original pilot stays unchanged."""
import base64
import hashlib
import io
import json
from pathlib import Path
import textwrap
import zipfile
import build_notebook

ROOT=Path(__file__).parent
NAME='Hinglish_Math_Qwen_GPU_Smoke_Colab.ipynb'

def embedded_payload():
    # Build the variant from maintained original sources, with a recorded pin update.
    buffer=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(build_notebook.payload())) as old, zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as new:
        for name in old.namelist():
            content=old.read(name)
            if name in ('hinglish_pilot/hf_backend.py','requirements-colab.txt'):
                content=content.replace(b'0.45.5',b'0.50.2')
            info=zipfile.ZipInfo(name,date_time=(2026,10,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            new.writestr(info,content)
        info=zipfile.ZipInfo('GPU_SMOKE_NOTES.md',date_time=(2026,10,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        new.writestr(info,'Real-model technical demo only. Variant pins bitsandbytes 0.50.2 for CUDA 13 support. Main pilot now uses the same tested bitsandbytes pin; version-1 artifacts remain archived. No full study or training performed. Documentation: https://huggingface.co/docs/bitsandbytes/v0.50.2/en/installation\n')
    return buffer.getvalue()

def build():
    blob=embedded_payload();cells=[]
    def add(kind,source):
        lines=source.strip().splitlines()
        source=lines[0]+('\n'+textwrap.dedent('\n'.join(lines[1:])) if len(lines)>1 else '')+'\n'
        c={'cell_type':kind,'id':f'gpu-cell-{len(cells):02d}','metadata':{},'source':source}
        if kind=='code':c.update(outputs=[],execution_count=None)
        cells.append(c)
    def md(x):add('markdown',x)
    def code(x):add('code',x)
    md('''# Qwen3-4B — GPU loading and inference smoke check
    **This is a technical demo, not research evidence.** It runs one format-only question and six synthetic E/R/C inputs using the actual unchanged model.
    No reviewed dataset upload is needed. No training is performed. The purpose is to measure load success, generation behavior, latency and memory before the full pilot.
    **Start a fresh Colab session and select Runtime → Change runtime type → T4 GPU**, then run all cells. The model download requires internet and may take several minutes.
    This variant uses bitsandbytes 0.50.2 because your previous runtime recorded CUDA 13.0. Its [official installation table](https://huggingface.co/docs/bitsandbytes/v0.50.2/en/installation) lists CUDA 13 builds and T4-compatible SM75 support. The returned version-1 run verified short-input T4 inference; this version changes fixture metadata, not the hardware recipe.
    Keep the original demo and reviewed-pilot notebook for their respective purposes. This notebook has a separate package/storage path and run name.''')
    code(f'''import os, sys, json, base64, io, zipfile, hashlib, subprocess
    from pathlib import Path
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    PACKAGE = Path('/content/hinglish_qwen_gpu_smoke') if Path('/content').exists() else Path.cwd()/'hinglish_qwen_gpu_smoke'
    PACKAGE.mkdir(parents=True,exist_ok=True)
    blob=base64.b64decode({base64.b64encode(blob).decode()!r})
    assert hashlib.sha256(blob).hexdigest()=={hashlib.sha256(blob).hexdigest()!r}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
        z.extractall(PACKAGE)
    sys.path.insert(0,str(PACKAGE))
    from hinglish_pilot.engine import default_config, environment, read, write, run, utc, recover_lock
    from hinglish_pilot.data import validate,digest
    from hinglish_pilot.report import analyze, export
    print('Self-contained package ready. DEMO — NOT RESEARCH EVIDENCE')''')
    md('''## Settings
    Defaults are ready for this smoke check. USE_DRIVE is optional. Keep a stable RUN_NAME to resume the same settings; do not reuse the fake demo's directory.
    If an old process died, enable RECOVER_STALE_LOCK only after checking no writer remains. A hard disconnect without Drive persistence loses local outputs.''')
    code('''RUN_NAME='demo-qwen-gpu-v2'
    USE_DRIVE=False
    RECOVER_STALE_LOCK=False
    CONFIG=default_config('demo')
    STATE={'label':'DEMO — NOT RESEARCH EVIDENCE','purpose':'Qwen GPU feasibility smoke',
           'started_at':utc(),'stage':'setup','status':'INCOMPLETE',
           'dependency_change':'bitsandbytes 0.45.5 → 0.50.2; separate smoke variant',
           'model_loaded':False,'real_generations_completed':0}
    assert RUN_NAME.startswith('demo-') and '..' not in RUN_NAME
    assert all(c.isalnum() or c in '-_.' for c in RUN_NAME)
    if USE_DRIVE:
        from google.colab import drive
        drive.mount('/content/drive')
        STORAGE=Path('/content/drive/MyDrive/Hinglish_Qwen_GPU_Smoke')
    else:
        STORAGE=PACKAGE/'runs'
    RUN_DIR=STORAGE/RUN_NAME
    RUN_DIR.mkdir(parents=True,exist_ok=True)
    def fail(stage,error):
        STATE.update(stage=stage,status='FAILED',exception_class=type(error).__name__)
        write(RUN_DIR/'smoke_status.json',STATE)
        print('Stopped at',stage,'with',type(error).__name__,'. Run the final export cell and return its ZIP.')
    print('Results directory:',RUN_DIR)''')
    md('''## GPU and candidate dependencies
    No CPU fallback or model substitution is performed. PyTorch remains the Colab-provided build. All actual package versions are saved.
    If a cell reports failure, run the last export cell anyway. It will package diagnostics when inference could not begin.''')
    code('''GPU_READY=False
    try:
        import torch
        assert torch.cuda.is_available(), 'Select a T4 GPU runtime'
        assert torch.cuda.device_count()==1, 'Need one GPU'
        print('GPU:',torch.cuda.get_device_name(0),'CUDA:',torch.version.cuda)
        subprocess.run([sys.executable,'-m','pip','install','-q','-r',str(PACKAGE/'requirements-colab.txt')],check=True)
        GPU_READY=True
        STATE.update(stage='dependencies_ready',gpu=torch.cuda.get_device_name(0),cuda=torch.version.cuda)
    except Exception as e:
        fail('gpu_or_dependencies',e)
    write(RUN_DIR/'smoke_environment.json',environment())
    write(RUN_DIR/'smoke_status.json',STATE)
    print(json.dumps(environment(),indent=2))''')
    md('''## Included software inputs
    These two synthetic families are not human validated. Every file and score stays labeled DEMO. Their answers do not establish Hinglish robustness.
    The model receives only the question and fixed instruction; it does not receive the gold answer.''')
    code('''DATASET=read(PACKAGE/'fixtures/demo_dataset.json')
    SPLITS=read(PACKAGE/'fixtures/demo_splits.json')
    SMOKE=read(PACKAGE/'fixtures/format_smoke.json')
    print(json.dumps(validate(DATASET,SPLITS,'demo'),indent=2))''')
    md('''## Load the actual model
    Qwen3-4B, pinned immutable revisions, NF4 double quantization, FP16, one GPU, SDPA math kernel, thinking disabled and fixed greedy decoding. The output cap remains 1,024 tokens.
    If loading fails, the diagnostic ZIP records the stage, exception class, actual environment and candidate configuration. It will not pretend the model loaded.''')
    code('''backend=None
    if GPU_READY:
        try:
            from hinglish_pilot.hf_backend import resolve_config,HFBackend
            CONFIG=resolve_config(CONFIG,RUN_DIR)
            backend=HFBackend(CONFIG)
            STATE.update(stage='model_loaded',model_loaded=True,backend=backend.metadata)
            write(RUN_DIR/'model_load_report.json',backend.load_report)
            print('Model loaded:',backend.metadata['hardware'])
            print('Load seconds:',backend.load_report['load_seconds'])
        except Exception as e:
            fail('model_loading',e)
    write(RUN_DIR/'smoke_config.json',CONFIG)
    write(RUN_DIR/'smoke_status.json',STATE)''')
    md('''## Format-only question
    This separate fixture is an engineering check. Inspect whether the response ends with one FINAL line. Do not tune the prompt using the six demo answers.''')
    code('''FORMAT_READY=False
    if backend is not None:
        try:
            if not (RUN_DIR/'format_smoke.json').exists():
                prepared=backend.prepare(SMOKE['text'],CONFIG)
                output=backend.generate(prepared,CONFIG,CONFIG['seed'])
                write(RUN_DIR/'format_smoke.json',dict(SMOKE,prepared=prepared,output=output,config_sha256=digest(CONFIG)))
            assert read(RUN_DIR/'format_smoke.json')['config_sha256']==digest(CONFIG), 'Format check settings changed: choose a new run name'
            print(read(RUN_DIR/'format_smoke.json')['output']['raw_response'])
            FORMAT_READY=True
        except Exception as e:
            fail('format_smoke',e)''')
    md('''## Six real-model demo outputs
    This uses the same journal/resume/scorer/export engine as Test 1. Each input has a fresh context. Successful outputs are never retried because they are wrong or malformed.
    One infrastructure retry is allowed under unchanged settings; OOM stops. Complete or incomplete, return the final ZIP.''')
    code('''if FORMAT_READY:
        try:
            if RECOVER_STALE_LOCK:
                recover_lock(RUN_DIR,confirmed_no_active_writer=True)
            def progress(done,total,item):
                print(f'{done}/{total}: {item["rendering_id"]} — {item["latency_seconds"]:.2f}s',flush=True)
            manifest=run(RUN_DIR,DATASET,SPLITS,CONFIG,backend,progress=progress)
            STATE.update(stage='inference',status=manifest['status'],real_generations_completed=manifest['completed'])
            metrics,_=analyze(RUN_DIR)
            print((RUN_DIR/'summary.md').read_text())
        except Exception as e:
            fail('inference',e)
    STATE['finished_at']=utc()
    write(RUN_DIR/'smoke_status.json',STATE)
    print(json.dumps(STATE,indent=2))''')
    md('''## Download the results or diagnostic ZIP
    Even when loading failed, run this cell. Keep the executed notebook too: File → Download → Download .ipynb.
    Send the ZIP and notebook to the research assistant. No reviewed dataset upload is needed for this step.''')
    code('''if (RUN_DIR/'run_manifest.json').exists():
        RESULTS_ZIP=export(RUN_DIR)
        # Add variant-level diagnostics with checksums while preserving the regular export.
        extra=['smoke_status.json','smoke_environment.json','smoke_config.json']
        temp=RESULTS_ZIP.with_suffix('.zip.tmp')
        with zipfile.ZipFile(RESULTS_ZIP) as old,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
            checksum=old.read('checksums.sha256').decode()
            for name in old.namelist():
                if name!='checksums.sha256':z.writestr(name,old.read(name))
            for name in extra:
                if (RUN_DIR/name).exists():
                    content=(RUN_DIR/name).read_bytes()
                    z.writestr(name,content)
                    checksum+=hashlib.sha256(content).hexdigest()+'  '+name+'\\n'
            z.writestr('checksums.sha256',checksum)
        temp.replace(RESULTS_ZIP)
    else:
        RESULTS_ZIP=RUN_DIR.parent/(RUN_NAME+'_diagnostics.zip')
        names=['smoke_status.json','smoke_environment.json','smoke_config.json','model_load_report.json','format_smoke.json']
        with zipfile.ZipFile(RESULTS_ZIP,'w',zipfile.ZIP_DEFLATED) as z:
            checks=''
            for name in names:
                if (RUN_DIR/name).exists():
                    content=(RUN_DIR/name).read_bytes();z.writestr(name,content)
                    checks+=hashlib.sha256(content).hexdigest()+'  '+name+'\\n'
            z.writestr('checksums.sha256',checks)
    print('Return:',RESULTS_ZIP)
    try:
        from google.colab import files
        files.download(str(RESULTS_ZIP))
    except ImportError:
        print('Local check: ZIP saved on disk.')''')
    nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python'},'colab':{'name':NAME},'accelerator':'GPU'},'cells':cells}
    (ROOT/NAME).write_text(json.dumps(nb,indent=2,ensure_ascii=False)+'\n')
    print(ROOT/NAME)

if __name__=='__main__':build()
