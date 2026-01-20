# Mindrian System Prompts
from .larry_core import LARRY_RAG_SYSTEM_PROMPT
from .tta_workshop import TTA_WORKSHOP_PROMPT
from .jtbd_workshop import JTBD_WORKSHOP_PROMPT
from .scurve_workshop import SCURVE_WORKSHOP_PROMPT
from .redteam import REDTEAM_PROMPT

__all__ = [
    "LARRY_RAG_SYSTEM_PROMPT",
    "TTA_WORKSHOP_PROMPT",
    "JTBD_WORKSHOP_PROMPT",
    "SCURVE_WORKSHOP_PROMPT",
    "REDTEAM_PROMPT"
]
