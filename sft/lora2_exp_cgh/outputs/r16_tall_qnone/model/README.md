---
library_name: peft
license: other
base_model: ./Qwen1.5-0.5B-Chat
tags:
- base_model:adapter:./Qwen1.5-0.5B-Chat
- llama-factory
- lora
- transformers
metrics:
- accuracy
pipeline_tag: text-generation
model-index:
- name: model
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# model

This model is a fine-tuned version of [./Qwen1.5-0.5B-Chat](https://huggingface.co/./Qwen1.5-0.5B-Chat) on the code_sft_train dataset.
It achieves the following results on the evaluation set:
- Loss: 0.7158
- Accuracy: 0.8229

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 0.0001
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
| 0.8250        | 0.4776 | 1000 | 0.7502          | 0.8153   |
| 0.7282        | 0.9552 | 2000 | 0.7314          | 0.8195   |
| 0.6849        | 1.4327 | 3000 | 0.7229          | 0.8215   |
| 0.5335        | 1.9103 | 4000 | 0.7130          | 0.8238   |
| 0.4462        | 2.3878 | 5000 | 0.7169          | 0.8227   |
| 0.5761        | 2.8654 | 6000 | 0.7158          | 0.8229   |
| 0.6588        | 3.0    | 6282 | 0.7158          | 0.8229   |


### Framework versions

- PEFT 0.18.1
- Transformers 5.6.0
- Pytorch 2.5.1+cu124
- Datasets 4.0.0
- Tokenizers 0.22.2