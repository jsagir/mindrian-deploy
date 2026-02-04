"""
Stage 1: Context Decomposition
==============================
Breaks challenge text into semantic segments and extracts core elements.
"""

import re
from datetime import datetime
from typing import Dict, List, Any


def segment_text(text: str, max_segment: int = 300) -> List[Dict]:
    """
    Segment text into coherent chunks at sentence boundaries.

    Args:
        text: Input text to segment
        max_segment: Maximum characters per segment

    Returns:
        List of segment dicts with text and metadata
    """
    # Split at sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    segments = []
    current = []
    current_len = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if current_len + len(sentence) > max_segment and current:
            segments.append({
                "text": " ".join(current),
                "char_count": current_len,
                "sentence_count": len(current),
            })
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += len(sentence) + 1

    if current:
        segments.append({
            "text": " ".join(current),
            "char_count": current_len,
            "sentence_count": len(current),
        })

    # Add indices
    for i, seg in enumerate(segments):
        seg["index"] = i

    return segments


def extract_elements(text: str) -> Dict[str, List[str]]:
    """
    Extract core elements from text using pattern matching.

    Extracts:
    - concepts: Key ideas and themes
    - technologies: Technical terms and tools
    - methodologies: Approaches and frameworks
    - challenges: Problems and obstacles
    - opportunities: Potential benefits and goals
    """
    text_lower = text.lower()

    # Concept patterns
    concept_patterns = [
        r'\b(innovation|disruption|transformation|convergence|integration)\b',
        r'\b(scalability|efficiency|optimization|automation)\b',
        r'\b(sustainability|resilience|adaptability)\b',
    ]

    # Technology patterns
    tech_patterns = [
        r'\b(AI|ML|machine learning|deep learning|neural network)\b',
        r'\b(blockchain|IoT|cloud|edge computing|quantum)\b',
        r'\b(API|platform|software|hardware|algorithm)\b',
        r'\b(data|analytics|sensor|robotics|automation)\b',
    ]

    # Methodology patterns
    method_patterns = [
        r'\b(agile|lean|design thinking|systems thinking)\b',
        r'\b(framework|methodology|approach|strategy|model)\b',
        r'\b(analysis|research|validation|testing)\b',
    ]

    # Challenge patterns
    challenge_patterns = [
        r'\b(challenge|problem|obstacle|barrier|limitation)\b',
        r'\b(risk|threat|constraint|bottleneck|gap)\b',
        r'\b(difficult|complex|uncertain|volatile)\b',
    ]

    # Opportunity patterns
    opportunity_patterns = [
        r'\b(opportunity|potential|possibility|benefit)\b',
        r'\b(growth|market|value|advantage|innovation)\b',
        r'\b(improve|enhance|optimize|transform)\b',
    ]

    def extract_matches(patterns):
        matches = set()
        for pattern in patterns:
            for match in re.findall(pattern, text_lower, re.IGNORECASE):
                matches.add(match.lower())
        return list(matches)[:15]  # Cap at 15

    return {
        "concepts": extract_matches(concept_patterns),
        "technologies": extract_matches(tech_patterns),
        "methodologies": extract_matches(method_patterns),
        "challenges": extract_matches(challenge_patterns),
        "opportunities": extract_matches(opportunity_patterns),
    }


def calculate_complexity(segments: List[Dict], elements: Dict) -> Dict:
    """
    Calculate complexity score based on segments and elements.

    Returns:
        Complexity dict with level, score, and depth required.
    """
    # Factors
    segment_count = len(segments)
    total_elements = sum(len(v) for v in elements.values())
    avg_segment_len = sum(s["char_count"] for s in segments) / max(segment_count, 1)

    # Score (0-10)
    score = min(10, (
        segment_count * 0.5 +
        total_elements * 0.3 +
        (avg_segment_len / 50) * 0.2
    ))

    # Level
    if score >= 7:
        level = "HIGH"
        depth = "AUTHORITY"
    elif score >= 4:
        level = "MEDIUM"
        depth = "EXPERT"
    else:
        level = "LOW"
        depth = "SPECIALIST"

    return {
        "level": level,
        "score": round(score, 2),
        "depthRequired": depth,
        "factors": {
            "segment_count": segment_count,
            "element_count": total_elements,
            "avg_segment_length": round(avg_segment_len, 1),
        }
    }


def decompose_context(
    text: str,
    max_segment: int = 300
) -> Dict[str, Any]:
    """
    Full context decomposition pipeline.

    Args:
        text: Challenge description to decompose
        max_segment: Max characters per segment

    Returns:
        Decomposition dict with segments, elements, complexity, metadata
    """
    if len(text.strip()) < 50:
        raise ValueError("Challenge text must be at least 50 characters")

    # Segment
    segments = segment_text(text, max_segment)

    # Extract elements
    elements = extract_elements(text)

    # Calculate complexity
    complexity = calculate_complexity(segments, elements)

    return {
        "segments": segments,
        "elements": elements,
        "complexity": complexity,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_length": len(text),
            "segment_count": len(segments),
            "total_elements": sum(len(v) for v in elements.values()),
        }
    }
