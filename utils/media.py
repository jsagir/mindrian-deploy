"""
Media utilities for Mindrian
Voice (ElevenLabs), Images, PDFs, Files, Videos, and more
"""

import os
import io
import tempfile
import chainlit as cl
from typing import Optional, Dict
from pathlib import Path

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel

# Recommended voices for different use cases
ELEVENLABS_VOICES = {
    "professional_male": "JBFqnCBsd6RMkjVDRZzb",    # Adam
    "friendly_female": "EXAVITQu4vr4xnSDxMaL",     # Bella
    "assistant": "21m00Tcm4TlvDq8ikWAM",           # Rachel (default)
    "narrator": "pMsXgVXv3BLzUgSXRplF",            # Domi
    "calm": "Xb7hH8MSUJpSbvTk6ES5",               # Callum
}

# Model options:
# - eleven_multilingual_v2: Best quality, supports 29+ languages (recommended)
# - eleven_flash_v2_5: Faster, good quality
# - eleven_turbo_v2_5: Fastest, acceptable quality
DEFAULT_MODEL = "eleven_multilingual_v2"

# Cached ElevenLabs client
_elevenlabs_client = None


def get_elevenlabs_client():
    """Get or create ElevenLabs client."""
    global _elevenlabs_client

    if _elevenlabs_client is None and ELEVENLABS_API_KEY:
        try:
            from elevenlabs import ElevenLabs
            _elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            print("✅ ElevenLabs client initialized")
        except Exception as e:
            print(f"ElevenLabs init error: {e}")
            return None

    return _elevenlabs_client


async def text_to_speech(
    text: str,
    voice_id: str = None,
    model_id: str = None,
    stability: float = 0.71,
    similarity_boost: float = 0.75,
    use_speaker_boost: bool = True
) -> Optional[cl.Audio]:
    """
    Convert text to speech using ElevenLabs API with streaming.

    Args:
        text: Text to convert to speech (max 5000 chars)
        voice_id: ElevenLabs voice ID (default: Rachel)
        model_id: ElevenLabs model ID (default: eleven_multilingual_v2)
        stability: Voice stability (0.0-1.0, higher = more consistent)
        similarity_boost: Voice clarity/similarity (0.0-1.0)
        use_speaker_boost: Enable speaker boost for clearer audio

    Returns:
        cl.Audio element or None if failed
    """
    if not ELEVENLABS_API_KEY:
        print("ElevenLabs API key not configured")
        return None

    client = get_elevenlabs_client()
    if not client:
        return None

    try:
        from elevenlabs import VoiceSettings

        # Truncate text to ElevenLabs limit
        text = text[:5000]

        # Use streaming for better perceived latency
        audio_stream = client.text_to_speech.convert_as_stream(
            text=text,
            voice_id=voice_id or ELEVENLABS_VOICE_ID,
            model_id=model_id or DEFAULT_MODEL,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                use_speaker_boost=use_speaker_boost
            )
        )

        # Collect audio bytes from stream
        audio_buffer = io.BytesIO()
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                audio_buffer.write(chunk)

        audio_bytes = audio_buffer.getvalue()

        if len(audio_bytes) < 100:
            print("ElevenLabs: Audio data too small, possibly corrupt")
            return None

        # Return audio element with correct MIME type
        return cl.Audio(
            content=audio_bytes,
            mime="audio/mpeg",
            name="response.mp3"
        )

    except Exception as e:
        print(f"ElevenLabs TTS error: {e}")
        return None


async def text_to_speech_fast(
    text: str,
    voice_id: str = None
) -> Optional[cl.Audio]:
    """
    Fast text-to-speech using turbo model (lower quality, lower latency).

    Args:
        text: Text to convert
        voice_id: Voice ID

    Returns:
        cl.Audio element or None
    """
    return await text_to_speech(
        text=text,
        voice_id=voice_id,
        model_id="eleven_turbo_v2_5",
        stability=0.5,
        similarity_boost=0.5,
        use_speaker_boost=False
    )


