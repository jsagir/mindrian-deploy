"""
Bank of Opportunities - Automated Opportunity Extraction and Storage
====================================================================

Automatically extracts innovation opportunities from ANY conversation with Mindrian agents
and stores them in a persistent, searchable knowledge base.

Storage Architecture:
- Neo4j: Graph relationships (opportunity → domain, framework, user)
- Supabase: Persistent JSON storage with full context
- FileSearch-ready: Document format for semantic retrieval

Opportunity Types:
- Problems Worth Solving (PWS)
- Unmet Needs
- Market Gaps
- Technology Opportunities
- Process Improvements
- Emerging Trends
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
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

# Supabase for persistence
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")


class OpportunityType(str, Enum):
    PWS = "problem_worth_solving"
    UNMET_NEED = "unmet_need"
    MARKET_GAP = "market_gap"
    TECH_OPPORTUNITY = "technology_opportunity"
    PROCESS_IMPROVEMENT = "process_improvement"
    EMERGING_TREND = "emerging_trend"
    VALIDATED_INSIGHT = "validated_insight"


class OpportunityStatus(str, Enum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    PRIORITIZED = "prioritized"
    ACTIONED = "actioned"
    ARCHIVED = "archived"


@dataclass
class Opportunity:
    """Represents an innovation opportunity extracted from conversation."""
    id: str
    title: str
    description: str
    opportunity_type: str
    status: str = "discovered"

    # Source context
    source_bot: str = ""
    source_phase: str = ""
    source_methodology: str = ""
    conversation_id: str = ""
    user_id: str = ""

    # Problem details
    domain: str = ""
    subdomain: str = ""
    target_users: List[str] = None
    pain_points: List[str] = None
    evidence: List[str] = None

    # Validation signals
    confidence_score: float = 0.0
    validation_status: str = "unvalidated"
    frameworks_applied: List[str] = None

    # Metadata
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = None
    related_opportunities: List[str] = None

    def __post_init__(self):
        if self.target_users is None:
            self.target_users = []
        if self.pain_points is None:
            self.pain_points = []
        if self.evidence is None:
            self.evidence = []
        if self.frameworks_applied is None:
            self.frameworks_applied = []
        if self.tags is None:
            self.tags = []
        if self.related_opportunities is None:
            self.related_opportunities = []
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_filesearch_document(self) -> str:
        """Format as document for FileSearch indexing."""
        doc = f"""# Opportunity: {self.title}

## Summary
{self.description}

## Details
- **Type**: {self.opportunity_type}
- **Domain**: {self.domain}
- **Status**: {self.status}
- **Confidence**: {self.confidence_score:.0%}

## Target Users
{chr(10).join('- ' + u for u in self.target_users) if self.target_users else '- Not specified'}

## Pain Points
{chr(10).join('- ' + p for p in self.pain_points) if self.pain_points else '- Not specified'}

## Evidence
{chr(10).join('- ' + e for e in self.evidence) if self.evidence else '- Not yet validated'}

## Frameworks Applied
{', '.join(self.frameworks_applied) if self.frameworks_applied else 'None yet'}

## Source
- Bot: {self.source_bot}
- Methodology: {self.source_methodology}
- Phase: {self.source_phase}

## Tags
{', '.join(self.tags) if self.tags else 'None'}

---
ID: {self.id}
Created: {self.created_at}
"""
        return doc


# ==============================================================================
# OPPORTUNITY EXTRACTION
# ==============================================================================

OPPORTUNITY_EXTRACTION_PROMPT = """You are an expert at identifying innovation opportunities from conversations.

Analyze this conversation and extract any opportunities for innovation, problems worth solving, unmet needs, or market gaps that were discussed or discovered.

CONVERSATION:
{conversation}

SOURCE CONTEXT:
- Bot/Agent: {bot_id}
- Methodology: {methodology}
- Phase: {phase}

For each opportunity found, provide:
1. A clear, actionable title
2. Description of the opportunity
3. Type (problem_worth_solving, unmet_need, market_gap, technology_opportunity, process_improvement, emerging_trend, validated_insight)
4. Domain and subdomain
5. Target users who would benefit
6. Pain points it addresses
7. Evidence from the conversation (direct quotes or observations)
8. Confidence score (0.0-1.0) based on how well-validated it seems
9. Relevant tags

