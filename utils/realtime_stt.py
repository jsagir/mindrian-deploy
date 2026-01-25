"""
True Real-Time Speech-to-Text with Deepgram
============================================

Streams audio to Deepgram AS IT ARRIVES - no batching.
LLM response starts the instant user stops speaking.

Flow:
  on_audio_start → Open Deepgram WebSocket
  on_audio_chunk → Send immediately to Deepgram (no buffering)
  Deepgram UtteranceEnd → Trigger LLM + TTS pipeline instantly
  on_audio_end → Clean up

Requirements:
  - DEEPGRAM_API_KEY environment variable
  - pip install websockets
"""

import os
import asyncio
import json
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass, field
import uuid

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

# Configuration
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Deepgram models
MODEL_NOVA2 = "nova-2"  # Best accuracy, low latency
MODEL_NOVA = "nova"     # Good balance
MODEL_BASE = "base"     # Fastest, lower accuracy


@dataclass
class TranscriptResult:
    """Result from streaming transcription."""
    text: str
    is_final: bool
    confidence: float = 0.0
    words: list = field(default_factory=list)


def is_deepgram_enabled() -> bool:
    """Check if Deepgram is configured."""
    return bool(DEEPGRAM_API_KEY) and WEBSOCKETS_AVAILABLE


class LiveSTTSession:
    """
    Persistent WebSocket session for true real-time STT.

    Opens connection on start, streams chunks as they arrive,
    triggers callback immediately when utterance ends.

    Usage:
        session = LiveSTTSession(on_utterance_end=handle_transcript)
        await session.start()

        # In on_audio_chunk:
        await session.send_audio(chunk.data)

        # In on_audio_end:
        await session.stop()
    """

    def __init__(
        self,
        on_utterance_end: Callable[[str], Awaitable[None]] = None,
        on_interim: Callable[[str], Awaitable[None]] = None,
        on_speech_start: Callable[[], Awaitable[None]] = None,
        model: str = MODEL_NOVA2,
        language: str = "en",
        utterance_end_ms: int = 800,  # Faster detection
    ):
        self.on_utterance_end = on_utterance_end
        self.on_interim = on_interim
        self.on_speech_start = on_speech_start

        self.model = model
        self.language = language
        self.utterance_end_ms = utterance_end_ms

        self.ws = None
        self.receive_task = None
        self.is_running = False
        self.session_id = str(uuid.uuid4())[:8]

        # Accumulated transcript for the current utterance
        self.current_transcript = ""
        self.chunks_sent = 0

    @property
    def ws_url(self) -> str:
        """WebSocket URL for Deepgram streaming."""
        params = [
            f"model={self.model}",
            f"language={self.language}",
            "smart_format=true",
            "punctuate=true",
            "interim_results=true",
            f"utterance_end_ms={self.utterance_end_ms}",
            "vad_events=true",
            "encoding=linear16",
            "sample_rate=24000",
            "channels=1",
        ]
        return f"wss://api.deepgram.com/v1/listen?{'&'.join(params)}"

    async def start(self) -> bool:
        """
        Open WebSocket connection to Deepgram.
        Call this in on_audio_start.
        """
        if not DEEPGRAM_API_KEY:
            print(f"🎤 [{self.session_id}] Deepgram not configured")
            return False

        if not WEBSOCKETS_AVAILABLE:
            print(f"🎤 [{self.session_id}] websockets not installed")
            return False

        try:
            headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
            self.ws = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )
            self.is_running = True
            self.current_transcript = ""
            self.chunks_sent = 0

            # Start receiver task
            self.receive_task = asyncio.create_task(self._receive_loop())

            print(f"🎤 [{self.session_id}] Connected to Deepgram ({self.model})")
            return True

        except Exception as e:
            print(f"🎤 [{self.session_id}] Connection failed: {e}")
            return False

    async def send_audio(self, audio_data: bytes):
        """
        Send audio chunk immediately to Deepgram.
        Call this in on_audio_chunk - no buffering!
        """
        if not self.ws or not self.is_running:
            return

        try:
            await self.ws.send(audio_data)
            self.chunks_sent += 1
        except Exception as e:
            print(f"🎤 [{self.session_id}] Send error: {e}")

    async def stop(self):
        """
        Close WebSocket connection.
        Call this in on_audio_end.
        """
        if not self.ws:
            return

        self.is_running = False

        try:
            # Send close message to Deepgram
            await self.ws.send(json.dumps({"type": "CloseStream"}))
            print(f"🎤 [{self.session_id}] Sent {self.chunks_sent} chunks, closing...")

            # Wait for receiver to finish (with timeout)
            if self.receive_task:
                try:
                    await asyncio.wait_for(self.receive_task, timeout=2.0)
                except asyncio.TimeoutError:
                    self.receive_task.cancel()

            await self.ws.close()

        except Exception as e:
            print(f"🎤 [{self.session_id}] Close error: {e}")
        finally:
            self.ws = None
            self.receive_task = None

    async def _receive_loop(self):
        """Background task receiving transcripts from Deepgram."""
        try:
            async for msg in self.ws:
                if not self.is_running:
                    break

                data = json.loads(msg)
                msg_type = data.get("type")

                # Speech started
                if msg_type == "SpeechStarted":
                    print(f"🎤 [{self.session_id}] Speech detected")
                    if self.on_speech_start:
                        asyncio.create_task(self.on_speech_start())

                # Transcript results
                elif msg_type == "Results":
                    channel = data.get("channel", {})
                    alternatives = channel.get("alternatives", [])

                    if alternatives:
                        alt = alternatives[0]
                        text = alt.get("transcript", "")
                        is_final = data.get("is_final", False)

                        if text.strip():
                            if is_final:
                                # Accumulate final segments
                                self.current_transcript += " " + text
                                self.current_transcript = self.current_transcript.strip()

                            # Interim callback for live UI updates
                            if self.on_interim and not is_final:
                                asyncio.create_task(self.on_interim(text))

                # Utterance ended - USER STOPPED SPEAKING
                # This is the magic moment - trigger LLM immediately!
                elif msg_type == "UtteranceEnd":
                    print(f"🎤 [{self.session_id}] Utterance ended: '{self.current_transcript[:50]}...'")

                    if self.current_transcript.strip() and self.on_utterance_end:
                        # Fire callback immediately - this starts LLM + TTS
                        transcript = self.current_transcript.strip()
                        self.current_transcript = ""  # Reset for next utterance
                        asyncio.create_task(self.on_utterance_end(transcript))

        except websockets.exceptions.ConnectionClosed:
            print(f"🎤 [{self.session_id}] WebSocket closed")
        except Exception as e:
            print(f"🎤 [{self.session_id}] Receive error: {e}")


