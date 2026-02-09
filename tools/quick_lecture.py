"""
Larry Teach Me — Cognitive Intervention Engine
===============================================

NOT content delivery. This is a cognitive intervention.
60-120 seconds that forces the user to think differently.

THE ONE RULE: If the user feels comfortable after listening, it failed.

Pipeline:
1. DIAGNOSE - Problem type + Thinking error + ONE framework
2. GATE - Should we even teach? (Refuse if inappropriate)
3. RETRIEVE - Neo4j framework + FileSearch examples
4. GENERATE - Script with Larry Lexicon
5. VALIDATE - Must have interruption, problem naming, no banned words
6. VOICE - ElevenLabs audio generation

Usage:
    from tools.quick_lecture import larry_teach_me

    result = await larry_teach_me(
        query="How do I scale my consulting practice?",
        user_history=[]
    )
    # Returns: {audio_bytes, transcript, diagnosis, thinking_exercise, cta}
"""

import os
import re
import asyncio
import logging
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger("larry_teach_me")

# ============================================================================
# CONFIGURATION
# ============================================================================

ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "SGh5MKvZcSYNF0SZXlAg")  # Larry voice
FILESEARCH_STORE_ID = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"

# ============================================================================
# THE LARRY LEXICON — Words That Do The Thinking
# ============================================================================

LARRY_LEXICON = {
    # Opening interruptions (must appear in first 10 seconds)
    "opening_interruptions": [
        "Let me stop you right there...",
        "Before we go any further...",
        "I'm going to interrupt you for a second...",
        "The way you're asking that tells me something important...",
        "I'm less interested in your answer than in why you asked it that way...",
        "That question sounds reasonable — and that's exactly the problem.",
    ],

    # Reframing moves
    "reframing_moves": [
        "The real question isn't X. It's Y.",
        "You think you're asking about ___, but you're actually struggling with ___.",
        "That's the symptom. Let's talk about the disease.",
        "You're solving at the wrong level.",
        "That framing makes the problem unsolvable.",
        "You've already constrained the answer without realizing it.",
    ],

    # Problem-type markers
    "problem_markers": [
        "This is an ill-defined problem, which means...",
        "You don't have a problem yet — you have a discomfort.",
        "This looks well-defined, but it isn't.",
        "This is a wicked problem. If you're looking for an answer, you're already stuck.",
        "You're treating a complex problem like it's complicated.",
    ],

    # Framework introduction patterns (not academic)
    "framework_intros": [
        "We have a way of thinking about this...",
        "There's a simple framework that helps here...",
        "Here's the distinction that matters...",
        "This is where most people get lost...",
        "Let me give you a lens to look at this differently...",
    ],

    # Thinking exercise prompts
    "exercise_prompts": [
        "Here's what I want you to do next...",
        "Take a piece of paper...",
        "Write this down...",
        "Describe it without using industry jargon...",
        "Kill one assumption and see what breaks...",
        "Rewrite the question three different ways...",
    ],

    # Closing commands (motion, not comfort)
    "closing_commands": [
        "Do that first.",
        "Start there.",
        "Don't move forward until you've done that.",
        "That's your next move.",
        "Go.",
    ],

    # BANNED WORDS (hard filter)
    "banned_words": [
        "journey", "unpack", "amazing question", "let's explore",
        "best practice", "holistic", "leverage", "ideate",
        "that's a great question", "let's unpack", "good luck",
    ],
}

# ============================================================================
# THINKING ERROR DETECTION
# ============================================================================

THINKING_ERRORS = {
    "jumping_to_solutions": {
        "signals": ["should I use", "how to implement", "best tool for", "which platform",
                    "what software", "how do I build", "which framework"],
        "framework": "Problem Types Taxonomy",
        "reframe": "solution_before_problem",
        "larry_instinct": "You're jumping to solutions. That's an answer to a question you haven't earned yet.",
    },
    "staying_abstract": {
        "signals": ["in general", "theoretically", "how does", "what is the concept",
                    "explain how", "what's the theory", "philosophically"],
        "framework": "Issue Tree",
        "reframe": "demand_specificity",
        "larry_instinct": "Give me a real case. Abstractions don't innovate — people with problems do.",
    },
    "presentism": {
        "signals": ["right now", "currently", "the market is", "people want",
                    "today's customers", "current trends", "what's working now"],
        "framework": "Trending to the Absurd",
        "reframe": "future_not_present",
        "larry_instinct": "You're designing for a world that won't exist. Take that trend and push it to its logical extreme.",
    },
    "complex_as_complicated": {
        "signals": ["the right answer", "best practice", "proven method", "what works",
                    "the correct approach", "industry standard", "what everyone does"],
        "framework": "Cynefin Framework",
        "reframe": "probe_not_analyze",
        "larry_instinct": "This isn't an engineering problem. Stop looking for a formula.",
    },
    "optimizing_wrong_thing": {
        "signals": ["improve our", "optimize", "more efficient", "scale up",
                    "increase our", "better metrics", "grow faster"],
        "framework": "Reverse Salients",
        "reframe": "wrong_surface",
        "larry_instinct": "The breakthrough isn't where you're looking. You're polishing the wrong surface.",
    },
    "fear_of_undefined": {
        "signals": ["not sure where to start", "too vague", "need clarity first", "risky",
                    "what if it fails", "need more data", "can't decide until"],
        "framework": "Un-Defined Problem Navigation",
        "reframe": "embrace_uncertainty",
        "larry_instinct": "Un-defined is where breakthroughs live. Your discomfort is the data.",
    },
}

