# Phase 1: Education — What Are AI Architects and What Do They Do?

> **System Phase**: This document is continuously updated by the `ResearchAgent` and `DocumentationAgent` as new information is discovered. Last conceptual update: March 2026.

---

## 1.1 The Role of an AI Architect

An **AI Architect** is a senior technical leader who bridges the gap between raw machine learning research and production-grade, business-critical AI systems. Unlike a Data Scientist who focuses on modeling, or an ML Engineer who focuses on code, the AI Architect is responsible for the *entire system* — from data ingestion to model serving, from governance to cost optimization.

### Core Responsibilities

| Domain | Responsibilities |
|--------|-----------------|
| **System Design** | Designing end-to-end ML and agentic pipelines; selecting frameworks, storage, and serving infrastructure |
| **Model Strategy** | Choosing between build vs. buy; fine-tuning vs. RAG vs. prompt engineering; model selection criteria |
| **Agentic Orchestration** | Designing multi-agent systems, tool use patterns, memory architectures, and agent communication protocols |
| **Data Architecture** | Vector databases, feature stores, data lineage, quality pipelines, schema evolution |
| **Governance & Safety** | Guardrails, prompt injection defense, hallucination mitigation, audit logging, model cards |
| **Evaluation & Observability** | Defining SLOs/SLIs, KPI frameworks, drift detection, A/B testing, shadow deployments |
| **Cost & Performance** | Token optimization, inference cost modeling, latency SLAs, caching strategies |
| **Stakeholder Alignment** | Translating business requirements into technical specs; communicating risk and capability |

### AI Architect vs. Related Roles

```
Data Scientist          → Experiments, models, notebooks
ML Engineer             → Code quality, deployment, CI/CD for models
MLOps Engineer          → Infrastructure, monitoring, pipelines
AI Architect            → System-level design, strategy, cross-cutting concerns
Solutions Architect     → Cloud/infra architecture (may specialize in AI)
Principal/Staff ML Eng  → Technical leadership, often overlapping with AI Architect
```

---

## 1.2 The AI Architect's Knowledge Domains

An AI Architect in 2025–2026 must be fluent across five broad knowledge domains:

### Domain 1: Foundational AI/ML
- Supervised, unsupervised, and reinforcement learning
- Neural network architectures (transformers, diffusion models, SSMs)
- Classical ML (decision trees, XGBoost, SVMs, ensemble methods)
- Statistical fundamentals (distributions, hypothesis testing, PSI/KS drift metrics)

### Domain 2: LLMs & Foundation Models
- Pretraining, RLHF, DPO, GRPO, Constitutional AI
- Prompt engineering, few-shot learning, chain-of-thought
- RAG (Retrieval-Augmented Generation) architectures
- Fine-tuning (LoRA, QLoRA, full fine-tuning)
- Context window management, long-context models
- Quantization (GGUF, AWQ, GPTQ)

### Domain 3: Agentic Systems
- Agent loop architectures (ReAct, Plan-and-Execute, Reflexion)
- Multi-agent patterns (hierarchical, parallel, collaborative, adversarial)
- Tool use, function calling, MCP (Model Context Protocol)
- Memory systems (episodic, semantic, working, procedural)
- Agent evaluation frameworks
- Dynamic tool discovery and loading

### Domain 4: Infrastructure & Operations
- MLflow, Weights & Biases, Comet for experiment tracking
- Vector databases (FAISS, Pinecone, Weaviate, Qdrant, ChromaDB)
- Feature stores (Feast, Tecton, Hopsworks)
- Serving infrastructure (vLLM, TGI, Triton, Ray Serve)
- Containerization and orchestration (Docker, Kubernetes)
- Cloud ML platforms (AWS SageMaker, Azure ML, GCP Vertex AI)

### Domain 5: Governance, Safety & Business
- Enterprise AI governance frameworks
- Responsible AI principles (fairness, explainability, privacy)
- EU AI Act, NIST AI RMF compliance
- Cost modeling and FinOps for AI
- ROI frameworks for AI investments
- Change management for AI adoption

---

## 1.3 Influential Figures in the AI Architecture Space

These are practitioners, researchers, and thought leaders whose work AI Architects should track closely.

### Research & Foundational Thinking

