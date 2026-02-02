"""
Triple-Mode Integration Helper (v2 - LangExtract Powered)
==========================================================

Intelligent entry point detection and semantic grounding using LangExtract.
Replaces turn-based grounding with content-aware signals.

CONSOLIDATED CALLBACKS (3 instead of 7):
- select_entry_point: Entry point selection
- mode_or_stage: Mode toggle + venture stage
- grounding_response: Grounding prompt responses

Usage in mindrian_chat.py:
    from protocols.triple_mode import (
        init_triple_mode_session,
        auto_detect_entry_point,
        extract_and_update_progress,
        check_semantic_grounding,
        handle_entry_point_selection,
        handle_mode_or_stage,
        handle_grounding_response,
        show_exploration_progress_sidebar,
    )
"""

import chainlit as cl
from typing import Optional, Tuple, List, Dict, Any
from protocols.entry_point_router import (
    detect_entry_point as regex_detect_entry_point,
    get_clarification_prompt,
    get_entry_point_welcome,
    get_grounding_prompt
)

# Import LangExtract for intelligent detection
try:
    from tools.langextract import instant_extract, get_extraction_hint
    LANGEXTRACT_ENABLED = True
except ImportError:
    LANGEXTRACT_ENABLED = False

# Triple-Mode is enabled by default (can be toggled via env var)
import os
TRIPLE_MODE_ENABLED = os.getenv("TRIPLE_MODE_ENABLED", "true").lower() == "true"


# ============================================================================
# SESSION INITIALIZATION & PERSISTENCE
# ============================================================================

# Keys we persist to thread metadata
TRIPLE_MODE_PERSIST_KEYS = [
    "entry_point",
    "mode",
    "venture_stage",
    "topics_explored",
    "exploration_depth",
    "grounding_score",
    "opportunities_banked",
]


def init_triple_mode_session():
    """
    Initialize triple-mode session variables.
    Call at END of on_chat_start (after existing initialization).
    """
    # Core state
    if cl.user_session.get("entry_point") is None:
        cl.user_session.set("entry_point", None)

    if cl.user_session.get("mode") is None:
        cl.user_session.set("mode", "sandbox")

    if cl.user_session.get("venture_stage") is None:
        cl.user_session.set("venture_stage", None)

    # Exploration tracking (replaces turn counting)
    if cl.user_session.get("topics_explored") is None:
        cl.user_session.set("topics_explored", [])

    if cl.user_session.get("exploration_depth") is None:
        cl.user_session.set("exploration_depth", "initial")

    if cl.user_session.get("grounding_score") is None:
        cl.user_session.set("grounding_score", 0.0)

    if cl.user_session.get("opportunities_banked") is None:
        cl.user_session.set("opportunities_banked", 0)

    if cl.user_session.get("last_grounding_reason") is None:
        cl.user_session.set("last_grounding_reason", None)

    # Element references for updates
    if cl.user_session.get("progress_element") is None:
        cl.user_session.set("progress_element", None)


def get_triple_mode_state() -> Dict[str, Any]:
    """
    Get current triple-mode state for persistence.
    Returns dict suitable for thread metadata.
    """
    state = {}
    for key in TRIPLE_MODE_PERSIST_KEYS:
        value = cl.user_session.get(key)
        if value is not None:
            state[f"triple_mode_{key}"] = value
    return state


def restore_triple_mode_state(metadata: Dict[str, Any]) -> bool:
    """
    Restore triple-mode state from thread metadata.
    Call in on_chat_resume after restoring bot.
    Returns True if state was restored.
    """
    restored = False

    for key in TRIPLE_MODE_PERSIST_KEYS:
        meta_key = f"triple_mode_{key}"
        if meta_key in metadata:
            cl.user_session.set(key, metadata[meta_key])
            restored = True

    # Initialize any missing keys with defaults
    if cl.user_session.get("mode") is None:
        cl.user_session.set("mode", "sandbox")
    if cl.user_session.get("topics_explored") is None:
        cl.user_session.set("topics_explored", [])
    if cl.user_session.get("exploration_depth") is None:
        cl.user_session.set("exploration_depth", "initial")
    if cl.user_session.get("grounding_score") is None:
        cl.user_session.set("grounding_score", 0.0)
    if cl.user_session.get("opportunities_banked") is None:
        cl.user_session.set("opportunities_banked", 0)

    return restored


