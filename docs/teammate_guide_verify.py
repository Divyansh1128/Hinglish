"""Read-only semantic/layout checks and optional PNG render for teammate guide.

Run after the builder: python docs/teammate_guide_verify.py --render
Requires PyMuPDF. Visual inspection of rendered pages remains mandatory.
"""
from pathlib import Path
import argparse
import hashlib
import json
import importlib.metadata
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'output/pdf/Hinglish_Math_Teammate_Guide.pdf'
parser = argparse.ArgumentParser()
parser.add_argument('--render', action='store_true')
args = parser.parse_args()
doc = pymupdf.open(PDF)
assert len(doc) == 12, f'Unexpected pagination: {len(doc)} pages'
texts = [page.get_text() for page in doc]
all_text = '\n'.join(texts)
for fragment in ['0/6', 'DRAFT', '10,000', '90', 'E+E', 'E+R', 'E+C', 'invalid_unit', 'No reviewed research pilot', '1cfa9a7208912126459214e8b04321603b3df60c']:
    assert fragment in all_text, f'Missing key content: {fragment}'
for forbidden in ['/Users/', 'divyanshraj', '\ufffd', '\u25a0', ':codex-', 'FINAL: 31', 'FINAL: 30']:
    assert forbidden not in all_text, f'Forbidden/private/invalid content: {forbidden}'
for index, page in enumerate(doc):
    assert len(texts[index]) > 1000, f'Sparse or overflow page {index+1}'
    assert str(index+1) in texts[index].splitlines(), 'Missing page number'
    for block in page.get_text('blocks'):
        x0,y0,x1,y1 = block[:4]
        assert x0 >= 35 and x1 <= page.rect.width-35, f'Horizontal spill on page {index+1}'
        assert y0 >= 10 and y1 <= page.rect.height-10, f'Vertical spill on page {index+1}'
    if args.render:
        out = ROOT / 'tmp/pdfs' / f'page-{index+1:02d}.png'
        out.parent.mkdir(parents=True, exist_ok=True)
        page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(out)
versions = {name: importlib.metadata.version(name) for name in ['PyMuPDF']}
result = {
    'status': 'PASS - PDF content and layout geometry checks',
    'pages': len(doc),
    'project_snapshot_date': '2026-10-10',
    'pdf_sha256': hashlib.sha256(PDF.read_bytes()).hexdigest(),
    'source_sha256': hashlib.sha256((ROOT / 'docs/teammate_guide.md').read_bytes()).hexdigest(),
    'builder_sha256': hashlib.sha256((ROOT / 'docs/teammate_guide_build.py').read_bytes()).hexdigest(),
    'qa_versions': versions,
    'content_checks': 'Current status, all three proposed arms, preserved smoke failure, review and analysis gates, no local personal path or pilot example gold',
    'geometry_checks': 'All page text blocks stay inside page margins; 12 substantive numbered pages',
    'visual_review': 'REQUIRED: inspect all rendered pages. This script checks content/geometry only and cannot certify visual quality.',
    'limitations': 'Summarizes project artifacts. Does not certify human review, run a research pilot or reproduce literature/model training.',
}
(ROOT / 'docs/teammate_guide_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
