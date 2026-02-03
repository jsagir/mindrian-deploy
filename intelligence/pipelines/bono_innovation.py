"""
BONO-Innovation Framework LangGraph Pipeline
=============================================
Edward de Bono's Six Thinking Hats + Lateral Thinking + Domain Personas.

Pipeline Flow:
1. Problem Classification (2D: Definition Clarity × System Complexity)
2. Domain Discovery (Extract relevant domains/subdomains)
3. Persona Generation (Create expert personas per domain)
4. Six Hats Exploration (Each persona contributes per hat)
5. Lateral Thinking (Random Entry, Provocation, Reversal)
6. Persona Discussion (Cross-domain synthesis)
7. Action Planning (Implementation roadmap)

Features:
- Parallel research per thinking hat
- Dynamic persona creation from problem context
- Multi-perspective synthesis via persona dialogue
- Neo4j integration for domain knowledge
"""

import asyncio
import random
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class ProblemClassification(BaseModel):
    """2D Problem Classification result."""
    definition_clarity: Literal["UDP", "IDP", "WDP"] = Field(
        description="UDP=Undefined, IDP=Ill-Defined, WDP=Well-Defined"
    )
    system_complexity: Literal["Simple", "Complex", "Wicked"] = Field(
        description="Simple=linear, Complex=emergent, Wicked=no stopping rule"
    )
    context_type: Literal["innovation", "strategic", "crisis", "product"] = Field(
        description="Session context determining hat sequence"
    )
    problem_statement: str = Field(description="Refined problem formulation")
    key_assumptions: List[str] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)


class DomainPersona(BaseModel):
    """Expert persona generated from domain."""
    name: str = Field(description="Persona name (e.g., 'Dr. Sarah Chen - Healthcare AI')")
    domain: str = Field(description="Primary domain")
    subdomain: str = Field(description="Specific subdomain")
    expertise: List[str] = Field(description="Areas of expertise")
    perspective: str = Field(description="Unique viewpoint this persona brings")
    biases: List[str] = Field(description="Known biases to be aware of")
    icon: str = Field(default="👤")


class HatContribution(BaseModel):
    """Single thinking hat contribution."""
    hat: Literal["white", "red", "black", "yellow", "green", "blue"]
    persona_name: str
    insights: List[str]
    key_point: str
    evidence: Optional[str] = None
    emotion: Optional[str] = None  # For red hat


class LateralInsight(BaseModel):
    """Result from lateral thinking technique."""
    technique: Literal["random_entry", "provocation", "reversal", "wishful", "escape"]
    trigger: str  # The word, provocation, or reversal used
    insight: str
    practical_application: Optional[str] = None
    generated_by: str  # Persona name


class PersonaDialogue(BaseModel):
    """Single turn in persona discussion."""
    speaker: str
    perspective: str
    statement: str
    responds_to: Optional[str] = None
    synthesis_point: Optional[str] = None


class ActionItem(BaseModel):
    """Implementation action item."""
    action: str
    owner_persona: str
    timeframe: Literal["quick_win", "medium_term", "long_term"]
    dependencies: List[str] = Field(default_factory=list)
    success_metric: str


class BONOSessionReport(BaseModel):
    """Final session output."""
    problem_classification: ProblemClassification
    personas: List[DomainPersona]
    hat_sequence: List[str]
    hat_contributions: Dict[str, List[HatContribution]]
    lateral_insights: List[LateralInsight]
    persona_synthesis: List[PersonaDialogue]
    action_plan: List[ActionItem]
    breakthrough_ideas: List[str]
    key_decisions: List[str]


# =============================================================================
# STATE DEFINITION
# =============================================================================

