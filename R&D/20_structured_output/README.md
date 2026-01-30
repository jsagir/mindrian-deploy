# R&D 20: Structured Output Validation

## Status: Research

## What Is This?

Guaranteed schema compliance for LLM outputs, ensuring reliable structured data extraction.

## Why Implement This?

### Current State
- LLM outputs parsed with regex/json.loads
- Failures require manual retry
- No schema enforcement
- Grading/assessment need reliable structure

### Solution: Validated Outputs
- Define Pydantic models for expected outputs
- Automatic retry on validation failure
- Schema-guided generation
- Type-safe response handling

## Approaches

### 1. Instructor Library
```python
import instructor
from pydantic import BaseModel

class GradingResult(BaseModel):
    grade: str
    score: float
    components: list[ComponentScore]
    verdict: str
    evidence_count: int

client = instructor.from_openai(OpenAI())
result = client.chat.completions.create(
    model="gpt-4",
    response_model=GradingResult,
    messages=[{"role": "user", "content": prompt}]
)
# result is guaranteed to be GradingResult
```

### 2. Gemini Structured Output
```python
# Native Gemini structured output mode
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": GradingResult.model_json_schema()
    }
)
```

### 3. Retry with Correction
```python
@retry(max_attempts=3)
async def get_structured_output(prompt: str, schema: type[BaseModel]):
    response = await llm.generate(prompt)
    try:
        return schema.model_validate_json(response)
    except ValidationError as e:
        # Include error in retry prompt
        correction_prompt = f"""
        Previous output was invalid:
        {response}

        Validation errors:
        {e.errors()}

        Please fix and respond with valid JSON matching the schema.
        """
        return await get_structured_output(correction_prompt, schema)
```

## Use Cases in Mindrian

| Feature | Schema Needed |
|---------|---------------|
| Grading | GradingResult, ComponentScore, EvidenceItem |
| Research | ResearchResult, Source, Insight |
| Phase Transition | PhaseValidation, Deliverable |
| Assumption Extraction | Assumption, Challenge, Evidence |
| Opportunity Bank | Opportunity, Priority, Framework |

## Research Resources

- [Instructor](https://github.com/jxnl/instructor) - Structured outputs from LLMs
- [Outlines](https://github.com/outlines-dev/outlines) - Structured text generation
- [Marvin](https://github.com/prefecthq/marvin) - AI functions
- [Gemini Structured Output](https://ai.google.dev/gemini-api/docs/structured-output)

## Estimated Effort

- Design: 4-6 hours
- Implementation: 12-18 hours
- Testing: 6-10 hours

## Status Checklist

- [ ] Research Instructor/Outlines
- [ ] Define core Pydantic models
- [ ] Implement validation wrapper
- [ ] Add retry logic
- [ ] Migrate grading to structured output
- [ ] Migrate research to structured output
- [ ] Testing

---

*Created: 2026-01-30*
