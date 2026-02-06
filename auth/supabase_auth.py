"""
Supabase Auth Integration for Mindrian Chainlit App

Provides:
- Password authentication via Supabase Auth
- JWT token validation for header auth
- Magic link support
- OAuth support (Google, GitHub)
- User profile management

Environment Variables Required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_ANON_KEY: Public anon key for frontend auth
- SUPABASE_SERVICE_KEY: Service role key for backend operations
- SUPABASE_JWT_SECRET: JWT secret for token validation
- CHAINLIT_AUTH_SECRET: Chainlit's auth secret
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import jwt
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# ============================================
# Environment Configuration
# ============================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Check if Supabase Auth is properly configured
SUPABASE_AUTH_ENABLED = bool(
    SUPABASE_URL and
    SUPABASE_ANON_KEY and
    SUPABASE_JWT_SECRET
)

if SUPABASE_AUTH_ENABLED:
    logger.info("[SUPABASE_AUTH] Supabase Auth is ENABLED")
else:
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_ANON_KEY:
        missing.append("SUPABASE_ANON_KEY")
    if not SUPABASE_JWT_SECRET:
        missing.append("SUPABASE_JWT_SECRET")
    logger.warning(f"[SUPABASE_AUTH] Supabase Auth DISABLED - missing: {', '.join(missing)}")


# ============================================
# Supabase Client Management
# ============================================

_auth_client: Optional[Client] = None
_service_client: Optional[Client] = None


def get_supabase_auth_client() -> Optional[Client]:
    """
    Get Supabase client for auth operations (uses anon key).
    This client is safe to use for user-facing auth operations.
    """
    global _auth_client

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None

    if _auth_client is None:
        try:
            _auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            logger.debug("[SUPABASE_AUTH] Auth client created")
        except Exception as e:
            logger.error(f"[SUPABASE_AUTH] Failed to create auth client: {e}")
            return None

    return _auth_client


def get_supabase_service_client() -> Optional[Client]:
    """
    Get Supabase client for backend operations (uses service key).
    This client bypasses RLS - use with caution!
    """
    global _service_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None

    if _service_client is None:
        try:
            _service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            logger.debug("[SUPABASE_AUTH] Service client created")
        except Exception as e:
            logger.error(f"[SUPABASE_AUTH] Failed to create service client: {e}")
            return None

    return _service_client


# ============================================
# JWT Token Validation
# ============================================

def validate_supabase_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a Supabase JWT token and return the decoded payload.

    Args:
        token: The JWT token string (without 'Bearer ' prefix)

    Returns:
        Decoded payload dict if valid, None otherwise.

    Payload contains:
        - sub: User ID (UUID)
        - email: User email
        - role: User role (usually 'authenticated')
        - aud: Audience (usually 'authenticated')
        - exp: Expiration timestamp
        - iat: Issued at timestamp
    """
    if not SUPABASE_JWT_SECRET:
        logger.warning("[SUPABASE_AUTH] JWT validation failed - no secret configured")
        return None

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        logger.debug(f"[SUPABASE_AUTH] JWT validated for user: {payload.get('email', payload.get('sub'))}")
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("[SUPABASE_AUTH] JWT token expired")
        return None
    except jwt.InvalidAudienceError:
        logger.warning("[SUPABASE_AUTH] JWT invalid audience")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[SUPABASE_AUTH] JWT invalid: {e}")
        return None
    except Exception as e:
        logger.error(f"[SUPABASE_AUTH] Unexpected JWT error: {e}")
        return None


# ============================================
# User Authentication Functions
# ============================================

