"""
Smart Phase Tracker using LangChain + Gemini

Intelligently tracks workshop phase progress by analyzing conversation content,
not just counting turns. Uses LLM to understand what has actually been accomplished.
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Use Google GenAI SDK (new unified SDK)
from google import genai
from google.genai import types
import os

# Initialize client
_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Import phase discovery for self-describing phases
try:
    from utils.phase_discovery import get_tracker_criteria_for_bot
    PHASE_DISCOVERY_ENABLED = True
except ImportError:
    PHASE_DISCOVERY_ENABLED = False
    get_tracker_criteria_for_bot = lambda x: None


@dataclass
class PhaseStatus:
    """Status of a workshop phase."""
    name: str
    status: str  # "completed", "in_progress", "pending"
    completion_evidence: List[str]  # What evidence shows this phase is done
    missing_elements: List[str]  # What's still needed
    confidence: float  # 0-1 confidence in this assessment


@dataclass
class WorkshopState:
    """Current state of the workshop."""
    current_phase_index: int
    current_phase_name: str
    phases: List[PhaseStatus]
    next_action: str  # What the user should do next
    progress_summary: str  # Brief summary of progress
    should_advance: bool  # Whether to auto-advance
    reasoning: str  # Why the tracker made this assessment


# Workshop phase definitions with completion criteria
WORKSHOP_PHASE_CRITERIA = {
    "scenario_analysis": {
        "phases": [
            {
                "name": "Introduction",
                "criteria": [
                    "User has stated a domain/industry to explore",
                    "A strategic question has been formulated",
                    "Time horizon has been discussed (5-15 years)"
                ],
                "key_outputs": ["domain", "strategic_question", "time_horizon"]
            },
            {
                "name": "Domain & Driving Forces",
                "criteria": [
                    "STEEP forces have been brainstormed (Social, Tech, Economic, Environmental, Political)",
                    "At least 5-8 driving forces identified",
                    "Forces categorized as predetermined vs uncertain"
                ],
                "key_outputs": ["driving_forces", "predetermined_trends", "critical_uncertainties"]
            },
            {
                "name": "Uncertainty Assessment",
                "criteria": [
                    "Two critical uncertainties selected for axes",
                    "Independence test performed on selected axes",
                    "Axes confirmed as truly independent"
                ],
                "key_outputs": ["axis_1", "axis_2", "independence_confirmed"]
            },
            {
                "name": "Scenario Matrix",
                "criteria": [
                    "2x2 matrix has been constructed",
                    "Four scenarios have been named",
                    "Each quadrant has a distinct narrative"
                ],
                "key_outputs": ["scenario_matrix", "scenario_names", "scenario_narratives"]
            },
            {
                "name": "Scenario Development",
                "criteria": [
                    "Each scenario has been fleshed out with details",
                    "Implications for the focal question explored",
                    "Early warning indicators identified"
                ],
                "key_outputs": ["detailed_scenarios", "implications", "early_warnings"]
            },
            {
                "name": "Strategic Implications",
                "criteria": [
                    "Problems worth solving identified across scenarios",
                    "Robust strategies discussed (work in multiple scenarios)",
                    "Action items or next steps defined"
                ],
                "key_outputs": ["problems_identified", "robust_strategies", "action_items"]
            }
        ]
    },
    "tta": {
        "phases": [
            {
                "name": "Introduction",
                "criteria": ["Domain selected", "User understands TTA methodology"],
                "key_outputs": ["domain"]
            },
            {
                "name": "Domain & Trends",
                "criteria": ["Current trends identified", "Trend velocity assessed"],
                "key_outputs": ["trends", "trend_analysis"]
            },
            {
                "name": "Deep Research",
                "criteria": ["Research conducted", "Data gathered"],
                "key_outputs": ["research_findings"]
            },
            {
                "name": "Absurd Extrapolation",
                "criteria": ["Trends pushed to extremes", "Absurd futures imagined"],
                "key_outputs": ["absurd_scenarios"]
            },
            {
                "name": "Problem Hunting",
                "criteria": ["Problems identified in absurd futures", "Problems prioritized"],
                "key_outputs": ["problems_found"]
            },
            {
                "name": "Opportunity Validation",
                "criteria": ["Problems validated", "Opportunities assessed"],
                "key_outputs": ["validated_opportunities"]
            },
            {
                "name": "Action Planning",
                "criteria": ["Action items defined", "Next steps clear"],
                "key_outputs": ["action_plan"]
            },
            {
                "name": "Reflection",
                "criteria": ["Workshop synthesized", "Key learnings captured"],
                "key_outputs": ["synthesis", "learnings"]
            }
        ]
    },
    "jtbd": {
        "phases": [
            {
                "name": "Introduction",
                "criteria": ["Context established", "JTBD methodology understood"],
                "key_outputs": ["context"]
            },
            {
                "name": "Struggling Moment",
                "criteria": ["Struggling moment identified", "Context of struggle understood"],
                "key_outputs": ["struggling_moment"]
            },
            {
                "name": "Functional Job",
                "criteria": ["Functional job articulated", "What user trying to accomplish"],
                "key_outputs": ["functional_job"]
            },
            {
                "name": "Emotional Job",
                "criteria": ["Emotional job identified", "How user wants to feel"],
                "key_outputs": ["emotional_job"]
            },
            {
                "name": "Social Job",
                "criteria": ["Social job identified", "How user wants to be perceived"],
                "key_outputs": ["social_job"]
            },
            {
                "name": "Competing Solutions",
                "criteria": ["Current solutions mapped", "Hiring/firing criteria understood"],
                "key_outputs": ["competing_solutions"]
            },
            {
                "name": "Job Statement",
                "criteria": ["Complete job statement formulated", "Job validated"],
                "key_outputs": ["job_statement"]
            }
        ]
    },
    # FIX: Add nested_hierarchies phases (bot added Feb 2, phases missing from tracker)
    "nested_hierarchies": {
        "phases": [
            {
                "name": "Introduction",
                "criteria": ["System context established", "Problem domain identified"],
                "key_outputs": ["context", "problem_domain"]
            },
            {
                "name": "Map the Hierarchy",
                "criteria": ["L1-L5 levels identified", "Hierarchy structure mapped", "Components at each level named"],
                "key_outputs": ["hierarchy_map", "level_components"]
            },
            {
                "name": "Find Reverse Salients",
                "criteria": ["Lagging components identified at each level", "Bottlenecks located", "Constraints analyzed"],
                "key_outputs": ["reverse_salients", "bottlenecks"]
            },
            {
                "name": "Locate Leverage Points",
                "criteria": ["High-impact intervention points identified", "Cascade effects analyzed", "Priority points selected"],
                "key_outputs": ["leverage_points", "cascade_analysis"]
            },
            {
                "name": "Design the Intervention",
                "criteria": ["Intervention strategy defined", "Action plan created", "Next steps clear"],
                "key_outputs": ["intervention_strategy", "action_plan"]
            }
        ]
    }
}

# Default generic phases for workshops without specific criteria
DEFAULT_PHASE_CRITERIA = {
    "phases": [
        {"name": "Introduction", "criteria": ["Context established"], "key_outputs": ["context"]},
        {"name": "Exploration", "criteria": ["Topic explored"], "key_outputs": ["findings"]},
        {"name": "Analysis", "criteria": ["Analysis completed"], "key_outputs": ["analysis"]},
        {"name": "Synthesis", "criteria": ["Insights synthesized"], "key_outputs": ["synthesis"]},
        {"name": "Action", "criteria": ["Next steps defined"], "key_outputs": ["actions"]}
    ]
}


PHASE_ANALYSIS_PROMPT = """You are analyzing workshop progress. Your job is to determine which phase the conversation is in.

