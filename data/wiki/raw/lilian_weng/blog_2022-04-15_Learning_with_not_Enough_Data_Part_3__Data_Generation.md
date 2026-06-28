# Learning with not Enough Data Part 3: Data Generation
url: https://lilianweng.github.io/posts/2022-04-15-data-gen/
author: Lilian Weng
published_at: 2022-04-15
persona_id: lilian_weng

---

Here comes the Part 3 on learning with not enough data (Previous: Part 1 and Part 2 ). Let’s consider two approaches for generating synthetic data for training. Augmented data . Given a set of existing training samples, we can apply a variety of augmentation, distortion and transformation to derive new data points without losing the key attributes. We have covered a bunch of augmentation methods on text and images in a previous post on contrastive learning. For the sake of post completeness, I duplicate the section on data augmentation here with some edits. New data . Given few or even no data points, we can rely on powerful pretrained models to generate a number of new data points. This is especially true in recent years given the fast progress in large pretrained language models (LM) . Few shot prompting is shown to be effective for LM to learn within context without extra training. Data Augmentation The goal of data augmentation is to modify the input format (e.g. text wording, visual appearance) while the semantic meaning stays unchanged.
