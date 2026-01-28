"""CV Domain Discovery prompts for the Domain Explorer bot."""

CV_EXTRACTION_PROMPT = """You are a CV/resume analysis expert. Extract structured information from the following CV text and return ONLY valid JSON (no markdown fences).

CV TEXT:
{cv_text}

Return this exact JSON structure:
{{
  "professional_experience": [
    {{
      "role": "job title",
      "org": "organization name",
      "org_type": "startup|corporate|academic|nonprofit|government",
      "duration_months": 24,
      "domain_indicators": ["industry/domain keywords"],
      "technologies": ["tools and technologies used"],
      "problems_addressed": ["problems they worked on"],
      "stakeholders": ["who they served"],
      "achievements": ["key accomplishments"]
    }}
  ],
  "education": [
    {{
      "degree": "degree type",
      "field": "field of study",
      "institution": "school name",
      "research_focus": "research area if any"
    }}
  ],
  "skills": {{
    "technical": ["technical skills"],
    "methodologies": ["methodologies known"],
    "tools": ["software/tools"],
    "certifications": ["certifications"]
  }},
  "publications": [
    {{
      "title": "publication title",
      "domain": "domain area",
      "year": 2024,
      "contribution": "what they contributed"
    }}
  ],
  "stated_interests": ["explicitly stated interests"],
  "projects": [
    {{
      "name": "project name",
      "domain": "domain area",
      "role": "their role",
      "outcome": "what resulted"
    }}
  ],
  "network_indicators": {{
    "industries": ["industries they've touched"],
    "organizations": ["notable orgs"],
    "communities": ["professional communities"]
  }}
}}

Be thorough. Infer domain indicators from context even if not explicitly stated. If a field has no data, use an empty list or empty string."""

DOMAIN_GENERATION_PROMPT = """You are a PWS (Problem Worth Solving) domain discovery expert. Given a person's CV extraction, knowledge graph hints, and methodology context, generate innovation domain candidates.

CV EXTRACTION:
{cv_extraction}

KNOWLEDGE GRAPH HINTS:
{graph_hints}

PWS METHODOLOGY CONTEXT:
{rag_context}

Generate 5-10 domain candidates. Each domain MUST follow the PWS format:
"[Activity/Problem] for [Stakeholder] in [Setting/Industry]"

For each domain, provide:
{{
  "domains": [
    {{
      "domain_statement": "[Activity] for [Stakeholder] in [Setting]",
      "category": "core|adjacent|intersection",
      "cv_evidence": ["specific CV elements supporting this domain"],
      "intersection_sources": ["if intersection: which 2+ experience areas combine"],
      "opportunity_hypothesis": "why this domain may contain problems worth solving",
      "pws_phase_1_seed": "initial problem space description for PWS Phase 1"
    }}
  ]
}}

Rules:
1. "core" domains come directly from their primary experience
2. "adjacent" domains extend their experience to neighboring fields
3. "intersection" domains combine 2+ distinct experience areas — these are often the most innovative
4. Prioritize domains where the person has both KNOWLEDGE and ACCESS to stakeholders
5. Each domain should be specific enough to research but broad enough to contain multiple problems
6. Use PWS language: focus on problems and stakeholders, not solutions

Return ONLY valid JSON (no markdown fences)."""

DOMAIN_SCORING_PROMPT = """You are a PWS domain evaluation expert. Score each domain candidate based on the person's CV evidence and research validation.

CV EXTRACTION:
{cv_extraction}

DOMAIN CANDIDATES:
{domain_candidates}

RESEARCH VALIDATION:
{research_results}

Score each domain on three criteria (1-5 scale):

1. **Interest** (1-5): How likely is this person to be passionate about this domain?
   - 5: Multiple CV signals of deep engagement (publications, side projects, stated interests)
   - 3: Related experience but no explicit passion signals
   - 1: Purely inferred, no direct evidence of interest

2. **Knowledge** (1-5): How much domain expertise does this person already have?
   - 5: Deep professional experience + education + publications in this exact area
   - 3: Adjacent experience that transfers well
   - 1: Would need significant learning to operate here

3. **Access** (1-5): Can this person reach stakeholders and gather insights?
   - 5: Has worked directly with these stakeholders, has network in this space
   - 3: Has some connections or could leverage existing network
   - 1: No apparent access, would need to build from scratch

Return JSON:
{{
  "scored_domains": [
    {{
      "domain_statement": "the domain statement",
      "interest": {{"score": 4, "rationale": "why this score"}},
      "knowledge": {{"score": 3, "rationale": "why this score"}},
      "access": {{"score": 5, "rationale": "why this score"}},
      "composite_score": 12,
      "top_evidence": ["key supporting evidence"],
      "recommended_next_steps": ["what to do to explore this domain"]
    }}
  ]
}}

Sort by composite_score descending. Return ONLY valid JSON (no markdown fences)."""
