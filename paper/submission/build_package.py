"""Build an allowlisted anonymous supplement; leaves frozen source artifacts unchanged."""
import csv, hashlib, io, json, re, shutil, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'paper/submission'
STAGE=ROOT/'tmp/submission_bundle/anon_supplement'
STAGE.mkdir(parents=True,exist_ok=True)
# Remove only prior generated files in the fixed staging directory.
for f in sorted(STAGE.rglob('*'),reverse=True):
    if f.is_file(): f.unlink()
    elif f.is_dir(): f.rmdir()
manifest=[]
def put(dest, data):
    p=STAGE/dest; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(data.encode() if isinstance(data,str) else data)
def copy(src,dest=None,anonymous=False):
    data=(ROOT/src).read_bytes(); orig=hashlib.sha256(data).hexdigest()
    if anonymous:
        s=data.decode()
        s=re.sub(r'/private/tmp/[^\"\n]+', '[temporary path withheld]', s)
        s=s.replace(str(ROOT), '[local project]')
        s=s.replace('/Users/divyanshraj/Major Project', '[local project]')
        s=re.sub(r'https?://github.com/Divyansh1128/Hinglish[^\s)`]*','[author repository withheld]',s)
        s=s.replace('github.com/Divyansh1128/Hinglish','[author repository withheld]')
        s=re.sub(r'/Users/[^\s`\"\']+','[local path withheld]',s)
        data=s.encode()
    put(dest or src,data)
    manifest.append({'source_path':src,'release_path':dest or src,'source_sha256':orig,'released_sha256':hashlib.sha256(data).hexdigest(),'anonymized':anonymous})
for f in ['LICENSE','DATA_LICENSE.md']: copy(f)
# Release actual implementation files, not notebooks with embedded test data or personal runtime output.
manifest_text=(ROOT/'phase2/IMPLEMENTATION_MANIFEST.md').read_text()
m=json.loads(manifest_text.split('```json\n',1)[1].split('```',1)[0])
for f in m['files']:
    if f.endswith('.py'): copy(f,'implementation/'+f)
for f in ['pilot_b/pilot_b_families.v2.json','pilot_original/cohort_dataset.json','pilot_original/cohort_splits.json','phase2/train_A.v2.json','phase2/train_B.v2.json','phase2/dev.v2.json']:
    copy(f,'data/'+f)
for f in ['pilot_b/PREREGISTRATION.md','pilot_b/FROZEN.md','pilot_original/PREREGISTRATION.md','pilot_original/FROZEN.md','phase2/PREREGISTRATION.md','phase2/IMPLEMENTATION_MANIFEST.md','phase2/ADAPTERS_FROZEN.md']:
    copy(f,'protocol/'+f,anonymous=True)
for cohort in ['pilot_b','pilot_original']:
    copy(f'results/{cohort}/SUMMARY.md',anonymous=True)
    for model in ['qwen3-4b','qwen3-8b','llama-3.2-3b']:
        for name in ['RESULTS.md','per_rendering.csv']:
            copy(f'results/{cohort}/{model}/{name}',anonymous=True)
for f in ['results/phase2/final_test/phase2_analysis.md','results/phase2/final_test/phase2_analysis.json','results/phase2/audit/final_audit.csv','results/phase2/audit/final_audit_summary.json']:
    copy(f,'phase2/'+Path(f).name,anonymous=True)
for f in ['results/pilot_b/audit/AUDIT_INSTRUCTIONS.md','pilot/annotation_draft_v2/R01/README.md','pilot/annotation_draft_v2/R01/stage1.html','pilot/annotation_draft_v2/R01/stage2.html']:
    copy(f,'instructions/'+Path(f).name,anonymous=True)
archive=ROOT/'results/phase2/final_test/Phase2_FinalTest_results.zip'
rows=[]; environments={}; latency=0.0
with zipfile.ZipFile(archive) as outer:
    names=sorted(n for n in outer.namelist() if n.endswith('_results.zip') and '/' not in n[len('final_test/'):])
    assert len(names)==10,names
    for n in names:
        run=Path(n).name.removesuffix('_results.zip')
        if run == 'base': run = 'unchanged'
        with zipfile.ZipFile(io.BytesIO(outer.read(n))) as z:
            for line in z.read('checksums.sha256').decode().splitlines():
                h, f=line.split('  ',1)
                assert hashlib.sha256(z.read(f)).hexdigest()==h,(run,f)
            predictions=list(csv.DictReader(io.StringIO(z.read('predictions.csv').decode())))
            assert len(predictions)==300
            for r in predictions:
                latency+=float(r['latency_seconds'])
                rows.append({k:r[k] for k in ['family_id','rendering_id','form','correct','invalid_reason','truncated','output_tokens','latency_seconds']}|{'checkpoint':run})
            # Model identity/configuration comes from the archive, not today's Hub.
            config=json.loads(z.read('experiment_config.json'))
            environments[run]={'config':config,'environment':json.loads(z.read('environment.json'))}
