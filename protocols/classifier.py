"""
Two-Stage Classifier - Cynefin + PWS Classification

This module implements the inline two-stage classification for the A2A orchestration system.

Key Insight: Cynefin and PWS are orthogonal dimensions:
- Cynefin: How uncertain is the situation? (Clear → Complicated → Complex → Chaotic)
- PWS: Where in the problem lifecycle? (Un-Defined → Ill-Defined → Well-Defined)

Implementation Note: This is inline in Python, NOT a separate Edge Function.
Extract to a service only if:
1. Multiple clients need the classifier independently
2. You need to A/B test classifier versions
3. Latency from Python becomes a bottleneck
"""

from typing import Literal, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


CynefinDomain = Literal["clear", "complicated", "complex", "chaotic"]
PWSType = Literal["un-defined", "ill-defined", "well-defined"]


@dataclass
class Classification:
    """Result of two-stage classification."""
    cynefin: CynefinDomain
    pws: PWSType
    cynefin_confidence: float
    pws_confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "cynefin": self.cynefin,
            "pws": self.pws,
            "cynefin_confidence": self.cynefin_confidence,
            "pws_confidence": self.pws_confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Classification":
        return cls(**data)


# Classification prompt template
CLASSIFIER_PROMPT = """You are a problem classifier for an innovation methodology system.

Classify the user's input on TWO orthogonal dimensions:

## DIMENSION 1: CYNEFIN DOMAIN (How uncertain is the situation?)

- **Clear**: Obvious cause-effect relationships. Best practices exist. "We know what works."
  - Example: "How do I format a CSV file?"
  - Example: "What's the formula for compound interest?"

- **Complicated**: Cause-effect requires analysis. Experts can help. Multiple right answers exist.
  - Example: "How should we architect our payment system?"
  - Example: "What's the best marketing strategy for our product?"

- **Complex**: Cause-effect only clear in retrospect. Need to probe and experiment. Patterns emerge.
  - Example: "How will AI change the healthcare industry?"
  - Example: "What's the future of urban transportation?"

- **Chaotic**: No clear cause-effect. Need to act immediately to stabilize.
  - Example: "Our startup is running out of money in 2 weeks"
  - Example: "A competitor just launched the exact product we're building"

## DIMENSION 2: PWS PROBLEM TYPE (Where in the problem lifecycle?)

- **Un-Defined**: Don't know what problem to solve yet. Exploring domains and trends.
  - Example: "What opportunities exist in sustainable energy?"
  - Example: "I want to start a company but don't know what to build"

- **Ill-Defined**: Have identified an opportunity but need to refine it into a clear problem.
  - Example: "People seem frustrated with banking apps, how can we help?"
  - Example: "There's something wrong with how hospitals handle patient data"

- **Well-Defined**: Know the problem clearly, ready to design a solution.
  - Example: "How can we reduce patient wait times from 45 min to 15 min?"
  - Example: "We need a mobile app that lets users track their carbon footprint"

## USER INPUT

{text}

{context_section}

## YOUR RESPONSE

Respond with a JSON object:
{{
  "cynefin": "clear" | "complicated" | "complex" | "chaotic",
  "pws": "un-defined" | "ill-defined" | "well-defined",
  "cynefin_confidence": 0.0-1.0,
  "pws_confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why you classified this way"
}}

Only respond with the JSON object, no other text."""


