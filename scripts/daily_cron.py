#!/usr/bin/env python3
"""
Daily Cron Job for Mindrian
===========================

Run daily tasks:
1. API Health Check (with Supabase logging)
2. Opportunity Digest Email
3. Cleanup stale data

Usage:
    # Run everything
    python scripts/daily_cron.py

    # Run specific tasks
    python scripts/daily_cron.py --health-only
    python scripts/daily_cron.py --digest-only
    python scripts/daily_cron.py --email user@example.com

Configure via environment:
    DIGEST_RECIPIENTS=email1@example.com,email2@example.com
    CRON_SECRET=your-secret-for-webhook
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

DIGEST_RECIPIENTS = os.getenv("DIGEST_RECIPIENTS", "").split(",")
DIGEST_RECIPIENTS = [e.strip() for e in DIGEST_RECIPIENTS if e.strip()]

# =============================================================================
# HEALTH CHECK TASK
# =============================================================================

async def run_health_check() -> dict:
    """Run comprehensive health check and log to Supabase."""
    print("\n" + "=" * 50)
    print("🏥 Running API Health Check")
    print("=" * 50)

    try:
        from utils.api_health_monitor import (
            run_startup_health_check,
            HealthStatus
        )

        results = await run_startup_health_check(
            sample_count=5,
            include_critical=True,
            log_to_supabase=True
        )

        # Summary
        healthy = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
        degraded = sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY)

        print(f"\n✅ Healthy: {healthy}")
        print(f"⚠️ Degraded: {degraded}")
        print(f"❌ Unhealthy: {unhealthy}")

        for api, result in results.items():
            icon = "✅" if result.status == HealthStatus.HEALTHY else "⚠️" if result.status == HealthStatus.DEGRADED else "❌"
            print(f"  {icon} {api}: {result.message} ({result.response_time_ms}ms)")

        return {
            "success": True,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "details": {k: v.to_dict() for k, v in results.items()}
        }

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# DIGEST EMAIL TASK
# =============================================================================

async def send_digest(recipients: list = None) -> dict:
    """Generate and send opportunity digest."""
    print("\n" + "=" * 50)
    print("📧 Sending Opportunity Digest")
    print("=" * 50)

    recipients = recipients or DIGEST_RECIPIENTS

    if not recipients:
        print("⚠️ No recipients configured. Set DIGEST_RECIPIENTS env var.")
        return {"success": False, "error": "No recipients"}

    try:
        from utils.opportunity_digest import send_opportunity_digest

        results = []
        for email in recipients:
            print(f"  Sending to: {email}")
            success = await send_opportunity_digest(to_email=email)
            results.append({"email": email, "success": success})
            if success:
                print(f"    ✅ Sent")
            else:
                print(f"    ❌ Failed")

        successful = sum(1 for r in results if r["success"])
        print(f"\n📊 Sent {successful}/{len(recipients)} emails")

        return {
            "success": successful > 0,
            "sent": successful,
            "total": len(recipients),
            "results": results
        }

    except Exception as e:
        print(f"❌ Digest failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# =============================================================================
# CLEANUP TASK
# =============================================================================

async def run_cleanup() -> dict:
    """Clean up stale data."""
    print("\n" + "=" * 50)
    print("🧹 Running Cleanup")
    print("=" * 50)

    try:
        # Clean old health logs (keep 30 days)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        if url and key:
            from supabase import create_client
            from datetime import timedelta

            client = create_client(url, key)

            # Delete health logs older than 30 days
            cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()

            try:
                result = client.table("api_health_log")\
                    .delete()\
                    .lt("created_at", cutoff)\
                    .execute()

                deleted = len(result.data) if result.data else 0
                print(f"  ✅ Deleted {deleted} old health log entries")

            except Exception as e:
                print(f"  ⚠️ Health log cleanup: {e}")

        print("✅ Cleanup complete")
        return {"success": True}

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# MAIN
# =============================================================================

async def main(args):
    """Run daily cron tasks."""
    print("=" * 50)
    print(f"🕐 Mindrian Daily Cron - {datetime.utcnow().isoformat()}")
    print("=" * 50)

    results = {}

    # Health check
    if not args.digest_only:
        results["health_check"] = await run_health_check()

    # Digest email
    if not args.health_only:
        recipients = [args.email] if args.email else None
        results["digest"] = await send_digest(recipients)

    # Cleanup (always run unless specific task requested)
    if not args.health_only and not args.digest_only:
        results["cleanup"] = await run_cleanup()

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)

    all_success = True
    for task, result in results.items():
        status = "✅" if result.get("success") else "❌"
        print(f"  {status} {task}")
        if not result.get("success"):
            all_success = False

    print("\n" + ("✅ All tasks completed" if all_success else "⚠️ Some tasks failed"))

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mindrian Daily Cron")
    parser.add_argument("--health-only", action="store_true", help="Run health check only")
    parser.add_argument("--digest-only", action="store_true", help="Run digest only")
    parser.add_argument("--email", type=str, help="Send digest to specific email")

    args = parser.parse_args()

    asyncio.run(main(args))
