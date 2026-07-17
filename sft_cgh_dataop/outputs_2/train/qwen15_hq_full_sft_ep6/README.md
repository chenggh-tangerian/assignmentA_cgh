---
library_name: transformers
license: other
base_model: ./sft_cgh_dataop/outputs/train/qwen15_hq_full_sft
tags:
- llama-factory
- full
- generated_from_trainer
metrics:
- accuracy
model-index:
- name: qwen15_hq_full_sft_ep6
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# qwen15_hq_full_sft_ep6

This model is a fine-tuned version of [./sft_cgh_dataop/outputs/train/qwen15_hq_full_sft](https://huggingface.co/./sft_cgh_dataop/outputs/train/qwen15_hq_full_sft) on the code_sft_train_hq dataset.
It achieves the following results on the evaluation set:
- Loss: 0.9420
- Accuracy: 0.8126

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 5e-06
- train_batch_size: 2
- eval_batch_size: 2
- seed: 42
- gradient_accumulation_steps: 4
- total_train_batch_size: 8
- optimizer: Use OptimizerNames.ADAMW_TORCH with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: cosine
- lr_scheduler_warmup_steps: 0.03
- num_epochs: 3.0
- mixed_precision_training: Native AMP

### Training results

| Training Loss | Epoch  | Step | Validation Loss | Accuracy |
|:-------------:|:------:|:----:|:---------------:|:--------:|
| 0.2967        | 0.3751 | 200  | 0.7525          | 0.8200   |
| 0.3325        | 0.7501 | 400  | 0.7710          | 0.8188   |
| 0.1573        | 1.1238 | 600  | 0.8602          | 0.8151   |
| 0.1821        | 1.4988 | 800  | 0.8512          | 0.8163   |
| 0.2574        | 1.8739 | 1000 | 0.8545          | 0.8152   |
| 0.1055        | 2.2475 | 1200 | 0.9349          | 0.8112   |
| 0.1493        | 2.6226 | 1400 | 0.9420          | 0.8125   |
| 0.1242        | 2.9977 | 1600 | 0.9420          | 0.8125   |
| 0.1242        | 3.0    | 1602 | 0.9420          | 0.8126   |


### Framework versions

- Transformers 5.6.0
- Pytorch 2.5.1+cu124
- Datasets 4.0.0
- Tokenizers 0.22.2
