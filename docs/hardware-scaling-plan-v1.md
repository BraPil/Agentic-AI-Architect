# Hardware Scaling Plan v1 — Mouseion / AAA / ExMorbus 3-Month Sprint

## Purpose

This document answers a specific strategic question:

> What hardware do we need to run the Agentic-AI-Architect (AAA), Mouseion shared substrate, and
> ExMorbus workloads 24/7 for three months so they produce valuable discoveries — and what does that
> look like at 1×, 10×, and 100× current scale?

Current design target: **100–200 concurrent agents**.
Scale tier 2: **1,000–2,000 concurrent agents (10×)**.
Scale tier 3: **10,000–20,000 concurrent agents (100×)**.

The hardware models discussed are: Mac Mini M4 / M4 Pro, NVIDIA DGX Spark (GB10 Grace
Blackwell), and NVIDIA GeForce RTX 5090.

---

## 1. What "Running 24/7 for 3 Months" Actually Demands

### 1.1 Operational Meaning

Three months continuous operation at target scale means:

| Metric | Value |
|--------|-------|
| Hours of operation | ~2,160 h |
| Expected cycles per agent at 1 task/min | ~129,600 cycles |
| Expected LLM calls per inference-active agent | ~43,200 |
| Estimated total LLM calls at 200 agents (20% active) | ~8.6 M |
| Estimated total LLM calls at 2,000 agents (20% active) | ~86 M |
| Estimated total LLM calls at 20,000 agents (20% active) | ~860 M |

Not all agents generate LLM load simultaneously. The workload breakdown for this system is:

| Agent Class | Bottleneck | Approximate share of time |
|-------------|-----------|---------------------------|
| CrawlerAgent | Network I/O | 40% |
| ResearchAgent | LLM inference | 25% |
| TrendTrackerAgent | SQLite / vector search | 15% |
| ToolDiscoveryAgent | Network + LLM | 10% |
| DocumentationAgent | LLM inference | 10% |

Assume **20–30% of active agents are LLM-inference-bound** at any moment. This is the capacity
number to size the GPU fleet around.

### 1.2 Knowledge Volume

Three months of continuous discovery at target scale will generate:

| Scale | Est. KB entries / day | Est. total entries | Est. SQLite DB size | Est. vector index |
|-------|----------------------|--------------------|---------------------|-------------------|
| Baseline (200 agents) | ~5,000 | ~450,000 | ~2–5 GB | ~20 GB |
| 10× (2,000 agents) | ~50,000 | ~4.5 M | ~20–50 GB | ~200 GB |
| 100× (20,000 agents) | ~500,000 | ~45 M | ~200–500 GB | ~2 TB |

At 10× and above, SQLite must be replaced with PostgreSQL + pgvector or a dedicated vector store
(Qdrant, Weaviate, or Pinecone). That migration point is part of the scale planning below.

### 1.3 The Value Production Goal

The purpose of running intensively for 3 months is not throughput for its own sake. The goal is:

- a curated, evaluated, and weighted knowledge base strong enough to serve as ExMorbus's
  architectural oracle
- a validated training-funnel progression for ExMorbus (broad health → oncology → experimental
  therapies)
- a set of answered canonical architecture questions with confidence scores, source provenance, and
  segment-aware overlays
- enough evaluation history to establish meaningful learned source weights

This shapes hardware priorities: prioritize inference capacity and storage over raw CPU count.

---

## 2. Hardware Selection Criteria

The specific machines mentioned in the planning prompt were:

- **Mac Mini M4 / M4 Pro** — power-efficient, cluster-friendly, runs MLX and llama.cpp locally
- **NVIDIA DGX Spark (Project DIGITS successor)** — compact desktop AI supercomputer, GB10 Grace
  Blackwell chip, 128 GB unified memory, ~1 PFLOP FP8 AI performance
- **NVIDIA GeForce RTX 5090** — 32 GB GDDR7, ~3,352 TOPS INT8, high parallel inference throughput
  in PCIe workstation or rack chassis

Selection criteria for each role:

