import argparse
import hashlib
import json
import re
from fractions import Fraction
from pathlib import Path


MODEL = "Qwen/Qwen3-4B"
INSTRUCTION_V1 = (
    "Solve the problem. Give a short explanation in English. End with exactly one "
    "line: FINAL: <number or fraction> <unit when applicable>."
)
INSTRUCTION = (
    "Solve the problem. Give a short explanation in English, even if the question is not "
    "in English. End with exactly one line: FINAL: <number or fraction>, followed by its "
    "unit in English only if the answer has a unit; write nothing after a pure number or fraction."
)
# Conservative vocabulary for model-free validation, not the frozen scoring
# alias ledger. New English units need an explicit vocabulary review here;
# Romanized Hindi aliases must never become training-target suffixes.
ENGLISH_UNITS = frozenset("""
    % INR Rs rupee rupees L mL m cm km kg g h s
    litre litres liter liters millilitre millilitres milliliter milliliters
    metre metres meter meters centimetre centimetres centimeter centimeters
    kilometre kilometres kilometer kilometers kilogram kilograms gram grams
    hour hours minute minutes second seconds percent percentage
    marble marbles bead beads ticket tickets notebook notebooks book books
    pen pens pencil pencils bottle bottles box boxes bag bags apple apples
    orange oranges mango mangoes student students person people plate plates
    seat seats bus buses cycle cycles jug jugs coin coins item items
    girl girls piece pieces sticker stickers
""".casefold().split())
_NUMBER = r"[+-]?(?:[0-9][0-9,]*(?:\.[0-9]+)?|\.[0-9]+)"
_FINAL_ANSWER = re.compile(r"FINAL: (" + _NUMBER + r"(?:[ \t]*/[ \t]*[+-]?[0-9][0-9,]*)?)(?:[ \t]+([^\n]+))?")
STACK = {
    "torch": "2.7.1", "transformers": "4.51.3", "peft": "0.15.2",
    "bitsandbytes": "0.45.5", "accelerate": "1.6.0",
    "huggingface-hub": "0.30.2", "safetensors": "0.5.3",
    "numpy": "2.2.5", "psutil": "7.0.0", "nvidia-ml-py": "12.570.86",
}
CONFIG = {
    "model": MODEL, "seed": 11, "sequence_length": 1024,
    "families": 16, "forms_per_arm": 2, "repetitions": 3,
    "microbatch": 1, "accumulation": 16, "updates": 6,
    "measurement_warmup_updates": 2, "resume_after_update": 4,
    "budget_seconds": 1800, "minimum_headroom_bytes": 2 * 1024**3,
    "rank": 16, "alpha": 32, "dropout": 0.05,
    "targets": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "quantization": "nf4", "double_quantization": True,
    "compute_dtype": "float16", "adapter_dtype": "float32",
    "optimizer": "torch.optim.AdamW", "optimizer_dtype": "float32",
    "lr": 1e-4, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0,
    "clip": 1.0, "lr_schedule": "constant_smoke_only",
    "attention": "sdpa_math_only", "gradient_checkpointing": "non_reentrant",
    "use_cache": False, "thinking": False, "packing": False,
    "probe_atol": 1e-3, "probe_rtol": 1e-3,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def file_digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def validate_revision(revision):
    require(bool(re.fullmatch(r"[0-9a-f]{40}", revision)), "Use an immutable 40-hex commit SHA")


def identifiers(record):
    for field in ("family_id", "source_family_id"):
        require(isinstance(record.get(field), str) and record[field].strip(), f"Missing {field}")
    return {record["family_id"], record["source_family_id"]}


def validate_final(text, unit=None):
    """Require the v2 terminal target format; optional gold unit disambiguates
    dimensionless answers. This checks syntax/language, not answer correctness.
    English suffixes use ENGLISH_UNITS; unsupported units fail for review.
    """
    require(isinstance(text, str) and bool(text.strip()), "Empty target/reference solution")
    require(len(re.findall(r"\bFINAL\s*:", text, re.IGNORECASE)) == 1, "Need exactly one FINAL line")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    match = _FINAL_ANSWER.fullmatch(lines[-1])
    require(match is not None, "Target/reference FINAL must end with a number or fraction and optional English unit")
    number, suffix = match.groups()
    for part in number.split("/"):
        whole = part.strip().split(".")[0].lstrip("+-")
        require(
            "," not in whole or bool(re.fullmatch(r"[1-9][0-9]{0,2}(?:,[0-9]{3})+|[1-9][0-9]?(?:,[0-9]{2})*,[0-9]{3}", whole)),
            "Invalid numeric grouping in FINAL",
        )
    try:
        parts = number.replace(",", "").split("/")
        value = Fraction(parts[0].strip())
        if len(parts) == 2:
            value /= Fraction(parts[1].strip())
    except (ValueError, ZeroDivisionError):
        raise ValueError("Invalid number/fraction in FINAL") from None
    require(suffix is None or suffix.casefold() in ENGLISH_UNITS, "FINAL suffix must be a supported English unit; nothing after a pure number/fraction")
    if unit is not None:
        require(isinstance(unit, str), "gold.unit must be text")
        require(bool(suffix) == bool(unit), "FINAL unit presence must match gold.unit; nothing after a pure number/fraction")


def validate_targets(family):
    unit = family.get("gold", {}).get("unit")
    validate_final(family["completion"], unit)
    if "reference_solution_en" in family:
        validate_final(family["reference_solution_en"], unit)


def validate_data(data, manifest):
    require(bool(data.get("version")), "Missing smoke data version")
    families = data["families"]
    require(len(families) == 16, "Exactly 16 smoke families required")
    audit = manifest["audit"]
    require(audit.get("approved") is True and bool(audit.get("reviewer")), "Human split audit required")
    require(audit.get("unresolved_matches") == 0, "Unresolved split matches")
    smoke_ids = set()
    prompts = set()
    for family in families:
        current = identifiers(family)
        require(not current & smoke_ids, "Repeated underlying smoke family ID")
        smoke_ids |= current
        require(family.get("split_role") == "SMOKE_TRAIN", "Not SMOKE_TRAIN")
        for field in ("provenance", "source_license", "completion"):
            require(isinstance(family.get(field), str) and family[field].strip(), f"Missing {field}")
        validate_targets(family)
        require(set(family["forms"]) == {"E", "R", "C"}, "Need all three forms to validate both arms")
        for text in family["forms"].values():
            require(isinstance(text, str) and text.strip(), "Empty prompt")
            normalized = " ".join(text.casefold().split())
            require(normalized not in prompts, "Duplicate normalized smoke prompt")
            prompts.add(normalized)
    role_ids = {}
    for role in ("PILOT_EVAL", "RETIRED_DRAFT", "CONFIRM_TRAIN", "FINAL_TEST"):
        records = manifest[role]
        require(isinstance(records, list), f"Invalid {role} manifest")
        collected = set()
        for record in records:
            current = identifiers(record)
            require(not collected & current, f"Duplicate family within {role}")
            collected |= current
        role_ids[role] = collected
        require(not smoke_ids & collected, f"Smoke overlap with {role}")
    require(len(manifest["PILOT_EVAL"]) == 30, "Need the 30 pilot family identities, not their questions")
    development = smoke_ids | role_ids["PILOT_EVAL"] | role_ids["RETIRED_DRAFT"]
    excluded = set(manifest["development_exclusion_ids"])
    require(development <= excluded, "Permanent exclusion manifest missing development IDs")
    require(not excluded & (role_ids["CONFIRM_TRAIN"] | role_ids["FINAL_TEST"]), "Confirmatory contamination")
    require(not role_ids["CONFIRM_TRAIN"] & role_ids["FINAL_TEST"], "Train/test family overlap")
    return sorted(families, key=lambda family: family["family_id"])


def encode_record(tokenizer, family, form):
    validate_targets(family)
    messages = [{"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": family["forms"][form]}]
    for text in (family["forms"][form], family["completion"]):
        require(not any(marker in text for marker in tokenizer.all_special_tokens), "Literal special token in input")
    prefix = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, enable_thinking=False,
    )
    completion = tokenizer.encode(family["completion"], add_special_tokens=False)
    require(bool(completion), "Empty completion tokens")
    target = completion + [tokenizer.eos_token_id]
    require(tokenizer.eos_token_id is not None and tokenizer.pad_token_id is not None, "Missing EOS/PAD")
    real = prefix + target
    require(len(prefix) > 0 and len(real) <= 1024, f"Overlength/invalid family {family['family_id']}; no truncation allowed")
    padding = 1024 - len(real)
    labels = [-100] * len(prefix) + target + [-100] * padding
    record = {
        "family_id": family["family_id"], "form": form,
        "input_ids": real + [tokenizer.pad_token_id] * padding,
        "attention_mask": [1] * len(real) + [0] * padding,
        "labels": labels, "prompt_tokens": len(prefix),
        "real_tokens": len(real), "supervised_tokens": len(target),
    }
    validate_masks(record, target)
    return record


