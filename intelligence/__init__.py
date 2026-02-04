"""
Mindrian Intelligence Layer
============================
LangChain tools and LangGraph pipelines for orchestrating:
- Neo4j GraphRAG
- LangExtract structured extraction
- Gemini reasoning
- Tavily research
- Sequential thinking
- Multi-agent orchestration
- Workshop state management

Architecture:
- tools.py: @tool wrapped functions for agent composition
- schemas.py: Pydantic models for structured LLM outputs
- pipelines/: LangGraph StateGraph implementations
- agents/: Research and multi-agent orchestrators
- workshop_manager.py: LangGraph workshop mode controller

Usage:
    # Tools (LangChain @tool decorated)
    from intelligence import search_web_tavily, query_neo4j_concepts

    # Pipelines (LangGraph StateGraph)
    from intelligence.pipelines import run_minto_pipeline, run_grading_pipeline

    # Agents
    from intelligence.agents import run_research_agent, run_multi_agent_analysis

    # Workshop Manager
    from intelligence import WorkshopManager
    manager = WorkshopManager("tta", session_id="user_123")
"""

# =============================================================================
# TOOLS (LangChain @tool decorated)
# =============================================================================
from .research_tools import (
    # Research tools
    search_web_tavily,
    search_arxiv,
    search_patents,
    search_trends,
    search_govdata,
    search_datasets,
    search_news,
    validate_assumption,
    research_trend,

    # Knowledge tools
    query_neo4j_concepts,
    query_neo4j_frameworks,
    query_neo4j_problems,

    # Extraction tools
    extract_instant,
    extract_deep,

    # All tools list for agent composition
    ALL_RESEARCH_TOOLS,
    ALL_KNOWLEDGE_TOOLS,
    ALL_EXTRACTION_TOOLS,
    ALL_TOOLS,
)

# =============================================================================
# SCHEMAS (Pydantic models for structured outputs)
# =============================================================================
from .schemas import (
    # Minto/SCQA
    SCQAAnalysis,
    BeautifulQuestion,
    ThinkingStep,
    MintoPyramidOutput,
    # Grading
    ComponentScore,
    GradeBreakdown,
    GradeReport,
    BiasDetectionResult,
    # Domain Discovery
    ParsedCV,
    DomainCandidate,
    IKAScore,
    DomainRecommendation,
    DomainDiscoveryOutput,
    # Reverse Salient
    ReverseSalient,
    ReverseSalientOutput,
    # Research
    ResearchSynthesis,
    # Extraction
    PWSSSignals,
)

# =============================================================================
# PIPELINES (LangGraph StateGraph)
# =============================================================================
from .pipelines import (
    # Minto Pyramid (deep_research_full)
    MintoPyramidState,
    create_minto_pipeline,
    run_minto_pipeline,
    format_minto_result,
    # Domain Discovery (analyze_cv)
    DomainDiscoveryState,
    create_domain_discovery_pipeline,
    run_domain_discovery,
    format_domain_discovery_result,
    # Reverse Salient (Cross Domain RS)
    ReverseSalientState,
    create_reverse_salient_pipeline,
    run_reverse_salient,
    format_reverse_salient_result,
    # Grading
    GradingState,
    create_grading_pipeline,
    run_grading_pipeline,
    # Oracle Prediction Market
    OracleState,
    create_oracle_pipeline,
    run_oracle_formulation,
    run_oracle_resolution,
    format_research_brief,
    format_retrospective,
    # File Processing Pipeline
    FileState,
    FilePipelineState,
    create_file_processing_pipeline,
    process_files,
    process_single_file,
    process_uploaded_files_langgraph,
)

# =============================================================================
# AGENTS (Research + Multi-Agent)
# =============================================================================
from .agents import (
    # Research Agent
    run_research_agent,
    run_research_agent_sync,
    research_for_tta,
    research_for_validation,
    research_for_domain,
    create_research_agent,
    # Multi-Agent Orchestrator
    run_multi_agent_analysis,
    quick_analysis,
    research_and_explore,
    validated_decision,
    full_analysis,
    format_multi_agent_result,
    create_multi_agent_pipeline,
)