def authenticate_with_password(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with email and password via Supabase Auth.

    Args:
        email: User's email address
        password: User's password

    Returns:
        Dict with user data and session if successful, None otherwise.
        {
            'user': {...},
            'session': {
                'access_token': '...',
                'refresh_token': '...',
                'expires_at': ...
            }
        }
    """
    client = get_supabase_auth_client()
    if not client:
        logger.error("[SUPABASE_AUTH] No auth client available")
        return None

    try:
        response = client.auth.sign_in_with_password({
            "email": email.lower().strip(),
            "password": password
        })

        if response and response.user:
            logger.info(f"[SUPABASE_AUTH] User authenticated: {response.user.email}")
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": str(response.user.email_confirmed_at) if response.user.email_confirmed_at else None,
                    "created_at": str(response.user.created_at) if response.user.created_at else None,
                    "user_metadata": response.user.user_metadata or {},
                },
                "session": {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None,
                    "expires_at": response.session.expires_at if response.session else None,
                }
            }

        return None

    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            logger.warning(f"[SUPABASE_AUTH] Invalid credentials for: {email}")
        elif "Email not confirmed" in error_msg:
            logger.warning(f"[SUPABASE_AUTH] Email not confirmed: {email}")
        else:
            logger.error(f"[SUPABASE_AUTH] Authentication error: {e}")
        return None


def send_magic_link(email: str, redirect_to: Optional[str] = None) -> bool:
    """
    Send a magic link to the user's email for passwordless login.

    Args:
        email: User's email address
        redirect_to: URL to redirect after login (optional)

    Returns:
        True if magic link sent successfully, False otherwise.
    """
    client = get_supabase_auth_client()
    if not client:
        return False

    try:
        options = {}
        if redirect_to:
            options["redirect_to"] = redirect_to

        client.auth.sign_in_with_otp({
            "email": email.lower().strip(),
            "options": options
        })

        logger.info(f"[SUPABASE_AUTH] Magic link sent to: {email}")
        return True

    except Exception as e:
        logger.error(f"[SUPABASE_AUTH] Failed to send magic link: {e}")
        return False


def sign_up_user(email: str, password: str, metadata: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Create a new user account via Supabase Auth.

    Args:
        email: User's email address
        password: User's password (min 8 characters)
        metadata: Optional user metadata (display_name, etc.)

    Returns:
        Dict with user data if successful, None otherwise.
    """
    client = get_supabase_auth_client()
    if not client:
        return None

    try:
        options = {}
        if metadata:
            options["data"] = metadata

        response = client.auth.sign_up({
            "email": email.lower().strip(),
            "password": password,
            "options": options
        })

        if response and response.user:
            logger.info(f"[SUPABASE_AUTH] User signed up: {response.user.email}")
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": str(response.user.email_confirmed_at) if response.user.email_confirmed_at else None,
                },
                "needs_confirmation": response.user.email_confirmed_at is None
            }

        return None

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            logger.warning(f"[SUPABASE_AUTH] Email already registered: {email}")
        else:
            logger.error(f"[SUPABASE_AUTH] Sign up error: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user data by their Supabase user ID.
    Requires service key (bypasses RLS).

    Args:
        user_id: Supabase user UUID

    Returns:
        User data dict if found, None otherwise.
    """
    client = get_supabase_service_client()
    if not client:
        return None

    try:
        response = client.auth.admin.get_user_by_id(user_id)

        if response and response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "email_confirmed_at": str(response.user.email_confirmed_at) if response.user.email_confirmed_at else None,
                "created_at": str(response.user.created_at) if response.user.created_at else None,
                "user_metadata": response.user.user_metadata or {},
            }

        return None

    except Exception as e:
        logger.error(f"[SUPABASE_AUTH] Failed to get user {user_id}: {e}")
        return None


# ============================================
# User Profile Management
# ============================================

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from profiles table.

    Args:
        user_id: Supabase user UUID

    Returns:
        Profile data dict if found, None otherwise.
    """
    client = get_supabase_service_client()
    if not client:
        return None

    try:
        response = client.table("profiles").select("*").eq("id", user_id).single().execute()

        if response.data:
            return response.data

        return None

    except Exception as e:
        logger.debug(f"[SUPABASE_AUTH] Profile not found for {user_id}: {e}")
        return None


def update_user_profile(user_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update user profile in profiles table.

    Args:
        user_id: Supabase user UUID
        updates: Dict of fields to update

    Returns:
        True if successful, False otherwise.
    """
    client = get_supabase_service_client()
    if not client:
        return False

    try:
        updates["updated_at"] = datetime.utcnow().isoformat()

        client.table("profiles").update(updates).eq("id", user_id).execute()

        logger.info(f"[SUPABASE_AUTH] Profile updated for {user_id}")
        return True

    except Exception as e:
        logger.error(f"[SUPABASE_AUTH] Failed to update profile: {e}")
        return False


# ============================================
# User Context Management (Replaces file-based storage)
# ============================================

def save_user_context(user_id: str, context_key: str, context_data: Dict[str, Any]) -> bool:
    """
    Save user context to user_contexts table (replaces file-based storage).

    Args:
        user_id: Supabase user UUID
        context_key: Context identifier (e.g., "default", "bot_lawrence")
        context_data: Context data to save (history, phases, etc.)

    Returns:
        True if successful, False otherwise.
    """
    client = get_supabase_service_client()
    if not client:
        return False

    try:
        upsert_data = {
            "user_id": user_id,
            "context_key": context_key,
            "bot_id": context_data.get("bot_id"),
            "history": context_data.get("history", []),
            "phases": context_data.get("phases", []),
            "current_phase": context_data.get("current_phase", 0),
            "metadata": context_data.get("metadata", {}),
            "updated_at": datetime.utcnow().isoformat(),
        }

        client.table("user_contexts").upsert(
            upsert_data,
            on_conflict="user_id,context_key"
        ).execute()

        logger.debug(f"[SUPABASE_AUTH] Context saved for user {user_id}, key {context_key}")
        return True

    except Exception as e:
        logger.error(f"[SUPABASE_AUTH] Failed to save context: {e}")
        return False


def load_user_context(user_id: str, context_key: str) -> Optional[Dict[str, Any]]:
    """
    Load user context from user_contexts table.

    Args:
        user_id: Supabase user UUID
        context_key: Context identifier

    Returns:
        Context data dict if found, None otherwise.
    """
    client = get_supabase_service_client()
    if not client:
        return None

    try:
        response = client.table("user_contexts").select("*").eq(
            "user_id", user_id
        ).eq(
            "context_key", context_key
        ).single().execute()

        if response.data:
            return {
                "bot_id": response.data.get("bot_id"),
                "history": response.data.get("history", []),
                "phases": response.data.get("phases", []),
                "current_phase": response.data.get("current_phase", 0),
                "metadata": response.data.get("metadata", {}),
                "updated_at": response.data.get("updated_at"),
            }

        return None

    except Exception as e:
        logger.debug(f"[SUPABASE_AUTH] Context not found for user {user_id}, key {context_key}")
        return None


# ============================================
# Rate Limiting (Brute Force Protection)
# ============================================

from collections import defaultdict
from time import time

_auth_attempts: Dict[str, list] = defaultdict(list)
MAX_AUTH_ATTEMPTS = 5
AUTH_WINDOW_SECONDS = 300  # 5 minutes


def check_rate_limit(identifier: str) -> bool:
    """
    Check if the identifier (email/IP) has exceeded rate limit.

    Args:
        identifier: Email or IP address to check

    Returns:
        True if within limit, False if exceeded.
    """
    now = time()
    attempts = _auth_attempts[identifier]

    # Clean old attempts
    attempts[:] = [t for t in attempts if now - t < AUTH_WINDOW_SECONDS]

    if len(attempts) >= MAX_AUTH_ATTEMPTS:
        logger.warning(f"[SUPABASE_AUTH] Rate limit exceeded for: {identifier}")
        return False

    return True


def record_auth_attempt(identifier: str):
    """Record an authentication attempt for rate limiting."""
    _auth_attempts[identifier].append(time())


def clear_auth_attempts(identifier: str):
    """Clear auth attempts after successful login."""
    if identifier in _auth_attempts:
        del _auth_attempts[identifier]
