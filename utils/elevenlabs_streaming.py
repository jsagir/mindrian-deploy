"""
ElevenLabs Real-Time TTS Streaming
==================================

Streams Gemini text output → ElevenLabs WebSocket → Audio chunks in real-time.

Flow:
  User input → Gemini streaming → chunk text → ElevenLabs WebSocket → audio chunks → play

Based on ElevenLabs official streaming pattern:
https://elevenlabs.io/docs/api-reference/text-to-speech-websockets
"""

import os
import json
import asyncio
import base64
from typing import AsyncGenerator, Optional, Callable, List
import websockets

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "SGh5MKvZcSYNF0SZXlAg")  # Larry voice

# Models (latency vs quality tradeoff)
MODEL_TURBO = "eleven_turbo_v2_5"      # Fastest, ~100ms latency
MODEL_FLASH = "eleven_flash_v2_5"       # Fast, good quality
MODEL_MULTILINGUAL = "eleven_multilingual_v2"  # Best quality, higher latency


def text_chunker(text: str) -> List[str]:
    """
    Split text into speakable chunks at natural boundaries.
    Avoids cutting words mid-phoneme for better prosody.

    Based on ElevenLabs reference chunker.
    """
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    chunks = []
    buffer = ""

    for char in text:
        buffer += char
        if char in splitters and len(buffer) >= 10:
            chunks.append(buffer)
            buffer = ""

    if buffer:
        chunks.append(buffer)

    return chunks


class ElevenLabsStreamingTTS:
    """
    Real-time TTS using ElevenLabs WebSocket API.

    Chains Gemini text streaming → ElevenLabs audio streaming.

    Usage:
        tts = ElevenLabsStreamingTTS()

        async for audio_chunk in tts.stream_text_to_speech(gemini_text_generator):
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
        """WebSocket URL for TTS streaming input."""
        return (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            f"/stream-input?model_id={self.model_id}"
        )

    async def stream_text_to_speech(
        self,
        text_chunks: AsyncGenerator[str, None],
        stability: float = 0.5,
        similarity_boost: float = 0.8,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream text chunks to ElevenLabs and yield audio chunks.

        Args:
            text_chunks: Async generator yielding text strings from LLM
            stability: Voice stability (0-1, lower = more expressive)
            similarity_boost: Voice clarity (0-1, higher = clearer)

        Yields:
            Audio bytes (MP3 chunks) - play immediately for real-time audio
        """
        audio_queue = asyncio.Queue()
        done_event = asyncio.Event()

        async with websockets.connect(self.ws_url) as ws:
            # === BOS: Beginning of Stream ===
            # Send initial config with API key and voice settings
            bos_message = {
                "text": " ",  # Space to initialize
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                },
                "xi_api_key": self.api_key,
            }
            await ws.send(json.dumps(bos_message))
            print(f"🔊 [TTS] WebSocket connected, voice: {self.voice_id}")

            # === Listener task: receive audio chunks ===
            async def listen_for_audio():
                try:
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        # Audio chunk received
                        if audio_b64 := data.get("audio"):
                            audio_bytes = base64.b64decode(audio_b64)
                            await audio_queue.put(audio_bytes)

                        # End of stream
                        if data.get("isFinal"):
                            print("🔊 [TTS] Stream complete (isFinal)")
                            break

                except websockets.exceptions.ConnectionClosed:
                    print("🔊 [TTS] WebSocket closed")
                finally:
                    done_event.set()

            # Start listener
            listen_task = asyncio.create_task(listen_for_audio())

            # === Send text chunks ===
            chunk_count = 0
            try:
                async for text in text_chunks:
                    if text.strip():
                        # Send each chunk with trigger flag
                        await ws.send(json.dumps({
                            "text": text,
                            "try_trigger_generation": True,
                        }))
                        chunk_count += 1

                # === EOS: End of Stream ===
                await ws.send(json.dumps({"text": ""}))
                print(f"🔊 [TTS] Sent {chunk_count} text chunks, waiting for audio...")

            except Exception as e:
                print(f"🔊 [TTS] Send error: {e}")
                listen_task.cancel()
                raise

            # === Yield audio chunks as they arrive ===
            while not done_event.is_set() or not audio_queue.empty():
                try:
                    audio = await asyncio.wait_for(audio_queue.get(), timeout=0.1)
                    yield audio
                except asyncio.TimeoutError:
                    continue

            # Cleanup
            await listen_task

    async def text_to_speech_streaming(
        self,
        text: str,
    ) -> AsyncGenerator[bytes, None]:
        """
        Convert a single text string to streaming audio.
        Chunks the text for optimal prosody.

        Args:
            text: Full text to convert

        Yields:
            Audio bytes (MP3 chunks)
        """
        chunks = text_chunker(text)

        async def chunk_generator():
            for chunk in chunks:
                yield chunk

        async for audio in self.stream_text_to_speech(chunk_generator()):
            yield audio


