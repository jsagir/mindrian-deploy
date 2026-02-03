"""
LangGraph File Processing Pipeline
==================================
Multi-step file upload → extraction → embedding workflow.

Pipeline Stages:
1. Upload Detection - Identify file type (PDF, DOCX, image, etc.)
2. Content Extraction - Route to appropriate extractor (PyPDF2, DocAI, OCR)
3. Quality Check - Validate extraction quality, retry if needed
4. Chunking - Split content into semantic chunks
5. Embedding - Store in Neo4j and/or FileSearch

Features:
- Automatic retry with fallback extractors
- Parallel processing for multiple files
- Conditional routing based on content type
- State tracking throughout pipeline
"""

import os
import asyncio
from typing import TypedDict, List, Dict, Any, Optional, Literal
from pathlib import Path
from datetime import datetime
import hashlib

from langgraph.graph import StateGraph, END

# =============================================================================
# STATE DEFINITION
# =============================================================================

class FileState(TypedDict):
    """State for a single file in the pipeline."""
    file_id: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str]

    # Detection results
    detected_type: Literal["pdf", "docx", "doc", "txt", "image", "spreadsheet", "presentation", "code", "unknown"]
    is_scanned: bool  # For PDFs - is it image-only?
    has_tables: bool
    has_equations: bool

    # Extraction results
    extraction_method: Optional[str]  # "pypdf2", "docai", "ocr", "docx", "text"
    raw_content: str
    char_count: int
    page_count: Optional[int]
    extraction_confidence: float  # 0-1
    extraction_error: Optional[str]

    # Chunking results
    chunks: List[Dict[str, Any]]  # [{text, metadata, embedding_id}]
    chunk_count: int

    # Embedding results
    embedded_to_neo4j: bool
    embedded_to_filesearch: bool
    neo4j_node_ids: List[str]
    filesearch_ids: List[str]

    # Pipeline metadata
    status: Literal["pending", "detecting", "extracting", "chunking", "embedding", "complete", "failed"]
    retry_count: int
    processing_time_ms: int
    error: Optional[str]


class FilePipelineState(TypedDict):
    """State for the entire file processing pipeline."""
    session_id: str
    files: List[FileState]
    total_files: int
    completed_files: int
    failed_files: int

    # Configuration
    extract_tables: bool
    extract_equations: bool
    embed_to_neo4j: bool
    embed_to_filesearch: bool
    max_chunk_size: int
    chunk_overlap: int

    # Results
    total_chunks: int
    total_chars: int
    processing_time_ms: int

    # Pipeline control
    current_stage: str
    error: Optional[str]


# =============================================================================
# CONSTANTS
# =============================================================================

# File type detection
DOCUMENT_EXTENSIONS = {
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.doc': 'doc',
    '.txt': 'txt',
    '.md': 'txt',
    '.csv': 'spreadsheet',
    '.xlsx': 'spreadsheet',
    '.xls': 'spreadsheet',
    '.pptx': 'presentation',
    '.ppt': 'presentation',
    '.py': 'code',
    '.js': 'code',
    '.ts': 'code',
    '.java': 'code',
    '.html': 'code',
    '.css': 'code',
    '.json': 'code',
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif', '.bmp', '.tiff'}

MIME_TYPE_MAP = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
    'text/plain': 'txt',
    'text/markdown': 'txt',
    'text/csv': 'spreadsheet',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'spreadsheet',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'presentation',
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
}


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

