"""
Validation Workflow Orchestrator
================================

Agentic, stateful workflow for Multi-Perspective Validation.
Executes all 6 phases automatically without user intervention.

Based on:
- BONO Domain-to-Decision Workflow specification
- de Bono's Six Thinking Hats
- IBM/ABB parallel thinking case studies

This module EXECUTES the workflow - it does not describe or wait for clicks.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

import chainlit as cl
from google import genai
from google.genai import types

# Initialize Gemini client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

logger = logging.getLogger("validation_workflow")

# =============================================================================
# STATE DATACLASSES
# =============================================================================

@dataclass
class DomainResolution:
    """Phase 0 output: Domain, sub-domain, and context resolution."""
    primary_domain: str = ""
    sub_domain: str = ""
    context_of_use: Dict = field(default_factory=dict)
    explicit_assumptions: List[str] = field(default_factory=list)
    remaining_ambiguities: List[str] = field(default_factory=list)
    raw_input: str = ""


@dataclass
class DomainExtraction:
    """Phase 1 output: Full domain characteristics."""
    challenge_summary: str = ""
    challenge_type: str = ""
    industry_domain: str = ""
    technical_domain: str = ""
    stakeholder_groups: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)
    adjacent_domains: List[str] = field(default_factory=list)
    validation_focus: str = ""


@dataclass
class Persona:
    """A single Six Thinking Hat persona."""
    hat: str = ""  # white, red, black, yellow, green, blue
    hat_emoji: str = ""
    name: str = ""  # Domain-specific expertise name
    expertise: str = ""
    mandate: str = ""
    research_focus: str = ""
    key_questions: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)


@dataclass
class HatResearch:
    """Research findings for a single hat."""
    hat: str = ""
    hat_emoji: str = ""
    persona_name: str = ""
    data_gathered: List[Dict] = field(default_factory=list)
    evidence_summary: str = ""
    information_gaps: List[str] = field(default_factory=list)
    confidence_level: str = ""  # High, Medium, Low
    raw_sources: List[Dict] = field(default_factory=list)


@dataclass
class DebateResults:
    """Phase 4 output: Structured debate findings."""
    evidence_challenges: List[Dict] = field(default_factory=list)
    assumption_challenges: List[Dict] = field(default_factory=list)
    key_tensions: List[Dict] = field(default_factory=list)
    convergence_points: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Phase 5 output: Final validation verdict."""
    executive_summary: str = ""
    evidence_overview: Dict[str, Dict] = field(default_factory=dict)
    key_tensions: List[Dict] = field(default_factory=list)
    trade_offs: List[Dict] = field(default_factory=list)
    verdict: str = ""  # VALIDATED, VALIDATED WITH CONDITIONS, NEEDS MORE INVESTIGATION, NOT RECOMMENDED
    verdict_rationale: str = ""
    confidence_level: str = ""
    action_plan: List[Dict] = field(default_factory=list)
    critical_success_factors: List[str] = field(default_factory=list)
    risks_to_monitor: List[Dict] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)


