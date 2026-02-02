"""
A2A Orchestrator - Main Orchestration Layer

This module wires together:
- Two-stage classifier (Cynefin + PWS)
- Context manager (Artifacts vs Frames)
- Phase manager (Directed graph transitions)
- Red Team middleware (Cross-cutting validation)
- Journey mapping view (Cross-cutting context)

Key Principle: Layer on top of existing bots, don't rewrite them.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Literal
from dataclasses import dataclass, field
from datetime import datetime

from .context_manager import ContextManager, Artifact, Frame, ValidationSource
from .phase_manager import PhaseManager, Phase, suggest_phase_from_classification
from .classifier import classify, Classification, get_routing_recommendation
from .supabase_storage import SupabaseStorage

logger = logging.getLogger(__name__)


# === Agent Interface ===

@dataclass
class AgentInput:
    """Input to an agent."""
    query: str
    context: Dict[str, Any]
    phase: Phase
    artifacts: List[Artifact]
    frames: List[Frame]  # Agent's own frames only
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Output from an agent."""
    response: str
    new_artifacts: List[Artifact] = field(default_factory=list)
    new_frames: List[Frame] = field(default_factory=list)
    confidence: float = 0.7
    contains_assumptions: bool = False
    suggested_next_phase: Optional[Phase] = None
    suggested_next_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Added by Red Team middleware
    challenges: List[Dict] = field(default_factory=list)
    needs_revision: bool = False
    red_team_feedback: Optional[str] = None


# === Red Team Middleware ===

@dataclass
class ValidationResult:
    """Result of Red Team validation."""
    passed: bool
    challenges: List[Dict]
    feedback: str
    confidence: float = 0.7


class RedTeamMiddleware:
    """
    Cross-cutting validation that applies to any stage.

    Red Team is NOT a destination - it's a checkpoint that any
    agent output can flow through.
    """

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self._validation_count = 0

    async def validate(
        self,
        claim: str,
        evidence: List[Artifact],
        stage: Phase,
        agent: str
    ) -> ValidationResult:
        """
        Challenge any agent's output with standard questions.

        Args:
            claim: The main output/claim from the agent
            evidence: Supporting artifacts
            stage: Current phase
            agent: Which agent produced this

        Returns:
            ValidationResult with pass/fail and challenges
        """
        self._validation_count += 1

        # Standard validation questions (apply to ALL stages)
        challenges = await self._run_challenges(claim, evidence, [
            "Is this real? What evidence supports it?",
            "What assumptions are being made?",
            "What would have to be true for this to work?",
            "What could make this wrong or irrelevant?",
        ])

        # Stage-specific challenges
        stage_challenges = await self._get_stage_challenges(claim, evidence, stage)
        challenges.extend(stage_challenges)

        # Determine if passed
        critical_challenges = [c for c in challenges if c.get("severity") == "critical"]
        passed = len(critical_challenges) == 0

        feedback = self._synthesize_feedback(challenges, passed)

        return ValidationResult(
            passed=passed,
            challenges=challenges,
            feedback=feedback,
            confidence=0.8 if passed else 0.4
        )

    async def _run_challenges(
        self,
        claim: str,
        evidence: List[Artifact],
        questions: List[str]
    ) -> List[Dict]:
        """Run challenge questions against a claim."""
        challenges = []

        for question in questions:
            # In production, this would call the LLM
            # For now, return placeholder challenges
            challenge = {
                "question": question,
                "severity": "minor",  # critical, major, minor
                "finding": f"Challenge for: {question[:50]}...",
                "recommendation": "Consider reviewing this aspect"
            }
            challenges.append(challenge)

        return challenges

    async def _get_stage_challenges(
        self,
        claim: str,
        evidence: List[Artifact],
        stage: Phase
    ) -> List[Dict]:
        """Get stage-specific challenges."""
        stage_questions = {
            Phase.EXPLORING: [
                "Is this trend real or just noise?",
                "Are we extrapolating too far from limited data?",
            ],
            Phase.FRAMING: [
                "Are we solving the right problem?",
                "Is the framing too narrow or too broad?",
            ],
            Phase.DEFINING: [
                "Is the problem statement testable?",
                "Have we validated with real users?",
            ],
            Phase.SOLVING: [
                "Does this solution address the root cause?",
                "What are the unintended consequences?",
            ],
            Phase.VALIDATING: [
                "Is our validation methodology sound?",
                "Are we measuring the right things?",
            ],
        }

        questions = stage_questions.get(stage, [])
        return await self._run_challenges(claim, evidence, questions)

    def _synthesize_feedback(self, challenges: List[Dict], passed: bool) -> str:
        """Synthesize challenges into actionable feedback."""
        if passed:
            return "Validation passed. Minor points to consider: " + \
                   ", ".join(c["question"][:30] for c in challenges[:3])
        else:
            critical = [c for c in challenges if c.get("severity") == "critical"]
            return "Validation failed. Critical issues: " + \
                   ", ".join(c["question"][:30] for c in critical[:3])


