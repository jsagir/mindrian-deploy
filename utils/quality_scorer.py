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


# ============================================================
# PWS PROBLEM CLASSIFICATION CRITERIA (From Neo4j Schema)
# The TRUE measurement for PWS assessment
# ============================================================

# Problem Definition Clarity (Undefined → Ill-Defined → Well-Defined)
PROBLEM_DEFINITION_CRITERIA = {
    "well_defined": {
        "name": "Well-Defined Problem",
        "description": "Specific, measurable problem with binary/falsifiable outcomes, clear user segments, and bounded scope",
        "indicators": ["specific", "measurable", "testable", "falsifiable", "bounded", "clear scope", "defined user", "success criteria"],
        "score_boost": 30,  # Well-defined problems get higher quality scores
    },
    "ill_defined": {
        "name": "Ill-Defined Problem",
        "description": "General direction identified but lacks specificity and testability. Emerging opportunities that need clarification",
        "indicators": ["general direction", "emerging", "unclear", "needs clarification", "partial understanding", "ambiguous"],
        "score_boost": 15,
    },
    "undefined": {
        "name": "Undefined Problem",
        "description": "Broad opportunity space with future-back thinking and scattered observations. Starting point for exploration",
        "indicators": ["future", "opportunity space", "scattered", "exploration", "what if", "might be", "could be"],
        "score_boost": 5,
    },
}

# Complexity/Wickedness Assessment (Simple → Complex → Wicked)
COMPLEXITY_WICKEDNESS_CRITERIA = {
    "simple": {
        "name": "Simple/Tame Problem",
        "description": "Clear cause and effect, best practices available, straightforward resolution",
        "indicators": ["obvious", "straightforward", "clear solution", "best practice", "standard", "routine"],
        "cynefin": "Clear",
    },
    "complicated": {
        "name": "Complicated Problem",
        "description": "Requires expertise to analyze, good practices exist, cause-effect discoverable",
        "indicators": ["requires expertise", "analysis needed", "multiple factors", "specialist", "technical"],
        "cynefin": "Complicated",
    },
    "complex": {
        "name": "Complex Problem",
        "description": "Emergent behavior, cause-effect only visible in retrospect, probe-sense-respond needed",
        "indicators": ["emergent", "unpredictable", "probe", "experiment", "iterate", "adaptive", "evolving"],
        "cynefin": "Complex",
    },
    "wicked": {
        "name": "Wicked Problem",
        "description": "No stopping rule, solutions create new problems, stakeholder conflicts, contested definitions",
        "indicators": ["wicked", "no clear solution", "stakeholder conflict", "contested", "ripple effects", "unintended consequences", "political"],
        "cynefin": "Chaotic/Complex",
    },
}

