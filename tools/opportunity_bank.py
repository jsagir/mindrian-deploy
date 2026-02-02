"""
Bank of Opportunities - PWS-Compliant Opportunity Registry
==========================================================

Automatically extracts innovation opportunities from ANY conversation with Mindrian agents
and stores them in a persistent, searchable knowledge base following PWS methodology.

Storage Architecture:
- Supabase Table: opportunity_bank (primary structured storage)
- Supabase Storage: JSON files (backwards compatibility)
- Neo4j: Graph relationships (opportunity → domain, framework, user)
- FileSearch-ready: Document format for semantic retrieval

PWS-Compliant Fields:
- name: Clear, descriptive title
- problem: The constraint/reverse salient being addressed
- value_potential: low/medium/high/transformative
- solution_direction: How it could be solved
- job_to_be_done: JTBD framing
- platform_multiplier: Scalability potential
- created_by: Who identified it (person, AI, framework)
- source_snippet: Key content excerpt
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio

# Gemini for extraction
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Neo4j for graph storage
try:
    from tools.graphrag_lite import query_neo4j, get_neo4j_driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

# LangExtract for enrichment
try:
    from tools.langextract import instant_extract
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

# Supabase for persistence
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")


# ==============================================================================
# EMBEDDING GENERATION (Lazy Cache Pattern)
# ==============================================================================

class _LazyEmbeddingCache:
    """
    Bounded in-memory embedding cache.

    Follows the lazy graph pattern from graphrag_lite:
    - Limited size (~1MB for 100 embeddings @ 1536 dims)
    - LRU eviction when full
    - On-demand computation, never preload all
    """
    __slots__ = ("_cache", "_max_size", "_hits", "_misses")

    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, List[float]] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[List[float]]:
        """Get embedding from cache if available."""
        if key in self._cache:
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, key: str, embedding: List[float]) -> None:
        """Store embedding, evicting oldest if at capacity."""
        if len(self._cache) >= self._max_size:
            # Simple eviction: remove first key (oldest)
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = embedding

    def stats(self) -> Dict[str, int]:
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
        }


# Global lazy embedding cache (bounded, ~1MB)
_embedding_cache = _LazyEmbeddingCache(max_size=100)


def _embedding_cache_key(text: str) -> str:
    """Generate cache key from text (truncated hash)."""
    return hashlib.md5(text[:500].encode()).hexdigest()[:16]


async def generate_embedding(text: str, use_cache: bool = True) -> Optional[List[float]]:
    """
    Generate embedding vector for semantic similarity search.

    Uses Google's text-embedding-004 model (1536 dimensions).
    Implements lazy cache pattern for bounded memory usage.

    Args:
        text: Text to embed (will be truncated to 2048 chars)
        use_cache: Whether to use the in-memory cache (default: True)

    Returns:
        List of floats (embedding vector) or None on error
    """
    if not GEMINI_AVAILABLE:
        return None

    if not text or len(text.strip()) < 10:
        return None

    # Truncate to model limit
    text = text[:2048]

    # Check cache first (lazy pattern)
    if use_cache:
        cache_key = _embedding_cache_key(text)
        cached = _embedding_cache.get(cache_key)
        if cached is not None:
            return cached

    try:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        # Use embedding model
        result = client.models.embed_content(
            model="text-embedding-004",
            content=text
        )

        if result and result.embedding:
            embedding = list(result.embedding.values)

            # Store in cache (lazy pattern - bounded memory)
            if use_cache:
                _embedding_cache.put(cache_key, embedding)

            return embedding
        return None

    except Exception as e:
        print(f"Embedding generation error: {e}")
        return None


async def generate_opportunity_embedding(opportunity: 'Opportunity') -> Optional[List[float]]:
    """
    Generate embedding for an opportunity based on key PWS fields.

    Combines name, description, problem, and job_to_be_done for
    comprehensive semantic representation.
    """
    # Build text from key fields
    parts = [
        opportunity.name,
        opportunity.description,
        opportunity.problem,
        opportunity.job_to_be_done,
        opportunity.solution_direction,
        " ".join(opportunity.tags) if opportunity.tags else ""
    ]
    text = " ".join(p for p in parts if p)

    return await generate_embedding(text)


class OpportunityType(str, Enum):
    """PWS-compliant opportunity types."""
    PWS = "problem_worth_solving"
    UNMET_NEED = "unmet_need"
    MARKET_GAP = "market_gap"
    TECH_OPPORTUNITY = "technology_opportunity"
    PROCESS_IMPROVEMENT = "process_improvement"
    EMERGING_TREND = "emerging_trend"
    VALIDATED_INSIGHT = "validated_insight"
    INNOVATION = "innovation"
    REVERSE_SALIENT = "reverse_salient"
    STRATEGIC = "strategic"


class OpportunityStatus(str, Enum):
    """Opportunity lifecycle status."""
    DRAFT = "draft"
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    PRIORITIZED = "prioritized"
    ACTIONED = "actioned"
    ARCHIVED = "archived"
    IMPLEMENTED = "implemented"


class ValuePotential(str, Enum):
    """PWS value potential assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    TRANSFORMATIVE = "transformative"


