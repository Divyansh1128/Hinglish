# Astra → Claude: endpoint proposal ready for review

14 October 2026. Requested scorer probe ran successfully and reproduced the summary. No model run, training, paid API or implementation adoption occurred. No commits/pushes/resets/branch changes.

Files created by this cycle:
- `research/pre_pilot_endpoint_spec_v1.md` — all endpoint proposals in one document, no pilot gold values.
- `docs/DECISIONS.md` — user decisions versus pending recommendations, plus cycle stopping rule.
- `docs/THESIS_OUTLINE.md` — chapter/evidence map.
- This handoff.

The user explicitly requested the decision log, thesis outline and stopping rule in addition to the endpoint document; those additions follow that instruction despite the earlier narrower “modify no other file” handoff. Existing TEAM_BOARD and Claude-owned review files remain untouched.

Technical disagreement/correction: Rs/Rs. prefixes cannot be fixed with aliases alone in scorer v1; prefix recognition fails before unit lookup. Metadata can address supported suffix aliases. The proposed secondary is deliberately a raw exact scalar diagnostic with no unit conversion or percentage scaling, so it can disagree in either direction with strict correctness. It is not “rescued accuracy”. Terminal-line requirement remains; no arbitrary intermediate-number mining or suffix prose. A frozen diagnostic suffix inventory prevents treating “or seven” as a unit.

Other review points: CMI has0–50 range for two languages, unresolved tags suppress final CMI, borrowed-word treatment is explicitly a project adaptation. No fabricated human language tags. Genuine refusals and regex hits remain distinct; no v1.1 adoption recommended now. Manual and English rubrics are separate from scoring. Twelve proposed fixtures are format elicitation rather than re-numbered pilot problems; no new independent research families claimed.

User responses today: deadlines not supplied (“take your time”); reviewers not done. A01 assignment and revised return date remain unconfirmed. Budget remains undecided from11 October. Neither latest answer approves endpoints or aliases.

Next: Claude reviews the spec, then user/A01 explicitly adopt/revise sections in DECISIONS. Sol implements after that recorded decision under TEAM_BOARD task5. No implementation or GPU execution is claimed. Cycle closes with concrete adoption questions and unresolved human review; do not continue planning indefinitely. Preserve frozen v1/v2/scorer and coordinate the next writer.
