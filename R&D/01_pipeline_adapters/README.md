# Pipeline Adapters - Modular Methodology Enhancement

## What Is This?

Inspired by the **GIA-LLM** project and **LLM-Adapters** framework, this pattern allows adding specific capabilities to a base model (Larry) without switching entire system prompts.

## Why Implement This?

### Current Problem
- Each bot (Larry, TTA, JTBD, etc.) has a completely separate system prompt
- Switching bots loses context nuance
- No way to combine methodologies (e.g., TTA + Red Teaming)

### Solution: Adapter Pattern
Instead of switching bots, we **enhance Larry** with methodology-specific adapters:

```python
# Conceptual Design
class MethodologyAdapter:
    def enhance_prompt(self, base_prompt: str) -> str:
        """Add methodology-specific instructions"""
        pass

    def post_process(self, response: str) -> str:
        """Apply methodology-specific formatting"""
        pass

class TrendingToAbsurdAdapter(MethodologyAdapter):
    def enhance_prompt(self, base_prompt: str) -> str:
        return base_prompt + """

        ACTIVE METHODOLOGY: Trending to the Absurd
        - Extrapolate current trends 10-20 years forward
        - Push implications to absurd but logical conclusions
        - Identify problems that emerge from extrapolation
        """
```

## Benefits

1. **Composable**: Combine TTA + Red Teaming for "challenge my extrapolations"
2. **Context Preservation**: Larry's base reasoning stays intact
3. **Lighter Weight**: Small prompt additions vs. full system prompt switches
4. **Easier Maintenance**: Update one adapter without touching others

## Research Sources

- **GIA-LLM**: https://gia-llm.readthedocs.io/en/latest/Documentation/scripts/1_Pipeline.html
- **LLM-Adapters (EMNLP 2023)**: https://github.com/AGI-Edgerunners/LLM-Adapters
- Paper: "LLM-Adapters: An Adapter Family for Parameter-Efficient Fine-Tuning"

## Implementation Plan

### Step 1: Design Adapter Interface
```python
# utils/adapters.py
from abc import ABC, abstractmethod

class MethodologyAdapter(ABC):
    name: str
    description: str
    keywords: list[str]

    @abstractmethod
    def enhance_system_prompt(self, base: str, context: dict) -> str:
        pass

    @abstractmethod
    def enhance_user_message(self, message: str, phase: int) -> str:
        pass

    def get_phase_instructions(self, phase: int) -> str:
        return ""
```

### Step 2: Create Adapters for Each Methodology
- `TTAAdapter` - Trend extrapolation instructions
- `JTBDAdapter` - Customer job discovery prompts
- `SCurveAdapter` - Technology timing analysis
- `AckoffAdapter` - DIKW pyramid guidance
- `RedTeamAdapter` - Assumption challenge mode

### Step 3: Modify Message Handler
```python
@cl.on_message
async def main(message):
    # Get active adapters from session
    adapters = cl.user_session.get("active_adapters", [])

    # Enhance base Larry prompt with adapters
    enhanced_prompt = LARRY_BASE_PROMPT
    for adapter in adapters:
        enhanced_prompt = adapter.enhance_system_prompt(enhanced_prompt, context)
```

### Step 4: Add Adapter Toggle UI
Allow users to activate/deactivate methodology adapters without full bot switch.

## Files to Create/Modify

| File | Action |
|------|--------|
| `utils/adapters.py` | NEW - Adapter base class and implementations |
| `mindrian_chat.py` | MODIFY - Add adapter support to message handler |
| `.chainlit/config.toml` | MODIFY - Add adapter toggle settings |

## Estimated Effort

- Design: 2-4 hours
- Implementation: 8-12 hours
- Testing: 4-6 hours

## Status

- [x] Research complete
- [ ] Design document
- [ ] Implementation
- [ ] Testing
- [ ] Documentation
