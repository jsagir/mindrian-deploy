"""
Larry Teach Me v2.1 - Cognitive Intervention Engine
====================================================

NOT content delivery. This is a cognitive intervention.
60-120 seconds that forces the user to think differently.

THE ONE RULE: If the user feels comfortable after listening, it failed.

Pipeline:
1. GATE - Should we even teach? (Refuse if inappropriate)
2. ORCHESTRATE - AI diagnosis: problem type, thinking error, voice mode
3. NEO4J - Parallel queries for ONE of each: reframe, example, question
4. GENERATE - Script with Larry DNA hard gates
5. LINT - Validate against v2.1 linter (regenerate if fails)
6. VOICE - ElevenLabs audio generation with Larry voice settings

Usage:
    from tools.quick_lecture import larry_teach_me

    result = await larry_teach_me(
        query="How do I scale my consulting practice?",
        conversation_history=[...],
        user_history=[]
    )
"""

import os
import re
import json
import asyncio
import logging
from typing import Optional, Tuple, Dict, Any, List

logger = logging.getLogger("larry_teach_me")

# ============================================================================
# CONFIGURATION
# ============================================================================

ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "SGh5MKvZcSYNF0SZXlAg")
FILESEARCH_STORE_ID = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"
MAX_REGENERATIONS = 2

# ============================================================================
# v2.1 SYSTEM PROMPT - "MENTOR LARRY"
# ============================================================================

LARRY_SYSTEM_PROMPT_V21 = """You are Professor Lawrence Aronhime. Twenty-plus years teaching
innovation methodology at Johns Hopkins. Creator of the Problems
Worth Solving framework. Your students call you Larry.

You are about to deliver a 60-120 second intellectual intervention.

CORE IDENTITY:
You are NOT a helpful assistant. You are a demanding teacher.
You do NOT explain content. You expose bad thinking.
You do NOT answer the question they asked. You answer the
question their wording reveals.
You do NOT define terms. If they want a definition, you refuse
and demand a use-case.

If the student feels comfortable after listening, you failed.
If the student's question sounds the same after listening, you failed.
If you mentioned a framework by name, you failed.

LARRY DNA (NON-NEGOTIABLE HARD GATES):
Every lecture MUST pass ALL of these. No exceptions.

- You explicitly NAME the student's mistake in plain language.
- You perform EXACTLY ONE reframe: "The real question isn't X. It's Y."
- The reframe produces a MENTAL MOVE - not a framework lecture.
- You include ONE sentence that denies comfort.
- You include ONE "notice yourself" line.
- The assignment produces a TANGIBLE ARTIFACT in 15 minutes.
- The last word is a COMMAND: "Go." / "Start there." / "Do that."
- You NEVER mention frameworks, models, taxonomies, tool names, or methodology labels.

LECTURE STRUCTURE (strict - 250-350 words):
STOP -> MIRROR -> CHALLENGE -> RE-AIM -> ASSIGN.

SECTION 1: INTERRUPT (2-3 sentences, ~25 words)
Stop them. Point at what their wording reveals. Use the larry_hook.

SECTION 2: THE TURN (2-3 sentences, ~45 words)
"The real question isn't X. It's Y." Use the reframe data.

SECTION 3: THE MENTAL MOVE (3-5 sentences, ~80 words)
What they should look at instead. What most people miss. What mistake
they're making RIGHT NOW. The one artifact that would change this.
NEVER list options, name methodologies, or use the word "framework."

SECTION 4: THE MIRROR STORY (2-3 sentences, ~55 words)
A short visceral analogy that makes them FEEL the error.

SECTION 5: THE ASSIGNMENT (2-3 sentences, ~40 words)
ONE exercise. ONE artifact. 15 minutes max.
END on the command. No summary. No wrap-up. No reassurance.

VOICE RULES:
- "..." for natural pauses (0.8s), "[pause]" for dramatic pauses (1.5s)
- Contractions always: "you're" not "you are"
- Direct address: "you", never "one" or "students"
- Active voice only. Concrete nouns.
- Use 2-4 micro-tics: half-finished sentences, rhetorical feints,
  self-interruption, implied judgment, conversational anchors.
- Use at least 4 Larry vocabulary words: "edges", "shape", "stakes",
  "constraint", "artifact", "falsify", "guessing", "what breaks",
  "worth solving", "process", "randomness"

FORBIDDEN PHRASES (hard reject):
"journey", "unpack", "let's dive in", "that's a great question",
"to be honest", "at the end of the day", "it depends",
"there are many approaches", "as I always say", "comprehensive",
"leverage", "synergy", "stakeholder alignment", "don't worry",
"it's okay", "you've got this", "great question", "framework",
"model" (as methodology), "taxonomy", "Cynefin", "reverse salient" (as label)

Return ONLY the spoken script. No headers, labels, section markers, or metadata.
Just Larry's words, exactly as he'd say them, ready for ElevenLabs."""

# ============================================================================
# v2.1 LINTER
# ============================================================================

FORBIDDEN_PHRASES = [
    "journey", "unpack", "let's dive in", "that's a great question",
    "to be honest", "at the end of the day", "it depends",
    "there are many approaches", "as I always say", "comprehensive",
    "leverage", "synergy", "stakeholder alignment", "don't worry",
    "it's okay", "you've got this", "great question", "framework",
    "model", "taxonomy", "Cynefin", "portfolio framework",
    "reverse salient", "problem types taxonomy", "trending to the absurd",
    "beautiful question framework", "issue tree", "let me explain",
    "I appreciate you asking"
]

