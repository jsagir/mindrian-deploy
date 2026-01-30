"""
Claims-Aware Presentation & PDF Analyzer for Mindrian
=====================================================

Analyzes PDFs, decks, and presentations using Gemini multimodal capabilities.
Extracts images from PDFs and performs visual + text analysis.
Integrates with LangExtract for PWS (Problems Worth Solving) methodology analysis.

Features:
- PDF page-to-image conversion for visual analysis
- Claims-First analysis to preserve key arguments
- Complete information extraction (names, research, links, data)
- PWS methodology integration via LangExtract
- Assumption detection and evidence anchoring
- Structured output with visual representation

Usage:
    from tools.presentation_analyzer import analyze_presentation, analyze_pdf_visually

    # Analyze a presentation/deck with PWS methodology
    result = await analyze_presentation(file_path, file_name)

    # Just extract PDF as images for Gemini
    images = extract_pdf_images(file_path)

    # Run PWS-aware claims analysis
    pws_analysis = await analyze_claims_pws(text_content)
"""

import os
import io
import logging
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger("presentation_analyzer")

# Import LangExtract for PWS analysis
try:
    from tools.langextract import (
        instant_extract,
        background_extract_pws,
        format_instant_extraction,
        format_deep_extraction,
        get_extraction_hint,
    )
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False
    logger.warning("LangExtract not available. PWS analysis will be limited.")

# Check for pdf2image availability
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not installed. PDF visual analysis will be limited.")

# Check for PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class ClaimsAnalysis:
    """Results of claims-aware analysis with PWS methodology integration."""
    # Core claims extraction
    primary_thesis: str = ""
    key_claims: List[str] = field(default_factory=list)
    evidence_anchors: List[str] = field(default_factory=list)
    presenters: List[Dict[str, str]] = field(default_factory=list)
    research_citations: List[str] = field(default_factory=list)
    links_resources: List[str] = field(default_factory=list)
    key_data_points: List[str] = field(default_factory=list)
    slide_summaries: List[Dict[str, Any]] = field(default_factory=list)
    generation_notes: str = ""

    # PWS Methodology Fields (from LangExtract)
    pws_core_problem: str = ""
    pws_sub_problems: List[str] = field(default_factory=list)
    stated_assumptions: List[str] = field(default_factory=list)
    hidden_assumptions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    potential_biases: List[str] = field(default_factory=list)
    pws_quality_scores: Dict[str, int] = field(default_factory=dict)  # problem_clarity, data_grounding, assumption_awareness
    suggested_next_steps: List[str] = field(default_factory=list)

    # Quick extraction signals (from instant_extract)
    content_signals: Dict[str, Any] = field(default_factory=dict)
    coaching_hint: Optional[str] = None


@dataclass
class PDFVisualExtraction:
    """Results of PDF visual extraction."""
    page_images: List[bytes] = field(default_factory=list)
    page_count: int = 0
    extraction_method: str = ""
    error: Optional[str] = None


def extract_pdf_images(
    file_path: str,
    max_pages: int = 20,
    dpi: int = 150,
    fmt: str = "PNG"
) -> PDFVisualExtraction:
    """
    Extract PDF pages as images for Gemini multimodal analysis.

    Args:
        file_path: Path to PDF file
        max_pages: Maximum pages to extract (default 20 for context limits)
        dpi: Resolution for conversion (default 150 for balance)
        fmt: Output format (PNG recommended for quality)

    Returns:
        PDFVisualExtraction with image bytes and metadata
    """
    result = PDFVisualExtraction()

    if not PDF2IMAGE_AVAILABLE:
        result.error = "pdf2image not installed. Run: pip install pdf2image"
        result.extraction_method = "failed"
        return result

    try:
        # Convert PDF pages to images
        images = convert_from_path(
            file_path,
            dpi=dpi,
            fmt=fmt,
            first_page=1,
            last_page=max_pages
        )

        result.page_count = len(images)
        result.extraction_method = "pdf2image"

        # Convert PIL images to bytes
        for img in images:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=fmt)
            result.page_images.append(img_bytes.getvalue())

        logger.info(f"Extracted {result.page_count} pages from PDF as images")
        return result

    except Exception as e:
        result.error = str(e)
        result.extraction_method = "failed"
        logger.error(f"PDF image extraction failed: {e}")
        return result


