"""
Stage 4: Research Orchestration
===============================
Generate execution plans, collaboration matrices, and quality controls.
"""

from datetime import datetime
from itertools import combinations
from typing import Dict, List, Any


def define_interaction(p1: Dict, p2: Dict) -> Dict:
    """
    Define interaction type between two personas.

    Interaction types:
    - SYNTHESIS (0.9): Integration expert ↔ anyone
    - BREAKTHROUGH (0.85): Authority ↔ Authority
    - VALIDATION (0.7): Methodology expert ↔ anyone
    - HAT_DIALOGUE (0.75): Different Six Hats perspectives
    - COLLABORATION (0.6): Same domain
    - EXPLORATORY (0.5): Default
    """
    OUTCOMES = {
        "SYNTHESIS": "Novel integration pathways and emergent breakthroughs",
        "VALIDATION": "Quality-assured findings with methodological certification",
        "COLLABORATION": "Deepened domain insights and validated approaches",
        "BREAKTHROUGH": "Paradigm-shifting insights and revolutionary approaches",
        "HAT_DIALOGUE": "Multi-perspective analysis from complementary thinking modes",
        "EXPLORATORY": "Unexpected connections and adjacent opportunities",
    }

    # Check for Six Hats dialogue opportunity
    p1_hat = p1.get("thinking_hat", {}).get("color")
    p2_hat = p2.get("thinking_hat", {}).get("color")
    hats_different = p1_hat and p2_hat and p1_hat != p2_hat

    # Determine type
    if "Integration" in p1["name"] or "Integration" in p2["name"]:
        itype, value = "SYNTHESIS", 0.9
        purpose = "Identify cross-domain breakthrough opportunities"
    elif "Methodology" in p1["name"] or "Methodology" in p2["name"]:
        itype, value = "VALIDATION", 0.7
        purpose = "Ensure methodological rigor and research quality"
    elif hats_different:
        # Six Hats dialogue - complementary perspectives
        itype, value = "HAT_DIALOGUE", 0.75
        purpose = f"Dialogue between {p1_hat} Hat ({p1.get('thinking_hat', {}).get('focus', 'unknown')}) and {p2_hat} Hat ({p2.get('thinking_hat', {}).get('focus', 'unknown')})"
    elif p1["primaryExpertise"] == p2["primaryExpertise"]:
        itype, value = "COLLABORATION", 0.6
        purpose = "Deep domain exploration and validation"
    elif p1["expertiseDepth"] == "AUTHORITY" and p2["expertiseDepth"] == "AUTHORITY":
        itype, value = "BREAKTHROUGH", 0.85
        purpose = "Challenge paradigms and identify revolutionary approaches"
    else:
        itype, value = "EXPLORATORY", 0.5
        purpose = "Explore unexpected connections"

    return {
        "between": [p1["name"], p2["name"]],
        "value": value,
        "type": itype,
        "purpose": purpose,
        "expectedOutcome": OUTCOMES.get(itype, OUTCOMES["EXPLORATORY"]),
        "hat_dialogue": hats_different,
    }


def generate_collaboration_matrix(personas: List[Dict]) -> Dict:
    """Generate collaboration matrix for all persona pairs."""
    matrix = {
        "primaryInteractions": [],
        "hatDialogues": [],  # Six Hats specific interactions
        "synthesisRoles": {},
        "conflictResolution": "Evidence-based consensus with documented dissent",
    }

    # Pairwise interactions
    for p1, p2 in combinations(personas, 2):
        interaction = define_interaction(p1, p2)
        if interaction["value"] > 0.4:
            matrix["primaryInteractions"].append(interaction)
            if interaction.get("hat_dialogue"):
                matrix["hatDialogues"].append(interaction)

    # Sort by value
    matrix["primaryInteractions"].sort(key=lambda x: x["value"], reverse=True)

    # Assign synthesis roles
    for p in personas:
        hat_info = p.get("thinking_hat", {})
        if "Integration" in p["name"]:
            role = "PRIMARY_SYNTHESIZER"
        elif "Methodology" in p["name"]:
            role = "QUALITY_VALIDATOR"
        elif hat_info.get("color") == "BLUE":
            role = "PROCESS_ORCHESTRATOR"
        elif hat_info.get("color") == "GREEN":
            role = "CREATIVE_CATALYST"
        elif hat_info.get("color") == "BLACK":
            role = "RISK_ASSESSOR"
        elif p["expertiseDepth"] == "AUTHORITY":
            role = "DOMAIN_VALIDATOR"
        else:
            role = "INSIGHT_CONTRIBUTOR"

        matrix["synthesisRoles"][p["name"]] = {
            "role": role,
            "hat": hat_info.get("name", "None"),
            "hat_focus": hat_info.get("focus", "domain expertise"),
        }

    return matrix


