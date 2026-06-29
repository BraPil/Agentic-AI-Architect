# AD4AD: Benchmarking Visual Anomaly Detection Models for Safer Autonomous Driving
arxiv_id: 2604.15291
url: https://arxiv.org/abs/2604.15291
authors: Fabrizio Genilotti, Arianna Stropeni, Gionata Grotto, Francesco Borsatti, Manuel Barusco, Davide Dalle Pezze, Gian Antonio Susto
published_at: 2026-04-16
categories: cs.CV, cs.AI

---

The reliability of a machine vision system for autonomous driving depends heavily on its training data distribution. When a vehicle encounters significantly different conditions, such as atypical obstacles, its perceptual capabilities can degrade substantially. Unlike many domains where errors carry limited consequences, failures in autonomous driving translate directly into physical risk for passengers, pedestrians, and other road users. To address this challenge, we explore Visual Anomaly Detection (VAD) as a solution. VAD enables the identification of anomalous objects not present during training, allowing the system to alert the driver when an unfamiliar situation is detected. Crucially, VAD models produce pixel-level anomaly maps that can guide driver attention to specific regions of concern without requiring any prior assumptions about the nature or form of the hazard. We benchmark eight state-of-the-art VAD methods on AnoVox, the largest synthetic dataset for anomaly detection in autonomous driving. In particular, we evaluate performance across four backbone architectures spanning from large networks to lightweight ones such as MobileNet and DeiT-Tiny. Our results demonstrate that VAD transfers effectively to road scenes. Notably, Tiny-Dinomaly achieves the best accuracy-efficiency trade-off for edge deployment, matching full-scale localization performance at a fraction of the memory cost. This study represents a concrete step toward safer, more responsible deployment of autonomous vehicles, ultimately improving protection for passengers, pedestrians, and all road users.
