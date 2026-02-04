"""
Research Contextualization Layer
================================

Transforms raw research results into humanized, context-aware insights.

Problem Solved:
- Raw API results (patents, news, trends) dumped without context = useless
- User gets "dead patents" or irrelevant news that don't connect to their exploration
- No synthesis of what results MEAN for the user's problem

Solution:
- Analyze results against conversation context
- Filter out irrelevant/low-quality results
- Synthesize insights explaining WHY each matters
- Present in human-readable, actionable format

Usage:
    from utils.research_contextualizer import contextualize_research

    # After getting raw results from any research API
    contextual_output = await contextualize_research(
        research_type="patents",
        raw_results=results,
        conversation_context=history[-6:],
        user_problem="urban farming economics"
    )
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("mindrian.research")

# =============================================================================
# RESEARCH TYPES
# =============================================================================

class ResearchType(str, Enum):
    PATENTS = "patents"
    NEWS = "news"
    ACADEMIC = "academic"  # arxiv
    TRENDS = "trends"
    GOVDATA = "govdata"
    DATASETS = "datasets"


# =============================================================================
# CONTEXTUALIZATION PROMPTS
# =============================================================================

CONTEXTUALIZATION_PROMPTS = {
    ResearchType.PATENTS: """You are analyzing patent search results for a user exploring: {user_problem}

CONVERSATION CONTEXT:
{conversation_summary}

RAW PATENT RESULTS:
{raw_results}

YOUR TASK:
1. Filter out patents that are NOT relevant to the user's current exploration
2. For each RELEVANT patent, explain in 1-2 sentences WHY it matters to their problem
3. Identify any patterns or insights across the patents
4. Flag if results suggest the space is crowded vs. open for innovation

OUTPUT FORMAT (JSON):
{{
    "relevant_count": <number>,
    "total_count": <number>,
    "relevance_summary": "<1 sentence: how relevant were these results?>",
    "key_insight": "<main takeaway for the user>",
    "relevant_patents": [
        {{
            "title": "<patent title>",
            "why_relevant": "<1-2 sentences explaining relevance to user's exploration>",
            "implication": "<what this means for their opportunity>"
        }}
    ],
    "landscape_assessment": "<is this space crowded/open/emerging?>",
    "recommendation": "<what should user do with this information?>"
}}

