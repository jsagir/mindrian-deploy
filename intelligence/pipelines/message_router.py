"""
LangGraph Message Router Pipeline
=================================
Routes incoming messages to the appropriate handler based on intent detection.

Routes:
- feedback: User providing feedback or rating
- image_gen: Image generation request
- file_process: File upload handling
- grading: Grading bot assessment
- research: Deep research trigger
- conversation: Normal conversation flow
"""

import re
from typing import TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END

# =============================================================================
# STATE DEFINITION
# =============================================================================

class MessageRouterState(TypedDict):
    """State for message routing pipeline."""
    # Input
    user_message: str
    session_id: str
    bot_id: str
    has_attachments: bool
    attachment_types: List[str]  # ["File", "Image", "Pdf", etc.]
    attachment_names: List[str]

    # Session context
    history: List[Dict[str, Any]]
    turn_count: int
    expecting_feedback: bool
    awaiting_image_prompt: bool

    # Routing decision
    route: Literal[
        "feedback",      # User providing feedback comment
        "image_gen",     # Image generation request
        "file_process",  # File upload handling
        "grading",       # Grading bot assessment
        "research",      # Deep research trigger
        "conversation",  # Normal conversation
    ]
    route_confidence: float
    route_reason: str

    # For downstream pipelines
    detected_intent: Dict[str, Any]
    should_enrich_context: bool


# =============================================================================
# INTENT DETECTION PATTERNS
# =============================================================================

# Image generation patterns
IMAGE_GEN_PATTERNS = [
    r"\b(generate|create|make|draw|design)\s+(an?\s+)?(image|picture|illustration|diagram|visual)",
    r"\b(show\s+me|visualize)\s+(an?\s+)?(image|picture)",
    r"\bimage\s+of\b",
    r"\bpicture\s+of\b",
    r"\billustrat(e|ion)\b",
]

# Research trigger patterns
RESEARCH_PATTERNS = [
    r"\b(research|investigate|look\s+up|find\s+out|search\s+for)\b",
    r"\b(what\s+does\s+the\s+research\s+say|according\s+to\s+studies)\b",
    r"\b(deep\s+dive|in-depth|comprehensive)\s+(analysis|research|review)\b",
    r"\b(latest|recent|current)\s+(research|studies|findings)\b",
]

# Grading bots
GRADING_BOTS = {"grading", "minto"}

# Document extensions that trigger file processing
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".pptx"}


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

