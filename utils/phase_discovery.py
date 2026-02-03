"""
Phase Discovery - Auto-discover phase definitions from prompt modules.

This eliminates shotgun surgery when adding new phased bots.
Instead of updating 5 places, you add PHASES to the prompt file and you're done.

Usage:
    from utils.phase_discovery import get_phases_for_bot, get_tracker_criteria_for_bot

    # Returns phases list or None if bot has no phases
    phases = get_phases_for_bot("nested_hierarchies")

    # Returns tracker criteria dict or None
    criteria = get_tracker_criteria_for_bot("nested_hierarchies")
"""

import importlib
from typing import Dict, List, Optional, Any
import copy


# Bot ID → prompt module mapping
BOT_TO_PROMPT_MODULE = {
    "tta": "prompts.tta_workshop",
    "jtbd": "prompts.jtbd_workshop",
    "scurve": "prompts.scurve_workshop",
    "ackoff": "prompts.ackoff_workshop",
    "redteam": "prompts.redteam",
    "bono": "prompts.bono_master",
    "knowns": "prompts.known_unknowns",
    "nested_hierarchies": "prompts.nested_hierarchies",
    "domain": "prompts.domain_explorer",
    "investment": "prompts.pws_investment",
    "scenario": "prompts.scenario_analysis",
    "beautiful_question": "prompts.beautiful_question",
    # Non-phased bots (Lawrence, Larry Playground) don't need entries
}

# Cache for loaded modules
_module_cache: Dict[str, Any] = {}


def _get_prompt_module(bot_id: str) -> Optional[Any]:
    """Load and cache prompt module for a bot."""
    if bot_id in _module_cache:
        return _module_cache[bot_id]

    module_name = BOT_TO_PROMPT_MODULE.get(bot_id)
    if not module_name:
        return None

    try:
        module = importlib.import_module(module_name)
        _module_cache[bot_id] = module
        return module
    except ImportError as e:
        print(f"[phase_discovery] Could not load module {module_name}: {e}")
        return None


def get_phases_for_bot(bot_id: str) -> Optional[List[Dict[str, str]]]:
    """
    Get phase definitions for a bot from its prompt module.

    Returns:
        List of phase dicts [{"name": "...", "status": "..."}] or None
    """
    module = _get_prompt_module(bot_id)
    if not module:
        return None

    # Look for PHASES constant in the module
    phases = getattr(module, "PHASES", None)
    if phases and isinstance(phases, list):
        # Return a deep copy so callers can modify status without affecting source
        return copy.deepcopy(phases)

    return None


def get_tracker_criteria_for_bot(bot_id: str) -> Optional[Dict[str, Any]]:
    """
    Get smart_phase_tracker criteria for a bot from its prompt module.

    Returns:
        Dict with "phases" key containing phase criteria, or None
    """
    module = _get_prompt_module(bot_id)
    if not module:
        return None

    # Look for PHASE_TRACKER_CRITERIA constant
    criteria = getattr(module, "PHASE_TRACKER_CRITERIA", None)
    if criteria and isinstance(criteria, dict):
        return copy.deepcopy(criteria)

    return None


def bot_has_phases(bot_id: str) -> bool:
    """Check if a bot has self-describing phases."""
    return get_phases_for_bot(bot_id) is not None


def get_all_phased_bots() -> List[str]:
    """Return list of bot IDs that have self-describing phases."""
    phased = []
    for bot_id in BOT_TO_PROMPT_MODULE:
        if bot_has_phases(bot_id):
            phased.append(bot_id)
    return phased


# =============================================================================
# Migration helper: Compare self-describing phases vs legacy WORKSHOP_PHASES
# =============================================================================

def check_phase_consistency(bot_id: str, legacy_phases: List[Dict]) -> Dict[str, Any]:
    """
    Compare self-describing phases with legacy WORKSHOP_PHASES dict.
    Useful during incremental migration.

    Returns:
        {
            "consistent": bool,
            "self_describing": [...] or None,
            "legacy": [...],
            "differences": [...] if inconsistent
        }
    """
    self_phases = get_phases_for_bot(bot_id)

    if self_phases is None:
        return {
            "consistent": True,  # No self-describing phases, legacy is source of truth
            "self_describing": None,
            "legacy": legacy_phases,
            "differences": []
        }

    # Compare phase names
    self_names = [p["name"] for p in self_phases]
    legacy_names = [p["name"] for p in legacy_phases]

    if self_names == legacy_names:
        return {
            "consistent": True,
            "self_describing": self_phases,
            "legacy": legacy_phases,
            "differences": []
        }

    # Find differences
    differences = []
    for i, (s, l) in enumerate(zip(self_names, legacy_names)):
        if s != l:
            differences.append(f"Phase {i}: self='{s}' vs legacy='{l}'")

    if len(self_names) != len(legacy_names):
        differences.append(f"Phase count: self={len(self_names)} vs legacy={len(legacy_names)}")

    return {
        "consistent": False,
        "self_describing": self_phases,
        "legacy": legacy_phases,
        "differences": differences
    }
