"""
Lazy GraphRAG Index Pipeline
============================

Builds a concept co-occurrence graph in Neo4j from PWS chunks.
Zero LLM cost - uses spaCy NLP only.

Pipeline:
  1. Load filtered chunks (756 chunks, 100+ chars each)
  2. spaCy noun-phrase extraction + custom PWS entity patterns
  3. Build co-occurrence graph: concepts in same chunk get linked
  4. Write LazyGraphConcept nodes + CO_OCCURS edges to Neo4j
  5. Python-side Louvain community detection
  6. Write community_id back to Neo4j concept nodes
  7. Verify the index

Usage:
  python lazy_graphrag_index.py /home/jsagi/pws_chunks_filtered.json
  python lazy_graphrag_index.py --verify          # Check existing index
  python lazy_graphrag_index.py --clear           # Remove lazy graph layer
"""

import json
import os
import sys
import argparse
import hashlib
from collections import Counter, defaultdict
from typing import Optional

import spacy
from spacy.language import Language
from spacy.tokens import Span
import networkx as nx
import community as community_louvain

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# PWS-specific entity patterns to boost extraction
PWS_ENTITIES = [
    # Frameworks
    "Jobs to Be Done", "JTBD", "Trending to the Absurd", "TTA",
    "S-Curve", "S Curve", "Ackoff's Pyramid", "Ackoff Pyramid",
    "Red Teaming", "Red Team", "Minto Pyramid", "Pyramid Principle",
    "Six Thinking Hats", "SCQA", "MECE", "Cynefin",
    "Camera Test", "Mom Test", "Reverse Salient",
    "Beautiful Question", "Disruptive Innovation",
    "Systems Thinking", "System Thinking",
    "Design Thinking", "Lean Startup",
    "Scenario Planning", "Scenario Analysis",
    "TRIZ", "DIKW", "Four Lenses",
    "Triple Validation", "Hypothesis Testing",
    "Wicked Problem", "Well-Defined Problem",
    # Key concepts
    "Problem Worth Solving", "PWS",
    "Customer Discovery", "Customer Interview",
    "Value Proposition", "Business Model",
    "Innovation Opportunity", "Opportunity Banking",
    "Assumption Testing", "Cognitive Bias",
    "Feedback Loop", "Leverage Point",
    "First Principles", "Root Cause",
    "Cross-Domain", "Cross Pollination",
    "Technology Lifecycle", "Adoption Curve",
    "Milkshake Example",
    # People
    "Russell Ackoff", "Clayton Christensen", "Barbara Minto",
    "Edward de Bono", "Warren Berger", "Dave Snowden",
]

# Minimum concept frequency to include in graph
MIN_CONCEPT_FREQ = 1
# Minimum noun phrase length (chars) to keep
MIN_PHRASE_LENGTH = 3
# Max noun phrase length (words) to keep
MAX_PHRASE_WORDS = 5


def get_neo4j_driver():
    """Create Neo4j driver."""
    from neo4j import GraphDatabase
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("ERROR: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD env vars required")
        sys.exit(1)
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def setup_nlp() -> Language:
    """Load spaCy with custom PWS entity patterns."""
    nlp = spacy.load("en_core_web_sm")

    # Add custom EntityRuler for PWS-specific terms
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    patterns = []
    for entity in PWS_ENTITIES:
        patterns.append({
            "label": "PWS_CONCEPT",
            "pattern": entity,
        })
        # Also add lowercase version
        if entity != entity.lower():
            patterns.append({
                "label": "PWS_CONCEPT",
                "pattern": entity.lower(),
            })
    ruler.add_patterns(patterns)

    return nlp


