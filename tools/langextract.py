"""
LangExtract - Zero-Latency Structured Data Extraction for Mindrian
Extracts structured insights from unstructured data without impacting response time.

Two modes:
1. instant_extract() - Regex-based, <5ms, runs synchronously
2. background_extract() - LLM-based, runs async after response sent

Storage:
- In-memory cache for fast access during session
- Supabase bucket for persistent storage across sessions
"""

import os
import re
import json
import asyncio
import hashlib
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime

# ============================================================================
# EXTRACTION CACHE - In-memory + Supabase persistence
# ============================================================================

# In-memory cache for current session (fast access)
extraction_cache: Dict[str, Dict] = {}

# Supabase folder for extractions
EXTRACTIONS_FOLDER = "extractions"


def get_cache_key(text: str, extract_type: str = "general") -> str:
    """Generate cache key from text content."""
    text_hash = hashlib.md5(text[:1000].encode()).hexdigest()[:12]
    return f"{extract_type}_{text_hash}"


def get_cached_extraction(text: str, extract_type: str = "general") -> Optional[Dict]:
    """Retrieve cached extraction - checks memory first, then Supabase."""
    key = get_cache_key(text, extract_type)

    # Check memory cache first (fastest)
    if key in extraction_cache:
        return extraction_cache[key]

    # Check Supabase if not in memory
    supabase_data = _load_from_supabase(key)
    if supabase_data:
        # Populate memory cache for future access
        extraction_cache[key] = supabase_data
        return supabase_data

    return None


def cache_extraction(text: str, extraction: Dict, extract_type: str = "general", session_id: str = None):
    """Store extraction in memory cache AND Supabase for persistence."""
    key = get_cache_key(text, extract_type)

    enriched_extraction = {
        **extraction,
        "_cache_key": key,
        "_cached_at": datetime.now().isoformat(),
        "_type": extract_type,
        "_session_id": session_id
    }

    # Store in memory (fast access)
    extraction_cache[key] = enriched_extraction

    # Store in Supabase (persistence)
    _save_to_supabase(key, enriched_extraction)

    return key


def _save_to_supabase(key: str, extraction: Dict) -> bool:
    """Save extraction to Supabase Storage as JSON."""
    try:
        from utils.storage import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            return False

        # Convert to JSON
        json_content = json.dumps(extraction, indent=2, default=str)

        # Save to Supabase
        storage_path = f"{EXTRACTIONS_FOLDER}/{key}.json"

        # Upload JSON content
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=json_content.encode('utf-8'),
            file_options={"content-type": "application/json", "upsert": "true"}
        )

        return True

    except Exception as e:
        print(f"Supabase save error: {e}")
        return False


def _load_from_supabase(key: str) -> Optional[Dict]:
    """Load extraction from Supabase Storage."""
    try:
        from utils.storage import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            return None

        storage_path = f"{EXTRACTIONS_FOLDER}/{key}.json"

        # Download JSON content
        result = client.storage.from_(SUPABASE_BUCKET).download(storage_path)

        if result:
            return json.loads(result.decode('utf-8'))

        return None

    except Exception as e:
        # File doesn't exist or other error - not necessarily an error
        return None


def list_stored_extractions(limit: int = 50) -> List[Dict]:
    """List all extractions stored in Supabase."""
    try:
        from utils.storage import get_supabase_client, SUPABASE_BUCKET

        client = get_supabase_client()
        if not client:
            return []

        result = client.storage.from_(SUPABASE_BUCKET).list(EXTRACTIONS_FOLDER)

        extractions = []
        for item in result[:limit]:
            if item.get("name", "").endswith(".json"):
                extractions.append({
                    "key": item["name"].replace(".json", ""),
                    "created_at": item.get("created_at"),
                    "size": item.get("metadata", {}).get("size", 0)
                })

        return extractions

    except Exception as e:
        print(f"List extractions error: {e}")
        return []

# ============================================================================
# INSTANT EXTRACTION - Pattern-based, NO API calls (<5ms)
# ============================================================================

