"""Completion-only labels for the D021 smoke test; no model dependencies."""


def build_example(tokenizer, instruction, question, solution, *, max_length=1024):
    """Return unpadded IDs, labels, and the first supervised ``boundary_index``.

    The rendered generation prompt, including its empty think block, is masked.
    Encode the completion separately so its IDs do not depend on the question's
    language or the prompt/completion tokenization boundary. Never truncate.
    """
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": question},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False,
    )
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False, truncation=False)
    target_ids = tokenizer.encode(
        solution + "<|im_end|>", add_special_tokens=False, truncation=False,
    )
    input_ids = prompt_ids + target_ids
    if len(input_ids) > max_length:
        raise ValueError(
            f"Example has {len(input_ids)} tokens, exceeding max_length={max_length}; "
            "no truncation allowed"
        )
    boundary_index = len(prompt_ids)
    return {
        "input_ids": input_ids,
        "labels": [-100] * boundary_index + target_ids,
        "boundary_index": boundary_index,
    }


def assert_matched_targets(examples_by_form):
    """Assert identical supervised IDs for one family's E, R, and C examples."""
    if set(examples_by_form) != {"E", "R", "C"}:
        raise AssertionError("Expected exactly the E, R, and C forms for one family")
    targets = {
        form: [token for token in example["labels"] if token != -100]
        for form, example in examples_by_form.items()
    }
    if not targets["E"] == targets["R"] == targets["C"]:
        raise AssertionError("Supervised target token IDs differ across E/R/C")
