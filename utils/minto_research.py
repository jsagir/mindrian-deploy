"""
Minto Pyramid + Sequential Thinking Research Planning

Implements PWS methodology for structured research:
1. SCQA Analysis (Situation, Complication, Question, Answer)
2. Sequential Thinking with revision/branching
3. Targeted research execution
4. Pyramid synthesis

Based on Barbara Minto's Pyramid Principle and PWS validation methodology.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ThoughtType(Enum):
    STANDARD = "standard"      # 💭 Normal thought
    REVISION = "revision"      # 🔄 Reconsidering previous thought
    BRANCH = "branch"          # 🌿 Alternative path


@dataclass
class BeautifulQuestions:
    """
    Warren Berger's "A More Beautiful Question" Framework.

    Three-stage questioning process for innovation:
    - WHY: Challenge the status quo, understand root causes
    - WHAT IF: Explore possibilities, reimagine scenarios
    - HOW: Actionable steps, practical implementation
    """
    why_questions: List[str]       # Why does this exist? Why is it a problem?
    what_if_questions: List[str]   # What if we...? What would happen if...?
    how_questions: List[str]       # How might we...? How could we test...?

    def to_prompt(self) -> str:
        """Format for LLM consumption."""
        lines = ["## Beautiful Questions (Berger Framework)\n"]

        lines.append("### 🔴 WHY Questions (Challenge assumptions)")
        for q in self.why_questions:
            lines.append(f"- {q}")

        lines.append("\n### 🟡 WHAT IF Questions (Explore possibilities)")
        for q in self.what_if_questions:
            lines.append(f"- {q}")

        lines.append("\n### 🟢 HOW Questions (Actionable inquiry)")
        for q in self.how_questions:
            lines.append(f"- {q}")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "why": self.why_questions,
            "what_if": self.what_if_questions,
            "how": self.how_questions
        }

    def get_all_questions(self) -> List[Dict[str, str]]:
        """Return all questions with their types for research targeting."""
        questions = []
        for q in self.why_questions:
            questions.append({"question": q, "type": "why", "label": "🔴 WHY"})
        for q in self.what_if_questions:
            questions.append({"question": q, "type": "what_if", "label": "🟡 WHAT IF"})
        for q in self.how_questions:
            questions.append({"question": q, "type": "how", "label": "🟢 HOW"})
        return questions


@dataclass
class SCQAAnalysis:
    """Minto SCQA Framework for structuring the research need."""
    situation: str           # Current state - what reader knows
    complication: str        # What tension/problem emerged
    question: str            # Specific question to answer
    answer_hypothesis: str   # Expected answer (to validate)
    confidence: float = 0.5  # 0-1 confidence in hypothesis

    def to_prompt(self) -> str:
        """Format for LLM consumption."""
        return f"""## SCQA Analysis (Minto Pyramid)

**SITUATION** (Current State):
{self.situation}

**COMPLICATION** (Problem/Tension):
{self.complication}

**QUESTION** (What needs answering):
{self.question}

