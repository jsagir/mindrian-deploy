"""
File processing utilities for Mindrian
Handles PDF, DOCX, text file extraction, and image detection
"""

import os
from typing import Optional, Tuple
from pathlib import Path

# === Image Support Constants ===
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif'}
IMAGE_MIME_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.heic': 'image/heic',
    '.heif': 'image/heif',
}


def is_image_file(file_name: str) -> bool:
    """Check if file is a supported image type."""
    return Path(file_name).suffix.lower() in IMAGE_EXTENSIONS


def get_image_mime_type(file_name: str) -> str:
    """Get MIME type for image file."""
    return IMAGE_MIME_TYPES.get(Path(file_name).suffix.lower(), 'image/jpeg')


def extract_text_from_pdf(file_path: str, max_pages: int = 50) -> Tuple[str, dict]:
    """
    Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file
        max_pages: Maximum number of pages to extract (default 50)

    Returns:
        Tuple of (extracted_text, metadata_dict)
    """
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        num_pages = len(reader.pages)

        text_parts = []
        pages_extracted = min(num_pages, max_pages)

        for i in range(pages_extracted):
            page = reader.pages[i]
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {i+1} ---\n{page_text}")

        full_text = "\n\n".join(text_parts)

        # Truncate if too long (keep ~50k chars for context)
        if len(full_text) > 50000:
            full_text = full_text[:50000] + "\n\n[... content truncated ...]"

        metadata = {
            "type": "pdf",
            "total_pages": num_pages,
            "pages_extracted": pages_extracted,
            "char_count": len(full_text),
            "truncated": len(full_text) >= 50000
        }

        return full_text, metadata

    except Exception as e:
        return f"Error extracting PDF: {str(e)}", {"type": "pdf", "error": str(e)}


def extract_text_from_docx(file_path: str) -> Tuple[str, dict]:
    """
    Extract text content from a DOCX file.

    Args:
        file_path: Path to the DOCX file

    Returns:
        Tuple of (extracted_text, metadata_dict)
    """
    try:
        from docx import Document

        doc = Document(file_path)

        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        # Also extract from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_parts.append(row_text)

        full_text = "\n\n".join(text_parts)

        # Truncate if too long
        if len(full_text) > 50000:
            full_text = full_text[:50000] + "\n\n[... content truncated ...]"

        metadata = {
            "type": "docx",
            "paragraphs": len(doc.paragraphs),
            "tables": len(doc.tables),
            "char_count": len(full_text),
            "truncated": len(full_text) >= 50000
        }

        return full_text, metadata

    except Exception as e:
        return f"Error extracting DOCX: {str(e)}", {"type": "docx", "error": str(e)}


