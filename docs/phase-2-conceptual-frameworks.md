# Phase 2: Conceptual Frameworks — The Complete AI Architect Knowledge Stack

> **System Phase**: This document is continuously updated by the `ResearchAgent`. Frameworks are tagged with maturity signals: 🟢 Growing | 🟡 Stable | 🔴 Declining | 🆕 Emerging.

---

## 2.1 Machine Learning Paradigms

### Supervised Learning 🟡 Stable
The workhorse of production ML. Models learn from labeled examples.

**Key variants**:
- Classification (binary, multi-class, multi-label)
- Regression (linear, polynomial, quantile)
- Sequence-to-sequence (NLP tasks, time series)

**AI Architect concerns**: Label quality pipelines, class imbalance strategies, calibration, online learning for concept drift.

### Unsupervised Learning 🟡 Stable
Pattern discovery without labels.

**Key variants**:
- Clustering (K-Means, DBSCAN, Gaussian Mixture Models)
- Dimensionality reduction (PCA, UMAP, t-SNE)
- Anomaly detection (Isolation Forest, autoencoders)
- Self-supervised learning (contrastive, masked prediction) 🟢

**AI Architect concerns**: Evaluation without ground truth, cluster stability, latent space interpretability.

### Reinforcement Learning 🟢 Growing (especially RLHF/RLAIF)
Agent learns via reward signals from environment interaction.

**Architectures**:
- Model-free: PPO, SAC, DQN
- Model-based: Dreamer, MuZero
- RLHF (Reinforcement Learning from Human Feedback) — core to LLM alignment
- DPO (Direct Preference Optimization) 🟢 — simpler RLHF alternative, rapidly displacing PPO for LLMs
- GRPO (Group Relative Policy Optimization) 🆕 — DeepSeek's approach, gaining traction

---

## 2.2 Agentic System Architectures

### Single-Agent Patterns

#### ReAct (Reason + Act) 🟢 Growing
The foundational agentic loop: the agent interleaves reasoning traces with tool use actions.
```
Thought → Action → Observation → Thought → Action → ...
```

#### Plan-and-Execute 🟢 Growing
Separates planning (high-level decomposition) from execution (step-by-step).
```
Planner Agent → [Step 1, Step 2, Step 3, ...] → Executor Agent → Results
```

#### Reflexion 🟡 Stable (research context)
Agent evaluates its own previous attempts and generates improved solutions.

#### LATS (Language Agent Tree Search) 🆕 Emerging
Combines Monte Carlo Tree Search with LLM agents for complex reasoning.

### Multi-Agent Patterns

#### Hierarchical Agents 🟢 Growing
```
Orchestrator (Manager)
├── Sub-Agent A (Specialist)
├── Sub-Agent B (Specialist)
└── Sub-Agent C (Specialist)
```
Used for: Complex tasks requiring decomposition, enterprise workflows.

#### Parallel Agents 🟢 Growing
Multiple agents work simultaneously on independent subtasks; results aggregated.
```
Task → [Agent A | Agent B | Agent C] → Aggregator → Result
```
Used for: Research synthesis, multi-source data gathering (exactly what this system does).

#### Collaborative / Debate 🟡 Stable (research context)
Agents discuss, critique each other's outputs, and reach consensus.

#### Adversarial / Red Team 🟢 Growing
Dedicated adversarial agent attempts to break or find flaws in other agents' outputs.

#### Swarm Agents 🆕 Emerging
Large numbers of simple agents with emergent collective behavior (inspired by OpenAI Swarm).

### Memory Architecture Patterns

| Memory Type | Analogy | Implementation |
|------------|---------|----------------|
| **Working Memory** | RAM | Context window; conversation buffer |
| **Episodic Memory** | Journal | Vector DB with timestamped event records |
| **Semantic Memory** | Encyclopedia | Knowledge graph or structured vector store |
| **Procedural Memory** | Muscle memory | Saved tool chains, agent workflows, prompt templates |

---

## 2.3 LLM-Specific Frameworks