# === Journey Map View ===

@dataclass
class Touchpoint:
    """A point in the user's journey."""
    timestamp: datetime
    type: str
    agent: str
    summary: str


@dataclass
class JourneyMap:
    """User's journey through the system."""
    touchpoints: List[Touchpoint]
    current_phase: Phase
    time_in_phase: float
    agents_visited: List[str]
    key_decisions: List[str]
    friction_points: List[str]


class JourneyMapView:
    """
    Cross-cutting view that any agent can request.

    Provides context about where the user has been in their exploration.
    """

    def __init__(self, context_manager: ContextManager, phase_manager: PhaseManager):
        self.context = context_manager
        self.phases = phase_manager

    def get_current_journey(self) -> JourneyMap:
        """Returns user's journey through the system so far."""
        artifacts = self.context.get_all_artifacts()

        touchpoints = self._extract_touchpoints(artifacts)
        agents_visited = self._get_agents_visited(artifacts)
        key_decisions = self._get_key_decisions(artifacts)
        friction_points = self._identify_friction()

        return JourneyMap(
            touchpoints=touchpoints,
            current_phase=self.phases.current_phase,
            time_in_phase=self.phases.time_in_current_phase(),
            agents_visited=agents_visited,
            key_decisions=key_decisions,
            friction_points=friction_points
        )

    def _extract_touchpoints(self, artifacts: List[Artifact]) -> List[Touchpoint]:
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

    def _get_agents_visited(self, artifacts: List[Artifact]) -> List[str]:
        """Get list of agents the user has interacted with."""
        agents = []
        for artifact in artifacts:
            if artifact.source and artifact.source not in agents:
                agents.append(artifact.source)
        return agents

    def _get_key_decisions(self, artifacts: List[Artifact]) -> List[str]:
        """Get key decisions made during the journey."""
        decisions = []
        for artifact in artifacts:
            if artifact.type == "decision":
                decisions.append(artifact.content[:100])
        return decisions

    def _identify_friction(self) -> List[str]:
        """Identify friction points in the journey."""
        friction = []

        # Check for phase regressions
        regression_count = self.phases.get_regression_count()
        if regression_count > 0:
            friction.append(f"Regressed {regression_count} time(s) - may indicate confusion")

        # Check for time spent
        time_in_phase = self.phases.time_in_current_phase()
        if time_in_phase > 600:  # 10 minutes
            friction.append(f"Spent {time_in_phase/60:.0f} min in {self.phases.current_phase.value}")

        return friction


# === Main Orchestrator ===

