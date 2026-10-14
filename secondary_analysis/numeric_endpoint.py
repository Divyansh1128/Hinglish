"""numeric_literal_v1: SECONDARY exact-literal diagnostic; never calls scorer v1.

Implements section 1 of research/pre_pilot_endpoint_spec_v1.md (PROPOSED, not
adopted). It asks one question: does the single declared FINAL line hold a
scalar literal equal to the frozen gold value? Units are retained but never
converted or validated, so this is not semantic or dimensional accuracy.
Extraction never consults gold or form; gold is used only for the comparison.
"""

import re
from fractions import Fraction

ENDPOINT_VERSION = "numeric_literal_v1"

# Ordered failure reasons (spec section 1, final paragraph).
REASONS = ("not_generated", "truncated", "missing_final", "multiple_finals", "unsupported_marker",
           "empty_final", "malformed_wrapper", "invalid_numeric_grouping", "zero_denominator",
           "unsupported_answer")

_MARKER = re.compile(r"\bFINAL(?:\*\*)?[ \t]*:", re.IGNORECASE)
_LINE_START = re.compile(r"^(?:\*\*FINAL[ \t]*:[ \t]*\*\*|\*\*FINAL\*\*[ \t]*:|FINAL[ \t]*:)", re.IGNORECASE)
_PLAIN_START = re.compile(r"^FINAL[ \t]*:", re.IGNORECASE)
_NUMBER = re.compile(
    r"(?P<number>[+-]?(?:[0-9][0-9,]*(?:\.[0-9]+)?|\.[0-9]+)"
    r"(?:\s*/\s*[+-]?[0-9][0-9,]*)?)(?P<percent>\s*%)?"
)
_ASSIGNMENT = re.compile(r"^[A-Za-z]\s*=\s*")
_CURRENCY = re.compile(r"^(?:₹|INR\b|Rs\.|Rs\b)\s*", re.IGNORECASE)
_WORD = r"[^\W\d_]+(?:['’-][^\W\d_]+)*"
_SUFFIX = re.compile(rf"^{_WORD}(?:\s+{_WORD})*$")
_DIGITS = str.maketrans("०१२३४५६७८९−", "0123456789-")


class _Fail(Exception):
    pass


def _text(value):
    return " ".join(value.strip().casefold().split())


def _integer(value):
    unsigned = value.lstrip("+-")
    if "," in unsigned and not (
        re.fullmatch(r"[1-9][0-9]{0,2}(?:,[0-9]{3})+", unsigned)
        or re.fullmatch(r"[1-9][0-9]?(?:,[0-9]{2})*,[0-9]{3}", unsigned)
    ):
        raise _Fail("invalid_numeric_grouping")
    return value.replace(",", "")


def _scalar(text):
    """Whole-string v1.0.0 numeric grammar; returns an exact Fraction."""
    match = _NUMBER.fullmatch(text.strip())
    if match is None:
        raise _Fail("unsupported_answer")
    parts = match["number"].split("/")
    numerator = parts[0].strip()
    if "." in numerator:
        whole, decimal = numerator.split(".")
        numerator = _integer(whole) + "." + decimal
    else:
        numerator = _integer(numerator)
    value = Fraction(numerator)
    if len(parts) == 2:
        denominator = Fraction(_integer(parts[1].strip()))
        if not denominator:
            raise _Fail("zero_denominator")
        value /= denominator
    return value / 100 if match["percent"] else value


def _wrapper_end(text):
    """If text starts with a D() wrapper, return (inner, end_index, label)."""
    if text.startswith("**"):
        end = text.find("**", 2)
        if end < 0:
            raise _Fail("malformed_wrapper")
        return text[2:end], end + 2, "bold"
    if text.startswith("$"):
        end = text.find("$", 1)
        if end < 0:
            raise _Fail("malformed_wrapper")
        return text[1:end], end + 1, "dollar"
    if text.startswith("\\boxed{"):
        depth = 0
        for index in range(len("\\boxed"), len(text)):
            depth += {"{": 1, "}": -1}.get(text[index], 0)
            if depth == 0:
                return text[len("\\boxed{"):index], index + 1, "boxed"
        raise _Fail("malformed_wrapper")
    return None


def _unwrap_whole(text, path):
    """Strip balanced D() wrappers that enclose the entire text."""
    while True:
        wrapped = _wrapper_end(text)
        if wrapped is None or wrapped[1] != len(text):
            return text
        inner, _, label = wrapped
        if not inner.strip():
            raise _Fail("malformed_wrapper")
        path.append(label)
        text = inner.strip()


