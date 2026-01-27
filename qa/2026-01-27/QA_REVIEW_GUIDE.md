# QA Review Guide: Graph-Driven Research Buttons + LangExtract Intelligence Layer

> **Date:** 2026-01-27
> **Scope:** Research tool buttons, intelligence layer, Neo4j schema rename
> **Commits:** `4e683a9`, `5269a73`, `ca21048`, `d6517fe`, `89853c2`

---

## Part 1: What Changed — Research Buttons

When users chat with any bot, **contextual research buttons now appear automatically** after messages. The system uses a 4-layer decision engine to determine which buttons to show:

| Layer | Source | Speed | What It Checks |
|-------|--------|-------|---------------|
| Layer 0 | LangExtract signals | <5ms | Regex-detected assumptions, certainty, forward-looking language, data presence |
| Layer 1 | Neo4j graph | ~50ms | Framework → ResearchTool → Technique relationships |
| Layer 2 | Problem context | ~50ms | Problem type classification (ill-defined, well-defined, emerging) |
| Layer 3 | Bot hints (fallback) | <1ms | Hardcoded bot-specific research suggestions |

**Function:** `suggest_research_tools()` at `mindrian_chat.py:1039`
**Called at:** `mindrian_chat.py:4492`

---

## Part 2: What Changed — Intelligence Layer

An invisible coaching system now runs on **every user message**:

1. `instant_extract()` (<5ms, regex) detects signals: assumptions, certainty, problems, solutions, forward-looking language
2. `get_extraction_hint()` generates a 1-sentence coaching instruction appended to system context
3. `background_intelligence()` fires async every ~5 turns for deep LLM extraction + coherence scoring

**No UI changes.** Coaching quality improves invisibly.

---

## Part 3: What Changed — Neo4j Schema

| Before | After |
|--------|-------|
| Node label `MCPTool` | `ResearchTool` |
| Relationship `ORCHESTRATES_MCP` | `USES_TOOL` |
| Relationship `USES_MCP` | `USES_TOOL` |

Code references in `graph_orchestrator.py` and `tool_dispatcher.py` updated to match.

**Neo4j graph itself must also have been updated.** If not, graph queries return empty (graceful degradation — Layer 0 + Layer 3 still work).

---

## What You'll See

After 2+ messages in any conversation, up to 6 new buttons may appear below the bot's response, alongside the existing agent-switch suggestions:

| Button | Label | When It Appears |
|--------|-------|----------------|
| 📚 Academic Evidence | `arxiv_search` | Claims need validation, empirical grounding, certainty without sources (Layer 0), or graph links to ArXiv (Layer 1) |
| 🔎 Prior Art & Patents | `patent_search` | Inventions, solutions, innovation landscape, "does this already exist?" |
| 📈 Trends | `trends_search` | Market trends, adoption curves, timing, forward-looking language (Layer 0), or "is this growing?" |
| 🏛️ Gov Data | `govdata_search` | Economic data, demographics, labor stats, industry numbers, low data grounding score (Layer 0 coherence) |
| 📊 Find Datasets | `dataset_search` | Raw data needed to prove a point, ground analysis, low data grounding (Layer 0 coherence) |
| 📰 News Signal | `news_search` | Current events, validating assumptions against reality, 3+ assumptions detected (Layer 0) |

Buttons are **NOT always visible**. They only appear when the layers justify them. Normal chat with no research signals = no extra buttons.

---

## Bot-Specific Research Hints (Layer 3 Fallback)

These fire when Layers 0-2 don't produce reasons. Defined at `mindrian_chat.py:1153`:

| Bot | Buttons It Gets | Reason Tooltips |
|-----|----------------|-----------------|
| **redteam** | 📚 📊 📰 | "Red Team challenges need counter-evidence", "Red Team — find contradicting data", "Red Team — check if news contradicts assumptions" |
| **ackoff** | 📚 🏛️ 📊 | "DIKW validation benefits from published data", "DIKW Data layer benefits from real government statistics", "DIKW Data layer — find raw datasets" |
| **scurve** | 🔎 📈 🏛️ 📰 | "S-Curve timing uses patent filing patterns", "S-Curve adoption maps to Google Trends", "S-Curve industry analysis uses BLS/FRED data", "S-Curve — news volume signals adoption phase" |
| **tta** | 🔎 📈 📊 📰 | "Trend analysis benefits from innovation landscape", "TTA extrapolation needs real trend baselines", "TTA needs real data to validate trends", "TTA — current news validates trend direction" |
| **jtbd** | 🏛️ 📊 | "JTBD customer research benefits from Census demographic data", "JTBD needs behavioral/survey datasets" |
| **larry**, **bono**, **knowns**, **domain**, **investment**, **scenario** | (none from Layer 3) | These bots only get buttons from Layers 0-2 when conversation signals warrant them |

