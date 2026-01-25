"""
Mindrian - Multi-Bot PWS Platform
Larry Core + Specialized Tool Workshop Bots
Enhanced with Task Lists, Action Buttons, File Upload, Charts, Data Persistence,
Chain-of-Thought Steps, Conversation Starters, and Session Resume
"""

import os
import json
import asyncio
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

from google import genai
from google.genai import types

# === Config ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# Chainlit uses CHAINLIT_DATABASE_URL, fallback to DATABASE_URL for compatibility
DATABASE_URL = os.getenv("CHAINLIT_DATABASE_URL") or os.getenv("DATABASE_URL")

client = genai.Client(api_key=GOOGLE_API_KEY)

# === Stop Event for Cancellation ===
stop_events: Dict[str, asyncio.Event] = {}

# === Context Preservation for Profile Switching ===
# Store conversation history by user/thread to persist across bot switches
context_store: Dict[str, Dict[str, Any]] = {}

# === Agent Suggestion Keywords ===
# Maps keywords/phrases to suggested agents
AGENT_TRIGGERS = {
    "tta": {
        "keywords": ["trend", "future", "extrapolate", "absurd", "emerging", "disruption", "10 years", "what if"],
        "description": "Explore future trends"
    },
    "jtbd": {
        "keywords": ["customer", "hire", "job", "struggling", "switch", "why do people", "motivation", "emotional"],
        "description": "Understand customer jobs"
    },
    "scurve": {
        "keywords": ["technology", "timing", "too early", "too late", "adoption", "s-curve", "dominant design", "era of ferment"],
        "description": "Analyze technology timing"
    },
    "redteam": {
        "keywords": ["assumption", "risk", "fail", "challenge", "devil's advocate", "what could go wrong", "attack", "critique"],
        "description": "Stress-test your idea"
    },
    "ackoff": {
        "keywords": ["validate", "data", "wisdom", "dikw", "evidence", "ground truth", "pyramid", "understand why"],
        "description": "Validate with DIKW"
    },
    "bono": {
        "keywords": ["six hats", "thinking hats", "minto", "pyramid", "expert panel", "parallel thinking", "perspectives", "white hat", "black hat"],
        "description": "Six Hats + Minto analysis"
    },
    "knowns": {
        "keywords": ["rumsfeld", "unknown unknowns", "blind spots", "knowledge gaps", "what don't we know", "uncertainty", "risk mapping"],
        "description": "Map unknowns & blind spots"
    },
    "domain": {
        "keywords": ["deep research", "multi-domain", "cross-domain", "comprehensive research", "exhaustive", "15 searches", "synthesis"],
        "description": "Exhaustive domain research"
    },
    "investment": {
        "keywords": ["ten questions", "investment thesis", "startup", "funding", "valuation", "due diligence", "invest", "evaluation"],
        "description": "PWS Investment analysis"
    },
    "scenario": {
        "keywords": ["scenario", "futures", "uncertainty", "2x2 matrix", "shell oil", "presentism", "driving forces", "multiple futures", "plausible futures", "strategic planning"],
        "description": "Multiple plausible futures"
    },
}

# === Data Persistence Setup ===
if DATABASE_URL:
    try:
        from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

        # Convert postgresql:// to postgresql+asyncpg:// for async support
        db_url = DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        # Initialize SQLAlchemy data layer for conversation persistence
        cl.data._data_layer = SQLAlchemyDataLayer(
            conninfo=db_url,
            ssl_require=True
        )
        print("✅ Data persistence enabled with PostgreSQL (asyncpg)")
    except Exception as e:
        print(f"⚠️ Data persistence disabled: {e}")
else:
    print("ℹ️ Data persistence disabled (no DATABASE_URL)")

# === System Prompts ===
from prompts import (
    LARRY_RAG_SYSTEM_PROMPT,
    TTA_WORKSHOP_PROMPT,
    JTBD_WORKSHOP_PROMPT,
    SCURVE_WORKSHOP_PROMPT,
    REDTEAM_PROMPT,
    ACKOFF_WORKSHOP_PROMPT,
    BONO_MASTER_PROMPT,
    KNOWN_UNKNOWNS_PROMPT,
    DOMAIN_EXPLORER_PROMPT,
    PWS_INVESTMENT_PROMPT,
    SCENARIO_ANALYSIS_PROMPT
)

# === RAG Cache Support ===
try:
    from utils.gemini_rag import get_cache_name
    RAG_ENABLED = True
except ImportError:
    RAG_ENABLED = False
    def get_cache_name(workshop_id):
        return None

# === Workshop Phase Definitions ===
WORKSHOP_PHASES = {
    "tta": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Domain & Trends", "status": "pending"},
        {"name": "Deep Research", "status": "pending"},
        {"name": "Absurd Extrapolation", "status": "pending"},
        {"name": "Problem Hunting", "status": "pending"},
        {"name": "Opportunity Validation", "status": "pending"},
        {"name": "Action Planning", "status": "pending"},
        {"name": "Reflection", "status": "pending"},
    ],
    "jtbd": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Struggling Moment", "status": "pending"},
        {"name": "Functional Job", "status": "pending"},
        {"name": "Emotional Job", "status": "pending"},
        {"name": "Social Job", "status": "pending"},
        {"name": "Competing Solutions", "status": "pending"},
        {"name": "Job Statement", "status": "pending"},
    ],
    "scurve": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Technology Identification", "status": "pending"},
        {"name": "Era Assessment", "status": "pending"},
        {"name": "Evidence Gathering", "status": "pending"},
        {"name": "Ecosystem Readiness", "status": "pending"},
        {"name": "Timing Decision", "status": "pending"},
    ],
    "redteam": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Assumption Extraction", "status": "pending"},
        {"name": "Assumption Ranking", "status": "pending"},
        {"name": "Attack Mode", "status": "pending"},
        {"name": "Competition & Alternatives", "status": "pending"},
        {"name": "Failure Modes", "status": "pending"},
        {"name": "Strengthening", "status": "pending"},
    ],
    "ackoff": [
        {"name": "Team Onboarding", "status": "ready"},
        {"name": "Direction Choice", "status": "pending"},
        {"name": "Data Level", "status": "pending"},
        {"name": "Information Level", "status": "pending"},
        {"name": "Knowledge Level", "status": "pending"},
        {"name": "Understanding Level", "status": "pending"},
        {"name": "Wisdom Level", "status": "pending"},
        {"name": "Validation & Action", "status": "pending"},
    ],
    "bono": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Persona Generation", "status": "pending"},
        {"name": "White Hat Analysis", "status": "pending"},
        {"name": "Red Hat Analysis", "status": "pending"},
        {"name": "Black Hat Analysis", "status": "pending"},
        {"name": "Yellow Hat Analysis", "status": "pending"},
        {"name": "Green Hat Analysis", "status": "pending"},
        {"name": "Blue Hat Synthesis", "status": "pending"},
        {"name": "Panel Discussion", "status": "pending"},
        {"name": "Breakthrough Recommendations", "status": "pending"},
    ],
    "knowns": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Context Gathering", "status": "pending"},
        {"name": "Known Knowns Audit", "status": "pending"},
        {"name": "Known Unknowns Mapping", "status": "pending"},
        {"name": "Unknown Knowns Surfacing", "status": "pending"},
        {"name": "Unknown Unknowns Discovery", "status": "pending"},
        {"name": "Risk Assessment", "status": "pending"},
        {"name": "Action Planning", "status": "pending"},
    ],
    "domain": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Scope Definition", "status": "pending"},
        {"name": "Domain Mapping", "status": "pending"},
        {"name": "Primary Research", "status": "pending"},
        {"name": "Adjacent Research", "status": "pending"},
        {"name": "Cross-Domain Research", "status": "pending"},
        {"name": "Dissent Collection", "status": "pending"},
        {"name": "Synthesis", "status": "pending"},
        {"name": "Gap Identification", "status": "pending"},
        {"name": "Insight Generation", "status": "pending"},
    ],
    "investment": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Scope Definition", "status": "pending"},
        {"name": "Ten Questions Part 1", "status": "pending"},
        {"name": "Ten Questions Part 2", "status": "pending"},
        {"name": "Go/No-Go Decision", "status": "pending"},
        {"name": "Thesis: Business & Team", "status": "pending"},
        {"name": "Thesis: Market & GTM", "status": "pending"},
        {"name": "Thesis: Competition & Value", "status": "pending"},
        {"name": "Adversarial Review", "status": "pending"},
        {"name": "Final Recommendation", "status": "pending"},
    ],
    "scenario": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Domain & Driving Forces", "status": "pending"},
        {"name": "Uncertainty Assessment", "status": "pending"},
        {"name": "Scenario Matrix (2×2)", "status": "pending"},
        {"name": "Scenario Narratives", "status": "pending"},
        {"name": "Synthesis & Implications", "status": "pending"},
    ],
}

# === Bot Configurations ===
BOTS = {
    "larry": {
        "name": "Larry",
        "icon": "/public/icons/larry.svg",
        "emoji": "🧠",  # Keep emoji for inline use
        "description": "General PWS thinking partner",
        "system_prompt": LARRY_RAG_SYSTEM_PROMPT,
        "has_phases": False,
        "welcome": """🧠 **Welcome to Mindrian!**

I'm Larry, your thinking partner. I help people identify problems worth solving before they chase solutions.

Before solutions, I ask questions. Let's make sure we're solving the right problem.

**What are you working on?**"""
    },
    "tta": {
        "name": "Trending to the Absurd",
        "icon": "/public/icons/tta.svg",
        "emoji": "🔮",
        "description": "Guided workshop: escape presentism, find future problems",
        "system_prompt": TTA_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """🔮 **Trending to the Absurd Workshop**

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

I'm listening."""
    },
    "jtbd": {
        "name": "Jobs to Be Done",
        "icon": "/public/icons/jtbd.svg",
        "emoji": "🎯",
        "description": "Workshop: discover what customers really hire products for",
        "system_prompt": JTBD_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """🎯 **Jobs to Be Done Workshop**

Hello, I'm Larry.

Jobs to Be Done is deceptively simple — but when you really get it, you'll never look at your customers the same way.

People don't buy products — they "hire" them to make progress in their lives. That job has three dimensions:

- **Functional:** The practical task
- **Emotional:** How they want to feel
- **Social:** How they want to be perceived

**What product or service are you exploring?** Tell me about the customers you're trying to understand."""
    },
    "scurve": {
        "name": "S-Curve Analysis",
        "icon": "/public/icons/scurve.svg",
        "emoji": "📈",
        "description": "Workshop: analyze technology timing and disruption",
        "system_prompt": SCURVE_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """📈 **S-Curve Analysis Workshop**

Hello, I'm Larry.

S-Curve Analysis is about reading the clock on technology evolution.

Every technology follows an S-curve: slow start, rapid growth, eventual plateau. Get the timing right, and you ride a wave. Get it wrong, and you're either too early (running out of cash) or too late (fighting giants).

- **Era of Ferment:** Many approaches compete, no standard yet
- **Dominant Design:** Industry converges, optimization begins
- **Discontinuity:** New curve emerges, disruption happens

**What technology or industry are you analyzing?**"""
    },
    "redteam": {
        "name": "Red Teaming",
        "icon": "/public/icons/redteam.svg",
        "emoji": "😈",
        "description": "Devil's advocate: stress-test your assumptions",
        "system_prompt": REDTEAM_PROMPT,
        "has_phases": True,
        "welcome": """😈 **Red Teaming Session**

I'm Larry, and right now I'm your devil's advocate.

My job is to find the holes in your thinking before the market does. I'm going to challenge your assumptions, stress-test your logic, and look for the fatal flaw.

This isn't about being negative — it's about making your idea bulletproof.

**What idea, plan, or assumption do you want me to attack?**"""
    },
    "ackoff": {
        "name": "Ackoff's Pyramid (DIKW)",
        "icon": "/public/icons/ackoff.svg",
        "emoji": "🔺",
        "description": "Workshop: Climb the DIKW pyramid to validate understanding",
        "system_prompt": ACKOFF_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """🔺 **Ackoff's Pyramid Workshop**
### The DIKW Validation Method

Hello. I'm Larry Aronhime.

Before we do anything else, I need to understand who I'm working with.

The DIKW Pyramid helps you climb from raw **Data** → **Information** → **Knowledge** → **Understanding** → **Wisdom**.

Or, if you already have a solution, we'll **climb down** to validate it's actually grounded in reality.

**Tell me about yourself/your team:**

1️⃣ **Who am I talking to?**
   → Individual or team? What roles?

2️⃣ **What's your domain?**
   → Industry, organization, product area?

3️⃣ **What's at stake?**
   → What happens if you get this wrong?

4️⃣ **What's your timeline?**
   → When do you need to act?

I'm listening."""
    },
    "bono": {
        "name": "BONO Master",
        "icon": "/public/icons/bono.svg",
        "emoji": "🎭",
        "description": "Workshop: Six Thinking Hats + Minto Pyramid synthesis",
        "system_prompt": BONO_MASTER_PROMPT,
        "has_phases": True,
        "welcome": """🎭 **BONO Master Workshop**
### Six Thinking Hats + Minto Pyramid + Expert Panels

Hello, I'm your BONO Master facilitator.

I orchestrate comprehensive strategic analysis by combining:
- **Domain-specific expert personas** tailored to your challenge
- **Six Thinking Hats** for parallel perspective exploration
- **Minto Pyramid** for structured synthesis
- **Expert Panel Discussions** for breakthrough insights

**Tell me about the challenge or decision you're facing.**

I'll generate a custom expert panel and guide you through a systematic exploration from multiple angles."""
    },
    "knowns": {
        "name": "Known-Unknowns",
        "icon": "/public/icons/knowns.svg",
        "emoji": "❓",
        "description": "Workshop: Rumsfeld Matrix for blind spot discovery",
        "system_prompt": KNOWN_UNKNOWNS_PROMPT,
        "has_phases": True,
        "welcome": """🎯 **Known-Unknowns Analyzer**
### Rumsfeld Matrix + Blind Spot Discovery

Hello, I'm your uncertainty mapper.

I help you systematically categorize what you know and don't know:

- ✅ **Known Knowns**: Facts you're confident about
- ❓ **Known Unknowns**: Questions you know to ask
- 💡 **Unknown Knowns**: Tacit expertise not yet surfaced
- ⚠️ **Unknown Unknowns**: Blind spots that could derail you

**What situation, decision, or plan do you want to map?**

We'll surface hidden assumptions and discover what you don't know you don't know."""
    },
    "domain": {
        "name": "Domain Explorer",
        "icon": "/public/icons/domain.svg",
        "emoji": "🔍",
        "description": "Workshop: Exhaustive multi-domain research synthesis",
        "system_prompt": DOMAIN_EXPLORER_PROMPT,
        "has_phases": True,
        "welcome": """🔍 **Domain Explorer**
### Exhaustive Research + Cross-Domain Synthesis

Hello, I'm your systematic researcher.

I conduct comprehensive multi-domain exploration:
- **15-20+ strategic searches** across domains
- **Multiple lenses**: disciplinary, stakeholder, temporal, scale
- **Both supporting AND dissenting evidence**
- **Cross-domain synthesis** for non-obvious connections

**What topic do you want to explore exhaustively?**

Whether it's a technology, market, problem, or opportunity, I'll map the full landscape."""
    },
    "investment": {
        "name": "PWS Investment",
        "icon": "/public/icons/investment.svg",
        "emoji": "💰",
        "description": "Workshop: Ten Questions + Investment Thesis evaluation",
        "system_prompt": PWS_INVESTMENT_PROMPT,
        "has_phases": True,
        "welcome": """💰 **PWS Investment Analysis**
### Ten Questions + Investment Thesis

Hello, I'm your rigorous investment analyst.

I evaluate opportunities using the PWS framework:
1. **Ten Questions Rapid Assessment** - Must pass 8/10 to proceed
2. **Investment Thesis Deep Analysis** - 6 comprehensive categories
3. **Devil's Advocate Integration** - Every positive challenged

**What startup, opportunity, or investment are you evaluating?**

I'll systematically assess whether this is worth pursuing and why."""
    },
    "scenario": {
        "name": "Scenario Analysis",
        "icon": "/public/icons/scenario.svg",
        "emoji": "🌐",
        "description": "Workshop: Navigate uncertainty with multiple plausible futures",
        "system_prompt": SCENARIO_ANALYSIS_PROMPT,
        "has_phases": True,
        "welcome": """🌐 **Scenario Analysis Workshop**
### Navigating Uncertainty to Find Problems Worth Solving

Hello, I'm Larry.

Here's a question that should make you uncomfortable: **What if everything you believe about the future is wrong—not because you're uninformed, but because you're trapped in the present?**

Scenario Analysis is your escape route from the prison of presentism. We won't predict the future—instead, we'll systematically imagine multiple plausible futures and discover what problems would matter in each.

This is how Shell survived the 1973 oil crisis when every other oil company was blindsided. It's how you can find problems worth solving that others can't see.

**To begin: What domain or industry do you want to explore, and what strategic question is driving your interest?**"""
    }
}


