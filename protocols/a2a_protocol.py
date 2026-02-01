"""
A2A Protocol - Agent-to-Agent Communication via Markdown Files

Enables structured handoffs between agents with:
- Human-readable markdown format
- Machine-parseable YAML frontmatter
- Context preservation across agent switches
- Task delegation and return flows

Author: Claude Code
Date: 2026-02-01
"""

import os
import json
import yaml
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class HandoffType(Enum):
    """Types of agent-to-agent handoffs."""
    SWITCH = "switch"      # User moves to different agent
    DELEGATE = "delegate"  # Agent asks another for help
    CONSULT = "consult"    # Quick question, expects immediate return
    RETURN = "return"      # Returning from delegation


class HandoffPriority(Enum):
    """Priority levels for handoffs."""
    URGENT = "urgent"      # Interrupt current work
    NORMAL = "normal"      # Process in order
    BACKGROUND = "background"  # When convenient


@dataclass
class ExtractedEntity:
    """An entity extracted from conversation."""
    type: str  # problem, stakeholder, assumption, constraint, opportunity
    value: str
    confidence: float = 0.8
    source_turn: int = 0


@dataclass
class ConversationHighlight:
    """A notable quote or moment from conversation."""
    quote: str
    speaker: str  # "user" or "assistant"
    turn: int
    significance: str = ""


@dataclass
class AgentTask:
    """A task for the receiving agent."""
    description: str
    completed: bool = False
    result: str = ""


@dataclass
class A2AHandoff:
    """
    Complete handoff document between agents.

    Can be serialized to/from Markdown with YAML frontmatter.
    """
    # Frontmatter (machine-readable)
    protocol_version: str = "a2a/v1"
    from_agent: str = ""
    to_agent: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str = ""
    handoff_type: HandoffType = HandoffType.SWITCH
    priority: HandoffPriority = HandoffPriority.NORMAL
    expects_return: bool = False
    return_to: str = ""  # Agent to return to after completion

    # Content sections
    context_summary: str = ""
    entities: List[ExtractedEntity] = field(default_factory=list)
    highlights: List[ConversationHighlight] = field(default_factory=list)
    tasks: List[AgentTask] = field(default_factory=list)

    # State preservation
    preserved_state: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict] = field(default_factory=list)

    # Return instructions (if expects_return)
    return_instructions: str = ""

    def to_markdown(self) -> str:
        """Serialize handoff to Markdown with YAML frontmatter."""
        # Build frontmatter
        frontmatter = {
            "protocol": self.protocol_version,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "handoff_type": self.handoff_type.value,
            "priority": self.priority.value,
            "expects_return": self.expects_return,
        }
        if self.return_to:
            frontmatter["return_to"] = self.return_to

        yaml_block = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        # Build markdown body
        md_parts = [
            f"---\n{yaml_block}---\n",
            f"# Agent Handoff: {self.from_agent} → {self.to_agent}\n",
        ]

        # Context summary
        if self.context_summary:
            md_parts.append(f"## Context Summary\n{self.context_summary}\n")

        # Entities
        if self.entities:
            md_parts.append("## Key Entities Extracted\n")
            for entity in self.entities:
                md_parts.append(f"- **{entity.type.title()}**: {entity.value}\n")
            md_parts.append("\n")

        # Highlights
        if self.highlights:
            md_parts.append("## Conversation Highlights\n")
            for h in self.highlights:
                md_parts.append(f"> \"{h.quote}\"\n> — {h.speaker.title()}, turn {h.turn}\n\n")

        # Tasks
        if self.tasks:
            md_parts.append("## Tasks for Receiving Agent\n")
            for task in self.tasks:
                checkbox = "[x]" if task.completed else "[ ]"
                md_parts.append(f"- {checkbox} {task.description}\n")
            md_parts.append("\n")

        # Preserved state
        if self.preserved_state:
            state_json = json.dumps(self.preserved_state, indent=2)
            md_parts.append(f"## Preserved State\n```json\n{state_json}\n```\n")

        # Return instructions
        if self.expects_return and self.return_instructions:
            md_parts.append(f"## Return Instructions\n{self.return_instructions}\n")

        return "\n".join(md_parts)

    @classmethod
    def from_markdown(cls, md_content: str) -> "A2AHandoff":
        """Parse handoff from Markdown with YAML frontmatter."""
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', md_content, re.DOTALL)
        if not frontmatter_match:
            raise ValueError("No YAML frontmatter found")

        frontmatter = yaml.safe_load(frontmatter_match.group(1))
        body = md_content[frontmatter_match.end():]

        handoff = cls(
            protocol_version=frontmatter.get("protocol", "a2a/v1"),
            from_agent=frontmatter.get("from_agent", ""),
            to_agent=frontmatter.get("to_agent", ""),
            timestamp=frontmatter.get("timestamp", ""),
            session_id=frontmatter.get("session_id", ""),
            handoff_type=HandoffType(frontmatter.get("handoff_type", "switch")),
            priority=HandoffPriority(frontmatter.get("priority", "normal")),
            expects_return=frontmatter.get("expects_return", False),
            return_to=frontmatter.get("return_to", ""),
        )

        # Parse context summary
        context_match = re.search(r'## Context Summary\n(.*?)(?=\n## |\Z)', body, re.DOTALL)
        if context_match:
            handoff.context_summary = context_match.group(1).strip()

        # Parse entities
        entities_match = re.search(r'## Key Entities Extracted\n(.*?)(?=\n## |\Z)', body, re.DOTALL)
        if entities_match:
            for line in entities_match.group(1).strip().split('\n'):
                entity_match = re.match(r'- \*\*(\w+)\*\*: (.+)', line)
                if entity_match:
                    handoff.entities.append(ExtractedEntity(
                        type=entity_match.group(1).lower(),
                        value=entity_match.group(2)
                    ))

        # Parse tasks
        tasks_match = re.search(r'## Tasks for Receiving Agent\n(.*?)(?=\n## |\Z)', body, re.DOTALL)
        if tasks_match:
            for line in tasks_match.group(1).strip().split('\n'):
                task_match = re.match(r'- \[([ x])\] (.+)', line)
                if task_match:
                    handoff.tasks.append(AgentTask(
                        description=task_match.group(2),
                        completed=(task_match.group(1) == 'x')
                    ))

        # Parse preserved state
        state_match = re.search(r'## Preserved State\n```json\n(.*?)\n```', body, re.DOTALL)
        if state_match:
            try:
                handoff.preserved_state = json.loads(state_match.group(1))
            except json.JSONDecodeError:
                pass

        # Parse return instructions
        return_match = re.search(r'## Return Instructions\n(.*?)(?=\n## |\Z)', body, re.DOTALL)
        if return_match:
            handoff.return_instructions = return_match.group(1).strip()

        return handoff


