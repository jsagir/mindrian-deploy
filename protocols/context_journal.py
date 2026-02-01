"""
Context Journal - Living Markdown Document for Conversation Context

Creates and maintains a running MD file that evolves alongside the conversation.
Each agent can read from and append to this journal, creating a shared context.

Features:
- Thinking steps logged as the conversation progresses
- Key extractions appended automatically
- Agent switches recorded
- Can be shown to user as "what we've figured out"

Author: Claude Code
Date: 2026-02-01
"""

import os
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json


JOURNAL_DIR = "journals"


@dataclass
class ThinkingStep:
    """A reasoning step from an agent."""
    agent: str
    step_type: str  # "observation", "reasoning", "decision", "action", "insight"
    content: str
    timestamp: str = ""
    turn: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().strftime("%H:%M:%S")


class ContextJournal:
    """
    A living markdown document that tracks conversation context.

    Can be appended to via Python or Bash, and read by any agent.
    """

    def __init__(self, session_id: str, user_id: str = "anonymous"):
        self.session_id = session_id
        self.user_id = user_id
        self.file_path = self._get_journal_path()
        self._ensure_journal_exists()

    def _get_journal_path(self) -> str:
        """Get path to journal file."""
        os.makedirs(JOURNAL_DIR, exist_ok=True)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return os.path.join(JOURNAL_DIR, f"{date_str}_{self.session_id}.md")

    def _ensure_journal_exists(self):
        """Create journal with header if it doesn't exist."""
        if not os.path.exists(self.file_path):
            header = f"""# Conversation Journal

**Session:** {self.session_id}
**Started:** {datetime.utcnow().isoformat()}
**User:** {self.user_id}

---

"""
            with open(self.file_path, 'w') as f:
                f.write(header)

    # === Core Methods ===

    def append(self, content: str, section: str = None):
        """Append content to the journal."""
        with open(self.file_path, 'a') as f:
            if section:
                f.write(f"\n## {section}\n")
            f.write(f"{content}\n")

    def append_thinking_step(self, step: ThinkingStep):
        """Append a thinking step to the journal."""
        emoji_map = {
            "observation": "👁️",
            "reasoning": "🧠",
            "decision": "✅",
            "action": "⚡",
            "insight": "💡",
        }
        emoji = emoji_map.get(step.step_type, "📝")

        entry = f"\n### {emoji} {step.step_type.title()} ({step.agent}) — Turn {step.turn}\n"
        entry += f"*{step.timestamp}*\n\n"
        entry += f"{step.content}\n"

        with open(self.file_path, 'a') as f:
            f.write(entry)

    def read_all(self) -> str:
        """Read entire journal content."""
        if not os.path.exists(self.file_path):
            return ""
        with open(self.file_path, 'r') as f:
            return f.read()

    def read_last_n_lines(self, n: int = 50) -> str:
        """Read last N lines of journal (for context injection)."""
        try:
            result = subprocess.run(
                ['tail', '-n', str(n), self.file_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout
        except Exception:
            # Fallback to Python
            content = self.read_all()
            lines = content.split('\n')
            return '\n'.join(lines[-n:])

    def get_summary(self) -> str:
        """Get a summary of key journal entries."""
        content = self.read_all()

        # Extract sections with 💡 (insights) and ✅ (decisions)
        lines = content.split('\n')
        key_entries = []

        in_key_section = False
        current_section = []

        for line in lines:
            if '💡' in line or '✅' in line:
                in_key_section = True
                current_section = [line]
            elif in_key_section:
                if line.startswith('### ') or line.startswith('## '):
                    key_entries.append('\n'.join(current_section))
                    in_key_section = False
                    current_section = []
                else:
                    current_section.append(line)

        if current_section:
            key_entries.append('\n'.join(current_section))

        return '\n\n'.join(key_entries[-5:])  # Last 5 key entries

    # === Structured Logging ===

    def log_agent_switch(self, from_agent: str, to_agent: str, reason: str = ""):
        """Log an agent switch."""
        entry = f"\n---\n\n## 🔄 Agent Switch: {from_agent} → {to_agent}\n"
        entry += f"*{datetime.utcnow().strftime('%H:%M:%S')}*\n\n"
        if reason:
            entry += f"**Reason:** {reason}\n"
        entry += "\n---\n"

        with open(self.file_path, 'a') as f:
            f.write(entry)

    def log_extraction(self, agent: str, extractions: Dict[str, List[str]]):
        """Log extracted entities."""
        entry = f"\n### 📋 Extractions ({agent})\n"

        for category, items in extractions.items():
            if items:
                entry += f"\n**{category.title()}:**\n"
                for item in items[:5]:
                    entry += f"- {item}\n"

        with open(self.file_path, 'a') as f:
            f.write(entry)

    def log_phase_transition(self, phase_from: str, phase_to: str, evidence: List[str] = None):
        """Log a phase transition."""
        entry = f"\n### 📍 Phase: {phase_from} → {phase_to}\n"
        entry += f"*{datetime.utcnow().strftime('%H:%M:%S')}*\n\n"

        if evidence:
            entry += "**Evidence of completion:**\n"
            for e in evidence[:3]:
                entry += f"- {e}\n"

        with open(self.file_path, 'a') as f:
            f.write(entry)

    def log_user_insight(self, insight: str, turn: int):
        """Log a notable user statement."""
        entry = f"\n> 💬 \"{insight}\"\n> — User, turn {turn}\n\n"

        with open(self.file_path, 'a') as f:
            f.write(entry)

    def log_decision(self, agent: str, decision: str, reasoning: str = ""):
        """Log an agent decision."""
        step = ThinkingStep(
            agent=agent,
            step_type="decision",
            content=f"**Decision:** {decision}\n\n{reasoning}" if reasoning else decision
        )
        self.append_thinking_step(step)

    def log_insight(self, agent: str, insight: str):
        """Log an insight or realization."""
        step = ThinkingStep(
            agent=agent,
            step_type="insight",
            content=insight
        )
        self.append_thinking_step(step)

    # === Bash Integration ===

    def append_via_bash(self, content: str) -> bool:
        """Append to journal using bash (for subprocess calls)."""
        try:
            # Escape content for bash
            escaped = content.replace("'", "'\"'\"'")
            cmd = f"echo '{escaped}' >> '{self.file_path}'"

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Bash append failed: {e}")
            return False

    def grep_pattern(self, pattern: str) -> List[str]:
        """Search journal for pattern using grep."""
        try:
            result = subprocess.run(
                ['grep', '-i', pattern, self.file_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip().split('\n') if result.stdout else []
        except Exception:
            return []

    # === Context for Agents ===

    def get_context_for_agent(self, agent: str, max_chars: int = 2000) -> str:
        """
        Get relevant journal context for an agent.

        Returns a focused summary suitable for injecting into prompts.
        """
        content = self.read_all()

        # Get key sections
        sections = []

        # Recent agent switches
        switches = self.grep_pattern("Agent Switch")
        if switches:
            sections.append("**Recent handoffs:** " + switches[-1] if switches[-1] else "")

        # Key insights
        summary = self.get_summary()
        if summary:
            sections.append(f"**Key insights:**\n{summary[:500]}")

        # Build context block
        context = "\n\n".join([s for s in sections if s])

        if len(context) > max_chars:
            context = context[:max_chars] + "..."

        return context


# === Session Journal Manager ===

_journals: Dict[str, ContextJournal] = {}


def get_journal(session_id: str, user_id: str = "anonymous") -> ContextJournal:
    """Get or create journal for session."""
    if session_id not in _journals:
        _journals[session_id] = ContextJournal(session_id, user_id)
    return _journals[session_id]


def clear_journal_cache():
    """Clear in-memory journal cache."""
    _journals.clear()


# === Convenience Functions ===

def log_thinking(
    session_id: str,
    agent: str,
    step_type: str,
    content: str,
    turn: int = 0
):
    """Quick function to log a thinking step."""
    journal = get_journal(session_id)
    step = ThinkingStep(
        agent=agent,
        step_type=step_type,
        content=content,
        turn=turn
    )
    journal.append_thinking_step(step)


def log_switch(session_id: str, from_agent: str, to_agent: str, reason: str = ""):
    """Quick function to log an agent switch."""
    journal = get_journal(session_id)
    journal.log_agent_switch(from_agent, to_agent, reason)


def inject_journal_context(session_id: str, system_prompt: str, agent: str) -> str:
    """Inject journal context into agent's system prompt."""
    journal = get_journal(session_id)
    context = journal.get_context_for_agent(agent)

    if not context:
        return system_prompt

    return system_prompt + f"""

## Conversation Journal Context
The following context was accumulated during this session:

{context}
"""


# === UI Integration ===

def get_journal_entries_for_ui(session_id: str, limit: int = 20) -> List[Dict]:
    """
    Get journal entries formatted for JournalViewer component.

    Returns list of dicts with: type, agent, content, timestamp, turn
    """
    journal = get_journal(session_id)
    content = journal.read_all()

    entries = []
    lines = content.split('\n')

    current_entry = None

    for line in lines:
        # Detect entry headers
        if line.startswith('### '):
            # Save previous entry
            if current_entry:
                entries.append(current_entry)

            # Parse new entry header
            # Format: ### 💡 Insight (Lawrence) — Turn 5
            import re
            match = re.match(r'### .+ (\w+) \((\w+)\)(?: — Turn (\d+))?', line)
            if match:
                current_entry = {
                    'type': match.group(1).lower(),
                    'agent': match.group(2),
                    'turn': int(match.group(3)) if match.group(3) else 0,
                    'content': '',
                    'timestamp': ''
                }
            elif '🔄 Agent Switch' in line:
                # Handle agent switch entries
                switch_match = re.search(r'(\w+) → (\w+)', line)
                if switch_match:
                    current_entry = {
                        'type': 'switch',
                        'agent': f"{switch_match.group(1)} → {switch_match.group(2)}",
                        'turn': 0,
                        'content': 'Agent handoff',
                        'timestamp': ''
                    }
        elif current_entry:
            # Parse timestamp
            if line.startswith('*') and line.endswith('*') and ':' in line:
                current_entry['timestamp'] = line.strip('*')
            # Add content (skip empty lines and metadata)
            elif line.strip() and not line.startswith('**') and not line.startswith('>'):
                if current_entry['content']:
                    current_entry['content'] += ' ' + line.strip()
                else:
                    current_entry['content'] = line.strip()

    # Add final entry
    if current_entry:
        entries.append(current_entry)

    # Return most recent entries
    return entries[-limit:]


async def create_journal_viewer_element(session_id: str):
    """
    Create a Chainlit CustomElement for the JournalViewer.

    Returns the element ready to be sent/updated.
    """
    try:
        import chainlit as cl

        entries = get_journal_entries_for_ui(session_id)

        return cl.CustomElement(
            name="JournalViewer",
            props={
                "entries": entries,
                "sessionId": session_id,
                "isExpanded": False,
                "lastUpdated": datetime.utcnow().strftime("%H:%M:%S"),
            },
            display="side"
        )
    except ImportError:
        return None


# === Export for mindrian_chat.py ===

__all__ = [
    'ContextJournal',
    'ThinkingStep',
    'get_journal',
    'log_thinking',
    'log_switch',
    'inject_journal_context',
    'get_journal_entries_for_ui',
    'create_journal_viewer_element',
]
