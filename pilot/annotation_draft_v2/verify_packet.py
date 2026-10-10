"""Model-free checks; no claim of human validity. No returned reviews modified."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import hashlib
import json
import random
import re
import subprocess
import sys
import tempfile
import zipfile
import ast

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'test1_pilot'))
from hinglish_pilot.data import validate, validate_gold, TOPICS
from hinglish_pilot.scorer_v1 import score_response

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def run():
    for path in HERE.glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    data=load(HERE/'coordinator/pilot_dataset.DRAFT.json')
    splits=load(HERE/'coordinator/split_manifest.DRAFT.json')
    families=data['families']
    assert len(families)==30
    assert Counter(f['topic'] for f in families)==Counter({t:5 for t in TOPICS})
    ids=[f['family_id'] for f in families]
    assert ids==[f'PIL{n:03d}' for n in range(1,31)]
    assert all(f['status']=='DRAFT' and f['authoring_origin']=='AI_DRAFT' and f['review']=={'reviewers':[],'adjudication':None} for f in families)
    assert splits['audit']['approved'] is False
    keys=('family_id','source_family_id','template_group_id')
    identities=[f[k] for f in families for k in keys]
    assert len(identities)==len(set(identities))==90
    assert set(identities)<=set(splits['development_exclusion_ids'])
    assert not splits['CONFIRM_TRAIN'] and not splits['FINAL_TEST']
    assert len(splits['SMOKE_TRAIN'])==1  # format-only fixture, not a QLoRA dataset
    render_ids=[r['rendering_id'] for f in families for r in f['forms'].values()]
    texts=[r['text'] for f in families for r in f['forms'].values()]
    assert len(set(render_ids))==len(set(texts))==90
    packet=(ROOT/'pilot_review_packet.md').read_text()
    for f in load(HERE.parent/'annotation_draft_v1/coordinator/pilot_dataset.DRAFT.json')['families'][:5]:
        section=packet.split('### '+f['family_id']+':',1)[1].split('\n### ',1)[0]
        for form in ('E','R','C'):
            assert f['forms'][form]['text']==re.search(rf'^- {form}: (.+)$',section,re.M).group(1)
    prior=load(HERE.parent/'annotation_draft_v1/coordinator/pilot_dataset.DRAFT.json')
    repairs=load(HERE/'repairs.json')
    log=load(HERE/'coordinator/repair_log.json')
    assert data['version']=='pilot-draft-v2'
    assert len(log['changes'])==len(repairs)==8
    for name,digest in log['v1_file_sha256'].items():
        assert hashlib.sha256((HERE.parent/'annotation_draft_v1'/name).read_bytes()).hexdigest()==digest,name
    changed=[]
    for old,new in zip(prior['families'],families):
        for key in ('family_id','source_family_id','template_group_id','gold','reference_equation','reference_solution_en','topic'):
            assert old[key]==new[key],(old['family_id'],key)
        for form in ('E','R','C'):
            key=old['family_id']+'-'+form
            a,b=old['forms'][form],new['forms'][form]
            if key in repairs:
                assert b['text']==repairs[key]['text'] and b['text']!=a['text']
                assert b['rendering_id']==key+'-v2'
                assert new['version']=='v2'
                entry=next(x for x in log['changes'] if x['family_id']==old['family_id'] and x['form']==form)
                assert entry['old_text']==a['text'] and entry['new_text']==b['text']
                assert entry['old_text_sha256']==hashlib.sha256(a['text'].encode()).hexdigest()
                assert entry['new_text_sha256']==hashlib.sha256(b['text'].encode()).hexdigest()
                changed.append(key)
            else:assert a==b,(key,'unplanned change')
    assert len(changed)==8
    conversion_tests=0
    # Independent physical unit map catches inconsistent factor directions/values.
    scales={'L':Fraction(1),'mL':Fraction(1,1000),'m':Fraction(1),'cm':Fraction(1,100),
            'km':Fraction(1000),'kg':Fraction(1),'g':Fraction(1,1000),
            'minute':Fraction(1),'h':Fraction(60)}
    conventional={'l':'L','litre':'L','litres':'L','millilitre':'mL','millilitres':'mL',
                  'metre':'m','metres':'m','centimetre':'cm','centimetres':'cm',
                  'gram':'g','grams':'g','hour':'h','hours':'h','minutes':'minute','min':'minute'}
    for f in families:
        gold=f['gold']
        validate_gold(gold)
        assert score_response(f['reference_solution_en'],gold)['correct'],f['family_id']
        assert score_response('FINAL: '+gold['value'],gold)['correct']
        for alias in gold['aliases']:
            assert score_response('FINAL: '+gold['value']+' '+alias,gold)['correct'],(f['family_id'],alias)
        for unit,factor in gold['conversions'].items():
            expected=scales[conventional.get(unit,unit)]/scales[gold['unit']]
            assert Fraction(factor)==expected,(f['family_id'],unit,factor,expected)
            given=Fraction(gold['value'])/Fraction(factor)
            assert score_response('FINAL: '+str(given)+' '+unit,gold)['correct']
            conversion_tests+=1
        assert not score_response('FINAL: '+gold['value']+' bananas',gold)['correct']
        assert not score_response('FINAL: '+gold['value'],gold,truncated=True)['correct']
    assert Fraction(families[-1]['gold']['value'])**2==49 and Fraction(families[-1]['gold']['value'])>0
    try:
        validate(data,splits,'reviewed')
    except ValueError as error:
        assert str(error)=='Human acceptance missing or demo status invalid',str(error)
        rejection=str(error)
    else:
        raise AssertionError('Draft must fail the unchanged reviewed validator')
    orders=load(HERE/'coordinator/randomization.json')
    assert orders['R01']['stage1']!=orders['R02']['stage1']
    js_checks=0
    for role in ('R01','R02'):
        expected=[(f['family_id'],form) for f in families for form in ('E','R','C')]
        random.Random(orders[role]['stage1_seed']).shuffle(expected)
        assert orders[role]['stage1']==[list(x) for x in expected]
        assert sorted(orders[role]['stage1'])==sorted(orders[role]['stage2'])
        with zipfile.ZipFile(HERE/f'{role}_review_packet.zip') as z:
            assert set(z.namelist())=={f'{role}/README.md',f'{role}/stage1.html',f'{role}/stage2.html'}
            for filename in (f'{role}/stage1.html',f'{role}/stage2.html'):
                page=z.read(filename).decode()
                assert z.read(filename)==(HERE/filename).read_bytes()
                script=re.search(r'<script>\n(.*?)\n</script>',page,re.S).group(1)
                raw=re.search(r'let packet = (.*?);\nfunction fill',script,re.S).group(1)
                payload=json.loads(raw)
                assert len(payload['rows'])==90
                assert payload['independent_solve_before_gold'] is None
                assert all(not r['independent_answer'] and not r['independent_equation'] and
                           r['naturalness'] is None and r['disposition']=='PENDING' for r in payload['rows'])
                assert not {'reference_equation','reference_solution_en','gold','value'} & set(payload)
                assert not any('gold' in r or 'reference_solution_en' in r for r in payload['rows'])
                assert 'FINAL:' not in page and 'fetch(' not in script and 'http' not in script
                if payload['stage']==2:
                    assert 'data-key="independent_answer"' not in page
                    assert 'data-key="independent_equation"' not in page
                    assert 'Import your completed stage1 submission first.' in script
                with tempfile.TemporaryDirectory() as temp:
                    p=Path(temp)/'check.js';p.write_text(script)
                    subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
                js_checks+=1
    adjud=load(HERE/'A01/adjudication.PENDING.json')
    assert len(adjud['families'])==30 and not adjud['role_assignment_confirmed']
    assert all(f['status']=='PENDING' and f['unresolved_issues'] is None and not f['final_answer'] for f in adjud['families'])
    with zipfile.ZipFile(HERE/'A01_adjudication_packet.zip') as z:
        assert set(z.namelist())=={'A01/README.md','A01/answer_key.md','A01/adjudication.PENDING.json'}
    logic=subprocess.run(['node',str(HERE/'test_form_imports.js')],check=True,capture_output=True,text=True)
    checksum_count=0
    for line in (HERE/'checksums.sha256').read_text().splitlines():
        checksum,filename=line.split('  ',1)
        assert hashlib.sha256((HERE/filename).read_bytes()).hexdigest()==checksum,filename
        checksum_count+=1
    result=dict(status='PASS — SOFTWARE CHECKS ONLY; NO HUMAN VALIDATION',families=30,renderings=90,
                topics=dict(Counter(f['topic'] for f in families)),all_reference_finals_score_correct=True,
                exact_unit_conversion_checks=conversion_tests,reviewer_javascript_syntax_checks=js_checks,
                archived_v1_first_five_texts_preserved=True, versioned_rendering_repairs=8, changed_families=6, v1_files_unchanged=True,reviewer_archives_have_no_gold_fields=True,
                draft_research_execution_rejection=rejection,verified_checksums=checksum_count,
                form_import_export_logic_checks=logic.stdout.strip(),
                limitations=['No human reviews, equivalence or independence certification.',
                             'JavaScript syntax checks do not establish browser workflow behavior.',
                             'No research model evaluation was performed on these drafts.'])
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    run()
