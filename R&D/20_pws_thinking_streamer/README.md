# PWS Thinking Streamer

## Overview

A Claude Code-inspired real-time thinking indicator that streams PWS/Larry-style vocabulary tokens while background processing happens. Creates an engaging UX where users see Lawrence "actively reasoning" through their documents instead of static "Processing..." messages.

## Inspiration

Claude Code displays streaming "thinking" tokens in orange text (like "sizzeling...", "codifying...") while the model reasons. This creates:
- **Transparency**: Shows the AI is actively working, not frozen
- **Progress feedback**: Real-time streaming makes long operations feel responsive
- **Engagement**: Playful pseudo-words make the AI feel "alive"

## Implementation

### Location
`mindrian_chat.py` lines 556-640

### Core Components

#### 1. PWS Thinking Tokens
```python
PWS_THINKING_TOKENS = [
    # Discovery / unpacking
    "unpacking...", "digging in...", "following threads...", "connecting dots...",
    "mapping terrain...", "scanning landscape...", "tracing patterns...",

    # PWS methodology concepts
    "what's the real job here...", "checking assumptions...", "where's the bottleneck...",
    "trending this forward...", "what breaks first...", "who cares most...",
    "what's the reverse salient...", "where on the curve...", "DIKW check...",

    # Analytical thinking
    "hypothesizing...", "stress-testing...", "validating...", "synthesizing...",
    "cross-referencing...", "contextualizing...", "reframing...", "inverting...",

    # Engagement / curiosity
    "interesting angle...", "hmm, this connects to...", "worth exploring...",
    "there's something here...", "the real question is...", "let me think...",

    # Progress signals
    "almost there...", "coming together...", "crystallizing...", "emerging picture...",
]
```

#### 2. Streaming Utility Function
```python
async def stream_thinking_while_processing(
    msg: "cl.Message",
    blocking_func,
    *args,
    color: str = "#f59e0b",  # Amber/orange
    interval: float = 0.4,
    **kwargs
):
    """
    Run a blocking function in background while streaming PWS thinking tokens.
    """
    import asyncio
    import concurrent.futures

    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    # Start blocking work in thread
    future = loop.run_in_executor(executor, lambda: blocking_func(*args, **kwargs))

    # Stream thinking tokens while waiting
    tokens_used = set()
    while not future.done():
        available = [t for t in PWS_THINKING_TOKENS if t not in tokens_used]
        if not available:
            tokens_used.clear()
            available = PWS_THINKING_TOKENS

        token = random.choice(available)
        tokens_used.add(token)

        await msg.stream_token(f"*{token}* ")
        await asyncio.sleep(interval)

    result = await future
    await msg.stream_token("\n")
    return result
```

### Current Integration

Used in file upload processing (PDF, DOCX, etc.):
```python
content, metadata = await stream_thinking_while_processing(
    processing_status,
    process_uploaded_file,
    element.path, element.name,
    interval=0.35
)
```

### User Experience

**Before:**
```
📎 **document.pdf**
Processing...
[5 seconds of nothing]
Done!
```

**After:**
```
📎 **document.pdf**
Got it — reading through now...

*unpacking...* *digging in...* *what's the real job here...* *tracing patterns...*
*checking assumptions...* *where's the bottleneck...* *synthesizing...*
*interesting angle...* *coming together...*

✅ *Finished!* Lots to work with.
```

## Future Enhancements

### 1. Visual Styling (CSS)
Add distinct color styling like Claude Code's orange text:
```css
.thinking-token {
    color: #f59e0b;
    font-style: italic;
    opacity: 0.8;
}
```

### 2. Bot-Specific Vocabularies
Different bots could have themed thinking tokens:

| Bot | Example Tokens |
|-----|----------------|
| TTA | *trending forward...* *what breaks at scale...* *extrapolating...* |
| JTBD | *what job is this hiring...* *progress seeking...* *switching costs...* |
| Red Team | *finding weaknesses...* *attacking assumption...* *stress testing...* |
| Ackoff | *data check...* *climbing to wisdom...* *validating understanding...* |

### 3. Context-Aware Tokens
Select tokens based on what's being processed:
- PDF upload → "unpacking document...", "extracting insights..."
- Research query → "searching landscape...", "cross-referencing..."
- Synthesis → "connecting threads...", "crystallizing..."

### 4. Animated UI Component
Create a custom Chainlit element that renders thinking tokens with:
- Fade-in/fade-out animations
- Color variations
- Optional expand/collapse

### 5. Extended Thinking Integration
Connect to Gemini's thinking/reasoning mode to show actual model reasoning alongside PWS tokens.

## Technical Considerations

### Thread Safety
The blocking function runs in a ThreadPoolExecutor, isolated from the main asyncio loop. This prevents blocking the UI while heavy processing (PyPDF2, etc.) happens.

### Token Randomization
Tokens are sampled without replacement until exhausted, then the pool resets. This prevents repetitive sequences.

### Interval Tuning
- `0.35s` feels responsive for file processing
- `0.5s` might be better for longer operations
- Could be dynamic based on estimated processing time

## Files

- `mindrian_chat.py:556-640` - Core implementation
- `mindrian_chat.py:9287-9310` - File processing integration

## Status

**Implemented**: Basic thinking streamer for file uploads
**Future**: Bot-specific vocabularies, visual styling, animated component