| Person | Affiliation | Why They Matter |
|--------|-------------|-----------------|
| **Andrej Karpathy** | Independent / previously OpenAI, Tesla | Exceptional communicator of deep learning fundamentals; "Software 2.0" thesis; neural net from-scratch tutorials define baseline understanding |
| **Yann LeCun** | Meta AI | Chief critic of pure LLM approaches; champion of world models and energy-based models; JEPA architecture may define next-gen AI |
| **Geoffrey Hinton** | Independent (ex-Google) | Godfather of deep learning; now focused on AI safety; his warnings shape governance thinking |
| **Yoshua Bengio** | MILA | AI safety focus, policy influence, fundamental research |
| **Ilya Sutskever** | SSI (ex-OpenAI) | Co-creator of GPT series; "super-alignment" focus with SSI |
| **Demis Hassabis** | Google DeepMind | AlphaFold, Gemini, AGI research direction |
| **Dario Amodei** | Anthropic | Constitutional AI, Claude, responsible scaling policies |

### Agentic Systems & Architecture Practitioners

| Person | Affiliation | Why They Matter |
|--------|-------------|-----------------|
| **Harrison Chase** | LangChain | Creator of LangChain/LangGraph; defines de-facto agentic framework patterns |
| **Jerry Liu** | LlamaIndex | Creator of LlamaIndex; RAG architecture patterns |
| **Swyx (Shawn Wang)** | Latent.Space / AIEngineer | AI Engineer concept; influential podcast and writing on production AI |
| **Simon Willison** | Independent | Obsessively tracks AI tool releases; LLM CLI tool; practical AI journalism |
| **Eugene Yan** | Amazon | Production ML systems at scale; applied ML writing |
| **Chip Huyen** | Rainbird / Stanford | "Designing ML Systems" book; feature stores, MLOps deep dives |
| **Lilian Weng** | OpenAI | Deep, rigorous blog posts on agents, RLHF, diffusion models — essential reading |

### Enterprise AI & Strategy

| Person | Affiliation | Why They Matter |
|--------|-------------|-----------------|
| **Andrew Ng** | DeepLearning.AI / AI Fund | AI adoption playbooks for companies; MLOps standards |
| **Cassie Kozyrkov** | Independent (ex-Google) | Decision intelligence; making AI useful for business decisions |
| **Gartner AI Research** | Gartner | Hype cycle positioning; enterprise adoption benchmarks |
| **Ben Thompson** | Stratechery | AI strategy and market dynamics analysis |

### Emerging Voices (2025–2026)

| Person | Why They Matter |
|--------|-----------------|
| **Kanjun Qiu** (Imbue) | Reasoning and agentic systems; long-horizon task completion |
| **Percy Liang** (Stanford HELM) | LLM evaluation rigor; HELM benchmark suite |
| **Carlos Guestrin** (Apple / ex-Turi) | XGBoost creator; practical ML at scale |
| **Jim Fan** (NVIDIA) | Embodied AI and foundation models for robotics |

### Communities to Track

- **AI Engineer World's Fair** — the premier conference for production AI practitioners
- **r/LocalLLaMA** — grassroots LLM experimentation and tool discovery
- **Hacker News /ai** — early signal for new tools and paradigm shifts
- **Discord: Latent Space, LangChain, LlamaIndex** — practitioner conversations
- **arXiv cs.AI, cs.LG, cs.CL** — preprint papers before peer review
- **Hugging Face Papers** — curated daily AI paper digests

---

## 1.4 Career Paths to AI Architect

The AI Architect role typically emerges from one of three paths:

```
Path A: ML Research → Applied ML → ML Platform Engineer → AI Architect
Path B: Software Architect → ML Engineering → AI Solutions Architect → AI Architect
Path C: Data Science Lead → MLOps → AI Platform Lead → AI Architect
```

**Key inflection point**: The shift from "I build models" to "I design systems that build, deploy, and govern models at scale."

---

## 1.5 How This System Tracks Education

The `ResearchAgent` is configured to continuously monitor:
- New job descriptions for "AI Architect" roles (signal for skill evolution)
- Course releases from Coursera, DeepLearning.AI, Fast.ai, and similar platforms
- New books and O'Reilly publications on AI architecture
- Conference talks at NeurIPS, ICLR, ICML, AI Engineer Summit
- Curated influencer and influential-post watchlists in `docs/influencer-tracker.md`
- Structured source registry records in `docs/influencer-source-registry.yaml`

Updates are stored in the knowledge base under the `education` namespace and surfaced in the `ResearchAgent`'s weekly digest.
