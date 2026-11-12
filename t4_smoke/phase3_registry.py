"""Study-wide, append-only evaluation reservations and journal identity.

Paths are canonical relative to the study root (train_root.parent), so a complete
study can be copied from Drive without changing its registered relative layout.
The OS lock is held through generation/export; unsupported locking fails closed.
"""
import contextlib
import fcntl
import json
from pathlib import Path
from t4_smoke import phase3_contract as c, train_phase2 as p2, train_phase3 as train

NAME = 'EVALUATION_REGISTRY.jsonl'
LOCK = 'EVALUATION_REGISTRY.lock'


@contextlib.contextmanager
def locked(train_root):
    root = Path(train_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / LOCK).open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise p2.Refused('Study evaluation registry locked or locking unsupported') from error
        try:
            yield root
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def records(train_root):
    reservations = {}
    for entry in p2.read_log(Path(train_root) / NAME):
        key = (entry['adapter']['arm'], entry['adapter']['seed'], entry['adapter']['attempt'], entry['split'])
        if entry['event'] == 'reserve':
            c.require(key not in reservations, 'Duplicate registered adapter/split')
            reservations[key] = entry
        else:
            c.require(entry['event'] == 'bind' and key in reservations, 'Invalid registry history')
            previous = reservations[key]
            c.require(previous['engine_run_id'] is None, 'Engine identity already bound')
            c.require(all(entry[k] == previous[k] for k in ('freeze_sha256', 'adapter', 'split', 'canonical_run_dir')),
                      'Registry identity changed')
            c.require(isinstance(entry['engine_run_id'], str) and entry['engine_run_id'], 'Missing engine run ID')
            reservations[key] = entry
    return list(reservations.values())


def canonical(train_root, run_dir):
    study = Path(train_root).resolve().parent
    path = Path(run_dir).resolve()
    c.require(path.is_relative_to(study), 'Evaluation directory outside study root')
    return path.relative_to(study).as_posix()


def reserve(train_root, run_dir, adapter, split, freeze_sha):
    """Caller must hold locked() until generation and export finish."""
    relative = canonical(train_root, run_dir)
    matches = [r for r in records(train_root) if all(r['adapter'][k] == adapter[k] for k in ('arm', 'seed', 'attempt')) and r['split'] == split]
    if matches:
        entry, = matches
        c.require(entry['adapter'] == adapter, 'Registered adapter identity changed')
        c.require(entry['canonical_run_dir'] == relative, 'Adapter/split already registered in another directory')
        c.require(entry['freeze_sha256'] == freeze_sha, 'Registered freeze differs')
        path = Path(run_dir) / 'run_manifest.json'
        if entry['engine_run_id'] is not None:
            c.require(path.is_file() and json.loads(path.read_bytes())['run_id'] == entry['engine_run_id'],
                      'Recovery must reuse the registered journal and engine run ID')
            from hinglish_pilot.engine import selected
            manifest = json.loads(path.read_bytes())
            journal, _ = selected(run_dir)
            c.require(len(journal) >= manifest['attempts'], 'Registered journal lost attempts')
            aggregate = Path(run_dir) / 'generation_attempts.jsonl'
            c.require(aggregate.is_file(), 'Registered journal aggregate missing')
            saved = [json.loads(line) for line in aggregate.read_bytes().splitlines() if line]
            c.require(all(row in journal for row in saved), 'Registered journal lost stored attempts')
        return entry
    expected = (train.attempt_dir(train_root, adapter['arm'], adapter['seed'], adapter['attempt']) / 'dev_eval'
                if split == 'dev' else Path(train_root).resolve().parent / 'final_test' / train.run_name(adapter['arm'], adapter['seed']))
    c.require(Path(run_dir).resolve() == expected.resolve(), 'Noncanonical evaluation directory')
    c.require(not Path(run_dir).exists(), 'Unregistered evaluation history; preserve and investigate')
    entry = dict(freeze_sha256=freeze_sha, adapter=adapter, split=split, canonical_run_dir=relative, engine_run_id=None)
    p2.log_event(Path(train_root) / NAME, 'reserve', **entry)
    return entry


def bind(train_root, entry, run_dir, manifest):
    if entry['engine_run_id'] is not None:
        c.require(manifest['run_id'] == entry['engine_run_id'], 'Registered engine identity changed')
        return
    # A crash during engine initialization may leave a zero-generation journal.
    # Never adopt a pre-existing generation history without a prior engine binding.
    folder = Path(run_dir)
    c.require(not any((folder / 'journal').rglob('*.json')) and manifest.get('attempts', 0) == 0,
              'Unbound generation history refused')
    fields = {k: entry[k] for k in ('freeze_sha256', 'adapter', 'split', 'canonical_run_dir')}
    p2.log_event(Path(train_root) / NAME, 'bind', **fields, engine_run_id=manifest['run_id'])


def reconcile(train_root, evaluations, frozen, freeze_sha):
    """All registered DEV/FINAL histories must resolve; extras anywhere in study refuse."""
    study = Path(train_root).resolve().parent
    c.require(Path(evaluations).resolve() == study / 'final_test', 'Use the registered study evaluation root')
    rows = records(train_root)
    expected = frozen['adapters']
    finals = [r for r in rows if r['split'] == 'final_test']
    c.require(len(finals) == len(expected) and all(any(r['adapter'] == a for r in finals) for a in expected),
              'Missing registered FINAL_TEST histories')
    known = set()
    for row in rows:
        folder = study / row['canonical_run_dir']
        c.require(canonical(train_root, folder) == row['canonical_run_dir'], 'Registry path is not canonical')
        c.require(row['split'] != 'final_test' or row['freeze_sha256'] == freeze_sha, 'Registered freeze differs')
        verify_history(study, row)
        known.add(folder.resolve())
    found = {p.parent.resolve() for p in study.rglob('run_manifest.json')}
    found |= {p.parent.resolve() for p in study.rglob('generation_attempts.jsonl')}
    found |= {p.parent.resolve() for p in study.rglob('journal') if p.is_dir()}
    c.require(found == known, 'Unregistered or extra evaluation history in study')
    exports = {p.resolve() for p in study.rglob('*_results.zip')}
    c.require(exports == {p.parent / (p.name + '_results.zip') for p in known}, 'Unregistered or extra evaluation export')
    return rows


def verify_history(study, row):
    folder = Path(study) / row['canonical_run_dir']
    path = folder / 'run_manifest.json'
    c.require(row['engine_run_id'] is not None and path.is_file(), 'Unresolved registered evaluation history')
    manifest = json.loads(path.read_bytes())
    c.require(manifest['run_id'] == row['engine_run_id'] and manifest['status'] == 'COMPLETE',
              'Registered journal incomplete or substituted')
    archive = folder.parent / (folder.name + '_results.zip')
    from phase2_analysis import analyze as core
    members, _ = core.read_run_members(archive)
    c.require(json.loads(members['run_manifest.json']) == manifest, 'Export differs from registered engine manifest')
    c.require(members['generation_attempts.jsonl'] == (folder / 'generation_attempts.jsonl').read_bytes(),
              'Export omits registered attempts')
    # Rebuild from the atomic journal, not merely its aggregate export file.
    from hinglish_pilot.engine import selected
    journal, completed = selected(folder)
    c.require(manifest.get('attempts') == len(journal), 'Registered attempt count differs')
    c.require(journal == [json.loads(line) for line in members['generation_attempts.jsonl'].splitlines() if line],
              'Export omits registered journal history')
