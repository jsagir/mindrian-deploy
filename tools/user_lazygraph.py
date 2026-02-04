"""
Per-User LazyGraph Memory Architecture
=======================================

Each user gets their own knowledge graph that persists across sessions:
  - Sessions explored
  - Problems identified
  - Assumptions made
  - Frameworks applied
  - Insights discovered
  - Opportunities captured

Uses LightRAG for entity extraction + Neo4j for graph storage.
Follows LazyGraph pattern: bounded cache, on-demand fetch, safe for 512MB.

Graph Schema:
  (:User {email: "john@example.com"})
      -[:HAD_SESSION]-> (:Session {id: "123", date: "2026-02-04"})
      -[:EXPLORED]-> (:Problem {name: "urban farming"})
      -[:APPLIED]-> (:Framework {name: "TTA"})
      -[:MADE_ASSUMPTION]-> (:Assumption {text: "customers will pay"})
      -[:DISCOVERED]-> (:Insight {text: "need validation"})
      -[:FOUND_OPPORTUNITY]-> (:Opportunity {name: "..."})
"""

import os
import time
import json
import hashlib
import logging
import requests
from typing import Optional, Dict, List, Any, Set
from datetime import datetime
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("user_lazygraph")

# === Configuration ===
LIGHTRAG_URL = os.getenv("LIGHTRAG_URL", "https://mondrian-ts.onrender.com")
LIGHTRAG_USERNAME = os.getenv("LIGHTRAG_USERNAME", "jsagir")
LIGHTRAG_PASSWORD = os.getenv("LIGHTRAG_PASSWORD", "12345678")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Cache settings (LazyGraph pattern)
_USER_CACHE_TTL = 600  # 10 minutes per user
_MAX_CACHED_USERS = 20  # Bounded: ~2MB max (100KB per user)

# === Data Models ===

@dataclass
class UserSession:
    """A user's session with Mindrian."""
    session_id: str
    user_id: str
    started_at: str
    bot_id: str = ""
    phase: str = ""
    turn_count: int = 0

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()


@dataclass
class UserProblem:
    """A problem the user explored."""
    id: str
    name: str
    description: str = ""
    domain: str = ""
    session_id: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"prob_{hashlib.sha256(self.name.encode()).hexdigest()[:8]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class UserAssumption:
    """An assumption the user made."""
    id: str
    text: str
    status: str = "untested"  # untested, testing, validated, invalidated
    session_id: str = ""
    problem_id: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"assum_{hashlib.sha256(self.text.encode()).hexdigest()[:8]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class UserInsight:
    """An insight the user discovered."""
    id: str
    text: str
    source: str = ""  # Which bot/framework generated it
    confidence: float = 0.5
    session_id: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"ins_{hashlib.sha256(self.text.encode()).hexdigest()[:8]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class UserMemory:
    """Aggregated user memory from LazyGraph."""
    user_id: str
    sessions: List[UserSession] = field(default_factory=list)
    problems: List[UserProblem] = field(default_factory=list)
    assumptions: List[UserAssumption] = field(default_factory=list)
    insights: List[UserInsight] = field(default_factory=list)
    frameworks_used: List[str] = field(default_factory=list)
    domains_explored: List[str] = field(default_factory=list)
    last_session_id: str = ""
    total_turns: int = 0
    loaded_at: float = 0.0  # For cache TTL


# === Bounded User Cache (LazyGraph pattern) ===

class _UserLazyCache:
    """
    Bounded per-user memory cache.

    Memory budget: ~100KB per user * 20 users = ~2MB max
    Safe for 512MB Render instances.
    """
    __slots__ = ("_cache", "_access_order", "_max_size")

    def __init__(self, max_size: int = _MAX_CACHED_USERS):
        self._cache: Dict[str, UserMemory] = {}
        self._access_order: List[str] = []  # LRU order
        self._max_size = max_size

    def get(self, user_id: str) -> Optional[UserMemory]:
        """Get user memory if cached and not expired."""
        if user_id not in self._cache:
            return None

        memory = self._cache[user_id]
        now = time.monotonic()

        # Check TTL
        if (now - memory.loaded_at) > _USER_CACHE_TTL:
            del self._cache[user_id]
            self._access_order.remove(user_id)
            return None

        # Update LRU order
        if user_id in self._access_order:
            self._access_order.remove(user_id)
        self._access_order.append(user_id)

        return memory

    def put(self, user_id: str, memory: UserMemory) -> None:
        """Store user memory, evicting LRU if at capacity."""
        # Evict if at capacity
        while len(self._cache) >= self._max_size and self._access_order:
            oldest = self._access_order.pop(0)
            if oldest in self._cache:
                del self._cache[oldest]

        memory.loaded_at = time.monotonic()
        self._cache[user_id] = memory

        if user_id in self._access_order:
            self._access_order.remove(user_id)
        self._access_order.append(user_id)

    def invalidate(self, user_id: str) -> None:
        """Remove user from cache (after graph update)."""
        if user_id in self._cache:
            del self._cache[user_id]
        if user_id in self._access_order:
            self._access_order.remove(user_id)

    def stats(self) -> Dict:
        return {
            "cached_users": len(self._cache),
            "max_size": self._max_size,
            "lru_order": self._access_order[-5:],  # Last 5 accessed
        }


