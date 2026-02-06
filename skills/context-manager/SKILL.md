# Mindrian Context Management Officer

**Version:** 1.0.0
**Last Updated:** 2026-02-06
**Domain:** Session State, User Isolation, Persistence Architecture

---

## Role

You are the **Context Management Officer** for Mindrian - the expert responsible for user session isolation, context persistence, and state management across the platform. You have deep expertise in:

- Supabase Auth integration (JWT validation, user identity)
- Session state management (Chainlit `cl.user_session`)
- Context persistence (Supabase Storage + PostgreSQL tables)
- Neo4j graph-based context (user knowledge graphs)
- LangChain/LangGraph state patterns

---

## Core Responsibilities

### 1. User Isolation

Ensure no cross-user data leakage:

```python
# CORRECT: Unique context key per user
def get_context_key() -> str:
    user = cl.user_session.get("user")
    if user and user.identifier:
        return f"user_{user.identifier}"  # Supabase UUID

    session_id = cl.user_session.get("id")
    if session_id:
        return f"session_{session_id}"  # Chainlit session

    return f"anon_{uuid.uuid4().hex[:12]}"  # Never shared

# WRONG: Shared fallback key (caused context mixing bug)
return "default_context"  # NEVER DO THIS
```

### 2. Context Persistence Layers

| Layer | Storage | Purpose | Scope |
|-------|---------|---------|-------|
| **L1: In-Memory** | `context_store` dict | Fast access during session | Process lifetime |
| **L2: Supabase Storage** | `context/{user_key}.json` | Cross-session persistence | User lifetime |
| **L3: PostgreSQL** | `user_contexts` table | Structured queries, RLS | User lifetime |
| **L4: Neo4j** | User knowledge graph | Relationship-aware context | User lifetime |

### 3. Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTH FLOW                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User visits app                                             │
│       │                                                      │
│       ▼                                                      │
│  auth-bridge.js checks localStorage for token                │
│       │                                                      │
│  ┌────┴────┐                                                │
│  │ Token?  │                                                │
│  └────┬────┘                                                │
│   No  │  Yes                                                │
│   │   │                                                      │
│   │   └──► Inject into Authorization header                 │
│   │        └──► Chainlit @cl.header_auth_callback           │
│   │             └──► validate_supabase_jwt()                │
│   │                  └──► cl.User(identifier=uuid)          │
│   │                                                          │
│   └──► Redirect to /public/login.html                       │
│        └──► Supabase Auth UI                                │
│             └──► On success: store token, redirect          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Files

### Authentication

| File | Purpose |
|------|---------|
| `auth/__init__.py` | Auth module exports |
| `auth/supabase_auth.py` | JWT validation, Supabase client, rate limiting |
| `public/login.html` | Branded login page with Supabase Auth UI |
| `public/auth-bridge.js` | Token injection into Chainlit requests |

### Context Management

| File | Purpose |
|------|---------|
| `mindrian_chat.py:get_context_key()` | Generate unique user context keys |
| `mindrian_chat.py:context_store` | In-memory context dict (L1) |
| `utils/context_persistence.py` | Supabase Storage persistence (L2) |
| `auth/supabase_auth.py:save_user_context()` | PostgreSQL persistence (L3) |
| `tools/user_lazygraph.py` | Neo4j user memory (L4) |
| `tools/session_memory.py` | Session-aware memory management |

### Database Schema

```sql
-- Supabase PostgreSQL (L3)
CREATE TABLE public.user_contexts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    context_key TEXT NOT NULL,
    bot_id TEXT,
    history JSONB DEFAULT '[]'::jsonb,
    phases JSONB DEFAULT '[]'::jsonb,
    current_phase INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, context_key)
);

-- RLS: Users can only access own contexts
CREATE POLICY "Users can manage own contexts"
    ON public.user_contexts FOR ALL
    USING (auth.uid() = user_id);
```

---

## Environment Variables

```bash
# Supabase Auth (required)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...  # Public, frontend auth
SUPABASE_SERVICE_KEY=eyJ...  # Private, backend operations
SUPABASE_JWT_SECRET=xxx  # JWT validation

# Chainlit Auth
CHAINLIT_AUTH_SECRET=xxx  # Session signing

# Neo4j (optional, for L4)
NEO4J_URI=neo4j+s://xxx
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=xxx
```

---

## Common Issues & Solutions

### Issue 1: Context Mixing Between Users

**Symptom:** User A sees User B's conversation history

**Root Cause:** `get_context_key()` returning shared key like `"default_context"`

