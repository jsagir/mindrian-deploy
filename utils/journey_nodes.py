"""
PWS Journey Nodes
=================

LangGraph-style nodes for the PWS Journey state machine.
Each node uses the hybrid LLM Router for optimal model selection.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.llm_router import (
    LLMRouter,
    TrackedTavilySearch,
    HybridResearchPipeline,
    cost_tracker,
)
from utils.journey_state import (
    PWSJourneyState,
    JourneyStateManager,
    cached_llm_call,
)


# ============================================================================
# NODE 1: INTAKE
# ============================================================================

async def intake_node(state: PWSJourneyState, problem: str = None, context: str = None, **kwargs) -> Dict:
    """
    First node: Capture and prepare problem statement.

    Uses Gemini Flash for quick keyword extraction.
    """
    problem = problem or state.get("problem_statement", "")
    context = context or state.get("user_context", "")

    # Quick keyword extraction (Gemini Flash)
    if problem:
        keywords_prompt = f"""Extract 5-10 key concepts from this problem statement.
Return as comma-separated list.

Problem: {problem}"""

        keywords = await LLMRouter.bulk_generate(
            keywords_prompt,
            task_type="keyword_extraction",
            max_tokens=100,
        )

        context = f"{context}\nExtracted keywords: {keywords}"

    return {
        "problem_statement": problem,
        "user_context": context,
        "current_phase": "classify",
        "phase_iteration": state.get("phase_iteration", 0) + 1,
    }


# ============================================================================
# NODE 2: CLASSIFY (Claude Opus)
# ============================================================================

async def classify_node(state: PWSJourneyState, fallback_mode: bool = False, **kwargs) -> Dict:
    """
    Classify problem type and Cynefin domain.

    Uses Claude Opus for nuanced classification.
    Falls back to Gemini if in fallback mode.
    """
    problem = state["problem_statement"]
    context = state.get("user_context", "")

    # Get Neo4j context for classification hints
    neo4j_hints = await _get_neo4j_classification_hints(problem)

    if fallback_mode:
        # Use Gemini Flash as fallback
        classification = await _classify_with_gemini(problem, context, neo4j_hints)
    else:
        # Use Claude Opus for best quality
        classification = await LLMRouter.classify_problem(
            problem,
            context={"user_context": context, "neo4j_hints": neo4j_hints}
        )

    return {
        "problem_type": classification.get("problem_type", "ill_defined"),
        "cynefin_domain": classification.get("cynefin_domain", "complicated"),
        "wickedness_score": classification.get("wickedness_score", 0.5),
        "classification_confidence": classification.get("confidence", 0.5),
        "classification_reasoning": classification.get("problem_type_reasoning", "") + "\n" + classification.get("cynefin_reasoning", ""),
        "classification_evidence": classification.get("evidence", []),
        "neo4j_context": {"classification_hints": neo4j_hints},
        "current_phase": "enrich",
    }


async def _get_neo4j_classification_hints(problem: str) -> Dict:
    """Query Neo4j for classification hints."""
    try:
        # This would use your MCP Neo4j tools
        # For now, return empty hints
        return {}
    except Exception as e:
        print(f"[NEO4J] Classification hints failed: {e}")
        return {}


async def _classify_with_gemini(problem: str, context: str, hints: Dict) -> Dict:
    """Fallback classification using Gemini Flash."""
    prompt = f"""Classify this problem:

Problem: {problem}
Context: {context}

