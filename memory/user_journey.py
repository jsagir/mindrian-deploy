"""
User Journey Store - Conductor-Style Persistent Memory
======================================================

Manages user PWS journeys across sessions using:
- Neo4j: Journey graph with frameworks, insights, relationships
- Supabase: Artifacts (specs, extractions, evidence)
- PostgreSQL: LangGraph checkpoints for state persistence

A "Journey" is like a Conductor "track" - it represents a user's
problem-solving process through the PWS methodology.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# =============================================================================
# Data Models
# =============================================================================

class JourneyPhase(str, Enum):
    """PWS Journey phases - maps to Conductor's spec → plan → implement."""
    DISCOVERY = "discovery"           # Initial problem exploration
    DOMAIN = "domain"                 # Domain discovery
    PROBLEM_DEFINITION = "problem"    # Spec - clear problem statement
    TTA = "tta"                       # Trending to Absurd
    JTBD = "jtbd"                     # Jobs to Be Done
    VALIDATION = "validation"         # Red Team / Validation
    SYNTHESIS = "synthesis"           # Final synthesis
    COMPLETE = "complete"             # Journey complete


class InsightType(str, Enum):
    """Types of insights extracted during journey."""
    ASSUMPTION = "assumption"
    FACT = "fact"
    QUESTION = "question"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    EVIDENCE = "evidence"


@dataclass
class Insight:
    """An insight extracted during the journey."""
    id: str
    type: InsightType
    content: str
    confidence: float = 0.5
    source_phase: str = ""
    tested: bool = False
    evidence: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, InsightType) else self.type,
            "content": self.content,
            "confidence": self.confidence,
            "source_phase": self.source_phase,
            "tested": self.tested,
            "evidence": self.evidence,
            "created_at": self.created_at,
        }


@dataclass
class PhaseCheckpoint:
    """A checkpoint within a phase - like Conductor's plan.md tasks."""
    phase: str
    step: str
    status: str = "pending"  # pending, in_progress, completed, skipped
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_summary: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class UserJourney:
    """
    A user's PWS journey - like a Conductor "track".

    Contains:
    - Problem spec (the "what")
    - Phase checkpoints (the "plan")
    - Extracted insights (learnings)
    - Framework recommendations (from Neo4j)
    """
    id: str
    user_id: str
    problem_spec: str
    problem_title: str = ""
    current_phase: JourneyPhase = JourneyPhase.DISCOVERY
    completed_phases: List[str] = field(default_factory=list)
    checkpoints: List[PhaseCheckpoint] = field(default_factory=list)
    insights: List[Insight] = field(default_factory=list)
    frameworks_used: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "problem_spec": self.problem_spec,
            "problem_title": self.problem_title,
            "current_phase": self.current_phase.value if isinstance(self.current_phase, JourneyPhase) else self.current_phase,
            "completed_phases": self.completed_phases,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "insights": [i.to_dict() for i in self.insights],
            "frameworks_used": self.frameworks_used,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "metadata": self.metadata,
        }

    @property
    def problem(self) -> str:
        """Alias for problem_spec for convenience."""
        return self.problem_spec

    @classmethod
    def from_dict(cls, data: Dict) -> "UserJourney":
        """Create journey from dictionary."""
        data = data.copy()

        # Convert phase enum
        if "current_phase" in data:
            try:
                data["current_phase"] = JourneyPhase(data["current_phase"])
            except ValueError:
                data["current_phase"] = JourneyPhase.DISCOVERY

        # Convert checkpoints
        if "checkpoints" in data:
            data["checkpoints"] = [
                PhaseCheckpoint(**cp) if isinstance(cp, dict) else cp
                for cp in data["checkpoints"]
            ]

        # Convert insights
        if "insights" in data:
            insights = []
            for i in data["insights"]:
                if isinstance(i, dict):
                    if "type" in i:
                        try:
                            i["type"] = InsightType(i["type"])
                        except ValueError:
                            i["type"] = InsightType.FACT
                    insights.append(Insight(**i))
                else:
                    insights.append(i)
            data["insights"] = insights

        return cls(**data)


# =============================================================================
# Neo4j Integration
# =============================================================================

def get_neo4j_driver():
    """Get Neo4j driver from environment."""
    try:
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")

        if not uri or not password:
            logger.warning("Neo4j credentials not found")
            return None

        return GraphDatabase.driver(uri, auth=(user, password))
    except ImportError:
        logger.warning("Neo4j driver not installed")
        return None
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        return None


