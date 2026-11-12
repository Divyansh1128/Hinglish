"""Phase-3 evaluation gates and provenance bridge to original Phase-2 evidence.

The engine transport modes remain phase2_dev/phase2_final_test to preserve the
registered configuration digest. Study identity is in separate authenticated bindings.
No baseline is generated here. FINAL_TEST is sealed and adapter-only.
"""
import argparse
import contextlib
import io
import json
import tempfile
import zipfile
from pathlib import Path
import sys
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from t4_smoke import phase3_contract as c, train_phase3 as train, phase3_registry as registry
from t4_smoke import train_phase2 as p2, phase2_eval as old, train_smoke as ts
from phase2_analysis import analyze as core
from paper_analysis.safezip import read_zip, verify_checksums

require = c.require
DEV_ARCHIVE = 'results/phase2/baseline_dev/Phase2_Baseline_DEV_results.zip'
FINAL_ARCHIVE = 'results/phase2/final_test/Phase2_FinalTest_results.zip'
FROZEN_PATH = 'phase3/ADAPTERS_FROZEN.md'


def config_for(split, adapter=None):
    config = old.config_for(split, adapter)
    require(core.digest(dict(config, adapter=None)) == {'dev': c.DEV_CONFIG_SHA, 'final_test': c.FINAL_CONFIG_SHA}[split],
            'Inference equivalence failed: amendment required; do not regenerate baseline')
    return config


def old_evidence(root):
    root = Path(root)
    require(c.file_sha(root / 'phase2/IMPLEMENTATION_MANIFEST.md') == c.OLD_MANIFEST_SHA, 'Original manifest changed')
    implementation = core.load_implementation_manifest(root / 'phase2/IMPLEMENTATION_MANIFEST.md')
    binding = core.load_frozen(root / 'phase2/ADAPTERS_FROZEN.md')
    return implementation, binding


def verify_dev_bridge(root=c.ROOT):
    root = Path(root)
    config_for('dev')
    implementation, binding = old_evidence(root)
    members = read_zip((root / DEV_ARCHIVE).read_bytes(), 'original DEV outer archive')
    names = [name for name in members if Path(name).name == 'base_results.zip']
    require(len(names) == 1, 'Original DEV archive must contain exactly one base_results.zip')
    inner = members[names[0]]
    require(c.sha(inner) == c.DEV_SHA, 'Original DEV archive hash mismatch')
    # Frozen Phase-2 validators see the genuine original manifest and archive, never a relabelled manifest.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'base_results.zip'
        path.write_bytes(inner)
        evidence = core.load_baseline(path, binding, implementation)
    evidence['path'] = DEV_ARCHIVE + '!base_results.zip'
    evidence['phase2_manifest_sha256'] = c.OLD_MANIFEST_SHA
    evidence['phase3_config_sha256'] = c.DEV_CONFIG_SHA
    return evidence


def archive_byte_binding(path, expected):
    """Byte hashing only: no response, dataset, config, journal or score is decoded.

    Allowed during the embargo. Bind every outer/inner member, including the
    original journal/config/environment/checksums, without semantic inspection.
    """
    raw = Path(path).read_bytes()
    require(c.sha(raw) == expected, 'Original FINAL_TEST outer archive hash mismatch')
    members = read_zip(raw, 'original FINAL_TEST archive (byte hashes only)')
    hashes = {name: c.sha(blob) for name, blob in members.items()}
    inner = {}
    for name, blob in members.items():
        if name.endswith('_results.zip'):
            inner[name] = {n: c.sha(b) for n, b in read_zip(blob, name).items()}
    return dict(outer_sha256=expected, members_sha256=hashes, inner_members_sha256=inner,
                original_run_id=c.FINAL_RUN_ID, original_config_sha256=c.FINAL_CONFIG_SHA,
                original_implementation_manifest_sha256=c.OLD_MANIFEST_SHA)


def validate_reused_run(run, implementation, binding, config_digest=c.FINAL_CONFIG_SHA):
    require(config_digest == implementation['final_test_config_sha256'] == c.FINAL_CONFIG_SHA,
            'Phase-3/Phase-2 inference configuration differs; halt and amend')
    core.check_final_test_run((core.UNCHANGED, None), run, binding, implementation)
    require(run['manifest']['run_id'] == c.FINAL_RUN_ID, 'Wrong original unchanged FINAL_TEST run')
    require(run['complete'] and run['expected'] == run['completed'] == 300 and run['unresolved'] == 0,
            'Original unchanged FINAL_TEST coverage incomplete')
    return run


