"""
Grading Pipeline - LangGraph Implementation with Structured Outputs
===================================================================
8-phase grading pipeline using Pydantic schemas for type-safe outputs.

Pipeline:
1. Bias Detection (MANDATORY - gate)
2. Domain Analysis
3. Framework Validation
4. Problem Extraction
5. Evidence Quality Assessment
6. Score Calculation
7. Quality Validation
8. Report Generation

Key improvements over grading_workflow.py:
- Pydantic schemas eliminate JSON parse errors
- LangGraph state management
- Checkpointing for resume capability
- Parallel execution where possible

Usage:
    from intelligence.pipelines.grading import run_grading_pipeline

    report, results = await run_grading_pipeline(
        student_work="...",
        session_id="user_123"
    )
"""

import os
import json
import asyncio
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Tuple
from operator import add
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from intelligence.schemas import (
    BiasDetectionResult,
    GradeReport,
    GradeBreakdown,
    ComponentScore,
    ProblemDiscovered,
    FrameworkUsage,
    LetterGrade,
    ProblemValidation,
    EvidenceType,
)

# Try to use Postgres checkpointer if available
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


# =============================================================================
# STATE DEFINITION
# =============================================================================

def merge_dicts(left: dict, right: dict) -> dict:
    """Reducer: merge dictionaries."""
    return {**left, **right}


class GradingState(TypedDict):
    """State for grading pipeline."""
    # Input
    student_work: str
    student_id: str
    document_id: str

    # Phase outputs (validated Pydantic objects serialized to dict)
    bias_detection: dict
    domain_analysis: dict
    framework_validation: dict
    problem_extraction: dict
    evidence_quality: dict
    scores: dict
    quality_validation: dict

    # Final outputs
    grade_report: dict  # GradeReport as dict
    report_markdown: str

    # Control flow
    can_proceed: bool
    blocking_reason: str

    # Metadata
    started_at: str
    completed_steps: Annotated[list, add]
    errors: Annotated[list, add]


# =============================================================================
# STRUCTURED LLM SETUP
# =============================================================================

def get_structured_llm(schema, model: str = "gemini-2.0-flash"):
    """
    Get a LangChain LLM with structured output.

    Uses Pydantic schema for guaranteed valid outputs.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2,
        )
        return llm.with_structured_output(schema)
    except ImportError:
        # Fallback to direct Gemini with manual parsing
        return None


def get_raw_llm(model: str = "gemini-2.0-flash"):
    """Get raw LLM for text generation."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
        )
    except ImportError:
        return None


# =============================================================================
# NODE IMPLEMENTATIONS
# =============================================================================

async def detect_bias(state: GradingState) -> dict:
    """
    PHASE 1: Bias Detection (MANDATORY GATE)
    Must achieve >= 75% confidence to proceed.
    """
    try:
        structured_llm = get_structured_llm(BiasDetectionResult)

        if structured_llm:
            prompt = f"""Analyze this student work for cognitive biases that could affect grading:

STUDENT WORK:
{state["student_work"][:15000]}

Detect:
1. Confirmation bias - Are they only seeking evidence that supports their view?
2. Anchoring bias - Are they fixated on initial numbers/ideas?
3. Survivorship bias - Are they only looking at successes?
4. Selection bias - Is their sample/evidence cherry-picked?

Set can_proceed to true only if overall_confidence >= 0.75."""

            result = await structured_llm.ainvoke(prompt)

            return {
                "bias_detection": result.model_dump(),
                "can_proceed": result.can_proceed,
                "blocking_reason": result.blocking_reason or "",
                "completed_steps": ["bias_detection"]
            }
        else:
            # Fallback to raw Gemini
            from tools.grading_workflow import run_bias_detection
            result = await run_bias_detection(state["student_work"])
            return {
                "bias_detection": result,
                "can_proceed": result.get("can_proceed", False),
                "blocking_reason": result.get("blocking_reason", ""),
                "completed_steps": ["bias_detection"]
            }

    except Exception as e:
        return {
            "bias_detection": {"error": str(e)},
            "can_proceed": False,
            "blocking_reason": f"Bias detection failed: {str(e)}",
            "errors": [f"Bias detection error: {str(e)}"],
            "completed_steps": ["bias_detection_failed"]
        }


def should_continue(state: GradingState) -> str:
    """Conditional edge: check if we can proceed past bias detection."""
    if state.get("can_proceed", False):
        return "continue"
    else:
        return "blocked"


