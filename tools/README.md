# Mindrian Research Tools — Developer Guide

## How This System Works

Mindrian uses a **graph-driven research tool orchestration** system. The user never manually picks a tool — the Neo4j knowledge graph decides which research buttons to show based on the conversation context.

### Architecture: 3-Layer Decision Engine

Every message goes through `suggest_research_tools()` in `mindrian_chat.py`, which runs 3 layers:

```
User message
    │
    ▼
┌─────────────────────────────────────────────────┐
│  LAYER 1: Graph Orchestrator                    │
│  graph_orchestrator.discover_research_plan()    │
│  Neo4j: ProblemType → Framework → ResearchTool       │
│  If ResearchTool name contains "arxiv" → show button │
│  If ResearchTool name contains "trend" → show button │
│  etc.                                           │
│  Also checks Technique names for signals        │
└─────────────────────┬───────────────────────────┘
                      │ (may find 0-6 tools)
                      ▼
┌─────────────────────────────────────────────────┐
│  LAYER 2: Problem Context                       │
│  graphrag_lite.get_problem_context()            │
│  "undefined/ill-defined" → Academic Evidence    │
│  "well-defined" → Prior Art & Patents           │
│  "emerging/evolving" → Trends                   │
│  "well-defined/complicated" → Gov Data          │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  LAYER 3: Bot-Specific Hints (fallback)         │
│  If graph is unavailable, each bot has           │
│  hardcoded hints for which tools are relevant   │
│  e.g. redteam → Academic Evidence, News Signal  │
│       scurve  → Patents, Trends, Gov Data       │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
            6 Possible Buttons
      (each with a "reason" tooltip)
```

### Neo4j Graph Path

The orchestrator traverses:
```
Challenge text
  → fulltext search → ProblemType node
    → PART_OF → CynefinDomain
    → ADDRESSES_PROBLEM_TYPE ← Framework
      → USES_TOOL → ResearchTool               ← THIS discovers which buttons to show
      → USES_TECHNIQUE → Technique
        → SUPPORTS ← ResearchTool              ← ALSO discovers buttons via techniques
```

### Every Button Has a Reason

Buttons are never shown without an explanation. The `reason` field (shown as tooltip/description) tells the user WHY this button appeared:
- `"Framework 'Trending to the Absurd' uses trend data"` (Layer 1)
- `"'Undefined Problem' problems need evidence grounding"` (Layer 2)
- `"Red Team challenges need counter-evidence"` (Layer 3)

---

## The 6 Research Tools

### 1. `arxiv_search.py` — Academic Evidence

**Button label:** 📚 Academic Evidence
**What it does:** Searches ArXiv for published academic papers to validate or challenge claims.
**API:** ArXiv API (free, no key required)
**Key functions:**
- `search_papers(query, max_results=5)` → `{"query", "papers": [...], "count"}`
- `search_for_validation(claim)` — search specifically for validation/challenge evidence
- `format_papers_markdown(results)` → formatted markdown with titles, authors, dates, links

**When the graph triggers it:**
- ResearchTool nodes: `ArXiv MCP Server`, `ArXiv Academic Search`, `ArXiv Research`
- Techniques containing: `validation`, `evidence`, `empirical`, `grounding`
- Bot hints: redteam (counter-evidence), ackoff (DIKW validation)

**Callback flow:**
1. Gemini extracts 8-word academic search query from conversation
2. Calls `search_papers()`
3. Formats results and injects into conversation history

---

### 2. `patent_search.py` — Prior Art & Patents

**Button label:** 🔎 Prior Art & Patents
**What it does:** Searches patent databases for existing inventions, prior art, innovation landscape.
**Key functions:**
- `search_patents(query, max_results=5)` → `{"query", "patents": [...], "count"}`
- `format_patents_markdown(results)` → formatted markdown

**When the graph triggers it:**
- ResearchTool nodes: `Google Patents MCP`, `Google Patents Search`
- Techniques containing: `prior art`, `landscape`, `innovation scan`, `patent`
- Problem context: "well-defined" problems → check if solutions already exist
- Bot hints: scurve (patent filing patterns)

---

### 3. `trends_search.py` — Trends

**Button label:** 📈 Trends
**What it does:** Fetches Google Trends data — interest over time, rising/declining direction, related queries.
**API:** SerpAPI Google Trends engine
**Env var:** `SERPAPI_API_KEY`
**Key functions:**
- `search_trends(query, data_type="TIMESERIES", date="today 12-m")` → timeseries data
- `search_related_queries(query)` → rising and top related queries
- `search_interest_over_time(query)` → convenience wrapper
- `format_trends_markdown(results)` → shows start/peak/latest values + direction (rising/declining/stable)

**When the graph triggers it:**
- ResearchTool node: `Google Trends Search`
- Connected to 8 Techniques: Trend Mapping, Trending to the Absurd, Trend Analysis, Domain & Trend Analysis, STEEP Analysis, Impact-Uncertainty Matrix, Pattern Detection, Emergent Pattern Sensing
- Connected from 9 Frameworks: Macro Trends, Megatrends, trend_detection_framework, etc.
- Technique signals containing: `trend`, `foresight`, `extrapolat`, `emerging`, `steep`, `pattern`
- Problem context: "emerging/evolving" problems
- Bot hints: scurve (adoption curves), tta (trend baselines)

