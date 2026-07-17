---
library_name: transformers
license: other
base_model: ./Qwen1.5-0.5B-Chat
tags:
- llama-factory
- full
- generated_from_trainer
metrics:
- accuracy
model-index:
- name: qwen15_hq_full_sft
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# qwen15_hq_full_sft

This model is a fine-tuned version of [./Qwen1.5-0.5B-Chat](https://huggingface.co/./Qwen1.5-0.5B-Chat) on the code_sft_train_hq dataset.
It achieves the following results on the evaluation set:
- Loss: 0.7238
- Accuracy: 0.8246

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 1e-05
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
| 0.7220        | 0.3751 | 200  | 0.7084          | 0.8178   |
| 0.7675        | 0.7501 | 400  | 0.6907          | 0.8200   |
| 0.4112        | 1.1238 | 600  | 0.6981          | 0.8240   |
| 0.4786        | 1.4988 | 800  | 0.6854          | 0.8266   |
| 0.5522        | 1.8739 | 1000 | 0.6783          | 0.8276   |
| 0.2884        | 2.2475 | 1200 | 0.7260          | 0.8243   |
| 0.3355        | 2.6226 | 1400 | 0.7259          | 0.8234   |
| 0.2956        | 2.9977 | 1600 | 0.7238          | 0.8245   |
| 0.2956        | 3.0    | 1602 | 0.7238          | 0.8246   |


### Framework versions

- Transformers 5.6.0
- Pytorch 2.5.1+cu124
- Datasets 4.0.0
- Tokenizers 0.22.2