# Global user cache
_user_cache = _UserLazyCache()


# === Neo4j Connection ===

_neo4j_driver = None

def _get_neo4j():
    """Get or create Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is None:
        try:
            from neo4j import GraphDatabase
            uri = os.getenv("NEO4J_URI")
            user = os.getenv("NEO4J_USER")
            password = os.getenv("NEO4J_PASSWORD")
            if all([uri, user, password]):
                _neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
    return _neo4j_driver


# === LightRAG Integration ===

_lightrag_token = None

def _get_lightrag_session() -> Optional[requests.Session]:
    """Get authenticated LightRAG session."""
    global _lightrag_token

    try:
        session = requests.Session()

        if not _lightrag_token:
            resp = requests.post(
                f"{LIGHTRAG_URL}/login",
                data={"username": LIGHTRAG_USERNAME, "password": LIGHTRAG_PASSWORD},
                timeout=15
            )
            if resp.status_code == 200:
                _lightrag_token = resp.json().get("access_token")
            else:
                logger.warning(f"LightRAG login failed: {resp.status_code}")
                return None

        session.headers.update({"Authorization": f"Bearer {_lightrag_token}"})
        return session

    except Exception as e:
        logger.warning(f"LightRAG session error: {e}")
        return None


async def extract_entities_lightrag(text: str) -> Dict[str, List]:
    """
    Use LightRAG to extract entities from conversation text.

    Returns:
        {
            "problems": ["problem1", "problem2"],
            "assumptions": ["assumption1"],
            "insights": ["insight1"],
            "frameworks": ["TTA", "JTBD"],
            "domains": ["education", "technology"]
        }
    """
    # Use Gemini for entity extraction (same as lightrag_graph_push.py)
    if not GOOGLE_API_KEY:
        return {"problems": [], "assumptions": [], "insights": [], "frameworks": [], "domains": []}

    prompt = """Analyze this conversation and extract structured elements for a PWS (Problems Worth Solving) knowledge graph.

Return JSON with this exact format:
{
  "problems": ["problem description 1", "problem description 2"],
  "assumptions": ["assumption text 1", "assumption text 2"],
  "insights": ["insight or discovery 1", "insight 2"],
  "frameworks": ["Framework Name 1", "Framework Name 2"],
  "domains": ["domain or industry 1", "domain 2"]
}

Rules:
- Problems: Challenges, constraints, pain points the user is exploring
- Assumptions: Things the user believes but hasn't validated
- Insights: Discoveries, realizations, validated learnings
- Frameworks: PWS methodologies mentioned (TTA, JTBD, S-Curve, Red Team, Ackoff, etc.)
- Domains: Industries, fields, or areas of focus
- Keep each item concise (1 sentence max)
- Return empty arrays if nothing found

Conversation:
"""

    try:
        from google import genai

        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt + text[:4000],  # Limit input size
            config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            }
        )

        result = json.loads(response.text)
        return {
            "problems": result.get("problems", []),
            "assumptions": result.get("assumptions", []),
            "insights": result.get("insights", []),
            "frameworks": result.get("frameworks", []),
            "domains": result.get("domains", []),
        }

    except Exception as e:
        logger.warning(f"LightRAG extraction error: {e}")
        return {"problems": [], "assumptions": [], "insights": [], "frameworks": [], "domains": []}


# === Neo4j Graph Operations ===

async def store_session(session: UserSession) -> bool:
    """Store session in user's graph."""
    driver = _get_neo4j()
    if not driver:
        return False

    try:
        with driver.session() as db_session:
            db_session.run("""
                MERGE (u:User {id: $user_id})
                MERGE (s:Session {id: $session_id})
                SET s.started_at = $started_at,
                    s.bot_id = $bot_id,
                    s.phase = $phase,
                    s.turn_count = $turn_count
                MERGE (u)-[:HAD_SESSION]->(s)
            """, {
                "user_id": session.user_id,
                "session_id": session.session_id,
                "started_at": session.started_at,
                "bot_id": session.bot_id,
                "phase": session.phase,
                "turn_count": session.turn_count,
            })

        _user_cache.invalidate(session.user_id)
        return True

    except Exception as e:
        logger.error(f"Store session error: {e}")
        return False


