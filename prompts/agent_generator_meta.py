"""
AGENT_GENERATOR_META_PROMPT - Mindrian Agent Creation System

This meta-prompt generates complete agent configurations for the Mindrian platform.
It includes all TIER 1-4 requirements and maps to the available tool stack.

Usage:
    from prompts.agent_generator_meta import AGENT_GENERATOR_META_PROMPT

    # Use with Gemini to generate a new agent configuration
    response = model.generate_content([AGENT_GENERATOR_META_PROMPT, user_intake])
"""

# =============================================================================
# MINDRIAN TOOL STACK REFERENCE
# =============================================================================
# This maps all available tools/utilities that agents can use.
# Each agent profile should specify which tools from this stack it needs.

MINDRIAN_TOOL_STACK = {
    # -------------------------------------------------------------------------
    # RESEARCH & KNOWLEDGE RETRIEVAL
    # -------------------------------------------------------------------------
    "research": {
        "tavily_search": {
            "path": "tools/tavily_search.py",
            "description": "Web search via Tavily API",
            "use_case": "Real-time web research, current events, market data",
            "best_for": ["lawrence", "larry_playground", "domain", "investment"],
        },
        "deep_research": {
            "path": "tools/deep_research.py",
            "description": "Multi-query research orchestration",
            "use_case": "Complex research requiring multiple angles",
            "best_for": ["larry_playground", "domain", "scenario"],
        },
        "arxiv_search": {
            "path": "tools/arxiv_search.py",
            "description": "Academic paper search",
            "use_case": "Scientific research, academic citations",
            "best_for": ["domain", "scurve", "validation"],
        },
        "patent_search": {
            "path": "tools/patent_search.py",
            "description": "Patent database search",
            "use_case": "IP research, technology landscape",
            "best_for": ["scurve", "investment", "domain"],
        },
        "news_search": {
            "path": "tools/news_search.py",
            "description": "News article search",
            "use_case": "Current events, market news",
            "best_for": ["investment", "scenario", "tta"],
        },
        "trends_search": {
            "path": "tools/trends_search.py",
            "description": "Google Trends data",
            "use_case": "Trend analysis, market interest",
            "best_for": ["scurve", "tta", "investment"],
        },
        "govdata_search": {
            "path": "tools/govdata_search.py",
            "description": "Government data search",
            "use_case": "Regulatory data, public statistics",
            "best_for": ["validation", "investment", "domain"],
        },
        "dataset_search": {
            "path": "tools/dataset_search.py",
            "description": "Dataset discovery",
            "use_case": "Find relevant datasets for analysis",
            "best_for": ["validation", "domain", "grading"],
        },
    },

    # -------------------------------------------------------------------------
    # KNOWLEDGE GRAPH (Neo4j)
    # -------------------------------------------------------------------------
    "graph": {
        "graphrag_lite": {
            "path": "tools/graphrag_lite.py",
            "description": "Hybrid vector + graph retrieval",
            "use_case": "Context enrichment with relationships",
            "best_for": ["all_agents"],
        },
        "neo4j_framework_discovery": {
            "path": "tools/neo4j_framework_discovery.py",
            "description": "Framework and methodology lookup",
            "use_case": "Find applicable PWS frameworks",
            "best_for": ["lawrence", "ackoff", "jtbd", "tta"],
        },
        "graph_router": {
            "path": "tools/graph_router.py",
            "description": "Intelligent graph query routing",
            "use_case": "Route queries to optimal graph paths",
            "best_for": ["larry_playground", "domain"],
        },
        "graph_orchestrator": {
            "path": "tools/graph_orchestrator.py",
            "description": "Multi-hop graph traversal",
            "use_case": "Complex relationship discovery",
            "best_for": ["domain", "nested_hierarchies", "scenario"],
        },
        "pws_brain": {
            "path": "tools/pws_brain.py",
            "description": "PWS methodology knowledge base",
            "use_case": "Core PWS concepts and frameworks",
            "best_for": ["lawrence", "larry_playground", "ackoff"],
        },
    },

    # -------------------------------------------------------------------------
    # ANALYSIS & CLASSIFICATION
    # -------------------------------------------------------------------------
    "analysis": {
        "problem_classifier": {
            "path": "tools/problem_classifier.py",
            "description": "Cynefin + PWS problem classification",
            "use_case": "Classify problem complexity and type",
            "best_for": ["lawrence", "knowns", "validation"],
        },
        "assessment_engine": {
            "path": "tools/assessment_engine.py",
            "description": "Multi-dimensional assessment",
            "use_case": "Structured evaluation with criteria",
            "best_for": ["grading", "validation", "investment"],
        },
        "grading_workflow": {
            "path": "tools/grading_workflow.py",
            "description": "PWS grading rubric application",
            "use_case": "Score against PWS criteria",
            "best_for": ["grading"],
        },
        "validation_workflow": {
            "path": "tools/validation_workflow.py",
            "description": "Triple Validation workflow",
            "use_case": "Is it Real? Can we Win? Worth it?",
            "best_for": ["validation", "investment", "redteam"],
        },
        "opportunity_bank": {
            "path": "tools/opportunity_bank.py",
            "description": "Opportunity tracking and scoring",
            "use_case": "Track and prioritize opportunities",
            "best_for": ["investment", "scenario", "jtbd"],
        },
    },

    # -------------------------------------------------------------------------
    # PHASE & WORKSHOP MANAGEMENT
    # -------------------------------------------------------------------------
    "workshop": {
        "smart_phase_tracker": {
            "path": "tools/smart_phase_tracker.py",
            "description": "LLM-based phase completion detection",
            "use_case": "Detect when phase goals are met",
            "best_for": ["all_workshop_bots"],
        },
        "phase_insights": {
            "path": "tools/phase_insights.py",
            "description": "User-facing progress insights",
            "use_case": "Surface progress non-intrusively",
            "best_for": ["all_workshop_bots"],
        },
        "phase_enricher": {
            "path": "tools/phase_enricher.py",
            "description": "Enrich phase context with knowledge",
            "use_case": "Add relevant examples to phases",
            "best_for": ["tta", "jtbd", "ackoff", "scurve"],
        },
        "phase_validator": {
            "path": "tools/phase_validator.py",
            "description": "Validate phase completion criteria",
            "use_case": "Check if phase requirements met",
            "best_for": ["all_workshop_bots"],
        },
    },

    # -------------------------------------------------------------------------
    # EXTRACTION & SYNTHESIS
    # -------------------------------------------------------------------------
    "extraction": {
        "langextract": {
            "path": "tools/langextract.py",
            "description": "Zero-latency structured extraction",
            "use_case": "Extract statistics, assumptions, questions",
            "best_for": ["all_agents"],
        },
        "google_langextract": {
            "path": "tools/google_langextract.py",
            "description": "Google-based extraction",
            "use_case": "Deep extraction with Gemini",
            "best_for": ["larry_playground", "validation"],
        },
        "result_synthesizer": {
            "path": "tools/result_synthesizer.py",
            "description": "Multi-source result synthesis",
            "use_case": "Combine research from multiple tools",
            "best_for": ["larry_playground", "domain", "scenario"],
        },
        "research_cache": {
            "path": "tools/research_cache.py",
            "description": "Cache and deduplicate research",
            "use_case": "Avoid redundant API calls",
            "best_for": ["all_agents"],
        },
        "document_ai": {
            "path": "tools/document_ai.py",
            "description": "Document analysis and extraction",
            "use_case": "Analyze uploaded PDFs, docs",
            "best_for": ["validation", "grading", "investment"],
        },
        "presentation_analyzer": {
            "path": "tools/presentation_analyzer.py",
            "description": "Slide deck analysis",
            "use_case": "Analyze pitch decks, presentations",
            "best_for": ["grading", "investment", "validation"],
        },
    },

    # -------------------------------------------------------------------------
    # VISUALIZATION & OUTPUT
    # -------------------------------------------------------------------------
    "visualization": {
        "diagrams": {
            "path": "utils/diagrams.py",
            "description": "Mermaid diagrams (mindmaps, flowcharts)",
            "use_case": "Visual idea mapping",
            "best_for": ["all_agents"],
            "elements": ["MermaidDiagram", "QuadrantChart", "BusinessModelCanvas"],
        },
        "charts": {
            "path": "utils/charts.py",
            "description": "Plotly charts (DIKW, S-Curve, DataFrames)",
            "use_case": "Data visualization",
            "best_for": ["ackoff", "scurve", "grading", "investment"],
        },
        "ui_elements": {
            "path": "utils/ui_elements.py",
            "description": "Custom Chainlit elements",
            "use_case": "Rich UI components",
            "best_for": ["all_agents"],
            "elements": ["ThinkingPanel", "GradeReveal", "ScoreBreakdown", "OpportunityCard"],
        },
        "image_generation": {
            "path": "utils/image_generation.py",
            "description": "AI image generation",
            "use_case": "Visual metaphors, diagrams",
            "best_for": ["scenario", "tta", "beautiful_question"],
        },
    },

    # -------------------------------------------------------------------------
    # QUALITY & SCORING
    # -------------------------------------------------------------------------
    "quality": {
        "quality_scorer": {
            "path": "utils/quality_scorer.py",
            "description": "Multi-dimensional quality scoring",
            "use_case": "Score responses against criteria",
            "best_for": ["grading", "validation"],
        },
        "dynamic_examples": {
            "path": "utils/dynamic_examples.py",
            "description": "Context-aware example retrieval",
            "use_case": "Find relevant case studies",
            "best_for": ["all_agents"],
        },
        "insight_extractor": {
            "path": "utils/insight_extractor.py",
            "description": "Extract key insights from conversation",
            "use_case": "Surface important findings",
            "best_for": ["lawrence", "validation", "ackoff"],
        },
    },

    # -------------------------------------------------------------------------
    # CONTEXT & MEMORY
    # -------------------------------------------------------------------------
    "context": {
        "context_persistence": {
            "path": "utils/context_persistence.py",
            "description": "Session context preservation",
            "use_case": "Maintain context across bot switches",
            "best_for": ["all_agents"],
        },
        "context_extraction": {
            "path": "utils/context_extraction.py",
            "description": "Extract key entities from context",
            "use_case": "Build context summary for handoffs",
            "best_for": ["all_agents"],
        },
        "session_distiller": {
            "path": "utils/session_distiller.py",
            "description": "Distill session into summary",
            "use_case": "Create session summaries",
            "best_for": ["all_agents"],
        },
        "gemini_rag": {
            "path": "utils/gemini_rag.py",
            "description": "Gemini RAG cache utilities",
            "use_case": "Workshop-specific RAG retrieval",
            "best_for": ["all_workshop_bots"],
        },
    },

    # -------------------------------------------------------------------------
    # MEDIA & EXPORT
    # -------------------------------------------------------------------------
    "media": {
        "media": {
            "path": "utils/media.py",
            "description": "Video, audio, file exports",
            "use_case": "Embed videos, play audiobooks, export MD",
            "best_for": ["all_workshop_bots"],
        },
        "voice_streaming": {
            "path": "utils/voice_streaming.py",
            "description": "Real-time voice streaming",
            "use_case": "Voice responses",
            "best_for": ["lawrence", "larry_playground"],
        },
        "elevenlabs_streaming": {
            "path": "utils/elevenlabs_streaming.py",
            "description": "ElevenLabs TTS integration",
            "use_case": "High-quality voice synthesis",
            "best_for": ["lawrence", "larry_playground"],
        },
        "storage": {
            "path": "utils/storage.py",
            "description": "Supabase storage integration",
            "use_case": "File uploads, exports",
            "best_for": ["all_agents"],
        },
        "file_processor": {
            "path": "utils/file_processor.py",
            "description": "PDF/DOCX/TXT extraction",
            "use_case": "Process uploaded documents",
            "best_for": ["all_agents"],
        },
    },

    # -------------------------------------------------------------------------
    # ORCHESTRATION
    # -------------------------------------------------------------------------
    "orchestration": {
        "tool_dispatcher": {
            "path": "tools/tool_dispatcher.py",
            "description": "Intelligent tool selection",
            "use_case": "Route to appropriate tool",
            "best_for": ["larry_playground"],
        },
        "research_orchestrator": {
            "path": "tools/research_orchestrator.py",
            "description": "Multi-tool research coordination",
            "use_case": "Coordinate complex research",
            "best_for": ["larry_playground", "domain"],
        },
        "adaptive_routing": {
            "path": "utils/adaptive_routing.py",
            "description": "Adaptive response routing",
            "use_case": "Route based on query type",
            "best_for": ["lawrence", "larry_playground"],
        },
    },
}

