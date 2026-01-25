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
| `04_voice_improvements` | MEDIUM | Partial | Advanced ElevenLabs patterns (WebSocket, Agent API) |
| `05_conversation_quality_scoring` | LOW | Research | Automated quality assessment of responses |
| `06_workshop_pipeline_engine` | HIGH | Research | Formalized phase progression as true pipeline |
| `07_audiobook_content` | HIGH | TODO | PWS audiobook chapter URLs need to be added |
| `08_video_tutorials` | HIGH | TODO | Workshop video URLs need to be added |
| `09_graphrag_lite` | HIGH | **DONE** | Neo4j + Vector hybrid RAG for conversational context |

---

## Quick Links

- **GIA-LLM Documentation**: https://gia-llm.readthedocs.io/en/latest/
- **Meta Synthetic Data Kit**: https://github.com/meta-llama/synthetic-data-kit
- **LLM-Adapters Framework**: https://github.com/AGI-Edgerunners/LLM-Adapters
- **Chainlit Documentation**: https://docs.chainlit.io/

---

## Implementation Priority

### Phase 1 (Immediate)
- [ ] Add audiobook chapter URLs to `utils/media.py`
- [ ] Add video tutorial URLs to `utils/media.py`
- [ ] Test feedback system end-to-end

### Phase 2 (Short-term)
- [ ] Implement Smart Router for automatic methodology selection
- [ ] Create Workshop Pipeline Engine for strict phase progression

### Phase 3 (Medium-term)
- [ ] Build adapter system for modular methodology enhancement
- [ ] Implement advanced voice patterns (WebSocket streaming)

### Phase 4 (Long-term)
- [ ] Synthetic data generation from workshop transcripts
- [ ] Fine-tuned quality scoring model

---

*Last Updated: 2026-01-22*
