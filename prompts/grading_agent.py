"""
Problem Discovery Grading Agent for Mindrian
============================================

Evaluates students' ability to systematically discover and validate REAL problems worth solving.
Prioritizes problem reality over business viability - this is discovery phase, not investment.

Integrated with Mindrian's Tools:
- **Neo4j (Mindrian_Brain)**: Graph database for framework validation and hidden connections
- **FileSearch RAG**: Semantic retrieval from PWS course materials and case studies
- **LangExtract**: Structured data extraction for PWS patterns
- **Gemini 3 Preview Pro**: Advanced reasoning for complex assessment tasks

Scoring Formula:
    Discovery_Score = 0.35×PR + 0.25×PD + 0.20×FI + 0.10×MT + 0.05×CW + 0.05×IW

Components:
    PR = Problem Reality (35%) - "Is it Real?" validation with evidence
    PD = Problem Discovery (25%) - Quantity and quality of problems uncovered
    FI = Framework Integration (20%) - Systematic use of discovery tools
    MT = Mindrian_Brain Thinking (10%) - Leveraging knowledge connections
    CW = Competitive Win (5%) - "Can We Win?" basic assessment
    IW = Impact Worth (5%) - "Is it Worth It?" basic sizing

Model Requirements:
    - Use gemini-3-flash-preview for grading analysis (advanced reasoning)
    - Use gemini-2.0-flash for quick extractions
"""

# ==============================================================================
# GRADING AGENT SYSTEM PROMPT
# ==============================================================================

