"""
Larry Mode Engine — Ask-Tell Dial Computation + Prompt Assembly

Computes the mode position (0.0 = Investigate, 1.0 = Insight) from weighted
signals and assembles the system prompt from modular .md skill files.

Files are read once at import time and cached in module-level variables.
Only the assembly (which files to include) changes per-turn.
"""

import os
import re
import logging
from typing import Optional

logger = logging.getLogger("mindrian")

# ---------------------------------------------------------------------------
# 1. Load and cache skill files at import time
# ---------------------------------------------------------------------------

_SKILL_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts", "larry_skill")

_FILE_CACHE: dict[str, str] = {}


def _load_file(filename: str) -> str:
    """Load a skill file from disk, caching in memory."""
    if filename in _FILE_CACHE:
        return _FILE_CACHE[filename]
    path = os.path.join(_SKILL_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        _FILE_CACHE[filename] = content
        return content
    except FileNotFoundError:
        logger.warning("Larry skill file not found: %s", path)
        return ""


# Pre-load all files at import time
_SYSTEM_PROMPT_V2 = _load_file("SYSTEM_PROMPT_V2.md")
_SKILL_OVERVIEW = _load_file("SKILL.md")
_STYLE_GUIDE = _load_file("STYLE_GUIDE.md")
_LEXICON = _load_file("LEXICON.md")
_INVESTIGATIVE_MODE = _load_file("INVESTIGATIVE_MODE.md")
_INSIGHT_MODE = _load_file("INSIGHT_MODE.md")
_MODE_CALIBRATION = _load_file("MODE_CALIBRATION.md")
_FRAMEWORK_CHAINS = _load_file("FRAMEWORK_CHAINS.md")

# ---------------------------------------------------------------------------
# 2. Intent → Mode position mapping
# ---------------------------------------------------------------------------

INTENT_MODE_MAP: dict[str, float] = {
    "convergent": 0.85,
    "analytical": 0.60,
    "factual": 0.75,
    "exploratory": 0.25,
}

# ---------------------------------------------------------------------------
# 3. Explicit mode intent patterns (regex-based)
# ---------------------------------------------------------------------------

MODE_INTENT_PATTERNS: dict[str, list[str]] = {
    "insight_direct": [
        r"what do you think",
        r"your (take|opinion|view|perspective|honest assessment)",
        r"what would you do",
        r"give me (the answer|your answer|an answer)",
        r"just tell me",
        r"stop asking questions",
        r"bottom line",
        r"summarize",
        r"what am i missing",
        r"give me (insights?|advice|recommendations?)",
        r"your honest",
    ],
    "investigate_direct": [
        r"help me (think|figure|work|reason)",
        r"challenge (this|me|my|that)",
        r"poke holes",
        r"play devil",
        r"what('s| is) wrong with",
        r"stress.?test",
        r"what should i (be )?(asking|thinking|considering)",
    ],
    "blend_direct": [
        r"am i on the right track",
        r"does this make sense",
        r"how does this (look|sound|compare)",
        r"what do you see",
    ],
}


def classify_mode_intent(message: str) -> Optional[float]:
    """
    Check for explicit mode triggers in the user's message.
    Returns an override dial position or None if no explicit trigger found.
    """
    msg_lower = message.lower().strip()

    for pattern in MODE_INTENT_PATTERNS["insight_direct"]:
        if re.search(pattern, msg_lower):
            return 0.90

    for pattern in MODE_INTENT_PATTERNS["investigate_direct"]:
        if re.search(pattern, msg_lower):
            return 0.15

    for pattern in MODE_INTENT_PATTERNS["blend_direct"]:
        if re.search(pattern, msg_lower):
            return 0.50

    return None


# ---------------------------------------------------------------------------
# 4. Mode position computation
# ---------------------------------------------------------------------------

# Phase-based default curve: turn → default dial position
_PHASE_CURVE = [
    (0, 0.15),   # Turn 0-1: Investigate-heavy
    (2, 0.15),   # Turn 2: Still investigating
    (3, 0.30),   # Turn 3: Diagnosing
    (4, 0.30),   # Turn 4: Diagnosing
    (5, 0.55),   # Turn 5: Blend zone
    (6, 0.55),   # Turn 6: Blend zone
    (7, 0.60),   # Turn 7: Blend leaning insight
    (8, 0.75),   # Turn 8+: Insight-heavy
]

# Problem type → starting dial position
_PROBLEM_TYPE_START = {
    "un-defined": 0.15,
    "undefined": 0.15,
    "ill-defined": 0.35,
    "illdefined": 0.35,
    "well-defined": 0.65,
    "welldefined": 0.65,
    "wicked": 0.45,
}


def _phase_default(turn_count: int) -> float:
    """Get the phase-based default dial position for a given turn count."""
    for turn, position in reversed(_PHASE_CURVE):
        if turn_count >= turn:
            return position
    return 0.15


def compute_mode_position(
    intent_signal: float,
    turn_count: int,
    problem_type: str = "",
    has_prior_sessions: bool = False,
    saturation_detected: bool = False,
    explicit_override: Optional[float] = None,
) -> float:
    """
    Compute the Ask-Tell Dial position from weighted signals.

    Returns a float from 0.0 (full investigate) to 1.0 (full insight).

    Signal weights:
        - Phase curve (turn-based default): 30%
        - Intent signal (from context_engine): 40%
        - Problem type: 15%
        - Prior session / saturation adjustments: 15%

    Explicit override (from classify_mode_intent) takes precedence when present.
    """
    # Explicit override from user's words takes highest priority
    if explicit_override is not None:
        return max(0.0, min(1.0, explicit_override))

    # Saturation forces convergence
    if saturation_detected:
        return 0.85

    # 1. Phase-based default (30%)
    phase_pos = _phase_default(turn_count)

    # 2. Intent signal (40%) — already a 0-1 value
    intent_pos = max(0.0, min(1.0, intent_signal))

    # 3. Problem type (15%)
    problem_pos = _PROBLEM_TYPE_START.get(
        problem_type.lower().strip().replace(" ", ""), 0.45
    )

    # 4. Session / context adjustments (15%)
    context_pos = 0.45  # neutral default
    if has_prior_sessions:
        context_pos = 0.60  # returning users lean insight

    # Weighted combination
    position = (
        0.30 * phase_pos
        + 0.40 * intent_pos
        + 0.15 * problem_pos
        + 0.15 * context_pos
    )

    return max(0.0, min(1.0, position))


# ---------------------------------------------------------------------------
# 5. Mode instruction generation
# ---------------------------------------------------------------------------

def mode_instruction(position: float) -> str:
    """
    Convert a numeric dial position to a behavioral instruction addendum
    appended at the end of the system prompt.
    """
    if position < 0.20:
        return (
            "\n\n[MODE: DEEP INVESTIGATE — Dial at {:.0%} Insight]\n"
            "You are in full Investigative Mode. Ask ONE question per response. "
            "Max 5 sentences. No framework names. No direct advice. "
            "Help the user discover the problem themselves through questions. "
            "Classify the problem silently — never announce it."
        ).format(position)

    elif position < 0.35:
        return (
            "\n\n[MODE: INVESTIGATE — Dial at {:.0%} Insight]\n"
            "You are in Investigative Mode. Lead with questions. "
            "Max 5 sentences. One question per response. "
            "You may offer a brief reframe before your question. "
            "No frameworks yet — earn the right first."
        ).format(position)

    elif position < 0.55:
        return (
            "\n\n[MODE: BLEND (Investigate-leaning) — Dial at {:.0%} Insight]\n"
            "You are in the Blend Zone, leaning investigative. "
            "40% asking, 60% telling. Questions informed by insights. "
            "You may name one framework if it directly serves the conversation. "
            "Cross-domain connections are available if relevant."
        ).format(position)

    elif position < 0.70:
        return (
            "\n\n[MODE: BLEND (Insight-leaning) — Dial at {:.0%} Insight]\n"
            "You are in the Blend Zone, leaning toward insight delivery. "
            "Lead with an observation or pattern, then check if it resonates. "
            "Frameworks can be named and applied. Cross-domain connections encouraged. "
            "End with a focused question, not open-ended exploration."
        ).format(position)

    elif position < 0.85:
        return (
            "\n\n[MODE: INSIGHT — Dial at {:.0%} Insight]\n"
            "You are in Insight Mode. Lead with your take. "
            "Use the Evidence → Insight → Warning structure. "
            "Deliver direct recommendations. Name frameworks when useful. "
            "End with a clear next step or specific homework. "
            "One question maximum — and it should be focused, not exploratory."
        ).format(position)

    else:
        return (
            "\n\n[MODE: FULL INSIGHT — Dial at {:.0%} Insight]\n"
            "You are in Full Insight / Delivery Mode. The user wants answers. "
            "Be direct. Lead with your recommendation. "
            "Give structure when helpful. Provide evidence and warnings. "
            "No Socratic questions — deliver your honest assessment. "
            "Zero resistance. Respect their time."
        ).format(position)


# ---------------------------------------------------------------------------
# 6. Prompt assembly
# ---------------------------------------------------------------------------

def assemble_larry_prompt(
    mode_position: float,
    turn_count: int,
    problem_type: str = "",
    saturation: bool = False,
    has_prior_sessions: bool = False,
) -> str:
    """
    Assemble the full Larry system prompt from modular skill files.

    Always includes:
        - SYSTEM_PROMPT_V2.md  (base prompt)
        - SKILL.md             (Ask-Tell Dial overview)
        - STYLE_GUIDE.md       (voice and tone rules)
        - LEXICON.md           (vocabulary and forbidden phrases)

    Conditionally includes based on mode_position:
        - mode < 0.35:    INVESTIGATIVE_MODE.md
        - mode > 0.70:    INSIGHT_MODE.md
        - 0.35 - 0.70:    MODE_CALIBRATION.md + FRAMEWORK_CHAINS.md

    Appends mode_instruction() addendum at the end.
    """
    parts = []

    # Always-included core files
    parts.append(_SYSTEM_PROMPT_V2)
    parts.append("\n\n---\n\n")
    parts.append(_SKILL_OVERVIEW)
    parts.append("\n\n---\n\n")
    parts.append(_STYLE_GUIDE)
    parts.append("\n\n---\n\n")
    parts.append(_LEXICON)

    # Mode-conditional files
    if mode_position < 0.35:
        parts.append("\n\n---\n\n")
        parts.append(_INVESTIGATIVE_MODE)
    elif mode_position > 0.70:
        parts.append("\n\n---\n\n")
        parts.append(_INSIGHT_MODE)
    else:
        # Blend zone
        parts.append("\n\n---\n\n")
        parts.append(_MODE_CALIBRATION)
        parts.append("\n\n---\n\n")
        parts.append(_FRAMEWORK_CHAINS)

    # Context hints
    context_hints = []
    if saturation:
        context_hints.append(
            "SATURATION DETECTED: The conversation is going circular. "
            "Synthesize and converge. Do not ask more exploratory questions."
        )
    if has_prior_sessions:
        context_hints.append(
            "RETURNING USER: This user has prior session history. "
            "You may reference past work casually if relevant."
        )
    if problem_type:
        context_hints.append(
            f"PROBLEM TYPE HINT: Classified as '{problem_type}' (use internally, never announce)."
        )

    if context_hints:
        parts.append("\n\n[CONTEXT SIGNALS]\n")
        for hint in context_hints:
            parts.append(f"- {hint}\n")

    # Mode instruction addendum (always last)
    parts.append(mode_instruction(mode_position))

    return "".join(parts)
