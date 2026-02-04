#!/usr/bin/env python3
"""
Push Pre-Extracted QA Opportunities to LightRAG
================================================

Pushes the opportunities extracted from Lawrence QA sessions to LightRAG.
No Gemini API required - uses the pre-extracted JSON file.

Usage:
  python scripts/push_qa_opportunities_to_lightrag.py
  python scripts/push_qa_opportunities_to_lightrag.py --dry-run
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
                _session.headers.update({"Authorization": f"Bearer {_token}"})
                print(f"  ✅ Logged in to {LIGHTRAG_URL}")
            else:
                print(f"  ❌ Login failed: {resp.status_code} - {resp.text[:100]}")
                return None
        except Exception as e:
            print(f"  ❌ Login error: {e}")
            return None

    return _session


def create_entity(name: str, entity_type: str, description: str, properties: dict = None, dry_run: bool = False) -> bool:
    """Create entity in LightRAG graph."""
    if dry_run:
        print(f"    [DRY RUN] Would create entity: {name} ({entity_type})")
        return True

    session = get_lightrag_session()
    if not session:
        return False

    try:
        entity_data = {
            "entity_type": entity_type,
            "description": description[:500] if description else "",
        }
        if properties:
            entity_data.update(properties)

        resp = session.post(
            f"{LIGHTRAG_URL}/graph/entity/create",
            json={"entity_name": name, "entity_data": entity_data},
            timeout=15
        )

        if resp.status_code in [200, 409]:  # 200=created, 409=already exists
            return True
        else:
            print(f"    ⚠️ Entity '{name}': {resp.status_code}")
            return False

    except Exception as e:
        print(f"    ⚠️ Entity error: {e}")
        return False


def create_relation(source: str, target: str, description: str, keywords: str = "", dry_run: bool = False) -> bool:
    """Create relationship in LightRAG graph."""
    if dry_run:
        print(f"    [DRY RUN] Would create relation: {source} -> {target}")
        return True

    session = get_lightrag_session()
    if not session:
        return False

    try:
        resp = session.post(
            f"{LIGHTRAG_URL}/graph/relation/create",
            json={
                "source_entity": source,
                "target_entity": target,
                "relation_data": {
                    "description": description,
                    "keywords": keywords,
                    "weight": 1.0,
                }
            },
            timeout=10
        )

        return resp.status_code in [200, 409]

    except Exception as e:
        print(f"    ⚠️ Relation error: {e}")
        return False


def push_opportunity(opp: dict, dry_run: bool = False) -> dict:
    """Push a single opportunity to LightRAG with full PWS graph relationships.

    Mirrors Neo4j structure:
    - Opportunity -[:ADDRESSES]-> Problem
    - Opportunity -[:IN_DOMAIN]-> Domain
    - ReverseSalient -[:ENABLES]-> Opportunity
    - Opportunity -[:TAGGED_WITH]-> Tag
    - Opportunity -[:TARGETS]-> UserType
    """
    result = {"entity": False, "domain": False, "problem": False, "reverse_salient": False, "tags": 0}

    name = opp.get("name", "Untitled")
    problem_text = opp.get("problem", "")

    # Create opportunity entity
    entity_ok = create_entity(
        name=name,
        entity_type="OPPORTUNITY",
        description=opp.get("description", ""),
        properties={
            "value_potential": opp.get("value_potential", "medium"),
            "solution_direction": opp.get("solution_direction", ""),
            "source_evidence": opp.get("source_evidence", ""),
            "source": "lawrence_qa",
        },
        dry_run=dry_run
    )
    result["entity"] = entity_ok

    if not entity_ok and not dry_run:
        return result

    time.sleep(0.3)  # Rate limit

    # Create Problem entity and ADDRESSES relationship (PWS core structure)
    if problem_text:
        problem_name = f"Problem: {problem_text[:60]}"
        create_entity(
            problem_name,
            "PROBLEM",
            problem_text,
            properties={"severity": opp.get("value_potential", "medium")},
            dry_run=dry_run
        )
        problem_ok = create_relation(name, problem_name, "ADDRESSES", "addresses, solves, problem", dry_run=dry_run)
        result["problem"] = problem_ok
        time.sleep(0.2)

    # Create domain entity and IN_DOMAIN relationship
    domain = opp.get("domain", "")
    if domain:
        create_entity(domain, "DOMAIN", f"Domain area: {domain}", dry_run=dry_run)
        domain_ok = create_relation(name, domain, "IN_DOMAIN", "domain, category, area", dry_run=dry_run)
        result["domain"] = domain_ok
        time.sleep(0.2)

    # Create ReverseSalient entity if opportunity has transformative/high value
    # ReverseSalients represent bottlenecks that enable breakthrough opportunities
    value = opp.get("value_potential", "medium")
    if value in ["high", "transformative"] and problem_text:
        rs_name = f"RS: {problem_text[:50]}"
        create_entity(
            rs_name,
            "REVERSE_SALIENT",
            f"Bottleneck/gap that enables innovation: {problem_text}",
            properties={"severity": value, "domain": domain},
            dry_run=dry_run
        )
        rs_ok = create_relation(rs_name, name, "ENABLES", "enables, unblocks, breakthrough", dry_run=dry_run)
        result["reverse_salient"] = rs_ok
        time.sleep(0.2)

    # Create tag entities and TAGGED_WITH relationships
    for tag in opp.get("tags", [])[:5]:
        create_entity(tag, "TAG", f"Topic tag: {tag}", dry_run=dry_run)
        if create_relation(name, tag, "TAGGED_WITH", "tag, topic, keyword", dry_run=dry_run):
            result["tags"] += 1
        time.sleep(0.1)

    # Create target user relationships
    for user in opp.get("target_users", [])[:3]:
        create_entity(user, "USER_TYPE", f"Target user type: {user}", dry_run=dry_run)
        create_relation(name, user, "TARGETS", "user, audience, beneficiary", dry_run=dry_run)
        time.sleep(0.1)

    return result


def main(dry_run: bool = False):
    print("=" * 70)
    print("Pushing Lawrence QA Opportunities to LightRAG")
    print("=" * 70)
    print(f"LightRAG URL: {LIGHTRAG_URL}")
    print(f"Opportunities file: {OPPORTUNITIES_FILE}")
    print(f"Dry run: {dry_run}")
    print()

    # Load opportunities
    if not OPPORTUNITIES_FILE.exists():
        print(f"❌ Opportunities file not found: {OPPORTUNITIES_FILE}")
        return

    with open(OPPORTUNITIES_FILE) as f:
        opportunities = json.load(f)

    print(f"Loaded {len(opportunities)} opportunities\n")

    # Test connection first
    if not dry_run:
        session = get_lightrag_session()
        if not session:
            print("❌ Cannot connect to LightRAG")
            return

    # Push each opportunity
    stats = {"success": 0, "failed": 0, "domains": set(), "tags": 0}

    for i, opp in enumerate(opportunities, 1):
        name = opp.get("name", "Untitled")
        domain = opp.get("domain", "N/A")
        value = opp.get("value_potential", "medium")

        print(f"\n[{i}/{len(opportunities)}] {name}")
        print(f"    Domain: {domain} | Value: {value}")

        result = push_opportunity(opp, dry_run=dry_run)

        if result["entity"]:
            stats["success"] += 1
            if domain:
                stats["domains"].add(domain)
            stats["tags"] += result["tags"]
            print(f"    ✅ Pushed (domain={result['domain']}, tags={result['tags']})")
        else:
            stats["failed"] += 1
            print(f"    ❌ Failed")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Opportunities pushed: {stats['success']}/{len(opportunities)}")
    print(f"Domains created: {len(stats['domains'])} - {sorted(stats['domains'])}")
    print(f"Tag relationships: {stats['tags']}")

    if stats["failed"] > 0:
        print(f"⚠️ Failed: {stats['failed']}")

    print("\n" + "=" * 70)
    print("Done! Query LightRAG at:")
    print(f"  {LIGHTRAG_URL}/webui/#/")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push QA opportunities to LightRAG")
    parser.add_argument("--dry-run", action="store_true", help="Preview without pushing")

    args = parser.parse_args()
    main(dry_run=args.dry_run)
