"""
Graph-Driven Research Orchestrator
===================================

Queries the Neo4j graph to discover:
  ProblemType → CynefinDomain → Framework → MCPTool → Technique

Then executes the discovered tool pipeline via tool_dispatcher.

This is the runtime implementation of the Universal Framework Orchestrator v3.0,
adapted for Mindrian's Chainlit + Gemini architecture.

Usage:
    from tools.graph_orchestrator import orchestrate_research

    plan = discover_research_plan("scale a tahini business")
    results = execute_research_plan(plan)
"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("graph_orchestrator")


@dataclass
class ResearchPlan:
    """A graph-discovered research execution plan."""
    challenge: str
    problem_type: Optional[str] = None
    cynefin_domain: Optional[str] = None
    frameworks: List[Dict] = field(default_factory=list)
    tool_names: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    process_steps: List[str] = field(default_factory=list)
    trace: Dict = field(default_factory=dict)


def _get_neo4j():
    """Reuse graphrag_lite's driver."""
    from tools.graphrag_lite import _get_neo4j as get_driver
    return get_driver()


def discover_research_plan(challenge: str) -> ResearchPlan:
    """
    Phase 1-4 of the orchestrator: query Neo4j to build a research plan.

    Steps:
        1. Classify ProblemType from challenge keywords
        2. Map to CynefinDomain
        3. Find Frameworks via ADDRESSES_PROBLEM_TYPE
        4. Get MCPTools via ORCHESTRATES_MCP / USES_MCP
        5. Get Techniques via USES_TECHNIQUE / SUPPORTS
        6. Find ProcessStep chains via LEADS_TO

    Returns:
        ResearchPlan with discovered tools and techniques.
    """
    t0 = time.time()
    plan = ResearchPlan(challenge=challenge)
    driver = _get_neo4j()

    if not driver:
        plan.trace["error"] = "no_neo4j_driver"
        return plan

    try:
        with driver.session() as session:
            # Step 1: Classify ProblemType
            result = session.run("""
                CALL db.index.fulltext.queryNodes('entity_fulltext', $challenge)
                YIELD node, score
                WHERE 'ProblemType' IN labels(node) AND score > 0.3
                RETURN node.name AS name, node.recommended_approach AS approach, score
                ORDER BY score DESC
                LIMIT 1
            """, challenge=challenge)
            rec = result.single()
            if rec:
                plan.problem_type = rec["name"]
                plan.trace["problem_type_score"] = rec["score"]

            # Step 2: CynefinDomain
            if plan.problem_type:
                result = session.run("""
                    MATCH (pt:ProblemType {name: $pt})-[:PART_OF]->(cd:CynefinDomain)
                    RETURN cd.name AS domain
                """, pt=plan.problem_type)
                rec = result.single()
                if rec:
                    plan.cynefin_domain = rec["domain"]

            # Step 3: Frameworks via ADDRESSES_PROBLEM_TYPE
            if plan.problem_type:
                result = session.run("""
                    MATCH (f:Framework)-[:ADDRESSES_PROBLEM_TYPE]->(pt:ProblemType {name: $pt})
                    OPTIONAL MATCH (f)-[:USES_TECHNIQUE]->(t:Technique)
                    RETURN f.name AS framework, f.framework_type AS type,
                           collect(DISTINCT t.name)[0..5] AS techniques
                    LIMIT 5
                """, pt=plan.problem_type)
                for rec in result:
                    plan.frameworks.append({
                        "name": rec["framework"],
                        "type": rec["type"],
                        "techniques": rec["techniques"],
                    })
                    plan.techniques.extend(rec["techniques"])

            # Step 4: MCPTools via ORCHESTRATES_MCP / USES_MCP
            fw_names = [f["name"] for f in plan.frameworks]
            if fw_names:
                result = session.run("""
                    MATCH (f:Framework)-[:ORCHESTRATES_MCP|USES_MCP]->(m:MCPTool)
                    WHERE f.name IN $frameworks
                    RETURN DISTINCT m.name AS tool, m.description AS desc
                """, frameworks=fw_names)
                for rec in result:
                    if rec["tool"] not in plan.tool_names:
                        plan.tool_names.append(rec["tool"])

            # If no tools from frameworks, try technique-based SUPPORTS
            if not plan.tool_names and plan.techniques:
                result = session.run("""
                    MATCH (m:MCPTool)-[:SUPPORTS]->(t:Technique)
                    WHERE t.name IN $techniques
                    RETURN DISTINCT m.name AS tool, count(t) AS support_count
                    ORDER BY support_count DESC
                    LIMIT 5
                """, techniques=list(set(plan.techniques))[:10])
                for rec in result:
                    if rec["tool"] not in plan.tool_names:
                        plan.tool_names.append(rec["tool"])

            # Step 5: ProcessStep chains (optional, for ordering)
            keywords = challenge.split()[:3]
            for kw in keywords:
                result = session.run("""
                    MATCH path = (s1:ProcessStep)-[:LEADS_TO*1..4]->(sN:ProcessStep)
                    WHERE toLower(s1.name) CONTAINS toLower($kw)
                    RETURN [n IN nodes(path) | n.name] AS steps
                    ORDER BY length(path) DESC
                    LIMIT 1
                """, kw=kw)
                rec = result.single()
                if rec and rec["steps"]:
                    plan.process_steps = rec["steps"]
                    break

    except Exception as e:
        plan.trace["error"] = str(e)
        logger.error("Research plan discovery failed: %s", e)

    plan.trace["ms"] = round((time.time() - t0) * 1000)
    plan.trace["tool_count"] = len(plan.tool_names)
    plan.trace["framework_count"] = len(plan.frameworks)
    logger.info(
        "Research plan: problem=%s, domain=%s, frameworks=%d, tools=%d [%dms]",
        plan.problem_type, plan.cynefin_domain,
        len(plan.frameworks), len(plan.tool_names), plan.trace["ms"]
    )
    return plan


