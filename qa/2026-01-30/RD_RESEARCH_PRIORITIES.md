# R&D Research Priorities - Future Mindrian Additions

**Date:** 2026-01-30
**Purpose:** Document potential additions to investigate based on R&D library review

---

## Current R&D Status Summary

| # | R&D Topic | Status | Priority |
|---|-----------|--------|----------|
| 01 | Pipeline Adapters | Research | HIGH |
| 02 | Synthetic Data Generation | Research | MEDIUM |
| 03 | Smart Router | Partial | HIGH |
| 04 | Voice Improvements | Partial | MEDIUM |
| 05 | Conversation Quality Scoring | Research | LOW |
| 06 | Workshop Pipeline Engine | Research | HIGH |
| 07 | Audiobook Content | TODO | HIGH |
| 08 | Video Tutorials | TODO | HIGH |
| 09 | GraphRAG Lite | **DONE** | - |
| 10 | GraphRAG Knowledge Base | **ACTIVE** | HIGH |
| 11 | Gemini Deep Research | Research | MEDIUM |
| 12 | Smart Phase Transitions | **DONE** | - |
| 13 | Custom Elements | **DONE** | - |
| 14 | OAuth Authentication | **DONE** | - |
| 15 | LangGraph Visualization | **DONE** | - |
| 16 | v4.0 Architecture | **ANALYSIS** | HIGH |

---

## HIGH PRIORITY INVESTIGATIONS

### 1. Multi-Agent Pipelines (v4.0)
**What:** Automated workflows chaining multiple bots together
**Why:** Users currently manually switch bots; orchestrated flows would provide guided experiences
**Research Areas:**
- LangGraph orchestration patterns
- Preset pipeline definitions (Startup Validation, Trend Analysis, Problem Deep Dive)
- Cross-bot context passing
- Visual pipeline progress with `cl.Step`

**Estimated Effort:** 12-20 hours
**Reference:** `R&D/16_v4_architecture/README.md`

---

### 2. Cynefin Cognitive Router
**What:** Problem complexity classification driving bot selection
**Why:** 85% of infrastructure exists but not exposed to routing decisions
**Research Areas:**
- Cynefin domain classification (Clear/Complicated/Complex/Chaotic)
- Bot boosting based on problem type
- UI exposure of classification
- Auto-suggestions based on Cynefin domain

**Estimated Effort:** 4-8 hours
**Reference:** `R&D/16_v4_architecture/README.md`

---

### 3. Workshop Pipeline Engine
**What:** Formalized state machine for workshop phase progression
**Why:** Current phase tracking is loose; no validation of completion
**Research Areas:**
- Entry/exit criteria per phase
- Required activities with minimum exchanges
- Structured data capture per phase
- Phase lock warnings

**Estimated Effort:** 30-40 hours
**Reference:** `R&D/06_workshop_pipeline_engine/README.md`

---

### 4. Pipeline Adapters
**What:** Methodology-specific enhancements to base Larry without full bot switch
**Why:** Enables composable methodology combinations (TTA + Red Team)
**Research Areas:**
- Adapter interface design
- Prompt enhancement patterns
- Lightweight vs. full methodology activation
- User-controlled adapter toggles

**Estimated Effort:** 16-22 hours
**Reference:** `R&D/01_pipeline_adapters/README.md`

---

### 5. Smart Router
**What:** Intent-based automatic methodology selection
**Why:** New users don't know which bot to choose
**Research Areas:**
- 3-level classification (Keyword → LLM → Multi-methodology)
- Auto-route vs. suggestion thresholds
- First-message analysis
- User override patterns

**Estimated Effort:** 12-15 hours
**Reference:** `R&D/03_smart_router/README.md`

---

## MEDIUM PRIORITY INVESTIGATIONS

### 6. Gemini Deep Research Integration
**What:** 5-20 minute autonomous research agent (30-50+ sources)
**Why:** Current Tavily search is surface-level; deep research provides comprehensive synthesis
**Research Areas:**
- Interactions API integration
- LazyGraphRAG query enrichment
- Long-running task UX patterns
- Report storage and retrieval

**Cost Consideration:** $2-5 per run
**Estimated Effort:** 8-12 hours
**Reference:** `R&D/11_gemini_deep_research/README.md`

---

### 7. Synthetic Data Generation for PWS Training
**What:** Generate fine-tuning data from quality conversations
**Why:** Could enable faster, PWS-specific local models
**Research Areas:**
- Quality conversation capture pipeline
- Variation generation with GPT-4
- LoRA/QLoRA fine-tuning on Mistral/Llama
- A/B testing fine-tuned vs. Gemini

**Estimated Effort:** 6+ weeks (long-term)
**Reference:** `R&D/02_synthetic_data_generation/README.md`

---

### 8. Voice Improvements
**What:** Enhanced voice input/output patterns
**Research Areas:**
- ElevenLabs streaming SDK patterns
- Voice activity detection improvements
- Multi-voice personas per bot
- Voice cloning for consistent Larry voice

