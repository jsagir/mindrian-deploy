#!/usr/bin/env python3
"""
Populate LightRAG with Opportunities from Lawrence QA Sessions
==============================================================

Extracts opportunities, problems, and improvement ideas from QA reports
and pushes them to LightRAG for the Bank of Opportunities.

This populates the graph with real-world opportunities discovered during
Lawrence Aronhime's testing sessions.

Usage:
  python scripts/populate_lightrag_from_qa.py
  python scripts/populate_lightrag_from_qa.py --dry-run  # Preview without pushing
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === Configuration ===
QA_DIR = Path(__file__).parent.parent / "qa"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# === Extraction Prompt ===
OPPORTUNITY_EXTRACTION_PROMPT = """Analyze this QA report and extract innovation opportunities using PWS (Problems Worth Solving) methodology.

For each opportunity, identify:
1. The problem or improvement need
2. Who it affects (users, developers, etc.)
3. The potential value (low/medium/high/transformative)
4. The domain (UX, AI/ML, Research, Infrastructure, Methodology, etc.)
5. A suggested solution direction

QA REPORT:
{content}

Return JSON array:
[
  {{
    "name": "Clear opportunity title (max 60 chars)",
    "description": "2-3 sentence description of the opportunity",
    "problem": "The core constraint or pain point",
    "value_potential": "low|medium|high|transformative",
    "domain": "UX|Research|AI|Infrastructure|Methodology|Integration",
    "target_users": ["User type 1", "User type 2"],
    "solution_direction": "Brief approach to solving",
    "source_evidence": "Key quote or finding from the report",
    "tags": ["tag1", "tag2", "tag3"]
  }}
]

