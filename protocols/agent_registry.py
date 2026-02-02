"""
Agent Registry - Mindrian Intelligence Layer
=============================================

Defines agent roles, capabilities, and routing rules for the full Mindrian stack.
Every agent (new or existing) gets registered here to access Mindrian intelligence.

AGENT ROLES:
- Orchestrator: Manages flow, routes to others, maintains conversation
- Workshop: Guides through phases, can call services
- Sub-Agent: Called by other agents for specific expertise
- Service: Does specific task, returns result, no dialogue

CAPABILITIES (all agents can access):
- GraphRAG enrichment
- Research orchestration
- LangExtract signals
- Graph Router scoring
- Phase tracking
- Context persistence

Usage:
    from protocols.agent_registry import (
        get_agent_config,
        get_agent_for_context,
        can_agent_call,
        get_agent_capabilities,
        register_agent,
    )
"""

from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field


# ============================================================================
# AGENT ROLE DEFINITIONS
# ============================================================================

class AgentRole(Enum):
    """Roles an agent can play in the system."""
    ORCHESTRATOR = "orchestrator"  # Manages flow, routes to others
    WORKSHOP = "workshop"          # Guides through phases
    SUB_AGENT = "sub_agent"        # Called by other agents
    SERVICE = "service"            # Returns data, no conversation


class AgentCapability(Enum):
    """Capabilities agents can access."""
    GRAPHRAG = "graphrag"              # Graph-enhanced retrieval
    RESEARCH = "research"              # Web/source research
    LANGEXTRACT = "langextract"        # Content signal extraction
    GRAPH_ROUTER = "graph_router"      # Bot scoring/routing
    PHASE_TRACKER = "phase_tracker"    # Semantic phase detection
    CONTEXT_STORE = "context_store"    # Cross-session context
    FILE_SEARCH = "file_search"        # PWS knowledge base
    NEO4J = "neo4j"                    # Direct graph queries
    GRADING = "grading"                # PWS quality scoring
    OPPORTUNITY_BANK = "opportunity_bank"  # Insight storage


# ============================================================================
# AGENT CONFIGURATION DATACLASS
# ============================================================================

@dataclass
class AgentConfig:
    """Configuration for a registered agent."""

    # Identity
    id: str
    name: str
    description: str
    icon: str = "🤖"

    # Roles (an agent can have multiple)
    roles: List[AgentRole] = field(default_factory=list)

    # Entry points this agent serves
    entry_points: List[str] = field(default_factory=list)  # ["brainstorming", "document_review", "build_venture"]

    # Venture stages (for build_venture entry point)
    venture_stages: List[str] = field(default_factory=list)  # ["pre_opportunity", "opportunity_identified", etc.]

    # Orchestration rules
    can_orchestrate: bool = False
    can_be_sub_agent: bool = False
    service_mode: bool = False  # If True, returns data, doesn't hold conversation

    # Call graph
    can_call: List[str] = field(default_factory=list)      # Agent IDs this agent can invoke
    called_by: List[str] = field(default_factory=list)     # Agent IDs that can invoke this ("*" = any)
    handoff_to: List[str] = field(default_factory=list)    # Agents to hand conversation to

    # Capabilities
    capabilities: List[AgentCapability] = field(default_factory=list)

    # Framework associations (for graph routing)
    frameworks: List[str] = field(default_factory=list)    # Framework names this agent specializes in
    keywords: List[str] = field(default_factory=list)      # Keywords that trigger this agent

    # Behavior
    has_phases: bool = False
    phase_count: int = 0
    default_mode: str = "sandbox"  # "sandbox" or "workshop"

    # Returns (for service agents)
    returns: Optional[str] = None  # Type of data returned (e.g., "GradingScorecard", "ResearchResult")


# ============================================================================
# AGENT REGISTRY
# ============================================================================

# Global registry - populated at module load
_AGENT_REGISTRY: Dict[str, AgentConfig] = {}


def register_agent(config: AgentConfig) -> None:
    """Register an agent in the global registry."""
    _AGENT_REGISTRY[config.id] = config


def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """Get configuration for an agent."""
    return _AGENT_REGISTRY.get(agent_id)


def get_all_agents() -> Dict[str, AgentConfig]:
    """Get all registered agents."""
    return _AGENT_REGISTRY.copy()


def get_agents_by_role(role: AgentRole) -> List[AgentConfig]:
    """Get all agents with a specific role."""
    return [a for a in _AGENT_REGISTRY.values() if role in a.roles]


def get_agents_for_entry_point(entry_point: str) -> List[AgentConfig]:
    """Get agents that serve a specific entry point."""
    return [a for a in _AGENT_REGISTRY.values()
            if entry_point in a.entry_points or "*" in a.entry_points]


