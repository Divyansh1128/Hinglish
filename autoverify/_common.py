"""Shared standard-library input handling; never invokes a model or network."""

import json
import re
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

FORMS = ("E", "R", "C")
SOLVERS = ("claude", "gpt")
DEFAULT_SEED = 20261015
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:/[+-]?[0-9]+)?\Z")


def exact(value):
    """Parse numeric strings, JSON integers or Decimal literals without floats."""
    if isinstance(value, Decimal):
        if value.is_finite():
            return Fraction(value)
    elif type(value) is int:
        return Fraction(value)
    elif isinstance(value, str) and _NUMBER.fullmatch(value.strip()):
        try:
            parts = value.strip().split("/")
            numerator = Fraction(parts[0])
            return numerator / Fraction(parts[1]) if len(parts) == 2 else numerator
        except (ValueError, ZeroDivisionError):
            pass
    raise ValueError("expected an exact number or fraction string (nonzero denominator)")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_float=Decimal)


def load_families(path, *, require_gold=False):
    """Accept an authoring list or a dataset object containing a families list.

    Validate only fields consumed by this pipeline. The authoring checker remains
    responsible for the full family contract. Blind task generation ignores gold.
    """
    data = read_json(path)
    families = data.get("families") if isinstance(data, dict) else data
    if not isinstance(families, list) or not families:
        raise ValueError("families must be a non-empty list")
    family_ids, rendering_ids = set(), set()
    for family in families:
        if not isinstance(family, dict):
            raise ValueError("each family must be an object")
        fid = family.get("family_id")
        if not isinstance(fid, str) or not fid.strip() or fid in family_ids:
            raise ValueError("family_id must be nonblank and unique")
        family_ids.add(fid)
        forms = family.get("forms")
        if not isinstance(forms, dict) or set(forms) != set(FORMS):
            raise ValueError(f"{fid}: exactly E/R/C forms required")
        for form in FORMS:
            rendering = forms[form]
            if not isinstance(rendering, dict):
                raise ValueError(f"{fid}/{form}: rendering must be an object")
            rid = rendering.get("rendering_id")
            if not isinstance(rid, str) or not rid.strip() or rid in rendering_ids:
                raise ValueError(f"{fid}/{form}: rendering_id must be nonblank and globally unique")
            rendering_ids.add(rid)
            if not isinstance(rendering.get("text"), str) or not rendering["text"].strip():
                raise ValueError(f"{rid}: question text required")
        if require_gold:
            gold = family.get("gold")
            if not isinstance(gold, dict) or not isinstance(gold.get("unit"), str):
                raise ValueError(f"{fid}: gold value and unit required")
            exact(gold.get("value"))
    return sorted(families, key=lambda family: family["family_id"])


def normalized_text(value):
    return " ".join(value.casefold().split())


def json_text(value):
    # Decimal tokens from solver files are stored as exact strings in reports.
    return json.dumps(value, ensure_ascii=False, allow_nan=False, default=str,
                      sort_keys=True, indent=2) + "\n"
