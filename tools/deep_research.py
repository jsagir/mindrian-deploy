"""
Gemini Deep Research Integration
=================================

Uses Google's Deep Research agent (Interactions API) for comprehensive,
multi-source autonomous research that takes 5-20 minutes.

The graph orchestrator composes a research-grade query using:
  - LazyGraphRAG concept co-occurrence for keyword enrichment
  - ProblemType → Cynefin → Framework chain for framing
  - Technique names for specificity

Results are stored in Supabase and injected into conversation context.

API: https://ai.google.dev/gemini-api/docs/deep-research
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger("deep_research")

# Gemini client (reuse from mindrian_chat)
_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client


# ── Query Composition (graph-enriched) ──────────────────────────────────────

def compose_research_query(
    user_topic: str,
    conversation_context: str = "",
    bot_id: str = "larry",
) -> Tuple[str, Dict]:
    """
    Compose a research-grade query using LazyGraphRAG + graph orchestrator.

    Layers:
      1. LazyGraphRAG: concept co-occurrence, community context, cross-domain signals
      2. Graph Orchestrator: ProblemType, Cynefin domain, frameworks, techniques
      3. Bot context: what the current bot cares about

    Returns:
        (composed_query, trace_dict)
    """
    trace = {
        "user_topic": user_topic[:100],
        "bot_id": bot_id,
        "lazy_concepts": [],
        "problem_type": None,
        "cynefin_domain": None,
        "frameworks": [],
        "techniques": [],
    }

    parts = [user_topic]

    # Layer 1: LazyGraphRAG enrichment
    try:
        from tools.graphrag_lite import (
            _extract_keywords, lazy_multi_concept_context,
            get_related_frameworks, get_problem_context,
        )

        keywords = _extract_keywords(user_topic)
        if keywords:
            lazy_hint, lazy_trace = lazy_multi_concept_context(keywords)
            if lazy_hint:
                parts.append(f"Key concepts and relationships: {lazy_hint}")
                trace["lazy_concepts"] = lazy_trace.get("matched_concepts", [])

        # Framework suggestions from entity layer
        frameworks = get_related_frameworks(user_topic, limit=3)
        if frameworks:
            fw_names = [f["name"] for f in frameworks]
            parts.append(f"Analyze through the lens of: {', '.join(fw_names)}")
            trace["frameworks"].extend(fw_names)

        # Problem context
        problem = get_problem_context(user_topic)
        if problem.get("problem_type"):
            parts.append(f"Problem classification: {problem['problem_type']}")
            trace["problem_type"] = problem["problem_type"]
            if problem.get("approaches"):
                parts.append(f"Recommended approaches: {', '.join(problem['approaches'][:3])}")

    except Exception as e:
        logger.warning("LazyGraphRAG enrichment failed (non-fatal): %s", e)

    # Layer 2: Graph Orchestrator (ProblemType → Cynefin → Framework → Technique)
    try:
        from tools.graph_orchestrator import discover_research_plan
        plan = discover_research_plan(user_topic)

        if plan.problem_type and not trace["problem_type"]:
            trace["problem_type"] = plan.problem_type
        if plan.cynefin_domain:
            trace["cynefin_domain"] = plan.cynefin_domain
            parts.append(f"Complexity domain: {plan.cynefin_domain}")
        if plan.frameworks:
            new_fws = [f["name"] for f in plan.frameworks if f["name"] not in trace["frameworks"]]
            trace["frameworks"].extend(new_fws)
        if plan.techniques:
            unique_techniques = list(dict.fromkeys(plan.techniques))[:5]
            trace["techniques"] = unique_techniques
            parts.append(f"Apply techniques: {', '.join(unique_techniques)}")

    except Exception as e:
        logger.warning("Graph orchestrator enrichment failed (non-fatal): %s", e)

    # Layer 3: Conversation context (last few turns for grounding)
    if conversation_context:
        # Truncate to avoid hitting token limits
        ctx_truncated = conversation_context[-1500:]
        parts.append(f"Conversation context: {ctx_truncated}")

    # Layer 4: Bot-specific research framing
    bot_framing = {
        "larry": "Focus on Problems Worth Solving methodology. Identify assumptions, evidence gaps, and validation needs.",
        "tta": "Focus on future trends, extrapolation, emerging disruptions, and timing of technology adoption.",
        "jtbd": "Focus on customer jobs, hiring criteria, functional/emotional/social dimensions, and switching costs.",
        "scurve": "Focus on technology lifecycle positioning, dominant design emergence, and disruption timing.",
        "redteam": "Focus on finding weaknesses, challenging assumptions, stress-testing with counter-evidence.",
        "ackoff": "Focus on DIKW pyramid: separate data from information, knowledge from wisdom.",
        "bono": "Focus on multiple perspectives: facts, emotions, risks, benefits, creativity, and meta-analysis.",
    }
    if bot_id in bot_framing:
        parts.append(bot_framing[bot_id])

    composed = "\n\n".join(parts)
    logger.info(
        "Deep research query composed: %d chars, concepts=%s, frameworks=%s, domain=%s",
        len(composed), trace["lazy_concepts"], trace["frameworks"], trace["cynefin_domain"]
    )
    return composed, trace


# ── Gemini Deep Research Execution ──────────────────────────────────────────

async def start_deep_research(query: str) -> Dict:
    """
    Start a Gemini Deep Research interaction (async, background).

    Returns:
        {"interaction_id": str, "status": "started"} or {"error": str}
    """
    client = _get_client()
    try:
        interaction = client.interactions.create(
            input=query,
            agent="deep-research-pro-preview-12-2025",
            background=True,
        )
        logger.info("Deep research started: id=%s", interaction.id)
        return {
            "interaction_id": interaction.id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Deep research start failed: %s", e)
        return {"error": str(e)}


async def poll_deep_research(
    interaction_id: str,
    poll_interval: int = 15,
    max_polls: int = 80,  # 80 * 15s = 20 min max
    on_progress=None,
) -> Dict:
    """
    Poll a running Deep Research interaction until completion.

    Args:
        interaction_id: The interaction ID from start_deep_research()
        poll_interval: Seconds between polls
        max_polls: Maximum number of polls before timeout
        on_progress: Optional async callback(poll_count, elapsed_sec) for UI updates

    Returns:
        {"status": "completed", "report": str, "elapsed_sec": int}
        or {"status": "failed", "error": str}
        or {"status": "timeout"}
    """
    client = _get_client()
    t0 = time.time()

    for poll_count in range(1, max_polls + 1):
        await asyncio.sleep(poll_interval)

        try:
            interaction = client.interactions.get(interaction_id)
        except Exception as e:
            logger.error("Poll error: %s", e)
            continue

        elapsed = int(time.time() - t0)

        if interaction.status == "completed":
            report = ""
            if interaction.outputs:
                report = interaction.outputs[-1].text or ""
            logger.info("Deep research completed: %d sec, %d chars", elapsed, len(report))
            return {
                "status": "completed",
                "report": report,
                "elapsed_sec": elapsed,
                "interaction_id": interaction_id,
            }

        elif interaction.status == "failed":
            error = getattr(interaction, "error", "Unknown error")
            logger.error("Deep research failed: %s", error)
            return {
                "status": "failed",
                "error": str(error),
                "elapsed_sec": elapsed,
            }

        # Progress callback for UI
        if on_progress:
            try:
                await on_progress(poll_count, elapsed)
            except Exception:
                pass

    return {"status": "timeout", "elapsed_sec": int(time.time() - t0)}


# ── Storage ─────────────────────────────────────────────────────────────────

def save_report_to_supabase(
    report: str,
    topic: str,
    trace: Dict,
    bot_id: str = "larry",
) -> Optional[str]:
    """
    Save a deep research report to Supabase Storage.

    Path: deep-research/{date}/{topic_slug}.md

    Returns:
        Public URL or None if storage unavailable.
    """
    try:
        from utils.storage import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            logger.info("Supabase not configured, skipping report storage")
            return None

        # Build path
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        slug = _slugify(topic)[:60]
        storage_path = f"deep-research/{date_str}/{slug}.md"

        # Build markdown report with metadata header
        header = f"""---
