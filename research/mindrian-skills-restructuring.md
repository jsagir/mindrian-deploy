# Mindrian Skills-Based Restructuring Proposal

**Branch:** `claude/create-median-branch-B3KVS` (Alternative Research)
**Date:** 2026-02-08
**Purpose:** Design a skills-based architecture to replace the monolithic mindrian_chat.py

---

## Executive Summary

Mindrian's intelligence — prompts, RAG, GraphRAG, tools, domain knowledge — is strong. But it's trapped inside a **6,308-line monolith** (`mindrian_chat.py`) where UI wiring, orchestration logic, bot configuration, and feature code are all tangled together.

This proposal restructures Mindrian around **skills** — self-contained, auto-registering capability modules that declare their own UI, triggers, and execution logic. Bots become **compositions of skills** rather than dict entries with hardcoded callbacks.

---

## Current Architecture Audit

### mindrian_chat.py Breakdown (6,308 lines)

| Section | Lines | What It Contains |
|---------|-------|-----------------|
| Imports + Config | 1-314 | API keys, clients, AGENT_TRIGGERS, DB setup |
| BOTS dict | 315-685 | 13 bot definitions (name, prompt, welcome, config) |
| Chat profiles + Starters | 686-1063 | `@cl.set_chat_profiles`, STARTERS dict |
| Settings | 1064-1514 | `@cl.on_settings_update` — widget handling |
| Session lifecycle | 1515-1987 | `on_chat_start`, `on_chat_resume`, `on_stop`, `on_feedback` |
| Action callbacks | 1988-4752 | **60+ hand-wired @cl.action_callback handlers** |
| Message handler | 4753-5250+ | The main `@cl.on_message` — 500-line if/else pipeline |
| Voice handling | 5427-5894 | Audio start/chunk/end + transcription |
| CV/Research analysis | 5895-6308 | Domain-specific feature callbacks |

### Key Problems

1. **Every new bot** requires edits in 5+ locations (BOTS dict, profiles, starters, phases, triggers, switch callbacks)
2. **Every new feature** means another `@cl.action_callback` in the monolith
3. **60+ action callbacks** are individually wired — 13 `switch_to_X` handlers that are all identical
4. **The message handler** is a 500-line pipeline mixing file processing, image detection, RAG enrichment, GraphRAG, LangExtract, validation workflows, model selection, streaming, and button generation
5. **No separation** between "what this skill does" and "how it renders in Chainlit"
6. **Bot config is static** — BOTS dict can't be extended at runtime

### What's Already Well-Structured (Keep As-Is)

| Module | Quality | Notes |
|--------|---------|-------|
| `tools/tool_dispatcher.py` | Good | Already has a registry pattern (TOOL_REGISTRY → callable) |
| `tools/graph_orchestrator.py` | Good | Graph-driven research plan discovery + execution |
| `tools/graphrag_lite.py` | Good | Clean enrichment API (enrich_for_bot) |
| `tools/langextract.py` | Good | Instant extraction + background extraction |
| `utils/charts.py` | Good | Standalone visualization functions |
| `utils/media.py` | Good | Video/audio utilities with config dicts |
| `utils/file_processor.py` | Good | Clean input → (content, metadata) interface |
| `prompts/*.py` | Good | Already modular, one file per bot |

---

## Proposed Architecture: Skills-Based Mindrian

### Layer Diagram

```
┌──────────────────────────────────────────────────┐
│                   UI Layer                        │
│  (Chainlit / or future: Next.js / Open WebUI)    │
│  Renders from SkillResult + ActionDef             │
├──────────────────────────────────────────────────┤
│                Orchestrator                        │
│  Message → Enrich → Route → Execute → Render      │
│  (Thin: ~200 lines, no feature logic)             │
├──────────────────────────────────────────────────┤
│              Skill Registry                        │
│  Auto-discovers skills/ directory                  │
│  Maps triggers, actions, bot availability          │
├──────────┬───────────┬───────────┬───────────────┤
│  Bot     │  Research  │  Workshop │  Utility      │
│  Skills  │  Skills    │  Skills   │  Skills       │
├──────────┴───────────┴───────────┴───────────────┤
│              Intelligence Layer                    │
│  prompts/ │ tools/ │ utils/ │ RAG │ GraphRAG      │
│  (Unchanged — this is what makes Mindrian work)   │
└──────────────────────────────────────────────────┘
```

### Core Abstractions

#### 1. SkillContext — What every skill receives

