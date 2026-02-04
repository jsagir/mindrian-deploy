"""
Input Validation and Sanitization
=================================

Centralized input validation for Mindrian to prevent:
- XSS attacks
- Prompt injection
- Path traversal
- Resource exhaustion
- Invalid data

All user inputs should pass through these validators before processing.

Usage:
    from utils.input_validation import (
        sanitize_text,
        validate_file_upload,
        sanitize_filename,
        validate_bot_id,
    )

    # Sanitize user message
    clean_message = sanitize_text(user_message)

    # Validate file upload
    is_valid, error = validate_file_upload(filename, size)
"""

import re
import html
from pathlib import Path
from typing import Tuple, Optional, List, Set

# =============================================================================
# CONFIGURATION
# =============================================================================

# Maximum lengths
MAX_MESSAGE_LENGTH = 50000  # 50K chars for messages
MAX_FILE_NAME_LENGTH = 255
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

# Allowed file types for upload
ALLOWED_FILE_EXTENSIONS: Set[str] = {
    # Documents
    '.pdf', '.txt', '.md', '.docx', '.doc', '.rtf',
    # Spreadsheets
    '.csv', '.xlsx', '.xls',
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    # Code (for review)
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json',
}

# Valid bot IDs (must match BOTS dict in mindrian_chat.py)
VALID_BOT_IDS: Set[str] = {
    'lawrence', 'larry_playground', 'tta', 'jtbd', 'scurve',
    'redteam', 'ackoff', 'domain', 'bono', 'known_unknowns',
    'pws_investment', 'scenario', 'validation', 'beautiful_question',
}

# Dangerous patterns to detect (potential prompt injection)
PROMPT_INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r'ignore\s+(previous|above|all)\s+instructions?', re.IGNORECASE),
    re.compile(r'disregard\s+(previous|above|all)\s+instructions?', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+in\s+.*?mode', re.IGNORECASE),
    re.compile(r'new\s+instruction[s]?:', re.IGNORECASE),
    re.compile(r'system\s*prompt[:\s]', re.IGNORECASE),
    re.compile(r'<\s*/?script', re.IGNORECASE),  # Script tags
    re.compile(r'<\s*/?iframe', re.IGNORECASE),  # Iframe injection
]


# =============================================================================
# TEXT SANITIZATION
# =============================================================================

def sanitize_text(
    text: str,
    max_length: int = MAX_MESSAGE_LENGTH,
    strip_html: bool = False,
    check_injection: bool = False
) -> str:
    """
    Sanitize user text input.

    Args:
        text: Raw user input
        max_length: Maximum allowed length (truncates if exceeded)
        strip_html: Whether to remove HTML tags
        check_injection: Whether to flag potential prompt injection

    Returns:
        Sanitized text string
    """
    if not text:
        return ""

    # Convert to string if needed
    if not isinstance(text, str):
        text = str(text)

    # Remove null bytes and control characters (except newline, tab)
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]

    # Strip HTML tags if requested
    if strip_html:
        text = re.sub(r'<[^>]+>', '', text)

    # Escape HTML entities for safe display
    # Note: We don't always want this, hence it's separate from strip_html
    # text = html.escape(text)

    return text


def detect_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """
    Detect potential prompt injection attempts.

    Args:
        text: User input to check

    Returns:
        Tuple of (is_suspicious, matched_pattern_description)
    """
    if not text:
        return False, None

    text_lower = text.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)

    return False, None


def sanitize_for_logging(text: str, max_length: int = 500) -> str:
    """
    Sanitize text for safe logging (removes PII patterns, truncates).

    Args:
        text: Text to sanitize
        max_length: Max length for log output

    Returns:
        Log-safe string
    """
    if not text:
        return ""

    # Truncate
    text = text[:max_length]

    # Mask potential PII patterns
    # Email
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
    # Phone (simple pattern)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    # Credit card (simple pattern)
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)

    return text


# =============================================================================
# FILE VALIDATION
# =============================================================================

