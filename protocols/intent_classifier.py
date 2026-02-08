"""
Intent Classifier - Wave 4: Auto-Orchestration
Classifies user intent to select appropriate multi-agent workflows.

Two-stage classification:
1. Fast pattern matching (< 5ms)
2. Optional LLM refinement for low-confidence cases
"""

import re
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


class WorkflowType(Enum):
    """Primary workflow categories."""
    TECH_TO_OPPORTUNITY = "tech_to_opportunity"  # "I have technology X..."
    EXPLORE = "explore"                           # "Tell me about Y..."
    DOCUMENT_REVIEW = "document_review"           # "Review this document..."
    STRESS_TEST = "stress_test"                   # "Challenge this idea..."
    VALIDATE = "validate"                         # "Is this real?"
    FULL_ANALYSIS = "full_analysis"               # "Full analysis of..."
    QUICK_PULSE = "quick_pulse"                   # Fast multi-perspective
    CUSTOM = "custom"                             # Manual agent selection


@dataclass
class IntentSignal:
    """Signals extracted from user message."""
    has_technology: bool = False
    has_opportunity_request: bool = False
    has_document: bool = False
    has_challenge_language: bool = False
    has_validation_need: bool = False
    has_exploration_intent: bool = False
    has_full_analysis_request: bool = False
    entities_mentioned: List[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    """Full classification output."""
    workflow_type: WorkflowType
    cynefin_domain: str  # clear, complicated, complex, chaotic
    pws_stage: str       # un-defined, ill-defined, well-defined
    recommended_agents: List[str]
    signals: IntentSignal
    reasoning: str
    confidence: float


# ═══════════════════════════════════════════════════════════════════════════════
# Pattern Definitions
# ═══════════════════════════════════════════════════════════════════════════════

TECH_PATTERNS = [
    r"i have\s+(?:a |an )?(?:technology|tech|invention|patent|solution|method)",
    r"we (?:built|developed|created|invented|have)",
    r"our (?:technology|tech|product|solution|company has)",
    r"proprietary (?:technology|tech|method|process)",
    r"my (?:technology|invention|innovation)",
]

OPPORTUNITY_PATTERNS = [
    r"find\s+(?:the |a )?(?:business |market )?opportunit(?:y|ies)",
    r"business potential",
    r"market for",
    r"commercialize",
    r"monetize",
    r"find (?:customers|markets|applications|uses)",
    r"business case",
    r"go[- ]to[- ]market",
    r"find the breakthrough",
    r"breakthrough",
    r"business opportunit(?:y|ies)",
    r"market opportunit(?:y|ies)",
]

CHALLENGE_PATTERNS = [
    r"stress[- ]?test",
    r"challenge",
    r"poke holes",
    r"devil'?s advocate",
    r"what (?:could|might) go wrong",
    r"critique",
    r"red team",
    r"find weaknesses",
    r"attack this",
]

EXPLORE_PATTERNS = [
    r"explore",
    r"learn about",
    r"understand",
    r"tell me about",
    r"what is",
    r"how does",
    r"help me think",
    r"brainstorm",
]

VALIDATE_PATTERNS = [
    r"is this (?:real|true|valid|accurate)",
    r"validate",
    r"verify",
    r"check if",
    r"evidence for",
    r"prove",
    r"data on",
]

FULL_ANALYSIS_PATTERNS = [
    r"full analysis",
    r"comprehensive",
    r"all agents",
    r"deep dive",
    r"thorough",
    r"complete analysis",
    r"analyze from all angles",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Classification Logic
# ═══════════════════════════════════════════════════════════════════════════════

def classify_intent(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    has_document: bool = False,
) -> ClassificationResult:
    """
    Two-stage intent classification.

    Stage 1: Fast pattern matching (< 5ms)
    Stage 2: LLM refinement if confidence < 0.7 (optional)

    Args:
        message: User input text
        context: Optional session context (current bot, phase, etc.)
        has_document: Whether a document is attached

    Returns:
        ClassificationResult with workflow type and recommended agents
    """
    context = context or {}
    signals = _extract_signals(message, has_document)

    # Stage 1: Pattern-based classification
    workflow, agents, confidence = _pattern_classify(signals)

    # Determine Cynefin domain and PWS stage
    cynefin = _infer_cynefin(signals)
    pws_stage = _infer_pws_stage(signals)

    # Generate reasoning
    reasoning = _generate_reasoning(workflow, signals)

    return ClassificationResult(
        workflow_type=workflow,
        cynefin_domain=cynefin,
        pws_stage=pws_stage,
        recommended_agents=agents,
        signals=signals,
        reasoning=reasoning,
        confidence=confidence,
    )


def _extract_signals(message: str, has_document: bool = False) -> IntentSignal:
    """Extract intent signals from message."""
    message_lower = message.lower()

    return IntentSignal(
        has_technology=any(re.search(p, message_lower) for p in TECH_PATTERNS),
        has_opportunity_request=any(re.search(p, message_lower) for p in OPPORTUNITY_PATTERNS),
        has_document=has_document or _has_document_mention(message_lower),
        has_challenge_language=any(re.search(p, message_lower) for p in CHALLENGE_PATTERNS),
        has_validation_need=any(re.search(p, message_lower) for p in VALIDATE_PATTERNS),
        has_exploration_intent=any(re.search(p, message_lower) for p in EXPLORE_PATTERNS),
        has_full_analysis_request=any(re.search(p, message_lower) for p in FULL_ANALYSIS_PATTERNS),
        entities_mentioned=_extract_entities(message),
    )


def _has_document_mention(message: str) -> bool:
    """Check if message mentions a document."""
    doc_patterns = [
        r"this document",
        r"attached",
        r"uploaded",
        r"my paper",
        r"the file",
        r"this pdf",
        r"this presentation",
    ]
    return any(re.search(p, message) for p in doc_patterns)


def _extract_entities(message: str) -> List[str]:
    """Extract potential entity names from message."""
    entities = []

    # Look for quoted terms
    quoted = re.findall(r'"([^"]+)"', message)
    entities.extend(quoted)

    # Look for capitalized phrases (potential proper nouns)
    caps = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', message)
    entities.extend([c for c in caps if len(c) > 3])

    return entities[:10]  # Limit to 10 entities


def _pattern_classify(signals: IntentSignal) -> tuple:
    """
    Pattern-based classification.

    Returns: (workflow_type, agents, confidence)
    """
    # Full analysis request (highest priority)
    if signals.has_full_analysis_request:
        return (
            WorkflowType.FULL_ANALYSIS,
            ["tta", "jtbd", "redteam", "ackoff", "research"],
            0.9
        )

    # Tech to Opportunity
    if signals.has_technology and signals.has_opportunity_request:
        return (
            WorkflowType.TECH_TO_OPPORTUNITY,
            ["tta", "jtbd", "redteam", "ackoff"],
            0.9
        )

    # Just Opportunity (no specific tech mentioned)
    if signals.has_opportunity_request:
        return (
            WorkflowType.TECH_TO_OPPORTUNITY,
            ["tta", "jtbd", "redteam"],
            0.75
        )

    # Document Review
    if signals.has_document:
        return (
            WorkflowType.DOCUMENT_REVIEW,
            ["pws_grading", "redteam", "ackoff"],
            0.85
        )

    # Stress Test / Challenge
    if signals.has_challenge_language:
        return (
            WorkflowType.STRESS_TEST,
            ["redteam", "ackoff"],
            0.85
        )

    # Validation
    if signals.has_validation_need:
        return (
            WorkflowType.VALIDATE,
            ["research", "ackoff", "validation"],
            0.8
        )

    # Exploration
    if signals.has_exploration_intent:
        return (
            WorkflowType.EXPLORE,
            ["tta", "research", "larry"],
            0.7
        )

    # Default: Custom (let Larry handle)
    return (
        WorkflowType.CUSTOM,
        ["larry"],
        0.5
    )


def _infer_cynefin(signals: IntentSignal) -> str:
    """Infer Cynefin domain from signals."""
    if signals.has_exploration_intent and not signals.has_technology:
        return "complex"  # Uncertain, needs probing
    elif signals.has_technology and signals.has_opportunity_request:
        return "complicated"  # Known solution, need expert analysis
    elif signals.has_validation_need:
        return "complicated"  # Data-driven decision
    else:
        return "complex"  # Default to complex for safety


def _infer_pws_stage(signals: IntentSignal) -> str:
    """Infer PWS problem stage from signals."""
    if signals.has_exploration_intent and not signals.has_technology:
        return "un-defined"  # Still exploring
    elif signals.has_technology:
        return "ill-defined"  # Have solution, refining problem
    elif signals.has_validation_need:
        return "well-defined"  # Testing specific hypothesis
    else:
        return "un-defined"


def _generate_reasoning(workflow: WorkflowType, signals: IntentSignal) -> str:
    """Generate human-readable reasoning for classification."""
    parts = []

    if signals.has_technology:
        parts.append("User has a technology/solution")
    if signals.has_opportunity_request:
        parts.append("looking for business opportunities")
    if signals.has_document:
        parts.append("with a document to review")
    if signals.has_challenge_language:
        parts.append("wants to stress test assumptions")
    if signals.has_validation_need:
        parts.append("needs validation/evidence")
    if signals.has_exploration_intent:
        parts.append("exploring ideas")
    if signals.has_full_analysis_request:
        parts.append("requesting comprehensive analysis")

    if parts:
        return f"Detected: {', '.join(parts)}. Workflow: {workflow.value}"
    return f"Default workflow: {workflow.value}"


# ═══════════════════════════════════════════════════════════════════════════════
# Quick Detection for Message Handler
# ═══════════════════════════════════════════════════════════════════════════════

def should_auto_orchestrate(message: str, min_confidence: float = 0.75) -> bool:
    """
    Quick check if message should trigger auto-orchestration.

    Use this for lightweight detection before full classification.
    """
    message_lower = message.lower()

    # High-confidence triggers
    high_triggers = [
        r"find (?:the )?breakthrough",
        r"full analysis",
        r"find (?:business |market )?opportunities?",
        r"analyze from all angles",
        r"what should i do with",
        r"help me commercialize",
    ]

    for pattern in high_triggers:
        if re.search(pattern, message_lower):
            return True

    return False


def get_workflow_description(workflow_type: WorkflowType) -> str:
    """Get human-readable description of a workflow."""
    descriptions = {
        WorkflowType.TECH_TO_OPPORTUNITY: "Finding business opportunities for your technology",
        WorkflowType.EXPLORE: "Exploring the topic from multiple perspectives",
        WorkflowType.DOCUMENT_REVIEW: "Analyzing and grading the document",
        WorkflowType.STRESS_TEST: "Challenging assumptions and finding weaknesses",
        WorkflowType.VALIDATE: "Validating claims with evidence",
        WorkflowType.FULL_ANALYSIS: "Comprehensive multi-agent analysis",
        WorkflowType.QUICK_PULSE: "Quick multi-perspective check",
        WorkflowType.CUSTOM: "Custom workflow",
    }
    return descriptions.get(workflow_type, "Analysis workflow")