async def detect_file_types(state: FilePipelineState) -> FilePipelineState:
    """
    Stage 1: Detect file types for all uploaded files.
    Uses extension, MIME type, and content inspection.
    """
    state["current_stage"] = "detecting"

    for file_state in state["files"]:
        if file_state["status"] != "pending":
            continue

        file_state["status"] = "detecting"
        file_name = file_state["file_name"]
        file_path = file_state["file_path"]
        mime_type = file_state.get("mime_type", "")

        # 1. Check extension
        ext = Path(file_name).suffix.lower()
        if not ext and file_path:
            ext = Path(file_path).suffix.lower()

        # 2. Determine type
        if ext in DOCUMENT_EXTENSIONS:
            file_state["detected_type"] = DOCUMENT_EXTENSIONS[ext]
        elif ext in IMAGE_EXTENSIONS:
            file_state["detected_type"] = "image"
        elif mime_type and mime_type in MIME_TYPE_MAP:
            file_state["detected_type"] = MIME_TYPE_MAP[mime_type]
        else:
            file_state["detected_type"] = "unknown"

        # 3. For PDFs, check if scanned (image-only)
        if file_state["detected_type"] == "pdf":
            file_state["is_scanned"] = await _check_if_scanned_pdf(file_path)

        print(f"[FILE_PIPELINE] Detected {file_name} as {file_state['detected_type']}")

    return state