async def create_task_list(profile: str) -> Optional[cl.TaskList]:
    """Create a task list for workshop phases."""
    if profile not in WORKSHOP_PHASES:
        return None

    task_list = cl.TaskList()
    task_list.name = "Workshop Progress"

    for phase in WORKSHOP_PHASES[profile]:
        status = cl.TaskStatus.READY if phase["status"] == "ready" else cl.TaskStatus.RUNNING if phase["status"] == "running" else cl.TaskStatus.DONE if phase["status"] == "done" else cl.TaskStatus.READY
        task = cl.Task(title=phase["name"], status=status)
        await task_list.add_task(task)

    return task_list


async def update_phase(profile: str, phase_index: int, new_status: str):
    """Update a workshop phase status."""
    phases = cl.user_session.get("phases", [])
    if phase_index < len(phases):
        phases[phase_index]["status"] = new_status
        cl.user_session.set("phases", phases)

        # Recreate task list with updated statuses
        task_list = cl.TaskList()
        task_list.name = "Workshop Progress"

        for i, phase in enumerate(phases):
            if phase["status"] == "done":
                status = cl.TaskStatus.DONE
            elif phase["status"] == "running":
                status = cl.TaskStatus.RUNNING
            elif i == phase_index:
                status = cl.TaskStatus.RUNNING
            else:
                status = cl.TaskStatus.READY
            task = cl.Task(title=phase["name"], status=status)
            await task_list.add_task(task)

        await task_list.send()


@cl.set_chat_profiles
async def chat_profiles():
    """Define available bot profiles."""
    return [
        cl.ChatProfile(
            name="larry",
            markdown_description=BOTS["larry"]["description"],
            icon=BOTS["larry"]["icon"],
        ),
        cl.ChatProfile(
            name="tta",
            markdown_description=BOTS["tta"]["description"],
            icon=BOTS["tta"]["icon"],
        ),
        cl.ChatProfile(
            name="jtbd",
            markdown_description=BOTS["jtbd"]["description"],
            icon=BOTS["jtbd"]["icon"],
        ),
        cl.ChatProfile(
            name="scurve",
            markdown_description=BOTS["scurve"]["description"],
            icon=BOTS["scurve"]["icon"],
        ),
        cl.ChatProfile(
            name="redteam",
            markdown_description=BOTS["redteam"]["description"],
            icon=BOTS["redteam"]["icon"],
        ),
        cl.ChatProfile(
            name="ackoff",
            markdown_description=BOTS["ackoff"]["description"],
            icon=BOTS["ackoff"]["icon"],
        ),
        cl.ChatProfile(
            name="bono",
            markdown_description=BOTS["bono"]["description"],
            icon=BOTS["bono"]["icon"],
        ),
        cl.ChatProfile(
            name="knowns",
            markdown_description=BOTS["knowns"]["description"],
            icon=BOTS["knowns"]["icon"],
        ),
        cl.ChatProfile(
            name="domain",
            markdown_description=BOTS["domain"]["description"],
            icon=BOTS["domain"]["icon"],
        ),
        cl.ChatProfile(
            name="investment",
            markdown_description=BOTS["investment"]["description"],
            icon=BOTS["investment"]["icon"],
        ),
        cl.ChatProfile(
            name="scenario",
            markdown_description=BOTS["scenario"]["description"],
            icon=BOTS["scenario"]["icon"],
        ),
    ]


# === Conversation Starters ===
STARTERS = {
    "larry": [
        cl.Starter(
            label="Explore a problem",
            message="I have a challenge I'm facing and need help thinking through it systematically.",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="Validate an idea",
            message="I have a solution idea and want to validate if it's worth pursuing.",
            icon="/public/icons/validate.svg",
        ),
        cl.Starter(
            label="Find the right problem",
            message="I'm not sure I'm solving the right problem. Help me step back and examine this.",
            icon="/public/icons/search.svg",
        ),
        cl.Starter(
            label="Challenge my thinking",
            message="I want you to challenge my assumptions and help me see blind spots.",
            icon="/public/icons/challenge.svg",
        ),
    ],
    "tta": [
        cl.Starter(
            label="Start with a trend",
            message="I've identified a trend I want to push to its absurd conclusion: [describe your trend]",
            icon="/public/icons/trend.svg",
        ),
        cl.Starter(
            label="Find emerging problems",
            message="Help me discover problems that don't exist yet by extrapolating current trends.",
            icon="/public/icons/future.svg",
        ),
        cl.Starter(
            label="Analyze my industry",
            message="I want to apply Trending to the Absurd to my industry. Let's start with what's changing.",
            icon="/public/icons/industry.svg",
        ),
        cl.Starter(
            label="Show an example",
            message="Show me how the Trending to the Absurd method works with a concrete example.",
            icon="/public/icons/example.svg",
        ),
    ],
    "jtbd": [
        cl.Starter(
            label="Analyze a product",
            message="I want to understand what job my customers are really hiring my product for.",
            icon="/public/icons/product.svg",
        ),
        cl.Starter(
            label="Find the struggling moment",
            message="Help me identify the struggling moment that triggers my customers to seek a solution.",
            icon="/public/icons/struggle.svg",
        ),
        cl.Starter(
            label="Map the full job",
            message="I want to map the functional, emotional, and social dimensions of my customer's job.",
            icon="/public/icons/map.svg",
        ),
        cl.Starter(
            label="See an example",
            message="Show me a Jobs to Be Done analysis example to understand the framework better.",
            icon="/public/icons/example.svg",
        ),
    ],
    "scurve": [
        cl.Starter(
            label="Analyze a technology",
            message="I want to determine where a specific technology sits on its S-curve.",
            icon="/public/icons/tech.svg",
        ),
        cl.Starter(
            label="Timing assessment",
            message="Help me figure out if I'm too early, too late, or right on time for my technology bet.",
            icon="/public/icons/timing.svg",
        ),
        cl.Starter(
            label="Find the dominant design",
            message="I need to identify whether a dominant design has emerged in my market.",
            icon="/public/icons/design.svg",
        ),
        cl.Starter(
            label="Show the S-curve",
            message="Explain the S-curve framework and show me how to read it.",
            icon="/public/icons/chart.svg",
        ),
    ],
    "redteam": [
        cl.Starter(
            label="Attack my idea",
            message="I have a business idea and I need you to find every hole in it. Here it is: [describe idea]",
            icon="/public/icons/attack.svg",
        ),
        cl.Starter(
            label="Extract assumptions",
            message="Help me identify all the hidden assumptions underlying my plan.",
            icon="/public/icons/extract.svg",
        ),
        cl.Starter(
            label="Find failure modes",
            message="Walk me through all the ways my project could fail.",
            icon="/public/icons/failure.svg",
        ),
        cl.Starter(
            label="Competitive threats",
            message="Analyze the competitive landscape and show me who could crush my idea.",
            icon="/public/icons/compete.svg",
        ),
    ],
    "ackoff": [
        cl.Starter(
            label="Validate a solution",
            message="I have a proposed solution I want to validate by climbing down the DIKW pyramid.",
            icon="/public/icons/validate.svg",
        ),
        cl.Starter(
            label="Explore a problem",
            message="I want to climb up the pyramid to understand a problem better before solving it.",
            icon="/public/icons/climb.svg",
        ),
        cl.Starter(
            label="Show the pyramid",
            message="Explain Ackoff's DIKW pyramid and how to use it for validation.",
            icon="/public/icons/pyramid.svg",
        ),
        cl.Starter(
            label="See an example",
            message="Show me a real example of DIKW validation in action.",
            icon="/public/icons/example.svg",
        ),
    ],
    "bono": [
        cl.Starter(
            label="Analyze a challenge",
            message="I have a strategic challenge I want to analyze with multiple expert perspectives.",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="Generate expert panel",
            message="Help me create a domain-specific expert panel for my problem.",
            icon="/public/icons/team.svg",
        ),
        cl.Starter(
            label="Six Hats analysis",
            message="Walk me through a Six Thinking Hats analysis of my situation.",
            icon="/public/icons/hats.svg",
        ),
        cl.Starter(
            label="See an example",
            message="Show me how the BONO Master framework works with an example.",
            icon="/public/icons/example.svg",
        ),
    ],
    "knowns": [
        cl.Starter(
            label="Map my knowledge",
            message="Help me map what I know and don't know about my situation.",
            icon="/public/icons/map.svg",
        ),
        cl.Starter(
            label="Find blind spots",
            message="What unknown unknowns might be lurking in my plan?",
            icon="/public/icons/search.svg",
        ),
        cl.Starter(
            label="Risk assessment",
            message="Help me assess the risks of what I don't know.",
            icon="/public/icons/risk.svg",
        ),
        cl.Starter(
            label="Explain Rumsfeld Matrix",
            message="Explain the Known-Unknowns framework and how to use it.",
            icon="/public/icons/info.svg",
        ),
    ],
    "domain": [
        cl.Starter(
            label="Deep dive research",
            message="I need exhaustive research on a topic. Here's what I want to explore: [topic]",
            icon="/public/icons/research.svg",
        ),
        cl.Starter(
            label="Cross-domain synthesis",
            message="Help me find connections between different fields related to my challenge.",
            icon="/public/icons/connect.svg",
        ),
        cl.Starter(
            label="Find dissenting evidence",
            message="I need to understand the opposing views and counter-evidence for my hypothesis.",
            icon="/public/icons/contrast.svg",
        ),
        cl.Starter(
            label="Map the landscape",
            message="Give me a comprehensive landscape analysis of a market/technology/problem.",
            icon="/public/icons/landscape.svg",
        ),
    ],
    "investment": [
        cl.Starter(
            label="Evaluate a startup",
            message="I want to evaluate a startup opportunity using the Ten Questions framework.",
            icon="/public/icons/startup.svg",
        ),
        cl.Starter(
            label="Investment thesis",
            message="Help me build an investment thesis for this opportunity: [describe it]",
            icon="/public/icons/thesis.svg",
        ),
        cl.Starter(
            label="Due diligence",
            message="Walk me through a systematic due diligence process.",
            icon="/public/icons/checklist.svg",
        ),
        cl.Starter(
            label="Explain the framework",
            message="Explain the Ten Questions and Investment Thesis framework.",
            icon="/public/icons/info.svg",
        ),
    ],
    "scenario": [
        cl.Starter(
            label="Explore a domain",
            message="I want to explore multiple plausible futures for my industry/domain: [describe it]",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="Build a 2×2 matrix",
            message="Help me build a scenario matrix to navigate uncertainty in my strategic decision.",
            icon="/public/icons/matrix.svg",
        ),
        cl.Starter(
            label="Find hidden problems",
            message="I want to discover problems worth solving that are invisible from my current position.",
            icon="/public/icons/search.svg",
        ),
        cl.Starter(
            label="Show Shell Oil example",
            message="Show me how Shell used scenario planning to prepare for the 1973 oil crisis.",
            icon="/public/icons/example.svg",
        ),
    ],
}


@cl.set_starters
async def set_starters():
    """Return conversation starters based on selected chat profile."""
    profile = cl.user_session.get("chat_profile")
    return STARTERS.get(profile, STARTERS["larry"])


# === Chat Settings (Input Widgets) ===
@cl.on_settings_update
async def settings_update(settings):
    """Handle settings changes."""
    cl.user_session.set("settings", settings)

    # Provide feedback on settings change
    feedback_parts = []
    if "research_depth" in settings:
        depth = settings["research_depth"]
        feedback_parts.append(f"Research: **{depth}**")
    if "show_examples" in settings:
        examples = "enabled" if settings["show_examples"] else "disabled"
        feedback_parts.append(f"Examples: **{examples}**")
    if "response_detail" in settings:
        detail = settings["response_detail"]
        feedback_parts.append(f"Detail level: **{detail}/10**")

    if feedback_parts:
        await cl.Message(content=f"Settings updated: {' | '.join(feedback_parts)}").send()


