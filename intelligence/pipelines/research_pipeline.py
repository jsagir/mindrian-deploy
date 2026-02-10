"""
Deep Research Pipeline — Claude Plans, Tavily Searches, Gemini Synthesizes
==========================================================================

LangGraph StateGraph implementation for iterative research with reflection.

Architecture:
    START → PLAN (Claude Sonnet) → SEARCH (Tavily) → EVALUATE (Python)
          → REFLECT (Claude Sonnet) → [loop or] SYNTHESIZE (Gemini Flash) → END

Depth tiers:
    basic    — 2-3 queries, no reflection, fast & cheap
    standard — 3-5 queries, 1 reflection round
    deep     — 5-8 queries, up to 3 reflection rounds

Public API:
    run_deep_research()        — Full pipeline with checkpointing
    quick_pipeline_research()  — One-shot, no reflection (drop-in for search_web)
    create_research_pipeline() — Graph factory for custom wiring
"""

import os
import json
import logging
import asyncio
import time
import re
from typing import Dict, List, Optional, Any, TypedDict, Literal

from langgraph.graph import StateGraph, END

logger = logging.getLogger("research_pipeline")


# ============================================================================
# State Definition
# ============================================================================

class DeepResearchState(TypedDict, total=False):
    original_query: str          # User's EXACT words (never truncated)
    research_question: str       # Cleaned version for display
    conversation_history: list   # Full chat history for context
    bot_id: str                  # Current bot
    depth: str                   # basic / standard / deep
    planned_queries: list        # Claude's search plan [{query, purpose, priority}]
    search_results: list         # Tavily results accumulated across iterations
    evaluated_sources: list      # Scored/filtered sources
    evidence_gaps: list          # What's still missing
    synthesis: str               # Final report markdown
    pws_context: str             # GraphRAG enrichment
    iteration: int               # Current loop count (max 3)
    cost_summary: dict           # API cost tracking
    error: str                   # Error state for graceful handling
    findings: list               # Structured findings for display
    sources_display: list        # Sources formatted for display
    graph_write_status: str      # "pending" / "success" / "failed" / "skipped"


# ============================================================================
# Depth Configuration
# ============================================================================

DEPTH_CONFIG = {
    "basic": {
        "min_queries": 2,
        "max_queries": 3,
        "tavily_depth": "basic",
        "max_reflections": 0,
        "max_results_per_query": 5,
    },
    "standard": {
        "min_queries": 3,
        "max_queries": 5,
        "tavily_depth": "advanced",
        "max_reflections": 1,
        "max_results_per_query": 5,
    },
    "deep": {
        "min_queries": 5,
        "max_queries": 8,
        "tavily_depth": "advanced",
        "max_reflections": 3,
        "max_results_per_query": 8,
    },
}


# ============================================================================
# Node 1: PLAN (Claude Sonnet)
# ============================================================================

PLAN_PROMPT = """You are a research strategist. Decompose this research question into targeted web search queries.

USER'S EXACT WORDS: "{original_query}"

RESEARCH QUESTION: {research_question}

CONVERSATION CONTEXT (recent):
{conversation_context}

PWS DOMAIN CONTEXT: {pws_context}

DEPTH: {depth} — Generate {min_queries}-{max_queries} queries.

CRITICAL FIDELITY RULES:
1. Every search query you generate MUST include at least one key phrase from the user's words above.
2. Do NOT substitute with synonyms. If the user said "project-based curricula", use "project-based curricula", NOT "Project 2025".
3. Think like a search engine — use keywords, not natural questions.
4. Include temporal markers (2024, 2025, 2026) for recent information.
5. Each query should target a DIFFERENT aspect: landscape, specific data, alternatives, recent news, comparisons.

Return ONLY valid JSON:
{{
    "queries": [
        {{"query": "keyword search query", "purpose": "what this finds", "priority": 1}},
        ...
    ]
}}"""