def execute_research_plan(plan: ResearchPlan) -> Dict:
    """
    Execute the tools discovered in a research plan via tool_dispatcher.

    Args:
        plan: A ResearchPlan from discover_research_plan()

    Returns:
        Dict with results per tool, skipped tools, and timing.
    """
    from tools.tool_dispatcher import execute_tool, resolve_tool

    t0 = time.time()
    results = []
    skipped = []

    for tool_name in plan.tool_names:
        entry = resolve_tool(tool_name)
        if not entry["available"]:
            skipped.append(tool_name)
            logger.info("Skipping unavailable tool: %s", tool_name)
            continue

        result = execute_tool(tool_name, plan.challenge)
        results.append({"tool": tool_name, "result": result})

    return {
        "challenge": plan.challenge,
        "problem_type": plan.problem_type,
        "cynefin_domain": plan.cynefin_domain,
        "frameworks": [f["name"] for f in plan.frameworks],
        "executed": [r["tool"] for r in results],
        "skipped": skipped,
        "results": results,
        "ms": round((time.time() - t0) * 1000),
    }


def format_plan_as_mermaid(plan: ResearchPlan) -> str:
    """
    Generate a Mermaid flowchart from a discovered research plan.

    Returns:
        Mermaid markdown string for rendering.
    """
    from tools.tool_dispatcher import resolve_tool

    lines = [
        "```mermaid",
        "graph TD",
        '    CHALLENGE["Challenge<br/>' + plan.challenge[:60].replace('"', "'") + '"]',
        "",
    ]

    # Discovery subgraph
    lines.append('    subgraph DISCOVERY["Neo4j Schema Discovery"]')
    if plan.problem_type:
        lines.append(f'        PT["{plan.problem_type}"]')
    if plan.cynefin_domain:
        lines.append(f'        CD["{plan.cynefin_domain} Domain"]')
    for i, fw in enumerate(plan.frameworks[:3]):
        lines.append(f'        FW{i}["{fw["name"][:40]}"]')
    lines.append("    end")
    lines.append("")

    # Connect discovery
    if plan.problem_type:
        lines.append("    CHALLENGE --> PT")
    if plan.cynefin_domain and plan.problem_type:
        lines.append("    PT -->|PART_OF| CD")
    for i, fw in enumerate(plan.frameworks[:3]):
        if plan.problem_type:
            lines.append(f"    PT -->|ADDRESSES| FW{i}")

    lines.append("")

    # Execution subgraph
    lines.append('    subgraph EXECUTION["Tool Execution"]')
    for i, tool_name in enumerate(plan.tool_names[:6]):
        entry = resolve_tool(tool_name)
        available = entry["available"]
        marker = "" if available else " ⛔"
        cat = entry.get("category", "?")
        lines.append(f'        T{i}["Step {i+1}: {tool_name[:30]}{marker}<br/>({cat})"]')
    lines.append("    end")
    lines.append("")

    # Connect frameworks to tools
    if plan.frameworks and plan.tool_names:
        lines.append(f"    FW0 --> T0")
    for i in range(1, min(len(plan.tool_names), 6)):
        lines.append(f"    T{i-1} -->|LEADS_TO| T{i}")

    # Synthesis
    lines.append("")
    lines.append('    SYNTH["Synthesis<br/>Merge findings"]')
    if plan.tool_names:
        last = min(len(plan.tool_names), 6) - 1
        lines.append(f"    T{last} --> SYNTH")
    lines.append("")

    # Styling
    lines.append("    classDef challenge fill:#e1f5fe,stroke:#01579b,stroke-width:3px")
    lines.append("    classDef discovery fill:#fff3e0,stroke:#e65100,stroke-width:2px")
    lines.append("    classDef execution fill:#f3e5f5,stroke:#4a148c,stroke-width:2px")
    lines.append("    classDef synthesis fill:#c8e6c9,stroke:#388e3c,stroke-width:2px")
    lines.append("    class CHALLENGE challenge")
    if plan.problem_type:
        lines.append("    class PT,CD discovery")
    for i in range(len(plan.frameworks[:3])):
        lines.append(f"    class FW{i} discovery")
    for i in range(min(len(plan.tool_names), 6)):
        lines.append(f"    class T{i} execution")
    lines.append("    class SYNTH synthesis")
    lines.append("```")

    return "\n".join(lines)


