#!/usr/bin/env python3
"""
Neo4j Triple-Mode Architecture Migration Script
Creates all required nodes and relationships for the new architecture.

Run this script to set up:
- Bot nodes (matching Agent Registry)
- VentureStage nodes (for Build Venture)
- EntryPoint nodes (for routing)
- Stage-Framework relationships
- Stage-Bot relationships
- EntryPoint-Bot relationships

Usage:
    python scripts/neo4j_triple_mode_migration.py
"""

import os
import sys
from typing import List, Dict, Any

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


class TripleModeMigration:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, name: str, cypher: str, params: Dict = None):
        """Run a Cypher query and report result."""
        print(f"\n{'='*50}")
        print(f"📝 {name}")
        print(f"{'='*50}")

        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                summary = result.consume()

                created = summary.counters.nodes_created
                rels = summary.counters.relationships_created

                if created > 0 or rels > 0:
                    print(f"  ✅ Created {created} nodes, {rels} relationships")
                else:
                    print(f"  ℹ️ No changes (may already exist)")

                return True

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    def migrate_bots(self):
        """Create Bot nodes matching the Agent Registry."""

        # Bot definitions from protocols/agent_registry.py
        bots = [
            {
                "id": "lawrence",
                "name": "Lawrence",
                "description": "PWS thinking partner - focused, concise guidance",
                "role": "orchestrator",
                "icon": "🧠",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search"]
            },
            {
                "id": "larry_playground",
                "name": "Larry Playground",
                "description": "Full-featured PWS lab with all tools",
                "role": "orchestrator",
                "icon": "🔬",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search", "research", "neo4j"]
            },
            {
                "id": "tta",
                "name": "Trending to the Absurd",
                "description": "Trend exploration and assumption stress-testing",
                "role": "workshop",
                "icon": "📈",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search", "research"]
            },
            {
                "id": "jtbd",
                "name": "Jobs to Be Done",
                "description": "Customer job discovery and validation",
                "role": "workshop",
                "icon": "🎯",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search"]
            },
            {
                "id": "ackoff",
                "name": "Ackoff DIKW Pyramid",
                "description": "Data-Information-Knowledge-Wisdom analysis",
                "role": "workshop",
                "icon": "🏛️",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search", "grading"]
            },
            {
                "id": "scurve",
                "name": "S-Curve Analysis",
                "description": "Technology adoption and timing analysis",
                "role": "workshop",
                "icon": "📊",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search", "research"]
            },
            {
                "id": "redteam",
                "name": "Red Team",
                "description": "Adversarial critique and assumption challenging",
                "role": "workshop",
                "icon": "🎯",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search"]
            },
            {
                "id": "pws_grading",
                "name": "PWS Grading",
                "description": "Quality assessment and scoring service",
                "role": "service",
                "icon": "📝",
                "capabilities": ["graphrag", "langextract", "grading"]
            },
            {
                "id": "research",
                "name": "Research Agent",
                "description": "Web research and data gathering service",
                "role": "service",
                "icon": "🔍",
                "capabilities": ["research", "langextract"]
            },
            {
                "id": "scenario",
                "name": "Scenario Analysis",
                "description": "Future scenario exploration and planning",
                "role": "workshop",
                "icon": "🔮",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search", "research"]
            },
            {
                "id": "beautiful_question",
                "name": "Beautiful Question",
                "description": "Deep question formulation and exploration",
                "role": "workshop",
                "icon": "❓",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search"]
            },
            {
                "id": "knowns",
                "name": "Known/Unknown Matrix",
                "description": "Risk and uncertainty mapping",
                "role": "workshop",
                "icon": "🗺️",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search"]
            },
            {
                "id": "nested_hierarchies",
                "name": "Nested Hierarchies",
                "description": "Multi-level systems analysis for finding leverage points",
                "role": "workshop",
                "icon": "🏛️",
                "capabilities": ["graphrag", "langextract", "context_store", "file_search"]
            },
            {
                "id": "graphrag",
                "name": "GraphRAG Service",
                "description": "Neo4j + vector hybrid retrieval service",
                "role": "service",
                "icon": "🕸️",
                "capabilities": ["graphrag", "neo4j"]
            }
        ]

        for bot in bots:
            self.run_query(
                f"Create Bot: {bot['name']}",
                """
                MERGE (b:Bot {id: $id})
                SET b.name = $name,
                    b.description = $description,
                    b.role = $role,
                    b.icon = $icon,
                    b.capabilities = $capabilities
                """,
                bot
            )

    def migrate_venture_stages(self):
        """Create VentureStage nodes for Build Venture entry point."""

        stages = [
            {
                "id": "pre_opportunity",
                "name": "Pre-Opportunity",
                "description": "Still looking for problems to solve",
                "order": 1,
                "job": "Find a problem worth solving",
                "mistake": "Jumping to solutions before understanding problems"
            },
            {
                "id": "opportunity_identified",
                "name": "Opportunity Identified",
                "description": "Found a problem, need to understand it deeply",
                "order": 2,
                "job": "Deeply understand the problem and who has it",
                "mistake": "Building before talking to customers"
            },
            {
                "id": "well_defined_problem",
                "name": "Well-Defined Problem",
                "description": "Problem is clear, designing the business",
                "order": 3,
                "job": "Design the business around the problem",
                "mistake": "Ignoring timing and competitive positioning"
            },
            {
                "id": "ready_to_build",
                "name": "Ready to Build",
                "description": "Problem validated, solution designed",
                "order": 4,
                "job": "Execute with discipline",
                "mistake": "Losing sight of the problem you're solving"
            }
        ]

        for stage in stages:
            self.run_query(
                f"Create VentureStage: {stage['name']}",
                """
                MERGE (v:VentureStage {id: $id})
                SET v.name = $name,
                    v.description = $description,
                    v.order = $order,
                    v.job = $job,
                    v.mistake = $mistake
                """,
                stage
            )

    def migrate_entry_points(self):
        """Create EntryPoint nodes for routing."""

        entry_points = [
            {
                "id": "brainstorming",
                "name": "Brainstorming",
                "description": "Free exploration of trends and opportunities",
                "default_mode": "sandbox",
                "icon": "💡"
            },
            {
                "id": "document_review",
                "name": "Document Review",
                "description": "Analysis of uploaded documents",
                "default_mode": "workshop",
                "icon": "📄"
            },
            {
                "id": "build_venture",
                "name": "Build Venture",
                "description": "Stage-based venture building",
                "default_mode": "sandbox",
                "icon": "🚀"
            }
        ]

        for ep in entry_points:
            self.run_query(
                f"Create EntryPoint: {ep['name']}",
                """
                MERGE (e:EntryPoint {id: $id})
                SET e.name = $name,
                    e.description = $description,
                    e.default_mode = $default_mode,
                    e.icon = $icon
                """,
                ep
            )

    def migrate_stage_framework_links(self):
        """Link VentureStages to recommended Frameworks."""

        # Stage → Framework mappings
        links = [
            # Pre-Opportunity: Exploration frameworks
            ("pre_opportunity", "Trending to the Absurd", 1, "primary"),
            ("pre_opportunity", "Beautiful Question", 2, "primary"),
            ("pre_opportunity", "Scenario Analysis", 3, "secondary"),

            # Opportunity Identified: Validation frameworks
            ("opportunity_identified", "Jobs to Be Done", 1, "primary"),
            ("opportunity_identified", "Problem Validation", 2, "primary"),
            ("opportunity_identified", "Customer Discovery", 3, "secondary"),

            # Well-Defined Problem: Business design frameworks
            ("well_defined_problem", "Business Model Canvas", 1, "primary"),
            ("well_defined_problem", "S-Curve Analysis", 2, "primary"),
            ("well_defined_problem", "Ackoff DIKW Pyramid", 3, "primary"),
            ("well_defined_problem", "BONO Six Thinking Hats", 4, "secondary"),

            # Ready to Build: Execution frameworks
            ("ready_to_build", "Red Teaming", 1, "primary"),
            ("ready_to_build", "Known/Unknown Matrix", 2, "primary"),
            ("ready_to_build", "Investment Readiness", 3, "secondary"),
        ]

        for stage_id, framework_name, order, priority in links:
            self.run_query(
                f"Link {stage_id} → {framework_name}",
                """
                MATCH (v:VentureStage {id: $stage_id})
                MATCH (f:Framework) WHERE f.name CONTAINS $framework_name
                MERGE (v)-[r:USES_FRAMEWORK]->(f)
                SET r.order = $order, r.priority = $priority
                """,
                {"stage_id": stage_id, "framework_name": framework_name, "order": order, "priority": priority}
            )

    def migrate_stage_bot_links(self):
        """Link VentureStages to recommended Bots."""

        # Stage → Bot mappings (primary bots first)
        links = [
            # Pre-Opportunity
            ("pre_opportunity", "lawrence", 1),
            ("pre_opportunity", "tta", 2),
            ("pre_opportunity", "beautiful_question", 3),
            ("pre_opportunity", "scenario", 4),

            # Opportunity Identified
            ("opportunity_identified", "jtbd", 1),
            ("opportunity_identified", "scenario", 2),
            ("opportunity_identified", "nested_hierarchies", 3),
            ("opportunity_identified", "research", 4),

            # Well-Defined Problem
            ("well_defined_problem", "ackoff", 1),
            ("well_defined_problem", "scurve", 2),
            ("well_defined_problem", "nested_hierarchies", 3),
            ("well_defined_problem", "redteam", 4),

            # Ready to Build
            ("ready_to_build", "redteam", 1),
            ("ready_to_build", "knowns", 2),
            ("ready_to_build", "pws_grading", 3),
        ]

        for stage_id, bot_id, priority in links:
            self.run_query(
                f"Link {stage_id} → {bot_id}",
                """
                MATCH (v:VentureStage {id: $stage_id})
                MATCH (b:Bot {id: $bot_id})
                MERGE (v)-[r:RECOMMENDED_BOT]->(b)
                SET r.priority = $priority
                """,
                {"stage_id": stage_id, "bot_id": bot_id, "priority": priority}
            )

    def migrate_entry_point_bot_links(self):
        """Link EntryPoints to available Bots."""

        # EntryPoint → Bot mappings
        links = [
            # Brainstorming entry point
            ("brainstorming", "lawrence", True),
            ("brainstorming", "tta", True),
            ("brainstorming", "beautiful_question", True),
            ("brainstorming", "scenario", True),
            ("brainstorming", "nested_hierarchies", True),
            ("brainstorming", "research", False),

            # Document Review entry point
            ("document_review", "lawrence", True),
            ("document_review", "ackoff", True),
            ("document_review", "redteam", True),
            ("document_review", "pws_grading", False),

            # Build Venture entry point
            ("build_venture", "jtbd", True),
            ("build_venture", "ackoff", True),
            ("build_venture", "scurve", True),
            ("build_venture", "redteam", True),
            ("build_venture", "knowns", True),
            ("build_venture", "nested_hierarchies", True),
        ]

        for ep_id, bot_id, is_primary in links:
            self.run_query(
                f"Link {ep_id} → {bot_id}",
                """
                MATCH (e:EntryPoint {id: $ep_id})
                MATCH (b:Bot {id: $bot_id})
                MERGE (e)-[r:USES_BOT]->(b)
                SET r.is_primary = $is_primary
                """,
                {"ep_id": ep_id, "bot_id": bot_id, "is_primary": is_primary}
            )

    def migrate_bot_relationships(self):
        """Create Bot → Bot relationships (can_call, handoff)."""

        # Bot → Bot call relationships
        call_links = [
            # Orchestrators can call anyone
            ("lawrence", "tta"),
            ("lawrence", "jtbd"),
            ("lawrence", "ackoff"),
            ("lawrence", "scurve"),
            ("lawrence", "redteam"),
            ("lawrence", "scenario"),
            ("lawrence", "beautiful_question"),
            ("lawrence", "knowns"),
            ("lawrence", "nested_hierarchies"),
            ("lawrence", "graphrag"),
            ("lawrence", "research"),
            ("lawrence", "pws_grading"),

            ("larry_playground", "tta"),
            ("larry_playground", "jtbd"),
            ("larry_playground", "ackoff"),
            ("larry_playground", "scurve"),
            ("larry_playground", "redteam"),
            ("larry_playground", "scenario"),
            ("larry_playground", "beautiful_question"),
            ("larry_playground", "knowns"),
            ("larry_playground", "nested_hierarchies"),
            ("larry_playground", "graphrag"),
            ("larry_playground", "research"),
            ("larry_playground", "pws_grading"),

            # Workshops can call services
            ("tta", "graphrag"),
            ("tta", "research"),
            ("jtbd", "graphrag"),
            ("ackoff", "graphrag"),
            ("ackoff", "pws_grading"),
            ("scurve", "graphrag"),
            ("scurve", "research"),
            ("redteam", "graphrag"),
            ("scenario", "graphrag"),
            ("scenario", "research"),
            ("nested_hierarchies", "graphrag"),
        ]

        for caller_id, callee_id in call_links:
            self.run_query(
                f"Link {caller_id} -[CAN_CALL]-> {callee_id}",
                """
                MATCH (caller:Bot {id: $caller_id})
                MATCH (callee:Bot {id: $callee_id})
                MERGE (caller)-[r:CAN_CALL]->(callee)
                """,
                {"caller_id": caller_id, "callee_id": callee_id}
            )

    def run_all(self):
        """Run all migrations in order."""

        print("\n" + "█"*60)
        print("█  NEO4J TRIPLE-MODE MIGRATION")
        print("█"*60)

        print("\n📦 Step 1: Creating Bot nodes...")
        self.migrate_bots()

        print("\n📦 Step 2: Creating VentureStage nodes...")
        self.migrate_venture_stages()

        print("\n📦 Step 3: Creating EntryPoint nodes...")
        self.migrate_entry_points()

        print("\n🔗 Step 4: Linking Stages → Frameworks...")
        self.migrate_stage_framework_links()

        print("\n🔗 Step 5: Linking Stages → Bots...")
        self.migrate_stage_bot_links()

        print("\n🔗 Step 6: Linking EntryPoints → Bots...")
        self.migrate_entry_point_bot_links()

        print("\n🔗 Step 7: Creating Bot → Bot relationships...")
        self.migrate_bot_relationships()

        print("\n" + "█"*60)
        print("█  MIGRATION COMPLETE")
        print("█"*60)
        print("\n✅ All Triple-Mode schema elements created!")
        print("   Run neo4j_analysis.py to verify.")


def main():
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')

    if not uri or not password:
        print("❌ Missing Neo4j credentials!")
        print("\nSet environment variables:")
        print("  export NEO4J_URI='neo4j+s://...'")
        print("  export NEO4J_PASSWORD='...'")
        sys.exit(1)

    print(f"🔷 Connecting to Neo4j: {uri}")

    migration = TripleModeMigration(uri, user, password)

    try:
        migration.run_all()
    finally:
        migration.close()


if __name__ == "__main__":
    main()