async def plan_node(state: DeepResearchState) -> dict:
    """Claude Sonnet decomposes the query into targeted search queries."""
    config = DEPTH_CONFIG.get(state.get("depth", "standard"), DEPTH_CONFIG["standard"])

    # Get PWS context from GraphRAG
    pws_context = await _get_pws_context(state.get("original_query", ""))

    # Build conversation context snippet
    conv_history = state.get("conversation_history", [])
    conv_snippet = ""
    if conv_history:
        recent = conv_history[-6:]
        conv_snippet = "\n".join(
            f"{m.get('role', 'user')}: {m.get('content', '')[:200]}"
            for m in recent
        )

    prompt = PLAN_PROMPT.format(
        original_query=state.get("original_query", state.get("research_question", "")),
        research_question=state.get("research_question", ""),
        conversation_context=conv_snippet[:1500] if conv_snippet else "No prior conversation",
        pws_context=pws_context,
        depth=state.get("depth", "standard"),
        min_queries=config["min_queries"],
        max_queries=config["max_queries"],
    )

    cost_summary = state.get("cost_summary", {"claude": 0.0, "tavily": 0.0, "gemini": 0.0, "total": 0.0})

    try:
        from utils.llm_router import get_claude_client, cost_tracker

        client = get_claude_client()
        start = time.time()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            temperature=0.2,
            system="You are a research strategist. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
        )

        latency = int((time.time() - start) * 1000)
        cost = cost_tracker.record_call(
            model="claude-sonnet-4-20250514",
            provider="anthropic",
            task_type="research_planning",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=latency,
            success=True,
        )
        cost_summary["claude"] += cost

        # Parse response
        result = _parse_json(response.content[0].text)
        queries = result.get("queries", []) if result else []

        if not queries:
            # Fallback: use original query directly
            queries = [
                {"query": state.get("original_query", ""), "purpose": "main query", "priority": 1},
                {"query": f"{state.get('original_query', '')} 2025 2026", "purpose": "recent data", "priority": 2},
            ]

        # Enforce max queries
        queries = queries[:config["max_queries"]]

        logger.info("Plan node: %d queries planned", len(queries))

        return {
            "planned_queries": queries,
            "pws_context": pws_context,
            "cost_summary": cost_summary,
            "iteration": state.get("iteration", 0),
        }

    except Exception as e:
        logger.error("Plan node failed: %s", e)
        # Graceful fallback to Gemini planning
        return await _fallback_plan(state, cost_summary, str(e))