---

## Intelligence Layer — Coaching Hints

These are invisible instructions appended to the system context. The user never sees them; the bot responds differently because of them.

| Signal Detected | Coaching Hint Appended |
|----------------|----------------------|
| Solution-focused + no problems mentioned | "Redirect to problem definition — user is jumping to solutions" |
| 2+ assumptions + no data | "Probe which assumptions to validate and what evidence would support them" |
| High certainty + no sources cited | "Ask what evidence or experience supports their confidence" |
| Forward-looking + no current data | "Ask what present-day data or trends support their projection" |

**Function:** `get_extraction_hint()` in `tools/langextract.py`

---

## Intelligence Layer — Agent Suggestion Boosts

The extraction signals add scores to agent suggestions (additive, on top of keyword + graph scoring):

| Signal | Agent Boosted | Score Added | What It Means |
|--------|--------------|-------------|--------------|
| `content_type=solution_focused` + `problems=0` | ackoff | +0.4 | User solving without defining problem → Ackoff helps define it |
| `assumptions >= 2` | redteam | +0.4 | Multiple assumptions piling up → Red Team challenges them |
| `is_forward_looking=True` | tta | +0.3 | Future-oriented discussion → TTA maps trends |

**Where:** `suggest_agents_from_context()` at `mindrian_chat.py:967`
**Existing limit:** `max_suggestions=2` (unchanged)

---

## Intelligence Layer — Research Button Boosts (Layer 0)

| Signal | Button(s) Boosted | Reason Added |
|--------|-------------------|-------------|
| Certainty >= 1 + no data | 📚 ArXiv | "Claims need evidence grounding" |
| Forward-looking | 📈 Trends | "Forward-looking discussion benefits from trend data" |
| Assumptions >= 3 | 📰 News | "Multiple assumptions — news may validate or challenge them" |
| Coherence: data_grounding < 4 | 🏛️ Gov Data + 📊 Datasets | "Low data grounding — government statistics could help" |
| Coherence: assumption_awareness < 4 | 📚 ArXiv | "Hidden assumptions detected — academic evidence may help" |

**Note:** Coherence scores come from `background_intelligence()` which runs every ~5 turns. Layer 0 coherence boosts only activate after the background task has run at least once.

---

## Test Scenarios

### Scenario 1: TTA Bot — Trend Discussion

1. Switch to **Trending to the Absurd**
2. Say: "Let's explore how electric vehicles are trending and where the market is heading"
3. Continue with: "What assumptions are we making about adoption rates?"

**Expected buttons:** 📈 Trends, 📰 News Signal, 📊 Find Datasets
**Expected tooltips:** "TTA extrapolation needs real trend baselines" or "Technique 'Trend Mapping' benefits from real trend data"
**Expected coaching:** Bot may probe assumptions (Layer 0 detected "assumptions" keyword + forward-looking language)

### Scenario 2: Red Team Bot — Challenge Assumptions

1. Switch to **Red Team**
2. Say: "Our startup assumes customers will pay $50/month for our SaaS product"
3. Continue with: "What evidence supports or contradicts this pricing?"

**Expected buttons:** 📚 Academic Evidence, 📰 News Signal, 📊 Find Datasets
**Expected tooltips:** "Red Team challenges need counter-evidence", "Red Team — check if news contradicts current assumptions"

### Scenario 3: S-Curve Bot — Industry Timing

1. Switch to **S-Curve**
2. Say: "Where is AI in healthcare on the S-Curve right now?"
3. Continue with: "How fast is adoption growing?"

**Expected buttons:** 🔎 Prior Art & Patents, 📈 Trends, 🏛️ Gov Data
**Expected tooltips:** "S-Curve timing uses patent filing patterns", "S-Curve adoption maps to Google Trends interest curves"

### Scenario 4: Ackoff Bot — DIKW Data Grounding