class BONOState(TypedDict):
    """State for BONO Innovation pipeline."""
    # Input
    user_input: str
    session_id: str
    context_type: Optional[str]  # innovation/strategic/crisis/product

    # Phase 1: Problem Classification
    problem_classification: Optional[Dict[str, Any]]
    discovered_domains: List[Dict[str, Any]]

    # Phase 2: Persona Generation
    personas: List[Dict[str, Any]]

    # Phase 3: Six Hats Exploration
    hat_sequence: List[str]
    current_hat: Optional[str]
    hat_contributions: Dict[str, List[Dict[str, Any]]]

    # Phase 4: Lateral Thinking
    lateral_insights: List[Dict[str, Any]]
    random_words: List[str]
    provocations: List[str]

    # Phase 5: Persona Discussion
    persona_dialogue: List[Dict[str, Any]]
    synthesis_points: List[str]

    # Phase 6: Action Planning
    action_items: List[Dict[str, Any]]
    breakthrough_ideas: List[str]

    # Research context
    web_research: Dict[str, List[str]]
    neo4j_context: List[str]

    # Output
    session_report: Optional[Dict[str, Any]]
    error: Optional[str]


# =============================================================================
# CONSTANTS
# =============================================================================

# Hat sequences based on context type
HAT_SEQUENCES = {
    "innovation": ["blue", "white", "red", "green", "yellow", "black", "blue"],
    "strategic": ["blue", "white", "black", "yellow", "green", "red", "blue"],
    "crisis": ["blue", "red", "white", "black", "yellow", "green", "blue"],
    "product": ["blue", "white", "green", "yellow", "black", "red", "blue"],
}

HAT_ICONS = {
    "white": "🤍",
    "red": "❤️",
    "black": "🖤",
    "yellow": "💛",
    "green": "💚",
    "blue": "💙",
}

HAT_FOCUS = {
    "white": "Facts, data, information - neutral and objective",
    "red": "Emotions, feelings, intuitions - no justification needed",
    "black": "Critical thinking, risks, problems - cautious and careful",
    "yellow": "Positive thinking, benefits, opportunities - optimistic",
    "green": "Creative thinking, alternatives, new ideas - provocative",
    "blue": "Process control, thinking about thinking - meta-cognitive",
}

# Random words for lateral thinking
RANDOM_WORD_POOL = [
    "elephant", "microscope", "jazz", "volcano", "blockchain",
    "origami", "lighthouse", "butterfly", "glacier", "symphony",
    "kaleidoscope", "bamboo", "thunder", "compass", "mosaic",
    "whirlpool", "constellation", "honeycomb", "avalanche", "pendulum",
]

# Provocation templates
PROVOCATION_TEMPLATES = [
    "Po: The problem solves itself",
    "Po: We do exactly the opposite",
    "Po: The constraint becomes the solution",
    "Po: Users become the providers",
    "Po: Time runs backwards",
    "Po: The solution already exists, we just can't see it",
    "Po: The worst approach is actually the best",
    "Po: We eliminate the problem entirely",
]


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

async def classify_problem(state: BONOState) -> BONOState:
    """
    Phase 1: Classify the problem using 2D matrix.
    Also discovers relevant domains and subdomains.
    """
    from google import genai

    user_input = state["user_input"]
    context_type = state.get("context_type", "innovation")

    # Build classification prompt
    classification_prompt = f"""Analyze this problem/opportunity and provide a structured classification:

PROBLEM/OPPORTUNITY:
{user_input}

Provide your analysis in this exact JSON format:
{{
    "definition_clarity": "UDP" or "IDP" or "WDP",
    "system_complexity": "Simple" or "Complex" or "Wicked",
    "context_type": "{context_type}",
    "problem_statement": "refined 1-2 sentence problem statement",
    "key_assumptions": ["assumption 1", "assumption 2", ...],
    "stakeholders": ["stakeholder 1", "stakeholder 2", ...],
    "domains": [
        {{"domain": "primary domain", "subdomain": "specific area", "relevance": "why relevant"}},
        {{"domain": "second domain", "subdomain": "specific area", "relevance": "why relevant"}},
        ...
    ]
}}

Definition Clarity:
- UDP (Undefined): Unclear what the problem even is
- IDP (Ill-Defined): Partially clear, multiple interpretations possible
- WDP (Well-Defined): Clear problem statement and success metrics

System Complexity:
- Simple: Straightforward cause-effect, repeatable solutions
- Complex: Multiple interacting variables, emergent properties
- Wicked: No definitive formulation, unique, no stopping rule

Identify 3-5 relevant domains and subdomains for expert persona creation.
"""

    try:
        client = genai.Client()
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=classification_prompt,
            config={"response_mime_type": "application/json"}
        )

        import json
        result = json.loads(response.text)

        state["problem_classification"] = {
            "definition_clarity": result.get("definition_clarity", "IDP"),
            "system_complexity": result.get("system_complexity", "Complex"),
            "context_type": result.get("context_type", context_type),
            "problem_statement": result.get("problem_statement", user_input),
            "key_assumptions": result.get("key_assumptions", []),
            "stakeholders": result.get("stakeholders", []),
        }

        state["discovered_domains"] = result.get("domains", [])

        # Set hat sequence based on context
        ctx = state["problem_classification"]["context_type"]
        state["hat_sequence"] = HAT_SEQUENCES.get(ctx, HAT_SEQUENCES["innovation"])

        print(f"[BONO] Classified: {state['problem_classification']['definition_clarity']}-{state['problem_classification']['system_complexity']}")
        print(f"[BONO] Discovered {len(state['discovered_domains'])} domains")

    except Exception as e:
        state["error"] = f"Classification failed: {e}"
        state["problem_classification"] = {
            "definition_clarity": "IDP",
            "system_complexity": "Complex",
            "context_type": context_type,
            "problem_statement": user_input,
            "key_assumptions": [],
            "stakeholders": [],
        }
        state["discovered_domains"] = []
        state["hat_sequence"] = HAT_SEQUENCES["innovation"]

    return state


