"""
Auto-Orchestrator - Wave 4: "Find the Breakthrough"
Orchestrates multi-agent workflows for automated insight discovery.

Features:
- Intent-based workflow selection
- Recipe-driven stage execution
- Parallel agent execution within stages
- Real-time progress tracking
- Swarm synthesis algorithm
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field

from .intent_classifier import classify_intent, ClassificationResult, WorkflowType, get_workflow_description
from .workflow_recipes import WORKFLOWS, WorkflowRecipe, get_workflow


class OrchestratorStatus(Enum):
    """Orchestrator lifecycle status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StageResult:
    """Result from a single workflow stage."""
    stage_index: int
    agents: List[str]
    task: str
    outputs: Dict[str, Any]  # agent_id -> output
    validation_result: Optional[Dict] = None
    started_at: str = ""
    completed_at: str = ""
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class OrchestratorState:
    """Full orchestrator state."""
    # Identity
    session_id: str
    workflow_id: str
    workflow_name: str

    # Input
    original_query: str
    classification: Dict = field(default_factory=dict)

    # Progress
    status: str = OrchestratorStatus.PENDING.value
    current_stage: int = 0
    total_stages: int = 0
    stage_results: List[StageResult] = field(default_factory=list)

    # Synthesis
    synthesis: Optional[Dict] = None
    confidence: float = 0.0

    # Timing
    started_at: str = ""
    estimated_completion: str = ""
    last_update: str = ""

    # Control
    paused_at: Optional[str] = None
    cancel_requested: bool = False
    error: Optional[str] = None


