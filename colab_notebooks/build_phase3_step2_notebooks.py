"""Add Phase-3 training/final launch builders without editing the frozen step-1 builder.

python -B colab_notebooks/build_phase3_step2_notebooks.py
python -B colab_notebooks/build_phase3_step2_notebooks.py --check
After adapter freeze ONLY:
python -B colab_notebooks/build_phase3_step2_notebooks.py --finalize --train-root TRAIN_ROOT

The final notebook is a fixed launcher. Its data-bearing payload and launch manifest
are built after adapter freeze, breaking the notebook/implementation/adapter hash cycle.
"""
import argparse
import base64
import io
import json
import sys
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from colab_notebooks import build_phase3_notebooks as step1
from t4_smoke import phase3_contract as c, train_smoke as ts

NAMES = dict(train='Phase3_Train.ipynb', final_test='Phase3_FinalTest.ipynb')
OUT = ROOT / 'colab_notebooks/phase3'
RUNTIME = 'phase3/step2_runtime_contract.json'


def sources():
    paths = ['t4_smoke/' + name for name in ('train_smoke.py', 'train_phase2.py', 'phase2_eval.py', 'labels.py', 'protocol.py',
             'phase3_targets.py', 'phase3_contract.py', 'train_phase3.py', 'phase3_eval.py', 'phase3_registry.py')]
    for directory in ('test1_pilot/hinglish_pilot', 'secondary_analysis', 'phase2_analysis', 'phase3_analysis'):
        paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT / directory).glob('*.py'))]
    paths += ['paper_analysis/safezip.py', 'phase2/IMPLEMENTATION_MANIFEST.md', 'phase2/ADAPTERS_FROZEN.md',
              'phase2/train_A.v2.json', 'phase2/train_B.v2.json', 'phase2/dev.v2.json',
              'phase3/PREREGISTRATION.md', 'phase3/DESIGN.md', 'phase3/TARGETS_FROZEN.md', 'phase3/targets.v1.json',
              'phase3/runtime_contract.json', 'phase3/TARGET_GEN_MANIFEST.md', 'phase3/EXPOSURE_ORDER.json',
              'results/phase3/targets/Phase3_Targets_frozen.zip', 'results/phase3/targets/Phase3_Targets_results.zip',
              'results/phase2/baseline_dev/Phase2_Baseline_DEV_results.zip', 'phase3/AUDIT_RUBRIC.md',
              'results/pilot_b/audit/AUDIT_INSTRUCTIONS.md', 'research/pre_pilot_endpoint_spec_v1.md']
    assert not any('final_test' in p.lower() for p in paths)
    return sorted(set(paths))


