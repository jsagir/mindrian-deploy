"""
Gentle LightRAG Upload Script
=============================

Uploads PWS knowledge chunks to LightRAG with extreme care:
- Tiny batches (5 docs)
- Long waits between batches (10s)
- Health checks before each batch
- Progress saved to resume after crashes
- Dry-run mode to test first

Usage:
  python lightrag_gentle_upload.py --dry-run     # Test without uploading
  python lightrag_gentle_upload.py --batch-size 3 --delay 15  # Extra gentle
  python lightrag_gentle_upload.py --resume      # Continue from last progress
"""

import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime

# Configuration
LIGHTRAG_URL = "https://mondrian-ts.onrender.com"
LIGHTRAG_USERNAME = "jsagir"
LIGHTRAG_PASSWORD = "12345678"
CHUNK_FILES = [
    "/home/jsagi/pws_chunks_filtered.json",  # Filtered: 100+ chars only (756 chunks)
    # "/home/jsagi/pws_chunks.json",  # Original 1136 (includes garbage <100 char chunks)
    # "/home/jsagi/larry_full_knowledge_chunks.json",  # Add later if stable
]
PROGRESS_FILE = "/home/jsagi/Mindrian/mindrian-deploy/scripts/lightrag_upload_progress.json"

# Gentle defaults
DEFAULT_BATCH_SIZE = 5
DEFAULT_DELAY_SECONDS = 10
MAX_RETRIES = 3

# Session for auth
_session = None
_token = None

def get_session() -> requests.Session:
    """Get authenticated session with Bearer token."""
    global _session, _token
    if _session is None or _token is None:
        _session = requests.Session()
        # Login and get JWT token
        resp = requests.post(
            f"{LIGHTRAG_URL}/login",
            data={"username": LIGHTRAG_USERNAME, "password": LIGHTRAG_PASSWORD},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            _token = data.get("access_token")
            # Set Authorization header for all future requests
            _session.headers.update({"Authorization": f"Bearer {_token}"})
            print("  [OK] Logged in to LightRAG")
        else:
            print(f"  [ERROR] Login failed: {resp.status_code} - {resp.text[:100]}")
    return _session


def check_health() -> bool:
    """Check if LightRAG is responsive."""
    try:
        session = get_session()
        resp = session.get(f"{LIGHTRAG_URL}/health", timeout=30)
        if resp.status_code == 200:
            print("  [OK] LightRAG is healthy")
            return True
        else:
            print(f"  [WARN] Health check returned {resp.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] Health check failed: {e}")
        return False


def get_processing_status() -> dict:
    """Get document processing status counts."""
    try:
        session = get_session()
        resp = session.get(f"{LIGHTRAG_URL}/documents/status_counts", timeout=30)
        if resp.status_code == 200:
            return resp.json().get("status_counts", {})
    except:
        pass
    return {}


def wait_for_processing(max_wait: int = 300, check_interval: int = 15) -> bool:
    """Wait until pending/processing docs reach 0 before uploading more.

    This prevents memory buildup that crashes LightRAG.

    Args:
        max_wait: Max seconds to wait (default 5 min)
        check_interval: Seconds between status checks

    Returns:
        True if queue cleared, False if timed out
    """
    elapsed = 0
    while elapsed < max_wait:
        status = get_processing_status()
        pending = status.get("pending", 0)
        processing = status.get("processing", 0)
        in_flight = pending + processing

        if in_flight == 0:
            print(f"  [OK] Processing queue clear (processed: {status.get('processed', 0)}, failed: {status.get('failed', 0)})")
            return True

        print(f"  [WAIT] {in_flight} docs still processing (pending={pending}, processing={processing})... checking in {check_interval}s")
        time.sleep(check_interval)
        elapsed += check_interval

    print(f"  [WARN] Timed out waiting for processing ({max_wait}s)")
    return False


def wait_for_health(max_attempts: int = 5, wait_between: int = 30) -> bool:
    """Wait for LightRAG to become healthy."""
    for attempt in range(max_attempts):
        if check_health():
            return True
        print(f"  Waiting {wait_between}s for service to recover... (attempt {attempt+1}/{max_attempts})")
        time.sleep(wait_between)
    return False


def load_progress() -> dict:
    """Load upload progress from file."""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"uploaded_ids": [], "last_file": None, "last_index": 0}