async def generate_personas(state: BONOState) -> BONOState:
    """
    Phase 2: Generate expert personas from discovered domains.
    Each persona has unique expertise and perspective.
    """
    from google import genai

    domains = state["discovered_domains"]
    problem = state["problem_classification"]["problem_statement"]

    if not domains:
        # Generate default personas if no domains discovered
        domains = [
            {"domain": "Innovation", "subdomain": "Strategy", "relevance": "General innovation perspective"},
            {"domain": "Technology", "subdomain": "Implementation", "relevance": "Technical feasibility"},
            {"domain": "Business", "subdomain": "Operations", "relevance": "Business viability"},
        ]

    persona_prompt = f"""Create expert personas for a Six Thinking Hats session on this problem:

PROBLEM: {problem}

DOMAINS TO COVER:
{domains}

For each domain, create a persona with this JSON format:
{{
    "personas": [
        {{
            "name": "Full Name - Title",
            "domain": "primary domain",
            "subdomain": "specific subdomain",
            "expertise": ["area 1", "area 2", "area 3"],
            "perspective": "unique viewpoint this persona brings",
            "biases": ["known bias 1", "bias 2"],
            "icon": "relevant emoji"
        }},
        ...
    ]
}}

Create {len(domains)} distinct personas with diverse perspectives.
Make names realistic and memorable.
Each persona should have genuine expertise relevant to the problem.
"""

    try:
        client = genai.Client()
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=persona_prompt,
            config={"response_mime_type": "application/json"}
        )

        import json
        result = json.loads(response.text)
        state["personas"] = result.get("personas", [])

        print(f"[BONO] Generated {len(state['personas'])} personas")
        for p in state["personas"]:
            print(f"  - {p.get('icon', '👤')} {p.get('name')}: {p.get('domain')}/{p.get('subdomain')}")

    except Exception as e:
        print(f"[BONO] Persona generation error: {e}")
        # Create fallback personas
        state["personas"] = [
            {
                "name": "Dr. Alex Chen - Innovation Strategist",
                "domain": "Innovation",
                "subdomain": "Strategy",
                "expertise": ["breakthrough thinking", "trend analysis", "opportunity mapping"],
                "perspective": "Sees patterns across industries",
                "biases": ["optimism bias", "technology solutionism"],
                "icon": "🔬"
            },
            {
                "name": "Maria Santos - Operations Expert",
                "domain": "Business",
                "subdomain": "Operations",
                "expertise": ["process optimization", "resource allocation", "risk management"],
                "perspective": "Focuses on practical implementation",
                "biases": ["status quo bias", "cost focus"],
                "icon": "📊"
            },
            {
                "name": "James Wright - User Experience Lead",
                "domain": "Design",
                "subdomain": "Human Factors",
                "expertise": ["user research", "behavior design", "accessibility"],
                "perspective": "Advocates for end-user needs",
                "biases": ["user-centric tunnel vision"],
                "icon": "👥"
            },
        ]

    return state


