# Voice Improvements - Advanced ElevenLabs Patterns

## What Is This?

Enhanced voice capabilities using ElevenLabs' advanced features: WebSocket streaming for lower latency, Conversational AI agents, and improved voice quality settings.

## Why Implement This?

### Current State
- Basic TTS implemented with `text_to_speech()` in `utils/media.py`
- Uses `convert_as_stream` for streaming
- Model: `eleven_multilingual_v2`
- Latency: 2-4 seconds per response

### Opportunities for Improvement
1. **WebSocket Streaming**: Real-time audio as it generates
2. **Conversational AI Agent**: Native voice assistant (sub-1s latency)
3. **Voice Cloning**: Create "Larry" voice from samples
4. **Interruption Handling**: User can interrupt mid-response

## Three Integration Patterns

### Pattern 1: Current (Text Pipeline) ✅ Implemented
```
User Audio → Gemini STT → LLM → ElevenLabs TTS → Audio Output
Latency: 2-4 seconds
```

### Pattern 2: WebSocket Streaming (Lower Latency)
```python
class ElevenLabsWebSocketTTS:
    async def stream_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        async with websockets.connect(self.ws_url, extra_headers=headers) as ws:
            await ws.send(json.dumps({"text": text, "voice_settings": {...}}))

            while True:
                message = await ws.recv()
                if isinstance(message, bytes):
                    yield message  # Stream chunks immediately
```
**Latency: 1-2 seconds (perceived faster)**

### Pattern 3: ElevenLabs Conversational AI
```python
# ElevenLabs handles STT + LLM + TTS internally
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=API_KEY)
conversation = client.conversational_ai.conversations.create_with_text(
    agent_id="YOUR_AGENT_ID"
)
```
**Latency: 500ms-1.5s (native voice AI)**

## Voice Quality Settings

Current settings in `utils/media.py`:
```python
stability=0.71,           # Higher = more consistent
similarity_boost=0.75,    # Higher = more like original voice
use_speaker_boost=True    # Clearer audio
```

### Recommended Adjustments by Use Case

| Use Case | Stability | Similarity | Model |
|----------|-----------|------------|-------|
| Workshop (clarity) | 0.75 | 0.70 | eleven_multilingual_v2 |
| Conversational | 0.50 | 0.80 | eleven_turbo_v2_5 |
| Dramatic reading | 0.30 | 0.85 | eleven_multilingual_v2 |

## Voice Options

Current voice: `21m00Tcm4TlvDq8ikWAM` (Rachel)

### Recommended Voices for Mindrian

```python
LARRY_VOICES = {
    "default": "21m00Tcm4TlvDq8ikWAM",      # Rachel - warm, professional
    "energetic": "EXAVITQu4vr4xnSDxMaL",    # Bella - friendly
    "authoritative": "JBFqnCBsd6RMkjVDRZzb", # Adam - professional male
    "calm": "Xb7hH8MSUJpSbvTk6ES5",         # Callum - soothing
}
```

## Implementation Plan

### Phase 1: WebSocket Streaming (Medium Effort)
```python
# Add to utils/media.py
async def text_to_speech_streaming(text: str, voice_id: str = None):
    """Stream audio chunks in real-time for lower perceived latency."""
    ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-websocket"
    # ... implementation
```

### Phase 2: Voice Selection UI (Low Effort)
Allow users to select Larry's voice in settings:
```python
@cl.on_settings_update
async def settings_update(settings):
    voice_id = settings.get("larry_voice", "default")
    cl.user_session.set("voice_id", LARRY_VOICES[voice_id])
```

### Phase 3: Custom Larry Voice (High Effort)
- Collect 30+ minutes of ideal "Larry" voice samples
- Upload to ElevenLabs for voice cloning
- Use cloned voice for all responses

## Files to Modify

| File | Action |
|------|--------|
| `utils/media.py` | ADD WebSocket streaming, voice options |
| `mindrian_chat.py` | MODIFY audio handlers for streaming |
| `.chainlit/config.toml` | ADD voice selection setting |

## API Costs

| Feature | Cost |
|---------|------|
| Standard TTS | ~$0.30 per 1K chars |
| Turbo Model | ~$0.15 per 1K chars |
| Voice Cloning | $5/month (starter) |
| Conversational AI | $0.08 per minute |

## Status

- [x] Basic TTS implemented
- [x] Streaming API used
- [x] WebSocket real-time streaming (utils/elevenlabs_streaming.py)
- [ ] Voice selection UI
- [ ] Custom Larry voice
- [ ] Conversational AI agent

## Real-Time Browser Audio Streaming (2026-01-25)

Complete implementation using Chainlit's `send_audio_chunk()` for real-time browser playback.

### Architecture

```
User speaks → Gemini STT → LLM Stream → ElevenLabs WebSocket → Browser Audio Playback
                                              ↓
                              cl.context.emitter.send_audio_chunk()
                                              ↓
                              OutputAudioChunk → Browser plays immediately
```

### Key Files