async def store_problem(user_id: str, problem: UserProblem) -> bool:
    """Store problem in user's graph."""
    driver = _get_neo4j()
    if not driver:
        return False

    try:
        with driver.session() as session:
            session.run("""
                MERGE (u:User {id: $user_id})
                MERGE (p:Problem {id: $problem_id})
                SET p.name = $name,
                    p.description = $description,
                    p.domain = $domain,
                    p.created_at = $created_at
                MERGE (u)-[:EXPLORED]->(p)

                WITH p
                WHERE $domain IS NOT NULL AND $domain <> ''
                MERGE (d:Domain {name: $domain})
                MERGE (p)-[:IN_DOMAIN]->(d)
            """, {
                "user_id": user_id,
                "problem_id": problem.id,
                "name": problem.name,
                "description": problem.description,
                "domain": problem.domain,
                "created_at": problem.created_at,
            })

            # Link to session if provided
            if problem.session_id:
                session.run("""
                    MATCH (p:Problem {id: $problem_id})
                    MATCH (s:Session {id: $session_id})
                    MERGE (p)-[:EXPLORED_IN]->(s)
                """, {"problem_id": problem.id, "session_id": problem.session_id})

        _user_cache.invalidate(user_id)
        return True

    except Exception as e:
        logger.error(f"Store problem error: {e}")
        return False


async def store_assumption(user_id: str, assumption: UserAssumption) -> bool:
    """Store assumption in user's graph."""
    driver = _get_neo4j()
    if not driver:
        return False

    try:
        with driver.session() as session:
            session.run("""
                MERGE (u:User {id: $user_id})
                MERGE (a:Assumption {id: $assumption_id})
                SET a.text = $text,
                    a.status = $status,
                    a.created_at = $created_at
                MERGE (u)-[:MADE_ASSUMPTION]->(a)
            """, {
                "user_id": user_id,
                "assumption_id": assumption.id,
                "text": assumption.text,
                "status": assumption.status,
                "created_at": assumption.created_at,
            })

            # Link to problem if provided
            if assumption.problem_id:
                session.run("""
                    MATCH (a:Assumption {id: $assumption_id})
                    MATCH (p:Problem {id: $problem_id})
                    MERGE (a)-[:ABOUT]->(p)
                """, {"assumption_id": assumption.id, "problem_id": assumption.problem_id})

            # Link to session if provided
            if assumption.session_id:
                session.run("""
                    MATCH (a:Assumption {id: $assumption_id})
                    MATCH (s:Session {id: $session_id})
                    MERGE (a)-[:MADE_IN]->(s)
                """, {"assumption_id": assumption.id, "session_id": assumption.session_id})

        _user_cache.invalidate(user_id)
        return True

    except Exception as e:
        logger.error(f"Store assumption error: {e}")
        return False


async def store_insight(user_id: str, insight: UserInsight) -> bool:
    """Store insight in user's graph."""
    driver = _get_neo4j()
    if not driver:
        return False

    try:
        with driver.session() as session:
            session.run("""
                MERGE (u:User {id: $user_id})
                MERGE (i:Insight {id: $insight_id})
                SET i.text = $text,
                    i.source = $source,
                    i.confidence = $confidence,
                    i.created_at = $created_at
                MERGE (u)-[:DISCOVERED]->(i)
            """, {
                "user_id": user_id,
                "insight_id": insight.id,
                "text": insight.text,
                "source": insight.source,
                "confidence": insight.confidence,
                "created_at": insight.created_at,
            })

            # Link to session if provided
            if insight.session_id:
                session.run("""
                    MATCH (i:Insight {id: $insight_id})
                    MATCH (s:Session {id: $session_id})
                    MERGE (i)-[:DISCOVERED_IN]->(s)
                """, {"insight_id": insight.id, "session_id": insight.session_id})

        _user_cache.invalidate(user_id)
        return True

    except Exception as e:
        logger.error(f"Store insight error: {e}")
        return False


