#!/usr/bin/env python3
"""
Embed All Opportunities
=======================

Generates embeddings for all opportunities in the Supabase opportunity_bank table
that don't have embeddings yet.

Usage:
    python scripts/embed_all_opportunities.py
    python scripts/embed_all_opportunities.py --force  # Re-embed all
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")


async def main(force_all: bool = False):
    """Embed all opportunities that need embeddings."""
    from tools.opportunity_bank import (
        get_supabase_client,
        generate_embedding,
        get_embedding_cache_stats,
    )

    client = get_supabase_client()
    if not client:
        print("❌ Supabase client not available")
        return

    # Get opportunities that need embeddings
    try:
        if force_all:
            print("🔄 Force mode: Re-embedding ALL opportunities...")
            result = client.table("opportunity_bank").select("id, name, description, problem, job_to_be_done, tags").execute()
        else:
            print("🔄 Finding opportunities without embeddings...")
            result = client.table("opportunity_bank").select("id, name, description, problem, job_to_be_done, tags").is_("embedding", "null").execute()

        opportunities = result.data if result.data else []
        print(f"📊 Found {len(opportunities)} opportunities to embed")

        if not opportunities:
            print("✅ All opportunities already have embeddings!")
            return

        # Process each opportunity
        embedded = 0
        errors = 0

        for i, opp in enumerate(opportunities, 1):
            opp_id = opp.get("id")
            name = opp.get("name", "Untitled")

            # Build text for embedding
            parts = [
                name,
                opp.get("description", ""),
                opp.get("problem", ""),
                opp.get("job_to_be_done", ""),
                " ".join(opp.get("tags", []) or [])
            ]
            text = " ".join(p for p in parts if p)

            if len(text.strip()) < 20:
                print(f"  ⏭️  [{i}/{len(opportunities)}] {name[:40]}... - too short, skipping")
                continue

            try:
                # Generate embedding
                embedding = await generate_embedding(text, use_cache=False)

                if embedding:
                    # Update in Supabase
                    client.table("opportunity_bank").update({
                        "embedding": embedding,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", opp_id).execute()

                    embedded += 1
                    print(f"  ✅ [{i}/{len(opportunities)}] {name[:40]}... ({len(embedding)} dims)")
                else:
                    errors += 1
                    print(f"  ❌ [{i}/{len(opportunities)}] {name[:40]}... - embedding failed")

            except Exception as e:
                errors += 1
                print(f"  ❌ [{i}/{len(opportunities)}] {name[:40]}... - {str(e)[:50]}")

            # Small delay to avoid rate limiting
            if i % 10 == 0:
                await asyncio.sleep(1)

        print(f"\n📊 Results:")
        print(f"  ✅ Embedded: {embedded}")
        print(f"  ❌ Errors: {errors}")
        print(f"  📈 Cache stats: {get_embedding_cache_stats()}")

    except Exception as e:
        if "does not exist" in str(e):
            print("❌ opportunity_bank table not found. Run sql/opportunity_bank.sql first.")
        else:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(main(force_all=force))
