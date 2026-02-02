# A2A Practical Architecture

> **Status**: Active Implementation Guide
> **Last Updated**: 2026-02-02
> **Decision Owner**: Architecture decisions consolidated from user review

This document captures the practical architectural decisions for Mindrian's A2A multi-agent system.

---

## Core Architectural Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Classification** | Two-stage (Cynefin + PWS) inline in Python | Cynefin tells you *how uncertain*, PWS tells you *where in lifecycle*. No separate service needed until multiple clients need it independently. |
| **Context Separation** | Artifacts vs Frames | TTA speculation shouldn't become JTBD's "facts". Frames are scoped; artifacts persist. |
| **Red Team** | Cross-cutting middleware | Applies to ANY stage as checkpoint, not just a destination stage. |
| **Journey Mapping** | Cross-cutting view | Any agent can request user's journey context, not just a tool. |
| **MVP Scope** | 4 agents: TTA, JTBD, Red Team, Validation | Complete loop with minimal complexity. |
| **Existing Code** | Layer on top, don't rewrite | Bots work; wrap with standard interface. |
| **Phase Transitions** | Directed graph with explicit states | Prevents infinite loops, forces explicit acknowledgment of stuck states. |

---

## Two-Stage Classification

### The Insight

Cynefin and PWS classification are **orthogonal dimensions**:

- **Cynefin**: How uncertain is the situation? (Clear → Complicated → Complex → Chaotic)
- **PWS**: Where in the problem lifecycle? (Un-Defined → Ill-Defined → Well-Defined)

### Routing Matrix

```
                    PWS Problem Type
                    Un-Defined    Ill-Defined    Well-Defined
Cynefin  ┌─────────────────────────────────────────────────────┐
Domain   │                                                      │
         │ Complex    Full TTA      JTBD + Red    Careful       │
         │            exploration   Team loops    validation    │
         │                                                      │
         │ Complicated Bounded TTA  Expert JTBD   Direct        │
         │              expert-led   structured   execution     │
         │                                                      │
         │ Clear      Quick scan    Standard      Execute       │
         │            for signals   process       immediately   │
         └─────────────────────────────────────────────────────┘
```

### Implementation (Inline Python)

```python
# In orchestrator.py - NOT a separate Edge Function

from typing import Literal, Tuple
from pydantic import BaseModel

class Classification(BaseModel):
    cynefin: Literal["clear", "complicated", "complex", "chaotic"]
    pws: Literal["un-defined", "ill-defined", "well-defined"]
    cynefin_confidence: float
    pws_confidence: float
    reasoning: str

async def classify(text: str, context: dict = None) -> Classification:
    """
    Two-stage classification inline in orchestrator.
    No separate service until we need:
    1. Multiple clients accessing independently
    2. A/B testing classifier versions
    3. Latency becomes a bottleneck
    """
    prompt = f"""Classify this user input on two dimensions:

1. CYNEFIN DOMAIN (how uncertain is the situation):
   - Clear: Obvious cause-effect, best practices exist
   - Complicated: Cause-effect requires analysis, experts help
   - Complex: Cause-effect only clear in retrospect, need to probe
   - Chaotic: No clear cause-effect, need to act immediately

2. PWS PROBLEM TYPE (where in the problem lifecycle):
   - Un-Defined: Don't know what problem to solve yet
   - Ill-Defined: Have an opportunity, need to refine it
   - Well-Defined: Know the problem, designing solution

User input: {text}
{"Context: " + str(context) if context else ""}

Respond with JSON: {{cynefin, pws, cynefin_confidence, pws_confidence, reasoning}}
"""
    response = await llm.invoke(prompt, temperature=0.3)
    return Classification.model_validate_json(response)
```

---

## Context Management: Artifacts vs Frames

### The Problem

In multi-agent systems, speculation from one agent often becomes "facts" for the next. This creates context pollution where hypothetical ideas are treated as validated claims.

### The Solution

Separate context into two types:

1. **Artifacts**: Validated evidence that persists across all agents
2. **Frames**: Agent-specific interpretations that don't leak

### Implementation

