"""
Domain Discovery Pipeline - LangGraph Implementation
=====================================================
5-phase CV/research domain discovery for analyze_cv action.

Pipeline:
1. CV Parsing (extract experience, skills, interests)
2. Domain Generation (Gemini generates candidate domains)
3. Domain Scoring (IKA scoring per domain) - can run PARALLEL
4. Graph Enrichment (Neo4j checks for related frameworks)
5. Synthesis (ranked domains with next steps)

Benefits over current implementation:
- Steps 3 (domain scoring) runs in PARALLEL for all domains
- State persists via checkpointing (can resume)
- Clear separation of concerns
- Easy to add human-in-the-loop for domain selection

Usage:
    from intelligence.pipelines import run_domain_discovery

    result = await run_domain_discovery(
        cv_text="User's background...",
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


class DomainDiscoveryState(TypedDict):
    """State for Domain Discovery pipeline."""
    # Input
    cv_text: str
    interests: str  # User-stated interests

    # Step outputs
    parsed_cv: dict                              # Extracted skills, experience, education
    candidate_domains: Annotated[list, add]      # Generated domain statements
    domain_scores: Annotated[dict, merge_dicts]  # {domain: {interest, knowledge, access, total}}
    graph_enrichment: Annotated[dict, merge_dicts]  # {domain: related_frameworks}
    ranked_domains: list                          # Final ranked list
    synthesis: str                                # Final recommendation

    # Metadata
    started_at: str
    completed_steps: Annotated[list, add]
    errors: Annotated[list, add]


# =============================================================================
# NODE IMPLEMENTATIONS
# =============================================================================

async def parse_cv(state: DomainDiscoveryState) -> dict:
    """
    STEP 1: Parse CV/background to extract structured information.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        prompt = f"""Parse this professional background and extract structured information:

BACKGROUND:
{state["cv_text"]}

{f"STATED INTERESTS: {state['interests']}" if state.get('interests') else ""}

Extract:
1. **Skills**: Technical and soft skills mentioned
2. **Experience Domains**: Industries/fields they've worked in
3. **Education**: Degrees, certifications, training
4. **Key Accomplishments**: Notable achievements
5. **Apparent Interests**: What they seem passionate about
6. **Unique Combinations**: Unusual skill/experience combinations

Format as a JSON object with these keys: skills, experience_domains, education, accomplishments, interests, unique_combinations

Return ONLY valid JSON."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        # Parse JSON from response
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        parsed = json.loads(text.strip())

        return {
            "parsed_cv": parsed,
            "completed_steps": ["parse_cv"]
        }

    except Exception as e:
        return {
            "parsed_cv": {"error": str(e)},
            "errors": [f"CV parsing error: {str(e)}"],
            "completed_steps": ["parse_cv_failed"]
        }


async def generate_domains(state: DomainDiscoveryState) -> dict:
    """
    STEP 2: Generate candidate problem domains based on parsed CV.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        parsed = state.get("parsed_cv", {})

        prompt = f"""Based on this professional profile, generate 5 potential problem domains
for PWS (Problems Worth Solving) research:

PROFILE:
- Skills: {json.dumps(parsed.get('skills', []))}
- Experience: {json.dumps(parsed.get('experience_domains', []))}
- Interests: {json.dumps(parsed.get('interests', []))}
- Unique Combinations: {json.dumps(parsed.get('unique_combinations', []))}

For each domain, create a "Domain Statement" in this format:
"[Stakeholder] in [Context] need [Outcome] because [Reason]"

Generate 5 diverse domains that leverage their unique background.
Consider:
1. A domain in their primary expertise area
2. A domain combining two of their skills/experiences
3. An adjacent domain they could enter
4. A passion-driven domain from their interests
5. A contrarian/unexpected domain

Format as a JSON array of objects with keys: domain_statement, type, rationale

Return ONLY valid JSON array."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        # Parse JSON from response
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        domains = json.loads(text.strip())

        return {
            "candidate_domains": domains,
            "completed_steps": ["generate_domains"]
        }

    except Exception as e:
        return {
            "candidate_domains": [],
            "errors": [f"Domain generation error: {str(e)}"],
            "completed_steps": ["generate_domains_failed"]
        }


async def score_domains(state: DomainDiscoveryState) -> dict:
    """
    STEP 3: Score each domain using IKA (Interest, Knowledge, Access) framework.
    Scores all domains in PARALLEL for efficiency.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        domains = state.get("candidate_domains", [])
        parsed = state.get("parsed_cv", {})

        if not domains:
            return {
                "domain_scores": {},
                "completed_steps": ["score_domains_skipped"]
            }

        async def score_single_domain(domain: dict) -> tuple:
            """Score a single domain."""
            domain_statement = domain.get("domain_statement", "")

            prompt = f"""Score this problem domain for the user using the IKA framework:

DOMAIN: {domain_statement}

USER PROFILE:
- Skills: {json.dumps(parsed.get('skills', [])[:5])}
- Experience: {json.dumps(parsed.get('experience_domains', [])[:5])}
- Interests: {json.dumps(parsed.get('interests', [])[:5])}

Score each dimension 1-5:

**Interest (1-5)**: How aligned is this with their stated/apparent interests?
**Knowledge (1-5)**: How much relevant expertise do they have?
**Access (1-5)**: How easily can they reach stakeholders in this domain?

Format as JSON: {{"interest": N, "knowledge": N, "access": N, "total": N, "rationale": "brief explanation"}}

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

            scores = json.loads(text.strip())
            scores["total"] = scores.get("interest", 0) + scores.get("knowledge", 0) + scores.get("access", 0)

            return (domain_statement, scores)

        # Score all domains in parallel
        tasks = [score_single_domain(d) for d in domains]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        domain_scores = {}
        for result in results:
            if isinstance(result, tuple):
                domain_statement, scores = result
                domain_scores[domain_statement] = scores
            elif isinstance(result, Exception):
                # Log error but continue
                pass

        return {
            "domain_scores": domain_scores,
            "completed_steps": ["score_domains"]
        }

    except Exception as e:
        return {
            "domain_scores": {},
            "errors": [f"Domain scoring error: {str(e)}"],
            "completed_steps": ["score_domains_failed"]
        }


async def enrich_with_graph(state: DomainDiscoveryState) -> dict:
    """
    STEP 4: Enrich domains with related frameworks from Neo4j knowledge graph.
    """
    try:
        from tools.graphrag_lite import get_related_frameworks

        domains = state.get("candidate_domains", [])
        enrichment = {}

        for domain in domains:
            domain_statement = domain.get("domain_statement", "")

            # Query Neo4j for related frameworks
            frameworks = get_related_frameworks(domain_statement, limit=3)

            enrichment[domain_statement] = {
                "frameworks": [fw.get("name", "") for fw in frameworks],
                "hints": [fw.get("hint", "") for fw in frameworks if fw.get("hint")]
            }

        return {
            "graph_enrichment": enrichment,
            "completed_steps": ["graph_enrichment"]
        }

    except Exception as e:
        return {
            "graph_enrichment": {},
            "errors": [f"Graph enrichment error: {str(e)}"],
            "completed_steps": ["graph_enrichment_failed"]
        }


async def synthesize_domains(state: DomainDiscoveryState) -> dict:
    """
    STEP 5: Synthesize findings into ranked recommendations.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        domains = state.get("candidate_domains", [])
        scores = state.get("domain_scores", {})
        enrichment = state.get("graph_enrichment", {})

        # Rank domains by total score
        ranked = []
        for domain in domains:
            statement = domain.get("domain_statement", "")
            score_data = scores.get(statement, {})
            graph_data = enrichment.get(statement, {})

            ranked.append({
                "domain_statement": statement,
                "type": domain.get("type", ""),
                "rationale": domain.get("rationale", ""),
                "scores": score_data,
                "total_score": score_data.get("total", 0),
                "related_frameworks": graph_data.get("frameworks", []),
                "hints": graph_data.get("hints", [])
            })

        # Sort by total score descending
        ranked.sort(key=lambda x: x.get("total_score", 0), reverse=True)

        # Generate synthesis
        prompt = f"""Synthesize these domain discovery findings into a recommendation:

RANKED DOMAINS (by IKA score):
{json.dumps(ranked, indent=2)}

Provide:
1. **Top Recommendation** - Which domain to pursue first and why
2. **Strong Alternatives** - Other viable options
3. **Key Considerations** - What to keep in mind
4. **Immediate Next Steps** - 3 concrete actions

Be specific and actionable. Reference the PWS frameworks suggested."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )

        return {
            "ranked_domains": ranked,
            "synthesis": response.text,
            "completed_steps": ["synthesize"]
        }

    except Exception as e:
        return {
            "ranked_domains": [],
            "synthesis": f"Synthesis error: {str(e)}",
            "errors": [f"Synthesis error: {str(e)}"],
            "completed_steps": ["synthesize_failed"]
        }


# =============================================================================
# PIPELINE CONSTRUCTION
# =============================================================================

def create_domain_discovery_pipeline(checkpointer=None):
    """
    Create the Domain Discovery LangGraph pipeline.

    Args:
        checkpointer: Optional checkpointer for state persistence.

    Returns:
        Compiled LangGraph application.
    """
    graph = StateGraph(DomainDiscoveryState)

    # Add nodes
    graph.add_node("parse_cv", parse_cv)
    graph.add_node("generate_domains", generate_domains)
    graph.add_node("score_domains", score_domains)
    graph.add_node("enrich_graph", enrich_with_graph)
    graph.add_node("synthesize", synthesize_domains)

    # Sequential flow (scoring happens internally in parallel)
    graph.add_edge(START, "parse_cv")
    graph.add_edge("parse_cv", "generate_domains")
    graph.add_edge("generate_domains", "score_domains")
    graph.add_edge("score_domains", "enrich_graph")
    graph.add_edge("enrich_graph", "synthesize")
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
        print(f"[DOMAIN] Postgres checkpointer unavailable: {e}")
        return None


# =============================================================================
# PUBLIC API
# =============================================================================

async def run_domain_discovery(
    cv_text: str,
    session_id: str,
    interests: str = "",
    use_postgres: bool = True
) -> Dict[str, Any]:
    """
    Run the Domain Discovery pipeline.

    Args:
        cv_text: User's CV/background text.
        session_id: Session ID for checkpointing.
        interests: Optional user-stated interests.
        use_postgres: Whether to use Postgres checkpointing.

    Returns:
        Dict with ranked domains and synthesis.

    Example:
        result = await run_domain_discovery(
            cv_text="10 years software engineering...",
            session_id="user_123",
            interests="climate tech, education"
        )
        print(result["synthesis"])
    """
    # Get checkpointer
    checkpointer = None
    if use_postgres:
        checkpointer = await get_postgres_checkpointer()

    if checkpointer is None:
        checkpointer = MemorySaver()
        print("[DOMAIN] Using in-memory checkpointer")

    # Create pipeline
    pipeline = create_domain_discovery_pipeline(checkpointer)

    # Initial state
    initial_state = {
        "cv_text": cv_text,
        "interests": interests,
        "parsed_cv": {},
        "candidate_domains": [],
        "domain_scores": {},
        "graph_enrichment": {},
        "ranked_domains": [],
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


def format_domain_discovery_result(result: Dict[str, Any]) -> str:
    """
    Format Domain Discovery result as markdown for display.

    Args:
        result: Pipeline result dict.

    Returns:
        Formatted markdown string.
    """
    output = ["# Domain Discovery Report\n"]

    # Synthesis (main output)
    if result.get("synthesis"):
        output.append(result["synthesis"])
        output.append("\n---\n")

    # Ranked domains table
    if result.get("ranked_domains"):
        output.append("## Domain Rankings\n")
        output.append("| Domain | I | K | A | Total | Frameworks |")
        output.append("|--------|---|---|---|-------|------------|")

        for domain in result["ranked_domains"][:5]:
            scores = domain.get("scores", {})
            frameworks = ", ".join(domain.get("related_frameworks", [])[:2])
            statement = domain.get("domain_statement", "")[:50] + "..."
            output.append(
                f"| {statement} | "
                f"{scores.get('interest', '-')} | "
                f"{scores.get('knowledge', '-')} | "
                f"{scores.get('access', '-')} | "
                f"{scores.get('total', '-')} | "
                f"{frameworks} |"
            )
        output.append("")

    # Errors
    if result.get("errors"):
        output.append(f"\n**Errors:** {'; '.join(result['errors'])}\n")

    return "\n".join(output)