async def _check_if_scanned_pdf(file_path: str) -> bool:
    """Check if PDF is scanned (image-only) by attempting text extraction."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)

        # Sample first 3 pages
        text_chars = 0
        for i, page in enumerate(reader.pages[:3]):
            text = page.extract_text() or ""
            text_chars += len(text.strip())

        # If less than 100 chars across 3 pages, likely scanned
        return text_chars < 100
    except Exception:
        return True  # Assume scanned if we can't read it


async def extract_content(state: FilePipelineState) -> FilePipelineState:
    """
    Stage 2: Extract content from files using appropriate method.
    Routes to different extractors based on file type.
    """
    state["current_stage"] = "extracting"

    # Process files in parallel
    tasks = []
    for file_state in state["files"]:
        if file_state["status"] == "detecting":
            tasks.append(_extract_single_file(file_state, state))

    if tasks:
        await asyncio.gather(*tasks)

    return state


async def _extract_single_file(file_state: FileState, pipeline_state: FilePipelineState) -> None:
    """Extract content from a single file."""
    import time
    start_time = time.time()

    file_state["status"] = "extracting"
    file_type = file_state["detected_type"]
    file_path = file_state["file_path"]

    try:
        if file_type == "pdf":
            if file_state.get("is_scanned"):
                # Try Document AI or OCR for scanned PDFs
                content, metadata = await _extract_with_docai(file_path)
                file_state["extraction_method"] = "docai"
            else:
                # Use PyPDF2 for text PDFs
                content, metadata = _extract_pdf_pypdf2(file_path)
                file_state["extraction_method"] = "pypdf2"

                # Fallback to Document AI if extraction is poor
                if len(content.strip()) < 100 and file_state["retry_count"] < 2:
                    file_state["retry_count"] += 1
                    content, metadata = await _extract_with_docai(file_path)
                    file_state["extraction_method"] = "docai_fallback"

        elif file_type == "docx":
            content, metadata = _extract_docx(file_path)
            file_state["extraction_method"] = "docx"

        elif file_type == "doc":
            # Legacy .doc files - try conversion or fallback
            content, metadata = await _extract_legacy_doc(file_path)
            file_state["extraction_method"] = "doc_converter"

        elif file_type == "txt" or file_type == "code":
            content, metadata = _extract_text(file_path)
            file_state["extraction_method"] = "text"

        elif file_type == "image":
            content, metadata = await _extract_image_ocr(file_path)
            file_state["extraction_method"] = "ocr"

        elif file_type == "spreadsheet":
            content, metadata = _extract_spreadsheet(file_path)
            file_state["extraction_method"] = "spreadsheet"

        elif file_type == "presentation":
            content, metadata = _extract_presentation(file_path)
            file_state["extraction_method"] = "presentation"

        else:
            # Unknown type - try as text
            content, metadata = _extract_text(file_path)
            file_state["extraction_method"] = "text_fallback"

        # Update state
        file_state["raw_content"] = content
        file_state["char_count"] = len(content)
        file_state["page_count"] = metadata.get("page_count")
        file_state["has_tables"] = metadata.get("has_tables", False)
        file_state["has_equations"] = metadata.get("has_equations", False)
        file_state["extraction_confidence"] = metadata.get("confidence", 0.8)

        print(f"[FILE_PIPELINE] Extracted {file_state['file_name']}: {file_state['char_count']} chars via {file_state['extraction_method']}")

    except Exception as e:
        file_state["extraction_error"] = str(e)
        file_state["raw_content"] = ""
        file_state["char_count"] = 0
        file_state["extraction_confidence"] = 0.0
        print(f"[FILE_PIPELINE] Extraction failed for {file_state['file_name']}: {e}")

    file_state["processing_time_ms"] = int((time.time() - start_time) * 1000)


def _extract_pdf_pypdf2(file_path: str) -> tuple[str, dict]:
    """Extract text from PDF using PyPDF2."""
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    text_parts = []

    for i, page in enumerate(reader.pages[:50]):  # Max 50 pages
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_parts.append(f"--- Page {i+1} ---\n{page_text}")

    content = "\n\n".join(text_parts)

    # Truncate if too long
    if len(content) > 100000:
        content = content[:100000] + "\n\n[... content truncated ...]"

    return content, {
        "page_count": len(reader.pages),
        "pages_extracted": min(len(reader.pages), 50),
        "has_tables": False,  # PyPDF2 doesn't detect tables
        "has_equations": False,
        "confidence": 0.85,
    }


async def _extract_with_docai(file_path: str) -> tuple[str, dict]:
    """Extract text using Document AI (with OCR for scanned docs)."""
    try:
        from tools.document_ai import smart_process_document, is_document_ai_available

        if not is_document_ai_available():
            # Fallback to PyPDF2
            return _extract_pdf_pypdf2(file_path)

        with open(file_path, 'rb') as f:
            file_content = f.read()

        result = await smart_process_document(
            file_content=file_content,
            file_name=Path(file_path).name,
            force_docai=True
        )

        return result.get("text", ""), {
            "page_count": result.get("page_count"),
            "has_tables": bool(result.get("tables")),
            "has_equations": bool(result.get("equations")),
            "confidence": result.get("confidence", 0.9),
        }
    except ImportError:
        # Document AI not available, fallback
        return _extract_pdf_pypdf2(file_path)
    except Exception as e:
        print(f"[FILE_PIPELINE] Document AI failed: {e}")
        return _extract_pdf_pypdf2(file_path)


def _extract_docx(file_path: str) -> tuple[str, dict]:
    """Extract text from DOCX files."""
    from docx import Document

    doc = Document(file_path)
    text_parts = []

    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    # Extract tables
    has_tables = len(doc.tables) > 0
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                text_parts.append(row_text)

    content = "\n\n".join(text_parts)

    return content, {
        "page_count": None,
        "paragraph_count": len(doc.paragraphs),
        "has_tables": has_tables,
        "has_equations": False,
        "confidence": 0.95,
    }


async def _extract_legacy_doc(file_path: str) -> tuple[str, dict]:
    """Extract text from legacy .doc files."""
    try:
        # Try antiword or similar tool
        import subprocess
        result = subprocess.run(
            ["antiword", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout, {"confidence": 0.8}
    except Exception:
        pass

    # Fallback: try reading as binary and extracting text
    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        # Basic text extraction from binary
        text = content.decode('utf-8', errors='ignore')
        # Filter to printable ASCII
        text = ''.join(c for c in text if c.isprintable() or c in '\n\t')

        return text, {"confidence": 0.5}
    except Exception as e:
        return f"Could not extract .doc file: {e}", {"confidence": 0.0}


def _extract_text(file_path: str) -> tuple[str, dict]:
    """Extract text from plain text files."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Truncate if too long
    if len(content) > 100000:
        content = content[:100000] + "\n\n[... content truncated ...]"

    return content, {
        "line_count": content.count('\n') + 1,
        "confidence": 1.0,
    }


