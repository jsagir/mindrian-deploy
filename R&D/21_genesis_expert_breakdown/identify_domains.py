"""
identify_domains.py — Domain Identification Engine
=====================================================
Pipeline Stage 2: Pattern matching against domain signatures, subdomain
discovery, confidence scoring, and domain map generation.

Implements the Genesis Engine's Domain Identifier logic. Matches text segments
against 14 technical + 10 non-technical domain signatures, discovers subdomains
within high-confidence matches, and produces a categorized domain map.

Usage:
    python scripts/identify_domains.py decomposition.json [domains.json]

Input:
    decomposition.json from decompose_context.py (Stage 1 output)

Output:
    domains.json with primary[], technical[], adjacent[], methodological[]
"""

import json
import re
import sys
import argparse
from datetime import datetime


# =============================================================================
# DOMAIN PATTERN DEFINITIONS
# =============================================================================

DOMAIN_PATTERNS = {
    # --- Technical Domains (14) ---
    "Machine-Learning": re.compile(
        r'\b(neural|network|training|model|dataset|classification|regression|'
        r'deep learning|supervised|unsupervised|reinforcement|gradient|'
        r'backpropagation|epoch|batch|overfitting|hyperparameter|feature '
        r'engineering|random forest|xgboost|ensemble)\b', re.IGNORECASE
    ),
    "Quantum-Computing": re.compile(
        r'\b(quantum|qubit|superposition|entanglement|quantum gate|quantum '
        r'circuit|decoherence|quantum algorithm|quantum supremacy|quantum '
        r'advantage|annealing|topological)\b', re.IGNORECASE
    ),
    "Blockchain": re.compile(
        r'\b(blockchain|cryptocurrency|smart contract|consensus|distributed '
        r'ledger|mining|defi|web3|dao|nft|token|decentralized)\b', re.IGNORECASE
    ),
    "Biotechnology": re.compile(
        r'\b(genetic|dna|rna|protein|cell|organism|crispr|sequencing|'
        r'bioengineering|synthetic biology|gene therapy|bioinformatics|'
        r'genomic|proteomic|molecular)\b', re.IGNORECASE
    ),
    "Data-Engineering": re.compile(
        r'\b(pipeline|etl|data lake|streaming|batch|processing|warehouse|'
        r'kafka|spark|airflow|data mesh|lakehouse|dbt|data quality)\b',
        re.IGNORECASE
    ),
    "Cybersecurity": re.compile(
        r'\b(security|encryption|vulnerability|threat|authentication|'
        r'authorization|penetration|firewall|malware|zero trust|soc|'
        r'incident response|intrusion|ransomware)\b', re.IGNORECASE
    ),
    "Cloud-Architecture": re.compile(
        r'\b(cloud|serverless|microservice|container|kubernetes|scaling|aws|'
        r'azure|gcp|devops|infrastructure as code|terraform|helm)\b',
        re.IGNORECASE
    ),
    "Natural-Language-Processing": re.compile(
        r'\b(natural language|nlp|tokenization|embedding|transformer|bert|'
        r'gpt|sentiment|parsing|language model|llm|rag|fine-tuning|prompt)\b',
        re.IGNORECASE
    ),
    "Robotics": re.compile(
        r'\b(robot|actuator|sensor fusion|kinematics|control system|autonomous|'
        r'navigation|manipulation|ros|lidar|slam|end effector)\b', re.IGNORECASE
    ),
    "FinTech": re.compile(
        r'\b(fintech|trading|portfolio|risk management|derivative|market '
        r'making|liquidity|payment|banking|insurtech|regtech|neobank)\b',
        re.IGNORECASE
    ),
    "Computer-Vision": re.compile(
        r'\b(vision|image recognition|video|cnn|object detection|segmentation|'
        r'recognition|opencv|yolo|diffusion model|generative image)\b',
        re.IGNORECASE
    ),
    "IoT": re.compile(
        r'\b(iot|internet of things|edge computing|mqtt|embedded system|'
        r'arduino|raspberry pi|telemetry|digital twin|smart sensor)\b',
        re.IGNORECASE
    ),
    "AR-VR": re.compile(
        r'\b(augmented reality|virtual reality|mixed reality|metaverse|oculus|'
        r'hololens|spatial computing|xr|3d rendering)\b', re.IGNORECASE
    ),
    "DevOps": re.compile(
        r'\b(ci[\\/]?cd|continuous integration|deployment|docker|jenkins|gitlab|'
        r'monitoring|infrastructure|sre|observability|grafana|prometheus)\b',
        re.IGNORECASE
    ),

    # --- Non-Technical Domains (10) ---
    "Infrastructure-Finance": re.compile(
        r'\b(infrastructure finance|project finance|dfc|development finance|'
        r'sovereign bond|blended finance|concession|toll road|ppp|public '
        r'private partnership|infrastructure fund|capex)\b', re.IGNORECASE
    ),
    "Geopolitical-Infrastructure": re.compile(
        r'\b(geopolitic|corridor|trade route|belt and road|land bridge|'
        r'sovereignty|bilateral|diplomatic|customs|border|free trade zone|'
        r'strategic corridor|transit)\b', re.IGNORECASE
    ),
    "Sovereign-Wealth-Investment": re.compile(
        r'\b(sovereign wealth|sovereign fund|swf|government investment|'
        r'national fund|state investment|pension fund|endowment|institutional)\b',
        re.IGNORECASE
    ),
    "Government-Contracting": re.compile(
        r'\b(government contract|procurement|rfp|rfi|bid|federal|defense '
        r'contract|sbir|sttr|far|dfars|compliance|clearance)\b', re.IGNORECASE
    ),
    "Enterprise-Scaling": re.compile(
        r'\b(scaling|enterprise|growth|go to market|gtm|series [a-d]|venture|'
        r'fundrais|valuation|burn rate|runway|product-market fit|tam|sam|som)\b',
        re.IGNORECASE
    ),
    "EdTech": re.compile(
        r'\b(edtech|education technology|e-learning|lms|learning management|'
        r'adaptive learning|tutoring|mooc|curriculum|pedagog|gamification)\b',
        re.IGNORECASE
    ),
    "Neuroscience": re.compile(
        r'\b(neuroscience|neuron|brain|cognit|neural pathway|neuroplasticity|'
        r'cortex|hippocampus|dopamine|serotonin|fmri|eeg|synaptic)\b',
        re.IGNORECASE
    ),
    "Climate-Tech": re.compile(
        r'\b(climate|carbon|emission|renewable|solar|wind|hydrogen|'
        r'decarboniz|sustainability|esg|green|clean energy|carbon capture|'
        r'net zero)\b', re.IGNORECASE
    ),
    "HealthTech": re.compile(
        r'\b(healthtech|health tech|telehealth|telemedicine|ehr|emr|'
        r'digital health|wearable|remote monitoring|clinical trial|fda|'
        r'precision medicine|diagnostics)\b', re.IGNORECASE
    ),
    "Supply-Chain": re.compile(
        r'\b(supply chain|logistics|warehouse|fulfillment|inventory|'
        r'distribution|procurement|freight|shipping|last mile|3pl|'
        r'supply network)\b', re.IGNORECASE
    ),
}


