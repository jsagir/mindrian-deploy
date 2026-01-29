"""
Advanced Research Orchestrator for Mindrian
=============================================

Implements a sophisticated multi-phase research workflow that combines:
- Tavily search best practices (query decomposition, parameter optimization)
- GraphRAG context enrichment (frameworks, concepts, problem types)
- LangExtract structured insight extraction
- Result synthesis with relevance scoring

The 5-Phase Research Workflow:
1. DISCOVERY - Map the landscape with broad queries
2. SOURCE EVALUATION - Categorize and prioritize sources
3. DEEP EXTRACTION - Get full content from promising sources
4. GAP ANALYSIS - Identify missing information
5. SYNTHESIS - Assemble findings into coherent insights

Usage:
    from tools.research_orchestrator import run_research_workflow, quick_research

    # Full workflow for complex questions
    result = await run_research_workflow(
        question="What funding options exist for AI startups in Israel?",
        user_context="I'm exploring government grants for my early-stage AI company",
        bot_id="lawrence",
        depth="deep"  # or "quick", "standard"
    )

    # Quick research for simple questions
    result = await quick_research(
        question="Tesla market cap 2025",
        bot_id="lawrence"
    )
"""

import os
import json
import logging
import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("research_orchestrator")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AtomicQuery:
    """A single, focused search query."""
    query: str
    purpose: str  # landscape, specific, alternatives, recent, comparison
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class SourceEvaluation:
    """Evaluation of a search result source."""
    url: str
    title: str
    category: str  # primary, secondary, weak
    authority_score: float  # 0.0-1.0
    recency_score: float  # 0.0-1.0
    relevance_score: float  # 0.0-1.0
    extract_priority: int  # 1=must extract, 2=maybe, 3=skip
    content_snippet: str = ""


@dataclass
class ResearchFinding:
    """A verified research finding."""
    fact: str
    sources: List[str]  # URLs that confirm this
    confidence: str  # high, medium, low
    category: str  # fact, context, analysis, recommendation
    pws_relevance: str = ""  # How it relates to PWS methodology


@dataclass
class ResearchReport:
    """Complete research report."""
    question: str
    queries_executed: int
    sources_evaluated: int
    findings: List[ResearchFinding]
    evidence_gaps: List[str]
    synthesis: str
    pws_implications: str
    recommended_actions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Query Decomposition (Phase 1 Prep)
# ============================================================================

QUERY_DECOMPOSITION_PROMPT = """Decompose this research question into 3-5 atomic, keyword-focused search queries.

**Research Question:** {question}

**User Context:** {user_context}

**PWS Context (from knowledge graph):** {pws_context}

Rules for query formulation:
1. Think like a search engine - use keywords, not natural questions
2. Each query should focus on ONE concept
3. Include temporal markers (2024, 2025) for recent information
4. Use entity + attribute pattern for specific facts

Return JSON:
```json
{{
    "queries": [
        {{"query": "keyword query here", "purpose": "landscape|specific|alternatives|recent|comparison", "priority": 1}},
        ...
    ],
    "key_entities": ["entity1", "entity2"],
    "research_type": "factual|exploratory|analytical|news"
}}
```
"""


async def decompose_query(
    question: str,
    user_context: str = "",
    bot_id: str = "lawrence",
) -> List[AtomicQuery]:
    """
    Decompose a complex question into atomic, searchable queries.
    Uses GraphRAG to enrich with PWS context.
    """
    # Get PWS context from GraphRAG
    pws_context = await _get_pws_context(question)

    # Use Gemini to decompose
    from google import genai

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = QUERY_DECOMPOSITION_PROMPT.format(
        question=question,
        user_context=user_context[:500],
        pws_context=pws_context,
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.3, "max_output_tokens": 1000}
        )

        result = _parse_json_response(response.text)

        if result and result.get("queries"):
            queries = []
            for q in result["queries"]:
                queries.append(AtomicQuery(
                    query=q["query"],
                    purpose=q.get("purpose", "landscape"),
                    priority=q.get("priority", 2),
                    params=_get_params_for_purpose(q.get("purpose", "landscape"))
                ))
            return queries
    except Exception as e:
        logger.error("Query decomposition failed: %s", e)

    # Fallback: simple keyword extraction
    return [
        AtomicQuery(query=question, purpose="landscape", priority=1),
        AtomicQuery(query=f"{question} 2024 2025", purpose="recent", priority=2),
    ]