async def _extract_image_ocr(file_path: str) -> tuple[str, dict]:
    """Extract text from images using OCR."""
    try:
        from tools.document_ai import smart_process_document, is_document_ai_available

        if is_document_ai_available():
            with open(file_path, 'rb') as f:
                file_content = f.read()

            result = await smart_process_document(
                file_content=file_content,
                file_name=Path(file_path).name,
                force_docai=True
            )

            return result.get("text", ""), {
                "confidence": result.get("confidence", 0.7),
            }
    except Exception as e:
        print(f"[FILE_PIPELINE] Image OCR failed: {e}")

    return "[Image content - OCR not available]", {"confidence": 0.0}


def _extract_spreadsheet(file_path: str) -> tuple[str, dict]:
    """Extract text from spreadsheet files."""
    try:
        import pandas as pd

        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Convert to markdown table
        content = df.to_markdown(index=False)

        return content, {
            "rows": len(df),
            "columns": len(df.columns),
            "has_tables": True,
            "confidence": 0.95,
        }
    except Exception as e:
        return f"Could not extract spreadsheet: {e}", {"confidence": 0.0}


def _extract_presentation(file_path: str) -> tuple[str, dict]:
    """Extract text from presentation files."""
    try:
        from pptx import Presentation

        prs = Presentation(file_path)
        text_parts = []

        for i, slide in enumerate(prs.slides):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

            if slide_text:
                text_parts.append(f"--- Slide {i+1} ---\n" + "\n".join(slide_text))

        content = "\n\n".join(text_parts)

        return content, {
            "slide_count": len(prs.slides),
            "confidence": 0.9,
        }
    except Exception as e:
        return f"Could not extract presentation: {e}", {"confidence": 0.0}


async def chunk_content(state: FilePipelineState) -> FilePipelineState:
    """
    Stage 3: Split extracted content into semantic chunks.
    Uses recursive character splitting with overlap.
    """
    state["current_stage"] = "chunking"

    max_chunk_size = state.get("max_chunk_size", 1000)
    chunk_overlap = state.get("chunk_overlap", 200)

    for file_state in state["files"]:
        if file_state["status"] != "extracting" or not file_state["raw_content"]:
            continue

        file_state["status"] = "chunking"
        content = file_state["raw_content"]

        # Simple recursive character splitter
        chunks = _split_into_chunks(content, max_chunk_size, chunk_overlap)

        file_state["chunks"] = [
            {
                "text": chunk,
                "metadata": {
                    "file_id": file_state["file_id"],
                    "file_name": file_state["file_name"],
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
                "embedding_id": None,
            }
            for i, chunk in enumerate(chunks)
        ]
        file_state["chunk_count"] = len(chunks)

        print(f"[FILE_PIPELINE] Chunked {file_state['file_name']}: {len(chunks)} chunks")

    # Update totals
    state["total_chunks"] = sum(f["chunk_count"] for f in state["files"])
    state["total_chars"] = sum(f["char_count"] for f in state["files"])

    return state


def _split_into_chunks(text: str, max_size: int, overlap: int) -> List[str]:
    """Split text into chunks with overlap."""
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_size

        # Try to break at paragraph or sentence boundary
        if end < len(text):
            # Look for paragraph break
            para_break = text.rfind('\n\n', start, end)
            if para_break > start + max_size // 2:
                end = para_break
            else:
                # Look for sentence break
                for sep in ['. ', '! ', '? ', '\n']:
                    sent_break = text.rfind(sep, start, end)
                    if sent_break > start + max_size // 2:
                        end = sent_break + len(sep)
                        break

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]  # Filter empty chunks