async def _fallback_plan(state: dict, cost_summary: dict, error_msg: str) -> dict:
    """Fallback to Gemini if Claude is unavailable."""
    logger.warning("Falling back to Gemini for planning: %s", error_msg)

    try:
        from utils.llm_router import get_gemini_client
        client = get_gemini_client()

        query = state.get("original_query", state.get("research_question", ""))
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Generate 3 web search queries for: {query}\n\nReturn JSON: {{\"queries\": [{{\"query\": \"...\", \"purpose\": \"...\", \"priority\": 1}}]}}",
            config={"temperature": 0.3, "max_output_tokens": 500},
        )

        result = _parse_json(response.text)
        queries = result.get("queries", []) if result else []

        if not queries:
            queries = [
                {"query": query, "purpose": "main", "priority": 1},
                {"query": f"{query} recent 2025", "purpose": "recent", "priority": 2},
            ]

        return {
            "planned_queries": queries,
            "pws_context": state.get("pws_context", ""),
            "cost_summary": cost_summary,
            "iteration": state.get("iteration", 0),
        }

    except Exception as e2:
        logger.error("Fallback plan also failed: %s", e2)
        query = state.get("original_query", "research query")
        return {
            "planned_queries": [
                {"query": query, "purpose": "main", "priority": 1},
            ],
            "pws_context": "",
            "cost_summary": cost_summary,
            "iteration": state.get("iteration", 0),
            "error": f"Planning failed: {error_msg}; fallback: {e2}",
        }


# ============================================================================
# Node 2: SEARCH (Tavily)
# ============================================================================

async def search_node(state: DeepResearchState) -> dict:
    """Execute all planned queries via Tavily in parallel."""
    from tools.tavily_search import search_web
    from utils.llm_router import cost_tracker

    config = DEPTH_CONFIG.get(state.get("depth", "standard"), DEPTH_CONFIG["standard"])
    queries = state.get("planned_queries", [])
    existing_results = state.get("search_results", [])
    cost_summary = state.get("cost_summary", {"claude": 0.0, "tavily": 0.0, "gemini": 0.0, "total": 0.0})

    if not queries:
        return {"search_results": existing_results, "cost_summary": cost_summary}

    async def run_single_search(q: dict) -> dict:
        """Execute one Tavily search in an executor (sync → async)."""
        try:
            loop = asyncio.get_event_loop()
            start = time.time()
            result = await loop.run_in_executor(
                None,
                lambda: search_web(
                    query=q.get("query", ""),
                    search_depth=config["tavily_depth"],
                    max_results=config["max_results_per_query"],
                ),
            )
            latency = int((time.time() - start) * 1000)

            # Track cost
            model = f"tavily-{config['tavily_depth']}"
            cost = cost_tracker.record_call(
                model=model,
                provider="tavily",
                task_type="research_search",
                latency_ms=latency,
                success=True,
                metadata={"query": q.get("query", "")[:100]},
            )

            return {
                "query": q.get("query", ""),
                "purpose": q.get("purpose", ""),
                "results": result.get("results", []),
                "answer": result.get("answer", ""),
                "cost": cost,
            }
        except Exception as e:
            logger.error("Search failed for '%s': %s", q.get("query", "")[:50], e)
            return {
                "query": q.get("query", ""),
                "purpose": q.get("purpose", ""),
                "results": [],
                "answer": "",
                "error": str(e),
                "cost": 0.0,
            }

    # Execute ALL searches in parallel
    results = await asyncio.gather(
        *[run_single_search(q) for q in queries],
        return_exceptions=True,
    )

    new_results = []
    total_tavily_cost = 0.0
    for r in results:
        if isinstance(r, Exception):
            logger.error("Search exception: %s", r)
        elif isinstance(r, dict):
            total_tavily_cost += r.get("cost", 0.0)
            new_results.append(r)

    cost_summary["tavily"] += total_tavily_cost

    # Accumulate results across iterations
    all_results = existing_results + new_results

    total_sources = sum(len(r.get("results", [])) for r in new_results)
    logger.info("Search node: %d queries → %d new sources (total accumulated: %d)",
                len(queries), total_sources,
                sum(len(r.get("results", [])) for r in all_results))

    return {
        "search_results": all_results,
        "cost_summary": cost_summary,
    }


# ============================================================================
# Node 3: EVALUATE (Python — no LLM)
# ============================================================================

async def evaluate_node(state: DeepResearchState) -> dict:
    """Score and filter sources by authority, recency, relevance."""
    from tools.research_orchestrator import evaluate_sources

    search_results = state.get("search_results", [])

    # evaluate_sources expects the discovery_results format
    evaluated = evaluate_sources(search_results)

    # Convert SourceEvaluation dataclasses to dicts for state
    sources = []
    for ev in evaluated:
        sources.append({
            "url": ev.url,
            "title": ev.title,
            "category": ev.category,
            "authority_score": ev.authority_score,
            "recency_score": ev.recency_score,
            "relevance_score": ev.relevance_score,
            "extract_priority": ev.extract_priority,
            "content_snippet": ev.content_snippet,
        })

    logger.info("Evaluate node: %d sources scored (%d primary, %d secondary)",
                len(sources),
                sum(1 for s in sources if s["category"] == "primary"),
                sum(1 for s in sources if s["category"] == "secondary"))

    return {"evaluated_sources": sources}


# ============================================================================
# Node 4: REFLECT (Claude Sonnet)
# ============================================================================

REFLECT_PROMPT = """You are a research quality reviewer. Analyze whether we have sufficient evidence to answer the user's question.

ORIGINAL QUESTION: "{original_query}"

SEARCH RESULTS SUMMARY:
- Total sources found: {total_sources}
- Primary (high-authority) sources: {primary_count}
- Secondary sources: {secondary_count}
- Queries executed so far: {queries_executed}
- Current iteration: {iteration}/{max_iterations}

TOP SOURCE TITLES:
{top_sources}

KEY ANSWERS FROM SEARCHES:
{search_answers}

ASSESSMENT REQUIRED:
1. Do these results adequately answer the original question?
2. Are there critical gaps in the evidence?
3. If gaps exist, what specific follow-up queries would fill them?

Return ONLY valid JSON:
{{
    "sufficient": true/false,
    "confidence": 0.0-1.0,
    "gaps": ["gap description 1", "gap description 2"],
    "follow_up_queries": [
        {{"query": "specific search query to fill gap", "purpose": "what this finds", "priority": 1}}
    ],
    "reasoning": "brief explanation"
}}"""


async def reflect_node(state: DeepResearchState) -> dict:
    """Claude Sonnet checks coverage and decides: loop or proceed."""
    config = DEPTH_CONFIG.get(state.get("depth", "standard"), DEPTH_CONFIG["standard"])
    iteration = state.get("iteration", 0)
    max_reflections = config["max_reflections"]

    # Skip reflection for basic depth
    if max_reflections == 0:
        return {
            "evidence_gaps": [],
            "iteration": iteration,
        }

    evaluated = state.get("evaluated_sources", [])
    search_results = state.get("search_results", [])

    # Build summary for reflection
    top_sources = "\n".join(
        f"- [{s['category']}] {s['title'][:80]} (authority: {s['authority_score']:.2f})"
        for s in evaluated[:10]
    )

    search_answers = "\n".join(
        f"- {r.get('query', '')[:60]}: {r.get('answer', 'No direct answer')[:150]}"
        for r in search_results[-5:]
    )

    prompt = REFLECT_PROMPT.format(
        original_query=state.get("original_query", ""),
        total_sources=len(evaluated),
        primary_count=sum(1 for s in evaluated if s["category"] == "primary"),
        secondary_count=sum(1 for s in evaluated if s["category"] == "secondary"),
        queries_executed=sum(len(r.get("results", [])) for r in search_results),
        iteration=iteration + 1,
        max_iterations=max_reflections,
        top_sources=top_sources or "None found",
        search_answers=search_answers or "No answers extracted",
    )

    cost_summary = state.get("cost_summary", {"claude": 0.0, "tavily": 0.0, "gemini": 0.0, "total": 0.0})

    try:
        from utils.llm_router import get_claude_client, cost_tracker

        client = get_claude_client()
        start = time.time()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            temperature=0.2,
            system="You are a research quality reviewer. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
        )

        latency = int((time.time() - start) * 1000)
        cost = cost_tracker.record_call(
            model="claude-sonnet-4-20250514",
            provider="anthropic",
            task_type="research_reflection",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=latency,
            success=True,
        )
        cost_summary["claude"] += cost

        result = _parse_json(response.content[0].text)

        if result:
            gaps = result.get("gaps", [])
            follow_ups = result.get("follow_up_queries", [])
            sufficient = result.get("sufficient", True)

            if not sufficient and follow_ups and iteration < max_reflections:
                # Need more research — set up next iteration
                return {
                    "evidence_gaps": gaps,
                    "planned_queries": follow_ups,
                    "iteration": iteration + 1,
                    "cost_summary": cost_summary,
                }
            else:
                # Sufficient or max iterations reached
                return {
                    "evidence_gaps": gaps if not sufficient else [],
                    "iteration": iteration + 1,
                    "cost_summary": cost_summary,
                }

        # Couldn't parse — proceed to synthesis
        return {
            "evidence_gaps": [],
            "iteration": iteration + 1,
            "cost_summary": cost_summary,
        }

    except Exception as e:
        logger.error("Reflect node failed: %s", e)
        # On failure, proceed to synthesis (don't block the pipeline)
        return {
            "evidence_gaps": [],
            "iteration": iteration + 1,
            "cost_summary": cost_summary,
        }


