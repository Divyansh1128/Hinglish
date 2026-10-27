# T4 smoke-test preparation

Status (27 Oct 2026): the D021 GPU runner `train_smoke.py` and its Colab
notebook (`../colab_notebooks/training_smoke/TrainSmoke_Qwen3-4B.ipynb`, built
by `../colab_notebooks/build_training_smoke_notebook.py`) exist and pass
model-free tests. They have **not run on a GPU**, so no hardware feasibility
result is established. The governing decision is D021 in `../docs/DECISIONS.md`.

## D021 training smoke (`train_smoke.py`)

- Stack: Colab torch 2.11.0+cu130 (recorded, not reinstalled), transformers
  4.51.3, bitsandbytes 0.50.2, PEFT 0.15.2; project-owned loop, no TRL.
- Data: 16 TRAIN families (8 per frozen TRAIN file, hash-ranked with seed
  `D021-smoke-2026-10-27`; see `SELECTION_RULE`). No DEV or FINAL_TEST file is read.
- Labels via `labels.py`; arms E+E, E+R, E+C with identical English targets.
- Per arm: updates 1-4, save, new-process reload and state/probe check, updates
  5-6. Then a 32-update E+C stability probe. `decide` prints the D021 go/no-go.
- These adapters are discarded: never evaluate them.

The older `protocol.py` preflight below targets the 2.7.1/0.45.5 stack in
`requirements.txt` (the D021 fallback stack) and remains unchanged.

## Local checks

Run from the project root with Python 3; these commands use the standard
library only. Do not install the CUDA requirements to run these checks.

```sh
python3 -B t4_smoke/protocol.py self-check
python3 -B -m unittest discover -s t4_smoke -p 'test_*.py' -v
python3 -B -m unittest discover -s pilot/scripts -p 'test_*.py' -v
python3 -B colab_notebooks/build_training_smoke_notebook.py --check
```

The in-memory fixtures are software tests, not authored pilot/smoke datasets
or evidence of human approval. The example JSON files are deliberately empty
and must fail validation.

## Audited input preflight

Supply 16 distinct SMOKE_TRAIN families, each with `family_id`,
`source_family_id`, `split_role`, `provenance`, `source_license`, `completion`,
and `forms` containing E, R, and C text. Each family's English completion is
shared across all three forms. Follow the review packet for human validation.

The split manifest must contain the actual 30 pilot family identities, all
known retired/confirmatory/final-test identities, permanent development
exclusions, and a completed human split audit. Do not set approval fields
merely to make a check pass. IDs cannot detect undisclosed paraphrases or
numerical siblings: those require the human cross-split audit.

```sh
python3 -B t4_smoke/protocol.py validate \
  --inputs /path/to/audited-inputs.json \
  --splits /path/to/audited-splits.json \
  --revision YOUR_IMMUTABLE_40_HEX_MODEL_COMMIT
```

On success the command prints an input-contract report, input hashes, and
explicit unverified checks. It verifies SHA syntax only, not existence of
the model revision. It does not load a tokenizer, download weights, validate
human judgments, or launch training. Errors exit nonzero.

## Remaining

- Run the notebook on a real T4 and review the returned ZIP. Everything that
  touches torch, bitsandbytes, PEFT or the real tokenizer is untested until then.

Dependency compatibility and GPU feasibility remain unverified. Human
review and audited input preparation remain prerequisites for real runs.
Do not evaluate smoke-trained adapters on PILOT_EVAL or report smoke answer
accuracy as evidence of a research effect.