# =============================================================================
# SUBDOMAIN DEFINITIONS
# =============================================================================

SUBDOMAIN_MAP = {
    "Machine-Learning": {
        "Computer-Vision": re.compile(
            r'\b(image|vision|cnn|object detection|segmentation|yolo|resnet)\b',
            re.IGNORECASE
        ),
        "Reinforcement-Learning": re.compile(
            r'\b(agent|reward|policy|q-learning|environment|mdp|actor-critic|'
            r'multi-agent)\b', re.IGNORECASE
        ),
        "Generative-AI": re.compile(
            r'\b(gan|vae|diffusion|generation|synthesis|stable diffusion|'
            r'midjourney|dall-e|generative)\b', re.IGNORECASE
        ),
        "Time-Series": re.compile(
            r'\b(lstm|rnn|forecasting|temporal|sequence|arima|time series)\b',
            re.IGNORECASE
        ),
        "MLOps": re.compile(
            r'\b(mlflow|kubeflow|model serving|model deployment|monitoring|'
            r'drift|model registry)\b', re.IGNORECASE
        ),
    },
    "Quantum-Computing": {
        "Quantum-Algorithms": re.compile(
            r'\b(shor|grover|vqe|qaoa|quantum algorithm|quantum supremacy)\b',
            re.IGNORECASE
        ),
        "Quantum-Hardware": re.compile(
            r'\b(ion trap|superconducting|photonic|quantum processor|ibm '
            r'quantum|rigetti)\b', re.IGNORECASE
        ),
        "Quantum-Error-Correction": re.compile(
            r'\b(error correction|fault tolerant|surface code|logical qubit)\b',
            re.IGNORECASE
        ),
        "Quantum-ML": re.compile(
            r'\b(quantum machine learning|qml|variational|quantum neural)\b',
            re.IGNORECASE
        ),
    },
    "Natural-Language-Processing": {
        "Large-Language-Models": re.compile(
            r'\b(llm|gpt|bert|transformer|attention|fine-tuning|rlhf|'
            r'prompt engineering)\b', re.IGNORECASE
        ),
        "Information-Extraction": re.compile(
            r'\b(ner|entity extraction|relation extraction|knowledge graph|'
            r'structured extraction)\b', re.IGNORECASE
        ),
        "Conversational-AI": re.compile(
            r'\b(chatbot|dialogue|intent|slot filling|rasa|assistant)\b',
            re.IGNORECASE
        ),
        "RAG-Systems": re.compile(
            r'\b(rag|retrieval augmented|vector search|embedding search|'
            r'semantic search|hybrid search)\b', re.IGNORECASE
        ),
    },
    "Biotechnology": {
        "Gene-Therapy": re.compile(
            r'\b(gene therapy|crispr|gene editing|cas9|base editing|'
            r'prime editing)\b', re.IGNORECASE
        ),
        "Drug-Discovery": re.compile(
            r'\b(drug discovery|pharma|clinical|compound|target|binding|'
            r'molecule|screening)\b', re.IGNORECASE
        ),
        "Synthetic-Biology": re.compile(
            r'\b(synthetic biology|bio.*manufacturing|cell factory|'
            r'metabolic engineering|bioreactor)\b', re.IGNORECASE
        ),
    },
    "FinTech": {
        "DeFi": re.compile(
            r'\b(defi|liquidity pool|amm|yield farming|lending protocol|'
            r'dex|staking)\b', re.IGNORECASE
        ),
        "InsurTech": re.compile(
            r'\b(insurtech|insurance technology|parametric|claims|'
            r'underwriting|actuarial)\b', re.IGNORECASE
        ),
        "Payments": re.compile(
            r'\b(payment|remittance|cross-border|swift|instant payment|'
            r'mobile money|digital wallet)\b', re.IGNORECASE
        ),
    },
}


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def analyze_domain_indicators(text: str) -> dict:
    """
    Match text against all domain patterns and return best match.

    Scores each domain by regex match count. Confidence is calculated as
    min(match_count / 10, 1.0). Technical flag set if match_count >= 2.

    Args:
        text: Text to analyze for domain indicators.

    Returns:
        Dict with domain, score, confidence, indicators[], technical flag,
        and subdomains[].
    """
    best = {
        "domain": "General-Systems",
        "score": 0,
        "confidence": 0.15,
        "indicators": [],
        "technical": False,
        "subdomains": [],
    }

    for domain, pattern in DOMAIN_PATTERNS.items():
        matches = pattern.findall(text)
        score = len(matches)

        if score > best["score"]:
            unique_indicators = list(set(m.lower() for m in matches))[:8]
            best = {
                "domain": domain,
                "score": score,
                "confidence": min(score / 10, 1.0),
                "indicators": unique_indicators,
                "technical": score >= 2,
                "subdomains": [],
            }

    # Discover subdomains for the matched domain
    if best["domain"] in SUBDOMAIN_MAP:
        best["subdomains"] = identify_subdomains(text, best["domain"])

    return best