async def _get_pws_context(question: str) -> str:
    """Get PWS-relevant context from GraphRAG."""
    try:
        from tools.graphrag_lite import (
            get_related_frameworks,
            get_problem_context,
            lazy_concept_lookup,
        )

        parts = []

        # Get relevant frameworks
        frameworks = get_related_frameworks(question, limit=3)
        if frameworks:
            fw_names = [f["name"] for f in frameworks]
            parts.append(f"Relevant PWS frameworks: {', '.join(fw_names)}")

        # Get problem context
        problem = get_problem_context(question)
        if problem.get("problem_type"):
            parts.append(f"Problem type: {problem['problem_type']}")
        if problem.get("approaches"):
            parts.append(f"Suggested approaches: {', '.join(problem['approaches'][:3])}")

        # Get related concepts
        concepts = lazy_concept_lookup(question, limit=5)
        if concepts:
            concept_names = [c["name"] for c in concepts]
            parts.append(f"Related concepts: {', '.join(concept_names)}")

        return " | ".join(parts) if parts else "General research query"

    except Exception as e:
        logger.warning("GraphRAG context failed: %s", e)
        return "General research query"


def _get_params_for_purpose(purpose: str) -> Dict[str, Any]:
    """Get optimal Tavily parameters for query purpose."""
    params = {
        "landscape": {
            "search_depth": "basic",
            "max_results": 10,
        },
        "specific": {
            "search_depth": "advanced",
            "max_results": 8,
        },
        "alternatives": {
            "search_depth": "basic",
            "max_results": 8,
        },
        "recent": {
            "search_depth": "advanced",
            "max_results": 10,
            "topic": "news",
        },
        "comparison": {
            "search_depth": "advanced",
            "max_results": 10,
        },
    }
    return params.get(purpose, params["landscape"])


# ============================================================================
# Discovery Search (Phase 1)
# ============================================================================

async def discovery_search(queries: List[AtomicQuery]) -> List[Dict]:
    """
    Execute discovery searches to map the research landscape.
    """
    from tools.tavily_search import search_web

    results = []

    # Sort by priority
    sorted_queries = sorted(queries, key=lambda q: q.priority)

    for query in sorted_queries[:5]:  # Max 5 discovery queries
        try:
            result = search_web(
                query=query.query,
                search_depth=query.params.get("search_depth", "basic"),
                max_results=query.params.get("max_results", 8),
            )

            results.append({
                "query": query.query,
                "purpose": query.purpose,
                "results": result.get("results", []),
                "answer": result.get("answer", ""),
            })

            logger.info("Discovery: '%s' → %d results", query.query[:50], len(result.get("results", [])))

        except Exception as e:
            logger.error("Discovery search failed for '%s': %s", query.query[:50], e)

    return results


# ============================================================================
# Source Evaluation (Phase 2)
# ============================================================================

# Domain authority scores
AUTHORITY_DOMAINS = {
    # Government/Official (0.95-1.0)
    "gov": 0.98, "gov.il": 0.98, "gov.uk": 0.98, "europa.eu": 0.97,
    "fda.gov": 0.99, "sec.gov": 0.99, "nih.gov": 0.98,

    # Academic/Research (0.85-0.95)
    "edu": 0.90, "ac.il": 0.90, "ac.uk": 0.90,
    "pubmed": 0.95, "arxiv.org": 0.92, "nature.com": 0.93,
    "sciencedirect": 0.92, "springer": 0.91,

    # Business/Finance (0.75-0.85)
    "bloomberg": 0.85, "reuters": 0.85, "wsj.com": 0.82,
    "techcrunch": 0.78, "crunchbase": 0.80, "pitchbook": 0.82,

    # News (0.65-0.75)
    "nytimes": 0.75, "bbc": 0.75, "theguardian": 0.73,
    "cnn": 0.70, "forbes": 0.68,

    # Tech/Industry (0.60-0.70)
    "medium.com": 0.55, "substack": 0.58,
    "hackernews": 0.60, "venturebeat": 0.65,

    # Low Authority (0.30-0.50)
    "reddit": 0.40, "quora": 0.35, "wikipedia": 0.50,
}


