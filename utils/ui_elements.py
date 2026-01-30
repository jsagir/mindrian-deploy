"""
UI Elements Helper Module

Provides easy-to-use functions for creating Chainlit UI elements:
- Native elements: TaskList, File, Text, PDF, Video, Audio
- Custom elements: GradeReveal, ScoreBreakdown, OpportunityCard

Usage:
    from utils.ui_elements import (
        create_assessment_tasklist,
        create_grade_reveal,
        create_score_breakdown,
        create_opportunity_card,
        create_report_download,
        create_evidence_display,
    )
"""

import chainlit as cl
from typing import List, Dict, Any, Optional
import json
from datetime import datetime


# =============================================================================
# NATIVE ELEMENTS
# =============================================================================

async def create_assessment_tasklist() -> cl.TaskList:
    """
    Create a TaskList for assessment progress tracking.

    Returns a TaskList with 5 modules:
    - Neo4j (Graph Analysis)
    - FileSearch (Pattern Discovery)
    - Tavily (External Validation)
    - Gemini (Synthesis)
    - Report Generation
    """
    task_list = cl.TaskList()
    task_list.tasks = [
        cl.Task(title="Querying Knowledge Graph (Neo4j)", status=cl.TaskStatus.READY),
        cl.Task(title="Discovering Patterns (FileSearch)", status=cl.TaskStatus.READY),
        cl.Task(title="Validating with Research (Tavily)", status=cl.TaskStatus.READY),
        cl.Task(title="Synthesizing Findings (Gemini)", status=cl.TaskStatus.READY),
        cl.Task(title="Generating Report", status=cl.TaskStatus.READY),
    ]
    return task_list


async def update_task_status(
    task_list: cl.TaskList,
    task_index: int,
    status: cl.TaskStatus,
    title_suffix: str = ""
) -> None:
    """
    Update a task's status and optionally append to its title.

    Args:
        task_list: The TaskList to update
        task_index: Index of the task (0-4 for assessment)
        status: New status (READY, RUNNING, DONE, FAILED)
        title_suffix: Optional suffix to append (e.g., ": 5 frameworks found")
    """
    if 0 <= task_index < len(task_list.tasks):
        task_list.tasks[task_index].status = status
        if title_suffix:
            base_titles = [
                "Neo4j",
                "FileSearch",
                "Tavily",
                "Synthesis",
                "Report"
            ]
            if task_index < len(base_titles):
                task_list.tasks[task_index].title = f"{base_titles[task_index]}{title_suffix}"
        try:
            await task_list.send()
        except TypeError as e:
            # Chainlit version compatibility: some versions pass for_id internally
            if "for_id" in str(e):
                # Skip the send - the task list will still show updated state
                pass
            else:
                raise


async def create_workshop_tasklist(phases: List[Dict[str, str]]) -> cl.TaskList:
    """
    Create a TaskList for workshop phase tracking.

    Args:
        phases: List of phase dicts with 'name' and 'status' keys

    Returns:
        TaskList with phases as tasks
    """
    task_list = cl.TaskList()
    status_map = {
        "ready": cl.TaskStatus.READY,
        "running": cl.TaskStatus.RUNNING,
        "complete": cl.TaskStatus.DONE,
        "done": cl.TaskStatus.DONE,
        "failed": cl.TaskStatus.FAILED,
        "pending": cl.TaskStatus.READY,
    }

    task_list.tasks = [
        cl.Task(
            title=phase.get("name", f"Phase {i+1}"),
            status=status_map.get(phase.get("status", "ready"), cl.TaskStatus.READY)
        )
        for i, phase in enumerate(phases)
    ]
    return task_list


def create_report_download(
    content: str,
    filename: str = "assessment_report.md",
    display: str = "inline"
) -> cl.File:
    """
    Create a downloadable file element for reports.

    Args:
        content: The file content (markdown, JSON, etc.)
        filename: Name for the downloaded file
        display: "inline" or "side"

    Returns:
        cl.File element
    """
    return cl.File(
        name=filename,
        content=content.encode('utf-8'),
        display=display
    )


def create_evidence_display(
    evidence: List[Dict[str, Any]],
    name: str = "evidence_chain",
    display: str = "side"
) -> cl.Text:
    """
    Create a syntax-highlighted JSON display of evidence.

    Args:
        evidence: List of evidence items
        name: Element name
        display: "inline" or "side"

    Returns:
        cl.Text element with JSON highlighting
    """
    # Format evidence for display
    formatted = []
    for ev in evidence:
        formatted.append({
            "source": ev.get("source_type", ev.get("source", "unknown")),
            "tag": ev.get("tag_type", ev.get("tag", "")),
            "confidence": f"{ev.get('confidence', 0) * 100:.0f}%",
            "content": ev.get("content", str(ev))[:200]  # Truncate long content
        })

    return cl.Text(
        name=name,
        content=json.dumps(formatted, indent=2),
        language="json",
        display=display
    )


def create_pdf_viewer(
    path: str,
    name: str = "document",
    display: str = "side",
    start_page: int = 1
) -> cl.Pdf:
    """
    Create an embedded PDF viewer.

    Args:
        path: Path to the PDF file
        name: Element name
        display: "inline" or "side"
        start_page: Page to start viewing at

    Returns:
        cl.Pdf element
    """
    return cl.Pdf(
        name=name,
        path=path,
        display=display,
        start_page=start_page
    )


def create_video_element(url: str, name: str = "video") -> cl.Video:
    """
    Create an embedded video element.

    Args:
        url: Video URL (YouTube, Vimeo, or direct)
        name: Element name

    Returns:
        cl.Video element
    """
    return cl.Video(
        name=name,
        url=url,
        display="inline"
    )


