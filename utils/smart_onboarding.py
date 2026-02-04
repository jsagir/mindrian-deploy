"""
Smart Onboarding & Contextual Tooltips
=======================================

Intelligent onboarding system that:
- Detects user expertise level from conversation patterns
- Shows progressive disclosure of PWS concepts
- Provides contextual tooltips that explain jargon in plain language
- Uses smart timing - helps when users seem confused, not when they're flowing

Philosophy: "Teach concepts in the moment of need, not in a lecture"

Usage:
    from utils.smart_onboarding import (
        get_onboarding_state,
        should_show_concept_help,
        get_contextual_tooltip,
        mark_concept_learned,
        detect_confusion_signals,
        get_progressive_welcome,
    )
"""

import os
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# =============================================================================
# PWS CONCEPT DEFINITIONS
# =============================================================================

class ExpertiseLevel(str, Enum):
    NEWCOMER = "newcomer"       # First time, needs everything explained
    FAMILIAR = "familiar"       # Has used before, knows basics
    PRACTITIONER = "practitioner"  # Uses regularly, knows frameworks
    EXPERT = "expert"           # Deep knowledge, no help needed

@dataclass
class PWSTerm:
    """A PWS methodology term with explanation."""
    term: str                          # The jargon term
    plain_english: str                 # Simple 1-sentence explanation
    detailed: str                      # Longer explanation when they want more
    example: str                       # Real-world example
    related_terms: List[str] = field(default_factory=list)
    first_mention_trigger: bool = True  # Show on first encounter?
    complexity_level: int = 1          # 1=basic, 2=intermediate, 3=advanced

