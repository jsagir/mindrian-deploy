# Genesis Expert Breakdown Engine + Swarm + LangGraph Integration

## Overview

The **agents-midrian** folder contains a sophisticated multi-agent expert panel system called the "Genesis Engine". This document outlines how to integrate it with **OpenAI Swarm** for agent coordination and **LangGraph** for stateful workflow orchestration.

## Source Files

Located at: `/home/jsagi/Mindrian/agents-midrian/`

| File | Stage | Purpose |
|------|-------|---------|
| `decompose_context.py` | 1 | Break challenge into semantic segments |
| `identify_domains.py` | 2 | Pattern match against 24 domain signatures |
| `generate_personas.py` | 3 | Create expert personas with competencies |
| `orchestrate_research.py` | 4 | Generate execution plans, collaboration matrices |
| *(Agent-conducted)* | 5 | 4-round expert panel discussion |
| `synthesize_breakthroughs.py` | 6 | Score, validate, rank breakthroughs |

## Current Architecture

```
Challenge Text
      ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 1: CONTEXT DECOMPOSITION                         │
│  - Segment into coherent chunks                         │
│  - Extract: concepts, technologies, methodologies       │
│  - Complexity scoring                                   │
└─────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 2: DOMAIN IDENTIFICATION                         │
│  - 14 technical domains (ML, Quantum, Blockchain...)    │
│  - 10 non-technical (FinTech, Climate, Geopolitical...) │
│  - Subdomain discovery (RAG-Systems, DeFi, etc.)        │
│  - Confidence scoring per domain                        │
└─────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 3: PERSONA GENERATION                            │
│  - Domain experts (PRIMARY, SUBDOMAIN)                  │
│  - Methodology validator                                │
│  - Integration architect (cross-domain synthesizer)     │
│  - Each has: competencies, query strategies, biases     │
└─────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 4: RESEARCH ORCHESTRATION                        │
│  - 4-phase execution plan                               │
│  - Collaboration matrix (pairwise interactions)         │
│  - Quality controls, synthesis strategy                 │
│  - Timeline estimation                                  │
└─────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 5: EXPERT PANEL (4 Rounds)                       │
│  Round 1: Domain presentations                          │
│  Round 2: Cross-domain connections                      │
│  Round 3: Breakthrough ideation                         │
│  Round 4: Implementation planning                       │
└─────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────┐
│  Stage 6: BREAKTHROUGH SYNTHESIS                        │
│  - Multi-criteria scoring (potential, feasibility...)   │
│  - Validation gates (evidence, cross-domain, impl)      │
│  - Ranked opportunities                                 │
│  - Implementation roadmaps                              │
└─────────────────────────────────────────────────────────┘
```

## Integration Vision

### 1. LangGraph for Workflow Orchestration

LangGraph provides the **state machine** backbone for the 6-stage pipeline:

```python
from langgraph.graph import StateGraph, END

class GenesisState(TypedDict):
    challenge: str
    decomposition: dict
    domains: dict
    personas: list
    research_plan: dict
    panel_findings: dict
    synthesis: dict
    current_stage: int

def create_genesis_graph():
    graph = StateGraph(GenesisState)

    # Add nodes
    graph.add_node("decompose", decompose_context_node)
    graph.add_node("identify_domains", identify_domains_node)
    graph.add_node("generate_personas", generate_personas_node)
    graph.add_node("orchestrate_research", orchestrate_research_node)
    graph.add_node("expert_panel", expert_panel_node)  # Swarm integration
    graph.add_node("synthesize", synthesize_breakthroughs_node)

    # Linear flow with checkpoints
    graph.add_edge("decompose", "identify_domains")
    graph.add_conditional_edges("identify_domains", domain_checkpoint)
    graph.add_edge("generate_personas", "orchestrate_research")
    graph.add_edge("orchestrate_research", "expert_panel")
    graph.add_edge("expert_panel", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile(checkpointer=PostgresSaver(db))
```

### 2. Swarm for Multi-Agent Expert Panel

OpenAI Swarm handles **Stage 5** - the expert panel discussion where multiple AI personas interact:

```python
from swarm import Swarm, Agent

def create_expert_agents(personas: list) -> list[Agent]:
    """Convert Genesis personas to Swarm agents."""
    agents = []

    for persona in personas:
        agent = Agent(
            name=persona["name"],
            model="gpt-4-turbo",  # or gemini
            instructions=f"""You are {persona['name']}, an expert in {persona['primaryExpertise']}.

            Expertise depth: {persona['expertiseDepth']}

            Your competencies:
            - Core: {', '.join(persona['competencies']['core'])}
            - Technical: {', '.join(persona['competencies']['technical'])}

            Research approach: {persona['researchApproach']['primary']}

            Your perspective:
            - Focus: {persona['perspectiveTraits']['focus']}
            - Bias: {persona['perspectiveTraits']['bias']}
            - Blind spot: {persona['perspectiveTraits']['blindSpot']}

            In panel discussions:
            - {persona['collaborationStyle']['role']}: {persona['collaborationStyle']['approach']}
            """,
            functions=[
                search_tavily,  # Each persona can search
                propose_connection,  # Flag cross-domain opportunities
                challenge_claim,  # Red team function
                synthesize_insight,  # Integration function
            ]
        )
        agents.append(agent)

    return agents

async def run_expert_panel(personas: list, research_findings: dict) -> dict:
    """Run 4-round Swarm panel discussion."""
    swarm = Swarm()
    agents = create_expert_agents(personas)

    # Round 1: Domain presentations
    presentations = {}
    for agent in agents:
        response = swarm.run(
            agent=agent,
            messages=[{
                "role": "user",
                "content": f"Present your domain's key findings from this research: {research_findings}"
            }]
        )
        presentations[agent.name] = response.messages[-1]["content"]

    # Round 2: Cross-domain connections
    connections = []
    integration_agent = next(a for a in agents if "Integration" in a.name)
    for i, agent in enumerate(agents):
        for other_agent in agents[i+1:]:
            response = swarm.run(
                agent=integration_agent,
                messages=[{
                    "role": "user",
                    "content": f"Find connections between {agent.name}'s insights and {other_agent.name}'s insights:\n\n{presentations[agent.name]}\n\n{presentations[other_agent.name]}"
                }]
            )
            connections.append(response.messages[-1]["content"])

    # Round 3: Breakthrough ideation
    breakthroughs = swarm.run(
        agent=integration_agent,
        messages=[{
            "role": "user",
            "content": f"Based on all presentations and connections, identify breakthrough opportunities:\n\n{json.dumps(presentations)}\n\n{json.dumps(connections)}"
        }]
    )

    # Round 4: Implementation planning
    implementation = swarm.run(
        agent=integration_agent,
        messages=[{
            "role": "user",
            "content": f"Create implementation plans for the top breakthroughs: {breakthroughs.messages[-1]['content']}"
        }]
    )

    return {
        "presentations": presentations,
        "connections": connections,
        "breakthroughs": breakthroughs.messages[-1]["content"],
        "implementation": implementation.messages[-1]["content"]
    }
```

### 3. Integration with Mindrian

The Genesis Engine integrates with existing Mindrian infrastructure:

```python
# intelligence/pipelines/genesis_engine.py

from langgraph.graph import StateGraph
from swarm import Swarm

# Import existing Genesis modules
from agents_midrian.decompose_context import decompose_context
from agents_midrian.identify_domains import identify_domains
from agents_midrian.generate_personas import generate_personas
from agents_midrian.orchestrate_research import orchestrate_research
from agents_midrian.synthesize_breakthroughs import synthesize_breakthroughs

# Import existing Mindrian integrations
from tools.tavily_search import tavily_search
from tools.graphrag_lite import enrich_for_larry
from utils.supabase_client import supabase

async def run_genesis_pipeline(
    challenge: str,
    session_id: str,
    user_id: str = None,
) -> dict:
    """
    Run full Genesis Expert Breakdown pipeline.

    Integrates:
    - LangGraph for workflow state
    - Swarm for expert panel
    - Tavily for research
    - Neo4j for knowledge persistence
    """
    # Stage 1: Decompose
    decomposition = decompose_context(challenge)

    # Stage 2: Identify domains
    domains = identify_domains(decomposition)

    # User checkpoint: Confirm domain map
    # (In Chainlit, this would be an action callback)

    # Stage 3: Generate personas
    personas = generate_personas(domains, decomposition["complexity"])

    # Stage 4: Orchestrate research
    plan = orchestrate_research(personas["personas"], challenge)

    # Execute Tavily searches per persona
    research_findings = {}
    for persona in personas["personas"]:
        findings = []
        for query in persona["queryStrategies"][:3]:
            results = await tavily_search(query)
            findings.extend(results.get("results", []))
        research_findings[persona["name"]] = findings

    # Stage 5: Expert panel (Swarm)
    panel_findings = await run_expert_panel(
        personas["personas"],
        research_findings
    )

    # Stage 6: Synthesize
    synthesis = synthesize_breakthroughs(panel_findings)

    # Persist to Neo4j
    await persist_to_knowledge_graph(synthesis, session_id)

    return synthesis
```

### 4. Chainlit Action Integration

Expose Genesis Engine to users via action buttons:

```python
# mindrian_chat.py

@cl.action_callback("run_genesis_analysis")
async def on_run_genesis_analysis(action: cl.Action):
    """Run Genesis Expert Breakdown pipeline."""
    history = cl.user_session.get("history", [])
    session_id = str(cl.user_session.get("id", "default"))

    # Extract challenge from conversation
    challenge = " ".join([m.get("content", "") for m in history[-6:]])[-3000:]

    if len(challenge.strip()) < 50:
        await cl.Message(content="Please describe a complex, multi-domain challenge first.").send()
        return

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("## 🧠 Genesis Expert Breakdown\n\n")
    await msg.stream_token("*Running multi-domain expert analysis...*\n\n")

    # Stream thinking tokens while processing
    await msg.stream_token("*decomposing context...* *identifying domains...* ")

    try:
        result = await run_genesis_pipeline(
            challenge=challenge,
            session_id=session_id
        )

        # Format output
        report = format_genesis_report(result)
        await msg.stream_token("\n\n---\n\n")
        await msg.stream_token(report)
        await msg.update()

    except Exception as e:
        await msg.stream_token(f"\n\n❌ Error: {str(e)[:200]}")
        await msg.update()
```

## Collaboration Matrix Visualization

The `orchestrate_research.py` generates interaction types between personas:

| Interaction Type | Value | When |
|-----------------|-------|------|
| SYNTHESIS | 0.9 | Integration expert ↔ anyone |
| BREAKTHROUGH | 0.85 | Authority ↔ Authority |
| HIERARCHICAL | 0.8 | Parent ↔ Subdomain |
| VALIDATION | 0.7 | Methodology expert ↔ anyone |
| COLLABORATION | 0.6 | Same domain experts |
| EXPLORATORY | 0.5 | Cross-domain, low overlap |

This could be visualized with a Mermaid diagram or D3 force graph.

## Scoring Model

Breakthroughs are scored with weighted multi-criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Breakthrough Potential | 35% | How novel and transformative |
| Feasibility | 25% | Can it actually be built |
| Cross-Domain Impact | 25% | How many domains benefit |
| Time to Value | 15% | How quickly delivers results |

Validation gates:
- **Gate 2**: Must have supporting evidence
- **Gate 3**: Must span 2+ domains
- **Gate 4**: Must have concrete implementation steps

## Implementation Roadmap

### Phase 1: Core Integration (2-3 weeks)
- [ ] Copy Genesis scripts to `intelligence/pipelines/genesis/`
- [ ] Create LangGraph state graph
- [ ] Integrate with existing Tavily search
- [ ] Add Chainlit action callback

### Phase 2: Swarm Expert Panel (2-3 weeks)
- [ ] Install OpenAI Swarm or implement with Gemini
- [ ] Convert persona generation to Swarm agents
- [ ] Implement 4-round panel protocol
- [ ] Add streaming output for panel discussion

### Phase 3: Visualization & UX (1-2 weeks)
- [ ] Create collaboration matrix visualization
- [ ] Add breakthrough scoring card component
- [ ] Implement domain map checkpoint UI
- [ ] Add progress tracking for 6 stages

### Phase 4: Knowledge Persistence (1 week)
- [ ] Store personas in Neo4j (DomainExpert nodes)
- [ ] Store breakthroughs (BreakthroughInnovation nodes)
- [ ] Create domain bridges (DomainBridge relationships)
- [ ] Enable retrieval of prior analyses

## Key Differentiators

| Feature | Current Mindrian | With Genesis |
|---------|-----------------|--------------|
| Problem analysis | Single LLM perspective | Multi-expert panel |
| Domain coverage | General PWS | 24 specialized domains |
| Research | Tavily search | Persona-directed queries |
| Validation | Basic checks | 3-gate validation |
| Output | Conversation | Scored breakthroughs + roadmaps |

## Files to Create

```
intelligence/pipelines/genesis/
├── __init__.py
├── decompose.py       # Adapted from decompose_context.py
├── domains.py         # Adapted from identify_domains.py
├── personas.py        # Adapted from generate_personas.py
├── orchestrate.py     # Adapted from orchestrate_research.py
├── panel.py           # Swarm expert panel
├── synthesize.py      # Adapted from synthesize_breakthroughs.py
└── pipeline.py        # LangGraph workflow
```

## Swarm vs Gemini Agents

Note: OpenAI Swarm is experimental. Alternative with Gemini:

```python
# Use Gemini function calling for agent simulation
async def run_gemini_expert_panel(personas, findings):
    for persona in personas:
        system_prompt = generate_persona_prompt(persona)
        response = await gemini_call(
            system=system_prompt,
            messages=[{"role": "user", "content": f"Present findings: {findings}"}],
            tools=[search_tool, propose_tool, challenge_tool]
        )
```

## References

- Source: `/home/jsagi/Mindrian/agents-midrian/`
- LangGraph docs: https://langchain-ai.github.io/langgraph/
- Swarm: https://github.com/openai/swarm
- Existing BONO pipeline: `intelligence/pipelines/bono_innovation.py`