def load_reused_baseline(root, frozen):
    """Semantic access ONLY after the Phase-3 adapter gate has succeeded at the caller."""
    require(c.block((Path(root) / FROZEN_PATH).read_bytes()) == frozen,
            'Semantic baseline access requires the actual Phase-3 adapter freeze')
    path = Path(root) / FINAL_ARCHIVE
    require(archive_byte_binding(path, c.FINAL_ARCHIVE_SHA) == frozen['baseline_final_test'], 'Frozen baseline bytes differ')
    implementation, binding = old_evidence(root)
    outer = read_zip(path.read_bytes(), 'original FINAL_TEST outer archive')
    candidates = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, blob in outer.items():
            if not name.endswith('_results.zip'):
                continue
            # The aggregate archive includes adapter exports. Keep their original provenance untouched.
            members = read_zip(blob, name)
            run_manifest = json.loads(members['run_manifest.json'])
            if run_manifest.get('run_id') == c.FINAL_RUN_ID:
                local = Path(tmp) / 'unchanged_results.zip'
                local.write_bytes(blob)
                run = validate_reused_run(core.load_run(local), implementation, binding,
                                          core.digest(config_for('final_test')))
                run['path'] = str(path) + '!' + name
                candidates.append(run)
    require(len(candidates) == 1, 'Exactly one original unchanged baseline required')
    return candidates[0]


def valid_attempt_folders(train_root):
    entries = p2.read_log(Path(train_root) / p2.ATTEMPT_LOG)
    p2.plan(entries)
    return [train.attempt_dir(train_root, e['arm'], e['seed'], e['attempt']) for e in entries
            if e['event'] == 'finish' and e['outcome'] == 'valid']


def verify_adapter(folder, root):
    folder = Path(folder)
    _, manifest_sha = c.verify_implementation(root)
    final = ts.read_json(folder / 'final_adapter.json')
    require(not p2.valid_run_problems(final), 'Invalid update-60 adapter')
    require(p2.attempt_outcome(folder)[0] == 'valid', 'Training report does not confirm valid run')
    require(final['implementation_manifest_sha256'] == manifest_sha, 'Adapter implementation differs')
    require(final['targets_sha256'] == c.TARGET_SHA, 'Adapter target identity differs')
    require(final['exposure_order_file_sha256'] == c.file_sha(Path(root) / 'phase3/EXPOSURE_ORDER.json'), 'Adapter exposure differs')
    require(old.adapter_digests(folder / 'final_adapter') == {k: final[k] for k in ('adapter_model_sha256', 'adapter_config_sha256')},
            'Adapter weight/config bytes differ')
    return final