Be HONEST. If results are not relevant, say so. Don't force connections.""",

    ResearchType.NEWS: """You are analyzing news search results for a user exploring: {user_problem}

CONVERSATION CONTEXT:
{conversation_summary}

RAW NEWS RESULTS:
{raw_results}

YOUR TASK:
1. Filter out news that is NOT relevant to the user's current exploration
2. For each RELEVANT article, explain WHY it matters and what signal it represents
3. Identify trends, sentiment, or patterns across articles
4. Highlight any breaking developments or emerging opportunities

OUTPUT FORMAT (JSON):
{{
    "relevant_count": <number>,
    "total_count": <number>,
    "relevance_summary": "<1 sentence: how relevant were these results?>",
    "key_insight": "<main takeaway about current news landscape>",
    "relevant_articles": [
        {{
            "title": "<article title>",
            "source": "<news source>",
            "why_relevant": "<1-2 sentences explaining relevance>",
            "signal": "<what this news signals for the problem space>"
        }}
    ],
    "trend_direction": "<growing/declining/stable/emerging>",
    "timeliness": "<is this a hot topic now or evergreen?>",
    "recommendation": "<what should user do with this information?>"
}}

Be HONEST. If news isn't relevant or useful, say so clearly.""",

    ResearchType.ACADEMIC: """You are analyzing academic paper results for a user exploring: {user_problem}

CONVERSATION CONTEXT:
{conversation_summary}

RAW ARXIV RESULTS:
{raw_results}

YOUR TASK:
1. Filter out papers that are NOT relevant to the user's problem
2. For each RELEVANT paper, explain the key finding and why it matters
3. Identify the current state of research in this space
4. Highlight any research gaps that could be opportunities

OUTPUT FORMAT (JSON):
{{
    "relevant_count": <number>,
    "total_count": <number>,
    "relevance_summary": "<how relevant is academic research to this problem?>",
    "key_insight": "<main takeaway from the research landscape>",
    "relevant_papers": [
        {{
            "title": "<paper title>",
            "authors": "<key authors>",
            "key_finding": "<main finding in plain English>",
            "why_relevant": "<how this applies to user's exploration>",
            "practical_implication": "<what can be done with this knowledge>"
        }}
    ],
    "research_maturity": "<nascent/developing/mature/saturated>",
    "gaps_identified": ["<potential research/opportunity gaps>"],
    "recommendation": "<what should user do with this information?>"
}}

Translate academic jargon into plain English. Be honest if papers aren't relevant.""",

    ResearchType.TRENDS: """You are analyzing Google Trends data for a user exploring: {user_problem}

CONVERSATION CONTEXT:
{conversation_summary}

RAW TRENDS RESULTS:
{raw_results}

YOUR TASK:
1. Interpret what the trend data actually MEANS (not just numbers)
2. Explain the trajectory and what's driving it
3. Identify related queries that reveal adjacent opportunities
4. Assess market timing implications

OUTPUT FORMAT (JSON):
{{
    "trend_interpretation": "<what does this trend data actually tell us?>",
    "key_insight": "<main takeaway about market interest>",
    "trajectory": {{
        "direction": "<growing/declining/stable/volatile>",
        "momentum": "<accelerating/decelerating/steady>",
        "seasonality": "<any seasonal patterns?>"
    }},
    "related_opportunities": [
        {{
            "query": "<related search term>",
            "why_interesting": "<what this reveals about the market>"
        }}
    ],
    "timing_assessment": "<is now a good time to enter this space?>",
    "recommendation": "<what should user do with this information?>"
}}

Focus on ACTIONABLE insights, not just data description.""",

    ResearchType.GOVDATA: """You are analyzing government/economic data for a user exploring: {user_problem}

CONVERSATION CONTEXT:
{conversation_summary}

RAW DATA RESULTS:
{raw_results}

YOUR TASK:
1. Interpret what the statistics actually MEAN for the user's exploration
2. Identify relevant economic/demographic signals
3. Highlight any surprising findings or trends
4. Connect data to potential opportunities

OUTPUT FORMAT (JSON):
{{
    "data_interpretation": "<what does this data tell us in plain English?>",
    "key_insight": "<main takeaway for the user's problem>",
    "relevant_metrics": [
        {{
            "metric": "<metric name>",
            "value": "<current value>",
            "trend": "<direction>",
            "implication": "<what this means for the opportunity>"
        }}
    ],
    "market_signals": ["<economic/demographic signals relevant to problem>"],
    "recommendation": "<what should user do with this information?>"
}}

Make statistics meaningful. Connect numbers to real-world implications.""",

    ResearchType.DATASETS: """You are analyzing dataset search results for a user exploring: {user_problem}

CONVERSATION CONTEXT:
{conversation_summary}

RAW DATASET RESULTS:
{raw_results}

YOUR TASK:
1. Filter datasets by actual usefulness for the user's exploration
2. Assess data quality and accessibility
3. Identify what insights could be extracted from each dataset
4. Recommend specific analyses that could be done

OUTPUT FORMAT (JSON):
{{
    "relevant_count": <number>,
    "total_count": <number>,
    "relevance_summary": "<how useful are these datasets?>",
    "key_insight": "<main opportunity from available data>",
    "relevant_datasets": [
        {{
            "name": "<dataset name>",
            "source": "<Kaggle/Socrata/etc>",
            "why_useful": "<what questions this data could answer>",
            "potential_analysis": "<specific analysis to run>",
            "accessibility": "<easy/moderate/complex>"
        }}
    ],
    "data_gaps": ["<what data is missing that would help?>"],
    "recommendation": "<what should user do with this information?>"
}}

Focus on ACTIONABLE data, not just data availability."""
}


# =============================================================================
# MAIN CONTEXTUALIZATION FUNCTION
# =============================================================================