async def analyze_claims_pws(text: str, context: str = "") -> Dict[str, Any]:
    """
    Run PWS methodology analysis on extracted presentation content.
    Uses LangExtract for structured insight extraction.

    Args:
        text: Extracted text content from presentation
        context: Additional context (user query, session info)

    Returns:
        Dict with PWS analysis results
    """
    results = {
        "instant_signals": {},
        "deep_extraction": {},
        "coaching_hint": None,
    }

    if not text or len(text) < 50:
        return results

    # 1. Run instant extraction (regex-based, <5ms)
    if LANGEXTRACT_AVAILABLE:
        results["instant_signals"] = instant_extract(text)

        # Get coaching hint based on signals
        hint = get_extraction_hint(results["instant_signals"], turn_count=1)
        results["coaching_hint"] = hint

    # 2. Run deep PWS extraction (LLM-based, async)
    if LANGEXTRACT_AVAILABLE:
        try:
            deep_results = await background_extract_pws(
                text=text[:15000],  # Limit for token context
                context=f"Presentation analysis. {context}",
                extract_type="presentation"
            )
            results["deep_extraction"] = deep_results
        except Exception as e:
            logger.error(f"Deep PWS extraction failed: {e}")
            results["deep_extraction"] = {"error": str(e)}

    return results


def merge_pws_into_claims(claims: ClaimsAnalysis, pws_results: Dict[str, Any]) -> ClaimsAnalysis:
    """
    Merge PWS extraction results into ClaimsAnalysis dataclass.

    Args:
        claims: Existing ClaimsAnalysis from visual/text extraction
        pws_results: Results from analyze_claims_pws()

    Returns:
        Enhanced ClaimsAnalysis with PWS fields populated
    """
    # Merge instant signals
    if pws_results.get("instant_signals"):
        claims.content_signals = pws_results["instant_signals"]

    # Merge coaching hint
    if pws_results.get("coaching_hint"):
        claims.coaching_hint = pws_results["coaching_hint"]

    # Merge deep extraction results
    deep = pws_results.get("deep_extraction", {})
    if deep and not deep.get("error"):
        claims.pws_core_problem = deep.get("core_problem", "")
        claims.pws_sub_problems = deep.get("sub_problems", [])
        claims.stated_assumptions = deep.get("stated_assumptions", [])
        claims.hidden_assumptions = deep.get("hidden_assumptions", [])
        claims.open_questions = deep.get("open_questions", [])
        claims.potential_biases = deep.get("potential_biases", [])
        claims.suggested_next_steps = deep.get("suggested_next_steps", [])

        # PWS quality scores
        pws_rel = deep.get("pws_relevance", {})
        if pws_rel:
            claims.pws_quality_scores = {
                "problem_clarity": pws_rel.get("problem_clarity", 0),
                "data_grounding": pws_rel.get("data_grounding", 0),
                "assumption_awareness": pws_rel.get("assumption_awareness", 0),
            }

    return claims


def get_claims_analysis_prompt() -> str:
    """Get the claims-aware analysis system prompt."""
    return """You are a Claims-Aware Presentation Analysis System. Analyze this presentation/document to:

## PRIMARY TASK
1. **Identify the Primary Thesis** - What is the main argument?
2. **Extract Key Claims** - What are the supporting arguments?
3. **Find Evidence Anchors** - What data/research supports the claims?

## EXTRACTION REQUIREMENTS
Extract ALL of the following:
- **Presenters/Authors**: Every name mentioned, with roles and affiliations
- **Research Citations**: All papers, studies, or academic references
- **Links & Resources**: Every URL, website, or external reference
- **Key Data Points**: All statistics, numbers, and metrics
- **Organizations**: Companies, institutions, universities mentioned

## OUTPUT FORMAT
Structure your response as:

### 🎯 CORE CLAIMS SUMMARY
**Primary Thesis:** [Main argument in one sentence]

**Key Supporting Claims:**
1. [First major claim]
2. [Second major claim]
3. [Third major claim]

**Critical Evidence:**
- [Key statistic or finding]
- [Essential research reference]
- [Important demonstration]

### 👥 PRESENTERS & PEOPLE
- **[Name]** - [Role] | [Organization]
[List everyone mentioned]

### 📚 RESEARCH & CITATIONS
1. [Author/Source] - "[Title or description]"
[List all academic references]

### 🔗 LINKS & RESOURCES
1. [Resource]: `[URL if visible]`
[List all URLs and external references]

### 📊 KEY DATA POINTS
- [Metric]: [Value] - [Context]
[List all important numbers]

### 📑 SLIDE-BY-SLIDE ANALYSIS
For each slide/page:
**Slide [X]: [Title]**
- **Claim Connection:** How this advances the thesis
- **Key Content:** Main points on this slide
- **Visual Elements:** Charts, diagrams, images described
- **Extraction:** Names, data, links found

### 💡 SYNTHESIS
- **Argument Flow:** How the presentation builds its case
- **Evidence Quality:** Strength of supporting data
- **Key Takeaways:** Most important insights

Be thorough. Extract EVERYTHING. Miss nothing important."""


