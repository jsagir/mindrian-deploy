"""
Result Synthesizer for Mindrian Research Tools
================================================

Uses AI to filter, score relevance, and frame raw API results
to provide contextually meaningful insights instead of raw data dumps.

Key Features:
- Relevance scoring: ranks results by relevance to user's context
- Smart filtering: removes irrelevant/low-quality results
- PWS framing: presents findings through PWS methodology lens
- Source consolidation: deduplicates and merges related findings

Usage:
    from tools.result_synthesizer import synthesize_results, synthesize_research_batch

    # Single source synthesis
    synthesized = await synthesize_results(
        raw_results=tavily_response,
        source_type="web",
        user_context="I'm exploring EV battery technology for my startup",
        bot_id="lawrence"
    )

    # Multi-source batch synthesis
    batch_result = await synthesize_research_batch(
        sources={
            "web": tavily_results,
            "patents": patent_results,
            "papers": arxiv_results,
        },
        user_context="Market opportunity in solid-state batteries",
        bot_id="tta"
    )
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("result_synthesizer")

# Lazy load Gemini client
_client = None


def _get_client():
    """Get Gemini client (lazy initialization)."""
    global _client
    if _client is None:
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SynthesizedResult:
    """A single synthesized finding with relevance metadata."""
    title: str
    summary: str
    relevance_score: float  # 0.0 - 1.0
    relevance_reason: str
    source_type: str  # web, patent, paper, news, dataset, govdata
    source_url: str
    pws_insight: str  # How this relates to PWS methodology
    key_facts: List[str]
    assumptions_challenged: List[str]
    questions_raised: List[str]


@dataclass
class SynthesisReport:
    """Complete synthesis report from multiple sources."""
    query_context: str
    total_sources_processed: int
    relevant_sources: int
    top_findings: List[SynthesizedResult]
    synthesis_summary: str
    pws_implications: str
    recommended_next_steps: List[str]
    evidence_gaps: List[str]
    confidence_level: str  # high, medium, low


# ============================================================================
# Core Synthesis Functions
# ============================================================================

SYNTHESIS_PROMPT = """You are an expert research analyst for PWS (Problems Worth Solving) methodology.

Analyze these raw research results and provide a synthesized, contextually relevant response.

**User Context:** {user_context}

**Current Bot/Workshop:** {bot_id}

**Raw Results from {source_type}:**
{raw_results}

---

Your task:
1. **Filter** - Remove irrelevant results that don't relate to the user's context
2. **Score** - Rate each relevant result's usefulness (0.0-1.0)
3. **Extract** - Pull out key facts, statistics, and insights
4. **Frame** - Present through PWS lens (assumptions, evidence, problems worth solving)
5. **Connect** - Show how findings relate to user's specific situation

Respond in this JSON format:
```json
{{
    "relevant_findings": [
        {{
            "title": "Finding title",
            "summary": "2-3 sentence summary of why this matters",
            "relevance_score": 0.85,
            "relevance_reason": "Why this is relevant to user's context",
            "key_facts": ["Fact 1", "Fact 2"],
            "pws_insight": "How this relates to PWS methodology",
            "source_url": "URL if available",
            "assumptions_challenged": ["Assumption this challenges"],
            "questions_raised": ["Question this raises"]
        }}
    ],
    "synthesis_summary": "3-4 sentence synthesis of all findings",
    "pws_implications": "How these findings impact the user's problem/opportunity",
    "recommended_next_steps": ["Step 1", "Step 2"],
    "evidence_gaps": ["What data is still missing"],
    "confidence_level": "high/medium/low",
    "confidence_reason": "Why this confidence level"
}}
```

