"""
Diagram utilities for Mindrian
Generate Mermaid diagrams for mindmaps, flowcharts, and idea visualization

Two rendering options:
1. CustomElement (client-side) - MermaidDiagram.jsx loads mermaid.js from CDN
2. Server-side SVG - Uses mermaid-cli or API to pre-render (more reliable)
"""

import chainlit as cl
from typing import List, Dict, Optional, Any
import re
import subprocess
import tempfile
import os
import base64


# Check if mermaid-cli is available for server-side rendering
MERMAID_CLI_AVAILABLE = False
try:
    result = subprocess.run(["mmdc", "--version"], capture_output=True, timeout=5)
    MERMAID_CLI_AVAILABLE = result.returncode == 0
except (subprocess.SubprocessError, FileNotFoundError):
    pass


async def render_mermaid_to_svg(diagram: str, theme: str = "default") -> Optional[str]:
    """
    Render Mermaid diagram to SVG using mermaid-cli (server-side).

    Args:
        diagram: Mermaid syntax string
        theme: 'default', 'dark', 'forest', 'neutral'

    Returns:
        SVG string or None if mermaid-cli not available
    """
    if not MERMAID_CLI_AVAILABLE:
        return None

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
            f.write(diagram)
            input_file = f.name

        output_file = input_file.replace('.mmd', '.svg')

        result = subprocess.run(
            ["mmdc", "-i", input_file, "-o", output_file, "-t", theme, "-b", "transparent"],
            capture_output=True,
            timeout=30
        )

        if result.returncode == 0 and os.path.exists(output_file):
            with open(output_file, 'r') as f:
                svg_content = f.read()
            os.unlink(output_file)
            os.unlink(input_file)
            return svg_content

        os.unlink(input_file)
        return None

    except Exception as e:
        print(f"Mermaid CLI error: {e}")
        return None


async def create_mermaid_element(
    diagram: str,
    title: str = "",
    theme: str = "default",
    prefer_server_render: bool = True
) -> cl.CustomElement:
    """
    Create a Chainlit element for rendering a Mermaid diagram.

    Uses server-side rendering (mermaid-cli) if available for reliability,
    otherwise falls back to client-side rendering via MermaidDiagram.jsx.

    Args:
        diagram: Mermaid syntax string
        title: Optional title above diagram
        theme: 'default', 'dark', 'forest', 'neutral'
        prefer_server_render: Try server-side SVG first (more reliable)

    Returns:
        cl.CustomElement or cl.Image for display
    """
    # Try server-side rendering first (more reliable)
    if prefer_server_render and MERMAID_CLI_AVAILABLE:
        svg = await render_mermaid_to_svg(diagram, theme)
        if svg:
            # Return as inline HTML element with the SVG
            return cl.CustomElement(
                name="MermaidDiagram",
                props={
                    "diagram": diagram,
                    "svg": svg,  # Pre-rendered SVG
                    "title": title,
                    "theme": theme,
                    "serverRendered": True
                },
                display="inline"
            )

    # Fall back to client-side rendering
    return cl.CustomElement(
        name="MermaidDiagram",
        props={
            "diagram": diagram,
            "title": title,
            "theme": theme,
            "serverRendered": False
        },
        display="inline"
    )


# =============================================================================
# MINDMAP GENERATION
# =============================================================================

async def create_mindmap(
    central_topic: str,
    branches: Dict[str, List[str]],
    title: str = "Idea Map"
) -> cl.CustomElement:
    """
    Create a mindmap diagram from structured data.

    Args:
        central_topic: The central idea/topic
        branches: Dict of {branch_name: [sub_items...]}
        title: Display title

    Returns:
        MermaidDiagram element

    Example:
        await create_mindmap(
            central_topic="AI in Education",
            branches={
                "Benefits": ["Personalized Learning", "24/7 Availability", "Scalability"],
                "Challenges": ["Data Privacy", "Digital Divide", "Teacher Training"],
                "Applications": ["Tutoring", "Assessment", "Content Creation"]
            }
        )
    """
    lines = ["mindmap", f"  root(({central_topic}))"]

    for branch, items in branches.items():
        lines.append(f"    {branch}")
        for item in items:
            # Clean item for Mermaid syntax
            clean_item = _sanitize_text(item)
            lines.append(f"      {clean_item}")

    diagram = "\n".join(lines)
    return await create_mermaid_element(diagram, title)


