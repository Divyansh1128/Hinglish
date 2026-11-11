# Responsible NLP checklist — evidence-based draft, 11 November 2026

AUTHOR-ONLY. Adapt to the exact current OpenReview questions. Source: https://aclrollingreview.org/responsibleNLPresearch/ (checked 11 November). A candid No/Partial with an explanation is preferable to an unsupported Yes. This is a form aid, not an ethics approval.

| Item | Answer supported by the package | Evidence / qualification |
| --- | --- | --- |
| A1 Limitations | Yes | Limitations: sample size, review depth, AI drafting, C definitions, format-based selection, script control, seed uncertainty and training recipe |
| A2 Risks | Yes | Ethics: avoid generalizing model behaviour to Hindi speakers; research-only artifacts; reviewer identity protection |
| A3 Summary of claims, if asked | Yes | Abstract and §1, including the negative training follow-up |
| B1 Creators cited | Yes for principal artifacts | §2, §4, references: benchmarks, Qwen3, QLoRA, Meta Llama 3.2 model card. Stack versions in Appendix D |
| B2 Licenses | Yes | Ethics and supplement: authored code MIT/data CC BY 4.0; Qwen Apache 2.0; Llama 3.2 Community License; weights not redistributed |
| B3 Intended use | Yes | Ethics: research evaluation, not deployment |
| B4 Privacy checks | Yes, bounded | Invented names in questions; automated identifier/credential scan of release files and PDF; no personal returned reviewer files. No claim that a regex proves absence of all sensitive content |
| B5 Documentation | Yes | §3 and supplement: E/R/C, topics, borrowing policy and differing cohort definitions |
| B6 Data statistics | Yes | §3, §6, Appendix C: 70/24-family pilots, TRAIN 160, DEV 40, FINAL_TEST 100 |
| C1 Compute/infrastructure | Partial | T4 and model sizes §4; Appendix D and supplement report ~3 training-update GPU-hours and 8.291 measured final-generation GPU-hours. Loading, DEV, screening and engineering costs are excluded; no complete project-wide total available |
| C2 Setup/hyperparameters | Yes | §4, §7, Appendices A/C/D; frozen plan included. DEV never selected checkpoints or changed the recipe |
| C3 Statistics | Yes | §6, §7, Appendix C: family intervals, three paired seeds, exact decision rule. Interval conditional on trained checkpoints; no claim to cover seed variance |
| C4 Software/model versions | Yes | Appendix D and supplement execution metadata with immutable model/tokenizer revisions; frozen source hashes |
| D1 Full instructions | Yes for included original reviewer/audit workflows; partial across all later workflows | Supplement original stage1/stage2 interfaces and audit instructions. Do not claim the full history of every later review interaction is included |
| D2 Recruitment/payment | Partial; PAYMENT UNCONFIRMED | User states reviewers were teammates. No payment answer was supplied. Do not label them unpaid without confirmation; fill the actual payment arrangement before submission |
| D3 Consent | Yes, author-attested | User confirmed all gave consent on 11 November; existing manuscript records consent covering data release. Personal consent records are not distributed |
| D4 Ethics-board approval/exemption | UNCONFIRMED | No institutional determination was supplied in this packaging session. Obtain/report the actual status; do not claim approval, exemption, or “not required” on the basis of teammate consent |
| D5 Demographics | Partial | Hindi–English bilingual teammates; no further demographics reported. Do not infer age, gender or proficiency certifications |
| E1 AI assistance | Yes | Ethics separates AI drafting, AI-assisted human review, pre-tagging, writing/coding; unverified original judgments excluded. Human acceptance/label provenance is reported |

Before sending: resolve payment and institutional-status answers; enter truthful form explanations. Confirm final author approval, student-first-author eligibility and required OpenReview profile fields. These facts cannot be supplied by a software check. Do not upload this author-only checklist as the anonymous supplement.
