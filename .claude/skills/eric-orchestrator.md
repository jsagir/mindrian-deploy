---
description: ERIC orchestration - break complex features into numbered plan files with validation gates, git commits between steps, and swarm coordination
---

# ERIC Orchestrator

Plan multi-step implementations with Execute, Review, Iterate, Commit loops.

Read the full skill guide: `skills/eric-orchestrator/SKILL.md`

## Quick Start

Ask:
- "Plan the implementation of [feature]"
- "Break this into ERIC steps"
- "Create plan files for [change]"
- "What's the safest way to implement [X]?"

## Depth Levels
- **Quick** (1-2 steps): Bug fix, config change
- **Standard** (3-4 steps): New feature, pipeline
- **Deep** (5-8 steps): Architecture change, new agent

## Key Files
- `R&D/26_eric_orchestration/eric.sh` — Bash orchestration script
- `R&D/26_eric_orchestration/README.md` — Full documentation
- `plans/mindrian-v4/` — Example plan files
- `.task-o-matic/state/` — Execution state tracking

## Part of the Swarm
ERIC = outer loop (sequencing, git, validation)
Swarm = inner loop (agent selection, execution)