async def contextualize_research(
    research_type: str,
    raw_results: Any,
    conversation_context: List[Dict],
    user_problem: str = None,
    search_query: str = None,
) -> Dict[str, Any]:
    """
    Transform raw research results into humanized, context-aware insights.

    Args:
        research_type: Type of research (patents, news, academic, trends, govdata, datasets)
        raw_results: Raw results from the research API
        conversation_context: Recent conversation history (last 4-6 messages)
        user_problem: Extracted problem statement (optional, will infer if not provided)
        search_query: The query that was used (for reference)

    Returns:
        Dict with contextualized insights and relevant results
    """
    from google import genai

    # Get client
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        logger.warning("[CONTEXTUALIZE] No API key, returning raw results")
        return {"raw_results": raw_results, "contextualized": False}

    client = genai.Client(api_key=api_key)

    # Normalize research type
    try:
        r_type = ResearchType(research_type.lower())
    except ValueError:
        logger.warning(f"[CONTEXTUALIZE] Unknown research type: {research_type}")
        return {"raw_results": raw_results, "contextualized": False}

    # Build conversation summary
    conversation_summary = _summarize_conversation(conversation_context)

    # Infer user problem if not provided
    if not user_problem:
        user_problem = await _extract_user_problem(client, conversation_context)

    # Format raw results for the prompt
    raw_results_str = _format_raw_results(raw_results, r_type)

    # Check if we have any results to contextualize
    if not raw_results_str or raw_results_str.strip() == "No results found.":
        return {
            "contextualized": True,
            "relevant_count": 0,
            "total_count": 0,
            "key_insight": "No results found for this search. Try broadening your query or exploring adjacent topics.",
            "recommendation": "Consider refining your search or exploring related areas.",
            "raw_results": raw_results
        }

    # Get the appropriate prompt
    prompt_template = CONTEXTUALIZATION_PROMPTS.get(r_type)
    if not prompt_template:
        return {"raw_results": raw_results, "contextualized": False}

    prompt = prompt_template.format(
        user_problem=user_problem,
        conversation_summary=conversation_summary,
        raw_results=raw_results_str
    )

    # Call Gemini for contextualization
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        # Parse JSON response
        result_text = response.text.strip()
        # Handle markdown code blocks
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()

        contextualized = json.loads(result_text)
        contextualized["contextualized"] = True
        contextualized["search_query"] = search_query
        contextualized["user_problem"] = user_problem

        return contextualized

    except json.JSONDecodeError as e:
        logger.warning(f"[CONTEXTUALIZE] JSON parse error: {e}")
        # Return partial result with the raw text
        return {
            "contextualized": True,
            "raw_analysis": response.text if 'response' in dir() else "",
            "raw_results": raw_results,
            "parse_error": True
        }
    except Exception as e:
        logger.error(f"[CONTEXTUALIZE] Error: {e}")
        return {"raw_results": raw_results, "contextualized": False, "error": str(e)}


# =============================================================================
# FORMATTING FUNCTIONS
# =============================================================================

def format_contextualized_output(
    contextualized: Dict[str, Any],
    research_type: str,
    search_query: str = None
) -> str:
    """
    Format contextualized results for display in chat.

    Returns markdown-formatted string ready for cl.Message.
    """
    if not contextualized.get("contextualized"):
        return "Unable to contextualize results. Showing raw data."

    r_type = research_type.lower()

    # Header with relevance summary
    output = []

    relevant = contextualized.get("relevant_count", "?")
    total = contextualized.get("total_count", "?")

    if relevant == 0:
        output.append(f"**No directly relevant results found.**")
        output.append(f"\n*{contextualized.get('relevance_summary', 'The search returned results but none matched your current exploration.')}*\n")
    else:
        output.append(f"**Found {relevant} relevant results** (out of {total} total)\n")

    # Key Insight (always show)
    key_insight = contextualized.get("key_insight")
    if key_insight:
        output.append(f"### Key Insight\n{key_insight}\n")

    # Type-specific formatting
    if r_type == "patents":
        output.append(_format_patent_results(contextualized))
    elif r_type == "news":
        output.append(_format_news_results(contextualized))
    elif r_type == "academic":
        output.append(_format_academic_results(contextualized))
    elif r_type == "trends":
        output.append(_format_trends_results(contextualized))
    elif r_type == "govdata":
        output.append(_format_govdata_results(contextualized))
    elif r_type == "datasets":
        output.append(_format_dataset_results(contextualized))

    # Recommendation (always show at end)
    recommendation = contextualized.get("recommendation")
    if recommendation:
        output.append(f"\n### What This Means For You\n{recommendation}")

    # Legal disclaimer (always at end)
    output.append("\n---\n*📋 Disclaimer: Research results are for informational purposes only. Verify important findings from primary sources before making decisions.*")

    return "\n".join(output)


