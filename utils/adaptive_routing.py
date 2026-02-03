"""
Adaptive Routing for Recursive Intelligence

Uses learned effectiveness scores to improve agent routing:
- Suggests better agents for problem types
- Warns when current agent has low effectiveness
- Learns from user reactions over time

Phase 4B of Recursive Intelligence implementation.
"""

import asyncio
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class RoutingSuggestion:
    """Suggestion for better routing."""
    suggested_agent: str
    reason: str
    effectiveness_score: float
    current_agent_score: Optional[float] = None
    confidence: str = "medium"  # low, medium, high


# In-memory cache for effectiveness scores
_effectiveness_cache: Dict[Tuple[str, str], float] = {}
_cache_loaded: bool = False


async def load_effectiveness_cache() -> bool:
    """
    Load effectiveness scores from Supabase into memory.

    Call this at startup or periodically to refresh.
    """
    global _effectiveness_cache, _cache_loaded

    try:
        from utils.storage import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            return False

        response = await asyncio.to_thread(
            lambda: supabase.table("agent_effectiveness").select("*").execute()
        )

        _effectiveness_cache.clear()
        for row in (response.data or []):
            key = (row["agent"], row["problem_type"])
            _effectiveness_cache[key] = row["effectiveness"]

        _cache_loaded = True
        print(f"[AdaptiveRouting] Loaded {len(_effectiveness_cache)} effectiveness scores")
        return True

    except Exception as e:
        print(f"[AdaptiveRouting] Cache load failed: {e}")
        return False


def get_effectiveness(agent: str, problem_type: str) -> Optional[float]:
    """
    Get effectiveness score for agent-problem combination.

    Returns:
        Score from 0.0 (bad) to 1.0 (good), or None if unknown
    """
    if not _cache_loaded:
        # Attempt sync load (not ideal but fallback)
        try:
            asyncio.get_event_loop().run_until_complete(load_effectiveness_cache())
        except RuntimeError:
            pass  # No event loop, skip

    return _effectiveness_cache.get((agent, problem_type))


def get_best_agents_for_problem(
    problem_type: str,
    exclude_agents: Optional[List[str]] = None,
    min_score: float = 0.6
) -> List[Tuple[str, float]]:
    """
    Get ranked list of best agents for a problem type.

    Args:
        problem_type: Type of problem
        exclude_agents: Agents to exclude (e.g., current agent)
        min_score: Minimum effectiveness score

    Returns:
        List of (agent, score) tuples, sorted by score descending
    """
    exclude = set(exclude_agents or [])

    matches = []
    for (agent, ptype), score in _effectiveness_cache.items():
        if ptype == problem_type and agent not in exclude and score >= min_score:
            matches.append((agent, score))

    return sorted(matches, key=lambda x: x[1], reverse=True)


def should_suggest_switch(
    current_agent: str,
    problem_type: Optional[str],
    min_improvement: float = 0.15
) -> Optional[RoutingSuggestion]:
    """
    Check if we should suggest switching to a better agent.

    Args:
        current_agent: Current agent ID
        problem_type: Detected problem type
        min_improvement: Minimum score improvement to suggest

    Returns:
        RoutingSuggestion if a better agent exists, None otherwise
    """
    if not problem_type:
        return None

    current_score = get_effectiveness(current_agent, problem_type)

    # Get better alternatives
    better_agents = get_best_agents_for_problem(
        problem_type,
        exclude_agents=[current_agent],
        min_score=(current_score or 0.5) + min_improvement
    )

    if not better_agents:
        return None

    best_agent, best_score = better_agents[0]

    # Only suggest if meaningful improvement
    improvement = best_score - (current_score or 0.5)
    if improvement < min_improvement:
        return None

    # Build reason
    if current_score and current_score < 0.4:
        reason = f"Users often struggle with {problem_type} problems in this mode"
    else:
        reason = f"Better match for {problem_type} problems"

    confidence = "high" if improvement > 0.25 else "medium"

    return RoutingSuggestion(
        suggested_agent=best_agent,
        reason=reason,
        effectiveness_score=best_score,
        current_agent_score=current_score,
        confidence=confidence
    )


