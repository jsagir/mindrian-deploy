"""
Conversation Quality Scorer
Evaluates AI responses against PWS methodology standards using Neo4j schema
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


@dataclass
class QualityDimension:
    """A single quality scoring dimension."""
    name: str
    score: float  # 0-100
    weight: float  # Contribution to overall score
    feedback: str  # Specific feedback for improvement
    evidence: List[str] = field(default_factory=list)


@dataclass
class QualityScore:
    """Complete quality assessment of a response."""
    overall_score: float
    dimensions: Dict[str, QualityDimension]
    improvement_suggestions: List[str]
    strengths: List[str]
    pws_alignment: str  # "high", "medium", "low"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# PWS Worthiness Criteria from Neo4j schema
PWS_WORTHINESS_CRITERIA = {
    "market_size": {
        "name": "Market Size",
        "description": "How many people/organizations are affected?",
        "weight": 0.15,
        "indicators": ["users", "customers", "market", "population", "scale", "millions", "billions"]
    },
    "future_urgency": {
        "name": "Future Urgency",
        "description": "How urgent will this problem become in the target timeframe?",
        "weight": 0.15,
        "indicators": ["urgent", "timeline", "deadline", "growing", "accelerating", "trend"]
    },
    "solvability": {
        "name": "Solvability",
        "description": "Can this problem be solved with foreseeable capabilities?",
        "weight": 0.20,
        "indicators": ["solution", "approach", "method", "technology", "feasible", "achievable"]
    },
    "expertise_match": {
        "name": "Expertise Match",
        "description": "Does the team have or can acquire relevant capabilities?",
        "weight": 0.15,
        "indicators": ["team", "skills", "capability", "experience", "expertise", "competency"]
    },
    "impact_potential": {
        "name": "Impact Potential",
        "description": "If solved, what is the magnitude of positive change?",
        "weight": 0.20,
        "indicators": ["impact", "change", "improvement", "benefit", "outcome", "transformation"]
    },
}

# PWS Methodology Quality Dimensions
PWS_QUALITY_DIMENSIONS = {
    "problem_before_solution": {
        "name": "Problem Before Solution",
        "description": "Does the response clarify the problem before jumping to solutions?",
        "weight": 0.25,
        "positive_indicators": ["problem", "issue", "challenge", "pain point", "what's wrong", "root cause"],
        "negative_indicators": ["you should", "just do", "the answer is", "simply implement"]
    },
    "assumption_awareness": {
        "name": "Assumption Awareness",
        "description": "Does the response surface and question underlying assumptions?",
        "weight": 0.20,
        "positive_indicators": ["assumption", "assuming", "if we assume", "might be assuming", "let's test", "validate"],
        "negative_indicators": []
    },
    "data_grounding": {
        "name": "Data Grounding",
        "description": "Is the response grounded in evidence and data rather than opinion?",
        "weight": 0.20,
        "positive_indicators": ["data", "evidence", "research", "study", "statistics", "%", "numbers", "measured"],
        "negative_indicators": ["everyone knows", "obviously", "clearly", "always", "never"]
    },
    "causal_chain": {
        "name": "Causal Chain Reasoning",
        "description": "Does the response show clear cause-effect reasoning?",
        "weight": 0.15,
        "positive_indicators": ["because", "therefore", "leads to", "results in", "causes", "effect", "consequence", "why"],
        "negative_indicators": []
    },
    "actionable_guidance": {
        "name": "Actionable Guidance",
        "description": "Does the response provide clear next steps?",
        "weight": 0.20,
        "positive_indicators": ["next step", "try", "consider", "explore", "validate", "test", "action", "experiment"],
        "negative_indicators": []
    },
}

# Larry Voice Quality Dimensions
VOICE_QUALITY_DIMENSIONS = {
    "socratic_method": {
        "name": "Socratic Method",
        "description": "Does the response ask probing questions to deepen understanding?",
        "weight": 0.30,
        "positive_indicators": ["?", "what if", "why do you", "how might", "have you considered", "what would happen"],
        "negative_indicators": []
    },
    "no_premature_solutions": {
        "name": "Avoids Premature Solutions",
        "description": "Does the response resist jumping to solutions before understanding the problem?",
        "weight": 0.25,
        "positive_indicators": ["let's first understand", "before solving", "what's the actual problem", "let me clarify"],
        "negative_indicators": ["just do", "you should", "the solution is", "simply"]
    },
    "teaching_moments": {
        "name": "Teaching Moments",
        "description": "Does the response include PWS methodology concepts and education?",
        "weight": 0.25,
        "positive_indicators": ["pws", "problem worth solving", "camera test", "dikw", "assumption", "validation", "worthiness"],
        "negative_indicators": []
    },
    "warmth_and_encouragement": {
        "name": "Warmth and Encouragement",
        "description": "Does the response show supportive and encouraging tone?",
        "weight": 0.20,
        "positive_indicators": ["great", "excellent", "good question", "interesting", "let's explore", "together"],
        "negative_indicators": ["wrong", "bad", "no", "that's not", "you're missing"]
    },
}


def get_neo4j_driver():
    """Get Neo4j driver if configured."""
    if not all([NEO4J_URI, NEO4J_PASSWORD]):
        return None
    try:
        from neo4j import GraphDatabase
        return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        return None


async def fetch_pws_criteria_from_neo4j() -> Dict:
    """Fetch PWS quality criteria from Neo4j schema."""
    driver = get_neo4j_driver()
    if not driver:
        return PWS_WORTHINESS_CRITERIA  # Fall back to static

    criteria = {}
    try:
        with driver.session() as session:
            # Fetch WorthinessCriteria nodes
            result = session.run("""
                MATCH (wc:WorthinessCriteria)
                WHERE wc.name IS NOT NULL
                RETURN wc.name as name, wc.description as description
            """)

            for record in result:
                name = record["name"]
                key = name.lower().replace(" ", "_")
                criteria[key] = {
                    "name": name,
                    "description": record["description"] or "",
                    "weight": 0.20,  # Equal weighting by default
                    "indicators": []
                }

            # Fetch ValidationRules if available
            validation_result = session.run("""
                MATCH (vr:ValidationRule)
                WHERE vr.description IS NOT NULL
                RETURN vr.name as name, vr.description as description
                LIMIT 10
            """)

            for record in validation_result:
                if record["description"]:
                    # Add as additional criteria
                    key = record["name"].lower().replace(" ", "_").replace("-", "_")[:20]
                    criteria[key] = {
                        "name": record["name"],
                        "description": record["description"],
                        "weight": 0.10,
                        "indicators": []
                    }

    except Exception as e:
        print(f"Neo4j criteria fetch error: {e}")
        return PWS_WORTHINESS_CRITERIA
    finally:
        driver.close()

    return criteria if criteria else PWS_WORTHINESS_CRITERIA


def score_dimension(
    text: str,
    dimension: Dict,
    is_voice: bool = False
) -> QualityDimension:
    """Score a single quality dimension based on text content."""
    text_lower = text.lower()

    # Count positive indicators
    positive_count = 0
    positive_matches = []
    for indicator in dimension.get("positive_indicators", dimension.get("indicators", [])):
        if indicator.lower() in text_lower:
            positive_count += 1
            positive_matches.append(indicator)

    # Count negative indicators
    negative_count = 0
    negative_matches = []
    for indicator in dimension.get("negative_indicators", []):
        if indicator.lower() in text_lower:
            negative_count += 1
            negative_matches.append(indicator)

    # Calculate base score
    # More positive indicators = higher score, negative indicators reduce score
    total_indicators = len(dimension.get("positive_indicators", dimension.get("indicators", [])))
    if total_indicators == 0:
        base_score = 50  # Neutral if no indicators defined
    else:
        base_score = min(100, (positive_count / max(1, total_indicators)) * 100)

    # Penalize for negative indicators
    penalty = negative_count * 15
    final_score = max(0, base_score - penalty)

    # Generate feedback
    if final_score >= 80:
        feedback = f"Strong: Found {positive_count} positive indicators for {dimension['name']}."
    elif final_score >= 50:
        feedback = f"Adequate: Some evidence of {dimension['name']}, but could be stronger."
    else:
        feedback = f"Needs improvement: Limited evidence of {dimension['name']}."

    if negative_matches:
        feedback += f" Warning: Found concerning patterns: {', '.join(negative_matches)}"

    return QualityDimension(
        name=dimension["name"],
        score=final_score,
        weight=dimension.get("weight", 0.20),
        feedback=feedback,
        evidence=positive_matches + [f"❌ {m}" for m in negative_matches]
    )


def score_response(
    ai_response: str,
    user_message: str = "",
    bot_id: str = "larry",
    phase: str = "",
    include_voice_scoring: bool = True
) -> QualityScore:
    """
    Score an AI response against PWS methodology standards.

    Args:
        ai_response: The AI's response text
        user_message: The user's original message (for context)
        bot_id: The bot that generated the response
        phase: Current workshop phase
        include_voice_scoring: Whether to include Larry voice scoring

    Returns:
        QualityScore with detailed breakdown
    """
    dimensions = {}
    overall_weighted_score = 0
    total_weight = 0

    # Score PWS methodology dimensions
    for key, dim_config in PWS_QUALITY_DIMENSIONS.items():
        dim_score = score_dimension(ai_response, dim_config)
        dimensions[key] = dim_score
        overall_weighted_score += dim_score.score * dim_score.weight
        total_weight += dim_score.weight

    # Score voice dimensions if requested
    if include_voice_scoring:
        for key, dim_config in VOICE_QUALITY_DIMENSIONS.items():
            dim_score = score_dimension(ai_response, dim_config, is_voice=True)
            dimensions[f"voice_{key}"] = dim_score
            # Voice dimensions have lower overall weight
            voice_weight = dim_score.weight * 0.5
            overall_weighted_score += dim_score.score * voice_weight
            total_weight += voice_weight

    # Calculate overall score
    overall_score = overall_weighted_score / total_weight if total_weight > 0 else 50

    # Generate improvement suggestions
    improvements = []
    strengths = []

    for dim in dimensions.values():
        if dim.score < 50:
            improvements.append(f"Improve {dim.name}: {dim.feedback}")
        elif dim.score >= 80:
            strengths.append(f"{dim.name}: {dim.feedback}")

    # Determine PWS alignment
    if overall_score >= 80:
        pws_alignment = "high"
    elif overall_score >= 60:
        pws_alignment = "medium"
    else:
        pws_alignment = "low"

    return QualityScore(
        overall_score=round(overall_score, 1),
        dimensions=dimensions,
        improvement_suggestions=improvements[:5],  # Top 5
        strengths=strengths[:5],  # Top 5
        pws_alignment=pws_alignment
    )


def format_quality_report(score: QualityScore) -> str:
    """Format a quality score as a readable report."""
    report = f"""## Quality Assessment Report

