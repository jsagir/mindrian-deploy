"""
Stage 3: Persona Generation with BONO Six Hats
==============================================
Create domain expert personas enriched with Six Thinking Hats perspectives.

Each persona has:
- Domain expertise (from Genesis)
- Six Hats perspective assignment (from BONO)
- Competencies, query strategies, collaboration style
"""

from datetime import datetime
from typing import Dict, List, Any


# =============================================================================
# BONO SIX THINKING HATS
# =============================================================================

SIX_HATS = {
    "WHITE": {
        "name": "White Hat",
        "focus": "Facts and Information",
        "mode": "objective_data",
        "questions": [
            "What data do we have?",
            "What information is missing?",
            "What are the verified facts?",
        ],
        "perspective_bias": "information_seeking",
        "blind_spot": "emotional_factors",
    },
    "RED": {
        "name": "Red Hat",
        "focus": "Emotions and Intuition",
        "mode": "gut_feeling",
        "questions": [
            "What does your intuition say?",
            "How does this make you feel?",
            "What's your immediate reaction?",
        ],
        "perspective_bias": "emotional_response",
        "blind_spot": "logical_analysis",
    },
    "BLACK": {
        "name": "Black Hat",
        "focus": "Caution and Critical Thinking",
        "mode": "risk_assessment",
        "questions": [
            "What could go wrong?",
            "What are the weaknesses?",
            "Why might this fail?",
        ],
        "perspective_bias": "risk_identification",
        "blind_spot": "opportunity_recognition",
    },
    "YELLOW": {
        "name": "Yellow Hat",
        "focus": "Optimism and Benefits",
        "mode": "value_seeking",
        "questions": [
            "What are the benefits?",
            "What's the best-case scenario?",
            "Why will this succeed?",
        ],
        "perspective_bias": "opportunity_focus",
        "blind_spot": "risk_awareness",
    },
    "GREEN": {
        "name": "Green Hat",
        "focus": "Creativity and Alternatives",
        "mode": "creative_thinking",
        "questions": [
            "What alternatives exist?",
            "How might we do this differently?",
            "What if we combined approaches?",
        ],
        "perspective_bias": "innovation_seeking",
        "blind_spot": "practical_constraints",
    },
    "BLUE": {
        "name": "Blue Hat",
        "focus": "Process and Organization",
        "mode": "meta_thinking",
        "questions": [
            "What's the next step?",
            "How should we structure this?",
            "What have we concluded?",
        ],
        "perspective_bias": "process_focus",
        "blind_spot": "content_depth",
    },
}


# =============================================================================
# TECHNICAL COMPETENCIES
# =============================================================================

TECHNICAL_COMPETENCIES = {
    "Machine-Learning": [
        "model architecture design", "optimization algorithms",
        "evaluation metrics", "deployment pipelines", "feature engineering",
    ],
    "Natural-Language-Processing": [
        "tokenization strategies", "embedding techniques",
        "model fine-tuning", "evaluation benchmarks", "RAG architectures",
    ],
    "Blockchain": [
        "consensus mechanisms", "smart contract design",
        "cryptographic protocols", "scalability solutions", "security auditing",
    ],
    "FinTech": [
        "risk modeling", "regulatory technology",
        "payment system design", "portfolio optimization", "fraud detection",
    ],
    "Climate-Tech": [
        "carbon accounting", "renewable system design",
        "ESG assessment", "lifecycle analysis", "green finance",
    ],
    "HealthTech": [
        "clinical trial design", "FDA regulatory pathways",
        "digital health architecture", "HIPAA compliance", "outcomes measurement",
    ],
    "EdTech": [
        "adaptive learning algorithms", "LMS architecture",
        "pedagogical assessment", "engagement measurement", "curriculum design",
    ],
    # Default
    "General-Systems": [
        "systems analysis", "technical implementation",
        "performance optimization", "quality assurance", "integration design",
    ],
}


def assign_hats_to_domains(domains: List[Dict]) -> Dict[str, str]:
    """
    Assign Six Hats to domains based on their characteristics.

    Strategy:
    - Primary domains get diverse hats (WHITE, YELLOW, GREEN)
    - Technical domains get analytical hats (WHITE, BLACK)
    - Integration architect always gets BLUE (process)
    - Methodology expert always gets WHITE (facts)
    """
    assignments = {}
    hat_pool = ["WHITE", "YELLOW", "GREEN", "BLACK", "RED"]
    hat_index = 0

    for domain in domains:
        domain_name = domain.get("domain", "General")

        # Special assignments
        if "Integration" in domain_name:
            assignments[domain_name] = "BLUE"
        elif "Methodology" in domain_name:
            assignments[domain_name] = "WHITE"
        elif domain.get("technical"):
            # Technical domains alternate between WHITE and BLACK
            assignments[domain_name] = "WHITE" if hat_index % 2 == 0 else "BLACK"
        else:
            # Cycle through hat pool
            assignments[domain_name] = hat_pool[hat_index % len(hat_pool)]

        hat_index += 1

    return assignments


