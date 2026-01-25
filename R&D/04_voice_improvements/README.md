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

## New: Real-Time Streaming (2026-01-25)

Added `utils/elevenlabs_streaming.py` with:
- `ElevenLabsStreamingTTS`: WebSocket-based TTS for real-time audio
- `ElevenLabsConversationalAI`: Full conversation mode (requires Agent ID)
- Integration in `mindrian_chat.py` audio handlers

Flow:
```
User speaks → Gemini STT → LLM Stream → TTS WebSocket → Audio chunks → Play immediately
```

**Latency improvement:** ~3-6s → ~1-2s to first audio
