#!/usr/bin/env python3
"""
Update Mindrian Consultant Knowledge Base

Generates recent commit summaries for the consultant skills to reference.
Run automatically via post-commit hook or manually.
"""

import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# Paths
REPO_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "skills" / "_knowledge"
RECENT_CHANGES_FILE = KNOWLEDGE_DIR / "RECENT_CHANGES.md"
QA_CHANGES_FILE = KNOWLEDGE_DIR / "QA_RELEVANT_CHANGES.md"
RND_CHANGES_FILE = KNOWLEDGE_DIR / "RND_RELEVANT_CHANGES.md"
COMMIT_EXPERT_FILE = KNOWLEDGE_DIR / "COMMIT_EXPERT_CHANGES.md"

# Keywords for categorizing commits
QA_KEYWORDS = ["fix", "bug", "test", "qa", "issue", "error", "crash", "fail", "broken"]
RND_KEYWORDS = ["feat", "feature", "research", "experiment", "r&d", "prototype", "poc", "new", "add", "implement"]


def run_git_command(args: list[str]) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_current_branch() -> str:
    """Get the current git branch name."""
    return run_git_command(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"


def get_recent_commits(count: int = 50) -> list[dict]:
    """Get recent commits with details including parent hash and ref decorations."""
    # Format: hash|parent|subject|author|date|decorations|body
    log_format = "%H|%P|%s|%an|%ai|%D|%b"
    output = run_git_command([
        "log", f"-{count}", f"--pretty=format:{log_format}", "--no-merges"
    ])

    commits = []
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|", 6)
            if len(parts) >= 5:
                commits.append({
                    "hash": parts[0][:8],
                    "full_hash": parts[0],
                    "parent": parts[1].split()[0][:8] if parts[1] else "",
                    "subject": parts[2],
                    "author": parts[3],
                    "date": parts[4][:10],
                    "datetime": parts[4][:19],
                    "refs": parts[5] if len(parts) > 5 else "",
                    "body": parts[6] if len(parts) > 6 else ""
                })
    return commits


def get_changed_files(commit_hash: str) -> list[str]:
    """Get files changed in a commit."""
    output = run_git_command(["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash])
    return output.split("\n") if output else []


def get_diff_stats(commit_hash: str) -> list[dict]:
    """Get diff stats (insertions/deletions per file) for a commit."""
    output = run_git_command(["diff-tree", "--no-commit-id", "--numstat", "-r", commit_hash])
    stats = []
    if not output:
        return stats
    for line in output.split("\n"):
        parts = line.split("\t")
        if len(parts) == 3:
            added = parts[0] if parts[0] != "-" else "bin"
            deleted = parts[1] if parts[1] != "-" else "bin"
            stats.append({
                "file": parts[2],
                "added": added,
                "deleted": deleted,
            })
    return stats


def get_file_operations(commit_hash: str) -> list[dict]:
    """Get file operations (Added/Modified/Deleted/Renamed) for a commit."""
    output = run_git_command([
        "diff-tree", "--no-commit-id", "-r", "--diff-filter=ADMR", "--name-status", commit_hash
    ])
    ops = []
    if not output:
        return ops
    for line in output.split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            op_code = parts[0][0]  # First char: A, D, M, or R
            op_map = {"A": "Added", "D": "Deleted", "M": "Modified", "R": "Renamed"}
            ops.append({
                "operation": op_map.get(op_code, op_code),
                "file": parts[-1],  # Last element is the destination file for renames
            })
    return ops


def compute_hot_files(commits: list[dict], threshold: int = 3, window: int = 10) -> list[tuple]:
    """Find files changed 3+ times in the last N commits. Returns [(file, count)]."""
    recent = commits[:window]
    file_counts = Counter()
    for commit in recent:
        files = get_changed_files(commit["hash"])
        for f in files:
            if not f.startswith(".") and not f.startswith("skills/_knowledge/"):
                file_counts[f] += 1
    return [(f, c) for f, c in file_counts.most_common() if c >= threshold]


def compute_velocity(commits: list[dict], days: int = 7) -> dict:
    """Compute commits per day over the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent = [c for c in commits if c["date"] >= cutoff]

    by_day = Counter()
    for c in recent:
        by_day[c["date"]] += 1

    total = len(recent)
    avg = round(total / days, 1) if days > 0 else 0

    return {
        "total": total,
        "days": days,
        "avg_per_day": avg,
        "by_day": dict(sorted(by_day.items(), reverse=True)),
    }


def categorize_commit(commit: dict, files: list[str]) -> dict:
    """Categorize commit as QA-relevant, R&D-relevant, or both."""
    subject_lower = commit["subject"].lower()

    is_qa = any(kw in subject_lower for kw in QA_KEYWORDS)
    is_rnd = any(kw in subject_lower for kw in RND_KEYWORDS)

    # Check file paths for additional categorization
    qa_paths = ["qa/", "test", "fix"]
    rnd_paths = ["r&d/", "research", "tools/", "agents/", "prompts/"]

    for f in files:
        f_lower = f.lower()
        if any(p in f_lower for p in qa_paths):
            is_qa = True
        if any(p in f_lower for p in rnd_paths):
            is_rnd = True

    return {"qa": is_qa, "rnd": is_rnd}


def get_commit_icon(subject: str) -> str:
    """Get icon based on commit type."""
    subject_lower = subject.lower()
    if subject_lower.startswith("fix"):
        return "🐛"
    elif subject_lower.startswith("feat"):
        return "✨"
    elif subject_lower.startswith("refactor"):
        return "♻️"
    elif subject_lower.startswith("docs"):
        return "📝"
    elif subject_lower.startswith("test"):
        return "🧪"
    else:
        return "🔧"


def get_commit_risk(subject: str) -> str:
    """Classify commit risk level based on type."""
    subject_lower = subject.lower()
    if subject_lower.startswith("fix"):
        return "medium"
    elif subject_lower.startswith("feat"):
        return "high"
    elif subject_lower.startswith("refactor"):
        return "high"
    elif subject_lower.startswith("docs"):
        return "low"
    elif subject_lower.startswith("test"):
        return "low"
    else:
        return "medium"


def generate_markdown_summary(commits: list[dict], title: str, filter_type: str = None) -> str:
    """Generate markdown summary of commits."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# {title}",
        f"",
        f"*Auto-generated: {now}*",
        f"",
        f"---",
        f"",
    ]

    # Group by date
    by_date = {}
    for commit in commits:
        files = get_changed_files(commit["hash"])
        category = categorize_commit(commit, files)

        # Filter if needed
        if filter_type == "qa" and not category["qa"]:
            continue
        if filter_type == "rnd" and not category["rnd"]:
            continue

        date = commit["date"]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append({**commit, "files": files, "category": category})

    if not by_date:
        lines.append("*No relevant changes found.*")
        return "\n".join(lines)

    for date in sorted(by_date.keys(), reverse=True):
        lines.append(f"## {date}")
        lines.append("")

        for c in by_date[date]:
            icon = get_commit_icon(c["subject"])

            lines.append(f"### {icon} {c['subject']}")
            lines.append(f"")
            lines.append(f"- **Commit:** `{c['hash']}`")
            lines.append(f"- **Author:** {c['author']}")

            if c["files"]:
                lines.append(f"- **Files changed:** {len(c['files'])}")
                # Show key files (limit to 5)
                key_files = [f for f in c["files"] if not f.startswith(".")][:5]
                if key_files:
                    lines.append(f"  - " + "\n  - ".join(key_files))

            if c["body"]:
                lines.append(f"- **Details:** {c['body'][:200]}")

            lines.append("")

    return "\n".join(lines)


def generate_expert_summary(commits: list[dict]) -> str:
    """Generate enriched commit expert knowledge file with velocity, hot files, and per-commit details."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    branch = get_current_branch()

    lines = [
        "# Commit Expert Intelligence",
        "",
        f"*Auto-generated: {now}*",
        "",
        f"**Current Branch:** `{branch}`",
        "",
        "---",
        "",
    ]

    # --- Velocity Section ---
    velocity = compute_velocity(commits)
    lines.append("## Change Velocity (Last 7 Days)")
    lines.append("")
    lines.append(f"- **Total commits:** {velocity['total']}")
    lines.append(f"- **Average per day:** {velocity['avg_per_day']}")
    lines.append("")
    if velocity["by_day"]:
        lines.append("| Date | Commits |")
        lines.append("|------|---------|")
        for date, count in velocity["by_day"].items():
            lines.append(f"| {date} | {count} |")
        lines.append("")

    # --- Hot Files Section ---
    hot_files = compute_hot_files(commits)
    lines.append("## Hot Files (Changed 3+ Times in Last 10 Commits)")
    lines.append("")
    if hot_files:
        lines.append("| File | Changes |")
        lines.append("|------|---------|")
        for f, count in hot_files:
            lines.append(f"| `{f}` | {count} |")
    else:
        lines.append("*No hot files detected.*")
    lines.append("")

    # --- Per-Commit Enriched Entries ---
    lines.append("---")
    lines.append("")
    lines.append("## Enriched Commit Log")
    lines.append("")

    # Group by date
    by_date = {}
    for commit in commits:
        date = commit["date"]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(commit)

    for date in sorted(by_date.keys(), reverse=True):
        lines.append(f"### {date}")
        lines.append("")

        for c in by_date[date]:
            icon = get_commit_icon(c["subject"])
            risk = get_commit_risk(c["subject"])

            lines.append(f"#### {icon} {c['subject']}")
            lines.append("")
            lines.append(f"- **Hash:** `{c['full_hash']}`")
            lines.append(f"- **Short:** `{c['hash']}`")
            if c.get("parent"):
                lines.append(f"- **Parent:** `{c['parent']}`")
            lines.append(f"- **Branch:** `{branch}`")
            if c.get("refs"):
                lines.append(f"- **Refs:** {c['refs']}")
            lines.append(f"- **Author:** {c['author']}")
            lines.append(f"- **Date:** {c.get('datetime', c['date'])}")
            lines.append(f"- **Risk:** {risk}")

            # Diff stats
            stats = get_diff_stats(c["hash"])
            if stats:
                total_added = sum(int(s["added"]) for s in stats if s["added"] != "bin")
                total_deleted = sum(int(s["deleted"]) for s in stats if s["deleted"] != "bin")
                lines.append(f"- **Diff:** +{total_added} / -{total_deleted}")
                lines.append("")
                lines.append("  | File | +Lines | -Lines |")
                lines.append("  |------|--------|--------|")
                for s in stats[:10]:  # Limit to 10 files
                    lines.append(f"  | `{s['file']}` | {s['added']} | {s['deleted']} |")
                lines.append("")

            # File operations
            ops = get_file_operations(c["hash"])
            if ops:
                lines.append("  **File Operations:**")
                for op in ops:
                    op_icon = {"Added": "➕", "Deleted": "➖", "Modified": "✏️", "Renamed": "🔄"}.get(op["operation"], "❓")
                    lines.append(f"  - {op_icon} {op['operation']}: `{op['file']}`")
                lines.append("")

            if c.get("body"):
                lines.append(f"- **Body:** {c['body'][:300]}")
                lines.append("")

            lines.append("")

    return "\n".join(lines)


def update_knowledge_base():
    """Update all knowledge files."""
    # Ensure directory exists
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    commits = get_recent_commits(50)

    if not commits:
        print("No commits found")
        return

    # Generate all changes summary
    all_summary = generate_markdown_summary(commits, "Recent Repository Changes")
    RECENT_CHANGES_FILE.write_text(all_summary)
    print(f"✅ Updated {RECENT_CHANGES_FILE}")

    # Generate QA-relevant changes
    qa_summary = generate_markdown_summary(commits, "QA-Relevant Changes", filter_type="qa")
    QA_CHANGES_FILE.write_text(qa_summary)
    print(f"✅ Updated {QA_CHANGES_FILE}")

    # Generate R&D-relevant changes
    rnd_summary = generate_markdown_summary(commits, "R&D-Relevant Changes", filter_type="rnd")
    RND_CHANGES_FILE.write_text(rnd_summary)
    print(f"✅ Updated {RND_CHANGES_FILE}")

    # Generate commit expert intelligence
    expert_summary = generate_expert_summary(commits)
    COMMIT_EXPERT_FILE.write_text(expert_summary)
    print(f"✅ Updated {COMMIT_EXPERT_FILE}")

    print(f"\n📊 Processed {len(commits)} commits")


if __name__ == "__main__":
    update_knowledge_base()
