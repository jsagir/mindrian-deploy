"""
Reaction Classifier for Recursive Intelligence

Classifies user messages into signal types for learning:
- positive: engagement, agreement, thanks, breakthrough moments
- negative: frustration, confusion, disagreement, stuck signals
- redirect: wants to change topic, switch agent, or try different approach
- neutral: continuing conversation normally

Phase 2 of Recursive Intelligence implementation.
Uses pattern matching for instant classification (no API calls).
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ReactionSignal:
    """Classified reaction from user message."""
    signal_type: str  # positive | negative | redirect | neutral
    confidence: float  # 0.0 - 1.0
    indicators: list[str]  # What patterns triggered this classification
    suggested_action: Optional[str] = None  # Hint for system (e.g., "suggest_switch")


# ============================================
# Pattern Definitions
# ============================================

POSITIVE_PATTERNS = [
    # Breakthrough/insight signals
    (r'\b(aha|eureka|got it|i see|makes sense|now i understand)\b', 0.9, 'insight'),
    (r'\b(brilliant|excellent|perfect|exactly|yes!|wow)\b', 0.85, 'enthusiasm'),
    (r'\b(thank you|thanks|appreciate|helpful|great help)\b', 0.8, 'gratitude'),
    (r'\b(this is great|love this|amazing|awesome)\b', 0.85, 'appreciation'),
    (r'\b(i like|good point|fair point|interesting)\b', 0.7, 'agreement'),
    (r'\b(let\'s do|let\'s try|sounds good|i\'m in)\b', 0.75, 'engagement'),
    (r'\b(that helps|cleared up|now i get)\b', 0.8, 'clarity'),
    (r'!{2,}', 0.6, 'excitement'),  # Multiple exclamation marks
]

NEGATIVE_PATTERNS = [
    # Frustration signals
    (r'\b(confused|don\'t understand|lost|stuck|frustrat)\b', 0.85, 'confusion'),
    (r'\b(not helpful|doesn\'t help|this isn\'t working)\b', 0.9, 'frustration'),
    (r'\b(wrong|incorrect|that\'s not|no that\'s)\b', 0.75, 'disagreement'),
    (r'\b(waste of time|going nowhere|circles|repeating)\b', 0.9, 'frustration'),
    (r'\b(too (complex|complicated|abstract|vague))\b', 0.8, 'overwhelm'),
    (r'\b(i give up|forget it|never ?mind)\b', 0.95, 'abandonment'),
    (r'\b(what\?|huh\?|i don\'t get)\b', 0.7, 'confusion'),
    (r'\b(already (said|told|tried|asked))\b', 0.8, 'repetition_frustration'),
    (r'\?{2,}', 0.6, 'confusion'),  # Multiple question marks
]

REDIRECT_PATTERNS = [
    # Topic change signals
    (r'\b(let\'s (talk about|try|switch|move to))\b', 0.85, 'topic_change'),
    (r'\b(different (approach|angle|way|method))\b', 0.8, 'approach_change'),
    (r'\b(can we (try|do|use|switch))\b', 0.75, 'request_change'),
    (r'\b(what about|how about|instead)\b', 0.7, 'alternative'),
    (r'\b(switch to|use|try) (tta|jtbd|red ?team|ackoff|scurve|scenario)\b', 0.95, 'agent_switch'),
    (r'\b(different (bot|agent|expert|tool))\b', 0.9, 'agent_switch'),
    (r'\b(back to|return to|go back)\b', 0.75, 'backtrack'),
    (r'\b(start over|restart|begin again|fresh start)\b', 0.85, 'reset'),
    (r'\b(skip|move on|next)\b', 0.7, 'advance'),
]


# ============================================
# Classification Logic
# ============================================

def classify_reaction(message: str) -> ReactionSignal:
    """
    Classify a user message into a reaction signal.

    Args:
        message: User's message text

    Returns:
        ReactionSignal with type, confidence, and indicators
    """
    message_lower = message.lower().strip()

    # Skip very short messages (likely just acknowledgments)
    if len(message_lower) < 3:
        return ReactionSignal(
            signal_type="neutral",
            confidence=0.5,
            indicators=["too_short"]
        )

    # Collect all matches
    positive_score, positive_indicators = _score_patterns(message_lower, POSITIVE_PATTERNS)
    negative_score, negative_indicators = _score_patterns(message_lower, NEGATIVE_PATTERNS)
    redirect_score, redirect_indicators = _score_patterns(message_lower, REDIRECT_PATTERNS)

    # Determine dominant signal
    scores = {
        "positive": (positive_score, positive_indicators),
        "negative": (negative_score, negative_indicators),
        "redirect": (redirect_score, redirect_indicators),
    }

    # Find highest score
    max_type = max(scores, key=lambda k: scores[k][0])
    max_score, max_indicators = scores[max_type]

    # If no strong signal, classify as neutral
    if max_score < 0.5:
        return ReactionSignal(
            signal_type="neutral",
            confidence=0.6,
            indicators=["no_strong_signal"]
        )

    # Build result
    result = ReactionSignal(
        signal_type=max_type,
        confidence=min(max_score, 1.0),
        indicators=max_indicators
    )

    # Add suggested actions for certain signals
    if max_type == "negative" and max_score > 0.8:
        if "abandonment" in max_indicators or "frustration" in max_indicators:
            result.suggested_action = "offer_help_or_switch"
        elif "confusion" in max_indicators:
            result.suggested_action = "simplify_explanation"

    if max_type == "redirect":
        if "agent_switch" in max_indicators:
            result.suggested_action = "suggest_agent_switch"
        elif "reset" in max_indicators:
            result.suggested_action = "offer_reset"

    return result


def _score_patterns(text: str, patterns: list) -> Tuple[float, list[str]]:
    """
    Score text against a list of patterns.

    Returns:
        Tuple of (max_score, list_of_matched_indicators)
    """
    max_score = 0.0
    indicators = []

    for pattern, weight, indicator in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            max_score = max(max_score, weight)
            indicators.append(indicator)

    # Boost score slightly if multiple indicators match
    if len(indicators) > 1:
        max_score = min(max_score + 0.1 * (len(indicators) - 1), 1.0)

    return max_score, indicators


# ============================================
# Convenience Functions
# ============================================

def get_signal_type(message: str) -> str:
    """Quick classification - returns just the signal type."""
    return classify_reaction(message).signal_type


def is_negative_signal(message: str, threshold: float = 0.7) -> bool:
    """Check if message has negative signal above threshold."""
    reaction = classify_reaction(message)
    return reaction.signal_type == "negative" and reaction.confidence >= threshold


def is_redirect_signal(message: str, threshold: float = 0.7) -> bool:
    """Check if message has redirect signal above threshold."""
    reaction = classify_reaction(message)
    return reaction.signal_type == "redirect" and reaction.confidence >= threshold


def should_suggest_switch(message: str) -> bool:
    """Check if user is signaling they want to switch agents."""
    reaction = classify_reaction(message)
    return (
        reaction.signal_type == "redirect" and
        reaction.suggested_action == "suggest_agent_switch"
    )


# ============================================
# Debug/Testing
# ============================================

def analyze_message(message: str) -> dict:
    """
    Full analysis of a message for debugging.
    Returns all scores and the final classification.
    """
    message_lower = message.lower().strip()

    positive_score, positive_indicators = _score_patterns(message_lower, POSITIVE_PATTERNS)
    negative_score, negative_indicators = _score_patterns(message_lower, NEGATIVE_PATTERNS)
    redirect_score, redirect_indicators = _score_patterns(message_lower, REDIRECT_PATTERNS)

    reaction = classify_reaction(message)

    return {
        "message": message,
        "classification": {
            "signal_type": reaction.signal_type,
            "confidence": reaction.confidence,
            "indicators": reaction.indicators,
            "suggested_action": reaction.suggested_action,
        },
        "all_scores": {
            "positive": {"score": positive_score, "indicators": positive_indicators},
            "negative": {"score": negative_score, "indicators": negative_indicators},
            "redirect": {"score": redirect_score, "indicators": redirect_indicators},
        }
    }


if __name__ == "__main__":
    # Test cases
    test_messages = [
        "Aha! Now I understand what you mean!",
        "This is really confusing, I don't get it",
        "Can we try a different approach?",
        "Let's switch to the Red Team bot",
        "Thanks, that was helpful",
        "I've already told you this twice",
        "Interesting point, let me think about that",
        "Ok",
        "What about using scenario planning instead?",
        "I give up, this isn't working",
    ]

    print("Reaction Classifier Test Results")
    print("=" * 60)

    for msg in test_messages:
        result = analyze_message(msg)
        print(f"\nMessage: \"{msg}\"")
        print(f"  → {result['classification']['signal_type'].upper()} "
              f"(confidence: {result['classification']['confidence']:.2f})")
        print(f"    Indicators: {result['classification']['indicators']}")
        if result['classification']['suggested_action']:
            print(f"    Suggested: {result['classification']['suggested_action']}")
