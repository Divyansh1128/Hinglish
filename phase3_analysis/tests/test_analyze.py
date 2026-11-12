"""Pure synthetic Phase-2-shaped inputs exercise the unchanged Phase-3 statistical core."""
import copy
import unittest
from unittest import mock
from phase2_analysis import analyze as core
from phase3_analysis import analyze as wrapper, compare
from t4_smoke import phase3_contract as c


def study_fixture(n=100, seeds=(11, 22, 33)):
    families = [dict(family_id=f'SYN{i:03d}', gold=dict(value='2', unit='', aliases=[], unit_omission_allowed=True),
                     provenance='synthetic operation words', forms={}) for i in range(n)]
    runs = {}
    for arm, seed in [(core.UNCHANGED, None)] + [(a, s) for a in core.ARMS for s in seeds]:
        rows = {}
        for i, f in enumerate(families):
            for form in core.FORMS:
                correct = (i + (seed or 0) + len(arm) + ord(form)) % 5 != 0
                rid = f['family_id'] + '_' + form
                rows[rid] = dict(family_id=f['family_id'], form=form, correct=correct,
                    raw_response='Working.\nFINAL: 2' if correct else 'FINAL: 3', truncated=False,
                    invalid_reason=None, output_tokens=i % 13 + 4, input_tokens=10, latency_seconds=.1)
        runs[(arm, seed)] = dict(selected=rows, complete=True, unresolved=0, expected=3*n, completed=3*n,
            path='synthetic/' + arm + str(seed), kind='synthetic', config=dict(adapter=None, model_revision=core.QWEN_REVISION),
            manifest=dict(run_id='synthetic-' + arm + str(seed), dataset_sha256='a'*64, config_sha256='b'*64),
            archive_sha256='c'*64, attempts=3*n)
    return dict(role='DEV', families=families, seeds=list(seeds), runs=runs, dataset_sha256='d'*64,
                model_id=core.QWEN_ID, warnings=['synthetic only'], labels=len(seeds) == 3,
                analysis_type='synthetic Phase-2-shaped fixture', freeze=None, baseline=None)


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = study_fixture()
        cls.expected = core.analyze(cls.study, ceiling_proxy_k=24)
        cls.actual = wrapper.statistical_core(cls.study, ceiling_proxy_k=24)

    def test_exact_core_output_equality(self):
        self.assertEqual(self.expected, self.actual)

    def test_shared_matrix_hash(self):
        self.assertEqual(self.actual['bootstrap']['matrix_sha256'], wrapper.MATRIX_SHA)
        self.assertEqual(self.actual['bootstrap']['seed'], 101)
        self.assertEqual(self.actual['bootstrap']['resamples'], 10000)

    def test_labels_english_flags_and_degeneracy_unchanged(self):
        self.assertEqual(self.actual['endpoints'], self.expected['endpoints'])
        for endpoint in core.ENDPOINTS:
            self.assertIn('retention_flags', self.actual['endpoints'][endpoint])
        self.assertEqual(core.decision_label(0, 0, True), core.DEGENERATE)

    def test_changed_core_hash_refused(self):
        with mock.patch.object(wrapper, 'CORE_SHA', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'core changed'):
                wrapper.statistical_core(self.study, 24)

    def test_unsealing_requires_all_archives(self):
        with __import__('tempfile').TemporaryDirectory() as tmp, \
             mock.patch.object(wrapper.ev, 'gate', return_value=dict(adapters=[dict(arm='EC', seed=11)])):
            with self.assertRaisesRegex(ValueError, 'missing required archive'):
                wrapper.assemble(tmp, tmp, tmp)

    def test_report_changes_only_title_and_preserves_phase2_attribution(self):
        source = '# Phase-2 pre-registered analysis — FINAL_TEST\nPhase-2 baseline; unchanged Phase-2 statistical method.\n'
        with mock.patch.object(core, 'markdown', return_value=source):
            output = wrapper.report_markdown({})
        self.assertEqual(output.split('\n', 1)[1], source.split('\n', 1)[1])
        self.assertTrue(output.startswith('# Phase-3 pre-specified follow-up'))

    def test_analysis_calls_study_registry_before_loading_outcomes(self):
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evaluations = root / 'final_test'
            evaluations.mkdir()
            (evaluations / 'Phase3_Train_EC-s11_results.zip').write_bytes(b'synthetic')
            with mock.patch.object(wrapper.ev, 'gate', return_value=dict(adapters=[dict(arm='EC', seed=11)])), \
                 mock.patch.object(c, 'file_sha', return_value='f'*64), \
                 mock.patch.object(wrapper.ev.registry, 'reconcile', side_effect=ValueError('extra history')), \
                 mock.patch.object(core, 'load_run') as load:
                with self.assertRaisesRegex(ValueError, 'extra history'):
                    wrapper.assemble(root, root / 'train', evaluations)
                load.assert_not_called()

    def test_primary_output_cannot_be_overwritten(self):
        with __import__('tempfile').TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'once'):
                wrapper.run_analysis(tmp, tmp, tmp, tmp)

    def test_descriptive_comparison_same_inputs_zero_change(self):
        result = compare.compare_studies(self.study, self.study)
        self.assertEqual(len(result['rows']), 9)
        self.assertTrue(all(row['change_pp'] == 0 for row in result['rows']))
        self.assertIn('DESCRIPTIVE ONLY', result['label'])
        self.assertIn('iqr', result['rows'][0]['phase3']['output_tokens'])
        self.assertFalse(any('decision' in row for row in result['rows']))

    def test_descriptive_compares_phase_specific_seed_means(self):
        other = study_fixture(seeds=(44, 22, 33))
        result = compare.compare_studies(other, self.study)
        self.assertIn('no seed pairing', result['label'])
        self.assertEqual(len(result['rows']), 9)

    def test_descriptive_family_mismatch_refused(self):
        other = copy.deepcopy(self.study)
        other['families'][0]['family_id'] = 'foreign'
        with self.assertRaisesRegex(ValueError, 'family mismatch'):
            compare.compare_studies(other, self.study)

class ReportIntegrationTests(unittest.TestCase):
    def test_phase3_final_report_uses_unchanged_core_and_provenance(self):
        import json
        import tempfile
        from pathlib import Path
        study = study_fixture()
        study.update(role='FINAL_TEST', baseline=dict(k=24, sha256='a'*64, run_id='synthetic-dev', generations=120),
                     freeze=dict(path='synthetic/ADAPTERS_FROZEN.md', sha256='b'*64,
                       retained_seeds=[dict(slot=s, seed=s) for s in (11,22,33)], S=3, confirmatory=True,
                       implementation_manifest=dict(path='synthetic/IMPLEMENTATION_MANIFEST.md', sha256='c'*64),
                       baseline_dev_results_zip_sha256='a'*64, baseline_dev_results=dict(generations=120)))
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(wrapper, 'assemble', return_value=(study, {'fixture': {'journal_sha256': 'd'*64}})):
            out = Path(tmp) / 'new-report'
            result = wrapper.run_analysis(tmp, tmp, tmp, out)
            saved = json.loads((out / 'phase3_analysis.json').read_text())
            markdown = (out / 'phase3_analysis.md').read_text()
            self.assertEqual(saved['bootstrap']['matrix_sha256'], wrapper.MATRIX_SHA)
            self.assertTrue(saved['preregistration'].startswith('phase3/'))
            self.assertIn('# Phase-3', markdown)
            self.assertIn('reused test set', markdown)
            self.assertEqual(result['endpoints'], core.analyze(study)['endpoints'])


if __name__ == '__main__':
    unittest.main()