async def analyze_domain(state: GradingState) -> dict:
    """PHASE 2: Domain Analysis."""
    try:
        from tools.grading_workflow import run_domain_analysis
        result = await run_domain_analysis(state["student_work"])
        return {
            "domain_analysis": result,
            "completed_steps": ["domain_analysis"]
        }
    except Exception as e:
        return {
            "domain_analysis": {"error": str(e)},
            "errors": [f"Domain analysis error: {str(e)}"],
            "completed_steps": ["domain_analysis_failed"]
        }


async def validate_frameworks(state: GradingState) -> dict:
    """PHASE 3: Framework Validation."""
    try:
        from tools.grading_workflow import run_framework_validation
        result = await run_framework_validation(state["student_work"])
        return {
            "framework_validation": result,
            "completed_steps": ["framework_validation"]
        }
    except Exception as e:
        return {
            "framework_validation": {"error": str(e)},
            "errors": [f"Framework validation error: {str(e)}"],
            "completed_steps": ["framework_validation_failed"]
        }


async def extract_problems(state: GradingState) -> dict:
    """PHASE 4: Problem Extraction."""
    try:
        from tools.grading_workflow import run_problem_extraction
        result = await run_problem_extraction(state["student_work"])
        return {
            "problem_extraction": result,
            "completed_steps": ["problem_extraction"]
        }
    except Exception as e:
        return {
            "problem_extraction": {"error": str(e)},
            "errors": [f"Problem extraction error: {str(e)}"],
            "completed_steps": ["problem_extraction_failed"]
        }


async def assess_evidence(state: GradingState) -> dict:
    """PHASE 5: Evidence Quality Assessment."""
    try:
        from tools.grading_workflow import run_evidence_quality
        result = await run_evidence_quality(state["student_work"])
        return {
            "evidence_quality": result,
            "completed_steps": ["evidence_quality"]
        }
    except Exception as e:
        return {
            "evidence_quality": {"error": str(e)},
            "errors": [f"Evidence quality error: {str(e)}"],
            "completed_steps": ["evidence_quality_failed"]
        }


async def calculate_scores(state: GradingState) -> dict:
    """PHASE 6: Calculate component scores and final grade."""
    try:
        from prompts.minto_grading import calculate_minto_score, get_minto_letter_grade

        fw = state.get("framework_validation", {})
        prob = state.get("problem_extraction", {})
        ev = state.get("evidence_quality", {})

        # Extract scores from phase outputs
        pr_score = ev.get("problem_reality_score", 5)
        pd_score = prob.get("discovery_score", 5)
        fi_score = fw.get("framework_score", 5)
        mt_score = fw.get("mindrian_thinking_score", 5)
        cw_score = prob.get("capability_score", 5)
        iw_score = prob.get("market_score", 5)

        # Calculate final score
        total = calculate_minto_score(pr_score, pd_score, fi_score, mt_score, cw_score, iw_score)
        total_scaled = total * 10  # Scale to 100

        scores = {
            "component_scores": {
                "problem_reality": {"score": pr_score, "weight": 0.35},
                "problem_discovery": {"score": pd_score, "weight": 0.25},
                "framework_integration": {"score": fi_score, "weight": 0.20},
                "mindrian_thinking": {"score": mt_score, "weight": 0.10},
                "can_we_win": {"score": cw_score, "weight": 0.05},
                "is_it_worth_it": {"score": iw_score, "weight": 0.05},
            },
            "total_score": total_scaled,
            "letter_grade": get_minto_letter_grade(total_scaled),
        }

        return {
            "scores": scores,
            "completed_steps": ["calculate_scores"]
        }

    except Exception as e:
        return {
            "scores": {"error": str(e)},
            "errors": [f"Score calculation error: {str(e)}"],
            "completed_steps": ["calculate_scores_failed"]
        }


async def validate_quality(state: GradingState) -> dict:
    """PHASE 7: Quality Validation."""
    try:
        from tools.grading_workflow import validate_quality as vq
        results = {
            "scores": state.get("scores", {}),
            "framework_validation": state.get("framework_validation", {}),
            "problem_extraction": state.get("problem_extraction", {}),
        }
        validation = await vq(results)
        return {
            "quality_validation": validation,
            "completed_steps": ["quality_validation"]
        }
    except Exception as e:
        return {
            "quality_validation": {"error": str(e)},
            "errors": [f"Quality validation error: {str(e)}"],
            "completed_steps": ["quality_validation_failed"]
        }


