"""
Ontology Designer for KG-RAG Applications

Generates graph schema (node types, relationship types, properties)
for common document domains. Use as starting point for knowledge graph
construction.

Usage:
    python ontology_designer.py --domain legal
    python ontology_designer.py --domain web_crawl
    python ontology_designer.py --domain support_tickets
    python ontology_designer.py --domain contracts
    python ontology_designer.py --domain enterprise_kb
    python ontology_designer.py --domain custom --description "Medical research papers"
"""

import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class NodeType:
    label: str
    description: str
    properties: dict  # {name: {type, indexed, vectorized, description}}


@dataclass
class RelationshipType:
    type: str
    from_label: str
    to_label: str
    description: str
    properties: dict = field(default_factory=dict)


@dataclass
class GraphOntology:
    domain: str
    description: str
    node_types: list
    relationship_types: list
    vector_indices: list
    expansion_strategy: dict

    def to_cypher_constraints(self) -> str:
        """Generate Cypher constraints for the ontology."""
        lines = ["// Node uniqueness constraints"]
        for nt in self.node_types:
            id_props = [p for p, v in nt.properties.items() if v.get("indexed")]
            if id_props:
                lines.append(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{nt.label}) "
                    f"REQUIRE n.{id_props[0]} IS UNIQUE;"
                )

        lines.append("\n// Vector indices")
        for vi in self.vector_indices:
            lines.append(
                f"CREATE VECTOR INDEX {vi['index_name']} IF NOT EXISTS\n"
                f"FOR (n:{vi['label']}) ON (n.{vi['property']})\n"
                f"OPTIONS {{indexConfig: {{`vector.dimensions`: {vi['dimensions']}, "
                f"`vector.similarity_function`: '{vi['similarity']}'}}}};"
            )

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def to_markdown(self) -> str:
        lines = [f"# Graph Ontology: {self.domain}\n"]
        lines.append(f"*{self.description}*\n")

        lines.append("## Node Types\n")
        for nt in self.node_types:
            lines.append(f"### {nt.label}")
            lines.append(f"{nt.description}\n")
            lines.append("| Property | Type | Indexed | Vectorized |")
            lines.append("|----------|------|---------|------------|")
            for pname, pinfo in nt.properties.items():
                lines.append(
                    f"| {pname} | {pinfo['type']} | "
                    f"{'Y' if pinfo.get('indexed') else ''} | "
                    f"{'Y' if pinfo.get('vectorized') else ''} |"
                )
            lines.append("")

        lines.append("## Relationship Types\n")
        lines.append("| Type | From | To | Description |")
        lines.append("|------|------|----|-------------|")
        for rt in self.relationship_types:
            lines.append(f"| {rt.type} | {rt.from_label} | {rt.to_label} | {rt.description} |")

        lines.append(f"\n## Expansion Strategy\n")
        lines.append(f"- **Max Hops:** {self.expansion_strategy['max_hops']}")
        lines.append(f"- **Relationships to Follow:** {', '.join(self.expansion_strategy['follow_relationships'])}")
        lines.append(f"- **Stop Conditions:** {self.expansion_strategy.get('stop_conditions', 'max hops reached')}")

        return "\n".join(lines)


# ============================================================
# DOMAIN ONTOLOGIES
# ============================================================

