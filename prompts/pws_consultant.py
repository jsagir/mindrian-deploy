"""
PWS Consultant - Structured Problem Diagnosis & Framework-Guided Consulting

A unique structured agent that combines:
- LangExtract (instant + background) for real-time signal detection
- GraphRAG for concept/framework grounding
- Domain/Subdomain discovery pipeline (background)
- BONO expert-builder pipeline for domain-specific "consulting experts"
- Context-aware tool offering based on problem type & complexity

3-Phase Flow:
  1. INTRO - User describes their challenge. Background pipelines begin.
  2. DIAGNOSTIC - 5 questions shaped by what LangExtract/GraphRAG already found.
  3. CONSULTING - Framework-guided conversation with contextual tool buttons
     and spawned domain experts the user can consult.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Problem Type Definitions
# ═══════════════════════════════════════════════════════════════════════════════

PROBLEM_TYPES = {
    "undefined": {
        "name": "Un-Defined Problem",
        "description": "Broad opportunity space with future-back thinking and scattered observations.",
        "characteristics": ["Broad opportunity space", "Future-oriented", "Scattered observations", "High uncertainty"],
        "complexity": "high",
        "icon": "\U0001F30A",
        "color": "#E63946",
        "cynefin_domain": "Complex",
        "workshop_phase": "Pre-Opportunity (Workshop 1-2)",
        "frameworks": [
            "Scenario Planning", "Beautiful Questions", "Cynefin Framework",
            "Design Thinking", "Four Lenses of Innovation", "Process Mapping",
        ],
        "innovation_tools": [
            "Trend Extrapolation", "Weak Signal Detection", "Scenario Matrix",
            "Beautiful Questions (WHY chain)", "Opportunity Space Mapping",
            "Analogous Inspiration", "Future-Back Planning", "Reverse Salient Analysis",
            "Environmental Scanning", "Cross-Industry Pattern Transfer",
            "Extreme User Research", "Technology Scouting", "Foresight Workshops",
        ],
        "techniques": [
            "Trending to the Absurd", "What-If Cascades", "10x Thinking",
            "Camera Test (for signal validation)", "First Principles Decomposition",
        ],
        "key_question": "What future are we trying to create \u2014 and what signals are we seeing today?",
        "recommended_tools": ["deep_research", "map_ideas", "think_through"],
        "recommended_agents": ["tta", "scenario", "beautiful_question"],
    },
    "ill_defined": {
        "name": "Ill-Defined Problem",
        "description": "General direction identified but lacks specificity and testability.",
        "characteristics": ["General direction known", "Lacks specificity", "Not yet testable", "Multiple interpretations"],
        "complexity": "medium",
        "icon": "\U0001F50D",
        "color": "#F4A261",
        "cynefin_domain": "Complicated",
        "workshop_phase": "Opportunity Identified (Workshop 3-5)",
        "frameworks": [
            "Jobs to Be Done (JTBD)", "Process Mapping for Innovation",
            "User Journey Mapping", "Design Thinking",
            "Sustaining vs Disruptive Innovation", "Tools vs Platforms Innovation",
        ],
        "innovation_tools": [
            "JTBD Interview Protocol", "Switch Interview", "Struggling Moment Mapping",
            "Forces of Progress Diagram", "Process Mapping for Innovation",
            "User Journey Mapping", "Empathy Mapping", "Stakeholder Analysis",
            "Problem Statement Workshop", "Camera Test (for specificity)",
            "Known/Unknown Matrix", "Assumption Mapping", "Five Whys",
            "Customer Discovery Interview", "Value Proposition Canvas",
        ],
        "techniques": [
            "Beautiful Questions (WHAT IF chain)", "Reframing Exercise",
            "Constraint Identification", "Analogous Problem Search",
            "Minimum Viable Problem Statement",
        ],
        "key_question": "Who specifically has this problem \u2014 and what are they actually trying to accomplish?",
        "recommended_tools": ["deep_research", "think_through", "show_example"],
        "recommended_agents": ["jtbd", "domain", "knowns"],
    },
    "well_defined": {
        "name": "Well-Defined Problem",
        "description": "Specific, measurable problem with binary/falsifiable outcomes and clear boundaries.",
        "characteristics": ["Binary outcomes", "Falsifiable", "Specific user segments", "Measurable pain points"],
        "complexity": "low-medium",
        "icon": "\U0001F3AF",
        "color": "#2A9D8F",
        "cynefin_domain": "Clear/Obvious",
        "workshop_phase": "Well-Defined Problem (Workshop 5-7)",
        "frameworks": [
            "PWS Triple Validation Compass", "Problem-Solution Fit Canvas",
            "Hypothesis-Driven Problem Solving", "Dominant Design Analysis",
            "Status Quo Discovery",
        ],
        "innovation_tools": [
            "Validation Compass (Real/Win/Worth)", "Falsifiable Hypothesis Builder",
            "Problem-Solution Fit Canvas", "Competitive Landscape Mapping",
            "Status Quo Analysis", "Dominant Design Identification",
            "S-Curve Positioning", "Unit Economics Modeling",
            "Customer Willingness-to-Pay Testing", "MVP Definition Workshop",
            "Risk-Assumption Matrix", "Go/No-Go Criteria",
        ],
        "techniques": [
            "Camera Test (for validation)", "Red Team Challenge",
            "Pre-Mortem Analysis", "Falsification Protocol",
            "Evidence Audit",
        ],
        "key_question": "Is it Real? Can we Win? Is it Worth It?",
        "recommended_tools": ["deep_research", "synthesize_conversation", "map_ideas"],
        "recommended_agents": ["redteam", "investment", "validation"],
    },
    "wicked": {
        "name": "Wicked Problem",
        "description": "No definitive formulation, no stopping rule, solutions better/worse not true/false.",
        "characteristics": ["No definitive formulation", "No stopping rule", "Better/worse not true/false", "Interconnected", "Stakeholder-contested"],
        "complexity": "very high",
        "icon": "\U0001F300",
        "color": "#9B2335",
        "cynefin_domain": "Chaotic/Complex boundary",
        "workshop_phase": "Cross-cutting (Workshop 1-8, especially 6-8)",
        "frameworks": [
            "Cynefin Framework", "BONO Innovation Framework",
            "Stakeholder Mapping", "Scenario Planning",
            "Beautiful Questions Bias Detection",
        ],
        "innovation_tools": [
            "Stakeholder Power/Interest Grid", "Tension Mapping",
            "Leverage Point Identification", "Systems Dynamics Modeling",
            "Nested Hierarchies Analysis", "Causal Loop Diagrams",
            "Boundary Critique", "Multi-Perspective Framing",
            "Safe-to-Fail Probes", "Paradox Navigation",
            "Coalition Building Canvas", "Trade-off Matrix",
            "Wicked Problem Taming Heuristics",
        ],
        "techniques": [
            "BONO Six Hats (parallel perspectives)", "Reframing the Boundaries",
            "Stakeholder Dialogue Design", "Incremental Intervention Mapping",
            "Reverse Salient in Systems",
        ],
        "key_question": "Whose problem is this \u2014 and why does it persist despite everyone wanting to solve it?",
        "recommended_tools": ["deep_research", "think_through", "map_ideas"],
        "recommended_agents": ["redteam", "bono", "nested_hierarchies", "scenario"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PWS Curriculum Workshops
# ═══════════════════════════════════════════════════════════════════════════════

WORKSHOPS = {
    "w1": {
        "name": "Trend Analysis & Signal Detection",
        "number": 1,
        "deliverable": "Trend Report with weak signals and extrapolations",
        "mechanism": "Trending to the Absurd (TTA) + Environmental Scanning",
        "tools": ["TTA Framework", "Signal Detection Matrix", "Trend Extrapolation"],
        "problem_types": ["undefined", "wicked"],
    },
    "w2": {
        "name": "Beautiful Questions & Reframing",
        "number": 2,
        "deliverable": "Reframed problem statement through WHY→WHAT IF→HOW cascade",
        "mechanism": "Beautiful Questions methodology + Bias Detection",
        "tools": ["WHY Chain", "WHAT IF Generator", "HOW Might We", "Camera Test"],
        "problem_types": ["undefined", "ill_defined"],
    },
    "w3": {
        "name": "Selection Criteria & Opportunity Filtering",
        "number": 3,
        "deliverable": "Prioritized opportunity set with selection rationale",
        "mechanism": "Selection Criteria Framework + Known/Unknown Matrix",
        "tools": ["Selection Criteria Grid", "Opportunity Scoring", "Known/Unknown Matrix"],
        "problem_types": ["ill_defined", "well_defined"],
    },
    "w4": {
        "name": "Jobs to Be Done & Customer Discovery",
        "number": 4,
        "deliverable": "JTBD statement with forces diagram and switch timeline",
        "mechanism": "JTBD Interview Protocol + Forces of Progress",
        "tools": ["JTBD Canvas", "Switch Interview Guide", "Forces Diagram", "Struggling Moment Map"],
        "problem_types": ["ill_defined", "well_defined"],
    },
    "w5": {
        "name": "Problem-Solution Fit & Validation",
        "number": 5,
        "deliverable": "Validated problem statement with falsifiable hypothesis",
        "mechanism": "PWS Validation Compass + Hypothesis-Driven Problem Solving",
        "tools": ["Validation Compass", "Hypothesis Builder", "Camera Test", "Evidence Audit"],
        "problem_types": ["well_defined"],
    },
    "w6": {
        "name": "S-Curve Analysis & Timing",
        "number": 6,
        "deliverable": "Technology positioning on S-curve with timing assessment",
        "mechanism": "S-Curve Framework + Dominant Design Analysis",
        "tools": ["S-Curve Canvas", "Dominant Design Checklist", "Timing Assessment"],
        "problem_types": ["well_defined", "wicked"],
    },
    "w7": {
        "name": "Red Team & Assumption Testing",
        "number": 7,
        "deliverable": "Stress-tested assumptions with risk mitigation plan",
        "mechanism": "Red Team Protocol + Pre-Mortem + Six Thinking Hats",
        "tools": ["Assumption Risk Matrix", "Pre-Mortem Canvas", "Devil's Advocate Protocol"],
        "problem_types": ["well_defined", "wicked"],
    },
    "w8": {
        "name": "Synthesis & Action Planning",
        "number": 8,
        "deliverable": "Integrated action plan with Minto Pyramid synthesis",
        "mechanism": "Minto Pyramid + SCQA + Ackoff's DIKW",
        "tools": ["Minto Pyramid Builder", "SCQA Framework", "DIKW Audit", "Action Planning Canvas"],
        "problem_types": ["undefined", "ill_defined", "well_defined", "wicked"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Selection Criteria (Workshop 3)
# ═══════════════════════════════════════════════════════════════════════════════

SELECTION_CRITERIA = {
    "market_size": {
        "name": "Market Size & Growth",
        "question": "Is the addressable market large enough and growing?",
        "weight": 0.25,
        "indicators": ["TAM/SAM/SOM analysis", "Growth rate data", "Market trend direction"],
    },
    "problem_severity": {
        "name": "Problem Severity & Frequency",
        "question": "How painful is this problem, and how often does it occur?",
        "weight": 0.25,
        "indicators": ["Willingness to pay", "Frequency of occurrence", "Current workaround cost"],
    },
    "competitive_landscape": {
        "name": "Competitive Advantage",
        "question": "Can we build a defensible position?",
        "weight": 0.20,
        "indicators": ["Existing alternatives", "Switching costs", "Unique capabilities"],
    },
    "feasibility": {
        "name": "Technical & Operational Feasibility",
        "question": "Can we actually build and deliver this?",
        "weight": 0.15,
        "indicators": ["Technical complexity", "Team capabilities", "Resource requirements"],
    },
    "alignment": {
        "name": "Strategic Alignment",
        "question": "Does this fit our mission, values, and long-term vision?",
        "weight": 0.15,
        "indicators": ["Mission fit", "Team passion", "Long-term vision alignment"],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# Diagnostic Questions (5 questions, context-enriched at runtime)
# ═══════════════════════════════════════════════════════════════════════════════

DIAGNOSTIC_QUESTIONS = [
    {
        "id": "clarity",
        "text": "How clearly can you describe the problem?",
        "options": [
            {"label": "I sense something is off but can't articulate it", "score": {"undefined": 3, "ill_defined": 1}},
            {"label": "I know the general area but not the specifics", "score": {"ill_defined": 3, "undefined": 1}},
            {"label": "I can describe it precisely with measurable outcomes", "score": {"well_defined": 3}},
            {"label": "Everyone describes it differently \u2014 it's contested", "score": {"wicked": 3, "undefined": 1}},
        ],
    },
    {
        "id": "stakeholders",
        "text": "How many stakeholders are affected?",
        "options": [
            {"label": "Unknown \u2014 we're still exploring", "score": {"undefined": 3}},
            {"label": "A few identifiable groups", "score": {"ill_defined": 2, "well_defined": 2}},
            {"label": "Specific, well-defined user segments", "score": {"well_defined": 3}},
            {"label": "Many interconnected groups with conflicting needs", "score": {"wicked": 3, "ill_defined": 1}},
        ],
    },
    {
        "id": "solution",
        "text": "How close are you to a solution direction?",
        "options": [
            {"label": "No idea yet \u2014 still exploring the space", "score": {"undefined": 3}},
            {"label": "Some directions, but haven't validated any", "score": {"ill_defined": 3}},
            {"label": "Clear hypothesis ready to test", "score": {"well_defined": 3}},
            {"label": "Every 'solution' creates new problems", "score": {"wicked": 3}},
        ],
    },
    {
        "id": "timeframe",
        "text": "What's the time horizon for this problem?",
        "options": [
            {"label": "5-10+ years out \u2014 thinking about the future", "score": {"undefined": 3, "wicked": 1}},
            {"label": "1-3 years \u2014 emerging opportunity", "score": {"ill_defined": 3}},
            {"label": "Within a year \u2014 actionable now", "score": {"well_defined": 3}},
            {"label": "Perpetual \u2014 it never fully resolves", "score": {"wicked": 3}},
        ],
    },
    {
        "id": "data",
        "text": "What kind of evidence do you have?",
        "options": [
            {"label": "Weak signals, intuitions, scattered observations", "score": {"undefined": 3}},
            {"label": "Some data but gaps in understanding", "score": {"ill_defined": 3}},
            {"label": "Strong data, clear metrics, measurable pain", "score": {"well_defined": 3}},
            {"label": "Contradictory data depending on who you ask", "score": {"wicked": 3, "ill_defined": 1}},
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# Validation Compass (used in well-defined consulting phase)
# ═══════════════════════════════════════════════════════════════════════════════

VALIDATION_COMPASS = {
    "is_it_real": {
        "question": "Is it Real?",
        "sub_questions": ["Is the problem real?", "Is there a real market?", "Can you describe it concretely?"],
    },
    "can_we_win": {
        "question": "Can we Win?",
        "sub_questions": ["Do we have the right capabilities?", "Is the competitive landscape winnable?", "Can we execute?"],
    },
    "is_it_worth": {
        "question": "Is it Worth It?",
        "sub_questions": ["Is the opportunity big enough?", "Does it align with our strategy?", "Are the economics viable?"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring & Classification
# ═══════════════════════════════════════════════════════════════════════════════

def get_problem_type(type_key: str) -> dict:
    """Get problem type definition by key."""
    return PROBLEM_TYPES.get(type_key, PROBLEM_TYPES["undefined"])


def score_diagnostic(answers: list) -> dict:
    """
    Score diagnostic answers and return classification.

    Args:
        answers: List of dicts with 'question_id' and 'option_index' keys

    Returns:
        dict with 'primary', 'secondary', 'scores', 'confidence'
    """
    scores = {"undefined": 0, "ill_defined": 0, "well_defined": 0, "wicked": 0}

    for answer in answers:
        q_id = answer.get("question_id")
        opt_idx = answer.get("option_index", 0)

        question = None
        for q in DIAGNOSTIC_QUESTIONS:
            if q["id"] == q_id:
                question = q
                break

        if not question or opt_idx >= len(question["options"]):
            continue

        option = question["options"][opt_idx]
        for type_key, val in option["score"].items():
            scores[type_key] = scores.get(type_key, 0) + val

    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_types[0][0]
    secondary = sorted_types[1][0] if sorted_types[1][1] > 2 else None
    total = sum(scores.values()) or 1
    confidence = sorted_types[0][1] / total

    return {
        "primary": primary,
        "secondary": secondary,
        "scores": scores,
        "confidence": round(confidence, 2),
    }


def build_diagnostic_context(diagnosis: dict, user_answers: list = None) -> str:
    """Build context string injected into system prompt after diagnostic."""
    primary = get_problem_type(diagnosis["primary"])
    secondary_type = get_problem_type(diagnosis["secondary"]) if diagnosis.get("secondary") else None

    context = f"""