1. Switch to **Ackoff's Pyramid**
2. Say: "I want to build the Data layer for understanding homelessness in Baltimore"
3. Continue with: "What real data exists on this?"

**Expected buttons:** 📚 Academic Evidence, 🏛️ Gov Data, 📊 Find Datasets
**Expected tooltips:** "DIKW Data layer benefits from real government statistics", "DIKW Data layer — find raw datasets to build Information from"

### Scenario 5: JTBD Bot — Customer Research

1. Switch to **Jobs to Be Done**
2. Say: "I'm researching what jobs college students hire food delivery apps to do"

**Expected buttons:** 🏛️ Gov Data, 📊 Find Datasets
**Expected tooltips:** "JTBD customer research benefits from Census demographic data", "JTBD needs behavioral/survey datasets for customer evidence"

### Scenario 6: No Buttons (Normal Chat)

1. Stay on **Larry**
2. Say: "Hi, what can you help me with?"

**Expected:** No research buttons appear (conversation too short / no research signals)

### Scenario 7: Intelligence Layer — Solution Jumping

1. Stay on **Larry**
2. Say: "We should build an Uber for plumbing"

**Expected:** Larry redirects to problem definition ("What problem are you trying to solve?")
**Why:** `content_type=solution_focused` + `problems=0` → coaching hint fires
**Expected agent suggestion:** Ackoff may appear (score boost +0.4)

### Scenario 8: Intelligence Layer — Assumption Accumulation

1. Any bot
2. Send: "Assuming the market grows 20% annually, and if we suppose millennials prefer mobile-first..."
3. Follow up: "Given that our competition won't adapt, we can assume first-mover advantage..."

**Expected:** Red Team agent suggestion appears (2+ assumptions → +0.4 score boost)
**Expected:** Bot probes which assumptions to validate (coaching hint)
**After 3+ assumptions:** 📰 News Signal button may appear

### Scenario 9: Intelligence Layer — Certainty Without Evidence

1. Any bot
2. Say: "This is definitely the right approach. Clearly AI will replace 80% of jobs."

**Expected:** 📚 Academic Evidence button appears ("Claims need evidence grounding")
**Expected:** Bot asks what evidence supports the confidence

### Scenario 10: Intelligence Layer — Forward-Looking

1. Any bot
2. Say: "By 2030, every company will need to be AI-first. The future is autonomous agents."

**Expected:** 📈 Trends button appears ("Forward-looking discussion benefits from trend data")
**Expected:** TTA agent suggestion appears (+0.3 score)
**Expected:** Bot asks what current data supports the projection

### Scenario 11: Background Intelligence (5+ turns)

1. Have a 5+ turn conversation on any topic
2. Check server logs for background_intelligence messages
3. Check Supabase `extractions/` bucket for new `conversation_intelligence_*.json` entries
4. After background runs, send a message with weak data grounding

**Expected:** Gov Data and Dataset buttons may appear ("Low data grounding")
**Expected:** No visible change during background processing

---

## What Happens When You Click a Button

Every button follows the same user experience:

1. **Header with reason appears immediately:**
   ```
   📈 Measuring Trend Momentum
   Why: S-Curve adoption maps to Google Trends interest curves
   ```