**Callback flow:**
1. Gemini extracts 1-3 comma-separated trend terms
2. Fetches BOTH timeseries + related queries in parallel
3. Shows direction analysis (rising/declining/stable)

---

### 4. `govdata_search.py` — Gov Data

**Button label:** 🏛️ Gov Data
**What it does:** Queries 3 US federal data sources for real economic/demographic/labor statistics.
**APIs:**
- **BLS** (Bureau of Labor Statistics) — unemployment, CPI, wages, productivity. No key needed.
- **FRED** (Federal Reserve Economic Data) — GDP, interest rates, consumer sentiment. Env: `FRED_API_KEY`
- **Census ACS** (American Community Survey) — population, income, education, housing. Env: `DATA_GOV_API_KEY`

**Key functions:**
- `search_bls(query)` — matches query to known BLS series (unemployment, CPI, payroll, etc.)
- `search_fred(query, limit=5)` — keyword search across 800K+ economic time series
- `search_census(query, year="2022")` — queries ACS variables (population, income, poverty, etc.)
- `search_govdata(query, sources=None)` — unified interface, auto-detects which source to use
- `format_govdata_markdown(results)` → shows latest values + direction for each series

**When the graph triggers it:**
- ResearchTool node: `Gov Data Search`
- Connected to 11 Techniques: Evidence Synthesis, STEEP Analysis, Stakeholder Interviews, etc.
- Technique signals containing: `evidence`, `stakeholder`, `cause-effect`, `best practice`, `expert analysis`
- Problem context: "well-defined/complicated" problems
- Bot hints: ackoff (DIKW Data layer), scurve (industry analysis), jtbd (Census demographics)

**Callback flow:**
1. Gemini extracts query + picks sources (bls/fred/census) as JSON
2. Calls max 2 sources per query
3. Shows latest values with rising/declining direction

---

### 5. `dataset_search.py` — Find Datasets

**Button label:** 📊 Find Datasets
**What it does:** Searches Kaggle (curated ML/research datasets) and Socrata (80K+ government open datasets from cities, states, federal agencies) for downloadable raw data.
**APIs:**
- **Kaggle** REST API — `GET /api/v1/datasets/list?search=...`. Env: `KAGGLE_USERNAME` + `KAGGLE_KEY`
- **Socrata** Discovery API — `GET api.us.socrata.com/api/catalog/v1?q=...`. No key needed.

**Key functions:**
- `search_kaggle(query, max_results=5)` → datasets with title, size, votes, downloads, URL
- `search_socrata(query, max_results=5)` → datasets with title, domain, columns, updated date
- `search_datasets(query, sources=None)` → unified search across both
- `format_datasets_markdown(results)` → shows both sources with metadata

**Uses caching:** Both `search_kaggle` and `search_socrata` use `research_cache.cached_call()` with 10-min TTL.

**When the graph triggers it:**
- ResearchTool node: `Dataset Search`
- Connected to 13 Techniques: Evidence Synthesis, Systematic Gap Analysis, Domain & Trend Analysis, etc.
- Technique signals containing: `evidence`, `gap analysis`, `domain`, `systematic`, `pattern`
- Bot hints: ackoff (raw data for DIKW), tta (validate extrapolations), jtbd (behavioral datasets), redteam (contradicting data)

---

### 6. `news_search.py` — News Signal

**Button label:** 📰 News Signal
**What it does:** Searches NewsMesh for structured news articles with categories, topics, and mentioned people — richer than Tavily for news-specific queries.
**API:** NewsMesh — `GET api.newsmesh.co/v1/search`
**Env var:** `NEWSMESH_API_KEY`
**Categories:** politics, technology, business, health, science, environment, world

**Key functions:**
- `search_news(query, max_results=5, category=None, sort_by="relevant")` → articles with title, source, date, category, topics, people
- `get_trending(max_results=5)` → trending articles
- `format_news_markdown(results)` → shows articles with source, date, category, topics, people

**Uses caching:** 15-min TTL (news changes faster).

**When the graph triggers it:**
- ResearchTool node: `News Signal Search`
- Connected to 11 Techniques: Assumption Challenging, Scenario Brainstorming, STEEP Analysis, Trending to the Absurd, etc.
- Technique signals containing: `trend`, `assumption`, `scenario`, `emerging`, `steep`
- Bot hints: redteam (news contradicts assumptions), scurve (news volume = adoption signal), tta (validate trend direction)

**Callback flow:**
1. Gemini extracts query + picks category from conversation as JSON
2. Calls `search_news()` with optional category filter
3. Shows articles with structured metadata

---

## Shared Infrastructure

### `research_cache.py` — TTL Cache

All tools share an in-memory cache to prevent redundant API calls when the same topic is discussed across turns.

**Key functions:**
- `cached_call(source, query, fetch_fn, ttl=600)` — returns cached result if fresh, otherwise calls `fetch_fn()` and caches
- `invalidate(source=None)` — clear cache (all or by namespace)
- `stats()` → `{"total", "fresh", "stale"}`

