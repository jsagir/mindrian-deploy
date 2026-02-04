"""
generate_personas.py — Expert Persona Generation Engine
=========================================================
Pipeline Stage 3: Create domain-specific expert personas with competency
matrices, research approaches, Tavily query strategies, collaboration styles,
and perspective traits.

Implements the Genesis Engine's Persona Generator logic. Uses expertise-based
naming (never real names) and generates full persona profiles for downstream
research orchestration.

Usage:
    python scripts/generate_personas.py domains.json decomposition.json [personas.json]

Input:
    domains.json from identify_domains.py (Stage 2 output)
    decomposition.json from decompose_context.py (Stage 1 output, for complexity)

Output:
    personas.json with array of expert persona objects
"""

import json
import sys
import argparse
from datetime import datetime


# =============================================================================
# TECHNICAL COMPETENCY LOOKUP
# =============================================================================

TECHNICAL_COMPETENCIES = {
    "Machine-Learning": [
        "model architecture design", "optimization algorithms",
        "evaluation metrics", "deployment pipelines", "feature engineering",
    ],
    "Quantum-Computing": [
        "circuit design", "gate operations", "error mitigation",
        "hardware constraints", "quantum advantage assessment",
    ],
    "Blockchain": [
        "consensus mechanisms", "smart contract design",
        "cryptographic protocols", "scalability solutions", "security auditing",
    ],
    "Biotechnology": [
        "experimental design", "genomic analysis", "regulatory compliance",
        "lab techniques", "bioinformatics",
    ],
    "Natural-Language-Processing": [
        "tokenization strategies", "embedding techniques",
        "model fine-tuning", "evaluation benchmarks", "RAG architectures",
    ],
    "Data-Engineering": [
        "pipeline architecture", "data quality assurance",
        "performance optimization", "schema design", "monitoring systems",
    ],
    "Cybersecurity": [
        "threat modeling", "vulnerability assessment",
        "incident response", "security architecture", "compliance frameworks",
    ],
    "Cloud-Architecture": [
        "service design", "scalability patterns",
        "cost optimization", "security implementation", "disaster recovery",
    ],
    "FinTech": [
        "risk modeling", "regulatory technology",
        "payment system design", "portfolio optimization", "fraud detection",
    ],
    "Infrastructure-Finance": [
        "project finance modeling", "blended finance structuring",
        "sovereign risk assessment", "concession negotiation", "PPP frameworks",
    ],
    "Geopolitical-Infrastructure": [
        "corridor analysis", "trade route economics",
        "bilateral agreement assessment", "customs optimization",
        "sovereignty risk mapping",
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
    "Neuroscience": [
        "neural imaging analysis", "cognitive assessment design",
        "neuroplasticity research", "behavioral experimentation",
        "brain-computer interface protocols",
    ],
}


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def create_persona(domain: dict, persona_type: str, depth: str) -> dict:
    """
    Create a single expert persona for a domain.

    Builds expertise-based name, competency matrix, research approach,
    query strategies, collaboration style, perspective traits, and
    output expectations.

    Args:
        domain: Domain analysis dict with domain name, indicators, subdomains.
        persona_type: One of PRIMARY, SUBDOMAIN, METHODOLOGY, INTEGRATION.
        depth: One of SPECIALIST, EXPERT, AUTHORITY.

    Returns:
        Complete persona dict.
    """
    depth_label = {
        "SPECIALIST": "Specialist",
        "EXPERT": "Expert",
        "AUTHORITY": "Authority",
    }

    # Build name
    domain_name = domain.get("name", domain.get("domain", "General-Systems"))
    parent_domain = domain.get("parentDomain", "")

    if persona_type == "SUBDOMAIN" and parent_domain:
        name = f"{domain_name}-{parent_domain}-{depth_label[depth]}"
    else:
        name = f"{domain_name}-{depth_label[depth]}"

    # Competencies
    lookup_key = parent_domain or domain_name
    tech_comps = TECHNICAL_COMPETENCIES.get(
        lookup_key,
        ["systems analysis", "technical implementation",
         "performance optimization", "quality assurance"]
    )

    confidence = domain.get("confidence", 0.5)
    if confidence > 0.7:
        method_comps = [
            "systematic experimentation", "hypothesis-driven research",
            "iterative refinement", "evidence-based decision making",
            "breakthrough identification",
        ]
    else:
        method_comps = [
            "exploratory analysis", "comparative evaluation",
            "feasibility assessment", "risk-benefit analysis",
        ]

    analytical_base = ["data analysis", "pattern recognition", "logical reasoning"]
    type_analytical = {
        "PRIMARY": ["domain modeling", "trend analysis", "competitive analysis"],
        "SUBDOMAIN": ["deep technical analysis", "specialized proficiency", "niche expertise"],
        "INTEGRATION": ["systems analysis", "cross-functional mapping", "synergy identification"],
        "METHODOLOGY": ["process analysis", "quality assessment", "rigor evaluation"],
    }
    depth_analytical = {
        "SPECIALIST": ["focused analysis", "detailed examination"],
        "EXPERT": ["comprehensive analysis", "strategic assessment"],
        "AUTHORITY": ["paradigm analysis", "future forecasting"],
    }

    # Research approach
    research_approaches = {
        "SPECIALIST": {
            "primary": "Deep-dive investigation within specialized domain boundaries",
            "methods": [
                "Targeted literature search", "Specific case study analysis",
                "Narrow technical deep dives", "Tool-specific exploration",
            ],
        },
        "EXPERT": {
            "primary": "Comprehensive domain exploration with adjacent area integration",
            "methods": [
                "Systematic domain review", "Comparative methodology analysis",
                "Trend identification and projection", "Best practice synthesis",
            ],
        },
        "AUTHORITY": {
            "primary": "Frontier-pushing research at paradigm boundaries",
            "methods": [
                "Breakthrough opportunity identification",
                "Paradigm-challenging investigation",
                "Future technology forecasting", "Revolutionary approach design",
            ],
        },
    }

    # Query strategies
    year = datetime.utcnow().year
    base_queries = [
        f'"{domain_name}" breakthrough research {year} {year + 1}',
        f'"{domain_name}" cutting edge developments patent application',
        f'"{domain_name}" novel approach startup innovation funding',
    ]

    if persona_type == "SUBDOMAIN" and parent_domain:
        queries = base_queries + [
            f'"{domain_name}" advances in "{parent_domain}" {year}',
            f'integrate "{domain_name}" new methodology "{parent_domain}"',
            f'"{domain_name}" paradigm shift technical breakthrough',
        ]
    elif persona_type == "PRIMARY":
        queries = base_queries + [
            f'"{domain_name}" paradigm shift recent advances review',
            f'overcome "{domain_name}" limitations new method {year}',
            f'"{domain_name}" unexpected applications breakthrough',
            f'revolutionary "{domain_name}" approach peer reviewed',
        ]
    else:
        queries = base_queries

    # Collaboration style
    if persona_type == "PRIMARY":
        collab_styles = {
            "SPECIALIST": {"role": "DOMAIN_CONTRIBUTOR",
                           "approach": "Provides focused domain insights and technical validation"},
            "EXPERT": {"role": "DOMAIN_ADVISOR",
                       "approach": "Guides domain-specific decisions and validates approaches"},
            "AUTHORITY": {"role": "DOMAIN_LEADER",
                          "approach": "Sets domain research direction and identifies breakthroughs"},
        }
        collab = collab_styles[depth]
    elif persona_type == "SUBDOMAIN":
        collab = {"role": "TECHNICAL_SPECIALIST",
                  "approach": "Provides deep technical insights and specialized knowledge"}
    elif persona_type == "METHODOLOGY":
        collab = {"role": "PROCESS_GUARDIAN",
                  "approach": "Ensures research quality and methodological soundness"}
    else:
        collab = {"role": "SYNTHESIS_LEADER",
                  "approach": "Drives cross-domain connections and breakthrough identification"}

    # Perspective traits
    focus_map = {
        "PRIMARY": "domain_excellence",
        "SUBDOMAIN": "technical_precision",
        "INTEGRATION": "breakthrough_synthesis",
        "METHODOLOGY": "quality_assurance",
    }
    bias_map = {
        "PRIMARY": "domain_advocacy",
        "SUBDOMAIN": "detail_orientation",
        "INTEGRATION": "possibility_thinking",
        "METHODOLOGY": "process_focus",
    }
    blindspot_map = {
        "PRIMARY": "cross_domain_opportunities",
        "SUBDOMAIN": "bigger_picture",
        "INTEGRATION": "implementation_details",
        "METHODOLOGY": "innovation_potential",
    }

    # Output expectations
    base_outputs = [
        "3-5 key insights from domain perspective",
        "Evidence-based recommendations",
        "Risk and limitation assessment",
    ]
    type_outputs = {
        "PRIMARY": ["Domain-specific breakthrough opportunities",
                     "Competitive landscape analysis"],
        "SUBDOMAIN": ["Technical deep-dive findings",
                       "Specialized implementation guidance"],
        "INTEGRATION": ["Cross-domain synergies",
                        "Emergent breakthrough pathways"],
        "METHODOLOGY": ["Research quality assessment",
                        "Methodological recommendations"],
    }
    depth_outputs = {
        "SPECIALIST": ["Detailed technical validations"],
        "EXPERT": ["Strategic recommendations"],
        "AUTHORITY": ["Paradigm shift opportunities"],
    }

    return {
        "name": name,
        "primaryExpertise": domain_name,
        "expertiseDepth": depth,
        "domainCategory": persona_type,
        "confidence": confidence,
        "competencies": {
            "core": domain.get("indicators", []),
            "technical": tech_comps,
            "methodological": method_comps,
            "analytical": (analytical_base +
                           type_analytical.get(persona_type, []) +
                           depth_analytical.get(depth, [])),
        },
        "researchApproach": research_approaches.get(depth, research_approaches["EXPERT"]),
        "queryStrategies": queries,
        "collaborationStyle": collab,
        "perspectiveTraits": {
            "focus": focus_map.get(persona_type, "domain_excellence"),
            "bias": bias_map.get(persona_type, "domain_advocacy"),
            "blindSpot": blindspot_map.get(persona_type, "cross_domain_opportunities"),
            "confidence": confidence,
        },
        "outputExpectations": (base_outputs +
                               type_outputs.get(persona_type, []) +
                               depth_outputs.get(depth, [])),
    }


def create_methodology_expert(method_domain: dict) -> dict:
    """
    Create a specialized methodology validation expert.

    Args:
        method_domain: Methodological domain dict with indicators.

    Returns:
        Methodology expert persona dict.
    """
    return {
        "name": "Research-Methodology-Integration-Expert",
        "primaryExpertise": "Cross-Domain Research Methodology",
        "expertiseDepth": "EXPERT",
        "domainCategory": "METHODOLOGY",
        "confidence": method_domain.get("confidence", 0.6),
        "competencies": {
            "core": method_domain.get("indicators", [])[:10],
            "technical": ["systematic review", "meta-analysis",
                          "experimental design", "statistical analysis"],
            "methodological": ["hypothesis formulation", "variable control",
                               "data validation", "result interpretation"],
            "analytical": ["pattern recognition", "causal inference",
                           "correlation analysis"],
        },
        "researchApproach": {
            "primary": "Methodological rigor and cross-domain validation",
            "methods": [
                "Systematic literature review",
                "Methodological framework comparison",
                "Best practice identification",
                "Validation protocol design",
            ],
        },
        "queryStrategies": [
            '"research methodology" breakthrough interdisciplinary',
            '"systematic approach" innovation "cross-domain"',
            "methodological framework cutting edge research",
            '"experimental design" novel approach',
        ],
        "collaborationStyle": {
            "role": "METHODOLOGY_VALIDATOR",
            "approach": "Ensures research rigor and methodological soundness across domains",
        },
        "perspectiveTraits": {
            "focus": "methodological_integrity",
            "bias": "process_over_outcome",
            "blindSpot": "domain_specific_nuances",
        },
        "outputExpectations": [
            "Methodological assessment of proposed approaches",
            "Cross-domain validation frameworks",
            "Research design recommendations",
            "Quality assurance protocols",
        ],
    }


def create_integration_architect(primary_domains: list) -> dict:
    """
    Create a cross-domain integration expert.

    Bridges all primary domains, focused on emergent breakthroughs and
    synergy identification.

    Args:
        primary_domains: List of primary domain dicts.

    Returns:
        Integration architect persona dict.
    """
    domain_names = [d["domain"] for d in primary_domains]
    name_str = "-".join(domain_names[:3])
    all_indicators = []
    for d in primary_domains:
        all_indicators.extend(d.get("indicators", []))

    # Build integration-specific queries
    if len(domain_names) == 2:
        queries = [
            f'"{domain_names[0]}" AND "{domain_names[1]}" convergence breakthrough',
            f'integrate "{domain_names[0]}" "{domain_names[1]}" novel approach',
            f'cross-pollination "{domain_names[0]}" "{domain_names[1]}" innovation',
            f'bridge "{domain_names[0]}" and "{domain_names[1]}" research',
            f'"{domain_names[0]}" meets "{domain_names[1]}" startup success',
        ]
    else:
        queries = [
            f'{" AND ".join(f""""{d}""" for d in domain_names[:3])} convergence innovation',
            f'multi-domain integration {" ".join(domain_names[:3])} breakthrough',
            f'cross-functional synergy {" ".join(domain_names[:3])}',
            f'interdisciplinary breakthrough {" ".join(f""""{d}""" for d in domain_names[:3])}',
        ]

    return {
        "name": f"{name_str}-Integration-Architect",
        "primaryExpertise": "Cross-Domain Integration and Breakthrough Synthesis",
        "expertiseDepth": "AUTHORITY",
        "domainCategory": "INTEGRATION",
        "confidence": 0.95,
        "competencies": {
            "core": ["systems thinking", "pattern recognition",
                     "synthesis", "integration", "emergence"],
            "technical": list(set(all_indicators))[:10],
            "methodological": ["comparative analysis", "gap bridging",
                               "synergy identification", "integration mapping"],
            "analytical": ["cross-domain pattern matching",
                           "emergent property identification",
                           "synergy quantification"],
        },
        "researchApproach": {
            "primary": "Identify breakthrough connections between domains",
            "methods": [
                "Cross-domain pattern matching",
                "Synergy opportunity analysis",
                "Integration pathway mapping",
                "Breakthrough potential assessment",
                "Emergent property identification",
            ],
        },
        "queryStrategies": queries,
        "collaborationStyle": {
            "role": "SYNTHESIS_ORCHESTRATOR",
            "approach": "Facilitates cross-domain insights, identifies integration "
                        "opportunities, drives breakthrough thinking",
        },
        "perspectiveTraits": {
            "focus": "emergent_breakthroughs",
            "bias": "integration_optimist",
            "blindSpot": "implementation_complexity",
        },
        "outputExpectations": [
            "Cross-domain breakthrough opportunities (3-5)",
            "Integration pathway recommendations",
            "Synergy quantification metrics",
            "Emergent property identification",
            "Implementation roadmap with milestones",
        ],
    }


def generate_personas(domain_map: dict, complexity: dict) -> list:
    """
    Full persona generation pipeline.

    Generates:
    - One PRIMARY expert per primary domain
    - SUBDOMAIN specialists for high-confidence subdomains
    - METHODOLOGY expert if methodological indicators present
    - INTEGRATION ARCHITECT if 2+ primary domains

    Args:
        domain_map: Output from identify_domains.py (Stage 2).
        complexity: Complexity dict from Stage 1 decomposition.

    Returns:
        List of expert persona dicts.
    """
    print(f"\n👥 EXPERT PERSONA GENERATION ENGINE")
    depth = complexity.get("depthRequired", "EXPERT")
    domains = domain_map["domains"]

    personas = []

    # Primary domain experts
    for d in domains["primary"]:
        persona = create_persona(d, "PRIMARY", depth)
        personas.append(persona)
        print(f"  ✅ Generated: {persona['name']}")

    # Subdomain specialists
    for d in domains["technical"]:
        for sub in d.get("subdomains", []):
            if sub.get("confidence", 0) > 0.5:
                sub_domain = {
                    "domain": d["domain"],
                    "name": sub["name"],
                    "indicators": sub.get("indicator_terms", []),
                    "parentDomain": d["domain"],
                    "confidence": sub["confidence"],
                }
                persona = create_persona(sub_domain, "SUBDOMAIN", depth)
                personas.append(persona)
                print(f"  ✅ Generated: {persona['name']}")

    # Also check primary domains for subdomains
    for d in domains["primary"]:
        for sub in d.get("subdomains", []):
            if sub.get("confidence", 0) > 0.5:
                sub_domain = {
                    "domain": d["domain"],
                    "name": sub["name"],
                    "indicators": sub.get("indicator_terms", []),
                    "parentDomain": d["domain"],
                    "confidence": sub["confidence"],
                }
                persona = create_persona(sub_domain, "SUBDOMAIN", depth)
                personas.append(persona)
                print(f"  ✅ Generated: {persona['name']}")

    # Methodology expert
    if domains["methodological"]:
        method_expert = create_methodology_expert(domains["methodological"][0])
        personas.append(method_expert)
        print(f"  ✅ Generated: {method_expert['name']}")

    # Integration architect
    if len(domains["primary"]) > 1:
        integration_expert = create_integration_architect(domains["primary"])
        personas.append(integration_expert)
        print(f"  ✅ Generated: {integration_expert['name']}")

    print(f"\n✅ Persona generation complete: {len(personas)} experts generated\n")
    return personas


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Genesis Persona Generator — Stage 3 of Expert Breakdown Pipeline"
    )
    parser.add_argument(
        "domains_input",
        help="Domains JSON from Stage 2 (domains.json)"
    )
    parser.add_argument(
        "decomposition_input",
        help="Decomposition JSON from Stage 1 (decomposition.json)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="personas.json",
        help="Output JSON path (default: personas.json)"
    )
    args = parser.parse_args()

    # Load inputs with error handling
    try:
        with open(args.domains_input, "r", encoding="utf-8") as f:
            domain_map = json.load(f)
    except FileNotFoundError:
        print(f"Error: Domain map not found: {args.domains_input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.domains_input}: {e}")
        sys.exit(1)

    try:
        with open(args.decomposition_input, "r", encoding="utf-8") as f:
            decomposition = json.load(f)
    except FileNotFoundError:
        print(f"Error: Decomposition not found: {args.decomposition_input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.decomposition_input}: {e}")
        sys.exit(1)

    # Validate required keys
    if "domains" not in domain_map:
        raise ValueError(
            "Domain map missing 'domains' key. "
            "Expected output from identify_domains.py (Stage 2)."
        )
    if "complexity" not in decomposition:
        raise ValueError(
            "Decomposition missing 'complexity' key. "
            "Expected output from decompose_context.py (Stage 1)."
        )

    print(f"Loaded domains from {args.domains_input}")
    print(f"Loaded decomposition from {args.decomposition_input}")

    # Generate personas
    personas = generate_personas(domain_map, decomposition["complexity"])

    # Save
    output = {
        "personas": personas,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "persona_count": len(personas),
            "depth_required": decomposition["complexity"]["depthRequired"],
            "primary_domains": len(domain_map["domains"]["primary"]),
        },
    }

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Error: Could not write to {args.output}: {e}")
        sys.exit(1)

    print(f"Saved personas to {args.output}")
    return output


if __name__ == "__main__":
    main()
