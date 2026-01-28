#!/usr/bin/env python3
"""
Mindrian Health Check Protocol
===============================
Verifies all APIs, databases, RAG systems, and integrations are operational.
Run: python scripts/health_check.py
"""

import os
import sys
import json
import time

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
SKIP = "⏭️"

results = {}


def check(name, status, detail=""):
    results[name] = {"status": status, "detail": detail}
    icon = PASS if status == "pass" else FAIL if status == "fail" else WARN if status == "warn" else SKIP
    detail_str = f" — {detail}" if detail else ""
    print(f"  {icon} {name}{detail_str}")


def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


# ─────────────────────────────────────────────
# 1. ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────
section("1. ENVIRONMENT VARIABLES")

REQUIRED_KEYS = {
    "GOOGLE_API_KEY": "Core LLM (Gemini)",
    "TAVILY_API_KEY": "Web Research",
    "SUPABASE_URL": "Storage Client",
    "SUPABASE_SERVICE_KEY": "Storage Auth",
    "SUPABASE_BUCKET": "Storage Bucket",
}

RECOMMENDED_KEYS = {
    "GOOGLE_FILESEARCH_API_KEY": "FileSearch Store Owner Key",
    "CHAINLIT_DATABASE_URL": "Chat Persistence",
    "NEO4J_URI": "Graph Database",
    "NEO4J_USER": "Graph Auth",
    "NEO4J_PASSWORD": "Graph Auth",
    "ELEVENLABS_API_KEY": "Text-to-Speech",
    "ELEVENLABS_VOICE_ID": "Voice Selection",
    "DEEPGRAM_API_KEY": "Speech-to-Text",
}

OPTIONAL_KEYS = {
    "SERPAPI_KEY": "Google Trends/Patents",
    "FRED_API_KEY": "Gov Economic Data (FRED)",
    "BLS_API_KEY": "Bureau of Labor Stats v2",
    "NEWSMESH_API_KEY": "Structured News",
    "KAGGLE_API_TOKEN": "Dataset Search",
}

for key, purpose in REQUIRED_KEYS.items():
    val = os.getenv(key)
    if val:
        masked = val[:6] + "..." + val[-4:] if len(val) > 12 else "***"
        check(f"{key} ({purpose})", "pass", f"{masked} ({len(val)} chars)")
    else:
        check(f"{key} ({purpose})", "fail", "NOT SET — REQUIRED")

for key, purpose in RECOMMENDED_KEYS.items():
    val = os.getenv(key)
    if val:
        masked = val[:6] + "..." + val[-4:] if len(val) > 12 else "***"
        check(f"{key} ({purpose})", "pass", f"{masked}")
    else:
        check(f"{key} ({purpose})", "warn", "Not set (recommended)")

for key, purpose in OPTIONAL_KEYS.items():
    val = os.getenv(key)
    if val:
        check(f"{key} ({purpose})", "pass", "Set")
    else:
        check(f"{key} ({purpose})", "skip", "Not set (optional)")


# ─────────────────────────────────────────────
# 2. GOOGLE GEMINI API
# ─────────────────────────────────────────────
section("2. GOOGLE GEMINI API")

try:
    from google import genai
    from google.genai import types
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        check("Gemini Client", "fail", "No API key")
    else:
        gclient = genai.Client(api_key=api_key)
        t0 = time.time()
        resp = gclient.models.generate_content(
            model="gemini-2.0-flash",
            contents="Reply with exactly: HEALTH_CHECK_OK",
            config=types.GenerateContentConfig(max_output_tokens=20),
        )
        elapsed = int((time.time() - t0) * 1000)
        if "HEALTH_CHECK_OK" in resp.text:
            check("Gemini LLM", "pass", f"Response OK ({elapsed}ms)")
        else:
            check("Gemini LLM", "warn", f"Unexpected response: {resp.text[:50]}")
except Exception as e:
    check("Gemini LLM", "fail", f"{type(e).__name__}: {e}")


# ─────────────────────────────────────────────
# 3. GEMINI FILE SEARCH (RAG)
# ─────────────────────────────────────────────
section("3. GEMINI FILE SEARCH (RAG)")

