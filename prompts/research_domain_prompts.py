"""Research Paper Domain Discovery prompts for the Domain Explorer bot."""

RESEARCH_EXTRACTION_PROMPT = """You are extracting structured information from a research document to identify innovation domain opportunities.

DOCUMENT TYPE: {detected_type}
DOCUMENT TEXT:
{document_text}

Extract the following and return ONLY valid JSON (no markdown fences):

{{
  "document_metadata": {{
    "type": "{detected_type}",
    "title": "string",
    "authors": ["string"],
    "institution": "string",
    "year": 0,
    "field": "primary discipline",
    "subfield": "specific area"
  }},
  "research_core": {{
    "research_question": "main question being addressed",
    "hypothesis": "if stated, else empty string",
    "key_contribution": "what this research adds",
    "methodology": "approach used",
    "key_findings": ["main results or conclusions"],
    "limitations_stated": ["acknowledged limitations"]
  }},
  "knowledge_landscape": {{
    "theoretical_framework": "underlying theory",
    "key_citations": [
      {{
        "author": "string",
        "concept": "what they contributed",
        "how_used": "how this paper builds on it"
      }}
    ],
    "debates_engaged": ["scholarly debates this touches"],
    "assumptions": ["implicit or explicit assumptions"]
  }},
  "frontier_indicators": {{
    "stated_gaps": ["gaps explicitly mentioned"],
    "future_work_suggested": ["what authors say should come next"],
    "unanswered_questions": ["questions raised but not answered"],
    "methodological_limitations": ["what the method couldn't capture"],
    "calls_for_research": ["explicit calls for future research"]
  }},
  "application_potential": {{
    "practical_implications": ["stated or implied applications"],
    "stakeholders_mentioned": ["who would use this"],
    "industries_relevant": ["sectors that could apply this"],
    "technology_readiness": 3,
    "commercialization_barriers": ["obstacles to application"]
  }},
  "domain_seeds": {{
    "primary_domain": "main territory of this research",
    "adjacent_domains": ["related territories touched"],
    "interdisciplinary_connections": ["fields that intersect"],
    "keywords": ["key terms and concepts"]
  }}
}}

Be thorough. Extract specific text evidence. If a field has no data, use empty string or empty list."""


RESEARCH_QUESTION_EXPANSION_PROMPT = """The user has provided a research question or topic without a full document:

"{user_input}"

Expand this into a structured research context. Identify the implied field and subfield, infer the type of research (empirical, theoretical, applied, methodological), generate likely related concepts and debates, hypothesize what gaps this question addresses, and suggest what prior work it builds on.

Return ONLY valid JSON (no markdown fences) using the same structure as a full paper extraction. Mark inferred fields with "(inferred)" prefix in their values:

{{
  "document_metadata": {{
    "type": "research_question",
    "title": "(inferred) the research question restated",
    "authors": [],
    "institution": "",
    "year": 0,
    "field": "(inferred) primary discipline",
    "subfield": "(inferred) specific area"
  }},
  "research_core": {{
    "research_question": "the user's question",
    "hypothesis": "(inferred) likely hypothesis",
    "key_contribution": "(inferred) what answering this would add",
    "methodology": "(inferred) likely approach",
    "key_findings": [],
    "limitations_stated": []
  }},
  "knowledge_landscape": {{
    "theoretical_framework": "(inferred) underlying theory",
    "key_citations": [
      {{
        "author": "(inferred) likely key author",
        "concept": "their contribution",
        "how_used": "relevance to this question"
      }}
    ],
    "debates_engaged": ["(inferred) scholarly debates this touches"],
    "assumptions": ["(inferred) implicit assumptions"]
  }},
  "frontier_indicators": {{
    "stated_gaps": ["(inferred) gaps this question implies"],
    "future_work_suggested": ["(inferred) follow-on research"],
    "unanswered_questions": ["the question itself plus related ones"],
    "methodological_limitations": ["(inferred) methodological challenges"],
    "calls_for_research": ["(inferred) why this research is needed"]
  }},
  "application_potential": {{
    "practical_implications": ["(inferred) potential applications"],
    "stakeholders_mentioned": ["(inferred) who would benefit"],
    "industries_relevant": ["(inferred) relevant sectors"],
    "technology_readiness": 1,
    "commercialization_barriers": ["(inferred) barriers"]
  }},
  "domain_seeds": {{
    "primary_domain": "(inferred) main territory",
    "adjacent_domains": ["(inferred) related territories"],
    "interdisciplinary_connections": ["(inferred) intersecting fields"],
    "keywords": ["key terms from the question"]
  }}
}}"""


