"""A4 lexical gloss probe: replace ONE operation word in an R rendering with its English gloss.

EXPLORATORY, POST-PILOT ONLY. No model inference here. See README.md.

Matching is whole-word and case-insensitive; only the exact lexicon surface is matched.
Inflected or longer forms (e.g. 'bhaagna' for 'bhaag', 'jodo' for 'jod') are NOT matched
unless they are themselves lexicon keys. All occurrences of the single chosen word are
replaced; no other lexicon word is touched (one word at a time).
"""
import re

LEXICON_STATUS = 'UNCONFIRMED'  # glosses not human-confirmed; see research/operation_vocabulary_2026-10-15.md
DEFAULT_LEXICON = {
    'bhaag': 'divide',
    'bhinn': 'fraction',
    'guna': 'multiply',
    'jod': 'add',
    'ghata': 'subtract',
    'anupat': 'ratio',
    'pratishat': 'percent',
}
GLOSS_SUFFIX = '-GL-'


def _pattern(word):
    return re.compile(r'(?<!\w)' + re.escape(word) + r'(?!\w)', re.IGNORECASE)


def _match_case(source, gloss):
    if source.isupper() and len(source) > 1:
        return gloss.upper()
    if source[:1].isupper():
        return gloss[:1].upper() + gloss[1:]
    return gloss


def gloss_variants(dataset, lexicon=None):
    """Return one variant per (R rendering, matched lexicon word); none if nothing matches."""
    lexicon = DEFAULT_LEXICON if lexicon is None else lexicon
    variants = []
    for family in dataset['families']:
        rendering = family['forms']['R']
        text = rendering['text']
        for word in sorted(lexicon):
            gloss = lexicon[word]
            pattern = _pattern(word)
            matches = [m.group(0) for m in pattern.finditer(text)]
            if not matches:
                continue
            new_text = pattern.sub(lambda m: _match_case(m.group(0), gloss), text)
            variants.append({
                'rendering_id': rendering['rendering_id'] + GLOSS_SUFFIX + word,
                'source_rendering_id': rendering['rendering_id'],
                'family_id': family['family_id'],
                'gold': family['gold'],
                'word': word, 'gloss': gloss, 'lexicon_status': LEXICON_STATUS,
                'matched_surfaces': matches, 'replacements': len(matches),
                'source_text': text, 'text': new_text,
            })
    return variants