**Overall Score: {score.overall_score}/100** ({score.pws_alignment.upper()} PWS Alignment)

### Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
"""

    for key, dim in sorted(score.dimensions.items(), key=lambda x: -x[1].score):
        emoji = "✅" if dim.score >= 80 else "⚠️" if dim.score >= 50 else "❌"
        report += f"| {dim.name} | {dim.score:.0f} | {emoji} |\n"

    if score.strengths:
        report += f"\n### Strengths\n"
        for s in score.strengths:
            report += f"- ✅ {s}\n"

    if score.improvement_suggestions:
        report += f"\n### Areas for Improvement\n"
        for i in score.improvement_suggestions:
            report += f"- 💡 {i}\n"

    return report


# Quick scoring function for real-time use
def quick_quality_score(response: str) -> int:
    """
    Fast, lightweight quality scoring for real-time use.
    Returns score 0-100.
    """
    score = 50  # Baseline

    text_lower = response.lower()

    # Positive signals (+10 each)
    if "?" in response:  # Contains questions (Socratic)
        score += 10
    if any(w in text_lower for w in ["assumption", "assuming", "assume"]):
        score += 10
    if any(w in text_lower for w in ["evidence", "data", "research", "study"]):
        score += 10
    if any(w in text_lower for w in ["problem", "challenge", "issue"]):
        score += 8
    if any(w in text_lower for w in ["because", "therefore", "leads to"]):
        score += 7
    if any(w in text_lower for w in ["next step", "try", "consider", "explore"]):
        score += 8

    # Negative signals (-10 each)
    if "you should just" in text_lower:
        score -= 15
    if any(w in text_lower for w in ["obviously", "clearly everyone"]):
        score -= 10
    if len(response) < 100:  # Too short
        score -= 10
    if response.count("?") == 0 and len(response) > 200:  # Long response with no questions
        score -= 8

    return max(0, min(100, score))


# Score interpretation helpers
def get_score_emoji(score: float) -> str:
    """Get emoji representation of score."""
    if score >= 90:
        return "🌟"
    elif score >= 80:
        return "✅"
    elif score >= 70:
        return "👍"
    elif score >= 60:
        return "😐"
    elif score >= 50:
        return "⚠️"
    else:
        return "❌"


def get_score_label(score: float) -> str:
    """Get label for score."""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Adequate"
    elif score >= 60:
        return "Fair"
    elif score >= 50:
        return "Needs Work"
    else:
        return "Poor"