# The PWS Glossary - plain English explanations
PWS_GLOSSARY: Dict[str, PWSTerm] = {
    "pws": PWSTerm(
        term="PWS (Problems Worth Solving)",
        plain_english="A framework for finding problems that are valuable enough to actually solve.",
        detailed="PWS helps you avoid solving the wrong problems. It's a systematic way to evaluate whether a problem is worth your time and resources before you invest in solutions.",
        example="Instead of building a faster horse, PWS would help you discover people actually need faster transportation - leading to cars.",
        related_terms=["reverse salient", "jobs to be done"],
        complexity_level=1
    ),
    "reverse salient": PWSTerm(
        term="Reverse Salient",
        plain_english="A bottleneck holding everything else back - fix this one thing, and everything improves.",
        detailed="Originally a military term for a weak point in a line. In innovation, it's the constraint that's blocking progress. Like how battery technology was the reverse salient for electric cars - solving batteries unlocked the whole industry.",
        example="For smartphones, the reverse salient was touch screen technology. Once that was solved, everything else became possible.",
        related_terms=["constraint", "bottleneck", "pws"],
        complexity_level=2
    ),
    "jtbd": PWSTerm(
        term="Jobs to Be Done (JTBD)",
        plain_english="What is the customer actually trying to accomplish in their life?",
        detailed="People don't buy products - they 'hire' them to do a job. Understanding the real job helps you build better solutions. The job stays constant even as products change.",
        example="People don't want a drill - they want a hole. They don't even want a hole - they want to hang a picture. JTBD asks 'what progress is the person trying to make?'",
        related_terms=["customer needs", "progress"],
        complexity_level=1
    ),
    "tta": PWSTerm(
        term="Trending to the Absurd (TTA)",
        plain_english="Take a trend to its extreme to see what breaks first.",
        detailed="A stress-testing technique. By extrapolating a trend to its logical extreme, you can identify which assumptions will fail first and where the real opportunities lie.",
        example="If remote work trends continue, eventually offices are empty. What breaks? Commercial real estate, commuting infrastructure, office supply companies. Each breaking point is an opportunity.",
        related_terms=["trend analysis", "assumptions"],
        complexity_level=2
    ),
    "s-curve": PWSTerm(
        term="S-Curve",
        plain_english="Every technology follows the same pattern: slow start, rapid growth, then plateau.",
        detailed="Understanding where a technology is on its S-curve helps you time your entry. Early = high risk but big reward. Middle = proven but competitive. Late = stable but commoditized.",
        example="Electric vehicles: Started slow (1990s), now in rapid growth (2020s), will plateau when most cars are electric (2030s?). Where on the curve are you investing?",
        related_terms=["timing", "technology adoption"],
        complexity_level=2
    ),
    "dikw": PWSTerm(
        term="DIKW Pyramid (Ackoff's Pyramid)",
        plain_english="Data → Information → Knowledge → Wisdom. Each level adds more understanding.",
        detailed="Raw data becomes information when organized. Information becomes knowledge when understood. Knowledge becomes wisdom when you can apply it well. Most people drown in data without climbing the pyramid.",
        example="Sales numbers (data) → 'Sales dropped 20%' (information) → 'Competitor launched cheaper product' (knowledge) → 'We should differentiate on quality, not price' (wisdom)",
        related_terms=["understanding", "decision making"],
        complexity_level=2
    ),
    "red team": PWSTerm(
        term="Red Teaming",
        plain_english="Deliberately try to break your own idea to find weaknesses before others do.",
        detailed="A practice from military and cybersecurity. The red team's job is to attack your plan. Better to discover flaws yourself than have the market or competitors find them.",
        example="Before launching, have someone role-play as your biggest competitor and try to destroy your business plan. What do they attack first?",
        related_terms=["devil's advocate", "assumptions"],
        complexity_level=1
    ),
    "validation": PWSTerm(
        term="Validation",
        plain_english="Testing whether your assumption is actually true, not just hoping it is.",
        detailed="Many ideas fail because founders fall in love with assumptions without testing them. Validation means gathering real evidence - talking to customers, running experiments, analyzing data.",
        example="You assume 'busy professionals will pay $50/month for meal planning.' Validation = actually asking 50 busy professionals if they would pay, and watching what they actually do.",
        related_terms=["assumptions", "evidence"],
        complexity_level=1
    ),
    "domain": PWSTerm(
        term="Domain",
        plain_english="The industry or field where your problem exists.",
        detailed="Understanding your domain deeply helps you identify problems others miss and build credibility. Domain expertise is often more valuable than technical skills.",
        example="'Healthcare' is a domain. 'Senior care' is a subdomain. 'Memory care for Alzheimer's patients' is a specific niche where deep domain knowledge matters.",
        related_terms=["industry", "market"],
        complexity_level=1
    ),
    "opportunity bank": PWSTerm(
        term="Bank of Opportunities",
        plain_english="A collection of problems worth solving that you've discovered over time.",
        detailed="Like a savings account, but for ideas. As you explore, you'll find more problems than you can solve immediately. The bank stores them so good ideas don't get lost.",
        example="While researching EdTech, you notice teachers struggling with parent communication. You're focused on curriculum now, but bank the communication problem for later.",
        related_terms=["problem discovery", "pws"],
        complexity_level=1
    ),
    "value potential": PWSTerm(
        term="Value Potential",
        plain_english="How much impact could solving this problem have?",
        detailed="Rates problems from low to transformative. A transformative opportunity could change an entire industry. High value problems are worth significant investment. Low value might not be worth solving at all.",
        example="'Making slightly faster toasters' = low value. 'Making food stay fresh 10x longer' = transformative (changes supply chains, reduces waste, feeds more people).",
        related_terms=["impact", "opportunity"],
        complexity_level=1
    ),
    "extraction confidence": PWSTerm(
        term="Extraction Confidence",
        plain_english="How sure we are that this opportunity is real and correctly identified.",
        detailed="When AI extracts opportunities from conversations, it assigns a confidence score. High confidence means clear evidence and strong signals. Low confidence means we're guessing.",
        example="If you explicitly said 'Customers told me they'd pay $100 for this', confidence is high. If we inferred a problem from vague complaints, confidence is lower.",
        related_terms=["validation", "evidence"],
        complexity_level=2
    ),
}

# Confusion signals - phrases that suggest the user is lost
CONFUSION_SIGNALS = [
    r"what (do you mean|does that mean|is)",
    r"i don't (understand|get|follow)",
    r"can you (explain|clarify|tell me more)",
    r"what's (a|an|the)",
    r"huh\??",
    r"confused",
    r"lost",
    r"not sure (what|how|why)",
    r"help me understand",
    r"in simpler terms",
    r"plain english",
    r"eli5",
    r"dumb it down",
]

# Expert signals - phrases that suggest they know what they're doing
EXPERT_SIGNALS = [
    r"reverse salient",
    r"s-curve (analysis|position|timing)",
    r"dikw|ackoff",
    r"jobs to be done|jtbd framework",
    r"validation (methodology|framework)",
    r"trending to (the )?absurd",
    r"cynefin",
    r"lean canvas",
    r"assumptions map",
]

