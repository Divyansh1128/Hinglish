"""Separate descriptive cross-phase accuracy/output-length comparison. No tests or decision labels."""
import argparse
import json
from pathlib import Path
import sys
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from phase2_analysis import analyze as core
from phase3_analysis.analyze import assemble
from t4_smoke import phase3_contract as c, phase3_eval as ev


from phase3_analysis.descriptive import length_summary


def compare_studies(phase3, phase2):
    c.require({f['family_id'] for f in phase3['families']} == {f['family_id'] for f in phase2['families']}, 'Cross-phase family mismatch')
    rows = []
    for arm in core.ARMS:
        for form in core.FORMS:
            levels = []
            for study in (phase2, phase3):
                selected = [row for (a, _), run in study['runs'].items() if a == arm
                            for row in run['selected'].values() if row['form'] == form]
                c.require(len(selected) == len(study['families']) * len(study['seeds']), 'Cross-phase coverage mismatch')
                levels.append(dict(accuracy=sum(r['correct'] for r in selected) / len(selected),
                                   output_tokens=length_summary([r.get('output_tokens') for r in selected])))
            rows.append(dict(arm=arm, form=form, phase2=levels[0], phase3=levels[1],
                             change_pp=100 * (levels[1]['accuracy'] - levels[0]['accuracy'])))
    return dict(label='DESCRIPTIVE ONLY: repeated family/seed observations; phase-specific seed means, no seed pairing',
                caveat='Targets, family membership, repetitions and supervised-token volume differ. No causal attribution to richer targets.',
                rows=rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=c.ROOT)
    p.add_argument('--train-root', type=Path, required=True)
    p.add_argument('--evaluations', type=Path, required=True)
    p.add_argument('--phase2-runs', type=Path, required=True, help='JSON map: unchanged path; arm:seed paths')
    p.add_argument('--primary-report', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args(argv)
    primary = json.loads(args.primary_report.read_bytes())
    c.require(primary['status'] == 'COMPLETE' and primary['dataset_role'] == 'FINAL_TEST'
              and primary['preregistration'].startswith('phase3/'), 'Run frozen primary analysis before descriptive comparison')
    phase3, receipts = assemble(args.root, args.train_root, args.evaluations)
    c.require(primary['sealed_export_receipts'] == receipts, 'Primary report describes different exports')
    sources = json.loads(args.phase2_runs.read_bytes())
    checkpoints = {(core.UNCHANGED, None) if k == 'unchanged' else (k.split(':')[0], int(k.split(':')[1])): Path(v)
                   for k, v in sources.items()}
    # Genuine Phase-2 assembly and all its original validators remain intact.
    with __import__('tempfile').TemporaryDirectory() as tmp:
        from paper_analysis.safezip import read_zip
        members = read_zip((args.root / ev.DEV_ARCHIVE).read_bytes())
        raw = next(blob for name, blob in members.items() if Path(name).name == 'base_results.zip')
        dev = Path(tmp) / 'base_results.zip'
        dev.write_bytes(raw)
        phase2 = core.assemble(args.root / 'phase2/final_test.v3.json', checkpoints,
                  frozen=args.root / 'phase2/ADAPTERS_FROZEN.md', implementation_manifest=args.root / 'phase2/IMPLEMENTATION_MANIFEST.md',
                  baseline_dev_results=dev)
    result = compare_studies(phase3, phase2)
    c.require(not args.out.exists(), 'Refusing to overwrite comparison')
    args.out.write_text(core.to_json(result) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
