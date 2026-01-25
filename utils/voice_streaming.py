"""
Real-Time Voice Streaming for Chainlit
=======================================

Complete voice pipeline:
  User speaks → Gemini STT → LLM Stream → ElevenLabs WebSocket → Browser Audio Playback

Uses Chainlit's send_audio_chunk() for real-time browser playback (not downloadable files).

Key Components:
- GeminiSTT: Speech-to-text using Gemini's multimodal capabilities
- ElevenLabsStreamingTTS: WebSocket TTS with BOS/EOS protocol
- VoiceStreamingPipeline: Complete pipeline orchestration
"""

import os
import json
import asyncio
import base64
import uuid
from typing import AsyncGenerator, Optional, Callable, List
from dataclasses import dataclass

import chainlit as cl
from chainlit.types import InputAudioChunk, OutputAudioChunk

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️ websockets not installed - voice streaming disabled")

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "SGh5MKvZcSYNF0SZXlAg")  # Larry voice

# Models (latency vs quality tradeoff)
MODEL_TURBO = "eleven_turbo_v2_5"      # Fastest, ~100ms latency
MODEL_FLASH = "eleven_flash_v2_5"       # Fast, good quality
MODEL_MULTILINGUAL = "eleven_multilingual_v2"  # Best quality, higher latency

# Audio output format for browser playback
# mp3_44100_128 is widely supported
OUTPUT_FORMAT = "mp3_44100_128"


@dataclass
class VoiceConfig:
    """Configuration for voice streaming."""
    voice_id: str = ELEVENLABS_VOICE_ID
    model_id: str = MODEL_TURBO
    stability: float = 0.5
    similarity_boost: float = 0.8
    output_format: str = OUTPUT_FORMAT


def is_voice_enabled() -> bool:
    """Check if voice streaming is properly configured."""
    return bool(ELEVENLABS_API_KEY) and WEBSOCKETS_AVAILABLE