**ANSWER HYPOTHESIS** (What we expect - confidence: {self.confidence:.0%}):
{self.answer_hypothesis}
"""

    def to_dict(self) -> Dict:
        return {
            "situation": self.situation,
            "complication": self.complication,
            "question": self.question,
            "answer_hypothesis": self.answer_hypothesis,
            "confidence": self.confidence
        }


@dataclass
class Thought:
    """A single thought in the sequential thinking process."""
    number: int
    content: str
    thought_type: ThoughtType = ThoughtType.STANDARD
    revises_thought: Optional[int] = None  # For revisions
    branch_id: Optional[str] = None        # For branches
    branch_from: Optional[int] = None      # Which thought this branches from
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def prefix(self) -> str:
        """Visual prefix for the thought type."""
        if self.thought_type == ThoughtType.REVISION:
            return "🔄"
        elif self.thought_type == ThoughtType.BRANCH:
            return "🌿"
        return "💭"

    def to_dict(self) -> Dict:
        return {
            "number": self.number,
            "content": self.content,
            "type": self.thought_type.value,
            "revises_thought": self.revises_thought,
            "branch_id": self.branch_id,
            "branch_from": self.branch_from,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ResearchPlan:
    """Structured research plan derived from sequential thinking."""
    known_knowns: List[str]           # What we already know
    known_unknowns: List[str]         # What we need to find out
    assumptions: List[str]            # Assumptions to validate
    validation_queries: List[str]     # Camera Test - observable evidence
    supporting_queries: List[str]     # Evidence FOR hypothesis
    challenging_queries: List[str]    # Evidence AGAINST (Red Team)
    context_queries: List[str]        # Background/market context

    def get_all_queries(self) -> List[Dict[str, str]]:
        """Return all queries with their types."""
        queries = []
        for q in self.validation_queries:
            queries.append({"query": q, "type": "validation", "label": "📊 Validation"})
        for q in self.supporting_queries:
            queries.append({"query": q, "type": "supporting", "label": "✅ Supporting"})
        for q in self.challenging_queries:
            queries.append({"query": q, "type": "challenging", "label": "⚠️ Challenging"})
        for q in self.context_queries:
            queries.append({"query": q, "type": "context", "label": "📚 Context"})
        return queries

    def to_dict(self) -> Dict:
        return {
            "known_knowns": self.known_knowns,
            "known_unknowns": self.known_unknowns,
            "assumptions": self.assumptions,
            "queries": {
                "validation": self.validation_queries,
                "supporting": self.supporting_queries,
                "challenging": self.challenging_queries,
                "context": self.context_queries
            }
        }


@dataclass
class SequentialThinkingSession:
    """Manages the sequential thinking process for research planning."""
    session_id: str
    scqa: Optional[SCQAAnalysis] = None
    beautiful_questions: Optional[BeautifulQuestions] = None  # Why/What If/How
    thoughts: List[Thought] = field(default_factory=list)
    branches: Dict[str, List[Thought]] = field(default_factory=dict)
    research_plan: Optional[ResearchPlan] = None
    total_thoughts_estimated: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_thought(self, content: str) -> Thought:
        """Add a standard thought."""
        thought = Thought(
            number=len(self.thoughts) + 1,
            content=content,
            thought_type=ThoughtType.STANDARD
        )
        self.thoughts.append(thought)
        return thought

    def add_revision(self, content: str, revises: int) -> Thought:
        """Add a revision to a previous thought."""
        thought = Thought(
            number=len(self.thoughts) + 1,
            content=content,
            thought_type=ThoughtType.REVISION,
            revises_thought=revises
        )
        self.thoughts.append(thought)
        return thought

    def add_branch(self, content: str, branch_id: str, branch_from: int) -> Thought:
        """Add a branching thought (alternative path)."""
        thought = Thought(
            number=len(self.thoughts) + 1,
            content=content,
            thought_type=ThoughtType.BRANCH,
            branch_id=branch_id,
            branch_from=branch_from
        )
        self.thoughts.append(thought)

        if branch_id not in self.branches:
            self.branches[branch_id] = []
        self.branches[branch_id].append(thought)

        return thought

    def needs_more_thoughts(self) -> bool:
        """Check if we need more thinking."""
        return len(self.thoughts) < self.total_thoughts_estimated

    def adjust_estimate(self, new_estimate: int):
        """Dynamically adjust thought estimate."""
        self.total_thoughts_estimated = new_estimate

    def to_markdown(self) -> str:
        """Export session as readable markdown."""
        lines = [
            "# Sequential Thinking Session",
            f"*Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}*",
            ""
        ]

        if self.scqa:
            lines.append(self.scqa.to_prompt())
            lines.append("")

        lines.append("## Thinking Process")
        lines.append("")

        for thought in self.thoughts:
            prefix = thought.prefix
            type_note = ""
            if thought.thought_type == ThoughtType.REVISION:
                type_note = f" *(revises thought {thought.revises_thought})*"
            elif thought.thought_type == ThoughtType.BRANCH:
                type_note = f" *(branch {thought.branch_id} from thought {thought.branch_from})*"

            lines.append(f"### {prefix} Thought {thought.number}{type_note}")
            lines.append(thought.content)
            lines.append("")

        if self.research_plan:
            lines.append("## Research Plan")
            lines.append("")
            lines.append("### Known Knowns")
            for item in self.research_plan.known_knowns:
                lines.append(f"- {item}")
            lines.append("")
            lines.append("### Known Unknowns (Research Targets)")
            for item in self.research_plan.known_unknowns:
                lines.append(f"- {item}")
            lines.append("")
            lines.append("### Assumptions to Validate")
            for item in self.research_plan.assumptions:
                lines.append(f"- {item}")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "scqa": self.scqa.to_dict() if self.scqa else None,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "branches": {k: [t.to_dict() for t in v] for k, v in self.branches.items()},
            "research_plan": self.research_plan.to_dict() if self.research_plan else None,
            "total_thoughts_estimated": self.total_thoughts_estimated,
            "created_at": self.created_at.isoformat()
        }


# === LLM Prompts for Sequential Thinking ===

BEAUTIFUL_QUESTIONS_PROMPT = """You are generating "Beautiful Questions" based on Warren Berger's framework from "A More Beautiful Question".

