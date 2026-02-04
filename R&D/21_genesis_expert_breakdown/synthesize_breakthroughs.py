"""
synthesize_breakthroughs.py — Breakthrough Synthesis Engine
=============================================================
Pipeline Stage 6: Cross-domain integration, breakthrough scoring,
validation, ranking, and implementation roadmap generation.

Implements the Genesis Engine's synthesis logic. Scores each breakthrough
using a weighted multi-criteria model, validates against evidence and
cross-domain requirements, and produces ranked opportunities with
implementation plans.

Usage:
    python scripts/synthesize_breakthroughs.py findings.json [synthesis.json]
        [--min-score 5.0] [--max-breakthroughs 5]

Input:
    findings.json — Expert panel findings with structure:
    {
        "breakthroughs": [
            {
                "name": "...",
                "description": "...",
                "domains_involved": ["Domain-A", "Domain-B"],
                "evidence": ["source1", "source2"],
                "breakthrough_potential": 8,
                "feasibility": 7,
                "cross_domain_impact": 9,
                "time_to_value_months": 6,
                "risks": [...],
                "implementation_steps": [...]
            }
        ],
        "expert_insights": [...],
        "cross_domain_connections": [...]
    }

Output:
    synthesis.json with ranked breakthroughs, scores, validations,
    implementation roadmaps, and risk assessments
"""

import json
import sys
import argparse
from datetime import datetime


# =============================================================================
# SCORING CONFIGURATION
# =============================================================================

SCORING_WEIGHTS = {
    "breakthrough_potential": 0.35,
    "feasibility": 0.25,
    "cross_domain_impact": 0.25,
    "time_to_value": 0.15,
}

# Time-to-value scoring: shorter = higher score
TIME_TO_VALUE_MAP = {
    (0, 3): 10.0,    # 0-3 months
    (3, 6): 8.5,     # 3-6 months
    (6, 12): 7.0,    # 6-12 months
    (12, 18): 5.5,   # 12-18 months
    (18, 24): 4.0,   # 18-24 months
    (24, 36): 2.5,   # 24-36 months
    (36, 999): 1.0,  # 36+ months
}


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def score_time_to_value(months: int) -> float:
    """
    Convert months to a 0-10 score (shorter = better).

    Args:
        months: Estimated months to value.

    Returns:
        Score from 0-10.
    """
    for (low, high), score in TIME_TO_VALUE_MAP.items():
        if low <= months < high:
            return score
    return 1.0