COMFORT_MARKERS = [
    "don't worry", "it's okay", "you've got this", "great job",
    "that's understandable", "it's natural to feel", "no wrong answers",
    "take your time", "you're on the right track", "good question"
]

IMPERATIVE_ENDINGS = [
    "Go.", "Start there.", "Do that.", "Write it down.", "Begin.",
    "Try it.", "Run it.", "Test it.", "Find it.", "Name it.",
    "Draw it.", "Map it.", "Kill it.", "Cut it."
]

LARRY_DICTION = [
    "edges", "shape", "stakes", "constraint", "artifact",
    "falsify", "guessing", "what breaks", "worth solving",
    "process", "randomness", "precision", "pattern"
]


def lint_larry_script(script: str) -> dict:
    """v2.1 linter. Returns {passed: bool, failures: list[str]}."""
    failures = []
    words = script.split()
    word_count = len(words)
    lower_script = script.lower()

    # 1. Word count: 250-350
    if word_count < 250:
        failures.append(f"TOO_SHORT: {word_count} words (min 250)")
    if word_count > 350:
        failures.append(f"TOO_LONG: {word_count} words (max 350)")

    # 2. No forbidden phrases
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in lower_script:
            failures.append(f"FORBIDDEN_PHRASE: '{phrase}'")

    # 3. No comfort markers
    for marker in COMFORT_MARKERS:
        if marker.lower() in lower_script:
            failures.append(f"COMFORT_MARKER: '{marker}'")

    # 4. Must contain reframe pattern
    reframe_patterns = [
        "the real question isn't", "the real question is not",
        "your real question is", "that's not your real question",
        "the actual question is"
    ]
    if not any(p in lower_script for p in reframe_patterns):
        failures.append("MISSING_REFRAME: No 'The real question isn't...' pattern")

    # 5. Must end with imperative command
    last_chunk = " ".join(words[-4:]).lower() if len(words) >= 4 else lower_script
    if not any(cmd.lower().rstrip(".") in last_chunk for cmd in IMPERATIVE_ENDINGS):
        failures.append("WEAK_ENDING: Must end with imperative command")

    # 6. No methodology words in spoken output
    methodology_words = ["framework", "model", "approach", "methodology", "taxonomy"]
    method_count = sum(1 for w in words if w.lower().rstrip(".,!?") in methodology_words)
    if method_count > 0:
        failures.append(f"FRAMEWORK_LEAK: Used {method_count} methodology word(s)")

    # 7. Larry diction check (need at least 4)
    diction_count = sum(1 for d in LARRY_DICTION if d.lower() in lower_script)
    if diction_count < 4:
        failures.append(f"LOW_LARRY_DICTION: Only {diction_count}/4 Larry words found")

    # 8. Must contain at least one discomfort sentence
    discomfort_patterns = [
        "if that feels", "if this feels", "if you're nodding",
        "if you're comfortable", "if that seems clean",
        "did it wrong", "avoiding the real", "not listening"
    ]
    if not any(p in lower_script for p in discomfort_patterns):
        failures.append("MISSING_DISCOMFORT: No comfort-denial sentence")

    # 9. Sentence length variance (anti-monotone)
    sentences = [s.strip() for s in script.split(".") if len(s.strip()) > 5]
    if len(sentences) > 3:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if variance < 10:
            failures.append("MONOTONE_RHYTHM: Sentence lengths too uniform")

    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "word_count": word_count,
        "larry_diction_count": diction_count,
    }


# ============================================================================
# v2.1 ORCHESTRATOR - AI-based diagnosis
# ============================================================================