GRADING_AGENT_PROMPT = """You are an expert grading agent focused on evaluating students' ability to **systematically discover and validate REAL problems worth solving**. You prioritize problem reality over business viability, as the goal is problem discovery, not investment readiness.

## Your Grading Approach

### Sequential Thinking Process
Before grading, you MUST:
1. **Identify frameworks/tools used** - What discovery methods did the student apply?
2. **Validate proper usage** - Were frameworks applied correctly per PWS methodology?
3. **Check evidence quality** - Is there real validation or just assumptions?
4. **Query Mindrian_Brain** - What problem spaces/connections were missed?
5. **Calculate scores** - Apply the weighted formula fairly

### Mathematical Scoring Equation
```
Discovery_Score = 0.35×PR + 0.25×PD + 0.20×FI + 0.10×MT + 0.05×CW + 0.05×IW
```

### Component Definitions
1. **Problem Reality (PR) - 35%**: "Is it Real?" validation
   - Direct user pain evidence (quotes, observations)
   - Problem frequency data
   - Current solutions gap analysis
   - Root cause analysis depth

2. **Problem Discovery (PD) - 25%**: Quantity and quality of problems
   - Number of problems identified
   - Validation rate (% confirmed as real)
   - Problem diversity (acute, chronic, latent, future)

3. **Framework Integration (FI) - 20%**: Systematic tool usage
   - Problem Finding: JTBD, Four Lenses, User Journey, TTA
   - Problem Validation: 5 Whys, Root Cause, Mom Test
   - Problem Framing: PWS, Issue Trees, MECE

4. **Mindrian_Brain Thinking (MT) - 10%**: Knowledge connections
   - Related framework discovery
   - Hidden problem space connections
   - Cross-domain insights

5. **Competitive Win (CW) - 5%**: Basic capability check
   - Team has relevant skills/access?
   - Not dominated by incumbents?

6. **Impact Worth (IW) - 5%**: Basic market sizing
   - Problem affects enough people?
   - Big enough to matter?

### Letter Grade Scale
- **A+ (95-100)**: Exceptional - Multiple validated real problems with deep evidence
- **A (90-94)**: Excellent - Well-validated problems with strong methodology
- **A- (87-89)**: Very Good - Solid validation with minor gaps
- **B+ (83-86)**: Good - Good discovery but validation incomplete
- **B (80-82)**: Above Average - Reasonable work, several assumptions unvalidated
- **B- (77-79)**: Slightly Above Average - Discovery present but evidence thin
- **C+ (73-76)**: Average - Problems identified but mostly assumed, not validated
- **C (70-72)**: Below Average - Weak validation, many assumptions
- **C- (67-69)**: Barely Passing - Minimal discovery, poor methodology
- **D (60-66)**: Poor - Little real problem discovery
- **F (<60)**: Failing - No validated problems, speculation only

## Output Format

You MUST output in this exact format:

### FINAL GRADE: [Letter Grade] ([Score]/100)

**One-Line Verdict:** [Whether they found real problems worth solving or not]

---

### GRADE BREAKDOWN

| Component | Weight | Score | Points | Brief Assessment |
|-----------|--------|-------|---------|-----------------|
| **Problem Reality (Is it Real?)** | 35% | X/10 | XX.X | [Evidence quality] |
| **Problem Discovery** | 25% | X/10 | XX.X | [# problems found] |
| **Framework Integration** | 20% | X/10 | XX.X | [Tools used properly] |
| **Mindiran Thinking** | 10% | X/10 | XX.X | [Hidden connections] |
| **Can We Win?** | 5% | X/10 | X.X | [Basic capability check] |
| **Is it Worth It?** | 5% | X/10 | X.X | [Basic market size] |
| **TOTAL** | **100%** | - | **XX.X** | **[Letter Grade]** |

---

### PROBLEM REALITY VALIDATION (35% - Most Critical)

**"Is it Real?" Deep Dive:**

| Validation Criteria | Expected | Delivered | Score | Evidence Quality |
|-------------------|----------|-----------|-------|-----------------|
| **User Pain Evidence** | Direct quotes, observations | [What provided] | X/10 | [Strong/Weak/None] |
| **Problem Frequency** | Occurrence data | [What provided] | X/10 | [Validated/Assumed] |
| **Current Solutions Gap** | What's broken now | [What provided] | X/10 | [Clear/Vague/Missing] |
| **Root Cause Analysis** | Why it exists | [What provided] | X/10 | [Deep/Surface/None] |

**Reality Check Results:**
- **Validated Problems:** [List with evidence]
- **Assumed Problems:** [List without evidence]
- **Fantasy Problems:** [List of unfounded assumptions]

**Missing Evidence Types:**
- [Evidence type 1 they should have gathered]
- [Evidence type 2 they should have gathered]
- [Evidence type 3 they should have gathered]

---

### PROBLEM DISCOVERY ANALYSIS (25%)

**Discovery Funnel:**
```
Domain Explored: [What space]
    |
Problems Identified: [#] problems
    |
Problems Validated as Real: [#] problems (X% validation rate)
    |
Problems Worth Pursuing: [#] problems
```

**Problem Quality Matrix:**

| Problem Category | Found | Quality | Missing Opportunities |
|-----------------|-------|---------|---------------------|
| Acute Pain Points | [#] | [H/M/L] | [What they missed] |
| Chronic Frustrations | [#] | [H/M/L] | [What they missed] |
| Latent Needs | [#] | [H/M/L] | [What they missed] |
| Future Problems | [#] | [H/M/L] | [What they missed] |

---

### FRAMEWORK INTEGRATION (20%)

**Discovery Tools Usage:**

| Framework Type | Expected Tools | Actually Used | Effectiveness |
|---------------|----------------|---------------|---------------|
| **Problem Finding** | JTBD, Four Lenses, User Journey | [Used] | [Score]/10 |
| **Problem Validation** | 5 Whys, Root Cause, Mom Test | [Used] | [Score]/10 |
| **Problem Framing** | PWS, Issue Trees, MECE | [Used] | [Score]/10 |

**Critical Missing Tools:**
Based on Mindrian_Brain, they should have used:
- [Tool 1]: [Why needed for their domain]
- [Tool 2]: [Why needed for their domain]

---

### MINDIRAN_BRAIN THINKING (10%)

**Hidden Connections Found/Missed:**
- **Found:** [Connections they identified]
- **Missed:** [High-value connections from knowledge graph]
- **Related Frameworks Unused:** [List]
- **Problem Space Coverage:** [X%]

---

### COMPETITIVE & WORTH ASSESSMENT (10% Combined)

**Can We Win? (5%):** [Basic assessment - capabilities exist? yes/no]

**Is it Worth It? (5%):** [Basic sizing - big enough problem? yes/no]

*Note: These are de-emphasized as we're in discovery phase, not business planning*

---

### IF THEY PURSUE: NEXT STEPS

**Top 3 Actions:**
1. **Validate [Most Promising Problem]** using [Specific Method]
2. **Deepen evidence** for [Problem X] via [Specific Research]
3. **Connect** [Problem Y] to [Adjacent Problem Space]

---

## Execution Guidelines

1. **Grade first, explain second** - Start with final grade and table
2. **Weight "Is it Real?" heavily** - 80% of validation score on evidence
3. **Count real problems, not ideas** - Only validated problems matter
4. **Query Mindiran_Brain** - Find what problem spaces they missed
5. **De-emphasize business case** - This is discovery, not pitch phase
6. **Focus on evidence quality** - Assumptions vs. validation
7. **Keep business aspects minimal** - Just basic checks for CW/IW
8. **Highlight missed discoveries** - What problems are still hidden
9. **Be direct about reality** - No credit for well-structured fantasies

Remember: Finding ONE deeply validated real problem is worth more than 20 assumed problems. Grade accordingly."""


# ==============================================================================
# NEO4J CYPHER QUERIES FOR GRADING
# ==============================================================================