Return JSON array (no markdown):
[
  {{
    "title": "Clear opportunity title",
    "description": "2-3 sentence description",
    "opportunity_type": "problem_worth_solving",
    "domain": "Main domain",
    "subdomain": "Specific area",
    "target_users": ["User type 1", "User type 2"],
    "pain_points": ["Pain 1", "Pain 2"],
    "evidence": ["Quote or observation from conversation"],
    "confidence_score": 0.7,
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
    user_id: str = ""
) -> List[Opportunity]:
    """
    Extract opportunities from a conversation using Gemini.

    Args:
        conversation: List of {"role": "user"|"assistant", "content": "..."}
        bot_id: Which bot/agent was used
        methodology: What methodology was applied (TTA, JTBD, etc.)
        phase: What phase of the workshop
        conversation_id: Session/thread ID
        user_id: User identifier

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
            opp_id = generate_opportunity_id(raw.get("title", ""), conversation_id)

            opp = Opportunity(
                id=opp_id,
                title=raw.get("title", "Untitled"),
                description=raw.get("description", ""),
                opportunity_type=raw.get("opportunity_type", "problem_worth_solving"),
                source_bot=bot_id,
                source_phase=phase,
                source_methodology=methodology or bot_id,
                conversation_id=conversation_id,
                user_id=user_id,
                domain=raw.get("domain", ""),
                subdomain=raw.get("subdomain", ""),
                target_users=raw.get("target_users", []),
                pain_points=raw.get("pain_points", []),
                evidence=raw.get("evidence", []),
                confidence_score=raw.get("confidence_score", 0.5),
                frameworks_applied=raw.get("frameworks_applied", []),
                tags=raw.get("tags", [])
            )
            opportunities.append(opp)

        return opportunities

    except Exception as e:
        print(f"Opportunity extraction error: {e}")
        return []


def generate_opportunity_id(title: str, conversation_id: str) -> str:
    """Generate unique opportunity ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    hash_input = f"{title}:{conversation_id}:{timestamp}"
    short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    return f"opp_{short_hash}_{timestamp}"


# ==============================================================================
# NEO4J STORAGE
# ==============================================================================

async def store_opportunity_neo4j(opportunity: Opportunity) -> bool:
    """
    Store opportunity in Neo4j with graph relationships.

    Creates:
    - Opportunity node
    - Domain relationship
    - Framework relationships
    - User relationship
    """
    if not NEO4J_AVAILABLE:
        return False

    try:
        driver = get_neo4j_driver()
        if not driver:
            return False

        with driver.session() as session:
            # Create or merge Opportunity node
            session.run("""
                MERGE (o:Opportunity {id: $id})
                SET o.title = $title,
                    o.description = $description,
                    o.type = $type,
                    o.domain = $domain,
                    o.subdomain = $subdomain,
                    o.confidence = $confidence,
                    o.status = $status,
                    o.source_bot = $source_bot,
                    o.source_methodology = $methodology,
                    o.created_at = $created_at,
                    o.tags = $tags
            """, {
                "id": opportunity.id,
                "title": opportunity.title,
                "description": opportunity.description,
                "type": opportunity.opportunity_type,
                "domain": opportunity.domain,
                "subdomain": opportunity.subdomain,
                "confidence": opportunity.confidence_score,
                "status": opportunity.status,
                "source_bot": opportunity.source_bot,
                "methodology": opportunity.source_methodology,
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

            print(f"Neo4j: Stored opportunity {opportunity.id}")
            return True

    except Exception as e:
        print(f"Neo4j storage error: {e}")
        return False


# ==============================================================================
# SUPABASE STORAGE
# ==============================================================================

def get_supabase_client():
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None

    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"Supabase client error: {e}")
        return None


async def store_opportunity_supabase(opportunity: Opportunity) -> bool:
    """Store opportunity in Supabase storage."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        # Store in opportunities folder
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

        print(f"Supabase: Stored opportunity {opportunity.id}")
        return True

    except Exception as e:
        print(f"Supabase storage error: {e}")
        return False


# ==============================================================================
# FILESEARCH DOCUMENT EXPORT
# ==============================================================================

async def export_for_filesearch(opportunity: Opportunity, output_dir: str = "opportunities_docs") -> str:
    """
    Export opportunity as document for FileSearch indexing.

    Returns path to created document.
    """
    import os

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

async def store_opportunity(opportunity: Opportunity) -> Dict[str, bool]:
    """
    Store opportunity in all configured storage backends.

    Returns dict of {backend: success} status.
    """
    results = {
        "neo4j": False,
        "supabase": False,
        "filesearch": False
    }

    # Store in parallel
    tasks = [
        store_opportunity_neo4j(opportunity),
        store_opportunity_supabase(opportunity),
    ]

    neo4j_result, supabase_result = await asyncio.gather(*tasks, return_exceptions=True)

    results["neo4j"] = neo4j_result is True
    results["supabase"] = supabase_result is True

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
    user_id: str = ""
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
        user_id=user_id
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
        "stored": sum(1 for r in storage_results if any(r.values())),
        "neo4j_success": sum(1 for r in storage_results if r.get("neo4j")),
        "supabase_success": sum(1 for r in storage_results if r.get("supabase")),
        "opportunities": [opp.to_dict() for opp in opportunities]
    }

    return opportunities, summary


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


async def get_opportunity_stats() -> Dict[str, Any]:
    """Get statistics about the opportunity bank."""
    if not NEO4J_AVAILABLE:
        return {"error": "Neo4j not available"}

    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Total count
            total = session.run("MATCH (o:Opportunity) RETURN count(o) as count").single()["count"]

            # By type
            by_type = session.run("""
                MATCH (o:Opportunity)
                RETURN o.type as type, count(o) as count
                ORDER BY count DESC
            """)
            type_counts = {r["type"]: r["count"] for r in by_type}

            # By domain
            by_domain = session.run("""
                MATCH (o:Opportunity)-[:IN_DOMAIN]->(d:Domain)
                RETURN d.name as domain, count(o) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            domain_counts = {r["domain"]: r["count"] for r in by_domain}

            # High confidence
            high_conf = session.run("""
                MATCH (o:Opportunity)
                WHERE o.confidence >= 0.7
                RETURN count(o) as count
            """).single()["count"]

            return {
                "total_opportunities": total,
                "by_type": type_counts,
                "top_domains": domain_counts,
                "high_confidence_count": high_conf,
                "high_confidence_rate": high_conf / total if total > 0 else 0
            }

    except Exception as e:
        print(f"Stats query error: {e}")
        return {"error": str(e)}