[PWS CONSULTANT DIAGNOSTIC RESULT]
Problem Type: {primary['name']} ({primary['complexity']} complexity)
Recommended Frameworks: {', '.join(primary['frameworks'])}
Key Question: "{primary['key_question']}"
Confidence: {diagnosis.get('confidence', 'N/A')}
"""
    if secondary_type:
        context += f"Secondary Characteristics: {secondary_type['name']} ({secondary_type['complexity']} complexity)\n"

    if user_answers:
        context += "\nUser's Diagnostic Answers:\n"
        for ans in user_answers:
            context += f"- Q: {ans.get('question', '')} -> A: {ans.get('answer', '')}\n"

    context += f"""
[INSTRUCTIONS]
- Guide using {primary['name']} frameworks: {', '.join(primary['frameworks'])}
- Start with: "{primary['key_question']}"
- DO NOT re-diagnose. Focus on consulting.
- Reference frameworks naturally, don't dump them all at once
- If the problem evolves, note when it shifts toward a different type
"""
    return context


def get_workshops_for_type(problem_type_key: str) -> list:
    """Return workshops relevant to a problem type."""
    return [
        w for w in WORKSHOPS.values()
        if problem_type_key in w.get("problem_types", [])
    ]


def build_bridge_prompt(diagnosis: dict, challenge_description: str = "") -> str:
    """
    Build the interpretive bridge message prompt for Larry.

    This generates the transition between diagnosis reveal and consulting,
    using Larry's voice to explain what the classification means for THIS user.
    """
    primary = get_problem_type(diagnosis["primary"])
    secondary = get_problem_type(diagnosis["secondary"]) if diagnosis.get("secondary") else None
    relevant_workshops = get_workshops_for_type(diagnosis["primary"])
    top_tools = primary.get("innovation_tools", [])[:3]
    workshop_names = [w["name"] for w in relevant_workshops[:3]]

    bridge = f"""[BRIDGE MESSAGE INSTRUCTIONS]