async def gather_research(state: BONOState) -> BONOState:
    """
    Parallel research gathering for White Hat thinking.
    Uses Mindrian's actual tool stack:
    - Tavily search for web research
    - GraphRAG Lite for Neo4j knowledge
    - PWS Brain for FileSearch RAG
    - ArXiv for academic research
    """
    problem = state["problem_classification"]["problem_statement"]
    domains = [d.get("domain", "") for d in state["discovered_domains"]]

    research_results = {
        "facts": [],
        "statistics": [],
        "trends": [],
        "case_studies": [],
        "frameworks": [],
        "academic": [],
    }

    # 1. Tavily Web Search - facts and statistics
    try:
        from tools.tavily_search import get_search_context, research_trend

        # General facts search
        facts_result = get_search_context(
            query=f"{problem} statistics data research facts",
            max_results=5,
            max_tokens=3000
        )
        if facts_result:
            research_results["facts"].append(facts_result)

        # Trend research for each domain
        for domain in domains[:2]:
            trend_result = research_trend(f"{domain} {problem}")
            if trend_result and trend_result.get("success"):
                research_results["trends"].append(trend_result.get("context", ""))

    except Exception as e:
        print(f"[BONO] Tavily search error: {e}")

    # 2. GraphRAG Lite - Neo4j knowledge graph
    try:
        from tools.graphrag_lite import enrich_for_bot, get_framework_context

        # Get framework context
        framework_context = get_framework_context(problem, limit=5)
        if framework_context:
            research_results["frameworks"].append(framework_context)

        # Enrich with Larry's knowledge for each domain
        for domain in domains[:3]:
            neo4j_hint = enrich_for_bot(
                message=f"{domain}: {problem}",
                turn_count=1,
                bot_id="bono"
            )
            if neo4j_hint:
                state["neo4j_context"].append(neo4j_hint)

    except ImportError:
        print(f"[BONO] GraphRAG not available")
    except Exception as e:
        print(f"[BONO] Neo4j query error: {e}")

    # 3. PWS Brain - FileSearch RAG for PWS methodology
    try:
        from tools.pws_brain import search_pws_knowledge, search_frameworks

        # Search for relevant PWS concepts
        pws_result = search_pws_knowledge(problem, max_results=3)
        if pws_result:
            research_results["case_studies"].extend(pws_result)

        # Search for applicable frameworks
        fw_result = search_frameworks(problem)
        if fw_result:
            research_results["frameworks"].append(fw_result)

    except ImportError:
        print(f"[BONO] PWS Brain not available")
    except Exception as e:
        print(f"[BONO] FileSearch error: {e}")

    # 4. ArXiv - academic research for complex problems
    if state["problem_classification"].get("system_complexity") in ["Complex", "Wicked"]:
        try:
            from tools.arxiv_search import search_arxiv

            arxiv_result = search_arxiv(
                query=problem,
                max_results=3
            )
            if arxiv_result and arxiv_result.get("papers"):
                for paper in arxiv_result["papers"][:3]:
                    research_results["academic"].append({
                        "title": paper.get("title"),
                        "summary": paper.get("summary", "")[:500],
                        "url": paper.get("url")
                    })

        except ImportError:
            print(f"[BONO] ArXiv search not available")
        except Exception as e:
            print(f"[BONO] ArXiv search error: {e}")

    state["web_research"] = research_results
    print(f"[BONO] Research gathered: {sum(len(v) if isinstance(v, list) else 1 for v in research_results.values())} items")
    return state


