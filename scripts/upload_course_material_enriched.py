"""
Upload Course Material to Gemini File Search with LangExtract Enrichment
=========================================================================
For each file:
1. Extract raw text (PDF/DOCX/TXT/MD/PPTX-as-txt)
2. Run instant_extract() for pattern signals
3. Run Gemini LLM extraction for entities, frameworks, concepts, problems
4. Prepend structured metadata header to file text before uploading
5. Save extraction JSON locally for future Neo4j graph ingestion

Uses GOOGLE_FILESEARCH_API_KEY (owns the store) for uploads,
and GOOGLE_API_KEY for LLM extraction calls.
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from google import genai

# --- API clients ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
GOOGLE_FILESEARCH_API_KEY = os.getenv("GOOGLE_FILESEARCH_API_KEY") or GOOGLE_API_KEY

llm_client = genai.Client(api_key=GOOGLE_API_KEY)
filesearch_client = genai.Client(api_key=GOOGLE_FILESEARCH_API_KEY)

STORE = os.getenv(
    "GEMINI_FILE_SEARCH_STORE",
    "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"
)

# --- Directories ---
COURSE_BASE = Path("/home/jsagi/Course Material")

DIRECTORIES = [
    ("Critical Frameworks of thinking", "Critical-Frameworks"),
    ("Related Material", "Related-Material"),
    # ("Slides", "Slides"),       # .pptx binaries excluded
    ("Cohort 2024", "Cohort-2024"),
    ("Cohort 2025", "Cohort-2025"),
]

SUPPORTED_EXT = {'.docx', '.pdf', '.txt', '.md'}
# Note: .pptx binary files are excluded — use .pptx.txt text exports instead

# Output dir for extraction JSONs (for future Neo4j ingestion)
EXTRACTIONS_DIR = PROJECT_ROOT / "data" / "course_extractions"
EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# --- LangExtract instant patterns (imported inline to avoid dependency issues) ---
PATTERNS = {
    "percentages": r'\b\d+(?:\.\d+)?%',
    "money": r'\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|thousand|B|M|K))?',
    "years": r'\b(?:19|20)\d{2}\b',
    "assumptions": r'\b(?:assume|assuming|assumption|if we|given that|suppose|premise|presume)\b',
    "problems": r'\b(?:problem|issue|challenge|pain point|difficulty|obstacle|barrier|bottleneck)\b',
    "solutions": r'\b(?:solution|solve|fix|address|resolve|approach|strategy|method)\b',
    "questions": r'[^.!]*\?',
    "causation": r'\b(?:because|therefore|thus|hence|consequently|as a result|leads to|causes|due to)\b',
    "trends": r'\b(?:trend|trending|emerging|growing|declining|shifting|changing|evolving)\b',
    "future": r'\b(?:will|future|forecast|predict|projection|by 20\d{2}|next \d+ years)\b',
}


def instant_extract(text: str) -> dict:
    """Regex-based instant extraction."""
    signals = {}
    for name, pattern in PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            signals[name] = matches[:5]
    return signals


# --- Text extraction ---

def extract_text(file_path: Path) -> str:
    """Extract text from supported file types."""
    suffix = file_path.suffix.lower()
    try:
        if suffix == '.pdf':
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            parts = []
            for i, page in enumerate(reader.pages[:50]):
                t = page.extract_text()
                if t:
                    parts.append(t)
            return "\n\n".join(parts)

        elif suffix == '.docx':
            import docx
            doc = docx.Document(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

        elif suffix in ('.txt', '.md'):
            return file_path.read_text(encoding='utf-8', errors='replace')

        elif suffix == '.pptx':
            # Try reading as text (many are .pptx.txt)
            try:
                return file_path.read_text(encoding='utf-8', errors='replace')
            except Exception:
                return ""
        else:
            return ""
    except Exception as e:
        print(f"    Extract error: {e}")
        return ""


# --- LLM extraction for hybrid-ready metadata ---

EXTRACTION_PROMPT = """Analyze this educational document and extract structured metadata for a knowledge graph.

DOCUMENT TITLE: {title}
CATEGORY: {category}