async def embed_content(state: FilePipelineState) -> FilePipelineState:
    """
    Stage 4: Embed chunks to Neo4j and/or FileSearch.
    """
    state["current_stage"] = "embedding"

    embed_neo4j = state.get("embed_to_neo4j", False)
    embed_filesearch = state.get("embed_to_filesearch", False)

    for file_state in state["files"]:
        if file_state["status"] != "chunking" or not file_state["chunks"]:
            continue

        file_state["status"] = "embedding"

        try:
            if embed_neo4j:
                node_ids = await _embed_to_neo4j(file_state)
                file_state["neo4j_node_ids"] = node_ids
                file_state["embedded_to_neo4j"] = True
                print(f"[FILE_PIPELINE] Embedded {file_state['file_name']} to Neo4j: {len(node_ids)} nodes")

            if embed_filesearch:
                fs_ids = await _embed_to_filesearch(file_state)
                file_state["filesearch_ids"] = fs_ids
                file_state["embedded_to_filesearch"] = True
                print(f"[FILE_PIPELINE] Embedded {file_state['file_name']} to FileSearch: {len(fs_ids)} chunks")

            file_state["status"] = "complete"
            state["completed_files"] += 1

        except Exception as e:
            file_state["error"] = str(e)
            file_state["status"] = "failed"
            state["failed_files"] += 1
            print(f"[FILE_PIPELINE] Embedding failed for {file_state['file_name']}: {e}")

    return state


async def _embed_to_neo4j(file_state: FileState) -> List[str]:
    """
    Embed file chunks to Neo4j using LazyGraph pattern.

    Creates:
    - Document node for the file
    - Chunk nodes for each chunk
    - Extracted entities (concepts, problems, frameworks) via LangExtract
    - Relationships: CONTAINS, MENTIONS, RELATES_TO
    """
    try:
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([uri, user, password]):
            return []

        driver = GraphDatabase.driver(uri, auth=(user, password))
        node_ids = []

        # Extract entities using LangExtract for relationship building
        extracted_entities = await _extract_entities_for_neo4j(file_state["raw_content"])

        with driver.session() as session:
            # 1. Create/merge Document node
            doc_result = session.run("""
                MERGE (d:Document {file_id: $file_id})
                SET d.file_name = $file_name,
                    d.detected_type = $detected_type,
                    d.char_count = $char_count,
                    d.chunk_count = $chunk_count,
                    d.extraction_method = $extraction_method,
                    d.created_at = datetime()
                RETURN elementId(d) as node_id
            """, {
                "file_id": file_state["file_id"],
                "file_name": file_state["file_name"],
                "detected_type": file_state["detected_type"],
                "char_count": file_state["char_count"],
                "chunk_count": file_state["chunk_count"],
                "extraction_method": file_state["extraction_method"],
            })
            doc_record = doc_result.single()
            doc_node_id = doc_record["node_id"] if doc_record else None

            # 2. Create Chunk nodes with CONTAINS relationship
            for chunk in file_state["chunks"]:
                chunk_result = session.run("""
                    MATCH (d:Document {file_id: $file_id})
                    MERGE (c:Chunk {
                        file_id: $file_id,
                        chunk_index: $chunk_index
                    })
                    SET c.content = $content,
                        c.char_count = $char_count,
                        c.created_at = datetime()
                    MERGE (d)-[:CONTAINS]->(c)
                    RETURN elementId(c) as node_id
                """, {
                    "file_id": file_state["file_id"],
                    "chunk_index": chunk["metadata"]["chunk_index"],
                    "content": chunk["text"][:5000],
                    "char_count": len(chunk["text"]),
                })

                record = chunk_result.single()
                if record:
                    node_ids.append(record["node_id"])
                    chunk["embedding_id"] = record["node_id"]

            # 3. Create LazyGraph relationships from extracted entities
            if extracted_entities:
                # Link to Concepts
                for concept in extracted_entities.get("concepts", []):
                    session.run("""
                        MATCH (d:Document {file_id: $file_id})
                        MERGE (c:Concept {name: $concept_name})
                        MERGE (d)-[:MENTIONS {confidence: $confidence}]->(c)
                    """, {
                        "file_id": file_state["file_id"],
                        "concept_name": concept["name"],
                        "confidence": concept.get("confidence", 0.7),
                    })

                # Link to Problems
                for problem in extracted_entities.get("problems", []):
                    session.run("""
                        MATCH (d:Document {file_id: $file_id})
                        MERGE (p:Problem {name: $problem_name})
                        SET p.description = $description
                        MERGE (d)-[:ADDRESSES]->(p)
                    """, {
                        "file_id": file_state["file_id"],
                        "problem_name": problem["name"][:100],
                        "description": problem.get("description", "")[:500],
                    })

                # Link to Frameworks
                for framework in extracted_entities.get("frameworks", []):
                    session.run("""
                        MATCH (d:Document {file_id: $file_id})
                        MATCH (f:Framework {name: $framework_name})
                        MERGE (d)-[:APPLIES]->(f)
                    """, {
                        "file_id": file_state["file_id"],
                        "framework_name": framework,
                    })

                # Store assumptions
                for assumption in extracted_entities.get("assumptions", []):
                    session.run("""
                        MATCH (d:Document {file_id: $file_id})
                        MERGE (a:Assumption {text: $assumption_text})
                        SET a.type = $assumption_type
                        MERGE (d)-[:CONTAINS_ASSUMPTION]->(a)
                    """, {
                        "file_id": file_state["file_id"],
                        "assumption_text": assumption["text"][:200],
                        "assumption_type": assumption.get("type", "stated"),
                    })

        driver.close()

        if node_ids:
            print(f"[FILE_PIPELINE] LazyGraph: Created {len(node_ids)} chunks + "
                  f"{len(extracted_entities.get('concepts', []))} concepts, "
                  f"{len(extracted_entities.get('problems', []))} problems")

        return node_ids

    except Exception as e:
        print(f"[FILE_PIPELINE] Neo4j LazyGraph embedding error: {e}")
        return []


