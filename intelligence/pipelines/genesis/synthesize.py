"""
Stage 6: Breakthrough Synthesis
===============================
Score, validate, rank, and generate implementation roadmaps.
"""

import re
from datetime import datetime
from typing import Dict, List, Any


# Scoring weights
SCORING_WEIGHTS = {
    "breakthrough_potential": 0.35,
    "feasibility": 0.25,
    "cross_domain_impact": 0.25,
    "time_to_value": 0.15,
}

# Time-to-value scoring (shorter = better)
TIME_TO_VALUE_MAP = {
    (0, 3): 10.0,
    (3, 6): 8.5,
    (6, 12): 7.0,
    (12, 18): 5.5,
    (18, 24): 4.0,
    (24, 36): 2.5,
    (36, 999): 1.0,
}


def score_time_to_value(months: int) -> float:
    """Convert months to a 0-10 score."""
    for (low, high), score in TIME_TO_VALUE_MAP.items():
        if low <= months < high:
            return score
    return 1.0


def extract_scores_from_text(text: str) -> Dict[str, int]:
    """
    Extract numeric scores from expert panel text.

    Looks for patterns like:
    - "breakthrough potential: 8"
    - "feasibility (7/10)"
    - "impact: 9"
    """
    scores = {
        "breakthrough_potential": 6,  # defaults
        "feasibility": 6,
        "cross_domain_impact": 6,
        "time_to_value_months": 12,
    }

    # Patterns to match
    patterns = [
        (r'breakthrough[^:]*[:=]\s*(\d+)', "breakthrough_potential"),
        (r'potential[^:]*[:=]\s*(\d+)', "breakthrough_potential"),
        (r'feasibility[^:]*[:=]\s*(\d+)', "feasibility"),
        (r'impact[^:]*[:=]\s*(\d+)', "cross_domain_impact"),
        (r'cross[- ]?domain[^:]*[:=]\s*(\d+)', "cross_domain_impact"),
        (r'(\d+)\s*months?', "time_to_value_months"),
    ]

    text_lower = text.lower()
    for pattern, key in patterns:
        match = re.search(pattern, text_lower)
        if match:
            value = int(match.group(1))
            if key == "time_to_value_months":
                scores[key] = min(value, 36)  # Cap at 36 months
            else:
                scores[key] = min(max(value, 1), 10)  # 1-10 scale

    return scores


def parse_breakthroughs_from_panel(panel_findings: Dict) -> List[Dict]:
    """
    Parse breakthrough opportunities from expert panel output.

    Extracts structured breakthroughs from Round 3 ideation.
    """
    breakthroughs = []
    round_3 = panel_findings.get("rounds", {}).get("round_3_breakthroughs", [])

    for idx, item in enumerate(round_3):
        ideas_text = item.get("ideas", "")
        proposed_by = item.get("proposed_by", "Unknown Expert")
        hat = item.get("hat", "None")

        # Extract scores from text
        scores = extract_scores_from_text(ideas_text)

        # Try to extract breakthrough name
        name_match = re.search(r'(?:breakthrough|opportunity|idea)[:\s]*["\']?([^"\'\n\.]{10,50})', ideas_text.lower())
        name = name_match.group(1).strip().title() if name_match else f"Breakthrough {idx + 1}"

        # Extract domains mentioned
        domains = []
        for domain_pattern in [
            r'\b(machine.?learning|ml|ai)\b',
            r'\b(blockchain|web3|defi)\b',
            r'\b(fintech|finance)\b',
            r'\b(climate|sustainability|green)\b',
            r'\b(health|medical|biotech)\b',
            r'\b(education|edtech)\b',
        ]:
            if re.search(domain_pattern, ideas_text.lower()):
                domains.append(domain_pattern.replace(r'\b', '').replace('|', '/').replace('(', '').replace(')', '').replace('.?', '-'))

        if not domains:
            domains = ["Cross-Domain"]

        breakthroughs.append({
            "name": name,
            "description": ideas_text[:500],
            "proposed_by": proposed_by,
            "hat": hat,
            "domains_involved": domains[:3],
            "evidence": [f"Expert panel Round 3 - {proposed_by}"],
            "breakthrough_potential": scores["breakthrough_potential"],
            "feasibility": scores["feasibility"],
            "cross_domain_impact": scores["cross_domain_impact"],
            "time_to_value_months": scores["time_to_value_months"],
            "risks": ["Requires cross-domain validation", "Implementation complexity"],
            "implementation_steps": [
                "Validate core hypothesis with domain experts",
                "Build proof of concept",
                "Test with target users",
                "Scale implementation",
            ],
        })

    return breakthroughs


def score_breakthrough(breakthrough: Dict) -> Dict:
    """
    Score a breakthrough using weighted multi-criteria model.

    Returns breakthrough enriched with composite_score.
    """
    bp = min(max(breakthrough.get("breakthrough_potential", 5), 0), 10)
    fe = min(max(breakthrough.get("feasibility", 5), 0), 10)
    ci = min(max(breakthrough.get("cross_domain_impact", 5), 0), 10)
    ttv_months = breakthrough.get("time_to_value_months", 12)
    ttv_score = score_time_to_value(ttv_months)

    composite = (
        bp * SCORING_WEIGHTS["breakthrough_potential"] +
        fe * SCORING_WEIGHTS["feasibility"] +
        ci * SCORING_WEIGHTS["cross_domain_impact"] +
        ttv_score * SCORING_WEIGHTS["time_to_value"]
    )

    return {
        **breakthrough,
        "scores": {
            "breakthrough_potential": bp,
            "feasibility": fe,
            "cross_domain_impact": ci,
            "time_to_value_score": round(ttv_score, 1),
        },
        "composite_score": round(composite, 2),
    }


