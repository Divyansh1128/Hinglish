import re
import unicodedata
from fractions import Fraction


SCORER_VERSION = "1.0.0"
_FINAL = re.compile(r"\bFINAL\s*:", re.IGNORECASE)
_REFUSAL = re.compile(r"\bi\s+(?:cannot\b|can['’]t\b|am\s+unable\b)", re.IGNORECASE)
_NUMBER = re.compile(
    r"(?P<number>[+-]?(?:[0-9][0-9,]*(?:\.[0-9]+)?|\.[0-9]+)"
    r"(?:\s*/\s*[+-]?[0-9][0-9,]*)?)(?P<percent>\s*%)?"
)
_CURRENCY = {"₹", "inr", "rs", "rupees"}


def _text(value):
    return " ".join(value.strip().casefold().split())


def _digits(value):
    return value.translate(str.maketrans("०१२३४५६७८९−", "0123456789-"))


def _integer(value):
    unsigned = value.lstrip("+-")
    if "," in unsigned and not (
        re.fullmatch(r"[1-9][0-9]{0,2}(?:,[0-9]{3})+", unsigned)
        or re.fullmatch(r"[1-9][0-9]?(?:,[0-9]{2})*,[0-9]{3}", unsigned)
    ):
        raise ValueError("invalid_numeric_grouping")
    return value.replace(",", "")


def _fraction(value):
    parts = value.split("/")
    numerator = parts[0].strip()
    if "." in numerator:
        whole, decimal = numerator.split(".")
        numerator = _integer(whole) + "." + decimal
    else:
        numerator = _integer(numerator)
    result = Fraction(numerator)
    if len(parts) == 2:
        denominator = Fraction(_integer(parts[1].strip()))
        if not denominator:
            raise ValueError("zero_denominator")
        result /= denominator
    return result


def score_response(response, gold, truncated=False):
    """Score one terminal scalar answer; malformed gold raises an exception.

    Conversion multipliers map supplied units into the canonical gold unit.
    A valid but numerically wrong answer has invalid_reason=None.
    """
    expected = Fraction(gold["value"])
    canonical = gold["unit"] or ""
    units = {_text(canonical): Fraction(1)}
    for alias in gold["aliases"]:
        units[_text(alias)] = Fraction(1)
    if _text(canonical) in _CURRENCY:
        units.update({alias: Fraction(1) for alias in _CURRENCY})
    for unit, multiplier in gold.get("conversions", {}).items():
        key = _text(unit)
        factor = Fraction(multiplier)
        if not key or factor <= 0 or (key in units and units[key] != factor):
            raise ValueError("invalid gold conversion")
        units[key] = factor
    result = {
        "correct": False,
        "invalid_reason": None,
        "extracted_final": None,
        "normalized_value": None,
        "normalized_unit": None,
        "scorer_version": SCORER_VERSION,
    }

    def invalid(reason):
        result["invalid_reason"] = reason
        return result

    if truncated:
        return invalid("truncated")
    if _REFUSAL.search(response):
        return invalid("refusal")
    markers = list(_FINAL.finditer(response))
    if not markers:
        return invalid("missing_final")
    if len(markers) != 1:
        return invalid("multiple_finals")
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    final = re.fullmatch(r"FINAL\s*:\s*(.*)", lines[-1], re.IGNORECASE)
    if final is None:
        return invalid("final_not_terminal_line")
    answer = final.group(1).strip()
    result["extracted_final"] = answer
    if not answer:
        return invalid("empty_final")
    answer = _digits(answer)
    if answer.endswith("."):
        answer = answer[:-1].rstrip()
    prefix = re.match(r"^(₹|INR\b)\s*", answer, re.IGNORECASE)
    prefix_unit = prefix.group(1) if prefix else None
    if prefix:
        answer = answer[prefix.end():]
    number = _NUMBER.match(answer)
    if number is None:
        return invalid("invalid_number")
    suffix = answer[number.end():].strip()
    if suffix and (suffix[0] in ".,+-/%=;:" or any(
        unicodedata.category(character).startswith("N") for character in suffix
    )):
        return invalid("invalid_answer")
    if prefix_unit and suffix:
        return invalid("conflicting_units")
    unit = _text(prefix_unit or suffix)
    if number.group("percent") and (unit or canonical):
        return invalid("percent_requires_dimensionless")
    if not unit:
        if canonical and not gold["unit_omission_allowed"]:
            return invalid("missing_unit")
        factor = Fraction(1)
    elif unit not in units:
        return invalid("invalid_unit")
    else:
        factor = units[unit]
    try:
        value = _fraction(number.group("number")) * factor
    except (ValueError, ZeroDivisionError) as error:
        return invalid(str(error))
    if number.group("percent"):
        value /= 100
    result["normalized_value"] = str(value)
    result["normalized_unit"] = canonical
    result["correct"] = value == expected
    return result