class CreatedByType(str, Enum):
    """Who/what created the opportunity."""
    USER = "user"
    AI_AGENT = "ai_agent"
    FRAMEWORK = "framework"
    SYSTEM = "system"


@dataclass
class Opportunity:
    """
    PWS-Compliant Opportunity Model.

    Core PWS Fields:
    - name: Clear, descriptive title
    - description: What is the opportunity
    - problem: The constraint/reverse salient being addressed
    - value_potential: Assessment (low/medium/high/transformative)
    - solution_direction: How it could be solved
    - validation: Evidence it's real
    - job_to_be_done: JTBD framing
    - platform_multiplier: Scalability potential

    Provenance:
    - created_by: Who identified it
    - created_by_type: user/ai_agent/framework/system
    - source_snippet: Key content excerpt
    """
    id: str
    name: str  # PWS uses "name" (aliased as title for backwards compat)
    description: str
    opportunity_type: str = "problem_worth_solving"
    status: str = "discovered"

    # Core PWS Fields
    problem: str = ""  # The constraint/reverse salient
    value_potential: str = "medium"  # low/medium/high/transformative
    solution_direction: str = ""
    validation: str = ""  # Text evidence
    job_to_be_done: str = ""
    platform_multiplier: str = ""

    # Provenance (Who Created It)
    created_by: str = "system"
    created_by_type: str = "system"  # user/ai_agent/framework/system

    # Source Tracking
    source_type: str = ""  # conversation/document/framework/analysis/external
    source_id: str = ""
    source_name: str = ""
    source_snippet: str = ""  # Key content excerpt
    source_url: str = ""
    source_bot: str = ""
    source_phase: str = ""
    source_methodology: str = ""

    # Session tracking
    conversation_id: str = ""
    user_id: str = ""

    # Problem details (legacy + extended)
    domain: str = ""
    subdomain: str = ""
    target_users: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    # LangExtract enrichment
    extraction_method: str = "ai_synthesis"  # manual/langextract/ai_synthesis/hybrid
    extraction_confidence: float = 0.5
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    extracted_keywords: List[str] = field(default_factory=list)

    # Scoring
    differential_score: float = 0.0  # Reverse salient scoring
    feasibility_score: float = 0.0
    impact_score: float = 0.0

    # Validation signals
    confidence_score: float = 0.0  # Legacy alias for extraction_confidence
    validation_status: str = "unvalidated"
    frameworks_applied: List[str] = field(default_factory=list)

    # Sync status
    neo4j_synced: bool = False
    neo4j_node_id: str = ""
    supabase_table_id: str = ""  # UUID from opportunity_bank table

    # Metadata
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = field(default_factory=list)
    related_opportunities: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        # Sync confidence scores
        if self.confidence_score and not self.extraction_confidence:
            self.extraction_confidence = self.confidence_score
        elif self.extraction_confidence and not self.confidence_score:
            self.confidence_score = self.extraction_confidence

    @property
    def title(self) -> str:
        """Alias for backwards compatibility."""
        return self.name

    @title.setter
    def title(self, value: str):
        """Alias setter for backwards compatibility."""
        self.name = value

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        data = asdict(self)
        # Include title alias for backwards compat with JSON storage
        data['title'] = self.name
        return data

    def to_supabase_row(self) -> Dict:
        """Format for Supabase table INSERT."""
        return {
            "name": self.name,
            "description": self.description,
            "problem": self.problem or None,
            "value_potential": self.value_potential,
            "solution_direction": self.solution_direction or None,
            "validation": self.validation or None,
            "job_to_be_done": self.job_to_be_done or None,
            "platform_multiplier": self.platform_multiplier or None,
            "opportunity_type": self.opportunity_type,
            "domain": self.domain or None,
            "subdomain": self.subdomain or None,
            "tags": self.tags or [],
            "created_by": self.created_by,
            "created_by_type": self.created_by_type,
            "source_type": self.source_type or None,
            "source_id": self.source_id or None,
            "source_name": self.source_name or None,
            "source_snippet": self.source_snippet or None,
            "source_url": self.source_url or None,
            "source_bot": self.source_bot or None,
            "source_phase": self.source_phase or None,
            "source_methodology": self.source_methodology or None,
            "extraction_method": self.extraction_method,
            "extraction_confidence": self.extraction_confidence,
            "extracted_entities": self.extracted_entities or {},
            "extracted_keywords": self.extracted_keywords or [],
            "differential_score": self.differential_score or None,
            "feasibility_score": self.feasibility_score or None,
            "impact_score": self.impact_score or None,
            "target_users": self.target_users or [],
            "pain_points": self.pain_points or [],
            "evidence": self.evidence or [],
            "frameworks_applied": self.frameworks_applied or [],
            "related_opportunities": self.related_opportunities or [],
            "status": self.status,
            "validation_status": self.validation_status,
            "user_id": self.user_id or None,
            "conversation_id": self.conversation_id or None,
        }

    def to_filesearch_document(self) -> str:
        """Format as document for FileSearch indexing."""
        doc = f"""# Opportunity: {self.name}

## Summary
{self.description}

## Problem (Reverse Salient)
{self.problem or 'Not specified'}

## Value Assessment
- **Value Potential**: {self.value_potential}
- **Type**: {self.opportunity_type}
- **Domain**: {self.domain}
- **Status**: {self.status}
- **Confidence**: {self.extraction_confidence:.0%}

## Solution Direction
{self.solution_direction or 'Not specified'}

## Job to Be Done
{self.job_to_be_done or 'Not specified'}

## Target Users
{chr(10).join('- ' + u for u in self.target_users) if self.target_users else '- Not specified'}

## Pain Points
{chr(10).join('- ' + p for p in self.pain_points) if self.pain_points else '- Not specified'}

## Evidence / Validation
{self.validation or chr(10).join('- ' + e for e in self.evidence) if self.evidence else '- Not yet validated'}

## Frameworks Applied
{', '.join(self.frameworks_applied) if self.frameworks_applied else 'None yet'}

## Source
- **Created By**: {self.created_by} ({self.created_by_type})
- **Bot**: {self.source_bot}
- **Methodology**: {self.source_methodology}
- **Phase**: {self.source_phase}

## Key Excerpt
> {self.source_snippet or 'No excerpt available'}

## Tags
{', '.join(self.tags) if self.tags else 'None'}

---
ID: {self.id}
Created: {self.created_at}
"""
        return doc