2. **Gemini extracts a search query** from the last 4 messages (user doesn't type anything)
3. **Results stream in** with the query shown
4. **Results are injected into conversation history** — the bot can reference them in follow-up responses

### Per-Button Output Format

| Button | Output Shows |
|--------|-------------|
| 📚 Academic Evidence | Paper titles, authors, dates, abstracts, ArXiv links |
| 🔎 Prior Art & Patents | Patent titles, assignees, filing dates, descriptions |
| 📈 Trends | Start/peak/latest interest values, rising/declining/stable direction, related queries |
| 🏛️ Gov Data | BLS series (unemployment, CPI) with latest values + direction; FRED economic indicators; Census state-level data |
| 📊 Find Datasets | Kaggle datasets (title, size, votes, downloads) + Socrata government datasets (title, domain, columns, updated date) |
| 📰 News Signal | Articles with source, date, category, topics, mentioned people, links |

---

## Edge Cases to Test

| Test | Expected Behavior |
|------|-------------------|
| First message in conversation (history < 2) | No research buttons appear |
| Neo4j is down | Buttons still appear via Layer 0 (extraction) + Layer 3 (bot hints). Layer 1 and 2 silently skip |
| API key missing for a tool (e.g. no SERPAPI_API_KEY) | Click shows error message: "SERPAPI_API_KEY not set". Other buttons unaffected |
| Click same button twice on same topic | Second click returns cached result instantly (10-min TTL default, 15-min for news) |
| Very short conversation ("yes", "ok") | Likely no buttons — not enough signal. Extraction returns `content_type=general` with no boosts |
| Hover over button | Tooltip shows the reason WHY (e.g. "Technique 'STEEP Analysis' benefits from real trend data") |
| Multiple buttons appear | Buttons appear in fixed order: Academic → Patents → Trends → Gov Data → Datasets → News |
| LangExtract import fails | App works exactly as before — all extraction wrapped in try/except: pass |
| Supabase is down | Background caching silently fails. Everything else works |
| "Extract Insights" button | Still works exactly as before (no regression) |

---

## Environment Variables Required

These must be set for full functionality. Missing keys degrade gracefully (that specific tool shows an error, others work):

| Variable | For Which Button | How to Get | Required? |
|----------|-----------------|------------|-----------|
| `SERPAPI_API_KEY` | 📈 Trends, 🔎 Patents | https://serpapi.com | Yes for these tools |
| `FRED_API_KEY` | 🏛️ Gov Data (FRED) | https://fred.stlouisfed.org/docs/api/api_key.html | Yes for FRED data |
| `BLS_API_KEY` | 🏛️ Gov Data (BLS) | https://www.bls.gov/developers/ | Optional (higher rate limits) |
| `DATA_GOV_API_KEY` or `CENSUS_API_KEY` | 🏛️ Gov Data (Census) | https://api.census.gov/data/key_signup.html | Optional |
| `KAGGLE_USERNAME` + `KAGGLE_KEY` | 📊 Find Datasets (Kaggle) | https://www.kaggle.com/settings → Create New API Token | Yes for Kaggle |
| `SOCRATA_APP_TOKEN` | 📊 Find Datasets (Socrata) | https://dev.socrata.com/register | Optional (higher limits) |
| `NEWSMESH_API_KEY` | 📰 News Signal | https://newsmesh.co | Yes for news |
| _(none needed)_ | 📚 Academic Evidence | ArXiv API is free | N/A |
| `GOOGLE_API_KEY` | All (query extraction) | Google AI Studio | Yes (existing) |
| `NEO4J_URI` + `NEO4J_USERNAME` + `NEO4J_PASSWORD` | Layer 1 + 2 graph queries | Neo4j Aura or self-hosted | Optional (graceful degradation) |
| `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` | Background extraction caching | Supabase dashboard | Optional (caching disabled without) |

---

## Files Added/Changed

| File | What It Is | Commit |
|------|-----------|--------|
| `tools/research_cache.py` | Shared TTL cache (10-min default) — prevents repeated API calls | `5269a73` |
| `tools/trends_search.py` | Google Trends search via SerpAPI + formatting | `5269a73` |
| `tools/govdata_search.py` | BLS + FRED + Census search + formatting | `5269a73` |
| `tools/dataset_search.py` | Kaggle + Socrata unified search + formatting | `5269a73` |
| `tools/news_search.py` | NewsMesh news search + formatting | `5269a73` |
| `tools/README.md` | Developer guide: architecture, all tools, how to add new ones | `5269a73` |
| `tools/graph_orchestrator.py` | Cypher queries updated: MCPTool → ResearchTool, ORCHESTRATES_MCP → USES_TOOL | `4e683a9` |
| `tools/tool_dispatcher.py` | Registry + docstrings updated: MCPTool → ResearchTool | `4e683a9` |
| `tools/langextract.py` | Added `get_extraction_hint()` + `background_intelligence()` | `ca21048` |
| `mindrian_chat.py` | `suggest_research_tools()` + 6 callbacks + Layer 0 extraction + coaching hints + background task + agent scoring | `5269a73` + `ca21048` |

### Neo4j Graph Schema

The Neo4j graph now uses:
- **Node labels:** `ResearchTool` (was `MCPTool`)
- **Relationships:** `USES_TOOL` (was `ORCHESTRATES_MCP` / `USES_MCP`)
- **Full path:** `ProblemType → CynefinDomain → Framework → ResearchTool → Technique`
- **Relationships used:** `ADDRESSES_PROBLEM_TYPE`, `PART_OF`, `USES_TECHNIQUE`, `USES_TOOL`, `SUPPORTS`, `LEADS_TO`

### Packages Required

Verify these are in `requirements.txt`:
- `google-search-results` (SerpAPI for Trends + Patents)
- `sodapy` (Socrata government data)
- `kaggle` (Kaggle dataset search)

---

## QA Session Feedback Items — Status in This Build

> See `QA_FEEDBACK_VS_CHANGES.md` for the full gap analysis (21 items, 3 done, 3 partial, 15 pending UI pass).

### Items Addressed by Today's Changes

| # | Feedback Item | Status | How Addressed |
|---|--------------|--------|--------------|
| 2b | Limit suggested agent buttons to 1-2 | DONE | `max_suggestions=2` (was already in place). Now smarter with extraction scoring |
| 4a | Keep Synthesize as always-available | DONE | Already pinned. No change needed |
| 7a | Keep dropdown for power users | DONE | 11-bot dropdown unchanged |
| 7b | Contextual hover descriptions | PARTIAL | Suggested agent buttons now have contextual tooltips from extraction. Dropdown still static |
| 10a | Clickable research links | PARTIAL | New research tool outputs render markdown with clickable links. No "copy all" button |
| 12 | MVP: context-suggested agents | PARTIAL | Intelligence layer makes suggestions significantly smarter |

### Items NOT Addressed (Pending UI Pass)

| # | Feedback Item | What's Needed |
|---|--------------|--------------|
| 1a | Slider on main page | Move from Settings panel to chat header. Chainlit UI customization needed |
| 1b | Slider default to 1 | Change `initial=5` to `initial=1` at `mindrian_chat.py:897` |
| 2a | Remove/relocate most buttons | Refactor `on_chat_start()` button creation. Keep only Research + Synthesize visible |
| 2c | "More options" menu | Chainlit doesn't natively support kebab menus. Needs custom component |
| 3a | Consolidate Research / Deep Research | Two callbacks exist: `deep_research` (line 3033) + `gemini_deep_research` (line 3695). Need to merge or remove one |
| 3b | Clarify "Think" button | `think_through` at line 3906. Needs tooltip or relocation to Advanced |
| 4b | Naming: "Synthesize" vs "Summarize" | Team decision needed on label |
| 5a | Simple / Advanced mode toggle | Significant UI architecture change. Could use two ChatProfiles or a settings toggle |
| 6a | De-emphasize Multi-agent analysis | `multi_agent_analysis` button at line 2032. Should only show when high confidence |
| 6b | Multi-agent respects slider | Handler doesn't read `response_detail` slider value |
| 7c | Plan for 50 agents | Future: search + favorites + recommended section |
| 8a | PDF image limitation warning | Add upload message: "Text extracted. Images not supported yet" |
| 9a | Voice stop control | Requires Chainlit UI fix |
| 9b | "Voice is experimental" banner | Add banner on voice activation |
| 11a | Hide metrics/feedback from normal users | Move `show_feedback_dashboard` + `show_usage_metrics` behind Admin menu |

---

## Quick Smoke Test Summary

| # | Test | What to Check | Pass? |
|---|------|--------------|-------|
| 1 | Fresh session | Larry loads, 4 starters visible, no delay | ☐ |
| 2 | "Build Uber for plumbing" | Larry redirects to problem definition | ☐ |
| 3 | 2+ assumption messages | Red Team suggested, bot probes assumptions | ☐ |
| 4 | "Definitely right, clearly best" | ArXiv button appears, bot asks for evidence | ☐ |
| 5 | "By 2030..." | Trends button + TTA suggestion | ☐ |
| 6 | Click each research button | Results stream with reason header + links | ☐ |
| 7 | 5+ turn conversation | Background extraction in logs, Supabase entries | ☐ |
| 8 | S-Curve + framework mention | Graph-driven tooltips on research buttons | ☐ |
| 9 | Neo4j down | Buttons still work (Layer 0 + 3 fallback) | ☐ |
| 10 | Extract Insights button | Still works (no regression) | ☐ |
| 11 | Synthesize button | Still works (no regression) | ☐ |
| 12 | Bot switch via dropdown | Context preserved | ☐ |
| 13 | Bot switch via suggestion | Context preserved, buttons update | ☐ |
