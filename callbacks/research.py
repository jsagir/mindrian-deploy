"""
Research Tool Callbacks
=======================

All research-related action callbacks:
- ArXiv academic search
- Patent search
- Google Trends
- Government data (BLS, FRED, Census)
- Dataset search
- News search

Extracted from mindrian_chat.py lines 7241-7518.
"""

import chainlit as cl
from typing import Optional

# Gemini client (initialized from main app)
client = None


def init_client(gemini_client):
    """Initialize the Gemini client for query extraction."""
    global client
    client = gemini_client


# =============================================================================
# Helper: Extract Last User Message
# =============================================================================

def get_context_for_query(history: list) -> str:
    """
    Build context for query extraction, prioritizing the last user message.

    BUG FIX: This ensures research tools search for the CURRENT topic,
    not stale context from earlier in the conversation.
    """
    last_user_msg = ""
    for m in reversed(history):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")[:200]
            break

    recent = " ".join([m.get("content", "") for m in history[-4:]])[-300:]
    return f"MOST RECENT USER TOPIC: {last_user_msg}\n\nBACKGROUND: {recent}"


# =============================================================================
# ArXiv Academic Search
# =============================================================================

@cl.action_callback("arxiv_search")
async def on_arxiv_search(action: cl.Action):
    """Search ArXiv for academic papers based on conversation context."""
    history = cl.user_session.get("history", [])
    context_for_query = get_context_for_query(history)
    reason = action.payload.get("reason", "Graph suggested academic research")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📚 Finding Academic Evidence**\n*Why: {reason}*\n\n")

    # Extract search query from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract a concise academic search query (max 8 words). IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. Return ONLY the query:\n\n{context_for_query}",
    )
    search_query = qr.text.strip().strip('"')

    from tools.arxiv_search import search_papers, format_papers_markdown
    results = search_papers(search_query, max_results=5)
    formatted = format_papers_markdown(results)

    await msg.stream_token(f"**Query:** {search_query}\n\n{formatted}")
    await msg.update()

    history.append({"role": "model", "content": f"[ArXiv Search: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


# =============================================================================
# Patent Search
# =============================================================================

@cl.action_callback("patent_search")
async def on_patent_search(action: cl.Action):
    """Search patents based on conversation context."""
    history = cl.user_session.get("history", [])
    context_for_query = get_context_for_query(history)
    reason = action.payload.get("reason", "Graph suggested patent landscaping")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**🔎 Checking Prior Art & Innovation Landscape**\n*Why: {reason}*\n\n")

    # Extract search query from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract a concise patent search query (max 8 words). IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. Return ONLY the query:\n\n{context_for_query}",
    )
    search_query = qr.text.strip().strip('"')

    from tools.patent_search import search_patents, format_patents_markdown
    results = search_patents(search_query, max_results=5)
    formatted = format_patents_markdown(results)

    await msg.stream_token(f"**Query:** {search_query}\n\n{formatted}")
    await msg.update()

    history.append({"role": "model", "content": f"[Patent Search: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


# =============================================================================
# Google Trends Search
# =============================================================================

@cl.action_callback("trends_search")
async def on_trends_search(action: cl.Action):
    """Search Google Trends based on conversation context (graph-driven)."""
    history = cl.user_session.get("history", [])
    context_for_query = get_context_for_query(history)
    reason = action.payload.get("reason", "Graph suggested trend analysis")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📈 Measuring Trend Momentum**\n*Why: {reason}*\n\n")

    # Extract 1-3 trend search terms from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Extract 1-3 concise Google Trends search terms (each max 3 words). "
            "IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. "
            "Return ONLY comma-separated terms, no explanation:\n\n" + context_for_query
        ),
    )
    search_query = qr.text.strip().strip('"')

    from tools.trends_search import search_trends, search_related_queries, format_trends_markdown

    # Fetch both timeseries and related queries
    timeseries = search_trends(search_query, data_type="TIMESERIES", date="today 12-m")
    related = search_related_queries(search_query)

    ts_formatted = format_trends_markdown(timeseries)
    rq_formatted = format_trends_markdown(related)

    await msg.stream_token(f"**Terms:** {search_query}\n\n{ts_formatted}\n\n---\n\n{rq_formatted}")
    await msg.update()

    combined = f"[Google Trends: {search_query}]\n{ts_formatted}\n\n{rq_formatted}"
    history.append({"role": "model", "content": combined})
    cl.user_session.set("history", history)


# =============================================================================
# Government Data Search (BLS, FRED, Census)
# =============================================================================

@cl.action_callback("govdata_search")
async def on_govdata_search(action: cl.Action):
    """Search US government data (BLS, FRED, Census) based on conversation context."""
    history = cl.user_session.get("history", [])
    context_for_query = get_context_for_query(history)
    reason = action.payload.get("reason", "Graph suggested public data grounding")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**🏛️ Pulling Public Statistics**\n*Why: {reason}*\n\n")

    # Use Gemini to extract a data-oriented query and pick sources
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Based on this conversation, extract:\n"
            "1. A concise data query (max 8 words)\n"
            "2. Best source: BLS, FRED, or CENSUS\n"
            "IMPORTANT: Focus on the MOST RECENT USER TOPIC.\n"
            "Format: QUERY: <query>\nSOURCE: <source>\n\n" + context_for_query
        ),
    )

    # Parse response
    response_text = qr.text.strip()
    search_query = "economic data"
    source = "FRED"

    for line in response_text.split("\n"):
        if line.startswith("QUERY:"):
            search_query = line.replace("QUERY:", "").strip()
        elif line.startswith("SOURCE:"):
            source = line.replace("SOURCE:", "").strip().upper()

    # Route to appropriate search
    from tools.govdata_search import search_bls, search_fred, search_census, format_govdata_markdown

    if "BLS" in source:
        results = search_bls(search_query, max_results=5)
    elif "CENSUS" in source:
        results = search_census(search_query, max_results=5)
    else:
        results = search_fred(search_query, max_results=5)

    formatted = format_govdata_markdown(results, source)

    await msg.stream_token(f"**Query:** {search_query} (via {source})\n\n{formatted}")
    await msg.update()

    history.append({"role": "model", "content": f"[{source} Data: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


# =============================================================================
# Dataset Search
# =============================================================================

@cl.action_callback("dataset_search")
async def on_dataset_search(action: cl.Action):
    """Search for public datasets based on conversation context."""
    history = cl.user_session.get("history", [])
    context_for_query = get_context_for_query(history)
    reason = action.payload.get("reason", "Graph suggested dataset exploration")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📊 Finding Relevant Datasets**\n*Why: {reason}*\n\n")

    # Extract search query from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract a concise dataset search query (max 8 words). IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. Return ONLY the query:\n\n{context_for_query}",
    )
    search_query = qr.text.strip().strip('"')

    from tools.dataset_search import search_datasets, format_datasets_markdown
    results = search_datasets(search_query, max_results=5)
    formatted = format_datasets_markdown(results)

    await msg.stream_token(f"**Query:** {search_query}\n\n{formatted}")
    await msg.update()

    history.append({"role": "model", "content": f"[Dataset Search: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


# =============================================================================
# News Search
# =============================================================================

@cl.action_callback("news_search")
async def on_news_search(action: cl.Action):
    """Search recent news based on conversation context."""
    history = cl.user_session.get("history", [])
    context_for_query = get_context_for_query(history)
    reason = action.payload.get("reason", "Graph suggested current events context")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📰 Checking Recent News**\n*Why: {reason}*\n\n")

    # Extract search query from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract a concise news search query (max 8 words). IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. Return ONLY the query:\n\n{context_for_query}",
    )
    search_query = qr.text.strip().strip('"')

    from tools.tavily_search import search_web
    results = search_web(search_query, search_depth="basic", max_results=5, topic="news")

    # Format results
    formatted = "**Recent News:**\n\n"
    if results and results.get("results"):
        for i, r in enumerate(results["results"][:5], 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = r.get("content", "")[:200]
            formatted += f"{i}. **[{title}]({url})**\n   {snippet}...\n\n"
    else:
        formatted += "_No recent news found._\n"

    await msg.stream_token(f"**Query:** {search_query}\n\n{formatted}")
    await msg.update()

    history.append({"role": "model", "content": f"[News Search: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


# =============================================================================
# Registration Function
# =============================================================================

def register_research_callbacks():
    """
    Register all research callbacks and initialize client.

    Note: In Chainlit, callbacks are registered via decorators at import time.
    This function can be used for additional setup like client initialization.
    """
    # Import and initialize the Gemini client
    try:
        from google import genai
        import os
        global client
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        print("✅ Research callbacks: Gemini client initialized")
    except Exception as e:
        print(f"⚠️ Research callbacks: Could not initialize Gemini client: {e}")
