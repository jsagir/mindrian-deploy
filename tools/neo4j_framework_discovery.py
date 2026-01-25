"""
Neo4j-Powered Framework Discovery for PWS Research Planning

Integrates Neo4j knowledge graph to:
1. Discover relevant PWS frameworks based on challenge analysis
2. Build research orchestration plans with framework-specific queries
3. Create mini-agent specifications for deep research

Based on the Mini-Agent Factory System for Framework Orchestration.
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# Neo4j connection (using MCP tools indirectly)
# These functions are called by the main application which has MCP access


@dataclass
class FrameworkRecommendation:
    """A recommended framework with context for research."""
    name: str
    category: str  # questioning, innovation, problem_solving, etc.
    relevance_score: float  # 0-1
    related_concepts: List[str]
    suggested_queries: List[str]
    mini_agent_role: str  # What role this framework plays in research

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "category": self.category,
            "relevance_score": self.relevance_score,
            "related_concepts": self.related_concepts,
            "suggested_queries": self.suggested_queries,
            "mini_agent_role": self.mini_agent_role
        }


@dataclass
class ResearchOrchestrationPlan:
    """
    Framework-driven research orchestration plan.
    Organizes frameworks into parallel and sequential phases.
    """
    challenge_summary: str
    phase_1_parallel: List[FrameworkRecommendation]  # Can run simultaneously
    phase_2_sequential: List[FrameworkRecommendation]  # Depends on Phase 1
    phase_3_synthesis: List[FrameworkRecommendation]  # Final integration
    total_frameworks: int
    orchestration_notes: str

    def to_dict(self) -> Dict:
        return {
            "challenge_summary": self.challenge_summary,
            "phase_1_parallel": [f.to_dict() for f in self.phase_1_parallel],
            "phase_2_sequential": [f.to_dict() for f in self.phase_2_sequential],
            "phase_3_synthesis": [f.to_dict() for f in self.phase_3_synthesis],
            "total_frameworks": self.total_frameworks,
            "orchestration_notes": self.orchestration_notes
        }


# ═══════════════════════════════════════════════════════════════════
# CYPHER QUERIES FOR FRAMEWORK DISCOVERY
# ═══════════════════════════════════════════════════════════════════

DISCOVER_FRAMEWORKS_BY_KEYWORDS_QUERY = """
// Find frameworks matching challenge keywords
WITH $keywords AS keywords
UNWIND keywords AS keyword
MATCH (f:Framework)
WHERE toLower(f.name) CONTAINS toLower(keyword)
WITH f, count(keyword) as matches
ORDER BY matches DESC
RETURN DISTINCT f.name AS name, matches
LIMIT $limit
"""

DISCOVER_FRAMEWORKS_BY_CATEGORY_QUERY = """
// Find frameworks by category (innovation, problem_solving, questioning, etc.)
MATCH (f:Framework)
WHERE toLower(f.name) CONTAINS $category
RETURN f.name AS name
LIMIT $limit
"""

GET_FRAMEWORK_RELATIONSHIPS_QUERY = """
// Get framework with its related concepts
MATCH (f:Framework {name: $framework_name})-[r]->(related)
RETURN f.name AS framework,
       type(r) AS relationship,
       labels(related)[0] AS related_type,
       related.name AS related_name
LIMIT 20
"""

DISCOVER_RELATED_FRAMEWORKS_QUERY = """
// Find frameworks connected through shared concepts
MATCH (f1:Framework {name: $framework_name})-[r1]->(concept)<-[r2]-(f2:Framework)
WHERE f1 <> f2
RETURN DISTINCT f2.name AS related_framework,
       count(concept) AS shared_concepts,
       collect(concept.name)[0..3] AS shared_items