def _format_patent_results(ctx: Dict) -> str:
    """Format contextualized patent results."""
    lines = []

    patents = ctx.get("relevant_patents", [])
    if patents:
        lines.append("### Relevant Patents\n")
        for i, p in enumerate(patents[:5], 1):
            lines.append(f"**{i}. {p.get('title', 'Untitled')}**")
            lines.append(f"   - *Why it matters:* {p.get('why_relevant', 'N/A')}")
            if p.get('implication'):
                lines.append(f"   - *Implication:* {p.get('implication')}")
            lines.append("")

    landscape = ctx.get("landscape_assessment")
    if landscape:
        lines.append(f"### Innovation Landscape\n{landscape}\n")

    return "\n".join(lines)


def _format_news_results(ctx: Dict) -> str:
    """Format contextualized news results."""
    lines = []

    articles = ctx.get("relevant_articles", [])
    if articles:
        lines.append("### Relevant News\n")
        for i, a in enumerate(articles[:5], 1):
            source = a.get('source', 'Unknown')
            lines.append(f"**{i}. {a.get('title', 'Untitled')}** ({source})")
            lines.append(f"   - *Why it matters:* {a.get('why_relevant', 'N/A')}")
            if a.get('signal'):
                lines.append(f"   - *Signal:* {a.get('signal')}")
            lines.append("")

    trend = ctx.get("trend_direction")
    timeliness = ctx.get("timeliness")
    if trend or timeliness:
        lines.append(f"### Market Signal")
        if trend:
            lines.append(f"- **Trend:** {trend}")
        if timeliness:
            lines.append(f"- **Timeliness:** {timeliness}")
        lines.append("")

    return "\n".join(lines)


def _format_academic_results(ctx: Dict) -> str:
    """Format contextualized academic results."""
    lines = []

    papers = ctx.get("relevant_papers", [])
    if papers:
        lines.append("### Relevant Research\n")
        for i, p in enumerate(papers[:5], 1):
            lines.append(f"**{i}. {p.get('title', 'Untitled')}**")
            if p.get('key_finding'):
                lines.append(f"   - *Key finding:* {p.get('key_finding')}")
            lines.append(f"   - *Why it matters:* {p.get('why_relevant', 'N/A')}")
            if p.get('practical_implication'):
                lines.append(f"   - *Practical use:* {p.get('practical_implication')}")
            lines.append("")

    maturity = ctx.get("research_maturity")
    if maturity:
        lines.append(f"### Research Maturity: {maturity.title()}\n")

    gaps = ctx.get("gaps_identified", [])
    if gaps:
        lines.append("### Opportunity Gaps")
        for gap in gaps[:3]:
            lines.append(f"- {gap}")
        lines.append("")

    return "\n".join(lines)


def _format_trends_results(ctx: Dict) -> str:
    """Format contextualized trends results."""
    lines = []

    interpretation = ctx.get("trend_interpretation")
    if interpretation:
        lines.append(f"### What The Data Shows\n{interpretation}\n")

    trajectory = ctx.get("trajectory", {})
    if trajectory:
        lines.append("### Trajectory")
        lines.append(f"- **Direction:** {trajectory.get('direction', 'Unknown')}")
        lines.append(f"- **Momentum:** {trajectory.get('momentum', 'Unknown')}")
        if trajectory.get('seasonality'):
            lines.append(f"- **Seasonality:** {trajectory.get('seasonality')}")
        lines.append("")

    opportunities = ctx.get("related_opportunities", [])
    if opportunities:
        lines.append("### Related Opportunities")
        for opp in opportunities[:4]:
            lines.append(f"- **{opp.get('query', '?')}**: {opp.get('why_interesting', '')}")
        lines.append("")

    timing = ctx.get("timing_assessment")
    if timing:
        lines.append(f"### Market Timing\n{timing}\n")

    return "\n".join(lines)