def enrich_with_bono_hats(persona: Dict, hat_color: str) -> Dict:
    """
    Enrich a persona with Six Thinking Hats perspective.

    Adds:
    - thinking_hat: Full hat configuration
    - hat_questions: Questions this persona should ask
    - enriched_perspective: Combined domain + hat perspective
    """
    hat = SIX_HATS.get(hat_color, SIX_HATS["WHITE"])

    # Merge perspectives
    original_focus = persona.get("perspectiveTraits", {}).get("focus", "domain_excellence")
    original_bias = persona.get("perspectiveTraits", {}).get("bias", "domain_advocacy")

    enriched_perspective = {
        "domain_focus": original_focus,
        "domain_bias": original_bias,
        "hat_mode": hat["mode"],
        "hat_bias": hat["perspective_bias"],
        "combined_blind_spots": [
            persona.get("perspectiveTraits", {}).get("blindSpot", "unknown"),
            hat["blind_spot"],
        ],
    }

    # Add hat-specific query strategies
    hat_queries = []
    domain_name = persona.get("primaryExpertise", "General")
    for q in hat["questions"]:
        hat_queries.append(f'"{domain_name}" {q.lower().replace("?", "")}')

    return {
        **persona,
        "thinking_hat": {
            "color": hat_color,
            "name": hat["name"],
            "focus": hat["focus"],
            "mode": hat["mode"],
        },
        "hat_questions": hat["questions"],
        "enriched_perspective": enriched_perspective,
        "query_strategies_with_hat": persona.get("queryStrategies", []) + hat_queries,
    }


def create_persona(
    domain: Dict,
    persona_type: str,
    depth: str,
    hat_color: str = None
) -> Dict:
    """
    Create a single expert persona.

    Args:
        domain: Domain analysis dict
        persona_type: PRIMARY, SUBDOMAIN, METHODOLOGY, INTEGRATION
        depth: SPECIALIST, EXPERT, AUTHORITY
        hat_color: Optional Six Hat color assignment
    """
    depth_label = {
        "SPECIALIST": "Specialist",
        "EXPERT": "Expert",
        "AUTHORITY": "Authority",
    }

    # Build name (expertise-based, never real names)
    domain_name = domain.get("name", domain.get("domain", "General-Systems"))
    parent_domain = domain.get("parentDomain", "")

    if persona_type == "SUBDOMAIN" and parent_domain:
        name = f"{domain_name}-{parent_domain}-{depth_label[depth]}"
    elif persona_type == "INTEGRATION":
        name = f"Cross-Domain-Integration-{depth_label[depth]}"
    elif persona_type == "METHODOLOGY":
        name = f"Research-Methodology-{depth_label[depth]}"
    else:
        name = f"{domain_name}-{depth_label[depth]}"

    # Competencies
    lookup_key = parent_domain or domain_name
    tech_comps = TECHNICAL_COMPETENCIES.get(
        lookup_key,
        TECHNICAL_COMPETENCIES["General-Systems"]
    )

    confidence = domain.get("confidence", 0.5)

    # Research approach based on depth
    research_approaches = {
        "SPECIALIST": {
            "primary": "Deep-dive investigation within specialized domain",
            "methods": [
                "Targeted literature search",
                "Specific case study analysis",
                "Technical deep dives",
            ],
        },
        "EXPERT": {
            "primary": "Comprehensive domain exploration with adjacent integration",
            "methods": [
                "Systematic domain review",
                "Comparative methodology analysis",
                "Trend identification",
            ],
        },
        "AUTHORITY": {
            "primary": "Frontier-pushing research at paradigm boundaries",
            "methods": [
                "Breakthrough opportunity identification",
                "Paradigm-challenging investigation",
                "Future technology forecasting",
            ],
        },
    }

    # Query strategies
    year = datetime.utcnow().year
    queries = [
        f'"{domain_name}" breakthrough research {year}',
        f'"{domain_name}" cutting edge developments',
        f'"{domain_name}" novel approach innovation',
    ]

    # Collaboration style
    collab_styles = {
        "PRIMARY": {
            "role": "DOMAIN_EXPERT",
            "approach": "Provides focused domain insights and validates approaches",
        },
        "SUBDOMAIN": {
            "role": "TECHNICAL_SPECIALIST",
            "approach": "Provides deep technical insights and specialized knowledge",
        },
        "METHODOLOGY": {
            "role": "PROCESS_GUARDIAN",
            "approach": "Ensures research quality and methodological soundness",
        },
        "INTEGRATION": {
            "role": "SYNTHESIS_ORCHESTRATOR",
            "approach": "Drives cross-domain connections and breakthrough identification",
        },
    }

    persona = {
        "name": name,
        "primaryExpertise": domain_name,
        "expertiseDepth": depth,
        "domainCategory": persona_type,
        "confidence": confidence,
        "competencies": {
            "core": domain.get("indicators", []),
            "technical": tech_comps,
            "methodological": [
                "systematic analysis", "hypothesis-driven research",
                "evidence-based decision making",
            ],
        },
        "researchApproach": research_approaches.get(depth, research_approaches["EXPERT"]),
        "queryStrategies": queries,
        "collaborationStyle": collab_styles.get(persona_type, collab_styles["PRIMARY"]),
        "perspectiveTraits": {
            "focus": f"{persona_type.lower()}_excellence",
            "bias": f"{persona_type.lower()}_advocacy",
            "blindSpot": "cross_domain_opportunities" if persona_type != "INTEGRATION" else "implementation_details",
        },
        "outputExpectations": [
            "3-5 key insights from domain perspective",
            "Evidence-based recommendations",
            "Risk and limitation assessment",
        ],
    }

    # Enrich with Six Hat if assigned
    if hat_color:
        persona = enrich_with_bono_hats(persona, hat_color)

    return persona