Return JSON:
{{
    "problem_type": "undefined|ill_defined|well_defined|wicked",
    "cynefin_domain": "clear|complicated|complex|chaotic",
    "wickedness_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "evidence": ["reason1", "reason2"]
}}"""

    response = await LLMRouter.bulk_generate(prompt, task_type="fallback_classification")

    try:
        if "```json" in response:
            return json.loads(response.split("```json")[1].split("```")[0])
        return json.loads(response)
    except:
        return {
            "problem_type": "ill_defined",
            "cynefin_domain": "complicated",
            "wickedness_score": 0.5,
            "confidence": 0.3,
            "evidence": ["Fallback classification"],
        }


# ============================================================================
# NODE 3: ENRICH (Parallel Neo4j + FileSearch)
# ============================================================================

async def enrich_node(state: PWSJourneyState, **kwargs) -> Dict:
    """
    Enrich context with tools, frameworks, examples.

    Runs Neo4j and FileSearch queries in parallel.
    Uses Gemini Flash for any summarization.
    """
    problem = state["problem_statement"]
    problem_type = state["problem_type"]
    cynefin_domain = state["cynefin_domain"]

    # Run enrichment in parallel
    neo4j_task = _enrich_from_neo4j(problem, problem_type)
    filesearch_task = _enrich_from_filesearch(problem, problem_type, cynefin_domain)

    neo4j_results, filesearch_results = await asyncio.gather(
        neo4j_task,
        filesearch_task,
        return_exceptions=True,
    )

    # Handle errors gracefully
    if isinstance(neo4j_results, Exception):
        print(f"[ENRICH] Neo4j failed: {neo4j_results}")
        neo4j_results = {}

    if isinstance(filesearch_results, Exception):
        print(f"[ENRICH] FileSearch failed: {filesearch_results}")
        filesearch_results = {}

    # Extract tool and framework recommendations
    tools = neo4j_results.get("tools", [])
    frameworks = neo4j_results.get("frameworks", [])

    return {
        "neo4j_context": neo4j_results,
        "filesearch_context": filesearch_results,
        "recommended_tools": [t.get("name") if isinstance(t, dict) else t for t in tools],
        "recommended_frameworks": [f.get("name") if isinstance(f, dict) else f for f in frameworks],
        "current_phase": "generate_questions",
    }


async def _enrich_from_neo4j(problem: str, problem_type: str) -> Dict:
    """Query Neo4j for tools, frameworks, relationships."""
    # This would use your MCP Neo4j tools
    # Placeholder implementation
    return {
        "tools": [],
        "frameworks": [],
        "relationships": [],
    }


async def _enrich_from_filesearch(problem: str, problem_type: str, cynefin_domain: str) -> Dict:
    """Query FileSearch for methodology content and examples."""
    # This would use Gemini FileSearch
    # Placeholder implementation
    return {
        "methodology": "",
        "examples": [],
        "case_studies": [],
    }


# ============================================================================
# NODE 4: GENERATE QUESTIONS (Claude Opus)
# ============================================================================

async def generate_questions_node(state: PWSJourneyState, fallback_mode: bool = False, **kwargs) -> Dict:
    """
    Generate Beautiful Questions tailored to problem type.

    Uses Claude Opus for quality pedagogical questions.
    """
    problem = state["problem_statement"]
    problem_type = state["problem_type"]
    context = {
        "cynefin_domain": state["cynefin_domain"],
        "recommended_tools": state.get("recommended_tools", []),
        "neo4j_context": state.get("neo4j_context", {}),
    }

    if fallback_mode:
        # Use Gemini Flash as fallback
        questions = await _generate_questions_with_gemini(problem, problem_type, context)
    else:
        # Use Claude Opus for best quality
        questions = await LLMRouter.generate_beautiful_questions(
            problem,
            problem_type,
            context,
        )

    # Parse questions into standard format
    why_qs = questions.get("why_questions", [])
    what_if_qs = questions.get("what_if_questions", [])
    how_qs = questions.get("how_questions", [])

    # Normalize questions to standard format
    def normalize_questions(qs):
        if not qs:
            return []
        if isinstance(qs[0], dict):
            return qs
        return [{"question": q, "purpose": ""} for q in qs]

    return {
        "why_questions": normalize_questions(why_qs),
        "what_if_questions": normalize_questions(what_if_qs),
        "how_questions": normalize_questions(how_qs),
        "priority_question": questions.get("priority_question", ""),
        "current_phase": "guide",
    }


async def _generate_questions_with_gemini(problem: str, problem_type: str, context: Dict) -> Dict:
    """Fallback question generation using Gemini Flash."""
    prompt = f"""Generate Beautiful Questions for this {problem_type} problem:

Problem: {problem}
Context: {json.dumps(context, indent=2)}

