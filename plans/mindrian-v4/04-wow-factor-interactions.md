---
description: Create wow-factor interactions that make users feel the AI truly understands them
---

# Step 4: Wow-Factor Interactions

## Goal
Create moments where users feel genuinely surprised by how well Mindrian understands them and connects their ideas. These "sparks" are Mindrian's core differentiator.

## Current State
- Responses are helpful but predictable
- No "surprise" factor — users get what they expect
- Cross-domain connections (the strongest PWS feature) are underutilized
- No visual "aha moments" in the UI

## What to Build

### 1. Cross-Domain Spark Generator
- When a user discusses topic X, actively search the knowledge graph for unexpected connections
- Use Neo4j path queries: find concepts 2-3 hops away that share non-obvious relationships
- Present as: "Interesting — your idea about X reminds me of how Y solved a similar problem in a completely different field"
- Only fire when connection confidence > 0.85 and novelty > 0.7

### 2. Idea Evolution Timeline
- Track how a user's thinking evolved during the session
- After 10+ turns, offer to show their "thinking journey" as a timeline
- Visual: Mermaid timeline showing key insight moments, pivots, and connections made
- Emotional impact: "Look how far your thinking has come in this session"

### 3. Perspective Shift Moments
- When the user seems locked into one framing, offer a genuine perspective shift
- Not devil's advocate (that's Red Team) — more like "What if you looked at this from the perspective of..."
- Use GraphRAG to find frameworks that would reframe the problem
- Present as a brief, unexpected question that makes the user pause

### 4. Visual Connection Maps (Real-time)
- As ideas accumulate, periodically update a visual map showing connections
- Use the existing MermaidDiagram custom element
- Auto-generate when the conversation hits natural "connection moments"
- The visual map itself becomes a conversation starter

## Files to Create/Modify

| Action | File | Changes |
|--------|------|---------|
| CREATE | `intelligence/spark_generator.py` | Cross-domain connection finder |
| MODIFY | `tools/graphrag_lite.py` | Add cross-domain path queries |
| MODIFY | `utils/diagrams.py` | Add create_thinking_timeline(), create_connection_map() |
| MODIFY | `mindrian_chat.py` | Add spark injection points in message flow |
| MODIFY | `prompts/larry_core.py` | Add perspective shift instructions |

## Acceptance Criteria
- [ ] Cross-domain connections surfaced naturally (not forced)
- [ ] "Thinking journey" timeline available after 10+ turns
- [ ] At least 1 perspective shift offered per substantive conversation
- [ ] Visual connection maps auto-generated at natural moments
- [ ] Users report genuine surprise/delight (qualitative testing)

## Validation
```bash
python3 -c "import ast; ast.parse(open('intelligence/spark_generator.py').read())"
python3 -c "import ast; ast.parse(open('mindrian_chat.py').read())"
python3 scripts/health_check.py
```