| File | Purpose |
|------|---------|
| `utils/voice_streaming.py` | Complete real-time voice pipeline |
| `utils/elevenlabs_streaming.py` | Low-level WebSocket TTS |
| `mindrian_chat.py` | Audio handlers (@cl.on_audio_*) |

### Key Classes & Functions

**utils/voice_streaming.py:**
- `RealtimeVoiceStreamer`: Streams to browser via `send_audio_chunk()`
- `VoiceConfig`: Voice settings (voice_id, model, stability)
- `is_voice_enabled()`: Check if voice is configured
- `stream_gemini_with_voice()`: Complete Gemini → Voice pipeline

**utils/elevenlabs_streaming.py:**
- `ElevenLabsStreamingTTS`: WebSocket-based TTS with BOS/EOS protocol
- `stream_gemini_to_elevenlabs()`: Direct Gemini → ElevenLabs pipeline
- `text_chunker()`: Natural boundary text splitting for prosody

### WebSocket Protocol (BOS/EOS)

```python
# 1. BOS (Beginning of Stream) - send API key in message body
bos_message = {
    "text": " ",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    "xi_api_key": api_key,  # Key goes in message, NOT headers
}
await ws.send(json.dumps(bos_message))

# 2. Send text chunks with trigger flag
await ws.send(json.dumps({
    "text": chunk,
    "try_trigger_generation": True,  # Required for streaming
}))

# 3. EOS (End of Stream) - empty text signals completion
await ws.send(json.dumps({"text": ""}))
```

### Browser Audio Streaming

```python
from chainlit.types import OutputAudioChunk

# Send audio chunk directly to browser for playback
await cl.context.emitter.send_audio_chunk(
    OutputAudioChunk(
        mimeType="audio/mpeg",
        data=audio_bytes,
        track=track_id  # Unique per session
    )
)
```

**Key requirement:** User must interact with microphone first (browser security).

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ELEVENLABS_API_KEY` | Required | API key |
| `ELEVENLABS_VOICE_ID` | `SGh5MKvZcSYNF0SZXlAg` | Larry voice |

### Flow

```
User speaks → Gemini STT → LLM Stream → TTS WebSocket → Browser Audio (real-time)
```

**Latency improvement:** ~3-6s → ~1-2s to first audio

### Dependencies

- `websockets>=12.0` (NOT aiohttp - ElevenLabs requires specific WebSocket library)
- `chainlit>=2.9.0` (Required for send_audio_chunk support)

---

## Evaluation: OpenAI Realtime WebRTC (2026-01-29)

**Question:** Should Mindrian adopt OpenAI Realtime API with WebRTC for voice?

### What OpenAI Realtime Offers

```
User Speech <--WebRTC--> OpenAI Realtime API
                              ↓
                         GPT-4o Voice
                              ↓
                       Direct Audio Response
```

**Key features:**
- Native voice-to-voice (no separate STT/TTS)
- Sub-500ms latency
- Natural interruption handling
- Built-in turn detection

### Comparison

| Feature | Current (Gemini + ElevenLabs) | OpenAI Realtime |
|---------|-------------------------------|-----------------|
| STT Provider | Gemini | OpenAI (native) |
| LLM Provider | Gemini | GPT-4o |
| TTS Provider | ElevenLabs | OpenAI (native) |
| Voice Quality | Excellent (custom voices) | Good (limited voices) |
| Latency | 1-2s | <500ms |
| Complexity | Medium | High (WebRTC) |
| Cost | ~$0.01-0.03/msg | ~$0.06/min audio |
| Customization | High | Limited |

### Why NOT to Switch (Recommendation)

1. **Consistency**: Mindrian uses Gemini throughout. Mixing OpenAI for voice creates cognitive dissonance.

2. **Voice Quality**: ElevenLabs offers superior voice customization (cloning, tuning). OpenAI voices are limited.

3. **Cost**: OpenAI Realtime is priced per minute of audio ($0.06/min input + $0.24/min output). For a workshop platform with longer sessions, this adds up quickly.

4. **Complexity**: WebRTC requires:
   - Ephemeral key server endpoint
   - Browser peer connection management
   - No direct Chainlit integration documented

5. **Value Proposition**: Mindrian is a workshop/coaching platform where text interaction is primary. Voice is secondary/optional.

### When OpenAI Realtime WOULD Make Sense

- Building a voice-first product (phone bot, voice assistant)
- Need native interruption handling
- Already using OpenAI ecosystem
- Latency is critical (<500ms)

### Decision

**Keep current architecture (Gemini + ElevenLabs).**

The 1-2 second latency is acceptable for workshop use cases, and the flexibility of ElevenLabs voices + Gemini's multimodal capabilities is more valuable than raw speed.

**Future consideration:** If Chainlit adds native OpenAI Realtime integration, revisit this evaluation.

### Sources

- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [OpenAI Realtime WebRTC Guide](https://platform.openai.com/docs/guides/realtime-webrtc)
- [Chainlit OpenAI Integration](https://docs.chainlit.io/integrations/openai)