async def get_settings_widgets():
    """Return the settings widgets for the current profile."""
    return [
        Select(
            id="research_depth",
            label="Research Depth",
            values=["basic", "advanced"],
            initial_value="basic",
            description="How thorough should web research be?",
        ),
        Switch(
            id="show_examples",
            label="Auto-show Examples",
            initial=False,
            description="Automatically show examples for each phase",
        ),
        Slider(
            id="response_detail",
            label="Response Detail",
            initial=5,
            min=1,
            max=10,
            step=1,
            description="How detailed should responses be? (1=concise, 10=comprehensive)",
        ),
        Select(
            id="workshop_mode",
            label="Workshop Mode",
            values=["guided", "freeform"],
            initial_value="guided",
            description="Strict phase progression vs flexible exploration",
        ),
    ]


async def suggest_agents_from_context(
    history: list,
    current_bot: str,
    max_suggestions: int = 2
) -> list:
    """
    Analyze conversation context and suggest relevant agents to switch to.

    Uses both keyword matching and LLM analysis for smart suggestions.
    Returns list of cl.Action buttons for suggested agents.
    """
    if len(history) < 2:
        return []

    # Get recent conversation text
    recent_text = " ".join([
        msg.get("content", "")
        for msg in history[-6:]
    ]).lower()

    suggestions = []

    # Score each agent based on keyword matches
    agent_scores = {}
    for agent_id, triggers in AGENT_TRIGGERS.items():
        if agent_id == current_bot:
            continue  # Don't suggest current bot

        score = 0
        for keyword in triggers["keywords"]:
            if keyword.lower() in recent_text:
                score += 1

        if score > 0:
            agent_scores[agent_id] = {
                "score": score,
                "description": triggers["description"]
            }

    # Sort by score and take top suggestions
    sorted_agents = sorted(
        agent_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:max_suggestions]

    # Create action buttons for suggestions
    for agent_id, info in sorted_agents:
        bot_info = BOTS.get(agent_id, {})
        suggestions.append(cl.Action(
            name=f"switch_to_{agent_id}",
            payload={"agent": agent_id, "action": "switch"},
            label=f"Switch to {bot_info.get('emoji', '')} {bot_info.get('name', agent_id)}",
            description=info["description"]
        ))

    return suggestions


async def get_ai_agent_suggestion(history: list, current_bot: str) -> Optional[str]:
    """
    Use LLM to analyze conversation and suggest the best agent.
    Returns agent_id or None.
    """
    if len(history) < 4:
        return None

    recent_context = "\n".join([
        f"{msg.get('role', 'user')}: {msg.get('content', '')[:200]}"
        for msg in history[-6:]
    ])

    agent_descriptions = "\n".join([
        f"- {agent_id}: {BOTS.get(agent_id, {}).get('description', '')}"
        for agent_id in BOTS.keys()
        if agent_id != current_bot
    ])

    prompt = f"""Based on this conversation, which specialized agent would be most helpful next?

CONVERSATION:
{recent_context}

AVAILABLE AGENTS:
{agent_descriptions}

CURRENT AGENT: {current_bot}

Respond with ONLY the agent_id (e.g., "tta", "ackoff", "redteam") if a switch would be beneficial.
Respond with "none" if the current agent is appropriate.
Be conservative - only suggest a switch if it would clearly add value."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=20
            )
        )
        suggestion = response.text.strip().lower()

        if suggestion in BOTS and suggestion != current_bot:
            return suggestion
    except Exception as e:
        print(f"Agent suggestion error: {e}")

    return None


def get_context_key() -> str:
    """Generate a key for context preservation across profile switches.
    Uses user identifier if available, or falls back to a session-based key.
    """
    try:
        # Try to get user info for consistent key across sessions
        user = cl.user_session.get("user")
        if user and hasattr(user, "identifier"):
            return f"user_{user.identifier}"
    except:
        pass

    # Fallback: Use a cookie/browser fingerprint approach via session
    # This preserves context within the same browser session
    return "default_context"


@cl.on_chat_start
async def start():
    """Initialize conversation with selected bot."""
    chat_profile = cl.user_session.get("chat_profile")
    bot = BOTS.get(chat_profile, BOTS["larry"])

    # Initialize stop event for this session
    session_id = cl.user_session.get("id")
    if session_id:
        stop_events[session_id] = asyncio.Event()

    # === Context Preservation: Check for existing conversation ===
    # Try persistent storage first (survives server restart), then in-memory cache
    from utils.context_persistence import load_cross_bot_context

    context_key = get_context_key()

    # Try to load from persistent storage (async), falls back to in-memory
    persisted_context = await load_cross_bot_context(context_key)
    preserved_context = persisted_context or context_store.get(context_key, {})

    previous_bot = preserved_context.get("bot_id") or preserved_context.get("last_bot_id")
    preserved_history = preserved_context.get("history", [])
    is_bot_switch = previous_bot and previous_bot != chat_profile and len(preserved_history) > 0

    if is_bot_switch:
        # Switching bots with existing context
        # Preserve history but switch personality
        cl.user_session.set("history", preserved_history.copy())
        cl.user_session.set("previous_bot", previous_bot)

        # Build context summary for the new bot
        context_summary = f"[CONTEXT HANDOFF: User was previously working with {BOTS.get(previous_bot, {}).get('name', previous_bot)}. "
        context_summary += f"Continuing the conversation with preserved context. {len(preserved_history)} messages in history.]"
        cl.user_session.set("context_handoff", context_summary)
    else:
        # Fresh start
        cl.user_session.set("history", [])
        cl.user_session.set("previous_bot", None)
        cl.user_session.set("context_handoff", None)

    cl.user_session.set("bot", bot)
    cl.user_session.set("bot_id", chat_profile or "larry")
    cl.user_session.set("current_phase", 0)

    # Update context store with current session info
    context_store[context_key] = {
        "bot_id": chat_profile or "larry",
        "history": cl.user_session.get("history", []),
    }

    # Initialize settings
    settings = await cl.ChatSettings(await get_settings_widgets()).send()
    cl.user_session.set("settings", settings)

    # Initialize phases for workshop bots
    if chat_profile in WORKSHOP_PHASES:
        phases = [p.copy() for p in WORKSHOP_PHASES[chat_profile]]
        cl.user_session.set("phases", phases)

        # Create and send task list
        task_list = await create_task_list(chat_profile)
        if task_list:
            await task_list.send()

    # Build action buttons for workshop bots
    actions = []
    if bot.get("has_phases"):
        actions = [
            cl.Action(
                name="show_example",
                payload={"action": "example"},
                label="Show Example",
                description="See an example of this phase",
                tooltip="View a real-world example of this methodology phase in action"
            ),
            cl.Action(
                name="next_phase",
                payload={"action": "next"},
                label="Next Phase",
                description="Move to the next workshop phase",
                tooltip="Progress to the next phase of the workshop"
            ),
            cl.Action(
                name="show_progress",
                payload={"action": "progress"},
                label="Show Progress",
                description="View your workshop progress",
                tooltip="See which phases you've completed and what's next"
            ),
            cl.Action(
                name="deep_research",
                payload={"action": "research"},
                label="Deep Research",
                description="Plan and execute web research with Tavily",
                tooltip="🔍 Search the web for relevant data, studies, and evidence"
            ),
            cl.Action(
                name="think_through",
                payload={"action": "think"},
                label="Think It Through",
                description="Break down the problem with sequential thinking",
                tooltip="🧠 Systematically analyze: identify problem → extract assumptions → find gaps → plan next steps"
            ),
            cl.Action(
                name="multi_agent_analysis",
                payload={"action": "multi_agent"},
                label="Multi-Agent Analysis",
                description="Get perspectives from multiple PWS experts",
                tooltip="👥 Get different perspectives from Larry, Red Team, Ackoff, and other PWS experts"
            ),
            cl.Action(
                name="watch_video",
                payload={"action": "video"},
                label="🎬 Watch Video",
                description="Watch tutorial video for this phase",
                tooltip="Watch a tutorial video explaining this workshop phase"
            ),
            cl.Action(
                name="listen_audiobook",
                payload={"action": "audiobook"},
                label="📖 Listen to Chapter",
                description="Listen to relevant PWS audiobook chapter",
                tooltip="Listen to audio content from the PWS course materials"
            ),
        ]

        # Add bot-specific chart buttons
        if chat_profile == "ackoff":
            actions.append(cl.Action(
                name="show_dikw_pyramid",
                payload={"action": "pyramid"},
                label="Show DIKW Pyramid",
                description="View the DIKW pyramid diagram",
                tooltip="📊 View the Data→Information→Knowledge→Wisdom hierarchy diagram"
            ))
        elif chat_profile == "scurve":
            actions.append(cl.Action(
                name="show_scurve",
                payload={"action": "scurve"},
                label="Show S-Curve",
                description="View the technology S-curve diagram",
                tooltip="📈 View the technology adoption S-curve showing ferment→takeoff→maturity phases"
            ))

        # Add export button for all workshop bots
        actions.append(cl.Action(
            name="export_summary",
            payload={"action": "export"},
            label="Export Summary",
            description="Download workshop summary as markdown",
            tooltip="⬇️ Download a complete summary of your workshop progress as a Markdown file"
        ))
    else:
        # Non-workshop bots (like Larry general) also get useful actions
        actions = [
            cl.Action(
                name="deep_research",
                payload={"action": "research"},
                label="🔍 Deep Research",
                description="Plan and execute web research with Tavily",
                tooltip="🔍 Search the web for relevant data, studies, and evidence to support your analysis"
            ),
            cl.Action(
                name="think_through",
                payload={"action": "think"},
                label="🧠 Think It Through",
                description="Break down the problem with sequential thinking",
                tooltip="🧠 Systematically analyze: identify problem → extract assumptions → find gaps → plan next steps"
            ),
            cl.Action(
                name="multi_agent_analysis",
                payload={"action": "multi_agent"},
                label="👥 Multi-Agent Analysis",
                description="Get perspectives from multiple PWS experts",
                tooltip="👥 Get different perspectives from Larry, Red Team, Ackoff, and other PWS experts"
            ),
            cl.Action(
                name="show_example",
                payload={"action": "example"},
                label="📖 Show Example",
                description="See an example of PWS methodology",
                tooltip="📖 View a real-world example of this methodology in action"
            ),
            cl.Action(
                name="listen_audiobook",
                payload={"action": "audiobook"},
                label="🎧 Listen to Chapter",
                description="Listen to relevant PWS audiobook chapter",
                tooltip="🎧 Listen to audio content from the PWS course materials"
            ),
        ]

    # Add "Synthesize & Download" button for ALL bots (Larry synthesizes regardless of current bot)
    actions.append(cl.Action(
        name="synthesize_conversation",
        payload={"action": "synthesize"},
        label="📝 Synthesize & Download",
        description="Larry synthesizes the entire conversation as a downloadable MD file",
        tooltip="📝 Larry summarizes your conversation: key insights, breakthroughs, and next steps"
    ))

    # Add "Extract Insights" button for ALL bots (deep structured extraction)
    actions.append(cl.Action(
        name="extract_insights",
        payload={"action": "extract"},
        label="🔍 Extract Insights",
        description="Extract structured data: facts, assumptions, statistics, open questions",
        tooltip="🔍 Extract: facts, assumptions, statistics, problems, solutions, and open questions"
    ))

    # Add "Generate Image" button for ALL bots
    actions.append(cl.Action(
        name="generate_image",
        payload={},
        label="🎨 Generate Image",
        description="Create an image from a text description using AI",
        tooltip="🎨 Generate images with Gemini Imagen - describe what you want to see"
    ))

    # Add Analytics buttons (dashboard access)
    actions.append(cl.Action(
        name="show_feedback_dashboard",
        payload={},
        label="📊 Feedback Analytics",
        description="View feedback analytics dashboard",
        tooltip="📊 See satisfaction rates, trends, and feedback by bot"
    ))

    actions.append(cl.Action(
        name="show_usage_metrics",
        payload={},
        label="📈 Usage Metrics",
        description="View usage metrics dashboard",
        tooltip="📈 See message counts, bot usage, and activity trends"
    ))

    # Add "Clear Context" action to all bots if there's preserved history
    if is_bot_switch or len(preserved_history) > 0:
        actions.append(cl.Action(
            name="clear_context",
            payload={"action": "clear"},
            label="Clear Context",
            description="Start fresh without previous conversation history",
            tooltip="🗑️ Clear conversation history and start fresh with this bot"
        ))

    # Send welcome message with context info if switching
    if is_bot_switch:
        previous_bot_name = BOTS.get(previous_bot, {}).get("name", previous_bot)
        switch_message = f"""**{bot.get('emoji', '')} {bot['name']}** is now active.

**Context preserved from {previous_bot_name}** ({len(preserved_history)} messages)
I'll continue our conversation with my perspective. Your previous discussion has been handed off to me.

---

