"""
Mindrian - Multi-Bot PWS Platform
Larry Core + Specialized Tool Workshop Bots
Enhanced with Task Lists, Action Buttons, File Upload, Charts, and more
"""

import os
import json
import chainlit as cl
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

from google import genai
from google.genai import types

# === Config ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

client = genai.Client(api_key=GOOGLE_API_KEY)

# === System Prompts ===
from prompts import (
    LARRY_RAG_SYSTEM_PROMPT,
    TTA_WORKSHOP_PROMPT,
    JTBD_WORKSHOP_PROMPT,
    SCURVE_WORKSHOP_PROMPT,
    REDTEAM_PROMPT
)

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
    ]


@cl.on_chat_start
async def start():
    """Initialize conversation with selected bot."""
    chat_profile = cl.user_session.get("chat_profile")
    bot = BOTS.get(chat_profile, BOTS["larry"])

    cl.user_session.set("history", [])
    cl.user_session.set("bot", bot)
    cl.user_session.set("current_phase", 0)

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
                label="📖 Show Example",
                description="See an example of this phase"
            ),
            cl.Action(
                name="next_phase",
                payload={"action": "next"},
                label="➡️ Next Phase",
                description="Move to the next workshop phase"
            ),
            cl.Action(
                name="show_progress",
                payload={"action": "progress"},
                label="📊 Show Progress",
                description="View your workshop progress"
            ),
        ]
        await cl.Message(content=bot["welcome"], actions=actions).send()
    else:
        await cl.Message(content=bot["welcome"]).send()


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


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with streaming."""

    bot = cl.user_session.get("bot", BOTS["larry"])
    history = cl.user_session.get("history", [])
    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])

    # Check for file attachments
    if message.elements:
        for element in message.elements:
            if hasattr(element, 'path'):
                await cl.Message(content=f"📎 Received file: **{element.name}**").send()

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

    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=message.content + phase_context)]
    ))

    # Create streaming message
    msg = cl.Message(content="")
    await msg.send()

    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-3-flash-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=bot["system_prompt"],
            ),
        )

        full_response = ""
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                await msg.stream_token(chunk.text)

        # Add action buttons to response for workshop bots
        if bot.get("has_phases"):
            msg.actions = [
                cl.Action(
                    name="show_example",
                    payload={"action": "example"},
                    label="📖 Example",
                ),
                cl.Action(
                    name="next_phase",
                    payload={"action": "next"},
                    label="➡️ Next Phase",
                ),
            ]

        await msg.update()

        # Update history
        history.append({"role": "user", "content": message.content})
        history.append({"role": "model", "content": full_response})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n⚠️ Error: {str(e)}")
        await msg.update()


# === File Upload Handler ===
@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.AudioChunk):
    """Handle audio input chunks for voice messages."""
    if chunk.isStart:
        buffer = cl.user_session.get("audio_buffer", b"")
        cl.user_session.set("audio_buffer", buffer + chunk.data)
    else:
        buffer = cl.user_session.get("audio_buffer", b"")
        cl.user_session.set("audio_buffer", buffer + chunk.data)


@cl.on_audio_end
async def on_audio_end(elements: list):
    """Process completed audio input."""
    audio_buffer = cl.user_session.get("audio_buffer", b"")
    if audio_buffer:
        await cl.Message(content="🎤 Audio received! (Transcription coming soon)").send()
        cl.user_session.set("audio_buffer", b"")
