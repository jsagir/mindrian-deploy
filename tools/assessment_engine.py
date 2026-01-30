"""
Innovation Assessment Engine v3.0 - Modular Architecture
=========================================================

Context-Engineered, Evidence-Driven, Token-Optimized Assessment System

Modules:
0. Core Engine & State Management
1. Graph Analysis (Neo4j) - Framework discovery, differential insights
2. Pattern Discovery (FileSearch) - Vector semantic search
3. External Validation (Tavily) - Research, expert validation
4. Synthesis Engine - Integrate findings, challenge questions
5. Report Generation - Full evidence-attributed assessment

Tools Used:
- Neo4j (graphrag_lite) → Framework knowledge, relationships
- FileSearch (pws_brain) → Semantic pattern discovery
- Tavily → Web research, expert validation
- LangExtract → Structured data extraction
- Gemini → Reasoning, synthesis
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

# === Tool Imports ===

# Gemini
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Neo4j (Graph Analysis)
try:
    from tools.graphrag_lite import query_neo4j, get_neo4j_driver, enrich_for_bot
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

# FileSearch (Pattern Discovery)
try:
    from tools.pws_brain import semantic_search, search_pws_knowledge
    FILESEARCH_AVAILABLE = True
except ImportError:
    FILESEARCH_AVAILABLE = False

# Tavily (External Validation)
try:
    from tools.tavily_search import tavily_search, tavily_search_context
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

# LangExtract (Structured Extraction)
try:
    from tools.langextract import instant_extract, background_extract_pws
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False


# ==============================================================================
# MODULE 0: CORE ENGINE & STATE MANAGEMENT
# ==============================================================================

class ModuleStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class EvidenceItem:
    """Single piece of evidence with source attribution."""
    id: str
    source_type: str  # neo4j, filesearch, tavily, langextract, gemini
    source_id: str  # query ID, search ID, etc.
    content: str
    confidence: float
    timestamp: str = ""
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.id:
            self.id = f"ev_{hashlib.sha256(f'{self.source_type}:{self.content[:50]}'.encode()).hexdigest()[:8]}"


@dataclass
class ModuleOutput:
    """Output from a module with evidence trail."""
    module_id: str
    status: str
    data: Dict
    evidence: List[EvidenceItem]
    execution_time_ms: int
    error: Optional[str] = None


@dataclass
class AssessmentState:
    """Complete state of an assessment session."""
    # Metadata
    session_id: str
    version: str = "3.0-modular"
    created_at: str = ""
    updated_at: str = ""

    # Project context
    project_name: str = ""
    project_domain: str = ""
    project_description: str = ""
    student_id: str = ""

    # Module tracking
    modules_completed: List[str] = field(default_factory=list)
    current_module: str = ""
    checkpoints: List[Dict] = field(default_factory=list)

    # Evidence trail
    evidence_trail: List[EvidenceItem] = field(default_factory=list)

    # Module outputs
    module_outputs: Dict[str, ModuleOutput] = field(default_factory=dict)

    # Analysis results
    frameworks_found: List[Dict] = field(default_factory=list)
    patterns_discovered: List[Dict] = field(default_factory=list)
    validations: List[Dict] = field(default_factory=list)
    synthesis: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

    def add_evidence(self, evidence: EvidenceItem):
        self.evidence_trail.append(evidence)

    def checkpoint(self) -> Dict:
        """Create a checkpoint for resumption."""
        cp = {
            "checkpoint_id": f"cp_{len(self.checkpoints)+1}",
            "timestamp": datetime.utcnow().isoformat(),
            "current_module": self.current_module,
            "modules_completed": self.modules_completed.copy(),
            "evidence_count": len(self.evidence_trail)
        }
        self.checkpoints.append(cp)
        return cp

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "version": self.version,
            "created_at": self.created_at,
            "project_name": self.project_name,
            "project_domain": self.project_domain,
            "modules_completed": self.modules_completed,
            "evidence_count": len(self.evidence_trail),
            "checkpoints": self.checkpoints,
            "module_outputs": {k: asdict(v) if hasattr(v, '__dataclass_fields__') else v
                              for k, v in self.module_outputs.items()}
        }


def create_assessment_session(
    project_name: str,
    project_domain: str = "",
    project_description: str = "",
    student_id: str = ""
) -> AssessmentState:
    """Initialize a new assessment session."""
    session_id = f"assess_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.sha256(project_name.encode()).hexdigest()[:6]}"

    return AssessmentState(
        session_id=session_id,
        project_name=project_name,
        project_domain=project_domain,
        project_description=project_description,
        student_id=student_id
    )


# ==============================================================================
# MODULE 1: GRAPH ANALYSIS (Neo4j)
# ==============================================================================

FRAMEWORK_DISCOVERY_QUERIES = {
    "find_frameworks": """
        MATCH (f:Framework)
        WHERE toLower(f.name) CONTAINS toLower($keyword)
           OR toLower(f.description) CONTAINS toLower($keyword)
           OR toLower(f.domain) CONTAINS toLower($keyword)
        RETURN f.name as name, f.description as description,
               f.domain as domain, f.effectiveness_score as score
        LIMIT 15
    """,

    "differential_analysis": """
        MATCH (da:DifferentialAnalysis)
        WHERE da.breakthrough_potential > 0.6
        RETURN da.insight as insight, da.framework_pair as frameworks,
               da.differential_score as score, da.thinking_triggers as triggers
        LIMIT 10
    """,

    "innovation_opportunities": """
        MATCH (io:InnovationOpportunity)
        WHERE io.domain CONTAINS $domain OR io.title CONTAINS $keyword
        RETURN io.title as title, io.description as description,
               io.breakthrough_potential as potential, io.implementation_path as path
        LIMIT 10
    """,

    "pedagogical_reflections": """
        MATCH (pr:PedagogicalReflection)
        WHERE pr.topic CONTAINS $topic
        RETURN pr.question as question, pr.socratic_cascade as cascade,
               pr.learning_objective as objective
        LIMIT 5
    """,

    "problem_patterns": """
        MATCH (p:Problem)-[:RELATED_TO]->(f:Framework)
        WHERE p.domain CONTAINS $domain
        RETURN p.name as problem, p.description as description,
               collect(f.name) as frameworks, p.severity as severity
        LIMIT 10
    """,

    "case_studies": """
        MATCH (cs:CaseStudy)
        WHERE cs.domain CONTAINS $domain OR cs.methodology CONTAINS $methodology
        RETURN cs.name as name, cs.outcome as outcome,
               cs.lessons as lessons, cs.methodology as methodology
        LIMIT 5
    """
}


async def run_graph_analysis(
    state: AssessmentState,
    content: str,
    keywords: List[str] = None
) -> ModuleOutput:
    """
    Module 1: Graph Analysis Engine

    Extracts framework knowledge, differential insights, and innovation patterns from Neo4j.
    """
    start_time = datetime.utcnow()
    state.current_module = "graph_analysis"

    if not NEO4J_AVAILABLE:
        return ModuleOutput(
            module_id="graph_analysis",
            status=ModuleStatus.SKIPPED,
            data={"reason": "Neo4j not available"},
            evidence=[],
            execution_time_ms=0
        )

    results = {
        "frameworks": [],
        "differentials": [],
        "innovations": [],
        "problems": [],
        "case_studies": [],
        "pedagogical": [],
        "coverage_gaps": []
    }
    evidence = []

    # Extract keywords from content if not provided
    if not keywords:
        keywords = extract_keywords(content)

    domain = state.project_domain or keywords[0] if keywords else "innovation"

    try:
        driver = get_neo4j_driver()
        if not driver:
            raise Exception("Could not connect to Neo4j")

        with driver.session() as session:
            # Step 1.1: Framework Discovery
            for keyword in keywords[:5]:  # Limit to 5 keywords
                result = session.run(
                    FRAMEWORK_DISCOVERY_QUERIES["find_frameworks"],
                    {"keyword": keyword}
                )
                for record in result:
                    fw = dict(record)
                    fw["source_keyword"] = keyword
                    results["frameworks"].append(fw)

                    evidence.append(EvidenceItem(
                        id=f"neo4j_fw_{len(evidence)}",
                        source_type="neo4j",
                        source_id=f"framework_discovery:{keyword}",
                        content=f"Framework: {fw.get('name')} - {fw.get('description', '')[:100]}",
                        confidence=fw.get('score', 0.5) or 0.5,
                        metadata={"query": "find_frameworks", "keyword": keyword}
                    ))

            # Step 1.2: Differential Analysis
            result = session.run(FRAMEWORK_DISCOVERY_QUERIES["differential_analysis"], {})
            for record in result:
                da = dict(record)
                results["differentials"].append(da)
                evidence.append(EvidenceItem(
                    id=f"neo4j_da_{len(evidence)}",
                    source_type="neo4j",
                    source_id="differential_analysis",
                    content=f"Differential: {da.get('insight', '')[:150]}",
                    confidence=da.get('score', 0.5) or 0.5,
                    metadata={"frameworks": da.get('frameworks')}
                ))

            # Step 1.3: Innovation Opportunities
            result = session.run(
                FRAMEWORK_DISCOVERY_QUERIES["innovation_opportunities"],
                {"domain": domain, "keyword": keywords[0] if keywords else ""}
            )
            for record in result:
                io = dict(record)
                results["innovations"].append(io)
                evidence.append(EvidenceItem(
                    id=f"neo4j_io_{len(evidence)}",
                    source_type="neo4j",
                    source_id="innovation_opportunities",
                    content=f"Opportunity: {io.get('title')} - {io.get('description', '')[:100]}",
                    confidence=io.get('potential', 0.5) or 0.5,
                    metadata={"path": io.get('path')}
                ))

            # Step 1.4: Problem Patterns
            result = session.run(
                FRAMEWORK_DISCOVERY_QUERIES["problem_patterns"],
                {"domain": domain}
            )
            for record in result:
                prob = dict(record)
                results["problems"].append(prob)
                evidence.append(EvidenceItem(
                    id=f"neo4j_prob_{len(evidence)}",
                    source_type="neo4j",
                    source_id="problem_patterns",
                    content=f"Problem: {prob.get('problem')} [{prob.get('severity', 'unknown')}]",
                    confidence=0.7,
                    metadata={"frameworks": prob.get('frameworks')}
                ))

            # Step 1.5: Case Studies
            result = session.run(
                FRAMEWORK_DISCOVERY_QUERIES["case_studies"],
                {"domain": domain, "methodology": "PWS"}
            )
            for record in result:
                cs = dict(record)
                results["case_studies"].append(cs)
                evidence.append(EvidenceItem(
                    id=f"neo4j_cs_{len(evidence)}",
                    source_type="neo4j",
                    source_id="case_studies",
                    content=f"Case: {cs.get('name')} - {cs.get('outcome', '')[:100]}",
                    confidence=0.8,
                    metadata={"methodology": cs.get('methodology')}
                ))

        # Identify coverage gaps
        expected_frameworks = ["JTBD", "TTA", "S-Curve", "Five Whys", "Mom Test", "Red Teaming"]
        found_names = [f.get('name', '').lower() for f in results["frameworks"]]
        results["coverage_gaps"] = [
            fw for fw in expected_frameworks
            if fw.lower() not in ' '.join(found_names)
        ]

    except Exception as e:
        return ModuleOutput(
            module_id="graph_analysis",
            status=ModuleStatus.FAILED,
            data={"error": str(e)},
            evidence=evidence,
            execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            error=str(e)
        )

    # Add evidence to state
    for ev in evidence:
        state.add_evidence(ev)

    state.frameworks_found = results["frameworks"]

    execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    return ModuleOutput(
        module_id="graph_analysis",
        status=ModuleStatus.COMPLETED,
        data=results,
        evidence=evidence,
        execution_time_ms=execution_time
    )


# ==============================================================================
# MODULE 2: PATTERN DISCOVERY (FileSearch)
# ==============================================================================

async def run_pattern_discovery(
    state: AssessmentState,
    content: str,
    frameworks: List[Dict] = None
) -> ModuleOutput:
    """
    Module 2: Pattern Discovery System

    Discovers cross-domain patterns and validates framework gaps using FileSearch.
    """
    start_time = datetime.utcnow()
    state.current_module = "pattern_discovery"

    if not FILESEARCH_AVAILABLE:
        return ModuleOutput(
            module_id="pattern_discovery",
            status=ModuleStatus.SKIPPED,
            data={"reason": "FileSearch not available"},
            evidence=[],
            execution_time_ms=0
        )

    results = {
        "patterns": [],
        "gap_validations": [],
        "cross_domain_insights": [],
        "methodology_matches": []
    }
    evidence = []

    try:
        # Step 2.1: Semantic search for patterns
        keywords = extract_keywords(content)

        for keyword in keywords[:3]:
            search_results = await search_pws_knowledge(
                query=f"{keyword} innovation pattern methodology",
                limit=5
            )

            if search_results:
                for result in search_results:
                    pattern = {
                        "keyword": keyword,
                        "content": result.get("content", "")[:300],
                        "source": result.get("source", ""),
                        "score": result.get("score", 0.5)
                    }
                    results["patterns"].append(pattern)

                    evidence.append(EvidenceItem(
                        id=f"fs_pattern_{len(evidence)}",
                        source_type="filesearch",
                        source_id=f"pattern_search:{keyword}",
                        content=pattern["content"][:150],
                        confidence=pattern["score"],
                        metadata={"source": pattern["source"], "keyword": keyword}
                    ))

        # Step 2.2: Gap validation - search for coverage gaps
        coverage_gaps = state.module_outputs.get("graph_analysis", ModuleOutput(
            module_id="", status="", data={}, evidence=[], execution_time_ms=0
        )).data.get("coverage_gaps", [])

        for gap in coverage_gaps[:3]:
            gap_results = await search_pws_knowledge(
                query=f"{gap} framework application {state.project_domain}",
                limit=3
            )

            if gap_results:
                validation = {
                    "gap": gap,
                    "findings": [r.get("content", "")[:200] for r in gap_results],
                    "relevance": sum(r.get("score", 0) for r in gap_results) / len(gap_results)
                }
                results["gap_validations"].append(validation)

                evidence.append(EvidenceItem(
                    id=f"fs_gap_{len(evidence)}",
                    source_type="filesearch",
                    source_id=f"gap_validation:{gap}",
                    content=f"Gap '{gap}' validation: {validation['findings'][0][:100] if validation['findings'] else 'No findings'}",
                    confidence=validation["relevance"],
                    metadata={"gap": gap}
                ))

        # Step 2.3: Cross-domain insights
        if frameworks:
            for fw in frameworks[:3]:
                fw_name = fw.get("name", "")
                cross_results = await search_pws_knowledge(
                    query=f"{fw_name} cross-domain application examples",
                    limit=2
                )

                if cross_results:
                    for result in cross_results:
                        insight = {
                            "framework": fw_name,
                            "insight": result.get("content", "")[:200],
                            "application": f"Apply {fw_name} to {state.project_domain}"
                        }
                        results["cross_domain_insights"].append(insight)

                        evidence.append(EvidenceItem(
                            id=f"fs_cross_{len(evidence)}",
                            source_type="filesearch",
                            source_id=f"cross_domain:{fw_name}",
                            content=insight["insight"][:150],
                            confidence=result.get("score", 0.5),
                            metadata={"framework": fw_name}
                        ))

    except Exception as e:
        return ModuleOutput(
            module_id="pattern_discovery",
            status=ModuleStatus.FAILED,
            data={"error": str(e)},
            evidence=evidence,
            execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            error=str(e)
        )

    # Add evidence to state
    for ev in evidence:
        state.add_evidence(ev)

    state.patterns_discovered = results["patterns"]

    execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    return ModuleOutput(
        module_id="pattern_discovery",
        status=ModuleStatus.COMPLETED,
        data=results,
        evidence=evidence,
        execution_time_ms=execution_time
    )


# ==============================================================================
# MODULE 3: EXTERNAL VALIDATION (Tavily)
# ==============================================================================

async def run_external_validation(
    state: AssessmentState,
    content: str,
    key_claims: List[str] = None
) -> ModuleOutput:
    """
    Module 3: External Validation

    Validates insights through expert research using Tavily.
    """
    start_time = datetime.utcnow()
    state.current_module = "external_validation"

    if not TAVILY_AVAILABLE:
        return ModuleOutput(
            module_id="external_validation",
            status=ModuleStatus.SKIPPED,
            data={"reason": "Tavily not available"},
            evidence=[],
            execution_time_ms=0
        )

    results = {
        "confirmed_insights": [],
        "challenged_insights": [],
        "new_perspectives": [],
        "market_research": [],
        "expert_opinions": []
    }
    evidence = []

    try:
        # Extract claims to validate if not provided
        if not key_claims:
            key_claims = await extract_claims(content)

        # Step 3.1: Validate each key claim
        for claim in key_claims[:5]:  # Limit to 5 claims
            search_query = f"{claim} expert analysis research 2024 2025"

            validation_results = await tavily_search(
                query=search_query,
                search_depth="advanced",
                max_results=3
            )

            if validation_results and validation_results.get("results"):
                # Analyze if results confirm or challenge the claim
                supporting = []
                contradicting = []

                for result in validation_results["results"]:
                    result_content = result.get("content", "")

                    # Simple heuristic: check for agreement/disagreement signals
                    if any(word in result_content.lower() for word in ["confirms", "supports", "validates", "shows"]):
                        supporting.append(result)
                    elif any(word in result_content.lower() for word in ["contradicts", "challenges", "disproves", "however"]):
                        contradicting.append(result)
                    else:
                        supporting.append(result)  # Default to supporting

                if supporting:
                    results["confirmed_insights"].append({
                        "claim": claim,
                        "sources": [{"title": s.get("title"), "url": s.get("url"), "snippet": s.get("content", "")[:150]} for s in supporting]
                    })

                if contradicting:
                    results["challenged_insights"].append({
                        "claim": claim,
                        "contradictions": [{"title": s.get("title"), "url": s.get("url"), "snippet": s.get("content", "")[:150]} for s in contradicting]
                    })

                # Add evidence
                for result in validation_results["results"]:
                    evidence.append(EvidenceItem(
                        id=f"tavily_val_{len(evidence)}",
                        source_type="tavily",
                        source_id=result.get("url", "unknown"),
                        content=f"{result.get('title', 'Untitled')}: {result.get('content', '')[:150]}",
                        confidence=result.get("score", 0.5),
                        metadata={"url": result.get("url"), "claim": claim}
                    ))

        # Step 3.2: Market research
        market_query = f"{state.project_domain} market trends innovation 2025"
        market_results = await tavily_search(
            query=market_query,
            search_depth="basic",
            max_results=3
        )

        if market_results and market_results.get("results"):
            for result in market_results["results"]:
                results["market_research"].append({
                    "title": result.get("title"),
                    "insight": result.get("content", "")[:200],
                    "url": result.get("url")
                })

                evidence.append(EvidenceItem(
                    id=f"tavily_mkt_{len(evidence)}",
                    source_type="tavily",
                    source_id=result.get("url", "unknown"),
                    content=f"Market: {result.get('content', '')[:150]}",
                    confidence=0.7,
                    metadata={"type": "market_research", "url": result.get("url")}
                ))

        # Step 3.3: Expert perspectives
        expert_query = f"{state.project_domain} expert opinion thought leader analysis"
        expert_results = await tavily_search(
            query=expert_query,
            search_depth="basic",
            max_results=2
        )

        if expert_results and expert_results.get("results"):
            for result in expert_results["results"]:
                results["expert_opinions"].append({
                    "title": result.get("title"),
                    "perspective": result.get("content", "")[:200],
                    "url": result.get("url")
                })

                evidence.append(EvidenceItem(
                    id=f"tavily_exp_{len(evidence)}",
                    source_type="tavily",
                    source_id=result.get("url", "unknown"),
                    content=f"Expert: {result.get('content', '')[:150]}",
                    confidence=0.8,
                    metadata={"type": "expert", "url": result.get("url")}
                ))

    except Exception as e:
        return ModuleOutput(
            module_id="external_validation",
            status=ModuleStatus.FAILED,
            data={"error": str(e)},
            evidence=evidence,
            execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            error=str(e)
        )

    # Add evidence to state
    for ev in evidence:
        state.add_evidence(ev)

    state.validations = results["confirmed_insights"] + results["challenged_insights"]

    execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    return ModuleOutput(
        module_id="external_validation",
        status=ModuleStatus.COMPLETED,
        data=results,
        evidence=evidence,
        execution_time_ms=execution_time
    )


# ==============================================================================
# MODULE 4: SYNTHESIS ENGINE
# ==============================================================================

SYNTHESIS_PROMPT = """You are synthesizing an innovation assessment from multiple data sources.