# =============================================================================
# ONBOARDING STATE
# =============================================================================

@dataclass
class OnboardingState:
    """Tracks a user's onboarding progress."""
    user_id: str
    expertise_level: ExpertiseLevel = ExpertiseLevel.NEWCOMER
    concepts_seen: Dict[str, datetime] = field(default_factory=dict)
    concepts_understood: List[str] = field(default_factory=list)
    confusion_count: int = 0
    expert_signals_count: int = 0
    message_count: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_help_shown: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "expertise_level": self.expertise_level.value,
            "concepts_seen": {k: v.isoformat() for k, v in self.concepts_seen.items()},
            "concepts_understood": self.concepts_understood,
            "confusion_count": self.confusion_count,
            "expert_signals_count": self.expert_signals_count,
            "message_count": self.message_count,
            "first_seen": self.first_seen.isoformat(),
            "last_help_shown": self.last_help_shown.isoformat() if self.last_help_shown else None
        }

# In-memory state cache (would be persisted to Supabase in production)
_onboarding_cache: Dict[str, OnboardingState] = {}

def get_onboarding_state(user_id: str) -> OnboardingState:
    """Get or create onboarding state for a user."""
    if user_id not in _onboarding_cache:
        _onboarding_cache[user_id] = OnboardingState(user_id=user_id)
    return _onboarding_cache[user_id]

def update_onboarding_state(user_id: str, state: OnboardingState):
    """Update the onboarding state."""
    _onboarding_cache[user_id] = state

# =============================================================================
# CONFUSION DETECTION
# =============================================================================

def detect_confusion_signals(message: str) -> Tuple[bool, List[str]]:
    """
    Detect if the user seems confused based on their message.

    Returns:
        Tuple of (is_confused, matched_patterns)
    """
    message_lower = message.lower()
    matches = []

    for pattern in CONFUSION_SIGNALS:
        if re.search(pattern, message_lower):
            matches.append(pattern)

    return len(matches) > 0, matches

def detect_expert_signals(message: str) -> Tuple[bool, List[str]]:
    """
    Detect if the user shows expert-level knowledge.

    Returns:
        Tuple of (is_expert, matched_patterns)
    """
    message_lower = message.lower()
    matches = []

    for pattern in EXPERT_SIGNALS:
        if re.search(pattern, message_lower):
            matches.append(pattern)

    return len(matches) > 0, matches

def update_expertise_level(state: OnboardingState) -> ExpertiseLevel:
    """
    Update expertise level based on signals over time.
    """
    # Calculate signal ratio
    if state.message_count < 3:
        return ExpertiseLevel.NEWCOMER

    confusion_ratio = state.confusion_count / state.message_count
    expert_ratio = state.expert_signals_count / state.message_count

    # Classify
    if expert_ratio > 0.15 or state.expert_signals_count >= 3:
        return ExpertiseLevel.EXPERT
    elif expert_ratio > 0.05 or len(state.concepts_understood) >= 5:
        return ExpertiseLevel.PRACTITIONER
    elif state.message_count >= 10 and confusion_ratio < 0.2:
        return ExpertiseLevel.FAMILIAR
    else:
        return ExpertiseLevel.NEWCOMER

# =============================================================================
# CONTEXTUAL TOOLTIPS
# =============================================================================

def find_terms_in_text(text: str) -> List[str]:
    """Find PWS terms mentioned in text."""
    text_lower = text.lower()
    found = []

    # Direct term matches
    term_patterns = {
        "pws": r"\bpws\b|problems? worth solving",
        "reverse salient": r"reverse salient",
        "jtbd": r"\bjtbd\b|jobs? to be done",
        "tta": r"\btta\b|trending to (the )?absurd",
        "s-curve": r"s-curve|s curve",
        "dikw": r"\bdikw\b|ackoff.?s? pyramid",
        "red team": r"red team",
        "validation": r"\bvalidat(e|ion|ing)\b",
        "domain": r"\bdomain\b",
        "opportunity bank": r"opportunity bank|bank of opportunities",
        "value potential": r"value potential",
        "extraction confidence": r"extraction confidence|confidence score",
    }

    for term, pattern in term_patterns.items():
        if re.search(pattern, text_lower):
            found.append(term)

    return found

