"""CMI_v1 and editable HEURISTIC pre-tags (standard library only).

Canonical tags: HI/EN/SHARED/MIXED/UNCERTAIN. Legacy input maps hi->HI,
en->EN, univ->SHARED; it cannot recover uncertainty in old annotations.

Dataset CLI (question text only; one token per CSV row):
  python3 -B -m secondary_analysis.cmi --dataset dataset.json --output-dir NEW_DIR
It writes R.csv and C.csv, never overwrites a directory or writes under pilot/.
One bilingual human must correct tokenization, names, homographs, borrowing
policy and all tags, and record boundaries/rationale/identity before freezing.
No gold answers or reference solutions are read into the sheets.
CSV text cells starting = + - @ receive a leading apostrophe for spreadsheet
safety; remove that one escape prefix when importing CSV text. Token offsets
and hashes always index the unescaped NFC question surface.
"""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

TAGS = frozenset({"HI", "EN", "SHARED", "MIXED", "UNCERTAIN"})
LEGACY_TAGS = {"hi": "HI", "en": "EN", "univ": "SHARED"}
HEURISTIC_LABEL = "HEURISTIC — NOT GOLD; HUMAN CORRECTION REQUIRED"
_ENGLISH = set("a an the is me are was were has have had of in on at to from with and or but if then how many much what find total left remaining each per more less than cost costs price weight volume distance time ratio solve equal equals plus minus times divided bottle bottles box boxes bag bags ticket tickets bead beads minutes kilograms litres kilometers receives sells buys holds travels".split())
_HINDI = set("ek do teen chaar paanch hai hain tha thi the ka ki ke ko se mein me par aur ya lekin agar toh to is kitna kitni kitne kya kul bache bachi bacha har prati zyada kam daam wajan vajan samay anupat nikalo batao barabar jod ghata guna bhaag rupaye kilo litar minat mitar kilomitar diya liya leta leti rakhta rakhti chalti bechta kharidta".split())
_NAMES = set("asha dev isha kabir leela neel om ritu tara zoya arun mira".split())
_UNIT_NOTATION = set("INR Rs L mL m cm km kg g h s".casefold().split())
_SWITCH_POLICY = "skip_SHARED_within_sentence; break_at_MIXED_UNCERTAIN"
_FIELDS = ("label", "human_corrected", "family_id", "rendering_id", "form",
           "source_text_sha256", "text_sha256", "offset_basis", "token_index",
           "start", "end", "token", "tag", "sentence_id", "sentence_end",
           "rationale", "tagger", "adjudicator", "borrowing_policy")


def analyze_tags(tagged_tokens, sentence_ends=()):
    """CMI_v1 = 100*(1-max(H,E)/(N-U)), with U=SHARED.

    Return missing (None) if MIXED/UNCERTAIN remains; otherwise zero when N=U.
    N counts every supplied token, including unresolved tokens. Lowercase
    hi/en/univ remain accepted via LEGACY_TAGS. The hi/en result keys are
    retained as aliases for H/E; `cmi` and `CMI_v1` are the same headline.

    Switches skip SHARED inside sentences, and break at unresolved tokens or
    . ? ! / newline tokens. For whitespace omitted during tokenization, supply
    zero-based sentence_ends indices (the token preceding a boundary). CSV
    sentence_end flags can be converted to these indices after human correction.
    """
    counts = Counter()
    previous = None
    switches = 0
    ends = set(sentence_ends)
    for index, (token, tag) in enumerate(tagged_tokens):
        if not isinstance(token, str) or not isinstance(tag, str):
            raise ValueError("Expected (text, tag) with a canonical or legacy tag")
        tag = LEGACY_TAGS.get(tag, tag)
        if tag not in TAGS:
            raise ValueError("Expected tag in HI/EN/SHARED/MIXED/UNCERTAIN (or hi/en/univ)")
        counts[tag] += 1
        # A literal newline represents omitted whitespace and cannot bridge a
        # switch, even if its supplied tag is language-bearing by mistake.
        if "\n" in token or "\r" in token:
            previous = None
        elif tag in {"MIXED", "UNCERTAIN"}:
            previous = None
        elif tag in {"HI", "EN"}:
            switches += int(previous is not None and previous != tag)
            previous = tag
        if index in ends or re.fullmatch(r"[.?!]+", token):
            previous = None
    n, u = sum(counts.values()), counts["SHARED"]
    h, e = counts["HI"], counts["EN"]
    score = None
    if not (counts["MIXED"] or counts["UNCERTAIN"]):
        score = 100 * (1 - max(h, e)/(n-u)) if n != u else 0.0
    return dict(cmi=score, CMI_v1=score, N=n, U=u, H=h, E=e, hi=h, en=e,
                SHARED=u, MIXED=counts["MIXED"], UNCERTAIN=counts["UNCERTAIN"],
                no_language_tokens=(n == u), switch_points=switches,
                switch_policy=_SWITCH_POLICY)


