# T4 smoke-test preparation

Status: input validation and model-free tests only. There is no GPU training
runner yet, and no hardware feasibility or research result is established.
The governing draft is `../pilot_review_packet.md`, section 7.

## Local checks

Run from the project root with Python 3; these commands use the standard
library only. Do not install the CUDA requirements to run these checks.

```sh
python3 -B t4_smoke/protocol.py self-check
python3 -B -m unittest discover -s t4_smoke -p 'test_*.py' -v
python3 -B -m unittest discover -s pilot/scripts -p 'test_*.py' -v
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

## Remaining implementation

- Real-tokenizer preflight against the pinned model revision, with no target
  truncation, completion-only masking, and identical paired targets.
- Fresh-process E+C and E+R GPU runners with the frozen recipe, six updates
  per arm, bounded runtime, resource telemetry, and training-integrity checks.
- Cold checkpoint save/reload after update four, restoring adapters,
  optimizer, scaler, RNG, cursor, and configuration before the last two updates.
- Before/after reload state and probe checks, per-arm reports, and the
  review packet's memory/time decision gates.

Dependency compatibility and GPU feasibility remain unverified. Human
review and audited input preparation remain prerequisites for real runs.
Do not evaluate smoke-trained adapters on PILOT_EVAL or report smoke answer
accuracy as evidence of a research effect.
