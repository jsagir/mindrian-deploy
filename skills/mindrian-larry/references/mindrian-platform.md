# Mindrian Platform Reference

Larry's quick reference for the Mindrian platform architecture and patterns.

## Platform Overview

```
MINDRIAN ARCHITECTURE
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  USER INTERFACE (Chainlit)                                                  │
│  ├── Chat interface                                                          │
│  ├── Action buttons                                                          │
│  ├── Task lists                                                              │
│  └── File handling                                                           │
│                                                                              │
│  ORCHESTRATION LAYER                                                         │
│  ├── Bot routing (handle_agent_switch)                                      │
│  ├── Context management (context_store)                                      │
│  ├── Workshop phases (WORKSHOP_PHASES)                                       │
│  └── Tool execution                                                          │
│                                                                              │
│  BOT LAYER (15+ specialized agents)                                          │
│  ├── Each bot has: system prompt + tools + personality                      │
│  └── Defined in BOTS dictionary                                              │
│                                                                              │
│  KNOWLEDGE LAYER                                                             │
│  ├── Neo4j GraphRAG (5,797+ nodes)                                          │
│  ├── Supabase pgvector (embeddings)                                          │
│  └── Pinecone indexes (semantic search)                                      │
│                                                                              │
│  AI MODELS                                                                   │
│  ├── gemini-2.5-flash-preview (fast)                                        │
│  └── gemini-2.5-pro-preview (capable)                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Files

| File | Purpose | Lines (approx) |
|------|---------|----------------|
| `mindrian_chat.py` | Main application, all orchestration | ~8686 |
| `prompts/lawrence.py` | Lawrence bot personality | ~200 |
| `prompts/larry_playground.py` | Larry Playground with full tools | ~300 |
| `prompts/red_team.py` | Red Team adversarial analysis | ~250 |
| `prompts/grading.py` | Grading bot with criteria | ~200 |
| `prompts/pws_investment.py` | Investment analysis (disclaimers!) | ~350 |
| `tools/*.py` | 31 tool files for research | varies |
| `governance/*.py` | Safety and compliance | varies |

---

## Bot Roster

### Core Bots
| Bot | Purpose | Special Rules |
|-----|---------|---------------|
| **Lawrence** | Conversational PWS guide | Main entry point |
| **Larry Playground** | Full tool access | For power users |

### Methodology Bots
| Bot | Purpose | Framework |
|-----|---------|-----------|
| **TTA** | Trending to the Absurd | Future extrapolation |
| **JTBD** | Jobs to Be Done | Customer discovery |
| **S-Curve** | Technology adoption | Lifecycle analysis |
| **Scenario** | Scenario planning | Future mapping |
| **Validation** | Problem validation | Triple Validation |
| **Beautiful Question** | Inquiry methodology | Question design |

### Analysis Bots
| Bot | Purpose | Special Rules |
|-----|---------|---------------|
| **Red Team** | Adversarial analysis | MUST refuse attack plans |
| **Grading** | Evaluation | MUST show criteria |
| **PWS Investment** | Opportunity analysis | MUST show disclaimers |
| **Ackoff** | Systems thinking | Leverage points |
| **Domain** | Multi-domain exploration | Cross-field research |
| **Knowns** | Uncertainty mapping | Rumsfeld matrix |
| **Bono** | Six Thinking Hats | Structured analysis |

---

## Critical Code Patterns

### Action Button Refresh
After any action callback, always refresh buttons:
```python
@cl.action_callback("some_action")
async def handle_action(action):
    # ... do work ...
    
    # ALWAYS refresh buttons at the end
    buttons = get_core_action_buttons(current_bot)
    await cl.Message(content="Done!", actions=buttons).send()
```

### Context Preservation on Bot Switch
```python
async def handle_agent_switch(new_bot, context_store):
    # Save current context
    context_store.save_current()
    
    # Clear bot-specific state if needed
    if requires_clean_slate(new_bot):
        context_store.clear_temporary()
    
    # Load new bot's prompt
    system_prompt = load_bot_prompt(new_bot)
    
    # Transfer relevant context
    context_store.transfer_to(new_bot)
```

### Task List Safety
```python
# Use safe wrapper for TaskList operations
await safe_task_list_send(task_list)

# Not direct:
# await task_list.send()  # Can fail silently
```

### Tool Step Hiding
```python
async with cl.Step(name="Research", show_input=False) as step:
    # show_input=False hides the raw tool call from users
    result = await tool.execute()
    step.output = result
```

---

## Common Issues & Fixes

### Issue: Identity Drift
**Symptom**: Bot responds with wrong personality
**Location**: `handle_agent_switch()` 
**Cause**: Context not cleared, previous bot state persists
**Fix**: Ensure context_store clears bot-specific state on switch

### Issue: Action Buttons Disappear
**Symptom**: Buttons gone after action
**Location**: Action callback handlers
**Cause**: Not calling `get_core_action_buttons()` after callback
**Fix**: Always send new buttons at end of callback

### Issue: Grading Without Criteria
**Symptom**: Grades given without showing rubric
**Location**: `prompts/grading.py`
**Cause**: Prompt not enforcing criteria display
**Fix**: Add mandatory criteria section to prompt

### Issue: Investment Without Disclaimers
**Symptom**: Investment advice without legal notice
**Location**: `prompts/pws_investment.py`
**Cause**: Disclaimer not in every response
**Fix**: Prepend disclaimer to all responses (P0!)

### Issue: Context Lost
**Symptom**: Bot forgets earlier conversation
**Location**: `context_store` implementation
**Cause**: Context not persisted or loaded incorrectly
**Fix**: Check persistence layer, verify session ID

---

## Governance Rules (Non-Negotiable)

### P0: Always Required
1. **PWS Investment disclaimers** on every response
2. **Grading criteria** visible with scores
3. **Red Team** refuses actual attack plans
4. **Prompt injection** blocked at input

### Safety Patterns
```python
# Input sanitization
user_input = sanitize_input(raw_input)
if contains_injection(user_input):
    return INJECTION_BLOCKED_RESPONSE

# Output filtering
response = generate_response(prompt)
if violates_safety(response):
    return SAFETY_FALLBACK_RESPONSE
```

---

## Neo4j Integration

### Connection
```python
from utils.neo4j_client import get_neo4j_client

client = get_neo4j_client()
result = client.query("MATCH (n:Framework) RETURN n.name LIMIT 10")
```

### Common Queries in Mindrian
```cypher
# Find frameworks for problem type
MATCH (f:Framework)-[:ADDRESSES_PROBLEM_TYPE]->(pt:ProblemType)
WHERE pt.name CONTAINS $type
RETURN f.name, pt.name

# Get concept definition
MATCH (c:Concept)
WHERE c.name CONTAINS $concept
RETURN c.name, c.description

# Find book for topic
MATCH (b:Book)-[:COVERS_TOPIC]->(t)
WHERE t.name CONTAINS $topic
RETURN b.name, b.author
```

---

## Repository Access

### Clone/Update
```bash
REPO_DIR="/home/claude/mindrian-deploy"
REPO_URL="https://github.com/jsagir/mindrian-deploy.git"

# Clone or update
if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR" && git fetch --all && git pull
else
    git clone "$REPO_URL" "$REPO_DIR"
fi
```

### Find Code
```bash
# Find function definition
grep -n "def function_name" mindrian_chat.py

# Find all usages
grep -rn "pattern" --include="*.py" .

# Find in specific file
grep -n "search_term" prompts/lawrence.py
```

---

## Useful Commands

```bash
# Health check
python scripts/health_check.py

# Safety evaluation
python governance/eval_suite.py --type safety

# Run locally
chainlit run mindrian_chat.py --watch

# Compare branches
git diff main..feature-branch --stat
```