```python
from dataclasses import dataclass, field
from typing import Literal, Optional
from datetime import datetime
import uuid

@dataclass
class Artifact:
    """Evidence that all agents can see."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["user_input", "research_finding", "validated_insight", "decision"]
    content: str
    source: str  # Which agent or user created it
    created_at: datetime = field(default_factory=datetime.utcnow)
    validation_source: Optional[str] = None  # How it was validated

@dataclass
class Frame:
    """Interpretation that only the creating agent sees."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent: str  # Which agent created this frame
    type: Literal["hypothesis", "assumption", "speculation", "working_model"]
    content: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)

class ContextManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._artifacts: dict[str, Artifact] = {}
        self._frames: dict[str, dict[str, Frame]] = {}  # agent -> frame_id -> frame

    def add_artifact(self, artifact: Artifact) -> str:
        """Add artifact that all agents can see."""
        self._artifacts[artifact.id] = artifact
        return artifact.id

    def add_frame(self, agent: str, content: str, frame_type: Literal["hypothesis", "assumption", "speculation", "working_model"], confidence: float = 0.5) -> str:
        """Add frame that only this agent sees."""
        frame = Frame(
            agent=agent,
            type=frame_type,
            content=content,
            confidence=confidence
        )
        if agent not in self._frames:
            self._frames[agent] = {}
        self._frames[agent][frame.id] = frame
        return frame.id

    def get_context_for_agent(self, agent: str) -> dict:
        """Get context visible to a specific agent."""
        return {
            "artifacts": list(self._artifacts.values()),
            "frames": list(self._frames.get(agent, {}).values())
        }

    def promote_frame_to_artifact(
        self,
        agent: str,
        frame_id: str,
        validation_source: Literal["user_confirmed", "red_team_passed", "research_verified"]
    ) -> str:
        """Promote validated frame to artifact."""
        frame = self._frames.get(agent, {}).get(frame_id)
        if not frame:
            raise ValueError(f"Frame {frame_id} not found for agent {agent}")

        artifact = Artifact(
            type="validated_insight",
            content=frame.content,
            source=agent,
            validation_source=validation_source
        )
        self._artifacts[artifact.id] = artifact

        # Remove the frame
        del self._frames[agent][frame_id]

        return artifact.id
```

---

## Red Team as Cross-Cutting Middleware

### The Insight

Red Team isn't a destination stage - it's a **checkpoint** that any agent output can flow through at ANY stage.

### Implementation

```python
async def execute_with_validation(
    agent: Agent,
    input: AgentInput,
    force_validation: bool = False
) -> AgentOutput:
    """
    Execute agent with optional Red Team validation as middleware.
    Red Team applies to ANY stage, not just as a final step.
    """
    result = await agent.execute(input)

    # Determine if we should validate
    should_validate = (
        force_validation or
        should_auto_validate(agent, input.phase) or
        result.confidence < 0.7 or
        result.contains_assumptions
    )

    if should_validate:
        validation = await red_team_middleware.validate({
            "claim": result.primary_output,
            "evidence": result.artifacts,
            "stage": input.phase,
            "agent": agent.name
        })

        if not validation.passed:
            return AgentOutput(
                **result.__dict__,
                challenges=validation.challenges,
                needs_revision=True,
                red_team_feedback=validation.feedback
            )

    return result

def should_auto_validate(agent: Agent, phase: str) -> bool:
    """
    Determine if Red Team should automatically validate.
    Red Team runs at transition points and on high-stakes outputs.
    """
    return (
        phase in ["framing", "defining", "validating"] or
        agent.name in ["tta", "jtbd"] or
        agent.produces_opportunities
    )
```

### Red Team Validation Protocol

```python
class RedTeamMiddleware:
    """Cross-cutting validation that applies to any stage."""

    async def validate(self, context: dict) -> ValidationResult:
        """
        Challenge any agent's output with standard questions.
        """
        claim = context["claim"]
        evidence = context["evidence"]
        stage = context["stage"]

        # Standard validation questions (apply to ALL stages)
        challenges = await self._run_challenges(claim, evidence, [
            "Is this real? What evidence supports it?",
            "What assumptions are being made?",
            "What would have to be true for this to work?",
            "What could make this wrong or irrelevant?",
            "Who else is working on this and why haven't they solved it?",
        ])

        # Stage-specific challenges
        if stage == "exploring":
            challenges.extend(await self._run_challenges(claim, evidence, [
                "Is this trend real or just noise?",
                "Are we extrapolating too far from limited data?",
            ]))
        elif stage == "framing":
            challenges.extend(await self._run_challenges(claim, evidence, [
                "Are we solving the right problem?",
                "Is the framing too narrow or too broad?",
            ]))
        elif stage == "defining":
            challenges.extend(await self._run_challenges(claim, evidence, [
                "Is the problem statement testable?",
                "Have we validated with real users?",
            ]))

        passed = all(c.severity != "critical" for c in challenges)

        return ValidationResult(
            passed=passed,
            challenges=challenges,
            feedback=self._synthesize_feedback(challenges)
        )
```