Return JSON with why_questions, what_if_questions, how_questions arrays."""

    response = await LLMRouter.bulk_generate(prompt, task_type="fallback_questions", max_tokens=1000)

    try:
        if "```json" in response:
            return json.loads(response.split("```json")[1].split("```")[0])
        return json.loads(response)
    except:
        return {
            "why_questions": [{"question": "Why does this problem exist?", "purpose": "Root cause"}],
            "what_if_questions": [{"question": "What if we approached this differently?", "purpose": "Alternatives"}],
            "how_questions": [{"question": "How might we validate our assumptions?", "purpose": "Testing"}],
        }


# ============================================================================
# NODE 5: GUIDE
# ============================================================================

async def guide_node(state: PWSJourneyState, **kwargs) -> Dict:
    """
    Create guidance message and determine available actions.

    Uses Gemini Flash for message generation (bulk task).
    """
    problem_type = state["problem_type"]
    cynefin_domain = state["cynefin_domain"]
    tools = state.get("recommended_tools", [])[:5]
    why_qs = state.get("why_questions", [])
    what_if_qs = state.get("what_if_questions", [])
    how_qs = state.get("how_questions", [])

    # Determine probe strategy based on Cynefin
    probe_strategies = {
        "clear": "sense → categorize → respond (apply best practice)",
        "complicated": "sense → analyze → respond (expert analysis needed)",
        "complex": "probe → sense → respond (safe-to-fail experiments)",
        "chaotic": "act → sense → respond (stabilize first)",
    }
    strategy = probe_strategies.get(cynefin_domain, probe_strategies["complicated"])

    # Format questions for display
    def fmt_q(q):
        if isinstance(q, dict):
            return q.get("question", str(q))
        return str(q)

    # Build guidance message
    guidance = f"""## 🧭 PWS Journey Status

**Problem Type:** {(problem_type or "Unknown").replace('_', ' ').title()}
**Cynefin Domain:** {(cynefin_domain or "Unknown").title()}
**Wickedness:** {'High' if state.get('wickedness_score', 0) > 0.6 else 'Moderate' if state.get('wickedness_score', 0) > 0.3 else 'Low'}
**Confidence:** {state.get('classification_confidence', 0):.0%}

### Recommended Approach
{strategy}

### Your Beautiful Questions
**WHY:** {fmt_q(why_qs[0]) if why_qs else 'Not generated yet'}
**WHAT IF:** {fmt_q(what_if_qs[0]) if what_if_qs else 'Not generated yet'}
**HOW:** {fmt_q(how_qs[0]) if how_qs else 'Not generated yet'}

### Recommended Tools
{chr(10).join(['• ' + t for t in tools]) if tools else '• No specific tools recommended yet'}

### Journey Progress
- Checkpoints: {len(state.get('checkpoints', []))}
- Probes executed: {len(state.get('probes_executed', []))}
- Insights captured: {len(state.get('insights', []))}
"""

    # Determine available actions based on problem type and phase
    actions = ["🔍 Research", "💡 Ideas", "💾 Save Checkpoint"]

    if problem_type == "undefined":
        actions.extend(["🔮 Trending to Absurd", "🎭 Scenario Analysis"])
    elif problem_type == "ill_defined":
        actions.extend(["🎯 JTBD Analysis", "📈 S-Curve", "🔎 5 Whys"])
    elif problem_type == "well_defined":
        actions.extend(["✅ Validate Hypothesis", "🧪 Design Probe"])
    elif problem_type == "wicked":
        actions.extend(["👥 Stakeholder Map", "🔄 Systems Mapping"])

    actions.append("🔄 Reassess Classification")

    return {
        "guidance_message": guidance,
        "available_actions": actions,
        "current_phase": "guide",
    }


# ============================================================================
# NODE 6: PROBE
# ============================================================================

async def probe_node(state: PWSJourneyState, probe_type: str = "research", probe_query: str = None, **kwargs) -> Dict:
    """
    Execute a probe and collect evidence.

    Uses HybridResearchPipeline for research probes.
    """
    problem = state["problem_statement"]
    query = probe_query or problem

    # Record probe attempt
    probe_record = {
        "type": probe_type,
        "query": query[:200],
        "timestamp": datetime.now().isoformat(),
        "status": "executing",
    }

    reassessment_triggers = []

    if probe_type == "research":
        # Use hybrid research pipeline
        result = await HybridResearchPipeline.run(
            question=query,
            context=state.get("user_context", ""),
            depth="standard",
            problem_type=state["problem_type"],
        )

        probe_record["result"] = result.get("conclusion", "")[:500]
        probe_record["sources_count"] = len(result.get("sources", []))
        probe_record["status"] = "completed"

        # Check for reassessment triggers
        conclusion = result.get("conclusion", "").lower()

        if "stakeholder conflict" in conclusion and state["problem_type"] != "wicked":
            reassessment_triggers.append("Stakeholder conflicts detected - may be wicked problem")

        if "clear solution" in conclusion and state["cynefin_domain"] != "clear":
            reassessment_triggers.append("Clear solution found - domain may be Clear")

        if "emergent" in conclusion or "unpredictable" in conclusion:
            if state["cynefin_domain"] not in ["complex", "chaotic"]:
                reassessment_triggers.append("Emergent patterns detected - domain may be Complex")

    else:
        # Other probe types (placeholder)
        probe_record["result"] = f"Probe type '{probe_type}' not fully implemented"
        probe_record["status"] = "partial"

    return {
        "probes_executed": [probe_record],
        "reassessment_triggers": reassessment_triggers,
        "phase_iteration": state.get("phase_iteration", 0) + 1,
        "current_phase": "reassess" if reassessment_triggers else "guide",
    }


# ============================================================================
# NODE 7: REASSESS (Claude Opus)
# ============================================================================

async def reassess_node(state: PWSJourneyState, fallback_mode: bool = False, **kwargs) -> Dict:
    """
    Evaluate if evidence warrants reclassification.

    Uses Claude Opus for judgment calls.
    """
    triggers = state.get("reassessment_triggers", [])

    if not triggers:
        return {"current_phase": "guide", "reassessment_triggers": []}

    # Build reassessment prompt
    prompt = f"""Evaluate if this problem needs reclassification based on new evidence.