# ============================================================================
# Conditional Edge: should_continue
# ============================================================================

def should_continue(state: DeepResearchState) -> Literal["search", "synthesize"]:
    """Decide whether to loop back for more search or proceed to synthesis."""
    config = DEPTH_CONFIG.get(state.get("depth", "standard"), DEPTH_CONFIG["standard"])
    iteration = state.get("iteration", 0)
    max_reflections = config["max_reflections"]

    # Check if we have new follow-up queries AND haven't exceeded max iterations
    gaps = state.get("evidence_gaps", [])
    planned = state.get("planned_queries", [])

    if gaps and planned and iteration <= max_reflections:
        logger.info("Reflect → Search (iteration %d/%d, %d gaps)",
                    iteration, max_reflections, len(gaps))
        return "search"

    logger.info("Reflect → Synthesize (iteration %d/%d)", iteration, max_reflections)
    return "synthesize"


# ============================================================================
# Node 5: SYNTHESIZE (Gemini Flash)
# ============================================================================

SYNTHESIZE_PROMPT = """Synthesize this research into a structured markdown report.

RESEARCH QUESTION: {research_question}

ORIGINAL USER QUESTION: {original_query}

PWS METHODOLOGY CONTEXT: {pws_context}

EVIDENCE GATHERED ({total_sources} sources across {iterations} search rounds):

{evidence_text}

REMAINING GAPS:
{gaps_text}

Generate a comprehensive research report in markdown:

## Key Insights
[3-4 sentence synthesis of the most important findings]

## Research Findings
[For each major finding, include:]
### [Finding Title]
[2-3 sentences explaining the finding with specific data/facts]
**Source:** [source title and URL]
**Confidence:** [high/medium/low based on source authority]

## PWS Implications
[How this research connects to problem validation and the user's learning journey]

## Recommended Next Steps
- [3 specific, actionable next steps]

## Questions to Explore
- [2-3 remaining questions based on evidence gaps]

---
*Research: {queries_count} queries | {total_sources} sources | {iterations} rounds*

RULES:
- Be specific. Use actual data, names, and numbers from the sources.
- Cite sources with URLs where possible.
- Do NOT fabricate information. Only report what the evidence supports.
- Acknowledge uncertainty where evidence is limited.
- Frame insights through PWS methodology where relevant."""