def create_integration_architect(primary_domains: List[Dict], depth: str) -> Dict:
    """Create a cross-domain integration expert."""
    domain_names = [d["domain"] for d in primary_domains]
    all_indicators = []
    for d in primary_domains:
        all_indicators.extend(d.get("indicators", []))

    # Integration-specific queries
    if len(domain_names) >= 2:
        queries = [
            f'"{domain_names[0]}" AND "{domain_names[1]}" convergence breakthrough',
            f'integrate "{domain_names[0]}" "{domain_names[1]}" novel approach',
            f'cross-pollination "{domain_names[0]}" "{domain_names[1]}" innovation',
        ]
    else:
        queries = ["multi-domain integration breakthrough", "cross-functional synergy"]

    persona = {
        "name": f"Integration-Architect-{'-'.join(domain_names[:2])}-Authority",
        "primaryExpertise": "Cross-Domain Integration",
        "expertiseDepth": "AUTHORITY",
        "domainCategory": "INTEGRATION",
        "confidence": 0.95,
        "competencies": {
            "core": ["systems thinking", "pattern recognition", "synthesis", "emergence"],
            "technical": list(set(all_indicators))[:10],
            "methodological": ["comparative analysis", "synergy identification", "integration mapping"],
        },
        "researchApproach": {
            "primary": "Identify breakthrough connections between domains",
            "methods": [
                "Cross-domain pattern matching",
                "Synergy opportunity analysis",
                "Breakthrough potential assessment",
            ],
        },
        "queryStrategies": queries,
        "collaborationStyle": {
            "role": "SYNTHESIS_ORCHESTRATOR",
            "approach": "Facilitates cross-domain insights, identifies integration opportunities",
        },
        "perspectiveTraits": {
            "focus": "emergent_breakthroughs",
            "bias": "integration_optimist",
            "blindSpot": "implementation_complexity",
        },
        "outputExpectations": [
            "Cross-domain breakthrough opportunities",
            "Integration pathway recommendations",
            "Synergy quantification",
        ],
    }

    # Integration architect gets BLUE hat (process/meta)
    return enrich_with_bono_hats(persona, "BLUE")


def generate_personas(
    domain_map: Dict,
    complexity: Dict,
    use_bono_hats: bool = True
) -> Dict[str, Any]:
    """
    Full persona generation pipeline with optional BONO enrichment.

    Args:
        domain_map: Output from identify_domains()
        complexity: Complexity dict from decompose()
        use_bono_hats: Whether to assign Six Thinking Hats

    Returns:
        Dict with personas list and metadata
    """
    depth = complexity.get("depthRequired", "EXPERT")
    domains = domain_map["domains"]

    personas = []

    # Assign hats to all domains
    all_domains = domains["primary"] + domains["technical"]
    hat_assignments = assign_hats_to_domains(all_domains) if use_bono_hats else {}

    # Primary domain experts
    for d in domains["primary"]:
        hat = hat_assignments.get(d["domain"]) if use_bono_hats else None
        persona = create_persona(d, "PRIMARY", depth, hat)
        personas.append(persona)

    # Subdomain specialists (from both primary and technical)
    for domain_list in [domains["primary"], domains["technical"]]:
        for d in domain_list:
            for sub in d.get("subdomains", []):
                if sub.get("confidence", 0) > 0.5:
                    sub_domain = {
                        "domain": d["domain"],
                        "name": sub["name"],
                        "indicators": sub.get("indicator_terms", []),
                        "parentDomain": d["domain"],
                        "confidence": sub["confidence"],
                    }
                    # Subdomains get parent's hat or WHITE
                    hat = hat_assignments.get(d["domain"], "WHITE") if use_bono_hats else None
                    persona = create_persona(sub_domain, "SUBDOMAIN", depth, hat)
                    personas.append(persona)

    # Methodology expert (if methodological indicators present)
    if domains["methodological"]:
        method_persona = create_persona(
            domains["methodological"][0],
            "METHODOLOGY",
            depth,
            "WHITE" if use_bono_hats else None  # Methodology gets WHITE (facts)
        )
        personas.append(method_persona)

    # Integration architect (if 2+ primary domains)
    if len(domains["primary"]) > 1:
        integration_persona = create_integration_architect(domains["primary"], depth)
        personas.append(integration_persona)

    return {
        "personas": personas,
        "hat_assignments": hat_assignments,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "persona_count": len(personas),
            "depth_required": depth,
            "bono_enriched": use_bono_hats,
            "primary_domains": len(domains["primary"]),
        }
    }
