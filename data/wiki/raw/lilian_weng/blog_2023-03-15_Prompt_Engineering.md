# Prompt Engineering
url: https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/
author: Lilian Weng
published_at: 2023-03-15
persona_id: lilian_weng

---

Prompt Engineering , also known as In-Context Prompting , refers to methods for how to communicate with LLM to steer its behavior for desired outcomes without updating the model weights. It is an empirical science and the effect of prompt engineering methods can vary a lot among models, thus requiring heavy experimentation and heuristics. This post only focuses on prompt engineering for autoregressive language models, so nothing with Cloze tests, image generation or multimodality models. At its core, the goal of prompt engineering is about alignment and model steerability. Check my previous post on controllable text generation.
