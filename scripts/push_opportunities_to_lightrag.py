#!/usr/bin/env python3
"""
Push Opportunities to LightRAG Bank of Opportunities
=====================================================

Creates a LightRAG-native Bank of Opportunities by formatting opportunities
as rich documents that LightRAG can process, extract entities from, and
build into its knowledge graph.

Unlike Neo4j (manual entity/relationship creation), LightRAG:
1. Ingests text documents via /documents/text
2. Uses LLM to extract entities and relationships
3. Builds a semantic knowledge graph automatically
4. Enables hybrid RAG queries (local/global/hybrid modes)

Usage:
  python scripts/push_opportunities_to_lightrag.py
  python scripts/push_opportunities_to_lightrag.py --dry-run
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === Configuration ===
LIGHTRAG_URL = os.getenv("LIGHTRAG_URL", "https://mondrian-ts.onrender.com")
LIGHTRAG_USERNAME = os.getenv("LIGHTRAG_USERNAME", "jsagir")
LIGHTRAG_PASSWORD = os.getenv("LIGHTRAG_PASSWORD", "12345678")
OPPORTUNITIES_FILE = Path(__file__).parent.parent / "qa" / "extracted_opportunities.json"


# === LightRAG Session ===
_token = None
_session = None


def get_lightrag_session():
    """Get authenticated LightRAG session."""
    global _token, _session

    if _session is None:
        _session = requests.Session()

    if _token is None:
        print("Logging into LightRAG...")
        try:
            resp = requests.post(
                f"{LIGHTRAG_URL}/login",
                data={"username": LIGHTRAG_USERNAME, "password": LIGHTRAG_PASSWORD},
                timeout=30
            )
            if resp.status_code == 200:
                _token = resp.json().get("access_token")
                _session.headers.update({
                    "Authorization": f"Bearer {_token}",
                    "Content-Type": "application/json"
                })
                print(f"  Logged in to {LIGHTRAG_URL}")
            else:
                print(f"  Login failed: {resp.status_code} - {resp.text[:100]}")
                return None
        except Exception as e:
            print(f"  Login error: {e}")
            return None

    return _session


def format_opportunity_document(opp: dict) -> str:
    """
    Format an opportunity as a rich text document for LightRAG ingestion.

    LightRAG will extract entities and relationships from this text:
    - OPPORTUNITY entity from the title and description
    - PROBLEM entity from the problem statement
    - DOMAIN entity from the domain field
    - TARGET_USER entities from target users
    - SOLUTION_DIRECTION as potential solution hints
    - REVERSE_SALIENT if high/transformative value (bottleneck enabling innovation)

    The structured format helps LightRAG's LLM extraction understand relationships.
    """
    name = opp.get("name", "Untitled")
    description = opp.get("description", "")
    problem = opp.get("problem", "")
    value = opp.get("value_potential", "medium")
    domain = opp.get("domain", "")
    target_users = opp.get("target_users", [])
    solution = opp.get("solution_direction", "")
    evidence = opp.get("source_evidence", "")
    tags = opp.get("tags", [])

    # Build rich document that LightRAG can parse
    doc_parts = [
        f"# OPPORTUNITY: {name}",
        "",
        f"**Value Potential**: {value.upper()}",
        f"**Domain**: {domain}",
        "",
        "## Description",
        description,
        "",
    ]

    if problem:
        doc_parts.extend([
            "## Problem Statement",
            f"This opportunity ADDRESSES the following PROBLEM: {problem}",
            "",
        ])

    if target_users:
        doc_parts.extend([
            "## Target Users",
            f"This opportunity BENEFITS the following USER TYPES: {', '.join(target_users)}",
            "",
        ])

    if solution:
        doc_parts.extend([
            "## Solution Direction",
            solution,
            "",
        ])

    # For high-value opportunities, add reverse salient framing
    if value in ["high", "transformative"] and problem:
        doc_parts.extend([
            "## Reverse Salient (Innovation Bottleneck)",
            f"The REVERSE SALIENT '{problem}' represents a critical bottleneck that ENABLES breakthrough innovation. ",
            f"Solving this gap would unlock significant value in the {domain} domain.",
            "",
        ])

    if evidence:
        doc_parts.extend([
            "## Source Evidence",
            f"From Lawrence QA sessions: {evidence}",
            "",
        ])

    if tags:
        doc_parts.extend([
            "## Tags",
            f"Topics: {', '.join(tags)}",
            "",
        ])

    # Add PWS methodology context
    doc_parts.extend([
        "---",
        "This opportunity was identified using PWS (Problems Worth Solving) methodology.",
        f"It is categorized as a {value} value opportunity in the {domain} domain.",
        "The Bank of Opportunities tracks innovation opportunities across Mindrian.",
    ])

    return "\n".join(doc_parts)


def push_opportunity(opp: dict, dry_run: bool = False) -> dict:
    """Push a single opportunity document to LightRAG."""
    result = {"success": False, "track_id": None}

    name = opp.get("name", "Untitled")
    document = format_opportunity_document(opp)

    if dry_run:
        print(f"    [DRY RUN] Would push document ({len(document)} chars)")
        print(f"    --- Preview ---")
        print(document[:500] + "..." if len(document) > 500 else document)
        print(f"    --- End Preview ---")
        return {"success": True, "dry_run": True}

    session = get_lightrag_session()
    if not session:
        return result

    try:
        resp = session.post(
            f"{LIGHTRAG_URL}/documents/text",
            json={
                "text": document,
                "description": f"Bank of Opportunities: {name}"
            },
            timeout=30
        )

        if resp.status_code == 200:
            data = resp.json()
            result["success"] = True
            result["track_id"] = data.get("track_id", "")
            return result
        else:
            print(f"    Push failed: {resp.status_code} - {resp.text[:100]}")
            return result

    except Exception as e:
        print(f"    Push error: {e}")
        return result


def main(dry_run: bool = False):
    print("=" * 70)
    print("Building LightRAG Bank of Opportunities")
    print("=" * 70)
    print(f"LightRAG URL: {LIGHTRAG_URL}")
    print(f"Opportunities file: {OPPORTUNITIES_FILE}")
    print(f"Dry run: {dry_run}")
    print()
    print("This script ingests opportunities as rich documents into LightRAG.")
    print("LightRAG will automatically:")
    print("  1. Extract entities (Opportunity, Problem, Domain, User Types)")
    print("  2. Build relationships (ADDRESSES, BENEFITS, IN_DOMAIN)")
    print("  3. Create embeddings for hybrid RAG queries")
    print("  4. Enable local/global/hybrid search across opportunities")
    print()

    # Load opportunities
    if not OPPORTUNITIES_FILE.exists():
        print(f"Opportunities file not found: {OPPORTUNITIES_FILE}")
        return

    with open(OPPORTUNITIES_FILE) as f:
        opportunities = json.load(f)

    print(f"Loaded {len(opportunities)} opportunities\n")

    # Test connection first
    if not dry_run:
        session = get_lightrag_session()
        if not session:
            print("Cannot connect to LightRAG")
            return
        print()

    # Push each opportunity
    stats = {"success": 0, "failed": 0, "track_ids": []}

    for i, opp in enumerate(opportunities, 1):
        name = opp.get("name", "Untitled")
        domain = opp.get("domain", "N/A")
        value = opp.get("value_potential", "medium")

        print(f"\n[{i}/{len(opportunities)}] {name}")
        print(f"    Domain: {domain} | Value: {value}")

        result = push_opportunity(opp, dry_run=dry_run)

        if result.get("success"):
            stats["success"] += 1
            if result.get("track_id"):
                stats["track_ids"].append(result["track_id"])
            print(f"    Pushed (track: {result.get('track_id', 'N/A')[:20]}...)")
        else:
            stats["failed"] += 1
            print(f"    Failed")

        # Rate limit - LightRAG processes in background
        if not dry_run:
            time.sleep(1.5)  # Give time for background processing

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Documents pushed: {stats['success']}/{len(opportunities)}")

    if stats["failed"] > 0:
        print(f"Failed: {stats['failed']}")

    if stats["track_ids"]:
        print(f"\nTrack IDs for monitoring:")
        for tid in stats["track_ids"][:5]:
            print(f"  - {tid}")
        if len(stats["track_ids"]) > 5:
            print(f"  ... and {len(stats['track_ids']) - 5} more")

    print("\n" + "=" * 70)
    print("LightRAG Bank of Opportunities")
    print("=" * 70)
    print(f"\nQuery the Bank at: {LIGHTRAG_URL}/webui/#/")
    print("\nExample queries:")
    print('  - "What high-value opportunities exist in the AI domain?"')
    print('  - "Find opportunities that address user experience problems"')
    print('  - "What reverse salients enable innovation?"')
    print('  - "Show opportunities for improving multi-agent systems"')
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build LightRAG Bank of Opportunities")
    parser.add_argument("--dry-run", action="store_true", help="Preview documents without pushing")

    args = parser.parse_args()
    main(dry_run=args.dry_run)
