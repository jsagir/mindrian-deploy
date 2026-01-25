"""
Cross-Bot Context Persistence using Supabase Storage
Saves and restores conversation context across bot switches and server restarts.
Follows the pattern established in feedback.py for Supabase integration.

Features:
- Custom JSON encoder for non-serializable types (datetime, bytes, etc.)
- Exponential backoff retry for Supabase writes
- Robust error handling for serialization/deserialization
"""

import os
import json
import asyncio
import base64
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from decimal import Decimal

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 0.5

# In-memory cache for fast access (primary layer)
_context_cache: Dict[str, Dict] = {}

# Track failed saves for potential recovery
_failed_saves: Dict[str, Dict] = {}

# Supabase client singleton
_supabase_client = None


class SafeJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles non-serializable types gracefully.
    Converts problematic types to JSON-safe representations.
    """

    def default(self, obj):
        # Handle datetime objects
        if isinstance(obj, datetime):
            return {"__type__": "datetime", "value": obj.isoformat()}
        if isinstance(obj, date):
            return {"__type__": "date", "value": obj.isoformat()}

        # Handle bytes (e.g., image data accidentally in history)
        if isinstance(obj, bytes):
            try:
                # Try to decode as UTF-8 text first
                return {"__type__": "bytes_utf8", "value": obj.decode('utf-8')}
            except UnicodeDecodeError:
                # Fall back to base64 for binary data
                return {"__type__": "bytes_b64", "value": base64.b64encode(obj).decode('ascii')}

        # Handle Decimal
        if isinstance(obj, Decimal):
            return {"__type__": "decimal", "value": str(obj)}

        # Handle sets
        if isinstance(obj, set):
            return {"__type__": "set", "value": list(obj)}

        # Handle objects with __dict__ (custom classes)
        if hasattr(obj, '__dict__'):
            return {"__type__": "object", "class": obj.__class__.__name__, "value": obj.__dict__}

        # Handle other iterables
        try:
            return list(obj)
        except TypeError:
            pass

        # Last resort: convert to string representation
        return {"__type__": "unknown", "repr": repr(obj)}


def safe_json_decode(obj: Dict) -> Any:
    """
    Decode objects that were encoded with SafeJSONEncoder.
    Restores datetime, bytes, etc. to their original types.
    """
    if not isinstance(obj, dict) or "__type__" not in obj:
        return obj

    type_tag = obj.get("__type__")
    value = obj.get("value")

    if type_tag == "datetime":
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value

    if type_tag == "date":
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            return value

    if type_tag == "bytes_utf8":
        return value  # Keep as string for JSON compatibility

    if type_tag == "bytes_b64":
        try:
            return base64.b64decode(value)
        except Exception:
            return value

    if type_tag == "decimal":
        try:
            return Decimal(value)
        except Exception:
            return value

    if type_tag == "set":
        return set(value) if isinstance(value, list) else value

    if type_tag == "object":
        return value  # Return the dict representation

    if type_tag == "unknown":
        return obj.get("repr", str(obj))

    return obj


def safe_json_dumps(data: Any) -> str:
    """
    Safely serialize data to JSON string.
    Uses custom encoder and handles errors gracefully.
    """
    try:
        return json.dumps(data, cls=SafeJSONEncoder, indent=2)
    except Exception as e:
        # Emergency fallback: try to salvage what we can
        print(f"JSON serialization warning: {e}")
        try:
            # Attempt to serialize with aggressive string conversion
            return json.dumps(_sanitize_for_json(data), indent=2)
        except Exception as e2:
            print(f"JSON serialization failed completely: {e2}")
            # Return minimal valid JSON
            return json.dumps({"error": "serialization_failed", "timestamp": datetime.utcnow().isoformat()})


def safe_json_loads(content: bytes) -> Optional[Dict]:
    """
    Safely deserialize JSON content with error handling.
    Handles encoding issues and malformed JSON gracefully.
    """
    # Try different encodings
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
        try:
            text = content.decode(encoding)
            data = json.loads(text, object_hook=safe_json_decode)
            return data
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError as e:
            print(f"JSON decode error with {encoding}: {e}")
            # Try to repair common JSON issues
            try:
                text = content.decode(encoding, errors='replace')
                # Remove null bytes and control characters
                text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')
                data = json.loads(text, object_hook=safe_json_decode)
                return data
            except Exception:
                continue

    print("Failed to decode JSON content with any encoding")
    return None


def _sanitize_for_json(data: Any, depth: int = 0) -> Any:
    """
    Recursively sanitize data for JSON serialization.
    Emergency fallback when SafeJSONEncoder fails.
    """
    if depth > 50:  # Prevent infinite recursion
        return str(data)

    if data is None or isinstance(data, (bool, int, float, str)):
        return data

    if isinstance(data, (datetime, date)):
        return data.isoformat()

    if isinstance(data, bytes):
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return f"<binary:{len(data)}bytes>"

    if isinstance(data, dict):
        return {str(k): _sanitize_for_json(v, depth + 1) for k, v in data.items()}

    if isinstance(data, (list, tuple)):
        return [_sanitize_for_json(item, depth + 1) for item in data]

    if isinstance(data, set):
        return [_sanitize_for_json(item, depth + 1) for item in data]

    # Convert anything else to string
    return str(data)


def get_supabase_client():
    """Get or create Supabase client."""
    global _supabase_client

    if _supabase_client is None and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        except Exception as e:
            print(f"Context persistence Supabase client error: {e}")
            return None

    return _supabase_client


async def _save_to_supabase_with_retry(
    client,
    filename: str,
    json_content: bytes,
    max_retries: int = MAX_RETRIES
) -> tuple[bool, Optional[str]]:
    """
    Save to Supabase with exponential backoff retry.

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    last_error = None
    backoff = INITIAL_BACKOFF_SECONDS

    for attempt in range(max_retries):
        try:
            # Try upload first
            try:
                client.storage.from_(SUPABASE_BUCKET).upload(
                    path=filename,
                    file=json_content,
                    file_options={"content-type": "application/json"}
                )
                return True, None
            except Exception as upload_err:
                error_str = str(upload_err).lower()
                # File exists, try update
                if "duplicate" in error_str or "already exists" in error_str:
                    client.storage.from_(SUPABASE_BUCKET).update(
                        path=filename,
                        file=json_content,
                        file_options={"content-type": "application/json"}
                    )
                    return True, None
                else:
                    raise upload_err

        except Exception as e:
            last_error = str(e)
            error_lower = last_error.lower()

            # Don't retry on certain errors
            if any(term in error_lower for term in ["unauthorized", "forbidden", "invalid", "bad request"]):
                return False, f"Non-retryable error: {last_error}"

            # Retry on network/timeout errors
            if attempt < max_retries - 1:
                print(f"Supabase save attempt {attempt + 1} failed: {last_error}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2  # Exponential backoff
            else:
                print(f"Supabase save failed after {max_retries} attempts: {last_error}")

    return False, last_error


async def save_cross_bot_context(
    user_key: str,
    history: List[Dict],
    bot_id: str,
    bot_name: str
) -> bool:
    """
    Save context to in-memory cache and Supabase Storage.

    Features:
    - Safe JSON serialization (handles datetime, bytes, custom objects)
    - Exponential backoff retry for Supabase
    - Tracks failed saves for potential recovery

    Args:
        user_key: Unique identifier for the user/session context
        history: List of conversation messages
        bot_id: Current bot identifier
        bot_name: Display name of the current bot

    Returns:
        True if saved to at least in-memory cache
    """
    context_data = {
        "user_key": user_key,
        "history": history[-100:],  # Keep last 100 messages to prevent unbounded growth
        "last_bot_id": bot_id,
        "last_bot_name": bot_name,
        "timestamp": datetime.utcnow().isoformat(),
        "message_count": len(history),
    }

    # Always update in-memory cache (fast, reliable)
    _context_cache[user_key] = context_data

    # Remove from failed saves if previously failed
    _failed_saves.pop(user_key, None)

    # Save to Supabase Storage with retry
    client = get_supabase_client()
    if client:
        filename = f"context/{user_key}.json"

        # Safe JSON serialization
        json_str = safe_json_dumps(context_data)
        json_content = json_str.encode('utf-8')

        # Attempt save with retry
        success, error = await _save_to_supabase_with_retry(client, filename, json_content)

        if success:
            print(f"Context saved to Supabase: {filename} ({len(history)} messages)")
        else:
            # Track failed save for potential recovery
            _failed_saves[user_key] = {
                "context_data": context_data,
                "error": error,
                "failed_at": datetime.utcnow().isoformat(),
            }
            print(f"Context save to Supabase failed: {error}")

        return success

    # In-memory only (Supabase not configured)
    return True


async def load_cross_bot_context(user_key: str) -> Optional[Dict]:
    """
    Load context from in-memory cache or Supabase Storage.

    Features:
    - Safe JSON deserialization with multiple encoding attempts
    - Graceful handling of corrupted data

    Args:
        user_key: Unique identifier for the user/session context

    Returns:
        Context dictionary if found, None otherwise
    """
    # Try in-memory cache first (fast path)
    if user_key in _context_cache:
        print(f"Context loaded from memory cache: {user_key}")
        return _context_cache[user_key]

    # Try Supabase Storage (cold start / after restart)
    client = get_supabase_client()
    if client:
        try:
            content = client.storage.from_(SUPABASE_BUCKET).download(f"context/{user_key}.json")
            if content:
                # Safe JSON deserialization
                context = safe_json_loads(content)
                if context:
                    # Populate cache for subsequent requests
                    _context_cache[user_key] = context
                    print(f"Context loaded from Supabase: {user_key} ({context.get('message_count', 0)} messages)")
                    return context
                else:
                    print(f"Failed to parse context JSON for {user_key}")
        except Exception as e:
            error_str = str(e).lower()
            # File likely doesn't exist (new user)
            if "not found" not in error_str and "404" not in error_str:
                print(f"Context load error: {e}")

    return None


async def clear_cross_bot_context(user_key: str) -> bool:
    """
    Clear context from both in-memory cache and Supabase Storage.

    Args:
        user_key: Unique identifier for the user/session context

    Returns:
        True if cleared successfully
    """
    # Clear from in-memory cache
    _context_cache.pop(user_key, None)
    _failed_saves.pop(user_key, None)

    # Clear from Supabase Storage
    client = get_supabase_client()
    if client:
        try:
            client.storage.from_(SUPABASE_BUCKET).remove([f"context/{user_key}.json"])
            print(f"Context cleared from Supabase: {user_key}")
        except Exception as e:
            # File may not exist, that's OK
            if "not found" not in str(e).lower():
                print(f"Context clear error: {e}")

    return True


async def retry_failed_saves() -> Dict[str, bool]:
    """
    Retry any previously failed saves.
    Call this periodically or on reconnection.

    Returns:
        Dict mapping user_key to success status
    """
    results = {}
    client = get_supabase_client()

    if not client or not _failed_saves:
        return results

    for user_key, failed_data in list(_failed_saves.items()):
        context_data = failed_data.get("context_data")
        if context_data:
            filename = f"context/{user_key}.json"
            json_str = safe_json_dumps(context_data)
            json_content = json_str.encode('utf-8')

            success, error = await _save_to_supabase_with_retry(client, filename, json_content)
            results[user_key] = success

            if success:
                _failed_saves.pop(user_key, None)
                print(f"Retry succeeded for {user_key}")
            else:
                print(f"Retry failed for {user_key}: {error}")

    return results


def get_cached_context(user_key: str) -> Optional[Dict]:
    """
    Get context from in-memory cache only (synchronous, fast).
    Use this for quick checks without async overhead.

    Args:
        user_key: Unique identifier for the user/session context

    Returns:
        Context dictionary if cached, None otherwise
    """
    return _context_cache.get(user_key)


def get_failed_saves() -> Dict[str, Dict]:
    """
    Get list of failed saves for monitoring/debugging.

    Returns:
        Dict of user_key -> failed save info
    """
    return _failed_saves.copy()


def is_context_persistence_configured() -> bool:
    """Check if Supabase is configured for context persistence."""
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