def get_agents_for_venture_stage(stage: str) -> List[AgentConfig]:
    """Get agents appropriate for a venture stage."""
    return [
        a for a in _AGENT_REGISTRY.values()
        if stage in a.venture_stages or "*" in a.venture_stages
    ]


# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def get_agent_for_context(
    entry_point: str,
    stage: Optional[str] = None,
    message: Optional[str] = None,
    current_agent: Optional[str] = None
) -> str:
    """
    Determine which agent should handle this context.

    Priority:
    1. Venture stage → specific agent
    2. Entry point → default orchestrator
    3. Message content → graph router suggestion
    4. Current agent (if valid)
    5. Fallback to lawrence
    """

    # Stage-specific routing for build_venture
    if entry_point == "build_venture" and stage:
        stage_agents = get_agents_for_venture_stage(stage)
        if stage_agents:
            # Return first orchestrator or workshop agent for this stage
            for agent in stage_agents:
                if AgentRole.ORCHESTRATOR in agent.roles or AgentRole.WORKSHOP in agent.roles:
                    return agent.id

    # Entry point defaults
    entry_defaults = {
        "brainstorming": "lawrence",
        "document_review": "pws_grading",
        "build_venture": "jtbd",  # Default if no stage
    }

    # If message provided, check for better agent via keywords
    if message:
        suggested = get_suggested_agent(message, entry_point)
        if suggested:
            return suggested

    return entry_defaults.get(entry_point, "lawrence")


def get_suggested_agent(message: str, entry_point: str) -> Optional[str]:
    """
    Suggest an agent based on message content and keywords.
    Uses keyword matching (fast) before graph router (slower).
    """
    message_lower = message.lower()

    # Get agents for this entry point
    candidates = get_agents_for_entry_point(entry_point)

    # Score by keyword matches
    scores: Dict[str, int] = {}
    for agent in candidates:
        score = 0
        for keyword in agent.keywords:
            if keyword.lower() in message_lower:
                score += 1
        if score > 0:
            scores[agent.id] = score

    if scores:
        return max(scores, key=scores.get)

    return None


def can_agent_call(caller_id: str, callee_id: str) -> bool:
    """Check if caller agent can invoke callee agent."""
    caller = get_agent_config(caller_id)
    callee = get_agent_config(callee_id)

    if not caller or not callee:
        return False

    # Check if callee allows being called by anyone
    if "*" in callee.called_by:
        return True

    # Check if caller can call this specific agent
    if callee_id in caller.can_call:
        return True

    # Check if callee lists caller as allowed
    if caller_id in callee.called_by:
        return True

    return False


def can_agent_handoff(from_id: str, to_id: str) -> bool:
    """Check if from_agent can hand conversation to to_agent."""
    from_agent = get_agent_config(from_id)

    if not from_agent:
        return False

    return to_id in from_agent.handoff_to or "*" in from_agent.handoff_to


# ============================================================================
# CAPABILITY FUNCTIONS
# ============================================================================

def get_agent_capabilities(agent_id: str) -> List[AgentCapability]:
    """Get capabilities available to an agent."""
    agent = get_agent_config(agent_id)
    if not agent:
        return []
    return agent.capabilities


def has_capability(agent_id: str, capability: AgentCapability) -> bool:
    """Check if agent has a specific capability."""
    return capability in get_agent_capabilities(agent_id)


def get_agents_with_capability(capability: AgentCapability) -> List[AgentConfig]:
    """Get all agents that have a specific capability."""
    return [
        config for config in _AGENT_REGISTRY.values()
        if capability in config.capabilities
    ]


def get_default_capabilities() -> List[AgentCapability]:
    """
    Get capabilities that ALL agents should have.
    This ensures every new agent gets full Mindrian intelligence.
    """
    return [
        AgentCapability.GRAPHRAG,
        AgentCapability.LANGEXTRACT,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ]


# ============================================================================
# AGENT DEFINITIONS - EXISTING BOTS
# ============================================================================

# Define all existing agents with their roles and capabilities

register_agent(AgentConfig(
    id="lawrence",
    name="Lawrence",
    description="PWS thinking partner - focused, concise guidance",
    icon="🧠",
    roles=[AgentRole.ORCHESTRATOR, AgentRole.WORKSHOP],
    entry_points=["brainstorming", "build_venture"],
    venture_stages=["*"],  # Available at all stages as orchestrator
    can_orchestrate=True,
    can_be_sub_agent=False,
    can_call=["tta", "scenario", "research", "graphrag", "redteam", "jtbd"],
    handoff_to=["tta", "jtbd", "redteam", "ackoff", "scurve"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.GRAPH_ROUTER,
        AgentCapability.PHASE_TRACKER,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
        AgentCapability.OPPORTUNITY_BANK,
    ],
    frameworks=["PWS", "Minto Pyramid", "SCQA"],
    keywords=["problem", "think", "explore", "help me", "where do i start"],
    has_phases=False,
    default_mode="sandbox",
))