```python
@dataclass
class SkillContext:
    """Everything a skill needs to do its job."""
    message: str                          # User's message
    history: list[dict]                   # Conversation history
    bot_id: str                           # Active bot
    bot_config: dict                      # Bot's full config
    session: dict                         # Session state
    settings: dict                        # User preferences
    phase: int                            # Current workshop phase
    phases: list[dict]                    # Phase definitions
    turn_count: int                       # Conversation turn number
    extraction_signals: dict | None       # LangExtract results
    graphrag_hint: str | None             # GraphRAG enrichment
    file_context: str                     # Processed file uploads
    image_parts: list                     # Multimodal image parts
```

#### 2. SkillResult — What every skill returns

```python
@dataclass
class SkillResult:
    """Structured output from any skill execution."""
    content: str                          # Markdown response
    actions: list[ActionDef] = field(default_factory=list)  # Follow-up buttons
    elements: list = field(default_factory=list)             # Charts, images, files
    history_entry: dict | None = None     # What to append to history
    phase_advance: bool = False           # Should we advance the workshop phase?
    metadata: dict = field(default_factory=dict)  # Skill-specific data

    # Rendering hints
    stream: bool = False                  # Was this streamed already?
    suppress_default: bool = False        # Don't run default LLM response after this
```

#### 3. ActionDef — Skills declare their own UI

```python
@dataclass
class ActionDef:
    """A UI action that a skill provides."""
    name: str                             # Unique action ID
    label: str                            # Button text
    tooltip: str = ""                     # Hover text
    icon: str = ""                        # Emoji or icon path
    payload: dict = field(default_factory=dict)
    visible_for: list[str] = field(default_factory=lambda: ["*"])  # Bot filter
```

#### 4. Skill Base Class

```python
class Skill:
    """Base class for all Mindrian skills."""

    # Identity
    name: str                             # Unique skill ID
    label: str                            # Display name
    description: str                      # What this skill does

    # Discovery
    trigger_keywords: list[str] = []      # Auto-suggest when these appear
    available_for: list[str] = ["*"]      # Which bots can use this skill
    requires_phases: bool = False         # Only for workshop bots

    # Priority
    priority: int = 50                    # 0-100, higher = runs first in pipeline

    async def execute(self, context: SkillContext) -> SkillResult:
        """Run the skill. Override in subclass."""
        raise NotImplementedError

    def actions(self) -> list[ActionDef]:
        """Declare UI actions this skill provides."""
        return []

    def should_activate(self, context: SkillContext) -> bool:
        """Optional: custom activation logic beyond keywords."""
        return True
```

---

### Skill Catalog (Migrating from Current Monolith)

#### Bot Skills (replace BOTS dict + switch callbacks)

| Skill | Current Location | What It Encapsulates |
|-------|-----------------|---------------------|
| `BotSwitchSkill` | 13 `switch_to_X` callbacks + `handle_agent_switch` | One generic handler for all bot switches |
| `BotRegistrySkill` | BOTS dict + chat_profiles + STARTERS | Auto-registers bots from `bots/` directory |

#### Research Skills (replace research action callbacks)

| Skill | Current Location | Lines Saved |
|-------|-----------------|-------------|
| `DeepResearchSkill` | `on_deep_research()` + `on_deep_research_full()` | ~450 |
| `GeminiDeepResearchSkill` | `on_gemini_deep_research()` | ~200 |
| `ArxivSearchSkill` | `on_arxiv_search()` | ~30 |
| `PatentSearchSkill` | `on_patent_search()` | ~30 |
| `TrendsSearchSkill` | `on_trends_search()` | ~40 |
| `GovDataSearchSkill` | `on_govdata_search()` | ~40 |
| `DatasetSearchSkill` | `on_dataset_search()` | ~30 |
| `NewsSearchSkill` | `on_news_search()` | ~50 |

#### Workshop Skills (replace phase/progress callbacks)

| Skill | Current Location | Lines Saved |
|-------|-----------------|-------------|
| `NextPhaseSkill` | `on_next_phase()` | ~180 |
| `ShowProgressSkill` | `on_show_progress()` | ~20 |
| `ShowExampleSkill` | `on_show_example()` | ~240 |
| `WatchVideoSkill` | `on_watch_video()` + chapter callbacks | ~200 |
| `AudiobookSkill` | `on_listen_audiobook()` + 18 chapter callbacks | ~150 |

#### Analysis Skills (replace analysis callbacks)