GRADING_NEO4J_QUERIES = {
    # Find frameworks student should have used based on domain
    "recommended_frameworks": """
    MATCH (d:Domain)-[:USES_FRAMEWORK]->(f:Framework)
    WHERE d.name CONTAINS $domain_keywords
    RETURN f.name as framework, f.description as description, f.when_to_use as usage
    LIMIT 10
    """,

    # Find related problem spaces they might have missed
    "related_problem_spaces": """
    MATCH (p:ProblemSpace)-[:RELATES_TO]->(related:ProblemSpace)
    WHERE p.name CONTAINS $topic
    RETURN related.name as problem_space, related.description as description
    LIMIT 10
    """,

    # Get assessment history for student
    "student_assessment_history": """
    MATCH (s:Student {id: $student_id})-[:RECEIVED_ASSESSMENT]->(a:Assessment)
    RETURN a.timestamp as date, a.total_score as score, a.letter_grade as grade
    ORDER BY a.timestamp DESC
    LIMIT 10
    """,

    # Find common weaknesses across assessments
    "common_weaknesses": """
    MATCH (a:Assessment)-[:HAS_CRITIQUE]->(c:Critique)-[:IDENTIFIES_WEAKNESS]->(w:Weakness)
    WITH w.description as weakness, count(*) as frequency
    WHERE frequency > 3
    RETURN weakness, frequency
    ORDER BY frequency DESC
    LIMIT 5
    """,

    # Track improvement trajectory
    "improvement_trajectory": """
    MATCH (s:Student {id: $student_id})-[:RECEIVED_ASSESSMENT]->(a:Assessment)
    WITH s, a ORDER BY a.timestamp
    WITH s, collect(a) as assessments
    UNWIND range(1, size(assessments)-1) as i
    WITH assessments[i-1] as prev, assessments[i] as curr
    RETURN prev.timestamp as from_date, curr.timestamp as to_date,
           prev.total_score as from_score, curr.total_score as to_score,
           curr.total_score - prev.total_score as improvement
    """,

    # Create assessment record
    "create_assessment": """
    CREATE (a:Assessment:ProblemDiscoveryAssessment {
        id: $assessment_id,
        student_id: $student_id,
        document_id: $document_id,
        timestamp: datetime(),
        total_score: $total_score,
        letter_grade: $letter_grade,
        verdict: $verdict,
        problem_reality_score: $pr_score,
        problem_discovery_score: $pd_score,
        framework_integration_score: $fi_score,
        mindrian_thinking_score: $mt_score,
        competitive_win_score: $cw_score,
        impact_worth_score: $iw_score
    })
    RETURN a.id as assessment_id
    """,

    # Find best practices from top performers
    "top_performer_patterns": """
    MATCH (a:Assessment)
    WHERE a.total_score >= 90
    MATCH (a)-[:HAS_CRITIQUE]->(c:Critique)-[:IDENTIFIES_STRENGTH]->(s:Strength)
    RETURN s.description as strength, count(*) as frequency
    ORDER BY frequency DESC
    LIMIT 10
    """,

    # Get framework details for validation
    "validate_framework_usage": """
    MATCH (f:Framework)
    WHERE f.name IN $framework_names
    RETURN f.name as name, f.proper_usage as proper_usage,
           f.common_mistakes as common_mistakes, f.validation_criteria as criteria
    """,

    # Find hidden connections in domain
    "hidden_connections": """
    MATCH (d:Domain {name: $domain})-[r:CONNECTS_TO|RELATES_TO|SHARES_PATTERN_WITH]->(other)
    WHERE NOT other.name IN $mentioned_items
    RETURN type(r) as connection_type, other.name as hidden_item,
           other.description as description
    LIMIT 15
    """,

    # Verify Neo4j schema availability
    "verify_schema": """
    MATCH (n) RETURN DISTINCT labels(n) as node_types, count(n) as count
    ORDER BY count DESC LIMIT 20
    """,

    # Load structured argument framework
    "load_argument_framework": """
    MATCH (f:Foundation)-[:SUPPORTS]->(mr:MainRecommendation)
    OPTIONAL MATCH (sp:SupportingPillar)-[:SUPPORTS]->(mr)
    OPTIONAL MATCH (e:Evidence)-[:SUPPORTS]->(sp)
    RETURN f.title as foundation, sp.title as pillar, collect(e.title) as evidence, mr.title as recommendation
    """,

    # Load bias framework
    "load_bias_framework": """
    MATCH (bf:BiasFramework)-[:HAS_CATEGORY]->(cat:BiasCategory)-[:CONTAINS_BIAS]->(cb:CognitiveBias)
    WHERE cb.risk_level = "critical"
    OPTIONAL MATCH (cb)-[:HAS_DETECTION_PROTOCOL]->(dp:DetectionProtocol)
    OPTIONAL MATCH (cb)-[:HAS_MITIGATION_STRATEGY]->(ms:MitigationStrategy)
    RETURN cb.name as bias_name, cb.risk_level as risk,
           dp.detection_questions as questions, dp.red_flags as red_flags,
           ms.mitigation_steps as mitigation, ms.validation_requirements as validation
    ORDER BY cb.innovation_impact DESC
    """,

    # AI System integration analysis
    "ai_system_analysis": """
    MATCH (ai:AISystem)
    RETURN ai.title as system, ai.function as function, ai.description as description
    ORDER BY ai.function
    """,

    # Implementation feasibility analysis
    "implementation_feasibility": """
    MATCH (impl:Implementation)
    OPTIONAL MATCH (phase:Phase)
    RETURN impl.title as implementation, impl.type as impl_type,
           phase.title as phase, phase.timeline as timeline
    ORDER BY phase.order
    """,

    # Evidence quality analysis
    "evidence_analysis": """
    MATCH (e:Evidence)-[:SUPPORTS]->(sp:SupportingPillar)
    RETURN sp.title as pillar, count(e) as evidence_count,
           collect(e.description) as evidence_descriptions
    """,

    # Framework case studies
    "framework_case_studies": """
    MATCH (cs:CaseStudy)-[:APPLIES_FRAMEWORK]->(f:Framework)
    WHERE f.name IN $framework_names
    RETURN f.name as framework, cs.name as case_study, cs.description as description,
           cs.success_factors as success_factors, cs.lessons_learned as lessons
    LIMIT 10
    """
}


# ==============================================================================
# COGNITIVE BIAS DETECTION FRAMEWORK
# ==============================================================================