def validate_masks(record, target):
    prefix = record["prompt_tokens"]
    real = record["real_tokens"]
    labels = record["labels"]
    require(all(len(record[field]) == 1024 for field in ("input_ids", "attention_mask", "labels")), "Wrong fixed shape")
    require(record["attention_mask"] == [1] * real + [0] * (1024 - real), "Wrong right padding")
    require(labels[:prefix] == [-100] * prefix and labels[real:] == [-100] * (1024 - real), "Prompt/pad label leakage")
    require([token for token in labels[1:] if token != -100] == target, "Causal-shift target mismatch")
    require(labels[prefix:real] == record["input_ids"][prefix:real] == target, "Input/target mismatch")


def build_records(tokenizer, families):
    prepared = {form: [] for form in ("E", "R", "C")}
    for family in families:
        paired = {form: encode_record(tokenizer, family, form) for form in prepared}
        targets = [[token for token in paired[form]["labels"] if token != -100] for form in prepared]
        require(targets[0] == targets[1] == targets[2], "Paired supervised targets differ")
        for form in prepared:
            prepared[form].append(paired[form])
    return {
        arm: [record for index in range(16) for record in (prepared["E"][index], prepared[arm][index])] * 3
        for arm in ("C", "R")
    }


def self_check():
    class FakeTokenizer:
        all_special_tokens = ["<EOS>", "<PAD>"]
        eos_token_id = 7
        pad_token_id = 7

        def apply_chat_template(self, messages, **settings):
            require(settings["enable_thinking"] is False, "Thinking enabled")
            return [8] + [20 + ord(char) for char in messages[-1]["content"]]

        def encode(self, text, **settings):
            return [20 + ord(char) for char in text]

    families = [{"family_id": f"smoke-{index}", "source_family_id": f"source-{index}",
                 "split_role": "SMOKE_TRAIN", "provenance": "in-memory contract fixture, not data",
                 "source_license": "fixture", "completion": "FINAL: 1",
                 "forms": {form: f"{form} fixture {index}" for form in ("E", "R", "C")}}
                for index in range(16)]
    pilot = [{"family_id": f"pilot-{index}", "source_family_id": f"pilot-source-{index}"} for index in range(30)]
    excluded = sorted(set().union(*(identifiers(record) for record in families + pilot)))
    manifest = {"audit": {"approved": True, "reviewer": "fixture", "unresolved_matches": 0},
                "PILOT_EVAL": pilot, "RETIRED_DRAFT": [], "CONFIRM_TRAIN": [], "FINAL_TEST": [],
                "development_exclusion_ids": excluded}
    ordered = validate_data({"version": "fixture", "families": families}, manifest)
    prepared = build_records(FakeTokenizer(), ordered)
    for records in prepared.values():
        require(len(records) == 96 and sum(len(record["input_ids"]) for record in records) == 98304, "Workload count")
        require(records[:32] == records[32:64] == records[64:], "Repeat order")
        require(sum(token != -100 for token in records[0]["labels"]) == records[0]["supervised_tokens"], "EOS/PAD masking")
    checks = 0
    mutations = [lambda copy: copy["families"].pop(),
                 lambda copy: copy["families"][1].update(source_family_id="source-0"),
                 lambda copy: copy["families"][0].update(split_role="PILOT_EVAL")]
    for mutation in mutations:
        altered = json.loads(json.dumps({"version": "fixture", "families": families}))
        mutation(altered)
        try:
            validate_data(altered, manifest)
        except ValueError:
            checks += 1
    require(checks == len(mutations), "Data rejection test failed")
    for kind in ("prompt", "pad", "target"):
        altered = json.loads(json.dumps(prepared["C"][0]))
        position = {"prompt": 1, "pad": 1023, "target": altered["prompt_tokens"]}[kind]
        altered["labels"][position] = 123
        target = [token for token in prepared["C"][0]["labels"] if token != -100]
        try:
            validate_masks(altered, target)
        except ValueError:
            checks += 1
    require(checks == 6, "Mask rejection test failed")
    print("PASS: model-free count/order, shared targets, EOS=PAD, mask and split contracts")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Model-free smoke-test input checks; never trains or downloads models.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("self-check", help="Run synthetic in-memory protocol contract checks")
    validate = commands.add_parser("validate", help="Validate audited input identities and split exclusions")
    validate.add_argument("--inputs", type=Path, required=True)
    validate.add_argument("--splits", type=Path, required=True)
    validate.add_argument("--revision", required=True, help="Pinned model/tokenizer commit SHA")
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "self-check":
            self_check()
            return
        validate_revision(arguments.revision)
        data = read_json(arguments.inputs)
        manifest = read_json(arguments.splits)
        families = validate_data(data, manifest)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.exit(1, f"Preflight failed: {error}\n")
    print(json.dumps({
        "status": "input_contracts_passed",
        "model": MODEL,
        "revision": arguments.revision,
        "smoke_data_version": data["version"],
        "smoke_families": len(families),
        "pilot_family_identities": len(manifest["PILOT_EVAL"]),
        "inputs_sha256": file_digest(arguments.inputs),
        "splits_sha256": file_digest(arguments.splits),
        "not_verified": [
            "Model revision existence and tokenizer compatibility",
            "Human review accuracy and semantic near-duplicates",
            "Real-tokenizer lengths, masks, and target equality",
            "GPU fit, training integrity, and cold checkpoint resume",
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
