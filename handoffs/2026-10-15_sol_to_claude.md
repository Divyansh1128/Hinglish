# Sol → Claude, 15 October 2026 (tasks 11 and 13)

Assigned code and tests implemented. One integration check remains red: the FMT2 notebook embeds the previous `cmi.py`; rebuilding that notebook is outside this handoff's file scope. No test was weakened or skipped to hide this.

## Files changed by Sol

- `t4_smoke/protocol.py`
- `t4_smoke/test_protocol.py`
- `secondary_analysis/cmi.py`
- `secondary_analysis/tests/test_cmi.py`
- `handoffs/2026-10-15_sol_to_claude.md`

Other working-tree changes belong to concurrent work and were left alone. No changes to research, scorer v1.0.0, Test 1 sources, pilot packets, requirements, stack pins, branches or commits. Python standard library only; no real model inference, training, network or paid API use. Required suites exercise their existing fake backends only.

## Task 11

Smoke `INSTRUCTION` now matches the engine's v2 instruction byte-for-byte; historical v1 is retained as `INSTRUCTION_V1`. Tests compare both UTF-8 byte strings with the engine and confirm encoding uses v2.

`validate_final` runs on every completion and any supplied `reference_solution_en`, both during data validation and before token encoding. It requires exactly one terminal plain FINAL line, a valid number/fraction, and an optional suffix from a conservative English unit/notation vocabulary. It rejects `unitless`, `unit`, `positions`, `whole`, `fraction`, `part`, Hindi suffixes, invented units, annotations/punctuation after bare numbers, prefixes, zero denominators and malformed numeric grouping. Optional `gold.unit` additionally checks whether a suffix must be present or absent. The existing smoke schema has no mandatory gold field; without it the check is syntactic and cannot infer dimensional meaning or mathematical correctness. Unsupported English units need explicit vocabulary review. No training families were authored; additions are in-memory software contract fixtures only.

## Task 13

`analyze_tags`, `cmi` and `switch_points` accept HI/EN/SHARED/MIXED/UNCERTAIN and legacy hi/en/univ (documented mapping: hi→HI, en→EN, univ→SHARED). Results retain `cmi`, `hi`, `en` and add `CMI_v1`, H/E, unresolved counts and `no_language_tokens`. CMI_v1 uses U=SHARED and is `None`/JSON null if any MIXED or UNCERTAIN token remains. Fully resolved N=U gives zero.

Switches skip SHARED only inside a sentence and break at `.`, `?`, `!`, newline boundaries and MIXED/UNCERTAIN. The optional `sentence_ends` argument takes zero-based indices after which to break when whitespace was omitted. Annotation JSON and CSV record these boundaries, including newline gaps; use their `sentence_end` flags when calculating corrected sheets. Plain token pairs cannot recover discarded newline locations themselves.

Dataset CLI:

```sh
python3 -B -m secondary_analysis.cmi \
  --dataset /path/to/dataset.json \
  --output-dir /path/to/NEW_cmi_sheets
```

Writes `R.csv` and `C.csv`, one token per row, covering every R/C question. Accepts the Test 1/FMT2 rendering objects and smoke-style string forms. Rows include NOT GOLD/HEURISTIC labels, false human-corrected status, IDs, raw/NFC text hashes, NFC codepoint offsets, surface, tag, boundaries, rationale, blank tagger/adjudicator identities and supplied draft borrowing policy. Unknowns, unknown capitalized words and homographs (`to`, `the`, `is`, `me`) default to UNCERTAIN; proposed borrowings are not automatically SHARED. One bilingual human must correct the table and freeze the policy. E questions, gold answers and reference solutions are excluded from sheets and dataset CLI output. Existing directories and pilot paths (including resolved symlinks) are refused. The earlier text-to-JSON CLI remains available. Spreadsheet formula prefixes receive a leading apostrophe; strip that one CSV escape prefix when importing text (offsets/hashes refer to the unescaped NFC surface).

Old tests were updated explicitly because switches must no longer bridge periods and unknowns/homographs must no longer default to universal/shared. Legacy input compatibility has its own equivalence test.

## Verification

| Requested command | Result |
| --- | --- |
| `python3 -B -m unittest discover -s secondary_analysis/tests` | 50 run; 49 pass, 1 failure: `test_built_notebook_is_current_and_compiles` |
| `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'` | 12 pass |
| `PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py'` | 22 pass |

CMI-only suite: 19/19 pass. Smoke `self-check` passes. `git diff --check` passes. Read-only integration on the existing v2 draft produced temporary sheets for all 30 R and 30 C renderings: 1,098 R tokens, 994 C tokens; every row remains NOT GOLD and uncorrected. No sheets were saved into pilot or committed as annotation evidence.

Compared the notebook's decoded embedded ZIP with `build_format_notebook.payload()`: the **only differing entry is `secondary_analysis/cmi.py`**. Notebook code still compiles, and all other secondary tests pass. Full final secondary-suite log: `/private/tmp/2026-10-15_sol_secondary_tests.log`.

Frozen scorer SHA-256 remains `c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc`.

## Stack-pin proposal — Claude decides

Unchanged `STACK` still pins **bitsandbytes 0.45.5** and **torch 2.7.1**. Unchanged `requirements.txt` specifies **torch 2.7.1+cu126**, bitsandbytes 0.45.5 and the cu126 wheel index. Returned Colab inference needed **bitsandbytes 0.50.2** on CUDA 13 and used **torch 2.11.0+cu130**.

Proposal: for a Colab CUDA 13 training candidate, align bitsandbytes to 0.50.2 and torch to 2.11.0 (CUDA wheel 2.11.0+cu130), with a matching cu130 wheel index; synchronize STACK/requirements and record runtime versions under a versioned recipe after Claude's decision. Successful inference is not evidence of training, optimizer, PEFT or checkpoint/resume compatibility. The other training dependencies remain pinned; compatibility needs the future human-run training feasibility smoke before adoption. No pin was changed here.

## Undone / integration follow-up

Claude should rebuild `secondary_analysis/Hinglish_FMT2_Format_Test_Colab.ipynb` with `python3 -B secondary_analysis/build_format_notebook.py` and rerun the secondary suite in an integration cycle that authorizes that artifact change. The README's old three-tag CMI description also remains untouched under the file-scope rule; current API/CLI behavior and mapping are documented in `cmi.py` and this handoff. Human annotation/freeze and GPU training remain future gates, not fabricated outcomes of this code task.