async def analyze_presentation_with_gemini(
    images: List[bytes],
    text_content: str = "",
    additional_context: str = ""
) -> ClaimsAnalysis:
    """
    Analyze presentation using Gemini multimodal.

    Args:
        images: List of page images as bytes
        text_content: Any extracted text content
        additional_context: User-provided context

    Returns:
        ClaimsAnalysis with structured extraction
    """
    from google import genai
    from google.genai import types

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    client = genai.Client(api_key=GOOGLE_API_KEY)

    result = ClaimsAnalysis()

    try:
        # Build multimodal content
        parts = []

        # Add system prompt
        parts.append(types.Part(text=get_claims_analysis_prompt()))

        # Add images (up to 10 for context limits)
        for i, img_bytes in enumerate(images[:10]):
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
            parts.append(types.Part(text=f"[Page {i+1} shown above]"))

        # Add text content if available
        if text_content:
            parts.append(types.Part(text=f"\n\n## EXTRACTED TEXT CONTENT:\n{text_content[:20000]}"))

        # Add user context
        if additional_context:
            parts.append(types.Part(text=f"\n\n## ADDITIONAL CONTEXT FROM USER:\n{additional_context}"))

        # Final instruction
        parts.append(types.Part(text="\n\nNow analyze this presentation following the claims-aware methodology. Extract ALL information."))

        # Call Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=8000,
            )
        )

        # Parse response into structured format
        analysis_text = response.text
        result = parse_claims_analysis(analysis_text)
        result.generation_notes = f"Analyzed {len(images)} pages with Gemini multimodal"

        return result

    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        result.generation_notes = f"Analysis error: {str(e)}"
        return result


def parse_claims_analysis(text: str) -> ClaimsAnalysis:
    """
    Parse Gemini's response into structured ClaimsAnalysis.

    This is a best-effort extraction from the formatted response.
    """
    result = ClaimsAnalysis()

    lines = text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        # Detect sections
        if "Primary Thesis:" in line:
            result.primary_thesis = line.split("Primary Thesis:")[-1].strip()
        elif "Key Supporting Claims:" in line:
            current_section = "claims"
        elif "Critical Evidence:" in line:
            current_section = "evidence"
        elif "PRESENTERS" in line.upper() or "PEOPLE" in line.upper():
            current_section = "presenters"
        elif "RESEARCH" in line.upper() or "CITATIONS" in line.upper():
            current_section = "research"
        elif "LINKS" in line.upper() or "RESOURCES" in line.upper():
            current_section = "links"
        elif "DATA POINTS" in line.upper() or "KEY DATA" in line.upper():
            current_section = "data"
        elif "SLIDE-BY-SLIDE" in line.upper():
            current_section = "slides"
        elif "SYNTHESIS" in line.upper():
            current_section = None

        # Extract items based on section
        elif line.startswith(('-', '•', '*')) or (line and line[0].isdigit() and '.' in line[:3]):
            item = line.lstrip('-•* 0123456789.').strip()
            if item:
                if current_section == "claims":
                    result.key_claims.append(item)
                elif current_section == "evidence":
                    result.evidence_anchors.append(item)
                elif current_section == "presenters":
                    result.presenters.append({"raw": item})
                elif current_section == "research":
                    result.research_citations.append(item)
                elif current_section == "links":
                    result.links_resources.append(item)
                elif current_section == "data":
                    result.key_data_points.append(item)

    return result


