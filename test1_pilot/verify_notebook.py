"""Optional nbformat/nbclient verification; uses no CUDA packages."""
from pathlib import Path
import ast
import hashlib
import json
import nbformat
from nbclient import NotebookClient

root=Path(__file__).parent.resolve()
original=root/'Hinglish_Math_Test1_Pilot_Colab.ipynb'
nb=nbformat.read(original,as_version=4)
nbformat.validate(nb)
for cell in nb.cells:
    if cell.cell_type=='code':ast.parse(cell.source)
output=root/'local_demo'
output.mkdir(exist_ok=True)
package=output/('fresh_kernel_package_'+hashlib.sha256(original.read_bytes()).hexdigest()[:12])
for cell in nb.cells:
    if cell.cell_type=='code':
        cell.source=cell.source.replace("PACKAGE = Path('/content/hinglish_test1') if Path('/content').exists() else Path.cwd() / 'hinglish_test1'",f'PACKAGE = Path({str(package)!r})')
client=NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(output)}})
client.execute()
nbformat.validate(nb)
nbformat.write(nb,output/'Hinglish_Test1_EXECUTED_DEMO.ipynb')
# Verify chart helper separately on the completed, labeled demo, with actual matplotlib.
import sys
sys.path.insert(0,str(package))
from hinglish_pilot.report import plot
import matplotlib
matplotlib.use('Agg')
run=package/'runs/demo/demo-v2'
fig=plot(run)
assert fig is not None
# Notebook test archive was generated before chart; verify all checksums.
import zipfile
archive=run.parent/'demo-v2_results.zip'
with zipfile.ZipFile(archive) as z:
    for line in z.read('checksums.sha256').decode().splitlines():
        expected,name=line.split('  ',1)
        assert hashlib.sha256(z.read(name)).hexdigest()==expected
report={'notebook_schema':'PASS nbformat 5.10.4','fresh_kernel_cells':'PASS',
        'demo_export_checksums':'PASS','demo_plot':'PASS',
        'notebook_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
        'gpu_execution':'NOT PERFORMED','label':'DEMO — NOT RESEARCH EVIDENCE'}
(output/'notebook_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