# === Handoff Storage ===

HANDOFF_DIR = "handoffs"


def get_handoff_path(session_id: str, handoff_id: str = None) -> str:
    """Get path for a handoff file."""
    os.makedirs(HANDOFF_DIR, exist_ok=True)
    if handoff_id:
        return os.path.join(HANDOFF_DIR, f"{session_id}_{handoff_id}.md")
    return os.path.join(HANDOFF_DIR, f"{session_id}_latest.md")


def save_handoff(handoff: A2AHandoff, handoff_id: str = None) -> str:
    """Save handoff to MD file."""
    path = get_handoff_path(handoff.session_id, handoff_id)
    with open(path, 'w') as f:
        f.write(handoff.to_markdown())

    # Also save as latest
    latest_path = get_handoff_path(handoff.session_id)
    with open(latest_path, 'w') as f:
        f.write(handoff.to_markdown())

    return path


def load_handoff(session_id: str, handoff_id: str = None) -> Optional[A2AHandoff]:
    """Load handoff from MD file."""
    path = get_handoff_path(session_id, handoff_id)
    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        return A2AHandoff.from_markdown(f.read())


def list_handoffs(session_id: str) -> List[str]:
    """List all handoff files for a session."""
    if not os.path.exists(HANDOFF_DIR):
        return []

    return [
        f for f in os.listdir(HANDOFF_DIR)
        if f.startswith(session_id) and f.endswith('.md')
    ]


# === Handoff Creation Helpers ===

