"""
Genesis Expert Breakdown Pipeline
=================================
LangGraph-powered workflow combining all stages with BONO integration.

Stages:
1. Context Decomposition
2. Domain Identification
3. Persona Generation (with Six Hats)
4. Research Orchestration
5. Expert Panel (multi-agent)
6. Breakthrough Synthesis
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END

from .decompose import decompose_context
from .domains import identify_domains
from .personas import generate_personas
from .orchestrate import orchestrate_research
from .panel import run_expert_panel
from .synthesize import synthesize_breakthroughs


# =============================================================================
# STATE DEFINITION
# =============================================================================

class GenesisState(TypedDict):
    """State for Genesis pipeline."""
    challenge: str
    session_id: str
    # Stage outputs
    decomposition: Optional[Dict]
    domains: Optional[Dict]
    personas: Optional[Dict]
    research_plan: Optional[Dict]
    research_findings: Optional[Dict]
    panel_findings: Optional[Dict]
    synthesis: Optional[Dict]
    # Control
    current_stage: int
    error: Optional[str]
    # Progress
    progress_messages: List[str]


# =============================================================================
# STAGE NODES
# =============================================================================

async def decompose_node(state: GenesisState) -> Dict:
    """Stage 1: Decompose challenge context."""
    try:
        decomposition = decompose_context(state["challenge"])
        return {
            "decomposition": decomposition,
            "current_stage": 1,
            "progress_messages": state.get("progress_messages", []) + [
                f"Stage 1: Decomposed into {len(decomposition['segments'])} segments, "
                f"complexity: {decomposition['complexity']['level']}"
            ],
        }
    except Exception as e:
        return {"error": f"Decomposition failed: {str(e)}"}


async def domains_node(state: GenesisState) -> Dict:
    """Stage 2: Identify domains."""
    try:
        domains = identify_domains(state["decomposition"])
        primary_names = [d["domain"] for d in domains["domains"]["primary"]]
        return {
            "domains": domains,
            "current_stage": 2,
            "progress_messages": state.get("progress_messages", []) + [
                f"Stage 2: Identified {domains['metadata']['total_domains']} domains: "
                f"{', '.join(primary_names[:3])}"
            ],
        }
    except Exception as e:
        return {"error": f"Domain identification failed: {str(e)}"}


async def personas_node(state: GenesisState) -> Dict:
    """Stage 3: Generate personas with BONO hats."""
    try:
        personas = generate_personas(
            state["domains"],
            state["decomposition"]["complexity"],
            use_bono_hats=True
        )
        hat_count = sum(1 for p in personas["personas"] if p.get("thinking_hat"))
        return {
            "personas": personas,
            "current_stage": 3,
            "progress_messages": state.get("progress_messages", []) + [
                f"Stage 3: Generated {len(personas['personas'])} expert personas, "
                f"{hat_count} with Six Hats"
            ],
        }
    except Exception as e:
        return {"error": f"Persona generation failed: {str(e)}"}


async def orchestrate_node(state: GenesisState) -> Dict:
    """Stage 4: Orchestrate research."""
    try:
        research_plan = orchestrate_research(
            state["personas"]["personas"],
            state["challenge"]
        )
        return {
            "research_plan": research_plan,
            "current_stage": 4,
            "progress_messages": state.get("progress_messages", []) + [
                f"Stage 4: Research plan ready, "
                f"{len(research_plan['collaborationMatrix']['primaryInteractions'])} interactions"
            ],
        }
    except Exception as e:
        return {"error": f"Research orchestration failed: {str(e)}"}


async def research_node(state: GenesisState) -> Dict:
    """Execute research queries (Tavily integration)."""
    try:
        # Import Tavily if available
        research_findings = {}

        try:
            from tools.tavily_search import tavily_search

            for persona in state["personas"]["personas"][:5]:  # Limit to 5 personas
                queries = persona.get("query_strategies_with_hat",
                                     persona.get("queryStrategies", []))[:2]
                findings = []
                for query in queries:
                    try:
                        results = await tavily_search(query)
                        findings.extend(results.get("results", [])[:3])
                    except Exception:
                        pass
                research_findings[persona["name"]] = findings

        except ImportError:
            # Mock findings if Tavily not available
            for persona in state["personas"]["personas"]:
                research_findings[persona["name"]] = [{
                    "title": "Simulated finding",
                    "content": f"Research insights for {persona['primaryExpertise']}",
                }]

        return {
            "research_findings": research_findings,
            "progress_messages": state.get("progress_messages", []) + [
                f"Research: Gathered findings for {len(research_findings)} personas"
            ],
        }
    except Exception as e:
        return {"error": f"Research failed: {str(e)}"}


async def panel_node(state: GenesisState) -> Dict:
    """Stage 5: Run expert panel discussion."""
    try:
        panel_findings = await run_expert_panel(
            state["personas"]["personas"],
            state["research_findings"],
            model_name="gemini-2.0-flash"
        )
        return {
            "panel_findings": panel_findings,
            "current_stage": 5,
            "progress_messages": state.get("progress_messages", []) + [
                f"Stage 5: Expert panel complete, "
                f"{len(panel_findings.get('breakthroughs', []))} breakthroughs proposed"
            ],
        }
    except Exception as e:
        return {"error": f"Expert panel failed: {str(e)}"}


async def synthesize_node(state: GenesisState) -> Dict:
    """Stage 6: Synthesize breakthroughs."""
    try:
        synthesis = synthesize_breakthroughs(
            state["panel_findings"],
            min_score=5.0,
            max_breakthroughs=5
        )
        return {
            "synthesis": synthesis,
            "current_stage": 6,
            "progress_messages": state.get("progress_messages", []) + [
                f"Stage 6: Synthesis complete, "
                f"{synthesis['summary']['top_selected']} top opportunities"
            ],
        }
    except Exception as e:
        return {"error": f"Synthesis failed: {str(e)}"}


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def should_continue(state: GenesisState) -> str:
    """Check if we should continue or end due to error."""
    if state.get("error"):
        return "error"
    return "continue"


def create_genesis_graph():
    """Create the LangGraph workflow."""
    graph = StateGraph(GenesisState)

    # Add nodes
    graph.add_node("decompose", decompose_node)
    graph.add_node("domains", domains_node)
    graph.add_node("personas", personas_node)
    graph.add_node("orchestrate", orchestrate_node)
    graph.add_node("research", research_node)
    graph.add_node("panel", panel_node)
    graph.add_node("synthesize", synthesize_node)

    # Set entry point
    graph.set_entry_point("decompose")

    # Add edges (linear flow)
    graph.add_edge("decompose", "domains")
    graph.add_edge("domains", "personas")
    graph.add_edge("personas", "orchestrate")
    graph.add_edge("orchestrate", "research")
    graph.add_edge("research", "panel")
    graph.add_edge("panel", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


# =============================================================================
# MAIN PIPELINE FUNCTION
# =============================================================================

async def run_genesis_pipeline(
    challenge: str,
    session_id: str,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Run the complete Genesis Expert Breakdown pipeline.

    Args:
        challenge: Multi-domain challenge description (50+ chars)
        session_id: Session identifier for tracking
        progress_callback: Optional async callback for progress updates

    Returns:
        Complete synthesis with breakthroughs and roadmaps

    Example:
        result = await run_genesis_pipeline(
            challenge="How can AI and blockchain transform supply chain transparency?",
            session_id="user_123"
        )
    """
    if len(challenge.strip()) < 50:
        return {
            "error": "Challenge must be at least 50 characters",
            "synthesis": None,
        }

    # Initialize state
    initial_state: GenesisState = {
        "challenge": challenge,
        "session_id": session_id,
        "decomposition": None,
        "domains": None,
        "personas": None,
        "research_plan": None,
        "research_findings": None,
        "panel_findings": None,
        "synthesis": None,
        "current_stage": 0,
        "error": None,
        "progress_messages": [],
    }

    # Create and run graph
    graph = create_genesis_graph()

    # Run with progress updates
    if progress_callback:
        await progress_callback("Starting Genesis Expert Breakdown pipeline...")

    try:
        # Execute the graph
        final_state = await graph.ainvoke(initial_state)

        if progress_callback:
            for msg in final_state.get("progress_messages", []):
                await progress_callback(msg)

        if final_state.get("error"):
            return {
                "error": final_state["error"],
                "partial_results": {
                    "decomposition": final_state.get("decomposition"),
                    "domains": final_state.get("domains"),
                    "personas": final_state.get("personas"),
                },
            }

        return {
            "synthesis": final_state["synthesis"],
            "personas": final_state["personas"],
            "domains": final_state["domains"],
            "research_plan": final_state["research_plan"],
            "panel_findings": final_state["panel_findings"],
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "session_id": session_id,
                "stages_completed": final_state["current_stage"],
                "progress": final_state["progress_messages"],
            },
        }

    except Exception as e:
        return {
            "error": f"Pipeline failed: {str(e)}",
            "synthesis": None,
        }


