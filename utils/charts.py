"""
Chart utilities for Mindrian
S-Curve visualization and other charts
"""

import plotly.graph_objects as go
import numpy as np
import chainlit as cl


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