| Role | Best fit | Why |
|------|----------|-----|
| Orchestration / coordination | Mac Mini M4 Pro | Low power, high concurrency, reliable scheduler host |
| Light agent processing (crawler, trend) | Mac Mini M4 | Lowest cost per concurrent process |
| LLM inference (7B–13B models) | DGX Spark | 128 GB unified memory; runs full 70B models locally |
| LLM inference (parallel batched requests) | RTX 5090 workstation | Highest token/s per dollar for smaller models |
| Heavy fine-tuning / training runs | RTX 5090 multi-GPU | 32 GB VRAM + FSDP sharding across cards |
| Shared storage NAS | Synology or TrueNAS | Cheap, redundant, easy NFS mount for all nodes |
| Networking fabric | 10 GbE managed switch | Sufficient for all tiers; upgrade to 25 GbE at 10× |

---

## 3. Tier 1 — Baseline: 100–200 Concurrent Agents

### 3.1 Rationale

The baseline tier runs AAA, Mouseion, and the ExMorbus PoC 24/7 for 3 months. This is enough to:

- complete the full AAA Phase 1 knowledge-discovery cycle at production quality
- pressure-test the Mouseion shell contracts through a real ExMorbus MoltBook-style loop
- produce a curated knowledge base with ~450,000 evaluated entries

### 3.2 Recommended Hardware Stack

#### Inference Cluster — 2× NVIDIA DGX Spark

| Attribute | Value |
|-----------|-------|
| Model | NVIDIA DGX Spark (GB10 Grace Blackwell) |
| GPU memory | 128 GB unified (20 GB VRAM GPU + 108 GB LPDDR5X CPU shared) |
| AI performance | 1 PFLOP FP8 per unit |
| TDP | ~300 W per unit |
| List price (2026) | ~$3,000 per unit |
| Quantity | 2 |
| Subtotal | ~$6,000 |

Why DGX Spark:
- Runs LLaMA 3.1 70B fully in memory on one unit. Critical for medical research-quality analysis.
- 128 GB unified memory means no model paging during long-context research extraction.
- Two units give ~100 concurrent small-model requests or ~20–30 concurrent 70B requests.
- Compact desktop form factor, minimal rack space, ~300 W each (lower OpEx than GPU workstations).
- ConnectX NIC for RDMA interconnect; two units can serve a distributed inference mesh over NVLink-C2C
  bridging.

#### Orchestration / Processing Cluster — 4× Mac Mini M4 Pro

| Attribute | Value |
|-----------|-------|
| Model | Mac Mini M4 Pro (14-core CPU / 20-core GPU) |
| RAM | 64 GB unified memory |
| Storage | 512 GB SSD (internal) |
| TDP | ~38 W average / 65 W peak |
| List price (2026) | ~$2,399 per unit |
| Quantity | 4 |
| Subtotal | ~$9,600 |

Each Mac Mini M4 Pro handles:
- Orchestrator scheduling (~200 concurrent async tasks per node via Python asyncio)
- CrawlerAgent pools (hundreds of lightweight HTTP coroutines per node)
- TrendTrackerAgent and ToolDiscoveryAgent (CPU/DB bound; macOS low-power scheduler is ideal)
- Light MLX inference backup when the DGX Sparks are saturated (7B models at ~15 req/s)

Four nodes give 800+ schedulable agent slots with comfortable headroom.

#### Training / Fine-Tuning Workstation — 1× RTX 5090 Workstation

| Attribute | Value |
|-----------|-------|
| GPU model | NVIDIA GeForce RTX 5090 |
| VRAM | 32 GB GDDR7 |
| AI performance | ~3,352 TOPS INT8 |
| GPU TDP | ~575 W |
| Chassis (e.g., SuperMicro SYS-740GP-TNRT) | ~$3,000–4,000 |
| GPU (RTX 5090) | ~$2,000–2,500 |
| RAM (128 GB DDR5) | ~$400 |
| NVMe (2 TB) | ~$200 |
| Total workstation build | ~$6,000–7,000 |
| Quantity | 1 |
| Subtotal | ~$6,500 |

Role in the baseline tier:
- Overnight fine-tuning of domain-adapted models using LoRA / QLoRA on the curated ExMorbus corpus
- Batch embedding generation for the vector store (high throughput, ~500K embeddings / hour)
- Fallback inference capacity during peak hours when DGX Sparks are busy

#### Shared Storage — 1× NAS Unit

| Component | Spec | Cost |
|-----------|------|------|
| Synology DS1823xs+ or TrueNAS Mini XL | 8-bay NAS | ~$1,200 |
| 8× 8 TB HDD (WD Red Pro) | 64 TB raw, ~48 TB usable (RAID 6) | ~$1,600 |
| 2× 4 TB NVMe cache (Samsung 990 Pro) | Read/write cache tier | ~$600 |
| 10 GbE dual-port card | NAS uplink | ~$200 |
| **NAS total** | | **~$3,600** |

