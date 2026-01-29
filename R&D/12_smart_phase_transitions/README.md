# Smart Phase Transitions

## Overview

Smart Phase Transitions enhance workshop bot UX by providing intelligent, context-aware guidance when users advance between phases. Instead of generic "Moving to Phase 2" messages, the system now validates completion, provides relevant context, and fetches real-world research.

## Problem Statement

### Before
- "Next Phase" button just updated internal counter
- No validation if user completed current phase
- No instructions on what to do next
- Generic messages with no context
- Phases lost when switching between bots

### After
- System validates phase completion using pattern extraction
- Shows what's missing if incomplete
- Provides smart transition with accumulated context
- Fetches relevant news and trends for the domain
- Phases persist across bot switches

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SMART PHASE TRANSITION                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User clicks "Next Phase"                                          │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Phase Validator │  ← LangExtract patterns                      │
│  │  (Completion %)  │                                              │
│  └────────┬─────────┘                                              │
│           │                                                         │
│     Score < 50%? ──Yes──▶ Show guidance + "Proceed Anyway"         │
│           │                                                         │
│          No                                                         │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Phase Enricher  │  ← Neo4j + NewsMesh + Google Trends          │
│  │  (Context)       │                                              │
│  └────────┬─────────┘                                              │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Smart Transition│  → Summary + Instructions + Research         │
│  │  Message         │                                              │
│  └──────────────────┘                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Enhanced Phase Definitions (`prompts/scenario_phases.py`)

Each phase includes:
- `name`: Display title
- `description`: What this phase accomplishes
- `instructions`: Clear steps for the user (list)
- `deliverables`: What "done" looks like (dict)
- `extraction_patterns`: Regex patterns for validation
- `neo4j_queries`: Cypher queries for context enrichment
- `completion_threshold`: Minimum score to auto-advance (0.0-1.0)
- `prompt`: Opening question to ask user

Example:
```python
"driving_forces": {
    "name": "Domain & Driving Forces",
    "description": "Map all forces that could reshape your domain using STEEP analysis.",
    "instructions": [
        "Brainstorm SOCIAL forces (demographics, culture, lifestyle shifts)",
        "Brainstorm TECHNOLOGICAL forces (innovation, automation, AI)",
        ...
    ],
    "deliverables": {
        "social_forces": "List of social/demographic forces",
        "technological_forces": "List of technology forces",
        ...
    },
    "extraction_patterns": {
        "social_forces": r"(?:social|demographic|cultural)[\s:]+([^\n.]{10,200})",
        ...
    },
    "completion_threshold": 0.5,
    "prompt": "Let's brainstorm driving forces. Start with SOCIAL forces..."
}
```

### 2. Phase Validator (`tools/phase_validator.py`)

Uses LangExtract-style regex patterns to extract deliverables from conversation history.

**Functions:**
- `validate_phase_completion(phase_config, history)` → (is_complete, score, extracted)
- `get_missing_deliverables(phase_config, extracted)` → List of missing items
- `generate_completion_guidance(phase_config, score, missing)` → Guidance message

**How it works:**
1. Combines last 12 messages into searchable text
2. Applies regex patterns for each deliverable
3. Falls back to keyword presence check
4. Returns completion score (0.0 - 1.0)

### 3. Phase Enricher (`tools/phase_enricher.py`)

Combines three data sources for context enrichment:

**Neo4j (LazyGraph):**
- Queries for relevant frameworks
- Fetches case studies
- Gets related concepts

**NewsMesh API:**
- Current news articles for user's domain
- Filtered by business/technology category
- Shows headlines during relevant phases

**Google Trends (SerpAPI):**
- Trend direction (rising/stable/declining)
- Rising related queries
- Interest over time data

**Functions:**
- `enrich_phase_context(phase_config, user_context)` → Neo4j enrichment
- `fetch_domain_news(domain, max_results)` → NewsMesh articles
- `fetch_domain_trends(domain, uncertainties)` → Google Trends data
- `enrich_phase_with_research(...)` → Combined enrichment
- `get_phase_transition_context(...)` → Full transition message

### 4. Updated Handler (`mindrian_chat.py`)

The `on_next_phase()` callback now:
1. Shows `cl.Step` for "Checking Phase Completion"
2. Validates using phase_validator
3. If incomplete: shows guidance + "Proceed Anyway" button
4. Shows `cl.Step` for "Preparing Next Phase"
5. Generates smart transition with enrichment
6. Syncs state to context_store for persistence

## Data Flow

```
User: "I want to explore healthcare in 2035"
                    │
                    ▼
         ┌─────────────────┐
         │ Phase 1: Intro  │
         │ extracted:      │
         │  - domain       │
         │  - focal_q      │
         │  - time_horizon │
         └────────┬────────┘
                  │
    User clicks "Next Phase"
                  │
                  ▼
         ┌─────────────────┐
         │ Validate: 85%   │
         │ ✓ domain        │
         │ ✓ focal_q       │
         │ ✓ time_horizon  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Enrich Phase 2  │
         │ Neo4j: STEEP    │
         │ News: 3 articles│
         │ Trends: Rising  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Smart Transition│
         │ - Summary       │
         │ - Instructions  │
         │ - Research      │
         │ - Prompt        │
         └─────────────────┘
```

## Configuration

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| NEO4J_URI | No | Neo4j connection for LazyGraph |
| NEO4J_USER | No | Neo4j username |
| NEO4J_PASSWORD | No | Neo4j password |
| NEWSMESH_API_KEY | No | NewsMesh news API |
| SERPAPI_API_KEY | No | Google Trends via SerpAPI |

All are optional - system degrades gracefully if not set.

### Which Phases Get Research

| Phase | News | Trends |
|-------|------|--------|
| Introduction | No | No |
| Driving Forces | Yes | Yes |
| Uncertainty Assessment | No | Yes |
| Scenario Matrix | No | No |
| Scenario Narratives | Yes | Yes |
| Synthesis | Yes | No |

## Extending to Other Bots

Currently implemented for Scenario Analysis. To add to other bots:

1. Create `prompts/{bot}_phases.py` with phase definitions
2. Update `on_next_phase()` to check for that bot_id
3. Add phase_context initialization in `on_chat_start()`

Example structure to copy:
```python
BOT_PHASES = {
    "phase_key": {
        "index": 0,
        "name": "Phase Name",
        "description": "What this phase does",
        "instructions": ["Step 1", "Step 2"],
        "deliverables": {"key": "description"},
        "extraction_patterns": {"key": r"pattern"},
        "completion_threshold": 0.6,
        "prompt": "Opening question?"
    }
}
```

## Files

| File | Purpose |
|------|---------|
| `prompts/scenario_phases.py` | Scenario Analysis phase definitions |
| `tools/phase_validator.py` | LangExtract completion validation |
| `tools/phase_enricher.py` | Neo4j + News + Trends enrichment |
| `mindrian_chat.py` | Updated on_next_phase handler |

## Related R&D

- `09_graphrag_lite/` - LazyGraph Neo4j integration
- `06_workshop_pipeline_engine/` - Workshop phase management
- `11_gemini_deep_research/` - Research tool patterns

## Future Improvements

1. **Auto-advance**: Automatically detect phase completion and prompt advancement
2. **Phase memory**: Remember insights across sessions via Supabase
3. **Cross-bot context**: Share extracted context between related bots
4. **Visualization**: Show phase completion as progress chart
5. **More bots**: Extend to TTA, JTBD, Ackoff, etc.