async def run_six_hats(state: BONOState) -> BONOState:
    """
    Phase 3: Run Six Thinking Hats sequence.
    Each persona contributes to each hat.
    Uses Mindrian's research_six_hats for targeted research per hat.
    """
    from google import genai

    hat_sequence = state["hat_sequence"]
    personas = state["personas"]
    problem = state["problem_classification"]["problem_statement"]
    research = state["web_research"]

    # Pre-fetch hat-specific research using Mindrian's tool
    hat_research = {}
    try:
        from tools.tavily_search import research_six_hats

        for hat in ["white", "black", "yellow", "green"]:
            hat_result = research_six_hats(problem, hat)
            if hat_result and hat_result.get("success"):
                hat_research[hat] = hat_result.get("context", "")
    except ImportError:
        print("[BONO] research_six_hats not available")
    except Exception as e:
        print(f"[BONO] Hat research error: {e}")

    state["hat_contributions"] = {}

    for hat in hat_sequence:
        state["current_hat"] = hat
        hat_contributions = []

        # Get hat-specific research context
        hat_context = hat_research.get(hat, "")

        # Each persona contributes to this hat
        for persona in personas:
            # Build research context for this hat
            research_context = ""
            if hat == "white":
                research_context = f"RESEARCH CONTEXT:\n{hat_context}\n{str(research.get('facts', [])[:2])}"
            elif hat == "black":
                research_context = f"RISK RESEARCH:\n{hat_context}"
            elif hat == "yellow":
                research_context = f"OPPORTUNITY RESEARCH:\n{hat_context}"
            elif hat == "green":
                research_context = f"INNOVATION RESEARCH:\n{hat_context}\n{str(research.get('academic', [])[:2])}"

            contribution_prompt = f"""You are {persona['name']}, an expert in {persona['domain']}/{persona['subdomain']}.

You are participating in a Six Thinking Hats session.
Current hat: {HAT_ICONS[hat]} {hat.upper()} HAT
Focus: {HAT_FOCUS[hat]}

PROBLEM: {problem}

Your expertise: {', '.join(persona.get('expertise', []))}
Your perspective: {persona.get('perspective', 'General expert view')}

{research_context}

Provide your {hat.upper()} HAT contribution as JSON:
{{
    "key_point": "your main insight (1 sentence)",
    "insights": ["insight 1", "insight 2", "insight 3"],
    "evidence": "supporting evidence if applicable (for white/black/yellow)",
    "emotion": "feeling word (for red hat only)"
}}

Stay strictly in {hat.upper()} HAT mode.
{"Focus on FACTS and DATA only." if hat == "white" else ""}
{"Express GUT FEELINGS without justification." if hat == "red" else ""}
{"Focus on RISKS and PROBLEMS." if hat == "black" else ""}
{"Focus on BENEFITS and OPPORTUNITIES." if hat == "yellow" else ""}
{"Generate CREATIVE ALTERNATIVES and NEW IDEAS." if hat == "green" else ""}
{"Summarize and SYNTHESIZE the discussion." if hat == "blue" else ""}
"""

            try:
                client = genai.Client()
                response = await client.aio.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contribution_prompt,
                    config={"response_mime_type": "application/json"}
                )

                import json
                contribution = json.loads(response.text)
                contribution["hat"] = hat
                contribution["persona_name"] = persona["name"]
                hat_contributions.append(contribution)

            except Exception as e:
                print(f"[BONO] Hat contribution error ({hat}, {persona['name']}): {e}")
                hat_contributions.append({
                    "hat": hat,
                    "persona_name": persona["name"],
                    "key_point": f"[Error generating {hat} hat contribution]",
                    "insights": [],
                })

        state["hat_contributions"][hat] = hat_contributions
        print(f"[BONO] {HAT_ICONS[hat]} {hat.upper()} HAT: {len(hat_contributions)} contributions")

    return state