def _format_govdata_results(ctx: Dict) -> str:
    """Format contextualized government data results."""
    lines = []

    interpretation = ctx.get("data_interpretation")
    if interpretation:
        lines.append(f"### What The Data Shows\n{interpretation}\n")

    metrics = ctx.get("relevant_metrics", [])
    if metrics:
        lines.append("### Key Metrics")
        for m in metrics[:5]:
            trend_icon = "📈" if "up" in m.get('trend', '').lower() or "grow" in m.get('trend', '').lower() else "📉" if "down" in m.get('trend', '').lower() or "declin" in m.get('trend', '').lower() else "➡️"
            lines.append(f"- **{m.get('metric', '?')}**: {m.get('value', '?')} {trend_icon}")
            if m.get('implication'):
                lines.append(f"  *{m.get('implication')}*")
        lines.append("")

    signals = ctx.get("market_signals", [])
    if signals:
        lines.append("### Market Signals")
        for s in signals[:3]:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


def _format_dataset_results(ctx: Dict) -> str:
    """Format contextualized dataset results."""
    lines = []

    datasets = ctx.get("relevant_datasets", [])
    if datasets:
        lines.append("### Useful Datasets\n")
        for i, d in enumerate(datasets[:5], 1):
            lines.append(f"**{i}. {d.get('name', 'Untitled')}** ({d.get('source', 'Unknown')})")
            lines.append(f"   - *Why useful:* {d.get('why_useful', 'N/A')}")
            if d.get('potential_analysis'):
                lines.append(f"   - *Analysis to run:* {d.get('potential_analysis')}")
            if d.get('accessibility'):
                lines.append(f"   - *Accessibility:* {d.get('accessibility')}")
            lines.append("")

    gaps = ctx.get("data_gaps", [])
    if gaps:
        lines.append("### Data Gaps")
        for gap in gaps[:3]:
            lines.append(f"- {gap}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _summarize_conversation(history: List[Dict]) -> str:
    """Create a brief summary of recent conversation for context."""
    if not history:
        return "No prior conversation context."

    # Get last 4-6 messages
    recent = history[-6:] if len(history) > 6 else history

    summary_parts = []
    for msg in recent:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:200]  # Truncate
        if role == "user":
            summary_parts.append(f"User: {content}")
        else:
            summary_parts.append(f"Assistant: {content[:100]}...")

    return "\n".join(summary_parts)


async def _extract_user_problem(client, history: List[Dict]) -> str:
    """Extract the user's core problem/exploration topic from conversation."""
    if not history:
        return "General exploration"

    # Build context from history
    context = "\n".join([
        f"{m.get('role', '?')}: {m.get('content', '')[:150]}"
        for m in history[-4:]
    ])

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Extract the user's core problem or exploration topic from this conversation.
Return a concise 5-15 word description of what they're exploring.

Conversation:
{context}

Core problem/topic:"""
        )
        return response.text.strip()
    except Exception:
        return "General exploration"


def _format_raw_results(results: Any, research_type: ResearchType) -> str:
    """Format raw results into a string for the contextualization prompt."""
    if not results:
        return "No results found."

    if isinstance(results, str):
        return results

    if isinstance(results, dict):
        if results.get("error"):
            return f"Error: {results.get('error')}"
        # Handle different result structures
        if "articles" in results:
            return json.dumps(results["articles"][:10], indent=2)
        if "patents" in results:
            return json.dumps(results["patents"][:10], indent=2)
        if "papers" in results:
            return json.dumps(results["papers"][:10], indent=2)
        return json.dumps(results, indent=2)

    if isinstance(results, list):
        return json.dumps(results[:10], indent=2)

    return str(results)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "contextualize_research",
    "format_contextualized_output",
    "ResearchType",
]
