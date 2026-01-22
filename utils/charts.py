"""
Chart utilities for Mindrian
S-Curve visualization, DIKW pyramid, DataFrames, and other charts
"""

import plotly.graph_objects as go
import numpy as np
import chainlit as cl

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


async def create_dataframe_element(
    data: dict,
    name: str = "data",
    display: str = "inline"
) -> cl.Dataframe:
    """
    Create a Chainlit DataFrame element for tabular display.

    Args:
        data: Dictionary with column names as keys and lists as values
        name: Element name
        display: "inline", "side", or "page"

    Returns:
        cl.Dataframe element
    """
    if not PANDAS_AVAILABLE:
        return None

    df = pd.DataFrame(data)
    return cl.Dataframe(data=df, name=name, display=display)


async def create_comparison_dataframe(
    items: list,
    criteria: list,
    scores: list,
    name: str = "comparison"
) -> cl.Dataframe:
    """
    Create a comparison table for workshop analysis.

    Args:
        items: List of items being compared
        criteria: List of criteria/dimensions
        scores: 2D list of scores [item][criteria]
        name: Element name

    Returns:
        cl.Dataframe element
    """
    if not PANDAS_AVAILABLE:
        return None

    data = {"Item": items}
    for i, criterion in enumerate(criteria):
        data[criterion] = [row[i] if i < len(row) else "" for row in scores]

    df = pd.DataFrame(data)
    return cl.Dataframe(data=df, name=name, display="inline")


async def create_research_results_dataframe(
    results: list,
    name: str = "research_results"
) -> cl.Dataframe:
    """
    Create a DataFrame from Tavily research results.

    Args:
        results: List of search result dicts with title, url, content
        name: Element name

    Returns:
        cl.Dataframe element
    """
    if not PANDAS_AVAILABLE or not results:
        return None

    data = {
        "Source": [r.get("title", "Unknown")[:50] for r in results],
        "Summary": [r.get("content", "")[:100] + "..." for r in results],
        "URL": [r.get("url", "") for r in results]
    }

    df = pd.DataFrame(data)
    return cl.Dataframe(data=df, name=name, display="inline")


async def create_dikw_pyramid(
    highlight_level: str = None,
    title: str = "Ackoff's DIKW Pyramid"
) -> cl.Plotly:
    """
    Create a DIKW pyramid diagram showing the hierarchy:
    Data → Information → Knowledge → Understanding → Wisdom

    Args:
        highlight_level: Which level to highlight ('data', 'information', 'knowledge', 'understanding', 'wisdom')
        title: Chart title

    Returns:
        cl.Plotly element to display
    """
    # Define pyramid levels (from bottom to top)
    levels = [
        {"name": "Data", "desc": "Raw facts, observations", "color": "#90CAF9", "y": 0},
        {"name": "Information", "desc": "Organized, contextualized data", "color": "#64B5F6", "y": 1},
        {"name": "Knowledge", "desc": "Patterns, cause & effect", "color": "#42A5F5", "y": 2},
        {"name": "Understanding", "desc": "Why things happen", "color": "#2196F3", "y": 3},
        {"name": "Wisdom", "desc": "Judgment, action decisions", "color": "#1976D2", "y": 4},
    ]

    fig = go.Figure()

    # Create pyramid using filled areas
    for i, level in enumerate(levels):
        # Calculate width (wider at bottom, narrower at top)
        width = 5 - i * 0.8
        y_base = i
        y_top = i + 0.9

        # Determine color (highlight if selected)
        color = level["color"]
        if highlight_level and level["name"].lower() == highlight_level.lower():
            color = "#FF9800"  # Orange highlight

        # Draw trapezoid for each level
        x_coords = [-width/2, width/2, (width-0.8)/2, -(width-0.8)/2, -width/2]
        y_coords = [y_base, y_base, y_top, y_top, y_base]

        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            fill="toself",
            fillcolor=color,
            line=dict(color="white", width=2),
            mode="lines",
            name=level["name"],
            hoverinfo="text",
            hovertext=f"<b>{level['name']}</b><br>{level['desc']}",
            showlegend=False,
        ))

        # Add level label
        fig.add_annotation(
            x=0,
            y=y_base + 0.45,
            text=f"<b>{level['name']}</b>",
            showarrow=False,
            font=dict(color="white", size=14),
        )

    # Add descriptions on the side
    descriptions = [
        "Can a camera record it?",
        "What does it mean?",
        "What patterns emerge?",
        "Why does it happen?",
        "What should we do?",
    ]

    for i, desc in enumerate(descriptions):
        fig.add_annotation(
            x=3.5,
            y=i + 0.45,
            text=desc,
            showarrow=True,
            arrowhead=2,
            arrowsize=0.5,
            arrowwidth=1,
            arrowcolor="#666",
            ax=-30,
            ay=0,
            font=dict(size=11, color="#666"),
        )

    # Add arrows showing direction
    fig.add_annotation(
        x=-4,
        y=2,
        text="Climb UP<br>to understand",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#4CAF50",
        ax=0,
        ay=60,
        font=dict(size=10, color="#4CAF50"),
    )

    fig.add_annotation(
        x=-4,
        y=3,
        text="Climb DOWN<br>to validate",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#F44336",
        ax=0,
        ay=-60,
        font=dict(size=10, color="#F44336"),
    )

    fig.update_layout(
        title=title,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-6, 6],
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, 5.5],
        ),
        template="plotly_white",
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return cl.Plotly(name="dikw_pyramid", figure=fig, display="inline")


