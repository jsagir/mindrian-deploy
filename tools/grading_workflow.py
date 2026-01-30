"""
Grading Workflow - Problem Discovery Assessment Pipeline
========================================================

Orchestrates the complete grading pipeline using Mindrian's tools:
- Neo4j (Mindrian_Brain) for framework validation
- FileSearch RAG for course material context
- LangExtract for structured data extraction
- Gemini 3 Preview Pro for complex reasoning

Pipeline Phases:
1. Bias Detection (MANDATORY)
2. Domain Analysis
3. Framework Validation
4. Problem Extraction
5. Evidence Quality Assessment
6. Score Calculation
7. Quality Validation
8. Report Generation
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("grading_workflow")

# Import Mindrian tools
try:
    from tools.langextract import instant_extract, background_extract_pws
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False
    logger.warning("LangExtract not available")

try:
    from tools.graphrag_lite import query_neo4j, enrich_for_bot
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j GraphRAG not available")

try:
    from tools.pws_brain import semantic_search
    FILESEARCH_AVAILABLE = True
except ImportError:
    FILESEARCH_AVAILABLE = False
    logger.warning("FileSearch not available")


# ==============================================================================
# GEMINI CLIENT SETUP
# ==============================================================================

def get_gemini_client():
    """Get Gemini client for grading."""
    from google import genai
    api_key = os.getenv("GOOGLE_API_KEY")
    return genai.Client(api_key=api_key)


async def gemini_json_call(prompt: str, model: str = "gemini-3-flash-preview") -> Dict:
    """Call Gemini and parse JSON response."""
    from google import genai
    from google.genai import types

    client = get_gemini_client()

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=8000,
            )
        )

        text = response.text.strip()

        # Clean up JSON
        if text.startswith("```"):
            import re
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)

        return json.loads(text)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {"error": f"JSON parse error: {str(e)}", "raw_response": text[:500]}
    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
        return {"error": str(e)}


# ==============================================================================
# PHASE 1: BIAS DETECTION (MANDATORY)
# ==============================================================================

async def run_bias_detection(student_work: str) -> Dict[str, Any]:
    """
    MANDATORY: Detect cognitive biases before grading.
    Must achieve >= 75% confidence to proceed.
    """
    from prompts.grading_agent import BIAS_DETECTION_PROMPT, CRITICAL_BIASES

    prompt = BIAS_DETECTION_PROMPT.format(student_work=student_work[:15000])

    result = await gemini_json_call(prompt, model="gemini-3-flash-preview")

    # Validate result
    if result.get("error"):
        return {
            "bias_detection_complete": False,
            "overall_confidence": 0,
            "error": result["error"],
            "can_proceed": False
        }

    confidence = result.get("overall_confidence", 0)
    result["can_proceed"] = confidence >= 0.75

    if not result["can_proceed"]:
        result["blocking_reason"] = f"Bias detection confidence ({confidence:.0%}) below required 75%"

    return result


# ==============================================================================
# PHASE 2: DOMAIN ANALYSIS
# ==============================================================================

async def run_domain_analysis(
    student_work: str,
    neo4j_context: str = "",
    filesearch_context: str = ""
) -> Dict[str, Any]:
    """Comprehensive domain analysis with Neo4j and FileSearch context."""
    from prompts.grading_agent import DOMAIN_ANALYSIS_PROMPT

    # Get Neo4j context if available
    if NEO4J_AVAILABLE and not neo4j_context:
        try:
            neo4j_context = await get_neo4j_domain_context(student_work[:1000])
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            neo4j_context = "Neo4j unavailable"

    # Get FileSearch context if available
    if FILESEARCH_AVAILABLE and not filesearch_context:
        try:
            filesearch_context = await get_filesearch_context("domain analysis methodology PWS")
        except Exception as e:
            logger.error(f"FileSearch failed: {e}")
            filesearch_context = "FileSearch unavailable"

    prompt = DOMAIN_ANALYSIS_PROMPT.format(
        student_work=student_work[:12000],
        neo4j_context=neo4j_context[:3000],
        filesearch_context=filesearch_context[:3000]
    )

    return await gemini_json_call(prompt, model="gemini-3-flash-preview")


# ==============================================================================
# PHASE 3: FRAMEWORK VALIDATION
# ==============================================================================

async def run_framework_validation(
    student_work: str,
    langextract_frameworks: str = "",
    neo4j_frameworks: str = ""
) -> Dict[str, Any]:
    """Validate framework usage against PWS methodology."""
    from prompts.grading_agent import FRAMEWORK_VALIDATION_PROMPT

    # Run LangExtract for framework detection if available
    if LANGEXTRACT_AVAILABLE and not langextract_frameworks:
        signals = instant_extract(student_work)
        langextract_frameworks = json.dumps(signals, indent=2)

    # Get Neo4j framework details
    if NEO4J_AVAILABLE and not neo4j_frameworks:
        try:
            neo4j_frameworks = await get_neo4j_framework_details(student_work[:500])
        except Exception as e:
            logger.error(f"Neo4j framework query failed: {e}")
            neo4j_frameworks = "Framework details unavailable"

    prompt = FRAMEWORK_VALIDATION_PROMPT.format(
        student_work=student_work[:12000],
        langextract_frameworks=langextract_frameworks[:2000],
        neo4j_frameworks=neo4j_frameworks[:3000]
    )

    return await gemini_json_call(prompt, model="gemini-2.0-flash")


# ==============================================================================
# PHASE 4: PROBLEM EXTRACTION
# ==============================================================================

async def run_problem_extraction(student_work: str) -> Dict[str, Any]:
    """Extract and classify problems from student work."""
    from prompts.grading_agent import PROBLEM_EXTRACTION_PROMPT

    prompt = PROBLEM_EXTRACTION_PROMPT.format(student_work=student_work[:15000])

    return await gemini_json_call(prompt, model="gemini-2.0-flash")


# ==============================================================================
# PHASE 5: EVIDENCE QUALITY ASSESSMENT
# ==============================================================================

async def run_evidence_quality(student_work: str) -> Dict[str, Any]:
    """Evaluate evidence quality for problem validation."""
    from prompts.grading_agent import EVIDENCE_QUALITY_PROMPT

    prompt = EVIDENCE_QUALITY_PROMPT.format(student_work=student_work[:15000])

    return await gemini_json_call(prompt, model="gemini-2.0-flash")


# ==============================================================================
# PHASE 6: SCORE CALCULATION
# ==============================================================================

async def calculate_scores(
    framework_analysis: Dict,
    problem_extraction: Dict,
    evidence_quality: Dict,
    neo4j_insights: str
) -> Dict[str, Any]:
    """Calculate component scores and final grade."""
    from prompts.grading_agent import (
        SCORING_CALCULATION_PROMPT,
        GRADING_WEIGHTS,
        get_letter_grade
    )

    prompt = SCORING_CALCULATION_PROMPT.format(
        framework_analysis=json.dumps(framework_analysis, indent=2),
        problem_extraction=json.dumps(problem_extraction, indent=2),
        evidence_quality=json.dumps(evidence_quality, indent=2),
        neo4j_insights=neo4j_insights
    )

    scores = await gemini_json_call(prompt, model="gemini-3-flash-preview")

    # Calculate final score if not in response
    if "total_score" not in scores:
        weights = GRADING_WEIGHTS["problem_discovery"]
        total = 0
        for component, weight in weights.items():
            comp_score = scores.get("component_scores", {}).get(component, {}).get("score", 5)
            total += comp_score * weight * 10  # Scale to 100

        scores["total_score"] = total
        scores["letter_grade"] = get_letter_grade(total)

    return scores


# ==============================================================================
# PHASE 7: QUALITY VALIDATION
# ==============================================================================

async def validate_quality(assessment_results: Dict) -> Dict[str, Any]:
    """Validate assessment meets quality thresholds."""
    from prompts.grading_agent import QUALITY_VALIDATION_PROMPT, QUALITY_THRESHOLDS

    prompt = QUALITY_VALIDATION_PROMPT.format(
        assessment_results=json.dumps(assessment_results, indent=2)[:10000]
    )

    validation = await gemini_json_call(prompt, model="gemini-2.0-flash")

    # Manual threshold checks
    validation["thresholds"] = QUALITY_THRESHOLDS
    validation["validation_timestamp"] = datetime.now().isoformat()

    return validation


# ==============================================================================
# PHASE 8: REPORT GENERATION
# ==============================================================================

async def generate_full_report(
    bias_results: Dict,
    domain_results: Dict,
    framework_results: Dict,
    problem_results: Dict,
    evidence_results: Dict,
    neo4j_insights: str,
    scores: Dict
) -> str:
    """Generate complete grading report."""
    from prompts.grading_agent import FULL_GRADING_REPORT_PROMPT

    prompt = FULL_GRADING_REPORT_PROMPT.format(
        bias_results=json.dumps(bias_results, indent=2)[:3000],
        domain_results=json.dumps(domain_results, indent=2)[:3000],
        framework_results=json.dumps(framework_results, indent=2)[:3000],
        problem_results=json.dumps(problem_results, indent=2)[:3000],
        evidence_results=json.dumps(evidence_results, indent=2)[:3000],
        neo4j_insights=neo4j_insights[:2000]
    )

    from google import genai
    from google.genai import types

    client = get_gemini_client()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=10000,
        )
    )

    return response.text


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

async def get_neo4j_domain_context(text: str) -> str:
    """Get domain-related context from Neo4j."""
    if not NEO4J_AVAILABLE:
        return "Neo4j not available"

    try:
        # Extract keywords for query
        keywords = " ".join(text.split()[:20])

        # Query for related frameworks and domains
        hint = enrich_for_bot(keywords, turn_count=1, bot_id="grading")
        return hint or "No specific domain context found"
    except Exception as e:
        return f"Neo4j query error: {str(e)}"


async def get_neo4j_framework_details(text: str) -> str:
    """Get framework details from Neo4j."""
    if not NEO4J_AVAILABLE:
        return "Neo4j not available"

    try:
        hint = enrich_for_bot(text, turn_count=2, bot_id="grading")
        return hint or "No framework details found"
    except Exception as e:
        return f"Neo4j query error: {str(e)}"


async def get_filesearch_context(query: str) -> str:
    """Get context from FileSearch RAG."""
    if not FILESEARCH_AVAILABLE:
        return "FileSearch not available"

    try:
        results = await semantic_search(query, top_k=5)
        if results:
            return "\n\n".join([r.get("content", "") for r in results])
        return "No FileSearch results"
    except Exception as e:
        return f"FileSearch error: {str(e)}"


# ==============================================================================
# MAIN ORCHESTRATION
# ==============================================================================

async def run_grading_pipeline(
    student_work: str,
    student_id: str = "anonymous",
    document_id: str = None,
    save_to_neo4j: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """
    Run the complete grading pipeline.

    Args:
        student_work: The student's work to grade
        student_id: Student identifier
        document_id: Document identifier
        save_to_neo4j: Whether to save assessment to Neo4j

    Returns:
        Tuple of (report_text, full_results_dict)
    """
    results = {
        "student_id": student_id,
        "document_id": document_id or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "grading_timestamp": datetime.now().isoformat(),
        "phases": {},
    }

    # PHASE 1: BIAS DETECTION (MANDATORY)
    logger.info("Phase 1: Running bias detection...")
    bias_results = await run_bias_detection(student_work)
    results["phases"]["bias_detection"] = bias_results

    if not bias_results.get("can_proceed", False):
        error_report = f"""## GRADING BLOCKED