WORKSHOP TYPE: {workshop_type}

EXACT PHASE NAMES (use these EXACTLY, do not make up new names):
{actual_phase_names}

PHASE COMPLETION CRITERIA:
{phase_criteria}

CONVERSATION HISTORY (last messages):
{conversation_history}

SYSTEM THINKS WE ARE AT: Phase {current_phase_index} ({current_phase_name})

CRITICAL RULES:
1. ONLY use phase names from the EXACT PHASE NAMES list above
2. Do NOT invent new phase names like "Problem Definition" if it's not in the list
3. The phase_assessments array MUST have exactly {num_phases} entries, one per phase
4. Each entry MUST use the EXACT phase name from the list

Respond with JSON only (no markdown):
{{
    "actual_phase_index": <0-based index>,
    "actual_phase_name": "<EXACT name from list above>",
    "phase_assessments": [
        {{
            "name": "<EXACT phase name from list>",
            "status": "completed|in_progress|pending",
            "completed_criteria": ["<what was done>"],
            "missing_criteria": ["<what's needed>"],
            "confidence": <0.0-1.0>
        }}
    ],
    "should_advance": <true|false>,
    "advance_reason": "<why>",
    "next_action": "<specific next step>",
    "progress_summary": "<1-2 sentences>",
    "reasoning": "<your analysis>"
}}"""


async def analyze_workshop_state(
    conversation_history: List[Dict[str, str]],
    workshop_type: str,
    current_phase_index: int = 0,
    phases: Optional[List[Dict]] = None
) -> WorkshopState:
    """
    Analyze conversation to determine actual workshop state.

    Args:
        conversation_history: List of {"role": "user"|"assistant", "content": "..."}
        workshop_type: Type of workshop (scenario_analysis, tta, jtbd, etc.)
        current_phase_index: What the system thinks the current phase is
        phases: Optional custom phase definitions

    Returns:
        WorkshopState with accurate phase tracking
    """
    # Get phase criteria for this workshop type
    # Priority: 1. Self-describing (from prompt module), 2. Legacy dict, 3. Default
    workshop_key = workshop_type.lower().replace(" ", "_")

    # Try auto-discovered criteria first (self-describing phases)
    criteria = None
    if PHASE_DISCOVERY_ENABLED:
        criteria = get_tracker_criteria_for_bot(workshop_key)

    # Fall back to legacy hardcoded dict
    if criteria is None:
        if workshop_key in WORKSHOP_PHASE_CRITERIA:
            criteria = WORKSHOP_PHASE_CRITERIA[workshop_key]
        else:
            criteria = DEFAULT_PHASE_CRITERIA

    # Use actual phases from session if provided, otherwise use criteria
    if phases:
        actual_phase_names = [p.get("name", f"Phase {i+1}") for i, p in enumerate(phases)]
        num_phases = len(phases)
    else:
        actual_phase_names = [p.get("name", f"Phase {i+1}") for i, p in enumerate(criteria["phases"])]
        num_phases = len(criteria["phases"])

    # Get current phase name
    current_phase_name = actual_phase_names[min(current_phase_index, num_phases - 1)] if actual_phase_names else "Unknown"

    # Format conversation history
    formatted_history = "\n".join([
        f"{'USER' if msg.get('role') == 'user' else 'ASSISTANT'}: {msg.get('content', '')[:500]}..."
        if len(msg.get('content', '')) > 500 else
        f"{'USER' if msg.get('role') == 'user' else 'ASSISTANT'}: {msg.get('content', '')}"
        for msg in conversation_history[-20:]  # Last 20 messages for context
    ])

    # Format phase criteria
    phase_criteria_str = json.dumps(criteria["phases"], indent=2)

    # Build prompt with actual phase names
    prompt = PHASE_ANALYSIS_PROMPT.format(
        workshop_type=workshop_type,
        actual_phase_names="\n".join([f"{i+1}. {name}" for i, name in enumerate(actual_phase_names)]),
        phase_criteria=phase_criteria_str,
        conversation_history=formatted_history,
        current_phase_index=current_phase_index,
        current_phase_name=current_phase_name,
        num_phases=num_phases
    )

    try:
        # Use Gemini Flash for fast analysis (new SDK pattern)
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent analysis
                max_output_tokens=2000
            )
        )

        # Parse JSON response
        result_text = response.text.strip()
        # Handle potential markdown code blocks
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()

        result = json.loads(result_text)

        # Build PhaseStatus objects
        phase_statuses = []
        for assessment in result.get("phase_assessments", []):
            phase_statuses.append(PhaseStatus(
                name=assessment.get("name", "Unknown"),
                status=assessment.get("status", "pending"),
                completion_evidence=assessment.get("completed_criteria", []),
                missing_elements=assessment.get("missing_criteria", []),
                confidence=assessment.get("confidence", 0.5)
            ))

        return WorkshopState(
            current_phase_index=result.get("actual_phase_index", current_phase_index),
            current_phase_name=result.get("actual_phase_name", "Unknown"),
            phases=phase_statuses,
            next_action=result.get("next_action", "Continue the conversation"),
            progress_summary=result.get("progress_summary", "Workshop in progress"),
            should_advance=result.get("should_advance", False),
            reasoning=result.get("reasoning", "")
        )

    except Exception as e:
        print(f"Smart phase tracker error: {e}")
        # Return safe defaults
        return WorkshopState(
            current_phase_index=current_phase_index,
            current_phase_name=criteria["phases"][min(current_phase_index, len(criteria["phases"])-1)]["name"],
            phases=[],
            next_action="Continue the conversation",
            progress_summary="Unable to analyze - continuing workshop",
            should_advance=False,
            reasoning=f"Analysis failed: {str(e)}"
        )


def format_progress_indicator(state: WorkshopState, total_phases: int) -> str:
    """
    Format a visual progress indicator for display.

    Args:
        state: Current workshop state
        total_phases: Total number of phases

    Returns:
        Formatted string with progress visualization
    """
    # Build phase indicator
    indicators = []
    for i, phase in enumerate(state.phases):
        if phase.status == "completed":
            indicators.append("✅")
        elif phase.status == "in_progress":
            indicators.append("🔵")
        else:
            indicators.append("⚪")

    # Pad if needed
    while len(indicators) < total_phases:
        indicators.append("⚪")

    phase_str = " ".join(indicators)

    return f"""📍 **Phase {state.current_phase_index + 1}/{total_phases}: {state.current_phase_name}**