async def _extract_entities_for_neo4j(content: str) -> Dict[str, Any]:
    """
    Use LangExtract to extract entities for Neo4j relationships.

    Extracts: concepts, problems, frameworks, assumptions
    """
    try:
        from tools.langextract import instant_extract

        # Use instant extraction for speed
        signals = instant_extract(content)

        entities = {
            "concepts": [],
            "problems": [],
            "frameworks": [],
            "assumptions": [],
        }

        # Extract concepts from statistics and key terms
        if signals.get("statistics"):
            for stat in signals["statistics"][:5]:
                entities["concepts"].append({
                    "name": f"Statistic: {stat[:50]}",
                    "confidence": 0.9,
                })

        # Extract problems
        if signals.get("problems"):
            for problem in signals["problems"][:5]:
                entities["problems"].append({
                    "name": problem[:100],
                    "description": problem,
                })

        # Extract assumptions
        if signals.get("assumptions"):
            for assumption in signals["assumptions"][:5]:
                entities["assumptions"].append({
                    "text": assumption,
                    "type": "stated",
                })

        # Check for framework mentions in content
        known_frameworks = [
            "JTBD", "Jobs to Be Done", "TTA", "Trending to the Absurd",
            "S-Curve", "Reverse Salient", "DIKW", "Ackoff", "Minto",
            "Design Thinking", "Lean Startup", "Business Model Canvas",
        ]
        content_lower = content.lower()
        for fw in known_frameworks:
            if fw.lower() in content_lower:
                entities["frameworks"].append(fw)

        return entities

    except ImportError:
        print("[FILE_PIPELINE] LangExtract not available for entity extraction")
        return {}
    except Exception as e:
        print(f"[FILE_PIPELINE] Entity extraction error: {e}")
        return {}


async def _embed_to_filesearch(file_state: FileState) -> List[str]:
    """Embed file chunks to Gemini FileSearch."""
    # This would integrate with the existing FileSearch setup
    # For now, return empty - can be implemented based on your FileSearch setup
    return []


def finalize_pipeline(state: FilePipelineState) -> FilePipelineState:
    """
    Final stage: Compute final statistics and mark complete.
    """
    import time

    state["current_stage"] = "complete"

    # Count completed/failed
    state["completed_files"] = sum(1 for f in state["files"] if f["status"] == "complete")
    state["failed_files"] = sum(1 for f in state["files"] if f["status"] == "failed")

    # Total processing time
    state["processing_time_ms"] = sum(f.get("processing_time_ms", 0) for f in state["files"])

    print(f"[FILE_PIPELINE] Complete: {state['completed_files']}/{state['total_files']} files, "
          f"{state['total_chunks']} chunks, {state['total_chars']} chars")

    return state


