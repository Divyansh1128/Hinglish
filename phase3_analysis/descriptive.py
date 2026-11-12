"""Descriptive token accounting, separate from primary statistical mechanics."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
from phase2_analysis import analyze as core
from t4_smoke import phase3_contract as c, train_phase3 as train, train_phase2 as p2


def length_summary(values):
    clean = sorted(v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool))
    summary = core._stats(clean)
    if clean:
        summary.update(q1=core.quantile(clean, Fraction(1, 4)), q3=core.quantile(clean, Fraction(3, 4)))
        summary['iqr'] = summary['q3'] - summary['q1']
    return summary


def output_lengths(study):
    return {core.checkpoint_name(key): {form: length_summary([r.get('output_tokens') for r in run['selected'].values()
                if r['form'] == form]) for form in core.FORMS} for key, run in study['runs'].items()}


def training_summary(root, train_root):
    targets = c.load_targets(root)
    attempts = []
    for entry in p2.read_log(Path(train_root) / p2.ATTEMPT_LOG):
        if entry['event'] != 'start':
            continue
        folder = train.attempt_dir(train_root, entry['arm'], entry['seed'], entry['attempt'])
        path = folder / 'train_report.json'
        report = __import__('json').loads(path.read_bytes()) if path.exists() else {}
        updates = report.get('updates', [])
        attempts.append(dict(arm=entry['arm'], seed=entry['seed'], slot=entry['slot'], attempt=entry['attempt'],
            status=report.get('status', 'missing report'), completed_updates=len(updates),
            completed_update_input_tokens=sum(r['input_tokens'] for r in updates),
            completed_update_supervised_tokens=sum(r['supervised_tokens'] for r in updates)))
    return dict(Q=len(targets), target_tokens=length_summary([r['target_tokens'] for r in targets.values()]),
                source_counts=dict(Counter(r['source'] for r in targets.values())),
                explanation_status_counts=dict(Counter(r['explanation_status'] for r in targets.values())),
                attempts=attempts,
                note='Token totals count completed accumulation windows; failed partial-window exposures remain in failed_update records.')
