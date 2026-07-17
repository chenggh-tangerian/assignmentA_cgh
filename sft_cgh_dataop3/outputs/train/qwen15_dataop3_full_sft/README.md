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
- name: qwen15_dataop3_full_sft
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# qwen15_dataop3_full_sft

This model is a fine-tuned version of [./Qwen1.5-0.5B-Chat](https://huggingface.co/./Qwen1.5-0.5B-Chat) on the code_sft_train dataset.
It achieves the following results on the evaluation set:
- Loss: 0.6086
- Accuracy: 0.8551

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
| 0.7542        | 0.0796 | 100  | 0.6379          | 0.8425   |
| 0.6566        | 0.1592 | 200  | 0.6355          | 0.8413   |
| 0.6422        | 0.2388 | 300  | 0.6281          | 0.8425   |
| 0.6474        | 0.3184 | 400  | 0.6168          | 0.8450   |
| 0.6797        | 0.3980 | 500  | 0.6154          | 0.8457   |
| 0.6463        | 0.4776 | 600  | 0.6110          | 0.8470   |
| 0.6168        | 0.5572 | 700  | 0.6027          | 0.8456   |
| 0.6499        | 0.6368 | 800  | 0.6011          | 0.8486   |
| 0.6593        | 0.7164 | 900  | 0.5980          | 0.8491   |
| 0.6503        | 0.7960 | 1000 | 0.5973          | 0.8495   |
| 0.5401        | 0.8756 | 1100 | 0.5914          | 0.8506   |
| 0.6220        | 0.9552 | 1200 | 0.5825          | 0.8520   |
| 0.4389        | 1.0342 | 1300 | 0.5951          | 0.8518   |
| 0.4534        | 1.1138 | 1400 | 0.5958          | 0.8517   |
| 0.4133        | 1.1934 | 1500 | 0.5914          | 0.8524   |
| 0.4097        | 1.2730 | 1600 | 0.5903          | 0.8536   |
| 0.5042        | 1.3526 | 1700 | 0.5863          | 0.8531   |
| 0.4332        | 1.4322 | 1800 | 0.5852          | 0.8531   |
| 0.4435        | 1.5118 | 1900 | 0.5835          | 0.8550   |
| 0.3998        | 1.5914 | 2000 | 0.5826          | 0.8530   |
| 0.4020        | 1.6710 | 2100 | 0.5801          | 0.8552   |
| 0.5133        | 1.7506 | 2200 | 0.5778          | 0.8552   |
| 0.4021        | 1.8302 | 2300 | 0.5720          | 0.8554   |
| 0.5009        | 1.9099 | 2400 | 0.5734          | 0.8548   |
| 0.4420        | 1.9895 | 2500 | 0.5687          | 0.8558   |
| 0.3092        | 2.0685 | 2600 | 0.6017          | 0.8544   |
| 0.2433        | 2.1481 | 2700 | 0.6097          | 0.8536   |
| 0.4112        | 2.2277 | 2800 | 0.6082          | 0.8545   |
| 0.3111        | 2.3073 | 2900 | 0.6086          | 0.8550   |
| 0.3330        | 2.3869 | 3000 | 0.6083          | 0.8557   |
| 0.3057        | 2.4665 | 3100 | 0.6083          | 0.8551   |
| 0.2945        | 2.5461 | 3200 | 0.6077          | 0.8548   |
| 0.3139        | 2.6257 | 3300 | 0.6107          | 0.8548   |
| 0.2865        | 2.7053 | 3400 | 0.6087          | 0.8552   |
| 0.2797        | 2.7849 | 3500 | 0.6081          | 0.8547   |
| 0.2575        | 2.8645 | 3600 | 0.6086          | 0.8549   |
| 0.3209        | 2.9441 | 3700 | 0.6087          | 0.8551   |
| 0.2953        | 3.0    | 3771 | 0.6086          | 0.8551   |


### Framework versions

- Transformers 5.6.0
- Pytorch 2.5.1+cu124
- Datasets 4.0.0
- Tokenizers 0.22.2