async def store_framework_usage(user_id: str, framework: str, session_id: str = "") -> bool:
    """Record that user applied a framework."""
    driver = _get_neo4j()
    if not driver:
        return False

    try:
        with driver.session() as session:
            session.run("""
                MERGE (u:User {id: $user_id})
                MERGE (f:Framework {name: $framework})
                MERGE (u)-[r:APPLIED]->(f)
                SET r.last_used = datetime()
                SET r.count = COALESCE(r.count, 0) + 1
            """, {"user_id": user_id, "framework": framework})

            if session_id:
                session.run("""
                    MATCH (s:Session {id: $session_id})
                    MATCH (f:Framework {name: $framework})
                    MERGE (s)-[:USED_FRAMEWORK]->(f)
                """, {"session_id": session_id, "framework": framework})

        _user_cache.invalidate(user_id)
        return True

    except Exception as e:
        logger.error(f"Store framework usage error: {e}")
        return False


# === User Memory Loading ===

async def load_user_memory(user_id: str) -> UserMemory:
    """
    Load user's complete memory from Neo4j.
    Uses cache for fast repeated access.
    """
    # Check cache first
    cached = _user_cache.get(user_id)
    if cached:
        logger.debug(f"User memory cache hit: {user_id}")
        return cached

    driver = _get_neo4j()
    if not driver:
        return UserMemory(user_id=user_id)

    memory = UserMemory(user_id=user_id)

    try:
        with driver.session() as session:
            # Load sessions
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:HAD_SESSION]->(s:Session)
                RETURN s.id AS id, s.started_at AS started_at,
                       s.bot_id AS bot_id, s.phase AS phase, s.turn_count AS turn_count
                ORDER BY s.started_at DESC
                LIMIT 20
            """, {"user_id": user_id})

            for r in result:
                memory.sessions.append(UserSession(
                    session_id=r["id"],
                    user_id=user_id,
                    started_at=r["started_at"] or "",
                    bot_id=r["bot_id"] or "",
                    phase=r["phase"] or "",
                    turn_count=r["turn_count"] or 0,
                ))

            if memory.sessions:
                memory.last_session_id = memory.sessions[0].session_id
                memory.total_turns = sum(s.turn_count for s in memory.sessions)

            # Load problems
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:EXPLORED]->(p:Problem)
                RETURN p.id AS id, p.name AS name, p.description AS description,
                       p.domain AS domain, p.created_at AS created_at
                ORDER BY p.created_at DESC
                LIMIT 30
            """, {"user_id": user_id})

            for r in result:
                memory.problems.append(UserProblem(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"] or "",
                    domain=r["domain"] or "",
                    created_at=r["created_at"] or "",
                ))

            # Load assumptions
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:MADE_ASSUMPTION]->(a:Assumption)
                RETURN a.id AS id, a.text AS text, a.status AS status, a.created_at AS created_at
                ORDER BY a.created_at DESC
                LIMIT 50
            """, {"user_id": user_id})

            for r in result:
                memory.assumptions.append(UserAssumption(
                    id=r["id"],
                    text=r["text"],
                    status=r["status"] or "untested",
                    created_at=r["created_at"] or "",
                ))

            # Load insights
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:DISCOVERED]->(i:Insight)
                RETURN i.id AS id, i.text AS text, i.source AS source,
                       i.confidence AS confidence, i.created_at AS created_at
                ORDER BY i.created_at DESC
                LIMIT 50
            """, {"user_id": user_id})

            for r in result:
                memory.insights.append(UserInsight(
                    id=r["id"],
                    text=r["text"],
                    source=r["source"] or "",
                    confidence=r["confidence"] or 0.5,
                    created_at=r["created_at"] or "",
                ))

            # Load frameworks used
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:APPLIED]->(f:Framework)
                RETURN f.name AS name
            """, {"user_id": user_id})
            memory.frameworks_used = [r["name"] for r in result]

            # Load domains explored
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:EXPLORED]->(p:Problem)-[:IN_DOMAIN]->(d:Domain)
                RETURN DISTINCT d.name AS name
            """, {"user_id": user_id})
            memory.domains_explored = [r["name"] for r in result]

        # Cache the result
        _user_cache.put(user_id, memory)
        logger.info(f"Loaded user memory: {user_id} - {len(memory.sessions)} sessions, {len(memory.problems)} problems")

        return memory

    except Exception as e:
        logger.error(f"Load user memory error: {e}")
        return UserMemory(user_id=user_id)


# === Main Entry Point ===

