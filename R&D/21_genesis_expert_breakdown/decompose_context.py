"""
decompose_context.py — Context Decomposition Engine
=====================================================
Pipeline Stage 1: Semantic segmentation, element extraction, and complexity scoring.

Transforms raw challenge text into structured components for domain identification.
Implements the Genesis Engine's Context Decomposer logic in executable Python.

Usage:
    python scripts/decompose_context.py input.txt [output.json] [--max-segment 300]

Input:
    Plain text file (.txt) or JSON with a "text" field.

Output:
    decomposition.json with segments[], elements{}, complexity{}, metadata{}
"""

import json
import sys
import re
import argparse
from datetime import datetime
from collections import Counter


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def semantic_segmentation(text: str, max_segment_length: int = 300) -> list:
    """
    Segment text into coherent semantic chunks.

    Splits by paragraph boundaries first, then by sentence boundaries if
    paragraphs exceed max_segment_length. Each segment includes type
    classification (atomic vs composite) and word count.

    Args:
        text: Raw input text to segment.
        max_segment_length: Maximum character length per segment (default: 300).

    Returns:
        List of segment dicts with text, type, word_count, and index.
    """
    print(f"  Segmenting text ({len(text)} chars, max {max_segment_length}/segment)...")

    # Split by paragraph boundaries
    raw_paragraphs = re.split(r'\n\n+', text)
    raw_paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

    segments = []
    seg_index = 0

    for para in raw_paragraphs:
        if len(para) > max_segment_length:
            # Split long paragraphs at sentence boundaries
            sentences = re.findall(r'[^.!?]+[.!?]*', para)
            sentences = [s.strip() for s in sentences if s.strip()]

            chunk = ""
            for sent in sentences:
                if len(chunk) + len(sent) > max_segment_length and chunk.strip():
                    segments.append({
                        "index": seg_index,
                        "text": chunk.strip(),
                        "type": "composite",
                        "word_count": len(chunk.strip().split()),
                    })
                    seg_index += 1
                    chunk = sent
                else:
                    chunk = (chunk + " " + sent).strip()

            if chunk.strip():
                segments.append({
                    "index": seg_index,
                    "text": chunk.strip(),
                    "type": "composite",
                    "word_count": len(chunk.strip().split()),
                })
                seg_index += 1

        elif len(para) > 50:
            segments.append({
                "index": seg_index,
                "text": para.strip(),
                "type": "atomic",
                "word_count": len(para.strip().split()),
            })
            seg_index += 1

    print(f"  → {len(segments)} segments created")
    return segments


