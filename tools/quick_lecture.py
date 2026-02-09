"""
Quick Lecture Generator
=======================

Creates a mini audio lecture using:
1. FileSearch - finds relevant PWS course materials
2. Claude - synthesizes a focused 2-3 minute lecture script
3. ElevenLabs - converts script to audio

Usage:
    from tools.quick_lecture import generate_quick_lecture

    audio, script = await generate_quick_lecture(
        question="How do I validate my assumptions?",
        context="User is working on a fintech startup idea"
    )
"""

import os
import asyncio
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("quick_lecture")

# Configuration
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "SGh5MKvZcSYNF0SZXlAg")  # Larry voice
FILESEARCH_STORE_ID = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"


async def query_neo4j_frameworks(question: str) -> Dict[str, Any]:
    """
    Query Neo4j to find relevant frameworks and methodologies for the question.

    Returns dict with frameworks, tools, concepts, and example queries.
    """
    try:
        from tools.graphrag_lite import get_neo4j_driver

        driver = get_neo4j_driver()
        if not driver:
            return {"frameworks": [], "tools": [], "concepts": []}

        # Extract keywords from question for matching
        keywords = question.lower().split()

        with driver.session() as session:
            # Find relevant frameworks
            frameworks_result = session.run("""
                MATCH (f:Framework)
                WHERE ANY(word IN $keywords WHERE toLower(f.name) CONTAINS word)
                   OR ANY(word IN $keywords WHERE toLower(f.description) CONTAINS word)
                RETURN f.name AS name, f.description AS description,
                       f.when_to_use AS when_to_use
                LIMIT 5
            """, {"keywords": keywords})
            frameworks = [dict(r) for r in frameworks_result]

            # Find relevant tools/exercises
            tools_result = session.run("""
                MATCH (t:Tool)
                WHERE ANY(word IN $keywords WHERE toLower(t.name) CONTAINS word)
                   OR ANY(word IN $keywords WHERE toLower(t.purpose) CONTAINS word)
                RETURN t.name AS name, t.purpose AS purpose
                LIMIT 5
            """, {"keywords": keywords})
            tools = [dict(r) for r in tools_result]

            # Find concepts
            concepts_result = session.run("""
                MATCH (c:Concept)
                WHERE ANY(word IN $keywords WHERE toLower(c.name) CONTAINS word)
                RETURN c.name AS name, c.definition AS definition
                LIMIT 5
            """, {"keywords": keywords})
            concepts = [dict(r) for r in concepts_result]

            # If no keyword matches, get general PWS frameworks
            if not frameworks:
                general_result = session.run("""
                    MATCH (f:Framework)
                    WHERE f.name IN ['JTBD', 'TTA', 'Beautiful Questions', 'Reverse Salient', 'Camera Test']
                    RETURN f.name AS name, f.description AS description
                    LIMIT 5
                """)
                frameworks = [dict(r) for r in general_result]

        logger.info(f"[Neo4j] Found {len(frameworks)} frameworks, {len(tools)} tools, {len(concepts)} concepts")
        return {
            "frameworks": frameworks,
            "tools": tools,
            "concepts": concepts
        }

    except Exception as e:
        logger.warning(f"Neo4j query failed: {e}")
        return {"frameworks": [], "tools": [], "concepts": []}


def format_neo4j_context(neo4j_data: Dict[str, Any]) -> str:
    """Format Neo4j results for the lecture prompt."""
    parts = []

    if neo4j_data.get("frameworks"):
        parts.append("RELEVANT FRAMEWORKS:")
        for f in neo4j_data["frameworks"]:
            parts.append(f"- {f.get('name', 'Unknown')}: {f.get('description', '')[:100]}")

    if neo4j_data.get("tools"):
        parts.append("\nRELEVANT TOOLS/EXERCISES:")
        for t in neo4j_data["tools"]:
            parts.append(f"- {t.get('name', 'Unknown')}: {t.get('purpose', '')[:100]}")

    if neo4j_data.get("concepts"):
        parts.append("\nKEY CONCEPTS:")
        for c in neo4j_data["concepts"]:
            parts.append(f"- {c.get('name', 'Unknown')}: {c.get('definition', '')[:100]}")

    return "\n".join(parts) if parts else "Use general PWS methodology frameworks."


LECTURE_PROMPT = """You are Lawrence Aronhime, a master teacher of the PWS (Problems Worth Solving) methodology.

Create a focused 2-3 minute mini-lecture that helps the student push their thinking further on their question.

STUDENT'S QUESTION:
{question}

CONTEXT:
{context}

RELEVANT PWS FRAMEWORKS (from knowledge graph):
{frameworks}

RELEVANT PWS MATERIALS (from course content):
{materials}

INSTRUCTIONS:
1. Open with a thought-provoking hook related to their question
2. Share 2-3 key insights from PWS methodology that apply
3. Give them a specific "thinking exercise" or question to work on
4. End with encouragement and a clear next step

STYLE:
- Conversational and warm, like a mentor speaking directly to them
- Use "you" language - make it personal
- Include brief pauses (write "..." for natural speech rhythm)
- Keep it focused - this is a mini-lecture, not a full course
- Reference specific PWS concepts (reverse salients, beautiful questions, JTBD, etc.)

Write the lecture script (300-500 words). Do NOT include stage directions or speaker labels - just the spoken words."""


