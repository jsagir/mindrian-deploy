"""
Mindrian Real-Time Voice WebSocket Server
==========================================

Handles browser ↔ server real-time voice streaming:
- Receives audio from browser microphone
- Transcribes with Google Cloud STT
- Processes with Gemini (uses Mindrian agents)
- Converts to speech with ElevenLabs (your custom voice)
- Streams audio back to browser

Runs alongside Chainlit on a separate port.
"""

import os
import json
import asyncio
import base64
import time
import uuid
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Dependencies
# =============================================================================

try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    from google.cloud import speech_v1 as speech
    GOOGLE_STT_AVAILABLE = True
except ImportError:
    GOOGLE_STT_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from elevenlabs import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# =============================================================================
# Import Mindrian Prompts
# =============================================================================

try:
    from prompts import (
        LARRY_RAG_SYSTEM_PROMPT,
        TTA_SYSTEM_PROMPT,
        JTBD_SYSTEM_PROMPT,
        SCURVE_SYSTEM_PROMPT,
        REDTEAM_SYSTEM_PROMPT,
        ACKOFF_SYSTEM_PROMPT,
    )
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False
    LARRY_RAG_SYSTEM_PROMPT = "You are Larry, a PWS methodology expert."

# =============================================================================
# Voice-Optimized Prompts
# =============================================================================

VOICE_ADDON = """

## Real-Time Voice Mode
You are in REAL-TIME VOICE conversation. Critical rules:

1. **BREVITY**: 2-3 sentences MAX per response
2. **NATURAL**: Use conversational language, contractions, "So...", "Well...", "Hmm..."
3. **ONE QUESTION**: Ask only ONE question per turn
4. **NO FORMATTING**: No bullets, no markdown - natural speech only
5. **THINKING ALOUD**: Say "Let me think..." when processing
6. **WARMTH**: Be encouraging, friendly, like talking to a colleague
"""

VOICE_AGENTS = {
    "larry": {
        "name": "Lawrence",
        "prompt": (LARRY_RAG_SYSTEM_PROMPT if PROMPTS_AVAILABLE else "You are Larry.") + VOICE_ADDON,
    },
    "tta": {
        "name": "TTA Expert",
        "prompt": (TTA_SYSTEM_PROMPT if PROMPTS_AVAILABLE else "You are a TTA expert.") + VOICE_ADDON,
    },
    "jtbd": {
        "name": "JTBD Expert",
        "prompt": (JTBD_SYSTEM_PROMPT if PROMPTS_AVAILABLE else "You are a JTBD expert.") + VOICE_ADDON,
    },
    "redteam": {
        "name": "Red Team",
        "prompt": (REDTEAM_SYSTEM_PROMPT if PROMPTS_AVAILABLE else "You are Red Team.") + VOICE_ADDON,
    },
}

# =============================================================================
# Session Management
# =============================================================================

@dataclass
class VoiceSession:
    """Represents an active voice conversation session."""
    session_id: str
    agent_id: str = "larry"
    history: List[Dict] = field(default_factory=list)
    is_speaking: bool = False
    should_interrupt: bool = False
    created_at: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

# Active sessions
sessions: Dict[str, VoiceSession] = {}

# =============================================================================
# Voice Processing Pipeline
# =============================================================================