async def create_mindmap_from_ideas(
    ideas: List[Dict[str, Any]],
    central_topic: str = "Ideas",
    title: str = "Idea Exploration"
) -> cl.CustomElement:
    """
    Create a mindmap from a list of idea dictionaries.

    Args:
        ideas: List of dicts with 'category' and 'items' keys
        central_topic: Center of the mindmap
        title: Display title

    Example:
        ideas = [
            {"category": "Problems", "items": ["High cost", "Low adoption"]},
            {"category": "Solutions", "items": ["Automation", "Training"]}
        ]
    """
    branches = {}
    for idea in ideas:
        category = idea.get("category", "Uncategorized")
        items = idea.get("items", [])
        branches[category] = items

    return await create_mindmap(central_topic, branches, title)


# =============================================================================
# FLOWCHART GENERATION
# =============================================================================

async def create_flowchart(
    steps: List[Dict[str, Any]],
    title: str = "Process Flow",
    direction: str = "TD"
) -> cl.CustomElement:
    """
    Create a flowchart from a list of steps.

    Args:
        steps: List of step dicts with 'id', 'label', 'type', 'next' keys
               type: 'start', 'end', 'process', 'decision', 'input', 'output'
        title: Display title
        direction: 'TD' (top-down), 'LR' (left-right), 'BT', 'RL'

    Returns:
        MermaidDiagram element

    Example:
        steps = [
            {"id": "A", "label": "Start", "type": "start", "next": ["B"]},
            {"id": "B", "label": "Is it valid?", "type": "decision", "next": ["C", "D"]},
            {"id": "C", "label": "Process", "type": "process", "next": ["E"]},
            {"id": "D", "label": "Error", "type": "output", "next": ["E"]},
            {"id": "E", "label": "End", "type": "end", "next": []}
        ]
    """
    shape_map = {
        "start": ("([", "])"),       # Stadium shape
        "end": ("([", "])"),         # Stadium shape
        "process": ("[", "]"),       # Rectangle
        "decision": ("{", "}"),      # Diamond
        "input": ("[/", "/]"),       # Parallelogram
        "output": ("[\\", "\\]"),    # Parallelogram (reverse)
        "database": ("[(", ")]"),    # Cylinder
        "subroutine": ("[[", "]]"),  # Subroutine
    }

    lines = [f"flowchart {direction}"]

    # Define nodes
    for step in steps:
        step_id = step.get("id", "")
        label = _sanitize_text(step.get("label", ""))
        step_type = step.get("type", "process")

        left, right = shape_map.get(step_type, ("[", "]"))
        lines.append(f"    {step_id}{left}{label}{right}")

    # Define connections
    for step in steps:
        step_id = step.get("id", "")
        next_steps = step.get("next", [])
        labels = step.get("edge_labels", [])  # Optional edge labels

        for i, next_id in enumerate(next_steps):
            if labels and i < len(labels):
                lines.append(f"    {step_id} -->|{labels[i]}| {next_id}")
            else:
                lines.append(f"    {step_id} --> {next_id}")

    diagram = "\n".join(lines)
    return await create_mermaid_element(diagram, title)


async def create_process_flowchart(
    process_name: str,
    stages: List[str],
    title: str = None
) -> cl.CustomElement:
    """
    Create a simple linear process flowchart.

    Args:
        process_name: Name of the process
        stages: List of stage names in order
        title: Optional title (defaults to process_name)

    Example:
        await create_process_flowchart(
            "Customer Journey",
            ["Awareness", "Interest", "Decision", "Action", "Retention"]
        )
    """
    steps = []
    for i, stage in enumerate(stages):
        step_type = "start" if i == 0 else ("end" if i == len(stages) - 1 else "process")
        next_steps = [f"S{i+1}"] if i < len(stages) - 1 else []
        steps.append({
            "id": f"S{i}",
            "label": stage,
            "type": step_type,
            "next": next_steps
        })

    return await create_flowchart(steps, title or process_name)


# =============================================================================
# JOURNEY / EXPERIENCE MAP
# =============================================================================