async def apply_lateral_thinking(state: BONOState) -> BONOState:
    """
    Phase 4: Apply lateral thinking techniques.
    Random Entry, Provocation, Reversal, Wishful Thinking.
    """
    from google import genai

    problem = state["problem_classification"]["problem_statement"]
    personas = state["personas"]

    # Select random words
    random_words = random.sample(RANDOM_WORD_POOL, 3)
    state["random_words"] = random_words

    # Select provocations
    provocations = random.sample(PROVOCATION_TEMPLATES, 3)
    state["provocations"] = provocations

    lateral_insights = []

    # Random Entry
    for word in random_words:
        persona = random.choice(personas)

        random_prompt = f"""You are {persona['name']}.
Use RANDOM ENTRY lateral thinking technique.

PROBLEM: {problem}
RANDOM WORD: {word}

Connect this random word to the problem to generate a creative insight.
How does "{word}" relate to or inspire a solution for the problem?

Respond as JSON:
{{
    "trigger": "{word}",
    "insight": "creative connection or solution inspired by the word",
    "practical_application": "how this could actually be applied"
}}
"""

        try:
            client = genai.Client()
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=random_prompt,
                config={"response_mime_type": "application/json"}
            )

            import json
            insight = json.loads(response.text)
            insight["technique"] = "random_entry"
            insight["generated_by"] = persona["name"]
            lateral_insights.append(insight)

        except Exception as e:
            print(f"[BONO] Random entry error: {e}")

    # Provocations
    for provocation in provocations:
        persona = random.choice(personas)

        provocation_prompt = f"""You are {persona['name']}.
Use PROVOCATION (Po) lateral thinking technique.

PROBLEM: {problem}
PROVOCATION: {provocation}

Take this deliberately unreasonable statement and extract a useful concept or principle from it.
What new perspective or solution does this provocation reveal?

Respond as JSON:
{{
    "trigger": "{provocation}",
    "insight": "concept or principle extracted from the provocation",
    "practical_application": "realistic application of this concept"
}}
"""

        try:
            client = genai.Client()
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=provocation_prompt,
                config={"response_mime_type": "application/json"}
            )

            import json
            insight = json.loads(response.text)
            insight["technique"] = "provocation"
            insight["generated_by"] = persona["name"]
            lateral_insights.append(insight)

        except Exception as e:
            print(f"[BONO] Provocation error: {e}")

    # Reversal
    reversal_prompt = f"""Apply REVERSAL lateral thinking to this problem:

PROBLEM: {problem}

Reverse the problem statement, process, or stakeholder roles.
What new perspective emerges?

Respond as JSON:
{{
    "trigger": "the reversal you applied",
    "insight": "new perspective from the reversal",
    "practical_application": "how to use this reversed thinking"
}}
"""

    try:
        client = genai.Client()
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=reversal_prompt,
            config={"response_mime_type": "application/json"}
        )

        import json
        insight = json.loads(response.text)
        insight["technique"] = "reversal"
        insight["generated_by"] = "Blue Hat Facilitator"
        lateral_insights.append(insight)

    except Exception as e:
        print(f"[BONO] Reversal error: {e}")

    state["lateral_insights"] = lateral_insights
    print(f"[BONO] Generated {len(lateral_insights)} lateral insights")

    return state


async def run_persona_discussion(state: BONOState) -> BONOState:
    """
    Phase 5: Personas discuss and synthesize findings.
    Cross-domain dialogue to reach breakthrough insights.
    """
    from google import genai

    personas = state["personas"]
    problem = state["problem_classification"]["problem_statement"]
    hat_contributions = state["hat_contributions"]
    lateral_insights = state["lateral_insights"]

    # Summarize key findings
    all_insights = []
    for hat, contributions in hat_contributions.items():
        for c in contributions:
            all_insights.append(f"{HAT_ICONS.get(hat, '💭')} {c.get('persona_name', 'Unknown')}: {c.get('key_point', '')}")

    for li in lateral_insights:
        all_insights.append(f"💡 {li.get('generated_by', 'Unknown')}: {li.get('insight', '')}")

    discussion_prompt = f"""You are facilitating a synthesis discussion between expert personas.

PROBLEM: {problem}

PERSONAS:
{[f"- {p['icon']} {p['name']} ({p['domain']}/{p['subdomain']})" for p in personas]}

KEY INSIGHTS FROM SESSION:
{chr(10).join(all_insights[:15])}

Create a dialogue where these personas discuss and synthesize the findings.
Each persona should:
1. Share their key takeaway
2. Respond to or build on another persona's point
3. Identify breakthrough connections

Respond as JSON:
{{
    "dialogue": [
        {{
            "speaker": "persona name",
            "statement": "what they say",
            "responds_to": "who they're responding to (or null if initiating)",
            "synthesis_point": "key insight from this turn (or null)"
        }},
        ...
    ],
    "breakthrough_ideas": ["breakthrough 1", "breakthrough 2", ...],
    "key_decisions": ["decision 1", "decision 2", ...]
}}

Create 6-8 dialogue turns with genuine intellectual exchange.
End with 2-3 breakthrough ideas and 2-3 key decisions.
"""

    try:
        client = genai.Client()
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=discussion_prompt,
            config={"response_mime_type": "application/json"}
        )

        import json
        result = json.loads(response.text)

        state["persona_dialogue"] = result.get("dialogue", [])
        state["breakthrough_ideas"] = result.get("breakthrough_ideas", [])
        state["synthesis_points"] = result.get("key_decisions", [])

        print(f"[BONO] Persona discussion: {len(state['persona_dialogue'])} turns")
        print(f"[BONO] Breakthroughs: {len(state['breakthrough_ideas'])}")

    except Exception as e:
        print(f"[BONO] Persona discussion error: {e}")
        state["persona_dialogue"] = []
        state["breakthrough_ideas"] = []
        state["synthesis_points"] = []

    return state