def format_plan_summary(plan: ResearchPlan) -> str:
    """Format a human-readable summary of the research plan."""
    from tools.tool_dispatcher import resolve_tool, get_available_tools

    parts = [f"## Research Orchestration Plan: {plan.challenge[:80]}"]
    parts.append("")

    if plan.problem_type:
        parts.append(f"**Problem Classification**: {plan.problem_type}")
    if plan.cynefin_domain:
        parts.append(f"**Cynefin Domain**: {plan.cynefin_domain}")
    if plan.frameworks:
        fw_names = ", ".join(f["name"] for f in plan.frameworks[:5])
        parts.append(f"**Frameworks**: {fw_names}")
    parts.append("")

    if plan.tool_names:
        parts.append("### Tool Pipeline")
        for i, tool_name in enumerate(plan.tool_names):
            entry = resolve_tool(tool_name)
            status = "available" if entry["available"] else "not available"
            parts.append(f"{i+1}. **{tool_name}** ({entry['category']}) — {status}")
    else:
        parts.append("*No specific tools discovered. Using default Tavily + Neo4j pipeline.*")

    if plan.techniques:
        unique = list(dict.fromkeys(plan.techniques))[:8]
        parts.append("")
        parts.append(f"**Techniques**: {', '.join(unique)}")

    if plan.process_steps:
        parts.append("")
        parts.append(f"**Process Pattern**: {' → '.join(plan.process_steps)}")

    return "\n".join(parts)