class RealtimeVoiceStreamer:
    """
    Real-time voice streaming to Chainlit browser.

    Streams audio chunks directly to browser for immediate playback,
    instead of collecting and sending as downloadable file.

    Usage:
        streamer = RealtimeVoiceStreamer()

        # Initialize audio session
        track_id = await streamer.start_session()

        # Stream text to voice
        async for _ in streamer.stream_text_to_browser(text_chunks, track_id):
            pass  # Audio is being played in browser

        # End session
        await streamer.end_session()
    """

    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig()
        self.api_key = ELEVENLABS_API_KEY

        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")
        if not WEBSOCKETS_AVAILABLE:
            raise ValueError("websockets library not installed")

    @property
    def ws_url(self) -> str:
        """WebSocket URL for TTS streaming input."""
        return (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self.config.voice_id}"
            f"/stream-input?model_id={self.config.model_id}"
            f"&output_format={self.config.output_format}"
        )

    async def start_session(self) -> str:
        """
        Initialize audio streaming session.

        Returns:
            track_id for this audio session
        """
        track_id = str(uuid.uuid4())
        cl.user_session.set("voice_track_id", track_id)
        cl.user_session.set("voice_enabled", True)
        print(f"🔊 [VOICE] Session started, track: {track_id[:8]}...")
        return track_id

    async def end_session(self):
        """Clean up audio session."""
        cl.user_session.set("voice_enabled", False)
        print("🔊 [VOICE] Session ended")

    async def stream_text_to_browser(
        self,
        text_chunks: AsyncGenerator[str, None],
        track_id: str,
        on_audio_sent: Callable[[int], None] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream text to ElevenLabs and forward audio chunks to browser.

        Args:
            text_chunks: Async generator yielding text strings from LLM
            track_id: Audio track ID for this session
            on_audio_sent: Optional callback when audio chunk is sent

        Yields:
            Audio bytes (also sent to browser via send_audio_chunk)
        """
        audio_queue = asyncio.Queue()
        done_event = asyncio.Event()
        chunks_sent = 0

        async with websockets.connect(self.ws_url) as ws:
            # === BOS: Beginning of Stream ===
            bos_message = {
                "text": " ",
                "voice_settings": {
                    "stability": self.config.stability,
                    "similarity_boost": self.config.similarity_boost,
                },
                "xi_api_key": self.api_key,
            }
            await ws.send(json.dumps(bos_message))
            print(f"🔊 [VOICE] WebSocket connected, voice: {self.config.voice_id}")

            # === Listener task: receive audio chunks ===
            async def listen_for_audio():
                nonlocal chunks_sent
                try:
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        # Audio chunk received
                        if audio_b64 := data.get("audio"):
                            audio_bytes = base64.b64decode(audio_b64)
                            await audio_queue.put(audio_bytes)

                            # Send directly to browser for playback
                            try:
                                await cl.context.emitter.send_audio_chunk(
                                    OutputAudioChunk(
                                        mimeType="audio/mpeg",
                                        data=audio_bytes,
                                        track=track_id
                                    )
                                )
                                chunks_sent += 1
                                if on_audio_sent:
                                    on_audio_sent(chunks_sent)
                            except Exception as e:
                                print(f"🔊 [VOICE] Browser send error: {e}")

                        # End of stream
                        if data.get("isFinal"):
                            print(f"🔊 [VOICE] Stream complete, sent {chunks_sent} chunks to browser")
                            break

                except websockets.exceptions.ConnectionClosed:
                    print("🔊 [VOICE] WebSocket closed")
                finally:
                    done_event.set()

            # Start listener
            listen_task = asyncio.create_task(listen_for_audio())

            # === Send text chunks ===
            chunk_count = 0
            try:
                async for text in text_chunks:
                    if text.strip():
                        await ws.send(json.dumps({
                            "text": text,
                            "try_trigger_generation": True,
                        }))
                        chunk_count += 1

                # === EOS: End of Stream ===
                await ws.send(json.dumps({"text": ""}))
                print(f"🔊 [VOICE] Sent {chunk_count} text chunks, waiting for audio...")

            except Exception as e:
                print(f"🔊 [VOICE] Send error: {e}")
                listen_task.cancel()
                raise

            # === Yield audio chunks as they arrive ===
            while not done_event.is_set() or not audio_queue.empty():
                try:
                    audio = await asyncio.wait_for(audio_queue.get(), timeout=0.1)
                    yield audio
                except asyncio.TimeoutError:
                    continue

            await listen_task


def text_chunker_for_tts(text: str, min_length: int = 10) -> List[str]:
    """
    Split text into speakable chunks at natural boundaries.
    Optimized for TTS prosody.
    """
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    chunks = []
    buffer = ""

    for char in text:
        buffer += char
        if char in splitters and len(buffer) >= min_length:
            chunks.append(buffer)
            buffer = ""

    if buffer:
        chunks.append(buffer)

    return chunks


async def stream_gemini_with_voice(
    client,
    contents: list,
    system_prompt: str,
    msg: cl.Message,
    track_id: str,
    voice_config: VoiceConfig = None,
) -> str:
    """
    Stream Gemini response with real-time voice playback.

    This is the main function to use in on_audio_end handler.

    Args:
        client: Gemini client
        contents: Conversation contents for Gemini
        system_prompt: System instruction
        msg: Chainlit message to stream text to
        track_id: Audio track ID for browser playback
        voice_config: Optional voice configuration

    Returns:
        Full response text
    """
    from google.genai import types

    config = voice_config or VoiceConfig()
    full_text = ""

    # Buffer for natural sentence chunking
    text_buffer = ""
    sentence_endings = {'.', '!', '?', '\n', ';', ':'}

    # Create streamer
    streamer = RealtimeVoiceStreamer(config)

    # Start Gemini stream
    response_stream = client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
    )

    async def gemini_text_chunks():
        """Generator that yields complete sentences from Gemini stream."""
        nonlocal full_text, text_buffer

        for chunk in response_stream:
            if chunk.text:
                full_text += chunk.text
                text_buffer += chunk.text

                # Stream to UI immediately
                await msg.stream_token(chunk.text)

                # Send complete sentences to TTS for better prosody
                if any(end in text_buffer for end in sentence_endings) and len(text_buffer) > 15:
                    yield text_buffer
                    text_buffer = ""

        # Send remaining text
        if text_buffer.strip():
            yield text_buffer

    # Stream to browser
    try:
        async for _ in streamer.stream_text_to_browser(gemini_text_chunks(), track_id):
            pass  # Audio is being sent to browser in real-time
    except Exception as e:
        print(f"🔊 [VOICE] Streaming error: {e}")

    await msg.update()
    return full_text


async def process_voice_input_with_response(
    client,
    audio_data: bytes,
    mime_type: str,
    bot: dict,
    history: list,
    phases: list = None,
    current_phase: int = 0,
) -> tuple[str, str]:
    """
    Complete voice input → transcription → LLM → voice response pipeline.

    Args:
        client: Gemini client
        audio_data: Raw audio bytes from user
        mime_type: Audio MIME type
        bot: Bot configuration dict
        history: Conversation history
        phases: Optional workshop phases
        current_phase: Current phase index

    Returns:
        tuple: (transcription, response_text)
    """
    from google.genai import types

    # === 1. Transcribe with Gemini ===
    print("🎤 [VOICE] Transcribing with Gemini...")

    transcription_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=audio_data, mime_type=mime_type),
                    types.Part(text="Transcribe this audio exactly. Only output the transcription, nothing else.")
                ]
            )
        ]
    )
    transcription = transcription_response.text.strip()
    print(f"🎤 [VOICE] Transcribed: '{transcription[:50]}...'")

    if not transcription:
        return "", ""

    # === 2. Show what user said ===
    await cl.Message(content=f"**You said:** {transcription}").send()

    # === 3. Build context ===
    contents = []
    for msg_item in history:
        contents.append(types.Content(
            role=msg_item["role"],
            parts=[types.Part(text=msg_item["content"])]
        ))

    phase_context = ""
    if phases and current_phase < len(phases):
        phase_context = f"\n\n[CURRENT WORKSHOP PHASE: {phases[current_phase]['name']}]"

    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=transcription + phase_context)]
    ))

    # === 4. Stream response with voice ===
    msg = cl.Message(content="")
    await msg.send()

    if is_voice_enabled():
        # Real-time voice streaming
        track_id = cl.user_session.get("voice_track_id")
        if not track_id:
            streamer = RealtimeVoiceStreamer()
            track_id = await streamer.start_session()

        response_text = await stream_gemini_with_voice(
            client=client,
            contents=contents,
            system_prompt=bot["system_prompt"],
            msg=msg,
            track_id=track_id,
        )
    else:
        # Fallback: text only
        print("🔊 [VOICE] Voice not enabled, text-only response")
        response_text = ""

        response_stream = client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=bot["system_prompt"],
            )
        )

        for chunk in response_stream:
            if chunk.text:
                response_text += chunk.text
                await msg.stream_token(chunk.text)

        await msg.update()

    return transcription, response_text


# === Chainlit Audio Handler Templates ===

def get_audio_handlers_code() -> str:
    """
    Returns template code for audio handlers.
    Copy this to mindrian_chat.py to replace existing handlers.
    """
    return '''
@cl.on_audio_start
async def on_audio_start():
    """Initialize real-time voice streaming session."""
    import uuid

    print("🎤 [VOICE] Audio recording started")

    # Initialize audio collection
    cl.user_session.set("audio_chunks", [])
    cl.user_session.set("audio_mime_type", "audio/webm")

    # Initialize real-time voice output
    track_id = str(uuid.uuid4())
    cl.user_session.set("voice_track_id", track_id)
    cl.user_session.set("voice_enabled", True)

    print(f"🎤 [VOICE] Track ID: {track_id[:8]}...")
    return True  # Accept audio stream


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """Collect incoming audio chunks."""
    audio_chunks = cl.user_session.get("audio_chunks", [])
    audio_chunks.append(chunk.data)
    cl.user_session.set("audio_chunks", audio_chunks)

    if len(audio_chunks) == 1:
        print(f"🎤 [VOICE] First chunk: {len(chunk.data)} bytes, mime: {chunk.mimeType}")

    if chunk.mimeType:
        cl.user_session.set("audio_mime_type", chunk.mimeType)


@cl.on_audio_end
async def on_audio_end(elements: list = None):
    """Process audio and respond with real-time voice streaming."""
    from utils.voice_streaming import (
        process_voice_input_with_response,
        is_voice_enabled,
    )

    audio_chunks = cl.user_session.get("audio_chunks", [])
    if not audio_chunks:
        await cl.Message(content="⚠️ No audio detected.").send()
        return

    audio_data = b"".join(audio_chunks)
    print(f"🎤 [VOICE] Recording complete: {len(audio_chunks)} chunks, {len(audio_data)} bytes")
    cl.user_session.set("audio_chunks", [])

    if len(audio_data) < 1000:
        await cl.Message(content="⚠️ Recording too short.").send()
        return

    mime_type = cl.user_session.get("audio_mime_type", "audio/webm")
    bot = cl.user_session.get("bot", BOTS["larry"])
    history = cl.user_session.get("history", [])
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)

    try:
        transcription, response_text = await process_voice_input_with_response(
            client=client,
            audio_data=audio_data,
            mime_type=mime_type,
            bot=bot,
            history=history,
            phases=phases,
            current_phase=current_phase,
        )

        if transcription and response_text:
            # Update history
            history.append({"role": "user", "content": transcription})
            history.append({"role": "model", "content": response_text})
            cl.user_session.set("history", history)

    except Exception as e:
        print(f"🎤 [VOICE] Error: {e}")
        await cl.Message(content=f"Voice processing error: {str(e)[:100]}").send()
'''
