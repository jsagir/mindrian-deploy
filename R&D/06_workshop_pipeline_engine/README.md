# Workshop Pipeline Engine - Formalized Phase Progression

## What Is This?

A structured pipeline engine that enforces proper workshop phase progression, ensuring users complete each phase before moving forward, with clear entry/exit criteria.

## Why Implement This?

### Current Problem
- Phases are loosely tracked (just status updates)
- Users can skip phases or jump around
- No validation that phase objectives are met
- No structured data capture per phase

### Solution: Pipeline Engine
Formalize workshops as state machines with:
- Entry conditions (prerequisites)
- Required activities (must complete)
- Exit criteria (validation)
- Data capture (structured outputs)

## Pipeline Design

### Core Concepts

```python
@dataclass
class PipelinePhase:
    id: str
    name: str
    description: str
    entry_criteria: List[Criterion]      # What's needed to enter
    required_activities: List[Activity]   # What must happen
    exit_criteria: List[Criterion]        # What validates completion
    outputs: List[OutputSchema]           # Structured data to capture

@dataclass
class Criterion:
    type: str  # "conversation", "data", "user_action"
    condition: str
    validator: Callable[[Context], bool]

@dataclass
class Activity:
    name: str
    prompt_template: str
    required: bool
    min_exchanges: int  # Minimum back-and-forth
```

### Example: Ackoff DIKW Pipeline

```python
ACKOFF_PIPELINE = Pipeline(
    id="ackoff",
    name="Ackoff's DIKW Pyramid",
    phases=[
        PipelinePhase(
            id="onboarding",
            name="Team Onboarding",
            entry_criteria=[],  # First phase, no prerequisites
            required_activities=[
                Activity(
                    name="introduce_problem",
                    prompt_template="What problem or solution are you exploring?",
                    min_exchanges=2
                )
            ],
            exit_criteria=[
                Criterion(
                    type="data",
                    condition="problem_statement_captured",
                    validator=lambda ctx: len(ctx.get("problem_statement", "")) > 50
                )
            ],
            outputs=[
                OutputSchema(
                    name="problem_statement",
                    type="text",
                    required=True
                )
            ]
        ),
        PipelinePhase(
            id="direction_choice",
            name="Direction Choice",
            entry_criteria=[
                Criterion(
                    type="data",
                    condition="has_problem_statement",
                    validator=lambda ctx: "problem_statement" in ctx
                )
            ],
            required_activities=[
                Activity(
                    name="choose_direction",
                    prompt_template="Are you climbing UP (exploring) or DOWN (validating)?",
                    min_exchanges=1
                )
            ],
            exit_criteria=[
                Criterion(
                    type="data",
                    condition="direction_chosen",
                    validator=lambda ctx: ctx.get("direction") in ["up", "down"]
                )
            ],
            outputs=[
                OutputSchema(name="direction", type="enum", values=["up", "down"])
            ]
        ),
        # ... more phases
    ]
)
```

## Pipeline Engine

```python
class WorkshopPipelineEngine:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.current_phase_idx = 0
        self.context = {}
        self.phase_data = {}

    async def process_message(self, message: str) -> PipelineResponse:
        phase = self.current_phase

        # Check if we can advance
        if self._check_exit_criteria(phase):
            self.current_phase_idx += 1
            return PipelineResponse(
                type="phase_complete",
                message=f"Phase '{phase.name}' complete! Moving to '{self.current_phase.name}'",
                next_prompt=self.current_phase.required_activities[0].prompt_template
            )

        # Process within current phase
        return await self._process_in_phase(message, phase)

    def _check_exit_criteria(self, phase: PipelinePhase) -> bool:
        return all(
            criterion.validator(self.context)
            for criterion in phase.exit_criteria
        )

    def get_progress(self) -> dict:
        return {
            "current_phase": self.current_phase.name,
            "phase_number": self.current_phase_idx + 1,
            "total_phases": len(self.pipeline.phases),
            "completion_percentage": (self.current_phase_idx / len(self.pipeline.phases)) * 100,
            "captured_data": list(self.context.keys())
        }
```

## Benefits

1. **Guided Experience**: Users can't skip important steps
2. **Structured Outputs**: Each phase captures specific data
3. **Progress Tracking**: Clear visibility into workshop state
4. **Quality Assurance**: Validation ensures completeness
5. **Export Ready**: Captured data ready for reports

## UI Integration

### Phase Indicator
```python
async def show_phase_progress(engine: WorkshopPipelineEngine):
    progress = engine.get_progress()

    # Visual progress bar
    phases_display = ""
    for i, phase in enumerate(engine.pipeline.phases):
        if i < engine.current_phase_idx:
            status = "✅"
        elif i == engine.current_phase_idx:
            status = "🔄"
        else:
            status = "⏳"
        phases_display += f"{status} {phase.name}\n"

    await cl.Message(
        content=f"**Workshop Progress ({progress['completion_percentage']:.0f}%)**\n\n{phases_display}"
    ).send()
```

### Phase Lock Warning
```python
if user_tries_to_skip_phase:
    await cl.Message(
        content=f"""**Cannot skip ahead** 🛑

        You need to complete **{current_phase.name}** first.

        **What's needed:**
        {format_exit_criteria(current_phase.exit_criteria)}
        """
    ).send()
```

## Files to Create

| File | Purpose |
|------|---------|
| `utils/pipeline_engine.py` | Core pipeline engine |
| `pipelines/ackoff.py` | Ackoff DIKW pipeline definition |
| `pipelines/tta.py` | TTA pipeline definition |
| `pipelines/jtbd.py` | JTBD pipeline definition |
| `pipelines/scurve.py` | S-Curve pipeline definition |
| `pipelines/redteam.py` | Red Team pipeline definition |

## Estimated Effort

- Engine design: 4-6 hours
- Engine implementation: 12-16 hours
- Pipeline definitions: 8-12 hours (all workshops)
- UI integration: 6-8 hours

## Status

- [x] Research complete
- [ ] Engine architecture design
- [ ] Core engine implementation
- [ ] Ackoff pipeline definition
- [ ] Other workshop pipelines
- [ ] UI integration
