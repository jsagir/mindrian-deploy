"""
LangGraph Pipelines for Mindrian
================================
StateGraph implementations for complex multi-step workflows.

Pipelines:
- minto_pyramid: 6-step Minto Pyramid research (deep_research_full)
- domain_discovery: 5-phase CV/research domain discovery (analyze_cv)
- reverse_salient: 10-stage Reverse Salient Discovery (Cross Domain RS)
- grading: 8-phase grading with structured outputs
"""

from .minto_pyramid import (
    MintoPyramidState,
    create_minto_pipeline,
    run_minto_pipeline,
    run_minto_pipeline_with_journey,
    format_minto_result,
)

from .domain_discovery import (
    DomainDiscoveryState,
    create_domain_discovery_pipeline,
    run_domain_discovery,
    format_domain_discovery_result,
)

from .reverse_salient import (
    ReverseSalientState,
    create_reverse_salient_pipeline,
    run_reverse_salient,
    format_reverse_salient_result,
)

from .grading import (
    GradingState,
    create_grading_pipeline,
    run_grading_pipeline,
)

from .oracle_pipeline import (
    OracleState,
    create_oracle_pipeline,
    run_oracle_formulation,
    run_oracle_resolution,
    format_research_brief_output,
    generate_retrospective,
)

from .file_processing import (
    FileState,
    FilePipelineState,
    create_file_processing_pipeline,
    process_files,
    process_single_file,
    process_uploaded_files_langgraph,
)

from .message_router import (
    MessageRouterState,
    create_message_router,
    get_message_router,
    route_message,
    GRADING_BOTS,
    DOCUMENT_EXTENSIONS,
)

from .bono_innovation import (
    BONOState,
    ProblemClassification,
    DomainPersona,
    HatContribution,
    LateralInsight,
    create_bono_pipeline,
    run_bono_session,
    format_bono_report,
    HAT_SEQUENCES,
    HAT_ICONS,
    HAT_FOCUS,
)

from .sequential_thinking import (
    ThinkingStep,
    ThinkingState,
    create_thinking_pipeline,
    run_thinking_pipeline,
    get_thinking_steps_sync,
)

from .genesis import (
    GenesisState,
    create_genesis_graph,
    run_genesis_pipeline,
    format_genesis_report,
    decompose_context,
    identify_domains,
    generate_personas,
    enrich_with_bono_hats,
    orchestrate_research,
    run_expert_panel,
    synthesize_breakthroughs,
    DOMAIN_PATTERNS,
)

__all__ = [
    # Minto Pyramid (deep_research_full)
    "MintoPyramidState",
    "create_minto_pipeline",
    "run_minto_pipeline",
    "format_minto_result",
    # Domain Discovery (analyze_cv)
    "DomainDiscoveryState",
    "create_domain_discovery_pipeline",
    "run_domain_discovery",
    "format_domain_discovery_result",
    # Reverse Salient (Cross Domain RS)
    "ReverseSalientState",
    "create_reverse_salient_pipeline",
    "run_reverse_salient",
    "format_reverse_salient_result",
    # Grading
    "GradingState",
    "create_grading_pipeline",
    "run_grading_pipeline",
    # Oracle Prediction Market
    "OracleState",
    "create_oracle_pipeline",
    "run_oracle_formulation",
    "run_oracle_resolution",
    "format_research_brief_output",
    "generate_retrospective",
    # File Processing Pipeline
    "FileState",
    "FilePipelineState",
    "create_file_processing_pipeline",
    "process_files",
    "process_single_file",
    "process_uploaded_files_langgraph",
    # Message Router Pipeline
    "MessageRouterState",
    "create_message_router",
    "get_message_router",
    "route_message",
    "GRADING_BOTS",
    "DOCUMENT_EXTENSIONS",
    # Sequential Thinking (ThinkingPanel)
    "ThinkingStep",
    "ThinkingState",
    "create_thinking_pipeline",
    "run_thinking_pipeline",
    "get_thinking_steps_sync",
    # Genesis Expert Breakdown + BONO
    "GenesisState",
    "create_genesis_graph",
    "run_genesis_pipeline",
    "format_genesis_report",
    "decompose_context",
    "identify_domains",
    "generate_personas",
    "enrich_with_bono_hats",
    "orchestrate_research",
    "run_expert_panel",
    "synthesize_breakthroughs",
    "DOMAIN_PATTERNS",
]