class VoicePipeline:
    """
    Handles the full voice processing pipeline:
    Browser Audio → Google STT → Gemini → ElevenLabs → Browser Audio
    """

    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        # Initialize clients
        self.gemini_client = None
        self.elevenlabs_client = None
        self.speech_client = None

        self._init_clients()

    def _init_clients(self):
        """Initialize API clients."""
        if GEMINI_AVAILABLE and self.google_api_key:
            self.gemini_client = genai.Client(api_key=self.google_api_key)
            print("✅ Gemini client ready")

        if ELEVENLABS_AVAILABLE and self.elevenlabs_api_key:
            self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)
            print(f"✅ ElevenLabs ready (voice: {self.elevenlabs_voice_id})")

        if GOOGLE_STT_AVAILABLE:
            self.speech_client = speech.SpeechClient()
            print("✅ Google STT ready")

    async def transcribe_audio(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes using Google Cloud STT.
        """
        if not self.speech_client:
            return ""

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        audio = speech.RecognitionAudio(content=audio_bytes)

        try:
            response = self.speech_client.recognize(config=config, audio=audio)

            if response.results:
                return response.results[0].alternatives[0].transcript
            return ""
        except Exception as e:
            print(f"STT error: {e}")
            return ""

    async def get_response(self, text: str, session: VoiceSession) -> str:
        """
        Get response from Gemini using session history.
        """
        session.add_message("user", text)

        # Build conversation
        contents = []
        for msg in session.history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Get agent prompt
        agent = VOICE_AGENTS.get(session.agent_id, VOICE_AGENTS["larry"])

        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config={
                    "system_instruction": agent["prompt"],
                    "temperature": 0.8,
                    "max_output_tokens": 200,  # Keep short for voice
                }
            )

            assistant_text = response.text.strip()
            session.add_message("assistant", assistant_text)
            return assistant_text

        except Exception as e:
            print(f"Gemini error: {e}")
            return "I'm sorry, I had trouble processing that. Could you say it again?"

    async def get_response_streaming(self, text: str, session: VoiceSession):
        """
        Stream response from Gemini for lower latency.
        Yields text chunks as they're generated.
        """
        session.add_message("user", text)

        contents = []
        for msg in session.history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        agent = VOICE_AGENTS.get(session.agent_id, VOICE_AGENTS["larry"])

        try:
            response_stream = self.gemini_client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=contents,
                config={
                    "system_instruction": agent["prompt"],
                    "temperature": 0.8,
                    "max_output_tokens": 200,
                }
            )

            full_response = ""
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text

            session.add_message("assistant", full_response)

        except Exception as e:
            print(f"Gemini streaming error: {e}")
            yield "Sorry, I had trouble with that."

    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech using ElevenLabs.
        Returns MP3 audio bytes.
        """
        if not self.elevenlabs_client:
            return b""

        try:
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=self.elevenlabs_voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",  # Fastest model
                output_format="mp3_44100_128",  # MP3 for browser
            )

            # Collect all chunks
            audio_data = b"".join(chunk for chunk in audio_generator)
            return audio_data

        except Exception as e:
            print(f"TTS error: {e}")
            return b""

    async def text_to_speech_streaming(self, text: str):
        """
        Stream TTS audio chunks for lower latency.
        Yields MP3 chunks as they're generated.
        """
        if not self.elevenlabs_client:
            return

        try:
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=self.elevenlabs_voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )

            for chunk in audio_generator:
                yield chunk

        except Exception as e:
            print(f"TTS streaming error: {e}")


# Global pipeline instance
pipeline = VoicePipeline()

# =============================================================================
# WebSocket Handler
# =============================================================================

async def handle_voice_connection(websocket):
    """
    Handle a WebSocket connection for real-time voice.

    Protocol:
    - Client sends: {"type": "audio", "audio": "<base64>", "sample_rate": 16000}
    - Client sends: {"type": "text", "text": "user message"}  (fallback)
    - Client sends: {"type": "switch_agent", "agent_id": "tta"}
    - Client sends: {"type": "interrupt"}

    - Server sends: {"type": "transcript", "text": "transcribed text"}
    - Server sends: {"type": "response_start", "text": ""}
    - Server sends: {"type": "response_chunk", "text": "chunk"}
    - Server sends: {"type": "response_end", "text": "full response"}
    - Server sends: {"type": "audio", "audio": "<base64 mp3>"}
    - Server sends: {"type": "audio_chunk", "audio": "<base64 mp3 chunk>"}
    """
    # Create session
    session_id = str(uuid.uuid4())
    session = VoiceSession(session_id=session_id)
    sessions[session_id] = session

    print(f"🎤 Voice session started: {session_id[:8]}")

    # Send session info
    await websocket.send(json.dumps({
        "type": "session_started",
        "session_id": session_id,
        "agent": session.agent_id,
        "agent_name": VOICE_AGENTS[session.agent_id]["name"],
    }))

    # Send greeting
    greeting = "Hi! I'm Larry, your PWS thinking partner. What are you working on?"
    await websocket.send(json.dumps({
        "type": "response_start",
        "text": greeting,
    }))

    # Generate and send greeting audio
    greeting_audio = await pipeline.text_to_speech(greeting)
    if greeting_audio:
        await websocket.send(json.dumps({
            "type": "audio",
            "audio": base64.b64encode(greeting_audio).decode("utf-8"),
        }))

    await websocket.send(json.dumps({"type": "response_end", "text": greeting}))

    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")

            # ─────────────────────────────────────────────────────────────
            # Handle audio input
            # ─────────────────────────────────────────────────────────────
            if msg_type == "audio":
                audio_bytes = base64.b64decode(data["audio"])
                sample_rate = data.get("sample_rate", 16000)

                # Transcribe
                transcript = await pipeline.transcribe_audio(audio_bytes, sample_rate)

                if transcript:
                    print(f"👤 User: {transcript}")

                    # Send transcript to client
                    await websocket.send(json.dumps({
                        "type": "transcript",
                        "text": transcript,
                    }))

                    # Check for exit
                    if transcript.lower() in ["goodbye", "exit", "quit", "bye", "stop"]:
                        farewell = "Great talking with you! Goodbye!"
                        farewell_audio = await pipeline.text_to_speech(farewell)
                        await websocket.send(json.dumps({
                            "type": "response_start",
                            "text": farewell,
                        }))
                        if farewell_audio:
                            await websocket.send(json.dumps({
                                "type": "audio",
                                "audio": base64.b64encode(farewell_audio).decode("utf-8"),
                            }))
                        await websocket.send(json.dumps({"type": "session_ended"}))
                        break

                    # Get response and convert to speech
                    await process_and_respond(websocket, transcript, session)

            # ─────────────────────────────────────────────────────────────
            # Handle text input (fallback / typing)
            # ─────────────────────────────────────────────────────────────
            elif msg_type == "text":
                text = data.get("text", "").strip()
                if text:
                    print(f"👤 User (text): {text}")
                    await process_and_respond(websocket, text, session)

            # ─────────────────────────────────────────────────────────────
            # Handle agent switch
            # ─────────────────────────────────────────────────────────────
            elif msg_type == "switch_agent":
                new_agent = data.get("agent_id", "larry")
                if new_agent in VOICE_AGENTS:
                    session.agent_id = new_agent
                    agent_name = VOICE_AGENTS[new_agent]["name"]
                    print(f"🔄 Switched to {agent_name}")

                    switch_msg = f"Switching you to {agent_name}. How can I help?"
                    await websocket.send(json.dumps({
                        "type": "agent_switched",
                        "agent_id": new_agent,
                        "agent_name": agent_name,
                    }))

                    switch_audio = await pipeline.text_to_speech(switch_msg)
                    if switch_audio:
                        await websocket.send(json.dumps({
                            "type": "audio",
                            "audio": base64.b64encode(switch_audio).decode("utf-8"),
                        }))

            # ─────────────────────────────────────────────────────────────
            # Handle interrupt (user started speaking)
            # ─────────────────────────────────────────────────────────────
            elif msg_type == "interrupt":
                session.should_interrupt = True
                print("🔇 User interrupted")

    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 Voice session ended: {session_id[:8]}")
    finally:
        # Cleanup
        if session_id in sessions:
            del sessions[session_id]