---

## Journey Mapping as Cross-Cutting View

### The Insight

Journey Mapping should be available to ANY agent, not just as a specific tool. It provides context about where the user has been in their exploration.

### Implementation

```python
class JourneyMapView:
    """Cross-cutting view that any agent can request."""

    def __init__(self, context_manager: ContextManager):
        self.context = context_manager

    def get_current_journey(self) -> JourneyMap:
        """Returns user's journey through the system so far."""
        artifacts = self.context.get_all_artifacts()

        return JourneyMap(
            touchpoints=self._extract_touchpoints(artifacts),
            emotional_arc=self._analyze_emotional_state(artifacts),
            friction_points=self._identify_friction(artifacts),
            decision_points=self._mark_decisions(artifacts),
            current_phase=self._determine_phase(artifacts),
            time_in_phase=self._calculate_time_in_phase(artifacts)
        )

    def _extract_touchpoints(self, artifacts: list[Artifact]) -> list[Touchpoint]:
        """Extract key moments in the user's journey."""
        touchpoints = []
        for artifact in artifacts:
            if artifact.type in ["user_input", "decision", "validated_insight"]:
                touchpoints.append(Touchpoint(
                    timestamp=artifact.created_at,
                    type=artifact.type,
                    agent=artifact.source,
                    summary=artifact.content[:100]
                ))
        return sorted(touchpoints, key=lambda t: t.timestamp)
```

---

## Phase Transition Graph

### Allowed Transitions

```
                    ┌─────────────┐
                    │  exploring  │
                    └──────┬──────┘
                           │ (forward only)
                           ▼
         ┌─────────────────────────────────────┐
         │               framing               │
         └──────┬─────────────────────┬────────┘
                │                     │
                │ (can regress)       │ (forward)
                ▼                     ▼
         ┌──────────────┐      ┌──────────────┐
         │  exploring   │      │   defining   │
         └──────────────┘      └──────┬───────┘
                                      │
                               ┌──────┴──────┐
                               │             │
                               ▼             ▼
                        ┌──────────┐   ┌──────────┐
                        │  solving │   │ framing  │
                        └────┬─────┘   └──────────┘
                             │         (can regress)
                             ▼
                      ┌─────────────┐
                      │ validating  │
                      └──────┬──────┘
                             │
                      ┌──────┴──────┐
                      │             │
                      ▼             ▼
               ┌──────────┐  ┌──────────┐
               │ complete │  │  stuck   │
               └──────────┘  └────┬─────┘
                                  │
                                  ▼
                           ┌──────────┐
                           │ framing  │
                           └──────────┘
                           (explicit fail)
```

### Implementation

```python
from enum import Enum
from typing import Optional

class Phase(Enum):
    EXPLORING = "exploring"
    FRAMING = "framing"
    DEFINING = "defining"
    SOLVING = "solving"
    VALIDATING = "validating"
    COMPLETE = "complete"
    STUCK = "stuck"

ALLOWED_TRANSITIONS = {
    Phase.EXPLORING: [Phase.FRAMING],
    Phase.FRAMING: [Phase.EXPLORING, Phase.DEFINING],  # Can regress
    Phase.DEFINING: [Phase.FRAMING, Phase.SOLVING],    # Can regress
    Phase.SOLVING: [Phase.VALIDATING],
    Phase.VALIDATING: [Phase.COMPLETE, Phase.STUCK, Phase.FRAMING],
    Phase.STUCK: [Phase.FRAMING],  # Explicit acknowledgment required
    Phase.COMPLETE: [],  # Terminal
}

class PhaseManager:
    def __init__(self, initial_phase: Phase = Phase.EXPLORING):
        self.current_phase = initial_phase
        self.phase_history: list[tuple[Phase, datetime]] = []

    def can_transition(self, target: Phase) -> bool:
        return target in ALLOWED_TRANSITIONS.get(self.current_phase, [])

    def transition(self, target: Phase, reason: str) -> bool:
        if not self.can_transition(target):
            return False

        self.phase_history.append((self.current_phase, datetime.utcnow()))
        self.current_phase = target
        return True

    def is_regression(self, target: Phase) -> bool:
        """Check if transition is going backwards."""
        phase_order = [Phase.EXPLORING, Phase.FRAMING, Phase.DEFINING, Phase.SOLVING, Phase.VALIDATING]
        current_idx = phase_order.index(self.current_phase) if self.current_phase in phase_order else -1
        target_idx = phase_order.index(target) if target in phase_order else -1
        return target_idx < current_idx
```