{phase_str}

{state.progress_summary}

**Next:** {state.next_action}"""


async def should_show_advance_prompt(
    conversation_history: List[Dict[str, str]],
    workshop_type: str,
    current_phase_index: int
) -> Tuple[bool, str]:
    """
    Quick check if we should prompt user to advance phases.

    Returns:
        (should_prompt, reason)
    """
    state = await analyze_workshop_state(
        conversation_history,
        workshop_type,
        current_phase_index
    )

    if state.should_advance:
        return True, state.next_action

    # Check if current phase seems complete
    if state.phases:
        current = next((p for p in state.phases if p.status == "in_progress"), None)
        if current and current.confidence > 0.8 and len(current.missing_elements) == 0:
            return True, f"Phase '{current.name}' appears complete. Ready to continue?"

    return False, ""


# === Sync wrapper for non-async contexts ===

def analyze_workshop_state_sync(
    conversation_history: List[Dict[str, str]],
    workshop_type: str,
    current_phase_index: int = 0
) -> WorkshopState:
    """Synchronous wrapper for analyze_workshop_state."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        analyze_workshop_state(conversation_history, workshop_type, current_phase_index)
    )


# === Integration helpers ===

def get_smart_phase_message(state: WorkshopState, include_buttons: bool = True) -> str:
    """
    Generate a message about phase progress for the user.

    Args:
        state: Current workshop state
        include_buttons: Whether to include action button suggestions

    Returns:
        Formatted message string
    """
    msg = f"📍 **{state.current_phase_name}**\n\n"
    msg += f"{state.progress_summary}\n\n"

    if state.should_advance:
        msg += f"✅ **Ready to advance!** {state.next_action}\n"
    else:
        msg += f"**Next step:** {state.next_action}\n"

    return msg