async def create_journey_in_neo4j(journey: UserJourney) -> bool:
    """Create journey node and relationships in Neo4j."""
    driver = get_neo4j_driver()
    if not driver:
        return False

    try:
        with driver.session() as session:
            # Create journey node
            session.run("""
                MERGE (j:Journey {id: $id})
                SET j.user_id = $user_id,
                    j.problem_spec = $problem_spec,
                    j.problem_title = $problem_title,
                    j.current_phase = $current_phase,
                    j.created_at = datetime($created_at),
                    j.last_active = datetime()
            """, {
                "id": journey.id,
                "user_id": journey.user_id,
                "problem_spec": journey.problem_spec,
                "problem_title": journey.problem_title,
                "current_phase": journey.current_phase.value,
                "created_at": journey.created_at,
            })

            # Link to user
            session.run("""
                MERGE (u:User {id: $user_id})
                WITH u
                MATCH (j:Journey {id: $journey_id})
                MERGE (u)-[:HAS_JOURNEY]->(j)
            """, {
                "user_id": journey.user_id,
                "journey_id": journey.id,
            })

        return True
    except Exception as e:
        logger.error(f"Neo4j journey creation failed: {e}")
        return False
    finally:
        driver.close()


async def update_journey_phase_in_neo4j(journey_id: str, phase: str, insights: List[Insight] = None) -> bool:
    """Update journey phase and add insights in Neo4j."""
    driver = get_neo4j_driver()
    if not driver:
        return False

    try:
        with driver.session() as session:
            # Update phase
            session.run("""
                MATCH (j:Journey {id: $journey_id})
                SET j.current_phase = $phase,
                    j.last_active = datetime()
                WITH j
                MERGE (p:PhaseCompletion {
                    journey_id: $journey_id,
                    phase: $phase
                })
                SET p.completed_at = datetime()
                MERGE (j)-[:COMPLETED_PHASE]->(p)
            """, {
                "journey_id": journey_id,
                "phase": phase,
            })

            # Add insights
            if insights:
                for insight in insights:
                    session.run("""
                        MATCH (j:Journey {id: $journey_id})
                        MERGE (i:Insight {id: $insight_id})
                        SET i.type = $type,
                            i.content = $content,
                            i.confidence = $confidence,
                            i.source_phase = $source_phase,
                            i.tested = $tested,
                            i.created_at = datetime()
                        MERGE (j)-[:HAS_INSIGHT]->(i)
                    """, {
                        "journey_id": journey_id,
                        "insight_id": insight.id,
                        "type": insight.type.value if isinstance(insight.type, InsightType) else insight.type,
                        "content": insight.content,
                        "confidence": insight.confidence,
                        "source_phase": insight.source_phase,
                        "tested": insight.tested,
                    })

        return True
    except Exception as e:
        logger.error(f"Neo4j phase update failed: {e}")
        return False
    finally:
        driver.close()


