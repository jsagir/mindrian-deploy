"""
Reverse Salient Discovery Pipeline - LangGraph Implementation
=============================================================
10-stage Cross Domain RS (Reverse Salient) discovery workflow.

Pipeline:
1. Problem Framing (understand the target problem)
2. System Decomposition (break into components)
3. Salient Identification (find the bottleneck/constraint)
4. Domain Abstraction (abstract the salient to find analogous domains)
5. Cross-Domain Search (search for solutions in other fields) - PARALLEL
6. Solution Harvesting (extract transferable solutions)
7. Adaptation Analysis (how to adapt solutions to original domain)
8. Validation Planning (plan tests for adapted solutions)
9. Risk Assessment (identify risks and failure modes)
10. Synthesis (final recommendations with implementation roadmap)

The Reverse Salient methodology finds breakthrough innovations by:
- Identifying the constraint holding back a system (the "salient")
- Abstracting it to find analogous problems in other domains
- Importing solutions that worked elsewhere

Usage:
    from intelligence.pipelines import run_reverse_salient

    result = await run_reverse_salient(
        problem="Electric vehicle charging takes too long",
        session_id="user_session_123"
    )
"""

import os
import json
import asyncio
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from operator import add
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Try to use Postgres checkpointer if available
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


# =============================================================================
# STATE DEFINITION
# =============================================================================

def merge_dicts(left: dict, right: dict) -> dict:
    """Reducer: merge dictionaries."""
    return {**left, **right}


class ReverseSalientState(TypedDict):
    """State for Reverse Salient Discovery pipeline."""
    # Input
    problem: str
    context: str  # Additional context

    # Step outputs
    problem_frame: dict                          # Structured problem understanding
    system_components: Annotated[list, add]      # Decomposed system elements
    identified_salient: dict                     # The constraint/bottleneck
    abstracted_domains: Annotated[list, add]     # Analogous domains to search
    cross_domain_results: Annotated[dict, merge_dicts]  # {domain: solutions}
    harvested_solutions: Annotated[list, add]    # Extracted transferable solutions
    adaptations: Annotated[list, add]            # How to adapt each solution
    validation_plan: dict                         # Tests and experiments
    risk_assessment: dict                         # Risks and mitigations
    synthesis: str                                # Final recommendations

    # Metadata
    started_at: str
    completed_steps: Annotated[list, add]
    errors: Annotated[list, add]


# =============================================================================
# NODE IMPLEMENTATIONS
# =============================================================================

async def frame_problem(state: ReverseSalientState) -> dict:
    """
    STEP 1: Frame the problem in structured terms.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        prompt = f"""Frame this problem for Reverse Salient analysis:

PROBLEM: {state["problem"]}
{f"CONTEXT: {state['context']}" if state.get('context') else ""}

Analyze and structure as:

1. **System Description**: What system is this problem embedded in?
2. **Current State**: What's the status quo?
3. **Desired State**: What would success look like?
4. **Gap**: What's preventing progress?
5. **Stakeholders**: Who is affected?
6. **Prior Attempts**: What solutions have been tried?

Format as JSON with keys: system, current_state, desired_state, gap, stakeholders, prior_attempts

Return ONLY valid JSON."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        frame = json.loads(text.strip())

        return {
            "problem_frame": frame,
            "completed_steps": ["frame_problem"]
        }

    except Exception as e:
        return {
            "problem_frame": {"error": str(e)},
            "errors": [f"Problem framing error: {str(e)}"],
            "completed_steps": ["frame_problem_failed"]
        }


async def decompose_system(state: ReverseSalientState) -> dict:
    """
    STEP 2: Decompose the system into components.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        frame = state.get("problem_frame", {})

        prompt = f"""Decompose this system into its key components:

SYSTEM: {frame.get('system', state['problem'])}
GAP: {frame.get('gap', 'Unknown')}

Identify:
1. **Input Components**: What goes into the system?
2. **Process Components**: What transformations occur?
3. **Output Components**: What results?
4. **Support Components**: What enables the system?
5. **Constraint Components**: What limits performance?

For each component, note:
- Name
- Function
- Current performance
- Potential for improvement (High/Medium/Low)

Format as JSON array of objects: {{"name": "", "type": "", "function": "", "performance": "", "improvement_potential": ""}}

