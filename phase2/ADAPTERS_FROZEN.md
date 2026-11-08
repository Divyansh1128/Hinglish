# Phase-2 adapter freeze (ADAPTERS_FROZEN.md)

Created on 8 November 2026 under PREREGISTRATION.md §11 and Amendment 1 item 12, before any FINAL_TEST access.

- **Retained runs:** all nine attempts (EC/ER/EE × seeds 11/22/33) are attempt 1 and valid: 60/60 steps, 0 scaler skips and not resumed. There were no infrastructure retries and no reserve seeds. S = 3, so the run is **confirmatory**.
- **Source:** `python3 -B t4_smoke/phase2_eval.py freeze-manifest`. Inputs:
  - the train root from the Train notebook's `Phase2_Train_logs.zip` (SHA-256 `808b08412b46f880ca8881ba722ccc9ebbec94bb29ed647b6a7d9f03c48cf03c`; all non-weight checksums OK; weights stay on Drive and are rechecked by the FinalTest gate);
  - the archived baseline `results/phase2/baseline_dev/Phase2_Baseline_DEV_results.zip`.
- **Environment:** every run used torch 2.11.0+cu130 on a Tesla T4. From seed 22 on, Colab's older runtime image was selected; see `results/phase2/train/README.md`.
- **Binding block:** the JSON block below. The FinalTest gate parses it and refuses on any mismatch.