def detect_saturation(
    conversation_history: List[Dict[str, str]],
    window: int = 6
) -> Dict[str, Any]:
    """
    Detect conversation saturation — when the user is going in circles.

    Uses lightweight heuristics (NO LLM call = zero latency cost):
    1. Repetition: Are the last N messages rehashing the same concepts?
    2. Short turns: Are user messages getting shorter (losing engagement)?
    3. Turn count: Has the conversation gone 10+ turns on the same topic?

    Args:
        conversation_history: Full message history
        window: Number of recent messages to analyze

    Returns:
        {
            "saturated": bool,
            "confidence": float (0-1),
            "signal": str ("repetition"|"fatigue"|"length"|"none"),
            "suggestion": str (what to tell the user)
        }
    """
    if len(conversation_history) < window:
        return {"saturated": False, "confidence": 0.0, "signal": "none", "suggestion": ""}

    recent = conversation_history[-window:]
    user_msgs = [m["content"] for m in recent if m.get("role") == "user"]

    if len(user_msgs) < 3:
        return {"saturated": False, "confidence": 0.0, "signal": "none", "suggestion": ""}

    # Signal 1: Word overlap between recent user messages (repetition)
    def _words(text: str) -> set:
        return set(w.lower().strip(".,!?;:") for w in text.split() if len(w) > 3)

    word_sets = [_words(m) for m in user_msgs]
    overlaps = []
    for i in range(len(word_sets) - 1):
        if word_sets[i] and word_sets[i + 1]:
            overlap = len(word_sets[i] & word_sets[i + 1]) / max(len(word_sets[i] | word_sets[i + 1]), 1)
            overlaps.append(overlap)

    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0

    # Signal 2: Shrinking message length (fatigue)
    lengths = [len(m) for m in user_msgs]
    shrinking = all(lengths[i] >= lengths[i + 1] for i in range(len(lengths) - 1)) and lengths[-1] < 50

    # Signal 3: High turn count without synthesis
    high_turns = len(conversation_history) >= 16

    # Combine signals
    if avg_overlap > 0.5:
        return {
            "saturated": True,
            "confidence": min(avg_overlap, 0.95),
            "signal": "repetition",
            "suggestion": "We seem to be circling the same ideas. Ready for me to pull it all together?"
        }

    if shrinking and high_turns:
        return {
            "saturated": True,
            "confidence": 0.7,
            "signal": "fatigue",
            "suggestion": "We've covered a lot of ground. Want me to synthesize the key insights?"
        }

    if high_turns and avg_overlap > 0.3:
        return {
            "saturated": True,
            "confidence": 0.6,
            "signal": "length",
            "suggestion": "This is a rich conversation. Good time to capture what we've built so far?"
        }

    return {"saturated": False, "confidence": avg_overlap, "signal": "none", "suggestion": ""}


def extract_phase_context(state: WorkshopState) -> Dict[str, Any]:
    """
    Extract context that should be persisted about phase progress.

    Args:
        state: Current workshop state

    Returns:
        Dictionary of context to save in session
    """
    return {
        "phase_index": state.current_phase_index,
        "phase_name": state.current_phase_name,
        "completed_phases": [p.name for p in state.phases if p.status == "completed"],
        "current_phase_evidence": (
            state.phases[state.current_phase_index].completion_evidence
            if state.phases and state.current_phase_index < len(state.phases)
            else []
        ),
        "next_action": state.next_action,
        "last_analysis": state.reasoning
    }
