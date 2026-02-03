# Mindrian Codebase Map

> **Source**: `claude/review-codebase-nRTQ3` branch  
> **Last Verified**: 2026-02-01

## Table of Contents
1. [Directory Structure](#directory-structure)
2. [Core Files](#core-files)
3. [Bot System](#bot-system)
4. [Tools & Research](#tools--research)
5. [Governance & Safety](#governance--safety)
6. [UI Components](#ui-components)

---

## Directory Structure

```
mindrian-deploy/
├── mindrian_chat.py          # Main application (8686 lines)
├── prompts/                  # Bot system prompts (18 files)
│   ├── ackoff_workshop.py
│   ├── beautiful_question.py
│   ├── bono_hats.py
│   ├── domain_expert.py
│   ├── grading_agent.py
│   ├── jtbd_workshop.py
│   ├── known_unknowns.py
│   ├── larry_core.py
│   ├── minto_grading.py
│   ├── multi_perspective_validation.py
│   ├── problem_classifier.py
│   ├── pws_investment.py
│   ├── redteam.py
│   ├── research_domain_prompts.py
│   ├── scenario_analysis.py
│   ├── scenario_phases.py
│   ├── scurve_workshop.py
│   └── tta_workshop.py
├── tools/                    # Research and utility tools (31 files)
│   ├── graphrag_lite.py      # Neo4j integration
│   ├── graph_router.py       # Agent routing
│   ├── smart_phase_tracker.py
│   ├── research_orchestrator.py
│   ├── grading_workflow.py
│   ├── neo4j_framework_discovery.py
│   └── ... (see full list below)
├── governance/               # Safety and compliance
│   ├── ai_monitor.py
│   ├── risk_tiers.py
│   ├── audit_trail.py
│   ├── eval_suite.py
│   └── prompt_cards/         # 14 YAML prompt cards
├── utils/                    # Shared utilities (21 files)
│   ├── ui_elements.py
│   ├── context_extraction.py
│   ├── context_persistence.py
│   ├── data_layer.py
│   └── ...
├── public/                   # Frontend assets
│   └── elements/             # Custom React components
├── scripts/                  # Automation scripts
│   ├── health_check.py
│   └── daily_summary.py
├── qa/                       # QA sessions and guides
└── docs/                     # User documentation
```

---

## Core Files

### mindrian_chat.py (Main Application - 8686 lines)

| Section | Line Number | Purpose |
|---------|-------------|---------|
| `context_store` | **303** | Session context dictionary |
| `WORKSHOP_PHASES` | **428** | Phase tracking definitions |
| `BOTS` dict | **554** | Bot configuration and metadata |
| `get_core_action_buttons()` | **946** | Standard action buttons |
| `get_contextual_actions()` | **990** | Context-aware button logic |
| `@cl.on_chat_start` | **2314** | Session initialization |
| `@cl.on_message` | (after 2314) | Main message handler |
| `@cl.action_callback` | **2800+** | Button action handlers |
| `handle_agent_switch()` | **3581** | Bot switching logic |

### Key Functions

```python
# Context management (line 303)
context_store: Dict[str, Dict[str, Any]] = {}

# Core action buttons (line 946)
def get_core_action_buttons(include_example: bool = True) -> list:
    """Returns: Research, Synthesize, Think, Example buttons"""

# Bot switching (line 3581)
async def handle_agent_switch(new_agent_id: str):
    """Handles context preservation during bot switch"""

# Safe TaskList (line ~65)
async def safe_task_list_send(task_list):
    """Version-compatible TaskList.send() wrapper"""
```

---

## Bot System

### Complete BOTS Dictionary (line 554)

| Bot ID | Name | Model | Has Phases |
|--------|------|-------|------------|
| `lawrence` | Lawrence | gemini-2.5-flash-preview | No |
| `larry_playground` | Larry Playground | gemini-2.5-flash-preview | No |
| `tta` | Trending to the Absurd | gemini-2.5-pro-preview | Yes |
| `jtbd` | Jobs to Be Done | gemini-2.5-pro-preview | Yes |
| `scurve` | S-Curve Analysis | gemini-2.5-pro-preview | Yes |
| `redteam` | Red Teaming | gemini-2.5-pro-preview | Yes |
| `ackoff` | Ackoff's Pyramid (DIKW) | gemini-2.5-pro-preview | Yes |
| `pws_investment` | PWS Investment | gemini-2.5-pro-preview | Yes |
| `scenario` | Scenario Analysis | gemini-2.5-pro-preview | Yes |
| `validation` | Multi-Perspective Validation | gemini-2.5-pro-preview | Yes |
| `beautiful_question` | Beautiful Question | gemini-2.5-pro-preview | Yes |
| `grading` | Problem Discovery Grading | gemini-2.5-pro-preview | No |
| `domain` | Domain Expert | gemini-2.5-pro-preview | No |
| `knowns` | Known Unknowns | gemini-2.5-pro-preview | No |
| `bono` | Six Thinking Hats | gemini-2.5-pro-preview | Yes |

### Bot Prompt Files

| Bot | Prompt File |
|-----|-------------|
| Lawrence | `prompts/larry_core.py` |
| TTA | `prompts/tta_workshop.py` |
| JTBD | `prompts/jtbd_workshop.py` |
| S-Curve | `prompts/scurve_workshop.py` |
| Red Team | `prompts/redteam.py` |
| Ackoff | `prompts/ackoff_workshop.py` |
| PWS Investment | `prompts/pws_investment.py` |
| Scenario | `prompts/scenario_analysis.py` |
| Validation | `prompts/multi_perspective_validation.py` |
| Beautiful Question | `prompts/beautiful_question.py` |
| Grading | `prompts/grading_agent.py` |
| Domain | `prompts/domain_expert.py` |
| Knowns | `prompts/known_unknowns.py` |
| Bono | `prompts/bono_hats.py` |

---

## Tools & Research

### GraphRAG Lite (`tools/graphrag_lite.py`)

```python
# Key exports
from tools.graphrag_lite import enrich_for_larry, enrich_for_bot, should_retrieve

# Cache characteristics
_CACHE_TTL = 3600        # Refresh every hour
_NEO4J_TIMEOUT = 3.0     # Circuit breaker: 3s max
_MIN_COMMUNITY_SIZE = 5  # Exclude micro-communities
```

### Graph Router (`tools/graph_router.py`)

```python
from tools.graph_router import graph_score_agents, classify_and_route, has_problem_language
```

### Smart Phase Tracker (`tools/smart_phase_tracker.py`)

```python
from tools.smart_phase_tracker import (
    analyze_workshop_state,
    format_progress_indicator,
    should_show_advance_prompt,
    get_smart_phase_message,
    extract_phase_context
)
```

### Research Orchestrator (`tools/research_orchestrator.py`)

Coordinates multiple research sources:
- Tavily web search
- ArXiv academic papers
- Google Trends
- Government data APIs
- Patent search
- News search
- Dataset search

### Grading Workflow (`tools/grading_workflow.py`)

**Critical Rule**: MUST always display criteria WITH scores.

### All Tools Files

| File | Purpose |
|------|---------|
| `arxiv_search.py` | Academic paper search |
| `assessment_engine.py` | Assessment logic |
| `dataset_search.py` | Dataset discovery |
| `deep_research.py` | Deep research workflow |
| `govdata_search.py` | Government data APIs |
| `grading_workflow.py` | Grading with criteria |
| `graph_orchestrator.py` | Graph operations |
| `graph_router.py` | Agent routing |
| `graphrag_lite.py` | Neo4j integration |
| `langextract.py` | Context extraction |
| `neo4j_framework_discovery.py` | Framework lookup |
| `news_search.py` | News search |
| `opportunity_bank.py` | Opportunity tracking |
| `patent_search.py` | Patent search |
| `phase_enricher.py` | Phase context |
| `phase_validator.py` | Phase validation |
| `presentation_analyzer.py` | Presentation analysis |
| `problem_classifier.py` | Problem classification |
| `pws_brain.py` | PWS methodology |
| `research_cache.py` | Research caching |
| `research_orchestrator.py` | Research coordination |
| `result_synthesizer.py` | Result synthesis |
| `smart_phase_tracker.py` | LLM phase tracking |
| `tavily_search.py` | Web search |
| `tool_dispatcher.py` | Tool dispatch |
| `trends_search.py` | Google Trends |
| `validation_workflow.py` | Validation logic |

---

## Governance & Safety

### AI Monitor (`governance/ai_monitor.py`)

**Detection Patterns:**

```python
class MonitoringEvent(str, Enum):
    FORBIDDEN_ATTEMPT = "forbidden_attempt"
    BOUNDARY_VIOLATION = "boundary_violation"
    PROMPT_INJECTION = "prompt_injection"
    QUALITY_DEGRADATION = "quality_degradation"
    SAFETY_TRIGGER = "safety_trigger"
    HALLUCINATION_RISK = "hallucination_risk"
    DISCLAIMER_MISSING = "disclaimer_missing"
    UNUSUAL_PATTERN = "unusual_pattern"

# Prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|above)\s+instructions",
    r"disregard\s+(all|your)\s+(instructions|programming|training)",
    r"you\s+are\s+now\s+a?\s*(different|new)",
    # ... more patterns
]
```

### Prompt Cards (`governance/prompt_cards/`)

14 YAML files defining bot boundaries:
- `ackoff.yaml`
- `bono.yaml`
- `domain.yaml`
- `grading.yaml`
- `jtbd.yaml`
- `knowns.yaml`
- `larry_playground.yaml`
- `lawrence.yaml`
- `pws_investment.yaml`
- `redteam.yaml`
- `scenario.yaml`
- `scurve.yaml`
- `tta.yaml`

### Safety Enforcement Locations

| Rule | Where Enforced |
|------|----------------|
| Investment disclaimers | `prompts/pws_investment.py` |
| Grading criteria | `tools/grading_workflow.py` |
| Prompt injection | `governance/ai_monitor.py` |
| Risk tiers | `governance/risk_tiers.py` |
| Audit trail | `governance/audit_trail.py` |

---

## UI Components

### Action Buttons (`utils/ui_elements.py`)

```python
# Key functions
async def create_assessment_tasklist() -> cl.TaskList
async def update_task_status(task_list, task_name, status)
async def create_workshop_tasklist(phases: List[Dict]) -> cl.TaskList
def create_grade_reveal(grade, breakdown)
def create_score_breakdown(scores)
def create_opportunity_card(opportunity)
async def display_grading_results(results)
async def display_opportunities(opportunities)
```

### Core Action Buttons (line 946)

```python
def get_core_action_buttons(include_example: bool = True) -> list:
    return [
        cl.Action(name="deep_research", label="🔍 Research"),
        cl.Action(name="synthesize_conversation", label="📥 Synthesize"),
        cl.Action(name="think_through", label="🧠 Think"),
        cl.Action(name="show_example", label="📖 Example"),  # if include_example
    ]
```

### Chainlit Compatibility

```python
# Safe TaskList wrapper (handles version issues)
async def safe_task_list_send(task_list):
    try:
        await task_list.send()
    except TypeError as e:
        if "for_id" in str(e):
            pass  # Skip - version incompatibility
        else:
            raise
```

---

## Action Callback Reference

| Callback Name | Line | Purpose |
|---------------|------|---------|
| `detailed_feedback` | 2800 | Feedback collection |
| `rate_1` to `rate_5` | 2834-2838 | Rating buttons |
| `add_feedback_comment` | 2902 | Comment input |
| `multi_agent_analysis` | 2918 | Multi-agent trigger |
| `ma_quick/research/validate/full` | 2960-2972 | MA modes |
| `clear_context` | 3100 | Clear session |
| `form_submit` | 3128 | Form submission |
| `show_problem_form` | 3285 | Problem form |
| `show_scenario_form` | 3314 | Scenario form |
| `show_feedback_dashboard` | 3343 | Dashboard |
| `show_usage_metrics` | 3368 | Metrics |
| `generate_image` | 3384 | Image generation |
| `cancel_generation` | 3455 | Cancel image |
| `switch_to_*` | 3465-3576 | Bot switching |
| `handle_agent_switch` | 3581 | Switch handler |
| `show_example` | 3708 | Example display |
| `next_phase` | 3953 | Phase advance |
| `show_progress` | 4173 | Progress display |
| `help_start_phase` | 4282 | Phase help |
| `acknowledge_phase` | 4378 | Phase ack |
| `stay_phase` | 4393 | Stay in phase |
| `show_dikw_pyramid` | 4408 | DIKW display |
| `explore_dikw_level` | 4473 | DIKW explore |
| `show_scurve` | 4570 | S-Curve display |