Why separate NAS:
- All nodes mount the same SQLite → PostgreSQL data directory and vector index over NFS or SMB3.
- Research artifacts, ingested PDFs, and evaluation run history are durable and accessible from any
  node.
- At the baseline tier, 48 TB is more than sufficient for 3 months of intensive discovery.

#### Network Switch

| Component | Spec | Cost |
|-----------|------|------|
| Ubiquiti UniFi Pro 24-port PoE (10 GbE uplinks) | 10 GbE backbone | ~$800 |
| SFP+ DAC cables (×8) | node interconnect | ~$200 |
| **Switch total** | | **~$1,000** |

#### Tier 1 — Total Estimated Hardware Cost

| Component | Cost |
|-----------|------|
| 2× DGX Spark | $6,000 |
| 4× Mac Mini M4 Pro (64 GB) | $9,600 |
| 1× RTX 5090 workstation | $6,500 |
| NAS + drives | $3,600 |
| Network | $1,000 |
| Cables, UPS, misc | $500 |
| **Total (before tax / shipping)** | **~$27,200** |

#### Tier 1 — Monthly Operating Cost (Power)

| Component | Avg draw | Monthly kWh | Monthly cost (@ $0.14/kWh) |
|-----------|----------|-------------|----------------------------|
| 2× DGX Spark | 600 W | 432 kWh | $60 |
| 4× Mac Mini M4 Pro | 152 W (38 W × 4) | 110 kWh | $15 |
| RTX 5090 workstation | 650 W (active) / 100 W (idle) | ~280 kWh | $39 |
| NAS | 80 W | 58 kWh | $8 |
| Switch + misc | 50 W | 36 kWh | $5 |
| **Total monthly** | ~1,530 W avg | ~916 kWh | **~$128/month** |
| **3-month sprint OpEx** | | ~2,750 kWh | **~$385** |

#### Tier 1 — Capacity Summary

| Metric | Capacity |
|--------|----------|
| Max concurrent LLM requests (70B model) | ~30–40 |
| Max concurrent LLM requests (7B model) | ~200–300 |
| Max orchestrated agent slots | ~800 |
| Peak throughput (7B, short context) | ~1,500 tokens/sec aggregate |
| Storage for 3-month knowledge base | 48 TB (NAS) + ~6 TB SSD (nodes) |
| Embedding throughput | ~500K embeddings/hour (RTX 5090) |

**Verdict**: This stack comfortably handles 100–200 simultaneous agents running a full pipeline
(crawl → research → trend → tool → document) with the DGX Sparks providing the quality LLM
backbone needed for medical-domain work.

---

## 4. Tier 2 — 10× Scale: 1,000–2,000 Concurrent Agents

### 4.1 What Changes at 10×

At 2,000 agents, several limits are crossed:

1. **SQLite is no longer sufficient.** Replace with PostgreSQL + pgvector or Qdrant.
2. **Single-rack power budget is approached.** Need colocation or a dedicated machine room with
   30A/240V circuits.
3. **LLM inference becomes the hard bottleneck.** ~400 concurrent LLM calls during peak hours.
4. **Embedding generation outpaces a single GPU.** Need at least 4 GPU-class inference nodes.
5. **Network becomes a constraint.** 10 GbE is marginal; upgrade to 25 GbE backbone.

### 4.2 Recommended Hardware Stack

#### Inference Cluster — 8× DGX Spark (+ 2 from Tier 1 = 10 total)

| Component | Quantity | Unit cost | Subtotal |
|-----------|----------|-----------|----------|
| NVIDIA DGX Spark | 8 new (10 total) | $3,000 | $24,000 new |
| Total inference PFLOPS | 10 PFLOPS FP8 | | |
| Total inference memory | 1,280 GB unified | | |
| TDP (all 10) | 3,000 W | | |

Ten DGX Spark units form a mesh via Ethernet (or future NVLink Fusion if available) and can
collectively serve:
- ~250–300 concurrent 70B-class requests
- ~2,000+ concurrent 7B-class requests

Alternatively, replace 4 of the Sparks with 2× **RTX 5090 multi-GPU workstations** (2 GPUs each)
for lower cost and higher raw token throughput on 13B–34B models:

| Component | Quantity | Unit cost | Subtotal |
|-----------|----------|-----------|----------|
| RTX 5090 dual-GPU workstation | 2 new | $10,000 | $20,000 |
| RTX 5090 GPU VRAM available | 64 GB per workstation | | |

These workstations serve ExMorbus batch training jobs overnight while the DGX Sparks handle
real-time inference for the AAA research loop.

#### Orchestration Cluster — 8× Mac Mini M4 Pro (+ 4 from Tier 1 = 12 total)

| Component | Quantity | Unit cost | Subtotal |
|-----------|----------|-----------|----------|
| Mac Mini M4 Pro (64 GB) | 8 new (12 total) | $2,399 | $19,192 new |
| Total agent slots | ~2,400 scheduled slots | | |
| TDP (all 12) | ~456 W avg | | |

Optionally, replace 4 of the new Mac Minis with **2× Mac Studio M4 Ultra** (if available) for
higher per-node concurrency, especially for orchestration of the Mouseion adapter layer and the
ExMorbus training funnel coordinator.

#### Database / Vector Store Server — 1× Dedicated PostgreSQL Node

| Component | Spec | Cost |
|-----------|------|------|
| AMD Ryzen 9 7950X workstation | 16-core, 32-thread | ~$1,500 |
| 256 GB DDR5 ECC RAM | 4× 64 GB modules | ~$1,200 |
| 4× 4 TB NVMe (Samsung 990 Pro) | RAID 10 array = 8 TB | ~$1,200 |
| **Database node total** | | **~$3,900** |

Role: Primary PostgreSQL instance with pgvector extension. Handles:
- Knowledge base (replaces SQLite)
- Evaluation run history
- Source weight ledger
- Vector index for nearest-neighbor search (pgvector or Qdrant sidecar on same node)

#### Expanded NAS — Add 2× NAS Expansion Units

| Component | Spec | Cost |
|-----------|------|------|
| Synology RX1223RP (12-bay expansion) | Adds 12 bays per unit | ~$1,500 |
| 24× 8 TB HDD additional | 192 TB raw additional | ~$4,800 |
| **NAS expansion total** | | **~$6,300** |

#### Network Upgrade — 25 GbE Switch

| Component | Spec | Cost |
|-----------|------|------|
| Ubiquiti UniFi Pro 48 (25 GbE uplinks) | Core switch | ~$1,500 |
| 25 GbE DAC cables (×16) | Node interconnect | ~$600 |
| **Network upgrade total** | | **~$2,100** |

#### Tier 2 — Incremental Hardware Cost (beyond Tier 1)

| Component | Incremental cost |
|-----------|-----------------|
| 8× DGX Spark | $24,000 |
| 2× RTX 5090 dual-GPU workstations | $20,000 |
| 8× Mac Mini M4 Pro | $19,192 |
| PostgreSQL node | $3,900 |
| NAS expansion | $6,300 |
| Network upgrade | $2,100 |
| UPS upgrade, rack, misc | $2,000 |
| **Tier 2 incremental total** | **~$77,492** |
| **Tier 1 + Tier 2 cumulative total** | **~$104,700** |

#### Tier 2 — Monthly Operating Cost

| Component | Avg draw | Monthly kWh | Monthly cost |
|-----------|----------|-------------|--------------|
| 10× DGX Spark | 3,000 W | 2,160 kWh | $302 |
| 12× Mac Mini M4 Pro | 456 W | 329 kWh | $46 |
| 3× RTX 5090 workstations | 1,950 W avg | 1,404 kWh | $197 |
| DB node | 150 W | 108 kWh | $15 |
| NAS (expanded) | 180 W | 130 kWh | $18 |
| Switch + misc | 100 W | 72 kWh | $10 |
| **Total monthly** | ~5,836 W avg | ~4,203 kWh | **~$588/month** |
| **3-month sprint OpEx** | | ~12,600 kWh | **~$1,764** |

> Note: At this scale, a colocation facility or dedicated machine room is strongly recommended.
> Consumer-grade home electrical circuits (15A/120V) cannot sustain ~6 kW continuous draw without
> dedicated 30A/240V circuits and professional cooling.

---

## 5. Tier 3 — 100× Scale: 10,000–20,000 Concurrent Agents

### 5.1 What Changes at 100×