DOMAIN_GENERATION_FROM_RESEARCH_PROMPT = """You are identifying innovation domains from research document analysis.

EXTRACTED RESEARCH DATA:
{research_extraction}

GRAPH CONTEXT (from knowledge base):
{graph_hints}

PWS METHODOLOGY CONTEXT:
{rag_context}

Generate domain candidates using FIVE lenses:

LENS 1: GAP-BASED DOMAINS — What the research explicitly says is missing or needed. Stated gaps, future work suggestions, and limitations become domain opportunities.

LENS 2: APPLICATION-BASED DOMAINS — Where this research could create practical value. Theoretical findings become applied domains. Lab results become industry domains.

LENS 3: INTERSECTION DOMAINS — Where this research meets other fields. Primary field x Adjacent field = Novel domain. Methodology from Field A applied to Problem in Field B.

LENS 4: FRONTIER DOMAINS — Where this research points to emerging territories. What would the next generation of this research address? What new questions does this enable?

LENS 5: TRANSLATION DOMAINS — Where research-to-practice gaps exist. Academic insight becomes practitioner domain. Scientific finding becomes product/service domain.

For each domain, use the PWS format: "[Activity/Problem] for [Stakeholder] in [Setting/Industry]"

Return ONLY valid JSON (no markdown fences):

{{
  "domains": [
    {{
      "domain_statement": "Activity for Stakeholder in Context",
      "source_lens": "gap | application | intersection | frontier | translation",
      "evidence_from_paper": "specific text or finding that suggests this",
      "research_foundation": "what scientific basis exists",
      "novelty_assessment": "established | emerging | speculative",
      "initial_scores": {{
        "research_maturity": 3,
        "application_readiness": 3,
        "competitive_whitespace": 3
      }},
      "key_questions_to_validate": ["question to investigate"]
    }}
  ]
}}

Generate 5-10 domains across multiple lenses. Prioritize intersection and frontier domains — these are often the most innovative."""


RESEARCH_DOMAIN_SCORING_PROMPT = """You are scoring research-derived domains for innovation opportunity.

RESEARCH EXTRACTION:
{research_extraction}

DOMAIN CANDIDATES:
{domain_candidates}

VALIDATION RESEARCH:
{research_results}

Score each domain on THREE CRITERIA:

CRITERION 1: RESEARCH MATURITY (1-5) — How developed is the scientific foundation?
5: Robust, replicated findings; established theories; mature methodology
4: Strong evidence base; some replication; accepted frameworks
3: Growing evidence; emerging methods; active debate
2: Early findings; limited replication; methodology developing
1: Speculative; minimal evidence; theoretical only

CRITERION 2: TRANSLATION READINESS (1-5) — How close to practical application?
5: Ready for implementation; clear pathway; demonstrated feasibility
4: Near-term applicable; minor gaps; feasibility shown
3: Medium-term potential; significant development needed
2: Long-term potential; major gaps between research and practice
1: Pure research; no clear application pathway

CRITERION 3: COMPETITIVE POSITION (1-5) — How much opportunity space exists?
5: Blue ocean; minimal competition; unique positioning possible
4: Low competition; differentiation achievable
3: Moderate competition; niche opportunities exist
2: High competition; differentiation difficult
1: Red ocean; saturated; late entry

Return ONLY valid JSON (no markdown fences):

{{
  "scored_domains": [
    {{
      "domain_statement": "the domain statement",
      "research_maturity": {{"score": 3, "rationale": "why this score", "key_evidence": ["evidence"]}},
      "translation_readiness": {{"score": 3, "rationale": "why this score", "key_evidence": ["evidence"]}},
      "competitive_position": {{"score": 3, "rationale": "why this score", "key_evidence": ["evidence"]}},
      "composite_score": 9.0,
      "uncertainty_level": "low | medium | high",
      "time_horizon": "near-term (1-2y) | medium-term (3-5y) | long-term (5+y)",
      "recommended_approach": "academic | startup | corporate | policy",
      "key_risks": ["risk"],
      "validation_priorities": ["what to investigate next"]
    }}
  ]
}}

Sort by composite_score descending. Composite = (Research Maturity * 0.3) + (Translation Readiness * 0.4) + (Competitive Position * 0.3)."""


RESEARCH_TRANSLATION_PROMPT = """Translate these research-derived domains into practitioner-friendly innovation opportunities.

SCORED DOMAINS:
{scored_domains}

RESEARCH CONTEXT:
{research_extraction}

For each of the top domains, provide:

1. PLAIN LANGUAGE STATEMENT — Rewrite for a non-academic audience
2. PROBLEM WORTH SOLVING FRAME — Who has this problem? What's their current pain? Why hasn't it been solved? What would solving it enable?
3. ENTRY POINT RECOMMENDATIONS — Academic path, Startup path, Corporate path, Policy path
4. STAKEHOLDER MAP — Research stakeholders (funders, publishers), Practice stakeholders (users, buyers), Bridge stakeholders (tech transfer, VCs)
5. PWS TOOL RECOMMENDATIONS — Which PWS tool to apply next based on the domain's characteristics

Return ONLY valid JSON (no markdown fences):

{{
  "translations": [
    {{
      "domain_statement": "original academic domain",
      "plain_language": "practitioner-friendly version",
      "problem_frame": {{
        "who_has_problem": "stakeholder description",
        "current_pain": "what they struggle with",
        "why_unsolved": "barriers to solution",
        "solving_enables": "what becomes possible"
      }},
      "entry_points": {{
        "academic": "research next step",
        "startup": "product/service opportunity",
        "corporate": "R&D initiative",
        "policy": "regulatory/funding change"
      }},
      "stakeholder_map": {{
        "research": ["who funds, publishes, cites"],
        "practice": ["who would use, buy, benefit"],
        "bridge": ["tech transfer, VCs, accelerators"]
      }},
      "recommended_pws_tool": "Scenario Analysis | JTBD | S-Curve | Trending to Absurd",
      "recommended_pws_reason": "why this tool fits"
    }}
  ]
}}"""