# ==============================================================================
# SUPABASE CLIENT
# ==============================================================================

_supabase_client = None

def get_supabase_client():
    """Get Supabase client (lazy singleton)."""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        return _supabase_client
    except Exception as e:
        print(f"Supabase client error: {e}")
        return None


# ==============================================================================
# OPPORTUNITY EXTRACTION
# ==============================================================================

OPPORTUNITY_EXTRACTION_PROMPT = """You are an expert at identifying innovation opportunities from conversations using the PWS (Problems Worth Solving) methodology.

Analyze this conversation and extract any opportunities for innovation, problems worth solving, unmet needs, or market gaps that were discussed or discovered.

CONVERSATION:
{conversation}

SOURCE CONTEXT:
- Bot/Agent: {bot_id}
- Methodology: {methodology}
- Phase: {phase}

For each opportunity found, provide (using PWS framework):
1. **name**: Clear, actionable title
2. **description**: What is the opportunity (2-3 sentences)
3. **problem**: The constraint/reverse salient being addressed
4. **value_potential**: Assessment (low, medium, high, transformative)
5. **solution_direction**: How might it be solved
6. **job_to_be_done**: JTBD framing - what user need is served
7. **opportunity_type**: problem_worth_solving, unmet_need, market_gap, technology_opportunity, process_improvement, emerging_trend, validated_insight
8. **domain**: Main domain/industry
9. **subdomain**: Specific area
10. **target_users**: Who would benefit
11. **pain_points**: Pain points it addresses
12. **evidence**: Direct quotes or observations from the conversation
13. **extraction_confidence**: 0.0-1.0 based on how well-validated it seems
14. **source_snippet**: Key excerpt from conversation that describes this opportunity
15. **tags**: Relevant tags
16. **frameworks_applied**: Which frameworks were used (JTBD, TTA, etc.)

Return JSON array (no markdown):
[
  {{
    "name": "Clear opportunity title",
    "description": "2-3 sentence description",
    "problem": "The reverse salient or constraint",
    "value_potential": "high",
    "solution_direction": "Proposed approach",
    "job_to_be_done": "Help users accomplish X",
    "opportunity_type": "problem_worth_solving",
    "domain": "Main domain",
    "subdomain": "Specific area",
    "target_users": ["User type 1", "User type 2"],
    "pain_points": ["Pain 1", "Pain 2"],
    "evidence": ["Quote or observation from conversation"],
    "extraction_confidence": 0.7,
    "source_snippet": "Key excerpt that describes this opportunity",
    "tags": ["tag1", "tag2"],
    "frameworks_applied": ["JTBD", "TTA"]
  }}
]

If no clear opportunities are found, return an empty array: []

Only extract opportunities that have some substance - not vague ideas."""


