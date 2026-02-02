#!/usr/bin/env python3
"""
Neo4j Lazy Graph Analysis for Mindrian Triple-Mode Architecture
Run this locally with your Neo4j credentials

Usage:
    export NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
    export NEO4J_USER="neo4j"
    export NEO4J_PASSWORD="your-password"
    python neo4j_analysis.py

Or pass credentials directly:
    python neo4j_analysis.py --uri "neo4j+s://..." --user "neo4j" --password "..."
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from neo4j import GraphDatabase
except ImportError:
    print("Installing neo4j driver...")
    os.system("pip install neo4j")
    from neo4j import GraphDatabase


class Neo4jAnalyzer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.results = {}

    def close(self):
        self.driver.close()

    def run_query(self, name, cypher, description=""):
        """Run a Cypher query and store results."""
        print(f"\n{'='*60}")
        print(f"📊 {name}")
        print(f"   {description}")
        print(f"{'='*60}")

        try:
            with self.driver.session() as session:
                result = session.run(cypher)
                records = [dict(record) for record in result]

                self.results[name] = {
                    "query": cypher,
                    "description": description,
                    "count": len(records),
                    "data": records[:50]  # Limit to 50 for display
                }

                if records:
                    # Pretty print first few results
                    for i, record in enumerate(records[:10]):
                        print(f"  {i+1}. {record}")
                    if len(records) > 10:
                        print(f"  ... and {len(records)-10} more")
                else:
                    print("  (No results)")

                return records

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results[name] = {"error": str(e)}
            return []

    def analyze(self):
        """Run comprehensive schema analysis."""

        # ═══════════════════════════════════════════════════════════════
        # SECTION 1: BASIC SCHEMA
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 1: BASIC SCHEMA")
        print("█"*60)

        self.run_query(
            "Node Labels",
            "CALL db.labels() YIELD label RETURN label ORDER BY label",
            "All node types in the graph"
        )

        self.run_query(
            "Relationship Types",
            "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType",
            "All relationship types"
        )

        self.run_query(
            "Node Counts by Label",
            """
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
            """,
            "Count of nodes per type"
        )

        self.run_query(
            "Relationship Counts",
            """
            MATCH ()-[r]->()
            RETURN type(r) as relationship, count(r) as count
            ORDER BY count DESC
            """,
            "Count of relationships per type"
        )

        # ═══════════════════════════════════════════════════════════════
        # SECTION 2: RELATIONSHIP PATTERNS
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 2: RELATIONSHIP PATTERNS")
        print("█"*60)

        self.run_query(
            "Common Patterns",
            """
            MATCH (a)-[r]->(b)
            RETURN labels(a)[0] as from_label,
                   type(r) as relationship,
                   labels(b)[0] as to_label,
                   count(*) as count
            ORDER BY count DESC
            LIMIT 25
            """,
            "Most common (NodeA)-[REL]->(NodeB) patterns"
        )

        # ═══════════════════════════════════════════════════════════════
        # SECTION 3: FRAMEWORK & METHODOLOGY NODES
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 3: FRAMEWORK & METHODOLOGY")
        print("█"*60)

        self.run_query(
            "Framework Nodes",
            """
            MATCH (f:Framework)
            RETURN f.name, f.description, f.domain, f.id
            ORDER BY f.name
            LIMIT 20
            """,
            "Framework definitions"
        )

        self.run_query(
            "Concept Nodes (Sample)",
            """
            MATCH (c:Concept)
            RETURN c.name, c.description, c.id
            ORDER BY c.name
            LIMIT 20
            """,
            "Sample concept nodes"
        )

        self.run_query(
            "ProcessStep Nodes",
            """
            MATCH (p:ProcessStep)
            RETURN p.action, p.order, p.description
            ORDER BY p.order
            LIMIT 20
            """,
            "Workflow process steps"
        )

        self.run_query(
            "Framework-Step Relationships",
            """
            MATCH (f:Framework)-[r:CONTAINS]->(s:ProcessStep)
            RETURN f.name as framework, s.order, s.action
            ORDER BY f.name, s.order
            LIMIT 30
            """,
            "How frameworks connect to steps"
        )

        # ═══════════════════════════════════════════════════════════════
        # SECTION 4: CYNEFIN & CLASSIFICATION
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 4: CYNEFIN & CLASSIFICATION")
        print("█"*60)

        self.run_query(
            "Cynefin Domains",
            """
            MATCH (d:CynefinDomain)
            RETURN d.name, d.characteristics, d.response_strategy
            """,
            "Cynefin complexity domains"
        )

        self.run_query(
            "Domain-Framework Links",
            """
            MATCH (d:CynefinDomain)-[r]-(f:Framework)
            RETURN d.name as domain, type(r) as relationship, f.name as framework
            LIMIT 20
            """,
            "Which frameworks apply to which domains"
        )

        # ═══════════════════════════════════════════════════════════════
        # SECTION 5: TRIPLE-MODE ARCHITECTURE CHECK
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 5: TRIPLE-MODE ARCHITECTURE CHECK")
        print("█"*60)

        self.run_query(
            "VentureStage Nodes",
            """
            MATCH (v:VentureStage)
            RETURN v.id, v.name, v.description, v.order
            """,
            "❓ Do VentureStage nodes exist for Build Venture?"
        )

        self.run_query(
            "Bot Nodes",
            """
            MATCH (b:Bot)
            RETURN b.id, b.name, b.description, b.role
            LIMIT 20
            """,
            "❓ Do Bot nodes exist for routing?"
        )

        self.run_query(
            "EntryPoint Nodes",
            """
            MATCH (e:EntryPoint)
            RETURN e.id, e.name, e.description, e.default_mode
            """,
            "❓ Do EntryPoint nodes exist?"
        )

        self.run_query(
            "Stage-Framework Links",
            """
            MATCH (v:VentureStage)-[r:USES_FRAMEWORK]->(f:Framework)
            RETURN v.name as stage, f.name as framework, r.order, r.priority
            ORDER BY v.name, r.order
            """,
            "❓ Are stages linked to frameworks?"
        )

        self.run_query(
            "Stage-Bot Links",
            """
            MATCH (v:VentureStage)-[r:RECOMMENDED_BOT]->(b:Bot)
            RETURN v.name as stage, b.id as bot_id, r.priority
            """,
            "❓ Are stages linked to bots?"
        )

        self.run_query(
            "EntryPoint-Bot Links",
            """
            MATCH (e:EntryPoint)-[r:USES_BOT]->(b:Bot)
            RETURN e.name as entry_point, b.id as bot_id
            """,
            "❓ Are entry points linked to bots?"
        )

        self.run_query(
            "Session Nodes",
            """
            MATCH (s:Session)
            RETURN s.id, s.started_at, s.entry_point
            ORDER BY s.started_at DESC
            LIMIT 10
            """,
            "❓ Do Session nodes exist for persistence?"
        )

        self.run_query(
            "Insight Nodes",
            """
            MATCH (i:Insight)
            RETURN i.id, i.content, i.type
            LIMIT 10
            """,
            "❓ Do Insight nodes exist for Opportunity Bank?"
        )

        self.run_query(
            "Topic Nodes",
            """
            MATCH (t:Topic)
            RETURN t.name
            LIMIT 20
            """,
            "❓ Do Topic nodes exist for exploration tracking?"
        )

        # ═══════════════════════════════════════════════════════════════
        # SECTION 6: COMMUNITY STRUCTURE (GraphRAG)
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 6: COMMUNITY STRUCTURE (GraphRAG)")
        print("█"*60)

        self.run_query(
            "Community Nodes",
            """
            MATCH (c:Community)
            RETURN c.id, c.name, c.summary
            LIMIT 10
            """,
            "Community groupings for GraphRAG"
        )

        self.run_query(
            "CO_OCCURS Relationships",
            """
            MATCH ()-[r:CO_OCCURS]->()
            RETURN count(r) as total_cooccurs
            """,
            "Co-occurrence edges count"
        )

        self.run_query(
            "CO_OCCURS Sample",
            """
            MATCH (a)-[r:CO_OCCURS]->(b)
            RETURN a.name as concept_a, b.name as concept_b, r.weight
            ORDER BY r.weight DESC
            LIMIT 15
            """,
            "Strongest co-occurrence relationships"
        )

        # ═══════════════════════════════════════════════════════════════
        # SECTION 7: PWS SPECIFIC
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 7: PWS SPECIFIC")
        print("█"*60)

        self.run_query(
            "PWS Terms",
            """
            MATCH (p)
            WHERE p.pws_term = true OR 'PWSTerm' IN labels(p)
            RETURN p.name, labels(p) as labels
            LIMIT 20
            """,
            "PWS methodology specific terms"
        )

        self.run_query(
            "Problem Nodes",
            """
            MATCH (p:Problem)
            RETURN p.id, p.description, p.cynefin_domain
            LIMIT 10
            """,
            "Problem definitions"
        )

        # ═══════════════════════════════════════════════════════════════
        # SECTION 8: GRAPH STATISTICS
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "█"*60)
        print("█  SECTION 8: GRAPH STATISTICS")
        print("█"*60)

        self.run_query(
            "Total Nodes",
            "MATCH (n) RETURN count(n) as total_nodes",
            "Total node count"
        )

        self.run_query(
            "Total Relationships",
            "MATCH ()-[r]->() RETURN count(r) as total_relationships",
            "Total relationship count"
        )

        self.run_query(
            "Most Connected Nodes",
            """
            MATCH (n)
            WITH n, size((n)--()) as connections
            RETURN labels(n)[0] as label, n.name, connections
            ORDER BY connections DESC
            LIMIT 15
            """,
            "Nodes with most connections (hubs)"
        )

        self.run_query(
            "Isolated Nodes",
            """
            MATCH (n)
            WHERE NOT (n)--()
            RETURN labels(n)[0] as label, count(n) as isolated_count
            ORDER BY isolated_count DESC
            """,
            "Orphan nodes with no relationships"
        )

        return self.results

    def generate_report(self):
        """Generate analysis report."""

        print("\n")
        print("█"*60)
        print("█  ANALYSIS SUMMARY")
        print("█"*60)

        # Summarize what exists vs what's missing for Triple-Mode

        print("\n📋 TRIPLE-MODE READINESS CHECK:")
        print("-"*40)

        checks = {
            "VentureStage Nodes": "VentureStage Nodes",
            "Bot Nodes": "Bot Nodes",
            "EntryPoint Nodes": "EntryPoint Nodes",
            "Stage-Framework Links": "Stage-Framework Links",
            "Stage-Bot Links": "Stage-Bot Links",
            "EntryPoint-Bot Links": "EntryPoint-Bot Links",
            "Session Nodes": "Session Nodes",
            "Insight Nodes": "Insight Nodes",
            "Topic Nodes": "Topic Nodes",
            "Cynefin Domains": "Cynefin Domains",
            "Framework Nodes": "Framework Nodes",
            "Community Nodes": "Community Nodes",
            "CO_OCCURS Relationships": "CO_OCCURS Relationships"
        }

        missing = []
        existing = []

        for check_name, result_key in checks.items():
            result = self.results.get(result_key, {})
            if "error" in result:
                status = "❌ Error"
                missing.append(check_name)
            elif result.get("count", 0) > 0:
                count = result['count']
                # For CO_OCCURS, get the actual count from data
                if result_key == "CO_OCCURS Relationships" and result.get("data"):
                    count = result["data"][0].get("total_cooccurs", count)
                status = f"✅ Found ({count})"
                existing.append(check_name)
            else:
                status = "⚠️ Missing"
                missing.append(check_name)
            print(f"  {check_name}: {status}")

        # Generate migration recommendations
        print("\n")
        print("█"*60)
        print("█  MIGRATION RECOMMENDATIONS")
        print("█"*60)

        if "Bot Nodes" in missing:
            print("\n🔴 CRITICAL: Bot nodes missing - required for agent routing")
            print("   Run: python scripts/neo4j_migrate_bots.py")

        if "VentureStage Nodes" in missing:
            print("\n🔴 CRITICAL: VentureStage nodes missing - required for Build Venture")
            print("   Run: python scripts/neo4j_migrate_stages.py")

        if "EntryPoint Nodes" in missing:
            print("\n🟡 IMPORTANT: EntryPoint nodes missing - recommended for routing")
            print("   Run: python scripts/neo4j_migrate_entry_points.py")

        if "Stage-Bot Links" in missing and "VentureStage Nodes" in existing:
            print("\n🟡 IMPORTANT: Stage-Bot links missing")
            print("   Run: python scripts/neo4j_migrate_stage_links.py")

        if "Framework Nodes" in missing:
            print("\n🔴 CRITICAL: No Framework nodes - core schema missing!")
            print("   GraphRAG may need to be rebuilt")

        if "Community Nodes" in missing:
            print("\n🟡 WARNING: No Community nodes - GraphRAG clustering may be incomplete")

        # Save full results to JSON
        output_file = f"neo4j_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Full results saved to: {output_file}")

        return output_file, missing, existing


def main():
    parser = argparse.ArgumentParser(description='Neo4j Schema Analysis for Mindrian')
    parser.add_argument('--uri', default=os.getenv('NEO4J_URI'), help='Neo4j URI')
    parser.add_argument('--user', default=os.getenv('NEO4J_USER', 'neo4j'), help='Neo4j username')
    parser.add_argument('--password', default=os.getenv('NEO4J_PASSWORD'), help='Neo4j password')

    args = parser.parse_args()

    if not args.uri or not args.password:
        print("❌ Missing Neo4j credentials!")
        print("\nUsage:")
        print("  export NEO4J_URI='neo4j+s://your-instance.databases.neo4j.io'")
        print("  export NEO4J_PASSWORD='your-password'")
        print("  python neo4j_analysis.py")
        print("\nOr:")
        print("  python neo4j_analysis.py --uri 'neo4j+s://...' --password '...'")
        sys.exit(1)

    print("🔷 Neo4j Lazy Graph Analysis for Mindrian Triple-Mode")
    print("="*60)
    print(f"URI: {args.uri}")
    print(f"User: {args.user}")
    print("="*60)

    analyzer = Neo4jAnalyzer(args.uri, args.user, args.password)

    try:
        analyzer.analyze()
        output_file, missing, existing = analyzer.generate_report()
        print(f"\n✅ Analysis complete!")
        print(f"   Existing components: {len(existing)}")
        print(f"   Missing components: {len(missing)}")
        print(f"   Report saved to: {output_file}")
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