Return ONLY valid JSON array."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        components = json.loads(text.strip())

        return {
            "system_components": components,
            "completed_steps": ["decompose_system"]
        }

    except Exception as e:
        return {
            "system_components": [],
            "errors": [f"System decomposition error: {str(e)}"],
            "completed_steps": ["decompose_system_failed"]
        }


async def identify_salient(state: ReverseSalientState) -> dict:
    """
    STEP 3: Identify the Reverse Salient (the constraint holding back progress).
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        components = state.get("system_components", [])
        frame = state.get("problem_frame", {})

        prompt = f"""Identify the REVERSE SALIENT in this system:

A Reverse Salient is the component or subsystem that is holding back the entire system's progress.
It's the "weakest link" or bottleneck that, if improved, would unlock advancement.

PROBLEM: {state["problem"]}
GAP: {frame.get('gap', 'Unknown')}

SYSTEM COMPONENTS:
{json.dumps(components, indent=2)}

Identify:
1. **The Reverse Salient**: Which component is the primary constraint?
2. **Why It's Limiting**: What makes this the bottleneck?
3. **Impact If Solved**: What would improve if this was fixed?
4. **Why It's Hard**: What has prevented solving it?
5. **Abstract Function**: What is the abstract function this component performs?
   (e.g., "energy storage" not "battery", "rapid information transfer" not "5G")

Format as JSON: {{"salient_component": "", "why_limiting": "", "impact_if_solved": "", "why_hard": "", "abstract_function": ""}}

Return ONLY valid JSON."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        salient = json.loads(text.strip())

        return {
            "identified_salient": salient,
            "completed_steps": ["identify_salient"]
        }

    except Exception as e:
        return {
            "identified_salient": {"error": str(e)},
            "errors": [f"Salient identification error: {str(e)}"],
            "completed_steps": ["identify_salient_failed"]
        }


async def abstract_to_domains(state: ReverseSalientState) -> dict:
    """
    STEP 4: Abstract the salient to find analogous domains.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        salient = state.get("identified_salient", {})

        prompt = f"""Find analogous domains where the same abstract problem has been solved:

REVERSE SALIENT: {salient.get('salient_component', '')}
ABSTRACT FUNCTION: {salient.get('abstract_function', '')}
WHY IT'S HARD: {salient.get('why_hard', '')}

Think creatively across:
- Biology and nature (biomimicry)
- Other industries (cross-industry)
- Historical solutions (temporal transfer)
- Adjacent technologies (technology transfer)
- Different scales (nano, micro, macro)

For each domain, identify:
1. Domain name
2. Analogous problem they solved
3. How it maps to our problem
4. Search query to find solutions

Generate 5 diverse analogous domains.

Format as JSON array: [{{"domain": "", "analogous_problem": "", "mapping": "", "search_query": ""}}]

Return ONLY valid JSON array."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        domains = json.loads(text.strip())

        return {
            "abstracted_domains": domains,
            "completed_steps": ["abstract_domains"]
        }

    except Exception as e:
        return {
            "abstracted_domains": [],
            "errors": [f"Domain abstraction error: {str(e)}"],
            "completed_steps": ["abstract_domains_failed"]
        }


async def search_cross_domain(state: ReverseSalientState) -> dict:
    """
    STEP 5: Search for solutions in analogous domains.
    Runs searches in PARALLEL for efficiency.
    """
    try:
        from tools.tavily_search import search_web

        domains = state.get("abstracted_domains", [])

        async def search_domain(domain: dict) -> tuple:
            """Search a single domain."""
            query = domain.get("search_query", domain.get("domain", ""))
            results = search_web(
                query=f"{query} solution innovation breakthrough",
                search_depth="advanced",
                max_results=5
            )
            return (domain.get("domain", ""), results.get("results", []))

        # Search all domains (note: Tavily is sync, so we run sequentially)
        cross_domain_results = {}
        for domain in domains:
            domain_name, results = await search_domain(domain)
            cross_domain_results[domain_name] = results

        return {
            "cross_domain_results": cross_domain_results,
            "completed_steps": ["cross_domain_search"]
        }

    except Exception as e:
        return {
            "cross_domain_results": {},
            "errors": [f"Cross-domain search error: {str(e)}"],
            "completed_steps": ["cross_domain_search_failed"]
        }