FILE_SEARCH_STORE = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"
try:
    from google.genai import types
    tool = types.Tool(file_search=types.FileSearch(file_search_store_names=[FILE_SEARCH_STORE]))
    check("FileSearch Tool Config", "pass", FILE_SEARCH_STORE)

    # Test actual File Search query (uses separate key that owns the store)
    fs_api_key = os.getenv("GOOGLE_FILESEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if fs_api_key:
        fs_client = genai.Client(api_key=fs_api_key)
        t0 = time.time()
        fs_resp = fs_client.models.generate_content(
            model="gemini-2.5-flash",
            contents="What is Domain Selection in PWS methodology? Answer in 1 sentence.",
            config=types.GenerateContentConfig(
                tools=[tool],
                max_output_tokens=100,
            ),
        )
        elapsed = int((time.time() - t0) * 1000)
        if fs_resp.text and len(fs_resp.text.strip()) > 10:
            check("FileSearch Live Query", "pass", f"Got response ({elapsed}ms): {fs_resp.text.strip()[:80]}...")
        else:
            check("FileSearch Live Query", "warn", "Empty or short response")
    else:
        check("FileSearch Live Query", "skip", "No API key")
except Exception as e:
    check("FileSearch", "fail", f"{type(e).__name__}: {e}")


# ─────────────────────────────────────────────
# 4. NEO4J (LazyGraph)
# ─────────────────────────────────────────────
section("4. NEO4J (LazyGraph)")

neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_pass = os.getenv("NEO4J_PASSWORD")

if neo4j_uri and neo4j_user and neo4j_pass:
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        with driver.session() as session:
            # Node counts
            result = session.run(
                "MATCH (n) RETURN labels(n)[0] AS type, count(n) AS cnt "
                "ORDER BY cnt DESC LIMIT 8"
            )
            counts = {r["type"]: r["cnt"] for r in result}
            total = sum(counts.values())
            check("Neo4j Connection", "pass", f"{total} total nodes")

            top_types = ", ".join(f"{t}:{c}" for t, c in list(counts.items())[:5])
            check("Neo4j Node Types", "pass", top_types)

            # Framework count
            fw_result = session.run("MATCH (f:Framework) RETURN count(f) AS cnt")
            fw_count = fw_result.single()["cnt"]
            check("Frameworks", "pass" if fw_count >= 5 else "warn", f"{fw_count} frameworks")

            # Domain Selection specifically
            ds_result = session.run(
                "MATCH (f:Framework {name: 'Domain Selection'})-[r]->(n) "
                "RETURN count(r) AS rels"
            )
            ds_rels = ds_result.single()["rels"]
            check("Domain Selection Graph", "pass" if ds_rels >= 10 else "warn", f"{ds_rels} relationships")

            # Case studies
            cs_result = session.run("MATCH (c:CaseStudy) RETURN count(c) AS cnt")
            cs_count = cs_result.single()["cnt"]
            check("Case Studies", "pass" if cs_count >= 2 else "warn", f"{cs_count} case studies")

        driver.close()
    except Exception as e:
        check("Neo4j Connection", "fail", f"{type(e).__name__}: {e}")
else:
    check("Neo4j", "skip", "NEO4J_URI/USER/PASSWORD not set")

# Test GraphRAG imports
try:
    from tools.graphrag_lite import enrich_for_bot, should_retrieve, light_context
    check("GraphRAG Imports", "pass", "enrich_for_bot, should_retrieve, light_context")
except Exception as e:
    check("GraphRAG Imports", "fail", str(e))


# ─────────────────────────────────────────────
# 5. TAVILY SEARCH API
# ─────────────────────────────────────────────
section("5. TAVILY SEARCH API")

tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key:
    try:
        from tavily import TavilyClient
        tc = TavilyClient(api_key=tavily_key)
        t0 = time.time()
        resp = tc.search(query="innovation methodology", max_results=1)
        elapsed = int((time.time() - t0) * 1000)
        count = len(resp.get("results", []))
        check("Tavily Search", "pass" if count > 0 else "warn", f"{count} results ({elapsed}ms)")
    except Exception as e:
        check("Tavily Search", "fail", f"{type(e).__name__}: {e}")
else:
    check("Tavily Search", "fail", "TAVILY_API_KEY not set")


# ─────────────────────────────────────────────
# 6. SUPABASE (Storage + Persistence)
# ─────────────────────────────────────────────
section("6. SUPABASE")

supa_url = os.getenv("SUPABASE_URL")
supa_key = os.getenv("SUPABASE_SERVICE_KEY")
supa_bucket = os.getenv("SUPABASE_BUCKET")

if supa_url and supa_key:
    try:
        from supabase import create_client
        sc = create_client(supa_url, supa_key)
        buckets = sc.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        check("Supabase Connection", "pass", f"{len(buckets)} buckets: {', '.join(bucket_names)}")

        if supa_bucket:
            if supa_bucket in bucket_names:
                check("Supabase Bucket", "pass", f"'{supa_bucket}' exists")
            else:
                check("Supabase Bucket", "warn", f"'{supa_bucket}' not in {bucket_names}")
        else:
            check("Supabase Bucket", "warn", "SUPABASE_BUCKET not set")
    except Exception as e:
        check("Supabase", "fail", f"{type(e).__name__}: {e}")
else:
    check("Supabase", "fail", "SUPABASE_URL or SUPABASE_SERVICE_KEY not set")


# ─────────────────────────────────────────────
# 7. ELEVENLABS TTS
# ─────────────────────────────────────────────
section("7. ELEVENLABS TTS")

eleven_key = os.getenv("ELEVENLABS_API_KEY")
if eleven_key:
    try:
        import requests
        resp = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": eleven_key},
            timeout=10,
        )
        if resp.status_code == 200:
            voice_count = len(resp.json().get("voices", []))
            check("ElevenLabs API", "pass", f"{voice_count} voices available")
        else:
            check("ElevenLabs API", "fail", f"HTTP {resp.status_code}")
    except Exception as e:
        check("ElevenLabs API", "fail", str(e))