async def create_user_journey(
    title: str,
    sections: Dict[str, List[Dict[str, Any]]],
) -> cl.CustomElement:
    """
    Create a user journey diagram.

    Args:
        title: Journey title
        sections: Dict of {section_name: [{task, score}...]}
                 score: 1-5 (1=frustrated, 5=happy)

    Example:
        await create_user_journey(
            "Student Learning Journey",
            {
                "Discovery": [
                    {"task": "Find course", "score": 3},
                    {"task": "Read reviews", "score": 4}
                ],
                "Enrollment": [
                    {"task": "Sign up", "score": 5},
                    {"task": "Payment", "score": 2}
                ]
            }
        )
    """
    lines = ["journey", f"    title {title}"]

    for section, tasks in sections.items():
        lines.append(f"    section {section}")
        for task in tasks:
            task_name = _sanitize_text(task.get("task", ""))
            score = task.get("score", 3)
            lines.append(f"        {task_name}: {score}")

    diagram = "\n".join(lines)
    return await create_mermaid_element(diagram, title)


# =============================================================================
# SEQUENCE DIAGRAM (Conversation/Process)
# =============================================================================

async def create_sequence_diagram(
    participants: List[str],
    interactions: List[Dict[str, str]],
    title: str = "Interaction Flow"
) -> cl.CustomElement:
    """
    Create a sequence diagram showing interactions between participants.

    Args:
        participants: List of participant names
        interactions: List of {from, to, message, type} dicts
                     type: 'solid', 'dotted', 'async' (default: 'solid')

    Example:
        await create_sequence_diagram(
            participants=["User", "AI Coach", "Knowledge Base"],
            interactions=[
                {"from": "User", "to": "AI Coach", "message": "Ask question"},
                {"from": "AI Coach", "to": "Knowledge Base", "message": "Search", "type": "async"},
                {"from": "Knowledge Base", "to": "AI Coach", "message": "Results", "type": "dotted"},
                {"from": "AI Coach", "to": "User", "message": "Answer"}
            ]
        )
    """
    arrow_map = {
        "solid": "->>",
        "dotted": "-->>",
        "async": "-)",
        "reply": "-->>"
    }

    lines = ["sequenceDiagram"]

    # Define participants
    for p in participants:
        lines.append(f"    participant {_sanitize_id(p)}")

    # Define interactions
    for interaction in interactions:
        from_p = _sanitize_id(interaction.get("from", ""))
        to_p = _sanitize_id(interaction.get("to", ""))
        message = _sanitize_text(interaction.get("message", ""))
        arrow_type = interaction.get("type", "solid")
        arrow = arrow_map.get(arrow_type, "->>")

        lines.append(f"    {from_p}{arrow}{to_p}: {message}")

    diagram = "\n".join(lines)
    return await create_mermaid_element(diagram, title)


# =============================================================================
# PWS-SPECIFIC DIAGRAMS
# =============================================================================

async def create_opportunity_map(
    problem: str,
    stakeholders: List[str],
    constraints: List[str],
    opportunities: List[str],
    title: str = "Opportunity Analysis"
) -> cl.CustomElement:
    """
    Create an opportunity mapping diagram for PWS analysis.

    Args:
        problem: Central problem statement
        stakeholders: List of stakeholders
        constraints: List of constraints
        opportunities: List of opportunities identified
    """
    branches = {
        "Stakeholders": stakeholders,
        "Constraints": constraints,
        "Opportunities": opportunities
    }
    return await create_mindmap(problem, branches, title)


async def create_assumption_map(
    hypothesis: str,
    assumptions: Dict[str, List[str]],
    title: str = "Assumption Analysis"
) -> cl.CustomElement:
    """
    Create an assumption mapping diagram.

    Args:
        hypothesis: Central hypothesis
        assumptions: Dict categorized by type:
            - "Validated": proven assumptions
            - "Testing": being tested
            - "Risky": need validation
            - "Unknown": not yet explored
    """
    return await create_mindmap(hypothesis, assumptions, title)


