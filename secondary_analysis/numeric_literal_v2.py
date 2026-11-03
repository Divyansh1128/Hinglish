"""numeric_literal_v2: SECONDARY exact-literal diagnostic (D040; phase2/PREREGISTRATION.md section 4).

v2 is numeric_literal_v1 (``numeric_endpoint.py``, unchanged and imported here) plus one
rupee rule. Extraction stays gold-blind and additionally accepts

* a trailing ``₹`` (optional whitespace) as the final token after the scalar or its
  wrapper, recorded as ``currency_suffix_symbol``; and
* a leading ``rupees`` / ``rupee`` (case-insensitive, optional whitespace) in the position
  where v1 accepts ``₹/INR/Rs./Rs``, recorded as ``currency_prefix_word``.

At most one currency marker per answer; two give ``unsupported_answer`` as in v1. The
marker is stripped before the numeric comparison. In evaluation an answer extracted only
through one of the two new paths is correct only if gold is rupees (casefolded gold unit in
``rupees, rupee, inr, rs, rs., ₹``) and the value matches; otherwise it scores exactly as v1
(``unsupported_answer``, incorrect).

Wrapping guarantees: the new parser is consulted only when v1 itself returned
``unsupported_answer``, and only its results that used a new path are kept. Every other
result (and every result for non-rupee gold) is v1's own output with ``endpoint`` relabelled,
so v2 can differ from v1 only on rupee-gold items. Never calls or changes scorer v1.0.0.
"""

import re
from fractions import Fraction

from secondary_analysis import numeric_endpoint as _v1

ENDPOINT_VERSION = "numeric_literal_v2"
REASONS = _v1.REASONS
NEW_PATHS = ("currency_suffix_symbol", "currency_prefix_word")
RUPEE_UNITS = frozenset({"rupees", "rupee", "inr", "rs", "rs.", "₹"})

_PREFIX_WORD = re.compile(r"^(?:rupees|rupee)(?![^\W\d_])\s*", re.IGNORECASE)
# Currency words that, appearing as the retained suffix next to a new marker, make a second marker.
_CURRENCY_WORDS = RUPEE_UNITS


def gold_is_rupees(gold):
    return _v1._text(gold.get("unit") or "") in RUPEE_UNITS


def _final_answer(response):
    """The FINAL-line answer text and marker path, exactly as v1 derives them.

    Only called after v1 returned unsupported_answer, which v1 can raise only after this
    head succeeded, so every _Fail here is unreachable in practice."""
    text = response.replace("\r\n", "\n").replace("\r", "\n").translate(_v1._DIGITS)
    markers = list(_v1._MARKER.finditer(text))
    if len(markers) != 1:
        raise _v1._Fail("unreachable")
    lines = text.split("\n")
    line = lines[text.count("\n", 0, markers[0].start())].strip()
    start = _v1._LINE_START.match(line)
    if start:
        path = ["bold_marker" if line.startswith("**") else "plain_marker"]
        answer = line[start.end():].strip()
    elif line.startswith("**") and line.endswith("**") and len(line) > 4 \
            and _v1._PLAIN_START.match(line[2:-2].strip()):
        path = ["bold_line"]
        inner = line[2:-2].strip()
        answer = inner[_v1._PLAIN_START.match(inner).end():].strip()
    else:
        raise _v1._Fail("unreachable")
    if answer.endswith("."):
        answer = answer[:-1].rstrip()
    return answer, path


def _parse_answer_v2(answer, path):
    """v1 _parse_answer with the two extra currency markers (at most one marker in total)."""
    _v1._check_syntax(answer)
    body = _v1._unwrap_whole(answer, path)
    assignment = _v1._ASSIGNMENT.match(body)
    if assignment:
        path.append("assignment")
        body = body[assignment.end():]
    markers = 0
    prefix = _v1._CURRENCY.match(body)
    if prefix:
        path.append("currency_prefix")
        body = body[prefix.end():]
        markers += 1
    else:
        word = _PREFIX_WORD.match(body)
        if word:
            path.append("currency_prefix_word")
            body = body[word.end():]
            markers += 1
    if _v1._CURRENCY.match(body) or _PREFIX_WORD.match(body):
        raise _v1._Fail("unsupported_answer")  # a second leading currency marker
    wrapped = _v1._wrapper_end(body)
    if wrapped is not None:
        inner, end, label = wrapped
        path.append(label)
        value = _v1._scalar(_v1._unwrap_whole(inner.strip(), path))
        suffix = body[end:].strip()
    else:
        match = _v1._NUMBER.match(body)
        if match is None:
            raise _v1._Fail("unsupported_answer")
        value = _v1._scalar(match.group())
        suffix = body[match.end():].strip()
    if suffix == "/-" and prefix:
        path.append("currency_slash_dash")
        suffix = ""
    if suffix.endswith("₹"):
        if suffix[:-1].strip():
            raise _v1._Fail("unsupported_answer")  # '₹' must follow the scalar/wrapper directly
        path.append("currency_suffix_symbol")
        suffix = ""
        markers += 1
    if markers > 1:
        raise _v1._Fail("unsupported_answer")
    if markers and "currency_prefix" not in path and _v1._text(suffix) in _CURRENCY_WORDS:
        raise _v1._Fail("unsupported_answer")  # new marker plus a currency word suffix
    if suffix and not _v1._SUFFIX.fullmatch(suffix):
        raise _v1._Fail("unsupported_answer")
    return value, suffix


def _relabel(result):
    return dict(result, endpoint=ENDPOINT_VERSION)


def extract_numeric(response, truncated=False):
    """Gold-blind extraction; identical to v1 except the two new currency paths."""
    base = _relabel(_v1.extract_numeric(response, truncated))
    if base["status"] != "unsupported_answer":
        return base
    try:
        answer, path = _final_answer(response)
        value, suffix = _parse_answer_v2(answer, path)
    except _v1._Fail:
        return base
    if not any(label in path for label in NEW_PATHS):
        return base  # unreachable: without a new marker the parser is v1's
    return dict(base, value=str(value), suffix=suffix, status="extracted", extraction_path="|".join(path))


def uses_new_path(result):
    return any(label in result["extraction_path"].split("|") for label in NEW_PATHS)


def evaluate_numeric(response, gold, truncated=False):
    """v1 comparison; a new-path answer counts only for rupee gold, else it scores as v1."""
    extracted = extract_numeric(response, truncated)
    if extracted["value"] is None or not uses_new_path(extracted) or not gold_is_rupees(gold):
        return _relabel(_v1.evaluate_numeric(response, gold, truncated))
    expected = Fraction(gold["value"])
    known = {_v1._text(gold["unit"] or "")} | {_v1._text(alias) for alias in gold.get("aliases", [])}
    suffix = _v1._text(extracted["suffix"])
    unvalidated = bool(suffix) and suffix not in known
    correct = Fraction(extracted["value"]) == expected
    return dict(extracted, status="match" if correct else "mismatch", correct=correct,
                unvalidated_suffix=unvalidated, unknown_unit=extracted["suffix"] if unvalidated else None)


def numeric_correct(response, gold, truncated=False):
    return evaluate_numeric(response, gold, truncated)["correct"]