### Prompt Engineering 🟡 Stable
- Zero-shot, few-shot, chain-of-thought (CoT)
- Tree-of-Thought, Graph-of-Thought
- Automatic prompt optimization (DSPy 🟢, APE)
- System prompt architecture patterns

### RAG (Retrieval-Augmented Generation) 🟢 Growing
```
Query → Embedding → Vector Search → Retrieved Chunks → LLM → Answer
```
**Variants**:
- Naive RAG → Advanced RAG (re-ranking, query rewriting) → Modular RAG 🟢
- Self-RAG: Model decides when to retrieve
- HyDE (Hypothetical Document Embedding)
- Graph RAG 🆕: Microsoft's approach using knowledge graphs for retrieval

### Context & State Management 🟢 Growing
Critical for production agents:
- **Context compression**: Summarization, selective forgetting
- **Context window management**: Sliding window, hierarchical summarization
- **State persistence**: Redis, PostgreSQL, LangGraph state graphs
- **Long-context models** (Gemini 1.5 Pro 2M tokens, Claude 3.5 Sonnet 200K): changing RAG calculus

### Prompt Injection Security 🟢 Growing (Critical)
Attack vectors:
- **Direct injection**: Malicious content in user input overrides system instructions
- **Indirect injection**: Injected via tool outputs, retrieved documents, web content

Defense strategies:
- Input sanitization and validation
- Privilege separation between system and user prompts
- Output filtering and intent classification
- LLM-as-guardrail with separate validation model
- Structured output enforcement (JSON Schema, Pydantic validation)

### Hallucination Control 🟢 Growing
Categories:
- **Factual hallucination**: Wrong facts stated confidently
- **Source fabrication**: Fake citations
- **Reasoning hallucination**: Correct conclusion, wrong reasoning chain

Mitigation strategies:
- RAG with source attribution
- Confidence calibration and uncertainty quantification
- Self-consistency sampling (majority vote across multiple generations)
- Chain-of-verification (CoVe)
- Structured output with validation

### Guardrails 🟢 Growing
Defense-in-depth for LLM outputs:
- **Input guardrails**: PII detection, toxicity filtering, jailbreak detection
- **Output guardrails**: Content policy, fact-checking, format validation
- **Frameworks**: NeMo Guardrails (NVIDIA), Guardrails AI, LlamaGuard, Llama Guard 3

---

## 2.4 Classical ML & Statistical Frameworks

### Decision Trees & Ensemble Methods 🟡 Stable

#### XGBoost 🟡 Stable (still dominant for tabular)
Gradient boosting framework. Still the gold standard for structured/tabular data.
- Key: Tree structure, regularization, DART dropout

#### LightGBM 🟡 Stable
Faster alternative to XGBoost for large datasets; histogram-based approach.

#### CatBoost 🟡 Stable
Strong handling of categorical features; used heavily in Yandex/enterprise settings.

#### Random Forest 🟡 Stable
Parallel ensemble; useful for uncertainty estimation via prediction variance.

### Hyperparameter Optimization 🟢 Growing

#### Optuna 🟢 Growing (de facto standard)
- Tree-structured Parzen Estimator (TPE) — efficient Bayesian optimization
- Pruning strategies (stop unpromising trials early)
- Multi-objective optimization (accuracy vs. latency)

#### Ray Tune 🟢 Growing
- Distributed hyperparameter search
- Integrates with most ML frameworks
- Population-Based Training (PBT)

#### FLAML 🆕 Emerging
- Microsoft's fast AutoML library; particularly effective for LLM cost optimization

---

## 2.5 ML Infrastructure Frameworks

### Experiment Tracking

#### MLflow 🟢 Growing (enterprise standard)
- Tracking: parameters, metrics, artifacts
- Model Registry: versioning, stage transitions (Staging → Production)
- MLflow Projects: reproducible runs
- Model Serving: built-in REST API

#### Weights & Biases (W&B) 🟢 Growing
- Superior visualization vs. MLflow
- Sweeps: hyperparameter search
- Reports: shareable experiment analyses
- Artifacts: dataset and model versioning

### Pipelines & Orchestration

