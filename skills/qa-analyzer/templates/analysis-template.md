# QA Analysis: [Issue Title]

## Classification

| Field | Value |
|-------|-------|
| **Priority** | P0 / P1 / P2 / P3 |
| **Type** | Bug / UX / Performance / Feature |
| **Failure Mode** | Logic / UX Friction / Identity Drift |
| **Affected** | [Bot(s) or component] |
| **Reproducibility** | Always / Sometimes / Once |

## Summary

[1-2 sentence summary of the issue]

## Root Cause Analysis

[What's actually happening and why]

## Recommended Fix

### Location

| Field | Value |
|-------|-------|
| **File** | `path/to/file.py` |
| **Function** | `function_name()` |
| **Line** | ~XXX |

### Code Change

```python
# Before
old_code()

# After
new_code()
```

### Testing After Fix

1. [Specific test case 1]
2. [Specific test case 2]
3. [Regression test]

## PM Recommendation

| Field | Value |
|-------|-------|
| **Urgency** | Fix now / This sprint / Backlog |
| **Dependencies** | [Any blockers] |
| **Risk** | Low / Medium / High |
| **What Could Break** | [Side effects] |

## Related Issues

- [Link to similar issues if any]

---

# Issue Classification Box

```
┌─────────────────────────────────────────────────────┐
│ ISSUE CLASSIFICATION                                 │
├─────────────────────────────────────────────────────┤
│ Priority:    P0 (Critical) / P1 (High) / P2 (Medium)│
│ Type:        Bug / UX / Performance / Feature       │
│ Failure Mode: Logic / UX Friction / Identity Drift  │
│ Affected Bot: All / Specific bot(s)                 │
│ Reproducible: Always / Sometimes / Once             │
└─────────────────────────────────────────────────────┘
```

---

# Priority Decision Tree

```
Is it a safety/governance violation? → P0
Does it break a core bot? → P0
Does it affect grading accuracy? → P0
Is it UI-only with workaround? → P2
Is it cosmetic? → P3
```

---

# Code Location Decision Tree

```
Feedback mentions...
├── Button not working → mindrian_chat.py (@cl.action_callback, line 2800+)
├── Wrong response content → prompts/*.py (system prompt)
├── UI element broken → utils/ui_elements.py
├── Research results wrong → tools/research_orchestrator.py
├── Grading issue → tools/grading_workflow.py + prompts/grading_agent.py
├── Context lost → mindrian_chat.py (context_store line 303, handle_agent_switch line 3581)
├── Phase not advancing → mindrian_chat.py (WORKSHOP_PHASES line 428)
├── Safety/Governance → governance/*.py, governance/prompt_cards/
├── Streaming broken → mindrian_chat.py (response_stream handling)
├── GraphRAG issue → tools/graphrag_lite.py, tools/graph_router.py
└── API error → Check which API, then tools/*.py
```