async def search_filesearch(query: str) -> str:
    """Search PWS FileSearch for relevant materials."""
    try:
        from google import genai

        client = genai.Client(api_key=os.environ.get("GOOGLE_FILESEARCH_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"PWS methodology guidance for: {query[:300]}",
            config={
                "tools": [{"google_search": {"file_search_store": FILESEARCH_STORE_ID}}],
                "temperature": 0.3,
                "max_output_tokens": 800,
            },
        )

        if response and response.text:
            return response.text[:1500]

    except Exception as e:
        logger.warning(f"FileSearch failed: {e}")

    return "No specific materials found - use general PWS methodology knowledge."


async def generate_lecture_script(
    question: str,
    context: str = "",
    materials: str = "",
    frameworks: str = ""
) -> str:
    """Generate lecture script using Claude."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        prompt = LECTURE_PROMPT.format(
            question=question,
            context=context or "General PWS exploration",
            frameworks=frameworks or "Use general PWS methodology frameworks",
            materials=materials or "Use general PWS methodology knowledge"
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        script = response.content[0].text
        logger.info(f"[QuickLecture] Generated script ({len(script)} chars)")
        return script

    except Exception as e:
        logger.error(f"Claude script generation failed: {e}")
        # Fallback to Gemini
        return await _generate_script_gemini(question, context, materials, frameworks)


async def _generate_script_gemini(
    question: str,
    context: str = "",
    materials: str = "",
    frameworks: str = ""
) -> str:
    """Fallback script generation using Gemini."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

        prompt = LECTURE_PROMPT.format(
            question=question,
            context=context or "General PWS exploration",
            frameworks=frameworks or "Use general PWS methodology frameworks",
            materials=materials or "Use general PWS methodology knowledge"
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000
            )
        )

        return response.text

    except Exception as e:
        logger.error(f"Gemini script generation failed: {e}")
        return f"""Let me share some thoughts on your question about {question[:50]}...

The PWS methodology teaches us that the best innovations come from deeply understanding problems before jumping to solutions.

Here's a thinking exercise for you: Take your question and ask "Why?" five times. Each answer reveals a deeper layer of the problem.

What assumptions are you making? Write them down, then ask yourself - what would have to be true for each assumption to be wrong?

Keep pushing your thinking. The best insights come when we challenge our own certainties."""


async def convert_to_audio(script: str) -> Optional[bytes]:
    """Convert script to audio using ElevenLabs."""
    try:
        from elevenlabs import ElevenLabs, VoiceSettings

        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not set")
            return None

        client = ElevenLabs(api_key=api_key)

        # Truncate to ElevenLabs limit
        script = script[:5000]

        audio_stream = client.text_to_speech.convert_as_stream(
            text=script,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.71,
                similarity_boost=0.75,
                use_speaker_boost=True
            )
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

        logger.info(f"[QuickLecture] Generated audio ({len(audio_bytes)} bytes)")
        return audio_bytes

    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e}")
        return None


async def generate_quick_lecture(
    question: str,
    context: str = "",
    include_audio: bool = True
) -> Tuple[Optional[bytes], str, Dict[str, Any]]:
    """
    Generate a quick lecture for the user's question.

    Args:
        question: The user's question or problem
        context: Additional context (conversation history, etc.)
        include_audio: Whether to generate audio (default: True)

    Returns:
        Tuple of (audio_bytes, script_text, metadata)
    """
    metadata = {
        "question": question[:100],
        "neo4j_used": False,
        "filesearch_used": False,
        "claude_used": False,
        "audio_generated": False,
        "script_length": 0,
        "frameworks_found": [],
    }

    # 1. Query Neo4j for relevant frameworks
    logger.info(f"[QuickLecture] Querying Neo4j for: {question[:50]}...")
    neo4j_data = await query_neo4j_frameworks(question)
    frameworks_context = format_neo4j_context(neo4j_data)
    metadata["neo4j_used"] = bool(neo4j_data.get("frameworks"))
    metadata["frameworks_found"] = [f.get("name") for f in neo4j_data.get("frameworks", [])]

    # 2. Search FileSearch for relevant materials (enriched with framework context)
    search_query = question
    if neo4j_data.get("frameworks"):
        framework_names = ", ".join(metadata["frameworks_found"][:3])
        search_query = f"{question} (using {framework_names})"

    logger.info(f"[QuickLecture] Searching FileSearch...")
    materials = await search_filesearch(search_query)
    metadata["filesearch_used"] = "No specific materials" not in materials

    # 3. Generate lecture script with Claude
    logger.info("[QuickLecture] Generating script with Claude...")
    script = await generate_lecture_script(question, context, materials, frameworks_context)
    metadata["script_length"] = len(script)
    metadata["claude_used"] = True

    # 3. Convert to audio
    audio_bytes = None
    if include_audio:
        logger.info("[QuickLecture] Converting to audio...")
        audio_bytes = await convert_to_audio(script)
        metadata["audio_generated"] = audio_bytes is not None

    return audio_bytes, script, metadata


# Chainlit integration helper
async def create_lecture_message(question: str, context: str = "") -> Dict[str, Any]:
    """
    Create a lecture and return Chainlit-ready elements.

    Returns dict with 'audio', 'script', 'metadata' keys.
    """
    import chainlit as cl

    audio_bytes, script, metadata = await generate_quick_lecture(question, context)

    result = {
        "script": script,
        "metadata": metadata,
        "audio": None
    }

    if audio_bytes:
        result["audio"] = cl.Audio(
            content=audio_bytes,
            mime="audio/mpeg",
            name="quick_lecture.mp3"
        )

    return result