CRITICAL_BIASES = {
    "confirmation_bias": {
        "name": "Confirmation Bias",
        "description": "Cherry-picking supporting evidence while ignoring contradictory data",
        "risk_level": "critical",
        "detection_questions": [
            "Does the student only cite evidence that supports their position?",
            "Are counter-arguments or alternative explanations addressed?",
            "Is there diversity in sources consulted?",
            "Are inconvenient data points acknowledged?"
        ],
        "red_flags": [
            "All sources agree with conclusion",
            "No mention of challenges or risks",
            "Selective quotation from sources",
            "Ignoring industry failures"
        ],
        "mitigation_strategy": "Require devil's advocate analysis, demand acknowledgment of limitations"
    },
    "wishful_thinking": {
        "name": "Wishful Thinking",
        "description": "Unrealistic feasibility assumptions based on desired outcomes",
        "risk_level": "critical",
        "detection_questions": [
            "Are projections grounded in comparable historical data?",
            "Is there a realistic assessment of implementation challenges?",
            "Are timelines based on similar projects or optimistic estimates?",
            "Does the plan account for typical failure modes?"
        ],
        "red_flags": [
            "Best-case scenario presented as baseline",
            "No contingency planning",
            "Unrealistic adoption curves",
            "Ignoring resource constraints"
        ],
        "mitigation_strategy": "Require comparison to similar projects, demand conservative scenario analysis"
    },
    "authority_bias": {
        "name": "Authority Bias",
        "description": "Over-reliance on expert opinions without independent validation",
        "risk_level": "critical",
        "detection_questions": [
            "Are expert claims validated with primary data?",
            "Is there diversity in expert perspectives cited?",
            "Are potential conflicts of interest acknowledged?",
            "Is the methodology behind expert claims examined?"
        ],
        "red_flags": [
            "Single source dominates citations",
            "No questioning of expert assumptions",
            "Appeal to authority without evidence",
            "Ignoring dissenting expert views"
        ],
        "mitigation_strategy": "Require multiple independent sources, demand methodology review"
    },
    "availability_heuristic": {
        "name": "Availability Heuristic",
        "description": "Overweighting memorable or recent examples while ignoring base rates",
        "risk_level": "critical",
        "detection_questions": [
            "Are conclusions based on representative samples?",
            "Is base rate data provided for claims?",
            "Are recent dramatic examples overweighted?",
            "Is there systematic analysis vs. anecdotal evidence?"
        ],
        "red_flags": [
            "Reliance on famous case studies only",
            "No statistical analysis",
            "Recent news driving conclusions",
            "Ignoring silent evidence"
        ],
        "mitigation_strategy": "Require statistical validation, demand base rate analysis"
    },
    "dunning_kruger": {
        "name": "Dunning-Kruger Effect",
        "description": "Overconfidence in competence without demonstrated expertise",
        "risk_level": "critical",
        "detection_questions": [
            "Does confidence level match demonstrated knowledge?",
            "Are limitations of knowledge acknowledged?",
            "Is there evidence of domain expertise?",
            "Are complex topics oversimplified?"
        ],
        "red_flags": [
            "Definitive claims without supporting evidence",
            "No acknowledgment of knowledge gaps",
            "Oversimplification of complex systems",
            "Dismissal of implementation challenges"
        ],
        "mitigation_strategy": "Require explicit acknowledgment of limitations, demand evidence of expertise"
    },
    "survivorship_bias": {
        "name": "Survivorship Bias",
        "description": "Focusing on successes while ignoring failures that didn't survive",
        "risk_level": "critical",
        "detection_questions": [
            "Are failures in the domain analyzed?",
            "Is the full population of attempts considered?",
            "Are success rates calculated accurately?",
            "Are conditions for failure examined?"
        ],
        "red_flags": [
            "Only successful case studies cited",
            "No failure analysis",
            "Inflated success rates",
            "Ignoring market casualties"
        ],
        "mitigation_strategy": "Require failure case studies, demand complete dataset analysis"
    },
    "planning_fallacy": {
        "name": "Planning Fallacy",
        "description": "Unrealistic timeline and budget estimates ignoring historical patterns",
        "risk_level": "critical",
        "detection_questions": [
            "Are timelines compared to similar completed projects?",
            "Are buffer times included for unexpected delays?",
            "Is the optimism of estimates acknowledged?",
            "Are resource estimates validated against benchmarks?"
        ],
        "red_flags": [
            "Aggressive timelines without justification",
            "No comparison to similar projects",
            "Underestimated complexity",
            "Missing dependency analysis"
        ],
        "mitigation_strategy": "Require reference class forecasting, demand historical comparison"
    }
}


# ==============================================================================
# COMPREHENSIVE GRADING SYSTEM
# ==============================================================================

GRADING_WEIGHTS = {
    "problem_discovery": {
        "problem_reality": 0.35,  # "Is it Real?" validation
        "problem_discovery": 0.25,  # Quantity and quality of problems
        "framework_integration": 0.20,  # Systematic tool usage
        "mindrian_thinking": 0.10,  # Knowledge connections
        "competitive_win": 0.05,  # Basic capability check
        "impact_worth": 0.05,  # Basic market sizing
    },
    "innovation_assessment": {
        "technical_feasibility": 0.30,  # Technology readiness
        "logical_argument": 0.60,  # Argument structure quality
        "tool_usage": 0.10,  # Methodology application
    }
}

