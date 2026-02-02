"""
Diagram utilities for Mindrian
Generate Mermaid diagrams for mindmaps, flowcharts, and idea visualization

Rendering: Client-side via MermaidDiagram.jsx (loads Mermaid v11 from CDN)
"""

import chainlit as cl
from typing import List, Dict, Optional, Any
import re


async def create_mermaid_element(
    diagram: str,
    title: str = "",
    theme: str = "default"
) -> cl.CustomElement:
    """
    Create a Chainlit CustomElement for rendering a Mermaid diagram.

    Renders client-side using Mermaid v11 loaded from jsDelivr CDN.

    Args:
        diagram: Mermaid syntax string
        title: Optional title above diagram
        theme: 'default', 'dark', 'forest', 'neutral'

    Returns:
        cl.CustomElement for display
    """
    return cl.CustomElement(
        name="MermaidDiagram",
        props={
            "diagram": diagram,
            "title": title,
            "theme": theme
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
# 2x2 QUADRANT CHART
# =============================================================================

async def create_quadrant_chart(
    items: List[Dict[str, Any]],
    title: str = "2x2 Analysis",
    x_label: str = "X Axis",
    y_label: str = "Y Axis",
    quadrant_labels: Dict[str, str] = None,
    quadrant_colors: Dict[str, str] = None
) -> cl.CustomElement:
    """
    Create an interactive 2x2 quadrant/matrix chart.

    Perfect for: Risk/Impact, Effort/Value, Urgency/Importance, Assumption mapping

    Args:
        items: List of dicts with {name, x, y, color?, size?, description?}
               x and y should be 0-100
        title: Chart title
        x_label: X-axis label (e.g., "Certainty", "Effort")
        y_label: Y-axis label (e.g., "Impact", "Value")
        quadrant_labels: Custom labels for each quadrant
        quadrant_colors: Custom colors for each quadrant

    Returns:
        cl.CustomElement (QuadrantChart)

    Example:
        await create_quadrant_chart(
            title="Assumption Risk Matrix",
            x_label="Certainty",
            y_label="Impact",
            items=[
                {"name": "Market size", "x": 30, "y": 90, "color": "#ef4444"},
                {"name": "Tech feasibility", "x": 80, "y": 70, "color": "#22c55e"},
                {"name": "Team capability", "x": 60, "y": 50, "color": "#3b82f6"},
            ]
        )
    """
    default_quadrant_labels = {
        "topLeft": f"High {y_label} / Low {x_label}",
        "topRight": f"High {y_label} / High {x_label}",
        "bottomLeft": f"Low {y_label} / Low {x_label}",
        "bottomRight": f"Low {y_label} / High {x_label}"
    }

    return cl.CustomElement(
        name="QuadrantChart",
        props={
            "title": title,
            "xLabel": x_label,
            "yLabel": y_label,
            "items": items,
            "quadrantLabels": quadrant_labels or default_quadrant_labels,
            "quadrantColors": quadrant_colors
        },
        display="inline"
    )


async def create_risk_matrix(
    assumptions: List[Dict[str, Any]],
    title: str = "Assumption Risk Matrix"
) -> cl.CustomElement:
    """
    Create a risk matrix for assumption testing (PWS pattern).

    Args:
        assumptions: List of {name, certainty (0-100), impact (0-100), description?}

    Example:
        await create_risk_matrix([
            {"name": "Customers will pay", "certainty": 20, "impact": 95},
            {"name": "Tech is feasible", "certainty": 80, "impact": 70},
        ])
    """
    items = [
        {
            "name": a["name"],
            "x": a.get("certainty", 50),
            "y": a.get("impact", 50),
            "color": "#ef4444" if a.get("certainty", 50) < 50 and a.get("impact", 50) > 50 else "#22c55e",
            "description": a.get("description", "")
        }
        for a in assumptions
    ]

    return await create_quadrant_chart(
        items=items,
        title=title,
        x_label="Certainty",
        y_label="Impact",
        quadrant_labels={
            "topLeft": "🔴 Test First",
            "topRight": "✅ Strong Foundation",
            "bottomLeft": "⚪ Low Priority",
            "bottomRight": "🔵 Nice to Validate"
        }
    )


async def create_priority_matrix(
    tasks: List[Dict[str, Any]],
    title: str = "Priority Matrix (Eisenhower)"
) -> cl.CustomElement:
    """
    Create an Eisenhower priority matrix.

    Args:
        tasks: List of {name, urgency (0-100), importance (0-100)}
    """
    items = [
        {
            "name": t["name"],
            "x": t.get("urgency", 50),
            "y": t.get("importance", 50),
            "description": t.get("description", "")
        }
        for t in tasks
    ]

    return await create_quadrant_chart(
        items=items,
        title=title,
        x_label="Urgency",
        y_label="Importance",
        quadrant_labels={
            "topLeft": "📅 Schedule",
            "topRight": "🔥 Do First",
            "bottomLeft": "🗑️ Eliminate",
            "bottomRight": "👥 Delegate"
        }
    )


# =============================================================================
# BUSINESS MODEL CANVAS
# =============================================================================

async def create_business_model_canvas(
    data: Dict[str, List[str]] = None,
    title: str = "Business Model Canvas",
    editable: bool = False,
    variant: str = "bmc"
) -> cl.CustomElement:
    """
    Create an interactive Business Model Canvas.

    Args:
        data: Dict with section arrays:
            - keyPartners: []
            - keyActivities: []
            - keyResources: []
            - valuePropositions: []
            - customerRelationships: []
            - channels: []
            - customerSegments: []
            - costStructure: []
            - revenueStreams: []
        title: Canvas title
        editable: Enable in-canvas editing
        variant: 'bmc' (Business Model Canvas) or 'lean' (Lean Canvas)

    Returns:
        cl.CustomElement (BusinessModelCanvas)

    Example:
        await create_business_model_canvas(
            title="Mindrian Business Model",
            data={
                "valuePropositions": ["AI coaching for innovation", "PWS methodology"],
                "customerSegments": ["Business students", "Entrepreneurs"],
                "channels": ["Web app", "University partnerships"],
                "revenueStreams": ["Subscription", "Enterprise licenses"]
            },
            editable=True
        )
    """
    return cl.CustomElement(
        name="BusinessModelCanvas",
        props={
            "title": title,
            "data": data or {},
            "editable": editable,
            "variant": variant
        },
        display="inline"
    )


async def create_lean_canvas(
    data: Dict[str, List[str]] = None,
    title: str = "Lean Canvas",
    editable: bool = False
) -> cl.CustomElement:
    """
    Create a Lean Canvas (startup-focused variant).

    Args:
        data: Dict with sections:
            - problem: []
            - solution: []
            - keyMetrics: []
            - uniqueValue: []
            - unfairAdvantage: []
            - channels: []
            - customerSegments: []
            - costStructure: []
            - revenueStreams: []

    Example:
        await create_lean_canvas(
            title="Startup Validation",
            data={
                "problem": ["Manual coaching doesn't scale", "Students lack real-world exposure"],
                "solution": ["AI-powered PWS coaching", "Real case study integration"],
                "uniqueValue": ["Learn innovation methodology with AI guidance"]
            }
        )
    """
    return await create_business_model_canvas(
        data=data,
        title=title,
        editable=editable,
        variant="lean"
    )


# =============================================================================
# AI PROMPT GENERATORS
# =============================================================================

def generate_quadrant_prompt(topic: str, x_axis: str, y_axis: str, context: str = "") -> str:
    """
    Generate a prompt for AI to create quadrant chart data.
    """
    return f"""Analyze this topic and place items on a 2x2 matrix.

Topic: {topic}
X-Axis: {x_axis} (0-100 scale)
Y-Axis: {y_axis} (0-100 scale)
Context: {context}

Return a JSON object:
{{
  "items": [
    {{"name": "Item 1", "x": 30, "y": 80, "description": "Why it's positioned here"}},
    {{"name": "Item 2", "x": 70, "y": 40, "description": "Why it's positioned here"}}
  ]
}}

Create 4-8 items with thoughtful positioning.
Return ONLY valid JSON."""


def generate_canvas_prompt(business_idea: str, context: str = "") -> str:
    """
    Generate a prompt for AI to create Business Model Canvas data.
    """
    return f"""Create a Business Model Canvas for this idea.

Business Idea: {business_idea}
Context: {context}

Return a JSON object:
{{
  "valuePropositions": ["value 1", "value 2"],
  "customerSegments": ["segment 1", "segment 2"],
  "channels": ["channel 1"],
  "customerRelationships": ["relationship type"],
  "revenueStreams": ["revenue 1"],
  "keyResources": ["resource 1"],
  "keyActivities": ["activity 1"],
  "keyPartners": ["partner 1"],
  "costStructure": ["cost 1"]
}}

Fill each section with 1-4 concise items.
Return ONLY valid JSON."""


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

    # 2x2 Quadrant Charts
    "create_quadrant_chart",
    "create_risk_matrix",
    "create_priority_matrix",

    # Business Canvases
    "create_business_model_canvas",
    "create_lean_canvas",

    # AI prompt generation
    "generate_mindmap_prompt",
    "generate_flowchart_prompt",
    "generate_quadrant_prompt",
    "generate_canvas_prompt",
]