register_agent(AgentConfig(
    id="larry_playground",
    name="Larry Playground",
    description="Full-featured PWS lab with all tools and research",
    icon="🔬",
    roles=[AgentRole.ORCHESTRATOR, AgentRole.WORKSHOP],
    entry_points=["brainstorming", "document_review", "build_venture"],
    can_orchestrate=True,
    can_be_sub_agent=False,
    can_call=["*"],  # Can call any agent
    handoff_to=["*"],  # Can hand off to any agent
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.GRAPH_ROUTER,
        AgentCapability.PHASE_TRACKER,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
        AgentCapability.NEO4J,
        AgentCapability.GRADING,
        AgentCapability.OPPORTUNITY_BANK,
    ],
    frameworks=["*"],  # All frameworks
    keywords=["playground", "full", "everything", "all tools"],
    has_phases=False,
    default_mode="sandbox",
))

register_agent(AgentConfig(
    id="tta",
    name="Trending to the Absurd",
    description="Extrapolate trends to discover opportunities",
    icon="📈",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT],
    entry_points=["brainstorming"],
    venture_stages=["pre_opportunity"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    called_by=["lawrence", "larry_playground"],
    can_call=["research"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ],
    frameworks=["Trending to the Absurd", "TTA"],
    keywords=["trend", "future", "what if", "extrapolate", "absurd", "emerging"],
    has_phases=True,
    phase_count=5,
    default_mode="workshop",
))

register_agent(AgentConfig(
    id="jtbd",
    name="Jobs to Be Done",
    description="Understand what job customers are hiring for",
    icon="🎯",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT],
    entry_points=["build_venture"],
    venture_stages=["opportunity_identified"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    called_by=["lawrence", "larry_playground", "stage_router"],
    can_call=["research", "graphrag"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.PHASE_TRACKER,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ],
    frameworks=["Jobs to Be Done", "JTBD", "Customer Jobs"],
    keywords=["job", "customer", "hire", "struggling", "progress", "outcome"],
    has_phases=True,
    phase_count=6,
    default_mode="workshop",
))

register_agent(AgentConfig(
    id="ackoff",
    name="Ackoff's Pyramid",
    description="Transform data into wisdom with DIKW hierarchy",
    icon="🔺",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT],
    entry_points=["build_venture"],
    venture_stages=["opportunity_identified", "well_defined_problem"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    called_by=["lawrence", "larry_playground", "jtbd"],
    can_call=["research", "graphrag"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.PHASE_TRACKER,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
        AgentCapability.NEO4J,
    ],
    frameworks=["Ackoff's Pyramid", "DIKW", "Data to Wisdom"],
    keywords=["data", "information", "knowledge", "wisdom", "pyramid", "dikw"],
    has_phases=True,
    phase_count=7,
    default_mode="workshop",
))

register_agent(AgentConfig(
    id="scurve",
    name="S-Curve Analysis",
    description="Understand technology lifecycles and timing",
    icon="📊",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT],
    entry_points=["build_venture"],
    venture_stages=["well_defined_problem"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    called_by=["lawrence", "larry_playground"],
    can_call=["research"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.PHASE_TRACKER,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ],
    frameworks=["S-Curve", "Technology Lifecycle", "Dominant Design"],
    keywords=["timing", "curve", "adoption", "lifecycle", "dominant design", "technology"],
    has_phases=True,
    phase_count=5,
    default_mode="workshop",
))

register_agent(AgentConfig(
    id="redteam",
    name="Red Team",
    description="Challenge assumptions and stress-test ideas",
    icon="🎯",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT, AgentRole.SERVICE],
    entry_points=["document_review", "brainstorming", "build_venture"],
    venture_stages=["*"],  # Relevant at all stages
    can_orchestrate=False,
    can_be_sub_agent=True,
    service_mode=True,  # Can be called as service for quick critique
    called_by=["*"],  # Any agent can call for critique
    can_call=["research"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ],
    frameworks=["Red Team", "Devil's Advocate", "Assumption Testing", "Six Thinking Hats"],
    keywords=["challenge", "critique", "assumption", "poke holes", "stress test", "devil"],
    has_phases=True,
    phase_count=4,
    default_mode="workshop",
    returns="CritiqueResult",
))