**Solution:**
```python
# Always return unique key
def get_context_key() -> str:
    # Priority 1: Authenticated user UUID
    user = cl.user_session.get("user")
    if user and hasattr(user, "identifier") and user.identifier:
        return f"user_{user.identifier}"

    # Priority 2: Session ID (unique per tab)
    session_id = cl.user_session.get("id")
    if session_id:
        return f"session_{session_id}"

    # Priority 3: Random UUID (never shared)
    import uuid
    return f"anon_{uuid.uuid4().hex[:12]}"
```

### Issue 2: JWT Token Expired

**Symptom:** User suddenly logged out, API returns 401

**Root Cause:** Supabase JWT expires (default: 1 hour)

**Solution:**
```javascript
// In auth-bridge.js - handle token refresh
supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'TOKEN_REFRESHED' && session) {
        localStorage.setItem('supabase_access_token', session.access_token);
    }
});
```

### Issue 3: Context Not Persisting Across Sessions

**Symptom:** User loses history after page reload

**Root Cause:** Using session ID instead of user ID (session changes on reload)

**Solution:** Ensure user is authenticated so `user.identifier` is used instead of session ID.

### Issue 4: Race Condition in Background Tasks

**Symptom:** Incomplete or mixed context when multiple tasks run

**Root Cause:** `asyncio.create_task()` without proper scoping

**Solution:**
```python
# Always capture user_id before creating task
user_id = cl.user_session.get("user").identifier

async def scoped_task(uid):
    # Use captured uid, not cl.user_session
    await save_user_context(uid, context_key, data)

asyncio.create_task(scoped_task(user_id))
```

---

## Integration with Other Systems

### Neo4j Integration

User context enrichment via LazyGraph:

```python
from tools.graphrag_lite import enrich_for_larry

# Get context-aware hints from Neo4j
hint = enrich_for_larry(
    user_message=message,
    turn_count=turn_count,
    user_id=user_id  # Scope to user's knowledge graph
)
```

### LangChain State Patterns

For LangGraph-style state management:

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class MindrianState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    context_key: str
    bot_id: str
    phases: list
    current_phase: int
```

### Session Memory

For cross-session memory retrieval:

```python
from tools.session_memory import session_memory_start, session_memory_process

# On session start
user_context = await session_memory_start(
    user_id=user_id,
    session_id=session_id,
    bot_id=bot_id
)

# After each message
asyncio.create_task(session_memory_process(
    user_id=user_id,
    session_id=session_id,
    conversation=history,
    bot_id=bot_id,
    phase=phase_name
))
```

---

## Security Considerations

### 1. JWT Validation

Always validate JWT tokens server-side:

```python
def validate_supabase_jwt(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except jwt.InvalidTokenError:
        return None
```

### 2. Rate Limiting

Protect against brute force:

```python
MAX_AUTH_ATTEMPTS = 5
AUTH_WINDOW_SECONDS = 300

def check_rate_limit(identifier: str) -> bool:
    attempts = _auth_attempts[identifier]
    attempts[:] = [t for t in attempts if time() - t < AUTH_WINDOW_SECONDS]
    return len(attempts) < MAX_AUTH_ATTEMPTS
```

### 3. Row Level Security (RLS)

Supabase policies ensure data isolation:

```sql
-- Users can only access their own contexts
CREATE POLICY "Users can manage own contexts"
    ON public.user_contexts FOR ALL
    USING (auth.uid() = user_id);
```

### 4. Service Key Protection

Never expose service key to frontend:

```python
# Backend only - bypasses RLS
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Frontend safe - respects RLS
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
```

---

## Debugging Commands

### Check User Context

```python
# In Python console or debug endpoint
context_key = get_context_key()
print(f"Context key: {context_key}")
print(f"In-memory: {context_store.get(context_key)}")
```

### Verify JWT

```python
from auth.supabase_auth import validate_supabase_jwt

token = "eyJ..."
payload = validate_supabase_jwt(token)
print(f"User ID: {payload.get('sub')}")
print(f"Email: {payload.get('email')}")
print(f"Expires: {payload.get('exp')}")
```

### Check Supabase Tables

```sql
-- List all user contexts
SELECT user_id, context_key, bot_id,
       jsonb_array_length(history) as msg_count,
       updated_at
FROM public.user_contexts
ORDER BY updated_at DESC;
```

---

## Related Skills

- `mindrian-stack` - Overall architecture
- `neo4j-schema-navigator` - Graph context queries
- `qa-consultant` - Quality assurance for context issues
- `commit-expert` - Recent changes to context code

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-06 | Initial release with Supabase Auth integration |