```json
{
  "schema": "phase2-adapters-frozen-3",
  "base_model": "Qwen/Qwen3-4B",
  "base_revision": "1cfa9a7208912126459214e8b04321603b3df60c",
  "implementation_manifest_sha256": "726241c5726aaba2c51fc027866dd572abfc13d02ef9235d1901af87a9f5b43d",
  "exposure_order_file_sha256": "adf43e50c80c59ffa831071558785469b1eda89880c18eefb4f89a9adeb5afb6",
  "base_weight_shards_sha256": {
    "model-00001-of-00003.safetensors": "328a91d3122359d5547f9d79521205bc0a46e1f79a792dfe650e99fc2d651223",
    "model-00002-of-00003.safetensors": "6cd087b316306a68c562436b5492edbcf6e16c6dba3a1308279caa5a58e21ca5",
    "model-00003-of-00003.safetensors": "e4bf436957184f4eeb86a80e9db394503f1f56446b2e6b7edeac5b81470f4ca1"
  },
  "baseline_dev_results_zip_sha256": "a8194ac29cb17711d8e8e526835daacc368fdc4b5265f51d41f96edff347171a",
  "attempt_log_sha256": "b1c08049ba874c14177830cc22e81258f6cd48fe958a77e3968223a14bebf2e9",
  "training_logs_sha256": {
    "EC-s11/attempt-01/dev_eval_results.zip": "93c614ee5769c4f3bbf8981950c3fdf09c9bf8815240d32fe2d61f7828d720d2",
    "EC-s11/attempt-01/dev_eval_implementation.json": "e0932e966bbfb6210ad5de92e794f4d4de48b1d7918dafee82389884926475d4",
    "ER-s11/attempt-01/dev_eval_results.zip": "7355f0d894024b5a8f7a044badf890623e9efbec77109a7a227204050cfdea7c",
    "ER-s11/attempt-01/dev_eval_implementation.json": "a0f95e1c8844585231e85e6e0c36d177cff6630794388c60a87d33363893fa73",
    "EE-s11/attempt-01/dev_eval_results.zip": "6df0515f7d4b7d55342d3e9a429acd60a6805afd4d8e4d0f3a4442037f7e0967",
    "EE-s11/attempt-01/dev_eval_implementation.json": "f1fa44776cb09b7b98946079545db404b9bb83a4992abcff9e66a0c2ee286c4f",
    "EC-s22/attempt-01/dev_eval_results.zip": "1a44056e640e7b8b6225250a4d57c107a35cd40a4f68e036f6f7e82fb837d705",
    "EC-s22/attempt-01/dev_eval_implementation.json": "7911ea1a3e7d0622296a5f9e8a788059e33f62b3c883dff77810f960b6b13dee",
    "ER-s22/attempt-01/dev_eval_results.zip": "3b47da2e46663f48cf325bc8a9ea5bee7b9ce5c600c23d293565f75ba40c307b",
    "ER-s22/attempt-01/dev_eval_implementation.json": "2f71b7285ad2e6d36dd15c9004e9602a50a33d1d760aa5bd9690d83f7bbb7785",
    "EE-s22/attempt-01/dev_eval_results.zip": "f0c1bfeffcd3657fe597be0021d2703935f1030966c3809fd88b932bbd26c3fe",
    "EE-s22/attempt-01/dev_eval_implementation.json": "3aed7ca6ea757ded4038f9a85f27ba223017a86a3f1982b89fb7ea8d4aac33ff",
    "EC-s33/attempt-01/dev_eval_results.zip": "fc52939274b386121c42b512c5c87a94d20ea2c685ee597cc5ba290d9eca6e87",
    "EC-s33/attempt-01/dev_eval_implementation.json": "188770c148ed62112050ca198c23172de09963a4aa60ba2f19bd86ac87474f2a",
    "ER-s33/attempt-01/dev_eval_results.zip": "876655a1ab7e09ded5ff311c6e5e33e994d76ce9ff3baf8c025c046f1732c0d7",
    "ER-s33/attempt-01/dev_eval_implementation.json": "dc40070202ef95a84330f93e027f732dc2600d53ba9c3c481cf06728c43a2b75",
    "EE-s33/attempt-01/dev_eval_results.zip": "708fb12af8942ed4ff420f4f7e8aa4171555305e7b4e1e48a436bf329ed5cb3c",
    "EE-s33/attempt-01/dev_eval_implementation.json": "ab45dd1f6c670ce7b36de05cbb82144406c60eb3fc15100aac7a4402164283e4",
    "EC-s11/attempt-01/train_report.json": "f1ba59aac9fd119aa9f0480697373ef843ed8e7e3f8dce3fa92a516509a7d335",
    "EC-s11/attempt-01/log.txt": "607baf4b09ce0e0eb8a69346c9bc6ac6d124400d87c07b201459964b87457902",
    "EC-s11/attempt-01/attempts.jsonl": "99b824dc5216bcdc9beb77f789be3933d33494484e863c7572761e09da36646b",
    "EE-s11/attempt-01/train_report.json": "c0e92c80fb2ea658fd8571cc01118c0619042305fbafec789096f130c298d63e",
    "EE-s11/attempt-01/log.txt": "b6fa8919dc659a2858d9a4bb5f939a693ceceecfdb13df10d1996a3755547465",
    "EE-s11/attempt-01/attempts.jsonl": "b30969f487709bfa5522db6d57b0eb8423015928009fb5076b41e2d28f3cd510",
    "ER-s11/attempt-01/train_report.json": "d92ec56fd285d646c046a1c4e9566d0628777822189f1763e4a08f0d20cfe030",
    "ER-s11/attempt-01/log.txt": "9578eda2c31f6d826e6c729a70d1116d1dfc65d6c06f06404e8c22f65ae1493a",
    "ER-s11/attempt-01/attempts.jsonl": "d0f343a907b05bae112b674b2197dbea2c8311a04556a42c67c75bea1e8980fa",
    "EC-s22/attempt-01/train_report.json": "b2406cf37711d0c98318832e732daed961771ee5783f1b8ae5416986e240a990",
    "EC-s22/attempt-01/log.txt": "eb83ef21cc875a3ebff2850e1555ca08030c5e1a955b7d1e60143666dee4260a",
    "EC-s22/attempt-01/attempts.jsonl": "afa33933063ef0308f718fe776e9a9a13baeaf9cddf6a588158b06fd7d522323",
    "EE-s22/attempt-01/train_report.json": "72791a1b7a676741a8be28c9a01881d36903bfafcc17c89ee88b405d0dcaa10b",
    "EE-s22/attempt-01/log.txt": "d87c51d62bea4a0c8b3d7f59e8ed5a62ff1881e3bb4acfb38fe470888c7425cf",
    "EE-s22/attempt-01/attempts.jsonl": "f906bc7ab19a8d4855db8214e0c18413b44a86eaec30b2b912a0760618f65068",
    "ER-s22/attempt-01/train_report.json": "abf9d7047d308036d5ddb05537e518b4047a1dd5036c54762f373e5ac7d9f0a1",
    "ER-s22/attempt-01/log.txt": "3d062a10b9197b635d8f422c649efd517aabfc1fb592dc4a144e7f4f865f1cd6",
    "ER-s22/attempt-01/attempts.jsonl": "6ae09c6932d32261b2cc339b91df6727fd4adac856fd3cc52cdd0125254a8089",
    "EC-s33/attempt-01/train_report.json": "9642774caf7b975dc44f24d2d031ac85b6023413f429c40e59740902aa36c49c",
    "EC-s33/attempt-01/log.txt": "0136a4f763d562948124ca639cfaa582f8170629c85c43985a818c89f3d7555b",
    "EC-s33/attempt-01/attempts.jsonl": "7b0f1a2bce3af434ce0f5a779e5a46553b8a9f8ba97ea4f7a867caffa7c14fc9",
    "EE-s33/attempt-01/train_report.json": "167b179efb7664f2abe8d5a5eefb1a707465fd2993c6d9bdc913b0056419565c",
    "EE-s33/attempt-01/log.txt": "466e36cbff8a998e2bd2087b23c590f062cb6d69294217eadc3faf22beedddee",
    "EE-s33/attempt-01/attempts.jsonl": "84f0d051d698a4eb9d4587f225b9ea28ef1bec275e6fd0fb2a2515a0cd42ad2c",
    "ER-s33/attempt-01/train_report.json": "a760356dec82f092a184ab4df4e7524bb92ce3029d76627b7c9d3bb886294fa5",
    "ER-s33/attempt-01/log.txt": "9f11ae19822ab0d93c71a592b9ab524ef7ee4cd8188aebb8ff2e4697c46eb806",
    "ER-s33/attempt-01/attempts.jsonl": "a4bd15017cef79527d522b5622de5e0f4c71e24ab2edf2f5815a88f476ebefc2"
  },
  "retained_seeds": [
    {
      "slot": 11,
      "seed": 11
    },
    {
      "slot": 22,
      "seed": 22
    },
    {
      "slot": 33,
      "seed": 33
    }
  ],
  "S": 3,
  "confirmatory": true,
  "descriptive_only": false,
  "adapters": [
    {
      "arm": "EC",
      "seed": 11,
      "attempt": 1,
      "adapter_model_sha256": "fd29387d920daaad070b753d554ad4f47267d961f694820ee43f9eb576d746e4",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "EE",
      "seed": 11,
      "attempt": 1,
      "adapter_model_sha256": "05da095ec5f94fc4c9612901689d7e46e51d3ab5b0a86d2e25fc0e1f40d9bb74",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "ER",
      "seed": 11,
      "attempt": 1,
      "adapter_model_sha256": "58c0b7ecb7a58d2d0ff4dc984868cc8329795cafeca622c7f5135004582fb722",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "EC",
      "seed": 22,
      "attempt": 1,
      "adapter_model_sha256": "c598ed47b1f8d63539c5e0b885c007108a7fea3fcc089699e885d141d49cbafe",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "EE",
      "seed": 22,
      "attempt": 1,
      "adapter_model_sha256": "034df0667bf2cee9fb1bd118071462321fe46e1dd9f2fb6ace213d57a025018c",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "ER",
      "seed": 22,
      "attempt": 1,
      "adapter_model_sha256": "1732ccf3a7a111d12306bf773b73d00cff993965e2b0ba3c5c46e5a4fc480bf5",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "EC",
      "seed": 33,
      "attempt": 1,
      "adapter_model_sha256": "050a5c6529d0da434e0a8c39b6384d6d43f4c488e7bf52925a88c5c25fc6a7c3",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "EE",
      "seed": 33,
      "attempt": 1,
      "adapter_model_sha256": "cd7b8f010c6b3095d6b08b1a63e22e79877bdeb76253d715b7183ea16e2be749",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    },
    {
      "arm": "ER",
      "seed": 33,
      "attempt": 1,
      "adapter_model_sha256": "6f4907507c73d11757fa5d097a83c5170f4d6f024cb8e808fb06dc5851bb2939",
      "adapter_config_sha256": "ab94f4783c34f7a8f5f0a35351589239008d4036cbef1e58e8727506ec37dac1"
    }
  ]
}
```