Important:
- Only include findings with relevance_score >= 0.5
- Focus on ACTIONABLE insights, not just information
- Highlight contradictions or surprising findings
- Connect to PWS concepts: assumptions, evidence, camera test, etc.
- Be concise but substantive
"""

BOT_CONTEXT = {
    "lawrence": "General PWS thinking partner. Focus on problem clarity, evidence quality, and assumption testing.",
    "larry_playground": "Full PWS lab. Deep analysis with all tools, multi-perspective examination.",
    "tta": "Trending to the Absurd. Focus on future trends, extrapolation, timing, emerging disruptions.",
    "jtbd": "Jobs to Be Done. Focus on customer jobs, progress, switching costs, hiring criteria.",
    "scurve": "S-Curve Analysis. Focus on technology lifecycle, dominant design, disruption timing.",
    "redteam": "Red Teaming. Focus on challenging assumptions, finding weaknesses, counter-evidence.",
    "ackoff": "Ackoff's DIKW Pyramid. Separate data from information, knowledge from wisdom.",
    "bono": "Six Thinking Hats. Multiple perspectives: facts, emotions, risks, benefits, creativity.",
}


async def synthesize_results(
    raw_results: Dict[str, Any],
    source_type: str,
    user_context: str,
    bot_id: str = "lawrence",
    max_results: int = 10,
) -> Dict:
    """
    Synthesize raw API results into contextually relevant findings.

    Args:
        raw_results: Raw response from a research API (Tavily, ArXiv, etc.)
        source_type: Type of source (web, patent, paper, news, dataset, govdata, trends)
        user_context: What the user is researching/working on
        bot_id: Current bot for framing context
        max_results: Max results to process

    Returns:
        Synthesized findings with relevance scores and PWS framing
    """
    # Format raw results based on source type
    formatted = _format_raw_results(raw_results, source_type, max_results)

    if not formatted:
        return {
            "success": False,
            "error": "No results to synthesize",
            "findings": [],
        }

    # Build the synthesis prompt
    bot_context = BOT_CONTEXT.get(bot_id, BOT_CONTEXT["lawrence"])

    prompt = SYNTHESIS_PROMPT.format(
        user_context=user_context[:1000],
        bot_id=f"{bot_id} - {bot_context}",
        source_type=source_type,
        raw_results=formatted[:8000],  # Limit to avoid token overflow
    )

    try:
        client = _get_client()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 4000,
            }
        )

        result_text = response.text

        # Parse JSON from response
        synthesis = _parse_json_response(result_text)

        if synthesis:
            synthesis["success"] = True
            synthesis["source_type"] = source_type
            synthesis["sources_processed"] = len(formatted.split("\n---"))
            return synthesis
        else:
            # Return simplified synthesis if JSON parsing failed
            return {
                "success": True,
                "source_type": source_type,
                "synthesis_summary": result_text[:1000],
                "relevant_findings": [],
                "pws_implications": "",
                "recommended_next_steps": [],
                "evidence_gaps": [],
                "confidence_level": "medium",
            }

    except Exception as e:
        logger.error("Synthesis error: %s", e)
        return {
            "success": False,
            "error": str(e),
            "findings": [],
        }


async def synthesize_research_batch(
    sources: Dict[str, Dict],
    user_context: str,
    bot_id: str = "lawrence",
) -> Dict:
    """
    Synthesize results from multiple research sources into a unified report.

    Args:
        sources: Dict of source_type -> raw_results
            e.g., {"web": tavily_results, "patents": patent_results}
        user_context: What the user is researching
        bot_id: Current bot for framing

    Returns:
        Unified synthesis report across all sources
    """
    # Process each source in parallel
    tasks = []
    for source_type, raw_results in sources.items():
        tasks.append(
            synthesize_results(raw_results, source_type, user_context, bot_id)
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine results
    all_findings = []
    total_processed = 0
    source_summaries = []

    for i, (source_type, _) in enumerate(sources.items()):
        result = results[i]
        if isinstance(result, Exception):
            logger.error("Batch synthesis error for %s: %s", source_type, result)
            continue

        if result.get("success"):
            findings = result.get("relevant_findings", [])
            all_findings.extend(findings)
            total_processed += result.get("sources_processed", 0)

            if result.get("synthesis_summary"):
                source_summaries.append(
                    f"**{source_type.title()}**: {result['synthesis_summary']}"
                )

    # Sort findings by relevance
    all_findings.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Generate unified synthesis
    unified = await _generate_unified_synthesis(
        all_findings[:15],  # Top 15 findings
        source_summaries,
        user_context,
        bot_id,
    )

    return {
        "success": True,
        "sources_queried": list(sources.keys()),
        "total_sources_processed": total_processed,
        "relevant_findings_count": len(all_findings),
        "top_findings": all_findings[:10],
        "source_summaries": source_summaries,
        **unified,
    }


# ============================================================================
# Formatting Functions
# ============================================================================

def _format_raw_results(raw: Dict, source_type: str, max_results: int = 10) -> str:
    """Format raw API results into text for synthesis."""
    parts = []

    if source_type == "web":
        # Tavily format
        results = raw.get("results", [])[:max_results]
        for i, r in enumerate(results, 1):
            parts.append(f"""