CONTENT:
{content}

Return ONLY valid JSON with these fields:
{{
  "title": "Document title",
  "topic": "Main topic (1-3 words)",
  "frameworks": ["Named frameworks/methodologies mentioned (e.g. JTBD, S-Curve, Ackoff Pyramid, TTA, DIKW, Six Thinking Hats)"],
  "concepts": ["Key concepts/terms (up to 10)"],
  "entities": ["Named people, organizations, companies mentioned"],
  "problems_discussed": ["Specific problems or problem types discussed"],
  "pws_phase_relevance": ["Which PWS workshop phases this relates to: Domain Selection, Problem Definition, Solution Framing, Validation, Scenario Analysis, Red Teaming, Portfolio"],
  "teaching_elements": ["Case studies, exercises, examples, or worksheets found"],
  "key_claims": ["2-3 most important factual claims or principles taught"],
  "cohort_context": "If from a specific cohort/session, what was the pedagogical context",
  "graph_connections": ["Suggested Neo4j relationships: 'THIS_DOC -[TEACHES]-> Concept', 'THIS_DOC -[USES_FRAMEWORK]-> Framework', etc."]
}}"""


def llm_extract(text: str, title: str, category: str) -> dict:
    """Run Gemini LLM extraction for graph-ready metadata."""
    if len(text) < 50:
        return {}

    truncated = text[:12000]
    prompt = EXTRACTION_PROMPT.format(
        title=title, category=category, content=truncated
    )

    try:
        response = llm_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1500,
            )
        )
        resp_text = response.text.strip()
        # Clean markdown wrapping
        if resp_text.startswith("```"):
            resp_text = re.sub(r'^```(?:json)?\n?', '', resp_text)
            resp_text = re.sub(r'\n?```$', '', resp_text)
        return json.loads(resp_text)
    except Exception as e:
        print(f"    LLM extract error: {e}")
        return {}


def build_enriched_header(extraction: dict, signals: dict) -> str:
    """Build a metadata header to prepend to file content for FileSearch."""
    lines = ["---", "METADATA (auto-extracted for hybrid search)", "---"]

    if extraction.get("topic"):
        lines.append(f"Topic: {extraction['topic']}")
    if extraction.get("frameworks"):
        lines.append(f"Frameworks: {', '.join(extraction['frameworks'])}")
    if extraction.get("concepts"):
        lines.append(f"Concepts: {', '.join(extraction['concepts'])}")
    if extraction.get("entities"):
        lines.append(f"Entities: {', '.join(extraction['entities'])}")
    if extraction.get("problems_discussed"):
        lines.append(f"Problems: {', '.join(extraction['problems_discussed'])}")
    if extraction.get("pws_phase_relevance"):
        lines.append(f"PWS Phases: {', '.join(extraction['pws_phase_relevance'])}")
    if extraction.get("teaching_elements"):
        lines.append(f"Teaching Elements: {', '.join(extraction['teaching_elements'])}")
    if extraction.get("key_claims"):
        lines.append(f"Key Claims: {'; '.join(extraction['key_claims'])}")

    # Add instant signals summary
    if signals:
        sig_parts = []
        if signals.get("problems"):
            sig_parts.append(f"problems({len(signals['problems'])})")
        if signals.get("assumptions"):
            sig_parts.append(f"assumptions({len(signals['assumptions'])})")
        if signals.get("trends"):
            sig_parts.append(f"trends({len(signals['trends'])})")
        if signals.get("questions"):
            sig_parts.append(f"questions({len(signals['questions'])})")
        if sig_parts:
            lines.append(f"Signal Density: {', '.join(sig_parts)}")

    lines.append("---\n")
    return "\n".join(lines)


# --- Upload ---

def upload_enriched_file(file_path: Path, category: str, subfolder: str = None):
    """Extract, enrich, and upload a single file."""
    fname = file_path.name
    if subfolder:
        display_name = f"Course/{category}/{subfolder}/{fname}"
    else:
        display_name = f"Course/{category}/{fname}"

    print(f"  Processing: {display_name}")

    # Skip if already uploaded (extraction JSON exists)
    safe_name = re.sub(r'[^\w\-.]', '_', fname)
    extraction_path = EXTRACTIONS_DIR / f"{category}__{safe_name}.json"
    if extraction_path.exists():
        print(f"    SKIP (already uploaded)")
        return True

    # 1. Extract text
    text = extract_text(file_path)
    if len(text) < 30:
        print(f"    SKIP (too short: {len(text)} chars)")
        return False

    # 2. Instant extract
    signals = instant_extract(text)

    # 3. LLM extract
    extraction = llm_extract(text, fname, category)

    # 4. Build enriched content (cap at 500K chars to avoid upload timeouts)
    header = build_enriched_header(extraction, signals)
    if len(text) > 500000:
        text = text[:500000] + "\n\n[... truncated for upload ...]"
    enriched_content = header + text

    # 5. Save extraction JSON locally for Neo4j
    extraction_data = {
        "file": str(file_path),
        "display_name": display_name,
        "category": category,
        "subfolder": subfolder,
        "extraction": extraction,
        "signals": signals,
        "char_count": len(text),
        "extracted_at": datetime.now().isoformat(),
    }
    extraction_path.write_text(json.dumps(extraction_data, indent=2, default=str))

    # 6. Upload enriched content as temp txt file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
        tmp.write(enriched_content)
        tmp_path = tmp.name

    try:
        operation = filesearch_client.file_search_stores.upload_to_file_search_store(
            file=tmp_path,
            file_search_store_name=STORE,
            config={'display_name': display_name},
        )
        # Poll with timeout (max 120s)
        waited = 0
        while not operation.done and waited < 120:
            time.sleep(3)
            waited += 3
            try:
                operation = filesearch_client.operations.get(operation)
            except Exception:
                break
        if waited >= 120:
            print(f"    TIMEOUT (upload started but not confirmed)")
            return True  # Extraction saved, upload likely processing
        print(f"    OK ({len(text)} chars, {len(extraction.get('frameworks', []))} frameworks)")
        return True
    except Exception as e:
        print(f"    UPLOAD ERROR: {e}")
        return False
    finally:
        os.unlink(tmp_path)


def find_files(directory: Path):
    """Find supported files recursively."""
    files = []
    for item in directory.rglob("*"):
        if item.is_file() and not item.name.endswith("Zone.Identifier"):
            if item.suffix.lower() in SUPPORTED_EXT:
                relative = item.relative_to(directory)
                subfolder = str(relative.parent) if relative.parent != Path(".") else None
                files.append((item, subfolder))
    return files


def main():
    print("=" * 70)
    print("ENRICHED COURSE MATERIAL UPLOAD (with LangExtract)")
    print("=" * 70)
    print(f"Store: {STORE}")
    print(f"LLM Key: ...{GOOGLE_API_KEY[-6:]}")
    print(f"FileSearch Key: ...{GOOGLE_FILESEARCH_API_KEY[-6:]}")
    print(f"Extractions dir: {EXTRACTIONS_DIR}")

    total_files = 0
    for dir_name, _ in DIRECTORIES:
        dp = COURSE_BASE / dir_name
        if dp.exists():
            f = find_files(dp)
            total_files += len(f)
            print(f"  {dir_name}: {len(f)} files")

    print(f"\nTotal: {total_files} files")
    print("Starting...\n")

    uploaded = 0
    failed = 0

    for dir_name, category in DIRECTORIES:
        dp = COURSE_BASE / dir_name
        if not dp.exists():
            print(f"SKIP dir not found: {dp}")
            continue

        files = find_files(dp)
        print(f"\n{'='*60}")
        print(f"{dir_name}: {len(files)} files")
        print(f"{'='*60}")

        for file_path, subfolder in files:
            ok = upload_enriched_file(file_path, category, subfolder)
            if ok:
                uploaded += 1
            else:
                failed += 1
            time.sleep(1)  # Rate limit buffer

    print(f"\n{'='*70}")
    print(f"DONE: {uploaded} uploaded, {failed} failed/skipped out of {total_files}")
    print(f"Extractions saved to: {EXTRACTIONS_DIR}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