# ============================================================================
# PROBLEM CLASSIFICATION MATRIX (Hardcoded fallback)
# ============================================================================

CLASSIFICATION_MATRIX = {
    "well_defined_disguised": {
        "signals": ["how do I", "what's the best way to", "steps to"],
        "problem_type": "well-defined (disguised)",
        "larry_instinct": "You already know the answer. Why are you avoiding it?",
    },
    "ill_defined": {
        "signals": ["too many options", "can't decide between", "which direction", "should I X or Y"],
        "problem_type": "ill-defined",
        "larry_instinct": "You're choosing between solutions before you understand the problem.",
    },
    "wicked_or_undefined": {
        "signals": ["nobody has solved", "never been done", "completely new", "unprecedented"],
        "problem_type": "wicked/un-defined",
        "larry_instinct": "Good. That means you're finally looking at the right question.",
    },
    "false_binary": {
        "signals": ["should I X or Y", "either this or that", "A vs B", "choose between"],
        "problem_type": "false binary",
        "larry_instinct": "You're asking the wrong question entirely. Why only those two options?",
    },
    "solution_addiction": {
        "signals": ["we tried everything", "nothing works", "already attempted", "keeps failing"],
        "problem_type": "solution addiction",
        "larry_instinct": "You tried everything except understanding what's actually broken.",
    },
    "premature_optimization": {
        "signals": ["what's the best way", "most efficient method", "optimize for", "maximize"],
        "problem_type": "premature optimization",
        "larry_instinct": "Best way to do what, exactly? Define the problem first.",
    },
}

# ============================================================================
# LARRY'S SIX FRAMEWORKS (Only ONE per lecture)
# ============================================================================

LARRYS_FRAMEWORKS = {
    "Problem Types Taxonomy": {
        "description": "Un-defined / Ill-defined / Well-defined classification",
        "signature_line": "You can't solve what you haven't defined.",
        "when_to_deploy": "User hasn't classified their problem",
    },
    "Portfolio (Now/New/Next)": {
        "description": "Time-horizon portfolio for innovation investments",
        "signature_line": "You're spending all your energy on Now. Where's your Next?",
        "when_to_deploy": "User is stuck in present execution",
    },
    "Presentism / TTA": {
        "description": "Projecting current constraints onto future possibilities",
        "signature_line": "You're designing for a world that won't exist.",
        "when_to_deploy": "User projects current constraints onto future",
    },
    "Reverse Salients": {
        "description": "Finding bottlenecks that hold back system progress",
        "signature_line": "The breakthrough isn't where you're looking.",
        "when_to_deploy": "User is optimizing in the wrong place",
    },
    "Wicked vs Well-Defined": {
        "description": "Recognizing problems that resist traditional solving",
        "signature_line": "This problem doesn't have an answer. It has a response.",
        "when_to_deploy": "User wants a clean answer to a messy problem",
    },
    "Cynefin Framework": {
        "description": "Complex vs complicated distinction",
        "signature_line": "You're treating a complex problem like it's complicated.",
        "when_to_deploy": "User seeks formula for problem that needs probing",
    },
}

# ============================================================================
# PROBLEM-TYPE TEMPLATES
# ============================================================================

PROBLEM_TEMPLATES = {
    "un-defined": {
        "opening_pattern": "You don't have a problem yet. You have a discomfort. Let's figure out what it's actually pointing at...",
        "reframe_direction": "Push from symptom to structure",
        "frameworks": ["Domain Exploration", "Trending to the Absurd"],
        "example_types": ["Penicillin discovery", "Post-it Notes", "Early internet applications"],
        "exercise_pattern": "Describe your discomfort without using the word 'problem.' What's the tension? What doesn't fit?",
    },
    "ill-defined": {
        "opening_pattern": "You have the shape of a problem but not the edges. That's actually a better position than you think...",
        "reframe_direction": "Show the gap between framing and structure",
        "frameworks": ["Problem Types Taxonomy", "Issue Trees", "Beautiful Questions"],
        "example_types": ["Marconi's wireless", "Dyson vacuum", "Southwest Airlines"],
        "exercise_pattern": "Rewrite your problem three different ways. Which version makes you most uncomfortable? That's probably the right one.",
    },
    "well-defined (disguised)": {
        "opening_pattern": "You think this is well-defined. It isn't. Let me show you what you're missing...",
        "reframe_direction": "Surface hidden assumptions",
        "frameworks": ["Reverse Salients", "Cynefin"],
        "example_types": ["Kodak failure", "Blackberry decline", "Blockbuster collapse"],
        "exercise_pattern": "List the three assumptions that make your solution feel obvious. Now kill one. What happens to your plan?",
    },
    "wicked": {
        "opening_pattern": "Stop looking for a solution. This problem doesn't have one. It has a response. And responses need to evolve...",
        "reframe_direction": "Legitimize the mess",
        "frameworks": ["Wicked Problem Characteristics", "Cynefin Chaotic/Complex"],
        "example_types": ["Climate policy", "Urban planning", "Healthcare systems"],
        "exercise_pattern": "Instead of solving it, map it. Draw three stakeholders and what each one thinks the problem is. Where do they disagree? That's where to start.",
    },
}