---
**Result {i}**
Title: {r.get('title', 'N/A')}
URL: {r.get('url', 'N/A')}
Content: {r.get('content', '')[:500]}
Score: {r.get('score', 'N/A')}
""")
        if raw.get("answer"):
            parts.insert(0, f"**Tavily Answer:** {raw['answer']}\n")

    elif source_type == "patent":
        patents = raw.get("patents", [])[:max_results]
        for i, p in enumerate(patents, 1):
            parts.append(f"""
---
**Patent {i}**
Title: {p.get('title', 'N/A')}
Patent ID: {p.get('patent_id', 'N/A')}
Assignee: {p.get('assignee', 'N/A')}
Inventor: {p.get('inventor', 'N/A')}
Published: {p.get('publication_date', 'N/A')}
Snippet: {p.get('snippet', '')[:400]}
URL: {p.get('url', 'N/A')}
""")

    elif source_type == "paper":
        papers = raw.get("papers", [])[:max_results]
        for i, p in enumerate(papers, 1):
            authors = ", ".join(p.get("authors", [])[:3])
            parts.append(f"""
---
**Paper {i}**
Title: {p.get('title', 'N/A')}
Authors: {authors}
Published: {p.get('published', 'N/A')}
Summary: {p.get('summary', '')[:400]}
Categories: {', '.join(p.get('categories', []))}
URL: {p.get('url', 'N/A')}
""")

    elif source_type == "news":
        articles = raw.get("articles", [])[:max_results]
        for i, a in enumerate(articles, 1):
            parts.append(f"""
---
**Article {i}**
Title: {a.get('title', 'N/A')}
Source: {a.get('source', 'N/A')}
Published: {a.get('published_at', 'N/A')}
Summary: {a.get('description', '')[:400]}
URL: {a.get('url', 'N/A')}
""")

    elif source_type == "trends":
        trends = raw.get("trends", []) or raw.get("interest_over_time", [])
        if trends:
            parts.append(f"**Trend Data for:** {raw.get('query', 'N/A')}")
            for t in trends[:max_results]:
                if isinstance(t, dict):
                    parts.append(f"- {t.get('keyword', t.get('query', 'N/A'))}: {t.get('value', t.get('interest', 'N/A'))}")
        related = raw.get("related_queries", [])
        if related:
            parts.append(f"\n**Related Queries:** {', '.join(str(q) for q in related[:10])}")

    elif source_type == "dataset":
        for source_key, data in raw.get("results", {}).items():
            datasets = data.get("datasets", [])[:max_results // 2]
            if datasets:
                parts.append(f"\n### {source_key.title()} Datasets")
                for i, d in enumerate(datasets, 1):
                    parts.append(f"""
---
**Dataset {i}**
Title: {d.get('title', 'N/A')}
Description: {d.get('description', '')[:300]}
URL: {d.get('url', 'N/A')}
Size: {d.get('size', 'N/A')}
""")

    elif source_type == "govdata":
        for source_key, data in raw.get("results", {}).items():
            if source_key == "bls":
                parts.append("\n### Bureau of Labor Statistics")
                for s in data.get("series", []):
                    latest = s.get("latest", {})
                    parts.append(f"- **{s.get('label', 'N/A')}**: {latest.get('value', 'N/A')} ({latest.get('year', '')}-{latest.get('period', '')})")
            elif source_key == "fred":
                parts.append("\n### Federal Reserve Economic Data")
                for s in data.get("series", []):
                    parts.append(f"- **{s.get('title', 'N/A')}**: {s.get('latest_value', 'N/A')} ({s.get('latest_date', '')})")
            elif source_key == "census":
                parts.append(f"\n### Census ACS ({data.get('year', '')})")
                parts.append(f"Variables: {', '.join(data.get('variables', []))}")

    else:
        # Generic format
        parts.append(json.dumps(raw, indent=2, default=str)[:4000])

    return "\n".join(parts)


def _parse_json_response(text: str) -> Optional[Dict]:
    """Parse JSON from model response, handling markdown code blocks."""
    # Try to find JSON in code blocks
    import re

    # Look for ```json ... ``` blocks
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try parsing the whole text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try finding any {...} in the text
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return None


async def _generate_unified_synthesis(
    findings: List[Dict],
    source_summaries: List[str],
    user_context: str,
    bot_id: str,
) -> Dict:
    """Generate a unified synthesis from multiple source findings."""
    if not findings:
        return {
            "unified_synthesis": "No relevant findings to synthesize.",
            "key_insights": [],
            "recommended_actions": [],
        }

    findings_text = "\n".join([
        f"- [{f.get('relevance_score', 0):.2f}] {f.get('title', 'N/A')}: {f.get('summary', '')[:200]}"
        for f in findings
    ])

    summaries_text = "\n".join(source_summaries) if source_summaries else "No summaries available."

    prompt = f"""Synthesize these research findings into a unified, actionable insight for PWS methodology.