| Skill | Current Location | Lines Saved |
|-------|-----------------|-------------|
| `ThinkThroughSkill` | `on_think_through()` | ~120 |
| `SynthesizeSkill` | `on_synthesize_conversation()` | ~120 |
| `ExtractInsightsSkill` | `on_extract_insights()` | ~120 |
| `MultiAgentSkill` | `on_multi_agent_analysis()` + 4 sub-handlers | ~180 |
| `ValidationWorkflowSkill` | Inline in `on_message` | ~60 |

#### Utility Skills

| Skill | Current Location | Lines Saved |
|-------|-----------------|-------------|
| `SpeakResponseSkill` | `on_speak_response()` | ~130 |
| `ImageGenerationSkill` | `on_generate_image()` + inline detection | ~150 |
| `ExportSummarySkill` | `on_export_summary()` | ~30 |
| `FeedbackSkill` | `on_detailed_feedback()` + rating handlers | ~100 |
| `CVAnalysisSkill` | `on_analyze_cv()` | ~140 |
| `ResearchAnalysisSkill` | `on_analyze_research()` + explore + deep dive | ~260 |

#### Enrichment Skills (pipeline middleware, not user-facing)

| Skill | Current Location | Priority |
|-------|-----------------|----------|
| `FileProcessorSkill` | Inline in `on_message` (~100 lines) | 90 (runs early) |
| `ImageProcessorSkill` | Inline in `on_message` (~80 lines) | 90 |
| `LangExtractSkill` | Inline in `on_message` (~15 lines) | 80 |
| `GraphRAGSkill` | Inline in `on_message` (~15 lines) | 70 |
| `PhaseContextSkill` | Inline in `on_message` (~10 lines) | 60 |
| `AgentSuggestionSkill` | Inline in `on_message` (~40 lines) | 10 (runs late) |

---

### Proposed Directory Structure

```
mindrian-deploy/
├── app.py                        # Thin entry point (~50 lines)
│                                 # Sets up Chainlit, loads registry,
│                                 # wires lifecycle hooks
│
├── core/
│   ├── __init__.py
│   ├── orchestrator.py           # Message pipeline (~200 lines)
│   │                             # receive → enrich → route → execute → render
│   ├── registry.py               # Skill auto-discovery + registration
│   ├── context.py                # SkillContext dataclass
│   ├── result.py                 # SkillResult + ActionDef dataclasses
│   ├── skill.py                  # Skill base class
│   └── renderer.py               # SkillResult → Chainlit UI elements
│                                 # (Abstracted so UI framework is swappable)
│
├── bots/                         # Bot definitions (replace BOTS dict)
│   ├── __init__.py               # Auto-discovers bot modules
│   ├── base.py                   # BotConfig dataclass
│   ├── lawrence.py               # { name, prompt, skills, starters, welcome }
│   ├── tta.py                    # + phases definition
│   ├── jtbd.py
│   ├── scurve.py
│   ├── redteam.py
│   ├── ackoff.py
│   ├── bono.py
│   ├── knowns.py
│   ├── domain.py
│   ├── investment.py
│   ├── scenario.py
│   ├── validation.py
│   └── beautiful_question.py
│
├── skills/                       # Self-contained skill modules
│   ├── __init__.py               # Auto-discovers skill modules
│   ├── base.py                   # Skill base class (re-exported from core)
│   │
│   ├── research/                 # Research skill family
│   │   ├── deep_research.py
│   │   ├── gemini_deep_research.py
│   │   ├── arxiv_search.py
│   │   ├── patent_search.py
│   │   ├── trends_search.py
│   │   ├── govdata_search.py
│   │   ├── dataset_search.py
│   │   └── news_search.py
│   │
│   ├── workshop/                 # Workshop skill family
│   │   ├── next_phase.py
│   │   ├── show_progress.py
│   │   ├── show_example.py
│   │   ├── watch_video.py
│   │   └── audiobook.py
│   │
│   ├── analysis/                 # Analysis skill family
│   │   ├── think_through.py
│   │   ├── synthesize.py
│   │   ├── extract_insights.py
│   │   ├── multi_agent.py
│   │   └── validation_workflow.py
│   │
│   ├── utility/                  # Utility skill family
│   │   ├── speak_response.py
│   │   ├── image_generation.py
│   │   ├── export_summary.py
│   │   ├── feedback.py
│   │   ├── cv_analysis.py
│   │   └── research_analysis.py
│   │
│   └── enrichment/               # Pipeline middleware (auto-run, no UI)
│       ├── file_processor.py
│       ├── image_processor.py
│       ├── langextract.py
│       ├── graphrag.py
│       ├── phase_context.py
│       └── agent_suggestion.py
│
├── prompts/                      # UNCHANGED — keep as-is
├── tools/                        # UNCHANGED — keep as-is
├── utils/                        # UNCHANGED — keep as-is
├── public/                       # UNCHANGED — keep as-is
└── .chainlit/                    # UNCHANGED — keep as-is
```

