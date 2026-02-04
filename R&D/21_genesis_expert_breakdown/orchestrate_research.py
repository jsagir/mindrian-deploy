"""
orchestrate_research.py — Research Orchestration Engine
=========================================================
Pipeline Stage 4: Generate execution plans, collaboration matrices,
quality controls, synthesis strategies, and timeline estimates for
multi-persona parallel research.

Implements the Genesis Engine's Research Orchestrator logic. Defines
pairwise interaction types, assigns synthesis roles, and produces
the complete research plan consumed by the expert panel simulation.

Usage:
    python scripts/orchestrate_research.py personas.json [--context context.txt] [research_plan.json]

Input:
    personas.json from generate_personas.py (Stage 3 output)
    Optional: context.txt with original challenge text

Output:
    research_plan.json with execution phases, collaboration matrix,
    quality controls, expected outcomes, timeline, synthesis strategy
"""

import json
import sys
import argparse
from datetime import datetime
from itertools import combinations


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def define_execution_phases(personas: list) -> list:
    """
    Define 4-phase execution plan with activities per persona.

    Phase 1: Parallel Domain Research (search execution)
    Phase 2: Cross-Reference & Validation (finding review)
    Phase 3: Synthesis Discussion (expert panel)
    Phase 4: Consensus & Documentation (final report)

    Args:
        personas: List of persona dicts from Stage 3.

    Returns:
        List of phase dicts with activities, duration, and outputs.
    """
    print("  Defining execution phases...")

    phases = [
        {
            "phase": 1,
            "name": "Parallel Domain Research",
            "duration": f"{15 + len(personas) * 2}-{20 + len(personas) * 3} minutes",
            "parallel": True,
            "activities": [
                {
                    "persona": p["name"],
                    "action": "Execute Tavily searches",
                    "queries": p["queryStrategies"][:3],
                    "expected_findings": "5-10 relevant sources per query",
                    "analysis_depth": p["expertiseDepth"],
                }
                for p in personas
            ],
            "outputs": [
                "Domain-specific research findings",
                "Initial breakthrough indicators",
                "Cross-reference opportunities",
            ],
        },
        {
            "phase": 2,
            "name": "Cross-Reference & Validation",
            "duration": "10-15 minutes",
            "parallel": False,
            "activities": [
                {
                    "action": "Cross-persona finding review",
                    "description": "Each persona reviews findings from related domains",
                    "method": "Systematic cross-validation",
                },
                {
                    "action": "Overlap identification",
                    "description": "Identify common themes and contradictions",
                    "method": "Comparative analysis matrix",
                },
                {
                    "action": "Breakthrough validation",
                    "description": "Validate potential breakthroughs against multiple domains",
                    "method": "Multi-domain verification protocol",
                },
            ],
            "outputs": [
                "Validated breakthrough opportunities",
                "Cross-domain connection map",
                "Contradiction resolution log",
            ],
        },
        {
            "phase": 3,
            "name": "Synthesis Discussion",
            "duration": "20-30 minutes",
            "parallel": False,
            "activities": [
                {
                    "action": "Expert panel convening",
                    "description": "All personas engage in structured discussion",
                    "method": "Moderated expert panel format (4 rounds)",
                },
                {
                    "action": "Breakthrough prioritization",
                    "description": "Rank opportunities by impact and feasibility",
                    "method": "Multi-criteria decision analysis",
                },
                {
                    "action": "Implementation design",
                    "description": "Design practical pathways for top opportunities",
                    "method": "Collaborative roadmapping",
                },
            ],
            "outputs": [
                "Prioritized breakthrough list",
                "Implementation roadmaps",
                "Risk mitigation strategies",
                "Next-step recommendations",
            ],
        },
        {
            "phase": 4,
            "name": "Consensus & Documentation",
            "duration": "10-15 minutes",
            "parallel": False,
            "activities": [
                {
                    "action": "Consensus building",
                    "description": "Resolve remaining disagreements",
                    "method": "Evidence-based consensus protocol",
                },
                {
                    "action": "Final documentation",
                    "description": "Compile comprehensive findings report",
                    "method": "Structured synthesis template",
                },
            ],
            "outputs": [
                "Final breakthrough report",
                "Executive summary",
                "Action plan",
            ],
        },
    ]

    return phases