@dataclass
class ValidationState:
    """Complete workflow state - accumulated across all phases."""
    user_input: str = ""
    domain_resolution: Optional[DomainResolution] = None
    domain_extraction: Optional[DomainExtraction] = None
    personas: List[Persona] = field(default_factory=list)
    research_by_hat: Dict[str, HatResearch] = field(default_factory=dict)
    debate_results: Optional[DebateResults] = None
    validation_report: Optional[ValidationReport] = None
    current_phase: int = 0
    errors: List[str] = field(default_factory=list)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_json_response(text: str) -> Dict:
    """Parse JSON from LLM response, handling markdown wrapping."""
    import re
    text = text.strip()

    # Remove markdown code blocks
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\n?', '', text)
        text = re.sub(r'\n?```$', '', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.error(f"Raw text: {text[:500]}")
        return {}


async def call_gemini(prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
    """Make a Gemini API call and return the text response."""
    if not client:
        return '{"error": "Gemini client not initialized"}'

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f'{{"error": "{str(e)}"}}'


async def search_tavily(query: str, max_results: int = 5) -> List[Dict]:
    """Execute a Tavily search and return results."""
    try:
        from tools.tavily_search import search_web
        result = search_web(query, search_depth="basic", max_results=max_results)
        return result.get("results", [])
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return []


# =============================================================================
# PHASE 0: DOMAIN, SUB-DOMAIN, AND CONTEXT RESOLUTION
# =============================================================================

PHASE_0_PROMPT = """You are a domain resolution specialist. Your job is to eliminate ambiguity by explicitly defining WHERE this problem lives.

## User Input
{user_input}

## Your Task
Analyze the input and produce a structured resolution. Return ONLY valid JSON:

```json
{{
  "primary_domain": "The broad problem universe (e.g., cybersecurity, healthcare, fintech)",
  "sub_domain": "The specific technical/market slice (e.g., quantum cryptography, medical imaging, payment processing)",
  "context_of_use": {{
    "target_users": "Who will use/buy this",
    "environment": "enterprise | consumer | regulated | emerging",
    "time_horizon": "current | near-term (1-2 years) | future (3+ years)",
    "maturity_stage": "research | pilot | early-market | scaling"
  }},
  "explicit_assumptions": [
    "Assumption 1 we're making based on the input",
    "Assumption 2 we're making"
  ],
  "remaining_ambiguities": [
    "What's still unclear that might affect validation"
  ]
}}
```

Be precise. This resolution drives the entire validation workflow."""


async def phase_0_domain_resolution(user_input: str) -> DomainResolution:
    """
    PHASE 0: Domain, Sub-Domain, and Context Resolution
    FOUNDATIONAL - Required before any persona construction.
    """
    async with cl.Step(name="Phase 0: Domain Resolution", type="llm") as step:
        step.input = f"Resolving domain for: {user_input[:200]}..."

        prompt = PHASE_0_PROMPT.format(user_input=user_input)
        response = await call_gemini(prompt, temperature=0.2)
        data = parse_json_response(response)

        if not data or "error" in data:
            step.output = "Failed to resolve domain"
            return DomainResolution(raw_input=user_input)

        resolution = DomainResolution(
            primary_domain=data.get("primary_domain", ""),
            sub_domain=data.get("sub_domain", ""),
            context_of_use=data.get("context_of_use", {}),
            explicit_assumptions=data.get("explicit_assumptions", []),
            remaining_ambiguities=data.get("remaining_ambiguities", []),
            raw_input=user_input,
        )

        # Show resolution to user
        output = f"""**Primary Domain:** {resolution.primary_domain}
**Sub-Domain:** {resolution.sub_domain}
**Context:** {resolution.context_of_use.get('environment', 'N/A')} / {resolution.context_of_use.get('maturity_stage', 'N/A')}
**Target Users:** {resolution.context_of_use.get('target_users', 'N/A')}
**Assumptions Made:** {len(resolution.explicit_assumptions)}"""

        step.output = output
        return resolution


# =============================================================================
# PHASE 1: DOMAIN EXTRACTION
# =============================================================================

PHASE_1_PROMPT = """You are a domain extraction specialist. Using the resolved domain context, extract detailed operational characteristics.

## Domain Resolution
Primary Domain: {primary_domain}
Sub-Domain: {sub_domain}
Context: {context}
User Input: {user_input}

## Your Task
Extract comprehensive domain characteristics. Return ONLY valid JSON:

```json
{{
  "challenge_summary": "One sentence summary of what needs to be validated",
  "challenge_type": "idea | strategy | decision | innovation | pivot | investment | partnership",
  "industry_domain": "Primary industry (e.g., healthcare, fintech, edtech, logistics)",
  "technical_domain": "Technical/engineering domain if applicable",
  "stakeholder_groups": ["List of key stakeholder groups affected"],
  "constraints": ["Known constraints: time, budget, regulatory, technical"],
  "success_criteria": ["What would make this a success?"],
  "risk_factors": ["Initial risk factors to investigate"],
  "knowledge_gaps": ["What we don't know yet that matters"],
  "adjacent_domains": ["Related domains that might offer insights"],
  "validation_focus": "What specific aspect needs the most rigorous validation?"
}}
```"""


async def phase_1_domain_extraction(resolution: DomainResolution) -> DomainExtraction:
    """
    PHASE 1: Domain Extraction
    Establishes the problem space rigorously.
    """
    async with cl.Step(name="Phase 1: Domain Extraction", type="llm") as step:
        step.input = f"Extracting domain characteristics for {resolution.sub_domain}..."

        prompt = PHASE_1_PROMPT.format(
            primary_domain=resolution.primary_domain,
            sub_domain=resolution.sub_domain,
            context=json.dumps(resolution.context_of_use),
            user_input=resolution.raw_input,
        )

        response = await call_gemini(prompt, temperature=0.2, max_tokens=2500)
        data = parse_json_response(response)

        if not data or "error" in data:
            step.output = "Failed to extract domain"
            return DomainExtraction()

        extraction = DomainExtraction(
            challenge_summary=data.get("challenge_summary", ""),
            challenge_type=data.get("challenge_type", ""),
            industry_domain=data.get("industry_domain", ""),
            technical_domain=data.get("technical_domain", ""),
            stakeholder_groups=data.get("stakeholder_groups", []),
            constraints=data.get("constraints", []),
            success_criteria=data.get("success_criteria", []),
            risk_factors=data.get("risk_factors", []),
            knowledge_gaps=data.get("knowledge_gaps", []),
            adjacent_domains=data.get("adjacent_domains", []),
            validation_focus=data.get("validation_focus", ""),
        )

        output = f"""**Challenge:** {extraction.challenge_summary}
**Type:** {extraction.challenge_type}
**Industry:** {extraction.industry_domain}
**Stakeholders:** {', '.join(extraction.stakeholder_groups[:3])}
**Validation Focus:** {extraction.validation_focus}"""

        step.output = output
        return extraction


# =============================================================================
# PHASE 2: PERSONA CONSTRUCTION
# =============================================================================

PHASE_2_PROMPT = """You are constructing domain-specific Six Thinking Hats expert personas.

## Domain Context
Industry: {industry}
Technical Domain: {technical_domain}
Challenge: {challenge_summary}
Stakeholders: {stakeholders}
Validation Focus: {validation_focus}

## Your Task
Generate exactly 6 domain-specific expert personas, one per thinking hat.
IMPORTANT: Name each persona by their EXPERTISE (e.g., "Quantum Cryptography Market Analyst"), NOT fictional personal names.

Return ONLY valid JSON:

```json
{{
  "personas": [
    {{
      "hat": "white",
      "hat_emoji": "🤍",
      "name": "Domain-Specific Data Expert Title",
      "expertise": "Specific expertise relevant to this domain",
      "mandate": "What this persona is responsible for validating",
      "research_focus": "What data/evidence this persona will seek",
      "key_questions": ["Question 1", "Question 2", "Question 3"],
      "data_sources": ["Source type 1", "Source type 2"]
    }},
    {{
      "hat": "red",
      "hat_emoji": "❤️",
      "name": "Domain-Specific Human Factors Expert Title",
      "expertise": "Stakeholder/user research expertise for this domain",
      "mandate": "Emotional and intuitive validation",
      "research_focus": "Feelings, gut reactions, user experience",
      "key_questions": ["Question 1", "Question 2", "Question 3"],
      "data_sources": ["Source type 1", "Source type 2"]
    }},
    {{
      "hat": "black",
      "hat_emoji": "🖤",
      "name": "Domain-Specific Risk Expert Title",
      "expertise": "Risk/failure analysis expertise for this domain",
      "mandate": "Identify everything that could go wrong",
      "research_focus": "Risks, failure modes, competitive threats",
      "key_questions": ["Question 1", "Question 2", "Question 3"],
      "data_sources": ["Source type 1", "Source type 2"]
    }},
    {{
      "hat": "yellow",
      "hat_emoji": "💛",
      "name": "Domain-Specific Opportunity Expert Title",
      "expertise": "Opportunity identification for this domain",
      "mandate": "Find the upside potential",
      "research_focus": "Benefits, advantages, success precedents",
      "key_questions": ["Question 1", "Question 2", "Question 3"],
      "data_sources": ["Source type 1", "Source type 2"]
    }},
    {{
      "hat": "green",
      "hat_emoji": "💚",
      "name": "Domain-Specific Innovation Expert Title",
      "expertise": "Innovation/alternatives expertise for this domain",
      "mandate": "Generate creative alternatives",
      "research_focus": "Alternative approaches, pivots, enhancements",
      "key_questions": ["Question 1", "Question 2", "Question 3"],
      "data_sources": ["Source type 1", "Source type 2"]
    }},
    {{
      "hat": "blue",
      "hat_emoji": "💙",
      "name": "Domain-Specific Systems Expert Title",
      "expertise": "Systems integration and synthesis for this domain",
      "mandate": "Orchestrate and synthesize all perspectives",
      "research_focus": "Integration, convergence, strategic coherence",
      "key_questions": ["Question 1", "Question 2", "Question 3"],
      "data_sources": ["Strategic frameworks", "Cross-domain patterns"]
    }}
  ]
}}
```"""


async def phase_2_persona_construction(extraction: DomainExtraction) -> List[Persona]:
    """
    PHASE 2: Persona Construction
    Creates domain-specific expert perspectives.
    """
    async with cl.Step(name="Phase 2: Persona Construction", type="llm") as step:
        step.input = f"Constructing 6 expert personas for {extraction.industry_domain}..."

        prompt = PHASE_2_PROMPT.format(
            industry=extraction.industry_domain,
            technical_domain=extraction.technical_domain,
            challenge_summary=extraction.challenge_summary,
            stakeholders=", ".join(extraction.stakeholder_groups),
            validation_focus=extraction.validation_focus,
        )

        response = await call_gemini(prompt, temperature=0.4, max_tokens=3000)
        data = parse_json_response(response)

        if not data or "error" in data or "personas" not in data:
            step.output = "Failed to construct personas"
            return []

        personas = []
        for p in data.get("personas", []):
            persona = Persona(
                hat=p.get("hat", ""),
                hat_emoji=p.get("hat_emoji", ""),
                name=p.get("name", ""),
                expertise=p.get("expertise", ""),
                mandate=p.get("mandate", ""),
                research_focus=p.get("research_focus", ""),
                key_questions=p.get("key_questions", []),
                data_sources=p.get("data_sources", []),
            )
            personas.append(persona)

        # Display personas
        persona_list = "\n".join([
            f"{p.hat_emoji} **{p.name}**" for p in personas
        ])
        step.output = f"Constructed 6 personas:\n{persona_list}"

        return personas


# =============================================================================
# PHASE 3: PARALLEL RESEARCH
# =============================================================================

HAT_RESEARCH_PROMPT = """You are the {hat_emoji} {hat_name} ({persona_name}) conducting validation research.

## Your Mandate
{mandate}

## Research Focus
{research_focus}

## Key Questions to Answer
{key_questions}

## Challenge Being Validated
{challenge_summary}

## Domain Context
Industry: {industry}
Stakeholders: {stakeholders}

## Research Results from Web Search
{search_results}

## Your Task
Synthesize the research into structured findings. Return ONLY valid JSON:

```json
{{
  "data_gathered": [
    {{"fact": "Specific finding", "source": "Where it came from", "confidence": "high|medium|low"}},
    {{"fact": "Another finding", "source": "Source", "confidence": "high|medium|low"}}
  ],
  "evidence_summary": "3-4 sentence synthesis of key findings",
  "information_gaps": ["What we couldn't find but need", "Another gap"],
  "confidence_level": "High|Medium|Low",
  "key_insight": "The single most important insight from this research"
}}
```"""


async def run_hat_research(
    persona: Persona,
    extraction: DomainExtraction
) -> HatResearch:
    """Run research for a single hat persona."""

    # Build search queries from persona's key questions
    queries = persona.key_questions[:3]  # Top 3 questions

    # Execute searches
    all_results = []
    for query in queries:
        # Add domain context to query
        enriched_query = f"{extraction.industry_domain} {query}"
        results = await search_tavily(enriched_query, max_results=3)
        all_results.extend(results)

    # Format search results for LLM
    search_results_text = ""
    for i, r in enumerate(all_results[:8], 1):
        title = r.get("title", "")
        content = r.get("content", "")[:300]
        url = r.get("url", "")
        search_results_text += f"{i}. [{title}]({url})\n   {content}...\n\n"

    if not search_results_text:
        search_results_text = "No search results available."

    # Call LLM to synthesize
    prompt = HAT_RESEARCH_PROMPT.format(
        hat_emoji=persona.hat_emoji,
        hat_name=persona.hat.upper() + " HAT",
        persona_name=persona.name,
        mandate=persona.mandate,
        research_focus=persona.research_focus,
        key_questions="\n".join([f"- {q}" for q in persona.key_questions]),
        challenge_summary=extraction.challenge_summary,
        industry=extraction.industry_domain,
        stakeholders=", ".join(extraction.stakeholder_groups),
        search_results=search_results_text,
    )

    response = await call_gemini(prompt, temperature=0.3, max_tokens=1500)
    data = parse_json_response(response)

    return HatResearch(
        hat=persona.hat,
        hat_emoji=persona.hat_emoji,
        persona_name=persona.name,
        data_gathered=data.get("data_gathered", []),
        evidence_summary=data.get("evidence_summary", "No summary available"),
        information_gaps=data.get("information_gaps", []),
        confidence_level=data.get("confidence_level", "Low"),
        raw_sources=all_results,
    )


async def phase_3_parallel_research(
    personas: List[Persona],
    extraction: DomainExtraction
) -> Dict[str, HatResearch]:
    """
    PHASE 3: Parallel Research
    Each persona conducts independent research.
    """
    async with cl.Step(name="Phase 3: Parallel Research", type="tool") as parent_step:
        parent_step.input = f"Running research for 6 perspectives..."

        research_by_hat = {}

        # Run research for each hat (could be parallelized with asyncio.gather)
        for persona in personas:
            if persona.hat == "blue":
                continue  # Blue hat synthesizes, doesn't research independently

            async with cl.Step(
                name=f"{persona.hat_emoji} {persona.name}",
                type="tool"
            ) as hat_step:
                hat_step.input = f"Researching: {persona.research_focus}"

                research = await run_hat_research(persona, extraction)
                research_by_hat[persona.hat] = research

                hat_step.output = f"**{research.confidence_level} confidence**\n{research.evidence_summary[:200]}..."

        total_sources = sum(len(r.raw_sources) for r in research_by_hat.values())
        parent_step.output = f"Completed research for {len(research_by_hat)} hats | {total_sources} sources analyzed"

        return research_by_hat


# =============================================================================
# PHASE 4: STRUCTURED DEBATE
# =============================================================================

PHASE_4_PROMPT = """You are facilitating a structured debate between Six Thinking Hat experts.

## Challenge Being Validated
{challenge_summary}

## Research Findings by Hat

### 🤍 White Hat (Data & Evidence)
{white_hat_findings}

### ❤️ Red Hat (Human Factors)
{red_hat_findings}

### 🖤 Black Hat (Risks)
{black_hat_findings}

### 💛 Yellow Hat (Opportunities)
{yellow_hat_findings}

### 💚 Green Hat (Alternatives)
{green_hat_findings}

## Your Task
Facilitate 4 rounds of structured debate. Each hat must EXPLICITLY challenge others.

Return ONLY valid JSON:

```json
{{
  "round_1_evidence_challenges": [
    {{"challenger": "black", "target": "yellow", "challenge": "The opportunity data lacks...", "response": "Yellow's defense..."}},
    {{"challenger": "white", "target": "black", "challenge": "The risk assessment doesn't account for...", "response": "Black's defense..."}}
  ],
  "round_2_assumption_challenges": [
    {{"challenger": "red", "target": "white", "assumption_exposed": "White assumes stakeholder buy-in, but...", "implication": "This could mean..."}},
    {{"challenger": "green", "target": "black", "assumption_exposed": "Black assumes status quo, but...", "implication": "This opens up..."}}
  ],
  "round_3_key_tensions": [
    {{"tension": "Risk vs Opportunity", "black_position": "...", "yellow_position": "...", "resolution_attempt": "..."}},
    {{"tension": "Data vs Intuition", "white_position": "...", "red_position": "...", "resolution_attempt": "..."}}
  ],
  "round_4_convergence": {{
    "points_of_agreement": ["All hats agree that...", "Consensus on..."],
    "remaining_disagreements": ["Unresolved: whether...", "Still debated: if..."],
    "open_questions_for_user": ["Only you can answer: ...", "We need your input on: ..."]
  }}
}}
```"""


async def phase_4_structured_debate(
    research_by_hat: Dict[str, HatResearch],
    extraction: DomainExtraction
) -> DebateResults:
    """
    PHASE 4: Structured Debate
    Hats challenge each other's findings.
    """
    async with cl.Step(name="Phase 4: Structured Debate", type="llm") as step:
        step.input = "Facilitating 4-round debate between perspectives..."

        # Format research findings
        def format_findings(hat: str) -> str:
            r = research_by_hat.get(hat)
            if not r:
                return "No research available"
            return f"**Summary:** {r.evidence_summary}\n**Confidence:** {r.confidence_level}\n**Gaps:** {', '.join(r.information_gaps[:2])}"

        prompt = PHASE_4_PROMPT.format(
            challenge_summary=extraction.challenge_summary,
            white_hat_findings=format_findings("white"),
            red_hat_findings=format_findings("red"),
            black_hat_findings=format_findings("black"),
            yellow_hat_findings=format_findings("yellow"),
            green_hat_findings=format_findings("green"),
        )

        response = await call_gemini(prompt, temperature=0.5, max_tokens=3000)
        data = parse_json_response(response)

        if not data or "error" in data:
            step.output = "Debate synthesis failed"
            return DebateResults()

        # Extract debate results
        convergence = data.get("round_4_convergence", {})

        debate = DebateResults(
            evidence_challenges=data.get("round_1_evidence_challenges", []),
            assumption_challenges=data.get("round_2_assumption_challenges", []),
            key_tensions=data.get("round_3_key_tensions", []),
            convergence_points=convergence.get("points_of_agreement", []),
            open_questions=convergence.get("open_questions_for_user", []),
        )

        output = f"""**Evidence Challenges:** {len(debate.evidence_challenges)}
**Assumption Challenges:** {len(debate.assumption_challenges)}
**Key Tensions:** {len(debate.key_tensions)}
**Points of Agreement:** {len(debate.convergence_points)}
**Open Questions:** {len(debate.open_questions)}"""

        step.output = output
        return debate


# =============================================================================
# PHASE 5: VALIDATION REPORT
# =============================================================================

PHASE_5_PROMPT = """You are generating the final Multi-Perspective Validation Report.

## Challenge Validated
{challenge_summary}

## Domain Context
Industry: {industry}
Validation Focus: {validation_focus}
Stakeholders: {stakeholders}

## Research Evidence by Perspective

### 🤍 White Hat (Data & Evidence)
{white_findings}
Confidence: {white_confidence}

### ❤️ Red Hat (Human Factors)
{red_findings}
Confidence: {red_confidence}

### 🖤 Black Hat (Risks)
{black_findings}
Confidence: {black_confidence}

### 💛 Yellow Hat (Opportunities)
{yellow_findings}
Confidence: {yellow_confidence}

### 💚 Green Hat (Alternatives)
{green_findings}
Confidence: {green_confidence}

## Debate Results
**Points of Agreement:** {convergence_points}
**Key Tensions:** {tensions}
**Open Questions:** {open_questions}

## Your Task
Generate a comprehensive validation report. The verdict must be ONE of:
- VALIDATED
- VALIDATED WITH CONDITIONS
- NEEDS MORE INVESTIGATION
- NOT RECOMMENDED

Return ONLY valid JSON:

```json
{{
  "executive_summary": "2-3 paragraph summary of validation conclusion",
  "evidence_overview": {{
    "white": {{"summary": "...", "confidence": "High|Medium|Low", "key_finding": "..."}},
    "red": {{"summary": "...", "confidence": "High|Medium|Low", "key_finding": "..."}},
    "black": {{"summary": "...", "confidence": "High|Medium|Low", "key_finding": "..."}},
    "yellow": {{"summary": "...", "confidence": "High|Medium|Low", "key_finding": "..."}},
    "green": {{"summary": "...", "confidence": "High|Medium|Low", "key_finding": "..."}}
  }},
  "key_tensions": [
    {{"tension": "...", "perspective_a": "...", "perspective_b": "...", "resolution": "..."}}
  ],
  "trade_offs": [
    {{"trade_off": "...", "option_a": "...", "option_b": "...", "recommendation": "..."}}
  ],
  "verdict": "VALIDATED | VALIDATED WITH CONDITIONS | NEEDS MORE INVESTIGATION | NOT RECOMMENDED",
  "verdict_rationale": "3-4 sentences explaining why this verdict based on multi-perspective evidence",
  "confidence_level": "High|Medium|Low",
  "action_plan": [
    {{"action": "...", "rationale": "...", "timeline": "immediate|short-term|medium-term"}},
    {{"action": "...", "rationale": "...", "timeline": "..."}}
  ],
  "critical_success_factors": ["Factor 1", "Factor 2", "Factor 3"],
  "risks_to_monitor": [
    {{"risk": "...", "mitigation": "...", "owner": "..."}}
  ],
  "open_questions": ["Question 1 for user to resolve", "Question 2"]
}}
```"""


async def phase_5_validation_report(
    state: ValidationState
) -> ValidationReport:
    """
    PHASE 5: Validation Report
    Produces the final decision-quality verdict.
    """
    async with cl.Step(name="Phase 5: Validation Report", type="llm") as step:
        step.input = "Generating final validation verdict..."

        extraction = state.domain_extraction
        research = state.research_by_hat
        debate = state.debate_results

        def get_findings(hat: str) -> tuple:
            r = research.get(hat)
            if r:
                return r.evidence_summary, r.confidence_level
            return "No findings", "Low"

        white_findings, white_conf = get_findings("white")
        red_findings, red_conf = get_findings("red")
        black_findings, black_conf = get_findings("black")
        yellow_findings, yellow_conf = get_findings("yellow")
        green_findings, green_conf = get_findings("green")

        prompt = PHASE_5_PROMPT.format(
            challenge_summary=extraction.challenge_summary,
            industry=extraction.industry_domain,
            validation_focus=extraction.validation_focus,
            stakeholders=", ".join(extraction.stakeholder_groups),
            white_findings=white_findings,
            white_confidence=white_conf,
            red_findings=red_findings,
            red_confidence=red_conf,
            black_findings=black_findings,
            black_confidence=black_conf,
            yellow_findings=yellow_findings,
            yellow_confidence=yellow_conf,
            green_findings=green_findings,
            green_confidence=green_conf,
            convergence_points=", ".join(debate.convergence_points) if debate else "None",
            tensions=json.dumps(debate.key_tensions[:3]) if debate else "[]",
            open_questions=", ".join(debate.open_questions) if debate else "None",
        )

        response = await call_gemini(prompt, temperature=0.3, max_tokens=4000)
        data = parse_json_response(response)

        if not data or "error" in data:
            step.output = "Report generation failed"
            return ValidationReport()

        report = ValidationReport(
            executive_summary=data.get("executive_summary", ""),
            evidence_overview=data.get("evidence_overview", {}),
            key_tensions=data.get("key_tensions", []),
            trade_offs=data.get("trade_offs", []),
            verdict=data.get("verdict", "NEEDS MORE INVESTIGATION"),
            verdict_rationale=data.get("verdict_rationale", ""),
            confidence_level=data.get("confidence_level", "Low"),
            action_plan=data.get("action_plan", []),
            critical_success_factors=data.get("critical_success_factors", []),
            risks_to_monitor=data.get("risks_to_monitor", []),
            open_questions=data.get("open_questions", []),
        )

        step.output = f"**Verdict: {report.verdict}** ({report.confidence_level} confidence)"

        return report


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

async def run_validation_workflow(user_input: str) -> ValidationState:
    """
    MAIN ORCHESTRATOR: Runs the complete 6-phase validation workflow.

    This function is AGENTIC - it runs all phases automatically without
    waiting for user clicks or manual phase advancement.

    Args:
        user_input: The user's challenge/idea/strategy to validate

    Returns:
        ValidationState: Complete state including final verdict
    """
    state = ValidationState(user_input=user_input)

    try:
        # PHASE 0: Domain Resolution (FOUNDATIONAL)
        state.domain_resolution = await phase_0_domain_resolution(user_input)
        if not state.domain_resolution.primary_domain:
            state.errors.append("Phase 0 failed: Could not resolve domain")
            return state
        state.current_phase = 0

        # PHASE 1: Domain Extraction
        state.domain_extraction = await phase_1_domain_extraction(state.domain_resolution)
        if not state.domain_extraction.challenge_summary:
            state.errors.append("Phase 1 failed: Could not extract domain")
            return state
        state.current_phase = 1

        # PHASE 2: Persona Construction
        state.personas = await phase_2_persona_construction(state.domain_extraction)
        if len(state.personas) < 6:
            state.errors.append("Phase 2 failed: Could not construct all personas")
            return state
        state.current_phase = 2

        # PHASE 3: Parallel Research
        state.research_by_hat = await phase_3_parallel_research(
            state.personas,
            state.domain_extraction
        )
        if len(state.research_by_hat) < 4:
            state.errors.append("Phase 3 failed: Insufficient research")
            return state
        state.current_phase = 3

        # PHASE 4: Structured Debate
        state.debate_results = await phase_4_structured_debate(
            state.research_by_hat,
            state.domain_extraction
        )
        state.current_phase = 4

        # PHASE 5: Validation Report
        state.validation_report = await phase_5_validation_report(state)
        state.current_phase = 5

        return state

    except Exception as e:
        logger.error(f"Validation workflow error: {e}")
        state.errors.append(f"Workflow error: {str(e)}")
        return state


def format_validation_report(state: ValidationState) -> str:
    """Format the validation report as markdown for display."""
    report = state.validation_report
    extraction = state.domain_extraction

    if not report or not report.verdict:
        return "## Validation Failed\n\nCould not generate validation report."

    # Verdict emoji
    verdict_emoji = {
        "VALIDATED": "✅",
        "VALIDATED WITH CONDITIONS": "⚠️",
        "NEEDS MORE INVESTIGATION": "🔍",
        "NOT RECOMMENDED": "❌",
    }.get(report.verdict, "❓")

    output = f"""# {verdict_emoji} MULTI-PERSPECTIVE VALIDATION REPORT

## Challenge Validated
{extraction.challenge_summary if extraction else 'N/A'}

---

## Executive Summary
{report.executive_summary}

---

## Validation Verdict

### {verdict_emoji} {report.verdict}

**Rationale:** {report.verdict_rationale}

**Confidence Level:** {report.confidence_level}

---

## Evidence Overview

| Perspective | Confidence | Key Finding |
|-------------|------------|-------------|
"""

    for hat, data in report.evidence_overview.items():
        hat_emoji = {"white": "🤍", "red": "❤️", "black": "🖤", "yellow": "💛", "green": "💚"}.get(hat, "")
        summary = data.get("summary", "N/A")[:100]
        conf = data.get("confidence", "N/A")
        output += f"| {hat_emoji} {hat.title()} | {conf} | {summary}... |\n"

    output += "\n---\n\n## Key Tensions & Trade-offs\n\n"

    for t in report.key_tensions[:3]:
        output += f"**{t.get('tension', 'N/A')}**\n"
        output += f"- {t.get('perspective_a', 'N/A')}\n"
        output += f"- {t.get('perspective_b', 'N/A')}\n"
        output += f"- *Resolution:* {t.get('resolution', 'N/A')}\n\n"

    output += "---\n\n## Action Plan\n\n"

    for i, action in enumerate(report.action_plan[:5], 1):
        output += f"{i}. **{action.get('action', 'N/A')}**\n"
        output += f"   - Rationale: {action.get('rationale', 'N/A')}\n"
        output += f"   - Timeline: {action.get('timeline', 'N/A')}\n\n"

    output += "---\n\n## Critical Success Factors\n\n"
    for csf in report.critical_success_factors:
        output += f"- {csf}\n"

    output += "\n---\n\n## Risks to Monitor\n\n"
    for risk in report.risks_to_monitor[:5]:
        output += f"- **{risk.get('risk', 'N/A')}**: {risk.get('mitigation', 'N/A')}\n"

    if report.open_questions:
        output += "\n---\n\n## Open Questions (For You to Resolve)\n\n"
        for q in report.open_questions:
            output += f"- {q}\n"

    output += "\n---\n\n*Report generated using Multi-Perspective Validation methodology*\n"
    output += "*Based on de Bono's Six Thinking Hats + IBM/ABB parallel thinking practices*"

    return output


def is_validation_request(message: str) -> bool:
    """Detect if user message is a validation request."""
    message_lower = message.lower()

    # Must have substantive content (not just a greeting)
    if len(message) < 50:
        return False

    # Validation trigger words
    validation_triggers = [
        "validate", "evaluate", "assess", "analyze", "feasibility",
        "should we", "is this viable", "worth pursuing", "good idea",
        "investment", "decision", "strategy", "opportunity",
    ]

    # Check for triggers
    return any(trigger in message_lower for trigger in validation_triggers) or len(message) > 100
