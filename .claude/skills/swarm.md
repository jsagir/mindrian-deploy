# Swarm Orchestrator

Multi-agent coordination for complex queries.

## Full Documentation
See: `skills/swarm-orchestrator/SKILL.md`

## Quick Strategies

| Command | What It Does |
|---------|--------------|
| `/swarm <question>` | Auto-select strategy |
| `/swarm --quick <question>` | 2 agents, ~10s |
| `/swarm --research <question>` | Research first |
| `/swarm --stress <question>` | Debate with Red Team |
| `/swarm --full <question>` | All agents |

## Workflows

| Workflow | Agents |
|----------|--------|
| `--workflow quick` | Router picks 2 |
| `--workflow research` | Research → 3 agents |
| `--workflow stress-test` | Agent + Red Team |
| `--workflow full` | All + Research |
| `--workflow regression-hunt` | Commit + QA |
| `--workflow arch-review` | Stack + R&D |

## Usage

```
/swarm Should I pivot to B2B?
/swarm --strategy debate Is AI tutoring overhyped?
/swarm --workflow full Analyze healthcare AI opportunity
```

## Arguments
$ARGUMENTS
