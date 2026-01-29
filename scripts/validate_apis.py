#!/usr/bin/env python3
"""
API Validation Script for Mindrian
===================================

Tests all external APIs used across the tools directory.
Run with: python scripts/validate_apis.py
"""

import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Results tracking
results = {
    "passed": [],
    "failed": [],
    "skipped": []
}


def log(status: str, name: str, message: str):
    """Log a test result."""
    icons = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠️", "INFO": "ℹ️"}
    print(f"{icons.get(status, '•')} [{status}] {name}: {message}")

    if status == "PASS":
        results["passed"].append(name)
    elif status == "FAIL":
        results["failed"].append((name, message))
    elif status == "SKIP":
        results["skipped"].append((name, message))


def test_env_var(name: str) -> bool:
    """Check if environment variable is set."""
    value = os.getenv(name)
    if value:
        masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
        log("PASS", f"ENV:{name}", f"Set ({masked})")
        return True
    else:
        log("SKIP", f"ENV:{name}", "Not set")
        return False


# ============================================================
# 1. GOOGLE GEMINI API
# ============================================================
def test_gemini_api():
    """Test Google Gemini API connection."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        log("SKIP", "Gemini API", "GOOGLE_API_KEY not set")
        return

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say 'API test successful' in exactly those words."
        )
        if response and response.text:
            log("PASS", "Gemini API", f"Response: {response.text[:50]}...")
        else:
            log("FAIL", "Gemini API", "Empty response")
    except Exception as e:
        log("FAIL", "Gemini API", str(e)[:100])


# ============================================================
# 2. TAVILY SEARCH API
# ============================================================
def test_tavily_api():
    """Test Tavily search API."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        log("SKIP", "Tavily API", "TAVILY_API_KEY not set")
        return

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        result = client.search("test query", max_results=1)
        if result and result.get("results"):
            log("PASS", "Tavily API", f"Found {len(result['results'])} results")
        else:
            log("FAIL", "Tavily API", "No results returned")
    except Exception as e:
        log("FAIL", "Tavily API", str(e)[:100])


# ============================================================
# 3. NEO4J DATABASE
# ============================================================
def test_neo4j():
    """Test Neo4j database connection."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not password:
        log("SKIP", "Neo4j", "NEO4J_URI or NEO4J_PASSWORD not set")
        return

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
            record = result.single()
            count = record["count"] if record else 0
            log("PASS", "Neo4j", f"Connected, {count} nodes in database")
        driver.close()
    except Exception as e:
        log("FAIL", "Neo4j", str(e)[:100])


# ============================================================
# 4. NEWSMESH API
# ============================================================
def test_newsmesh_api():
    """Test NewsMesh news API."""
    api_key = os.getenv("NEWSMESH_API_KEY")
    if not api_key:
        log("SKIP", "NewsMesh API", "NEWSMESH_API_KEY not set")
        return

    try:
        from tools.news_search import search_news
        result = search_news("technology", max_results=2)
        if result.get("error"):
            log("FAIL", "NewsMesh API", result["error"])
        elif result.get("articles"):
            log("PASS", "NewsMesh API", f"Found {len(result['articles'])} articles")
        else:
            log("FAIL", "NewsMesh API", "No articles returned")
    except Exception as e:
        log("FAIL", "NewsMesh API", str(e)[:100])


# ============================================================
# 5. SERPAPI (GOOGLE TRENDS & PATENTS)
# ============================================================
def test_serpapi():
    """Test SerpAPI for Google Trends."""
    api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        log("SKIP", "SerpAPI", "SERPAPI_KEY not set")
        return

    try:
        from tools.trends_search import search_trends
        result = search_trends("artificial intelligence", date="today 1-m")
        if result.get("error"):
            log("FAIL", "SerpAPI Trends", result["error"])
        elif result.get("data"):
            log("PASS", "SerpAPI Trends", "Trend data retrieved")
        else:
            log("FAIL", "SerpAPI Trends", "No data returned")
    except Exception as e:
        log("FAIL", "SerpAPI Trends", str(e)[:100])


# ============================================================
# 6. FRED API (Federal Reserve)
# ============================================================
def test_fred_api():
    """Test FRED economic data API."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        log("SKIP", "FRED API", "FRED_API_KEY not set")
        return

    try:
        from tools.govdata_search import search_fred
        result = search_fred("GDP")
        if result.get("error"):
            log("FAIL", "FRED API", result["error"])
        elif result.get("series"):
            log("PASS", "FRED API", f"Found {len(result['series'])} series")
        else:
            log("FAIL", "FRED API", "No series returned")
    except Exception as e:
        log("FAIL", "FRED API", str(e)[:100])