At 20,000 agents, the architecture crosses from a high-end home/office lab into a small datacenter:

1. **On-premises inference alone cannot serve 4,000 concurrent LLM calls economically.** A hybrid
   cloud inference strategy is required (on-prem for research-grade 70B work; cloud API for burst
   load at lower-quality tiers).
2. **Power draw exceeds 20 kW.** Requires a dedicated server room, 3-phase power, and precision
   cooling (CRAC units, liquid cooling).
3. **Storage scales to multiple petabytes** — NAS becomes inadequate; a Ceph cluster or enterprise
   all-flash array is required.
4. **Orchestration moves to Kubernetes** with autoscaling pods replacing the fixed Mac Mini fleet.
5. **Network requires a 100 GbE leaf-spine topology** with RDMA for inter-GPU traffic.

### 5.2 Recommended Architecture

#### Inference Layer — On-Prem Cluster: 4× NVIDIA HGX H100/H200 or DGX H100 Nodes

| Component | Spec | Unit cost |
|-----------|------|-----------|
| NVIDIA HGX H100 (8× H100 SXM5, 640 GB total) | Server chassis + 8× H100 80 GB | ~$300,000 |
| Quantity | 4 nodes | |
| Total GPU memory | 2,560 GB | |
| Total AI performance | ~32 PFLOPS FP8 | |
| **HGX cluster cost** | | **~$1,200,000** |

Alternatively, a more cost-effective option for this scale:

**32× NVIDIA DGX Spark** (consumer-grade, no maintenance contract):

| Component | Quantity | Unit cost | Subtotal |
|-----------|----------|-----------|----------|
| DGX Spark | 32 units | $3,000 | $96,000 |
| Total PFLOPS | 32 PFLOPS FP8 | | |
| Total memory | 4,096 GB unified | | |
| TDP | ~9,600 W | | |

The DGX Spark cluster is ~12× cheaper for comparable FP8 PFLOPS but lacks NVLink SXM bandwidth.
For research-quality 70B inference (not sub-100ms latency production serving), the Spark cluster
is the right choice. Reserve HGX-class hardware for post-PoC production phases.

#### Burst Load Offload — Cloud API Tier

For the fraction of agent work that can tolerate higher latency or uses smaller models:

| Service | Use case | Est. monthly cost at 100× |
|---------|----------|--------------------------|
| Together.ai or Groq | Fast 7B–13B inference burst | ~$5,000–10,000/month |
| OpenAI GPT-4o mini | High-quality extraction fallback | ~$2,000–5,000/month |
| Anthropic Claude Haiku | Document summarization | ~$1,000–3,000/month |

Hybrid rule: on-prem DGX Sparks serve 70B research requests; cloud APIs absorb burst beyond
on-prem capacity.

#### Orchestration Layer — Kubernetes on Mac Studio M4 Ultra (×8) or ARM Server Rack

| Option | Spec | Cost |
|--------|------|------|
| 8× Mac Studio M4 Ultra (expected 2026) | 24-core CPU, 192 GB memory | ~$10,000 × 8 = $80,000 |
| Alternative: 4× ARM rack server (Ampere Altra Q80) | 80-core, 512 GB RAM each | ~$8,000 × 4 = $32,000 |

The ARM server option offers better Kubernetes pod density. The Mac Studio option maintains
ecosystem consistency and supports MLX fallback inference.

#### Database Cluster — 3-Node PostgreSQL HA + Ceph Object Store

| Component | Spec | Cost |
|-----------|------|------|
| 3× PostgreSQL HA node (AMD EPYC, 512 GB RAM, 8× 4 TB NVMe) | Primary + 2 replicas | ~$15,000 × 3 = $45,000 |
| 6× Ceph storage node (2× 25 GbE, 12× 16 TB HDD, 2× 4 TB NVMe) | ~1.1 PB usable (3-way replica) | ~$12,000 × 6 = $72,000 |
| **Storage cluster total** | | **~$117,000** |

#### Network — 100 GbE Leaf-Spine

| Component | Spec | Cost |
|-----------|------|------|
| 4× Arista 7050CX3-32S (32× 100 GbE) | Spine switches | ~$20,000 × 4 = $80,000 |
| 8× Arista 7060CX2-32S (leaf) | Leaf switches | ~$15,000 × 8 = $120,000 |
| QSFP28 cables + fiber | Interconnect | ~$15,000 |
| **Network total** | | **~$215,000** |

