# Colab notebooks

Upload a notebook to https://colab.research.google.com (File → Upload notebook), choose **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. A results ZIP downloads at the end; send it to the team.

## The real experiment (pilot)

`test1_pilot/Hinglish_Math_Test1_Pilot_Colab.ipynb` runs the reviewed pilot. **Run it only after the human-reviewed dataset is frozen.** Set `MODE='reviewed'`, `BACKEND='huggingface'`, and run once per model with its own `RUN_NAME`: `MODEL_ID='Qwen/Qwen3-4B'` (primary) `MODEL_ID='Qwen/Qwen3-8B'` (second, decision D030) and `MODEL_ID='meta-llama/Llama-3.2-3B-Instruct'` (third, cross-family, decision D032; needs the HF token secret).

## Model screening (`model_screening/`)

Each notebook runs the same 36 excluded practice prompts with the frozen prompt, decoding and scorer. A model joins the pilot only with ≤3/36 format failures (decision D028).

| Notebook | Result | Status |
|---|---|---|
| `ModelTest_Qwen3-4B.ipynb` | 0/36 failures | ✅ Done: primary pilot model |
| `ModelTest_Qwen3-8B.ipynb` | 0/36 failures | ✅ Done: second pilot model |
| `ModelTest_Qwen3-1.7B.ipynb` | 36/36 (copies the instruction) | ✅ Done: excluded |
| `ModelTest_Phi-4-mini.ipynb` | 14/36 (inline answer, R looping) | ✅ Done: excluded |
| `ModelTest_Granite-3.3-2B.ipynb` | 36/36 (remarks after answer) | ✅ Done: excluded |
| `ModelTest_Gemma-3-4B.ipynb` | GPU crash under FP16 | ✅ Done: excluded |
| `ModelTest_Llama-3.2-3B.ipynb` | 2/36 failures; E 12, R 9, C 9 | ✅ Done: third pilot model |

Results and analyses: `research/fmt2_*`. Rebuild these notebooks with `python3 -B secondary_analysis/build_format_notebook.py`.