async def classify_message_intent(state: MessageRouterState) -> MessageRouterState:
    """
    Stage 1: Classify the message intent to determine routing.

    Priority order:
    1. Session state flags (expecting_feedback, awaiting_image_prompt)
    2. Attachments (files trigger file_process)
    3. Bot type (grading bots get special handling)
    4. Content patterns (image gen, research triggers)
    5. Default to conversation
    """
    message = state["user_message"].lower()
    bot_id = state["bot_id"]

    # Track detected signals
    detected = {
        "patterns_matched": [],
        "attachment_signals": [],
        "bot_signals": [],
        "session_signals": [],
    }

    # === Priority 1: Session state flags ===
    if state.get("expecting_feedback"):
        state["route"] = "feedback"
        state["route_confidence"] = 1.0
        state["route_reason"] = "Session expecting feedback comment"
        detected["session_signals"].append("expecting_feedback=True")
        state["detected_intent"] = detected
        state["should_enrich_context"] = False
        return state

    if state.get("awaiting_image_prompt"):
        state["route"] = "image_gen"
        state["route_confidence"] = 1.0
        state["route_reason"] = "Session awaiting image prompt"
        detected["session_signals"].append("awaiting_image_prompt=True")
        state["detected_intent"] = detected
        state["should_enrich_context"] = False
        return state

    # === Priority 2: Attachments ===
    if state["has_attachments"]:
        attachment_names = state.get("attachment_names", [])
        has_documents = any(
            any(name.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)
            for name in attachment_names
        )

        if has_documents:
            # Check if grading bot with document = assessment mode
            if bot_id in GRADING_BOTS:
                state["route"] = "grading"
                state["route_confidence"] = 0.95
                state["route_reason"] = f"Document uploaded to {bot_id} bot"
                detected["attachment_signals"].append("document_for_grading")
                state["detected_intent"] = detected
                state["should_enrich_context"] = True
                return state
            else:
                state["route"] = "file_process"
                state["route_confidence"] = 0.9
                state["route_reason"] = "Document attachment detected"
                detected["attachment_signals"].append("document_upload")
                state["detected_intent"] = detected
                state["should_enrich_context"] = True
                return state

        # Images go to conversation (multimodal)
        has_images = "Image" in state["attachment_types"]
        if has_images:
            detected["attachment_signals"].append("image_upload")
            # Continue to conversation with multimodal

    # === Priority 3: Grading bot with substantial content ===
    if bot_id in GRADING_BOTS and len(state["user_message"]) > 500:
        state["route"] = "grading"
        state["route_confidence"] = 0.85
        state["route_reason"] = "Substantial content in grading bot (likely student work)"
        detected["bot_signals"].append("grading_bot_substantial_content")
        state["detected_intent"] = detected
        state["should_enrich_context"] = True
        return state

    # === Priority 4: Content pattern matching ===

    # Check image generation patterns
    for pattern in IMAGE_GEN_PATTERNS:
        if re.search(pattern, message):
            state["route"] = "image_gen"
            state["route_confidence"] = 0.8
            state["route_reason"] = f"Image generation pattern: {pattern}"
            detected["patterns_matched"].append(("image_gen", pattern))
            state["detected_intent"] = detected
            state["should_enrich_context"] = False
            return state

    # Check research patterns (only if explicitly triggered)
    research_score = 0
    for pattern in RESEARCH_PATTERNS:
        if re.search(pattern, message):
            research_score += 1
            detected["patterns_matched"].append(("research", pattern))

    if research_score >= 2:  # Multiple research signals
        state["route"] = "research"
        state["route_confidence"] = 0.75
        state["route_reason"] = f"Multiple research patterns detected ({research_score})"
        state["detected_intent"] = detected
        state["should_enrich_context"] = True
        return state

    # === Priority 5: Default to conversation ===
    state["route"] = "conversation"
    state["route_confidence"] = 0.7
    state["route_reason"] = "Default conversation flow"
    state["detected_intent"] = detected
    state["should_enrich_context"] = True
    return state


async def validate_route(state: MessageRouterState) -> MessageRouterState:
    """
    Stage 2: Validate and potentially adjust the routing decision.

    Checks:
    - Route makes sense for current bot
    - Confidence threshold met
    - No conflicting signals
    """
    route = state["route"]
    bot_id = state["bot_id"]
    confidence = state["route_confidence"]

    # Validate grading route
    if route == "grading" and bot_id not in GRADING_BOTS:
        # Downgrade to conversation if not a grading bot
        state["route"] = "conversation"
        state["route_reason"] += " (downgraded: not a grading bot)"
        state["route_confidence"] = 0.6

    # Validate research route - ensure it's not just casual mention
    if route == "research" and confidence < 0.7:
        state["route"] = "conversation"
        state["route_reason"] += " (downgraded: low confidence research)"

    # Add validation metadata
    state["detected_intent"]["validated"] = True
    state["detected_intent"]["final_route"] = state["route"]

    return state


def determine_next_step(state: MessageRouterState) -> str:
    """Conditional routing based on detected route."""
    return state["route"]


# =============================================================================
# PIPELINE CREATION
# =============================================================================

def create_message_router() -> StateGraph:
    """Create the message routing pipeline."""

    workflow = StateGraph(MessageRouterState)

    # Add nodes
    workflow.add_node("classify", classify_message_intent)
    workflow.add_node("validate", validate_route)

    # Set entry point
    workflow.set_entry_point("classify")

    # Classify -> Validate
    workflow.add_edge("classify", "validate")

    # Validate -> END (routing info is in state)
    workflow.add_edge("validate", END)

    return workflow.compile()


# =============================================================================
# PUBLIC API
# =============================================================================