def extract_concepts(nlp: Language, text: str) -> list[str]:
    """Extract noun phrases and named entities from text."""
    doc = nlp(text)
    concepts = set()

    # Named entities (including our custom PWS_CONCEPT)
    for ent in doc.ents:
        name = ent.text.strip()
        if len(name) >= MIN_PHRASE_LENGTH:
            concepts.add(normalize_concept(name))

    # Noun phrases (chunks)
    for chunk in doc.noun_chunks:
        name = chunk.text.strip()
        # Filter: min length, max words, not just stopwords/pronouns
        if (len(name) >= MIN_PHRASE_LENGTH
            and len(name.split()) <= MAX_PHRASE_WORDS
            and not all(t.is_stop or t.is_punct for t in chunk)):
            concepts.add(normalize_concept(name))

    return list(concepts)


def normalize_concept(name: str) -> str:
    """Normalize concept name for consistent matching."""
    # Title case, strip extra whitespace
    name = " ".join(name.split())
    # Keep acronyms uppercase
    if name.isupper() and len(name) <= 6:
        return name
    # Title case for multi-word
    return name.title() if len(name.split()) > 1 else name.capitalize()


def build_cooccurrence_graph(
    chunks: list[dict],
    nlp: Language,
) -> tuple[nx.Graph, dict]:
    """
    Build co-occurrence graph from chunks.

    Returns:
        graph: NetworkX graph with concepts as nodes, co-occurrence as edges
        concept_chunks: {concept_name: [chunk_ids]} mapping
    """
    print("\n=== Phase 1: Extracting concepts from chunks ===")

    concept_chunks = defaultdict(list)  # concept -> [chunk_ids]
    chunk_concepts = {}  # chunk_id -> [concepts]
    all_concepts = Counter()

    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get("chunk_id", hashlib.sha1(chunk["content"].encode()).hexdigest())
        content = chunk["content"]

        concepts = extract_concepts(nlp, content)
        chunk_concepts[chunk_id] = concepts

        for concept in concepts:
            concept_chunks[concept].append(chunk_id)
            all_concepts[concept] += 1

        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(chunks)} chunks...")

    print(f"  Total unique concepts extracted: {len(all_concepts)}")
    print(f"  Top 20 concepts: {all_concepts.most_common(20)}")

    # Filter rare concepts
    filtered_concepts = {c for c, count in all_concepts.items() if count >= MIN_CONCEPT_FREQ}
    print(f"  After filtering (freq >= {MIN_CONCEPT_FREQ}): {len(filtered_concepts)} concepts")

    # Build co-occurrence graph
    print("\n=== Phase 2: Building co-occurrence graph ===")
    G = nx.Graph()

    # Add nodes
    for concept in filtered_concepts:
        G.add_node(concept, chunk_count=all_concepts[concept])

    # Add edges: concepts in same chunk
    edge_weights = Counter()
    for chunk_id, concepts in chunk_concepts.items():
        # Filter to kept concepts
        concepts = [c for c in concepts if c in filtered_concepts]
        # All pairs co-occur
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                pair = tuple(sorted([concepts[i], concepts[j]]))
                edge_weights[pair] += 1

    for (c1, c2), weight in edge_weights.items():
        G.add_edge(c1, c2, weight=weight)

    print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    return G, dict(concept_chunks)


def detect_communities(G: nx.Graph) -> dict:
    """
    Run Louvain community detection.

    Returns:
        {concept_name: community_id}
    """
    print("\n=== Phase 3: Community detection (Louvain) ===")

    if G.number_of_nodes() == 0:
        return {}

    # Louvain on the largest connected component
    partition = community_louvain.best_partition(G, weight="weight", resolution=1.0)

    num_communities = len(set(partition.values()))
    print(f"  Found {num_communities} communities")

    # Community size distribution
    community_sizes = Counter(partition.values())
    print(f"  Community sizes: {community_sizes.most_common(10)}")

    return partition


