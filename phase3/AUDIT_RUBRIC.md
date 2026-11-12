# Phase-3 audit contract

Use the frozen Pilot-B rubric in `results/pilot_b/audit/AUDIT_INSTRUCTIONS.md`.
Before tagging, clarify: labelled equations without an English explanatory proposition
are `no_explanation`. Do not infer explanation quality from correctness or output length.

After the complete sealed evaluation passes the outcome-unsealing gate and the frozen
primary analysis runs, audit every strict-incorrect C generation of every retained
ER and EC seed. Denominators are all C generations per arm. Independent Claude Opus
and GPT taggers work blind to each other's tags and to arm/seed where feasible.
A human checks every audited output; retain both tag sets, agreement, all human
returns, disagreements, unresolved rows and final decisions. No sampling or rule
propagation replaces individual checks. Audit tags never replace strict scores or
establish causal mechanisms. Freeze/hash the packet and all returns for release.