async def create_action_plan(state: BONOState) -> BONOState:
    """
    Phase 6: Create implementation roadmap.
    Quick wins, medium-term, long-term actions.
    """
    from google import genai

    problem = state["problem_classification"]["problem_statement"]
    personas = state["personas"]
    breakthroughs = state["breakthrough_ideas"]
    decisions = state["synthesis_points"]

    action_prompt = f"""Create an implementation action plan for this BONO session.

PROBLEM: {problem}

BREAKTHROUGH IDEAS:
{breakthroughs}

KEY DECISIONS:
{decisions}

AVAILABLE PERSONAS (assign as owners):
{[p['name'] for p in personas]}

Create action items in JSON format:
{{
    "action_items": [
        {{
            "action": "specific action to take",
            "owner_persona": "persona name",
            "timeframe": "quick_win" or "medium_term" or "long_term",
            "dependencies": ["dependency 1", ...],
            "success_metric": "how we know it's done"
        }},
        ...
    ]
}}

Create 2-3 quick wins (0-3 months), 2-3 medium-term (3-12 months), 1-2 long-term (1-3 years).
"""

    try:
        client = genai.Client()
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=action_prompt,
            config={"response_mime_type": "application/json"}
        )

        import json
        result = json.loads(response.text)
        state["action_items"] = result.get("action_items", [])

        print(f"[BONO] Created {len(state['action_items'])} action items")

    except Exception as e:
        print(f"[BONO] Action planning error: {e}")
        state["action_items"] = []

    return state


def compile_session_report(state: BONOState) -> BONOState:
    """
    Final step: Compile complete session report.
    """
    state["session_report"] = {
        "generated_at": datetime.now().isoformat(),
        "problem_classification": state["problem_classification"],
        "personas": state["personas"],
        "hat_sequence": state["hat_sequence"],
        "hat_contributions": state["hat_contributions"],
        "lateral_insights": state["lateral_insights"],
        "persona_dialogue": state["persona_dialogue"],
        "breakthrough_ideas": state["breakthrough_ideas"],
        "key_decisions": state["synthesis_points"],
        "action_items": state["action_items"],
    }

    print(f"[BONO] Session report compiled")
    return state


# =============================================================================
# PIPELINE CREATION
# =============================================================================