def write_to_neo4j(
    driver,
    G: nx.Graph,
    concept_chunks: dict,
    partition: dict,
):
    """Write LazyGraphConcept nodes and CO_OCCURS edges to Neo4j."""
    print("\n=== Phase 4: Writing to Neo4j ===")

    with driver.session() as session:
        # Create constraint for uniqueness
        print("  Creating constraint...")
        try:
            session.run("""
                CREATE CONSTRAINT lazy_concept_name IF NOT EXISTS
                FOR (n:LazyGraphConcept)
                REQUIRE n.name IS UNIQUE
            """)
        except Exception as e:
            print(f"  Constraint note: {e}")

        # Batch create nodes
        print(f"  Writing {G.number_of_nodes()} concept nodes...")
        nodes_data = []
        for concept in G.nodes():
            nodes_data.append({
                "name": concept,
                "chunk_count": G.nodes[concept].get("chunk_count", 0),
                "community_id": partition.get(concept, -1),
                "chunk_ids": concept_chunks.get(concept, [])[:20],  # Cap at 20
                "degree": G.degree(concept),
            })

        # Batch in groups of 100
        for i in range(0, len(nodes_data), 100):
            batch = nodes_data[i:i+100]
            session.run("""
                UNWIND $nodes AS node
                MERGE (n:LazyGraphConcept {name: node.name})
                SET n.chunk_count = node.chunk_count,
                    n.community_id = node.community_id,
                    n.chunk_ids = node.chunk_ids,
                    n.degree = node.degree
            """, nodes=batch)

        print(f"  Nodes written. Writing {G.number_of_edges()} CO_OCCURS edges...")

        # Batch create edges
        edges_data = []
        for c1, c2, data in G.edges(data=True):
            edges_data.append({
                "source": c1,
                "target": c2,
                "weight": data.get("weight", 1),
            })

        for i in range(0, len(edges_data), 200):
            batch = edges_data[i:i+200]
            session.run("""
                UNWIND $edges AS edge
                MATCH (a:LazyGraphConcept {name: edge.source})
                MATCH (b:LazyGraphConcept {name: edge.target})
                MERGE (a)-[r:CO_OCCURS]-(b)
                SET r.weight = edge.weight
            """, edges=batch)

        # Create index for fast lookups
        print("  Creating indexes...")
        try:
            session.run("""
                CREATE INDEX lazy_concept_community IF NOT EXISTS
                FOR (n:LazyGraphConcept)
                ON (n.community_id)
            """)
        except Exception:
            pass

        try:
            session.run("""
                CREATE FULLTEXT INDEX lazy_concept_search IF NOT EXISTS
                FOR (n:LazyGraphConcept)
                ON EACH [n.name]
            """)
        except Exception:
            pass

    print("  Done writing to Neo4j.")


def link_to_chunks(driver, concept_chunks: dict):
    """Link LazyGraphConcept nodes to existing Chunk nodes if they exist."""
    print("\n=== Phase 5: Linking concepts to chunk nodes ===")

    with driver.session() as session:
        # Check if Chunk nodes exist
        result = session.run("MATCH (c:Chunk) RETURN count(c) AS count")
        chunk_count = result.single()["count"]

        if chunk_count == 0:
            print("  No Chunk nodes found - skipping linkage")
            return

        print(f"  Found {chunk_count} Chunk nodes. Creating MENTIONED_IN links...")

        # For each concept, link to its chunks
        count = 0
        for concept, chunk_ids in concept_chunks.items():
            for chunk_id in chunk_ids[:10]:  # Limit links per concept
                session.run("""
                    MATCH (c:LazyGraphConcept {name: $concept})
                    MATCH (ch:Chunk) WHERE ch.id = $chunk_id OR ch.chunk_id = $chunk_id
                    MERGE (c)-[:MENTIONED_IN]->(ch)
                """, concept=concept, chunk_id=chunk_id)
                count += 1

        print(f"  Created {count} MENTIONED_IN links")