# === Session Management for Chainlit ===

_active_sessions: dict[str, LiveSTTSession] = {}


async def create_stt_session(
    user_session_id: str,
    on_utterance_end: Callable[[str], Awaitable[None]],
    on_interim: Callable[[str], Awaitable[None]] = None,
) -> Optional[LiveSTTSession]:
    """
    Create and start a new STT session.

    Args:
        user_session_id: Chainlit user session ID
        on_utterance_end: Called immediately when user stops speaking
        on_interim: Called with partial transcripts for live UI

    Returns:
        LiveSTTSession if started successfully, None otherwise
    """
    if not is_deepgram_enabled():
        return None

    session = LiveSTTSession(
        on_utterance_end=on_utterance_end,
        on_interim=on_interim,
    )

    if await session.start():
        _active_sessions[user_session_id] = session
        return session

    return None


def get_stt_session(user_session_id: str) -> Optional[LiveSTTSession]:
    """Get existing STT session."""
    return _active_sessions.get(user_session_id)


async def close_stt_session(user_session_id: str):
    """Close and remove STT session."""
    session = _active_sessions.pop(user_session_id, None)
    if session:
        await session.stop()


# === Legacy support (batch mode) ===

class RealtimeSTT:
    """
    Legacy batch-mode STT for fallback.
    Use LiveSTTSession for true real-time.
    """

    def __init__(self, model: str = MODEL_NOVA2):
        self.model = model
        self.api_key = DEEPGRAM_API_KEY

    @property
    def ws_url(self) -> str:
        params = [
            f"model={self.model}",
            "language=en",
            "smart_format=true",
            "punctuate=true",
            "encoding=linear16",
            "sample_rate=24000",
            "channels=1",
        ]
        return f"wss://api.deepgram.com/v1/listen?{'&'.join(params)}"

    async def transcribe_batch(self, audio_data: bytes) -> str:
        """Transcribe complete audio buffer (batch mode)."""
        if not self.api_key or not WEBSOCKETS_AVAILABLE:
            return ""

        headers = {"Authorization": f"Token {self.api_key}"}

        try:
            async with websockets.connect(self.ws_url, extra_headers=headers) as ws:
                await ws.send(audio_data)
                await ws.send(json.dumps({"type": "CloseStream"}))

                transcript = ""
                async for msg in ws:
                    data = json.loads(msg)
                    if data.get("type") == "Results":
                        channel = data.get("channel", {})
                        alts = channel.get("alternatives", [])
                        if alts and alts[0].get("transcript"):
                            transcript = alts[0]["transcript"]
                            if data.get("is_final"):
                                break

                return transcript

        except Exception as e:
            print(f"🎤 [STT] Batch transcribe error: {e}")
            return ""
