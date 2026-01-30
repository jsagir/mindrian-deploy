"""
Intelligent Context Extraction for Custom UI Components

This module extracts structured intelligence from:
1. Conversation history (LangExtract patterns)
2. Neo4j knowledge graph
3. Session context

Powers: AssumptionTracker, EvidenceDashboard, FrameworkSelector, etc.
"""

import re
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# === DATA CLASSES ===

@dataclass
class Assumption:
    """Extracted assumption from conversation"""
    id: str
    text: str
    criticality: str  # critical, moderate, low
    status: str  # untested, partial, validated, invalidated
    source_bot: str
    source_phase: Optional[str]
    evidence: List[str]
    discovered_at: str

    def to_dict(self):
        return asdict(self)

@dataclass
class Evidence:
    """Evidence item with source attribution"""
    id: str
    content: str
    source_type: str  # neo4j, filesearch, tavily, gemini, user
    relevance: float  # 0.0 - 1.0
    tags: List[str]
    timestamp: str

    def to_dict(self):
        return asdict(self)

@dataclass
class Insight:
    """Key insight extracted from conversation"""
    id: str
    text: str
    context: str
    source_bot: str
    confidence: float
    evidence_count: int
    timestamp: str

    def to_dict(self):
        return asdict(self)

@dataclass
class FrameworkMatch:
    """Framework recommendation based on context"""
    framework_id: str
    name: str
    score: float
    reasoning: str
    keywords_matched: List[str]

# === EXTRACTION PATTERNS ===

ASSUMPTION_PATTERNS = [
    r"(?:we\s+)?assum(?:e|ing|ption)[s]?\s+(?:that\s+)?(.{20,150})",
    r"(?:I\s+)?(?:think|believe|expect)\s+(?:that\s+)?(.{20,150})",
    r"(?:it's\s+)?(?:likely|probably)\s+(?:that\s+)?(.{20,150})",
    r"users?\s+(?:will|would|should)\s+(.{20,150})",
    r"the\s+market\s+(?:will|is|has)\s+(.{20,150})",
    r"customers?\s+(?:want|need|prefer)\s+(.{20,150})",
]

INSIGHT_PATTERNS = [
    r"(?:key\s+)?insight[s]?:\s*(.{20,200})",
    r"(?:the\s+)?(?:main|core|key)\s+(?:finding|takeaway|point)\s+(?:is|was)\s+(.{20,200})",
    r"(?:this\s+)?(?:suggests|indicates|shows|reveals)\s+(?:that\s+)?(.{20,200})",
    r"(?:importantly|crucially|notably),?\s+(.{20,200})",
]

EVIDENCE_PATTERNS = [
    r"(?:according\s+to|based\s+on|from)\s+(.{10,100})",
    r"(?:research|study|data|survey)\s+(?:shows|indicates|found)\s+(.{20,150})",
    r"(\d+%)\s+(?:of\s+)?(.{10,100})",
    r"\$[\d,]+(?:\s+(?:billion|million|B|M))?\s+(.{10,100})",
]

QUOTE_PATTERNS = [
    r'"([^"]{20,200})"',
    r"'([^']{20,200})'",
    r"(?:user|customer|patient)\s+said[,:]?\s*[\"'](.{20,200})[\"']",
]

# === FRAMEWORK KEYWORDS ===

FRAMEWORK_KEYWORDS = {
    "jtbd": {
        "keywords": ["customer", "job", "hire", "progress", "struggling", "switch", "outcome", "situation", "motivation", "need", "want"],
        "name": "Jobs to Be Done",
        "description": "Understand what progress customers are trying to make"
    },
    "tta": {
        "keywords": ["trend", "future", "extrapolate", "absurd", "emerging", "scenario", "what if", "years from now", "projection"],
        "name": "Trending to the Absurd",
        "description": "Explore future trends and extreme scenarios"
    },
    "scurve": {
        "keywords": ["timing", "adoption", "technology", "mature", "emerging", "disruption", "lifecycle", "when", "ready"],
        "name": "S-Curve Analysis",
        "description": "Analyze technology timing and market readiness"
    },
    "redteam": {
        "keywords": ["challenge", "assumption", "weakness", "risk", "failure", "critique", "devil", "stress test", "flaw"],
        "name": "Red Team",
        "description": "Stress-test assumptions and find weaknesses"
    },
    "ackoff": {
        "keywords": ["data", "information", "knowledge", "wisdom", "validate", "evidence", "dikw", "pyramid", "proof"],
        "name": "Ackoff's DIKW Pyramid",
        "description": "Validate with data, information, knowledge, wisdom"
    },
    "bono": {
        "keywords": ["perspective", "hat", "thinking", "creative", "emotion", "logic", "optimist", "pessimist"],
        "name": "Six Thinking Hats",
        "description": "Explore multiple perspectives systematically"
    }
}