def is_elevenlabs_configured() -> bool:
    """Check if ElevenLabs is configured."""
    return bool(ELEVENLABS_API_KEY)


async def create_pdf_element(
    file_path: str,
    name: str = "document.pdf",
    display: str = "side"
) -> cl.Pdf:
    """
    Create a PDF element for inline display.

    Args:
        file_path: Path to PDF file
        name: Display name
        display: "inline", "side", or "page"

    Returns:
        cl.Pdf element
    """
    return cl.Pdf(
        name=name,
        path=file_path,
        display=display
    )


async def create_image_element(
    path: str = None,
    url: str = None,
    name: str = "image",
    display: str = "inline"
) -> cl.Image:
    """
    Create an image element.

    Args:
        path: Local file path
        url: Remote URL
        name: Display name
        display: "inline", "side", or "page"

    Returns:
        cl.Image element
    """
    if path:
        return cl.Image(name=name, path=path, display=display)
    elif url:
        return cl.Image(name=name, url=url, display=display)
    return None


async def create_file_download(
    content: str,
    filename: str,
    mime_type: str = "text/markdown"
) -> cl.File:
    """
    Create a downloadable file from text content.

    Args:
        content: Text content
        filename: Download filename
        mime_type: MIME type

    Returns:
        cl.File element
    """
    # Save to temp file
    temp_path = tempfile.mktemp(suffix=Path(filename).suffix)
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)

    return cl.File(
        name=filename,
        path=temp_path,
        display="inline"
    )


async def export_workshop_summary(
    bot_name: str,
    phases: list,
    history: list,
    current_phase: int
) -> cl.File:
    """
    Export workshop progress as a downloadable markdown file.

    Args:
        bot_name: Name of the workshop bot
        phases: List of phase dicts
        history: Conversation history
        current_phase: Current phase index

    Returns:
        cl.File element for download
    """
    # Build markdown summary
    md = f"# {bot_name} Workshop Summary\n\n"
    md += f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    # Phase progress
    md += "## Workshop Progress\n\n"
    for i, phase in enumerate(phases):
        status = phase.get("status", "pending")
        emoji = {"done": "[x]", "running": "[~]", "ready": "[ ]", "pending": "[ ]"}.get(status, "[ ]")
        current = " <- Current" if i == current_phase else ""
        md += f"- {emoji} **Phase {i+1}:** {phase['name']}{current}\n"

    # Conversation highlights
    md += "\n## Key Discussion Points\n\n"
    for msg in history[-20:]:  # Last 20 messages
        role = msg.get("role", "user")
        content = msg.get("content", "")[:500]
        if role == "user":
            md += f"**You:** {content}\n\n"
        else:
            md += f"**Larry:** {content}\n\n"

    return await create_file_download(
        content=md,
        filename=f"{bot_name.lower().replace(' ', '_')}_summary.md"
    )


# Framework diagram URLs (hosted images for workshops)
FRAMEWORK_IMAGES = {
    "dikw": "https://upload.wikimedia.org/wikipedia/commons/0/06/DIKW_Pyramid.svg",
    "jtbd": "https://jobs-to-be-done.com/wp-content/uploads/2020/01/JTBD-Framework.png",
    "scurve": "https://upload.wikimedia.org/wikipedia/commons/8/8b/S-curve_adoption.png",
    "design_thinking": "https://upload.wikimedia.org/wikipedia/commons/b/bd/Double_diamond.png",
}


async def get_framework_image(framework: str) -> Optional[cl.Image]:
    """
    Get a framework diagram image.

    Args:
        framework: Framework name (dikw, jtbd, scurve, etc.)

    Returns:
        cl.Image element or None
    """
    url = FRAMEWORK_IMAGES.get(framework.lower())
    if url:
        return await create_image_element(url=url, name=f"{framework}_diagram", display="inline")
    return None


# ============================================================================
# VIDEO SUPPORT
# ============================================================================