# Singleton router instance
_router_instance = None


def get_message_router():
    """Get or create the message router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = create_message_router()
    return _router_instance


async def route_message(
    user_message: str,
    session_id: str,
    bot_id: str,
    history: List[Dict] = None,
    attachments: List[Any] = None,
    expecting_feedback: bool = False,
    awaiting_image_prompt: bool = False,
) -> Dict[str, Any]:
    """
    Route an incoming message to the appropriate handler.

    Args:
        user_message: The user's message content
        session_id: Session identifier
        bot_id: Current bot ID
        history: Conversation history
        attachments: List of Chainlit elements (files, images)
        expecting_feedback: Whether we're expecting a feedback comment
        awaiting_image_prompt: Whether we're expecting an image prompt

    Returns:
        Dict with routing decision:
        - route: The determined route
        - confidence: Confidence in the routing decision
        - reason: Explanation for the route
        - should_enrich_context: Whether to run RAG enrichment
        - detected_intent: Detailed detection info
    """
    # Process attachments
    attachment_types = []
    attachment_names = []
    if attachments:
        for att in attachments:
            attachment_types.append(type(att).__name__)
            if hasattr(att, 'name'):
                attachment_names.append(att.name or "")

    # Build initial state
    initial_state: MessageRouterState = {
        "user_message": user_message,
        "session_id": session_id,
        "bot_id": bot_id,
        "has_attachments": bool(attachments),
        "attachment_types": attachment_types,
        "attachment_names": attachment_names,
        "history": history or [],
        "turn_count": len(history) if history else 0,
        "expecting_feedback": expecting_feedback,
        "awaiting_image_prompt": awaiting_image_prompt,
        "route": "conversation",  # Default
        "route_confidence": 0.0,
        "route_reason": "",
        "detected_intent": {},
        "should_enrich_context": True,
    }

    # Run router
    router = get_message_router()
    result = await router.ainvoke(initial_state)

    return {
        "route": result["route"],
        "confidence": result["route_confidence"],
        "reason": result["route_reason"],
        "should_enrich_context": result["should_enrich_context"],
        "detected_intent": result["detected_intent"],
    }


# =============================================================================
# ROUTE HANDLERS (Stubs for downstream pipelines)
# =============================================================================

async def handle_feedback_route(state: MessageRouterState) -> Dict[str, Any]:
    """Handle feedback submission. Returns response dict."""
    # This would be implemented to process feedback
    return {
        "response": "Thank you for your feedback!",
        "actions": [],
        "elements": [],
    }


async def handle_image_gen_route(state: MessageRouterState) -> Dict[str, Any]:
    """Handle image generation request. Returns response dict."""
    # This would call utils.image_generation
    return {
        "response": "Generating image...",
        "actions": [],
        "elements": [],
    }


async def handle_file_process_route(state: MessageRouterState) -> Dict[str, Any]:
    """Handle file processing. Returns response dict."""
    # This would call intelligence.pipelines.file_processing
    from .file_processing import process_uploaded_files_langgraph
    # Implementation would go here
    return {
        "response": "Processing files...",
        "actions": [],
        "elements": [],
    }


async def handle_grading_route(state: MessageRouterState) -> Dict[str, Any]:
    """Handle grading assessment. Returns response dict."""
    # This would call the grading pipeline
    return {
        "response": "Analyzing submission...",
        "actions": [],
        "elements": [],
    }


async def handle_research_route(state: MessageRouterState) -> Dict[str, Any]:
    """Handle deep research request. Returns response dict."""
    # This would call research orchestrator
    return {
        "response": "Conducting research...",
        "actions": [],
        "elements": [],
    }


async def handle_conversation_route(state: MessageRouterState) -> Dict[str, Any]:
    """Handle normal conversation. Returns response dict."""
    # This would call the conversation pipeline
    return {
        "response": "",  # Streaming response
        "actions": [],
        "elements": [],
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "MessageRouterState",
    "create_message_router",
    "get_message_router",
    "route_message",
    "GRADING_BOTS",
    "DOCUMENT_EXTENSIONS",
]
