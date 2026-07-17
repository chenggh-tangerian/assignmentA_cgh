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
- name: qwen15_code_full_sft
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# qwen15_code_full_sft

This model is a fine-tuned version of [./Qwen1.5-0.5B-Chat](https://huggingface.co/./Qwen1.5-0.5B-Chat) on the code_sft_train dataset.
It achieves the following results on the evaluation set:
- Loss: 0.7487
- Accuracy: 0.8214

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
| 0.7601        | 0.0955 | 200  | 0.8100          | 0.8036   |
| 1.1576        | 0.1910 | 400  | 0.7949          | 0.8063   |
| 1.1367        | 0.2866 | 600  | 0.7902          | 0.8052   |
| 0.9173        | 0.3821 | 800  | 0.7736          | 0.8107   |
| 0.8423        | 0.4776 | 1000 | 0.7659          | 0.8110   |
| 1.0372        | 0.5731 | 1200 | 0.7639          | 0.8105   |
| 0.9131        | 0.6687 | 1400 | 0.7542          | 0.8132   |
| 0.8262        | 0.7642 | 1600 | 0.7479          | 0.8142   |
| 0.6624        | 0.8597 | 1800 | 0.7442          | 0.8153   |
| 0.7290        | 0.9552 | 2000 | 0.7382          | 0.8156   |
| 0.6603        | 1.0506 | 2200 | 0.7462          | 0.8163   |
| 0.6518        | 1.1461 | 2400 | 0.7467          | 0.8136   |
| 0.4632        | 1.2417 | 2600 | 0.7427          | 0.8169   |
| 0.5153        | 1.3372 | 2800 | 0.7389          | 0.8163   |
| 0.5742        | 1.4327 | 3000 | 0.7353          | 0.8182   |
| 0.5844        | 1.5282 | 3200 | 0.7290          | 0.8197   |
| 0.7036        | 1.6238 | 3400 | 0.7284          | 0.8199   |
| 0.6269        | 1.7193 | 3600 | 0.7241          | 0.8203   |
| 0.5874        | 1.8148 | 3800 | 0.7230          | 0.8214   |
| 0.4448        | 1.9103 | 4000 | 0.7162          | 0.8233   |
| 0.3851        | 2.0057 | 4200 | 0.7216          | 0.8234   |
| 0.5609        | 2.1013 | 4400 | 0.7519          | 0.8211   |
| 0.5558        | 2.1968 | 4600 | 0.7538          | 0.8192   |
| 0.3448        | 2.2923 | 4800 | 0.7489          | 0.8195   |
| 0.3016        | 2.3878 | 5000 | 0.7505          | 0.8205   |
| 0.5633        | 2.4833 | 5200 | 0.7512          | 0.8208   |
| 0.4096        | 2.5789 | 5400 | 0.7485          | 0.8209   |
| 0.5077        | 2.6744 | 5600 | 0.7490          | 0.8215   |
| 0.4835        | 2.7699 | 5800 | 0.7482          | 0.8213   |
| 0.3356        | 2.8654 | 6000 | 0.7486          | 0.8215   |
| 0.4713        | 2.9610 | 6200 | 0.7487          | 0.8213   |
| 0.4166        | 3.0    | 6282 | 0.7487          | 0.8214   |


### Framework versions

- Transformers 5.6.0
- Pytorch 2.5.1+cu124
- Datasets 4.0.0
- Tokenizers 0.22.2