# =============================================================================
# FORMATTING
# =============================================================================

def format_genesis_report(result: Dict) -> str:
    """Format Genesis pipeline result as markdown report."""
    if result.get("error"):
        return f"## Genesis Analysis Error\n\n{result['error']}"

    synthesis = result.get("synthesis", {})
    if not synthesis:
        return "## Genesis Analysis\n\nNo results generated."

    lines = ["## Genesis Expert Breakdown Report\n"]

    # Summary
    summary = synthesis.get("summary", {})
    lines.append(f"**{summary.get('total_candidates', 0)}** breakthroughs identified, "
                 f"**{summary.get('top_selected', 0)}** selected\n")
    lines.append(f"Best score: **{summary.get('max_composite_score', 0):.1f}**/10\n")

    # Personas used
    personas = result.get("personas", {}).get("personas", [])
    if personas:
        lines.append("\n### Expert Panel\n")
        for p in personas[:5]:
            hat = p.get("thinking_hat", {}).get("name", "No hat")
            lines.append(f"- **{p['name']}** ({p['expertiseDepth']}) - {hat}")

    # Top opportunities
    top = synthesis.get("top_opportunities", [])
    if top:
        lines.append("\n### Top Breakthrough Opportunities\n")
        for i, opp in enumerate(top[:3], 1):
            lines.append(f"\n#### {i}. {opp['name']}")
            lines.append(f"**Score:** {opp.get('composite_score', 0):.1f}/10")
            lines.append(f"**Domains:** {', '.join(opp.get('domains_involved', []))}")
            lines.append(f"**Proposed by:** {opp.get('proposed_by', 'Panel')}")
            if opp.get("description"):
                lines.append(f"\n{opp['description'][:300]}...")

    # Implementation roadmaps
    roadmaps = synthesis.get("implementation_roadmaps", [])
    if roadmaps:
        lines.append("\n### Implementation Roadmaps\n")
        for rm in roadmaps[:2]:
            lines.append(f"\n**{rm['breakthrough']}** - {rm['total_timeline']}")
            for phase in rm.get("phases", []):
                lines.append(f"- Phase {phase['phase']}: {phase['name']} ({phase['duration']})")

    # Cross-domain insights
    connections = synthesis.get("cross_domain_connections", [])
    if connections:
        lines.append("\n### Cross-Domain Connections\n")
        for conn in connections[:2]:
            lines.append(f"*{conn.get('identified_by', 'Integration Architect')}:*")
            lines.append(f"{conn.get('connections', '')[:300]}...")

    return "\n".join(lines)