ORDER BY shared_concepts DESC
LIMIT 10
"""


# ═══════════════════════════════════════════════════════════════════
# FRAMEWORK CATEGORIZATION
# ═══════════════════════════════════════════════════════════════════

FRAMEWORK_CATEGORIES = {
    "questioning": {
        "keywords": ["question", "inquiry", "why", "what if", "how"],
        "role": "Challenge assumptions and generate research questions",
        "examples": ["Beautiful Question Framework", "Framework for Question and Answer Clarification"]
    },
    "problem_solving": {
        "keywords": ["problem", "solution", "solving", "wicked", "defined"],
        "role": "Structure and decompose the core problem",
        "examples": ["Wicked Problem Detection Framework", "Well-Defined Problem Framework"]
    },
    "innovation": {
        "keywords": ["innovation", "disrupt", "creative", "breakthrough"],
        "role": "Identify innovation opportunities and patterns",
        "examples": ["Open Innovation", "Sustaining vs Disruptive Innovation"]
    },
    "systems": {
        "keywords": ["system", "complexity", "dynamics", "feedback"],
        "role": "Analyze systemic relationships and feedback loops",
        "examples": ["Systems Thinking", "Cynefin Framework"]
    },
    "trends": {
        "keywords": ["trend", "future", "forecast", "megatrend", "scenario"],
        "role": "Project trends and explore future scenarios",
        "examples": ["Scenario Analysis Framework", "Trending to the Absurd"]
    },
    "validation": {
        "keywords": ["validate", "test", "evidence", "camera", "proof"],
        "role": "Validate hypotheses with observable evidence",
        "examples": ["PWS Triple Validation Compass", "Hypothesis-Driven Problem Solving"]
    },
    "synthesis": {
        "keywords": ["pyramid", "minto", "structure", "mece", "synthesis"],
        "role": "Synthesize findings into structured arguments",
        "examples": ["The Pyramid Principle", "MECE"]
    }
}


def categorize_framework(framework_name: str) -> str:
    """Categorize a framework based on its name."""
    name_lower = framework_name.lower()

    for category, config in FRAMEWORK_CATEGORIES.items():
        for keyword in config["keywords"]:
            if keyword in name_lower:
                return category

    return "general"


def get_category_role(category: str) -> str:
    """Get the research role for a category."""
    return FRAMEWORK_CATEGORIES.get(category, {}).get("role", "Support general analysis")


# ═══════════════════════════════════════════════════════════════════
# FRAMEWORK DISCOVERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def extract_challenge_keywords(challenge_text: str) -> List[str]:
    """Extract keywords from challenge text for framework matching."""
    # Common words to filter out
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "and", "or", "but", "not", "this", "that", "these", "those",
        "it", "its", "we", "our", "they", "their", "how", "what",
        "when", "where", "why", "which", "who", "can", "will", "would"
    }

    # Extract words and filter
    words = challenge_text.lower().split()
    keywords = []

    for word in words:
        # Clean word
        word = ''.join(c for c in word if c.isalnum())
        if word and word not in stop_words and len(word) > 3:
            keywords.append(word)

    # Also add specific PWS-related terms if present in challenge
    pws_terms = {
        "innovation": ["innovation", "innovate", "disrupt", "breakthrough"],
        "problem": ["problem", "challenge", "issue", "pain", "struggle"],
        "opportunity": ["opportunity", "potential", "market", "growth"],
        "strategy": ["strategy", "strategic", "competitive", "advantage"],
        "customer": ["customer", "user", "consumer", "audience", "stakeholder"],
        "technology": ["technology", "tech", "digital", "ai", "automation"],
        "trend": ["trend", "future", "emerging", "shift", "change"]
    }

    for category, terms in pws_terms.items():
        for term in terms:
            if term in challenge_text.lower() and category not in keywords:
                keywords.append(category)

    return list(set(keywords))[:15]  # Max 15 keywords


def build_framework_recommendations(
    framework_names: List[str],
    challenge_keywords: List[str]
) -> List[FrameworkRecommendation]:
    """Build framework recommendations with suggested queries."""
    recommendations = []

    for name in framework_names:
        category = categorize_framework(name)
        role = get_category_role(category)

        # Calculate relevance score based on keyword matches
        name_lower = name.lower()
        matches = sum(1 for kw in challenge_keywords if kw in name_lower)
        relevance = min(1.0, matches / max(1, len(challenge_keywords) / 3))

        # Generate suggested search queries
        suggested_queries = generate_framework_queries(name, category, challenge_keywords)

        recommendations.append(FrameworkRecommendation(
            name=name,
            category=category,
            relevance_score=relevance,
            related_concepts=[],  # Can be populated from Neo4j
            suggested_queries=suggested_queries,
            mini_agent_role=role
        ))

    # Sort by relevance
    recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
    return recommendations


def generate_framework_queries(
    framework_name: str,
    category: str,
    challenge_keywords: List[str]
) -> List[str]:
    """Generate search queries specific to this framework application."""
    queries = []

    # Base query using framework name
    framework_clean = framework_name.replace("Framework", "").strip()

    # Category-specific query templates
    if category == "questioning":
        queries.extend([
            f"{framework_clean} questioning methodology examples",
            f"how to apply {framework_clean} innovation discovery"
        ])
    elif category == "problem_solving":
        queries.extend([
            f"{framework_clean} problem decomposition technique",
            f"{framework_clean} applied to business challenges"
        ])
    elif category == "innovation":
        queries.extend([
            f"{framework_clean} innovation patterns examples",
            f"{framework_clean} startup application case study"
        ])
    elif category == "systems":
        queries.extend([
            f"{framework_clean} systems analysis method",
            f"{framework_clean} complexity mapping"
        ])
    elif category == "trends":
        queries.extend([
            f"{framework_clean} trend analysis 2025 2026",
            f"{framework_clean} future scenario building"
        ])
    elif category == "validation":
        queries.extend([
            f"{framework_clean} evidence validation method",
            f"{framework_clean} hypothesis testing business"
        ])
    elif category == "synthesis":
        queries.extend([
            f"{framework_clean} structured thinking example",
            f"{framework_clean} argument hierarchy building"
        ])
    else:
        queries.extend([
            f"{framework_clean} methodology application",
            f"{framework_clean} practical examples"
        ])

    # Add challenge-specific queries
    if challenge_keywords:
        kw_string = " ".join(challenge_keywords[:3])
        queries.append(f"{framework_clean} {kw_string}")

    return queries[:3]  # Max 3 queries per framework


# ═══════════════════════════════════════════════════════════════════
# RESEARCH ORCHESTRATION PLAN BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_orchestration_plan(
    challenge_text: str,
    frameworks: List[FrameworkRecommendation]
) -> ResearchOrchestrationPlan:
    """
    Build a research orchestration plan organizing frameworks into phases.

    Phase 1 (Parallel): Problem decomposition + Trend analysis
    Phase 2 (Sequential): Innovation exploration + Validation
    Phase 3 (Synthesis): Pyramid structuring + Final recommendations
    """
    phase_1 = []  # Problem decomposition, questioning, trends
    phase_2 = []  # Innovation, systems, deeper analysis
    phase_3 = []  # Synthesis, validation

    for fw in frameworks:
        if fw.category in ["questioning", "problem_solving", "trends"]:
            phase_1.append(fw)
        elif fw.category in ["innovation", "systems", "general"]:
            phase_2.append(fw)
        elif fw.category in ["synthesis", "validation"]:
            phase_3.append(fw)
        else:
            # Default to phase 2
            phase_2.append(fw)

    # Ensure at least one framework per phase (from available frameworks)
    if not phase_1 and frameworks:
        phase_1.append(frameworks[0])
    if not phase_3 and len(frameworks) > 1:
        phase_3.append(frameworks[-1])

    # Build orchestration notes
    notes = f"""Orchestration Plan for: {challenge_text[:100]}...

