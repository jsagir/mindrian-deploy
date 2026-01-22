"""
Media utilities for Mindrian
Voice (ElevenLabs), Images, PDFs, Files, and more
"""

import os
import tempfile
import chainlit as cl
from typing import Optional
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
