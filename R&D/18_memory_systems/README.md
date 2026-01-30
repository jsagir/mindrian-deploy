# R&D 18: Memory Systems

## Status: Research

## What Is This?

Long-term user context storage that persists beyond individual sessions, enabling personalized and continuous coaching experiences.

## Why Implement This?

### Current State
- Each session starts fresh
- Users must re-explain their context
- No learning from past interactions
- Assumptions tracked only within session

### Solution: Memory Layer
- Store user preferences and history
- Track problems explored over time
- Remember validated/invalidated assumptions
- Personalize responses based on history

## Memory Types

### 1. User Preferences
```python
{
    "user_id": "...",
    "preferred_bots": ["lawrence", "tta"],
    "verbosity": "concise",
    "research_depth": "thorough",
    "domains_of_interest": ["healthcare", "AI"]
}
```

### 2. Problem History
```python
{
    "problems_explored": [
        {
            "statement": "How to scale artisanal food business",
            "date": "2026-01-15",
            "bots_used": ["lawrence", "jtbd", "scurve"],
            "insights": ["..."],
            "status": "in_progress"
        }
    ]
}
```

### 3. Assumption Tracking
```python
{
    "assumptions": [
        {
            "text": "Customers will pay premium for organic",
            "status": "challenged",
            "evidence": "Red Team: competitor pricing analysis",
            "date": "2026-01-20"
        }
    ]
}
```

### 4. Learning Progress
```python
{
    "frameworks_learned": ["JTBD", "TTA"],
    "frameworks_in_progress": ["Ackoff"],
    "common_mistakes": ["jumping to solutions"]
}
```

## Research Resources

- [Mem0](https://github.com/mem0ai/mem0) - Memory layer for LLMs
- [LangChain Memory](https://python.langchain.com/docs/modules/memory/)
- [Zep](https://www.getzep.com/) - Long-term memory for agents
- [MemGPT](https://memgpt.ai/) - Virtual context management

## Storage Options

| Option | Pros | Cons |
|--------|------|------|
| Supabase | Already integrated, SQL queries | Schema changes needed |
| Redis | Fast, TTL support | New infrastructure |
| Neo4j | Graph relationships | Query complexity |
| Vector DB | Semantic retrieval | New infrastructure |

## Privacy Considerations

- Opt-in memory storage
- User data deletion API
- Anonymization options
- Session-only mode available

## Estimated Effort

- Design: 8-10 hours
- Implementation: 25-35 hours
- Testing: 10-15 hours

## Status Checklist

- [ ] Research memory patterns
- [ ] Define memory schema
- [ ] Storage layer implementation
- [ ] Retrieval integration
- [ ] Privacy controls
- [ ] User settings UI
- [ ] Testing

---

*Created: 2026-01-30*