def evaluate_sources(discovery_results: List[Dict]) -> List[SourceEvaluation]:
    """
    Evaluate and categorize sources from discovery results.
    """
    evaluations = []
    seen_urls = set()

    for disc_result in discovery_results:
        for result in disc_result.get("results", []):
            url = result.get("url", "")

            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Calculate authority score
            authority = _calculate_authority(url)

            # Calculate recency score
            recency = _calculate_recency(result)

            # Calculate relevance score (from Tavily score if available)
            relevance = result.get("score", 0.5)

            # Determine category
            if authority >= 0.85:
                category = "primary"
            elif authority >= 0.60:
                category = "secondary"
            else:
                category = "weak"

            # Determine extraction priority
            combined_score = (authority * 0.4) + (relevance * 0.4) + (recency * 0.2)
            if combined_score >= 0.7:
                extract_priority = 1
            elif combined_score >= 0.5:
                extract_priority = 2
            else:
                extract_priority = 3

            evaluations.append(SourceEvaluation(
                url=url,
                title=result.get("title", ""),
                category=category,
                authority_score=authority,
                recency_score=recency,
                relevance_score=relevance,
                extract_priority=extract_priority,
                content_snippet=result.get("content", "")[:300],
            ))

    # Sort by extract priority
    evaluations.sort(key=lambda e: (e.extract_priority, -e.authority_score))

    return evaluations


def _calculate_authority(url: str) -> float:
    """Calculate authority score based on domain."""
    url_lower = url.lower()

    for domain, score in AUTHORITY_DOMAINS.items():
        if domain in url_lower:
            return score

    # Default score based on TLD
    if ".gov" in url_lower:
        return 0.90
    elif ".edu" in url_lower or ".ac." in url_lower:
        return 0.85
    elif ".org" in url_lower:
        return 0.60

    return 0.50  # Default


def _calculate_recency(result: Dict) -> float:
    """Calculate recency score based on publication date."""
    # Check for date in result
    pub_date = result.get("published_date") or result.get("date")

    if not pub_date:
        return 0.5  # Unknown date

    try:
        # Parse date and calculate age
        if isinstance(pub_date, str):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%B %d, %Y"]:
                try:
                    dt = datetime.strptime(pub_date[:19], fmt)
                    break
                except ValueError:
                    continue
            else:
                return 0.5

        age_days = (datetime.now() - dt).days

        if age_days <= 30:
            return 1.0
        elif age_days <= 90:
            return 0.9
        elif age_days <= 180:
            return 0.8
        elif age_days <= 365:
            return 0.6
        else:
            return 0.4

    except Exception:
        return 0.5


# ============================================================================
# Deep Extraction (Phase 3)
# ============================================================================

async def deep_extract(
    sources: List[SourceEvaluation],
    max_extractions: int = 5,
) -> List[Dict]:
    """
    Extract full content from high-priority sources.
    """
    from tools.tavily_search import get_search_context

    extractions = []

    # Get top priority sources
    priority_sources = [s for s in sources if s.extract_priority <= 2][:max_extractions]

    for source in priority_sources:
        try:
            # Use Tavily to get content
            context = get_search_context(
                query=f"site:{source.url}",
                max_results=1,
                max_tokens=3000,
            )

            extractions.append({
                "url": source.url,
                "title": source.title,
                "category": source.category,
                "authority": source.authority_score,
                "content": context if isinstance(context, str) else str(context),
            })

            logger.info("Extracted: %s (authority: %.2f)", source.url[:50], source.authority_score)

        except Exception as e:
            logger.warning("Extraction failed for %s: %s", source.url[:50], e)

    return extractions