# === EXTRACTION FUNCTIONS ===

def extract_assumptions(text: str, bot_id: str = "unknown", phase: str = None) -> List[Assumption]:
    """Extract assumptions from text using regex patterns"""
    assumptions = []
    seen_texts = set()

    for pattern in ASSUMPTION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            assumption_text = match.group(1).strip()
            # Clean up
            assumption_text = re.sub(r'\s+', ' ', assumption_text)
            assumption_text = assumption_text.rstrip('.,;:')

            # Skip duplicates
            if assumption_text.lower() in seen_texts:
                continue
            seen_texts.add(assumption_text.lower())

            # Determine criticality based on keywords
            criticality = "moderate"
            critical_keywords = ["will pay", "market size", "revenue", "users will", "definitely", "certainly"]
            low_keywords = ["might", "possibly", "could be", "perhaps"]

            text_lower = assumption_text.lower()
            if any(kw in text_lower for kw in critical_keywords):
                criticality = "critical"
            elif any(kw in text_lower for kw in low_keywords):
                criticality = "low"

            assumptions.append(Assumption(
                id=f"asm_{hash(assumption_text) % 100000:05d}",
                text=assumption_text,
                criticality=criticality,
                status="untested",
                source_bot=bot_id,
                source_phase=phase,
                evidence=[],
                discovered_at=datetime.now().isoformat()
            ))

    return assumptions


def extract_insights(text: str, bot_id: str = "unknown") -> List[Insight]:
    """Extract key insights from text"""
    insights = []
    seen_texts = set()

    for pattern in INSIGHT_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            insight_text = match.group(1).strip()
            insight_text = re.sub(r'\s+', ' ', insight_text)

            if insight_text.lower() in seen_texts:
                continue
            seen_texts.add(insight_text.lower())

            # Get surrounding context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()

            insights.append(Insight(
                id=f"ins_{hash(insight_text) % 100000:05d}",
                text=insight_text,
                context=context,
                source_bot=bot_id,
                confidence=0.7,  # Base confidence
                evidence_count=0,
                timestamp=datetime.now().isoformat()
            ))

    return insights


def extract_evidence(text: str, source_type: str = "conversation") -> List[Evidence]:
    """Extract evidence items from text"""
    evidence_items = []
    seen = set()

    for pattern in EVIDENCE_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            content = match.group(0).strip()
            if content.lower() in seen:
                continue
            seen.add(content.lower())

            # Extract tags
            tags = []
            if "$" in content or "revenue" in content.lower():
                tags.append("financial")
            if "%" in content:
                tags.append("statistic")
            if any(word in content.lower() for word in ["user", "customer", "patient"]):
                tags.append("user-research")
            if any(word in content.lower() for word in ["study", "research", "survey"]):
                tags.append("research")

            evidence_items.append(Evidence(
                id=f"evd_{hash(content) % 100000:05d}",
                content=content,
                source_type=source_type,
                relevance=0.7,
                tags=tags if tags else ["general"],
                timestamp=datetime.now().isoformat()
            ))

    return evidence_items


def extract_quotes(text: str) -> List[Dict[str, str]]:
    """Extract user quotes from text"""
    quotes = []
    seen = set()

    for pattern in QUOTE_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            quote_text = match.group(1).strip()
            if quote_text.lower() in seen:
                continue
            seen.add(quote_text.lower())

            quotes.append({
                "id": f"qte_{hash(quote_text) % 100000:05d}",
                "text": quote_text,
                "source": "user research",
                "timestamp": datetime.now().isoformat()
            })

    return quotes


def recommend_frameworks(text: str, history: List[Dict] = None) -> List[FrameworkMatch]:
    """Recommend frameworks based on text content"""
    recommendations = []
    text_lower = text.lower()

    # Also check recent history
    history_text = ""
    if history:
        history_text = " ".join([
            msg.get("content", "")
            for msg in history[-10:]  # Last 10 messages
            if msg.get("role") == "user"
        ]).lower()

    combined_text = f"{text_lower} {history_text}"

    for framework_id, data in FRAMEWORK_KEYWORDS.items():
        matched_keywords = [
            kw for kw in data["keywords"]
            if kw in combined_text
        ]

        if matched_keywords:
            score = len(matched_keywords) / len(data["keywords"])
            recommendations.append(FrameworkMatch(
                framework_id=framework_id,
                name=data["name"],
                score=min(score * 1.5, 1.0),  # Boost but cap at 1.0
                reasoning=f"Matched: {', '.join(matched_keywords[:3])}",
                keywords_matched=matched_keywords
            ))

    # Sort by score
    recommendations.sort(key=lambda x: x.score, reverse=True)
    return recommendations[:3]  # Top 3


