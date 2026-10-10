"""Descriptive paired-family analysis and allowlisted exports."""
import csv
import hashlib
import json
import math
import random
import re
import statistics
import zipfile
from collections import Counter
from pathlib import Path
from .data import DEMO_LABEL, FORMS, digest, records, require
from .engine import attempts, csvfile, jsonl, read, selected, utc, write

PRED_FIELDS = ['label', 'run_id', 'family_id', 'rendering_id', 'topic', 'form', 'attempt_id',
    'input_text', 'raw_response', 'extracted_final', 'normalized_value', 'normalized_unit', 'correct',
    'invalid_reason', 'refusal', 'truncated', 'input_tokens', 'output_tokens', 'latency_seconds', 'status']
AUDIT_FIELDS = ['label', 'rendering_id', 'attempt_id', 'form', 'input_text', 'raw_response',
    'gold_value', 'gold_unit', 'automatic_correct', 'invalid_reason',
    'reviewer_id', 'manual_correct', 'reason', 'category', 'reviewed_at']


def wilson(k, n):
    z = 1.959963984540054
    p = k/n
    center = (p + z*z/(2*n))/(1+z*z/n)
    radius = z * math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [max(0, center-radius), min(1, center+radius)]


def quantile(xs, p):
    position = (len(xs)-1)*p
    low = math.floor(position)
    high = math.ceil(position)
    return xs[low] + (xs[high]-xs[low])*(position-low)


def paired(values, a, b, rng, resamples):
    diffs = [int(f[a])-int(f[b]) for f in values]
    n = len(diffs)
    draws = sorted(sum(diffs[rng.randrange(n)] for _ in range(n))/n for _ in range(resamples))
    return {'difference': sum(diffs)/n, 'bootstrap_95_interval': [quantile(draws, .025), quantile(draws, .975)],
            'both_correct': sum(f[a] and f[b] for f in values),
            'both_wrong': sum(not f[a] and not f[b] for f in values),
            'a_correct_b_wrong': sum(f[a] and not f[b] for f in values),
            'a_wrong_b_correct': sum(not f[a] and f[b] for f in values), 'families': n}


def stats(values):
    clean = [v for v in values if isinstance(v, (int, float))]
    return {'n': len(clean), 'sum': sum(clean), 'median': statistics.median(clean) if clean else None,
            'min': min(clean) if clean else None, 'max': max(clean) if clean else None}


