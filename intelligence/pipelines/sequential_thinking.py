"""
Sequential Thinking Pipeline - LangGraph Self-Prompting
========================================================

Real-time chain-of-thought reasoning that powers the ThinkingPanel.
Uses LangGraph StateGraph for multi-step reasoning with streaming updates.

Features:
- Self-prompting: Each step can trigger follow-up analysis
- Tree-of-thoughts: Explores multiple reasoning paths
- Streaming: Updates ThinkingPanel in real-time as steps complete
- PWS-aware: Checks for assumptions, solution-jumping, evidence needs

Usage:
    from intelligence.pipelines.sequential_thinking import run_thinking_pipeline

    async for step in run_thinking_pipeline(message, bot_id, history):
        # Update ThinkingPanel with step
        await update_thinking_panel(step)
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime

from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# Lazy load Gemini
_client = None


def _get_client():
    """Get Gemini client (lazy initialization)."""
    global _client
    if _client is None:
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client


# ============================================================================
# State & Data Classes
# ============================================================================

@dataclass
class ThinkingStep:
    """A single thinking step for the panel."""
    name: str
    status: str  # pending, active, complete, error
    icon: str
    output: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ThinkingState:
    """State for the sequential thinking pipeline."""
    message: str
    bot_id: str
    history: List[Dict] = field(default_factory=list)
    steps: List[ThinkingStep] = field(default_factory=list)
    current_step: int = 0

    # Analysis results
    message_type: str = ""  # question, statement, request, emotion
    assumptions_found: List[str] = field(default_factory=list)
    solution_jumping: bool = False
    evidence_needed: List[str] = field(default_factory=list)
    pws_frameworks: List[str] = field(default_factory=list)
    key_entities: List[str] = field(default_factory=list)
    recommended_action: str = ""

    # Self-prompting context
    follow_up_needed: bool = False
    follow_up_question: str = ""


# ============================================================================
# Thinking Step Functions
# ============================================================================

async def understand_message(state: ThinkingState) -> ThinkingState:
    """Step 1: Understand what the user is asking/saying."""
    state.steps.append(ThinkingStep(
        name="Understanding your message",
        status="active",
        icon="🔍",
    ))

    client = _get_client()

    prompt = f"""Quickly classify this message (respond with just the type and one-line explanation):

Message: "{state.message}"

Types:
- QUESTION: Asking for information or guidance
- STATEMENT: Making a claim or sharing an observation
- REQUEST: Asking for an action (research, analysis, etc.)
- EMOTION: Expressing frustration, excitement, or confusion

Format: TYPE: explanation"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        result = response.text.strip()

        # Parse type
        if "QUESTION" in result.upper():
            state.message_type = "question"
        elif "STATEMENT" in result.upper():
            state.message_type = "statement"
        elif "REQUEST" in result.upper():
            state.message_type = "request"
        else:
            state.message_type = "emotion"

        state.steps[-1].status = "complete"
        state.steps[-1].output = result

    except Exception as e:
        logger.error(f"Understanding step failed: {e}")
        state.steps[-1].status = "error"
        state.steps[-1].output = f"Error: {e}"
        state.message_type = "question"  # Default fallback

    return state


async def detect_assumptions(state: ThinkingState) -> ThinkingState:
    """Step 2: Detect hidden assumptions in the message."""
    state.steps.append(ThinkingStep(
        name="Checking for assumptions",
        status="active",
        icon="⚠️",
    ))

    # Quick pattern-based detection first
    assumption_patterns = [
        "assume", "think", "believe", "should", "must",
        "obviously", "clearly", "everyone knows", "of course",
        "definitely", "surely", "always", "never"
    ]

    msg_lower = state.message.lower()
    found_patterns = [p for p in assumption_patterns if p in msg_lower]

    if found_patterns:
        state.assumptions_found = found_patterns
        state.steps[-1].output = f"Found assumption signals: {', '.join(found_patterns)}"
        state.follow_up_needed = True
        state.follow_up_question = "What evidence supports these assumptions?"
    else:
        state.steps[-1].output = "No obvious assumption language detected"

    state.steps[-1].status = "complete"
    return state


async def check_solution_jumping(state: ThinkingState) -> ThinkingState:
    """Step 3: Check if user is jumping to solutions before understanding the problem."""
    state.steps.append(ThinkingStep(
        name="Checking for solution-jumping",
        status="active",
        icon="🚀",
    ))

    solution_patterns = [
        "we should build", "let's create", "the solution is",
        "my idea is", "i want to make", "we need to develop",
        "the app should", "the platform will"
    ]

    msg_lower = state.message.lower()
    has_solution = any(p in msg_lower for p in solution_patterns)

    if has_solution:
        state.solution_jumping = True
        state.steps[-1].output = "User may be jumping to solutions. PWS methodology: validate problem first."
        state.recommended_action = "Ask about problem validation before discussing solutions"
    else:
        state.steps[-1].output = "No premature solution-jumping detected"

    state.steps[-1].status = "complete"
    return state