def dev_sanity_problem(folder, root):
    try:
        final = verify_adapter(folder, root)
        old_manifest = c.block((Path(root) / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
        archive = Path(folder) / 'dev_eval_results.zip'
        members, _ = core.read_run_members(archive)
        run_manifest = json.loads(members['run_manifest.json'])
        problems = p2.baseline_archive_problems(archive, run_manifest, old_manifest, adapter=old.adapter_record(final))
        require(not problems, '; '.join(problems))
        binding = json.loads((Path(folder) / 'dev_eval_implementation.json').read_bytes())
        require(binding['implementation_manifest_sha256'] == final['implementation_manifest_sha256'], 'DEV implementation mismatch')
        train_root = Path(folder).resolve().parents[1]
        registered = [r for r in registry.records(train_root) if r['split'] == 'dev' and r['adapter'] == old.adapter_record(final)]
        require(len(registered) == 1, 'DEV lacks unique study registration')
        require(registered[0]['freeze_sha256'] == final['implementation_manifest_sha256'], 'DEV registration freeze differs')
        registry.verify_history(train_root.parent, registered[0])
        return None
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        return str(error)


def require_dev_sanity(train_root, root):
    for folder in valid_attempt_folders(train_root):
        problem = dev_sanity_problem(folder, root)
        require(problem is None, f'DEV sanity incomplete for {folder}: {problem}')


def run_dev_sanity(train_root, root, *, recover=False, evaluate=None):
    with p2.WriterLock(train_root):
        for folder in valid_attempt_folders(train_root):
            if dev_sanity_problem(folder, root) is None:
                continue
            args = ['evaluate', '--root', str(root), '--split', 'dev', '--adapter-dir', str(folder / 'final_adapter'),
                    '--adapter-record', str(folder / 'final_adapter.json'), '--run-dir', str(folder / 'dev_eval'), '--train-root', str(train_root)]
            if recover:
                args += ['--recover-stale-lock']
            code = evaluate(folder, args) if evaluate else main(args)
            require(code == 0 and dev_sanity_problem(folder, root) is None, 'DEV sanity incomplete; resume before further training')


def freeze_manifest(train_root, root=c.ROOT):
    root, train_root = Path(root), Path(train_root)
    doc, manifest_sha = c.verify_implementation(root)
    require(p2.read_writer_lock(train_root) is None, 'Active writer: freeze refused')
    entries = p2.read_log(train_root / p2.ATTEMPT_LOG)
    current = p2.plan(entries)
    require(not p2.open_attempts(current) and p2.next_run(current)['kind'] == 'complete', 'Unsettled training plan')
    require(current['S'] > 0, 'S=0: no FINAL_TEST access')
    # Reduced-S is explicit in the preregistration, never silently treated as nine adapters.
    require_dev_sanity(train_root, root)
    dev = verify_dev_bridge(root)
    records = []
    for slot, seed in current['retained']:
        for arm in p2.ARMS:
            attempt = current['slots'][slot]['arms'][arm]['valid_attempt']
            final = verify_adapter(train.attempt_dir(train_root, arm, seed, attempt), root)
            require(final['slot'] == slot and final['seed'] == seed and final['arm'] == arm, 'Slot/adapter mismatch')
            records.append(final)
    require(all(r['same_order'] and r['same_initial_adapter'] and r['arms'] == sorted(p2.ARMS)
                for r in p2.pairing(records).values()), 'Initial adapter triplet mismatch')
    starts = [e['identity'] for e in entries if e['event'] == 'start']
    require(starts and all(x == starts[0] for x in starts), 'Attempts differ in implementation/configuration')
    expected_identity = train.attempt_identity(root, dev)
    require(starts[0] == expected_identity, 'Attempt identity differs from frozen implementation')
    for final in records:
        require(all(final.get(k) == v for k, v in expected_identity.items()), 'Final adapter differs from attempt identity')
        require(final['base_weight_shards_sha256'] == doc['base_weight_shards_sha256'], 'Base shard mismatch')
    # Bind every attempt, report, recovery and sanity archive, including discarded triplets.
    logs = {}
    for path in sorted(train_root.rglob('*')):
        if path.is_file() and 'final_adapter' not in path.parts and 'checkpoint' not in path.parts and path.name not in (registry.NAME, registry.LOCK):
            logs[str(path.relative_to(train_root))] = c.file_sha(path)
    return dict(schema='phase3-adapters-frozen-1', implementation_manifest_sha256=manifest_sha,
                targets_sha256=c.TARGET_SHA, target_freeze_sha256=c.file_sha(root / 'phase3/TARGETS_FROZEN.md'),
                exposure_order_file_sha256=c.file_sha(root / 'phase3/EXPOSURE_ORDER.json'),
                base_model=ts.MODEL_ID, base_revision=ts.MODEL_REVISION,
                base_weight_shards_sha256=doc['base_weight_shards_sha256'],
                retained_seeds=[dict(slot=s, seed=v) for s, v in current['retained']], S=current['S'],
                confirmatory=current['S'] == 3, descriptive_only=current['S'] < 3,
                adapters=[old.adapter_record(f) for f in records], training_logs_sha256=logs,
                dev_evaluation_registry=[r for r in registry.records(train_root) if r['split'] == 'dev'],
                attempt_log_sha256=c.file_sha(train_root / p2.ATTEMPT_LOG), baseline_dev=dev,
                baseline_final_test=archive_byte_binding(root / FINAL_ARCHIVE, c.FINAL_ARCHIVE_SHA),
                final_test_file_sha256=c.file_sha(root / old.FROZEN['final_test'][0]))


def gate(root, train_root):
    root, train_root = Path(root), Path(train_root)
    path = root / FROZEN_PATH
    frozen = c.block(path.read_bytes())
    require(frozen['schema'] == 'phase3-adapters-frozen-1', 'Wrong adapter freeze schema')
    # Recompute from actual logs, adapters, DEV archives and byte hashes; never semantic test access here.
    require(frozen == freeze_manifest(train_root, root), 'Adapter freeze no longer matches actual evidence')
    require(frozen['S'] in (1, 2, 3) and len(frozen['adapters']) == 3 * frozen['S'], 'Incomplete triplets')
    return frozen


def bind_implementation(run_dir, root, adapter, split):
    _, checksum = c.verify_implementation(root)
    path = Path(run_dir).parent / (Path(run_dir).name + '_implementation.json')
    binding = dict(study='phase3', implementation_manifest_sha256=checksum,
                   phase2_manifest_sha256=c.OLD_MANIFEST_SHA, adapter=adapter, split=split,
                   inference_config_sha256=core.digest(config_for(split, adapter)))
    if path.exists():
        require(json.loads(path.read_bytes()) == binding, 'Run implementation binding differs')
    else:
        require(not (Path(run_dir) / 'run_manifest.json').exists(), 'Existing run lacks implementation binding')
        ts.write_json(path, binding)
    return binding


def evaluation_preflight(config, backend, original_manifest, adapter):
    from hinglish_pilot.engine import environment, PHASE2_PACKAGES, PHASE2_MODES, PACKAGES
    env = environment(PHASE2_PACKAGES if config['mode'] in PHASE2_MODES else PACKAGES)
    execution = dict(backend=backend.metadata, environment=env)
    preflight = dict(backend=backend.metadata, sessions=[execution], execution_sha256=core.digest(execution))
    problems = p2.execution_problems(preflight, env, original_manifest, adapter=adapter)
    require(not problems, 'Inference backend equivalence failed before generation: ' + '; '.join(problems))
    return preflight, env


def run_evaluate(args):
    # Derive the authoritative training root from the adapter, never from --run-dir.
    c.verify_implementation(args.root)
    train_root = Path(args.adapter_record).resolve().parents[2]
    if args.train_root is not None:
        require(Path(args.train_root).resolve() == train_root, 'Adapter outside training root')
    with registry.locked(train_root):
        return _run_evaluate(args, train_root)


def _run_evaluate(args, train_root):
    root, run_dir = Path(args.root), Path(args.run_dir)
    c.verify_implementation(root)
    final = verify_adapter(Path(args.adapter_record).parent, root)
    require(Path(args.adapter_record).resolve() == (Path(args.adapter_dir).parent / 'final_adapter.json').resolve(), 'Adapter record/path mismatch')
    require(Path(args.adapter_dir).resolve() == (Path(args.adapter_record).parent / 'final_adapter').resolve(), 'Wrong adapter directory')
    adapter = old.adapter_record(final)
    frozen = None
    if args.split == 'final_test':
        require(args.train_root is not None, 'FINAL_TEST requires training-root gate')
        frozen = gate(root, args.train_root)  # BEFORE dataset or original outcome parsing
        require(adapter in frozen['adapters'], 'Adapter outside retained freeze')
        authorized = train.attempt_dir(args.train_root, adapter['arm'], adapter['seed'], adapter['attempt'])
        require(Path(args.adapter_record).parent.resolve() == authorized.resolve(), 'Adapter path outside freeze')
        load_reused_baseline(root, frozen)  # bridge failure halts before new generation
    p2.check_stack()
    config = config_for(args.split, adapter)
    identities = old.split_identities(root)
    # Sole semantic held-out loading boundary, reached only after gate and reuse bridge.
    dataset, splits = old.inputs((root / old.FROZEN[args.split][0]).read_bytes(), args.split, identities)
    from hinglish_pilot.hf_backend import HFBackend
    from hinglish_pilot.engine import run, read, write, code_hash
    from hinglish_pilot.report import analyze, export
    c.verify_implementation(root)  # includes the modules imported above
    freeze_sha = c.file_sha(root / FROZEN_PATH) if frozen else final['implementation_manifest_sha256']
    entry = registry.reserve(train_root, run_dir, adapter, args.split, freeze_sha)
    bind_implementation(run_dir, root, adapter, args.split)
    if args.recover_stale_lock:
        old.recover_stale_lock(run_dir)
    manifest_path = run_dir / 'run_manifest.json'
    if manifest_path.exists() and read(manifest_path).get('status') == 'COMPLETE':
        manifest = read(manifest_path)
        require(entry['engine_run_id'] == manifest['run_id'], 'Completed run lacks registered engine identity')
        require(all(manifest[k] == v for k, v in dict(config_sha256=core.digest(config), dataset_sha256=core.digest(dataset),
                split_sha256=core.digest(splits), code_sha256=code_hash()).items()), 'Completed evaluation identity changed')
    else:
        original_manifest = c.block((root / 'phase2/IMPLEMENTATION_MANIFEST.md').read_bytes())
        p2.verify_hub_files(original_manifest)
        backend = HFBackend(config, adapter_path=args.adapter_dir)
        p2.verify_chat_template(backend.tokenizer, original_manifest)
        evaluation_preflight(config, backend, original_manifest, adapter)
        expected_shards = c.block((root / 'phase2/ADAPTERS_FROZEN.md').read_bytes())['base_weight_shards_sha256']
        require(backend.metadata['base_weight_shards_sha256'] == expected_shards, 'Evaluation base shards changed')
        def progress(done, total, _item):
            if done % 25 == 0 or done == total:
                print(f'{run_dir.name}: {done}/{total} generated', flush=True)
        if entry['engine_run_id'] is None:
            manifest = run(run_dir, dataset, splits, config, backend, max_items=0)
            registry.bind(train_root, entry, run_dir, manifest)
        manifest = run(run_dir, dataset, splits, config, backend, progress=progress)
    # Suppress previews for DEV too; complete sanity archives remain available to operator.
    with contextlib.redirect_stdout(io.StringIO()):
        metrics, _ = analyze(run_dir)
        if metrics['status'] == 'COMPLETE':
            from secondary_analysis.report_secondary import analyze as analyze_secondary
            c.verify_implementation(root)  # authenticate lazy imports before executing them
            try:
                analyze_secondary(run_dir)
            except Exception:
                print('Secondary analysis failed; primary unaffected; details remain sealed')
        archive = export(run_dir)
    status = old.sealed_status(run_dir, manifest, archive)
    write(run_dir.parent / (run_dir.name + '_status.json'), status)
    print('SEALED — completion/checksum/infrastructure only:', json.dumps(status))
    return 0 if metrics['status'] == 'COMPLETE' else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('evaluate', 'freeze-manifest', 'gate', 'dev-sanity'):
        sub = commands.add_parser(name)
        sub.add_argument('--root', type=Path, default=c.ROOT)
        sub.add_argument('--train-root', type=Path, required=name != 'evaluate')
        if name == 'evaluate':
            sub.add_argument('--split', choices=('dev', 'final_test'), required=True)
            sub.add_argument('--run-dir', type=Path, required=True)
            sub.add_argument('--adapter-dir', type=Path, required=True)
            sub.add_argument('--adapter-record', type=Path, required=True)
            sub.add_argument('--recover-stale-lock', action='store_true')
        if name == 'dev-sanity':
            sub.add_argument('--recover-stale-lock', action='store_true')
    args = parser.parse_args(argv)
    if args.command == 'evaluate':
        return run_evaluate(args)
    if args.command == 'dev-sanity':
        run_dev_sanity(args.train_root, args.root, recover=args.recover_stale_lock)
    elif args.command == 'gate':
        frozen = gate(args.root, args.train_root)
        load_reused_baseline(args.root, frozen)
        print('Gate verified:', frozen['S'], 'complete triplets;', len(frozen['adapters']) * 300, 'new generations')
    else:
        c.verify_implementation(args.root, full=True)
        frozen = freeze_manifest(args.train_root, args.root)
        path = args.root / FROZEN_PATH
        raw = '# Phase-3 adapters frozen\n\n```json\n' + json.dumps(frozen, indent=2) + '\n```\n'
        require(not path.exists() or path.read_text() == raw, 'Existing freeze differs; do not overwrite')
        path.write_text(raw)
        print(path, c.file_sha(path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
