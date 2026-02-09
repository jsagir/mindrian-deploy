# PWS Consultant

Structured problem diagnosis: classify challenges, get targeted framework guidance with domain-specific expert panels.

Read the full skill guide: `skills/pws-consultant/SKILL.md`

## 3-Phase Flow

1. **Describe Your Challenge** -- background intelligence begins (domain discovery, expert building)
2. **Problem Diagnostic** -- 5 questions classify problem type (Un-Defined / Ill-Defined / Well-Defined / Wicked)
3. **Guided Consulting** -- framework-guided conversation with expert panel

## Intelligence Pipeline

Each turn: `instant_extract()` -> `text_to_cypher()` -> `Neo4j` -> `cypher_to_text()` -> `FileSearch` -> `LLM context`

## Problem Types

| Type | Key Question | Frameworks |
|------|-------------|------------|
| Un-Defined | "What future are we creating?" | Scenario Planning, TTA, Beautiful Questions |
| Ill-Defined | "Who has this problem?" | JTBD, Process Mapping, User Journey |
| Well-Defined | "Is it Real? Can we Win?" | Validation Compass, Hypothesis Testing |
| Wicked | "Whose problem is this?" | Cynefin, BONO, Stakeholder Mapping |

## Expert Panel

Domain-specific experts built in background via BONO pipeline:
- Domain Insider, End-User Advocate, Skeptical Analyst, Cross-Domain Innovator, + problem-type expert

## Key Files

- Prompt: `prompts/pws_consultant.py`
- Pipeline: `tools/pws_consultant_pipeline.py`
- Components: `public/elements/DiagnosticFlow.jsx`, `DiagnosisResult.jsx`, `ExpertPanel.jsx`

$ARGUMENTS
