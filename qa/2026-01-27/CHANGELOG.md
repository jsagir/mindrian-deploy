# QA Changelog — 2026-01-27

## Session Summary

Four commits pushed to `main` today. The primary feature is the **LangExtract Intelligence Layer** — an invisible coaching system that runs on every message. Secondary changes include new research tools, a Neo4j schema rename, and upload scripts.

---

## Commits Made Today

| Commit | Message |
|--------|---------|
| `4e683a9` | refactor: Rename MCPTool to ResearchTool in graph orchestrator and tool dispatcher |
| `5269a73` | feat: Add research tool modules (govdata, trends, dataset, news) with caching |
| `ca21048` | feat: Add LangExtract Intelligence Layer — invisible coaching on every message |
| `d6517fe` | chore: Add LightRAG upload scripts and progress tracking |

---

## Detailed Change Log

### 1. LangExtract Intelligence Layer (`ca21048`)

**Files:** `mindrian_chat.py`, `tools/langextract.py`

#### What Changed

| Location | Change |
|----------|--------|
| `mindrian_chat.py` ~line 4231 | `instant_extract()` now runs on every user message before GraphRAG. Stores signals in `cl.user_session["last_extraction"]`. |
| `mindrian_chat.py` ~line 4253 | `get_extraction_hint()` appends a 1-sentence coaching instruction to `full_user_message` based on signals. |
| `mindrian_chat.py` ~line 4451 | `background_intelligence()` fires as async task every ~5 turns. Stores coherence metrics in `cl.user_session["extraction_coherence"]`. |
| `mindrian_chat.py` ~line 967 | `suggest_agents_from_context()` now adds extraction-driven scores: ackoff +0.4 (solution w/o problem), redteam +0.4 (assumptions >= 2), tta +0.3 (forward-looking). |
| `mindrian_chat.py` ~line 1029 | `suggest_research_tools()` now has Layer 0: extraction signals drive arxiv (certainty w/o data), trends (forward-looking), news (assumptions >= 3), govdata/dataset (low coherence grounding). |
| `tools/langextract.py` end of file | New function `get_extraction_hint()` — returns coaching hints like "Redirect to problem definition" or "Ask what evidence supports this". |
| `tools/langextract.py` end of file | New function `background_intelligence()` — async deep extraction, stores coherence metrics, caches to Supabase. |

#### How It Works

```
User sends message
  |-- instant_extract() runs (<5ms, regex only)
  |-- Signals stored in session
  |-- get_extraction_hint() generates coaching instruction
  |-- Hint appended to system context (invisible to user)
  |-- Bot responds with better coaching
  |-- After response: background_intelligence() fires every ~5 turns
  |      |-- Deep LLM extraction
  |      |-- Coherence metrics stored in session
  |      |-- Cached to Supabase
```

#### Why

- Larry/Lawrence becomes adaptive: redirects solution-focused users, probes assumptions, asks for evidence
- Agent suggestions get smarter: Red Team appears when assumptions pile up
- Research tool buttons become more targeted: Academic Evidence when claims lack sources
- Zero UI changes, zero latency impact

#### What QA Should Expect

- **Solution-jumping:** Saying "We should build X" without defining a problem -> Larry redirects to problem definition
- **Assumptions:** 2+ messages with "assuming that..." -> Red Team agent suggestion appears
- **High certainty:** "This is definitely right" with no sources -> ArXiv button appears
- **Forward-looking:** "By 2030..." -> TTA suggestion + Trends button
- **After 5+ turns:** Background extraction runs silently; check Supabase `extractions/` for new entries
- **"Extract Insights" button:** Still works exactly as before (no regression)

---

### 2. Neo4j Schema Rename (`4e683a9`)

**Files:** `tools/graph_orchestrator.py`, `tools/tool_dispatcher.py`

#### What Changed

| Before | After |
|--------|-------|
| Node label `MCPTool` | `ResearchTool` |
| Relationship `ORCHESTRATES_MCP` | `USES_TOOL` |
| Relationship `USES_MCP` | `USES_TOOL` |

All Cypher queries updated. All docstrings updated.

#### Why

The Neo4j graph schema was updated to use clearer, non-MCP-specific naming. `ResearchTool` better describes what these nodes represent.

#### What QA Should Expect

- Graph-driven research tool suggestions should work identically
- If Neo4j is down, graceful degradation (unchanged behavior)
- **Prerequisite:** The Neo4j database itself must have the renamed labels/relationships. If it doesn't, graph queries will return empty (but won't error — just no graph-based suggestions)

---

### 3. New Research Tool Modules (`5269a73`)

**Files:** `tools/govdata_search.py`, `tools/trends_search.py`, `tools/dataset_search.py`, `tools/news_search.py`, `tools/research_cache.py`, `tools/README.md`

#### What Changed

New callable Python modules for 4 research tools:
- **Gov Data Search** — queries government statistics (BLS, FRED, Census)
- **Trends Search** — Google Trends interest data
- **Dataset Search** — discovers datasets from Kaggle, data.gov, etc.
- **News Search** — current news signal analysis

Shared `research_cache.py` provides Supabase-backed caching for all research results.

New `tools/README.md` documents the full tools directory.

#### Why

These tools were registered in the graph as `ResearchTool` nodes but had no Python implementation. Now the button callbacks (`govdata_search`, `trends_search`, `dataset_search`, `news_search`) can actually execute.

#### What QA Should Expect

- Clicking any of the 6 research buttons (ArXiv, Patents, Trends, Gov Data, Datasets, News) should execute and return results
- Results include a "Why" reason tooltip explaining why the button appeared
- Results are appended to conversation history
- Results cached in Supabase `research_cache/` bucket

---

### 4. LightRAG Upload Scripts (`d6517fe`)

**Files:** `scripts/lightrag_gentle_upload.py`, `scripts/lightrag_graph_push.py`, `scripts/lightrag_graph_progress.json`, `scripts/lightrag_upload_progress.json`

#### What Changed

Utility scripts for batch uploading content to LightRAG with progress tracking. Not user-facing.

#### What QA Should Expect

- No user-facing impact
- Scripts are in `scripts/` directory for admin use only

---

## Graph / Neo4j Schema Change

The Neo4j graph was updated in a prior session to rename:
- `MCPTool` nodes -> `ResearchTool` nodes
- `ORCHESTRATES_MCP` / `USES_MCP` relationships -> `USES_TOOL`

Today's code commits align the Python code with this schema change. The graph queries in `graph_orchestrator.py` now use `MATCH (f:Framework)-[:USES_TOOL]->(m:ResearchTool)` instead of the old MCP references.

**QA verification:** Run a conversation mentioning frameworks (e.g., "S-Curve analysis") and confirm research tool buttons still appear with graph-driven reasons.

---
