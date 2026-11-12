"""Validate all sealed Phase-3 exports before calling the unchanged statistical core.

python -m phase3_analysis.analyze --root REPO --train-root DRIVE/train \
    --evaluations DRIVE/final_test --out NEW_DIRECTORY
"""
import argparse
import json
from pathlib import Path
import sys
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from phase2_analysis import analyze as core
from phase3_analysis import descriptive
from t4_smoke import phase3_contract as c, phase3_eval as ev, train_phase3 as train

CORE_SHA = '11d6f1c837ff05d8de7ef96732ddca023f1f4b8faa4762b25747f7a49749150f'
MATRIX_SHA = '33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1'
WARNING = ('Pre-specified Phase-3 follow-up on a reused test set. Intervals condition on these checkpoints; '
           'they omit seed, target-selection and adaptive design variance. Cross-phase changes are descriptive.')


def statistical_core(study, ceiling_proxy_k=None):
    c.require(c.file_sha(core.__file__) == CORE_SHA, 'Frozen statistical core changed')
    return core.analyze(study, ceiling_proxy_k=ceiling_proxy_k)


def assemble(root, train_root, evaluations):
    root, evaluations = Path(root), Path(evaluations)
    frozen = ev.gate(root, train_root)
    expected = {(r['arm'], r['seed']): r for r in frozen['adapters']}
    # No operator-provided checkpoint labels. Freeze specifies every archive path.
    paths = {key: evaluations / (train.run_name(*key) + '_results.zip') for key in expected}
    c.require(all(p.is_file() for p in paths.values()), 'Outcome unsealing refused: missing required archive')
    c.require(set(p.name for p in evaluations.glob('*_results.zip')) == {p.name for p in paths.values()},
              'Unexpected or substituted evaluation archive')
    with ev.registry.locked(train_root):
        ev.registry.reconcile(train_root, evaluations, frozen, c.file_sha(root / ev.FROZEN_PATH))
    implementation, _ = ev.old_evidence(root)
    binding = dict(adapters=expected, unchanged=dict(base_weight_shards_sha256=frozen['base_weight_shards_sha256']))
    runs = {}
    receipts = {}
    for key, path in paths.items():
        run = core.load_run(path)  # unchanged safe ZIP/checksum, record identity and attempt-budget validation
        core.check_final_test_run(key, run, binding, implementation)
        c.require(run['complete'] and run['expected'] == run['completed'] == 300 and run['unresolved'] == 0,
                  'Outcome unsealing refused: unresolved evaluation')
        recorded = json.loads((evaluations / (train.run_name(*key) + '_implementation.json')).read_bytes())
        c.require(recorded == dict(study='phase3', implementation_manifest_sha256=frozen['implementation_manifest_sha256'],
            phase2_manifest_sha256=c.OLD_MANIFEST_SHA, adapter=expected[key], split='final_test',
            inference_config_sha256=core.digest(ev.config_for('final_test', expected[key]))), 'Evaluation implementation binding changed')
        runs[key] = run
        members, _ = core.read_run_members(path)
        receipts[path.name] = dict(archive_sha256=c.file_sha(path),
            journal_sha256=c.sha(members['generation_attempts.jsonl']), checksums_sha256=c.sha(members['checksums.sha256']))
    c.require(len({r['manifest']['run_id'] for r in runs.values()}) == len(runs), 'Duplicate run identity')
    # All required adapters are resolved before any analysis or output preview.
    runs[(core.UNCHANGED, None)] = ev.load_reused_baseline(root, frozen)
    role, data_sha, families = core.load_frozen_dataset(root / 'phase2/final_test.v3.json')
    c.require(role == 'FINAL_TEST', 'Wrong analysis dataset')
    model_id = core._common_model(runs, families, role)
    c.require(len({r['manifest']['dataset_sha256'] for r in runs.values()}) == 1, 'Unpaired dataset snapshots')
    baseline = ev.verify_dev_bridge(root)
    seeds = sorted(r['seed'] for r in frozen['retained_seeds'])
    freeze = dict(frozen, path=str(root / ev.FROZEN_PATH), sha256=c.file_sha(root / ev.FROZEN_PATH),
                  baseline_dev_results_zip_sha256=baseline['sha256'],
                  baseline_dev_results=baseline,
                  implementation_manifest=dict(path=str(root / 'phase3/IMPLEMENTATION_MANIFEST.md'),
                                               sha256=frozen['implementation_manifest_sha256']))
    return dict(role=role, dataset_sha256=data_sha, families=families, runs=runs, seeds=seeds,
                model_id=model_id, warnings=[WARNING], labels=frozen['confirmatory'],
                analysis_type='Phase-3 pre-specified follow-up on reused FINAL_TEST' if len(seeds) == 3 else
                    'Phase-3 descriptive reduced-S follow-up; no decision or retention labels',
                freeze=freeze, baseline=baseline, training_descriptives=descriptive.training_summary(root, train_root)), receipts


def report_markdown(result):
    text = core.markdown(result)
    title, rest = text.split('\n', 1)
    c.require(title.startswith('# Phase-2 pre-registered analysis'), 'Unexpected statistical report title')
    return title.replace('# Phase-2 pre-registered analysis', '# Phase-3 pre-specified follow-up', 1) + '\n' + rest


def run_analysis(root, train_root, evaluations, out):
    out = Path(out)
    c.require(not out.exists(), 'Primary analysis runs once into a new output directory')
    study, receipts = assemble(root, train_root, evaluations)
    result = statistical_core(study)
    c.require(result['status'] == 'COMPLETE' and result['bootstrap']['matrix_sha256'] == MATRIX_SHA,
              'Primary analysis incomplete or bootstrap matrix changed')
    # Only study attribution changes; all numerical results/labels are untouched.
    result['analysis_version'] = 'phase3 wrapper; unchanged ' + result['analysis_version']
    result['preregistration'] = 'phase3/PREREGISTRATION.md §§7–8; statistical core unchanged'
    result['sealed_export_receipts'] = receipts
    result['descriptive_output_lengths'] = descriptive.output_lengths(study)
    result['descriptive_training'] = study.get('training_descriptives')
    out.mkdir()
    (out / 'phase3_analysis.json').write_text(core.to_json(result))
    (out / 'phase3_analysis.md').write_text(report_markdown(result) + '\n\n' + WARNING + '\n')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=c.ROOT)
    p.add_argument('--train-root', type=Path, required=True)
    p.add_argument('--evaluations', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args(argv)
    run_analysis(args.root, args.train_root, args.evaluations, args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