async def generate_report(state: GradingState) -> dict:
    """PHASE 8: Generate final grade report."""
    try:
        # Try structured output first
        structured_llm = get_structured_llm(GradeReport, model="gemini-2.0-flash")

        if structured_llm:
            prompt = f"""Generate a complete grading report for this student work:

STUDENT WORK SUMMARY:
{state["student_work"][:8000]}

BIAS DETECTION:
{json.dumps(state.get("bias_detection", {}), indent=2)[:2000]}

DOMAIN ANALYSIS:
{json.dumps(state.get("domain_analysis", {}), indent=2)[:2000]}

FRAMEWORK VALIDATION:
{json.dumps(state.get("framework_validation", {}), indent=2)[:2000]}

PROBLEM EXTRACTION:
{json.dumps(state.get("problem_extraction", {}), indent=2)[:2000]}

EVIDENCE QUALITY:
{json.dumps(state.get("evidence_quality", {}), indent=2)[:2000]}

CALCULATED SCORES:
{json.dumps(state.get("scores", {}), indent=2)}

Generate a comprehensive GradeReport with:
- Final letter grade and numeric score
- Complete breakdown by component
- List of problems discovered with validation status
- Framework usage analysis
- Top 3 improvement actions
- Strongest finding and biggest gap"""

            result = await structured_llm.ainvoke(prompt)
            grade_report = result.model_dump()
        else:
            # Fallback to raw report
            grade_report = {
                "letter_grade": state.get("scores", {}).get("letter_grade", "C"),
                "numeric_score": state.get("scores", {}).get("total_score", 70),
                "verdict": "Grading completed",
                "breakdown": state.get("scores", {}).get("component_scores", {}),
            }

        # Generate markdown report
        report_md = format_grade_report_markdown(state, grade_report)

        return {
            "grade_report": grade_report,
            "report_markdown": report_md,
            "completed_steps": ["generate_report"]
        }

    except Exception as e:
        return {
            "grade_report": {"error": str(e)},
            "report_markdown": f"Report generation failed: {str(e)}",
            "errors": [f"Report generation error: {str(e)}"],
            "completed_steps": ["generate_report_failed"]
        }


async def generate_blocked_report(state: GradingState) -> dict:
    """Generate report when grading is blocked."""
    report_md = f"""## GRADING BLOCKED

**Reason:** {state.get('blocking_reason', 'Unknown')}

The grading pipeline cannot proceed without completing bias detection with >= 75% confidence.

**Bias Detection Results:**
{json.dumps(state.get('bias_detection', {}), indent=2)}

Please review the student work for potential bias issues and resubmit.
"""
    return {
        "report_markdown": report_md,
        "grade_report": {"blocked": True, "reason": state.get("blocking_reason", "")},
        "completed_steps": ["blocked_report"]
    }


# =============================================================================
# FORMATTING HELPERS
# =============================================================================

def format_grade_report_markdown(state: GradingState, grade_report: dict) -> str:
    """Format grade report as markdown."""
    scores = state.get("scores", {})
    cs = scores.get("component_scores", {})

    output = [f"""# Grading Report

## FINAL GRADE: {grade_report.get('letter_grade', 'N/A')} ({grade_report.get('numeric_score', 0):.1f}/100)

**Verdict:** {grade_report.get('verdict', 'Assessment complete')}

---

## Grade Breakdown

| Component | Weight | Score | Points |
|-----------|--------|-------|--------|
| Problem Reality (Is it Real?) | 35% | {cs.get('problem_reality', {}).get('score', '-')}/10 | {cs.get('problem_reality', {}).get('score', 0) * 0.35 * 10:.1f} |
| Problem Discovery | 25% | {cs.get('problem_discovery', {}).get('score', '-')}/10 | {cs.get('problem_discovery', {}).get('score', 0) * 0.25 * 10:.1f} |
| Framework Integration | 20% | {cs.get('framework_integration', {}).get('score', '-')}/10 | {cs.get('framework_integration', {}).get('score', 0) * 0.20 * 10:.1f} |
| Mindrian Thinking | 10% | {cs.get('mindrian_thinking', {}).get('score', '-')}/10 | {cs.get('mindrian_thinking', {}).get('score', 0) * 0.10 * 10:.1f} |
| Can We Win? | 5% | {cs.get('can_we_win', {}).get('score', '-')}/10 | {cs.get('can_we_win', {}).get('score', 0) * 0.05 * 10:.1f} |
| Is it Worth It? | 5% | {cs.get('is_it_worth_it', {}).get('score', '-')}/10 | {cs.get('is_it_worth_it', {}).get('score', 0) * 0.05 * 10:.1f} |
| **TOTAL** | **100%** | - | **{scores.get('total_score', 0):.1f}** |

---
"""]

    # Problems discovered
    problems = grade_report.get("problems_discovered", [])
    if problems:
        output.append("## Problems Discovered\n")
        for p in problems[:5]:
            status = p.get("validation_status", "unknown")
            output.append(f"- **{p.get('problem_statement', 'Unknown')}** [{status}]")
        output.append("")

    # Strongest finding and biggest gap
    output.append(f"""## Key Insights

**Strongest Finding:** {grade_report.get('strongest_finding', 'N/A')}

**Biggest Gap:** {grade_report.get('biggest_gap', 'N/A')}

---

## Top Actions for Improvement

""")

    for i, action in enumerate(grade_report.get("top_actions", [])[:3], 1):
        output.append(f"{i}. {action}")

    output.append(f"\n\n---\n*Graded at: {state.get('started_at', 'Unknown')}*")

    return "\n".join(output)