def identify_subdomains(text: str, primary_domain: str) -> list:
    """
    Discover subdomains within a primary domain.

    Args:
        text: Text to analyze.
        primary_domain: The primary domain to check subdomains for.

    Returns:
        List of subdomain dicts sorted by confidence (descending).
    """
    subdomains = []
    domain_subs = SUBDOMAIN_MAP.get(primary_domain, {})

    for sub_name, pattern in domain_subs.items():
        matches = pattern.findall(text)
        if matches:
            unique_terms = list(set(m.lower() for m in matches))
            subdomains.append({
                "name": sub_name,
                "indicator_count": len(matches),
                "indicator_terms": unique_terms,
                "confidence": min(len(matches) / 5, 1.0),
            })

    return sorted(subdomains, key=lambda x: x["confidence"], reverse=True)


def deduplicate_domains(domains: list) -> list:
    """
    Deduplicate domain list, keeping highest confidence per domain.

    Merges subdomain lists when same primary domain appears multiple times.

    Args:
        domains: List of domain analysis dicts.

    Returns:
        Deduplicated list with merged subdomains.
    """
    unique = {}

    for d in domains:
        key = d["domain"]
        if key not in unique or unique[key]["confidence"] < d["confidence"]:
            unique[key] = d
        elif d.get("subdomains"):
            # Merge subdomains
            existing_subs = {s["name"] for s in unique[key].get("subdomains", [])}
            for sub in d["subdomains"]:
                if sub["name"] not in existing_subs:
                    unique[key].setdefault("subdomains", []).append(sub)

    return list(unique.values())