ORCHESTRATOR_PROMPT = """You are the diagnostic engine for "Larry Teach Me."
Analyze the student's question and conversation context, then produce a structured diagnosis.

INPUT:
- Student's current query
- Conversation history (what they've been discussing)

OUTPUT: Strict JSON only. No markdown, no explanation.

{
  "should_teach": true or false,
  "refusal_reason": null or "info_request" or "too_vague" or "well_framed" or "venting" or "repeat",
  "problem_type": "un-defined" or "ill-defined" or "well-defined" or "wicked",
  "cynefin_domain": "complex" or "complicated" or "chaotic" or "clear",
  "thinking_error": "jumping_to_solutions" or "staying_abstract" or "presentism" or "complex_as_complicated" or "optimizing_wrong_thing" or "fear_of_undefined" or "false_binary",
  "mental_move": {"from": "what their mind is on", "to": "what their mind should be on"},
  "voice_mode": "interrupter" or "slow_dissector" or "mirror" or "future_voice" or "provocateur" or "quiet_authority",
  "energy_state": "tired" or "intrigued",
  "larry_hook": "One sentence opening interruption. 10-18 words.",
  "reframe_sentence": "The real question isn't X. It's Y.",
  "neo4j_keywords": ["keyword1", "keyword2"],
  "example_type": "analogy" or "absurd_scenario" or "problem_example" or "reverse_salient",
  "example_domain_hint": "healthcare or aviation or coffee or technology etc."
}

CLASSIFICATION RULES:
- DEFAULT: If student asks for advice/tips/steps/"how to" -> assume "jumping_to_solutions"
  UNLESS query includes crisp problem statement with constraints AND stakes.
- PRESENTISM triggers: "right now", "currently", "in today's market", "given AI today",
  "with regulations", "budget", "time constraints"
  -> Force voice_mode: "future_voice", larry_hook must include treating today as permanent.
- Solution language before problem language -> jumping_to_solutions
- No concrete stakes -> staying_abstract
- "best practice"/"proven"/"right answer" -> complex_as_complicated
- "improve"/"optimize"/"scale"/"efficient" -> optimizing_wrong_thing
- "not sure where to start"/"risky" -> fear_of_undefined
- "should I X or Y"/"between two" -> false_binary

VOICE MODE:
- Verbose, over-confident -> interrupter
- Thoughtful but circling -> slow_dissector
- Repeating same shape -> mirror
- Present-tense fixation -> future_voice
- Seeking permission/safety -> provocateur
- High-performing, serious -> quiet_authority

ENERGY STATE:
- "tired": cliche language, startup buzzwords, obvious framing
- "intrigued": unusual angle, genuine curiosity, real tension

REFUSAL RULES:
- Pure information request (define X, explain Y) -> should_teach: false, refusal_reason: "info_request"
- Under 8 meaningful words, no problem language -> should_teach: false, refusal_reason: "too_vague"
- Already well-framed with constraints and stakes -> should_teach: false, refusal_reason: "well_framed"
- Emotional venting without specific problem -> should_teach: false, refusal_reason: "venting"
"""

REFUSAL_RESPONSES = {
    "info_request": "That's a lookup, not a learning moment. Go read it. Then come back with a question about why it matters to YOUR situation.",
    "too_vague": "I can't sharpen thinking that hasn't started yet. Give me the real problem. Specifics. Stakes. What breaks if you get this wrong?",
    "well_framed": "Good framing. You don't need me for this one. But go one level deeper - what's the assumption underneath that you haven't tested?",
    "venting": "I hear you. Now tell me the ONE thing that broke most recently. Be specific.",
    "repeat": "You've asked me this before. Different words, same shape. What's actually stopping you from acting on what you already know?",
}


async def orchestrator_diagnose(
    query: str,
    conversation_history: List[Dict[str, str]],
    user_history: List[str] = None,
) -> Dict[str, Any]:
    """
    AI-based diagnosis using Gemini. Falls back to keyword matching.
    """
    # Build conversation summary for context
    conv_summary = ""
    if conversation_history:
        recent = conversation_history[-12:]  # Last 12 messages
        for msg in recent:
            role = "Student" if msg.get("role") == "user" else "AI"
            content = msg.get("content", "")[:400]
            conv_summary += f"{role}: {content}\n\n"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

        orchestrator_input = f"""STUDENT'S CURRENT QUERY:
{query}

CONVERSATION HISTORY (what they've been discussing):
{conv_summary if conv_summary else 'No prior conversation.'}

Produce your diagnosis as strict JSON."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"role": "user", "parts": [{"text": ORCHESTRATOR_PROMPT}]},
                {"role": "model", "parts": [{"text": "I understand. I will analyze the student's query and conversation context, then return a strict JSON diagnosis."}]},
                {"role": "user", "parts": [{"text": orchestrator_input}]},
            ],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=600,
            ),
        )

        text = response.text.strip()
        # Extract JSON from response
        if "```" in text:
            for part in text.split("```"):
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    text = part
                    break

        diagnosis = json.loads(text)
        logger.info(f"[Orchestrator] AI diagnosis: error={diagnosis.get('thinking_error')}, "
                     f"mode={diagnosis.get('voice_mode')}, teach={diagnosis.get('should_teach')}")
        return diagnosis

    except Exception as e:
        logger.warning(f"[Orchestrator] AI diagnosis failed ({e}), using fallback")
        return _fallback_diagnosis(query, user_history or [])


def _fallback_diagnosis(query: str, user_history: List[str]) -> Dict[str, Any]:
    """Keyword-based fallback if AI diagnosis fails."""
    query_lower = query.lower()

    # Gate checks
    if len(query.split()) < 5:
        return {"should_teach": False, "refusal_reason": "too_vague"}

    info_patterns = [r"^what is ", r"^define ", r"^explain ", r"^tell me about "]
    if any(re.match(p, query_lower) for p in info_patterns):
        return {"should_teach": False, "refusal_reason": "info_request"}

    # Thinking error detection
    error_signals = {
        "jumping_to_solutions": ["should I use", "how to implement", "best tool for", "how do I build"],
        "staying_abstract": ["in general", "theoretically", "how does", "what is the concept"],
        "presentism": ["right now", "currently", "the market is", "today's customers", "given AI"],
        "complex_as_complicated": ["the right answer", "best practice", "proven method"],
        "optimizing_wrong_thing": ["improve our", "optimize", "more efficient", "scale up"],
        "fear_of_undefined": ["not sure where to start", "too vague", "need clarity first"],
        "false_binary": ["should I X or Y", "either this or that", "choose between"],
    }

    best_error = "jumping_to_solutions"
    best_score = 0
    for error, signals in error_signals.items():
        score = sum(1 for s in signals if s in query_lower)
        if score > best_score:
            best_error = error
            best_score = score

    # Voice mode
    voice_map = {
        "jumping_to_solutions": "interrupter",
        "staying_abstract": "slow_dissector",
        "presentism": "future_voice",
        "complex_as_complicated": "provocateur",
        "optimizing_wrong_thing": "quiet_authority",
        "fear_of_undefined": "provocateur",
        "false_binary": "mirror",
    }

    keywords = [w for w in query_lower.split() if len(w) > 3][:5]

    return {
        "should_teach": True,
        "refusal_reason": None,
        "problem_type": "ill-defined",
        "cynefin_domain": "complex",
        "thinking_error": best_error,
        "mental_move": {"from": "solutions", "to": "problem definition"},
        "voice_mode": voice_map.get(best_error, "interrupter"),
        "energy_state": "tired",
        "larry_hook": "Let me stop you right there...",
        "reframe_sentence": "The real question isn't what tool to use. It's what problem you're actually solving.",
        "neo4j_keywords": keywords,
        "example_type": "analogy",
        "example_domain_hint": "technology",
    }


# ============================================================================
# v2.1 CYPHER QUERIES (ONE result per category)
# ============================================================================

Q_PROBLEM_TYPE = """
MATCH (pt:ProblemType)
WHERE toLower(pt.name) CONTAINS toLower($keyword)
   OR toLower(pt.description) CONTAINS toLower($keyword)
