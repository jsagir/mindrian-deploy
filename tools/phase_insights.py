"""
Phase Insights Engine

Transforms raw WorkshopState from smart_phase_tracker into user-facing guidance.
Surfaces the AI's knowledge about phase progress in a helpful, non-intrusive way.

Key Design Principles:
1. Show, don't force — Surface what the AI knows, let user decide
2. Evidence-based — Always show WHY the AI thinks something
3. Confidence-gated — Only suggest when confidence is high
4. Contextual — Guidance appears naturally, not as interruptions
5. Actionable — Every insight comes with clear options

Author: Claude Code
Date: 2026-02-01
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class InsightType(Enum):
    """Types of insights we can show."""
    NONE = "none"  # Don't show anything
    PROGRESS = "progress"  # Making progress, encouragement
    READY = "ready"  # Phase complete, ready to advance
    GAP = "gap"  # Almost there, specific gaps identified
    ENCOURAGEMENT = "encouragement"  # Early stage, keep going


@dataclass
class PhaseInsight:
    """User-facing insight about phase progress."""
    show: bool  # Whether to show this insight
    type: InsightType
    message: str  # Formatted message for display
    actions: List[str]  # Suggested action button names
    confidence: float  # How confident we are (0-1)
    evidence: List[str] = field(default_factory=list)  # What user accomplished
    gaps: List[str] = field(default_factory=list)  # What's still needed


# User preference configurations
INSIGHT_PREFERENCES = {
    "minimal": {
        "description": "Only show when phase is complete",
        "min_turns": 8,
        "confidence_threshold": 0.9,
        "show_gaps": False,
        "show_encouragement": False
    },
    "balanced": {
        "description": "Show progress and completion",
        "min_turns": 4,
        "confidence_threshold": 0.7,
        "show_gaps": True,
        "show_encouragement": True
    },
    "detailed": {
        "description": "Frequent progress updates",
        "min_turns": 2,
        "confidence_threshold": 0.5,
        "show_gaps": True,
        "show_encouragement": True
    }
}


def generate_phase_insights(
    workshop_state,  # WorkshopState from smart_phase_tracker
    turn_count: int = 0,
    last_insight_turn: int = 0,
    preference: str = "balanced"
) -> PhaseInsight:
    """
    Generate user-facing insights from workshop state.

    This is the main entry point. It takes the raw WorkshopState
    from analyze_workshop_state() and transforms it into a user-friendly
    insight message with suggested actions.

    Args:
        workshop_state: WorkshopState from smart_phase_tracker.analyze_workshop_state()
        turn_count: Current turn number in conversation
        last_insight_turn: Last turn when we showed an insight
        preference: User's insight preference ("minimal", "balanced", "detailed")

    Returns:
        PhaseInsight with guidance for the user
    """
    # Get preference settings
    prefs = INSIGHT_PREFERENCES.get(preference, INSIGHT_PREFERENCES["balanced"])

    # Check frequency limits
    if turn_count - last_insight_turn < prefs["min_turns"]:
        # Exception: Always allow if phase appears complete with high confidence
        current_phase = _get_current_phase(workshop_state)
        if not (current_phase and current_phase.confidence > 0.85 and len(current_phase.missing_elements) == 0):
            return PhaseInsight(
                show=False,
                type=InsightType.NONE,
                message="",
                actions=[],
                confidence=0
            )

    # Get current phase status
    current_phase = _get_current_phase(workshop_state)

    if not current_phase:
        return PhaseInsight(
            show=False,
            type=InsightType.NONE,
            message="",
            actions=[],
            confidence=0
        )

    # === Decision Logic Based on State ===

    # Case 1: High confidence, no missing elements → Ready to advance
    if current_phase.confidence > 0.8 and len(current_phase.missing_elements) == 0:
        evidence_summary = _format_evidence(current_phase.completion_evidence[:4])
        next_action = workshop_state.next_action if workshop_state.next_action else "Ready to continue"

        return PhaseInsight(
            show=True,
            type=InsightType.READY,
            message=f"""───── ✅ {current_phase.name} Complete ─────

**What you've covered:**
{evidence_summary}

**{next_action}**

