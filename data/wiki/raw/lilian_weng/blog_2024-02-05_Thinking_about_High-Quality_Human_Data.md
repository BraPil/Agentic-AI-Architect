# Thinking about High-Quality Human Data
url: https://lilianweng.github.io/posts/2024-02-05-human-data-quality/
author: Lilian Weng
published_at: 2024-02-05
persona_id: lilian_weng

---

[Special thank you to Ian Kivlichan for many useful pointers (E.g. the 100+ year old Nature paper “Vox populi”) and nice feedback. 🙏 ] High-quality data is the fuel for modern data deep learning model training. Most of the task-specific labeled data comes from human annotation, such as classification task or RLHF labeling (which can be constructed as classification format) for LLM alignment training. Lots of ML techniques in the post can help with data quality, but fundamentally human data collection involves attention to details and careful execution. The community knows the value of high quality data, but somehow we have this subtle impression that “Everyone wants to do the model work, not the data work” ( Sambasivan et al. 2021 ).
