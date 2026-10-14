"""CMI on supplied tags; optional HEURISTIC tags require human correction."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

TAGS = {"hi", "en", "univ"}
HEURISTIC_LABEL = "HEURISTIC — NOT GOLD; HUMAN CORRECTION REQUIRED"
_ENGLISH = set("a an the is are was were has have had of in on at to from with and or but if then how many much what find total left remaining each per more less than cost costs price weight volume distance time ratio solve equal equals plus minus times divided bottle bottles box boxes bag bags ticket tickets bead beads minutes kilograms litres kilometers receives sells buys holds travels".split())
_HINDI = set("ek do teen chaar paanch hai hain tha thi the ka ki ke ko se mein par aur ya lekin agar toh to kitna kitni kitne kya kul bache bachi bacha har prati zyada kam daam wajan vajan samay anupat nikalo batao barabar jod ghata guna bhaag rupaye kilo litar minat mitar kilomitar diya liya leta leti rakhta rakhti chalti bechta kharidta".split())
_NAMES = set("asha dev isha kabir leela neel om ritu tara zoya arun mira".split())


def analyze_tags(tagged_tokens):
    """Gambäck & Das CMI: 100*(1-max(hi,en)/(N-U)); zero if N=U.

    Switch points count changes between successive language-bearing tokens,
    skipping univ tokens (thus hi/univ/en is one switch). Input tags must be
    human-corrected to interpret the result as annotated CMI.
    """
    counts = Counter()
    languages = []
    for token, tag in tagged_tokens:
        if not isinstance(token, str) or tag not in TAGS:
            raise ValueError("Expected (text, tag) with tag in {hi, en, univ}")
        counts[tag] += 1
        if tag != "univ":
            languages.append(tag)
    n = sum(counts.values())
    u = counts["univ"]
    score = 100 * (1 - max(counts["hi"], counts["en"])/(n-u)) if n != u else 0.0
    return dict(cmi=score, N=n, U=u, hi=counts["hi"], en=counts["en"],
                switch_points=sum(a != b for a, b in zip(languages, languages[1:])),
                switch_policy="skip_univ")


def cmi(tagged_tokens):
    return analyze_tags(tagged_tokens)["cmi"]


def switch_points(tagged_tokens):
    return analyze_tags(tagged_tokens)["switch_points"]


def heuristic_tag(text, names=()):
    """Small wordlists, NOT a language-ID model or gold annotation.

    Tokenization keeps numbers/decimals together and punctuation separately.
    Supplied/known names, unknown capitalized words, numbers and punctuation
    are univ. Other unknown words and overlapping words (e.g. 'to', 'the') are
    also univ pending human correction. Borrowings need human policy review.
    """
    name_set = _NAMES | {name.casefold() for name in names}
    tokens = re.findall(r"\d+(?:[.,]\d+)*|[^\W\d_]+(?:['’][^\W\d_]+)*|[^\w\s]|_", text, re.UNICODE)
    tagged = []
    for token in tokens:
        lower = token.casefold()
        if lower in name_set or lower in (_ENGLISH & _HINDI):
            tag = "univ"
        elif lower in _HINDI:
            tag = "hi"
        elif lower in _ENGLISH:
            tag = "en"
        else:
            tag = "univ"
        tagged.append((token, tag))
    return tagged


def heuristic_annotation(text, names=()):
    tagged = heuristic_tag(text, names)
    return dict(label=HEURISTIC_LABEL, human_corrected=False,
                tokens=[dict(token=token, tag=tag) for token, tag in tagged],
                heuristic_diagnostic=analyze_tags(tagged),
                limitations="Unknown/overlapping words default to univ; names and borrowings need human review.")


def main():
    parser = argparse.ArgumentParser(description=HEURISTIC_LABEL)
    parser.add_argument("text", help="Romanized text to pre-tag for human correction")
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--output", type=Path, help="New JSON file only; existing files are refused")
    args = parser.parse_args()
    content = json.dumps(heuristic_annotation(args.text, args.name), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(content)
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
