"""Build a NEW unaccepted v2 packet from maintained v1 logic and explicit repairs.
Never rebuild over an existing generated dataset or human submissions.
"""
from pathlib import Path
import importlib.util
import hashlib
import json
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V1=HERE.parent/'annotation_draft_v1'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if (HERE/'coordinator/pilot_dataset.DRAFT.json').exists():
        raise SystemExit('Refusing to overwrite existing v2 inputs. Preserve reviews; build a separately versioned release for further edits.')
    before={str(p.relative_to(V1)):digest(p) for p in V1.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    spec=importlib.util.spec_from_file_location('v1_packet',V1/'build_packet.py')
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    base.OUT=HERE;base.VERSION='pilot-draft-v2'
    edits=json.loads((HERE/'repairs.json').read_text())
    original_build=base.build_family
    changes=[]
    def repaired_family(seed):
        f=original_build(seed)
        changed=False
        for form,r in f['forms'].items():
            key=f['family_id']+'-'+form
            if key not in edits:continue
            edit=edits[key];old=r['text'];assert old!=edit['text']
            changes.append(dict(family_id=f['family_id'],form=form,old_rendering_id=r['rendering_id'],new_rendering_id=key+'-v2',old_text=old,new_text=edit['text'],old_text_sha256=base.sha(old),new_text_sha256=base.sha(edit['text']),reason=edit['reason'],editor_type='AI_DRAFT',human_review='PENDING'))
            r.update(text=edit['text'],rendering_id=key+'-v2',generation_or_edit_history=r['generation_or_edit_history']+' AI pre-review repair 2026-10-10; v1 preserved; human re-review pending.')
            changed=True
        if changed:
            f['version']='v2'
            f['provenance']+=' Versioned AI wording repair from pilot-draft-v1; family/source/template identity retained; no human validation.'
        return f
    base.build_family=repaired_family
    base.main()
    assert len(changes)==8
    base.write(HERE/'coordinator/repair_log.json',dict(status='AI_DRAFT_REPAIRS_NOT_HUMAN_VALIDATION',parent_dataset_version='pilot-draft-v1',dataset_version=base.VERSION,changes=changes,v1_file_sha256=before,unchanged_gold_and_units=True,ancestry_resolved=False))
    readme=(HERE/'README.md').read_text().replace('draft annotation package v1','draft annotation package v2').replace('All 30 families and 90 E/R/C texts are **DRAFT**, AI-authored and awaiting two independent bilingual reviews and adjudication. PIL001–005 retain the earlier illustrative wording verbatim; the other 25 are new candidates.','All 30 families and 90 E/R/C texts remain **DRAFT**, AI-authored and awaiting two independent bilingual reviews and adjudication. Eight renderings in six families were repaired from v1: PIL004 E/R/C, PIL006 R, PIL008 C, PIL016 C, PIL025 C and PIL026 C. PIL004 is now a versioned revision of an original illustrative example; v1 remains unchanged. Gold, units and source/template identities are preserved.').replace('annotation_draft_v1','annotation_draft_v2')
    readme+='\n## Version and exposure instructions\n\nUse only these v2 packets for a new review round. Existing v1 submissions remain evidence for v1; do not rename or force-import them. The forms reject mismatched dataset versions. Re-review changed triplets and preserve original responses. The coordinator repair log and AI reports contain proposed answers/interpretation hints and must stay away from reviewers before independent solving. Record actual prior exposure; changing version does not restore blinding.\n\nOptional PIL009/PIL019 terminology changes were deferred to humans. Family ancestry questions, including PIL002/PIL010, PIL011/PIL012 and PIL005/PIL021, remain unresolved; 30 IDs are not proof of independence. Borrowing policy remains proposed. No family is ACCEPT.\n\nThe builder reuses maintained v1 generation logic plus repairs.json; it refuses to overwrite existing generated v2 data. Do not delete submissions to bypass this guard. Use a new version for further changes.\n'
    base.write(HERE/'README.md',readme)
    for role in ('R01','R02','A01'):
        p=HERE/role/'README.md'
        base.write(p,p.read_text()+'\nPacket version: pilot-draft-v2. Do not combine with v1 submissions. Disclose any prior answer exposure; AI repairs are not human approval.\n')
        target=HERE/(f'{role}_review_packet.zip' if role!='A01' else 'A01_adjudication_packet.zip')
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted((HERE/role).iterdir()):z.write(p,f'{role}/{p.name}')
    assert before=={str(p.relative_to(V1)):digest(p) for p in V1.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    hashes={str(p.relative_to(HERE)):digest(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in ('checksums.sha256','verification.json')}
    base.write(HERE/'checksums.sha256',''.join(f'{v}  {k}\n' for k,v in hashes.items()))

if __name__=='__main__':main()
