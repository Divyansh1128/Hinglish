"""Model-free checks of the smoke variant; no CUDA dependencies installed."""
import ast
import base64
import hashlib
import io
from pathlib import Path
import tempfile
import sys
import zipfile
import nbformat

root=Path(__file__).parent
nb=nbformat.read(root/'Hinglish_Math_Qwen_GPU_Smoke_Colab.ipynb',as_version=4)
nbformat.validate(nb)
for c in nb.cells:
    if c.cell_type=='code':ast.parse(c.source)
for mode in ('diagnostic','simulated_success'):
    for name in list(sys.modules):
        if name == 'hinglish_pilot' or name.startswith('hinglish_pilot.'):
            del sys.modules[name]
    with tempfile.TemporaryDirectory() as directory:
        ns={'__name__':'__main__'}
        for i,c in enumerate(nb.cells):
            if c.cell_type!='code':continue
            source=c.source.replace("PACKAGE = Path('/content/hinglish_qwen_gpu_smoke') if Path('/content').exists() else Path.cwd()/'hinglish_qwen_gpu_smoke'",f'PACKAGE = Path({directory!r})')
            if source.startswith('GPU_READY=False'):
                source="GPU_READY=False\nwrite(RUN_DIR/'smoke_environment.json',environment())\nwrite(RUN_DIR/'smoke_status.json',STATE)"
            if source.startswith('backend=None') and mode=='simulated_success':
                source="from hinglish_pilot.engine import FakeBackend\nCONFIG['model_revision']=CONFIG['tokenizer_revision']='0'*40\nbackend=FakeBackend()\nwrite(RUN_DIR/'smoke_config.json',CONFIG)"
            exec(compile(source,f'gpu-cell-{i}','exec'),ns)
        with zipfile.ZipFile(ns['RESULTS_ZIP']) as z:
            lines=z.read('checksums.sha256').decode().splitlines()
            for line in lines:
                sha,name=line.split('  ',1)
                assert hashlib.sha256(z.read(name)).hexdigest()==sha
            assert 'smoke_status.json' in z.namelist()
        pin=(Path(directory)/'requirements-colab.txt').read_text()
        assert 'bitsandbytes==0.50.2' in pin and '0.45.5' not in pin
        assert "'bitsandbytes': '0.50.2'" in (Path(directory)/'hinglish_pilot/hf_backend.py').read_text()
        print('PASS',mode,'and all ZIP checksums; no real model execution')
print('PASS nbformat schema and Python syntax')