async def extract_opportunities(
    conversation: List[Dict[str, str]],
    bot_id: str = "unknown",
    methodology: str = "",
    phase: str = "",
    conversation_id: str = "",
    user_id: str = "",
    created_by: str = None,
    created_by_type: str = "ai_agent"
) -> List[Opportunity]:
    """
    Extract opportunities from a conversation using Gemini + LangExtract enrichment.

    Args:
        conversation: List of {"role": "user"|"assistant", "content": "..."}
        bot_id: Which bot/agent was used
        methodology: What methodology was applied (TTA, JTBD, etc.)
        phase: What phase of the workshop
        conversation_id: Session/thread ID
        user_id: User identifier
        created_by: Who/what identified this (defaults to bot_id)
        created_by_type: user/ai_agent/framework/system

    Returns:
        List of extracted Opportunity objects
    """
    if not GEMINI_AVAILABLE:
        return []

    # Format conversation
    conv_text = "\n".join([
        f"{'USER' if msg.get('role') == 'user' else 'ASSISTANT'}: {msg.get('content', '')}"
        for msg in conversation[-30:]  # Last 30 messages
    ])

    prompt = OPPORTUNITY_EXTRACTION_PROMPT.format(
        conversation=conv_text,
        bot_id=bot_id,
        methodology=methodology or bot_id,
        phase=phase or "general"
    )

    try:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4000
            )
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        raw_opportunities = json.loads(text)

        opportunities = []
        for raw in raw_opportunities:
            opp_id = generate_opportunity_id(raw.get("name", raw.get("title", "")), conversation_id)

            # Build opportunity with PWS fields
            opp = Opportunity(
                id=opp_id,
                name=raw.get("name", raw.get("title", "Untitled")),
                description=raw.get("description", ""),
                problem=raw.get("problem", ""),
                value_potential=raw.get("value_potential", "medium"),
                solution_direction=raw.get("solution_direction", ""),
                job_to_be_done=raw.get("job_to_be_done", ""),
                opportunity_type=raw.get("opportunity_type", "problem_worth_solving"),
                source_bot=bot_id,
                source_phase=phase,
                source_methodology=methodology or bot_id,
                source_type="conversation",
                source_id=conversation_id,
                source_snippet=raw.get("source_snippet", ""),
                conversation_id=conversation_id,
                user_id=user_id,
                created_by=created_by or bot_id,
                created_by_type=created_by_type,
                domain=raw.get("domain", ""),
                subdomain=raw.get("subdomain", ""),
                target_users=raw.get("target_users", []),
                pain_points=raw.get("pain_points", []),
                evidence=raw.get("evidence", []),
                extraction_confidence=raw.get("extraction_confidence", raw.get("confidence_score", 0.5)),
                confidence_score=raw.get("extraction_confidence", raw.get("confidence_score", 0.5)),
                frameworks_applied=raw.get("frameworks_applied", []),
                tags=raw.get("tags", []),
                extraction_method="ai_synthesis"
            )

            # Enrich with LangExtract if available
            if LANGEXTRACT_AVAILABLE:
                try:
                    signals = instant_extract(f"{opp.name} {opp.description} {opp.problem}")
                    opp.extracted_keywords = signals.get("keywords", [])[:20]
                    opp.extracted_entities = {
                        "statistics": signals.get("statistics", []),
                        "assumptions": signals.get("assumptions", []),
                        "problems": signals.get("problems", []),
                        "questions": signals.get("questions", [])
                    }
                    opp.extraction_method = "hybrid"
                except Exception:
                    pass

            opportunities.append(opp)

        return opportunities

    except Exception as e:
        print(f"Opportunity extraction error: {e}")
        return []


def generate_opportunity_id(name: str, conversation_id: str) -> str:
    """Generate unique opportunity ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    hash_input = f"{name}:{conversation_id}:{timestamp}"
    short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    return f"opp_{short_hash}_{timestamp}"


# ==============================================================================
# SUPABASE TABLE STORAGE (Primary)
# ==============================================================================

async def store_opportunity_to_table(
    opportunity: Opportunity,
    generate_embedding_flag: bool = False
) -> Optional[str]:
    """
    Store opportunity in Supabase opportunity_bank table.

    Args:
        opportunity: The Opportunity to store
        generate_embedding_flag: If True, generate and store embedding vector

    Returns the UUID of the inserted row, or None on failure.
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        row = opportunity.to_supabase_row()

        # Generate embedding if requested
        if generate_embedding_flag:
            embedding = await generate_opportunity_embedding(opportunity)
            if embedding:
                row["embedding"] = embedding
                print(f"Generated embedding ({len(embedding)} dims) for {opportunity.id}")

        result = client.table("opportunity_bank").insert(row).execute()

        if result.data and len(result.data) > 0:
            table_id = result.data[0].get("id")
            opportunity.supabase_table_id = table_id
            print(f"Supabase table: Stored opportunity {opportunity.id} -> {table_id}")
            return table_id

        return None

    except Exception as e:
        error_msg = str(e)
        # Handle table not existing
        if "relation" in error_msg and "does not exist" in error_msg:
            print("Supabase table 'opportunity_bank' not found. Run sql/opportunity_bank.sql to create it.")
            print("Falling back to JSON storage...")
            return None
        print(f"Supabase table storage error: {e}")
        return None