async def stream_gemini_to_elevenlabs(
    gemini_stream,
    voice_id: str = None,
    model_id: str = MODEL_TURBO,
    on_text_chunk: Callable[[str], None] = None,
) -> AsyncGenerator[bytes, None]:
    """
    Stream Gemini text output directly to ElevenLabs TTS.

    Args:
        gemini_stream: Gemini generate_content_stream response
        voice_id: ElevenLabs voice ID
        model_id: ElevenLabs model (eleven_turbo_v2_5 for lowest latency)
        on_text_chunk: Optional callback for each text chunk (for UI streaming)

    Yields:
        Audio bytes (MP3 chunks)

    Usage:
        response_stream = client.models.generate_content_stream(...)

        async for audio in stream_gemini_to_elevenlabs(response_stream, on_text_chunk=msg.stream_token):
            # audio is ready to play
    """
    tts = ElevenLabsStreamingTTS(voice_id=voice_id, model_id=model_id)

    # Buffer for natural chunking
    text_buffer = ""
    sentence_endings = {'.', '!', '?', '\n', ';', ':'}

    async def gemini_text_chunks():
        nonlocal text_buffer

        for chunk in gemini_stream:
            if chunk.text:
                text_buffer += chunk.text

                # Callback for UI text streaming
                if on_text_chunk:
                    on_text_chunk(chunk.text)

                # Send complete sentences to TTS for better prosody
                if any(end in text_buffer for end in sentence_endings) and len(text_buffer) > 15:
                    yield text_buffer
                    text_buffer = ""

        # Send remaining text
        if text_buffer.strip():
            yield text_buffer

    async for audio in tts.stream_text_to_speech(gemini_text_chunks()):
        yield audio


async def collect_streaming_audio(audio_stream: AsyncGenerator[bytes, None]) -> bytes:
    """Collect all audio chunks into a single bytes object."""
    chunks = []
    async for chunk in audio_stream:
        chunks.append(chunk)
    return b"".join(chunks)


# === Chainlit Integration Helper ===

async def generate_streaming_voice_response(
    client,
    contents,
    system_prompt: str,
    voice_id: str = None,
    on_text: Callable = None,
) -> tuple[str, bytes]:
    """
    Generate LLM response with streaming voice.

    Args:
        client: Gemini client
        contents: Conversation contents
        system_prompt: System instruction
        voice_id: ElevenLabs voice
        on_text: Callback for text streaming (e.g., msg.stream_token)

    Returns:
        tuple: (full_text, audio_bytes)
    """
    from google.genai import types

    full_text = ""

    response_stream = client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
    )

    audio_chunks = []

    async for audio in stream_gemini_to_elevenlabs(
        response_stream,
        voice_id=voice_id,
        on_text_chunk=lambda t: (full_text := full_text + t, on_text(t) if on_text else None)[0]
    ):
        audio_chunks.append(audio)

    return full_text, b"".join(audio_chunks)