async def analyze_presentation(
    file_path: str,
    file_name: str,
    additional_context: str = "",
    include_pws_analysis: bool = True
) -> Tuple[str, ClaimsAnalysis]:
    """
    Full presentation analysis pipeline with PWS methodology integration.

    Args:
        file_path: Path to the file
        file_name: Original filename
        additional_context: User-provided context
        include_pws_analysis: Whether to run LangExtract PWS analysis

    Returns:
        Tuple of (formatted_analysis_text, ClaimsAnalysis)
    """
    from pathlib import Path

    ext = Path(file_name).suffix.lower()

    images = []
    text_content = ""

    # Extract based on file type
    if ext == '.pdf':
        # Try visual extraction first
        visual_result = extract_pdf_images(file_path)

        if visual_result.page_images:
            images = visual_result.page_images
            logger.info(f"Extracted {len(images)} page images from PDF")

        # Also get text as backup/supplement
        from utils.file_processor import extract_text_from_pdf
        text_content, _ = extract_text_from_pdf(file_path)

    elif ext in ['.pptx', '.ppt']:
        # PowerPoint - would need python-pptx for extraction
        # For now, try to extract text
        text_content = f"[PowerPoint file: {file_name}]"

    else:
        # Unsupported
        return f"Unsupported file type for presentation analysis: {ext}", ClaimsAnalysis()

    # Run Gemini analysis for claims extraction
    if images:
        analysis = await analyze_presentation_with_gemini(images, text_content, additional_context)
    elif text_content:
        # Text-only analysis
        analysis = await analyze_presentation_with_gemini([], text_content, additional_context)
    else:
        return "Could not extract content from file", ClaimsAnalysis()

    # Run PWS methodology analysis via LangExtract
    if include_pws_analysis and text_content and LANGEXTRACT_AVAILABLE:
        try:
            pws_results = await analyze_claims_pws(text_content, additional_context)
            analysis = merge_pws_into_claims(analysis, pws_results)
            logger.info("PWS analysis merged into claims")
        except Exception as e:
            logger.error(f"PWS analysis failed: {e}")
            analysis.generation_notes += f" | PWS analysis error: {str(e)}"

    # Format output with PWS sections
    output = format_claims_analysis(analysis, file_name)

    return output, analysis