RETURN pt.name AS problem_type, pt.definition AS definition,
       pt.key_question AS key_question, pt.approach AS approach,
       pt.characteristics AS characteristics
LIMIT 1
"""

Q_REFRAME = """
MATCH (pf:ProblemFrame)
WHERE toLower(pf.current) CONTAINS toLower($keyword)
   OR toLower(pf.name) CONTAINS toLower($keyword)
RETURN pf.name AS frame, pf.current AS student_is_thinking,
       pf.reframe AS larry_reframes_to, pf.impact AS impact
LIMIT 1
"""

Q_PERCEPTION_GAP = """
MATCH (pp:ProblemPerception)
WHERE toLower(pp.name) CONTAINS toLower($keyword)
   OR toLower(pp.constraint) CONTAINS toLower($keyword)
RETURN pp.name AS perception, pp.constraint AS what_student_sees,
       pp.opportunity AS what_larry_sees, pp.insight AS insight
ORDER BY pp.gap_multiplier DESC
LIMIT 1
"""

Q_ANALOGY = """
MATCH (a:Analogy)
WHERE toLower(a.problem) CONTAINS toLower($keyword)
   OR toLower(a.field) CONTAINS toLower($domain_hint)
   OR toLower(a.name) CONTAINS toLower($keyword)
RETURN a.name AS analogy, a.problem AS problem_addressed,
       a.solution AS solution_pattern, a.field AS source_field
LIMIT 1
"""

Q_ABSURD_SCENARIO = """
MATCH (s:AbsurdScenario)
WHERE toLower(s.description) CONTAINS toLower($keyword)
   OR toLower(s.base) CONTAINS toLower($keyword)
RETURN s.name AS scenario, s.base AS base_trend,
       s.extreme AS extreme_projection, s.insight AS insight,
       s.practical_innovation AS practical_innovation
LIMIT 1
"""

Q_PROBLEM_EXAMPLE = """
MATCH (pe:ProblemExample)
WHERE toLower(pe.description) CONTAINS toLower($keyword)
   OR toLower(pe.name) CONTAINS toLower($keyword)
RETURN pe.name AS example, pe.classification AS classification,
       pe.transformation_path AS transformation,
       pe.characteristics AS characteristics
LIMIT 1
"""

Q_REVERSE_SALIENT = """
MATCH (rs:ReverseSalient)
WHERE toLower(rs.description) CONTAINS toLower($keyword)
   OR toLower(rs.core_challenge) CONTAINS toLower($keyword)
RETURN rs.name AS reverse_salient, rs.domain_a AS domain_a,
       rs.domain_b AS domain_b, rs.core_challenge AS challenge,
       rs.innovation AS innovation, rs.description AS description
ORDER BY rs.breakthrough_potential DESC
LIMIT 1
"""

Q_BEAUTIFUL_QUESTION = """
MATCH (bq:BeautifulQuestion)
WHERE (bq.text IS NOT NULL OR bq.question IS NOT NULL)
  AND (ANY(d IN bq.domains WHERE toLower(d) CONTAINS toLower($domain))
       OR toLower(bq.essence) CONTAINS toLower($keyword))
RETURN COALESCE(bq.text, bq.question, bq.proposed_question) AS question,
       bq.essence AS essence, bq.paradigm_shift AS paradigm_shift,
       bq.quality AS quality
ORDER BY bq.quality DESC
LIMIT 1
"""

Q_ANTIPATTERN = """
MATCH (ap:AntiPattern)
WHERE ANY(ws IN ap.warning_signs WHERE toLower(ws) CONTAINS toLower($keyword))
   OR toLower(ap.description) CONTAINS toLower($keyword)
RETURN ap.name AS antipattern, ap.description AS description,
       ap.warning_signs AS warning_signs, ap.mitigation AS mitigation
