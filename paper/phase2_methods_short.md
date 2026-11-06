**Ongoing pre-registered follow-up.** We are testing whether Hinglish training improves Hinglish (C) accuracy relative to Romanized Hindi (R). E+E, E+R and E+C pair English (E) with the named form, supervising identical English solutions. Qwen3-4B QLoRA uses NF4/FP16, rank 16, alpha 32, dropout 0.05, 60 AdamW updates over three passes, and learning rate 10⁻⁴ with six-update warm-up and cosine decay to 10⁻⁵. Seeds 11/22/33 pair initialization and exposure order. SHA-256-frozen splits contain 160 TRAIN, 40 sanity-only DEV and 100 FINAL_TEST families. The sole confirmatory estimand, Δ_C, is seed-averaged E+C minus E+R strict accuracy on C. Paired family bootstrapping uses 10,000 resamples, seed 101, and 95% percentile intervals conditional on checkpoints; Wilson intervals describe checkpoint accuracies. With bounds [L,U] in percentage points, labels are useful support (L>5), support (0<L≤5), informative null (L≤0≤U<5), harm (U<0), or inconclusive (L≤0,U≥5); degeneracy overrides claims. Descriptive English-retention flags use L>−2, U<0 and U<−2; primary support plus U<−2 flags EC–EE/EC–unchanged trade-offs. Typed training infrastructure failures allow one identical restart, then whole-triplet reserves 44/55; numerical/protocol failures halt. Evaluation allows one infrastructure retry, excluding OOM; generated answers are never retried. Unresolved generations suppress confirmation. FINAL_TEST evaluation requires committed adapter/code/hash freezes; outputs remain sealed until completion. Historical construction exposure and unattended test-access deviations are disclosed in the amendments. Returned seed-11 adapters produce shorter, less accurate DEV answers than the unchanged model (D050 and training log), consistent with shared terse targets: a descriptive design limitation, not grounds for tuning. No held-out result is reported.

<!-- Editorial provenance, not part of the camera-ready paragraph.
Binding sources: phase2/PREREGISTRATION.md sections 1--8,10--13 with
Amendments 1--3; phase2/IMPLEMENTATION_MANIFEST.md; docs/DECISIONS.md
D040--D050; results/phase2/baseline_dev/README.md;
results/phase2/train/README.md. Amendments override the original plan.
Full mechanics, flags, limitations and data hashes are in the companion
report/phase2_methods_draft.tex; no FINAL_TEST data were opened.
Data SHA-256 (transcribed from PREREGISTRATION section 1):
TRAIN A: b9656a8c41af2a795bce9c131efc6a5efc652df78368d14fb7720fd985883666
TRAIN B: c975fe12459df6160effc5aeb0087f94666ba0b49778c3d827a67bb923ff35bd
DEV: e741c1652f5b3dcaebc78d9dd9d7c31fdf4417306fbb2f0862149f27f858f28b
FINAL_TEST: da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46
TODO: supply the FT057 verification-exception disclosure from authorized
non-sealed provenance when integrating the full access-history disclosure;
the binding sources name the exception but do not explain it.
-->
