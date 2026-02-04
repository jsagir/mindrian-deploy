"""
Smart Document Processing for Mindrian
=======================================

Multi-model document extraction with intelligent fallback:
1. Gemini 2.5 Flash (FREE - 15 req/min, 1M tokens/min)
2. Gemini 2.5 Pro (2 req/min, 32K tokens/min)
3. Claude Sonnet (PAID - last resort)
4. PyPDF2 (basic fallback)

Supports:
- Handwriting recognition
- Math equation extraction (LaTeX)
- Scanned/image PDFs
- Tables and charts
"""

import os
import base64
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Models in priority order
GEMINI_FLASH = "gemini-2.5-flash-preview-05-20"
GEMINI_PRO = "gemini-2.5-pro-preview-05-06"
CLAUDE_SONNET = "claude-sonnet-4-20250514"


def is_smart_doc_available() -> bool:
    """Check if smart document processing is available."""
    return bool(GOOGLE_API_KEY)  # At minimum need Gemini


# =============================================================================
# PDF TO IMAGES CONVERSION
# =============================================================================

def _convert_pdf_to_images(pdf_path: str, max_pages: int = 20, dpi: int = 150) -> List[Tuple[bytes, str]]:
    """
    Convert PDF pages to images for vision models.

    Returns:
        List of (image_bytes, mime_type) tuples
    """
    try:
        from pdf2image import convert_from_path
        import io

        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=1,
            last_page=max_pages,
            fmt='png'
        )

        result = []
        for img in images:
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            result.append((buffer.getvalue(), 'image/png'))

        return result

    except Exception as e:
        print(f"⚠️ PDF to image conversion failed: {e}")
        return []


def _image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.standard_b64encode(image_bytes).decode('utf-8')


# =============================================================================
# GEMINI DOCUMENT PROCESSING
# =============================================================================

async def _process_with_gemini(
    file_path: str,
    file_name: str,
    model: str = GEMINI_FLASH,
    max_pages: int = 20
) -> Dict[str, Any]:
    """
    Process document using Gemini Vision API.

    Args:
        file_path: Path to file
        file_name: Original filename
        model: Gemini model to use
        max_pages: Max pages for PDFs

    Returns:
        {text, equations, confidence, method, error}
    """
    if not GOOGLE_API_KEY:
        return {"text": "", "error": "GOOGLE_API_KEY not set", "method": "gemini_unavailable"}

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GOOGLE_API_KEY)
        file_ext = Path(file_name).suffix.lower()

        # Build content parts
        content_parts = []

        if file_ext == '.pdf':
            # Convert PDF to images
            print(f"📄 Converting PDF to images for {model}...")
            page_images = _convert_pdf_to_images(file_path, max_pages)

            if not page_images:
                return {"text": "", "error": "PDF to image conversion failed", "method": "gemini_error"}

            for i, (img_bytes, mime_type) in enumerate(page_images):
                content_parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
                content_parts.append(types.Part.from_text(text=f"\n--- Page {i+1} ---\n"))

        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Direct image
            with open(file_path, 'rb') as f:
                img_bytes = f.read()

            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                       '.gif': 'image/gif', '.webp': 'image/webp'}
            mime_type = mime_map.get(file_ext, 'image/jpeg')
            content_parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
        else:
            return {"text": "", "error": f"Unsupported file type: {file_ext}", "method": "gemini_unsupported"}

        # Add extraction prompt
        extraction_prompt = """Extract ALL text from this document accurately.

Instructions:
1. Transcribe all printed and handwritten text
2. For mathematical equations, output them in LaTeX format with $$ delimiters (e.g., $$E = mc^2$$)
3. Preserve table structure using markdown format
4. Note any sections that are unclear or illegible
5. Maintain the logical reading order

Output the complete text content:"""

        content_parts.append(types.Part.from_text(text=extraction_prompt))

        print(f"🤖 Sending to {model}...")

        # Call Gemini
        response = client.models.generate_content(
            model=model,
            contents=content_parts,
            config=types.GenerateContentConfig(
                max_output_tokens=16000,
                temperature=0.1,  # Low temp for accuracy
            )
        )

        extracted_text = response.text

        # Parse equations
        equations = []
        import re
        latex_matches = re.findall(r'\$\$(.*?)\$\$', extracted_text, re.DOTALL)
        equations = [{"latex": eq.strip(), "confidence": 0.9} for eq in latex_matches]

        # Estimate confidence
        confidence = "high"
        if "unclear" in extracted_text.lower() or "illegible" in extracted_text.lower():
            confidence = "medium"
        if "cannot read" in extracted_text.lower() or len(extracted_text) < 100:
            confidence = "low"

        model_short = "flash" if "flash" in model.lower() else "pro"
        print(f"✅ Gemini {model_short}: {len(extracted_text)} chars, {len(equations)} equations")

        return {
            "text": extracted_text,
            "equations": equations,
            "confidence": confidence,
            "pages_processed": len([p for p in content_parts if hasattr(p, '_pb') and p._pb.inline_data.mime_type.startswith('image/')]) if content_parts else 0,
            "method": f"gemini_{model_short}"
        }

    except Exception as e:
        error_str = str(e)
        print(f"⚠️ Gemini {model} error: {error_str}")

        # Check for rate limit
        if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
            return {"text": "", "error": f"Rate limited: {error_str}", "method": "gemini_rate_limited"}

        return {"text": "", "error": error_str, "method": "gemini_error"}