---

### The Orchestrator (core/orchestrator.py)

This replaces the 500-line `@cl.on_message` handler:

```python
async def handle_message(message, session):
    """
    The entire message pipeline in ~50 lines of orchestration.
    No feature logic here — skills do the work.
    """
    # 1. Build context
    context = build_context(message, session)

    # 2. Run enrichment skills (sorted by priority, no UI)
    enrichment_skills = registry.get_enrichment_skills(context.bot_id)
    for skill in sorted(enrichment_skills, key=lambda s: -s.priority):
        context = await skill.enrich(context)

    # 3. Check for skill interceptions (image gen, validation, etc.)
    for skill in registry.get_intercepting_skills(context.bot_id):
        if skill.should_intercept(context):
            result = await skill.execute(context)
            if result.suppress_default:
                await render(result, session)
                return

    # 4. Send to LLM (Gemini) with enriched context
    result = await llm_generate(context)

    # 5. Collect action buttons from all applicable skills
    actions = []
    for skill in registry.get_skills_for_bot(context.bot_id):
        actions.extend(skill.actions())
    result.actions = actions

    # 6. Auto-suggest agents based on response
    suggestions = registry.suggest_skills(result.content, context)
    result.actions.extend(suggestions)

    # 7. Render
    await render(result, session)

    # 8. Post-response (background extraction, context sync)
    for skill in registry.get_post_skills(context.bot_id):
        asyncio.create_task(skill.post_execute(context, result))
```

### The Registry (core/registry.py)

```python
class SkillRegistry:
    """Auto-discovers and manages all skills."""

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._bots: dict[str, BotConfig] = {}

    def discover(self, skills_dir="skills/", bots_dir="bots/"):
        """Scan directories, import modules, register skills/bots."""
        # Walk skills/ directory
        # For each module with a Skill subclass, register it
        # Walk bots/ directory
        # For each module with a BotConfig, register it

    def get_skills_for_bot(self, bot_id: str) -> list[Skill]:
        """Return skills available for this bot."""
        return [s for s in self._skills.values()
                if "*" in s.available_for or bot_id in s.available_for]

    def get_enrichment_skills(self, bot_id: str) -> list[Skill]:
        """Return pipeline middleware skills."""
        return [s for s in self.get_skills_for_bot(bot_id)
                if isinstance(s, EnrichmentSkill)]

    def suggest_skills(self, text: str, context: SkillContext) -> list[ActionDef]:
        """Suggest relevant skills based on response content."""
        suggestions = []
        for skill in self._skills.values():
            if any(kw in text.lower() for kw in skill.trigger_keywords):
                suggestions.extend(skill.actions())
        return suggestions

    def handle_action(self, action_name: str) -> Skill | None:
        """Route an action callback to its owning skill."""
        for skill in self._skills.values():
            for action_def in skill.actions():
                if action_def.name == action_name:
                    return skill
        return None
```

### The Renderer (core/renderer.py)

```python
async def render(result: SkillResult, session):
    """
    Convert SkillResult → Chainlit UI.

    This is the ONLY place that imports chainlit.
    Swap this module to change UI frameworks.
    """
    import chainlit as cl

    # Convert ActionDefs to cl.Action
    cl_actions = [
        cl.Action(
            name=a.name,
            payload=a.payload,
            label=a.label,
            tooltip=a.tooltip,
        )
        for a in result.actions
    ]

    # Convert elements
    cl_elements = result.elements  # Already cl.* objects from skills

    # Send
    if not result.stream:  # Non-streamed results
        await cl.Message(
            content=result.content,
            actions=cl_actions,
            elements=cl_elements,
        ).send()
```

---

### Bot Definition Example