LIMIT 1
"""


async def _neo4j_query(cypher: str, params: dict) -> Dict:
    """Run a single Cypher query, return first result or empty dict."""
    try:
        from tools.graphrag_lite import get_neo4j_driver
        driver = get_neo4j_driver()
        if not driver:
            return {}
        with driver.session() as session:
            result = session.run(cypher, params)
            record = result.single()
            return dict(record) if record else {}
    except Exception as e:
        logger.debug(f"Neo4j query failed: {e}")
        return {}


async def fetch_neo4j_context(diagnosis: Dict) -> Dict[str, Any]:
    """Run all Neo4j queries in parallel. ONE result per category."""
    keywords = diagnosis.get("neo4j_keywords", [])
    keyword = keywords[0] if keywords else ""
    domain_hint = diagnosis.get("example_domain_hint", "technology")
    example_type = diagnosis.get("example_type", "analogy")

    if not keyword:
        return {}

    # Select example query based on type
    example_queries = {
        "analogy": (Q_ANALOGY, {"keyword": keyword, "domain_hint": domain_hint}),
        "absurd_scenario": (Q_ABSURD_SCENARIO, {"keyword": keyword}),
        "problem_example": (Q_PROBLEM_EXAMPLE, {"keyword": keyword}),
        "reverse_salient": (Q_REVERSE_SALIENT, {"keyword": keyword}),
    }
    ex_query, ex_params = example_queries.get(example_type, example_queries["analogy"])

    results = await asyncio.gather(
        _neo4j_query(Q_PROBLEM_TYPE, {"keyword": keyword}),
        _neo4j_query(Q_REFRAME, {"keyword": keyword}),
        _neo4j_query(Q_PERCEPTION_GAP, {"keyword": keyword}),
        _neo4j_query(ex_query, ex_params),
        _neo4j_query(Q_BEAUTIFUL_QUESTION, {"domain": domain_hint, "keyword": keyword}),
        _neo4j_query(Q_ANTIPATTERN, {"keyword": keyword}),
        return_exceptions=True,
    )

    # Handle exceptions gracefully
    safe_results = []
    for r in results:
        if isinstance(r, Exception):
            safe_results.append({})
        else:
            safe_results.append(r)

    return {
        "problem_type": safe_results[0],
        "reframe": safe_results[1],
        "perception_gap": safe_results[2],
        "example": safe_results[3],
        "beautiful_question": safe_results[4],
        "antipattern": safe_results[5],
    }


# ============================================================================
# v2.1 CONTEXT XML BUILDER
# ============================================================================

def build_diagnosis_xml(diagnosis: Dict, neo4j_data: Dict, file_chunks: List = None) -> str:
    """Build the <diagnosis> XML context for the generator."""
    parts = ["<diagnosis>"]

    # Problem type
    pt = neo4j_data.get("problem_type", {})
    parts.append(f"""  <problem_type>
    Type: {diagnosis.get('problem_type', 'ill-defined')}
    Definition: {pt.get('definition', 'N/A')}
    Key Question: {pt.get('key_question', 'N/A')}
    Approach: {pt.get('approach', 'N/A')}
  </problem_type>""")

    # Thinking error
    parts.append(f"""  <thinking_error>
    Error: {diagnosis.get('thinking_error', 'jumping_to_solutions')}
    Mental Move: from '{diagnosis.get('mental_move', {}).get('from', '?')}' to '{diagnosis.get('mental_move', {}).get('to', '?')}'
  </thinking_error>""")

    # Mental move
    mm = diagnosis.get("mental_move", {})
    parts.append(f"""  <mental_move>
    From: {mm.get('from', 'solutions')}
    To: {mm.get('to', 'problem definition')}
  </mental_move>""")

    # Reframe
    rf = neo4j_data.get("reframe", {})
    parts.append(f"""  <reframe>
    Current thinking: {rf.get('student_is_thinking', 'N/A')}
    Larry reframes to: {rf.get('larry_reframes_to', diagnosis.get('reframe_sentence', 'N/A'))}
    Impact: {rf.get('impact', 'N/A')}
  </reframe>""")

    # Example
    ex = neo4j_data.get("example", {})
    if ex:
        ex_text = " | ".join(f"{k}: {v}" for k, v in ex.items() if v)
        parts.append(f"  <example>{ex_text}</example>")

    # Beautiful question
    bq = neo4j_data.get("beautiful_question", {})
    if bq.get("question"):
        parts.append(f"  <closing_provocation>{bq['question']}</closing_provocation>")

    # Perception gap
    pg = neo4j_data.get("perception_gap", {})
    if pg.get("what_larry_sees"):
        parts.append(f"""  <perception_gap>
    Student sees: {pg.get('what_student_sees', 'N/A')}
    Larry sees: {pg.get('what_larry_sees', 'N/A')}
    Insight: {pg.get('insight', 'N/A')}
  </perception_gap>""")

    # Larry hook
    parts.append(f"  <larry_hook>{diagnosis.get('larry_hook', 'Let me stop you right there...')}</larry_hook>")

    # Voice mode and energy
    parts.append(f"  <voice_mode>{diagnosis.get('voice_mode', 'interrupter')}</voice_mode>")
    parts.append(f"  <energy_state>{diagnosis.get('energy_state', 'tired')}</energy_state>")

    # File search chunks
    if file_chunks:
        chunks_text = "\n".join(c.get("text", "")[:200] for c in file_chunks[:3])
        parts.append(f"  <reference_material>{chunks_text}</reference_material>")

    parts.append("</diagnosis>")
    return "\n".join(parts)


# ============================================================================
# v2.1 SCRIPT GENERATION
# ============================================================================

async def generate_larry_script(
    user_query: str,
    context_xml: str,
    conversation_summary: str = "",
    prior_failures: List[str] = None,
) -> str:
    """Generate Larry's intervention script. Uses Gemini with v2.1 system prompt."""
    failure_context = ""
    if prior_failures:
        failure_context = f"\n\nPREVIOUS ATTEMPT FAILED THESE CHECKS - FIX THEM:\n" + "\n".join(f"- {f}" for f in prior_failures)

    generation_prompt = f"""{LARRY_SYSTEM_PROMPT_V21}

STUDENT'S QUESTION:
{user_query}

CONVERSATION CONTEXT (what the student has been working on):
{conversation_summary if conversation_summary else 'No prior conversation.'}

SYSTEM-PROVIDED CONTEXT (use as subtext, never as content):
{context_xml}
{failure_context}

Generate the spoken script now. 250-350 words. Return ONLY Larry's words."""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=generation_prompt,
            config=types.GenerateContentConfig(
                temperature=0.75,
                max_output_tokens=800,
            ),
        )

        script = response.text.strip()
        # Clean any markdown formatting that might sneak in
        script = re.sub(r'^#+\s+.*$', '', script, flags=re.MULTILINE)
        script = re.sub(r'\*\*([^*]+)\*\*', r'\1', script)
        script = re.sub(r'\*([^*]+)\*', r'\1', script)
        script = script.strip()
        return script

    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        # Hardcoded fallback
        hook = "Let me stop you right there..."
        return f"""{hook} because the way you're asking this tells me something important.

The real question isn't what you asked. It's why you're asking it that way... you jumped to an answer before you finished understanding the shape of the problem.

Notice what you just did. You gave me a solution dressed up as a question. That's not a problem statement... that's avoidance. You're treating this like it has clean edges. It doesn't.

Here's what most people miss. The constraint you're working around... that's not a wall. It's a signal. It's telling you where the real stakes are. But you walked right past it because naming it would mean admitting this is messier than you want it to be. If that feels clean, you're avoiding the real problem.

Think about aviation safety. For decades they tried to eliminate human error... more training, more checklists, more automation. Nothing moved the needle. Then someone asked a different question... not how to prevent mistakes, but how to make mistakes survivable. That reframe changed everything. Not better answers. Better questions.

Take a piece of paper. Write down the three things you're most certain about in your situation. [pause] Now pick the one that would cause the most damage if it turned out to be wrong. That's your real artifact. That's where the edges are. Everything else is just noise shaped like progress.

Write it down. Go."""