def get_contextual_tooltip(
    term: str,
    user_state: OnboardingState,
    format: str = "inline"  # "inline", "card", "modal"
) -> Optional[Dict[str, Any]]:
    """
    Get a contextual tooltip for a PWS term.

    Returns None if:
    - User already understands this concept
    - User is an expert (doesn't need help)
    - We showed help too recently (avoid spam)

    Args:
        term: The PWS term to explain
        user_state: User's onboarding state
        format: How to display ("inline", "card", "modal")

    Returns:
        Tooltip data or None if not needed
    """
    if term not in PWS_GLOSSARY:
        return None

    pws_term = PWS_GLOSSARY[term]

    # Skip if user already understands
    if term in user_state.concepts_understood:
        return None

    # Skip if user is expert level
    if user_state.expertise_level == ExpertiseLevel.EXPERT:
        return None

    # Skip if we showed help very recently (within 2 minutes)
    if user_state.last_help_shown:
        if datetime.utcnow() - user_state.last_help_shown < timedelta(minutes=2):
            return None

    # Mark as seen
    user_state.concepts_seen[term] = datetime.utcnow()

    # Build tooltip based on expertise level
    if user_state.expertise_level == ExpertiseLevel.NEWCOMER:
        # Full explanation for newcomers
        return {
            "term": pws_term.term,
            "explanation": pws_term.plain_english,
            "example": pws_term.example,
            "format": format,
            "show_learn_more": True,
            "detailed": pws_term.detailed
        }
    elif user_state.expertise_level == ExpertiseLevel.FAMILIAR:
        # Shorter reminder
        return {
            "term": pws_term.term,
            "explanation": pws_term.plain_english,
            "format": "inline",
            "show_learn_more": False
        }
    else:
        # Just a quick hint
        return {
            "term": pws_term.term,
            "explanation": pws_term.plain_english,
            "format": "inline",
            "show_learn_more": False
        }

def format_tooltip_html(tooltip: Dict[str, Any]) -> str:
    """Format a tooltip as inline HTML for chat."""
    if not tooltip:
        return ""

    term = tooltip.get("term", "")
    explanation = tooltip.get("explanation", "")
    example = tooltip.get("example", "")

    if tooltip.get("format") == "card":
        return f"""
<div style="background: #f0f7ff; border-left: 4px solid #3498db; padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;">
    <div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px;">💡 {term}</div>
    <div style="color: #555; font-size: 14px;">{explanation}</div>
    {f'<div style="color: #777; font-size: 13px; margin-top: 8px; font-style: italic;">Example: {example}</div>' if example else ''}
</div>
"""
    else:
        # Inline format
        return f"💡 *{term}*: {explanation}"

def mark_concept_learned(user_id: str, concept: str):
    """Mark a concept as understood by the user."""
    state = get_onboarding_state(user_id)
    if concept not in state.concepts_understood:
        state.concepts_understood.append(concept)
    update_onboarding_state(user_id, state)

# =============================================================================
# PROGRESSIVE WELCOME
# =============================================================================

