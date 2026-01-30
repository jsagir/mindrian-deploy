# Mindrian R&D - Research & Development Backlog

This folder contains research, ideas, and implementation plans for future Mindrian enhancements.

Each subfolder represents a feature or capability that has been researched but not yet fully implemented.

---

## Folder Structure

| Folder | Priority | Status | Description |
|--------|----------|--------|-------------|
| `01_pipeline_adapters` | HIGH | Research | Modular adapter system inspired by GIA-LLM |
| `02_synthetic_data_generation` | MEDIUM | Research | Generate training data from conversations |
| `03_smart_router` | HIGH | Partial | Intent-based routing to best methodology |
| `04_voice_improvements` | MEDIUM | Partial | ElevenLabs patterns + OpenAI Realtime evaluation |
| `05_conversation_quality_scoring` | LOW | Research | Automated quality assessment of responses |
| `06_workshop_pipeline_engine` | HIGH | Research | Formalized phase progression as true pipeline |
| `07_audiobook_content` | HIGH | TODO | PWS audiobook chapter URLs need to be added |
| `08_video_tutorials` | HIGH | TODO | Workshop video URLs need to be added |
| `09_graphrag_lite` | - | **DONE** | Neo4j + Vector hybrid RAG for conversational context |
| `10_graphrag_knowledge_base` | HIGH | **ACTIVE** | Graph schema, skill file, problem taxonomy, reverse salient spec |
| `11_gemini_deep_research` | MEDIUM | Research | Gemini's Deep Research API integration |
| `12_smart_phase_transitions` | - | **DONE** | LangExtract + LazyGraph for intelligent phase progression |
| `13_custom_elements` | - | **DONE** | Custom JSX elements + AskElementMessage forms |
| `14_oauth_authentication` | - | **DONE** | Google/GitHub OAuth social login |
| `15_langgraph_visualization` | - | **DONE** | Chainlit cl.Step integration for LangGraph workflows |
| `16_v4_architecture` | HIGH | **ANALYSIS** | v4.0 Cynefin Router + Devil's Advocate + Multi-Agent Pipelines |
| `17_agentic_tool_use` | HIGH | Research | ReAct pattern, dynamic tool selection |
| `18_memory_systems` | MEDIUM | Research | Long-term user context, cross-session tracking |
| `19_collaborative_workspaces` | LOW | Research | Multi-user workshop sessions |
| `20_structured_output` | HIGH | Research | Pydantic validation, Instructor patterns |
| `21_rag_quality` | MEDIUM | Research | Hybrid search, reranking, query expansion |
| `22_evaluation_monitoring` | MEDIUM | Research | Quality metrics, A/B testing, regression tests |
| `23_mcp_expansion` | MEDIUM | Research | Additional MCP tools (Notion, code sandbox, etc.) |
| `24_export_integration` | MEDIUM | Research | Slides, Notion, Google Docs, Miro exports |

---

## Recent Implementations (2026-01-30)

### Custom UI Elements
- **GradeReveal.jsx**: Soft-landing grade reveal with 5 stages
- **ScoreBreakdown.jsx**: Interactive component drill-down
- **OpportunityCard.jsx**: Bank of Opportunities cards
- **ui_elements.py**: Python helper module for all UI elements

### Assessment Engine v3.1
- Evidence tagging by source (neo4j_*, filesearch_*, tavily_*, gemini_*)
- Quality gates per module
- Minto grading integration

---

## Implementation Priority

### Phase 1: Quick Wins (Week 1) - 12 hours
- [ ] Expose Cynefin domain in UI
- [ ] Cynefin-aware bot boosting
- [ ] Devil's Advocate mode toggle
- [ ] Beautiful Questions auto-trigger
- [ ] Add audiobook chapter URLs
- [ ] Add video tutorial URLs

### Phase 2: Intelligence (Week 2-3) - 30 hours
- [ ] Smart Router implementation
- [ ] Multi-agent pipeline basics
- [ ] Assumption tracking across bots
- [ ] Structured output validation

### Phase 3: Advanced (Week 4+) - 40 hours
- [ ] Full Workshop Pipeline Engine
- [ ] Gemini Deep Research integration
- [ ] Reverse Salient discovery queries
- [ ] Agentic tool use patterns

### Phase 4: Long-term Investments
- [ ] Synthetic data generation
- [ ] Fine-tuned PWS model
- [ ] Memory systems
- [ ] Collaborative workspaces
- [ ] Export integrations

---

## Quick Links

- **GIA-LLM Documentation**: https://gia-llm.readthedocs.io/en/latest/
- **Meta Synthetic Data Kit**: https://github.com/meta-llama/synthetic-data-kit
- **LLM-Adapters Framework**: https://github.com/AGI-Edgerunners/LLM-Adapters
- **Chainlit Documentation**: https://docs.chainlit.io/
- **Chainlit Custom Elements**: https://docs.chainlit.io/custom-elements
- **MCP Specification**: https://modelcontextprotocol.io/
- **Instructor Library**: https://github.com/jxnl/instructor

---

## Research Questions

1. **Adapter vs. Bot Pattern:** Is composable methodology better than full bot switching?
2. **Deep Research ROI:** At $2-5 per query, when is Deep Research worth it?
3. **Fine-tuning Viability:** Would a PWS-specific Mistral 7B outperform Gemini for coaching?
4. **Memory Trade-offs:** How much user context helps vs. privacy concerns?
5. **Multi-user Complexity:** Is collaborative PWS worth the implementation effort?
6. **Agentic vs. Explicit:** Should tool use be autonomous or user-triggered?

---

## External Resources to Monitor

| Resource | Why | URL |
|----------|-----|-----|
| Chainlit Changelog | New features/elements | https://docs.chainlit.io/changelog |
| Google AI Blog | Gemini updates | https://ai.googleblog.com/ |
| Anthropic Research | Claude patterns | https://www.anthropic.com/research |
| LangChain Blog | Agent patterns | https://blog.langchain.dev/ |
| Simon Willison's Blog | LLM tooling | https://simonwillison.net/ |

---

*Last Updated: 2026-01-30*