def extract_core_elements(segments: list) -> dict:
    """
    Extract conceptual elements from segmented text.

    Identifies five element categories: concepts (capitalized noun phrases),
    technologies, methodologies, challenges, and opportunities. Uses pattern
    matching against curated term lists.

    Args:
        segments: List of segment dicts from semantic_segmentation().

    Returns:
        Dict with five lists: concepts, technologies, methodologies,
        challenges, opportunities.
    """
    print("  Extracting core elements...")

    concepts = set()
    technologies = set()
    methodologies = set()
    challenges = set()
    opportunities = set()

    # ── Keyword sets for robust matching (handles inflections) ──────────
    TECH_KEYWORDS = {
        "algorithm", "system", "platform", "framework", "protocol",
        "architecture", "model", "network", "database", "api", "interface",
        "software", "hardware", "cloud", "edge", "iot", "blockchain",
        "quantum", "ai", "ml", "neural", "pipeline", "microservice",
        "container", "serverless", "streaming", "encryption", "sensor",
        "robot", "vision", "nlp", "transformer", "embedding", "tokenization",
        "automation", "infrastructure", "logistics", "fintech", "corridor",
        "port", "shipping", "trade", "supply", "computing", "processing",
    }

    METHOD_KEYWORDS = {
        "approach", "method", "technique", "strategy", "process",
        "procedure", "analysis", "optimization", "implementation", "design",
        "development", "evaluation", "assessment", "validation", "simulation",
        "experiment", "iteration", "workflow", "methodology", "synthesis",
        "integration", "decomposition", "orchestration", "scaling",
        "contracting", "financing", "partnership", "balancing", "navigating",
    }

    CHALLENGE_KEYWORDS = {
        "challenge", "problem", "issue", "constraint", "limitation",
        "bottleneck", "obstacle", "difficulty", "barrier", "gap", "risk",
        "threat", "vulnerability", "complexity", "trade-off", "tension",
        "conflict", "shortage", "deficit", "uncertainty", "volatility",
        "competition", "regulation", "compliance", "friction",
    }

    OPP_KEYWORDS = {
        "opportunity", "potential", "enable", "allow", "unlock",
        "breakthrough", "innovation", "advantage", "benefit", "synergy",
        "convergence", "disruption", "transformation", "revolution",
        "emergence", "catalyst", "accelerate", "amplify", "moat",
        "sustainable", "competitive", "corridor", "bridge", "venture",
    }

    # Multi-word phrases to detect as whole units
    PHRASE_MAP = {
        "technologies": [
            "deep learning", "data lake", "supply chain", "machine learning",
            "artificial intelligence", "smart contract", "edge computing",
            "natural language processing", "computer vision", "augmented reality",
            "virtual reality", "mixed reality", "digital twin",
        ],
        "methodologies": [
            "paradigm shift", "best practice", "due diligence",
            "risk assessment", "cost benefit", "feasibility study",
        ],
        "challenges": [
            "geopolitical risk", "financing gap", "capability gap",
            "market risk", "execution risk", "regulatory barrier",
            "talent shortage", "supply chain disruption",
        ],
        "opportunities": [
            "competitive moat", "first mover", "market opportunity",
            "value creation", "trade corridor", "growth potential",
            "sovereign wealth", "blended finance", "public private",
        ],
    }

    def _normalize(word):
        """Strip common English suffixes for keyword matching."""
        w = word.lower().strip(".,;:!?()\"'")
        for suffix in ("ies", "ment", "tion", "sion", "ness", "ing", "ed", "es", "s"):
            if len(w) > len(suffix) + 2 and w.endswith(suffix):
                return w[: -len(suffix)]
        return w

    # Capitalized concept pattern
    concept_pattern = re.compile(
        r'\b([A-Z][a-z0-9\-]{2,}(?:\s[A-Z][a-z0-9\-]{2,})*)\b'
    )

    for seg in segments:
        text = seg["text"]
        text_lower = text.lower()

        # ── Multi-word phrase extraction ──
        for category, phrases in PHRASE_MAP.items():
            for phrase in phrases:
                if phrase in text_lower:
                    locals()[category].add(phrase)

        # ── Single-word keyword matching with normalization ──
        words = re.findall(r'[a-zA-Z\-]{3,}', text_lower)
        for word in words:
            stem = _normalize(word)
            if stem in TECH_KEYWORDS or word in TECH_KEYWORDS:
                technologies.add(word)
            if stem in METHOD_KEYWORDS or word in METHOD_KEYWORDS:
                methodologies.add(word)
            if stem in CHALLENGE_KEYWORDS or word in CHALLENGE_KEYWORDS:
                challenges.add(word)
            if stem in OPP_KEYWORDS or word in OPP_KEYWORDS:
                opportunities.add(word)

        # ── Concepts: capitalized noun phrases ──
        for match in concept_pattern.findall(text):
            cleaned = match.strip()
            if len(cleaned) > 3 and cleaned not in {
                "The", "This", "That", "These", "Those", "When",
                "How", "What", "Where", "Why", "Which", "Each",
            }:
                concepts.add(cleaned)

    result = {
        "concepts": sorted(concepts),
        "technologies": sorted(technologies),
        "methodologies": sorted(methodologies),
        "challenges": sorted(challenges),
        "opportunities": sorted(opportunities),
    }

    total = sum(len(v) for v in result.values())
    print(f"  → {total} elements extracted: "
          f"{len(result['concepts'])} concepts, "
          f"{len(result['technologies'])} technologies, "
          f"{len(result['methodologies'])} methodologies, "
          f"{len(result['challenges'])} challenges, "
          f"{len(result['opportunities'])} opportunities")

    return result


