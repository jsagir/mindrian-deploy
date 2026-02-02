# Mindrian Architecture Evolution: Triple-Mode Entry Points

## Technical Specification for Development Team

**Document Version:** 1.0  
**Date:** February 2, 2026  
**Reviewed by:** PM Larry (PWS Methodology Expert)  
**Status:** Approved for Implementation

---

## Executive Summary

### What We Proposed (Dual-Mode)
The original proposal suggested adding Workshop/Sandbox toggle to each bot, making 14 bots × 2 modes = 28 configurations.

### What We're Building Instead (Triple-Mode Entry Points)
After methodology review, we're implementing a **user-journey-driven architecture** with three entry points that match how students actually work:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MINDRIAN TRIPLE-MODE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🧠 BRAINSTORMING           📄 DOCUMENT REVIEW          🚀 BUILD VENTURE   │
│  ───────────────            ────────────────           ────────────────    │
│  "Find problems"            "Validate thinking"        "Execute"           │
│  Sandbox-primary            Workshop-primary           Stage-adaptive      │
│  T3-heavy (examples)        T2-heavy (rubrics)        Stage-based tiers   │
│                                                                             │
│                    ↓ All feed into ↓                                       │
│                                                                             │
│               📤 DOCUMENT CREATION (Universal Output)                       │
│               ─────────────────────────────────────                        │
│               Individual work → Team handoff                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Change?

**Key Observation from PWS Methodology Review:**
> *"Students do not work collaboratively in Mindrian. They have individual conversations and get help and then they get together with their team."*

The dual-mode proposal was **technology-driven** (organizing around RAG tiers). The triple-mode architecture is **user-journey-driven** (organizing around what users actually need).

### Key Benefits Over Original Proposal

| Aspect | Dual-Mode (Original) | Triple-Mode (New) |
|--------|---------------------|-------------------|
| Mental model | 14 bots × 2 modes | 3 entry points → relevant agents |
| User question | "Which bot? Which mode?" | "Where am I in my journey?" |
| Navigation | Bot selection then mode toggle | Entry point selection, agents suggested |
| Document handoff | Afterthought | Core feature (team workflow) |
| PWS alignment | Modes as constraint toggle | Entry points as journey stages |

---

## Part 1: Architecture Overview

### 1.1 Entry Point → Agent → Mode Flow

```
USER ARRIVES
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    ENTRY POINT ROUTER                        │
│  Conversational discovery OR explicit selection              │
└─────────────────────────────────────────────────────────────┘
    │
    ├─── 🧠 BRAINSTORMING ────────────────────────────────────┐
    │         │                                                │
    │         ├── TTA (Trending to Absurd)                    │
    │         ├── Domain Explorer                              │
    │         ├── Beautiful Question                           │
    │         ├── Scenario Planning                            │
    │         ├── Known-Unknowns                               │
    │         └── Red Team (challenge assumptions)             │
    │                                                          │
    │         Default Mode: SANDBOX                            │
    │         Tier Weights: T1=0.35, T2=0.25, T3=0.40         │
    │                                                          │
    ├─── 📄 DOCUMENT REVIEW ──────────────────────────────────┤
    │         │                                                │
    │         ├── PWS Grading                                  │
    │         ├── Red Team (adversarial critique)              │
    │         ├── Devil's Advocate                             │
    │         ├── PWS Investment Analysis                      │
    │         └── Multi-Perspective Validation                 │
    │                                                          │
    │         Default Mode: WORKSHOP                           │
    │         Tier Weights: T1=0.20, T2=0.50, T3=0.30         │
    │                                                          │
    └─── 🚀 BUILD VENTURE ────────────────────────────────────┤
              │                                                │
              │  REQUIRES STAGE ASSESSMENT                     │
              │                                                │
              ├── Pre-opportunity → Route to BRAINSTORMING     │
              │                                                │
              ├── Opportunity Identified:                      │
              │   ├── JTBD                                     │
              │   ├── Ackoff's Pyramid                         │
              │   └── Problem Validation                       │
              │                                                │
              ├── Well-Defined Problem:                        │
              │   ├── Business Model Canvas                    │
              │   ├── S-Curve Analysis                         │
              │   └── BONO Master                              │
              │                                                │
              └── Ready to Build:                              │
                  ├── Investment Analysis                      │
                  └── Execution Planning                       │
                                                               │
              Default Mode: ADAPTIVE (stage-based)             │
              Tier Weights: Varies by stage                    │
───────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│              📤 DOCUMENT CREATION (Universal)                │
│  Available from any entry point via:                         │
│  • User request ("package this")                            │
│  • Milestone trigger (phase complete, opportunity banked)   │
│  • Validation gate ("Is it Real?" checkpoint)               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 The Larry Identity (Consistent Across All Entry Points)

Every interaction must embody the "Larry vibe" — this is non-negotiable.

```python
# prompts/larry_core.py

LARRY_CORE_IDENTITY = """
You are Larry — a rigorous, provocative thinking partner for innovation.

## CORE BEHAVIORS (Non-Negotiable)

1. **Problem-First**: Never accept solutions without questioning the problem
   - BAD: "Great idea! Let me help you with the business model..."
   - GOOD: "Hold on. What problem are you actually solving?"

2. **Provocative**: Ask questions that OPEN thinking, not close it
   - BAD: "Here are 5 trends you should consider..."
   - GOOD: "What's been bugging you lately? Where do you see things that don't work?"

3. **Grounded**: Every claim backed by evidence or PWS methodology
   - BAD: "The market is probably large enough."
   - GOOD: "What's your TAM/SAM/SOM? Who specifically are your first 10 customers?"

4. **Direct**: Say what's wrong clearly but constructively
   - BAD: "That's interesting, though there might be some concerns..."
   - GOOD: "Let me push back on that. What evidence do you have?"

5. **Structured Freedom**: Explore widely WITHIN discipline
   - BAD: Random brainstorming OR rigid phase enforcement
   - GOOD: "Let's explore that — but before we go far, can you articulate the problem?"

## CONVERSATIONAL FORMULA

Every response should follow this implicit structure:
1. ACKNOWLEDGE — Show you heard them
2. CHALLENGE  — Question the assumption/framing
3. GROUND     — Connect to evidence or methodology
4. OPEN       — Ask a question that advances thinking

## SIGNATURE PHRASES

Opening:
- "What are you curious about?"
- "What's been bugging you lately?"
- "What problem are you circling?"

Challenging:
- "That's a solution. What's the problem?"
- "Let me push back on that..."
- "What evidence do you have for that?"
- "Who specifically has this problem?"

Grounding:
- "Let's validate that assumption."
- "Before we go further..."
- "The methodology suggests..."

Synthesis:
- "What patterns are you seeing?"
- "If you had to bet on one opportunity, which would it be?"
- "Complete this: '[WHO] struggles with [PROBLEM] because...'"

## NEVER DO

- Accept "the market is huge" without numbers
- Skip problem validation to discuss solutions
- Give vague, hedge-filled feedback
- Lecture when you should question
- Abandon methodology for user comfort
- Use more than one question per turn (usually)
"""
```

---

## Part 2: File-by-File Implementation Specification

### 2.1 New Files to Create

```
mindrian-deploy/
├── protocols/
│   ├── entry_point_router.py      # NEW - Entry point detection and routing
│   ├── mode_manager.py            # NEW - Workshop/Sandbox mode state
│   ├── stage_assessor.py          # NEW - Build Venture stage assessment
│   └── document_generator.py      # NEW - Universal document creation
├── prompts/
│   ├── larry_core.py              # NEW - Shared Larry identity
│   ├── entry_brainstorming.py     # NEW - Brainstorming entry context
│   ├── entry_document_review.py   # NEW - Document Review entry context
│   ├── entry_build_venture.py     # NEW - Build Venture entry context
│   └── grounding_prompts.py       # NEW - Periodic grounding interventions
├── ui/
│   ├── entry_point_selector.py    # NEW - Welcome flow UI
│   ├── mode_toggle.py             # NEW - Workshop/Sandbox toggle
│   ├── stage_progress.py          # NEW - Build Venture stage tracker
│   └── document_export.py         # NEW - Export UI components
└── state/
    └── conversation_state.py      # NEW - Unified state machine
```

### 2.2 Files to Modify

```
mindrian-deploy/
├── mindrian_chat.py               # MODIFY - Entry point routing, state management
├── tools/
│   └── graphrag_lite.py           # MODIFY - Mode-aware tier weighting
├── protocols/
│   ├── a2a_protocol.py            # MODIFY - Entry point + mode in handoffs
│   ├── context_journal.py         # MODIFY - Entry point sections
│   ├── smart_phase_tracker.py     # MODIFY - Depth tracking for sandbox
│   └── opportunity_bank.py        # MODIFY - Entry point + mode tagging
├── prompts/
│   └── [all bot prompts]          # MODIFY - Inject entry point context
└── utils/
    └── session_manager.py         # MODIFY - Entry point state persistence
```

---

## Part 3: Core Implementation Details

### 3.1 Entry Point Router

```python
# protocols/entry_point_router.py

import re
from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass

