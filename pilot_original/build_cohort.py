"""Build the original-pilot cohort (decision D036) in the engine's `pilot_adjudicated` mode.

Reads only the raw sources:
  pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json   (texts and gold, unchanged)
  pilot/reviews_v2_round2/R0{1,2}_stage{1,2}_responses.json       (official round-2 files)
  pilot/reviews_v2_round2/A01_worksheet_returned.csv               (adjudication)

Cohort = families A01 marked ACCEPT with no proposed repair (expected: 24). Reviewer judgments are
copied as entered; `answer_matches_gold` is derived (see FROZEN.md) and is allowed to be False:
A01's adjudication resolves disagreements. Fails loudly on any unexpected count or mismatch.

Usage from the repository root: python3 -B pilot_original/build_cohort.py
"""
import csv
import hashlib
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'pilot_original'
DRAFT = ROOT / 'pilot' / 'annotation_draft_v2' / 'coordinator' / 'pilot_dataset.DRAFT.json'
REVIEWS = ROOT / 'pilot' / 'reviews_v2_round2'
STAGE_FILES = {r: (REVIEWS / f'{r}_stage1_responses.json', REVIEWS / f'{r}_stage2_responses.json') for r in ('R01', 'R02')}
WORKSHEET = REVIEWS / 'A01_worksheet_returned.csv'
ADJUDICATOR = 'A01'
ADJUDICATED_AT = '2026-10-26'  # date the A01 worksheet was returned (the worksheet carries no timestamp)
FORMS = ('E', 'R', 'C')
EXPECTED = {'families': 30, 'cohort': 24, 'exclude': {'PIL010'},
            'revise': {'PIL009', 'PIL015', 'PIL019', 'PIL020', 'PIL024'}}
STATUS_COL = 'A01_status (ACCEPT/REVISE/EXCLUDE)'
REPAIR_COL = 'A01_proposed_text_repairs (form: new text)'
GOLD_COL = 'A01_gold_and_units_ok (yes/no)'
NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:\s*/\s*[+-]?\d+)?')


def fail(message):
    raise SystemExit('build_cohort: ' + message)


