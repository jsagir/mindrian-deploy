# Swarm Strategy Guide

Deep-dive on execution strategies for multi-agent orchestration.

## Strategy Selection Decision Tree

```
Query Received
    │
    ├─ Simple question? ──────────────> Single Agent (no swarm needed)
    │
    ├─ Unknown domain? ───────────────> Research First Pipeline
    │   └─ Research → Relevant Agents → Synthesis
    │
    ├─ Multiple perspectives needed? ─> Fan-Out (Parallel)
    │   └─ All agents run simultaneously
    │
    ├─ Progressive refinement? ───────> Pipeline (Sequential)
    │   └─ Each agent builds on previous
    │
    ├─ Challenging assumptions? ──────> Debate
    │   └─ Agent → Red Team → Agent rebuttal
    │
    └─ Unknown complexity? ───────────> Escalation
        └─ Start quick, deepen if needed
```

## Fan-Out Strategy

**Implementation:** `agents/multi_agent_graph.py` → `run_parallel_workflow()`

```python
async def run_parallel_workflow(query: str, agents: List[str]) -> SwarmReport:
    """Run all agents in parallel, then synthesize."""
    tasks = [call_agent(agent, query) for agent in agents]
    results = await asyncio.gather(*tasks)
    synthesis = await synthesize_responses(query, results)
    return SwarmReport(...)
```

**Strengths:**
- Fastest total time (parallel execution)
- Independent perspectives (no contamination)
- Easy to add/remove agents

**Weaknesses:**
- No agent can build on another's insight
- May produce contradictory outputs
- Synthesis is challenging

**Best for:**
- "What do different experts think about X?"
- Initial brainstorming
- Diverse perspective gathering

## Pipeline Strategy

**Implementation:** `agents/multi_agent_graph.py` → `run_sequential_workflow()`

```python
async def run_sequential_workflow(query: str, agents: List[str]) -> SwarmReport:
    """Chain agents, each building on previous output."""
    context = ""
    results = {}
    for agent in agents:
        response = await call_agent(agent, query, context=context)
        results[agent] = response
        context += f"\n[{agent}]: {response}"
    return SwarmReport(...)
```

**Strengths:**
- Each agent has full context
- Progressive refinement
- Natural flow of reasoning

**Weaknesses:**
- Slower (sequential)
- Early agents bias later ones
- Error propagation

**Best for:**
- Research → Analysis → Synthesis
- Progressive validation
- Building on discoveries

## Debate Strategy

**Implementation:** Composed from pipeline with alternating perspectives.

```python
async def run_debate(query: str, protagonist: str = "larry") -> SwarmReport:
    """Agent proposes, Red Team challenges, Agent rebuts."""
    # Round 1: Initial proposal
    proposal = await call_agent(protagonist, query)

    # Round 2: Red Team challenge
    challenge = await call_agent("redteam", query,
        context=f"Challenge this proposal: {proposal}")

    # Round 3: Rebuttal
    rebuttal = await call_agent(protagonist, query,
        context=f"Proposal: {proposal}\nChallenge: {challenge}\nNow respond to the challenge.")

    return SwarmReport(synthesis=rebuttal, dissent=challenge, ...)
```

**Strengths:**
- Forces confrontation of assumptions
- Builds conviction through challenge
- Reveals blind spots

**Weaknesses:**
- Can be adversarial/uncomfortable
- May overweight dissent
- Requires strong synthesis

**Best for:**
- Major decisions
- Investment theses
- Assumptions that need testing

## Escalation Strategy

**Implementation:** `protocols/auto_orchestrator.py` → `AutoOrchestrator.run()`

```python
class AutoOrchestrator:
    async def run(self, query: str, max_depth: str = "auto") -> SwarmReport:
        # Level 1: Quick pulse (2 agents)
        quick_result = await self.quick_pulse(query)
        if quick_result.confidence > 0.8 or max_depth == "quick":
            return quick_result

        # Level 2: Standard analysis (4 agents)
        standard_result = await self.standard_analysis(query)
        if standard_result.confidence > 0.7 or max_depth == "standard":
            return standard_result

        # Level 3: Full swarm (all + research)
        return await self.full_analysis(query)
```

**Strengths:**
- Respects user's time
- Automatic complexity detection
- Progressive investment

**Weaknesses:**
- May under-analyze complex queries
- Confidence thresholds are heuristic
- Can feel inconsistent

**Best for:**
- Unknown query types
- Default swarm invocation
- When "just figure it out"

## Background Agents Integration

Background agents have tool access and run alongside conversation agents:

| Agent | Tools | When Included |
|-------|-------|---------------|
| `research` | Tavily, web search | Unknown domain queries |
| `validation` | Camera Test, fact-check | Claims that need verification |
| `analysis` | LangExtract, patterns | Data-heavy queries |

```python
from agents.multi_agent_graph import run_enhanced_workflow

result = await run_enhanced_workflow(
    query="Is vertical farming economically viable?",
    conversation_agents=["larry", "tta", "ackoff"],
    background_agents=["research", "validation"]
)
```

## Synthesis Pattern Customization

### Integrative Synthesis
```python
synthesis_prompt = """
You have received perspectives from multiple experts.
Create a UNIFIED narrative that weaves together their insights.
Do not list agent names - speak as one coherent voice.
"""
```

### Comparative Synthesis
```python
synthesis_prompt = """
Present a comparison table:
| Aspect | Agent A View | Agent B View | Resolution |
Highlight where experts agree and where they differ.
"""
```

### Consensus Synthesis
```python
synthesis_prompt = """
Identify themes ALL agents mentioned.
Lead with: "All perspectives agree that..."
Then note any outlier views briefly.
"""
```

### Prioritized Synthesis
```python
synthesis_prompt = """
From all agent inputs, distill:
1. Top recommendation (most supported)
2. Second priority
3. Third priority

For each, note which agents support it.
"""
```

## Performance Benchmarks

| Strategy | Agents | Avg Time | Token Usage |
|----------|--------|----------|-------------|
| Quick Pulse | 2 | ~8s | ~2K |
| Fan-Out (4) | 4 | ~12s | ~4K |
| Pipeline (4) | 4 | ~25s | ~6K |
| Debate | 3 rounds | ~20s | ~5K |
| Full Swarm | 6+ | ~45s | ~10K |

## Error Handling

```python
try:
    result = await run_parallel_workflow(query, agents)
except AgentTimeoutError as e:
    # One agent timed out - continue with others
    partial_result = e.partial_results
    result = await synthesize_responses(query, partial_result)
except AllAgentsFailedError:
    # Fall back to single Larry response
    result = await call_agent("larry", query)
```