```python
# bots/tta.py
from core.skill import BotConfig
from prompts.tta_workshop import TTA_WORKSHOP_PROMPT

tta = BotConfig(
    id="tta",
    name="Trending to the Absurd",
    icon="/public/icons/tta.svg",
    emoji="🔮",
    description="Guided workshop: escape presentism, find future problems",
    prompt=TTA_WORKSHOP_PROMPT,
    has_phases=True,
    phases=[
        {"name": "Introduction", "status": "ready"},
        {"name": "Domain & Trends", "status": "pending"},
        {"name": "Deep Research", "status": "pending"},
        {"name": "Absurd Extrapolation", "status": "pending"},
        {"name": "Problem Hunting", "status": "pending"},
        {"name": "Opportunity Validation", "status": "pending"},
        {"name": "Action Planning", "status": "pending"},
        {"name": "Reflection", "status": "pending"},
    ],
    skills=[
        "deep_research", "show_example", "next_phase",
        "show_progress", "think_through", "synthesize",
        "speak_response", "trends_search", "watch_video",
        "audiobook", "extract_insights",
    ],
    starters=[
        {"label": "Start Workshop", "message": "I'm ready to begin the TTA workshop", "icon": "/public/icons/start.svg"},
        {"label": "Explore a Trend", "message": "Help me explore an emerging trend in my industry", "icon": "/public/icons/trend.svg"},
        {"label": "Show Example", "message": "Show me an example of TTA in action", "icon": "/public/icons/example.svg"},
        {"label": "I Have a Domain", "message": "I already have a domain I want to explore", "icon": "/public/icons/domain.svg"},
    ],
    welcome="""🔮 **Trending to the Absurd Workshop**

Hello, I'm Larry Aronhime. Tell me about yourself and your team...""",
)
```

### Skill Definition Example

```python
# skills/research/deep_research.py
from core.skill import Skill, SkillContext, SkillResult, ActionDef

class DeepResearchSkill(Skill):
    name = "deep_research"
    label = "Deep Research"
    description = "Multi-source web research with Tavily"
    trigger_keywords = ["research", "evidence", "source", "data", "study"]
    available_for = ["*"]  # All bots

    def actions(self) -> list[ActionDef]:
        return [
            ActionDef(
                name="deep_research",
                label="🔍 Research",
                tooltip="Search the web for relevant data and evidence",
            ),
            ActionDef(
                name="deep_research_full",
                label="🔍 Full Research",
                tooltip="Comprehensive multi-source research",
                visible_for=["larry_playground"],  # Only in playground
            ),
        ]

    async def execute(self, context: SkillContext) -> SkillResult:
        from tools.deep_research import run_deep_research

        # Get the topic from recent conversation
        topic = context.message or context.history[-1]["content"][:200]

        # Run research (this is the existing logic, extracted)
        results = await run_deep_research(
            topic=topic,
            bot_id=context.bot_id,
            search_depth=context.settings.get("research_depth", "advanced"),
        )

        # Format results
        content = f"## 🔍 Research Results: {topic[:60]}\n\n{results['formatted']}"

        return SkillResult(
            content=content,
            suppress_default=True,
            metadata={"sources": results.get("sources", [])},
        )
```

---

## Migration Strategy

### Phase 0: Foundation (No Breaking Changes)

1. Create `core/` directory with base classes (Skill, SkillContext, SkillResult, ActionDef)
2. Create `core/registry.py` with auto-discovery
3. Create `core/renderer.py` as thin Chainlit adapter
4. **mindrian_chat.py continues to work unchanged**

### Phase 1: Extract Skills (Parallel Operation)

1. Extract one skill at a time from mindrian_chat.py into `skills/`
2. Each extracted skill registers with the registry
3. `mindrian_chat.py` delegates to the skill via registry (one-line change per callback)
4. **Tests verify identical behavior**

Example migration of one callback:

```python
# BEFORE (in mindrian_chat.py):
@cl.action_callback("deep_research")
async def on_deep_research(action: cl.Action):
    # 50 lines of feature code...

# AFTER (in mindrian_chat.py):
@cl.action_callback("deep_research")
async def on_deep_research(action: cl.Action):
    await registry.execute_action("deep_research", session)
```

### Phase 2: Extract Bots

1. Move BOTS dict entries into `bots/*.py` modules
2. Registry auto-discovers and registers them
3. Replace STARTERS, WORKSHOP_PHASES, chat_profiles with registry lookups
4. Delete 13 `switch_to_X` handlers, replace with one generic handler

### Phase 3: Slim Orchestrator

1. Replace 500-line `@cl.on_message` with orchestrator pipeline
2. Move enrichment logic (LangExtract, GraphRAG, file processing) into enrichment skills
3. `mindrian_chat.py` → `app.py` (~50 lines of Chainlit lifecycle wiring)

### Phase 4: UI Swappable (Future)

