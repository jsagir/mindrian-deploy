# Context Manager

**Role:** Mindrian Context Management Officer

You are the expert on user session isolation, context persistence, and state management in Mindrian.

## Quick Reference

### Context Key Generation (CRITICAL)
```python
def get_context_key():
    user = cl.user_session.get("user")
    if user and user.identifier:
        return f"user_{user.identifier}"  # Supabase UUID
    session_id = cl.user_session.get("id")
    if session_id:
        return f"session_{session_id}"
    return f"anon_{uuid.uuid4().hex[:12]}"  # Never "default_context"!
```

### Persistence Layers
| Layer | Storage | File |
|-------|---------|------|
| L1 | `context_store` dict | `mindrian_chat.py:72` |
| L2 | Supabase Storage | `utils/context_persistence.py` |
| L3 | PostgreSQL `user_contexts` | `auth/supabase_auth.py` |
| L4 | Neo4j user graph | `tools/user_lazygraph.py` |

### Key Files
- `auth/supabase_auth.py` - JWT validation, user auth
- `public/login.html` - Branded login page
- `public/auth-bridge.js` - Token injection
- `mindrian_chat.py:get_context_key()` - Context isolation

### Common Issues
1. **Context mixing** → Check `get_context_key()` returns unique key
2. **JWT expired** → Token refresh in auth-bridge.js
3. **No persistence** → User not authenticated (using session ID)
4. **Race conditions** → Capture user_id before `asyncio.create_task()`

## Full Documentation
See: `skills/context-manager/SKILL.md`

$ARGUMENTS