{bot.get('welcome', 'How can I help?')}"""

        await cl.Message(content=switch_message, actions=actions if actions else None).send()
    elif bot.get("has_phases"):
        await cl.Message(content=bot["welcome"], actions=actions).send()
    else:
        await cl.Message(content=bot["welcome"], actions=actions if actions else None).send()


# === Chat Resume Handler ===
@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    """Restore session state when user returns to an existing conversation."""
    # Get thread metadata from various possible locations
    metadata = thread.get("metadata", {})

    # Also check user_data which some Chainlit versions use
    user_data = thread.get("user_data", {})
    if not metadata and user_data:
        metadata = user_data

    # Try to infer chat_profile from thread name or first messages if not in metadata
    chat_profile = metadata.get("chat_profile", "larry")

    # Restore bot configuration
    bot = BOTS.get(chat_profile, BOTS["larry"])
    cl.user_session.set("bot", bot)
    cl.user_session.set("bot_id", chat_profile)
    cl.user_session.set("chat_profile", chat_profile)

    # Initialize stop event
    session_id = cl.user_session.get("id")
    if session_id:
        stop_events[session_id] = asyncio.Event()

    # Restore phase progress from metadata
    current_phase = metadata.get("current_phase", 0)
    phases = metadata.get("phases", None)

    if phases is None and chat_profile in WORKSHOP_PHASES:
        # Fallback: initialize fresh phases
        phases = [p.copy() for p in WORKSHOP_PHASES[chat_profile]]

    if phases:
        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", current_phase)

        # Recreate task list
        task_list = cl.TaskList()
        task_list.name = "Workshop Progress"

        for i, phase in enumerate(phases):
            if phase.get("status") == "done":
                status = cl.TaskStatus.DONE
            elif phase.get("status") == "running" or i == current_phase:
                status = cl.TaskStatus.RUNNING
            else:
                status = cl.TaskStatus.READY
            task = cl.Task(title=phase["name"], status=status)
            await task_list.add_task(task)

        await task_list.send()

    # Restore conversation history from thread messages
    history = []
    for message in thread.get("steps", []):
        msg_type = message.get("type", "")
        output = message.get("output", "")

        if msg_type == "user_message" and output:
            history.append({"role": "user", "content": output})
        elif msg_type == "assistant_message" and output:
            history.append({"role": "model", "content": output})

    cl.user_session.set("history", history)

    # Restore settings from metadata
    settings = metadata.get("settings", {})
    if settings:
        cl.user_session.set("settings", settings)

    # Re-initialize settings widgets
    await cl.ChatSettings(await get_settings_widgets()).send()

    # Welcome back message
    phase_info = ""
    if phases and current_phase < len(phases):
        phase_info = f"\n\n**Current phase:** {phases[current_phase]['name']} (Phase {current_phase + 1} of {len(phases)})"

    await cl.Message(
        content=f"**Welcome back!** Your conversation has been restored.{phase_info}"
    ).send()


# === Stop Handler ===
@cl.on_stop
async def on_stop():
    """Handle user clicking the stop button during generation."""
    session_id = cl.user_session.get("id")
    if session_id and session_id in stop_events:
        stop_events[session_id].set()

    await cl.Message(content="**Stopped.** You can continue or ask something else.").send()


# === User Feedback Handler ===
@cl.on_feedback
async def on_feedback(feedback):
    """
    Handle user feedback (thumbs up/down) on messages.
    Stores feedback in Supabase for QA analytics and shows confirmation.
    """
    try:
        from utils.feedback import store_feedback, get_feedback_confirmation_message

        # Get session context
        thread_id = cl.user_session.get("id", "unknown")
        bot_id = cl.user_session.get("chat_profile", "larry")
        phase = cl.user_session.get("current_phase")
        phases = cl.user_session.get("phases", [])
        phase_name = phases[phase]["name"] if phases and phase is not None and phase < len(phases) else None

        # Get the message content and user's last message for context
        history = cl.user_session.get("history", [])
        message_content = None
        user_message = None

        # Find the last assistant message and user message
        for msg in reversed(history):
            if msg.get("role") in ["assistant", "model"] and message_content is None:
                message_content = msg.get("content", "")[:500]
            if msg.get("role") == "user" and user_message is None:
                user_message = msg.get("content", "")[:200]
            if message_content and user_message:
                break

        # Store feedback
        store_feedback(
            message_id=feedback.id,
            thread_id=thread_id,
            score=feedback.value,  # 1 = thumbs up, 0 = thumbs down
            comment=feedback.comment,
            bot_id=bot_id,
            phase=phase_name,
            message_content=message_content,
            user_message=user_message,
            feedback_type="thumbs",
        )

        # Show confirmation in conversation
        confirmation = get_feedback_confirmation_message(
            score=feedback.value,
            feedback_type="thumbs",
            comment=feedback.comment
        )

        # Add option for more detailed feedback
        await cl.Message(
            content=confirmation,
            actions=[
                cl.Action(
                    name="detailed_feedback",
                    payload={"message_id": feedback.id},
                    label="📝 Add Detailed Feedback",
                    description="Rate specific aspects of this response",
                    tooltip="Provide detailed feedback on accuracy, helpfulness, and other aspects"
                )
            ]
        ).send()

        print(f"Feedback received: {'👍' if feedback.value == 1 else '👎'} for {bot_id}")

    except Exception as e:
        print(f"Feedback storage error: {e}")


@cl.action_callback("detailed_feedback")
async def on_detailed_feedback(action: cl.Action):
    """Show detailed feedback options with 1-5 scale."""
    from utils.feedback import RATING_SCALE, FEEDBACK_CATEGORIES

    message_id = action.payload.get("message_id", "unknown")

    # Create rating buttons (1-5 scale with emojis)
    rating_actions = [
        cl.Action(
            name=f"rate_{score}",
            payload={"message_id": message_id, "score": score},
            label=f"{info['emoji']} {score}",
            description=info['description']
        )
        for score, info in RATING_SCALE.items()
    ]

    # Format the rating scale display
    scale_display = "\n".join([
        f"**{score}** {info['emoji']} - {info['label']}: *{info['description']}*"
        for score, info in RATING_SCALE.items()
    ])

    await cl.Message(
        content=f"""**📊 Rate This Response (1-5):**

{scale_display}

Select your rating:""",
        actions=rating_actions
    ).send()


@cl.action_callback("rate_1")
@cl.action_callback("rate_2")
@cl.action_callback("rate_3")
@cl.action_callback("rate_4")
@cl.action_callback("rate_5")
async def on_rate_detailed(action: cl.Action):
    """Handle detailed rating submission."""
    from utils.feedback import store_feedback, get_feedback_confirmation_message, RATING_SCALE

    payload = action.payload
    message_id = payload.get("message_id", "unknown")
    score = payload.get("score", 3)

    # Get session context
    thread_id = cl.user_session.get("id", "unknown")
    bot_id = cl.user_session.get("chat_profile", "larry")
    phase = cl.user_session.get("current_phase")
    phases = cl.user_session.get("phases", [])
    phase_name = phases[phase]["name"] if phases and phase is not None and phase < len(phases) else None

    # Get message context
    history = cl.user_session.get("history", [])
    message_content = None
    user_message = None

    for msg in reversed(history):
        if msg.get("role") in ["assistant", "model"] and message_content is None:
            message_content = msg.get("content", "")[:500]
        if msg.get("role") == "user" and user_message is None:
            user_message = msg.get("content", "")[:200]
        if message_content and user_message:
            break

    # Store detailed feedback
    store_feedback(
        message_id=message_id,
        thread_id=thread_id,
        score=score,
        bot_id=bot_id,
        phase=phase_name,
        message_content=message_content,
        user_message=user_message,
        feedback_type="detailed",
    )

    # Get rating info
    rating_info = RATING_SCALE.get(score, {"emoji": "⭐", "label": "Unknown"})

    # Show confirmation with option to add comment
    await cl.Message(
        content=f"""**{rating_info['emoji']} Thank you for your detailed feedback!**

You rated this response: **{score}/5 - {rating_info['label']}**

Your feedback helps improve Mindrian for everyone.""",
        actions=[
            cl.Action(
                name="add_feedback_comment",
                payload={"message_id": message_id, "score": score},
                label="💬 Add a Comment",
                description="Tell us more about your experience"
            )
        ]
    ).send()

    print(f"Detailed feedback: {score}/5 ({rating_info['label']}) for {bot_id}")


@cl.action_callback("add_feedback_comment")
async def on_add_feedback_comment(action: cl.Action):
    """Prompt user to add a comment to their feedback."""
    await cl.Message(
        content="""**💬 Add Your Comment**

Please type your feedback comment below. What worked well? What could be improved?

*(Just send your comment as a regular message)*"""
    ).send()

    # Store that we're expecting a feedback comment
    cl.user_session.set("expecting_feedback_comment", True)
    cl.user_session.set("feedback_context", action.payload)


@cl.action_callback("multi_agent_analysis")
async def on_multi_agent_analysis(action: cl.Action):
    """Trigger multi-agent analysis - let user choose the type."""

    # Show options for different analysis types
    await cl.Message(
        content="""**Choose Multi-Agent Analysis Type:**

Select the type of analysis you want:""",
        actions=[
            cl.Action(
                name="ma_quick",
                payload={"type": "quick"},
                label="Quick Analysis",
                description="Router picks best agents (fastest)",
                tooltip="⚡ Fast: AI router selects the most relevant agents automatically"
            ),
            cl.Action(
                name="ma_research",
                payload={"type": "research"},
                label="Research & Explore",
                description="Web research → TTA → Larry",
                tooltip="🔍 Web research → Trending to Absurd → Larry synthesis"
            ),
            cl.Action(
                name="ma_validate",
                payload={"type": "validate"},
                label="Validate Decision",
                description="Validation → Ackoff → Red Team",
                tooltip="✅ Fact-check → Ackoff DIKW validation → Red Team challenge"
            ),
            cl.Action(
                name="ma_full",
                payload={"type": "full"},
                label="Full Analysis",
                description="Research → Validate → All Agents (most thorough)",
                tooltip="🔄 Comprehensive: research + validation + all expert perspectives"
            ),
        ]
    ).send()


@cl.action_callback("ma_quick")
async def on_ma_quick(action: cl.Action):
    await run_multi_agent_with_type("quick")

@cl.action_callback("ma_research")
async def on_ma_research(action: cl.Action):
    await run_multi_agent_with_type("research")

@cl.action_callback("ma_validate")
async def on_ma_validate(action: cl.Action):
    await run_multi_agent_with_type("validate")

@cl.action_callback("ma_full")
async def on_ma_full(action: cl.Action):
    await run_multi_agent_with_type("full")


async def run_multi_agent_with_type(analysis_type: str):
    """Execute the selected multi-agent analysis type."""
    from agents.multi_agent_graph import (
        quick_analysis,
        research_and_explore,
        validated_decision,
        full_analysis_with_research,
        AGENTS,
        BACKGROUND_AGENTS
    )

    history = cl.user_session.get("history", [])

    # Build context from recent conversation
    recent_context = "\n".join([
        f"{msg.get('role', 'user')}: {msg.get('content', '')[:300]}"
        for msg in history[-6:]
    ])

    if not recent_context:
        await cl.Message(content="No conversation context yet. Please discuss your problem first, then request multi-agent analysis.").send()
        return

    # Map types to workflows and descriptions
    workflows = {
        "quick": {
            "func": quick_analysis,
            "name": "Quick Analysis",
            "agents": "Auto-selected by router"
        },
        "research": {
            "func": research_and_explore,
            "name": "Research & Explore",
            "agents": "Research Agent → TTA → Larry"
        },
        "validate": {
            "func": validated_decision,
            "name": "Validate Decision",
            "agents": "Validation Agent → Ackoff → Red Team"
        },
        "full": {
            "func": full_analysis_with_research,
            "name": "Full Analysis",
            "agents": "Research + Validation → Larry + Red Team + Ackoff"
        }
    }

    workflow = workflows.get(analysis_type, workflows["quick"])

    try:
        # Show progress with cl.Step
        async with cl.Step(name=f"Multi-Agent: {workflow['name']}", type="run") as main_step:
            main_step.input = f"Analyzing with: {workflow['agents']}"

            # Execute workflow
            async with cl.Step(name="Running Agent Pipeline", type="tool") as pipeline_step:
                pipeline_step.input = f"Context: {recent_context[:200]}..."

                result = await workflow["func"](recent_context)

                pipeline_step.output = f"Completed - received responses from agents"

            # Process results
            output_parts = []

            # Background agent results
            if result.get("background_results"):
                async with cl.Step(name="Background Agent Results", type="tool") as bg_step:
                    bg_outputs = []
                    for agent_id, agent_result in result["background_results"].items():
                        if agent_result.get("success"):
                            agent_name = BACKGROUND_AGENTS[agent_id].name
                            if agent_id == "research":
                                findings = agent_result.get("findings", "No findings")
                                sources = agent_result.get("sources", [])
                                bg_outputs.append(f"**{agent_name}:**\n{findings}")
                                if sources:
                                    source_list = "\n".join([f"- [{s['title']}]({s['url']})" for s in sources[:5]])
                                    bg_outputs.append(f"\n**Sources:**\n{source_list}")
                            elif agent_id == "validation":
                                report = agent_result.get("validation_report", "No report")
                                bg_outputs.append(f"**{agent_name}:**\n{report}")
                            elif agent_id == "analysis":
                                analysis = agent_result.get("analysis", "No analysis")
                                bg_outputs.append(f"**{agent_name}:**\n{analysis}")

                    bg_step.output = f"Processed {len(result['background_results'])} background agents"
                    output_parts.extend(bg_outputs)

            # Conversation agent responses
            if result.get("conversation_responses"):
                async with cl.Step(name="Expert Perspectives", type="llm") as conv_step:
                    conv_outputs = []
                    for agent_id, response in result["conversation_responses"].items():
                        agent_name = AGENTS.get(agent_id, {}).get("name", agent_id)
                        conv_outputs.append(f"### {agent_name}\n{response}")

                    conv_step.output = f"Received {len(result['conversation_responses'])} expert perspectives"
                    output_parts.extend(conv_outputs)

            # Synthesis
            synthesis = result.get("synthesis", "")
            if synthesis:
                output_parts.append(f"---\n\n## Synthesis\n{synthesis}")

            main_step.output = "Analysis complete"

        # Send final combined message
        final_output = "\n\n".join(output_parts)
        if not final_output:
            final_output = "No results generated. Try providing more context in your conversation."

        await cl.Message(
            content=f"## {workflow['name']} Results\n\n{final_output}",
            actions=[
                cl.Action(name="multi_agent_analysis", payload={}, label="Run Another Analysis"),
            ]
        ).send()

    except Exception as e:
        await cl.Message(content=f"Multi-agent analysis error: {str(e)}").send()


@cl.action_callback("clear_context")
async def on_clear_context(action: cl.Action):
    """Clear preserved context and start fresh."""
    from utils.context_persistence import clear_cross_bot_context

    context_key = get_context_key()

    # Clear the stored context (in-memory)
    if context_key in context_store:
        del context_store[context_key]

    # Clear from persistent storage (Supabase)
    await clear_cross_bot_context(context_key)

    # Clear session history
    cl.user_session.set("history", [])
    cl.user_session.set("previous_bot", None)
    cl.user_session.set("context_handoff", None)

    bot = cl.user_session.get("bot", BOTS["larry"])

    await cl.Message(
        content=f"**Context cleared.** Starting fresh with {bot.get('name', 'Larry')}.\n\n{bot.get('welcome', 'How can I help?')}"
    ).send()


# === Analytics & Dashboard Callbacks ===

@cl.action_callback("show_feedback_dashboard")
async def on_show_feedback_dashboard(action: cl.Action):
    """Show the feedback analytics dashboard."""
    from utils.feedback import get_feedback_dashboard, format_dashboard_message

    async with cl.Step(name="Loading Feedback Analytics", type="tool") as step:
        step.input = "Fetching feedback data from Supabase..."

        dashboard = await get_feedback_dashboard(days=7)
        message = format_dashboard_message(dashboard)

        step.output = f"Found {dashboard.get('total_feedback', 0)} feedback entries"

    await cl.Message(content=message).send()


@cl.action_callback("show_usage_metrics")
async def on_show_usage_metrics(action: cl.Action):
    """Show the usage metrics dashboard."""
    from utils.usage_metrics import get_usage_dashboard, format_usage_dashboard_message

    async with cl.Step(name="Loading Usage Metrics", type="tool") as step:
        step.input = "Fetching usage data from Supabase..."

        dashboard = await get_usage_dashboard(days=7)
        message = format_usage_dashboard_message(dashboard)

        step.output = f"Analyzed {dashboard.get('total_messages', 0)} messages"

    await cl.Message(content=message).send()


@cl.action_callback("generate_image")
async def on_generate_image(action: cl.Action):
    """Handle image generation request from action button."""
    from utils.image_generation import generate_image, save_image_to_temp, get_style_presets
    from utils.usage_metrics import track_image_generation

    # Get the prompt from payload or ask user
    prompt = action.payload.get("prompt") if action.payload else None

    if not prompt:
        # Send a message asking for the prompt
        await cl.Message(
            content="**Generate Image**\n\nPlease describe the image you want to create. For example:\n"
                    "- *A sunset over mountains with a lake reflection*\n"
                    "- *A futuristic city with flying cars*\n"
                    "- *A cozy coffee shop interior in watercolor style*\n\n"
                    "Type your description and I'll generate an image for you.",
            actions=[
                cl.Action(name="cancel_generation", payload={}, label="Cancel", tooltip="Cancel image generation")
            ]
        ).send()
        cl.user_session.set("awaiting_image_prompt", True)
        return

    # Generate the image
    async with cl.Step(name="Generating Image", type="tool") as step:
        step.input = f"Prompt: {prompt}"

        image_bytes, mime_type, metadata = await generate_image(
            prompt=prompt,
            model="fast",
            aspect_ratio="square"
        )

        if image_bytes:
            step.output = f"Image generated ({metadata.get('size_bytes', 0):,} bytes)"

            # Save to temp file for display
            temp_path = save_image_to_temp(image_bytes, mime_type)

            # Track usage
            context_key = get_context_key()
            track_image_generation(context_key)

            # Display the image
            await cl.Message(
                content=f"**Generated Image**\n\n*Prompt:* {prompt}",
                elements=[
                    cl.Image(name="generated_image", path=temp_path, display="inline")
                ],
                actions=[
                    cl.Action(
                        name="generate_image",
                        payload={"prompt": prompt},
                        label="Regenerate",
                        tooltip="Generate a new variation"
                    ),
                    cl.Action(
                        name="generate_image",
                        payload={},
                        label="New Image",
                        tooltip="Generate a different image"
                    )
                ]
            ).send()
        else:
            error_msg = metadata.get("user_message", metadata.get("error", "Unknown error"))
            step.output = f"Failed: {error_msg}"
            await cl.Message(content=f"**Image Generation Failed**\n\n{error_msg}").send()


@cl.action_callback("cancel_generation")
async def on_cancel_generation(action: cl.Action):
    """Cancel pending image generation."""
    cl.user_session.set("awaiting_image_prompt", False)
    await cl.Message(content="Image generation cancelled.").send()


# === Dynamic Agent Switching ===
# These callbacks handle the context-aware "Switch to X" buttons

@cl.action_callback("switch_to_tta")
async def on_switch_to_tta(action: cl.Action):
    await handle_agent_switch("tta")

@cl.action_callback("switch_to_jtbd")
async def on_switch_to_jtbd(action: cl.Action):
    await handle_agent_switch("jtbd")

@cl.action_callback("switch_to_scurve")
async def on_switch_to_scurve(action: cl.Action):
    await handle_agent_switch("scurve")

@cl.action_callback("switch_to_redteam")
async def on_switch_to_redteam(action: cl.Action):
    await handle_agent_switch("redteam")

@cl.action_callback("switch_to_ackoff")
async def on_switch_to_ackoff(action: cl.Action):
    await handle_agent_switch("ackoff")

@cl.action_callback("switch_to_larry")
async def on_switch_to_larry(action: cl.Action):
    await handle_agent_switch("larry")

@cl.action_callback("switch_to_bono")
async def on_switch_to_bono(action: cl.Action):
    await handle_agent_switch("bono")

@cl.action_callback("switch_to_knowns")
async def on_switch_to_knowns(action: cl.Action):
    await handle_agent_switch("knowns")

@cl.action_callback("switch_to_domain")
async def on_switch_to_domain(action: cl.Action):
    await handle_agent_switch("domain")

@cl.action_callback("switch_to_investment")
async def on_switch_to_investment(action: cl.Action):
    await handle_agent_switch("investment")

@cl.action_callback("switch_to_scenario")
async def on_switch_to_scenario(action: cl.Action):
    await handle_agent_switch("scenario")


async def handle_agent_switch(new_agent_id: str):
    """
    Handle switching to a new agent while preserving conversation context.
    This performs an in-session switch without reloading the page.
    """
    current_bot_id = cl.user_session.get("bot_id", "larry")
    history = cl.user_session.get("history", [])

    if new_agent_id not in BOTS:
        await cl.Message(content=f"Unknown agent: {new_agent_id}").send()
        return

    new_bot = BOTS[new_agent_id]
    old_bot = BOTS.get(current_bot_id, BOTS["larry"])

    # Update session with new bot
    cl.user_session.set("bot", new_bot)
    cl.user_session.set("bot_id", new_agent_id)
    cl.user_session.set("previous_bot", current_bot_id)

    # Add context handoff for the new bot
    handoff = f"[CONTEXT HANDOFF: User switched from {old_bot.get('name')} to {new_bot.get('name')}. Previous conversation preserved.]"
    cl.user_session.set("context_handoff", handoff)

    # Initialize phases for new bot if it's a workshop
    if new_agent_id in WORKSHOP_PHASES:
        phases = [p.copy() for p in WORKSHOP_PHASES[new_agent_id]]
        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", 0)

        # Create task list
        task_list = cl.TaskList()
        task_list.name = "Workshop Progress"
        for phase in phases:
            status = cl.TaskStatus.READY if phase["status"] == "ready" else cl.TaskStatus.RUNNING
            task = cl.Task(title=phase["name"], status=status)
            await task_list.add_task(task)
        await task_list.send()
    else:
        cl.user_session.set("phases", [])
        cl.user_session.set("current_phase", 0)

    # Update context store
    context_key = get_context_key()
    context_store[context_key] = {
        "bot_id": new_agent_id,
        "history": history.copy(),
    }

    # Build actions for the new bot
    actions = []
    if new_bot.get("has_phases"):
        actions = [
            cl.Action(name="show_example", payload={"action": "example"}, label="Show Example", tooltip="View a real-world example of this methodology"),
            cl.Action(name="next_phase", payload={"action": "next"}, label="Next Phase", tooltip="Progress to the next workshop phase"),
            cl.Action(name="think_through", payload={"action": "think"}, label="Think Through", tooltip="Systematically break down the problem"),
        ]

    # Add clear context button
    actions.append(cl.Action(
        name="clear_context",
        payload={"action": "clear"},
        label="Clear Context",
        description="Start fresh without previous history",
        tooltip="🗑️ Clear conversation history and start fresh with this bot"
    ))

    # Generate a handoff response from the new bot
    handoff_prompt = f"""You are {new_bot.get('name')}. The user just switched to you from {old_bot.get('name')}.

