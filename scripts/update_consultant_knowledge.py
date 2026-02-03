#!/usr/bin/env python3
"""
Update Mindrian Consultant Knowledge Base

Generates recent commit summaries for the consultant skills to reference.
Run automatically via post-commit hook or manually.
"""

import subprocess
import os
from datetime import datetime
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "skills" / "_knowledge"
RECENT_CHANGES_FILE = KNOWLEDGE_DIR / "RECENT_CHANGES.md"
QA_CHANGES_FILE = KNOWLEDGE_DIR / "QA_RELEVANT_CHANGES.md"
RND_CHANGES_FILE = KNOWLEDGE_DIR / "RND_RELEVANT_CHANGES.md"

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


def get_recent_commits(count: int = 50) -> list[dict]:
    """Get recent commits with details."""
    # Format: hash|subject|author|date|body
    log_format = "%H|%s|%an|%ai|%b"
    output = run_git_command([
        "log", f"-{count}", f"--pretty=format:{log_format}", "--no-merges"
    ])

    commits = []
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|", 4)
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0][:8],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3][:10],
                    "body": parts[4] if len(parts) > 4 else ""
                })
    return commits


def get_changed_files(commit_hash: str) -> list[str]:
    """Get files changed in a commit."""
    output = run_git_command(["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash])
    return output.split("\n") if output else []


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
            # Icon based on type
            if c["subject"].lower().startswith("fix"):
                icon = "🐛"
            elif c["subject"].lower().startswith("feat"):
                icon = "✨"
            elif c["subject"].lower().startswith("refactor"):
                icon = "♻️"
            elif c["subject"].lower().startswith("docs"):
                icon = "📝"
            elif c["subject"].lower().startswith("test"):
                icon = "🧪"
            else:
                icon = "🔧"

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

    print(f"\n📊 Processed {len(commits)} commits")


if __name__ == "__main__":
    update_knowledge_base()
