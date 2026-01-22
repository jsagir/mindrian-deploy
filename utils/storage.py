"""
Supabase Storage utilities for Mindrian
Persistent file storage for uploaded documents
"""

import os
import uuid
from typing import Optional, Tuple
from pathlib import Path

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")

# Initialize Supabase client
_supabase_client = None


def get_supabase_client():
    """Get or create Supabase client."""
    global _supabase_client

    if _supabase_client is None and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            print("✅ Supabase Storage initialized")
        except Exception as e:
            print(f"⚠️ Supabase Storage error: {e}")
            return None

    return _supabase_client


def upload_file(
    file_path: str,
    file_name: str,
    folder: str = "uploads"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Upload a file to Supabase Storage.

    Args:
        file_path: Local path to the file
        file_name: Original filename
        folder: Folder in bucket (default: uploads)

    Returns:
        Tuple of (public_url, storage_path) or (None, None) if failed
    """
    client = get_supabase_client()
    if not client:
        return None, None

    try:
        # Generate unique filename to avoid collisions
        ext = Path(file_name).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = f"{folder}/{unique_name}"

        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Upload to Supabase
        result = client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": get_mime_type(file_name)}
        )

        # Get public URL
        public_url = client.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)

        return public_url, storage_path

    except Exception as e:
        print(f"Upload error: {e}")
        return None, None


def download_file(storage_path: str) -> Optional[bytes]:
    """
    Download a file from Supabase Storage.

    Args:
        storage_path: Path in storage bucket

    Returns:
        File content as bytes or None if failed
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        result = client.storage.from_(SUPABASE_BUCKET).download(storage_path)
        return result
    except Exception as e:
        print(f"Download error: {e}")
        return None


def delete_file(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage.

    Args:
        storage_path: Path in storage bucket

    Returns:
        True if deleted, False otherwise
    """
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.storage.from_(SUPABASE_BUCKET).remove([storage_path])
        return True
    except Exception as e:
        print(f"Delete error: {e}")
        return False


def list_files(folder: str = "uploads") -> list:
    """
    List files in a folder.

    Args:
        folder: Folder path in bucket

    Returns:
        List of file metadata dicts
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        result = client.storage.from_(SUPABASE_BUCKET).list(folder)
        return result
    except Exception as e:
        print(f"List error: {e}")
        return []


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename."""
    ext = Path(filename).suffix.lower()
    mime_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".json": "application/json",
        ".py": "text/x-python",
        ".js": "application/javascript",
        ".html": "text/html",
        ".css": "text/css",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
    }
    return mime_types.get(ext, "application/octet-stream")


def is_storage_configured() -> bool:
    """Check if Supabase Storage is configured."""
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