PROJECT: {project_name}
DOMAIN: {project_domain}

MODULE OUTPUTS:

### Graph Analysis Results:
Frameworks Found: {frameworks_count}
{frameworks_summary}

Differential Insights: {differentials_count}
{differentials_summary}

Coverage Gaps: {coverage_gaps}

### Pattern Discovery Results:
Patterns Found: {patterns_count}
{patterns_summary}

### External Validation Results:
Confirmed Claims: {confirmed_count}
{confirmed_summary}

Challenged Claims: {challenged_count}
{challenged_summary}

Market Research:
{market_summary}

---

SYNTHESIS TASKS:
1. Identify the TOP 3 key themes across all findings
2. Generate 5 strategic CHALLENGE QUESTIONS that probe deeper
3. Assess cognitive balance (operational vs breakthrough thinking)
4. Identify the TOP 5 strategic insights with evidence
5. Note any critical gaps or blind spots

Respond in JSON:
{{
    "key_themes": ["theme1", "theme2", "theme3"],
    "challenge_questions": [
        {{"question": "...", "context": "...", "evidence_refs": ["ev_id1", "ev_id2"]}},
        ...
    ],
    "cognitive_balance": {{
        "operational_pct": 0-100,
        "breakthrough_pct": 0-100,
        "assessment": "description"
    }},
    "strategic_insights": [
        {{"insight": "...", "evidence": ["..."], "priority": "high/medium/low"}},
        ...
    ],
    "gaps_and_blindspots": ["gap1", "gap2"],
    "overall_assessment": "2-3 sentence summary"
}}"""


async def run_synthesis(state: AssessmentState) -> ModuleOutput:
    """
    Module 4: Synthesis Engine

    Integrates all findings and generates challenge questions.
    """
    start_time = datetime.utcnow()
    state.current_module = "synthesis"

    if not GEMINI_AVAILABLE:
        return ModuleOutput(
            module_id="synthesis",
            status=ModuleStatus.SKIPPED,
            data={"reason": "Gemini not available"},
            evidence=[],
            execution_time_ms=0
        )

    # Gather all module outputs
    graph_output = state.module_outputs.get("graph_analysis", ModuleOutput(
        module_id="", status="", data={}, evidence=[], execution_time_ms=0
    ))
    pattern_output = state.module_outputs.get("pattern_discovery", ModuleOutput(
        module_id="", status="", data={}, evidence=[], execution_time_ms=0
    ))
    validation_output = state.module_outputs.get("external_validation", ModuleOutput(
        module_id="", status="", data={}, evidence=[], execution_time_ms=0
    ))

    # Build synthesis prompt
    prompt = SYNTHESIS_PROMPT.format(
        project_name=state.project_name,
        project_domain=state.project_domain,
        frameworks_count=len(graph_output.data.get("frameworks", [])),
        frameworks_summary="\n".join([f"- {f.get('name')}: {f.get('description', '')[:80]}" for f in graph_output.data.get("frameworks", [])[:5]]),
        differentials_count=len(graph_output.data.get("differentials", [])),
        differentials_summary="\n".join([f"- {d.get('insight', '')[:100]}" for d in graph_output.data.get("differentials", [])[:3]]),
        coverage_gaps=", ".join(graph_output.data.get("coverage_gaps", [])),
        patterns_count=len(pattern_output.data.get("patterns", [])),
        patterns_summary="\n".join([f"- {p.get('content', '')[:100]}" for p in pattern_output.data.get("patterns", [])[:5]]),
        confirmed_count=len(validation_output.data.get("confirmed_insights", [])),
        confirmed_summary="\n".join([f"- {c.get('claim', '')[:80]}" for c in validation_output.data.get("confirmed_insights", [])[:3]]),
        challenged_count=len(validation_output.data.get("challenged_insights", [])),
        challenged_summary="\n".join([f"- {c.get('claim', '')[:80]}" for c in validation_output.data.get("challenged_insights", [])[:3]]),
        market_summary="\n".join([f"- {m.get('insight', '')[:100]}" for m in validation_output.data.get("market_research", [])[:3]])
    )

    try:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=3000
            )
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        synthesis_data = json.loads(text)

        # Add synthesis evidence
        evidence = [EvidenceItem(
            id="synth_main",
            source_type="gemini",
            source_id="synthesis_engine",
            content=synthesis_data.get("overall_assessment", ""),
            confidence=0.9,
            metadata={"themes": synthesis_data.get("key_themes", [])}
        )]

        state.synthesis = synthesis_data

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return ModuleOutput(
            module_id="synthesis",
            status=ModuleStatus.COMPLETED,
            data=synthesis_data,
            evidence=evidence,
            execution_time_ms=execution_time
        )

    except Exception as e:
        return ModuleOutput(
            module_id="synthesis",
            status=ModuleStatus.FAILED,
            data={"error": str(e)},
            evidence=[],
            execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            error=str(e)
        )


# ==============================================================================
# MODULE 5: REPORT GENERATION
# ==============================================================================

async def generate_assessment_report(state: AssessmentState) -> str:
    """
    Module 5: Report Generation

    Produces comprehensive assessment report with full evidence attribution.
    """
    state.current_module = "report_generation"

    # Gather all data
    graph_data = state.module_outputs.get("graph_analysis", ModuleOutput(
        module_id="", status="", data={}, evidence=[], execution_time_ms=0
    )).data
    pattern_data = state.module_outputs.get("pattern_discovery", ModuleOutput(
        module_id="", status="", data={}, evidence=[], execution_time_ms=0
    )).data
    validation_data = state.module_outputs.get("external_validation", ModuleOutput(
        module_id="", status="", data={}, evidence=[], execution_time_ms=0
    )).data
    synthesis = state.synthesis

    # Build report
    report = f"""# 🎯 Innovation Assessment: {state.project_name}