**Reference:** `R&D/04_voice_improvements/README.md`

---

### 9. Reverse Salient Cross-Intersectional Discovery
**What:** Find innovation opportunities at concept intersections
**Why:** 233 ReverseSalient nodes exist but not utilized
**Research Areas:**
- Bottleneck/gap identification from graph
- Cross-domain bridging queries
- Innovation opportunity scoring
- Automatic opportunity bank population

**Reference:** `R&D/10_graphrag_knowledge_base/REVERSE_SALIENT_SPEC.md`

---

## NEW RESEARCH AREAS TO INVESTIGATE

Based on current codebase analysis and industry trends:

### 10. Agentic Workflows with Tool Use
**What:** LLM agents that dynamically select and use tools
**Why:** Current tool use is predefined; agentic patterns would enable dynamic problem-solving
**Research Areas:**
- ReAct pattern implementation
- Tool selection reasoning
- Multi-step planning
- Error recovery and retry patterns

**Resources:**
- Anthropic Claude tool use patterns
- LangChain agents
- OpenAI function calling

---

### 11. Memory Systems
**What:** Long-term user context beyond session
**Why:** Currently each session starts fresh; returning users must re-explain context
**Research Areas:**
- User preference storage
- Problem history tracking
- Cross-session assumption tracking
- Personalized bot responses based on history

**Resources:**
- Mem0 (memory layer for LLMs)
- LangChain memory modules
- Vector-based user context retrieval

---

### 12. Collaborative Workspaces
**What:** Multi-user workshop sessions
**Why:** PWS methodology often involves teams
**Research Areas:**
- Real-time collaboration in Chainlit
- Role-based contributions
- Shared artifact editing
- Team progress tracking

---

### 13. Structured Output Validation
**What:** Guaranteed schema compliance for LLM outputs
**Why:** Grading and assessment need reliable structured data
**Research Areas:**
- Pydantic models for output validation
- Retry with schema correction
- Instructor library patterns
- Gemini structured output mode

---

### 14. RAG Quality Improvements
**What:** Better retrieval accuracy and context relevance
**Research Areas:**
- Hybrid search (BM25 + vector)
- Reranking with cross-encoders
- Query expansion techniques
- Chunk overlap optimization

---

### 15. Evaluation and Monitoring
**What:** Systematic quality measurement
**Research Areas:**
- LLM response quality metrics
- User engagement analytics
- A/B testing framework
- Automated regression testing

**Resources:**
- LangSmith
- Braintrust
- Arize Phoenix

---

### 16. Model Context Protocol (MCP) Expansion
**What:** Additional MCP tools for specialized capabilities
**Research Areas:**
- Database querying tools
- Code execution sandboxes
- Document generation tools
- Calendar/scheduling integration

---

### 17. Export and Integration
**What:** Better output formats for external tools
**Research Areas:**
- Notion integration
- Google Docs export
- Miro/FigJam visualization export
- PowerPoint/Slides generation

---

## IMPLEMENTATION ROADMAP

### Week 1-2: Quick Wins (12-20 hours)
- [ ] Cynefin UI exposure
- [ ] Devil's Advocate mode toggle
- [ ] Beautiful Questions auto-trigger
- [ ] Audiobook/video URL population

### Week 3-4: Intelligence Layer (20-30 hours)
- [ ] Smart Router implementation
- [ ] Multi-agent pipeline basics
- [ ] Assumption tracking across bots

### Month 2: Advanced Features (40-60 hours)
- [ ] Full Workshop Pipeline Engine
- [ ] Gemini Deep Research integration
- [ ] Reverse Salient discovery queries

### Month 3+: Long-term Investments
- [ ] Synthetic data generation
- [ ] Fine-tuned PWS model
- [ ] Memory systems
- [ ] Collaborative workspaces

---

## EXTERNAL RESOURCES TO MONITOR

| Resource | Why | URL |
|----------|-----|-----|
| Chainlit Changelog | New features/elements | https://docs.chainlit.io/changelog |
| Google AI Blog | Gemini updates | https://ai.googleblog.com/ |
| Anthropic Research | Claude patterns | https://www.anthropic.com/research |
| LangChain Blog | Agent patterns | https://blog.langchain.dev/ |
| Simon Willison's Blog | LLM tooling | https://simonwillison.net/ |

---

## KEY QUESTIONS FOR FURTHER RESEARCH

1. **Adapter vs. Bot Pattern:** Is composable methodology better than full bot switching?
2. **Deep Research ROI:** At $2-5 per query, when is Deep Research worth it?
3. **Fine-tuning Viability:** Would a PWS-specific Mistral 7B outperform Gemini for coaching?
4. **Memory Trade-offs:** How much user context helps vs. privacy concerns?
5. **Multi-user Complexity:** Is collaborative PWS worth the implementation effort?

---

*Last Updated: 2026-01-30*