async def persist_triple_mode_state():
    """
    Persist current triple-mode state to thread metadata.
    Call after state changes (entry point selection, mode toggle, grounding, etc.)
    """
    try:
        # Get current thread
        thread_id = cl.user_session.get("id")
        if not thread_id:
            return

        # Get state to persist
        state = get_triple_mode_state()
        if not state:
            return

        # Update thread metadata
        # Note: Chainlit's thread update API varies by version
        # This uses the context approach which works in 2.9+
        context = cl.context.session
        if hasattr(context, 'thread') and context.thread:
            if context.thread.metadata is None:
                context.thread.metadata = {}
            context.thread.metadata.update(state)

    except Exception as e:
        # Don't fail the operation if persistence fails
        print(f"[TRIPLE_MODE] Persistence warning: {e}")


# ============================================================================
# LANGEXTRACT-POWERED ENTRY POINT DETECTION
# ============================================================================

async def auto_detect_entry_point(
    message: str,
    has_attachment: bool = False
) -> Dict[str, Any]:
    """
    Use LangExtract to intelligently detect entry point from first message.

    Returns:
        {
            "entry_point": str or None,
            "confidence": float,
            "mode": str,
            "signals": dict,
            "should_show_selector": bool
        }
    """
    # Attachment = Document Review (high confidence)
    if has_attachment:
        return {
            "entry_point": "document_review",
            "confidence": 0.95,
            "mode": "workshop",
            "signals": {"has_attachment": True},
            "should_show_selector": False
        }

    # Use LangExtract if available
    if LANGEXTRACT_ENABLED:
        signals = instant_extract(message)
        return _analyze_signals_for_entry_point(signals, message)

    # Fallback to regex detection
    entry_point, confidence, _ = regex_detect_entry_point(message, has_attachment)
    return {
        "entry_point": entry_point,
        "confidence": confidence,
        "mode": "sandbox" if entry_point == "brainstorming" else "workshop",
        "signals": {},
        "should_show_selector": entry_point is None or confidence < 0.5
    }


