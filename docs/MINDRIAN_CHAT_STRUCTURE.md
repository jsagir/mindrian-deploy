# Mindrian Chat Structure Analysis

**File:** `mindrian_chat.py`
**Lines:** 10,828
**Last Updated:** 2026-02-04

---

## Overview

This monolithic file contains the entire Chainlit application. It handles:
- Bot configurations and system prompts
- Chat lifecycle (start, resume, stop)
- Message processing and streaming
- 50+ action callbacks
- Research tools and pipelines
- Audio/voice handling
- Grading system
- Analytics and feedback

---

## TOPIC 1: Imports & Configuration (Lines 1-700)

### 1.1 Core Imports (1-50)
- Standard library imports
- Chainlit imports
- Environment setup

### 1.2 Feature Toggles (47-200)
| Feature | Lines | Purpose |
|---------|-------|---------|
| Triple-Mode Architecture | 24-45 | Defines bot modes |
| Cron API Endpoint | 47-100 | Daily summary middleware |
| GraphRAG Lite | 102-110 | Context enrichment |
| Smart Phase Tracker | 112-125 | LLM-based phase detection |
| Phase Insights | 127-143 | User-facing intelligence |
| Recursive Intelligence | 145-165 | Session logging |
| Reaction Classifier | 166-176 | Sentiment detection |
| Session Distiller | 178-188 | End-session insights |
| Self-Describing Phases | 189-200 | Auto-discovery |

### 1.3 UI Element Imports (205-268)
- Custom components: WorkshopRoadmap, DIKWPyramid, etc.
- Grading elements: GradeReveal, ScoreBreakdown
- Pipeline elements

### 1.4 LangGraph Pipeline Imports (224-268)
```python
from intelligence.pipelines import (
    run_bono_session, format_bono_report,
    run_reverse_salient, format_reverse_salient_result,
    run_domain_discovery, format_domain_discovery_result,
    run_oracle_formulation, run_oracle_resolution,
    run_grading_pipeline,
    run_minto_pipeline, format_minto_result,
)
```

### 1.5 Global Config (333-443)
- API key diagnostics (344-367)
- OAuth authentication setup (369-443)
- Stop event management (444-446)

---

## TOPIC 2: UI Helpers & Extended Thinking (Lines 447-700)

### 2.1 Extended Thinking UI (450-558)
| Function | Lines | Purpose |
|----------|-------|---------|
| `show_thinking_panel()` | 450-493 | Display ThinkingPanel element |
| `capture_reasoning_steps()` | 494-558 | Extract reasoning from response |

### 2.2 Context Preservation (559-579)
- `context_store = {}` - In-memory context cache
- Cross-bot conversation persistence

### 2.3 Topic-Aware Threading (580-636)
- Thread naming by topic
- Agent suggestion keywords (`AGENT_TRIGGERS`)

### 2.4 Data Persistence Setup (637-692)
- Supabase/PostgreSQL data layer
- Native feedback system integration

### 2.5 System Prompts Import (660-692)
- Import all workshop prompts
- Fallback definitions

### 2.6 RAG Cache Support (693-706)
- Gemini file search setup
- Knowledge base integration

---

## TOPIC 3: Workshop Phase System (Lines 707-1210)

### 3.1 Phase Definitions (707-839)
```python
WORKSHOP_PHASES = {
    "tta": [...],
    "jtbd": [...],
    "scurve": [...],
    "redteam": [...],
    "ackoff": [...],
    # etc.
}
```

### 3.2 Bot Configurations (840-1210)
```python
BOTS = {
    "lawrence": {...},
    "larry_playground": {...},
    "tta": {...},
    "jtbd": {...},
    "scurve": {...},
    "redteam": {...},
    "ackoff": {...},
    "bono": {...},
    "knowns": {...},
    "nested_hierarchies": {...},
    "domain": {...},
    "investment": {...},
    "scenario": {...},
    "validation": {...},
    "beautiful_question": {...},
    "grading": {...},
}
```

---

## TOPIC 4: Phase & Navigation Helpers (Lines 1211-1756)

### 4.1 Phase Discovery (1211-1228)
- `_get_phases_for_bot()` - Auto-discover phases from prompts

### 4.2 Workshop Roadmap (1229-1310)
- `create_workshop_roadmap()` - Create roadmap element
- `get_core_action_buttons()` - Standard action buttons

### 4.3 Pipeline Buttons (1311-1369)
```python
def get_pipeline_buttons(bot_id: str) -> list:
    pipeline_buttons = {
        "bono": [BONO buttons],
        "nested_hierarchies": [RS buttons],
        "domain": [Domain buttons],
        "scenario": [Oracle buttons],
        "tta": [Oracle buttons],
        "validation": [BONO buttons],
    }
```

