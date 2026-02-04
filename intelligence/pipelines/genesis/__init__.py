"""
Genesis Expert Breakdown Engine
================================
Multi-domain expert analysis with BONO (Six Thinking Hats) integration.

Stages:
1. Context Decomposition
2. Domain Identification (24 domains)
3. Persona Generation (with Six Hats enrichment)
4. Research Orchestration
5. Expert Panel (multi-agent discussion)
6. Breakthrough Synthesis

Usage:
    from intelligence.pipelines.genesis import run_genesis_pipeline

    result = await run_genesis_pipeline(
        challenge="How can AI transform urban farming?",
        session_id="user_123"
    )
"""

from .decompose import decompose_context
from .domains import identify_domains, DOMAIN_PATTERNS
from .personas import generate_personas, enrich_with_bono_hats
from .orchestrate import orchestrate_research
from .panel import run_expert_panel
from .synthesize import synthesize_breakthroughs, score_breakthrough
from .pipeline import (
    run_genesis_pipeline,
    GenesisState,
    create_genesis_graph,
    format_genesis_report,
)

__all__ = [
    # Stage functions
    "decompose_context",
    "identify_domains",
    "generate_personas",
    "enrich_with_bono_hats",
    "orchestrate_research",
    "run_expert_panel",
    "synthesize_breakthroughs",
    "score_breakthrough",
    # Pipeline
    "run_genesis_pipeline",
    "GenesisState",
    "create_genesis_graph",
    "format_genesis_report",
    # Constants
    "DOMAIN_PATTERNS",
]
