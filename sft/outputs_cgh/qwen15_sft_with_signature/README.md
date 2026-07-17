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
- name: qwen15_sft_with_signature
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# qwen15_sft_with_signature

This model is a fine-tuned version of [./Qwen1.5-0.5B-Chat](https://huggingface.co/./Qwen1.5-0.5B-Chat) on the code_sft_train_with_signature dataset.
It achieves the following results on the evaluation set:
- Loss: 0.6978
- Accuracy: 0.8375

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
| 0.7059        | 0.0955 | 200  | 0.7569          | 0.8186   |
| 1.1227        | 0.1910 | 400  | 0.7414          | 0.8218   |
| 1.1039        | 0.2866 | 600  | 0.7350          | 0.8231   |
| 0.8889        | 0.3821 | 800  | 0.7213          | 0.8263   |
| 0.8022        | 0.4776 | 1000 | 0.7137          | 0.8271   |
| 0.9947        | 0.5731 | 1200 | 0.7126          | 0.8266   |
| 0.8729        | 0.6687 | 1400 | 0.7039          | 0.8294   |
| 0.7923        | 0.7642 | 1600 | 0.6972          | 0.8307   |
| 0.6281        | 0.8597 | 1800 | 0.6936          | 0.8314   |
| 0.7062        | 0.9552 | 2000 | 0.6882          | 0.8323   |
| 0.6179        | 1.0506 | 2200 | 0.6945          | 0.8312   |
| 0.6239        | 1.1461 | 2400 | 0.6932          | 0.8305   |
| 0.4158        | 1.2417 | 2600 | 0.6926          | 0.8341   |
| 0.4833        | 1.3372 | 2800 | 0.6891          | 0.8328   |
| 0.5455        | 1.4327 | 3000 | 0.6855          | 0.8345   |
| 0.5594        | 1.5282 | 3200 | 0.6792          | 0.8348   |
| 0.6736        | 1.6238 | 3400 | 0.6781          | 0.8357   |
| 0.5903        | 1.7193 | 3600 | 0.6736          | 0.8371   |
| 0.5517        | 1.8148 | 3800 | 0.6739          | 0.8374   |
| 0.4153        | 1.9103 | 4000 | 0.6670          | 0.8384   |
| 0.3593        | 2.0057 | 4200 | 0.6720          | 0.8395   |
| 0.5267        | 2.1013 | 4400 | 0.7007          | 0.8373   |
| 0.5230        | 2.1968 | 4600 | 0.7033          | 0.8354   |
| 0.3155        | 2.2923 | 4800 | 0.6967          | 0.8353   |
| 0.2779        | 2.3878 | 5000 | 0.6998          | 0.8359   |
| 0.5430        | 2.4833 | 5200 | 0.7000          | 0.8368   |
| 0.4140        | 2.5789 | 5400 | 0.6977          | 0.8371   |
| 0.4933        | 2.6744 | 5600 | 0.6983          | 0.8372   |
| 0.4635        | 2.7699 | 5800 | 0.6972          | 0.8375   |
| 0.3115        | 2.8654 | 6000 | 0.6977          | 0.8374   |
| 0.4393        | 2.9610 | 6200 | 0.6978          | 0.8375   |
| 0.3854        | 3.0    | 6282 | 0.6978          | 0.8375   |


### Framework versions

- Transformers 5.6.0
- Pytorch 2.5.1+cu124
- Datasets 4.0.0
- Tokenizers 0.22.2