# ============================================================================
# DATACLASS FOR LECTURE SPINE
# ============================================================================

@dataclass
class LectureSpine:
    """The diagnosis that drives the entire lecture."""
    problem_type: str
    thinking_error: str
    primary_framework: str
    reframe_direction: str
    larry_instinct: str
    template: dict
    example_domain: str = ""


# ============================================================================
# DIAGNOSIS ENGINE
# ============================================================================

def detect_thinking_error(query: str) -> Tuple[str, dict]:
    """
    Detect which thinking error the user is making.
    Returns (error_name, error_config).
    """
    query_lower = query.lower()

    # Score each thinking error
    scores = {}
    for error_name, config in THINKING_ERRORS.items():
        score = sum(1 for signal in config["signals"] if signal in query_lower)
        scores[error_name] = score

    # Get highest scoring error
    if max(scores.values()) > 0:
        best_error = max(scores, key=scores.get)
        return best_error, THINKING_ERRORS[best_error]

    # Default to jumping_to_solutions (most common)
    return "jumping_to_solutions", THINKING_ERRORS["jumping_to_solutions"]


def classify_problem_type(query: str) -> Tuple[str, str]:
    """
    Classify the problem type from the query.
    Returns (problem_type, larry_instinct).
    """
    query_lower = query.lower()

    # Score each classification
    scores = {}
    for class_name, config in CLASSIFICATION_MATRIX.items():
        score = sum(1 for signal in config["signals"] if signal in query_lower)
        scores[class_name] = score

    # Get highest scoring classification
    if max(scores.values()) > 0:
        best_class = max(scores, key=scores.get)
        config = CLASSIFICATION_MATRIX[best_class]
        return config["problem_type"], config["larry_instinct"]

    # Default to ill-defined
    return "ill-defined", "You haven't defined the problem yet. Let's fix that."


def build_lecture_spine(query: str) -> LectureSpine:
    """
    Build the complete diagnosis that drives the lecture.
    This is THE BRAIN of the system.
    """
    # Step 1: Classify problem type
    problem_type, type_instinct = classify_problem_type(query)

    # Step 2: Detect thinking error
    error_name, error_config = detect_thinking_error(query)

    # Step 3: Select ONE primary framework
    primary_framework = error_config["framework"]

    # Step 4: Get template for this problem type
    template_key = problem_type.split(" (")[0]  # Handle "well-defined (disguised)"
    if template_key not in PROBLEM_TEMPLATES:
        template_key = "ill-defined"  # Fallback
    template = PROBLEM_TEMPLATES[template_key]

    # Step 5: Combine Larry's instincts
    larry_instinct = error_config["larry_instinct"]

    return LectureSpine(
        problem_type=problem_type,
        thinking_error=error_name,
        primary_framework=primary_framework,
        reframe_direction=error_config["reframe"],
        larry_instinct=larry_instinct,
        template=template,
        example_domain=template["example_types"][0] if template["example_types"] else "",
    )


# ============================================================================
# REFUSAL GATE — When NOT to teach
# ============================================================================

def is_information_query(query: str) -> bool:
    """Check if this is a pure information request, not a problem."""
    info_patterns = [
        r"^what is ", r"^define ", r"^explain ", r"^tell me about ",
        r"^describe ", r"^list ", r"^how does .+ work",
    ]
    query_lower = query.lower().strip()
    return any(re.match(p, query_lower) for p in info_patterns)


def is_repeat_pattern(query: str, history: List[str]) -> bool:
    """Check if user is asking the same question again."""
    if not history:
        return False

    query_words = set(query.lower().split())
    for past_query in history[-5:]:
        past_words = set(past_query.lower().split())
        overlap = len(query_words & past_words) / max(len(query_words), 1)
        if overlap > 0.7:
            return True
    return False


def problem_quality_score(query: str) -> float:
    """
    Score how well-framed the problem already is.
    High score = already well-framed, don't reframe.
    """
    score = 0.0
    query_lower = query.lower()

    # Positive indicators (shows good thinking)
    good_indicators = [
        "assumption", "constraint", "stakeholder", "tradeoff",
        "hypothesis", "root cause", "underlying", "structural",
    ]
    for indicator in good_indicators:
        if indicator in query_lower:
            score += 0.15

    # Negative indicators (shows poor framing) - subtract from score
    poor_indicators = [
        "best way", "should I", "how do I", "which is better",
        "right answer", "correct approach",
    ]
    for indicator in poor_indicators:
        if indicator in query_lower:
            score -= 0.1

    return max(0.0, min(1.0, score))