Here's the conversation context:
{chr(10).join([f"{m.get('role')}: {m.get('content', '')[:300]}" for m in history[-4:]])}

Briefly (2-3 sentences):
1. Acknowledge the switch
2. Explain how YOUR perspective/methodology differs
3. Ask a probing question that leverages your specialty

Be direct and engaging. Show your unique value."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=handoff_prompt,
            config=types.GenerateContentConfig(
                system_instruction=new_bot.get("system_prompt", ""),
                temperature=0.7,
                max_output_tokens=300
            )
        )
        handoff_message = response.text.strip()
    except Exception as e:
        handoff_message = f"I'm {new_bot.get('name')}. I've received the context from your conversation with {old_bot.get('name')}. How can I apply my expertise here?"

    # Send the handoff message
    await cl.Message(
        content=f"**{new_bot.get('emoji', '')} Switched to {new_bot.get('name')}**\n\n{handoff_message}",
        actions=actions
    ).send()

    # Add to history
    history.append({"role": "model", "content": handoff_message})
    cl.user_session.set("history", history)


@cl.action_callback("show_example")
async def on_show_example(action: cl.Action):
    """Handle show example button click - pulls diverse examples from Neo4j and File Search."""
    current_phase = cl.user_session.get("current_phase", 0)
    chat_profile = cl.user_session.get("chat_profile", "larry")
    session_id = cl.user_session.get("id", "default")

    try:
        from utils.dynamic_examples import (
            get_diverse_example,
            get_shown_examples,
            track_shown_example
        )

        # Get recently shown examples to avoid repetition
        exclude_recent = get_shown_examples(session_id)

        # Fetch a diverse example (from Neo4j, File Search, or static)
        example = await get_diverse_example(
            bot_id=chat_profile,
            phase=current_phase,
            exclude_recent=exclude_recent
        )

        # Track this example to avoid showing it again soon
        # Extract title for tracking (assumes **Title**: format)
        if "**" in example:
            title = example.split("**")[1] if len(example.split("**")) > 1 else f"example_{current_phase}"
        else:
            title = f"example_{current_phase}"
        track_shown_example(session_id, title)

        await cl.Message(content=f"**📖 Example:**\n\n{example}").send()

    except Exception as e:
        print(f"Dynamic example fetch error: {e}")
        # Fallback to simple static examples
        fallback_examples = {
            "tta": "**Trending to the Absurd**: Push a trend to its extreme to reveal future problems. Example: 'What if 100% of workers are remote?' surfaces problems in collaboration, culture, and infrastructure.",
            "jtbd": "**Jobs to Be Done**: People don't buy products, they hire them for a job. Example: Milkshakes are 'hired' for a boring commute, not as a dessert.",
            "scurve": "**S-Curve Analysis**: Technologies progress through Era of Ferment → Dominant Design → Incremental Improvement. Know where your technology sits to time your innovation.",
            "redteam": "**Red Teaming**: Attack your own assumptions before the market does. 'What if customers won't pay?' 'What if a free alternative exists?'",
            "ackoff": "**Camera Test**: If a camera can't record it, it's interpretation, not data. '47 people in line' is data. 'Long line' is interpretation.",
            "larry": "**PWS Methodology**: Validate the problem is worth solving BEFORE building the solution. Is it Real? Can you Win? Is it Worth it?",
        }
        example = fallback_examples.get(chat_profile, "No specific example available.")
        await cl.Message(content=f"**📖 Example:**\n\n{example}").send()


@cl.action_callback("next_phase")
async def on_next_phase(action: cl.Action):
    """Handle next phase button click."""
    current_phase = cl.user_session.get("current_phase", 0)
    chat_profile = cl.user_session.get("chat_profile", "larry")
    phases = cl.user_session.get("phases", [])

    if current_phase < len(phases) - 1:
        # Mark current as done, next as running
        phases[current_phase]["status"] = "done"
        phases[current_phase + 1]["status"] = "running"
        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", current_phase + 1)

        # Update task list
        task_list = cl.TaskList()
        task_list.name = "Workshop Progress"

        for i, phase in enumerate(phases):
            if phase["status"] == "done":
                status = cl.TaskStatus.DONE
            elif phase["status"] == "running":
                status = cl.TaskStatus.RUNNING
            else:
                status = cl.TaskStatus.READY
            task = cl.Task(title=phase["name"], status=status)
            await task_list.add_task(task)

        await task_list.send()

        await cl.Message(
            content=f"**✅ Moving to Phase {current_phase + 2}: {phases[current_phase + 1]['name']}**\n\nLet's continue with the next phase of the workshop."
        ).send()
    else:
        await cl.Message(
            content="**🎉 Workshop Complete!**\n\nYou've completed all phases. Would you like to review your progress or start fresh?"
        ).send()


@cl.action_callback("show_progress")
async def on_show_progress(action: cl.Action):
    """Handle show progress button click."""
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)

    progress_text = "**📊 Workshop Progress:**\n\n"
    for i, phase in enumerate(phases):
        if phase["status"] == "done":
            emoji = "✅"
        elif phase["status"] == "running" or i == current_phase:
            emoji = "🔄"
        else:
            emoji = "⬜"
        progress_text += f"{emoji} **Phase {i+1}:** {phase['name']}\n"

    completed = sum(1 for p in phases if p["status"] == "done")
    progress_text += f"\n**Progress: {completed}/{len(phases)} phases complete**"

    await cl.Message(content=progress_text).send()


@cl.action_callback("show_dikw_pyramid")
async def on_show_dikw_pyramid(action: cl.Action):
    """Handle showing the DIKW pyramid visualization."""
    from utils.charts import create_dikw_pyramid

    # Get the current phase to potentially highlight
    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])

    # Map phase index to DIKW level for highlighting
    highlight_map = {
        2: "data",          # Data Level
        3: "information",   # Information Level
        4: "knowledge",     # Knowledge Level
        5: "understanding", # Understanding Level
        6: "wisdom",        # Wisdom Level
    }

    highlight = highlight_map.get(current_phase)

    pyramid_chart = await create_dikw_pyramid(
        highlight_level=highlight,
        title="Ackoff's DIKW Pyramid - Validation Framework"
    )

    explanation = """**The DIKW Pyramid** shows the hierarchy of understanding:

- **Data**: Raw observations (Camera Test: Could a camera record it?)
- **Information**: Organized, contextualized data (What does it mean?)
- **Knowledge**: Patterns and relationships (What patterns emerge?)
- **Understanding**: Cause and effect (Why does it happen?)
- **Wisdom**: Judgment and decisions (What should we do?)

**Climb UP** to explore and understand a problem.
**Climb DOWN** to validate that your solution is grounded in reality.
"""

    await cl.Message(
        content=explanation,
        elements=[pyramid_chart]
    ).send()


@cl.action_callback("show_scurve")
async def on_show_scurve(action: cl.Action):
    """Handle showing the S-Curve visualization."""
    from utils.charts import create_scurve_chart

    # Default to early stage, could be customized based on context
    scurve_chart = await create_scurve_chart(
        title="Technology S-Curve - Adoption Lifecycle",
        current_position=0.3  # Default to dominant design phase
    )

    explanation = """**The Technology S-Curve** shows how technologies evolve:

- **Era of Ferment** (0-25%): Many competing approaches, high uncertainty, no clear winner
- **Dominant Design** (25-50%): Industry converges on a standard, optimization begins
- **Incremental Change** (50-75%): Refinement and efficiency improvements
- **Maturity/Discontinuity** (75-100%): Performance limits approached, watch for the next curve

**Key Question**: Where does your technology sit on this curve?
- Too early = high risk, may run out of resources
- Too late = fighting established giants
- Right timing = ride the wave
"""

    await cl.Message(
        content=explanation,
        elements=[scurve_chart]
    ).send()