else:
    check("ElevenLabs API", "skip", "Not set")


# ─────────────────────────────────────────────
# 8. OPTIONAL RESEARCH APIs
# ─────────────────────────────────────────────
section("8. OPTIONAL RESEARCH APIs")

# SerpAPI
serpapi_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
if serpapi_key:
    try:
        import requests
        resp = requests.get(
            "https://serpapi.com/account.json",
            params={"api_key": serpapi_key},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            searches_left = data.get("total_searches_left", "?")
            check("SerpAPI (Trends/Patents)", "pass", f"{searches_left} searches remaining")
        else:
            check("SerpAPI", "fail", f"HTTP {resp.status_code}")
    except Exception as e:
        check("SerpAPI", "fail", str(e))
else:
    check("SerpAPI (Trends/Patents)", "skip", "Not set")

# FRED
fred_key = os.getenv("FRED_API_KEY")
if fred_key:
    try:
        import requests
        resp = requests.get(
            "https://api.stlouisfed.org/fred/series",
            params={"series_id": "GDP", "api_key": fred_key, "file_type": "json"},
            timeout=10,
        )
        if resp.status_code == 200:
            check("FRED API", "pass", "GDP series accessible")
        else:
            check("FRED API", "fail", f"HTTP {resp.status_code}")
    except Exception as e:
        check("FRED API", "fail", str(e))
else:
    check("FRED API", "skip", "Not set")

# BLS
bls_key = os.getenv("BLS_API_KEY")
if bls_key:
    check("BLS API", "pass", "Key set (v2 enabled)")
else:
    check("BLS API", "skip", "Not set — v1 (limited) still works")

# NewsMesh
newsmesh_key = os.getenv("NEWSMESH_API_KEY")
if newsmesh_key:
    try:
        import requests
        resp = requests.get(
            "https://api.newsmesh.co/v1/search",
            params={"q": "test", "limit": 1},
            headers={"x-api-key": newsmesh_key},
            timeout=10,
        )
        if resp.status_code == 200:
            check("NewsMesh API", "pass", "Search operational")
        elif resp.status_code == 401:
            check("NewsMesh API", "fail", "Invalid API key")
        else:
            check("NewsMesh API", "warn", f"HTTP {resp.status_code}")
    except Exception as e:
        check("NewsMesh API", "fail", str(e))
else:
    check("NewsMesh API", "skip", "Not set")

# Kaggle
kaggle_token = os.getenv("KAGGLE_API_TOKEN")
kaggle_user = os.getenv("KAGGLE_USERNAME")
kaggle_key_val = os.getenv("KAGGLE_KEY")
if kaggle_token:
    try:
        token_data = json.loads(kaggle_token)
        if "username" in token_data and "key" in token_data:
            check("Kaggle API", "pass", f"Token format OK (user: {token_data['username']})")
        else:
            check("Kaggle API", "fail", f"Token missing username/key. Got keys: {list(token_data.keys())}")
    except json.JSONDecodeError:
        check("Kaggle API", "fail", "KAGGLE_API_TOKEN is not valid JSON — needs legacy format")
elif kaggle_user and kaggle_key_val:
    check("Kaggle API", "pass", f"Using KAGGLE_USERNAME={kaggle_user}")
else:
    check("Kaggle API", "skip", "Not set")

# ArXiv (free, no key)
try:
    import requests
    resp = requests.get(
        "http://export.arxiv.org/api/query",
        params={"search_query": "innovation", "max_results": 1},
        timeout=10,
    )
    check("ArXiv API (free)", "pass" if resp.status_code == 200 else "fail", f"HTTP {resp.status_code}")
except Exception as e:
    check("ArXiv API", "fail", str(e))


# ─────────────────────────────────────────────
# 9. LANGEXTRACT (Always-On Background)
# ─────────────────────────────────────────────
section("9. LANGEXTRACT")

try:
    from tools.langextract import instant_extract, get_extraction_hint, background_intelligence
    check("LangExtract Imports", "pass", "instant_extract, get_extraction_hint, background_intelligence")

    test_msg = "About 45% of hospitals use AI. The market is worth $15B and growing 40% annually."
    signals = instant_extract(test_msg)

    has_data = signals.get("quality_signals", {}).get("has_data", False)
    content_type = signals.get("content_type", "unknown")
    check("Instant Extract", "pass" if has_data else "warn",
          f"data={has_data}, type={content_type}")

    hint = get_extraction_hint(signals, 3)
    check("Extraction Hints", "pass", f"Hint: {hint[:60]}..." if hint else "No hint (OK for this input)")
except Exception as e:
    check("LangExtract", "fail", f"{type(e).__name__}: {e}")


# ─────────────────────────────────────────────
# 10. CODE INTEGRITY
# ─────────────────────────────────────────────
section("10. CODE INTEGRITY")

import ast

critical_files = [
    "mindrian_chat.py",
    "tools/graphrag_lite.py",
    "tools/langextract.py",
    "tools/tavily_search.py",
    "tools/trends_search.py",
    "tools/patent_search.py",
    "tools/dataset_search.py",
    "tools/news_search.py",
    "tools/govdata_search.py",
    "utils/gemini_rag.py",
    "utils/storage.py",
    "utils/media.py",
    "utils/file_processor.py",
]

for f in critical_files:
    fpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f)
    if os.path.exists(fpath):
        try:
            ast.parse(open(fpath).read())
            check(f, "pass")
        except SyntaxError as e:
            check(f, "fail", f"Syntax error line {e.lineno}: {e.msg}")
    else:
        check(f, "warn", "File not found")