def save_progress(progress: dict):
    """Save upload progress to file."""
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"  [SAVED] Progress saved ({len(progress['uploaded_ids'])} docs uploaded)")


def upload_batch(texts: list[dict], dry_run: bool = False) -> bool:
    """Upload a batch of texts to LightRAG."""
    if dry_run:
        print(f"  [DRY-RUN] Would upload {len(texts)} documents")
        return True

    try:
        session = get_session()

        # Format for LightRAG /documents/texts endpoint
        payload = {
            "texts": [doc["content"] for doc in texts],
            "split_by_character": "\n\n",
            "split_by_character_only": False,
        }

        resp = session.post(
            f"{LIGHTRAG_URL}/documents/texts",
            json=payload,
            timeout=120  # Long timeout for processing
        )

        if resp.status_code == 200:
            print(f"  [OK] Uploaded {len(texts)} documents")
            return True
        else:
            print(f"  [ERROR] Upload failed: {resp.status_code} - {resp.text[:200]}")
            return False

    except requests.Timeout:
        print("  [ERROR] Upload timed out - LightRAG may be processing")
        return False
    except Exception as e:
        print(f"  [ERROR] Upload exception: {e}")
        return False


def load_chunks(file_path: str) -> list[dict]:
    """Load chunks from JSON file."""
    with open(file_path) as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from {Path(file_path).name}")
    return chunks