async def get_opportunities_from_table(
    date_start: datetime = None,
    date_end: datetime = None,
    limit: int = 100,
    created_by: str = None,
    domain: str = None,
    value_potential: str = None
) -> List[Dict]:
    """
    Query opportunities from Supabase table.

    Args:
        date_start: Filter by created_at >= date_start
        date_end: Filter by created_at <= date_end
        limit: Max results
        created_by: Filter by creator
        domain: Filter by domain
        value_potential: Filter by value potential

    Returns:
        List of opportunity dicts
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        query = client.table("opportunity_bank").select("*")

        if date_start:
            query = query.gte("created_at", date_start.isoformat())
        if date_end:
            query = query.lte("created_at", date_end.isoformat())
        if created_by:
            query = query.eq("created_by", created_by)
        if domain:
            query = query.eq("domain", domain)
        if value_potential:
            query = query.eq("value_potential", value_potential)

        query = query.order("created_at", desc=True).limit(limit)

        result = query.execute()
        return result.data if result.data else []

    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg and "does not exist" in error_msg:
            return []  # Table doesn't exist yet
        print(f"Supabase table query error: {e}")
        return []


# ==============================================================================
# SUPABASE JSON STORAGE (Legacy/Backup)
# ==============================================================================

async def store_opportunity_supabase(opportunity: Opportunity) -> bool:
    """Store opportunity as JSON in Supabase storage (legacy method)."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        filename = f"opportunities/{date_str}/{opportunity.id}.json"

        json_content = json.dumps(opportunity.to_dict(), indent=2).encode('utf-8')

        try:
            client.storage.from_(SUPABASE_BUCKET).upload(
                path=filename,
                file=json_content,
                file_options={"content-type": "application/json"}
            )
        except Exception as upload_error:
            if "Duplicate" in str(upload_error) or "already exists" in str(upload_error).lower():
                client.storage.from_(SUPABASE_BUCKET).update(
                    path=filename,
                    file=json_content,
                    file_options={"content-type": "application/json"}
                )

        print(f"Supabase JSON: Stored opportunity {opportunity.id}")
        return True

    except Exception as e:
        print(f"Supabase JSON storage error: {e}")
        return False


# ==============================================================================
# NEO4J STORAGE
# ==============================================================================

async def store_opportunity_neo4j(opportunity: Opportunity) -> bool:
    """
    Store opportunity in Neo4j with graph relationships.

    Creates:
    - Opportunity node with PWS properties
    - Domain relationship
    - Framework relationships
    - User relationship
    - Creator relationship
    """
    if not NEO4J_AVAILABLE:
        return False

    try:
        driver = get_neo4j_driver()
        if not driver:
            return False

        with driver.session() as session:
            # Create or merge Opportunity node with PWS fields
            session.run("""
                MERGE (o:Opportunity {id: $id})
                SET o.name = $name,
                    o.title = $name,
                    o.description = $description,
                    o.problem = $problem,
                    o.value_potential = $value_potential,
                    o.solution_direction = $solution_direction,
                    o.job_to_be_done = $job_to_be_done,
                    o.type = $type,
                    o.domain = $domain,
                    o.subdomain = $subdomain,
                    o.confidence = $confidence,
                    o.status = $status,
                    o.source_bot = $source_bot,
                    o.source_methodology = $methodology,
                    o.source_snippet = $source_snippet,
                    o.created_by = $created_by,
                    o.created_by_type = $created_by_type,
                    o.created_at = $created_at,
                    o.tags = $tags
            """, {
                "id": opportunity.id,
                "name": opportunity.name,
                "description": opportunity.description,
                "problem": opportunity.problem,
                "value_potential": opportunity.value_potential,
                "solution_direction": opportunity.solution_direction,
                "job_to_be_done": opportunity.job_to_be_done,
                "type": opportunity.opportunity_type,
                "domain": opportunity.domain,
                "subdomain": opportunity.subdomain,
                "confidence": opportunity.extraction_confidence,
                "status": opportunity.status,
                "source_bot": opportunity.source_bot,
                "methodology": opportunity.source_methodology,
                "source_snippet": opportunity.source_snippet,
                "created_by": opportunity.created_by,
                "created_by_type": opportunity.created_by_type,
                "created_at": opportunity.created_at,
                "tags": opportunity.tags
            })

            # Link to Domain if exists
            if opportunity.domain:
                session.run("""
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (d:Domain {name: $domain})
                    MERGE (o)-[:IN_DOMAIN]->(d)
                """, {"opp_id": opportunity.id, "domain": opportunity.domain})

            # Link to Frameworks used
            for framework in opportunity.frameworks_applied:
                session.run("""
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (f:Framework {name: $framework})
                    MERGE (o)-[:USED_FRAMEWORK]->(f)
                """, {"opp_id": opportunity.id, "framework": framework})

            # Link to User if known
            if opportunity.user_id:
                session.run("""
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (u:User {id: $user_id})
                    MERGE (u)-[:DISCOVERED]->(o)
                """, {"opp_id": opportunity.id, "user_id": opportunity.user_id})

            # Link to Creator (Person node)
            if opportunity.created_by and opportunity.created_by != "system":
                session.run("""
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (p:Person {name: $created_by})
                    MERGE (o)-[:CREATED_BY]->(p)
                """, {"opp_id": opportunity.id, "created_by": opportunity.created_by})

            # Link to Source (SYNTHESIZED_FROM relationship)
            if opportunity.source_id or opportunity.conversation_id:
                source_id = opportunity.source_id or opportunity.conversation_id
                source_type = opportunity.source_type or "conversation"
                session.run("""
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (s:Source {id: $source_id})
                    SET s.type = $source_type,
                        s.name = $source_name,
                        s.bot = $source_bot
                    MERGE (o)-[:SYNTHESIZED_FROM]->(s)
                """, {
                    "opp_id": opportunity.id,
                    "source_id": source_id,
                    "source_type": source_type,
                    "source_name": opportunity.source_name or source_id,
                    "source_bot": opportunity.source_bot
                })

            opportunity.neo4j_synced = True
            opportunity.neo4j_node_id = opportunity.id
            print(f"Neo4j: Stored opportunity {opportunity.id}")
            return True

    except Exception as e:
        print(f"Neo4j storage error: {e}")
        return False