async def create_framework_flow(
    framework: str,
    title: str = None
) -> cl.CustomElement:
    """
    Create a flowchart for common PWS frameworks.

    Args:
        framework: 'tta', 'jtbd', 'scurve', 'dikw', 'cynefin'
    """
    frameworks = {
        "tta": {
            "title": "Trending to the Absurd",
            "steps": [
                {"id": "T1", "label": "Identify Trend", "type": "start", "next": ["T2"]},
                {"id": "T2", "label": "Extend to Extreme", "type": "process", "next": ["T3"]},
                {"id": "T3", "label": "Find Absurdity", "type": "decision", "next": ["T4", "T2"], "edge_labels": ["Found", "Not yet"]},
                {"id": "T4", "label": "Identify Tension", "type": "process", "next": ["T5"]},
                {"id": "T5", "label": "Extract Opportunity", "type": "end", "next": []}
            ]
        },
        "jtbd": {
            "title": "Jobs to Be Done",
            "steps": [
                {"id": "J1", "label": "Identify Job", "type": "start", "next": ["J2"]},
                {"id": "J2", "label": "When/Where/Why", "type": "process", "next": ["J3"]},
                {"id": "J3", "label": "Current Solutions", "type": "process", "next": ["J4"]},
                {"id": "J4", "label": "Pain Points", "type": "decision", "next": ["J5"]},
                {"id": "J5", "label": "Design Solution", "type": "end", "next": []}
            ]
        },
        "dikw": {
            "title": "DIKW Pyramid Analysis",
            "steps": [
                {"id": "D", "label": "Data: Raw observations", "type": "database", "next": ["I"]},
                {"id": "I", "label": "Information: Organized data", "type": "process", "next": ["K"]},
                {"id": "K", "label": "Knowledge: Patterns", "type": "process", "next": ["U"]},
                {"id": "U", "label": "Understanding: Why", "type": "process", "next": ["W"]},
                {"id": "W", "label": "Wisdom: Action", "type": "end", "next": []}
            ]
        }
    }

    if framework.lower() not in frameworks:
        # Return generic mindmap
        return await create_mindmap(
            f"{framework} Framework",
            {"Components": ["Define steps", "Add details"]},
            title or framework
        )

    fw = frameworks[framework.lower()]
    return await create_flowchart(fw["steps"], title or fw["title"])


# =============================================================================
# AI-POWERED DIAGRAM GENERATION
# =============================================================================

def generate_mindmap_prompt(topic: str, context: str = "") -> str:
    """
    Generate a prompt for AI to create mindmap structure.

    Returns a prompt that will produce structured JSON for create_mindmap_from_ideas()
    """
    return f"""Analyze this topic and create a mindmap structure.

Topic: {topic}
Context: {context}

Return a JSON object with this structure:
{{
  "central_topic": "Main topic name",
  "branches": {{
    "Category 1": ["item 1", "item 2", "item 3"],
    "Category 2": ["item 1", "item 2"],
    "Category 3": ["item 1", "item 2", "item 3", "item 4"]
  }}
}}

Create 3-5 main branches with 2-5 items each.
Keep items concise (2-4 words).
Return ONLY valid JSON, no explanation."""


def generate_flowchart_prompt(process: str, context: str = "") -> str:
    """
    Generate a prompt for AI to create flowchart structure.
    """
    return f"""Create a flowchart for this process.

Process: {process}
Context: {context}

Return a JSON object with this structure:
{{
  "title": "Process name",
  "steps": [
    {{"id": "A", "label": "Start step", "type": "start", "next": ["B"]}},
    {{"id": "B", "label": "Decision?", "type": "decision", "next": ["C", "D"], "edge_labels": ["Yes", "No"]}},
    {{"id": "C", "label": "Process step", "type": "process", "next": ["E"]}},
    {{"id": "D", "label": "Alternative", "type": "process", "next": ["E"]}},
    {{"id": "E", "label": "End", "type": "end", "next": []}}
  ]
}}

Types: start, end, process, decision, input, output
Return ONLY valid JSON, no explanation."""


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _sanitize_text(text: str) -> str:
    """Sanitize text for Mermaid syntax."""
    if not text:
        return ""
    # Remove or escape problematic characters
    text = text.replace('"', "'")
    text = text.replace("(", "[")
    text = text.replace(")", "]")
    text = text.replace("{", "[")
    text = text.replace("}", "]")
    text = text.replace("<", "")
    text = text.replace(">", "")
    text = text.replace("\n", " ")
    return text.strip()


def _sanitize_id(text: str) -> str:
    """Create a valid Mermaid ID from text."""
    if not text:
        return "Node"
    # Remove spaces and special characters
    text = re.sub(r'[^a-zA-Z0-9]', '', text)
    return text or "Node"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core element creation
    "create_mermaid_element",

    # Mindmaps
    "create_mindmap",
    "create_mindmap_from_ideas",

    # Flowcharts
    "create_flowchart",
    "create_process_flowchart",

    # Journey/Experience
    "create_user_journey",
    "create_sequence_diagram",

    # PWS-specific
    "create_opportunity_map",
    "create_assumption_map",
    "create_framework_flow",

    # AI prompt generation
    "generate_mindmap_prompt",
    "generate_flowchart_prompt",
]
