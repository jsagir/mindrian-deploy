---
description: Deep intent understanding using conversation context and LazyGraph patterns
---

# Step 3: Deep Intent Understanding

## Goal
Make Lawrence understand user intent at a deeper level by combining conversation signals with LazyGraph patterns — so the bot responds to what the user MEANS, not just what they SAID.

## Current State
- Basic keyword matching for agent triggers
- GraphRAG provides concept-level context
- No intent history tracking across sessions
- No pattern recognition ("this user always asks about X after Y")

## What to Build

### 1. Intent Analyzer (`intelligence/intent_analyzer.py`)
- Classify user intent into categories: explore, validate, decide, learn, create, compare
- Track intent transitions across the conversation (explore → validate → decide)
- Use conversation history + GraphRAG context for classification
- Store intent patterns in Neo4j for cross-session learning

### 2. LazyGraph Intent Patterns
- Create `IntentPattern` nodes in Neo4j
- Track: which intents follow which, what tools were useful at each stage
- Use patterns to predict next likely intent and pre-prepare context
- Example: "Users who explore vertical farming usually validate market size next"

### 3. Proactive Context Loading
- Based on predicted intent, pre-load relevant:
  - GraphRAG concepts and frameworks
  - Previous research on the topic
  - Related case studies
- Inject pre-loaded context before the user even asks

## Files to Create/Modify

| Action | File | Changes |
|--------|------|---------|
| CREATE | `intelligence/intent_analyzer.py` | Intent classification + pattern tracking |
| MODIFY | `tools/user_lazygraph.py` | Add IntentPattern node type |
| MODIFY | `tools/graphrag_lite.py` | Add intent-aware enrichment |
| MODIFY | `mindrian_chat.py` | Add intent analysis in message flow |

## Acceptance Criteria
- [ ] Intent classified for each user message
- [ ] Intent patterns stored in Neo4j
- [ ] Proactive context loading based on predicted intent
- [ ] Response quality improves measurably (fewer irrelevant suggestions)

## Validation
```bash
python3 -c "import ast; ast.parse(open('intelligence/intent_analyzer.py').read())"
python3 scripts/health_check.py
```