LETTER_GRADE_SCALE = {
    (95, 100): "A+",
    (90, 94.99): "A",
    (87, 89.99): "A-",
    (83, 86.99): "B+",
    (80, 82.99): "B",
    (77, 79.99): "B-",
    (73, 76.99): "C+",
    (70, 72.99): "C",
    (67, 69.99): "C-",
    (60, 66.99): "D",
    (0, 59.99): "F",
}

def get_letter_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    for (low, high), grade in LETTER_GRADE_SCALE.items():
        if low <= score <= high:
            return grade
    return "F"


# ==============================================================================
# TECHNICAL FEASIBILITY SUB-COMPONENTS
# ==============================================================================

TECHNICAL_FEASIBILITY_COMPONENTS = {
    "technology_maturity": {
        "weight": 0.25,
        "description": "Assess readiness level of proposed technology",
        "scoring_criteria": [
            "TRL level assessment",
            "Proven implementations",
            "Industry adoption",
            "Technical risk factors"
        ]
    },
    "technology_availability": {
        "weight": 0.20,
        "description": "Current accessibility of required technology",
        "scoring_criteria": [
            "Commercial availability",
            "Open source options",
            "Vendor ecosystem",
            "Integration complexity"
        ]
    },
    "resource_availability": {
        "weight": 0.20,
        "description": "Required resources assessment",
        "scoring_criteria": [
            "Team skills match",
            "Infrastructure needs",
            "Data requirements",
            "Partnership dependencies"
        ]
    },
    "cost_viability": {
        "weight": 0.15,
        "description": "Economic feasibility assessment",
        "scoring_criteria": [
            "Development costs",
            "Operational costs",
            "ROI timeline",
            "Funding requirements"
        ]
    },
    "implementation_simplicity": {
        "weight": 0.15,
        "description": "Complexity assessment",
        "scoring_criteria": [
            "Architecture complexity",
            "Integration points",
            "Change management",
            "Phasing approach"
        ]
    },
    "risk_score": {
        "weight": 0.05,
        "description": "Implementation risks",
        "scoring_criteria": [
            "Technical risks",
            "Market risks",
            "Regulatory risks",
            "Execution risks"
        ]
    }
}


# ==============================================================================
# LOGICAL ARGUMENT ASSESSMENT (MECE + PYRAMID PRINCIPLE)
# ==============================================================================

LOGICAL_ARGUMENT_COMPONENTS = {
    "structure": {
        "weight": 0.20,
        "description": "Logical flow analysis",
        "criteria": [
            "Clear situation-complication-resolution",
            "Hierarchical organization",
            "Proper scoping",
            "Introduction-body-conclusion coherence"
        ]
    },
    "reasoning": {
        "weight": 0.25,
        "description": "Gap detection and logic quality",
        "criteria": [
            "Causal chain validity",
            "Assumption explicitness",
            "Counter-argument handling",
            "Logical fallacy absence"
        ]
    },
    "mece": {
        "weight": 0.20,
        "description": "Mutually Exclusive, Collectively Exhaustive",
        "criteria": [
            "No overlap between categories",
            "Complete coverage of topic",
            "Clear boundaries",
            "Balanced depth"
        ]
    },
    "evidence": {
        "weight": 0.20,
        "description": "Source diversity and quality",
        "criteria": [
            "Multiple source types",
            "Primary vs secondary sources",
            "Recency of data",
            "Source credibility"
        ]
    },
    "conclusion": {
        "weight": 0.15,
        "description": "Derivation strength",
        "criteria": [
            "Supported by evidence",
            "Follows from arguments",
            "Actionable recommendations",
            "Appropriate confidence level"
        ]
    }
}


# ==============================================================================
# JSON HANDOFF TEMPLATE
# ==============================================================================

GRADING_JSON_TEMPLATE = """{
  "grading_summary": {
    "final_grade": "[Letter]",
    "numeric_score": XX.X,
    "grading_approach": "Problem Reality First - 80% weight on 'Is it Real?' validation",
    "primary_verdict": "[Found real problems | Found assumed problems | Found no real problems]"
  },
  "component_scores": {
    "problem_reality": {
      "score": X.X,
      "weight": 0.35,
      "evidence_quality": "[Strong|Moderate|Weak|None]",
      "validated_problems_count": X,
      "key_issue": "[Main validation failure]"
    },
    "problem_discovery": {
      "score": X.X,
      "weight": 0.25,
      "problems_found": X,
      "problems_validated": X,
      "discovery_rate": "X%"
    },
    "framework_integration": {
      "score": X.X,
      "weight": 0.20,
      "tools_used": ["tool1", "tool2"],
      "tools_missed": ["tool3", "tool4"],
      "integration_quality": "[Excellent|Good|Poor]"
    },
    "mindrian_thinking": {
      "score": X.X,
      "weight": 0.10,
      "hidden_connections_found": X,
      "hidden_connections_missed": X
    },
    "competitive_win": {
      "score": X.X,
      "weight": 0.05,
      "assessment": "[Pass|Fail|Partial]"
    },
    "impact_worth": {
      "score": X.X,
      "weight": 0.05,
      "assessment": "[Pass|Fail|Partial]"
    }
  },
  "key_findings": {
    "strongest_validated_problem": {
      "name": "[Problem name]",
      "evidence_strength": "X/10",
      "validation_method": "[How validated]"
    },
    "biggest_miss": {
      "what": "[What they missed]",
      "why_critical": "[Impact of missing this]",
      "discovery_tool_needed": "[Tool that would have found it]"
    }
  },
  "grading_rationale": {
    "why_this_grade": "[Core reason for grade]",
    "grade_limiting_factor": "[What prevented higher grade]",
    "comparison_benchmark": "Expected X validated problems, found Y"
  },
  "improvement_priorities": [
    {
      "priority": 1,
      "action": "[Specific action]",
      "tool": "[Specific framework]",
      "expected_outcome": "[What this achieves]"
    }
  ],
  "neo4j_insights": {
    "related_frameworks_unused": ["framework1", "framework2"],
    "hidden_connections_missed": X,
    "problem_space_coverage": "X%"
  }
}"""


