"""
Context Engine — Budget-Aware Context Assembly for All Mindrian Bots
====================================================================

Applies to ALL bots across Mindrian: Lawrence, Larry Playground, TTA,
JTBD, S-Curve, Ackoff, Red Team, Validation, and any future agents.

Implements context engineering principles for KG-RAG:
- Layered context assembly with priority-based budgets
- Dynamic retrieval strategy selection (vector-first, text-to-cypher, hybrid)
- Graph expansion with hop control
- Cross-domain connection surfacing
- Session-aware deduplication
- Invisible methodology injection
- A2A protocol integration (classification, handoff context, agent transitions)

Integrates with existing pipeline:
- graphrag_lite.py: Vector + graph retrieval
- invisible_router.py: Methodology detection + injection
- langextract.py: Signal extraction
- session_memory.py: Conversation memory
- protocols/: A2A orchestration, classification, context journal

Usage in mindrian_chat.py:
    from tools.context_engine import assemble_context, ContextLayer

    context_result = assemble_context(
        user_message=message.content,
        history=history,
        turn_count=turn_count,
        bot_id=bot_id,
        excluded_topics=excluded_topics,
        a2a_context=a2a_pre_result,       # A2A classification + routing
    )
    # context_result.enriched_message  -> user message + invisible context
    # context_result.system_addendum   -> additions to system prompt
    # context_result.layers_used       -> which layers contributed
"""

import os
import re
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger("context_engine")

# Token budget defaults (conservative for Gemini Flash context)
DEFAULT_CONTEXT_BUDGET = 6000  # tokens reserved for injected context
TOKENS_PER_CHAR = 0.25  # rough estimate for English/Hebrew mix


@dataclass
class ContextLayer:
    """A single layer of assembled context."""
    priority: int           # 1=highest (always), 4=lowest (optional)
    label: str              # human-readable label for logging
    content: str            # actual context text
    source: str             # where it came from
    token_estimate: int = 0 # estimated tokens

    def __post_init__(self):
        if not self.token_estimate:
            self.token_estimate = int(len(self.content) * TOKENS_PER_CHAR)


@dataclass
class ContextResult:
    """Output of context assembly."""
    enriched_message: str           # user message + invisible context appended
    system_addendum: str            # additions to system prompt
    layers_used: List[str]          # which layers contributed
    total_tokens_injected: int = 0  # estimated tokens used
    retrieval_strategy: str = ""    # which strategy was selected
    latency_ms: int = 0             # total context assembly time


def estimate_tokens(text: str) -> int:
    """Rough token estimate for budget management."""
    return int(len(text) * TOKENS_PER_CHAR)


def classify_query_intent(user_message: str, turn_count: int) -> str:
    """
    Fast regex-based query classification to select retrieval strategy.
    No LLM call — runs in <1ms.

    Returns: 'factual' | 'analytical' | 'exploratory' | 'convergent'
    """
    msg_lower = user_message.lower().strip()

    # Convergent: user wants answers, not more questions
    convergent_patterns = [
        r"just (give|tell) me",
        r"summarize",
        r"what('s| is) (the|your) (answer|recommendation|take)",
        r"bottom line",
        r"i('m| am) done (thinking|exploring)",
        r"wrap.?up",
    ]
    for pat in convergent_patterns:
        if re.search(pat, msg_lower):
            return "convergent"

    # Analytical: structured/aggregate questions
    analytical_patterns = [
        r"how many",
        r"which (team|project|person)",
        r"compare",
        r"list (all|the)",
        r"what('s| is) the (status|count|total)",
        r"show me (all|the)",
    ]
    for pat in analytical_patterns:
        if re.search(pat, msg_lower):
            return "analytical"

    # Factual: direct knowledge lookup
    factual_patterns = [
        r"what (is|are|does)",
        r"define\b",
        r"explain\b",
        r"tell me about",
        r"who (is|was)",
    ]
    for pat in factual_patterns:
        if re.search(pat, msg_lower):
            return "factual"

    # Default: exploratory (most coaching conversations)
    return "exploratory"


def select_retrieval_depth(intent: str, turn_count: int) -> Dict[str, Any]:
    """
    Select retrieval parameters based on query intent and conversation stage.
    Implements dynamic context selection — not the same depth for every query.
    """
    if intent == "convergent":
        # User wants closure — minimal new context, focus on synthesis
        return {
            "vector_k": 2,
            "max_hops": 0,
            "include_cross_domain": False,
            "include_definitions": False,
            "budget_fraction": 0.3,
        }

    if intent == "analytical":
        # Structured query — prefer graph traversal over vector
        return {
            "vector_k": 3,
            "max_hops": 2,
            "include_cross_domain": False,
            "include_definitions": True,
            "budget_fraction": 0.5,
        }

    if intent == "factual":
        # Direct lookup — moderate context
        return {
            "vector_k": 5,
            "max_hops": 1,
            "include_cross_domain": False,
            "include_definitions": True,
            "budget_fraction": 0.5,
        }

    # Exploratory (default for coaching)
    return {
        "vector_k": 5,
        "max_hops": 2,
        "include_cross_domain": turn_count > 3,  # only after rapport built
        "include_definitions": turn_count > 1,
        "budget_fraction": 0.7,
    }