class EntryPoint(Enum):
    BRAINSTORMING = "brainstorming"
    DOCUMENT_REVIEW = "document_review"
    BUILD_VENTURE = "build_venture"
    AMBIGUOUS = "ambiguous"

@dataclass
class RoutingResult:
    entry_point: EntryPoint
    confidence: float
    suggested_agent: Optional[str]
    clarification_needed: bool
    clarification_prompt: Optional[str]

class EntryPointRouter:
    """
    Route users to appropriate entry point based on intent detection.
    
    Design Principle: Conversational discovery, not forced menu selection.
    """
    
    INTENT_PATTERNS = {
        EntryPoint.BRAINSTORMING: {
            "patterns": [
                r"explore", r"discover", r"what if", r"trends", r"opportunities",
                r"no idea", r"curious about", r"interesting", r"future of",
                r"brainstorm", r"generate ideas", r"looking for problems",
                r"what.*(work on|should I|could I)", r"where.*(start|begin|look)"
            ],
            "weight": 1.0
        },
        EntryPoint.DOCUMENT_REVIEW: {
            "patterns": [
                r"review", r"feedback", r"grade", r"evaluate", r"look at",
                r"critique", r"poke holes", r"what's wrong", r"improve",
                r"pitch deck", r"business plan", r"is this good", r"check my",
                r"uploaded", r"attached", r"here's my", r"read this"
            ],
            "weight": 1.0
        },
        EntryPoint.BUILD_VENTURE: {
            "patterns": [
                r"build", r"create", r"start", r"execute", r"implement",
                r"next steps", r"stuck on", r"how do I", r"business model",
                r"already have a company", r"startup", r"venture", r"launch",
                r"ready to", r"validated", r"know the problem"
            ],
            "weight": 1.0
        }
    }
    
    AGENT_SUGGESTIONS = {
        EntryPoint.BRAINSTORMING: {
            "trends|future|what if|extrapolat": "tta",
            "domain|where.*look|industry": "domain_explorer",
            "question|reframe|ask": "beautiful_question",
            "scenario|possible|futures": "scenario_analysis",
            "don't know|unknown|blind spot": "known_unknowns",
            "challenge|stress.?test|assumption": "red_team"
        },
        EntryPoint.DOCUMENT_REVIEW: {
            "grade|score|rubric": "pws_grading",
            "poke holes|attack|challenge": "red_team",
            "bias|assumption|flaw": "devil_advocate",
            "invest|fund|pitch": "pws_investment",
            "perspective|stakeholder|viewpoint": "multi_perspective"
        },
        EntryPoint.BUILD_VENTURE: {
            "job|customer|hire": "jtbd",
            "pyramid|data|wisdom": "ackoff",
            "model|canvas|revenue": "bmc",
            "timing|curve|adoption": "s_curve",
            "hat|perspective|comprehensive": "bono"
        }
    }
    
    def route(self, user_message: str, has_attachment: bool = False) -> RoutingResult:
        """Determine entry point from user message."""
        
        message_lower = user_message.lower()
        
        # Attachment strongly suggests Document Review
        if has_attachment:
            return RoutingResult(
                entry_point=EntryPoint.DOCUMENT_REVIEW,
                confidence=0.9,
                suggested_agent=self._suggest_agent(EntryPoint.DOCUMENT_REVIEW, message_lower),
                clarification_needed=False,
                clarification_prompt=None
            )
        
        # Score each entry point
        scores = {}
        for entry_point, config in self.INTENT_PATTERNS.items():
            score = 0
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower):
                    score += config["weight"]
            scores[entry_point] = score
        
        # Find best match
        best_entry = max(scores, key=scores.get)
        best_score = scores[best_entry]
        
        # Check confidence
        if best_score == 0:
            return RoutingResult(
                entry_point=EntryPoint.AMBIGUOUS,
                confidence=0.0,
                suggested_agent=None,
                clarification_needed=True,
                clarification_prompt=self._get_clarification_prompt()
            )
        
        # Check if clear winner (score gap > 1)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) < 1:
            # Close call - still route but note lower confidence
            confidence = 0.6
        else:
            confidence = min(0.95, 0.5 + (best_score * 0.15))
        
        return RoutingResult(
            entry_point=best_entry,
            confidence=confidence,
            suggested_agent=self._suggest_agent(best_entry, message_lower),
            clarification_needed=False,
            clarification_prompt=None
        )
    
    def _suggest_agent(self, entry_point: EntryPoint, message: str) -> Optional[str]:
        """Suggest specific agent based on message content."""
        
        if entry_point not in self.AGENT_SUGGESTIONS:
            return None
        
        for pattern, agent in self.AGENT_SUGGESTIONS[entry_point].items():
            if re.search(pattern, message):
                return agent
        
        # Default agents per entry point
        defaults = {
            EntryPoint.BRAINSTORMING: "tta",
            EntryPoint.DOCUMENT_REVIEW: "red_team",
            EntryPoint.BUILD_VENTURE: "jtbd"
        }
        return defaults.get(entry_point)
    
    def _get_clarification_prompt(self) -> str:
        """Generate clarification prompt when intent is ambiguous."""
        return """
I want to help you effectively. Tell me where you are:

🧠 **EXPLORE** — "I'm looking for problems worth solving"
   → I'll help you discover opportunities

📄 **VALIDATE** — "I have something, need feedback"
   → I'll critique and improve your thinking

🚀 **BUILD** — "I'm ready to execute"
   → I'll help you build your venture

Which fits best? Or just tell me what's on your mind.
"""
```

### 3.2 Conversation State Machine

```python
# state/conversation_state.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Mode(Enum):
    WORKSHOP = "workshop"
    SANDBOX = "sandbox"
    ADAPTIVE = "adaptive"

class ResearchDepth(Enum):
    INITIAL = "initial"
    EXPLORING = "exploring"
    DEEP = "deep"
    SYNTHESIS = "synthesis"

class VentureStage(Enum):
    PRE_OPPORTUNITY = "pre_opportunity"
    OPPORTUNITY_IDENTIFIED = "opportunity_identified"
    WELL_DEFINED_PROBLEM = "well_defined_problem"
    READY_TO_BUILD = "ready_to_build"

@dataclass
class GroundingState:
    """Track PWS grounding indicators."""
    problem_articulated: bool = False
    who_identified: bool = False
    evidence_provided: bool = False
    consequences_considered: bool = False
    synthesis_attempted: bool = False
    
    def grounding_score(self) -> float:
        """Calculate grounding completeness (0-1)."""
        checks = [
            self.problem_articulated,
            self.who_identified,
            self.evidence_provided,
            self.consequences_considered
        ]
        return sum(checks) / len(checks)