def should_generate_lecture(query: str, user_history: List[str]) -> Tuple[bool, str, str]:
    """
    Gate: Should we generate a lecture for this query?
    Returns (should_proceed, reason_code, response_if_refused).
    """
    # Too short
    if len(query.split()) < 5:
        return False, "too_short", "Give me more to work with. What's the real problem you're wrestling with?"

    # Pure information request
    if is_information_query(query):
        return False, "search_redirect", "That's a content question, not a thinking problem. Let me search the materials for you instead."

    # Repeat question
    if is_repeat_pattern(query, user_history):
        return False, "meta_callout", "You've asked me this before. What's really stopping you from moving forward?"

    # Already well-framed (don't reframe good thinking)
    if problem_quality_score(query) > 0.75:
        return False, "push_deeper", "Good framing. Now go further. What's the one assumption that scares you most?"

    return True, "proceed", ""


# ============================================================================
# NEO4J INTEGRATION
# ============================================================================

async def get_framework_from_graph(framework_name: str) -> Dict[str, Any]:
    """
    Query Neo4j for ONE specific framework.
    Returns framework details or empty dict if not found.
    """
    try:
        from tools.graphrag_lite import get_neo4j_driver

        driver = get_neo4j_driver()
        if not driver:
            return {}

        with driver.session() as session:
            result = session.run("""
                MATCH (f:Framework)
                WHERE toLower(f.name) CONTAINS toLower($framework_name)
                RETURN f.name AS name,
                       f.description AS description,
                       f.principles AS principles,
                       f.when_to_use AS when_to_use
                LIMIT 1
            """, {"framework_name": framework_name})

            record = result.single()
            if record:
                return dict(record)

        return {}

    except Exception as e:
        logger.warning(f"Neo4j framework query failed: {e}")
        return {}


async def classify_from_graph(query: str) -> Optional[str]:
    """
    Query Neo4j for problem type classification.
    Returns problem type or None.
    """
    try:
        from tools.graphrag_lite import get_neo4j_driver

        driver = get_neo4j_driver()
        if not driver:
            return None

        keywords = query.lower().split()[:10]  # Limit keywords

        with driver.session() as session:
            result = session.run("""
                MATCH (pt:ProblemType)
                WHERE ANY(word IN $keywords WHERE toLower(pt.name) CONTAINS word)
                   OR ANY(word IN $keywords WHERE toLower(pt.description) CONTAINS word)
                RETURN pt.name AS name, pt.problem_classification AS classification
                LIMIT 1
            """, {"keywords": keywords})

            record = result.single()
            if record:
                return record.get("classification") or record.get("name")

        return None

    except Exception as e:
        logger.warning(f"Neo4j classification failed: {e}")
        return None


# ============================================================================
# FILESEARCH INTEGRATION
# ============================================================================

