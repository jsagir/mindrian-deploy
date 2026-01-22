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
    ACKOFF_WORKSHOP_PROMPT
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
}

# === Bot Configurations ===
BOTS = {
    "larry": {
        "name": "Larry",
        "icon": "🧠",
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
        "icon": "🔮",
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
        "icon": "🎯",
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
        "icon": "📈",
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
        "icon": "😈",
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
        "icon": "🔺",
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


@cl.on_chat_start
async def start():
    """Initialize conversation with selected bot."""
    chat_profile = cl.user_session.get("chat_profile")
    bot = BOTS.get(chat_profile, BOTS["larry"])

    cl.user_session.set("history", [])
    cl.user_session.set("bot", bot)
    cl.user_session.set("bot_id", chat_profile or "larry")
    cl.user_session.set("current_phase", 0)

    # Initialize stop event for this session
    session_id = cl.user_session.get("id")
    if session_id:
        stop_events[session_id] = asyncio.Event()

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

    # Send welcome message with action buttons for workshop bots
    if bot.get("has_phases"):
        actions = [
            cl.Action(
                name="show_example",
                payload={"action": "example"},
                label="Show Example",
                description="See an example of this phase"
            ),
            cl.Action(
                name="next_phase",
                payload={"action": "next"},
                label="Next Phase",
                description="Move to the next workshop phase"
            ),
            cl.Action(
                name="show_progress",
                payload={"action": "progress"},
                label="Show Progress",
                description="View your workshop progress"
            ),
            cl.Action(
                name="deep_research",
                payload={"action": "research"},
                label="Deep Research",
                description="Plan and execute web research with Tavily"
            ),
            cl.Action(
                name="think_through",
                payload={"action": "think"},
                label="Think It Through",
                description="Break down the problem with sequential thinking"
            ),
        ]

        # Add bot-specific chart buttons
        if chat_profile == "ackoff":
            actions.append(cl.Action(
                name="show_dikw_pyramid",
                payload={"action": "pyramid"},
                label="Show DIKW Pyramid",
                description="View the DIKW pyramid diagram"
            ))
        elif chat_profile == "scurve":
            actions.append(cl.Action(
                name="show_scurve",
                payload={"action": "scurve"},
                label="Show S-Curve",
                description="View the technology S-curve diagram"
            ))

        # Add export button for all workshop bots
        actions.append(cl.Action(
            name="export_summary",
            payload={"action": "export"},
            label="Export Summary",
            description="Download workshop summary as markdown"
        ))

        await cl.Message(content=bot["welcome"], actions=actions).send()
    else:
        await cl.Message(content=bot["welcome"]).send()


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


@cl.action_callback("show_example")
async def on_show_example(action: cl.Action):
    """Handle show example button click."""
    current_phase = cl.user_session.get("current_phase", 0)
    chat_profile = cl.user_session.get("chat_profile", "larry")

    example_prompts = {
        "tta": [
            "Here's an example: A team analyzing the trend of remote work might push it to the absurd: 'What if 95% of knowledge workers never set foot in an office?' This forces you to think about problems that don't exist yet.",
            "Example trend verification: 'Remote work increased from 5% to 35% between 2019-2023 (Stanford study)' - that's evidence. 'Everyone is working remotely' is not.",
        ],
        "jtbd": [
            "Example: People don't buy a drill because they want a drill. They don't even want a hole. They want to hang a picture that makes their spouse happy. The functional job is 'hang picture', but the emotional job is 'feel competent' and the social job is 'please my partner'.",
        ],
        "scurve": [
            "Example: Electric vehicles in 2015 were in the Era of Ferment - many competing approaches (Tesla, Leaf, Bolt, various startups). By 2020, a dominant design emerged around lithium-ion batteries and specific form factors. Now we're in incremental improvement mode.",
        ],
        "redteam": [
            "Example assumption attack: 'You assume customers will pay $50/month. What if they only pay $20? What if there's a free alternative? What if the problem you're solving isn't painful enough to pay for at all?'",
        ],
        "ackoff": [
            "Example of the Camera Test: 'The line was long' is interpretation. '47 people in line at 12:15' is data. Could a camera record it? If not, it's interpretation, not observation.",
            "Example of pattern vs causation: 'Users leave when prices increase' is a pattern. 'Price increases CAUSE users to leave' is a causal claim we haven't verified yet. Don't confuse correlation with causation.",
            "Example of the 5 Whys: Why do customers complain? → Wait times. Why long wait times? → Understaffed. Why understaffed? → Budget cuts. Why budget cuts? → Revenue down. Why revenue down? → Product-market fit issues. There's your root cause.",
            "Example climb-down validation: Your solution traces cleanly to data—or it doesn't. If there's a gap at the Knowledge level, you're building on assumption, not evidence. That's when projects fail.",
        ],
    }

    examples = example_prompts.get(chat_profile, ["No specific example available for this phase."])
    example = examples[min(current_phase, len(examples)-1)]

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

    bot = cl.user_session.get("bot", BOTS["larry"])
    history = cl.user_session.get("history", [])
    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])
    settings = cl.user_session.get("settings", {})
    session_id = cl.user_session.get("id")

    # Reset stop event for this request
    if session_id and session_id in stop_events:
        stop_events[session_id].clear()

    # Process file attachments (PDF, DOCX, TXT, etc.)
    file_context = ""
    if message.elements:
        from utils.file_processor import process_uploaded_file, format_file_context

        for element in message.elements:
            if hasattr(element, 'path') and element.path:
                # Extract text from uploaded file
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

    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=full_user_message)]
    ))

    # Create streaming message
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Check for cached context (RAG) for this bot
        bot_id = cl.user_session.get("bot_id", "larry")
        cache_name = get_cache_name(bot_id) if RAG_ENABLED else None

        if cache_name:
            # Use cached context with RAG materials
            config = types.GenerateContentConfig(
                cached_content=cache_name,
            )
            print(f"Using RAG cache: {cache_name}")
        else:
            # Fall back to regular system instruction
            config = types.GenerateContentConfig(
                system_instruction=bot["system_prompt"],
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

        # Add action buttons to response for workshop bots
        if bot.get("has_phases") and not stopped:
            msg.actions = [
                cl.Action(
                    name="show_example",
                    payload={"action": "example"},
                    label="Example",
                ),
                cl.Action(
                    name="next_phase",
                    payload={"action": "next"},
                    label="Next Phase",
                ),
                cl.Action(
                    name="think_through",
                    payload={"action": "think"},
                    label="Think Through",
                ),
            ]

        await msg.update()

        # Update history
        history.append({"role": "user", "content": message.content})
        history.append({"role": "model", "content": full_response})
        cl.user_session.set("history", history)

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


# === Audio Handlers ===
# Note: Audio handling is now managed by Chainlit's built-in speech-to-text
# which is configured in .chainlit/config.toml under [features.speech_to_text]
# The browser handles transcription and sends text directly to on_message