def cmi(tagged_tokens, sentence_ends=()):
    return analyze_tags(tagged_tokens, sentence_ends)["cmi"]


def switch_points(tagged_tokens, sentence_ends=()):
    return analyze_tags(tagged_tokens, sentence_ends)["switch_points"]


def _letter(char):
    return unicodedata.category(char)[0] in {"L", "M"}


def tokenize(text):
    """NFC tokens with half-open codepoint offsets; whitespace is omitted.

    Maximal letter/mark words retain internal apostrophes. Numbers retain
    internal . , / separators; adjacent letters, hyphens and symbols split.
    Newline gaps set sentence_end on the preceding token, as do . ? ! tokens.
    Offsets index NFC text, not the original potentially decomposed string.
    """
    normalized = unicodedata.normalize("NFC", text)
    tokens = []
    index = 0
    while index < len(normalized):
        char = normalized[index]
        if char.isspace():
            if char in "\r\n" and tokens:
                tokens[-1]["sentence_end"] = True
            index += 1
            continue
        start = index
        if char.isdecimal() or (char == "." and index + 1 < len(normalized) and normalized[index+1].isdecimal()):
            index += 1
            while index < len(normalized):
                if normalized[index].isdecimal():
                    index += 1
                elif (normalized[index] in ".,/" and index + 1 < len(normalized)
                      and normalized[index+1].isdecimal()):
                    index += 1
                else:
                    break
            kind = "number"
        elif _letter(char):
            index += 1
            while index < len(normalized):
                if _letter(normalized[index]):
                    index += 1
                elif (normalized[index] in "'’" and index + 1 < len(normalized)
                      and _letter(normalized[index+1])):
                    index += 1
                else:
                    break
            kind = "word"
        else:
            index += 1
            kind = "symbol"
        surface = normalized[start:index]
        tokens.append(dict(token=surface, start=start, end=index, kind=kind,
                           sentence_end=(surface in {".", "?", "!"})))
    return tokens


def _pretag(token, name_set):
    lower = token["token"].casefold()
    if token["kind"] != "word":
        return "SHARED", "Number, punctuation or symbol; human must check tokenization"
    if lower in name_set:
        return "SHARED", "Known/supplied proper name; human must verify"
    if lower in (_ENGLISH & _HINDI):
        return "UNCERTAIN", "Homograph; disambiguate by syntax/meaning"
    if lower in _UNIT_NOTATION:
        return "SHARED", "Unit notation; human must verify context"
    if lower in _HINDI:
        return "HI", "Hindi heuristic wordlist; human must verify"
    if lower in _ENGLISH:
        return "EN", "English heuristic wordlist; human must verify"
    return "UNCERTAIN", "Unknown word/name/morphology; human must resolve under frozen borrowing policy"


def heuristic_annotation(text, names=()):
    name_set = _NAMES | {unicodedata.normalize("NFC", name).casefold() for name in names}
    tokens = tokenize(text)
    sentence = 0
    for index, token in enumerate(tokens):
        tag, rationale = _pretag(token, name_set)
        token.update(tag=tag, rationale=rationale, token_index=index,
                     sentence_id=sentence, tagger="", adjudicator="")
        sentence += int(token["sentence_end"])
    ends = [i for i, token in enumerate(tokens) if token["sentence_end"]]
    return dict(label=HEURISTIC_LABEL, human_corrected=False,
                source_text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                text_sha256=hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest(),
                offset_basis="NFC Unicode codepoints; start inclusive, end exclusive",
                tokens=tokens,
                heuristic_diagnostic=analyze_tags([(t["token"], t["tag"]) for t in tokens], ends),
                limitations="Single human correction required; unknown/homograph tokens are UNCERTAIN. Borrowings are not automatically SHARED; freeze policy and token table before generation.")


def heuristic_tag(text, names=()):
    """Return canonical pre-tag pairs; NOT GOLD. For newline-safe diagnostics,
    use heuristic_annotation (which retains sentence_end metadata) or pass the
    corresponding boundary indices to analyze_tags.
    """
    return [(t["token"], t["tag"]) for t in heuristic_annotation(text, names)["tokens"]]


def _outside_pilot(path):
    # Resolve existing symlinks before checking, including symlinked parents.
    if "pilot" in Path(path).resolve().parts:
        raise ValueError("CMI output must not be written into pilot/")


