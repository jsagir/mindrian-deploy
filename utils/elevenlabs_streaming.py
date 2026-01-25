"""
ElevenLabs Real-Time TTS Streaming
==================================

Uses WebSocket for real-time text-to-speech streaming.
Text chunks from LLM are converted to audio in real-time.

Two modes:
1. TTS Input Streaming: Stream text chunks → Get audio chunks
2. Conversational AI: Full voice conversation (ElevenLabs handles LLM)
"""

import os
import json
import asyncio
import base64
from typing import AsyncGenerator, Optional, Callable
import aiohttp

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "SGh5MKvZcSYNF0SZXlAg")  # Larry voice
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")  # For Conversational AI mode

# Models
MODEL_TURBO = "eleven_turbo_v2_5"  # Fastest, ~100ms latency
MODEL_FLASH = "eleven_flash_v2_5"   # Fast, good quality
MODEL_MULTILINGUAL = "eleven_multilingual_v2"  # Best quality, higher latency


class ElevenLabsStreamingTTS:
    """
    Real-time TTS using ElevenLabs WebSocket API.

    Usage:
        tts = ElevenLabsStreamingTTS()

        # Stream text chunks and get audio chunks
        async for audio_chunk in tts.stream_text_to_speech(text_generator()):
            await play_audio(audio_chunk)
    """

    def __init__(
        self,
        api_key: str = None,
        voice_id: str = None,
        model_id: str = MODEL_TURBO,
    ):
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.voice_id = voice_id or ELEVENLABS_VOICE_ID
        self.model_id = model_id

        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")

    @property
    def ws_url(self) -> str:
        """WebSocket URL for TTS streaming."""
        return (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            f"/stream-input?model_id={self.model_id}"
            f"&output_format=mp3_44100_128"
        )

    async def stream_text_to_speech(
        self,
        text_chunks: AsyncGenerator[str, None],
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream text chunks to ElevenLabs and yield audio chunks.

        Args:
            text_chunks: Async generator yielding text strings
            stability: Voice stability (0-1)
            similarity_boost: Voice clarity (0-1)

        Yields:
            Audio bytes (MP3 chunks)
        """
        headers = {
            "xi-api-key": self.api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.ws_url, headers=headers) as ws:
                # Send initial configuration
                init_message = {
                    "text": " ",  # Initial space to start
                    "voice_settings": {
                        "stability": stability,
                        "similarity_boost": similarity_boost,
                    },
                    "generation_config": {
                        "chunk_length_schedule": [120, 160, 250, 290]
                    }
                }
                await ws.send_json(init_message)

                # Task to send text chunks
                async def send_chunks():
                    async for chunk in text_chunks:
                        if chunk.strip():
                            await ws.send_json({"text": chunk})
                    # Signal end of text
                    await ws.send_json({"text": ""})

                # Start sending in background
                send_task = asyncio.create_task(send_chunks())

                # Receive audio chunks
                try:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)

                            if data.get("audio"):
                                # Decode base64 audio
                                audio_bytes = base64.b64decode(data["audio"])
                                yield audio_bytes

                            if data.get("isFinal"):
                                break

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"WebSocket error: {ws.exception()}")
                            break
                finally:
                    send_task.cancel()

    async def text_to_speech_streaming(
        self,
        text: str,
    ) -> AsyncGenerator[bytes, None]:
        """
        Convert a single text string to streaming audio.

        Args:
            text: Full text to convert

        Yields:
            Audio bytes (MP3 chunks)
        """
        async def single_chunk():
            yield text

        async for audio in self.stream_text_to_speech(single_chunk()):
            yield audio


class ElevenLabsConversationalAI:
    """
    ElevenLabs Conversational AI WebSocket.

    For full voice conversations where ElevenLabs handles:
    - Speech-to-text
    - LLM response (can use custom LLM via function calling)
    - Text-to-speech

    Requires an ElevenLabs Agent to be configured in the dashboard.
    """

    def __init__(
        self,
        api_key: str = None,
        agent_id: str = None,
    ):
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.agent_id = agent_id or ELEVENLABS_AGENT_ID

        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")
        if not self.agent_id:
            raise ValueError("ELEVENLABS_AGENT_ID not configured for Conversational AI")

    @property
    def ws_url(self) -> str:
        """WebSocket URL for Conversational AI."""
        return f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={self.agent_id}"

    async def start_conversation(
        self,
        on_transcript: Callable[[str], None] = None,
        on_response_text: Callable[[str], None] = None,
        on_response_audio: Callable[[bytes], None] = None,
    ):
        """
        Start a voice conversation with the ElevenLabs agent.

        Args:
            on_transcript: Callback when user speech is transcribed
            on_response_text: Callback when agent responds with text
            on_response_audio: Callback when agent responds with audio
        """
        headers = {
            "xi-api-key": self.api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.ws_url, headers=headers) as ws:
                print(f"Connected to ElevenLabs Conversational AI (Agent: {self.agent_id})")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        msg_type = data.get("type")

                        if msg_type == "user_transcript" and on_transcript:
                            on_transcript(data.get("text", ""))

                        elif msg_type == "agent_response":
                            if on_response_text:
                                on_response_text(data.get("text", ""))

                        elif msg_type == "agent_response_correction":
                            # Final corrected response
                            if on_response_text:
                                on_response_text(data.get("text", ""))

                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        # Audio data
                        if on_response_audio:
                            on_response_audio(msg.data)

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"Conversational AI error: {ws.exception()}")
                        break

    async def send_user_input(self, ws, text: str):
        """Send text input to the agent."""
        await ws.send_json({
            "type": "user_input",
            "text": text,
        })

    async def send_audio_input(self, ws, audio_bytes: bytes):
        """Send audio input to the agent."""
        await ws.send_bytes(audio_bytes)


# === Integration Helpers ===

async def stream_llm_to_speech(
    llm_stream: AsyncGenerator[str, None],
    voice_id: str = None,
    model_id: str = MODEL_TURBO,
) -> AsyncGenerator[bytes, None]:
    """
    Helper: Stream LLM text output directly to ElevenLabs TTS.

    Usage with Gemini:
        async def gemini_stream():
            response = client.models.generate_content_stream(...)
            for chunk in response:
                if chunk.text:
                    yield chunk.text

        async for audio in stream_llm_to_speech(gemini_stream()):
            # Send audio chunk to client
    """
    tts = ElevenLabsStreamingTTS(voice_id=voice_id, model_id=model_id)
    async for audio in tts.stream_text_to_speech(llm_stream):
        yield audio


async def collect_streaming_audio(audio_stream: AsyncGenerator[bytes, None]) -> bytes:
    """Collect all audio chunks into a single bytes object."""
    chunks = []
    async for chunk in audio_stream:
        chunks.append(chunk)
    return b"".join(chunks)


# === Chainlit Integration ===

async def create_streaming_audio_message(
    text_stream: AsyncGenerator[str, None],
    voice_id: str = None,
) -> tuple[str, bytes]:
    """
    Create a message with streaming audio from text stream.

    Returns:
        tuple: (full_text, audio_bytes)
    """
    full_text = ""

    async def capture_text():
        nonlocal full_text
        async for chunk in text_stream:
            full_text += chunk
            yield chunk

    audio_bytes = await collect_streaming_audio(
        stream_llm_to_speech(capture_text(), voice_id)
    )

    return full_text, audio_bytes
