"""
PWS Consultant Validation - Red Team Middleware Integration

Provides PWS problem-type-specific validation for the consulting stage.
Based on A2A_PRACTICAL_ARCHITECTURE.md Red Team middleware pattern.

Key principle: Red Team is a cross-cutting checkpoint, not a destination.
Validation happens at transitions and when high-stakes claims are detected.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# === PWS Problem Type Challenges ===

PWS_VALIDATION_QUESTIONS = {
    "undefined": {
        "name": "Un-Defined Problem",
        "standard": [
            "Are we exploring a real trend or chasing noise?",
            "What evidence suggests this domain is worth exploring?",
            "Who actually has this problem? (Not who 'should' have it)",
            "What would make this opportunity disappear?",
        ],
        "transition": [
            "Have we identified a specific opportunity within this domain?",
            "Is there a clear 'who' and 'what' emerging?",
        ],
        "red_flags": [
            "Vague generalizations without specific examples",
            "No mention of actual people or customers",
            "Solutions appearing before problems are defined",
        ],
    },
    "ill_defined": {
        "name": "Ill-Defined Problem",
        "standard": [
            "Is the problem framing too broad or too narrow?",
            "What assumptions are embedded in how we've framed this?",
            "Have we validated this framing with real potential customers?",
            "What would have to be true for this problem to be worth solving?",
        ],
        "transition": [
            "Can we state the problem in one clear sentence?",
            "Do we know who has this problem and how badly?",
            "Is the problem testable/measurable?",
        ],
        "red_flags": [
            "Multiple unrelated problems bundled together",
            "Problem statement that's really a solution in disguise",
            "No evidence of customer pain/frequency/willingness to pay",
        ],
    },
    "well_defined": {
        "name": "Well-Defined Problem",
        "standard": [
            "Does this solution address the root cause?",
            "What are the unintended consequences of this approach?",
            "Who are the competitors and why will we win?",
            "What's the simplest version we could build to test this?",
        ],
        "transition": [
            "Have we validated the core assumptions?",
            "Is there a clear path to market/adoption?",
            "Do we have the right team/resources?",
        ],
        "red_flags": [
            "Building for edge cases before validating the core use case",
            "Overengineering before market validation",
            "Dismissing competition too easily",
        ],
    },
    "wicked": {
        "name": "Wicked Problem",
        "standard": [
            "Are we trying to 'solve' something that can only be managed?",
            "What stakeholder perspectives are we missing?",
            "What would 'good enough' look like vs perfection?",
            "How might this intervention create new problems?",
        ],
        "transition": [
            "Have we identified manageable sub-problems?",
            "Is there a coalition of stakeholders aligned on next steps?",
        ],
        "red_flags": [
            "Treating complex system as simple cause-effect",
            "Ignoring stakeholders who will resist change",
            "Expecting permanent solutions to adaptive challenges",
        ],
    },
}


# === Validation Result ===

@dataclass
class PWSValidationResult:
    """Result of PWS-specific validation."""
    passed: bool
    challenges: List[Dict]
    red_flags_detected: List[str]
    feedback: str
    should_reclassify: bool = False
    suggested_questions: List[str] = None

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "challenges": self.challenges,
            "red_flags_detected": self.red_flags_detected,
            "feedback": self.feedback,
            "should_reclassify": self.should_reclassify,
            "suggested_questions": self.suggested_questions,
        }


# === Validation Functions ===

def detect_claims(text: str) -> List[str]:
    """
    Detect claims or assumptions in user's text that warrant validation.
    Returns list of detected claims.
    """
    claims = []

    # Strong assertion patterns
    strong_indicators = [
        "everyone", "nobody", "always", "never", "definitely",
        "obviously", "clearly", "must", "will always", "can't",
        "impossible", "certain", "guaranteed", "no way",
    ]

    # Assumption patterns
    assumption_indicators = [
        "i assume", "i think", "probably", "should be", "likely",
        "i believe", "i expect", "presumably", "my sense is",
    ]

    text_lower = text.lower()

    for indicator in strong_indicators:
        if indicator in text_lower:
            # Extract the sentence containing the claim
            sentences = text.split('.')
            for sentence in sentences:
                if indicator in sentence.lower():
                    claims.append(f"Strong claim: '{sentence.strip()}'")
                    break

    for indicator in assumption_indicators:
        if indicator in text_lower:
            sentences = text.split('.')
            for sentence in sentences:
                if indicator in sentence.lower():
                    claims.append(f"Assumption: '{sentence.strip()}'")
                    break

    return claims[:3]  # Limit to 3 most significant


def detect_red_flags(text: str, problem_type: str) -> List[str]:
    """
    Detect red flags specific to the problem type.
    """
    red_flags = []
    text_lower = text.lower()

    type_config = PWS_VALIDATION_QUESTIONS.get(problem_type, {})
    potential_flags = type_config.get("red_flags", [])

    # Simple keyword-based detection (can be enhanced with LLM)
    flag_keywords = {
        "Vague generalizations": ["everyone needs", "the market wants", "people would"],
        "No mention of actual people": ["customers will", "users would"],
        "Solutions appearing before problems": ["we should build", "the product should"],
        "Multiple unrelated problems": ["also", "another thing", "plus we need"],
        "Problem statement that's really a solution": ["we need to build", "the solution is"],
    }

    for flag in potential_flags:
        keywords = flag_keywords.get(flag, [])
        for kw in keywords:
            if kw in text_lower:
                red_flags.append(flag)
                break

    return list(set(red_flags))


async def validate_pws_response(
    user_message: str,
    assistant_response: str,
    problem_type: str,
    turn_count: int,
    context: Optional[Dict] = None
) -> PWSValidationResult:
    """
    Validate a consulting stage response using PWS-specific criteria.

    Args:
        user_message: User's latest message
        assistant_response: Larry's response
        problem_type: Current diagnosed problem type (undefined, ill_defined, etc.)
        turn_count: Number of turns in consulting stage
        context: Additional context (diagnosis, artifacts, etc.)

    Returns:
        PWSValidationResult with challenges and recommendations
    """
    challenges = []
    red_flags = []
    should_reclassify = False

    # Get problem-type-specific config
    type_config = PWS_VALIDATION_QUESTIONS.get(problem_type, PWS_VALIDATION_QUESTIONS["ill_defined"])

    # Detect claims in user message
    claims = detect_claims(user_message)
    for claim in claims:
        challenges.append({
            "type": "claim",
            "content": claim,
            "question": "What evidence supports this?",
            "severity": "minor",
        })

    # Detect red flags
    red_flags = detect_red_flags(user_message, problem_type)
    for flag in red_flags:
        challenges.append({
            "type": "red_flag",
            "content": flag,
            "question": f"This might be a concern: {flag}",
            "severity": "major",
        })

    # Periodic validation at turn milestones
    if turn_count > 0 and turn_count % 5 == 0:
        transition_questions = type_config.get("transition", [])
        for q in transition_questions[:2]:  # Add 2 transition questions
            challenges.append({
                "type": "transition_check",
                "content": q,
                "question": q,
                "severity": "info",
            })

    # Determine if validation passed
    major_issues = [c for c in challenges if c.get("severity") in ["major", "critical"]]
    passed = len(major_issues) == 0

    # Check if reclassification might be needed
    if len(red_flags) >= 2:
        should_reclassify = True

    # Build feedback
    if passed:
        if challenges:
            feedback = f"Moving forward. Minor points to consider: {len(challenges)} observations noted."
        else:
            feedback = "Validation passed. Continue exploring."
    else:
        feedback = f"Heads up: {len(major_issues)} concern(s) detected. {major_issues[0]['content'] if major_issues else ''}"

    # Suggest relevant questions from the problem type
    suggested = type_config.get("standard", [])[:2]

    return PWSValidationResult(
        passed=passed,
        challenges=challenges,
        red_flags_detected=red_flags,
        feedback=feedback,
        should_reclassify=should_reclassify,
        suggested_questions=suggested,
    )


def should_validate(
    turn_count: int,
    last_validation_turn: int,
    user_message: str,
    problem_type: str
) -> bool:
    """
    Determine if validation should run this turn.

    Returns True if:
    - It's been 5+ turns since last validation
    - User message contains strong claims or assumptions
    - Red flags are detected in the message
    """
    # Validate every 5 turns
    if turn_count - last_validation_turn >= 5:
        return True

    # Validate if claims detected
    claims = detect_claims(user_message)
    if claims:
        return True

    # Validate if red flags detected
    flags = detect_red_flags(user_message, problem_type)
    if flags:
        return True

    return False


def format_validation_message(result: PWSValidationResult) -> str:
    """
    Format validation result as a message to append to Larry's response.
    Only shown when there are notable observations.
    """
    if result.passed and not result.challenges:
        return ""  # No message needed

    parts = []

    if result.red_flags_detected:
        parts.append("\n\n---\n*🔴 Observations:*")
        for flag in result.red_flags_detected[:2]:
            parts.append(f"\n- {flag}")

    if result.challenges:
        claim_challenges = [c for c in result.challenges if c["type"] == "claim"]
        if claim_challenges:
            parts.append("\n\n*Consider:*")
            parts.append(f" {claim_challenges[0]['question']}")

    if result.should_reclassify:
        parts.append("\n\n*The problem might be evolving. Would you like to re-assess the problem type?*")

    return "".join(parts)


# === Integration with PWS Consultant ===

class PWSValidationMiddleware:
    """
    Middleware for PWS Consultant validation.

    Wraps the validation logic for easy integration with the consulting stage.
    """

    def __init__(self):
        self.validation_history: List[PWSValidationResult] = []
        self.last_validation_turn = 0

    async def check(
        self,
        user_message: str,
        assistant_response: str,
        problem_type: str,
        turn_count: int,
        context: Optional[Dict] = None,
        force: bool = False
    ) -> Optional[PWSValidationResult]:
        """
        Check if validation is needed and run it.

        Returns None if validation not needed, otherwise returns result.
        """
        if not force and not should_validate(
            turn_count,
            self.last_validation_turn,
            user_message,
            problem_type
        ):
            return None

        result = await validate_pws_response(
            user_message,
            assistant_response,
            problem_type,
            turn_count,
            context
        )

        self.validation_history.append(result)
        self.last_validation_turn = turn_count

        return result

    def get_validation_summary(self) -> Dict:
        """Get summary of validation history."""
        if not self.validation_history:
            return {"total": 0, "passed": 0, "failed": 0}

        passed = sum(1 for r in self.validation_history if r.passed)
        return {
            "total": len(self.validation_history),
            "passed": passed,
            "failed": len(self.validation_history) - passed,
            "red_flags_total": sum(len(r.red_flags_detected) for r in self.validation_history),
        }