async def get_larry_material(framework: str, problem_context: str) -> List[Dict[str, str]]:
    """
    Pull Larry-specific phrasing and ONE example.
    HARD LIMIT: 3 excerpts max.
    """
    try:
        from google import genai

        client = genai.Client(
            api_key=os.environ.get("GOOGLE_FILESEARCH_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )

        queries = [
            f"Larry Aronhime teaching {framework} methodology example",
            f"PWS {framework} case study real-world application",
            f"innovation {problem_context[:50]} breakthrough story",
        ]

        results = []
        for q in queries:
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=q,
                    config={
                        "tools": [{"google_search": {"file_search_store": FILESEARCH_STORE_ID}}],
                        "temperature": 0.3,
                        "max_output_tokens": 400,
                    },
                )

                if response and response.text:
                    results.append({
                        "text": response.text[:300],
                        "query": q,
                    })

                if len(results) >= 3:  # HARD LIMIT
                    break

            except Exception as e:
                logger.debug(f"FileSearch query failed: {e}")
                continue

        return results[:3]

    except Exception as e:
        logger.warning(f"FileSearch integration failed: {e}")
        return []


# ============================================================================
# SCRIPT GENERATION — The Larry Voice
# ============================================================================

INTERVENTION_PROMPT = """You are Professor Lawrence Aronhime. You have taught innovation methodology
at Johns Hopkins for 20+ years. You are about to deliver a 60–120 second
intellectual intervention.

You are NOT explaining. You are NOT comforting. You are PUSHING.

## YOUR DIAGNOSIS (provided by system):
- Problem type: {problem_type}
- Student's thinking error: {thinking_error}
- Primary framework: {primary_framework}
- Reframe direction: {reframe_direction}
- Larry's instinct: {larry_instinct}

## STUDENT'S QUESTION:
{query}

## MATERIALS FOR EXAMPLE (use sparingly):
{materials}

## STRICT STRUCTURE (total: 250–350 words):

### 1. PROVOCATIVE OPENING (2–3 sentences, ~30 words)
Stop them. Reframe what they just said.
Start with one of these patterns:
- "Let me stop you right there..."
- "Before we go any further..."
- "The way you're asking that tells me something important..."
DO NOT be gentle. DO NOT validate their framing.

### 2. REFRAME THE QUESTION (2–3 sentences, ~50 words)
"The real question isn't X. It's Y."
Use the diagnosis to show them the question beneath their question.

### 3. ONE FRAMEWORK (3–4 sentences, ~80 words)
Introduce {primary_framework} and ONLY {primary_framework}.
Say explicitly: "This is a {problem_type} problem, which means..."
Connect it to their specific situation. Make it visceral, not academic.

### 4. ONE EXAMPLE (2–3 sentences, ~60 words)
Short. Familiar. Memorable.
Keep it concrete. No abstractions.

### 5. THINKING EXERCISE (2–3 sentences, ~40 words)
Start with: "Here's what I want you to do next..."
Give them ONE specific action that forces better thinking.
End with a command: "Go." or "Start there." or "Do that first."
NO summary. NO reassurance. NO "good luck."

## VOICE RULES:
- Use "..." for natural pauses (ElevenLabs will render these)
- Short sentences. Punchy rhythm.
- Contractions: "you're" not "you are", "can't" not "cannot"
- Direct address: "you", never "one" or "students"
- NEVER use bullet points, numbered lists, or headers
- NEVER summarize at the end
- NEVER say "That's a great question" or "Let's unpack this"
- NEVER use the words: journey, holistic, leverage, ideate, best practice

## TONE: A mentor who respects you enough to make you uncomfortable.

Write ONLY the spoken script. No commentary. No labels."""


def validate_script(script: str) -> Tuple[bool, List[str]]:
    """
    Validate script meets Larry standards.
    Returns (is_valid, list_of_issues).
    """
    issues = []
    script_lower = script.lower()

    # Must have an interruption opener
    has_opener = any(
        opener.lower()[:20] in script_lower[:200]  # Check first 200 chars
        for opener in LARRY_LEXICON["opening_interruptions"]
    )
    if not has_opener:
        # Also check for "let me stop" pattern
        if "let me stop" not in script_lower[:200] and "before we go" not in script_lower[:200]:
            issues.append("Missing provocative opening (must interrupt)")

    # Must name the problem type
    problem_markers = ["ill-defined", "well-defined", "un-defined", "wicked",
                       "undefined", "this is a", "this is an"]
    has_marker = any(marker in script_lower for marker in problem_markers)
    if not has_marker:
        issues.append("Must explicitly name the problem type")

    # Must NOT end with summary or encouragement
    last_100 = script_lower[-100:]
    bad_endings = ["good luck", "you got this", "in summary", "to summarize",
                   "in conclusion", "best of luck"]
    for bad in bad_endings:
        if bad in last_100:
            issues.append(f"Ends with forbidden phrase: '{bad}'")

    # Check for banned words throughout
    for banned in LARRY_LEXICON["banned_words"]:
        if banned.lower() in script_lower:
            issues.append(f"Contains banned word: '{banned}'")

    # Word count check
    word_count = len(script.split())
    if word_count < 200:
        issues.append(f"Too short ({word_count} words, need 250-350)")
    if word_count > 400:
        issues.append(f"Too long ({word_count} words, need 250-350)")

    return len(issues) == 0, issues


async def generate_intervention_script(
    query: str,
    spine: LectureSpine,
    materials: List[Dict[str, str]],
) -> str:
    """Generate the intervention script using Claude."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # Format materials
        materials_text = "\n".join([
            f"- {m.get('text', '')[:200]}" for m in materials
        ]) if materials else "Use general PWS methodology knowledge."

        prompt = INTERVENTION_PROMPT.format(
            problem_type=spine.problem_type,
            thinking_error=spine.thinking_error,
            primary_framework=spine.primary_framework,
            reframe_direction=spine.reframe_direction,
            larry_instinct=spine.larry_instinct,
            query=query,
            materials=materials_text,
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        script = response.content[0].text.strip()

        # Validate
        is_valid, issues = validate_script(script)
        if not is_valid:
            logger.warning(f"Script validation issues: {issues}")
            # Could regenerate here, but for MVP let it pass

        return script

    except Exception as e:
        logger.error(f"Claude script generation failed: {e}")
        return await _generate_script_gemini(query, spine, materials)


async def _generate_script_gemini(
    query: str,
    spine: LectureSpine,
    materials: List[Dict[str, str]],
) -> str:
    """Fallback script generation using Gemini."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

        materials_text = "\n".join([
            f"- {m.get('text', '')[:200]}" for m in materials
        ]) if materials else "Use general PWS methodology knowledge."

        prompt = INTERVENTION_PROMPT.format(
            problem_type=spine.problem_type,
            thinking_error=spine.thinking_error,
            primary_framework=spine.primary_framework,
            reframe_direction=spine.reframe_direction,
            larry_instinct=spine.larry_instinct,
            query=query,
            materials=materials_text,
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=800
            )
        )

        return response.text.strip()

    except Exception as e:
        logger.error(f"Gemini script generation failed: {e}")
        # Ultimate fallback - use Larry's instinct directly
        return f"""Let me stop you right there... because the way you're asking
this tells me something important.

{spine.larry_instinct}

This is a {spine.problem_type} problem. That means you can't approach it
the way you're approaching it. You need to step back and look at what
you're actually trying to solve... not the solution you jumped to.

Think about it this way... the best innovations don't come from better
answers. They come from better questions. And right now... you're asking
the wrong question.

Here's what I want you to do. Take your question and rewrite it three
different ways. Which version makes you most uncomfortable? That's
probably the right one.

Go."""


