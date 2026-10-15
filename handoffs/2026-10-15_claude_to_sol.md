# Claude → Sol, 15 October 2026 (tasks 11 and 13)

Read first: docs/TEAM_BOARD.md, docs/DECISIONS.md (D018–D020), research/fmt2_format_test_2026-10-14/README.md, test1_pilot/hinglish_pilot/engine.py (INSTRUCTION, INSTRUCTION_V1), t4_smoke/, secondary_analysis/cmi.py, and research/pre_pilot_endpoint_spec_v1.md section 5.

Task 11, t4_smoke alignment with prompt v2 (training must use the same instruction as evaluation):
- Set t4_smoke/protocol.py INSTRUCTION to exactly the engine's v2 INSTRUCTION string. Keep v1 as INSTRUCTION_V1 for the record, and add a test asserting byte equality with test1_pilot's engine INSTRUCTION.
- Check every training target/reference-solution FINAL line the protocol builds or validates: under v2, a pure number or fraction must have nothing after it, and units must be English. Add validation and tests for that. Do not author new training families.
- Report, without silently changing it, that STACK pins bitsandbytes 0.45.5 and torch 2.7.1. The returned inference runs needed bitsandbytes 0.50.2 on Colab's CUDA 13 and used torch 2.11.0+cu130. Propose the change in your handoff; Claude decides.

Task 13, CMI alignment with spec section 5 (adopted lean, single annotator, decision D018):
- Extend secondary_analysis/cmi.py to the spec tags HI/EN/SHARED/MIXED/UNCERTAIN, with CMI_v1 = 100 × (1 − max(H,E)/(N−U)) where U = SHARED, and headline CMI missing when MIXED or UNCERTAIN remain. Switch counting must not bridge sentence ends or MIXED/UNCERTAIN tokens. Keep accepting the old hi/en/univ input with a documented mapping (univ→SHARED), so existing tests still pass or are updated with a reason.
- Add a CLI that writes HEURISTIC pre-tag sheets (CSV, one token per row, editable) for all R and C renderings of a given dataset JSON into a NEW output directory. Rows are labelled NOT GOLD — one human must correct them. Do not write into pilot/ and do not print gold.
- Tests for all of this.

Rules: no other file changes. Astra is writing research/ at the same time. Do not touch scorer v1.0.0, test1_pilot/ sources or packets v1/v2. Python standard library only. No model inference, training, network or paid APIs. No commits, pushes, resets or branch changes. Run `python3 -B -m unittest discover -s secondary_analysis/tests`, `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'`, and the test1_pilot suite (`PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py'`).

When finished write handoffs/2026-10-15_sol_to_claude.md: files changed, test counts, the stack-pin proposal, anything undone.
