"""
Real-Time Speech-to-Text with Deepgram
======================================

Streams audio from user's microphone to Deepgram for live transcription.
Transcription appears in real-time as user speaks.

Flow:
  User speaks → Audio chunks → Deepgram WebSocket → Live transcription → Gemini → ElevenLabs

Requirements:
  - DEEPGRAM_API_KEY environment variable
  - pip install deepgram-sdk

Usage:
  streamer = RealtimeSTT()

  async for transcript in streamer.transcribe_stream(audio_chunks):
      # transcript.text = current transcription
      # transcript.is_final = True when utterance complete
      if transcript.is_final:
          response = await get_llm_response(transcript.text)
"""

import os
import asyncio
import json
from typing import AsyncGenerator, Optional, Callable
from dataclasses import dataclass

import chainlit as cl

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
    words: list = None

    def __post_init__(self):
        if self.words is None:
            self.words = []


def is_deepgram_enabled() -> bool:
    """Check if Deepgram is configured."""
    return bool(DEEPGRAM_API_KEY)


class RealtimeSTT:
    """
    Real-time Speech-to-Text using Deepgram's streaming API.

    Features:
    - Live transcription as user speaks
    - Interim results (partial transcriptions)
    - Final results (complete utterances)
    - Automatic punctuation
    - Smart formatting

    Usage:
        stt = RealtimeSTT()

        async for result in stt.transcribe_stream(audio_generator):
            if result.is_final:
                # Complete utterance - send to LLM
                await process_utterance(result.text)
            else:
                # Partial - update UI
                await update_live_transcript(result.text)
    """

    def __init__(
        self,
        model: str = MODEL_NOVA2,
        language: str = "en",
        smart_format: bool = True,
        punctuate: bool = True,
        interim_results: bool = True,
        utterance_end_ms: int = 1000,  # Silence duration to end utterance
        vad_events: bool = True,
    ):
        if not DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not configured")

        self.api_key = DEEPGRAM_API_KEY
        self.model = model
        self.language = language
        self.smart_format = smart_format
        self.punctuate = punctuate
        self.interim_results = interim_results
        self.utterance_end_ms = utterance_end_ms
        self.vad_events = vad_events

    @property
    def ws_url(self) -> str:
        """WebSocket URL for Deepgram streaming."""
        params = [
            f"model={self.model}",
            f"language={self.language}",
            f"smart_format={str(self.smart_format).lower()}",
            f"punctuate={str(self.punctuate).lower()}",
            f"interim_results={str(self.interim_results).lower()}",
            f"utterance_end_ms={self.utterance_end_ms}",
            f"vad_events={str(self.vad_events).lower()}",
            "encoding=linear16",
            "sample_rate=24000",
            "channels=1",
        ]
        return f"wss://api.deepgram.com/v1/listen?{'&'.join(params)}"

    async def transcribe_stream(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
        on_interim: Callable[[str], None] = None,
    ) -> AsyncGenerator[TranscriptResult, None]:
        """
        Stream audio to Deepgram and yield transcription results.

        Args:
            audio_chunks: Async generator yielding audio bytes (PCM16, 24kHz)
            on_interim: Optional callback for interim results (for UI updates)

        Yields:
            TranscriptResult with text, is_final flag, and confidence
        """
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required: pip install websockets")

        headers = {
            "Authorization": f"Token {self.api_key}",
        }

        transcript_queue = asyncio.Queue()
        done_event = asyncio.Event()

        async with websockets.connect(self.ws_url, extra_headers=headers) as ws:
            print(f"🎤 [STT] Connected to Deepgram ({self.model})")

            # === Receiver task: get transcriptions ===
            async def receive_transcripts():
                try:
                    async for msg in ws:
                        data = json.loads(msg)

                        # Handle transcript results
                        if data.get("type") == "Results":
                            channel = data.get("channel", {})
                            alternatives = channel.get("alternatives", [])

                            if alternatives:
                                alt = alternatives[0]
                                text = alt.get("transcript", "")
                                confidence = alt.get("confidence", 0.0)
                                words = alt.get("words", [])
                                is_final = data.get("is_final", False)

                                if text.strip():
                                    result = TranscriptResult(
                                        text=text,
                                        is_final=is_final,
                                        confidence=confidence,
                                        words=words,
                                    )
                                    await transcript_queue.put(result)

                                    # Callback for interim results
                                    if on_interim and not is_final:
                                        on_interim(text)

                        # Handle utterance end (speech finished)
                        elif data.get("type") == "UtteranceEnd":
                            print("🎤 [STT] Utterance ended")

                        # Handle speech started
                        elif data.get("type") == "SpeechStarted":
                            print("🎤 [STT] Speech detected")

                except websockets.exceptions.ConnectionClosed:
                    print("🎤 [STT] WebSocket closed")
                finally:
                    done_event.set()

            # Start receiver
            receive_task = asyncio.create_task(receive_transcripts())

            # === Sender task: stream audio ===
            try:
                chunk_count = 0
                async for audio_data in audio_chunks:
                    if audio_data:
                        await ws.send(audio_data)
                        chunk_count += 1

                # Send close message
                await ws.send(json.dumps({"type": "CloseStream"}))
                print(f"🎤 [STT] Sent {chunk_count} audio chunks")

            except Exception as e:
                print(f"🎤 [STT] Send error: {e}")
                receive_task.cancel()
                raise

            # === Yield transcripts as they arrive ===
            while not done_event.is_set() or not transcript_queue.empty():
                try:
                    result = await asyncio.wait_for(transcript_queue.get(), timeout=0.1)
                    yield result
                except asyncio.TimeoutError:
                    continue

            await receive_task