Rules:
- Extract 3-10 opportunities per report
- Focus on actionable improvements, not just bugs
- Include both user-facing and technical opportunities
- Value potential should reflect impact on Mindrian's success
- Return empty array if no clear opportunities found
"""


async def extract_opportunities_from_file(file_path: Path, dry_run: bool = False) -> list:
    """Extract opportunities from a single QA file using Gemini."""
    if not GOOGLE_API_KEY:
        print(f"  ⚠️ GOOGLE_API_KEY not set, skipping extraction")
        return []

    try:
        content = file_path.read_text(encoding='utf-8')

        # Skip very short files
        if len(content) < 200:
            print(f"  ⏭️ Skipping {file_path.name} (too short)")
            return []

        from google import genai

        client = genai.Client(api_key=GOOGLE_API_KEY)
        prompt = OPPORTUNITY_EXTRACTION_PROMPT.format(content=content[:8000])

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
            }
        )

        opportunities = json.loads(response.text)
        print(f"  ✅ Extracted {len(opportunities)} opportunities from {file_path.name}")
        return opportunities

    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSON parse error for {file_path.name}: {e}")
        return []
    except Exception as e:
        print(f"  ⚠️ Extraction error for {file_path.name}: {e}")
        return []


async def push_to_lightrag(opportunities: list, source_file: str, dry_run: bool = False) -> dict:
    """Push opportunities to LightRAG graph."""
    if dry_run:
        print(f"  [DRY RUN] Would push {len(opportunities)} opportunities")
        return {"pushed": 0, "dry_run": True}

    try:
        from tools.opportunity_bank_lightrag import (
            push_opportunity_to_lightrag,
            _get_lightrag_session,
        )
        from tools.opportunity_bank import Opportunity, generate_opportunity_id

        # Verify LightRAG connection
        session = _get_lightrag_session()
        if not session:
            print(f"  ⚠️ LightRAG not available")
            return {"pushed": 0, "error": "LightRAG unavailable"}

        pushed = 0
        for opp_data in opportunities:
            try:
                # Create Opportunity object
                opp = Opportunity(
                    id=generate_opportunity_id(opp_data.get("name", ""), source_file),
                    name=opp_data.get("name", "Untitled"),
                    description=opp_data.get("description", ""),
                    problem=opp_data.get("problem", ""),
                    value_potential=opp_data.get("value_potential", "medium"),
                    domain=opp_data.get("domain", ""),
                    target_users=opp_data.get("target_users", []),
                    solution_direction=opp_data.get("solution_direction", ""),
                    source_type="qa_report",
                    source_name=source_file,
                    source_snippet=opp_data.get("source_evidence", ""),
                    tags=opp_data.get("tags", []),
                    created_by="qa_extraction",
                    created_by_type="system",
                )

                # Push to LightRAG
                success = push_opportunity_to_lightrag(opp)
                if success:
                    pushed += 1
                    print(f"    ✅ Pushed: {opp.name[:50]}")

            except Exception as e:
                print(f"    ⚠️ Push error for {opp_data.get('name', 'unknown')}: {e}")

        return {"pushed": pushed, "total": len(opportunities)}

    except ImportError as e:
        print(f"  ⚠️ Import error: {e}")
        return {"pushed": 0, "error": str(e)}


async def push_to_neo4j(opportunities: list, source_file: str, dry_run: bool = False) -> dict:
    """Also store opportunities in Neo4j for local graph queries."""
    if dry_run:
        return {"stored": 0, "dry_run": True}

    try:
        from tools.opportunity_bank import Opportunity, generate_opportunity_id, store_opportunity

        stored = 0
        for opp_data in opportunities:
            try:
                opp = Opportunity(
                    id=generate_opportunity_id(opp_data.get("name", ""), source_file),
                    name=opp_data.get("name", "Untitled"),
                    description=opp_data.get("description", ""),
                    problem=opp_data.get("problem", ""),
                    value_potential=opp_data.get("value_potential", "medium"),
                    domain=opp_data.get("domain", ""),
                    target_users=opp_data.get("target_users", []),
                    solution_direction=opp_data.get("solution_direction", ""),
                    source_type="qa_report",
                    source_name=source_file,
                    source_snippet=opp_data.get("source_evidence", ""),
                    tags=opp_data.get("tags", []),
                    created_by="qa_extraction",
                    created_by_type="system",
                )

                result = await store_opportunity(opp, generate_embedding=False)
                if result.get("neo4j") or result.get("supabase_table"):
                    stored += 1

            except Exception as e:
                print(f"    ⚠️ Neo4j store error: {e}")

        return {"stored": stored, "total": len(opportunities)}

    except ImportError as e:
        return {"stored": 0, "error": str(e)}


async def main(dry_run: bool = False):
    print("=" * 70)
    print("Populating LightRAG Bank of Opportunities from Lawrence QA Sessions")
    print("=" * 70)
    print(f"QA Directory: {QA_DIR}")
    print(f"Dry Run: {dry_run}")
    print()

    # Find all QA files
    qa_files = []
    for ext in ["*.md", "*.txt"]:
        qa_files.extend(QA_DIR.glob(f"**/{ext}"))

    print(f"Found {len(qa_files)} QA files\n")

    all_opportunities = []
    stats = {
        "files_processed": 0,
        "opportunities_extracted": 0,
        "opportunities_pushed": 0,
        "opportunities_stored": 0,
    }

    for file_path in sorted(qa_files):
        relative_path = file_path.relative_to(QA_DIR)
        print(f"\n[{relative_path}]")

        # Extract opportunities
        opportunities = await extract_opportunities_from_file(file_path, dry_run)
        stats["files_processed"] += 1
        stats["opportunities_extracted"] += len(opportunities)

        if not opportunities:
            continue

        all_opportunities.extend(opportunities)

        # Push to LightRAG
        lightrag_result = await push_to_lightrag(opportunities, str(relative_path), dry_run)
        stats["opportunities_pushed"] += lightrag_result.get("pushed", 0)

        # Also store in Neo4j
        neo4j_result = await push_to_neo4j(opportunities, str(relative_path), dry_run)
        stats["opportunities_stored"] += neo4j_result.get("stored", 0)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed:        {stats['files_processed']}")
    print(f"Opportunities extracted: {stats['opportunities_extracted']}")
    print(f"Pushed to LightRAG:     {stats['opportunities_pushed']}")
    print(f"Stored in Neo4j:        {stats['opportunities_stored']}")

    # Save extracted opportunities for reference
    if all_opportunities:
        output_file = QA_DIR / "extracted_opportunities.json"
        with open(output_file, 'w') as f:
            json.dump(all_opportunities, f, indent=2)
        print(f"\nSaved to: {output_file}")

    # Show sample opportunities
    if all_opportunities and len(all_opportunities) <= 20:
        print("\n" + "-" * 70)
        print("EXTRACTED OPPORTUNITIES")
        print("-" * 70)
        for i, opp in enumerate(all_opportunities, 1):
            print(f"\n{i}. {opp.get('name', 'Untitled')}")
            print(f"   Domain: {opp.get('domain', 'N/A')}")
            print(f"   Value: {opp.get('value_potential', 'N/A')}")
            print(f"   Problem: {opp.get('problem', 'N/A')[:80]}...")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate LightRAG from QA reports")
    parser.add_argument("--dry-run", action="store_true", help="Preview without pushing")

    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