async def create_video_element(
    url: str = None,
    path: str = None,
    name: str = "video",
    display: str = "inline",
    autoplay: bool = False,
    loop: bool = False
) -> Optional[cl.Video]:
    """
    Create a video element for inline display.

    Args:
        url: Remote video URL (YouTube, Vimeo, direct MP4, etc.)
        path: Local file path to video
        name: Display name
        display: "inline", "side", or "page"
        autoplay: Whether to autoplay (default False)
        loop: Whether to loop (default False)

    Returns:
        cl.Video element or None if no source provided

    Supported URL formats:
        - YouTube: https://www.youtube.com/watch?v=VIDEO_ID
        - YouTube short: https://youtu.be/VIDEO_ID
        - Vimeo: https://vimeo.com/VIDEO_ID
        - Direct MP4: https://example.com/video.mp4
        - Supabase Storage URL
    """
    if url:
        return cl.Video(
            name=name,
            url=url,
            display=display
        )
    elif path:
        return cl.Video(
            name=name,
            path=path,
            display=display
        )
    return None


def extract_youtube_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.

    Args:
        url: YouTube URL

    Returns:
        Video ID or None
    """
    import re

    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_youtube_embed_url(video_id: str) -> str:
    """Convert YouTube video ID to embed URL."""
    return f"https://www.youtube.com/embed/{video_id}"


def get_youtube_thumbnail(video_id: str, quality: str = "hqdefault") -> str:
    """
    Get YouTube video thumbnail URL.

    Args:
        video_id: YouTube video ID
        quality: Thumbnail quality (default, mqdefault, hqdefault, sddefault, maxresdefault)

    Returns:
        Thumbnail URL
    """
    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"


# Workshop tutorial videos - configure per bot and phase
# Format: { "bot_id": { "intro": "url", "phase_1": "url", ... } }
WORKSHOP_VIDEOS: Dict[str, Dict[str, str]] = {
    "larry": {
        "intro": "",  # Add YouTube/video URL here
        "welcome": "",
    },
    "tta": {
        "intro": "",  # Trending to the Absurd intro video
        "phase_1": "",  # Trend Identification
        "phase_2": "",  # Extrapolation
        "phase_3": "",  # Absurd Scenarios
        "phase_4": "",  # Implications
        "phase_5": "",  # Opportunities
    },
    "jtbd": {
        "intro": "",  # Jobs to Be Done intro
        "phase_1": "",  # Job Discovery
        "phase_2": "",  # Job Mapping
        "phase_3": "",  # Solution Fit
    },
    "scurve": {
        "intro": "",  # S-Curve intro video
        "phase_1": "",  # Technology Assessment
        "phase_2": "",  # Curve Positioning
        "phase_3": "",  # Timing Strategy
    },
    "redteam": {
        "intro": "",  # Red Teaming intro
        "phase_1": "",  # Assumption Identification
        "phase_2": "",  # Attack Scenarios
        "phase_3": "",  # Mitigation Strategies
    },
    "ackoff": {
        "intro": "",  # Ackoff's Pyramid intro
        "phase_1": "",  # Team Onboarding
        "phase_2": "",  # Data Collection
        "phase_3": "",  # Information Synthesis
        "phase_4": "",  # Knowledge Building
        "phase_5": "",  # Understanding
        "phase_6": "",  # Wisdom Application
        "phase_7": "",  # Action Planning
        "phase_8": "",  # Debrief
    },
}


async def get_workshop_video(
    bot_id: str,
    phase: str = "intro"
) -> Optional[cl.Video]:
    """
    Get a tutorial video for a specific workshop bot and phase.

    Args:
        bot_id: Bot identifier (larry, tta, jtbd, scurve, redteam, ackoff)
        phase: Phase identifier (intro, phase_1, phase_2, etc.)

    Returns:
        cl.Video element or None if no video configured
    """
    bot_videos = WORKSHOP_VIDEOS.get(bot_id, {})
    video_url = bot_videos.get(phase, "") or bot_videos.get("intro", "")

    if not video_url:
        return None

    # Extract YouTube ID if it's a YouTube URL
    youtube_id = extract_youtube_id(video_url)
    if youtube_id:
        video_url = get_youtube_embed_url(youtube_id)

    return await create_video_element(
        url=video_url,
        name=f"{bot_id}_{phase}_tutorial",
        display="inline"
    )


async def get_video_with_thumbnail(
    url: str,
    name: str = "video"
) -> tuple[Optional[cl.Video], Optional[cl.Image]]:
    """
    Get video element and its thumbnail (for YouTube videos).

    Args:
        url: Video URL
        name: Display name

    Returns:
        Tuple of (Video element, Thumbnail image element)
    """
    video = await create_video_element(url=url, name=name)
    thumbnail = None

    youtube_id = extract_youtube_id(url)
    if youtube_id:
        thumbnail_url = get_youtube_thumbnail(youtube_id)
        thumbnail = await create_image_element(
            url=thumbnail_url,
            name=f"{name}_thumbnail",
            display="inline"
        )

    return video, thumbnail


def set_workshop_video(bot_id: str, phase: str, url: str):
    """
    Set a video URL for a specific workshop phase.

    Args:
        bot_id: Bot identifier
        phase: Phase identifier
        url: Video URL (YouTube, Vimeo, or direct)
    """
    if bot_id not in WORKSHOP_VIDEOS:
        WORKSHOP_VIDEOS[bot_id] = {}
    WORKSHOP_VIDEOS[bot_id][phase] = url


def list_configured_videos() -> Dict[str, list]:
    """
    List all bots and their configured video phases.

    Returns:
        Dict of bot_id -> list of phases with videos
    """
    result = {}
    for bot_id, phases in WORKSHOP_VIDEOS.items():
        configured = [phase for phase, url in phases.items() if url]
        if configured:
            result[bot_id] = configured
    return result


# ============================================================================
# PWS AUDIOBOOK CHAPTERS
# ============================================================================

# Audiobook chapter configuration by topic/methodology
# Format: { "topic": { "chapter_id": { "title": "...", "url": "...", "duration": "...", "keywords": [...] } } }
AUDIOBOOK_CHAPTERS: Dict[str, Dict[str, Dict]] = {
    "pws_foundation": {
        "chapter_1": {
            "title": "Introduction to Problems Worth Solving",
            "url": "",  # Add Supabase Storage or direct URL
            "duration": "15:00",
            "keywords": ["problem", "worth solving", "introduction", "overview", "pws"],
            "bot_relevance": ["larry"],
        },
        "chapter_2": {
            "title": "The Nature of Problems",
            "url": "",
            "duration": "12:00",
            "keywords": ["problem types", "tame", "wicked", "complex"],
            "bot_relevance": ["larry", "ackoff"],
        },
        "chapter_3": {
            "title": "Problem vs Solution Mindset",
            "url": "",
            "duration": "10:00",
            "keywords": ["solution", "mindset", "premature", "assumption"],
            "bot_relevance": ["larry", "redteam"],
        },
    },
    "trending_to_absurd": {
        "chapter_1": {
            "title": "Why Extrapolate Trends?",
            "url": "",
            "duration": "8:00",
            "keywords": ["trend", "extrapolate", "future", "absurd"],
            "bot_relevance": ["tta"],
        },
        "chapter_2": {
            "title": "Identifying Meaningful Trends",
            "url": "",
            "duration": "12:00",
            "keywords": ["trend", "signal", "noise", "meaningful"],
            "bot_relevance": ["tta"],
        },
        "chapter_3": {
            "title": "From Trend to Absurd Conclusion",
            "url": "",
            "duration": "14:00",
            "keywords": ["absurd", "extreme", "conclusion", "implication"],
            "bot_relevance": ["tta"],
        },
    },
    "jobs_to_be_done": {
        "chapter_1": {
            "title": "What Jobs Do Customers Hire Products For?",
            "url": "",
            "duration": "10:00",
            "keywords": ["job", "customer", "hire", "product"],
            "bot_relevance": ["jtbd"],
        },
        "chapter_2": {
            "title": "Functional, Emotional, and Social Jobs",
            "url": "",
            "duration": "12:00",
            "keywords": ["functional", "emotional", "social", "job"],
            "bot_relevance": ["jtbd"],
        },
        "chapter_3": {
            "title": "The Struggling Moment",
            "url": "",
            "duration": "9:00",
            "keywords": ["struggle", "moment", "pain point", "switch"],
            "bot_relevance": ["jtbd"],
        },
    },
    "s_curve": {
        "chapter_1": {
            "title": "Technology S-Curves Explained",
            "url": "",
            "duration": "11:00",
            "keywords": ["s-curve", "technology", "adoption", "timing"],
            "bot_relevance": ["scurve"],
        },
        "chapter_2": {
            "title": "Era of Ferment vs Dominant Design",
            "url": "",
            "duration": "13:00",
            "keywords": ["ferment", "dominant design", "era", "transition"],
            "bot_relevance": ["scurve"],
        },
        "chapter_3": {
            "title": "Timing Your Entry",
            "url": "",
            "duration": "10:00",
            "keywords": ["timing", "entry", "too early", "too late"],
            "bot_relevance": ["scurve"],
        },
    },
    "ackoffs_pyramid": {
        "chapter_1": {
            "title": "Data, Information, Knowledge, Wisdom",
            "url": "",
            "duration": "12:00",
            "keywords": ["dikw", "data", "information", "knowledge", "wisdom"],
            "bot_relevance": ["ackoff"],
        },
        "chapter_2": {
            "title": "Climbing vs Descending the Pyramid",
            "url": "",
            "duration": "14:00",
            "keywords": ["climb", "descend", "validate", "explore"],
            "bot_relevance": ["ackoff"],
        },
        "chapter_3": {
            "title": "The Camera Test: Grounding in Data",
            "url": "",
            "duration": "10:00",
            "keywords": ["camera test", "ground", "data", "observable"],
            "bot_relevance": ["ackoff", "redteam"],
        },
    },
    "red_teaming": {
        "chapter_1": {
            "title": "The Art of Devil's Advocacy",
            "url": "",
            "duration": "9:00",
            "keywords": ["devil", "advocate", "challenge", "assumption"],
            "bot_relevance": ["redteam"],
        },
        "chapter_2": {
            "title": "Identifying Hidden Assumptions",
            "url": "",
            "duration": "11:00",
            "keywords": ["hidden", "assumption", "implicit", "explicit"],
            "bot_relevance": ["redteam"],
        },
        "chapter_3": {
            "title": "Attack Scenarios and Failure Modes",
            "url": "",
            "duration": "13:00",
            "keywords": ["attack", "failure", "scenario", "risk"],
            "bot_relevance": ["redteam"],
        },
    },
}

# Bot to topic mapping for automatic chapter suggestions
BOT_TOPIC_MAP = {
    "larry": ["pws_foundation"],
    "tta": ["trending_to_absurd", "pws_foundation"],
    "jtbd": ["jobs_to_be_done", "pws_foundation"],
    "scurve": ["s_curve", "pws_foundation"],
    "ackoff": ["ackoffs_pyramid", "pws_foundation"],
    "redteam": ["red_teaming", "pws_foundation"],
}


async def get_audiobook_chapter(
    topic: str,
    chapter_id: str
) -> Optional[cl.Audio]:
    """
    Get an audiobook chapter as cl.Audio element.

    Args:
        topic: Topic identifier (pws_foundation, trending_to_absurd, etc.)
        chapter_id: Chapter identifier (chapter_1, chapter_2, etc.)

    Returns:
        cl.Audio element or None if not found/configured
    """
    topic_chapters = AUDIOBOOK_CHAPTERS.get(topic, {})
    chapter = topic_chapters.get(chapter_id, {})
    url = chapter.get("url", "")

    if not url:
        return None

    try:
        # If it's a direct URL, fetch and return
        if url.startswith("http"):
            return cl.Audio(
                url=url,
                name=f"{chapter.get('title', 'audiobook')}.mp3",
                mime="audio/mpeg"
            )
        # If it's a local path
        elif os.path.exists(url):
            with open(url, "rb") as f:
                audio_bytes = f.read()
            return cl.Audio(
                content=audio_bytes,
                name=f"{chapter.get('title', 'audiobook')}.mp3",
                mime="audio/mpeg"
            )
    except Exception as e:
        print(f"Audiobook chapter error: {e}")

    return None


def find_relevant_chapters(
    text: str,
    bot_id: str = None,
    max_results: int = 3
) -> list[Dict]:
    """
    Find audiobook chapters relevant to the conversation context.

    Args:
        text: Conversation text to analyze for relevance
        bot_id: Current bot ID to prioritize relevant topics
        max_results: Maximum number of chapters to return

    Returns:
        List of chapter dicts with title, topic, chapter_id, and match_score
    """
    text_lower = text.lower()
    results = []

    # Determine relevant topics based on bot
    relevant_topics = BOT_TOPIC_MAP.get(bot_id, list(AUDIOBOOK_CHAPTERS.keys()))

    for topic in relevant_topics:
        if topic not in AUDIOBOOK_CHAPTERS:
            continue

        for chapter_id, chapter in AUDIOBOOK_CHAPTERS[topic].items():
            url = chapter.get("url", "")
            if not url:  # Skip unconfigured chapters
                continue

            # Calculate relevance score based on keyword matches
            keywords = chapter.get("keywords", [])
            match_count = sum(1 for kw in keywords if kw in text_lower)

            if match_count > 0:
                results.append({
                    "topic": topic,
                    "chapter_id": chapter_id,
                    "title": chapter.get("title", "Unknown"),
                    "duration": chapter.get("duration", ""),
                    "match_score": match_count,
                    "url": url,
                })

    # Sort by match score and return top results
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:max_results]


def get_chapters_for_bot(bot_id: str) -> list[Dict]:
    """
    Get all configured audiobook chapters relevant to a specific bot.

    Args:
        bot_id: Bot identifier

    Returns:
        List of chapter info dicts
    """
    relevant_topics = BOT_TOPIC_MAP.get(bot_id, [])
    chapters = []

    for topic in relevant_topics:
        if topic not in AUDIOBOOK_CHAPTERS:
            continue

        for chapter_id, chapter in AUDIOBOOK_CHAPTERS[topic].items():
            if chapter.get("url"):  # Only include configured chapters
                chapters.append({
                    "topic": topic,
                    "chapter_id": chapter_id,
                    "title": chapter.get("title", "Unknown"),
                    "duration": chapter.get("duration", ""),
                })

    return chapters


def set_audiobook_chapter(topic: str, chapter_id: str, url: str, **kwargs):
    """
    Set or update an audiobook chapter URL.

    Args:
        topic: Topic identifier
        chapter_id: Chapter identifier
        url: Audio file URL (Supabase Storage, direct MP3, etc.)
        **kwargs: Additional metadata (title, duration, keywords)
    """
    if topic not in AUDIOBOOK_CHAPTERS:
        AUDIOBOOK_CHAPTERS[topic] = {}

    if chapter_id not in AUDIOBOOK_CHAPTERS[topic]:
        AUDIOBOOK_CHAPTERS[topic][chapter_id] = {}

    AUDIOBOOK_CHAPTERS[topic][chapter_id]["url"] = url

    # Update other metadata if provided
    for key, value in kwargs.items():
        AUDIOBOOK_CHAPTERS[topic][chapter_id][key] = value


def list_configured_audiobook_chapters() -> Dict[str, list]:
    """
    List all topics and their configured audiobook chapters.

    Returns:
        Dict of topic -> list of configured chapter IDs
    """
    result = {}
    for topic, chapters in AUDIOBOOK_CHAPTERS.items():
        configured = [
            {
                "chapter_id": ch_id,
                "title": ch.get("title", "Unknown"),
                "duration": ch.get("duration", ""),
            }
            for ch_id, ch in chapters.items()
            if ch.get("url")
        ]
        if configured:
            result[topic] = configured
    return result