def _check_syntax(answer):
    if "$$" in answer or "_" in answer or "`" in answer:
        raise _Fail("unsupported_answer")
    if re.search(r"\\(?!boxed\{)", answer):
        raise _Fail("unsupported_answer")  # \text{}, \frac{} and other commands
    if answer.count("**") % 2 or answer.count("$") % 2 or answer.count("{") != answer.count("}"):
        raise _Fail("malformed_wrapper")


def _parse_answer(answer, path):
    _check_syntax(answer)
    body = _unwrap_whole(answer, path)
    assignment = _ASSIGNMENT.match(body)
    if assignment:
        path.append("assignment")
        body = body[assignment.end():]
    prefix = _CURRENCY.match(body)
    if prefix:
        path.append("currency_prefix")
        body = body[prefix.end():]
    wrapped = _wrapper_end(body)
    if wrapped is not None:
        inner, end, label = wrapped
        path.append(label)
        value = _scalar(_unwrap_whole(inner.strip(), path))
        suffix = body[end:].strip()
    else:
        match = _NUMBER.match(body)
        if match is None:
            raise _Fail("unsupported_answer")
        value = _scalar(match.group())
        suffix = body[match.end():].strip()
    if suffix == "/-" and prefix:
        path.append("currency_slash_dash")
        suffix = ""
    if suffix and not _SUFFIX.fullmatch(suffix):
        raise _Fail("unsupported_answer")
    return value, suffix


def extract_numeric(response, truncated=False):
    """Extract the declared FINAL-line scalar without consulting gold.

    Returns value (exact Fraction string or None), suffix (retained, never
    converted), status ('extracted' or one REASONS entry), extraction_path,
    final_markers and trailing_nonblank.
    """
    result = dict(endpoint=ENDPOINT_VERSION, value=None, suffix="", status=None,
                  extraction_path="", final_markers=0, trailing_nonblank=False)
    if response is None:
        result["status"] = "not_generated"
        return result
    if not isinstance(response, str):
        raise TypeError("response must be text or None")
    path = []
    try:
        if truncated:
            raise _Fail("truncated")
        text = response.replace("\r\n", "\n").replace("\r", "\n").translate(_DIGITS)
        markers = list(_MARKER.finditer(text))
        result["final_markers"] = len(markers)
        if not markers:
            raise _Fail("missing_final")
        if len(markers) > 1:
            raise _Fail("multiple_finals")
        lines = text.split("\n")
        index = text.count("\n", 0, markers[0].start())
        line = lines[index].strip()
        result["trailing_nonblank"] = any(rest.strip() for rest in lines[index + 1:])
        start = _LINE_START.match(line)
        if start:
            path.append("bold_marker" if line.startswith("**") else "plain_marker")
            answer = line[start.end():].strip()
        elif line.startswith("**") and line.endswith("**") and len(line) > 4 \
                and _PLAIN_START.match(line[2:-2].strip()):
            path.append("bold_line")
            inner = line[2:-2].strip()
            answer = inner[_PLAIN_START.match(inner).end():].strip()
        else:
            raise _Fail("unsupported_marker")
        if answer.endswith("."):
            answer = answer[:-1].rstrip()
        if not answer:
            raise _Fail("empty_final")
        value, suffix = _parse_answer(answer, path)
    except _Fail as failure:
        result.update(status=failure.args[0], extraction_path="|".join(path))
        return result
    result.update(value=str(value), suffix=suffix, status="extracted", extraction_path="|".join(path))
    return result


def evaluate_numeric(response, gold, truncated=False):
    """Compare the extracted literal with Fraction(gold value); no conversions.

    status is 'match', 'mismatch' or the extraction failure reason. A suffix
    that is neither the canonical unit nor a listed alias is flagged
    unvalidated_suffix; it never changes the numeric comparison.
    """
    expected = Fraction(gold["value"])  # malformed gold stops analysis
    extracted = extract_numeric(response, truncated)
    known = {_text(gold["unit"] or "")} | {_text(alias) for alias in gold.get("aliases", [])}
    suffix = _text(extracted["suffix"])
    unvalidated = bool(suffix) and suffix not in known
    if extracted["value"] is None:
        correct, status = False, extracted["status"]
    else:
        correct = Fraction(extracted["value"]) == expected
        status = "match" if correct else "mismatch"
    return dict(extracted, status=status, correct=correct, unvalidated_suffix=unvalidated,
                unknown_unit=extracted["suffix"] if unvalidated else None)


def numeric_correct(response, gold, truncated=False):
    """Return bool: the declared FINAL literal equals gold exactly."""
    return evaluate_numeric(response, gold, truncated)["correct"]