### 4.4 Phase Navigation (1370-1490)
- `get_phase_navigation_buttons()` - Prev/Next buttons
- `create_or_update_roadmap()` - Update roadmap state
- `on_jump_to_phase()` - Jump to specific phase

### 4.5 Contextual Actions (1563-1734)
- `get_contextual_actions()` - Dynamic button suggestions
- `send_phase_transition_card()` - Phase change UI

### 4.6 Phase Update Logic (1735-1756)
- `update_phase()` - Mark phases complete

---

## TOPIC 5: Custom Elements & Visualization (Lines 1757-1930)

### 5.1 Phase Progress Element (1761-1785)
- Visual progress indicator

### 5.2 DIKW Pyramid Element (1786-1806)
- `show_dikw_pyramid_element()` - Ackoff pyramid chart

### 5.3 Research Matrix Element (1807-1827)
- `show_research_matrix_element()` - Research planning UI

### 5.4 Workshop Sidebar (1832-1930)
- `setup_workshop_sidebar()` - ElementSidebar configuration
- `update_sidebar_phase()` - Update sidebar state

---

## TOPIC 6: Chat Profiles & Starters (Lines 1931-2388)

### 6.1 Chat Profiles (1931-2023)
```python
@cl.set_chat_profiles
async def chat_profiles():
    return [
        cl.ChatProfile(name="lawrence", ...),
        cl.ChatProfile(name="larry_playground", ...),
        cl.ChatProfile(name="tta", ...),
        # 16+ profiles total
    ]
```

### 6.2 Conversation Starters (2024-2380)
```python
STARTERS = {
    "lawrence": [4 starters],
    "larry_playground": [4 starters],
    "tta": [4 starters],
    # Per-bot starters
}
```

---

## TOPIC 7: Settings & Agent Suggestions (Lines 2388-2901)

### 7.1 Settings Update Handler (2389-2409)
- `@cl.on_settings_update` - Handle settings changes

### 7.2 Settings Widgets (2410-2444)
- Response detail slider
- Research depth selector
- Feature toggles

### 7.3 Agent Suggestion System (2445-2832)
| Function | Lines | Purpose |
|----------|-------|---------|
| `suggest_agents_from_context()` | 2445-2632 | Keyword-based suggestions |
| `suggest_research_tools()` | 2633-2832 | Context-aware research buttons |

### 7.4 AI Agent Suggestion (2833-2884)
- `get_ai_agent_suggestion()` - LLM-based agent recommendation

### 7.5 Context Key Helper (2885-2901)
- `get_context_key()` - Generate unique context identifier

---

## TOPIC 8: Chat Lifecycle Handlers (Lines 2902-3378)

### 8.1 Chat Start (2902-3271)
```python
@cl.on_chat_start
async def start():
    # 1. Context preservation check
    # 2. Session initialization
    # 3. Settings setup
    # 4. Phase initialization
    # 5. Action buttons
    # 6. Welcome message
```

### 8.2 Chat Resume (3272-3360)
```python
@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    # Restore conversation from database
```

### 8.3 Stop Handler (3361-3377)
```python
@cl.on_stop
async def on_stop():
    # Handle cancellation
```

---

## TOPIC 9: Feedback System (Lines 3378-3565)

### 9.1 Native Feedback Handler (3378-3448)
```python
@cl.on_feedback
async def on_feedback(feedback):
    # Store thumbs up/down
```

### 9.2 Detailed Feedback (3449-3550)
- `on_detailed_feedback()` - Extended feedback form
- `on_rate_1/2/3/4/5()` - Star rating handlers

### 9.3 Feedback Comments (3551-3565)
- `on_add_feedback_comment()` - Add text feedback

---

## TOPIC 10: Multi-Agent Analysis (Lines 3567-3748)

### 10.1 Multi-Agent Launch (3567-3625)
- `on_multi_agent_analysis()` - Show analysis type selector
- `on_ma_quick/research/validate/full()` - Type handlers

### 10.2 Multi-Agent Execution (3626-3748)
- `run_multi_agent_with_type()` - Execute agent pipeline
- Background agent orchestration

---

## TOPIC 11: Form Handlers (Lines 3749-3991)

### 11.1 Clear Context (3749-3776)
- `on_clear_context()` - Reset conversation history

### 11.2 Form Submit Router (3777-3933)
- `on_form_submit()` - Route form submissions
- `handle_scenario_setup_form()` - Scenario form
- `handle_problem_definition_form()` - Problem form

### 11.3 Form Display (3934-3991)
- `on_show_problem_form()` - ProblemDefinitionForm element
- `on_show_scenario_form()` - ScenarioSetupForm element

---