register_agent(AgentConfig(
    id="pws_grading",
    name="PWS Grading",
    description="Grade problem statements against PWS criteria",
    icon="📝",
    roles=[AgentRole.SERVICE],
    entry_points=["document_review"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    service_mode=True,
    called_by=["*"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.LANGEXTRACT,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
        AgentCapability.GRADING,
    ],
    frameworks=["PWS Grading Rubric"],
    keywords=["grade", "score", "rubric", "evaluate", "rate"],
    has_phases=False,
    returns="GradingScorecard",
))

register_agent(AgentConfig(
    id="research",
    name="Research",
    description="Multi-source web research and synthesis",
    icon="🔍",
    roles=[AgentRole.SERVICE],
    entry_points=["*"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    service_mode=True,
    called_by=["*"],
    capabilities=[
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
    ],
    frameworks=[],
    keywords=["research", "search", "find", "sources", "evidence"],
    has_phases=False,
    returns="ResearchResult",
))

register_agent(AgentConfig(
    id="scenario",
    name="Scenario Analysis",
    description="Explore alternative futures and possibilities",
    icon="🔮",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT],
    entry_points=["brainstorming", "build_venture"],
    venture_stages=["pre_opportunity", "opportunity_identified", "ready_to_build"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    called_by=["lawrence", "larry_playground"],
    can_call=["research"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.RESEARCH,
        AgentCapability.LANGEXTRACT,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ],
    frameworks=["Scenario Analysis", "Future Scenarios"],
    keywords=["scenario", "what if", "future", "possibilities", "alternatives"],
    has_phases=True,
    phase_count=4,
    default_mode="workshop",
))

register_agent(AgentConfig(
    id="beautiful_question",
    name="Beautiful Question",
    description="Reframe problems through powerful questions",
    icon="❓",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT],
    entry_points=["brainstorming"],
    venture_stages=["pre_opportunity"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    called_by=["lawrence", "larry_playground"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.LANGEXTRACT,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ],
    frameworks=["Beautiful Question", "Why-What If-How"],
    keywords=["question", "reframe", "why", "what if", "how might we"],
    has_phases=True,
    phase_count=3,
    default_mode="workshop",
))

register_agent(AgentConfig(
    id="knowns",
    name="Known/Unknown Matrix",
    description="Map what you know and don't know",
    icon="🧩",
    roles=[AgentRole.WORKSHOP, AgentRole.SUB_AGENT],
    entry_points=["brainstorming", "build_venture"],
    venture_stages=["opportunity_identified"],
    can_orchestrate=False,
    can_be_sub_agent=True,
    called_by=["lawrence", "larry_playground"],
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.LANGEXTRACT,
        AgentCapability.CONTEXT_STORE,
        AgentCapability.FILE_SEARCH,
    ],
    frameworks=["Known/Unknown Matrix", "Johari Window"],
    keywords=["know", "unknown", "blind spot", "don't know", "uncertainty"],
    has_phases=True,
    phase_count=4,
    default_mode="workshop",
))

# ============================================================================
# SERVICE AGENTS (No conversation, return data only)
# ============================================================================

register_agent(AgentConfig(
    id="graphrag",
    name="GraphRAG Service",
    description="Neo4j + vector hybrid retrieval service",
    icon="🕸️",
    roles=[AgentRole.SERVICE],
    entry_points=[],  # Services don't have entry points
    venture_stages=[],
    can_orchestrate=False,
    can_be_sub_agent=False,
    service_mode=True,  # Returns data, no conversation
    called_by=["*"],  # Can be called by anyone
    capabilities=[
        AgentCapability.GRAPHRAG,
        AgentCapability.NEO4J,
    ],
    frameworks=[],
    keywords=[],
    has_phases=False,
))

register_agent(AgentConfig(
    id="stage_router",
    name="Stage Router Service",
    description="Routes users to appropriate venture stage",
    icon="🔀",
    roles=[AgentRole.SERVICE],
    entry_points=[],
    venture_stages=[],
    can_orchestrate=False,
    can_be_sub_agent=False,
    service_mode=True,
    called_by=["lawrence", "larry_playground"],
    capabilities=[
        AgentCapability.GRAPH_ROUTER,
        AgentCapability.LANGEXTRACT,
    ],
    frameworks=[],
    keywords=[],
    has_phases=False,
))


# ============================================================================
# HELPER: CREATE NEW AGENT WITH FULL CAPABILITIES
# ============================================================================

def create_agent_with_defaults(
    id: str,
    name: str,
    description: str,
    icon: str = "🤖",
    roles: List[AgentRole] = None,
    entry_points: List[str] = None,
    frameworks: List[str] = None,
    keywords: List[str] = None,
    has_phases: bool = False,
    phase_count: int = 0,
    **kwargs
) -> AgentConfig:
    """
    Create a new agent with full Mindrian intelligence capabilities.

    This ensures every new agent gets:
    - GraphRAG enrichment
    - LangExtract signals
    - Context persistence
    - File search access

    Plus any additional capabilities specified.
    """

    # Start with default capabilities
    capabilities = list(get_default_capabilities())

    # Add research if agent is orchestrator or workshop
    if roles and (AgentRole.ORCHESTRATOR in roles or AgentRole.WORKSHOP in roles):
        capabilities.append(AgentCapability.RESEARCH)
        capabilities.append(AgentCapability.PHASE_TRACKER)

    # Add any extra capabilities from kwargs
    extra_caps = kwargs.pop('capabilities', [])
    capabilities.extend(extra_caps)

    # Deduplicate
    capabilities = list(set(capabilities))

    config = AgentConfig(
        id=id,
        name=name,
        description=description,
        icon=icon,
        roles=roles or [AgentRole.WORKSHOP],
        entry_points=entry_points or ["brainstorming"],
        frameworks=frameworks or [],
        keywords=keywords or [],
        has_phases=has_phases,
        phase_count=phase_count,
        capabilities=capabilities,
        can_be_sub_agent=True,  # Default to callable
        called_by=["lawrence", "larry_playground"],  # Default callers
        **kwargs
    )

    # Auto-register
    register_agent(config)

    return config


# ============================================================================
# QUERY HELPERS
# ============================================================================

def get_orchestrator_for_entry_point(entry_point: str) -> Optional[str]:
    """Get the default orchestrator for an entry point."""
    agents = get_agents_for_entry_point(entry_point)
    for agent in agents:
        if AgentRole.ORCHESTRATOR in agent.roles:
            return agent.id
    return "lawrence"  # Ultimate fallback


def get_service_agents() -> List[AgentConfig]:
    """Get all service agents (can be called for tasks)."""
    return [a for a in _AGENT_REGISTRY.values() if a.service_mode]


def get_workshop_agents() -> List[AgentConfig]:
    """Get all workshop agents (have phases)."""
    return [a for a in _AGENT_REGISTRY.values() if a.has_phases]


def get_callable_agents(caller_id: str) -> List[AgentConfig]:
    """Get all agents that a given agent can call."""
    caller = get_agent_config(caller_id)
    if not caller:
        return []

    if "*" in caller.can_call:
        return list(_AGENT_REGISTRY.values())

    return [get_agent_config(aid) for aid in caller.can_call if get_agent_config(aid)]


def agent_to_dict(agent: AgentConfig) -> Dict[str, Any]:
    """Convert agent config to dictionary for JSON serialization."""
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "icon": agent.icon,
        "roles": [r.value for r in agent.roles],
        "entry_points": agent.entry_points,
        "venture_stages": agent.venture_stages,
        "can_orchestrate": agent.can_orchestrate,
        "can_be_sub_agent": agent.can_be_sub_agent,
        "service_mode": agent.service_mode,
        "frameworks": agent.frameworks,
        "keywords": agent.keywords,
        "has_phases": agent.has_phases,
        "phase_count": agent.phase_count,
        "capabilities": [c.value for c in agent.capabilities],
    }


# ============================================================================
# RUNTIME CHECKS
# ============================================================================

def validate_registry():
    """Validate that all agent cross-references are valid."""
    errors = []

    for agent_id, agent in _AGENT_REGISTRY.items():
        # Check can_call references exist
        for called_id in agent.can_call:
            if called_id != "*" and called_id not in _AGENT_REGISTRY:
                errors.append(f"{agent_id}.can_call references unknown agent: {called_id}")

        # Check handoff_to references exist
        for handoff_id in agent.handoff_to:
            if handoff_id != "*" and handoff_id not in _AGENT_REGISTRY:
                errors.append(f"{agent_id}.handoff_to references unknown agent: {handoff_id}")

        # Check called_by references exist
        for caller_id in agent.called_by:
            if caller_id != "*" and caller_id not in _AGENT_REGISTRY:
                errors.append(f"{agent_id}.called_by references unknown agent: {caller_id}")

    return errors


# Run validation at module load (development check)
_validation_errors = validate_registry()
if _validation_errors:
    import warnings
    for err in _validation_errors:
        warnings.warn(f"Agent Registry: {err}")


# Public alias for the registry (for external access)
AGENT_REGISTRY = _AGENT_REGISTRY
