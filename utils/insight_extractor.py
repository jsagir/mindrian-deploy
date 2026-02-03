"""
Insight Extractor for Recursive Intelligence

Extracts structured insights from session conversations:
- Framework applications (which frameworks were used, how)
- Cross-connections (links between concepts)
- Reframings (when user changed perspective)
- Dead-ends (abandoned approaches)
- Key insights (breakthrough moments)

Phase 3 of Recursive Intelligence implementation.
"""

import re
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class InsightType(str, Enum):
    """Types of extractable insights."""
    INSIGHT = "insight"
    FRAMEWORK_APPLICATION = "framework_application"
    CROSS_CONNECTION = "cross_connection"
    REFRAMING = "reframing"
    DEAD_END = "dead_end"


class Confidence(str, Enum):
    """Confidence levels for extracted insights."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExtractedInsight:
    """A single extracted insight from conversation."""
    insight_type: InsightType
    content: str
    confidence: Confidence
    source_agent: str
    entities_mentioned: List[str] = field(default_factory=list)
    source_turn: Optional[int] = None
    context_snippet: Optional[str] = None


@dataclass
class SessionExtraction:
    """Complete extraction from a session."""
    session_id: str
    insights: List[ExtractedInsight] = field(default_factory=list)
    frameworks_used: List[str] = field(default_factory=list)
    problem_type: Optional[str] = None
    extraction_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============================================
# Pattern-Based Extraction (Instant, No LLM)
# ============================================

# Framework mention patterns
FRAMEWORK_PATTERNS = {
    "tta": (r'\b(trending to (the )?absurd|tta|extrapolat|future trend|10x)\b', "Trending to the Absurd"),
    "jtbd": (r'\b(jobs? to be done|jtbd|hired|progress|struggling)\b', "Jobs to Be Done"),
    "scurve": (r'\b(s[- ]?curve|adoption|maturity|technology lifecycle)\b', "S-Curve Analysis"),
    "redteam": (r'\b(red ?team|devil\'?s? advocate|attack|vulnerabilit|weak point)\b', "Red Team Analysis"),
    "ackoff": (r'\b(ackoff|dikw|pyramid|data.*information.*knowledge|wisdom)\b', "Ackoff's Pyramid"),
    "scenario": (r'\b(scenario planning|future scenario|what if|alternative future)\b', "Scenario Planning"),
    "validation": (r'\b(triple validation|is it real|can we win|worth it)\b', "Triple Validation"),
    "bono": (r'\b(six (thinking )?hats?|white hat|black hat|green hat|de ?bono)\b', "Six Thinking Hats"),
}

# Insight signal patterns
INSIGHT_PATTERNS = [
    (r'\b(i (now )?realize|it\'s clear|the key is|fundamental)\b', Confidence.HIGH, "realization"),
    (r'\b(connection between|links? to|relates to|similar to)\b', Confidence.MEDIUM, "connection"),
    (r'\b(reframe|different angle|new perspective|looked at it wrong)\b', Confidence.HIGH, "reframing"),
    (r'\b(dead ?end|didn\'t work|abandon|wrong approach|backtrack)\b', Confidence.HIGH, "dead_end"),
    (r'\b(breakthrough|eureka|aha|finally|got it)\b', Confidence.HIGH, "breakthrough"),
]

# Problem type patterns
PROBLEM_TYPE_PATTERNS = {
    "strategy": r'\b(strateg|competitive|market position|differentiat)\b',
    "product": r'\b(product|feature|user experience|design|mvp)\b',
    "validation": r'\b(validat|assumption|hypothesis|test|evidence)\b',
    "innovation": r'\b(innovat|disrupt|new idea|creative|novel)\b',
    "process": r'\b(process|workflow|efficien|optimiz|streamline)\b',
    "growth": r'\b(growth|scale|expand|acquire|retention)\b',
}


def extract_from_conversation(
    history: List[dict],
    session_id: str,
    current_agent: str
) -> SessionExtraction:
    """
    Extract insights from conversation history.

    Args:
        history: List of {"role": "user"|"model", "content": str}
        session_id: Session UUID
        current_agent: Current bot ID

    Returns:
        SessionExtraction with all detected insights
    """
    extraction = SessionExtraction(session_id=session_id)

    # Combine all text for analysis
    full_text = " ".join([
        msg.get("content", "") for msg in history
    ]).lower()

    # Extract frameworks mentioned
    for framework_id, (pattern, framework_name) in FRAMEWORK_PATTERNS.items():
        if re.search(pattern, full_text, re.IGNORECASE):
            if framework_name not in extraction.frameworks_used:
                extraction.frameworks_used.append(framework_name)

                # Create framework application insight
                extraction.insights.append(ExtractedInsight(
                    insight_type=InsightType.FRAMEWORK_APPLICATION,
                    content=f"Applied {framework_name} methodology",
                    confidence=Confidence.HIGH,
                    source_agent=current_agent,
                    entities_mentioned=[framework_name],
                ))

    # Detect problem type
    for ptype, pattern in PROBLEM_TYPE_PATTERNS.items():
        if re.search(pattern, full_text, re.IGNORECASE):
            extraction.problem_type = ptype
            break

    # Extract insights from each turn
    for turn_idx, msg in enumerate(history):
        content = msg.get("content", "")
        role = msg.get("role", "")

        # Focus on user messages for insights (their realizations)
        if role == "user":
            for pattern, confidence, insight_marker in INSIGHT_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    # Determine insight type
                    if insight_marker == "dead_end":
                        itype = InsightType.DEAD_END
                    elif insight_marker == "reframing":
                        itype = InsightType.REFRAMING
                    elif insight_marker == "connection":
                        itype = InsightType.CROSS_CONNECTION
                    else:
                        itype = InsightType.INSIGHT

                    extraction.insights.append(ExtractedInsight(
                        insight_type=itype,
                        content=content[:500],  # Truncate for storage
                        confidence=confidence,
                        source_agent=current_agent,
                        source_turn=turn_idx,
                        context_snippet=content[:200],
                    ))
                    break  # One insight per message

    return extraction


def extract_dead_ends(history: List[dict], current_agent: str) -> List[ExtractedInsight]:
    """
    Specifically extract dead-end signals from conversation.

    Dead-ends are valuable for learning:
    - Which approaches don't work for which problems
    - When to suggest switching frameworks
    """
    dead_ends = []

    dead_end_patterns = [
        (r'\b(this (isn\'t|doesn\'t) work|wrong approach|dead ?end)\b', Confidence.HIGH),
        (r'\b(let\'s try something else|different approach|start over)\b', Confidence.MEDIUM),
        (r'\b(stuck|going in circles|not getting anywhere)\b', Confidence.MEDIUM),
        (r'\b(abandon|give up on|forget about) (this|that)\b', Confidence.HIGH),
    ]

    for turn_idx, msg in enumerate(history):
        if msg.get("role") != "user":
            continue

        content = msg.get("content", "")

        for pattern, confidence in dead_end_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                dead_ends.append(ExtractedInsight(
                    insight_type=InsightType.DEAD_END,
                    content=content[:500],
                    confidence=confidence,
                    source_agent=current_agent,
                    source_turn=turn_idx,
                    context_snippet=content[:200],
                ))
                break

    return dead_ends


def extract_cross_connections(history: List[dict], current_agent: str) -> List[ExtractedInsight]:
    """
    Extract cross-domain connections made during conversation.

    These are valuable for enriching the knowledge graph.
    """
    connections = []

    connection_patterns = [
        r'([\w\s]+) (?:is )?(?:like|similar to|connects to|relates to|reminds me of) ([\w\s]+)',
        r'(?:connection|link|relationship) between ([\w\s]+) and ([\w\s]+)',
        r'([\w\s]+) (?:can be applied|works for|helps with) ([\w\s]+)',
    ]

    for turn_idx, msg in enumerate(history):
        content = msg.get("content", "")

        for pattern in connection_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    entity1 = match[0].strip()[:50]
                    entity2 = match[1].strip()[:50]

                    if len(entity1) > 3 and len(entity2) > 3:  # Filter noise
                        connections.append(ExtractedInsight(
                            insight_type=InsightType.CROSS_CONNECTION,
                            content=f"Connection: {entity1} ↔ {entity2}",
                            confidence=Confidence.MEDIUM,
                            source_agent=current_agent,
                            entities_mentioned=[entity1, entity2],
                            source_turn=turn_idx,
                        ))

    return connections


# ============================================
# Supabase Storage
# ============================================

async def store_extraction(extraction: SessionExtraction) -> bool:
    """
    Store extracted insights to Supabase session_insights table.

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        from utils.storage import get_supabase_client
        import asyncio

        supabase = get_supabase_client()
        if not supabase:
            return False

        # Convert insights to table rows
        rows = []
        for insight in extraction.insights:
            rows.append({
                "session_id": extraction.session_id,
                "insight_type": insight.insight_type.value,
                "content": insight.content,
                "confidence": insight.confidence.value,
                "source_agent": insight.source_agent,
                "entities_mentioned": insight.entities_mentioned,
                "source_positions": {
                    "turn": insight.source_turn,
                    "snippet": insight.context_snippet,
                },
                "status": "pending",
            })

        if rows:
            await asyncio.to_thread(
                lambda: supabase.table("session_insights").insert(rows).execute()
            )

        return True

    except Exception as e:
        print(f"[InsightExtractor] Storage failed: {e}")
        return False