## TOPIC 12: Analytics & Dashboard (Lines 3992-4113)

### 12.1 Feedback Dashboard (3992-4016)
- `on_show_feedback_dashboard()` - Analytics view

### 12.2 Usage Metrics (4017-4032)
- `on_show_usage_metrics()` - Usage statistics

### 12.3 Image Generation (4033-4103)
- `on_generate_image()` - Gemini Imagen integration

### 12.4 Cancel Generation (4104-4113)
- `on_cancel_generation()` - Stop image generation

---

## TOPIC 13: Agent Switching (Lines 4114-4437)

### 13.1 Switch Callbacks (4114-4241)
```python
@cl.action_callback("switch_to_tta")
@cl.action_callback("switch_to_jtbd")
@cl.action_callback("switch_to_scurve")
@cl.action_callback("switch_to_redteam")
@cl.action_callback("switch_to_ackoff")
@cl.action_callback("switch_to_larry")
@cl.action_callback("switch_to_bono")
@cl.action_callback("switch_to_knowns")
@cl.action_callback("switch_to_nested_hierarchies")
@cl.action_callback("switch_to_domain")
@cl.action_callback("switch_to_investment")
@cl.action_callback("switch_to_scenario")
@cl.action_callback("switch_to_validation")
@cl.action_callback("switch_to_beautiful_question")
```

### 13.2 Entry Point Selection (4242-4272)
- `on_select_entry_point()` - Bot selection
- `on_mode_or_stage()` - Mode selection
- `on_grounding_response()` - Grounding handler

### 13.3 Agent Switch Handler (4273-4437)
- `handle_agent_switch()` - Core switch logic with context preservation

---

## TOPIC 14: Workshop Phase Callbacks (Lines 4438-5687)

### 14.1 Show Example (4438-4683)
- `on_show_example()` - Display methodology examples
- `_show_fallback_example()` - Fallback static examples

### 14.2 Next/Prev Phase (4684-4985)
- `on_next_phase()` - Advance to next phase
- `on_prev_phase()` - Return to previous phase

### 14.3 Phase Exploration (4986-5133)
- `on_explore_gaps()` - Explore missing elements
- `on_explore_more()` - Continue in current phase
- `on_show_full_progress()` - Detailed progress view

### 14.4 Journal & Summary (5134-5268)
- `on_summarize_journal()` - Summarize conversation
- `on_view_full_journal()` - Full journal view

### 14.5 Progress Display (5269-5495)
- `on_show_progress()` - Show progress card
- `on_help_start_phase()` - Phase help
- `on_acknowledge_phase()` - Acknowledge completion
- `on_stay_phase()` - Stay in current phase

### 14.6 DIKW Pyramid (5496-5687)
- `on_show_dikw_pyramid()` - Show Ackoff pyramid
- `on_explore_dikw_level()` - Explore specific level

---

## TOPIC 15: Media Callbacks (Lines 5688-5928)

### 15.1 Watch Video (5688-5755)
- `on_watch_video()` - Play workshop video

### 15.2 Listen Audiobook (5756-5898)
- `on_listen_audiobook()` - Play audio chapter
- `play_chapter_*` callbacks (18 total) - Per-chapter handlers

### 15.3 Export Summary (5899-5927)
- `on_export_summary()` - Download workshop summary

---

## TOPIC 16: Synthesis & Insights (Lines 5929-6250)

### 16.1 Synthesize Conversation (5929-6050)
- `on_synthesize_conversation()` - Larry synthesizes full conversation

### 16.2 Voice Chat (6051-6092)
- `on_start_voice_chat()` - Launch real-time voice

### 16.3 Extract Insights (6093-6214)
- `on_extract_insights()` - LangExtract structured extraction

### 16.4 Speak Response (6215-6250)
- `on_speak_response()` - TTS for response

### 16.5 Map Ideas (6251-6775)
- `on_map_ideas()` - Generate Mermaid mindmaps

---

## TOPIC 17: Research Tools (Lines 6776-7729)

### 17.1 Deep Research (6776-7240)
| Callback | Lines | Purpose |
|----------|-------|---------|
| `deep_research_full` | 6776-6790 | Full Minto pipeline |
| `deep_research` | 6791-7240 | Tavily web search |

### 17.2 Specialized Research (7241-7518)
| Callback | Lines | Purpose |
|----------|-------|---------|
| `arxiv_search` | 7241-7278 | Academic papers |
| `patent_search` | 7279-7316 | Patents |
| `trends_search` | 7317-7364 | Google Trends |
| `govdata_search` | 7365-7420 | Government data |
| `dataset_search` | 7421-7463 | Datasets |
| `news_search` | 7464-7518 | News articles |