# ==============================================================================
# FILESEARCH DOCUMENT EXPORT
# ==============================================================================

async def export_for_filesearch(opportunity: Opportunity, output_dir: str = "opportunities_docs") -> str:
    """
    Export opportunity as document for FileSearch indexing.

    Returns path to created document.
    """
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{opportunity.id}.md"
    filepath = os.path.join(output_dir, filename)

    doc_content = opportunity.to_filesearch_document()

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(doc_content)

    print(f"FileSearch: Exported {filepath}")
    return filepath


# ==============================================================================
# MAIN STORAGE FUNCTION
# ==============================================================================

async def store_opportunity(
    opportunity: Opportunity,
    generate_embedding: bool = True
) -> Dict[str, Any]:
    """
    Store opportunity in all configured storage backends.

    Priority:
    1. Supabase Table (primary structured storage)
    2. Neo4j (graph relationships)
    3. Supabase JSON (legacy backup)
    4. FileSearch export

    Args:
        opportunity: The Opportunity to store
        generate_embedding: If True, generate embedding for semantic search (default: True)

    Returns dict of {backend: success/id} status.
    """
    results = {
        "supabase_table": None,
        "neo4j": False,
        "supabase_json": False,
        "filesearch": False,
        "embedding": False
    }

    # Primary: Supabase table (with optional embedding)
    table_id = await store_opportunity_to_table(opportunity, generate_embedding_flag=generate_embedding)
    results["supabase_table"] = table_id
    results["embedding"] = generate_embedding and table_id is not None

    # If table storage failed, use JSON as fallback
    if not table_id:
        supabase_json_result = await store_opportunity_supabase(opportunity)
        results["supabase_json"] = supabase_json_result
    else:
        # Still create JSON backup
        try:
            await store_opportunity_supabase(opportunity)
            results["supabase_json"] = True
        except Exception:
            pass

    # Neo4j graph storage
    neo4j_result = await store_opportunity_neo4j(opportunity)
    results["neo4j"] = neo4j_result

    # FileSearch export (local file, can be batch uploaded later)
    try:
        await export_for_filesearch(opportunity)
        results["filesearch"] = True
    except Exception as e:
        print(f"FileSearch export error: {e}")

    return results


async def extract_and_store_opportunities(
    conversation: List[Dict[str, str]],
    bot_id: str = "unknown",
    methodology: str = "",
    phase: str = "",
    conversation_id: str = "",
    user_id: str = "",
    created_by: str = None,
    created_by_type: str = "ai_agent"
) -> Tuple[List[Opportunity], Dict[str, Any]]:
    """
    Extract opportunities from conversation and store them.

    Returns:
        (list of opportunities, storage results summary)
    """
    # Extract
    opportunities = await extract_opportunities(
        conversation=conversation,
        bot_id=bot_id,
        methodology=methodology,
        phase=phase,
        conversation_id=conversation_id,
        user_id=user_id,
        created_by=created_by,
        created_by_type=created_by_type
    )

    if not opportunities:
        return [], {"extracted": 0, "stored": 0}

    # Store each opportunity
    storage_results = []
    for opp in opportunities:
        result = await store_opportunity(opp)
        storage_results.append(result)

    # Summarize
    summary = {
        "extracted": len(opportunities),
        "stored": sum(1 for r in storage_results if r.get("supabase_table") or r.get("supabase_json")),
        "supabase_table_success": sum(1 for r in storage_results if r.get("supabase_table")),
        "neo4j_success": sum(1 for r in storage_results if r.get("neo4j")),
        "supabase_json_success": sum(1 for r in storage_results if r.get("supabase_json")),
        "opportunities": [opp.to_dict() for opp in opportunities]
    }

    return opportunities, summary