def score_breakthrough(breakthrough: dict) -> dict:
    """
    Score a single breakthrough using weighted multi-criteria model.

    Criteria:
    - Breakthrough Potential (0-10, weight 0.35)
    - Implementation Feasibility (0-10, weight 0.25)
    - Cross-Domain Impact (0-10, weight 0.25)
    - Time to Value (0-10 derived from months, weight 0.15)

    Args:
        breakthrough: Dict with raw scores and metadata.

    Returns:
        Breakthrough dict enriched with composite_score, score_breakdown,
        and innovation_differential.
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

    # Innovation differential: how much the cross-domain aspect adds
    single_domain_estimate = bp * 0.6  # Estimated single-domain score
    innovation_differential = composite - single_domain_estimate

    return {
        **breakthrough,
        "scores": {
            "breakthrough_potential": bp,
            "feasibility": fe,
            "cross_domain_impact": ci,
            "time_to_value_score": round(ttv_score, 1),
            "time_to_value_months": ttv_months,
        },
        "composite_score": round(composite, 2),
        "innovation_differential": round(max(innovation_differential, 0), 2),
    }


def validate_breakthrough(scored_bt: dict) -> dict:
    """
    Validate a scored breakthrough against Genesis Engine gates.

    Gate 2: Evidence requirement (must have supporting sources)
    Gate 3: Cross-domain validation (must involve 2+ domains)
    Gate 4: Implementation reality (must have concrete steps)

    Args:
        scored_bt: Scored breakthrough dict.

    Returns:
        Breakthrough dict enriched with validation results.
    """
    validations = {
        "gate_2_evidence": {
            "passed": False,
            "requirement": "Must have supporting evidence sources",
            "findings": "",
        },
        "gate_3_cross_domain": {
            "passed": False,
            "requirement": "Must emerge from 2+ domain intersection",
            "findings": "",
        },
        "gate_4_implementation": {
            "passed": False,
            "requirement": "Must include concrete next steps",
            "findings": "",
        },
    }

    # Gate 2: Evidence
    evidence = scored_bt.get("evidence", [])
    if len(evidence) >= 1:
        validations["gate_2_evidence"]["passed"] = True
        validations["gate_2_evidence"]["findings"] = (
            f"{len(evidence)} evidence sources provided"
        )
    else:
        validations["gate_2_evidence"]["findings"] = "No evidence sources — requires research backup"

    # Gate 3: Cross-domain
    domains = scored_bt.get("domains_involved", [])
    if len(domains) >= 2:
        validations["gate_3_cross_domain"]["passed"] = True
        validations["gate_3_cross_domain"]["findings"] = (
            f"Spans {len(domains)} domains: {', '.join(domains)}"
        )
    else:
        validations["gate_3_cross_domain"]["findings"] = (
            f"Only {len(domains)} domain(s) — needs cross-domain validation"
        )

    # Gate 4: Implementation
    steps = scored_bt.get("implementation_steps", [])
    if len(steps) >= 2:
        validations["gate_4_implementation"]["passed"] = True
        validations["gate_4_implementation"]["findings"] = (
            f"{len(steps)} implementation steps defined"
        )
    else:
        validations["gate_4_implementation"]["findings"] = (
            "Insufficient implementation detail — needs concrete steps"
        )

    all_passed = all(v["passed"] for v in validations.values())

    return {
        **scored_bt,
        "validations": validations,
        "fully_validated": all_passed,
        "validation_score": sum(1 for v in validations.values() if v["passed"]) / 3,
    }


def generate_implementation_roadmap(breakthrough: dict) -> dict:
    """
    Generate a phased implementation roadmap for a validated breakthrough.

    Args:
        breakthrough: Validated and scored breakthrough dict.

    Returns:
        Implementation roadmap dict with phases, milestones, resources, and risks.
    """
    ttv = breakthrough.get("scores", {}).get("time_to_value_months", 12)
    steps = breakthrough.get("implementation_steps", [])
    risks = breakthrough.get("risks", [])

    # Determine phase structure based on timeline
    if ttv <= 6:
        phases = [
            {"phase": 1, "name": "Foundation", "duration": f"0-{ttv // 3} months",
             "focus": "Validate core hypothesis and build prototype"},
            {"phase": 2, "name": "Development", "duration": f"{ttv // 3}-{2 * ttv // 3} months",
             "focus": "Build minimum viable solution"},
            {"phase": 3, "name": "Launch", "duration": f"{2 * ttv // 3}-{ttv} months",
             "focus": "Deploy and measure impact"},
        ]
    else:
        phases = [
            {"phase": 1, "name": "Research & Validation", "duration": f"0-{ttv // 4} months",
             "focus": "Deep research and hypothesis validation"},
            {"phase": 2, "name": "Prototype", "duration": f"{ttv // 4}-{ttv // 2} months",
             "focus": "Build and test proof of concept"},
            {"phase": 3, "name": "Scale", "duration": f"{ttv // 2}-{3 * ttv // 4} months",
             "focus": "Scale solution and integrate"},
            {"phase": 4, "name": "Optimize", "duration": f"{3 * ttv // 4}-{ttv} months",
             "focus": "Optimize for production and expand"},
        ]

    # Map steps to phases
    steps_per_phase = max(1, len(steps) // len(phases))
    for i, phase in enumerate(phases):
        start = i * steps_per_phase
        end = start + steps_per_phase if i < len(phases) - 1 else len(steps)
        phase["key_activities"] = steps[start:end] if steps else [
            f"Define {phase['name'].lower()} requirements",
            f"Execute {phase['name'].lower()} activities",
        ]

    # Risk mapping
    risk_assessment = []
    for risk in risks[:5]:
        if isinstance(risk, str):
            risk_assessment.append({
                "risk": risk,
                "probability": "MEDIUM",
                "impact": "MEDIUM",
                "mitigation": f"Monitor and develop contingency for: {risk}",
            })
        elif isinstance(risk, dict):
            risk_assessment.append(risk)

    return {
        "breakthrough": breakthrough["name"],
        "total_timeline": f"{ttv} months",
        "phases": phases,
        "success_criteria": [
            f"Achieve composite score validation > {breakthrough.get('composite_score', 7):.1f}",
            "Cross-domain integration verified by domain experts",
            "Implementation feasibility confirmed with prototype",
        ],
        "resources": {
            "domains_required": breakthrough.get("domains_involved", []),
            "expertise_level": "AUTHORITY" if breakthrough.get("composite_score", 0) > 8
                              else "EXPERT",
        },
        "risks": risk_assessment,
    }


def synthesize_breakthroughs(
    findings: dict,
    min_score: float = 5.0,
    max_breakthroughs: int = 5,
) -> dict:
    """
    Full breakthrough synthesis pipeline.

    Scores → Validates → Ranks → Generates roadmaps for top opportunities.

    Args:
        findings: Expert panel findings dict with breakthroughs list.
        min_score: Minimum composite score to include (default: 5.0).
        max_breakthroughs: Maximum number of breakthroughs to return (default: 5).

    Returns:
        Complete synthesis dict with ranked opportunities and roadmaps.
    """
    print(f"\n⚡ BREAKTHROUGH SYNTHESIS ENGINE")
    breakthroughs = findings.get("breakthroughs", [])
    print(f"   Processing {len(breakthroughs)} candidate breakthroughs...\n")

    if not breakthroughs:
        print("  ⚠️  No breakthroughs to synthesize")
        return {
            "top_opportunities": [],
            "all_candidates": [],
            "summary": {"total_candidates": 0, "validated": 0, "above_threshold": 0},
            "metadata": {"timestamp": datetime.utcnow().isoformat() + "Z"},
        }

    # Step 1: Score all breakthroughs
    scored = []
    for bt in breakthroughs:
        s = score_breakthrough(bt)
        scored.append(s)
        print(f"  📊 Scored: {s['name']} → {s['composite_score']:.2f}")

    # Step 2: Validate all scored breakthroughs
    validated = []
    for s in scored:
        v = validate_breakthrough(s)
        validated.append(v)
        status = "✅ PASS" if v["fully_validated"] else "⚠️  PARTIAL"
        print(f"  {status}: {v['name']} (gates: {v['validation_score']:.0%})")

    # Step 3: Rank by composite score
    validated.sort(key=lambda x: x["composite_score"], reverse=True)

    # Step 4: Filter by minimum score
    above_threshold = [v for v in validated if v["composite_score"] >= min_score]

    # Step 5: Take top N
    top = above_threshold[:max_breakthroughs]

    # Step 6: Generate implementation roadmaps for top breakthroughs
    roadmaps = []
    for bt in top:
        roadmap = generate_implementation_roadmap(bt)
        roadmaps.append(roadmap)
        print(f"  🗺️  Roadmap: {bt['name']} → {roadmap['total_timeline']}")

    # Build summary
    summary = {
        "total_candidates": len(breakthroughs),
        "scored": len(scored),
        "fully_validated": sum(1 for v in validated if v["fully_validated"]),
        "above_threshold": len(above_threshold),
        "top_selected": len(top),
        "avg_composite_score": round(
            sum(v["composite_score"] for v in validated) / max(len(validated), 1), 2
        ),
        "max_composite_score": round(max(
            (v["composite_score"] for v in validated), default=0
        ), 2),
        "scoring_weights": SCORING_WEIGHTS,
    }

    result = {
        "top_opportunities": top,
        "implementation_roadmaps": roadmaps,
        "all_candidates": validated,
        "expert_insights": findings.get("expert_insights", []),
        "cross_domain_connections": findings.get("cross_domain_connections", []),
        "summary": summary,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "min_score_threshold": min_score,
            "max_breakthroughs": max_breakthroughs,
        },
    }

    print(f"\n✅ Synthesis complete:")
    print(f"   {summary['top_selected']} top opportunities selected")
    print(f"   {summary['fully_validated']}/{summary['total_candidates']} fully validated")
    print(f"   Best score: {summary['max_composite_score']}")
    print(f"   Average score: {summary['avg_composite_score']}\n")

    return result


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Genesis Breakthrough Synthesizer — Stage 6 of Expert Breakdown Pipeline"
    )
    parser.add_argument(
        "input",
        help="Expert panel findings JSON (findings.json)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="synthesis.json",
        help="Output JSON path (default: synthesis.json)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=5.0,
        help="Minimum composite score threshold (default: 5.0)"
    )
    parser.add_argument(
        "--max-breakthroughs",
        type=int,
        default=5,
        help="Maximum breakthroughs to return (default: 5)"
    )
    args = parser.parse_args()

    # Validate parameters
    if args.min_score < 0 or args.min_score > 10:
        raise ValueError(f"min-score must be between 0 and 10, got {args.min_score}")
    if args.max_breakthroughs < 1:
        raise ValueError(f"max-breakthroughs must be >= 1, got {args.max_breakthroughs}")

    # Load findings with error handling
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            findings = json.load(f)
    except FileNotFoundError:
        print(f"Error: Findings file not found: {args.input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input}: {e}")
        sys.exit(1)

    # Validate findings structure
    if "breakthroughs" not in findings:
        raise ValueError(
            "Findings JSON missing 'breakthroughs' key. "
            "Expected expert panel output with breakthrough candidates."
        )

    print(f"Loaded findings from {args.input}")

    # Synthesize
    result = synthesize_breakthroughs(
        findings,
        min_score=args.min_score,
        max_breakthroughs=args.max_breakthroughs,
    )

    # Save with error handling
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Error: Could not write to {args.output}: {e}")
        sys.exit(1)

    print(f"Saved synthesis to {args.output}")
    return result


if __name__ == "__main__":
    main()