async def create_scurve_chart(
    title: str = "Technology S-Curve",
    current_position: float = 0.3,  # 0-1 representing position on curve
    labels: list = None
) -> cl.Plotly:
    """
    Create an S-curve chart showing technology adoption lifecycle.

    Args:
        title: Chart title
        current_position: Where the technology currently sits (0-1)
        labels: Optional custom labels for phases

    Returns:
        cl.Plotly element to display
    """
    # Generate S-curve data
    x = np.linspace(0, 10, 100)
    y = 1 / (1 + np.exp(-(x - 5)))  # Sigmoid/S-curve

    # Default phase labels
    if labels is None:
        labels = {
            0.1: "Era of Ferment",
            0.3: "Dominant Design",
            0.7: "Era of Incremental Change",
            0.9: "Maturity/Discontinuity"
        }

    # Create figure
    fig = go.Figure()

    # Add S-curve
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        name='Adoption Curve',
        line=dict(color='#2196F3', width=3)
    ))

    # Add current position marker
    current_x = current_position * 10
    current_y = 1 / (1 + np.exp(-(current_x - 5)))

    fig.add_trace(go.Scatter(
        x=[current_x],
        y=[current_y],
        mode='markers',
        name='Current Position',
        marker=dict(color='#FF5722', size=15, symbol='star')
    ))

    # Add phase annotations
    fig.add_vrect(x0=0, x1=2.5, fillcolor="rgba(255,193,7,0.1)", line_width=0)
    fig.add_vrect(x0=2.5, x1=5, fillcolor="rgba(76,175,80,0.1)", line_width=0)
    fig.add_vrect(x0=5, x1=7.5, fillcolor="rgba(33,150,243,0.1)", line_width=0)
    fig.add_vrect(x0=7.5, x1=10, fillcolor="rgba(156,39,176,0.1)", line_width=0)

    # Phase labels
    fig.add_annotation(x=1.25, y=0.05, text="Era of<br>Ferment", showarrow=False)
    fig.add_annotation(x=3.75, y=0.3, text="Dominant<br>Design", showarrow=False)
    fig.add_annotation(x=6.25, y=0.7, text="Incremental<br>Change", showarrow=False)
    fig.add_annotation(x=8.75, y=0.95, text="Maturity/<br>Discontinuity", showarrow=False)

    # Layout
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Market Adoption / Performance",
        showlegend=True,
        template="plotly_white",
        height=400
    )

    return cl.Plotly(name="scurve", figure=fig, display="inline")


async def create_comparison_chart(
    data: dict,
    title: str = "Comparison Analysis"
) -> cl.Plotly:
    """
    Create a comparison bar chart.

    Args:
        data: Dictionary of {label: value}
        title: Chart title

    Returns:
        cl.Plotly element
    """
    fig = go.Figure(data=[
        go.Bar(
            x=list(data.keys()),
            y=list(data.values()),
            marker_color='#2196F3'
        )
    ])

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=350
    )

    return cl.Plotly(name="comparison", figure=fig, display="inline")


async def create_radar_chart(
    categories: list,
    values: list,
    title: str = "Multi-Dimensional Analysis"
) -> cl.Plotly:
    """
    Create a radar/spider chart for multi-dimensional analysis.

    Args:
        categories: List of category names
        values: List of values (0-100 scale recommended)
        title: Chart title

    Returns:
        cl.Plotly element
    """
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # Close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(33,150,243,0.3)',
        line=dict(color='#2196F3', width=2),
        name='Analysis'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title=title,
        showlegend=False,
        height=400
    )

    return cl.Plotly(name="radar", figure=fig, display="inline")