*Ready to continue, or want to explore more?*""",
            actions=["next_phase", "explore_more"],
            confidence=current_phase.confidence,
            evidence=current_phase.completion_evidence,
            gaps=[]
        )

    # Case 2: High confidence but has missing elements → Almost there (Gap insight)
    if current_phase.confidence > prefs["confidence_threshold"] and len(current_phase.missing_elements) > 0:
        if not prefs["show_gaps"]:
            return PhaseInsight(show=False, type=InsightType.NONE, message="", actions=[], confidence=0)

        evidence_summary = _format_evidence(current_phase.completion_evidence[:3])
        gaps_summary = _format_gaps(current_phase.missing_elements[:3])

        return PhaseInsight(
            show=True,
            type=InsightType.GAP,
            message=f"""───── 📍 {current_phase.name} Progress ─────

**Covered so far:**
{evidence_summary}

**Still to explore:**
{gaps_summary}

*Would you like to dig into these, or move forward?*""",
            actions=["explore_gaps", "next_phase"],
            confidence=current_phase.confidence,
            evidence=current_phase.completion_evidence,
            gaps=current_phase.missing_elements
        )

    # Case 3: Medium confidence, some progress → Encouragement
    if current_phase.confidence > 0.4 and len(current_phase.completion_evidence) > 0:
        if not prefs["show_encouragement"]:
            return PhaseInsight(show=False, type=InsightType.NONE, message="", actions=[], confidence=0)

        evidence_summary = _format_evidence(current_phase.completion_evidence[:3])
        next_action = workshop_state.next_action if workshop_state.next_action else "Continue exploring"

        return PhaseInsight(
            show=True,
            type=InsightType.PROGRESS,
            message=f"""───── 🔵 Making Progress ─────

**You've explored:**
{evidence_summary}