# ============================================================================
# Gap Analysis (Phase 4)
# ============================================================================

GAP_ANALYSIS_PROMPT = """Analyze these research findings and identify what's still missing.

**Original Question:** {question}

**Findings So Far:**
{findings_summary}

**Source Categories:**
- Primary (authoritative): {primary_count}
- Secondary (news/analysis): {secondary_count}
- Weak (forums/blogs): {weak_count}

Identify:
1. Missing critical information
2. Conflicting facts that need clarification
3. Topics that need deeper research
4. Recent updates that might exist

Return JSON:
```json
{{
    "gaps": [
        {{"topic": "what's missing", "importance": "critical|important|nice_to_have", "suggested_query": "search query to fill gap"}}
    ],
    "conflicts": [
        {{"fact": "conflicting info", "clarification_query": "search to resolve"}}
    ],
    "confidence_assessment": "high|medium|low",
    "reason": "why this confidence level"
}}
```
"""


async def analyze_gaps(
    question: str,
    sources: List[SourceEvaluation],
    extractions: List[Dict],
) -> Tuple[List[Dict], List[AtomicQuery]]:
    """
    Analyze gaps in research and generate follow-up queries.
    """
    from google import genai

    # Summarize findings
    findings_summary = []
    for ext in extractions[:5]:
        findings_summary.append(f"- {ext['title']}: {ext['content'][:200]}...")

    # Count by category
    primary_count = len([s for s in sources if s.category == "primary"])
    secondary_count = len([s for s in sources if s.category == "secondary"])
    weak_count = len([s for s in sources if s.category == "weak"])

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = GAP_ANALYSIS_PROMPT.format(
        question=question,
        findings_summary="\n".join(findings_summary) if findings_summary else "Limited findings so far",
        primary_count=primary_count,
        secondary_count=secondary_count,
        weak_count=weak_count,
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.3, "max_output_tokens": 1000}
        )

        result = _parse_json_response(response.text)

        if result:
            gaps = result.get("gaps", [])
            conflicts = result.get("conflicts", [])

            # Generate follow-up queries
            follow_up_queries = []

            for gap in gaps:
                if gap.get("importance") in ["critical", "important"]:
                    follow_up_queries.append(AtomicQuery(
                        query=gap.get("suggested_query", gap["topic"]),
                        purpose="specific",
                        priority=1 if gap["importance"] == "critical" else 2,
                    ))

            for conflict in conflicts:
                follow_up_queries.append(AtomicQuery(
                    query=conflict.get("clarification_query", conflict["fact"]),
                    purpose="specific",
                    priority=1,
                ))

            return gaps, follow_up_queries

    except Exception as e:
        logger.error("Gap analysis failed: %s", e)

    return [], []


# ============================================================================
# Synthesis with LangExtract (Phase 5)
# ============================================================================