async def classify(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    llm_client: Any = None,
    temperature: float = 0.3
) -> Classification:
    """
    Classify user input on Cynefin and PWS dimensions.

    Args:
        text: User input to classify
        context: Optional context from previous turns
        llm_client: LLM client (if None, uses default)
        temperature: LLM temperature (lower = more consistent)

    Returns:
        Classification result with both dimensions and confidence scores
    """
    # Build context section
    context_section = ""
    if context:
        context_section = f"""## CONTEXT FROM PREVIOUS TURNS

Previous artifacts: {json.dumps(context.get('artifacts', [])[:3], indent=2)}
Current phase: {context.get('current_phase', 'unknown')}
Previous agent: {context.get('previous_agent', 'none')}
"""

    prompt = CLASSIFIER_PROMPT.format(
        text=text,
        context_section=context_section
    )

    # Use provided LLM client or default
    if llm_client is None:
        # Import here to avoid circular imports
        try:
            from google import genai
            client = genai.Client()
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "temperature": temperature,
                    "response_mime_type": "application/json"
                }
            )
            result_text = response.text
        except ImportError:
            logger.warning("Google GenAI not available, using mock classification")
            return _mock_classify(text)
    else:
        response = await llm_client.invoke(prompt, temperature=temperature)
        result_text = response

    # Parse response
    try:
        result = json.loads(result_text)
        return Classification(
            cynefin=result["cynefin"],
            pws=result["pws"],
            cynefin_confidence=result["cynefin_confidence"],
            pws_confidence=result["pws_confidence"],
            reasoning=result["reasoning"]
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse classification response: {e}")
        return _fallback_classify(text)


async def classify_with_logging(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    llm_client: Any = None,
    log_fn: Optional[callable] = None
) -> Classification:
    """
    Classify with logging for analytics and validation.

    Logs classification decisions for:
    - Validating 80% accuracy target
    - Identifying systematic misclassifications
    - A/B testing classifier improvements
    """
    import time
    start_time = time.time()

    result = await classify(text, context, llm_client)

    latency_ms = (time.time() - start_time) * 1000

    log_entry = {
        "input_hash": _hash_text(text),  # Privacy-safe
        "cynefin_result": result.cynefin,
        "pws_result": result.pws,
        "cynefin_confidence": result.cynefin_confidence,
        "pws_confidence": result.pws_confidence,
        "latency_ms": latency_ms,
        "timestamp": datetime.utcnow().isoformat()
    }

    if log_fn:
        await log_fn(log_entry)
    else:
        logger.info(f"Classification: {json.dumps(log_entry)}")

    return result


def _hash_text(text: str) -> str:
    """Create privacy-safe hash of input text."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _mock_classify(text: str) -> Classification:
    """Mock classification for testing without LLM."""
    text_lower = text.lower()

    # Simple heuristics for mock
    if any(w in text_lower for w in ["how do i", "what's the", "help me"]):
        cynefin = "complicated"
    elif any(w in text_lower for w in ["future of", "what will", "opportunity"]):
        cynefin = "complex"
    elif any(w in text_lower for w in ["urgent", "emergency", "running out"]):
        cynefin = "chaotic"
    else:
        cynefin = "complex"

    if any(w in text_lower for w in ["don't know", "explore", "opportunity"]):
        pws = "un-defined"
    elif any(w in text_lower for w in ["how can we", "reduce", "improve"]):
        pws = "well-defined"
    else:
        pws = "ill-defined"

    return Classification(
        cynefin=cynefin,
        pws=pws,
        cynefin_confidence=0.6,
        pws_confidence=0.6,
        reasoning="Mock classification based on keyword matching"
    )


def _fallback_classify(text: str) -> Classification:
    """Fallback classification when LLM fails."""
    return Classification(
        cynefin="complex",
        pws="ill-defined",
        cynefin_confidence=0.3,
        pws_confidence=0.3,
        reasoning="Fallback classification due to LLM error"
    )


# === Routing Matrix ===

def get_routing_recommendation(classification: Classification) -> Dict[str, Any]:
    """
    Get agent routing recommendation based on classification.

    Returns recommended agent, interaction style, and tools.
    """
    cynefin = classification.cynefin
    pws = classification.pws

    # Routing matrix
    routing = {
        ("complex", "un-defined"): {
            "primary_agent": "tta",
            "style": "high_divergence",
            "tools": ["trend_research", "scenario_analysis"],
            "red_team_frequency": "every_output"
        },
        ("complex", "ill-defined"): {
            "primary_agent": "jtbd",
            "style": "structured_exploration",
            "tools": ["process_mapping", "job_statements"],
            "red_team_frequency": "on_transitions"
        },
        ("complex", "well-defined"): {
            "primary_agent": "validation",
            "style": "careful_validation",
            "tools": ["evidence_gathering", "assumption_testing"],
            "red_team_frequency": "intensive"
        },
        ("complicated", "un-defined"): {
            "primary_agent": "tta",
            "style": "bounded_exploration",
            "tools": ["expert_consultation", "trend_research"],
            "red_team_frequency": "on_transitions"
        },
        ("complicated", "ill-defined"): {
            "primary_agent": "jtbd",
            "style": "expert_guided",
            "tools": ["process_mapping", "best_practices"],
            "red_team_frequency": "periodic"
        },
        ("complicated", "well-defined"): {
            "primary_agent": "solution_designer",
            "style": "direct_execution",
            "tools": ["implementation_planning"],
            "red_team_frequency": "final_only"
        },
        ("clear", "un-defined"): {
            "primary_agent": "lawrence",
            "style": "quick_scan",
            "tools": ["basic_research"],
            "red_team_frequency": "optional"
        },
        ("clear", "ill-defined"): {
            "primary_agent": "jtbd",
            "style": "standard_process",
            "tools": ["templates", "checklists"],
            "red_team_frequency": "final_only"
        },
        ("clear", "well-defined"): {
            "primary_agent": "execution",
            "style": "execute_immediately",
            "tools": ["implementation"],
            "red_team_frequency": "none"
        },
        ("chaotic", "un-defined"): {
            "primary_agent": "lawrence",
            "style": "stabilize_first",
            "tools": ["triage", "quick_wins"],
            "red_team_frequency": "post_stabilization"
        },
        ("chaotic", "ill-defined"): {
            "primary_agent": "lawrence",
            "style": "rapid_framing",
            "tools": ["constraint_mapping"],
            "red_team_frequency": "post_stabilization"
        },
        ("chaotic", "well-defined"): {
            "primary_agent": "execution",
            "style": "crisis_execution",
            "tools": ["rapid_implementation"],
            "red_team_frequency": "none"
        },
    }

    key = (cynefin, pws)
    recommendation = routing.get(key, {
        "primary_agent": "lawrence",
        "style": "adaptive",
        "tools": ["general"],
        "red_team_frequency": "on_transitions"
    })

    return {
        **recommendation,
        "classification": classification.to_dict(),
        "confidence": min(classification.cynefin_confidence, classification.pws_confidence)
    }


# === Test Cases ===

TEST_CASES = [
    # Clear cases
    {
        "text": "How do I format a JSON file in Python?",
        "expected_cynefin": "clear",
        "expected_pws": "well-defined"
    },
    # Complicated cases
    {
        "text": "How should we architect our microservices for the payment system?",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined"
    },
    # Complex + Un-defined
    {
        "text": "What opportunities exist in the future of sustainable energy?",
        "expected_cynefin": "complex",
        "expected_pws": "un-defined"
    },
    # Complex + Ill-defined
    {
        "text": "People seem frustrated with how healthcare data is shared between providers",
        "expected_cynefin": "complex",
        "expected_pws": "ill-defined"
    },
    # Chaotic
    {
        "text": "We have 2 weeks of runway left and our main customer just churned",
        "expected_cynefin": "chaotic",
        "expected_pws": "ill-defined"
    },
    # Boundary: Framing → Defining edge
    {
        "text": "We've done customer research but haven't validated our assumptions yet",
        "expected_cynefin": "complicated",
        "expected_pws": "ill-defined"  # Still ill-defined until validated
    },
    # Multi-domain
    {
        "text": "The technology is straightforward but the market dynamics are chaotic",
        "expected_cynefin": "complex",  # Take the more uncertain domain
        "expected_pws": "ill-defined"
    },
    # Override trigger: User states something different than detected
    {
        "text": "I know what I want to build, I just need to explore the space first",
        "expected_cynefin": "complicated",
        "expected_pws": "un-defined"  # User intent: explore
    },
]


async def run_test_cases(llm_client: Any = None) -> Dict[str, Any]:
    """Run test cases and return accuracy metrics."""
    results = []

    for case in TEST_CASES:
        classification = await classify(case["text"], llm_client=llm_client)

        cynefin_correct = classification.cynefin == case["expected_cynefin"]
        pws_correct = classification.pws == case["expected_pws"]

        results.append({
            "text": case["text"][:50] + "...",
            "expected_cynefin": case["expected_cynefin"],
            "actual_cynefin": classification.cynefin,
            "cynefin_correct": cynefin_correct,
            "expected_pws": case["expected_pws"],
            "actual_pws": classification.pws,
            "pws_correct": pws_correct,
            "both_correct": cynefin_correct and pws_correct
        })

    total = len(results)
    cynefin_accuracy = sum(r["cynefin_correct"] for r in results) / total
    pws_accuracy = sum(r["pws_correct"] for r in results) / total
    both_accuracy = sum(r["both_correct"] for r in results) / total

    return {
        "total_cases": total,
        "cynefin_accuracy": cynefin_accuracy,
        "pws_accuracy": pws_accuracy,
        "both_accuracy": both_accuracy,
        "target_accuracy": 0.8,
        "meets_target": both_accuracy >= 0.8,
        "results": results
    }