def get_progressive_welcome(
    user_id: str,
    bot_name: str = "Lawrence",
    show_onboarding_offer: bool = True
) -> Dict[str, Any]:
    """
    Get a welcome message appropriate for the user's expertise level.

    First-time users get a warm, jargon-free introduction with onboarding offer.
    Returning users get a quick greeting.
    Experts get straight to business.

    Returns:
        Dict with 'message', 'show_onboarding_buttons', and 'expertise_level'
    """
    state = get_onboarding_state(user_id)

    if state.expertise_level == ExpertiseLevel.NEWCOMER and state.message_count == 0:
        # First-time user - warm, explanatory welcome
        message = f"""🧠 **Welcome to {bot_name}!**

I'm your thinking partner for discovering **problems worth solving** — the kind of challenges that, once solved, create real value for real people.

---

**What I help you do:**

🔍 **Explore Ideas** — Tell me about an industry, technology, or challenge you're curious about. I'll help you dig deeper than surface-level thinking.

💡 **Find Hidden Opportunities** — Most valuable problems are hiding in plain sight. I use proven frameworks to reveal what others miss.

🎯 **Focus Your Energy** — Not every problem is worth your time. I'll help you identify which ones matter and why.

---

**How we'll work together:**

1. **You share** what's on your mind — an idea, a frustration, a market you're curious about
2. **I ask questions** to understand better and challenge assumptions
3. **We explore together** — I'll introduce frameworks like "Jobs to Be Done" or "Reverse Salients" when they're useful (and explain them in plain English)
4. **You leave with clarity** — knowing which problems are worth pursuing

---

*I noticed you're new here. Want a quick 2-minute tour of how this works?*"""

        return {
            "message": message,
            "show_onboarding_buttons": show_onboarding_offer,
            "expertise_level": state.expertise_level.value,
            "is_first_time": True
        }

    elif state.expertise_level == ExpertiseLevel.NEWCOMER:
        # Newcomer, but not first message
        return {
            "message": f"""🧠 **{bot_name} here.**

Ready to explore? Tell me what you're thinking about — an idea, a problem, or something you're curious about.

*I'll explain any unfamiliar terms as we go.*""",
            "show_onboarding_buttons": False,
            "expertise_level": state.expertise_level.value,
            "is_first_time": False
        }

    elif state.expertise_level == ExpertiseLevel.FAMILIAR:
        # Knows the basics
        return {
            "message": f"""🧠 **Welcome back!**

What problem space are you exploring today?""",
            "show_onboarding_buttons": False,
            "expertise_level": state.expertise_level.value,
            "is_first_time": False
        }

    elif state.expertise_level == ExpertiseLevel.PRACTITIONER:
        # Regular user
        return {
            "message": f"""🧠 **Good to see you!** What are we working on today?""",
            "show_onboarding_buttons": False,
            "expertise_level": state.expertise_level.value,
            "is_first_time": False
        }

    else:
        # Expert - minimal
        return {
            "message": f"""🧠 **{bot_name} ready.** What's the focus?""",
            "show_onboarding_buttons": False,
            "expertise_level": state.expertise_level.value,
            "is_first_time": False
        }


def get_onboarding_tour_steps() -> List[Dict[str, Any]]:
    """
    Get the interactive onboarding tour steps.

    Each step explains a key concept with an example.
    """
    return [
        {
            "step": 1,
            "title": "🎯 Finding Problems Worth Solving",
            "content": """**Not all problems are created equal.**

Some problems, when solved, unlock massive value. Others... not so much.

**Example:**
- ❌ "Make a faster spreadsheet" — incremental improvement
- ✅ "Why do teams miscommunicate during handoffs?" — addressing root cause

The second question might lead to a transformative solution. The first just makes a slightly better tool.

**Key question to ask:** "If this problem disappeared tomorrow, how many people would notice? How much would their lives improve?"
""",
            "concept": "pws"
        },
        {
            "step": 2,
            "title": "🔓 The Bottleneck Principle",
            "content": """**Every system has ONE constraint holding everything else back.**

Find it, solve it, and everything improves. We call this a "reverse salient" — borrowed from military strategy.

**Example:**
For years, electric cars struggled. The reverse salient? **Battery technology.**
- Motors? Fine.
- Charging infrastructure? Could be built.
- Batteries? Too heavy, too expensive, too slow to charge.

Tesla bet everything on batteries. Once that constraint broke, the whole industry took off.

**Ask yourself:** "What's the one thing that, if fixed, would unlock everything else?"
""",
            "concept": "reverse salient"
        },
        {
            "step": 3,
            "title": "💼 Jobs to Be Done",
            "content": """**People don't buy products. They hire them to do a job.**

Understanding the real "job" leads to better solutions.

**Example:**
People don't buy drills because they want drills.
They don't even want holes.
They want to **hang a picture** — to make their home feel personal.

The "job" isn't drilling. It's creating a sense of home.

**This changes everything:**
- Maybe they don't need a drill at all
- Maybe a better solution is command strips
- Maybe the real opportunity is in the "decorating" journey

**Ask:** "What progress is this person trying to make in their life?"
""",
            "concept": "jtbd"
        }
    ]


def mark_onboarding_skipped(user_id: str):
    """Mark that user chose to skip onboarding."""
    state = get_onboarding_state(user_id)
    state.expertise_level = ExpertiseLevel.FAMILIAR  # Assume some familiarity
    state.concepts_understood.extend(["pws", "jtbd", "reverse salient"])  # Don't show basic tooltips
    update_onboarding_state(user_id, state)