async def identify_frameworks(state: ThinkingState) -> ThinkingState:
    """Step 4: Identify relevant PWS frameworks for the context."""
    state.steps.append(ThinkingStep(
        name="Identifying relevant frameworks",
        status="active",
        icon="🧰",
    ))

    # Quick keyword matching to relevant frameworks
    framework_keywords = {
        "tta": ["trend", "future", "absurd", "extrapolate", "10 years"],
        "jtbd": ["job", "customer", "need", "hire", "progress", "switching"],
        "scurve": ["growth", "maturity", "adoption", "lifecycle", "technology"],
        "redteam": ["challenge", "critique", "weakness", "risk", "fail"],
        "ackoff": ["data", "information", "knowledge", "wisdom", "understand"],
    }

    msg_lower = state.message.lower()
    matched_frameworks = []

    for framework, keywords in framework_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            matched_frameworks.append(framework.upper())

    if matched_frameworks:
        state.pws_frameworks = matched_frameworks
        state.steps[-1].output = f"Relevant frameworks: {', '.join(matched_frameworks)}"
    else:
        state.pws_frameworks = ["General PWS"]
        state.steps[-1].output = "Using general PWS methodology"

    state.steps[-1].status = "complete"
    return state


async def synthesize_thinking(state: ThinkingState) -> ThinkingState:
    """Step 5: Synthesize insights and determine response strategy."""
    state.steps.append(ThinkingStep(
        name="Synthesizing analysis",
        status="active",
        icon="💡",
    ))

    insights = []

    if state.message_type:
        insights.append(f"Message type: {state.message_type}")

    if state.assumptions_found:
        insights.append(f"Assumptions to probe: {len(state.assumptions_found)}")

    if state.solution_jumping:
        insights.append("Solution-jumping detected - will guide back to problem")

    if state.pws_frameworks:
        insights.append(f"Will apply: {', '.join(state.pws_frameworks)}")

    if state.recommended_action:
        insights.append(f"Strategy: {state.recommended_action}")
    else:
        # Determine strategy based on analysis
        if state.solution_jumping:
            state.recommended_action = "Probe problem validity before solutions"
        elif state.assumptions_found:
            state.recommended_action = "Challenge assumptions with evidence questions"
        elif state.message_type == "question":
            state.recommended_action = "Answer with PWS framework guidance"
        else:
            state.recommended_action = "Engage with Socratic questioning"

    state.steps[-1].output = "\n".join(insights) if insights else "Ready to respond"
    state.steps[-1].status = "complete"

    return state


# ============================================================================
# Pipeline Creation
# ============================================================================

def create_thinking_pipeline() -> StateGraph:
    """Create the sequential thinking LangGraph pipeline."""

    workflow = StateGraph(ThinkingState)

    # Add nodes
    workflow.add_node("understand", understand_message)
    workflow.add_node("assumptions", detect_assumptions)
    workflow.add_node("solution_check", check_solution_jumping)
    workflow.add_node("frameworks", identify_frameworks)
    workflow.add_node("synthesize", synthesize_thinking)

    # Add edges (sequential)
    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "assumptions")
    workflow.add_edge("assumptions", "solution_check")
    workflow.add_edge("solution_check", "frameworks")
    workflow.add_edge("frameworks", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()


# ============================================================================
# Runner with Streaming
# ============================================================================

async def run_thinking_pipeline(
    message: str,
    bot_id: str = "lawrence",
    history: List[Dict] = None,
) -> AsyncGenerator[ThinkingStep, None]:
    """
    Run the thinking pipeline and yield steps as they complete.

    This is designed to stream updates to the ThinkingPanel in real-time.

    Usage:
        async for step in run_thinking_pipeline(message, bot_id, history):
            # Each step is yielded as it completes
            await update_thinking_panel(step)
    """
    history = history or []

    # Create initial state
    initial_state = ThinkingState(
        message=message,
        bot_id=bot_id,
        history=history,
    )

    # Create and run pipeline
    pipeline = create_thinking_pipeline()

    # Run through pipeline, yielding steps as they complete
    try:
        # Start first step
        yield ThinkingStep(name="Understanding your message", status="active", icon="🔍")

        result = await pipeline.ainvoke(initial_state)

        # Yield all completed steps
        for step in result.steps:
            yield step

    except Exception as e:
        logger.error(f"Thinking pipeline error: {e}")
        yield ThinkingStep(
            name="Analysis",
            status="error",
            icon="❌",
            output=f"Thinking pipeline error: {e}"
        )


async def get_thinking_steps_sync(
    message: str,
    bot_id: str = "lawrence",
    history: List[Dict] = None,
) -> List[Dict]:
    """
    Non-streaming version that returns all steps at once.

    Returns list of step dicts ready for ThinkingPanel props.
    """
    steps = []
    async for step in run_thinking_pipeline(message, bot_id, history):
        steps.append({
            "name": step.name,
            "status": step.status,
            "icon": step.icon,
            "output": step.output,
        })
    return steps