async def synthesize_node(state: DeepResearchState) -> dict:
    """Gemini Flash generates the final research report."""
    from utils.llm_router import cost_tracker

    evaluated = state.get("evaluated_sources", [])
    search_results = state.get("search_results", [])
    gaps = state.get("evidence_gaps", [])
    cost_summary = state.get("cost_summary", {"claude": 0.0, "tavily": 0.0, "gemini": 0.0, "total": 0.0})

    # Build evidence text from search results
    evidence_parts = []
    sources_display = []
    seen_urls = set()

    for sr in search_results:
        if sr.get("answer"):
            evidence_parts.append(f"Query: {sr.get('query', '')}\nAnswer: {sr['answer']}\n")

        for r in sr.get("results", []):
            url = r.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = r.get("title", "Untitled")
            content = r.get("content", "")[:400]
            score = r.get("score", 0.5)

            evidence_parts.append(f"Source: {title}\nURL: {url}\nContent: {content}\n")
            sources_display.append({
                "title": title,
                "url": url,
                "content": content,
                "score": score,
            })

    evidence_text = "\n---\n".join(evidence_parts[:15])  # Cap at 15 sources
    gaps_text = "\n".join(f"- {g}" for g in gaps) if gaps else "No significant gaps identified."

    # Count queries
    queries_count = len(search_results)

    prompt = SYNTHESIZE_PROMPT.format(
        research_question=state.get("research_question", ""),
        original_query=state.get("original_query", ""),
        pws_context=state.get("pws_context", "General research"),
        total_sources=len(seen_urls),
        iterations=state.get("iteration", 1),
        evidence_text=evidence_text or "No evidence gathered.",
        gaps_text=gaps_text,
        queries_count=queries_count,
    )

    try:
        from utils.llm_router import get_gemini_client
        from google.genai import types

        client = get_gemini_client()
        start = time.time()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=3000,
            ),
        )

        latency = int((time.time() - start) * 1000)

        # Estimate tokens for cost tracking
        input_tokens = len(prompt) // 4
        output_tokens = len(response.text) // 4 if response.text else 0

        cost = cost_tracker.record_call(
            model="gemini-2.5-flash",
            provider="google",
            task_type="research_synthesis",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            success=True,
        )
        cost_summary["gemini"] += cost

        synthesis = response.text if response.text else "Synthesis unavailable."

    except Exception as e:
        logger.error("Synthesis failed: %s", e)
        # Fallback: build a basic report from raw results
        synthesis = _fallback_synthesis(state, search_results, evaluated, gaps)

    # Build structured findings for callers
    findings = []
    for s in sources_display[:10]:
        # Look up authority from evaluated sources
        eval_source = next((e for e in evaluated if e["url"] == s["url"]), None)
        authority = eval_source["authority_score"] if eval_source else 0.5
        category = eval_source["category"] if eval_source else "secondary"

        confidence = "high" if authority >= 0.85 else ("medium" if authority >= 0.60 else "low")

        findings.append({
            "fact": s["content"],
            "sources": [s["url"]],
            "title": s["title"],
            "confidence": confidence,
            "category": category,
        })

    cost_summary["total"] = cost_summary["claude"] + cost_summary["tavily"] + cost_summary["gemini"]

    return {
        "synthesis": synthesis,
        "findings": findings,
        "sources_display": sources_display,
        "cost_summary": cost_summary,
    }


def _fallback_synthesis(state: dict, search_results: list, evaluated: list, gaps: list) -> str:
    """Build a basic report when Gemini synthesis fails."""
    parts = [f"## Research: {state.get('research_question', 'Unknown')}\n"]
    parts.append(f"*{len(search_results)} queries executed*\n")

    for sr in search_results[:5]:
        if sr.get("answer"):
            parts.append(f"**{sr.get('query', '')}:** {sr['answer']}\n")

    if evaluated:
        parts.append("\n### Sources\n")
        for s in evaluated[:5]:
            parts.append(f"- [{s['title'][:60]}]({s['url']})")

    if gaps:
        parts.append("\n### Remaining Gaps\n")
        for g in gaps:
            parts.append(f"- {g}")

    return "\n".join(parts)


# ============================================================================
# Graph Construction
# ============================================================================