**Default TTL:** 10 minutes (600s). News uses 15 minutes (900s).
**Auto-eviction:** when cache exceeds 200 entries, stale items (3x TTL old) are purged.

---

## Adding a New Research Tool

Follow this pattern exactly:

### Step 1: Create `tools/your_tool.py`
```python
from tools.research_cache import cached_call

def search_your_source(query, max_results=5):
    def _fetch():
        # Call the API here
        return {"source": "YourSource", "query": query, "results": [...], "error": None}
    return cached_call("your_source", query, _fetch, ttl=600)

def format_your_source_markdown(results):
    # Return formatted markdown string
    ...
```

### Step 2: Create Neo4j ResearchTool node
```cypher
CREATE (m:ResearchTool {
  name: 'Your Tool Name',
  description: 'What it does'
})

// Connect to techniques it supports
WITH m
MATCH (t:Technique) WHERE t.name IN ['Technique1', 'Technique2']
CREATE (m)-[:SUPPORTS]->(t)

// Connect from frameworks that use it
WITH m
MATCH (f:Framework) WHERE f.name IN ['Framework1', 'Framework2']
CREATE (f)-[:USES_TOOL]->(m)
```

### Step 3: Wire into `suggest_research_tools()` in `mindrian_chat.py`

1. Add `your_reasons = []` to the initialization block
2. In Layer 1 (graph orchestrator), add detection:
   ```python
   if "yourkeyword" in tl:
       your_reasons.append(f"Framework '{plan.frameworks[0]['name']}' uses your tool" if plan.frameworks else "Graph suggests your tool")
   ```
3. In Layer 1 technique signals, add:
   ```python
   if any(w in tl for w in ["keyword1", "keyword2"]):
       your_reasons.append(f"Technique '{tech}' benefits from your tool")
   ```
4. In Layer 3 bot hints, add `"your_tool": "Reason"` to relevant bots
5. Add hint check: `if "your_tool" in bot_hints and not your_reasons:`
6. Add button builder:
   ```python
   if your_reasons:
       reason = your_reasons[0]
       actions.append(cl.Action(
           name="your_tool_search",
           payload={"action": "your_tool_search", "reason": reason},
           label="🔧 Functional Name",  # NAME BY FUNCTION, NOT SERVICE
           tooltip=reason,
           description=reason,
       ))
   ```

### Step 4: Add `@cl.action_callback("your_tool_search")` handler

```python
@cl.action_callback("your_tool_search")
async def on_your_tool_search(action: cl.Action):
    history = cl.user_session.get("history", [])
    recent = " ".join([m.get("content", "") for m in history[-4:]])[-500:]
    reason = action.payload.get("reason", "Graph suggested your tool")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**🔧 Doing the Thing**\n*Why: {reason}*\n\n")

    # Extract query via Gemini
    qr = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Extract a concise search query (max 6 words) from this conversation. Return ONLY the query:\n\n{recent}",
    )
    search_query = qr.text.strip().strip('"')

    from tools.your_tool import search_your_source, format_your_source_markdown
    results = search_your_source(search_query)
    formatted = format_your_source_markdown(results)

    await msg.stream_token(f"**Query:** {search_query}\n\n{formatted}")
    await msg.update()

    history.append({"role": "model", "content": f"[Your Tool: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)
```

### Naming Rules

**CRITICAL:** Button labels describe the FUNCTION, not the service.
- Good: `📈 Trends`, `📚 Academic Evidence`, `📰 News Signal`
- Bad: `📈 Google Trends`, `📚 ArXiv Search`, `📰 NewsMesh`

The user should never know or care which API is behind the button.

---

## Environment Variables

| Variable | Tool | Required? |
|----------|------|-----------|
| (none) | ArXiv | Free, no key |
| (none) | Patent Search | Free, no key |
| `SERPAPI_API_KEY` | Trends | Yes |
| `FRED_API_KEY` | Gov Data (FRED) | For FRED data |
| `BLS_API_KEY` | Gov Data (BLS) | Optional (v1 is free) |
| `DATA_GOV_API_KEY` | Gov Data (Census) | Optional |
| `KAGGLE_USERNAME` | Find Datasets | For Kaggle |
| `KAGGLE_KEY` | Find Datasets | For Kaggle |
| `SOCRATA_APP_TOKEN` | Find Datasets | Optional (higher rate limits) |
| `NEWSMESH_API_KEY` | News Signal | Yes |

---

## Failure Modes

The system is designed to degrade gracefully:

1. **Neo4j unavailable** → Layer 1 skipped, Layer 2+3 still work
2. **Graph returns no tools** → Layer 2 (problem context) may still trigger buttons
3. **Graph + problem context return nothing** → Layer 3 bot hints provide fallback
4. **All layers return nothing** → No buttons shown (safe default)
5. **API key missing for a tool** → Tool returns error message, other tools unaffected
6. **API call fails** → Error shown to user, history still updated
7. **Cache prevents redundant calls** → Same topic in same conversation reuses results