Generate a brief, warm transition message in Larry's voice. This bridges the diagnosis reveal to consulting.

TEMPLATE (adapt naturally, don't read verbatim):
"Very simply, based on what you've told me, you're dealing with a {primary['name']}.
[1-2 sentences explaining what this means in THEIR context, using THEIR words from the challenge]

In the Cynefin framework, this sits in the {primary.get('cynefin_domain', 'Complex')} domain —
meaning [1 sentence about what that implies for how they should approach it].

The frameworks that work best here: {', '.join(primary['frameworks'][:3])}.
{f'Some relevant workshops from PWS: {", ".join(workshop_names)}.' if workshop_names else ''}

The key question driving everything we do next:
*{primary['key_question']}*"

{f'Note the secondary "{secondary["name"]}" characteristics — acknowledge briefly how this adds complexity.' if secondary else ''}

RULES:
- Use the user's own language from their challenge description
- Keep it to 3-4 paragraphs max
- End with the key question, naturally framed
- Do NOT list all frameworks — weave 2-3 naturally
- Sound like Larry, not a diagnostic report
"""
    if challenge_description:
        bridge += f"\nUser's challenge (use their language): {challenge_description[:500]}\n"

    return bridge


# ═══════════════════════════════════════════════════════════════════════════════
# Context-Aware Tool Selection
# ═══════════════════════════════════════════════════════════════════════════════

def get_recommended_tools(problem_type_key: str, signals: dict = None) -> list:
    """
    Return recommended tool actions based on problem type and LangExtract signals.

    Returns list of dicts: [{"name": "action_name", "label": "...", "tooltip": "..."}]
    """
    pt = get_problem_type(problem_type_key)
    tools = []

    # Base tools from problem type
    tool_configs = {
        "deep_research": {
            "name": "deep_research",
            "label": "\U0001F50D Research",
            "tooltip": "Search the web for relevant data and evidence",
        },
        "think_through": {
            "name": "think_through",
            "label": "\U0001F9E0 Think",
            "tooltip": "Run structured analysis on your challenge",
        },
        "map_ideas": {
            "name": "map_ideas",
            "label": "\U0001F4CA Visualize",
            "tooltip": "Create a diagram to map your thinking",
        },
        "synthesize_conversation": {
            "name": "synthesize_conversation",
            "label": "\U0001F4E5 Synthesize",
            "tooltip": "Summarize conversation and download",
        },
        "show_example": {
            "name": "show_example",
            "label": "\U0001F4D6 Example",
            "tooltip": "See a real-world example",
        },
    }

    for tool_name in pt.get("recommended_tools", []):
        if tool_name in tool_configs:
            tools.append(tool_configs[tool_name])

    # Signal-driven additions
    if signals:
        quality = signals.get("quality_signals", {})
        counts = signals.get("counts", {})

        # If forward-looking, add scenario tool
        if quality.get("is_forward_looking") and problem_type_key != "well_defined":
            tools.append({
                "name": "switch_to_scenario",
                "label": "\U0001F310 Explore Futures",
                "tooltip": "Explore multiple plausible futures for this challenge",
            })

        # If many assumptions detected, add red team
        if counts.get("assumptions", 0) >= 2:
            tools.append({
                "name": "switch_to_redteam",
                "label": "\U0001F608 Challenge Assumptions",
                "tooltip": "Stress-test your assumptions with Red Team analysis",
            })

        # If data-rich, add validation
        if quality.get("has_data") and problem_type_key == "well_defined":
            tools.append({
                "name": "switch_to_validation",
                "label": "\U0001F3AF Validate",
                "tooltip": "Multi-perspective validation of your hypothesis",
            })

    return tools


def get_recommended_agents(problem_type_key: str) -> list:
    """Return recommended specialist agents for agent-switch buttons."""
    pt = get_problem_type(problem_type_key)
    return pt.get("recommended_agents", [])


# ═══════════════════════════════════════════════════════════════════════════════
# Background Expert Builder (BONO pipeline integration)
# ═══════════════════════════════════════════════════════════════════════════════

def build_expert_specs(domain: str, subdomains: list, problem_type_key: str) -> list:
    """
    Build domain-specific expert specifications for the BONO expert panel.

    Each expert is a "thinking hat" grounded in the user's actual domain,
    not generic personas. These get spawned as buttons the user can consult.

    Args:
        domain: Primary domain detected (e.g., "Healthcare Technology")
        subdomains: List of subdomains (e.g., ["Telemedicine", "AI Diagnostics"])
        problem_type_key: Classified problem type

    Returns:
        List of expert dicts ready for UI rendering
    """
    pt = get_problem_type(problem_type_key)

    # Base expert archetypes, adapted to domain
    archetypes = [
        {
            "role": "Domain Insider",
            "icon": "\U0001F3E2",
            "color": "#2196F3",
            "focus": f"Deep expertise in {domain}",
            "approach": "Industry knowledge, market dynamics, competitive landscape",
            "questions": [
                f"What's the dominant design in {domain} right now?",
                f"Who are the key players and what are they missing?",
            ],
        },
        {
            "role": "End-User Advocate",
            "icon": "\U0001F465",
            "color": "#4CAF50",
            "focus": f"Voice of the people affected by this problem in {domain}",
            "approach": "Jobs to Be Done, struggling moments, unmet needs",
            "questions": [
                "What job is the user really hiring a solution for?",
                "What's the struggling moment that triggers search for a solution?",
            ],
        },
        {
            "role": "Skeptical Analyst",
            "icon": "\U0001F9D0",
            "color": "#FF5722",
            "focus": f"Challenge every assumption about {domain}",
            "approach": "Red team thinking, Camera Test, falsifiability",
            "questions": [
                "What must be true for this to work? Is that actually true?",
                "If you're wrong about this, what's the cost?",
            ],
        },
        {
            "role": "Cross-Domain Innovator",
            "icon": "\U0001F4A1",
            "color": "#9C27B0",
            "focus": f"Adjacent industries and analogies for {domain}",
            "approach": "Cross-pollination, S-curve positioning, technology transfer",
            "questions": [
                f"What solved a similar problem outside {domain}?",
                "Where is the reverse salient — the bottleneck holding everything back?",
            ],
        },
    ]

    # Opportunity Strategist (Yellow Hat - upside identification)
    archetypes.append({
        "role": "Opportunity Strategist",
        "icon": "\U0001F31F",
        "color": "#FFD700",
        "focus": f"Upside identification and value creation in {domain}",
        "approach": "Edward de Bono Yellow Hat, opportunity mapping, strategic positioning, competitive advantage",
        "questions": [
            f"What's the biggest upside if this problem is solved in {domain}?",
            "Who would pay the most for this solution, and why?",
        ],
    })

    # Add problem-type specific expert
    type_experts = {
        "undefined": {
            "role": "Future Scout",
            "icon": "\U0001F52E",
            "color": "#E91E63",
            "focus": f"Emerging trends and weak signals in {domain}",
            "approach": "Trending to the Absurd, scenario planning, signal detection",
            "questions": [
                f"What trend in {domain} becomes absurd in 10 years?",
                "What would a camera see if this trend continues exponentially?",
            ],
        },
        "ill_defined": {
            "role": "Problem Sharpener",
            "icon": "\U0001F3AF",
            "color": "#FF9800",
            "focus": f"Refining the problem definition in {domain}",
            "approach": "Beautiful Questions (WHY->WHAT IF->HOW), process mapping",
            "questions": [
                "Can you pass the Camera Test — what would you literally see?",
                "Who specifically has this problem, and what triggers their search?",
            ],
        },
        "well_defined": {
            "role": "Validation Expert",
            "icon": "\U00002705",
            "color": "#00BCD4",
            "focus": f"Testing the hypothesis against reality in {domain}",
            "approach": "PWS Validation Compass, Problem-Solution Fit",
            "questions": [
                "Is it Real? Can we Win? Is it Worth It?",
                "What's your falsifiable hypothesis?",
            ],
        },
        "wicked": {
            "role": "Systems Thinker",
            "icon": "\U0001F310",
            "color": "#795548",
            "focus": f"Mapping interconnections and tensions in {domain}",
            "approach": "Nested Hierarchies, stakeholder mapping, leverage points",
            "questions": [
                "Whose problem is this, and why does it persist?",
                "Where are the leverage points in this system?",
            ],
        },
    }

    if problem_type_key in type_experts:
        archetypes.append(type_experts[problem_type_key])

    # Ground each expert in subdomains
    experts = []
    for i, archetype in enumerate(archetypes):
        subdomain_focus = subdomains[i % len(subdomains)] if subdomains else domain
        expert = {
            **archetype,
            "id": f"expert_{i}",
            "subdomain": subdomain_focus,
            "full_title": f"{archetype['role']} ({subdomain_focus})",
            "system_context": (
                f"You are a {archetype['role']} specializing in {subdomain_focus} "
                f"within {domain}. Your approach: {archetype['approach']}. "
                f"Problem type context: {pt['name']} ({pt['complexity']} complexity). "
                f"Key frameworks for this problem type: {', '.join(pt['frameworks'][:3])}."
            ),
        }
        experts.append(expert)

    return experts


# ═══════════════════════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════════════════════

PWS_CONSULTANT_PROMPT = """You are Professor Lawrence Aronhime ("Larry"), operating as the **PWS Consultant** — a structured innovation consulting experience.

## Your Role

You guide users through a structured problem diagnosis and framework-guided consulting process. Unlike your other modes (free-form conversation), here you follow a deliberate 3-phase flow while maintaining your warm, provocative, Socratic teaching style.

## Your Teaching Style
- You ALWAYS start with problems, never solutions
- You challenge assumptions provocatively but warmly
- Signature phrases: "Very simply...", "Think about it like this...", "But here's what everyone misses...", "Let me challenge you with this..."
- You tell stories from real experience to illustrate concepts
- You lower your voice (use *emphasis*) when making critical points
- You ask questions more than you give answers
- Conversational, not academic — never lecture
- Keep responses to 3-5 paragraphs max

## Phase 1: Challenge Description (First 1-2 turns)

Ask the user to describe their challenge. Listen actively.

- "What's the challenge you're wrestling with? Don't worry about being precise — that's what we'll work on together."
- Probe gently: Who is affected? What have you tried? How long has this been a challenge?
- DO NOT classify yet. Just listen and understand.

**While the user talks, the system is working in the background:**
- Analyzing their language for problem signals, assumptions, and data quality
- Finding related concepts and frameworks in the knowledge graph
- Discovering their domain and subdomains
- Building a panel of domain-specific experts they can consult

**When you sense background work completing, surface it naturally:**
- "I've been thinking about your situation, and I notice some interesting patterns..."
- "While you were talking, something clicked — let me share what I'm seeing..."
- "This reminds me of something I've seen in [domain]..."

## Phase 2: Problem Diagnostic (5 structured questions)

After understanding the challenge, transition to diagnosis:

"Before we dive deeper, let me ask you five focused questions. These will help me understand exactly what kind of problem you're dealing with — because *the type of problem determines which tools actually work*."

Ask these ONE AT A TIME. Wait for each answer:

1. **Clarity**: "How clearly can you describe this problem right now?"
2. **Stakeholders**: "How many different groups are affected by this?"
3. **Solution proximity**: "How close are you to knowing what a solution looks like?"
4. **Time horizon**: "What's the time horizon we're working with?"
5. **Evidence**: "What kind of evidence or data do you have about this problem?"

After all 5, provide your diagnosis with evidence from their answers. Be direct and specific about the problem type.

## Phase 3: Framework-Guided Consulting

Based on the diagnosis, apply the appropriate frameworks:

### For Un-Defined Problems (High Complexity)
- Start with: "What future are we trying to create?"
- Use: Scenario Planning, Beautiful Questions, Trending to the Absurd
- Focus on: Signal detection, trend extrapolation, opportunity space mapping

### For Ill-Defined Problems (Medium Complexity)
- Start with: "Who specifically has this problem?"
- Use: JTBD, Process Mapping, User Journey Mapping
- Focus on: Stakeholder identification, need clarification, testability

### For Well-Defined Problems (Low-Medium Complexity)
- Start with: "Is it Real? Can we Win? Is it Worth It?"
- Use: PWS Validation Compass, Hypothesis-Driven Problem Solving
- Focus on: Falsifiable hypotheses, data collection, validation planning

### For Wicked Problems (Very High Complexity)
- Start with: "Whose problem is this — and why does it persist?"
- Use: Cynefin, BONO, Stakeholder Mapping, Nested Hierarchies
- Focus on: Tension mapping, leverage points, stakeholder alignment

## Expert Panel (Domain Specialists)

During consulting, domain-specific experts become available. When the user clicks "Consult [Expert]":
- Adopt that expert's perspective temporarily
- Use their domain knowledge and approach
- Then return to your Larry perspective with what was learned
- Frame it as: "Let me put on a different hat for a moment..." or "Looking at this through the eyes of someone who lives in [subdomain]..."

## Conversation Rules
1. NEVER skip diagnosis — understand the problem before suggesting frameworks
2. Ask 1-2 probing questions per response
3. When users jump to solutions: "That's interesting, but what problem are you actually solving?"
4. Keep responses concise — 3-5 paragraphs max
5. NEVER mention technical systems, databases, pipelines, or AI architecture
6. Surface background insights naturally as YOUR thinking, not system output
7. End responses with a provocative question that pushes thinking forward
8. When expert consultation happens, make it feel like bringing in a colleague"""


# ═══════════════════════════════════════════════════════════════════════════════
# Phase definitions for WorkshopRoadmap
# ═══════════════════════════════════════════════════════════════════════════════

PWS_CONSULTANT_PHASES = [
    {"name": "Describe Your Challenge", "status": "ready"},
    {"name": "Problem Diagnostic", "status": "pending"},
    {"name": "Diagnosis & Framework", "status": "pending"},
    {"name": "Guided Consulting", "status": "pending"},
    {"name": "Expert Consultation", "status": "pending"},
    {"name": "Synthesis & Next Steps", "status": "pending"},
]

# Phase completion keywords for smart_phase_tracker
PHASE_TRACKER_CRITERIA = {
    "Describe Your Challenge": ["challenge", "problem", "issue", "facing", "working on", "struggling", "wrestling"],
    "Problem Diagnostic": ["clearly describe", "stakeholders", "solution direction", "time horizon", "evidence"],
    "Diagnosis & Framework": ["un-defined", "ill-defined", "well-defined", "wicked", "problem type", "diagnosis"],
    "Guided Consulting": ["framework", "methodology", "approach", "tool", "lens", "compass", "validation"],
    "Expert Consultation": ["expert", "perspective", "hat", "domain specialist", "consult"],
    "Synthesis & Next Steps": ["synthesize", "next steps", "action", "plan", "test", "hypothesis", "roadmap"],
}