def create_research_pipeline(checkpointer=None):
    """
    Build the LangGraph StateGraph for deep research.

    Args:
        checkpointer: Optional LangGraph checkpointer for state persistence.

    Returns:
        CompiledGraph ready for invocation.
    """
    graph = StateGraph(DeepResearchState)

    # Add nodes
    graph.add_node("plan", plan_node)
    graph.add_node("search", search_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("research_to_graph", research_to_graph_node)

    # Edges: plan → search → evaluate → reflect → (search | synthesize) → research_to_graph → END
    graph.set_entry_point("plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "evaluate")
    graph.add_edge("evaluate", "reflect")

    # Conditional edge from reflect
    graph.add_conditional_edges(
        "reflect",
        should_continue,
        {
            "search": "search",
            "synthesize": "synthesize",
        },
    )

    graph.add_edge("synthesize", "research_to_graph")
    graph.add_edge("research_to_graph", END)

    # Compile
    compile_kwargs = {}
    if checkpointer:
        compile_kwargs["checkpointer"] = checkpointer

    return graph.compile(**compile_kwargs)


# ============================================================================
# Public API — Tier 1: Full Pipeline
# ============================================================================

async def run_deep_research(
    query: str,
    conversation_history: list = None,
    bot_id: str = "lawrence",
    depth: str = "standard",
    thread_id: str = None,
) -> dict:
    """
    Execute the full deep research pipeline.

    Args:
        query: The user's research question (exact words).
        conversation_history: Full chat history for context.
        bot_id: Current bot identifier.
        depth: Research depth — "basic", "standard", or "deep".
        thread_id: Optional thread ID for checkpointing.

    Returns:
        Dict with: synthesis, findings, sources, cost_summary, iterations, evidence_gaps
    """
    # Get checkpointer if thread_id provided
    checkpointer = None
    if thread_id:
        try:
            from memory.checkpointer import get_shared_checkpointer
            checkpointer = await get_shared_checkpointer()
        except Exception as e:
            logger.warning("Checkpointer unavailable: %s", e)

    pipeline = create_research_pipeline(checkpointer=checkpointer)

    initial_state = {
        "original_query": query,
        "research_question": query,
        "conversation_history": conversation_history or [],
        "bot_id": bot_id,
        "depth": depth,
        "planned_queries": [],
        "search_results": [],
        "evaluated_sources": [],
        "evidence_gaps": [],
        "synthesis": "",
        "pws_context": "",
        "iteration": 0,
        "cost_summary": {"claude": 0.0, "tavily": 0.0, "gemini": 0.0, "total": 0.0},
        "error": "",
        "findings": [],
        "sources_display": [],
    }

    # Generate per-user thread_id to prevent shared state between users
    if not thread_id:
        try:
            from memory.checkpointer import create_thread_id
            import hashlib
            # Use query hash as session scope — each unique research gets its own checkpoint
            query_hash = hashlib.md5(query[:200].encode()).hexdigest()[:12]
            thread_id = create_thread_id(
                user_id=bot_id,
                pipeline="research",
                session_id=query_hash,
            )
        except Exception:
            thread_id = f"research_{bot_id}_{id(query) % 100000}"

    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await pipeline.ainvoke(initial_state, config)

        output = {
            "synthesis": result.get("synthesis", ""),
            "findings": result.get("findings", []),
            "sources": result.get("sources_display", []),
            "cost_summary": result.get("cost_summary", {}),
            "iterations": result.get("iteration", 1),
            "evidence_gaps": result.get("evidence_gaps", []),
            "evaluated_sources": result.get("evaluated_sources", []),
            "search_results": result.get("search_results", []),
            "graph_write_status": result.get("graph_write_status", "skipped"),
        }

        return output

    except Exception as e:
        logger.error("Deep research pipeline failed: %s", e)
        import traceback
        traceback.print_exc()

        return {
            "synthesis": f"Research pipeline encountered an error: {str(e)}",
            "findings": [],
            "sources": [],
            "cost_summary": {"claude": 0.0, "tavily": 0.0, "gemini": 0.0, "total": 0.0},
            "iterations": 0,
            "evidence_gaps": [],
            "error": str(e),
        }


# ============================================================================
# Public API — Tier 2: Quick Pipeline (no reflection)
# ============================================================================

async def quick_pipeline_research(
    query: str,
    max_results: int = 5,
) -> dict:
    """
    Quick one-shot research: Claude plans → Tavily searches → returns raw results.
    No reflection loop, no synthesis. Fast drop-in for raw search_web() calls.

    Args:
        query: The search query.
        max_results: Max results per query.

    Returns:
        Dict with: answer, sources, findings, queries_executed
    """
    cost_summary = {"claude": 0.0, "tavily": 0.0, "gemini": 0.0, "total": 0.0}

    # Step 1: Claude plans 2-3 queries
    planned_queries = []
    try:
        from utils.llm_router import get_claude_client, cost_tracker

        client = get_claude_client()
        start = time.time()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            temperature=0.2,
            system="You are a search strategist. Return only valid JSON.",
            messages=[{"role": "user", "content": (
                f"Generate 2-3 focused web search queries for: \"{query}\"\n\n"
                f"CRITICAL: Each query MUST include key terms from the text above. "
                f"Do NOT substitute with synonyms.\n\n"
                f"Return JSON: {{\"queries\": [{{\"query\": \"...\", \"purpose\": \"...\", \"priority\": 1}}]}}"
            )}],
        )

        latency = int((time.time() - start) * 1000)
        cost = cost_tracker.record_call(
            model="claude-sonnet-4-20250514",
            provider="anthropic",
            task_type="quick_research_planning",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=latency,
            success=True,
        )
        cost_summary["claude"] += cost

        result = _parse_json(response.content[0].text)
        if result and result.get("queries"):
            planned_queries = result["queries"][:3]

    except Exception as e:
        logger.warning("Quick pipeline Claude planning failed: %s (using query directly)", e)

    # Fallback: use query directly
    if not planned_queries:
        planned_queries = [{"query": query, "purpose": "main", "priority": 1}]

    # Step 2: Tavily searches
    from tools.tavily_search import search_web

    all_results = []
    all_sources = []

    for q in planned_queries:
        try:
            result = search_web(
                query=q.get("query", query),
                search_depth="basic",
                max_results=max_results,
            )
            if result.get("results"):
                all_results.append({
                    "query": q.get("query", ""),
                    "results": result["results"],
                    "answer": result.get("answer", ""),
                })
                all_sources.extend(result["results"])
        except Exception as e:
            logger.error("Quick search failed for '%s': %s", q.get("query", "")[:50], e)

    # Compile answer
    answers = [r["answer"] for r in all_results if r.get("answer")]
    combined_answer = "\n\n".join(answers) if answers else ""

    # Build findings
    findings = []
    for src in all_sources[:10]:
        findings.append({
            "title": src.get("title", ""),
            "url": src.get("url", ""),
            "content": src.get("content", "")[:300],
            "score": src.get("score", 0.5),
        })

    cost_summary["total"] = cost_summary["claude"] + cost_summary["tavily"]

    return {
        "answer": combined_answer,
        "sources": all_sources,
        "findings": findings,
        "queries_executed": len(all_results),
        "planned_queries": [q.get("query", "") for q in planned_queries],
        "cost_summary": cost_summary,
    }


# ============================================================================
# Utilities
# ============================================================================

async def _get_pws_context(question: str) -> str:
    """Get PWS-relevant context from GraphRAG (reuse from research_orchestrator)."""
    try:
        from tools.research_orchestrator import _get_pws_context as _get_ctx
        return await _get_ctx(question)
    except Exception as e:
        logger.warning("PWS context retrieval failed: %s", e)
        return "General research query"


def _parse_json(text: str) -> Optional[dict]:
    """Parse JSON from model response."""
    if not text:
        return None

    # Look for JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try parsing whole text
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try finding {...}
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return None


# ============================================================================
# Graph Write Node — Checkpointed LightRAG storage (replaces fire-and-forget)
# ============================================================================

async def research_to_graph_node(state: DeepResearchState) -> dict:
    """
    LangGraph node: store research insights in LightRAG.
    Checkpointed — if it fails, LangGraph can retry from synthesize checkpoint.
    """
    findings = state.get("findings", [])
    evaluated_sources = state.get("evaluated_sources", [])
    evidence_gaps = state.get("evidence_gaps", [])
    query = state.get("original_query", "")
    bot_id = state.get("bot_id", "lawrence")

    if not findings and not evaluated_sources:
        return {"graph_write_status": "skipped"}

    try:
        await _store_research_in_lightrag(
            query=query,
            findings=findings,
            evaluated_sources=evaluated_sources,
            evidence_gaps=evidence_gaps,
            bot_id=bot_id,
        )
        return {"graph_write_status": "success"}
    except Exception as e:
        logger.warning("research_to_graph failed: %s", e)
        return {"graph_write_status": "failed"}


# ============================================================================
# LightRAG Integration — Store research insights as graph entities/relations
# ============================================================================

async def _store_research_in_lightrag(
    query: str,
    findings: list,
    evaluated_sources: list,
    evidence_gaps: list,
    bot_id: str = "lawrence",
) -> None:
    """
    Store research insights, domains, and sub-domains in LightRAG graph.
    Stores ONLY relationships and metadata (no full content) for faster further research.

    Creates:
    - RESEARCH_INSIGHT entity (the query as a research topic)
    - DOMAIN entities for identified domains
    - SUBDOMAIN entities for specific sub-topics
    - Relationships: insight→domain, insight→subdomain, insight→source
    - Links to Bank of Opportunities if relevant

    This runs fire-and-forget after pipeline completion.
    """
    try:
        from tools.opportunity_bank_lightrag import _get_lightrag_session, LIGHTRAG_URL

        session = _get_lightrag_session()
        if not session:
            logger.debug("LightRAG session unavailable, skipping insight storage")
            return

        # Create the research insight entity (metadata only, no full content)
        insight_name = query[:120].strip()
        _create_entity(session, LIGHTRAG_URL, insight_name, "RESEARCH_INSIGHT", json.dumps({
            "query": query[:200],
            "sources_count": len(evaluated_sources),
            "high_authority_count": sum(1 for s in evaluated_sources if s.get("authority_score", 0) >= 0.85),
            "gaps_remaining": len(evidence_gaps),
            "bot_id": bot_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }))

        # Extract domains and sub-domains from findings titles and content
        domains_found = set()
        subdomains_found = set()

        for f in findings[:10]:
            title = f.get("title", "")
            content = f.get("fact", f.get("content", ""))[:200]

            # Use title as a sub-domain indicator
            if title and len(title) > 5:
                subdomains_found.add(title[:80])

        # Extract domain from high-authority sources
        for s in evaluated_sources[:10]:
            url = s.get("url", "")
            category = s.get("category", "")

            # Derive domain from URL patterns
            if ".edu" in url or ".ac." in url:
                domains_found.add("Academic Research")
            elif ".gov" in url:
                domains_found.add("Government & Policy")
            elif "arxiv" in url or "pubmed" in url or "nature.com" in url:
                domains_found.add("Scientific Literature")
            elif "techcrunch" in url or "venturebeat" in url:
                domains_found.add("Technology & Innovation")
            elif "bloomberg" in url or "wsj" in url or "reuters" in url:
                domains_found.add("Business & Finance")

        # Create domain entities and relationships
        for domain in domains_found:
            _create_entity(session, LIGHTRAG_URL, domain, "DOMAIN", domain)
            _create_relation(session, LIGHTRAG_URL,
                           insight_name, domain,
                           "researched in domain",
                           f"research, {domain.lower()}, {bot_id}")

        # Create sub-domain entities and relationships (top sources as sub-topics)
        for subdomain in list(subdomains_found)[:5]:
            _create_entity(session, LIGHTRAG_URL, subdomain, "SUBDOMAIN", subdomain)
            _create_relation(session, LIGHTRAG_URL,
                           insight_name, subdomain,
                           "covers sub-topic",
                           f"finding, {subdomain.lower()[:50]}")

        # Link high-authority sources as relationships (metadata only)
        for s in evaluated_sources[:5]:
            if s.get("authority_score", 0) >= 0.70:
                source_name = s.get("title", "")[:80]
                if source_name:
                    _create_entity(session, LIGHTRAG_URL, source_name, "SOURCE", json.dumps({
                        "url": s.get("url", ""),
                        "authority": s.get("authority_score", 0),
                        "category": s.get("category", ""),
                    }))
                    _create_relation(session, LIGHTRAG_URL,
                                   insight_name, source_name,
                                   "supported by source",
                                   f"evidence, {s.get('category', '')}")

        # Store evidence gaps as entities for future research targeting
        for gap in evidence_gaps[:3]:
            gap_name = gap[:80] if isinstance(gap, str) else str(gap)[:80]
            _create_entity(session, LIGHTRAG_URL, gap_name, "EVIDENCE_GAP", gap_name)
            _create_relation(session, LIGHTRAG_URL,
                           insight_name, gap_name,
                           "has evidence gap",
                           "gap, research needed")

        logger.info("[LightRAG] Stored research insight: '%s' (%d domains, %d subdomains, %d sources)",
                    insight_name[:50], len(domains_found), len(subdomains_found),
                    min(5, len(evaluated_sources)))

    except Exception as e:
        logger.warning("[LightRAG] Failed to store research insights: %s", e)


def _create_entity(session, base_url: str, name: str, entity_type: str, description: str) -> bool:
    """Create a single entity in LightRAG. Silent on failure."""
    try:
        resp = session.post(
            f"{base_url}/graph/entity/create",
            json={
                "entity_name": name,
                "entity_data": {
                    "entity_type": entity_type,
                    "description": description[:500],
                },
            },
            timeout=10,
        )
        return resp.status_code in (200, 201, 409)  # 409 = already exists
    except Exception:
        return False


def _create_relation(session, base_url: str, source: str, target: str,
                     description: str, keywords: str, weight: float = 0.8) -> bool:
    """Create a single relation in LightRAG. Silent on failure."""
    try:
        resp = session.post(
            f"{base_url}/graph/relation/create",
            json={
                "source_entity": source,
                "target_entity": target,
                "relation_data": {
                    "description": description,
                    "keywords": keywords,
                    "weight": weight,
                },
            },
            timeout=10,
        )
        return resp.status_code in (200, 201, 409)
    except Exception:
        return False