async def process_conversation_turn(
    user_id: str,
    session_id: str,
    conversation: List[Dict[str, str]],
    bot_id: str = "",
    phase: str = ""
) -> Dict[str, Any]:
    """
    Process a conversation turn and extract/store user knowledge.

    Called after each turn to update the user's LazyGraph.

    Args:
        user_id: User's email or ID
        session_id: Current session ID
        conversation: List of {"role": "user"|"assistant", "content": "..."}
        bot_id: Current bot (lawrence, tta, etc.)
        phase: Current workshop phase

    Returns:
        {
            "extracted": {"problems": [...], "assumptions": [...], ...},
            "stored": {"problems": 1, "assumptions": 2, ...},
            "user_memory_summary": {...}
        }
    """
    result = {
        "extracted": {},
        "stored": {"problems": 0, "assumptions": 0, "insights": 0, "frameworks": 0},
        "user_memory_summary": {},
    }

    if not user_id or not session_id:
        return result

    # Format conversation for extraction (last 10 turns)
    conv_text = "\n".join([
        f"{'USER' if msg.get('role') == 'user' else 'ASSISTANT'}: {msg.get('content', '')}"
        for msg in conversation[-10:]
    ])

    # Extract entities using LightRAG/Gemini
    extracted = await extract_entities_lightrag(conv_text)
    result["extracted"] = extracted

    # Store session
    await store_session(UserSession(
        session_id=session_id,
        user_id=user_id,
        started_at="",
        bot_id=bot_id,
        phase=phase,
        turn_count=len(conversation),
    ))

    # Store problems
    for prob_text in extracted.get("problems", [])[:3]:  # Limit to 3 per turn
        domain = extracted.get("domains", [""])[0] if extracted.get("domains") else ""
        await store_problem(user_id, UserProblem(
            id="",
            name=prob_text[:100],
            description=prob_text,
            domain=domain,
            session_id=session_id,
        ))
        result["stored"]["problems"] += 1

    # Store assumptions
    for assum_text in extracted.get("assumptions", [])[:3]:
        await store_assumption(user_id, UserAssumption(
            id="",
            text=assum_text,
            session_id=session_id,
        ))
        result["stored"]["assumptions"] += 1

    # Store insights
    for ins_text in extracted.get("insights", [])[:3]:
        await store_insight(user_id, UserInsight(
            id="",
            text=ins_text,
            source=bot_id,
            session_id=session_id,
        ))
        result["stored"]["insights"] += 1

    # Store frameworks
    for framework in extracted.get("frameworks", []):
        await store_framework_usage(user_id, framework, session_id)
        result["stored"]["frameworks"] += 1

    # Load and return user memory summary
    memory = await load_user_memory(user_id)
    result["user_memory_summary"] = {
        "total_sessions": len(memory.sessions),
        "total_problems": len(memory.problems),
        "total_assumptions": len(memory.assumptions),
        "total_insights": len(memory.insights),
        "frameworks_used": memory.frameworks_used,
        "domains_explored": memory.domains_explored,
    }

    return result


async def get_user_context_for_llm(user_id: str, max_items: int = 5) -> str:
    """
    Get a concise context string about the user for the LLM.

    Returns something like:
        "Returning user (3 sessions). Explored: urban farming, education tech.
         Applied: TTA, JTBD. Key assumptions: 'customers will pay' (untested)."
    """
    if not user_id:
        return ""

    memory = await load_user_memory(user_id)

    if not memory.sessions:
        return ""  # New user

    parts = []

    # Session count
    session_count = len(memory.sessions)
    if session_count == 1:
        parts.append("Returning user (1 previous session)")
    else:
        parts.append(f"Returning user ({session_count} sessions)")

    # Problems explored
    if memory.problems:
        prob_names = [p.name[:30] for p in memory.problems[:max_items]]
        parts.append(f"Explored: {', '.join(prob_names)}")

    # Frameworks applied
    if memory.frameworks_used:
        parts.append(f"Applied: {', '.join(memory.frameworks_used[:max_items])}")

    # Key untested assumptions
    untested = [a for a in memory.assumptions if a.status == "untested"][:max_items]
    if untested:
        assum_texts = [f"'{a.text[:40]}'" for a in untested]
        parts.append(f"Untested assumptions: {', '.join(assum_texts)}")

    # Recent insights
    if memory.insights:
        recent = memory.insights[0]
        parts.append(f"Recent insight: '{recent.text[:50]}...'")

    return ". ".join(parts)


def get_cache_stats() -> Dict:
    """Get user cache statistics for monitoring."""
    return _user_cache.stats()
