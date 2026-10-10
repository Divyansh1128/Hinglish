"""Strict JSON input contract. Human attestations cannot be machine-certified."""
import hashlib
import json
import re
from collections import Counter
from fractions import Fraction

FORMS = ('E', 'R', 'C')
TOPICS = ('comparison_remaining', 'two_step_money', 'fractions_percentages',
          'ratios', 'rates_units', 'elementary_algebra')
DEMO_LABEL = 'DEMO — NOT RESEARCH EVIDENCE'
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z')
ROLES = ('PILOT_EVAL', 'SMOKE_TRAIN', 'RETIRED_DRAFT', 'CONFIRM_TRAIN', 'FINAL_TEST')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')).encode()).hexdigest()

def text(value, field):
    require(isinstance(value, str) and bool(value.strip()), f'Missing/nontext {field}')
    require(len(value) <= 20000, f'{field} exceeds size bound')
    return value

def ident(value, field):
    require(isinstance(value, str) and ID.fullmatch(value), f'Invalid {field}: use pseudonymous safe IDs')
    return value

def exact(value, field):
    require(isinstance(value, str) and len(value) <= 100 and
            re.fullmatch(r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:/[+-]?\d+)?', value),
            f'{field}: use an exact numeric string, not a float')
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f'Invalid {field}') from None

def validate_gold(gold):
    require(isinstance(gold, dict) and set(gold) == {
        'value', 'unit', 'aliases', 'conversions', 'unit_omission_allowed', 'rounding_rule'},
        'Gold fields: value/unit/aliases/conversions/unit_omission_allowed/rounding_rule')
    exact(gold['value'], 'gold.value')
    require(isinstance(gold['unit'], str), 'gold.unit must be text')
    require(isinstance(gold['unit_omission_allowed'], bool), 'Omission policy must be boolean')
    require(isinstance(gold['aliases'], list) and all(isinstance(x, str) and x.strip() for x in gold['aliases']),
            'Invalid unit aliases')
    require(isinstance(gold['conversions'], dict), 'Invalid conversions')
    for unit, factor in gold['conversions'].items():
        text(unit, 'conversion unit')
        require(exact(factor, 'conversion factor') > 0, 'Conversion factor must be positive')
    # All accepted values are exact; if a question asks for rounding, author its
    # rounded gold in advance. Unspecified approximate equivalence is unsupported.
    require(gold['rounding_rule'] == 'exact',
            'Test 1 accepts exact gold only; supply the requested rounded value as exact gold and document it in the reference solution')
    from .scorer_v1 import score_response
    score_response('FINAL: 0', gold)  # reject conflicting aliases/conversions

def identities(record):
    return {ident(record[k], k) for k in ('family_id', 'source_family_id', 'template_group_id')}