# PWS-relevant patterns
PATTERNS = {
    # Statistics and numbers
    "percentages": r'\b\d+(?:\.\d+)?%',
    "money": r'\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|thousand|B|M|K))?',
    "large_numbers": r'\b\d{1,3}(?:,\d{3})+\b',
    "years": r'\b(?:19|20)\d{2}\b',

    # Source indicators
    "citations": r'(?:according to|cited by|reported by|study by|research from|data from|per)\s+[A-Z][a-zA-Z\s]+',
    "quotes": r'"[^"]{20,}"',

    # PWS-specific signals
    "assumptions": r'\b(?:assume|assuming|assumption|if we|given that|suppose|supposing|premise|presume)\b',
    "problems": r'\b(?:problem|issue|challenge|pain point|difficulty|obstacle|barrier|bottleneck)\b',
    "solutions": r'\b(?:solution|solve|fix|address|resolve|approach|strategy|method)\b',
    "questions": r'[^.!]*\?',
    "causation": r'\b(?:because|therefore|thus|hence|consequently|as a result|leads to|causes|due to)\b',

    # Confidence/uncertainty markers
    "certainty": r'\b(?:definitely|certainly|clearly|obviously|undoubtedly|proven|confirmed)\b',
    "uncertainty": r'\b(?:might|maybe|perhaps|possibly|could be|uncertain|unclear|debatable)\b',

    # Trend indicators (for TTA)
    "trends": r'\b(?:trend|trending|emerging|growing|declining|shifting|changing|evolving)\b',
    "future": r'\b(?:will|future|forecast|predict|projection|by 20\d{2}|next \d+ years)\b',
}

def instant_extract(text: str) -> Dict[str, Any]:
    """
    Instant pattern-based extraction - NO API calls, <5ms latency.

    Returns structured signals about the content without deep analysis.
    """
    if not text or len(text) < 10:
        return {"empty": True, "signals": {}}

    text_lower = text.lower()

    # Extract all pattern matches
    extractions = {
        "signals": {},
        "counts": {},
        "samples": {},
    }

    for pattern_name, pattern in PATTERNS.items():
        flags = re.IGNORECASE if pattern_name not in ["quotes"] else 0
        matches = re.findall(pattern, text, flags)

        if matches:
            extractions["signals"][pattern_name] = True
            extractions["counts"][pattern_name] = len(matches)
            # Store first 3 samples
            extractions["samples"][pattern_name] = matches[:3]
        else:
            extractions["signals"][pattern_name] = False
            extractions["counts"][pattern_name] = 0

    # Calculate quality indicators
    extractions["quality_signals"] = {
        "has_data": extractions["signals"].get("percentages", False) or
                    extractions["signals"].get("money", False) or
                    extractions["signals"].get("large_numbers", False),
        "has_sources": extractions["signals"].get("citations", False) or
                       extractions["signals"].get("quotes", False),
        "has_pws_elements": extractions["signals"].get("problems", False) or
                           extractions["signals"].get("assumptions", False),
        "has_uncertainty": extractions["signals"].get("uncertainty", False),
        "is_forward_looking": extractions["signals"].get("future", False) or
                              extractions["signals"].get("trends", False),
    }

    # Quick content classification
    problem_count = extractions["counts"].get("problems", 0)
    solution_count = extractions["counts"].get("solutions", 0)
    question_count = extractions["counts"].get("questions", 0)

    if question_count > 2:
        extractions["content_type"] = "exploratory"
    elif problem_count > solution_count:
        extractions["content_type"] = "problem_focused"
    elif solution_count > problem_count:
        extractions["content_type"] = "solution_focused"
    else:
        extractions["content_type"] = "general"

    extractions["char_count"] = len(text)
    extractions["word_count"] = len(text.split())

    return extractions


def instant_extract_research(results: List[Dict]) -> Dict[str, Any]:
    """
    Instant extraction optimized for Tavily search results.
    """
    if not results:
        return {"empty": True, "results_analyzed": 0}

    combined_text = ""
    sources = []

    for r in results:
        content = r.get("content", "") or r.get("snippet", "")
        combined_text += content + "\n"
        sources.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "score": r.get("score", 0)
        })

    base_extraction = instant_extract(combined_text)

    return {
        **base_extraction,
        "results_analyzed": len(results),
        "sources": sources,
        "source_diversity": len(set(r.get("url", "").split("/")[2] if r.get("url") else "" for r in results))
    }