# ==============================================================================
# GRADING WORKFLOW PROMPTS
# ==============================================================================

FRAMEWORK_DETECTION_PROMPT = """Analyze this student work and identify all problem discovery frameworks, tools, and methodologies used.

STUDENT WORK:
{student_work}

Return a JSON object:
{{
    "frameworks_used": [
        {{"name": "Framework Name", "evidence": "How it was used", "properly_applied": true/false}}
    ],
    "tools_mentioned": ["tool1", "tool2"],
    "methodologies_applied": ["methodology1", "methodology2"],
    "domain_explored": "The problem domain they investigated",
    "key_topics": ["topic1", "topic2", "topic3"]
}}

Return ONLY valid JSON."""


PROBLEM_EXTRACTION_PROMPT = """Extract all problems identified in this student work. Classify each by validation status.

STUDENT WORK:
{student_work}

Return a JSON object:
{{
    "problems_identified": [
        {{
            "problem_statement": "The problem described",
            "category": "acute_pain|chronic_frustration|latent_need|future_problem",
            "validation_status": "validated|assumed|fantasy",
            "evidence_provided": "What evidence supports this",
            "evidence_quality": "strong|moderate|weak|none"
        }}
    ],
    "total_problems": X,
    "validated_count": X,
    "assumed_count": X,
    "fantasy_count": X,
    "validation_rate": "X%"
}}

Return ONLY valid JSON."""


EVIDENCE_QUALITY_PROMPT = """Evaluate the evidence quality in this student work for problem validation.

STUDENT WORK:
{student_work}

Rate evidence on these criteria:
1. Direct user quotes/observations (not assumptions)
2. Quantitative frequency data
3. Current solution gap analysis
4. Root cause analysis depth

Return a JSON object:
{{
    "user_pain_evidence": {{
        "score": X,
        "examples": ["example1", "example2"],
        "quality": "strong|weak|none"
    }},
    "frequency_data": {{
        "score": X,
        "data_points": ["data1", "data2"],
        "validated_or_assumed": "validated|assumed"
    }},
    "solution_gap_analysis": {{
        "score": X,
        "gaps_identified": ["gap1", "gap2"],
        "clarity": "clear|vague|missing"
    }},
    "root_cause_analysis": {{
        "score": X,
        "depth": "deep|surface|none",
        "methods_used": ["method1", "method2"]
    }},
    "overall_evidence_score": X,
    "missing_evidence_types": ["type1", "type2"]
}}

Return ONLY valid JSON."""


SCORING_CALCULATION_PROMPT = """Calculate the final grade based on these component analyses.

FRAMEWORK ANALYSIS:
{framework_analysis}

PROBLEM EXTRACTION:
{problem_extraction}

EVIDENCE QUALITY:
{evidence_quality}

NEO4J INSIGHTS:
{neo4j_insights}

Apply the scoring formula:
Discovery_Score = 0.35×PR + 0.25×PD + 0.20×FI + 0.10×MT + 0.05×CW + 0.05×IW

Calculate each component score (0-10), multiply by weight, sum for total.

Return a JSON object with all scores and the final grade following the GRADING_JSON_TEMPLATE format.

Return ONLY valid JSON."""


# ==============================================================================
# MINDRIAN TOOL INTEGRATION
# ==============================================================================

MINDRIAN_TOOLS_CONFIG = {
    "gemini_model": {
        "primary": "gemini-3-flash-preview",  # For complex reasoning (grading, bias detection)
        "secondary": "gemini-2.0-flash",  # For quick extractions
    },
    "neo4j": {
        "description": "Graph database (Mindrian_Brain) for framework discovery and hidden connections",
        "use_cases": [
            "Find related frameworks based on domain",
            "Discover hidden problem space connections",
            "Validate framework usage patterns",
            "Track student assessment history",
            "Query case studies for comparison"
        ]
    },
    "filesearch": {
        "description": "Semantic retrieval from PWS course materials",
        "use_cases": [
            "Find relevant methodology guides",
            "Retrieve framework documentation",
            "Get case study examples",
            "Pull lecture content for validation"
        ]
    },
    "langextract": {
        "description": "Structured data extraction for PWS patterns",
        "use_cases": [
            "Extract problems from student work",
            "Identify assumptions (stated and hidden)",
            "Detect evidence quality signals",
            "Parse framework usage patterns"
        ]
    }
}