def validate(dataset, manifest, mode):
    require(mode in ('demo', 'reviewed'), 'Mode must be demo or reviewed')
    require(isinstance(dataset, dict) and dataset.get('schema_version') == 'test1-1', 'Dataset schema_version must be test1-1')
    text(dataset.get('version'), 'dataset version')
    text(dataset.get('borrowing_policy'), 'borrowing policy')
    require(dataset.get('kind') == mode, 'Dataset kind does not match execution mode')
    families = dataset.get('families')
    require(isinstance(families, list) and (len(families) == 30 if mode == 'reviewed' else 1 <= len(families) <= 6),
            'Reviewed pilot requires 30 families; demo requires 1–6')
    require(isinstance(manifest, dict) and manifest.get('schema_version') == 'test1-1', 'Split schema_version must be test1-1')
    text(manifest.get('version'), 'split version')
    require(manifest.get('kind') == mode, 'Manifest kind mismatch')
    expected_top = {'schema_version', 'version', 'kind', 'borrowing_policy', 'families'}
    require(set(dataset) == expected_top, 'Unexpected dataset fields; do not include personal details/credentials')
    require(set(manifest) == {'schema_version', 'version', 'kind', 'audit', 'development_exclusion_ids', *ROLES},
            'Unexpected/missing split fields')
    seen_ids, seen_text, render_ids = set(), set(), set()
    for family in families:
        require(set(family) == {'family_id', 'source_family_id', 'template_group_id', 'topic', 'split_role',
                'version', 'authoring_origin', 'provenance', 'source_license', 'reference_equation',
                'reference_solution_en', 'status', 'gold', 'forms', 'review'}, 'Unexpected/missing family fields')
        ids = identities(family)
        require(not ids & seen_ids, 'Repeated underlying family/source/template IDs')
        seen_ids |= ids
        require(family['topic'] in TOPICS, 'Unrecognized topic')
        require(family['split_role'] == ('PILOT_EVAL' if mode == 'reviewed' else 'DEMO'), 'Wrong split role')
        for field in ('version', 'authoring_origin', 'provenance', 'source_license', 'reference_equation', 'reference_solution_en'):
            text(family[field], field)
        require(family['status'] == ('ACCEPT' if mode == 'reviewed' else 'DEMO'), 'Human acceptance missing or demo status invalid')
        validate_gold(family['gold'])
        require(set(family['forms']) == set(FORMS), 'Exactly E/R/C forms required')
        for form, rendering in family['forms'].items():
            require(set(rendering) == {'rendering_id', 'text', 'creator_type', 'generation_or_edit_history', 'switching_roles'},
                    'Unexpected/missing rendering fields')
            rid = ident(rendering['rendering_id'], 'rendering_id')
            require(rid not in render_ids, 'Duplicate rendering ID')
            render_ids.add(rid)
            question = text(rendering['text'], 'question')
            normalized = ' '.join(question.casefold().split())
            require(normalized not in seen_text, 'Duplicate normalized rendering')
            seen_text.add(normalized)
            require(not re.search(r'<\|[^>]+\|>|/no_think|/think', question), 'Input contains model control markers')
            for field in ('creator_type', 'generation_or_edit_history'):
                text(rendering[field], field)
            require(isinstance(rendering['switching_roles'], list), 'switching_roles must be a list')
            if mode == 'reviewed' and form == 'C':
                require(bool(rendering['switching_roles']), 'C needs documented productive switching roles')
        review = family['review']
        require(set(review) == {'reviewers', 'adjudication'}, 'Unexpected/missing review fields')
        require(isinstance(review['reviewers'], list), 'Reviewers must be a list')
        if mode == 'demo':
            require(review == {'reviewers': [], 'adjudication': None}, 'Demo cannot include fabricated approvals')
            continue
        require(len(review['reviewers']) == 2, 'Two independent reviewers required')
        reviewers = set()
        for reviewer in review['reviewers']:
            require(set(reviewer) == {'reviewer_id', 'independent_solve_before_gold', 'forms'}, 'Invalid review schema')
            reviewers.add(ident(reviewer['reviewer_id'], 'reviewer_id'))
            require(reviewer['independent_solve_before_gold'] is True, 'Independent solve before gold required')
            require(set(reviewer['forms']) == set(FORMS), 'Both reviewers must review all forms')
            for form, assessment in reviewer['forms'].items():
                require(set(assessment) == {'text_sha256', 'equation', 'answer', 'unit', 'semantic_equivalence',
                    'ambiguity_resolved', 'classification', 'naturalness', 'readability', 'disposition'}, 'Invalid form review fields')
                require(assessment['text_sha256'] == hashlib.sha256(family['forms'][form]['text'].encode()).hexdigest(),
                        'Review hash does not match current rendering; re-review edits')
                text(assessment['equation'], 'independent equation')
                require(exact(assessment['answer'], 'independent answer') == exact(family['gold']['value'], 'gold') and
                        assessment['unit'] == family['gold']['unit'], 'Independent canonical answer/unit disagrees')
                require(assessment['semantic_equivalence'] is True and assessment['ambiguity_resolved'] is True,
                        'Unresolved equivalence/ambiguity review')
                require(assessment['classification'] == form and assessment['disposition'] == 'ACCEPT', 'Classification/acceptance required')
                for field in ('naturalness', 'readability'):
                    require(type(assessment[field]) is int and 4 <= assessment[field] <= 5, 'Review ratings must be 4–5')
        require(len(reviewers) == 2, 'Reviewers must be distinct')
        adjudication = review['adjudication']
        require(isinstance(adjudication, dict) and set(adjudication) == {'adjudicator_id', 'status', 'unresolved_issues', 'reviewed_at'},
                'Adjudication required')
        require(ident(adjudication['adjudicator_id'], 'adjudicator_id') not in reviewers, 'Adjudicator must be independent')
        require(adjudication['status'] == 'ACCEPT' and adjudication['unresolved_issues'] == 0, 'Unresolved adjudication')
        text(adjudication['reviewed_at'], 'review timestamp')
    if mode == 'reviewed':
        require(Counter(f['topic'] for f in families) == Counter({t: 5 for t in TOPICS}), 'Need five independent families per topic')
    role_ids = {}
    for role in ROLES:
        require(isinstance(manifest[role], list), f'{role} must be a list')
        ids = set()
        for record in manifest[role]:
            require(set(record) == {'family_id', 'source_family_id', 'template_group_id'}, 'Split records require three identity fields only')
            current = identities(record)
            require(not ids & current, f'Duplicate identity in {role}')
            ids |= current
        role_ids[role] = ids
    for i, role in enumerate(ROLES):
        for other in ROLES[i+1:]:
            require(not role_ids[role] & role_ids[other], f'Cross-split overlap {role}/{other}')
    expected = [{k: f[k] for k in ('family_id', 'source_family_id', 'template_group_id')} for f in families]
    if mode == 'reviewed':
        require(sorted(manifest['PILOT_EVAL'], key=digest) == sorted(expected, key=digest), 'PILOT_EVAL identities do not match data')
        audit = manifest['audit']
        require(isinstance(audit, dict) and set(audit) == {'approved', 'reviewer_id', 'unresolved_matches', 'audited_at'}, 'Invalid split audit')
        ident(audit['reviewer_id'], 'split reviewer ID')
        require(audit['approved'] is True and audit['unresolved_matches'] == 0, 'Completed human split audit required')
        text(audit['audited_at'], 'split audit timestamp')
    else:
        require(manifest['audit'] is None, 'Demo split audit must be null')
    require(isinstance(manifest['development_exclusion_ids'], list), 'Exclusion IDs must be a list')
    excluded = {ident(x, 'exclusion ID') for x in manifest['development_exclusion_ids']}
    development = seen_ids | role_ids['PILOT_EVAL'] | role_ids['SMOKE_TRAIN'] | role_ids['RETIRED_DRAFT']
    require(development <= excluded, 'Permanent development exclusions missing; include source/template descendants')
    require(not excluded & (role_ids['CONFIRM_TRAIN'] | role_ids['FINAL_TEST']), 'Confirmatory contamination')
    require(not seen_ids & (role_ids['SMOKE_TRAIN'] | role_ids['RETIRED_DRAFT'] | role_ids['CONFIRM_TRAIN'] | role_ids['FINAL_TEST']),
            'Dataset overlaps nonpilot split')
    return {'families': len(families), 'prompts': 3 * len(families),
            'status': DEMO_LABEL if mode == 'demo' else 'REVIEW METADATA PASSED — human judgments not machine verified',
            'dataset_sha256': digest(dataset), 'split_sha256': digest(manifest)}

def records(dataset):
    return [dict(family_id=f['family_id'], topic=f['topic'], form=form,
                 rendering_id=f['forms'][form]['rendering_id'], input_text=f['forms'][form]['text'], gold=f['gold'])
            for f in dataset['families'] for form in FORMS]