# === CONTEXT AGGREGATOR ===

class ConversationContext:
    """Aggregates extracted intelligence across conversation"""

    def __init__(self):
        self.assumptions: List[Assumption] = []
        self.insights: List[Insight] = []
        self.evidence: List[Evidence] = []
        self.quotes: List[Dict] = []
        self.framework_recommendations: List[FrameworkMatch] = []
        self.problem_statement: Optional[str] = None
        self.current_bot: str = "lawrence"
        self.current_phase: Optional[str] = None
        self.turn_count: int = 0

    def process_message(self, content: str, role: str, bot_id: str = None, phase: str = None):
        """Process a message and extract intelligence"""
        if bot_id:
            self.current_bot = bot_id
        if phase:
            self.current_phase = phase

        self.turn_count += 1

        # Extract from user messages
        if role == "user":
            self.framework_recommendations = recommend_frameworks(content)

        # Extract from assistant messages (richer content)
        if role == "assistant":
            new_assumptions = extract_assumptions(content, self.current_bot, self.current_phase)
            new_insights = extract_insights(content, self.current_bot)
            new_evidence = extract_evidence(content, "assistant")
            new_quotes = extract_quotes(content)

            # Merge without duplicates
            existing_ids = {a.id for a in self.assumptions}
            for a in new_assumptions:
                if a.id not in existing_ids:
                    self.assumptions.append(a)

            existing_insight_ids = {i.id for i in self.insights}
            for i in new_insights:
                if i.id not in existing_insight_ids:
                    self.insights.append(i)

            existing_evidence_ids = {e.id for e in self.evidence}
            for e in new_evidence:
                if e.id not in existing_evidence_ids:
                    self.evidence.append(e)

            existing_quote_ids = {q["id"] for q in self.quotes}
            for q in new_quotes:
                if q["id"] not in existing_quote_ids:
                    self.quotes.append(q)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of extracted context"""
        return {
            "assumptions": {
                "total": len(self.assumptions),
                "critical": len([a for a in self.assumptions if a.criticality == "critical"]),
                "untested": len([a for a in self.assumptions if a.status == "untested"]),
                "validated": len([a for a in self.assumptions if a.status == "validated"]),
            },
            "evidence": {
                "total": len(self.evidence),
                "by_source": self._count_by_source(),
                "strength": self._calculate_evidence_strength(),
            },
            "insights": len(self.insights),
            "quotes": len(self.quotes),
            "recommended_framework": self.framework_recommendations[0].name if self.framework_recommendations else None,
            "turn_count": self.turn_count,
        }

    def _count_by_source(self) -> Dict[str, int]:
        """Count evidence by source type"""
        counts = {}
        for e in self.evidence:
            counts[e.source_type] = counts.get(e.source_type, 0) + 1
        return counts

    def _calculate_evidence_strength(self) -> float:
        """Calculate overall evidence strength (0-100)"""
        if not self.evidence:
            return 0.0

        # Weight by source type
        weights = {
            "user": 1.5,  # User quotes are most valuable
            "neo4j": 1.2,
            "filesearch": 1.0,
            "tavily": 0.8,
            "gemini": 0.7,
            "conversation": 0.5,
        }

        total_weight = sum(
            weights.get(e.source_type, 0.5) * e.relevance
            for e in self.evidence
        )

        # Normalize to 0-100
        max_expected = 20  # Expected evidence items for "complete"
        return min(100, (total_weight / max_expected) * 100)

    def to_props(self, component: str) -> Dict[str, Any]:
        """Generate props for a specific component"""

        if component == "AssumptionTracker":
            return {
                "title": "Assumption Tracker",
                "show_risk": True,
                "allow_actions": True,
                "assumptions": [
                    {
                        "text": a.text,
                        "type": "critical" if a.criticality == "critical" else "explicit",
                        "status": a.status,
                        "risk_level": "high" if a.criticality == "critical" else "medium" if a.criticality == "moderate" else "low",
                        "evidence": ", ".join(a.evidence) if a.evidence else None,
                        "source": f"From {a.source_bot}" + (f" ({a.source_phase})" if a.source_phase else "")
                    }
                    for a in self.assumptions
                ],
            }

        elif component == "EvidenceDashboard":
            return {
                "title": "Evidence Dashboard",
                "show_sources": True,
                "filterable": True,
                "evidence": [
                    {
                        "text": e.content,
                        "source_type": self._map_source_type(e.source_type),
                        "strength": "strong" if e.relevance > 0.8 else "moderate" if e.relevance > 0.5 else "weak",
                        "tags": e.tags,
                        "timestamp": e.timestamp.split("T")[0] if "T" in e.timestamp else e.timestamp
                    }
                    for e in self.evidence
                ],
            }

        elif component == "FrameworkSelector":
            return {
                "recommendations": [
                    {
                        "id": r.framework_id,
                        "name": r.name,
                        "score": r.score,
                        "reasoning": r.reasoning,
                    }
                    for r in self.framework_recommendations
                ],
                "context_keywords": self._get_context_keywords(),
                "show_all": False,
            }

        elif component == "InsightCard":
            return {
                "title": "Key Insights",
                "show_confidence": True,
                "expandable": True,
                "max_display": 3,
                "insights": [
                    {
                        "text": i.text,
                        "category": self._categorize_insight(i.text),
                        "confidence": i.confidence,
                        "source_message": i.context,
                        "timestamp": i.timestamp.split("T")[0] if "T" in i.timestamp else i.timestamp
                    }
                    for i in self.insights
                ],
            }

        elif component == "QuoteCarousel":
            return {
                "title": "Key Quotes",
                "layout": "carousel",
                "autoplay": False,
                "show_attribution": True,
                "quotes": [
                    {
                        "text": q.get("text", ""),
                        "attribution": q.get("attribution", "User Research"),
                        "source": q.get("source", "Conversation"),
                        "category": "customer",
                        "timestamp": q.get("timestamp", "").split("T")[0] if q.get("timestamp") else None
                    }
                    for q in self.quotes
                ],
            }

        elif component == "SessionSummary":
            summary = self.get_summary()
            return {
                "session_title": "PWS Session Summary",
                "duration": f"{self.turn_count * 2} minutes",  # Rough estimate
                "framework_used": self.framework_recommendations[0].framework_id if self.framework_recommendations else None,
                "phases_completed": [self.current_phase] if self.current_phase else [],
                "insights": [
                    {"text": i.text, "category": self._categorize_insight(i.text)}
                    for i in self.insights
                ],
                "assumptions": [
                    {"text": a.text, "status": a.status}
                    for a in self.assumptions
                ],
                "evidence": [
                    {"text": e.content, "source_type": self._map_source_type(e.source_type)}
                    for e in self.evidence
                ],
                "quotes": self.quotes,
                "action_items": self._generate_action_items(),
                "quality_score": {
                    "overall": min(1.0, (len(self.evidence) + len(self.insights)) / 20),
                    "dimensions": {
                        "problem_clarity": min(1.0, len(self.insights) / 5),
                        "assumption_awareness": min(1.0, len(self.assumptions) / 5),
                        "evidence_grounding": min(1.0, len(self.evidence) / 10),
                        "actionability": min(1.0, len(self._generate_action_items()) / 3)
                    }
                }
            }

        elif component == "DecisionMatrix":
            return {
                "title": "Decision Matrix",
                "editable": True,
                "highlight_winner": True,
                "options": [],  # User needs to add options
                "criteria": [],  # User needs to add criteria
                "scores": {},
            }

        elif component == "ResearchOrganizer":
            return {
                "title": "Research Organizer",
                "show_gaps": True,
                "editable": True,
                "research_items": self._generate_research_items(),
            }

        elif component == "FrameworkOverlay":
            return {
                "framework_id": self.framework_recommendations[0].framework_id if self.framework_recommendations else "jtbd",
                "current_phase": 0,
                "show_visualization": True,
                "tips": self._generate_tips(),
                "key_concepts": [],
            }

        elif component == "ProblemCanvas":
            return {
                "title": "Problem Definition Canvas",
                "editable": True,
                "show_completeness": True,
                "sections": {
                    "problem": self.problem_statement or "",
                    "who": "",
                    "why": "",
                    "impact": "",
                    "solutions": "",
                    "constraints": "",
                },
            }

        return {}

    def _map_source_type(self, source: str) -> str:
        """Map internal source types to component source types"""
        mapping = {
            "neo4j": "graph",
            "filesearch": "rag",
            "tavily": "web",
            "gemini": "ai",
            "conversation": "user",
            "assistant": "ai",
            "user": "user",
        }
        return mapping.get(source, "external")

    def _categorize_insight(self, text: str) -> str:
        """Categorize an insight based on content"""
        text_lower = text.lower()
        if any(w in text_lower for w in ["customer", "user", "they want", "they need"]):
            return "customer"
        if any(w in text_lower for w in ["risk", "fail", "problem", "issue"]):
            return "risk"
        if any(w in text_lower for w in ["opportunity", "potential", "could"]):
            return "opportunity"
        if any(w in text_lower for w in ["assume", "believe", "think"]):
            return "assumption"
        return "general"

    def _generate_action_items(self) -> List[Dict]:
        """Generate action items based on context"""
        items = []

        # Based on untested assumptions
        untested = [a for a in self.assumptions if a.status == "untested" and a.criticality == "critical"]
        for a in untested[:2]:
            items.append({
                "text": f"Validate assumption: {a.text[:50]}...",
                "priority": "high",
                "completed": False
            })

        # Based on evidence gaps
        gaps = self._identify_gaps()
        for gap in gaps[:2]:
            items.append({
                "text": f"Address: {gap}",
                "priority": "medium",
                "completed": False
            })

        return items

    def _generate_research_items(self) -> List[Dict]:
        """Generate research items based on gaps"""
        items = []
        gaps = self._identify_gaps()

        if "user research" in " ".join(gaps).lower():
            items.append({
                "id": "r1",
                "title": "Customer Interviews",
                "description": "Gather direct user feedback",
                "category": "customer",
                "status": "planned",
                "priority": "high"
            })

        if "evidence" in " ".join(gaps).lower():
            items.append({
                "id": "r2",
                "title": "Market Research",
                "description": "Gather market data and trends",
                "category": "market",
                "status": "planned",
                "priority": "medium"
            })

        return items

    def _generate_tips(self) -> List[str]:
        """Generate contextual tips"""
        tips = []

        if len(self.assumptions) > 3 and len([a for a in self.assumptions if a.status == "validated"]) == 0:
            tips.append("You have several untested assumptions. Consider validating the most critical ones first.")

        if len(self.evidence) < 3:
            tips.append("Gather more evidence to strengthen your analysis.")

        if self.framework_recommendations:
            tips.append(f"Consider using {self.framework_recommendations[0].name} for this type of problem.")

        return tips if tips else ["Continue exploring your problem systematically."]

    def _identify_gaps(self) -> List[str]:
        """Identify evidence gaps"""
        gaps = []
        sources = self._count_by_source()

        if sources.get("user", 0) < 2:
            gaps.append("Limited direct user research quotes")
        if sources.get("neo4j", 0) == 0:
            gaps.append("No knowledge graph connections found")
        if len(self.assumptions) > 3 and len([a for a in self.assumptions if a.status == "validated"]) == 0:
            gaps.append("Multiple assumptions but none validated")
        if len(self.evidence) < 5:
            gaps.append("Evidence base is thin - need more sources")

        return gaps

    def _get_context_keywords(self) -> List[str]:
        """Get keywords from current context"""
        keywords = set()
        for r in self.framework_recommendations:
            keywords.update(r.keywords_matched)
        return list(keywords)[:10]


# === NEO4J INTEGRATION ===

async def enrich_from_graph(context: ConversationContext, query: str) -> ConversationContext:
    """Enrich context with Neo4j graph data"""
    try:
        from tools.graphrag_lite import query_lazy_graph

        # Query for related concepts
        results = await query_lazy_graph(query, limit=5)

        for result in results:
            context.evidence.append(Evidence(
                id=f"neo4j_{hash(str(result)) % 100000:05d}",
                content=result.get("content", str(result)),
                source_type="neo4j",
                relevance=result.get("score", 0.7),
                tags=["graph", "framework"],
                timestamp=datetime.now().isoformat()
            ))

    except ImportError:
        pass  # Neo4j not available
    except Exception as e:
        print(f"Graph enrichment error: {e}")

    return context


# === SINGLETON CONTEXT MANAGER ===

_session_contexts: Dict[str, ConversationContext] = {}

def get_context(session_id: str) -> ConversationContext:
    """Get or create context for session"""
    if session_id not in _session_contexts:
        _session_contexts[session_id] = ConversationContext()
    return _session_contexts[session_id]

def clear_context(session_id: str):
    """Clear context for session"""
    if session_id in _session_contexts:
        del _session_contexts[session_id]