# Wicked Problem Characteristics (Rittel & Webber)
WICKED_CHARACTERISTICS = {
    "no_definitive_formulation": {
        "name": "No Definitive Formulation",
        "description": "The problem cannot be definitively stated - understanding the problem IS the problem",
        "indicators": ["hard to define", "changes when examined", "different perspectives", "contested framing"],
    },
    "no_stopping_rule": {
        "name": "No Stopping Rule",
        "description": "There's no way to know when the problem is 'solved' - work continues indefinitely",
        "indicators": ["never done", "ongoing", "continuous", "no end point", "perpetual"],
    },
    "solutions_not_true_false": {
        "name": "Solutions Not True/False",
        "description": "Solutions are good/bad, not true/false - subjective judgment required",
        "indicators": ["subjective", "judgment", "trade-off", "depends on perspective", "stakeholder dependent"],
    },
    "no_immediate_test": {
        "name": "No Immediate Test",
        "description": "Cannot immediately test if a solution works - effects unfold over time",
        "indicators": ["long-term", "delayed effects", "unintended", "ripple", "downstream"],
    },
    "one_shot_operation": {
        "name": "One-Shot Operation",
        "description": "Every solution attempt counts - cannot undo and try again",
        "indicators": ["irreversible", "can't undo", "path dependent", "committed", "no going back"],
    },
    "unique": {
        "name": "Essentially Unique",
        "description": "Every wicked problem is essentially unique despite surface similarities",
        "indicators": ["unique", "unprecedented", "novel context", "no precedent", "first time"],
    },
    "symptom_of_another": {
        "name": "Symptom of Another Problem",
        "description": "The problem is a symptom of another problem - nested problems",
        "indicators": ["symptom", "root cause", "underlying", "deeper issue", "surface level"],
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


def classify_problem_definition(text: str) -> Dict:
    """
    Classify a problem by its definition clarity level.
    Returns: {"level": "well_defined"|"ill_defined"|"undefined", "confidence": 0-100, "evidence": []}
    """
    text_lower = text.lower()
    scores = {}

    for level, criteria in PROBLEM_DEFINITION_CRITERIA.items():
        matches = [ind for ind in criteria["indicators"] if ind in text_lower]
        scores[level] = len(matches)

    # Determine best match
    best_level = max(scores, key=scores.get)
    total_matches = sum(scores.values())
    confidence = (scores[best_level] / max(1, total_matches)) * 100 if total_matches > 0 else 50

    return {
        "level": best_level,
        "confidence": round(confidence, 1),
        "evidence": [ind for ind in PROBLEM_DEFINITION_CRITERIA[best_level]["indicators"] if ind in text_lower],
        "description": PROBLEM_DEFINITION_CRITERIA[best_level]["description"]
    }


def classify_problem_complexity(text: str) -> Dict:
    """
    Classify a problem by its complexity/wickedness level.
    Returns: {"level": "simple"|"complicated"|"complex"|"wicked", "confidence": 0-100, "evidence": []}
    """
    text_lower = text.lower()
    scores = {}

    for level, criteria in COMPLEXITY_WICKEDNESS_CRITERIA.items():
        matches = [ind for ind in criteria["indicators"] if ind in text_lower]
        scores[level] = len(matches)

    # Determine best match
    best_level = max(scores, key=scores.get)
    total_matches = sum(scores.values())
    confidence = (scores[best_level] / max(1, total_matches)) * 100 if total_matches > 0 else 50

    return {
        "level": best_level,
        "confidence": round(confidence, 1),
        "cynefin_domain": COMPLEXITY_WICKEDNESS_CRITERIA[best_level]["cynefin"],
        "evidence": [ind for ind in COMPLEXITY_WICKEDNESS_CRITERIA[best_level]["indicators"] if ind in text_lower],
        "description": COMPLEXITY_WICKEDNESS_CRITERIA[best_level]["description"]
    }


def assess_wickedness(text: str) -> Dict:
    """
    Assess how many wicked problem characteristics are present.
    Returns: {"wickedness_score": 0-100, "characteristics_found": [], "is_wicked": bool}
    """
    text_lower = text.lower()
    found_characteristics = []

    for char_id, char_info in WICKED_CHARACTERISTICS.items():
        matches = [ind for ind in char_info["indicators"] if ind in text_lower]
        if matches:
            found_characteristics.append({
                "id": char_id,
                "name": char_info["name"],
                "evidence": matches
            })

    # Wickedness score based on how many characteristics are present
    total_characteristics = len(WICKED_CHARACTERISTICS)
    wickedness_score = (len(found_characteristics) / total_characteristics) * 100

    return {
        "wickedness_score": round(wickedness_score, 1),
        "characteristics_found": found_characteristics,
        "characteristics_count": len(found_characteristics),
        "total_possible": total_characteristics,
        "is_wicked": len(found_characteristics) >= 3  # 3+ characteristics = wicked
    }


def get_problem_classification_matrix(text: str) -> str:
    """
    Get the full problem classification (Definition x Complexity matrix).
    Returns classification like "Ill-Defined + Complex" or "Well-Defined + Simple"
    """
    definition = classify_problem_definition(text)
    complexity = classify_problem_complexity(text)

    # Map to matrix cell
    def_label = definition["level"].replace("_", "-").title()
    comp_label = complexity["level"].title()

    return f"{def_label} + {comp_label}"


async def fetch_pws_criteria_from_neo4j() -> Dict:
    """Fetch PWS problem classification criteria from Neo4j schema."""
    driver = get_neo4j_driver()
    if not driver:
        return PROBLEM_DEFINITION_CRITERIA  # Fall back to static

    criteria = {}
    try:
        with driver.session() as session:
            # Fetch ProblemType nodes for classification criteria
            result = session.run("""
                MATCH (pt:ProblemType)
                WHERE pt.name IS NOT NULL AND pt.description IS NOT NULL
                RETURN pt.name as name, pt.description as description
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
        return PROBLEM_DEFINITION_CRITERIA
    finally:
        driver.close()

    return criteria if criteria else PROBLEM_DEFINITION_CRITERIA


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
    include_voice_scoring: bool = True,
    include_problem_classification: bool = True
) -> QualityScore:
    """
    Score an AI response against PWS methodology standards.

    Args:
        ai_response: The AI's response text
        user_message: The user's original message (for context)
        bot_id: The bot that generated the response
        phase: Current workshop phase
        include_voice_scoring: Whether to include Larry voice scoring
        include_problem_classification: Whether to classify the problem being discussed

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


def assess_conversation_quality(
    conversation_text: str,
    user_problem: str = "",
    ai_responses: List[str] = None
) -> Dict:
    """
    Comprehensive PWS quality assessment including problem classification and wickedness.

    This is the TRUE PWS measurement based on:
    1. Problem Classification (Undefined → Ill-Defined → Well-Defined)
    2. Complexity/Wickedness Assessment (Simple → Complicated → Complex → Wicked)

    Args:
        conversation_text: Full conversation or problem description
        user_problem: The user's stated problem (if separate)
        ai_responses: List of AI responses to evaluate

    Returns:
        Comprehensive assessment dict
    """
    # Analyze the problem being discussed
    combined_text = f"{user_problem} {conversation_text}"

    # 1. Problem Definition Classification
    definition_class = classify_problem_definition(combined_text)

    # 2. Complexity/Wickedness Assessment
    complexity_class = classify_problem_complexity(combined_text)

    # 3. Detailed Wickedness Analysis
    wickedness = assess_wickedness(combined_text)

    # 4. Get the matrix classification
    matrix_class = get_problem_classification_matrix(combined_text)

    # 5. Score AI responses if provided
    response_scores = []
    if ai_responses:
        for response in ai_responses:
            score = score_response(response, user_problem)
            response_scores.append(score.overall_score)

    avg_response_score = sum(response_scores) / len(response_scores) if response_scores else None

    # 6. Generate PWS recommendations based on classification
    recommendations = generate_pws_recommendations(
        definition_class["level"],
        complexity_class["level"],
        wickedness["is_wicked"]
    )

    return {
        "problem_classification": {
            "definition": definition_class,
            "complexity": complexity_class,
            "matrix_position": matrix_class,
            "wickedness": wickedness,
        },
        "cynefin_domain": complexity_class["cynefin_domain"],
        "is_wicked_problem": wickedness["is_wicked"],
        "response_quality": {
            "average_score": avg_response_score,
            "individual_scores": response_scores,
        } if response_scores else None,
        "recommendations": recommendations,
        "appropriate_approach": get_appropriate_approach(
            definition_class["level"],
            complexity_class["level"]
        ),
    }


def generate_pws_recommendations(definition_level: str, complexity_level: str, is_wicked: bool) -> List[str]:
    """Generate PWS methodology recommendations based on problem classification."""
    recommendations = []

    # Definition-based recommendations
    if definition_level == "undefined":
        recommendations.extend([
            "Use Trending to the Absurd (TTA) to explore future scenarios",
            "Apply future-back thinking to identify potential problems",
            "Focus on observation and data gathering before framing",
        ])
    elif definition_level == "ill_defined":
        recommendations.extend([
            "Apply Jobs to Be Done (JTBD) to understand underlying needs",
            "Use the Camera Test to distinguish data from interpretation",
            "Iterate on problem framing with stakeholder input",
        ])
    else:  # well_defined
        recommendations.extend([
            "Validate assumptions with the PWS Triple Validation (Real? Win? Worth?)",
            "Apply S-Curve analysis for timing decisions",
            "Use Red Teaming to stress-test your solution",
        ])

    # Complexity-based recommendations
    if is_wicked or complexity_level == "wicked":
        recommendations.extend([
            "Accept there's no 'solution' - aim for improvement",
            "Map stakeholder conflicts explicitly",
            "Use iterative probe-sense-respond approach",
            "Document assumptions - they will change",
        ])
    elif complexity_level == "complex":
        recommendations.extend([
            "Run safe-to-fail experiments",
            "Expect emergent patterns - don't over-plan",
            "Use Cynefin Complex domain practices",
        ])
    elif complexity_level == "complicated":
        recommendations.extend([
            "Engage domain experts for analysis",
            "Break down into analyzable components",
            "Use structured frameworks methodically",
        ])

    return recommendations[:6]  # Top 6 most relevant


def get_appropriate_approach(definition_level: str, complexity_level: str) -> str:
    """Get the appropriate PWS approach based on problem classification."""
    approaches = {
        ("undefined", "simple"): "Exploration with TTA, minimal risk in experimentation",
        ("undefined", "complicated"): "Expert-guided exploration, scenario planning",
        ("undefined", "complex"): "Future-back thinking, multiple scenario development",
        ("undefined", "wicked"): "Stakeholder mapping + TTA, accept ongoing evolution",

        ("ill_defined", "simple"): "JTBD analysis, quick validation cycles",
        ("ill_defined", "complicated"): "JTBD + expert analysis, structured discovery",
        ("ill_defined", "complex"): "Iterative JTBD, probe-sense-respond",
        ("ill_defined", "wicked"): "Multi-stakeholder JTBD, conflict resolution focus",

        ("well_defined", "simple"): "Direct solution development, standard practices",
        ("well_defined", "complicated"): "S-Curve positioning, expert-driven solution",
        ("well_defined", "complex"): "Agile/adaptive implementation, continuous learning",
        ("well_defined", "wicked"): "Red Team validation, anticipate second-order effects",
    }

    return approaches.get(
        (definition_level, complexity_level),
        "Apply PWS methodology iteratively, reassess classification as you learn"
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