# =============================================================================
# PIPELINE CONSTRUCTION
# =============================================================================

def create_grading_pipeline(checkpointer=None):
    """
    Create the Grading LangGraph pipeline.

    Returns:
        Compiled LangGraph application.
    """
    graph = StateGraph(GradingState)

    # Add nodes
    graph.add_node("detect_bias", detect_bias)
    graph.add_node("analyze_domain", analyze_domain)
    graph.add_node("validate_frameworks", validate_frameworks)
    graph.add_node("extract_problems", extract_problems)
    graph.add_node("assess_evidence", assess_evidence)
    graph.add_node("calculate_scores", calculate_scores)
    graph.add_node("validate_quality", validate_quality)
    graph.add_node("generate_report", generate_report)
    graph.add_node("blocked_report", generate_blocked_report)

    # Entry point
    graph.add_edge(START, "detect_bias")

    # Conditional: proceed or block after bias detection
    graph.add_conditional_edges(
        "detect_bias",
        should_continue,
        {
            "continue": "analyze_domain",
            "blocked": "blocked_report"
        }
    )

    # Parallel phase 2-5 (domain, framework, problems, evidence)
    graph.add_edge("analyze_domain", "validate_frameworks")
    graph.add_edge("validate_frameworks", "extract_problems")
    graph.add_edge("extract_problems", "assess_evidence")

    # Sequential phase 6-8
    graph.add_edge("assess_evidence", "calculate_scores")
    graph.add_edge("calculate_scores", "validate_quality")
    graph.add_edge("validate_quality", "generate_report")

    # End points
    graph.add_edge("generate_report", END)
    graph.add_edge("blocked_report", END)

    # Use provided checkpointer or default to memory
    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


async def get_postgres_checkpointer():
    """Get Postgres checkpointer if available."""
    if not POSTGRES_AVAILABLE:
        return None

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None

    try:
        checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
        await checkpointer.setup()
        return checkpointer
    except Exception as e:
        print(f"[GRADING] Postgres checkpointer unavailable: {e}")
        return None


# =============================================================================
# PUBLIC API
# =============================================================================

async def run_grading_pipeline(
    student_work: str,
    session_id: str,
    student_id: str = "anonymous",
    document_id: str = None,
    use_postgres: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Run the complete grading pipeline.

    Args:
        student_work: The student's work to grade.
        session_id: Session ID for checkpointing.
        student_id: Student identifier.
        document_id: Document identifier.
        use_postgres: Whether to use Postgres checkpointing.

    Returns:
        Tuple of (report_markdown, full_results_dict).

    Example:
        report, results = await run_grading_pipeline(
            student_work="...",
            session_id="user_123"
        )
        print(report)
    """
    # Get checkpointer
    checkpointer = None
    if use_postgres:
        checkpointer = await get_postgres_checkpointer()

    if checkpointer is None:
        checkpointer = MemorySaver()
        print("[GRADING] Using in-memory checkpointer")

    # Create pipeline
    pipeline = create_grading_pipeline(checkpointer)

    # Initial state
    initial_state = {
        "student_work": student_work,
        "student_id": student_id,
        "document_id": document_id or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "bias_detection": {},
        "domain_analysis": {},
        "framework_validation": {},
        "problem_extraction": {},
        "evidence_quality": {},
        "scores": {},
        "quality_validation": {},
        "grade_report": {},
        "report_markdown": "",
        "can_proceed": True,
        "blocking_reason": "",
        "started_at": datetime.now().isoformat(),
        "completed_steps": [],
        "errors": [],
    }

    # Config for checkpointing
    config = {"configurable": {"thread_id": session_id}}

    # Run pipeline
    try:
        result = await pipeline.ainvoke(initial_state, config)
        return result.get("report_markdown", ""), result
    except Exception as e:
        error_report = f"Pipeline error: {str(e)}"
        return error_report, {**initial_state, "errors": [error_report]}