async def harvest_solutions(state: ReverseSalientState) -> dict:
    """
    STEP 6: Extract transferable solutions from cross-domain results.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        results = state.get("cross_domain_results", {})
        salient = state.get("identified_salient", {})

        # Compile search results
        results_text = ""
        for domain, domain_results in results.items():
            results_text += f"\n## {domain}\n"
            for r in domain_results[:3]:
                results_text += f"- {r.get('title', '')}: {r.get('content', '')[:200]}...\n"

        prompt = f"""Extract transferable solutions from these cross-domain findings:

OUR REVERSE SALIENT: {salient.get('salient_component', '')}
ABSTRACT FUNCTION NEEDED: {salient.get('abstract_function', '')}

CROSS-DOMAIN FINDINGS:
{results_text}

For each promising solution, extract:
1. **Solution Name**: What is it called in its original domain?
2. **Original Domain**: Where does it come from?
3. **Core Mechanism**: How does it work (abstractly)?
4. **Transfer Potential**: How might it apply to our problem?
5. **Novelty Score**: How novel would this transfer be? (1-5)

Identify 3-5 most promising transferable solutions.

Format as JSON array: [{{"name": "", "domain": "", "mechanism": "", "transfer_potential": "", "novelty": N}}]

Return ONLY valid JSON array."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        solutions = json.loads(text.strip())

        return {
            "harvested_solutions": solutions,
            "completed_steps": ["harvest_solutions"]
        }

    except Exception as e:
        return {
            "harvested_solutions": [],
            "errors": [f"Solution harvesting error: {str(e)}"],
            "completed_steps": ["harvest_solutions_failed"]
        }


async def analyze_adaptations(state: ReverseSalientState) -> dict:
    """
    STEP 7: Analyze how to adapt each solution to the original domain.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        solutions = state.get("harvested_solutions", [])
        salient = state.get("identified_salient", {})
        frame = state.get("problem_frame", {})

        prompt = f"""Analyze how to adapt these solutions to our problem:

ORIGINAL PROBLEM: {state["problem"]}
REVERSE SALIENT: {salient.get('salient_component', '')}
SYSTEM CONTEXT: {frame.get('system', '')}

HARVESTED SOLUTIONS:
{json.dumps(solutions, indent=2)}

For each solution, provide an adaptation analysis:
1. **Adaptation Strategy**: How would we translate this to our domain?
2. **Key Modifications**: What changes are needed?
3. **Technical Gaps**: What capabilities are missing?
4. **Resource Requirements**: What would implementation need?
5. **Timeline Estimate**: How long might adaptation take?
6. **Confidence Level**: How confident are we this could work? (1-5)

Format as JSON array matching the solutions order.

Return ONLY valid JSON array."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        adaptations = json.loads(text.strip())

        return {
            "adaptations": adaptations,
            "completed_steps": ["analyze_adaptations"]
        }

    except Exception as e:
        return {
            "adaptations": [],
            "errors": [f"Adaptation analysis error: {str(e)}"],
            "completed_steps": ["analyze_adaptations_failed"]
        }


async def plan_validation(state: ReverseSalientState) -> dict:
    """
    STEP 8: Plan validation tests for adapted solutions.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        solutions = state.get("harvested_solutions", [])
        adaptations = state.get("adaptations", [])

        prompt = f"""Create a validation plan for these adapted solutions:

SOLUTIONS AND ADAPTATIONS:
{json.dumps(list(zip(solutions, adaptations)), indent=2)}

For the top 3 most promising solutions, design:

1. **Hypothesis**: What are we testing?
2. **Minimum Viable Test**: Smallest experiment to validate
3. **Success Criteria**: What would prove it works?
4. **Failure Criteria**: What would prove it doesn't work?
5. **Resources Needed**: What's required to run the test?
6. **Timeline**: How long would the test take?

Format as JSON with keys: tests (array of test objects), priority_order (array of solution names)

Return ONLY valid JSON."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        validation = json.loads(text.strip())

        return {
            "validation_plan": validation,
            "completed_steps": ["plan_validation"]
        }

    except Exception as e:
        return {
            "validation_plan": {"error": str(e)},
            "errors": [f"Validation planning error: {str(e)}"],
            "completed_steps": ["plan_validation_failed"]
        }