With all feature logic in skills and rendering in `core/renderer.py`:
- Swap Chainlit for **Next.js + Vercel AI SDK** — just rewrite renderer.py
- Swap for **Open WebUI** — same intelligence, different UI
- Swap for **custom React app** — full control over UI/UX
- Chainlit remains as one option among many

---

## What Changes vs What Stays

### UNCHANGED (Intelligence Layer)

| Module | Status |
|--------|--------|
| `prompts/*.py` | Keep as-is — already modular |
| `tools/tool_dispatcher.py` | Keep as-is — already has registry pattern |
| `tools/graph_orchestrator.py` | Keep as-is — clean interface |
| `tools/graphrag_lite.py` | Keep as-is — used by enrichment skill |
| `tools/langextract.py` | Keep as-is — used by enrichment skill |
| `tools/tavily_search.py` | Keep as-is — used by research skills |
| `tools/deep_research.py` | Keep as-is — used by research skills |
| `tools/arxiv_search.py` | Keep as-is |
| `tools/patent_search.py` | Keep as-is |
| `tools/news_search.py` | Keep as-is |
| `tools/trends_search.py` | Keep as-is |
| `utils/charts.py` | Keep as-is |
| `utils/media.py` | Keep as-is |
| `utils/file_processor.py` | Keep as-is |
| `utils/feedback.py` | Keep as-is |
| `utils/dynamic_examples.py` | Keep as-is |
| `utils/quality_scorer.py` | Keep as-is |

### NEW (Orchestration Layer)

| Module | Purpose | Est. Lines |
|--------|---------|-----------|
| `core/skill.py` | Base classes | ~80 |
| `core/context.py` | SkillContext dataclass | ~40 |
| `core/result.py` | SkillResult + ActionDef | ~40 |
| `core/registry.py` | Auto-discovery + routing | ~150 |
| `core/orchestrator.py` | Message pipeline | ~200 |
| `core/renderer.py` | SkillResult → Chainlit UI | ~80 |
| `bots/*.py` (13 files) | Bot definitions | ~50 each, ~650 total |
| `skills/**/*.py` (~25 files) | Extracted skills | ~100 each avg, ~2500 total |
| `app.py` | Entry point | ~50 |

### DELETED

| What | Lines Removed |
|------|--------------|
| `mindrian_chat.py` | **6,308 lines → 0** |

### Net Effect

| Metric | Before | After |
|--------|--------|-------|
| Files | 1 monolith + 38 modules | ~45 focused modules |
| Largest file | 6,308 lines | ~200 lines (orchestrator) |
| Lines to add a bot | 5+ edits across monolith | 1 file in bots/ |
| Lines to add a skill | Edit monolith + test | 1 file in skills/ |
| Lines to add a switch handler | Copy-paste callback | Automatic (registry) |
| UI framework coupling | Deep (Chainlit everywhere) | Thin (renderer.py only) |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking existing functionality | High | Phase 1 runs in parallel — old code works until verified |
| Chainlit-specific features (TaskList, Step, etc.) | Medium | Renderer abstracts these; skills return structured results |
| Performance overhead from registry lookups | Low | Registry is in-memory dict, O(1) lookup |
| Over-abstraction | Medium | Keep skills simple — a skill is just execute() + actions() |
| Session state management across skills | Medium | SkillContext is read-only; mutations go through orchestrator |
| Deployment complexity | Low | Same `chainlit run app.py`, same Render deploy |

---

## Decision: Stay on Chainlit or Migrate UI?

### Option A: Skills Architecture + Keep Chainlit
- **Effort:** Medium (4-6 focused sessions)
- **Risk:** Low (incremental migration)
- **Result:** Clean architecture, same proven UI, easier to extend

### Option B: Skills Architecture + New UI (Next.js / Open WebUI)
- **Effort:** High (full rewrite of rendering layer)
- **Risk:** High (two big changes at once)
- **Result:** Full UI control, modern frontend, but more work

### Recommendation: **Option A first, Option B becomes trivial after.**

The skills architecture is the hard part. Once intelligence is decoupled from UI, swapping the UI is just rewriting `core/renderer.py` (~80 lines). Do Option A, prove it works, then evaluate if Chainlit is still the right UI.

---

## Next Steps

1. **Decide:** Approve this architecture direction
2. **Prototype:** Build `core/` with one skill extracted (e.g., DeepResearchSkill)
3. **Validate:** Run prototype alongside existing monolith
4. **Migrate:** Extract skills one by one, test each
5. **Ship:** Replace mindrian_chat.py with app.py + skills

---

*This document is a living proposal. Architecture decisions should be validated with a working prototype before full migration.*
