"""
Entry Point Router - Triple-Mode Architecture
==============================================

Detects user intent and routes to appropriate entry point:
- brainstorming: Exploration, finding problems
- document_review: Validation, getting feedback
- build_venture: Execution, building business

Uses regex patterns first (fast), falls back to clarification prompt.
"""

import re
from typing import Optional, Tuple

# Intent patterns for each entry point
ENTRY_POINT_PATTERNS = {
    "brainstorming": [
        r"explore", r"discover", r"what if", r"trends", r"opportunities",
        r"no idea", r"curious about", r"interesting", r"future of",
        r"brainstorm", r"generate ideas", r"looking for problems",
        r"what.*(work on|should I|could I)", r"where.*(start|begin|look)",
        r"find.*(problem|opportunity)", r"help me think"
    ],
    "document_review": [
        r"review", r"feedback", r"grade", r"evaluate", r"look at",
        r"critique", r"poke holes", r"what's wrong", r"improve",
        r"pitch deck", r"business plan", r"is this good", r"check my",
        r"uploaded", r"attached", r"here's my", r"read this",
        r"what do you think of", r"rate my", r"score"
    ],
    "build_venture": [
        r"build", r"create", r"start", r"execute", r"implement",
        r"next steps", r"stuck on", r"how do I", r"business model",
        r"already have a company", r"startup", r"venture", r"launch",
        r"ready to", r"validated", r"know the problem", r"have an idea"
    ]
}

# Agent suggestions per entry point based on message content
AGENT_SUGGESTIONS = {
    "brainstorming": {
        r"trend|future|what if|extrapolat": "tta",
        r"domain|where.*look|industry": "domain_explorer",
        r"question|reframe|ask": "beautiful_question",
        r"scenario|possible|futures": "scenario",
        r"don't know|unknown|blind spot": "knowns",
        r"challenge|stress.?test|assumption": "redteam"
    },
    "document_review": {
        r"grade|score|rubric": "pws_grading",
        r"poke holes|attack|challenge": "redteam",
        r"bias|assumption|flaw": "devil_advocate",
        r"invest|fund|pitch": "pws_investment"
    },
    "build_venture": {
        r"job|customer|hire": "jtbd",
        r"pyramid|data|wisdom": "ackoff",
        r"model|canvas|revenue": "bmc",
        r"timing|curve|adoption": "scurve",
        r"hat|perspective|comprehensive": "bono"
    }
}


def detect_entry_point(message: str, has_attachment: bool = False) -> Tuple[Optional[str], float, Optional[str]]:
    """
    Detect entry point from user message.

    Args:
        message: User's message text
        has_attachment: Whether user uploaded a file

    Returns:
        Tuple of (entry_point, confidence, suggested_agent)
        entry_point: "brainstorming" | "document_review" | "build_venture" | None
        confidence: 0.0 to 1.0
        suggested_agent: Bot ID to suggest, or None
    """
    # Attachment strongly suggests Document Review
    if has_attachment:
        agent = _suggest_agent("document_review", message)
        return ("document_review", 0.9, agent)

    message_lower = message.lower()

    # Score each entry point
    scores = {}
    for entry_point, patterns in ENTRY_POINT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, message_lower):
                score += 1
        scores[entry_point] = score

    # Find best match
    best_entry = max(scores, key=scores.get)
    best_score = scores[best_entry]

    # No matches - ambiguous
    if best_score == 0:
        return (None, 0.0, None)

    # Check confidence (score gap between top two)
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) < 1:
        confidence = 0.6  # Close call
    else:
        confidence = min(0.95, 0.5 + (best_score * 0.15))

    # Suggest agent
    suggested_agent = _suggest_agent(best_entry, message_lower)

    return (best_entry, confidence, suggested_agent)


def _suggest_agent(entry_point: str, message: str) -> Optional[str]:
    """Suggest specific agent based on message content."""

    if entry_point not in AGENT_SUGGESTIONS:
        return None

    message_lower = message.lower()

    for pattern, agent in AGENT_SUGGESTIONS[entry_point].items():
        if re.search(pattern, message_lower):
            return agent

    # Default agents per entry point
    defaults = {
        "brainstorming": "tta",
        "document_review": "redteam",
        "build_venture": "jtbd"
    }
    return defaults.get(entry_point)


def get_clarification_prompt() -> str:
    """Get clarification prompt when intent is ambiguous."""
    return """I want to help you effectively. Tell me where you are:

🧠 **EXPLORE** — "I'm looking for problems worth solving"
   → I'll help you discover opportunities

📄 **VALIDATE** — "I have something, need feedback"
   → I'll critique and improve your thinking

🚀 **BUILD** — "I'm ready to execute"
   → I'll help you build your venture

Which fits best? Or just tell me what's on your mind."""


def get_entry_point_welcome(entry_point: str) -> str:
    """Get welcome message for selected entry point."""

    welcomes = {
        "brainstorming": """## 🧠 Exploration Mode

Let's find problems worth solving.

**What are you curious about?** What's been bugging you lately?

I'm not asking for a business plan. I'm asking: what's interesting?""",

        "document_review": """## 📄 Validation Mode

Show me what you've got, and I'll give you honest feedback.

**What would you like me to review?**

You can upload a document or describe your idea.""",

        "build_venture": """## 🚀 Build Mode

Let's turn your opportunity into a venture.

But first — let me check where you are. A few quick questions:

• Can you clearly state the problem you're solving?
• Do you know who has this problem?
• Do you have evidence they care?

Answer what you can, and I'll guide you to the right tools."""
    }

    return welcomes.get(entry_point, "How can I help you today?")


# Grounding prompts for each intervention type
GROUNDING_PROMPTS = {
    "pattern_check": """We've been exploring for a bit. Let me check:

• What patterns are you seeing?
• What's the most interesting thread so far?
• Who would care if you pulled on that thread?""",

    "synthesis": """Time to synthesize. You've gathered threads — now weave them.

Complete this:
**[WHO]** struggles with **[PROBLEM]** because **[REASON]**,
and if we could **[SOLVE]**, then **[OUTCOME]**.

Can you fill that in?""",

    "bank_prompt": """We've explored a lot. Before we continue:

You need to articulate at least one opportunity.

An opportunity isn't a solution — it's a problem worth solving.

**What's the single most promising problem you've identified?**""",

    "problem_validation": """Hold on. Before we build anything:

• What's the problem you're solving?
• Who has this problem?
• What evidence do you have that they care?

I can't help you build something until we've validated there's a problem worth solving."""
}


def get_grounding_prompt(reason: str) -> str:
    """Get grounding prompt for intervention."""
    return GROUNDING_PROMPTS.get(reason, GROUNDING_PROMPTS["pattern_check"])