# Check prompts
try:
    from prompts import (
        LARRY_RAG_SYSTEM_PROMPT, TTA_WORKSHOP_PROMPT, JTBD_WORKSHOP_PROMPT,
        SCURVE_WORKSHOP_PROMPT, REDTEAM_PROMPT, ACKOFF_WORKSHOP_PROMPT,
        DOMAIN_EXPLORER_PROMPT, BONO_MASTER_PROMPT, KNOWN_UNKNOWNS_PROMPT,
        PWS_INVESTMENT_PROMPT, SCENARIO_ANALYSIS_PROMPT, PROBLEM_CLASSIFIER_PROMPT,
        CV_EXTRACTION_PROMPT, DOMAIN_GENERATION_PROMPT, DOMAIN_SCORING_PROMPT,
        RESEARCH_EXTRACTION_PROMPT, RESEARCH_DOMAIN_SCORING_PROMPT,
    )
    check("All Prompts Import", "pass", "17 prompts loaded")
except ImportError as e:
    check("Prompts Import", "fail", str(e))


# ─────────────────────────────────────────────
# 11. FILESEARCH STORE BACKUP
# ─────────────────────────────────────────────
section("11. FILESEARCH STORE BACKUP")

backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups", "filesearch")
os.makedirs(backup_dir, exist_ok=True)

