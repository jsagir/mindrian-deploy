"""
Claude Document Processing for Mindrian
========================================

Uses Claude's vision capabilities for high-accuracy document extraction:
- Handwriting recognition
- Math equation extraction (LaTeX)
- Scanned/image PDFs
- Tables and charts

Requires: ANTHROPIC_API_KEY environment variable
"""

import os
import base64
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

# Check if Claude is available
CLAUDE_AVAILABLE = False
CLAUDE_CLIENT = None

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    pass

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_CONFIGURED = CLAUDE_AVAILABLE and bool(ANTHROPIC_API_KEY)

# Model for document processing (vision-capable)
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Best balance of speed/accuracy for docs


def is_claude_doc_available() -> bool:
    """Check if Claude document processing is available."""
    return CLAUDE_CONFIGURED


def _get_client():
    """Get or create Anthropic client."""
    global CLAUDE_CLIENT
    if CLAUDE_CLIENT is None and CLAUDE_CONFIGURED:
        CLAUDE_CLIENT = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return CLAUDE_CLIENT


def _convert_pdf_to_images(pdf_path: str, max_pages: int = 20) -> List[Tuple[bytes, str]]:
    """
    Convert PDF pages to images for Claude vision.

    Returns:
        List of (image_bytes, mime_type) tuples
    """
    try:
        from pdf2image import convert_from_path
        import io

        # Convert PDF to images (PNG for best quality)
        images = convert_from_path(
            pdf_path,
            dpi=150,  # Balance quality vs size
            first_page=1,
            last_page=max_pages,
            fmt='png'
        )

        result = []
        for img in images:
            # Convert PIL image to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            result.append((buffer.getvalue(), 'image/png'))

        return result

    except Exception as e:
        print(f"⚠️ PDF to image conversion failed: {e}")
        return []


def _convert_image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.standard_b64encode(image_bytes).decode('utf-8')


async def process_document_with_claude(
    file_path: str,
    file_name: str,
    extract_equations: bool = True,
    extract_handwriting: bool = True,
    max_pages: int = 20
) -> Dict[str, Any]:
    """
    Process document using Claude's vision capabilities.

    Args:
        file_path: Path to the file
        file_name: Original filename
        extract_equations: Extract math as LaTeX
        extract_handwriting: Note handwritten content
        max_pages: Maximum pages to process

    Returns:
        {
            "text": str,              # Full extracted text
            "equations": list,        # LaTeX equations
            "tables": list,           # Extracted tables
            "handwriting_notes": str, # Notes about handwritten content
            "confidence": str,        # Quality assessment
            "method": "claude"
        }
    """
    if not CLAUDE_CONFIGURED:
        return {
            "text": "",
            "error": "Claude not configured. Set ANTHROPIC_API_KEY environment variable.",
            "method": "claude_unavailable"
        }

    try:
        client = _get_client()
        file_ext = Path(file_name).suffix.lower()

        # Prepare image content for Claude
        image_content = []

        if file_ext == '.pdf':
            # Convert PDF pages to images
            print(f"📄 Converting PDF to images for Claude analysis...")
            page_images = _convert_pdf_to_images(file_path, max_pages)

            if not page_images:
                return {
                    "text": "",
                    "error": "Failed to convert PDF to images. Install poppler-utils.",
                    "method": "claude_error"
                }

            for i, (img_bytes, mime_type) in enumerate(page_images):
                image_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": _convert_image_to_base64(img_bytes)
                    }
                })
                # Add page separator in text
                image_content.append({
                    "type": "text",
                    "text": f"\n--- Page {i+1} ---\n"
                })

        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Direct image processing
            with open(file_path, 'rb') as f:
                img_bytes = f.read()

            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_map.get(file_ext, 'image/jpeg')

            image_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": _convert_image_to_base64(img_bytes)
                }
            })
        else:
            return {
                "text": "",
                "error": f"Unsupported file type for Claude vision: {file_ext}",
                "method": "claude_unsupported"
            }

        # Build extraction prompt
        extraction_instructions = []
        extraction_instructions.append("Extract ALL text from this document accurately.")

        if extract_handwriting:
            extraction_instructions.append("Pay special attention to handwritten text - transcribe it carefully.")

        if extract_equations:
            extraction_instructions.append(
                "For any mathematical equations or formulas, output them in LaTeX format "
                "enclosed in $$ delimiters (e.g., $$E = mc^2$$)."
            )

        extraction_instructions.append(
            "For tables, preserve their structure using markdown table format."
        )
        extraction_instructions.append(
            "At the end, add a brief note about document quality and any handwritten sections found."
        )

        prompt = "\n".join(extraction_instructions)

        # Add the extraction prompt
        image_content.append({
            "type": "text",
            "text": prompt
        })

        print(f"🤖 Sending {len([c for c in image_content if c['type'] == 'image'])} page(s) to Claude...")

        # Call Claude
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            messages=[{
                "role": "user",
                "content": image_content
            }]
        )

        extracted_text = response.content[0].text

        # Parse out equations if present
        equations = []
        if extract_equations:
            import re
            latex_pattern = r'\$\$(.*?)\$\$'
            matches = re.findall(latex_pattern, extracted_text, re.DOTALL)
            equations = [{"latex": eq.strip(), "confidence": 0.95} for eq in matches]

        # Estimate confidence based on response
        confidence = "high"
        if "unclear" in extracted_text.lower() or "illegible" in extracted_text.lower():
            confidence = "medium"
        if "cannot read" in extracted_text.lower():
            confidence = "low"

        print(f"✅ Claude extracted {len(extracted_text)} chars, {len(equations)} equations")

        return {
            "text": extracted_text,
            "equations": equations,
            "tables": [],  # Tables are inline in the text as markdown
            "confidence": confidence,
            "pages_processed": len([c for c in image_content if c['type'] == 'image']),
            "method": "claude"
        }

    except anthropic.APIError as e:
        print(f"⚠️ Claude API error: {e}")
        return {
            "text": "",
            "error": f"Claude API error: {str(e)}",
            "method": "claude_error"
        }
    except Exception as e:
        print(f"⚠️ Claude processing error: {e}")
        return {
            "text": "",
            "error": str(e),
            "method": "claude_error"
        }


# Synchronous wrapper for non-async contexts
def process_document_with_claude_sync(
    file_path: str,
    file_name: str,
    **kwargs
) -> Dict[str, Any]:
    """Synchronous wrapper for Claude document processing."""
    return asyncio.run(process_document_with_claude(file_path, file_name, **kwargs))