# =============================================================================
# THINKINGPANEL BOT COLORS
# =============================================================================
# Each bot needs a color for ThinkingPanel visualization.
# Reference: public/elements/ThinkingPanel.jsx

THINKINGPANEL_COLORS = {
    "lawrence": "#6366f1",           # indigo
    "larry_playground": "#8b5cf6",   # purple
    "tta": "#f59e0b",                # amber
    "jtbd": "#10b981",               # emerald
    "scurve": "#3b82f6",             # blue
    "redteam": "#ef4444",            # red
    "ackoff": "#14b8a6",             # teal
    "scenario": "#6366f1",           # indigo
    "beautiful_question": "#ec4899", # pink
    "nested_hierarchies": "#0891b2", # cyan
    "validation": "#059669",         # emerald-600
    "bono": "#7c3aed",               # violet
    "knowns": "#dc2626",             # red-600
    "domain": "#0d9488",             # teal-600
    "investment": "#ca8a04",         # yellow-600
    "grading": "#4f46e5",            # indigo-600
}

# =============================================================================
# AGENT GENERATOR META-PROMPT
# =============================================================================

AGENT_GENERATOR_META_PROMPT = '''
# MINDRIAN AGENT GENERATOR v2.0

You are an expert system that generates complete Mindrian agent configurations.
Your output enables a new PWS methodology bot to be fully integrated into the platform.

## YOUR TASK

Given an intake describing a new agent's purpose, methodology, and personality,
generate ALL required configuration components for TIER 1-4 integration.

---

# SECTION 1: INTAKE ANALYSIS

Analyze the user's intake to extract:

## 1A. IDENTITY MODEL
- **Archetype**: The agent's core persona (e.g., "Socratic Coach", "Devil's Advocate")
- **Voice**: Communication style (e.g., direct, nurturing, provocative)
- **Values**: What the agent prioritizes (e.g., evidence, creativity, rigor)
- **Non-negotiables**: Rules that must NEVER be broken

## 1B. KNOWLEDGE STRUCTURE
- **Primary Domain(s)**: Main expertise areas
- **Frameworks Used**: PWS methodologies applied
- **Cynefin Affinity**: Which complexity domains it handles best
- **Cross-references**: Related agents for handoffs

## 1C. LEARNING PATH (if workshop bot)
- **Phase Count**: Number of workshop phases
- **Phase Goals**: What each phase accomplishes
- **Completion Criteria**: How to detect phase completion
- **Progression Logic**: How phases advance

## 1D. TOOL REQUIREMENTS
Analyze which tools from MINDRIAN_TOOL_STACK the agent needs:
- Research tools (web, academic, patents, news)
- Graph tools (Neo4j, GraphRAG)
- Analysis tools (classification, assessment, validation)
- Workshop tools (phase tracking, insights)
- Visualization tools (diagrams, charts)
- Quality tools (scoring, examples)

---

# SECTION 2: CONFIGURATION OUTPUT

Generate these components:

## COMPONENT A: CORE SYSTEM PROMPT
```python
{BOT_ID}_SYSTEM_PROMPT = """
You are {Agent Name}, a PWS methodology expert specializing in {methodology}.

## Your Role
{Detailed description of expertise and approach}

## Methodology Overview
{Key concepts and how they apply}

## Workshop Phases (if applicable)
1. **{Phase 1}** - {Description}
   Completion indicators: {keywords/evidence}
2. **{Phase 2}** - {Description}
   Completion indicators: {keywords/evidence}
...

## Interaction Style
- {Style point 1}
- {Style point 2}
- {Style point 3}

## Non-Negotiable Rules
- {Rule 1 - e.g., "NEVER provide specific advice without disclaimer"}
- {Rule 2}

## CRITICAL: Language & Response Rules
- ALWAYS respond in ENGLISH regardless of user's locale
- NEVER say you "cannot see images" when text content is provided
- If content appears in another language, translate and respond in English
"""
```

## COMPONENT B: CONVERSATION STARTERS (4 Required)
```python
STARTERS["{bot_id}"] = [
    cl.Starter(
        label="{Action Label 1}",
        message="{Full message user sends}",
        icon="/public/icons/{icon1}.svg"
    ),
    cl.Starter(
        label="{Action Label 2}",
        message="{Full message user sends}",
        icon="/public/icons/{icon2}.svg"
    ),
    cl.Starter(
        label="{Action Label 3}",
        message="{Full message user sends}",
        icon="/public/icons/{icon3}.svg"
    ),
    cl.Starter(
        label="{Action Label 4}",
        message="{Full message user sends}",
        icon="/public/icons/{icon4}.svg"
    ),
]
```
Available icons: start.svg, info.svg, example.svg, apply.svg, research.svg,
                 analyze.svg, validate.svg, challenge.svg, synthesize.svg

## COMPONENT C: BOTS DICT ENTRY
```python
BOTS["{bot_id}"] = {
    "name": "{Display Name}",
    "icon": "{emoji}",
    "description": "{One-line for chat profile dropdown}",
    "system_prompt": {BOT_ID}_SYSTEM_PROMPT,
    "has_phases": {True/False},
    "simple_mode": {True/False},
    "welcome": """{Welcome Message}

I'll guide you through {methodology}. We'll work through {N} phases:

1. **{Phase 1}** - {Brief}
2. **{Phase 2}** - {Brief}
...

{Opening question to start conversation}""",
}
```

## COMPONENT D: AGENT TRIGGERS (CRITICAL - Without this, bot is never suggested!)
```python
AGENT_TRIGGERS["{bot_id}"] = {
    "keywords": [
        "{keyword1}",      # Primary methodology term
        "{keyword2}",      # Secondary concept
        "{keyword3}",      # Related framework
        "{keyword4}",      # Common user phrase
        "{keyword5}",      # Alternative terminology
    ],
    "description": "{Short action description for suggestion button}"
}
```

## COMPONENT E: ACTION CALLBACK (CRITICAL - Without this, switch button won't work!)
```python
@cl.action_callback("switch_to_{bot_id}")
async def on_switch_to_{bot_id}(action: cl.Action):
    """Handle switch to {Agent Name}."""
    await handle_agent_switch("{bot_id}")
```

## COMPONENT F: WORKSHOP PHASES (if has_phases=True)
```python
WORKSHOP_PHASES["{bot_id}"] = [
    {
        "name": "{Phase 1 Name}",
        "status": "ready",
        "completion_keywords": ["{keyword1}", "{keyword2}"],
        "goal": "{What user should accomplish}",
    },
    {
        "name": "{Phase 2 Name}",
        "status": "pending",
        "completion_keywords": ["{keyword1}", "{keyword2}"],
        "goal": "{What user should accomplish}",
    },
    # ... more phases
    {
        "name": "Synthesis",
        "status": "pending",
        "completion_keywords": ["summary", "conclusion", "next steps"],
        "goal": "Consolidate findings and define action items",
    },
]
```

## COMPONENT G: THINKINGPANEL COLOR
```javascript
// Add to public/elements/ThinkingPanel.jsx → botColors
{bot_id}: '{hex_color}',  // {color_name}
```

## COMPONENT H: DYNAMIC EXAMPLES
```python
# Add to utils/dynamic_examples.py

BOT_TO_METHODOLOGY["{bot_id}"] = [
    "{Methodology Name}",
    "{Alternate Name}",
    "{Key Concept}",
]

BOT_TO_CASE_TOPICS["{bot_id}"] = [
    "{Relevant Case Study 1}",
    "{Relevant Case Study 2}",
    "{Company/Industry Example}",
]

STATIC_EXAMPLES["{bot_id}"] = [
    "**{Example 1 Title}**: {Detailed description of real-world application...}",
    "**{Example 2 Title}**: {Another case study with specific details...}",
    "**{Example 3 Title}**: {Third example demonstrating the methodology...}",
]
```

## COMPONENT I: TOOL STACK CONFIGURATION
```python
# Tools this agent should use (from MINDRIAN_TOOL_STACK)

{BOT_ID}_TOOLS = {
    "research": [
        # Select from: tavily_search, deep_research, arxiv_search,
        # patent_search, news_search, trends_search, govdata_search, dataset_search
        "{tool1}",
        "{tool2}",
    ],
    "graph": [
        # Select from: graphrag_lite, neo4j_framework_discovery,
        # graph_router, graph_orchestrator, pws_brain
        "graphrag_lite",  # Always include
        "{tool1}",
    ],
    "analysis": [
        # Select from: problem_classifier, assessment_engine,
        # grading_workflow, validation_workflow, opportunity_bank
        "{tool1}",
    ],
    "workshop": [
        # If has_phases=True, include:
        "smart_phase_tracker",
        "phase_insights",
    ],
    "extraction": [
        "langextract",  # Always include
        # Optional: google_langextract, result_synthesizer, document_ai
    ],
    "visualization": [
        "diagrams",  # Always include
        # Optional: charts, ui_elements, image_generation
    ],
    "quality": [
        "dynamic_examples",  # Always include
        # Optional: quality_scorer, insight_extractor
    ],
    "context": [
        "context_persistence",  # Always include
        # If workshop: gemini_rag
    ],
}
```

---

# SECTION 3: NEO4J GRAPH QUERIES

## COMPONENT J: RECOMMENDED GRAPH QUERIES
```cypher
// Query 1: Find relevant frameworks for this methodology
MATCH (f:Framework)-[:ADDRESSES_PROBLEM_TYPE]->(pt:ProblemType)
WHERE f.name CONTAINS '{methodology_keyword}'
   OR pt.name CONTAINS '{problem_type}'
RETURN f.name, f.description, pt.name
LIMIT 10;

// Query 2: Find related concepts
MATCH (c:Concept)-[r]-(related)
WHERE c.name CONTAINS '{core_concept}'
RETURN c.name, type(r), related.name
LIMIT 20;

// Query 3: Find case studies
MATCH (cs:CaseStudy)-[:EXEMPLIFIES]->(c:Concept)
WHERE c.name CONTAINS '{methodology_keyword}'
RETURN cs.name, cs.description, c.name
LIMIT 5;

// Query 4: Find complementary frameworks
MATCH (f1:Framework)-[:COMPLEMENTS]->(f2:Framework)
WHERE f1.name CONTAINS '{methodology}'
RETURN f1.name, f2.name, f2.description
LIMIT 5;
```

## COMPONENT K: GRAPH WRITE TEMPLATES (for knowledge addition)
```cypher
// Pre-flight checklist:
// WHAT: Creating {node_type} nodes for {purpose}
// WHY: Enables {benefit for Larry/users}
// HOW: Using MERGE to prevent duplicates, batch ≤200

// Add methodology concepts
MERGE (c:Concept {name: "{Concept Name}"})
SET c.description = "{Description}",
    c.methodology = "{bot_id}",
    c.added_by = "agent-generator",
    c.added_date = date()
RETURN c;

// Link to framework
MATCH (c:Concept {name: "{Concept Name}"})
MATCH (f:Framework {name: "{Framework Name}"})
MERGE (c)-[r:PART_OF]->(f)
SET r.added_by = "agent-generator"
RETURN c.name, f.name;
```

---

# SECTION 4: MICRO SUB-AGENTS (Optional)

If the agent needs specialized sub-agents:

## COMPONENT L: SUB-AGENT DEFINITIONS
```python
{BOT_ID}_SUB_AGENTS = {
    "{sub_agent_1}": {
        "name": "{Sub-Agent Name}",
        "role": "{What it does}",
        "trigger": "{When to invoke}",
        "prompt_suffix": "{Additional instructions}",
        "tools": ["{tool1}", "{tool2}"],
    },
    "{sub_agent_2}": {
        "name": "{Sub-Agent Name}",
        "role": "{What it does}",
        "trigger": "{When to invoke}",
        "prompt_suffix": "{Additional instructions}",
        "tools": ["{tool1}", "{tool2}"],
    },
}
```

---

# SECTION 5: MEDIA CONFIGURATION (Optional)

## COMPONENT M: VIDEO URLS
```python
# Add to utils/media.py → WORKSHOP_VIDEOS

WORKSHOP_VIDEOS["{bot_id}"] = {
    "intro": "",  # Add URL when available
    "phase_1": "",
    "phase_2": "",
    # ... one per phase
}
```

## COMPONENT N: AUDIOBOOK CHAPTERS
```python
# Add to utils/media.py → AUDIOBOOK_CHAPTERS

AUDIOBOOK_CHAPTERS["{methodology_topic}"] = {
    "chapter_1": {
        "title": "{Chapter Title}",
        "url": "",  # Add URL when available
        "duration": "15:00",
        "keywords": ["{keyword1}", "{keyword2}"],
        "bot_relevance": ["{bot_id}"],
    },
}
```

---

# SECTION 6: VALIDATION CHECKLIST

After generating all components, verify:

## TIER 1: Core (ALL must pass)
- [ ] System prompt file created with proper structure
- [ ] Prompt exported in prompts/__init__.py
- [ ] BOTS dict entry has ALL required fields
- [ ] Chat profile added to chat_profiles()
- [ ] 4 conversation starters with valid icon paths

## TIER 2: Workshop (if has_phases=True)
- [ ] WORKSHOP_PHASES defined with completion keywords
- [ ] Phase goals described in system prompt
- [ ] smart_phase_tracker can detect completion

## TIER 3: Dynamic (ALL must pass)
- [ ] AGENT_TRIGGERS with 5+ keywords
- [ ] Action callback "switch_to_{bot_id}" defined
- [ ] ThinkingPanel color added
- [ ] BOT_TO_METHODOLOGY entry
- [ ] BOT_TO_CASE_TOPICS entry
- [ ] STATIC_EXAMPLES (3-5 examples)

## TIER 4: Knowledge (if RAG-enabled)
- [ ] Neo4j queries defined
- [ ] Graph write templates with pre-flight
- [ ] Concepts linked to existing frameworks

## TIER 5: Integration
- [ ] Tool stack matches agent purpose
- [ ] Sub-agents defined if complex
- [ ] Media URLs placeholder ready

---

# GENERATION INSTRUCTIONS

1. **Read the intake carefully** - Extract all identity, knowledge, and tool requirements
2. **Match to tool stack** - Select appropriate tools from MINDRIAN_TOOL_STACK
3. **Generate ALL components** - Don't skip any required section
4. **Use exact formats** - Follow the Python/Cypher templates precisely
5. **Include validation** - Mark each checklist item
6. **Suggest a color** - Pick a unique ThinkingPanel color not already used

## OUTPUT FORMAT

Your response should include:
1. Brief analysis of the intake
2. All components (A through N as applicable)
3. Completed validation checklist
4. Any warnings or recommendations

---

# EXAMPLE INTAKE → OUTPUT

## Example Intake:
"Create a 'Camera Test' bot that helps users validate assumptions using evidence.
It should be skeptical but supportive, asking for data to back claims.
Uses Triple Validation framework."

## Example Output Summary:
- bot_id: camera_test
- Archetype: Skeptical Validator
- Phases: Evidence Gathering → Assumption Testing → Validation Synthesis
- Tools: validation_workflow, assessment_engine, dataset_search, govdata_search
- Color: #f97316 (orange - represents caution/verification)
- Keywords: validate, assumption, evidence, prove, data, verify, test

[Full component output would follow...]

---

Now analyze the intake provided and generate the complete agent configuration.
'''


