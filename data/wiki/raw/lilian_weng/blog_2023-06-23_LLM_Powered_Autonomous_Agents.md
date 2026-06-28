# LLM Powered Autonomous Agents
url: https://lilianweng.github.io/posts/2023-06-23-agent/
author: Lilian Weng
published_at: 2023-06-23
persona_id: lilian_weng

---

Building agents with LLM (large language model) as its core controller is a cool concept. Several proof-of-concepts demos, such as AutoGPT , GPT-Engineer and BabyAGI , serve as inspiring examples. The potentiality of LLM extends beyond generating well-written copies, stories, essays and programs; it can be framed as a powerful general problem solver. Agent System Overview In a LLM-powered autonomous agent system, LLM functions as the agent’s brain, complemented by several key components: Planning Subgoal and decomposition: The agent breaks down large tasks into smaller, manageable subgoals, enabling efficient handling of complex tasks. Reflection and refinement: The agent can do self-criticism and self-reflection over past actions, learn from mistakes and refine them for future steps, thereby improving the quality of final results. Memory Short-term memory: I would consider all the in-context learning (See Prompt Engineering ) as utilizing short-term memory of the model to learn. Long-term memory: This provides the agent with the capability to retain and recall (infinite) information over extended periods, often by leveraging an external vector store and fast retrieval. Tool use The agent learns to call external APIs for extra information that is missing from the model weights (often hard to change after pre-training), including current information, code execution capability, access to proprietary information sources and more. Overview of a LLM-powered autonomous agent system. Component One: Planning A complicated task usually involves many steps. An agent needs to know what they are and plan ahead.
