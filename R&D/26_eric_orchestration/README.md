# R&D 26: ERIC Orchestration Pattern

**Status:** Active
**Priority:** High
**Dependencies:** Swarm Orchestrator (skills/swarm-orchestrator), All consultant skills

## Overview

ERIC (Execute, Review, Iterate, Commit) is a bash-based AI orchestration pattern for multi-step project implementation. It drives numbered plan files through AI harnesses (Claude, OpenCode, Gemini, Codex, Kilo) with validation gates and git commits between steps.

## Architecture

```
eric.sh (outer loop)
  │
  ├── Step 1: Read plan file → Generate prompt → Run AI harness
  │   ├── Validation gate (run validation commands)
  │   ├── Git commit
  │   └── Git push
  │
  ├── Step 2: Read plan file → Generate prompt → Run AI harness
  │   ├── Validation gate
  │   ├── Git commit
  │   └── Git push
  │
  ├── ... (N steps)
  │
  └── Review Phase (optional)
      ├── Architecture review
      ├── Type safety check
      ├── Security review
      └── Master fix plan generation
```

## How It Works

1. **Plan Discovery**: Scans a directory for numbered `.md` files (01-*.md, 02-*.md, etc.)
2. **Step Execution**: For each plan file, generates a prompt and sends it to an AI harness
3. **Validation**: Runs user-specified validation commands after each step
4. **State Management**: Tracks step status in `.task-o-matic/state/eric-state.json`
5. **Git Integration**: Auto-commits and pushes after each successful step
6. **Resume**: Can resume from last failed step
7. **Review Phase**: Optional final review with a different AI harness

## Integration with Mindrian Skills

### Swarm Orchestrator as Inner Loop

```
eric.sh (outer loop - drives plan files)
  └── swarm-orchestrator (inner loop - coordinates agents per step)
       ├── commit-expert (validates git changes)
       ├── qa-consultant (runs verification)
       ├── rnd-consultant (tracks R&D progress)
       ├── mindrian-stack (provides tech context)
       └── research-pipeline (gathers evidence)
```

### Skill Roles in ERIC Loop

| Skill | ERIC Role | When Used |
|-------|-----------|-----------|
| swarm-orchestrator | Step coordinator | Every step - selects agents, execution strategy |
| commit-expert | Change validator | After each step - reviews diff, ensures quality |
| qa-consultant | Quality gate | Validation phase - runs checks, flags issues |
| rnd-consultant | Progress tracker | Before/after - tracks which R&D projects are being implemented |
| mindrian-stack | Tech reference | During execution - provides stack context for agents |
| research-pipeline | Evidence gatherer | When step needs external data or validation |
| pws-consultant | Problem framing | When step involves user-facing methodology changes |
| neo4j-writer | Knowledge storage | After implementation - stores new patterns in graph |
| chainlit-consultant | UI validation | When step touches frontend/UI components |

## Usage

```bash
# Basic: run all steps with Claude
./eric.sh plans/mindrian-v4 -H claude --project-name "Mindrian v4"

# With validation and review
./eric.sh plans/mindrian-v4 \
  -H claude \
  --validation-cmd "python3 scripts/health_check.py" \
  --validation-cmd "python3 -m py_compile mindrian_chat.py" \
  --review-harness claude \
  --project-name "Mindrian v4"

# Resume from failure
./eric.sh plans/mindrian-v4 -H claude --resume

# Dry run (show commands without executing)
./eric.sh plans/mindrian-v4 -H claude --dry-run
```

## Plan File Format

Each plan file is a numbered markdown document:

```
plans/mindrian-v4/
├── 01-lazy-graph-enhancement.md
├── 02-agentic-tool-selection.md
├── 03-intent-understanding.md
├── 04-wow-factor-ui.md
└── 05-integration-testing.md
```

Each file contains:
- Description of the feature/change
- Files to create/modify
- Implementation steps
- Acceptance criteria
- Validation commands

## Key Design Decisions

1. **Outer loop (eric.sh) + inner loop (swarm)**: eric.sh handles sequencing, git, and state; swarm handles agent coordination per step
2. **AI harness agnostic**: Supports Claude, OpenCode, Gemini, Codex, Kilo — pick the best for each project
3. **Validation gates**: Each step must pass validation before proceeding
4. **Resume capability**: Can restart from last failure without re-running successful steps
5. **Review phase**: Separate AI does a full codebase review after all steps complete

## Files

- `eric.sh` — Main orchestration script
- `plans/` — Directory for numbered plan files
- `.task-o-matic/state/` — Step state tracking
- `.task-o-matic/logs/` — Execution logs
- `.task-o-matic/review/` — Review phase outputs

## Next Steps

- [ ] Test eric.sh with Claude harness on a 3-step plan
- [ ] Create plan files for next Mindrian features
- [ ] Wire swarm-orchestrator as the inner-loop agent coordinator
- [ ] Add LightRAG storage of implementation decisions after each step
- [ ] Build a Chainlit UI for monitoring ERIC loop progress