rows.sort(key=lambda r:(r['checkpoint'],r['family_id'],r['form']))
buf=io.StringIO(); writer=csv.DictWriter(buf,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
put('phase2/scored_outcomes.csv',buf.getvalue())
put('phase2/execution_metadata.json',json.dumps(environments,indent=2,sort_keys=True))
copy('paper/submission/verify_scores.py','verify_scores.py')
put('SOURCE_MANIFEST.json',json.dumps({'source_files':manifest,'final_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))
put('README.md',f'''# Anonymous review supplement

Updated 11 November 2026. This supports the pilot audit and completed controlled training follow-up. No model weights, credentials or personal reviewer submissions are distributed.

## Quick verification (CPU only, Python 3.9+; no packages)

From this folder run `python3 -B verify_scores.py`. It checks checksums, the 3,000-row coverage, all 30 strict checkpoint/form counts, the exact family bootstrap and the 331 final human-label rows. Expected primary: -4.333333 pp [-8.000000, -0.666667], Harm. This script is a post-study verification utility, not a replacement registered analysis or a rescoring rule.

## Contents and limits

- `phase2/scored_outcomes.csv`: derived stored strict outcomes, no question text, gold or generated answers. Each checkpoint has 100 matched families × E/R/C. Bootstrap families jointly across the three fixed seeds; do not treat 300 seed/family records as independent families.
- `phase2/phase2_analysis.*`: original registered final analysis, with separate strict/numeric endpoints, scope and interval limitations. `final_audit.*`: recorded human labels/summary for the ER/EC C failures only. No personal identities or handwritten submissions.
- `phase2/execution_metadata.json`: recorded immutable revisions, configurations and environments. It documents the actual stack; do not replace it with current package defaults.
- `data/`: pilot datasets and TRAIN/DEV. Final-test wording, raw final-test responses and weights are intentionally withheld pending camera-ready release. Therefore this bundle supports score-level reproduction but cannot independently rescore or regenerate FINAL_TEST.
- `implementation/`: unchanged source files from the implementation manifest, retained for inspection. Builders that need withheld FINAL_TEST data are not self-contained runnable training/evaluation packages here. No claim of full GPU reproduction from this review bundle.
- `protocol/`: plans, deviations, freezes; identifying repository link removed in release copies. Original and release hashes are distinguished in `SOURCE_MANIFEST.json`. Relative links referencing the private working tree may not resolve here.
- `instructions/`: original empty review interfaces/README and audit instructions (contains pilot reference material, not returned reviewer answers).
- `results/`: separately reported pilot cohorts. Their definitions/review differ; do not pool.

## Compute accounting

Measured committed FINAL_TEST generation latency totals {latency/3600:.3f} T4-hours over 3,000 outputs. Nine training runs × 60 updates at approximately 20 seconds/update imply about 3 T4-hours of updates. Neither includes all model loading, checkpointing, failed launches, DEV, screening or engineering work; a complete project-wide compute total is unavailable. These are component costs, not a full budget.

## Release/provenance

Code MIT; authored data CC BY 4.0. Upstream models remain under their own licenses (Qwen3 Apache 2.0; Llama 3.2 Community License). No upstream weights are redistributed. AI drafting/checking and human review are described in the paper; stored human labels are evidence records, not an independent certification of human activity. The protocol discloses pre-training CPU test access beyond the byte-hash-only rule. Results were not changed after the negative finding.
''')
# Explicit scan of every release byte; fail rather than silently publishing personal paths/names.
blocked=[rb'Divyansh',rb'Ayush Kumar',rb'Dinesh Udar',rb'Delhi Technological',rb'/Users/',rb'23/MC/',rb'hf_[A-Za-z0-9]{20,}',rb'gh[pousr]_[A-Za-z0-9]{20,}']
for f in STAGE.rglob('*'):
    if f.is_file():
        for pat in blocked:
            assert not re.search(pat,f.read_bytes(),re.I), (str(f.relative_to(STAGE)),pat)
checks=''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(STAGE).as_posix()}\n' for f in sorted(STAGE.rglob('*')) if f.is_file())
put('checksums.sha256',checks)
with zipfile.ZipFile(OUT/'supplementary_anonymous.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(STAGE.rglob('*')):
        if f.is_file():
            info=zipfile.ZipInfo('anon_supplement/'+f.relative_to(STAGE).as_posix(),(2026,11,11,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,f.read_bytes())
print('Built anonymous supplement:',len(list(STAGE.rglob('*'))),'entries; final-generation hours',round(latency/3600,3))