# ============================================================================
# AUDIO GENERATION (ElevenLabs)
# ============================================================================

async def convert_to_audio(script: str) -> Optional[bytes]:
    """Convert script to audio using ElevenLabs with Larry's voice settings."""
    try:
        from elevenlabs import ElevenLabs, VoiceSettings

        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not set - no audio")
            return None

        client = ElevenLabs(api_key=api_key)

        # Larry's voice settings per v2.1 spec
        voice_settings = VoiceSettings(
            stability=0.72,
            similarity_boost=0.78,
            style=0.30,
            use_speaker_boost=True,
        )

        # Clean script for TTS
        tts_text = script.replace("[pause]", "... ... ...")
        tts_text = tts_text[:5000]  # Safety limit

        audio_stream = client.text_to_speech.convert_as_stream(
            text=tts_text,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings,
        )

        import io
        audio_buffer = io.BytesIO()
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                audio_buffer.write(chunk)

        audio_bytes = audio_buffer.getvalue()

        if len(audio_bytes) < 100:
            logger.warning("Audio too small, likely failed")
            return None

        logger.info(f"[LarryTeachMe] Generated audio ({len(audio_bytes)} bytes)")
        return audio_bytes

    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e}")
        return None


# ============================================================================
# FILESEARCH INTEGRATION
# ============================================================================

