# Conversation Quality Scoring - Automated Assessment

## What Is This?

An automated system to evaluate the quality of AI responses and workshop conversations against PWS methodology standards.

## Why Implement This?

### Current Problem
- No way to automatically assess response quality
- Feedback is subjective (thumbs up/down)
- Can't identify patterns in poor responses
- No continuous improvement loop

### Solution: Quality Scoring Engine
Automatically score each response on PWS-specific criteria:
- Methodology adherence
- Problem clarity improvement
- Data grounding
- Assumption surfacing
- Actionable guidance

## Scoring Dimensions

### 1. PWS Methodology Score (0-100)
```python
PWS_CRITERIA = {
    "problem_before_solution": 25,  # Did we clarify problem first?
    "assumption_awareness": 20,     # Were assumptions surfaced?
    "data_grounding": 20,           # Is response grounded in evidence?
    "causal_chain": 15,             # Clear cause-effect reasoning?
    "actionable_guidance": 20,      # Did we provide next steps?
}
```

### 2. Larry Voice Score (0-100)
```python
VOICE_CRITERIA = {
    "socratic_method": 30,          # Asked probing questions?
    "no_premature_solutions": 25,   # Avoided jumping to solutions?
    "teaching_moments": 25,         # Explained PWS concepts?
    "warmth_and_encouragement": 20, # Supportive tone?
}
```

### 3. Workshop Progress Score (0-100)
```python
PROGRESS_CRITERIA = {
    "phase_appropriate": 30,        # Content fits current phase?
    "builds_on_prior": 25,          # References earlier discussion?
    "moves_forward": 25,            # Advances the workshop?
    "user_engagement": 20,          # User actively participating?
}
```

## Implementation Approaches

### Approach 1: LLM-Based Scoring (Recommended)
Use Gemini/GPT to evaluate responses:

```python
QUALITY_EVAL_PROMPT = """
Evaluate this AI response against PWS methodology standards.

CONTEXT:
- User question: {user_message}
- AI response: {ai_response}
- Current phase: {phase}
- Bot: {bot_name}

SCORE EACH DIMENSION (0-100):
1. Problem Clarity: Did the response help clarify the problem?
2. Assumption Awareness: Were underlying assumptions surfaced?
3. Data Grounding: Is the response grounded in evidence/data?
4. Methodology Adherence: Does it follow {bot_name}'s methodology?
5. Actionable Guidance: Are next steps clear?

OVERALL QUALITY: [0-100]
IMPROVEMENT SUGGESTIONS: [brief]
"""
```

### Approach 2: Rule-Based Scoring (Fast, Limited)
```python
def quick_quality_score(response: str, context: dict) -> int:
    score = 50  # Baseline

    # Positive signals
    if "?" in response:  # Contains questions
        score += 10
    if "assumption" in response.lower():
        score += 10
    if "evidence" in response.lower() or "data" in response.lower():
        score += 10

    # Negative signals
    if "you should" in response.lower():  # Premature advice
        score -= 15
    if len(response) < 100:  # Too short
        score -= 10

    return max(0, min(100, score))
```

### Approach 3: Trained Classifier (Best, Most Effort)
Fine-tune a model on labeled quality examples:
- Input: (user_message, ai_response, context)
- Output: Quality scores per dimension

## Usage Patterns

### Real-Time Scoring
```python
@cl.on_message
async def main(message):
    response = await generate_response(message)

    # Score before sending
    quality = await score_response(message.content, response, context)

    if quality.overall < 60:
        # Log for review, potentially regenerate
        log_low_quality_response(message, response, quality)

    await cl.Message(content=response).send()
```

### Batch Analysis
```python
# Analyze all conversations from past week
def analyze_conversation_quality(thread_id: str) -> QualityReport:
    messages = get_thread_messages(thread_id)
    scores = [score_message_pair(m) for m in messages]

    return QualityReport(
        average_score=mean(scores),
        low_score_count=len([s for s in scores if s < 60]),
        improvement_areas=identify_patterns(scores)
    )
```

## Dashboard Metrics

| Metric | Description |
|--------|-------------|
| Avg Quality Score | Mean score across all responses |
| % High Quality | Responses scoring 80+ |
| % Needs Review | Responses scoring <60 |
| By Bot | Quality breakdown by methodology |
| By Phase | Quality at each workshop stage |
| Improvement Trend | Score change over time |

## Files to Create

| File | Purpose |
|------|---------|
| `utils/quality_scorer.py` | Scoring engine |
| `utils/quality_dashboard.py` | Analytics and reporting |
| `prompts/quality_eval.py` | LLM evaluation prompts |

## Estimated Effort

- Rule-based scoring: 4-6 hours
- LLM-based scoring: 8-12 hours
- Trained classifier: 2-3 weeks
- Dashboard: 1 week

## Status

- [x] Research complete
- [ ] Define scoring criteria
- [ ] Implement basic scorer
- [ ] LLM evaluation integration
- [ ] Dashboard/analytics