**Phase 1 - Parallel Exploration** ({len(phase_1)} frameworks)
These frameworks can run simultaneously to decompose the problem:
{chr(10).join([f'- {fw.name}: {fw.mini_agent_role}' for fw in phase_1])}

**Phase 2 - Sequential Deep Dive** ({len(phase_2)} frameworks)
Build on Phase 1 findings to explore innovations and systems:
{chr(10).join([f'- {fw.name}: {fw.mini_agent_role}' for fw in phase_2])}

**Phase 3 - Synthesis** ({len(phase_3)} frameworks)
Synthesize all findings into structured recommendations:
{chr(10).join([f'- {fw.name}: {fw.mini_agent_role}' for fw in phase_3])}

**Total Queries Planned:** {sum(len(fw.suggested_queries) for fw in frameworks)}
"""

    return ResearchOrchestrationPlan(
        challenge_summary=challenge_text[:200],
        phase_1_parallel=phase_1,
        phase_2_sequential=phase_2,
        phase_3_synthesis=phase_3,
        total_frameworks=len(frameworks),
        orchestration_notes=notes
    )


# ═══════════════════════════════════════════════════════════════════
# MINI-AGENT PROMPT GENERATOR
# ═══════════════════════════════════════════════════════════════════

def generate_mini_agent_prompt(
    framework: FrameworkRecommendation,
    challenge_text: str,
    phase: int
) -> str:
    """Generate a mini-agent system prompt for this framework."""

    input_context = "Base challenge description only" if phase == 1 else f"Results from Phase {phase - 1}"

    prompt = f"""### Framework Agent: {framework.name}