async def get_journey_from_neo4j(journey_id: str) -> Optional[Dict]:
    """Retrieve journey with all relationships from Neo4j."""
    driver = get_neo4j_driver()
    if not driver:
        return None

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (j:Journey {id: $journey_id})
                OPTIONAL MATCH (j)-[:HAS_INSIGHT]->(i:Insight)
                OPTIONAL MATCH (j)-[:COMPLETED_PHASE]->(p:PhaseCompletion)
                OPTIONAL MATCH (j)-[:USED_FRAMEWORK]->(f:Framework)
                RETURN j,
                       collect(DISTINCT i) as insights,
                       collect(DISTINCT p.phase) as completed_phases,
                       collect(DISTINCT f.name) as frameworks
            """, {"journey_id": journey_id})

            record = result.single()
            if not record:
                return None

            journey_node = record["j"]
            return {
                "id": journey_node["id"],
                "user_id": journey_node["user_id"],
                "problem_spec": journey_node["problem_spec"],
                "problem_title": journey_node.get("problem_title", ""),
                "current_phase": journey_node["current_phase"],
                "completed_phases": record["completed_phases"],
                "frameworks_used": record["frameworks"],
                "insights": [
                    {
                        "id": i["id"],
                        "type": i["type"],
                        "content": i["content"],
                        "confidence": i["confidence"],
                        "source_phase": i["source_phase"],
                        "tested": i["tested"],
                    }
                    for i in record["insights"] if i
                ],
            }
    except Exception as e:
        logger.error(f"Neo4j journey retrieval failed: {e}")
        return None
    finally:
        driver.close()


async def get_related_frameworks_for_journey(problem: str, limit: int = 5) -> List[Dict]:
    """Get relevant PWS frameworks for a problem from Neo4j."""
    driver = get_neo4j_driver()
    if not driver:
        # Fallback to default frameworks
        return [
            {"name": "TTA", "type": "Framework", "hint": "Trend analysis"},
            {"name": "JTBD", "type": "Framework", "hint": "Customer needs"},
            {"name": "Red Team", "type": "Framework", "hint": "Validation"},
        ]

    try:
        # Extract keywords from problem
        keywords = problem.lower().split()[:10]

        with driver.session() as session:
            result = session.run("""
                WITH $keywords AS keywords
                UNWIND keywords AS keyword
                MATCH (f:Framework)
                WHERE toLower(f.name) CONTAINS keyword
                   OR toLower(f.description) CONTAINS keyword
                WITH f, count(keyword) as relevance
                ORDER BY relevance DESC
                RETURN f.name as name, f.category as type,
                       f.description as hint
                LIMIT $limit
            """, {"keywords": keywords, "limit": limit})

            frameworks = []
            for record in result:
                frameworks.append({
                    "name": record["name"],
                    "type": record["type"] or "Framework",
                    "hint": record["hint"] or "",
                })
            return frameworks

    except Exception as e:
        logger.error(f"Neo4j framework query failed: {e}")
        return []
    finally:
        driver.close()


# =============================================================================
# Supabase Integration
# =============================================================================

def get_supabase_client():
    """Get Supabase client from environment."""
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

        if not url or not key:
            logger.warning("Supabase credentials not found")
            return None

        return create_client(url, key)
    except ImportError:
        logger.warning("Supabase not installed")
        return None
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        return None


async def save_journey_to_supabase(journey: UserJourney) -> bool:
    """Save journey artifacts to Supabase."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        # Save as JSON to storage bucket
        journey_data = json.dumps(journey.to_dict(), indent=2)
        file_path = f"journeys/{journey.user_id}/{journey.id}.json"

        client.storage.from_("mindrian").upload(
            file_path,
            journey_data.encode(),
            {"content-type": "application/json", "upsert": "true"}
        )

        logger.info(f"Journey saved to Supabase: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Supabase save failed: {e}")
        return False


async def load_journey_from_supabase(user_id: str, journey_id: str) -> Optional[UserJourney]:
    """Load journey from Supabase storage."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        file_path = f"journeys/{user_id}/{journey_id}.json"
        response = client.storage.from_("mindrian").download(file_path)

        if response:
            data = json.loads(response.decode())
            return UserJourney.from_dict(data)
        return None
    except Exception as e:
        logger.debug(f"Journey not found in Supabase: {e}")
        return None


async def list_user_journeys_from_supabase(user_id: str) -> List[Dict]:
    """List all journeys for a user from Supabase."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        folder_path = f"journeys/{user_id}"
        response = client.storage.from_("mindrian").list(folder_path)

        journeys = []
        for file_info in response:
            if file_info["name"].endswith(".json"):
                journey_id = file_info["name"].replace(".json", "")
                journey = await load_journey_from_supabase(user_id, journey_id)
                if journey:
                    journeys.append({
                        "id": journey.id,
                        "problem_title": journey.problem_title or journey.problem_spec[:50],
                        "current_phase": journey.current_phase.value,
                        "last_active": journey.last_active,
                    })
        return journeys
    except Exception as e:
        logger.error(f"Supabase list failed: {e}")
        return []


# =============================================================================
# PostgreSQL Checkpointer Integration
# =============================================================================

async def get_postgres_checkpointer():
    """Get PostgreSQL checkpointer for LangGraph state persistence."""
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        database_url = os.getenv("DATABASE_URL") or os.getenv("CHAINLIT_DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL not found for checkpointer")
            return None

        checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
        await checkpointer.setup()

        logger.info("PostgreSQL checkpointer initialized")
        return checkpointer

    except ImportError:
        logger.warning("langgraph-checkpoint-postgres not installed")
        return None
    except Exception as e:
        logger.error(f"PostgreSQL checkpointer failed: {e}")
        return None


# =============================================================================
# Journey Store - Main Interface
# =============================================================================