Given this SCQA analysis, generate powerful questions in three categories:

SCQA ANALYSIS:
{scqa}

CONVERSATION CONTEXT:
{context}

Generate questions that could drive breakthrough thinking and research:

1. **WHY Questions** (2-3): Challenge assumptions, understand root causes
   - Why does this situation exist?
   - Why hasn't this been solved before?
   - Why do we assume X is true?

2. **WHAT IF Questions** (2-3): Explore possibilities, reimagine scenarios
   - What if we approached this completely differently?
   - What if the opposite were true?
   - What if we combined X with Y?

3. **HOW Questions** (2-3): Actionable inquiry, practical implementation
   - How might we test this assumption?
   - How could we validate this with data?
   - How would we know if we're wrong?

Format as JSON:
```json
{{
    "why_questions": [
        "Why does...?",
        "Why hasn't...?"
    ],
    "what_if_questions": [
        "What if...?",
        "What would happen if...?"
    ],
    "how_questions": [
        "How might we...?",
        "How could we...?"
    ]
}}
```

Make questions specific to the SCQA analysis, not generic. Each question should be actionable and researchable."""


SCQA_ANALYSIS_PROMPT = """You are analyzing a conversation to identify what research is needed using Barbara Minto's SCQA framework.

CONVERSATION CONTEXT:
{context}

CURRENT BOT/WORKSHOP: {bot_name}

Analyze this conversation and extract:

1. **SITUATION**: What is the current state? What does the user know or believe? What's the starting point?

2. **COMPLICATION**: What problem, tension, or gap has emerged? What changed or what obstacle appeared?

3. **QUESTION**: What specific question needs to be answered through research? Be precise and focused.

4. **ANSWER HYPOTHESIS**: Based on the conversation, what answer do we expect to find? This is our hypothesis to validate.

5. **CONFIDENCE**: How confident are we in this hypothesis? (0.0 = complete uncertainty, 1.0 = highly confident)

Format your response as JSON:
```json
{{
    "situation": "...",
    "complication": "...",
    "question": "...",
    "answer_hypothesis": "...",
    "confidence": 0.X
}}
```"""


SEQUENTIAL_THINKING_PROMPT = """You are conducting sequential thinking to plan research based on this analysis:

{scqa}

{beautiful_questions}

Think through the research need step by step, incorporating the Beautiful Questions above. For each thought:
- Build on previous thoughts
- You may REVISE a previous thought if you realize it was incomplete or wrong
- You may BRANCH to explore alternative angles (especially for WHY vs WHAT IF perspectives)

