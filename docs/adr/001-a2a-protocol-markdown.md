# ADR-001: Agent-to-Agent Communication via Markdown Files

**Status:** Accepted
**Date:** 2026-02-01
**Decision Makers:** Development Team

## Context

Mindrian is a multi-agent platform where specialized AI agents collaborate on user problems. When users switch between agents (e.g., from Lawrence to TTA), or when agents need to delegate tasks to each other, context must be preserved and transferred.

We needed a mechanism for:
1. Preserving conversation context across agent switches
2. Enabling agents to delegate tasks to other agents
3. Providing an audit trail of agent collaboration
4. Supporting debugging and quality assurance

## Decision Drivers

- **Human Readability**: Developers and QA must be able to inspect handoffs
- **Machine Parseability**: Agents must programmatically consume handoffs
- **Debuggability**: When things go wrong, we need clear visibility
- **Extensibility**: The protocol must accommodate future features
- **Simplicity**: Avoid over-engineering for the current use case

## Considered Options

### Option A: JSON Files
```json
{
  "from_agent": "lawrence",
  "to_agent": "tta",
  "context": "..."
}
```

**Pros:** Easy to parse, widely supported
**Cons:** Hard to read, no natural place for long-form context

### Option B: Database Records
Store handoffs in Supabase with structured columns.

**Pros:** Queryable, scalable
**Cons:** Opaque to developers, requires database access for debugging

### Option C: Markdown with YAML Frontmatter (Selected)
```markdown
---
protocol: a2a/v1
from_agent: lawrence
to_agent: tta
handoff_type: delegate
---

# Agent Handoff: Lawrence → TTA

## Context Summary
User exploring urban farming...
```

**Pros:** Human-readable, machine-parseable, self-documenting
**Cons:** Requires parsing logic, potential for malformed documents

## Decision

We chose **Option C: Markdown with YAML Frontmatter** because:

1. **Best of both worlds**: YAML frontmatter provides structured, machine-readable metadata while the Markdown body supports rich, human-readable context.

2. **Debugging-first design**: When investigating issues, developers can open handoff files in any text editor and immediately understand what happened.

3. **Natural language context**: Long-form summaries, conversation highlights, and task descriptions are naturally expressed in Markdown.

4. **Version control friendly**: Plain text files work well with git, enabling history and diff viewing.

5. **Extensible**: The Markdown body can be extended with new sections without changing the parsing logic for existing sections.

## Consequences

### Positive
- Excellent debugging experience
- Self-documenting handoffs
- Easy to add new context sections
- Works offline (file-based)

### Negative
- Requires custom parsing logic
- Potential for malformed documents (mitigated by JSON schema validation)
- Larger file size than pure JSON

### Mitigations
- Added JSON schema validation for YAML frontmatter (ADR-001a)
- Created helper functions for creating/parsing handoffs
- Established clear section conventions

## Implementation

### File Structure
```
protocols/
├── a2a_protocol.py      # Handoff creation, parsing, validation
├── context_journal.py   # Living conversation document
└── schemas/
    └── a2a_handoff_v1.json  # JSON schema for validation
```

### Key Functions
```python
# Create handoff
handoff = await create_switch_handoff(from_agent, to_agent, ...)

# Save to file
save_handoff(handoff)

# Load and validate
handoff = A2AHandoff.from_markdown(content, validate=True)
```

### Handoff Types
| Type | Purpose |
|------|---------|
| `switch` | User moves to different agent |
| `delegate` | Agent asks another for help |
| `consult` | Quick question, expects immediate return |
| `return` | Returning from delegation |

## Related Decisions

- ADR-002: Context Journal for Thinking Steps (pending)
- ADR-003: Neo4j Integration for Insight Nodes (pending)

## References

- [YAML Frontmatter Specification](https://jekyllrb.com/docs/front-matter/)
- [JSON Schema](https://json-schema.org/)
- `protocols/a2a_protocol.py` - Implementation
- `CLAUDE.md` - A2A Protocol section