def format_claims_analysis(analysis: ClaimsAnalysis, file_name: str) -> str:
    """Format ClaimsAnalysis as readable markdown with PWS methodology sections."""

    output = f"""# 📊 Claims-Aware Analysis: {file_name}

## 🎯 CORE CLAIMS SUMMARY

**Primary Thesis:** {analysis.primary_thesis or "Not identified"}

**Key Supporting Claims:**
"""

    if analysis.key_claims:
        for i, claim in enumerate(analysis.key_claims, 1):
            output += f"{i}. {claim}\n"
    else:
        output += "- No specific claims extracted\n"

    output += "\n**Critical Evidence:**\n"
    if analysis.evidence_anchors:
        for evidence in analysis.evidence_anchors:
            output += f"- {evidence}\n"
    else:
        output += "- No specific evidence extracted\n"

    # === PWS METHODOLOGY SECTION ===
    has_pws_content = (
        analysis.pws_core_problem or
        analysis.stated_assumptions or
        analysis.hidden_assumptions or
        analysis.pws_quality_scores
    )

    if has_pws_content:
        output += "\n## 🧪 PWS METHODOLOGY ANALYSIS\n"

        if analysis.pws_core_problem:
            output += f"\n**Core Problem Identified:**\n{analysis.pws_core_problem}\n"

        if analysis.pws_sub_problems:
            output += "\n**Sub-Problems:**\n"
            for sp in analysis.pws_sub_problems:
                output += f"- {sp}\n"

        if analysis.stated_assumptions:
            output += "\n### ⚠️ STATED ASSUMPTIONS\n"
            for assumption in analysis.stated_assumptions:
                output += f"- {assumption}\n"

        if analysis.hidden_assumptions:
            output += "\n### 🔍 HIDDEN ASSUMPTIONS\n"
            for assumption in analysis.hidden_assumptions:
                output += f"- {assumption}\n"

        if analysis.potential_biases:
            output += "\n### 🎭 POTENTIAL BIASES\n"
            for bias in analysis.potential_biases:
                output += f"- {bias}\n"

        if analysis.open_questions:
            output += "\n### ❓ OPEN QUESTIONS\n"
            for question in analysis.open_questions:
                output += f"- {question}\n"

        # PWS Quality Scores
        if analysis.pws_quality_scores:
            scores = analysis.pws_quality_scores
            output += "\n### 📈 PWS QUALITY SCORES\n"
            output += f"- **Problem Clarity:** {scores.get('problem_clarity', '?')}/10\n"
            output += f"- **Data Grounding:** {scores.get('data_grounding', '?')}/10\n"
            output += f"- **Assumption Awareness:** {scores.get('assumption_awareness', '?')}/10\n"

        if analysis.suggested_next_steps:
            output += "\n### 🚀 SUGGESTED NEXT STEPS\n"
            for step in analysis.suggested_next_steps:
                output += f"- {step}\n"

        # Coaching hint (if available)
        if analysis.coaching_hint:
            output += f"\n### 💡 COACHING INSIGHT\n{analysis.coaching_hint.replace('[Coaching hint: ', '').replace(']', '')}\n"

    # Content signals summary (from instant extraction)
    if analysis.content_signals:
        signals = analysis.content_signals
        quality = signals.get("quality_signals", {})
        counts = signals.get("counts", {})

        signal_flags = []
        if quality.get("has_data"):
            signal_flags.append("📊 Data present")
        if quality.get("has_sources"):
            signal_flags.append("📚 Sources cited")
        if quality.get("has_pws_elements"):
            signal_flags.append("🎯 PWS elements")
        if quality.get("is_forward_looking"):
            signal_flags.append("🔮 Forward-looking")
        if quality.get("has_uncertainty"):
            signal_flags.append("❓ Uncertainty expressed")

        if signal_flags:
            output += f"\n**Content Signals:** {' | '.join(signal_flags)}\n"

    # === STANDARD SECTIONS ===

    # Presenters
    if analysis.presenters:
        output += "\n## 👥 PRESENTERS & PEOPLE\n"
        for person in analysis.presenters:
            if isinstance(person, dict):
                output += f"- {person.get('raw', str(person))}\n"
            else:
                output += f"- {person}\n"

    # Research
    if analysis.research_citations:
        output += "\n## 📚 RESEARCH & CITATIONS\n"
        for i, citation in enumerate(analysis.research_citations, 1):
            output += f"{i}. {citation}\n"

    # Links
    if analysis.links_resources:
        output += "\n## 🔗 LINKS & RESOURCES\n"
        for link in analysis.links_resources:
            output += f"- {link}\n"

    # Data points
    if analysis.key_data_points:
        output += "\n## 📊 KEY DATA POINTS\n"
        for data in analysis.key_data_points:
            output += f"- {data}\n"

    # Generation notes
    if analysis.generation_notes:
        output += f"\n---\n*{analysis.generation_notes}*\n"

    return output


# === Convenience function for PDF visual analysis ===

async def analyze_pdf_visually(
    file_path: str,
    prompt: str = "Analyze this document thoroughly.",
    max_pages: int = 10
) -> str:
    """
    Simple function to analyze a PDF using Gemini vision.

    Args:
        file_path: Path to PDF
        prompt: What to analyze
        max_pages: Maximum pages to process

    Returns:
        Analysis text from Gemini
    """
    from google import genai
    from google.genai import types

    # Extract images
    extraction = extract_pdf_images(file_path, max_pages=max_pages)

    if extraction.error:
        return f"Error extracting PDF: {extraction.error}"

    if not extraction.page_images:
        return "No pages could be extracted from PDF"

    # Send to Gemini
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    client = genai.Client(api_key=GOOGLE_API_KEY)

    parts = [types.Part(text=prompt)]

    for i, img_bytes in enumerate(extraction.page_images):
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
        parts.append(types.Part(text=f"[Page {i+1}]"))

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=8000,
            )
        )
        return response.text
    except Exception as e:
        return f"Analysis error: {str(e)}"
