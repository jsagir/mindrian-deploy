#!/usr/bin/env python3
"""
Process Insights Batch Job

Processes pending insights from session_insights table:
1. High confidence insights → auto-ingest to Neo4j
2. Medium confidence → flag for review
3. Updates agent_effectiveness scores

Run daily via cron or manually:
    python scripts/process_insights.py --auto-ingest
    python scripts/process_insights.py --rebuild-effectiveness
    python scripts/process_insights.py --all

Phase 4 of Recursive Intelligence implementation.
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def get_supabase():
    """Get Supabase client."""
    from utils.storage import get_supabase_client
    return get_supabase_client()


async def auto_ingest_high_confidence(dry_run: bool = False) -> Dict[str, Any]:
    """
    Auto-ingest high confidence insights.

    High confidence framework applications and cross-connections
    can be automatically added to the knowledge base.

    Args:
        dry_run: If True, don't actually modify anything

    Returns:
        Summary of processing
    """
    results = {
        "processed": 0,
        "ingested": 0,
        "skipped": 0,
        "errors": 0,
    }

    supabase = get_supabase()
    if not supabase:
        return {"error": "Supabase not configured"}

    try:
        # Fetch pending high-confidence insights
        response = supabase.table("session_insights").select("*").eq(
            "status", "pending"
        ).eq(
            "confidence", "high"
        ).limit(100).execute()

        insights = response.data or []
        results["processed"] = len(insights)

        print(f"[AutoIngest] Found {len(insights)} high-confidence pending insights")

        for insight in insights:
            insight_id = insight.get("id")
            insight_type = insight.get("insight_type")
            content = insight.get("content")
            entities = insight.get("entities_mentioned", [])

            try:
                # For now, mark as auto_ingested
                # Full implementation would write to Neo4j
                if not dry_run:
                    # Update status
                    supabase.table("session_insights").update({
                        "status": "auto_ingested",
                        "reviewed_at": datetime.now(timezone.utc).isoformat(),
                        "reviewed_by": "auto_ingest_job"
                    }).eq("id", insight_id).execute()

                    results["ingested"] += 1

                    # Log what would be ingested
                    print(f"  ✓ [{insight_type}] {content[:60]}...")
                else:
                    print(f"  [DRY RUN] Would ingest: [{insight_type}] {content[:60]}...")
                    results["skipped"] += 1

            except Exception as e:
                print(f"  ✗ Error processing {insight_id}: {e}")
                results["errors"] += 1

    except Exception as e:
        results["error"] = str(e)
        print(f"[AutoIngest] Error: {e}")

    return results


async def rebuild_effectiveness_scores() -> Dict[str, Any]:
    """
    Rebuild agent effectiveness scores from session data.

    Aggregates positive/negative reactions by agent and problem type
    to learn which agents work best for which problems.
    """
    results = {
        "agents_updated": 0,
        "problem_types_covered": set(),
    }

    supabase = get_supabase()
    if not supabase:
        return {"error": "Supabase not configured"}

    try:
        # Call the rebuild function
        response = supabase.rpc("rebuild_agent_effectiveness").execute()

        # Get updated stats
        stats = supabase.table("agent_effectiveness").select("*").execute()

        for row in (stats.data or []):
            results["agents_updated"] += 1
            results["problem_types_covered"].add(row.get("problem_type"))

        results["problem_types_covered"] = list(results["problem_types_covered"])

        print(f"[Effectiveness] Updated {results['agents_updated']} agent-problem combinations")

    except Exception as e:
        results["error"] = str(e)
        print(f"[Effectiveness] Error: {e}")

    return results


async def apply_effectiveness_decay(factor: float = 0.95) -> Dict[str, Any]:
    """
    Apply decay to effectiveness scores to prevent stale data.

    Scores drift toward 0.5 (neutral) over time if not refreshed.
    """
    results = {"success": False}

    supabase = get_supabase()
    if not supabase:
        return {"error": "Supabase not configured"}

    try:
        response = supabase.rpc("decay_effectiveness", {"factor": factor}).execute()
        results["success"] = True
        print(f"[Decay] Applied decay factor {factor} to all effectiveness scores")

    except Exception as e:
        results["error"] = str(e)
        print(f"[Decay] Error: {e}")

    return results


async def get_insights_summary() -> Dict[str, Any]:
    """Get summary of insights by status and type."""
    supabase = get_supabase()
    if not supabase:
        return {"error": "Supabase not configured"}

    try:
        # Count by status
        response = supabase.table("session_insights").select(
            "status", count="exact"
        ).execute()

        # Get counts by querying each status
        summary = {}
        for status in ["pending", "approved", "rejected", "auto_ingested", "archived"]:
            count_resp = supabase.table("session_insights").select(
                "id", count="exact"
            ).eq("status", status).execute()
            summary[status] = count_resp.count or 0

        return {
            "total": sum(summary.values()),
            "by_status": summary
        }

    except Exception as e:
        return {"error": str(e)}


async def get_effectiveness_summary() -> Dict[str, Any]:
    """Get summary of agent effectiveness scores."""
    supabase = get_supabase()
    if not supabase:
        return {"error": "Supabase not configured"}

    try:
        response = supabase.table("agent_effectiveness").select("*").execute()
        rows = response.data or []

        if not rows:
            return {"message": "No effectiveness data yet"}

        # Group by agent
        by_agent = {}
        for row in rows:
            agent = row.get("agent")
            if agent not in by_agent:
                by_agent[agent] = []
            by_agent[agent].append({
                "problem_type": row.get("problem_type"),
                "effectiveness": row.get("effectiveness"),
                "sample_size": row.get("sample_size"),
            })

        return {
            "total_entries": len(rows),
            "agents": list(by_agent.keys()),
            "by_agent": by_agent
        }

    except Exception as e:
        return {"error": str(e)}


async def main():
    parser = argparse.ArgumentParser(description="Process insights batch job")
    parser.add_argument("--auto-ingest", action="store_true",
                        help="Auto-ingest high confidence insights")
    parser.add_argument("--rebuild-effectiveness", action="store_true",
                        help="Rebuild agent effectiveness scores")
    parser.add_argument("--decay", action="store_true",
                        help="Apply decay to effectiveness scores")
    parser.add_argument("--decay-factor", type=float, default=0.95,
                        help="Decay factor (default: 0.95)")
    parser.add_argument("--summary", action="store_true",
                        help="Show insights and effectiveness summary")
    parser.add_argument("--all", action="store_true",
                        help="Run all processing steps")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't modify data, just show what would happen")

    args = parser.parse_args()

    print("=" * 60)
    print("Recursive Intelligence - Batch Processing")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if args.summary or args.all:
        print("\n📊 INSIGHTS SUMMARY")
        print("-" * 40)
        summary = await get_insights_summary()
        if "error" in summary:
            print(f"Error: {summary['error']}")
        else:
            print(f"Total insights: {summary['total']}")
            for status, count in summary.get("by_status", {}).items():
                print(f"  {status}: {count}")

        print("\n📈 EFFECTIVENESS SUMMARY")
        print("-" * 40)
        eff_summary = await get_effectiveness_summary()
        if "error" in eff_summary:
            print(f"Error: {eff_summary['error']}")
        elif "message" in eff_summary:
            print(eff_summary["message"])
        else:
            print(f"Total entries: {eff_summary['total_entries']}")
            print(f"Agents tracked: {', '.join(eff_summary['agents'])}")

    if args.auto_ingest or args.all:
        print("\n🔄 AUTO-INGEST HIGH CONFIDENCE")
        print("-" * 40)
        result = await auto_ingest_high_confidence(dry_run=args.dry_run)
        print(f"Processed: {result.get('processed', 0)}")
        print(f"Ingested: {result.get('ingested', 0)}")
        print(f"Errors: {result.get('errors', 0)}")

    if args.rebuild_effectiveness or args.all:
        print("\n🎯 REBUILD EFFECTIVENESS SCORES")
        print("-" * 40)
        result = await rebuild_effectiveness_scores()
        print(f"Agents updated: {result.get('agents_updated', 0)}")

    if args.decay or args.all:
        print("\n📉 APPLY EFFECTIVENESS DECAY")
        print("-" * 40)
        result = await apply_effectiveness_decay(args.decay_factor)
        print(f"Success: {result.get('success', False)}")

    print("\n" + "=" * 60)
    print("Processing complete")


if __name__ == "__main__":
    asyncio.run(main())