#### Apache Airflow 🟡 Stable (heavy; used in enterprises)
#### Prefect 🟢 Growing (modern, Pythonic)
#### ZenML 🟢 Growing (ML-specific pipeline framework)
#### Metaflow (Netflix) 🟡 Stable

---

## 2.6 Vector Databases & Similarity Search

### FAISS (Facebook AI Similarity Search) 🟢 Growing
Open-source, extremely fast local vector search. Used for:
- Offline index building
- Embedded in applications (no separate server)
- Billion-scale search with ANN (Approximate Nearest Neighbor)

**Index types**: IVF, HNSW, PQ (Product Quantization) for compression

### Pinecone 🟢 Growing (managed cloud)
Fully managed, serverless vector DB. Best for: production RAG without infrastructure overhead.

### Weaviate 🟢 Growing
Open-source vector DB with built-in GraphQL interface and multimodal support.

### Qdrant 🟢 Growing (Rust-based, high performance)
Strong filtering capabilities; good on-premise option.

### ChromaDB 🟢 Growing (developer-friendly)
Lightweight, embedded, great for prototyping and small-to-medium scale.

### pgvector 🟢 Growing
PostgreSQL extension for vector similarity. Compelling for teams already on Postgres — reduces infrastructure complexity.

### Similarity Metrics & Statistical Tests

#### Cosine Similarity
Standard for semantic similarity between embeddings.

#### Population Stability Index (PSI) 🟡 Stable (model monitoring)
Measures distribution shift between training and production data:
- PSI < 0.1: No significant change
- 0.1 ≤ PSI < 0.2: Moderate shift (investigate)
- PSI ≥ 0.2: Significant shift (retrain)

#### Kolmogorov-Smirnov (KS) Test 🟡 Stable (model monitoring)
Non-parametric test for distribution equality. Used in model drift detection.

---

## 2.7 Model Context Protocol (MCP) & Tool Frameworks

### MCP (Model Context Protocol) 🆕 High Growth (Anthropic, 2024–2025)
Standardized protocol for connecting LLMs to external tools, data sources, and services.

**Architecture**:
```
LLM ↔ MCP Client ↔ MCP Server ↔ External Tool/Service
```

**Key insight (2025–2026)**: The paradigm is shifting from **always-on MCP servers** to **dynamic tool loading**:
- Load MCP at moment of need → execute → unload
- Reduces resource consumption and attack surface
- Aligns with Anthropic's recommendations for code execution patterns
- ChatGPT's "tool search" feature (2025) demonstrates this direction

### LangChain Tools & Toolkits 🟡 Stable
Standard tool abstraction for LangChain agents.

### LangGraph 🟢 Growing (replaces LangChain Expression Language for agents)
Graph-based stateful agent orchestration. Key concepts:
- Nodes (agent steps), Edges (transitions), State (shared context)
- Conditional edges for dynamic routing
- Built-in human-in-the-loop support
- Persistence layer (SQLite, PostgreSQL)

### AutoGen (Microsoft) 🟢 Growing
Multi-agent conversation framework with rich agent customization.

### CrewAI 🟢 Growing (role-based multi-agent)
Structured role assignment for agent teams; good for enterprise workflows.

### Semantic Kernel (Microsoft) 🟡 Stable
Enterprise-grade SDK for integrating LLMs into .NET, Python, and Java applications.

---

## 2.8 Evaluation Frameworks

### Model Evaluation

#### HELM (Holistic Evaluation of Language Models) 🟢 Growing
Stanford's comprehensive LLM benchmark covering accuracy, calibration, robustness, fairness.

#### LMSYS Chatbot Arena 🟢 Growing
Human preference-based evaluation via pairwise comparisons (Elo rating system).

#### Evals (OpenAI) 🟡 Stable
Framework for creating and running custom evaluations.

### Agent Evaluation

#### AgentBench 🟡 Stable
Benchmarks for agentic tasks across web browsing, coding, games.

#### GAIA 🟢 Growing
Real-world question answering requiring tool use; strong signal for practical agent capability.

#### Custom Evaluation Loops 🟢 Growing
Building task-specific evaluation harnesses with LLM judges.