def deduplicate_context(layers: List[ContextLayer], history: list) -> List[ContextLayer]:
    """
    Session-aware deduplication.
    Remove context that was already surfaced in recent conversation turns.
    """
    if not history:
        return layers

    # Build a set of recently-discussed content fingerprints
    recent_content = ""
    for msg in history[-6:]:  # last 3 exchanges
        if isinstance(msg, dict):
            recent_content += msg.get("content", msg.get("parts", [""])[0] if isinstance(msg.get("parts"), list) else "") + " "
        elif isinstance(msg, str):
            recent_content += msg + " "
    recent_lower = recent_content.lower()

    deduped = []
    for layer in layers:
        # Check if >60% of this layer's key terms are in recent conversation
        words = set(re.findall(r'\b[a-zA-Z]{4,}\b', layer.content.lower()))
        if not words:
            deduped.append(layer)
            continue
        overlap = sum(1 for w in words if w in recent_lower)
        overlap_ratio = overlap / len(words) if words else 0

        if overlap_ratio < 0.6:
            deduped.append(layer)
        else:
            logger.debug("Deduped layer '%s' (%.0f%% overlap with recent turns)", layer.label, overlap_ratio * 100)

    return deduped


def assemble_context(
    user_message: str,
    history: list,
    turn_count: int,
    bot_id: str = "lawrence",
    excluded_topics: Optional[List[str]] = None,
    graphrag_hint: Optional[str] = None,
    extraction_signals: Optional[Dict] = None,
    methodology_injection: Optional[str] = None,
    journey_context: Optional[str] = None,
    a2a_context: Optional[Dict] = None,
) -> ContextResult:
    """
    Budget-aware layered context assembly for ALL Mindrian bots.

    Layers (by priority):
        1. GraphRAG hints (vector + graph expansion)
        2. A2A classification + routing context
        3. Methodology injection (from invisible router)
        4. Extraction signals (from langextract)
        5. Cross-domain connections (from creative leaps)
        6. Journey memory (cross-session context)

    All layers are invisible to the user — injected into the message
    or system prompt without announcement.
    """
    t0 = time.monotonic()
    layers: List[ContextLayer] = []
    system_layers: List[ContextLayer] = []

    # Classify intent and select depth
    intent = classify_query_intent(user_message, turn_count)
    depth = select_retrieval_depth(intent, turn_count)
    budget = int(DEFAULT_CONTEXT_BUDGET * depth["budget_fraction"])

    logger.info("Context engine: intent=%s, budget=%d tokens, turn=%d", intent, budget, turn_count)

    # === Layer 1: GraphRAG hints (already computed upstream) ===
    if graphrag_hint:
        layers.append(ContextLayer(
            priority=1,
            label="graphrag",
            content=graphrag_hint,
            source="graphrag_lite",
        ))

    # === Layer 1.5: A2A Protocol context (classification + routing) ===
    if a2a_context and a2a_context.get("enabled"):
        a2a_parts = []
        # Cynefin + PWS classification
        classification = a2a_context.get("classification", {})
        if classification:
            cynefin = classification.get("cynefin", "")
            pws = classification.get("pws", "")
            if cynefin or pws:
                a2a_parts.append(f"[A2A Classification: Cynefin={cynefin}, PWS={pws}]")
        # Phase awareness
        phase = a2a_context.get("current_phase", "")
        if phase:
            a2a_parts.append(f"[A2A Phase: {phase}]")
        # Context hint from orchestrator
        context_hint = a2a_context.get("context_hint", "")
        if context_hint:
            a2a_parts.append(context_hint)
        # Routing suggestion (invisible to user, shapes response)
        suggested = a2a_context.get("suggested_agent", "")
        if suggested and suggested != bot_id:
            a2a_parts.append(f"[A2A: {suggested} may be better suited for this topic]")

        if a2a_parts:
            layers.append(ContextLayer(
                priority=2,
                label="a2a_protocol",
                content=" ".join(a2a_parts),
                source="a2a_orchestrator",
            ))

    # === Layer 2: Methodology injection (goes into system prompt) ===
    if methodology_injection:
        system_layers.append(ContextLayer(
            priority=2,
            label="methodology",
            content=methodology_injection,
            source="invisible_router",
        ))

    # === Layer 3: Extraction signals ===
    if extraction_signals and not extraction_signals.get("empty"):
        try:
            from tools.langextract import get_extraction_hint
            hint = get_extraction_hint(extraction_signals, turn_count)
            if hint:
                layers.append(ContextLayer(
                    priority=3,
                    label="extraction",
                    content=hint,
                    source="langextract",
                ))
        except Exception:
            pass

    # === Layer 4: Saturation detection (turn 8+) ===
    if turn_count >= 8:
        try:
            from tools.smart_phase_tracker import detect_saturation
            sat = detect_saturation(history)
            if sat.get("saturated"):
                layers.append(ContextLayer(
                    priority=3,
                    label="saturation",
                    content=f"[System: Conversation saturation detected ({sat['signal']}). Consider suggesting convergence.]",
                    source="phase_tracker",
                ))
        except Exception:
            pass

    # === Layer 5: Journey memory (lowest priority, highest token cost) ===
    if journey_context:
        layers.append(ContextLayer(
            priority=5,
            label="journey",
            content=journey_context,
            source="journey_memory",
        ))

    # === Deduplication ===
    layers = deduplicate_context(layers, history)

    # === Budget enforcement ===
    # Sort by priority (ascending = highest priority first)
    layers.sort(key=lambda x: x.priority)
    system_layers.sort(key=lambda x: x.priority)

    used_tokens = 0
    kept_layers = []
    for layer in layers:
        if used_tokens + layer.token_estimate <= budget:
            kept_layers.append(layer)
            used_tokens += layer.token_estimate
        else:
            logger.info("Context budget: dropped layer '%s' (%d tokens over budget)",
                       layer.label, layer.token_estimate)

    # === Assemble output ===
    enriched_message = user_message
    for layer in kept_layers:
        enriched_message += f"\n\n{layer.content}"

    system_addendum = ""
    for layer in system_layers:
        system_addendum += f"\n\n{layer.content}\n"

    elapsed_ms = int((time.monotonic() - t0) * 1000)

    result = ContextResult(
        enriched_message=enriched_message,
        system_addendum=system_addendum,
        layers_used=[l.label for l in kept_layers] + [l.label for l in system_layers],
        total_tokens_injected=used_tokens + sum(l.token_estimate for l in system_layers),
        retrieval_strategy=f"{intent}:{depth['vector_k']}k:{depth['max_hops']}hop",
        latency_ms=elapsed_ms,
    )

    logger.info(
        "Context assembled: layers=%s, tokens=%d, strategy=%s, latency=%dms",
        result.layers_used, result.total_tokens_injected,
        result.retrieval_strategy, result.latency_ms,
    )

    return result