# =============================================================================
# WORKSHOP MANAGER (LangGraph workshop mode controller)
# =============================================================================
from .workshop_manager import (
    WorkshopManager,
    WorkshopState,
    WORKSHOP_CONFIGS,
    get_workshop_types,
    run_workshop_turn,
)

# =============================================================================
# ORACLE TOOLS (Prediction Market + Text2Cypher)
# =============================================================================
from .tools import (
    # Oracle Prediction Market Tools
    create_prediction_market,
    get_open_markets,
    get_research_brief,
    get_hsi_surprises,
    place_prediction,
    get_market_predictions,
    resolve_market,
    get_user_calibration,
    get_leaderboard,
    ALL_ORACLE_TOOLS,
    # Text2Cypher Tools
    query_knowledge_graph,
    explain_cypher_query,
    text_to_cypher_query,
    store_market_in_neo4j,
    store_market_outcome_in_neo4j,
    MINDRIAN_SCHEMA,
)

# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    # Tools
    "search_web_tavily",
    "search_arxiv",
    "search_patents",
    "search_trends",
    "search_govdata",
    "search_datasets",
    "search_news",
    "validate_assumption",
    "research_trend",
    "query_neo4j_concepts",
    "query_neo4j_frameworks",
    "query_neo4j_problems",
    "extract_instant",
    "extract_deep",
    "ALL_RESEARCH_TOOLS",
    "ALL_KNOWLEDGE_TOOLS",
    "ALL_EXTRACTION_TOOLS",
    "ALL_TOOLS",
    # Schemas
    "SCQAAnalysis",
    "BeautifulQuestion",
    "ThinkingStep",
    "MintoPyramidOutput",
    "ComponentScore",
    "GradeBreakdown",
    "GradeReport",
    "BiasDetectionResult",
    "ParsedCV",
    "DomainCandidate",
    "IKAScore",
    "DomainRecommendation",
    "DomainDiscoveryOutput",
    "ReverseSalient",
    "ReverseSalientOutput",
    "ResearchSynthesis",
    "PWSSSignals",
    # Pipelines
    "MintoPyramidState",
    "create_minto_pipeline",
    "run_minto_pipeline",
    "format_minto_result",
    "DomainDiscoveryState",
    "create_domain_discovery_pipeline",
    "run_domain_discovery",
    "format_domain_discovery_result",
    "ReverseSalientState",
    "create_reverse_salient_pipeline",
    "run_reverse_salient",
    "format_reverse_salient_result",
    "GradingState",
    "create_grading_pipeline",
    "run_grading_pipeline",
    # Agents
    "run_research_agent",
    "run_research_agent_sync",
    "research_for_tta",
    "research_for_validation",
    "research_for_domain",
    "create_research_agent",
    "run_multi_agent_analysis",
    "quick_analysis",
    "research_and_explore",
    "validated_decision",
    "full_analysis",
    "format_multi_agent_result",
    "create_multi_agent_pipeline",
    # Workshop Manager
    "WorkshopManager",
    "WorkshopState",
    "WORKSHOP_CONFIGS",
    "get_workshop_types",
    "run_workshop_turn",
    # Oracle Pipeline
    "OracleState",
    "create_oracle_pipeline",
    "run_oracle_formulation",
    "run_oracle_resolution",
    "format_research_brief",
    "format_retrospective",
    # File Processing Pipeline
    "FileState",
    "FilePipelineState",
    "create_file_processing_pipeline",
    "process_files",
    "process_single_file",
    "process_uploaded_files_langgraph",
    # Oracle Tools
    "create_prediction_market",
    "get_open_markets",
    "get_research_brief",
    "get_hsi_surprises",
    "place_prediction",
    "get_market_predictions",
    "resolve_market",
    "get_user_calibration",
    "get_leaderboard",
    "ALL_ORACLE_TOOLS",
    # Text2Cypher
    "query_knowledge_graph",
    "explain_cypher_query",
    "text_to_cypher_query",
    "store_market_in_neo4j",
    "store_market_outcome_in_neo4j",
    "MINDRIAN_SCHEMA",
]
