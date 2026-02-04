"""
Mindrian Real-Time Voice Chat
=============================

Hybrid architecture:
- Google Cloud Speech-to-Text (Streaming) → STT
- Google Gemini → Intelligence/LLM
- ElevenLabs → TTS with custom voice

Flow:
    🎤 User speaks → Google STT → Gemini → ElevenLabs TTS → 🔊 Audio response

Run: python realtime_voice.py
"""

import os
import asyncio
import queue
import threading
import time
from typing import Optional, AsyncGenerator
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Audio Configuration
# =============================================================================

SAMPLE_RATE_INPUT = 16000   # Google STT expects 16kHz
SAMPLE_RATE_OUTPUT = 24000  # ElevenLabs output
CHUNK_SIZE = 1024           # Audio chunk size

# =============================================================================
# Google Cloud Speech-to-Text (Streaming)
# =============================================================================

try:
    from google.cloud import speech_v1 as speech
    from google.cloud.speech_v1 import SpeechClient
    GOOGLE_STT_AVAILABLE = True
except ImportError:
    GOOGLE_STT_AVAILABLE = False
    print("⚠️  Install: pip install google-cloud-speech")

# =============================================================================
# Google Gemini (Intelligence)
# =============================================================================

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Install: pip install google-genai")

# =============================================================================
# ElevenLabs TTS (Custom Voice)
# =============================================================================

try:
    from elevenlabs import ElevenLabs
    from elevenlabs.conversational_ai.conversation import Conversation
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("⚠️  Install: pip install elevenlabs")

# =============================================================================
# PyAudio for Microphone/Speaker
# =============================================================================

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️  Install: pip install pyaudio")

# =============================================================================
# Import Mindrian Prompts
# =============================================================================

try:
    from prompts import LARRY_RAG_SYSTEM_PROMPT
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False
    LARRY_RAG_SYSTEM_PROMPT = """You are Lawrence (Larry), a warm and insightful PWS methodology expert.
Keep responses SHORT and conversational - this is a voice chat.
Ask ONE question at a time. Be encouraging and Socratic."""

# =============================================================================
# Voice-Optimized System Prompt
# =============================================================================

VOICE_SYSTEM_PROMPT = LARRY_RAG_SYSTEM_PROMPT + """

## Voice Conversation Mode
You are now in REAL-TIME VOICE mode. Critical guidelines:

1. **BREVITY**: Keep responses to 2-3 sentences MAX. This is spoken, not written.
2. **NATURAL SPEECH**: Use conversational language, contractions, filler words like "So...", "Well...", "Hmm..."
3. **ONE QUESTION**: Ask only ONE question per response
4. **NO FORMATTING**: No bullet points, no markdown, no lists - just natural speech
5. **THINKING ALOUD**: It's OK to say "Let me think about that..." or "That's interesting..."
6. **INTERRUPTION-FRIENDLY**: End responses cleanly so user can jump in
7. **WARMTH**: You're having a conversation with a friend, be warm and encouraging

Example good response:
"Ah, that's a really interesting problem! So you're trying to figure out if there's a real market for this. Have you talked to any potential customers yet?"

Example bad response:
"That's a great question! Here are the key considerations:
1. Market validation
2. Customer interviews
3. Competitive analysis
Let me know which one you'd like to explore first!"
"""

# =============================================================================
# Real-Time Voice Session
# =============================================================================

@dataclass
class VoiceSession:
    """Manages a real-time voice conversation session."""

    conversation_history: list = None
    is_active: bool = False
    current_agent: str = "larry"

    def __post_init__(self):
        self.conversation_history = []
        self.audio_input_queue = queue.Queue()
        self.audio_output_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.is_speaking = False
        self.should_interrupt = False

    def add_user_message(self, text: str):
        self.conversation_history.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str):
        self.conversation_history.append({"role": "assistant", "content": text})


