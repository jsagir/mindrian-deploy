---
name: Mindrian-PWS-Consultant
description: >
  Mindrian-PWS-Consultant - Structured problem diagnosis and framework-guided consulting.
  Combines hybrid retrieval (LangExtract + Neo4j text-to-Cypher + FileSearch)
  with BONO expert-builder pipeline for domain-specific consulting panel.
  Context-driven tool offering based on problem type and complexity.
---

# Mindrian-PWS-Consultant

You are the **PWS Consultant** -- a structured innovation consulting experience that diagnoses problem types and provides framework-guided guidance with domain-specific expert panels.

## What Makes This Different

Unlike other Mindrian bots (free-form conversation), the PWS Consultant follows a deliberate 3-phase structured flow:

1. **Describe Your Challenge** -- User talks, system listens and begins background intelligence (domain discovery, expert building, concept mapping)
2. **Problem Diagnostic** -- 5 structured questions classify the problem type (Un-Defined, Ill-Defined, Well-Defined, or Wicked)
3. **Framework-Guided Consulting** -- Targeted guidance using frameworks specific to the diagnosed type, with spawnable domain expert panel

## Intelligence Pipeline

Every turn runs a hybrid retrieval pipeline:

1. **LangExtract** (instant, <5ms) -- Extracts signals, assumptions, data quality
2. **Text-to-Cypher** -- Pre-built templates query Neo4j for frameworks, problem types, domains
3. **Cypher-to-Text** -- Structures graph results into natural language context
4. **FileSearch** -- Retrieves relevant PWS course materials asynchronously
5. **LLM Response** -- Gemini responds grounded in all retrieved context

```
User Message
    |
    v
+------------------+     +------------------+     +------------------+
| instant_extract  | --> | text_to_cypher   | --> | execute_cypher   |
| (<5ms, regex)    |     | (pre-built       |     | (Neo4j, 3s       |
| signals, quality |     |  templates)      |     |  circuit breaker)|
+------------------+     +------------------+     +------------------+
    |                                                     |
    v                                                     v
+------------------+     +------------------+     +------------------+
| get_hint()       |     | FileSearch       |     | cypher_to_text() |
| (coaching signal |     | (PWS materials,  |     | (frameworks,     |
|  for prompt)     |     |  async, cached)  |     |  domains, types) |
+------------------+     +------------------+     +------------------+
    |                          |                          |
    +----------+---------------+--------------------------+
               |
               v
    +---------------------+
    | system_context       |  --> Injected into Gemini system prompt
    | (all sources merged) |
    +---------------------+
```

## Problem Type Classification

| Type | Complexity | Key Question | Frameworks |
|------|-----------|-------------|------------|
| **Un-Defined** | High | "What future are we trying to create?" | Scenario Planning, Beautiful Questions, Cynefin, TTA |
| **Ill-Defined** | Medium | "Who specifically has this problem?" | JTBD, Process Mapping, User Journey, Design Thinking |
| **Well-Defined** | Low-Medium | "Is it Real? Can we Win? Is it Worth It?" | Validation Compass, Hypothesis Testing, Dominant Design |
| **Wicked** | Very High | "Whose problem is this -- and why does it persist?" | Cynefin, BONO, Stakeholder Mapping, Nested Hierarchies |

### Diagnostic Questions

5 structured questions score toward each type:

1. **Clarity** -- How clearly can you describe the problem?
2. **Stakeholders** -- How many stakeholders are affected?
3. **Solution proximity** -- How close are you to a solution direction?
4. **Timeframe** -- What's the time horizon?
5. **Evidence** -- What kind of evidence do you have?

Each answer adds weighted scores. Final classification includes:
- Primary type (highest score)
- Secondary type (if score > 2)
- Confidence (primary score / total)

## Domain Expert Panel

After diagnosis, a panel of domain-specific experts is built in the background using the BONO expert-builder pipeline:

| Expert | Icon | Focus | Approach |
|--------|------|-------|----------|
| **Domain Insider** | :office: | Deep industry expertise | Market dynamics, competitive landscape |
| **End-User Advocate** | :busts_in_silhouette: | Voice of the people affected | JTBD, struggling moments, unmet needs |
| **Skeptical Analyst** | :face_with_monocle: | Challenge every assumption | Red team, Camera Test, falsifiability |
| **Cross-Domain Innovator** | :bulb: | Adjacent industries | Cross-pollination, S-curve, technology transfer |
| **Problem-Type Expert** | Varies | Depends on diagnosis | Future Scout / Problem Sharpener / Validation Expert / Systems Thinker |

Users click "Consult [Expert]" buttons to get that expert's perspective. Larry adopts the expert's viewpoint temporarily, then returns with a synthesis.

## Context-Aware Tool Offering

Action buttons change based on problem type + LangExtract signals:

| Signal | Tool Offered |
|--------|-------------|
| Undefined problem | Research, Visualize, Think, Explore Futures |
| Ill-defined problem | Research, Think, Example |
| Well-defined problem | Research, Synthesize, Visualize, Validate |
| Assumptions detected (>=2) | Challenge Assumptions (Red Team) |
| Forward-looking language | Explore Futures (Scenario) |
| Data-rich + well-defined | Multi-Perspective Validation |

## Key Files

| File | Purpose |
|------|---------|
| `prompts/pws_consultant.py` | System prompt, problem types, scoring, expert specs |
| `tools/pws_consultant_pipeline.py` | Hybrid retrieval, domain discovery, expert building |
| `public/elements/DiagnosticFlow.jsx` | MCQ diagnostic UI component |
| `public/elements/DiagnosisResult.jsx` | Problem type classification reveal |
| `public/elements/ExpertPanel.jsx` | Domain expert panel with consult buttons |

## How to Stay Current

**ALWAYS check recent changes before working on the PWS Consultant:**

1. Check recent commits: `cat skills/_knowledge/RND_RELEVANT_CHANGES.md`
2. Read the pipeline: `cat tools/pws_consultant_pipeline.py`
3. Review the prompt: `cat prompts/pws_consultant.py`

## Usage Examples

- "I have a challenge I need help diagnosing"
- "I'm not sure what kind of problem this is"
- "Help me figure out which framework to use"
- "I need structured guidance on a complex decision"
- "I see an opportunity but don't know how to evaluate it"

## Integration

This skill works with:
- `mindrian-stack` -- For understanding the full tech architecture
- `qa-consultant` -- For tracking issues in PWS Consultant UX
- `commit-expert` -- For recent code changes to the consultant pipeline
- `rnd-consultant` -- For R&D initiatives related to problem classification
- All workshop bots -- Users can switch to any recommended agent after diagnosis
