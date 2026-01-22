# Synthetic Data Generation for PWS Training

## What Is This?

Use LLMs to generate high-quality training data from real workshop conversations, enabling fine-tuning of smaller, faster models specifically for PWS methodology.

## Why Implement This?

### Current Problem
- Responses can be slow (Gemini API latency)
- No domain-specific fine-tuning
- Quality varies based on generic model training

### Solution: PWS-Specific Training Data
1. Capture successful workshop conversations
2. Use GPT-4/Gemini to generate variations
3. Fine-tune smaller models (Llama, Mistral) on PWS methodology
4. Deploy locally or on edge for faster responses

## Research Sources

- **Meta Synthetic Data Kit**: https://github.com/meta-llama/synthetic-data-kit
- **Fine-tune SmolLM on Synthetic Data**: https://huggingface.co/blog/davidberenstein1957/fine-tune-a-smollm-on-synthetic-data-of-llm
- **LoRA Fine-Tuning Pipeline**: https://github.com/Vishalkagade/Efficient-LLM-Fine-Tuning-LoRA-Synthetic-Data-Pipeline
- **Best Practices for Synthetic Data**: https://community.databricks.com/t5/technical-blog/best-practices-for-using-synthetic-data-for-fine-tuning-ai/ba-p/122083

## Data Generation Pipeline

### Step 1: Capture Quality Conversations
```python
# Store conversations with positive feedback
def capture_quality_conversation(thread_id: str, feedback_score: int):
    if feedback_score >= 4:  # 4-5 stars
        conversation = get_full_thread(thread_id)
        save_to_training_corpus(conversation)
```

### Step 2: Generate Variations
```python
VARIATION_PROMPT = """
Given this successful PWS workshop conversation:
{conversation}

Generate 5 variations that:
1. Address similar problems from different industries
2. Use the same methodology with different user personas
3. Handle common objections or confusion points
4. Show recovery from misunderstandings
5. Demonstrate advanced methodology application

Each variation should maintain Larry's teaching style and PWS rigor.
"""
```

### Step 3: Quality Filter
```python
# Use another LLM to score generated data
QUALITY_PROMPT = """
Rate this training example (1-5) on:
- PWS methodology accuracy
- Pedagogical value
- Realistic user behavior
- Larry voice consistency
"""
```

### Step 4: Fine-Tune
```python
# Using QLoRA for efficient fine-tuning
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    task_type="CAUSAL_LM"
)
```

## Data Categories to Generate

| Category | Source | Examples Needed |
|----------|--------|-----------------|
| Problem Clarification | Larry conversations | 500+ |
| TTA Extrapolations | TTA workshops | 200+ |
| JTBD Discovery | JTBD workshops | 200+ |
| S-Curve Analysis | S-Curve workshops | 200+ |
| Ackoff DIKW Validation | Ackoff workshops | 300+ |
| Red Team Challenges | Red Team sessions | 200+ |
| Error Recovery | Failed attempts | 100+ |

## Implementation Plan

### Phase 1: Data Collection (2 weeks)
- Enable conversation export for quality sessions
- Build feedback → corpus pipeline
- Store in Supabase with metadata

### Phase 2: Variation Generation (1 week)
- Create variation prompts per methodology
- Run batch generation with GPT-4
- Quality filter with automated scoring

### Phase 3: Fine-Tuning (2 weeks)
- Select base model (Mistral 7B or Llama 3.2 3B)
- Configure QLoRA training
- Train and evaluate

### Phase 4: Deployment (1 week)
- Host fine-tuned model (Ollama local or cloud)
- A/B test against base Gemini
- Measure latency and quality

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/export_quality_conversations.py` | Export positively-rated conversations |
| `scripts/generate_variations.py` | Create synthetic training data |
| `scripts/quality_filter.py` | Score and filter generated data |
| `scripts/finetune_pws_model.py` | LoRA fine-tuning script |

## Estimated Effort

- Data collection: 2 weeks (ongoing)
- Variation generation: 1 week
- Fine-tuning: 2 weeks
- Evaluation: 1 week

## Status

- [x] Research complete
- [ ] Data collection pipeline
- [ ] Variation generation
- [ ] Quality filtering
- [ ] Fine-tuning
- [ ] Deployment