def instant_extract_document(text: str, metadata: Dict) -> Dict[str, Any]:
    """
    Instant extraction optimized for uploaded documents.
    """
    base_extraction = instant_extract(text)

    # Document-specific analysis
    paragraphs = text.split("\n\n")

    return {
        **base_extraction,
        "document_type": metadata.get("type", "unknown"),
        "paragraph_count": len([p for p in paragraphs if len(p) > 50]),
        "has_structure": "---" in text or "##" in text or len(paragraphs) > 5,
        "metadata": metadata
    }


# ============================================================================
# BACKGROUND EXTRACTION - LLM-based, runs async after response
# ============================================================================

async def background_extract_pws(
    text: str,
    context: str = "",
    extract_type: str = "general"
) -> Dict[str, Any]:
    """
    Deep LLM-based extraction for PWS-relevant structures.
    Runs in background - does NOT block user response.

    Args:
        text: Content to extract from
        context: Additional context (conversation history, etc.)
        extract_type: Type of extraction (research, document, conversation)

    Returns:
        Structured extraction with PWS elements
    """
    # Check cache first
    cached = get_cached_extraction(text, extract_type)
    if cached:
        return cached

    try:
        from google import genai

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        extraction_prompt = f"""Extract structured information from this content for a PWS (Problems Worth Solving) analysis.

CONTENT TO ANALYZE:
{text[:8000]}

{f"CONTEXT: {context[:1000]}" if context else ""}

Return a JSON object with these fields:
{{
    "core_problem": "The main problem or question being addressed (1 sentence)",
    "sub_problems": ["List of related sub-problems or aspects"],
    "stated_assumptions": ["Explicitly stated assumptions"],
    "hidden_assumptions": ["Implied but unstated assumptions"],
    "key_facts": [
        {{"fact": "The factual claim", "source": "Where it came from", "confidence": "high/medium/low"}}
    ],
    "statistics": [
        {{"value": "The number/percentage", "context": "What it measures", "source": "Citation if any"}}
    ],
    "open_questions": ["Questions that remain unanswered"],
    "potential_biases": ["Possible biases in the content"],
    "pws_relevance": {{
        "problem_clarity": 1-10,
        "data_grounding": 1-10,
        "assumption_awareness": 1-10
    }},
    "suggested_next_steps": ["What to explore next"]
}}

Return ONLY valid JSON, no markdown or explanation."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=extraction_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2000
            )
        )

        # Parse JSON response
        import json
        response_text = response.text.strip()

        # Clean up potential markdown wrapping
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        extraction = json.loads(response_text)

        # Cache the result
        cache_extraction(text, extraction, extract_type)

        return extraction

    except Exception as e:
        return {
            "error": str(e),
            "fallback": instant_extract(text)
        }


async def background_extract_research(
    query: str,
    results: List[Dict]
) -> Dict[str, Any]:
    """
    Deep extraction for Tavily research results.
    """
    if not results:
        return {"empty": True}

    # Combine results into analyzable text
    combined = f"Research Query: {query}\n\n"
    for i, r in enumerate(results, 1):
        combined += f"Source {i}: {r.get('title', 'Unknown')}\n"
        combined += f"URL: {r.get('url', 'N/A')}\n"
        combined += f"Content: {r.get('content', r.get('snippet', ''))}\n\n"

    return await background_extract_pws(combined, extract_type="research")


async def background_extract_conversation(
    history: List[Dict],
    current_bot: str = "larry"
) -> Dict[str, Any]:
    """
    Extract structured insights from conversation history.
    """
    if not history or len(history) < 2:
        return {"empty": True, "message_count": len(history) if history else 0}

    # Format conversation
    conversation_text = ""
    for msg in history[-30:]:  # Last 30 messages
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")[:500]
        conversation_text += f"{role}: {content}\n\n"

    return await background_extract_pws(
        conversation_text,
        context=f"Conversation with {current_bot} bot",
        extract_type="conversation"
    )


# ============================================================================
# EXTRACTION FORMATTING - Convert to readable output
# ============================================================================

def format_instant_extraction(extraction: Dict) -> str:
    """Format instant extraction as readable markdown."""
    if extraction.get("empty"):
        return "*No content to analyze*"

    lines = ["### Quick Analysis\n"]

    quality = extraction.get("quality_signals", {})
    if quality.get("has_data"):
        lines.append("- **Data Present**: Statistics/numbers detected")
    if quality.get("has_sources"):
        lines.append("- **Sources Cited**: References found")
    if quality.get("has_pws_elements"):
        lines.append("- **PWS Elements**: Problems/assumptions identified")
    if quality.get("has_uncertainty"):
        lines.append("- **Uncertainty**: Hedging language detected")
    if quality.get("is_forward_looking"):
        lines.append("- **Forward-Looking**: Trends/predictions present")

    content_type = extraction.get("content_type", "general")
    lines.append(f"\n**Content Type:** {content_type.replace('_', ' ').title()}")

    # Show samples if available
    samples = extraction.get("samples", {})
    if samples.get("percentages"):
        lines.append(f"\n**Statistics Found:** {', '.join(samples['percentages'][:5])}")
    if samples.get("questions"):
        lines.append(f"\n**Questions Raised:** {len(samples['questions'])} questions")

    return "\n".join(lines)


def format_deep_extraction(extraction: Dict) -> str:
    """Format deep LLM extraction as readable markdown."""
    if extraction.get("error"):
        return f"*Extraction error: {extraction['error']}*"

    if extraction.get("empty"):
        return "*No content to analyze*"

    lines = ["## Structured Analysis\n"]

    if extraction.get("core_problem"):
        lines.append(f"### Core Problem\n{extraction['core_problem']}\n")

    if extraction.get("sub_problems"):
        lines.append("### Related Aspects")
        for sp in extraction["sub_problems"][:5]:
            lines.append(f"- {sp}")
        lines.append("")

    if extraction.get("stated_assumptions"):
        lines.append("### Stated Assumptions")
        for a in extraction["stated_assumptions"][:5]:
            lines.append(f"- {a}")
        lines.append("")

    if extraction.get("hidden_assumptions"):
        lines.append("### Hidden Assumptions")
        for a in extraction["hidden_assumptions"][:5]:
            lines.append(f"- {a}")
        lines.append("")

    if extraction.get("key_facts"):
        lines.append("### Key Facts")
        for f in extraction["key_facts"][:5]:
            confidence = f.get("confidence", "unknown")
            source = f.get("source", "unspecified")
            lines.append(f"- {f.get('fact', '')} *(Source: {source}, Confidence: {confidence})*")
        lines.append("")

    if extraction.get("statistics"):
        lines.append("### Statistics")
        for s in extraction["statistics"][:5]:
            lines.append(f"- **{s.get('value', '')}**: {s.get('context', '')} *(Source: {s.get('source', 'N/A')})*")
        lines.append("")

    if extraction.get("open_questions"):
        lines.append("### Open Questions")
        for q in extraction["open_questions"][:5]:
            lines.append(f"- {q}")
        lines.append("")

    if extraction.get("pws_relevance"):
        rel = extraction["pws_relevance"]
        lines.append("### PWS Quality Scores")
        lines.append(f"- Problem Clarity: **{rel.get('problem_clarity', '?')}/10**")
        lines.append(f"- Data Grounding: **{rel.get('data_grounding', '?')}/10**")
        lines.append(f"- Assumption Awareness: **{rel.get('assumption_awareness', '?')}/10**")
        lines.append("")

    if extraction.get("suggested_next_steps"):
        lines.append("### Suggested Next Steps")
        for step in extraction["suggested_next_steps"][:5]:
            lines.append(f"- {step}")

    return "\n".join(lines)


# ============================================================================
# TAVILY EXTRACT INTEGRATION
# ============================================================================

async def extract_from_urls(urls: List[str], extract_depth: str = "basic") -> Dict[str, Any]:
    """
    Use Tavily Extract API to get clean structured content from URLs.

    Args:
        urls: List of URLs to extract content from
        extract_depth: "basic" or "advanced"

    Returns:
        Extracted content with metadata
    """
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"error": "Tavily API key not configured"}

    try:
        client = TavilyClient(api_key=api_key)

        response = client.extract(
            urls=urls[:5],  # Limit to 5 URLs
            extract_depth=extract_depth
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "raw_content": r.get("raw_content", ""),
                "extracted_at": datetime.now().isoformat()
            })

        return {
            "success": True,
            "urls_processed": len(results),
            "results": results,
            "failed_urls": response.get("failed_results", [])
        }

    except Exception as e:
        return {"error": str(e), "success": False}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_extraction_summary(extraction: Dict) -> str:
    """Get a one-line summary of extraction results."""
    if extraction.get("empty"):
        return "No content"

    signals = extraction.get("quality_signals", {})
    parts = []

    if signals.get("has_data"):
        parts.append("data")
    if signals.get("has_sources"):
        parts.append("sources")
    if signals.get("has_pws_elements"):
        parts.append("PWS elements")

    if parts:
        return f"Contains: {', '.join(parts)}"
    return "General content"


def clear_extraction_cache():
    """Clear the extraction cache."""
    global extraction_cache
    extraction_cache = {}
    return {"cleared": True, "timestamp": datetime.now().isoformat()}


# ============================================================================
# INTELLIGENCE LAYER - Coaching hints + background coherence tracking
# ============================================================================

def get_extraction_hint(signals: Dict[str, Any], turn_count: int = 0) -> Optional[str]:
    """
    Generate a 1-sentence coaching instruction based on extraction signals.
    Returns None if no actionable hint is warranted.

    Used as invisible context appended to system message — not shown to user.
    """
    if not signals or signals.get("empty"):
        return None

    content_type = signals.get("content_type", "general")
    counts = signals.get("counts", {})
    quality = signals.get("quality_signals", {})

    # Solution-focused + no problems → redirect to problem definition
    if content_type == "solution_focused" and counts.get("problems", 0) == 0:
        return "[Coaching hint: The user is jumping to solutions without defining the problem. Gently redirect them to articulate the problem first before exploring solutions.]"

    # High assumptions + no data → probe which assumptions to validate
    if counts.get("assumptions", 0) >= 2 and not quality.get("has_data"):
        return "[Coaching hint: The user is making multiple assumptions without data support. Ask which assumptions they consider most critical and what evidence would validate them.]"

    # High certainty + no sources → ask what evidence supports this
    if counts.get("certainty", 0) >= 1 and not quality.get("has_sources"):
        return "[Coaching hint: The user expresses high certainty but cites no sources. Ask what evidence or experience supports their confidence.]"

    # Forward-looking + no data → ask what current data supports projection
    if quality.get("is_forward_looking") and not quality.get("has_data"):
        return "[Coaching hint: The user is making forward-looking claims without current data. Ask what present-day data or trends support their projection.]"

    return None


async def background_intelligence(
    history: List[Dict],
    bot_id: str = "larry",
    session=None,
) -> None:
    """
    Fire-and-forget background task: deep extraction + coherence tracking.

    Runs every ~5 turns. Stores coherence metrics in session and caches
    extraction to Supabase.
    """
    try:
        extraction = await background_extract_conversation(history, bot_id)

        if not extraction or extraction.get("empty"):
            return

        # Store coherence metrics in session for research tool scoring
        pws_relevance = extraction.get("pws_relevance", {})
        if pws_relevance and session:
            try:
                session.set("extraction_coherence", {
                    "problem_clarity": pws_relevance.get("problem_clarity", 5),
                    "data_grounding": pws_relevance.get("data_grounding", 5),
                    "assumption_awareness": pws_relevance.get("assumption_awareness", 5),
                })
            except Exception:
                pass

        # Cache full extraction to Supabase
        conversation_text = " ".join(
            msg.get("content", "")[:200] for msg in history[-10:]
        )
        cache_extraction(conversation_text, extraction, "conversation_intelligence")

    except Exception as e:
        print(f"Background intelligence error (non-fatal): {e}")
