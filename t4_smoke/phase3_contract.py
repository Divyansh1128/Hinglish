"""Phase-3 identities and byte-only gates. Never opens held-out data semantically."""
import hashlib
import json
import re
import sys
from pathlib import Path
from t4_smoke import train_phase2 as p2

ROOT = Path(__file__).resolve().parents[1]
TARGET_SHA = 'df85aa0554a4122b23226c6a34d1343cd3472ffba4de8b6d095adb252ba349b0'
OLD_MANIFEST_SHA = '726241c5726aaba2c51fc027866dd572abfc13d02ef9235d1901af87a9f5b43d'
TARGET_MANIFEST_SHA = '6652022b395d097db7e6ee1431f79e7ea81ab5ca0c3e8f026059730e5fa30c46'
DEV_SHA = 'a8194ac29cb17711d8e8e526835daacc368fdc4b5265f51d41f96edff347171a'
FINAL_ARCHIVE_SHA = 'fb4a71ccb22d8d4f274ec3c94c0b7455f870aebe7fcc673d18e47632a0024f9a'
FINAL_CONFIG_SHA = '91a0cf80d989a9ff5cb1aec15207a4298c2b0c7422d9304b70a4b56dcab6c915'
DEV_CONFIG_SHA = 'ef75d11575fb2b609fb81023b186c7f6f4038346d53e8a0e81146c12e16d8b85'
FINAL_RUN_ID = 'phase2_final_test-627d68ad676f426c8c698c0258d433d6'
require = p2.require


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def block(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    match = re.search(r'```json\s*\n(.*?)\n```', raw, re.S)
    require(match is not None, 'Missing JSON manifest block')
    return json.loads(match.group(1))


def safe_path(root, name):
    require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe manifest path')
    return Path(root) / name


def verify_prior(root=ROOT):
    result = {}
    for name, expected in [('phase2/IMPLEMENTATION_MANIFEST.md', OLD_MANIFEST_SHA),
                           ('phase3/TARGET_GEN_MANIFEST.md', TARGET_MANIFEST_SHA)]:
        raw = (Path(root) / name).read_bytes()
        require(sha(raw) == expected, name + ' identity changed')
        doc = block(raw)
        files = dict(doc['files'])
        if 'preregistration' in doc:
            p = doc['preregistration']
            files[p['path']] = p['sha256']
        for path, checksum in files.items():
            require(file_sha(safe_path(root, path)) == checksum, 'Frozen input changed: ' + path)
        result[name] = expected
    return result


def load_targets(root=ROOT):
    raw = (Path(root) / 'phase3/targets.v1.json').read_bytes()
    require(sha(raw) == TARGET_SHA, 'Frozen targets SHA-256 mismatch')
    freeze = block((Path(root) / 'phase3/TARGETS_FROZEN.md').read_bytes())
    require(freeze['targets_sha256'] == TARGET_SHA and freeze['Q'] == 158, 'Target freeze mismatch')
    require(file_sha(Path(root) / 'results/phase3/targets/Phase3_Targets_frozen.zip') == freeze['archive_sha256'],
            'Frozen target archive/journals/review ledger changed')
    doc = json.loads(raw)
    require(doc['Q'] == len(doc['families']) == 158 and doc['terminal_marker'] == '<|im_end|>'
            and doc['terminal_id'] == 151645, 'Target protocol mismatch')
    rows = {row['family_id']: row for row in doc['families']}
    require(len(rows) == 158, 'Duplicate target family')
    for row in rows.values():
        require(sha(row['candidate_output'].encode()) == row['text_sha256'], 'Target text mismatch')
        require(set(row['lengths']) == {'E', 'R', 'C'} and max(row['lengths'].values()) <= 1024,
                'Target length ledger mismatch')
    return rows


def verify_implementation(root=ROOT, *, full=False):
    root = Path(root).resolve()
    require(root == ROOT.resolve(), '--root differs from executing tree; use the authenticated checkout')
    raw = (root / 'phase3/IMPLEMENTATION_MANIFEST.md').read_bytes()
    doc = block(raw)
    require(doc['schema'] == 'phase3-implementation-manifest-1', 'Wrong Phase-3 manifest')
    # Runtime payloads omit notebooks, archives and FINAL_TEST. Verify every executable/input
    # in the separately frozen runtime contract, with its hash bound by the outer manifest.
    contract_raw = (root / 'phase3/step2_runtime_contract.json').read_bytes()
    require(sha(contract_raw) == doc['files']['phase3/step2_runtime_contract.json'], 'Runtime contract changed')
    contract = json.loads(contract_raw)
    for name, expected in [('phase2/IMPLEMENTATION_MANIFEST.md', OLD_MANIFEST_SHA),
                           ('phase3/TARGET_GEN_MANIFEST.md', TARGET_MANIFEST_SHA)]:
        prior_raw = (root / name).read_bytes()
        require(sha(prior_raw) == expected, 'Prior manifest identity changed: ' + name)
        prior_files = block(prior_raw)['files']
        for path in set(prior_files) & set(contract['files']):
            require(contract['files'][path] == prior_files[path], 'Frozen source pin changed: ' + path)
    for path, checksum in contract['files'].items():
        require(doc['files'].get(path) == checksum, 'Runtime/outer manifest disagreement: ' + path)
        require(file_sha(safe_path(root, path)) == checksum, 'Runtime input changed: ' + path)
    require(contract['targets_sha256'] == TARGET_SHA and contract['final_config_sha256'] == FINAL_CONFIG_SHA
            and contract['dev_config_sha256'] == DEV_CONFIG_SHA, 'Runtime constants changed')
    verify_running_sources(root, contract, doc)
    if full:
        for path, checksum in doc['files'].items():
            require(file_sha(safe_path(root, path)) == checksum, 'Implementation changed: ' + path)
        verify_prior(root)
    return doc, sha(raw)


def verify_running_sources(root, contract, manifest):
    """Authenticate resolved imported sources and the engine's complete inventory.

    Data and code share one root. Alternate --root trees are deliberately refused.
    The outer manifest additionally covers entry points not shipped in GPU payloads.
    """
    prefixes = ('t4_smoke.', 'hinglish_pilot', 'phase2_analysis', 'phase3_analysis',
                'secondary_analysis', 'paper_analysis.safezip')
    for name, module in list(sys.modules.items()):
        if not name.startswith(prefixes) or '.test' in name:
            continue
        source = getattr(module, '__file__', None)
        if source is None:
            continue
        source = Path(source).resolve()
        require(source.is_relative_to(root), 'Running code outside executing tree: ' + name)
        relative = source.relative_to(root).as_posix()
        expected = contract['files'].get(relative, manifest['files'].get(relative))
        require(expected is not None and file_sha(source) == expected, 'Running code differs: ' + relative)
    main = sys.modules.get('__main__')
    source = getattr(main, '__file__', None)
    if source:
        source = Path(source).resolve()
        if source.is_relative_to(root) and source.relative_to(root).as_posix() in manifest['files']:
            relative = source.relative_to(root).as_posix()
            require(file_sha(source) == manifest['files'][relative], 'Running entry point differs: ' + relative)
    from hinglish_pilot import engine
    folder = Path(engine.__file__).resolve().parent
    actual = {p.relative_to(root).as_posix() for p in folder.glob('*.py')}
    expected = {p for p in contract['files'] if p.startswith('test1_pilot/hinglish_pilot/') and p.endswith('.py')}
    require(actual == expected, 'Running engine source inventory differs')
    for path in actual:
        require(file_sha(root / path) == contract['files'][path], 'Running engine changed: ' + path)