# ==============================================================================
# BIAS DETECTION PROMPT (Uses Gemini 3 Preview Pro)
# ==============================================================================

BIAS_DETECTION_PROMPT = """You are conducting MANDATORY cognitive bias detection for student work assessment.
This MUST be completed before any grading proceeds.

STUDENT WORK:
{student_work}

MANDATORY BIAS CHECK - Analyze for all 7 critical biases:

1. **CONFIRMATION BIAS** - Cherry-picking supporting evidence
   - Detection questions: Only supportive sources? Missing counter-arguments?
   - Red flags: All sources agree, no challenges mentioned

2. **WISHFUL THINKING** - Unrealistic feasibility assumptions
   - Detection questions: Are projections grounded? Realistic timelines?
   - Red flags: Best-case as baseline, no contingencies

3. **AUTHORITY BIAS** - Over-reliance on expert opinions
   - Detection questions: Claims validated independently? Source diversity?
   - Red flags: Single source dominates, no methodology review

4. **AVAILABILITY HEURISTIC** - Overweighting memorable examples
   - Detection questions: Representative samples? Base rate data?
   - Red flags: Only famous cases, no statistics

5. **DUNNING-KRUGER EFFECT** - Overconfidence in competence
   - Detection questions: Confidence matches knowledge? Limitations acknowledged?
   - Red flags: Definitive claims without evidence, oversimplification

6. **SURVIVORSHIP BIAS** - Focusing on successes only
   - Detection questions: Failures analyzed? Full population considered?
   - Red flags: Only success stories, inflated success rates

7. **PLANNING FALLACY** - Unrealistic estimates
   - Detection questions: Historical comparison? Buffer times included?
   - Red flags: Aggressive timelines, missing dependencies

Return JSON:
{{
    "bias_detection_complete": true,
    "overall_confidence": 0.XX,
    "biases_detected": [
        {{
            "bias_name": "Name",
            "detected": true/false,
            "confidence": 0.XX,
            "risk_level": "high/medium/low",
            "evidence": "Specific evidence from student work",
            "mitigation_applied": "What mitigation was needed"
        }}
    ],
    "flagged_claims": ["Claim 1 needing validation", "Claim 2"],
    "confidence_adjustments": "How bias detection affected analysis"
}}

CRITICAL: If overall_confidence < 0.75, the grading CANNOT proceed.

Return ONLY valid JSON."""


# ==============================================================================
# DOMAIN ANALYSIS PROMPT (Uses FileSearch + Neo4j)
# ==============================================================================

DOMAIN_ANALYSIS_PROMPT = """Conduct comprehensive domain analysis for the student work.

STUDENT WORK:
{student_work}

NEO4J CONTEXT (Related frameworks and connections):
{neo4j_context}

FILESEARCH CONTEXT (PWS course materials):
{filesearch_context}

Perform systematic domain mapping:

1. **EXPLICIT DOMAINS**: Directly mentioned in the work
2. **IMPLICIT DOMAINS**: Inferred from context
3. **SIGNIFICANCE RANKING**: Primary/Secondary/Tertiary
4. **ADDRESSED vs OVERLOOKED**: What's covered and what's missing
5. **KEY ASSUMPTIONS**: About each domain
6. **CRITICAL OMISSIONS**: Important gaps

Return JSON:
{{
    "domain_analysis_complete": true,
    "domains": [
        {{
            "name": "Domain name",
            "significance": "primary/secondary/tertiary",
            "mentioned": true/false,
            "addressed_depth": "full/partial/none",
            "key_assumptions": ["assumption 1", "assumption 2"],
            "omissions": ["what's missing"]
        }}
    ],
    "major_omissions": ["Critical gap 1", "Critical gap 2"],
    "problematic_assumptions": [
        {{"assumption": "The assumption", "why_problematic": "Reason"}}
    ],
    "neo4j_suggested_domains": ["Domain from graph not mentioned"],
    "domain_coverage_score": 0.XX
}}

Return ONLY valid JSON."""


# ==============================================================================
# FRAMEWORK VALIDATION PROMPT (Uses Neo4j + LangExtract)
# ==============================================================================

FRAMEWORK_VALIDATION_PROMPT = """Validate framework usage in student work against PWS methodology standards.

STUDENT WORK:
{student_work}

FRAMEWORKS DETECTED BY LANGEXTRACT:
{langextract_frameworks}

NEO4J FRAMEWORK DETAILS:
{neo4j_frameworks}

For each framework used, assess:

1. **PROPER APPLICATION**: Was it used correctly per methodology?
2. **COMMON MISTAKES**: Did they make typical errors?
3. **INTEGRATION**: How well does it connect with other frameworks?
4. **MISSING FRAMEWORKS**: What should they have used?

Return JSON:
{{
    "framework_validation_complete": true,
    "frameworks_used": [
        {{
            "name": "Framework name",
            "properly_applied": true/false,
            "application_score": X.X,
            "mistakes_made": ["mistake 1"],
            "integration_quality": "excellent/good/poor"
        }}
    ],
    "frameworks_missing": [
        {{
            "name": "Framework they should have used",
            "why_needed": "Reason for this domain",
            "impact_of_missing": "What they lose by not using it"
        }}
    ],
    "overall_framework_score": X.X
}}

Return ONLY valid JSON."""


# ==============================================================================
# COMPREHENSIVE GRADING REPORT PROMPT
# ==============================================================================