class JourneyStore:
    """
    Main interface for managing user PWS journeys.

    Combines Neo4j (graph), Supabase (artifacts), and Postgres (checkpoints)
    into a unified Conductor-style memory system.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._current_journey: Optional[UserJourney] = None
        self._checkpointer = None

    async def get_or_create_journey(
        self,
        problem: str,
        journey_id: str = None,
        title: str = None
    ) -> UserJourney:
        """
        Get existing journey or create a new one.

        Like Conductor's /conductor:newTrack command.
        """
        import uuid

        # Try to load existing journey
        if journey_id:
            existing = await self.get_journey(journey_id)
            if existing:
                self._current_journey = existing
                return existing

        # Create new journey
        new_id = journey_id or f"journey_{uuid.uuid4().hex[:12]}"
        journey = UserJourney(
            id=new_id,
            user_id=self.user_id,
            problem_spec=problem,
            problem_title=title or problem[:50],
            current_phase=JourneyPhase.DISCOVERY,
        )

        # Initialize with default checkpoints (like Conductor's plan.md)
        journey.checkpoints = [
            PhaseCheckpoint(phase="discovery", step="initial_exploration"),
            PhaseCheckpoint(phase="domain", step="domain_identification"),
            PhaseCheckpoint(phase="problem", step="problem_definition"),
            PhaseCheckpoint(phase="tta", step="trend_analysis"),
            PhaseCheckpoint(phase="jtbd", step="customer_needs"),
            PhaseCheckpoint(phase="validation", step="red_team"),
            PhaseCheckpoint(phase="synthesis", step="final_synthesis"),
        ]

        # Get relevant frameworks from Neo4j
        frameworks = await get_related_frameworks_for_journey(problem)
        journey.frameworks_used = [f["name"] for f in frameworks]

        # Save to Neo4j
        await create_journey_in_neo4j(journey)

        # Save to Supabase
        await save_journey_to_supabase(journey)

        self._current_journey = journey
        logger.info(f"Created journey {new_id} for user {self.user_id}")

        return journey

    async def get_journey(self, journey_id: str = None) -> Optional[UserJourney]:
        """Get a specific journey or the current one."""
        if journey_id:
            # Try Neo4j first (has relationships)
            neo4j_data = await get_journey_from_neo4j(journey_id)
            if neo4j_data:
                # Merge with Supabase data (has full details)
                supabase_journey = await load_journey_from_supabase(
                    self.user_id, journey_id
                )
                if supabase_journey:
                    # Update with Neo4j relationships
                    supabase_journey.completed_phases = neo4j_data.get("completed_phases", [])
                    supabase_journey.frameworks_used = neo4j_data.get("frameworks_used", [])
                    return supabase_journey
                return UserJourney.from_dict(neo4j_data)

            # Fallback to Supabase only
            return await load_journey_from_supabase(self.user_id, journey_id)

        return self._current_journey

    async def list_journeys(self) -> List[Dict]:
        """List all journeys for this user."""
        return await list_user_journeys_from_supabase(self.user_id)

    async def get_recent_journey(self) -> Optional[UserJourney]:
        """Get the most recent journey for this user."""
        journeys = await self.list_journeys()
        if not journeys:
            return None

        # Sort by last_active and get most recent
        journeys_sorted = sorted(
            journeys,
            key=lambda j: j.get("last_active", ""),
            reverse=True
        )

        if journeys_sorted:
            most_recent = journeys_sorted[0]
            return await self.get_journey(most_recent["id"])

        return None

    async def save_journey(self, journey: UserJourney) -> bool:
        """Save journey to both Neo4j and Supabase."""
        journey.last_active = datetime.now().isoformat()
        self._current_journey = journey

        # Update Neo4j
        await update_journey_phase_in_neo4j(
            journey.id,
            journey.current_phase.value if isinstance(journey.current_phase, JourneyPhase) else journey.current_phase,
            journey.insights if hasattr(journey, 'insights') else []
        )

        # Save to Supabase
        return await save_journey_to_supabase(journey)

    async def update_phase(
        self,
        new_phase: str,
        insights: List[Dict] = None,
        checkpoint_step: str = None
    ) -> bool:
        """
        Update journey to a new phase.

        Like marking tasks complete in Conductor's plan.md.
        """
        if not self._current_journey:
            logger.error("No active journey to update")
            return False

        # Convert phase string to enum
        try:
            phase_enum = JourneyPhase(new_phase)
        except ValueError:
            phase_enum = JourneyPhase.DISCOVERY

        # Mark previous phase as completed
        if self._current_journey.current_phase.value not in self._current_journey.completed_phases:
            self._current_journey.completed_phases.append(
                self._current_journey.current_phase.value
            )

        # Update current phase
        self._current_journey.current_phase = phase_enum
        self._current_journey.last_active = datetime.now().isoformat()

        # Update checkpoint
        if checkpoint_step:
            for cp in self._current_journey.checkpoints:
                if cp.phase == new_phase and cp.step == checkpoint_step:
                    cp.status = "completed"
                    cp.completed_at = datetime.now().isoformat()
                    break

        # Add insights
        insight_objects = []
        if insights:
            import uuid
            for i in insights:
                insight = Insight(
                    id=f"insight_{uuid.uuid4().hex[:8]}",
                    type=InsightType(i.get("type", "fact")),
                    content=i.get("content", ""),
                    confidence=i.get("confidence", 0.5),
                    source_phase=new_phase,
                )
                self._current_journey.insights.append(insight)
                insight_objects.append(insight)

        # Persist to Neo4j
        await update_journey_phase_in_neo4j(
            self._current_journey.id,
            new_phase,
            insight_objects
        )

        # Persist to Supabase
        await save_journey_to_supabase(self._current_journey)

        logger.info(f"Journey {self._current_journey.id} updated to phase {new_phase}")
        return True

    async def add_insight(self, insight_type: str, content: str, confidence: float = 0.5) -> Insight:
        """Add a single insight to the current journey."""
        import uuid

        if not self._current_journey:
            raise ValueError("No active journey")

        insight = Insight(
            id=f"insight_{uuid.uuid4().hex[:8]}",
            type=InsightType(insight_type),
            content=content,
            confidence=confidence,
            source_phase=self._current_journey.current_phase.value,
        )

        self._current_journey.insights.append(insight)
        await save_journey_to_supabase(self._current_journey)

        return insight

    async def get_journey_context(self, max_insights: int = 10) -> str:
        """
        Get journey context for injection into agent prompts.

        This is the key integration point - provides persistent memory
        context to any LangGraph pipeline or agent.
        """
        if not self._current_journey:
            return ""

        j = self._current_journey

        # Build context string
        context_parts = [
            f"## User Journey Context",
            f"**Problem:** {j.problem_title or j.problem_spec[:100]}",
            f"**Current Phase:** {j.current_phase.value}",
            f"**Completed Phases:** {', '.join(j.completed_phases) or 'None yet'}",
        ]

        # Add frameworks
        if j.frameworks_used:
            context_parts.append(f"**Frameworks Applied:** {', '.join(j.frameworks_used[:5])}")

        # Add recent insights
        if j.insights:
            context_parts.append("\n**Key Insights:**")
            for insight in j.insights[-max_insights:]:
                tested_marker = "✓" if insight.tested else "?"
                context_parts.append(
                    f"- [{tested_marker}] ({insight.type.value}) {insight.content[:100]}"
                )

        # Add checkpoint progress
        completed_checkpoints = [cp for cp in j.checkpoints if cp.status == "completed"]
        if completed_checkpoints:
            context_parts.append(f"\n**Progress:** {len(completed_checkpoints)}/{len(j.checkpoints)} checkpoints")

        return "\n".join(context_parts)

    async def get_checkpointer(self):
        """Get PostgreSQL checkpointer for LangGraph pipelines."""
        if not self._checkpointer:
            self._checkpointer = await get_postgres_checkpointer()
        return self._checkpointer

    def get_thread_id(self, pipeline_name: str = "default") -> str:
        """
        Generate thread ID for LangGraph checkpointing.

        Format: {pipeline}_{user_id}_{journey_id}
        This ensures state persists across sessions for the same journey.
        """
        journey_id = self._current_journey.id if self._current_journey else "no_journey"
        return f"{pipeline_name}_{self.user_id}_{journey_id}"


# =============================================================================
# Convenience Functions
# =============================================================================

async def get_journey_context(user_id: str, journey_id: str = None) -> str:
    """Quick access to journey context for agent prompts."""
    store = JourneyStore(user_id)

    if journey_id:
        journey = await store.get_journey(journey_id)
        if journey:
            store._current_journey = journey
            return await store.get_journey_context()

    return ""


def create_journey_context_injection(context: str) -> str:
    """Format journey context for system prompt injection."""
    if not context:
        return ""

    return f"""
[PERSISTENT MEMORY - USER JOURNEY]
{context}
[END JOURNEY CONTEXT]

IMPORTANT: Use this journey context to:
1. Reference previous insights and progress
2. Avoid re-asking questions already answered
3. Build on frameworks already applied
4. Track assumptions that need testing
"""