def define_interaction(p1: dict, p2: dict) -> dict:
    """
    Define the interaction type between two personas.

    Scoring rules:
    - Integration expert ↔ anyone: 0.9 (SYNTHESIS)
    - Methodology expert ↔ anyone: 0.7 (VALIDATION)
    - Authority ↔ Authority: 0.85 (BREAKTHROUGH)
    - Parent ↔ Subdomain: 0.8 (HIERARCHICAL)
    - Same domain: 0.6 (COLLABORATION)
    - Other: 0.5 (EXPLORATORY)

    Args:
        p1: First persona dict.
        p2: Second persona dict.

    Returns:
        Interaction dict with value, type, purpose, and expected outcome.
    """
    OUTCOMES = {
        "SYNTHESIS": "Novel integration pathways and emergent breakthrough opportunities",
        "VALIDATION": "Quality-assured findings with methodological certification",
        "COLLABORATION": "Deepened domain insights and validated approaches",
        "HIERARCHICAL": "Technical specifications and implementation pathways",
        "BREAKTHROUGH": "Paradigm-shifting insights and revolutionary approaches",
        "EXPLORATORY": "Unexpected connections and adjacent innovation opportunities",
    }

    STYLES = {
        "SYNTHESIS": "Integrative dialogue focusing on connections",
        "VALIDATION": "Critical review with constructive feedback",
        "COLLABORATION": "Peer exchange with mutual enrichment",
        "HIERARCHICAL": "Technical mentorship and guidance",
        "BREAKTHROUGH": "Visionary exploration and paradigm challenging",
        "EXPLORATORY": "Open-ended discovery and creative ideation",
    }

    # Determine type
    if "Integration" in p1["name"] or "Integration" in p2["name"]:
        itype, value = "SYNTHESIS", 0.9
        purpose = "Identify cross-domain breakthrough opportunities and emergent synergies"
    elif "Methodology" in p1["name"] or "Methodology" in p2["name"]:
        itype, value = "VALIDATION", 0.7
        purpose = "Ensure methodological rigor and research quality"
    elif p1["primaryExpertise"] == p2["primaryExpertise"]:
        itype, value = "COLLABORATION", 0.6
        purpose = "Deep domain exploration and validation"
    elif (p1["domainCategory"] == "SUBDOMAIN" or p2["domainCategory"] == "SUBDOMAIN") and \
         (p1["primaryExpertise"] in p2["name"] or p2["primaryExpertise"] in p1["name"]):
        itype, value = "HIERARCHICAL", 0.8
        purpose = "Technical deep-dive and specialized insight integration"
    elif p1["expertiseDepth"] == "AUTHORITY" and p2["expertiseDepth"] == "AUTHORITY":
        itype, value = "BREAKTHROUGH", 0.85
        purpose = "Challenge paradigms and identify revolutionary approaches"
    else:
        itype, value = "EXPLORATORY", 0.5
        purpose = "Explore unexpected connections and adjacent possibilities"

    return {
        "between": [p1["name"], p2["name"]],
        "value": value,
        "type": itype,
        "purpose": purpose,
        "expectedOutcome": OUTCOMES.get(itype, OUTCOMES["EXPLORATORY"]),
        "communicationStyle": STYLES.get(itype, STYLES["EXPLORATORY"]),
    }