def get_routing_hint(
    current_agent: str,
    problem_type: Optional[str],
    user_signal: Optional[str] = None
) -> Optional[str]:
    """
    Get a hint for the router based on learned patterns.

    This integrates with existing routing logic to improve decisions.

    Args:
        current_agent: Current agent ID
        problem_type: Detected problem type
        user_signal: Recent user signal (positive, negative, redirect)

    Returns:
        Optional hint string for the router
    """
    # Check for negative signal with low effectiveness
    if user_signal == "negative" and problem_type:
        score = get_effectiveness(current_agent, problem_type)
        if score and score < 0.4:
            better = get_best_agents_for_problem(problem_type, [current_agent])
            if better:
                return f"suggest_switch:{better[0][0]}"

    # Check for struggling pattern
    if user_signal == "negative":
        suggestion = should_suggest_switch(current_agent, problem_type)
        if suggestion and suggestion.confidence == "high":
            return f"offer_alternative:{suggestion.suggested_agent}"

    return None


# ============================================
# Agent Descriptions for User-Facing Suggestions
# ============================================

AGENT_DESCRIPTIONS = {
    "lawrence": "General PWS thinking partner",
    "larry_playground": "Full research toolkit",
    "tta": "Trending to the Absurd - future extrapolation",
    "jtbd": "Jobs to Be Done - customer progress",
    "scurve": "S-Curve Analysis - technology adoption",
    "redteam": "Red Team - adversarial analysis",
    "ackoff": "Ackoff's Pyramid - data to wisdom",
    "scenario": "Scenario Planning - multiple futures",
    "validation": "Triple Validation - opportunity testing",
    "bono": "Six Thinking Hats - structured perspectives",
    "domain": "Domain Explorer - cross-field research",
    "knowns": "Known/Unknown Matrix - uncertainty mapping",
}


def format_suggestion_for_user(suggestion: RoutingSuggestion) -> str:
    """Format a routing suggestion for display to user."""
    agent_name = AGENT_DESCRIPTIONS.get(
        suggestion.suggested_agent,
        suggestion.suggested_agent
    )

    if suggestion.current_agent_score and suggestion.current_agent_score < 0.4:
        return (
            f"💡 **Suggestion:** Users working on similar problems often find "
            f"**{agent_name}** more helpful. Would you like to try it?"
        )
    else:
        return (
            f"💡 Based on patterns from other sessions, **{agent_name}** "
            f"might be a good fit for this type of problem."
        )


# ============================================
# Integration with Existing Router
# ============================================

def enhance_router_scores(
    base_scores: Dict[str, float],
    problem_type: Optional[str],
    boost_factor: float = 0.2
) -> Dict[str, float]:
    """
    Enhance existing router scores with learned effectiveness.

    This allows the adaptive routing to work WITH existing routing logic
    rather than replacing it.

    Args:
        base_scores: Original router scores {agent: score}
        problem_type: Detected problem type
        boost_factor: How much to weight learned effectiveness

    Returns:
        Enhanced scores
    """
    if not problem_type:
        return base_scores

    enhanced = base_scores.copy()

    for agent in enhanced:
        effectiveness = get_effectiveness(agent, problem_type)
        if effectiveness is not None:
            # Blend: (1-boost)*base + boost*effectiveness
            enhanced[agent] = (
                (1 - boost_factor) * enhanced[agent] +
                boost_factor * effectiveness
            )

    return enhanced


# ============================================
# Testing
# ============================================

if __name__ == "__main__":
    # Test with mock data
    _effectiveness_cache = {
        ("tta", "innovation"): 0.85,
        ("jtbd", "product"): 0.82,
        ("validation", "validation"): 0.90,
        ("redteam", "strategy"): 0.78,
        ("lawrence", "innovation"): 0.55,
        ("lawrence", "product"): 0.60,
    }
    _cache_loaded = True

    print("Adaptive Routing Test")
    print("=" * 60)

    # Test best agents
    print("\nBest agents for 'innovation' problems:")
    for agent, score in get_best_agents_for_problem("innovation"):
        print(f"  {agent}: {score:.2f}")

    # Test switch suggestion
    print("\nShould suggest switch from Lawrence on innovation?")
    suggestion = should_suggest_switch("lawrence", "innovation")
    if suggestion:
        print(f"  Yes: {suggestion.suggested_agent} ({suggestion.effectiveness_score:.2f})")
        print(f"  Reason: {suggestion.reason}")
        print(f"\n  User message: {format_suggestion_for_user(suggestion)}")
    else:
        print("  No suggestion")

    # Test router enhancement
    print("\nRouter score enhancement:")
    base = {"tta": 0.5, "jtbd": 0.5, "lawrence": 0.8}
    enhanced = enhance_router_scores(base, "innovation")
    for agent in base:
        print(f"  {agent}: {base[agent]:.2f} → {enhanced[agent]:.2f}")
