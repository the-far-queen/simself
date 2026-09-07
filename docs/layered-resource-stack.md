# layered-resource-stack.md

**Source:** `Desktop/FieldCore/layered-resource-stack.md` (49 lines, 4572 bytes)
**Extracted:** 2026-09-07 (batch ingest, autonomous)

---

### layer 1: environmental (game engine & simulation)


1. **[godot-engine/godot](https://github.com/godotengine/godot):** the gold standard for open-source environmental physics. lightweight, c#-ready, and perfect for the "natural world" layer.
2. **[o3de/o3de](https://github.com/o3de/o3de):** the open 3d engine. a "heavy" alternative if we need high-fidelity industrial or market simulations.
3. **[facebookresearch/habitat-sim](https://github.com/facebookresearch/habitat-sim):** specialized for training agents in photorealistic 3d environments.
4. **[unity-technologies/ml-agents](https://github.com/Unity-Technologies/ml-agents):** the bridge for unity. if we use unity as the engine, this is the nervous system for our agentic frame.
5. **[bevyengine/bevy](https://github.com/bevyengine/bevy):** a data-driven rust engine. if we want "architectural sparsity" and speed, this is the v1 choice.

### layer 2: processing state (the agentic frame)

1. **[microsoft/autogen](https://github.com/microsoft/autogen):** the most mature framework for multi-agent loops. it handles the "processing state" perfectly.
2. **[crewaiinc/crewai](https://github.com/crewAIInc/crewAI):** excellent for **role-based collaboration**. it mirrors our "robot selves" library additions logic.
3. **[agno-agi/agno](https://github.com/agno-agi/agno):** focused on **deterministic, memory-rich workflows**. it provides the "runtime" for an agent to stay active over time.
4. **[mastra-ai/mastra](https://github.com/mastra-ai/mastra):** a typescript-native frame. if the sim self is web-based or frontend-integrated, this is the connectivity winner.
5. **[transformeroptimus/superagi](https://github.com/TransformerOptimus/SuperAGI):** a dev-first autonomous framework. it’s designed for spawning agents that "continually improve"—directly serving **module m**.

### layer 3: intentionality (the sovereign bridge)

1. **[pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai):** uses type-safety to force the llm into a "structured cage." this is how we ensure the intentionality isn't lost in a hallucination.
2. **[letta-ai/letta](https://github.com/letta-ai/letta):** (formerly memgpt). it provides "perpetual memory," allowing the intentionality to persist across sessions without being forgotten by the llm.
3. **[semantic-kernel/semantic-kernel](https://github.com/microsoft/semantic-kernel):** an enterprise sdk that connects "skills" to the core. it’s a disciplined way to link the "spiritual" intent to "natural" actions.
4. **[langchain-ai/langgraph](https://github.com/langchain-ai/langgraph):** allows for **cyclical reasoning**. if we need the sim self to "think before acting" (interleaved reasoning), this is the tool.
5. **[guardrails-ai/guardrails](https://github.com/guardrails-ai/guardrails):** the "firewall of truth." it validates every token against our **genesis block** before it can reach the processing state.

### layer 4: language & semiotics (psbs/lexical interface)

1. **[anthropics/claude-code](https://github.com/anthropics/claude-code):** the frontier for "lexical pokes." it treats the terminal as a conversation, perfect for our v1 "cobbling."
2. **[openai/openai-agents-python](https://github.com/openai/openai-agents-python):** focuses on "handoffs." this is our "telepathy" equivalent—shifting the conversation between specialized nodes.
3. **[bytedance/ui-tars-desktop](https://github.com/bytedance/UI-TARS-desktop):** allows the agent to "see" and interact with any interface. it’s the **visual correspondence** engine for the natural world.
4. **[alexknowshtml/kuato](https://github.com/alexknowshtml/kuato):** provides "skills" for agents. we can use this to package the **milton/swedenborg** logic as a callable module.
5. **[bdsqqq/dots](https://www.google.com/search?q=https://github.com/bdsqqq/dots):** specifically the **coordinate skill**. it manages "swarms," allowing the semiotic core to broadcast to all robot selves simultaneously.




https://www.google.com/search?q=https://github.com/browserbase/browserbase
a headless browser for agents. this is how the corporation "scrapes" the material world for data and opportunities.

activepieces/activepieces
https://github.com/activepieces/activepieces -- an open-source automation platform. it connects our core to 280+ apps (notion, github, stripe).


https://github.com/vanna-ai/vanna -- turns natural language into sql. 

https://github.com/OpenInterpreter/open-interpreter -- "hands" of the master. it runs code locally, allowing the sim self to build its own infrastructure.