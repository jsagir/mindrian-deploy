---
description: End-to-end integration testing of all new features
---

# Step 5: Integration Testing

## Goal
Verify all new features (Idea Engine, Tool Router, Intent Analyzer, Spark Generator) work together seamlessly and don't break existing functionality.

## Test Scenarios

### Scenario 1: New User Journey
1. User arrives with no context: "I want to explore AI in education"
2. Verify: Onboarding flow activates, intent = explore
3. User discusses for 5 turns
4. Verify: Ideas captured in LazyGraph, connections forming
5. User asks a specific question
6. Verify: Tool router suggests research (auto or button)
7. Research runs
8. Verify: Results stored in LightRAG, sources valid (no homepage URLs)

### Scenario 2: Power User Deep Session
1. User with history discusses a complex topic
2. Verify: Previous session context loaded from LazyGraph
3. After 10 turns, cross-domain spark fires
4. Verify: Connection is genuinely novel (not obvious)
5. User clicks "Map My Ideas"
6. Verify: Mermaid mindmap renders with all session ideas
7. User triggers convergence ("Give me your answer")
8. Verify: Synthesis includes all accumulated evidence

### Scenario 3: Multi-Tool Chain
1. User describes a business problem
2. Verify: Tool router chains research → validation → visualization
3. Each tool feeds into the next
4. Verify: Final output includes research evidence, validation results, visual

### Scenario 4: Existing Feature Regression
1. Workshop phases still advance correctly
2. Agent triggers still work
3. Settings (response detail slider, research depth) still function
4. Context preservation across bot switches intact
5. Voice input/output still works
6. File upload still handles PDF, DOCX

## Files to Verify

| File | Check |
|------|-------|
| `mindrian_chat.py` | Syntax check, all imports resolve |
| `tools/idea_engine.py` | Unit tests pass |
| `intelligence/tool_router.py` | Classification accuracy |
| `intelligence/intent_analyzer.py` | Intent detection accuracy |
| `intelligence/spark_generator.py` | Connection quality |
| `intelligence/pipelines/research_pipeline.py` | All 3 tiers work |

## Validation
```bash
python3 scripts/health_check.py
python3 -c "import ast; [ast.parse(open(f).read()) for f in ['mindrian_chat.py', 'tools/idea_engine.py', 'intelligence/tool_router.py', 'intelligence/intent_analyzer.py', 'intelligence/spark_generator.py', 'intelligence/pipelines/research_pipeline.py']]"
```