async def synthesize_findings(
    question: str,
    user_context: str,
    sources: List[SourceEvaluation],
    extractions: List[Dict],
    gaps: List[Dict],
    bot_id: str = "lawrence",
) -> ResearchReport:
    """
    Synthesize all findings into a coherent research report.
    Uses LangExtract to structure insights.
    """
    # Extract structured insights using LangExtract
    structured_insights = await _extract_structured_insights(extractions)

    # Build findings with triangulation
    findings = _triangulate_findings(extractions, sources)

    # Generate synthesis using Gemini
    synthesis, pws_implications, actions = await _generate_synthesis(
        question, findings, gaps, structured_insights, bot_id
    )

    # Compile report
    return ResearchReport(
        question=question,
        queries_executed=len(sources),
        sources_evaluated=len(sources),
        findings=findings,
        evidence_gaps=[g.get("topic", "") for g in gaps if g.get("importance") == "critical"],
        synthesis=synthesis,
        pws_implications=pws_implications,
        recommended_actions=actions,
        metadata={
            "primary_sources": len([s for s in sources if s.category == "primary"]),
            "secondary_sources": len([s for s in sources if s.category == "secondary"]),
            "structured_insights": structured_insights,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


async def _extract_structured_insights(extractions: List[Dict]) -> Dict:
    """Use LangExtract to extract structured data from research."""
    try:
        from tools.langextract import instant_extract

        # Combine all extracted content
        combined_text = "\n\n".join([
            f"Source: {e['title']}\n{e['content']}"
            for e in extractions
        ])

        # Extract signals
        signals = instant_extract(combined_text)

        return {
            "statistics": signals.get("statistics", []),
            "assumptions": signals.get("assumptions", []),
            "questions": signals.get("questions", []),
            "key_entities": signals.get("entities", []),
        }

    except Exception as e:
        logger.warning("LangExtract failed: %s", e)
        return {}


def _triangulate_findings(
    extractions: List[Dict],
    sources: List[SourceEvaluation],
) -> List[ResearchFinding]:
    """
    Triangulate findings across sources to verify facts.
    """
    findings = []

    # Group content by themes (simplified - in production use NLP)
    for ext in extractions:
        # Create finding from each primary/secondary source
        source_eval = next(
            (s for s in sources if s.url == ext["url"]),
            None
        )

        if not source_eval:
            continue

        # Determine confidence based on authority
        if source_eval.authority_score >= 0.85:
            confidence = "high"
        elif source_eval.authority_score >= 0.60:
            confidence = "medium"
        else:
            confidence = "low"

        findings.append(ResearchFinding(
            fact=ext["content"][:500] if ext["content"] else ext["title"],
            sources=[ext["url"]],
            confidence=confidence,
            category="fact" if source_eval.category == "primary" else "context",
        ))

    return findings[:10]  # Top 10 findings


async def _generate_synthesis(
    question: str,
    findings: List[ResearchFinding],
    gaps: List[Dict],
    insights: Dict,
    bot_id: str,
) -> Tuple[str, str, List[str]]:
    """Generate final synthesis using Gemini."""
    from google import genai

    # Format findings for prompt
    findings_text = "\n".join([
        f"- [{f.confidence}] {f.fact[:200]}... (source: {f.sources[0][:50]})"
        for f in findings[:8]
    ])

    insights_text = ""
    if insights.get("statistics"):
        insights_text += f"\nStatistics found: {', '.join(insights['statistics'][:5])}"
    if insights.get("assumptions"):
        insights_text += f"\nAssumptions identified: {', '.join(insights['assumptions'][:3])}"

    gaps_text = "\n".join([f"- {g.get('topic', '')}" for g in gaps[:5]])

    prompt = f"""Synthesize this research into actionable insights for PWS methodology.

**Question:** {question}

**Key Findings:**
{findings_text}

**Extracted Insights:**
{insights_text}

**Information Gaps:**
{gaps_text}

Provide:
1. **Synthesis** (3-4 sentences): What does this research tell us?
2. **PWS Implications**: How does this affect problem validation?
3. **Recommended Actions** (3 specific next steps)

Format as JSON:
```json
{{
    "synthesis": "...",
    "pws_implications": "...",
    "recommended_actions": ["action1", "action2", "action3"]
}}
```
"""

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.4, "max_output_tokens": 1500}
        )

        result = _parse_json_response(response.text)

        if result:
            return (
                result.get("synthesis", ""),
                result.get("pws_implications", ""),
                result.get("recommended_actions", []),
            )
    except Exception as e:
        logger.error("Synthesis generation failed: %s", e)

    return ("Research synthesis unavailable.", "", [])


# ============================================================================
# Main Orchestration Functions
# ============================================================================