def legal_ontology() -> GraphOntology:
    return GraphOntology(
        domain="Legal / Legislation",
        description="Hierarchical legal document structure with definitions, cross-references, and amendments",
        node_types=[
            NodeType("Legislation", "Root document node", {
                "id": {"type": "string", "indexed": True, "vectorized": False, "description": "Unique legislation ID"},
                "title": {"type": "string", "indexed": False, "vectorized": False, "description": "Legislation title"},
                "jurisdiction": {"type": "string", "indexed": True, "vectorized": False, "description": "Legal jurisdiction"},
                "effective_date": {"type": "date", "indexed": True, "vectorized": False, "description": "Date enacted"},
            }),
            NodeType("Part", "Major division of legislation", {
                "number": {"type": "integer", "indexed": True, "vectorized": False, "description": "Part number"},
                "title": {"type": "string", "indexed": False, "vectorized": False, "description": "Part title"},
            }),
            NodeType("Section", "Section within a part", {
                "number": {"type": "string", "indexed": True, "vectorized": False, "description": "Section number"},
                "title": {"type": "string", "indexed": False, "vectorized": False, "description": "Section title"},
                "text": {"type": "string", "indexed": False, "vectorized": True, "description": "Full text content"},
            }),
            NodeType("Definition", "Defined term within legislation", {
                "term": {"type": "string", "indexed": True, "vectorized": False, "description": "Defined term"},
                "text": {"type": "string", "indexed": False, "vectorized": True, "description": "Definition text"},
            }),
            NodeType("Clause", "Individual clause or provision", {
                "number": {"type": "string", "indexed": True, "vectorized": False, "description": "Clause number"},
                "text": {"type": "string", "indexed": False, "vectorized": True, "description": "Clause text"},
            }),
        ],
        relationship_types=[
            RelationshipType("CONTAINS", "Legislation", "Part", "Legislation contains parts"),
            RelationshipType("CONTAINS", "Part", "Section", "Part contains sections"),
            RelationshipType("CONTAINS", "Section", "Definition", "Section contains definitions"),
            RelationshipType("CONTAINS", "Section", "Clause", "Section contains clauses"),
            RelationshipType("DEFINES", "Definition", "Term", "Definition defines a term"),
            RelationshipType("REFERENCES", "Section", "Section", "Cross-reference between sections"),
            RelationshipType("AMENDS", "Clause", "Clause", "Amendment relationship"),
        ],
        vector_indices=[
            {"index_name": "section_embeddings", "label": "Section", "property": "embedding", "dimensions": 1536, "similarity": "cosine"},
            {"index_name": "definition_embeddings", "label": "Definition", "property": "embedding", "dimensions": 1536, "similarity": "cosine"},
            {"index_name": "clause_embeddings", "label": "Clause", "property": "embedding", "dimensions": 1536, "similarity": "cosine"},
        ],
        expansion_strategy={
            "max_hops": 3,
            "follow_relationships": ["CONTAINS", "REFERENCES", "DEFINES"],
            "stop_conditions": "max hops or 50 nodes reached",
            "priority": "definitions > parent sections > cross-references"
        }
    )


def web_crawl_ontology() -> GraphOntology:
    return GraphOntology(
        domain="Web Crawl",
        description="Crawled website structure with pages, sections, links, and extracted entities",
        node_types=[
            NodeType("WebSite", "Root website node", {
                "domain": {"type": "string", "indexed": True, "vectorized": False, "description": "Website domain"},
                "crawl_date": {"type": "datetime", "indexed": True, "vectorized": False, "description": "Last crawl date"},
            }),
            NodeType("WebPage", "Individual web page", {
                "url": {"type": "string", "indexed": True, "vectorized": False, "description": "Page URL"},
                "title": {"type": "string", "indexed": False, "vectorized": False, "description": "Page title"},
                "meta_description": {"type": "string", "indexed": False, "vectorized": False, "description": "Meta description"},
            }),
            NodeType("Section", "Content section within a page", {
                "heading": {"type": "string", "indexed": False, "vectorized": False, "description": "Section heading"},
                "level": {"type": "integer", "indexed": False, "vectorized": False, "description": "Heading level (h1-h6)"},
                "text": {"type": "string", "indexed": False, "vectorized": True, "description": "Section text content"},
            }),
            NodeType("Entity", "Extracted named entity", {
                "name": {"type": "string", "indexed": True, "vectorized": False, "description": "Entity name"},
                "type": {"type": "string", "indexed": True, "vectorized": False, "description": "Entity type (person, org, etc)"},
            }),
        ],
        relationship_types=[
            RelationshipType("HAS_PAGE", "WebSite", "WebPage", "Website contains page"),
            RelationshipType("HAS_SECTION", "WebPage", "Section", "Page contains section"),
            RelationshipType("NEXT_SECTION", "Section", "Section", "Sequential section ordering"),
            RelationshipType("LINKS_TO", "WebPage", "WebPage", "Hyperlink between pages"),
            RelationshipType("MENTIONS", "Section", "Entity", "Section mentions entity"),
            RelationshipType("RELATED_TO", "Entity", "Entity", "Entities related to each other"),
        ],
        vector_indices=[
            {"index_name": "section_embeddings", "label": "Section", "property": "embedding", "dimensions": 1536, "similarity": "cosine"},
        ],
        expansion_strategy={
            "max_hops": 2,
            "follow_relationships": ["HAS_SECTION", "LINKS_TO", "MENTIONS"],
            "stop_conditions": "max hops or 30 nodes reached",
            "priority": "sibling sections > linked pages > mentioned entities"
        }
    )


