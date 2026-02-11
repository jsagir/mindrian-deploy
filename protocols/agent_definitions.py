"""
Agent Definitions — UI Registration for All Mindrian Agents
=============================================================

All agents are registered here with their UI-specific configuration.
Adding a new agent? Just add a register_ui_agent() call here.

The orchestration-focused configs are already in agent_registry.py.
This file handles the UI layer: prompts, welcome messages, starters, triggers.
"""

from .unified_registry import UIAgentConfig, register_ui_agent


def register_all_agents():
    """
    Register all agent UI configurations.

    Called at module load. Prompts are resolved lazily to avoid
    circular imports with the prompts package.
    """
    # Import prompts lazily to avoid import-time issues
    from prompts import (
        LARRY_RAG_SYSTEM_PROMPT,
        TTA_WORKSHOP_PROMPT,
        JTBD_WORKSHOP_PROMPT,
        SCURVE_WORKSHOP_PROMPT,
        REDTEAM_PROMPT,
        ACKOFF_WORKSHOP_PROMPT,
        BONO_MASTER_PROMPT,
        KNOWN_UNKNOWNS_PROMPT,
        NESTED_HIERARCHIES_PROMPT,
        DOMAIN_EXPLORER_PROMPT,
        PWS_INVESTMENT_PROMPT,
        SCENARIO_ANALYSIS_PROMPT,
        MULTI_PERSPECTIVE_VALIDATION_PROMPT,
        BEAUTIFUL_QUESTION_PROMPT,
        GRADING_AGENT_PROMPT,
        MINTO_GRADING_PROMPT,
        MINTO_WELCOME,
        PWS_CONSULTANT_PROMPT,
    )

    # ═══════════════════════════════════════════════════════════════════════
    # LAWRENCE — Default PWS Thinking Partner
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="lawrence",
        name="Lawrence",
        icon="/public/icons/larry.svg",
        emoji="🧠",
        description="Your PWS thinking partner — focused and concise",
        system_prompt=LARRY_RAG_SYSTEM_PROMPT,
        has_phases=False,
        simple_mode=True,
        profile_order=1,
        welcome="""🧠 **What are you working on?**""",
        starters=[
            {"label": "Explore a Problem", "message": "I have a problem I want to think through", "icon": "/public/icons/explore.svg"},
            {"label": "Find a Market Gap", "message": "Help me identify problems worth solving in my industry", "icon": "/public/icons/search.svg"},
            {"label": "Challenge My Idea", "message": "I have a business idea I want you to challenge", "icon": "/public/icons/challenge.svg"},
            {"label": "What's PWS?", "message": "Explain Problems Worth Solving methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["problem", "think", "explore", "help me", "where do i start"],
        trigger_description="PWS thinking partner",
        orchestration_tags=["synthesis", "general"],
        agent_role_description="General PWS thinking partner - synthesizes and guides",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # LARRY PLAYGROUND — Full-Featured Lab
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="larry_playground",
        name="Larry Playground",
        icon="/public/icons/larry.svg",
        emoji="🔬",
        description="Full-featured PWS lab — all tools, research, multi-agent analysis",
        system_prompt=LARRY_RAG_SYSTEM_PROMPT,
        has_phases=False,
        simple_mode=False,
        profile_order=2,
        welcome="""🔬 **Welcome to the Playground!**

Think of this as your innovation laboratory. You have access to every thinking tool, research capability, and specialist AI available in Mindrian.

It's like having a team of consultants, researchers, and devil's advocates on call — ready to dig deep, challenge assumptions, and help you see what you're missing.

**What challenge are you wrestling with?**""",
        starters=[
            {"label": "Deep Research", "message": "I need deep research on a topic", "icon": "/public/icons/search.svg"},
            {"label": "Multi-Agent Analysis", "message": "Analyze my idea from multiple perspectives", "icon": "/public/icons/multi.svg"},
            {"label": "Upload & Analyze", "message": "I want to upload a document for analysis", "icon": "/public/icons/upload.svg"},
            {"label": "Explore Everything", "message": "Show me all the tools available", "icon": "/public/icons/tools.svg"},
        ],
        trigger_keywords=["playground", "full", "everything", "all tools"],
        trigger_description="Full-featured PWS lab",
        orchestration_tags=["synthesis", "general"],
        agent_role_description="Full-featured PWS lab with all tools and research",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # TTA — Trending to the Absurd
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="tta",
        name="Trending to the Absurd",
        icon="/public/icons/tta.svg",
        emoji="🔮",
        description="Guided workshop: escape presentism, find future problems",
        system_prompt=TTA_WORKSHOP_PROMPT,
        has_phases=True,
        profile_order=10,
        welcome="""🔮 **Trending to the Absurd Workshop**

Hello, I'm Larry Aronhime.

Before we dive into Trending to the Absurd, I need to understand who I'm working with.

**Tell me about yourself and your team:**

1️⃣ **Who's on this journey?**
   - Are you working alone or with a team?
   - What are your backgrounds?

2️⃣ **What's your starting point?**
   - Do you already have a domain or industry in mind?
   - Have you done any prior PWS work?

3️⃣ **What's driving this exploration?**
   - Looking for new market opportunities?
   - Anticipating disruption?
   - Exploring problems for a new venture?

I'm listening.""",
        starters=[
            {"label": "Start TTA Workshop", "message": "I'm ready to explore future trends and find emerging problems", "icon": "/public/icons/tta.svg"},
            {"label": "Explore a Trend", "message": "I want to extrapolate a specific trend to the absurd", "icon": "/public/icons/explore.svg"},
            {"label": "Technology Impact", "message": "Help me explore how a specific technology will disrupt my industry", "icon": "/public/icons/tech.svg"},
            {"label": "What is TTA?", "message": "Explain the Trending to the Absurd methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["trend", "future", "extrapolate", "absurd", "emerging", "disruption", "10 years", "what if"],
        trigger_description="Explore future trends",
        orchestration_tags=["expand_domains", "gather_perspectives", "initial_exploration"],
        agent_role_description="Future trends analyst - extrapolates and finds emerging problems",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # JTBD — Jobs to Be Done
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="jtbd",
        name="Jobs to Be Done",
        icon="/public/icons/jtbd.svg",
        emoji="🎯",
        description="Workshop: discover what customers really hire products for",
        system_prompt=JTBD_WORKSHOP_PROMPT,
        has_phases=True,
        profile_order=11,
        welcome="""🎯 **Jobs to Be Done Workshop**

Hello, I'm Larry.

Jobs to Be Done is deceptively simple — but when you really get it, you'll never look at your customers the same way.

People don't buy products — they "hire" them to make progress in their lives. That job has three dimensions:

- **Functional:** The practical task
- **Emotional:** How they want to feel
- **Social:** How they want to be perceived

**What product or service are you exploring?** Tell me about the customers you're trying to understand.""",
        starters=[
            {"label": "Start JTBD Workshop", "message": "I want to understand what job my customers are hiring my product for", "icon": "/public/icons/jtbd.svg"},
            {"label": "Customer Interviews", "message": "Help me design customer interviews to uncover jobs", "icon": "/public/icons/interview.svg"},
            {"label": "Switching Analysis", "message": "Why are customers switching from competitor products?", "icon": "/public/icons/switch.svg"},
            {"label": "What is JTBD?", "message": "Explain the Jobs to Be Done framework", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["customer", "hire", "job", "struggling", "switch", "why do people", "motivation", "emotional"],
        trigger_description="Understand customer jobs",
        orchestration_tags=["find_customer_jobs", "market_and_timing"],
        agent_role_description="Customer jobs analyst - understands what customers really need",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # S-CURVE — Technology Timing
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="scurve",
        name="S-Curve Analysis",
        icon="/public/icons/scurve.svg",
        emoji="📈",
        description="Workshop: analyze technology timing and disruption",
        system_prompt=SCURVE_WORKSHOP_PROMPT,
        has_phases=True,
        profile_order=12,
        welcome="""📈 **S-Curve Analysis Workshop**

Hello, I'm Larry.

S-Curve Analysis is about reading the clock on technology evolution.

Every technology follows an S-curve: slow start, rapid growth, eventual plateau. Get the timing right, and you ride a wave. Get it wrong, and you're either too early (running out of cash) or too late (fighting giants).

- **Era of Ferment:** Many approaches compete, no standard yet
- **Dominant Design:** Industry converges, optimization begins
- **Discontinuity:** New curve emerges, disruption happens

**What technology or industry are you analyzing?**""",
        starters=[
            {"label": "Start S-Curve Workshop", "message": "I want to analyze the timing of a technology", "icon": "/public/icons/scurve.svg"},
            {"label": "Is It Too Early?", "message": "Help me determine if my technology is too early for the market", "icon": "/public/icons/timing.svg"},
            {"label": "Disruption Watch", "message": "Identify potential disruptions in my industry", "icon": "/public/icons/disrupt.svg"},
            {"label": "What is S-Curve?", "message": "Explain S-Curve analysis methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["technology", "timing", "too early", "too late", "adoption", "s-curve", "dominant design", "era of ferment"],
        trigger_description="Analyze technology timing",
        orchestration_tags=["market_and_timing"],
        agent_role_description="Technology timing analyst - determines if timing is right",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # RED TEAM — Devil's Advocate
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="redteam",
        name="Red Teaming",
        icon="/public/icons/redteam.svg",
        emoji="😈",
        description="Devil's advocate: stress-test your assumptions",
        system_prompt=REDTEAM_PROMPT,
        has_phases=True,
        profile_order=13,
        welcome="""😈 **Red Teaming Session**

I'm Larry, and right now I'm your devil's advocate.

My job is to find the holes in your thinking before the market does. I'm going to challenge your assumptions, stress-test your logic, and look for the fatal flaw.

This isn't about being negative — it's about making your idea bulletproof.

**What idea, plan, or assumption do you want me to attack?**""",
        starters=[
            {"label": "Attack My Idea", "message": "Here's my business idea — find every flaw", "icon": "/public/icons/redteam.svg"},
            {"label": "Assumption Audit", "message": "Help me identify and test my hidden assumptions", "icon": "/public/icons/audit.svg"},
            {"label": "Pre-Mortem", "message": "Run a pre-mortem: imagine this failed — why?", "icon": "/public/icons/premortem.svg"},
            {"label": "What is Red Teaming?", "message": "Explain the Red Team methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["assumption", "risk", "fail", "challenge", "devil's advocate", "what could go wrong", "attack", "critique"],
        trigger_description="Stress-test your idea",
        orchestration_tags=["identify_assumptions", "challenge_and_validate", "final_challenge"],
        agent_role_description="Devil's advocate - finds holes and challenges assumptions",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # ACKOFF — DIKW Pyramid
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="ackoff",
        name="Ackoff's Pyramid (DIKW)",
        icon="/public/icons/ackoff.svg",
        emoji="🔺",
        description="Workshop: Climb the DIKW pyramid to validate understanding",
        system_prompt=ACKOFF_WORKSHOP_PROMPT,
        has_phases=True,
        profile_order=14,
        welcome="""🔺 **Ackoff's Pyramid Workshop**
### From Data to Wisdom — Or Catch Yourself Climbing the Wrong Ladder

Hello, I'm Larry Aronhime.

Here's a common trap: People think they have knowledge when they only have information. They think they have wisdom when they only have opinions.

Ackoff's Pyramid is like a ladder from raw data at the bottom to genuine wisdom at the top. Most people are stuck somewhere in the middle, thinking they're higher than they are.

**We can work two directions:**
- **Climb up** — Build from data to actionable understanding
- **Climb down** — Test whether your "brilliant insight" is actually grounded in reality

**Who am I working with today, and what's the challenge?**

Tell me a bit about yourself and what you're trying to figure out.""",
        starters=[
            {"label": "Start DIKW Workshop", "message": "I want to validate my understanding using the DIKW pyramid", "icon": "/public/icons/ackoff.svg"},
            {"label": "Check My Data", "message": "I have data but I'm not sure what it means", "icon": "/public/icons/data.svg"},
            {"label": "Test My Wisdom", "message": "I think I have insight — help me verify it's grounded", "icon": "/public/icons/verify.svg"},
            {"label": "What is DIKW?", "message": "Explain Ackoff's DIKW Pyramid", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["validate", "data", "wisdom", "dikw", "evidence", "ground truth", "pyramid", "understand why"],
        trigger_description="Validate with DIKW",
        orchestration_tags=["assess_market_wisdom", "apply_dikw", "challenge_and_validate", "validate_claims"],
        agent_role_description="DIKW validator - ensures decisions are grounded in data",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # BONO — Six Thinking Hats + Minto
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="bono",
        name="BONO Master",
        icon="/public/icons/bono.svg",
        emoji="🎭",
        description="Workshop: Six Thinking Hats + Minto Pyramid synthesis",
        system_prompt=BONO_MASTER_PROMPT,
        has_phases=True,
        profile_order=15,
        welcome="""🎭 **BONO Master Workshop**
### See Your Challenge Through Six Different Lenses

Hello, I'm your strategic thinking facilitator.

Imagine assembling a panel of experts — each wearing a different "thinking hat" — to examine your challenge from every angle. One focuses purely on facts, another on gut feelings, one plays devil's advocate, another looks for possibilities... and so on.

This is how companies like IBM cut meeting time by 75% while making better decisions. Instead of everyone arguing from their default position, we think in parallel — one lens at a time.

**What challenge or decision do you want this expert panel to examine?**

Tell me what's on your mind, and I'll assemble the right specialists for your situation.""",
        starters=[
            {"label": "Six Hats Analysis", "message": "Analyze my challenge using the Six Thinking Hats", "icon": "/public/icons/bono.svg"},
            {"label": "Expert Panel", "message": "I need different perspectives on a decision", "icon": "/public/icons/multi.svg"},
            {"label": "Minto Structure", "message": "Help me structure my argument using the Minto Pyramid", "icon": "/public/icons/structure.svg"},
            {"label": "What are Six Hats?", "message": "Explain the Six Thinking Hats methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["six hats", "thinking hats", "minto", "pyramid", "expert panel", "parallel thinking", "perspectives", "white hat", "black hat"],
        trigger_description="Six Hats + Minto analysis",
        orchestration_tags=["quick_perspectives"],
        agent_role_description="Parallel thinking facilitator - Six Hats structured analysis",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # KNOWN-UNKNOWNS — Rumsfeld Matrix
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="knowns",
        name="Known-Unknowns",
        icon="/public/icons/knowns.svg",
        emoji="❓",
        description="Workshop: Rumsfeld Matrix for blind spot discovery",
        system_prompt=KNOWN_UNKNOWNS_PROMPT,
        has_phases=True,
        profile_order=16,
        welcome="""🎯 **Known-Unknowns Analyzer**
### Rumsfeld Matrix + Blind Spot Discovery

Hello, I'm your uncertainty mapper.

I help you systematically categorize what you know and don't know:

- ✅ **Known Knowns**: Facts you're confident about
- ❓ **Known Unknowns**: Questions you know to ask
- 💡 **Unknown Knowns**: Tacit expertise not yet surfaced
- ⚠️ **Unknown Unknowns**: Blind spots that could derail you

**What situation, decision, or plan do you want to map?**

We'll surface hidden assumptions and discover what you don't know you don't know.""",
        starters=[
            {"label": "Map My Unknowns", "message": "Help me map what I know and don't know about my situation", "icon": "/public/icons/knowns.svg"},
            {"label": "Find Blind Spots", "message": "What am I missing that I don't know I'm missing?", "icon": "/public/icons/blind.svg"},
            {"label": "Risk Assessment", "message": "Map the uncertainty landscape of my project", "icon": "/public/icons/risk.svg"},
            {"label": "What is Rumsfeld Matrix?", "message": "Explain the Known-Unknowns framework", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["rumsfeld", "unknown unknowns", "blind spots", "knowledge gaps", "what don't we know", "uncertainty", "risk mapping"],
        trigger_description="Map unknowns & blind spots",
        orchestration_tags=["map_uncertainties"],
        agent_role_description="Uncertainty mapper - surfaces blind spots and hidden assumptions",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # NESTED HIERARCHIES — Systems Analysis
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="nested_hierarchies",
        name="Nested Hierarchies",
        icon="/public/icons/hierarchy.svg",
        emoji="🏛️",
        description="Workshop: Multi-level systems analysis for finding leverage points",
        system_prompt=NESTED_HIERARCHIES_PROMPT,
        has_phases=True,
        profile_order=17,
        welcome="""🏛️ **Nested Hierarchies Workshop**
### Seeing the System Behind the Problem

Hello, I'm Larry Aronhime.

**Here's what most people miss:** They focus on parts when they should focus on patterns. They fix batteries when the constraint is in transmission. They redesign interfaces when the friction is in the business model.

Every problem exists within a **nested hierarchy of systems**. The most consequential innovations address **reverse salients**—the constraints that hold back entire system hierarchies.

We'll work through 4 phases:
1. **Map the Hierarchy** — See the full system stack (5+ levels)
2. **Find Reverse Salients** — Identify what's really constraining growth
3. **Locate Leverage Points** — Find where intervention cascades
4. **Design the Intervention** — Act at the right level

**What problem or opportunity are you exploring?**

Tell me about the component you're focused on—I'll help you see the system around it.""",
        starters=[
            {"label": "Map System Levels", "message": "Help me map the hierarchy of systems around my problem", "icon": "/public/icons/hierarchy.svg"},
            {"label": "Find Leverage Points", "message": "Where should I intervene for maximum impact?", "icon": "/public/icons/leverage.svg"},
            {"label": "Reverse Salient", "message": "What's the bottleneck holding back my entire system?", "icon": "/public/icons/bottleneck.svg"},
            {"label": "What are Nested Hierarchies?", "message": "Explain Nested Hierarchies and reverse salients", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["hierarchy", "system", "leverage point", "reverse salient", "constraint", "cascade", "herbert simon", "donella meadows", "thomas hughes", "component", "architecture", "levels"],
        trigger_description="Multi-level systems analysis",
        orchestration_tags=[],
        agent_role_description="Systems analyst - finds leverage points in nested hierarchies",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # DOMAIN SELECTION
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="domain",
        name="Domain Selection",
        icon="/public/icons/domain.svg",
        emoji="🧭",
        description="Workshop: Domain Selection — Choose where to innovate",
        system_prompt=DOMAIN_EXPLORER_PROMPT,
        has_phases=True,
        profile_order=18,
        welcome="""🧭 **Domain Selection Workshop**
### Find Your Innovation Territory

Hello, I'm Larry Aronhime.

**Here's what most people miss:** They think domain selection is a warm-up exercise. It's not. It's the foundation. Get it wrong, and no amount of creativity will save you.

We'll work through 4 phases:
1. **Generation** — Mine your experience for candidate domains
2. **Evaluation** — Score honestly on Interest, Knowledge, Access
3. **Validation** — Test with real research and stakeholder checks
4. **Finalization** — Craft your domain statement and action plan

You can also upload a **CV** or **research paper** to discover domains automatically.

**Where are you starting from?** Do you have candidates in mind, or are you starting fresh?""",
        starters=[
            {"label": "Find My Domain", "message": "Help me identify the right domain for innovation", "icon": "/public/icons/domain.svg"},
            {"label": "Upload CV", "message": "I want to upload my CV to discover domains from my experience", "icon": "/public/icons/upload.svg"},
            {"label": "Evaluate Domains", "message": "I have some domain candidates — help me score them", "icon": "/public/icons/evaluate.svg"},
            {"label": "What is Domain Selection?", "message": "Explain the Domain Selection methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["domain selection", "choose domain", "pick domain", "domain candidate", "interest knowledge access", "where to innovate", "innovation territory", "domain statement"],
        trigger_description="Domain Selection Workshop",
        orchestration_tags=[],
        agent_role_description="Domain selection guide - helps choose where to innovate",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # PWS INVESTMENT
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="investment",
        name="PWS Investment",
        icon="/public/icons/investment.svg",
        emoji="💰",
        description="Workshop: Ten Questions + Investment Thesis evaluation",
        system_prompt=PWS_INVESTMENT_PROMPT,
        has_phases=True,
        profile_order=19,
        welcome="""💰 **Investment Analysis Workshop**
### Is This Worth Your Time and Money?

Hello, I'm your investment analyst.

Every investor has the same nightmare: falling in love with an idea and realizing too late it was fatally flawed. I help you avoid that by asking the questions that separate the winners from the wishful thinking.

Think of me as your skeptical but fair-minded partner who wants you to succeed — but won't let you fool yourself.

**What startup, opportunity, or investment are you considering?**

We'll pressure-test it together and see if it holds up.""",
        starters=[
            {"label": "Evaluate Startup", "message": "I want to evaluate a startup investment opportunity", "icon": "/public/icons/investment.svg"},
            {"label": "Investment Thesis", "message": "Help me build an investment thesis", "icon": "/public/icons/thesis.svg"},
            {"label": "Due Diligence", "message": "Run due diligence on this opportunity", "icon": "/public/icons/diligence.svg"},
            {"label": "What are the Ten Questions?", "message": "Explain the PWS investment analysis framework", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["ten questions", "investment thesis", "startup", "funding", "valuation", "due diligence", "invest", "evaluation"],
        trigger_description="PWS Investment analysis",
        orchestration_tags=[],
        agent_role_description="Investment analyst - evaluates opportunities against PWS criteria",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="scenario",
        name="Scenario Analysis",
        icon="/public/icons/scenario.svg",
        emoji="🌐",
        description="Workshop: Navigate uncertainty with multiple plausible futures",
        system_prompt=SCENARIO_ANALYSIS_PROMPT,
        has_phases=True,
        profile_order=20,
        welcome="""🌐 **Scenario Analysis Workshop**
### Navigating Uncertainty to Find Problems Worth Solving

Hello, I'm Larry.

Here's a question that should make you uncomfortable: **What if everything you believe about the future is wrong—not because you're uninformed, but because you're trapped in the present?**

Scenario Analysis is your escape route from the prison of presentism. We won't predict the future—instead, we'll systematically imagine multiple plausible futures and discover what problems would matter in each.

This is how Shell survived the 1973 oil crisis when every other oil company was blindsided. It's how you can find problems worth solving that others can't see.

**To begin: What domain or industry do you want to explore, and what strategic question is driving your interest?**""",
        starters=[
            {"label": "Start Scenario Workshop", "message": "I want to explore multiple plausible futures for my industry", "icon": "/public/icons/scenario.svg"},
            {"label": "Strategic Planning", "message": "Help me with scenario-based strategic planning", "icon": "/public/icons/strategy.svg"},
            {"label": "Uncertainty Mapping", "message": "Map the key uncertainties in my domain", "icon": "/public/icons/uncertainty.svg"},
            {"label": "What is Scenario Analysis?", "message": "Explain Scenario Analysis methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["scenario", "futures", "uncertainty", "2x2 matrix", "shell oil", "presentism", "driving forces", "multiple futures", "plausible futures", "strategic planning"],
        trigger_description="Multiple plausible futures",
        orchestration_tags=[],
        agent_role_description="Scenario planner - explores alternative futures and possibilities",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # MULTI-PERSPECTIVE VALIDATION
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="validation",
        name="Multi-Perspective Validation",
        icon="/public/icons/validate.svg",
        emoji="🎯",
        description="Workshop: Validate ideas with domain-specific Six Thinking Hats + research",
        system_prompt=MULTI_PERSPECTIVE_VALIDATION_PROMPT,
        has_phases=True,
        profile_order=21,
        welcome="""🎯 **Validation Workshop**
### Put Your Idea Through the Wringer

Hello, I'm your validation specialist.

You know that feeling when you think your idea is brilliant, but something nags at you? *"What am I missing?"* That's what this workshop answers.

Think of it like a mock trial for your idea. I'll assemble a panel of perspectives — optimists, skeptics, data analysts, creative thinkers — and each will independently research and challenge your concept. No groupthink. No echo chambers. Just rigorous, multi-angle validation.

**What idea, strategy, or decision needs validation?**

The more context you give me about your situation, the sharper the analysis will be.""",
        starters=[
            {"label": "Validate My Idea", "message": "I have an idea that needs rigorous validation", "icon": "/public/icons/validate.svg"},
            {"label": "Multi-Angle Check", "message": "Check my strategy from multiple perspectives", "icon": "/public/icons/multi.svg"},
            {"label": "Evidence Review", "message": "Do I have enough evidence to support my thesis?", "icon": "/public/icons/evidence.svg"},
            {"label": "What is Validation?", "message": "Explain the Multi-Perspective Validation methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["validate", "multi-perspective", "six hats", "evidence-based", "stress test", "parallel thinking", "hat analysis", "de bono", "ibm case", "abb case", "validation report", "challenge assumptions"],
        trigger_description="Multi-Perspective Validation",
        orchestration_tags=["final_assessment"],
        agent_role_description="Validation specialist - multi-angle evidence-based assessment",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # BEAUTIFUL QUESTION
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="beautiful_question",
        name="Beautiful Question",
        icon="/public/icons/explore.svg",
        emoji="❓",
        description="Workshop: WHY → WHAT IF → HOW breakthrough questioning methodology",
        system_prompt=BEAUTIFUL_QUESTION_PROMPT,
        has_phases=True,
        profile_order=22,
        welcome="""❓ **Beautiful Question Workshop**
### WHY → WHAT IF → HOW

Hello, I'm your Beautiful Question guide, based on Warren Berger's breakthrough methodology.

Most people jump to solutions before understanding problems. I'll help you ask better questions to find better answers.

**The Three Phases:**

🔴 **WHY Phase** — Stop and question
- Five Whys to find root causes
- Assumption mapping to surface hidden beliefs
- Vuja De to see familiar things freshly

🟡 **WHAT IF Phase** — Imagine possibilities
- Constraint removal to expand solution space
- Thinking Wrong to break patterns
- Cross-domain analogies for fresh approaches

🟢 **HOW Phase** — Move to action
- How Might We (HMW) statements
- Rapid prototyping and pretotyping
- MVP design with success metrics

**What challenge are you exploring?**

Tell me what problem you're trying to solve, and we'll start by questioning whether you're solving the right problem.""",
        starters=[
            {"label": "Start Questioning", "message": "Help me ask better questions about my challenge", "icon": "/public/icons/explore.svg"},
            {"label": "Five Whys", "message": "Run a Five Whys analysis on my problem", "icon": "/public/icons/why.svg"},
            {"label": "How Might We", "message": "Help me reframe my problem as HMW statements", "icon": "/public/icons/hmw.svg"},
            {"label": "What is Beautiful Question?", "message": "Explain Warren Berger's Beautiful Question methodology", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["beautiful question", "warren berger", "why what if how", "five whys", "root cause", "what if", "how might we", "hmw", "assumption challenge", "constraint removal", "vuja de", "questioning"],
        trigger_description="WHY → WHAT IF → HOW questioning",
        orchestration_tags=[],
        agent_role_description="Questioning facilitator - WHY, WHAT IF, HOW breakthrough methodology",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # GRADING AGENTS
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="grading",
        name="Problem Discovery Grading",
        icon="/public/icons/grading.svg",
        emoji="🎓",
        description="Grade student work on problem discovery and validation methodology",
        system_prompt=GRADING_AGENT_PROMPT,
        has_phases=False,
        simple_mode=False,
        profile_order=30,
        welcome="""🎓 **Problem Discovery Grading**
### Did You Find a Real Problem Worth Solving?

Hello, I'm your grading assistant.

My job is simple: determine whether you've found a **real problem** that real people actually have. Not just an interesting idea. Not just something that sounds good on paper. A real problem, validated with real evidence.

I'll look at:
- Did you prove the problem exists? (This is most of the grade)
- Did you discover multiple problems before picking one?
- Did you use the right thinking tools?
- Did you find connections others might miss?

**Upload your work (PDF, DOCX, or TXT) or paste it directly.**

I'll give you honest feedback on where you nailed it and where you have gaps.""",
        starters=[
            {"label": "Grade My Work", "message": "I want to upload my problem discovery work for grading", "icon": "/public/icons/grading.svg"},
            {"label": "Rubric Explained", "message": "What rubric do you use to grade problem discovery?", "icon": "/public/icons/rubric.svg"},
            {"label": "Improve My Score", "message": "What are the most common gaps in student work?", "icon": "/public/icons/improve.svg"},
            {"label": "Sample Grade", "message": "Show me an example of an A-grade problem discovery", "icon": "/public/icons/example.svg"},
        ],
        trigger_keywords=["grade", "score", "rubric", "evaluate", "rate"],
        trigger_description="Grade problem discovery work",
        orchestration_tags=["grade_document"],
        agent_role_description="Grading service - evaluates problem discovery against PWS rubric",
    ))

    register_ui_agent(UIAgentConfig(
        id="minto",
        name="Minto Problem Discovery Grading",
        icon="/public/icons/grading.svg",
        emoji="📊",
        description="One-shot autonomous grading focused on problem reality validation",
        system_prompt=MINTO_GRADING_PROMPT,
        has_phases=False,
        simple_mode=False,
        profile_order=31,
        welcome=MINTO_WELCOME,
        starters=[
            {"label": "Grade My Submission", "message": "I want to submit my work for Minto-style grading", "icon": "/public/icons/grading.svg"},
            {"label": "What is Minto Grading?", "message": "Explain the Minto grading methodology", "icon": "/public/icons/info.svg"},
            {"label": "Upload Document", "message": "I'll upload my problem discovery document", "icon": "/public/icons/upload.svg"},
            {"label": "Grade Criteria", "message": "What criteria does the Minto grading focus on?", "icon": "/public/icons/rubric.svg"},
        ],
        trigger_keywords=[],
        trigger_description="",
        orchestration_tags=[],
        agent_role_description="Minto grading - autonomous problem reality validation",
    ))

    # ═══════════════════════════════════════════════════════════════════════
    # PWS CONSULTANT
    # ═══════════════════════════════════════════════════════════════════════
    register_ui_agent(UIAgentConfig(
        id="pws_consultant",
        name="PWS Consultant",
        icon="/public/icons/explore.svg",
        emoji="🩺",
        description="Structured problem diagnosis: classify your challenge, get targeted framework guidance with domain experts",
        system_prompt=PWS_CONSULTANT_PROMPT,
        has_phases=False,
        simple_mode=False,
        profile_order=3,
        welcome="""🩺 **PWS Consultant**
### Problems Before Solutions — Always.

Hello, I'm Larry Aronhime.

Most people jump to solutions too fast. Let's start where it matters — *with the problem itself*.

Here's how this works: You'll tell me about your challenge, I'll run a quick diagnostic to understand what kind of problem you're dealing with, and then we'll work through it together using exactly the right frameworks for your situation.

Along the way, I'll bring in domain-specific perspectives — think of them as colleagues with different expertise who can offer fresh angles on your challenge.

**What's the challenge you're wrestling with?**

Don't worry about being precise — that's what we'll work on together.""",
        starters=[
            {"label": "Diagnose My Problem", "message": "I have a challenge and I'm not sure what kind of problem it is", "icon": "/public/icons/explore.svg"},
            {"label": "Framework Help", "message": "Which PWS framework should I use for my situation?", "icon": "/public/icons/framework.svg"},
            {"label": "Expert Panel", "message": "I need domain-specific expert perspectives on my challenge", "icon": "/public/icons/multi.svg"},
            {"label": "What is PWS Consulting?", "message": "How does the structured consulting process work?", "icon": "/public/icons/info.svg"},
        ],
        trigger_keywords=["diagnose", "classify", "problem type", "what kind of problem", "consultant", "structured help",
                          "which framework", "not sure where to start", "need guidance", "confused about approach",
                          "expert panel", "domain experts"],
        trigger_description="Structured problem diagnosis & guided consulting",
        orchestration_tags=[],
        agent_role_description="Structured problem diagnosis with domain-specific expert panels",
    ))


    # ──────────────────────────────────────────────────────
    # MACRO-CHANGES ANALYSIS
    # ──────────────────────────────────────────────────────
    try:
        from prompts.macro_changes import MACRO_CHANGES_PROMPT
    except ImportError:
        MACRO_CHANGES_PROMPT = None

    if MACRO_CHANGES_PROMPT:
        register_ui_agent(UIAgentConfig(
            id="macro_changes",
            name="Macro-Changes Analysis",
            description="Analyze macro-level changes in a domain — PEST systems, destruction, multi-order consequences, and emerging problems worth solving",
            icon="/public/icons/industry.svg",
            emoji="🌍",
            system_prompt=MACRO_CHANGES_PROMPT,
            has_phases=True,
            welcome="""**🌍 Welcome to Macro-Changes Analysis**

We're going to look at the macro-level changes reshaping a domain and trace them to their consequences.

Most people see change and react. We're going to see change and **hunt for what it destroys** — because destruction creates the next generation of problems worth solving.

**Tell me: What domain or industry are you interested in exploring?**""",
            profile_order=25,
            starters=[
                {"label": "Analyze my industry", "message": "I want to analyze the macro-changes reshaping my industry and find opportunities in what's being destroyed.", "icon": "/public/icons/industry.svg"},
                {"label": "PEST systems analysis", "message": "Help me build a PEST systems diagram for the major changes happening in my domain.", "icon": "/public/icons/map.svg"},
                {"label": "Find what's being destroyed", "message": "I see changes happening but I can't figure out what's actually being destroyed. Help me trace the consequences.", "icon": "/public/icons/search.svg"},
                {"label": "Show me the method", "message": "Walk me through the Macro-Changes Analysis methodology with an example.", "icon": "/public/icons/example.svg"},
            ],
            trigger_keywords=["macro-change", "macro change", "pest analysis", "pest framework",
                              "what is being destroyed", "systemic change", "destruction",
                              "first order", "second order", "third order", "consequences",
                              "political economic social technological", "macro level"],
            trigger_description="Analyze macro-level changes and find opportunities in destruction",
            orchestration_tags=["explore", "macro", "systemic"],
            agent_role_description="Macro-changes analyst — maps PEST forces, destruction, multi-order consequences, and emerging opportunities",
        ))

    # ──────────────────────────────────────────────────────
    # DOMINANT DESIGNS
    # ──────────────────────────────────────────────────────
    try:
        from prompts.dominant_designs import DOMINANT_DESIGNS_PROMPT
    except ImportError:
        DOMINANT_DESIGNS_PROMPT = None

    if DOMINANT_DESIGNS_PROMPT:
        register_ui_agent(UIAgentConfig(
            id="dominant_designs",
            name="Dominant Designs",
            description="Find where dominant designs are falling apart — discontinuities, S-curve limits, and opportunities for what comes next",
            icon="/public/icons/design.svg",
            emoji="🏗️",
            system_prompt=DOMINANT_DESIGNS_PROMPT,
            has_phases=True,
            welcome="""**🏗️ Welcome to Dominant Designs Analysis**

Every industry has dominant designs — the standard way things are done. And every dominant design eventually falls apart.

We're going to find where that's happening in your domain, understand why it's breaking, and discover the problems worth solving in the transition.

**Tell me: What domain or industry are you interested in exploring?**""",
            profile_order=26,
            starters=[
                {"label": "Find crumbling designs", "message": "I want to identify where dominant designs in my industry are starting to fall apart.", "icon": "/public/icons/design.svg"},
                {"label": "S-curve analysis", "message": "Is there a technology or product in my domain reaching its physical or market limit?", "icon": "/public/icons/chart.svg"},
                {"label": "What comes next?", "message": "I see an old standard dying. Help me figure out what the new dominant design could be.", "icon": "/public/icons/future.svg"},
                {"label": "Show me the method", "message": "Walk me through the Dominant Designs methodology with a classic example.", "icon": "/public/icons/example.svg"},
            ],
            trigger_keywords=["dominant design", "standard design", "falling apart", "breaking apart",
                              "design paradigm", "industry standard", "disruption", "discontinuity",
                              "new design", "replacing the standard", "what comes next",
                              "physical limit", "market limit", "obsolete"],
            trigger_description="Analyze where dominant designs are crumbling and what replaces them",
            orchestration_tags=["explore", "disruption", "scurve"],
            agent_role_description="Dominant designs analyst — identifies crumbling standards, S-curve limits, discontinuities, and opportunities for new paradigms",
        ))

    # ──────────────────────────────────────────────────────
    # UNDERSTANDING USER NEEDS
    # ──────────────────────────────────────────────────────
    try:
        from prompts.user_needs import USER_NEEDS_PROMPT
    except ImportError:
        USER_NEEDS_PROMPT = None

    if USER_NEEDS_PROMPT:
        register_ui_agent(UIAgentConfig(
            id="user_needs",
            name="Understanding User Needs",
            description="Map user processes, rate importance vs satisfaction, find high-gap opportunities, and understand what prevents improvement",
            icon="/public/icons/product.svg",
            emoji="👤",
            system_prompt=USER_NEEDS_PROMPT,
            has_phases=True,
            welcome="""**👤 Welcome to Understanding User Needs**

We're going to map a real user experience step by step, find where importance is high but satisfaction is low, and discover what's preventing improvement.

This is where product opportunities live — in the gaps between what matters and what works.

**Tell me: What domain do you know well? Preferably one that others may not know as deeply.**""",
            profile_order=27,
            starters=[
                {"label": "Map a user process", "message": "I want to map out a user process in my domain and find the pain points.", "icon": "/public/icons/map.svg"},
                {"label": "Importance vs satisfaction", "message": "Help me rate the steps in a process by importance and satisfaction to find opportunities.", "icon": "/public/icons/chart.svg"},
                {"label": "Find the real barriers", "message": "I know where users struggle but I can't figure out why it hasn't been fixed. Help me find the barriers.", "icon": "/public/icons/search.svg"},
                {"label": "Show me the method", "message": "Walk me through the Understanding User Needs methodology with an example.", "icon": "/public/icons/example.svg"},
            ],
            trigger_keywords=["user needs", "process map", "user process", "importance satisfaction",
                              "user experience", "pain point", "gap analysis", "user journey",
                              "satisfaction rating", "what prevents improvement", "user pain",
                              "process mapping", "high importance low satisfaction"],
            trigger_description="Map user processes and find high-importance, low-satisfaction opportunities",
            orchestration_tags=["explore", "jtbd", "user_research"],
            agent_role_description="User needs analyst — maps processes, identifies importance-satisfaction gaps, traces root causes and barriers to find actionable opportunities",
        ))


# Auto-register all agents at module load
register_all_agents()
