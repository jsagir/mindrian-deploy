# Memory System Reference

## Table of Contents
1. [Memory Architecture](#memory-architecture)
2. [Memory Types](#memory-types)
3. [Storage Patterns](#storage-patterns)
4. [Retrieval Strategies](#retrieval-strategies)
5. [Context Management](#context-management)
6. [Personalization](#personalization)

---

## Memory Architecture

The Memory System provides **continuity** and **personalization** across sessions.

```
┌─────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM                        │
├─────────────────────────────────────────────────────────┤
│  Working Memory    │  Short-term (current session)     │
│  Episodic Memory   │  Conversation history             │
│  Semantic Memory   │  Long-term knowledge (Neo4j)      │
│  Procedural Memory │  Learned workflows                │
│  User Memory       │  Preferences & context            │
└─────────────────────────────────────────────────────────┘
```

---

## Memory Types

### Working Memory
- **Scope:** Current conversation turn
- **Storage:** In-context (Claude's context window)
- **Capacity:** ~100k tokens
- **Use:** Immediate reasoning and response

### Episodic Memory
- **Scope:** Session history
- **Storage:** Supabase `conversation_memory`
- **Capacity:** Unlimited (summarized)
- **Use:** Conversation continuity

### Semantic Memory
- **Scope:** Domain knowledge
- **Storage:** Neo4j + Supabase knowledge_base
- **Capacity:** Unlimited
- **Use:** RAG retrieval, relationship traversal

### User Memory
- **Scope:** User-specific context
- **Storage:** Supabase `user_preferences`
- **Capacity:** Per-user profile
- **Use:** Personalization, adaptation

---

## Storage Patterns

### Conversation Summarization

```python
def summarize_conversation(messages: list[dict]) -> str:
    """Summarize conversation for long-term storage."""
    # Extract key points
    key_points = []
    decisions_made = []
    topics_discussed = []
    
    for msg in messages:
        if msg['role'] == 'assistant':
            # Extract decisions and recommendations
            pass
        elif msg['role'] == 'user':
            # Extract questions and requirements
            pass
    
    return f"""
    Topics: {', '.join(topics_discussed)}
    Key Points: {'; '.join(key_points)}
    Decisions: {'; '.join(decisions_made)}
    """
```

### Memory Consolidation

```sql
-- Consolidate session memory at end of conversation
INSERT INTO conversation_memory (session_id, role, content, summary)
SELECT 
    session_id,
    'system',
    string_agg(content, E'\n---\n' ORDER BY created_at),
    $summary_text
FROM conversation_memory
WHERE session_id = $session_id
GROUP BY session_id;
```

---

## Retrieval Strategies

### Context-Aware Retrieval

```python
def retrieve_relevant_memory(query: str, user_id: str, session_id: str) -> dict:
    """Multi-source memory retrieval."""
    
    # 1. User preferences (always include)
    user_prefs = get_user_preferences(user_id)
    
    # 2. Recent session context
    recent_context = get_session_summary(session_id)
    
    # 3. Semantic search for relevant knowledge
    relevant_knowledge = vector_search(query, limit=5)
    
    # 4. Graph traversal for related concepts
    related_concepts = graph_expand(relevant_knowledge)
    
    return {
        'user_context': user_prefs,
        'session_context': recent_context,
        'knowledge': relevant_knowledge,
        'related': related_concepts
    }
```

### Tiered Memory Access

| Priority | Source | When to Access |
|----------|--------|----------------|
| 1 | Working Memory | Always (in context) |
| 2 | User Preferences | Every request |
| 3 | Session Summary | Start of conversation |
| 4 | Episodic Memory | When referencing past |
| 5 | Semantic Memory | When knowledge needed |

---

## Context Management

### Context Window Optimization

```python
def build_context(query: str, max_tokens: int = 8000) -> str:
    """Build optimized context within token budget."""
    
    context_parts = []
    remaining_tokens = max_tokens
    
    # Priority 1: User preferences (always include)
    user_ctx = get_user_context()
    context_parts.append(user_ctx)
    remaining_tokens -= count_tokens(user_ctx)
    
    # Priority 2: Session summary
    session_ctx = get_session_summary()
    if count_tokens(session_ctx) <= remaining_tokens:
        context_parts.append(session_ctx)
        remaining_tokens -= count_tokens(session_ctx)
    
    # Priority 3: Relevant knowledge (fill remaining)
    knowledge = vector_search(query)
    for chunk in knowledge:
        if count_tokens(chunk) <= remaining_tokens:
            context_parts.append(chunk)
            remaining_tokens -= count_tokens(chunk)
        else:
            break
    
    return '\n---\n'.join(context_parts)
```

### Sliding Window for Long Conversations

```python
def manage_conversation_window(messages: list, max_messages: int = 20):
    """Keep recent messages, summarize older ones."""
    
    if len(messages) <= max_messages:
        return messages
    
    # Keep system message and recent messages
    system_msg = messages[0] if messages[0]['role'] == 'system' else None
    recent = messages[-max_messages:]
    older = messages[1:-max_messages] if system_msg else messages[:-max_messages]
    
    # Summarize older messages
    summary = summarize_conversation(older)
    
    result = []
    if system_msg:
        result.append(system_msg)
    result.append({'role': 'system', 'content': f'Previous context: {summary}'})
    result.extend(recent)
    
    return result
```

---

## Personalization

### User Profile Schema

```json
{
  "expertise_level": "beginner|intermediate|expert",
  "communication_style": {
    "verbosity": "concise|detailed",
    "formality": "casual|professional",
    "examples_preference": "minimal|moderate|extensive"
  },
  "topic_interests": ["AI", "product management", "strategy"],
  "interaction_history": {
    "total_sessions": 42,
    "common_queries": ["framework selection", "problem analysis"],
    "preferred_frameworks": ["Cynefin", "MECE"]
  }
}
```

### Adaptive Response Generation

```python
def adapt_response(response: str, user_prefs: dict) -> str:
    """Adapt response based on user preferences."""
    
    if user_prefs['expertise_level'] == 'beginner':
        # Add more explanations
        response = add_explanations(response)
    elif user_prefs['expertise_level'] == 'expert':
        # Remove basic explanations
        response = condense_response(response)
    
    if user_prefs['communication_style']['verbosity'] == 'concise':
        response = summarize_key_points(response)
    
    return response
```

---

## Best Practices

1. **Summarize aggressively** - Don't store raw conversations long-term
2. **Prioritize recency** - Recent context > old context
3. **User context first** - Always include user preferences
4. **Lazy loading** - Only retrieve memory when needed
5. **Consolidate regularly** - Merge episodic → semantic memory
6. **Respect token budgets** - Never exceed context limits