**Assessment Engine**: v{state.version} | **Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Domain**: {state.project_domain} | **Evidence Items**: {len(state.evidence_trail)}

---

## 📊 EXECUTIVE SUMMARY

{synthesis.get('overall_assessment', 'Assessment synthesis pending.')}

**Key Themes:**
{chr(10).join(['- ' + t for t in synthesis.get('key_themes', ['No themes identified'])])}

---

## 📈 KNOWLEDGE GRAPH ANALYSIS

### Frameworks Identified
| Framework | Domain | Relevance |
|-----------|--------|-----------|
"""

    for fw in graph_data.get("frameworks", [])[:8]:
        report += f"| {fw.get('name', 'Unknown')} | {fw.get('domain', '-')} | {fw.get('score', '-')} |\n"

    report += f"""
### Differential Insights
"""
    for da in graph_data.get("differentials", [])[:5]:
        report += f"- {da.get('insight', 'No insight')[:150]}\n"

    if graph_data.get("coverage_gaps"):
        report += f"""
### Coverage Gaps
*Frameworks not explicitly referenced:* {', '.join(graph_data.get('coverage_gaps', []))}
"""

    report += f"""
---

## 🔍 PATTERN DISCOVERY

### Cross-Domain Patterns Found: {len(pattern_data.get('patterns', []))}
"""
    for p in pattern_data.get("patterns", [])[:5]:
        report += f"- **{p.get('keyword', '')}**: {p.get('content', '')[:120]}...\n"

    if pattern_data.get("cross_domain_insights"):
        report += "\n### Cross-Domain Applications\n"
        for insight in pattern_data.get("cross_domain_insights", [])[:3]:
            report += f"- **{insight.get('framework', '')}**: {insight.get('insight', '')[:100]}...\n"

    report += f"""