> For a cost-conscious 100× deployment, replace enterprise switches with Mellanox SN2010 25/100 GbE
> switches (~$3,000 each) and use RDMA over Converged Ethernet (RoCEv2) for GPU-to-GPU traffic.
> Total network cost drops to ~$40,000–60,000.

#### Tier 3 — Estimated Total Capital Cost

| Component | Cost |
|-----------|------|
| 32× DGX Spark inference cluster | $96,000 |
| Orchestration layer (8× Mac Studio or ARM) | $80,000 |
| PostgreSQL HA + Ceph storage | $117,000 |
| 100 GbE network | $215,000 (or ~$50,000 budget option) |
| Power distribution + PDUs + UPS (3-phase) | $30,000 |
| Precision cooling (CRAC units) | $25,000 |
| Colocation or dedicated machine room build-out | $20,000–50,000 |
| Misc (cables, racks, labor) | $10,000 |
| **Total (premium networking)** | **~$593,000** |
| **Total (budget networking option)** | **~$428,000** |

Cloud hybrid OpEx (3 months) at 100×:
| Cost Item | 3-Month Estimate |
|-----------|-----------------|
| On-prem power (~30 kW avg) | ~$18,000 |
| Cloud API burst (Together.ai + OpenAI) | ~$24,000–54,000 |
| Colo or facility OpEx | ~$6,000–15,000 |
| **Total 3-month OpEx** | **~$48,000–87,000** |

---

## 6. Hardware Comparison Matrix

| Metric | Mac Mini M4 Pro | DGX Spark (GB10) | RTX 5090 Workstation |
|--------|----------------|------------------|-----------------------|
| Primary role | Orchestration / CPU agents | LLM inference (quality) | LLM inference (throughput) + training |
| GPU / NPU memory | 64 GB unified | 128 GB unified | 32 GB GDDR7 |
| FP8 AI TOPS | ~11 (GPU only) | ~1,000 (PFLOP) | ~3,352 TOPS |
| 70B model (full) | ❌ (not enough memory) | ✅ (fits in 128 GB) | ❌ (requires 2+ 5090s) |
| 7B model concurrent req/s | ~15 (MLX) | ~100–150 | ~150–300 |
| TDP | 38 W avg | 300 W | 575 W (GPU only) |
| Form factor | Desktop | Desktop | Workstation / rack |
| Price (2026 est.) | ~$2,399 (64 GB) | ~$3,000 | ~$6,000–7,000 (full system) |
| Cost per PFLOP (FP8) | ~$218/TFLOP | ~$3/TFLOP | ~$2/TFLOP |
| Best for 3-month sprint | Orchestration layer | Quality inference backbone | Training + throughput burst |
| Scales via | Ethernet cluster | NVLink Fusion / Ethernet | NVLink (2×) + PCIe |
| macOS / MLX support | ✅ Native | ✅ ARM Linux (Ubuntu); no macOS | ❌ (Linux/Windows only) |

---

## 7. Recommended Starter Configuration for the 3-Month Sprint

Start with the Tier 1 stack. Do not over-purchase infrastructure before the research loop
validates what the real compute bottleneck is.

**Order of operations:**

### Month 0 — Setup (before sprint begins)

1. Purchase **2× DGX Spark** for inference backbone. These ship relatively fast and are the
   highest-leverage buy: running LLaMA 3.1 70B locally is what separates a research-quality
   ExMorbus from a GPT-wrapper.
2. Purchase **2× Mac Mini M4 Pro (64 GB)** for orchestration. Run the Orchestrator, CrawlerAgent
   pool, and TrendTrackerAgent here.
3. Use existing development machines or a $200/month VPS for the RTX 5090 workstation role (cloud
   GPU from Lambda Labs or RunPod) until you need to commit to on-prem training hardware.
4. Set up the NAS with at least 16 TB usable before the sprint begins.

Estimated Month 0 hardware spend: **~$12,000**

### Month 1 — Validate and Profile

Run the system at 50–100 agents. Measure:
- DGX Spark GPU utilization (target: 60–80% sustained)
- Orchestration CPU (target: <50% sustained on Mac Minis)
- SQLite query latency (trigger PostgreSQL migration if > 100ms P95)
- Storage growth rate (validate NAS runway)