def define_execution_phases(personas: List[Dict]) -> List[Dict]:
    """Define 4-phase execution plan."""
    return [
        {
            "phase": 1,
            "name": "Parallel Domain Research",
            "duration": f"{10 + len(personas) * 2}-{15 + len(personas) * 3} minutes",
            "parallel": True,
            "activities": [
                {
                    "persona": p["name"],
                    "hat": p.get("thinking_hat", {}).get("name", "None"),
                    "action": "Execute research with domain + hat lens",
                    "queries": p.get("query_strategies_with_hat", p.get("queryStrategies", []))[:4],
                }
                for p in personas
            ],
        },
        {
            "phase": 2,
            "name": "Cross-Reference & Hat Dialogue",
            "duration": "10-15 minutes",
            "parallel": False,
            "activities": [
                {"action": "Cross-persona finding review"},
                {"action": "Six Hats dialogue sessions"},
                {"action": "Breakthrough validation"},
            ],
        },
        {
            "phase": 3,
            "name": "Synthesis Discussion",
            "duration": "15-25 minutes",
            "parallel": False,
            "activities": [
                {"action": "Expert panel convening (4 rounds)"},
                {"action": "Breakthrough prioritization"},
                {"action": "Implementation design"},
            ],
        },
        {
            "phase": 4,
            "name": "Consensus & Documentation",
            "duration": "10-15 minutes",
            "parallel": False,
            "activities": [
                {"action": "Consensus building"},
                {"action": "Final documentation"},
            ],
        },
    ]


def estimate_timeline(personas: List[Dict]) -> Dict:
    """Estimate research timeline."""
    n = len(personas)
    base = 40
    persona_complexity = n * 4
    hat_dialogues = sum(1 for p in personas if p.get("thinking_hat"))
    total = base + persona_complexity + hat_dialogues * 2

    return {
        "minimum": f"{round(total * 0.8)} minutes",
        "expected": f"{total} minutes",
        "maximum": f"{round(total * 1.3)} minutes",
    }


def orchestrate_research(
    personas: List[Dict],
    original_context: str = ""
) -> Dict[str, Any]:
    """
    Full research orchestration pipeline.

    Args:
        personas: List of persona dicts from generate_personas()
        original_context: Original challenge text

    Returns:
        Research plan with phases, collaboration matrix, timeline
    """
    return {
        "planId": f"GENESIS-{int(datetime.utcnow().timestamp())}",
        "context": (original_context[:500] + "...") if len(original_context) > 500 else original_context,
        "personaCount": len(personas),
        "personas": [
            {
                "name": p["name"],
                "expertise": p["primaryExpertise"],
                "hat": p.get("thinking_hat", {}).get("name", "None"),
                "queries": p.get("query_strategies_with_hat", p.get("queryStrategies", []))[:3],
            }
            for p in personas
        ],
        "executionPhases": define_execution_phases(personas),
        "collaborationMatrix": generate_collaboration_matrix(personas),
        "timeline": estimate_timeline(personas),
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_queries": sum(len(p.get("queryStrategies", [])) for p in personas),
            "hat_enriched_count": sum(1 for p in personas if p.get("thinking_hat")),
        },
    }