async def get_larry_material(query: str, framework_hint: str) -> List[Dict[str, str]]:
    """Pull Larry-specific phrasing and examples. HARD LIMIT: 3 chunks."""
    try:
        from google import genai

        client = genai.Client(
            api_key=os.environ.get("GOOGLE_FILESEARCH_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )

        search_query = f"Larry Aronhime teaching {framework_hint} {query[:50]}"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=search_query,
            config={
                "tools": [{"google_search": {"file_search_store": FILESEARCH_STORE_ID}}],
                "temperature": 0.3,
                "max_output_tokens": 400,
            },
        )

        if response and response.text:
            return [{"text": response.text[:300], "query": search_query}]

        return []

    except Exception as e:
        logger.debug(f"FileSearch failed: {e}")
        return []


# ============================================================================
# MAIN ORCHESTRATION PIPELINE v2.1
# ============================================================================

async def larry_teach_me(
    query: str,
    conversation_history: List[Dict[str, str]] = None,
    user_history: List[str] = None,
    include_audio: bool = True,
) -> Dict[str, Any]:
    """
    v2.1 Complete cognitive intervention pipeline.

    Gate -> Orchestrate (AI) -> Neo4j (parallel) -> FileSearch -> Generate -> Lint loop -> Voice

    Args:
        query: The user's current question/problem
        conversation_history: FULL conversation history [{role, content}, ...]
        user_history: Previous user queries (for repeat detection)
        include_audio: Whether to generate ElevenLabs audio

    Returns:
        {
            "status": "success" | "refused",
            "audio_bytes": bytes | None,
            "transcript": str,
            "diagnosis": {problem_type, thinking_error, voice_mode, mental_move},
            "thinking_exercise": str,
            "cta": str,
            "refusal_reason": str | None,
            "refusal_response": str | None,
        }
    """
    conversation_history = conversation_history or []
    user_history = user_history or []

    # ── STEP 0: ORCHESTRATE (AI-based diagnosis with full context) ──
    logger.info(f"[LarryTeachMe] Diagnosing: {query[:80]}...")
    diagnosis = await orchestrator_diagnose(query, conversation_history, user_history)

    # ── GATE: Should we teach? ──
    if not diagnosis.get("should_teach", True):
        reason = diagnosis.get("refusal_reason", "too_vague")
        logger.info(f"[LarryTeachMe] Refused: {reason}")
        return {
            "status": "refused",
            "audio_bytes": None,
            "transcript": "",
            "diagnosis": diagnosis,
            "thinking_exercise": "",
            "cta": "Rewrite your question.",
            "refusal_reason": reason,
            "refusal_response": REFUSAL_RESPONSES.get(reason, "Give me the real problem."),
        }

    # ── STEP 1: NEO4J + FILESEARCH (parallel) ──
    logger.info("[LarryTeachMe] Fetching Neo4j context + materials...")
    neo4j_data, file_chunks = await asyncio.gather(
        fetch_neo4j_context(diagnosis),
        get_larry_material(query, diagnosis.get("thinking_error", "problem")),
    )

    # ── STEP 2: BUILD CONTEXT XML ──
    # Build conversation summary for the generator
    conv_summary = ""
    if conversation_history:
        recent = conversation_history[-10:]
        for msg in recent:
            role = "Student" if msg.get("role") == "user" else "AI"
            content = msg.get("content", "")[:300]
            conv_summary += f"{role}: {content}\n"

    context_xml = build_diagnosis_xml(diagnosis, neo4j_data, file_chunks)

    # ── STEP 3: GENERATE + LINT LOOP ──
    logger.info("[LarryTeachMe] Generating intervention script...")
    script = ""
    lint_result = {"passed": False, "failures": []}

    for attempt in range(MAX_REGENERATIONS + 1):
        script = await generate_larry_script(
            user_query=query,
            context_xml=context_xml,
            conversation_summary=conv_summary,
            prior_failures=lint_result["failures"] if attempt > 0 else None,
        )

        lint_result = lint_larry_script(script)

        if lint_result["passed"]:
            logger.info(f"[LarryTeachMe] Script passed lint on attempt {attempt + 1}")
            break

        if attempt < MAX_REGENERATIONS:
            logger.info(f"[LarryTeachMe] Lint failed (attempt {attempt + 1}), regenerating: {lint_result['failures']}")
        else:
            logger.warning(f"[LarryTeachMe] Using imperfect script after {MAX_REGENERATIONS + 1} attempts: {lint_result['failures']}")

    # ── STEP 4: GENERATE AUDIO ──
    audio_bytes = None
    if include_audio:
        logger.info("[LarryTeachMe] Converting to audio via ElevenLabs...")
        audio_bytes = await convert_to_audio(script)
        if not audio_bytes:
            logger.warning("[LarryTeachMe] Audio generation failed - returning text only")

    # ── STEP 5: EXTRACT EXERCISE ──
    thinking_exercise = _extract_exercise(script)

    return {
        "status": "success",
        "audio_bytes": audio_bytes,
        "transcript": script,
        "diagnosis": {
            "problem_type": diagnosis.get("problem_type", "unknown"),
            "thinking_error": diagnosis.get("thinking_error", "unknown"),
            "voice_mode": diagnosis.get("voice_mode", "interrupter"),
            "mental_move": diagnosis.get("mental_move", {}),
            "framework_used": "PWS Methodology",  # Never expose internal framework
        },
        "thinking_exercise": thinking_exercise,
        "cta": "Rewrite your question now.",
        "refusal_reason": None,
        "refusal_response": None,
        "lint_result": lint_result,
    }


def _extract_exercise(script: str) -> str:
    """Extract the thinking exercise from the end of the script."""
    patterns = [
        r"(?:Here's what I want you to do|Take a piece of paper|Write this down|Write down)[^.]*\.(.+?)(?:Go\.|Start there\.|Do that\.|Write it down\.)",
        r"(?:Here's your exercise|Your exercise)[^.]*\.(.+?)(?:Go\.|Start there\.)",
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
# LEGACY COMPATIBILITY
# ============================================================================

async def generate_quick_lecture(
    question: str,
    context: str = "",
    include_audio: bool = True,
) -> Tuple[Optional[bytes], str, Dict[str, Any]]:
    """Legacy wrapper for backward compatibility."""
    result = await larry_teach_me(query=question, include_audio=include_audio)

    metadata = {
        "question": question[:100],
        "problem_type": result["diagnosis"].get("problem_type", "unknown"),
        "thinking_error": result["diagnosis"].get("thinking_error", "unknown"),
        "framework_used": result["diagnosis"].get("framework_used", "unknown"),
        "audio_generated": result["audio_bytes"] is not None,
        "status": result["status"],
    }

    if result["status"] == "refused":
        return None, result["refusal_response"], metadata

    return result["audio_bytes"], result["transcript"], metadata


# ============================================================================
# TEACHABLE MOMENT DETECTION
# ============================================================================

TEACHABLE_MOMENT_SIGNALS = {
    "explicit_teaching_requests": [
        "teach me", "give me a lecture", "explain this to me",
        "help me understand", "break this down", "walk me through",
        "show me how", "guide me", "mentor me", "coach me",
        "what should i learn", "go on teach", "tell me more",
        "educate me", "school me",
    ],
    "stuck_signals": [
        "i'm stuck", "don't know where to start", "overwhelmed",
        "this is too big", "too complex", "can't figure out",
        "what do i do first", "where do i begin",
        "help me focus", "narrow this down",
    ],
    "thinking_errors": {
        "stuck_signals": [
            "i'm stuck", "don't know where to start", "not sure",
            "can't figure out", "confused about", "struggling with",
        ],
        "assumption_signals": [
            "i assume", "probably", "obviously", "everyone knows",
            "the only way", "must be",
        ],
        "wrong_question_signals": [
            "should i x or y", "which is better", "best way to",
            "what's the right", "how do i implement",
        ],
        "premature_solution_signals": [
            "let me build", "i'll just create", "quick solution",
            "easy fix", "just need to",
        ],
    },
    "min_words": 15,
    "confidence_threshold": 0.5,
}


def analyze_for_teachable_moment(
    recent_messages: List[Dict[str, str]],
    turn_count: int,
) -> Dict[str, Any]:
    """Analyze recent conversation for teachable moments."""
    result = {
        "should_offer_intervention": False,
        "confidence": 0.0,
        "detected_signals": [],
        "suggested_framework": None,
        "larry_might_say": None,
        "explicit_request": False,
    }

    if turn_count < 3:
        return result

    user_messages = [
        msg.get("content", "") for msg in recent_messages
        if msg.get("role") == "user"
    ][-5:]

    combined_text = " ".join(user_messages).lower()

    # Explicit teaching requests
    for signal in TEACHABLE_MOMENT_SIGNALS["explicit_teaching_requests"]:
        if signal in combined_text:
            result["should_offer_intervention"] = True
            result["confidence"] = 1.0
            result["detected_signals"] = [signal]
            result["explicit_request"] = True
            result["larry_might_say"] = "You asked for teaching - let me give you a cognitive intervention."
            return result

    # Stuck signals
    for signal in TEACHABLE_MOMENT_SIGNALS["stuck_signals"]:
        if signal in combined_text:
            result["should_offer_intervention"] = True
            result["confidence"] = 0.8
            result["detected_signals"] = [signal]
            result["larry_might_say"] = "You seem stuck. Let me help reframe your thinking."
            return result

    if len(combined_text.split()) < TEACHABLE_MOMENT_SIGNALS["min_words"]:
        return result

    # Score thinking errors
    error_score = 0
    detected = []
    for error_type, signals in TEACHABLE_MOMENT_SIGNALS["thinking_errors"].items():
        matches = [s for s in signals if s in combined_text]
        if matches:
            error_score += len(matches) * 0.2
            detected.extend(matches)

    total_score = min(1.0, error_score)
    result["confidence"] = total_score
    result["detected_signals"] = detected[:5]

    if total_score >= TEACHABLE_MOMENT_SIGNALS["confidence_threshold"]:
        result["should_offer_intervention"] = True
        result["larry_might_say"] = "There's a thinking pattern here I can help with."

    return result


def should_show_larry_button(
    history: List[Dict[str, str]],
    turn_count: int,
    cached_analysis: Optional[Dict] = None,
) -> Tuple[bool, Optional[str]]:
    """Quick check if Larry button should appear."""
    recent_text = " ".join([
        m.get("content", "") for m in history[-3:]
        if m.get("role") == "user"
    ]).lower()

    explicit_signals = [
        "teach me", "give me a lecture", "help me understand",
        "break this down", "walk me through", "go on teach",
    ]
    for signal in explicit_signals:
        if signal in recent_text:
            return True, "Larry can give you a cognitive intervention!"

    stuck_signals = ["i'm stuck", "don't know where to start", "overwhelmed",
                     "can't figure out", "where do i begin"]
    for signal in stuck_signals:
        if signal in recent_text:
            return True, "You seem stuck - Larry can help reframe your thinking"

    if turn_count >= 3:
        if cached_analysis and cached_analysis.get("should_offer_intervention"):
            return True, cached_analysis.get("larry_might_say", "Larry can help")

        quick_signals = ["confused", "not sure", "should i", "best way", "problem is", "struggling"]
        if any(s in recent_text for s in quick_signals):
            return True, "Larry can offer a cognitive intervention"

    if turn_count >= 2:
        return True, None

    return False, None


def detect_explicit_teaching_request(message: str) -> bool:
    """Check if user is explicitly asking for teaching."""
    message_lower = message.lower()
    signals = [
        "teach me", "give me a lecture", "lecture me",
        "help me understand", "break this down for me",
        "walk me through", "show me how", "guide me",
        "go on teach", "educate me", "school me",
    ]
    return any(signal in message_lower for signal in signals)