async def run_research_workflow(
    question: str,
    user_context: str = "",
    bot_id: str = "lawrence",
    depth: str = "standard",  # quick, standard, deep
) -> ResearchReport:
    """
    Execute the full 5-phase research workflow.

    Args:
        question: The research question
        user_context: Additional context about what user is working on
        bot_id: Current bot for PWS framing
        depth: Research depth (quick=2 queries, standard=5, deep=8+)

    Returns:
        Complete ResearchReport with findings, synthesis, and recommendations
    """
    logger.info("Starting research workflow: '%s' (depth=%s)", question[:50], depth)

    # Phase 1: Query Decomposition
    queries = await decompose_query(question, user_context, bot_id)

    # Limit queries based on depth
    max_queries = {"quick": 2, "standard": 5, "deep": 8}.get(depth, 5)
    queries = queries[:max_queries]

    # Phase 1: Discovery Search
    discovery_results = await discovery_search(queries)

    # Phase 2: Source Evaluation
    sources = evaluate_sources(discovery_results)

    # Phase 3: Deep Extraction
    max_extractions = {"quick": 2, "standard": 4, "deep": 6}.get(depth, 4)
    extractions = await deep_extract(sources, max_extractions)

    # Phase 4: Gap Analysis (skip for quick)
    gaps = []
    if depth != "quick":
        gaps, follow_up_queries = await analyze_gaps(question, sources, extractions)

        # Execute follow-up queries for deep research
        if depth == "deep" and follow_up_queries:
            follow_up_results = await discovery_search(follow_up_queries[:3])
            follow_up_sources = evaluate_sources(follow_up_results)
            sources.extend(follow_up_sources)

            follow_up_extractions = await deep_extract(follow_up_sources, 2)
            extractions.extend(follow_up_extractions)

    # Phase 5: Synthesis
    report = await synthesize_findings(
        question, user_context, sources, extractions, gaps, bot_id
    )

    logger.info(
        "Research complete: %d queries, %d sources, %d findings",
        len(queries), len(sources), len(report.findings)
    )

    return report


async def quick_research(
    question: str,
    bot_id: str = "lawrence",
) -> Dict:
    """
    Quick research for simple factual questions.
    Single query, minimal processing.
    """
    from tools.tavily_search import search_web, qna_search

    # Try Q&A first for direct answers
    qna_result = qna_search(question)

    if qna_result.get("answer"):
        return {
            "answer": qna_result["answer"],
            "type": "direct_answer",
            "confidence": "medium",
        }

    # Fall back to search
    search_result = search_web(
        query=question,
        search_depth="basic",
        max_results=5,
    )

    # Quick synthesis
    from tools.result_synthesizer import quick_synthesize

    synthesis = await quick_synthesize(
        raw_results=search_result,
        source_type="web",
        question=question,
    )

    return {
        "synthesis": synthesis,
        "type": "search_synthesis",
        "sources": len(search_result.get("results", [])),
    }


# ============================================================================
# Formatting Functions
# ============================================================================

def format_research_report(report: ResearchReport) -> str:
    """Format a research report as markdown for display."""
    parts = [f"## Research: {report.question}\n"]

    # Metadata
    parts.append(f"*{report.queries_executed} queries | {report.sources_evaluated} sources evaluated*\n")

    # Synthesis
    if report.synthesis:
        parts.append(f"### Summary\n{report.synthesis}\n")

    # Key Findings
    if report.findings:
        parts.append("### Key Findings\n")
        for i, finding in enumerate(report.findings[:5], 1):
            confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🟠"}.get(finding.confidence, "⚪")
            parts.append(f"{i}. {confidence_icon} {finding.fact[:200]}...")
            if finding.sources:
                parts.append(f"   *Source: {finding.sources[0][:50]}...*")
        parts.append("")

    # PWS Implications
    if report.pws_implications:
        parts.append(f"### PWS Implications\n{report.pws_implications}\n")

    # Recommended Actions
    if report.recommended_actions:
        parts.append("### Recommended Next Steps")
        for action in report.recommended_actions[:3]:
            parts.append(f"- {action}")
        parts.append("")

    # Evidence Gaps
    if report.evidence_gaps:
        parts.append("### Questions to Explore")
        for gap in report.evidence_gaps[:3]:
            parts.append(f"- {gap}")

    return "\n".join(parts)


# ============================================================================
# Utility Functions
# ============================================================================

def _parse_json_response(text: str) -> Optional[Dict]:
    """Parse JSON from model response."""
    # Look for JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try parsing whole text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try finding {...}
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return None