---

## ✅ EXTERNAL VALIDATION

### Confirmed Insights ({len(validation_data.get('confirmed_insights', []))})
"""
    for conf in validation_data.get("confirmed_insights", [])[:5]:
        report += f"- ✅ **{conf.get('claim', '')[:80]}**\n"
        for src in conf.get("sources", [])[:2]:
            report += f"  - [{src.get('title', 'Source')[:40]}]({src.get('url', '#')})\n"

    if validation_data.get("challenged_insights"):
        report += f"""
### Challenged Insights ({len(validation_data.get('challenged_insights', []))})
"""
        for chal in validation_data.get("challenged_insights", [])[:3]:
            report += f"- ⚠️ **{chal.get('claim', '')[:80]}**\n"

    if validation_data.get("market_research"):
        report += "\n### Market Research\n"
        for mkt in validation_data.get("market_research", [])[:3]:
            report += f"- {mkt.get('insight', '')[:150]}\n"

    report += f"""
---

## 🧠 COGNITIVE ASSESSMENT

| Mode | Current | Target | Analysis |
|------|---------|--------|----------|
| Operational | {synthesis.get('cognitive_balance', {}).get('operational_pct', 50)}% | 40% | {synthesis.get('cognitive_balance', {}).get('assessment', '-')[:50]} |
| Breakthrough | {synthesis.get('cognitive_balance', {}).get('breakthrough_pct', 50)}% | 60% | - |

