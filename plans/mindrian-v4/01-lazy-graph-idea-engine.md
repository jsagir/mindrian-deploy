---
description: Enhance LazyGraph to become an Idea Engine that maps user insights in real-time
---

# Step 1: LazyGraph Idea Engine

## Goal
Transform the existing Neo4j LazyGraph from a passive knowledge store into an active **Idea Engine** that maps user insights, connections, and "aha moments" in real-time during conversations.

## Current State
- `tools/user_lazygraph.py` stores basic user interaction data
- `tools/graphrag_lite.py` enriches responses with graph context
- Neo4j has 18,795+ nodes (concepts, frameworks, case studies)
- Users don't see their ideas being connected in real-time

## What to Build

### 1. Real-time Idea Capture (`tools/idea_engine.py`)
- Extract ideas/insights from each user message using LangExtract patterns
- Create `Idea` nodes in Neo4j with: content, confidence, source_turn, timestamp
- Auto-link ideas to existing `Concept`, `Framework`, `CaseStudy` nodes
- Create `SPARKED_BY`, `CONNECTS_TO`, `CONTRADICTS`, `BUILDS_ON` relationships
- Track idea evolution: when user refines an idea, link old → new with `EVOLVED_INTO`

### 2. Idea Graph Enrichment in Chat
- After extracting ideas, inject a brief "connection hint" into the response context
- Example: "Your idea about X connects to the JTBD framework and 3 other users explored similar territory"
- Only surface connections when confidence > 0.7 (don't spam)

### 3. "Map My Ideas" Action Button
- New action button that generates a Mermaid mindmap of the user's ideas from the current session
- Uses existing `utils/diagrams.py` create_mindmap()
- Shows idea clusters, connections, and evolution paths

## Files to Create/Modify

| Action | File | Changes |
|--------|------|---------|
| CREATE | `tools/idea_engine.py` | Core idea extraction + Neo4j storage |
| MODIFY | `mindrian_chat.py` | Add idea extraction in on_message, add "Map My Ideas" button |
| MODIFY | `tools/graphrag_lite.py` | Add idea-aware enrichment |
| MODIFY | `utils/diagrams.py` | Add `create_idea_map()` function |

## Acceptance Criteria
- [ ] Ideas extracted from user messages and stored as Neo4j nodes
- [ ] Ideas auto-linked to relevant concepts/frameworks
- [ ] "Map My Ideas" button generates visual mindmap
- [ ] Connection hints appear naturally in responses (not forced)
- [ ] No performance degradation (idea extraction is fire-and-forget)

## Validation
```bash
python3 -c "import ast; ast.parse(open('tools/idea_engine.py').read())"
python3 -c "import ast; ast.parse(open('mindrian_chat.py').read())"
python3 scripts/health_check.py
```