# ============================================
# Testing
# ============================================

if __name__ == "__main__":
    # Test extraction
    test_history = [
        {"role": "user", "content": "I want to validate my startup idea"},
        {"role": "model", "content": "Let's use Triple Validation. Is it Real?"},
        {"role": "user", "content": "I realize the key is that my assumption about customer willingness to pay is untested"},
        {"role": "model", "content": "Good insight! That's a critical assumption."},
        {"role": "user", "content": "This approach of using JTBD connects to what we discussed about user needs"},
        {"role": "model", "content": "Exactly, Jobs to Be Done helps understand the progress users want."},
        {"role": "user", "content": "The feature-based approach was a dead end, let's try something else"},
    ]

    extraction = extract_from_conversation(
        history=test_history,
        session_id="test-123",
        current_agent="validation"
    )

    print("Extraction Results")
    print("=" * 60)
    print(f"Session: {extraction.session_id}")
    print(f"Problem Type: {extraction.problem_type}")
    print(f"Frameworks Used: {extraction.frameworks_used}")
    print(f"\nInsights ({len(extraction.insights)}):")

    for i, insight in enumerate(extraction.insights, 1):
        print(f"\n{i}. [{insight.insight_type.value}] (confidence: {insight.confidence.value})")
        print(f"   {insight.content[:100]}...")
        if insight.entities_mentioned:
            print(f"   Entities: {insight.entities_mentioned}")
