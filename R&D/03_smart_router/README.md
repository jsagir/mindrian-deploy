# Smart Router - Intent-Based Methodology Selection

## What Is This?

An intelligent routing system that analyzes user input and automatically suggests or activates the most relevant PWS methodology, rather than requiring manual bot selection.

## Why Implement This?

### Current Problem
- Users must manually select a bot from dropdown
- New users don't know which methodology fits their problem
- Mismatched bot selection leads to suboptimal guidance

### Solution: Smart Router
Analyze user's first message and:
1. Detect problem type and intent
2. Suggest best methodology
3. Optionally auto-activate relevant bot

## Current State (Partial Implementation)

We already have `AGENT_TRIGGERS` in `mindrian_chat.py`:

```python
AGENT_TRIGGERS = {
    "tta": {
        "keywords": ["trend", "future", "extrapolate", "absurd", "emerging"],
        "description": "Explore future trends"
    },
    "jtbd": {
        "keywords": ["customer", "hire", "job", "struggling", "switch"],
        "description": "Understand customer jobs"
    },
    # ... etc
}
```

This is used for **suggesting** agent switches during conversation, but not for initial routing.

## Enhanced Router Design

### Level 1: Keyword Matching (Current)
Fast, rule-based matching on trigger keywords.

### Level 2: LLM Classification (New)
Use Gemini to classify problem type:

```python
ROUTER_PROMPT = """
Analyze this user's problem and classify it:

USER INPUT: {user_message}

METHODOLOGIES:
1. LARRY (General) - Clarify the problem before chasing solutions
2. TTA (Trending to Absurd) - Extrapolate trends to find future problems
3. JTBD (Jobs to Be Done) - Understand what customers really need
4. S-CURVE - Analyze technology timing and adoption
5. RED_TEAM - Challenge assumptions and find weaknesses
6. ACKOFF (DIKW) - Validate solutions with data/evidence

Respond with:
- PRIMARY: [methodology name]
- CONFIDENCE: [0.0-1.0]
- REASONING: [one sentence]
- SECONDARY: [optional backup methodology]
"""
```

### Level 3: Multi-Methodology (Future)
Route to multiple methodologies in sequence:
- "I have a startup idea" → JTBD → S-CURVE → RED_TEAM

## Implementation Plan

### Step 1: Router Service
```python
# utils/router.py

class SmartRouter:
    def __init__(self):
        self.keyword_weights = load_keyword_weights()

    async def classify(self, user_message: str) -> RouterResult:
        # Level 1: Keyword scoring
        keyword_scores = self._keyword_score(user_message)

        # Level 2: LLM classification (if ambiguous)
        if max(keyword_scores.values()) < 0.7:
            llm_result = await self._llm_classify(user_message)
            return llm_result

        return RouterResult(
            primary=max(keyword_scores, key=keyword_scores.get),
            confidence=max(keyword_scores.values()),
            reasoning="Keyword match"
        )
```

### Step 2: Integration with Chat Start
```python
@cl.on_chat_start
async def on_chat_start():
    # Show router option
    await cl.Message(
        content="What problem are you working on?",
        actions=[
            cl.Action(name="auto_route", label="Help me choose a methodology"),
            cl.Action(name="manual_select", label="I'll pick my own")
        ]
    ).send()
```

### Step 3: Router UI Flow
1. User types problem description
2. Router analyzes and suggests methodology
3. User confirms or overrides
4. Session starts with selected bot

## Configuration

```python
ROUTER_CONFIG = {
    "auto_route_threshold": 0.85,  # Auto-select if confidence > 85%
    "suggest_threshold": 0.6,       # Suggest if confidence > 60%
    "use_llm_classification": True, # Enable Level 2
    "multi_methodology": False,     # Enable Level 3 (future)
}
```

## Files to Create/Modify

| File | Action |
|------|--------|
| `utils/router.py` | NEW - Smart router implementation |
| `mindrian_chat.py` | MODIFY - Add router to chat start |
| `prompts/router.py` | NEW - Router classification prompt |

## Estimated Effort

- Design: 2-3 hours
- Implementation: 6-8 hours
- Testing: 3-4 hours

## Status

- [x] Keyword triggers exist (partial)
- [ ] Router service design
- [ ] LLM classification integration
- [ ] UI flow implementation
- [ ] Testing with real users
