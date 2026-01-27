"""
LightRAG Direct Graph Push
===========================

Extracts entities + relationships using Gemini, then pushes directly
to LightRAG's graph API - bypassing document processing entirely.

This avoids the memory-intensive entity extraction that crashes LightRAG.

Flow:
  1. Load PWS chunks
  2. For each chunk, use Gemini to extract entities + relationships
  3. Push entities via POST /graph/entity/create
  4. Push relationships via POST /graph/relation/create
  5. Save progress to resume after interruption

Usage:
  python lightrag_graph_push.py --max-chunks 10     # Test with 10 chunks
  python lightrag_graph_push.py --resume             # Continue from progress
  python lightrag_graph_push.py --status             # Show current status
"""

import json
import time
import argparse
import hashlib
import os
import requests
from pathlib import Path
from datetime import datetime

# === Configuration ===
LIGHTRAG_URL = "https://mondrian-ts.onrender.com"
LIGHTRAG_USERNAME = "jsagir"
LIGHTRAG_PASSWORD = "12345678"
CHUNK_FILE = "/home/jsagi/pws_chunks_filtered.json"
PROGRESS_FILE = "/home/jsagi/Mindrian/mindrian-deploy/scripts/lightrag_graph_progress.json"

# Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Rate limits
GEMINI_DELAY = 2       # Seconds between Gemini calls
LIGHTRAG_DELAY = 0.5   # Seconds between LightRAG API calls
MAX_RETRIES = 2

# === Auth ===
_token = None
_session = None


def get_session() -> requests.Session:
    global _session, _token
    if _session is None or _token is None:
        _session = requests.Session()
        resp = requests.post(
            f"{LIGHTRAG_URL}/login",
            data={"username": LIGHTRAG_USERNAME, "password": LIGHTRAG_PASSWORD},
            timeout=30
        )
        if resp.status_code == 200:
            _token = resp.json().get("access_token")
            _session.headers.update({"Authorization": f"Bearer {_token}"})
            print("  [OK] Logged in to LightRAG")
        else:
            print(f"  [ERROR] Login failed: {resp.status_code}")
    return _session


# === Gemini Extraction ===

EXTRACTION_PROMPT = """Extract entities and relationships from this PWS (Problems Worth Solving) educational text.

Return JSON with this exact format:
{
  "entities": [
    {"name": "Entity Name", "type": "CONCEPT|FRAMEWORK|PERSON|TOOL|PRINCIPLE|EXAMPLE", "description": "Brief description"}
  ],
  "relationships": [
    {"source": "Entity A", "target": "Entity B", "description": "How they relate", "keywords": "key, words"}
  ]
}

Rules:
- Entity names should be capitalized properly (e.g., "Jobs To Be Done", "S-Curve Analysis")
- Focus on PWS methodology concepts, frameworks, tools, and principles
- Include 3-10 entities and 2-8 relationships per chunk
- Keep descriptions concise (1 sentence)
- If the text is too short or meaningless, return {"entities": [], "relationships": []}

Text:
"""


def extract_with_gemini(text: str) -> dict:
    """Extract entities and relationships using Gemini."""
    if not GOOGLE_API_KEY:
        print("  [ERROR] GOOGLE_API_KEY not set")
        return {"entities": [], "relationships": []}

    try:
        import google.genai as genai

        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=EXTRACTION_PROMPT + text,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            }
        )

        result = json.loads(response.text)
        return result

    except json.JSONDecodeError as e:
        print(f"  [WARN] Gemini returned invalid JSON: {e}")
        return {"entities": [], "relationships": []}
    except Exception as e:
        print(f"  [ERROR] Gemini extraction failed: {e}")
        return {"entities": [], "relationships": []}


# === LightRAG Graph Push ===