class RealtimeVoiceChat:
    """
    Real-time voice chat using:
    - Google Cloud STT (streaming speech recognition)
    - Gemini (intelligence)
    - ElevenLabs (custom voice TTS)
    """

    def __init__(
        self,
        elevenlabs_api_key: Optional[str] = None,
        elevenlabs_voice_id: Optional[str] = None,
        google_api_key: Optional[str] = None,
    ):
        # API Keys
        self.elevenlabs_api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = elevenlabs_voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")

        # Initialize clients
        self.gemini_client = None
        self.elevenlabs_client = None
        self.speech_client = None

        # Session state
        self.session = VoiceSession()

        # Audio
        self.pyaudio_instance = None
        self.input_stream = None
        self.output_stream = None

        self._validate_setup()

    def _validate_setup(self):
        """Validate all required components are available."""
        missing = []

        if not GOOGLE_STT_AVAILABLE:
            missing.append("google-cloud-speech")
        if not GEMINI_AVAILABLE:
            missing.append("google-genai")
        if not ELEVENLABS_AVAILABLE:
            missing.append("elevenlabs")
        if not PYAUDIO_AVAILABLE:
            missing.append("pyaudio")

        if not self.google_api_key:
            missing.append("GOOGLE_API_KEY env var")
        if not self.elevenlabs_api_key:
            missing.append("ELEVENLABS_API_KEY env var")

        if missing:
            print(f"❌ Missing: {', '.join(missing)}")
            return False

        print("✅ All components available")
        return True

    def _init_clients(self):
        """Initialize API clients."""
        # Gemini
        if GEMINI_AVAILABLE and self.google_api_key:
            self.gemini_client = genai.Client(api_key=self.google_api_key)
            print("✅ Gemini client initialized")

        # ElevenLabs
        if ELEVENLABS_AVAILABLE and self.elevenlabs_api_key:
            self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)
            print(f"✅ ElevenLabs client initialized (voice: {self.elevenlabs_voice_id})")

        # Google Cloud STT
        if GOOGLE_STT_AVAILABLE:
            self.speech_client = SpeechClient()
            print("✅ Google Cloud STT client initialized")

    def _init_audio(self):
        """Initialize PyAudio streams."""
        if not PYAUDIO_AVAILABLE:
            return

        self.pyaudio_instance = pyaudio.PyAudio()

        # Input stream (microphone)
        self.input_stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE_INPUT,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        # Output stream (speaker)
        self.output_stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE_OUTPUT,
            output=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        print("✅ Audio streams initialized")

    # =========================================================================
    # Google Cloud STT (Streaming)
    # =========================================================================

    def _create_stt_config(self) -> speech.StreamingRecognitionConfig:
        """Create Google STT streaming config."""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE_INPUT,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long",  # Best for conversations
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,  # Get partial results for responsiveness
            single_utterance=False,  # Continuous listening
        )

        return streaming_config

    def _audio_generator(self):
        """Generate audio chunks from microphone for STT."""
        print("🎤 Listening... (speak now)")

        while self.session.is_active:
            try:
                # Read from microphone
                data = self.input_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                yield speech.StreamingRecognizeRequest(audio_content=data)
            except Exception as e:
                print(f"Audio read error: {e}")
                break

    async def transcribe_stream(self) -> AsyncGenerator[str, None]:
        """
        Stream audio to Google STT and yield transcriptions.
        Yields both interim (partial) and final results.
        """
        streaming_config = self._create_stt_config()

        # Create streaming request
        requests = self._audio_generator()
        responses = self.speech_client.streaming_recognize(
            config=streaming_config,
            requests=requests,
        )

        for response in responses:
            if not response.results:
                continue

            result = response.results[0]

            if result.is_final:
                transcript = result.alternatives[0].transcript.strip()
                if transcript:
                    print(f"👤 User: {transcript}")
                    yield transcript

    # =========================================================================
    # Gemini (Intelligence)
    # =========================================================================

    async def get_gemini_response(self, user_text: str) -> str:
        """Get response from Gemini."""
        self.session.add_user_message(user_text)

        # Build conversation contents
        contents = []
        for msg in self.session.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Generate response
        response = self.gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config={
                "system_instruction": VOICE_SYSTEM_PROMPT,
                "temperature": 0.8,
                "max_output_tokens": 256,  # Keep responses short for voice
            }
        )

        assistant_text = response.text.strip()
        self.session.add_assistant_message(assistant_text)

        print(f"🤖 Larry: {assistant_text}")
        return assistant_text

    async def get_gemini_response_stream(self, user_text: str) -> AsyncGenerator[str, None]:
        """Stream response from Gemini for lower latency."""
        self.session.add_user_message(user_text)

        contents = []
        for msg in self.session.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        response = self.gemini_client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=contents,
            config={
                "system_instruction": VOICE_SYSTEM_PROMPT,
                "temperature": 0.8,
                "max_output_tokens": 256,
            }
        )

        full_response = ""
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text

        self.session.add_assistant_message(full_response)

    # =========================================================================
    # ElevenLabs TTS (Custom Voice)
    # =========================================================================

    async def speak_text(self, text: str):
        """Convert text to speech using ElevenLabs and play it."""
        self.session.is_speaking = True

        try:
            # Generate audio with ElevenLabs
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=self.elevenlabs_voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",  # Fast, low-latency model
                output_format="pcm_24000",  # Raw PCM for direct playback
            )

            # Play audio chunks
            for chunk in audio_generator:
                if self.session.should_interrupt:
                    print("🔇 Interrupted!")
                    break
                self.output_stream.write(chunk)

        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            self.session.is_speaking = False
            self.session.should_interrupt = False

    async def speak_text_streaming(self, text_generator: AsyncGenerator[str, None]):
        """
        Stream TTS - start speaking as soon as we have enough text.
        This reduces latency by not waiting for full response.
        """
        self.session.is_speaking = True
        buffer = ""
        min_chars = 50  # Minimum characters before starting TTS

        try:
            async for chunk in text_generator:
                buffer += chunk

                # Start TTS when we have enough text or hit a sentence end
                if len(buffer) >= min_chars or buffer.rstrip().endswith((".", "!", "?", ":")):
                    if buffer.strip():
                        await self.speak_text(buffer.strip())
                    buffer = ""

                    if self.session.should_interrupt:
                        break

            # Speak remaining buffer
            if buffer.strip() and not self.session.should_interrupt:
                await self.speak_text(buffer.strip())

        finally:
            self.session.is_speaking = False
            self.session.should_interrupt = False

    # =========================================================================
    # Main Conversation Loop
    # =========================================================================

    async def run_conversation(self):
        """
        Main real-time voice conversation loop with FULL STREAMING.

        Low-latency flow:
        1. 🎤 Listen (Google STT - streaming) → partial transcripts
        2. 🧠 Think (Gemini - streaming) → start processing immediately
        3. 🔊 Speak (ElevenLabs - streaming) → start speaking while still generating

        Target latency: < 500ms from end of speech to start of response
        """
        print("\n" + "=" * 60)
        print("🎙️  MINDRIAN REAL-TIME VOICE CHAT (LOW LATENCY)")
        print("=" * 60)
        print("🎤 Google STT (stream) → 🧠 Gemini (stream) → 🔊 ElevenLabs (stream)")
        print("=" * 60)
        print("\nSay 'goodbye' or 'exit' to end the conversation.")
        print("Press Ctrl+C to force quit.\n")

        self._init_clients()
        self._init_audio()

        self.session.is_active = True

        # Opening greeting
        greeting = "Hi there! I'm Larry, your PWS thinking partner. What problem are you working on today?"
        print(f"🤖 Larry: {greeting}")
        await self.speak_text(greeting)

        try:
            async for transcript in self.transcribe_stream():
                # Check for exit commands
                if transcript.lower() in ["goodbye", "exit", "quit", "bye", "stop"]:
                    farewell = "Great talking with you! Good luck with your problem. Goodbye!"
                    print(f"🤖 Larry: {farewell}")
                    await self.speak_text(farewell)
                    break

                # Interrupt if user speaks while Larry is speaking
                if self.session.is_speaking:
                    self.session.should_interrupt = True
                    await asyncio.sleep(0.1)  # Wait for interrupt to process

                # STREAMING: Start TTS as soon as Gemini starts generating
                await self.respond_streaming(transcript)

        except KeyboardInterrupt:
            print("\n\n👋 Conversation ended by user.")
        finally:
            self.session.is_active = False
            self._cleanup()

    async def respond_streaming(self, user_text: str):
        """
        FULLY STREAMING response pipeline for minimum latency.

        Uses ElevenLabs streaming TTS that accepts text chunks
        and starts generating audio immediately.
        """
        self.session.add_user_message(user_text)
        self.session.is_speaking = True

        contents = []
        for msg in self.session.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        try:
            # Start Gemini streaming
            response_stream = self.gemini_client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=contents,
                config={
                    "system_instruction": VOICE_SYSTEM_PROMPT,
                    "temperature": 0.8,
                    "max_output_tokens": 256,
                }
            )

            # Use ElevenLabs streaming TTS with text input stream
            full_response = ""
            text_buffer = ""
            MIN_CHARS_TO_SPEAK = 30  # Start TTS after this many chars

            print("🤖 Larry: ", end="", flush=True)

            for chunk in response_stream:
                if self.session.should_interrupt:
                    break

                if chunk.text:
                    full_response += chunk.text
                    text_buffer += chunk.text
                    print(chunk.text, end="", flush=True)

                    # Start speaking when we hit sentence boundary or enough text
                    sentence_end = text_buffer.rstrip().endswith((".", "!", "?", ":", ","))
                    enough_text = len(text_buffer) >= MIN_CHARS_TO_SPEAK

                    if sentence_end or enough_text:
                        if text_buffer.strip():
                            await self._speak_chunk(text_buffer.strip())
                        text_buffer = ""

            # Speak any remaining text
            if text_buffer.strip() and not self.session.should_interrupt:
                await self._speak_chunk(text_buffer.strip())

            print()  # Newline after response
            self.session.add_assistant_message(full_response)

        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.session.is_speaking = False
            self.session.should_interrupt = False

    async def _speak_chunk(self, text: str):
        """Speak a single text chunk with ElevenLabs."""
        if not text or self.session.should_interrupt:
            return

        try:
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=self.elevenlabs_voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",  # Fastest model (~300ms latency)
                output_format="pcm_24000",
            )

            for audio_chunk in audio_generator:
                if self.session.should_interrupt:
                    break
                self.output_stream.write(audio_chunk)

        except Exception as e:
            print(f"TTS chunk error: {e}")

    def _cleanup(self):
        """Clean up audio resources."""
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        print("✅ Audio resources cleaned up")