def check(condition, message):
    if not condition:
        fail(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def answer_matches_gold(raw_answer, gold_value):
    """True iff the last number written in the raw answer equals the gold value exactly (units ignored)."""
    numbers = NUMBER.findall(raw_answer.replace(',', ''))
    if not numbers:
        return False
    try:
        return Fraction(re.sub(r'\s+', '', numbers[-1])) == Fraction(gold_value)
    except (ValueError, ZeroDivisionError):
        return False


def load_reviewer(reviewer_id, texts):
    stage1_path, stage2_path = STAGE_FILES[reviewer_id]
    stage1_raw, stage2_raw = stage1_path.read_bytes(), stage2_path.read_bytes()
    stage1, stage2 = json.loads(stage1_raw), json.loads(stage2_raw)
    for stage, number in ((stage1, 1), (stage2, 2)):
        check(stage['reviewer_id'] == reviewer_id and stage['stage'] == number, f'{reviewer_id} stage{number} header mismatch')
        check(stage['dataset_version'] == 'pilot-draft-v2', f'{reviewer_id} stage{number} dataset version')
        check(len(stage['rows']) == 90, f'{reviewer_id} stage{number}: expected 90 rows')
    check(stage2['stage1_submission_sha256'] == sha(stage1_raw), f'{reviewer_id}: stage2 does not cite this stage1 file')
    check(stage1['independent_solve_before_gold'] is True and stage2['independent_solve_before_gold'] is True,
          f'{reviewer_id}: independence attestation missing')
    first = {row['rendering_id']: row for row in stage1['rows']}
    rows = {}
    for row in stage2['rows']:
        rid = row['rendering_id']
        check(rid in texts and rid not in rows, f'{reviewer_id}: unknown or repeated rendering {rid}')
        check(first[rid]['independent_answer'] == row['independent_answer'] and
              first[rid]['independent_unit'] == row['independent_unit'], f'{reviewer_id}: stage1 answer changed for {rid}')
        check(row['text_sha256'] == sha(texts[rid].encode()), f'{reviewer_id}: text hash mismatch for {rid}')
        rows[rid] = row
    check(set(rows) == set(texts), f'{reviewer_id}: renderings do not cover the dataset')
    provenance = sorted(rid for rid, row in rows.items() if row.get('_annotation_provenance'))
    return rows, provenance


def form_entry(row, gold_value):
    checks = row['semantic_checks']
    check(isinstance(checks, dict) and all(type(v) is bool for v in checks.values()), f'semantic checks for {row["rendering_id"]}')
    provenance = row.get('_annotation_provenance') or {}
    source = 'ai_prefill_unverified' if provenance.get('source') == 'AI prefill suggestion' and provenance.get('human_verified') is False else 'human'
    check(not provenance or source == 'ai_prefill_unverified', f'unknown provenance for {row["rendering_id"]}')
    return {'judgment_source': source, 'text_sha256': row['text_sha256'], 'raw_answer': row['independent_answer'], 'raw_unit': row['independent_unit'],
            'answer_matches_gold': answer_matches_gold(row['independent_answer'], gold_value),
            'disposition': row['disposition'], 'classification': row['classification'],
            'naturalness': row['naturalness'], 'readability': row['readability'], 'ambiguity_flag': row['ambiguity_flag'],
            'failed_semantic_checks': [name for name, ok in checks.items() if ok is False], 'notes': row['issue_notes']}


def build():
    draft_raw = DRAFT.read_bytes()
    draft = json.loads(draft_raw)
    families = draft['families']
    check(len(families) == EXPECTED['families'], 'expected 30 draft families')
    texts = {f['forms'][form]['rendering_id']: f['forms'][form]['text'] for f in families for form in FORMS}
    check(len(texts) == 90, 'expected 90 renderings')
    reviewers = {}
    provenance = {}
    for reviewer_id in ('R01', 'R02'):
        reviewers[reviewer_id], provenance[reviewer_id] = load_reviewer(reviewer_id, texts)

    worksheet_raw = WORKSHEET.read_bytes()
    worksheet = list(csv.DictReader(worksheet_raw.decode('utf-8-sig').splitlines()))
    check(len(worksheet) == 30 and len({r['family_id'] for r in worksheet}) == 30, 'A01 worksheet must have 30 distinct families')
    by_id = {f['family_id']: f for f in families}
    check(set(by_id) == {r['family_id'] for r in worksheet}, 'A01 worksheet families differ from the draft')
    statuses = {}
    for row in worksheet:
        family = by_id[row['family_id']]
        for form in FORMS:
            check(row[f'{form}_text'] == family['forms'][form]['text'], f'A01 worksheet text differs for {row["family_id"]}-{form}')
        statuses[row['family_id']] = (row[STATUS_COL].strip(), row[REPAIR_COL].strip())
    cohort_ids = sorted(fid for fid, (status, repair) in statuses.items() if status == 'ACCEPT' and not repair)
    excluded = {fid for fid, (status, _) in statuses.items() if status == 'EXCLUDE'}
    revised = {fid for fid, (status, _) in statuses.items() if status == 'REVISE'}
    check(len(cohort_ids) == EXPECTED['cohort'], f'expected 24 cohort families, got {len(cohort_ids)}')
    check(excluded == EXPECTED['exclude'] and revised == EXPECTED['revise'], f'unexpected exclusions {excluded} / revisions {revised}')
    check(not any(repair for fid, (status, repair) in statuses.items() if status == 'ACCEPT'), 'an ACCEPT row proposes a repair')

    converted = []
    for family in families:
        if family['family_id'] not in cohort_ids:
            continue
        row = next(r for r in worksheet if r['family_id'] == family['family_id'])
        check(row[GOLD_COL].strip().lower() == 'yes', f'A01 did not confirm gold for {family["family_id"]}')
        check(Fraction(row['A01_final_answer'].strip()) == Fraction(family['gold']['value']), f'A01 answer differs from gold: {family["family_id"]}')
        unit = row['A01_final_unit'].strip()
        check((unit == '(none)' and family['gold']['unit'] == '') or unit == family['gold']['unit'], f'A01 unit differs: {family["family_id"]}')
        review = {'reviewers': [{'reviewer_id': rid, 'independent': True,
                                 'forms': {form: form_entry(reviewers[rid][family['forms'][form]['rendering_id']], family['gold']['value'])
                                           for form in FORMS}} for rid in ('R01', 'R02')],
                  'adjudication': {'adjudicator_id': ADJUDICATOR, 'status': 'ACCEPT', 'gold_confirmed': True,
                                   'reason': row['A01_decision_reason'].strip(), 'reviewed_at': ADJUDICATED_AT}}
        converted.append(dict(family, status='ACCEPT', review=review))
    check(len(converted) == 24, 'conversion lost families')

    version = 'pilot_original-v1-' + sha(draft_raw)[:12]
    dataset = dict(schema_version='test1-1', version=version, kind='pilot_adjudicated',
                   borrowing_policy=draft['borrowing_policy'], families=converted)
    identity = lambda f: {k: f[k] for k in ('family_id', 'source_family_id', 'template_group_id')}
    all_ids = sorted({f[k] for f in families for k in ('family_id', 'source_family_id', 'template_group_id')})
    check(len(all_ids) == 90, 'expected 90 distinct pilot identities')
    splits = dict(schema_version='test1-1', version=version, kind='pilot_adjudicated', audit=None,
                  PILOT_EVAL=[identity(f) for f in converted], SMOKE_TRAIN=[], RETIRED_DRAFT=[], CONFIRM_TRAIN=[], FINAL_TEST=[],
                  development_exclusion_ids=all_ids)
    sources = {DRAFT: draft_raw, WORKSHEET: worksheet_raw}
    for paths in STAGE_FILES.values():
        for path in paths:
            sources[path] = path.read_bytes()
    return dataset, splits, sources, provenance


def mismatches(dataset):
    return sorted(f"{f['family_id']}-{form} {r['reviewer_id']}: raw answer {r['forms'][form]['raw_answer']!r} (gold {f['gold']['value']})"
                  for f in dataset['families'] for r in f['review']['reviewers'] for form in FORMS
                  if not r['forms'][form]['answer_matches_gold'])


def main():
    dataset, splits, sources, provenance = build()
    sys.path.insert(0, str(ROOT / 'test1_pilot'))
    from hinglish_pilot.data import validate
    summary = validate(dataset, splits, 'pilot_adjudicated')
    check(summary['prompts'] == 72, 'expected 72 prompts')
    outputs = {}
    for name, value in (('cohort_dataset.json', dataset), ('cohort_splits.json', splits)):
        data = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
        (OUT / name).write_bytes(data)
        outputs[name] = sha(data)
    cohort = [f['family_id'] for f in dataset['families']]
    cohort_prov = {r: [x for x in provenance[r] if x.split('-')[0] in cohort] for r in provenance}
    lines = ['# Original-pilot cohort — frozen (decision D036)', '',
             'Built by `python3 -B pilot_original/build_cohort.py` from the raw sources only. Texts, gold, units and IDs are '
             'unchanged from the v2 draft; only `status` (DRAFT → ACCEPT) and `review` (round-2 R01/R02 + A01) are filled in.', '',
             f'Engine mode `pilot_adjudicated`; {summary["families"]} families × E/R/C = {summary["prompts"]} prompts.', '',
             '## Outputs', '', '| File | SHA-256 |', '|---|---|']
    lines += [f'| pilot_original/{name} | {digest} |' for name, digest in outputs.items()]
    lines += ['', f'Engine digests (canonical JSON): dataset `{summary["dataset_sha256"]}`, splits `{summary["split_sha256"]}`.', '',
              '## Sources', '', '| File | SHA-256 |', '|---|---|']
    lines += [f'| {path.relative_to(ROOT)} | {sha(data)} |' for path, data in sources.items()]
    lines += ['', '## Cohort', '', ', '.join(cohort), '',
              'Out: PIL010 (A01 EXCLUDE, near-duplicate of PIL002); PIL009, PIL015, PIL019, PIL020, PIL024 (A01 REVISE; the repairs '
              'lack an independent re-review). All 30 pilot identities stay in `development_exclusion_ids`; no descendant IDs exist in the sources.', '',
              '## Review metadata', '',
              '- Reviewer entries copy the round-2 stage-2 rows as entered (answers are the stage-1 independent answers, verified unchanged). '
              'Ratings, dispositions, classifications, ambiguity flags and notes are not corrected, even where they conflict with each other or with gold.',
              '- `answer_matches_gold` is derived: True iff the last number written in the raw answer equals the gold value exactly (units ignored). '
              'False entries (resolved by A01, who confirmed the gold for every cohort family):', '']
    lines += [f'  - {m}' for m in mismatches(dataset)]
    lines += ['- `failed_semantic_checks` lists the semantic checks the reviewer marked false.',
              f'- `adjudication.reviewed_at` = {ADJUDICATED_AT}, the date the A01 worksheet was returned (it has no timestamp); '
              '`reason` is A01\'s decision reason verbatim.',
              '- No separate human split audit is claimed (`audit: null`).', '',
              '## Provenance warning', '',
              'The official `R01_stage2_responses.json` carries a field `_annotation_provenance = {"source": "AI prefill suggestion", '
              '"human_verified": false}` on ' + f'{len(provenance["R01"])}/90 stage-2 rows ({sum(map(len, cohort_prov.values()))} of the cohort\'s 72 R01 renderings). '
              'The project\'s annotation form does not write this field. It is not carried into the engine schema; the affected cohort renderings are:', '',
              ', '.join(cohort_prov['R01']) or 'none', '',
              f'R02 rows with this field: {len(provenance["R02"])}.', '']
    (OUT / 'FROZEN.md').write_text('\n'.join(lines))
    print(json.dumps(dict(summary, files=outputs, cohort=cohort), indent=1))


if __name__ == '__main__':
    main()
