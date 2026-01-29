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
| `09_graphrag_lite` | HIGH | **DONE** | Neo4j + Vector hybrid RAG for conversational context |
| `10_graphrag_knowledge_base` | HIGH | **ACTIVE** | Graph schema, skill file, problem taxonomy, reverse salient spec |
| `11_gemini_deep_research` | MEDIUM | Research | Gemini's Deep Research API integration |
| `12_smart_phase_transitions` | HIGH | **DONE** | LangExtract + LazyGraph for intelligent phase progression |
| `13_custom_elements` | HIGH | **DONE** | Custom JSX elements + AskElementMessage forms |
| `14_oauth_authentication` | MEDIUM | **DONE** | Google/GitHub OAuth social login |
| `15_langgraph_visualization` | MEDIUM | **DONE** | Chainlit cl.Step integration for LangGraph workflows |
| `16_v4_architecture` | HIGH | **ANALYSIS** | v4.0 Cynefin Router + Devil's Advocate + Multi-Agent Pipelines |

---

## Recent Implementations (2026-01-29)

### Research Enhancement
- **Result Synthesizer**: AI-powered relevance scoring and PWS framing for all research tools
- **Research Orchestrator**: Full 5-phase Tavily workflow (Query Decomposition → Discovery → Evaluation → Extraction → Synthesis)
- **Source Authority Scoring**: .gov (0.98) > .edu (0.90) > news (0.75) > blogs (0.55) > forums (0.40)

### P0 Features
- **Custom JSX Elements**: PhaseProgress, DIKWPyramid, ResearchMatrix
- **ElementSidebar**: Reference materials with live phase checklist

### P1 Features
- **OAuth Authentication**: Google and GitHub social login
- **LangGraph Visualization**: `run_multi_agent_with_steps()` for transparent workflows

### P2 Features
- **OpenAI Realtime Evaluation**: Documented decision to keep Gemini+ElevenLabs
- **AskElementMessage Forms**: ScenarioSetupForm, ProblemDefinitionForm with validation

### v4.0 Architecture Analysis
- **Fit Assessment**: 85-90% of v4.0 infrastructure already exists
- **Key Gaps**: Cynefin UI exposure, Multi-agent pipelines, Cross-bot assumption tracking
- **Estimated Effort**: 50-60 hours for full v4.0 implementation

See `13_custom_elements/`, `14_oauth_authentication/`, `15_langgraph_visualization/`, `16_v4_architecture/` for details.

---

## Quick Links

- **GIA-LLM Documentation**: https://gia-llm.readthedocs.io/en/latest/
- **Meta Synthetic Data Kit**: https://github.com/meta-llama/synthetic-data-kit
- **LLM-Adapters Framework**: https://github.com/AGI-Edgerunners/LLM-Adapters
- **Chainlit Documentation**: https://docs.chainlit.io/
- **Chainlit Custom Elements**: https://docs.chainlit.io/custom-elements

---

## Implementation Priority

### Phase 1 (Immediate)
- [ ] Add audiobook chapter URLs to `utils/media.py`
- [ ] Add video tutorial URLs to `utils/media.py`
- [ ] Wire forms to action buttons (show_problem_form, show_scenario_form)

### Phase 2 (Short-term) - v4.0 Quick Wins
- [ ] Expose Cynefin domain classification in UI
- [ ] Add Cynefin-aware bot boosting to agent suggestions
- [ ] Add Devil's Advocate mode toggle to Red Team
- [ ] Auto-trigger Beautiful Questions based on conversation phase
- [ ] Implement Smart Router for automatic methodology selection
- [ ] Create Workshop Pipeline Engine for strict phase progression

### Phase 3 (Medium-term)
- [ ] Build adapter system for modular methodology enhancement
- [ ] Role-based access control with OAuth users

### Phase 4 (Long-term)
- [ ] Synthetic data generation from workshop transcripts
- [ ] Fine-tuned quality scoring model

---

*Last Updated: 2026-01-29*