**SYSTEM PROMPT:**
You are a {framework.category.replace('_', ' ').title()} Agent specializing in {framework.name}.

**INPUT CONTEXT:** {input_context}

**YOUR MISSION:**
{framework.mini_agent_role} for the challenge: "{challenge_text[:100]}..."

**EXECUTION STEPS:**
1. **Think** about how {framework.name} applies to this challenge
2. **Search** for supporting evidence and examples:
   {chr(10).join([f'   - "{q}"' for q in framework.suggested_queries])}
3. **Analyze** findings through the lens of {framework.name}
4. **Document** key insights and recommendations

**OUTPUT REQUIRED:**
- Key findings from {framework.name} perspective
- Specific recommendations for the challenge
- Questions raised for further investigation
- Evidence and sources supporting conclusions

---"""

    return prompt


def generate_full_orchestration_prompts(
    plan: ResearchOrchestrationPlan,
    challenge_text: str
) -> str:
    """Generate all mini-agent prompts for the orchestration plan."""

    prompts = [f"# Mini Agent System Prompts for Challenge\n\n**Challenge:** {challenge_text[:200]}...\n"]

    # Phase 1
    prompts.append("\n## PHASE 1 - PARALLEL FRAMEWORKS\n")
    for fw in plan.phase_1_parallel:
        prompts.append(generate_mini_agent_prompt(fw, challenge_text, 1))

    # Phase 2
    prompts.append("\n## PHASE 2 - SEQUENTIAL FRAMEWORKS\n")
    for fw in plan.phase_2_sequential:
        prompts.append(generate_mini_agent_prompt(fw, challenge_text, 2))

    # Phase 3
    prompts.append("\n## PHASE 3 - SYNTHESIS\n")
    for fw in plan.phase_3_synthesis:
        prompts.append(generate_mini_agent_prompt(fw, challenge_text, 3))

    # Orchestration notes
    prompts.append(f"\n## ORCHESTRATION NOTES\n\n{plan.orchestration_notes}")

    return "\n".join(prompts)


# ═══════════════════════════════════════════════════════════════════
# HARDCODED PWS FRAMEWORKS (fallback when Neo4j unavailable)
# ═══════════════════════════════════════════════════════════════════

PWS_CORE_FRAMEWORKS = [
    # Questioning
    "Beautiful Question Framework",
    "Framework for Question and Answer Clarification",

    # Problem Solving
    "Wicked Problem Detection Framework",
    "Well-Defined Problem Framework",
    "Problem Definition Transformation Framework",

    # Innovation
    "Sustaining vs Disruptive Innovation",
    "Four Lenses of Innovation",
    "Reverse Salient Analysis",

    # Systems
    "Cynefin Framework",
    "Systems Thinking",
    "Knowns and Unknowns Matrix Framework",

    # Trends
    "Scenario Analysis Framework",
    "Trending to the Absurd",
    "Macro Trends",

    # Validation
    "PWS Triple Validation Compass",
    "Hypothesis-Driven Problem Solving",

    # Synthesis
    "The Pyramid Principle",
    "MECE (Mutually Exclusive, Collectively Exhaustive)",
    "Six Thinking Hats"
]


def get_default_pws_frameworks(challenge_text: str, limit: int = 8) -> List[FrameworkRecommendation]:
    """Get default PWS frameworks when Neo4j is unavailable."""
    keywords = extract_challenge_keywords(challenge_text)

    # Filter frameworks based on challenge keywords
    relevant = []
    for name in PWS_CORE_FRAMEWORKS:
        category = categorize_framework(name)
        name_lower = name.lower()

        # Score based on keyword matches
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > 0 or len(relevant) < limit:
            relevant.append((name, score, category))

    # Sort by score and take top ones
    relevant.sort(key=lambda x: x[1], reverse=True)
    relevant = relevant[:limit]

    return build_framework_recommendations(
        [name for name, _, _ in relevant],
        keywords
    )