def validate_file_upload(
    filename: str,
    size_bytes: int,
    allowed_extensions: Optional[Set[str]] = None,
    max_size: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Validate a file upload.

    Args:
        filename: Name of the uploaded file
        size_bytes: File size in bytes
        allowed_extensions: Override default allowed extensions
        max_size: Override default max size

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    if not filename:
        return False, "Filename is required"

    allowed = allowed_extensions or ALLOWED_FILE_EXTENSIONS
    max_bytes = max_size or MAX_FILE_SIZE_BYTES

    # Check filename length
    if len(filename) > MAX_FILE_NAME_LENGTH:
        return False, f"Filename too long (max {MAX_FILE_NAME_LENGTH} chars)"

    # Check file extension
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        allowed_str = ', '.join(sorted(allowed))
        return False, f"File type '{ext}' not allowed. Allowed: {allowed_str}"

    # Check file size
    if size_bytes > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        return False, f"File too large ({actual_mb:.1f}MB). Max: {max_mb:.0f}MB"

    if size_bytes <= 0:
        return False, "File is empty"

    return True, "OK"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other issues.

    Args:
        filename: Raw filename

    Returns:
        Safe filename
    """
    if not filename:
        return "unnamed_file"

    # Get just the filename, no path
    filename = Path(filename).name

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Replace dangerous characters
    # Keep only alphanumeric, dash, underscore, period
    safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
    filename = ''.join(c if c in safe_chars else '_' for c in filename)

    # Prevent double extensions that might bypass filters
    # e.g., "file.pdf.exe" -> "file_pdf.exe"
    parts = filename.split('.')
    if len(parts) > 2:
        filename = '_'.join(parts[:-1]) + '.' + parts[-1]

    # Prevent hidden files (starting with .)
    if filename.startswith('.'):
        filename = '_' + filename[1:]

    # Truncate if too long
    if len(filename) > MAX_FILE_NAME_LENGTH:
        ext = Path(filename).suffix
        base = filename[:MAX_FILE_NAME_LENGTH - len(ext) - 1]
        filename = base + ext

    return filename or "unnamed_file"


# =============================================================================
# BOT/SESSION VALIDATION
# =============================================================================

def validate_bot_id(bot_id: str) -> Tuple[bool, str]:
    """
    Validate a bot ID.

    Args:
        bot_id: Bot identifier to validate

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    if not bot_id:
        return False, "Bot ID is required"

    if not isinstance(bot_id, str):
        return False, "Bot ID must be a string"

    # Sanitize
    bot_id_clean = bot_id.lower().strip()

    if bot_id_clean not in VALID_BOT_IDS:
        valid_str = ', '.join(sorted(VALID_BOT_IDS))
        return False, f"Invalid bot ID '{bot_id}'. Valid: {valid_str}"

    return True, "OK"


def validate_session_id(session_id: str) -> Tuple[bool, str]:
    """
    Validate a session ID format.

    Args:
        session_id: Session identifier to validate

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    if not session_id:
        return False, "Session ID is required"

    if not isinstance(session_id, str):
        return False, "Session ID must be a string"

    # Session IDs should be alphanumeric with dashes
    if not re.match(r'^[a-zA-Z0-9_-]{8,128}$', session_id):
        return False, "Invalid session ID format"

    return True, "OK"


def validate_user_id(user_id: str) -> Tuple[bool, str]:
    """
    Validate a user ID (typically email or UUID).

    Args:
        user_id: User identifier to validate

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    if not user_id:
        return False, "User ID is required"

    if not isinstance(user_id, str):
        return False, "User ID must be a string"

    # Check length
    if len(user_id) > 256:
        return False, "User ID too long"

    # Allow email format or UUID format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    uuid_pattern = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
    simple_pattern = r'^[a-zA-Z0-9_.-]{3,64}$'

    if not (re.match(email_pattern, user_id) or
            re.match(uuid_pattern, user_id) or
            re.match(simple_pattern, user_id)):
        return False, "Invalid user ID format"

    return True, "OK"


# =============================================================================
# URL VALIDATION
# =============================================================================

def validate_url(url: str, allowed_schemes: Optional[Set[str]] = None) -> Tuple[bool, str]:
    """
    Validate a URL.

    Args:
        url: URL to validate
        allowed_schemes: Allowed URL schemes (default: http, https)

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    if not url:
        return False, "URL is required"

    schemes = allowed_schemes or {'http', 'https'}

    # Basic URL pattern
    url_pattern = re.compile(
        r'^(?P<scheme>https?|ftp)://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    match = url_pattern.match(url)
    if not match:
        return False, "Invalid URL format"

    scheme = match.group('scheme').lower()
    if scheme not in schemes:
        return False, f"URL scheme '{scheme}' not allowed. Allowed: {', '.join(schemes)}"

    # Block local/private IPs (prevent SSRF)
    private_patterns = [
        r'127\.0\.0\.\d+',
        r'10\.\d+\.\d+\.\d+',
        r'172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+',
        r'192\.168\.\d+\.\d+',
        r'localhost',
        r'0\.0\.0\.0',
    ]

    for pattern in private_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False, "Private/local URLs not allowed"

    return True, "OK"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Text
    'sanitize_text',
    'detect_prompt_injection',
    'sanitize_for_logging',
    # Files
    'validate_file_upload',
    'sanitize_filename',
    # IDs
    'validate_bot_id',
    'validate_session_id',
    'validate_user_id',
    # URLs
    'validate_url',
    # Constants
    'ALLOWED_FILE_EXTENSIONS',
    'VALID_BOT_IDS',
    'MAX_MESSAGE_LENGTH',
    'MAX_FILE_SIZE_BYTES',
]
