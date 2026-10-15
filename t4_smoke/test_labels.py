import unittest

from t4_smoke.labels import assert_matched_targets, build_example


class FakeTokenizer:
    """Character tokenizer with atomic Qwen-style special tokens; no downloads."""

    special_tokens = {"<|im_start|>": 1, "<|im_end|>": 2, "<think>": 3, "</think>": 4}

    def __init__(self):
        self.template_calls = []
        self.encode_calls = []

    def apply_chat_template(
        self, messages, *, tokenize, add_generation_prompt, enable_thinking,
    ):
        self.template_calls.append((messages, {
            "tokenize": tokenize,
            "add_generation_prompt": add_generation_prompt,
            "enable_thinking": enable_thinking,
        }))
        prompt = "".join(
            f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"
            for message in messages
        )
        if add_generation_prompt:
            prompt += "<|im_start|>assistant\n"
            if enable_thinking is False:
                prompt += "<think>\n\n</think>\n\n"
        return self.encode(prompt) if tokenize else prompt

    def encode(self, text, *, add_special_tokens=False, truncation=False):
        self.encode_calls.append((text, {
            "add_special_tokens": add_special_tokens, "truncation": truncation,
        }))
        ids = []
        cursor = 0
        while cursor < len(text):
            for marker, token_id in self.special_tokens.items():
                if text.startswith(marker, cursor):
                    ids.append(token_id)
                    cursor += len(marker)
                    break
            else:
                ids.append(1000 + ord(text[cursor]))
                cursor += 1
        return ids

    def decode(self, ids):
        markers = {token_id: marker for marker, token_id in self.special_tokens.items()}
        return "".join(markers[token] if token in markers else chr(token - 1000) for token in ids)


class LabelTests(unittest.TestCase):
    instruction = "Explain in English. End with FINAL."
    solution = "Add 2 and 3.\nFINAL: 5"

    def build(self, question="What is 2 + 3?", **settings):
        return build_example(FakeTokenizer(), self.instruction, question, self.solution, **settings)

    def test_template_and_tokenization_contract(self):
        tokenizer = FakeTokenizer()
        build_example(tokenizer, self.instruction, "Question?", self.solution)
        self.assertEqual(tokenizer.template_calls, [([
            {"role": "system", "content": self.instruction},
            {"role": "user", "content": "Question?"},
        ], {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False})])
        self.assertEqual(len(tokenizer.encode_calls), 2)
        self.assertTrue(tokenizer.encode_calls[0][0].endswith(
            "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        ))
        self.assertEqual(tokenizer.encode_calls[1][0], self.solution + "<|im_end|>")
        for _, settings in tokenizer.encode_calls:
            self.assertEqual(settings, {"add_special_tokens": False, "truncation": False})

    def test_prompt_and_entire_empty_think_block_are_masked(self):
        example = self.build()
        boundary = example["boundary_index"]
        tokenizer = FakeTokenizer()
        prompt_ids = example["input_ids"][:boundary]
        self.assertGreater(boundary, 0)
        self.assertEqual(example["labels"][:boundary], [-100] * boundary)
        think_ids = tokenizer.encode("<think>\n\n</think>\n\n")
        self.assertEqual(prompt_ids[-len(think_ids):], think_ids)
        self.assertEqual(example["labels"][boundary - len(think_ids):boundary], [-100] * len(think_ids))
        self.assertEqual(tokenizer.decode(prompt_ids), (
            f"<|im_start|>system\n{self.instruction}<|im_end|>\n"
            "<|im_start|>user\nWhat is 2 + 3?<|im_end|>\n"
            "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        ))
        self.assertEqual(example["labels"][boundary:], example["input_ids"][boundary:])
        self.assertEqual(tokenizer.decode(example["labels"][boundary:]), self.solution + "<|im_end|>")

    def test_identical_targets_with_different_form_lengths(self):
        examples = {form: self.build(question) for form, question in {
            "E": "What is 2 + 3?", "R": "2 aur 3 ka yog kitna hai?", "C": "2 aur 3 ka sum?",
        }.items()}
        self.assertEqual(len({example["boundary_index"] for example in examples.values()}), 3)
        assert_matched_targets(examples)
        expected = FakeTokenizer().encode(self.solution + "<|im_end|>")
        for example in examples.values():
            self.assertEqual([token for token in example["labels"] if token != -100], expected)

    def test_changed_target_is_rejected(self):
        examples = {form: self.build(form) for form in ("E", "R", "C")}
        examples["R"]["labels"][examples["R"]["boundary_index"]] += 1
        with self.assertRaisesRegex(AssertionError, "target token IDs differ"):
            assert_matched_targets(examples)

    def test_missing_or_extra_forms_are_rejected(self):
        examples = {form: self.build(form) for form in ("E", "R", "C")}
        for forms in ({"E", "R"}, {"E", "R", "C", "X"}, set()):
            with self.subTest(forms=forms), self.assertRaisesRegex(AssertionError, "E, R, and C"):
                assert_matched_targets({form: examples.get(form, examples["E"]) for form in forms})

    def test_combined_overlength_raises_without_truncation(self):
        length = len(self.build()["input_ids"])
        with self.assertRaisesRegex(ValueError, "no truncation allowed"):
            self.build(max_length=length - 1)

    def test_exact_length_limit_is_accepted(self):
        expected = self.build()
        self.assertEqual(self.build(max_length=len(expected["input_ids"])), expected)

    def test_default_length_limit_is_1024(self):
        with self.assertRaisesRegex(ValueError, "max_length=1024"):
            self.build("q" * 1024)

    def test_label_count_equals_solution_tokens_plus_one(self):
        tokenizer = FakeTokenizer()
        for solution in (self.solution, "FINAL: 7/27", ""):
            with self.subTest(solution=solution):
                example = build_example(tokenizer, self.instruction, "Question?", solution)
                labels = [token for token in example["labels"] if token != -100]
                self.assertEqual(len(labels), len(tokenizer.encode(solution)) + 1)
                self.assertEqual(labels[-1], tokenizer.special_tokens["<|im_end|>"])
                self.assertEqual(len(example["input_ids"]), len(example["labels"]))


if __name__ == "__main__":
    unittest.main()
