"""
Mindrian Voice Module
=====================

Real-time voice chat using:
- Google Cloud STT (Speech-to-Text)
- Google Gemini (Intelligence)
- ElevenLabs TTS (Custom Voice)

Usage:
    # Start voice server (runs alongside Chainlit)
    python -m voice.realtime_server --port 8765

    # Or import and run programmatically
    from voice.realtime_server import start_voice_server
    asyncio.run(start_voice_server())
"""

from .realtime_server import (
    start_voice_server,
    VoiceSession,
    VoicePipeline,
    VOICE_AGENTS,
)

__all__ = [
    "start_voice_server",
    "VoiceSession",
    "VoicePipeline",
    "VOICE_AGENTS",
]