# ============================================================================
# AUDIO GENERATION
# ============================================================================

async def convert_to_audio(script: str) -> Optional[bytes]:
    """Convert script to audio using ElevenLabs."""
    try:
        from elevenlabs import ElevenLabs, VoiceSettings

        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not set")
            return None

        client = ElevenLabs(api_key=api_key)

        # Larry's voice settings (slightly unstable for human feel)
        voice_settings = VoiceSettings(
            stability=0.72,  # Slightly unstable = more human
            similarity_boost=0.78,
            style=0.30,  # Moderate expressiveness
            use_speaker_boost=True
        )

        audio_stream = client.text_to_speech.convert_as_stream(
            text=script[:5000],
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings
        )

        # Collect audio bytes
        import io
        audio_buffer = io.BytesIO()
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                audio_buffer.write(chunk)

        audio_bytes = audio_buffer.getvalue()

        if len(audio_bytes) < 100:
            logger.warning("Audio too small, possibly failed")
            return None

        logger.info(f"[LarryTeachMe] Generated audio ({len(audio_bytes)} bytes)")
        return audio_bytes

    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e}")
        return None


def extract_thinking_exercise(script: str) -> str:
    """Extract the thinking exercise from the script."""
    # Look for exercise patterns
    patterns = [
        r"Here's what I want you to do[^.]*\.(.*?)(?:Go\.|Start there\.|Do that first\.)",
        r"Take a piece of paper[^.]*\.(.*?)(?:Go\.|Start there\.)",
        r"Write this down[^.]*\.(.*?)(?:Go\.|Start there\.)",
    ]

    for pattern in patterns:
        match = re.search(pattern, script, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0).strip()

    # Fallback: last paragraph
    paragraphs = script.strip().split("\n\n")
    if paragraphs:
        return paragraphs[-1].strip()

    return "Rewrite your question now."


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

async def larry_teach_me(
    query: str,
    user_history: List[str] = None,
    include_audio: bool = True,
) -> Dict[str, Any]:
    """
    The complete cognitive intervention pipeline.

    Query → Diagnose → Gate → Retrieve → Script → Validate → Voice

    Args:
        query: The user's question/problem
        user_history: Previous queries from this user (for repeat detection)
        include_audio: Whether to generate audio

    Returns:
        {
            "status": "success" | "refused",
            "audio_bytes": bytes | None,
            "transcript": str,
            "diagnosis": {problem_type, thinking_error, framework_used},
            "thinking_exercise": str,
            "cta": str,
            "refusal_reason": str | None,
            "refusal_response": str | None,
        }
    """
    user_history = user_history or []

    # ── GATE: Should we even teach? ──
    should_proceed, reason, refusal_response = should_generate_lecture(query, user_history)

    if not should_proceed:
        logger.info(f"[LarryTeachMe] Refused: {reason}")
        return {
            "status": "refused",
            "audio_bytes": None,
            "transcript": "",
            "diagnosis": {},
            "thinking_exercise": "",
            "cta": "Rewrite your question.",
            "refusal_reason": reason,
            "refusal_response": refusal_response,
        }

    # ── STEP 1: DIAGNOSE (the brain) ──
    logger.info(f"[LarryTeachMe] Diagnosing: {query[:50]}...")
    spine = build_lecture_spine(query)

    # Optional: Enrich from Neo4j (run in parallel)
    neo4j_classification = await classify_from_graph(query)
    if neo4j_classification:
        # Could refine spine.problem_type here
        logger.info(f"[LarryTeachMe] Neo4j classification: {neo4j_classification}")

    # ── STEP 2: RETRIEVE (the fuel) ──
    logger.info(f"[LarryTeachMe] Retrieving materials for: {spine.primary_framework}")
    framework_context, larry_material = await asyncio.gather(
        get_framework_from_graph(spine.primary_framework),
        get_larry_material(spine.primary_framework, query)
    )

    # Enrich spine with Neo4j framework if found
    if framework_context:
        spine.example_domain = framework_context.get("example", spine.example_domain)

    # ── STEP 3: GENERATE SCRIPT ──
    logger.info("[LarryTeachMe] Generating intervention script...")
    script = await generate_intervention_script(query, spine, larry_material)

    # ── STEP 4: VALIDATE ──
    is_valid, issues = validate_script(script)
    if not is_valid:
        logger.warning(f"[LarryTeachMe] Script issues (proceeding anyway): {issues}")

    # ── STEP 5: GENERATE AUDIO ──
    audio_bytes = None
    if include_audio:
        logger.info("[LarryTeachMe] Converting to audio...")
        audio_bytes = await convert_to_audio(script)

    # ── EXTRACT EXERCISE ──
    thinking_exercise = extract_thinking_exercise(script)

    return {
        "status": "success",
        "audio_bytes": audio_bytes,
        "transcript": script,
        "diagnosis": {
            "problem_type": spine.problem_type,
            "thinking_error": spine.thinking_error,
            "framework_used": spine.primary_framework,
            "larry_instinct": spine.larry_instinct,
        },
        "thinking_exercise": thinking_exercise,
        "cta": "Rewrite your question now.",
        "refusal_reason": None,
        "refusal_response": None,
    }