def analyze(root, audit_overlay=None):
    root = Path(root)
    require(not (root / 'RUNNING.lock').exists(), 'Stop writer before analysis')
    manifest = read(root / 'run_manifest.json')
    config = read(root / 'experiment_config.json')
    dataset = read(root / 'dataset.json')
    require(digest(config) == manifest['config_sha256'] and digest(dataset) == manifest['dataset_sha256'] and
            digest(read(root / 'split_manifest.json')) == manifest['split_sha256'], 'Snapshot corruption')
    require(digest({'backend': manifest['backend'], 'environment': read(root / 'environment.json')}) == manifest['execution_sha256'], 'Environment snapshot changed')
    journal, done = selected(root)
    require(len(done) == manifest.get('completed', 0), 'Manifest/journal mismatch: resume run to repair completion state')
    label = manifest['label']
    complete = len(done) == manifest['expected']
    metrics = {'label': label, 'mode': manifest['mode'], 'run_id': manifest['run_id'], 'status': 'COMPLETE' if complete else 'INCOMPLETE',
               'expected': manifest['expected'], 'attempted_renderings': len({x['rendering_id'] for x in journal}),
               'completed': len(done), 'unresolved': manifest['expected']-len(done), 'attempts': len(journal),
               'independent_families': len(dataset['families']), 'created_at': utc(),
               'analysis': 'automatic', 'bootstrap_seed': config['bootstrap_seed'], 'bootstrap_resamples': config['bootstrap_resamples'],
               'warnings': manifest['warnings'], 'accuracy': None, 'paired': None, 'topics': None,
               'memory_measurement': 'PyTorch attempt peaks; endpoint device free is not a continuously measured minimum'}
    analyzed = [dict(x) for x in done]
    overlay = []
    if audit_overlay is not None:
        with Path(audit_overlay).open(newline='', encoding='utf-8') as stream:
            overlay = list(csv.DictReader(stream))
        by_id = {x['rendering_id']: x for x in analyzed}
        seen = set()
        for entry in overlay:
            if not entry.get('manual_correct', '').strip():
                continue
            rid = entry['rendering_id']
            require(rid in by_id and rid not in seen, 'Audit contains unknown or duplicate rendering')
            seen.add(rid)
            require(entry['attempt_id'] == by_id[rid]['attempt_id'], 'Audit attempt mismatch')
            require(entry['manual_correct'].lower() in ('true', 'false'), 'Audit manual_correct must be true/false')
            require(re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', entry['reviewer_id'] or '') and
                    entry['reason'].strip() and entry['reviewed_at'].strip(), 'Audit requires pseudonymous reviewer/reason/time')
            by_id[rid]['correct'] = entry['manual_correct'].lower() == 'true'
        metrics.update(analysis='manual_overlay', audit_sha256=digest(overlay), manually_reviewed=len(seen),
                       warning_manual='Manual correctness overlays do not change automatic format-failure diagnostics.')
    failure_rates = {}
    for form in FORMS:
        rows = [x for x in done if x['form'] == form]
        failure_rates[form] = {'completed': len(rows), 'invalid': sum(x['invalid_reason'] is not None for x in rows),
            'refusals': sum(x['refusal'] for x in rows), 'truncated': sum(x['truncated'] for x in rows),
            'invalid_reasons': dict(Counter(x['invalid_reason'] for x in rows if x['invalid_reason'])),
            'rates_over_completed': {kind: sum(bool(x[field]) for x in rows)/len(rows) if rows else None
                for kind, field in [('invalid', 'invalid_reason'), ('refusal', 'refusal'), ('truncated', 'truncated')]}}
    metrics['failure_diagnostics'] = failure_rates
    metrics['resources'] = {form: {field: stats(x[field] for x in done if x['form'] == form)
        for field in ('input_tokens', 'output_tokens', 'latency_seconds')} for form in FORMS}
    metrics['memory'] = {field: stats(x.get('memory', {}).get(field) for x in done)
        for field in ('peak_allocated_bytes', 'peak_reserved_bytes', 'device_free_at_end_bytes')}
    family_rows = []
    if complete:
        by_family = {f['family_id']: {'family_id': f['family_id'], 'topic': f['topic'], 'label': label} for f in dataset['families']}
        for item in analyzed:
            by_family[item['family_id']][item['form']] = bool(item['correct'])
        family_rows = list(by_family.values())
        n = len(family_rows)
        metrics['accuracy'] = {form: {'correct': sum(f[form] for f in family_rows), 'denominator': n,
            'accuracy': sum(f[form] for f in family_rows)/n, 'wilson_95_interval': wilson(sum(f[form] for f in family_rows), n)} for form in FORMS}
        rng = random.Random(config['bootstrap_seed'])
        metrics['paired'] = {a+'-'+b: paired(family_rows, a, b, rng, config['bootstrap_resamples']) for a, b in [('E', 'C'), ('E', 'R'), ('R', 'C')]}
        metrics['topics'] = {}
        for topic in sorted({f['topic'] for f in family_rows}):
            group = [f for f in family_rows if f['topic'] == topic]
            metrics['topics'][topic] = {'label': 'DESCRIPTIVE SMALL-SAMPLE', 'families': len(group),
                                      'accuracy': {form: sum(f[form] for f in group)/len(group) for form in FORMS}}
    # Every analysis revision is retained; base automatic predictions never change.
    revision = digest({'journal': [x['record_sha256'] for x in journal], 'overlay': overlay, 'config': config})[:16]
    dest = root if audit_overlay is None else root / 'analysis_revisions' / revision
    dest.mkdir(parents=True, exist_ok=True)
    metrics['analysis_revision'] = revision
    write(dest / 'metrics.json', metrics)
    csvfile(dest / 'predictions.csv', analyzed, PRED_FIELDS)
    csvfile(dest / 'family_comparisons.csv', family_rows, ['label', 'family_id', 'topic', *FORMS])
    if audit_overlay is not None:
        csvfile(dest / 'manual_overlay.csv', overlay, AUDIT_FIELDS)
    audit_rows = [dict(label=label, rendering_id=x['rendering_id'], attempt_id=x['attempt_id'], form=x['form'],
        input_text=x['input_text'], raw_response=x['raw_response'], gold_value=x['gold']['value'], gold_unit=x['gold']['unit'],
        automatic_correct=x['correct'], invalid_reason=x['invalid_reason']) for x in done]
    if not (root / 'manual_audit.csv').exists():
        csvfile(root / 'manual_audit.csv', audit_rows, AUDIT_FIELDS)
    elif audit_overlay is None:
        # Analysis can occur before completion: preserve edited audit and add newly completed rows.
        with (root / 'manual_audit.csv').open(newline='', encoding='utf-8') as stream:
            old = list(csv.DictReader(stream))
        known = {x['rendering_id'] for x in old}
        csvfile(root / 'manual_audit.csv', old + [x for x in audit_rows if x['rendering_id'] not in known], AUDIT_FIELDS)
    lines = [f'# {label}', '', f'Run status: **{metrics["status"]}**; analysis: {metrics["analysis"]}.',
        f'{len(done)}/{manifest["expected"]} outputs completed; {metrics["unresolved"]} unresolved.',
        f'{len(dataset["families"])} independent families, each with E/R/C renderings.', '',
        'Human review metadata are attestations, not automated proof of validity. All scored generations need independent manual audit.', '']
    if not complete:
        lines += ['Headline accuracy and paired comparisons suppressed. Resolve infrastructure failures before interpreting differences.']
    else:
        lines += ['| Form | Correct / families | Accuracy | Wilson 95% interval |', '|---|---:|---:|---:|']
        for form, a in metrics['accuracy'].items():
            lo, hi = a['wilson_95_interval']
            lines.append(f'| {form} | {a["correct"]}/{a["denominator"]} | {a["accuracy"]:.1%} | [{lo:.1%}, {hi:.1%}] |')
        lines += ['', 'Paired differences (percentage points); descriptive family bootstrap:']
        for name, result in metrics['paired'].items():
            lo, hi = result['bootstrap_95_interval']
            lines.append(f'- {name}: {100*result["difference"]:.1f} pp [{100*lo:.1f}, {100*hi:.1f}]')
        bad = sum(x['invalid_reason'] is not None for x in done)
        lines += ['', f'Automatic invalid/truncated outputs: {bad}/{len(done)}. Review-packet threshold: more than 3/90 requires protocol revision before scaling.',
                  'Inspect floor/ceiling effects, all format failures, language equivalence, and wrong-answer examples before choosing the next experiment.']
    lines += ['', 'Not evidence of E+C versus E+R training benefit; no training performed. No significance or internal-mechanism claim.',
              'For the executed notebook: Colab File > Download > Download .ipynb. Return it with the results ZIP.',
              'Resource telemetry excludes download/load time from generation latency. Device free is sampled at endpoints only.']
    (dest / 'summary.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return metrics, dest


def plot(root):
    import matplotlib.pyplot as plt
    root = Path(root)
    m = read(root / 'metrics.json')
    if m['accuracy'] is None:
        print(m['label'], 'INCOMPLETE: no accuracy plot')
        return None
    a = m['accuracy']
    ys = [a[f]['accuracy'] for f in FORMS]
    errors = [[a[f]['accuracy']-a[f]['wilson_95_interval'][0] for f in FORMS],
              [a[f]['wilson_95_interval'][1]-a[f]['accuracy'] for f in FORMS]]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(FORMS, ys, yerr=errors, capsize=5, color=['#3366aa', '#dd8844', '#448855'])
    ax.set(ylim=(0, 1), ylabel='Accuracy', title=f'{m["label"]}\n{m["independent_families"]} families; Wilson 95% intervals')
    fig.tight_layout()
    fig.savefig(root / 'accuracy.png', dpi=180)
    return fig


# Known credential patterns and email identifiers are rejected rather than silently
# changing reproducibility-critical source text. Review free text before sharing.
SENSITIVE = re.compile(r'\b(?:hf_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9_-]{16,}|AKIA[A-Z0-9]{16})\b|'
                       r'-----BEGIN [A-Z ]*PRIVATE KEY-----|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|'
                       r'(?i:bearer\s+[A-Za-z0-9._-]{16,})')


def export(root, notebook=None):
    root = Path(root)
    analyze(root)
    dataset = read(root / 'dataset.json')
    jsonl(root / 'dataset_snapshot.jsonl', [dict(f, dataset_version=dataset['version'],
        schema_version=dataset['schema_version'], kind=dataset['kind'], borrowing_policy=dataset['borrowing_policy']) for f in dataset['families']])
    journal = attempts(root)
    jsonl(root / 'generation_attempts.jsonl', journal)
    jsonl(root / 'errors.jsonl', [x for x in journal if x['status'] != 'generated'])
    required = ['run_manifest.json', 'environment.json', 'experiment_config.json', 'dataset_snapshot.jsonl',
                'dataset.json', 'split_manifest.json', 'generation_attempts.jsonl', 'predictions.csv',
                'family_comparisons.csv', 'metrics.json', 'summary.md', 'manual_audit.csv', 'errors.jsonl', 'evaluation_order.json']
    paths = [root / name for name in required]
    sources = sorted((root / 'source').glob('*.py'))
    require(sources and digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}) ==
            read(root / 'run_manifest.json')['code_sha256'], 'Frozen source snapshot missing or changed')
    paths += sources
    if (root / 'model_load_report.json').exists():
        paths.append(root / 'model_load_report.json')
    if (root / 'format_smoke.json').exists():
        paths.append(root / 'format_smoke.json')
    if (root / 'accuracy.png').exists():
        paths.append(root / 'accuracy.png')
    paths += sorted((root / 'analysis_revisions').glob('*/*'))
    if notebook is not None:
        require(Path(notebook).suffix == '.ipynb', 'Notebook must be ipynb')
        paths.append(Path(notebook))
    names = []
    for path in paths:
        require(path.is_file() and not path.is_symlink(), f'Export file missing or unsafe: {path.name}')
        if path.suffix != '.png':
            require(not SENSITIVE.search(path.read_text(encoding='utf-8')), f'Credential/email-like text detected in {path.name}; clean upstream inputs or remove secrets before export')
        name = str(path.relative_to(root)) if path.is_relative_to(root) else 'executed_notebook.ipynb'
        require(name not in names, 'Duplicate archive path')
        names.append(name)
    checks = ''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {name}\n' for path, name in zip(paths, names))
    (root / 'checksums.sha256').write_text(checks)
    archive = root.parent / (root.name + '_results.zip')
    temp = archive.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as z:
        for path, name in zip(paths, names):
            z.write(path, name)
        z.write(root / 'checksums.sha256', 'checksums.sha256')
    temp.replace(archive)
    return archive
