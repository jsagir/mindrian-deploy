"""
Conversation Forking - Merge Logic
Wave 2 of Mindrian Session Management

Provides utilities for:
- Extracting insights from branches
- Merging branch insights
- Detecting conflicts between branches
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.forking_types import MergeResult


async def extract_and_merge_insights(
    source_history: List[Dict],
    target_history: List[Dict],
    source_title: str,
    target_title: str,
    merge_mode: str = "insights"
) -> MergeResult:
    """
    Extract key insights from source branch and merge into target.

    Uses LLM to:
    1. Extract key insights from source branch
    2. Identify conflicts with target branch
    3. Generate merged summary

    Args:
        source_history: Messages from source branch
        target_history: Messages from target branch
        source_title: Title of source branch
        target_title: Title of target branch
        merge_mode: "insights" (key points only) or "full" (complete merge)

    Returns:
        MergeResult with success status, insights, conflicts, and summary
    """
    try:
        # Format histories for analysis
        source_text = _format_history_for_llm(source_history, max_messages=20)
        target_text = _format_history_for_llm(target_history, max_messages=20)

        if not source_text.strip():
            return MergeResult(
                success=False,
                source_branch_id="",
                target_branch_id="",
                insights_merged=[],
                conflicts=[],
                merge_summary="",
                error="Source branch has no messages to merge"
            )

        # Use Gemini for insight extraction
        insights, conflicts, summary = await _llm_extract_insights(
            source_text=source_text,
            target_text=target_text,
            source_title=source_title,
            target_title=target_title,
            merge_mode=merge_mode
        )

        return MergeResult(
            success=True,
            source_branch_id="",  # Will be set by caller
            target_branch_id="",  # Will be set by caller
            insights_merged=insights,
            conflicts=conflicts,
            merge_summary=summary,
            error=None
        )

    except Exception as e:
        return MergeResult(
            success=False,
            source_branch_id="",
            target_branch_id="",
            insights_merged=[],
            conflicts=[],
            merge_summary="",
            error=str(e)
        )


def _format_history_for_llm(history: List[Dict], max_messages: int = 20) -> str:
    """Format conversation history for LLM analysis."""
    lines = []
    # Take most recent messages if over limit
    recent = history[-max_messages:] if len(history) > max_messages else history

    for msg in recent:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if content:
            # Truncate very long messages
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"**{role.upper()}**: {content}")

    return "\n\n".join(lines)


async def _llm_extract_insights(
    source_text: str,
    target_text: str,
    source_title: str,
    target_title: str,
    merge_mode: str
) -> tuple:
    """
    Use LLM to extract insights and detect conflicts.

    Returns:
        (insights: List[str], conflicts: List[str], summary: str)
    """
    try:
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Fallback to pattern-based extraction
            return _pattern_based_extraction(source_text)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""Analyze these two conversation branches and extract insights for merging.

## Source Branch: "{source_title}"
{source_text}

## Target Branch: "{target_title}"
{target_text if target_text.strip() else "(empty)"}

## Task
1. Extract the top 5 KEY INSIGHTS from the source branch (discoveries, decisions, conclusions)
2. Identify any CONFLICTS between the two branches (contradicting conclusions)
3. Write a brief MERGE SUMMARY (2-3 sentences) suitable for adding to the target branch

## Response Format (use exactly this format):

INSIGHTS:
- insight 1
- insight 2
- insight 3
- insight 4
- insight 5

CONFLICTS:
- conflict 1 (if any)
- conflict 2 (if any)

SUMMARY:
Your 2-3 sentence summary here."""

        response = model.generate_content(prompt)
        text = response.text

        # Parse response
        insights = []
        conflicts = []
        summary = ""

        current_section = None
        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("INSIGHTS:"):
                current_section = "insights"
            elif line.upper().startswith("CONFLICTS:"):
                current_section = "conflicts"
            elif line.upper().startswith("SUMMARY:"):
                current_section = "summary"
            elif line.startswith("- ") and current_section == "insights":
                insights.append(line[2:])
            elif line.startswith("- ") and current_section == "conflicts":
                if "none" not in line.lower() and "no conflict" not in line.lower():
                    conflicts.append(line[2:])
            elif current_section == "summary" and line:
                summary += line + " "

        summary = summary.strip()
        if not summary:
            summary = f"Merged insights from '{source_title}' exploration."

        return insights[:5], conflicts[:3], summary

    except Exception as e:
        print(f"LLM merge extraction error: {e}")
        # Fallback to pattern-based
        return _pattern_based_extraction(source_text)


def _pattern_based_extraction(text: str) -> tuple:
    """
    Fallback pattern-based insight extraction when LLM unavailable.

    Returns:
        (insights: List[str], conflicts: List[str], summary: str)
    """
    import re

    insights = []
    conflicts = []

    # Extract statements that look like conclusions/insights
    insight_patterns = [
        r"(?:I think|I believe|we concluded|the key is|important to note|discovered that)\s+(.+?)[.!]",
        r"(?:This means|Therefore|So essentially)\s+(.+?)[.!]",
        r"(?:The main|Key insight|Takeaway):\s*(.+?)[.!]",
    ]

    for pattern in insight_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) > 20 and len(match) < 200:
                insights.append(match.strip())
                if len(insights) >= 5:
                    break
        if len(insights) >= 5:
            break

    # If no pattern matches, extract first few assistant responses
    if not insights:
        assistant_msgs = re.findall(r"\*\*ASSISTANT\*\*:\s*(.+?)(?=\*\*|$)", text, re.DOTALL)
        for msg in assistant_msgs[:3]:
            # Take first sentence
            sentences = msg.split(".")
            if sentences and len(sentences[0]) > 20:
                insights.append(sentences[0].strip() + ".")

    summary = f"Explored {len(insights)} key points in this branch."

    return insights[:5], conflicts, summary


def create_merge_message(
    source_title: str,
    insights: List[str],
    conflicts: List[str],
    summary: str
) -> Dict:
    """
    Create a system message documenting the merge.

    This message gets added to the target branch's history.
    """
    content_parts = [
        f"[Merged from '{source_title}' — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]",
        "",
        summary,
        "",
    ]

    if insights:
        content_parts.append("**Key insights merged:**")
        for insight in insights:
            content_parts.append(f"• {insight}")
        content_parts.append("")

    if conflicts:
        content_parts.append("**Notes (potential differences from main thread):**")
        for conflict in conflicts:
            content_parts.append(f"⚠️ {conflict}")

    return {
        "role": "system",
        "content": "\n".join(content_parts),
        "metadata": {
            "type": "merge",
            "source_branch": source_title,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
