---
description: Expert in LangChain - building LLM apps with agents, chains, and RAG. Use for ReAct agents, tool calling, vector stores, memory management.
---

# LangChain

Read the full guide: `skills/langchain/SKILL.md`

## Quick Start

```python
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent

agent = create_agent(
    model=ChatAnthropic(model="claude-sonnet-4-5-20250929"),
    tools=[get_weather, search_web],
    system_prompt="You are a helpful assistant."
)

result = agent.invoke({"messages": [{"role": "user", "content": "What's the weather?"}]})
```

## Key Concepts

- **Models**: LLM abstraction (swap providers easily)
- **Chains**: Sequential operations
- **Agents**: Tool-using reasoning (ReAct)
- **Memory**: Conversation history
- **RAG**: Retrieval-augmented generation

$ARGUMENTS