def analyze_complexity(elements: dict) -> dict:
    """
    Score complexity and determine required expertise depth.

    Combines element counts with weighted formula:
    total = tech + method + challenges + (concepts * 0.5)

    Thresholds: LOW (<10), MEDIUM (10-20), HIGH (>20)
    Depth: SPECIALIST, EXPERT, AUTHORITY

    Args:
        elements: Dict of extracted element lists from extract_core_elements().

    Returns:
        Dict with level, component scores, totalComplexity, and depthRequired.
    """
    print("  Analyzing complexity...")

    tech_c = len(elements["technologies"])
    method_c = len(elements["methodologies"])
    challenge_c = len(elements["challenges"])
    concept_c = len(elements["concepts"])
    opp_c = len(elements["opportunities"])

    total = tech_c + method_c + challenge_c + (concept_c * 0.5) + (opp_c * 0.3)
    total = round(total)

    if total > 20:
        level, depth = "HIGH", "AUTHORITY"
    elif total > 10:
        level, depth = "MEDIUM", "EXPERT"
    else:
        level, depth = "LOW", "SPECIALIST"

    result = {
        "level": level,
        "techComplexity": tech_c,
        "methodComplexity": method_c,
        "challengeComplexity": challenge_c,
        "conceptComplexity": concept_c,
        "opportunityComplexity": opp_c,
        "totalComplexity": total,
        "depthRequired": depth,
    }

    print(f"  → Complexity: {level} ({total} weighted score) → Depth: {depth}")
    return result


def decompose_context(text: str, max_segment: int = 300) -> dict:
    """
    Full context decomposition pipeline.

    Orchestrates segmentation → extraction → complexity analysis.

    Args:
        text: Raw challenge text (minimum 50 characters).
        max_segment: Maximum segment length in characters (default: 300).

    Returns:
        Complete decomposition dict with segments, elements, complexity, metadata.

    Raises:
        ValueError: If text is shorter than 50 characters.
    """
    if not text or len(text.strip()) < 50:
        raise ValueError(
            f"Context too short for meaningful analysis "
            f"(got {len(text.strip())} chars, need ≥50)"
        )

    print(f"\n🧠 CONTEXT DECOMPOSITION ENGINE")
    print(f"   Input: {len(text)} characters\n")

    # Step 1: Segment
    segments = semantic_segmentation(text, max_segment)

    # Step 2: Extract elements
    elements = extract_core_elements(segments)

    # Step 3: Analyze complexity
    complexity = analyze_complexity(elements)

    # Build metadata
    word_counts = [s["word_count"] for s in segments]
    metadata = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_length_chars": len(text),
        "input_length_words": len(text.split()),
        "segment_count": len(segments),
        "avg_segment_words": round(sum(word_counts) / max(len(word_counts), 1), 1),
        "total_elements": sum(len(v) for v in elements.values()),
    }

    result = {
        "originalContext": text[:2000] + ("..." if len(text) > 2000 else ""),
        "segments": segments,
        "elements": elements,
        "complexity": complexity,
        "metadata": metadata,
    }

    print(f"\n✅ Decomposition complete: {metadata['segment_count']} segments, "
          f"{metadata['total_elements']} elements, {complexity['level']} complexity\n")

    return result


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Genesis Context Decomposer — Stage 1 of Expert Breakdown Pipeline"
    )
    parser.add_argument(
        "input",
        help="Input file path (.txt or .json with 'text' field)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="decomposition.json",
        help="Output JSON path (default: decomposition.json)"
    )
    parser.add_argument(
        "--max-segment",
        type=int,
        default=300,
        help="Maximum segment length in characters (default: 300)"
    )
    args = parser.parse_args()

    # Load input
    with open(args.input, "r", encoding="utf-8") as f:
        raw = f.read()

    # Try JSON first, fall back to plain text
    try:
        data = json.loads(raw)
        text = data.get("text", data.get("content", raw))
    except json.JSONDecodeError:
        text = raw

    print(f"Loaded input from {args.input} ({len(text)} chars)")

    # Decompose
    result = decompose_context(text, max_segment=args.max_segment)

    # Save
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Saved decomposition to {args.output}")
    return result


if __name__ == "__main__":
    main()