@dataclass
class ConversationState:
    """
    Unified state machine for Mindrian conversations.
    
    Tracks:
    - Entry point and mode
    - Workshop phase OR sandbox depth
    - PWS grounding indicators
    - Opportunities banked
    - Documents created
    """
    
    # Session identity
    session_id: str
    user_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    
    # Entry point state
    entry_point: str = "brainstorming"  # brainstorming | document_review | build_venture
    current_agent: Optional[str] = None
    
    # Mode state
    mode: Mode = Mode.SANDBOX
    
    # Workshop state (when mode == WORKSHOP)
    current_phase: int = 0
    phase_completion: Dict[int, float] = field(default_factory=dict)
    phase_evidence: Dict[int, List[str]] = field(default_factory=dict)
    
    # Sandbox state (when mode == SANDBOX)
    research_depth: ResearchDepth = ResearchDepth.INITIAL
    topics_explored: List[str] = field(default_factory=list)
    sources_consulted: int = 0
    
    # Build Venture state
    venture_stage: VentureStage = VentureStage.PRE_OPPORTUNITY
    stage_assessment_complete: bool = False
    
    # Grounding state (tracks PWS discipline)
    grounding: GroundingState = field(default_factory=GroundingState)
    
    # Turn tracking
    turn_count: int = 0
    turns_since_grounding: int = 0
    
    # Outputs
    opportunities_banked: List[str] = field(default_factory=list)
    documents_created: List[str] = field(default_factory=list)
    
    # Mode history (for cross-mode context)
    mode_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_turn(self, user_message: str, assistant_response: str):
        """Update state after each conversation turn."""
        self.turn_count += 1
        self.turns_since_grounding += 1
        
        # Detect grounding signals in user message
        self._detect_grounding_signals(user_message)
        
        # Update research depth in sandbox
        if self.mode == Mode.SANDBOX:
            self._update_research_depth()
    
    def _detect_grounding_signals(self, message: str):
        """Detect PWS grounding indicators in user message."""
        message_lower = message.lower()
        
        # Problem articulation patterns
        problem_patterns = [
            r"the problem is", r"problem.*solving", r"struggling with",
            r"pain point", r"challenge is", r"issue is"
        ]
        if any(re.search(p, message_lower) for p in problem_patterns):
            self.grounding.problem_articulated = True
        
        # Who identification patterns
        who_patterns = [
            r"(customers?|users?|people) (who|that)", r"target (market|audience)",
            r"(they|these people) (need|want|struggle)"
        ]
        if any(re.search(p, message_lower) for p in who_patterns):
            self.grounding.who_identified = True
        
        # Evidence patterns
        evidence_patterns = [
            r"\d+%", r"research shows", r"data (shows|indicates)",
            r"interviewed", r"spoke (to|with)", r"evidence"
        ]
        if any(re.search(p, message_lower) for p in evidence_patterns):
            self.grounding.evidence_provided = True
    
    def _update_research_depth(self):
        """Update research depth based on conversation progress."""
        if self.sources_consulted >= 7 and len(self.topics_explored) >= 3:
            self.research_depth = ResearchDepth.DEEP
        elif self.sources_consulted >= 3 or len(self.topics_explored) >= 2:
            self.research_depth = ResearchDepth.EXPLORING
        
        # Synthesis trigger
        if (self.research_depth == ResearchDepth.DEEP and 
            self.grounding.grounding_score() >= 0.5):
            self.research_depth = ResearchDepth.SYNTHESIS
    
    def should_ground(self) -> Tuple[bool, Optional[str]]:
        """Determine if grounding intervention is needed."""
        
        # Entry-point specific grounding rules
        if self.entry_point == "brainstorming":
            if self.turns_since_grounding >= 5 and not self.grounding.problem_articulated:
                return True, "PATTERN_CHECK"
            if self.turns_since_grounding >= 10 and not self.grounding.synthesis_attempted:
                return True, "SYNTHESIS_PROMPT"
            if self.turn_count >= 15 and len(self.opportunities_banked) == 0:
                return True, "OPPORTUNITY_REQUIRED"
        
        elif self.entry_point == "build_venture":
            if not self.stage_assessment_complete:
                return True, "STAGE_ASSESSMENT_REQUIRED"
            if not self.grounding.problem_articulated:
                return True, "PROBLEM_VALIDATION_REQUIRED"
        
        return False, None
    
    def switch_mode(self, new_mode: Mode) -> Dict[str, Any]:
        """Switch modes while preserving context."""
        
        # Save current mode state
        preserved = {
            "mode": self.mode.value,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.mode == Mode.WORKSHOP:
            preserved.update({
                "current_phase": self.current_phase,
                "phase_completion": self.phase_completion.copy(),
                "phase_evidence": {k: v.copy() for k, v in self.phase_evidence.items()}
            })
        else:  # SANDBOX
            preserved.update({
                "research_depth": self.research_depth.value,
                "topics_explored": self.topics_explored.copy(),
                "sources_consulted": self.sources_consulted
            })
        
        self.mode_history.append(preserved)
        
        # Switch to new mode
        self.mode = new_mode
        
        # Generate context injection for new mode
        return self._generate_mode_switch_context(preserved, new_mode)
    
    def _generate_mode_switch_context(self, preserved: Dict, new_mode: Mode) -> Dict[str, Any]:
        """Generate context injection when switching modes."""
        
        if new_mode == Mode.WORKSHOP:
            # Sandbox → Workshop
            return {
                "injection": f"""
Your sandbox exploration covered:
- Topics: {', '.join(preserved.get('topics_explored', []))}
- Sources consulted: {preserved.get('sources_consulted', 0)}
- Opportunities banked: {len(self.opportunities_banked)}

Now entering workshop mode. Your research is available as evidence.
""",
                "restore_phase": preserved.get("current_phase", 0) if "current_phase" in preserved else 0
            }
        
        else:  # Workshop → Sandbox
            completed_phases = [k for k, v in preserved.get("phase_completion", {}).items() if v >= 0.7]
            return {
                "injection": f"""
Workshop progress saved:
- Completed phases: {len(completed_phases)}
- Current phase: {preserved.get('current_phase', 0)}
- Key evidence gathered: {sum(len(v) for v in preserved.get('phase_evidence', {}).values())} items

You can explore freely. Your workshop progress is preserved.
""",
                "restore_depth": preserved.get("research_depth", "initial") if "research_depth" in preserved else "initial"
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for persistence."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "entry_point": self.entry_point,
            "current_agent": self.current_agent,
            "mode": self.mode.value,
            "current_phase": self.current_phase,
            "phase_completion": self.phase_completion,
            "research_depth": self.research_depth.value,
            "topics_explored": self.topics_explored,
            "sources_consulted": self.sources_consulted,
            "venture_stage": self.venture_stage.value,
            "grounding": {
                "problem_articulated": self.grounding.problem_articulated,
                "who_identified": self.grounding.who_identified,
                "evidence_provided": self.grounding.evidence_provided,
                "consequences_considered": self.grounding.consequences_considered,
                "synthesis_attempted": self.grounding.synthesis_attempted
            },
            "turn_count": self.turn_count,
            "opportunities_banked": self.opportunities_banked,
            "documents_created": self.documents_created,
            "mode_history": self.mode_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Deserialize state from persistence."""
        state = cls(session_id=data["session_id"])
        state.user_id = data.get("user_id")
        state.entry_point = data.get("entry_point", "brainstorming")
        state.current_agent = data.get("current_agent")
        state.mode = Mode(data.get("mode", "sandbox"))
        state.current_phase = data.get("current_phase", 0)
        state.phase_completion = data.get("phase_completion", {})
        state.research_depth = ResearchDepth(data.get("research_depth", "initial"))
        state.topics_explored = data.get("topics_explored", [])
        state.sources_consulted = data.get("sources_consulted", 0)
        state.venture_stage = VentureStage(data.get("venture_stage", "pre_opportunity"))
        
        grounding_data = data.get("grounding", {})
        state.grounding = GroundingState(
            problem_articulated=grounding_data.get("problem_articulated", False),
            who_identified=grounding_data.get("who_identified", False),
            evidence_provided=grounding_data.get("evidence_provided", False),
            consequences_considered=grounding_data.get("consequences_considered", False),
            synthesis_attempted=grounding_data.get("synthesis_attempted", False)
        )
        
        state.turn_count = data.get("turn_count", 0)
        state.opportunities_banked = data.get("opportunities_banked", [])
        state.documents_created = data.get("documents_created", [])
        state.mode_history = data.get("mode_history", [])
        
        return state
```

### 3.3 Mode-Aware GraphRAG

```python
# tools/graphrag_lite.py - MODIFICATIONS

# Add these imports
from state.conversation_state import Mode, ResearchDepth

# Add tier weight configurations
TIER_WEIGHTS = {
    # Entry point defaults
    "brainstorming": {"t1": 0.35, "t2": 0.25, "t3": 0.40},
    "document_review": {"t1": 0.20, "t2": 0.50, "t3": 0.30},
    "build_venture": {"t1": 0.30, "t2": 0.40, "t3": 0.30},
    
    # Workshop phase weights
    "workshop_early": {"t1": 0.60, "t2": 0.30, "t3": 0.10},
    "workshop_core": {"t1": 0.20, "t2": 0.60, "t3": 0.20},
    "workshop_late": {"t1": 0.10, "t2": 0.30, "t3": 0.60},
    
    # Sandbox (equal access)
    "sandbox": {"t1": 0.33, "t2": 0.33, "t3": 0.34},
    
    # Sandbox with intent detection
    "sandbox_conceptual": {"t1": 0.50, "t2": 0.30, "t3": 0.20},
    "sandbox_applied": {"t1": 0.20, "t2": 0.30, "t3": 0.50},
    "sandbox_practice": {"t1": 0.20, "t2": 0.60, "t3": 0.20},
}

# Phase category mapping
PHASE_CATEGORIES = {
    "intro": "workshop_early",
    "welcome": "workshop_early",
    "overview": "workshop_early",
    "setup": "workshop_early",
    "discover": "workshop_core",
    "identify": "workshop_core",
    "research": "workshop_core",
    "analys": "workshop_core",
    "extrapolat": "workshop_core",
    "explor": "workshop_core",
    "valid": "workshop_late",
    "test": "workshop_late",
    "verify": "workshop_late",
    "synthe": "workshop_late",
    "reflect": "workshop_late",
    "action": "workshop_late",
}

def get_tier_weights(
    entry_point: str,
    mode: Mode,
    current_phase: int = None,
    phase_name: str = None,
    query: str = None
) -> dict:
    """
    Determine tier weights based on entry point, mode, and context.
    
    Workshop Mode: Phase determines weights
    Sandbox Mode: Equal weights with optional intent detection
    """
    
    if mode == Mode.WORKSHOP and phase_name:
        # Classify phase into category
        phase_lower = phase_name.lower()
        for keyword, category in PHASE_CATEGORIES.items():
            if keyword in phase_lower:
                return TIER_WEIGHTS[category]
        return TIER_WEIGHTS["workshop_core"]  # Default
    
    elif mode == Mode.SANDBOX:
        # Optional: Detect query intent for smarter weighting
        if query:
            query_lower = query.lower()
            if any(w in query_lower for w in ["what is", "explain", "define", "theory"]):
                return TIER_WEIGHTS["sandbox_conceptual"]
            elif any(w in query_lower for w in ["example", "case", "how do", "real world"]):
                return TIER_WEIGHTS["sandbox_applied"]
            elif any(w in query_lower for w in ["exercise", "practice", "try", "help me"]):
                return TIER_WEIGHTS["sandbox_practice"]
        return TIER_WEIGHTS["sandbox"]
    
    else:
        # Fall back to entry point default
        return TIER_WEIGHTS.get(entry_point, TIER_WEIGHTS["sandbox"])


def enrich_for_bot(
    message: str,
    turn_count: int,
    bot_id: str,
    entry_point: str = "brainstorming",
    mode: Mode = Mode.SANDBOX,
    current_phase: int = None,
    phase_name: str = None,
    research_depth: ResearchDepth = None
) -> Optional[str]:
    """
    Mode-aware context enrichment.
    
    Workshop Mode: Phase-gated tier access, focused retrieval
    Sandbox Mode: Open tier access, broad retrieval
    """
    
    # Get appropriate tier weights
    weights = get_tier_weights(entry_point, mode, current_phase, phase_name, message)
    
    # Build query based on mode
    if mode == Mode.WORKSHOP and phase_name:
        # Scope query to phase context
        scoped_query = f"In {phase_name} of {bot_id} workshop: {message}"
        max_results = 3  # Focused
    else:
        # Expand query for breadth
        scoped_query = f"{message} frameworks applications examples"
        max_results = 7  # Broad
    
    # Retrieve with tier weighting
    results = tiered_retrieve(
        query=scoped_query,
        weights=weights,
        max_results=max_results
    )
    
    if not results:
        return None
    
    # Format based on mode
    if mode == Mode.WORKSHOP:
        return format_workshop_hint(results, phase_name, bot_id)
    else:
        return format_sandbox_context(results, research_depth)


def tiered_retrieve(query: str, weights: dict, max_results: int) -> List[dict]:
    """
    Retrieve from knowledge base with tier weighting.
    
    Weights determine how many results to pull from each tier:
    - t1 (Frameworks): Core methodology definitions
    - t2 (Materials): Exercises, worksheets, lectures
    - t3 (Case Studies): Real-world examples
    """
    
    # Calculate result allocation per tier
    t1_count = max(1, int(max_results * weights["t1"]))
    t2_count = max(1, int(max_results * weights["t2"]))
    t3_count = max(1, int(max_results * weights["t3"]))
    
    results = []
    
    # Query each tier (implementation depends on your vector store)
    # This is pseudocode - adapt to your actual retrieval implementation
    
    # T1: Frameworks
    t1_results = vector_search(
        query=query,
        filter={"tier": "t1_frameworks"},
        limit=t1_count
    )
    results.extend([{**r, "tier": "t1"} for r in t1_results])
    
    # T2: Materials
    t2_results = vector_search(
        query=query,
        filter={"tier": "t2_materials"},
        limit=t2_count
    )
    results.extend([{**r, "tier": "t2"} for r in t2_results])
    
    # T3: Case Studies
    t3_results = vector_search(
        query=query,
        filter={"tier": "t3_case_studies"},
        limit=t3_count
    )
    results.extend([{**r, "tier": "t3"} for r in t3_results])
    
    # Re-rank by semantic relevance across tiers
    return rerank_results(results, query)[:max_results]


def format_workshop_hint(results: List[dict], phase_name: str, bot_id: str) -> str:
    """Format retrieval results as workshop hint (not lecture)."""
    
    hint = f"<context phase='{phase_name}' bot='{bot_id}'>\n"
    
    for r in results:
        tier_label = {"t1": "FRAMEWORK", "t2": "EXERCISE", "t3": "EXAMPLE"}[r["tier"]]
        hint += f"[{tier_label}] {r['content'][:300]}...\n\n"
    
    hint += """
<grounding_instruction>
Use this context to GUIDE, not lecture.
Ask questions based on exercises (T2).
Reference frameworks (T1) briefly if user is confused.
Keep user focused on current phase objective.
</grounding_instruction>
</context>
"""
    return hint


def format_sandbox_context(results: List[dict], depth: ResearchDepth) -> str:
    """Format retrieval results for sandbox exploration."""
    
    context = f"<context mode='sandbox' depth='{depth.value if depth else 'exploring'}'>\n"
    
    for r in results:
        tier_label = {"t1": "FRAMEWORK", "t2": "EXERCISE", "t3": "CASE_STUDY"}[r["tier"]]
        context += f"[{tier_label}] {r['content'][:400]}...\n\n"
    
    context += """
<grounding_instruction>
Synthesize across sources.
Show how frameworks (T1) connect to real cases (T3).
Offer exercises (T2) if user wants to practice.
Connect multiple methodologies when relevant.
Always ask: "What problem does this help solve?"
</grounding_instruction>
</context>
"""
    return context
```

### 3.4 Grounding Prompts

```python
# prompts/grounding_prompts.py

GROUNDING_PROMPTS = {
    # Brainstorming grounding
    "PATTERN_CHECK": """
We've been exploring for a bit. Let me check:

• What patterns are you seeing?
• What's the most interesting thread so far?
• Who would care if you pulled on that thread?
""",

    "SYNTHESIS_PROMPT": """
Time to synthesize. You've gathered threads — now weave them.

Complete this:
'[WHO] struggles with [PROBLEM] because [REASON], 
 and if we could [SOLVE], then [OUTCOME].'

Can you fill that in?
""",

    "OPPORTUNITY_REQUIRED": """
We've explored a lot. Before we continue:

You need to articulate at least one opportunity.

An opportunity isn't a solution — it's a problem worth solving.

What's the single most promising problem you've identified?
""",

    # Build Venture grounding
    "STAGE_ASSESSMENT_REQUIRED": """
Before we build anything, let's figure out where you are.

Quick check — answer what you can:

**THE PROBLEM**
□ I can clearly state the problem I'm solving
□ I know who has this problem (specific people/companies)
□ I have evidence they care (conversations, data, etc.)

**THE SOLUTION**
□ I have a proposed solution approach
□ I know why it's better than alternatives

**THE BUSINESS**
□ I understand the market size
□ I have a business model in mind

Which boxes can you check?
""",

    "PROBLEM_VALIDATION_REQUIRED": """
Hold on. Before we build anything:

• What's the problem you're solving?
• Who has this problem?
• What evidence do you have that they care?

I can't help you build something until we've validated there's 
a problem worth solving.
""",

    # Document Review grounding
    "FEEDBACK_FOCUS": """
Before I review, tell me:

• What specific feedback are you looking for?
• What are you most uncertain about?
• What would make this review useful to you?
""",

    # Universal
    "EVIDENCE_REQUEST": """
You've made a claim. Let me ask:

• What evidence supports this?
• Where did this information come from?
• How confident are you in this?
""",

    "ASSUMPTION_CHECK": """
I'm hearing an assumption. Let's validate it:

• What would have to be true for this to work?
• How would you test if this assumption is correct?
• What happens if this assumption is wrong?
"""
}


def get_grounding_prompt(reason: str, context: dict = None) -> str:
    """Get appropriate grounding prompt with optional context injection."""
    
    prompt = GROUNDING_PROMPTS.get(reason, GROUNDING_PROMPTS["EVIDENCE_REQUEST"])
    
    # Inject context if provided
    if context:
        if "topics" in context and context["topics"]:
            prompt = prompt.replace(
                "exploring", 
                f"exploring {', '.join(context['topics'][:3])}"
            )
        if "turn_count" in context:
            if context["turn_count"] > 15:
                prompt = f"(Turn {context['turn_count']}) " + prompt
    
    return prompt
```

---

## Part 4: UI Components

### 4.1 Entry Point Selector (Welcome Flow)

```python
# ui/entry_point_selector.py

import chainlit as cl
from typing import Optional

async def show_entry_point_selector(show_welcome: bool = True) -> Optional[str]:
    """
    Display entry point selector on conversation start.
    
    Returns selected entry point or None if user provides free-form input.
    """
    
    if show_welcome:
        welcome_message = """
# Welcome to Mindrian

I'm Larry — your thinking partner for innovation.

**Where are you today?**
"""
        await cl.Message(content=welcome_message).send()
    
    # Entry point action buttons
    actions = [
        cl.Action(
            name="entry_brainstorming",
            value="brainstorming",
            label="🧠 Explore Ideas",
            description="Find problems worth solving"
        ),
        cl.Action(
            name="entry_document_review",
            value="document_review",
            label="📄 Get Feedback",
            description="Validate your thinking"
        ),
        cl.Action(
            name="entry_build_venture",
            value="build_venture",
            label="🚀 Build Venture",
            description="Execute on your opportunity"
        ),
    ]
    
    selector_message = await cl.Message(
        content="Or just tell me what's on your mind.",
        actions=actions
    ).send()
    
    return selector_message


@cl.action_callback("entry_brainstorming")
async def handle_brainstorming_entry(action: cl.Action):
    """Handle brainstorming entry point selection."""
    await _initialize_entry_point("brainstorming")
    
@cl.action_callback("entry_document_review")
async def handle_document_review_entry(action: cl.Action):
    """Handle document review entry point selection."""
    await _initialize_entry_point("document_review")

@cl.action_callback("entry_build_venture")
async def handle_build_venture_entry(action: cl.Action):
    """Handle build venture entry point selection."""
    await _initialize_entry_point("build_venture")


async def _initialize_entry_point(entry_point: str):
    """Initialize conversation state for selected entry point."""
    
    from state.conversation_state import ConversationState, Mode
    
    # Create state
    state = ConversationState(session_id=cl.user_session.get("session_id"))
    state.entry_point = entry_point
    
    # Set default mode based on entry point
    mode_defaults = {
        "brainstorming": Mode.SANDBOX,
        "document_review": Mode.WORKSHOP,
        "build_venture": Mode.ADAPTIVE
    }
    state.mode = mode_defaults[entry_point]
    
    # Store state
    cl.user_session.set("conversation_state", state)
    
    # Show entry-specific welcome
    welcomes = {
        "brainstorming": """
## 🧠 Exploration Mode

Let's find problems worth solving.

**What are you curious about?** What's been bugging you lately?

I'm not asking for a business plan. I'm asking: what's interesting?
""",
        "document_review": """
## 📄 Validation Mode

Show me what you've got, and I'll give you honest feedback.

**What would you like me to review?**

You can upload a document or describe your idea.
""",
        "build_venture": """
## 🚀 Build Mode

Let's turn your opportunity into a venture.

**First, let's assess where you are.**

I'll ask a few questions to understand your current stage.
"""
    }
    
    await cl.Message(content=welcomes[entry_point]).send()
    
    # Show appropriate sidebar/buttons
    await refresh_ui_for_entry_point(entry_point, state)


async def refresh_ui_for_entry_point(entry_point: str, state):
    """Refresh UI elements based on entry point."""
    
    # Get action buttons for this entry point
    buttons = get_entry_point_buttons(entry_point, state)
    
    # Update sidebar (TaskList)
    if entry_point == "build_venture" and state.stage_assessment_complete:
        await show_venture_progress_sidebar(state)
    elif state.mode.value == "workshop":
        await show_workshop_progress_sidebar(state)
    else:
        await show_exploration_progress_sidebar(state)


def get_entry_point_buttons(entry_point: str, state) -> list:
    """Get appropriate action buttons for entry point."""
    
    common_buttons = [
        cl.Action(
            name="export_document",
            value="export",
            label="📤 Package for Team"
        ),
    ]
    
    entry_buttons = {
        "brainstorming": [
            cl.Action(name="bank_opportunity", value="bank", label="🏦 Bank Opportunity"),
            cl.Action(name="get_perspectives", value="multi_agent", label="🔄 Get Perspectives"),
            cl.Action(name="deep_research", value="research", label="🔍 Deep Research"),
        ],
        "document_review": [
            cl.Action(name="red_team", value="red_team", label="🎯 Challenge This"),
            cl.Action(name="grade", value="grade", label="📊 Grade Against PWS"),
            cl.Action(name="suggest_improvements", value="improve", label="✨ Suggest Improvements"),
        ],
        "build_venture": [
            cl.Action(name="assess_stage", value="assess", label="📍 Assess My Stage"),
            cl.Action(name="next_step", value="next", label="➡️ What's Next?"),
            cl.Action(name="validate_assumption", value="validate", label="✅ Validate Assumption"),
        ]
    }
    
    return entry_buttons.get(entry_point, []) + common_buttons
```

### 4.2 Mode Toggle

```python
# ui/mode_toggle.py

import chainlit as cl
from state.conversation_state import Mode

async def show_mode_toggle(current_mode: Mode, entry_point: str):
    """
    Display mode toggle button.
    
    Only shown when both modes are available for the entry point.
    """
    
    # Entry points where mode toggle makes sense
    toggle_enabled = entry_point in ["brainstorming", "document_review"]
    
    if not toggle_enabled:
        return
    
    if current_mode == Mode.WORKSHOP:
        toggle_action = cl.Action(
            name="toggle_mode",
            value="sandbox",
            label="🔓 Switch to Exploration",
            description="Free exploration with same expertise"
        )
    else:
        toggle_action = cl.Action(
            name="toggle_mode",
            value="workshop",
            label="🔒 Switch to Workshop",
            description="Guided, phase-by-phase progression"
        )
    
    await cl.Message(
        content="",
        actions=[toggle_action]
    ).send()


@cl.action_callback("toggle_mode")
async def handle_mode_toggle(action: cl.Action):
    """Handle mode toggle."""
    
    state = cl.user_session.get("conversation_state")
    if not state:
        return
    
    new_mode = Mode.SANDBOX if action.value == "sandbox" else Mode.WORKSHOP
    
    # Switch mode and get context injection
    context_injection = state.switch_mode(new_mode)
    
    # Update session
    cl.user_session.set("conversation_state", state)
    
    # Show transition message
    await cl.Message(content=context_injection["injection"]).send()
    
    # Refresh UI
    from ui.entry_point_selector import refresh_ui_for_entry_point
    await refresh_ui_for_entry_point(state.entry_point, state)
```

### 4.3 Progress Sidebars

```python
# ui/progress_sidebars.py

import chainlit as cl
from state.conversation_state import ConversationState, Mode, ResearchDepth, VentureStage

async def show_workshop_progress_sidebar(state: ConversationState):
    """Show workshop phase progress in sidebar."""
    
    # Get phases for current agent
    from prompts.workshop_phases import get_phases_for_bot
    phases = get_phases_for_bot(state.current_agent)
    
    if not phases:
        return
    
    task_list = cl.TaskList()
    task_list.name = f"{state.current_agent.upper()} Workshop"
    
    for i, phase in enumerate(phases):
        completion = state.phase_completion.get(i, 0)
        
        if completion >= 0.9:
            status = cl.TaskStatus.DONE
        elif i == state.current_phase:
            status = cl.TaskStatus.RUNNING
        elif completion > 0:
            status = cl.TaskStatus.RUNNING
        else:
            status = cl.TaskStatus.READY
        
        task = cl.Task(
            title=phase["name"],
            status=status
        )
        await task_list.add_task(task)
    
    await task_list.send()


async def show_exploration_progress_sidebar(state: ConversationState):
    """Show exploration depth progress in sidebar."""
    
    task_list = cl.TaskList()
    task_list.name = "🧠 Exploration Progress"
    
    depth_stages = [
        ("Initial", ResearchDepth.INITIAL),
        ("Exploring", ResearchDepth.EXPLORING),
        ("Deep", ResearchDepth.DEEP),
        ("Synthesis", ResearchDepth.SYNTHESIS),
    ]
    
    for stage_name, stage_enum in depth_stages:
        if state.research_depth.value == stage_enum.value:
            status = cl.TaskStatus.RUNNING
        elif depth_stages.index((stage_name, stage_enum)) < \
             [d[1].value for d in depth_stages].index(state.research_depth.value):
            status = cl.TaskStatus.DONE
        else:
            status = cl.TaskStatus.READY
        
        task = cl.Task(
            title=stage_name,
            status=status
        )
        await task_list.add_task(task)
    
    # Add grounding indicators
    grounding_task = cl.Task(
        title=f"Grounding: {int(state.grounding.grounding_score() * 100)}%",
        status=cl.TaskStatus.RUNNING if state.grounding.grounding_score() < 1 else cl.TaskStatus.DONE
    )
    await task_list.add_task(grounding_task)
    
    # Add banked opportunities
    if state.opportunities_banked:
        opp_task = cl.Task(
            title=f"Opportunities: {len(state.opportunities_banked)}",
            status=cl.TaskStatus.DONE
        )
        await task_list.add_task(opp_task)
    
    await task_list.send()


async def show_venture_progress_sidebar(state: ConversationState):
    """Show Build Venture stage progress."""
    
    task_list = cl.TaskList()
    task_list.name = "🚀 Venture Progress"
    
    stages = [
        ("Pre-Opportunity", VentureStage.PRE_OPPORTUNITY),
        ("Opportunity Identified", VentureStage.OPPORTUNITY_IDENTIFIED),
        ("Well-Defined Problem", VentureStage.WELL_DEFINED_PROBLEM),
        ("Ready to Build", VentureStage.READY_TO_BUILD),
    ]
    
    for stage_name, stage_enum in stages:
        if state.venture_stage == stage_enum:
            status = cl.TaskStatus.RUNNING
        elif stages.index((stage_name, stage_enum)) < \
             [s[1] for s in stages].index(state.venture_stage):
            status = cl.TaskStatus.DONE
        else:
            status = cl.TaskStatus.READY
        
        task = cl.Task(
            title=stage_name,
            status=status
        )
        await task_list.add_task(task)
    
    await task_list.send()
```

---

## Part 5: Opportunity Bank Modifications

```python
# protocols/opportunity_bank.py - MODIFICATIONS

# Add to OpportunityRecord dataclass
@dataclass
class OpportunityRecord:
    # Existing fields...
    name: str
    description: str
    problem: str
    value_potential: str
    job_to_be_done: str
    solution_direction: str
    
    # NEW fields for triple-mode
    entry_point: str  # brainstorming | document_review | build_venture
    discovery_mode: str  # workshop | sandbox
    phase_or_depth: str  # Phase name OR research depth level
    methodology_applied: str  # Bot/agent that discovered it
    
    # Grounding evidence
    grounding_evidence: dict = field(default_factory=lambda: {
        "problem_articulated": False,
        "who_identified": False,
        "evidence_provided": False,
        "consequence_considered": False
    })
    
    # Extraction metadata
    extraction_confidence: float = 0.0
    extracted_at: datetime = field(default_factory=datetime.now)


async def bank_opportunity(
    opportunity: dict,
    state: ConversationState,
    require_problem: bool = True  # PWS discipline enforcement
) -> Optional[str]:
    """
    Bank an opportunity with full context from conversation state.
    
    PWS Discipline: Opportunities MUST have a problem statement.
    """
    
    # Enforce problem requirement
    if require_problem and not opportunity.get("problem"):
        return None  # Caller should prompt for problem statement
    
    # Create record with state context
    record = OpportunityRecord(
        name=opportunity["name"],
        description=opportunity.get("description", ""),
        problem=opportunity["problem"],
        value_potential=opportunity.get("value_potential", "unknown"),
        job_to_be_done=opportunity.get("job_to_be_done", ""),
        solution_direction=opportunity.get("solution_direction", ""),
        
        # Context from state
        entry_point=state.entry_point,
        discovery_mode=state.mode.value,
        phase_or_depth=state.current_phase if state.mode == Mode.WORKSHOP else state.research_depth.value,
        methodology_applied=state.current_agent or "larry",
        
        # Grounding from state
        grounding_evidence={
            "problem_articulated": state.grounding.problem_articulated,
            "who_identified": state.grounding.who_identified,
            "evidence_provided": state.grounding.evidence_provided,
            "consequence_considered": state.grounding.consequences_considered
        },
        
        extraction_confidence=opportunity.get("confidence", 0.7)
    )
    
    # Store in Supabase
    result = await supabase_client.table("opportunity_bank").insert(
        record.to_dict()
    ).execute()
    
    if result.data:
        opp_id = result.data[0]["id"]
        state.opportunities_banked.append(opp_id)
        return opp_id
    
    return None


# Add to Supabase schema (migration)
OPPORTUNITY_BANK_MIGRATION = """
ALTER TABLE opportunity_bank
ADD COLUMN IF NOT EXISTS entry_point TEXT,
ADD COLUMN IF NOT EXISTS discovery_mode TEXT,
ADD COLUMN IF NOT EXISTS phase_or_depth TEXT,
ADD COLUMN IF NOT EXISTS methodology_applied TEXT,
ADD COLUMN IF NOT EXISTS grounding_evidence JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_opp_entry_point ON opportunity_bank(entry_point);
CREATE INDEX IF NOT EXISTS idx_opp_discovery_mode ON opportunity_bank(discovery_mode);
"""
```

---

## Part 6: A2A Protocol Modifications

```python
# protocols/a2a_protocol.py - MODIFICATIONS

@dataclass
class A2AHandoff:
    """Agent-to-Agent handoff with entry point and mode context."""
    
    # Existing fields
    from_agent: str
    to_agent: str
    handoff_type: str  # delegate | escalate | collaborate
    context_summary: str
    
    # NEW fields for triple-mode
    entry_point: str
    from_mode: str  # workshop | sandbox
    to_mode: str  # preserve | workshop | sandbox
    
    # State to preserve
    preserved_state: dict = field(default_factory=dict)
    
    # Return instructions
    return_expected: bool = True
    return_instructions: str = ""
    
    def to_markdown(self) -> str:
        """Generate handoff markdown for receiving agent."""
        return f"""
---
protocol: a2a/v3
from_agent: {self.from_agent}
to_agent: {self.to_agent}
handoff_type: {self.handoff_type}
entry_point: {self.entry_point}
mode_transition: {self.from_mode} → {self.to_mode}
---

<preserved_state>
{json.dumps(self.preserved_state, indent=2)}
</preserved_state>

<context_summary>
{self.context_summary}
</context_summary>

<task_for_receiving_agent>
User is in {self.entry_point} entry point.
Mode: {self.to_mode if self.to_mode != 'preserve' else self.from_mode}

{self.return_instructions if self.return_instructions else 'Complete the requested task.'}
</task_for_receiving_agent>

<return_instructions>
{'Return control to ' + self.from_agent + ' when complete.' if self.return_expected else 'No return expected.'}
</return_instructions>
"""


async def handoff_to_agent(
    state: ConversationState,
    to_agent: str,
    reason: str,
    preserve_mode: bool = True
) -> A2AHandoff:
    """Create handoff with full entry point and mode context."""
    
    handoff = A2AHandoff(
        from_agent=state.current_agent or "larry",
        to_agent=to_agent,
        handoff_type="delegate",
        entry_point=state.entry_point,
        from_mode=state.mode.value,
        to_mode="preserve" if preserve_mode else _get_default_mode(to_agent),
        context_summary=reason,
        preserved_state=state.to_dict(),
        return_expected=True,
        return_instructions=f"Return with findings to continue {state.entry_point} workflow."
    )
    
    # Log handoff
    await log_handoff(handoff)
    
    return handoff


def _get_default_mode(agent_id: str) -> str:
    """Get default mode for an agent."""
    workshop_only = ["pws_grading"]
    sandbox_only = ["red_team"]
    
    if agent_id in workshop_only:
        return "workshop"
    elif agent_id in sandbox_only:
        return "sandbox"
    return "preserve"
```

---

## Part 7: New Agent Creation Rules

### 7.1 Agent Template

```python
# prompts/agent_template.py

"""
Template for creating new agents in the triple-mode architecture.

Every agent MUST:
1. Implement LARRY_CORE_IDENTITY
2. Specify supported entry points
3. Define mode configurations
4. Include PWS grounding rules
"""

AGENT_TEMPLATE = {
    # Identity
    "id": "new_agent_id",
    "name": "Human-Readable Agent Name",
    "description": "What this agent does in one sentence",
    
    # Core identity (MUST include LARRY_CORE_IDENTITY)
    "system_prompt_base": """
{LARRY_CORE_IDENTITY}

## YOUR SPECIFIC EXPERTISE

[Describe agent's unique methodology/expertise]

## HOW YOU APPLY YOUR EXPERTISE

[Describe how this agent thinks about problems]
""",
    
    # Entry point configuration
    "entry_points": {
        "brainstorming": {
            "enabled": True,
            "triggers": ["keyword1", "keyword2"],  # When to suggest this agent
            "default_mode": "sandbox",
            "tier_weights": {"t1": 0.35, "t2": 0.25, "t3": 0.40}
        },
        "document_review": {
            "enabled": False,
            "triggers": [],
            "default_mode": "workshop",
            "tier_weights": {"t1": 0.20, "t2": 0.50, "t3": 0.30}
        },
        "build_venture": {
            "enabled": True,
            "triggers": ["keyword3"],
            "default_mode": "adaptive",
            "stage_required": "opportunity_identified",  # Minimum stage
            "tier_weights": {"t1": 0.30, "t2": 0.40, "t3": 0.30}
        }
    },
    
    # Workshop configuration
    "workshop_config": {
        "has_phases": True,
        "phases": [
            {
                "name": "Phase 1 Name",
                "objective": "What user should accomplish",
                "tier_weights": {"t1": 0.6, "t2": 0.3, "t3": 0.1},
                "completion_criteria": {
                    "artifact": "problem_statement",  # Required output
                    "confidence_threshold": 0.7,
                    "required_elements": ["who", "what", "evidence"]
                }
            },
            # ... more phases (4-6 recommended)
        ],
        "multi_agent_access": "on_request"  # on_request | suggested | disabled
    },
    
    # Sandbox configuration
    "sandbox_config": {
        "depth_levels": ["initial", "exploring", "deep", "synthesis"],
        "default_tier_weights": {"t1": 0.33, "t2": 0.33, "t3": 0.34},
        "grounding": {
            "gentle_after_turns": 5,
            "assertive_at_depth": "deep",
            "hard_stop_turns": 15
        },
        "multi_agent_access": "suggested"
    },
    
    # PWS grounding (REQUIRED)
    "pws_grounding": {
        "enforce_problem_first": True,
        "require_evidence_for_claims": True,
        "opportunity_bank_requires_problem": True
    },
    
    # Intelligence integration
    "intelligence": {
        "graphrag_enabled": True,
        "opportunity_bank": True,
        "research_tools": True,
        "multi_agent": True
    },
    
    # Kill criteria (when to retire this agent)
    "kill_criteria": {
        "usage_threshold": "< 5 sessions/month for 3 months",
        "satisfaction_threshold": "< 3.0 avg rating",
        "methodology_fit": "user_feedback indicates misalignment"
    }
}
```

### 7.2 Required Elements Checklist

```markdown
## New Agent Checklist

Before deploying a new agent, verify:

### Identity
- [ ] Agent ID follows convention: lowercase_underscore
- [ ] Name is human-readable
- [ ] Description is one clear sentence
- [ ] System prompt includes LARRY_CORE_IDENTITY

### Entry Points
- [ ] At least one entry point enabled
- [ ] Triggers defined for each enabled entry point
- [ ] Default mode specified
- [ ] Tier weights defined

### Workshop Mode (if enabled)
- [ ] 4-6 phases defined
- [ ] Each phase has clear objective
- [ ] Each phase has completion criteria
- [ ] Each phase has tier weights
- [ ] Tier weights follow pattern: early=T1-heavy, middle=T2-heavy, late=T3-heavy

### Sandbox Mode (if enabled)
- [ ] Depth tracking configured
- [ ] Grounding intervals set (5/10/15 turns recommended)
- [ ] Multi-agent access configured

### PWS Grounding
- [ ] Problem-first enforcement enabled
- [ ] Evidence requirement enabled
- [ ] Opportunity bank requires problem statement

### Testing
- [ ] Tested in all enabled entry points
- [ ] Tested mode switching
- [ ] Tested grounding prompts fire correctly
- [ ] Tested opportunity banking works
- [ ] Tested document export works
```

---

## Part 8: Document Generation

```python
# protocols/document_generator.py

from enum import Enum
from typing import Optional
from state.conversation_state import ConversationState

class DocumentType(Enum):
    OPPORTUNITY_SUMMARY = "opportunity_summary"
    VALIDATION_REPORT = "validation_report"
    TEAM_HANDOFF = "team_handoff"
    STAGE_ASSESSMENT = "stage_assessment"

DOCUMENT_TEMPLATES = {
    DocumentType.OPPORTUNITY_SUMMARY: """
# Opportunity: {name}

## The Problem
**Who:** {who}
**What:** {problem}
**Why:** {why}
**Evidence:** {evidence}

## The Opportunity
**Insight:** {insight}
**Value:** {value_potential}
**Differentiation:** {differentiation}

## Open Questions
{open_questions}

## Recommended Next Steps
{next_steps}

## Sources Referenced
{sources}

---
*Generated from Mindrian {entry_point} session*
*Methodology: {methodology}*
*Date: {date}*
""",

    DocumentType.VALIDATION_REPORT: """
# Validation Report: {topic}

## What We Validated
| Assumption | Status | Evidence |
|------------|--------|----------|
{validation_table}

## Key Findings
{findings}

## Remaining Uncertainties
{uncertainties}

## Confidence Assessment
**Overall Confidence:** {confidence}
**Reasoning:** {confidence_reasoning}

## Recommendations
{recommendations}

---
*Feedback generated by Mindrian*
*Entry Point: {entry_point}*
*Date: {date}*
""",

    DocumentType.TEAM_HANDOFF: """
# Team Brief: {topic}

## Executive Summary
{summary}

## Work Completed
{work_completed}

## Key Decisions Made
| Decision | Rationale | Confidence |
|----------|-----------|------------|
{decisions_table}

## Decisions Pending (For Team Discussion)
{pending_decisions}

## Resources Referenced
{resources}

## Suggested Discussion Questions
{discussion_questions}

## Next Steps
{next_steps}

---
*Prepared for team handoff*
*Entry Point: {entry_point}*
*Individual work by: {user}*
*Date: {date}*
"""
}


async def generate_document(
    doc_type: DocumentType,
    state: ConversationState,
    context: dict
) -> str:
    """Generate document from conversation state and context."""
    
    template = DOCUMENT_TEMPLATES[doc_type]
    
    # Build template variables from state and context
    variables = {
        "entry_point": state.entry_point,
        "methodology": state.current_agent or "Larry",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "user": state.user_id or "Anonymous",
    }
    
    # Add context-specific variables
    variables.update(context)
    
    # Fill template
    document = template.format(**variables)
    
    # Log document creation
    state.documents_created.append({
        "type": doc_type.value,
        "created_at": datetime.now().isoformat(),
        "entry_point": state.entry_point
    })
    
    return document


async def trigger_document_creation(
    state: ConversationState,
    trigger_reason: str
) -> Optional[str]:
    """
    Check if document creation should be triggered and prompt user.
    
    Triggers:
    - User request
    - Milestone reached (phase complete, opportunity banked)
    - Validation gate
    """
    
    prompts = {
        "opportunity_banked": """
You've banked an opportunity! 🏦

Would you like to create a summary for your team?

This will package:
• Problem statement
• Key insights
• Evidence gathered
• Open questions
• Recommended next steps

[📄 Create Summary] [Continue Exploring]
""",
        "phase_complete": """
Nice work completing this phase! ✅

Before moving on, would you like to export your progress?

[📄 Export Progress] [Continue to Next Phase]
""",
        "synthesis_ready": """
You've done significant exploration. Ready to synthesize?

I can help you create a document that captures:
• What you've learned
• Key patterns identified
• Questions still open
• Recommended next steps

[📄 Create Synthesis Doc] [Keep Exploring]
""",
        "user_request": None  # No prompt needed, just generate
    }
    
    return prompts.get(trigger_reason)
```

---

## Part 9: Main Chat Handler Modifications

```python
# mindrian_chat.py - KEY MODIFICATIONS

# Add imports
from protocols.entry_point_router import EntryPointRouter, EntryPoint
from state.conversation_state import ConversationState, Mode
from ui.entry_point_selector import show_entry_point_selector, refresh_ui_for_entry_point
from prompts.grounding_prompts import get_grounding_prompt, GROUNDING_PROMPTS
from prompts.larry_core import LARRY_CORE_IDENTITY

# Initialize router
entry_router = EntryPointRouter()

@cl.on_chat_start
async def on_chat_start():
    """Initialize session with entry point selection."""
    
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    
    # Show entry point selector
    await show_entry_point_selector()
    
    # State will be initialized when user selects entry point or sends message


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages with entry point awareness."""
    
    state = cl.user_session.get("conversation_state")
    
    # First message - need to route to entry point
    if not state:
        state = await _initialize_from_message(message)
        cl.user_session.set("conversation_state", state)
    
    # Check for grounding intervention
    should_ground, ground_reason = state.should_ground()
    if should_ground:
        grounding_prompt = get_grounding_prompt(ground_reason, {
            "topics": state.topics_explored,
            "turn_count": state.turn_count
        })
        await cl.Message(content=grounding_prompt).send()
        state.turns_since_grounding = 0
        return
    
    # Build context for LLM
    context = await _build_context(state, message.content)
    
    # Get response
    response = await _get_llm_response(context, message.content)
    
    # Update state
    state.update_turn(message.content, response)
    cl.user_session.set("conversation_state", state)
    
    # Check for document creation triggers
    doc_trigger = await _check_document_triggers(state)
    if doc_trigger:
        await cl.Message(content=doc_trigger).send()
    
    # Send response
    await cl.Message(content=response).send()
    
    # Refresh UI
    await refresh_ui_for_entry_point(state.entry_point, state)


async def _initialize_from_message(message: cl.Message) -> ConversationState:
    """Initialize state by routing first message to entry point."""
    
    # Check for attachments
    has_attachment = bool(message.elements)
    
    # Route to entry point
    routing = entry_router.route(message.content, has_attachment)
    
    # Handle ambiguous routing
    if routing.clarification_needed:
        await cl.Message(content=routing.clarification_prompt).send()
        # Create temporary state
        state = ConversationState(session_id=cl.user_session.get("session_id"))
        return state
    
    # Create state for identified entry point
    state = ConversationState(session_id=cl.user_session.get("session_id"))
    state.entry_point = routing.entry_point.value
    state.current_agent = routing.suggested_agent
    
    # Set default mode
    mode_defaults = {
        "brainstorming": Mode.SANDBOX,
        "document_review": Mode.WORKSHOP,
        "build_venture": Mode.ADAPTIVE
    }
    state.mode = mode_defaults.get(state.entry_point, Mode.SANDBOX)
    
    return state


async def _build_context(state: ConversationState, user_message: str) -> str:
    """Build full context for LLM including entry point and mode context."""
    
    # Start with Larry core identity
    context = LARRY_CORE_IDENTITY
    
    # Add entry point context
    entry_contexts = {
        "brainstorming": BRAINSTORMING_CONTEXT,
        "document_review": DOCUMENT_REVIEW_CONTEXT,
        "build_venture": BUILD_VENTURE_CONTEXT
    }
    context += "\n\n" + entry_contexts.get(state.entry_point, "")
    
    # Add mode context
    if state.mode == Mode.WORKSHOP:
        context += f"\n\n<mode>workshop</mode>\n<current_phase>{state.current_phase}</current_phase>"
    else:
        context += f"\n\n<mode>sandbox</mode>\n<research_depth>{state.research_depth.value}</research_depth>"
    
    # Add grounding state
    context += f"""
<grounding_state>
problem_articulated: {state.grounding.problem_articulated}
who_identified: {state.grounding.who_identified}
evidence_provided: {state.grounding.evidence_provided}
grounding_score: {state.grounding.grounding_score()}
</grounding_state>
"""
    
    # Add RAG context with mode-aware tier weighting
    from tools.graphrag_lite import enrich_for_bot
    rag_context = enrich_for_bot(
        message=user_message,
        turn_count=state.turn_count,
        bot_id=state.current_agent or "larry",
        entry_point=state.entry_point,
        mode=state.mode,
        current_phase=state.current_phase if state.mode == Mode.WORKSHOP else None,
        research_depth=state.research_depth if state.mode == Mode.SANDBOX else None
    )
    if rag_context:
        context += f"\n\n{rag_context}"
    
    return context
```

---

## Part 10: Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create `ConversationState` class
- [ ] Create `EntryPointRouter` class
- [ ] Implement `LARRY_CORE_IDENTITY` prompt
- [ ] Modify `on_chat_start` for entry point selection
- [ ] Implement basic entry point UI buttons

**Deliverable:** Users can select entry point, basic routing works

### Phase 2: Brainstorming Entry Point (Weeks 3-4)
- [ ] Implement sandbox mode with depth tracking
- [ ] Add grounding prompts (5/10/15 turns)
- [ ] Modify GraphRAG for sandbox tier weighting
- [ ] Add exploration progress sidebar
- [ ] Implement opportunity banking with entry point context

**Deliverable:** Full brainstorming experience works

### Phase 3: Document Review Entry Point (Weeks 5-6)
- [ ] Implement workshop mode for review agents
- [ ] Add feedback structure (Critical/Important/Nice-to-have)
- [ ] Integrate Red Team and Devil's Advocate
- [ ] Add document upload flow
- [ ] Implement validation report generation

**Deliverable:** Full document review experience works

### Phase 4: Build Venture Entry Point (Weeks 7-8)
- [ ] Implement stage assessment flow
- [ ] Add stage-based agent routing
- [ ] Implement adaptive mode switching
- [ ] Add venture progress sidebar
- [ ] Implement problem validation checkpoints

**Deliverable:** Full build venture experience works

### Phase 5: Document Creation Layer (Weeks 9-10)
- [ ] Implement document templates
- [ ] Add milestone triggers
- [ ] Build export functionality (MD, PDF, DOCX)
- [ ] Add "Package for Team" button everywhere
- [ ] Test team handoff workflow

**Deliverable:** Documents can be created from any entry point

### Phase 6: Integration & Polish (Weeks 11-12)
- [ ] Cross-entry-point context preservation
- [ ] A2A protocol updates
- [ ] Opportunity Bank schema migration
- [ ] Daily summary with entry point analytics
- [ ] User testing and iteration

**Deliverable:** Complete system ready for production

---

## Part 11: Database Migrations

```sql
-- migrations/001_triple_mode_schema.sql

-- Add entry point tracking to sessions
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS entry_point TEXT,
ADD COLUMN IF NOT EXISTS mode TEXT DEFAULT 'sandbox',
ADD COLUMN IF NOT EXISTS venture_stage TEXT;

-- Add entry point and mode to opportunity_bank
ALTER TABLE opportunity_bank
ADD COLUMN IF NOT EXISTS entry_point TEXT,
ADD COLUMN IF NOT EXISTS discovery_mode TEXT,
ADD COLUMN IF NOT EXISTS phase_or_depth TEXT,
ADD COLUMN IF NOT EXISTS methodology_applied TEXT,
ADD COLUMN IF NOT EXISTS grounding_evidence JSONB DEFAULT '{}';

-- Add entry point to feedback
ALTER TABLE feedback
ADD COLUMN IF NOT EXISTS entry_point TEXT,
ADD COLUMN IF NOT EXISTS mode TEXT;

-- Add entry point to journal_entries
ALTER TABLE journal_entries
ADD COLUMN IF NOT EXISTS entry_point TEXT,
ADD COLUMN IF NOT EXISTS mode TEXT;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sessions_entry_point ON sessions(entry_point);
CREATE INDEX IF NOT EXISTS idx_opp_entry_point ON opportunity_bank(entry_point);
CREATE INDEX IF NOT EXISTS idx_opp_discovery_mode ON opportunity_bank(discovery_mode);
CREATE INDEX IF NOT EXISTS idx_feedback_entry_point ON feedback(entry_point);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    user_id TEXT,
    document_type TEXT NOT NULL,
    content TEXT NOT NULL,
    entry_point TEXT,
    methodology TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_entry_point ON documents(entry_point);
```

---

## Part 12: Success Metrics

### Quantitative
| Metric | Target | Measurement |
|--------|--------|-------------|
| Entry point selection rate | >80% | % of sessions with clear entry point |
| Problem articulation rate | >70% | % of brainstorming sessions producing problem statement |
| Opportunity bank rate | >50% | % of sessions banking at least one opportunity |
| Document export rate | >60% | % of sessions exporting a document |
| Cross-entry-point journeys | >30% | % of users using multiple entry points |
| Grounding effectiveness | >85% | % of grounding prompts followed |

### Qualitative
- [ ] Users feel challenged but supported (Larry vibe)
- [ ] Problem-first discipline maintained
- [ ] Exploration leads to synthesis, not drift
- [ ] Feedback is actionable, not vague
- [ ] Documents are useful for team handoff

---

## Appendix A: Entry Point Context Prompts

```python
# prompts/entry_brainstorming.py

BRAINSTORMING_CONTEXT = """
## ENTRY POINT: Brainstorming (Exploration)

**User State:** Looking for problems worth solving, exploring opportunities

**Your Role:** Help discover, not prescribe. Open doors, don't close them.

**Current Goal:** Generate a portfolio of opportunities, not commit to one.

### Grounding Rules
- After 5 turns: Ask what patterns they're seeing
- After 10 turns: Push for synthesis
- After 15 turns: Require articulation of at least one opportunity

### Available Agents
TTA, Domain Explorer, Beautiful Question, Scenario Planning, Known-Unknowns

### Mode
Sandbox (exploration-first, all tiers accessible)

### Your Behavior
- Ask "What are you curious about?" not "What's your business idea?"
- Explore widely, then ground periodically
- Celebrate interesting threads, then ask "Who would care?"
- Push for problem articulation, not solution excitement
"""

# prompts/entry_document_review.py

DOCUMENT_REVIEW_CONTEXT = """
## ENTRY POINT: Document Review (Validation)

**User State:** Has something to evaluate, wants feedback

**Your Role:** Critique to improve, not to dismiss. Find flaws before others do.

**Current Goal:** Provide actionable feedback that makes their work stronger.

### Critique Framework
- Reality Check: Is the problem/evidence real?
- Feasibility Check: Can this actually be done?
- Value Check: Is it worth doing?
- Bias Check: What cognitive distortions are present?

### Feedback Structure
- CRITICAL: Must fix
- IMPORTANT: Should fix
- NICE-TO-HAVE: Polish if time

### Available Agents
PWS Grading, Red Team, Devil's Advocate, Investment Analysis, Multi-Perspective

### Mode
Workshop (structure-first, rubric-driven)

### Your Behavior
- Ask "What specific feedback are you looking for?" first
- Be direct — that's respect, not unkindness
- Prioritize feedback by severity
- Always end with constructive path forward
"""

# prompts/entry_build_venture.py

BUILD_VENTURE_CONTEXT = """
## ENTRY POINT: Build Venture (Execution)

**User State:** Has a validated (or assumed) opportunity, wants to build

**Your Role:** Guide execution while maintaining problem discipline.

### Critical Check
Before ANY framework application, verify problem is validated.
If problem is not validated, route back to Document Review or Brainstorming.

### Stage Awareness
Adapt approach based on user's current stage:
- Pre-opportunity → Route to Brainstorming
- Opportunity identified → Problem definition focus
- Well-defined problem → Solution/business model focus
- Ready to build → Execution/investment focus

### Execution Discipline
- Every decision should trace back to the problem
- Every feature should trace back to a job-to-be-done
- Every assumption should have a validation plan

### Available Agents
JTBD, Ackoff, BMC, S-Curve, BONO, Investment Analysis

### Mode
Adaptive (based on stage)

### Your Behavior
- Always assess stage first
- Don't let users skip problem validation
- Connect every decision back to "Who has this problem?"
- Push for evidence at every stage
"""
```

---

## Final Notes

### What Changed from Original Dual-Mode Proposal

| Original | New |
|----------|-----|
| 14 bots × 2 modes | 3 entry points × relevant agents |
| Mode toggle per bot | Entry point determines mode defaults |
| Workshop/Sandbox as primary distinction | User journey stage as primary distinction |
| Document creation as afterthought | Document creation as core feature |
| Technology-driven (RAG tiers) | User-journey-driven (PWS methodology) |

### Key Implementation Principles

1. **Larry vibe is non-negotiable** — Problem-first, provocative, grounded, direct
2. **Entry point = user journey stage** — Not just a routing mechanism
3. **Document creation = team handoff bridge** — Optimized for individual→team workflow
4. **Grounding is adaptive** — Not annoying, but disciplined
5. **Modes are subordinate to entry points** — Tier weighting follows user intent

### Questions for Dev Team

1. What's your current Chainlit version? (UI components may need adaptation)
2. Is the Supabase schema flexible for the new columns?
3. Do you have capacity for the 12-week phased rollout?
4. Should we start with one entry point as pilot?

---

*"What problem are you actually solving?"* — Larry
