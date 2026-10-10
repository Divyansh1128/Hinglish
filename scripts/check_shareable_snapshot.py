"""Scan staged research files and nested notebook/ZIP payloads without printing secrets.

Standard library only. This detects common credential patterns, not all possible
private information. Review the staged file list separately before publication.
"""
import ast
import base64
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github_token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'huggingface_token': re.compile(rb'\bhf_[A-Za-z0-9]{25,}\b'),
    'openai_token': re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}\b'),
    'aws_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
}
findings=[]
inspected=0

def scan(name, raw, depth=0):
    global inspected
    if depth>5:
        raise ValueError('Nested payload exceeds scan limit: '+name)
    inspected+=1
    for kind,pattern in PATTERNS.items():
        if pattern.search(raw):
            findings.append({'path':name,'pattern':kind})
    if raw.startswith(b'PK\x03\x04'):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for entry in archive.infolist():
                if entry.is_dir():
                    continue
                if entry.file_size>20_000_000:
                    raise ValueError('Archive entry exceeds scan limit: '+name+'!'+entry.filename)
                scan(name+'!'+entry.filename,archive.read(entry),depth+1)
    elif name.endswith('.ipynb'):
        notebook=json.loads(raw)
        for index,cell in enumerate(notebook['cells']):
            source=''.join(cell['source'])
            if cell['cell_type']!='code':
                continue
            tree=ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='b64decode' and node.args:
                    value=node.args[0]
                    if isinstance(value,ast.Constant) and isinstance(value.value,str):
                        scan(f'{name}!cell{index}-embedded',base64.b64decode(value.value,validate=True),depth+1)

def main():
    paths=subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'],cwd=ROOT).decode().split('\0')
    paths=[p for p in paths if p]
    if not paths:
        raise ValueError('Stage a snapshot before scanning')
    forbidden=[p for p in paths if 'codex-session-' in p or 'local_demo/' in p or '__pycache__/' in p or p.endswith('.DS_Store') or '/review_submissions/' in '/'+p]
    if forbidden:
        raise ValueError('Excluded local/private paths were staged: '+', '.join(forbidden))
    for path in paths:
        raw=subprocess.check_output(['git','show',':'+path],cwd=ROOT)
        scan(path,raw)
    print(json.dumps({'status':'FAIL' if findings else 'PASS','staged_files':len(paths),
                      'payloads_inspected':inspected,'credential_pattern_findings':findings},indent=2))
    return 1 if findings else 0

if __name__=='__main__':
    sys.exit(main())