**{next_action}**""",
            actions=["continue", "show_full_progress"],
            confidence=current_phase.confidence,
            evidence=current_phase.completion_evidence,
            gaps=current_phase.missing_elements
        )

    # Case 4: Low confidence or no evidence → Silent tracking
    return PhaseInsight(
        show=False,
        type=InsightType.NONE,
        message="",
        actions=[],
        confidence=current_phase.confidence if current_phase else 0
    )


def should_show_insight(
    workshop_state,
    turn_count: int,
    last_insight_turn: int,
    preference: str = "balanced"
) -> bool:
    """
    Quick check whether to generate a full insight.

    Use this for early filtering before calling generate_phase_insights()
    to avoid unnecessary processing.

    Args:
        workshop_state: WorkshopState from smart_phase_tracker
        turn_count: Current turn number
        last_insight_turn: Last turn when insight was shown
        preference: User preference setting

    Returns:
        True if we should generate an insight
    """
    prefs = INSIGHT_PREFERENCES.get(preference, INSIGHT_PREFERENCES["balanced"])

    # Always show if phase appears complete with high confidence
    current_phase = _get_current_phase(workshop_state)
    if current_phase and current_phase.confidence > 0.85 and len(current_phase.missing_elements) == 0:
        return True

    # Otherwise respect frequency limits
    return turn_count - last_insight_turn >= prefs["min_turns"]


def append_insight_to_response(
    response: str,
    insight: PhaseInsight,
    position: str = "end"
) -> str:
    """
    Append insight to bot response.

    Args:
        response: Original bot response
        insight: Generated insight
        position: Where to place ("end" or "inline")

    Returns:
        Response with insight appended
    """
    if not insight.show or not insight.message:
        return response

    if position == "end":
        return f"{response}\n\n{insight.message}"
    else:
        # Inline: Insert after first paragraph
        paragraphs = response.split("\n\n")
        if len(paragraphs) > 1:
            return f"{paragraphs[0]}\n\n{insight.message}\n\n" + "\n\n".join(paragraphs[1:])
        return f"{response}\n\n{insight.message}"


def get_insight_actions(insight: PhaseInsight) -> List[Dict[str, str]]:
    """
    Convert insight actions to Chainlit Action format.

    Args:
        insight: Generated insight

    Returns:
        List of action dicts with name and label
    """
    ACTION_LABELS = {
        "next_phase": ("Next Phase →", "Advance to the next phase"),
        "explore_more": ("🔍 Explore More", "Continue exploring this phase"),
        "explore_gaps": ("🎯 Explore Gaps", "Dig into the remaining topics"),
        "continue": ("Continue", "Keep working on current topic"),
        "show_full_progress": ("📊 Full Progress", "See detailed progress view"),
    }

    actions = []
    for action_name in insight.actions:
        if action_name in ACTION_LABELS:
            label, tooltip = ACTION_LABELS[action_name]
            actions.append({
                "name": action_name,
                "label": label,
                "tooltip": tooltip
            })

    return actions


def get_smart_sidebar_data(workshop_state, history: List = None) -> Dict[str, Any]:
    """
    Extract data for the WorkshopRoadmap sidebar component.

    Transforms WorkshopState into the props format expected by
    the WorkshopRoadmap.jsx component.

    Args:
        workshop_state: WorkshopState from smart_phase_tracker
        history: Conversation history (optional, for additional context)

    Returns:
        Dict with props for WorkshopRoadmap component
    """
    phase_context = {}
    phase_confidences = {}

    if workshop_state.phases:
        for i, phase in enumerate(workshop_state.phases):
            # Build insight text for each phase
            if phase.status == "completed":
                if phase.completion_evidence:
                    phase_context[i] = "; ".join(phase.completion_evidence[:2])
                else:
                    phase_context[i] = "Completed"
            elif phase.status == "in_progress":
                if phase.completion_evidence:
                    phase_context[i] = f"In progress: {phase.completion_evidence[0]}" if phase.completion_evidence else "In progress"
                else:
                    phase_context[i] = "Getting started..."

            # Store confidence for potential display
            phase_confidences[i] = phase.confidence

    return {
        "phaseContext": phase_context,
        "phaseConfidences": phase_confidences,
        "nextAction": workshop_state.next_action,
        "progressSummary": workshop_state.progress_summary,
        "shouldAdvance": workshop_state.should_advance
    }


# === Private Helper Functions ===

def _get_current_phase(workshop_state):
    """Get the current phase status from workshop state."""
    if not workshop_state.phases:
        return None

    # Find the in_progress phase
    for phase in workshop_state.phases:
        if phase.status == "in_progress":
            return phase

    # Fallback to index
    if workshop_state.current_phase_index < len(workshop_state.phases):
        return workshop_state.phases[workshop_state.current_phase_index]

    return None


def _format_evidence(evidence: List[str]) -> str:
    """Format evidence list as bullet points."""
    if not evidence:
        return "• (Analyzing your progress...)"
    return "\n".join([f"• {e}" for e in evidence])


def _format_gaps(gaps: List[str]) -> str:
    """Format gaps list as bullet points."""
    if not gaps:
        return "• (None identified)"
    return "\n".join([f"• {g}" for g in gaps])


# === Convenience function for integration ===

async def get_phase_insight_for_response(
    history: List[Dict],
    bot_id: str,
    current_phase: int,
    phases: List[Dict],
    turn_count: int,
    last_insight_turn: int,
    preference: str = "balanced"
) -> Optional[PhaseInsight]:
    """
    High-level function to get phase insight for a bot response.

    This handles the full flow:
    1. Analyze workshop state (calls smart_phase_tracker)
    2. Check if insight should be shown
    3. Generate and return insight

    Args:
        history: Conversation history
        bot_id: Current bot ID
        current_phase: Current phase index
        phases: List of phase definitions
        turn_count: Current turn number
        last_insight_turn: Last turn with insight
        preference: User preference

    Returns:
        PhaseInsight if one should be shown, None otherwise
    """
    try:
        from tools.smart_phase_tracker import analyze_workshop_state

        # Get the intelligent analysis
        workshop_state = await analyze_workshop_state(
            conversation_history=history,
            workshop_type=bot_id,
            current_phase_index=current_phase,
            phases=phases
        )

        # Check if we should show insight
        if not should_show_insight(workshop_state, turn_count, last_insight_turn, preference):
            return None

        # Generate the insight
        insight = generate_phase_insights(
            workshop_state=workshop_state,
            turn_count=turn_count,
            last_insight_turn=last_insight_turn,
            preference=preference
        )

        return insight if insight.show else None

    except ImportError:
        # smart_phase_tracker not available
        return None
    except Exception as e:
        print(f"Phase insight generation error: {e}")
        return None