@cl.action_callback("watch_video")
async def on_watch_video(action: cl.Action):
    """Handle watching tutorial video for current phase."""
    from utils.media import get_workshop_video, WORKSHOP_VIDEOS

    bot = cl.user_session.get("bot", BOTS["larry"])
    bot_id = None

    # Find the bot_id from current bot
    for bid, bdata in BOTS.items():
        if bdata.get("name") == bot.get("name"):
            bot_id = bid
            break

    if not bot_id:
        bot_id = "larry"

    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])

    # Determine which video to show
    phase_key = f"phase_{current_phase + 1}" if current_phase > 0 else "intro"

    # Try to get the phase-specific video, fall back to intro
    video = await get_workshop_video(bot_id, phase_key)

    if not video:
        # Check if any videos are configured for this bot
        bot_videos = WORKSHOP_VIDEOS.get(bot_id, {})
        configured_videos = [p for p, url in bot_videos.items() if url]

        if not configured_videos:
            await cl.Message(
                content=f"""**No tutorial videos configured yet for {bot.get('name', 'this workshop')}.**

To add videos, update `WORKSHOP_VIDEOS` in `utils/media.py`:

```python
WORKSHOP_VIDEOS["{bot_id}"] = {{
    "intro": "https://youtube.com/watch?v=YOUR_VIDEO_ID",
    "phase_1": "https://youtube.com/watch?v=PHASE1_VIDEO",
    # ... more phases
}}
```

Or set videos programmatically:
```python
from utils.media import set_workshop_video
set_workshop_video("{bot_id}", "intro", "https://youtube.com/watch?v=...")
```
"""
            ).send()
        else:
            # Some videos exist, but not for current phase
            await cl.Message(
                content=f"No video available for Phase {current_phase + 1}. Videos exist for: {', '.join(configured_videos)}"
            ).send()
        return

    # Get current phase name
    phase_name = phases[current_phase]["name"] if phases and current_phase < len(phases) else "Introduction"

    await cl.Message(
        content=f"**🎬 Tutorial Video: {phase_name}**\n\nWatch the video below for guidance on this phase:",
        elements=[video]
    ).send()


@cl.action_callback("listen_audiobook")
async def on_listen_audiobook(action: cl.Action):
    """Handle listening to PWS audiobook chapters."""
    from utils.media import (
        find_relevant_chapters,
        get_chapters_for_bot,
        get_audiobook_chapter,
        AUDIOBOOK_CHAPTERS
    )

    bot_id = cl.user_session.get("chat_profile", "larry")
    history = cl.user_session.get("history", [])

    # Get recent conversation context for relevance matching
    recent_text = " ".join([
        msg.get("content", "")
        for msg in history[-6:]
    ])

    # Find relevant chapters based on conversation
    relevant_chapters = find_relevant_chapters(recent_text, bot_id, max_results=3)

    # If no relevant chapters found based on context, show all chapters for this bot
    if not relevant_chapters:
        all_chapters = get_chapters_for_bot(bot_id)
        if not all_chapters:
            await cl.Message(
                content=f"""**No audiobook chapters configured yet.**

To add audiobook chapters, update `AUDIOBOOK_CHAPTERS` in `utils/media.py`:

```python
from utils.media import set_audiobook_chapter

set_audiobook_chapter(
    topic="pws_foundation",
    chapter_id="chapter_1",
    url="https://your-supabase-url/audio/chapter1.mp3",
    title="Introduction to PWS",
    duration="15:00"
)
```

Or upload audio files to Supabase Storage and add URLs to the `AUDIOBOOK_CHAPTERS` dict.
"""
            ).send()
            return

        # Create action buttons for all available chapters
        chapter_actions = [
            cl.Action(
                name=f"play_chapter_{ch['topic']}_{ch['chapter_id']}",
                payload={"topic": ch['topic'], "chapter_id": ch['chapter_id']},
                label=f"▶️ {ch['title'][:30]}..." if len(ch['title']) > 30 else f"▶️ {ch['title']}",
                description=f"Duration: {ch['duration']}"
            )
            for ch in all_chapters[:4]  # Limit to 4 buttons
        ]

        await cl.Message(
            content=f"**📖 Available PWS Audiobook Chapters for {BOTS.get(bot_id, {}).get('name', 'this workshop')}:**\n\nSelect a chapter to listen:",
            actions=chapter_actions
        ).send()
        return

    # Show relevant chapters based on conversation context
    chapter_info = "\n".join([
        f"• **{ch['title']}** ({ch['duration']})"
        for ch in relevant_chapters
    ])

    chapter_actions = [
        cl.Action(
            name=f"play_chapter_{ch['topic']}_{ch['chapter_id']}",
            payload={"topic": ch['topic'], "chapter_id": ch['chapter_id']},
            label=f"▶️ {ch['title'][:30]}..." if len(ch['title']) > 30 else f"▶️ {ch['title']}",
            description=f"Duration: {ch['duration']}"
        )
        for ch in relevant_chapters
    ]

    await cl.Message(
        content=f"""**📖 Relevant PWS Audiobook Chapters**

Based on your conversation, these chapters may be helpful:

{chapter_info}

Select a chapter to listen:""",
        actions=chapter_actions
    ).send()


@cl.action_callback("play_chapter_pws_foundation_chapter_1")
@cl.action_callback("play_chapter_pws_foundation_chapter_2")
@cl.action_callback("play_chapter_pws_foundation_chapter_3")
@cl.action_callback("play_chapter_trending_to_absurd_chapter_1")
@cl.action_callback("play_chapter_trending_to_absurd_chapter_2")
@cl.action_callback("play_chapter_trending_to_absurd_chapter_3")
@cl.action_callback("play_chapter_jobs_to_be_done_chapter_1")
@cl.action_callback("play_chapter_jobs_to_be_done_chapter_2")
@cl.action_callback("play_chapter_jobs_to_be_done_chapter_3")
@cl.action_callback("play_chapter_s_curve_chapter_1")
@cl.action_callback("play_chapter_s_curve_chapter_2")
@cl.action_callback("play_chapter_s_curve_chapter_3")
@cl.action_callback("play_chapter_ackoffs_pyramid_chapter_1")
@cl.action_callback("play_chapter_ackoffs_pyramid_chapter_2")
@cl.action_callback("play_chapter_ackoffs_pyramid_chapter_3")
@cl.action_callback("play_chapter_red_teaming_chapter_1")
@cl.action_callback("play_chapter_red_teaming_chapter_2")
@cl.action_callback("play_chapter_red_teaming_chapter_3")
async def on_play_chapter(action: cl.Action):
    """Play a specific audiobook chapter."""
    from utils.media import get_audiobook_chapter, AUDIOBOOK_CHAPTERS

    payload = action.payload
    topic = payload.get("topic")
    chapter_id = payload.get("chapter_id")

    if not topic or not chapter_id:
        await cl.Message(content="Invalid chapter selection.").send()
        return

    # Get chapter metadata
    chapter_info = AUDIOBOOK_CHAPTERS.get(topic, {}).get(chapter_id, {})
    title = chapter_info.get("title", "Unknown Chapter")
    duration = chapter_info.get("duration", "")

    # Get audio element
    audio = await get_audiobook_chapter(topic, chapter_id)

    if not audio:
        await cl.Message(
            content=f"**Audio not available for: {title}**\n\nThe audiobook chapter URL has not been configured yet."
        ).send()
        return

    await cl.Message(
        content=f"**📖 Now Playing: {title}**\n\n*Duration: {duration}*",
        elements=[audio]
    ).send()


@cl.action_callback("export_summary")
async def on_export_summary(action: cl.Action):
    """Export workshop progress as downloadable markdown file."""
    from utils.media import export_workshop_summary

    bot = cl.user_session.get("bot", BOTS["larry"])
    phases = cl.user_session.get("phases", [])
    history = cl.user_session.get("history", [])
    current_phase = cl.user_session.get("current_phase", 0)

    if not phases:
        await cl.Message(content="No workshop progress to export.").send()
        return

    try:
        file_element = await export_workshop_summary(
            bot_name=bot.get("name", "Workshop"),
            phases=phases,
            history=history,
            current_phase=current_phase
        )

        await cl.Message(
            content="**Workshop Summary exported.** Click to download:",
            elements=[file_element]
        ).send()
    except Exception as e:
        await cl.Message(content=f"Export error: {str(e)}").send()


@cl.action_callback("synthesize_conversation")
async def on_synthesize_conversation(action: cl.Action):
    """Synthesize the entire conversation using Larry's voice and style, then export as MD file."""
    from utils.media import create_file_download
    from prompts import LARRY_RAG_SYSTEM_PROMPT
    import datetime

    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["larry"])

    if len(history) < 2:
        await cl.Message(content="Not enough conversation to synthesize. Have a discussion first!").send()
        return

    # Build conversation transcript for Larry to synthesize
    transcript = ""
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            transcript += f"**User:** {content}\n\n"
        else:
            transcript += f"**Assistant:** {content}\n\n"

    try:
        async with cl.Step(name="Larry Synthesizing Conversation", type="llm") as synth_step:
            synth_step.input = f"Synthesizing {len(history)} messages..."

            # Create synthesis prompt with Larry's voice
            synthesis_prompt = f"""You are Larry - Prof. Lawrence Aronhime's thinking partner persona.

Your task is to synthesize the following conversation into a coherent, insightful summary document.

**CRITICAL: Use YOUR voice - Larry's voice - regardless of which bot the conversation was with.**

Your synthesis should:
1. Start with a brief overview of what was explored
2. Identify the core problem or question being worked on
3. Highlight key insights, reframes, and breakthroughs
4. Note any assumptions that were challenged
5. List concrete next steps or open questions
6. End with Larry's perspective on where to go next

**Your Voice Guidelines:**
- Conversational, not academic
- Provocative, not condescending
- Warm but demanding
- Use signature phrases like "Very simply...", "Here's what everyone misses...", "Think about it like this..."

**Format as a clean Markdown document suitable for download.**

---

## CONVERSATION TO SYNTHESIZE:

{transcript}

---

Now synthesize this conversation in Larry's voice. Create a document titled "Conversation Synthesis" with clear sections."""

            # Use Gemini to generate synthesis with Larry's voice
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=synthesis_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=LARRY_RAG_SYSTEM_PROMPT[:2000],  # Use Larry's core personality
                    temperature=0.7,
                    max_output_tokens=4000
                )
            )

            synthesis = response.text
            synth_step.output = f"Generated {len(synthesis)} character synthesis"

        # Create the MD file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"larry_synthesis_{timestamp}.md"

        # Add header metadata to the synthesis
        full_content = f"""# Larry's Conversation Synthesis

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
**Original Bot:** {bot.get('name', 'Unknown')}
**Messages Analyzed:** {len(history)}

---

{synthesis}

---

*Synthesized by Larry - your PWS thinking partner*
"""

        file_element = await create_file_download(
            content=full_content,
            filename=filename
        )

        # Show synthesis inline in chat AND offer download
        await cl.Message(
            content=f"""**📝 Larry's Synthesis Complete!**

---

{synthesis}

---

**Download your synthesis:**""",
            elements=[file_element]
        ).send()

    except Exception as e:
        await cl.Message(content=f"Synthesis error: {str(e)}").send()


@cl.action_callback("extract_insights")
async def on_extract_insights(action: cl.Action):
    """Extract structured insights from the conversation - stored in Supabase."""
    from tools.langextract import (
        instant_extract,
        background_extract_conversation,
        format_instant_extraction,
        format_deep_extraction,
        cache_extraction
    )
    from utils.media import create_file_download
    import datetime

    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["larry"])
    session_id = cl.user_session.get("id", "unknown")

    if len(history) < 2:
        await cl.Message(content="Not enough conversation to analyze. Have a discussion first!").send()
        return

    # Build conversation text for extraction
    conversation_text = ""
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")
        conversation_text += f"{role}: {content}\n\n"

    try:
        # Step 1: Instant extraction (NO latency, regex-based)
        async with cl.Step(name="Quick Analysis", type="tool") as quick_step:
            quick_step.input = f"Analyzing {len(history)} messages with pattern matching..."
            instant_results = instant_extract(conversation_text)
            quick_step.output = format_instant_extraction(instant_results)

        # Show instant results immediately
        await cl.Message(
            content=f"**🔍 Quick Analysis Complete**\n\n{format_instant_extraction(instant_results)}\n\n*Running deep analysis...*"
        ).send()

        # Step 2: Deep LLM extraction (background, but user triggered so we show progress)
        async with cl.Step(name="Deep Extraction", type="llm") as deep_step:
            deep_step.input = "Extracting structured PWS elements: problems, assumptions, facts, questions..."

            deep_results = await background_extract_conversation(history, bot.get("name", "larry"))

            if deep_results.get("error"):
                deep_step.output = f"Error: {deep_results['error']}"
            else:
                deep_step.output = f"Extracted {len(deep_results.get('key_facts', []))} facts, {len(deep_results.get('stated_assumptions', []))} assumptions"

        # Cache the extraction in Supabase
        cache_key = cache_extraction(
            conversation_text,
            {**instant_results, "deep": deep_results},
            extract_type="conversation",
            session_id=session_id
        )

        # Format the deep extraction
        deep_formatted = format_deep_extraction(deep_results)

        # Create downloadable JSON export
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        export_data = {
            "extracted_at": datetime.datetime.now().isoformat(),
            "bot": bot.get("name", "Unknown"),
            "message_count": len(history),
            "cache_key": cache_key,
            "instant_analysis": instant_results,
            "deep_analysis": deep_results
        }

        # Create both MD and JSON downloads
        md_content = f"""# Conversation Extraction

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
**Bot:** {bot.get('name', 'Unknown')}
**Messages:** {len(history)}
**Cache Key:** `{cache_key}` *(stored in Supabase)*

---

{format_instant_extraction(instant_results)}

---

{deep_formatted}

---

*Extracted by LangExtract - Zero-latency structured data extraction*
"""

        md_file = await create_file_download(
            content=md_content,
            filename=f"extraction_{timestamp}.md"
        )

        import json
        json_file = await create_file_download(
            content=json.dumps(export_data, indent=2, default=str),
            filename=f"extraction_{timestamp}.json"
        )

        await cl.Message(
            content=f"""**🔍 Deep Extraction Complete!**

{deep_formatted}

---

**Stored in Supabase** with key: `{cache_key}`

Download your extraction:""",
            elements=[md_file, json_file]
        ).send()

    except Exception as e:
        await cl.Message(content=f"Extraction error: {str(e)}").send()


