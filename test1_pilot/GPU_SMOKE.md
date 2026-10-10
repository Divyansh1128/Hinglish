# Next step: actual-model GPU smoke check

Open Hinglish_Math_Qwen_GPU_Smoke_Colab.ipynb in a fresh Colab session, select T4 GPU, and run all cells. No dataset upload is required. Defaults run Qwen3-4B on one format-only fixture and six included synthetic E/R/C inputs. This tests loading and inference only; it is not the reviewed 30-family research pilot and performs no training.

Return demo-qwen-gpu-v2_results.zip and the executed notebook. If loading or setup fails, still run the final export cell and return demo-qwen-gpu-v2_diagnostics.zip. No model substitution or CPU fallback is performed. USE_DRIVE is optional; a stable run name and matching stack are required for resume.

This is a separate notebook/storage path; the original pilot notebook and old demo are unchanged. The embedded package is generated from maintained Test 1 sources by build_gpu_smoke.py, replacing the bitsandbytes pin in both dependency file and backend check with 0.50.2. The previous runtime recorded torch 2.11.0+cu130; stable documentation lists CUDA 13 builds and SM75 support: https://huggingface.co/docs/bitsandbytes/v0.50.2/en/installation . The compatibility candidate is explicit; successful execution on the actual GPU remains unverified.

Verification on 10 October 2026: nbformat schema and all Python cells passed; both diagnostic-only and simulated-success export branches passed, including all ZIP checksums and the embedded pin consistency check. Tests bypassed GPU installation/model loading and used fake generation only. No actual GPU feasibility result was produced. Failure diagnostics export stage/exception class rather than arbitrary exception text, which might contain credentials.

After this engineering check, prepare and independently review the 30-family dataset and split manifest before the real research pilot. The asynchronous reviewer-availability question is independent of the GPU smoke run.

The user's version-1 smoke run has now passed actual Qwen/T4 inference. No rerun is required merely to establish this short check. Version-2 repairs count-unit fixture metadata and uses a new run name; fraction suffix rejection remains unchanged. Main pilot dependencies now adopt the tested bitsandbytes pin. Original files remain in archive/.
