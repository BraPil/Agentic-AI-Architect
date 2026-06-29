# Pure Borrow: Linear Haskell Meets Rust-Style Borrowing
arxiv_id: 2604.15290
url: https://arxiv.org/abs/2604.15290
authors: Yusuke Matsushita, Hiromi Ishii
published_at: 2026-04-16
categories: cs.PL

---

A promising approach to unifying functional and imperative programming paradigms is to localize mutation using linear or affine types. Haskell, a purely functional language, was recently extended with linear types by Bernardy et al., named Linear Haskell. However, it remained unknown whether such a pure language could safely support non-local \emph{borrowing} in the style of Rust, where each borrower can be freely split and dropped without direct communication of ownership back to the lender. We answer this question affirmatively by \emph{Pure Borrow}, a novel framework that realizes Rust-style borrowing in Linear Haskell with purity. Notably, it features parallel state mutation with affine mutable references inside pure computation, unlike the IO and ST monads and existing Linear Haskell APIs. It also enjoys purity, lazy evaluation, first-class polymorphism and leak freedom, unlike Rust. We implement Pure Borrow simply as a library in Linear Haskell and demonstrate its power with a case study in parallel computing. We formalize the core of Pure Borrow and build a metatheory that works toward establishing safety, leak freedom and confluence, with a new, history-based model of borrowing.
