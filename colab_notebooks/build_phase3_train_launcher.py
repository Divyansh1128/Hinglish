"""Build Phase3_Train_Launcher.ipynb (D057).

The frozen Phase3_Train.ipynb embeds a 2.8 MB one-line package that freezes the
Colab editor. The launcher runs that notebook's code cells, byte-verified, without
rendering them. Only the operator line the frozen notebook asks to be edited
(EXPECTED_IMPLEMENTATION_SHA256) and, when instructed, the two RECOVER flags are
substituted, each asserted to occur exactly once.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SHA = '5d0c20e318c89a44871c20b2220e044cb6fdbb1ef6b82d8731dff244a13afec4'
IMPL_SHA = '824671917d4782a01f458aed001c56671869eae6b494bf837568d2f83c7184df'

md = f"""# Phase-3 train launcher

Runs the frozen `Phase3_Train.ipynb` (SHA-256 `{FROZEN_SHA[:12]}…`) without opening it, because its embedded package freezes the Colab editor (D057).

Before launch, put both files in `MyDrive/Hinglish_Phase3/` (upload through drive.google.com; **do not open** the train notebook):
- `Phase3_Train.ipynb` (unchanged)
- `IMPLEMENTATION_MANIFEST.md`

Runtime: T4 GPU, fresh. Run cell 1, then cell 2. One training run per session."""

cell1 = f"""import hashlib, json
from pathlib import Path
from google.colab import drive
drive.mount('/content/drive')
_STORE = Path('/content/drive/MyDrive/Hinglish_Phase3')
_NB = _STORE / 'Phase3_Train.ipynb'
assert _NB.is_file(), f'Upload the unchanged Phase3_Train.ipynb to {{_NB}} (do not open it).'
_raw = _NB.read_bytes()
assert hashlib.sha256(_raw).hexdigest() == '{FROZEN_SHA}', 'Phase3_Train.ipynb on Drive is not the frozen file; re-upload it unchanged.'
_manifest = _STORE / 'IMPLEMENTATION_MANIFEST.md'
assert _manifest.is_file() and '{FROZEN_SHA}' in _manifest.read_text(), 'Manifest missing or does not list the frozen train notebook.'
_cells = [''.join(c['source']) for c in json.loads(_raw)['cells'] if c['cell_type'] == 'code']
assert len(_cells) == 2, len(_cells)

def _sub(src, old, new):
    assert src.count(old) == 1, old
    return src.replace(old, new)

_src = _sub(_cells[0], "EXPECTED_IMPLEMENTATION_SHA256 = ''\\n",
            "EXPECTED_IMPLEMENTATION_SHA256 = '{IMPL_SHA}'\\n")
print('Frozen notebook verified; running its setup cell (Drive, package checks, pip, GPU checks)...')
get_ipython().run_cell(_src).raise_error()
print('Setup cell finished.')"""

cell2 = """# Leave both False unless Claude tells you otherwise after an interrupted run.
RECOVER_STALE_WRITER_OVERRIDE = False
RECOVER_STALE_LOCK_OVERRIDE = False
_src2 = _cells[1]
if RECOVER_STALE_WRITER_OVERRIDE:
    _src2 = _sub(_src2, 'RECOVER_STALE_WRITER = False', 'RECOVER_STALE_WRITER = True')
if RECOVER_STALE_LOCK_OVERRIDE:
    _src2 = _sub(_src2, 'RECOVER_STALE_LOCK = False', 'RECOVER_STALE_LOCK = True')
get_ipython().run_cell(_src2).raise_error()"""

def code(s):
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
            'source': s.splitlines(keepends=True)}

nb = {'nbformat': 4, 'nbformat_minor': 0,
      'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                   'colab': {'name': 'Phase3_Train_Launcher.ipynb'}, 'accelerator': 'GPU'},
      'cells': [{'cell_type': 'markdown', 'metadata': {}, 'source': md.splitlines(keepends=True)},
                code(cell1), code(cell2)]}
out = ROOT / 'colab_notebooks/phase3/Phase3_Train_Launcher.ipynb'
out.write_text(json.dumps(nb, indent=1) + '\n')
print(out, out.stat().st_size)
