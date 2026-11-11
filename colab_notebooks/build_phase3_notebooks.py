"""Deterministic, TRAIN-only Phase-3 target notebook. No held-out file is read.

Build before the manifest: python3 -B colab_notebooks/build_phase3_notebooks.py
Then python3 -B phase3/build_target_gen_manifest.py. Both support --check.
The runtime contract is embedded; the outer manifest binds the notebook and payload
without a circular notebook/manifest hash dependency.
"""
import base64
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from t4_smoke import phase3_targets as pt
from t4_smoke import train_smoke as ts

NOTEBOOK = ROOT / 'colab_notebooks/phase3/Phase3_Targets.ipynb'
CONTRACT = ROOT / 'phase3/runtime_contract.json'


def sources():
    paths = sorted('test1_pilot/hinglish_pilot/' + p.name for p in (ROOT / 'test1_pilot/hinglish_pilot').glob('*.py'))
    paths += ['t4_smoke/phase3_targets.py', 't4_smoke/labels.py', 't4_smoke/protocol.py', 't4_smoke/train_smoke.py',
              'phase2/IMPLEMENTATION_MANIFEST.md', 'phase3/PREREGISTRATION.md', 'phase3/DESIGN.md']
    paths += list(pt.TRAIN_FILES)
    assert all('dev.v2.json' not in p and 'final_test' not in p.lower() for p in paths)
    return sorted(paths)


def contract():
    families = pt.load_train(ROOT)
    old_raw = (ROOT / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes()
    old = pt.parse_manifest(old_raw)
    for path in sources():
        if path in old['files']:
            assert pt.sha((ROOT / path).read_bytes()) == old['files'][path], path
    frozen = pt.parse_manifest((ROOT / 'phase2/ADAPTERS_FROZEN.md').read_bytes())
    return dict(schema='phase3-target-runtime-1', files={p: pt.sha((ROOT / p).read_bytes()) for p in sources()},
                backend_config=pt.backend_config(), phase2_manifest_sha256=pt.sha(old_raw),
                base_shard_source=dict(path='phase2/ADAPTERS_FROZEN.md', sha256=pt.sha((ROOT / 'phase2/ADAPTERS_FROZEN.md').read_bytes())),
                base_weight_shards_sha256=frozen['base_weight_shards_sha256'],
                word_list=list(pt.HINDI_WORDS), flag_rule=pt.FLAG_RULE, explanation_rule=pt.EXPLANATION_RULE,
                length_rule='Frozen labels.build_example; no truncation; all E/R/C <=1024; last supervised ID 151645; identical E/R/C/EE IDs',
                authorized_e_inputs=pt.e_inputs(families), evaluation_order=pt.evaluation_order(families),
                dependencies=dict(ts.PINS, torch=ts.TORCH_BUILD), model=old['model'],
                eos_stopping=old['eos_stopping'], dtype_preparation=old['dtype_preparation']['evaluation'])


def contract_bytes():
    return (json.dumps(contract(), indent=2, ensure_ascii=False) + '\n').encode()


def payload():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        def put(name, raw):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)
        for path in sources():
            put(path, (ROOT / path).read_bytes())
        put('phase3/runtime_contract.json', contract_bytes())
    return buffer.getvalue()


def cell(kind, text):
    result = dict(cell_type=kind, metadata={}, source=text.splitlines(keepends=True))
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result


def render():
    raw = payload()
    setup = '''# Unpack the frozen TRAIN-only payload and authenticate every runtime file.
import base64, hashlib, io, json, os, subprocess, sys, zipfile
from pathlib import Path
PACKAGE = Path('/content/phase3_targets') if Path('/content').exists() else Path('/tmp/phase3_targets')
PACKAGE.mkdir(parents=True, exist_ok=True)
BLOB = base64.b64decode(BLOB_TEXT)
assert hashlib.sha256(BLOB).hexdigest() == BLOB_SHA256
with zipfile.ZipFile(io.BytesIO(BLOB)) as archive:
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in archive.namelist())
    assert not any('dev.v2.json' in n.lower() or 'final_test' in n.lower() for n in archive.namelist())
    archive.extractall(PACKAGE)
sys.path.insert(0, str(PACKAGE))
from t4_smoke import phase3_targets as pt
contract, _, _ = pt.verify_contract(PACKAGE)
# torch must be the Colab build; never install or replace it.
import importlib.metadata
assert importlib.metadata.version('torch') == '2.11.0+cu130', 'Wrong Colab image: stop.'
subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet'] + [f'{k}=={v}' for k,v in contract['dependencies'].items() if k != 'torch'], check=True)
from t4_smoke import train_smoke as ts
assert not ts.stack_mismatches(ts.versions()), 'Stack mismatch: restart runtime if imports are stale.'
import torch
assert torch.cuda.is_available() and torch.cuda.device_count() == 1
assert 'T4' in torch.cuda.get_device_name(0) and torch.cuda.get_device_capability(0) == (7, 5)
from google.colab import drive
# Persistent journals and all attempts stay here across runtime disconnects.
drive.mount('/content/drive')
STORE = Path('/content/drive/MyDrive/Hinglish_Phase3')
STORE.mkdir(parents=True, exist_ok=True)
RUN = STORE / 'targets_v1'
try:
    from google.colab import userdata
    token = userdata.get('HF_TOKEN')
    if token:
        os.environ['HF_TOKEN'] = token
except Exception:
    pass  # Ungated model: anonymous download is allowed.
'''
    setup = 'BLOB_TEXT = ' + repr(base64.b64encode(raw).decode()) + '\nBLOB_SHA256 = ' + repr(pt.sha(raw)) + '\n' + setup
    execute = '''# Run generation in a subprocess, freeing GPU memory before CPU selection.
# Set True ONLY after confirming no other evaluator is active for this run.
RECOVER_STALE_LOCK = False
common = ['--root', str(PACKAGE), '--run-dir', str(RUN)]
script = str(PACKAGE / 't4_smoke/phase3_targets.py')
subprocess.run([sys.executable, script, 'generate'] + common + (['--recover-stale-lock'] if RECOVER_STALE_LOCK else []), check=True)
subprocess.run([sys.executable, script, 'select'] + common, check=True)
from google.colab import files
files.download(str(STORE / 'Phase3_Targets_results.zip'))
'''
    notebook = dict(nbformat=4, nbformat_minor=5, metadata={'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                    'colab': {'name': 'Phase3_Targets.ipynb'}, 'accelerator': 'GPU'}, cells=[
        cell('markdown', '# Phase-3 TRAIN targets\n\nUse a fresh T4 runtime. Run the two code cells in order. Resume with the same Drive folder after a disconnect. Outputs stay sealed in the ZIP; no response previews.\n\nReturn only `human_check.csv` after a bilingual human fills every flagged row with pass/fail/uncertain and a reason. Q is a provisional lower bound until review; Q <120 after review halts. Freeze is a separate CPU command after the return; this notebook never trains.\n'),
        cell('code', setup), cell('code', execute)])
    return (json.dumps(notebook, indent=1, ensure_ascii=False) + '\n').encode()


def build(check=False):
    files = {CONTRACT: contract_bytes(), NOTEBOOK: render()}
    if check:
        return all(p.is_file() and p.read_bytes() == raw for p, raw in files.items())
    for path, raw in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        print(path.relative_to(ROOT), pt.sha(raw))
    return True


if __name__ == '__main__':
    sys.exit(0 if build('--check' in sys.argv) else 1)
