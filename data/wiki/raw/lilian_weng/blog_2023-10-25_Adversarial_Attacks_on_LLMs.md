# Adversarial Attacks on LLMs
url: https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/
author: Lilian Weng
published_at: 2023-10-25
persona_id: lilian_weng

---

The use of large language models in the real world has strongly accelerated by the launch of ChatGPT. We (including my team at OpenAI, shoutout to them) have invested a lot of effort to build default safe behavior into the model during the alignment process (e.g. via RLHF ). However, adversarial attacks or jailbreak prompts could potentially trigger the model to output something undesired. A large body of ground work on adversarial attacks is on images, and differently it operates in the continuous, high-dimensional space. Attacks for discrete data like text have been considered to be a lot more challenging, due to lack of direct gradient signals. My past post on Controllable Text Generation is quite relevant to this topic, as attacking LLMs is essentially to control the model to output a certain type of (unsafe) content.