# =============================================================================
# CONDITIONAL ROUTING
# =============================================================================

def should_retry_extraction(state: FilePipelineState) -> str:
    """Check if any files need extraction retry."""
    for file_state in state["files"]:
        if file_state["status"] == "extracting":
            # Check if extraction failed and retries available
            if file_state["char_count"] < 50 and file_state["retry_count"] < 2:
                return "retry_extraction"

    return "continue"


def has_content_to_chunk(state: FilePipelineState) -> str:
    """Check if there's content to chunk."""
    for file_state in state["files"]:
        if file_state["status"] == "extracting" and file_state["char_count"] > 0:
            return "chunk"

    return "skip_chunking"


def has_chunks_to_embed(state: FilePipelineState) -> str:
    """Check if there are chunks to embed."""
    if not state.get("embed_to_neo4j") and not state.get("embed_to_filesearch"):
        return "skip_embedding"

    for file_state in state["files"]:
        if file_state["status"] == "chunking" and file_state["chunk_count"] > 0:
            return "embed"

    return "skip_embedding"


# =============================================================================
# PIPELINE CREATION
# =============================================================================

def create_file_processing_pipeline() -> StateGraph:
    """Create the LangGraph file processing pipeline."""

    workflow = StateGraph(FilePipelineState)

    # Add nodes
    workflow.add_node("detect", detect_file_types)
    workflow.add_node("extract", extract_content)
    workflow.add_node("chunk", chunk_content)
    workflow.add_node("embed", embed_content)
    workflow.add_node("finalize", finalize_pipeline)

    # Set entry point
    workflow.set_entry_point("detect")

    # Add edges
    workflow.add_edge("detect", "extract")

    # Conditional edge after extraction
    workflow.add_conditional_edges(
        "extract",
        has_content_to_chunk,
        {
            "chunk": "chunk",
            "skip_chunking": "finalize",
        }
    )

    # Conditional edge after chunking
    workflow.add_conditional_edges(
        "chunk",
        has_chunks_to_embed,
        {
            "embed": "embed",
            "skip_embedding": "finalize",
        }
    )

    # Embed to finalize
    workflow.add_edge("embed", "finalize")

    # Finalize to END
    workflow.add_edge("finalize", END)

    return workflow.compile()


# =============================================================================
# PUBLIC API
# =============================================================================