# ============================================================================
# LEGACY COMPATIBILITY (for existing code)
# ============================================================================

async def generate_quick_lecture(
    question: str,
    context: str = "",
    include_audio: bool = True
) -> Tuple[Optional[bytes], str, Dict[str, Any]]:
    """
    Legacy wrapper for backward compatibility.
    Converts new API to old return format.
    """
    result = await larry_teach_me(
        query=question,
        user_history=[],
        include_audio=include_audio,
    )

    metadata = {
        "question": question[:100],
        "problem_type": result["diagnosis"].get("problem_type", "unknown"),
        "thinking_error": result["diagnosis"].get("thinking_error", "unknown"),
        "framework_used": result["diagnosis"].get("framework_used", "unknown"),
        "audio_generated": result["audio_bytes"] is not None,
        "script_length": len(result["transcript"]),
        "status": result["status"],
    }

    if result["status"] == "refused":
        # Return the refusal response as the script
        return None, result["refusal_response"], metadata

    return result["audio_bytes"], result["transcript"], metadata


# ============================================================================
# CHAINLIT INTEGRATION HELPER
# ============================================================================

async def create_lecture_message(question: str, context: str = "") -> Dict[str, Any]:
    """
    Create a lecture and return Chainlit-ready elements.

    Returns dict with 'audio', 'script', 'metadata', 'diagnosis', 'cta' keys.
    """
    import chainlit as cl

    result = await larry_teach_me(
        query=question,
        user_history=[],
        include_audio=True,
    )

    output = {
        "script": result["transcript"],
        "diagnosis": result["diagnosis"],
        "thinking_exercise": result["thinking_exercise"],
        "cta": result["cta"],
        "status": result["status"],
        "audio": None,
    }

    if result["audio_bytes"]:
        output["audio"] = cl.Audio(
            content=result["audio_bytes"],
            mime="audio/mpeg",
            name="larry_intervention.mp3"
        )

    if result["status"] == "refused":
        output["refusal_response"] = result["refusal_response"]

    return output


# ============================================================================
# TEACHABLE MOMENT DETECTION — Background Analysis for Contextual Triggering
# ============================================================================

# Signals that indicate a teachable moment
TEACHABLE_MOMENT_SIGNALS = {
    "thinking_errors": {
        # User is stuck or confused
        "stuck_signals": [
            "i'm stuck", "don't know where to start", "not sure",
            "can't figure out", "confused about", "struggling with",
            "having trouble", "don't understand", "lost on",
        ],
        # User is making assumptions
        "assumption_signals": [
            "i assume", "probably", "i think it should",
            "obviously", "everyone knows", "the only way",
            "it's clear that", "must be", "has to be",
        ],
        # User is asking wrong questions
        "wrong_question_signals": [
            "should i x or y", "which is better", "best way to",
            "what's the right", "how do i implement", "which tool",
        ],
        # User is solution-focused prematurely
        "premature_solution_signals": [
            "let me build", "i'll just create", "quick solution",
            "easy fix", "just need to", "simply do",
        ],
    },
    "opportunity_patterns": {
        # User describing real problems
        "problem_language": [
            "the problem is", "we're facing", "challenge is",
            "obstacle", "bottleneck", "barrier", "constraint",
            "can't seem to", "keeps happening", "recurring issue",
        ],
        # User exploring ideas
        "exploration_language": [
            "what if", "wondering about", "thinking about",
            "exploring", "considering", "might work", "could try",
        ],
        # User making decisions
        "decision_language": [
            "deciding between", "choose", "evaluate",
            "compare", "weigh options", "trade-off",
        ],
    },
    # Minimum word count for meaningful analysis
    "min_words": 15,
    # Confidence threshold
    "confidence_threshold": 0.5,
}


