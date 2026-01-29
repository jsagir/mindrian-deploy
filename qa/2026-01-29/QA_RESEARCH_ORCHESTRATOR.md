# QA Test Plan: Research Orchestrator & Result Synthesizer

**Date:** 2026-01-29
**Feature:** Advanced Research Workflow with AI Synthesis
**Status:** Ready for Testing

---

## Overview

Two new modules enhance Mindrian's research capabilities:

1. **Result Synthesizer** (`tools/result_synthesizer.py`) - AI-powered relevance scoring and PWS framing
2. **Research Orchestrator** (`tools/research_orchestrator.py`) - Full 5-phase Tavily workflow

---

## Test Cases

### TC-01: Quick Research (Lawrence - Simple Mode)

**Preconditions:** Using Lawrence bot (simple_mode=True)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start conversation with Lawrence | Welcome message appears |
| 2 | Ask: "What are the latest trends in AI regulation?" | Bot responds |
| 3 | Click 🔍 Research button | Research workflow starts |
| 4 | Observe output | Should show: Query, depth (Quick), phases progress |
| 5 | Check findings | Should have confidence indicators (🟢🟡🟠) |
| 6 | Verify sources | Each finding should have clickable source link |

**Expected Behavior:**
- Research depth: "Quick" (2 queries)
- Shows Key Insights, Research Findings, PWS Implications
- Completes in ~10-15 seconds

---

### TC-02: Standard Research (Larry Playground)

**Preconditions:** Using Larry Playground bot (simple_mode=False)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Switch to Larry Playground | Full-featured interface |
| 2 | Ask: "Should I pivot my SaaS to AI-native?" | Bot responds |
| 3 | Click 🔍 Research button | Research workflow starts |
| 4 | Observe phases | Should show all 6 phases |
| 5 | Check synthesis | Detailed synthesis with PWS framing |
| 6 | Verify actions | "Recommended Next Steps" section present |
| 7 | Check gaps | "Questions to Explore" section present |

**Expected Behavior:**
- Research depth: "Standard" (5 queries)
- Shows metadata: X queries | Y primary sources | Z secondary sources
- Completes in ~20-30 seconds

---

### TC-03: Deep Research (Advanced Depth Setting)

**Preconditions:** Larry Playground with research_depth="advanced" in settings

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open Settings (⚙️) | Settings panel opens |
| 2 | Set Research Depth to "Advanced" | Setting saved |
| 3 | Ask complex question | Bot responds |
| 4 | Click 🔍 Research | Deep workflow starts |
| 5 | Observe gap analysis | Follow-up queries should execute |
| 6 | Check source count | Should have more sources than Standard |

**Expected Behavior:**
- Research depth: "Deep" (8+ queries)
- Gap analysis generates follow-up queries
- Completes in ~30-45 seconds

---

### TC-04: Source Authority Scoring

**Objective:** Verify source categorization works correctly

| Source Type | Expected Authority | Category |
|-------------|-------------------|----------|
| .gov domains | 0.90-0.99 | Primary 🟢 |
| .edu domains | 0.85-0.92 | Primary 🟢 |
| Major news (NYT, BBC) | 0.70-0.80 | Secondary 🟡 |
| Tech blogs | 0.55-0.65 | Secondary 🟡 |
| Reddit, Quora | 0.35-0.45 | Weak 🟠 |

**Test:**
1. Research a topic with government data (e.g., "FDA drug approval process")
2. Verify .gov sources appear with higher confidence
3. Research a general topic
4. Verify diverse source categories

---

### TC-05: Query Decomposition

**Objective:** Verify complex questions are broken into atomic queries

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Ask: "What funding options exist for AI startups in Israel and how do I apply?" | Complex question |
| 2 | Click Research | Workflow starts |
| 3 | Check cl.Step output | Should show decomposed queries |

**Expected Decomposition:**
- Query 1: "Israel AI startup funding programs 2024 2025" (landscape)
- Query 2: "IIA Innovation Authority eligibility requirements" (specific)
- Query 3: "Israel tech grants application process" (how-to)
- Query 4: "Israel venture capital AI recent investments" (alternatives)

---

### TC-06: PWS Context Integration (GraphRAG)

**Objective:** Verify GraphRAG enriches queries with PWS context

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Ask about a PWS-related topic | E.g., "How do I validate my startup idea?" |
| 2 | Click Research | Workflow runs |
| 3 | Check synthesis | Should reference PWS frameworks |
| 4 | Verify PWS Implications | Section should mention relevant concepts |

**Expected PWS Context:**
- References to frameworks (Camera Test, JTBD, etc.)
- Problem type classification
- Relevant approaches from knowledge graph

---

### TC-07: LangExtract Integration

**Objective:** Verify structured insight extraction works

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Research a data-rich topic | E.g., "Electric vehicle market size 2025" |
| 2 | Check findings | Should extract statistics |
| 3 | Verify assumptions | Should identify implicit assumptions |

**Expected Extractions:**
- Statistics: Market sizes, growth rates, percentages
- Assumptions: Implicit beliefs in sources
- Questions: Open questions raised by research

---

### TC-08: Fallback Behavior

**Objective:** Verify graceful degradation when advanced features fail

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Trigger research with network issues | Simulated/real network problem |
| 2 | Check error handling | Should show fallback message |
| 3 | Verify simple search runs | Basic Tavily search as fallback |
| 4 | Results displayed | Basic source list without synthesis |

---

### TC-09: Result Synthesizer Standalone

**Objective:** Test synthesizer with different source types

```python
# Test code for developers
from tools.result_synthesizer import synthesize_results, quick_synthesize

# Test with web results
result = await synthesize_results(
    raw_results={"results": [...]},
    source_type="web",
    user_context="Exploring market opportunity",
    bot_id="lawrence"
)

# Verify output structure
assert result.get("success") == True
assert "relevant_findings" in result
assert "synthesis_summary" in result
```

---

### TC-10: Research Orchestrator Performance

**Objective:** Verify acceptable performance

| Research Depth | Max Time | Queries | Sources |
|----------------|----------|---------|---------|
| Quick | 15 sec | 2 | 5-10 |
| Standard | 30 sec | 5 | 15-25 |
| Deep | 60 sec | 8+ | 30-50 |

---

## Integration Points

### Files Modified

| File | Change |
|------|--------|
| `tools/result_synthesizer.py` | NEW - AI synthesis module |
| `tools/research_orchestrator.py` | NEW - Full workflow |
| `tools/__init__.py` | Added exports |
| `tools/tool_dispatcher.py` | Added synthesized execution |
| `mindrian_chat.py` | Updated `_research_sources_first()` |

### Dependencies

- Tavily API (TAVILY_API_KEY)
- Gemini API (GOOGLE_API_KEY)
- GraphRAG (optional - graceful fallback)
- LangExtract (optional - graceful fallback)

---

## Known Limitations

1. **Rate Limits:** Deep research may hit Tavily rate limits with many queries
2. **Timeout:** Very deep research (8+ queries) may timeout on slow connections
3. **GraphRAG:** If Neo4j is unavailable, PWS context is limited
4. **Synthesis Quality:** Depends on source quality; garbage in = garbage out

---

## Rollback Plan

If issues arise, revert `_research_sources_first()` in `mindrian_chat.py` to the previous simple implementation (git history commit before `6694436`).

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | Claude | 2026-01-29 | Complete |
| QA Tester | | | Pending |
| Product Owner | | | Pending |