CURRENT CLASSIFICATION:
- Problem Type: {state['problem_type']}
- Cynefin Domain: {state['cynefin_domain']}
- Confidence: {state.get('classification_confidence', 0):.0%}

NEW EVIDENCE (Reassessment Triggers):
{chr(10).join('• ' + t for t in triggers)}

RECENT PROBES:
{json.dumps(state.get('probes_executed', [])[-3:], indent=2, default=str)}

Should we reclassify? Consider:
1. Is the new evidence strong enough to override initial classification?
2. Would reclassification lead to better tool/approach recommendations?
3. Is this a boundary case between domains?

Return JSON:
{{
    "should_reclassify": true/false,
    "new_problem_type": "type or null",
    "new_cynefin_domain": "domain or null",
    "new_confidence": 0.0-1.0,
    "reasoning": "Why or why not to reclassify"
}}"""

    if fallback_mode:
        response = await LLMRouter.bulk_generate(prompt, task_type="fallback_reassess")
    else:
        response = await LLMRouter.orchestrate(
            prompt,
            system="You are a PWS methodology expert. Make careful judgment calls about problem classification.",
            task_type="reassessment",
        )

    try:
        if "```json" in response:
            decision = json.loads(response.split("```json")[1].split("```")[0])
        else:
            decision = json.loads(response)
    except:
        decision = {"should_reclassify": False, "reasoning": "Parse error, maintaining current classification"}

    if decision.get("should_reclassify"):
        transition = {
            "from_type": state["problem_type"],
            "to_type": decision.get("new_problem_type"),
            "from_domain": state["cynefin_domain"],
            "to_domain": decision.get("new_cynefin_domain"),
            "reasoning": decision.get("reasoning"),
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "problem_type": decision.get("new_problem_type") or state["problem_type"],
            "cynefin_domain": decision.get("new_cynefin_domain") or state["cynefin_domain"],
            "classification_confidence": decision.get("new_confidence", state.get("classification_confidence")),
            "domain_transitions": [transition],
            "reassessment_triggers": [],  # Clear triggers
            "current_phase": "enrich",  # Re-enrich with new classification
        }

    return {
        "reassessment_triggers": [],  # Clear triggers
        "current_phase": "guide",
    }


# ============================================================================
# NODE 8: CHECKPOINT
# ============================================================================

async def checkpoint_node(state: PWSJourneyState, checkpoint_name: str = None, **kwargs) -> Dict:
    """
    Save progress checkpoint for cross-session persistence.
    """
    from utils.journey_state import CheckpointManager

    checkpoint_name = checkpoint_name or f"checkpoint_{len(state.get('checkpoints', [])) + 1}"

    result = await CheckpointManager.save_checkpoint(state, checkpoint_name)

    checkpoint_record = {
        "name": checkpoint_name,
        "timestamp": datetime.now().isoformat(),
        "phase": state["current_phase"],
        "problem_type": state["problem_type"],
        "cynefin_domain": state["cynefin_domain"],
        "success": result.get("success", False),
    }

    return {
        "checkpoints": [checkpoint_record],
        "current_phase": "guide",
    }


# ============================================================================
# NODE REGISTRY
# ============================================================================

NODE_REGISTRY = {
    "intake": intake_node,
    "classify": classify_node,
    "enrich": enrich_node,
    "generate_questions": generate_questions_node,
    "guide": guide_node,
    "probe": probe_node,
    "reassess": reassess_node,
    "checkpoint": checkpoint_node,
}


def get_node(name: str):
    """Get a node function by name."""
    return NODE_REGISTRY.get(name)


def list_nodes() -> List[str]:
    """List all available nodes."""
    return list(NODE_REGISTRY.keys())