---

## MVP Implementation: 4-Agent Pipeline

### Agents

1. **TTA (Trending to the Absurd)**: Entry point for exploration, generates opportunities
2. **JTBD (Jobs to Be Done)**: Refines opportunities into customer-centric problem statements
3. **Red Team**: Validates at ANY stage (middleware, not destination)
4. **Validation Agent**: Final quality check before completion

### Complete Loop

```
User Input
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│  CLASSIFIER (inline)                                       │
│  Cynefin: Complex | PWS: Un-Defined                       │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│  TTA AGENT                                                 │
│  - Explore domain                                          │
│  - Identify trends                                         │
│  - Generate opportunities                                  │
│  [Red Team checkpoint after opportunity generation]        │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│  JTBD AGENT                                                │
│  - Who has this problem?                                   │
│  - What progress are they trying to make?                  │
│  - What's preventing them?                                 │
│  [Red Team checkpoint after job statement]                 │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│  VALIDATION AGENT                                          │
│  - Is it real?                                             │
│  - Can we win?                                             │
│  - Is it worth it?                                         │
│  [Final Red Team before completion]                        │
└───────────────────────────────────────────────────────────┘
    │
    ▼
Complete (or → Stuck → Framing)
```

---

## Implementation Priority

### Week 1: Context Manager + Basic Orchestration (The Plumbing)

Build the foundation first. If the classifier fails validation, you can manually route while iterating.

```python
# protocols/context_manager.py
# protocols/phase_manager.py
# protocols/orchestrator.py
```

### Week 2: Classifier with 50+ Test Cases

Include edge cases:
- Boundary cases: "We've done customer research but haven't validated it"
- Multi-domain: "The tech is simple but the market is chaotic"
- Override triggers: User intent conflicts with detected stage

```python
# protocols/classifier.py
# tests/test_classifier.py (50+ cases)
```

### Week 3: Wire Up Agents Through Orchestrator

Connect existing bots through the new orchestration layer.

```python
# Update mindrian_chat.py to use orchestrator
# Add Red Team middleware hooks
# Wire journey mapping view
```

---

## Key Principles

1. **Inline Until Proven Otherwise**: Don't extract services until you have evidence of need
2. **Frames Don't Leak**: Agent speculation stays scoped to that agent
3. **Red Team Is Everywhere**: Validation happens at transitions, not just at the end
4. **Explicit Stuck States**: Force acknowledgment rather than infinite loops
5. **Layer, Don't Rewrite**: Existing bots work - add orchestration on top

---

## Files to Create/Update

| File | Action | Purpose |
|------|--------|---------|
| `protocols/context_manager.py` | Create | Artifacts vs Frames separation |
| `protocols/phase_manager.py` | Create | Phase transition graph |
| `protocols/classifier.py` | Create | Two-stage classification |
| `protocols/orchestrator.py` | Create | Main orchestration logic |
| `protocols/red_team_middleware.py` | Create | Cross-cutting validation |
| `protocols/journey_view.py` | Create | Cross-cutting journey context |
| `mindrian_chat.py` | Update | Wire orchestrator on chat start |
| `tests/test_classifier.py` | Create | 50+ classification test cases |

---

## Monitoring & Instrumentation

From day one, log classification decisions:

```python
# In classifier
async def classify_with_logging(text: str, context: dict = None) -> Classification:
    start_time = time.time()
    result = await classify(text, context)

    # Log for later analysis
    await log_classification({
        "input_hash": hash_text(text),  # Privacy-safe
        "cynefin_result": result.cynefin,
        "pws_result": result.pws,
        "cynefin_confidence": result.cynefin_confidence,
        "pws_confidence": result.pws_confidence,
        "latency_ms": (time.time() - start_time) * 1000,
        "timestamp": datetime.utcnow().isoformat()
    })

    return result
```

This gives you the data to validate the 80% accuracy target and identify systematic misclassifications.