---

## ❓ STRATEGIC CHALLENGE QUESTIONS

"""
    for i, q in enumerate(synthesis.get("challenge_questions", [])[:5], 1):
        report += f"### {i}. {q.get('question', 'Question')}\n"
        report += f"*Context:* {q.get('context', 'No context')}\n\n"

    report += f"""
---

## 💡 STRATEGIC INSIGHTS

"""
    for insight in synthesis.get("strategic_insights", [])[:5]:
        priority_emoji = "🔴" if insight.get("priority") == "high" else "🟡" if insight.get("priority") == "medium" else "🟢"
        report += f"{priority_emoji} **{insight.get('insight', '')}**\n"
        for ev in insight.get("evidence", [])[:2]:
            report += f"   - *Evidence:* {ev[:80]}...\n"
        report += "\n"

    if synthesis.get("gaps_and_blindspots"):
        report += f"""
---

## ⚠️ GAPS & BLIND SPOTS

"""
        for gap in synthesis.get("gaps_and_blindspots", []):
            report += f"- {gap}\n"

    report += f"""
---

## 📋 EVIDENCE TRAIL

**Total Evidence Items:** {len(state.evidence_trail)}

| Source | Count |
|--------|-------|
| Neo4j | {len([e for e in state.evidence_trail if e.source_type == 'neo4j'])} |
| FileSearch | {len([e for e in state.evidence_trail if e.source_type == 'filesearch'])} |
| Tavily | {len([e for e in state.evidence_trail if e.source_type == 'tavily'])} |
| Gemini | {len([e for e in state.evidence_trail if e.source_type == 'gemini'])} |

