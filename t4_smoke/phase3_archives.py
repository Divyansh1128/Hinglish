"""Phase-3 recovery validation around the byte-frozen Phase-2 validators.

Archive bytes and journal digests are never rewritten. Only authenticated, resolved
interruption records are projected to the legacy infrastructure-failure spelling.
"""
import json
from t4_smoke import train_phase2 as p2
from phase2_analysis import analyze as core


def generation_problems(run, config, journal, errors, order):
    projected = []
    for item in journal:
        if isinstance(item, dict) and item.get('status') == 'in_progress':
            history = sorted([r for r in journal if isinstance(r, dict)
                              and r.get('rendering_id') == item.get('rendering_id')],
                             key=lambda r: r.get('attempt_number', 0))
            if not (item.get('infrastructure_failure') is True
                    and item.get('error_code') == 'interrupted_before_commit'
                    and 'raw_response' in item and item['raw_response'] is None
                    and item.get('record_sha256') == p2.engine_digest(
                        {k: v for k, v in item.items() if k != 'record_sha256'})
                    and item in errors and errors == [r for r in journal if isinstance(r, dict) and r.get('status') != 'generated']
                    and history and history[-1].get('status') == 'generated'
                    and item is not history[-1]
                    and [r.get('attempt_number') for r in history] == list(range(1, len(history) + 1))
                    and len(history) <= 1 + config.get('max_infrastructure_retries', 0)):
                return p2.generation_problems(run, config, journal, errors, order) or ['Unresolved interruption']
            item = dict(item, status='infrastructure_failure')
            item['record_sha256'] = p2.engine_digest({k: v for k, v in item.items() if k != 'record_sha256'})
        projected.append(item)
    # The original mirror was checked above before projecting either side.
    projected_errors = [r for r in projected if isinstance(r, dict) and r.get('status') != 'generated']
    return p2.generation_problems(run, config, projected,
        projected_errors if projected != journal else errors, order)


def journal_inputs(members):
    rows = lambda name: [json.loads(line) for line in members[name].splitlines() if line.strip()]
    return (json.loads(members['run_manifest.json']), json.loads(members['experiment_config.json']),
            rows('generation_attempts.jsonl'), rows('errors.jsonl'), json.loads(members['evaluation_order.json']))


def baseline_archive_problems(archive, record, manifest, adapter=None):
    problems = p2.baseline_archive_problems(archive, record, manifest, adapter=adapter)
    try:
        members, _ = core.read_run_members(archive)
    except ValueError:
        if problems:
            return problems
        raise
    if any(name not in members for name in p2.BASELINE_MEMBERS):
        return problems
    args = journal_inputs(members)
    original = p2.generation_problems(*args)
    # Legacy archive validator appends exactly this suffix; retain every other check.
    if original:
        p2.require(problems[-len(original):] == original, 'Legacy validator journal suffix changed')
        problems = problems[:-len(original)]
    return problems + generation_problems(*args)


def load_run(path):
    run = core.load_run(path)
    members, _ = core.read_run_members(path)
    args = journal_inputs(members)
    # The legacy journal validator is DEV-sized; its other checks apply to both splits.
    problems = generation_problems(*args)
    count = len(args[-1])
    if count != p2.BASELINE_PROMPTS:
        message = f"{count} resolved generations over {count} renderings; exactly {p2.BASELINE_PROMPTS} required"
        problems = [p for p in problems if p != message]
    p2.require(not problems, '; '.join(problems))
    return run
