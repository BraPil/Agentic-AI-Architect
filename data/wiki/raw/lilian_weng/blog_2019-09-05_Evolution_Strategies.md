# Evolution Strategies
url: https://lilianweng.github.io/posts/2019-09-05-evolution-strategies/
author: Lilian Weng
published_at: 2019-09-05
persona_id: lilian_weng

---

Stochastic gradient descent is a universal choice for optimizing deep learning models. However, it is not the only option. With black-box optimization algorithms, you can evaluate a target function $f(x): \mathbb{R}^n \to \mathbb{R}$, even when you don’t know the precise analytic form of $f(x)$ and thus cannot compute gradients or the Hessian matrix. Examples of black-box optimization methods include Simulated Annealing , Hill Climbing and Nelder-Mead method .
