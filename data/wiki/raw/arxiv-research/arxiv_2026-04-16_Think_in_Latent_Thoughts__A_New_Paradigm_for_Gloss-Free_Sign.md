# Think in Latent Thoughts: A New Paradigm for Gloss-Free Sign Language Translation
arxiv_id: 2604.15301
url: https://arxiv.org/abs/2604.15301
authors: Yiyang Jiang, Li Zhang, Xiao-Yong Wei, Li Qing
published_at: 2026-04-16
categories: cs.CV

---

Many SLT systems quietly assume that brief chunks of signing map directly to spoken-language words. That assumption breaks down because signers often create meaning on the fly using context, space, and movement. We revisit SLT and argue that it is mainly a cross-modal reasoning task, not just a straightforward video-to-text conversion. We thus introduce a reasoning-driven SLT framework that uses an ordered sequence of latent thoughts as an explicit middle layer between the video and the generated text. These latent thoughts gradually extract and organize meaning over time. On top of this, we use a plan-then-ground decoding method: the model first decides what it wants to say, and then looks back at the video to find the evidence. This separation improves coherence and faithfulness. We also built and released a new large-scale gloss-free SLT dataset with stronger context dependencies and more realistic meanings. Experiments across several benchmarks show consistent gains over existing gloss-free methods. Code and data will be released upon acceptance at https://github.com/fletcherjiang/SignThought.