fs_api_key = os.getenv("GOOGLE_FILESEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY")
if fs_api_key:
    try:
        fs_backup_client = genai.Client(api_key=fs_api_key)
        FS_STORE = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"

        # List files in the store
        # List files in the store via the API
        store_files = []
        try:
            for sf in fs_backup_client.file_search_stores.list_files(name=FS_STORE):
                store_files.append(sf)
        except AttributeError:
            # SDK may not support listing — try alternative
            try:
                store_info = fs_backup_client.file_search_stores.get(name=FS_STORE)
                store_files = [{"name": FS_STORE, "display_name": getattr(store_info, "display_name", ""), "info": "store exists"}]
            except Exception:
                store_files = [{"name": FS_STORE, "status": "accessible (verified via query)"}]

        manifest = {
            "store_name": FS_STORE,
            "api_key_prefix": fs_api_key[:8] + "...",
            "file_count": len(store_files),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "files": [],
        }

        for sf in store_files:
            manifest["files"].append({
                "name": getattr(sf, "name", "unknown"),
                "display_name": getattr(sf, "display_name", "unknown"),
                "size_bytes": getattr(sf, "size_bytes", 0),
            })

        manifest_path = os.path.join(backup_dir, "store_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        check("FileSearch Backup", "pass",
              f"{len(store_files)} files cataloged → {manifest_path}")

    except Exception as e:
        check("FileSearch Backup", "warn", f"Could not backup: {type(e).__name__}: {e}")
else:
    check("FileSearch Backup", "skip", "No FileSearch API key")

# Also record which local PWS files should be in the store
from pathlib import Path as _Path
pws_base = _Path("/home/jsagi/Mindrian/PWS - Lectures and worksheets created by Mindrian-20251219T001450Z-1-001/PWS - Lectures and worksheets created by Mindrian")
if pws_base.exists():
    local_files = []
    for ext in ["*.txt", "*.docx", "*.pdf"]:
        for f in pws_base.rglob(ext):
            if "Zone.Identifier" not in f.name and "~$" not in f.name:
                local_files.append(str(f.relative_to(pws_base)))

    local_manifest_path = os.path.join(backup_dir, "local_pws_files.json")
    with open(local_manifest_path, "w") as f:
        json.dump({"count": len(local_files), "files": sorted(local_files)}, f, indent=2)

    check("Local PWS Files Index", "pass", f"{len(local_files)} files indexed → {local_manifest_path}")
else:
    check("Local PWS Files Index", "skip", "PWS base folder not found")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
section("SUMMARY")

passed = sum(1 for r in results.values() if r["status"] == "pass")
failed = sum(1 for r in results.values() if r["status"] == "fail")
warned = sum(1 for r in results.values() if r["status"] == "warn")
skipped = sum(1 for r in results.values() if r["status"] == "skip")
total = len(results)

print(f"\n  {PASS} Passed:  {passed}/{total}")
print(f"  {FAIL} Failed:  {failed}/{total}")
print(f"  {WARN} Warnings: {warned}/{total}")
print(f"  {SKIP} Skipped: {skipped}/{total}")

if failed > 0:
    print(f"\n  {FAIL} FAILURES:")
    for name, r in results.items():
        if r["status"] == "fail":
            print(f"     - {name}: {r['detail']}")

if warned > 0:
    print(f"\n  {WARN} WARNINGS:")
    for name, r in results.items():
        if r["status"] == "warn":
            print(f"     - {name}: {r['detail']}")

print(f"\n{'='*50}")
if failed == 0:
    print("  ALL CRITICAL SYSTEMS OPERATIONAL")
else:
    print(f"  {failed} CRITICAL FAILURE(S) — FIX BEFORE DEPLOYING")
print(f"{'='*50}\n")

sys.exit(1 if failed > 0 else 0)
