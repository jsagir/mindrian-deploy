"""
Document AI Integration for Mindrian
Fallback processor for difficult documents that Gemini can't handle well:
- Scanned/image-only PDFs
- Math equations (LaTeX extraction)
- Handwritten notes

Only used when standard processing fails or specific features needed.
"""

import os
from typing import Optional, Dict, Any, List, Tuple
import io

# Check if Document AI is available
DOCUMENT_AI_AVAILABLE = False
try:
    from google.cloud import documentai_v1 as documentai
    DOCUMENT_AI_AVAILABLE = True
except ImportError:
    pass

# Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us")
DOCAI_PROCESSOR_ID = os.getenv("DOCAI_PROCESSOR_ID")

# Check if fully configured
DOCUMENT_AI_CONFIGURED = all([
    DOCUMENT_AI_AVAILABLE,
    GCP_PROJECT_ID,
    DOCAI_PROCESSOR_ID
])


def is_document_ai_available() -> bool:
    """Check if Document AI is available and configured."""
    return DOCUMENT_AI_CONFIGURED


def detect_document_needs_docai(
    file_content: bytes,
    file_name: str,
    gemini_extraction_failed: bool = False,
    has_math: bool = False,
    is_handwritten: bool = False
) -> Tuple[bool, str]:
    """
    Detect if a document needs Document AI processing.

    Returns:
        (needs_docai: bool, reason: str)
    """
    reasons = []

    # Check file type
    file_lower = file_name.lower()
    is_image = any(file_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.webp'])

    # Image files always need OCR
    if is_image:
        reasons.append("image file needs OCR")

    # Explicit flags
    if gemini_extraction_failed:
        reasons.append("Gemini extraction failed (likely scanned PDF)")

    if has_math:
        reasons.append("math equations detected - need LaTeX extraction")

    if is_handwritten:
        reasons.append("handwritten content detected")

    # Check if PDF might be scanned (image-only)
    if file_lower.endswith('.pdf'):
        if _is_likely_scanned_pdf(file_content):
            reasons.append("scanned/image-only PDF detected")

    needs_docai = len(reasons) > 0
    reason = "; ".join(reasons) if reasons else "standard processing sufficient"

    return needs_docai, reason


def _is_likely_scanned_pdf(content: bytes) -> bool:
    """
    Heuristic to detect if PDF is likely scanned (image-only).

    Scanned PDFs typically have:
    - Very little extractable text
    - Large file size relative to page count
    - Image streams but no text streams
    """
    try:
        # Quick check: look for text markers in PDF
        content_str = content[:50000].decode('latin-1', errors='ignore')

        # Count text stream markers vs image markers
        text_markers = content_str.count('/Type /Font') + content_str.count('BT') + content_str.count('Tj')
        image_markers = content_str.count('/Subtype /Image') + content_str.count('/XObject')

        # If very few text markers but images present, likely scanned
        if image_markers > 0 and text_markers < 5:
            return True

        # If file is large (>1MB) with few text markers, likely scanned
        if len(content) > 1_000_000 and text_markers < 20:
            return True

        return False
    except Exception:
        return False


def detect_math_content(text: str) -> bool:
    """
    Detect if text likely contains math equations.

    Looks for patterns that suggest mathematical content.
    """
    import re

    math_patterns = [
        r'\b(equation|formula|theorem|proof|lemma)\b',
        r'[∫∑∏√∞±×÷≠≤≥≈∈∉⊂⊃∪∩]',  # Math symbols
        r'\b\d+\s*[+\-*/^]\s*\d+',  # Basic operations
        r'[a-z]\s*=\s*[a-z0-9+\-*/^()]+',  # Algebraic expressions
        r'\b(sin|cos|tan|log|ln|exp|lim|sum|int)\b',  # Functions
        r'[α-ωΑ-Ω]',  # Greek letters
        r'\^\{?\d+\}?',  # Exponents
        r'_\{?\d+\}?',  # Subscripts
        r'\\frac\{',  # LaTeX fractions
    ]

    for pattern in math_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


async def process_with_document_ai(
    file_content: bytes,
    mime_type: str = "application/pdf",
    enable_math_ocr: bool = False,
    enable_handwriting: bool = True
) -> Dict[str, Any]:
    """
    Process document with Google Document AI.

    Args:
        file_content: Raw file bytes
        mime_type: MIME type of the document
        enable_math_ocr: Enable LaTeX extraction for equations
        enable_handwriting: Enable handwriting recognition

    Returns:
        {
            "text": str,              # Full extracted text
            "pages": list,            # Per-page content
            "equations": list,        # LaTeX equations (if math_ocr enabled)
            "tables": list,           # Extracted tables
            "handwritten_blocks": list,  # Handwritten text blocks
            "confidence": float,      # Overall OCR confidence
            "method": "document_ai"
        }
    """
    if not DOCUMENT_AI_CONFIGURED:
        return {
            "text": "",
            "error": "Document AI not configured. Set GCP_PROJECT_ID and DOCAI_PROCESSOR_ID.",
            "method": "document_ai_unavailable"
        }

    try:
        client = documentai.DocumentProcessorServiceClient()

        # Build processor name
        processor_name = f"projects/{GCP_PROJECT_ID}/locations/{GCP_LOCATION}/processors/{DOCAI_PROCESSOR_ID}"

        # Configure processing options
        ocr_config = documentai.OcrConfig(
            enable_native_pdf_parsing=True,
        )

        # Add premium features if requested
        if enable_math_ocr:
            ocr_config.premium_features = documentai.OcrConfig.PremiumFeatures(
                enable_math_ocr=True
            )

        process_options = documentai.ProcessOptions(
            ocr_config=ocr_config
        )

        # Create request
        request = documentai.ProcessRequest(
            name=processor_name,
            raw_document=documentai.RawDocument(
                content=file_content,
                mime_type=mime_type
            ),
            process_options=process_options
        )

        # Process document
        result = client.process_document(request=request)
        document = result.document

        # Extract results
        extracted = {
            "text": document.text,
            "pages": _extract_pages(document),
            "equations": _extract_equations(document) if enable_math_ocr else [],
            "tables": _extract_tables(document),
            "handwritten_blocks": _extract_handwritten(document) if enable_handwriting else [],
            "confidence": _calculate_confidence(document),
            "method": "document_ai"
        }

        print(f"✅ Document AI processed: {len(document.text)} chars, confidence: {extracted['confidence']:.2f}")

        return extracted

    except Exception as e:
        print(f"⚠️ Document AI error: {e}")
        return {
            "text": "",
            "error": str(e),
            "method": "document_ai_error"
        }


def _extract_pages(document) -> List[Dict]:
    """Extract per-page content."""
    pages = []

    for page in document.pages:
        page_text = _get_text_from_layout(page.layout, document.text)

        pages.append({
            "page_number": page.page_number,
            "text": page_text,
            "width": page.dimension.width if page.dimension else 0,
            "height": page.dimension.height if page.dimension else 0,
        })

    return pages


def _extract_equations(document) -> List[Dict]:
    """Extract math equations as LaTeX."""
    equations = []

    for page in document.pages:
        if hasattr(page, 'math_formulas'):
            for formula in page.math_formulas:
                equations.append({
                    "latex": formula.detected_latex if hasattr(formula, 'detected_latex') else "",
                    "confidence": formula.confidence if hasattr(formula, 'confidence') else 0,
                    "page": page.page_number,
                })

    return equations


def _extract_tables(document) -> List[Dict]:
    """Extract tables as structured data."""
    tables = []

    for page in document.pages:
        if hasattr(page, 'tables'):
            for table in page.tables:
                rows = []
                headers = []

                # Extract headers
                if hasattr(table, 'header_rows'):
                    for row in table.header_rows:
                        headers = [_get_cell_text(cell, document.text) for cell in row.cells]

                # Extract body rows
                if hasattr(table, 'body_rows'):
                    for row in table.body_rows:
                        row_data = [_get_cell_text(cell, document.text) for cell in row.cells]
                        rows.append(row_data)

                tables.append({
                    "headers": headers,
                    "rows": rows,
                    "page": page.page_number
                })

    return tables


def _extract_handwritten(document) -> List[Dict]:
    """Extract handwritten text blocks."""
    handwritten = []

    for page in document.pages:
        if hasattr(page, 'blocks'):
            for block in page.blocks:
                # Check if block is handwritten
                if hasattr(block, 'detected_break'):
                    text = _get_text_from_layout(block.layout, document.text)
                    # Heuristic: handwritten text often has lower confidence
                    if block.layout.confidence < 0.9:
                        handwritten.append({
                            "text": text,
                            "confidence": block.layout.confidence,
                            "page": page.page_number
                        })

    return handwritten


def _get_text_from_layout(layout, full_text: str) -> str:
    """Extract text from a layout element."""
    if not hasattr(layout, 'text_anchor') or not layout.text_anchor.text_segments:
        return ""

    text_parts = []
    for segment in layout.text_anchor.text_segments:
        start = int(segment.start_index) if segment.start_index else 0
        end = int(segment.end_index) if segment.end_index else len(full_text)
        text_parts.append(full_text[start:end])

    return "".join(text_parts)


def _get_cell_text(cell, full_text: str) -> str:
    """Extract text from a table cell."""
    return _get_text_from_layout(cell.layout, full_text).strip()


def _calculate_confidence(document) -> float:
    """Calculate overall OCR confidence."""
    confidences = []

    for page in document.pages:
        if hasattr(page, 'blocks'):
            for block in page.blocks:
                if hasattr(block.layout, 'confidence'):
                    confidences.append(block.layout.confidence)

    return sum(confidences) / len(confidences) if confidences else 0.0


def format_equations_for_display(equations: List[Dict]) -> str:
    """Format extracted equations for markdown display."""
    if not equations:
        return ""

    lines = ["## Extracted Equations\n"]

    for i, eq in enumerate(equations, 1):
        latex = eq.get("latex", "")
        confidence = eq.get("confidence", 0)
        page = eq.get("page", "?")

        # Format as display math
        lines.append(f"**Equation {i}** (page {page}, confidence: {confidence:.0%})")
        lines.append(f"$$\n{latex}\n$$\n")

    return "\n".join(lines)


def format_tables_as_markdown(tables: List[Dict]) -> str:
    """Format extracted tables as markdown."""
    if not tables:
        return ""

    lines = ["## Extracted Tables\n"]

    for i, table in enumerate(tables, 1):
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        page = table.get("page", "?")

        lines.append(f"**Table {i}** (page {page})\n")

        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in rows:
            lines.append("| " + " | ".join(row) + " |")

        lines.append("")

    return "\n".join(lines)


# =============================================================================
# SMART PROCESSOR - Chooses best method automatically
# =============================================================================

async def smart_process_document(
    file_content: bytes,
    file_name: str,
    mime_type: str = None,
    gemini_result: str = None,
    force_docai: bool = False
) -> Dict[str, Any]:
    """
    Smart document processor that uses Document AI only when needed.

    1. Checks if document needs Document AI
    2. Falls back to Document AI for scans, math, handwriting
    3. Returns enhanced results when Document AI is used

    Args:
        file_content: Raw file bytes
        file_name: Original filename
        mime_type: MIME type (auto-detected if None)
        gemini_result: Result from Gemini extraction (to detect failures)
        force_docai: Force Document AI processing

    Returns:
        {
            "text": str,
            "method": "gemini" | "document_ai",
            "equations": list (if any),
            "tables": list (if any),
            "enhanced": bool
        }
    """
    # Auto-detect mime type
    if mime_type is None:
        mime_type = _detect_mime_type(file_name)

    # Check if Gemini extraction was weak
    gemini_failed = gemini_result is not None and len(gemini_result.strip()) < 100

    # Detect if we have math content in any existing text
    has_math = gemini_result and detect_math_content(gemini_result)

    # Decide if Document AI is needed
    needs_docai, reason = detect_document_needs_docai(
        file_content=file_content,
        file_name=file_name,
        gemini_extraction_failed=gemini_failed,
        has_math=has_math
    )

    if force_docai:
        needs_docai = True
        reason = "forced by user"

    # If Document AI not needed, return Gemini result
    if not needs_docai:
        return {
            "text": gemini_result or "",
            "method": "gemini",
            "equations": [],
            "tables": [],
            "enhanced": False,
            "reason": reason
        }

    # Check if Document AI is available
    if not DOCUMENT_AI_CONFIGURED:
        print(f"⚠️ Document AI needed ({reason}) but not configured")
        return {
            "text": gemini_result or "",
            "method": "gemini_fallback",
            "equations": [],
            "tables": [],
            "enhanced": False,
            "reason": f"Document AI needed ({reason}) but not configured"
        }

    print(f"📄 Using Document AI: {reason}")

    # Process with Document AI
    result = await process_with_document_ai(
        file_content=file_content,
        mime_type=mime_type,
        enable_math_ocr=has_math,
        enable_handwriting=True
    )

    if result.get("error"):
        # Fall back to Gemini result on error
        return {
            "text": gemini_result or "",
            "method": "gemini_fallback",
            "equations": [],
            "tables": [],
            "enhanced": False,
            "reason": f"Document AI error: {result['error']}"
        }

    return {
        "text": result["text"],
        "method": "document_ai",
        "equations": result.get("equations", []),
        "tables": result.get("tables", []),
        "handwritten": result.get("handwritten_blocks", []),
        "confidence": result.get("confidence", 0),
        "enhanced": True,
        "reason": reason
    }


def _detect_mime_type(file_name: str) -> str:
    """Detect MIME type from filename."""
    ext = file_name.lower().split('.')[-1]

    mime_map = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
    }

    return mime_map.get(ext, 'application/pdf')