def identify_domains(decomposition: dict) -> dict:
    """
    Full domain identification pipeline.

    Analyzes all segments from context decomposition, categorizes domains
    by confidence threshold: PRIMARY (>0.7), TECHNICAL (>0.4), ADJACENT (>0.2).
    Adds methodological domain if 3+ methodology elements detected.

    Args:
        decomposition: Output from decompose_context.py (Stage 1).

    Returns:
        Domain map dict with primary[], technical[], adjacent[],
        methodological[], implementation[], and metadata.
    """
    print(f"\n🎯 DOMAIN IDENTIFICATION ENGINE")
    print(f"   Analyzing {len(decomposition['segments'])} segments...\n")

    domains = {
        "primary": [],
        "technical": [],
        "adjacent": [],
        "methodological": [],
        "implementation": [],
    }

    # Strategy 1: Per-segment analysis
    for idx, seg in enumerate(decomposition["segments"]):
        analysis = analyze_domain_indicators(seg["text"])

        if (idx + 1) % 5 == 0 or idx == 0:
            print(f"  Segment {idx + 1}: {analysis['domain']} "
                  f"(confidence: {analysis['confidence']:.2f})")

        # Categorize by confidence
        if analysis["confidence"] > 0.7:
            domains["primary"].append(analysis)
        elif analysis["technical"] and analysis["confidence"] > 0.4:
            domains["technical"].append(analysis)
        elif analysis["confidence"] > 0.2:
            domains["adjacent"].append(analysis)

    # Strategy 2: Full-text aggregated analysis (catches terms spread across segments)
    full_text = " ".join(seg["text"] for seg in decomposition["segments"])
    print(f"\n  Aggregated full-text analysis ({len(full_text)} chars)...")
    for domain_name, pattern in DOMAIN_PATTERNS.items():
        matches = pattern.findall(full_text)
        score = len(matches)
        if score >= 2:
            confidence = min(score / 10, 1.0)
            unique_indicators = list(set(m.lower() for m in matches))[:8]
            subdomains = identify_subdomains(full_text, domain_name)
            agg_domain = {
                "domain": domain_name,
                "score": score,
                "confidence": confidence,
                "indicators": unique_indicators,
                "technical": score >= 2,
                "subdomains": subdomains,
            }
            print(f"  Full-text: {domain_name} → {score} matches, "
                  f"confidence {confidence:.2f}")

            if confidence > 0.7:
                domains["primary"].append(agg_domain)
            elif confidence > 0.4:
                domains["technical"].append(agg_domain)
            elif confidence > 0.2:
                domains["adjacent"].append(agg_domain)

    # Check for methodological domain
    method_elements = decomposition["elements"].get("methodologies", [])
    if len(method_elements) > 2:
        domains["methodological"].append({
            "domain": "Research-Methodology",
            "indicators": method_elements[:10],
            "confidence": min(len(method_elements) / 8, 0.9),
            "technical": False,
            "subdomains": [],
        })

    # Deduplicate
    domains["primary"] = deduplicate_domains(domains["primary"])
    domains["technical"] = deduplicate_domains(domains["technical"])
    domains["adjacent"] = deduplicate_domains(domains["adjacent"])

    # Metadata
    all_domains = (domains["primary"] + domains["technical"] +
                   domains["adjacent"] + domains["methodological"])

    metadata = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_domains": len(all_domains),
        "primary_count": len(domains["primary"]),
        "technical_count": len(domains["technical"]),
        "adjacent_count": len(domains["adjacent"]),
        "methodological_count": len(domains["methodological"]),
        "complexity_input": decomposition["complexity"]["level"],
    }

    result = {
        "domains": domains,
        "metadata": metadata,
    }

    print(f"\n✅ Domain identification complete:")
    print(f"   PRIMARY ({len(domains['primary'])}): "
          f"{', '.join(d['domain'] for d in domains['primary'])}")
    print(f"   TECHNICAL ({len(domains['technical'])}): "
          f"{', '.join(d['domain'] for d in domains['technical'])}")
    print(f"   ADJACENT ({len(domains['adjacent'])}): "
          f"{', '.join(d['domain'] for d in domains['adjacent'])}")
    if domains["methodological"]:
        print(f"   METHODOLOGICAL: Research-Methodology")
    print()

    return result


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Genesis Domain Identifier — Stage 2 of Expert Breakdown Pipeline"
    )
    parser.add_argument(
        "input",
        help="Decomposition JSON from Stage 1 (decomposition.json)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="domains.json",
        help="Output JSON path (default: domains.json)"
    )
    args = parser.parse_args()

    # Load decomposition with error handling
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            decomposition = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input}: {e}")
        sys.exit(1)

    # Validate input structure
    if "segments" not in decomposition:
        raise ValueError(
            f"Input JSON missing 'segments' key. "
            f"Expected output from decompose_context.py (Stage 1)."
        )

    print(f"Loaded decomposition from {args.input}")

    # Identify domains
    result = identify_domains(decomposition)

    # Save with error handling
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Error: Could not write to {args.output}: {e}")
        sys.exit(1)

    print(f"Saved domain map to {args.output}")
    return result


if __name__ == "__main__":
    main()