def validate_breakthrough(scored_bt: Dict) -> Dict:
    """
    Validate against Genesis gates.

    Gate 2: Evidence requirement
    Gate 3: Cross-domain validation (2+ domains)
    Gate 4: Implementation steps
    """
    validations = {
        "gate_2_evidence": {
            "passed": len(scored_bt.get("evidence", [])) >= 1,
            "details": f"{len(scored_bt.get('evidence', []))} evidence sources",
        },
        "gate_3_cross_domain": {
            "passed": len(scored_bt.get("domains_involved", [])) >= 2,
            "details": f"{len(scored_bt.get('domains_involved', []))} domains involved",
        },
        "gate_4_implementation": {
            "passed": len(scored_bt.get("implementation_steps", [])) >= 2,
            "details": f"{len(scored_bt.get('implementation_steps', []))} implementation steps",
        },
    }

    all_passed = all(v["passed"] for v in validations.values())

    return {
        **scored_bt,
        "validations": validations,
        "fully_validated": all_passed,
        "validation_score": sum(1 for v in validations.values() if v["passed"]) / 3,
    }


def generate_roadmap(breakthrough: Dict) -> Dict:
    """Generate implementation roadmap for a breakthrough."""
    ttv = breakthrough.get("scores", {}).get("time_to_value_months", 12) or 12
    steps = breakthrough.get("implementation_steps", [])

    phases = [
        {
            "phase": 1,
            "name": "Validation",
            "duration": f"0-{max(1, ttv // 4)} months",
            "focus": "Validate core hypothesis",
            "activities": steps[:1] if steps else ["Research validation"],
        },
        {
            "phase": 2,
            "name": "Prototype",
            "duration": f"{max(1, ttv // 4)}-{max(2, ttv // 2)} months",
            "focus": "Build proof of concept",
            "activities": steps[1:2] if len(steps) > 1 else ["Prototype development"],
        },
        {
            "phase": 3,
            "name": "Scale",
            "duration": f"{max(2, ttv // 2)}-{ttv} months",
            "focus": "Production deployment",
            "activities": steps[2:] if len(steps) > 2 else ["Scale and deploy"],
        },
    ]

    return {
        "breakthrough": breakthrough["name"],
        "total_timeline": f"{ttv} months",
        "phases": phases,
        "risks": breakthrough.get("risks", []),
        "success_criteria": [
            f"Achieve validation score > {breakthrough.get('validation_score', 0.5):.0%}",
            "Cross-domain integration verified",
            "User/market validation complete",
        ],
    }


def synthesize_breakthroughs(
    panel_findings: Dict,
    min_score: float = 5.0,
    max_breakthroughs: int = 5,
) -> Dict[str, Any]:
    """
    Full breakthrough synthesis pipeline.

    Args:
        panel_findings: Output from run_expert_panel()
        min_score: Minimum composite score threshold
        max_breakthroughs: Maximum number to return

    Returns:
        Synthesis with ranked breakthroughs and roadmaps
    """
    # Parse breakthroughs from panel
    breakthroughs = parse_breakthroughs_from_panel(panel_findings)

    if not breakthroughs:
        return {
            "top_opportunities": [],
            "implementation_roadmaps": [],
            "summary": {"total_candidates": 0, "validated": 0},
            "metadata": {"timestamp": datetime.utcnow().isoformat() + "Z"},
        }

    # Score all
    scored = [score_breakthrough(bt) for bt in breakthroughs]

    # Validate all
    validated = [validate_breakthrough(s) for s in scored]

    # Sort by composite score
    validated.sort(key=lambda x: x["composite_score"], reverse=True)

    # Filter by min score
    above_threshold = [v for v in validated if v["composite_score"] >= min_score]

    # Take top N
    top = above_threshold[:max_breakthroughs]

    # Generate roadmaps
    roadmaps = [generate_roadmap(bt) for bt in top]

    summary = {
        "total_candidates": len(breakthroughs),
        "scored": len(scored),
        "fully_validated": sum(1 for v in validated if v["fully_validated"]),
        "above_threshold": len(above_threshold),
        "top_selected": len(top),
        "avg_composite_score": round(
            sum(v["composite_score"] for v in validated) / max(len(validated), 1), 2
        ),
        "max_composite_score": round(
            max((v["composite_score"] for v in validated), default=0), 2
        ),
    }

    return {
        "top_opportunities": top,
        "implementation_roadmaps": roadmaps,
        "all_candidates": validated,
        "expert_insights": panel_findings.get("expert_insights", []),
        "cross_domain_connections": panel_findings.get("cross_domain_connections", []),
        "summary": summary,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "min_score_threshold": min_score,
            "scoring_weights": SCORING_WEIGHTS,
        },
    }
