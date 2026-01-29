"""
Scenario Analysis - Enhanced Phase Definitions
===============================================

Each phase includes:
- name: Display title
- description: What this phase is about
- instructions: Clear steps for the user
- deliverables: What "done" looks like
- extraction_patterns: Regex patterns for LangExtract validation
- neo4j_queries: LazyGraph queries for context enrichment
- completion_threshold: Minimum score to auto-advance
- prompt: Opening question for the phase
"""

SCENARIO_PHASES = {
    "introduction": {
        "index": 0,
        "name": "Introduction",
        "description": "Understand scenario planning and escape presentism.",
        "instructions": [
            "Share your domain or industry to explore",
            "Define your focal strategic question (what decision are you facing?)",
            "Set your time horizon (typically 7-15 years out)"
        ],
        "deliverables": {
            "domain": "Industry or domain to explore",
            "focal_question": "Strategic question driving the analysis",
            "time_horizon": "Target year or timeframe"
        },
        "extraction_patterns": {
            "domain": r"(?:domain|industry|sector|field|area|business|market)[\s:]+([A-Za-z\s]{3,50})",
            "focal_question": r"(?:question|decision|wondering|should\s+(?:I|we)|trying\s+to)[\s:]+([^.?]+\??)",
            "time_horizon": r"(\d{4})|(\d+)\s*years?"
        },
        "neo4j_queries": {
            "context": """
                MATCH (f:Framework)
                WHERE f.name CONTAINS 'Scenario' OR f.name CONTAINS 'Future'
                OPTIONAL MATCH (f)-[:HAS_COMPONENT]->(c)
                RETURN f.name AS framework, collect(c.name)[0..3] AS components
                LIMIT 3
            """,
            "case_study": """
                MATCH (cs:CaseStudy)
                WHERE cs.methodology CONTAINS 'scenario' OR cs.name CONTAINS 'Shell'
                RETURN cs.name AS name, cs.summary AS summary
                LIMIT 2
            """
        },
        "completion_threshold": 0.6,
        "prompt": "What domain do you want to explore, and what strategic decision is driving this?"
    },

    "driving_forces": {
        "index": 1,
        "name": "Domain & Driving Forces",
        "description": "Map all forces that could reshape your domain using STEEP analysis.",
        "instructions": [
            "Brainstorm SOCIAL forces (demographics, culture, lifestyle shifts)",
            "Brainstorm TECHNOLOGICAL forces (innovation, automation, AI, platforms)",
            "Brainstorm ECONOMIC forces (markets, trade, employment, inflation)",
            "Brainstorm ENVIRONMENTAL forces (climate, resources, sustainability)",
            "Brainstorm POLITICAL forces (regulation, geopolitics, policy changes)"
        ],
        "deliverables": {
            "social_forces": "List of social/demographic forces",
            "technological_forces": "List of technology forces",
            "economic_forces": "List of economic forces",
            "environmental_forces": "List of environmental forces",
            "political_forces": "List of political forces"
        },
        "extraction_patterns": {
            "social_forces": r"(?:social|demographic|cultural|lifestyle)[\s:]+([^\n.]{10,200})",
            "technological_forces": r"(?:tech|technology|technological|digital|AI|automation)[\s:]+([^\n.]{10,200})",
            "economic_forces": r"(?:economic|market|financial|trade|employment)[\s:]+([^\n.]{10,200})",
            "environmental_forces": r"(?:environment|climate|sustainable|green|resource)[\s:]+([^\n.]{10,200})",
            "political_forces": r"(?:political|regulation|policy|government|geopolitical)[\s:]+([^\n.]{10,200})"
        },
        "neo4j_queries": {
            "steep": """
                MATCH (f:Framework)
                WHERE f.name CONTAINS 'STEEP' OR f.name CONTAINS 'PESTLE'
                OPTIONAL MATCH (f)-[:HAS_COMPONENT]->(c)
                RETURN f.name AS framework, collect(c.name) AS components
                LIMIT 1
            """,
            "trends": """
                MATCH (t:Trend)
                RETURN t.name AS trend, t.category AS category, t.description AS description
                LIMIT 8
            """
        },
        "completion_threshold": 0.5,
        "prompt": "Let's brainstorm driving forces. Start with SOCIAL forces - what social or demographic shifts could impact your domain?"
    },

    "uncertainty_assessment": {
        "index": 2,
        "name": "Uncertainty Assessment",
        "description": "Separate predetermined elements from genuine uncertainties.",
        "instructions": [
            "Review each driving force you identified",
            "Mark as PREDETERMINED (will definitely happen) or UNCERTAIN (could go either way)",
            "For uncertainties, rate by: Impact (1-5) and Unpredictability (1-5)",
            "Rank your top 5 uncertainties by Impact x Unpredictability"
        ],
        "deliverables": {
            "predetermined_forces": "List of forces that will definitely happen",
            "uncertain_forces": "List of genuinely uncertain forces",
            "top_uncertainties": "Top 5 uncertainties ranked by impact"
        },
        "extraction_patterns": {
            "predetermined_forces": r"(?:predetermined|certain|will\s+happen|definitely|inevitable|given)[\s:]+([^\n]{10,300})",
            "uncertain_forces": r"(?:uncertain|unpredictable|could\s+go|unknown|unsure|maybe)[\s:]+([^\n]{10,300})",
            "top_uncertainties": r"(?:top|critical|key|most\s+important)\s+(?:uncertaint|factor)[\s:]+([^\n]{10,200})"
        },
        "neo4j_queries": {
            "uncertainty_examples": """
                MATCH (c:Concept)
                WHERE c.name CONTAINS 'uncertainty' OR c.name CONTAINS 'risk'
                RETURN c.name AS concept, c.description AS description
                LIMIT 3
            """
        },
        "completion_threshold": 0.6,
        "prompt": "Looking at your driving forces, let's categorize them. Which ones are PREDETERMINED (will happen regardless) vs truly UNCERTAIN?"
    },

    "scenario_matrix": {
        "index": 3,
        "name": "Scenario Matrix (2x2)",
        "description": "Select two independent axes and build four scenario quadrants.",
        "instructions": [
            "Select your 2 most CRITICAL uncertainties from the ranked list",
            "INDEPENDENCE CHECK: If Axis A moves high, does it predict Axis B? If yes, choose different axes!",
            "Define the extreme endpoints for each axis (e.g., 'High Regulation' vs 'Low Regulation')",
            "Name each of the 4 quadrants with memorable, evocative titles"
        ],
        "deliverables": {
            "axis_1": "First uncertainty axis with high/low endpoints",
            "axis_2": "Second uncertainty axis with high/low endpoints",
            "independence_verified": "Confirmation that axes are independent",
            "quadrant_1": "Name for quadrant 1 (Axis1-High, Axis2-High)",
            "quadrant_2": "Name for quadrant 2 (Axis1-High, Axis2-Low)",
            "quadrant_3": "Name for quadrant 3 (Axis1-Low, Axis2-High)",
            "quadrant_4": "Name for quadrant 4 (Axis1-Low, Axis2-Low)"
        },
        "extraction_patterns": {
            "axis_1": r"(?:axis|dimension|first|1st)\s*(?:1|one)?[\s:]+([^\n]{5,100})",
            "axis_2": r"(?:axis|dimension|second|2nd)\s*(?:2|two)?[\s:]+([^\n]{5,100})",
            "quadrant_1": r"(?:quadrant|scenario)\s*(?:1|one|first)[\s:\"']+([^\n\"']{3,50})",
            "quadrant_2": r"(?:quadrant|scenario)\s*(?:2|two|second)[\s:\"']+([^\n\"']{3,50})",
            "quadrant_3": r"(?:quadrant|scenario)\s*(?:3|three|third)[\s:\"']+([^\n\"']{3,50})",
            "quadrant_4": r"(?:quadrant|scenario)\s*(?:4|four|fourth)[\s:\"']+([^\n\"']{3,50})"
        },
        "validation_rules": {
            "independence_test": "If Axis A moves to its high extreme, would that make Axis B more likely to move in a particular direction? If yes, they are CORRELATED and you must choose different axes."
        },
        "neo4j_queries": {
            "matrix_examples": """
                MATCH (cs:CaseStudy)
                WHERE cs.name CONTAINS 'Shell' OR cs.methodology CONTAINS 'scenario'
                RETURN cs.name AS case_study, cs.summary AS summary
                LIMIT 2
            """
        },
        "completion_threshold": 0.7,
        "prompt": "From your top uncertainties, which TWO are most critical AND independent? Remember: if one moves, it should NOT predict the other."
    },

    "scenario_narratives": {
        "index": 4,
        "name": "Scenario Narratives",
        "description": "Develop rich, internally consistent stories for each quadrant.",
        "instructions": [
            "For EACH of your 4 scenarios, describe:",
            "  - How did we get here? (the pathway from present to this future)",
            "  - What does daily life look like in this world?",
            "  - Who are the WINNERS and who are the LOSERS?",
            "  - What NEW problems have emerged that don't exist today?",
            "  - What current problems have DISAPPEARED?"
        ],
        "deliverables": {
            "narrative_1": "Full narrative for Scenario 1",
            "narrative_2": "Full narrative for Scenario 2",
            "narrative_3": "Full narrative for Scenario 3",
            "narrative_4": "Full narrative for Scenario 4"
        },
        "extraction_patterns": {
            "narrative_1": r"(?:scenario|quadrant|future)\s*(?:1|one)[\s:]+(.{50,}?)(?=(?:scenario|quadrant)\s*(?:2|two)|$)",
            "narrative_2": r"(?:scenario|quadrant|future)\s*(?:2|two)[\s:]+(.{50,}?)(?=(?:scenario|quadrant)\s*(?:3|three)|$)",
            "narrative_3": r"(?:scenario|quadrant|future)\s*(?:3|three)[\s:]+(.{50,}?)(?=(?:scenario|quadrant)\s*(?:4|four)|$)",
            "narrative_4": r"(?:scenario|quadrant|future)\s*(?:4|four)[\s:]+(.{50,}?)(?=$)"
        },
        "neo4j_queries": {
            "narrative_elements": """
                MATCH (c:Concept)
                WHERE c.name CONTAINS 'narrative' OR c.name CONTAINS 'story'
                RETURN c.name AS concept, c.description AS description
                LIMIT 3
            """
        },
        "completion_threshold": 0.5,
        "prompt": "Let's develop your first scenario. It's your target year. Walk me through: How did we get to this future?"
    },

    "synthesis": {
        "index": 5,
        "name": "Synthesis & Implications",
        "description": "Extract strategic insights and identify problems worth solving.",
        "instructions": [
            "Identify ROBUST PROBLEMS - problems that appear in ALL or MOST scenarios",
            "Identify CONTINGENT OPPORTUNITIES - opportunities unique to specific scenarios",
            "STRESS-TEST your current strategy against all 4 scenarios",
            "Find your FAILURE SCENARIO - in which scenario does your current approach break?"
        ],
        "deliverables": {
            "robust_problems": "Problems that appear across multiple futures",
            "contingent_opportunities": "Opportunities unique to specific scenarios",
            "strategy_test": "How current strategy performs in each scenario",
            "failure_scenario": "Which scenario breaks the current approach"
        },
        "extraction_patterns": {
            "robust_problems": r"(?:robust|all\s+scenarios|every|across|common)[\s:]+([^\n]{10,200})",
            "contingent_opportunities": r"(?:contingent|specific|only\s+in|unique)[\s:]+([^\n]{10,200})",
            "failure_scenario": r"(?:fail|break|doesn't\s+work|vulnerable)[\s:]+([^\n]{10,200})"
        },
        "neo4j_queries": {
            "pws_connection": """
                MATCH (c:Concept)
                WHERE c.name CONTAINS 'problem' OR c.name CONTAINS 'opportunity'
                RETURN c.name AS concept, c.description AS description
                LIMIT 5
            """
        },
        "completion_threshold": 0.6,
        "prompt": "Looking across all 4 scenarios: What problems appear in MULTIPLE futures? Those are your most robust opportunities."
    }
}

# Phase key lookup by index
PHASE_KEYS = list(SCENARIO_PHASES.keys())

def get_phase_by_index(index: int) -> dict:
    """Get phase config by index."""
    if 0 <= index < len(PHASE_KEYS):
        return SCENARIO_PHASES[PHASE_KEYS[index]]
    return {}

def get_phase_key_by_index(index: int) -> str:
    """Get phase key by index."""
    if 0 <= index < len(PHASE_KEYS):
        return PHASE_KEYS[index]
    return ""

__all__ = [
    "SCENARIO_PHASES",
    "PHASE_KEYS",
    "get_phase_by_index",
    "get_phase_key_by_index"
]