# ==============================================================================
# REMOVE OPPORTUNITY (P0 BUG FIX)
# ==============================================================================

async def remove_opportunity(opportunity_id: str, session_id: str = None) -> bool:
    """
    Remove opportunity from all storage backends.

    Args:
        opportunity_id: The opportunity ID to remove
        session_id: Optional session ID (for logging/audit)

    Returns:
        True if removed from any backend, False otherwise
    """
    results = {
        "supabase_table": False,
        "neo4j": False,
        "supabase_json": False,
        "filesearch": False
    }

    # Remove from Supabase table
    client = get_supabase_client()
    if client:
        try:
            # Try to find by id field first (our custom id)
            result = client.table("opportunity_bank").delete().eq("id", opportunity_id).execute()
            if not result.data:
                # Try by our custom id stored somewhere
                # The id might be in a different field, so also try pattern match
                pass
            results["supabase_table"] = True
        except Exception as e:
            if "does not exist" not in str(e):
                print(f"Supabase table delete error: {e}")

    # Remove from Supabase JSON storage
    if client:
        try:
            # Find the file - need to search through date folders
            date_folders = client.storage.from_(SUPABASE_BUCKET).list("opportunities")
            for folder in date_folders:
                folder_name = folder.get('name')
                if folder_name and not folder_name.endswith('.json'):
                    try:
                        files = client.storage.from_(SUPABASE_BUCKET).list(f"opportunities/{folder_name}")
                        for f in files:
                            if f.get('name') == f"{opportunity_id}.json":
                                client.storage.from_(SUPABASE_BUCKET).remove([
                                    f"opportunities/{folder_name}/{opportunity_id}.json"
                                ])
                                results["supabase_json"] = True
                                break
                    except Exception:
                        pass
                if results["supabase_json"]:
                    break
        except Exception as e:
            print(f"Supabase JSON delete error: {e}")

    # Remove from Neo4j
    if NEO4J_AVAILABLE:
        try:
            driver = get_neo4j_driver()
            if driver:
                with driver.session() as session:
                    session.run("""
                        MATCH (o:Opportunity {id: $id})
                        DETACH DELETE o
                    """, {"id": opportunity_id})
                    results["neo4j"] = True
        except Exception as e:
            print(f"Neo4j delete error: {e}")

    # Remove FileSearch document
    try:
        filepath = f"opportunities_docs/{opportunity_id}.md"
        if os.path.exists(filepath):
            os.remove(filepath)
            results["filesearch"] = True
    except Exception as e:
        print(f"FileSearch delete error: {e}")

    print(f"Removed opportunity {opportunity_id} (session: {session_id}): {results}")
    # Return True if removed from any backend
    return any(results.values())


# ==============================================================================
# QUERY FUNCTIONS
# ==============================================================================

async def get_opportunities_by_domain(domain: str) -> List[Dict]:
    """Get all opportunities in a domain from Neo4j."""
    if not NEO4J_AVAILABLE:
        return []

    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (o:Opportunity)-[:IN_DOMAIN]->(d:Domain {name: $domain})
                RETURN o
                ORDER BY o.created_at DESC
                LIMIT 50
            """, {"domain": domain})

            return [dict(record["o"]) for record in result]

    except Exception as e:
        print(f"Query error: {e}")
        return []


async def get_opportunities_by_user(user_id: str) -> List[Dict]:
    """Get all opportunities discovered by a user."""
    if not NEO4J_AVAILABLE:
        return []

    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:DISCOVERED]->(o:Opportunity)
                RETURN o
                ORDER BY o.created_at DESC
                LIMIT 100
            """, {"user_id": user_id})

            return [dict(record["o"]) for record in result]

    except Exception as e:
        print(f"Query error: {e}")
        return []


async def get_opportunities_by_creator(created_by: str) -> List[Dict]:
    """Get all opportunities by a specific creator."""
    # Try Supabase table first
    try:
        opportunities = await get_opportunities_from_table(created_by=created_by, limit=100)
        if opportunities:
            return opportunities
    except Exception:
        pass

    # Fallback to Neo4j
    if not NEO4J_AVAILABLE:
        return []

    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (o:Opportunity)
                WHERE o.created_by = $created_by
                RETURN o
                ORDER BY o.created_at DESC
                LIMIT 100
            """, {"created_by": created_by})

            return [dict(record["o"]) for record in result]

    except Exception as e:
        print(f"Query error: {e}")
        return []


async def get_related_opportunities(opportunity_id: str) -> List[Dict]:
    """Find opportunities related by domain or framework."""
    if not NEO4J_AVAILABLE:
        return []

    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (o:Opportunity {id: $id})-[:IN_DOMAIN|USED_FRAMEWORK]-(shared)-[:IN_DOMAIN|USED_FRAMEWORK]-(related:Opportunity)
                WHERE related.id <> $id
                RETURN DISTINCT related, count(shared) as overlap
                ORDER BY overlap DESC
                LIMIT 10
            """, {"id": opportunity_id})

            return [dict(record["related"]) for record in result]

    except Exception as e:
        print(f"Query error: {e}")
        return []