Generate exactly {num_thoughts} thoughts covering:
1. What do we KNOW already? (Known Knowns) - informed by WHY questions
2. What do we NEED TO KNOW? (Known Unknowns) - informed by WHAT IF questions
3. What ASSUMPTIONS are we making that need validation? - challenged by WHY questions
4. What EVIDENCE would support the hypothesis? - guided by HOW questions
5. What EVIDENCE would CHALLENGE the hypothesis? (Devil's Advocate) - explore WHAT IF alternatives

Format as JSON:
```json
{{
    "thoughts": [
        {{"number": 1, "type": "standard", "content": "..."}},
        {{"number": 2, "type": "standard", "content": "..."}},
        {{"number": 3, "type": "revision", "revises": 1, "content": "Wait, I need to reconsider..."}},
        {{"number": 4, "type": "branch", "branch_id": "devil_advocate", "branch_from": 2, "content": "Alternative view:..."}},
        {{"number": 5, "type": "standard", "content": "..."}}
    ],
    "needs_more_thoughts": false,
    "adjusted_estimate": 5
}}
```"""


RESEARCH_PLAN_PROMPT = """Based on this sequential thinking session, create a structured research plan:

SCQA ANALYSIS:
{scqa}

THINKING PROCESS:
{thoughts}

Create a research plan with specific, actionable search queries. Each query should be something Tavily can search effectively.

Format as JSON:
```json
{{
    "known_knowns": ["What we already know from conversation..."],
    "known_unknowns": ["What we need to find out..."],
    "assumptions": ["Assumptions that need validation..."],
    "validation_queries": [
        "Query for observable/measurable evidence (Camera Test)..."
    ],
    "supporting_queries": [
        "Query for evidence supporting the hypothesis..."
    ],
    "challenging_queries": [
        "Query for counter-evidence or challenges (Red Team)..."
    ],
    "context_queries": [
        "Query for background market/technical context..."
    ]
}}
```

Generate 1-2 queries per category (4-8 total queries). Make them specific and searchable."""


PYRAMID_SYNTHESIS_PROMPT = """Synthesize research results into a Minto Pyramid structure.

ORIGINAL SCQA:
{scqa}

RESEARCH RESULTS:
{results}

Build a pyramid answer with:
1. **MAIN ANSWER** (top of pyramid): Direct answer to the Question, validated or revised based on evidence
2. **KEY LINE** (3 supporting points): The main arguments/evidence supporting your answer
3. **EVIDENCE BASE**: Specific sources and data for each key line point
4. **REMAINING UNKNOWNS**: What still needs investigation

Format as markdown with clear hierarchy showing the pyramid structure."""


# === Helper Functions ===

def format_thoughts_for_prompt(thoughts: List[Thought]) -> str:
    """Format thoughts list for LLM prompt."""
    lines = []
    for t in thoughts:
        prefix = t.prefix
        note = ""
        if t.thought_type == ThoughtType.REVISION:
            note = f" (revises #{t.revises_thought})"
        elif t.thought_type == ThoughtType.BRANCH:
            note = f" (branch '{t.branch_id}' from #{t.branch_from})"
        lines.append(f"{prefix} Thought {t.number}{note}: {t.content}")
    return "\n".join(lines)


def parse_beautiful_questions_response(response_text: str) -> Optional[BeautifulQuestions]:
    """Parse LLM response into BeautifulQuestions."""
    import json
    import re

    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return BeautifulQuestions(
                why_questions=data.get("why_questions", []),
                what_if_questions=data.get("what_if_questions", []),
                how_questions=data.get("how_questions", [])
            )
        except json.JSONDecodeError:
            pass
    return None


def parse_scqa_response(response_text: str) -> Optional[SCQAAnalysis]:
    """Parse LLM response into SCQAAnalysis."""
    import json
    import re

    # Extract JSON from response
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return SCQAAnalysis(
                situation=data.get("situation", ""),
                complication=data.get("complication", ""),
                question=data.get("question", ""),
                answer_hypothesis=data.get("answer_hypothesis", ""),
                confidence=data.get("confidence", 0.5)
            )
        except json.JSONDecodeError:
            pass
    return None


def parse_thoughts_response(response_text: str, session: SequentialThinkingSession) -> List[Thought]:
    """Parse LLM response into Thought objects."""
    import json
    import re

    thoughts = []
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))

            for t_data in data.get("thoughts", []):
                t_type = ThoughtType(t_data.get("type", "standard"))

                if t_type == ThoughtType.STANDARD:
                    thought = session.add_thought(t_data.get("content", ""))
                elif t_type == ThoughtType.REVISION:
                    thought = session.add_revision(
                        t_data.get("content", ""),
                        t_data.get("revises", 1)
                    )
                elif t_type == ThoughtType.BRANCH:
                    thought = session.add_branch(
                        t_data.get("content", ""),
                        t_data.get("branch_id", "alternative"),
                        t_data.get("branch_from", 1)
                    )
                thoughts.append(thought)

            # Adjust estimate if needed
            if data.get("needs_more_thoughts"):
                session.adjust_estimate(data.get("adjusted_estimate", session.total_thoughts_estimated + 2))

        except json.JSONDecodeError:
            pass

    return thoughts


def parse_research_plan_response(response_text: str) -> Optional[ResearchPlan]:
    """Parse LLM response into ResearchPlan."""
    import json
    import re

    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return ResearchPlan(
                known_knowns=data.get("known_knowns", []),
                known_unknowns=data.get("known_unknowns", []),
                assumptions=data.get("assumptions", []),
                validation_queries=data.get("validation_queries", []),
                supporting_queries=data.get("supporting_queries", []),
                challenging_queries=data.get("challenging_queries", []),
                context_queries=data.get("context_queries", [])
            )
        except json.JSONDecodeError:
            pass
    return None
