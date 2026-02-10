#!/usr/bin/env python3
"""
Background ERIC — Nightly Graph Enrichment Pipeline

Runs as a scheduled job (cron / Render scheduler) with ZERO latency impact
on live conversations. Uses Claude (Anthropic API) for smart analysis,
Tavily for web research, and writes findings to Neo4j.

Architecture:
    Claude (Anthropic) → smart planning/gap analysis (background)
    Tavily → web search for evidence
    Neo4j → write new concepts & relationships

Usage:
    # Run manually
    python scripts/background_eric.py

    # Run with specific lookback window (hours)
    python scripts/background_eric.py --hours 24

    # Dry run (analyze but don't write to Neo4j)
    python scripts/background_eric.py --dry-run

    # Cron entry (nightly at 3am UTC)
    0 3 * * * cd /home/jsagi/Mindrian/mindrian-deploy && python scripts/background_eric.py >> logs/eric_nightly.log 2>&1
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ERIC] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("background_eric")


# ---------------------------------------------------------------------------
# Step 1: Gather recent conversations from PostgreSQL
# ---------------------------------------------------------------------------

async def gather_recent_conversations(hours: int = 24) -> list:
    """Pull recent conversation messages from Chainlit's PostgreSQL store."""
    try:
        import asyncpg
        db_url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
        if not db_url:
            logger.warning("No DATABASE_URL — skipping conversation gathering")
            return []

        conn = await asyncpg.connect(db_url)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        rows = await conn.fetch("""
            SELECT s.id as thread_id, s."createdAt" as created,
                   m.content, m.type
            FROM steps m
            JOIN threads s ON m."threadId" = s.id
            WHERE s."createdAt" > $1
              AND m.type IN ('user_message', 'assistant_message')
              AND m.content IS NOT NULL
              AND LENGTH(m.content) > 20
            ORDER BY s."createdAt" DESC, m."createdAt" ASC
            LIMIT 500
        """, cutoff)

        await conn.close()

        # Group by thread
        threads = {}
        for row in rows:
            tid = str(row["thread_id"])
            if tid not in threads:
                threads[tid] = []
            threads[tid].append({
                "role": "user" if row["type"] == "user_message" else "assistant",
                "content": row["content"][:1000]  # Truncate for cost
            })

        logger.info("Gathered %d conversations (%d messages) from last %dh",
                     len(threads), len(rows), hours)
        return list(threads.values())

    except Exception as e:
        logger.error("Failed to gather conversations: %s", e)
        return []


# ---------------------------------------------------------------------------
# Step 2: Claude analyzes conversations for knowledge gaps
# ---------------------------------------------------------------------------

def analyze_gaps_with_claude(conversations: list) -> dict:
    """
    Use Claude (Anthropic API) to identify knowledge gaps and new concepts.
    This is the SMART part — Claude is better at reasoning about what's missing.
    """
    from utils.llm_router import get_claude_client

    # Build a summary of what users discussed
    summaries = []
    for i, conv in enumerate(conversations[:20]):  # Cap at 20 conversations
        user_msgs = [m["content"] for m in conv if m["role"] == "user"]
        if user_msgs:
            combined = " | ".join(user_msgs[:5])  # First 5 user messages
            summaries.append(f"Conv {i+1}: {combined[:300]}")

    if not summaries:
        return {"gaps": [], "new_concepts": [], "research_queries": []}

    conversation_digest = "\n".join(summaries)

    try:
        client = get_claude_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""You are analyzing recent user conversations from Mindrian, a PWS (Problems Worth Solving) innovation coaching platform.

RECENT CONVERSATIONS:
{conversation_digest}

Analyze these conversations and identify:

1. **Knowledge gaps**: Topics users asked about that the knowledge graph likely doesn't cover well
2. **New concepts**: Emerging themes or frameworks that should be added to the graph
3. **Research queries**: Specific web searches that would fill the gaps