def _analyze_signals_for_entry_point(signals: Dict, message: str) -> Dict[str, Any]:
    """Analyze LangExtract signals to determine entry point."""

    content_type = signals.get("content_type", "general")
    quality = signals.get("quality_signals", {})
    counts = signals.get("counts", {})
    msg_lower = message.lower()

    # Keyword hints for short messages (boost detection)
    BRAINSTORM_KEYWORDS = ["explore", "trend", "brainstorm", "future", "what if", "curious", "wondering", "possibilities"]
    DOCUMENT_KEYWORDS = ["review", "pitch deck", "document", "analyze", "feedback", "deck", "pdf", "uploaded", "attached"]
    VENTURE_KEYWORDS = ["startup", "venture", "build", "company", "business", "launch", "market", "customers", "idea", "product", "solve", "problem worth"]

    brainstorm_score = sum(1 for kw in BRAINSTORM_KEYWORDS if kw in msg_lower)
    document_score = sum(1 for kw in DOCUMENT_KEYWORDS if kw in msg_lower)
    venture_score = sum(1 for kw in VENTURE_KEYWORDS if kw in msg_lower)

    # If keywords strongly indicate an entry point, use that
    max_score = max(brainstorm_score, document_score, venture_score)
    if max_score >= 2:
        if brainstorm_score == max_score:
            return {
                "entry_point": "brainstorming",
                "confidence": 0.7 + (brainstorm_score * 0.05),
                "mode": "sandbox",
                "signals": signals,
                "should_show_selector": False
            }
        elif document_score == max_score:
            return {
                "entry_point": "document_review",
                "confidence": 0.7 + (document_score * 0.05),
                "mode": "workshop",
                "signals": signals,
                "should_show_selector": False
            }
        elif venture_score == max_score:
            return {
                "entry_point": "build_venture",
                "confidence": 0.7 + (venture_score * 0.05),
                "mode": "sandbox",
                "signals": signals,
                "should_show_selector": False
            }

    # Single keyword with moderate confidence
    if max_score == 1:
        if brainstorm_score == 1:
            return {
                "entry_point": "brainstorming",
                "confidence": 0.55,
                "mode": "sandbox",
                "signals": signals,
                "should_show_selector": True  # Still show selector for confirmation
            }
        elif document_score == 1:
            return {
                "entry_point": "document_review",
                "confidence": 0.55,
                "mode": "workshop",
                "signals": signals,
                "should_show_selector": True
            }
        elif venture_score == 1:
            return {
                "entry_point": "build_venture",
                "confidence": 0.55,
                "mode": "sandbox",
                "signals": signals,
                "should_show_selector": True
            }

    # Document Review: Has structure, PWS elements, data
    if quality.get("has_pws_elements") and quality.get("has_data"):
        return {
            "entry_point": "document_review",
            "confidence": 0.75,
            "mode": "workshop",
            "signals": signals,
            "should_show_selector": False
        }

    # Build Venture: Solution-focused without exploration
    if content_type == "solution_focused" and counts.get("problems", 0) == 0:
        return {
            "entry_point": "build_venture",
            "confidence": 0.7,
            "mode": "sandbox",
            "signals": signals,
            "should_show_selector": False
        }

    # Brainstorming: Exploratory, question-heavy, trend-focused
    if content_type == "exploratory" or quality.get("is_forward_looking"):
        return {
            "entry_point": "brainstorming",
            "confidence": 0.8,
            "mode": "sandbox",
            "signals": signals,
            "should_show_selector": False
        }

    # Problem-focused could be either brainstorming or document review
    if content_type == "problem_focused":
        # Short message = exploring, long message = reviewing
        if signals.get("word_count", 0) > 100:
            return {
                "entry_point": "document_review",
                "confidence": 0.6,
                "mode": "workshop",
                "signals": signals,
                "should_show_selector": False
            }
        else:
            return {
                "entry_point": "brainstorming",
                "confidence": 0.65,
                "mode": "sandbox",
                "signals": signals,
                "should_show_selector": False
            }

    # Low confidence - show selector
    return {
        "entry_point": None,
        "confidence": 0.3,
        "mode": "sandbox",
        "signals": signals,
        "should_show_selector": True
    }


# ============================================================================
# SEMANTIC GROUNDING (REPLACES TURN COUNTING)
# ============================================================================

def check_semantic_grounding(signals: Dict) -> Optional[str]:
    """
    Check if semantic grounding is needed based on content signals.
    Returns grounding reason or None.

    This replaces turn-based grounding with content-aware detection.
    """
    if not signals or signals.get("empty"):
        return None

    counts = signals.get("counts", {})
    quality = signals.get("quality_signals", {})
    content_type = signals.get("content_type", "general")

    # Pattern check: Multiple problems identified, not connecting them
    if counts.get("problems", 0) >= 3 and counts.get("causation", 0) == 0:
        return "pattern_check"

    # Synthesis: Has assumptions + causation but no clear problem statement
    if counts.get("assumptions", 0) >= 2 and counts.get("causation", 0) >= 1:
        if content_type != "problem_focused":
            return "synthesis"

    # Bank prompt: Has solutions + forward-looking + data
    if (counts.get("solutions", 0) >= 2 and
        quality.get("is_forward_looking") and
        quality.get("has_data")):
        return "bank_prompt"

    # Problem validation: Solution-focused without problem clarity
    if content_type == "solution_focused" and counts.get("problems", 0) == 0:
        return "problem_validation"

    return None


