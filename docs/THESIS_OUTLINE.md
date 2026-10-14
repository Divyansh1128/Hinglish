# Thesis outline and evidence map

14 October 2026. Proposed structure for faculty confirmation, not an institutional template. Keep completed implementation separate from planned experiments; update results chapters only from traceable artifacts.

| Chapter | Main content | Evidence required | Current state / missing evidence |
| --- | --- | --- | --- |
| 1. Introduction and objectives | Language-form question, educational motivation, E/R/C definitions, scoped contribution | Final research questions; clear distinction between input language and output supervision | Scoped; no claim of demonstrated improvement or universal novelty |
| 2. Related work | Multilingual maths, Romanized/code-mixed evaluation and training, exact comparator | Primary-source matrix with versions/locators and bounded search log | Existing audit available; refresh near submission; unresolved artifacts disclosed |
| 3. Research design | Unchanged pilot, eventual E+E/E+R/E+C, matching, estimands, independence and leakage | Adopted protocol, decision log, author/sampling design, checkpoints/configuration hashes | Proposals available; sample, resource budget and final recipe not frozen |
| 4. Dataset and human review | Provenance, 30 draft families, E/R/C authoring, borrowing policy, versions, review/consent | Authentic reviewer JSONs, exposure declarations, adjudication, repairs, lineage/split audit, consent/credit choices, CMI tags and policy | AI drafts/v2 repairs ready; human reviews and acceptance pending; no validated CMI yet |
| 5. System implementation | Notebook, model loading, attempts/resume, strict scorer, exports and optional secondary module | Versioned code, meaningful tests, immutable environment, manifest/hash evidence, analysis adoption | Pilot software and T4 synthetic smoke exist; new secondary module not yet implemented |
| 6. Pilot evaluation | Strict scores, secondary diagnostic if adopted, error/language audit, difficulty, paired uncertainty, runtime | Accepted frozen dataset, complete real run ZIP + executed notebook, raw generations and versioned audit | Reviewed pilot not run. Synthetic fixtures are software evidence only; original invalid-unit scores remain visible |
| 7. Controlled training study | Training feasibility, matched three-arm runs, held-out transfer and English retention | Separate smoke families; finite-gradient/memory/reload results; all seeds/checkpoints; untouched test data; frozen analysis | Not executed. If infeasible by deadline, explicitly label as future work and revise thesis scope with supervisor |
| 8. Discussion and limitations | Format-vs-number distinction, author/seed conditional claims, bias, null/tradeoff interpretation | Results tied to source artifacts, uncertainty and measurement limitations | Statistical simulations available only as planning evidence, not model findings |
| 9. Conclusion and future work | Answer only questions supported by completed experiments; future languages/models/scripts | Traceable outcome statements and remaining work | Cannot assert a training benefit now |
| Appendices | Rubrics, consent template, config, schemas, exclusions, environment, reproducibility instructions | Redacted/pseudonymous reproducibility artifacts with permissions | Existing artifacts partly available; protect raw personal reviews and distinguish proposed forms from signed consent |

## Minimum defensible evidence chain

Question → adopted design → accepted/versioned data → complete run → immutable raw outputs → frozen scoring + declared secondary analysis → audited results → appropriately limited conclusions. AI pre-review cannot replace human acceptance in this chain. A technical GPU smoke is not a reviewed evaluation; a synthetic power/coverage simulation is not a training experiment.

## Writing and deadline policy

Draft background/method/implementation prose now using accurate completed/planned labels. Leave result tables empty or marked “not run”; never insert simulated values as expected model results. Cite code versions and data artifacts, not just screenshots. Faculty must confirm chapter format and scope once actual evaluation dates are supplied. Publication is an aim, not a promised deliverable or accepted result.
