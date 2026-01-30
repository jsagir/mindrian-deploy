# R&D 17: Agentic Tool Use

## Status: Research

## What Is This?

LLM agents that dynamically select and execute tools based on reasoning, rather than predefined tool sequences.

## Why Implement This?

### Current State
- Tools are explicitly called via action buttons
- No dynamic tool selection based on context
- Multi-step reasoning requires manual orchestration

### Solution: Agentic Patterns
Enable Larry/bots to:
1. Reason about which tools would help
2. Select and execute tools autonomously
3. Chain tool calls for multi-step problems
4. Recover from tool errors gracefully

## Research Areas

### 1. ReAct Pattern
- Reasoning + Acting in interleaved steps
- Thought → Action → Observation loop
- Reference: [ReAct paper](https://arxiv.org/abs/2210.03629)

### 2. Tool Selection
- Tool description embedding for semantic matching
- Confidence thresholds for auto-execution
- User approval workflows for sensitive tools

### 3. Multi-Step Planning
- Plan generation before execution
- Plan revision based on intermediate results
- Backtracking on tool failures

### 4. Error Recovery
- Tool failure detection
- Alternative tool selection
- Graceful degradation messaging

## Integration Points

- `tools/` directory has 15+ tools available
- MCP tools configured in `.chainlit/config.toml`
- Neo4j has 35 `ResearchTool` nodes with descriptions

## Research Resources

- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Instructor Library](https://github.com/jxnl/instructor)

## Estimated Effort

- Design: 8-12 hours
- Implementation: 20-30 hours
- Testing: 10-15 hours

## Status Checklist

- [ ] Research ReAct patterns
- [ ] Define tool schema format
- [ ] Implement reasoning loop
- [ ] Add confidence thresholds
- [ ] User approval UI
- [ ] Error recovery
- [ ] Testing

---

*Created: 2026-01-30*