@cl.action_callback("speak_response")
async def on_speak_response(action: cl.Action):
    """Convert last response to speech using ElevenLabs."""
    from utils.media import text_to_speech

    history = cl.user_session.get("history", [])

    # Get last assistant response
    last_response = None
    for msg in reversed(history):
        if msg.get("role") == "model":
            last_response = msg.get("content", "")[:2000]  # Limit for voice
            break

    if not last_response:
        await cl.Message(content="No response to speak.").send()
        return

    async with cl.Step(name="Generating Voice", type="tool") as voice_step:
        voice_step.input = f"Converting {len(last_response)} characters to speech..."

        audio_element = await text_to_speech(last_response)

        if audio_element:
            voice_step.output = "Voice generated successfully"
            await cl.Message(
                content="**Larry's voice response:**",
                elements=[audio_element]
            ).send()
        else:
            voice_step.output = "ElevenLabs API key not configured"
            await cl.Message(
                content="Voice not available. Set ELEVENLABS_API_KEY in environment."
            ).send()


@cl.action_callback("deep_research")
async def on_deep_research(action: cl.Action):
    """Handle deep research button - sequential thinking + Tavily execution with cl.Step visualization."""
    from tools.tavily_search import search_web

    # Get context
    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["larry"])
    chat_profile = cl.user_session.get("chat_profile", "larry")
    settings = cl.user_session.get("settings", {})
    search_depth = settings.get("research_depth", "basic")

    # Build context from recent conversation
    recent_context = ""
    for msg in history[-6:]:  # Last 3 exchanges
        role = msg.get("role", "user")
        content = msg.get("content", "")[:500]
        recent_context += f"{role}: {content}\n"

    try:
        # Parent step for the entire research process
        async with cl.Step(name="Deep Research", type="run") as research_step:
            research_step.input = f"Context: {recent_context[:200]}..."

            # Step 1: Planning
            async with cl.Step(name="Planning Research Strategy", type="llm") as plan_step:
                planning_prompt = f"""Based on this conversation context, create a focused research plan.

CONTEXT:
{recent_context}

WORKSHOP: {chat_profile}

Create exactly 3 search queries that would help validate or explore the key topics discussed.
Format your response as:

**Research Plan:**
1. [First search query - most important]
2. [Second search query - supporting evidence]
3. [Third search query - alternative perspectives or challenges]

Be specific and actionable. Each query should be something Tavily can search effectively."""

                plan_step.input = "Analyzing conversation context..."

                plan_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=planning_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=500
                    )
                )
                research_plan = plan_response.text
                plan_step.output = research_plan

            # Extract queries from the plan
            queries = []
            for line in research_plan.split('\n'):
                line = line.strip()
                if line.startswith(('1.', '2.', '3.')):
                    query = line[2:].strip().strip('[]').strip()
                    if query and len(query) > 10:
                        queries.append(query)

            if not queries:
                queries = ["innovation trends 2025", "market validation methods", "problem solving frameworks"]

            # Step 2: Execute searches (nested steps)
            all_results = []
            async with cl.Step(name="Executing Web Searches", type="tool") as search_parent:
                search_parent.input = f"{len(queries)} queries to execute"

                for i, query in enumerate(queries[:3], 1):
                    async with cl.Step(name=f"Search {i}: {query[:40]}...", type="tool") as search_step:
                        search_step.input = query
                        result = search_web(query, search_depth=search_depth, max_results=3)

                        if result.get("results"):
                            all_results.append({
                                "query": query,
                                "results": result["results"],
                                "answer": result.get("answer", "")
                            })
                            search_step.output = f"Found {len(result['results'])} results"
                        else:
                            search_step.output = "No results found"

                search_parent.output = f"Completed {len(all_results)} successful searches"

            # Step 3: Synthesize results
            async with cl.Step(name="Synthesizing Results", type="llm") as synth_step:
                if all_results:
                    synthesis = "## Research Results\n\n"
                    for item in all_results:
                        synthesis += f"### Query: {item['query']}\n"
                        if item.get('answer'):
                            synthesis += f"**Summary:** {item['answer'][:300]}...\n\n"
                        for r in item['results'][:2]:
                            synthesis += f"- [{r.get('title', 'Source')}]({r.get('url', '')})\n"
                            synthesis += f"  {r.get('content', '')[:150]}...\n\n"

                    synth_step.output = synthesis
                else:
                    synthesis = "No research results found. Try being more specific about what you want to research."
                    synth_step.output = synthesis

            research_step.output = f"Research complete: {len(all_results)} queries, {sum(len(r['results']) for r in all_results)} total sources"

        # Send final synthesis as a message with optional DataFrame
        elements = []
        if all_results:
            try:
                from utils.charts import create_research_results_dataframe
                # Flatten all results for DataFrame
                flat_results = []
                for item in all_results:
                    flat_results.extend(item.get("results", []))

                if flat_results:
                    df_element = await create_research_results_dataframe(flat_results[:10])
                    if df_element:
                        elements.append(df_element)
            except Exception:
                pass  # DataFrame is optional enhancement

        await cl.Message(content=synthesis, elements=elements).send()

    except Exception as e:
        await cl.Message(content=f"Research error: {str(e)}").send()


@cl.action_callback("think_through")
async def on_think_through(action: cl.Action):
    """Handle think through button - sequential thinking breakdown with cl.Step visualization."""
    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["larry"])
    chat_profile = cl.user_session.get("chat_profile", "larry")

    # Build context from recent conversation
    recent_context = ""
    for msg in history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")[:500]
        recent_context += f"{role}: {content}\n"

    try:
        # Parent step for the thinking process
        async with cl.Step(name="Think It Through", type="run") as think_step:
            think_step.input = f"Analyzing: {recent_context[:150]}..."

            # Step 1: Extract the core problem
            async with cl.Step(name="Identifying Core Problem", type="llm") as problem_step:
                problem_prompt = f"""Based on this conversation context, identify the central question or problem being explored.

CONTEXT:
{recent_context}

WORKSHOP: {chat_profile}

In 1-2 sentences, state the core problem or question. Be specific and clear."""

                problem_step.input = "Extracting core problem..."
                problem_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=problem_prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=200)
                )
                core_problem = problem_response.text.strip()
                problem_step.output = core_problem

            # Step 2: Extract assumptions
            async with cl.Step(name="Extracting Assumptions", type="llm") as assumptions_step:
                assumptions_prompt = f"""Given this problem: "{core_problem}"

And context:
{recent_context}

List 2-3 key assumptions that underlie this problem. Be specific about what is being taken for granted."""

                assumptions_step.input = f"Core problem: {core_problem[:100]}"
                assumptions_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=assumptions_prompt,
                    config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=300)
                )
                assumptions = assumptions_response.text.strip()
                assumptions_step.output = assumptions

            # Step 3: Check what we know vs don't know
            async with cl.Step(name="Knowledge Gap Analysis", type="llm") as gaps_step:
                gaps_prompt = f"""Given this problem: "{core_problem}"
And these assumptions:
{assumptions}

Identify:
1. What do we have evidence for? (2-3 items)
2. What do we need to find out? (2-3 items)

Be specific and actionable."""

                gaps_step.input = "Analyzing evidence and gaps..."
                gaps_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=gaps_prompt,
                    config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=400)
                )
                knowledge_analysis = gaps_response.text.strip()
                gaps_step.output = knowledge_analysis

            # Step 4: Generate next steps
            async with cl.Step(name="Planning Next Steps", type="llm") as steps_step:
                steps_prompt = f"""Given:
- Core Problem: {core_problem}
- Assumptions: {assumptions[:200]}
- Knowledge Gaps: {knowledge_analysis[:200]}

Suggest 2-3 concrete, actionable next steps to move forward. Be specific."""

                steps_step.input = "Generating action plan..."
                steps_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=steps_prompt,
                    config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=300)
                )
                next_steps = steps_response.text.strip()
                steps_step.output = next_steps

            think_step.output = "Analysis complete"

        # Compile and send the full analysis as a message
        full_analysis = f"""## Structured Problem Breakdown

### Core Question/Problem
{core_problem}

### Key Assumptions
{assumptions}

### Knowledge Analysis
{knowledge_analysis}

### Suggested Next Steps
{next_steps}
"""
        await cl.Message(content=full_analysis).send()

    except Exception as e:
        await cl.Message(content=f"Thinking error: {str(e)}").send()


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with streaming and stop event support."""

    # Check if we're expecting a feedback comment
    if cl.user_session.get("expecting_feedback_comment"):
        from utils.feedback import store_feedback, get_feedback_confirmation_message

        feedback_context = cl.user_session.get("feedback_context", {})
        cl.user_session.set("expecting_feedback_comment", False)
        cl.user_session.set("feedback_context", None)

        # Get session context for storing the comment
        thread_id = cl.user_session.get("id", "unknown")
        bot_id = cl.user_session.get("chat_profile", "larry")

        # Store the comment with the previous feedback
        store_feedback(
            message_id=feedback_context.get("message_id", "unknown"),
            thread_id=thread_id,
            score=feedback_context.get("score", 3),
            comment=message.content,
            bot_id=bot_id,
            feedback_type="detailed",
        )

        # Show confirmation
        await cl.Message(
            content=f"""**💬 Comment Added!**

Thank you for your detailed feedback:
> *"{message.content[:200]}{'...' if len(message.content) > 200 else ''}"*

Your insights help us improve Mindrian!"""
        ).send()
        return  # Don't process as regular message

    # Check if user is providing an image generation prompt
    if cl.user_session.get("awaiting_image_prompt"):
        cl.user_session.set("awaiting_image_prompt", False)
        from utils.image_generation import generate_image, save_image_to_temp
        from utils.usage_metrics import track_image_generation

        prompt = message.content.strip()
        if prompt:
            async with cl.Step(name="Generating Image", type="tool") as step:
                step.input = f"Prompt: {prompt}"

                image_bytes, mime_type, metadata = await generate_image(
                    prompt=prompt,
                    model="fast",
                    aspect_ratio="square"
                )

                if image_bytes:
                    step.output = f"Image generated ({metadata.get('size_bytes', 0):,} bytes)"
                    temp_path = save_image_to_temp(image_bytes, mime_type)

                    # Track usage
                    context_key = get_context_key()
                    track_image_generation(context_key)

                    await cl.Message(
                        content=f"**Generated Image**\n\n*Prompt:* {prompt}",
                        elements=[cl.Image(name="generated_image", path=temp_path, display="inline")],
                        actions=[
                            cl.Action(name="generate_image", payload={"prompt": prompt}, label="Regenerate"),
                            cl.Action(name="generate_image", payload={}, label="New Image")
                        ]
                    ).send()
                else:
                    error_msg = metadata.get("user_message", metadata.get("error", "Unknown error"))
                    step.output = f"Failed: {error_msg}"
                    await cl.Message(content=f"**Image Generation Failed**\n\n{error_msg}").send()
        return  # Don't process as regular message

    # Check for image generation intent in message
    from utils.image_generation import detect_image_generation_intent
    is_image_request, image_prompt = detect_image_generation_intent(message.content)
    if is_image_request and image_prompt:
        from utils.image_generation import generate_image, save_image_to_temp
        from utils.usage_metrics import track_image_generation

        async with cl.Step(name="Generating Image", type="tool") as step:
            step.input = f"Detected image request: {image_prompt}"

            image_bytes, mime_type, metadata = await generate_image(
                prompt=image_prompt,
                model="fast",
                aspect_ratio="square"
            )

            if image_bytes:
                step.output = f"Image generated ({metadata.get('size_bytes', 0):,} bytes)"
                temp_path = save_image_to_temp(image_bytes, mime_type)

                # Track usage
                context_key = get_context_key()
                track_image_generation(context_key)

                await cl.Message(
                    content=f"**Generated Image**\n\n*Prompt:* {image_prompt}",
                    elements=[cl.Image(name="generated_image", path=temp_path, display="inline")],
                    actions=[
                        cl.Action(name="generate_image", payload={"prompt": image_prompt}, label="Regenerate"),
                        cl.Action(name="generate_image", payload={}, label="New Image")
                    ]
                ).send()
                return  # Image generated, don't process as regular message
            else:
                # Fall through to regular processing if image generation failed
                step.output = f"Image generation failed, falling back to text response"

    bot = cl.user_session.get("bot", BOTS["larry"])
    history = cl.user_session.get("history", [])
    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])
    settings = cl.user_session.get("settings", {})
    session_id = cl.user_session.get("id")

    # Reset stop event for this request
    if session_id and session_id in stop_events:
        stop_events[session_id].clear()

    # Process file attachments (PDF, DOCX, TXT, images, etc.)
    file_context = ""
    image_parts = []  # For Gemini multimodal
    image_elements = []  # For display
    failed_images = []  # Track failed images for text fallback

    if message.elements:
        from utils.file_processor import process_uploaded_file, format_file_context, is_image_file, get_image_mime_type
        import os

        for element in message.elements:
            if hasattr(element, 'path') and element.path:
                # Check if it's an image file
                if is_image_file(element.name):
                    # Handle image upload for multimodal
                    async with cl.Step(name=f"Processing image: {element.name}", type="tool") as img_step:
                        img_step.input = f"Preparing image for analysis: {element.name}"
                        image_processed = False
                        try:
                            # Check file size before reading (Gemini limit ~20MB)
                            file_size = os.path.getsize(element.path)
                            if file_size > 20 * 1024 * 1024:  # 20MB limit
                                raise ValueError(f"Image too large ({file_size / 1024 / 1024:.1f}MB). Max 20MB.")

                            with open(element.path, "rb") as f:
                                image_bytes = f.read()

                            # Validate image bytes are not empty/corrupt
                            if len(image_bytes) < 100:
                                raise ValueError("Image file appears to be empty or corrupt")

                            mime_type = get_image_mime_type(element.name)

                            # Add to Gemini parts for multimodal
                            image_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

                            # Add to display elements
                            image_elements.append(cl.Image(name=element.name, path=element.path, display="inline"))

                            # Track image upload
                            from utils.usage_metrics import track_image_upload
                            track_image_upload(get_context_key())

                            img_step.output = f"Image ready ({len(image_bytes):,} bytes, {mime_type})"
                            image_processed = True

                        except Exception as img_err:
                            img_step.output = f"Error: {str(img_err)}"
                            failed_images.append({
                                "name": element.name,
                                "error": str(img_err),
                                "path": element.path
                            })

                        # Fallback: Add text description if image processing failed
                        if not image_processed:
                            fallback_desc = f"\n\n---\n**IMAGE UPLOAD (Processing Failed): {element.name}**\n"
                            fallback_desc += f"Error: {failed_images[-1]['error']}\n"
                            fallback_desc += "Note: The user attempted to upload an image but it could not be processed for visual analysis. "
                            fallback_desc += "Please acknowledge the upload attempt and ask the user to describe the image content or try re-uploading.\n---\n"
                            file_context += fallback_desc

                            await cl.Message(
                                content=f"**Image processing failed for {element.name}**\n\n"
                                        f"Error: {failed_images[-1]['error']}\n\n"
                                        f"*The AI will acknowledge your upload but cannot see the image. "
                                        f"Please describe what's in the image or try re-uploading.*"
                            ).send()
                else:
                    # Extract text from uploaded document file
                    async with cl.Step(name=f"Processing: {element.name}", type="tool") as file_step:
                        file_step.input = f"Extracting content from {element.name}"

                        content, metadata = process_uploaded_file(element.path, element.name)

                        if metadata.get("error"):
                            file_step.output = f"Error: {metadata['error']}"
                            await cl.Message(content=f"Could not process **{element.name}**: {metadata['error']}").send()
                        else:
                            file_type = metadata.get("type", "file")
                            char_count = metadata.get("char_count", 0)
                            file_step.output = f"Extracted {char_count:,} characters from {file_type}"

                            # Add to context for LLM
                            file_context += format_file_context(element.name, content, metadata)

                            # Notify user with inline PDF display if applicable
                            info_msg = f"**{element.name}** processed"
                            elements = []

                            if file_type == "pdf":
                                info_msg += f" ({metadata.get('pages_extracted')}/{metadata.get('total_pages')} pages)"
                                # Add inline PDF viewer
                                elements.append(cl.Pdf(
                                    name=element.name,
                                    path=element.path,
                                    display="side"
                                ))
                            elif file_type == "docx":
                                info_msg += f" ({metadata.get('paragraphs')} paragraphs)"

                            if metadata.get("truncated"):
                                info_msg += " *(truncated for length)*"

                            await cl.Message(content=info_msg, elements=elements).send()

        # Display uploaded images together
        if image_elements:
            await cl.Message(
                content=f"**{len(image_elements)} image(s) uploaded** - analyzing...",
                elements=image_elements
            ).send()

    # Build contents for Gemini
    contents = []
    for msg in history:
        contents.append(types.Content(
            role=msg["role"],
            parts=[types.Part(text=msg["content"])]
        ))

    # Add phase context for workshop bots
    phase_context = ""
    if phases and current_phase < len(phases):
        phase_context = f"\n\n[CURRENT WORKSHOP PHASE: {phases[current_phase]['name']} (Phase {current_phase + 1} of {len(phases)})]"

    # Add settings context
    detail_level = settings.get("response_detail", 5)
    workshop_mode = settings.get("workshop_mode", "guided")
    detail_instruction = ""
    if detail_level <= 3:
        detail_instruction = "\n[USER PREFERENCE: Be concise and brief in your response.]"
    elif detail_level >= 8:
        detail_instruction = "\n[USER PREFERENCE: Provide comprehensive, detailed explanations.]"

    # Combine user message with file context and other context
    full_user_message = message.content
    if file_context:
        full_user_message += f"\n\n{file_context}"
    full_user_message += phase_context + detail_instruction

    # Build multimodal content (supports images + text)
    user_parts = []
    if image_parts:
        # Add image parts first for Gemini multimodal
        user_parts.extend(image_parts)
    # Add text part (or default prompt if only images provided)
    text_content = full_user_message if message.content.strip() else "Please analyze this image and describe what you see."
    user_parts.append(types.Part(text=text_content))

    contents.append(types.Content(
        role="user",
        parts=user_parts
    ))

    # Create streaming message
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Check for cached context (RAG) for this bot
        bot_id = cl.user_session.get("bot_id", "larry")
        cache_name = get_cache_name(bot_id) if RAG_ENABLED else None

        # Build system instruction with context handoff if applicable
        system_instruction = bot["system_prompt"]
        context_handoff = cl.user_session.get("context_handoff")
        previous_bot = cl.user_session.get("previous_bot")

        if context_handoff and previous_bot:
            previous_bot_name = BOTS.get(previous_bot, {}).get("name", previous_bot)
            handoff_addendum = f"""

