# Wave 4: Auto-Orchestration - "Find the Breakthrough"

> **Status**: Design Document - NOT FOR IMPLEMENTATION YET
> **Version**: 1.0
> **Date**: 2026-02-08
> **Author**: Architecture Team

---

## Table of Contents

1. [Vision](#vision)
2. [User Experience](#user-experience)
3. [Intent Classification System](#intent-classification-system)
4. [Workflow Recipes](#workflow-recipes)
5. [Orchestrator Architecture](#orchestrator-architecture)
6. [Parallel Execution Strategy](#parallel-execution-strategy)
7. [Swarm Synthesis Algorithm](#swarm-synthesis-algorithm)
8. [Context Management](#context-management)
9. [UI Integration Plan](#ui-integration-plan)
10. [Implementation Checklist](#implementation-checklist)
11. [Risk Analysis](#risk-analysis)

---

## Vision

### The Problem

Currently, users must manually:
1. Know which agent to use (TTA, JTBD, Red Team, Ackoff, etc.)
2. Switch between agents manually
3. Carry context between sessions
4. Synthesize insights from multiple perspectives

### The Solution

**Auto-Orchestration** - User says: "I have reentry heat shield technology. Find the business opportunity."

The system automatically:
1. Classifies intent (tech-to-opportunity workflow)
2. Picks the right agents (TTA -> JTBD -> Red Team -> Ackoff)
3. Runs agents in optimal order (parallel where possible)
4. Synthesizes results into actionable insights
5. Displays progress on canvas in real-time

### Design Principles

1. **Invisible Intelligence** - User doesn't need to know PWS methodology
2. **Layer, Don't Rewrite** - Build on existing `multi_agent_graph.py` and pipelines
3. **Fail Gracefully** - If orchestration fails, fall back to current manual mode
4. **Observable Progress** - User sees which agents are working
5. **Interruptible** - User can stop, adjust, and resume

---

## User Experience

### Entry Points

```
User Input: "I have reentry heat shield technology. Find the business opportunity."
                                    |
                                    v
         ┌──────────────────────────────────────────────────────────────┐
         │           AUTO-ORCHESTRATION TRIGGERED                       │
         │                                                              │
         │   🔮 "Finding your breakthrough..."                          │
         │                                                              │
         │   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │
         │   │  TTA   │→→│  JTBD  │→→│Red Team│→→│ Ackoff │           │
         │   │ 🟢 Done│  │ 🟡 Run │  │ ⚪ Wait│  │ ⚪ Wait│           │
         │   └────────┘  └────────┘  └────────┘  └────────┘           │
         │                                                              │
         │   Stage 2/4: Finding customer jobs for heat shield tech...  │
         │   ━━━━━━━━━━━━━━━━━━━━━━░░░░░░░░░░░░░░░░░░░░ 50%             │
         │                                                              │
         │   [⏸️ Pause] [🔧 Adjust Agents] [❌ Cancel]                   │
         └──────────────────────────────────────────────────────────────┘
```

### Three Ways to Trigger

1. **"Find Breakthrough" Button** - Explicit request for full analysis
2. **Natural Language Detection** - "Find opportunity for...", "Business potential of..."
3. **Quick Actions** - Buttons like "Full Analysis", "Stress Test", "Research Deep Dive"

### Canvas Display

Results appear on canvas as they complete:

```
┌─────────────────────────────────────────────────────────────────────┐
│  BREAKTHROUGH ANALYSIS: Heat Shield Technology                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─── TTA Insights ───────────────────────────────────────────────┐ │
│  │ Trend: Private space sector growing 15% annually               │ │
│  │ Absurd: By 2040, 500+ commercial reentries per year            │ │
│  │ Opportunity: "Reusable heat shields as a service"              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─── JTBD Analysis ──────────────────────────────────────────────┐ │
│  │ Job: "When launching satellites, I want to recover my          │ │
│  │       booster so I can reduce launch costs by 80%"             │ │
│  │ Customer: SpaceX competitors, emerging space nations           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─── Red Team Challenges ────────────────────────────────────────┐ │
│  │ 🔴 Assumption: "Market needs cheaper shields" - needs data     │ │
│  │ 🟡 Risk: Incumbents (Lockheed, Boeing) have deep relationships │ │
│  │ 🟢 Strength: Unique material science advantage                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─── DIKW Validation ────────────────────────────────────────────┐ │
│  │ Data: Global reentry market $2.3B (2024) → $8B (2030)          │ │
│  │ Knowledge: 3 incumbents control 85% of market                  │ │
│  │ Wisdom: Entry via emerging customers, not incumbents           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ═══════════════════════════════════════════════════════════════════│
│  SYNTHESIS                                                           │
│  ═══════════════════════════════════════════════════════════════════│
│  Recommended Path: Partner with emerging space nations (India,       │
│  Japan, UAE) who need reentry capability but lack incumbent ties.    │
│  Initial market: $500M. First customer: ISRO for reusable booster.  │
│                                                                      │
│  Confidence: 7/10 | Key Assumption to Test: ISRO budget allocation  │
│                                                                      │
│  [📥 Export Report] [🔄 Dig Deeper] [✅ Accept & Continue]           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Intent Classification System

### Classification Taxonomy

```python
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class WorkflowType(Enum):
    """Primary workflow categories."""
    TECH_TO_OPPORTUNITY = "tech_to_opportunity"    # "I have technology X..."
    EXPLORE = "explore"                             # "Tell me about Y..."
    DOCUMENT_REVIEW = "document_review"             # "Review this document..."
    STRESS_TEST = "stress_test"                     # "Challenge this idea..."
    VALIDATE = "validate"                           # "Is this real?"
    FULL_ANALYSIS = "full_analysis"                 # "Full analysis of..."
    CUSTOM = "custom"                               # Manual agent selection

class IntentSignal(BaseModel):
    """Signals extracted from user message."""
    has_technology: bool = False       # "I have...", "We built...", "Our tech..."
    has_opportunity_request: bool = False  # "Find opportunity", "business potential"
    has_document: bool = False         # File attached or mentioned
    has_challenge_language: bool = False   # "stress test", "challenge", "poke holes"
    has_validation_need: bool = False  # "is this real", "validate", "evidence"
    has_exploration_intent: bool = False   # "explore", "learn about", "understand"
    entities_mentioned: List[str] = []  # Technology names, markets, etc.
    confidence: float = 0.0

class ClassificationResult(BaseModel):
    """Full classification output."""
    workflow_type: WorkflowType
    cynefin_domain: str  # clear, complicated, complex, chaotic
    pws_stage: str       # un-defined, ill-defined, well-defined
    recommended_agents: List[str]
    signals: IntentSignal
    reasoning: str
    confidence: float
```

### Classification Logic

```python
# protocols/intent_classifier.py

import re
from typing import Tuple

# Pattern-based quick classification (< 5ms)
TECH_PATTERNS = [
    r"i have\s+(?:a |an )?(?:technology|tech|invention|patent|solution)",
    r"we (?:built|developed|created|invented)",
    r"our (?:technology|tech|product|solution)",
    r"proprietary (?:technology|tech|method|process)",
]

OPPORTUNITY_PATTERNS = [
    r"find\s+(?:the |a )?(?:business |market )?opportunity",
    r"business potential",
    r"market for",
    r"commercialize",
    r"monetize",
    r"find (?:customers|markets|applications)",
]

CHALLENGE_PATTERNS = [
    r"stress[- ]?test",
    r"challenge",
    r"poke holes",
    r"devil'?s advocate",
    r"what (?:could|might) go wrong",
    r"critique",
    r"red team",
]

EXPLORE_PATTERNS = [
    r"explore",
    r"learn about",
    r"understand",
    r"tell me about",
    r"what is",
    r"how does",
]

def classify_intent(message: str, context: dict = None) -> ClassificationResult:
    """
    Two-stage intent classification.

    Stage 1: Fast pattern matching (< 5ms)
    Stage 2: LLM refinement if confidence < 0.7 (optional, ~200ms)

    Args:
        message: User input text
        context: Optional session context (current bot, phase, etc.)

    Returns:
        ClassificationResult with workflow type and recommended agents
    """
    signals = _extract_signals(message)

    # Stage 1: Pattern-based classification
    if signals.has_technology and signals.has_opportunity_request:
        workflow = WorkflowType.TECH_TO_OPPORTUNITY
        agents = ["tta", "jtbd", "redteam", "ackoff"]
        confidence = 0.9

    elif signals.has_document:
        workflow = WorkflowType.DOCUMENT_REVIEW
        agents = ["pws_grading", "redteam"]
        confidence = 0.85

    elif signals.has_challenge_language:
        workflow = WorkflowType.STRESS_TEST
        agents = ["redteam", "ackoff"]
        confidence = 0.85

    elif signals.has_validation_need:
        workflow = WorkflowType.VALIDATE
        agents = ["ackoff", "research", "validation"]
        confidence = 0.8

    elif signals.has_exploration_intent:
        workflow = WorkflowType.EXPLORE
        agents = ["tta", "research", "larry"]
        confidence = 0.7

    else:
        workflow = WorkflowType.CUSTOM
        agents = ["larry"]  # Default to Larry for routing
        confidence = 0.5

    # Stage 2: LLM refinement if needed
    if confidence < 0.7 and context.get("enable_llm_classification", True):
        refined = _llm_classify(message, signals, context)
        if refined.confidence > confidence:
            return refined

    return ClassificationResult(
        workflow_type=workflow,
        cynefin_domain=_infer_cynefin(signals),
        pws_stage=_infer_pws_stage(signals),
        recommended_agents=agents,
        signals=signals,
        reasoning=_generate_reasoning(workflow, signals),
        confidence=confidence,
    )

def _extract_signals(message: str) -> IntentSignal:
    """Extract intent signals from message."""
    message_lower = message.lower()

    return IntentSignal(
        has_technology=any(re.search(p, message_lower) for p in TECH_PATTERNS),
        has_opportunity_request=any(re.search(p, message_lower) for p in OPPORTUNITY_PATTERNS),
        has_document=_has_document_mention(message),
        has_challenge_language=any(re.search(p, message_lower) for p in CHALLENGE_PATTERNS),
        has_validation_need=_has_validation_language(message_lower),
        has_exploration_intent=any(re.search(p, message_lower) for p in EXPLORE_PATTERNS),
        entities_mentioned=_extract_entities(message),
        confidence=0.0,  # Updated by classifier
    )

def _infer_cynefin(signals: IntentSignal) -> str:
    """Infer Cynefin domain from signals."""
    if signals.has_exploration_intent and not signals.has_technology:
        return "complex"  # Uncertain, needs probing
    elif signals.has_technology and signals.has_opportunity_request:
        return "complicated"  # Known solution, need expert analysis
    elif signals.has_validation_need:
        return "complicated"  # Data-driven decision
    else:
        return "complex"  # Default to complex for safety

def _infer_pws_stage(signals: IntentSignal) -> str:
    """Infer PWS problem stage from signals."""
    if signals.has_exploration_intent and not signals.has_technology:
        return "un-defined"  # Still exploring
    elif signals.has_technology:
        return "ill-defined"  # Have solution, refining problem
    elif signals.has_validation_need:
        return "well-defined"  # Testing specific hypothesis
    else:
        return "un-defined"
```

### Integration with Existing Classifier

The new intent classifier builds on the existing two-stage classifier from `protocols/classifier.py`:

```python
# Compose with existing classification
from protocols.classifier import classify as classify_cynefin_pws

async def full_classification(message: str, context: dict = None) -> ClassificationResult:
    """
    Full classification combining intent and Cynefin/PWS.
    """
    # Get intent classification
    intent = classify_intent(message, context)

    # Get Cynefin/PWS classification from existing system
    try:
        cynefin_pws = await classify_cynefin_pws(message, context)
        intent.cynefin_domain = cynefin_pws.cynefin
        intent.pws_stage = cynefin_pws.pws
    except Exception:
        pass  # Use inferred values

    return intent
```

---

## Workflow Recipes

### Recipe Definition Schema

```python
# protocols/workflow_recipes.py

from typing import TypedDict, List, Optional, Literal
from dataclasses import dataclass

class StageConfig(TypedDict):
    """Configuration for a workflow stage."""
    agents: List[str]          # Agent IDs to run
    task: str                  # Task description for logging
    parallel: bool             # Run agents in parallel?
    timeout_seconds: int       # Max time for stage
    skip_if: Optional[str]     # Condition to skip (e.g., "no_entities")
    validation: bool           # Apply Red Team validation after?

class WorkflowRecipe(TypedDict):
    """Complete workflow recipe."""
    id: str
    name: str
    description: str
    stages: List[StageConfig]
    synthesis_mode: Literal["sequential", "parallel", "consensus"]
    estimated_seconds: int
    min_confidence: float      # Minimum classification confidence to auto-run

# ============================================================================
# PREDEFINED WORKFLOWS
# ============================================================================

WORKFLOWS: dict[str, WorkflowRecipe] = {

    "tech_to_opportunity": {
        "id": "tech_to_opportunity",
        "name": "Technology to Opportunity",
        "description": "Find business opportunities for a technology",
        "stages": [
            {
                "agents": ["tta", "research"],
                "task": "expand_domains",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["jtbd"],
                "task": "find_customer_jobs",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": True,  # Red Team validates job statements
            },
            {
                "agents": ["ackoff", "validation"],
                "task": "assess_market_wisdom",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": True,
            },
            {
                "agents": ["larry"],
                "task": "synthesize_opportunity",
                "parallel": False,
                "timeout_seconds": 30,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "sequential",
        "estimated_seconds": 180,
        "min_confidence": 0.75,
    },

    "explore": {
        "id": "explore",
        "name": "Open Exploration",
        "description": "Explore a topic from multiple angles",
        "stages": [
            {
                "agents": ["tta", "research", "scenario"],
                "task": "gather_perspectives",
                "parallel": True,
                "timeout_seconds": 90,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["knowns"],
                "task": "map_uncertainties",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["larry"],
                "task": "synthesize_exploration",
                "parallel": False,
                "timeout_seconds": 30,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "parallel",
        "estimated_seconds": 150,
        "min_confidence": 0.6,
    },

    "stress_test": {
        "id": "stress_test",
        "name": "Stress Test",
        "description": "Challenge assumptions and find weaknesses",
        "stages": [
            {
                "agents": ["redteam"],
                "task": "identify_assumptions",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["ackoff", "research"],
                "task": "validate_claims",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["redteam"],
                "task": "final_challenge",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "consensus",
        "estimated_seconds": 120,
        "min_confidence": 0.8,
    },

    "document_review": {
        "id": "document_review",
        "name": "Document Review",
        "description": "Analyze and grade a document",
        "stages": [
            {
                "agents": ["pws_grading"],
                "task": "grade_document",
                "parallel": False,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["redteam", "ackoff"],
                "task": "challenge_claims",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": "low_score",  # Skip if grade is very low
                "validation": False,
            },
            {
                "agents": ["larry"],
                "task": "synthesize_feedback",
                "parallel": False,
                "timeout_seconds": 30,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "sequential",
        "estimated_seconds": 120,
        "min_confidence": 0.85,
    },

    "validate": {
        "id": "validate",
        "name": "Validate Hypothesis",
        "description": "Test a specific claim or hypothesis",
        "stages": [
            {
                "agents": ["research"],
                "task": "gather_evidence",
                "parallel": False,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["ackoff"],
                "task": "apply_dikw",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["validation"],
                "task": "final_assessment",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": True,
            },
        ],
        "synthesis_mode": "consensus",
        "estimated_seconds": 130,
        "min_confidence": 0.75,
    },

    "full_analysis": {
        "id": "full_analysis",
        "name": "Full Analysis",
        "description": "Comprehensive multi-agent analysis",
        "stages": [
            {
                "agents": ["tta", "research"],
                "task": "initial_exploration",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["jtbd", "scurve"],
                "task": "market_and_timing",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": True,
            },
            {
                "agents": ["redteam", "ackoff"],
                "task": "challenge_and_validate",
                "parallel": True,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["scenario"],
                "task": "future_scenarios",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
            {
                "agents": ["larry"],
                "task": "final_synthesis",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": False,
            },
        ],
        "synthesis_mode": "sequential",
        "estimated_seconds": 240,
        "min_confidence": 0.5,
    },
}
```

### Custom Workflow Builder

```python
def create_custom_workflow(
    agents: List[str],
    parallel_groups: List[List[str]] = None,
    validation_points: List[int] = None,
) -> WorkflowRecipe:
    """
    Create a custom workflow from agent selection.

    Args:
        agents: List of agent IDs in order
        parallel_groups: Groups of agents to run in parallel
        validation_points: Stage indices where Red Team validates

    Returns:
        Custom WorkflowRecipe
    """
    stages = []

    if parallel_groups:
        for group in parallel_groups:
            stages.append({
                "agents": group,
                "task": f"parallel_{'-'.join(group)}",
                "parallel": len(group) > 1,
                "timeout_seconds": 60,
                "skip_if": None,
                "validation": len(stages) in (validation_points or []),
            })
    else:
        # Sequential by default
        for i, agent in enumerate(agents):
            stages.append({
                "agents": [agent],
                "task": f"run_{agent}",
                "parallel": False,
                "timeout_seconds": 45,
                "skip_if": None,
                "validation": i in (validation_points or []),
            })

    return {
        "id": "custom",
        "name": "Custom Workflow",
        "description": f"Custom: {', '.join(agents)}",
        "stages": stages,
        "synthesis_mode": "sequential",
        "estimated_seconds": len(stages) * 45,
        "min_confidence": 0.0,
    }
```

---

## Orchestrator Architecture

### State Definition

```python
# protocols/orchestrator_state.py

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class OrchestratorStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StageResult(TypedDict):
    """Result from a single stage."""
    stage_index: int
    agents: List[str]
    task: str
    outputs: Dict[str, Any]  # agent_id -> output
    validation_result: Optional[Dict]
    started_at: str
    completed_at: str
    duration_ms: int
    error: Optional[str]

class OrchestratorState(TypedDict):
    """Full orchestrator state."""
    # Identity
    session_id: str
    workflow_id: str
    workflow_name: str

    # Input
    original_query: str
    classification: Dict  # ClassificationResult as dict

    # Progress
    status: str  # OrchestratorStatus value
    current_stage: int
    total_stages: int
    stage_results: List[StageResult]

    # Context Management (from A2A architecture)
    artifacts: List[Dict]  # Validated evidence
    frames: Dict[str, List[Dict]]  # Agent-specific interpretations

    # Synthesis
    synthesis: Optional[Dict]
    confidence: float

    # Timing
    started_at: str
    estimated_completion: str
    last_update: str

    # Control
    paused_at: Optional[str]
    cancel_requested: bool
    error: Optional[str]
```

### Orchestrator Class

```python
# protocols/orchestrator.py

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional
import chainlit as cl

from .orchestrator_state import OrchestratorState, OrchestratorStatus, StageResult
from .workflow_recipes import WORKFLOWS, WorkflowRecipe
from .intent_classifier import classify_intent, ClassificationResult
from .context_manager import ContextManager, Artifact, Frame
from agents.multi_agent_graph import call_agent, synthesize_responses
from protocols.agent_registry import get_agent_config, can_agent_call

class AutoOrchestrator:
    """
    Orchestrates multi-agent workflows for "Find the Breakthrough" feature.

    Builds on existing multi_agent_graph.py with:
    - Intent-based workflow selection
    - Recipe-driven stage execution
    - Parallel agent execution within stages
    - Cross-cutting Red Team validation
    - Swarm synthesis algorithms
    """

    def __init__(
        self,
        session_id: str,
        progress_callback: Optional[Callable] = None,
        on_stage_complete: Optional[Callable] = None,
    ):
        self.session_id = session_id
        self.progress_callback = progress_callback
        self.on_stage_complete = on_stage_complete
        self.context_manager = ContextManager(session_id)
        self._cancel_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self.state: Optional[OrchestratorState] = None

    async def run(
        self,
        query: str,
        workflow_override: Optional[str] = None,
    ) -> OrchestratorState:
        """
        Main entry point for auto-orchestration.

        Args:
            query: User's question or request
            workflow_override: Force a specific workflow (bypasses classification)

        Returns:
            Final orchestrator state with synthesis
        """
        # Step 1: Classify intent
        classification = classify_intent(query)

        # Step 2: Select workflow
        if workflow_override and workflow_override in WORKFLOWS:
            workflow = WORKFLOWS[workflow_override]
        elif classification.workflow_type.value in WORKFLOWS:
            workflow = WORKFLOWS[classification.workflow_type.value]
        else:
            workflow = WORKFLOWS["full_analysis"]

        # Step 3: Initialize state
        self.state = self._init_state(query, classification, workflow)

        # Step 4: Add initial artifact
        self.context_manager.add_artifact(Artifact(
            type="user_input",
            content=query,
            source="user",
        ))

        # Step 5: Execute stages
        try:
            await self._execute_workflow(workflow)
        except asyncio.CancelledError:
            self.state["status"] = OrchestratorStatus.CANCELLED.value
            self.state["error"] = "Cancelled by user"
        except Exception as e:
            self.state["status"] = OrchestratorStatus.FAILED.value
            self.state["error"] = str(e)

        # Step 6: Synthesize results
        if self.state["status"] != OrchestratorStatus.FAILED.value:
            await self._synthesize()

        return self.state

    async def _execute_workflow(self, workflow: WorkflowRecipe):
        """Execute all stages in a workflow."""
        self.state["status"] = OrchestratorStatus.RUNNING.value

        for i, stage in enumerate(workflow["stages"]):
            # Check for cancellation
            if self._cancel_event.is_set():
                raise asyncio.CancelledError()

            # Check for pause
            while self._pause_event.is_set():
                await asyncio.sleep(0.5)

            # Check skip condition
            if stage.get("skip_if") and self._should_skip(stage["skip_if"]):
                continue

            # Update state
            self.state["current_stage"] = i
            self.state["last_update"] = datetime.utcnow().isoformat() + "Z"

            # Progress callback
            if self.progress_callback:
                await self.progress_callback({
                    "stage": i,
                    "total": len(workflow["stages"]),
                    "task": stage["task"],
                    "agents": stage["agents"],
                })

            # Execute stage
            stage_result = await self._execute_stage(i, stage)
            self.state["stage_results"].append(stage_result)

            # Apply validation if requested
            if stage.get("validation"):
                validation_result = await self._apply_validation(stage_result)
                stage_result["validation_result"] = validation_result

            # Stage complete callback
            if self.on_stage_complete:
                await self.on_stage_complete(stage_result)

        self.state["status"] = OrchestratorStatus.COMPLETED.value

    async def _execute_stage(
        self,
        stage_index: int,
        stage: dict,
    ) -> StageResult:
        """Execute a single stage, potentially with parallel agents."""
        started_at = datetime.utcnow()
        outputs = {}

        agents = stage["agents"]
        timeout = stage.get("timeout_seconds", 60)

        # Get context for agents
        context = self._build_agent_context()

        if stage.get("parallel") and len(agents) > 1:
            # Parallel execution
            tasks = []
            for agent_id in agents:
                task = asyncio.create_task(
                    self._call_agent_with_context(agent_id, context)
                )
                tasks.append((agent_id, task))

            # Wait with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*[t for _, t in tasks], return_exceptions=True),
                    timeout=timeout,
                )
                for (agent_id, _), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        outputs[agent_id] = {"error": str(result)}
                    else:
                        outputs[agent_id] = result
            except asyncio.TimeoutError:
                outputs["_timeout"] = True
        else:
            # Sequential execution
            for agent_id in agents:
                try:
                    result = await asyncio.wait_for(
                        self._call_agent_with_context(agent_id, context),
                        timeout=timeout,
                    )
                    outputs[agent_id] = result

                    # Add to context for next agent
                    context += f"\n\n{agent_id}: {result.get('response', '')}"
                except asyncio.TimeoutError:
                    outputs[agent_id] = {"error": "Timeout"}
                except Exception as e:
                    outputs[agent_id] = {"error": str(e)}

        completed_at = datetime.utcnow()

        return {
            "stage_index": stage_index,
            "agents": agents,
            "task": stage["task"],
            "outputs": outputs,
            "validation_result": None,
            "started_at": started_at.isoformat() + "Z",
            "completed_at": completed_at.isoformat() + "Z",
            "duration_ms": int((completed_at - started_at).total_seconds() * 1000),
            "error": None,
        }

    async def _call_agent_with_context(
        self,
        agent_id: str,
        context: str,
    ) -> dict:
        """Call an agent with current context."""
        query = self.state["original_query"]

        # Get agent-specific context (artifacts + own frames)
        agent_context = self.context_manager.get_context_for_agent(agent_id)

        # Build full prompt
        full_query = f"{query}\n\n{context}"
        if agent_context["artifacts"]:
            artifact_summary = "\n".join([
                f"- {a['content'][:100]}" for a in agent_context["artifacts"]
            ])
            full_query += f"\n\nValidated findings:\n{artifact_summary}"

        # Call agent using existing infrastructure
        response = await call_agent(agent_id, full_query, context)

        # Extract any frames (hypotheses/assumptions) and store them
        if self._contains_hypothesis(response):
            self.context_manager.add_frame(
                agent=agent_id,
                content=response,
                frame_type="hypothesis",
                confidence=0.6,
            )

        return {"response": response, "agent_id": agent_id}

    async def _apply_validation(self, stage_result: StageResult) -> dict:
        """Apply Red Team validation to stage outputs."""
        # Collect claims from stage
        claims = []
        for agent_id, output in stage_result["outputs"].items():
            if isinstance(output, dict) and "response" in output:
                claims.append({
                    "agent": agent_id,
                    "claim": output["response"],
                })

        # Run Red Team validation (using existing redteam agent)
        validation_prompt = f"""
        Validate these claims from the analysis:

        {claims}

        For each claim:
        1. Is this supported by evidence?
        2. What assumptions are being made?
        3. What could make this wrong?

        Return a validation assessment.
        """

        validation_result = await call_agent("redteam", validation_prompt, "")

        return {
            "claims_validated": len(claims),
            "validation_output": validation_result,
        }

    async def _synthesize(self):
        """Synthesize all stage results into final output."""
        # Collect all agent responses
        all_responses = {}
        for stage_result in self.state["stage_results"]:
            for agent_id, output in stage_result["outputs"].items():
                if isinstance(output, dict) and "response" in output:
                    all_responses[agent_id] = output["response"]

        # Use existing synthesis from multi_agent_graph
        synthesis = await synthesize_responses(
            self.state["original_query"],
            all_responses,
        )

        self.state["synthesis"] = {
            "summary": synthesis,
            "agent_count": len(all_responses),
            "stages_completed": len(self.state["stage_results"]),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        # Calculate confidence based on validation results and agreement
        self.state["confidence"] = self._calculate_confidence()

    def _calculate_confidence(self) -> float:
        """Calculate overall confidence in synthesis."""
        scores = []

        # Factor 1: Validation pass rate
        validations = [
            sr["validation_result"]
            for sr in self.state["stage_results"]
            if sr.get("validation_result")
        ]
        if validations:
            scores.append(0.8)  # Validations were run

        # Factor 2: No errors
        errors = sum(
            1 for sr in self.state["stage_results"]
            if sr.get("error") or "_timeout" in sr.get("outputs", {})
        )
        if errors == 0:
            scores.append(1.0)
        else:
            scores.append(max(0.3, 1.0 - (errors * 0.2)))

        # Factor 3: Agent agreement (simplified)
        # In full implementation, would analyze semantic similarity
        scores.append(0.7)  # Placeholder

        return sum(scores) / len(scores) if scores else 0.5

    def pause(self):
        """Pause workflow execution."""
        self._pause_event.set()
        self.state["status"] = OrchestratorStatus.PAUSED.value
        self.state["paused_at"] = datetime.utcnow().isoformat() + "Z"

    def resume(self):
        """Resume workflow execution."""
        self._pause_event.clear()
        self.state["status"] = OrchestratorStatus.RUNNING.value
        self.state["paused_at"] = None

    def cancel(self):
        """Cancel workflow execution."""
        self._cancel_event.set()
        self.state["cancel_requested"] = True

    def _init_state(
        self,
        query: str,
        classification: ClassificationResult,
        workflow: WorkflowRecipe,
    ) -> OrchestratorState:
        """Initialize orchestrator state."""
        now = datetime.utcnow()
        estimated_completion = now + timedelta(seconds=workflow["estimated_seconds"])

        return {
            "session_id": self.session_id,
            "workflow_id": workflow["id"],
            "workflow_name": workflow["name"],
            "original_query": query,
            "classification": classification.model_dump() if hasattr(classification, 'model_dump') else classification.__dict__,
            "status": OrchestratorStatus.PENDING.value,
            "current_stage": 0,
            "total_stages": len(workflow["stages"]),
            "stage_results": [],
            "artifacts": [],
            "frames": {},
            "synthesis": None,
            "confidence": 0.0,
            "started_at": now.isoformat() + "Z",
            "estimated_completion": estimated_completion.isoformat() + "Z",
            "last_update": now.isoformat() + "Z",
            "paused_at": None,
            "cancel_requested": False,
            "error": None,
        }

    def _build_agent_context(self) -> str:
        """Build context string from previous stage results."""
        context_parts = []
        for sr in self.state["stage_results"]:
            for agent_id, output in sr["outputs"].items():
                if isinstance(output, dict) and "response" in output:
                    agent_name = get_agent_config(agent_id)
                    name = agent_name.name if agent_name else agent_id
                    context_parts.append(f"**{name}:** {output['response'][:500]}")
        return "\n\n".join(context_parts)

    def _should_skip(self, condition: str) -> bool:
        """Check if a stage should be skipped."""
        if condition == "no_entities":
            return len(self.state["classification"].get("signals", {}).get("entities_mentioned", [])) == 0
        if condition == "low_score":
            # Check if grading stage produced low score
            for sr in self.state["stage_results"]:
                if "pws_grading" in sr["agents"]:
                    # Parse score from response (simplified)
                    return False  # Don't skip by default
        return False

    def _contains_hypothesis(self, response: str) -> bool:
        """Check if response contains hypothesis language."""
        hypothesis_markers = [
            "hypothesis", "assume", "if we", "might be",
            "could be", "speculation", "theory", "believe",
        ]
        response_lower = response.lower()
        return any(marker in response_lower for marker in hypothesis_markers)
```

---

## Parallel Execution Strategy

### Parallelization Rules

1. **Within-Stage Parallelism**: Agents in the same stage run concurrently
2. **Cross-Stage Sequencing**: Stages run in order (context dependency)
3. **Validation Checkpoints**: Red Team validation can be parallel with next stage prep

### Execution Diagram

```
Timeline:
0s        20s       40s       60s       80s       100s      120s
├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│         │         │         │         │         │         │
│  Stage 1: Expand Domains                                  │
│  ┌───────────────────────────┐                           │
│  │ TTA      ████████████████ │                           │
│  │ Research ██████████████   │ (parallel)                │
│  └───────────────────────────┘                           │
│                    │                                      │
│                    ▼ (context handoff)                    │
│  Stage 2: Find Jobs                                       │
│  ┌───────────────────────────┐                           │
│  │ JTBD     ████████████████ │                           │
│  └───────────────────────────┘                           │
│                    │                                      │
│             ┌──────┴──────┐                              │
│             │ Red Team    │ (validation checkpoint)       │
│             │ Validation  │                               │
│             └─────────────┘                              │
│                    │                                      │
│  Stage 3: Validate                                        │
│  ┌───────────────────────────┐                           │
│  │ Ackoff    ███████████████ │                           │
│  │ Validation ██████████████ │ (parallel)                │
│  └───────────────────────────┘                           │
│                    │                                      │
│  Stage 4: Synthesize                                      │
│  ┌───────────────────────────┐                           │
│  │ Larry     ██████████████  │                           │
│  └───────────────────────────┘                           │
└──────────────────────────────────────────────────────────┘
```

### Implementation Details

```python
# protocols/parallel_executor.py

import asyncio
from typing import List, Dict, Callable, Any

class ParallelAgentExecutor:
    """
    Executes multiple agents in parallel with proper error handling.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout_seconds: int = 60,
    ):
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_parallel(
        self,
        agent_tasks: List[Dict],
        shared_context: str = "",
    ) -> Dict[str, Any]:
        """
        Execute multiple agent tasks in parallel.

        Args:
            agent_tasks: List of {"agent_id": str, "query": str}
            shared_context: Context available to all agents

        Returns:
            Dict of agent_id -> result
        """
        async def run_with_semaphore(agent_id: str, query: str):
            async with self._semaphore:
                return await self._call_agent(agent_id, query, shared_context)

        tasks = [
            asyncio.create_task(
                run_with_semaphore(t["agent_id"], t["query"])
            )
            for t in agent_tasks
        ]

        # Wait for all with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            results = [{"error": "Timeout"} for _ in tasks]

        # Map results to agent IDs
        output = {}
        for agent_task, result in zip(agent_tasks, results):
            agent_id = agent_task["agent_id"]
            if isinstance(result, Exception):
                output[agent_id] = {"error": str(result)}
            else:
                output[agent_id] = result

        return output

    async def _call_agent(
        self,
        agent_id: str,
        query: str,
        context: str,
    ) -> Dict:
        """Call agent with retry logic."""
        from agents.multi_agent_graph import call_agent

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await call_agent(agent_id, query, context)
                return {"response": response, "agent_id": agent_id}
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"error": str(e), "agent_id": agent_id}
                await asyncio.sleep(1)  # Brief retry delay
```

---

## Swarm Synthesis Algorithm

### Overview

The swarm synthesis combines outputs from multiple agents into a coherent recommendation.

### Algorithm Components

1. **Claim Extraction**: Extract key claims from each agent
2. **Agreement Analysis**: Identify consensus and conflicts
3. **Confidence Weighting**: Weight by agent expertise and validation
4. **Conflict Resolution**: Resolve disagreements
5. **Final Synthesis**: Generate actionable recommendation

### Implementation

```python
# protocols/swarm_synthesis.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AgreementLevel(Enum):
    CONSENSUS = "consensus"     # All agents agree
    MAJORITY = "majority"       # Most agents agree
    SPLIT = "split"             # No clear majority
    CONFLICT = "conflict"       # Direct contradiction

@dataclass
class ExtractedClaim:
    """A claim extracted from an agent's response."""
    agent_id: str
    claim: str
    confidence: float
    evidence: Optional[str] = None
    is_validated: bool = False

@dataclass
class SynthesisResult:
    """Result of swarm synthesis."""
    summary: str
    key_insights: List[str]
    recommendations: List[str]
    conflicts: List[Dict]
    confidence: float
    agreement_level: AgreementLevel
    agent_contributions: Dict[str, str]

async def synthesize_swarm(
    agent_responses: Dict[str, str],
    query: str,
    validation_results: Optional[Dict] = None,
    mode: str = "sequential",  # sequential, parallel, consensus
) -> SynthesisResult:
    """
    Synthesize multiple agent responses into a coherent recommendation.

    Args:
        agent_responses: Dict of agent_id -> response text
        query: Original user query
        validation_results: Optional Red Team validation results
        mode: Synthesis mode
            - sequential: Build on each response
            - parallel: Compare independent analyses
            - consensus: Find areas of agreement

    Returns:
        SynthesisResult with recommendations and confidence
    """
    # Step 1: Extract claims from each agent
    all_claims = []
    for agent_id, response in agent_responses.items():
        claims = await _extract_claims(agent_id, response)
        all_claims.extend(claims)

    # Step 2: Analyze agreement
    agreement = _analyze_agreement(all_claims)

    # Step 3: Apply confidence weighting
    weighted_claims = _apply_weights(all_claims, validation_results)

    # Step 4: Resolve conflicts
    resolved_conflicts = []
    if agreement in [AgreementLevel.SPLIT, AgreementLevel.CONFLICT]:
        resolved_conflicts = await _resolve_conflicts(weighted_claims, mode)

    # Step 5: Generate synthesis based on mode
    if mode == "consensus":
        synthesis = await _consensus_synthesis(weighted_claims, query)
    elif mode == "parallel":
        synthesis = await _parallel_synthesis(agent_responses, query)
    else:
        synthesis = await _sequential_synthesis(agent_responses, query)

    return SynthesisResult(
        summary=synthesis["summary"],
        key_insights=synthesis["insights"],
        recommendations=synthesis["recommendations"],
        conflicts=resolved_conflicts,
        confidence=_calculate_synthesis_confidence(weighted_claims, agreement),
        agreement_level=agreement,
        agent_contributions={
            aid: _summarize_contribution(resp)
            for aid, resp in agent_responses.items()
        },
    )

async def _extract_claims(agent_id: str, response: str) -> List[ExtractedClaim]:
    """Extract key claims from agent response."""
    # Use LLM to extract claims
    from google import genai
    from google.genai import types

    client = genai.Client()

    extraction_prompt = f"""
    Extract the key claims from this analysis.
    For each claim, provide:
    1. The claim itself (one sentence)
    2. Any evidence mentioned
    3. Confidence level (0-1)

    Response:
    {response}

    Format as JSON: [{{"claim": "...", "evidence": "...", "confidence": 0.X}}]
    """

    try:
        result = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=extraction_prompt,
            config=types.GenerateContentConfig(temperature=0.2),
        )

        import json
        claims_data = json.loads(result.text)
        return [
            ExtractedClaim(
                agent_id=agent_id,
                claim=c["claim"],
                confidence=c.get("confidence", 0.5),
                evidence=c.get("evidence"),
            )
            for c in claims_data
        ]
    except Exception:
        # Fallback: treat entire response as single claim
        return [ExtractedClaim(
            agent_id=agent_id,
            claim=response[:500],
            confidence=0.5,
        )]

def _analyze_agreement(claims: List[ExtractedClaim]) -> AgreementLevel:
    """Analyze level of agreement between claims."""
    if len(claims) < 2:
        return AgreementLevel.CONSENSUS

    # Group claims by semantic similarity (simplified)
    # In production, would use embeddings
    agents = set(c.agent_id for c in claims)

    # Simple heuristic: check for contradiction markers
    contradiction_markers = ["however", "but", "disagree", "contrary", "wrong"]
    has_contradictions = any(
        any(m in c.claim.lower() for m in contradiction_markers)
        for c in claims
    )

    if has_contradictions:
        return AgreementLevel.CONFLICT
    elif len(agents) >= 3:
        return AgreementLevel.MAJORITY
    else:
        return AgreementLevel.CONSENSUS

def _apply_weights(
    claims: List[ExtractedClaim],
    validation_results: Optional[Dict] = None,
) -> List[ExtractedClaim]:
    """Apply confidence weights based on validation and agent expertise."""
    # Agent expertise weights
    AGENT_WEIGHTS = {
        "ackoff": 1.2,      # DIKW adds credibility
        "redteam": 1.1,     # Challenges are valuable
        "research": 1.15,   # Data-backed
        "tta": 1.0,         # Speculative
        "jtbd": 1.05,       # Customer-focused
        "larry": 1.0,       # General
    }

    for claim in claims:
        weight = AGENT_WEIGHTS.get(claim.agent_id, 1.0)

        # Boost if validated
        if validation_results and claim.is_validated:
            weight *= 1.2

        claim.confidence *= weight
        claim.confidence = min(1.0, claim.confidence)  # Cap at 1.0

    return claims

async def _resolve_conflicts(
    claims: List[ExtractedClaim],
    mode: str,
) -> List[Dict]:
    """Resolve conflicts between claims."""
    conflicts = []

    # Group claims by topic (simplified)
    # In production, would cluster by embeddings

    # For now, identify claims that seem to contradict
    for i, claim1 in enumerate(claims):
        for claim2 in claims[i+1:]:
            if claim1.agent_id != claim2.agent_id:
                # Check for potential conflict
                if _claims_conflict(claim1.claim, claim2.claim):
                    resolution = _resolve_pair(claim1, claim2, mode)
                    conflicts.append({
                        "claim1": {"agent": claim1.agent_id, "text": claim1.claim},
                        "claim2": {"agent": claim2.agent_id, "text": claim2.claim},
                        "resolution": resolution,
                    })

    return conflicts

def _claims_conflict(claim1: str, claim2: str) -> bool:
    """Check if two claims potentially conflict."""
    # Simplified conflict detection
    negation_words = ["not", "no", "never", "unlikely", "impossible"]

    c1_words = set(claim1.lower().split())
    c2_words = set(claim2.lower().split())

    # Check if one has negation of shared concept
    shared = c1_words & c2_words
    c1_negated = bool(c1_words & set(negation_words))
    c2_negated = bool(c2_words & set(negation_words))

    return len(shared) > 3 and c1_negated != c2_negated

def _resolve_pair(
    claim1: ExtractedClaim,
    claim2: ExtractedClaim,
    mode: str,
) -> str:
    """Resolve conflict between two claims."""
    if mode == "consensus":
        # In consensus mode, highlight both and require user decision
        return "Requires user decision: both perspectives have merit"
    elif claim1.confidence > claim2.confidence + 0.2:
        return f"Favoring {claim1.agent_id} (higher confidence)"
    elif claim2.confidence > claim1.confidence + 0.2:
        return f"Favoring {claim2.agent_id} (higher confidence)"
    else:
        return "No clear resolution - recommending further investigation"

async def _sequential_synthesis(
    agent_responses: Dict[str, str],
    query: str,
) -> Dict:
    """Generate synthesis in sequential mode (agents build on each other)."""
    # Use existing synthesize_responses from multi_agent_graph
    from agents.multi_agent_graph import synthesize_responses

    synthesis = await synthesize_responses(query, agent_responses)

    return {
        "summary": synthesis,
        "insights": _extract_bullet_points(synthesis),
        "recommendations": _extract_recommendations(synthesis),
    }

async def _consensus_synthesis(
    claims: List[ExtractedClaim],
    query: str,
) -> Dict:
    """Generate synthesis focused on consensus points."""
    # Group claims by confidence
    high_confidence = [c for c in claims if c.confidence > 0.7]

    if high_confidence:
        consensus_points = "\n".join([f"- {c.claim}" for c in high_confidence])
        summary = f"Strong consensus on:\n{consensus_points}"
    else:
        summary = "No strong consensus - multiple valid perspectives"

    return {
        "summary": summary,
        "insights": [c.claim for c in high_confidence[:5]],
        "recommendations": ["Validate key assumptions before proceeding"],
    }

async def _parallel_synthesis(
    agent_responses: Dict[str, str],
    query: str,
) -> Dict:
    """Generate synthesis from parallel perspectives."""
    perspectives = []
    for agent_id, response in agent_responses.items():
        perspectives.append(f"**{agent_id.upper()}**: {response[:200]}...")

    return {
        "summary": "Multiple independent perspectives gathered",
        "insights": perspectives[:5],
        "recommendations": ["Compare and contrast viewpoints"],
    }

def _calculate_synthesis_confidence(
    claims: List[ExtractedClaim],
    agreement: AgreementLevel,
) -> float:
    """Calculate overall synthesis confidence."""
    base_confidence = {
        AgreementLevel.CONSENSUS: 0.85,
        AgreementLevel.MAJORITY: 0.7,
        AgreementLevel.SPLIT: 0.5,
        AgreementLevel.CONFLICT: 0.4,
    }

    # Average claim confidence
    if claims:
        avg_claim_confidence = sum(c.confidence for c in claims) / len(claims)
    else:
        avg_claim_confidence = 0.5

    return (base_confidence[agreement] + avg_claim_confidence) / 2

def _extract_bullet_points(text: str) -> List[str]:
    """Extract bullet points from text."""
    import re
    bullets = re.findall(r'[-*]\s*(.+?)(?=\n[-*]|\n\n|$)', text, re.DOTALL)
    return [b.strip() for b in bullets[:5]]

def _extract_recommendations(text: str) -> List[str]:
    """Extract recommendations from text."""
    import re
    # Look for recommendation patterns
    patterns = [
        r'recommend[s]?\s*(?:to|that)?\s*(.+?)(?:\.|$)',
        r'should\s+(.+?)(?:\.|$)',
        r'next step[s]?[:\s]+(.+?)(?:\.|$)',
    ]

    recommendations = []
    for pattern in patterns:
        matches = re.findall(pattern, text.lower(), re.IGNORECASE)
        recommendations.extend(matches[:3])

    return list(set(recommendations))[:5]

def _summarize_contribution(response: str) -> str:
    """Summarize an agent's contribution."""
    # Take first sentence or first 100 chars
    sentences = response.split('.')
    if sentences:
        return sentences[0][:100] + "..."
    return response[:100] + "..."
```

---

## Context Management

### Integration with A2A Architecture

The orchestrator uses the Artifacts vs Frames pattern from `A2A_PRACTICAL_ARCHITECTURE.md`:

```python
# protocols/orchestrator_context.py

from protocols.context_manager import ContextManager, Artifact, Frame

class OrchestratorContextManager(ContextManager):
    """
    Extended context manager for auto-orchestration.

    Manages:
    - Artifacts: Validated findings visible to all agents
    - Frames: Agent-specific hypotheses (don't leak)
    - Stage context: What each stage produced
    """

    def __init__(self, session_id: str):
        super().__init__(session_id)
        self._stage_outputs: Dict[int, Dict] = {}

    def record_stage_output(
        self,
        stage_index: int,
        agent_id: str,
        output: str,
        is_validated: bool = False,
    ):
        """Record output from a stage for context building."""
        if stage_index not in self._stage_outputs:
            self._stage_outputs[stage_index] = {}

        self._stage_outputs[stage_index][agent_id] = {
            "output": output,
            "is_validated": is_validated,
        }

        # If validated, promote to artifact
        if is_validated:
            self.add_artifact(Artifact(
                type="validated_insight",
                content=output,
                source=agent_id,
                validation_source="red_team",
            ))
        else:
            # Store as frame (doesn't leak to other agents)
            self.add_frame(
                agent=agent_id,
                content=output,
                frame_type="hypothesis",
                confidence=0.5,
            )

    def get_context_for_stage(self, stage_index: int) -> str:
        """Get cumulative context for a stage."""
        context_parts = []

        # All artifacts (validated)
        for artifact in self._artifacts.values():
            context_parts.append(
                f"[VALIDATED - {artifact.source}]: {artifact.content[:200]}"
            )

        # Previous stage outputs (summarized)
        for i in range(stage_index):
            if i in self._stage_outputs:
                for agent_id, data in self._stage_outputs[i].items():
                    prefix = "VALIDATED" if data["is_validated"] else "Pending"
                    context_parts.append(
                        f"[{prefix} - {agent_id}]: {data['output'][:200]}"
                    )

        return "\n\n".join(context_parts)
```

---

## UI Integration Plan

### Chainlit Custom Elements

```python
# public/elements/OrchestrationProgress.jsx (design specification)

"""
OrchestrationProgress Component
==============================
Displays real-time orchestration progress.

Props:
- workflow: {id, name, stages: [{agents, task, status}]}
- currentStage: number
- progress: {percent, estimatedTimeRemaining}
- agentOutputs: {agentId: {status, preview}}

States:
- running: Show progress bar and active agents
- paused: Show pause indicator with resume button
- completed: Show summary with expand option
- error: Show error with retry option

Actions:
- pause: Pause workflow
- resume: Resume workflow
- cancel: Cancel workflow
- adjustAgents: Modify agents (opens modal)
- expandStage: Show full stage output
"""
```

### Canvas Layout

```python
# utils/canvas_layout.py

async def render_orchestration_canvas(
    state: OrchestratorState,
    synthesis: SynthesisResult,
) -> List[cl.Element]:
    """
    Render orchestration results on Chainlit canvas.

    Returns list of Chainlit elements for display.
    """
    elements = []

    # 1. Progress indicator (if still running)
    if state["status"] == "running":
        progress_element = cl.CustomElement(
            name="OrchestrationProgress",
            props={
                "workflow": {
                    "id": state["workflow_id"],
                    "name": state["workflow_name"],
                    "stages": _format_stages(state),
                },
                "currentStage": state["current_stage"],
                "progress": _calculate_progress(state),
            },
            display="inline",
        )
        elements.append(progress_element)

    # 2. Agent cards (one per agent that contributed)
    for agent_id, contribution in synthesis.agent_contributions.items():
        agent_card = cl.CustomElement(
            name="AgentCard",
            props={
                "agentId": agent_id,
                "agentName": _get_agent_name(agent_id),
                "icon": _get_agent_icon(agent_id),
                "contribution": contribution,
                "expandable": True,
            },
            display="inline",
        )
        elements.append(agent_card)

    # 3. Synthesis panel
    synthesis_panel = cl.CustomElement(
        name="SynthesisPanel",
        props={
            "summary": synthesis.summary,
            "insights": synthesis.key_insights,
            "recommendations": synthesis.recommendations,
            "confidence": synthesis.confidence,
            "agreementLevel": synthesis.agreement_level.value,
        },
        display="inline",
    )
    elements.append(synthesis_panel)

    # 4. Action buttons
    actions_element = cl.CustomElement(
        name="BreakthroughActions",
        props={
            "actions": [
                {"id": "export", "label": "Export Report", "icon": "download"},
                {"id": "dig_deeper", "label": "Dig Deeper", "icon": "search"},
                {"id": "accept", "label": "Accept & Continue", "icon": "check"},
            ],
        },
        display="inline",
    )
    elements.append(actions_element)

    return elements
```

### Action Callbacks

```python
# Add to mindrian_chat.py

@cl.action_callback("find_breakthrough")
async def on_find_breakthrough(action: cl.Action):
    """Handle 'Find Breakthrough' button click."""
    from protocols.orchestrator import AutoOrchestrator

    session_id = cl.user_session.get("id")
    history = cl.user_session.get("history", [])

    # Get the most recent user message as query
    query = None
    for msg in reversed(history):
        if msg.get("role") == "user":
            query = msg.get("content")
            break

    if not query:
        await cl.Message(
            content="Please describe what you'd like to analyze first."
        ).send()
        return

    # Progress callback
    progress_msg = cl.Message(content="")
    await progress_msg.send()

    async def on_progress(update):
        stage = update.get("stage", 0)
        total = update.get("total", 1)
        task = update.get("task", "")
        agents = ", ".join(update.get("agents", []))

        await progress_msg.stream_token(
            f"\n**Stage {stage + 1}/{total}:** {task}\n"
            f"Running: {agents}\n"
        )

    # Run orchestration
    orchestrator = AutoOrchestrator(
        session_id=session_id,
        progress_callback=on_progress,
    )

    result = await orchestrator.run(query)

    # Display results
    from protocols.swarm_synthesis import synthesize_swarm

    if result["synthesis"]:
        synthesis = await synthesize_swarm(
            agent_responses={
                sr["agents"][0]: sr["outputs"].get(sr["agents"][0], {}).get("response", "")
                for sr in result["stage_results"]
                if sr["outputs"]
            },
            query=query,
        )

        elements = await render_orchestration_canvas(result, synthesis)

        await cl.Message(
            content=f"## Breakthrough Analysis Complete\n\n"
                   f"**Confidence:** {synthesis.confidence:.0%}\n\n"
                   f"{synthesis.summary}",
            elements=elements,
        ).send()
    else:
        await cl.Message(
            content=f"Analysis could not be completed: {result.get('error', 'Unknown error')}"
        ).send()
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Week 1-2)

- [ ] **1.1 Intent Classifier**
  - [ ] Create `protocols/intent_classifier.py`
  - [ ] Implement pattern-based classification
  - [ ] Add LLM fallback for low-confidence cases
  - [ ] Write 30+ test cases
  - [ ] Integrate with existing `protocols/classifier.py`

- [ ] **1.2 Workflow Recipes**
  - [ ] Create `protocols/workflow_recipes.py`
  - [ ] Define 6 core workflows
  - [ ] Add custom workflow builder
  - [ ] Test recipe validation

- [ ] **1.3 Orchestrator State**
  - [ ] Create `protocols/orchestrator_state.py`
  - [ ] Define TypedDict schemas
  - [ ] Add serialization/deserialization

### Phase 2: Execution Engine (Week 2-3)

- [ ] **2.1 Orchestrator Core**
  - [ ] Create `protocols/orchestrator.py`
  - [ ] Implement stage execution
  - [ ] Add pause/resume/cancel support
  - [ ] Integrate with existing `multi_agent_graph.py`

- [ ] **2.2 Parallel Executor**
  - [ ] Create `protocols/parallel_executor.py`
  - [ ] Implement semaphore-based parallelism
  - [ ] Add timeout handling
  - [ ] Add retry logic

- [ ] **2.3 Context Management**
  - [ ] Extend `protocols/context_manager.py`
  - [ ] Implement stage context tracking
  - [ ] Add artifact promotion

### Phase 3: Synthesis (Week 3-4)

- [ ] **3.1 Swarm Synthesis**
  - [ ] Create `protocols/swarm_synthesis.py`
  - [ ] Implement claim extraction
  - [ ] Add agreement analysis
  - [ ] Implement conflict resolution

- [ ] **3.2 Red Team Integration**
  - [ ] Wire validation checkpoints
  - [ ] Implement cross-cutting validation
  - [ ] Add confidence adjustments

### Phase 4: UI Integration (Week 4-5)

- [ ] **4.1 Custom Elements**
  - [ ] Create `public/elements/OrchestrationProgress.jsx`
  - [ ] Create `public/elements/AgentCard.jsx`
  - [ ] Create `public/elements/SynthesisPanel.jsx`
  - [ ] Create `public/elements/BreakthroughActions.jsx`

- [ ] **4.2 Action Callbacks**
  - [ ] Add `find_breakthrough` callback
  - [ ] Add `pause_orchestration` callback
  - [ ] Add `resume_orchestration` callback
  - [ ] Add `adjust_agents` callback
  - [ ] Add `export_breakthrough` callback

- [ ] **4.3 Canvas Rendering**
  - [ ] Create `utils/canvas_layout.py`
  - [ ] Implement progressive display
  - [ ] Add expand/collapse behavior

### Phase 5: Testing & Polish (Week 5-6)

- [ ] **5.1 Integration Testing**
  - [ ] Test full workflows end-to-end
  - [ ] Test edge cases (timeouts, errors, cancellation)
  - [ ] Test with real user queries

- [ ] **5.2 Performance Optimization**
  - [ ] Profile execution time
  - [ ] Optimize parallel execution
  - [ ] Add caching where appropriate

- [ ] **5.3 Documentation**
  - [ ] Update CLAUDE.md
  - [ ] Add user-facing help text
  - [ ] Document API

---

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent timeout cascade | Medium | High | Independent timeouts per agent; partial results acceptable |
| Classification misfire | Medium | Medium | Conservative routing; default to Larry for guidance |
| Context overflow | Low | High | Bounded context windows; summarization at stage boundaries |
| Synthesis hallucination | Medium | Medium | Ground in agent outputs; confidence scoring |
| UI lag with streaming | Low | Medium | Debounced updates; skeleton loading |

### User Experience Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Over-automation | Medium | High | Always show what's happening; easy pause/adjust |
| Confusing results | Medium | Medium | Clear source attribution; expandable cards |
| Long wait times | High | Medium | Progress indicators; estimated time; partial results |
| Loss of control | Medium | High | Cancel always available; adjust agents mid-run |

### Mitigation Strategy

1. **Fallback to Manual**: If orchestration fails, fall back to current bot-switching UX
2. **Progressive Enhancement**: Start with simple workflows, add complexity gradually
3. **User Override**: Always allow user to adjust agents or skip stages
4. **Transparency**: Show which agents contributed what, with confidence

---

## Future Enhancements (Post-Wave 4)

### Wave 5: Learning Orchestrator
- Learn from user feedback on synthesis quality
- Personalized workflow recommendations
- A/B testing of workflow recipes

### Wave 6: Collaborative Orchestration
- Multiple users running same workflow
- Real-time collaboration on synthesis
- Shared breakthrough boards

### Wave 7: External Integration
- Slack/Teams integration for breakthrough alerts
- Calendar integration for follow-up tasks
- CRM integration for opportunity tracking

---

## Appendix: File Locations

| File | Purpose | Status |
|------|---------|--------|
| `protocols/intent_classifier.py` | Intent classification | To Create |
| `protocols/workflow_recipes.py` | Workflow definitions | To Create |
| `protocols/orchestrator_state.py` | State definitions | To Create |
| `protocols/orchestrator.py` | Main orchestrator | To Create |
| `protocols/parallel_executor.py` | Parallel execution | To Create |
| `protocols/swarm_synthesis.py` | Synthesis algorithm | To Create |
| `protocols/orchestrator_context.py` | Context management | To Create |
| `public/elements/OrchestrationProgress.jsx` | Progress UI | To Create |
| `public/elements/AgentCard.jsx` | Agent result card | To Create |
| `public/elements/SynthesisPanel.jsx` | Synthesis display | To Create |
| `public/elements/BreakthroughActions.jsx` | Action buttons | To Create |
| `utils/canvas_layout.py` | Canvas rendering | To Create |
| `mindrian_chat.py` | Integration callbacks | To Update |
| `CLAUDE.md` | Documentation | To Update |

---

*This document is a design specification. Implementation should follow the phased checklist above.*
