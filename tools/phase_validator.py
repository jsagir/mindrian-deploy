"""
Phase Validator - LangExtract-based phase completion checking
=============================================================

Uses regex pattern extraction to validate if user has completed
the deliverables for a workshop phase before advancing.
"""

import re
from typing import Dict, List, Tuple, Any


def validate_phase_completion(
    phase_config: dict,
    conversation_history: List[dict],
    bot_id: str = "scenario"
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Validate if user has completed current phase deliverables.

    Uses LangExtract-style regex patterns to extract deliverables
    from conversation history.

    Args:
        phase_config: Phase definition with deliverables and extraction_patterns
        conversation_history: List of message dicts with 'role' and 'content'
        bot_id: Current bot identifier

    Returns:
        Tuple of (is_complete, confidence_score, extracted_deliverables)
    """
    # Combine recent conversation into searchable text
    recent_messages = conversation_history[-12:]  # Last 12 messages
    conversation_text = "\n".join([
        f"{m.get('role', 'user')}: {m.get('content', '')}"
        for m in recent_messages
        if m.get('content')
    ])

    deliverables = phase_config.get("deliverables", {})
    patterns = phase_config.get("extraction_patterns", {})
    threshold = phase_config.get("completion_threshold", 0.7)

    extracted = {}
    found_count = 0
    total_deliverables = len(deliverables)

    if total_deliverables == 0:
        return True, 1.0, {}

    # Try to extract each deliverable using patterns
    for key, description in deliverables.items():
        pattern = patterns.get(key)
        value_found = False

        if pattern:
            try:
                matches = re.findall(pattern, conversation_text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Take the most recent (last) match
                    match = matches[-1]
                    # Handle tuple matches from groups
                    if isinstance(match, tuple):
                        match = next((m for m in match if m), "")
                    if match and len(match.strip()) > 2:
                        extracted[key] = match.strip()
                        found_count += 1
                        value_found = True
            except re.error:
                pass  # Invalid pattern, skip

        # Fallback: keyword presence check
        if not value_found:
            keywords = description.lower().split()[:4]
            keyword_matches = sum(1 for kw in keywords if kw in conversation_text.lower())
            if keyword_matches >= 2:
                extracted[key] = "[discussed but not explicitly stated]"
                found_count += 0.5

    # Calculate completion score
    score = found_count / total_deliverables
    is_complete = score >= threshold

    return is_complete, score, extracted


def get_missing_deliverables(
    phase_config: dict,
    extracted: Dict[str, Any]
) -> List[str]:
    """
    Get list of missing deliverables with helpful descriptions.

    Args:
        phase_config: Phase definition with deliverables
        extracted: Dict of already extracted deliverables

    Returns:
        List of formatted missing deliverable strings
    """
    deliverables = phase_config.get("deliverables", {})
    missing = []

    for key, description in deliverables.items():
        if key not in extracted:
            clean_key = key.replace("_", " ").title()
            missing.append(f"- **{clean_key}**: {description}")
        elif extracted[key] == "[discussed but not explicitly stated]":
            clean_key = key.replace("_", " ").title()
            missing.append(f"- **{clean_key}**: Please state this more explicitly")

    return missing


def generate_completion_guidance(
    phase_config: dict,
    score: float,
    missing: List[str]
) -> str:
    """
    Generate helpful guidance message based on completion status.

    Args:
        phase_config: Phase definition
        score: Completion score (0.0 to 1.0)
        missing: List of missing deliverable strings

    Returns:
        Formatted guidance message
    """
    phase_name = phase_config.get("name", "this phase")

    if score >= 0.9:
        return f"You've covered everything needed for {phase_name}. Ready to advance!"

    elif score >= 0.7:
        guidance = f"Almost there with {phase_name}! Consider addressing:\n"
        guidance += "\n".join(missing[:2])
        return guidance

    elif score >= 0.4:
        guidance = f"Good progress on {phase_name}. Let's make sure we cover:\n"
        guidance += "\n".join(missing[:4])
        return guidance

    else:
        # Low completion - show full instructions
        instructions = phase_config.get("instructions", [])
        guidance = f"Let's work through {phase_name} step by step:\n"
        guidance += "\n".join([f"- {inst}" for inst in instructions])
        return guidance


def summarize_extracted_deliverables(
    extracted: Dict[str, Any],
    phase_config: dict
) -> str:
    """
    Create a summary of what was extracted/completed in a phase.

    Args:
        extracted: Dict of extracted deliverables
        phase_config: Phase definition

    Returns:
        Formatted summary string
    """
    if not extracted:
        return ""

    phase_name = phase_config.get("name", "Phase")
    lines = [f"**{phase_name} - What you established:**"]

    for key, value in extracted.items():
        if value and value != "[discussed but not explicitly stated]":
            clean_key = key.replace("_", " ").title()
            # Truncate long values
            if len(str(value)) > 100:
                display_value = str(value)[:100] + "..."
            else:
                display_value = str(value)
            lines.append(f"- {clean_key}: {display_value}")

    return "\n".join(lines) if len(lines) > 1 else ""


__all__ = [
    "validate_phase_completion",
    "get_missing_deliverables",
    "generate_completion_guidance",
    "summarize_extracted_deliverables"
]