async def create_switch_handoff(
    from_agent: str,
    to_agent: str,
    session_id: str,
    history: List[Dict],
    current_phase: int = 0,
    phases: List[Dict] = None,
    context_summary: str = None
) -> A2AHandoff:
    """
    Create a handoff for switching between agents.

    Extracts entities and highlights from conversation history.
    """
    handoff = A2AHandoff(
        from_agent=from_agent,
        to_agent=to_agent,
        session_id=session_id,
        handoff_type=HandoffType.SWITCH,
    )

    # Preserve state
    handoff.preserved_state = {
        "current_phase": current_phase,
        "turn_count": len(history) // 2,
    }
    if phases:
        completed = [p["name"] for p in phases if p.get("status") == "done"]
        handoff.preserved_state["phases_completed"] = completed

    # Store recent history (last 20 messages)
    handoff.conversation_history = history[-20:] if history else []

    # Extract entities using LangExtract if available
    try:
        from tools.langextract import instant_extract

        # Combine recent messages
        recent_text = " ".join([
            msg.get("content", "") for msg in history[-10:]
        ])

        signals = instant_extract(recent_text)

        # Convert to entities
        for problem in signals.get("problems", []):
            handoff.entities.append(ExtractedEntity(type="problem", value=problem))
        for assumption in signals.get("assumptions", []):
            handoff.entities.append(ExtractedEntity(type="assumption", value=assumption))
        for question in signals.get("questions", []):
            handoff.entities.append(ExtractedEntity(type="question", value=question))

    except ImportError:
        pass

    # Extract notable quotes
    for i, msg in enumerate(history[-10:]):
        content = msg.get("content", "")
        role = msg.get("role", "user")

        # Find sentences with strong signals
        if any(kw in content.lower() for kw in ["i think", "the problem is", "we need to", "my concern"]):
            # Extract first relevant sentence
            sentences = content.split('.')
            for s in sentences:
                if len(s) > 20 and len(s) < 200:
                    handoff.highlights.append(ConversationHighlight(
                        quote=s.strip(),
                        speaker="user" if role == "user" else "assistant",
                        turn=len(history) - 10 + i
                    ))
                    break

    # Generate context summary if not provided
    if not context_summary:
        if handoff.entities:
            problems = [e.value for e in handoff.entities if e.type == "problem"]
            if problems:
                handoff.context_summary = f"User is exploring: {problems[0]}"
            else:
                handoff.context_summary = "Conversation context preserved for continuation."
        else:
            handoff.context_summary = "Switching agents with conversation history."
    else:
        handoff.context_summary = context_summary

    return handoff


async def create_delegate_handoff(
    from_agent: str,
    to_agent: str,
    session_id: str,
    task_description: str,
    context: str,
    history: List[Dict] = None,
    expects_return: bool = True
) -> A2AHandoff:
    """
    Create a handoff for delegating a task to another agent.

    The delegating agent expects a response back.
    """
    handoff = A2AHandoff(
        from_agent=from_agent,
        to_agent=to_agent,
        session_id=session_id,
        handoff_type=HandoffType.DELEGATE,
        expects_return=expects_return,
        return_to=from_agent,
    )

    handoff.context_summary = context
    handoff.tasks.append(AgentTask(description=task_description))

    handoff.return_instructions = f"""
When task is complete, return to {from_agent} with:
- Task result or analysis
- Key findings
- Recommended next steps
"""

    if history:
        handoff.conversation_history = history[-10:]

    return handoff


async def create_return_handoff(
    from_agent: str,
    to_agent: str,
    session_id: str,
    original_handoff: A2AHandoff,
    results: str,
    completed_tasks: List[str] = None
) -> A2AHandoff:
    """
    Create a handoff for returning from a delegation.
    """
    handoff = A2AHandoff(
        from_agent=from_agent,
        to_agent=to_agent,
        session_id=session_id,
        handoff_type=HandoffType.RETURN,
    )

    handoff.context_summary = f"Returning from delegation.\n\n**Results:**\n{results}"

    # Mark tasks as completed
    if original_handoff and original_handoff.tasks:
        for task in original_handoff.tasks:
            if completed_tasks and task.description in completed_tasks:
                task.completed = True
                task.result = results
            handoff.tasks.append(task)

    # Preserve original state
    handoff.preserved_state = original_handoff.preserved_state if original_handoff else {}

    return handoff


# === Integration with mindrian_chat.py ===

def inject_handoff_context(handoff: A2AHandoff, system_prompt: str) -> str:
    """
    Inject handoff context into agent's system prompt.

    Returns modified system prompt with handoff awareness.
    """
    if not handoff:
        return system_prompt

    context_block = f"""

## Agent Handoff Context (A2A Protocol)

**Handed off from:** {handoff.from_agent}
**Handoff type:** {handoff.handoff_type.value}

### Context
{handoff.context_summary}

### Key Information
"""

    for entity in handoff.entities[:5]:
        context_block += f"- {entity.type.title()}: {entity.value}\n"

    if handoff.tasks:
        context_block += "\n### Your Tasks\n"
        for task in handoff.tasks:
            context_block += f"- {task.description}\n"

    if handoff.expects_return:
        context_block += f"\n### Return Instructions\n{handoff.return_instructions}\n"

    return system_prompt + context_block


def get_handoff_for_display(handoff: A2AHandoff) -> str:
    """
    Format handoff for user-facing display.
    """
    if not handoff:
        return ""

    parts = [f"───── 🔄 Handoff: {handoff.from_agent} → {handoff.to_agent} ─────\n"]

    if handoff.context_summary:
        parts.append(f"**Context:** {handoff.context_summary[:200]}\n")

    if handoff.entities:
        parts.append("\n**Carrying forward:**")
        for e in handoff.entities[:3]:
            parts.append(f"\n• {e.type.title()}: {e.value}")

    if handoff.tasks:
        parts.append("\n\n**Focus areas:**")
        for t in handoff.tasks[:3]:
            parts.append(f"\n• {t.description}")

    return "".join(parts)