Return JSON only:
{{
    "gaps": [
        {{"topic": "...", "evidence": "users asked about X but got vague answers", "priority": "high|medium|low"}}
    ],
    "new_concepts": [
        {{"name": "...", "description": "...", "related_to": ["existing concept 1", "existing concept 2"]}}
    ],
    "research_queries": [
        {{"query": "...", "purpose": "fill gap in X", "depth": "basic|advanced"}}
    ]
}}"""
            }]
        )

        result_text = response.content[0].text.strip()
        # Handle markdown code blocks
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()

        return json.loads(result_text)

    except Exception as e:
        logger.error("Claude gap analysis failed: %s", e)
        return {"gaps": [], "new_concepts": [], "research_queries": []}


# ---------------------------------------------------------------------------
# Step 3: Tavily researches the gaps
# ---------------------------------------------------------------------------

async def research_gaps(research_queries: list) -> list:
    """Use Tavily to fill knowledge gaps identified by Claude."""
    from tools.tavily_search import search_web

    results = []
    for rq in research_queries[:10]:  # Cap at 10 queries
        query = rq.get("query", "")
        depth = rq.get("depth", "basic")
        if not query:
            continue

        try:
            search_result = search_web(
                query=query,
                search_depth=depth,
                max_results=3
            )
            if search_result:
                results.append({
                    "query": query,
                    "purpose": rq.get("purpose", ""),
                    "results": search_result if isinstance(search_result, list) else [search_result]
                })
                logger.info("Researched: '%s' → %d results", query,
                           len(results[-1]["results"]))
        except Exception as e:
            logger.warning("Tavily search failed for '%s': %s", query, e)

    return results


# ---------------------------------------------------------------------------
# Step 4: Write new knowledge to Neo4j
# ---------------------------------------------------------------------------

def write_to_neo4j(new_concepts: list, research_results: list, dry_run: bool = False) -> dict:
    """Write discovered concepts and relationships to Neo4j."""
    from tools.graphrag_lite import _get_neo4j

    driver = _get_neo4j()
    if not driver:
        logger.warning("Neo4j not available — skipping writes")
        return {"written": 0, "skipped": 0}

    written = 0
    skipped = 0
    today = datetime.now().strftime("%Y-%m-%d")

    for concept in new_concepts[:50]:  # Cap at 50 new concepts
        name = concept.get("name", "").strip()
        description = concept.get("description", "").strip()
        related = concept.get("related_to", [])

        if not name or len(name) < 3:
            skipped += 1
            continue

        if dry_run:
            logger.info("[DRY RUN] Would write: %s — %s", name, description[:80])
            written += 1
            continue

        try:
            with driver.session() as session:
                # MERGE concept (no duplicates)
                session.run("""
                    MERGE (c:LazyGraphConcept {name: $name})
                    ON CREATE SET
                        c.description = $desc,
                        c.added_by = 'background-eric',
                        c.added_date = $today,
                        c.source_type = 'nightly_enrichment',
                        c.chunk_count = 1
                    ON MATCH SET
                        c.chunk_count = c.chunk_count + 1
                """, name=name.lower(), desc=description, today=today)

                # Create relationships to existing concepts
                for rel_name in related[:5]:
                    session.run("""
                        MATCH (a:LazyGraphConcept {name: $source})
                        MATCH (b:LazyGraphConcept {name: $target})
                        MERGE (a)-[r:CO_OCCURS]-(b)
                        ON CREATE SET r.weight = 1, r.added_by = 'background-eric'
                        ON MATCH SET r.weight = r.weight + 1
                    """, source=name.lower(), target=rel_name.lower())

                written += 1
                logger.info("Wrote concept: %s", name)

        except Exception as e:
            logger.warning("Failed to write '%s': %s", name, e)
            skipped += 1

    # Also write research-discovered concepts
    for research in research_results:
        for result in research.get("results", []):
            # Extract title as a lightweight concept
            title = result.get("title", "") if isinstance(result, dict) else ""
            url = result.get("url", "") if isinstance(result, dict) else ""
            if not title or len(title) < 5:
                continue

            if dry_run:
                logger.info("[DRY RUN] Would index research: %s", title[:80])
                continue

            try:
                with driver.session() as session:
                    session.run("""
                        MERGE (c:LazyGraphConcept {name: $name})
                        ON CREATE SET
                            c.description = $desc,
                            c.added_by = 'background-eric-research',
                            c.added_date = $today,
                            c.source_type = 'tavily_research',
                            c.source_url = $url,
                            c.chunk_count = 1
                    """, name=title.lower()[:100], desc=research.get("purpose", ""),
                        today=today, url=url)
            except Exception:
                pass

    return {"written": written, "skipped": skipped}


# ---------------------------------------------------------------------------
# Step 5: Write to LightRAG for vector retrieval
# ---------------------------------------------------------------------------

async def write_to_lightrag(new_concepts: list, research_results: list) -> int:
    """Optionally push findings to LightRAG for vector search."""
    try:
        import httpx
        lightrag_url = os.getenv("LIGHTRAG_URL", "https://mondrian-ts.onrender.com")

        documents = []
        for concept in new_concepts[:20]:
            name = concept.get("name", "")
            desc = concept.get("description", "")
            if name and desc:
                documents.append(f"## {name}\n\n{desc}")

        if not documents:
            return 0

        combined = "\n\n---\n\n".join(documents)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{lightrag_url}/documents/text",
                json={"text": combined, "description": "Background ERIC nightly enrichment"}
            )
            if resp.status_code == 200:
                logger.info("Pushed %d concepts to LightRAG", len(documents))
                return len(documents)
            else:
                logger.warning("LightRAG push failed: %s", resp.text[:200])
                return 0

    except Exception as e:
        logger.debug("LightRAG not available: %s", e)
        return 0


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

async def run_nightly_eric(hours: int = 24, dry_run: bool = False):
    """Full ERIC nightly pipeline: Gather → Analyze → Research → Write."""
    logger.info("=" * 60)
    logger.info("Background ERIC starting (lookback=%dh, dry_run=%s)", hours, dry_run)
    logger.info("=" * 60)

    t0 = datetime.now()

    # Step 1: Gather
    conversations = await gather_recent_conversations(hours)
    if not conversations:
        logger.info("No recent conversations found. Exiting.")
        return

    # Step 2: Analyze with Claude (smart planning)
    logger.info("Step 2: Claude analyzing %d conversations for gaps...", len(conversations))
    analysis = analyze_gaps_with_claude(conversations)

    gaps = analysis.get("gaps", [])
    new_concepts = analysis.get("new_concepts", [])
    research_queries = analysis.get("research_queries", [])

    logger.info("Found: %d gaps, %d new concepts, %d research queries",
                len(gaps), len(new_concepts), len(research_queries))

    # Step 3: Research gaps with Tavily
    research_results = []
    if research_queries:
        logger.info("Step 3: Researching %d queries with Tavily...", len(research_queries))
        research_results = await research_gaps(research_queries)

    # Step 4: Write to Neo4j
    logger.info("Step 4: Writing to Neo4j (dry_run=%s)...", dry_run)
    write_stats = write_to_neo4j(new_concepts, research_results, dry_run=dry_run)

    # Step 5: Push to LightRAG (optional)
    lightrag_count = await write_to_lightrag(new_concepts, research_results)

    elapsed = (datetime.now() - t0).total_seconds()

    # Summary
    logger.info("=" * 60)
    logger.info("Background ERIC complete in %.1fs", elapsed)
    logger.info("  Conversations analyzed: %d", len(conversations))
    logger.info("  Knowledge gaps found: %d", len(gaps))
    logger.info("  New concepts: %d", len(new_concepts))
    logger.info("  Research queries: %d", len(research_queries))
    logger.info("  Neo4j writes: %d (skipped: %d)", write_stats["written"], write_stats["skipped"])
    logger.info("  LightRAG pushes: %d", lightrag_count)
    logger.info("=" * 60)

    # Write run report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(elapsed, 1),
        "conversations_analyzed": len(conversations),
        "gaps_found": len(gaps),
        "gaps": gaps,
        "new_concepts_found": len(new_concepts),
        "research_queries": len(research_queries),
        "neo4j_written": write_stats["written"],
        "neo4j_skipped": write_stats["skipped"],
        "lightrag_pushed": lightrag_count,
        "dry_run": dry_run,
    }

    report_dir = PROJECT_ROOT / "logs"
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / f"eric_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("Report saved: %s", report_path)

    return report


def main():
    parser = argparse.ArgumentParser(description="Background ERIC — Nightly Graph Enrichment")
    parser.add_argument("--hours", type=int, default=24, help="Lookback window in hours (default: 24)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze but don't write to Neo4j")
    args = parser.parse_args()

    asyncio.run(run_nightly_eric(hours=args.hours, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
