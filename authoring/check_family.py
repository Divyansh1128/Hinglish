#!/usr/bin/env python3
"""Validate a JSON list of Phase-2 authored families (standard library only).

Usage: python3 -B authoring/check_family.py families.json

Checks: test1-1 family structure, gold schema (test1_pilot validate_gold),
reference_equation exactness via a safe AST evaluator, duplicate texts, and
character 5-gram Jaccard near-duplicates against the pilot draft texts and FMT2
fixtures. Reports name IDs and similarity only; pilot gold is never printed.
"""
import ast
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'test1_pilot'))
from hinglish_pilot.data import FORMS, TOPICS, ID, exact, validate_gold  # noqa: E402

PILOT_PATH = ROOT / 'pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json'
FMT2_PATH = ROOT / 'secondary_analysis/format_fixtures.json'
NEAR_DUP_THRESHOLD = 0.5
FAMILY_FIELDS = {'family_id', 'source_family_id', 'template_group_id', 'topic', 'split_role',
                 'version', 'authoring_origin', 'provenance', 'source_license', 'reference_equation',
                 'reference_solution_en', 'status', 'gold', 'forms', 'review'}
RENDER_FIELDS = {'rendering_id', 'text', 'creator_type', 'generation_or_edit_history', 'switching_roles'}
GOLD_FIELDS = {'value', 'unit', 'aliases', 'conversions', 'unit_omission_allowed', 'rounding_rule'}
STATUSES = ('DRAFT', 'ACCEPT')
NUMBER = re.compile(r'\d+(?:\.\d+)?|\.\d+')
ARITH_CHARS = re.compile(r'[0-9.+\-*/() ]+\Z')
VARIABLE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')


class UnsafeExpression(ValueError):
    pass