def analyze_for_teachable_moment(
    recent_messages: List[Dict[str, str]],
    turn_count: int
) -> Dict[str, Any]:
    """
    Analyze recent conversation for teachable moments.
    Runs in background every 3-7 turns.

    Returns:
        {
            "should_offer_intervention": bool,
            "confidence": float (0-1),
            "detected_signals": list,
            "suggested_framework": str,
            "larry_might_say": str,
        }
    """
    result = {
        "should_offer_intervention": False,
        "confidence": 0.0,
        "detected_signals": [],
        "suggested_framework": None,
        "larry_might_say": None,
        "turn_count": turn_count,
    }

    # Only analyze every 3-7 turns
    if turn_count < 3:
        return result

    # Combine recent user messages
    user_messages = [
        msg.get("content", "") for msg in recent_messages
        if msg.get("role") == "user"
    ][-5:]  # Last 5 user messages

    combined_text = " ".join(user_messages).lower()

    # Skip if too short
    if len(combined_text.split()) < TEACHABLE_MOMENT_SIGNALS["min_words"]:
        return result

    # Score thinking errors
    error_score = 0
    detected_signals = []
    suggested_error = None

    for error_type, signals in TEACHABLE_MOMENT_SIGNALS["thinking_errors"].items():
        matches = [s for s in signals if s in combined_text]
        if matches:
            error_score += len(matches) * 0.2
            detected_signals.extend(matches)
            if not suggested_error:
                suggested_error = error_type

    # Score opportunity patterns
    opportunity_score = 0
    for pattern_type, patterns in TEACHABLE_MOMENT_SIGNALS["opportunity_patterns"].items():
        matches = [p for p in patterns if p in combined_text]
        if matches:
            opportunity_score += len(matches) * 0.15
            detected_signals.extend(matches)

    # Calculate confidence
    total_score = min(1.0, error_score + opportunity_score)
    result["confidence"] = total_score
    result["detected_signals"] = detected_signals[:5]  # Top 5 signals

    # Determine if we should offer intervention
    if total_score >= TEACHABLE_MOMENT_SIGNALS["confidence_threshold"]:
        result["should_offer_intervention"] = True

        # Map error type to framework
        framework_map = {
            "stuck_signals": "Problem Types Taxonomy",
            "assumption_signals": "Reverse Salients",
            "wrong_question_signals": "Beautiful Questions",
            "premature_solution_signals": "Problem Types Taxonomy",
        }
        result["suggested_framework"] = framework_map.get(suggested_error, "PWS Methodology")

        # Generate Larry's potential insight
        larry_hints = {
            "stuck_signals": "It sounds like you're wrestling with something. That's actually good — discomfort is data.",
            "assumption_signals": "I notice some assumptions in there. What if they're wrong?",
            "wrong_question_signals": "You might be asking the wrong question. Let me show you a different angle.",
            "premature_solution_signals": "You're jumping to solutions. Back up — what's the real problem?",
        }
        result["larry_might_say"] = larry_hints.get(
            suggested_error,
            "There's a thinking pattern here I can help with."
        )

    return result


async def background_teachable_moment_check(
    session_id: str,
    history: List[Dict[str, str]],
    turn_count: int
) -> Optional[Dict[str, Any]]:
    """
    Run teachable moment analysis in background.
    Called by message handler every 3-7 turns.

    Returns analysis result or None if not ready.
    """
    # Only check every 3-7 turns
    if turn_count < 3:
        return None

    # Check at turn 3, 5, 7, etc.
    if turn_count % 2 != 1:  # Odd turns: 3, 5, 7...
        return None

    logger.info(f"[TeachableMoment] Analyzing turn {turn_count} for session {session_id[:8]}...")

    # Run analysis
    analysis = analyze_for_teachable_moment(history, turn_count)

    if analysis["should_offer_intervention"]:
        logger.info(f"[TeachableMoment] Found opportunity! Confidence: {analysis['confidence']:.2f}")
        logger.info(f"[TeachableMoment] Signals: {analysis['detected_signals']}")

    return analysis


def should_show_larry_button(
    history: List[Dict[str, str]],
    turn_count: int,
    cached_analysis: Optional[Dict] = None
) -> Tuple[bool, Optional[str]]:
    """
    Quick check if Larry button should appear.
    Uses cached analysis if available, otherwise does instant check.

    Returns:
        (should_show, tooltip_hint)
    """
    # Always show after turn 3
    if turn_count >= 3:
        # If we have cached analysis showing opportunity
        if cached_analysis and cached_analysis.get("should_offer_intervention"):
            hint = cached_analysis.get("larry_might_say", "Larry can help push your thinking")
            return True, f"💡 {hint}"

        # Quick instant check (no LLM)
        recent_text = " ".join([
            m.get("content", "") for m in history[-3:]
            if m.get("role") == "user"
        ]).lower()

        # Quick signal check
        quick_signals = [
            "stuck", "confused", "not sure", "help",
            "should i", "which is", "best way", "don't know",
            "problem is", "challenge", "struggling",
        ]

        if any(signal in recent_text for signal in quick_signals):
            return True, "💡 Larry can offer a cognitive intervention"

    # Default: show button but without special tooltip
    if turn_count >= 2:
        return True, None

    return False, None