Buy the **RTX 5090 workstation** only after validating that overnight fine-tuning is actually
producing higher-quality research outputs. Budget: **~$6,500**

### Month 2 — Scale to Baseline Ceiling

Add **2× more Mac Mini M4 Pro** to reach 4-node orchestration cluster.
Add **1× more DGX Spark** if GPU utilization sustained above 80%.

Month 2 incremental spend: **~$7,200**

### Month 3 — Sprint at Full Baseline

All 200 agent slots active. Document:
- actual throughput (LLM calls/hour achieved vs. designed)
- discovered knowledge quality (measured by evaluation harness scores)
- storage burn rate (validate 10× planning assumptions)

Use Month 3 data to justify and size the 10× investment.

---

## 8. Upgrade Path Summary

| Phase | Hardware investment | Cumulative CapEx | Agent capacity | Monthly OpEx |
|-------|--------------------|--------------------|---------------|--------------|
| Baseline sprint (Tier 1) | ~$27,200 | ~$27,200 | 100–200 | ~$128 |
| After sprint — add Tier 2 | ~$77,500 | ~$104,700 | 1,000–2,000 | ~$588 |
| After validation — add Tier 3 | ~$400,000–565,000 | ~$505,000–670,000 | 10,000–20,000 | ~$16,000–29,000 |

---

## 9. Key Constraints and Risks

### 9.1 RTX 5090 Availability

As of early 2026, RTX 5090 cards remain constrained by TSMC CoWoS allocation. MSRP is ~$1,999 but
street prices are $2,500–$3,000+. If availability is poor, substitute 2× RTX 5080 (16 GB GDDR7,
~$1,000 each) for the initial training workstation and upgrade to a 5090 once supply normalises.

### 9.2 DGX Spark Cluster Interconnect

DGX Spark units are not NVLink-connected to each other in the GB10 generation. Multi-unit inference
requires the vLLM tensor-parallel feature over Ethernet (10–25 GbE). This means 70B inference
across multiple units incurs non-trivial latency vs. a single large-VRAM system. Benchmark this
before committing to a 10-unit cluster over a single HGX node.

### 9.3 Power Infrastructure

At Tier 2 (~6 kW) and Tier 3 (~30 kW), standard residential or small-office power panels cannot
support the load. Budget for electrical upgrade (dedicated 30A/240V circuits at Tier 2;
3-phase 100A at Tier 3) before hardware arrives.

### 9.4 Cooling

Each DGX Spark exhausts ~300 W. Four units in a small office will raise room temperature
meaningfully. At Tier 2 (10 units = 3 kW), a portable precision cooling unit (~$2,000–3,000) is
required. At Tier 3, CRAC units are mandatory.

### 9.5 Software Migration Points

| Scale | Trigger | Action |
|-------|---------|--------|
| >1 M KB entries | SQLite P95 latency > 100ms | Migrate to PostgreSQL + pgvector |
| >50 concurrent GPU requests | DGX Spark sustained > 80% | Add a second inference unit |
| >200 agents | Orchestration CPU > 60% | Add Mac Mini node to cluster |
| >10× scale | Orchestration complexity | Migrate to Kubernetes |
| >100× scale | On-prem inference undersized | Adopt hybrid cloud API for burst tier |

---

## 10. Relation to the Current Roadmap

This hardware plan supports the following documented decisions and tracks:

- `docs/research-training-cycle-v1.md` — 3-month intensive discovery cycle that this hardware
  sustains
- `docs/exmorbus-moltbook-poc-scope-v1.md` — ExMorbus PoC training funnel and agent-economy loop
  that requires quality 70B inference (DGX Spark backbone)
- `docs/phase-5-implementation-plan.md` — Phases 1–5 can be completed within the Tier 1 hardware
  budget; Phase 6+ (self-improvement, production hardening) maps to Tier 2
- `docs/mouseion-core-v0.md` — Mouseion shared substrate runs as an API layer on the orchestration
  cluster; no dedicated hardware needed at Tier 1

The hardware strategy does not change the software architecture. It enables the planned software
architecture to run at the intended scale and duration.

---

## Related Documents

- `docs/research-training-cycle-v1.md`
- `docs/exmorbus-moltbook-poc-scope-v1.md`
- `docs/phase-5-implementation-plan.md`
- `docs/mouseion-core-v0.md`
- `docs/exmorbus-v3-integration.md`
- `docs/decision-log.md`