async def assess_risks(state: ReverseSalientState) -> dict:
    """
    STEP 9: Assess risks and failure modes.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        solutions = state.get("harvested_solutions", [])
        adaptations = state.get("adaptations", [])

        prompt = f"""Assess risks for these cross-domain transfer solutions:

SOLUTIONS: {json.dumps(solutions, indent=2)}
ADAPTATIONS: {json.dumps(adaptations, indent=2)}

Analyze:

1. **Transfer Risks**: What could go wrong in the adaptation?
2. **Technical Risks**: What technical challenges might arise?
3. **Market Risks**: What if the market doesn't accept it?
4. **Competitive Risks**: How might competitors respond?
5. **Resource Risks**: What if we underestimate requirements?

For each risk:
- Likelihood (1-5)
- Impact (1-5)
- Mitigation strategy

Also identify:
- **Assumptions Being Made**: What are we assuming is true?
- **Unknown Unknowns**: What don't we know that we don't know?

Format as JSON with keys: risks (array), assumptions (array), unknowns (array)

Return ONLY valid JSON."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        risk_assessment = json.loads(text.strip())

        return {
            "risk_assessment": risk_assessment,
            "completed_steps": ["assess_risks"]
        }

    except Exception as e:
        return {
            "risk_assessment": {"error": str(e)},
            "errors": [f"Risk assessment error: {str(e)}"],
            "completed_steps": ["assess_risks_failed"]
        }


async def synthesize_findings(state: ReverseSalientState) -> dict:
    """
    STEP 10: Synthesize all findings into final recommendations.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        prompt = f"""Synthesize this Reverse Salient Discovery into actionable recommendations:

## Original Problem
{state["problem"]}

## Identified Reverse Salient
{json.dumps(state.get("identified_salient", {}), indent=2)}

## Cross-Domain Solutions Found
{json.dumps(state.get("harvested_solutions", []), indent=2)}

## Adaptation Strategies
{json.dumps(state.get("adaptations", []), indent=2)}

## Validation Plan
{json.dumps(state.get("validation_plan", {}), indent=2)}

## Risk Assessment
{json.dumps(state.get("risk_assessment", {}), indent=2)}

---

Provide a comprehensive synthesis:

1. **Executive Summary** (2-3 sentences on the breakthrough opportunity)

2. **The Reverse Salient Insight** - What we discovered about the true constraint

3. **Top Recommended Solution** - Which cross-domain solution to pursue first and why

4. **Implementation Roadmap** - 5-step plan with milestones

5. **Critical Success Factors** - What must go right

6. **Watch-Outs** - Key risks to monitor

7. **Immediate Next Actions** - 3 things to do this week

Be specific, actionable, and grounded in the analysis."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        return {
            "synthesis": response.text,
            "completed_steps": ["synthesize"]
        }

    except Exception as e:
        return {
            "synthesis": f"Synthesis error: {str(e)}",
            "errors": [f"Synthesis error: {str(e)}"],
            "completed_steps": ["synthesize_failed"]
        }


# =============================================================================
# PIPELINE CONSTRUCTION
# =============================================================================

def create_reverse_salient_pipeline(checkpointer=None):
    """
    Create the Reverse Salient Discovery LangGraph pipeline.

    Args:
        checkpointer: Optional checkpointer for state persistence.

    Returns:
        Compiled LangGraph application.
    """
    graph = StateGraph(ReverseSalientState)

    # Add nodes
    graph.add_node("frame_problem", frame_problem)
    graph.add_node("decompose_system", decompose_system)
    graph.add_node("identify_salient", identify_salient)
    graph.add_node("abstract_domains", abstract_to_domains)
    graph.add_node("search_cross_domain", search_cross_domain)
    graph.add_node("harvest_solutions", harvest_solutions)
    graph.add_node("analyze_adaptations", analyze_adaptations)
    graph.add_node("plan_validation", plan_validation)
    graph.add_node("assess_risks", assess_risks)
    graph.add_node("synthesize", synthesize_findings)

    # Sequential flow
    graph.add_edge(START, "frame_problem")
    graph.add_edge("frame_problem", "decompose_system")
    graph.add_edge("decompose_system", "identify_salient")
    graph.add_edge("identify_salient", "abstract_domains")
    graph.add_edge("abstract_domains", "search_cross_domain")
    graph.add_edge("search_cross_domain", "harvest_solutions")
    graph.add_edge("harvest_solutions", "analyze_adaptations")
    graph.add_edge("analyze_adaptations", "plan_validation")
    graph.add_edge("plan_validation", "assess_risks")
    graph.add_edge("assess_risks", "synthesize")
    graph.add_edge("synthesize", END)

    # Use provided checkpointer or default to memory
    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