### SLO/SLI/SLA for AI Systems

| Term | Meaning in AI Context | Example |
|------|----------------------|---------|
| **SLI** (Service Level Indicator) | Metric measured | Response latency, hallucination rate |
| **SLO** (Service Level Objective) | Target for SLI | P99 latency < 2s; hallucination rate < 1% |
| **SLA** (Service Level Agreement) | Contractual commitment | Uptime ≥ 99.9%; support response < 4h |

**AI-specific KPIs**:
- Answer relevance score (LLM judge)
- Grounding rate (% answers with valid citations)
- Tool call success rate
- Context utilization efficiency
- Cost per query (token economics)

---

## 2.9 Data Pipelines & Feature Engineering

### Feature Stores

#### Feast 🟡 Stable (open-source reference)
Point-in-time correct feature retrieval for training/serving consistency.

#### Tecton 🟡 Stable (enterprise managed)
#### Hopsworks 🟡 Stable (open-source enterprise)

### Data Quality & Lineage

#### Great Expectations 🟡 Stable
Data validation with "expectation suites" — the unit testing of data.

#### dbt (data build tool) 🟢 Growing
SQL-first transformation pipeline with documentation and testing.

#### Apache Atlas / OpenLineage 🟡 Stable
Data lineage tracking — critical for compliance and debugging.

---

## 2.10 Emerging Paradigms to Watch

### Small Language Models (SLMs) 🆕 High Growth
- Microsoft Phi series, Google Gemma, Apple OpenELM
- "Small but capable" trend driven by: on-device inference, cost, privacy
- Yann LeCun's critique: pure LLMs are fundamentally limited; SLMs trained on structured world models may be the path forward

### World Models 🆕 Emerging (5–10 year horizon)
- LeCun's vision: AI systems that learn a model of the world and plan within it
- JEPA (Joint Embedding Predictive Architecture): learns by predicting representations, not pixels
- Genie (Google): generative world model for interactive environments

### Mixture of Experts (MoE) 🟢 Growing
- GPT-4, Mixtral, Grok use MoE: only a subset of parameters active per token
- Enables much larger total model capacity at lower inference cost
- Architectural shift that AI Architects must design serving infrastructure around

### Speculative Decoding 🟢 Growing
- Use small "draft" model to propose tokens; large model verifies in parallel
- Major latency improvement for large models (2–5x speedup)

### Retrieval vs. Long Context Tension 🆕 Active Research
- As context windows grow (2M tokens), when do you RAG vs. stuff-the-context?
- Cost/latency tradeoffs still favor RAG for most production use cases (2026)

### Compound AI Systems 🟢 Growing
- Shift from single monolithic model to systems of specialized models
- LMSYS's Compound AI paper; Databricks' trend analysis

---

## 2.11 Framework Maturity Matrix

| Framework | 2024 Status | 2026 Trajectory | Notes |
|-----------|-------------|-----------------|-------|
| LangChain | 🟢 Dominant | 🟡 Stabilizing | Heavy; LangGraph replacing for agents |
| LangGraph | 🆕 Emerging | 🟢 Growing fast | State-based agents, production-ready |
| LlamaIndex | 🟢 Growing | 🟢 Growing | Best-in-class RAG pipelines |
| AutoGen | 🟡 Moderate | 🟢 Growing | Microsoft backing; enterprise adoption |
| CrewAI | 🆕 Fast growth | 🟢 Growing | Role-based multi-agent; accessible |
| DSPy | 🆕 Emerging | 🟢 Growing | Programmatic prompt optimization |
| FAISS | 🟡 Stable | 🟡 Stable | Core utility; not going anywhere |
| MLflow | 🟢 Growing | 🟢 Growing | Enterprise experiment tracking standard |
| Optuna | 🟡 Stable | 🟡 Stable | HPO reference implementation |
| XGBoost | 🟡 Stable | 🟡 Stable | Tabular data king; not displaced |

---

*This document is generated and maintained by the `DocumentationAgent`. To trigger a refresh, run:*
```bash
python -m src.agents.orchestrator --update-phase frameworks
```
