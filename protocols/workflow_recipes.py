"""
Workflow Recipes - Wave 4: Auto-Orchestration
Defines multi-agent workflow recipes for different intent types.

Each recipe specifies:
- Stages with agent groups
- Parallel vs sequential execution
- Validation checkpoints
- Synthesis mode
"""

from typing import TypedDict, List, Optional, Literal


class StageConfig(TypedDict):
    """Configuration for a workflow stage."""
    agents: List[str]          # Agent IDs to run
    task: str                  # Task description for logging
    parallel: bool             # Run agents in parallel?
    timeout_seconds: int       # Max time for stage
    skip_if: Optional[str]     # Condition to skip (e.g., "no_entities")
    validation: bool           # Apply Red Team validation after?


class WorkflowRecipe(TypedDict):
    """Complete workflow recipe."""
    id: str
    name: str
    description: str
    stages: List[StageConfig]
    synthesis_mode: Literal["sequential", "parallel", "consensus"]
    estimated_seconds: int
    min_confidence: float      # Minimum classification confidence to auto-run


# ═══════════════════════════════════════════════════════════════════════════════
# PREDEFINED WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════

WORKFLOWS: dict[str, WorkflowRecipe] = {

    "tech_to_opportunity": {
        "id": "tech_to_opportunity",
        "name": "Technology to Opportunity",
        "description": "Find business opportunities for a technology",
        "stages": [
            {
                "agents": ["tta", "research"],
                "task": "expand_domains",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["jtbd"],
                "task": "find_customer_jobs",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": True,
            },
            {
                "agents": ["ackoff", "validation"],
                "task": "assess_market_wisdom",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": True,
            },
            {
                "agents": ["larry"],
                "task": "synthesize_opportunity",
                "parallel": False,
                "timeout_seconds": 30,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "sequential",
        "estimated_seconds": 180,
        "min_confidence": 0.75,
    },

    "explore": {
        "id": "explore",
        "name": "Open Exploration",
        "description": "Explore a topic from multiple angles",
        "stages": [
            {
                "agents": ["tta", "research"],
                "task": "gather_perspectives",
                "parallel": True,
                "timeout_seconds": 90,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["knowns"],
                "task": "map_uncertainties",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["larry"],
                "task": "synthesize_exploration",
                "parallel": False,
                "timeout_seconds": 30,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "parallel",
        "estimated_seconds": 150,
        "min_confidence": 0.6,
    },

    "stress_test": {
        "id": "stress_test",
        "name": "Stress Test",
        "description": "Challenge assumptions and find weaknesses",
        "stages": [
            {
                "agents": ["redteam"],
                "task": "identify_assumptions",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["ackoff", "research"],
                "task": "validate_claims",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["redteam"],
                "task": "final_challenge",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "consensus",
        "estimated_seconds": 120,
        "min_confidence": 0.8,
    },

    "document_review": {
        "id": "document_review",
        "name": "Document Review",
        "description": "Analyze and grade a document",
        "stages": [
            {
                "agents": ["pws_grading"],
                "task": "grade_document",
                "parallel": False,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["redteam", "ackoff"],
                "task": "challenge_claims",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["larry"],
                "task": "synthesize_feedback",
                "parallel": False,
                "timeout_seconds": 30,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "sequential",
        "estimated_seconds": 120,
        "min_confidence": 0.85,
    },

    "validate": {
        "id": "validate",
        "name": "Validate Hypothesis",
        "description": "Test a specific claim or hypothesis",
        "stages": [
            {
                "agents": ["research"],
                "task": "gather_evidence",
                "parallel": False,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["ackoff"],
                "task": "apply_dikw",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["validation"],
                "task": "final_assessment",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": True,
            },
        ],
        "synthesis_mode": "consensus",
        "estimated_seconds": 130,
        "min_confidence": 0.75,
    },

    "full_analysis": {
        "id": "full_analysis",
        "name": "Full Analysis",
        "description": "Comprehensive multi-agent analysis",
        "stages": [
            {
                "agents": ["tta", "research"],
                "task": "initial_exploration",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["jtbd", "scurve"],
                "task": "market_and_timing",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": True,
            },
            {
                "agents": ["redteam", "ackoff"],
                "task": "challenge_and_validate",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["larry"],
                "task": "final_synthesis",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "sequential",
        "estimated_seconds": 240,
        "min_confidence": 0.5,
    },

    "quick_pulse": {
        "id": "quick_pulse",
        "name": "Quick Pulse",
        "description": "Fast multi-perspective check",
        "stages": [
            {
                "agents": ["tta", "redteam"],
                "task": "quick_perspectives",
                "parallel": True,
                "timeout_seconds": 30,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["larry"],
                "task": "quick_synthesis",
                "parallel": False,
                "timeout_seconds": 20,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "parallel",
        "estimated_seconds": 50,
        "min_confidence": 0.5,
    },
}


def get_workflow(workflow_id: str) -> Optional[WorkflowRecipe]:
    """Get a workflow by ID."""
    return WORKFLOWS.get(workflow_id)


def list_workflows() -> List[dict]:
    """List all available workflows with summary info."""
    return [
        {
            "id": w["id"],
            "name": w["name"],
            "description": w["description"],
            "estimated_seconds": w["estimated_seconds"],
            "stage_count": len(w["stages"]),
        }
        for w in WORKFLOWS.values()
    ]


def create_custom_workflow(
    agents: List[str],
    parallel_groups: Optional[List[List[str]]] = None,
    validation_points: Optional[List[int]] = None,
) -> WorkflowRecipe:
    """
    Create a custom workflow from agent selection.

    Args:
        agents: List of agent IDs in order
        parallel_groups: Groups of agents to run in parallel
        validation_points: Stage indices where Red Team validates

    Returns:
        Custom WorkflowRecipe
    """
    stages = []
    validation_points = validation_points or []

    if parallel_groups:
        for i, group in enumerate(parallel_groups):
            stages.append({
                "agents": group,
                "task": f"parallel_{'-'.join(group)}",
                "parallel": len(group) > 1,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": i in validation_points,
            })
    else:
        # Sequential by default
        for i, agent in enumerate(agents):
            stages.append({
                "agents": [agent],
                "task": f"run_{agent}",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": i in validation_points,
            })

    # Always add synthesis stage
    stages.append({
        "agents": ["larry"],
        "task": "synthesize_results",
        "parallel": False,
        "timeout_seconds": 30,
        "skip_if": None,
        "validation": False,
    })

    return {
        "id": "custom",
        "name": "Custom Workflow",
        "description": f"Custom: {', '.join(agents)}",
        "stages": stages,
        "synthesis_mode": "sequential",
        "estimated_seconds": len(stages) * 45,
        "min_confidence": 0.0,
    }