def contract_bytes():
    c.load_targets(ROOT)
    old = c.block((ROOT / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
    return (json.dumps(dict(schema='phase3-step2-runtime-1', files={p: c.file_sha(ROOT / p) for p in sources()},
              targets_sha256=c.TARGET_SHA, dev_config_sha256=c.DEV_CONFIG_SHA, final_config_sha256=c.FINAL_CONFIG_SHA,
              recipe=__import__('t4_smoke.train_phase3', fromlist=['RECIPE']).RECIPE,
              model=old['model'], dependencies=dict(ts.PINS, torch=ts.TORCH_BUILD)), indent=2) + '\n').encode()


def pack(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, raw)
    return buffer.getvalue()


def payload(kind, *, root=ROOT, train_root=None):
    files = {p: (Path(root) / p).read_bytes() for p in sources()}
    files[RUNTIME] = contract_bytes()
    if kind == 'final_test':
        from t4_smoke import phase3_eval as ev
        c.require(train_root is not None, 'Final payload requires adapter freeze and training-root verification')
        ev.gate(root, train_root)  # must precede any test-byte packaging
        for path in ('phase2/final_test.v3.json', ev.FINAL_ARCHIVE, ev.FROZEN_PATH, 'phase3/IMPLEMENTATION_MANIFEST.md'):
            files[path] = (Path(root) / path).read_bytes()
    else:
        assert kind == 'train' and not any('final_test' in n.lower() for n in files)
    return pack(files)


def setup_common():
    return '''import base64, hashlib, io, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
from google.colab import drive, files
import importlib.metadata
drive.mount('/content/drive')
STORE = Path('/content/drive/MyDrive/Hinglish_Phase3')
STORE.mkdir(parents=True, exist_ok=True)
PACKAGE = Path('/content/phase3_step2')
PACKAGE.mkdir(parents=True, exist_ok=True)
TRAIN_ROOT = STORE / 'train'
'''


def unpack():
    return '''with zipfile.ZipFile(io.BytesIO(BLOB)) as archive:
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in archive.namelist())
    archive.extractall(PACKAGE)
sys.path.insert(0, str(PACKAGE))
os.chdir(PACKAGE)
contract = json.loads((PACKAGE / 'phase3/step2_runtime_contract.json').read_bytes())
for path, checksum in contract['files'].items():
    assert hashlib.sha256((PACKAGE / path).read_bytes()).hexdigest() == checksum, path
subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet'] + [f'{k}=={v}' for k,v in contract['dependencies'].items() if k != 'torch'], check=True)
from t4_smoke import train_smoke as ts, train_phase3 as train, phase3_eval as ev, phase3_contract as c
assert not ts.stack_mismatches(ts.versions()), 'Stack mismatch; restart runtime if imports are stale.'
import torch
assert torch.cuda.is_available() and torch.cuda.device_count() == 1
assert 'T4' in torch.cuda.get_device_name(0) and torch.cuda.get_device_capability(0) == (7, 5)
# Copy the authenticated companion even when a stale local copy exists.
if (STORE / 'IMPLEMENTATION_MANIFEST.md').is_file():
    shutil.copyfile(STORE / 'IMPLEMENTATION_MANIFEST.md', PACKAGE / 'phase3/IMPLEMENTATION_MANIFEST.md')
c.verify_implementation(PACKAGE)
try:
    from google.colab import userdata
    token = userdata.get('HF_TOKEN')
    if token:
        os.environ['HF_TOKEN'] = token
except Exception:
    pass
'''


def render_train():
    raw = payload('train')
    setup = setup_common() + '''# Paste the SHA-256 printed by build_implementation_manifest.py from the archived release.
# It cannot be embedded in a notebook which that same manifest hashes.
EXPECTED_IMPLEMENTATION_SHA256 = ''
companion = STORE / 'IMPLEMENTATION_MANIFEST.md'
remedy = ('Copy the matching phase3/IMPLEMENTATION_MANIFEST.md to '
          'MyDrive/Hinglish_Phase3/IMPLEMENTATION_MANIFEST.md and paste its archived '
          'build SHA-256 into EXPECTED_IMPLEMENTATION_SHA256, then rerun this cell.')
assert companion.is_file(), 'Missing implementation manifest. ' + remedy
assert len(EXPECTED_IMPLEMENTATION_SHA256) == 64, 'Expected manifest SHA-256 is unset. ' + remedy
assert hashlib.sha256(companion.read_bytes()).hexdigest() == EXPECTED_IMPLEMENTATION_SHA256, 'Wrong implementation manifest. ' + remedy
assert importlib.metadata.version('torch') == '2.11.0+cu130', 'Wrong Colab image: stop; never install torch.'
''' + 'BLOB = base64.b64decode(' + repr(base64.b64encode(raw).decode()) + ')\n'
    setup += 'assert hashlib.sha256(BLOB).hexdigest() == ' + repr(c.sha(raw)) + '\n'
    setup += "with zipfile.ZipFile(io.BytesIO(BLOB)) as z:\n    assert not any('final_test' in n.lower() for n in z.namelist())\n"
    setup += unpack()
    execute = '''# Operator settings must match plan: slot 11 then 22 then 33, EC -> ER -> EE.
RECOVER_STALE_WRITER = False  # True only after confirming no other trainer session is active.
RECOVER_STALE_LOCK = False    # True only after confirming no other evaluator is active.
print('Training writer lock:', train.p2.read_writer_lock(TRAIN_ROOT))
if RECOVER_STALE_WRITER:
    train.recover_stale_writer(TRAIN_ROOT, confirmed_no_other_session=True)
pending = train.p2.next_run(train.p2.plan(train.p2.read_log(TRAIN_ROOT / train.p2.ATTEMPT_LOG)))
print('Pending plan (arm/seed/attempt):', pending)
from t4_smoke import phase3_registry as registry
try:
    with registry.locked(TRAIN_ROOT):
        print('Evaluation registry lock: available')
except train.p2.Refused:
    print('Evaluation registry lock: held or unsupported')
    raise
print('Evaluation engine locks:', [str(p) for p in STORE.rglob('RUNNING.lock')])
ARM = pending['arm'] if pending['kind'] == 'train' else None  # Operator may override; trainer asserts the plan.
SEED = pending['seed'] if pending['kind'] == 'train' else None
common = ['--root', str(PACKAGE), '--train-root', str(TRAIN_ROOT)]
def evaluate(folder, args):
    return subprocess.run([sys.executable, '-m', 't4_smoke.phase3_eval'] + args).returncode
try:
    ev.run_dev_sanity(TRAIN_ROOT, PACKAGE, recover=RECOVER_STALE_LOCK, evaluate=evaluate)
    if pending['kind'] == 'complete':
        print('Training plan and DEV sanity complete; proceed to the adapter freeze.')
    else:
        result = subprocess.run([sys.executable, '-m', 't4_smoke.train_phase3', 'train'] + common + ['--arm', ARM, '--seed', str(SEED)])
        if result.returncode == 0:
            ev.run_dev_sanity(TRAIN_ROOT, PACKAGE, recover=RECOVER_STALE_LOCK, evaluate=evaluate)
        else:
            print('Training exit code:', result.returncode, '; inspect attempt plan/status. No automatic retry.')
finally:
    archive = shutil.make_archive(str(STORE / f'Phase3_Train_{ARM}-s{SEED}'), 'zip', TRAIN_ROOT)
    files.download(archive)
'''
    return notebook('train', 'One run, then DEV sanity. Fresh T4 runtime. Copy the frozen `phase3/IMPLEMENTATION_MANIFEST.md` to '
                    '`MyDrive/Hinglish_Phase3/IMPLEMENTATION_MANIFEST.md` before launch. All attempts and recoveries persist. '
                    'Set ARM/SEED to the plan; never resume partial training. DEV cannot authorize a retry.', setup, execute)


def render_final():
    setup = setup_common() + '''# Build FINAL_EVAL_PAYLOAD.zip locally AFTER phase3/ADAPTERS_FROZEN.md exists and verifies.
# Copy it and FINAL_EVAL_MANIFEST.md into STORE. This fixed launcher is frozen before training.
launch = (STORE / 'FINAL_EVAL_MANIFEST.md').read_text()
manifest = json.loads(launch.split('```json\\n', 1)[1].split('\\n```', 1)[0])
BLOB = (STORE / 'FINAL_EVAL_PAYLOAD.zip').read_bytes()
assert hashlib.sha256(BLOB).hexdigest() == manifest['payload_sha256']
with zipfile.ZipFile(io.BytesIO(BLOB)) as z:
    assert 'phase2/final_test.v3.json' in z.namelist()
    assert 'results/phase2/final_test/Phase2_FinalTest_results.zip' in z.namelist()
    assert hashlib.sha256(z.read('phase3/ADAPTERS_FROZEN.md')).hexdigest() == manifest['adapters_frozen_sha256']
    assert hashlib.sha256(z.read('phase3/IMPLEMENTATION_MANIFEST.md')).hexdigest() == manifest['implementation_manifest_sha256']
''' + "assert importlib.metadata.version('torch') == '2.11.0+cu130', 'Wrong Colab image: stop; never install torch.'\n" + unpack() + '''assert c.file_sha(PACKAGE / 'phase3/IMPLEMENTATION_MANIFEST.md') == manifest['implementation_manifest_sha256']
frozen = ev.gate(PACKAGE, TRAIN_ROOT)
ev.load_reused_baseline(PACKAGE, frozen)  # Original provenance and inference equivalence, before new GPU generation.
'''
    execute = '''RECOVER_STALE_LOCK = False  # Confirm no other evaluator is active before setting True.
EVALUATIONS = STORE / 'final_test'
EVALUATIONS.mkdir(exist_ok=True)
try:
    for adapter in frozen['adapters']:
        folder = train.attempt_dir(TRAIN_ROOT, adapter['arm'], adapter['seed'], adapter['attempt'])
        run_dir = EVALUATIONS / train.run_name(adapter['arm'], adapter['seed'])
        args = ['evaluate', '--root', str(PACKAGE), '--train-root', str(TRAIN_ROOT), '--split', 'final_test',
                '--run-dir', str(run_dir), '--adapter-dir', str(folder / 'final_adapter'),
                '--adapter-record', str(folder / 'final_adapter.json')]
        if RECOVER_STALE_LOCK:
            args += ['--recover-stale-lock']
        subprocess.run([sys.executable, '-m', 't4_smoke.phase3_eval'] + args, check=True)
finally:
    archive = shutil.make_archive(str(STORE / 'Phase3_FinalTest_bundle'), 'zip', STORE, 'final_test')
    # Merge this bundle into the same study root as the downloaded training tree.
    with zipfile.ZipFile(archive, 'a', zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(TRAIN_ROOT / 'EVALUATION_REGISTRY.jsonl', 'train/EVALUATION_REGISTRY.jsonl')
    files.download(archive)
# No response/accuracy previews. Unseal only with the frozen analysis wrapper after all required exports validate.
'''
    return notebook('final_test', 'Sealed adapter-only FINAL_TEST evaluation: nine adapters, 2,700 generations at S=3; unchanged baseline reused. '
                    'Before launch run the sibling builder with `--finalize --train-root TRAIN_ROOT` after adapter freeze. '
                    'Copy its FINAL_EVAL_PAYLOAD.zip and FINAL_EVAL_MANIFEST.md to Hinglish_Phase3 on Drive. '
                    'The payload cannot be built before a matching adapter freeze; no FINAL_TEST bytes are embedded during implementation. '
                    'With registered attrition S=1/2 this runs 3S adapters for descriptive reporting only.', setup, execute)


def notebook(kind, description, setup, execute):
    doc = dict(nbformat=4, nbformat_minor=5, metadata={'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
               'colab': {'name': NAMES[kind]}, 'accelerator': 'GPU'},
               cells=[step1.cell('markdown', '# Phase-3 ' + kind + '\n\n' + description + '\n'),
                      step1.cell('code', setup), step1.cell('code', execute)])
    return (json.dumps(doc, indent=1, ensure_ascii=False) + '\n').encode()


def build(check=False):
    generated = {ROOT / RUNTIME: contract_bytes(), OUT / NAMES['train']: render_train(), OUT / NAMES['final_test']: render_final()}
    c.require(step1.build(check=True), 'Frozen target notebook/contract no longer verifies')
    if check:
        return all(path.is_file() and path.read_bytes() == raw for path, raw in generated.items())
    for path, raw in generated.items():
        path.write_bytes(raw)
        print(path.relative_to(ROOT), c.sha(raw))
    return True


def finalize(train_root):
    from t4_smoke import phase3_eval as ev
    c.verify_implementation(ROOT, full=True)
    ev.gate(ROOT, train_root)
    raw = payload('final_test', train_root=train_root)
    path = ROOT / 'phase3/FINAL_EVAL_PAYLOAD.zip'
    c.require(not path.exists(), 'Final payload already exists; preserve launch evidence')
    path.write_bytes(raw)
    binding = dict(payload_sha256=c.sha(raw), adapters_frozen_sha256=c.file_sha(ROOT / ev.FROZEN_PATH),
                   implementation_manifest_sha256=c.file_sha(ROOT / 'phase3/IMPLEMENTATION_MANIFEST.md'),
                   notebook_sha256=c.file_sha(OUT / NAMES['final_test']))
    (ROOT / 'phase3/FINAL_EVAL_MANIFEST.md').write_text('# Phase-3 final-evaluation launch freeze\n\n```json\n' + json.dumps(binding, indent=2) + '\n```\n')
    print(path, c.sha(raw))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--finalize', action='store_true')
    parser.add_argument('--train-root', type=Path)
    args = parser.parse_args()
    if args.finalize:
        c.require(args.train_root is not None, '--train-root required')
        finalize(args.train_root)
    else:
        raise SystemExit(0 if build(args.check) else 1)