def verify_index(driver):
    """Verify the Lazy GraphRAG index in Neo4j."""
    print("\n=== Verification ===")

    with driver.session() as session:
        # Node count
        result = session.run("MATCH (n:LazyGraphConcept) RETURN count(n) AS count")
        node_count = result.single()["count"]
        print(f"  LazyGraphConcept nodes: {node_count}")

        # Edge count
        result = session.run("MATCH ()-[r:CO_OCCURS]-() RETURN count(r) AS count")
        edge_count = result.single()["count"]
        print(f"  CO_OCCURS edges: {edge_count}")

        # Community distribution
        result = session.run("""
            MATCH (n:LazyGraphConcept)
            RETURN n.community_id AS community, count(n) AS size
            ORDER BY size DESC LIMIT 10
        """)
        print("  Top communities:")
        for record in result:
            print(f"    Community {record['community']}: {record['size']} concepts")

        # Sample high-degree concepts
        result = session.run("""
            MATCH (n:LazyGraphConcept)
            RETURN n.name AS name, n.degree AS degree, n.community_id AS community
            ORDER BY n.degree DESC LIMIT 15
        """)
        print("  Top concepts by degree:")
        for record in result:
            print(f"    {record['name']} (degree={record['degree']}, community={record['community']})")

        # Sample co-occurrence path
        result = session.run("""
            MATCH (a:LazyGraphConcept)-[r:CO_OCCURS]-(b:LazyGraphConcept)
            WHERE r.weight > 2
            RETURN a.name AS from, b.name AS to, r.weight AS weight
            ORDER BY r.weight DESC LIMIT 10
        """)
        print("  Strongest co-occurrences:")
        for record in result:
            print(f"    {record['from']} <-> {record['to']} (weight={record['weight']})")

    print("\n  Verification complete.")


def clear_lazy_graph(driver):
    """Remove all Lazy GraphRAG data from Neo4j."""
    print("Clearing Lazy GraphRAG layer...")
    with driver.session() as session:
        session.run("MATCH (n:LazyGraphConcept) DETACH DELETE n")
        try:
            session.run("DROP INDEX lazy_concept_community IF EXISTS")
            session.run("DROP INDEX lazy_concept_search IF EXISTS")
            session.run("DROP CONSTRAINT lazy_concept_name IF EXISTS")
        except Exception:
            pass
    print("  Cleared.")


def main():
    parser = argparse.ArgumentParser(description="Lazy GraphRAG Index Pipeline")
    parser.add_argument("chunk_file", nargs="?", default="/home/jsagi/pws_chunks_filtered.json",
                        help="Path to filtered chunks JSON")
    parser.add_argument("--verify", action="store_true", help="Verify existing index")
    parser.add_argument("--clear", action="store_true", help="Remove lazy graph layer")

    args = parser.parse_args()

    driver = get_neo4j_driver()

    if args.clear:
        clear_lazy_graph(driver)
        driver.close()
        return

    if args.verify:
        verify_index(driver)
        driver.close()
        return

    # Full pipeline
    print("=" * 60)
    print("Lazy GraphRAG Index Pipeline")
    print("=" * 60)

    # Load chunks
    print(f"\nLoading chunks from {args.chunk_file}...")
    with open(args.chunk_file) as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks)} chunks")

    # Setup NLP
    print("\nLoading spaCy + PWS entity patterns...")
    nlp = setup_nlp()

    # Build co-occurrence graph
    G, concept_chunks = build_cooccurrence_graph(chunks, nlp)

    # Community detection
    partition = detect_communities(G)

    # Write to Neo4j
    write_to_neo4j(driver, G, concept_chunks, partition)

    # Link to existing Chunk nodes
    link_to_chunks(driver, concept_chunks)

    # Verify
    verify_index(driver)

    driver.close()

    print("\n" + "=" * 60)
    print("COMPLETE - Lazy GraphRAG index built in Neo4j")
    print("=" * 60)


if __name__ == "__main__":
    main()