def create_bono_pipeline() -> StateGraph:
    """Create the BONO Innovation pipeline."""

    workflow = StateGraph(BONOState)

    # Add nodes
    workflow.add_node("classify", classify_problem)
    workflow.add_node("personas", generate_personas)
    workflow.add_node("research", gather_research)
    workflow.add_node("six_hats", run_six_hats)
    workflow.add_node("lateral", apply_lateral_thinking)
    workflow.add_node("discussion", run_persona_discussion)
    workflow.add_node("action_plan", create_action_plan)
    workflow.add_node("report", compile_session_report)

    # Set entry point
    workflow.set_entry_point("classify")

    # Linear flow with parallel research
    workflow.add_edge("classify", "personas")
    workflow.add_edge("personas", "research")
    workflow.add_edge("research", "six_hats")
    workflow.add_edge("six_hats", "lateral")
    workflow.add_edge("lateral", "discussion")
    workflow.add_edge("discussion", "action_plan")
    workflow.add_edge("action_plan", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


# =============================================================================
# PUBLIC API
# =============================================================================

async def run_bono_session(
    problem: str,
    session_id: str = None,
    context_type: str = "innovation",
) -> Dict[str, Any]:
    """
    Run a complete BONO Innovation session.

    Args:
        problem: The problem/opportunity to explore
        session_id: Session identifier
        context_type: One of 'innovation', 'strategic', 'crisis', 'product'

    Returns:
        Complete session report with personas, hat contributions,
        lateral insights, and action plan
    """
    import time

    session_id = session_id or f"bono_{int(time.time())}"

    initial_state: BONOState = {
        "user_input": problem,
        "session_id": session_id,
        "context_type": context_type,
        "problem_classification": None,
        "discovered_domains": [],
        "personas": [],
        "hat_sequence": [],
        "current_hat": None,
        "hat_contributions": {},
        "lateral_insights": [],
        "random_words": [],
        "provocations": [],
        "persona_dialogue": [],
        "synthesis_points": [],
        "action_items": [],
        "breakthrough_ideas": [],
        "web_research": {},
        "neo4j_context": [],
        "session_report": None,
        "error": None,
    }

    pipeline = create_bono_pipeline()
    result = await pipeline.ainvoke(initial_state)

    return result["session_report"]


def format_bono_report(report: Dict[str, Any]) -> str:
    """Format BONO session report as markdown."""

    if not report:
        return "No report generated."

    classification = report.get("problem_classification", {})
    personas = report.get("personas", [])
    hat_contributions = report.get("hat_contributions", {})
    lateral_insights = report.get("lateral_insights", [])
    dialogue = report.get("persona_dialogue", [])
    breakthroughs = report.get("breakthrough_ideas", [])
    actions = report.get("action_items", [])

    output = f"""# 🎭 BONO Innovation Session Report

## Problem Classification
- **Definition Clarity**: {classification.get('definition_clarity', 'N/A')}
- **System Complexity**: {classification.get('system_complexity', 'N/A')}
- **Context**: {classification.get('context_type', 'N/A')}
- **Problem Statement**: {classification.get('problem_statement', 'N/A')}

## 👥 Expert Personas

"""

    for p in personas:
        output += f"### {p.get('icon', '👤')} {p.get('name', 'Unknown')}\n"
        output += f"**Domain**: {p.get('domain', 'N/A')} / {p.get('subdomain', 'N/A')}\n"
        output += f"**Expertise**: {', '.join(p.get('expertise', []))}\n"
        output += f"**Perspective**: {p.get('perspective', 'N/A')}\n\n"

    output += "## 🎩 Six Thinking Hats Journey\n\n"

    for hat, contributions in hat_contributions.items():
        output += f"### {HAT_ICONS.get(hat, '💭')} {hat.upper()} HAT\n"
        for c in contributions:
            output += f"**{c.get('persona_name', 'Unknown')}**: {c.get('key_point', 'N/A')}\n"
        output += "\n"

    output += "## 💡 Lateral Thinking Insights\n\n"

    for li in lateral_insights:
        output += f"- **{li.get('technique', 'N/A').replace('_', ' ').title()}** ({li.get('trigger', 'N/A')})\n"
        output += f"  {li.get('insight', 'N/A')}\n\n"

    output += "## 🗣️ Persona Synthesis Discussion\n\n"

    for turn in dialogue:
        output += f"**{turn.get('speaker', 'Unknown')}**: {turn.get('statement', 'N/A')}\n\n"

    output += "## 🚀 Breakthrough Ideas\n\n"

    for i, idea in enumerate(breakthroughs, 1):
        output += f"{i}. {idea}\n"

    output += "\n## 📋 Action Plan\n\n"

    for action in actions:
        timeframe = action.get('timeframe', 'N/A').replace('_', ' ').title()
        output += f"### [{timeframe}] {action.get('action', 'N/A')}\n"
        output += f"- **Owner**: {action.get('owner_persona', 'TBD')}\n"
        output += f"- **Success Metric**: {action.get('success_metric', 'TBD')}\n\n"

    return output


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BONOState",
    "ProblemClassification",
    "DomainPersona",
    "HatContribution",
    "LateralInsight",
    "create_bono_pipeline",
    "run_bono_session",
    "format_bono_report",
    "HAT_SEQUENCES",
    "HAT_ICONS",
    "HAT_FOCUS",
]
