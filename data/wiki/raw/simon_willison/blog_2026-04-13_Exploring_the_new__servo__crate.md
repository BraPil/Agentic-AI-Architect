# Exploring the new `servo` crate
url: https://simonwillison.net/2026/Apr/13/servo-crate-exploration/#atom-everything
author: Simon Willison
published_at: 2026-04-13
persona_id: simon_willison

---

Research: Exploring the new `servo` crate In Servo is now available on crates.io the Servo team announced the initial release of the servo crate, which packages their browser engine as an embeddable library. I set Claude Code for web the task of figuring out what it can do, building a CLI tool for taking screenshots using it and working out if it could be compiled to WebAssembly. The servo-shot Rust tool it built works pretty well: git clone https://github.com/simonw/research
cd research/servo-crate-exploration/servo-shot
cargo build
./target/debug/servo-shot https://news.ycombinator.com/ Here's the result: Compiling Servo itself to WebAssembly is not feasible due to its heavy use of threads and dependencies like SpiderMonkey, but Claude did build me this playground page for trying out a WebAssembly build of the html5ever and markup5ever_rcdom crates, providing a tool for turning fragments of HTML into a parse tree. Tags: research , browsers , rust , webassembly , claude-code , servo
