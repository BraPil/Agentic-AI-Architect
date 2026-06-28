# ChatGPT voice mode is a weaker model
url: https://simonwillison.net/2026/Apr/10/voice-mode-is-weaker/#atom-everything
author: Simon Willison
published_at: 2026-04-10
persona_id: simon_willison

---

I think it's non-obvious to many people that the OpenAI voice mode runs on a much older, much weaker model - it feels like the AI that you can talk to should be the smartest AI but it really isn't. If you ask ChatGPT voice mode for its knowledge cutoff date it tells you April 2024 - it's a GPT-4o era model. This thought inspired by this Andrej Karpathy tweet about the growing gap in understanding of AI capability based on the access points and domains people are using the models with: [...] It really is simultaneously the case that OpenAI's free and I think slightly orphaned (?) "Advanced Voice Mode" will fumble the dumbest questions in your Instagram's reels and at the same time , OpenAI's highest-tier and paid Codex model will go off for 1 hour to coherently restructure an entire code base, or find and exploit vulnerabilities in computer systems. This part really works and has made dramatic strides because 2 properties: these domains offer explicit reward functions that are verifiable meaning they are easily amenable to reinforcement learning training (e.g. unit tests passed yes or no, in contrast to writing, which is much harder to explicitly judge), but also they are a lot more valuable in b2b settings, meaning that the biggest fraction of the team is focused on improving them. Tags: andrej-karpathy , generative-ai , openai , chatgpt , ai , llms