class AutoOrchestrator:
    """
    Orchestrates multi-agent workflows for "Find the Breakthrough" feature.

    Usage:
        orchestrator = AutoOrchestrator(session_id, progress_callback)
        result = await orchestrator.run("I have reentry tech. Find opportunities.")
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
        self._cancel_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self.state: Optional[OrchestratorState] = None

    async def run(
        self,
        query: str,
        workflow_override: Optional[str] = None,
        history: Optional[List[Dict]] = None,
    ) -> OrchestratorState:
        """
        Main entry point for auto-orchestration.

        Args:
            query: User's question or request
            workflow_override: Force a specific workflow (bypasses classification)
            history: Conversation history for context

        Returns:
            Final orchestrator state with synthesis
        """
        history = history or []

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
        now = datetime.utcnow().isoformat() + "Z"
        estimated = datetime.utcnow() + timedelta(seconds=workflow["estimated_seconds"])

        self.state = OrchestratorState(
            session_id=self.session_id,
            workflow_id=workflow["id"],
            workflow_name=workflow["name"],
            original_query=query,
            classification={
                "workflow_type": classification.workflow_type.value,
                "cynefin_domain": classification.cynefin_domain,
                "pws_stage": classification.pws_stage,
                "recommended_agents": classification.recommended_agents,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
            },
            status=OrchestratorStatus.PENDING.value,
            current_stage=0,
            total_stages=len(workflow["stages"]),
            stage_results=[],
            started_at=now,
            estimated_completion=estimated.isoformat() + "Z",
            last_update=now,
        )

        # Step 4: Execute stages
        try:
            await self._execute_workflow(workflow, history)
        except asyncio.CancelledError:
            self.state.status = OrchestratorStatus.CANCELLED.value
            self.state.error = "Cancelled by user"
        except Exception as e:
            self.state.status = OrchestratorStatus.FAILED.value
            self.state.error = str(e)
            print(f"[ORCHESTRATOR] Error: {e}")

        # Step 5: Synthesize results
        if self.state.status not in [OrchestratorStatus.FAILED.value, OrchestratorStatus.CANCELLED.value]:
            await self._synthesize(query, workflow)

        return self.state

    async def _execute_workflow(self, workflow: WorkflowRecipe, history: List[Dict]):
        """Execute all stages in a workflow."""
        self.state.status = OrchestratorStatus.RUNNING.value

        for i, stage in enumerate(workflow["stages"]):
            # Check for cancellation
            if self._cancel_event.is_set():
                raise asyncio.CancelledError()

            # Check for pause
            while self._pause_event.is_set():
                await asyncio.sleep(0.5)

            # Update state
            self.state.current_stage = i
            self.state.last_update = datetime.utcnow().isoformat() + "Z"

            # Progress callback
            if self.progress_callback:
                await self.progress_callback({
                    "stage": i,
                    "total": len(workflow["stages"]),
                    "task": stage["task"],
                    "agents": stage["agents"],
                    "workflow_name": workflow["name"],
                })

            # Execute stage
            stage_result = await self._execute_stage(i, stage, history)
            self.state.stage_results.append(stage_result)

            # Stage complete callback
            if self.on_stage_complete:
                await self.on_stage_complete(stage_result)

        self.state.status = OrchestratorStatus.COMPLETED.value

    async def _execute_stage(
        self,
        stage_index: int,
        stage: dict,
        history: List[Dict],
    ) -> StageResult:
        """Execute a single stage, potentially with parallel agents."""
        started_at = datetime.utcnow()
        outputs = {}

        agents = stage["agents"]
        timeout = stage.get("timeout_seconds", 60)

        # Build context from previous stages
        context = self._build_context_from_stages()

        if stage.get("parallel") and len(agents) > 1:
            # Parallel execution
            tasks = []
            for agent_id in agents:
                task = asyncio.create_task(
                    self._call_agent(agent_id, self.state.original_query, context, history)
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
                for agent_id, task in tasks:
                    if not task.done():
                        task.cancel()
                        outputs[agent_id] = {"error": "Timeout"}
        else:
            # Sequential execution
            for agent_id in agents:
                try:
                    result = await asyncio.wait_for(
                        self._call_agent(agent_id, self.state.original_query, context, history),
                        timeout=timeout,
                    )
                    outputs[agent_id] = result

                    # Add to context for next agent
                    if isinstance(result, dict) and "response" in result:
                        context += f"\n\n**{agent_id.upper()}:**\n{result['response']}"
                except asyncio.TimeoutError:
                    outputs[agent_id] = {"error": "Timeout"}
                except Exception as e:
                    outputs[agent_id] = {"error": str(e)}

        completed_at = datetime.utcnow()

        return StageResult(
            stage_index=stage_index,
            agents=agents,
            task=stage["task"],
            outputs=outputs,
            started_at=started_at.isoformat() + "Z",
            completed_at=completed_at.isoformat() + "Z",
            duration_ms=int((completed_at - started_at).total_seconds() * 1000),
        )

    async def _call_agent(
        self,
        agent_id: str,
        query: str,
        context: str,
        history: List[Dict],
    ) -> dict:
        """Call an agent and get response."""
        try:
            # Try to use existing multi-agent infrastructure
            from agents.multi_agent_graph import call_agent as magi_call
            response = await magi_call(agent_id, query, context)
            return {"response": response, "agent_id": agent_id}
        except ImportError:
            # Fallback: call agent directly using Gemini
            return await self._direct_agent_call(agent_id, query, context, history)

    async def _direct_agent_call(
        self,
        agent_id: str,
        query: str,
        context: str,
        history: List[Dict],
    ) -> dict:
        """Direct agent call fallback using Gemini."""
        try:
            from google import genai
            from google.genai import types

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return {"error": "No API key", "agent_id": agent_id}

            client = genai.Client(api_key=api_key)

            # Get agent description
            agent_desc = self._get_agent_description(agent_id)

            prompt = f"""You are {agent_id}, a specialized agent.

{agent_desc}

## Task
Analyze the following query and provide your perspective:

**Query:** {query}

**Context from other agents:**
{context if context else "(None yet)"}

