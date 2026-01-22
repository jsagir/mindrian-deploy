"""
Media utilities for Mindrian
Voice (ElevenLabs), Images, PDFs, Files, Videos, and more
"""

import os
import tempfile
import chainlit as cl
from typing import Optional, Dict
from pathlib import Path

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel


async def text_to_speech(
    text: str,
    voice_id: str = None,
    model_id: str = "eleven_monolingual_v1"
) -> Optional[cl.Audio]:
    """
    Convert text to speech using ElevenLabs API.

    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (default: Rachel)
        model_id: ElevenLabs model ID

    Returns:
        cl.Audio element or None if failed
    """
    if not ELEVENLABS_API_KEY:
        return None

    try:
        from elevenlabs import generate, set_api_key

        set_api_key(ELEVENLABS_API_KEY)

        audio = generate(
            text=text[:5000],  # ElevenLabs limit
            voice=voice_id or ELEVENLABS_VOICE_ID,
            model=model_id
        )

        # Save to temp file
        temp_path = tempfile.mktemp(suffix=".mp3")
        with open(temp_path, "wb") as f:
            f.write(audio)

        return cl.Audio(
            name="larry_response.mp3",
            path=temp_path,
            display="inline"
        )

    except Exception as e:
        print(f"ElevenLabs error: {e}")
        return None


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