def generate_collaboration_matrix(personas: list) -> dict:
    """
    Generate complete collaboration matrix for all persona pairs.

    Defines pairwise interactions, assigns synthesis roles, and
    establishes conflict resolution protocols.

    Args:
        personas: List of persona dicts.

    Returns:
        Collaboration matrix dict.
    """
    print(f"  Building collaboration matrix ({len(personas)} personas)...")

    matrix = {
        "primaryInteractions": [],
        "synthesisRoles": {},
        "conflictResolution": "Evidence-based consensus with documented dissent",
        "interactionProtocol": "Structured dialogue with clear handoffs",
    }

    # Pairwise interactions
    for p1, p2 in combinations(personas, 2):
        interaction = define_interaction(p1, p2)
        if interaction["value"] > 0.4:
            matrix["primaryInteractions"].append(interaction)

    # Sort by value descending
    matrix["primaryInteractions"].sort(key=lambda x: x["value"], reverse=True)

    # Assign synthesis roles
    for p in personas:
        if "Integration" in p["name"]:
            matrix["synthesisRoles"][p["name"]] = {
                "role": "PRIMARY_SYNTHESIZER",
                "responsibilities": [
                    "Drive cross-domain connections",
                    "Identify emergent properties",
                    "Lead breakthrough identification",
                ],
            }
        elif "Methodology" in p["name"]:
            matrix["synthesisRoles"][p["name"]] = {
                "role": "QUALITY_VALIDATOR",
                "responsibilities": [
                    "Ensure research rigor",
                    "Validate methodologies",
                    "Assess evidence quality",
                ],
            }
        elif p["expertiseDepth"] == "AUTHORITY":
            matrix["synthesisRoles"][p["name"]] = {
                "role": "DOMAIN_VALIDATOR",
                "responsibilities": [
                    "Validate domain-specific insights",
                    "Identify paradigm shifts",
                    "Assess breakthrough potential",
                ],
            }
        elif p["domainCategory"] == "SUBDOMAIN":
            matrix["synthesisRoles"][p["name"]] = {
                "role": "TECHNICAL_VALIDATOR",
                "responsibilities": [
                    "Verify technical feasibility",
                    "Provide implementation details",
                    "Assess technical risks",
                ],
            }
        else:
            matrix["synthesisRoles"][p["name"]] = {
                "role": "INSIGHT_CONTRIBUTOR",
                "responsibilities": [
                    "Contribute domain insights",
                    "Identify opportunities",
                    "Support validation",
                ],
            }

    print(f"  → {len(matrix['primaryInteractions'])} interactions defined")
    print(f"  → {len(matrix['synthesisRoles'])} roles assigned")
    return matrix


def define_quality_controls(personas: list) -> dict:
    """
    Define quality control measures based on persona composition.

    Args:
        personas: List of persona dicts.

    Returns:
        Quality controls dict.
    """
    has_methodology = any("Methodology" in p["name"] for p in personas)
    authority_count = sum(1 for p in personas if p["expertiseDepth"] == "AUTHORITY")

    return {
        "evidenceStandards": {
            "minimum": "Peer-reviewed sources or validated patents",
            "preferred": "Multiple corroborating sources from different domains",
            "breakthrough": "Novel connections validated by at least 2 domain experts",
        },
        "validationProtocol": {
            "level1": "Self-validation within domain",
            "level2": "Cross-domain expert validation",
            "level3": ("Methodology expert certification" if has_methodology
                       else "Multi-expert consensus"),
        },
        "conflictResolution": {
            "method": "Evidence-based argumentation",
            "escalation": ("Authority panel review" if authority_count > 1
                           else "Integration expert mediation"),
            "documentation": "All dissenting views recorded with rationale",
        },
        "qualityMetrics": [
            "Source credibility score (1-10)",
            "Cross-domain validation count",
            "Implementation feasibility rating",
            "Breakthrough potential score",
        ],
    }