# =============================================================================
# TIER VALIDATION HELPER
# =============================================================================

def validate_agent_config(config: dict) -> dict:
    """
    Validate that an agent configuration has all required components.

    Args:
        config: Dictionary with bot_id and all component values

    Returns:
        Dictionary with validation results for each tier
    """
    results = {
        "tier1_core": {"passed": False, "missing": []},
        "tier2_workshop": {"passed": False, "missing": [], "skipped": False},
        "tier3_dynamic": {"passed": False, "missing": []},
        "tier4_knowledge": {"passed": False, "missing": [], "skipped": False},
        "tier5_integration": {"passed": False, "missing": []},
    }

    # TIER 1: Core
    tier1_required = ["system_prompt", "starters", "bots_entry", "chat_profile"]
    results["tier1_core"]["missing"] = [
        r for r in tier1_required if r not in config or not config[r]
    ]
    results["tier1_core"]["passed"] = len(results["tier1_core"]["missing"]) == 0

    # TIER 2: Workshop (only if has_phases)
    if config.get("has_phases", False):
        tier2_required = ["workshop_phases", "phase_completion_keywords"]
        results["tier2_workshop"]["missing"] = [
            r for r in tier2_required if r not in config or not config[r]
        ]
        results["tier2_workshop"]["passed"] = len(results["tier2_workshop"]["missing"]) == 0
    else:
        results["tier2_workshop"]["skipped"] = True
        results["tier2_workshop"]["passed"] = True

    # TIER 3: Dynamic
    tier3_required = ["agent_triggers", "action_callback", "thinking_color",
                      "bot_to_methodology", "static_examples"]
    results["tier3_dynamic"]["missing"] = [
        r for r in tier3_required if r not in config or not config[r]
    ]
    results["tier3_dynamic"]["passed"] = len(results["tier3_dynamic"]["missing"]) == 0

    # TIER 4: Knowledge (optional but validated if present)
    if config.get("rag_enabled", False):
        tier4_required = ["neo4j_queries", "graph_write_templates"]
        results["tier4_knowledge"]["missing"] = [
            r for r in tier4_required if r not in config or not config[r]
        ]
        results["tier4_knowledge"]["passed"] = len(results["tier4_knowledge"]["missing"]) == 0
    else:
        results["tier4_knowledge"]["skipped"] = True
        results["tier4_knowledge"]["passed"] = True

    # TIER 5: Integration
    tier5_required = ["tool_stack"]
    results["tier5_integration"]["missing"] = [
        r for r in tier5_required if r not in config or not config[r]
    ]
    results["tier5_integration"]["passed"] = len(results["tier5_integration"]["missing"]) == 0

    return results


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "AGENT_GENERATOR_META_PROMPT",
    "MINDRIAN_TOOL_STACK",
    "THINKINGPANEL_COLORS",
    "validate_agent_config",
]