def extract_text_from_txt(file_path: str) -> Tuple[str, dict]:
    """
    Read text content from a plain text file.

    Args:
        file_path: Path to the text file

    Returns:
        Tuple of (text_content, metadata_dict)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Truncate if too long
        truncated = False
        if len(content) > 50000:
            content = content[:50000] + "\n\n[... content truncated ...]"
            truncated = True

        metadata = {
            "type": "text",
            "char_count": len(content),
            "line_count": content.count('\n') + 1,
            "truncated": truncated
        }

        return content, metadata

    except Exception as e:
        return f"Error reading text file: {str(e)}", {"type": "text", "error": str(e)}


def process_uploaded_file(file_path: str, file_name: str) -> Tuple[str, dict]:
    """
    Process an uploaded file and extract its text content.

    Args:
        file_path: Path to the uploaded file
        file_name: Original filename (used to determine type)

    Returns:
        Tuple of (extracted_text, metadata_dict)
    """
    ext = Path(file_name).suffix.lower()

    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext in ['.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.css']:
        return extract_text_from_txt(file_path)
    else:
        return f"Unsupported file type: {ext}", {"type": "unsupported", "extension": ext}


def format_file_context(file_name: str, content: str, metadata: dict) -> str:
    """
    Format extracted file content for inclusion in conversation context.

    Args:
        file_name: Name of the file
        content: Extracted text content
        metadata: Metadata about the extraction

    Returns:
        Formatted context string
    """
    file_type = metadata.get("type", "unknown")

    header = f"\n\n---\n**UPLOADED FILE: {file_name}**\n"

    if file_type == "pdf":
        header += f"(PDF: {metadata.get('pages_extracted', '?')}/{metadata.get('total_pages', '?')} pages, {metadata.get('char_count', 0):,} characters)\n"
    elif file_type == "docx":
        header += f"(Word Document: {metadata.get('paragraphs', '?')} paragraphs, {metadata.get('char_count', 0):,} characters)\n"
    elif file_type == "text":
        header += f"(Text file: {metadata.get('line_count', '?')} lines, {metadata.get('char_count', 0):,} characters)\n"

    # Document AI enhanced processing
    if metadata.get("method") == "document_ai":
        header += f"**Enhanced with Document AI** (confidence: {metadata.get('confidence', 0):.0%})\n"

    if metadata.get("truncated"):
        header += "**Note: Content was truncated due to length.**\n"

    if metadata.get("error"):
        return header + f"Error: {metadata['error']}\n---\n"

    # Add equations if present
    equations = metadata.get("equations", [])
    if equations:
        header += f"**{len(equations)} equations extracted (LaTeX)**\n"

    # Add tables if present
    tables = metadata.get("tables", [])
    if tables:
        header += f"**{len(tables)} tables extracted**\n"

    return header + "---\n" + content + "\n---\n"


# =============================================================================
# SMART PROCESSING WITH DOCUMENT AI FALLBACK
# =============================================================================

async def smart_process_file(
    file_path: str,
    file_name: str,
    force_document_ai: bool = False
) -> Tuple[str, dict]:
    """
    Smart file processor that uses Document AI when needed.

    Automatically falls back to Document AI for:
    - Scanned/image-only PDFs
    - Image files (JPG, PNG, etc.)
    - Documents with math equations
    - Handwritten content

    Args:
        file_path: Path to the uploaded file
        file_name: Original filename
        force_document_ai: Force Document AI processing

    Returns:
        Tuple of (extracted_text, metadata_dict)
    """
    ext = Path(file_name).suffix.lower()

    # First, try standard extraction
    content, metadata = process_uploaded_file(file_path, file_name)

    # Check if we need Document AI
    needs_enhancement = False
    reason = ""

    # Image files always need OCR
    if is_image_file(file_name):
        needs_enhancement = True
        reason = "image file requires OCR"

    # Check if PDF extraction failed or returned very little
    elif ext == '.pdf':
        if metadata.get("error") or len(content.strip()) < 100:
            needs_enhancement = True
            reason = "PDF extraction failed or minimal content (likely scanned)"

    # Check for math content
    if not needs_enhancement and content:
        try:
            from tools.document_ai import detect_math_content
            if detect_math_content(content):
                needs_enhancement = True
                reason = "math content detected - LaTeX extraction available"
        except ImportError:
            pass

    # If enhancement needed or forced, try Document AI
    if needs_enhancement or force_document_ai:
        try:
            from tools.document_ai import smart_process_document, is_document_ai_available

            if is_document_ai_available():
                # Read file content
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                # Process with Document AI
                result = await smart_process_document(
                    file_content=file_content,
                    file_name=file_name,
                    gemini_result=content if not metadata.get("error") else None,
                    force_docai=force_document_ai
                )

                if result.get("enhanced") or result.get("method") == "document_ai":
                    # Use Document AI result
                    enhanced_content = result["text"]

                    # Append equations in LaTeX format
                    if result.get("equations"):
                        from tools.document_ai import format_equations_for_display
                        enhanced_content += "\n\n" + format_equations_for_display(result["equations"])

                    # Append tables as markdown
                    if result.get("tables"):
                        from tools.document_ai import format_tables_as_markdown
                        enhanced_content += "\n\n" + format_tables_as_markdown(result["tables"])

                    enhanced_metadata = {
                        **metadata,
                        "method": "document_ai",
                        "confidence": result.get("confidence", 0),
                        "equations": result.get("equations", []),
                        "tables": result.get("tables", []),
                        "enhancement_reason": reason
                    }

                    print(f"✅ Document AI enhanced: {file_name} ({reason})")
                    return enhanced_content, enhanced_metadata

            else:
                print(f"⚠️ Document AI needed for {file_name} ({reason}) but not configured")

        except ImportError:
            print("⚠️ Document AI module not available")
        except Exception as e:
            print(f"⚠️ Document AI error: {e}")

    # Return standard extraction result
    return content, metadata


def is_document_ai_configured() -> bool:
    """Check if Document AI is available and configured."""
    try:
        from tools.document_ai import is_document_ai_available
        return is_document_ai_available()
    except ImportError:
        return False