async def get_postgres_checkpointer():
    """Get Postgres checkpointer if available."""
    if not POSTGRES_AVAILABLE:
        return None

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None

    try:
        checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
        await checkpointer.setup()
        return checkpointer
    except Exception as e:
        print(f"[REVERSE_SALIENT] Postgres checkpointer unavailable: {e}")
        return None


# =============================================================================
# PUBLIC API
# =============================================================================

async def run_reverse_salient(
    problem: str,
    session_id: str,
    context: str = "",
    use_postgres: bool = True
) -> Dict[str, Any]:
    """
    Run the Reverse Salient Discovery pipeline.

    Args:
        problem: The problem to analyze for reverse salients.
        session_id: Session ID for checkpointing.
        context: Additional context.
        use_postgres: Whether to use Postgres checkpointing.

    Returns:
        Dict with synthesis and all intermediate results.

    Example:
        result = await run_reverse_salient(
            problem="Electric vehicle charging takes too long",
            session_id="user_123",
            context="Target market is urban commuters"
        )
        print(result["synthesis"])
    """
    # Get checkpointer
    checkpointer = None
    if use_postgres:
        checkpointer = await get_postgres_checkpointer()

    if checkpointer is None:
        checkpointer = MemorySaver()
        print("[REVERSE_SALIENT] Using in-memory checkpointer")

    # Create pipeline
    pipeline = create_reverse_salient_pipeline(checkpointer)

    # Initial state
    initial_state = {
        "problem": problem,
        "context": context,
        "problem_frame": {},
        "system_components": [],
        "identified_salient": {},
        "abstracted_domains": [],
        "cross_domain_results": {},
        "harvested_solutions": [],
        "adaptations": [],
        "validation_plan": {},
        "risk_assessment": {},
        "synthesis": "",
        "started_at": datetime.now().isoformat(),
        "completed_steps": [],
        "errors": [],
    }

    # Config for checkpointing
    config = {"configurable": {"thread_id": session_id}}

    # Run pipeline
    try:
        result = await pipeline.ainvoke(initial_state, config)
        return result
    except Exception as e:
        return {
            **initial_state,
            "errors": [f"Pipeline error: {str(e)}"],
            "synthesis": f"Pipeline failed: {str(e)}"
        }


def format_reverse_salient_result(result: Dict[str, Any]) -> str:
    """
    Format Reverse Salient result as markdown for display.

    Args:
        result: Pipeline result dict.

    Returns:
        Formatted markdown string.
    """
    output = ["# Reverse Salient Discovery Report\n"]

    # Synthesis (main output)
    if result.get("synthesis"):
        output.append(result["synthesis"])
        output.append("\n---\n")

    # Key findings summary
    salient = result.get("identified_salient", {})
    if salient and not salient.get("error"):
        output.append("## The Reverse Salient\n")
        output.append(f"**Component:** {salient.get('salient_component', 'Unknown')}\n")
        output.append(f"**Abstract Function:** {salient.get('abstract_function', 'Unknown')}\n")
        output.append(f"**Why Limiting:** {salient.get('why_limiting', 'Unknown')}\n")

    # Solutions found
    solutions = result.get("harvested_solutions", [])
    if solutions:
        output.append("\n## Cross-Domain Solutions\n")
        for sol in solutions[:5]:
            output.append(f"- **{sol.get('name', 'Unknown')}** from {sol.get('domain', 'Unknown')}: {sol.get('transfer_potential', '')[:100]}...")

    # Errors
    if result.get("errors"):
        output.append(f"\n**Errors:** {'; '.join(result['errors'])}\n")

    return "\n".join(output)