def support_tickets_ontology() -> GraphOntology:
    return GraphOntology(
        domain="Support Tickets / Tasks",
        description="Project management and support system with teams, projects, tasks, and users",
        node_types=[
            NodeType("Team", "Organizational team", {
                "name": {"type": "string", "indexed": True, "vectorized": False, "description": "Team name"},
                "department": {"type": "string", "indexed": True, "vectorized": False, "description": "Department"},
            }),
            NodeType("Project", "Project or product area", {
                "name": {"type": "string", "indexed": True, "vectorized": False, "description": "Project name"},
                "status": {"type": "string", "indexed": True, "vectorized": False, "description": "Project status"},
            }),
            NodeType("Task", "Individual task or ticket", {
                "title": {"type": "string", "indexed": True, "vectorized": False, "description": "Task title"},
                "description": {"type": "string", "indexed": False, "vectorized": True, "description": "Task description"},
                "status": {"type": "string", "indexed": True, "vectorized": False, "description": "Task status"},
                "priority": {"type": "string", "indexed": True, "vectorized": False, "description": "Priority level"},
                "created": {"type": "datetime", "indexed": True, "vectorized": False, "description": "Creation date"},
            }),
            NodeType("User", "System user", {
                "name": {"type": "string", "indexed": True, "vectorized": False, "description": "User name"},
                "role": {"type": "string", "indexed": True, "vectorized": False, "description": "User role"},
                "email": {"type": "string", "indexed": True, "vectorized": False, "description": "User email"},
            }),
        ],
        relationship_types=[
            RelationshipType("ASSIGNED_TO", "Team", "Project", "Team works on project"),
            RelationshipType("HAS_TASK", "Project", "Task", "Project contains task"),
            RelationshipType("MEMBER_OF", "User", "Team", "User belongs to team"),
            RelationshipType("CREATED", "User", "Task", "User created task"),
            RelationshipType("ASSIGNED", "User", "Task", "User assigned to task"),
            RelationshipType("DEPENDS_ON", "Task", "Task", "Task dependency"),
            RelationshipType("RELATED_TO", "Task", "Task", "Related tasks"),
        ],
        vector_indices=[
            {"index_name": "task_embeddings", "label": "Task", "property": "embedding", "dimensions": 1536, "similarity": "cosine"},
        ],
        expansion_strategy={
            "max_hops": 2,
            "follow_relationships": ["HAS_TASK", "ASSIGNED_TO", "DEPENDS_ON", "ASSIGNED"],
            "stop_conditions": "max hops reached",
            "priority": "task context > team context > user context",
            "dual_retrieval": True,
            "note": "Use vector search for content questions, text-to-Cypher for analytical questions"
        }
    )


DOMAIN_REGISTRY = {
    "legal": legal_ontology,
    "web_crawl": web_crawl_ontology,
    "support_tickets": support_tickets_ontology,
}


def main():
    parser = argparse.ArgumentParser(description="Generate graph ontology for KG-RAG")
    parser.add_argument("--domain", required=True, choices=list(DOMAIN_REGISTRY.keys()) + ["custom"])
    parser.add_argument("--description", help="Description for custom domain")
    parser.add_argument("--format", choices=["json", "markdown", "cypher"], default="markdown")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    if args.domain == "custom":
        print(f"Custom domain: {args.description}")
        print("Custom ontology generation requires LLM assistance.")
        print("Use the KG-RAG Architect skill to design a custom ontology.")
        return

    ontology = DOMAIN_REGISTRY[args.domain]()

    if args.format == "json":
        output = ontology.to_json()
    elif args.format == "cypher":
        output = ontology.to_cypher_constraints()
    else:
        output = ontology.to_markdown()

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