# =============================================================================
# CLAUDE DOCUMENT PROCESSING (FALLBACK)
# =============================================================================

async def _process_with_claude(
    file_path: str,
    file_name: str,
    max_pages: int = 20
) -> Dict[str, Any]:
    """
    Process document using Claude Vision (fallback).
    """
    if not ANTHROPIC_API_KEY:
        return {"text": "", "error": "ANTHROPIC_API_KEY not set", "method": "claude_unavailable"}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        file_ext = Path(file_name).suffix.lower()

        # Build image content
        image_content = []

        if file_ext == '.pdf':
            print(f"📄 Converting PDF to images for Claude...")
            page_images = _convert_pdf_to_images(file_path, max_pages)

            if not page_images:
                return {"text": "", "error": "PDF to image conversion failed", "method": "claude_error"}

            for i, (img_bytes, mime_type) in enumerate(page_images):
                image_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": _image_to_base64(img_bytes)
                    }
                })
                image_content.append({"type": "text", "text": f"\n--- Page {i+1} ---\n"})

        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            with open(file_path, 'rb') as f:
                img_bytes = f.read()

            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                       '.gif': 'image/gif', '.webp': 'image/webp'}
            mime_type = mime_map.get(file_ext, 'image/jpeg')

            image_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": _image_to_base64(img_bytes)
                }
            })
        else:
            return {"text": "", "error": f"Unsupported file type: {file_ext}", "method": "claude_unsupported"}

        # Add extraction prompt
        image_content.append({
            "type": "text",
            "text": """Extract ALL text from this document accurately.

Instructions:
1. Transcribe all printed and handwritten text carefully
2. For mathematical equations, output them in LaTeX format with $$ delimiters
3. Preserve table structure using markdown format
4. Note any unclear or illegible sections

Output the complete text content:"""
        })

        print(f"🤖 Sending to Claude (fallback)...")

        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=16000,
            messages=[{"role": "user", "content": image_content}]
        )

        extracted_text = response.content[0].text

        # Parse equations
        import re
        equations = []
        latex_matches = re.findall(r'\$\$(.*?)\$\$', extracted_text, re.DOTALL)
        equations = [{"latex": eq.strip(), "confidence": 0.95} for eq in latex_matches]

        confidence = "high"
        if "unclear" in extracted_text.lower():
            confidence = "medium"

        print(f"✅ Claude: {len(extracted_text)} chars, {len(equations)} equations")

        return {
            "text": extracted_text,
            "equations": equations,
            "confidence": confidence,
            "method": "claude"
        }

    except Exception as e:
        print(f"⚠️ Claude error: {e}")
        return {"text": "", "error": str(e), "method": "claude_error"}


# =============================================================================
# PYPDF2 FALLBACK
# =============================================================================