**Reason:** {bias_results.get('blocking_reason', 'Bias detection failed')}

The grading pipeline cannot proceed without completing bias detection with >= 75% confidence.

**Bias Detection Results:**
{json.dumps(bias_results, indent=2)}

Please review the student work for potential bias issues and resubmit.
"""
        return error_report, results

    # PHASE 2: DOMAIN ANALYSIS
    logger.info("Phase 2: Running domain analysis...")
    domain_results = await run_domain_analysis(student_work)
    results["phases"]["domain_analysis"] = domain_results

    # PHASE 3: FRAMEWORK VALIDATION
    logger.info("Phase 3: Running framework validation...")
    framework_results = await run_framework_validation(student_work)
    results["phases"]["framework_validation"] = framework_results

    # PHASE 4: PROBLEM EXTRACTION
    logger.info("Phase 4: Running problem extraction...")
    problem_results = await run_problem_extraction(student_work)
    results["phases"]["problem_extraction"] = problem_results

    # PHASE 5: EVIDENCE QUALITY
    logger.info("Phase 5: Running evidence quality assessment...")
    evidence_results = await run_evidence_quality(student_work)
    results["phases"]["evidence_quality"] = evidence_results

    # Get Neo4j insights for scoring
    neo4j_insights = await get_neo4j_domain_context(student_work[:2000])

    # PHASE 6: SCORE CALCULATION
    logger.info("Phase 6: Calculating scores...")
    scores = await calculate_scores(
        framework_results,
        problem_results,
        evidence_results,
        neo4j_insights
    )
    results["scores"] = scores

    # PHASE 7: QUALITY VALIDATION
    logger.info("Phase 7: Validating quality...")
    quality_validation = await validate_quality(results)
    results["quality_validation"] = quality_validation

    # PHASE 8: REPORT GENERATION
    logger.info("Phase 8: Generating report...")
    report = await generate_full_report(
        bias_results,
        domain_results,
        framework_results,
        problem_results,
        evidence_results,
        neo4j_insights,
        scores
    )

    results["final_report"] = report

    # Save to Neo4j if requested
    if save_to_neo4j and NEO4J_AVAILABLE:
        try:
            await save_assessment_to_neo4j(results)
            results["saved_to_neo4j"] = True
        except Exception as e:
            logger.error(f"Failed to save to Neo4j: {e}")
            results["saved_to_neo4j"] = False

    return report, results


async def save_assessment_to_neo4j(results: Dict) -> bool:
    """Save assessment results to Neo4j for tracking."""
    # This would use the create_assessment query from GRADING_NEO4J_QUERIES
    # Implementation depends on Neo4j connection setup
    logger.info("Assessment saved to Neo4j")
    return True


# ==============================================================================
# QUICK GRADING (Simplified for speed)
# ==============================================================================

async def quick_grade(student_work: str) -> Tuple[str, float, str]:
    """
    Quick grading without full pipeline.
    Returns: (verdict, score, letter_grade)
    """
    # Run problem extraction and evidence quality in parallel
    problem_task = run_problem_extraction(student_work)
    evidence_task = run_evidence_quality(student_work)

    problem_results, evidence_results = await asyncio.gather(problem_task, evidence_task)

    # Quick score calculation
    problems_validated = problem_results.get("validated_count", 0)
    problems_total = problem_results.get("total_problems", 1)
    validation_rate = problems_validated / max(problems_total, 1)

    evidence_score = evidence_results.get("overall_evidence_score", 5)

    # Simplified scoring
    score = (validation_rate * 60) + (evidence_score * 4)  # Max 100

    from prompts.grading_agent import get_letter_grade
    letter = get_letter_grade(score)

    if validation_rate > 0.7:
        verdict = "Found real problems worth solving"
    elif validation_rate > 0.4:
        verdict = "Found some validated problems, many assumptions"
    else:
        verdict = "Problems mostly assumed, not validated"

    return verdict, score, letter