# ============================================================
# GRAPH EXPANSION UTILITIES (for future deeper integration)
# ============================================================

def expand_from_hits(hit_ids: List[str], max_hops: int = 2,
                     follow_rels: Optional[List[str]] = None) -> List[Dict]:
    """
    N-hop graph expansion from vector search hits.
    Uses existing Neo4j driver from graphrag_lite.

    Pattern: Vector-First with Graph Expansion (Pattern 1)
    """
    try:
        from tools.graphrag_lite import _get_neo4j
        driver = _get_neo4j()
        if not driver:
            return []

        if follow_rels is None:
            follow_rels = ["CONTAINS", "REFERENCES", "DEFINES",
                          "HAS_COMPONENT", "REQUIRES", "CO_OCCURS"]

        rel_filter = "|".join(follow_rels)

        results = []
        with driver.session() as session:
            for hit_id in hit_ids[:5]:  # cap at 5 hits
                query = """
                MATCH (hit) WHERE elementId(hit) = $hitId
                CALL apoc.path.subgraphNodes(hit, {
                    maxLevel: $maxHops,
                    relationshipFilter: $relFilter
                })
                YIELD node AS related
                WHERE related <> hit
                RETURN related.name AS name,
                       labels(related)[0] AS label,
                       related.description AS description
                LIMIT 10
                """
                try:
                    records = session.run(query, hitId=hit_id,
                                         maxHops=max_hops, relFilter=rel_filter)
                    for r in records:
                        results.append({
                            "name": r["name"],
                            "label": r["label"],
                            "description": r["description"],
                        })
                except Exception:
                    pass  # graceful fallback per hit

        return results

    except Exception as e:
        logger.debug("Graph expansion failed: %s", e)
        return []


def resolve_definitions(text: str) -> List[Dict[str, str]]:
    """
    Definition-aware retrieval (Pattern 4).
    Finds defined terms in text and looks them up in the knowledge graph.
    """
    try:
        from tools.graphrag_lite import _get_neo4j
        driver = _get_neo4j()
        if not driver:
            return []

        # Extract potential defined terms (capitalized multi-word phrases, quoted terms)
        candidates = set()
        # Capitalized phrases: "Problem Worth Solving", "Jobs to Be Done"
        candidates.update(re.findall(r'(?:[A-Z][a-z]+(?:\s+(?:to|the|of|and|in|for|a)\s+)?){2,}', text))
        # Quoted terms
        candidates.update(re.findall(r'"([^"]+)"', text))
        candidates.update(re.findall(r"'([^']+)'", text))

        if not candidates:
            return []

        definitions = []
        with driver.session() as session:
            for term in list(candidates)[:10]:  # cap lookups
                query = """
                MATCH (c:Concept)
                WHERE toLower(c.name) = toLower($term)
                RETURN c.name AS term, c.description AS definition
                LIMIT 1
                """
                records = session.run(query, term=term.strip())
                for r in records:
                    if r["definition"]:
                        definitions.append({
                            "term": r["term"],
                            "definition": r["definition"][:200],
                        })

        return definitions

    except Exception as e:
        logger.debug("Definition resolution failed: %s", e)
        return []