def _process_with_pypdf2(file_path: str, max_pages: int = 50) -> Dict[str, Any]:
    """Basic PDF text extraction with PyPDF2."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        text_parts = []

        for i, page in enumerate(reader.pages[:max_pages]):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"--- Page {i+1} ---\n{page_text}")

        content = "\n\n".join(text_parts)

        if len(content) > 100000:
            content = content[:100000] + "\n\n[... truncated ...]"

        print(f"📄 PyPDF2: {len(content)} chars (basic extraction)")

        return {
            "text": content,
            "equations": [],
            "confidence": "low" if len(content) < 500 else "medium",
            "pages_processed": min(len(reader.pages), max_pages),
            "method": "pypdf2"
        }

    except Exception as e:
        print(f"⚠️ PyPDF2 error: {e}")
        return {"text": "", "error": str(e), "method": "pypdf2_error"}


# =============================================================================
# SMART DOCUMENT PROCESSOR (MAIN ENTRY POINT)
# =============================================================================

async def process_document_smart(
    file_path: str,
    file_name: str,
    extract_equations: bool = True,
    extract_handwriting: bool = True,
    max_pages: int = 20
) -> Dict[str, Any]:
    """
    Smart document processor with multi-model fallback.

    Priority:
    1. Gemini 2.5 Flash (FREE - 15 req/min)
    2. Gemini 2.5 Pro (2 req/min)
    3. Claude Sonnet (PAID)
    4. PyPDF2 (basic)

    Args:
        file_path: Path to the file
        file_name: Original filename
        extract_equations: Extract math as LaTeX
        extract_handwriting: Note handwritten content
        max_pages: Maximum pages to process

    Returns:
        {text, equations, confidence, method, error}
    """
    file_ext = Path(file_name).suffix.lower()

    # For non-PDF/image files, use PyPDF2 directly
    if file_ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return _process_with_pypdf2(file_path, max_pages) if file_ext == '.pdf' else {
            "text": "",
            "error": f"Use standard extractor for {file_ext}",
            "method": "unsupported"
        }

    print(f"\n{'='*50}")
    print(f"📄 Smart Document Processing: {file_name}")
    print(f"{'='*50}")

    # 1. Try Gemini Flash (FREE)
    print("\n[1/4] Trying Gemini 2.5 Flash (free tier)...")
    result = await _process_with_gemini(file_path, file_name, GEMINI_FLASH, max_pages)

    if result.get("text") and not result.get("error"):
        return result

    if "rate" in result.get("error", "").lower():
        print("⚠️ Flash rate limited, trying Pro...")
    else:
        print(f"⚠️ Flash failed: {result.get('error', 'unknown')}")

    # 2. Try Gemini Pro
    print("\n[2/4] Trying Gemini 2.5 Pro...")
    result = await _process_with_gemini(file_path, file_name, GEMINI_PRO, max_pages)

    if result.get("text") and not result.get("error"):
        return result

    print(f"⚠️ Pro failed: {result.get('error', 'unknown')}")

    # 3. Try Claude (PAID fallback)
    if ANTHROPIC_API_KEY:
        print("\n[3/4] Trying Claude Sonnet (paid fallback)...")
        result = await _process_with_claude(file_path, file_name, max_pages)

        if result.get("text") and not result.get("error"):
            return result

        print(f"⚠️ Claude failed: {result.get('error', 'unknown')}")
    else:
        print("\n[3/4] Claude skipped (ANTHROPIC_API_KEY not set)")

    # 4. PyPDF2 basic fallback
    print("\n[4/4] Falling back to PyPDF2 (basic extraction)...")
    if file_ext == '.pdf':
        return _process_with_pypdf2(file_path, max_pages)

    return {
        "text": "",
        "error": "All extraction methods failed",
        "method": "all_failed"
    }


# Synchronous wrapper
def process_document_smart_sync(file_path: str, file_name: str, **kwargs) -> Dict[str, Any]:
    """Synchronous wrapper for smart document processing."""
    return asyncio.run(process_document_smart(file_path, file_name, **kwargs))