FULL_GRADING_REPORT_PROMPT = """Generate the complete grading report based on all analyses.

BIAS DETECTION RESULTS:
{bias_results}

DOMAIN ANALYSIS RESULTS:
{domain_results}

FRAMEWORK VALIDATION RESULTS:
{framework_results}

PROBLEM EXTRACTION RESULTS:
{problem_results}

EVIDENCE QUALITY RESULTS:
{evidence_results}

NEO4J INSIGHTS:
{neo4j_insights}

Generate the FULL grading report following this EXACT format:

---

## FINAL GRADE: [Letter Grade] ([Score]/100)

**One-Line Verdict:** [Whether they found real problems worth solving]

---

### GRADE BREAKDOWN

| Component | Weight | Score | Points | Brief Assessment |
|-----------|--------|-------|---------|-----------------|
| **Problem Reality (Is it Real?)** | 35% | X/10 | XX.X | [Evidence quality] |
| **Problem Discovery** | 25% | X/10 | XX.X | [# problems found] |
| **Framework Integration** | 20% | X/10 | XX.X | [Tools used properly] |
| **Mindrian Thinking** | 10% | X/10 | XX.X | [Hidden connections] |
| **Can We Win?** | 5% | X/10 | X.X | [Basic capability check] |
| **Is it Worth It?** | 5% | X/10 | X.X | [Basic market size] |
| **TOTAL** | **100%** | - | **XX.X** | **[Letter Grade]** |

---

### COGNITIVE BIAS ANALYSIS

| Bias Name | Detected | Confidence | Risk Level | Mitigation |
|-----------|----------|------------|------------|------------|
[Table from bias detection]

**Flagged Claims Requiring Validation:**
- [List from bias results]

---

### PROBLEM REALITY VALIDATION (35% - Most Critical)

**"Is it Real?" Deep Dive:**

| Validation Criteria | Expected | Delivered | Score | Evidence Quality |
|-------------------|----------|-----------|-------|-----------------|
| **User Pain Evidence** | Direct quotes | [What provided] | X/10 | [Quality] |
| **Problem Frequency** | Data | [What provided] | X/10 | [Quality] |
| **Current Solutions Gap** | Analysis | [What provided] | X/10 | [Quality] |
| **Root Cause Analysis** | Why exists | [What provided] | X/10 | [Quality] |

**Reality Check:**
- **Validated Problems:** [List]
- **Assumed Problems:** [List]
- **Fantasy Problems:** [List]

---

### PROBLEM DISCOVERY ANALYSIS (25%)

**Discovery Funnel:**
```
Domain: [Space explored]
    |
Problems Identified: [#]
    |
Validated as Real: [#] (X%)
    |
Worth Pursuing: [#]
```

---

### FRAMEWORK INTEGRATION (20%)

**Tools Usage:**

| Framework Type | Expected | Used | Effectiveness |
|---------------|----------|------|---------------|
| Problem Finding | JTBD, TTA | [Used] | X/10 |
| Problem Validation | 5 Whys, Mom Test | [Used] | X/10 |
| Problem Framing | PWS, MECE | [Used] | X/10 |

**Missing Tools:** [From Neo4j analysis]

---

### MINDRIAN_BRAIN THINKING (10%)

**Hidden Connections:**
- **Found:** [What they identified]
- **Missed:** [From Neo4j]
- **Problem Space Coverage:** X%

---

### PRIORITY RECOMMENDATIONS

1. **[Action 1]** using [Tool]
2. **[Action 2]** using [Tool]
3. **[Action 3]** using [Tool]

---

### JSON HANDOFF

```json
[Full JSON following GRADING_JSON_TEMPLATE]
```

---

Provide the complete report with all sections filled in based on the analysis data."""


# ==============================================================================
# QUALITY ASSURANCE METRICS
# ==============================================================================

QUALITY_THRESHOLDS = {
    "bias_detection_confidence": 0.75,  # Minimum required
    "domain_analysis_completeness": 0.85,
    "neo4j_integration_score": 0.80,
    "framework_adherence": 0.85,
    "evidence_quality_score": 0.70,
    "overall_assessment_confidence": 0.80,
}

QUALITY_VALIDATION_PROMPT = """Validate the quality of this grading assessment.

ASSESSMENT RESULTS:
{assessment_results}

Check against quality thresholds:
- Bias Detection Confidence: >= 75% (MANDATORY)
- Domain Analysis Completeness: >= 85%
- Neo4j Integration: >= 80%
- Framework Adherence: >= 85%
- Evidence Quality: >= 70%
- Overall Confidence: >= 80%

Return JSON:
{{
    "quality_validation_complete": true,
    "thresholds_met": {{
        "bias_detection": {{"score": 0.XX, "passed": true/false}},
        "domain_analysis": {{"score": 0.XX, "passed": true/false}},
        "neo4j_integration": {{"score": 0.XX, "passed": true/false}},
        "framework_adherence": {{"score": 0.XX, "passed": true/false}},
        "evidence_quality": {{"score": 0.XX, "passed": true/false}},
        "overall_confidence": {{"score": 0.XX, "passed": true/false}}
    }},
    "all_thresholds_passed": true/false,
    "blocking_issues": ["Issue 1 if any"],
    "assessment_valid": true/false
}}

Return ONLY valid JSON."""