class LiveConversation:
    """
    Complete live conversation handler.

    Combines:
    - Deepgram real-time STT
    - Gemini LLM
    - ElevenLabs real-time TTS

    Usage in Chainlit:
        conversation = LiveConversation()

        @cl.on_audio_chunk
        async def on_audio_chunk(chunk):
            await conversation.process_audio_chunk(chunk.data)
    """

    def __init__(self):
        self.stt = RealtimeSTT() if is_deepgram_enabled() else None
        self.audio_buffer = []
        self.current_transcript = ""
        self.is_speaking = False

    async def start_listening(self):
        """Initialize listening session."""
        self.audio_buffer = []
        self.current_transcript = ""
        self.is_speaking = False

        # Create live transcript message
        self.transcript_msg = cl.Message(content="🎤 *Listening...*")
        await self.transcript_msg.send()

        return True

    async def process_audio_chunk(self, audio_data: bytes):
        """Process incoming audio chunk."""
        self.audio_buffer.append(audio_data)

    async def finish_listening(self) -> Optional[str]:
        """
        Finish listening and return final transcript.

        Returns:
            Final transcription text, or None if no speech detected
        """
        if not self.audio_buffer:
            return None

        if not self.stt:
            # Fallback to batch transcription
            print("🎤 [STT] Deepgram not configured, using fallback")
            return None

        # Create async generator from buffer
        async def audio_generator():
            for chunk in self.audio_buffer:
                yield chunk

        # Stream to Deepgram and collect final transcript
        final_text = ""

        async for result in self.stt.transcribe_stream(
            audio_generator(),
            on_interim=lambda t: asyncio.create_task(self._update_transcript(t))
        ):
            if result.is_final:
                final_text = result.text
                break

        # Update message with final transcript
        if final_text:
            await self.transcript_msg.update()
            self.transcript_msg.content = f"**You said:** {final_text}"
            await self.transcript_msg.update()

        self.audio_buffer = []
        return final_text

    async def _update_transcript(self, text: str):
        """Update live transcript in UI."""
        self.current_transcript = text
        self.transcript_msg.content = f"🎤 *{text}*"
        await self.transcript_msg.update()


# === Chainlit Integration Helpers ===

async def create_live_stt_session() -> dict:
    """Create a new live STT session for Chainlit."""
    if not is_deepgram_enabled():
        return {"enabled": False, "reason": "DEEPGRAM_API_KEY not set"}

    session_id = str(id(asyncio.current_task()))

    return {
        "enabled": True,
        "session_id": session_id,
        "stt": RealtimeSTT(),
        "buffer": [],
    }


def get_audio_handler_code() -> str:
    """
    Returns template code for real-time audio handlers.
    Copy this to mindrian_chat.py.
    """
    return '''
# === REAL-TIME VOICE HANDLERS ===

@cl.on_audio_start
async def on_audio_start():
    """Initialize real-time STT session."""
    import uuid
    from utils.realtime_stt import is_deepgram_enabled, RealtimeSTT

    print("🎤 [VOICE] Audio started")

    # Initialize buffers
    cl.user_session.set("audio_chunks", [])
    cl.user_session.set("audio_mime_type", "audio/pcm")

    # Initialize voice output track
    track_id = str(uuid.uuid4())
    cl.user_session.set("voice_track_id", track_id)

    # Check if real-time STT is available
    if is_deepgram_enabled():
        cl.user_session.set("realtime_stt", True)
        # Show live transcript placeholder
        transcript_msg = cl.Message(content="🎤 *Listening...*")
        await transcript_msg.send()
        cl.user_session.set("transcript_msg", transcript_msg)
    else:
        cl.user_session.set("realtime_stt", False)

    return True


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """Stream audio to Deepgram for live transcription."""
    audio_chunks = cl.user_session.get("audio_chunks", [])
    audio_chunks.append(chunk.data)
    cl.user_session.set("audio_chunks", audio_chunks)

    # TODO: For true real-time, stream each chunk to Deepgram here
    # Currently batching for simplicity


@cl.on_audio_end
async def on_audio_end(elements: list = None):
    """Process complete audio with streaming STT."""
    from utils.realtime_stt import is_deepgram_enabled, RealtimeSTT

    audio_chunks = cl.user_session.get("audio_chunks", [])
    if not audio_chunks:
        await cl.Message(content="⚠️ No audio detected.").send()
        return

    audio_data = b"".join(audio_chunks)
    cl.user_session.set("audio_chunks", [])

    # Use Deepgram for transcription if available
    if is_deepgram_enabled():
        stt = RealtimeSTT()

        async def audio_gen():
            yield audio_data

        transcript = ""
        async for result in stt.transcribe_stream(audio_gen()):
            if result.is_final:
                transcript = result.text
                break

        if transcript:
            # Process with LLM...
            pass
    else:
        # Fallback to Gemini batch transcription
        pass
'''