# ============================================================
# 7. BLS API (Bureau of Labor Statistics)
# ============================================================
def test_bls_api():
    """Test BLS labor statistics API."""
    # BLS v1 works without key
    try:
        from tools.govdata_search import search_bls
        result = search_bls("unemployment")  # Query string
        if result.get("error"):
            log("FAIL", "BLS API", result["error"])
        elif result.get("series"):
            latest = result["series"][0].get("latest", {})
            value = latest.get("value", "?")
            log("PASS", "BLS API", f"Unemployment rate: {value}%")
        else:
            log("FAIL", "BLS API", "No series returned")
    except Exception as e:
        log("FAIL", "BLS API", str(e)[:100])


# ============================================================
# 8. CENSUS/DATA.GOV API
# ============================================================
def test_census_api():
    """Test Census/Data.gov API."""
    api_key = os.getenv("DATA_GOV_API_KEY") or os.getenv("CENSUS_API_KEY")
    if not api_key:
        log("SKIP", "Census API", "DATA_GOV_API_KEY not set")
        return

    try:
        from tools.govdata_search import search_census_acs
        result = search_census_acs("population", state="06")  # California
        if result.get("error"):
            log("FAIL", "Census API", result["error"])
        elif result.get("data"):
            log("PASS", "Census API", "Census data retrieved")
        else:
            log("FAIL", "Census API", "No data returned")
    except Exception as e:
        log("FAIL", "Census API", str(e)[:100])


# ============================================================
# 9. KAGGLE API
# ============================================================
def test_kaggle_api():
    """Test Kaggle datasets API."""
    # Check for either KAGGLE_API_TOKEN (Render) or KAGGLE_USERNAME+KEY (legacy)
    token = os.getenv("KAGGLE_API_TOKEN")
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")

    if not token and (not username or not key):
        log("SKIP", "Kaggle API", "KAGGLE_API_TOKEN not set")
        return

    try:
        from tools.dataset_search import search_kaggle
        result = search_kaggle("machine learning")
        if result.get("error"):
            log("FAIL", "Kaggle API", result["error"])
        elif result.get("datasets"):
            log("PASS", "Kaggle API", f"Found {len(result['datasets'])} datasets")
        else:
            log("FAIL", "Kaggle API", "No datasets returned")
    except Exception as e:
        log("FAIL", "Kaggle API", str(e)[:100])


# ============================================================
# 10. ANTHROPIC API (Claude)
# ============================================================
def test_anthropic_api():
    """Test Anthropic Claude API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log("SKIP", "Anthropic API", "ANTHROPIC_API_KEY not set")
        return

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'API test successful'"}]
        )
        if response and response.content:
            log("PASS", "Anthropic API", f"Claude responded")
        else:
            log("FAIL", "Anthropic API", "Empty response")
    except ImportError:
        log("SKIP", "Anthropic API", "anthropic package not installed")
    except Exception as e:
        log("FAIL", "Anthropic API", str(e)[:100])


# ============================================================
# 11. ELEVENLABS API (Voice)
# ============================================================
def test_elevenlabs_api():
    """Test ElevenLabs TTS API."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        log("SKIP", "ElevenLabs API", "ELEVENLABS_API_KEY not set")
        return

    try:
        import requests
        headers = {"xi-api-key": api_key}
        resp = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, timeout=10)
        if resp.status_code == 200:
            voices = resp.json().get("voices", [])
            log("PASS", "ElevenLabs API", f"{len(voices)} voices available")
        else:
            log("FAIL", "ElevenLabs API", f"HTTP {resp.status_code}")
    except Exception as e:
        log("FAIL", "ElevenLabs API", str(e)[:100])