def estimate_timeline(personas: list) -> dict:
    """
    Estimate research timeline based on persona count and depth.

    Args:
        personas: List of persona dicts.

    Returns:
        Timeline dict with min/expected/max and phase allocation.
    """
    n = len(personas)
    base = 45
    persona_complexity = n * 5
    interaction_complexity = (n * (n - 1) // 2) * 2
    depth_complexity = sum(10 for p in personas if p["expertiseDepth"] == "AUTHORITY")

    total = base + persona_complexity + interaction_complexity + depth_complexity

    return {
        "minimum": f"{round(total * 0.8)} minutes",
        "expected": f"{total} minutes",
        "maximum": f"{round(total * 1.3)} minutes",
        "phases": {
            "research": "40%",
            "validation": "20%",
            "synthesis": "30%",
            "documentation": "10%",
        },
    }


def define_synthesis_strategy(personas: list) -> dict:
    """
    Define synthesis strategy based on persona composition.

    Args:
        personas: List of persona dicts.

    Returns:
        Synthesis strategy dict.
    """
    has_integrator = any("Integration" in p["name"] for p in personas)
    domain_count = len(set(p["primaryExpertise"] for p in personas))

    return {
        "approach": "Integration-led synthesis" if has_integrator else "Collaborative emergence",
        "method": "Hierarchical clustering" if domain_count > 3 else "Full panel discussion",
        "prioritization": {
            "criteria": [
                "Breakthrough potential (0-10)",
                "Implementation feasibility (0-10)",
                "Cross-domain impact (0-10)",
                "Time to value (months)",
            ],
            "weights": {
                "breakthroughPotential": 0.35,
                "feasibility": 0.25,
                "impact": 0.25,
                "timeToValue": 0.15,
            },
        },
        "deliverableFormat": {
            "structure": "Executive summary → Detailed findings → Implementation roadmap",
            "visualizations": ["Opportunity matrix", "Connection graph", "Timeline"],
            "actionability": "Each recommendation includes next 3 concrete steps",
        },
    }


def orchestrate_research(personas: list, original_context: str = "") -> dict:
    """
    Full research orchestration pipeline.

    Generates execution phases, collaboration matrix, quality controls,
    expected outcomes, timeline, and synthesis strategy.

    Args:
        personas: List of persona dicts from Stage 3.
        original_context: Original challenge text for reference.

    Returns:
        Complete research plan dict.
    """
    print(f"\n🔬 RESEARCH ORCHESTRATION ENGINE")
    print(f"   Orchestrating {len(personas)} personas...\n")

    plan = {
        "planId": f"RESEARCH-{int(datetime.utcnow().timestamp())}",
        "context": (original_context[:500] + "...") if len(original_context) > 500
                   else original_context,
        "personaCount": len(personas),
        "personas": [
            {
                "name": p["name"],
                "expertise": p["primaryExpertise"],
                "queries": p["queryStrategies"],
                "focus": p["researchApproach"]["primary"],
                "deliverables": p["outputExpectations"],
            }
            for p in personas
        ],
        "executionPhases": define_execution_phases(personas),
        "collaborationMatrix": generate_collaboration_matrix(personas),
        "qualityControls": define_quality_controls(personas),
        "timeline": estimate_timeline(personas),
        "synthesisStrategy": define_synthesis_strategy(personas),
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_queries": sum(len(p["queryStrategies"]) for p in personas),
            "total_interactions": len(list(combinations(personas, 2))),
        },
    }

    print(f"✅ Research plan generated:")
    print(f"   {len(plan['executionPhases'])} phases")
    print(f"   {len(plan['collaborationMatrix']['primaryInteractions'])} interactions")
    print(f"   {plan['metadata']['total_queries']} search queries planned")
    print(f"   Timeline: {plan['timeline']['expected']}\n")

    return plan


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Genesis Research Orchestrator — Stage 4 of Expert Breakdown Pipeline"
    )
    parser.add_argument(
        "personas_input",
        help="Personas JSON from Stage 3 (personas.json)"
    )
    parser.add_argument(
        "--context",
        default="",
        help="Optional: original context text file"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="research_plan.json",
        help="Output JSON path (default: research_plan.json)"
    )
    args = parser.parse_args()

    # Load personas with error handling
    try:
        with open(args.personas_input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Personas file not found: {args.personas_input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.personas_input}: {e}")
        sys.exit(1)

    personas = data.get("personas", data) if isinstance(data, dict) else data

    if not personas or len(personas) < 2:
        raise ValueError(
            f"Need at least 2 personas for orchestration, got {len(personas)}. "
            f"Expected output from generate_personas.py (Stage 3)."
        )

    print(f"Loaded {len(personas)} personas from {args.personas_input}")

    # Load context if provided
    context = ""
    if args.context:
        try:
            with open(args.context, "r", encoding="utf-8") as f:
                context = f.read()
            print(f"Loaded context from {args.context}")
        except FileNotFoundError:
            print(f"Warning: Context file not found: {args.context}. Continuing without context.")

    # Orchestrate
    plan = orchestrate_research(personas, context)

    # Save with error handling
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Error: Could not write to {args.output}: {e}")
        sys.exit(1)

    print(f"Saved research plan to {args.output}")
    return plan


if __name__ == "__main__":
    main()