def gentle_upload(
    batch_size: int = DEFAULT_BATCH_SIZE,
    delay_seconds: int = DEFAULT_DELAY_SECONDS,
    dry_run: bool = False,
    resume: bool = True,
    max_docs: int = None,
):
    """
    Gently upload chunks to LightRAG.

    Args:
        batch_size: Documents per batch (default 5)
        delay_seconds: Wait between batches (default 10)
        dry_run: Test without actually uploading
        resume: Continue from last progress
        max_docs: Stop after this many docs (for testing)
    """
    print("=" * 60)
    print("LightRAG Gentle Upload")
    print("=" * 60)
    print(f"  Batch size: {batch_size}")
    print(f"  Delay: {delay_seconds}s between batches")
    print(f"  Dry run: {dry_run}")
    print(f"  Resume: {resume}")
    print()

    # Load progress
    progress = load_progress() if resume else {"uploaded_ids": [], "last_file": None, "last_index": 0}
    uploaded_ids = set(progress["uploaded_ids"])

    if uploaded_ids:
        print(f"Resuming from previous session ({len(uploaded_ids)} already uploaded)")

    # Initial health check
    print("\nChecking LightRAG health...")
    if not dry_run and not wait_for_health():
        print("ERROR: LightRAG is not responding. Aborting.")
        return

    total_uploaded = 0
    total_skipped = 0

    for chunk_file in CHUNK_FILES:
        if not Path(chunk_file).exists():
            print(f"SKIP: {chunk_file} not found")
            continue

        chunks = load_chunks(chunk_file)

        # Filter already uploaded
        pending = [c for c in chunks if c.get("chunk_id") not in uploaded_ids]
        print(f"  Pending: {len(pending)} (skipping {len(chunks) - len(pending)} already uploaded)")

        # Apply max_docs limit
        if max_docs:
            pending = pending[:max_docs - total_uploaded]

        # Process in batches
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(pending) + batch_size - 1) // batch_size

            print(f"\n--- Batch {batch_num}/{total_batches} ({len(batch)} docs) ---")

            # Health check every 5 batches
            if not dry_run and batch_num % 5 == 0:
                print("  Periodic health check...")
                if not wait_for_health():
                    print("  Service unhealthy - saving progress and stopping")
                    save_progress({
                        "uploaded_ids": list(uploaded_ids),
                        "last_file": chunk_file,
                        "last_index": i,
                    })
                    return

            # Upload batch
            success = upload_batch(batch, dry_run=dry_run)

            if success:
                for doc in batch:
                    uploaded_ids.add(doc.get("chunk_id", f"unknown_{i}"))
                total_uploaded += len(batch)

                # Save progress every batch
                save_progress({
                    "uploaded_ids": list(uploaded_ids),
                    "last_file": chunk_file,
                    "last_index": i + batch_size,
                })
            else:
                # On failure, wait longer and retry
                print(f"  Batch failed - waiting 30s before retry...")
                time.sleep(30)

                if not wait_for_health():
                    print("  Service crashed - saving progress and stopping")
                    save_progress({
                        "uploaded_ids": list(uploaded_ids),
                        "last_file": chunk_file,
                        "last_index": i,
                    })
                    return

                # Retry once
                success = upload_batch(batch, dry_run=dry_run)
                if not success:
                    print("  Retry failed - stopping to prevent data loss")
                    save_progress({
                        "uploaded_ids": list(uploaded_ids),
                        "last_file": chunk_file,
                        "last_index": i,
                    })
                    return

            # Wait for LightRAG to finish processing before adding more
            if i + batch_size < len(pending):
                print(f"  Waiting {delay_seconds}s then checking processing queue...")
                time.sleep(delay_seconds)
                if not wait_for_processing(max_wait=300, check_interval=15):
                    print("  Processing stalled - pausing to let LightRAG recover...")
                    time.sleep(60)
                    if not wait_for_health():
                        print("  Service down - saving and stopping")
                        save_progress({
                            "uploaded_ids": list(uploaded_ids),
                            "last_file": chunk_file,
                            "last_index": i,
                        })
                        return

            # Check if we hit max_docs
            if max_docs and total_uploaded >= max_docs:
                print(f"\nReached max_docs limit ({max_docs})")
                break

    print("\n" + "=" * 60)
    print(f"COMPLETE: Uploaded {total_uploaded} documents")
    print(f"  Skipped: {total_skipped} (already uploaded)")
    print(f"  Progress saved to: {PROGRESS_FILE}")
    print("=" * 60)


def get_current_status():
    """Show current LightRAG status."""
    print("=== LightRAG Status ===")

    # Health
    check_health()

    session = get_session()

    # Document count
    try:
        resp = session.get(f"{LIGHTRAG_URL}/documents/status_counts", timeout=30)
        if resp.status_code == 200:
            print(f"  Documents: {resp.json()}")
    except:
        pass

    # Graph stats
    try:
        resp = session.get(f"{LIGHTRAG_URL}/graph/label/list", timeout=30)
        if resp.status_code == 200:
            labels = resp.json()
            print(f"  Graph labels: {len(labels) if isinstance(labels, list) else labels}")
    except:
        pass

    # Local progress
    progress = load_progress()
    print(f"  Local progress: {len(progress.get('uploaded_ids', []))} uploaded")
    print(f"  Last updated: {progress.get('last_updated', 'never')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gentle LightRAG upload")
    parser.add_argument("--dry-run", action="store_true", help="Test without uploading")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Docs per batch")
    parser.add_argument("--delay", type=int, default=DEFAULT_DELAY_SECONDS, help="Seconds between batches")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from progress")
    parser.add_argument("--fresh", action="store_true", help="Start fresh (ignore progress)")
    parser.add_argument("--max-docs", type=int, help="Stop after N docs (for testing)")
    parser.add_argument("--status", action="store_true", help="Show current status only")

    args = parser.parse_args()

    if args.status:
        get_current_status()
    else:
        gentle_upload(
            batch_size=args.batch_size,
            delay_seconds=args.delay,
            dry_run=args.dry_run,
            resume=not args.fresh,
            max_docs=args.max_docs,
        )