---

*Assessment ID: {state.session_id}*
*Modules Completed: {', '.join(state.modules_completed)}*
"""

    return report


# ==============================================================================
# MAIN ORCHESTRATION
# ==============================================================================

async def run_full_assessment(
    content: str,
    project_name: str = "Innovation Project",
    project_domain: str = "",
    student_id: str = ""
) -> Tuple[str, AssessmentState]:
    """
    Run complete innovation assessment through all modules.

    Returns: (report_string, assessment_state)
    """
    # Initialize state
    state = create_assessment_session(
        project_name=project_name,
        project_domain=project_domain or extract_domain(content),
        project_description=content[:500],
        student_id=student_id
    )

    # Module 1: Graph Analysis
    graph_result = await run_graph_analysis(state, content)
    state.module_outputs["graph_analysis"] = graph_result
    state.modules_completed.append("graph_analysis")
    state.checkpoint()

    # Module 2: Pattern Discovery
    pattern_result = await run_pattern_discovery(
        state, content,
        frameworks=graph_result.data.get("frameworks", [])
    )
    state.module_outputs["pattern_discovery"] = pattern_result
    state.modules_completed.append("pattern_discovery")
    state.checkpoint()

    # Module 3: External Validation
    validation_result = await run_external_validation(state, content)
    state.module_outputs["external_validation"] = validation_result
    state.modules_completed.append("external_validation")
    state.checkpoint()

    # Module 4: Synthesis
    synthesis_result = await run_synthesis(state)
    state.module_outputs["synthesis"] = synthesis_result
    state.modules_completed.append("synthesis")

    # Module 5: Report Generation
    report = await generate_assessment_report(state)
    state.modules_completed.append("report_generation")

    return report, state


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
    """Extract key terms from content."""
    # Simple keyword extraction - in production use NLP
    import re

    # Remove common words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                  'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                  'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
                  'below', 'between', 'under', 'again', 'further', 'then', 'once', 'and',
                  'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither', 'not',
                  'only', 'own', 'same', 'than', 'too', 'very', 'just', 'also', 'now',
                  'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
                  'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all',
                  'each', 'every', 'any', 'some', 'no', 'one', 'two', 'more', 'most',
                  'other', 'such', 'their', 'our', 'your', 'my', 'his', 'her', 'its'}

    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())

    # Filter and count
    word_counts = {}
    for word in words:
        if word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    return [word for word, count in sorted_words[:max_keywords]]


def extract_domain(content: str) -> str:
    """Extract primary domain from content."""
    keywords = extract_keywords(content, 5)
    return keywords[0] if keywords else "innovation"


async def extract_claims(content: str) -> List[str]:
    """Extract key claims from content using Gemini."""
    if not GEMINI_AVAILABLE:
        # Fallback: extract sentences with claim indicators
        import re
        claim_patterns = [
            r'(?:we believe|we found|evidence shows|data indicates|research suggests|the problem is|users need|market shows)[^.]+\.',
        ]
        claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, content.lower())
            claims.extend(matches[:3])
        return claims[:5] if claims else extract_keywords(content, 5)

    try:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""Extract the 5 most important claims or assertions from this text.
Return as JSON array of strings:
["claim1", "claim2", ...]

Text:
{content[:3000]}""",
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=500
            )
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    except Exception:
        return extract_keywords(content, 5)
