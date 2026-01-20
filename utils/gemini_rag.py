"""
Gemini File Search / RAG Utilities
Handles file upload and caching for workshop materials
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
from google.genai import types

# Cache configuration file
CACHE_CONFIG_FILE = Path(__file__).parent.parent / ".gemini_caches.json"

def get_client():
    """Get Gemini client."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    return genai.Client(api_key=api_key)


def upload_file(file_path: str, display_name: str = None) -> dict:
    """
    Upload a file to Gemini File API.

    Args:
        file_path: Path to the file to upload
        display_name: Optional display name for the file

    Returns:
        dict with file info (name, uri, mime_type)
    """
    client = get_client()

    if display_name is None:
        display_name = Path(file_path).name

    print(f"Uploading {display_name}...")

    uploaded_file = client.files.upload(
        file=file_path,
        config=types.UploadFileConfig(display_name=display_name)
    )

    print(f"  -> Uploaded: {uploaded_file.name}")

    return {
        "name": uploaded_file.name,
        "uri": uploaded_file.uri,
        "mime_type": uploaded_file.mime_type,
        "display_name": display_name
    }


def create_workshop_cache(
    workshop_id: str,
    file_paths: list,
    system_instruction: str,
    model: str = "models/gemini-2.0-flash-001",
    ttl_seconds: int = 86400  # 24 hours
) -> str:
    """
    Create a cached context for a workshop with its materials.

    Args:
        workshop_id: Unique identifier for the workshop (e.g., "ackoff")
        file_paths: List of file paths to include in the cache
        system_instruction: System prompt for the workshop
        model: Gemini model to use
        ttl_seconds: Time-to-live for the cache in seconds

    Returns:
        Cache name/ID
    """
    client = get_client()

    # Upload all files
    uploaded_files = []
    for file_path in file_paths:
        file_info = upload_file(file_path)
        uploaded_files.append(file_info)

    # Create content parts from uploaded files
    parts = []
    for file_info in uploaded_files:
        parts.append(
            types.Part.from_uri(
                file_uri=file_info["uri"],
                mime_type=file_info["mime_type"]
            )
        )

    print(f"Creating cache for {workshop_id}...")

    # Create cached content
    cache = client.caches.create(
        model=model,
        config=types.CreateCachedContentConfig(
            system_instruction=system_instruction,
            contents=[
                types.Content(
                    role="user",
                    parts=parts
                )
            ],
            ttl=f"{ttl_seconds}s",
            display_name=f"mindrian-{workshop_id}-cache"
        )
    )

    print(f"  -> Cache created: {cache.name}")

    # Save cache info to config file
    save_cache_config(workshop_id, {
        "cache_name": cache.name,
        "model": model,
        "files": uploaded_files,
        "ttl_seconds": ttl_seconds
    })

    return cache.name


def save_cache_config(workshop_id: str, config: dict):
    """Save cache configuration to file."""
    all_configs = load_all_cache_configs()
    all_configs[workshop_id] = config

    with open(CACHE_CONFIG_FILE, "w") as f:
        json.dump(all_configs, f, indent=2)

    print(f"  -> Config saved to {CACHE_CONFIG_FILE}")


def load_all_cache_configs() -> dict:
    """Load all cache configurations from file."""
    if CACHE_CONFIG_FILE.exists():
        with open(CACHE_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def get_cache_name(workshop_id: str) -> str:
    """Get the cache name for a workshop."""
    configs = load_all_cache_configs()
    if workshop_id in configs:
        return configs[workshop_id].get("cache_name")
    return None


def refresh_cache(workshop_id: str) -> str:
    """
    Refresh/recreate a cache for a workshop.
    Uses the stored file paths to recreate the cache.
    """
    configs = load_all_cache_configs()
    if workshop_id not in configs:
        raise ValueError(f"No cache config found for {workshop_id}")

    config = configs[workshop_id]
    # For refresh, we'd need to re-upload files since they expire
    # This is a placeholder - actual implementation would need stored file paths
    print(f"Cache refresh for {workshop_id} - requires re-running setup script")
    return None


def list_caches():
    """List all cached contents."""
    client = get_client()

    print("Listing all caches...")
    caches = list(client.caches.list())

    for cache in caches:
        print(f"  - {cache.name} ({cache.display_name})")
        print(f"    Model: {cache.model}")
        print(f"    Expires: {cache.expire_time}")

    return caches


def delete_cache(cache_name: str):
    """Delete a cache by name."""
    client = get_client()
    client.caches.delete(name=cache_name)
    print(f"Deleted cache: {cache_name}")


# ============================================================
# Workshop-specific setup functions
# ============================================================

def setup_ackoff_cache():
    """
    Set up the Ackoff's Pyramid workshop cache with all materials.
    Run this once to upload materials and create the cache.
    """
    from prompts.ackoff_workshop import ACKOFF_WORKSHOP_PROMPT

    # Path to Ackoff materials
    base_path = Path("/home/jsagi/Mindrian/PWS - Lectures and worksheets created by Mindrian-20251219T001450Z-1-001/PWS - Lectures and worksheets created by Mindrian/Akhoffs Pyramid")

    file_paths = [
        base_path / "Lecture adhoffs pyramid.txt",
        base_path / "Worksheet.txt",
    ]

    # Verify files exist
    for fp in file_paths:
        if not fp.exists():
            raise FileNotFoundError(f"File not found: {fp}")

    cache_name = create_workshop_cache(
        workshop_id="ackoff",
        file_paths=[str(fp) for fp in file_paths],
        system_instruction=ACKOFF_WORKSHOP_PROMPT,
        model="models/gemini-2.0-flash-001",
        ttl_seconds=604800  # 7 days
    )

    print(f"\n{'='*50}")
    print(f"Ackoff cache setup complete!")
    print(f"Cache name: {cache_name}")
    print(f"{'='*50}")

    return cache_name


if __name__ == "__main__":
    """Run setup when executed directly."""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "setup-ackoff":
            setup_ackoff_cache()
        elif command == "list":
            list_caches()
        elif command == "delete" and len(sys.argv) > 2:
            delete_cache(sys.argv[2])
        else:
            print("Usage:")
            print("  python gemini_rag.py setup-ackoff  - Set up Ackoff workshop cache")
            print("  python gemini_rag.py list          - List all caches")
            print("  python gemini_rag.py delete <name> - Delete a cache")
    else:
        print("Setting up all workshop caches...")
        setup_ackoff_cache()