class A2AOrchestrator:
    """
    Main orchestration layer that coordinates:
    - Classification
    - Context management
    - Phase transitions
    - Agent execution with Red Team validation
    - Journey tracking
    """

    def __init__(
        self,
        session_id: str,
        llm_client: Any = None,
        agent_registry: Dict[str, Callable] = None
    ):
        self.session_id = session_id
        self.llm_client = llm_client

        # Core managers
        self.context = ContextManager(session_id)
        self.phases = PhaseManager(session_id)
        self.red_team = RedTeamMiddleware(llm_client)
        self.journey = JourneyMapView(self.context, self.phases)

        # Supabase storage (persists to cloud)
        self.storage = SupabaseStorage(session_id)

        # Agent registry (existing bots wrapped with standard interface)
        self.agents = agent_registry or {}

        # State
        self.current_agent: Optional[str] = None
        self.classification: Optional[Classification] = None
        self.routing: Optional[Dict] = None

    async def process_message(
        self,
        message: str,
        force_agent: Optional[str] = None,
        skip_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user message through the orchestration pipeline.

        Args:
            message: User's message
            force_agent: Override agent selection
            skip_validation: Skip Red Team validation

        Returns:
            Response with agent output, context updates, and recommendations
        """
        # Step 1: Add user input as artifact
        self.context.create_artifact(
            content=message,
            source="user",
            artifact_type="user_input"
        )

        # Step 2: Classify (if not already classified or significant new input)
        if self.classification is None or self._should_reclassify(message):
            self.classification = await classify(
                message,
                context=self.context.get_shared_context()
            )
            self.routing = get_routing_recommendation(self.classification)

            # Update phase based on classification
            suggested_phase = suggest_phase_from_classification(
                self.classification.cynefin,
                self.classification.pws
            )
            if self.phases.can_transition(suggested_phase):
                self.phases.transition(
                    suggested_phase,
                    f"Classification suggests {suggested_phase.value}",
                    triggered_by="classifier"
                )

        # Step 3: Select agent
        agent_name = force_agent or self.routing.get("primary_agent", "lawrence")
        self.current_agent = agent_name

        # Step 4: Prepare agent input
        agent_input = AgentInput(
            query=message,
            context=self.context.get_context_for_agent(agent_name),
            phase=self.phases.current_phase,
            artifacts=self.context.get_all_artifacts(),
            frames=self.context.get_agent_frames(agent_name)
        )

        # Step 5: Execute agent (with or without validation)
        if skip_validation:
            output = await self._execute_agent(agent_name, agent_input)
        else:
            output = await self._execute_with_validation(agent_name, agent_input)

        # Step 6: Process output
        result = await self._process_output(agent_name, output)

        return result

    async def _execute_agent(
        self,
        agent_name: str,
        input: AgentInput
    ) -> AgentOutput:
        """Execute an agent without validation."""
        agent_fn = self.agents.get(agent_name)

        if agent_fn is None:
            # Return placeholder for agents not yet integrated
            return AgentOutput(
                response=f"[Agent {agent_name} not yet integrated. Input: {input.query[:100]}...]",
                confidence=0.5
            )

        return await agent_fn(input)

    async def _execute_with_validation(
        self,
        agent_name: str,
        input: AgentInput
    ) -> AgentOutput:
        """Execute agent with Red Team validation as middleware."""
        output = await self._execute_agent(agent_name, input)

        # Determine if we should validate
        should_validate = self._should_validate(agent_name, input.phase, output)

        if should_validate:
            validation = await self.red_team.validate(
                claim=output.response,
                evidence=output.new_artifacts + input.artifacts,
                stage=input.phase,
                agent=agent_name
            )

            if not validation.passed:
                output.challenges = validation.challenges
                output.needs_revision = True
                output.red_team_feedback = validation.feedback

        return output

    def _should_validate(
        self,
        agent_name: str,
        phase: Phase,
        output: AgentOutput
    ) -> bool:
        """Determine if Red Team should validate this output."""
        # Always validate at transition points
        if phase in [Phase.FRAMING, Phase.DEFINING, Phase.VALIDATING]:
            return True

        # Always validate TTA and JTBD outputs (they produce opportunities)
        if agent_name in ["tta", "jtbd"]:
            return True

        # Validate if confidence is low
        if output.confidence < 0.7:
            return True

        # Validate if output contains assumptions
        if output.contains_assumptions:
            return True

        return False

    def _should_reclassify(self, message: str) -> bool:
        """Determine if we should reclassify based on new input."""
        # Reclassify if message is long (substantial new input)
        if len(message) > 200:
            return True

        # Reclassify if certain keywords suggest a shift
        shift_keywords = [
            "actually", "wait", "let me rethink", "different approach",
            "new problem", "another question", "pivot"
        ]
        message_lower = message.lower()
        if any(kw in message_lower for kw in shift_keywords):
            return True

        return False

    async def _process_output(
        self,
        agent_name: str,
        output: AgentOutput
    ) -> Dict[str, Any]:
        """Process agent output and update context/state."""
        # Add new artifacts
        for artifact in output.new_artifacts:
            artifact.source = agent_name
            self.context.add_artifact(artifact)

        # Add new frames (scoped to this agent)
        for frame in output.new_frames:
            self.context.add_frame(
                agent=agent_name,
                content=frame.content,
                frame_type=frame.type,
                confidence=frame.confidence
            )

        # Handle phase transition suggestion
        if output.suggested_next_phase:
            if self.phases.can_transition(output.suggested_next_phase):
                success, msg = self.phases.transition(
                    output.suggested_next_phase,
                    f"Agent {agent_name} suggested transition",
                    triggered_by=agent_name
                )

        # Build response
        return {
            "response": output.response,
            "agent": agent_name,
            "phase": self.phases.current_phase.value,
            "classification": self.classification.to_dict() if self.classification else None,
            "needs_revision": output.needs_revision,
            "red_team_feedback": output.red_team_feedback,
            "challenges": output.challenges,
            "suggested_next_agent": output.suggested_next_agent,
            "allowed_transitions": [p.value for p in self.phases.get_allowed_transitions()],
            "journey_summary": {
                "agents_visited": self.journey.get_current_journey().agents_visited,
                "time_in_phase": self.phases.time_in_current_phase(),
                "regression_count": self.phases.get_regression_count()
            },
            "context_summary": self.context.get_summary()
        }

    # === Public API ===

    def get_state(self) -> Dict[str, Any]:
        """Get current orchestrator state."""
        return {
            "session_id": self.session_id,
            "current_agent": self.current_agent,
            "phase": self.phases.current_phase.value,
            "classification": self.classification.to_dict() if self.classification else None,
            "routing": self.routing,
            "context_summary": self.context.get_summary(),
            "phase_summary": self.phases.get_summary()
        }

    def get_journey(self) -> JourneyMap:
        """Get current journey map."""
        return self.journey.get_current_journey()

    async def transition_phase(
        self,
        target: Phase,
        reason: str,
        triggered_by: str = "user"
    ) -> Dict[str, Any]:
        """Manually transition to a new phase."""
        success, message = self.phases.transition(target, reason, triggered_by)
        return {
            "success": success,
            "message": message,
            "new_phase": self.phases.current_phase.value,
            "allowed_next": [p.value for p in self.phases.get_allowed_transitions()]
        }

    async def promote_frame(
        self,
        frame_id: str,
        validation_source: ValidationSource
    ) -> str:
        """Promote a frame to artifact after validation."""
        if self.current_agent is None:
            raise ValueError("No current agent set")

        return self.context.promote_frame_to_artifact(
            self.current_agent,
            frame_id,
            validation_source
        )

    async def save_state(self):
        """Save all state to Supabase and local disk."""
        # Save to local disk (backup)
        self.context.save()
        self.phases.save()

        # Save to Supabase (primary)
        await self.storage.save_full_state(
            artifacts=[a.to_dict() for a in self.context.get_all_artifacts()],
            frames={
                agent: [f.to_dict() for f in frames.values()]
                for agent, frames in self.context._frames.items()
            },
            phase_history=[t.to_dict() for t in self.phases.phase_history],
            current_phase=self.phases.current_phase.value,
            classification=self.classification.to_dict() if self.classification else None
        )

    @classmethod
    def load(cls, session_id: str, llm_client: Any = None) -> "A2AOrchestrator":
        """Load orchestrator from saved state."""
        orchestrator = cls(session_id, llm_client)
        orchestrator.context = ContextManager.load(session_id)
        orchestrator.phases = PhaseManager.load(session_id)
        orchestrator.journey = JourneyMapView(orchestrator.context, orchestrator.phases)
        return orchestrator


# === Integration Helper ===

def create_agent_wrapper(bot_config: Dict, system_prompt: str) -> Callable:
    """
    Create a wrapper that adapts existing bot configs to the agent interface.

    This allows layering the new orchestration on top of existing bots
    without rewriting them.
    """
    async def agent_wrapper(input: AgentInput) -> AgentOutput:
        # This would call the existing bot's LLM integration
        # For now, return a placeholder

        # In real implementation:
        # 1. Build messages from input.context and input.query
        # 2. Call LLM with system_prompt
        # 3. Parse response into AgentOutput

        return AgentOutput(
            response=f"[{bot_config.get('name', 'Agent')} processing: {input.query[:50]}...]",
            confidence=0.7
        )

    return agent_wrapper