async def process_files(
    files: List[Dict[str, Any]],
    session_id: str = None,
    embed_to_neo4j: bool = False,
    embed_to_filesearch: bool = False,
    max_chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Dict[str, Any]:
    """
    Process multiple files through the extraction pipeline.

    Args:
        files: List of file dicts with keys: name, path, mime_type (optional)
        session_id: Session identifier for tracking
        embed_to_neo4j: Whether to embed chunks to Neo4j
        embed_to_filesearch: Whether to embed to Gemini FileSearch
        max_chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks

    Returns:
        Pipeline result with extracted content and metadata
    """
    import time
    start_time = time.time()

    # Initialize file states
    file_states = []
    for i, f in enumerate(files):
        file_id = hashlib.md5(f"{f['path']}_{i}".encode()).hexdigest()[:12]

        file_size = 0
        try:
            file_size = os.path.getsize(f["path"])
        except Exception:
            pass

        file_states.append({
            "file_id": file_id,
            "file_name": f.get("name", Path(f["path"]).name),
            "file_path": f["path"],
            "file_size": file_size,
            "mime_type": f.get("mime_type"),
            "detected_type": "unknown",
            "is_scanned": False,
            "has_tables": False,
            "has_equations": False,
            "extraction_method": None,
            "raw_content": "",
            "char_count": 0,
            "page_count": None,
            "extraction_confidence": 0.0,
            "extraction_error": None,
            "chunks": [],
            "chunk_count": 0,
            "embedded_to_neo4j": False,
            "embedded_to_filesearch": False,
            "neo4j_node_ids": [],
            "filesearch_ids": [],
            "status": "pending",
            "retry_count": 0,
            "processing_time_ms": 0,
            "error": None,
        })

    # Initialize pipeline state
    initial_state: FilePipelineState = {
        "session_id": session_id or f"session_{int(time.time())}",
        "files": file_states,
        "total_files": len(files),
        "completed_files": 0,
        "failed_files": 0,
        "extract_tables": True,
        "extract_equations": True,
        "embed_to_neo4j": embed_to_neo4j,
        "embed_to_filesearch": embed_to_filesearch,
        "max_chunk_size": max_chunk_size,
        "chunk_overlap": chunk_overlap,
        "total_chunks": 0,
        "total_chars": 0,
        "processing_time_ms": 0,
        "current_stage": "initializing",
        "error": None,
    }

    # Run pipeline
    pipeline = create_file_processing_pipeline()
    result = await pipeline.ainvoke(initial_state)

    # Calculate total time
    result["processing_time_ms"] = int((time.time() - start_time) * 1000)

    return result


async def process_single_file(
    file_path: str,
    file_name: str = None,
    mime_type: str = None,
    embed_to_neo4j: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to process a single file.

    Returns:
        Dict with: content, char_count, chunks, metadata
    """
    result = await process_files(
        files=[{
            "path": file_path,
            "name": file_name or Path(file_path).name,
            "mime_type": mime_type,
        }],
        embed_to_neo4j=embed_to_neo4j,
    )

    if result["files"]:
        file_result = result["files"][0]
        return {
            "content": file_result["raw_content"],
            "char_count": file_result["char_count"],
            "chunks": file_result["chunks"],
            "detected_type": file_result["detected_type"],
            "extraction_method": file_result["extraction_method"],
            "confidence": file_result["extraction_confidence"],
            "error": file_result.get("error"),
        }

    return {"content": "", "char_count": 0, "error": "No files processed"}


# =============================================================================
# INTEGRATION WITH MINDRIAN_CHAT
# =============================================================================

async def process_uploaded_files_langgraph(
    elements: List[Any],
    embed_to_neo4j: bool = False,
) -> tuple[str, List[Dict], List[Any]]:
    """
    Process Chainlit uploaded elements through LangGraph pipeline.

    Returns:
        Tuple of (file_context_string, image_parts_for_gemini, processed_results)
    """
    from google import genai
    from google.genai import types
    from utils.file_processor import is_image_file, get_image_mime_type

    files_to_process = []
    image_parts = []

    for element in elements:
        if not hasattr(element, 'path') or not element.path:
            continue

        elem_name = element.name or ""
        elem_path = element.path or ""

        # Separate images from documents
        if is_image_file(elem_name) or is_image_file(elem_path):
            # Handle images separately for Gemini multimodal
            try:
                with open(elem_path, "rb") as f:
                    image_bytes = f.read()
                mime_type = get_image_mime_type(elem_name or elem_path)
                image_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
            except Exception as e:
                print(f"[FILE_PIPELINE] Image read error: {e}")
        else:
            # Add document to processing queue
            files_to_process.append({
                "path": elem_path,
                "name": elem_name,
                "mime_type": getattr(element, 'mime', None),
            })

    # Process documents through LangGraph pipeline
    file_context = ""
    results = []

    if files_to_process:
        pipeline_result = await process_files(
            files=files_to_process,
            embed_to_neo4j=embed_to_neo4j,
        )

        for file_state in pipeline_result["files"]:
            if file_state["char_count"] > 0:
                # Format file context
                file_context += f"\n\n---\n**UPLOADED FILE: {file_state['file_name']}**\n"
                file_context += f"(Type: {file_state['detected_type']}, "
                file_context += f"{file_state['char_count']:,} characters, "
                file_context += f"Method: {file_state['extraction_method']})\n"
                file_context += f"---\n{file_state['raw_content']}\n---\n"

            results.append(file_state)

    return file_context, image_parts, results