def mark_onboarding_completed(user_id: str):
    """Mark that user completed onboarding tour."""
    state = get_onboarding_state(user_id)
    state.concepts_understood.extend(["pws", "jtbd", "reverse salient"])
    # Keep as newcomer until they show expertise
    update_onboarding_state(user_id, state)

# =============================================================================
# SMART HELP TIMING
# =============================================================================

def should_show_concept_help(
    user_id: str,
    message: str,
    bot_response: str
) -> Optional[Dict[str, Any]]:
    """
    Determine if we should show concept help based on:
    - User's confusion signals
    - Terms mentioned in bot response
    - User's expertise level
    - How recently we showed help

    Returns:
        Help content to show, or None
    """
    state = get_onboarding_state(user_id)
    state.message_count += 1

    # Check for confusion
    is_confused, confusion_patterns = detect_confusion_signals(message)
    if is_confused:
        state.confusion_count += 1

    # Check for expertise
    is_expert, expert_patterns = detect_expert_signals(message)
    if is_expert:
        state.expert_signals_count += 1

    # Update expertise level
    state.expertise_level = update_expertise_level(state)
    update_onboarding_state(user_id, state)

    # If user is explicitly confused, offer help
    if is_confused and state.expertise_level != ExpertiseLevel.EXPERT:
        # Find what terms might be confusing
        terms_in_response = find_terms_in_text(bot_response)
        if terms_in_response:
            # Offer to explain the most relevant term
            for term in terms_in_response:
                tooltip = get_contextual_tooltip(term, state, format="card")
                if tooltip:
                    state.last_help_shown = datetime.utcnow()
                    update_onboarding_state(user_id, state)
                    return {
                        "type": "tooltip",
                        "content": tooltip,
                        "trigger": "confusion_detected",
                        "terms_available": terms_in_response
                    }

    # Proactive help for newcomers - explain first occurrence of terms
    if state.expertise_level == ExpertiseLevel.NEWCOMER:
        terms_in_response = find_terms_in_text(bot_response)
        for term in terms_in_response:
            if term not in state.concepts_seen:
                tooltip = get_contextual_tooltip(term, state, format="inline")
                if tooltip:
                    state.last_help_shown = datetime.utcnow()
                    update_onboarding_state(user_id, state)
                    return {
                        "type": "inline_tip",
                        "content": tooltip,
                        "trigger": "first_encounter"
                    }

    return None

# =============================================================================
# ONBOARDING WIZARD STEPS
# =============================================================================

def get_onboarding_step(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the next onboarding step for a newcomer.

    Returns None if onboarding is complete or not needed.
    """
    state = get_onboarding_state(user_id)

    # Only for newcomers in their first few messages
    if state.expertise_level != ExpertiseLevel.NEWCOMER:
        return None

    if state.message_count >= 5:
        return None

    # Progressive steps
    steps = [
        {
            "step": 1,
            "title": "What's a Problem Worth Solving?",
            "content": "Not every problem is worth your time. PWS helps you find the ones that matter - where solving them creates real value.",
            "action": "Got it! Let's explore.",
            "concept": "pws"
        },
        {
            "step": 2,
            "title": "The Bottleneck Principle",
            "content": "Look for 'reverse salients' - the one constraint holding everything back. Fix that, and everything else improves.",
            "action": "Show me an example",
            "concept": "reverse salient"
        },
        {
            "step": 3,
            "title": "Think About Jobs, Not Products",
            "content": "People hire products to do a job. Understanding the real job leads to better solutions.",
            "action": "Makes sense",
            "concept": "jtbd"
        }
    ]

    # Find next step
    for step in steps:
        if step["concept"] not in state.concepts_seen:
            return step

    return None

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # State management
    "OnboardingState",
    "ExpertiseLevel",
    "get_onboarding_state",
    "update_onboarding_state",
    # Detection
    "detect_confusion_signals",
    "detect_expert_signals",
    "find_terms_in_text",
    # Tooltips
    "get_contextual_tooltip",
    "format_tooltip_html",
    "mark_concept_learned",
    # Help timing
    "should_show_concept_help",
    # Progressive onboarding
    "get_progressive_welcome",
    "get_onboarding_step",
    "get_onboarding_tour_steps",
    "mark_onboarding_skipped",
    "mark_onboarding_completed",
    # Data
    "PWS_GLOSSARY",
]