def create_entity(name: str, entity_type: str, description: str) -> bool:
    """Create entity in LightRAG graph."""
    session = get_session()
    try:
        resp = session.post(
            f"{LIGHTRAG_URL}/graph/entity/create",
            json={
                "entity_name": name,
                "entity_data": {
                    "entity_type": entity_type,
                    "description": description,
                }
            },
            timeout=30
        )
        if resp.status_code == 200:
            return True
        elif resp.status_code == 409:  # Already exists
            return True
        else:
            print(f"    [WARN] Entity '{name}': {resp.status_code} - {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"    [ERROR] Entity '{name}': {e}")
        return False


def create_relation(source: str, target: str, description: str, keywords: str = "") -> bool:
    """Create relationship in LightRAG graph."""
    session = get_session()
    try:
        resp = session.post(
            f"{LIGHTRAG_URL}/graph/relation/create",
            json={
                "source_entity": source,
                "target_entity": target,
                "relation_data": {
                    "description": description,
                    "keywords": keywords,
                    "weight": 1.0,
                }
            },
            timeout=30
        )
        if resp.status_code == 200:
            return True
        else:
            print(f"    [WARN] Relation '{source}' -> '{target}': {resp.status_code} - {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"    [ERROR] Relation '{source}' -> '{target}': {e}")
        return False


# === Progress ===

def load_progress() -> dict:
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"processed_chunks": [], "entities_created": 0, "relations_created": 0}


def save_progress(progress: dict):
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


# === Main ===

def run_graph_push(max_chunks: int = None, resume: bool = True):
    print("=" * 60)
    print("LightRAG Direct Graph Push (via Gemini extraction)")
    print("=" * 60)

    # Load chunks
    with open(CHUNK_FILE) as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} filtered chunks")

    # Load progress
    progress = load_progress() if resume else {"processed_chunks": [], "entities_created": 0, "relations_created": 0}
    processed_set = set(progress["processed_chunks"])
    entities_created = progress.get("entities_created", 0)
    relations_created = progress.get("relations_created", 0)

    if processed_set:
        print(f"Resuming: {len(processed_set)} chunks already processed")

    # Filter pending
    pending = []
    for c in chunks:
        chunk_id = c.get("chunk_id", hashlib.sha1(c["content"].encode()).hexdigest())
        if chunk_id not in processed_set:
            pending.append((chunk_id, c))

    print(f"Pending: {len(pending)} chunks")

    if max_chunks:
        pending = pending[:max_chunks]
        print(f"Limited to: {max_chunks} chunks")

    # Process
    for i, (chunk_id, chunk) in enumerate(pending):
        content = chunk["content"]
        print(f"\n--- Chunk {i+1}/{len(pending)} [{len(content)} chars] ---")
        print(f"  Preview: {content[:80]}...")

        # Extract with Gemini
        extraction = extract_with_gemini(content)
        entities = extraction.get("entities", [])
        relationships = extraction.get("relationships", [])
        print(f"  Extracted: {len(entities)} entities, {len(relationships)} relationships")

        # Push entities
        for ent in entities:
            name = ent.get("name", "").strip()
            if not name:
                continue
            ok = create_entity(name, ent.get("type", "CONCEPT"), ent.get("description", ""))
            if ok:
                entities_created += 1
            time.sleep(LIGHTRAG_DELAY)

        # Push relationships
        for rel in relationships:
            source = rel.get("source", "").strip()
            target = rel.get("target", "").strip()
            if not source or not target:
                continue
            ok = create_relation(source, target, rel.get("description", ""), rel.get("keywords", ""))
            if ok:
                relations_created += 1
            time.sleep(LIGHTRAG_DELAY)

        # Mark processed
        processed_set.add(chunk_id)
        progress["processed_chunks"] = list(processed_set)
        progress["entities_created"] = entities_created
        progress["relations_created"] = relations_created

        # Save every 5 chunks
        if (i + 1) % 5 == 0:
            save_progress(progress)
            print(f"  [SAVED] {len(processed_set)} chunks, {entities_created} entities, {relations_created} relations")

        # Rate limit Gemini
        time.sleep(GEMINI_DELAY)

    # Final save
    save_progress(progress)

    print("\n" + "=" * 60)
    print(f"COMPLETE")
    print(f"  Chunks processed: {len(processed_set)}")
    print(f"  Entities created: {entities_created}")
    print(f"  Relations created: {relations_created}")
    print("=" * 60)


def show_status():
    print("=== Graph Push Status ===")
    progress = load_progress()
    print(f"  Chunks processed: {len(progress.get('processed_chunks', []))}")
    print(f"  Entities created: {progress.get('entities_created', 0)}")
    print(f"  Relations created: {progress.get('relations_created', 0)}")
    print(f"  Last updated: {progress.get('last_updated', 'never')}")

    # LightRAG graph size
    try:
        session = get_session()
        r = session.get(f"{LIGHTRAG_URL}/graph/label/list", timeout=15)
        if r.status_code == 200:
            print(f"  Graph labels: {len(r.json())}")
    except:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LightRAG Direct Graph Push")
    parser.add_argument("--max-chunks", type=int, help="Process N chunks max")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--fresh", action="store_true", help="Start fresh")
    parser.add_argument("--status", action="store_true")

    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        run_graph_push(
            max_chunks=args.max_chunks,
            resume=not args.fresh,
        )
