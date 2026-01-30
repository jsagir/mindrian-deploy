"""
Smart Phase Tracker using LangChain + Gemini

Intelligently tracks workshop phase progress by analyzing conversation content,
not just counting turns. Uses LLM to understand what has actually been accomplished.
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Use Google Generative AI directly (already configured in the project)
import google.generativeai as genai
import os

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


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


PHASE_ANALYSIS_PROMPT = """You are an expert workshop facilitator analyzing conversation progress.

WORKSHOP TYPE: {workshop_type}
WORKSHOP PHASES AND COMPLETION CRITERIA:
{phase_criteria}

CONVERSATION HISTORY:
{conversation_history}

CURRENT PHASE INDEX (system thinks): {current_phase_index}

Analyze the conversation and determine:
1. What phase are we ACTUALLY in based on conversation content?
2. For each phase, what has been completed vs what's missing?
3. Should we advance to the next phase?
4. What should happen next?

Respond with a JSON object (no markdown, just raw JSON):
{{
    "actual_phase_index": <0-based index of actual current phase>,
    "actual_phase_name": "<name of actual current phase>",
    "phase_assessments": [
        {{
            "name": "<phase name>",
            "status": "completed|in_progress|pending",
            "completed_criteria": ["<criterion that was met>", ...],
            "missing_criteria": ["<criterion still needed>", ...],
            "confidence": <0.0-1.0>
        }}
    ],
    "should_advance": <true|false>,
    "advance_reason": "<why or why not to advance>",
    "next_action": "<specific next step for user>",
    "progress_summary": "<1-2 sentence summary of where we are>",
    "reasoning": "<your analysis of the conversation state>"
}}

Be accurate - don't say something is completed unless the conversation clearly shows it was done.
If the system's current_phase_index doesn't match reality, correct it."""


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
    workshop_key = workshop_type.lower().replace(" ", "_")
    if workshop_key in WORKSHOP_PHASE_CRITERIA:
        criteria = WORKSHOP_PHASE_CRITERIA[workshop_key]
    else:
        criteria = DEFAULT_PHASE_CRITERIA

    # Format conversation history
    formatted_history = "\n".join([
        f"{'USER' if msg.get('role') == 'user' else 'ASSISTANT'}: {msg.get('content', '')[:500]}..."
        if len(msg.get('content', '')) > 500 else
        f"{'USER' if msg.get('role') == 'user' else 'ASSISTANT'}: {msg.get('content', '')}"
        for msg in conversation_history[-20:]  # Last 20 messages for context
    ])

    # Format phase criteria
    phase_criteria_str = json.dumps(criteria["phases"], indent=2)

    # Build prompt
    prompt = PHASE_ANALYSIS_PROMPT.format(
        workshop_type=workshop_type,
        phase_criteria=phase_criteria_str,
        conversation_history=formatted_history,
        current_phase_index=current_phase_index
    )

    try:
        # Use Gemini Flash for fast analysis
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
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