def _csv_safe(value):
    # Keep editable text from becoming a spreadsheet formula. Offsets/hashes
    # still refer to the original NFC surface; strip the leading quote on import.
    return "'" + value if isinstance(value, str) and value and value[:1] in "=+-@" else value


def write_dataset_sheets(dataset_path, output_dir, names=()):
    """Create NEW_DIR/{R,C}.csv after validating every rendering.

    Accept forms as rendering objects {rendering_id, text, ...} (Test 1 and
    FMT2) or text strings (smoke schema). E, gold and solutions are excluded.
    Metadata is a draft, not proof that the supplied borrowing policy is frozen.
    """
    output_dir = Path(output_dir)
    _outside_pilot(output_dir)
    dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(dataset, dict) or not isinstance(dataset.get("families"), list) or not dataset["families"]:
        raise ValueError("Dataset must contain a nonempty families list")
    policy = dataset.get("borrowing_policy", "NOT FROZEN — human must supply borrowing policy")
    if not isinstance(policy, str):
        raise ValueError("borrowing_policy must be text")
    rows = {"R": [], "C": []}
    family_ids, rendering_ids = set(), set()
    for family in dataset["families"]:
        if not isinstance(family, dict):
            raise ValueError("Each family must be an object")
        fid = family.get("family_id")
        if not isinstance(fid, str) or not fid.strip() or fid in family_ids:
            raise ValueError("Missing/duplicate family_id")
        family_ids.add(fid)
        forms = family.get("forms")
        if not isinstance(forms, dict):
            raise ValueError("Each family must contain R and C forms")
        for form in rows:
            rendering = forms.get(form)
            if isinstance(rendering, str):
                text, rid = rendering, f"{fid}-{form}"
            elif isinstance(rendering, dict):
                text, rid = rendering.get("text"), rendering.get("rendering_id")
            else:
                raise ValueError(f"Missing/invalid {form} rendering")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Empty/nontext {form} rendering")
            if not isinstance(rid, str) or not rid.strip() or rid in rendering_ids:
                raise ValueError("Missing/duplicate rendering_id")
            rendering_ids.add(rid)
            draft = heuristic_annotation(text, names)
            for token in draft["tokens"]:
                row = {k: draft[k] for k in ("label", "human_corrected", "source_text_sha256", "text_sha256", "offset_basis")}
                row.update(family_id=fid, rendering_id=rid, form=form, borrowing_policy=policy)
                row.update({k: token[k] for k in ("token_index", "start", "end", "token", "tag", "sentence_id", "sentence_end", "rationale", "tagger", "adjudicator")})
                rows[form].append(row)
    # Deliberately no parents=True/exist_ok=True: the output must be a fresh
    # directory, and invalid datasets must not create partial sheets.
    output_dir.mkdir()
    for form, sheet in rows.items():
        with (output_dir / f"{form}.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, _FIELDS)
            writer.writeheader()
            writer.writerows({k: _csv_safe(v) for k, v in row.items()} for row in sheet)
    return {form: len(sheet) for form, sheet in rows.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=HEURISTIC_LABEL, epilog="Legacy input tags: hi→HI, en→EN, univ→SHARED. Dataset sheets require one human to correct every rendering.")
    parser.add_argument("text", nargs="?", help="Romanized text to pre-tag for human correction")
    parser.add_argument("--dataset", type=Path, help="Dataset JSON; pre-tag every R/C question into CSV")
    parser.add_argument("--output-dir", type=Path, help="NEW directory for R.csv/C.csv; never under pilot/")
    parser.add_argument("--name", action="append", default=[], help="Known proper name (repeatable)")
    parser.add_argument("--output", type=Path, help="Text mode: new editable JSON file only")
    args = parser.parse_args(argv)
    if args.dataset is not None:
        if args.text is not None or args.output is not None or args.output_dir is None:
            parser.error("--dataset requires --output-dir and cannot be combined with text/--output")
    elif args.text is None or args.output_dir is not None:
        parser.error("Supply text (optional --output), or --dataset with --output-dir")
    try:
        if args.dataset is not None:
            counts = write_dataset_sheets(args.dataset, args.output_dir, args.name)
            print(f"{HEURISTIC_LABEL}\nCreated R.csv/C.csv: {counts['R']} R tokens, {counts['C']} C tokens. One human must correct every rendering.")
        else:
            content = json.dumps(heuristic_annotation(args.text, args.name), ensure_ascii=False, indent=2) + "\n"
            if args.output is not None:
                _outside_pilot(args.output)
                with args.output.open("x", encoding="utf-8") as stream:
                    stream.write(content)
            else:
                print(content, end="")
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"CMI pre-tagging failed: {error}\n")


if __name__ == "__main__":
    main()
