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
- name: qwen15_dataop3_full_sft_ep2500
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# qwen15_dataop3_full_sft_ep2500

This model is a fine-tuned version of [./Qwen1.5-0.5B-Chat](https://huggingface.co/./Qwen1.5-0.5B-Chat) on the code_sft_train dataset.
It achieves the following results on the evaluation set:
- Loss: 0.5538
- Accuracy: 0.8508

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
- eval_batch_size: 1
- seed: 42
- gradient_accumulation_steps: 4
- total_train_batch_size: 8
- optimizer: Use OptimizerNames.ADAMW_TORCH with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: cosine
- lr_scheduler_warmup_steps: 0.03
- num_epochs: 2.0
- mixed_precision_training: Native AMP

### Training results

| Training Loss | Epoch  | Step | Accuracy | Validation Loss |
|:-------------:|:------:|:----:|:--------:|:---------------:|
| 0.7575        | 0.0796 | 100  | 0.8418   | 0.6448          |
| 0.6559        | 0.1592 | 200  | 0.8417   | 0.6338          |
| 0.6405        | 0.2388 | 300  | 0.8428   | 0.6266          |
| 0.6465        | 0.3184 | 400  | 0.8453   | 0.6154          |
| 0.6762        | 0.3980 | 500  | 0.8462   | 0.6128          |
| 0.6450        | 0.4776 | 600  | 0.8469   | 0.6076          |
| 0.6116        | 0.5572 | 700  | 0.8469   | 0.5984          |
| 0.6419        | 0.6368 | 800  | 0.8496   | 0.5959          |
| 0.6492        | 0.7164 | 900  | 0.8504   | 0.5913          |
| 0.6419        | 0.7960 | 1000 | 0.8507   | 0.5891          |
| 0.5290        | 0.8756 | 1100 | 0.8520   | 0.5821          |
| 0.6094        | 0.9552 | 1200 | 0.8546   | 0.5726          |
| 0.4332        | 1.0342 | 1300 | 0.8541   | 0.5834          |
| 0.4422        | 1.1138 | 1400 | 0.8542   | 0.5828          |
| 0.4026        | 1.1934 | 1500 | 0.8558   | 0.5774          |
| 0.4155        | 1.2730 | 1600 | 0.5613   | 0.8514          |
| 0.5304        | 1.3526 | 1700 | 0.5649   | 0.8503          |
| 0.4652        | 1.4322 | 1800 | 0.5697   | 0.8488          |
| 0.4942        | 1.5118 | 1900 | 0.5733   | 0.8486          |
| 0.4447        | 1.5914 | 2000 | 0.5699   | 0.8490          |
| 0.4479        | 1.6710 | 2100 | 0.5740   | 0.8484          |
| 0.6005        | 1.7506 | 2200 | 0.5693   | 0.8495          |
| 0.4380        | 1.8302 | 2300 | 0.5596   | 0.8506          |
| 0.5493        | 1.9099 | 2400 | 0.5628   | 0.8481          |
| 0.4963        | 1.9895 | 2500 | 0.5538   | 0.8508          |
| 0.4018        | 2.0    | 2514 | 0.5560   | 0.8510          |


### Framework versions

- Transformers 5.6.0
- Pytorch 2.5.1+cu124
- Datasets 4.0.0
- Tokenizers 0.22.2
