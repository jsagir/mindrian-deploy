"""
Risk Tier System for Mindrian AI Governance

Classifies AI features by impact level and defines oversight requirements.

Usage:
    from governance.risk_tiers import get_risk_tier, requires_human_oversight, RISK_CONFIG

    tier = get_risk_tier("redteam")  # Returns 3
    needs_review = requires_human_oversight("redteam", "challenge_assumption")  # Returns True
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import IntEnum


class RiskTier(IntEnum):
    """Risk tier levels"""
    INTERNAL = 0      # Internal/testing only
    LOW_IMPACT = 1    # General chat, exploration
    BUSINESS = 2      # Business methodology, workshops
    HIGH_STAKES = 3   # Decisions with consequences


@dataclass
class TierConfig:
    """Configuration for a risk tier"""
    level: RiskTier
    name: str
    description: str
    human_oversight: str  # "none", "async", "optional", "required"
    audit_required: bool
    rate_limit: Optional[int]  # requests per hour, None = unlimited
    allowed_actions: List[str]
    forbidden_actions: List[str]


# === TIER DEFINITIONS ===

TIER_CONFIGS: Dict[RiskTier, TierConfig] = {
    RiskTier.INTERNAL: TierConfig(
        level=RiskTier.INTERNAL,
        name="Internal/Testing",
        description="Development and testing only, not user-facing",
        human_oversight="none",
        audit_required=False,
        rate_limit=None,
        allowed_actions=["*"],
        forbidden_actions=[]
    ),
    RiskTier.LOW_IMPACT: TierConfig(
        level=RiskTier.LOW_IMPACT,
        name="Low Impact",
        description="General exploration, no significant decisions",
        human_oversight="async",  # Feedback buttons only
        audit_required=False,
        rate_limit=100,  # per hour
        allowed_actions=[
            "chat",
            "explain_methodology",
            "recommend_framework",
            "basic_research",
            "answer_questions"
        ],
        forbidden_actions=[
            "make_decisions",
            "financial_advice",
            "legal_advice",
            "medical_advice"
        ]
    ),
    RiskTier.BUSINESS: TierConfig(
        level=RiskTier.BUSINESS,
        name="Business Methodology",
        description="Workshop facilitation, methodology application",
        human_oversight="optional",  # User can request review
        audit_required=True,
        rate_limit=50,  # per hour
        allowed_actions=[
            "facilitate_workshop",
            "apply_framework",
            "deep_research",
            "generate_insights",
            "synthesize_findings",
            "create_visualizations"
        ],
        forbidden_actions=[
            "make_business_decisions",
            "investment_recommendations",
            "definitive_predictions",
            "replace_customer_research"
        ]
    ),
    RiskTier.HIGH_STAKES: TierConfig(
        level=RiskTier.HIGH_STAKES,
        name="High Stakes",
        description="Decisions with potential consequences",
        human_oversight="required",  # Must acknowledge/confirm
        audit_required=True,
        rate_limit=20,  # per hour
        allowed_actions=[
            "score_quality",
            "challenge_assumptions",
            "validate_evidence",
            "grade_work",
            "assess_opportunities"
        ],
        forbidden_actions=[
            "final_decisions",
            "investment_advice",
            "replace_professional_advice",
            "automated_actions",
            "permanent_judgments"
        ]
    )
}


# === BOT TO TIER MAPPING ===

BOT_RISK_TIERS: Dict[str, RiskTier] = {
    # Tier 0 - Internal
    # (none currently in production)

    # Tier 1 - Low Impact
    "lawrence": RiskTier.LOW_IMPACT,
    "domain": RiskTier.LOW_IMPACT,

    # Tier 2 - Business Methodology
    "larry_playground": RiskTier.BUSINESS,
    "tta": RiskTier.BUSINESS,
    "jtbd": RiskTier.BUSINESS,
    "scurve": RiskTier.BUSINESS,
    "bono": RiskTier.BUSINESS,
    "knowns": RiskTier.BUSINESS,
    "scenario": RiskTier.BUSINESS,

    # Tier 3 - High Stakes
    "redteam": RiskTier.HIGH_STAKES,
    "ackoff": RiskTier.HIGH_STAKES,
    "grading": RiskTier.HIGH_STAKES,
    "pws_investment": RiskTier.HIGH_STAKES,
}


# === ACTION RISK MAPPING ===

HIGH_RISK_ACTIONS = {
    "grade_problem_definition",
    "score_opportunity",
    "validate_dikw",
    "challenge_core_assumption",
    "investment_assessment",
    "final_synthesis",
}

MEDIUM_RISK_ACTIONS = {
    "deep_research",
    "multi_agent_analysis",
    "extract_insights",
    "generate_recommendations",
}

LOW_RISK_ACTIONS = {
    "chat",
    "explain",
    "list_frameworks",
    "basic_search",
}


# === FUNCTIONS ===

def get_risk_tier(bot_id: str) -> RiskTier:
    """Get the risk tier for a bot"""
    return BOT_RISK_TIERS.get(bot_id, RiskTier.BUSINESS)  # Default to BUSINESS


def get_tier_config(tier: RiskTier) -> TierConfig:
    """Get configuration for a tier"""
    return TIER_CONFIGS[tier]


def get_bot_config(bot_id: str) -> TierConfig:
    """Get tier configuration for a bot"""
    tier = get_risk_tier(bot_id)
    return get_tier_config(tier)


def requires_human_oversight(bot_id: str, action: Optional[str] = None) -> bool:
    """
    Check if an action requires human oversight.

    Args:
        bot_id: The bot performing the action
        action: Specific action being taken (optional)

    Returns:
        True if human oversight is required
    """
    config = get_bot_config(bot_id)

    # Always required for high-stakes tier
    if config.human_oversight == "required":
        return True

    # Check if specific action is high-risk
    if action and action in HIGH_RISK_ACTIONS:
        return True

    return False


def requires_audit(bot_id: str) -> bool:
    """Check if bot actions should be audited"""
    config = get_bot_config(bot_id)
    return config.audit_required


def is_action_allowed(bot_id: str, action: str) -> bool:
    """
    Check if an action is allowed for a bot.

    Args:
        bot_id: The bot attempting the action
        action: The action being attempted

    Returns:
        True if action is allowed
    """
    config = get_bot_config(bot_id)

    # Check forbidden first
    if action in config.forbidden_actions:
        return False

    # Wildcard allows all (for internal tier)
    if "*" in config.allowed_actions:
        return True

    # Check allowed list
    return action in config.allowed_actions


def get_rate_limit(bot_id: str) -> Optional[int]:
    """Get rate limit (requests per hour) for a bot"""
    config = get_bot_config(bot_id)
    return config.rate_limit


def get_disclaimer(bot_id: str) -> Optional[str]:
    """Get required disclaimer for bot outputs"""
    tier = get_risk_tier(bot_id)

    if tier == RiskTier.HIGH_STAKES:
        if bot_id == "pws_investment":
            return "⚠️ This analysis is not financial advice. Consult qualified professionals before making investment decisions."
        elif bot_id == "grading":
            return "📊 This grade is based on PWS methodology criteria and should be validated against your specific context."
        elif bot_id == "redteam":
            return "🎯 These challenges are designed to strengthen your thinking, not discourage action."
        elif bot_id == "ackoff":
            return "🔍 Validation requires evidence from primary sources. AI synthesis should be verified."

    return None


def validate_bot_action(bot_id: str, action: str) -> Dict[str, Any]:
    """
    Validate if a bot can perform an action.

    Returns:
        {
            "allowed": bool,
            "requires_oversight": bool,
            "requires_audit": bool,
            "disclaimer": Optional[str],
            "reason": Optional[str]
        }
    """
    allowed = is_action_allowed(bot_id, action)

    return {
        "allowed": allowed,
        "requires_oversight": requires_human_oversight(bot_id, action),
        "requires_audit": requires_audit(bot_id),
        "disclaimer": get_disclaimer(bot_id),
        "reason": None if allowed else f"Action '{action}' not allowed for {bot_id}"
    }


# === EXPORTS ===

RISK_CONFIG = {
    "tiers": TIER_CONFIGS,
    "bot_tiers": BOT_RISK_TIERS,
    "high_risk_actions": HIGH_RISK_ACTIONS,
    "medium_risk_actions": MEDIUM_RISK_ACTIONS,
    "low_risk_actions": LOW_RISK_ACTIONS,
}


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    # Example: Check risk tier for redteam
    print(f"Redteam tier: {get_risk_tier('redteam')}")
    print(f"Requires oversight: {requires_human_oversight('redteam')}")
    print(f"Disclaimer: {get_disclaimer('redteam')}")

    # Validate an action
    result = validate_bot_action("grading", "grade_problem_definition")
    print(f"Validation: {result}")
