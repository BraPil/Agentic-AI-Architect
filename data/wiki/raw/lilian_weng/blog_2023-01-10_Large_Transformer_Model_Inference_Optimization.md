# Large Transformer Model Inference Optimization
url: https://lilianweng.github.io/posts/2023-01-10-inference-optimization/
author: Lilian Weng
published_at: 2023-01-10
persona_id: lilian_weng

---

[Updated on 2023-01-24: add a small section on Distillation .] Large transformer models are mainstream nowadays, creating SoTA results for a variety of tasks. They are powerful but very expensive to train and use. The extremely high inference cost, in both time and memory, is a big bottleneck for adopting a powerful transformer for solving real-world tasks at scale. Why is it hard to run inference for large transformer models? Besides the increasing size of SoTA models, there are two main factors contributing to the inference challenge ( Pope et al. 2022 ):