topic: {topic[:100]}
bot: {bot_id}
date: {datetime.utcnow().isoformat()}
problem_type: {trace.get('problem_type', 'unknown')}
cynefin_domain: {trace.get('cynefin_domain', 'unknown')}
frameworks: {', '.join(trace.get('frameworks', []))}
concepts: {', '.join(trace.get('lazy_concepts', []))}
---

"""
        full_content = header + report

        # Upload
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=full_content.encode("utf-8"),
            file_options={"content-type": "text/markdown"},
        )

        public_url = client.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
        logger.info("Report saved: %s", storage_path)
        return public_url

    except Exception as e:
        logger.error("Report storage failed: %s", e)
        return None


def save_report_to_json(
    report: str,
    topic: str,
    trace: Dict,
    bot_id: str = "larry",
) -> Optional[str]:
    """
    Save report metadata as JSON to Supabase for analytics.

    Path: deep-research/{date}/{topic_slug}.json
    """
    try:
        from utils.storage import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            return None

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        slug = _slugify(topic)[:60]
        storage_path = f"deep-research/{date_str}/{slug}.json"

        metadata = {
            "topic": topic,
            "bot_id": bot_id,
            "timestamp": datetime.utcnow().isoformat(),
            "report_length": len(report),
            "trace": trace,
        }

        client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=json.dumps(metadata, indent=2).encode("utf-8"),
            file_options={"content-type": "application/json"},
        )
        return storage_path

    except Exception as e:
        logger.error("Report JSON storage failed: %s", e)
        return None


def _slugify(text: str) -> str:
    """Simple slugify for file paths."""
    import re
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


# ── High-Level Orchestration ────────────────────────────────────────────────

async def run_deep_research(
    topic: str,
    conversation_context: str = "",
    bot_id: str = "larry",
    on_progress=None,
) -> Dict:
    """
    Full deep research pipeline:
      1. Compose query (LazyGraphRAG + orchestrator)
      2. Start Gemini Deep Research
      3. Poll until completion
      4. Save to Supabase

    Args:
        topic: User's research topic
        conversation_context: Recent conversation for grounding
        bot_id: Active bot
        on_progress: async callback(poll_count, elapsed_sec)

    Returns:
        {
            "status": "completed" | "failed" | "timeout",
            "report": str,
            "report_url": str | None,
            "summary": str,  # first 500 chars
            "trace": dict,
            "elapsed_sec": int,
        }
    """
    # Step 1: Compose enriched query
    composed_query, trace = compose_research_query(topic, conversation_context, bot_id)

    # Step 2: Start deep research
    start_result = await start_deep_research(composed_query)
    if "error" in start_result:
        return {
            "status": "failed",
            "error": start_result["error"],
            "report": "",
            "trace": trace,
            "elapsed_sec": 0,
        }

    # Step 3: Poll
    poll_result = await poll_deep_research(
        start_result["interaction_id"],
        on_progress=on_progress,
    )

    report = poll_result.get("report", "")
    elapsed = poll_result.get("elapsed_sec", 0)

    # Step 4: Save to Supabase
    report_url = None
    if report:
        report_url = save_report_to_supabase(report, topic, trace, bot_id)
        save_report_to_json(report, topic, trace, bot_id)

    return {
        "status": poll_result.get("status", "unknown"),
        "report": report,
        "report_url": report_url,
        "summary": report[:500] if report else "",
        "trace": trace,
        "elapsed_sec": elapsed,
    }