def create_audio_element(url: str, name: str = "audio") -> cl.Audio:
    """
    Create an embedded audio element.

    Args:
        url: Audio URL
        name: Element name

    Returns:
        cl.Audio element
    """
    return cl.Audio(
        name=name,
        url=url,
        display="inline"
    )


# =============================================================================
# CUSTOM ELEMENTS
# =============================================================================

def create_grade_reveal(
    grade: str,
    score: float,
    verdict: str,
    strengths: List[str],
    growth_areas: List[str],
    evidence_count: int = 0,
    components: List[Dict[str, Any]] = None,
    stage: str = "context",
    bot_type: str = "minto"
) -> cl.CustomElement:
    """
    Create a soft-landing grade reveal element.

    Args:
        grade: Letter grade (e.g., "B+")
        score: Numeric score (0-100)
        verdict: Summary verdict
        strengths: List of things done well
        growth_areas: List of improvement areas
        evidence_count: Number of evidence items analyzed
        components: Optional list of score components for expanded view
        stage: Starting stage ('context', 'strengths', 'growth', 'reveal', 'expanded')
        bot_type: Which grading bot ('minto' or 'grading')

    Returns:
        cl.CustomElement for GradeReveal.jsx
    """
    return cl.CustomElement(
        name="GradeReveal",
        props={
            "stage": stage,
            "grade": grade,
            "score": score,
            "verdict": verdict,
            "strengths": strengths,
            "growth_areas": growth_areas,
            "evidence_count": evidence_count,
            "components": components or [],
            "bot_type": bot_type
        }
    )


def create_score_breakdown(
    components: List[Dict[str, Any]],
    total_score: float,
    grade: str,
    selected: int = None
) -> cl.CustomElement:
    """
    Create an interactive score breakdown element.

    Args:
        components: List of component dicts with:
            - name: Component name
            - weight: Percentage weight
            - score: Score out of 10
            - assessment: Text assessment
            - evidence: List of evidence items
            - missing: List of what would improve score
        total_score: Total score (0-100)
        grade: Letter grade
        selected: Initially selected component index (None for none)

    Returns:
        cl.CustomElement for ScoreBreakdown.jsx
    """
    return cl.CustomElement(
        name="ScoreBreakdown",
        props={
            "components": components,
            "total_score": total_score,
            "grade": grade,
            "selected": selected
        }
    )


def create_opportunity_card(
    opportunity_id: str,
    title: str,
    problem: str,
    evidence_quality: int = 3,
    domain: str = "General",
    priority: str = "medium",
    source: str = "",
    frameworks: List[str] = None,
    created_at: str = None
) -> cl.CustomElement:
    """
    Create an opportunity bank card element.

    Args:
        opportunity_id: Unique identifier
        title: Opportunity title
        problem: Problem description
        evidence_quality: 1-5 star rating
        domain: Domain/industry
        priority: 'high', 'medium', or 'low'
        source: Where it was discovered
        frameworks: Relevant frameworks
        created_at: Timestamp

    Returns:
        cl.CustomElement for OpportunityCard.jsx
    """
    return cl.CustomElement(
        name="OpportunityCard",
        props={
            "id": opportunity_id,
            "title": title,
            "problem": problem,
            "evidence_quality": evidence_quality,
            "domain": domain,
            "priority": priority,
            "source": source,
            "frameworks": frameworks or [],
            "created_at": created_at or datetime.utcnow().isoformat()
        }
    )


# =============================================================================
# COMPOSITE HELPERS
# =============================================================================

async def display_grading_results(
    grade: str,
    score: float,
    verdict: str,
    components: List[Dict[str, Any]],
    strengths: List[str],
    growth_areas: List[str],
    evidence: List[Dict[str, Any]],
    report_content: str,
    bot_type: str = "minto"
) -> None:
    """
    Display complete grading results with all UI elements.

    This sends:
    1. GradeReveal (soft landing)
    2. File download for report
    3. Evidence display in sidebar

    Args:
        grade: Letter grade
        score: Numeric score
        verdict: Summary verdict
        components: Score breakdown components
        strengths: What was done well
        growth_areas: Improvement areas
        evidence: Evidence chain
        report_content: Full report markdown
        bot_type: Grading bot type
    """
    # Create all elements
    grade_reveal = create_grade_reveal(
        grade=grade,
        score=score,
        verdict=verdict,
        strengths=strengths,
        growth_areas=growth_areas,
        evidence_count=len(evidence),
        components=components,
        stage="context",
        bot_type=bot_type
    )

    report_file = create_report_download(
        content=report_content,
        filename=f"assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.md"
    )

    evidence_text = create_evidence_display(evidence)

    # Send message with elements
    await cl.Message(
        content="## Assessment Complete",
        elements=[grade_reveal, report_file, evidence_text]
    ).send()


async def display_opportunities(opportunities: List[Dict[str, Any]]) -> None:
    """
    Display a list of opportunities as cards.

    Args:
        opportunities: List of opportunity dicts
    """
    elements = []
    for opp in opportunities:
        card = create_opportunity_card(
            opportunity_id=opp.get("id", ""),
            title=opp.get("title", "Untitled"),
            problem=opp.get("problem", ""),
            evidence_quality=opp.get("evidence_quality", 3),
            domain=opp.get("domain", "General"),
            priority=opp.get("priority", "medium"),
            source=opp.get("source", ""),
            frameworks=opp.get("frameworks", []),
            created_at=opp.get("created_at")
        )
        elements.append(card)

    await cl.Message(
        content=f"## Bank of Opportunities ({len(opportunities)} saved)",
        elements=elements
    ).send()