# ============================================================================
# TOPIC EXTRACTION & PROGRESS TRACKING
# ============================================================================

def extract_topics_from_signals(signals: Dict) -> List[str]:
    """Extract topic keywords from LangExtract signals."""
    topics = []

    samples = signals.get("samples", {})

    # Extract from problem mentions
    if samples.get("problems"):
        for problem in samples["problems"][:3]:
            # Clean up the match
            cleaned = problem.strip().lower()
            if len(cleaned) > 3 and len(cleaned) < 50:
                topics.append(cleaned)

    # Extract from trends
    if samples.get("trends"):
        for trend in samples["trends"][:2]:
            cleaned = trend.strip().lower()
            if len(cleaned) > 3:
                topics.append(cleaned)

    return list(set(topics))[:10]  # Dedupe and limit


def calculate_depth_from_signals(signals: Dict, current_depth: str, topic_count: int) -> str:
    """Calculate exploration depth from content signals."""

    counts = signals.get("counts", {})
    quality = signals.get("quality_signals", {})

    # Depth scoring
    depth_score = 0

    # Questions indicate exploration
    depth_score += min(counts.get("questions", 0), 3)

    # Causation indicates deeper thinking
    depth_score += counts.get("causation", 0) * 2

    # Assumptions indicate awareness
    depth_score += counts.get("assumptions", 0)

    # Data grounding is good
    if quality.get("has_data"):
        depth_score += 2

    # Sources add credibility
    if quality.get("has_sources"):
        depth_score += 2

    # Topic diversity matters
    depth_score += min(topic_count // 2, 3)

    # Map to depth levels
    if depth_score >= 10:
        return "synthesis"
    elif depth_score >= 6:
        return "deep"
    elif depth_score >= 3:
        return "exploring"
    else:
        return "initial"


def calculate_grounding_score(signals: Dict) -> float:
    """Calculate grounding score (0-1) from signals."""

    quality = signals.get("quality_signals", {})
    counts = signals.get("counts", {})

    score = 0.0
    max_score = 5.0

    # Has data = well-grounded
    if quality.get("has_data"):
        score += 1.5

    # Has sources = evidence-based
    if quality.get("has_sources"):
        score += 1.5

    # Low uncertainty = confident
    if not quality.get("has_uncertainty"):
        score += 0.5

    # Causation = connecting dots
    if counts.get("causation", 0) >= 1:
        score += 1.0

    # PWS elements = structured thinking
    if quality.get("has_pws_elements"):
        score += 0.5

    return min(score / max_score, 1.0)


async def extract_and_update_progress(message: str) -> Dict[str, Any]:
    """
    Extract signals from message and update exploration progress.
    Returns signals for use in grounding check.
    """
    if not LANGEXTRACT_ENABLED:
        return {}

    signals = instant_extract(message)

    # Get current state
    current_topics = cl.user_session.get("topics_explored", [])
    current_depth = cl.user_session.get("exploration_depth", "initial")

    # Extract new topics
    new_topics = extract_topics_from_signals(signals)
    all_topics = list(set(current_topics + new_topics))[:20]  # Limit to 20

    # Calculate new depth
    new_depth = calculate_depth_from_signals(signals, current_depth, len(all_topics))

    # Calculate grounding score
    grounding = calculate_grounding_score(signals)

    # Update session
    cl.user_session.set("topics_explored", all_topics)
    cl.user_session.set("exploration_depth", new_depth)
    cl.user_session.set("grounding_score", grounding)

    # Update sidebar element if exists
    progress_element = cl.user_session.get("progress_element")
    if progress_element:
        try:
            progress_element.props["depth"] = new_depth
            progress_element.props["topicsExplored"] = all_topics
            progress_element.props["groundingScore"] = grounding
            await progress_element.update()
        except Exception:
            pass  # Element update failed, continue anyway

    # Persist state (topics, depth, score changed)
    await persist_triple_mode_state()

    return signals


# ============================================================================
# ENTRY POINT HANDLERS
# ============================================================================

async def show_entry_point_selector():
    """Show entry point selector element."""
    try:
        selector = cl.CustomElement(
            name="EntryPointSelector",
            props={"showWelcome": True, "disabled": False},
            display="inline"
        )
        await cl.Message(content="", elements=[selector]).send()
    except Exception:
        await cl.Message(content=get_clarification_prompt()).send()


async def handle_entry_point_selection(entry_point: str):
    """
    CONSOLIDATED HANDLER for select_entry_point callback.
    Sets session vars and shows appropriate UI.
    """
    cl.user_session.set("entry_point", entry_point)

    # Set default mode
    mode_defaults = {
        "brainstorming": "sandbox",
        "document_review": "workshop",
        "build_venture": "sandbox"
    }
    cl.user_session.set("mode", mode_defaults.get(entry_point, "sandbox"))

    # Reset exploration state
    cl.user_session.set("topics_explored", [])
    cl.user_session.set("exploration_depth", "initial")
    cl.user_session.set("grounding_score", 0.0)
    cl.user_session.set("last_grounding_reason", None)

    # Show welcome message
    welcome = get_entry_point_welcome(entry_point)
    await cl.Message(content=welcome).send()

    # Show mode toggle for applicable entry points
    if entry_point in ["brainstorming", "document_review"]:
        await show_mode_toggle()

    # Show venture stage selector for build venture
    if entry_point == "build_venture":
        await show_venture_stage_selector()

    # Show exploration progress sidebar for brainstorming
    if entry_point == "brainstorming":
        await show_exploration_progress_sidebar()

    # Persist state to thread metadata
    await persist_triple_mode_state()


# ============================================================================
# MODE/STAGE HANDLER (CONSOLIDATED)
# ============================================================================

async def handle_mode_or_stage(payload: Dict):
    """
    CONSOLIDATED HANDLER for mode_or_stage callback.
    Handles both mode toggle and venture stage selection.
    """
    if "mode" in payload:
        await _handle_mode_toggle(payload["mode"])
    elif "stage" in payload:
        await _handle_venture_stage(payload["stage"])


async def _handle_mode_toggle(new_mode: str):
    """Handle mode toggle (sandbox/workshop)."""
    old_mode = cl.user_session.get("mode", "sandbox")
    cl.user_session.set("mode", new_mode)

    # Generate transition message
    if new_mode == "workshop":
        msg = """🎯 **Workshop Mode Active**

Switching to guided, phase-by-phase progression.
Your exploration context is preserved."""
    else:
        msg = """🔬 **Sandbox Mode Active**

Switching to free exploration.
Your workshop progress is saved."""

    await cl.Message(content=msg).send()
    await show_mode_toggle()

    # Persist state
    await persist_triple_mode_state()


async def _handle_venture_stage(stage: str):
    """Handle venture stage selection."""
    cl.user_session.set("venture_stage", stage)

    responses = {
        "pre_opportunity": """Based on your selection, you're still **looking for problems**.

That means your immediate job is: **Find a problem worth solving**

I recommend switching to **Exploration Mode** to discover opportunities.

Would you like me to help you explore? Just tell me what domain or trend interests you.""",

        "opportunity_identified": """You're at **Opportunity Identified** stage.

Your immediate job is: **Deeply understand the problem and who has it**

The biggest mistake at this stage: **Building before talking to customers**

Let's work on:
• Jobs to Be Done - What job is the customer hiring for?
• Problem Validation - Is this problem real and painful?

What problem have you identified?""",

        "well_defined_problem": """You're at **Well-Defined Problem** stage.

Your immediate job is: **Design the business around the problem**

The biggest mistake at this stage: **Ignoring timing and competitive positioning**

Let's work on:
• Business Model Canvas - How will you create and capture value?
• S-Curve Analysis - Is the timing right?

Describe your problem and proposed solution.""",

        "ready_to_build": """You're at **Ready to Build** stage.

Your immediate job is: **Execute with discipline**

The biggest mistake at this stage: **Losing sight of the problem you're solving**

Let's work on:
• Execution Planning - What's the roadmap?
• Investment Readiness - Are you fundable?

What's your biggest execution challenge right now?"""
    }

    response = responses.get(stage, responses["pre_opportunity"])
    await cl.Message(content=response).send()

    # If pre-opportunity, redirect to brainstorming
    if stage == "pre_opportunity":
        cl.user_session.set("entry_point", "brainstorming")
        cl.user_session.set("mode", "sandbox")
        await show_exploration_progress_sidebar()

    # Persist state
    await persist_triple_mode_state()


# ============================================================================
# GROUNDING RESPONSE HANDLER (CONSOLIDATED)
# ============================================================================

async def handle_grounding_response(payload: Dict):
    """
    CONSOLIDATED HANDLER for grounding_response callback.
    Handles acknowledge, skip, and bank actions.
    """
    action = payload.get("action", "acknowledge")
    reason = payload.get("reason", "pattern_check")

    if action == "acknowledge":
        # User engaged with prompt
        cl.user_session.set("last_grounding_reason", None)
        await cl.Message(
            content="Take your time. When you're ready, share what you're thinking."
        ).send()

    elif action == "skip":
        # User wants to continue exploring
        cl.user_session.set("last_grounding_reason", None)
        await cl.Message(
            content="Continuing exploration. I'll check in again when it seems helpful."
        ).send()

    elif action == "bank":
        # User wants to bank an opportunity
        banked = cl.user_session.get("opportunities_banked", 0) + 1
        cl.user_session.set("opportunities_banked", banked)
        cl.user_session.set("last_grounding_reason", None)

        # Update progress element
        progress_element = cl.user_session.get("progress_element")
        if progress_element:
            try:
                progress_element.props["opportunitiesBanked"] = banked
                await progress_element.update()
            except Exception:
                pass

        # Try to extract and store opportunities from recent conversation
        stored_count = 0
        try:
            from tools.opportunity_bank import extract_and_store_opportunities

            history = cl.user_session.get("history", [])
            if history:
                bot_id = cl.user_session.get("bot_id", "lawrence")
                user_id = cl.user_session.get("user_id") or cl.user_session.get("id")
                thread_id = cl.user_session.get("id", "")

                opportunities, summary = await extract_and_store_opportunities(
                    conversation=history[-20:],  # Last 20 messages
                    bot_id=bot_id,
                    methodology=bot_id,
                    phase=cl.user_session.get("exploration_depth", "initial"),
                    conversation_id=thread_id,
                    user_id=user_id,
                    created_by_type="user"
                )
                stored_count = summary.get("stored", 0)

        except ImportError:
            pass  # opportunity_bank not available
        except Exception as e:
            print(f"[TRIPLE_MODE] Opportunity extraction error: {e}")

        # Show result message
        if stored_count > 0:
            await cl.Message(
                content=f"🏦 **{stored_count} Opportunity{'s' if stored_count > 1 else ''} Banked!**\n\nI've extracted and saved the opportunities from our conversation. You can continue exploring or describe any additional insights you'd like to capture."
            ).send()
        else:
            await cl.Message(
                content=f"🏦 **Opportunity #{banked} noted!**\n\nDescribe the opportunity you've identified, and I'll help you capture it properly."
            ).send()

        # Persist state after banking
        await persist_triple_mode_state()


# ============================================================================
# UI ELEMENT HELPERS
# ============================================================================

async def show_mode_toggle():
    """Show mode toggle element."""
    try:
        mode = cl.user_session.get("mode", "sandbox")
        entry_point = cl.user_session.get("entry_point", "brainstorming")

        toggle = cl.CustomElement(
            name="ModeToggle",
            props={
                "currentMode": mode,
                "entryPoint": entry_point,
                "disabled": False
            },
            display="inline"
        )
        await cl.Message(content="", elements=[toggle]).send()
    except Exception:
        pass


async def show_venture_stage_selector():
    """Show venture stage selector element."""
    try:
        selector = cl.CustomElement(
            name="VentureStageSelector",
            props={"disabled": False, "currentStage": None},
            display="inline"
        )
        await cl.Message(content="", elements=[selector]).send()
    except Exception:
        await cl.Message(content="""**Where are you in your journey?**

• 🔍 **Pre-Opportunity** - Still looking for problems
• 💡 **Opportunity Identified** - Found a problem, understanding it
• 🎯 **Well-Defined Problem** - Problem is clear, designing business
• 🚀 **Ready to Build** - Problem validated, solution designed

Which stage are you at?""").send()


async def show_exploration_progress_sidebar():
    """Show exploration progress element in sidebar (display='side')."""
    try:
        progress = cl.CustomElement(
            name="ExplorationProgress",
            props={
                "depth": cl.user_session.get("exploration_depth", "initial"),
                "topicsExplored": cl.user_session.get("topics_explored", []),
                "sourcesConsulted": 0,
                "groundingScore": cl.user_session.get("grounding_score", 0.0),
                "opportunitiesBanked": cl.user_session.get("opportunities_banked", 0),
                "lastGroundingReason": None
            },
            display="side"  # SIDEBAR - persists
        )

        # Store reference for updates
        cl.user_session.set("progress_element", progress)

        await cl.Message(content="", elements=[progress]).send()
    except Exception:
        pass


async def show_grounding_prompt(reason: str):
    """Show grounding prompt element."""
    prompt_text = get_grounding_prompt(reason)
    topics = cl.user_session.get("topics_explored", [])

    # Update last grounding reason
    cl.user_session.set("last_grounding_reason", reason)

    # Update progress element hint
    progress_element = cl.user_session.get("progress_element")
    if progress_element:
        try:
            progress_element.props["lastGroundingReason"] = reason
            await progress_element.update()
        except Exception:
            pass

    try:
        grounding_el = cl.CustomElement(
            name="GroundingPrompt",
            props={
                "reason": reason,
                "turnCount": len(topics),  # Use topic count instead of turn count
                "topics": topics,
                "prompt": prompt_text
            },
            display="inline"
        )
        await cl.Message(content="", elements=[grounding_el]).send()
    except Exception:
        # Fallback to text
        await cl.Message(
            content=f"---\n\n**💡 {reason.replace('_', ' ').title()}**\n\n{prompt_text}\n\n---"
        ).send()


# ============================================================================
# COACHING HINT (FOR SYSTEM MESSAGE INJECTION)
# ============================================================================

def get_coaching_hint_for_message(message: str) -> Optional[str]:
    """
    Get coaching hint to inject into system message.
    Uses LangExtract's get_extraction_hint.
    """
    if not LANGEXTRACT_ENABLED:
        return None

    signals = instant_extract(message)
    return get_extraction_hint(signals)


# ============================================================================
# CONTEXT BUTTONS (ENTRY-POINT SPECIFIC)
# ============================================================================

def get_entry_point_buttons() -> List[cl.Action]:
    """Get entry-point-specific action buttons."""
    entry_point = cl.user_session.get("entry_point")

    buttons = []

    if entry_point == "brainstorming":
        buttons.extend([
            cl.Action(
                name="grounding_response",
                payload={"action": "bank", "reason": "user_initiated"},
                label="🏦 Bank Opportunity",
                tooltip="Save this opportunity to your bank"
            ),
        ])

    elif entry_point == "document_review":
        buttons.extend([
            cl.Action(
                name="red_team_critique",
                payload={"action": "red_team"},
                label="🎯 Challenge This",
                tooltip="Get adversarial critique"
            ),
        ])

    elif entry_point == "build_venture":
        buttons.extend([
            cl.Action(
                name="mode_or_stage",
                payload={"stage": None},  # Will show selector
                label="📍 Reassess Stage",
                tooltip="Check your current venture stage"
            ),
        ])

    return buttons