Provide a concise, actionable response (2-4 paragraphs max)."""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )

            return {"response": response.text, "agent_id": agent_id}

        except Exception as e:
            return {"error": str(e), "agent_id": agent_id}

    def _get_agent_description(self, agent_id: str) -> str:
        """Get description for an agent — reads from unified registry first, falls back to hardcoded."""
        # Try unified registry
        try:
            from .unified_registry import get_agent_role_description
            desc = get_agent_role_description(agent_id)
            if desc and desc != f"Expert agent: {agent_id}":
                return desc
        except Exception:
            pass

        # Fallback descriptions
        descriptions = {
            "tta": "Trending to the Absurd - explore extreme future scenarios and emerging trends",
            "jtbd": "Jobs to Be Done - identify customer jobs and unmet needs",
            "redteam": "Red Team - challenge assumptions and find weaknesses",
            "ackoff": "Ackoff's Pyramid - apply DIKW hierarchy (Data, Information, Knowledge, Wisdom)",
            "research": "Research Agent - gather external data and evidence",
            "validation": "Validation Agent - verify claims and assess credibility",
            "scurve": "S-Curve Analysis - assess technology maturity and timing",
            "knowns": "Known-Unknowns - map certainty landscape",
            "larry": "Lawrence - synthesize insights and provide strategic guidance",
        }
        return descriptions.get(agent_id, f"Expert agent: {agent_id}")

    def _build_context_from_stages(self) -> str:
        """Build context string from completed stages."""
        context_parts = []

        for stage_result in self.state.stage_results:
            for agent_id, output in stage_result.outputs.items():
                if isinstance(output, dict) and "response" in output:
                    context_parts.append(f"**{agent_id.upper()} ({stage_result.task}):**\n{output['response']}")

        return "\n\n---\n\n".join(context_parts)

    async def _synthesize(self, query: str, workflow: WorkflowRecipe):
        """Synthesize results from all stages."""
        try:
            from google import genai
            from google.genai import types

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                self.state.synthesis = {"error": "No API key for synthesis"}
                return

            client = genai.Client(api_key=api_key)

            # Gather all agent outputs
            all_outputs = []
            for stage_result in self.state.stage_results:
                for agent_id, output in stage_result.outputs.items():
                    if isinstance(output, dict) and "response" in output:
                        all_outputs.append({
                            "agent": agent_id,
                            "task": stage_result.task,
                            "response": output["response"]
                        })

            if not all_outputs:
                self.state.synthesis = {"error": "No outputs to synthesize"}
                return

            # Build synthesis prompt
            outputs_text = "\n\n".join([
                f"**{o['agent'].upper()} ({o['task']}):**\n{o['response']}"
                for o in all_outputs
            ])

            synthesis_prompt = f"""You are synthesizing insights from multiple expert agents.

## Original Query
{query}

## Agent Insights
{outputs_text}

## Your Task
Create a unified synthesis that:
1. **Key Finding** - The most important insight (1-2 sentences)
2. **Supporting Points** - 3-5 bullet points of key supporting evidence
3. **Risks & Challenges** - What could go wrong
4. **Recommended Action** - What should the user do next
5. **Confidence Level** - How confident are you (Low/Medium/High) and why

Be concise but actionable. Focus on synthesis, not repetition."""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=synthesis_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=1500
                )
            )

            self.state.synthesis = {
                "content": response.text,
                "workflow": workflow["name"],
                "agents_used": list(set(a for sr in self.state.stage_results for a in sr.agents)),
                "total_duration_ms": sum(sr.duration_ms for sr in self.state.stage_results),
            }

            # Estimate confidence from outputs
            error_count = sum(
                1 for sr in self.state.stage_results
                for o in sr.outputs.values()
                if isinstance(o, dict) and "error" in o
            )
            total_outputs = sum(len(sr.outputs) for sr in self.state.stage_results)
            self.state.confidence = 1.0 - (error_count / max(total_outputs, 1))

        except Exception as e:
            self.state.synthesis = {"error": str(e)}

    def pause(self):
        """Pause orchestration."""
        self._pause_event.set()
        if self.state:
            self.state.status = OrchestratorStatus.PAUSED.value
            self.state.paused_at = datetime.utcnow().isoformat() + "Z"

    def resume(self):
        """Resume orchestration."""
        self._pause_event.clear()
        if self.state:
            self.state.status = OrchestratorStatus.RUNNING.value
            self.state.paused_at = None

    def cancel(self):
        """Cancel orchestration."""
        self._cancel_event.set()
        if self.state:
            self.state.cancel_requested = True


async def run_orchestration(
    query: str,
    session_id: str,
    progress_callback: Optional[Callable] = None,
    workflow_override: Optional[str] = None,
    history: Optional[List[Dict]] = None,
) -> OrchestratorState:
    """
    Convenience function to run orchestration.

    Args:
        query: User's question
        session_id: Session identifier
        progress_callback: Optional progress callback
        workflow_override: Force specific workflow
        history: Conversation history

    Returns:
        Final orchestrator state
    """
    orchestrator = AutoOrchestrator(
        session_id=session_id,
        progress_callback=progress_callback,
    )
    return await orchestrator.run(query, workflow_override, history)
