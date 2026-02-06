# Skills Knowledge Base Index

This directory contains the accumulated intelligence from skill development — swarm discussions, skill reviews, and change tracking.

## Directory Structure

```
_knowledge/
├── KNOWLEDGE_INDEX.md          # This file
├── COMMIT_EXPERT_CHANGES.md    # Commit expert change tracking
├── QA_RELEVANT_CHANGES.md      # QA-relevant changes
├── RECENT_CHANGES.md           # General recent changes
├── RND_RELEVANT_CHANGES.md     # R&D-relevant changes
├── swarm-reports/              # Multi-agent swarm discussion reports
│   └── YYYY-MM-DD_TOPIC.md
└── skill-reviews/              # Individual skill implementation reviews
    └── YYYY-MM-DD_SKILL_NAME_REVIEW.md
```

## Swarm Reports

Multi-agent discussions where 3-6 specialized agents (Larry, Red Team, Stack Architect, Ackoff, QA, BONO, UI Architect) examine a topic from different perspectives, debate, and converge on consensus + action items.

| Date | Report | Agents | Topic |
|------|--------|--------|-------|
| 2026-02-05 | `PWS_CONSULTANT_DESIGN_REVIEW.md` | Larry, Red Team, Ackoff, Stack, QA, BONO | Architecture review of PWS Consultant agent |
| 2026-02-05 | `PWS_CONSULTANT_IMPLEMENTATION_PLAN.md` | UI Architect (lead), Larry, Stack, Red Team, QA | 12-task implementation plan for all gaps |
| 2026-02-05 | `PWS_CONSULTANT_FINAL_PLAN.md` | Swarm + LangGraph Opus 4.5 | Revised 18-task plan with LangGraph state machine analysis |

### Swarm Report Format

Each report includes:
- **Date, agents, subject, status**
- **Consensus** — what all agents agree on
- **Disagreements** — where agents diverge + reasoning
- **Key findings per agent** — each agent's unique perspective
- **Prioritized action items** — P0/P1/P2/P3 with task descriptions

## Skill Reviews

Implementation reviews for individual skills — what was built, what was verified, known gaps, architecture notes.

| Date | Review | Skill | Status |
|------|--------|-------|--------|
| 2026-02-05 | `PWS_CONSULTANT_REVIEW.md` | pws-consultant | Implemented, gaps documented |
| 2026-02-05 | `PWS_CONSULTANT_UX_REVIEW.md` | pws-consultant | UI/UX review of simulation -- 17 findings (4 critical, 4 high, 5 medium, 4 low) |

### Skill Review Format

Each review includes:
- **Files created and modified** with line counts and purposes
- **Verification results** — what was tested and passed
- **Architecture notes** — unique patterns, integration points
- **Known gaps** — prioritized list of missing features
- **Comparison notes** — vs reference implementations or prototypes

## How to Use

**Before working on a skill:**
```bash
# Check if there's an existing review
ls skills/_knowledge/skill-reviews/ | grep SKILL_NAME

# Check if there's a swarm report with relevant findings
ls skills/_knowledge/swarm-reports/
```

**After a swarm discussion:**
Save the report to `swarm-reports/YYYY-MM-DD_TOPIC.md`

**After implementing or reviewing a skill:**
Save the review to `skill-reviews/YYYY-MM-DD_SKILL_NAME_REVIEW.md`

**Naming convention:**
- Date prefix: `YYYY-MM-DD`
- Topic/skill: UPPER_SNAKE_CASE
- File extension: `.md`
