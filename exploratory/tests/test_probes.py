import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gloss_probe  # noqa: E402
import self_translate  # noqa: E402


def form(rid, text):
    return {'rendering_id': rid, 'text': text, 'creator_type': 'SYNTHETIC',
            'generation_or_edit_history': 'test', 'switching_roles': []}


def family(fid, e, r, c, gold):
    return {'family_id': fid, 'gold': {'value': gold, 'unit': ''},
            'forms': {'E': form(fid + '-E', e), 'R': form(fid + '-R', r), 'C': form(fid + '-C', c)}}


DATASET = {'schema_version': 'test1-1', 'version': 'syn-v1', 'kind': 'demo', 'families': [
    family('f1', 'Divide 10 by 2.', '10 ko 2 se Bhaag karo, phir jod do 3.', '10 ko 2 se divide karo.', '5'),
    family('f2', 'What fraction is 1 of 2?', '1, 2 ka kaun sa bhinn hai? bhaagna mat.', '1, 2 ka kaun sa fraction hai?', '1/2'),
    family('f3', 'Add 2 and 3.', '2 aur 3 ko milao.', '2 and 3 add karo.', '5'),
]}


class SelfTranslateTests(unittest.TestCase):
    def setUp(self):
        self.ds = copy.deepcopy(DATASET)

    def translations(self):
        return {r['rendering_id']: 'EN: ' + r['rendering_id'] for r in self_translate.build_requests(self.ds)}

    def test_prompt_frozen(self):
        self.assertEqual(self_translate.SELF_TRANSLATE_PROMPT_V1,
                         'Translate the following math word problem into English. Preserve every number, '
                         'quantity and relation exactly. Output only the translation.')

    def test_request_count_and_no_e(self):
        reqs = self_translate.build_requests(self.ds)
        self.assertEqual(len(reqs), 2 * len(self.ds['families']))
        self.assertEqual({r['form'] for r in reqs}, {'R', 'C'})
        e_texts = [f['forms']['E']['text'] for f in self.ds['families']]
        for r in reqs:
            self.assertTrue(r['prompt'].startswith(self_translate.SELF_TRANSLATE_PROMPT_V1))
            self.assertFalse(any(e in r['prompt'] for e in e_texts))
            self.assertFalse(r['rendering_id'].endswith('-E'))

    def test_second_stage_ids_gold_and_text(self):
        tr = self.translations()
        out = self_translate.second_stage_dataset(self.ds, tr)
        self.assertEqual(self.ds, DATASET)  # input untouched
        for src, new in zip(self.ds['families'], out['families']):
            self.assertEqual(new['gold'], src['gold'])
            self.assertEqual(new['forms']['E'], src['forms']['E'])
            for f in ('R', 'C'):
                rid = src['forms'][f]['rendering_id']
                self.assertEqual(new['forms'][f]['rendering_id'], rid + '-ST')
                self.assertEqual(new['forms'][f]['source_rendering_id'], rid)
                self.assertEqual(new['forms'][f]['text'], tr[rid])
                self.assertNotEqual(new['forms'][f]['text'], src['forms']['E']['text'])

    def test_missing_translation_has_no_e_fallback(self):
        tr = self.translations()
        tr.pop('f1-R')
        with self.assertRaises(ValueError):
            self_translate.second_stage_dataset(self.ds, tr)
        tr = self.translations()
        tr['f1-E'] = 'x'
        with self.assertRaises(ValueError):
            self_translate.second_stage_dataset(self.ds, tr)
        tr = self.translations()
        tr['f1-C'] = '  '
        with self.assertRaises(ValueError):
            self_translate.second_stage_dataset(self.ds, tr)

    def test_identical_to_e_is_flagged(self):
        tr = self.translations()
        tr['f1-R'] = 'Divide 10 by 2.'
        out = self_translate.second_stage_dataset(self.ds, tr)
        self.assertTrue(out['families'][0]['forms']['R']['translation_equals_E_text'])
        self.assertFalse(out['families'][0]['forms']['C']['translation_equals_E_text'])


class GlossProbeTests(unittest.TestCase):
    def setUp(self):
        self.ds = copy.deepcopy(DATASET)
        self.v = gloss_probe.gloss_variants(self.ds, gloss_probe.DEFAULT_LEXICON)

    def test_default_lexicon(self):
        self.assertEqual(gloss_probe.LEXICON_STATUS, 'UNCONFIRMED')
        self.assertEqual(gloss_probe.DEFAULT_LEXICON, {
            'bhaag': 'divide', 'bhinn': 'fraction', 'guna': 'multiply', 'jod': 'add',
            'ghata': 'subtract', 'anupat': 'ratio', 'pratishat': 'percent'})

    def test_ids_and_counts(self):
        self.assertEqual(sorted(x['rendering_id'] for x in self.v),
                         ['f1-R-GL-bhaag', 'f1-R-GL-jod', 'f2-R-GL-bhinn'])

    def test_no_match_no_variant(self):
        self.assertFalse([x for x in self.v if x['family_id'] == 'f3'])
        self.assertEqual(gloss_probe.gloss_variants(self.ds, {'xyz': 'q'}), [])

    def test_one_word_at_a_time_and_case(self):
        by = {x['rendering_id']: x for x in self.v}
        self.assertEqual(by['f1-R-GL-bhaag']['text'], '10 ko 2 se Divide karo, phir jod do 3.')
        self.assertEqual(by['f1-R-GL-jod']['text'], '10 ko 2 se Bhaag karo, phir add do 3.')
        self.assertEqual(by['f1-R-GL-bhaag']['matched_surfaces'], ['Bhaag'])
        self.assertEqual(by['f1-R-GL-bhaag']['source_text'], DATASET['families'][0]['forms']['R']['text'])

    def test_whole_word_only(self):
        # 'bhaagna' is an inflected form: NOT matched by 'bhaag' (documented behaviour).
        f2 = [x for x in self.v if x['family_id'] == 'f2']
        self.assertEqual([x['word'] for x in f2], ['bhinn'])
        self.assertIn('bhaagna', f2[0]['text'])
        self.assertEqual(f2[0]['text'], '1, 2 ka kaun sa fraction hai? bhaagna mat.')
        # It is matched only when listed explicitly.
        only = gloss_probe.gloss_variants(self.ds, {'bhaagna': 'dividing'})
        self.assertEqual([x['rendering_id'] for x in only], ['f2-R-GL-bhaagna'])

    def test_gold_unchanged_and_only_r(self):
        for x in self.v:
            fam = next(f for f in DATASET['families'] if f['family_id'] == x['family_id'])
            self.assertEqual(x['gold'], fam['gold'])
            self.assertEqual(x['source_rendering_id'], fam['forms']['R']['rendering_id'])
        self.assertEqual(self.ds, DATASET)


if __name__ == '__main__':
    unittest.main()
