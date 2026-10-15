import copy
import csv
import hashlib
from pathlib import Path
import random
import tempfile
import unittest
import zipfile
from hinglish_pilot.data import DEMO_LABEL, FORMS, TOPICS, validate
from hinglish_pilot.engine import MODELS, FakeBackend, attempts, default_config, read, recover_lock, run, validate_config, write
from hinglish_pilot.report import analyze, export, paired, wilson
from hinglish_pilot.scorer_v1 import score_response
ROOT=Path(__file__).resolve().parents[1]

def fixture(): return read(ROOT/'fixtures/demo_dataset.json'),read(ROOT/'fixtures/demo_splits.json')
def config():
    c=default_config();c['model_revision']=c['tokenizer_revision']='0'*40
    return c

def reviewed_fixture():
    # In-memory contract fixtures are never released as human-reviewed data.
    d,s=fixture();rows=[]
    for i in range(30):
        f=copy.deepcopy(d['families'][0]);fid=f'contract-{i}'
        f.update(family_id=fid,source_family_id=fid+'-source',template_group_id=fid+'-template',topic=TOPICS[i//5],split_role='PILOT_EVAL',status='ACCEPT')
        for form in FORMS: f['forms'][form].update(rendering_id=fid+'-'+form,text=f'{form} contract fixture {i}')
        f['review']={'reviewers':[{'reviewer_id':f'fixture-reviewer-{j}','independent_solve_before_gold':True,'forms':{form:{'text_sha256':hashlib.sha256(f['forms'][form]['text'].encode()).hexdigest(),'equation':'2+3','answer':'5','unit':f['gold']['unit'],'semantic_equivalence':True,'ambiguity_resolved':True,'classification':form,'naturalness':4,'readability':4,'disposition':'ACCEPT'} for form in FORMS}} for j in range(2)],'adjudication':{'adjudicator_id':'fixture-adjudicator','status':'ACCEPT','unresolved_issues':0,'reviewed_at':'fixture'}}
        rows.append(f)
    d.update(kind='reviewed',families=rows)
    s.update(kind='reviewed',audit={'approved':True,'reviewer_id':'fixture-auditor','unresolved_matches':0,'audited_at':'fixture'},PILOT_EVAL=[{k:f[k] for k in ('family_id','source_family_id','template_group_id')} for f in rows],development_exclusion_ids=[f[k] for f in rows for k in ('family_id','source_family_id','template_group_id')])
    return d,s

class Contracts(unittest.TestCase):
    def test_model_registry(self):
        for model_id in MODELS:
            config = default_config('demo', model_id)
            config.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
            validate_config(config)
        self.assertEqual(default_config()['model_id'], 'Qwen/Qwen3-4B')
        config = default_config('demo', 'some/unlisted-model')
        config.update(model_revision='0' * 40, tokenizer_revision='0' * 40)
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_valid_contracts(self):
        self.assertEqual(validate(*fixture(),'demo')['prompts'],6)
        self.assertEqual(validate(*reviewed_fixture(),'reviewed')['prompts'],90)
    def test_review_split_and_numeric_rejections(self):
        mutations=[lambda d,s:d['families'][0].update(status='DRAFT'),lambda d,s:d['families'][0]['review']['reviewers'].pop(),lambda d,s:d['families'][0]['forms']['R'].update(text='edited'),lambda d,s:d['families'][0]['review']['reviewers'][0]['forms']['C'].update(naturalness=3),lambda d,s:s['audit'].update(approved=False),lambda d,s:s['development_exclusion_ids'].pop(),lambda d,s:s['FINAL_TEST'].append(s['PILOT_EVAL'][0]),lambda d,s:d['families'][1].update(template_group_id=d['families'][0]['template_group_id']),lambda d,s:d['families'][0]['gold'].update(value=.5),lambda d,s:d.update(api_key='forbidden'),lambda d,s:d['families'][0]['review']['reviewers'][1].update(reviewer_id='fixture-reviewer-0'),lambda d,s:d['families'][0]['gold'].update(conversions={'m':'0'})]
        for change in mutations:
            d,s=reviewed_fixture();change(d,s)
            with self.subTest(change=change),self.assertRaises(ValueError):validate(d,s,'reviewed')
    def test_templates_fail(self):
        with self.assertRaises(ValueError):validate(read(ROOT/'templates/pilot_dataset.template.json'),read(ROOT/'templates/split_manifest.template.json'),'reviewed')
    def test_demo_cannot_claim_review(self):
        d,s=fixture();d['families'][0]['review']['reviewers']=[{'reviewer_id':'fabricated'}]
        with self.assertRaises(ValueError):validate(d,s,'demo')
    def test_scoring(self):
        g=fixture()[0]['families'][1]['gold']
        for r in ('FINAL: .5','FINAL: 2/4','FINAL: 50%'):self.assertTrue(score_response(r,g)['correct'])
        for r in ('Intermediate .5','FINAL: .5\nFINAL: .5','FINAL: .5 or .6','I cannot answer\nFINAL: .5'):self.assertFalse(score_response(r,g)['correct'])
        self.assertEqual(score_response('FINAL: .5',g,True)['invalid_reason'],'truncated')
        metre=dict(g,value='1',unit='m',aliases=['metre'],conversions={'cm':'1/100'},unit_omission_allowed=False)
        self.assertTrue(score_response('FINAL: 100 cm',metre)['correct']);self.assertFalse(score_response('FINAL: 100 kg',metre)['correct'])
    def test_count_fixture_unit_metadata_and_fraction_suffix_policy(self):
        count, fraction = fixture()[0]['families']
        self.assertEqual(count['gold']['unit'],'counters')
        for answer in ('FINAL: 5 counters','FINAL: 5 counters.','FINAL: 5 tukde.','FINAL: 5'):
            self.assertTrue(score_response(answer,count['gold'])['correct'])
        self.assertFalse(score_response('FINAL: 5 metres',count['gold'])['correct'])
        self.assertTrue(score_response('FINAL: 1/2',fraction['gold'])['correct'])
        for answer in ('FINAL: 1/2 whole.','FINAL: 1/2 fraction.','FINAL: 1/2 part.'):
            self.assertEqual(score_response(answer,fraction['gold'])['invalid_reason'],'invalid_unit')

class Execution(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'demo-run';self.d,self.s=fixture();self.c=config()
    def execute(self,backend=None,**kwargs):return run(self.root,self.d,self.s,self.c,backend or FakeBackend(),**kwargs)
    def test_complete_export(self):
        self.assertEqual(self.execute()['status'],'COMPLETE');m,_=analyze(self.root)
        self.assertEqual(m['completed'],6);self.assertEqual(m['accuracy']['E']['denominator'],2);self.assertEqual(m['paired']['E-C']['families'],2)
        self.assertIn(DEMO_LABEL,(self.root/'summary.md').read_text())
        with zipfile.ZipFile(export(self.root)) as z:
            for line in z.read('checksums.sha256').decode().splitlines():
                sha,name=line.split('  ',1);self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),sha)
            self.assertIn('manual_audit.csv',z.namelist());self.assertNotIn('RUNNING.lock',z.namelist())
    def test_resume_and_changed_inputs(self):
        self.assertEqual(self.execute(max_items=2)['completed'],2);self.assertIsNone(analyze(self.root)[0]['accuracy'])
        self.execute();self.execute();self.assertEqual(len(attempts(self.root)),6)
        self.c['seed']+=1
        with self.assertRaises(ValueError):self.execute()
        self.c['seed']-=1;self.d['families'][0]['forms']['E']['text']+=' edited'
        with self.assertRaises(ValueError):self.execute()
    def test_invalid_success_not_retried(self):
        class Invalid(FakeBackend):
            def generate(self,*a):return dict(super().generate(*a),raw_response='FINAL: 999',truncated=True)
        self.execute(Invalid());self.execute(Invalid());self.assertEqual(len(attempts(self.root)),6)
        m,_=analyze(self.root);self.assertEqual(m['accuracy']['E']['correct'],0);self.assertEqual(m['failure_diagnostics']['C']['truncated'],2)
    def test_transient_retry(self):
        class Transient(FakeBackend):
            def __init__(self):self.failed=False
            def generate(self,*a):
                if not self.failed:self.failed=True;raise RuntimeError('secret exception text')
                return super().generate(*a)
        self.execute(Transient());self.assertEqual(len(attempts(self.root)),7);self.assertEqual(analyze(self.root)[0]['completed'],6)
        self.assertNotIn('secret exception text',(self.root/'generation_attempts.jsonl').read_text())
    def test_persistent_failures(self):
        class Broken(FakeBackend):
            def generate(self,*a):raise RuntimeError()
        self.execute(Broken());self.execute(Broken());self.assertEqual(len(attempts(self.root)),12)
        m,_=analyze(self.root);self.assertEqual(m['unresolved'],6);self.assertIsNone(m['accuracy']);self.assertIsNone(m['paired']);export(self.root)
    def test_interrupt_and_lock(self):
        class Interrupted(FakeBackend):
            def generate(self,*a):raise KeyboardInterrupt()
        self.assertEqual(self.execute(Interrupted())['status'],'INCOMPLETE');self.assertFalse((self.root/'RUNNING.lock').exists());self.execute()
        (self.root/'RUNNING.lock').write_text('stale')
        with self.assertRaises(ValueError):self.execute()
        with self.assertRaises(ValueError):recover_lock(self.root)
        recover_lock(self.root,True);self.execute();self.assertEqual(len(attempts(self.root)),7)
    def test_oom_stops(self):
        class OutOfMemoryError(Exception):pass
        class OOM(FakeBackend):
            def generate(self,*a):raise OutOfMemoryError()
        self.assertEqual(self.execute(OOM())['attempts'],1);self.assertEqual(attempts(self.root)[0]['error_code'],'out_of_memory')
    def test_preflight_length(self):
        self.d['families'][0]['forms']['E']['text']='too long '*1800
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(len(attempts(self.root)),0)
    def test_reviewed_fake_rejected(self):
        d,s=reviewed_fixture();c=config();c['mode']='reviewed'
        with self.assertRaises(ValueError):run(self.root,d,s,c,FakeBackend())
    def test_corrupt_journal(self):
        self.execute();p=next((self.root/'journal').glob('*.json'));row=read(p);row['correct']=False;write(p,row)
        with self.assertRaises(ValueError):analyze(self.root)
    def test_secret_export_block(self):
        self.execute()
        for secret in ('hf_'+'A'*25,'person@example.com','sk-'+'x'*32):
            write(self.root/'environment.json',{'credential':secret})
            with self.assertRaises(ValueError):export(self.root)
    def test_secret_in_model_text_blocked_without_tampering(self):
        class SecretOutput(FakeBackend):
            def generate(self,*a):
                return dict(super().generate(*a),raw_response='hf_'+'A'*25)
        self.execute(SecretOutput())
        with self.assertRaisesRegex(ValueError,'Credential/email-like'):export(self.root)
    def test_killed_inflight_attempt_retained_on_resume(self):
        class Killed(FakeBackend):
            def generate(self,*a):raise SystemExit('simulated runtime loss')
        with self.assertRaises(SystemExit):self.execute(Killed())
        self.assertEqual(attempts(self.root)[0]['status'],'in_progress')
        self.execute()
        self.assertEqual(len(attempts(self.root)),7)
        self.assertEqual(analyze(self.root)[0]['completed'],6)
    def test_manual_overlay(self):
        self.execute();analyze(self.root);original=(self.root/'predictions.csv').read_bytes()
        with (self.root/'manual_audit.csv').open(newline='') as f:rows=list(csv.DictReader(f));fields=list(rows[0])
        rows[0].update(manual_correct='false',reviewer_id='audit-1',reason='Fixture disagreement',reviewed_at='fixture')
        overlay=self.root.parent/'overlay.csv'
        with overlay.open('w',newline='') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
        m,dest=analyze(self.root,overlay);self.assertEqual(m['manually_reviewed'],1);self.assertNotEqual(dest,self.root)
        self.assertEqual((self.root/'predictions.csv').read_bytes(),original)
        with zipfile.ZipFile(export(self.root)) as z:self.assertTrue(any(n.startswith('analysis_revisions/') for n in z.namelist()))
    def test_family_pairing(self):
        v=[{'E':True,'C':False},{'E':False,'C':True},{'E':True,'C':True}]
        p=paired(v,'E','C',random.Random(1),10000);self.assertEqual(p['difference'],0);self.assertEqual(p['families'],3)
        self.assertEqual(p['a_correct_b_wrong'],1);self.assertEqual(p['a_wrong_b_correct'],1)
        self.assertEqual(p,paired(v,'E','C',random.Random(1),10000));self.assertAlmostEqual(wilson(0,30)[0],0)

class NotebookTests(unittest.TestCase):
    def test_cells_and_full_demo_execution(self):
        nb=read(ROOT/'Hinglish_Math_Test1_Pilot_Colab.ipynb');self.assertEqual(nb['nbformat'],4)
        with tempfile.TemporaryDirectory() as directory:
            ns={'__name__':'__main__'}
            for i,cell in enumerate(nb['cells']):
                if cell['cell_type']!='code':continue
                source=cell['source'];compile(source,f'cell-{i}','exec')
                source=source.replace("PACKAGE = Path('/content/hinglish_test1') if Path('/content').exists() else Path.cwd() / 'hinglish_test1'",f'PACKAGE = Path({directory!r})')
                exec(compile(source,f'cell-{i}','exec'),ns)
            self.assertTrue(ns['RESULTS_ZIP'].is_file());self.assertEqual(ns['METRICS']['status'],'COMPLETE')

if __name__=='__main__':unittest.main()
