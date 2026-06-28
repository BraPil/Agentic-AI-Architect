# Gemma 4 audio with MLX
url: https://simonwillison.net/2026/Apr/12/mlx-audio/#atom-everything
author: Simon Willison
published_at: 2026-04-12
persona_id: simon_willison

---

Thanks to a tip from Rahim Nathwani , here's a uv run recipe for transcribing an audio file on macOS using the 10.28 GB Gemma 4 E2B model with MLX and mlx-vlm : uv run --python 3.13 --with mlx_vlm --with torchvision --with gradio \ mlx_vlm.generate \ --model google/gemma-4-e2b-it \ --audio file.wav \ --prompt "Transcribe this audio" \ --max-tokens 500 \ --temperature 1.0 Your browser does not support the audio element. I tried it on this 14 second .wav file and it output the following: This front here is a quick voice memo. I want to try it out with MLX VLM. Just going to see if it can be transcribed by Gemma and how that works. (That was supposed to be "This right here..." and "... how well that works" but I can hear why it misinterpreted that as "front" and "how that works".) Tags: uv , mlx , ai , gemma , llms , speech-to-text , python , generative-ai
