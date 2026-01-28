"""
Upload BONO/Six Thinking Hats Materials to Gemini File Search
==============================================================
Uploads the three Bono materials with LangExtract enrichment:
1. BONO_Innovation_Framework_Materials_Guide.md
2. BONO_Innovation_Framework_Complete_Workbook.md
3. BONO_Innovation_Framework_Case_Studies_Reference_Library.md

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

# --- Source Directory ---
BONO_DIR = Path("/home/jsagi/Mindrian/PWS - Lectures and worksheets created by Mindrian-20251219T001450Z-1-001/PWS - Lectures and worksheets created by Mindrian/Bono")

BONO_FILES = [
    "BONO_Innovation_Framework_Materials_Guide.md",
    "BONO_Innovation_Framework_Complete_Workbook.md",
    "BONO_Innovation_Framework_Case_Studies_Reference_Library.md",
]

# Output dir for extraction JSONs (for future Neo4j ingestion)
EXTRACTIONS_DIR = PROJECT_ROOT / "data" / "course_extractions"
EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# --- LangExtract instant patterns ---
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
    "hats": r'\b(?:white hat|red hat|black hat|yellow hat|green hat|blue hat|thinking hat|parallel thinking)\b',
    "frameworks": r'\b(?:Six Thinking Hats|de Bono|BONO|parallel thinking|adversarial thinking)\b',
}


def instant_extract(text: str) -> dict:
    """Regex-based instant extraction."""
    signals = {}
    for name, pattern in PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            signals[name] = matches[:10]  # Keep more matches for Bono materials
    return signals


# --- LLM extraction for Bono-specific metadata ---

EXTRACTION_PROMPT = """Analyze this BONO/Six Thinking Hats educational document and extract structured metadata for a knowledge graph.

DOCUMENT TITLE: {title}
CATEGORY: Six Thinking Hats / Parallel Thinking

CONTENT (first 15000 chars):
{content}

