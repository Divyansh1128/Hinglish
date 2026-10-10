# Returned Qwen GPU smoke audit

Integrity passed: exported-file checksums plus config/data/split/source/environment fingerprints and all six attempt-record hashes. Original archive is unchanged.

Qwen3-4B completed real quantized inference on Tesla T4 with bitsandbytes 0.50.2, Transformers 4.51.3, torch 2.11.0+cu130 and Python 3.13.15. All six generations ended without truncation/infrastructure failure. This establishes feasibility for these short engineering inputs only, not training or the full pilot workload.

Original automatic score is 0/6: all outputs were marked invalid_unit. Inspection finds mathematically correct final numbers in all six. The count fixture had blank gold unit despite asking for counters, a fixture-authoring defect. The three fraction outputs append whole/fraction/part; strict dimensionless scoring rejects these suffixes. Preserve these as output-format diagnostics instead of silently accepting arbitrary trailing nouns. The R count explanation also violates the requested English output register.

The post-hoc CSV is a technical diagnostic, not a human review record or confirmatory result. Original score columns and raw archive remain preserved. Only the count unit metadata is corrected in demo-v2, with canonical counters and predefined equivalent count aliases. The scorer and fraction policy remain unchanged. No additional GPU run is needed to conclude the short load/inference check passed.

Next: prepare the 30 independent draft families and blinded reviewer packets; independently review/adjudicate before freezing research inputs. Use the now-tested bitsandbytes pin in the full pilot candidate, and keep checkpoint/decoding/scoring choices explicit. No full training is authorized or implemented here.