# =============================================================================
# Alternative: WebSocket Server for Browser Integration
# =============================================================================

async def create_websocket_voice_server(host: str = "0.0.0.0", port: int = 8765):
    """
    WebSocket server for browser-based real-time voice.
    Browser sends audio → Server processes → Sends back audio.
    """
    import websockets
    import json
    import base64

    voice_chat = RealtimeVoiceChat()
    voice_chat._init_clients()

    async def handle_connection(websocket, path):
        print(f"🌐 New WebSocket connection from {websocket.remote_address}")
        session = VoiceSession()
        session.is_active = True

        try:
            async for message in websocket:
                data = json.loads(message)

                if data["type"] == "audio":
                    # Decode audio from base64
                    audio_bytes = base64.b64decode(data["audio"])

                    # TODO: Send to Google STT for transcription
                    # For now, assume we receive text
                    pass

                elif data["type"] == "text":
                    # User sent text directly
                    user_text = data["text"]
                    print(f"👤 User: {user_text}")

                    # Get Gemini response
                    response = await voice_chat.get_gemini_response(user_text)

                    # Generate TTS audio
                    audio_generator = voice_chat.elevenlabs_client.text_to_speech.convert(
                        voice_id=voice_chat.elevenlabs_voice_id,
                        text=response,
                        model_id="eleven_turbo_v2_5",
                        output_format="mp3_44100_128",
                    )

                    # Collect audio chunks
                    audio_data = b"".join(chunk for chunk in audio_generator)

                    # Send back to browser
                    await websocket.send(json.dumps({
                        "type": "audio",
                        "text": response,
                        "audio": base64.b64encode(audio_data).decode("utf-8"),
                    }))

        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Connection closed")
        finally:
            session.is_active = False

    print(f"\n🌐 Starting WebSocket voice server on ws://{host}:{port}")
    async with websockets.serve(handle_connection, host, port):
        await asyncio.Future()  # Run forever


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Mindrian Real-Time Voice Chat")
    parser.add_argument("--mode", choices=["local", "server"], default="local",
                        help="Run mode: 'local' for microphone, 'server' for WebSocket")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    args = parser.parse_args()

    print("""
╔═══════════════════════════════════════════════════════════════════╗
║           MINDRIAN REAL-TIME VOICE CHAT                           ║
╠═══════════════════════════════════════════════════════════════════╣
║  🎤 Google Cloud STT (Speech-to-Text)                             ║
║  🧠 Google Gemini (Intelligence)                                  ║
║  🔊 ElevenLabs TTS (Your Custom Voice)                            ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    voice_chat = RealtimeVoiceChat()

    if args.mode == "local":
        asyncio.run(voice_chat.run_conversation())
    else:
        asyncio.run(create_websocket_voice_server(port=args.port))


if __name__ == "__main__":
    main()
