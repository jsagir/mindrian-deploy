# Mindrian Skills Guide

Skills are specialized knowledge modules that enhance Claude Code with domain expertise. They are **documentation + knowledge**, NOT bots.

## What Are Skills?

Skills provide:
- Domain-specific knowledge and patterns
- Code references and examples
- Integration with Mindrian's agent ecosystem
- Structured workflows and best practices

## Available Skills

| Skill | Purpose | Invoke With |
|-------|---------|-------------|
| `swarm-orchestrator` | Multi-agent coordination | `/swarm` |
| `commit-expert` | Repository change tracking | `/commit-expert` |
| `qa-consultant` | Testing and quality analysis | `/qa` |
| `rnd-consultant` | R&D and architecture decisions | `/rnd` |
| `mindrian-stack` | Technical stack knowledge | `/stack` |
| `chainlit-components` | UI component patterns | `/components` |
| `neo4j-schema-navigator` | Graph database navigation | `/neo4j` |

## How Skills Auto-Update

Skills update automatically via post-commit hook:

```bash
# In .git/hooks/post-commit
python3 scripts/update_consultant_knowledge.py
```

This regenerates:
- `skills/_knowledge/RECENT_CHANGES.md`
- `skills/_knowledge/QA_RELEVANT_CHANGES.md`
- `skills/_knowledge/RND_RELEVANT_CHANGES.md`
- `skills/_knowledge/COMMIT_EXPERT_CHANGES.md`

## Installing in Claude Code

### Option 1: Project Skills (Recommended)
Copy skill files to your project:

```bash
cp -r skills/swarm-orchestrator .claude/skills/
```

Then invoke with `/swarm` in Claude Code.

### Option 2: User Skills
Add to your user skills directory:

```bash
cp .claude/skills/*.md ~/.claude/skills/
```

Skills are available across all projects.

## Installing in Claude Desktop

Add the skills repo as an MCP resource, or reference SKILL.md files directly in your Claude Desktop configuration.

## Using the Swarm Orchestrator

The Swarm Orchestrator coordinates multiple agents for complex queries:

```
/swarm Should I pursue this startup idea?
```

**Strategies:**
- `--quick` - Fast 2-agent check
- `--research` - Research before analysis
- `--stress` - Debate with Red Team
- `--full` - Comprehensive all-agent analysis

**Workflows:**
- `--workflow regression-hunt` - Bug investigation
- `--workflow arch-review` - Architecture decisions

## Using Individual Skills

### Commit Expert
```
/commit-expert What changed in the auth module?
/commit-expert Show regressions since last deploy
```

### QA Consultant
```
/qa What should we test for the new feature?
/qa Analyze test coverage gaps
```

### R&D Consultant
```
/rnd Should we adopt GraphQL?
/rnd Review the migration plan
```

## Creating New Skills

Follow this pattern:

```
skills/
└── my-skill/
    ├── SKILL.md           # Main documentation
    └── references/        # Supporting docs
        ├── patterns.md
        └── examples.md
```

### SKILL.md Template

```markdown
# Skill Name

**Role**: Brief description

## Quick Reference
[Cheat sheet table]

## Knowledge Base
[Links to reference docs]

## Patterns
[Code patterns and examples]

## Integration
[How it works with other skills]
```

### Add Claude Code Shortcut

Create `.claude/skills/my-skill.md`:

```markdown
# My Skill

Brief description.

## Full Documentation
See: `skills/my-skill/SKILL.md`

## Quick Reference
[Essential patterns]

## Arguments
$ARGUMENTS
```

## Skill Architecture

```
User invokes /skill
    │
    ├─ Claude Code loads .claude/skills/skill.md
    │
    ├─ Skill references full SKILL.md if needed
    │
    ├─ Knowledge base provides context
    │   ├─ _knowledge/*.md (auto-updated)
    │   └─ references/*.md (manual docs)
    │
    └─ Skill may invoke other skills or agents
```

## Best Practices

1. **Keep shortcuts concise** - `.claude/skills/*.md` should be quick reference
2. **Full docs in SKILL.md** - Detailed patterns and examples
3. **Cross-reference** - Link skills that work together
4. **Update knowledge** - Run `scripts/update_consultant_knowledge.py` after major changes
5. **Test invocation** - Verify `/skill` works before committing
