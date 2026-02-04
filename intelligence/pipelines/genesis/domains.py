"""
Stage 2: Domain Identification
==============================
Pattern matching against 24 domain signatures with subdomain discovery.
"""

import re
from datetime import datetime
from typing import Dict, List, Any


# =============================================================================
# DOMAIN PATTERNS (14 Technical + 10 Non-Technical)
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
# SUBDOMAIN PATTERNS
# =============================================================================

SUBDOMAIN_MAP = {
    "Machine-Learning": {
        "Computer-Vision": re.compile(
            r'\b(image|vision|cnn|object detection|segmentation|yolo|resnet)\b',
            re.IGNORECASE
        ),
        "Reinforcement-Learning": re.compile(
            r'\b(agent|reward|policy|q-learning|environment|mdp|actor-critic)\b',
            re.IGNORECASE
        ),
        "Generative-AI": re.compile(
            r'\b(gan|vae|diffusion|generation|synthesis|stable diffusion|'
            r'midjourney|dall-e|generative)\b', re.IGNORECASE
        ),
        "MLOps": re.compile(
            r'\b(mlflow|kubeflow|model serving|model deployment|monitoring|'
            r'drift|model registry)\b', re.IGNORECASE
        ),
    },
    "Natural-Language-Processing": {
        "Large-Language-Models": re.compile(
            r'\b(llm|gpt|bert|transformer|attention|fine-tuning|rlhf|'
            r'prompt engineering)\b', re.IGNORECASE
        ),
        "RAG-Systems": re.compile(
            r'\b(rag|retrieval augmented|vector search|embedding search|'
            r'semantic search|hybrid search)\b', re.IGNORECASE
        ),
        "Conversational-AI": re.compile(
            r'\b(chatbot|dialogue|intent|slot filling|assistant)\b',
            re.IGNORECASE
        ),
    },
    "FinTech": {
        "DeFi": re.compile(
            r'\b(defi|liquidity pool|amm|yield farming|lending protocol|'
            r'dex|staking)\b', re.IGNORECASE
        ),
        "Payments": re.compile(
            r'\b(payment|remittance|cross-border|swift|instant payment|'
            r'mobile money|digital wallet)\b', re.IGNORECASE
        ),
    },
}


def analyze_domain_indicators(text: str) -> Dict[str, Any]:
    """
    Match text against all domain patterns.

    Returns:
        Dict with domain, score, confidence, indicators, subdomains
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

    # Discover subdomains
    if best["domain"] in SUBDOMAIN_MAP:
        best["subdomains"] = identify_subdomains(text, best["domain"])

    return best


def identify_subdomains(text: str, primary_domain: str) -> List[Dict]:
    """Discover subdomains within a primary domain."""
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


def deduplicate_domains(domains: List[Dict]) -> List[Dict]:
    """Deduplicate domain list, keeping highest confidence."""
    unique = {}
    for d in domains:
        key = d["domain"]
        if key not in unique or unique[key]["confidence"] < d["confidence"]:
            unique[key] = d
        elif d.get("subdomains"):
            existing_subs = {s["name"] for s in unique[key].get("subdomains", [])}
            for sub in d["subdomains"]:
                if sub["name"] not in existing_subs:
                    unique[key].setdefault("subdomains", []).append(sub)
    return list(unique.values())


def identify_domains(decomposition: Dict) -> Dict[str, Any]:
    """
    Full domain identification pipeline.

    Args:
        decomposition: Output from decompose_context()

    Returns:
        Domain map with primary, technical, adjacent, methodological domains
    """
    domains = {
        "primary": [],
        "technical": [],
        "adjacent": [],
        "methodological": [],
    }

    # Per-segment analysis
    for seg in decomposition["segments"]:
        analysis = analyze_domain_indicators(seg["text"])

        if analysis["confidence"] > 0.7:
            domains["primary"].append(analysis)
        elif analysis["technical"] and analysis["confidence"] > 0.4:
            domains["technical"].append(analysis)
        elif analysis["confidence"] > 0.2:
            domains["adjacent"].append(analysis)

    # Full-text aggregated analysis
    full_text = " ".join(seg["text"] for seg in decomposition["segments"])
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

    all_domains = (domains["primary"] + domains["technical"] +
                   domains["adjacent"] + domains["methodological"])

    return {
        "domains": domains,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_domains": len(all_domains),
            "primary_count": len(domains["primary"]),
            "technical_count": len(domains["technical"]),
            "adjacent_count": len(domains["adjacent"]),
            "complexity_input": decomposition["complexity"]["level"],
        }
    }
