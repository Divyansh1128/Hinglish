"""A5 self-translate probe: frozen prompt and pure-Python request/dataset builders.

EXPLORATORY, POST-PILOT ONLY. No model inference here. See README.md.
"""
import copy

SELF_TRANSLATE_PROMPT_VERSION = 'self-translate-v1'
SELF_TRANSLATE_PROMPT_V1 = ('Translate the following math word problem into English. Preserve every number, '
                            'quantity and relation exactly. Output only the translation.')
TRANSLATED_FORMS = ('R', 'C')  # E is never translated and never used as a translation.
ST_SUFFIX = '-ST'


def _prompt(text):
    return SELF_TRANSLATE_PROMPT_V1 + '\n\n' + text


def build_requests(dataset):
    """One request per R and C rendering: dicts with rendering_id, prompt, prompt_version."""
    requests = []
    for family in dataset['families']:
        for form in TRANSLATED_FORMS:
            rendering = family['forms'][form]
            requests.append({'rendering_id': rendering['rendering_id'], 'family_id': family['family_id'],
                             'form': form, 'prompt_version': SELF_TRANSLATE_PROMPT_VERSION,
                             'prompt': _prompt(rendering['text'])})
    return requests


def second_stage_dataset(dataset, translations):
    """Return a test1-1-style dataset whose R/C texts are replaced by saved translations.

    translations: {source rendering_id: translated text}. Every R/C rendering must have a
    non-empty translation; there is no fallback (in particular, never the E text). R/C
    rendering_ids gain the '-ST' suffix and keep source_rendering_id; E and gold are unchanged.
    """
    expected = {family['forms'][f]['rendering_id'] for family in dataset['families'] for f in TRANSLATED_FORMS}
    missing = sorted(expected - set(translations))
    extra = sorted(set(translations) - expected)
    if missing or extra:
        raise ValueError(f'Translation ids mismatch; missing={missing} extra={extra}')
    out = copy.deepcopy(dataset)
    out['version'] = f"{dataset.get('version', '')}{ST_SUFFIX}"
    out['kind'] = 'exploratory'
    out['exploratory_probe'] = {'name': 'A5-self-translate', 'prompt_version': SELF_TRANSLATE_PROMPT_VERSION,
                                'prompt': SELF_TRANSLATE_PROMPT_V1,
                                'note': 'EXPLORATORY post-pilot; never alters primary endpoints'}
    for family in out['families']:
        e_text = family['forms']['E']['text'].strip()
        for form in TRANSLATED_FORMS:
            rendering = family['forms'][form]
            source_id = rendering['rendering_id']
            text = translations[source_id]
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f'Empty translation for {source_id}')
            rendering['source_rendering_id'] = source_id
            rendering['source_text'] = rendering['text']
            rendering['rendering_id'] = source_id + ST_SUFFIX
            rendering['text'] = text
            # Flag (do not alter) a model output that happens to equal E verbatim.
            rendering['translation_equals_E_text'] = text.strip() == e_text
            rendering['generation_or_edit_history'] = (
                f"Model self-translation ({SELF_TRANSLATE_PROMPT_VERSION}) of {source_id}")
    return out