### 17.3 Gemini Deep Research (7519-7729)
- `on_gemini_deep_research()` - Gemini-powered research

---

## TOPIC 18: Think Through (Lines 7730-7857)

### 18.1 Sequential Thinking (7730-7857)
- `on_think_through()` - Structured analysis with ThinkingPanel

---

## TOPIC 19: Main Message Handler (Lines 7858-9132)

### 19.1 Message Processing (7858-9132)
```python
@cl.on_message
async def main(message: cl.Message):
    # 1. File attachment processing
    # 2. Context enrichment (GraphRAG)
    # 3. Agent suggestion check
    # 4. Research tool suggestions
    # 5. Message routing (grading vs regular)
    # 6. Gemini response generation
    # 7. Response streaming
    # 8. Phase progression check
    # 9. Action button refresh
```

**Key Subsections:**
- File processing (7900-8000)
- Context handoff (8573-8600)
- Research query generation (8200-8400)
- Phase insight check (8700-8800)
- Response streaming (8500-8900)

---

## TOPIC 20: Audio/Voice Handlers (Lines 9133-9613)

### 20.1 Audio Start (9136-9203)
```python
@cl.on_audio_start
async def on_audio_start():
    # Initialize audio session
```

### 20.2 Audio Chunk (9204-9431)
```python
@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    # Process incoming audio
```

### 20.3 Audio End (9432-9516)
```python
@cl.on_audio_end
async def on_audio_end(elements: list):
    # Finalize transcription
```

### 20.4 File Upload Processing (9517-9613)
- Uploaded file handling

---

## TOPIC 21: Domain Discovery (Lines 9614-10029)

### 21.1 CV Analysis (9614-9753)
- `on_analyze_cv()` - Extract domains from CV

### 21.2 Research Analysis (9754-9770)
- `on_analyze_research()` - Extract from research paper

### 21.3 Question Exploration (9771-9962)
- `on_explore_question()` - Domain discovery from question

### 21.4 Domain Deep Dive (9963-10029)
- `on_domain_deep_dive()` - Detailed domain exploration

---

## TOPIC 22: Grading System (Lines 10030-10610)

### 22.1 Grade Student Work (10034-10067)
- `on_grade_student_work()` - Main grading entry
- `on_quick_grade()` - Fast grading mode

### 22.2 Grade Discussion (10068-10169)
- `on_discuss_grade()` - Discuss grading with AI

### 22.3 Report Views (10170-10234)
- `on_show_full_report()` - Full grading report
- `on_view_full_report()` - Alternative view
- `on_view_evidence()` - View grading evidence

### 22.4 Component Discussion (10235-10274)
- `on_discuss_component()` - Discuss specific component

### 22.5 Opportunities (10275-10542)
- `on_remove_opportunity()` - Remove from bank
- `on_view_opportunities()` - View opportunity bank
- `on_explore_opportunity()` - Explore opportunity

### 22.6 Export & Explain (10543-10610)
- `on_export_grading_json()` - Export as JSON
- `on_explain_grade()` - Explain grading rationale

---

## TOPIC 23: LangGraph Pipelines (Lines 10611-10828)

### 23.1 BONO Six Hats (10615-10679)
- `on_run_bono_analysis()` - Run Six Thinking Hats pipeline

### 23.2 Reverse Salient Discovery (10680-10738)
- `on_run_rs_discovery()` - Find reverse salients

### 23.3 Oracle Prediction (10739-10784)
- `on_run_oracle_prediction()` - Prediction market pipeline

### 23.4 Domain Discovery Pipeline (10785-10828)
- `on_run_domain_discovery()` - Full domain discovery pipeline

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Lines | 10,828 |
| Major Sections | 23 |
| Chainlit Decorators | 67 |
| Action Callbacks | 54 |
| Helper Functions | 35 |
| Bot Configurations | 16 |
| Research Tools | 7 |

---

## Recommended Refactoring

### High Priority Extractions:
1. **Research Tools** (Lines 6776-7729) → `tools/research_callbacks.py`
2. **Grading System** (Lines 10030-10610) → `callbacks/grading.py`
3. **Agent Switching** (Lines 4114-4437) → `callbacks/agent_switch.py`
4. **Phase Callbacks** (Lines 4438-5687) → `callbacks/phase_navigation.py`

### Medium Priority:
5. **Media Handlers** (Lines 5688-5928) → `callbacks/media.py`
6. **Audio Handlers** (Lines 9133-9613) → `voice/audio_handlers.py`
7. **Domain Discovery** (Lines 9614-10029) → `callbacks/domain.py`

### Keep in Main File:
- Bot configurations
- Chat lifecycle (`start`, `resume`, `stop`)
- Main message handler
- Settings

---

*Generated: 2026-02-04*
