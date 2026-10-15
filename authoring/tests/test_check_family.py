import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

AUTHORING = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AUTHORING))
import check_family as cf  # noqa: E402


def make_family(fid='AUT001', value='18', equation='3*(10-4)=18'):
    fam = json.loads((AUTHORING / 'family_template.json').read_text(encoding='utf-8'))[0]
    fam.update(family_id=fid, source_family_id=f'{fid}-src', template_group_id=f'{fid}-grp',
               topic='two_step_money', split_role='DEV', provenance='Written from scratch for tests.',
               reference_equation=equation, reference_solution_en='Each costs 10-4 = 6; 3*6 = 18.')
    fam['gold'].update(value=value, unit='INR', aliases=['rupees'])
    texts = {'E': f'{fid}: a pen costs 10 rupees with a 4 rupee discount; what do 3 such pens cost?',
             'R': f'{fid}: ek pen 10 rupaye ka hai aur 4 rupaye ki chhoot hai; aise 3 pen kitne ke honge?',
             'C': f'{fid}: ek pen 10 rupaye ka hai with a 4 rupee discount; 3 pen ka total kitna hoga?'}
    for form, text in texts.items():
        fam['forms'][form].update(rendering_id=f'{fid}-{form}', text=text, creator_type='HUMAN',
                                  generation_or_edit_history='authored')
    fam['forms']['C']['switching_roles'] = ['discount']
    return fam


class EquationTests(unittest.TestCase):
    def test_exact_decimal_and_fraction(self):
        self.assertEqual(cf.safe_eval('0.1+0.2'), cf.Fraction(3, 10))
        self.assertEqual(cf.safe_eval('-(7/2)*2'), -7)
        cf.check_equation('0.1+0.2=0.3', '0.3')
        cf.check_equation('9*x-14=58; x=(58+14)/9=8', '8')
        cf.check_equation('10/3', '10/3')

    def test_inexact_rejected(self):
        with self.assertRaises(ValueError):
            cf.check_equation('10/3=3.33', '3.33')
        with self.assertRaises(ValueError):
            cf.check_equation('3*(10-4)', '17')

    def test_unsafe_rejected(self):
        for expr in ("__import__('os').system('true')", '2**10', '7//2', 'x+1',
                     '(1).__class__', '1e3', '[1][0]', '', '1/0'):
            with self.subTest(expr=expr), self.assertRaises(cf.UnsafeExpression):
                cf.safe_eval(expr)


class FamilyTests(unittest.TestCase):
    def test_template_structure_valid_but_content_incomplete(self):
        template = json.loads((AUTHORING / 'family_template.json').read_text(encoding='utf-8'))
        self.assertIsInstance(template, list)
        self.assertEqual(len(template), 1)
        self.assertEqual(template[0]['status'], 'DRAFT')
        self.assertEqual(cf.check_structure(template[0]), [])
        self.assertTrue(cf.check_content(template[0]))

    def test_valid_family_passes(self):
        errors, flags = cf.check_families([make_family()], [])
        self.assertEqual((errors, flags), ([], []))

    def test_wrong_gold_equation_reported(self):
        errors, _ = cf.check_families([make_family(value='17')], [])
        self.assertTrue(any('does not equal gold' in e for e in errors))

    def test_duplicate_text_and_ids(self):
        a, b = make_family('AUT001'), make_family('AUT002')
        b['forms']['E']['text'] = '  ' + a['forms']['E']['text'].upper() + ' '
        errors, _ = cf.check_families([a, b], [])
        self.assertTrue(any('duplicate text' in e for e in errors))
        errors, _ = cf.check_families([a, copy.deepcopy(a)], [])
        self.assertTrue(any('repeated family' in e for e in errors))

    def test_near_duplicate_flagged(self):
        fam = make_family()
        ref = [('ref:X:E', fam['forms']['E']['text'].replace('3 such', 'three such'))]
        _, flags = cf.check_families([fam], ref)
        self.assertTrue(any('ref:X:E' in f for f in flags))
        _, flags = cf.check_families([fam], [('ref:Y:E', 'A train travels 120 km in 2 hours.')])
        self.assertEqual(flags, [])

    def test_real_reference_corpus_loads(self):
        refs = cf.load_reference_texts()
        self.assertGreater(len(refs), 90)
        self.assertTrue(all(isinstance(t, str) for _, t in refs))

    def test_cli_never_prints_pilot_gold(self):
        pilot = json.loads(cf.PILOT_PATH.read_text(encoding='utf-8'))
        copied = pilot['families'][0]
        fam = make_family()
        fam['forms']['E']['text'] = copied['forms']['E']['text']
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'f.json'
            path.write_text(json.dumps([fam]), encoding='utf-8')
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cf.main([str(path)])
        text = out.getvalue()
        self.assertEqual(code, 1)
        self.assertIn('NEAR-DUP', text)
        self.assertNotIn(copied['gold']['value'] + ' ', text.replace('Jaccard', ''))
        self.assertNotIn(copied['reference_equation'], text)
        self.assertNotIn(copied['reference_solution_en'], text)


if __name__ == '__main__':
    unittest.main()
