# Mindrian System Prompts
from .larry_core import LARRY_RAG_SYSTEM_PROMPT
from .tta_workshop import TTA_WORKSHOP_PROMPT
from .jtbd_workshop import JTBD_WORKSHOP_PROMPT
from .scurve_workshop import SCURVE_WORKSHOP_PROMPT
from .redteam import REDTEAM_PROMPT
from .ackoff_workshop import ACKOFF_WORKSHOP_PROMPT
from .bono_master import BONO_MASTER_PROMPT
from .known_unknowns import KNOWN_UNKNOWNS_PROMPT
from .domain_explorer import DOMAIN_EXPLORER_PROMPT
from .pws_investment import PWS_INVESTMENT_PROMPT
from .scenario_analysis import SCENARIO_ANALYSIS_PROMPT

__all__ = [
    "LARRY_RAG_SYSTEM_PROMPT",
    "TTA_WORKSHOP_PROMPT",
    "JTBD_WORKSHOP_PROMPT",
    "SCURVE_WORKSHOP_PROMPT",
    "REDTEAM_PROMPT",
    "ACKOFF_WORKSHOP_PROMPT",
    "BONO_MASTER_PROMPT",
    "KNOWN_UNKNOWNS_PROMPT",
    "DOMAIN_EXPLORER_PROMPT",
    "PWS_INVESTMENT_PROMPT",
    "SCENARIO_ANALYSIS_PROMPT",
]