# ============================================================
# 12. DEEPGRAM API (Speech-to-Text)
# ============================================================
def test_deepgram_api():
    """Test Deepgram STT API."""
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        log("SKIP", "Deepgram API", "DEEPGRAM_API_KEY not set")
        return

    try:
        import requests
        headers = {"Authorization": f"Token {api_key}"}
        resp = requests.get("https://api.deepgram.com/v1/projects", headers=headers, timeout=10)
        if resp.status_code == 200:
            log("PASS", "Deepgram API", "Connected")
        else:
            log("FAIL", "Deepgram API", f"HTTP {resp.status_code}")
    except Exception as e:
        log("FAIL", "Deepgram API", str(e)[:100])


# ============================================================
# 13. ARXIV API (No key needed)
# ============================================================
def test_arxiv_api():
    """Test arXiv papers search."""
    try:
        from tools.arxiv_search import search_papers
        result = search_papers("machine learning", max_results=2)
        if result.get("error"):
            log("FAIL", "arXiv API", result["error"])
        elif result.get("papers"):
            log("PASS", "arXiv API", f"Found {len(result['papers'])} papers")
        else:
            log("FAIL", "arXiv API", "No papers returned")
    except Exception as e:
        log("FAIL", "arXiv API", str(e)[:100])


# ============================================================
# 11. TOOL IMPORTS
# ============================================================
def test_tool_imports():
    """Test that all tools can be imported."""
    tools = [
        ("tavily_search", "search_web"),
        ("news_search", "search_news"),
        ("trends_search", "search_trends"),
        ("arxiv_search", "search_papers"),
        ("patent_search", "search_patents"),
        ("govdata_search", "search_fred"),
        ("dataset_search", "search_kaggle"),
        ("graphrag_lite", "enrich_for_larry"),
        ("langextract", "instant_extract"),
        ("phase_validator", "validate_phase_completion"),
        ("phase_enricher", "enrich_phase_context"),
        ("deep_research", "run_deep_research"),
    ]

    for module, func in tools:
        try:
            mod = __import__(f"tools.{module}", fromlist=[func])
            if hasattr(mod, func):
                log("PASS", f"Import:{module}", f"{func}() available")
            else:
                log("FAIL", f"Import:{module}", f"{func}() not found")
        except Exception as e:
            log("FAIL", f"Import:{module}", str(e)[:80])


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("MINDRIAN API VALIDATION")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Environment variables check
    print("--- ENVIRONMENT VARIABLES ---")
    env_vars = [
        # Core AI
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        # Search & Research
        "TAVILY_API_KEY",
        "SERPAPI_KEY",
        "NEWSMESH_API_KEY",
        # Graph & Database
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "DATABASE_URL",
        "CHAINLIT_DATABASE_URL",
        # Storage
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        # Voice
        "ELEVENLABS_API_KEY",
        "DEEPGRAM_API_KEY",
        # Economic Data
        "FRED_API_KEY",
        "BLS_API_KEY",
        # Datasets
        "KAGGLE_API_TOKEN",
    ]
    for var in env_vars:
        test_env_var(var)
    print()

    # Tool imports
    print("--- TOOL IMPORTS ---")
    test_tool_imports()
    print()

    # API tests
    print("--- API CONNECTIVITY ---")
    print()
    print("Core AI:")
    test_gemini_api()
    test_anthropic_api()
    print()
    print("Search & Research:")
    test_tavily_api()
    test_serpapi()
    test_newsmesh_api()
    test_arxiv_api()
    print()
    print("Graph & Database:")
    test_neo4j()
    print()
    print("Voice:")
    test_elevenlabs_api()
    test_deepgram_api()
    print()
    print("Economic Data:")
    test_fred_api()
    test_bls_api()
    test_census_api()
    test_kaggle_api()
    print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ PASSED: {len(results['passed'])}")
    print(f"❌ FAILED: {len(results['failed'])}")
    print(f"⚠️  SKIPPED: {len(results['skipped'])}")
    print()

    if results["failed"]:
        print("FAILURES:")
        for name, msg in results["failed"]:
            print(f"  - {name}: {msg}")
        print()

    if results["skipped"]:
        print("SKIPPED (missing API keys):")
        for name, msg in results["skipped"]:
            print(f"  - {name}")
        print()

    # Exit code
    return 1 if results["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