[CONTEXT HANDOFF NOTICE]
The user was previously working with {previous_bot_name} and has switched to you while preserving conversation context.
The previous conversation history is included above. Continue the discussion from your unique perspective.
DO NOT repeat what was already discussed. Build on the existing conversation.
The user expects you to understand the context and add your specialized value.
[END HANDOFF NOTICE]
"""
            system_instruction = system_instruction + handoff_addendum

        if cache_name:
            # Use cached context with RAG materials
            config = types.GenerateContentConfig(
                cached_content=cache_name,
            )
            print(f"Using RAG cache: {cache_name}")
        else:
            # Fall back to regular system instruction
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
            )

        response_stream = client.models.generate_content_stream(
            model="gemini-3-flash-preview",
            contents=contents,
            config=config,
        )

        full_response = ""
        stopped = False

        for chunk in response_stream:
            # Check if user requested stop
            if session_id and session_id in stop_events and stop_events[session_id].is_set():
                full_response += "\n\n*[Response stopped by user]*"
                await msg.stream_token("\n\n*[Response stopped by user]*")
                stopped = True
                break

            if chunk.text:
                full_response += chunk.text
                await msg.stream_token(chunk.text)

        # Add action buttons to EVERY response (key actions always visible)
        actions = []
        if not stopped:
            # Core actions for ALL bots - always visible
            actions = [
                cl.Action(
                    name="deep_research",
                    payload={"action": "research"},
                    label="🔍 Research",
                    tooltip="Search the web for relevant data and evidence",
                ),
                cl.Action(
                    name="think_through",
                    payload={"action": "think"},
                    label="🧠 Think",
                    tooltip="Systematically analyze: problem → assumptions → gaps → next steps",
                ),
                cl.Action(
                    name="synthesize_conversation",
                    payload={"action": "synthesize"},
                    label="📥 Synthesize",
                    tooltip="Summarize conversation: key insights, breakthroughs, next steps",
                ),
            ]

            # Add workshop-specific actions
            if bot.get("has_phases"):
                actions.extend([
                    cl.Action(
                        name="show_example",
                        payload={"action": "example"},
                        label="📖 Example",
                        tooltip="View a real-world example of this methodology",
                    ),
                    cl.Action(
                        name="next_phase",
                        payload={"action": "next"},
                        label="➡️ Next Phase",
                        tooltip="Progress to the next workshop phase",
                    ),
                ])
            else:
                # Non-workshop bots get example and multi-agent
                actions.extend([
                    cl.Action(
                        name="show_example",
                        payload={"action": "example"},
                        label="📖 Example",
                        tooltip="View a real-world example of this methodology",
                    ),
                    cl.Action(
                        name="multi_agent_analysis",
                        payload={"action": "multi_agent"},
                        label="👥 Multi-Agent",
                        tooltip="Get perspectives from multiple PWS experts",
                    ),
                ])

        # Add dynamic agent suggestions based on conversation context
        if not stopped and len(history) >= 2:
            current_bot_id = cl.user_session.get("bot_id", "larry")
            # Include the new messages for analysis
            updated_history = history + [
                {"role": "user", "content": message.content},
                {"role": "model", "content": full_response}
            ]
            agent_suggestions = await suggest_agents_from_context(
                updated_history,
                current_bot_id,
                max_suggestions=2
            )
            if agent_suggestions:
                actions.extend(agent_suggestions)

        if actions:
            msg.actions = actions

        await msg.update()

        # Update history
        history.append({"role": "user", "content": message.content})
        history.append({"role": "model", "content": full_response})
        cl.user_session.set("history", history)

        # Sync history to context store for preservation across bot switches
        context_key = get_context_key()
        bot_id = cl.user_session.get("bot_id", "larry")
        context_store[context_key] = {
            "bot_id": bot_id,
            "history": history.copy(),
        }

        # Persist to Supabase for cross-session survival (fire-and-forget)
        from utils.context_persistence import save_cross_bot_context
        asyncio.create_task(save_cross_bot_context(
            user_key=context_key,
            history=history.copy(),
            bot_id=bot_id,
            bot_name=BOTS.get(bot_id, {}).get("name", bot_id)
        ))

        # Track usage metrics
        from utils.usage_metrics import track_context_save, track_message
        track_context_save(context_key, bot_id, len(history))
        track_message(session_id or "unknown", context_key, bot_id)

        # Save session metadata for resume (phases, settings, current_phase)
        # Metadata is persisted through the data layer when threads are saved
        chat_profile = cl.user_session.get("chat_profile", "larry")
        try:
            # Update thread metadata for resume
            thread_id = cl.context.session.thread_id
            if thread_id and hasattr(cl.context.session, 'thread'):
                # Store in session for persistence
                metadata = {
                    "chat_profile": chat_profile,
                    "current_phase": current_phase,
                    "phases": phases,
                    "settings": settings,
                }
                # Store metadata in user session - will be persisted by data layer
                cl.user_session.set("thread_metadata", metadata)
        except Exception as meta_err:
            print(f"Metadata save warning: {meta_err}")

    except Exception as e:
        await msg.stream_token(f"\n\nError: {str(e)}")
        await msg.update()


# === Audio Stream Handlers (Voice Assistant) ===
# Real-time audio processing with ElevenLabs voice responses

@cl.on_audio_start
async def on_audio_start():
    """Initialize audio streaming session."""
    print("🎤 [AUDIO DEBUG] Audio recording started")
    cl.user_session.set("audio_chunks", [])
    cl.user_session.set("audio_mime_type", "audio/webm")
    return True  # Accept audio stream


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """Process incoming audio chunks in real-time."""
    audio_chunks = cl.user_session.get("audio_chunks", [])
    audio_chunks.append(chunk.data)
    cl.user_session.set("audio_chunks", audio_chunks)

    # Debug log first chunk
    if len(audio_chunks) == 1:
        print(f"🎤 [AUDIO DEBUG] First chunk received, size: {len(chunk.data)} bytes, mime: {chunk.mimeType}")

    # Store mime type from first chunk
    if chunk.mimeType:
        cl.user_session.set("audio_mime_type", chunk.mimeType)


@cl.on_audio_end
async def on_audio_end(elements: list = None):
    """Process complete audio and respond with ElevenLabs voice."""
    import tempfile
    import io

    audio_chunks = cl.user_session.get("audio_chunks", [])
    if not audio_chunks:
        print("🎤 [AUDIO DEBUG] No audio chunks received - audio recording may have failed")
        await cl.Message(content="⚠️ No audio detected. Please check microphone permissions and try again.").send()
        return

    # Combine audio chunks
    audio_data = b"".join(audio_chunks)
    print(f"🎤 [AUDIO DEBUG] Audio recording ended. Total chunks: {len(audio_chunks)}, Total size: {len(audio_data)} bytes")
    cl.user_session.set("audio_chunks", [])  # Clear for next session

    # Check if audio is too small (likely no speech)
    if len(audio_data) < 1000:
        print(f"🎤 [AUDIO DEBUG] Audio too small ({len(audio_data)} bytes) - likely no speech detected")
        await cl.Message(content="⚠️ Audio recording too short. Please speak clearly and try again.").send()
        return

    # Save to temp file for transcription
    mime_type = cl.user_session.get("audio_mime_type", "audio/webm")
    suffix = ".webm" if "webm" in mime_type else ".wav"
    print(f"🎤 [AUDIO DEBUG] Mime type: {mime_type}, Saving as: {suffix}")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_data)
        audio_path = f.name
    print(f"🎤 [AUDIO DEBUG] Audio saved to: {audio_path}")

    try:
        # Use Gemini for transcription (it supports audio)
        transcription = None

        # Try Google Speech-to-Text via Gemini
        print("🎤 [AUDIO DEBUG] Sending to Gemini for transcription...")
        try:
            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            # Use Gemini to transcribe
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            types.Part(text="Transcribe this audio exactly. Only output the transcription, nothing else.")
                        ]
                    )
                ]
            )
            transcription = response.text.strip()
            print(f"🎤 [AUDIO DEBUG] Transcription successful: '{transcription[:100]}...' ({len(transcription)} chars)")
        except Exception as e:
            print(f"🎤 [AUDIO DEBUG] Transcription error: {e}")
            await cl.Message(content=f"Could not transcribe audio: {str(e)[:100]}. Please try again or type your message.").send()
            return

        if not transcription:
            print("🎤 [AUDIO DEBUG] Empty transcription returned")
            await cl.Message(content="No speech detected in the audio.").send()
            return

        # Show what was heard
        await cl.Message(content=f"**You said:** {transcription}").send()

        # Process as regular message
        bot = cl.user_session.get("bot", BOTS["larry"])
        history = cl.user_session.get("history", [])
        current_phase = cl.user_session.get("current_phase", 0)
        phases = cl.user_session.get("phases", [])

        # Build context
        contents = []
        for msg in history:
            contents.append(types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["content"])]
            ))

        phase_context = ""
        if phases and current_phase < len(phases):
            phase_context = f"\n\n[CURRENT WORKSHOP PHASE: {phases[current_phase]['name']}]"

        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=transcription + phase_context)]
        ))

        # Generate response
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=bot["system_prompt"],
            )
        )

        response_text = response.text

        # Update history
        history.append({"role": "user", "content": transcription})
        history.append({"role": "model", "content": response_text})
        cl.user_session.set("history", history)

        # Sync history to context store for preservation across bot switches
        context_key = get_context_key()
        bot_id = cl.user_session.get("bot_id", "larry")
        context_store[context_key] = {
            "bot_id": bot_id,
            "history": history.copy(),
        }

        # Persist to Supabase for cross-session survival (fire-and-forget)
        from utils.context_persistence import save_cross_bot_context
        asyncio.create_task(save_cross_bot_context(
            user_key=context_key,
            history=history.copy(),
            bot_id=bot_id,
            bot_name=BOTS.get(bot_id, {}).get("name", bot_id)
        ))

        # Generate voice response with ElevenLabs
        from utils.media import text_to_speech, ELEVENLABS_API_KEY
        print(f"🔊 [AUDIO DEBUG] Generating TTS for response ({len(response_text)} chars)")
        print(f"🔊 [AUDIO DEBUG] ElevenLabs API key configured: {bool(ELEVENLABS_API_KEY)}")

        audio_element = await text_to_speech(response_text[:2000])

        if audio_element:
            print("🔊 [AUDIO DEBUG] TTS successful - audio element created")
            await cl.Message(
                content=response_text,
                elements=[audio_element]
            ).send()
        else:
            print("🔊 [AUDIO DEBUG] TTS failed - no audio element returned. Check ELEVENLABS_API_KEY env var.")
            await cl.Message(content=response_text + "\n\n*(Voice response unavailable - check ElevenLabs API key)*").send()

    except Exception as e:
        print(f"🎤 [AUDIO DEBUG] Audio processing error: {e}")
        await cl.Message(content=f"Audio processing error: {str(e)}").send()
    finally:
        # Cleanup temp file
        import os
        try:
            os.unlink(audio_path)
        except:
            pass