def safe_eval(expr):
    """Exactly evaluate + - * / and parentheses over integer/decimal literals."""
    expr = expr.strip()
    if not expr or not ARITH_CHARS.fullmatch(expr) or '**' in expr or '//' in expr:
        raise UnsafeExpression(f'unsupported expression: {expr!r}')
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError:
        raise UnsafeExpression(f'unparsable expression: {expr!r}') from None

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            literal = ast.get_source_segment(expr, node)
            if literal is None or not NUMBER.fullmatch(literal):
                raise UnsafeExpression(f'bad literal in {expr!r}')
            return Fraction(literal)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = ev(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise UnsafeExpression('division by zero')
            return left / right
        raise UnsafeExpression(f'disallowed syntax {type(node).__name__} in {expr!r}')

    return ev(tree)


def check_equation(equation, gold_value):
    """Last ';'-statement: optional bare variable, then '='-separated arithmetic
    segments; each must evaluate exactly to gold. Earlier statements are free text."""
    gold = exact(gold_value, 'gold.value')
    statement = equation.split(';')[-1]
    segments = [s.strip() for s in statement.split('=')]
    if segments and VARIABLE.fullmatch(segments[0]):
        segments = segments[1:]
    if not segments or not all(segments):
        raise ValueError('reference_equation: final statement has no arithmetic segment')
    for segment in segments:
        if safe_eval(segment) != gold:
            raise ValueError(f'reference_equation segment {segment!r} does not equal gold exactly')


def normalize(text):
    return ' '.join(text.casefold().split())


def grams(text, n=5):
    t = normalize(text)
    return {t[i:i + n] for i in range(max(1, len(t) - n + 1))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def check_structure(family):
    """Field-set structure only (blank values allowed)."""
    errors = []
    if not isinstance(family, dict) or set(family) != FAMILY_FIELDS:
        return ['Unexpected/missing family fields']
    if not isinstance(family['gold'], dict) or set(family['gold']) != GOLD_FIELDS:
        errors.append('Unexpected/missing gold fields')
    forms = family['forms']
    if not isinstance(forms, dict) or set(forms) != set(FORMS):
        errors.append('Exactly E/R/C forms required')
    else:
        for form, rendering in forms.items():
            if not isinstance(rendering, dict) or set(rendering) != RENDER_FIELDS:
                errors.append(f'{form}: unexpected/missing rendering fields')
    if not isinstance(family['review'], dict) or set(family['review']) != {'reviewers', 'adjudication'}:
        errors.append('Unexpected/missing review fields')
    return errors


def check_content(family):
    errors = []
    for key in ('family_id', 'source_family_id', 'template_group_id'):
        if not (isinstance(family[key], str) and ID.fullmatch(family[key])):
            errors.append(f'Invalid {key}')
    if family['topic'] not in TOPICS:
        errors.append('Unrecognized topic')
    if family['status'] not in STATUSES:
        errors.append('status must be DRAFT or ACCEPT')
    for key in ('version', 'authoring_origin', 'provenance', 'source_license', 'reference_solution_en'):
        if not (isinstance(family[key], str) and family[key].strip()):
            errors.append(f'Missing {key}')
    try:
        validate_gold(family['gold'])
    except Exception as exc:  # report, never echo pilot data
        errors.append(f'gold: {exc}')
    else:
        try:
            check_equation(family['reference_equation'], family['gold']['value'])
        except (ValueError, AttributeError) as exc:
            errors.append(str(exc))
    for form in FORMS:
        r = family['forms'][form]
        if not (isinstance(r['rendering_id'], str) and ID.fullmatch(r['rendering_id'])):
            errors.append(f'{form}: invalid rendering_id')
        if not (isinstance(r['text'], str) and r['text'].strip()):
            errors.append(f'{form}: missing text')
        if not isinstance(r['switching_roles'], list):
            errors.append(f'{form}: switching_roles must be a list')
    if isinstance(family['forms']['C']['switching_roles'], list) and not family['forms']['C']['switching_roles']:
        errors.append('C: document productive switching_roles')
    return errors


def load_reference_texts(paths=(PILOT_PATH, FMT2_PATH)):
    """[(label, text)] from family renderings; gold and equations are not retained."""
    refs = []
    for path in paths:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        for fam in data.get('families', []):
            for form, r in fam.get('forms', {}).items():
                if isinstance(r, dict) and isinstance(r.get('text'), str):
                    refs.append((f'{Path(path).name}:{fam.get("family_id")}:{form}', r['text']))
    return refs


def check_families(families, references):
    """Return (errors, flags) lists of strings."""
    errors, flags = [], []
    if not isinstance(families, list) or not families:
        return ['Input must be a non-empty JSON list of families'], []
    ref_grams = [(label, grams(t)) for label, t in references]
    seen_ids, seen_texts = set(), {}
    for i, family in enumerate(families):
        name = family.get('family_id') if isinstance(family, dict) else None
        tag = f'[{i}:{name}]'
        structural = check_structure(family)
        if structural:
            errors += [f'{tag} {e}' for e in structural]
            continue
        errors += [f'{tag} {e}' for e in check_content(family)]
        ids = {family[k] for k in ('family_id', 'source_family_id', 'template_group_id')}
        if ids & seen_ids:
            errors.append(f'{tag} repeated family/source/template ID')
        seen_ids |= ids
        for form in FORMS:
            text = family['forms'][form]['text']
            if not isinstance(text, str) or not text.strip():
                continue
            key = normalize(text)
            if key in seen_texts:
                errors.append(f'{tag} {form}: duplicate text of {seen_texts[key]}')
            else:
                seen_texts[key] = f'{tag} {form}'
            g = grams(text)
            for label, rg in ref_grams:
                score = jaccard(g, rg)
                if score >= NEAR_DUP_THRESHOLD:
                    flags.append(f'{tag} {form}: near-duplicate of {label} (5-gram Jaccard {score:.2f})')
    return errors, flags


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print('usage: check_family.py families.json', file=sys.stderr)
        return 2
    families = json.loads(Path(argv[0]).read_text(encoding='utf-8'))
    errors, flags = check_families(families, load_reference_texts())
    for e in errors:
        print('ERROR', e)
    for f in flags:
        print('NEAR-DUP', f)
    n = len(families) if isinstance(families, list) else 0
    print(f'{n} families checked: {len(errors)} errors, {len(flags)} near-duplicate flags')
    return 1 if errors or flags else 0


if __name__ == '__main__':
    sys.exit(main())