**User's Research Context:** {user_context}

**Source Summaries:**
{summaries_text}

**Top Findings (sorted by relevance):**
{findings_text}

Provide:
1. **Unified Synthesis** (3-4 sentences): What does all this research tell us?
2. **Key Insights** (3-5 bullets): The most important takeaways
3. **PWS Implications**: How does this affect problem-solving approach?
4. **Recommended Actions** (2-3 specific next steps)
5. **Evidence Gaps**: What questions remain unanswered?

Be concise, actionable, and connect to PWS methodology (assumptions, evidence, camera test).
"""

    try:
        client = _get_client()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "temperature": 0.4,
                "max_output_tokens": 1500,
            }
        )

        return {
            "unified_synthesis": response.text,
            "key_insights": [],  # Could parse from response if structured
            "recommended_actions": [],
        }

    except Exception as e:
        logger.error("Unified synthesis error: %s", e)
        return {
            "unified_synthesis": "Unable to generate unified synthesis.",
            "error": str(e),
        }


# ============================================================================
# Quick Synthesis (for real-time use)
# ============================================================================

async def quick_synthesize(
    raw_results: Dict,
    source_type: str,
    question: str,
    max_findings: int = 5,
) -> str:
    """
    Quick synthesis for real-time chat responses.
    Returns a formatted markdown string ready to display.

    Args:
        raw_results: Raw API response
        source_type: Type of source
        question: User's original question
        max_findings: Max findings to include

    Returns:
        Formatted markdown string
    """
    synthesis = await synthesize_results(
        raw_results,
        source_type,
        user_context=question,
        bot_id="lawrence",
        max_results=max_findings * 2,
    )

    if not synthesis.get("success"):
        return f"*Research synthesis unavailable: {synthesis.get('error', 'Unknown error')}*"

    parts = []

    # Synthesis summary
    if synthesis.get("synthesis_summary"):
        parts.append(f"**Key Findings:**\n{synthesis['synthesis_summary']}\n")

    # Top findings
    findings = synthesis.get("relevant_findings", [])
    if findings:
        parts.append("**Most Relevant Results:**")
        for i, f in enumerate(findings[:max_findings], 1):
            score = f.get("relevance_score", 0)
            title = f.get("title", "Untitled")
            summary = f.get("summary", "")[:200]
            url = f.get("source_url", "")

            relevance_indicator = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🟠"

            parts.append(f"\n{i}. {relevance_indicator} **{title}**")
            if summary:
                parts.append(f"   {summary}")
            if url:
                parts.append(f"   [{url}]({url})")

    # PWS implications
    if synthesis.get("pws_implications"):
        parts.append(f"\n**PWS Implications:**\n{synthesis['pws_implications']}")

    # Evidence gaps
    gaps = synthesis.get("evidence_gaps", [])
    if gaps:
        parts.append(f"\n**Questions to Explore:**")
        for gap in gaps[:3]:
            parts.append(f"- {gap}")

    return "\n".join(parts) if parts else "*No relevant findings synthesized.*"


# ============================================================================
# Integration Helpers
# ============================================================================

def get_synthesis_config_for_bot(bot_id: str) -> Dict:
    """Get synthesis configuration optimized for specific bot."""
    configs = {
        "lawrence": {
            "focus": "problem clarity and evidence quality",
            "max_findings": 5,
            "emphasis": ["assumptions", "evidence gaps", "camera test criteria"],
        },
        "tta": {
            "focus": "future trends and timing",
            "max_findings": 7,
            "emphasis": ["trend direction", "adoption timing", "disruption signals"],
        },
        "jtbd": {
            "focus": "customer jobs and progress",
            "max_findings": 5,
            "emphasis": ["functional jobs", "emotional jobs", "switching costs"],
        },
        "scurve": {
            "focus": "technology lifecycle positioning",
            "max_findings": 6,
            "emphasis": ["maturity stage", "dominant design", "disruption timing"],
        },
        "redteam": {
            "focus": "challenging assumptions and finding weaknesses",
            "max_findings": 8,
            "emphasis": ["counter-evidence", "failure modes", "blind spots"],
        },
        "ackoff": {
            "focus": "data-information-knowledge-wisdom hierarchy",
            "max_findings": 6,
            "emphasis": ["data quality", "knowledge gaps", "wisdom implications"],
        },
    }
    return configs.get(bot_id, configs["lawrence"])
