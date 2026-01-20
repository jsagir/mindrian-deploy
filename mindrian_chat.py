"""
Mindrian - Multi-Bot PWS Platform
Larry Core + Specialized Tool Workshop Bots
"""

import os
import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

# === Config ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")

client = genai.Client(api_key=GOOGLE_API_KEY)

# === System Prompts ===
from prompts import (
    LARRY_RAG_SYSTEM_PROMPT,
    TTA_WORKSHOP_PROMPT,
    JTBD_WORKSHOP_PROMPT,
    SCURVE_WORKSHOP_PROMPT,
    REDTEAM_PROMPT
)

# === Bot Configurations ===
BOTS = {
    "larry": {
        "name": "Larry",
        "icon": "🧠",
        "description": "General PWS thinking partner",
        "system_prompt": LARRY_RAG_SYSTEM_PROMPT,
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
        "welcome": """😈 **Red Teaming Session**

I'm Larry, and right now I'm your devil's advocate.

My job is to find the holes in your thinking before the market does. I'm going to challenge your assumptions, stress-test your logic, and look for the fatal flaw.

This isn't about being negative — it's about making your idea bulletproof.

**What idea, plan, or assumption do you want me to attack?**"""
    }
}


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

    await cl.Message(content=bot["welcome"]).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with streaming."""

    bot = cl.user_session.get("bot", BOTS["larry"])
    history = cl.user_session.get("history", [])

    # Build contents for Gemini
    contents = []
    for msg in history:
        contents.append(types.Content(
            role=msg["role"],
            parts=[types.Part(text=msg["content"])]
        ))

    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=message.content)]
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

        await msg.update()

        # Update history
        history.append({"role": "user", "content": message.content})
        history.append({"role": "model", "content": full_response})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n⚠️ Error: {str(e)}")
        await msg.update()
