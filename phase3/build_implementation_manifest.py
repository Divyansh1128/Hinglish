"""Build/check Phase-3 step-2 freeze; held-out bytes are hashed, never parsed.

python3 -B phase3/build_implementation_manifest.py [--check]
Earlier manifests are verified with their own --check before deriving this one.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from colab_notebooks import build_phase3_step2_notebooks as nb
from t4_smoke import phase3_contract as c, phase3_eval as ev, train_phase3 as train
from phase3_analysis import analyze as analysis

MANIFEST = ROOT / 'phase3/IMPLEMENTATION_MANIFEST.md'
STEP2 = ['t4_smoke/phase3_registry.py', 't4_smoke/phase3_contract.py', 't4_smoke/train_phase3.py', 't4_smoke/phase3_eval.py',
         't4_smoke/test_train_phase3.py', 't4_smoke/test_phase3_eval.py',
         'phase3_analysis/__init__.py', 'phase3_analysis/analyze.py', 'phase3_analysis/compare.py', 'phase3_analysis/descriptive.py',
         'phase3_analysis/tests/test_analyze.py', 'colab_notebooks/build_phase3_step2_notebooks.py',
         'colab_notebooks/phase3/Phase3_Train.ipynb', 'colab_notebooks/phase3/Phase3_FinalTest.ipynb',
         'phase3/step2_runtime_contract.json', 'phase3/build_implementation_manifest.py',
         'phase3/STEP2_RUNBOOK.md', 'phase3/AUDIT_RUBRIC.md']


def verify_earlier():
    for script in ('phase2/build_implementation_manifest.py', 'phase3/build_target_gen_manifest.py'):
        result = subprocess.run([sys.executable, '-B', str(ROOT / script), '--check'], cwd=ROOT,
                                text=True, capture_output=True)
        c.require(result.returncode == 0, script + ' --check failed:\n' + result.stdout + result.stderr)
    return c.verify_prior(ROOT)


def build():
    prior = verify_earlier()
    c.require(nb.build(check=True), 'Step-2 runtime/notebooks stale; rebuild first')
    old = c.block((ROOT / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
    target = c.block((ROOT / 'phase3/TARGET_GEN_MANIFEST.md').read_bytes())
    files = set(nb.sources()) | set(STEP2) | set(old['files']) | set(target['files'])
    files |= {'phase3/TARGET_GEN_MANIFEST.md', 'phase2/PREREGISTRATION.md', 'phase2/final_test.v3.json'}
    dev = ev.verify_dev_bridge(ROOT)
    return dict(schema='phase3-implementation-manifest-1',
        prior_manifests=dict(verified=prior, method='Both original builders --check plus byte verification of all listed files'),
        files={p: c.file_sha(ROOT / p) for p in sorted(files)},
        target_freeze=c.block((ROOT / 'phase3/TARGETS_FROZEN.md').read_bytes()),
        exposure=dict(path='phase3/EXPOSURE_ORDER.json', sha256=c.file_sha(ROOT / 'phase3/EXPOSURE_ORDER.json'),
                      visits_per_run=480, examples_per_run=960, updates=60, seeds=[11, 22, 33, 44, 55]),
        training=dict(recipe=train.RECIPE, grad_scaler=train.p2.SCALER, schedule=train.p2.SCHEDULE_RULE,
            stack=dict(train.ts.PINS, torch=train.ts.TORCH_BUILD), run_order=dict(slots=[11,22,33], arms=['EC','ER','EE'], reserves=[44,55]),
            recovery='One from-scratch retry for typed infrastructure failure; reserves replace whole triplets; numerical/protocol halt; no partial resume'),
        model=old['model'], base_weight_shards_sha256=nb.step1.contract()['base_weight_shards_sha256'],
        inference_bridge=dict(phase2_manifest_sha256=c.OLD_MANIFEST_SHA,
            dev_config_sha256=c.DEV_CONFIG_SHA, final_test_config_sha256=c.FINAL_CONFIG_SHA,
            transport_modes='phase2_dev / phase2_final_test; identical frozen engine, all config bytes unchanged; Phase-3 study binding separate'),
        baseline_dev=dev,
        baseline_final_test=ev.archive_byte_binding(ROOT / ev.FINAL_ARCHIVE, c.FINAL_ARCHIVE_SHA),
        statistical_core=dict(path='phase2_analysis/analyze.py', sha256=analysis.CORE_SHA,
            bootstrap_seed=101, resamples=10000, matrix_sha256=analysis.MATRIX_SHA,
            unchanged='bootstrap, quantiles, labels, degeneracy, English flags and numeric endpoints'),
        notebooks=dict(train_payload_sha256=c.sha(nb.payload('train')),
            target_notebook_sha256=c.file_sha(ROOT / 'colab_notebooks/phase3/Phase3_Targets.ipynb'),
            final_payload='Post-adapter-freeze FINAL_EVAL_PAYLOAD.zip; separate FINAL_EVAL_MANIFEST.md binds payload, adapter freeze, implementation and frozen launcher; cannot build before gate'),
        gate_status='Implementation only. No training, Phase-3 DEV/FINAL_TEST evaluation, adapter freeze, outcome unsealing or server-side archival evidence claimed.',
        judgments=judgments(), self_hash_note='Self hash printed externally; manifest excludes its own bytes.')


def judgments():
    return [
        'Hard new-files-only rule wins over request to edit frozen build_phase3_notebooks.py: sibling builder imports step-1 helpers; frozen Targets notebook unchanged.',
        'FinalTest notebook is a frozen launcher. Data-bearing final payload and separate launch manifest are built only after adapter freeze; this avoids pre-freeze test copying and circular implementation/notebook/adapter hashes.',
        'Original engine transport modes are retained to make inference digests exactly identical; Phase-3 provenance is a separate binding, never a forged Phase-2 manifest.',
        'Before adapter freeze, original FINAL_TEST archive/member bytes are only hashed. Semantic baseline validation runs after the adapter gate and before new generation; failure cannot authorize regeneration.',
        'S=1/2 descriptive attrition branch follows preregistration §10 despite nominal nine-adapter deliverable; S=0 refuses access; S=3 requires all nine adapters for primary labels.',
        'Operator ARM/SEED settings assert the append-only plan rather than select a run. Checkpoints remain diagnostics; no partial training resume is exposed.',
        'DEV is sealed on console too; complete DEV archives support sanity review. All successful attempts, including later discarded seeds, require DEV sanity.',
        'The outer implementation manifest is copied to Drive separately; notebook payloads embed a separately hashed runtime contract to avoid a circular notebook hash.',
        'The Pilot-B taxonomy is retained with Phase-3 full-human-check and labelled-equation clarification in AUDIT_RUBRIC.md; no audit labels are assigned before outcomes.',
        'Output-length IQR is added descriptively outside the unchanged statistical core; primary computations and labels are untouched.',
        'Primary analysis writes into a new directory once; descriptive comparison requires its complete report and matching export receipts.',
        'Runtime authentication checks resolved imported source paths and hashes plus the full engine inventory; --root must be the executing tree.',
        'Study registry under train root reserves canonical study-relative paths, then binds the unchanged engine run ID using a zero-generation initialization before generation; one OS lock covers registration through export. The adapter freeze binds DEV registry rows; later FINAL_TEST append operations are excluded from generic training-log hashes.',
        'The notebook requires the independently archived implementation SHA-256 as an explicit setting immediately after Drive mount; embedding it in the notebook hashed by that manifest is circular.',
        'Only the Markdown title and explicit study attribution change; original Phase-2 method/baseline references stay intact.',
        'Prior archival evidence and independent execution review are operator prerequisites in STEP2_RUNBOOK.md, not fabricated execution claims.'
    ]


def render():
    return '# Phase-3 training/evaluation implementation manifest\n\nGenerated by `python3 -B phase3/build_implementation_manifest.py`; verify with `--check`.\n\n```json\n' + json.dumps(build(), indent=2, ensure_ascii=False) + '\n```\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    raw = render().encode()
    if args.check:
        c.require(MANIFEST.is_file() and MANIFEST.read_bytes() == raw, 'Phase-3 implementation manifest STALE')
    else:
        MANIFEST.write_bytes(raw)
    print('Phase-3 implementation manifest verified:', c.sha(raw))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
