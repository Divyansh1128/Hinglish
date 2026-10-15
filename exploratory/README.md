# exploratory/ — post-pilot probes (A4, A5)

**Exploratory and post-pilot only.** These inputs must not be run on pilot items before the
pilot's primary run is complete, and their outputs never change the primary endpoints, frozen
items or frozen prompt (`test1_pilot/hinglish_pilot/engine.py` INSTRUCTION). Source:
`research/claude_deep_research/mechanisms_tokenization_2026-10-15.md` (A4, A5).

- `self_translate.py` (A5): frozen `SELF_TRANSLATE_PROMPT_V1` (`self-translate-v1`);
  `build_requests(dataset)` gives one request per R and C rendering (never E);
  `second_stage_dataset(dataset, translations)` swaps in saved translations, suffixes R/C
  rendering_ids with `-ST`, keeps `source_rendering_id`, leaves E and gold unchanged, and raises
  on any missing/empty translation (no E fallback).
- `gloss_probe.py` (A4): `gloss_variants(dataset, lexicon)` replaces ONE lexicon word at a time
  in R renderings (whole-word, case-preserving), ids `<rendering_id>-GL-<word>`. Exact surfaces
  only: `bhaagna` is not matched by `bhaag`. The default lexicon is **UNCONFIRMED**.
  Glossed text is C-like; describe it as an intervention, not a new form.

Standard library only; no inference. Tests: `python3 -B -m unittest discover -s exploratory/tests -v`