Return ONLY valid JSON with these fields:
{{
  "title": "Document title",
  "topic": "Main topic (e.g., 'Six Thinking Hats', 'Parallel Thinking')",
  "hat_definitions": ["Which hats are explained: White, Red, Black, Yellow, Green, Blue"],
  "case_studies": ["Named organizations/cases: IBM, ABB, Statoil, NASA, Challenger, etc."],
  "frameworks": ["Named frameworks: Six Thinking Hats, BONO Framework, Parallel Thinking"],
  "concepts": ["Key concepts: adversarial thinking, mode mixing, hat discipline, etc."],
  "personas_discussed": ["Any role-based personas or thinking styles discussed"],
  "session_designs": ["Workshop formats mentioned: 3-hour intro, full day, two sessions, etc."],
  "standard_sequences": ["Hat sequences mentioned: Initial Exploration, Idea Evaluation, etc."],
  "pws_integration": ["How this connects to PWS methodology"],
  "teaching_elements": ["Worksheets, exercises, assessments, discussion questions"],
  "key_claims": ["3-5 most important factual claims or principles (e.g., 'IBM reduced meeting time by 75%')"],
  "graph_connections": ["Suggested Neo4j relationships: 'BONO -[TEACHES]-> WhiteHat', 'IBM -[IMPLEMENTED]-> SixThinkingHats', etc."]
}}"""


def llm_extract(text: str, title: str) -> dict:
    """Run Gemini LLM extraction for Bono-specific metadata."""
    if len(text) < 100:
        return {}

    truncated = text[:15000]  # Larger context for comprehensive materials
    prompt = EXTRACTION_PROMPT.format(title=title, content=truncated)

    try:
        response = llm_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2000,
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
    lines.append("Category: Six Thinking Hats / BONO Framework")
    lines.append("Workshop: Multi-Perspective Validation")

    if extraction.get("topic"):
        lines.append(f"Topic: {extraction['topic']}")
    if extraction.get("hat_definitions"):
        lines.append(f"Hats Covered: {', '.join(extraction['hat_definitions'])}")
    if extraction.get("case_studies"):
        lines.append(f"Case Studies: {', '.join(extraction['case_studies'])}")
    if extraction.get("frameworks"):
        lines.append(f"Frameworks: {', '.join(extraction['frameworks'])}")
    if extraction.get("concepts"):
        lines.append(f"Concepts: {', '.join(extraction['concepts'])}")
    if extraction.get("standard_sequences"):
        lines.append(f"Hat Sequences: {', '.join(extraction['standard_sequences'])}")
    if extraction.get("pws_integration"):
        lines.append(f"PWS Integration: {', '.join(extraction['pws_integration'])}")
    if extraction.get("teaching_elements"):
        lines.append(f"Teaching Elements: {', '.join(extraction['teaching_elements'])}")
    if extraction.get("key_claims"):
        lines.append(f"Key Claims: {'; '.join(extraction['key_claims'])}")

    # Add instant signals summary
    if signals:
        sig_parts = []
        if signals.get("hats"):
            sig_parts.append(f"hat_mentions({len(signals['hats'])})")
        if signals.get("frameworks"):
            sig_parts.append(f"frameworks({len(signals['frameworks'])})")
        if signals.get("problems"):
            sig_parts.append(f"problems({len(signals['problems'])})")
        if signals.get("questions"):
            sig_parts.append(f"questions({len(signals['questions'])})")
        if sig_parts:
            lines.append(f"Signal Density: {', '.join(sig_parts)}")

    lines.append("---\n")
    return "\n".join(lines)


def upload_bono_file(file_path: Path):
    """Extract, enrich, and upload a single Bono file."""
    fname = file_path.name
    display_name = f"T2_Tools/SixThinkingHats/{fname}"

    print(f"  Processing: {display_name}")

    # Skip if already uploaded (extraction JSON exists)
    safe_name = re.sub(r'[^\w\-.]', '_', fname)
    extraction_path = EXTRACTIONS_DIR / f"BONO__{safe_name}.json"
    if extraction_path.exists():
        print(f"    SKIP (already uploaded)")
        return True

    # 1. Read text
    try:
        text = file_path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"    Read error: {e}")
        return False

    if len(text) < 100:
        print(f"    SKIP (too short: {len(text)} chars)")
        return False

    # 2. Instant extract
    signals = instant_extract(text)

    # 3. LLM extract
    extraction = llm_extract(text, fname)

    # 4. Build enriched content
    header = build_enriched_header(extraction, signals)
    if len(text) > 500000:
        text = text[:500000] + "\n\n[... truncated for upload ...]"
    enriched_content = header + text

    # 5. Save extraction JSON locally for Neo4j
    extraction_data = {
        "file": str(file_path),
        "display_name": display_name,
        "category": "BONO",
        "subcategory": "Six Thinking Hats",
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
            return True
        print(f"    OK ({len(text)} chars, {len(extraction.get('hat_definitions', []))} hats, {len(extraction.get('case_studies', []))} cases)")
        return True
    except Exception as e:
        print(f"    UPLOAD ERROR: {e}")
        return False
    finally:
        os.unlink(tmp_path)


def main():
    print("=" * 70)
    print("BONO/SIX THINKING HATS MATERIALS UPLOAD")
    print("=" * 70)
    print(f"Store: {STORE}")
    print(f"LLM Key: ...{GOOGLE_API_KEY[-6:]}")
    print(f"FileSearch Key: ...{GOOGLE_FILESEARCH_API_KEY[-6:]}")
    print(f"Source: {BONO_DIR}")
    print(f"Extractions dir: {EXTRACTIONS_DIR}")
    print()

    if not BONO_DIR.exists():
        print(f"ERROR: Source directory not found: {BONO_DIR}")
        return

    # Find files
    files_found = [BONO_DIR / f for f in BONO_FILES if (BONO_DIR / f).exists()]
    print(f"Found {len(files_found)} of {len(BONO_FILES)} expected files")

    if not files_found:
        print("ERROR: No Bono files found!")
        return

    print("Starting upload...\n")

    uploaded = 0
    failed = 0

    for file_path in files_found:
        ok = upload_bono_file(file_path)
        if ok:
            uploaded += 1
        else:
            failed += 1
        time.sleep(1)  # Rate limit buffer

    print(f"\n{'='*70}")
    print(f"DONE: {uploaded} uploaded, {failed} failed out of {len(files_found)}")
    print(f"Extractions saved to: {EXTRACTIONS_DIR}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
