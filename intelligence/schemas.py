"""
Pydantic Schemas for Mindrian Intelligence Layer
=================================================
Type-safe structured outputs for LLM responses.
Eliminates JSON parsing errors via LangChain's with_structured_output().

Usage:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from intelligence.schemas import MintoPyramidOutput, GradeReport

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    structured_llm = llm.with_structured_output(GradeReport)
    result = structured_llm.invoke("Grade this work: ...")
    # result is a validated GradeReport object
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class LetterGrade(str, Enum):
    """Standard letter grades."""
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D_PLUS = "D+"
    D = "D"
    D_MINUS = "D-"
    F = "F"


class EvidenceType(str, Enum):
    """Types of evidence for problem validation."""
    USER_QUOTE = "user_quote"
    DATA_POINT = "data_point"
    OBSERVATION = "observation"
    ASSUMPTION = "assumption"
    EXPERT_OPINION = "expert_opinion"
    RESEARCH_FINDING = "research_finding"


class ProblemValidation(str, Enum):
    """Problem validation status."""
    VALIDATED = "validated"
    PARTIALLY_VALIDATED = "partially_validated"
    ASSUMED = "assumed"
    FANTASY = "fantasy"


# =============================================================================
# MINTO PYRAMID / SCQA SCHEMAS
# =============================================================================

class SCQAAnalysis(BaseModel):
    """SCQA (Situation, Complication, Question, Answer) analysis output."""
    situation: str = Field(description="Current state and background context")
    complication: str = Field(description="Problem or tension that creates the need")
    question: str = Field(description="Core question arising from the complication")
    answer_hypothesis: str = Field(description="Hypothesized answer or direction")
    confidence: float = Field(ge=0, le=1, description="Confidence in the analysis (0-1)")


class BeautifulQuestion(BaseModel):
    """A 'Beautiful Question' for exploration."""
    question: str = Field(description="The question itself")
    category: str = Field(description="WHY, WHAT IF, or HOW")
    rationale: str = Field(description="Why this question matters")


class ThinkingStep(BaseModel):
    """A sequential thinking step."""
    step_number: int = Field(ge=1, le=10)
    title: str = Field(description="Step title")
    content: str = Field(description="Thinking content for this step")
    key_insight: Optional[str] = Field(default=None, description="Key insight from this step")


class MintoPyramidOutput(BaseModel):
    """Complete Minto Pyramid analysis output."""
    scqa: SCQAAnalysis
    beautiful_questions: List[BeautifulQuestion]
    thinking_steps: List[ThinkingStep]
    executive_summary: str = Field(description="2-3 sentence summary")
    key_findings: List[str] = Field(description="3-5 key findings")
    recommended_actions: List[str] = Field(description="3-5 actionable next steps")
    confidence_level: float = Field(ge=0, le=1, description="Overall confidence")


# =============================================================================
# GRADING SCHEMAS
# =============================================================================

class ComponentScore(BaseModel):
    """Score for a single grading component."""
    score: float = Field(ge=0, le=10, description="Score out of 10")
    weight: float = Field(ge=0, le=1, description="Weight in final calculation")
    assessment: str = Field(description="Brief assessment explanation")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")


class ProblemDiscovered(BaseModel):
    """A discovered problem from student work."""
    problem_statement: str = Field(description="The problem as stated")
    validation_status: ProblemValidation
    evidence_type: EvidenceType
    evidence_quote: Optional[str] = Field(default=None, description="Direct quote if available")
    confidence: float = Field(ge=0, le=1)
    worth_pursuing: bool = Field(description="Whether this problem is worth pursuing")


class BiasDetectionResult(BaseModel):
    """Cognitive bias detection results."""
    confirmation_bias_detected: bool
    confirmation_bias_evidence: Optional[str] = None
    anchoring_bias_detected: bool
    anchoring_bias_evidence: Optional[str] = None
    survivorship_bias_detected: bool
    survivorship_bias_evidence: Optional[str] = None
    selection_bias_detected: bool
    selection_bias_evidence: Optional[str] = None
    overall_confidence: float = Field(ge=0, le=1)
    can_proceed: bool = Field(description="Whether grading can proceed")
    blocking_reason: Optional[str] = None


class FrameworkUsage(BaseModel):
    """Framework usage analysis."""
    framework_name: str
    claimed_usage: bool = Field(description="Did student claim to use it?")
    actual_usage: bool = Field(description="Was it actually used properly?")
    effectiveness: float = Field(ge=0, le=10, description="How well was it used (0-10)")
    evidence: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)


class GradeBreakdown(BaseModel):
    """Complete grade breakdown by component."""
    problem_reality: ComponentScore = Field(description="Is it Real? (35%)")
    problem_discovery: ComponentScore = Field(description="Problem discovery quality (25%)")
    framework_integration: ComponentScore = Field(description="Framework usage (20%)")
    mindrian_thinking: ComponentScore = Field(description="Hidden connections (10%)")
    can_we_win: ComponentScore = Field(description="Capability check (5%)")
    is_it_worth_it: ComponentScore = Field(description="Market sizing (5%)")


class GradeReport(BaseModel):
    """Complete grading report output."""
    # Final grade
    letter_grade: LetterGrade
    numeric_score: float = Field(ge=0, le=100)
    verdict: str = Field(description="One-line summary verdict")

    # Breakdown
    breakdown: GradeBreakdown

    # Problems analysis
    problems_discovered: List[ProblemDiscovered]
    validated_problem_count: int
    assumed_problem_count: int

    # Framework analysis
    frameworks_used: List[FrameworkUsage]
    frameworks_missed: List[str] = Field(description="Frameworks that should have been used")

    # Insights
    strongest_finding: str = Field(description="Best validated finding")
    biggest_gap: str = Field(description="Most significant missing element")

    # Recommendations
    top_actions: List[str] = Field(description="Top 3 improvement actions")

    # Metadata
    grading_confidence: float = Field(ge=0, le=1)


# =============================================================================
# DOMAIN DISCOVERY SCHEMAS
# =============================================================================

class ParsedCV(BaseModel):
    """Parsed CV/background information."""
    skills: List[str]
    experience_domains: List[str]
    education: List[str]
    accomplishments: List[str]
    interests: List[str]
    unique_combinations: List[str]


class DomainCandidate(BaseModel):
    """A candidate problem domain."""
    domain_statement: str = Field(description="Stakeholder + Context + Outcome + Reason format")
    domain_type: str = Field(description="primary, combination, adjacent, passion, contrarian")
    rationale: str = Field(description="Why this domain fits the user")


class IKAScore(BaseModel):
    """Interest-Knowledge-Access scoring."""
    interest: int = Field(ge=1, le=5, description="Interest alignment (1-5)")
    knowledge: int = Field(ge=1, le=5, description="Relevant expertise (1-5)")
    access: int = Field(ge=1, le=5, description="Stakeholder access (1-5)")
    total: int = Field(ge=3, le=15, description="Total IKA score")
    rationale: str


class DomainRecommendation(BaseModel):
    """Ranked domain recommendation."""
    rank: int = Field(ge=1)
    domain_statement: str
    ika_score: IKAScore
    related_frameworks: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class DomainDiscoveryOutput(BaseModel):
    """Complete domain discovery output."""
    parsed_profile: ParsedCV
    top_recommendation: DomainRecommendation
    alternatives: List[DomainRecommendation]
    key_considerations: List[str]
    immediate_actions: List[str]


# =============================================================================
# REVERSE SALIENT SCHEMAS
# =============================================================================

class SystemComponent(BaseModel):
    """A component of the analyzed system."""
    name: str
    component_type: str = Field(description="input, process, output, support, constraint")
    function: str
    current_performance: str
    improvement_potential: str = Field(description="High, Medium, Low")


class ReverseSalient(BaseModel):
    """The identified reverse salient (bottleneck)."""
    component_name: str
    why_limiting: str
    impact_if_solved: str
    why_hard: str
    abstract_function: str = Field(description="Generic function, not domain-specific")


class AnalogousDomain(BaseModel):
    """An analogous domain for cross-domain search."""
    domain_name: str
    analogous_problem: str
    mapping_to_original: str
    search_query: str


class CrossDomainSolution(BaseModel):
    """A solution harvested from another domain."""
    solution_name: str
    source_domain: str
    core_mechanism: str
    transfer_potential: str
    novelty_score: int = Field(ge=1, le=5)


class AdaptationAnalysis(BaseModel):
    """Analysis of how to adapt a solution."""
    solution_name: str
    adaptation_strategy: str
    key_modifications: List[str]
    technical_gaps: List[str]
    resource_requirements: List[str]
    timeline_estimate: str
    confidence_level: int = Field(ge=1, le=5)


class Risk(BaseModel):
    """An identified risk."""
    risk_name: str
    risk_type: str = Field(description="transfer, technical, market, competitive, resource")
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    mitigation_strategy: str


class ReverseSalientOutput(BaseModel):
    """Complete Reverse Salient Discovery output."""
    problem_summary: str
    identified_salient: ReverseSalient
    analogous_domains: List[AnalogousDomain]
    harvested_solutions: List[CrossDomainSolution]
    top_recommendation: CrossDomainSolution
    adaptation_plan: AdaptationAnalysis
    risks: List[Risk]
    key_assumptions: List[str]
    implementation_roadmap: List[str]
    immediate_actions: List[str]


# =============================================================================
# RESEARCH SCHEMAS
# =============================================================================

class SearchResult(BaseModel):
    """A single search result."""
    title: str
    snippet: str
    url: str
    relevance_score: float = Field(ge=0, le=1, default=0.5)


class ResearchCategory(BaseModel):
    """Research results for a category."""
    category: str = Field(description="why, what_if, how, validation, trends")
    query_used: str
    results: List[SearchResult]
    key_insights: List[str]


class ResearchSynthesis(BaseModel):
    """Synthesized research output."""
    original_question: str
    executive_summary: str
    key_findings: List[str]
    evidence_assessment: str
    well_supported_claims: List[str]
    needs_validation: List[str]
    recommended_next_steps: List[str]
    questions_for_further_exploration: List[str]
    sources_used: int
    confidence_level: float = Field(ge=0, le=1)


# =============================================================================
# EXTRACTION SCHEMAS
# =============================================================================

class ExtractedStatistic(BaseModel):
    """An extracted statistic from text."""
    value: str
    context: str
    source_type: str = Field(description="stated, inferred, external")
    confidence: float = Field(ge=0, le=1)


class ExtractedAssumption(BaseModel):
    """An extracted assumption."""
    assumption: str
    is_explicit: bool
    criticality: str = Field(description="high, medium, low")
    needs_validation: bool


class PWSSSignals(BaseModel):
    """PWS signals extracted from text."""
    statistics: List[ExtractedStatistic]
    explicit_assumptions: List[ExtractedAssumption]
    implicit_assumptions: List[ExtractedAssumption]
    problems_mentioned: List[str]
    solutions_mentioned: List[str]
    open_questions: List[str]
    certainty_markers: List[str]
    uncertainty_markers: List[str]
    pws_quality_score: float = Field(ge=0, le=10)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "LetterGrade",
    "EvidenceType",
    "ProblemValidation",
    # Minto
    "SCQAAnalysis",
    "BeautifulQuestion",
    "ThinkingStep",
    "MintoPyramidOutput",
    # Grading
    "ComponentScore",
    "ProblemDiscovered",
    "BiasDetectionResult",
    "FrameworkUsage",
    "GradeBreakdown",
    "GradeReport",
    # Domain Discovery
    "ParsedCV",
    "DomainCandidate",
    "IKAScore",
    "DomainRecommendation",
    "DomainDiscoveryOutput",
    # Reverse Salient
    "SystemComponent",
    "ReverseSalient",
    "AnalogousDomain",
    "CrossDomainSolution",
    "AdaptationAnalysis",
    "Risk",
    "ReverseSalientOutput",
    # Research
    "SearchResult",
    "ResearchCategory",
    "ResearchSynthesis",
    # Extraction
    "ExtractedStatistic",
    "ExtractedAssumption",
    "PWSSSignals",
]
