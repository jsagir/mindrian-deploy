"""
Ingest Course Extractions to Neo4j LazyGraph
=============================================
Creates nodes and relationships from LangExtract extraction JSONs:
- Framework nodes (Six Thinking Hats, JTBD, TTA, etc.)
- CaseStudy nodes (IBM, ABB, Statoil, etc.)
- LazyGraphConcept nodes (for concepts to integrate with existing graph)
- Course material Document nodes
- Relationships between them based on graph_connections suggestions

Uses NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD from environment.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    print("ERROR: Missing Neo4j environment variables (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)")
    sys.exit(1)

from neo4j import GraphDatabase

# Directories
EXTRACTIONS_DIR = PROJECT_ROOT / "data" / "course_extractions"

# Known frameworks (normalize names)
FRAMEWORK_ALIASES = {
    "six thinking hats": "Six Thinking Hats",
    "bono-innovation framework": "Six Thinking Hats",
    "bono framework": "Six Thinking Hats",
    "parallel thinking": "Parallel Thinking",
    "pws methodology": "PWS Methodology",
    "jtbd": "Jobs To Be Done",
    "jobs to be done": "Jobs To Be Done",
    "tta": "Trending to the Absurd",
    "trending to the absurd": "Trending to the Absurd",
    "s-curve": "S-Curve Analysis",
    "scurve": "S-Curve Analysis",
    "red teaming": "Red Teaming",
    "ackoff's pyramid": "Ackoff's Pyramid",
    "dikw": "Ackoff's Pyramid",
    "scenario analysis": "Scenario Analysis",
    "minto pyramid": "Minto Pyramid",
    "five whys": "Five Whys",
    "design thinking": "Design Thinking",
}

# Known case studies
CASE_STUDY_INFO = {
    "IBM": {"industry": "Technology", "context": "Meeting time reduction via Six Thinking Hats", "result": "75% reduction"},
    "ABB": {"industry": "Engineering", "context": "Multinational project coordination", "result": "30 days to 2 days"},
    "Statoil": {"industry": "Energy", "context": "Strategic decision making", "result": "Improved collaboration"},
    "Shell": {"industry": "Energy", "context": "Scenario planning 1973 oil crisis", "result": "Prepared for disruption"},
    "NASA": {"industry": "Aerospace", "context": "Technical decision making", "result": "Referenced in safety"},
    "Challenger": {"industry": "Aerospace", "context": "O-ring decision failure", "result": "Cautionary tale"},
}

# Hat definitions
THINKING_HATS = {
    "White Hat": {"focus": "Facts, data, information", "question": "What do we know?"},
    "Red Hat": {"focus": "Emotions, intuitions", "question": "What does my gut tell me?"},
    "Black Hat": {"focus": "Risks, problems, cautions", "question": "What could go wrong?"},
    "Yellow Hat": {"focus": "Benefits, opportunities", "question": "What value could this create?"},
    "Green Hat": {"focus": "Creativity, alternatives", "question": "What else is possible?"},
    "Blue Hat": {"focus": "Process, meta-thinking", "question": "How should we think about this?"},
}


def normalize_framework(name: str) -> str:
    """Normalize framework name to canonical form."""
    lower = name.lower().strip()
    return FRAMEWORK_ALIASES.get(lower, name)


def parse_graph_connection(conn: str) -> Tuple[str, str, str]:
    """Parse a graph connection string like 'A -[REL]-> B' into (source, rel, target)."""
    # Pattern: SOURCE -[RELATIONSHIP]-> TARGET
    match = re.match(r'^(.+?)\s*-\[(.+?)\]->\s*(.+)$', conn.strip())
    if match:
        return (match.group(1).strip(), match.group(2).strip(), match.group(3).strip())
    return (None, None, None)


class Neo4jIngester:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.frameworks_created: Set[str] = set()
        self.cases_created: Set[str] = set()
        self.concepts_created: Set[str] = set()
        self.documents_created: Set[str] = set()
        self.relationships_created: int = 0

    def close(self):
        self.driver.close()

    def create_indexes(self):
        """Create indexes for efficient lookups."""
        with self.driver.session() as session:
            # Framework index
            session.run("""
                CREATE INDEX framework_name IF NOT EXISTS
                FOR (f:Framework) ON (f.name)
            """)
            # CaseStudy index
            session.run("""
                CREATE INDEX case_study_name IF NOT EXISTS
                FOR (c:CaseStudy) ON (c.name)
            """)
            # Document index
            session.run("""
                CREATE INDEX document_display_name IF NOT EXISTS
                FOR (d:Document) ON (d.display_name)
            """)
            print("  Indexes created/verified")

    def create_framework(self, name: str, description: str = None) -> bool:
        """Create or merge a Framework node."""
        normalized = normalize_framework(name)
        if normalized in self.frameworks_created:
            return False

        with self.driver.session() as session:
            session.run("""
                MERGE (f:Framework {name: $name})
                ON CREATE SET
                    f.description = $description,
                    f.created_at = datetime(),
                    f.source = 'langextract'
                ON MATCH SET
                    f.updated_at = datetime()
            """, name=normalized, description=description or f"PWS methodology framework: {normalized}")

        self.frameworks_created.add(normalized)
        return True

    def create_case_study(self, name: str) -> bool:
        """Create or merge a CaseStudy node."""
        if name in self.cases_created:
            return False

        info = CASE_STUDY_INFO.get(name, {})

        with self.driver.session() as session:
            session.run("""
                MERGE (c:CaseStudy {name: $name})
                ON CREATE SET
                    c.industry = $industry,
                    c.context = $context,
                    c.result = $result,
                    c.created_at = datetime(),
                    c.source = 'langextract'
                ON MATCH SET
                    c.updated_at = datetime()
            """,
                name=name,
                industry=info.get("industry", "Unknown"),
                context=info.get("context", "Referenced in PWS materials"),
                result=info.get("result", "See materials for details")
            )

        self.cases_created.add(name)
        return True

    def create_concept(self, name: str, category: str = None) -> bool:
        """Create or merge a LazyGraphConcept node (integrates with existing graph)."""
        normalized = name.lower().strip()
        if normalized in self.concepts_created:
            return False

        with self.driver.session() as session:
            session.run("""
                MERGE (c:LazyGraphConcept {name: $name})
                ON CREATE SET
                    c.category = $category,
                    c.chunk_count = 1,
                    c.created_at = datetime(),
                    c.source = 'langextract'
                ON MATCH SET
                    c.chunk_count = COALESCE(c.chunk_count, 0) + 1,
                    c.updated_at = datetime()
            """, name=normalized, category=category)

        self.concepts_created.add(normalized)
        return True

    def create_thinking_hat(self, hat_name: str) -> bool:
        """Create or merge a ThinkingHat node."""
        info = THINKING_HATS.get(hat_name, {})
        if not info:
            return False

        with self.driver.session() as session:
            session.run("""
                MERGE (h:ThinkingHat {name: $name})
                ON CREATE SET
                    h.focus = $focus,
                    h.key_question = $question,
                    h.created_at = datetime()
                ON MATCH SET
                    h.updated_at = datetime()
            """, name=hat_name, focus=info.get("focus", ""), question=info.get("question", ""))

        return True

    def create_document(self, display_name: str, category: str, extraction: dict) -> bool:
        """Create or merge a Document node representing the source material."""
        if display_name in self.documents_created:
            return False

        with self.driver.session() as session:
            session.run("""
                MERGE (d:Document {display_name: $display_name})
                ON CREATE SET
                    d.category = $category,
                    d.topic = $topic,
                    d.created_at = datetime(),
                    d.source = 'gemini_filesearch'
                ON MATCH SET
                    d.updated_at = datetime()
            """,
                display_name=display_name,
                category=category,
                topic=extraction.get("topic", "")
            )

        self.documents_created.add(display_name)
        return True

    def create_relationship(self, source: str, source_label: str, rel_type: str,
                           target: str, target_label: str) -> bool:
        """Create a relationship between two nodes."""
        # Sanitize relationship type (Neo4j requires alphanumeric + underscore)
        rel_type_safe = re.sub(r'[^a-zA-Z0-9_]', '_', rel_type.upper())

        with self.driver.session() as session:
            # Dynamic query based on labels
            query = f"""
                MATCH (s:{source_label} {{name: $source}})
                MATCH (t:{target_label} {{name: $target}})
                MERGE (s)-[r:{rel_type_safe}]->(t)
                ON CREATE SET r.created_at = datetime()
                RETURN count(r) as cnt
            """
            result = session.run(query, source=source, target=target)
            record = result.single()
            if record and record["cnt"] > 0:
                self.relationships_created += 1
                return True
        return False

    def ingest_extraction(self, extraction_path: Path) -> dict:
        """Ingest a single extraction JSON into Neo4j."""
        stats = {"frameworks": 0, "cases": 0, "concepts": 0, "hats": 0, "relationships": 0}

        try:
            data = json.loads(extraction_path.read_text())
        except Exception as e:
            print(f"    ERROR reading {extraction_path.name}: {e}")
            return stats

        display_name = data.get("display_name", extraction_path.stem)
        category = data.get("category", "Unknown")
        extraction = data.get("extraction", {})

        # Create document node
        self.create_document(display_name, category, extraction)

        # Create frameworks
        for fw in extraction.get("frameworks", []):
            if self.create_framework(fw):
                stats["frameworks"] += 1

        # Create case studies
        for cs in extraction.get("case_studies", []):
            if self.create_case_study(cs):
                stats["cases"] += 1

        # Create thinking hats if mentioned
        for hat in extraction.get("hat_definitions", []):
            hat_name = f"{hat} Hat" if not hat.endswith("Hat") else hat
            if self.create_thinking_hat(hat_name):
                stats["hats"] += 1

        # Create concepts
        for concept in extraction.get("concepts", []):
            if self.create_concept(concept, category):
                stats["concepts"] += 1

        # Process graph_connections
        for conn in extraction.get("graph_connections", []):
            source, rel, target = parse_graph_connection(conn)
            if source and rel and target:
                # Determine node types
                source_label = self._guess_node_label(source)
                target_label = self._guess_node_label(target)

                # Ensure nodes exist
                if source_label == "Framework":
                    self.create_framework(source)
                elif source_label == "CaseStudy":
                    self.create_case_study(source)
                elif source_label == "ThinkingHat":
                    self.create_thinking_hat(source)

                if target_label == "Framework":
                    self.create_framework(target)
                elif target_label == "CaseStudy":
                    self.create_case_study(target)
                elif target_label == "ThinkingHat":
                    self.create_thinking_hat(target)

                # Create relationship
                if self.create_relationship(source, source_label, rel, target, target_label):
                    stats["relationships"] += 1

        return stats

    def _guess_node_label(self, name: str) -> str:
        """Guess the node label based on the name."""
        lower = name.lower()

        # Check if it's a framework
        if normalize_framework(lower) != name or any(fw in lower for fw in ["framework", "methodology", "analysis", "thinking"]):
            return "Framework"

        # Check if it's a case study
        if name in CASE_STUDY_INFO:
            return "CaseStudy"

        # Check if it's a thinking hat
        if "hat" in lower:
            return "ThinkingHat"

        # Check for teaching elements
        if lower in ["workbook", "lecture", "worksheets"]:
            return "Document"

        # Default to Framework for known methodologies
        return "Framework"

    def link_documents_to_frameworks(self):
        """Create relationships between Document nodes and Framework nodes based on content."""
        with self.driver.session() as session:
            # Link BONO documents to Six Thinking Hats
            session.run("""
                MATCH (d:Document)
                WHERE d.category = 'BONO' OR d.display_name CONTAINS 'SixThinkingHats'
                MATCH (f:Framework {name: 'Six Thinking Hats'})
                MERGE (d)-[:TEACHES]->(f)
            """)

            # Link cohort documents to PWS Methodology
            session.run("""
                MATCH (d:Document)
                WHERE d.category STARTS WITH 'Cohort'
                MATCH (f:Framework {name: 'PWS Methodology'})
                MERGE (d)-[:PART_OF]->(f)
            """)

            print("  Document-Framework links created")

    def link_case_studies_to_frameworks(self):
        """Create relationships between CaseStudy nodes and Framework nodes."""
        with self.driver.session() as session:
            # IBM implemented Six Thinking Hats
            session.run("""
                MATCH (c:CaseStudy {name: 'IBM'})
                MATCH (f:Framework {name: 'Six Thinking Hats'})
                MERGE (c)-[:IMPLEMENTED]->(f)
            """)

            # ABB implemented Six Thinking Hats
            session.run("""
                MATCH (c:CaseStudy {name: 'ABB'})
                MATCH (f:Framework {name: 'Six Thinking Hats'})
                MERGE (c)-[:IMPLEMENTED]->(f)
            """)

            # Shell used Scenario Analysis
            session.run("""
                MATCH (c:CaseStudy {name: 'Shell'})
                MATCH (f:Framework {name: 'Scenario Analysis'})
                MERGE (c)-[:IMPLEMENTED]->(f)
            """)

            print("  CaseStudy-Framework links created")

    def link_hats_to_framework(self):
        """Create relationships between ThinkingHat nodes and Six Thinking Hats framework."""
        with self.driver.session() as session:
            session.run("""
                MATCH (h:ThinkingHat)
                MATCH (f:Framework {name: 'Six Thinking Hats'})
                MERGE (f)-[:HAS_COMPONENT]->(h)
            """)
            print("  ThinkingHat-Framework links created")


def main():
    print("=" * 70)
    print("NEO4J LAZYGRAPH INGESTION FROM COURSE EXTRACTIONS")
    print("=" * 70)
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Extractions dir: {EXTRACTIONS_DIR}")

    if not EXTRACTIONS_DIR.exists():
        print(f"ERROR: Extractions directory not found: {EXTRACTIONS_DIR}")
        return

    # Find all extraction JSONs
    extraction_files = list(EXTRACTIONS_DIR.glob("*.json"))
    print(f"\nFound {len(extraction_files)} extraction files")

    if not extraction_files:
        print("No extraction files to process!")
        return

    # Initialize ingester
    ingester = Neo4jIngester(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        print("\n1. Creating indexes...")
        ingester.create_indexes()

        print("\n2. Processing extractions...")
        total_stats = {"frameworks": 0, "cases": 0, "concepts": 0, "hats": 0, "relationships": 0}

        for i, extraction_path in enumerate(extraction_files, 1):
            print(f"  [{i}/{len(extraction_files)}] {extraction_path.name[:60]}...")
            stats = ingester.ingest_extraction(extraction_path)
            for k, v in stats.items():
                total_stats[k] += v

        print("\n3. Creating framework relationships...")
        ingester.link_documents_to_frameworks()
        ingester.link_case_studies_to_frameworks()
        ingester.link_hats_to_framework()

        print("\n" + "=" * 70)
        print("INGESTION COMPLETE")
        print("=" * 70)
        print(f"Frameworks created:    {len(ingester.frameworks_created)}")
        print(f"Case studies created:  {len(ingester.cases_created)}")
        print(f"Concepts created:      {len(ingester.concepts_created)}")
        print(f"Documents created:     {len(ingester.documents_created)}")
        print(f"Relationships created: {ingester.relationships_created}")
        print()
        print("Frameworks:", sorted(ingester.frameworks_created))
        print("Case Studies:", sorted(ingester.cases_created))

    finally:
        ingester.close()


if __name__ == "__main__":
    main()