async def search_opportunities(query: str, limit: int = 10) -> List[Dict]:
    """
    Search opportunities using full-text search.

    Tries Supabase table first, falls back to Neo4j.
    """
    client = get_supabase_client()
    if client:
        try:
            result = client.rpc("search_opportunities", {
                "query_text": query,
                "limit_count": limit
            }).execute()
            if result.data:
                return result.data
        except Exception as e:
            if "does not exist" not in str(e):
                print(f"Search error: {e}")

    # Fallback: basic filter on Neo4j
    if NEO4J_AVAILABLE:
        try:
            driver = get_neo4j_driver()
            with driver.session() as session:
                result = session.run("""
                    MATCH (o:Opportunity)
                    WHERE toLower(o.name) CONTAINS toLower($query)
                       OR toLower(o.description) CONTAINS toLower($query)
                       OR toLower(o.problem) CONTAINS toLower($query)
                    RETURN o
                    ORDER BY o.created_at DESC
                    LIMIT $limit
                """, {"query": query, "limit": limit})

                return [dict(record["o"]) for record in result]
        except Exception:
            pass

    return []


async def get_opportunity_stats() -> Dict[str, Any]:
    """Get statistics about the opportunity bank."""
    stats = {
        "total_opportunities": 0,
        "by_type": {},
        "by_value_potential": {},
        "top_domains": {},
        "high_confidence_count": 0,
        "high_confidence_rate": 0,
        "sources": {
            "supabase_table": 0,
            "neo4j": 0
        }
    }

    # Try Supabase table first
    client = get_supabase_client()
    if client:
        try:
            # Total count
            result = client.table("opportunity_bank").select("id", count="exact").execute()
            if result.count is not None:
                stats["total_opportunities"] = result.count
                stats["sources"]["supabase_table"] = result.count

            # By type
            result = client.table("opportunity_bank").select("opportunity_type").execute()
            if result.data:
                for row in result.data:
                    t = row.get("opportunity_type", "unknown")
                    stats["by_type"][t] = stats["by_type"].get(t, 0) + 1

            # By value potential
            result = client.table("opportunity_bank").select("value_potential").execute()
            if result.data:
                for row in result.data:
                    v = row.get("value_potential", "unknown")
                    stats["by_value_potential"][v] = stats["by_value_potential"].get(v, 0) + 1

            # High confidence
            result = client.table("opportunity_bank").select("id").gte("extraction_confidence", 0.7).execute()
            if result.data:
                stats["high_confidence_count"] = len(result.data)
                if stats["total_opportunities"] > 0:
                    stats["high_confidence_rate"] = stats["high_confidence_count"] / stats["total_opportunities"]

            return stats

        except Exception as e:
            if "does not exist" not in str(e):
                print(f"Stats query error: {e}")

    # Fallback to Neo4j
    if not NEO4J_AVAILABLE:
        return stats

    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Total count
            total = session.run("MATCH (o:Opportunity) RETURN count(o) as count").single()["count"]
            stats["total_opportunities"] = total
            stats["sources"]["neo4j"] = total

            # By type
            by_type = session.run("""
                MATCH (o:Opportunity)
                RETURN o.type as type, count(o) as count
                ORDER BY count DESC
            """)
            stats["by_type"] = {r["type"]: r["count"] for r in by_type}

            # By domain
            by_domain = session.run("""
                MATCH (o:Opportunity)-[:IN_DOMAIN]->(d:Domain)
                RETURN d.name as domain, count(o) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            stats["top_domains"] = {r["domain"]: r["count"] for r in by_domain}

            # High confidence
            high_conf = session.run("""
                MATCH (o:Opportunity)
                WHERE o.confidence >= 0.7
                RETURN count(o) as count
            """).single()["count"]
            stats["high_confidence_count"] = high_conf
            stats["high_confidence_rate"] = high_conf / total if total > 0 else 0

    except Exception as e:
        print(f"Stats query error: {e}")

    return stats


def get_embedding_cache_stats() -> Dict[str, Any]:
    """
    Get embedding cache statistics for monitoring.

    Returns dict with:
    - size: Current cache size
    - max_size: Maximum cache capacity
    - hits: Number of cache hits
    - misses: Number of cache misses
    - hit_rate: Ratio of hits to total requests
    - memory_estimate: Estimated memory usage in MB

    This follows the lazy graph pattern - bounded memory for
    safe usage on 512MB instances (~1MB max for embeddings).
    """
    stats = _embedding_cache.stats()

    # Estimate memory: 1536 floats * 8 bytes * num_embeddings
    embedding_size_bytes = 1536 * 8  # ~12KB per embedding
    stats["memory_estimate_mb"] = round(stats["size"] * embedding_size_bytes / (1024 * 1024), 3)

    return stats