async def process_and_respond(websocket, text: str, session: VoiceSession):
    """
    Process user input and send streaming response with audio.
    """
    session.is_speaking = True
    session.should_interrupt = False

    await websocket.send(json.dumps({"type": "response_start", "text": ""}))

    # Stream response from Gemini
    full_response = ""
    text_buffer = ""
    MIN_CHARS = 40  # Minimum chars before TTS

    async for chunk in pipeline.get_response_streaming(text, session):
        if session.should_interrupt:
            break

        full_response += chunk
        text_buffer += chunk

        # Send text chunk to client
        await websocket.send(json.dumps({
            "type": "response_chunk",
            "text": chunk,
        }))

        # Convert to speech when we have enough text or hit sentence end
        sentence_end = text_buffer.rstrip().endswith((".", "!", "?", ":"))
        enough_text = len(text_buffer) >= MIN_CHARS

        if (sentence_end or enough_text) and text_buffer.strip():
            audio_chunk = await pipeline.text_to_speech(text_buffer.strip())
            if audio_chunk and not session.should_interrupt:
                await websocket.send(json.dumps({
                    "type": "audio_chunk",
                    "audio": base64.b64encode(audio_chunk).decode("utf-8"),
                }))
            text_buffer = ""

    # Send remaining text as audio
    if text_buffer.strip() and not session.should_interrupt:
        audio_chunk = await pipeline.text_to_speech(text_buffer.strip())
        if audio_chunk:
            await websocket.send(json.dumps({
                "type": "audio_chunk",
                "audio": base64.b64encode(audio_chunk).decode("utf-8"),
            }))

    # Signal response complete
    await websocket.send(json.dumps({
        "type": "response_end",
        "text": full_response,
    }))

    print(f"🤖 {VOICE_AGENTS[session.agent_id]['name']}: {full_response[:100]}...")
    session.is_speaking = False


# =============================================================================
# Server Entry Point
# =============================================================================

async def start_voice_server(host: str = "0.0.0.0", port: int = 8765):
    """Start the WebSocket voice server."""
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║         MINDRIAN REAL-TIME VOICE SERVER                           ║
╠═══════════════════════════════════════════════════════════════════╣
║  WebSocket: ws://{host}:{port}                                     ║
║  Pipeline:  🎤 Google STT → 🧠 Gemini → 🔊 ElevenLabs             ║
╠═══════════════════════════════════════════════════════════════════╣
║  Agents:    larry, tta, jtbd, redteam                             ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    async with serve(handle_voice_connection, host, port):
        print(f"🎤 Voice server listening on ws://{host}:{port}")
        await asyncio.Future()  # Run forever


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Mindrian Voice Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    args = parser.parse_args()

    asyncio.run(start_voice_server(args.host, args.port))


if __name__ == "__main__":
    main()
