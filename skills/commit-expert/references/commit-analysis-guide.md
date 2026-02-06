# Commit Analysis Guide

Advanced analysis patterns for the Commit Expert skill.

---

## File History Reconstruction

Trace the full history of a file to understand how it evolved.

### Commands

```bash
# Full file history with stats
git log --follow --stat -- <file>

# One-line history (compact)
git log --follow --oneline -- <file>

# Show who changed each line (blame)
git blame <file>

# Show a file at a specific commit
git show <hash>:<file>

# Diff a file between two commits
git diff <hash1>..<hash2> -- <file>
```

### Investigation Template

When asked "What happened to file X?":

1. **Get recent history**: `git log --follow -10 --pretty=format:"%h %ai %an | %s" -- <file>`
2. **Check for renames**: `git log --follow --diff-filter=R --name-status -- <file>`
3. **Find when it was created**: `git log --follow --diff-filter=A -- <file>`
4. **Check current blame**: `git blame --date=short <file> | head -20`

---

## Change Coupling Analysis

Find files that tend to change together (coupling indicates dependencies).

### Commands

```bash
# Files changed in the same commit as <file> (last 20 commits)
git log -20 --pretty=format:"%H" -- <file> | while read hash; do
  git diff-tree --no-commit-id --name-only -r $hash
done | sort | uniq -c | sort -rn | head -20

# Co-change frequency between two files
git log --pretty=format:"%H" -- <file1> | while read hash; do
  git diff-tree --no-commit-id --name-only -r $hash | grep -q "<file2>" && echo $hash
done | wc -l
```

### Interpretation

| Co-change Frequency | Meaning |
|---------------------|---------|
| >80% | Tightly coupled - changes in one almost always require changes in the other |
| 50-80% | Moderately coupled - often change together |
| 20-50% | Loosely coupled - sometimes related |
| <20% | Independent - rarely related |

### Common Coupling Patterns in Mindrian

| File A | File B | Why |
|--------|--------|-----|
| `prompts/*.py` | `prompts/__init__.py` | New prompts must be exported |
| `mindrian_chat.py` | `public/elements/*.jsx` | UI changes need backend wiring |
| `tools/*.py` | `mindrian_chat.py` | New tools need integration |
| `protocols/agent_registry.py` | `protocols/__init__.py` | New agents need export |

---

## Deployment Audit Template

When asked "What went into the deployment?" or "Audit the release":

### Step 1: Identify the Range

```bash
# Find the last deployment tag or known-good commit
git tag --sort=-creatordate | head -5

# Or find commits between dates
git log --after="2026-01-28" --before="2026-02-01" --oneline
```

### Step 2: List All Changes

```bash
# All commits in range
git log <from>..<to> --oneline --no-merges

# With stats
git log <from>..<to> --stat --no-merges

# Just file names (unique)
git diff <from>..<to> --name-only | sort -u
```

### Step 3: Risk Assessment

For each commit in the range, classify:

| Commit | Type | Risk | Critical Files? | Notes |
|--------|------|------|-----------------|-------|
| abc1234 | feat | High | mindrian_chat.py | New action handler |
| def5678 | fix | Medium | tools/tavily.py | API key handling |
| ghi9012 | docs | Low | -- | README update |

### Step 4: Summary Report

```markdown
## Deployment Audit: [date range]

**Commits:** X total (Y feat, Z fix, W other)
**Risk Level:** [High/Medium/Low]
**Critical Files Changed:** [list]
**Hot Files:** [files changed multiple times]

### High-Risk Changes
- [commit] [description] [why risky]

### Regression Watch
- [files/features to monitor post-deploy]
```

---

## Regression Investigation Template

When asked "Did commit X break something?" or "Find the regression":

### Step 1: Identify the Symptom

- What's broken? (specific behavior)
- When was it last working? (approximate date/commit)
- What's the affected file/feature?

### Step 2: Find Candidate Commits

```bash
# Commits touching the affected file since it last worked
git log --oneline <last-good>..<current> -- <affected-file>

# Or by date range
git log --after="2026-01-30" --oneline -- <affected-file>
```

### Step 3: Analyze Each Candidate

For each candidate commit:

```bash
# View the full diff
git show <hash> -- <affected-file>

# Check what else changed in the same commit
git diff-tree --no-commit-id --name-only -r <hash>

# Check the commit message for context
git log -1 --format="%B" <hash>
```

### Step 4: Bisect (if needed)

```bash
# Automated binary search for the breaking commit
git bisect start
git bisect bad HEAD
git bisect good <last-known-good>
# Test at each step, then:
git bisect good  # or git bisect bad
# When found:
git bisect reset
```

### Step 5: Report

```markdown
## Regression Report

**Symptom:** [what's broken]
**Root Cause Commit:** `<hash>` - [subject]
**Author:** [name]
**Date:** [date]
**Affected Files:** [list]
**Why It Broke:** [analysis of the diff]
**Fix:** [recommended action]
```

---

## Velocity Analysis Patterns

### Weekly Trend

```bash
# Commits per day for last 14 days
for i in $(seq 0 13); do
  date=$(date -d "$i days ago" +%Y-%m-%d)
  count=$(git log --after="$date 00:00" --before="$date 23:59" --oneline | wc -l)
  echo "$date: $count"
done
```

### Author Activity

```bash
# Commits per author (last 30 days)
git shortlog -sn --since="30 days ago" --no-merges
```

### Interpretation

| Velocity | Signal |
|----------|--------|
| >10/day | Sprint mode - watch for quality drops |
| 3-10/day | Normal active development |
| 1-3/day | Maintenance mode or deep work |
| <1/day | Slow period - check for blockers |
