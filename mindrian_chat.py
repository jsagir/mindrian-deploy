"""
Mindrian - Multi-Bot PWS Platform
Larry Core + Specialized Tool Workshop Bots
Enhanced with Task Lists, Action Buttons, File Upload, Charts, Data Persistence,
Chain-of-Thought Steps, Conversation Starters, and Session Resume
"""

import os
import json
import asyncio
import subprocess
import sys
import logging
import uuid
from datetime import datetime
import chainlit as cl

# Module logger for debugging
logger = logging.getLogger("mindrian")
from chainlit.input_widget import Select, Switch, Slider
from chainlit.server import app as fastapi_app
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi import APIRouter, Request
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

# === Sentry Error Monitoring ===
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=0.1,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        )
        logging.getLogger("mindrian").info("[SENTRY] Error monitoring initialized")
    except ImportError:
        logging.getLogger("mindrian").warning("[SENTRY] sentry-sdk not installed - error monitoring disabled")

# === Triple-Mode Architecture ===
# Entry point routing, mode management, and grounding logic (v2 - LangExtract powered)
try:
    from protocols.triple_mode import (
        init_triple_mode_session,
        auto_detect_entry_point,
        extract_and_update_progress,
        check_semantic_grounding,
        handle_entry_point_selection,
        handle_mode_or_stage,
        handle_grounding_response,
        show_entry_point_selector,
        show_exploration_progress_sidebar,
        show_grounding_prompt,
        get_entry_point_buttons,
        get_coaching_hint_for_message,
        restore_triple_mode_state,
    )
    TRIPLE_MODE_ENABLED = True
except ImportError as e:
    print(f"Triple-mode not available: {e}")
    TRIPLE_MODE_ENABLED = False

# === Cron API Endpoint via Middleware ===
# Using middleware to intercept /api/daily-summary BEFORE Chainlit's catch-all routing

CRON_SECRET = os.getenv("CRON_SECRET", "")

class CronEndpointMiddleware(BaseHTTPMiddleware):
    """Middleware to handle /api/daily-summary before Chainlit routing."""

    async def dispatch(self, request: Request, call_next):
        # Handle /api/health - public endpoint, no auth needed
        if request.url.path == "/api/health":
            import chainlit as cl
            db_status = "not_configured"
            db_error = None
            tables_exist = []
            try:
                # get_data_layer() is sync when using @cl.data_layer decorator
                data_layer = cl.data.get_data_layer()
                if data_layer:
                    db_status = "connected"
                    # Check if tables exist
                    try:
                        from sqlalchemy import text
                        async with data_layer.engine.connect() as conn:
                            result = await conn.execute(text(
                                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                            ))
                            tables_exist = [row[0] for row in result.fetchall()]
                    except Exception as te:
                        db_error = f"Table check failed: {te}"
                else:
                    db_status = "no_data_layer"
            except Exception as e:
                db_status = "error"
                db_error = str(e)
            return JSONResponse(content={
                "status": "ok",
                "database": db_status,
                "database_error": db_error,
                "tables": tables_exist,
                "required_tables": ["users", "threads", "steps", "elements", "feedbacks"],
                "database_url_set": bool(os.environ.get("DATABASE_URL")),
                "auth_secret_set": bool(os.environ.get("CHAINLIT_AUTH_SECRET")),
            })

        # Handle /api/public-config - public endpoint for login page
        if request.url.path == "/api/public-config":
            return JSONResponse(content={
                "supabase_url": os.environ.get("SUPABASE_URL", ""),
                "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
            })

        # Handle /api/lightrag-health - test LightRAG connection
        if request.url.path == "/api/lightrag-health":
            import requests as req
            lightrag_url = os.environ.get("LIGHTRAG_URL", "https://mondrian-ts.onrender.com")
            lightrag_user = os.environ.get("LIGHTRAG_USERNAME", "jsagir")
            lightrag_pass = os.environ.get("LIGHTRAG_PASSWORD")
            lightrag_api_key = os.environ.get("LIGHTRAG_API_KEY")
            if not lightrag_api_key:
                logger.warning("[SECURITY] LIGHTRAG_API_KEY not set - LightRAG health check will fail")

            result = {
                "url": lightrag_url,
                "username": lightrag_user,
                "api_key_set": bool(lightrag_api_key),
                "password_set": bool(lightrag_pass),
                "login_status": "not_tested",
                "token": None,
                "error": None,
            }

            if not lightrag_pass:
                result["error"] = "LIGHTRAG_PASSWORD not set"
                return JSONResponse(content=result)

            try:
                # Test login with both API key and OAuth2
                resp = req.post(
                    f"{lightrag_url}/login",
                    headers={"X-API-Key": lightrag_api_key},
                    data={"username": lightrag_user, "password": lightrag_pass},
                    timeout=30  # Longer timeout for cold start
                )
                if resp.status_code == 200:
                    token_data = resp.json()
                    result["login_status"] = "success"
                    result["token"] = token_data.get("access_token", "")[:20] + "..." if token_data.get("access_token") else None

                    # Test a simple query to verify full auth (separate try block)
                    token = token_data.get("access_token")
                    try:
                        test_resp = req.post(
                            f"{lightrag_url}/query",
                            headers={
                                "X-API-Key": lightrag_api_key,
                                "Authorization": f"Bearer {token}"
                            },
                            json={"query": "test connection", "mode": "local"},
                            timeout=30  # Longer timeout for cold start
                        )
                        result["query_test"] = "success" if test_resp.status_code == 200 else f"failed: {test_resp.status_code}"
                    except req.exceptions.Timeout:
                        result["query_test"] = "timeout (server may be waking up)"
                    except Exception as qe:
                        result["query_test"] = f"error: {str(qe)[:50]}"
                else:
                    result["login_status"] = f"failed: {resp.status_code}"
                    result["error"] = resp.text[:200]
            except req.exceptions.Timeout:
                result["login_status"] = "timeout"
                result["error"] = "Server may be waking up from sleep. Try again in 30s."
            except Exception as e:
                result["login_status"] = "error"
                result["error"] = str(e)

            return JSONResponse(content=result)

        # Handle /api/init-db - one-time database initialization (auth required)
        if request.url.path == "/api/init-db":
            secret = request.query_params.get("secret", "")
            if CRON_SECRET and secret != CRON_SECRET:
                return JSONResponse(status_code=403, content={"error": "Invalid secret", "success": False})
            try:
                database_url = os.environ.get("DATABASE_URL")
                if not database_url:
                    return JSONResponse(content={"success": False, "error": "No DATABASE_URL"})

                # Convert to asyncpg format
                if database_url.startswith("postgresql://"):
                    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                elif database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

                from sqlalchemy.ext.asyncio import create_async_engine
                from sqlalchemy import text

                # Raw SQL to create Chainlit tables - matching Chainlit's expected schema
                # Chainlit uses TEXT for IDs and timestamps, not UUID/TIMESTAMP
                CREATE_STATEMENTS = [
                    # Idempotent DDL - only creates if not exists
                    """CREATE TABLE IF NOT EXISTS users (
                        "id" TEXT PRIMARY KEY,
                        "identifier" TEXT NOT NULL UNIQUE,
                        "createdAt" TEXT,
                        "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb
                    )""",
                    """CREATE TABLE IF NOT EXISTS threads (
                        "id" TEXT PRIMARY KEY,
                        "createdAt" TEXT,
                        "name" TEXT,
                        "userId" TEXT REFERENCES users("id") ON DELETE SET NULL,
                        "userIdentifier" TEXT,
                        "tags" TEXT[],
                        "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb
                    )""",
                    """CREATE TABLE IF NOT EXISTS steps (
                        "id" TEXT PRIMARY KEY,
                        "name" TEXT NOT NULL,
                        "type" TEXT NOT NULL,
                        "threadId" TEXT REFERENCES threads("id") ON DELETE CASCADE,
                        "parentId" TEXT,
                        "streaming" BOOLEAN,
                        "waitForAnswer" BOOLEAN,
                        "isError" BOOLEAN,
                        "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
                        "tags" TEXT[],
                        "input" TEXT,
                        "output" TEXT,
                        "createdAt" TEXT,
                        "start" TEXT,
                        "end" TEXT,
                        "generation" JSONB,
                        "showInput" TEXT,
                        "language" TEXT
                    )""",
                    """CREATE TABLE IF NOT EXISTS elements (
                        "id" TEXT PRIMARY KEY,
                        "threadId" TEXT REFERENCES threads("id") ON DELETE CASCADE,
                        "type" TEXT NOT NULL,
                        "chainlitKey" TEXT,
                        "url" TEXT,
                        "objectKey" TEXT,
                        "name" TEXT NOT NULL,
                        "display" TEXT,
                        "size" TEXT,
                        "language" TEXT,
                        "page" INTEGER,
                        "forId" TEXT,
                        "mime" TEXT,
                        "props" JSONB,
                        "autoPlay" BOOLEAN,
                        "playerConfig" JSONB
                    )""",
                    """CREATE TABLE IF NOT EXISTS feedbacks (
                        "id" TEXT PRIMARY KEY,
                        "forId" TEXT NOT NULL,
                        "threadId" TEXT REFERENCES threads("id") ON DELETE CASCADE,
                        "value" INTEGER NOT NULL,
                        "comment" TEXT
                    )""",
                    """CREATE INDEX IF NOT EXISTS idx_threads_userid ON threads("userId")""",
                    """CREATE INDEX IF NOT EXISTS idx_threads_useridentifier ON threads("userIdentifier")""",
                    """CREATE INDEX IF NOT EXISTS idx_steps_threadid ON steps("threadId")""",
                    """CREATE INDEX IF NOT EXISTS idx_elements_threadid ON elements("threadId")""",
                    """CREATE INDEX IF NOT EXISTS idx_feedbacks_threadid ON feedbacks("threadId")""",
                    """CREATE INDEX IF NOT EXISTS idx_feedbacks_forid ON feedbacks("forId")""",
                ]

                engine = create_async_engine(database_url)
                async with engine.begin() as conn:
                    for stmt in CREATE_STATEMENTS:
                        await conn.execute(text(stmt))

                # Verify tables
                async with engine.connect() as conn:
                    result = await conn.execute(text("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """))
                    tables = [row[0] for row in result.fetchall()]
                await engine.dispose()

                return JSONResponse(content={
                    "success": True,
                    "message": "Database tables created",
                    "tables": tables
                })
            except Exception as e:
                import traceback
                return JSONResponse(content={
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })

        # Handle /api/embed-opportunities - Generate embeddings for all opportunities
        if request.url.path == "/api/embed-opportunities":
            force = request.query_params.get("force", "false").lower() == "true"

            try:
                args = [sys.executable, "scripts/embed_all_opportunities.py"]
                if force:
                    args.append("--force")

                result = subprocess.run(
                    args,
                    capture_output=True, text=True, timeout=600,  # 10 min timeout
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )

                return JSONResponse(content={
                    "success": result.returncode == 0,
                    "force_mode": force,
                    "output": result.stdout[-2000:] if result.stdout else "",
                    "errors": result.stderr[-500:] if result.stderr else ""
                })
            except subprocess.TimeoutExpired:
                return JSONResponse(status_code=504, content={
                    "success": False,
                    "error": "Embedding timed out after 10 minutes"
                })
            except Exception as e:
                return JSONResponse(status_code=500, content={
                    "success": False,
                    "error": str(e)
                })

        if request.url.path == "/api/daily-summary":
            # Handle cron endpoint
            secret = request.query_params.get("secret", "")

            if CRON_SECRET and secret != CRON_SECRET:
                return JSONResponse(status_code=403, content={"error": "Invalid secret", "success": False})

            try:
                result = subprocess.run(
                    [sys.executable, "scripts/daily_summary.py", "--last-24h"],
                    capture_output=True, text=True, timeout=300,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                if result.returncode == 0:
                    return JSONResponse(content={
                        "success": True,
                        "message": "Daily summary sent",
                        "output": result.stdout[-500:] if result.stdout else ""
                    })
                else:
                    # Combine stderr and stdout for better error reporting
                    error_msg = result.stderr.strip() if result.stderr else ""
                    stdout_msg = result.stdout.strip() if result.stdout else ""

                    # Check for common config issues
                    if "Email not configured" in error_msg or "Email not configured" in stdout_msg:
                        return JSONResponse(status_code=503, content={
                            "success": False,
                            "error": "Email not configured. Set SMTP_USER/SMTP_PASSWORD or SENDGRID_API_KEY in Render environment.",
                            "hint": "Add email credentials to Render > Environment"
                        })

                    return JSONResponse(status_code=500, content={
                        "success": False,
                        "error": error_msg[-500:] if error_msg else stdout_msg[-500:] or "Unknown error",
                        "stdout": stdout_msg[-200:],
                        "stderr": error_msg[-200:]
                    })
            except subprocess.TimeoutExpired:
                return JSONResponse(status_code=500, content={"success": False, "error": "Timeout after 5 minutes"})
            except Exception as e:
                return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

        # Handle /api/qa-feedback - admin review of QA feedback submissions
        if request.url.path == "/api/qa-feedback":
            try:
                from supabase import create_client
                sb_url = os.getenv("SUPABASE_URL")
                sb_key = os.getenv("SUPABASE_SERVICE_KEY")
                sb_bucket = os.getenv("SUPABASE_BUCKET", "mindrian-files")
                if not sb_url or not sb_key:
                    return JSONResponse(status_code=503, content={"error": "Supabase not configured"})

                date_filter = request.query_params.get("date", None)
                prefix = f"qa_feedback/{date_filter}" if date_filter else "qa_feedback"

                sb_client = create_client(sb_url, sb_key)
                files = sb_client.storage.from_(sb_bucket).list(prefix)
                feedback_items = []

                # List files — Supabase returns folders at top level, files inside date folders
                if date_filter:
                    # Direct file list for a specific date
                    for f in (files or []):
                        if f.get("name", "").endswith(".json"):
                            try:
                                data = sb_client.storage.from_(sb_bucket).download(f"{prefix}/{f['name']}")
                                feedback_items.append(json.loads(data.decode("utf-8")))
                            except Exception:
                                pass
                else:
                    # List date folders, then files in each
                    for folder in (files or []):
                        folder_name = folder.get("name", "")
                        if not folder_name:
                            continue
                        try:
                            inner_files = sb_client.storage.from_(sb_bucket).list(f"qa_feedback/{folder_name}")
                            for f in (inner_files or []):
                                if f.get("name", "").endswith(".json"):
                                    try:
                                        data = sb_client.storage.from_(sb_bucket).download(
                                            f"qa_feedback/{folder_name}/{f['name']}"
                                        )
                                        feedback_items.append(json.loads(data.decode("utf-8")))
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                return JSONResponse(content={
                    "total": len(feedback_items),
                    "date_filter": date_filter,
                    "feedback": feedback_items,
                })
            except ImportError:
                return JSONResponse(status_code=503, content={"error": "supabase package not installed"})
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})

        # Not our endpoint, continue to Chainlit
        return await call_next(request)

# Add middleware BEFORE any routes
# This middleware handles /api/* endpoints BEFORE Chainlit's auth kicks in
fastapi_app.add_middleware(CronEndpointMiddleware)
print("[API] Middleware registered: /api/health, /api/public-config, /api/lightrag-health, /api/embed-opportunities, /api/daily-summary, /api/qa-feedback")

from google import genai
from google.genai import types

# === GraphRAG Lite - Conditional context enrichment ===
try:
    from tools.graphrag_lite import enrich_for_larry, enrich_for_bot, should_retrieve
    from tools.graph_router import graph_score_agents, classify_and_route, has_problem_language
    GRAPHRAG_ENABLED = True
    print("GraphRAG Lite + Graph Router enabled")
except ImportError:
    GRAPHRAG_ENABLED = False
    print("GraphRAG Lite not available (Neo4j not configured)")

# === Context Engine - Budget-aware context assembly with KG-RAG patterns ===
try:
    from tools.context_engine import assemble_context as ce_assemble_context, classify_query_intent
    CONTEXT_ENGINE_ENABLED = True
    print("Context Engine enabled (KG-RAG patterns + context engineering)")
except ImportError:
    CONTEXT_ENGINE_ENABLED = False
    print("Context Engine not available")

# === Smart Phase Tracker - LLM-based phase detection ===
try:
    from tools.smart_phase_tracker import (
        analyze_workshop_state,
        format_progress_indicator,
        should_show_advance_prompt,
        get_smart_phase_message,
        extract_phase_context
    )
    SMART_PHASE_ENABLED = True
    print("Smart Phase Tracker enabled (LangChain + Gemini)")
except ImportError as e:
    SMART_PHASE_ENABLED = False
    print(f"Smart Phase Tracker not available: {e}")

# === Phase Insights - User-facing intelligence from smart_phase_tracker ===
try:
    from tools.phase_insights import (
        generate_phase_insights,
        should_show_insight,
        append_insight_to_response,
        get_insight_actions,
        get_smart_sidebar_data,
        get_phase_insight_for_response,
        PhaseInsight,
        InsightType
    )
    PHASE_INSIGHTS_ENABLED = True
    print("Phase Insights module enabled (intelligent progress surfacing)")
except ImportError as e:
    PHASE_INSIGHTS_ENABLED = False
    print(f"Phase Insights not available: {e}")

# === Recursive Intelligence Session Logger - Learning from every session ===
try:
    from utils.session_logger import (
        log_session_event,
        log_session_summary,
        track_agent_start,
        get_agents_used,
        get_logger_stats
    )
    SESSION_LOGGER_ENABLED = True
    print("Session Logger enabled (Recursive Intelligence Phase 1)")
except ImportError as e:
    SESSION_LOGGER_ENABLED = False
    print(f"Session Logger not available: {e}")
    # Fallback stubs
    async def log_session_event(*args, **kwargs): pass
    async def log_session_summary(*args, **kwargs): pass
    def track_agent_start(*args, **kwargs): pass
    def get_agents_used(*args, **kwargs): return []
    def get_logger_stats(): return {}

# === Reaction Classifier - Detect user sentiment signals ===
try:
    from utils.reaction_classifier import classify_reaction, ReactionSignal
    REACTION_CLASSIFIER_ENABLED = True
    print("Reaction Classifier enabled (Recursive Intelligence Phase 2)")
except ImportError as e:
    REACTION_CLASSIFIER_ENABLED = False
    print(f"Reaction Classifier not available: {e}")
    # Fallback stub
    def classify_reaction(msg):
        return type('ReactionSignal', (), {'signal_type': 'neutral', 'confidence': 0.5, 'indicators': []})()

# === Session Distiller - Extract insights at session end ===
try:
    from utils.session_distiller import on_session_end, on_significant_turn
    SESSION_DISTILLER_ENABLED = True
    print("Session Distiller enabled (Recursive Intelligence Phase 3)")
except ImportError as e:
    SESSION_DISTILLER_ENABLED = False
    print(f"Session Distiller not available: {e}")
    async def on_session_end(*args, **kwargs): pass
    async def on_significant_turn(*args, **kwargs): return None

# === Hybrid LLM Router - Claude Opus for orchestration, Gemini Flash for bulk ===
try:
    from utils.llm_router import (
        LLMRouter,
        CostTracker,
        TrackedTavilySearch,
        HybridResearchPipeline,
        cost_tracker as global_cost_tracker,  # Use the module-level global
    )
    LLM_ROUTER_ENABLED = True

    def get_llm_router() -> type:
        """Get the LLMRouter class (uses static methods)."""
        return LLMRouter

    def get_cost_tracker() -> CostTracker:
        """Get the global cost tracker."""
        return global_cost_tracker

    print("Hybrid LLM Router enabled (Claude Opus + Gemini Flash)")
except ImportError as e:
    LLM_ROUTER_ENABLED = False
    print(f"LLM Router not available: {e}")
    # Fallback stubs
    class _DummyRouter:
        @staticmethod
        async def orchestrate(*args, **kwargs): return ""
        @staticmethod
        async def bulk_generate(*args, **kwargs): return ""
    def get_llm_router(): return _DummyRouter
    def get_cost_tracker(): return None

# === User LazyGraph + LightRAG Opportunity Bank - Per-user memory across sessions ===
try:
    from tools.session_memory import (
        on_session_start as session_memory_start,
        on_message_processed as session_memory_process,
        get_user_context as get_session_user_context,
        extract_opportunities_with_lightrag,
        queue_opportunity_notification,
        get_pending_opportunities,
    )
    SESSION_MEMORY_ENABLED = True
    print("Session Memory enabled (per-user LazyGraph + LightRAG)")
except ImportError as e:
    SESSION_MEMORY_ENABLED = False
    print(f"Session Memory not available: {e}")
    # Fallback stubs
    async def session_memory_start(*args, **kwargs): return None
    async def session_memory_process(*args, **kwargs): return None
    async def get_session_user_context(*args, **kwargs): return ""
    async def extract_opportunities_with_lightrag(*args, **kwargs): return {}
    def queue_opportunity_notification(*args, **kwargs): pass
    def get_pending_opportunities(*args, **kwargs): return []

# === Self-Describing Phases - Auto-discovery from prompt modules ===
try:
    from utils.phase_discovery import get_phases_for_bot, get_tracker_criteria_for_bot, bot_has_phases
    PHASE_DISCOVERY_ENABLED = True
    print("Phase Discovery enabled (self-describing phases)")
except ImportError as e:
    PHASE_DISCOVERY_ENABLED = False
    print(f"Phase Discovery not available: {e}")
    # Fallback stubs
    def get_phases_for_bot(bot_id): return None
    def bot_has_phases(bot_id): return False

# === WorkshopRoadmap is now the ONLY progress UI ===
# TaskList fallbacks have been removed (Feb 2026 simplification)
# All progress visualization goes through create_or_update_roadmap()

# === UI Elements - Custom components for grading, opportunities, etc. ===
try:
    from utils.ui_elements import (
        create_assessment_tasklist,
        update_task_status,
        create_grade_reveal,
        create_score_breakdown,
        create_opportunity_card,
        create_report_download,
        create_evidence_display,
        display_grading_results,
        display_opportunities,
    )
    UI_ELEMENTS_ENABLED = True
    print("UI Elements module enabled (GradeReveal, ScoreBreakdown)")
except ImportError as e:
    UI_ELEMENTS_ENABLED = False
    print(f"UI Elements not available: {e}")

# === Smart Onboarding - Intelligent PWS concept introduction ===
try:
    from utils.smart_onboarding import (
        get_progressive_welcome,
        get_onboarding_tour_steps,
        mark_onboarding_skipped,
        mark_onboarding_completed,
        get_onboarding_state,
        should_show_concept_help,
    )
    SMART_ONBOARDING_ENABLED = True
    print("Smart Onboarding enabled (progressive welcome, tour)")
except ImportError as e:
    SMART_ONBOARDING_ENABLED = False
    print(f"Smart Onboarding not available: {e}")

# === Bounded History Manager - Prevent memory leaks ===
try:
    from utils.history_manager import (
        add_to_history,
        get_bounded_history,
        compact_history_if_needed,
        MAX_HISTORY_LENGTH,
    )
    HISTORY_MANAGER_ENABLED = True
    print(f"History Manager enabled (max {MAX_HISTORY_LENGTH} messages)")
except ImportError as e:
    HISTORY_MANAGER_ENABLED = False
    print(f"History Manager not available: {e}")
    # Fallback stubs
    MAX_HISTORY_LENGTH = 50
    def add_to_history(history, role, content, **kwargs):
        # Normalize role: Gemini expects "user" or "model", never "assistant"
        if role == "assistant":
            role = "model"
        history.append({"role": role, "content": content})
        return history[-MAX_HISTORY_LENGTH:]
    def get_bounded_history(history, **kwargs):
        return history[-MAX_HISTORY_LENGTH:]
    def compact_history_if_needed(history, **kwargs):
        return history

# === LangGraph Pipelines - Advanced multi-step workflows ===
try:
    from intelligence.pipelines import (
        # BONO Innovation (Six Hats + Lateral Thinking)
        run_bono_session,
        format_bono_report,
        HAT_SEQUENCES,
        HAT_ICONS,
        # Reverse Salient Discovery
        run_reverse_salient,
        format_reverse_salient_result,
        # Domain Discovery
        run_domain_discovery,
        format_domain_discovery_result,
        # Oracle Prediction Market
        run_oracle_formulation,
        run_oracle_resolution,
        format_research_brief,
        # Message Router
        route_message as route_message_pipeline,
        # File Processing
        process_uploaded_files_langgraph,
        # Grading
        run_grading_pipeline,
        # Minto Pyramid (already used)
        run_minto_pipeline,
        format_minto_result,
        # Genesis Expert Breakdown (multi-agent + BONO)
        run_genesis_pipeline,
        format_genesis_report,
    )
    LANGGRAPH_PIPELINES_ENABLED = True
    print("LangGraph Pipelines enabled (BONO, RS, Domain, Oracle, Router)")
except ImportError as e:
    LANGGRAPH_PIPELINES_ENABLED = False
    print(f"LangGraph Pipelines not available: {e}")
    # Fallback stubs
    async def run_bono_session(*args, **kwargs): return {"error": "Pipeline not available"}
    async def run_reverse_salient(*args, **kwargs): return {"error": "Pipeline not available"}
    async def run_domain_discovery(*args, **kwargs): return {"error": "Pipeline not available"}
    async def run_oracle_formulation(*args, **kwargs): return {"error": "Pipeline not available"}
    async def run_grading_pipeline(*args, **kwargs): return {"error": "Pipeline not available"}
    async def run_genesis_pipeline(*args, **kwargs): return {"error": "Pipeline not available"}
    def format_bono_report(*args, **kwargs): return "Pipeline not available"
    def format_reverse_salient_result(*args, **kwargs): return "Pipeline not available"
    def format_genesis_report(*args, **kwargs): return "Pipeline not available"
    HAT_SEQUENCES = {}
    HAT_ICONS = {}


# === TaskList Compatibility Helper ===
async def safe_task_list_send(task_list):
    """
    Send TaskList with error handling for Chainlit version compatibility.
    Some Chainlit versions pass 'for_id' internally which causes TypeError.
    """
    try:
        await task_list.send()
    except TypeError as e:
        if "for_id" in str(e):
            # Skip - Chainlit version incompatibility, state still updated
            pass
        else:
            raise


def extract_phase_insights(history: list, phases: list, current_phase: int, workshop_state=None) -> dict:
    """
    Extract brief insights for each completed phase from conversation history.

    If workshop_state (from smart_phase_tracker) is provided, uses AI-extracted
    evidence. Otherwise falls back to simple keyword matching.

    Returns a dict of {phase_index: "insight text"} for display in the sidebar.
    """
    # Use smart insights if workshop_state is available (from get_smart_sidebar_data)
    if workshop_state and PHASE_INSIGHTS_ENABLED:
        try:
            sidebar_data = get_smart_sidebar_data(workshop_state, history)
            return sidebar_data.get("phaseContext", {})
        except Exception as e:
            print(f"Smart insights fallback: {e}")
            # Fall through to simple extraction

    # Simple keyword extraction fallback
    insights = {}
    phase_keywords = {
        "Introduction": "Started the workshop",
        "Domain": "Defined the problem domain",
        "Driving Forces": "Identified key driving forces",
        "Uncertainty": "Assessed uncertainties",
        "Matrix": "Built scenario matrix",
        "Narratives": "Developed scenario stories",
        "Synthesis": "Synthesized findings",
        "Stakeholder": "Mapped stakeholders",
        "Problem": "Clarified the problem",
        "Validation": "Validated assumptions",
        "Research": "Gathered research",
        "Analysis": "Completed analysis",
    }

    for i in range(min(current_phase + 1, len(phases))):
        phase_name = phases[i].get("name", "")
        for keyword, insight in phase_keywords.items():
            if keyword.lower() in phase_name.lower():
                insights[i] = insight
                break
        else:
            if phases[i].get("status") == "done":
                insights[i] = f"Completed {phase_name}"

    return insights


# === Config ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
# FileSearch store owned by a different API key
GOOGLE_FILESEARCH_API_KEY = os.getenv("GOOGLE_FILESEARCH_API_KEY") or GOOGLE_API_KEY
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# Chainlit uses CHAINLIT_DATABASE_URL, fallback to DATABASE_URL for compatibility
DATABASE_URL = os.getenv("CHAINLIT_DATABASE_URL") or os.getenv("DATABASE_URL")

client = genai.Client(api_key=GOOGLE_API_KEY)
filesearch_client = genai.Client(api_key=GOOGLE_FILESEARCH_API_KEY)

# === API Key Diagnostics (runs once at startup) ===
def _check_api_keys():
    """Log API key status at startup for debugging."""
    keys = {
        "GOOGLE_API_KEY": GOOGLE_API_KEY,
        "TAVILY_API_KEY": TAVILY_API_KEY,
        "SERPAPI_KEY": os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY"),
        "FRED_API_KEY": os.getenv("FRED_API_KEY"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    }
    print("=" * 50)
    print("API KEY DIAGNOSTIC")
    print("=" * 50)
    for name, value in keys.items():
        if value:
            masked = value[:6] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"  ✅ {name}: {masked}")
        else:
            print(f"  ❌ {name}: NOT FOUND")
    print("=" * 50)

_check_api_keys()

# === Supabase Authentication ===
# Full Supabase Auth integration with password, magic links, and OAuth support.
#
# Required environment variables:
#   SUPABASE_URL - Your Supabase project URL
#   SUPABASE_ANON_KEY - Public anon key for auth operations
#   SUPABASE_JWT_SECRET - JWT secret for token validation
#   CHAINLIT_AUTH_SECRET - Chainlit's auth secret
#
# Optional (for OAuth):
#   OAUTH_GOOGLE_CLIENT_ID, OAUTH_GOOGLE_CLIENT_SECRET
#   OAUTH_GITHUB_CLIENT_ID, OAUTH_GITHUB_CLIENT_SECRET

try:
    from auth.supabase_auth import (
        SUPABASE_AUTH_ENABLED,
        authenticate_with_password,
        validate_supabase_jwt,
        check_rate_limit,
        record_auth_attempt,
        clear_auth_attempts,
        get_user_profile,
    )
    print(f"[AUTH] Supabase Auth module loaded. Enabled: {SUPABASE_AUTH_ENABLED}")
except ImportError as e:
    SUPABASE_AUTH_ENABLED = False
    print(f"[AUTH] Supabase Auth module not available: {e}")


# === Password Authentication (Supabase) ===
# Uses Chainlit's built-in login screen with Supabase validation
if SUPABASE_AUTH_ENABLED:
    @cl.password_auth_callback
    def supabase_password_auth(username: str, password: str) -> Optional[cl.User]:
        """
        Validate username/password against Supabase Auth.
        Shows Chainlit's built-in login screen.
        """
        try:
            # Rate limiting check
            if not check_rate_limit(username):
                logger.warning(f"[AUTH] Rate limit exceeded for {username}")
                return None

            # Authenticate with Supabase
            result = authenticate_with_password(username, password)

            if result and result.get("user"):
                user_data = result["user"]
                user_id = user_data.get("id", username)
                email = user_data.get("email", username)

                # Clear failed attempts on success
                clear_auth_attempts(username)

                logger.info(f"[AUTH] Password authenticated: {email}")

                return cl.User(
                    identifier=user_id,
                    metadata={
                        "email": email,
                        "provider": "supabase_password",
                        "role": user_data.get("role", "authenticated"),
                    }
                )
            else:
                # Record failed attempt
                record_auth_attempt(username, success=False)
                return None

        except Exception as e:
            logger.error(f"[AUTH] Password auth error: {e}")
            record_auth_attempt(username, success=False)
            return None

    print("[AUTH] Supabase password authentication ENABLED")
elif os.getenv("CHAINLIT_AUTH_SECRET"):
    # Fallback: Simple env-based password auth (only when auth secret is set)
    # Set MINDRIAN_USER_<NAME>_PASSWORD=password in env
    @cl.password_auth_callback
    def simple_password_auth(username: str, password: str) -> Optional[cl.User]:
        """
        Simple password auth using environment variables.
        Set MINDRIAN_USER_<NAME>_PASSWORD=password for each user.
        Example: MINDRIAN_USER_DEMO_PASSWORD=demo123
        """
        # Normalize username
        name = username.split("@")[0].upper().replace(" ", "_").replace("-", "_")
        env_key = f"MINDRIAN_USER_{name}_PASSWORD"
        expected_password = os.getenv(env_key)

        # Also check for a default demo user (password MUST be set via env var)
        if not expected_password and username.lower() == "demo":
            expected_password = os.getenv("MINDRIAN_DEMO_PASSWORD")

        if expected_password and password == expected_password:
            logger.info(f"[AUTH] Simple auth succeeded: {username}")
            return cl.User(
                identifier=username,
                metadata={
                    "email": f"{username}@mindrian.local",
                    "provider": "simple_password",
                    "role": "authenticated",
                }
            )

        return None

    print("[AUTH] Simple password authentication ENABLED (env-based)")
else:
    print("[AUTH] No authentication configured - anonymous access allowed")


# === Header Authentication (JWT Validation) ===
# For API clients that send Supabase JWT in Authorization header
if SUPABASE_AUTH_ENABLED:
    @cl.header_auth_callback
    def supabase_header_auth(headers: dict) -> Optional[cl.User]:
        """
        Validate Supabase JWT tokens from Authorization header.
        Enables API access and programmatic integrations.

        Expected header: Authorization: Bearer <supabase_jwt_token>
        """
        auth_header = headers.get("Authorization", "").strip()

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        payload = validate_supabase_jwt(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            return None

        logger.info(f"[AUTH] JWT authenticated: {email or user_id}")

        return cl.User(
            identifier=user_id,
            metadata={
                "email": email,
                "provider": "supabase_jwt",
                "role": payload.get("role", "authenticated"),
            }
        )

    print("[AUTH] Supabase JWT header authentication ENABLED")


# === OAuth Authentication (Google/GitHub via Supabase) ===
# When using Supabase Auth, OAuth is handled by Supabase, not Chainlit directly.
# Users go to Supabase OAuth flow, get JWT, then use header auth.
# However, we can still support Chainlit OAuth as a fallback.

OAUTH_ENABLED = bool(
    os.getenv("OAUTH_GOOGLE_CLIENT_ID") or os.getenv("OAUTH_GITHUB_CLIENT_ID")
)

if OAUTH_ENABLED:
    @cl.oauth_callback
    def oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: dict,
        default_user: cl.User
    ) -> Optional[cl.User]:
        """Handle OAuth callback from Google or GitHub."""
        user_id = default_user.identifier
        logger.info(f"[AUTH] OAuth user via {provider_id}: {user_id}")

        if provider_id == "google":
            email = raw_user_data.get("email", "")
            name = raw_user_data.get("name", user_id)
            picture = raw_user_data.get("picture", "")
            return cl.User(
                identifier=email or user_id,
                metadata={
                    "name": name,
                    "image": picture,
                    "provider": "google",
                    "email": email,
                }
            )
        elif provider_id == "github":
            login = raw_user_data.get("login", user_id)
            name = raw_user_data.get("name") or login
            email = raw_user_data.get("email", "")
            avatar = raw_user_data.get("avatar_url", "")
            return cl.User(
                identifier=email or login,
                metadata={
                    "name": name,
                    "image": avatar,
                    "provider": "github",
                    "email": email,
                }
            )

        return default_user

    print("[AUTH] OAuth (Google/GitHub) ENABLED")


# === Stop Event for Cancellation ===
stop_events: Dict[str, asyncio.Event] = {}

# === Resume Welcome Guard ===
# Module-level set prevents "Welcome back!" spam on WebSocket reconnects
_resumed_threads: set = set()

# === Extended Thinking UI ===
# Captures and visualizes LLM reasoning steps

async def show_thinking_panel(bot_id: str, steps: list, methodology: str = None):
    """
    Display thinking panel with reasoning steps.

    Args:
        bot_id: Current bot identifier
        steps: List of {"name": str, "status": str, "output": str, "icon": str}
        methodology: Optional methodology name to display
    """
    bot_titles = {
        "lawrence": "Lawrence's Thinking",
        "larry_playground": "Larry's Analysis",
        "tta": "Trend Analysis",
        "jtbd": "Job Analysis",
        "scurve": "Timing Analysis",
        "redteam": "Attack Analysis",
        "ackoff": "DIKW Analysis",
        "scenario": "Scenario Analysis",
        "beautiful_question": "Question Analysis",
        "nested_hierarchies": "Systems Analysis",
        "validation": "Validation Analysis",
        "bono": "Hat Analysis",
        "knowns": "Uncertainty Analysis",
        "domain": "Domain Analysis",
        "investment": "Investment Analysis",
        "grading": "Assessment Analysis",
    }
    title = bot_titles.get(bot_id, "Thinking")

    # Create custom element for thinking panel
    thinking_element = cl.CustomElement(
        name="ThinkingPanel",
        props={
            "steps": steps,
            "title": title,
            "botId": bot_id,
            "methodology": methodology,
            "collapsed": False,
        },
        display="inline"
    )
    return thinking_element


# === PWS-Style Thinking Streamer ===
# Streams Larry-style thinking tokens while background work happens

PWS_THINKING_TOKENS = [
    # Discovery / unpacking
    "unpacking...", "digging in...", "following threads...", "connecting dots...",
    "mapping terrain...", "scanning landscape...", "tracing patterns...",
    # PWS methodology concepts
    "what's the real job here...", "checking assumptions...", "where's the bottleneck...",
    "trending this forward...", "what breaks first...", "who cares most...",
    "what's the reverse salient...", "where on the curve...", "DIKW check...",
    # Analytical thinking
    "hypothesizing...", "stress-testing...", "validating...", "synthesizing...",
    "cross-referencing...", "contextualizing...", "reframing...", "inverting...",
    # Engagement / curiosity
    "interesting angle...", "hmm, this connects to...", "worth exploring...",
    "there's something here...", "the real question is...", "let me think...",
    # Progress signals
    "almost there...", "coming together...", "crystallizing...", "emerging picture...",
]

async def stream_thinking_while_processing(
    msg: "cl.Message",
    blocking_func,
    *args,
    color: str = "#f59e0b",  # Amber/orange like Claude Code
    interval: float = 0.4,
    **kwargs
):
    """
    Run a blocking function in background while streaming PWS thinking tokens.

    Creates Claude Code-like "sizzeling... codifying..." UX but with
    Larry/PWS methodology vocabulary.

    Args:
        msg: Chainlit message to stream tokens to
        blocking_func: Synchronous function to run
        *args: Args for blocking_func
        color: Token text color (default amber)
        interval: Seconds between tokens
        **kwargs: Kwargs for blocking_func

    Returns:
        Result of blocking_func

    Example:
        content, metadata = await stream_thinking_while_processing(
            status_msg,
            process_uploaded_file,
            file_path, file_name
        )
    """
    import asyncio
    import random
    import concurrent.futures

    # Run blocking function in thread pool
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    # Start the blocking work
    future = loop.run_in_executor(executor, lambda: blocking_func(*args, **kwargs))

    # Stream thinking tokens while waiting
    tokens_used = set()
    try:
        while not future.done():
            # Pick a random unused token (or reuse if exhausted)
            available = [t for t in PWS_THINKING_TOKENS if t not in tokens_used]
            if not available:
                tokens_used.clear()
                available = PWS_THINKING_TOKENS

            token = random.choice(available)
            tokens_used.add(token)

            # Stream with styling (markdown italic + color hint)
            await msg.stream_token(f"*{token}* ")
            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        future.cancel()
        raise

    # Get result
    result = await future
    executor.shutdown(wait=False)

    # Clear line and show completion
    await msg.stream_token("\n")

    return result


async def capture_reasoning_steps(user_message: str, bot_id: str, history: list = None) -> list:
    """
    LangGraph-powered sequential thinking pipeline.

    Uses real AI analysis to:
    1. Understand message type (question/statement/request/emotion)
    2. Detect hidden assumptions in the user's thinking
    3. Check for premature solution-jumping
    4. Identify relevant PWS frameworks
    5. Synthesize an analysis strategy

    Returns list of thinking steps for the ThinkingPanel.
    """
    try:
        # Use LangGraph sequential thinking pipeline
        from intelligence.pipelines.sequential_thinking import get_thinking_steps_sync

        steps = await get_thinking_steps_sync(
            message=user_message,
            bot_id=bot_id,
            history=history or [],
        )
        return steps

    except Exception as e:
        # Fallback to simple pattern-based analysis if pipeline fails
        logger.warning(f"Sequential thinking pipeline failed, using fallback: {e}")

        steps = []

        # Step 1: Understand the question
        steps.append({
            "name": "Understanding the question",
            "status": "complete",
            "icon": "🔍",
            "output": f"User is asking about: {user_message[:100]}..."
        })

        # Step 2: Check for assumptions (quick pattern match)
        assumption_patterns = ["assume", "think", "believe", "should", "must", "obviously", "clearly"]
        has_assumptions = any(p in user_message.lower() for p in assumption_patterns)
        if has_assumptions:
            steps.append({
                "name": "Detecting assumptions",
                "status": "complete",
                "icon": "⚠️",
                "output": "Found assumption language - will probe for validation"
            })

        # Step 3: Check for solution-jumping
        solution_patterns = ["we should", "let's build", "the solution is", "i want to create", "my idea is"]
        has_solution_jump = any(p in user_message.lower() for p in solution_patterns)
        if has_solution_jump:
            steps.append({
                "name": "Checking problem definition",
                "status": "complete",
                "icon": "🎯",
                "output": "Solution language detected - will redirect to problem first"
            })

        # Step 4: Select methodology
        methodology_map = {
            "tta": "Trending to the Absurd",
            "jtbd": "Jobs to Be Done",
            "scurve": "S-Curve Analysis",
            "redteam": "Red Team Challenge",
            "ackoff": "DIKW Pyramid",
            "scenario": "Scenario Planning",
            "beautiful_question": "Beautiful Questions",
        }
        if bot_id in methodology_map:
            steps.append({
                "name": f"Applying {methodology_map[bot_id]}",
                "status": "active",
                "icon": "📚",
                "output": None
            })
        else:
            steps.append({
                "name": "Formulating PWS response",
                "status": "active",
                "icon": "💭",
                "output": None
            })

        return steps


# === Context Preservation for Profile Switching ===
# Store conversation history by user/thread to persist across bot switches
context_store: Dict[str, Dict[str, Any]] = {}


async def _persist_context_async(context_key: str):
    """Write-through: persist context_store entry to Supabase (fire-and-forget)."""
    data = context_store.get(context_key)
    if not data:
        return
    try:
        from utils.context_persistence import save_cross_bot_context
        bot_id = data.get("bot_id", "lawrence")
        await save_cross_bot_context(
            user_key=context_key,
            history=data.get("history", []),
            bot_id=bot_id,
            bot_name=BOTS.get(bot_id, {}).get("name", bot_id),
            phases=data.get("phases", []),
            current_phase=data.get("current_phase", 0),
            excluded_topics=data.get("excluded_topics", []),
        )
    except Exception as e:
        logger.debug(f"[PERSIST] Background persist failed for {context_key}: {e}")


# === PWS Consultant State Management ===
# LangGraph-style TypedDict state with context_store integration
try:
    from utils.pws_state import (
        init_pws_state,
        get_pws_state,
        set_pws_state,
        update_pws_state,
        set_context_store,
        sync_pws_to_context_store,
        restore_pws_from_context_store,
        CapturedPWSContext,
        run_background_task_with_context,
        transition_stage,
        persist_pws_state_to_supabase,
        is_stage,
        get_stage,
        increment_turn_count,
    )
    # Inject context_store for cross-bot persistence
    set_context_store(context_store)
    PWS_STATE_ENABLED = True
    print("[PWS_STATE] Formal state management enabled (LangGraph-style)")
except ImportError as e:
    PWS_STATE_ENABLED = False
    print(f"[PWS_STATE] State management not available: {e}")

# === PWS Validation Middleware (Red Team Pattern) ===
# AGENTS.md pattern: Cross-cutting validation at key transitions
try:
    from utils.pws_validation import (
        PWSValidationMiddleware,
        validate_pws_response,
        should_validate,
        format_validation_message,
    )
    PWS_VALIDATION_ENABLED = True
    print("[PWS_VALIDATION] Red Team middleware enabled")
except ImportError as e:
    PWS_VALIDATION_ENABLED = False
    print(f"[PWS_VALIDATION] Validation middleware not available: {e}")

# === Two-Stage Classifier (Cynefin + PWS) ===
# Quick win from AGENTS.md architecture analysis
try:
    from protocols.classifier import classify, Classification, get_routing_recommendation
    TWO_STAGE_CLASSIFIER_ENABLED = True
    print("[CLASSIFIER] Two-stage Cynefin + PWS classifier enabled")
except ImportError as e:
    TWO_STAGE_CLASSIFIER_ENABLED = False
    print(f"[CLASSIFIER] Two-stage classifier not available: {e}")

# === Topic-Aware Thread System ===
# Fixes context-mixing bug by tracking conversations by topic, not just by user
try:
    from utils.conversation_threads import (
        get_or_create_thread,
        get_thread_for_topic,
        save_thread_context,
        get_active_threads,
        get_context_for_continue,
        get_most_recent_thread,
        extract_topic_keywords,
        migrate_from_context_store,
    )
    THREAD_SYSTEM_ENABLED = True
except ImportError:
    THREAD_SYSTEM_ENABLED = False

# === Agent Suggestion Keywords ===
# Maps keywords/phrases to suggested agents
AGENT_TRIGGERS = {
    "tta": {
        "keywords": ["trend", "future", "extrapolate", "absurd", "emerging", "disruption", "10 years", "what if"],
        "description": "Explore future trends"
    },
    "jtbd": {
        "keywords": ["customer", "hire", "job", "struggling", "switch", "why do people", "motivation", "emotional"],
        "description": "Understand customer jobs"
    },
    "scurve": {
        "keywords": ["technology", "timing", "too early", "too late", "adoption", "s-curve", "dominant design", "era of ferment"],
        "description": "Analyze technology timing"
    },
    "redteam": {
        "keywords": ["assumption", "risk", "fail", "challenge", "devil's advocate", "what could go wrong", "attack", "critique"],
        "description": "Stress-test your idea"
    },
    "ackoff": {
        "keywords": ["validate", "data", "wisdom", "dikw", "evidence", "ground truth", "pyramid", "understand why"],
        "description": "Validate with DIKW"
    },
    "bono": {
        "keywords": ["six hats", "thinking hats", "minto", "pyramid", "expert panel", "parallel thinking", "perspectives", "white hat", "black hat"],
        "description": "Six Hats + Minto analysis"
    },
    "knowns": {
        "keywords": ["rumsfeld", "unknown unknowns", "blind spots", "knowledge gaps", "what don't we know", "uncertainty", "risk mapping"],
        "description": "Map unknowns & blind spots"
    },
    "nested_hierarchies": {
        "keywords": ["hierarchy", "system", "leverage point", "reverse salient", "constraint", "cascade", "herbert simon", "donella meadows", "thomas hughes", "component", "architecture", "levels"],
        "description": "Multi-level systems analysis"
    },
    "domain": {
        "keywords": ["domain selection", "choose domain", "pick domain", "domain candidate", "interest knowledge access", "where to innovate", "innovation territory", "domain statement"],
        "description": "Domain Selection Workshop"
    },
    "investment": {
        "keywords": ["ten questions", "investment thesis", "startup", "funding", "valuation", "due diligence", "invest", "evaluation"],
        "description": "PWS Investment analysis"
    },
    "scenario": {
        "keywords": ["scenario", "futures", "uncertainty", "2x2 matrix", "shell oil", "presentism", "driving forces", "multiple futures", "plausible futures", "strategic planning"],
        "description": "Multiple plausible futures"
    },
    "validation": {
        "keywords": ["validate", "multi-perspective", "six hats", "evidence-based", "stress test", "parallel thinking", "hat analysis", "de bono", "ibm case", "abb case", "validation report", "challenge assumptions"],
        "description": "Multi-Perspective Validation"
    },
    "beautiful_question": {
        "keywords": ["beautiful question", "warren berger", "why what if how", "five whys", "root cause", "what if", "how might we", "hmw", "assumption challenge", "constraint removal", "vuja de", "questioning"],
        "description": "WHY → WHAT IF → HOW questioning"
    },
    "pws_consultant": {
        "keywords": ["diagnose", "classify", "problem type", "what kind of problem", "consultant", "structured help",
                      "which framework", "not sure where to start", "need guidance", "confused about approach",
                      "expert panel", "domain experts"],
        "description": "Structured problem diagnosis & guided consulting"
    },
    "pws_navigator": {
        "keywords": ["cross-domain", "bridge", "unexpected connection", "different field", "analogy",
                      "combine domains", "interdisciplinary", "cross-pollinate", "navigate knowledge",
                      "knowledge graph", "explore domains", "innovation bridge"],
        "description": "Cross-domain bridge detection & innovation discovery"
    },
}

# === Data Persistence Setup with Native Feedback System ===
# Using MindrianDataLayer which extends SQLAlchemyDataLayer with:
# - Automatic feedback collection (thumbs up/down UI on all AI messages)
# - CSV export for analytics
# - Supabase storage integration
#
# IMPORTANT: We use @cl.data_layer decorator to ensure the data layer is
# registered BEFORE Chainlit's routes are created. This fixes the /threads 404 issue.
if DATABASE_URL:
    try:
        from utils.data_layer import create_mindrian_data_layer

        # Create the data layer instance
        _mindrian_data_layer = create_mindrian_data_layer(DATABASE_URL)

        if _mindrian_data_layer:
            # Use the decorator pattern to register with Chainlit's route system
            @cl.data_layer
            def get_data_layer():
                return _mindrian_data_layer

            print("✅ Data persistence enabled with MindrianDataLayer (PostgreSQL + Feedback Analytics)")
        else:
            print("⚠️ Data layer creation failed - threads/persistence disabled")

    except Exception as e:
        print(f"⚠️ Data persistence disabled: {e}")
        import traceback
        traceback.print_exc()
else:
    print("ℹ️ Data persistence disabled (no DATABASE_URL)")

# === System Prompts ===
from prompts import (
    LARRY_RAG_SYSTEM_PROMPT,
    TTA_WORKSHOP_PROMPT,
    JTBD_WORKSHOP_PROMPT,
    SCURVE_WORKSHOP_PROMPT,
    REDTEAM_PROMPT,
    ACKOFF_WORKSHOP_PROMPT,
    BONO_MASTER_PROMPT,
    KNOWN_UNKNOWNS_PROMPT,
    NESTED_HIERARCHIES_PROMPT,
    DOMAIN_EXPLORER_PROMPT,
    PWS_INVESTMENT_PROMPT,
    SCENARIO_ANALYSIS_PROMPT,
    MULTI_PERSPECTIVE_VALIDATION_PROMPT,
    BEAUTIFUL_QUESTION_PROMPT,
    GRADING_AGENT_PROMPT,  # Problem Discovery Grading Agent
    CV_EXTRACTION_PROMPT,
    DOMAIN_GENERATION_PROMPT,
    DOMAIN_SCORING_PROMPT,
    RESEARCH_EXTRACTION_PROMPT,
    RESEARCH_QUESTION_EXPANSION_PROMPT,
    DOMAIN_GENERATION_FROM_RESEARCH_PROMPT,
    RESEARCH_DOMAIN_SCORING_PROMPT,
    RESEARCH_TRANSLATION_PROMPT,
    # Minto Grading
    MINTO_GRADING_PROMPT,
    MINTO_WELCOME,
    POST_GRADING_LAWRENCE_CONTEXT,
    calculate_minto_score,
    get_minto_letter_grade,
    # PWS Consultant
    PWS_CONSULTANT_PROMPT,
    PWS_CONSULTANT_PHASES,
    PWS_PROBLEM_TYPES,
    PWS_DIAGNOSTIC_QUESTIONS,
    PWS_WORKSHOPS,
    PWS_SELECTION_CRITERIA,
    PWS_VALIDATION_COMPASS,
    pws_score_diagnostic,
    pws_build_diagnostic_context,
    pws_get_recommended_tools,
    pws_get_recommended_agents,
    pws_build_expert_specs,
)

# === RAG Cache Support ===
try:
    from utils.gemini_rag import get_cache_name
    RAG_ENABLED = True
except ImportError:
    RAG_ENABLED = False
    def get_cache_name(workshop_id):
        return None

# === File Search Store (Gemini RAG) ===
# PWS Knowledge Base with Tier 1 (Core), Tier 2 (Workshop Materials), Tier 3 (Case Studies)
FILE_SEARCH_STORE = "fileSearchStores/pwsknowledgebase-a4rnz3u41lsn"
FILE_SEARCH_ENABLED = True  # Set to False to disable File Search

# === Workshop Phase Definitions ===
WORKSHOP_PHASES = {
    "tta": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Domain & Trends", "status": "pending"},
        {"name": "Deep Research", "status": "pending"},
        {"name": "Absurd Extrapolation", "status": "pending"},
        {"name": "Problem Hunting", "status": "pending"},
        {"name": "Opportunity Validation", "status": "pending"},
        {"name": "Action Planning", "status": "pending"},
        {"name": "Reflection", "status": "pending"},
    ],
    "jtbd": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Struggling Moment", "status": "pending"},
        {"name": "Functional Job", "status": "pending"},
        {"name": "Emotional Job", "status": "pending"},
        {"name": "Social Job", "status": "pending"},
        {"name": "Competing Solutions", "status": "pending"},
        {"name": "Job Statement", "status": "pending"},
    ],
    "scurve": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Technology Identification", "status": "pending"},
        {"name": "Era Assessment", "status": "pending"},
        {"name": "Evidence Gathering", "status": "pending"},
        {"name": "Ecosystem Readiness", "status": "pending"},
        {"name": "Timing Decision", "status": "pending"},
    ],
    "redteam": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Assumption Extraction", "status": "pending"},
        {"name": "Assumption Ranking", "status": "pending"},
        {"name": "Attack Mode", "status": "pending"},
        {"name": "Competition & Alternatives", "status": "pending"},
        {"name": "Failure Modes", "status": "pending"},
        {"name": "Strengthening", "status": "pending"},
    ],
    "ackoff": [
        {"name": "Team Onboarding", "status": "ready"},
        {"name": "Direction Choice", "status": "pending"},
        {"name": "Data Level", "status": "pending"},
        {"name": "Information Level", "status": "pending"},
        {"name": "Knowledge Level", "status": "pending"},
        {"name": "Understanding Level", "status": "pending"},
        {"name": "Wisdom Level", "status": "pending"},
        {"name": "Validation & Action", "status": "pending"},
    ],
    "bono": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Persona Generation", "status": "pending"},
        {"name": "White Hat Analysis", "status": "pending"},
        {"name": "Red Hat Analysis", "status": "pending"},
        {"name": "Black Hat Analysis", "status": "pending"},
        {"name": "Yellow Hat Analysis", "status": "pending"},
        {"name": "Green Hat Analysis", "status": "pending"},
        {"name": "Blue Hat Synthesis", "status": "pending"},
        {"name": "Panel Discussion", "status": "pending"},
        {"name": "Breakthrough Recommendations", "status": "pending"},
    ],
    "knowns": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Context Gathering", "status": "pending"},
        {"name": "Known Knowns Audit", "status": "pending"},
        {"name": "Known Unknowns Mapping", "status": "pending"},
        {"name": "Unknown Knowns Surfacing", "status": "pending"},
        {"name": "Unknown Unknowns Discovery", "status": "pending"},
        {"name": "Risk Assessment", "status": "pending"},
        {"name": "Action Planning", "status": "pending"},
    ],
    "nested_hierarchies": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Map the Hierarchy", "status": "pending"},
        {"name": "Find Reverse Salients", "status": "pending"},
        {"name": "Locate Leverage Points", "status": "pending"},
        {"name": "Design the Intervention", "status": "pending"},
    ],
    "domain": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Domain Generation", "status": "pending"},
        {"name": "Domain Evaluation", "status": "pending"},
        {"name": "Domain Validation", "status": "pending"},
        {"name": "Domain Finalization", "status": "pending"},
    ],
    "investment": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Scope Definition", "status": "pending"},
        {"name": "Ten Questions Part 1", "status": "pending"},
        {"name": "Ten Questions Part 2", "status": "pending"},
        {"name": "Go/No-Go Decision", "status": "pending"},
        {"name": "Thesis: Business & Team", "status": "pending"},
        {"name": "Thesis: Market & GTM", "status": "pending"},
        {"name": "Thesis: Competition & Value", "status": "pending"},
        {"name": "Adversarial Review", "status": "pending"},
        {"name": "Final Recommendation", "status": "pending"},
    ],
    "scenario": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Domain & Driving Forces", "status": "pending"},
        {"name": "Uncertainty Assessment", "status": "pending"},
        {"name": "Scenario Matrix (2×2)", "status": "pending"},
        {"name": "Scenario Narratives", "status": "pending"},
        {"name": "Synthesis & Implications", "status": "pending"},
    ],
    "validation": [
        {"name": "Introduction", "status": "ready"},
        {"name": "Domain Extraction", "status": "pending"},
        {"name": "Persona Construction", "status": "pending"},
        {"name": "White Hat Research", "status": "pending"},
        {"name": "Red Hat Research", "status": "pending"},
        {"name": "Black Hat Research", "status": "pending"},
        {"name": "Yellow Hat Research", "status": "pending"},
        {"name": "Green Hat Research", "status": "pending"},
        {"name": "Blue Hat Synthesis", "status": "pending"},
        {"name": "Structured Debate", "status": "pending"},
        {"name": "Validation Report", "status": "pending"},
    ],
    "beautiful_question": [
        {"name": "Introduction", "status": "ready"},
        {"name": "WHY: Five Whys", "status": "pending"},
        {"name": "WHY: Assumption Mapping", "status": "pending"},
        {"name": "WHY: Vuja De", "status": "pending"},
        {"name": "WHAT IF: Constraint Removal", "status": "pending"},
        {"name": "WHAT IF: Thinking Wrong", "status": "pending"},
        {"name": "WHAT IF: Cross-Domain", "status": "pending"},
        {"name": "HOW: HMW Statements", "status": "pending"},
        {"name": "HOW: Rapid Prototyping", "status": "pending"},
        {"name": "HOW: MVP Design", "status": "pending"},
        {"name": "Action Plan", "status": "pending"},
    ],
    # pws_consultant: REMOVED — uses CONSULTANT_STAGES state machine, not workshop phases
    # See prompts/pws_consultant.py PWS_CONSULTANT_PHASES for documentation only
    # Note: grading is one-shot, not a phased workshop
    "macro_changes": [
        {"name": "Domain Selection", "status": "ready"},
        {"name": "Macro-Changes Mapping", "status": "pending"},
        {"name": "PEST Systems Analysis", "status": "pending"},
        {"name": "Destruction & Discontinuity", "status": "pending"},
        {"name": "Multi-Order Consequences", "status": "pending"},
        {"name": "Problems Worth Solving", "status": "pending"},
    ],
    "dominant_designs": [
        {"name": "Domain Selection", "status": "ready"},
        {"name": "Dominant Design Identification", "status": "pending"},
        {"name": "Discontinuity Analysis", "status": "pending"},
        {"name": "S-Curve & Limits Analysis", "status": "pending"},
        {"name": "Destruction & Opportunity", "status": "pending"},
        {"name": "New Design & PWS", "status": "pending"},
    ],
    "user_needs": [
        {"name": "Domain Selection", "status": "ready"},
        {"name": "Process Identification & Mapping", "status": "pending"},
        {"name": "Importance-Satisfaction Rating", "status": "pending"},
        {"name": "Gap Analysis & Root Causes", "status": "pending"},
        {"name": "Barrier Identification", "status": "pending"},
        {"name": "Opportunity Synthesis", "status": "pending"},
    ],
}

# === PWS Consultant Stage Machine ===
# Deterministic stage transitions driven by action callbacks, NOT LLM-detected phases
CONSULTANT_STAGES = {
    "intro": {"name": "Challenge Description", "next": "diagnostic", "trigger": "submit_challenge"},
    "diagnostic": {"name": "Problem Diagnostic", "next": "consulting", "trigger": "diagnostic_answer"},
    "consulting": {"name": "Guided Consulting", "next": None, "trigger": None},
}

# === Bot Configurations ===
BOTS = {
    "lawrence": {
        "name": "Lawrence",
        "icon": "/public/icons/larry.svg",
        "emoji": "🧠",
        "description": "Your PWS thinking partner — focused and concise",
        "system_prompt": LARRY_RAG_SYSTEM_PROMPT,
        "has_phases": False,
        "simple_mode": True,
        "welcome": """🧠 **What are you working on?**"""
    },
    "larry_playground": {
        "name": "Larry Playground",
        "icon": "/public/icons/larry.svg",
        "emoji": "🔬",
        "description": "Full-featured PWS lab — all tools, research, multi-agent analysis",
        "system_prompt": LARRY_RAG_SYSTEM_PROMPT,
        "has_phases": False,
        "simple_mode": False,
        "welcome": """🔬 **Welcome to the Playground!**

Think of this as your innovation laboratory. You have access to every thinking tool, research capability, and specialist AI available in Mindrian.

It's like having a team of consultants, researchers, and devil's advocates on call — ready to dig deep, challenge assumptions, and help you see what you're missing.

**What challenge are you wrestling with?**"""
    },
    "tta": {
        "name": "Trending to the Absurd",
        "icon": "/public/icons/tta.svg",
        "emoji": "🔮",
        "description": "Guided workshop: escape presentism, find future problems",
        "system_prompt": TTA_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """🔮 **Trending to the Absurd Workshop**

Hello, I'm Larry Aronhime.

Before we dive into Trending to the Absurd, I need to understand who I'm working with.

**Tell me about yourself and your team:**

1️⃣ **Who's on this journey?**
   - Are you working alone or with a team?
   - What are your backgrounds?

2️⃣ **What's your starting point?**
   - Do you already have a domain or industry in mind?
   - Have you done any prior PWS work?

3️⃣ **What's driving this exploration?**
   - Looking for new market opportunities?
   - Anticipating disruption?
   - Exploring problems for a new venture?

I'm listening."""
    },
    "jtbd": {
        "name": "Jobs to Be Done",
        "icon": "/public/icons/jtbd.svg",
        "emoji": "🎯",
        "description": "Workshop: discover what customers really hire products for",
        "system_prompt": JTBD_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """🎯 **Jobs to Be Done Workshop**

Hello, I'm Larry.

Jobs to Be Done is deceptively simple — but when you really get it, you'll never look at your customers the same way.

People don't buy products — they "hire" them to make progress in their lives. That job has three dimensions:

- **Functional:** The practical task
- **Emotional:** How they want to feel
- **Social:** How they want to be perceived

**What product or service are you exploring?** Tell me about the customers you're trying to understand."""
    },
    "scurve": {
        "name": "S-Curve Analysis",
        "icon": "/public/icons/scurve.svg",
        "emoji": "📈",
        "description": "Workshop: analyze technology timing and disruption",
        "system_prompt": SCURVE_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """📈 **S-Curve Analysis Workshop**

Hello, I'm Larry.

S-Curve Analysis is about reading the clock on technology evolution.

Every technology follows an S-curve: slow start, rapid growth, eventual plateau. Get the timing right, and you ride a wave. Get it wrong, and you're either too early (running out of cash) or too late (fighting giants).

- **Era of Ferment:** Many approaches compete, no standard yet
- **Dominant Design:** Industry converges, optimization begins
- **Discontinuity:** New curve emerges, disruption happens

**What technology or industry are you analyzing?**"""
    },
    "redteam": {
        "name": "Red Teaming",
        "icon": "/public/icons/redteam.svg",
        "emoji": "😈",
        "description": "Devil's advocate: stress-test your assumptions",
        "system_prompt": REDTEAM_PROMPT,
        "has_phases": True,
        "welcome": """😈 **Red Teaming Session**

I'm Larry, and right now I'm your devil's advocate.

My job is to find the holes in your thinking before the market does. I'm going to challenge your assumptions, stress-test your logic, and look for the fatal flaw.

This isn't about being negative — it's about making your idea bulletproof.

**What idea, plan, or assumption do you want me to attack?**"""
    },
    "ackoff": {
        "name": "Ackoff's Pyramid (DIKW)",
        "icon": "/public/icons/ackoff.svg",
        "emoji": "🔺",
        "description": "Workshop: Climb the DIKW pyramid to validate understanding",
        "system_prompt": ACKOFF_WORKSHOP_PROMPT,
        "has_phases": True,
        "welcome": """🔺 **Ackoff's Pyramid Workshop**
### From Data to Wisdom — Or Catch Yourself Climbing the Wrong Ladder

Hello, I'm Larry Aronhime.

Here's a common trap: People think they have knowledge when they only have information. They think they have wisdom when they only have opinions.

Ackoff's Pyramid is like a ladder from raw data at the bottom to genuine wisdom at the top. Most people are stuck somewhere in the middle, thinking they're higher than they are.

**We can work two directions:**
- **Climb up** — Build from data to actionable understanding
- **Climb down** — Test whether your "brilliant insight" is actually grounded in reality

**Who am I working with today, and what's the challenge?**

Tell me a bit about yourself and what you're trying to figure out."""
    },
    "bono": {
        "name": "BONO Master",
        "icon": "/public/icons/bono.svg",
        "emoji": "🎭",
        "description": "Workshop: Six Thinking Hats + Minto Pyramid synthesis",
        "system_prompt": BONO_MASTER_PROMPT,
        "has_phases": True,
        "welcome": """🎭 **BONO Master Workshop**
### See Your Challenge Through Six Different Lenses

Hello, I'm your strategic thinking facilitator.

Imagine assembling a panel of experts — each wearing a different "thinking hat" — to examine your challenge from every angle. One focuses purely on facts, another on gut feelings, one plays devil's advocate, another looks for possibilities... and so on.

This is how companies like IBM cut meeting time by 75% while making better decisions. Instead of everyone arguing from their default position, we think in parallel — one lens at a time.

**What challenge or decision do you want this expert panel to examine?**

Tell me what's on your mind, and I'll assemble the right specialists for your situation."""
    },
    "knowns": {
        "name": "Known-Unknowns",
        "icon": "/public/icons/knowns.svg",
        "emoji": "❓",
        "description": "Workshop: Rumsfeld Matrix for blind spot discovery",
        "system_prompt": KNOWN_UNKNOWNS_PROMPT,
        "has_phases": True,
        "welcome": """🎯 **Known-Unknowns Analyzer**
### Rumsfeld Matrix + Blind Spot Discovery

Hello, I'm your uncertainty mapper.

I help you systematically categorize what you know and don't know:

- ✅ **Known Knowns**: Facts you're confident about
- ❓ **Known Unknowns**: Questions you know to ask
- 💡 **Unknown Knowns**: Tacit expertise not yet surfaced
- ⚠️ **Unknown Unknowns**: Blind spots that could derail you

**What situation, decision, or plan do you want to map?**

We'll surface hidden assumptions and discover what you don't know you don't know."""
    },
    "nested_hierarchies": {
        "name": "Nested Hierarchies",
        "icon": "/public/icons/hierarchy.svg",
        "emoji": "🏛️",
        "description": "Workshop: Multi-level systems analysis for finding leverage points",
        "system_prompt": NESTED_HIERARCHIES_PROMPT,
        "has_phases": True,
        "welcome": """🏛️ **Nested Hierarchies Workshop**
### Seeing the System Behind the Problem

Hello, I'm Larry Aronhime.

**Here's what most people miss:** They focus on parts when they should focus on patterns. They fix batteries when the constraint is in transmission. They redesign interfaces when the friction is in the business model.

Every problem exists within a **nested hierarchy of systems**. The most consequential innovations address **reverse salients**—the constraints that hold back entire system hierarchies.

We'll work through 4 phases:
1. **Map the Hierarchy** — See the full system stack (5+ levels)
2. **Find Reverse Salients** — Identify what's really constraining growth
3. **Locate Leverage Points** — Find where intervention cascades
4. **Design the Intervention** — Act at the right level

**What problem or opportunity are you exploring?**

Tell me about the component you're focused on—I'll help you see the system around it."""
    },
    "domain": {
        "name": "Domain Selection",
        "icon": "/public/icons/domain.svg",
        "emoji": "🧭",
        "description": "Workshop: Domain Selection — Choose where to innovate",
        "system_prompt": DOMAIN_EXPLORER_PROMPT,
        "has_phases": True,
        "welcome": """🧭 **Domain Selection Workshop**
### Find Your Innovation Territory

Hello, I'm Larry Aronhime.

**Here's what most people miss:** They think domain selection is a warm-up exercise. It's not. It's the foundation. Get it wrong, and no amount of creativity will save you.

We'll work through 4 phases:
1. **Generation** — Mine your experience for candidate domains
2. **Evaluation** — Score honestly on Interest, Knowledge, Access
3. **Validation** — Test with real research and stakeholder checks
4. **Finalization** — Craft your domain statement and action plan

You can also upload a **CV** or **research paper** to discover domains automatically.

**Where are you starting from?** Do you have candidates in mind, or are you starting fresh?"""
    },
    "investment": {
        "name": "PWS Investment",
        "icon": "/public/icons/investment.svg",
        "emoji": "💰",
        "description": "Workshop: Ten Questions + Investment Thesis evaluation",
        "system_prompt": PWS_INVESTMENT_PROMPT,
        "has_phases": True,
        "welcome": """💰 **Investment Analysis Workshop**
### Is This Worth Your Time and Money?

Hello, I'm your investment analyst.

Every investor has the same nightmare: falling in love with an idea and realizing too late it was fatally flawed. I help you avoid that by asking the questions that separate the winners from the wishful thinking.

Think of me as your skeptical but fair-minded partner who wants you to succeed — but won't let you fool yourself.

**What startup, opportunity, or investment are you considering?**

We'll pressure-test it together and see if it holds up."""
    },
    "scenario": {
        "name": "Scenario Analysis",
        "icon": "/public/icons/scenario.svg",
        "emoji": "🌐",
        "description": "Workshop: Navigate uncertainty with multiple plausible futures",
        "system_prompt": SCENARIO_ANALYSIS_PROMPT,
        "has_phases": True,
        "welcome": """🌐 **Scenario Analysis Workshop**
### Navigating Uncertainty to Find Problems Worth Solving

Hello, I'm Larry.

Here's a question that should make you uncomfortable: **What if everything you believe about the future is wrong—not because you're uninformed, but because you're trapped in the present?**

Scenario Analysis is your escape route from the prison of presentism. We won't predict the future—instead, we'll systematically imagine multiple plausible futures and discover what problems would matter in each.

This is how Shell survived the 1973 oil crisis when every other oil company was blindsided. It's how you can find problems worth solving that others can't see.

**To begin: What domain or industry do you want to explore, and what strategic question is driving your interest?**"""
    },
    "validation": {
        "name": "Multi-Perspective Validation",
        "icon": "/public/icons/validate.svg",
        "emoji": "🎯",
        "description": "Workshop: Validate ideas with domain-specific Six Thinking Hats + research",
        "system_prompt": MULTI_PERSPECTIVE_VALIDATION_PROMPT,
        "has_phases": True,
        "welcome": """🎯 **Validation Workshop**
### Put Your Idea Through the Wringer

Hello, I'm your validation specialist.

You know that feeling when you think your idea is brilliant, but something nags at you? *"What am I missing?"* That's what this workshop answers.

Think of it like a mock trial for your idea. I'll assemble a panel of perspectives — optimists, skeptics, data analysts, creative thinkers — and each will independently research and challenge your concept. No groupthink. No echo chambers. Just rigorous, multi-angle validation.

**What idea, strategy, or decision needs validation?**

The more context you give me about your situation, the sharper the analysis will be."""
    },
    "beautiful_question": {
        "name": "Beautiful Question",
        "icon": "/public/icons/explore.svg",
        "emoji": "❓",
        "description": "Workshop: WHY → WHAT IF → HOW breakthrough questioning methodology",
        "system_prompt": BEAUTIFUL_QUESTION_PROMPT,
        "has_phases": True,
        "welcome": """❓ **Beautiful Question Workshop**
### WHY → WHAT IF → HOW

Hello, I'm your Beautiful Question guide, based on Warren Berger's breakthrough methodology.

Most people jump to solutions before understanding problems. I'll help you ask better questions to find better answers.

**The Three Phases:**

🔴 **WHY Phase** — Stop and question
- Five Whys to find root causes
- Assumption mapping to surface hidden beliefs
- Vuja De to see familiar things freshly

🟡 **WHAT IF Phase** — Imagine possibilities
- Constraint removal to expand solution space
- Thinking Wrong to break patterns
- Cross-domain analogies for fresh approaches

🟢 **HOW Phase** — Move to action
- How Might We (HMW) statements
- Rapid prototyping and pretotyping
- MVP design with success metrics

**What challenge are you exploring?**

Tell me what problem you're trying to solve, and we'll start by questioning whether you're solving the right problem."""
    },
    "grading": {
        "name": "Problem Discovery Grading",
        "icon": "/public/icons/grading.svg",
        "emoji": "🎓",
        "description": "Grade student work on problem discovery and validation methodology",
        "system_prompt": GRADING_AGENT_PROMPT,
        "has_phases": False,  # One-shot grading, not a phased workshop
        "simple_mode": False,
        "welcome": """🎓 **Problem Discovery Grading**
### Did You Find a Real Problem Worth Solving?

Hello, I'm your grading assistant.

My job is simple: determine whether you've found a **real problem** that real people actually have. Not just an interesting idea. Not just something that sounds good on paper. A real problem, validated with real evidence.

I'll look at:
- Did you prove the problem exists? (This is most of the grade)
- Did you discover multiple problems before picking one?
- Did you use the right thinking tools?
- Did you find connections others might miss?

**Upload your work (PDF, DOCX, or TXT) or paste it directly.**

I'll give you honest feedback on where you nailed it and where you have gaps."""
    },
    "minto": {
        "name": "Minto Problem Discovery Grading",
        "icon": "/public/icons/grading.svg",
        "emoji": "📊",
        "description": "One-shot autonomous grading focused on problem reality validation",
        "system_prompt": MINTO_GRADING_PROMPT,
        "has_phases": False,  # One-shot grading, no phases
        "simple_mode": False,
        "welcome": MINTO_WELCOME
    },
    "pws_consultant": {
        "name": "PWS Consultant",
        "icon": "/public/icons/explore.svg",
        "emoji": "🩺",
        "description": "Structured problem diagnosis: classify your challenge, get targeted framework guidance with domain experts",
        "system_prompt": PWS_CONSULTANT_PROMPT,
        "has_phases": False,  # Uses CONSULTANT_STAGES state machine, not workshop phases
        "simple_mode": False,
        "welcome": """🩺 **PWS Consultant**
### Problems Before Solutions — Always.

Hello, I'm Larry Aronhime.

Most people jump to solutions too fast. Let's start where it matters — *with the problem itself*.

Here's how this works: You'll tell me about your challenge, I'll run a quick diagnostic to understand what kind of problem you're dealing with, and then we'll work through it together using exactly the right frameworks for your situation.

Along the way, I'll bring in domain-specific perspectives — think of them as colleagues with different expertise who can offer fresh angles on your challenge.

**What's the challenge you're wrestling with?**

Don't worry about being precise — that's what we'll work on together."""
    }
}

# === WAVE 5: Unified Registry Bridge ===
# Registry-generated BOTS/AGENT_TRIGGERS override inline definitions.
# This ensures new agents added to agent_definitions.py automatically appear everywhere.
try:
    from protocols.unified_registry import (
        generate_bots_dict as _gen_bots,
        generate_agent_triggers as _gen_triggers,
    )
    _registry_bots = _gen_bots()
    _registry_triggers = _gen_triggers()

    # Merge: registry values override inline values for matching keys;
    # inline values preserved for keys not in registry.
    for _k, _v in _registry_bots.items():
        BOTS[_k] = _v

    for _k, _v in _registry_triggers.items():
        AGENT_TRIGGERS[_k] = _v

    logger.info(f"[REGISTRY] Merged {len(_registry_bots)} bots, {len(_registry_triggers)} triggers from unified registry")
except ImportError as _reg_err:
    logger.debug(f"[REGISTRY] Unified registry not available: {_reg_err}")
except Exception as _reg_err:
    logger.warning(f"[REGISTRY] Bridge error (non-fatal): {_reg_err}")


def _get_phases_for_bot(bot_id: str) -> Optional[list]:
    """
    Get phases for a bot with auto-discovery fallback.
    Priority: 1. Self-describing (from prompt module), 2. Legacy WORKSHOP_PHASES dict
    """
    # Try self-describing phases first
    if PHASE_DISCOVERY_ENABLED:
        phases = get_phases_for_bot(bot_id)
        if phases:
            return phases

    # Fall back to legacy dict
    if bot_id in WORKSHOP_PHASES:
        return [p.copy() for p in WORKSHOP_PHASES[bot_id]]

    return None


async def create_workshop_roadmap(profile: str) -> None:
    """
    Create the WorkshopRoadmap custom element for phase visualization.

    This is the ONLY progress UI (TaskList fallback removed Feb 2026).
    """
    # Use auto-discovery with legacy fallback
    phases = _get_phases_for_bot(profile)
    if phases is None:
        return

    bot = BOTS.get(profile, BOTS.get("lawrence", {}))

    try:
        await create_or_update_roadmap(
            phases=phases,
            current_phase=0,
            bot_name=bot.get("name", "Workshop"),
            bot_icon=bot.get("icon", "🎯"),
            phase_context={}
        )
    except Exception as e:
        print(f"WorkshopRoadmap creation failed: {e}")


def get_core_action_buttons(
    include_example: bool = True,
    larry_context: dict = None
) -> list:
    """
    Build the core action buttons that should appear on most responses.

    This ensures consistency - after Research, Synthesize, Think, etc. complete,
    the user still has access to all core actions.

    Args:
        include_example: Whether to include the Example button
        larry_context: Optional dict with teachable moment analysis:
            - show_larry: bool (True to show button)
            - tooltip: str (custom tooltip if teachable moment detected)
            - highlight: bool (True to highlight button)

    Returns:
        List of cl.Action objects
    """
    actions = [
        cl.Action(
            name="deep_research",
            payload={"action": "research"},
            label="🔍 Research",
            tooltip="Search the web for relevant data and evidence",
        ),
        cl.Action(
            name="synthesize_conversation",
            payload={"action": "synthesize"},
            label="📥 Synthesize",
            tooltip="Summarize conversation: key insights, breakthroughs, next steps",
        ),
        cl.Action(
            name="think_through",
            payload={"action": "think"},
            label="🧠 Think",
            tooltip="Run a structured analysis: define the problem → list assumptions → find gaps → suggest next steps",
        ),
        cl.Action(
            name="map_ideas",
            payload={"action": "map"},
            label="📊 Visualize",
            tooltip="Auto-select best diagram type: mindmap, flowchart, quadrant, journey, or sequence",
        ),
        cl.Action(
            name="view_opportunities",
            payload={"action": "bank"},
            label="🏦 Opportunities",
            tooltip="View your saved opportunities bank",
        ),
        cl.Action(
            name="journey_status",
            payload={"action": "journey"},
            label="🧭 My Journey",
            tooltip="View your PWS learning journey: phases, insights, and progress",
        ),
        cl.Action(
            name="fork_conversation",
            payload={"action": "fork"},
            label="🍴 Fork",
            tooltip="Create a branch to explore an alternative direction",
        ),
        cl.Action(
            name="show_idea_canvas",
            payload={"action": "ideas"},
            label="💡 Ideas",
            tooltip="View and manage extracted ideas from this conversation",
        ),
        cl.Action(
            name="creative_leaps",
            payload={"action": "leaps"},
            label="🔗 Creative Leaps",
            tooltip="Find unexpected cross-domain connections for innovation (Granmoe method)",
        ),
        cl.Action(
            name="pws_navigate",
            payload={"action": "navigate"},
            label="🧭 PWS Navigator",
            tooltip="Discover cross-domain bridges and innovation opportunities using knowledge graph",
        ),
        cl.Action(
            name="converge_answer",
            payload={"action": "converge"},
            label="🎯 Give me your answer",
            tooltip="Stop exploring and give me a direct, synthesized answer to my question",
        ),
        cl.Action(
            name="assess_progress",
            payload={"action": "assess"},
            label="📋 Assess My Progress",
            tooltip="Get an AI-powered assessment of your understanding and progress",
        ),
    ]

    # Larry Teach Me button - contextual based on teachable moments
    larry_context = larry_context or {}
    show_larry = larry_context.get("show_larry", True)

    if show_larry:
        # Check if we detected a teachable moment (highlight the button)
        has_teachable_moment = larry_context.get("highlight", False)
        custom_tooltip = larry_context.get("tooltip")

        larry_label = "🎓✨ Larry teach me" if has_teachable_moment else "🎓 Larry teach me"
        larry_tooltip = custom_tooltip or "Get a cognitive intervention from Larry"

        actions.append(cl.Action(
            name="larry_teach_me",
            payload={"action": "teach"},
            label=larry_label,
            tooltip=larry_tooltip,
        ))

    if include_example:
        actions.append(cl.Action(
            name="show_example",
            payload={"action": "example"},
            label="📖 Example",
            tooltip="View a real-world example of this methodology",
        ))

    return actions


def get_pipeline_buttons(bot_id: str) -> list:
    """
    Get LangGraph pipeline buttons specific to the current bot.
    These enable advanced multi-step analysis workflows.
    """
    pipeline_buttons = {
        "bono": [
            cl.Action(
                name="run_bono_analysis",
                payload={"action": "bono"},
                label="🎭 Run Six Hats",
                tooltip="Run complete Six Thinking Hats + Lateral Thinking pipeline",
            ),
        ],
        "nested_hierarchies": [
            cl.Action(
                name="run_rs_discovery",
                payload={"action": "rs"},
                label="🔍 Find Reverse Salients",
                tooltip="Discover constraints holding back system hierarchies",
            ),
        ],
        "domain": [
            cl.Action(
                name="run_domain_discovery",
                payload={"action": "domain"},
                label="🌐 Discover Domains",
                tooltip="Run LangGraph domain discovery pipeline",
            ),
        ],
        "scenario": [
            cl.Action(
                name="run_oracle_prediction",
                payload={"action": "oracle"},
                label="🔮 Oracle Prediction",
                tooltip="Generate prediction market and research brief",
            ),
        ],
        "validation": [
            cl.Action(
                name="run_bono_analysis",
                payload={"action": "bono"},
                label="🎭 Multi-Perspective Hats",
                tooltip="Run Six Hats analysis for multi-perspective validation",
            ),
        ],
        "tta": [
            cl.Action(
                name="run_oracle_prediction",
                payload={"action": "oracle"},
                label="🔮 Oracle Prediction",
                tooltip="Generate prediction market for trend scenarios",
            ),
        ],
    }

    return pipeline_buttons.get(bot_id, [])


def get_phase_navigation_buttons(current_phase: int, total_phases: int, include_core: bool = True) -> list:
    """
    Build phase navigation buttons with optional core actions.

    Args:
        current_phase: 0-indexed current phase
        total_phases: Total number of phases
        include_core: Whether to include Research/Synthesize/Think buttons

    Returns:
        List of cl.Action objects for phase navigation
    """
    actions = []

    # Back button (if not on first phase)
    if current_phase > 0:
        actions.append(cl.Action(
            name="prev_phase",
            payload={},
            label="← Back",
            tooltip="Return to the previous phase",
        ))

    # Next button (if not on last phase)
    if current_phase < total_phases - 1:
        actions.append(cl.Action(
            name="next_phase",
            payload={},
            label="Next Phase →",
            tooltip="Advance to the next phase",
        ))

    # Add core action buttons
    if include_core:
        actions.extend([
            cl.Action(name="deep_research", payload={}, label="🔍 Research"),
            cl.Action(name="show_example", payload={}, label="📖 Example"),
        ])

    return actions


async def create_or_update_roadmap(
    phases: list,
    current_phase: int,
    bot_name: str,
    bot_icon: str = "🎯",
    phase_context: dict = None
) -> cl.CustomElement:
    """
    Create or update the WorkshopRoadmap custom sidebar element.

    This replaces cl.TaskList with a richer, interactive component that:
    - Shows visual progress bar
    - Allows clicking to jump to completed phases
    - Displays AI-extracted insights per phase
    - Provides back/next navigation

    Args:
        phases: List of phase dicts with 'name' and 'status'
        current_phase: 0-indexed current phase
        bot_name: Display name for the workshop
        bot_icon: Emoji icon for the workshop
        phase_context: Dict of phase_index -> insight text

    Returns:
        The CustomElement (for reference, already sent/updated)
    """
    # Get existing roadmap or create new one
    roadmap = cl.user_session.get("workshop_roadmap")

    # Build props for the component
    props = {
        "phases": [{"name": p["name"], "status": p["status"]} for p in phases],
        "currentPhase": current_phase,
        "botName": bot_name,
        "botIcon": bot_icon,
        "phaseContext": phase_context or {},
        "canGoBack": current_phase > 0,
        "showInsights": bool(phase_context),
        "completedInsights": [],
    }

    # Extract completed insights from phase_context
    if phase_context:
        for i in range(current_phase):
            if i in phase_context:
                props["completedInsights"].append(phase_context[i])

    try:
        if roadmap is None:
            # Create new roadmap element
            roadmap = cl.CustomElement(
                name="WorkshopRoadmap",
                props=props,
                display="inline"  # Will appear in message flow
            )
            cl.user_session.set("workshop_roadmap", roadmap)

            # Send as part of a minimal message
            await cl.Message(
                content="",
                elements=[roadmap]
            ).send()
        else:
            # Update existing roadmap
            roadmap.props = props
            await roadmap.update()

    except Exception as e:
        # Log error but don't fallback - WorkshopRoadmap is the only UI
        print(f"WorkshopRoadmap error: {e}")
        return None

    return roadmap


# === Cron API Endpoint for Daily Summary ===
# Moved to top-level registration to ensure it's added before Chainlit's catch-all


@cl.action_callback("jump_to_phase")
async def on_jump_to_phase(action: cl.Action):
    """
    Jump to a specific phase (clicked from WorkshopRoadmap sidebar).

    Only allows jumping to completed phases or current phase.
    """
    try:
        target_phase = action.payload.get("phase", 0)
        phases = cl.user_session.get("phases", [])
        current_phase = cl.user_session.get("current_phase", 0)
        bot_id = cl.user_session.get("bot_id", "lawrence")
        bot = BOTS.get(bot_id, BOTS["lawrence"])

        # Validate target is accessible
        if target_phase > current_phase:
            await cl.Message(
                content="⚠️ You can only jump to completed phases or the current phase."
            ).send()
            return

        if target_phase < 0 or target_phase >= len(phases):
            await cl.Message(content="⚠️ Invalid phase selection.").send()
            return

        # If jumping to current phase, just acknowledge
        if target_phase == current_phase:
            phase_name = phases[current_phase]["name"]
            await cl.Message(
                content=f"📍 You're already on Phase {target_phase + 1}: {phase_name}",
                actions=get_phase_navigation_buttons(current_phase, len(phases))
            ).send()
            return

        # Update phase states: mark all phases after target as pending
        for i, phase in enumerate(phases):
            if i < target_phase:
                phase["status"] = "done"
            elif i == target_phase:
                phase["status"] = "running"
            else:
                phase["status"] = "pending"

        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", target_phase)

        # Sync to context_store + persist
        context_key = get_context_key()
        if context_key in context_store:
            context_store[context_key]["phases"] = [p.copy() for p in phases]
            context_store[context_key]["current_phase"] = target_phase
            asyncio.create_task(_persist_context_async(context_key))

        # Update the roadmap
        phase_context = cl.user_session.get("phase_context", {})
        await create_or_update_roadmap(
            phases, target_phase, bot.get("name", "Workshop"),
            bot.get("icon", "🎯"), phase_context
        )

        # Soft transition message
        phase_name = phases[target_phase]["name"]
        await cl.Message(
            content=f"───── 📍 Jumped to Phase {target_phase + 1}/{len(phases)}: {phase_name} ─────\n\n"
                    f"*Returned to this phase. Your conversation history is preserved.*",
            actions=get_phase_navigation_buttons(target_phase, len(phases))
        ).send()

    except Exception as e:
        print(f"Jump to phase error: {e}")
        await cl.Message(content=f"⚠️ Unable to jump to phase: {str(e)[:100]}").send()


def get_contextual_actions(
    bot: dict,
    phases: list,
    current_phase: int,
    turn_count: int = 0,
    is_simple: bool = False
) -> list:
    """
    Get contextual actions based on current state.

    Priority system:
    - P0: Phase transition (when ready to advance)
    - P1: Core workflow actions (2-3 max)
    - P2: Secondary actions (collapsed or hidden)

    Returns max 5 buttons to avoid overwhelm.
    """
    actions = []
    has_phases = bot.get("has_phases", False)

    # === P0: Phase Transition (most important for workshop bots) ===
    if has_phases and phases and current_phase < len(phases) - 1:
        next_phase_name = phases[current_phase + 1]["name"] if current_phase + 1 < len(phases) else None

        # Make this the PRIMARY action - big and obvious
        if next_phase_name:
            actions.append(cl.Action(
                name="next_phase",
                payload={"action": "next"},
                label=f"✅ Continue → {next_phase_name}",
                description=f"Move to the next phase when you're ready",
                tooltip="Click when you've completed this phase"
            ))

    # === P1: Core Workflow Actions (max 2) ===
    actions.append(cl.Action(
        name="deep_research",
        payload={"action": "research"},
        label="🔍 Research",
        tooltip="Search for evidence and data"
    ))

    actions.append(cl.Action(
        name="show_example",
        payload={"action": "example"},
        label="📖 Example",
        tooltip="See a real-world example"
    ))

    # === P2: Secondary Actions (only if not too many already) ===
    if len(actions) < 4:
        actions.append(cl.Action(
            name="synthesize_conversation",
            payload={"action": "synthesize"},
            label="📥 Synthesize",
            tooltip="Summarize key insights"
        ))

    # Think button only for non-simple modes
    if not is_simple and len(actions) < 5:
        actions.append(cl.Action(
            name="think_through",
            payload={"action": "think"},
            label="🧠 Think",
            tooltip="Structured problem breakdown"
        ))

    return actions[:5]  # Never more than 5 buttons


async def send_phase_transition_card(
    phases: list,
    current_phase: int,
    bot_name: str,
    is_auto: bool = False
):
    """
    Send an explicit, unmissable phase transition message with clear instructions.

    Args:
        phases: List of phase dicts
        current_phase: Current phase index (just moved to this)
        bot_name: Name of the current bot
        is_auto: Whether this was auto-detected
    """
    total = len(phases)
    current_name = phases[current_phase]["name"] if current_phase < total else "Complete"

    # Progress bar with emojis
    progress_bar = " ".join([
        "✅" if i < current_phase else "🔵" if i == current_phase else "⚪"
        for i in range(total)
    ])

    # Try to get detailed phase instructions
    phase_instructions = None
    phase_prompt = None
    bot_id = cl.user_session.get("bot_id", "scenario")

    try:
        if bot_id == "scenario":
            from prompts.scenario_phases import get_phase_by_index
            phase_config = get_phase_by_index(current_phase)
            if phase_config:
                phase_instructions = phase_config.get("instructions", [])
                phase_prompt = phase_config.get("prompt", "")
    except ImportError:
        pass

    # Build the card
    content = f"""
---

## 📍 Phase {current_phase + 1}/{total}: {current_name}

{progress_bar}

"""

    # NOTE: Removed auto-advance message per user feedback
    # User controls ALL navigation - phases only advance when user explicitly clicks

    # Add clear instructions for what to do
    if phase_instructions:
        content += f"### What to do in this phase:\n\n"
        for i, instruction in enumerate(phase_instructions, 1):
            content += f"{i}. {instruction}\n"
        content += "\n"
    else:
        content += f"**Focus:** Work through {current_name}\n\n"

    # Add help option
    content += "---\n\n"
    content += "**Choose how to proceed:**\n\n"

    # Build actions based on state
    actions = []

    # Primary action: Help me start this phase
    actions.append(cl.Action(
        name="help_start_phase",
        payload={"phase": current_phase, "phase_name": current_name},
        label=f"🚀 Help me start {current_name}",
        tooltip="Get guided through this phase step by step"
    ))

    # Secondary: Let me work on my own
    actions.append(cl.Action(
        name="acknowledge_phase",
        payload={},
        label="👍 Got it, I'll work on this",
        tooltip="Dismiss this card and continue on your own"
    ))

    # Show next phase preview
    if current_phase + 1 < total:
        next_name = phases[current_phase + 1]["name"]
        content += f"\n*Coming up next: {next_name}*\n"

        # Add skip option
        actions.append(cl.Action(
            name="next_phase",
            payload={"action": "next"},
            label=f"⏭️ Skip to {next_name}",
            tooltip="Skip ahead if you've already covered this"
        ))

    content += "\n---"

    await cl.Message(content=content, actions=actions).send()


async def update_phase(profile: str, phase_index: int, new_status: str):
    """Update a workshop phase status and refresh the roadmap."""
    phases = cl.user_session.get("phases", [])
    if phase_index < len(phases):
        phases[phase_index]["status"] = new_status
        cl.user_session.set("phases", phases)

        # Update WorkshopRoadmap
        bot_id = cl.user_session.get("bot_id", profile)
        bot = BOTS.get(bot_id, BOTS.get("lawrence", {}))
        history = cl.user_session.get("history", [])
        phase_insights = extract_phase_insights(history, phases, phase_index)

        await create_or_update_roadmap(
            phases=phases,
            current_phase=phase_index,
            bot_name=bot.get("name", "Workshop"),
            bot_icon=bot.get("icon", "🎯"),
            phase_context=phase_insights
        )


# ============================================================================
# CUSTOM ELEMENTS - Rich Interactive Components
# ============================================================================

async def show_phase_progress_element():
    """
    Show the WorkshopRoadmap element (replaced PhaseProgress Feb 2026).
    Displays workshop progress with clickable phase navigation.
    """
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)
    bot_id = cl.user_session.get("bot_id", "lawrence")
    bot = BOTS.get(bot_id, BOTS["lawrence"])
    history = cl.user_session.get("history", [])

    if not phases:
        return

    phase_insights = extract_phase_insights(history, phases, current_phase)

    await create_or_update_roadmap(
        phases=phases,
        current_phase=current_phase,
        bot_name=bot.get("name", "Workshop"),
        bot_icon=bot.get("icon", "🎯"),
        phase_context=phase_insights
    )


async def show_dikw_pyramid_element(highlight_level: str = None, scores: dict = None):
    """
    Show the interactive DIKW Pyramid custom element.
    Clickable levels that trigger exploration of each knowledge layer.

    Args:
        highlight_level: Which level to highlight (data, information, knowledge, wisdom)
        scores: Optional dict with scores per level {data: 7, information: 5, ...}
    """
    element = cl.CustomElement(
        name="DIKWPyramid",
        props={
            "highlightLevel": highlight_level,
            "scores": scores or {},
            "showDescriptions": True
        }
    )

    await cl.Message(content="", elements=[element]).send()


async def show_research_matrix_element(categories: dict, query: str = "", total_sources: int = 0):
    """
    Show research results in an interactive matrix visualization.

    Args:
        categories: Dict with research categories (why, what_if, how, validation, challenge)
        query: The original research query
        total_sources: Total number of sources found
    """
    element = cl.CustomElement(
        name="ResearchMatrix",
        props={
            "categories": categories,
            "query": query,
            "totalSources": total_sources
        }
    )

    await cl.Message(content="", elements=[element]).send()


# ============================================================================
# ELEMENT SIDEBAR - Reference Materials
# ============================================================================

async def setup_workshop_sidebar(bot_id: str):
    """
    Configure sidebar with workshop-relevant reference materials.
    Shows methodology reference, phase checklist, and uploaded documents.
    """
    bot = BOTS.get(bot_id, BOTS["lawrence"])
    elements = []

    # Methodology quick reference
    methodology_refs = {
        "tta": "## Trending to the Absurd\n\n1. Identify current trends\n2. Extrapolate to absurd extremes\n3. Find problems worth solving\n4. Validate opportunities",
        "jtbd": "## Jobs to Be Done\n\n1. Find the struggling moment\n2. Map functional, emotional, social jobs\n3. Identify competing solutions\n4. Write job statement",
        "scurve": "## S-Curve Analysis\n\n1. Identify the technology\n2. Assess current era\n3. Gather evidence\n4. Evaluate ecosystem readiness\n5. Make timing decision",
        "ackoff": "## Ackoff's DIKW Pyramid\n\n**Data** → **Information** → **Knowledge** → **Wisdom**\n\nApply Camera Test: Can you observe it?",
        "redteam": "## Red Teaming\n\n1. Extract assumptions\n2. Prioritize by risk\n3. Attack each assumption\n4. Find breaking points\n5. Strengthen or pivot",
        "scenario": "## Scenario Analysis\n\n1. Define domain & focal question\n2. Map STEEP driving forces\n3. Assess uncertainties\n4. Build 2x2 matrix\n5. Write scenario narratives\n6. Synthesize insights",
    }

    if bot_id in methodology_refs:
        elements.append(cl.Text(
            content=methodology_refs[bot_id],
            name=f"{bot.get('name', 'Workshop')} Quick Reference"
        ))

    # Phase checklist for workshop bots
    if bot.get("has_phases"):
        phases = cl.user_session.get("phases") or _get_phases_for_bot(bot_id) or []
        current_phase = cl.user_session.get("current_phase", 0)

        checklist_lines = ["## Phase Checklist\n"]
        for i, p in enumerate(phases):
            status = p.get("status", "pending")
            if status == "done":
                checklist_lines.append(f"- [x] ~~{p['name']}~~")
            elif i == current_phase:
                checklist_lines.append(f"- [ ] **{p['name']}** ← Current")
            else:
                checklist_lines.append(f"- [ ] {p['name']}")

        elements.append(cl.Text(
            content="\n".join(checklist_lines),
            name="Phase Checklist"
        ))

    # Uploaded documents (if any)
    uploaded_docs = cl.user_session.get("uploaded_files", [])
    for doc in uploaded_docs[:3]:
        if doc.get("path"):
            if doc.get("type") == "application/pdf":
                elements.append(cl.Pdf(path=doc["path"], name=doc.get("name", "Document")))
            else:
                elements.append(cl.File(path=doc["path"], name=doc.get("name", "File")))

    # Set sidebar if we have elements
    if elements:
        try:
            await cl.ElementSidebar.set_elements(elements)
            await cl.ElementSidebar.set_title(f"📚 {bot.get('name', 'Workshop')} Resources")
        except Exception as e:
            # ElementSidebar may not be available in all Chainlit versions
            print(f"[SIDEBAR] Could not set sidebar: {e}")


async def update_sidebar_phase(current_phase: int):
    """Update sidebar to reflect current phase progress."""
    bot_id = cl.user_session.get("bot_id", "lawrence")
    bot = BOTS.get(bot_id, BOTS["lawrence"])

    if not bot.get("has_phases"):
        return

    phases = cl.user_session.get("phases", [])
    if not phases:
        return

    # Rebuild checklist with current progress
    checklist_lines = ["## Phase Checklist\n"]
    for i, p in enumerate(phases):
        status = p.get("status", "pending")
        if status == "done":
            checklist_lines.append(f"- [x] ~~{p['name']}~~ ✅")
        elif i == current_phase:
            checklist_lines.append(f"- [ ] **{p['name']}** 🔵 Current")
        else:
            checklist_lines.append(f"- [ ] {p['name']}")

    elements = [
        cl.Text(
            content="\n".join(checklist_lines),
            name="Phase Checklist"
        )
    ]

    try:
        await cl.ElementSidebar.set_elements(elements)
    except Exception as e:
        logger.debug("Sidebar update failed (may be version incompatibility): %s", e)


@cl.set_chat_profiles
async def chat_profiles():
    """Define available bot profiles — dynamically generated from BOTS dict.

    Any agent registered via protocols/agent_definitions.py and merged into BOTS
    automatically appears in the dropdown. No manual editing needed.

    Profile ordering uses unified_registry.profile_order when available;
    falls back to the insertion order of BOTS dict.
    """
    # Build ordered list: use profile_order from UI registry if available
    try:
        from protocols.unified_registry import get_ui_config as _get_ui
    except ImportError:
        _get_ui = None

    _PROFILE_ORDER_FALLBACK = 100

    def _order_key(bot_id):
        if _get_ui:
            ui = _get_ui(bot_id)
            if ui:
                return ui.profile_order
        return _PROFILE_ORDER_FALLBACK

    profiles = []
    for bot_id in sorted(BOTS.keys(), key=_order_key):
        bot_config = BOTS[bot_id]
        if not bot_config.get("system_prompt"):
            continue
        profiles.append(cl.ChatProfile(
            name=bot_id,
            markdown_description=bot_config.get("description", ""),
            icon=bot_config.get("icon", "/public/icons/explore.svg"),
            default=(bot_id == "lawrence"),
        ))

    return profiles


# === Conversation Starters ===
STARTERS = {
    "lawrence": [
        cl.Starter(
            label="Explore a problem",
            message="I have a challenge I'm facing and need help thinking through it systematically.",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="Validate an idea",
            message="I have a solution idea and want to validate if it's worth pursuing.",
            icon="/public/icons/validate.svg",
        ),
        cl.Starter(
            label="Find the right problem",
            message="I'm not sure I'm solving the right problem. Help me step back and examine this.",
            icon="/public/icons/search.svg",
        ),
        cl.Starter(
            label="Challenge my thinking",
            message="I want you to challenge my assumptions and help me see blind spots.",
            icon="/public/icons/challenge.svg",
        ),
    ],
    "tta": [
        cl.Starter(
            label="Start with a trend",
            message="I've identified a trend I want to push to its absurd conclusion: [describe your trend]",
            icon="/public/icons/trend.svg",
        ),
        cl.Starter(
            label="Find emerging problems",
            message="Help me discover problems that don't exist yet by extrapolating current trends.",
            icon="/public/icons/future.svg",
        ),
        cl.Starter(
            label="Analyze my industry",
            message="I want to apply Trending to the Absurd to my industry. Let's start with what's changing.",
            icon="/public/icons/industry.svg",
        ),
        cl.Starter(
            label="Show an example",
            message="Show me how the Trending to the Absurd method works with a concrete example.",
            icon="/public/icons/example.svg",
        ),
    ],
    "jtbd": [
        cl.Starter(
            label="Analyze a product",
            message="I want to understand what job my customers are really hiring my product for.",
            icon="/public/icons/product.svg",
        ),
        cl.Starter(
            label="Find the struggling moment",
            message="Help me identify the struggling moment that triggers my customers to seek a solution.",
            icon="/public/icons/struggle.svg",
        ),
        cl.Starter(
            label="Map the full job",
            message="I want to map the functional, emotional, and social dimensions of my customer's job.",
            icon="/public/icons/map.svg",
        ),
        cl.Starter(
            label="See an example",
            message="Show me a Jobs to Be Done analysis example to understand the framework better.",
            icon="/public/icons/example.svg",
        ),
    ],
    "scurve": [
        cl.Starter(
            label="Analyze a technology",
            message="I want to determine where a specific technology sits on its S-curve.",
            icon="/public/icons/tech.svg",
        ),
        cl.Starter(
            label="Timing assessment",
            message="Help me figure out if I'm too early, too late, or right on time for my technology bet.",
            icon="/public/icons/timing.svg",
        ),
        cl.Starter(
            label="Find the dominant design",
            message="I need to identify whether a dominant design has emerged in my market.",
            icon="/public/icons/design.svg",
        ),
        cl.Starter(
            label="Show the S-curve",
            message="Explain the S-curve framework and show me how to read it.",
            icon="/public/icons/chart.svg",
        ),
    ],
    "redteam": [
        cl.Starter(
            label="Attack my idea",
            message="I have a business idea and I need you to find every hole in it. Here it is: [describe idea]",
            icon="/public/icons/attack.svg",
        ),
        cl.Starter(
            label="Extract assumptions",
            message="Help me identify all the hidden assumptions underlying my plan.",
            icon="/public/icons/extract.svg",
        ),
        cl.Starter(
            label="Find failure modes",
            message="Walk me through all the ways my project could fail.",
            icon="/public/icons/failure.svg",
        ),
        cl.Starter(
            label="Competitive threats",
            message="Analyze the competitive landscape and show me who could crush my idea.",
            icon="/public/icons/compete.svg",
        ),
    ],
    "ackoff": [
        cl.Starter(
            label="Validate a solution",
            message="I have a proposed solution I want to validate by climbing down the DIKW pyramid.",
            icon="/public/icons/validate.svg",
        ),
        cl.Starter(
            label="Explore a problem",
            message="I want to climb up the pyramid to understand a problem better before solving it.",
            icon="/public/icons/climb.svg",
        ),
        cl.Starter(
            label="Show the pyramid",
            message="Explain Ackoff's DIKW pyramid and how to use it for validation.",
            icon="/public/icons/pyramid.svg",
        ),
        cl.Starter(
            label="See an example",
            message="Show me a real example of DIKW validation in action.",
            icon="/public/icons/example.svg",
        ),
    ],
    "bono": [
        cl.Starter(
            label="Analyze a challenge",
            message="I have a strategic challenge I want to analyze with multiple expert perspectives.",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="Generate expert panel",
            message="Help me create a domain-specific expert panel for my problem.",
            icon="/public/icons/team.svg",
        ),
        cl.Starter(
            label="Six Hats analysis",
            message="Walk me through a Six Thinking Hats analysis of my situation.",
            icon="/public/icons/hats.svg",
        ),
        cl.Starter(
            label="See an example",
            message="Show me how the BONO Master framework works with an example.",
            icon="/public/icons/example.svg",
        ),
    ],
    "knowns": [
        cl.Starter(
            label="Map my knowledge",
            message="Help me map what I know and don't know about my situation.",
            icon="/public/icons/map.svg",
        ),
        cl.Starter(
            label="Find blind spots",
            message="What unknown unknowns might be lurking in my plan?",
            icon="/public/icons/search.svg",
        ),
        cl.Starter(
            label="Risk assessment",
            message="Help me assess the risks of what I don't know.",
            icon="/public/icons/risk.svg",
        ),
        cl.Starter(
            label="Explain Rumsfeld Matrix",
            message="Explain the Known-Unknowns framework and how to use it.",
            icon="/public/icons/info.svg",
        ),
    ],
    "nested_hierarchies": [
        cl.Starter(
            label="Map my system",
            message="Help me map the nested hierarchy around a problem I'm trying to solve.",
            icon="/public/icons/hierarchy.svg",
        ),
        cl.Starter(
            label="Find the real constraint",
            message="I keep solving problems but nothing changes. Help me find the real constraint.",
            icon="/public/icons/search.svg",
        ),
        cl.Starter(
            label="Find leverage points",
            message="Where should I intervene to create cascading change across the system?",
            icon="/public/icons/leverage.svg",
        ),
        cl.Starter(
            label="Edison's Battery Example",
            message="Explain the Edison battery example and why solving at the wrong level fails.",
            icon="/public/icons/example.svg",
        ),
    ],
    "domain": [
        cl.Starter(
            label="Start fresh",
            message="I'm starting fresh — help me find my innovation domain from scratch.",
            icon="/public/icons/start.svg",
        ),
        cl.Starter(
            label="I have candidates",
            message="I already have some domain candidates in mind. Help me evaluate them honestly.",
            icon="/public/icons/evaluate.svg",
        ),
        cl.Starter(
            label="Analyze my CV",
            message="I'd like to upload my CV so you can extract potential innovation domains from my background.",
            icon="/public/icons/cv.svg",
        ),
        cl.Starter(
            label="Analyze research paper",
            message="I have a research paper I'd like to analyze for domain opportunities.",
            icon="/public/icons/research.svg",
        ),
    ],
    "investment": [
        cl.Starter(
            label="Evaluate a startup",
            message="I want to evaluate a startup opportunity using the Ten Questions framework.",
            icon="/public/icons/startup.svg",
        ),
        cl.Starter(
            label="Investment thesis",
            message="Help me build an investment thesis for this opportunity: [describe it]",
            icon="/public/icons/thesis.svg",
        ),
        cl.Starter(
            label="Due diligence",
            message="Walk me through a systematic due diligence process.",
            icon="/public/icons/checklist.svg",
        ),
        cl.Starter(
            label="Explain the framework",
            message="Explain the Ten Questions and Investment Thesis framework.",
            icon="/public/icons/info.svg",
        ),
    ],
    "scenario": [
        cl.Starter(
            label="Explore a domain",
            message="I want to explore multiple plausible futures for my industry/domain: [describe it]",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="Build a 2×2 matrix",
            message="Help me build a scenario matrix to navigate uncertainty in my strategic decision.",
            icon="/public/icons/matrix.svg",
        ),
        cl.Starter(
            label="Find hidden problems",
            message="I want to discover problems worth solving that are invisible from my current position.",
            icon="/public/icons/search.svg",
        ),
        cl.Starter(
            label="Show Shell Oil example",
            message="Show me how Shell used scenario planning to prepare for the 1973 oil crisis.",
            icon="/public/icons/example.svg",
        ),
    ],
    "validation": [
        cl.Starter(
            label="Validate an idea",
            message="I have an idea I want to validate with rigorous multi-perspective analysis: [describe your idea]",
            icon="/public/icons/validate.svg",
        ),
        cl.Starter(
            label="Stress-test a strategy",
            message="I have a strategy that needs stress-testing from multiple expert perspectives.",
            icon="/public/icons/attack.svg",
        ),
        cl.Starter(
            label="Make a big decision",
            message="I'm facing a significant decision and want evidence-grounded validation before committing.",
            icon="/public/icons/challenge.svg",
        ),
        cl.Starter(
            label="Show IBM case study",
            message="Show me how IBM used Six Thinking Hats to reduce meeting time by 75%.",
            icon="/public/icons/example.svg",
        ),
    ],
    "beautiful_question": [
        cl.Starter(
            label="Start with WHY",
            message="I have a challenge I want to explore using the Beautiful Question methodology. Help me start with WHY.",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="Challenge assumptions",
            message="I think I know the problem, but I want to challenge my assumptions before jumping to solutions.",
            icon="/public/icons/challenge.svg",
        ),
        cl.Starter(
            label="Generate possibilities",
            message="I understand the problem now. Help me generate bold WHAT IF possibilities.",
            icon="/public/icons/future.svg",
        ),
        cl.Starter(
            label="Show the methodology",
            message="Explain Warren Berger's Beautiful Question methodology and show me an example.",
            icon="/public/icons/example.svg",
        ),
    ],
    "grading": [
        cl.Starter(
            label="Grade student work",
            message="I want to grade student work on problem discovery methodology. I'll upload the document.",
            icon="/public/icons/grading.svg",
        ),
        cl.Starter(
            label="Quick grade",
            message="Give me a quick assessment of this problem discovery work without the full pipeline.",
            icon="/public/icons/speed.svg",
        ),
        cl.Starter(
            label="Explain grading rubric",
            message="Explain your grading methodology and what you look for in problem discovery work.",
            icon="/public/icons/info.svg",
        ),
        cl.Starter(
            label="Show grading example",
            message="Show me an example of how you grade problem discovery work with a sample assessment.",
            icon="/public/icons/example.svg",
        ),
    ],
    "minto": [
        cl.Starter(
            label="Grade problem discovery work",
            message="I want to grade student work using the Minto Problem Reality framework. I'll upload the document.",
            icon="/public/icons/grading.svg",
        ),
        cl.Starter(
            label="Explain Minto approach",
            message="Explain the Minto grading approach - what does 'Problem Reality First' mean?",
            icon="/public/icons/info.svg",
        ),
        cl.Starter(
            label="Show component weights",
            message="Show me the detailed breakdown of how you weight each component in the Minto framework.",
            icon="/public/icons/chart.svg",
        ),
        cl.Starter(
            label="Example assessment",
            message="Show me an example of a Minto-style assessment with the full breakdown.",
            icon="/public/icons/example.svg",
        ),
    ],
    "pws_consultant": [
        cl.Starter(
            label="🧠 Explore Ideas",
            message="I want to explore and find problems worth solving. I'm curious about something but don't have a clear direction yet.",
            icon="/public/icons/explore.svg",
        ),
        cl.Starter(
            label="📄 Get Feedback",
            message="I have something I need feedback on - a document, idea, or plan. Help me validate my thinking.",
            icon="/public/icons/info.svg",
        ),
        cl.Starter(
            label="🚀 Build Venture",
            message="I'm ready to execute on an opportunity. Help me build and launch my venture.",
            icon="/public/icons/startup.svg",
        ),
        cl.Starter(
            label="❓ Not sure yet",
            message="I'm not sure where to start. Can you help me figure out what I need?",
            icon="/public/icons/challenge.svg",
        ),
    ],
}

# --- Registry bridge: merge starters from unified registry ---
try:
    from protocols.unified_registry import generate_starters as _gen_starters
    _registry_starters = _gen_starters()
    for _k, _starter_list in _registry_starters.items():
        if _k not in STARTERS:
            STARTERS[_k] = [
                cl.Starter(
                    label=s.get("label", ""),
                    message=s.get("message", ""),
                    icon=s.get("icon", "/public/icons/explore.svg"),
                )
                for s in _starter_list
            ]
    logger.info(f"[REGISTRY] Merged {len(_registry_starters)} starter sets from registry")
except Exception as _starters_err:
    logger.debug(f"[REGISTRY] Starters merge skipped: {_starters_err}")


@cl.set_starters
async def set_starters():
    """Return conversation starters based on selected chat profile."""
    profile = cl.user_session.get("chat_profile")
    return STARTERS.get(profile, STARTERS.get("lawrence", []))


# === Chat Settings (Input Widgets) ===
@cl.on_settings_update
async def settings_update(settings):
    """Handle settings changes."""
    cl.user_session.set("settings", settings)

    # Handle Quick Mode separately - persist in session
    if "quick_mode" in settings:
        quick_mode = settings["quick_mode"]
        cl.user_session.set("quick_mode", quick_mode)

    # Provide feedback on settings change
    feedback_parts = []
    if "quick_mode" in settings:
        quick_mode = settings["quick_mode"]
        mode_status = "ON" if quick_mode else "OFF"
        feedback_parts.append(f"Quick Mode: **{mode_status}**")
    if "research_depth" in settings:
        depth = settings["research_depth"]
        feedback_parts.append(f"Research: **{depth}**")
    if "show_examples" in settings:
        examples = "enabled" if settings["show_examples"] else "disabled"
        feedback_parts.append(f"Examples: **{examples}**")
    if "response_detail" in settings:
        detail = settings["response_detail"]
        feedback_parts.append(f"Detail level: **{detail}/10**")

    if feedback_parts:
        await cl.Message(content=f"Settings updated: {' | '.join(feedback_parts)}").send()


async def get_settings_widgets():
    """Return the settings widgets for the current profile."""
    # Get current quick_mode state from session for initial value
    quick_mode_initial = cl.user_session.get("quick_mode", False) if cl.user_session else False

    return [
        Switch(
            id="quick_mode",
            label="Quick Mode",
            initial=quick_mode_initial,
            description="Get fast, direct answers instead of Socratic exploration",
        ),
        Select(
            id="research_depth",
            label="Research Depth",
            values=["basic", "advanced", "deep"],
            initial_value="basic",
            description="How thorough should web research be? Deep = iterative with reflection loops",
        ),
        Switch(
            id="show_examples",
            label="Auto-show Examples",
            initial=False,
            description="Automatically show examples for each phase",
        ),
        Slider(
            id="response_detail",
            label="Response Detail",
            initial=1,
            min=1,
            max=10,
            step=1,
            description="How detailed should responses be? (1=concise, 10=comprehensive)",
        ),
        Select(
            id="workshop_mode",
            label="Workshop Mode",
            values=["guided", "freeform"],
            initial_value="guided",
            description="Strict phase progression vs flexible exploration",
        ),
    ]


async def suggest_agents_from_context(
    history: list,
    current_bot: str,
    max_suggestions: int = 2
) -> list:
    """
    Analyze conversation context and suggest relevant agents to switch to.

    Uses keyword matching + graph scoring (advisory, additive only).
    final_score = keyword_score + (graph_score * 1.5)
    Returns list of cl.Action buttons for suggested agents.
    """
    if len(history) < 2:
        return []

    # Get recent conversation text
    recent_text = " ".join([
        msg.get("content", "")
        for msg in history[-6:]
    ]).lower()

    suggestions = []

    # Score each agent based on keyword matches
    agent_scores = {}
    for agent_id, triggers in AGENT_TRIGGERS.items():
        if agent_id == current_bot:
            continue  # Don't suggest current bot

        score = 0
        for keyword in triggers["keywords"]:
            if keyword.lower() in recent_text:
                score += 1

        if score > 0:
            agent_scores[agent_id] = {
                "keyword_score": score,
                "description": triggers["description"]
            }

    # Graph scoring — advisory, additive only (Constraint 1)
    graph_scores = {}
    graph_trace = {}
    problem_trace = {}
    if GRAPHRAG_ENABLED:
        try:
            graph_scores, graph_trace = graph_score_agents(recent_text, current_bot)
            if has_problem_language(recent_text):
                problem_scores, problem_trace = classify_and_route(recent_text, current_bot)
                for bot_id, ps in problem_scores.items():
                    graph_scores[bot_id] = graph_scores.get(bot_id, 0) + ps
        except Exception as e:
            print(f"Graph routing error (non-fatal): {e}")

    # Extraction-driven agent scoring
    extraction = None
    try:
        extraction = cl.user_session.get("last_extraction")
    except Exception as e:
        logger.debug("Could not get last_extraction from session: %s", e)

    if extraction and not extraction.get("empty"):
        content_type = extraction.get("content_type", "general")
        counts = extraction.get("counts", {})
        quality = extraction.get("quality_signals", {})

        if content_type == "solution_focused" and counts.get("problems", 0) == 0:
            if "ackoff" in AGENT_TRIGGERS and current_bot != "ackoff":
                if "ackoff" not in agent_scores:
                    agent_scores["ackoff"] = {"keyword_score": 0, "description": AGENT_TRIGGERS.get("ackoff", {}).get("description", "")}
                agent_scores["ackoff"]["keyword_score"] = agent_scores["ackoff"].get("keyword_score", 0) + 0.4

        if counts.get("assumptions", 0) >= 2:
            if "redteam" in AGENT_TRIGGERS and current_bot != "redteam":
                if "redteam" not in agent_scores:
                    agent_scores["redteam"] = {"keyword_score": 0, "description": AGENT_TRIGGERS.get("redteam", {}).get("description", "")}
                agent_scores["redteam"]["keyword_score"] = agent_scores["redteam"].get("keyword_score", 0) + 0.4

        if quality.get("is_forward_looking"):
            if "tta" in AGENT_TRIGGERS and current_bot != "tta":
                if "tta" not in agent_scores:
                    agent_scores["tta"] = {"keyword_score": 0, "description": AGENT_TRIGGERS.get("tta", {}).get("description", "")}
                agent_scores["tta"]["keyword_score"] = agent_scores["tta"].get("keyword_score", 0) + 0.3

    # ═══════════════════════════════════════════════════════════════════════════
    # v4.0 ENHANCEMENT: Cynefin Domain-Aware Agent Boosting
    # ═══════════════════════════════════════════════════════════════════════════
    cynefin_domain = None
    try:
        from tools.graph_orchestrator import discover_research_plan
        plan = discover_research_plan(recent_text[:300])
        cynefin_domain = plan.cynefin_domain

        if cynefin_domain:
            # Boost agents based on Cynefin domain complexity
            cynefin_boosts = {
                "simple": {"ackoff": 0.25, "validation": 0.2},  # Clear domain - validate with evidence
                "complicated": {"scurve": 0.25, "jtbd": 0.2, "investment": 0.15},  # Expert analysis needed
                "complex": {"tta": 0.3, "scenario": 0.25, "beautiful_question": 0.2},  # Probe-sense-respond
                "chaotic": {"redteam": 0.3, "knowns": 0.25},  # Act-sense-respond, manage unknowns
            }
            boosts = cynefin_boosts.get(cynefin_domain.lower(), {})
            for agent_id, boost in boosts.items():
                if agent_id != current_bot and agent_id in AGENT_TRIGGERS:
                    if agent_id not in agent_scores:
                        agent_scores[agent_id] = {"keyword_score": 0, "description": AGENT_TRIGGERS.get(agent_id, {}).get("description", "")}
                    agent_scores[agent_id]["keyword_score"] = agent_scores[agent_id].get("keyword_score", 0) + boost
    except Exception as e:
        print(f"[v4.0] Cynefin boost skipped: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # v4.0 ENHANCEMENT: Beautiful Questions Phase Auto-Trigger
    # ═══════════════════════════════════════════════════════════════════════════
    if extraction and not extraction.get("empty"):
        counts = extraction.get("counts", {})
        quality = extraction.get("quality_signals", {})
        certainty = counts.get("certainty_statements", 0)
        problems = counts.get("problems", 0)
        solutions = counts.get("solutions", 0)

        # WHY phase: High certainty but no clear problem definition
        if certainty >= 2 and problems == 0:
            if "beautiful_question" in AGENT_TRIGGERS and current_bot != "beautiful_question":
                if "beautiful_question" not in agent_scores:
                    agent_scores["beautiful_question"] = {"keyword_score": 0, "description": "Clarify with WHY questions"}
                agent_scores["beautiful_question"]["keyword_score"] += 0.35

        # WHAT IF phase: Problem defined, exploring solutions
        elif problems > 0 and solutions < 2:
            if "beautiful_question" in AGENT_TRIGGERS and current_bot != "beautiful_question":
                if "beautiful_question" not in agent_scores:
                    agent_scores["beautiful_question"] = {"keyword_score": 0, "description": "Explore possibilities with WHAT IF questions"}
                agent_scores["beautiful_question"]["keyword_score"] += 0.25

        # HOW phase: Has solutions, needs implementation validation
        elif solutions >= 2 and quality.get("is_forward_looking"):
            if "beautiful_question" in AGENT_TRIGGERS and current_bot != "beautiful_question":
                if "beautiful_question" not in agent_scores:
                    agent_scores["beautiful_question"] = {"keyword_score": 0, "description": "Validate approach with HOW questions"}
                agent_scores["beautiful_question"]["keyword_score"] += 0.2

    # Merge: final_score = keyword_score + (graph_score * 1.5)
    all_agent_ids = set(agent_scores.keys()) | set(graph_scores.keys())
    merged_scores = {}
    for agent_id in all_agent_ids:
        if agent_id == current_bot:
            continue
        kw = agent_scores.get(agent_id, {}).get("keyword_score", 0)
        gs = graph_scores.get(agent_id, 0)
        final = kw + (gs * 1.5)
        if final > 0:
            desc = agent_scores.get(agent_id, {}).get("description") or AGENT_TRIGGERS.get(agent_id, {}).get("description", "")
            merged_scores[agent_id] = {"score": round(final, 2), "description": desc}

    # Trace for logging (Constraint 2) - v4.0: Added Cynefin domain
    import logging
    _logger = logging.getLogger("mindrian")
    sorted_merged = sorted(merged_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    trace = {
        "query": recent_text[:120],
        "cynefin_domain": cynefin_domain,  # v4.0: Expose Cynefin classification
        "keyword_scores": {k: v.get("keyword_score", 0) for k, v in agent_scores.items()},
        "graph_trace": graph_trace,
        "problem_trace": problem_trace,
        "final_ranked": [(a, s["score"]) for a, s in sorted_merged[:3]],
    }
    _logger.info("graph_route_trace: %s", trace)

    # v4.0: Store Cynefin domain in session for UI display
    if cynefin_domain:
        cl.user_session.set("cynefin_domain", cynefin_domain)

    # Sort by score and take top suggestions
    sorted_agents = sorted_merged[:max_suggestions]

    # Create action buttons for suggestions
    for agent_id, info in sorted_agents:
        bot_info = BOTS.get(agent_id, {})
        suggestions.append(cl.Action(
            name=f"switch_to_{agent_id}",
            payload={"agent": agent_id, "action": "switch"},
            label=f"Switch to {bot_info.get('emoji', '')} {bot_info.get('name', agent_id)}",
            description=info["description"]
        ))

    return suggestions


async def suggest_research_tools(history: list, current_bot: str) -> list:
    """
    Use LazyGraphRAG to decide if ArXiv, Patent, or Google Trends buttons should appear.

    Decision sources:
      1. Graph orchestrator: if discovered frameworks/techniques link to
         ArXiv, Patents, or Google Trends ResearchTool nodes via SUPPORTS/USES_TOOL
      2. Problem context: if problem type suggests validation (empirical,
         prior art, evidence gaps) or trend analysis
      3. Bot context: Red Team → ArXiv; S-Curve → Patents; TTA → Trends

    Each button includes a 'reason' tooltip explaining WHY it appeared.
    """
    if len(history) < 2:
        return []

    recent_text = " ".join([
        m.get("content", "") for m in history[-4:]
    ]).lower()

    actions = []
    arxiv_reasons = []
    patent_reasons = []
    trends_reasons = []
    govdata_reasons = []
    dataset_reasons = []
    news_reasons = []

    # Layer 0: Extraction signals (fastest, most precise)
    extraction = None
    coherence = None
    try:
        extraction = cl.user_session.get("last_extraction")
        coherence = cl.user_session.get("extraction_coherence")
    except Exception as e:
        logger.debug("Could not get extraction data from session: %s", e)

    if extraction and not extraction.get("empty"):
        counts = extraction.get("counts", {})
        quality = extraction.get("quality_signals", {})

        if not quality.get("has_data") and counts.get("certainty", 0) >= 1:
            arxiv_reasons.append("Claims need evidence grounding")

        if quality.get("is_forward_looking"):
            trends_reasons.append("Forward-looking discussion benefits from trend data")

        if counts.get("assumptions", 0) >= 3:
            news_reasons.append("Multiple assumptions — news may validate or challenge them")

    if coherence:
        if coherence.get("data_grounding", 10) < 4:
            govdata_reasons.append("Low data grounding — government statistics could help")
            dataset_reasons.append("Low data grounding — datasets could validate claims")
        if coherence.get("assumption_awareness", 10) < 4:
            arxiv_reasons.append("Hidden assumptions detected — academic evidence may help")

    # Layer 1: Graph orchestrator — check if discovered tools include ArXiv/Patents/Trends
    try:
        from tools.graph_orchestrator import discover_research_plan
        plan = discover_research_plan(recent_text[:300])

        for tool_name in plan.tool_names:
            tl = tool_name.lower()
            if "arxiv" in tl:
                arxiv_reasons.append(f"Framework '{plan.frameworks[0]['name']}' uses academic research" if plan.frameworks else "Graph suggests academic validation")
            if "patent" in tl:
                patent_reasons.append(f"Framework '{plan.frameworks[0]['name']}' uses patent analysis" if plan.frameworks else "Graph suggests patent landscaping")
            if "trend" in tl:
                trends_reasons.append(f"Framework '{plan.frameworks[0]['name']}' uses trend data" if plan.frameworks else "Graph suggests trend analysis")
            if "gov" in tl or "data search" in tl:
                govdata_reasons.append(f"Framework '{plan.frameworks[0]['name']}' uses public data" if plan.frameworks else "Graph suggests government data grounding")
            if "dataset" in tl:
                dataset_reasons.append(f"Framework '{plan.frameworks[0]['name']}' needs raw data" if plan.frameworks else "Graph suggests dataset discovery")
            if "news" in tl:
                news_reasons.append(f"Framework '{plan.frameworks[0]['name']}' needs current events" if plan.frameworks else "Graph suggests news signal analysis")

        # Technique signals
        for tech in plan.techniques:
            tl = tech.lower()
            if any(w in tl for w in ["validation", "evidence", "empirical", "grounding"]):
                arxiv_reasons.append(f"Technique '{tech}' benefits from academic evidence")
            if any(w in tl for w in ["prior art", "landscape", "innovation scan", "patent"]):
                patent_reasons.append(f"Technique '{tech}' benefits from patent search")
            if any(w in tl for w in ["trend", "foresight", "extrapolat", "emerging", "steep", "pattern"]):
                trends_reasons.append(f"Technique '{tech}' benefits from real trend data")
            if any(w in tl for w in ["evidence", "stakeholder", "cause-effect", "best practice", "expert analysis"]):
                govdata_reasons.append(f"Technique '{tech}' benefits from public economic/demographic data")
            if any(w in tl for w in ["evidence", "gap analysis", "domain", "systematic", "pattern"]):
                dataset_reasons.append(f"Technique '{tech}' can be grounded with real datasets")
            if any(w in tl for w in ["trend", "assumption", "scenario", "emerging", "steep"]):
                news_reasons.append(f"Technique '{tech}' benefits from current news signals")

    except Exception:
        pass  # Graph unavailable — fall through to layer 2

    # Layer 2: Problem context signals
    try:
        from tools.graphrag_lite import get_problem_context
        problem = get_problem_context(recent_text[:200])
        if problem.get("problem_type"):
            pt = problem["problem_type"].lower()
            if "undefined" in pt or "ill-defined" in pt:
                arxiv_reasons.append(f"'{problem['problem_type']}' problems need evidence grounding")
            if "well-defined" in pt:
                patent_reasons.append(f"'{problem['problem_type']}' — check if solutions already exist")
            if "emerging" in pt or "evolving" in pt:
                trends_reasons.append(f"'{problem['problem_type']}' — track real-world momentum")
            if "well-defined" in pt or "complicated" in pt:
                govdata_reasons.append(f"'{problem['problem_type']}' — ground in public economic/labor data")
    except Exception:
        pass

    # Layer 3: Bot-specific signals
    BOT_RESEARCH_HINTS = {
        "redteam":  {"arxiv": "Red Team challenges need counter-evidence", "dataset": "Red Team — find contradicting data to challenge assumptions", "news": "Red Team — check if news contradicts current assumptions"},
        "ackoff":   {"arxiv": "DIKW validation benefits from published data", "govdata": "DIKW Data layer benefits from real government statistics", "dataset": "DIKW Data layer — find raw datasets to build Information from"},
        "scurve":   {"patent": "S-Curve timing uses patent filing patterns", "trends": "S-Curve adoption maps to Google Trends interest curves", "govdata": "S-Curve industry analysis uses BLS/FRED economic data", "news": "S-Curve — news volume signals adoption phase"},
        "tta":      {"patent": "Trend analysis benefits from innovation landscape", "trends": "TTA extrapolation needs real trend baselines", "dataset": "TTA needs real data to validate trend extrapolations", "news": "TTA — current news validates or challenges trend direction"},
        "jtbd":     {"govdata": "JTBD customer research benefits from Census demographic data", "dataset": "JTBD needs behavioral/survey datasets for customer evidence"},
        "scenario": {"trends": "Scenario Analysis — validate uncertainty axes with Google Trends", "news": "Scenario Analysis — current events inform scenario drivers", "govdata": "Scenario Analysis — economic data grounds scenario assumptions", "arxiv": "Scenario Analysis — academic research validates driving forces"},
    }
    bot_hints = BOT_RESEARCH_HINTS.get(current_bot, {})
    if "arxiv" in bot_hints and not arxiv_reasons:
        arxiv_reasons.append(bot_hints["arxiv"])
    if "patent" in bot_hints and not patent_reasons:
        patent_reasons.append(bot_hints["patent"])
    if "trends" in bot_hints and not trends_reasons:
        trends_reasons.append(bot_hints["trends"])
    if "govdata" in bot_hints and not govdata_reasons:
        govdata_reasons.append(bot_hints["govdata"])
    if "dataset" in bot_hints and not dataset_reasons:
        dataset_reasons.append(bot_hints["dataset"])
    if "news" in bot_hints and not news_reasons:
        news_reasons.append(bot_hints["news"])

    # Build buttons with reason tooltips
    if arxiv_reasons:
        reason = arxiv_reasons[0]  # Most specific reason
        actions.append(cl.Action(
            name="arxiv_search",
            payload={"action": "arxiv_search", "reason": reason},
            label="📚 Academic Evidence",
            tooltip=reason,
            description=reason,
        ))

    if patent_reasons:
        reason = patent_reasons[0]
        actions.append(cl.Action(
            name="patent_search",
            payload={"action": "patent_search", "reason": reason},
            label="🔎 Prior Art & Patents",
            tooltip=reason,
            description=reason,
        ))

    if trends_reasons:
        reason = trends_reasons[0]
        actions.append(cl.Action(
            name="trends_search",
            payload={"action": "trends_search", "reason": reason},
            label="📈 Trends",
            tooltip=reason,
            description=reason,
        ))

    if govdata_reasons:
        reason = govdata_reasons[0]
        actions.append(cl.Action(
            name="govdata_search",
            payload={"action": "govdata_search", "reason": reason},
            label="🏛️ Gov Data",
            tooltip=reason,
            description=reason,
        ))

    if dataset_reasons:
        reason = dataset_reasons[0]
        actions.append(cl.Action(
            name="dataset_search",
            payload={"action": "dataset_search", "reason": reason},
            label="📊 Find Datasets",
            tooltip=reason,
            description=reason,
        ))

    if news_reasons:
        reason = news_reasons[0]
        actions.append(cl.Action(
            name="news_search",
            payload={"action": "news_search", "reason": reason},
            label="📰 News Signal",
            tooltip=reason,
            description=reason,
        ))

    return actions


async def get_ai_agent_suggestion(history: list, current_bot: str) -> Optional[str]:
    """
    Use LLM to analyze conversation and suggest the best agent.
    Returns agent_id or None.
    """
    if len(history) < 4:
        return None

    recent_context = "\n".join([
        f"{msg.get('role', 'user')}: {msg.get('content', '')[:200]}"
        for msg in history[-6:]
    ])

    agent_descriptions = "\n".join([
        f"- {agent_id}: {BOTS.get(agent_id, {}).get('description', '')}"
        for agent_id in BOTS.keys()
        if agent_id != current_bot
    ])

    prompt = f"""Based on this conversation, which specialized agent would be most helpful next?

CONVERSATION:
{recent_context}

AVAILABLE AGENTS:
{agent_descriptions}

CURRENT AGENT: {current_bot}

Respond with ONLY the agent_id (e.g., "tta", "ackoff", "redteam") if a switch would be beneficial.
Respond with "none" if the current agent is appropriate.
Be conservative - only suggest a switch if it would clearly add value."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=20
            )
        )
        suggestion = response.text.strip().lower()

        if suggestion in BOTS and suggestion != current_bot:
            return suggestion
    except Exception as e:
        print(f"Agent suggestion error: {e}")

    return None




# === Topic Exclusion Detection ===
# BUG-001 FIX: Detect when user wants to avoid certain topics

import re as _exclusion_re

# Patterns to detect exclusion requests - each pattern captures the topic directly
_EXCLUSION_PATTERNS = [
    # "avoid discussing X", "avoid talking about X", "avoid X"
    r"avoid\s+(?:discussing|talking\s+about|mentioning|covering)\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    r"(?:please\s+)?avoid\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "don't/do not discuss X", "don't bring up X"
    r"(?:please\s+)?(?:don'?t|do\s+not)\s+(?:discuss|talk\s+about|mention|bring\s+up|cover)\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "skip X", "skip the X"
    r"(?:please\s+)?skip\s+(?:the\s+)?(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "I don't want to discuss X"
    r"i\s+(?:don'?t|do\s+not)\s+want\s+(?:to\s+)?(?:discuss|talk\s+about|hear\s+about|cover)\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "not interested in X"
    r"(?:i'?m\s+)?not\s+interested\s+in\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "let's skip X", "let's avoid X", "let's not talk about X"
    r"let'?s\s+(?:skip|avoid)\s+(?:the\s+)?(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    r"let'?s\s+not\s+(?:talk|discuss)\s+about\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "no more X", "enough about X"
    r"no\s+more\s+(?:about\s+)?(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    r"enough\s+about\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "exclude X from the discussion"
    r"exclude\s+(.+?)\s+from\s+(?:the\s+)?(?:discussion|conversation|topics?)",
    # "stay away from X"
    r"stay\s+away\s+from\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
    # "stop with X", "stop mentioning X"
    r"stop\s+(?:with|mentioning|discussing|talking\s+about)\s+(.+?)(?:\s+(?:for\s+now|please|today)|[.,!?]|$)",
]


def detect_topic_exclusion(message: str) -> tuple:
    """
    Detect if user wants to exclude a topic from the conversation.

    Returns:
        (is_exclusion, topic_name) - tuple with bool and extracted topic
    """
    message_lower = message.lower().strip()

    # Skip very short messages
    if len(message_lower) < 10:
        return False, None

    for pattern in _EXCLUSION_PATTERNS:
        match = _exclusion_re.search(pattern, message_lower, _exclusion_re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            # Clean up the topic - remove articles and trailing words
            topic = _exclusion_re.sub(r'^(the|a|an|any|all|those|these)\s+', '', topic)
            topic = _exclusion_re.sub(r'\s+(for\s+now|please|today)$', '', topic)
            topic = topic.rstrip('.,!?')

            # Validate topic is reasonable (2-50 chars, not just stopwords)
            if 2 <= len(topic) <= 50:
                stopwords = {'it', 'that', 'this', 'them', 'they', 'we', 'you', 'me', 'i', 'about'}
                if topic.lower() not in stopwords:
                    return True, topic.title()

    return False, None

def get_context_key() -> str:
    """Generate a key for context preservation across profile switches.

    SECURITY FIX (2026-02-06): NEVER return a shared key like "default_context".
    This caused complete conversation history bleed across all unauthenticated users.

    Priority order:
    1. Authenticated user identifier + thread (persistent, thread-isolated)
    2. Chainlit session ID (unique per browser tab, but lost on refresh)
    3. Random UUID (last resort, prevents mixing but no persistence)
    """
    # Get thread_id for multi-thread isolation
    thread_id = None
    try:
        thread_id = cl.user_session.get("thread_id") or cl.user_session.get("id")
    except Exception:
        pass

    try:
        # Priority 1: Authenticated user - stable key across sessions
        user = cl.user_session.get("user")
        if user and hasattr(user, "identifier") and user.identifier:
            if thread_id:
                return f"user_{user.identifier}_{thread_id}"
            return f"user_{user.identifier}"
    except Exception as e:
        logger.debug("Could not get user identifier for context key: %s", e)

    # Priority 2: Session ID - unique per browser tab
    # Trade-off: Context won't persist across page reloads, but NEVER mixes between users
    try:
        session_id = cl.user_session.get("id")
        if session_id:
            return f"session_{session_id}"
    except Exception as e:
        logger.debug("Could not get session ID for context key: %s", e)

    # Priority 3: Random UUID - absolute last resort
    # This should never happen in practice (Chainlit always provides session ID)
    import uuid
    fallback_key = f"anon_{uuid.uuid4().hex[:12]}"
    logger.warning(f"[SECURITY] Using random fallback context key: {fallback_key}")
    return fallback_key


@cl.on_chat_start
async def start():
    """Initialize conversation with selected bot."""
    chat_profile = cl.user_session.get("chat_profile")
    bot = BOTS.get(chat_profile, BOTS["lawrence"])

    # Initialize stop event for this session
    session_id = cl.user_session.get("id")
    if session_id:
        stop_events[session_id] = asyncio.Event()

    # === Context Preservation: Check for existing conversation ===
    # Try persistent storage first (survives server restart), then in-memory cache
    from utils.context_persistence import load_cross_bot_context

    context_key = get_context_key()

    # Try to load from persistent storage (async), falls back to in-memory
    persisted_context = await load_cross_bot_context(context_key)
    preserved_context = persisted_context or context_store.get(context_key, {})

    previous_bot = preserved_context.get("bot_id") or preserved_context.get("last_bot_id")
    preserved_history = preserved_context.get("history", [])
    is_bot_switch = previous_bot and previous_bot != chat_profile and len(preserved_history) > 0

    # Also try to restore phases from persisted context
    preserved_phases = preserved_context.get("phases", [])
    preserved_current_phase = preserved_context.get("current_phase", 0)

    if is_bot_switch:
        # Switching bots with existing context
        # Preserve history but switch personality
        cl.user_session.set("history", preserved_history.copy())
        cl.user_session.set("previous_bot", previous_bot)

        # Build context summary for the new bot
        context_summary = f"[CONTEXT HANDOFF: User was previously working with {BOTS.get(previous_bot, {}).get('name', previous_bot)}. "
        context_summary += f"Continuing the conversation with preserved context. {len(preserved_history)} messages in history.]"
        cl.user_session.set("context_handoff", context_summary)

        # Restore phases if returning to same bot (or same bot type with phases)
        if previous_bot == chat_profile and preserved_phases:
            cl.user_session.set("phases", [p.copy() for p in preserved_phases])
            cl.user_session.set("current_phase", preserved_current_phase)
    else:
        # Fresh start — do NOT load old history into new conversations
        # Server restart resume is handled by on_chat_resume, not here
        cl.user_session.set("history", [])
        cl.user_session.set("previous_bot", None)
        cl.user_session.set("context_handoff", None)

    cl.user_session.set("bot", bot)
    cl.user_session.set("bot_id", chat_profile or "lawrence")

    # === Topic Exclusions: Initialize or restore excluded topics ===
    # BUG-001 FIX: Track topics user wants to avoid
    preserved_exclusions = preserved_context.get("excluded_topics", [])
    cl.user_session.set("excluded_topics", preserved_exclusions)
    if preserved_exclusions:
        print(f"[EXCLUSIONS] Restored {len(preserved_exclusions)} excluded topics: {preserved_exclusions}")

    # === Conversation Metadata: Unique ID, name, and checkpoint tracking ===
    # Restore from persisted context or create new
    conversation_id = preserved_context.get("conversation_id") or str(uuid.uuid4())
    conversation_name = preserved_context.get("conversation_name", "")
    last_checkpoint = preserved_context.get("last_checkpoint") or datetime.utcnow().isoformat()

    cl.user_session.set("conversation_id", conversation_id)
    cl.user_session.set("conversation_name", conversation_name)
    cl.user_session.set("last_checkpoint", last_checkpoint)
    logger.info(f"[PERSISTENCE] Conversation ID: {conversation_id[:8]}..., checkpoint: {last_checkpoint}")

    # === Wave 2: Conversation Forking - Initialize or restore branch state ===
    preserved_branch_tree = preserved_context.get("branch_tree")
    preserved_active_branch_id = preserved_context.get("active_branch_id")

    if preserved_branch_tree:
        cl.user_session.set("branch_tree", preserved_branch_tree)
        cl.user_session.set("active_branch_id", preserved_active_branch_id)
        cl.user_session.set("fork_points", preserved_branch_tree.get("fork_points", []))

        # If we have an active branch, restore its specific history
        if preserved_active_branch_id:
            active_branch = preserved_branch_tree["branches"].get(preserved_active_branch_id, {})
            cl.user_session.set("branch_history", active_branch.get("history", []))
        else:
            cl.user_session.set("branch_history", [])

        print(f"[FORKING] Restored branch tree with {len(preserved_branch_tree['branches'])} branches")
    else:
        # No branching yet - initialize empty state
        cl.user_session.set("branch_tree", None)
        cl.user_session.set("active_branch_id", None)
        cl.user_session.set("fork_points", [])
        cl.user_session.set("branch_history", [])

    cl.user_session.set("show_branch_selector", False)
    cl.user_session.set("pending_merge", None)

    # === Invisible Router: Initialize routing state ===
    cl.user_session.set("mindrian_mode", "working")  # "working" = invisible routing, "classroom" = agent dropdown
    cl.user_session.set("methodology_cooldowns", {})
    cl.user_session.set("methodology_history", [])

    # === Wave 3: Idea Canvas - Initialize canvas state ===
    try:
        from tools.idea_canvas import init_canvas_state, load_canvas_state
        session_id = cl.user_session.get("id") or str(uuid.uuid4())
        branch_id = cl.user_session.get("active_branch_id") or "main"

        # Try to load existing canvas state
        existing_canvas = await load_canvas_state(session_id)
        if existing_canvas:
            cl.user_session.set("canvas_state", existing_canvas)
            print(f"[CANVAS] Restored {len(existing_canvas.get('idea_nodes', {}))} ideas")
        else:
            cl.user_session.set("canvas_state", init_canvas_state(session_id, branch_id))
    except Exception as e:
        print(f"[CANVAS] Init error (non-fatal): {e}")
        cl.user_session.set("canvas_state", None)

    # === WAVE 4: Auto-Orchestration State ===
    cl.user_session.set("active_orchestrator", None)
    cl.user_session.set("orchestrator_history", [])  # Track completed orchestrations

    # === Recursive Intelligence: Track session start ===
    if SESSION_LOGGER_ENABLED and session_id:
        track_agent_start(session_id, chat_profile or "lawrence")

    # === Per-User LazyGraph Memory: Track session + load context ===
    if SESSION_MEMORY_ENABLED and session_id:
        try:
            # Get user ID from Chainlit auth or context key
            user = cl.user_session.get("user")
            user_id = user.identifier if user else get_context_key()

            # Start session and get returning user context
            user_context = await session_memory_start(
                user_id=user_id,
                session_id=session_id,
                bot_id=chat_profile or "lawrence"
            )

            # Store for later use
            cl.user_session.set("memory_user_id", user_id)

            # If returning user, inject context hint
            if user_context:
                cl.user_session.set("user_memory_context", user_context)
                print(f"[SESSION_MEMORY] Returning user: {user_context[:100]}...")
        except Exception as e:
            print(f"[SESSION_MEMORY] Start error: {e}")

    # === A2A Protocol: Initialize orchestration session ===
    try:
        from protocols import A2A_ORCHESTRATION_ENABLED, init_a2a_session
        if A2A_ORCHESTRATION_ENABLED and session_id:
            orchestrator = await init_a2a_session(session_id)
            cl.user_session.set("a2a_orchestrator", orchestrator)
            logger.info(f"[A2A] Orchestration session initialized for {session_id}")
    except ImportError:
        logger.debug("[A2A] Protocol module not available")
    except Exception as e:
        logger.debug(f"[A2A] Init error (non-fatal): {e}")

    # Only set current_phase to 0 if not already restored
    if cl.user_session.get("current_phase") is None:
        cl.user_session.set("current_phase", 0)

    # Update context store with current session info (including phases and exclusions)
    context_store[context_key] = {
        "bot_id": chat_profile or "lawrence",
        "history": cl.user_session.get("history", []),
        "phases": cl.user_session.get("phases", []),
        "current_phase": cl.user_session.get("current_phase", 0),
        "excluded_topics": cl.user_session.get("excluded_topics", []),  # BUG-001 FIX
    }

    # === PWS Consultant: Initialize stage machine state ===
    if chat_profile == "pws_consultant":
        # Try to restore state from context_store (for bot switching or page refresh)
        restored_state = None
        if PWS_STATE_ENABLED:
            restored_state = restore_pws_from_context_store(context_key)

        if restored_state and restored_state.get("stage"):
            # Restore preserved state
            logger.info(f"[PWS] Restoring state from context_store: stage={restored_state.get('stage')}")
            cl.user_session.set("pws_stage", restored_state.get("stage", "intro"))
            cl.user_session.set("pws_sub_mode", restored_state.get("sub_mode", "normal"))
            cl.user_session.set("pws_challenge_description", restored_state.get("challenge_description", ""))
            cl.user_session.set("pws_challenge_signals", restored_state.get("challenge_signals", {}))
            cl.user_session.set("pws_diagnostic_answers", restored_state.get("diagnostic_answers", []))
            cl.user_session.set("pws_diagnosis", restored_state.get("diagnosis"))
            cl.user_session.set("pws_diagnostic_context", restored_state.get("diagnostic_context", ""))
            cl.user_session.set("pws_expert_panel_data", restored_state.get("expert_panel"))
            cl.user_session.set("pws_domain_discovery", restored_state.get("domain_discovery"))
            cl.user_session.set("pws_consulting_turn_count", restored_state.get("consulting_turn_count", 0))
            # Reset ephemeral state
            cl.user_session.set("pws_intro_turn_count", 0)
            cl.user_session.set("pws_expert_consult_count", 0)
            cl.user_session.set("pws_active_expert_context", "")
            cl.user_session.set("pws_hybrid_context", "")
            cl.user_session.set("pws_expert_panel_task", None)
        else:
            # Fresh initialization
            cl.user_session.set("pws_stage", "intro")
            cl.user_session.set("pws_sub_mode", "normal")
            cl.user_session.set("pws_intro_turn_count", 0)
            cl.user_session.set("pws_challenge_description", "")
            cl.user_session.set("pws_challenge_signals", {})
            cl.user_session.set("pws_diagnostic_answers", [])
            cl.user_session.set("pws_diagnosis", {})
            cl.user_session.set("pws_diagnostic_context", "")
            cl.user_session.set("pws_expert_panel_task", None)
            cl.user_session.set("pws_expert_panel_data", {})
            cl.user_session.set("pws_domain_discovery", {})
            cl.user_session.set("pws_hybrid_context", "")
            cl.user_session.set("pws_consulting_turn_count", 0)
            cl.user_session.set("pws_expert_consult_count", 0)
            cl.user_session.set("pws_active_expert_context", "")
            cl.user_session.set("pws_last_validation_turn", 0)

            # Initialize Red Team validation middleware (AGENTS.md pattern)
            if PWS_VALIDATION_ENABLED:
                cl.user_session.set("pws_validation_middleware", PWSValidationMiddleware())

    # Initialize Quick Mode (default: False for Socratic exploration)
    cl.user_session.set("quick_mode", False)

    # Initialize settings
    settings = await cl.ChatSettings(await get_settings_widgets()).send()
    cl.user_session.set("settings", settings)

    # Inject sticky action buttons CSS (renders nothing visible, just injects CSS)
    try:
        sticky_css_injector = cl.CustomElement(
            name="StickyActionsInjector",
            props={},
            display="inline"
        )
        await cl.Message(content="", elements=[sticky_css_injector]).send()
    except Exception as e:
        print(f"StickyActionsInjector not available: {e}")

    # Show slider reminder on main page (so users don't have to find Settings)
    if not bot.get("has_phases"):
        await cl.Message(
            content="💡 **Tip:** Use the ⚙️ Settings gear (top right) to adjust **Response Detail** — it's set to **1** (concise) by default. Slide up for more detail.",
        ).send()

    # Initialize phases for workshop bots (auto-discovery with legacy fallback)
    phases = _get_phases_for_bot(chat_profile)
    if phases:
        cl.user_session.set("phases", phases)
        cl.user_session.set("phase_context", {})  # For smart phase transitions

        # Create WorkshopRoadmap (the only progress UI)
        await create_workshop_roadmap(chat_profile)

    # Build action buttons for workshop bots
    actions = []
    if bot.get("has_phases"):
        actions = [
            cl.Action(
                name="show_example",
                payload={"action": "example"},
                label="Show Example",
                description="See an example of this phase",
                tooltip="View a real-world example of this methodology phase in action"
            ),
            cl.Action(
                name="next_phase",
                payload={"action": "next"},
                label="Next Phase",
                description="Move to the next workshop phase",
                tooltip="Progress to the next phase of the workshop"
            ),
            cl.Action(
                name="show_progress",
                payload={"action": "progress"},
                label="Show Progress",
                description="View your workshop progress",
                tooltip="See which phases you've completed and what's next"
            ),
            cl.Action(
                name="deep_research",
                payload={"action": "research"},
                label="Deep Research",
                description="Plan and execute web research with Tavily",
                tooltip="🔍 Search the web for relevant data, studies, and evidence"
            ),
            cl.Action(
                name="think_through",
                payload={"action": "think"},
                label="Think It Through",
                description="Break down the problem with sequential thinking",
                tooltip="🧠 Systematically analyze: identify problem → extract assumptions → find gaps → plan next steps"
            ),
            cl.Action(
                name="multi_agent_analysis",
                payload={"action": "multi_agent"},
                label="Multi-Agent Analysis",
                description="Get perspectives from multiple PWS experts",
                tooltip="👥 Get different perspectives from Larry, Red Team, Ackoff, and other PWS experts"
            ),
            cl.Action(
                name="find_breakthrough",
                payload={"action": "breakthrough"},
                label="🚀 Find the Breakthrough",
                description="Auto-orchestrated multi-agent analysis",
                tooltip="🚀 Intelligent workflow selection with auto-orchestrated agent collaboration"
            ),
            cl.Action(
                name="watch_video",
                payload={"action": "video"},
                label="🎬 Watch Video",
                description="Watch tutorial video for this phase",
                tooltip="Watch a tutorial video explaining this workshop phase"
            ),
            cl.Action(
                name="listen_audiobook",
                payload={"action": "audiobook"},
                label="📖 Listen to Chapter",
                description="Listen to relevant PWS audiobook chapter",
                tooltip="Listen to audio content from the PWS course materials"
            ),
        ]

        # Add bot-specific chart buttons
        if chat_profile == "ackoff":
            actions.append(cl.Action(
                name="show_dikw_pyramid",
                payload={"action": "pyramid"},
                label="Show DIKW Pyramid",
                description="View the DIKW pyramid diagram",
                tooltip="📊 View the Data→Information→Knowledge→Wisdom hierarchy diagram"
            ))
        elif chat_profile == "scurve":
            actions.append(cl.Action(
                name="show_scurve",
                payload={"action": "scurve"},
                label="Show S-Curve",
                description="View the technology S-curve diagram",
                tooltip="📈 View the technology adoption S-curve showing ferment→takeoff→maturity phases"
            ))
        elif chat_profile == "redteam":
            # v4.0: Extreme Opposition Mode Toggle
            actions.append(cl.Action(
                name="toggle_extreme_opposition",
                payload={"action": "toggle"},
                label="🔴 Extreme Opposition",
                description="Activate pure devil's advocate mode",
                tooltip="🔴 Switch to Extreme Opposition mode - no mercy, find the fatal flaw"
            ))
        elif chat_profile == "domain":
            actions.append(cl.Action(
                name="analyze_cv",
                payload={"action": "analyze_cv"},
                label="Analyze CV",
                description="Upload a CV/resume to discover innovation domains",
                tooltip="📄 Upload a CV/resume to extract potential innovation domains from your background"
            ))
            actions.append(cl.Action(
                name="analyze_research",
                payload={"action": "analyze_research"},
                label="Analyze Research",
                description="Upload a research paper to discover domain opportunities",
                tooltip="📑 Upload a research paper, patent, or proposal to identify innovation domains"
            ))
            actions.append(cl.Action(
                name="explore_question",
                payload={"action": "explore_question"},
                label="Explore Question",
                description="Enter a research question to discover domain opportunities",
                tooltip="❓ Enter a research question or topic to identify innovation domains without a document"
            ))

        # Add export button for all workshop bots
        actions.append(cl.Action(
            name="export_summary",
            payload={"action": "export"},
            label="Export Summary",
            description="Download workshop summary as markdown",
            tooltip="⬇️ Download a complete summary of your workshop progress as a Markdown file"
        ))
    else:
        # Non-workshop bots — simple_mode (Lawrence) gets fewer buttons
        is_simple = bot.get("simple_mode", False)

        # Core buttons for all non-workshop bots
        actions = [
            cl.Action(
                name="deep_research",
                payload={"action": "research"},
                label="🔍 Research",
                description="Search the web for relevant data and evidence",
                tooltip="🔍 Search the web for relevant data, studies, and evidence to support your analysis"
            ),
            cl.Action(
                name="think_through",
                payload={"action": "think"},
                label="🧠 Think It Through",
                description="Run a structured analysis: problem → assumptions → gaps → next steps",
                tooltip="🧠 Run a structured analysis: define the problem → list assumptions → find gaps → suggest next steps"
            ),
        ]

        # Voice Chat button for Lawrence bots only
        if chat_profile in ["lawrence", "larry_playground"]:
            actions.append(cl.Action(
                name="start_voice_chat",
                payload={"action": "voice"},
                label="🎙️ Voice Chat",
                description="Talk to Lawrence in real-time with your voice",
                tooltip="🎙️ Start a real-time voice conversation with Lawrence using your custom voice"
            ))

        # Full-mode-only buttons (Playground, not Lawrence)
        if not is_simple:
            actions.append(cl.Action(
                name="multi_agent_analysis",
                payload={"action": "multi_agent"},
                label="👥 Multi-Agent Analysis",
                description="Get perspectives from multiple PWS experts",
                tooltip="👥 Get different perspectives from Larry, Red Team, Ackoff, and other PWS experts"
            ))
            actions.append(cl.Action(
                name="find_breakthrough",
                payload={"action": "breakthrough"},
                label="🚀 Find the Breakthrough",
                description="Auto-orchestrated multi-agent analysis",
                tooltip="🚀 Intelligent workflow selection with auto-orchestrated agent collaboration"
            ))
            actions.append(cl.Action(
                name="show_example",
                payload={"action": "example"},
                label="📖 Show Example",
                description="See an example of PWS methodology",
                tooltip="📖 View a real-world example of this methodology in action"
            ))
            actions.append(cl.Action(
                name="listen_audiobook",
                payload={"action": "audiobook"},
                label="🎧 Listen to Chapter",
                description="Listen to relevant PWS audiobook chapter",
                tooltip="🎧 Listen to audio content from the PWS course materials"
            ))

    # Add "Synthesize & Download" button for ALL bots
    actions.append(cl.Action(
        name="synthesize_conversation",
        payload={"action": "synthesize"},
        label="📝 Synthesize & Download",
        description="Larry synthesizes the entire conversation as a downloadable MD file",
        tooltip="📝 Larry summarizes your conversation: key insights, breakthroughs, and next steps"
    ))

    # Add "Save Conversation" button for ALL bots - explicit checkpoint
    actions.append(cl.Action(
        name="save_conversation",
        payload={"action": "save"},
        label="💾 Save Conversation",
        description="Save your progress to cloud storage",
        tooltip="💾 Create a checkpoint - your conversation will persist across server restarts"
    ))

    # Add "Rate Session" button for ALL bots - QA feedback
    actions.append(cl.Action(
        name="rate_session",
        payload={"action": "rate_session"},
        label="📋 Rate Session",
        description="Give QA feedback on this session",
        tooltip="📋 Fill out a QA feedback form to help improve Mindrian"
    ))

    # Full-mode-only: Extract Insights, Generate Image, Analytics
    if not bot.get("has_phases") and not bot.get("simple_mode", False):
        actions.append(cl.Action(
            name="extract_insights",
            payload={"action": "extract"},
            label="🔍 Extract Insights",
            description="Extract structured data: facts, assumptions, statistics, open questions",
            tooltip="🔍 Extract: facts, assumptions, statistics, problems, solutions, and open questions"
        ))

        actions.append(cl.Action(
            name="generate_image",
            payload={},
            label="🎨 Generate Image",
            description="Create an image from a text description using AI",
            tooltip="🎨 Generate images with Gemini Imagen - describe what you want to see"
        ))

        actions.append(cl.Action(
            name="show_feedback_dashboard",
            payload={},
            label="📊 Feedback Analytics",
            description="View feedback analytics dashboard",
            tooltip="📊 See satisfaction rates, trends, and feedback by bot"
        ))

        actions.append(cl.Action(
            name="show_usage_metrics",
            payload={},
            label="📈 Usage Metrics",
            description="View usage metrics dashboard",
            tooltip="📈 See message counts, bot usage, and activity trends"
        ))

        # === WAVE 2: Conversation Forking ===
        actions.append(cl.Action(
            name="show_branch_selector",
            payload={},
            label="🌿 Branches",
            description="View and manage conversation branches",
            tooltip="🌿 Fork conversations, switch branches, merge insights"
        ))

        # === WAVE 3: Idea Canvas ===
        actions.append(cl.Action(
            name="show_idea_canvas",
            payload={},
            label="🎨 Idea Canvas",
            description="Visual workspace for extracted ideas",
            tooltip="🎨 View, organize, and connect ideas extracted from conversation"
        ))

    # Add "Clear Context" action to all bots if there's preserved history
    if is_bot_switch or len(preserved_history) > 0:
        actions.append(cl.Action(
            name="clear_context",
            payload={"action": "clear"},
            label="Clear Context",
            description="Start fresh without previous conversation history",
            tooltip="🗑️ Clear conversation history and start fresh with this bot"
        ))

    # Initialize ElementSidebar for workshop bots
    if bot.get("has_phases"):
        await setup_workshop_sidebar(chat_profile or "lawrence")

    # === Triple-Mode: Initialize session variables ===
    if TRIPLE_MODE_ENABLED:
        init_triple_mode_session()

    # Send welcome message with context info if switching
    # BUG FIX: Add guard to prevent welcome re-send on WebSocket reconnection (Bug 6)
    # Check if welcome was already sent in this session
    welcome_already_sent = cl.user_session.get("welcome_sent", False)

    if not welcome_already_sent:
        # === PWS Tools Panel: Floating toolbar for methodology tools ===
        # Create element BEFORE welcome so it can be attached to welcome message
        tools_panel_elements = []
        try:
            tools_panel = cl.CustomElement(
                name="ToolsPanel",
                props={
                    "conversationContext": "",
                    "currentBot": chat_profile or "lawrence",
                    "expanded": False,
                },
                display="inline"
            )
            tools_panel_elements = [tools_panel]
            cl.user_session.set("tools_panel_id", tools_panel.id if hasattr(tools_panel, 'id') else None)
        except Exception as e:
            print(f"[TOOLS_PANEL] Not available: {e}")

        if is_bot_switch:
            previous_bot_name = BOTS.get(previous_bot, {}).get("name", previous_bot)

            # HONEST CONTEXT MESSAGE (QA P1 fix): Verify context is actually present
            # Only claim context is preserved if we actually have meaningful history
            actual_history = cl.user_session.get("history", [])
            context_actually_preserved = len(actual_history) >= len(preserved_history) and len(actual_history) > 0

            if context_actually_preserved:
                switch_message = f"""**{bot.get('emoji', '')} {bot['name']}** is now active.

**Context preserved from {previous_bot_name}** ({len(actual_history)} messages)
I'll continue our conversation with my perspective.

---

{bot.get('welcome', 'How can I help?')}"""
            else:
                # Context was lost (server restart, deploy, etc.) - be honest
                switch_message = f"""**{bot.get('emoji', '')} {bot['name']}** is now active.

*Session was refreshed. Starting fresh with {bot['name']}.*

{bot.get('welcome', 'How can I help?')}"""

            await cl.Message(content=switch_message, actions=actions if actions else None, elements=tools_panel_elements or None).send()
        elif bot.get("has_phases"):
            await cl.Message(content=bot["welcome"], actions=actions, elements=tools_panel_elements or None).send()
        else:
            # === Smart Onboarding for Lawrence bots ===
            # Show progressive welcome with onboarding offer for first-time users
            if SMART_ONBOARDING_ENABLED and chat_profile in ["lawrence", "larry_playground"]:
                try:
                    # Get user_id for onboarding state
                    user = cl.user_session.get("user")
                    user_id = user.identifier if user else session_id or "anonymous"

                    # Get progressive welcome based on expertise
                    welcome_data = get_progressive_welcome(
                        user_id=user_id,
                        bot_name=bot["name"],
                        show_onboarding_offer=True
                    )

                    welcome_message = welcome_data["message"]
                    show_buttons = welcome_data.get("show_onboarding_buttons", False)

                    # Add onboarding buttons for first-time users
                    if show_buttons:
                        onboarding_actions = [
                            cl.Action(
                                name="start_onboarding",
                                payload={"action": "start"},
                                label="Yes, show me around!",
                                description="Take a quick 2-minute tour of key concepts"
                            ),
                            cl.Action(
                                name="skip_onboarding",
                                payload={"action": "skip"},
                                label="No thanks, let's dive in",
                                description="Skip the tour and start exploring"
                            ),
                        ]
                        # Combine with existing actions
                        all_actions = (actions or []) + onboarding_actions
                        await cl.Message(content=welcome_message, actions=all_actions, elements=tools_panel_elements or None).send()
                    else:
                        await cl.Message(content=welcome_message, actions=actions if actions else None, elements=tools_panel_elements or None).send()

                except Exception as e:
                    logger.warning(f"[SMART_ONBOARDING] Error: {e}, falling back to default welcome")
                    await cl.Message(content=bot["welcome"], actions=actions if actions else None, elements=tools_panel_elements or None).send()
            elif chat_profile == "pws_consultant":
                # PWS Consultant: Welcome + ChallengeIntro component
                await cl.Message(content=bot["welcome"], actions=actions if actions else None, elements=tools_panel_elements or None).send()
                # Send ChallengeIntro component for challenge capture
                challenge_intro = cl.CustomElement(
                    name="ChallengeIntro",
                    props={
                        "placeholder": "Describe your problem or challenge...\n\nFor example:\n- What situation are you facing?\n- What have you tried so far?\n- What's at stake if this isn't resolved?",
                        "showDirectSelect": True,
                    },
                    display="inline",
                )
                await cl.Message(content="", elements=[challenge_intro]).send()
            else:
                await cl.Message(content=bot["welcome"], actions=actions if actions else None, elements=tools_panel_elements or None).send()

        # Mark welcome as sent for this session
        cl.user_session.set("welcome_sent", True)
    else:
        # Reconnection case - just log, don't re-send welcome
        print(f"[WELCOME] Skipping duplicate welcome (session already active with history={len(preserved_history)})")


# === Chat Resume Handler ===
@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    """Restore session state when user returns to an existing conversation."""
    # Get thread metadata from various possible locations
    metadata = thread.get("metadata", {})

    # Also check user_data which some Chainlit versions use
    user_data = thread.get("user_data", {})
    if not metadata and user_data:
        metadata = user_data

    # Try to infer chat_profile from thread name or first messages if not in metadata
    chat_profile = metadata.get("chat_profile", "lawrence")

    # === CRITICAL FIX: Load persisted context from Supabase ===
    # This ensures conversation history survives server restarts
    from utils.context_persistence import load_cross_bot_context
    context_key = get_context_key()
    persisted_context = await load_cross_bot_context(context_key)

    if persisted_context:
        logger.info(f"[PERSISTENCE] Restored context on resume: {persisted_context.get('message_count', 0)} messages")
        # Use persisted data to augment/override thread metadata
        if not metadata.get("current_phase") and persisted_context.get("current_phase"):
            metadata["current_phase"] = persisted_context["current_phase"]
        if not metadata.get("phases") and persisted_context.get("phases"):
            metadata["phases"] = persisted_context["phases"]

        # Restore conversation metadata
        cl.user_session.set("conversation_id", persisted_context.get("conversation_id") or str(uuid.uuid4()))
        cl.user_session.set("conversation_name", persisted_context.get("conversation_name", ""))
        cl.user_session.set("last_checkpoint", persisted_context.get("last_checkpoint", datetime.utcnow().isoformat()))

        # === Wave 2: Restore branch tree from persisted context ===
        preserved_branch_tree = persisted_context.get("branch_tree")
        preserved_active_branch_id = persisted_context.get("active_branch_id")

        if preserved_branch_tree:
            cl.user_session.set("branch_tree", preserved_branch_tree)
            cl.user_session.set("active_branch_id", preserved_active_branch_id)
            cl.user_session.set("fork_points", preserved_branch_tree.get("fork_points", []))

            if preserved_active_branch_id:
                active_branch = preserved_branch_tree["branches"].get(preserved_active_branch_id, {})
                cl.user_session.set("branch_history", active_branch.get("history", []))
            else:
                cl.user_session.set("branch_history", [])

            print(f"[FORKING] Restored {len(preserved_branch_tree['branches'])} branches on resume")
        else:
            cl.user_session.set("branch_tree", None)
            cl.user_session.set("active_branch_id", None)
            cl.user_session.set("fork_points", [])
            cl.user_session.set("branch_history", [])
    else:
        # No persisted context - initialize fresh conversation metadata
        cl.user_session.set("conversation_id", str(uuid.uuid4()))
        cl.user_session.set("conversation_name", "")
        cl.user_session.set("last_checkpoint", datetime.utcnow().isoformat())

        # Initialize empty branch state
        cl.user_session.set("branch_tree", None)
        cl.user_session.set("active_branch_id", None)
        cl.user_session.set("fork_points", [])
        cl.user_session.set("branch_history", [])

    # Restore bot configuration
    bot = BOTS.get(chat_profile, BOTS["lawrence"])
    cl.user_session.set("bot", bot)
    cl.user_session.set("bot_id", chat_profile)
    cl.user_session.set("chat_profile", chat_profile)

    # === Triple-Mode: Restore state from metadata ===
    if TRIPLE_MODE_ENABLED:
        restored = restore_triple_mode_state(metadata)
        if restored:
            entry_point = cl.user_session.get("entry_point")
            print(f"[TRIPLE_MODE] Restored state: entry_point={entry_point}")

            # Re-show exploration sidebar if in brainstorming mode
            if entry_point == "brainstorming":
                await show_exploration_progress_sidebar()

    # Initialize stop event
    session_id = cl.user_session.get("id")
    if session_id:
        stop_events[session_id] = asyncio.Event()

    # Restore phase progress from metadata
    current_phase = metadata.get("current_phase", 0)
    phases = metadata.get("phases", None)

    if phases is None:
        # Fallback: initialize fresh phases (auto-discovery with legacy fallback)
        phases = _get_phases_for_bot(chat_profile)

    if phases:
        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", current_phase)

        # Create WorkshopRoadmap
        await create_or_update_roadmap(
            phases=phases,
            current_phase=current_phase,
            bot_name=bot.get("name", "Workshop"),
            bot_icon=bot.get("icon", "🎯"),
            phase_context={}  # Will be populated as history is restored
        )

    # Restore conversation history - prefer persisted context over thread.steps
    history = []

    # First try: Use persisted context from Supabase (most reliable)
    if persisted_context and persisted_context.get("history"):
        history = persisted_context.get("history", [])
        logger.info(f"[PERSISTENCE] Using {len(history)} messages from Supabase context")
    else:
        # Fallback: Extract from thread.steps (Chainlit's native storage)
        for message in thread.get("steps", []):
            msg_type = message.get("type", "")
            output = message.get("output", "")

            # Handle both old and new Chainlit message type formats
            if msg_type in ("user_message", "user") and output:
                history.append({"role": "user", "content": output})
            elif msg_type in ("assistant_message", "assistant") and output:
                history.append({"role": "model", "content": output})

        if history:
            logger.info(f"[PERSISTENCE] Using {len(history)} messages from thread.steps fallback")

    cl.user_session.set("history", history)

    # Restore settings from metadata
    settings = metadata.get("settings", {})
    if settings:
        cl.user_session.set("settings", settings)
        # Restore Quick Mode from settings
        quick_mode = settings.get("quick_mode", False)
        cl.user_session.set("quick_mode", quick_mode)
    else:
        # Default Quick Mode to False
        cl.user_session.set("quick_mode", False)

    # Re-initialize settings widgets
    await cl.ChatSettings(await get_settings_widgets()).send()

    # Welcome back message - module-level guard prevents spam on reconnects
    thread_id = thread.get("id", "")
    if thread_id and thread_id not in _resumed_threads:
        _resumed_threads.add(thread_id)
        # Cap set size to prevent memory leak
        if len(_resumed_threads) > 500:
            _resumed_threads.clear()

        phase_info = ""
        if phases and current_phase < len(phases):
            phase_info = f"\n\n**Current phase:** {phases[current_phase]['name']} (Phase {current_phase + 1} of {len(phases)})"

        # Generate a concise Minto-structured recap via Gemini
        recap = ""
        if history and len(history) >= 4:
            try:
                # Take last 8 messages max, truncate for cost
                recent = history[-8:]
                digest = "\n".join([
                    f"{'User' if m.get('role')=='user' else 'Larry'}: {m['content'][:200]}"
                    for m in recent
                ])
                recap_resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"""Summarize this conversation so the user can continue where they left off.
Write 2-4 sentences in a warm, conversational tone (like a coach catching someone up).
Structure: What we discussed → Where we got to → What's next.
Do NOT use framework names or jargon. Be concise.

Conversation:
{digest}""",
                    config={"max_output_tokens": 150, "temperature": 0.3},
                )
                recap_text = recap_resp.text.strip() if recap_resp.text else ""
                if recap_text:
                    recap = f"\n\n{recap_text}"
            except Exception as e:
                # Fallback: simple last-message recap
                user_msgs = [m["content"][:100] for m in history if m.get("role") == "user"][-2:]
                if user_msgs:
                    recap = "\n\n**Where we left off:** " + " → ".join(user_msgs)
                logger.debug("Resume recap generation failed: %s", e)

        await cl.Message(
            content=f"**Welcome back!**{phase_info}{recap}"
        ).send()
        cl.user_session.set("welcome_sent", True)


# === Stop Handler ===
@cl.on_stop
async def on_stop():
    """Handle user clicking the stop button during generation."""
    session_id = cl.user_session.get("id")
    if session_id and session_id in stop_events:
        stop_events[session_id].set()

    await cl.Message(
        content="**Stopped.** Ready for your next message.",
        actions=[
            cl.Action(name="deep_research", payload={"action": "research"}, label="🔍 Research"),
            cl.Action(name="synthesize_conversation", payload={"action": "synthesize"}, label="📥 Synthesize"),
        ],
    ).send()


# === User Feedback Handler ===
@cl.on_feedback
async def on_feedback(feedback):
    """
    Handle user feedback (thumbs up/down) on messages.
    Stores feedback in Supabase for QA analytics and shows confirmation.
    """
    try:
        from utils.feedback import store_feedback, get_feedback_confirmation_message

        # Get session context
        thread_id = cl.user_session.get("id", "unknown")
        bot_id = cl.user_session.get("chat_profile", "lawrence")
        phase = cl.user_session.get("current_phase")
        phases = cl.user_session.get("phases", [])
        phase_name = phases[phase]["name"] if phases and phase is not None and phase < len(phases) else None

        # Get the message content and user's last message for context
        history = cl.user_session.get("history", [])
        message_content = None
        user_message = None

        # Find the last assistant message and user message
        for msg in reversed(history):
            if msg.get("role") in ["assistant", "model"] and message_content is None:
                message_content = msg.get("content", "")[:500]
            if msg.get("role") == "user" and user_message is None:
                user_message = msg.get("content", "")[:200]
            if message_content and user_message:
                break

        # Store feedback
        store_feedback(
            message_id=feedback.id,
            thread_id=thread_id,
            score=feedback.value,  # 1 = thumbs up, 0 = thumbs down
            comment=feedback.comment,
            bot_id=bot_id,
            phase=phase_name,
            message_content=message_content,
            user_message=user_message,
            feedback_type="thumbs",
        )

        # Show confirmation in conversation
        confirmation = get_feedback_confirmation_message(
            score=feedback.value,
            feedback_type="thumbs",
            comment=feedback.comment
        )

        # Add option for more detailed feedback
        await cl.Message(
            content=confirmation,
            actions=[
                cl.Action(
                    name="detailed_feedback",
                    payload={"message_id": feedback.id},
                    label="📝 Add Detailed Feedback",
                    description="Rate specific aspects of this response",
                    tooltip="Provide detailed feedback on accuracy, helpfulness, and other aspects"
                )
            ]
        ).send()

        print(f"Feedback received: {'👍' if feedback.value == 1 else '👎'} for {bot_id}")

    except Exception as e:
        print(f"Feedback storage error: {e}")


@cl.action_callback("detailed_feedback")
async def on_detailed_feedback(action: cl.Action):
    """Show detailed feedback options with 1-5 scale."""
    from utils.feedback import RATING_SCALE, FEEDBACK_CATEGORIES

    message_id = action.payload.get("message_id", "unknown")

    # Create rating buttons (1-5 scale with emojis)
    rating_actions = [
        cl.Action(
            name=f"rate_{score}",
            payload={"message_id": message_id, "score": score},
            label=f"{info['emoji']} {score}",
            description=info['description']
        )
        for score, info in RATING_SCALE.items()
    ]

    # Format the rating scale display
    scale_display = "\n".join([
        f"**{score}** {info['emoji']} - {info['label']}: *{info['description']}*"
        for score, info in RATING_SCALE.items()
    ])

    await cl.Message(
        content=f"""**📊 Rate This Response (1-5):**

{scale_display}

Select your rating:""",
        actions=rating_actions
    ).send()


@cl.action_callback("rate_1")
@cl.action_callback("rate_2")
@cl.action_callback("rate_3")
@cl.action_callback("rate_4")
@cl.action_callback("rate_5")
async def on_rate_detailed(action: cl.Action):
    """Handle detailed rating submission."""
    from utils.feedback import store_feedback, get_feedback_confirmation_message, RATING_SCALE

    payload = action.payload
    message_id = payload.get("message_id", "unknown")
    score = payload.get("score", 3)

    # Get session context
    thread_id = cl.user_session.get("id", "unknown")
    bot_id = cl.user_session.get("chat_profile", "lawrence")
    phase = cl.user_session.get("current_phase")
    phases = cl.user_session.get("phases", [])
    phase_name = phases[phase]["name"] if phases and phase is not None and phase < len(phases) else None

    # Get message context
    history = cl.user_session.get("history", [])
    message_content = None
    user_message = None

    for msg in reversed(history):
        if msg.get("role") in ["assistant", "model"] and message_content is None:
            message_content = msg.get("content", "")[:500]
        if msg.get("role") == "user" and user_message is None:
            user_message = msg.get("content", "")[:200]
        if message_content and user_message:
            break

    # Store detailed feedback
    store_feedback(
        message_id=message_id,
        thread_id=thread_id,
        score=score,
        bot_id=bot_id,
        phase=phase_name,
        message_content=message_content,
        user_message=user_message,
        feedback_type="detailed",
    )

    # Get rating info
    rating_info = RATING_SCALE.get(score, {"emoji": "⭐", "label": "Unknown"})

    # Show confirmation with option to add comment
    await cl.Message(
        content=f"""**{rating_info['emoji']} Thank you for your detailed feedback!**

You rated this response: **{score}/5 - {rating_info['label']}**

Your feedback helps improve Mindrian for everyone.""",
        actions=[
            cl.Action(
                name="add_feedback_comment",
                payload={"message_id": message_id, "score": score},
                label="💬 Add a Comment",
                description="Tell us more about your experience"
            )
        ]
    ).send()

    print(f"Detailed feedback: {score}/5 ({rating_info['label']}) for {bot_id}")


@cl.action_callback("add_feedback_comment")
async def on_add_feedback_comment(action: cl.Action):
    """Prompt user to add a comment to their feedback."""
    await cl.Message(
        content="""**💬 Add Your Comment**

Please type your feedback comment below. What worked well? What could be improved?

*(Just send your comment as a regular message)*"""
    ).send()

    # Store that we're expecting a feedback comment
    cl.user_session.set("expecting_feedback_comment", True)
    cl.user_session.set("feedback_context", action.payload)


@cl.action_callback("multi_agent_analysis")
async def on_multi_agent_analysis(action: cl.Action):
    """Trigger multi-agent analysis - let user choose the type."""

    # Show options for different analysis types
    await cl.Message(
        content="""**Choose Multi-Agent Analysis Type:**

Select the type of analysis you want:""",
        actions=[
            cl.Action(
                name="ma_quick",
                payload={"type": "quick"},
                label="Quick Analysis",
                description="Router picks best agents (fastest)",
                tooltip="⚡ Fast: AI router selects the most relevant agents automatically"
            ),
            cl.Action(
                name="ma_research",
                payload={"type": "research"},
                label="Research & Explore",
                description="Web research → TTA → Larry",
                tooltip="🔍 Web research → Trending to Absurd → Larry synthesis"
            ),
            cl.Action(
                name="ma_validate",
                payload={"type": "validate"},
                label="Validate Decision",
                description="Validation → Ackoff → Red Team",
                tooltip="✅ Fact-check → Ackoff DIKW validation → Red Team challenge"
            ),
            cl.Action(
                name="ma_full",
                payload={"type": "full"},
                label="Full Analysis",
                description="Research → Validate → All Agents (most thorough)",
                tooltip="🔄 Comprehensive: research + validation + all expert perspectives"
            ),
        ]
    ).send()


@cl.action_callback("ma_quick")
async def on_ma_quick(action: cl.Action):
    await run_multi_agent_with_type("quick")

@cl.action_callback("ma_research")
async def on_ma_research(action: cl.Action):
    await run_multi_agent_with_type("research")

@cl.action_callback("ma_validate")
async def on_ma_validate(action: cl.Action):
    await run_multi_agent_with_type("validate")

@cl.action_callback("ma_full")
async def on_ma_full(action: cl.Action):
    await run_multi_agent_with_type("full")


@cl.action_callback("larry_teach_me")
async def on_larry_teach_me(action: cl.Action):
    """Generate a cognitive intervention based on conversation context."""
    try:
        from tools.quick_lecture import larry_teach_me

        history = cl.user_session.get("history", [])

        # Get the user's last question/message
        last_user_msg = ""
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if not last_user_msg:
            await cl.Message(content="I need a question or problem to work with. What's the real challenge you're wrestling with?").send()
            return

        # Get user's question history for repeat detection
        # IMPORTANT: Exclude the current message to avoid comparing against itself
        all_user_msgs = [
            msg.get("content", "") for msg in history
            if msg.get("role") == "user"
        ]
        # Exclude last message (which is the query) - compare against PREVIOUS messages only
        user_history = all_user_msgs[:-1][-5:] if len(all_user_msgs) > 1 else []

        # Show loading message with diagnosis steps
        loading_msg = cl.Message(content="""🎓 **Larry is diagnosing your thinking...**

→ Classifying your problem type...
→ Detecting thinking patterns...
→ Selecting the right framework...
→ Crafting your intervention...
→ Converting to audio...""")
        await loading_msg.send()

        # Generate the cognitive intervention with FULL conversation history
        result = await larry_teach_me(
            query=last_user_msg,
            conversation_history=history,
            user_history=user_history,
            include_audio=True
        )

        # Handle refusal
        if result["status"] == "refused":
            loading_msg.content = f"""🎓 **Larry says:**

{result['refusal_response']}

*Sometimes the most valuable intervention is the question itself.*"""
            await loading_msg.update()
            return

        # Build response with diagnosis
        diagnosis = result["diagnosis"]
        elements = []
        if result["audio_bytes"]:
            elements.append(cl.Audio(
                content=result["audio_bytes"],
                mime="audio/mpeg",
                name="larry_intervention.mp3"
            ))

        response = f"""🎓 **Larry's Cognitive Intervention**

**📋 Diagnosis:**
• **Problem Type:** {diagnosis.get('problem_type', 'unknown').title()}
• **Thinking Pattern:** {diagnosis.get('thinking_error', 'unknown').replace('_', ' ').title()}
• **Framework Applied:** {diagnosis.get('framework_used', 'PWS Methodology')}

---

{result['transcript']}

---

{'🎧 *Click play above to listen*' if result['audio_bytes'] else ''}

**✏️ Your Next Move:** {result['cta']}"""

        # Add rewrite button for tracking
        actions = [
            cl.Action(
                name="rewrite_question",
                payload={"original": last_user_msg[:200]},
                label="✏️ Rewrite My Question",
                tooltip="Reframe your question based on Larry's intervention",
            )
        ]

        loading_msg.content = response
        loading_msg.elements = elements
        loading_msg.actions = actions
        await loading_msg.update()

    except Exception as e:
        logger.error(f"Larry teach me error: {e}")
        await cl.Message(content=f"I couldn't generate the intervention: {str(e)[:100]}").send()


@cl.action_callback("rewrite_question")
async def on_rewrite_question(action: cl.Action):
    """Handle rewrite question CTA - the key success metric."""
    original = action.payload.get("original", "")
    await cl.Message(content=f"""📝 **Time to rewrite your question.**

Your original question was:
> {original}

Now, based on Larry's intervention, ask it differently. What's the question beneath your question?

*Tip: If your new question makes you slightly uncomfortable, you're probably on the right track.*""").send()


async def run_multi_agent_with_type(analysis_type: str):
    """Execute the selected multi-agent analysis type."""
    from agents.multi_agent_graph import (
        quick_analysis,
        research_and_explore,
        validated_decision,
        full_analysis_with_research,
        AGENTS,
        BACKGROUND_AGENTS
    )

    history = cl.user_session.get("history", [])

    # Build context from recent conversation - use more context for better analysis
    recent_context = "\n".join([
        f"{msg.get('role', 'user')}: {msg.get('content', '')[:800]}"
        for msg in history[-10:]
    ])

    if not recent_context:
        await cl.Message(content="No conversation context yet. Please discuss your problem first, then request multi-agent analysis.").send()
        return

    # Map types to workflows and descriptions
    workflows = {
        "quick": {
            "func": quick_analysis,
            "name": "Quick Analysis",
            "agents": "Auto-selected by router"
        },
        "research": {
            "func": research_and_explore,
            "name": "Research & Explore",
            "agents": "Research Agent → TTA → Larry"
        },
        "validate": {
            "func": validated_decision,
            "name": "Validate Decision",
            "agents": "Validation Agent → Ackoff → Red Team"
        },
        "full": {
            "func": full_analysis_with_research,
            "name": "Full Analysis",
            "agents": "Research + Validation → Larry + Red Team + Ackoff"
        }
    }

    workflow = workflows.get(analysis_type, workflows["quick"])

    try:
        # Show progress with cl.Step
        async with cl.Step(name=f"Multi-Agent: {workflow['name']}", type="run") as main_step:
            main_step.input = f"Analyzing with: {workflow['agents']}"

            # Execute workflow
            async with cl.Step(name="Running Agent Pipeline", type="tool") as pipeline_step:
                pipeline_step.input = f"Context: {recent_context[:200]}..."

                result = await workflow["func"](recent_context)

                pipeline_step.output = f"Completed - received responses from agents"

            # Process results
            output_parts = []

            # Background agent results
            if result.get("background_results"):
                async with cl.Step(name="Background Agent Results", type="tool") as bg_step:
                    bg_outputs = []
                    for agent_id, agent_result in result["background_results"].items():
                        if agent_result.get("success"):
                            agent_name = BACKGROUND_AGENTS[agent_id].name
                            if agent_id == "research":
                                findings = agent_result.get("findings", "No findings")
                                sources = agent_result.get("sources", [])
                                bg_outputs.append(f"**{agent_name}:**\n{findings}")
                                if sources:
                                    source_list = "\n".join([f"- [{s['title']}]({s['url']})" for s in sources[:5]])
                                    bg_outputs.append(f"\n**Sources:**\n{source_list}")
                            elif agent_id == "validation":
                                report = agent_result.get("validation_report", "No report")
                                bg_outputs.append(f"**{agent_name}:**\n{report}")
                            elif agent_id == "analysis":
                                analysis = agent_result.get("analysis", "No analysis")
                                bg_outputs.append(f"**{agent_name}:**\n{analysis}")

                    bg_step.output = f"Processed {len(result['background_results'])} background agents"
                    output_parts.extend(bg_outputs)

            # Conversation agent responses
            if result.get("conversation_responses"):
                async with cl.Step(name="Expert Perspectives", type="llm") as conv_step:
                    conv_outputs = []
                    for agent_id, response in result["conversation_responses"].items():
                        agent_name = AGENTS.get(agent_id, {}).get("name", agent_id)
                        conv_outputs.append(f"### {agent_name}\n{response}")

                    conv_step.output = f"Received {len(result['conversation_responses'])} expert perspectives"
                    output_parts.extend(conv_outputs)

            # Synthesis
            synthesis = result.get("synthesis", "")
            if synthesis:
                output_parts.append(f"---\n\n## Synthesis\n{synthesis}")

            main_step.output = "Analysis complete"

        # Send final combined message
        final_output = "\n\n".join(output_parts)
        if not final_output:
            final_output = "No results generated. Try providing more context in your conversation."

        await cl.Message(
            content=f"## {workflow['name']} Results\n\n{final_output}",
            actions=[
                cl.Action(name="multi_agent_analysis", payload={}, label="Run Another Analysis"),
            ]
        ).send()

    except Exception as e:
        await cl.Message(content=f"Multi-agent analysis error: {str(e)}").send()


@cl.action_callback("clear_context")
async def on_clear_context(action: cl.Action):
    """Clear ALL preserved context and start completely fresh."""
    from utils.context_persistence import clear_cross_bot_context

    context_key = get_context_key()

    # Clear in-memory context
    if context_key in context_store:
        del context_store[context_key]

    # Clear from persistent storage (Supabase)
    await clear_cross_bot_context(context_key)

    # Clear ALL session state that could carry old context
    cl.user_session.set("history", [])
    cl.user_session.set("previous_bot", None)
    cl.user_session.set("context_handoff", None)
    cl.user_session.set("excluded_topics", [])
    cl.user_session.set("turn_count", 0)

    bot = cl.user_session.get("bot", BOTS["lawrence"])
    bot_name = bot.get("name", "Larry")

    await cl.Message(
        content=f"**Context cleared.** Fresh start with {bot_name}. What's on your mind?"
    ).send()


# === BUG-001 FIX: Topic Exclusion Management Callbacks ===

@cl.action_callback("manage_exclusions")
async def on_manage_exclusions(action: cl.Action):
    """Show current list of excluded topics with management options."""
    excluded_topics = cl.user_session.get("excluded_topics", [])

    if not excluded_topics:
        await cl.Message(
            content="You don't have any excluded topics. To exclude a topic, just say something like:\n\n- *\"Avoid discussing S-curves\"*\n- *\"Skip the JTBD framework\"*\n- *\"Don't bring up market sizing\"*"
        ).send()
        return

    topics_list = "\n".join([f"- {topic}" for topic in excluded_topics])
    await cl.Message(
        content=f"""**Currently Excluded Topics:**

{topics_list}

To remove a topic from this list, click \"Clear All\" or ask me to discuss the topic again.""",
        actions=[
            cl.Action(
                name="clear_exclusions",
                payload={"action": "clear_all"},
                label="Clear All Exclusions",
                tooltip="Remove all topic exclusions"
            )
        ]
    ).send()


@cl.action_callback("clear_exclusions")
async def on_clear_exclusions(action: cl.Action):
    """Clear all excluded topics."""
    excluded_topics = cl.user_session.get("excluded_topics", [])
    count = len(excluded_topics)

    # Clear the list
    cl.user_session.set("excluded_topics", [])

    # Update context store + persist
    context_key = get_context_key()
    if context_key in context_store:
        context_store[context_key]["excluded_topics"] = []
        asyncio.create_task(_persist_context_async(context_key))

    await cl.Message(
        content=f"**All topic exclusions cleared.** I've removed {count} topic{'s' if count != 1 else ''} from the exclusion list. I'm now free to discuss any topic."
    ).send()


# === Explicit Save Conversation ===
@cl.action_callback("save_conversation")
async def on_save_conversation(action: cl.Action):
    """
    Explicitly save the current conversation state.

    Creates a checkpoint with:
    - Full conversation history
    - Current phase progress
    - Conversation metadata (ID, name, timestamp)
    """
    from utils.context_persistence import save_cross_bot_context

    context_key = get_context_key()
    bot_id = cl.user_session.get("bot_id", "lawrence")
    history = cl.user_session.get("history", [])
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)

    # Update checkpoint timestamp
    last_checkpoint = datetime.utcnow().isoformat()
    cl.user_session.set("last_checkpoint", last_checkpoint)

    # Get or create conversation_id
    conversation_id = cl.user_session.get("conversation_id")
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        cl.user_session.set("conversation_id", conversation_id)

    # Get optional conversation name from action payload
    conversation_name = action.payload.get("name") or cl.user_session.get("conversation_name", "")
    if action.payload.get("name"):
        cl.user_session.set("conversation_name", conversation_name)

    try:
        # BUG-001 FIX: Include excluded_topics in context persistence
        excluded_topics = cl.user_session.get("excluded_topics", [])
        success = await save_cross_bot_context(
            user_key=context_key,
            history=history.copy(),
            bot_id=bot_id,
            bot_name=BOTS.get(bot_id, {}).get("name", bot_id),
            phases=[p.copy() for p in phases] if phases else None,
            current_phase=current_phase,
            conversation_id=conversation_id,
            conversation_name=conversation_name,
            excluded_topics=excluded_topics
        )

        if success:
            # Format timestamp for display
            checkpoint_display = datetime.fromisoformat(last_checkpoint).strftime("%I:%M %p")
            message_count = len(history)

            name_display = f' "{conversation_name}"' if conversation_name else ""
            await cl.Message(
                content=f"**Conversation saved!**{name_display}\n\n"
                        f"- Messages: {message_count}\n"
                        f"- Checkpoint: {checkpoint_display}\n"
                        f"- ID: `{conversation_id[:8]}...`\n\n"
                        f"*Your progress is now persisted and will survive server restarts.*"
            ).send()
            logger.info(f"[PERSISTENCE] Manual save: {message_count} messages, checkpoint {last_checkpoint}")
        else:
            await cl.Message(
                content="**Warning:** Could not save to cloud storage. Your conversation is cached locally but may not persist across server restarts."
            ).send()
    except Exception as e:
        logger.error(f"[PERSISTENCE] Manual save failed: {e}")
        await cl.Message(
            content=f"**Error saving conversation:** {str(e)}"
        ).send()


# === Form Submission Callbacks (AskElementMessage) ===

@cl.action_callback("form_submit")
async def on_form_submit(action: cl.Action):
    """
    Handle form submissions from custom JSX elements.

    Supports multiple form types:
    - scenario_setup: Scenario Analysis initialization
    - problem_definition: PWS problem definition

    The form data is stored in session and used to initialize the conversation.
    """
    form_type = action.payload.get("formType", "")
    form_data = action.payload.get("data", {})

    if not form_data:
        await cl.Message(content="No form data received. Please try again.").send()
        return

    if form_type == "scenario_setup":
        await handle_scenario_setup_form(form_data)
    elif form_type == "problem_definition":
        await handle_problem_definition_form(form_data)
    else:
        # Generic form handling - store data and continue conversation
        cl.user_session.set("form_data", form_data)
        await cl.Message(
            content=f"**Form received.** Processing {form_type} data...\n\n"
                    f"Fields: {', '.join(form_data.keys())}"
        ).send()


async def handle_scenario_setup_form(data: dict):
    """Process Scenario Analysis setup form."""
    domain = data.get("domain", "")
    focal_question = data.get("focalQuestion", "")
    time_horizon = data.get("timeHorizon", "2035")
    stakeholders = data.get("stakeholders", "")
    decision_context = data.get("decisionContext", "")

    # Store structured data in session for phase context
    phase_context = {
        "domain": domain,
        "focal_question": focal_question,
        "time_horizon": time_horizon,
        "stakeholders": [s.strip() for s in stakeholders.split(",") if s.strip()],
        "decision_context": decision_context
    }
    cl.user_session.set("phase_context", phase_context)

    # Build summary message
    summary = f"""**🔮 Scenario Analysis Setup Complete**

**Domain:** {domain}
**Focal Question:** {focal_question}
**Time Horizon:** {time_horizon}"""

    if stakeholders:
        summary += f"\n**Key Stakeholders:** {stakeholders}"
    if decision_context:
        summary += f"\n**Context:** {decision_context[:150]}..."

    summary += """

---

**You've completed Phase 1: Introduction.**

Now let's move to **Phase 2: Domain & Driving Forces**.

I'll help you identify the STEEP forces (Social, Technological, Economic, Environmental, Political) that could reshape your domain.

**Let's start:** What SOCIAL forces (demographics, culture, lifestyle) might impact {domain}?"""

    # Advance to Phase 2
    phases = cl.user_session.get("phases", [])
    if phases and len(phases) > 1:
        phases[0]["status"] = "done"
        phases[1]["status"] = "running"
        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", 1)
        await update_sidebar_phase(1)

    await cl.Message(
        content=summary.format(domain=domain),
        actions=[
            cl.Action(name="show_example", payload={}, label="Show STEEP Example"),
            cl.Action(name="deep_research", payload={}, label="Research Trends"),
        ]
    ).send()


async def handle_problem_definition_form(data: dict):
    """Process Problem Definition form."""
    problem_statement = data.get("problemStatement", "")
    who_experiences = data.get("whoExperiences", "")
    impact = data.get("impact", "")
    current_solutions = data.get("currentSolutions", "")
    why_now = data.get("whyNow", "")
    camera_test = data.get("cameraTestPassed")

    # Store in session
    problem_data = {
        "statement": problem_statement,
        "who": who_experiences,
        "impact": impact,
        "current_solutions": current_solutions,
        "why_now": why_now,
        "camera_test_passed": camera_test
    }
    cl.user_session.set("problem_definition", problem_data)

    # Build response
    summary = f"""**📋 Problem Definition Captured**

**Problem:** {problem_statement}
**Who:** {who_experiences}"""

    if impact:
        summary += f"\n**Impact:** {impact}"
    if current_solutions:
        summary += f"\n**Current Solutions:** {current_solutions}"
    if why_now:
        summary += f"\n**Why Now:** {why_now}"

    # Add Camera Test feedback
    if camera_test is not None:
        if camera_test:
            summary += "\n\n✅ **Camera Test:** Passed - Your problem is observable."
        else:
            summary += "\n\n⚠️ **Camera Test:** Consider making this more observable. Can you describe what a camera would record?"

    summary += """

---

**Great start!** Now I can help you explore this problem deeper.

What would you like to do next?"""

    # Add to conversation history as context
    history = cl.user_session.get("history", [])
    history.append({
        "role": "user",
        "content": f"My problem: {problem_statement}\nWho experiences it: {who_experiences}"
    })
    cl.user_session.set("history", history)

    await cl.Message(
        content=summary,
        actions=[
            cl.Action(name="think_through", payload={}, label="🧠 Analyze Problem"),
            cl.Action(name="deep_research", payload={}, label="🔍 Research Context"),
            cl.Action(name="multi_agent_analysis", payload={}, label="👥 Get Expert Perspectives"),
        ]
    ).send()


@cl.action_callback("show_problem_form")
async def on_show_problem_form(action: cl.Action):
    """Show the Problem Definition form."""
    try:
        element = cl.CustomElement(
            name="ProblemDefinitionForm",
            props={
                "showCameraTest": True,
                "initialValues": {}
            }
        )

        await cl.Message(
            content="**Define your problem using the form below.**\n\n"
                    "A well-defined problem is half-solved. Be specific and observable.",
            elements=[element]
        ).send()
    except Exception as e:
        # Fallback to text-based input
        await cl.Message(
            content=f"**Define your problem:**\n\n"
                    f"Please describe:\n"
                    f"1. What is the problem? (be specific and observable)\n"
                    f"2. Who experiences it?\n"
                    f"3. What's the impact?\n"
                    f"4. How do people currently deal with it?"
        ).send()


@cl.action_callback("show_scenario_form")
async def on_show_scenario_form(action: cl.Action):
    """Show the Scenario Analysis setup form."""
    try:
        element = cl.CustomElement(
            name="ScenarioSetupForm",
            props={
                "initialValues": {}
            }
        )

        await cl.Message(
            content="**Set up your Scenario Analysis using the form below.**\n\n"
                    "This will help structure your exploration of possible futures.",
            elements=[element]
        ).send()
    except Exception as e:
        # Fallback to text-based input
        await cl.Message(
            content=f"**Scenario Analysis Setup:**\n\n"
                    f"Please tell me:\n"
                    f"1. What domain/industry are you exploring?\n"
                    f"2. What's your focal question (the decision you're trying to inform)?\n"
                    f"3. What time horizon (2030, 2035, 2040, 2050)?"
        ).send()


# === Analytics & Dashboard Callbacks ===

@cl.action_callback("show_feedback_dashboard")
async def on_show_feedback_dashboard(action: cl.Action):
    """Show the feedback analytics dashboard using native Chainlit feedback data."""

    async with cl.Step(name="Loading Feedback Analytics", type="tool") as step:
        step.input = "Fetching feedback data..."

        # Try to use the new MindrianDataLayer first (native Chainlit feedback)
        data_layer = await cl.data.get_data_layer()
        if data_layer and hasattr(data_layer, 'get_feedback_stats'):
            # Using MindrianDataLayer with built-in analytics
            stats = data_layer.get_feedback_stats()
            report = data_layer.export_feedback_report()
            step.output = f"Found {stats.get('total', 0)} feedback entries (from native data layer)"
            message = report
        else:
            # Fallback to old feedback module
            from utils.feedback import get_feedback_dashboard, format_dashboard_message
            dashboard = await get_feedback_dashboard(days=7)
            message = format_dashboard_message(dashboard)
            step.output = f"Found {dashboard.get('total_feedback', 0)} feedback entries (from Supabase)"

    await cl.Message(content=message).send()


@cl.action_callback("show_usage_metrics")
async def on_show_usage_metrics(action: cl.Action):
    """Show the usage metrics dashboard."""
    from utils.usage_metrics import get_usage_dashboard, format_usage_dashboard_message

    async with cl.Step(name="Loading Usage Metrics", type="tool") as step:
        step.input = "Fetching usage data from Supabase..."

        dashboard = await get_usage_dashboard(days=7)
        message = format_usage_dashboard_message(dashboard)

        step.output = f"Analyzed {dashboard.get('total_messages', 0)} messages"

    await cl.Message(content=message).send()


@cl.action_callback("generate_image")
async def on_generate_image(action: cl.Action):
    """Handle image generation request from action button."""
    from utils.image_generation import generate_image, save_image_to_temp, get_style_presets
    from utils.usage_metrics import track_image_generation

    # Get the prompt from payload or ask user
    prompt = action.payload.get("prompt") if action.payload else None

    if not prompt:
        # Send a message asking for the prompt
        await cl.Message(
            content="**Generate Image**\n\nPlease describe the image you want to create. For example:\n"
                    "- *A sunset over mountains with a lake reflection*\n"
                    "- *A futuristic city with flying cars*\n"
                    "- *A cozy coffee shop interior in watercolor style*\n\n"
                    "Type your description and I'll generate an image for you.",
            actions=[
                cl.Action(name="cancel_generation", payload={}, label="Cancel", tooltip="Cancel image generation")
            ]
        ).send()
        cl.user_session.set("awaiting_image_prompt", True)
        return

    # Generate the image
    async with cl.Step(name="Generating Image", type="tool") as step:
        step.input = f"Prompt: {prompt}"

        image_bytes, mime_type, metadata = await generate_image(
            prompt=prompt,
            model="fast",
            aspect_ratio="square"
        )

        if image_bytes:
            step.output = f"Image generated ({metadata.get('size_bytes', 0):,} bytes)"

            # Save to temp file for display
            temp_path = save_image_to_temp(image_bytes, mime_type)

            # Track usage
            context_key = get_context_key()
            track_image_generation(context_key)

            # Display the image
            await cl.Message(
                content=f"**Generated Image**\n\n*Prompt:* {prompt}",
                elements=[
                    cl.Image(name="generated_image", path=temp_path, display="inline")
                ],
                actions=[
                    cl.Action(
                        name="generate_image",
                        payload={"prompt": prompt},
                        label="Regenerate",
                        tooltip="Generate a new variation"
                    ),
                    cl.Action(
                        name="generate_image",
                        payload={},
                        label="New Image",
                        tooltip="Generate a different image"
                    )
                ]
            ).send()
        else:
            error_msg = metadata.get("user_message", metadata.get("error", "Unknown error"))
            step.output = f"Failed: {error_msg}"
            await cl.Message(content=f"**Image Generation Failed**\n\n{error_msg}").send()


@cl.action_callback("cancel_generation")
async def on_cancel_generation(action: cl.Action):
    """Cancel pending image generation."""
    cl.user_session.set("awaiting_image_prompt", False)
    await cl.Message(content="Image generation cancelled.").send()


# === Dynamic Agent Switching ===
# These callbacks handle the context-aware "Switch to X" buttons

@cl.action_callback("switch_to_tta")
async def on_switch_to_tta(action: cl.Action):
    await handle_agent_switch("tta")

@cl.action_callback("switch_to_jtbd")
async def on_switch_to_jtbd(action: cl.Action):
    await handle_agent_switch("jtbd")

@cl.action_callback("switch_to_scurve")
async def on_switch_to_scurve(action: cl.Action):
    await handle_agent_switch("scurve")

@cl.action_callback("switch_to_redteam")
async def on_switch_to_redteam(action: cl.Action):
    await handle_agent_switch("redteam")


# ═══════════════════════════════════════════════════════════════════════════════
# Quick Mode Toggle - Enable fast, direct answers
# ═══════════════════════════════════════════════════════════════════════════════
@cl.action_callback("toggle_quick_mode")
async def on_toggle_quick_mode(action: cl.Action):
    """Toggle Quick Mode for faster, more direct responses."""
    # Get current state
    quick_mode = cl.user_session.get("quick_mode", False)

    # Toggle
    quick_mode = not quick_mode
    cl.user_session.set("quick_mode", quick_mode)

    # Update settings to keep in sync
    settings = cl.user_session.get("settings", {})
    settings["quick_mode"] = quick_mode
    cl.user_session.set("settings", settings)

    # Determine new button label
    if quick_mode:
        mode_message = (
            "**Quick Mode: ON**\n\n"
            "I'll give you fast, direct answers:\n"
            "- Lead with the key insight\n"
            "- Max 3 bullet points\n"
            "- Skip the Socratic questions\n\n"
            "*Want depth on anything? Just ask!*"
        )
    else:
        mode_message = (
            "**Quick Mode: OFF**\n\n"
            "Back to Socratic exploration. I'll:\n"
            "- Ask probing questions\n"
            "- Help you think through problems\n"
            "- Guide discovery over answers"
        )

    # Send confirmation with updated toggle button
    await cl.Message(
        content=mode_message,
        actions=[
            cl.Action(
                name="toggle_quick_mode",
                payload={"action": "toggle"},
                label=f"{'OFF' if quick_mode else 'ON'} Quick Mode",
                tooltip="Toggle between fast answers and Socratic exploration"
            )
        ]
    ).send()


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 2: Conversation Forking - Branch management callbacks
# ═══════════════════════════════════════════════════════════════════════════════

@cl.action_callback("fork_conversation")
async def on_fork_conversation(action: cl.Action):
    """
    Create a new branch from the current conversation point.

    Triggered by:
    - "Fork Here" button on message hover
    - "Create Branch" in BranchSelector
    - Automatic fork suggestion after "what if" detection
    """
    from utils.forking_utils import (
        create_root_branch,
        create_new_branch,
        generate_branch_title,
    )
    from utils.context_persistence import save_cross_bot_context

    try:
        fork_at_index = action.payload.get("fork_at_index")
        custom_title = action.payload.get("title")
        copy_excluded = action.payload.get("copy_excluded_topics", True)

        # Get current state
        history = cl.user_session.get("history", [])
        bot_id = cl.user_session.get("bot_id", "lawrence")
        phases = cl.user_session.get("phases", [])
        current_phase = cl.user_session.get("current_phase", 0)
        excluded_topics = cl.user_session.get("excluded_topics", [])
        conversation_id = cl.user_session.get("conversation_id", str(uuid.uuid4()))

        # Determine fork point
        if fork_at_index is None:
            fork_at_index = len(history)  # Fork from current position

        # Get or create branch tree
        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            # First fork - create root branch from existing conversation
            branch_tree = create_root_branch(
                history=history,
                bot_id=bot_id,
                phases=phases,
                current_phase=current_phase,
                excluded_topics=excluded_topics,
                conversation_id=conversation_id,
            )
            parent_branch_id = branch_tree["root_branch_id"]
        else:
            parent_branch_id = branch_tree["active_branch_id"]

        # Generate branch title
        context = "\n".join([
            m.get("content", "")[:200]
            for m in history[max(0, fork_at_index-3):fork_at_index]
        ])
        parent_title = branch_tree["branches"][parent_branch_id]["title"]
        title = custom_title or generate_branch_title(
            context,
            parent_title,
            len(branch_tree["branches"])
        )

        # Create new branch
        new_branch_id = create_new_branch(
            branch_tree=branch_tree,
            parent_branch_id=parent_branch_id,
            fork_at_index=fork_at_index,
            title=title,
            bot_id=bot_id,
            phases=phases,
            current_phase=current_phase,
            excluded_topics=excluded_topics,
            copy_excluded=copy_excluded,
        )

        # Update session state
        cl.user_session.set("branch_tree", branch_tree)
        cl.user_session.set("active_branch_id", new_branch_id)
        cl.user_session.set("fork_points", branch_tree["fork_points"])
        cl.user_session.set("branch_history", [])

        # Persist to storage
        context_key = get_context_key()
        await save_cross_bot_context(
            user_key=context_key,
            history=history,
            bot_id=bot_id,
            bot_name=BOTS.get(bot_id, {}).get("name", "Bot"),
            phases=phases,
            current_phase=current_phase,
            conversation_id=conversation_id,
            excluded_topics=excluded_topics,
            branch_tree=branch_tree,
            active_branch_id=new_branch_id,
        )

        # Show confirmation
        await cl.Message(
            content=f"**🌿 Branch Created: {title}**\n\n"
                    f"Forked from *{parent_title}* at message {fork_at_index}.\n\n"
                    "Continue exploring this path. Your original conversation is preserved.",
            actions=[
                cl.Action(
                    name="show_branch_selector",
                    payload={},
                    label="View All Branches",
                    tooltip="See all conversation branches"
                ),
                cl.Action(
                    name="switch_branch",
                    payload={"branch_id": parent_branch_id},
                    label=f"← Back to {parent_title}",
                    tooltip="Return to the original branch"
                ),
            ]
        ).send()

        print(f"[FORKING] Created branch '{title}' from message {fork_at_index}")

    except Exception as e:
        print(f"Fork error: {e}")
        await cl.Message(content=f"Unable to create branch: {str(e)[:100]}").send()


@cl.action_callback("switch_branch")
async def on_switch_branch(action: cl.Action):
    """Switch to a different conversation branch."""
    from utils.forking_utils import switch_to_branch, get_composed_history
    from utils.context_persistence import save_cross_bot_context

    try:
        target_branch_id = action.payload.get("branch_id")

        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            await cl.Message(content="No branches exist yet.").send()
            return

        target_branch = branch_tree["branches"].get(target_branch_id)
        if not target_branch:
            await cl.Message(content="Branch not found.").send()
            return

        current_branch_id = branch_tree["active_branch_id"]
        if current_branch_id == target_branch_id:
            await cl.Message(content=f"Already on branch: {target_branch['title']}").send()
            return

        # Save current branch state and switch
        current_session = {
            "branch_history": cl.user_session.get("branch_history", []),
            "bot_id": cl.user_session.get("bot_id"),
            "phases": cl.user_session.get("phases", []),
            "current_phase": cl.user_session.get("current_phase", 0),
            "excluded_topics": cl.user_session.get("excluded_topics", []),
        }

        branch_tree = switch_to_branch(branch_tree, target_branch_id, current_session)

        # Restore target branch state
        cl.user_session.set("branch_tree", branch_tree)
        cl.user_session.set("active_branch_id", target_branch_id)
        cl.user_session.set("branch_history", target_branch.get("history", []))
        cl.user_session.set("bot_id", target_branch.get("bot_id", "lawrence"))
        cl.user_session.set("phases", target_branch.get("phases", []))
        cl.user_session.set("current_phase", target_branch.get("current_phase", 0))
        cl.user_session.set("excluded_topics", target_branch.get("excluded_topics", []))

        # Compose full history for LLM context
        # Use the branch's history directly (forking utils composes internally)
        composed_history = []
        parent_id = target_branch.get("parent_branch_id")
        if parent_id:
            parent = branch_tree["branches"].get(parent_id, {})
            fork_point = target_branch.get("fork_point_message_index", 0)
            shared_history = parent.get("history", [])[:fork_point]
            composed_history = shared_history + target_branch.get("history", [])
        else:
            composed_history = target_branch.get("history", [])

        cl.user_session.set("history", composed_history)

        # Persist
        context_key = get_context_key()
        bot_id = target_branch.get("bot_id", "lawrence")
        await save_cross_bot_context(
            user_key=context_key,
            history=composed_history,
            bot_id=bot_id,
            bot_name=BOTS.get(bot_id, {}).get("name", "Bot"),
            phases=target_branch.get("phases"),
            current_phase=target_branch.get("current_phase", 0),
            conversation_id=cl.user_session.get("conversation_id"),
            excluded_topics=target_branch.get("excluded_topics", []),
            branch_tree=branch_tree,
            active_branch_id=target_branch_id,
        )

        # Get previous branch name for message
        current_branch = branch_tree["branches"].get(current_branch_id, {})

        await cl.Message(
            content=f"**Switched to: {target_branch['title']}**\n\n"
                    f"Left *{current_branch.get('title', 'previous branch')}* (paused).\n"
                    f"This branch has {target_branch.get('message_count', 0)} messages.",
            actions=[
                cl.Action(
                    name="show_branch_selector",
                    payload={},
                    label="View All Branches",
                    tooltip="See all conversation branches"
                ),
            ]
        ).send()

        print(f"[FORKING] Switched from '{current_branch.get('title')}' to '{target_branch['title']}'")

    except Exception as e:
        print(f"Switch branch error: {e}")
        await cl.Message(content=f"Unable to switch branch: {str(e)[:100]}").send()


@cl.action_callback("delete_branch")
async def on_delete_branch(action: cl.Action):
    """Delete (archive) a conversation branch."""
    from utils.forking_utils import can_delete_branch, archive_branch
    from utils.context_persistence import save_cross_bot_context

    try:
        branch_id = action.payload.get("branch_id")
        permanent = action.payload.get("permanent", False)

        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            await cl.Message(content="No branches exist.").send()
            return

        # Check if we can delete
        can_delete, reason = can_delete_branch(branch_tree, branch_id)
        if not can_delete:
            await cl.Message(
                content=reason,
                actions=[cl.Action(name="show_branch_selector", payload={}, label="View Branches")]
            ).send()
            return

        branch = branch_tree["branches"].get(branch_id)
        if not branch:
            await cl.Message(content="Branch not found.").send()
            return

        branch_title = branch.get("title", "Unknown")

        # Archive (soft delete)
        branch_tree = archive_branch(branch_tree, branch_id)
        cl.user_session.set("branch_tree", branch_tree)

        # Persist
        context_key = get_context_key()
        await save_cross_bot_context(
            user_key=context_key,
            history=cl.user_session.get("history", []),
            bot_id=cl.user_session.get("bot_id", "lawrence"),
            bot_name=BOTS.get(cl.user_session.get("bot_id", "lawrence"), {}).get("name", "Bot"),
            phases=cl.user_session.get("phases"),
            current_phase=cl.user_session.get("current_phase", 0),
            conversation_id=cl.user_session.get("conversation_id"),
            excluded_topics=cl.user_session.get("excluded_topics", []),
            branch_tree=branch_tree,
            active_branch_id=cl.user_session.get("active_branch_id"),
        )

        await cl.Message(
            content=f"**Branch Archived:** {branch_title}\n\nYou can still access it from the branch selector.",
            actions=[cl.Action(name="show_branch_selector", payload={}, label="View Branches")]
        ).send()

        print(f"[FORKING] Archived branch '{branch_title}'")

    except Exception as e:
        print(f"Delete branch error: {e}")
        await cl.Message(content=f"Unable to delete branch: {str(e)[:100]}").send()


@cl.action_callback("show_branch_selector")
async def on_show_branch_selector(action: cl.Action):
    """Display the BranchSelector custom element."""
    branch_tree = cl.user_session.get("branch_tree")

    if not branch_tree or len(branch_tree["branches"]) <= 1:
        await cl.Message(
            content="No branches yet. Use the **Fork** button to create a branch for exploring alternative directions.",
            actions=[
                cl.Action(
                    name="fork_conversation",
                    payload={},
                    label="🌿 Create Branch",
                    tooltip="Fork the conversation to explore a 'what if' scenario"
                )
            ]
        ).send()
        return

    # Create BranchSelector element
    selector = cl.CustomElement(
        name="BranchSelector",
        props={
            "branches": list(branch_tree["branches"].values()),
            "activeBranchId": branch_tree["active_branch_id"],
            "rootBranchId": branch_tree["root_branch_id"],
            "forkPoints": branch_tree["fork_points"],
        },
        display="inline"
    )

    await cl.Message(content="", elements=[selector]).send()


@cl.action_callback("merge_branches")
async def on_merge_branches(action: cl.Action):
    """Merge insights from one branch into another."""
    from utils.forking_merge import extract_and_merge_insights, create_merge_message
    from utils.context_persistence import save_cross_bot_context

    try:
        source_id = action.payload.get("source_branch_id")
        target_id = action.payload.get("target_branch_id")
        archive_source = action.payload.get("archive_source", True)

        branch_tree = cl.user_session.get("branch_tree")
        if not branch_tree:
            await cl.Message(content="No branches to merge.").send()
            return

        source_branch = branch_tree["branches"].get(source_id)
        target_branch = branch_tree["branches"].get(target_id)

        if not source_branch or not target_branch:
            await cl.Message(content="Source or target branch not found.").send()
            return

        # Show merging status
        msg = cl.Message(content="Merging branches...")
        await msg.send()

        # Extract insights using LLM
        source_history = source_branch.get("history", [])
        target_history = target_branch.get("history", [])

        merge_result = await extract_and_merge_insights(
            source_history=source_history,
            target_history=target_history,
            source_title=source_branch["title"],
            target_title=target_branch["title"],
        )

        if merge_result["success"]:
            # Create merge message and add to target branch
            merge_msg = create_merge_message(
                source_title=source_branch["title"],
                insights=merge_result["insights_merged"],
                conflicts=merge_result["conflicts"],
                summary=merge_result["merge_summary"],
            )

            target_branch["history"].append(merge_msg)
            target_branch["message_count"] = len(target_branch["history"])
            target_branch["last_activity"] = datetime.utcnow().isoformat()

            # Archive source branch if requested
            if archive_source:
                source_branch["status"] = "merged"
                source_branch["merge_target"] = target_id

            branch_tree["last_modified"] = datetime.utcnow().isoformat()
            cl.user_session.set("branch_tree", branch_tree)

            # Persist
            context_key = get_context_key()
            await save_cross_bot_context(
                user_key=context_key,
                history=cl.user_session.get("history", []),
                bot_id=cl.user_session.get("bot_id", "lawrence"),
                bot_name=BOTS.get(cl.user_session.get("bot_id", "lawrence"), {}).get("name", "Bot"),
                phases=cl.user_session.get("phases"),
                current_phase=cl.user_session.get("current_phase", 0),
                conversation_id=cl.user_session.get("conversation_id"),
                excluded_topics=cl.user_session.get("excluded_topics", []),
                branch_tree=branch_tree,
                active_branch_id=cl.user_session.get("active_branch_id"),
            )

            # Show result
            insights_list = "\n".join(f"• {i}" for i in merge_result["insights_merged"][:5])
            conflicts_section = ""
            if merge_result["conflicts"]:
                conflicts_list = "\n".join(f"⚠️ {c}" for c in merge_result["conflicts"][:3])
                conflicts_section = f"\n\n**Differences Noted:**\n{conflicts_list}"

            await msg.remove()
            await cl.Message(
                content=f"**✅ Merge Complete**\n\n"
                        f"Merged insights from *{source_branch['title']}* into *{target_branch['title']}*.\n\n"
                        f"**Key Insights Merged:**\n{insights_list}{conflicts_section}",
                actions=[
                    cl.Action(
                        name="switch_branch",
                        payload={"branch_id": target_id},
                        label=f"Go to {target_branch['title']}",
                    ),
                    cl.Action(
                        name="show_branch_selector",
                        payload={},
                        label="View All Branches",
                    ),
                ]
            ).send()

            print(f"[FORKING] Merged '{source_branch['title']}' into '{target_branch['title']}'")

        else:
            await msg.remove()
            await cl.Message(content=f"Merge failed: {merge_result.get('error', 'Unknown error')}").send()

    except Exception as e:
        print(f"Merge error: {e}")
        await cl.Message(content=f"Unable to merge branches: {str(e)[:100]}").send()


# ═══════════════════════════════════════════════════════════════════════════════
# PWS Navigator - Cross-Domain Bridge Detection
# ═══════════════════════════════════════════════════════════════════════════════

@cl.action_callback("pws_navigate")
async def on_pws_navigate(action: cl.Action):
    """PWS Navigator: Cross-domain bridge detection and innovation discovery."""
    history = cl.user_session.get("history", [])

    # Extract query from conversation or use a default
    query = ""
    for msg in reversed(history):
        if msg.get("role") == "user" and len(msg.get("content", "")) > 5:
            query = msg["content"][:200]
            break

    if not query:
        await cl.Message(
            content="Start a conversation first, then click PWS Navigator to discover cross-domain connections."
        ).send()
        return

    try:
        async with cl.Step(name="PWS Navigator", type="tool") as nav_step:
            nav_step.input = f"Exploring cross-domain bridges for: {query[:100]}..."

            from tools.pws_navigator import (
                cross_domain_discovery,
                format_discovery_as_markdown,
                discovery_to_mermaid,
            )

            discovery = cross_domain_discovery(query)
            markdown = format_discovery_as_markdown(discovery)
            mermaid_code = discovery_to_mermaid(discovery)

            nav_step.output = f"Found {len(discovery.get('cross_domain_bridges', []))} cross-domain connections"

        # Send results
        elements = []
        if mermaid_code:
            try:
                from utils.diagrams import create_mermaid_element
                diagram = await create_mermaid_element(mermaid_code, title="Cross-Domain Map")
                elements.append(diagram)
            except Exception:
                pass

        # Add explore buttons for discovered domains
        actions = []
        for xd in discovery.get("cross_domain_bridges", [])[:3]:
            target = xd.get("target_domain", {})
            label = target.get("label", "Unknown")
            actions.append(cl.Action(
                name="pws_explore_bridge",
                payload={"domain": label, "community": target.get("community", 0)},
                label=f"Explore: {label[:25]}",
                tooltip=f"Deep-dive into bridges with {label}",
            ))

        await cl.Message(content=markdown, elements=elements, actions=actions).send()

    except Exception as e:
        logger.error("PWS Navigator error: %s", e)
        await cl.Message(content=f"PWS Navigator encountered an error: {e}").send()


@cl.action_callback("pws_explore_bridge")
async def on_pws_explore_bridge(action: cl.Action):
    """Deep-dive into a specific cross-domain bridge."""
    domain_name = action.payload.get("domain", "")
    history = cl.user_session.get("history", [])

    # Get original query
    query = ""
    for msg in reversed(history):
        if msg.get("role") == "user" and len(msg.get("content", "")) > 5:
            query = msg["content"][:200]
            break

    if not query or not domain_name:
        return

    try:
        async with cl.Step(name=f"Bridge Analysis: {domain_name}", type="tool") as step:
            from tools.pws_navigator import find_bridges_by_name
            result = find_bridges_by_name(query, domain_name)

            bridges = result.get("bridges", [])
            step.output = f"Found {len(bridges)} bridge concepts"

        # Format output
        lines = [f"## Bridge Analysis: {query[:50]} <> {domain_name}", ""]

        d1 = result.get("domain1", {})
        d2 = result.get("domain2", {})
        if d1.get("top_concepts"):
            lines.append(f"**Domain 1**: {', '.join(d1['top_concepts'][:4])}")
        if d2.get("top_concepts"):
            lines.append(f"**Domain 2**: {', '.join(d2['top_concepts'][:4])}")
        lines.append("")

        if bridges and isinstance(bridges[0], dict) and bridges[0].get("note"):
            lines.append(bridges[0]["note"])
        elif bridges:
            lines.append("### Bridge Concepts")
            for b in bridges[:5]:
                c1 = b.get("c1_connections", [])
                c2 = b.get("c2_connections", [])
                lines.append(f"- **{b['name']}** (score: {b.get('bridge_score', 0):.0f}) "
                             f"connects {', '.join(c1[:2])} with {', '.join(c2[:2])}")
            lines.append("")

        prompts = result.get("innovation_prompts", [])
        if prompts:
            lines.append("### Innovation Questions")
            for p in prompts:
                lines.append(f"> {p}")

        await cl.Message(content="\n".join(lines)).send()

    except Exception as e:
        logger.error("Bridge exploration error: %s", e)
        await cl.Message(content=f"Bridge analysis error: {e}").send()


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 3: Idea Canvas - Extracted ideas visualization
# ═══════════════════════════════════════════════════════════════════════════════

@cl.action_callback("show_idea_canvas")
async def on_show_idea_canvas(action: cl.Action):
    """Display the IdeaCanvas custom element."""
    canvas_state = cl.user_session.get("canvas_state")

    if not canvas_state or not canvas_state.get("idea_nodes"):
        await cl.Message(
            content="No ideas extracted yet. Ideas will appear as you explore topics in conversation.",
            actions=[
                cl.Action(
                    name="extract_ideas_now",
                    payload={},
                    label="🔍 Extract Ideas Now",
                    tooltip="Analyze conversation for ideas"
                )
            ]
        ).send()
        return

    # Create IdeaCanvas element
    canvas = cl.CustomElement(
        name="IdeaCanvas",
        props={
            "nodes": list(canvas_state["idea_nodes"].values()),
            "layout": canvas_state["layout"],
            "viewMode": canvas_state["view_mode"],
            "filters": canvas_state["filters"],
            "currentBranchId": canvas_state.get("current_branch_id", "main"),
            "title": "Idea Canvas",
            "editable": True,
        },
        display="inline"
    )

    await cl.Message(content="", elements=[canvas]).send()


@cl.action_callback("star_idea")
async def on_star_idea(action: cl.Action):
    """Toggle star status on an idea."""
    try:
        node_id = action.payload.get("node_id")
        print(f"[STAR_IDEA] Received node_id: {node_id}")

        canvas_state = cl.user_session.get("canvas_state")
        if not canvas_state:
            # Try to initialize from stored data
            try:
                from tools.idea_canvas import init_canvas_state, load_canvas_state
                session_id = str(cl.user_session.get("id", "anonymous"))

                # Try loading from persistence first
                canvas_state = await load_canvas_state(session_id)
                if not canvas_state:
                    canvas_state = init_canvas_state(session_id, "main")

                cl.user_session.set("canvas_state", canvas_state)
                print(f"[STAR_IDEA] Initialized canvas_state with {len(canvas_state.get('idea_nodes', {}))} nodes")
            except Exception as e:
                print(f"[STAR_IDEA] Failed to init canvas: {e}")
                await cl.Message(content="No canvas state. Try extracting ideas first.").send()
                return

        idea_nodes = canvas_state.get("idea_nodes", {})
        print(f"[STAR_IDEA] idea_nodes keys: {list(idea_nodes.keys())[:5]}...")

        if node_id not in idea_nodes:
            print(f"[STAR_IDEA] node_id {node_id} not in idea_nodes")
            await cl.Message(content=f"Idea not found: {node_id}").send()
            return

        node = idea_nodes[node_id]
        node["starred"] = not node.get("starred", False)

        cl.user_session.set("canvas_state", canvas_state)

        # Try to save, but don't fail if save_canvas_state doesn't exist
        try:
            from tools.idea_canvas import save_canvas_state
            await save_canvas_state(canvas_state)
        except ImportError:
            print("[STAR_IDEA] save_canvas_state not available, skipping persist")

        status = "⭐ Starred" if node["starred"] else "Unstarred"
        await cl.Message(
            content=f"{status}: {node.get('content', 'idea')[:60]}...",
        ).send()
    except Exception as e:
        print(f"[STAR_IDEA] Error: {e}")
        await cl.Message(content=f"Star error: {str(e)[:100]}").send()


@cl.action_callback("prune_idea")
async def on_prune_idea(action: cl.Action):
    """Mark an idea as pruned (dead end)."""
    try:
        node_id = action.payload.get("node_id")
        print(f"[PRUNE_IDEA] Received node_id: {node_id}")

        canvas_state = cl.user_session.get("canvas_state")
        if not canvas_state:
            print("[PRUNE_IDEA] No canvas_state in session")
            await cl.Message(content="No canvas state. Try extracting ideas first.").send()
            return

        idea_nodes = canvas_state.get("idea_nodes", {})
        if node_id not in idea_nodes:
            print(f"[PRUNE_IDEA] node_id {node_id} not in idea_nodes")
            await cl.Message(content=f"Idea not found: {node_id}").send()
            return

        node = idea_nodes[node_id]
        node["pruned"] = True

        # Cascade prune to children
        def prune_children(nid):
            for child_id in idea_nodes.get(nid, {}).get("child_node_ids", []):
                if child_id in idea_nodes:
                    idea_nodes[child_id]["pruned"] = True
                    prune_children(child_id)

        prune_children(node_id)

        cl.user_session.set("canvas_state", canvas_state)

        # Try to save, but don't fail if save_canvas_state doesn't exist
        try:
            from tools.idea_canvas import save_canvas_state
            await save_canvas_state(canvas_state)
        except ImportError:
            print("[PRUNE_IDEA] save_canvas_state not available, skipping persist")

        await cl.Message(
            content=f"🗑️ Pruned: {node.get('content', 'idea')[:50]}...",
        ).send()
    except Exception as e:
        print(f"[PRUNE_IDEA] Error: {e}")
        await cl.Message(content=f"Prune error: {str(e)[:100]}").send()

    children_count = len(node.get("child_node_ids", []))
    child_text = f" (and {children_count} children)" if children_count > 0 else ""
    await cl.Message(
        content=f"🗑️ Pruned: {node['content'][:50]}...{child_text}",
        author="system"
    ).send()


@cl.action_callback("canvas_layout_updated")
async def on_canvas_layout_updated(action: cl.Action):
    """Save new node positions from drag-and-drop."""
    from tools.idea_canvas import save_canvas_state
    from datetime import datetime

    positions = action.payload.get("positions", {})
    canvas_state = cl.user_session.get("canvas_state")

    if not canvas_state:
        return

    canvas_state["layout"]["positions"] = positions
    canvas_state["last_updated"] = datetime.utcnow().isoformat()

    cl.user_session.set("canvas_state", canvas_state)
    await save_canvas_state(canvas_state)


@cl.action_callback("canvas_node_selected")
async def on_canvas_node_selected(action: cl.Action):
    """Handle node selection - show source context."""
    node_id = action.payload.get("node_id")
    message_index = action.payload.get("message_index")

    canvas_state = cl.user_session.get("canvas_state")
    if not canvas_state or node_id not in canvas_state.get("idea_nodes", {}):
        return

    node = canvas_state["idea_nodes"][node_id]
    history = cl.user_session.get("history", [])

    # Get source message context
    source_context = ""
    if message_index is not None and message_index < len(history):
        msg = history[message_index]
        source_context = f"\n\n**Source ({node.get('source_role', 'unknown')}):**\n> {msg.get('content', '')[:300]}..."

    await cl.Message(
        content=f"**{node.get('node_type', 'idea').upper()}**: {node['content']}{source_context}",
        actions=[
            cl.Action(
                name="star_idea",
                payload={"node_id": node_id},
                label="⭐ Star" if not node.get("starred") else "★ Unstar",
            ),
            cl.Action(
                name="prune_idea",
                payload={"node_id": node_id},
                label="🗑️ Prune",
            ),
        ]
    ).send()


@cl.action_callback("extract_ideas_now")
async def on_extract_ideas_now(action: cl.Action):
    """Manually trigger idea extraction from conversation history."""
    from tools.idea_canvas import (
        background_extract_ideas,
        link_idea_parents,
        init_canvas_state,
        auto_layout,
        save_canvas_state,
    )
    from datetime import datetime

    history = cl.user_session.get("history", [])
    if len(history) < 2:
        await cl.Message(content="Not enough conversation to extract ideas from. Keep chatting!").send()
        return

    msg = cl.Message(content="🔍 Analyzing conversation for ideas...")
    await msg.send()

    # Get or create canvas state
    canvas_state = cl.user_session.get("canvas_state")
    if not canvas_state:
        session_id = cl.user_session.get("id") or str(uuid.uuid4())
        branch_id = cl.user_session.get("active_branch_id") or "main"
        canvas_state = init_canvas_state(session_id, branch_id)

    branch_id = canvas_state.get("current_branch_id", "main")

    # Extract ideas from recent messages
    all_ideas = []
    recent_history = history[-20:]  # Last 20 messages

    for i, msg_data in enumerate(recent_history):
        role = msg_data.get("role", "user")
        if role == "model":
            role = "assistant"
        content = msg_data.get("content", "")

        if len(content) > 50:  # Skip very short messages
            ideas = await background_extract_ideas(
                message_content=content,
                message_role=role,
                message_index=len(history) - len(recent_history) + i,
                message_id=str(i),
                branch_id=branch_id,
                conversation_context=""
            )
            all_ideas.extend(ideas)

    # LIMIT to top 10 ideas with PWS-aware ranking (BUG-104: 52 ideas is too many)
    if len(all_ideas) > 10:
        # PWS-aware scoring: prioritize problems worth solving
        def pws_score(idea):
            score = idea.get("confidence", 0.5)
            content = idea.get("content", "").lower()
            node_type = idea.get("node_type", "")

            # Boost problems and insights (PWS core)
            if node_type == "problem":
                score += 0.3
            elif node_type == "insight":
                score += 0.2

            # Boost ideas with PWS keywords
            pws_keywords = ["opportunity", "gap", "need", "pain", "struggle", "worth solving",
                           "market", "customer", "value", "solution", "assumption"]
            for kw in pws_keywords:
                if kw in content:
                    score += 0.1

            # Penalize generic/vague ideas
            vague_keywords = ["something", "maybe", "might", "could be", "perhaps"]
            for kw in vague_keywords:
                if kw in content:
                    score -= 0.1

            # Boost longer, more substantive ideas (more context)
            if len(content) > 100:
                score += 0.1
            if len(content) > 200:
                score += 0.1

            return score

        all_ideas = sorted(all_ideas, key=pws_score, reverse=True)[:10]
        print(f"[EXTRACT_IDEAS] Filtered {len(all_ideas)} ideas from original set using PWS ranking")

    # Add to canvas state
    for idea in all_ideas:
        canvas_state["idea_nodes"][idea["node_id"]] = idea

    # Link parents
    parent_hints = [idea.get("metadata", {}).get("parent_hint", "") for idea in all_ideas]
    link_idea_parents(all_ideas, canvas_state["idea_nodes"], parent_hints)

    # Calculate layout
    canvas_state["layout"]["positions"] = auto_layout(
        list(canvas_state["idea_nodes"].values()),
        canvas_state["view_mode"]
    )
    canvas_state["last_updated"] = datetime.utcnow().isoformat()

    cl.user_session.set("canvas_state", canvas_state)
    await save_canvas_state(canvas_state)

    await msg.remove()
    await cl.Message(
        content=f"✨ Extracted {len(all_ideas)} ideas from conversation!",
        actions=[
            cl.Action(
                name="show_idea_canvas",
                payload={},
                label="🎨 View Canvas",
            )
        ]
    ).send()


@cl.action_callback("export_canvas")
async def on_export_canvas(action: cl.Action):
    """Export canvas to markdown."""
    from tools.idea_canvas import export_canvas_to_markdown

    canvas_state = cl.user_session.get("canvas_state")
    if not canvas_state or not canvas_state.get("idea_nodes"):
        await cl.Message(content="No ideas to export. Use the canvas first!").send()
        return

    markdown = export_canvas_to_markdown(canvas_state)

    # Create downloadable file
    from utils.media import create_downloadable_file
    file_elem = await create_downloadable_file(
        content=markdown,
        filename="idea_canvas_export.md",
        content_type="text/markdown"
    )

    await cl.Message(
        content="📥 **Canvas Exported**\n\nDownload your idea canvas as markdown.",
        elements=[file_elem] if file_elem else []
    ).send()


@cl.action_callback("creative_leaps")
async def on_creative_leaps(action: cl.Action):
    """
    Find unexpected cross-domain connections for innovation.

    Based on Austin Granmoe's research: interclass edges between different
    modularity classes reveal non-obvious connections that drive innovation.
    """
    from tools.graphrag_lite import find_creative_leaps, _extract_keywords

    # Get concept from payload or extract from recent conversation
    concept = action.payload.get("concept", "")

    if not concept:
        history = cl.user_session.get("history", [])
        if history:
            # Extract keywords from last few messages
            recent_text = " ".join([
                m.get("content", "") for m in history[-3:]
                if m.get("role") == "user"
            ])[:500]
            keywords = _extract_keywords(recent_text)
            if keywords:
                concept = keywords[0].title()

    if not concept:
        await cl.Message(
            content="💡 **No topic detected.**\n\nTry discussing a specific concept first, then click Creative Leaps to find unexpected connections."
        ).send()
        return

    # Show thinking step
    async with cl.Step(name="Finding Creative Leaps", type="tool") as step:
        step.input = f"Searching for unexpected connections from: {concept}"
        leaps_result = find_creative_leaps(concept, limit=5, min_community_distance=2)
        step.output = f"Found {len(leaps_result.get('leaps', []))} creative connections"

    leaps = leaps_result.get("leaps", [])
    src_community = leaps_result.get("source_community")

    if not leaps:
        await cl.Message(
            content=f"💡 **No strong cross-domain connections found for \"{concept}\".**\n\n"
                    f"This topic may be well-contained within its domain, or try a more specific concept."
        ).send()
        return

    # Build rich response with innovation questions
    lines = [
        f"## 💡 Creative Leaps from \"{concept}\"",
        "",
        f"*Your topic is in Community {src_community}. Here are connections to distant domains:*",
        ""
    ]

    actions = []
    for i, leap in enumerate(leaps[:3], 1):
        lines.append(f"### {i}. {leap['name']} (Community {leap['community']})")
        lines.append(f"- **Distance:** {leap['community_distance']} communities away")
        lines.append(f"- **Connection strength:** {leap['weight']:.1f} co-occurrences")
        lines.append(f"- **Leap score:** {leap['leap_score']:.1f} (higher = more surprising)")
        lines.append("")

        # Add explore button for each leap
        actions.append(cl.Action(
            name="explore_creative_leap",
            payload={"source": concept, "target": leap["name"]},
            label=f"🔍 Explore {leap['name'][:15]}...",
        ))

    # Add innovation questions
    innovation_qs = leaps_result.get("innovation_questions", [])
    if innovation_qs:
        lines.append("---")
        lines.append("### 🤔 Innovation Questions")
        for q in innovation_qs[:3]:
            lines.append(f"> {q}")
        lines.append("")

    lines.append("*Based on Austin Granmoe's research on interclass edges in knowledge networks.*")

    await cl.Message(
        content="\n".join(lines),
        actions=actions
    ).send()


@cl.action_callback("explore_creative_leap")
async def on_explore_creative_leap(action: cl.Action):
    """Explore the connection between two concepts from a creative leap."""
    source = action.payload.get("source", "")
    target = action.payload.get("target", "")

    if not source or not target:
        await cl.Message(content="Missing concepts to explore.").send()
        return

    # Inject as a question to Larry
    exploration_prompt = (
        f"I found a creative connection between **{source}** and **{target}** - "
        f"two concepts from very different domains. Help me explore: "
        f"What principles or patterns from {target} could be applied to {source}? "
        f"What unexpected insights might emerge from this cross-domain connection?"
    )

    history = cl.user_session.get("history", [])
    history.append({"role": "user", "content": exploration_prompt})
    cl.user_session.set("history", history)

    # Trigger the main message handler by sending as user message
    await cl.Message(
        content=f"🔗 **Exploring creative leap:** {source} ↔ {target}\n\n{exploration_prompt}",
        author="user"
    ).send()


@cl.action_callback("apply_idea_context")
async def on_apply_idea_context(action: cl.Action):
    """
    Apply starred/pruned ideas as focus areas and exclusions for AI responses.

    Starred ideas → Focus areas (positive context injection)
    Pruned ideas → Topics to avoid (negative prompt injection)

    Implements swarm-recommended "Focus/Park" semantic framing.
    """
    starred_ids = action.payload.get("starred_ids", [])
    pruned_ids = action.payload.get("pruned_ids", [])

    canvas_state = cl.user_session.get("canvas_state")
    if not canvas_state:
        await cl.Message(content="No canvas state found. Extract ideas first!").send()
        return

    idea_nodes = canvas_state.get("idea_nodes", {})

    # Extract content from starred ideas (limit to 10 for prompt size)
    focus_ideas = []
    for node_id in starred_ids[:10]:
        node = idea_nodes.get(node_id)
        if node:
            focus_ideas.append({
                "type": node.get("node_type", "idea"),
                "content": node.get("content", "")[:200],
            })

    # Extract content from pruned ideas (limit to 10 for prompt size)
    avoid_ideas = []
    for node_id in pruned_ids[:10]:
        node = idea_nodes.get(node_id)
        if node:
            avoid_ideas.append({
                "type": node.get("node_type", "idea"),
                "content": node.get("content", "")[:200],
            })

    # Store in session for injection into system prompt
    cl.user_session.set("idea_focus_context", focus_ideas)
    cl.user_session.set("idea_avoid_context", avoid_ideas)

    # Build confirmation message
    focus_summary = ""
    if focus_ideas:
        focus_items = [f"• **{i['type']}**: {i['content'][:60]}..." for i in focus_ideas[:5]]
        focus_summary = "**🎯 Focus areas:**\n" + "\n".join(focus_items)
        if len(focus_ideas) > 5:
            focus_summary += f"\n*...and {len(focus_ideas) - 5} more*"

    avoid_summary = ""
    if avoid_ideas:
        avoid_items = [f"• ~~{i['content'][:50]}...~~" for i in avoid_ideas[:3]]
        avoid_summary = "**🚫 Avoiding:**\n" + "\n".join(avoid_items)
        if len(avoid_ideas) > 3:
            avoid_summary += f"\n*...and {len(avoid_ideas) - 3} more*"

    message = "✅ **Idea Context Applied!**\n\n"
    if focus_summary:
        message += focus_summary + "\n\n"
    if avoid_summary:
        message += avoid_summary + "\n\n"
    message += "*The AI will now prioritize your starred ideas and avoid pruned topics.*"

    await cl.Message(
        content=message,
        actions=[
            cl.Action(
                name="clear_idea_context",
                payload={},
                label="🔄 Clear Context",
                tooltip="Remove focus/avoid filters",
            ),
            cl.Action(
                name="show_idea_canvas",
                payload={"action": "ideas"},
                label="🎨 View Canvas",
            ),
        ]
    ).send()


@cl.action_callback("clear_idea_context")
async def on_clear_idea_context(action: cl.Action):
    """Clear the applied idea focus/avoid context."""
    cl.user_session.set("idea_focus_context", None)
    cl.user_session.set("idea_avoid_context", None)

    await cl.Message(
        content="🔄 **Idea context cleared.**\n\nThe AI will no longer use starred/pruned ideas for filtering.",
    ).send()


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# WAVE 5: Orchestration Middleware — Accept/Dismiss callbacks
# ═══════════════════════════════════════════════════════════════════════════════

@cl.action_callback("accept_orchestration")
async def on_accept_orchestration(action: cl.Action):
    """User confirmed orchestration recommendation — run the workflow."""
    try:
        from protocols.auto_orchestrator import AutoOrchestrator, OrchestratorStatus
        from protocols.orchestration_middleware import record_orchestration_run
    except ImportError as e:
        await cl.Message(content=f"Orchestration unavailable: {e}").send()
        return

    workflow_type = action.payload.get("workflow_type", "full_analysis")
    agents = action.payload.get("agents", [])
    query = action.payload.get("query", "")

    if not query:
        history = cl.user_session.get("history", [])
        for msg_item in reversed(history):
            if msg_item.get("role") == "user":
                query = msg_item.get("content", "")
                break

    if not query:
        await cl.Message(content="Please describe what you're working on first.").send()
        return

    session_id = cl.user_session.get("id", "")
    history = cl.user_session.get("history", [])
    turn_count = len(history)

    # Record that orchestration is running (for cooldown)
    record_orchestration_run(str(session_id), turn_count)

    # Show progress
    progress_msg = await cl.Message(
        content=f"🚀 **Running {workflow_type.replace('_', ' ').title()} Analysis**\n\n"
                f"Agents: {', '.join(agents[:4])}\n\n"
                f"*This may take 1-3 minutes...*"
    ).send()

    # Run orchestration
    async def progress_callback(info):
        stage = info.get("stage", 0) + 1
        total = info.get("total", 1)
        task = info.get("task", "Processing")
        current_agents = info.get("agents", [])
        try:
            progress_msg.content = (
                f"🚀 **Running {workflow_type.replace('_', ' ').title()} Analysis**\n\n"
                f"Stage {stage}/{total}: {task}\n"
                f"Agents: {', '.join(current_agents)}\n\n"
                f"{'█' * stage}{'░' * (total - stage)} {stage}/{total}"
            )
            await progress_msg.update()
        except Exception:
            pass

    orchestrator = AutoOrchestrator(
        session_id=str(session_id),
        progress_callback=progress_callback,
    )
    state = await orchestrator.run(query, workflow_override=workflow_type, history=history)

    # Show results
    if state.synthesis and isinstance(state.synthesis, dict):
        synthesis_content = state.synthesis.get("content", "No synthesis generated.")
        agents_used = state.synthesis.get("agents_used", agents)
        duration_ms = state.synthesis.get("total_duration_ms", 0)

        result_msg = f"## 🎯 Multi-Agent Analysis Complete\n\n"
        result_msg += f"**Workflow:** {state.workflow_name}\n"
        result_msg += f"**Agents:** {', '.join(agents_used)}\n"
        if duration_ms:
            result_msg += f"**Duration:** {duration_ms / 1000:.1f}s\n"
        result_msg += f"\n---\n\n{synthesis_content}"

        await cl.Message(
            content=result_msg,
            actions=[
                cl.Action(
                    name="find_breakthrough",
                    payload={"query": query},
                    label="🔄 Run Again",
                    tooltip="Re-run with different parameters",
                ),
            ],
        ).send()
    else:
        error = state.error or "Unknown error"
        await cl.Message(content=f"Analysis encountered an issue: {error}").send()


@cl.action_callback("dismiss_orchestration")
async def on_dismiss_orchestration(action: cl.Action):
    """User declined orchestration recommendation."""
    try:
        from protocols.orchestration_middleware import record_orchestration_dismissed
        session_id = cl.user_session.get("id", "")
        record_orchestration_dismissed(str(session_id))
    except Exception:
        pass
    # No message needed — the normal response continues


# WAVE 4: Auto-Orchestration - "Find the Breakthrough"
# ═══════════════════════════════════════════════════════════════════════════════

@cl.action_callback("find_breakthrough")
async def on_find_breakthrough(action: cl.Action):
    """Trigger auto-orchestration workflow for breakthrough discovery."""
    try:
        from protocols.auto_orchestrator import AutoOrchestrator, OrchestratorStatus
        from protocols.intent_classifier import classify_intent, get_workflow_description
    except Exception as import_err:
        print(f"[BREAKTHROUGH] Import error: {import_err}")
        await cl.Message(content=f"⚠️ Breakthrough feature is temporarily unavailable: {str(import_err)[:100]}").send()
        return

    # Get the query - either from payload or from recent history
    query = action.payload.get("query", "")
    if not query:
        history = cl.user_session.get("history", [])
        # Find the most recent user message
        for msg in reversed(history):
            if msg.get("role") == "user":
                query = msg.get("content", "")
                break

    if not query:
        await cl.Message(
            content="🔍 **Find the Breakthrough**\n\nPlease describe what you're working on first, then I can help find opportunities!"
        ).send()
        return

    try:
        # Classify intent to determine workflow
        classification = classify_intent(query)
        workflow_desc = get_workflow_description(classification.workflow_type)
    except Exception as classify_err:
        print(f"[BREAKTHROUGH] Classification error: {classify_err}")
        await cl.Message(content=f"⚠️ Could not classify intent: {str(classify_err)[:100]}").send()
        return

    # Show initial message with workflow selection
    await cl.Message(
        content=f"🚀 **Starting: {workflow_desc}**\n\n"
                f"*Detected intent: {classification.workflow_type.value}*\n"
                f"*Confidence: {classification.confidence:.0%}*\n"
                f"*Agents: {', '.join(classification.recommended_agents)}*\n\n"
                "Orchestrating multi-agent analysis...",
        actions=[
            cl.Action(
                name="cancel_orchestration",
                payload={},
                label="⏹️ Cancel",
            )
        ]
    ).send()

    session_id = cl.user_session.get("id") or str(uuid.uuid4())
    history = cl.user_session.get("history", [])

    # Progress callback for real-time updates
    async def progress_callback(progress: dict):
        stage = progress.get("stage", 0) + 1
        total = progress.get("total", 1)
        task = progress.get("task", "")
        agents = progress.get("agents", [])

        msg = cl.Message(
            content=f"📊 **Stage {stage}/{total}**: {task}\n"
                    f"*Running: {', '.join(agents)}*"
        )
        await msg.send()

    # Create and run orchestrator
    orchestrator = AutoOrchestrator(
        session_id=session_id,
        progress_callback=progress_callback,
    )

    # Store orchestrator for cancellation
    cl.user_session.set("active_orchestrator", orchestrator)

    try:
        result = await orchestrator.run(
            query=query,
            workflow_override=action.payload.get("workflow"),
            history=history
        )

        # Clear active orchestrator
        cl.user_session.set("active_orchestrator", None)

        # Display synthesis
        if result.synthesis and "content" in result.synthesis:
            synthesis_content = result.synthesis["content"]
            agents_used = result.synthesis.get("agents_used", [])
            duration_ms = result.synthesis.get("total_duration_ms", 0)

            await cl.Message(
                content=f"## 🎯 Breakthrough Analysis Complete\n\n"
                        f"{synthesis_content}\n\n"
                        f"---\n"
                        f"*Agents: {', '.join(agents_used)} | "
                        f"Duration: {duration_ms/1000:.1f}s | "
                        f"Confidence: {result.confidence:.0%}*",
                actions=[
                    cl.Action(
                        name="find_breakthrough",
                        payload={"query": query},
                        label="🔄 Re-analyze",
                    ),
                    cl.Action(
                        name="show_workflow_options",
                        payload={"query": query},
                        label="📋 Try Different Workflow",
                    ),
                ]
            ).send()
        elif result.status == OrchestratorStatus.CANCELLED.value:
            await cl.Message(content="❌ Analysis cancelled.").send()
        else:
            error = result.error or result.synthesis.get("error", "Unknown error")
            await cl.Message(
                content=f"⚠️ **Analysis incomplete**\n\n{error}"
            ).send()

    except Exception as e:
        cl.user_session.set("active_orchestrator", None)
        print(f"[ORCHESTRATOR] Error: {e}")
        await cl.Message(content=f"⚠️ Orchestration error: {str(e)}").send()


@cl.action_callback("run_workflow")
async def on_run_workflow(action: cl.Action):
    """Run a specific workflow by ID."""
    from protocols.workflow_recipes import get_workflow, list_workflows

    workflow_id = action.payload.get("workflow_id")
    query = action.payload.get("query", "")

    if not workflow_id:
        await cl.Message(content="⚠️ No workflow specified.").send()
        return

    workflow = get_workflow(workflow_id)
    if not workflow:
        await cl.Message(content=f"⚠️ Unknown workflow: {workflow_id}").send()
        return

    # Re-trigger find_breakthrough with workflow override
    await on_find_breakthrough(cl.Action(
        name="find_breakthrough",
        payload={"query": query, "workflow": workflow_id}
    ))


@cl.action_callback("show_workflow_options")
async def on_show_workflow_options(action: cl.Action):
    """Show available workflow options."""
    from protocols.workflow_recipes import list_workflows

    query = action.payload.get("query", "")
    workflows = list_workflows()

    workflow_list = "\n".join([
        f"- **{w['name']}** ({w['stage_count']} stages): {w['description']}"
        for w in workflows
    ])

    actions = [
        cl.Action(
            name="run_workflow",
            payload={"workflow_id": w["id"], "query": query},
            label=f"▶️ {w['name']}",
        )
        for w in workflows[:6]  # Limit to 6 buttons
    ]

    await cl.Message(
        content=f"## 📋 Available Workflows\n\n{workflow_list}\n\n*Select a workflow to run:*",
        actions=actions
    ).send()


@cl.action_callback("cancel_orchestration")
async def on_cancel_orchestration(action: cl.Action):
    """Cancel running orchestration."""
    orchestrator = cl.user_session.get("active_orchestrator")
    if orchestrator:
        orchestrator.cancel()
        await cl.Message(content="⏹️ Cancelling analysis...").send()
    else:
        await cl.Message(content="No active analysis to cancel.").send()


@cl.action_callback("show_orchestrator_progress")
async def on_show_orchestrator_progress(action: cl.Action):
    """Show current orchestrator state."""
    orchestrator = cl.user_session.get("active_orchestrator")
    if not orchestrator or not orchestrator.state:
        await cl.Message(content="No active analysis running.").send()
        return

    state = orchestrator.state
    progress_pct = (state.current_stage / max(state.total_stages, 1)) * 100

    completed_stages = []
    for sr in state.stage_results:
        agents_ok = sum(1 for o in sr.outputs.values() if isinstance(o, dict) and "response" in o)
        agents_err = sum(1 for o in sr.outputs.values() if isinstance(o, dict) and "error" in o)
        completed_stages.append(f"- Stage {sr.stage_index + 1} ({sr.task}): {agents_ok} ✅ {agents_err} ❌")

    stages_text = "\n".join(completed_stages) if completed_stages else "No stages completed yet."

    await cl.Message(
        content=f"## 📊 Orchestration Progress\n\n"
                f"**Workflow:** {state.workflow_name}\n"
                f"**Status:** {state.status}\n"
                f"**Progress:** {progress_pct:.0f}% ({state.current_stage}/{state.total_stages} stages)\n\n"
                f"### Completed Stages\n{stages_text}",
        actions=[
            cl.Action(
                name="cancel_orchestration",
                payload={},
                label="⏹️ Cancel",
            )
        ] if state.status == "running" else []
    ).send()


# ═══════════════════════════════════════════════════════════════════════════════
# v4.0: Extreme Opposition Mode Toggle for Red Team
# ═══════════════════════════════════════════════════════════════════════════════
@cl.action_callback("toggle_extreme_opposition")
async def on_toggle_extreme_opposition(action: cl.Action):
    """Toggle Extreme Opposition mode for Red Team bot."""
    bot = cl.user_session.get("bot", {})

    # Only works for Red Team
    if bot.get("name") != "Red Team":
        await cl.Message(content="⚠️ Extreme Opposition mode is only available in Red Team.").send()
        return

    # Toggle the mode
    extreme_mode = not bot.get("extreme_opposition_mode", False)
    bot["extreme_opposition_mode"] = extreme_mode

    # Update system prompt
    from prompts.redteam import get_redteam_prompt
    bot["system_prompt"] = get_redteam_prompt(extreme_mode=extreme_mode)

    cl.user_session.set("bot", bot)

    # Notify user
    if extreme_mode:
        msg = await cl.Message(
            content="🔴 **EXTREME OPPOSITION MODE ACTIVATED**\n\n"
                    "I'm now in pure opposition mode. I will:\n"
                    "- Contradict your main thesis\n"
                    "- Find counter-evidence for every claim\n"
                    "- Play strategic competitor\n"
                    "- Escalate edge cases\n"
                    "- Assume every assumption is wrong\n\n"
                    "*No mercy. No balanced views. Just the fatal flaw.*",
            actions=[
                cl.Action(
                    name="toggle_extreme_opposition",
                    payload={"action": "toggle"},
                    label="🟢 Return to Normal Mode",
                    description="Switch back to balanced Red Team analysis"
                )
            ]
        ).send()
    else:
        msg = await cl.Message(
            content="🟢 **Normal Red Team Mode Restored**\n\n"
                    "I'm back to balanced devil's advocate mode:\n"
                    "- Challenge assumptions constructively\n"
                    "- Find weaknesses AND suggest fixes\n"
                    "- Stress-test ideas fairly\n\n"
                    "*Constructively brutal, but still helpful.*",
            actions=[
                cl.Action(
                    name="toggle_extreme_opposition",
                    payload={"action": "toggle"},
                    label="🔴 Activate Extreme Opposition",
                    description="Pure opposition mode - no mercy"
                )
            ]
        ).send()


@cl.action_callback("switch_to_ackoff")
async def on_switch_to_ackoff(action: cl.Action):
    await handle_agent_switch("ackoff")

@cl.action_callback("switch_to_larry")
async def on_switch_to_larry(action: cl.Action):
    await handle_agent_switch("lawrence")

@cl.action_callback("switch_to_bono")
async def on_switch_to_bono(action: cl.Action):
    await handle_agent_switch("bono")

@cl.action_callback("switch_to_knowns")
async def on_switch_to_knowns(action: cl.Action):
    await handle_agent_switch("knowns")

@cl.action_callback("switch_to_nested_hierarchies")
async def on_switch_to_nested_hierarchies(action: cl.Action):
    await handle_agent_switch("nested_hierarchies")

@cl.action_callback("switch_to_domain")
async def on_switch_to_domain(action: cl.Action):
    await handle_agent_switch("domain")

@cl.action_callback("switch_to_investment")
async def on_switch_to_investment(action: cl.Action):
    await handle_agent_switch("investment")

@cl.action_callback("switch_to_scenario")
async def on_switch_to_scenario(action: cl.Action):
    await handle_agent_switch("scenario")

@cl.action_callback("switch_to_validation")
async def on_switch_to_validation(action: cl.Action):
    await handle_agent_switch("validation")

@cl.action_callback("switch_to_beautiful_question")
async def on_switch_to_beautiful_question(action: cl.Action):
    await handle_agent_switch("beautiful_question")

@cl.action_callback("switch_to_pws_consultant")
async def on_switch_to_pws_consultant(action: cl.Action):
    await handle_agent_switch("pws_consultant")


# --- Dynamic switch callback registration for registry-added agents ---
# Any agent in BOTS that doesn't have a hardcoded switch_to_* callback above
# gets one auto-registered here. This makes new agents fully switchable.
_HARDCODED_SWITCHES = {
    "tta", "jtbd", "scurve", "redteam", "ackoff", "lawrence",
    "bono", "knowns", "nested_hierarchies", "domain", "investment",
    "scenario", "validation", "beautiful_question", "pws_consultant",
    "larry_playground", "grading", "minto",
}

def _make_switch_handler(agent_id):
    """Create a switch handler closure for the given agent."""
    async def handler(action):
        await handle_agent_switch(agent_id)
    handler.__name__ = f"on_switch_to_{agent_id}"
    return handler

for _bid in BOTS:
    if _bid not in _HARDCODED_SWITCHES:
        _handler = _make_switch_handler(_bid)
        cl.action_callback(f"switch_to_{_bid}")(_handler)
        logger.info(f"[REGISTRY] Auto-registered switch callback for '{_bid}'")


# ═══════════════════════════════════════════════════════════════════════════════
# PWS Consultant: Shared Diagnosis Completion + Callbacks
# ═══════════════════════════════════════════════════════════════════════════════

async def _complete_pws_diagnosis(diagnosis: dict, answers: list, challenge_description: str = ""):
    """
    Shared post-diagnosis completion logic.

    Called by:
    - diagnostic_answer (normal 5-question flow)
    - direct_select_type (skip diagnostic, manual type selection)
    - reclassify_problem (redo diagnosis with different type)

    Handles: DiagnosisResult, bridge message, ExpertPanel, tool actions, stage transition.
    """
    cl.user_session.set("pws_diagnosis", diagnosis)

    primary = PWS_PROBLEM_TYPES.get(diagnosis["primary"], {})
    secondary = PWS_PROBLEM_TYPES.get(diagnosis.get("secondary", ""), {})

    # Show DiagnosisResult component
    result_element = cl.CustomElement(
        name="DiagnosisResult",
        props={
            "problemType": diagnosis["primary"],
            "problemName": primary.get("name", ""),
            "description": primary.get("description", ""),
            "icon": primary.get("icon", ""),
            "color": primary.get("color", "#E63946"),
            "keyQuestion": primary.get("key_question", ""),
            "frameworks": primary.get("frameworks", []),
            "confidence": diagnosis.get("confidence", 0),
            "complexity": primary.get("complexity", ""),
            "secondaryName": secondary.get("name"),
            "secondaryIcon": secondary.get("icon"),
            "secondaryColor": secondary.get("color"),
        },
        display="inline",
    )

    # Build context-aware tool actions
    tool_actions = []
    rec_tools = pws_get_recommended_tools(diagnosis["primary"])
    for tool in rec_tools:
        tool_actions.append(
            cl.Action(
                name=tool["name"],
                payload={"action": tool["name"], "problem_type": diagnosis["primary"]},
                label=tool["label"],
                description=tool.get("tooltip", ""),
            )
        )

    # Collect expert panel (from background task or build fresh)
    expert_panel_data = cl.user_session.get("pws_expert_panel_data")

    if not expert_panel_data or not expert_panel_data.get("experts"):
        # Build expert panel now with correct problem type
        try:
            domain_data = cl.user_session.get("pws_domain_discovery", {})
            domain = domain_data.get("domain", "General")
            subdomains = domain_data.get("subdomains", ["General"])
            experts = pws_build_expert_specs(domain, subdomains, diagnosis["primary"])
            expert_panel_data = {"experts": experts, "domain": domain}
            cl.user_session.set("pws_expert_panel_data", expert_panel_data)
        except Exception as e:
            print(f"[PWS] Expert panel build error: {e}")
            expert_panel_data = {"experts": [], "domain": ""}

    elements_to_send = [result_element]

    if expert_panel_data.get("experts"):
        expert_element = cl.CustomElement(
            name="ExpertPanel",
            props={
                "experts": expert_panel_data["experts"],
                "domain": expert_panel_data.get("domain", ""),
                "title": "Your Consulting Panel",
                "subtitle": "Domain specialists ready to offer their perspective",
                "loading": False,
            },
            display="inline",
        )
        elements_to_send.append(expert_element)
    else:
        expert_element = cl.CustomElement(
            name="ExpertPanel",
            props={
                "experts": [],
                "loading": True,
                "loadingMessage": "I'm assembling a panel of domain experts for your situation...",
            },
            display="inline",
        )
        elements_to_send.append(expert_element)

    # Build diagnostic context for LLM
    diag_context = pws_build_diagnostic_context(diagnosis, answers)

    # Enrich with two-stage classification if available (Quick win from AGENTS.md)
    classification = cl.user_session.get("pws_classification")
    if classification:
        cynefin = classification.get("cynefin", "unknown")
        pws = classification.get("pws", "unknown")
        cynefin_conf = classification.get("cynefin_confidence", 0)
        pws_conf = classification.get("pws_confidence", 0)
        diag_context += f"""
[CYNEFIN DOMAIN ANALYSIS]
Domain: {cynefin.upper()} (confidence: {cynefin_conf:.0%})
PWS Lifecycle: {pws} (confidence: {pws_conf:.0%})
Reasoning: {classification.get('reasoning', 'N/A')}

[GUIDANCE BASED ON CYNEFIN DOMAIN]
"""
        if cynefin == "complex":
            diag_context += "- Use probe-sense-respond: Suggest small experiments, not full solutions\n"
            diag_context += "- Embrace emergence: Patterns will become clear through action\n"
        elif cynefin == "complicated":
            diag_context += "- Use sense-analyze-respond: Consult expert frameworks\n"
            diag_context += "- Multiple valid approaches exist - help user analyze options\n"
        elif cynefin == "chaotic":
            diag_context += "- Act first, sense second: Establish stability before analysis\n"
            diag_context += "- Focus on immediate actionable steps\n"
        elif cynefin == "clear":
            diag_context += "- Apply best practice directly\n"
            diag_context += "- The path forward is straightforward\n"

    cl.user_session.set("pws_diagnostic_context", diag_context)

    # Transition stage: -> consulting
    cl.user_session.set("pws_stage", "consulting")
    cl.user_session.set("pws_sub_mode", "normal")
    cl.user_session.set("pws_consulting_turn_count", 0)
    cl.user_session.set("pws_expert_consult_count", 0)

    await cl.Message(
        content="",
        elements=elements_to_send,
        actions=tool_actions,
    ).send()

    # Build bridge prompt and send Larry's interpretive bridge message
    from prompts.pws_consultant import build_bridge_prompt
    bridge_instructions = build_bridge_prompt(diagnosis, challenge_description)

    bot = cl.user_session.get("bot", {})
    system_prompt = bot.get("system_prompt", PWS_CONSULTANT_PROMPT) + "\n\n" + diag_context + "\n\n" + bridge_instructions

    # Get hybrid retrieval context
    hybrid_ctx = ""
    try:
        from tools.pws_consultant_pipeline import hybrid_retrieve
        hybrid_ctx_result, _ = hybrid_retrieve(challenge_description or "problem diagnosis")
        if hybrid_ctx_result:
            hybrid_ctx = hybrid_ctx_result
            system_prompt += f"\n\n[KNOWLEDGE CONTEXT]\n{hybrid_ctx}"
            cl.user_session.set("pws_hybrid_context", hybrid_ctx)
    except Exception as e:
        logger.debug("Hybrid retrieval in diagnosis failed: %s", e)

    history = cl.user_session.get("history", [])

    msg = cl.Message(content="")
    await msg.send()

    try:
        bridge_prompt = f"I've completed the diagnostic. My problem has been classified as: {primary.get('name', '')}. Now give me the bridge message explaining what this means for my specific situation."
        history.append({"role": "user", "content": bridge_prompt})

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
        response_stream = client.models.generate_content_stream(
            model="gemini-3-flash-preview",
            contents=history,
            config=config,
        )
        full_response = ""
        for chunk in response_stream:
            if chunk.text:
                await msg.stream_token(chunk.text)
                full_response += chunk.text
        await msg.update()

        history.append({"role": "model", "content": full_response})
        cl.user_session.set("history", history)
    except Exception as e:
        await msg.stream_token(f"Let me think about this differently... ({e})")
        await msg.update()


@cl.action_callback("submit_challenge")
async def on_submit_challenge(action: cl.Action):
    """Handle challenge submission from ChallengeIntro component.

    Transitions from intro to diagnostic stage, fires background expert panel task,
    and shows the first diagnostic question.
    """
    try:
        payload = action.payload or {}
        challenge = payload.get("challenge", "").strip()

        if not challenge:
            await cl.Message(content="Please describe your challenge before continuing.").send()
            return

        # Store challenge in session
        cl.user_session.set("pws_challenge_description", challenge)

        # Retrieve two-stage classification result if available (Quick win from AGENTS.md)
        classification_task = cl.user_session.get("pws_classification_task")
        if classification_task:
            try:
                classification_result = await asyncio.wait_for(classification_task, timeout=2.0)
                cl.user_session.set("pws_classification", classification_result)
                logger.info(f"[PWS] Classification retrieved: {classification_result}")
            except asyncio.TimeoutError:
                logger.debug("[PWS] Classification task timed out, will complete in background")
            except Exception as e:
                logger.debug(f"[PWS] Classification retrieval error: {e}")

        # Transition stage: intro -> diagnostic
        cl.user_session.set("pws_stage", "diagnostic")

        # Run instant analysis on challenge text
        try:
            from tools.pws_consultant_pipeline import instant_analyze
            turn_count = cl.user_session.get("pws_intro_turn_count", 1)
            signals = instant_analyze(challenge, turn_count)
            cl.user_session.set("pws_challenge_signals", signals)
        except Exception as e:
            logger.debug("Instant analyze failed in submit_challenge: %s", e)

        # Fire background expert panel task (runs in parallel during diagnostic)
        try:
            from tools.pws_consultant_pipeline import build_expert_panel
            task = asyncio.create_task(build_expert_panel(
                user_message=challenge,
                problem_type_key="undefined",  # Updated after diagnosis
                conversation_context="",
            ))
            cl.user_session.set("pws_expert_panel_task", task)
        except Exception as e:
            logger.debug("Expert panel background task failed: %s", e)

        # Fire hybrid retrieval in background
        try:
            from tools.pws_consultant_pipeline import hybrid_retrieve
            loop = asyncio.get_event_loop()
            hybrid_task = loop.run_in_executor(None, lambda: hybrid_retrieve(challenge))
            cl.user_session.set("pws_hybrid_task", hybrid_task)
        except Exception as e:
            logger.debug("Hybrid retrieval background task failed: %s", e)

        # Show acknowledgment and first diagnostic question
        await cl.Message(content="I understand. Let me ask you 5 questions to classify your problem type.").send()

        # Show first DiagnosticFlow question
        first_q = PWS_DIAGNOSTIC_QUESTIONS[0]
        elements = [
            cl.CustomElement(
                name="DiagnosticFlow",
                props={
                    "question": first_q["text"],
                    "options": [opt["label"] for opt in first_q["options"]],
                    "questionNumber": 1,
                    "totalQuestions": 5,
                    "questionId": first_q["id"],
                },
                display="inline",
            )
        ]
        await cl.Message(content="", elements=elements).send()

    except Exception as e:
        logger.warning("Submit challenge callback error: %s", e)
        await cl.Message(content="Something went wrong. Please try describing your challenge again.").send()


@cl.action_callback("direct_select_type")
async def on_direct_select_type(action: cl.Action):
    """Handle direct problem type selection from ChallengeIntro component.

    Skips the diagnostic phase and goes directly to consulting with
    the manually selected problem type.
    """
    try:
        payload = action.payload or {}
        problem_type = payload.get("problemType", "undefined")
        challenge = payload.get("challenge", "").strip()

        # Store challenge if provided
        if challenge:
            cl.user_session.set("pws_challenge_description", challenge)

        # Map short type id to full type key
        type_mapping = {
            "undefined": "Un-Defined",
            "illdefined": "Ill-Defined",
            "welldefined": "Well-Defined",
            "wicked": "Wicked",
        }
        primary_type = type_mapping.get(problem_type, "Un-Defined")

        # Create a synthetic diagnosis result (bypassing the 5-question flow)
        diagnosis = {
            "primary": primary_type,
            "secondary": None,
            "confidence": 0.85,  # Manual selection has high confidence
            "scores": {primary_type: 5},  # Full score for selected type
            "manual_selection": True,
        }

        # Create empty answers list (no diagnostic questions answered)
        answers = []

        # Store the challenge (use stored or fallback)
        stored_challenge = cl.user_session.get("pws_challenge_description", "")
        final_challenge = stored_challenge or challenge or "User selected problem type directly"
        cl.user_session.set("pws_challenge_description", final_challenge)

        # Show acknowledgment
        await cl.Message(content=f"You've selected **{primary_type}** as your problem type. Let me configure our session for this approach.").send()

        # Use shared completion function (handles DiagnosisResult, ExpertPanel, stage transition)
        await _complete_pws_diagnosis(diagnosis, answers, final_challenge)

    except Exception as e:
        logger.warning("Direct select type callback error: %s", e)
        await cl.Message(content="Something went wrong. Please try again.").send()


@cl.action_callback("diagnostic_answer")
async def on_diagnostic_answer(action: cl.Action):
    """Handle a diagnostic question answer from DiagnosticFlow component."""
    try:
        payload = action.payload or {}
        question_id = payload.get("questionId", "")
        option_index = payload.get("optionIndex", 0)
        option_label = payload.get("optionLabel", "")
        question_number = payload.get("questionNumber", 1)

        # Store answer in session (pws_ namespace)
        answers = cl.user_session.get("pws_diagnostic_answers", [])
        answers.append({
            "question_id": question_id,
            "option_index": option_index,
            "question": question_id,
            "answer": option_label,
        })
        cl.user_session.set("pws_diagnostic_answers", answers)

        if question_number < 5:
            # Send next question
            next_q = PWS_DIAGNOSTIC_QUESTIONS[question_number]  # 0-indexed, questionNumber is 1-based
            elements = [
                cl.CustomElement(
                    name="DiagnosticFlow",
                    props={
                        "question": next_q["text"],
                        "options": [opt["label"] for opt in next_q["options"]],
                        "questionNumber": question_number + 1,
                        "totalQuestions": 5,
                        "questionId": next_q["id"],
                    },
                    display="inline",
                )
            ]
            await cl.Message(content="", elements=elements).send()
        else:
            # All 5 answered - score and use shared completion function
            diagnosis = pws_score_diagnostic(answers)
            challenge = cl.user_session.get("pws_challenge_description", "")
            await _complete_pws_diagnosis(diagnosis, answers, challenge)

    except Exception as e:
        logger.warning("Diagnostic answer callback error: %s", e)
        await cl.Message(content="Let me process that... Could you rephrase your challenge?").send()


@cl.action_callback("consult_expert")
async def on_consult_expert(action: cl.Action):
    """Handle expert consultation from the ExpertPanel component."""
    try:
        payload = action.payload or {}
        expert_id = payload.get("expertId", "")
        role = payload.get("role", "Expert")
        subdomain = payload.get("subdomain", "")
        system_context = payload.get("systemContext", "")
        approach = payload.get("approach", "")

        # Set sub-mode to expert (will be reset to normal after the response)
        cl.user_session.set("pws_sub_mode", "expert")
        consult_count = cl.user_session.get("pws_expert_consult_count", 0) + 1
        cl.user_session.set("pws_expert_consult_count", consult_count)

        # Get the main system prompt + diagnostic context
        bot = cl.user_session.get("bot", {})
        base_prompt = bot.get("system_prompt", PWS_CONSULTANT_PROMPT)
        diag_context = cl.user_session.get("pws_diagnostic_context", "")

        # Build expert consultation prompt
        expert_prompt = f"""{base_prompt}

{diag_context}

[EXPERT CONSULTATION MODE]
The user has asked to consult with the {role} ({subdomain}).
{system_context}

Adopt this expert's perspective temporarily. Use their approach: {approach}
Frame it as: "Let me put on a different hat for a moment — looking at this through the eyes of someone who lives in {subdomain}..."
After giving the expert's perspective, return to your Larry perspective with a synthesis.
End by asking what the user wants to explore next."""

        # Get conversation history
        history = cl.user_session.get("history", [])
        history_messages = [{"role": h["role"], "parts": [{"text": h["content"]}]} for h in history[-10:]]

        msg = cl.Message(content="")
        await msg.send()

        try:
            response_stream = client.models.generate_content_stream(
                model=MODEL_ID,
                contents=history_messages + [{"role": "user", "parts": [{"text": f"I'd like to consult with the {role} about my challenge."}]}],
                config=types.GenerateContentConfig(
                    system_instruction=expert_prompt,
                    temperature=0.7,
                    max_output_tokens=1200,
                ),
            )
            full_response = ""
            for chunk in response_stream:
                if chunk.text:
                    await msg.stream_token(chunk.text)
                    full_response += chunk.text
            await msg.update()

            history.append({"role": "user", "content": f"[Consulted {role} ({subdomain})]"})
            history.append({"role": "model", "content": full_response})
            cl.user_session.set("history", history)

            # === AGENTS.md Pattern: Store expert response as Frame (not Artifact) ===
            # Expert opinions are scoped interpretations, not validated evidence yet
            frame_id = None
            if PWS_STATE_ENABLED:
                try:
                    from utils.pws_state import add_frame
                    frame_id = add_frame(
                        agent=f"expert_{expert_id}",
                        content=full_response[:500],  # Truncate for storage
                        frame_type="expert_opinion",
                        confidence=0.6  # Expert opinions start at moderate confidence
                    )
                    cl.user_session.set("pws_last_expert_frame_id", frame_id)
                    cl.user_session.set("pws_last_expert_agent", f"expert_{expert_id}")
                except Exception as e:
                    logger.debug(f"[PWS] Frame storage error: {e}")

            # Show action buttons for accepting or challenging the expert insight
            expert_actions = [
                cl.Action(
                    name="accept_expert_insight",
                    payload={"expert_id": expert_id, "frame_id": frame_id, "role": role},
                    label="✅ Accept this insight",
                    description="Promote this to validated evidence"
                ),
                cl.Action(
                    name="challenge_expert_insight",
                    payload={"expert_id": expert_id, "frame_id": frame_id, "role": role},
                    label="🤔 Challenge this",
                    description="Apply Red Team validation"
                ),
            ]
            await cl.Message(content="", actions=expert_actions).send()

        except Exception as e:
            await msg.stream_token(f"Let me bring in that perspective... {e}")
            await msg.update()

    except Exception as e:
        logger.warning("Expert consultation callback error: %s", e)
        await cl.Message(content="Let me try bringing in that perspective differently.").send()


@cl.action_callback("accept_expert_insight")
async def on_accept_expert_insight(action: cl.Action):
    """
    Accept an expert's insight and promote it to a validated artifact.

    AGENTS.md pattern: Frame -> Artifact promotion after user confirmation.
    """
    try:
        payload = action.payload or {}
        frame_id = payload.get("frame_id")
        expert_id = payload.get("expert_id")
        role = payload.get("role", "Expert")

        if PWS_STATE_ENABLED and frame_id:
            try:
                from utils.pws_state import promote_frame_to_artifact
                artifact_id = promote_frame_to_artifact(
                    agent=f"expert_{expert_id}",
                    frame_id=frame_id,
                    validation_source="user_confirmed"
                )
                if artifact_id:
                    await cl.Message(
                        content=f"Got it — I've noted that insight from the {role} as validated evidence. "
                                "We can build on this as we continue."
                    ).send()
                else:
                    await cl.Message(content="Thanks, I'll keep that in mind.").send()
            except Exception as e:
                logger.debug(f"[PWS] Promotion error: {e}")
                await cl.Message(content="Thanks, I'll keep that in mind.").send()
        else:
            await cl.Message(content="Thanks, I'll factor that perspective into our discussion.").send()

    except Exception as e:
        logger.warning(f"Accept expert insight error: {e}")


@cl.action_callback("challenge_expert_insight")
async def on_challenge_expert_insight(action: cl.Action):
    """
    Challenge an expert's insight using Red Team validation.

    AGENTS.md pattern: Apply cross-cutting validation to any output.
    """
    try:
        payload = action.payload or {}
        frame_id = payload.get("frame_id")
        expert_id = payload.get("expert_id")
        role = payload.get("role", "Expert")

        # Get the expert's response from history
        history = cl.user_session.get("history", [])
        expert_response = ""
        for h in reversed(history):
            if "[Consulted" in h.get("content", ""):
                # Next one is the expert response
                idx = history.index(h)
                if idx + 1 < len(history):
                    expert_response = history[idx + 1].get("content", "")
                break

        if not expert_response:
            await cl.Message(content="Let me re-examine that perspective...").send()
            return

        # Apply Red Team validation
        if PWS_VALIDATION_ENABLED:
            diagnosis = cl.user_session.get("pws_diagnosis", {})
            problem_type = diagnosis.get("primary", "ill_defined")

            validation_result = await validate_pws_response(
                user_message=f"The {role} said: {expert_response[:200]}...",
                assistant_response=expert_response,
                problem_type=problem_type,
                turn_count=cl.user_session.get("pws_consulting_turn_count", 0),
                context={"source": "expert_challenge", "expert": role}
            )

            # Format the challenge as a response
            challenge_intro = f"Let me put on my Red Team hat and challenge the {role}'s perspective:\n\n"

            if validation_result.challenges:
                questions = [c.get("question", "") for c in validation_result.challenges[:3] if c.get("question")]
                challenge_points = "\n".join([f"• {q}" for q in questions])
                challenge_msg = f"{challenge_intro}**Questions to consider:**\n{challenge_points}"
            else:
                challenge_msg = f"{challenge_intro}The perspective seems well-grounded, but consider: What evidence would change this view?"

            if validation_result.red_flags_detected:
                challenge_msg += f"\n\n**Potential concerns:** {', '.join(validation_result.red_flags_detected[:2])}"

            await cl.Message(content=challenge_msg).send()
        else:
            # Fallback without validation middleware
            await cl.Message(
                content=f"Let me push back on that perspective from the {role}:\n\n"
                        "• What assumptions is this based on?\n"
                        "• What evidence would prove this wrong?\n"
                        "• Who might disagree and why?"
            ).send()

    except Exception as e:
        logger.warning(f"Challenge expert insight error: {e}")
        await cl.Message(content="Let me reconsider that perspective...").send()


@cl.action_callback("reclassify_problem")
async def on_reclassify_problem(action: cl.Action):
    """
    Handle reclassification request from Red Team validation or user request.

    This allows users to re-run the diagnostic if the problem has evolved
    or if the initial classification feels wrong.

    AGENTS.md pattern: Explicit handling of problem evolution.
    """
    try:
        payload = action.payload or {}
        reason = payload.get("reason", "user_request")

        # Preserve challenge description for context
        challenge_description = cl.user_session.get("pws_challenge_description", "")
        existing_diagnosis = cl.user_session.get("pws_diagnosis", {})
        consulting_turns = cl.user_session.get("pws_consulting_turn_count", 0)

        # Log the reclassification event
        logger.info(f"[PWS] Reclassification requested: reason={reason}, "
                    f"previous_type={existing_diagnosis.get('primary', 'unknown')}, "
                    f"consulting_turns={consulting_turns}")

        # Reset to diagnostic stage
        cl.user_session.set("pws_stage", "diagnostic")
        cl.user_session.set("pws_sub_mode", "normal")
        cl.user_session.set("pws_diagnostic_answers", [])
        cl.user_session.set("pws_diagnosis", None)
        cl.user_session.set("pws_diagnostic_context", "")

        # Acknowledge the transition
        if reason == "validation_suggested":
            intro_msg = ("Let's step back and re-assess. Your problem seems to be "
                         "evolving — that's actually a good sign that you're thinking "
                         "more deeply about it. Let me ask the diagnostic questions again "
                         "with your current understanding in mind.")
        else:
            intro_msg = ("Got it — let's re-assess. Problems often evolve as we think "
                         "through them. I'll ask the questions again, and you can "
                         "answer based on where you are now.")

        await cl.Message(content=intro_msg).send()

        # Show first diagnostic question
        first_q = PWS_DIAGNOSTIC_QUESTIONS[0]
        elements = [
            cl.CustomElement(
                name="DiagnosticFlow",
                props={
                    "question": first_q["text"],
                    "options": [opt["label"] for opt in first_q["options"]],
                    "questionNumber": 1,
                    "totalQuestions": 5,
                    "questionId": first_q["id"],
                    "isReclassification": True,  # Flag for UI to show differently
                },
                display="inline",
            )
        ]
        await cl.Message(content="", elements=elements).send()

    except Exception as e:
        logger.warning(f"[PWS] Reclassify callback error: {e}")
        await cl.Message(content="Let me try that again...").send()


# ═══════════════════════════════════════════════════════════════════════════════
# Smart Onboarding Callbacks
# ═══════════════════════════════════════════════════════════════════════════════

@cl.action_callback("start_onboarding")
async def on_start_onboarding(action: cl.Action):
    """User chose to take the onboarding tour."""
    if not SMART_ONBOARDING_ENABLED:
        return

    try:
        # Get user_id
        user = cl.user_session.get("user")
        session_id = cl.user_session.get("id")
        user_id = user.identifier if user else session_id or "anonymous"

        # Get tour steps
        tour_steps = get_onboarding_tour_steps()

        # Store tour state
        cl.user_session.set("onboarding_step", 0)
        cl.user_session.set("onboarding_active", True)

        # Show first step
        if tour_steps:
            step = tour_steps[0]
            step_content = f"""### {step['title']}

{step['content']}

---
*Step 1 of {len(tour_steps)}*"""

            # Create next/skip buttons
            step_actions = [
                cl.Action(
                    name="onboarding_next",
                    payload={"step": 1},
                    label="Next →",
                    description="Continue to next concept"
                ),
                cl.Action(
                    name="onboarding_skip_rest",
                    payload={"action": "skip"},
                    label="Got it, let's start!",
                    description="Skip remaining steps and start exploring"
                ),
            ]

            await cl.Message(content=step_content, actions=step_actions).send()

    except Exception as e:
        logger.warning(f"[ONBOARDING] Error starting tour: {e}")
        await cl.Message(content="Let's get started! What would you like to explore today?").send()


@cl.action_callback("skip_onboarding")
async def on_skip_onboarding(action: cl.Action):
    """User chose to skip the onboarding tour."""
    if not SMART_ONBOARDING_ENABLED:
        return

    try:
        # Get user_id
        user = cl.user_session.get("user")
        session_id = cl.user_session.get("id")
        user_id = user.identifier if user else session_id or "anonymous"

        # Mark as skipped (assumes some familiarity)
        mark_onboarding_skipped(user_id)

        # Send a quick acknowledgment
        await cl.Message(
            content="""No problem! I'll explain any unfamiliar terms as they come up.

**What's on your mind?** Share an idea, a problem you're curious about, or an industry you want to explore."""
        ).send()

    except Exception as e:
        logger.warning(f"[ONBOARDING] Error skipping: {e}")
        await cl.Message(content="What would you like to explore today?").send()


@cl.action_callback("onboarding_next")
async def on_onboarding_next(action: cl.Action):
    """User clicked next in the onboarding tour."""
    if not SMART_ONBOARDING_ENABLED:
        return

    try:
        # Get current step
        current_step = action.payload.get("step", 0)
        tour_steps = get_onboarding_tour_steps()

        if current_step < len(tour_steps):
            step = tour_steps[current_step]
            step_content = f"""### {step['title']}

{step['content']}

---
*Step {current_step + 1} of {len(tour_steps)}*"""

            # Determine next action
            if current_step + 1 < len(tour_steps):
                step_actions = [
                    cl.Action(
                        name="onboarding_next",
                        payload={"step": current_step + 1},
                        label="Next →",
                        description="Continue to next concept"
                    ),
                    cl.Action(
                        name="onboarding_skip_rest",
                        payload={"action": "skip"},
                        label="Got it, let's start!",
                        description="Skip remaining steps and start exploring"
                    ),
                ]
            else:
                # Last step
                step_actions = [
                    cl.Action(
                        name="onboarding_complete",
                        payload={"action": "complete"},
                        label="Let's explore!",
                        description="Start your first exploration"
                    ),
                ]

            await cl.Message(content=step_content, actions=step_actions).send()
            cl.user_session.set("onboarding_step", current_step)

    except Exception as e:
        logger.warning(f"[ONBOARDING] Error in next step: {e}")
        await cl.Message(content="What would you like to explore today?").send()


@cl.action_callback("onboarding_skip_rest")
async def on_onboarding_skip_rest(action: cl.Action):
    """User clicked to skip remaining onboarding steps."""
    if not SMART_ONBOARDING_ENABLED:
        return

    try:
        user = cl.user_session.get("user")
        session_id = cl.user_session.get("id")
        user_id = user.identifier if user else session_id or "anonymous"

        mark_onboarding_completed(user_id)
        cl.user_session.set("onboarding_active", False)

        await cl.Message(
            content="""**You're all set!**

Now let's put these ideas to work. What problem or opportunity are you thinking about?

*I'll introduce more frameworks as they become relevant.*"""
        ).send()

    except Exception as e:
        logger.warning(f"[ONBOARDING] Error skipping rest: {e}")
        await cl.Message(content="What would you like to explore?").send()


@cl.action_callback("onboarding_complete")
async def on_onboarding_complete(action: cl.Action):
    """User completed the full onboarding tour."""
    if not SMART_ONBOARDING_ENABLED:
        return

    try:
        user = cl.user_session.get("user")
        session_id = cl.user_session.get("id")
        user_id = user.identifier if user else session_id or "anonymous"

        mark_onboarding_completed(user_id)
        cl.user_session.set("onboarding_active", False)

        await cl.Message(
            content="""**Excellent! You've got the fundamentals.**

You now know about:
- **Problems Worth Solving** — finding valuable challenges
- **Reverse Salients** — identifying bottlenecks
- **Jobs to Be Done** — understanding real customer needs

Ready to apply these? Tell me about a problem, industry, or idea you're curious about."""
        ).send()

    except Exception as e:
        logger.warning(f"[ONBOARDING] Error completing: {e}")
        await cl.Message(content="What would you like to explore?").send()


# ═══════════════════════════════════════════════════════════════════════════════
# Triple-Mode Entry Point & Mode Callbacks
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# TRIPLE-MODE ENTRY POINT CALLBACKS (separate for reliability)
# ═══════════════════════════════════════════════════════════════════════════════

@cl.action_callback("ep_brainstorming")
async def on_ep_brainstorming(action: cl.Action):
    """Handle Explore Ideas entry point."""
    logger.info("[ACTION] ep_brainstorming triggered")
    if TRIPLE_MODE_ENABLED:
        await handle_entry_point_selection("brainstorming")


@cl.action_callback("ep_document_review")
async def on_ep_document_review(action: cl.Action):
    """Handle Get Feedback entry point."""
    logger.info("[ACTION] ep_document_review triggered")
    if TRIPLE_MODE_ENABLED:
        await handle_entry_point_selection("document_review")


@cl.action_callback("ep_build_venture")
async def on_ep_build_venture(action: cl.Action):
    """Handle Build Venture entry point."""
    logger.info("[ACTION] ep_build_venture triggered")
    if TRIPLE_MODE_ENABLED:
        await handle_entry_point_selection("build_venture")


@cl.action_callback("select_entry_point")
async def on_select_entry_point(action: cl.Action):
    """Legacy handler for backward compatibility."""
    logger.info(f"[ACTION] select_entry_point triggered: {action.payload}")
    try:
        if TRIPLE_MODE_ENABLED:
            entry_point = action.payload.get("entry_point", "brainstorming")
            await handle_entry_point_selection(entry_point)
    except Exception as e:
        logger.error(f"[ACTION] Error in select_entry_point: {e}", exc_info=True)


@cl.action_callback("mode_or_stage")
async def on_mode_or_stage(action: cl.Action):
    """
    CONSOLIDATED: Handle mode toggle AND venture stage selection.
    Payload: { mode: "sandbox" | "workshop" } OR { stage: "pre_opportunity" | ... }
    """
    if TRIPLE_MODE_ENABLED:
        await handle_mode_or_stage(action.payload)


@cl.action_callback("grounding_response")
async def on_grounding_response(action: cl.Action):
    """
    CONSOLIDATED: Handle all grounding prompt responses.
    Payload: { action: "acknowledge" | "skip" | "bank", reason: str }
    """
    if TRIPLE_MODE_ENABLED:
        await handle_grounding_response(action.payload)


async def handle_agent_switch(new_agent_id: str):
    """
    Handle switching to a new agent while preserving conversation context.
    This performs an in-session switch without reloading the page.
    """
    current_bot_id = cl.user_session.get("bot_id", "lawrence")
    history = cl.user_session.get("history", [])

    if new_agent_id not in BOTS:
        await cl.Message(content=f"Unknown agent: {new_agent_id}").send()
        return

    new_bot = BOTS[new_agent_id]
    old_bot = BOTS.get(current_bot_id, BOTS["lawrence"])

    # Update session with new bot
    cl.user_session.set("bot", new_bot)
    cl.user_session.set("bot_id", new_agent_id)
    cl.user_session.set("previous_bot", current_bot_id)

    # Add context handoff for the new bot
    handoff = f"[CONTEXT HANDOFF: User switched from {old_bot.get('name')} to {new_bot.get('name')}. Previous conversation preserved.]"
    cl.user_session.set("context_handoff", handoff)

    # === A2A Protocol: Create structured handoff ===
    try:
        from protocols import A2A_ORCHESTRATION_ENABLED, create_switch_handoff, inject_handoff_context
        if A2A_ORCHESTRATION_ENABLED:
            session_id = cl.user_session.get("id", "")
            a2a_handoff = await create_switch_handoff(
                from_agent=current_bot_id,
                to_agent=new_agent_id,
                session_id=session_id,
                history=history,
                current_phase=cl.user_session.get("current_phase", 0),
                phases=cl.user_session.get("phases"),
            )
            # Inject handoff context into the new bot's system prompt
            enriched_prompt = inject_handoff_context(a2a_handoff, new_bot.get("system_prompt", ""))
            cl.user_session.set("a2a_enriched_prompt", enriched_prompt)
            cl.user_session.set("a2a_last_handoff", a2a_handoff)
            logger.info(f"[A2A] Handoff created: {current_bot_id} -> {new_agent_id}")

            # Carry context engine state across handoff
            if CONTEXT_ENGINE_ENABLED:
                try:
                    last_strategy = cl.user_session.get("_ce_last_strategy", "")
                    if last_strategy:
                        handoff_ce_note = f"\n[Context Engine: Previous bot used strategy={last_strategy}]"
                        cl.user_session.set("a2a_enriched_prompt",
                            enriched_prompt + handoff_ce_note)
                except Exception:
                    pass
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"[A2A] Handoff creation failed (non-fatal): {e}")

    # === Recursive Intelligence: Log agent switch event ===
    if SESSION_LOGGER_ENABLED:
        session_id = cl.user_session.get("id")
        if session_id:
            # Fire-and-forget async log (non-blocking)
            await log_session_event(
                session_id=session_id,
                event_type="agent_switch",
                agent=new_agent_id,
                from_agent=current_bot_id,
                to_agent=new_agent_id,
                user_initiated=True,  # User clicked switch button
                turn_count=len(history),
                metadata={"context_preserved": True}
            )

    # Initialize or restore phases for new bot if it's a workshop
    context_key = get_context_key()  # Define early for use in both branches
    bot_phases = _get_phases_for_bot(new_agent_id)  # Auto-discovery with fallback
    if bot_phases:
        # Check if we have saved phase progress for this bot (QA-006 fix)
        saved_context = context_store.get(context_key, {})
        saved_bot_id = saved_context.get("bot_id")
        saved_phases = saved_context.get("phases", [])
        saved_current_phase = saved_context.get("current_phase", 0)

        # Restore saved progress if switching back to same workshop bot
        if saved_bot_id == new_agent_id and saved_phases:
            phases = [p.copy() for p in saved_phases]
            current_phase = saved_current_phase
        else:
            # Fresh start for this workshop
            phases = bot_phases
            current_phase = 0

        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", current_phase)

        # Create WorkshopRoadmap showing current progress
        history = cl.user_session.get("history", [])
        phase_insights = extract_phase_insights(history, phases, current_phase)
        await create_or_update_roadmap(
            phases=phases,
            current_phase=current_phase,
            bot_name=new_bot.get("name", "Workshop"),
            bot_icon=new_bot.get("icon", "🎯"),
            phase_context=phase_insights
        )
    else:
        cl.user_session.set("phases", [])
        cl.user_session.set("current_phase", 0)

    # Update context store - include phases for persistence across bot switches (QA-006 fix)
    stored_phases = cl.user_session.get("phases", [])
    context_store[context_key] = {
        "bot_id": new_agent_id,
        "history": history.copy(),
        "phases": [p.copy() for p in stored_phases] if stored_phases else [],
        "current_phase": cl.user_session.get("current_phase", 0),
    }

    # CRITICAL: Persist to Supabase on bot switch to survive server restarts
    # This fixes P0 bug where context was lost on Render deploys
    try:
        from utils.context_persistence import save_cross_bot_context
        # Update last_checkpoint on bot switch
        last_checkpoint = datetime.utcnow().isoformat()
        cl.user_session.set("last_checkpoint", last_checkpoint)

        # BUG-001 FIX: Preserve excluded_topics on bot switch
        await save_cross_bot_context(
            user_key=context_key,
            history=history.copy(),
            bot_id=new_agent_id,
            bot_name=new_bot.get("name", new_agent_id),
            phases=[p.copy() for p in stored_phases] if stored_phases else None,
            current_phase=cl.user_session.get("current_phase", 0),
            conversation_id=cl.user_session.get("conversation_id"),
            conversation_name=cl.user_session.get("conversation_name", ""),
            excluded_topics=cl.user_session.get("excluded_topics", [])
        )
        logger.info(f"[PERSISTENCE] Checkpoint saved on bot switch: {last_checkpoint}")
    except Exception as e:
        logger.warning(f"Context persistence failed on bot switch: {e}")

    # === Thread System: Save to topic-aware thread ===
    # This fixes the context-mixing bug by tracking conversations by topic
    if THREAD_SYSTEM_ENABLED:
        try:
            # Get or create thread for this conversation topic
            thread_id, thread = get_or_create_thread(
                user_key=context_key,
                bot_id=new_agent_id,
                history=history
            )
            # Save current context to thread
            save_thread_context(
                thread_id=thread_id,
                user_key=context_key,
                history=history,
                phases=stored_phases,
                current_phase=cl.user_session.get("current_phase", 0),
                bot_id=new_agent_id
            )
            # Store thread_id in session for later use
            cl.user_session.set("current_thread_id", thread_id)
        except Exception as e:
            logger.warning(f"Thread system error in agent switch: {e}")

    # Build actions for the new bot
    actions = []
    if new_bot.get("has_phases"):
        actions = [
            cl.Action(name="show_example", payload={"action": "example"}, label="Show Example", tooltip="View a real-world example of this methodology"),
            cl.Action(name="next_phase", payload={"action": "next"}, label="Next Phase", tooltip="Progress to the next workshop phase"),
            cl.Action(name="think_through", payload={"action": "think"}, label="Think Through", tooltip="Systematically break down the problem"),
        ]

    # Add clear context button
    actions.append(cl.Action(
        name="clear_context",
        payload={"action": "clear"},
        label="Clear Context",
        description="Start fresh without previous history",
        tooltip="🗑️ Clear conversation history and start fresh with this bot"
    ))

    # Generate a handoff response from the new bot
    handoff_prompt = f"""You are {new_bot.get('name')}. The user just switched to you from {old_bot.get('name')}.

Here's the conversation context:
{chr(10).join([f"{m.get('role')}: {m.get('content', '')[:300]}" for m in history[-4:]])}

Briefly (2-3 sentences):
1. Acknowledge the switch
2. Explain how YOUR perspective/methodology differs
3. Ask a probing question that leverages your specialty

Be direct and engaging. Show your unique value."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=handoff_prompt,
            config=types.GenerateContentConfig(
                system_instruction=new_bot.get("system_prompt", ""),
                temperature=0.7,
                max_output_tokens=300
            )
        )
        handoff_message = response.text.strip()
    except Exception as e:
        handoff_message = f"I'm {new_bot.get('name')}. I've received the context from your conversation with {old_bot.get('name')}. How can I apply my expertise here?"

    # Send the handoff message
    await cl.Message(
        content=f"**{new_bot.get('emoji', '')} Switched to {new_bot.get('name')}**\n\n{handoff_message}",
        actions=actions
    ).send()

    # Add to history
    history.append({"role": "model", "content": handoff_message})
    cl.user_session.set("history", history)


@cl.action_callback("show_example")
async def on_show_example(action: cl.Action):
    """Show example — LazyGraph → File Search → Fit Analysis → Tavily → Story.

    Pipeline:
    1. LazyGraph: get related concepts, frameworks, techniques from Neo4j
    2. File Search (RAG): query PWS knowledge base for 1-3 relevant examples
    3. Fit analysis: Gemini understands conversation + graph + RAG to decide
       what kind of real-world example best fits the discussion
    4. Tavily: fetch real web sources for that specific example type
    5. Synthesis: Gemini writes a proper story (not search results) from all layers
    Falls back gracefully at every step.
    """
    current_phase = cl.user_session.get("current_phase", 0)
    chat_profile = cl.user_session.get("chat_profile", "lawrence")
    session_id = cl.user_session.get("id", "default")
    history = cl.user_session.get("history", [])

    recent_context = " ".join(
        [m.get("content", "") for m in history[-6:]]
    )[-1200:]

    # No conversation yet → static fallback
    if not recent_context.strip():
        await _show_fallback_example(chat_profile, current_phase, session_id)
        return

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("**📖 Finding a relevant example...**\n\n")

    # --- Step 1: LazyGraph — concepts & frameworks from Neo4j ---
    graph_hint = ""
    graph_concepts = []
    try:
        from tools.graphrag_lite import light_context, _extract_keywords
        keywords = _extract_keywords(recent_context)
        if keywords:
            hint, trace = light_context(recent_context[:500], context_type="auto")
            if hint:
                graph_hint = hint
                graph_concepts = trace.get("lazy_trace", {}).get("matched_concepts", [])
    except Exception as e:
        print(f"Example graph lookup error: {e}")

    # --- Step 2: Gemini File Search (RAG) — PWS knowledge base examples ---
    rag_examples = ""
    try:
        if FILE_SEARCH_ENABLED:
            from utils.dynamic_examples import BOT_TO_METHODOLOGY
            methodology = BOT_TO_METHODOLOGY.get(chat_profile, ["PWS"])[0]

            rag_query = (
                f"Find 1-3 specific examples or case studies from the PWS course materials "
                f"that relate to this topic: {recent_context[:400]}\n\n"
                f"Focus on real-world cases, historical parallels, or applied examples "
                f"from the {methodology} framework. Return concrete examples with names "
                f"and details, not methodology explanations."
            )

            file_search_tool = types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[FILE_SEARCH_STORE]
                )
            )

            rag_response = filesearch_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=rag_query,
                config=types.GenerateContentConfig(
                    tools=[file_search_tool],
                    temperature=0.3,
                    max_output_tokens=600,
                ),
            )

            if rag_response.text and len(rag_response.text.strip()) > 30:
                rag_examples = rag_response.text.strip()
    except Exception as e:
        print(f"Example File Search error: {e}")

    # --- Step 3: Fit analysis — understand what example type best matches ---
    example_direction = ""
    tavily_query = ""
    try:
        from utils.dynamic_examples import BOT_TO_METHODOLOGY
        methodology = BOT_TO_METHODOLOGY.get(chat_profile, ["PWS"])[0]

        graph_block = f"\nKnowledge graph concepts: {graph_hint}" if graph_hint else ""
        rag_block = f"\nPWS knowledge base examples:\n{rag_examples}" if rag_examples else ""

        fit_prompt = (
            f"Conversation:\n{recent_context}\n"
            f"{graph_block}"
            f"{rag_block}\n\n"
            f"The user is in a {methodology} workshop. Based on the conversation, "
            f"graph context, and any PWS examples found above:\n\n"
            f"1. What specific type of real-world example would best illuminate "
            f"what the user is discussing? (1 sentence)\n"
            f"2. A web search query (max 10 words) to find that specific example "
            f"— a concrete historical case, not a definition.\n\n"
            f"Return EXACTLY this format:\n"
            f"DIRECTION: [what kind of example fits best]\n"
            f"SEARCH: [the search query]"
        )

        fit_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=fit_prompt,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=80),
        )

        if fit_response.text:
            for line in fit_response.text.strip().split("\n"):
                line = line.strip()
                if line.upper().startswith("DIRECTION:"):
                    example_direction = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SEARCH:"):
                    tavily_query = line.split(":", 1)[1].strip().strip('"').strip("'")
    except Exception as e:
        print(f"Example fit analysis error: {e}")

    # --- Step 4: Tavily — fetch real-world sources for the example ---
    web_evidence = ""
    web_sources = []  # Store sources with URLs for display
    try:
        if tavily_query:
            from tools.tavily_search import search_web
            results = search_web(tavily_query, search_depth="basic", max_results=3)
            snippets = []
            for r in results.get("results", []):
                title = r.get("title", "")
                content = r.get("content", "")[:400]
                url = r.get("url", "")
                if content and url:
                    snippets.append(f"- {title}: {content} ({url})")
                    # Store for clickable display
                    web_sources.append({"title": title, "url": url})
            if snippets:
                web_evidence = "\n".join(snippets)
    except Exception as e:
        print(f"Example Tavily search error: {e}")

    # --- Step 5: Gemini synthesizes the final story ---
    try:
        parts = [f"Conversation context:\n{recent_context}"]
        if graph_hint:
            parts.append(f"Knowledge graph context: {graph_hint}")
        if rag_examples:
            parts.append(f"PWS knowledge base examples:\n{rag_examples}")
        if example_direction:
            parts.append(f"Best example type for this discussion: {example_direction}")
        if web_evidence:
            parts.append(f"Web research findings:\n{web_evidence}")

        synthesis_prompt = (
            "\n\n".join(parts) + "\n\n"
            "Using ALL of the above (conversation, graph, PWS examples, web sources), "
            "write ONE specific, real-world example that directly parallels what the "
            "user is discussing.\n\n"
            "CRITICAL RULES:\n"
            "- Write a COMPLETE paragraph (minimum 6-8 full sentences, 150-250 words)\n"
            "- Tell a STORY: specific names, dates, places, events, and outcomes\n"
            "- Include context: what was the situation, who was involved, what happened\n"
            "- Include outcome: what was the result, what lessons were learned\n"
            "- Do NOT explain methodology or frameworks — only the example itself\n"
            "- If PWS knowledge base had a relevant example, USE it as a starting "
            "point but enrich it with web source details\n"
            "- Connect the example back to the user's topic in 1 final sentence\n"
            "- NEVER cut off mid-sentence — finish every thought completely\n\n"
            "Format: **Title (Year/Era)**: The complete story in one full paragraph..."
        )

        # Increased max_output_tokens to 1200 to ensure complete paragraph generation
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=synthesis_prompt,
            config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=1200),
        )

        example_text = (response.text or "").strip()

        # If synthesis is too short (truncated/incomplete), retry with simpler prompt
        if example_text and len(example_text) < 200:
            retry_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=(
                    f"Write a complete 150-250 word paragraph about a real-world example "
                    f"related to: {recent_context[:300]}\n\n"
                    f"Include: specific names, dates, outcomes. "
                    f"Format: **Title (Year)**: Full story paragraph. "
                    f"Do NOT stop mid-sentence."
                ),
                config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=1500),
            )
            if retry_response.text and len(retry_response.text.strip()) > len(example_text):
                example_text = retry_response.text.strip()

        if example_text and len(example_text) > 30:
            # Source attribution with clickable links
            sources_used = []
            if graph_hint:
                sources_used.append("knowledge graph")
            if rag_examples:
                sources_used.append("PWS knowledge base")
            if web_sources:
                sources_used.append("web research")

            source_note = ""
            if sources_used:
                source_note = f"\n\n*Sourced from: {', '.join(sources_used)}.*"

            # Add clickable source links if we have web sources
            source_links = ""
            if web_sources:
                links = []
                for src in web_sources[:3]:  # Max 3 sources
                    title = src.get("title", "Source")[:50]  # Truncate long titles
                    url = src.get("url", "")
                    if url:
                        links.append(f"- [{title}]({url})")
                if links:
                    source_links = "\n\n**📚 Sources:**\n" + "\n".join(links)

            await msg.stream_token(example_text + source_note + source_links)
            # Add core action buttons so user can continue
            msg.actions = get_core_action_buttons(include_example=True)
            await msg.update()

            # Inject into history so the bot can reference it
            history.append({"role": "model", "content": f"[Example shown]\n{example_text}"})
            cl.user_session.set("history", history)
            return

    except Exception as e:
        print(f"Example synthesis error: {e}")

    # --- Fallback ---
    await msg.stream_token("*(Showing a general example instead.)*\n\n")
    msg.actions = get_core_action_buttons(include_example=True)
    await msg.update()
    await _show_fallback_example(chat_profile, current_phase, session_id)


async def _show_fallback_example(chat_profile: str, current_phase: int, session_id: str):
    """Fallback example from static/Neo4j/File Search pool."""
    try:
        from utils.dynamic_examples import (
            get_diverse_example,
            get_shown_examples,
            track_shown_example
        )

        exclude_recent = get_shown_examples(session_id)
        example = await get_diverse_example(
            bot_id=chat_profile,
            phase=current_phase,
            exclude_recent=exclude_recent
        )

        if "**" in example:
            title = example.split("**")[1] if len(example.split("**")) > 1 else f"example_{current_phase}"
        else:
            title = f"example_{current_phase}"
        track_shown_example(session_id, title)

        await cl.Message(content=f"**📖 Example:**\n\n{example}").send()

    except Exception as e:
        print(f"Dynamic example fetch error: {e}")
        fallback_examples = {
            "tta": "**Trending to the Absurd**: Push a trend to its extreme to reveal future problems. Example: 'What if 100% of workers are remote?' surfaces problems in collaboration, culture, and infrastructure.",
            "jtbd": "**Jobs to Be Done**: People don't buy products, they hire them for a job. Example: Milkshakes are 'hired' for a boring commute, not as a dessert.",
            "scurve": "**S-Curve Analysis**: Technologies progress through Era of Ferment → Dominant Design → Incremental Improvement. Know where your technology sits to time your innovation.",
            "redteam": "**Red Teaming**: Attack your own assumptions before the market does. 'What if customers won't pay?' 'What if a free alternative exists?'",
            "ackoff": "**Camera Test**: If a camera can't record it, it's interpretation, not data. '47 people in line' is data. 'Long line' is interpretation.",
            "lawrence": "**PWS Methodology**: Validate the problem is worth solving BEFORE building the solution. Is it Real? Can you Win? Is it Worth it?",
        }
        example = fallback_examples.get(chat_profile, "No specific example available.")
        await cl.Message(content=f"**📖 Example:**\n\n{example}").send()


@cl.action_callback("next_phase")
async def on_next_phase(action: cl.Action):
    """
    Handle next phase button click with user-controlled navigation.

    User explicitly chooses to advance - no auto-detection or auto-advance.
    """
    try:
        current_phase_idx = cl.user_session.get("current_phase", 0)
        bot_id = cl.user_session.get("bot_id", "scenario")
        phases = cl.user_session.get("phases", [])
        history = cl.user_session.get("history", [])
        user_context = cl.user_session.get("phase_context", {})
        force_advance = action.payload.get("force", False) if action.payload else False

        # === VALIDATION: Check for required data ===
        if not phases:
            await cl.Message(
                content="⚠️ **No workshop phases loaded.**\n\n"
                        "Please start a workshop first by selecting a methodology.",
                actions=[
                    cl.Action(name="switch_to_scenario", payload={}, label="🎯 Start Scenario Planning"),
                    cl.Action(name="switch_to_tta", payload={}, label="🔮 Start TTA Workshop")
                ]
            ).send()
            return

        if current_phase_idx is None:
            current_phase_idx = 0
            cl.user_session.set("current_phase", 0)

        # Validate phase index is within bounds
        if current_phase_idx < 0 or current_phase_idx >= len(phases):
            await cl.Message(
                content=f"⚠️ **Phase tracking issue detected.**\n\n"
                        f"Resetting to Phase 1. Your conversation history is preserved."
            ).send()
            cl.user_session.set("current_phase", 0)
            current_phase_idx = 0

        # Check if workshop is complete
        if current_phase_idx >= len(phases) - 1:
            await cl.Message(
                content="🎉 **Workshop Complete!**\n\n"
                        "You've completed all phases. What would you like to do?\n\n"
                        "• **Review** — See what you've accomplished\n"
                        "• **Synthesize** — Download a summary of your work\n"
                        "• **Go Back** — Return to a previous phase",
                actions=[
                    cl.Action(name="show_progress", payload={}, label="📊 Review Progress"),
                    cl.Action(name="synthesize_conversation", payload={}, label="📥 Synthesize"),
                    cl.Action(name="prev_phase", payload={}, label="← Go Back"),
                    cl.Action(name="clear_context", payload={}, label="🔄 Start Fresh"),
                ]
            ).send()
            return

        # Try to load enhanced phase configs for scenario bot
        current_config = {}
        next_config = {}
        use_smart_transition = False

        if bot_id == "scenario":
            try:
                from prompts.scenario_phases import get_phase_by_index
                current_config = get_phase_by_index(current_phase_idx)
                next_config = get_phase_by_index(current_phase_idx + 1)
                use_smart_transition = bool(current_config and next_config)
            except ImportError:
                pass

        extracted = {}

        # === STEP 1: Validate Current Phase ===
        if use_smart_transition and current_config and not force_advance:
            async with cl.Step(name="Checking Phase Completion", type="tool") as step:
                step.input = f"Validating {current_config.get('name', 'current phase')} deliverables..."

                try:
                    from tools.phase_validator import (
                        validate_phase_completion,
                        get_missing_deliverables,
                        generate_completion_guidance
                    )

                    is_complete, score, extracted = validate_phase_completion(
                        current_config, history, bot_id
                    )

                    # Store extracted context for future phases
                    user_context.update(extracted)
                    cl.user_session.set("phase_context", user_context)

                    step.output = f"Completion: {score:.0%} | Found: {len(extracted)} deliverables"

                except Exception as e:
                    is_complete = True
                    score = 1.0
                    step.output = f"Validation skipped: {str(e)[:50]}"

            # If incomplete and low score, offer guidance
            if not is_complete and score < 0.5:
                missing = get_missing_deliverables(current_config, extracted)
                guidance = generate_completion_guidance(current_config, score, missing)

                await cl.Message(
                    content=f"📊 **Phase Progress: {score:.0%}**\n\n{guidance}\n\n"
                            f"*You can proceed anyway or continue working on this phase.*",
                    actions=[
                        cl.Action(name="next_phase", payload={"force": True}, label="Proceed Anyway →"),
                        cl.Action(name="show_example", payload={}, label="📖 Example"),
                        cl.Action(name="deep_research", payload={}, label="🔍 Research"),
                    ]
                ).send()
                return

        # === STEP 2: Advance Phase State ===
        phases[current_phase_idx]["status"] = "done"
        phases[current_phase_idx + 1]["status"] = "running"
        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", current_phase_idx + 1)

        # === Recursive Intelligence: Log phase completion ===
        if SESSION_LOGGER_ENABLED:
            session_id = cl.user_session.get("id")
            completed_phase_name = phases[current_phase_idx].get("name", f"Phase {current_phase_idx + 1}")
            if session_id:
                await log_session_event(
                    session_id=session_id,
                    event_type="phase_completion",
                    agent=bot_id,
                    phase_name=completed_phase_name,
                    turn_count=len(history),
                    metadata={
                        "phase_index": current_phase_idx,
                        "next_phase": phases[current_phase_idx + 1].get("name") if current_phase_idx + 1 < len(phases) else None,
                        "total_phases": len(phases)
                    }
                )

        # Update WorkshopRoadmap
        bot = BOTS.get(bot_id, BOTS["lawrence"])
        phase_insights = extract_phase_insights(history, phases, current_phase_idx + 1)
        await create_or_update_roadmap(
            phases=phases,
            current_phase=current_phase_idx + 1,
            bot_name=bot.get("name", "Workshop"),
            bot_icon=bot.get("icon", "🎯"),
            phase_context=phase_insights
        )

        # Update sidebar to reflect phase progress
        await update_sidebar_phase(current_phase_idx + 1)

        # Sync to context_store (QA-002 fix)
        context_key = get_context_key()
        if context_key in context_store:
            context_store[context_key]["phases"] = [p.copy() for p in phases]
            context_store[context_key]["current_phase"] = current_phase_idx + 1

        # === CRITICAL: Persist phase transition to Supabase ===
        # Phase transitions are key checkpoints - save immediately
        try:
            from utils.context_persistence import save_cross_bot_context
            last_checkpoint = datetime.utcnow().isoformat()
            cl.user_session.set("last_checkpoint", last_checkpoint)

            # BUG-001 FIX: Preserve excluded_topics on phase transition
            await save_cross_bot_context(
                user_key=context_key,
                history=history.copy(),
                bot_id=bot_id,
                bot_name=BOTS.get(bot_id, {}).get("name", bot_id),
                phases=[p.copy() for p in phases],
                current_phase=current_phase_idx + 1,
                conversation_id=cl.user_session.get("conversation_id"),
                conversation_name=cl.user_session.get("conversation_name", ""),
                excluded_topics=cl.user_session.get("excluded_topics", [])
            )
            logger.info(f"[PERSISTENCE] Phase transition saved: phase {current_phase_idx + 1} -> {current_phase_idx + 2}")
        except Exception as e:
            logger.warning(f"[PERSISTENCE] Phase transition save failed: {e}")

        # === STEP 3: Generate Smart Transition ===
        if use_smart_transition and next_config:
            async with cl.Step(name="Preparing Next Phase", type="tool") as step:
                step.input = f"Loading context for {next_config.get('name', 'next phase')}..."

                try:
                    from tools.phase_enricher import get_phase_transition_context

                    transition_content = get_phase_transition_context(
                        from_phase=current_config,
                        to_phase=next_config,
                        user_context=user_context,
                        extracted_deliverables=extracted
                    )

                    step.output = f"Ready: {next_config.get('name')}"

                except Exception as e:
                    # Fallback to basic transition
                    transition_content = None
                    step.output = f"Using basic transition: {str(e)[:50]}"

            if transition_content:
                # Soft transition with navigation buttons
                await cl.Message(
                    content=f"───── 📍 Phase {current_phase_idx + 2}/{len(phases)}: {phases[current_phase_idx + 1]['name']} ─────\n\n"
                            f"{transition_content}",
                    actions=get_phase_navigation_buttons(current_phase_idx + 1, len(phases))
                ).send()
                return

        # === FALLBACK: Soft Basic Transition ===
        phase_num = current_phase_idx + 2
        phase_name = phases[current_phase_idx + 1]["name"]
        completed_count = sum(1 for p in phases if p["status"] == "done")
        total_count = len(phases)

        # Get instructions from next_config if available
        instructions_text = ""
        if next_config and next_config.get("instructions"):
            instructions_text = "\n\n" + "\n".join(
                [f"• {inst}" for inst in next_config.get("instructions", [])[:4]]
            )

        prompt_text = ""
        if next_config and next_config.get("prompt"):
            prompt_text = f"\n\n*{next_config.get('prompt')}*"

        # Soft, non-disruptive phase transition (Quick Win UX)
        await cl.Message(
            content=(
                f"───── 📍 Phase {phase_num}/{total_count}: {phase_name} ─────\n\n"
                f"*{completed_count} of {total_count} phases completed*"
                f"{instructions_text}"
                f"{prompt_text}"
            ),
            actions=get_phase_navigation_buttons(current_phase_idx + 1, total_count)
        ).send()

    except Exception as e:
        # Graceful error handling - don't crash, help the user
        print(f"Phase transition error: {e}")
        await cl.Message(
            content=f"⚠️ **Unable to transition to next phase.**\n\n"
                    f"This may be due to missing session data. "
                    f"Your conversation is preserved - you can continue working here.\n\n"
                    f"*Error: {str(e)[:100]}*",
            actions=[
                cl.Action(name="show_progress", payload={}, label="📊 View Progress"),
                cl.Action(name="stay_phase", payload={}, label="Continue Here"),
            ]
        ).send()


@cl.action_callback("prev_phase")
async def on_prev_phase(action: cl.Action):
    """
    Navigate back to previous phase.

    Quick Win UX improvement: Users should be able to go back
    without losing their work or restarting the workshop.
    """
    try:
        phases = cl.user_session.get("phases", [])
        current_phase_idx = cl.user_session.get("current_phase", 0)
        bot_id = cl.user_session.get("bot_id", "lawrence")
        bot = BOTS.get(bot_id, BOTS["lawrence"])

        # Validate we have phases
        if not phases:
            await cl.Message(content="⚠️ No workshop phases loaded.").send()
            return

        # Check if already at first phase
        if current_phase_idx <= 0:
            await cl.Message(
                content="📍 You're already at the first phase.",
                actions=get_phase_navigation_buttons(0, len(phases))
            ).send()
            return

        # Update phase states
        phases[current_phase_idx]["status"] = "pending"
        phases[current_phase_idx - 1]["status"] = "running"

        cl.user_session.set("phases", phases)
        cl.user_session.set("current_phase", current_phase_idx - 1)

        # Update WorkshopRoadmap
        history = cl.user_session.get("history", [])
        phase_insights = extract_phase_insights(history, phases, current_phase_idx - 1)
        await create_or_update_roadmap(
            phases=phases,
            current_phase=current_phase_idx - 1,
            bot_name=bot.get("name", "Workshop"),
            bot_icon=bot.get("icon", "🎯"),
            phase_context=phase_insights
        )

        # Sync to context_store + persist
        context_key = get_context_key()
        if context_key in context_store:
            context_store[context_key]["phases"] = [p.copy() for p in phases]
            context_store[context_key]["current_phase"] = current_phase_idx - 1
            asyncio.create_task(_persist_context_async(context_key))

        # Soft transition message (non-disruptive)
        phase_name = phases[current_phase_idx - 1]["name"]
        new_phase_num = current_phase_idx  # 1-indexed for display

        await cl.Message(
            content=f"───── 📍 Phase {new_phase_num}/{len(phases)}: {phase_name} ─────\n\n"
                    f"*Returned to previous phase. Your work is preserved.*",
            actions=get_phase_navigation_buttons(current_phase_idx - 1, len(phases))
        ).send()

    except Exception as e:
        print(f"Prev phase error: {e}")
        await cl.Message(
            content=f"⚠️ Unable to go back: {str(e)[:100]}"
        ).send()


@cl.action_callback("explore_gaps")
async def on_explore_gaps(action: cl.Action):
    """
    Handle 'Explore Gaps' button from phase insights.

    When the AI identifies missing elements in the current phase,
    the user can click this to get guided exploration of those gaps.
    """
    try:
        phases = cl.user_session.get("phases", [])
        current_phase_idx = cl.user_session.get("current_phase", 0)
        bot_id = cl.user_session.get("bot_id", "lawrence")
        bot = BOTS.get(bot_id, BOTS["lawrence"])
        history = cl.user_session.get("history", [])

        if not phases or not SMART_PHASE_ENABLED:
            await cl.Message(
                content="Let's continue exploring this phase. What would you like to focus on?",
                actions=get_phase_navigation_buttons(current_phase_idx, len(phases)) if phases else None
            ).send()
            return

        # Get the current workshop state to find gaps
        workshop_state = await analyze_workshop_state(
            conversation_history=history,
            workshop_type=bot_id,
            current_phase_index=current_phase_idx,
            phases=phases
        )

        # Find current phase gaps
        current_phase_status = None
        for phase in workshop_state.phases:
            if phase.status == "in_progress":
                current_phase_status = phase
                break

        if current_phase_status and current_phase_status.missing_elements:
            gaps = current_phase_status.missing_elements[:3]
            phase_name = current_phase_status.name

            gaps_list = "\n".join([f"• {g}" for g in gaps])
            guidance = f"**🎯 Exploring Remaining Topics in {phase_name}**\n\n"
            guidance += f"Based on our conversation, here are areas we haven't fully covered:\n\n{gaps_list}\n\n"
            guidance += "Which of these would you like to explore? Or share your thoughts on any of them."

            await cl.Message(
                content=guidance,
                actions=get_phase_navigation_buttons(current_phase_idx, len(phases))
            ).send()

            # Add to history as system guidance
            history.append({"role": "model", "content": f"[Phase guidance: Exploring gaps in {phase_name}]"})
            cl.user_session.set("history", history)
        else:
            # No specific gaps - general encouragement
            phase_name = phases[current_phase_idx]["name"] if current_phase_idx < len(phases) else "this phase"
            await cl.Message(
                content=f"**Let's continue with {phase_name}**\n\nWhat aspect would you like to explore further?",
                actions=get_phase_navigation_buttons(current_phase_idx, len(phases))
            ).send()

    except Exception as e:
        print(f"Explore gaps error: {e}")
        await cl.Message(
            content="Let's continue exploring. What would you like to discuss?",
            actions=get_phase_navigation_buttons(
                cl.user_session.get("current_phase", 0),
                len(cl.user_session.get("phases", []))
            )
        ).send()


@cl.action_callback("explore_more")
async def on_explore_more(action: cl.Action):
    """
    Handle 'Explore More' button from phase completion insights.

    When the AI thinks a phase is complete, the user can choose to
    explore more before advancing.
    """
    try:
        phases = cl.user_session.get("phases", [])
        current_phase_idx = cl.user_session.get("current_phase", 0)
        bot_id = cl.user_session.get("bot_id", "lawrence")
        bot = BOTS.get(bot_id, BOTS["lawrence"])
        history = cl.user_session.get("history", [])

        phase_name = phases[current_phase_idx]["name"] if current_phase_idx < len(phases) else "this phase"

        # Get workshop state for context
        if SMART_PHASE_ENABLED and len(history) >= 2:
            workshop_state = await analyze_workshop_state(
                conversation_history=history,
                workshop_type=bot_id,
                current_phase_index=current_phase_idx,
                phases=phases
            )

            # Find what was covered
            current_phase_status = None
            for phase in workshop_state.phases:
                if phase.status == "in_progress" or phase.name.lower() == phase_name.lower():
                    current_phase_status = phase
                    break

            if current_phase_status and current_phase_status.completion_evidence:
                evidence = current_phase_status.completion_evidence[:3]
                evidence_list = "\n".join([f"• {e}" for e in evidence])

                guidance = f"**🔍 Continuing to Explore {phase_name}**\n\n"
                guidance += f"We've covered:\n{evidence_list}\n\n"
                guidance += "What else would you like to dive deeper into? Any questions or areas that need more attention?"
            else:
                guidance = f"**🔍 Exploring More in {phase_name}**\n\n"
                guidance += "What aspect would you like to explore further? Any questions or insights?"
        else:
            guidance = f"**🔍 Exploring More in {phase_name}**\n\n"
            guidance += "What would you like to discuss further?"

        await cl.Message(
            content=guidance,
            actions=get_phase_navigation_buttons(current_phase_idx, len(phases))
        ).send()

    except Exception as e:
        print(f"Explore more error: {e}")
        await cl.Message(
            content="Let's continue exploring. What would you like to discuss?",
            actions=get_phase_navigation_buttons(
                cl.user_session.get("current_phase", 0),
                len(cl.user_session.get("phases", []))
            )
        ).send()


@cl.action_callback("show_full_progress")
async def on_show_full_progress(action: cl.Action):
    """
    Handle 'Full Progress' button from phase insights.

    Shows detailed AI-analyzed progress across all phases.
    Essentially a convenience redirect to show_progress with enhanced formatting.
    """
    # Delegate to existing show_progress handler
    await on_show_progress(action)


@cl.action_callback("summarize_journal")
async def on_summarize_journal(action: cl.Action):
    """
    Generate an AI summary of the conversation journal.

    Uses the LLM to create a concise summary of key insights,
    decisions, and progress from the journal entries.
    """
    try:
        session_id = str(cl.user_session.get("id", ""))
        bot_id = cl.user_session.get("bot_id", "lawrence")

        # Try to get entries from Supabase first
        try:
            from protocols.context_journal import get_journal

            journal = get_journal(session_id)
            entries = journal.get_entries_from_supabase(limit=30)

            if not entries:
                # Fallback to MD file
                content = journal.read_all()
                if not content or len(content) < 100:
                    await cl.Message(content="📔 **Journal is empty**\n\nNo entries to summarize yet.").send()
                    return
                journal_text = content
            else:
                # Format entries for summarization
                journal_text = "\n\n".join([
                    f"[{e.get('entry_type', 'entry').upper()}] ({e.get('bot_id', 'agent')}): {e.get('content', '')}"
                    for e in entries
                ])

        except ImportError:
            await cl.Message(content="Journal system not available.").send()
            return

        # Generate summary using LLM
        async with cl.Step(name="Summarizing Journal", type="llm") as step:
            step.input = f"Summarizing {len(entries) if entries else 'all'} journal entries"

            summary_prompt = f"""Summarize this conversation journal concisely. Focus on:
1. Key insights discovered (💡)
2. Important decisions made (✅)
3. Main topics explored
4. Current status and next steps

Journal content:
{journal_text[:8000]}

Provide a clear, bulleted summary in 150-200 words."""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=summary_prompt
            )

            summary = response.text.strip()
            step.output = f"Generated summary ({len(summary)} chars)"

        await cl.Message(
            content=f"## 📔 Journal Summary\n\n{summary}",
            actions=[
                cl.Action(name="view_full_journal", payload={}, label="📄 View Full Journal")
            ]
        ).send()

    except Exception as e:
        print(f"Journal summarize error: {e}")
        await cl.Message(content=f"Could not generate summary: {str(e)[:100]}").send()


@cl.action_callback("view_full_journal")
async def on_view_full_journal(action: cl.Action):
    """
    Display the full conversation journal in a readable format.

    Shows all entries from the current session's journal.
    """
    try:
        session_id = str(cl.user_session.get("id", ""))

        try:
            from protocols.context_journal import get_journal

            journal = get_journal(session_id)

            # Try Supabase first
            entries = journal.get_entries_from_supabase(limit=100)

            if entries:
                # Format entries nicely
                formatted = "## 📔 Full Conversation Journal\n\n"
                formatted += f"**Session:** `{session_id[:8]}...`\n"
                formatted += f"**Entries:** {len(entries)}\n\n---\n\n"

                for entry in entries:
                    icon_map = {
                        "insight": "💡", "decision": "✅", "reasoning": "🧠",
                        "observation": "👁️", "action": "⚡", "switch": "🔄",
                        "extraction": "📋"
                    }
                    icon = icon_map.get(entry.get("entry_type", "").lower(), "📝")
                    entry_type = entry.get("entry_type", "entry").title()
                    bot = entry.get("bot_id", "agent")
                    turn = entry.get("turn_number", 0)
                    content = entry.get("content", "")

                    formatted += f"### {icon} {entry_type} ({bot}) — Turn {turn}\n"
                    formatted += f"{content}\n\n"

            else:
                # Fallback to MD file
                content = journal.read_all()
                if content:
                    formatted = f"## 📔 Full Conversation Journal\n\n{content}"
                else:
                    formatted = "📔 **Journal is empty**\n\nNo entries recorded yet."

        except ImportError:
            formatted = "Journal system not available."

        # Send as text element for better readability
        await cl.Message(
            content=formatted[:10000],  # Limit to avoid message size issues
            actions=[
                cl.Action(name="summarize_journal", payload={}, label="✨ Summarize")
            ]
        ).send()

    except Exception as e:
        print(f"View journal error: {e}")
        await cl.Message(content=f"Could not load journal: {str(e)[:100]}").send()


@cl.action_callback("show_progress")
async def on_show_progress(action: cl.Action):
    """Handle show progress button click with smart phase analysis."""
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)
    bot_id = cl.user_session.get("bot_id", "lawrence")
    bot = BOTS.get(bot_id, BOTS["lawrence"])
    history = cl.user_session.get("history", [])

    if not phases:
        await cl.Message(content="No workshop phases configured for this bot.").send()
        return

    # === SMART PROGRESS ANALYSIS ===
    if SMART_PHASE_ENABLED and len(history) >= 2:
        try:
            async with cl.Step(name="Analyzing Progress", type="tool") as step:
                step.input = "Using AI to analyze actual conversation progress..."

                workshop_state = await analyze_workshop_state(
                    conversation_history=history,
                    workshop_type=bot_id,
                    current_phase_index=current_phase,
                    phases=phases
                )

                # Build smart progress display
                progress_text = f"**📊 Workshop Progress: {bot.get('name', 'Workshop')}**\n\n"

                for i, phase_status in enumerate(workshop_state.phases):
                    if phase_status.status == "completed":
                        emoji = "✅"
                        detail = f" - *{len(phase_status.completion_evidence)} criteria met*"
                    elif phase_status.status == "in_progress":
                        emoji = "🔵"
                        missing = len(phase_status.missing_elements)
                        detail = f" - *{missing} item{'s' if missing != 1 else ''} remaining*"
                    else:
                        emoji = "⚪"
                        detail = ""

                    progress_text += f"{emoji} **Phase {i+1}:** {phase_status.name}{detail}\n"

                progress_text += f"\n---\n\n**Current Phase:** {workshop_state.current_phase_name}\n"
                progress_text += f"**Next Step:** {workshop_state.next_action}\n\n"
                progress_text += f"*{workshop_state.progress_summary}*"

                step.output = f"Phase {workshop_state.current_phase_index + 1}/{len(phases)}"

            # Show with user-controlled actions (always available, not based on should_advance)
            actions = []
            if current_phase < len(phases) - 1:
                next_name = phases[current_phase + 1]["name"]
                actions.append(cl.Action(
                    name="next_phase",
                    payload={"from_progress": True},
                    label=f"→ Move to {next_name}"
                ))

            # Always show "keep working" option
            actions.append(cl.Action(
                name="stay_phase",
                payload={},
                label="Continue Working Here"
            ))

            await cl.Message(content=progress_text, actions=actions).send()
            return

        except Exception as e:
            print(f"Smart progress analysis failed: {e}")
            # Fall through to basic progress display

    # === FALLBACK: Basic Progress Display using WorkshopRoadmap ===
    try:
        phase_insights = extract_phase_insights(history, phases, current_phase)
        await create_or_update_roadmap(
            phases=phases,
            current_phase=current_phase,
            bot_name=bot.get("name", "Workshop"),
            bot_icon=bot.get("icon", "🎯"),
            phase_context=phase_insights
        )
    except Exception:
        # Last resort: text-based progress
        progress_text = "**📊 Workshop Progress:**\n\n"
        for i, phase in enumerate(phases):
            if phase["status"] == "done":
                emoji = "✅"
            elif phase["status"] == "running" or i == current_phase:
                emoji = "🔄"
            else:
                emoji = "⬜"
            progress_text += f"{emoji} **Phase {i+1}:** {phase['name']}\n"

        completed = sum(1 for p in phases if p["status"] == "done")
        progress_text += f"\n**Progress: {completed}/{len(phases)} phases complete**"

        await cl.Message(content=progress_text).send()


@cl.action_callback("help_start_phase")
async def on_help_start_phase(action: cl.Action):
    """
    Help user start the current phase by generating a guided response.
    This directly calls the LLM to walk them through the phase.
    """
    phase_name = action.payload.get("phase_name", "this phase")
    phase_idx = action.payload.get("phase", 0)
    bot_id = cl.user_session.get("bot_id", "scenario")
    bot = BOTS.get(bot_id, BOTS["lawrence"])

    # Get phase-specific instructions and prompt
    phase_instructions = []
    phase_prompt = ""
    try:
        if bot_id == "scenario":
            from prompts.scenario_phases import get_phase_by_index
            phase_config = get_phase_by_index(phase_idx)
            if phase_config:
                phase_instructions = phase_config.get("instructions", [])
                phase_prompt = phase_config.get("prompt", "")
    except ImportError:
        pass

    # Build the help request
    help_request = f"Help me start {phase_name}."

    # Show user's request
    await cl.Message(content=help_request, author="User").send()

    # Add to history
    history = cl.user_session.get("history", [])
    history.append({"role": "user", "content": help_request})

    # Build context for LLM
    phase_context = f"\n\n[PHASE GUIDANCE: The user is starting '{phase_name}'. "
    if phase_instructions:
        phase_context += f"They need to: {'; '.join(phase_instructions)}. "
    if phase_prompt:
        phase_context += f"Start with this question: {phase_prompt}"
    phase_context += "]"

    # Generate response
    msg = cl.Message(content="")
    await msg.send()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        # Build messages
        messages = []
        for h in history[-10:]:  # Last 10 messages for context
            role = "user" if h.get("role") == "user" else "model"
            messages.append({"role": role, "parts": [{"text": h.get("content", "")}]})

        # Add the help request with phase context
        messages.append({"role": "user", "parts": [{"text": help_request + phase_context}]})

        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=bot.get("system_prompt", ""),
                temperature=0.7,
                max_output_tokens=800
            )
        )

        full_response = ""
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                await msg.stream_token(chunk.text)

        await msg.update()

        # Update history
        history.append({"role": "model", "content": full_response})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"I'll help you with **{phase_name}**. Let's start!\n\n")
        if phase_instructions:
            for i, instruction in enumerate(phase_instructions, 1):
                await msg.stream_token(f"{i}. {instruction}\n")
        if phase_prompt:
            await msg.stream_token(f"\n**Let's begin:** {phase_prompt}")
        await msg.update()

    # Reset turn counter
    cl.user_session.set("phase_turn_count", 0)


@cl.action_callback("acknowledge_phase")
async def on_acknowledge_phase(action: cl.Action):
    """User acknowledges they understand the phase and will work on it."""
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)
    current_name = phases[current_phase]["name"] if current_phase < len(phases) else "current phase"

    await cl.Message(
        content=f"👍 Great! I'm here to help with **{current_name}**. Just ask when you need guidance.",
    ).send()

    # Reset turn counter
    cl.user_session.set("phase_turn_count", 0)


@cl.action_callback("stay_phase")
async def on_stay_phase(action: cl.Action):
    """User wants to continue working on current phase (from nudge)."""
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)
    current_name = phases[current_phase]["name"] if current_phase < len(phases) else "current phase"

    await cl.Message(
        content=f"👍 No problem! Let's keep working on **{current_name}**. What would you like to explore?",
    ).send()

    # Reset turn counter
    cl.user_session.set("phase_turn_count", 0)


@cl.action_callback("show_dikw_pyramid")
async def on_show_dikw_pyramid(action: cl.Action):
    """Handle showing the DIKW pyramid visualization using interactive custom element."""
    # Get the current phase to potentially highlight
    current_phase = cl.user_session.get("current_phase", 0)

    # Map phase index to DIKW level for highlighting
    highlight_map = {
        2: "data",          # Data Level
        3: "information",   # Information Level
        4: "knowledge",     # Knowledge Level
        5: "understanding", # Understanding Level
        6: "wisdom",        # Wisdom Level
    }

    highlight = highlight_map.get(current_phase)

    explanation = """**The DIKW Pyramid** shows the hierarchy of understanding.
Click any level to explore it in depth.

**Climb UP** to explore and understand a problem.
**Climb DOWN** to validate that your solution is grounded in reality."""

    # Try to use custom interactive element first
    try:
        element = cl.CustomElement(
            name="DIKWPyramid",
            props={
                "highlightLevel": highlight,
                "scores": {},
                "showDescriptions": True
            }
        )

        await cl.Message(
            content=explanation,
            elements=[element]
        ).send()
    except Exception:
        # Fallback to Plotly chart
        from utils.charts import create_dikw_pyramid

        pyramid_chart = await create_dikw_pyramid(
            highlight_level=highlight,
            title="Ackoff's DIKW Pyramid - Validation Framework"
        )

        fallback_explanation = """**The DIKW Pyramid** shows the hierarchy of understanding:

- **Data**: Raw observations (Camera Test: Could a camera record it?)
- **Information**: Organized, contextualized data (What does it mean?)
- **Knowledge**: Patterns and relationships (What patterns emerge?)
- **Understanding**: Cause and effect (Why does it happen?)
- **Wisdom**: Judgment and decisions (What should we do?)

**Climb UP** to explore and understand a problem.
**Climb DOWN** to validate that your solution is grounded in reality.
"""

        await cl.Message(
            content=fallback_explanation,
            elements=[pyramid_chart]
        ).send()


@cl.action_callback("explore_dikw_level")
async def on_explore_dikw_level(action: cl.Action):
    """Handle clicking on a DIKW pyramid level to explore it."""
    level = action.payload.get("level", "data")

    # Detailed explanations and guiding questions for each level
    level_content = {
        "data": {
            "title": "📊 Data Level - Raw Observations",
            "description": """**Data** is raw, unprocessed facts. The foundation of the pyramid.

**Camera Test:** Could a video camera record this? If yes, it's data.

**Examples of Data:**
- "5 customers complained today"
- "Sales were $50,000 last month"
- "The button is red"
- "Users spent 3 minutes on the page"

**Guiding Questions:**
1. What can you directly observe about your problem?
2. What numbers or facts do you have?
3. Can you point to specific, recordable events?

**Action:** List 3-5 pieces of raw data relevant to your problem.""",
        },
        "information": {
            "title": "📋 Information Level - Organized Data",
            "description": """**Information** is data that has been processed, organized, or given context.

**Transformation:** Data + Organization = Information

**Examples of Information:**
- "Customer complaints increased 25% this month" (data + comparison)
- "Most complaints come from Enterprise users" (data + segmentation)
- "Sales peak on Tuesdays" (data + pattern)

**Guiding Questions:**
1. What patterns do you see in your data?
2. How can you categorize or segment your observations?
3. What comparisons reveal insights?

**Action:** Take your data and organize it - find patterns, make comparisons.""",
        },
        "knowledge": {
            "title": "🧠 Knowledge Level - Understanding Relationships",
            "description": """**Knowledge** is understanding how things relate and why.

**Transformation:** Information + Relationships = Knowledge

**Examples of Knowledge:**
- "Enterprise complaints rise after we ship features without consulting them"
- "Tuesday sales peak because that's when our newsletter goes out"
- "Users leave after 3 minutes because the signup process is confusing"

**Guiding Questions:**
1. Why do these patterns exist?
2. What causes lead to these effects?
3. How do different pieces of information connect?

**Action:** For each piece of information, ask "Why?" and "What causes this?" """,
        },
        "wisdom": {
            "title": "💡 Wisdom Level - Good Judgment",
            "description": """**Wisdom** is knowing what to do with your knowledge. It's judgment.

**Transformation:** Knowledge + Judgment = Wisdom

**Examples of Wisdom:**
- "We should involve Enterprise customers in beta testing before shipping"
- "We should send our newsletter on other days to spread revenue risk"
- "We should simplify signup - it's more important than adding features"

**Guiding Questions:**
1. What should we do differently based on what we know?
2. What trade-offs are we willing to make?
3. What's the most important insight to act on first?

**Action:** Based on your knowledge, what's one specific action you recommend?""",
        },
    }

    content = level_content.get(level, level_content["data"])

    await cl.Message(
        content=f"{content['title']}\n\n{content['description']}",
        actions=[
            cl.Action(
                name="show_dikw_pyramid",
                payload={},
                label="↩️ Back to Pyramid",
                description="Return to the full DIKW pyramid view"
            )
        ]
    ).send()


@cl.action_callback("show_scurve")
async def on_show_scurve(action: cl.Action):
    """Handle showing the S-Curve visualization."""
    from utils.charts import create_scurve_chart

    # Default to early stage, could be customized based on context
    scurve_chart = await create_scurve_chart(
        title="Technology S-Curve - Adoption Lifecycle",
        current_position=0.3  # Default to dominant design phase
    )

    explanation = """**The Technology S-Curve** shows how technologies evolve:

- **Era of Ferment** (0-25%): Many competing approaches, high uncertainty, no clear winner
- **Dominant Design** (25-50%): Industry converges on a standard, optimization begins
- **Incremental Change** (50-75%): Refinement and efficiency improvements
- **Maturity/Discontinuity** (75-100%): Performance limits approached, watch for the next curve

**Key Question**: Where does your technology sit on this curve?
- Too early = high risk, may run out of resources
- Too late = fighting established giants
- Right timing = ride the wave
"""

    await cl.Message(
        content=explanation,
        elements=[scurve_chart]
    ).send()


@cl.action_callback("watch_video")
async def on_watch_video(action: cl.Action):
    """Handle watching tutorial video for current phase."""
    from utils.media import get_workshop_video, WORKSHOP_VIDEOS

    bot = cl.user_session.get("bot", BOTS["lawrence"])
    bot_id = None

    # Find the bot_id from current bot
    for bid, bdata in BOTS.items():
        if bdata.get("name") == bot.get("name"):
            bot_id = bid
            break

    if not bot_id:
        bot_id = "lawrence"

    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])

    # Determine which video to show
    phase_key = f"phase_{current_phase + 1}" if current_phase > 0 else "intro"

    # Try to get the phase-specific video, fall back to intro
    video = await get_workshop_video(bot_id, phase_key)

    if not video:
        # Check if any videos are configured for this bot
        bot_videos = WORKSHOP_VIDEOS.get(bot_id, {})
        configured_videos = [p for p, url in bot_videos.items() if url]

        if not configured_videos:
            await cl.Message(
                content=f"""**No tutorial videos configured yet for {bot.get('name', 'this workshop')}.**

To add videos, update `WORKSHOP_VIDEOS` in `utils/media.py`:

```python
WORKSHOP_VIDEOS["{bot_id}"] = {{
    "intro": "https://youtube.com/watch?v=YOUR_VIDEO_ID",
    "phase_1": "https://youtube.com/watch?v=PHASE1_VIDEO",
    # ... more phases
}}
```

Or set videos programmatically:
```python
from utils.media import set_workshop_video
set_workshop_video("{bot_id}", "intro", "https://youtube.com/watch?v=...")
```
"""
            ).send()
        else:
            # Some videos exist, but not for current phase
            await cl.Message(
                content=f"No video available for Phase {current_phase + 1}. Videos exist for: {', '.join(configured_videos)}"
            ).send()
        return

    # Get current phase name
    phase_name = phases[current_phase]["name"] if phases and current_phase < len(phases) else "Introduction"

    await cl.Message(
        content=f"**🎬 Tutorial Video: {phase_name}**\n\nWatch the video below for guidance on this phase:",
        elements=[video]
    ).send()


@cl.action_callback("listen_audiobook")
async def on_listen_audiobook(action: cl.Action):
    """Handle listening to PWS audiobook chapters."""
    from utils.media import (
        find_relevant_chapters,
        get_chapters_for_bot,
        get_audiobook_chapter,
        AUDIOBOOK_CHAPTERS
    )

    bot_id = cl.user_session.get("chat_profile", "lawrence")
    history = cl.user_session.get("history", [])

    # Get recent conversation context for relevance matching
    recent_text = " ".join([
        msg.get("content", "")
        for msg in history[-6:]
    ])

    # Find relevant chapters based on conversation
    relevant_chapters = find_relevant_chapters(recent_text, bot_id, max_results=3)

    # If no relevant chapters found based on context, show all chapters for this bot
    if not relevant_chapters:
        all_chapters = get_chapters_for_bot(bot_id)
        if not all_chapters:
            await cl.Message(
                content=f"""**No audiobook chapters configured yet.**

To add audiobook chapters, update `AUDIOBOOK_CHAPTERS` in `utils/media.py`:

```python
from utils.media import set_audiobook_chapter

set_audiobook_chapter(
    topic="pws_foundation",
    chapter_id="chapter_1",
    url="https://your-supabase-url/audio/chapter1.mp3",
    title="Introduction to PWS",
    duration="15:00"
)
```

Or upload audio files to Supabase Storage and add URLs to the `AUDIOBOOK_CHAPTERS` dict.
"""
            ).send()
            return

        # Create action buttons for all available chapters
        chapter_actions = [
            cl.Action(
                name=f"play_chapter_{ch['topic']}_{ch['chapter_id']}",
                payload={"topic": ch['topic'], "chapter_id": ch['chapter_id']},
                label=f"▶️ {ch['title'][:30]}..." if len(ch['title']) > 30 else f"▶️ {ch['title']}",
                description=f"Duration: {ch['duration']}"
            )
            for ch in all_chapters[:4]  # Limit to 4 buttons
        ]

        await cl.Message(
            content=f"**📖 Available PWS Audiobook Chapters for {BOTS.get(bot_id, {}).get('name', 'this workshop')}:**\n\nSelect a chapter to listen:",
            actions=chapter_actions
        ).send()
        return

    # Show relevant chapters based on conversation context
    chapter_info = "\n".join([
        f"• **{ch['title']}** ({ch['duration']})"
        for ch in relevant_chapters
    ])

    chapter_actions = [
        cl.Action(
            name=f"play_chapter_{ch['topic']}_{ch['chapter_id']}",
            payload={"topic": ch['topic'], "chapter_id": ch['chapter_id']},
            label=f"▶️ {ch['title'][:30]}..." if len(ch['title']) > 30 else f"▶️ {ch['title']}",
            description=f"Duration: {ch['duration']}"
        )
        for ch in relevant_chapters
    ]

    await cl.Message(
        content=f"""**📖 Relevant PWS Audiobook Chapters**

Based on your conversation, these chapters may be helpful:

{chapter_info}

Select a chapter to listen:""",
        actions=chapter_actions
    ).send()


@cl.action_callback("play_chapter_pws_foundation_chapter_1")
@cl.action_callback("play_chapter_pws_foundation_chapter_2")
@cl.action_callback("play_chapter_pws_foundation_chapter_3")
@cl.action_callback("play_chapter_trending_to_absurd_chapter_1")
@cl.action_callback("play_chapter_trending_to_absurd_chapter_2")
@cl.action_callback("play_chapter_trending_to_absurd_chapter_3")
@cl.action_callback("play_chapter_jobs_to_be_done_chapter_1")
@cl.action_callback("play_chapter_jobs_to_be_done_chapter_2")
@cl.action_callback("play_chapter_jobs_to_be_done_chapter_3")
@cl.action_callback("play_chapter_s_curve_chapter_1")
@cl.action_callback("play_chapter_s_curve_chapter_2")
@cl.action_callback("play_chapter_s_curve_chapter_3")
@cl.action_callback("play_chapter_ackoffs_pyramid_chapter_1")
@cl.action_callback("play_chapter_ackoffs_pyramid_chapter_2")
@cl.action_callback("play_chapter_ackoffs_pyramid_chapter_3")
@cl.action_callback("play_chapter_red_teaming_chapter_1")
@cl.action_callback("play_chapter_red_teaming_chapter_2")
@cl.action_callback("play_chapter_red_teaming_chapter_3")
async def on_play_chapter(action: cl.Action):
    """Play a specific audiobook chapter."""
    from utils.media import get_audiobook_chapter, AUDIOBOOK_CHAPTERS

    payload = action.payload
    topic = payload.get("topic")
    chapter_id = payload.get("chapter_id")

    if not topic or not chapter_id:
        await cl.Message(content="Invalid chapter selection.").send()
        return

    # Get chapter metadata
    chapter_info = AUDIOBOOK_CHAPTERS.get(topic, {}).get(chapter_id, {})
    title = chapter_info.get("title", "Unknown Chapter")
    duration = chapter_info.get("duration", "")

    # Get audio element
    audio = await get_audiobook_chapter(topic, chapter_id)

    if not audio:
        await cl.Message(
            content=f"**Audio not available for: {title}**\n\nThe audiobook chapter URL has not been configured yet."
        ).send()
        return

    await cl.Message(
        content=f"**📖 Now Playing: {title}**\n\n*Duration: {duration}*",
        elements=[audio]
    ).send()


@cl.action_callback("export_summary")
async def on_export_summary(action: cl.Action):
    """Export workshop progress as downloadable markdown file."""
    from utils.media import export_workshop_summary

    bot = cl.user_session.get("bot", BOTS["lawrence"])
    phases = cl.user_session.get("phases", [])
    history = cl.user_session.get("history", [])
    current_phase = cl.user_session.get("current_phase", 0)

    if not phases:
        await cl.Message(content="No workshop progress to export.").send()
        return

    try:
        file_element = await export_workshop_summary(
            bot_name=bot.get("name", "Workshop"),
            phases=phases,
            history=history,
            current_phase=current_phase
        )

        await cl.Message(
            content="**Workshop Summary exported.** Click to download:",
            elements=[file_element]
        ).send()
    except Exception as e:
        await cl.Message(content=f"Export error: {str(e)}").send()


@cl.action_callback("assess_progress")
async def on_assess_progress(action: cl.Action):
    """Run the assessment engine on current conversation to evaluate user's progress."""
    history = cl.user_session.get("history", [])
    bot_id = cl.user_session.get("bot_id", "lawrence")
    bot = cl.user_session.get("bot", BOTS.get(bot_id, BOTS["lawrence"]))

    if len(history) < 4:
        await cl.Message(
            content="**Need more conversation first.** Continue chatting for a few more turns, then I can assess your progress.",
            actions=get_core_action_buttons(include_example=False),
        ).send()
        return

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("**Analyzing your progress...**\n\n")

    try:
        from tools.assessment_engine import run_full_assessment

        session_id = str(cl.user_session.get("id", "anonymous"))

        assessment = await run_full_assessment(
            content="\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:500]}"
                for m in history[-20:]
            ),
            user_id=session_id,
            session_id=session_id,
        )

        if assessment and assessment.get("report"):
            await msg.stream_token(assessment["report"])
        elif assessment and assessment.get("overall_score") is not None:
            score = assessment["overall_score"]
            await msg.stream_token(f"**Overall Score: {score}/100**\n\n")
            for module_name, module_result in assessment.get("modules", {}).items():
                module_score = module_result.get("score", "N/A")
                feedback = module_result.get("feedback", "")
                await msg.stream_token(f"- **{module_name}**: {module_score}/100 - {feedback}\n")
        else:
            await msg.stream_token("Assessment completed but no detailed report was generated. Keep engaging with the material!")

        # Display as GradeReveal custom element if available
        try:
            if assessment and assessment.get("overall_score") is not None:
                grade_element = cl.CustomElement(
                    name="GradeReveal",
                    props={
                        "score": assessment.get("overall_score", 0),
                        "grade": assessment.get("grade", ""),
                        "feedback": assessment.get("report", ""),
                        "botName": bot.get("name", "Assessment"),
                    },
                    display="inline",
                )
                await cl.Message(content="", elements=[grade_element]).send()
        except Exception:
            pass

    except ImportError:
        await msg.stream_token("The assessment engine is not available. Please check your installation.")
    except Exception as e:
        logger.error(f"[ASSESSMENT] Error: {e}")
        await msg.stream_token(f"Assessment encountered an error: {str(e)[:200]}")

    await msg.update()


@cl.action_callback("converge_answer")
async def on_converge_answer(action: cl.Action):
    """Stop exploring and give a direct, synthesized answer. The convergence mechanism."""
    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["lawrence"])

    if len(history) < 4:
        await cl.Message(content="Let's explore a bit more before I give you a definitive answer.").send()
        return

    # Build the user's original question from early history
    user_messages = [m["content"] for m in history if m.get("role") == "user"]
    original_question = user_messages[0] if user_messages else "the topic we discussed"
    recent_context = "\n".join([
        f"{'User' if m.get('role') == 'user' else 'Larry'}: {m.get('content', '')[:300]}"
        for m in history[-10:]
    ])

    convergence_prompt = f"""The user has pressed "Give me your answer". They want you to STOP asking questions and DELIVER a direct, actionable answer.

ORIGINAL QUESTION: {original_question}

FULL CONVERSATION CONTEXT (last 10 messages):
{recent_context}

RULES:
1. DO NOT ask any more questions
2. Give a DIRECT answer — "Here's what I think..."
3. Structure it as: Answer → Evidence from our conversation → 3 concrete next steps
4. Be opinionated — take a position based on what you've learned
5. Keep it under 300 words
6. End with "If you want to explore further, just keep talking."

Use Larry's voice: conversational, direct, provocative."""

    try:
        msg = cl.Message(content="", actions=get_core_action_buttons(include_example=False))
        await msg.send()

        model_name = "gemini-2.5-flash"
        response = client.models.generate_content(
            model=model_name,
            contents=[
                {"role": m.get("role", "user"), "parts": [{"text": m.get("content", "")}]}
                for m in history[-10:]
            ] + [{"role": "user", "parts": [{"text": convergence_prompt}]}],
            config=types.GenerateContentConfig(
                system_instruction=bot.get("system_prompt", ""),
                temperature=0.7,
                max_output_tokens=1500,
            )
        )

        if response and response.text:
            msg.content = response.text
            await msg.update()

            # Add to history
            history.append({"role": "user", "content": "[User pressed: Give me your answer]"})
            history.append({"role": "model", "content": response.text})
            cl.user_session.set("history", history)
        else:
            msg.content = "I couldn't generate a convergent answer. Let me try a different approach — what specific question would you like me to answer directly?"
            await msg.update()

    except Exception as e:
        await cl.Message(content=f"Convergence error: {str(e)}").send()


@cl.action_callback("synthesize_conversation")
async def on_synthesize_conversation(action: cl.Action):
    """Synthesize the entire conversation using Larry's voice and style, then export as MD file."""
    from utils.media import create_file_download
    from prompts import LARRY_RAG_SYSTEM_PROMPT
    import datetime

    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["lawrence"])

    if len(history) < 2:
        await cl.Message(content="Not enough conversation to synthesize. Have a discussion first!").send()
        return

    # Build conversation transcript for Larry to synthesize
    # Support both "content" (standard) and "parts" (legacy) history formats
    transcript = ""
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content") or (msg["parts"][0] if isinstance(msg.get("parts"), list) and msg["parts"] else "")
        if not content:
            continue
        if role == "user":
            transcript += f"**User:** {content}\n\n"
        else:
            transcript += f"**Assistant:** {content}\n\n"

    try:
        async with cl.Step(name="Larry Synthesizing Conversation", type="llm") as synth_step:
            synth_step.input = f"Synthesizing {len(history)} messages..."

            # Create synthesis prompt with Larry's voice
            synthesis_prompt = f"""You are Larry - Prof. Lawrence Aronhime's thinking partner persona.

Your task is to synthesize the following conversation into a coherent, insightful summary document.

**CRITICAL: Use YOUR voice - Larry's voice - regardless of which bot the conversation was with.**

Your synthesis should:
1. Start with a brief overview of what was explored
2. Identify the core problem or question being worked on
3. Highlight key insights, reframes, and breakthroughs
4. Note any assumptions that were challenged
5. List concrete next steps or open questions
6. End with Larry's perspective on where to go next

**Your Voice Guidelines:**
- Conversational, not academic
- Provocative, not condescending
- Warm but demanding
- Use micro-tics like trailing thoughts ("And that's where this starts to..."), self-correction, implied judgment

**Format as a clean Markdown document suitable for download.**

---

## CONVERSATION TO SYNTHESIZE:

{transcript}

---

Now synthesize this conversation in Larry's voice. Create a document titled "Conversation Synthesis" with clear sections."""

            # Use Gemini to generate synthesis with Larry's voice
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=synthesis_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=LARRY_RAG_SYSTEM_PROMPT[:2000],  # Use Larry's core personality
                    temperature=0.7,
                    max_output_tokens=4000
                )
            )

            synthesis = response.text
            synth_step.output = f"Generated {len(synthesis)} character synthesis"

        # Create the MD file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"larry_synthesis_{timestamp}.md"

        # Add header metadata to the synthesis
        full_content = f"""# Larry's Conversation Synthesis

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
**Original Bot:** {bot.get('name', 'Unknown')}
**Messages Analyzed:** {len(history)}

---

{synthesis}

---

*Synthesized by Larry - your PWS thinking partner*
"""

        file_element = await create_file_download(
            content=full_content,
            filename=filename
        )

        # Show synthesis inline in chat AND offer download
        # Include core action buttons so user can continue
        await cl.Message(
            content=f"""**📝 Larry's Synthesis Complete!**

---

{synthesis}

---

**Download your synthesis:**""",
            elements=[file_element],
            actions=get_core_action_buttons(include_example=True)
        ).send()

    except Exception as e:
        await cl.Message(content=f"Synthesis error: {str(e)}").send()


@cl.action_callback("start_voice_chat")
async def on_start_voice_chat(action: cl.Action):
    """
    Launch real-time voice chat with Lawrence.
    Uses: Google STT → Gemini → ElevenLabs (your custom voice)
    """
    import os

    # Check if voice server is configured
    voice_server_url = os.getenv("VOICE_SERVER_URL", "ws://localhost:8765")

    # Create the VoiceChat custom element
    voice_chat_element = cl.CustomElement(
        name="VoiceChat",
        props={
            "serverUrl": voice_server_url,
            "showTranscript": True,
        },
        display="inline"
    )

    await cl.Message(
        content="""## 🎙️ Voice Chat with Lawrence

Talk to Lawrence in **real-time** using your voice!

**How it works:**
1. Click **Connect** to start
2. Click **Start Listening** and speak naturally
3. Lawrence responds with your custom ElevenLabs voice
4. Say "goodbye" to end the conversation

**Pipeline:** 🎤 Google STT → 🧠 Gemini → 🔊 Your Custom Voice

---

⚠️ **Make sure the voice server is running:** `python -m voice.realtime_server`
""",
        elements=[voice_chat_element],
    ).send()


# === Journey Memory Callbacks (Conductor-style Persistent Context) ===

@cl.action_callback("journey_status")
async def on_journey_status(action: cl.Action):
    """
    Show user's PWS learning journey: phases, insights, progress.
    Conductor-style persistent memory across sessions.
    """
    try:
        from memory import JourneyStore
        from memory.user_journey import create_journey_context_injection

        user_id = cl.user_session.get("user_id") or cl.user_session.get("id", "anonymous")
        journey_id = cl.user_session.get("journey_id")

        journey_store = JourneyStore(user_id)
        journey = await journey_store.get_journey(journey_id) if journey_id else None

        if not journey:
            # Check if there's any journey for this user
            recent_journey = await journey_store.get_recent_journey()
            if recent_journey:
                journey = recent_journey
                cl.user_session.set("journey_id", journey.id)

        if not journey:
            await cl.Message(
                content="""## 🧭 No Active Journey

You haven't started a PWS journey yet. Begin by:
1. **Describing a problem** you want to explore
2. **Sharing a challenge** from your work or research
3. **Asking a question** about innovation methodology

Once you start, I'll track your progress across sessions!""",
                actions=get_core_action_buttons(include_example=True)
            ).send()
            return

        # Format journey status
        phase_emoji = {"discovery": "🔍", "framing": "🎯", "validation": "✅", "synthesis": "📝", "domain": "🌐", "problem": "🎯", "tta": "📈", "jtbd": "💼", "complete": "✅"}

        # Handle phase as string or enum
        current_phase_str = journey.current_phase.value if hasattr(journey.current_phase, 'value') else str(journey.current_phase)
        current_phase_icon = phase_emoji.get(current_phase_str, "📍")

        # Build insights summary - handle Insight objects
        insights_text = ""
        if journey.insights:
            insight_lines = []
            for i in journey.insights[:5]:
                # Handle both Insight objects and simple strings
                content = i.content if hasattr(i, 'content') else str(i)
                insight_type = f"({i.type.value})" if hasattr(i, 'type') and hasattr(i.type, 'value') else ""
                insight_lines.append(f"- {insight_type} {content[:80]}{'...' if len(content) > 80 else ''}")
            insights_text = "\n".join(insight_lines)
            if len(journey.insights) > 5:
                insights_text += f"\n- *...and {len(journey.insights) - 5} more*"

        # Build checkpoints timeline - handle PhaseCheckpoint objects
        checkpoints_text = ""
        if journey.checkpoints:
            completed_checkpoints = [cp for cp in journey.checkpoints if (cp.status == "completed" if hasattr(cp, 'status') else cp.get("status") == "completed")]
            for cp in completed_checkpoints[-3:]:  # Show last 3 completed
                # Handle both PhaseCheckpoint objects and dicts
                phase = cp.phase if hasattr(cp, 'phase') else cp.get("phase", "")
                summary = cp.output_summary if hasattr(cp, 'output_summary') else cp.get("summary", "Checkpoint saved")
                summary = summary or "Completed"
                cp_icon = phase_emoji.get(phase, "📌")
                checkpoints_text += f"- {cp_icon} **{phase.title() if phase else 'Unknown'}**: {summary[:60]}...\n"

        # Count completed checkpoints
        total_checkpoints = len(journey.checkpoints)
        completed_count = len([cp for cp in journey.checkpoints if (cp.status == "completed" if hasattr(cp, 'status') else cp.get("status") == "completed")])

        status_message = f"""## 🧭 Your PWS Journey

**Problem:** {journey.problem[:100]}{'...' if len(journey.problem) > 100 else ''}

### {current_phase_icon} Current Phase: {current_phase_str.replace('_', ' ').title()}

**Progress:** {completed_count}/{total_checkpoints} checkpoints completed

---

### 💡 Key Insights
{insights_text if insights_text else "*No insights extracted yet. Keep exploring!*"}

### 📍 Recent Checkpoints
{checkpoints_text if checkpoints_text else "*No checkpoints yet. Your progress will be saved automatically.*"}

---

**Journey ID:** `{journey.id[:12]}...`
**Started:** {journey.created_at[:10] if journey.created_at else 'Unknown'}

*Your journey persists across sessions. Pick up right where you left off!*"""

        # Journey action buttons
        journey_actions = [
            cl.Action(
                name="journey_checkpoint",
                payload={"action": "checkpoint"},
                label="💾 Save Checkpoint",
                tooltip="Save your current progress as a checkpoint",
            ),
            cl.Action(
                name="journey_revert",
                payload={"action": "revert"},
                label="⏪ Revert Phase",
                tooltip="Go back to a previous phase",
            ),
            cl.Action(
                name="journey_export",
                payload={"action": "export"},
                label="📤 Export Journey",
                tooltip="Download your journey as markdown",
            ),
        ]

        await cl.Message(
            content=status_message,
            actions=journey_actions + get_core_action_buttons(include_example=False)
        ).send()

    except ImportError as e:
        await cl.Message(
            content=f"Journey memory module not available: {e}\n\nMake sure `memory/` module is installed.",
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"Error loading journey: {str(e)}",
            actions=get_core_action_buttons(include_example=True)
        ).send()


@cl.action_callback("journey_checkpoint")
async def on_journey_checkpoint(action: cl.Action):
    """Manually save a checkpoint of current progress."""
    try:
        from memory import JourneyStore

        user_id = cl.user_session.get("user_id") or cl.user_session.get("id", "anonymous")
        journey_id = cl.user_session.get("journey_id")
        history = cl.user_session.get("history", [])

        if not journey_id:
            await cl.Message(content="No active journey to checkpoint. Start exploring a problem first!").send()
            return

        journey_store = JourneyStore(user_id)
        journey = await journey_store.get_journey(journey_id)

        if not journey:
            await cl.Message(content="Journey not found.").send()
            return

        # Create checkpoint from recent conversation
        from memory.user_journey import PhaseCheckpoint

        recent_messages = history[-6:] if len(history) > 6 else history
        summary = ""
        for msg in recent_messages:
            if msg.get("role") == "user":
                summary += msg.get("content", "")[:100] + " "

        # Get phase as string
        phase_str = journey.current_phase.value if hasattr(journey.current_phase, 'value') else str(journey.current_phase)

        checkpoint = PhaseCheckpoint(
            phase=phase_str,
            step="manual_checkpoint",
            status="completed",
            output_summary=summary[:200] or "Manual checkpoint",
        )

        journey.checkpoints.append(checkpoint)
        await journey_store.save_journey(journey)

        await cl.Message(
            content=f"✅ **Checkpoint Saved**\n\nPhase: {phase_str.replace('_', ' ').title()}\nSummary: {checkpoint.output_summary[:60]}...",
            actions=get_core_action_buttons(include_example=False)
        ).send()

    except Exception as e:
        await cl.Message(content=f"Error saving checkpoint: {str(e)}").send()


@cl.action_callback("journey_revert")
async def on_journey_revert(action: cl.Action):
    """Revert to a previous phase in the journey."""
    try:
        from memory import JourneyStore

        user_id = cl.user_session.get("user_id") or cl.user_session.get("id", "anonymous")
        journey_id = cl.user_session.get("journey_id")

        if not journey_id:
            await cl.Message(content="No active journey to revert.").send()
            return

        journey_store = JourneyStore(user_id)
        journey = await journey_store.get_journey(journey_id)

        if not journey:
            await cl.Message(content="Journey not found.").send()
            return

        # Show phase options
        phases = ["discovery", "domain", "problem", "tta", "jtbd", "validation", "synthesis"]
        phase_icons = {"discovery": "🔍", "domain": "🌐", "problem": "🎯", "tta": "📈", "jtbd": "💼", "validation": "✅", "synthesis": "📝"}

        # Get current phase as string
        current_phase_str = journey.current_phase.value if hasattr(journey.current_phase, 'value') else str(journey.current_phase)
        current_idx = phases.index(current_phase_str) if current_phase_str in phases else 0

        phase_actions = []
        for i, phase in enumerate(phases):
            if i <= current_idx:  # Can only revert to current or earlier phases
                icon = phase_icons.get(phase, "📌")
                phase_actions.append(cl.Action(
                    name="set_journey_phase",
                    payload={"phase": phase},
                    label=f"{icon} {phase.replace('_', ' ').title()}",
                    tooltip=f"Revert to {phase} phase",
                ))

        await cl.Message(
            content=f"""## ⏪ Revert Journey Phase

**Current Phase:** {current_phase_str.replace('_', ' ').title()}

Select a phase to revert to:""",
            actions=phase_actions
        ).send()

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()


@cl.action_callback("set_journey_phase")
async def on_set_journey_phase(action: cl.Action):
    """Set journey to a specific phase."""
    try:
        from memory import JourneyStore

        phase = action.payload.get("phase", "discovery")
        user_id = cl.user_session.get("user_id") or cl.user_session.get("id", "anonymous")
        journey_id = cl.user_session.get("journey_id")

        if not journey_id:
            await cl.Message(content="No active journey.").send()
            return

        journey_store = JourneyStore(user_id)
        journey = await journey_store.get_journey(journey_id)

        if journey:
            # Handle phase as string or enum
            old_phase_str = journey.current_phase.value if hasattr(journey.current_phase, 'value') else str(journey.current_phase)

            # Import JourneyPhase enum for type-safe update
            from memory.user_journey import JourneyPhase, PhaseCheckpoint
            try:
                journey.current_phase = JourneyPhase(phase)
            except ValueError:
                journey.current_phase = phase  # Fallback to string

            # Add checkpoint for the revert (using proper PhaseCheckpoint object)
            revert_checkpoint = PhaseCheckpoint(
                phase=phase,
                step="revert",
                status="completed",
                output_summary=f"Reverted from {old_phase_str} to {phase}",
            )
            journey.checkpoints.append(revert_checkpoint)

            await journey_store.save_journey(journey)

            await cl.Message(
                content=f"✅ **Phase Updated**\n\nReverted from **{old_phase_str.replace('_', ' ').title()}** → **{phase.replace('_', ' ').title()}**\n\nContinue exploring!",
                actions=get_core_action_buttons(include_example=True)
            ).send()

    except Exception as e:
        await cl.Message(content=f"Error setting phase: {str(e)}").send()


@cl.action_callback("journey_export")
async def on_journey_export(action: cl.Action):
    """Export the journey as a downloadable markdown file."""
    try:
        from memory import JourneyStore
        from utils.media import create_file_download
        import datetime

        user_id = cl.user_session.get("user_id") or cl.user_session.get("id", "anonymous")
        journey_id = cl.user_session.get("journey_id")

        if not journey_id:
            await cl.Message(content="No active journey to export.").send()
            return

        journey_store = JourneyStore(user_id)
        journey = await journey_store.get_journey(journey_id)

        if not journey:
            await cl.Message(content="Journey not found.").send()
            return

        # Build markdown export - handle objects properly
        phase_str = journey.current_phase.value if hasattr(journey.current_phase, 'value') else str(journey.current_phase)

        export_md = f"""# PWS Learning Journey Export

**Problem:** {journey.problem}
**Current Phase:** {phase_str.replace('_', ' ').title()}
**Created:** {journey.created_at or 'Unknown'}
**Exported:** {datetime.datetime.now().isoformat()[:19]}

---

## 💡 Key Insights

"""
        for insight in journey.insights:
            # Handle both Insight objects and simple strings
            if hasattr(insight, 'content'):
                insight_type = f"[{insight.type.value}]" if hasattr(insight, 'type') and hasattr(insight.type, 'value') else ""
                export_md += f"- {insight_type} {insight.content}\n"
            else:
                export_md += f"- {insight}\n"

        export_md += "\n---\n\n## 📍 Journey Checkpoints\n\n"
        for i, cp in enumerate(journey.checkpoints):
            # Handle both PhaseCheckpoint objects and dicts
            phase = cp.phase if hasattr(cp, 'phase') else cp.get('phase', 'Unknown')
            summary = cp.output_summary if hasattr(cp, 'output_summary') else cp.get('summary', 'No summary')
            export_md += f"### Checkpoint {i + 1}: {phase.replace('_', ' ').title()}\n"
            export_md += f"{summary or 'Completed'}\n\n"

        export_md += """
---

*Exported from Mindrian PWS Platform*
*Journey memory powered by Conductor-style persistent context*
"""

        # Create downloadable file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pws_journey_{timestamp}.md"
        file_element = await create_file_download(export_md, filename, "text/markdown")

        await cl.Message(
            content="## 📤 Journey Exported\n\nDownload your PWS journey below:",
            elements=[file_element],
            actions=get_core_action_buttons(include_example=False)
        ).send()

    except Exception as e:
        await cl.Message(content=f"Error exporting journey: {str(e)}").send()


@cl.action_callback("extract_insights")
async def on_extract_insights(action: cl.Action):
    """Extract structured insights from the conversation - stored in Supabase."""
    from tools.langextract import (
        instant_extract,
        background_extract_conversation,
        format_instant_extraction,
        format_deep_extraction,
        cache_extraction
    )
    from utils.media import create_file_download
    import datetime

    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["lawrence"])
    session_id = cl.user_session.get("id", "unknown")

    if len(history) < 2:
        await cl.Message(content="Not enough conversation to analyze. Have a discussion first!").send()
        return

    # Build conversation text for extraction
    conversation_text = ""
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")
        conversation_text += f"{role}: {content}\n\n"

    try:
        # Step 1: Instant extraction (NO latency, regex-based)
        async with cl.Step(name="Quick Analysis", type="tool") as quick_step:
            quick_step.input = f"Analyzing {len(history)} messages with pattern matching..."
            instant_results = instant_extract(conversation_text)
            quick_step.output = format_instant_extraction(instant_results)

        # Show instant results immediately
        await cl.Message(
            content=f"**🔍 Quick Analysis Complete**\n\n{format_instant_extraction(instant_results)}\n\n*Running deep analysis...*"
        ).send()

        # Step 2: Deep LLM extraction (background, but user triggered so we show progress)
        async with cl.Step(name="Deep Extraction", type="llm") as deep_step:
            deep_step.input = "Extracting structured PWS elements: problems, assumptions, facts, questions..."

            deep_results = await background_extract_conversation(history, bot.get("name", "lawrence"))

            if deep_results.get("error"):
                deep_step.output = f"Error: {deep_results['error']}"
            else:
                deep_step.output = f"Extracted {len(deep_results.get('key_facts', []))} facts, {len(deep_results.get('stated_assumptions', []))} assumptions"

        # Cache the extraction in Supabase
        cache_key = cache_extraction(
            conversation_text,
            {**instant_results, "deep": deep_results},
            extract_type="conversation",
            session_id=session_id
        )

        # Format the deep extraction
        deep_formatted = format_deep_extraction(deep_results)

        # Create downloadable JSON export
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        export_data = {
            "extracted_at": datetime.datetime.now().isoformat(),
            "bot": bot.get("name", "Unknown"),
            "message_count": len(history),
            "cache_key": cache_key,
            "instant_analysis": instant_results,
            "deep_analysis": deep_results
        }

        # Create both MD and JSON downloads
        md_content = f"""# Conversation Extraction

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
**Bot:** {bot.get('name', 'Unknown')}
**Messages:** {len(history)}
**Cache Key:** `{cache_key}` *(stored in Supabase)*

---

{format_instant_extraction(instant_results)}

---

{deep_formatted}

---

*Extracted by LangExtract - Zero-latency structured data extraction*
"""

        md_file = await create_file_download(
            content=md_content,
            filename=f"extraction_{timestamp}.md"
        )

        import json
        json_file = await create_file_download(
            content=json.dumps(export_data, indent=2, default=str),
            filename=f"extraction_{timestamp}.json"
        )

        await cl.Message(
            content=f"""**🔍 Deep Extraction Complete!**

{deep_formatted}

---

**Stored in Supabase** with key: `{cache_key}`

Download your extraction:""",
            elements=[md_file, json_file]
        ).send()

    except Exception as e:
        await cl.Message(content=f"Extraction error: {str(e)}").send()


@cl.action_callback("speak_response")
async def on_speak_response(action: cl.Action):
    """Convert last response to speech using ElevenLabs."""
    from utils.media import text_to_speech

    history = cl.user_session.get("history", [])

    # Get last assistant response
    last_response = None
    for msg in reversed(history):
        if msg.get("role") == "model":
            last_response = msg.get("content", "")[:2000]  # Limit for voice
            break

    if not last_response:
        await cl.Message(content="No response to speak.").send()
        return

    async with cl.Step(name="Generating Voice", type="tool") as voice_step:
        voice_step.input = f"Converting {len(last_response)} characters to speech..."

        audio_element = await text_to_speech(last_response)

        if audio_element:
            voice_step.output = "Voice generated successfully"
            await cl.Message(
                content="**Larry's voice response:**",
                elements=[audio_element]
            ).send()
        else:
            voice_step.output = "ElevenLabs API key not configured"
            await cl.Message(
                content="Voice not available. Set ELEVENLABS_API_KEY in environment."
            ).send()


@cl.action_callback("map_ideas")
async def on_map_ideas(action: cl.Action):
    """Generate the most appropriate diagram type based on conversation content."""
    from utils.diagrams import (
        create_mindmap, create_mermaid_element, create_flowchart,
        create_quadrant_chart, create_user_journey
    )
    import json
    import re

    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["lawrence"])

    if len(history) < 2:
        await cl.Message(content="Not enough conversation to visualize. Have a discussion first!").send()
        return

    # Build conversation summary for AI to analyze
    conversation_text = ""
    for msg in history[-10:]:  # Last 10 messages for context
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")[:500]  # Truncate
        conversation_text += f"{role}: {content}\n\n"

    try:
        async with cl.Step(name="Analyzing Best Visualization", type="llm") as map_step:
            map_step.input = f"Analyzing {len(history)} messages to determine best diagram type..."

            # Step 1: Ask Gemini to recommend the best diagram type
            classify_prompt = f"""Analyze this conversation and recommend the BEST Mermaid diagram type.

Conversation:
{conversation_text}

DIAGRAM TYPES (choose the MOST appropriate one):

1. "mindmap" - Best for:
   - Brainstorming sessions
   - Exploring ideas/concepts
   - Showing relationships between themes
   - When user is discovering or exploring

2. "flowchart" - Best for:
   - Processes with steps
   - Decision trees (if/then logic)
   - Workflows or procedures
   - When user discusses "how to" or sequences

3. "quadrant" - Best for:
   - Prioritization (urgent/important)
   - Risk assessment (impact/likelihood)
   - Comparing options on 2 dimensions
   - When user is evaluating/ranking

4. "journey" - Best for:
   - Customer/user experiences
   - Emotional journeys
   - Timeline of experiences
   - When discussing user pain points

5. "sequence" - Best for:
   - Interactions between parties
   - API/system communications
   - Meeting/conversation flows
   - When multiple actors are involved

Return ONLY a JSON object (no markdown):
{{
  "diagram_type": "mindmap|flowchart|quadrant|journey|sequence",
  "reason": "Brief explanation why this type fits best",
  "title": "2-4 word title for the diagram"
}}"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=classify_prompt,
                config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=300)
            )
            classify_text = response.text.strip()

            # Extract JSON from response
            if "```" in classify_text:
                parts = classify_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        classify_text = part
                        break

            try:
                classification = json.loads(classify_text)
                diagram_type = classification.get("diagram_type", "mindmap")
                title = classification.get("title", "Visualization")
                reason = classification.get("reason", "")
            except json.JSONDecodeError:
                diagram_type = "mindmap"
                title = "Idea Map"
                reason = "Default fallback"

            map_step.output = f"Selected: {diagram_type} - {reason}"

        # Step 2: Generate the appropriate diagram based on type
        async with cl.Step(name=f"Creating {diagram_type.title()}", type="llm") as gen_step:

            if diagram_type == "flowchart":
                # Generate flowchart structure
                flow_prompt = f"""Create a flowchart structure from this conversation.

Conversation:
{conversation_text}

Return ONLY valid JSON (no markdown):
{{
  "steps": [
    {{"id": "A", "label": "Start/Trigger", "type": "start", "next": ["B"]}},
    {{"id": "B", "label": "First step", "type": "process", "next": ["C"]}},
    {{"id": "C", "label": "Decision?", "type": "decision", "next": ["D", "E"]}},
    {{"id": "D", "label": "Yes path", "type": "process", "next": ["F"]}},
    {{"id": "E", "label": "No path", "type": "process", "next": ["F"]}},
    {{"id": "F", "label": "End", "type": "end", "next": []}}
  ]
}}

Types: "start", "end", "process", "decision"
Keep labels to 2-5 words. Create 4-8 steps."""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=flow_prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=1000)
                )
                flow_data = _extract_json(response.text)
                steps = flow_data.get("steps", [])
                diagram = await create_flowchart(steps, title=title)
                gen_step.output = f"Created flowchart with {len(steps)} steps"

            elif diagram_type == "quadrant":
                # Generate quadrant chart structure
                quad_prompt = f"""Create a 2x2 quadrant chart from this conversation.

Conversation:
{conversation_text}

Return ONLY valid JSON (no markdown):
{{
  "x_label": "X-axis label (e.g., 'Urgency', 'Effort')",
  "y_label": "Y-axis label (e.g., 'Impact', 'Value')",
  "items": [
    {{"name": "Item 1", "x": 75, "y": 85}},
    {{"name": "Item 2", "x": 25, "y": 60}},
    {{"name": "Item 3", "x": 80, "y": 30}},
    {{"name": "Item 4", "x": 20, "y": 20}}
  ]
}}

x and y are 0-100. Create 3-6 items from the conversation."""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=quad_prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=800)
                )
                quad_data = _extract_json(response.text)
                diagram = await create_quadrant_chart(
                    title=title,
                    x_label=quad_data.get("x_label", "X-Axis"),
                    y_label=quad_data.get("y_label", "Y-Axis"),
                    items=quad_data.get("items", [])
                )
                gen_step.output = f"Created quadrant with {len(quad_data.get('items', []))} items"

            elif diagram_type == "journey":
                # Generate user journey
                journey_prompt = f"""Create a user journey map from this conversation.

Conversation:
{conversation_text}

Return ONLY valid JSON (no markdown):
{{
  "title": "Journey title",
  "sections": [
    {{
      "name": "Discovery",
      "tasks": [
        {{"name": "Realizes problem", "score": 3}},
        {{"name": "Searches for solution", "score": 4}}
      ]
    }},
    {{
      "name": "Evaluation",
      "tasks": [
        {{"name": "Compares options", "score": 2}},
        {{"name": "Gets confused", "score": 1}}
      ]
    }}
  ]
}}

Score is emotion: 1=frustrated, 3=neutral, 5=happy. Create 3-4 sections with 2-3 tasks each."""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=journey_prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=1000)
                )
                journey_data = _extract_json(response.text)
                diagram = await create_user_journey(
                    title=journey_data.get("title", title),
                    sections=journey_data.get("sections", [])
                )
                gen_step.output = f"Created journey with {len(journey_data.get('sections', []))} sections"

            elif diagram_type == "sequence":
                # Generate sequence diagram
                seq_prompt = f"""Create a sequence diagram from this conversation.

Conversation:
{conversation_text}

Return ONLY valid Mermaid sequence diagram syntax (no JSON, no markdown code blocks):

sequenceDiagram
    participant User
    participant System
    User->>System: Request something
    System-->>User: Response
    Note over User,System: Important note

Create 4-8 interactions. Use ->> for requests, -->> for responses."""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=seq_prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=800)
                )
                mermaid_code = response.text.strip()
                if "```" in mermaid_code:
                    mermaid_code = mermaid_code.split("```")[1].replace("mermaid", "").strip()
                if not mermaid_code.startswith("sequenceDiagram"):
                    mermaid_code = "sequenceDiagram\n" + mermaid_code
                diagram = await create_mermaid_element(mermaid_code, title=title)
                gen_step.output = "Created sequence diagram"

            else:  # Default: mindmap
                # Generate mindmap (original logic)
                mind_prompt = f"""Create a mindmap structure from this conversation.

Conversation:
{conversation_text}

Return ONLY valid JSON (no markdown):
{{
  "central_topic": "Main topic (2-4 words)",
  "branches": {{
    "Key Ideas": ["idea 1", "idea 2", "idea 3"],
    "Questions": ["question 1", "question 2"],
    "Insights": ["insight 1", "insight 2"],
    "Next Steps": ["action 1", "action 2"]
  }}
}}

Create 3-5 branches with 2-4 items each. Keep items to 2-5 words."""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=mind_prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=1000)
                )
                mindmap_data = _extract_json(response.text)
                diagram = await create_mindmap(
                    central_topic=mindmap_data.get("central_topic", "Discussion"),
                    branches=mindmap_data.get("branches", {}),
                    title=title
                )
                gen_step.output = f"Created mindmap: {mindmap_data.get('central_topic', 'Unknown')}"

        # Send the diagram
        type_icons = {
            "mindmap": "🗺️", "flowchart": "📊", "quadrant": "📐",
            "journey": "🚶", "sequence": "🔄"
        }
        icon = type_icons.get(diagram_type, "📈")

        await cl.Message(
            content=f"**{icon} {title}** ({diagram_type})\n\n*{reason}*",
            elements=[diagram]
        ).send()

    except Exception as e:
        await cl.Message(content=f"Visualization error: {str(e)[:200]}").send()


def _extract_json(text: str) -> dict:
    """Extract JSON from Gemini response, handling markdown and extra text."""
    import json
    import re

    text = text.strip()

    # Remove markdown code blocks
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break

    # Find JSON object if wrapped in other text
    if not text.startswith("{"):
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            text = json_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


async def _research_sources_first(recent_context: str, bot_name: str, search_depth: str, history: list):
    """
    Deep research pipeline: Claude plans, Tavily searches, Gemini synthesizes.

    Uses the LangGraph-based research pipeline with:
    1. Claude Sonnet for query planning (preserves user's exact terms)
    2. Tavily parallel search execution
    3. Python-based source evaluation (authority scoring)
    4. Claude Sonnet for reflection/gap analysis (depth-dependent)
    5. Gemini Flash for synthesis with PWS methodology framing
    """
    try:
        from intelligence.pipelines.research_pipeline import run_deep_research
    except Exception as import_err:
        print(f"[RESEARCH] Import error: {import_err}")
        import traceback
        traceback.print_exc()
        await cl.Message(
            content=f"⚠️ Research pipeline unavailable: {str(import_err)[:150]}\n\nPlease try again or refresh the page.",
            actions=get_core_action_buttons(include_example=True),
        ).send()
        return

    msg = cl.Message(content="")
    await msg.send()

    # Get bot context
    bot = cl.user_session.get("bot", BOTS["lawrence"])
    chat_profile = cl.user_session.get("chat_profile", "lawrence")

    # Map settings to pipeline depth — deep is available everywhere
    # basic setting → basic pipeline (fast, no reflection)
    # advanced setting → standard pipeline (1 reflection round)
    # deep setting (playground OR Lawrence) → deep pipeline (up to 3 reflections)
    if search_depth == "deep":
        research_depth = "deep"
    elif search_depth == "advanced":
        research_depth = "standard"
    else:
        research_depth = "basic"

    # Extract the main question from context
    # Prioritize the USER's topic, not the bot's question back to them
    last_user_topic = ""
    for hist_item in reversed(history):
        if hist_item.get("role") == "user":
            content = hist_item.get("content", "").strip()
            # Skip trivial messages
            if len(content) > 5 and content.lower() not in ["go", "yes", "ok", "next", "continue",
                                                              "sure", "yeah", "no", "nah", "thanks"]:
                last_user_topic = content[:1000]
                break

    if not last_user_topic or len(last_user_topic) < 5:
        # Try extracting from recent_context
        last_user_topic = recent_context.split("user:")[-1][:300].strip() if "user:" in recent_context else recent_context[:300]

    if not last_user_topic or len(last_user_topic) < 5:
        await msg.stream_token("Could not determine what to research. Try asking a more specific question.")
        await msg.update()
        return

    # Show research progress
    depth_labels = {"basic": "Basic", "standard": "Standard", "deep": "Deep (Iterative)"}
    await msg.stream_token(f"## 🔬 Deep Research Pipeline\n\n")
    await msg.stream_token(f"**Question:** {last_user_topic[:200]}\n\n")
    await msg.stream_token(f"**Depth:** {depth_labels.get(research_depth, research_depth.title())}\n")
    await msg.stream_token(f"**Strategy:** Claude plans → Tavily searches → Gemini synthesizes\n\n")
    await msg.stream_token("---\n\n")

    # Phase indicators based on depth
    if research_depth == "basic":
        phases = ["🎯 Claude planning queries", "🔍 Tavily searching", "📊 Evaluating sources", "✨ Gemini synthesizing"]
    else:
        phases = ["🎯 Claude planning queries", "🔍 Tavily searching", "📊 Evaluating sources",
                  "🔎 Claude reflecting on gaps", "✨ Gemini synthesizing"]

    try:
        async with cl.Step(name="🔬 Deep Research Pipeline", type="run") as research_step:
            research_step.input = f"Researching: {last_user_topic[:200]}"

            # Show phase progress
            for phase in phases:
                await msg.stream_token(f"- {phase}...\n")

            await msg.stream_token("\n")

            # Execute the LangGraph pipeline
            result = await run_deep_research(
                query=last_user_topic,
                conversation_history=history,
                bot_id=chat_profile,
                depth=research_depth,
            )

            # Check for pipeline errors before displaying results
            if result.get("error"):
                error_msg = result["error"]
                print(f"[RESEARCH] Pipeline returned error: {error_msg}")
                await msg.stream_token(f"\n⚠️ Research encountered an issue: {str(error_msg)[:200]}\n\n")
                await msg.stream_token("Falling back to simple search...\n\n")
                # Fallback to simple Tavily search
                from tools.tavily_search import search_web
                try:
                    fallback = search_web(last_user_topic, search_depth=search_depth, max_results=8)
                    for i, src in enumerate(fallback.get("results", [])[:5], 1):
                        await msg.stream_token(f"**{i}. [{src.get('title', 'Untitled')}]({src.get('url', '')})**\n")
                        await msg.stream_token(f"   {src.get('content', '')[:200]}...\n\n")
                except Exception as fb_err:
                    await msg.stream_token(f"Fallback search also failed: {fb_err}\n")
                research_step.output = f"Error: {str(error_msg)[:100]}"
            else:
                research_step.output = (
                    f"Found {len(result.get('findings', []))} findings from "
                    f"{len(result.get('sources', []))} sources in "
                    f"{result.get('iterations', 1)} round(s)"
                )

                # Display synthesis (the main output from Gemini) — only on success
                await msg.stream_token("\n---\n\n")

                synthesis = result.get("synthesis", "")
                if synthesis:
                    await msg.stream_token(synthesis)
                    await msg.stream_token("\n\n")

                # Show evidence gaps if any remain
                evidence_gaps = result.get("evidence_gaps", [])
                if evidence_gaps:
                    await msg.stream_token("### ❓ Remaining Questions\n\n")
                    for gap in evidence_gaps[:3]:
                        await msg.stream_token(f"- {gap}\n")
                    await msg.stream_token("\n")

                # Cost summary in collapsed step
                cost = result.get("cost_summary", {})
                if cost and cost.get("total", 0) > 0:
                    async with cl.Step(name="💰 Cost Summary", type="tool") as cost_step:
                        cost_step.output = (
                            f"Claude: ${cost.get('claude', 0):.4f} | "
                            f"Tavily: ${cost.get('tavily', 0):.4f} | "
                            f"Gemini: ${cost.get('gemini', 0):.4f} | "
                            f"**Total: ${cost.get('total', 0):.4f}** | "
                            f"Iterations: {result.get('iterations', 1)}"
                        )

    except Exception as e:
        print(f"[RESEARCH] Pipeline error: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to simple search
        await msg.stream_token(f"\n⚠️ Research pipeline failed, using simple search...\n\n")
        from tools.tavily_search import search_web

        try:
            results = search_web(last_user_topic, search_depth=search_depth, max_results=8)
            sources = results.get("results", [])

            if sources:
                await msg.stream_token(f"**Found {len(sources)} sources:**\n\n")
                for i, src in enumerate(sources, 1):
                    title = src.get("title", "Untitled")
                    url = src.get("url", "")
                    content = src.get("content", "")[:200]
                    await msg.stream_token(f"**{i}. [{title}]({url})**\n")
                    if content:
                        await msg.stream_token(f"   {content}...\n\n")
        except Exception as e2:
            await msg.stream_token(f"Search failed: {e2}")

    # Add action buttons
    msg.actions = get_core_action_buttons(include_example=True)
    msg.actions.insert(0, cl.Action(
        name="deep_research_full",
        payload={"action": "deep_research_full"},
        label="🔬 Deep Analyze (Minto Pyramid)",
        tooltip="Run full structured analysis with SCQA, Beautiful Questions, and Sequential Thinking",
    ))
    await msg.update()

    # Inject into history
    history.append({"role": "model", "content": f"[Research completed for: {last_user_topic[:200]}]"})
    cl.user_session.set("history", history)


@cl.action_callback("deep_research_full")
async def on_deep_research_full(action: cl.Action):
    """Run full Minto Pyramid analysis (triggered from Sources-First view)."""
    # Delegate to the full pipeline by temporarily disabling simple_mode
    bot = cl.user_session.get("bot", BOTS["lawrence"])
    original_simple = bot.get("simple_mode", False)
    bot["simple_mode"] = False
    cl.user_session.set("bot", bot)
    try:
        await on_deep_research(action)
    finally:
        bot["simple_mode"] = original_simple
        cl.user_session.set("bot", bot)


@cl.action_callback("deep_research")
async def on_deep_research(action: cl.Action):
    """
    Handle research button — Sources-First approach.

    For simple_mode (Lawrence): Show sources with links, offer deep analysis as optional.
    For playground: Full Minto Pyramid pipeline.

    CRITICAL: This callback must NEVER crash and destroy the session.
    All errors are caught and displayed gracefully with action buttons preserved.
    """
    try:
        import uuid
        from tools.tavily_search import search_web

        # Get context
        history = cl.user_session.get("history", [])
        bot = cl.user_session.get("bot", BOTS["lawrence"])
        bot_name = bot.get("name", "Larry")
        chat_profile = cl.user_session.get("chat_profile", "lawrence")
        settings = cl.user_session.get("settings", {})
        search_depth = settings.get("research_depth", "basic")
        is_simple = bot.get("simple_mode", False)

        # Build context from recent conversation - use more context for accuracy
        recent_context = ""
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:800]
            recent_context += f"{role}: {content}\n"

        # ─── Sources-First Mode (ALL bots) ───
        # Always show sources first. Users can click "Deep Analyze" for Minto Pyramid.
        # This fixes the UX mismatch where users expect sources but get Minto analysis.
        await _research_sources_first(recent_context, bot_name, search_depth, history)
        return

    except Exception as e:
        # CRITICAL: Never let research errors destroy the session
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[RESEARCH] Critical callback error: {e}")
        print(f"[RESEARCH] Full traceback:\n{error_traceback}")

        # Map technical errors to user-friendly messages
        error_msg = str(e).lower()
        if "timeout" in error_msg or "timed out" in error_msg:
            user_message = "The search service took too long to respond. This usually resolves itself."
        elif "api" in error_msg or "key" in error_msg or "401" in error_msg or "403" in error_msg:
            user_message = "There's a temporary issue with the research service. Please try again in a moment."
        elif "connection" in error_msg or "network" in error_msg:
            user_message = "Network connection issue. Please check your connection and try again."
        elif "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
            user_message = "The research service is busy. Please wait a moment and try again."
        elif "none" in error_msg and "attribute" in error_msg:
            user_message = "Received an unexpected response from the search service. Please try again."
        elif "tavily" in error_msg or "search" in error_msg:
            user_message = "Web search service is temporarily unavailable. Please try again."
        else:
            # Log the actual error for debugging
            user_message = f"Research encountered an issue: {str(e)[:100]}"

        # Send graceful error message with action buttons preserved
        try:
            await cl.Message(
                content=f"""## ⚠️ Research Temporarily Unavailable

{user_message}

**Your conversation is preserved.** You can:
- Try the Research button again
- Continue our conversation
- Use other tools

*If this persists, try refreshing the page.*""",
                actions=get_core_action_buttons(include_example=True)
            ).send()
        except Exception:
            # Last resort: even message send failed, just log
            print(f"[RESEARCH] Failed to send error message: {e}")

    # ─── Full Minto Pyramid Mode (only via "Deep Analyze" button) ───
    from utils.minto_research import (
        SequentialThinkingSession, SCQAAnalysis, ResearchPlan, ThoughtType,
        BeautifulQuestions, SCQA_ANALYSIS_PROMPT, BEAUTIFUL_QUESTIONS_PROMPT,
        SEQUENTIAL_THINKING_PROMPT, RESEARCH_PLAN_PROMPT, PYRAMID_SYNTHESIS_PROMPT,
        parse_scqa_response, parse_beautiful_questions_response, parse_thoughts_response,
        parse_research_plan_response, format_thoughts_for_prompt
    )

    # Initialize session
    session = SequentialThinkingSession(session_id=str(uuid.uuid4())[:8])

    try:
        # Parent step for the entire research process
        async with cl.Step(name="🔬 PWS Methodology Research", type="run") as research_step:
            research_step.input = f"Analyzing conversation for {bot_name}..."

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 0: PWS METHODOLOGY DISCOVERY (Framework-Driven Planning)
            # ═══════════════════════════════════════════════════════════════════
            from tools.neo4j_framework_discovery import (
                extract_challenge_keywords, get_default_pws_frameworks,
                build_orchestration_plan, generate_full_orchestration_prompts
            )

            framework_plan = None
            async with cl.Step(name="🧭 PWS Methodology Discovery", type="tool") as discovery_step:
                discovery_step.input = "Discovering relevant PWS frameworks and methodologies..."

                # Extract keywords from conversation
                keywords = extract_challenge_keywords(recent_context)

                # Get relevant frameworks (uses Neo4j internally, fallback to defaults)
                try:
                    # Try to query Neo4j for frameworks
                    from tools.pws_brain import query_neo4j_for_frameworks
                    frameworks = await query_neo4j_for_frameworks(keywords, limit=8)
                except Exception:
                    # Fallback to default PWS frameworks
                    frameworks = get_default_pws_frameworks(recent_context, limit=8)

                if frameworks:
                    # Build orchestration plan
                    framework_plan = build_orchestration_plan(recent_context, frameworks)

                    discovery_output = f"""**PWS Frameworks Identified:** {len(frameworks)}

**Phase 1 (Parallel):**
{chr(10).join([f'- {fw.name} ({fw.category})' for fw in framework_plan.phase_1_parallel])}

**Phase 2 (Sequential):**
{chr(10).join([f'- {fw.name} ({fw.category})' for fw in framework_plan.phase_2_sequential])}

**Phase 3 (Synthesis):**
{chr(10).join([f'- {fw.name} ({fw.category})' for fw in framework_plan.phase_3_synthesis])}

**Research Queries Planned:** {sum(len(fw.suggested_queries) for fw in frameworks)}"""
                    discovery_step.output = discovery_output
                else:
                    discovery_step.output = "Using default PWS methodology approach..."

            # Store framework context for later phases
            framework_context = ""
            if framework_plan:
                framework_context = f"\n\nRelevant PWS Frameworks to consider:\n"
                for fw in framework_plan.phase_1_parallel + framework_plan.phase_2_sequential:
                    framework_context += f"- {fw.name}: {fw.mini_agent_role}\n"

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 1: SCQA ANALYSIS (Minto Pyramid Framework)
            # ═══════════════════════════════════════════════════════════════════
            async with cl.Step(name="📐 SCQA Analysis (Minto Pyramid)", type="llm") as scqa_step:
                scqa_step.input = "Identifying Situation → Complication → Question → Answer hypothesis..."

                scqa_prompt = SCQA_ANALYSIS_PROMPT.format(
                    context=recent_context,
                    bot_name=bot_name
                )

                scqa_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=scqa_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=800
                    )
                )

                session.scqa = parse_scqa_response(scqa_response.text)

                if session.scqa:
                    scqa_output = f"""**SITUATION:** {session.scqa.situation[:200]}...

**COMPLICATION:** {session.scqa.complication[:200]}...

**QUESTION:** {session.scqa.question}

**HYPOTHESIS** (confidence: {session.scqa.confidence:.0%}): {session.scqa.answer_hypothesis[:200]}..."""
                    scqa_step.output = scqa_output
                else:
                    scqa_step.output = "SCQA extraction failed, using fallback..."
                    session.scqa = SCQAAnalysis(
                        situation="User exploring topic with " + bot_name,
                        complication="Need more evidence/validation",
                        question="What research would validate or challenge our thinking?",
                        answer_hypothesis="Research will reveal supporting and contradicting evidence",
                        confidence=0.5
                    )

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 2: BEAUTIFUL QUESTIONS (Why / What If / How)
            # ═══════════════════════════════════════════════════════════════════
            async with cl.Step(name="❓ Beautiful Questions (Berger)", type="llm") as questions_step:
                questions_step.input = "Generating Why → What If → How questions..."

                questions_prompt = BEAUTIFUL_QUESTIONS_PROMPT.format(
                    scqa=session.scqa.to_prompt(),
                    context=recent_context[:800]
                )

                questions_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=questions_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.5,
                        max_output_tokens=800
                    )
                )

                session.beautiful_questions = parse_beautiful_questions_response(questions_response.text)

                if session.beautiful_questions:
                    q_output = f"""**🔴 WHY Questions:**
{chr(10).join('- ' + q for q in session.beautiful_questions.why_questions[:3])}

**🟡 WHAT IF Questions:**
{chr(10).join('- ' + q for q in session.beautiful_questions.what_if_questions[:3])}

**🟢 HOW Questions:**
{chr(10).join('- ' + q for q in session.beautiful_questions.how_questions[:3])}"""
                    questions_step.output = q_output
                else:
                    questions_step.output = "Question generation failed, using defaults..."
                    session.beautiful_questions = BeautifulQuestions(
                        why_questions=["Why does this problem exist?", "Why hasn't it been solved?"],
                        what_if_questions=["What if we approached this differently?", "What if our assumptions are wrong?"],
                        how_questions=["How might we validate this?", "How could we test our hypothesis?"]
                    )

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 3: SEQUENTIAL THINKING (with revision & branching)
            # ═══════════════════════════════════════════════════════════════════
            async with cl.Step(name="💭 Sequential Thinking", type="llm") as thinking_step:
                thinking_step.input = "Breaking down research need with revision/branching..."

                thinking_prompt = SEQUENTIAL_THINKING_PROMPT.format(
                    scqa=session.scqa.to_prompt(),
                    beautiful_questions=session.beautiful_questions.to_prompt() if session.beautiful_questions else "",
                    num_thoughts=5
                )

                thinking_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=thinking_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=1200
                    )
                )

                thoughts = parse_thoughts_response(thinking_response.text, session)

                # Format thoughts for display
                thoughts_display = []
                for t in session.thoughts:
                    prefix = t.prefix
                    note = ""
                    if t.thought_type == ThoughtType.REVISION:
                        note = f" *(revises #{t.revises_thought})*"
                    elif t.thought_type == ThoughtType.BRANCH:
                        note = f" *(🌿 {t.branch_id})*"
                    thoughts_display.append(f"{prefix} **Thought {t.number}**{note}: {t.content[:150]}...")

                thinking_step.output = "\n\n".join(thoughts_display)

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 4: RESEARCH MATRIX PLANNING (Pre-Consolidation)
            # ═══════════════════════════════════════════════════════════════════
            from utils.minto_research import (
                RESEARCH_MATRIX_PROMPT, CONSOLIDATION_PROMPT, FINAL_SYNTHESIS_PROMPT,
                parse_research_matrix_response, consolidate_results_by_group,
                format_consolidated_for_synthesis, ResearchMatrix
            )
            from tools.tavily_search import research_matrix_execution, get_search_context

            # Include framework-specific queries from discovery phase
            framework_queries_context = ""
            if framework_plan:
                framework_queries_context = "\n\nPWS FRAMEWORK-SPECIFIC QUERIES TO INCLUDE:\n"
                for fw in framework_plan.phase_1_parallel + framework_plan.phase_2_sequential:
                    for q in fw.suggested_queries:
                        framework_queries_context += f"- [{fw.category}] {q}\n"

            async with cl.Step(name="📋 Research Matrix Planning", type="llm") as matrix_step:
                matrix_step.input = "Generating comprehensive research matrix (12-20 queries across categories)..."

                matrix_prompt = RESEARCH_MATRIX_PROMPT.format(
                    scqa=session.scqa.to_prompt(),
                    beautiful_questions=session.beautiful_questions.to_prompt() if session.beautiful_questions else "",
                    thoughts=format_thoughts_for_prompt(session.thoughts) + framework_queries_context
                )

                matrix_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=matrix_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=2000
                    )
                )

                session.research_matrix = parse_research_matrix_response(matrix_response.text)

                if session.research_matrix:
                    total_queries = session.research_matrix.total_queries()
                    groups = list(session.research_matrix.consolidation_groups.keys())
                    matrix_output = f"""**Research Matrix Generated:**
- 🔴 WHY queries: {len(session.research_matrix.why_queries)}
- 🟡 WHAT IF queries: {len(session.research_matrix.what_if_queries)}
- 🟢 HOW queries: {len(session.research_matrix.how_queries)}
- 📊 Validation queries: {len(session.research_matrix.validation_queries)}
- ⚠️ Challenge queries: {len(session.research_matrix.challenge_queries)}

**Total: {total_queries} queries** → **{len(groups)} consolidation groups**

**Groups:** {', '.join(groups[:5])}{"..." if len(groups) > 5 else ""}"""
                    matrix_step.output = matrix_output
                else:
                    # Fallback to simple matrix with ACTUAL queries from previous phases
                    print(f"[RESEARCH] Matrix parse failed, building fallback from questions")
                    from utils.minto_research import ResearchQuery

                    # Build queries from Beautiful Questions
                    bq = session.beautiful_questions
                    why_qs = []
                    what_if_qs = []
                    how_qs = []

                    if bq:
                        for q in bq.why_questions[:2]:
                            # Convert question to search query keywords
                            keywords = q.replace("?", "").replace("Why ", "").replace("why ", "")
                            why_qs.append(ResearchQuery(
                                query=f"{keywords} research data 2024 2025",
                                category="why",
                                source_question=q,
                                consolidation_group="general",
                                priority=1
                            ))
                        for q in bq.what_if_questions[:2]:
                            keywords = q.replace("?", "").replace("What if ", "").replace("what if ", "")
                            what_if_qs.append(ResearchQuery(
                                query=f"{keywords} alternatives possibilities",
                                category="what_if",
                                source_question=q,
                                consolidation_group="general",
                                priority=1
                            ))
                        for q in bq.how_questions[:2]:
                            keywords = q.replace("?", "").replace("How ", "").replace("how ", "")
                            how_qs.append(ResearchQuery(
                                query=f"{keywords} implementation examples",
                                category="how",
                                source_question=q,
                                consolidation_group="general",
                                priority=1
                            ))

                    # Add one validation query from SCQA hypothesis
                    val_qs = []
                    if session.scqa and session.scqa.answer_hypothesis:
                        val_qs.append(ResearchQuery(
                            query=f"{session.scqa.question[:50]} evidence validation",
                            category="validation",
                            source_question=session.scqa.question,
                            consolidation_group="general",
                            priority=1
                        ))

                    session.research_matrix = ResearchMatrix(
                        why_queries=why_qs,
                        what_if_queries=what_if_qs,
                        how_queries=how_qs,
                        validation_queries=val_qs,
                        challenge_queries=[],
                        consolidation_groups={"general": "General research results"}
                    )
                    total_fallback = len(why_qs) + len(what_if_qs) + len(how_qs) + len(val_qs)
                    matrix_step.output = f"Using fallback research matrix... ({total_fallback} queries from Beautiful Questions)"

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 5: EXECUTE MATRIX RESEARCH (12-20 queries)
            # ═══════════════════════════════════════════════════════════════════
            all_results = {"why": [], "what_if": [], "how": [], "validation": [], "challenge": []}
            total_sources = 0

            async with cl.Step(name="🔍 Executing Research Matrix", type="tool") as search_parent:
                matrix = session.research_matrix
                total_queries = matrix.total_queries() if matrix else 0
                search_parent.input = f"Executing {total_queries} queries across 5 categories with RAG-optimized context..."

                async def execute_category_searches(queries, category: str, label: str, emoji: str):
                    """Execute searches for a query category."""
                    nonlocal total_sources
                    results = []

                    if not queries:
                        return results

                    async with cl.Step(name=f"{emoji} {label} ({len(queries)} queries)", type="tool") as cat_step:
                        cat_step.input = f"Searching: {', '.join([q.query[:30] + '...' for q in queries[:3]])}"

                        for q in queries[:4]:  # Max 4 queries per category
                            try:
                                # Use get_search_context for RAG-optimized results
                                context = get_search_context(q.query, max_results=4, max_tokens=2000)
                                result = search_web(q.query, search_depth=search_depth, max_results=4)

                                results.append({
                                    "query": q.query,
                                    "source_question": q.source_question,
                                    "consolidation_group": q.consolidation_group,
                                    "context": context,
                                    "results": result.get("results", []),
                                    "answer": result.get("answer", "")
                                })
                                total_sources += len(result.get("results", []))
                            except Exception as e:
                                results.append({
                                    "query": q.query,
                                    "error": str(e),
                                    "results": []
                                })

                        cat_step.output = f"Found {sum(len(r.get('results', [])) for r in results)} sources"

                    return results

                # Execute all categories
                if matrix:
                    all_results["why"] = await execute_category_searches(
                        matrix.why_queries, "why", "WHY Questions", "🔴"
                    )
                    all_results["what_if"] = await execute_category_searches(
                        matrix.what_if_queries, "what_if", "WHAT IF Questions", "🟡"
                    )
                    all_results["how"] = await execute_category_searches(
                        matrix.how_queries, "how", "HOW Questions", "🟢"
                    )
                    all_results["validation"] = await execute_category_searches(
                        matrix.validation_queries, "validation", "Validation (Camera Test)", "📊"
                    )
                    all_results["challenge"] = await execute_category_searches(
                        matrix.challenge_queries, "challenge", "Challenge (Devil's Advocate)", "⚠️"
                    )

                queries_executed = sum(len(v) for v in all_results.values())
                search_parent.output = f"Completed {queries_executed} searches, found {total_sources} total sources"

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 5.5: CONSOLIDATE BY GROUP
            # ═══════════════════════════════════════════════════════════════════
            async with cl.Step(name="📦 Consolidating Results", type="run") as consolidate_step:
                consolidate_step.input = "Grouping results by consolidation theme..."

                consolidated = consolidate_results_by_group(session.research_matrix, all_results)
                session.consolidated_results = consolidated

                group_summary = []
                for group_name, results in consolidated.items():
                    group_summary.append(f"- **{group_name}**: {results.source_count} sources from {len(results.queries_executed)} queries")

                consolidate_step.output = f"**{len(consolidated)} groups:**\n" + "\n".join(group_summary)

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 6: PYRAMID SYNTHESIS (Enhanced)
            # ═══════════════════════════════════════════════════════════════════
            async with cl.Step(name="🔺 Pyramid Synthesis", type="llm") as synth_step:
                synth_step.input = "Building comprehensive Minto Pyramid from consolidated research..."

                # Format consolidated results for synthesis
                consolidated_text = format_consolidated_for_synthesis(consolidated)

                synthesis_prompt = FINAL_SYNTHESIS_PROMPT.format(
                    scqa=session.scqa.to_prompt(),
                    beautiful_questions=session.beautiful_questions.to_prompt() if session.beautiful_questions else "",
                    consolidated_groups=consolidated_text,
                    original_confidence=int(session.scqa.confidence * 100)
                )

                synthesis_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=synthesis_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.5,
                        max_output_tokens=2500
                    )
                )

                synthesis = synthesis_response.text
                synth_step.output = f"Pyramid synthesis complete ({len(synthesis)} chars)"

            queries_executed = sum(len(v) for v in all_results.values())
            research_step.output = f"Research complete: SCQA → Beautiful Questions → {len(session.thoughts)} thoughts → {queries_executed} queries → {len(consolidated)} groups → Pyramid synthesis"

        # ═══════════════════════════════════════════════════════════════════
        # FINAL OUTPUT MESSAGE
        # ═══════════════════════════════════════════════════════════════════
        # Build comprehensive output
        final_output = f"""## 🔬 Research Analysis

### 📐 SCQA Framework (Minto Pyramid)
**Question:** {session.scqa.question}
**Hypothesis:** {session.scqa.answer_hypothesis} *(confidence: {session.scqa.confidence:.0%})*

---

{synthesis}

---

### 📊 Research Summary
- **WHY queries:** {len(all_results.get('why', []))}
- **WHAT IF queries:** {len(all_results.get('what_if', []))}
- **HOW queries:** {len(all_results.get('how', []))}
- **Validation queries:** {len(all_results.get('validation', []))}
- **Challenge queries:** {len(all_results.get('challenge', []))}
- **Total sources:** {sum(len(r.get('results', [])) for cat in all_results.values() for r in cat)}
"""

        # Add DataFrame if available
        elements = []
        if all_results:
            try:
                from utils.charts import create_research_results_dataframe
                flat_results = []
                for category, items in all_results.items():
                    for item in items:
                        for r in item.get("results", []):
                            r["query_type"] = category
                        flat_results.extend(item.get("results", []))

                if flat_results:
                    df_element = await create_research_results_dataframe(flat_results[:12])
                    if df_element:
                        elements.append(df_element)
            except Exception:
                pass

        await cl.Message(content=final_output, elements=elements).send()

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Research error: {error_details}")
        await cl.Message(content=f"Research error: {str(e)}").send()


@cl.action_callback("arxiv_search")
async def on_arxiv_search(action: cl.Action):
    """Search ArXiv for academic papers with humanized contextual analysis."""
    history = cl.user_session.get("history", [])

    # BUG FIX: Prioritize the LAST USER MESSAGE as the primary topic
    last_user_msg = ""
    for m in reversed(history):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")[:200]
            break

    recent = " ".join([m.get("content", "") for m in history[-4:]])[-300:]
    context_for_query = f"MOST RECENT USER TOPIC: {last_user_msg}\n\nBACKGROUND: {recent}"
    reason = action.payload.get("reason", "Graph suggested academic research")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📚 Analyzing Academic Research**\n*Why: {reason}*\n\n")

    # Extract search query from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract a concise academic search query (max 8 words). IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. Return ONLY the query:\n\n{context_for_query}",
    )
    search_query = qr.text.strip().strip('"')
    await msg.stream_token(f"*Searching: {search_query}*\n\n")

    from tools.arxiv_search import search_papers
    results = search_papers(search_query, max_results=7)

    # Contextualize results - humanize and analyze relevance
    try:
        from utils.research_contextualizer import contextualize_research, format_contextualized_output
        contextualized = await contextualize_research(
            research_type="academic",
            raw_results=results,
            conversation_context=history[-6:],
            search_query=search_query
        )
        formatted = format_contextualized_output(contextualized, "academic", search_query)
    except Exception as e:
        logger.warning(f"[ARXIV_SEARCH] Contextualization failed: {e}, using raw format")
        from tools.arxiv_search import format_papers_markdown
        formatted = format_papers_markdown(results)

    await msg.stream_token(formatted)
    await msg.update()

    history.append({"role": "model", "content": f"[Academic Analysis: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


@cl.action_callback("patent_search")
async def on_patent_search(action: cl.Action):
    """Search patents based on conversation context with humanized analysis."""
    history = cl.user_session.get("history", [])

    # BUG FIX: Prioritize the LAST USER MESSAGE as the primary topic
    last_user_msg = ""
    for m in reversed(history):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")[:200]
            break

    recent = " ".join([m.get("content", "") for m in history[-4:]])[-300:]
    context_for_query = f"MOST RECENT USER TOPIC: {last_user_msg}\n\nBACKGROUND: {recent}"
    reason = action.payload.get("reason", "Graph suggested patent landscaping")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**🔎 Analyzing Innovation Landscape**\n*Why: {reason}*\n\n")

    # Extract search query from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract a concise patent search query (max 8 words). IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. Return ONLY the query:\n\n{context_for_query}",
    )
    search_query = qr.text.strip().strip('"')
    await msg.stream_token(f"*Searching: {search_query}*\n\n")

    from tools.patent_search import search_patents
    results = search_patents(search_query, max_results=7)

    # Contextualize results - humanize and analyze relevance
    try:
        from utils.research_contextualizer import contextualize_research, format_contextualized_output
        contextualized = await contextualize_research(
            research_type="patents",
            raw_results=results,
            conversation_context=history[-6:],
            search_query=search_query
        )
        formatted = format_contextualized_output(contextualized, "patents", search_query)
    except Exception as e:
        logger.warning(f"[PATENT_SEARCH] Contextualization failed: {e}, using raw format")
        from tools.patent_search import format_patents_markdown
        formatted = format_patents_markdown(results)

    await msg.stream_token(formatted)
    await msg.update()

    history.append({"role": "model", "content": f"[Patent Analysis: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


@cl.action_callback("trends_search")
async def on_trends_search(action: cl.Action):
    """Search Google Trends with humanized contextual analysis."""
    history = cl.user_session.get("history", [])

    # BUG FIX: Prioritize the LAST USER MESSAGE as the primary topic
    last_user_msg = ""
    for m in reversed(history):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")[:200]
            break

    recent = " ".join([m.get("content", "") for m in history[-4:]])[-300:]
    context_for_query = f"MOST RECENT USER TOPIC: {last_user_msg}\n\nBACKGROUND: {recent}"
    reason = action.payload.get("reason", "Graph suggested trend analysis")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📈 Analyzing Market Trends**\n*Why: {reason}*\n\n")

    # Extract 1-3 trend search terms from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Extract 1-3 concise Google Trends search terms (each max 3 words). "
            "IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context. "
            "Return ONLY comma-separated terms, no explanation:\n\n" + context_for_query
        ),
    )
    search_query = qr.text.strip().strip('"')
    await msg.stream_token(f"*Searching: {search_query}*\n\n")

    from tools.trends_search import search_trends, search_related_queries

    # Fetch both timeseries and related queries
    timeseries = search_trends(search_query, data_type="TIMESERIES", date="today 12-m")
    related = search_related_queries(search_query)

    # Combine results for contextualization
    combined_results = {
        "timeseries": timeseries,
        "related_queries": related,
        "search_terms": search_query
    }

    # Contextualize results - humanize and analyze relevance
    try:
        from utils.research_contextualizer import contextualize_research, format_contextualized_output
        contextualized = await contextualize_research(
            research_type="trends",
            raw_results=combined_results,
            conversation_context=history[-6:],
            search_query=search_query
        )
        formatted = format_contextualized_output(contextualized, "trends", search_query)
    except Exception as e:
        logger.warning(f"[TRENDS_SEARCH] Contextualization failed: {e}, using raw format")
        from tools.trends_search import format_trends_markdown
        ts_formatted = format_trends_markdown(timeseries)
        rq_formatted = format_trends_markdown(related)
        formatted = f"{ts_formatted}\n\n---\n\n{rq_formatted}"

    await msg.stream_token(formatted)
    await msg.update()

    history.append({"role": "model", "content": f"[Trend Analysis: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


@cl.action_callback("govdata_search")
async def on_govdata_search(action: cl.Action):
    """Search US government data with humanized contextual analysis."""
    history = cl.user_session.get("history", [])

    # BUG FIX: Prioritize the LAST USER MESSAGE as the primary topic
    last_user_msg = ""
    for m in reversed(history):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")[:200]
            break

    recent = " ".join([m.get("content", "") for m in history[-4:]])[-300:]
    context_for_query = f"MOST RECENT USER TOPIC: {last_user_msg}\n\nBACKGROUND CONTEXT: {recent}"
    reason = action.payload.get("reason", "Graph suggested public data grounding")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**🏛️ Analyzing Public Statistics**\n*Why: {reason}*\n\n")

    # Use Gemini to extract a data-oriented query and pick sources
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Extract a data search query from this conversation. IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context.\n"
            "1) concise data search query (max 6 words) based on what the user JUST asked about\n"
            "2) which US government data sources are relevant: 'bls' (labor/employment/wages/CPI), "
            "'fred' (GDP/interest rates/economic indicators), 'census' (demographics/income/population). "
            "Return JSON like: {\"query\": \"...\", \"sources\": [\"bls\", \"fred\"]}\n\n" + context_for_query
        ),
    )

    import json as _json
    try:
        parsed = _json.loads(qr.text.strip().strip("```json").strip("```"))
        search_query = parsed.get("query", "economic trends")
        sources = parsed.get("sources", ["fred", "bls"])
    except Exception:
        search_query = qr.text.strip().strip('"')[:50]
        sources = None

    await msg.stream_token(f"*Searching: {search_query}*\n\n")

    from tools.govdata_search import search_govdata
    results = search_govdata(search_query, sources=sources)

    # Contextualize results - humanize and analyze relevance
    try:
        from utils.research_contextualizer import contextualize_research, format_contextualized_output
        contextualized = await contextualize_research(
            research_type="govdata",
            raw_results=results,
            conversation_context=history[-6:],
            search_query=search_query
        )
        formatted = format_contextualized_output(contextualized, "govdata", search_query)
    except Exception as e:
        logger.warning(f"[GOVDATA_SEARCH] Contextualization failed: {e}, using raw format")
        from tools.govdata_search import format_govdata_markdown
        formatted = format_govdata_markdown(results)

    await msg.stream_token(formatted)
    await msg.update()

    history.append({"role": "model", "content": f"[Data Analysis: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


@cl.action_callback("dataset_search")
async def on_dataset_search(action: cl.Action):
    """Search datasets with humanized contextual analysis."""
    history = cl.user_session.get("history", [])

    # BUG FIX: Prioritize the LAST USER MESSAGE as the primary topic
    last_user_msg = ""
    for m in reversed(history):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")[:200]
            break

    recent = " ".join([m.get("content", "") for m in history[-4:]])[-300:]
    context_for_query = f"MOST RECENT USER TOPIC: {last_user_msg}\n\nBACKGROUND: {recent}"
    reason = action.payload.get("reason", "Graph suggested dataset discovery")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📊 Finding Useful Datasets**\n*Why: {reason}*\n\n")

    # Extract dataset search query from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Extract a concise dataset search query (max 5 words). "
            "IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context or bot questions. "
            "Think about what raw data would help validate or explore the topic. "
            "Return ONLY the query:\n\n" + context_for_query
        ),
    )
    search_query = qr.text.strip().strip('"')
    await msg.stream_token(f"*Searching: {search_query}*\n\n")

    from tools.dataset_search import search_datasets
    results = search_datasets(search_query)

    # Contextualize results - humanize and analyze relevance
    try:
        from utils.research_contextualizer import contextualize_research, format_contextualized_output
        contextualized = await contextualize_research(
            research_type="datasets",
            raw_results=results,
            conversation_context=history[-6:],
            search_query=search_query
        )
        formatted = format_contextualized_output(contextualized, "datasets", search_query)
    except Exception as e:
        logger.warning(f"[DATASET_SEARCH] Contextualization failed: {e}, using raw format")
        from tools.dataset_search import format_datasets_markdown
        formatted = format_datasets_markdown(results)

    await msg.stream_token(formatted)
    await msg.update()

    history.append({"role": "model", "content": f"[Dataset Analysis: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


@cl.action_callback("news_search")
async def on_news_search(action: cl.Action):
    """Search news with humanized contextual analysis."""
    history = cl.user_session.get("history", [])

    # BUG FIX: Prioritize the LAST USER MESSAGE as the primary topic
    last_user_msg = ""
    for m in reversed(history):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")[:200]
            break

    recent = " ".join([m.get("content", "") for m in history[-4:]])[-300:]
    context_for_query = f"MOST RECENT USER TOPIC: {last_user_msg}\n\nBACKGROUND: {recent}"
    reason = action.payload.get("reason", "Graph suggested news signal analysis")

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token(f"**📰 Analyzing Current Events**\n*Why: {reason}*\n\n")

    # Extract news search query + optional category from context via Gemini
    qr = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Extract a news search query from this conversation. IMPORTANT: Focus on the MOST RECENT USER TOPIC, not old context.\n"
            "1) a news search query (max 6 words) based on what the user JUST asked about\n"
            "2) the most relevant news category from: politics, technology, business, "
            "health, science, environment, world (or 'none' if unclear). "
            "Return JSON: {\"query\": \"...\", \"category\": \"...\"}\n\n" + context_for_query
        ),
    )

    import json as _json
    try:
        parsed = _json.loads(qr.text.strip().strip("```json").strip("```"))
        search_query = parsed.get("query", "innovation")
        category = parsed.get("category")
        if category == "none":
            category = None
    except Exception:
        search_query = qr.text.strip().strip('"')[:40]
        category = None

    cat_label = f" ({category})" if category else ""
    await msg.stream_token(f"*Searching: {search_query}{cat_label}*\n\n")

    from tools.news_search import search_news
    results = search_news(search_query, max_results=7, category=category)

    # Contextualize results - humanize and analyze relevance
    try:
        from utils.research_contextualizer import contextualize_research, format_contextualized_output
        contextualized = await contextualize_research(
            research_type="news",
            raw_results=results,
            conversation_context=history[-6:],
            search_query=search_query
        )
        formatted = format_contextualized_output(contextualized, "news", search_query)
    except Exception as e:
        logger.warning(f"[NEWS_SEARCH] Contextualization failed: {e}, using raw format")
        from tools.news_search import format_news_markdown
        formatted = format_news_markdown(results)

    await msg.stream_token(formatted)
    await msg.update()

    history.append({"role": "model", "content": f"[News Analysis: {search_query}]\n{formatted}"})
    cl.user_session.set("history", history)


@cl.action_callback("gemini_deep_research")
async def on_gemini_deep_research(action: cl.Action):
    """
    Gemini Deep Research — comprehensive autonomous research (5-15 min).

    Flow:
    1. Expectation-setting message (immediate)
    2. cl.Step: Graph Intelligence (LazyGraphRAG + orchestrator compose query)
    3. cl.Step: Gemini Deep Research (background polling with live updates)
    4. cl.Step: Report storage (Supabase)
    5. Result message with download actions
    """
    import asyncio
    from tools.deep_research import (
        compose_research_query,
        start_deep_research,
        poll_deep_research,
        save_report_to_supabase,
        save_report_to_json,
    )

    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["lawrence"])
    bot_id = cl.user_session.get("bot_id", "lawrence")

    # Build recent context
    recent_context = ""
    for msg in history[-8:]:
        role = "User" if msg.get("role") == "user" else "Larry"
        content = msg.get("content", "")[:300]
        recent_context += f"{role}: {content}\n"

    # Derive research topic from last user message
    topic = ""
    for msg in reversed(history):
        if msg.get("role") == "user":
            topic = msg.get("content", "")
            break
    if not topic:
        await cl.Message(content="Please send a message first so I know what to research.").send()
        return

    # ── Expectation Setting (immediate) ──
    intro_msg = await cl.Message(content=f"""🔬 **Gemini Deep Research Starting**

**Topic:** {topic[:150]}{'...' if len(topic) > 150 else ''}

**What to expect:**
- ⏱️ This takes **5-15 minutes** (autonomous multi-source analysis)
- 📚 The agent will browse and analyze **30-50+ sources**
- 📊 You'll get a comprehensive research report with citations
- 🧠 Your conversation's graph intelligence shapes the research query

**You can keep chatting** — I'll notify you when results are ready.
""").send()

    # ── Phase 1: Graph Intelligence (cl.Step) ──
    try:
        async with cl.Step(name="🔬 Gemini Deep Research", type="run") as main_step:
            main_step.input = f"Topic: {topic[:200]}"

            # Phase 1: Compose query
            async with cl.Step(name="🧭 Graph Intelligence", type="tool") as graph_step:
                graph_step.input = "Querying LazyGraphRAG + Neo4j orchestrator for research framing..."

                composed_query, trace = compose_research_query(
                    topic, recent_context, bot_id
                )

                graph_output_parts = []
                if trace.get("lazy_concepts"):
                    graph_output_parts.append(f"**Key Concepts** (LazyGraphRAG): {', '.join(trace['lazy_concepts'])}")
                if trace.get("problem_type"):
                    graph_output_parts.append(f"**Problem Type**: {trace['problem_type']}")
                if trace.get("cynefin_domain"):
                    graph_output_parts.append(f"**Cynefin Domain**: {trace['cynefin_domain']}")
                if trace.get("frameworks"):
                    graph_output_parts.append(f"**Frameworks**: {', '.join(trace['frameworks'])}")
                if trace.get("techniques"):
                    graph_output_parts.append(f"**Techniques**: {', '.join(trace['techniques'][:5])}")

                graph_step.output = "\n".join(graph_output_parts) if graph_output_parts else "Using direct topic query (no graph matches)"

            # Phase 2: Start deep research
            async with cl.Step(name="📝 Research Query Composed", type="tool") as compose_step:
                compose_step.output = f"Query length: {len(composed_query)} chars\n\n{composed_query[:500]}..."

            # Phase 3: Gemini Deep Research (long-running)
            async with cl.Step(name="🔍 Gemini Deep Research", type="run") as research_step:
                research_step.input = "Autonomous agent browsing and analyzing sources..."

                # Start the research
                start_result = await start_deep_research(composed_query)

                if "error" in start_result:
                    research_step.output = f"❌ Failed to start: {start_result['error']}"
                    await cl.Message(
                        content=f"❌ **Deep Research failed to start:** {start_result['error']}\n\nTry the regular 🔍 Research button instead."
                    ).send()
                    return

                interaction_id = start_result["interaction_id"]

                # Progress message (updated during polling)
                progress_msg = cl.Message(content="🔍 Research in progress... (0s elapsed)")
                await progress_msg.send()

                # Poll with live updates
                async def on_progress(poll_count, elapsed_sec):
                    minutes = elapsed_sec // 60
                    seconds = elapsed_sec % 60
                    dots = "." * ((poll_count % 3) + 1)
                    time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                    await progress_msg.update(
                        content=f"🔍 Research in progress{dots} ({time_str} elapsed)\n\n"
                                f"_The agent is autonomously browsing and analyzing sources. "
                                f"You can keep chatting — I'll notify you when done._"
                    )
                    # Also update the step
                    research_step.output = f"Running... {time_str} elapsed"

                poll_result = await poll_deep_research(
                    interaction_id,
                    poll_interval=15,
                    on_progress=on_progress,
                )

                status = poll_result.get("status", "unknown")
                elapsed = poll_result.get("elapsed_sec", 0)
                report = poll_result.get("report", "")

                if status == "completed":
                    research_step.output = f"✅ Completed in {elapsed}s — {len(report)} chars"
                elif status == "failed":
                    research_step.output = f"❌ Failed: {poll_result.get('error', 'Unknown')}"
                elif status == "timeout":
                    research_step.output = f"⏰ Timed out after {elapsed}s"

                # Remove progress message
                await progress_msg.remove()

            # Phase 4: Storage
            report_url = None
            if report:
                async with cl.Step(name="💾 Saving Report", type="tool") as save_step:
                    report_url = save_report_to_supabase(report, topic, trace, bot_id)
                    save_report_to_json(report, topic, trace, bot_id)
                    if report_url:
                        save_step.output = f"✅ Saved to Supabase: {report_url}"
                    else:
                        save_step.output = "Report kept in session (Supabase not configured)"

            main_step.output = f"Status: {status} | {len(report)} chars | {elapsed}s"

        # ── Result Message ──
        if status == "completed" and report:
            # Truncate for chat display
            display_report = report
            if len(report) > 3000:
                display_report = report[:3000] + f"\n\n*... [{len(report) - 3000} more characters in full report]*"

            result_actions = []
            if report_url:
                result_actions.append(cl.Action(
                    name="open_report_url",
                    payload={"url": report_url},
                    label="📄 View Full Report",
                    tooltip="Open the complete research report",
                ))

            minutes = elapsed // 60
            seconds = elapsed % 60
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

            header_parts = [f"🔬 **Deep Research Complete** ({time_str})"]
            if trace.get("frameworks"):
                header_parts.append(f"**Frameworks applied**: {', '.join(trace['frameworks'][:3])}")
            if trace.get("lazy_concepts"):
                header_parts.append(f"**Graph concepts**: {', '.join(trace['lazy_concepts'][:4])}")

            await cl.Message(
                content="\n".join(header_parts) + f"\n\n---\n\n{display_report}",
                actions=result_actions,
            ).send()

            # Inject summary into conversation history so the bot can reference it
            research_summary = f"[Deep Research findings on '{topic[:80]}']: {report[:1500]}"
            history.append({"role": "model", "content": research_summary})
            cl.user_session.set("history", history)

        elif status == "failed":
            await cl.Message(
                content=f"❌ **Deep Research Failed**\n\n{poll_result.get('error', 'Unknown error')}\n\n"
                        f"Try the regular 🔍 Research button for a quick Tavily search instead."
            ).send()
        elif status == "timeout":
            await cl.Message(
                content=f"⏰ **Deep Research Timed Out** after {elapsed}s.\n\n"
                        f"The research may still be running on Google's servers. "
                        f"Try again or use the regular 🔍 Research button."
            ).send()

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Gemini Deep Research error: {error_details}")
        await cl.Message(
            content=f"❌ **Deep Research Error:** {str(e)}\n\nFalling back to regular research is available via 🔍 Research."
        ).send()


@cl.action_callback("think_through")
async def on_think_through(action: cl.Action):
    """Handle think through button - sequential thinking breakdown with cl.Step visualization."""
    history = cl.user_session.get("history", [])
    bot = cl.user_session.get("bot", BOTS["lawrence"])
    chat_profile = cl.user_session.get("chat_profile", "lawrence")

    # Build context from recent conversation
    # BUG FIX: Increased content truncation from 500 to 1000 chars to prevent incomplete analysis
    recent_context = ""
    for msg in history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")[:1000]  # Increased from 500 for better context
        recent_context += f"{role}: {content}\n"

    try:
        # Parent step for the thinking process
        async with cl.Step(name="Think It Through", type="run") as think_step:
            think_step.input = f"Analyzing: {recent_context[:150]}..."

            # Step 1: Extract the core problem
            async with cl.Step(name="Identifying Core Problem", type="llm") as problem_step:
                problem_prompt = f"""Based on this conversation context, identify the central question or problem being explored.

CONTEXT:
{recent_context}

WORKSHOP: {chat_profile}

In 1-2 sentences, state the core problem or question. Be specific and clear."""

                problem_step.input = "Extracting core problem..."
                # BUG FIX: Increased max_output_tokens from 200 to 400 to prevent truncation
                problem_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=problem_prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=400)
                )
                core_problem = problem_response.text.strip()
                problem_step.output = core_problem

            # Step 2: Extract assumptions
            async with cl.Step(name="Extracting Assumptions", type="llm") as assumptions_step:
                assumptions_prompt = f"""Given this problem: "{core_problem}"

And context:
{recent_context}

List 2-3 key assumptions that underlie this problem. Be specific about what is being taken for granted."""

                assumptions_step.input = f"Core problem: {core_problem[:100]}"
                # BUG FIX: Increased max_output_tokens from 300 to 500 to prevent truncation
                assumptions_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=assumptions_prompt,
                    config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=500)
                )
                assumptions = assumptions_response.text.strip()
                assumptions_step.output = assumptions

            # Step 3: Check what we know vs don't know
            async with cl.Step(name="Knowledge Gap Analysis", type="llm") as gaps_step:
                gaps_prompt = f"""Given this problem: "{core_problem}"
And these assumptions:
{assumptions}

Identify:
1. What do we have evidence for? (2-3 items)
2. What do we need to find out? (2-3 items)

Be specific and actionable."""

                gaps_step.input = "Analyzing evidence and gaps..."
                gaps_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=gaps_prompt,
                    config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=400)
                )
                knowledge_analysis = gaps_response.text.strip()
                gaps_step.output = knowledge_analysis

            # Step 4: Generate next steps
            async with cl.Step(name="Planning Next Steps", type="llm") as steps_step:
                # BUG FIX: Increased truncation limits from 200 to 500 chars for better context
                steps_prompt = f"""Given:
- Core Problem: {core_problem}
- Assumptions: {assumptions[:500]}
- Knowledge Gaps: {knowledge_analysis[:500]}

Suggest 2-3 concrete, actionable next steps to move forward. Be specific."""

                steps_step.input = "Generating action plan..."
                # FIX: Increase max_output_tokens from 300 to 800 for complete Think button responses
                steps_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=steps_prompt,
                    config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=800)
                )
                next_steps = steps_response.text.strip()
                steps_step.output = next_steps

            think_step.output = "Analysis complete"

        # Compile and send the full analysis as a message
        full_analysis = f"""## Structured Problem Breakdown

### Core Question/Problem
{core_problem}

### Key Assumptions
{assumptions}

### Knowledge Analysis
{knowledge_analysis}

### Suggested Next Steps
{next_steps}
"""
        # Include core action buttons so user can continue
        await cl.Message(
            content=full_analysis,
            actions=get_core_action_buttons(include_example=True)
        ).send()

    except Exception as e:
        await cl.Message(content=f"Thinking error: {str(e)}").send()


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with streaming and stop event support."""

    # DEBUG: Log incoming message details including file attachments
    _elem_count = len(message.elements) if message.elements else 0
    _elem_names = [e.name for e in message.elements] if message.elements else []
    logger.info(f"[ON_MESSAGE] content='{message.content[:50] if message.content else 'empty'}', elements={_elem_count}, names={_elem_names}")
    print(f"[ON_MESSAGE] Received: {_elem_count} elements, content={len(message.content or '')} chars")

    # Check if we're expecting a feedback comment
    if cl.user_session.get("expecting_feedback_comment"):
        from utils.feedback import store_feedback, get_feedback_confirmation_message

        feedback_context = cl.user_session.get("feedback_context", {})
        cl.user_session.set("expecting_feedback_comment", False)
        cl.user_session.set("feedback_context", None)

        # Get session context for storing the comment
        thread_id = cl.user_session.get("id", "unknown")
        bot_id = cl.user_session.get("chat_profile", "lawrence")

        # Store the comment with the previous feedback
        store_feedback(
            message_id=feedback_context.get("message_id", "unknown"),
            thread_id=thread_id,
            score=feedback_context.get("score", 3),
            comment=message.content,
            bot_id=bot_id,
            feedback_type="detailed",
        )

        # Show confirmation
        await cl.Message(
            content=f"""**💬 Comment Added!**

Thank you for your detailed feedback:
> *"{message.content[:200]}{'...' if len(message.content) > 200 else ''}"*

Your insights help us improve Mindrian!"""
        ).send()
        return  # Don't process as regular message

    # Check if user is providing an image generation prompt
    if cl.user_session.get("awaiting_image_prompt"):
        cl.user_session.set("awaiting_image_prompt", False)
        from utils.image_generation import generate_image, save_image_to_temp
        from utils.usage_metrics import track_image_generation

        prompt = message.content.strip()
        if prompt:
            async with cl.Step(name="Generating Image", type="tool") as step:
                step.input = f"Prompt: {prompt}"

                image_bytes, mime_type, metadata = await generate_image(
                    prompt=prompt,
                    model="fast",
                    aspect_ratio="square"
                )

                if image_bytes:
                    step.output = f"Image generated ({metadata.get('size_bytes', 0):,} bytes)"
                    temp_path = save_image_to_temp(image_bytes, mime_type)

                    # Track usage
                    context_key = get_context_key()
                    track_image_generation(context_key)

                    await cl.Message(
                        content=f"**Generated Image**\n\n*Prompt:* {prompt}",
                        elements=[cl.Image(name="generated_image", path=temp_path, display="inline")],
                        actions=[
                            cl.Action(name="generate_image", payload={"prompt": prompt}, label="Regenerate"),
                            cl.Action(name="generate_image", payload={}, label="New Image")
                        ]
                    ).send()
                else:
                    error_msg = metadata.get("user_message", metadata.get("error", "Unknown error"))
                    step.output = f"Failed: {error_msg}"
                    await cl.Message(content=f"**Image Generation Failed**\n\n{error_msg}").send()
        return  # Don't process as regular message

    # Check for image generation intent in message
    from utils.image_generation import detect_image_generation_intent
    is_image_request, image_prompt = detect_image_generation_intent(message.content)
    if is_image_request and image_prompt:
        from utils.image_generation import generate_image, save_image_to_temp
        from utils.usage_metrics import track_image_generation

        async with cl.Step(name="Generating Image", type="tool") as step:
            step.input = f"Detected image request: {image_prompt}"

            image_bytes, mime_type, metadata = await generate_image(
                prompt=image_prompt,
                model="fast",
                aspect_ratio="square"
            )

            if image_bytes:
                step.output = f"Image generated ({metadata.get('size_bytes', 0):,} bytes)"
                temp_path = save_image_to_temp(image_bytes, mime_type)

                # Track usage
                context_key = get_context_key()
                track_image_generation(context_key)

                await cl.Message(
                    content=f"**Generated Image**\n\n*Prompt:* {image_prompt}",
                    elements=[cl.Image(name="generated_image", path=temp_path, display="inline")],
                    actions=[
                        cl.Action(name="generate_image", payload={"prompt": image_prompt}, label="Regenerate"),
                        cl.Action(name="generate_image", payload={}, label="New Image")
                    ]
                ).send()
                return  # Image generated, don't process as regular message
            else:
                # Fall through to regular processing if image generation failed
                step.output = f"Image generation failed, falling back to text response"

    # === Triple-Mode: Auto-detect entry point on first message ===
    # BUG FIX: Only run entry point detection for NEW sessions (no history).
    # If there's existing history, user is in an active session - don't re-initialize.
    if TRIPLE_MODE_ENABLED:
        entry_point = cl.user_session.get("entry_point")
        existing_history = cl.user_session.get("history", [])

        if entry_point is None:
            # Check if this is a NEW session or a session that lost entry_point
            if len(existing_history) > 0:
                # Session has history but lost entry_point - set default, don't show selector
                # This prevents mid-session re-initialization on typo-heavy messages
                cl.user_session.set("entry_point", "brainstorming")
                cl.user_session.set("mode", "sandbox")
                print(f"[TRIPLE_MODE] Recovered lost entry_point for active session (history={len(existing_history)})")
            else:
                # True first message - auto-detect entry point
                has_attachment = bool(message.elements)
                logger.info(f"[TRIPLE_MODE] First message: has_attachment={has_attachment}, elements={len(message.elements) if message.elements else 0}, content='{message.content[:50]}'")
                detection = await auto_detect_entry_point(message.content, has_attachment)

                # SIMPLIFIED: No selector - just default to brainstorming if unsure
                # The starters provide navigation, selector was unreliable
                if detection["should_show_selector"]:
                    if has_attachment:
                        # Has attachment - force document_review mode
                        detection["entry_point"] = "document_review"
                        detection["mode"] = "workshop"
                        logger.info(f"[TRIPLE_MODE] Forced document_review due to attachment")
                    else:
                        # No attachment, low confidence - default to brainstorming
                        detection["entry_point"] = "brainstorming"
                        detection["mode"] = "sandbox"
                        logger.info(f"[TRIPLE_MODE] Defaulted to brainstorming (low confidence)")

                # High confidence - set entry point and continue
                cl.user_session.set("entry_point", detection["entry_point"])
                cl.user_session.set("mode", detection["mode"])

                # Show sidebar for brainstorming
                if detection["entry_point"] == "brainstorming":
                    await show_exploration_progress_sidebar()

    bot = cl.user_session.get("bot", BOTS["lawrence"])
    history = cl.user_session.get("history", [])
    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])
    settings = cl.user_session.get("settings", {})
    session_id = cl.user_session.get("id")
    bot_id = cl.user_session.get("bot_id", "lawrence")
    turn_count = len(history)

    # === Show pending opportunity notifications from previous turn ===
    # Opportunities are extracted in background, so we notify on next message
    if SESSION_MEMORY_ENABLED and session_id:
        pending_opps = get_pending_opportunities(str(session_id))
        if pending_opps:
            try:
                # Show a subtle notification that opportunities were found
                opp_names = [opp.get("name", "opportunity")[:40] for opp in pending_opps[:3]]
                notification = f"💡 **{len(pending_opps)} opportunity{'s' if len(pending_opps) > 1 else ''} captured**: {', '.join(opp_names)}"
                if len(pending_opps) > 3:
                    notification += f" (+{len(pending_opps) - 3} more)"
                await cl.Message(
                    content=notification,
                    actions=[
                        cl.Action(
                            name="view_opportunities",
                            payload={},
                            label="📊 View Bank",
                            tooltip="See all your captured opportunities"
                        )
                    ]
                ).send()
            except Exception as opp_err:
                logger.warning(f"[OPPORTUNITY] Notification error: {opp_err}")

    # === BUG-001 FIX: Topic Exclusion Detection ===
    # Check if user wants to exclude a topic from the conversation
    is_exclusion, excluded_topic = detect_topic_exclusion(message.content)
    if is_exclusion and excluded_topic:
        # Add to excluded topics list
        excluded_topics = cl.user_session.get("excluded_topics", [])
        if excluded_topic not in excluded_topics:
            excluded_topics.append(excluded_topic)
            cl.user_session.set("excluded_topics", excluded_topics)
            print(f"[EXCLUSIONS] Added topic: {excluded_topic} (total: {len(excluded_topics)})")

            # Confirm to user with management action
            await cl.Message(
                content=f"Got it, I'll avoid discussing **{excluded_topic}** in our conversation.",
                actions=[
                    cl.Action(
                        name="manage_exclusions",
                        payload={"action": "show"},
                        label="Manage Exclusions",
                        tooltip="View and manage excluded topics"
                    )
                ]
            ).send()

            # Persist exclusions to context store + Supabase
            context_key = get_context_key()
            if context_key in context_store:
                context_store[context_key]["excluded_topics"] = excluded_topics
                asyncio.create_task(_persist_context_async(context_key))
        else:
            await cl.Message(
                content=f"I'm already avoiding **{excluded_topic}**."
            ).send()

        # Don't process further - the exclusion request was handled
        return

    # === PWS Consultant: Stage-Aware Message Handler ===
    # The PWS Consultant uses a deterministic stage machine instead of workshop phases.
    # Each stage has a different interaction pattern, handled here instead of the generic flow.
    if bot_id == "pws_consultant":
        pws_stage = cl.user_session.get("pws_stage", "intro")

        if pws_stage == "intro":
            # Capture challenge description, run instant_analyze, accumulate text
            existing_challenge = cl.user_session.get("pws_challenge_description", "")
            cl.user_session.set("pws_challenge_description",
                                (existing_challenge + "\n" + message.content).strip())

            # Run instant analysis on challenge text
            try:
                from tools.pws_consultant_pipeline import instant_analyze
                intro_turn = cl.user_session.get("pws_intro_turn_count", 0) + 1
                cl.user_session.set("pws_intro_turn_count", intro_turn)
                signals = instant_analyze(message.content, intro_turn)
                cl.user_session.set("pws_challenge_signals", signals)
            except Exception as e:
                print(f"[PWS] instant_analyze error (non-critical): {e}")

            # Fire background domain discovery + two-stage classification on first turn
            if cl.user_session.get("pws_intro_turn_count", 0) == 1:
                try:
                    import asyncio
                    from tools.pws_consultant_pipeline import discover_domain_and_subdomains
                    domain_task = asyncio.create_task(
                        discover_domain_and_subdomains(message.content)
                    )
                    cl.user_session.set("pws_domain_task", domain_task)
                except Exception as e:
                    print(f"[PWS] domain discovery launch error: {e}")

                # Two-stage classification (Cynefin + PWS) - Quick win from AGENTS.md
                if TWO_STAGE_CLASSIFIER_ENABLED:
                    try:
                        async def run_classification(text: str):
                            classification = await classify(text)
                            print(f"[PWS] Classification: Cynefin={classification.cynefin}, PWS={classification.pws}")
                            return classification.to_dict()

                        classification_task = asyncio.create_task(run_classification(message.content))
                        cl.user_session.set("pws_classification_task", classification_task)
                    except Exception as e:
                        print(f"[PWS] classification launch error: {e}")

            # Add user message to history
            history.append({"role": "user", "content": message.content})
            cl.user_session.set("history", history)

            # Generate Larry's intro response (probing, not classifying)
            system_prompt = bot.get("system_prompt", PWS_CONSULTANT_PROMPT)
            system_prompt += "\n\n[STAGE: INTRO — Listen and probe. Do NOT classify yet. Ask 1-2 probing questions about the challenge.]"

            msg = cl.Message(content="")
            await msg.send()

            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                )
                response_stream = client.models.generate_content_stream(
                    model="gemini-3-flash-preview",
                    contents=history,
                    config=config,
                )
                full_response = ""
                for chunk in response_stream:
                    if chunk.text:
                        await msg.stream_token(chunk.text)
                        full_response += chunk.text
                await msg.update()

                history.append({"role": "model", "content": full_response})
                cl.user_session.set("history", history)
            except Exception as e:
                await msg.stream_token(f"I'm having trouble processing that. Could you try again? ({e})")
                await msg.update()

            return  # Handled — don't fall through to generic handler

        elif pws_stage == "diagnostic":
            # During diagnostic, MCQ is handled by action callbacks.
            # Any free text here gets a gentle redirect.
            history.append({"role": "user", "content": message.content})
            cl.user_session.set("history", history)

            redirect = ("I see you're typing — but the diagnostic questions above need your click to continue. "
                        "Pick the option that best fits your situation, and we'll keep moving. "
                        "If none of the options feel right, pick the closest one — we can always reclassify later.")
            await cl.Message(content=redirect).send()

            history.append({"role": "model", "content": redirect})
            cl.user_session.set("history", history)
            return  # Handled

        elif pws_stage == "consulting":
            # Augment system prompt with diagnostic context + expert panel info
            system_prompt = bot.get("system_prompt", PWS_CONSULTANT_PROMPT)

            # Add diagnostic context
            diag_context = cl.user_session.get("pws_diagnostic_context", "")
            if diag_context:
                system_prompt += "\n\n" + diag_context

            # Add hybrid retrieval context if available
            hybrid_context = cl.user_session.get("pws_hybrid_context", "")
            if hybrid_context:
                system_prompt += f"\n\n[KNOWLEDGE CONTEXT]\n{hybrid_context}"

            # Check sub-mode
            sub_mode = cl.user_session.get("pws_sub_mode", "normal")
            if sub_mode == "expert":
                expert_ctx = cl.user_session.get("pws_active_expert_context", "")
                if expert_ctx:
                    system_prompt += f"\n\n[EXPERT MODE]\n{expert_ctx}"

            # Track consulting turns
            consulting_turns = cl.user_session.get("pws_consulting_turn_count", 0) + 1
            cl.user_session.set("pws_consulting_turn_count", consulting_turns)

            # Exit condition: at turn 15+, suggest synthesis
            if consulting_turns >= 15:
                system_prompt += ("\n\n[TURN 15+ — You've covered substantial ground. "
                                  "Naturally suggest synthesizing the conversation: "
                                  "'We've covered a lot of ground. Would you like me to synthesize what we've discussed?']")

            # Add user message to history
            history.append({"role": "user", "content": message.content})
            cl.user_session.set("history", history)

            # Stream response
            msg = cl.Message(content="")
            await msg.send()

            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                )
                response_stream = client.models.generate_content_stream(
                    model="gemini-3-flash-preview",
                    contents=history,
                    config=config,
                )
                full_response = ""
                for chunk in response_stream:
                    if chunk.text:
                        await msg.stream_token(chunk.text)
                        full_response += chunk.text
                await msg.update()

                history.append({"role": "model", "content": full_response})
                cl.user_session.set("history", history)

                # === Red Team Validation (AGENTS.md pattern) ===
                # Run cross-cutting validation at key turns or when claims detected
                if PWS_VALIDATION_ENABLED:
                    try:
                        diagnosis = cl.user_session.get("pws_diagnosis", {})
                        problem_type = diagnosis.get("primary", "ill_defined")
                        last_val_turn = cl.user_session.get("pws_last_validation_turn", 0)

                        if should_validate(consulting_turns, last_val_turn, message.content, problem_type):
                            validation_result = await validate_pws_response(
                                user_message=message.content,
                                assistant_response=full_response,
                                problem_type=problem_type,
                                turn_count=consulting_turns,
                                context={"diagnosis": diagnosis}
                            )

                            cl.user_session.set("pws_last_validation_turn", consulting_turns)

                            # If validation has notable observations, append to response
                            validation_msg = format_validation_message(validation_result)
                            if validation_msg:
                                await msg.stream_token(validation_msg)
                                await msg.update()

                                # Also add to history so it's part of context
                                history[-1]["parts"][0] += validation_msg
                                cl.user_session.set("history", history)

                            # If reclassification suggested, offer the option
                            if validation_result.should_reclassify:
                                reclassify_action = cl.Action(
                                    name="reclassify_problem",
                                    payload={"reason": "validation_suggested"},
                                    label="🔄 Re-assess Problem Type",
                                    description="The problem may be evolving - re-run diagnostic"
                                )
                                await cl.Message(
                                    content="",
                                    actions=[reclassify_action]
                                ).send()

                            logger.debug(f"[PWS_VALIDATION] Turn {consulting_turns}: passed={validation_result.passed}, flags={len(validation_result.red_flags_detected)}")
                    except Exception as e:
                        logger.debug(f"[PWS_VALIDATION] Error: {e}")

                # Reset sub-mode after each turn (self-loop returns to normal)
                if sub_mode != "normal":
                    cl.user_session.set("pws_sub_mode", "normal")
                    cl.user_session.set("pws_active_expert_context", "")

            except Exception as e:
                await msg.stream_token(f"I'm having trouble with that. Let's try again. ({e})")
                await msg.update()

            # Sync to context store (including PWS state) + persist
            context_key = get_context_key()
            context_store[context_key] = {
                "bot_id": bot_id,
                "history": history.copy(),
                "phases": [],
                "current_phase": 0,
            }
            asyncio.create_task(_persist_context_async(context_key))

            # Sync PWS-specific state for cross-bot persistence
            if PWS_STATE_ENABLED:
                sync_pws_to_context_store()
                # Persist to Supabase every 5 turns
                if consulting_turns % 5 == 0:
                    asyncio.create_task(persist_pws_state_to_supabase())

            return  # Handled

    # === Smart Thread Matching for "continue from above" ===
    # Detect if user wants to continue a previous conversation topic
    if THREAD_SYSTEM_ENABLED and turn_count < 3:
        msg_lower = message.content.lower()
        continue_signals = ["continue", "from above", "where we left", "same as above", "keep going", "go on"]
        is_continue_request = any(signal in msg_lower for signal in continue_signals)

        if is_continue_request:
            try:
                context_key = get_context_key()
                # Find the right thread based on topic keywords in the message
                matching_thread = get_context_for_continue(context_key, message.content, bot_id)

                if matching_thread and len(matching_thread.history) > len(history):
                    # Found a better matching thread - restore its context
                    history = matching_thread.history.copy()
                    phases = [p.copy() for p in matching_thread.phases] if matching_thread.phases else phases
                    current_phase = matching_thread.current_phase

                    cl.user_session.set("history", history)
                    cl.user_session.set("phases", phases)
                    cl.user_session.set("current_phase", current_phase)
                    cl.user_session.set("current_thread_id", matching_thread.thread_id)

                    logger.info(f"[THREAD] Restored context from thread {matching_thread.thread_id} ({len(history)} messages)")
            except Exception as e:
                logger.debug(f"Thread matching error: {e}")

    # === Recursive Intelligence: Classify and log user reaction ===
    if SESSION_LOGGER_ENABLED and REACTION_CLASSIFIER_ENABLED and session_id:
        try:
            reaction = classify_reaction(message.content)
            # Only log non-neutral signals (reduce noise)
            if reaction.signal_type != "neutral" or reaction.confidence > 0.7:
                await log_session_event(
                    session_id=session_id,
                    event_type="reaction",
                    agent=bot_id,
                    signal_type=reaction.signal_type,
                    turn_count=turn_count,
                    metadata={
                        "confidence": reaction.confidence,
                        "indicators": reaction.indicators,
                        "suggested_action": getattr(reaction, 'suggested_action', None),
                        "message_preview": message.content[:100] if len(message.content) > 100 else message.content
                    }
                )
        except Exception as e:
            # Non-blocking - don't fail the message if classification fails
            print(f"[ReactionClassifier] Error (non-critical): {e}")

    # Reset stop event for this request
    if session_id and session_id in stop_events:
        stop_events[session_id].clear()

    # Process file attachments (PDF, DOCX, TXT, images, etc.)
    file_context = ""
    image_parts = []  # For Gemini multimodal
    image_elements = []  # For display
    failed_images = []  # Track failed images for text fallback

    # DEBUG: Log element count at start of processing
    element_count = len(message.elements) if message.elements else 0
    logger.info(f"[FILE PROCESSING] Starting with {element_count} elements, content='{message.content[:50] if message.content else 'empty'}'")
    print(f"[FILE PROCESSING] {element_count} elements to process")

    # DEBUG: If elements exist, log each one's details
    if message.elements:
        # IMMEDIATE USER FEEDBACK: Show file received with STREAMING status updates
        file_names = [getattr(e, 'name', 'file') for e in message.elements if hasattr(e, 'name')]
        if file_names:
            file_list = ", ".join(file_names[:3])
            if len(file_names) > 3:
                file_list += f" (+{len(file_names) - 3} more)"

            # Create streaming status message with PWS/Lawrence-style conversational language
            # Not robotic "processing..." but human thinking-out-loud
            import random
            opening_phrases = [
                "Interesting, let me take a look at this...",
                "Got it — reading through now...",
                "Okay, let me dig into this...",
                "Thanks! Opening this up...",
                "Perfect, let me see what we have here...",
            ]
            processing_status = cl.Message(content=f"📎 **{file_list}**\n\n")
            await processing_status.send()
            await processing_status.stream_token(f"*{random.choice(opening_phrases)}*\n\n")

            # Store reference for updates during processing
            cl.user_session.set("file_processing_status", processing_status)

        for idx, elem in enumerate(message.elements):
            elem_type = type(elem).__name__
            elem_name = getattr(elem, 'name', 'no-name')
            elem_path = getattr(elem, 'path', 'no-path')
            elem_mime = getattr(elem, 'mime', None) or getattr(elem, 'type', 'no-mime')
            print(f"[FILE PROCESSING] Element {idx}: type={elem_type}, name={elem_name}, path={elem_path}, mime={elem_mime}")
            logger.info(f"[FILE PROCESSING] Element {idx}: type={elem_type}, name={elem_name}, path={elem_path}, mime={elem_mime}")

    if message.elements:
        from utils.file_processor import process_uploaded_file, format_file_context, is_image_file, get_image_mime_type
        import os

        for element in message.elements:
            if hasattr(element, 'path') and element.path:
                # DEBUG: Log element details for file type diagnosis
                elem_mime = getattr(element, 'mime', None) or getattr(element, 'type', None)
                elem_name = element.name or ""
                elem_path = element.path or ""
                logger.info(f"[FILE UPLOAD] name={elem_name}, path={elem_path}, mime={elem_mime}")

                # Determine if this is a document (PDF, DOCX, etc.) vs image
                # Priority: 1) Extension from name, 2) Extension from path, 3) MIME type
                from pathlib import Path
                name_ext = Path(elem_name).suffix.lower() if elem_name else ""
                path_ext = Path(elem_path).suffix.lower() if elem_path else ""
                file_ext = name_ext or path_ext

                # Document extensions that should NEVER be treated as images
                DOCUMENT_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.css', '.xlsx', '.xls', '.pptx', '.ppt'}

                # Check MIME type for PDFs that might have wrong extension
                is_pdf_mime = elem_mime and 'pdf' in str(elem_mime).lower()
                is_document = file_ext in DOCUMENT_EXTENSIONS or is_pdf_mime

                # BUG FIX: Explicitly check for documents first, then images
                # This prevents PDFs from being misidentified as images
                # Get streaming status message for real-time feedback
                processing_status = cl.user_session.get("file_processing_status")

                if is_document:
                    logger.info(f"[FILE UPLOAD] Detected as DOCUMENT: ext={file_ext}, mime={elem_mime}")
                    is_image = False
                    # No status update here - we'll show progress during extraction
                else:
                    is_image = is_image_file(elem_name) or is_image_file(elem_path)
                    logger.info(f"[FILE UPLOAD] Detected as {'IMAGE' if is_image else 'UNKNOWN'}: ext={file_ext}, mime={elem_mime}")
                    if processing_status and is_image:
                        await processing_status.stream_token("*Looking at your image...*\n")

                # Check if it's an image file (by extension, not mime type)
                if is_image:
                    # Handle image upload for multimodal
                    async with cl.Step(name=f"Processing image: {element.name}", type="tool") as img_step:
                        img_step.input = f"Preparing image for analysis: {element.name}"
                        image_processed = False
                        try:
                            # Check file size before reading (Gemini limit ~20MB)
                            file_size = os.path.getsize(element.path)
                            if file_size > 20 * 1024 * 1024:  # 20MB limit
                                raise ValueError(f"Image too large ({file_size / 1024 / 1024:.1f}MB). Max 20MB.")

                            with open(element.path, "rb") as f:
                                image_bytes = f.read()

                            # Validate image bytes are not empty/corrupt
                            if len(image_bytes) < 100:
                                raise ValueError("Image file appears to be empty or corrupt")

                            mime_type = get_image_mime_type(element.name)

                            # Add to Gemini parts for multimodal
                            image_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

                            # Add to display elements
                            image_elements.append(cl.Image(name=element.name, path=element.path, display="inline"))

                            # Track image upload
                            from utils.usage_metrics import track_image_upload
                            track_image_upload(get_context_key())

                            img_step.output = f"Image ready ({len(image_bytes):,} bytes, {mime_type})"
                            image_processed = True

                        except Exception as img_err:
                            img_step.output = f"Error: {str(img_err)}"
                            failed_images.append({
                                "name": element.name,
                                "error": str(img_err),
                                "path": element.path
                            })

                        # Fallback: Add text description if image processing failed
                        if not image_processed:
                            fallback_desc = f"\n\n---\n**IMAGE UPLOAD (Processing Failed): {element.name}**\n"
                            fallback_desc += f"Error: {failed_images[-1]['error']}\n"
                            fallback_desc += "Note: The user attempted to upload an image but it could not be processed for visual analysis. "
                            fallback_desc += "Please acknowledge the upload attempt and ask the user to describe the image content or try re-uploading.\n---\n"
                            file_context += fallback_desc

                            await cl.Message(
                                content=f"**Image processing failed for {elem_name}**\n\n"
                                        f"Error: {failed_images[-1]['error']}\n\n"
                                        f"*The AI will acknowledge your upload but cannot see the image. "
                                        f"Please describe what's in the image or try re-uploading.*"
                            ).send()
                else:
                    # Extract text from uploaded document file (PDF, DOCX, TXT, etc.)
                    # Use Document AI as PRIMARY for PDFs (handwriting, equations, scanned docs)
                    async with cl.Step(name=f"Processing: {element.name}", type="tool") as file_step:
                        file_step.input = f"Extracting content from {element.name}"

                        content = ""
                        metadata = {}

                        # For PDFs: Smart multi-model extraction (Gemini Flash → Pro → Claude → PyPDF2)
                        if file_ext == '.pdf':
                            if processing_status:
                                reading_phrases = [
                                    "Reading through this PDF...",
                                    "Scanning through the pages...",
                                    "Working through the document...",
                                    "Going through this...",
                                ]
                                import random
                                await processing_status.stream_token(f"*{random.choice(reading_phrases)}*")

                            try:
                                from tools.smart_document import is_smart_doc_available, process_document_smart

                                if is_smart_doc_available():
                                    file_step.input = f"Smart document processing for {element.name}"
                                    logger.info(f"[SMART DOC] Processing PDF: {element.name}")

                                    # Process with smart multi-model fallback
                                    smart_result = await process_document_smart(
                                        file_path=element.path,
                                        file_name=element.name,
                                        extract_equations=True,
                                        extract_handwriting=True,
                                        max_pages=20
                                    )

                                    if smart_result.get("text") and not smart_result.get("error"):
                                        content = smart_result["text"]
                                        method = smart_result.get("method", "unknown")

                                        metadata = {
                                            "type": "pdf",
                                            "method": method,
                                            "char_count": len(content),
                                            "confidence": smart_result.get("confidence", "high"),
                                            "equations": smart_result.get("equations", []),
                                            "pages_processed": smart_result.get("pages_processed", 0),
                                        }
                                        logger.info(f"[SMART DOC] Success via {method}: {len(content)} chars, {len(metadata.get('equations', []))} equations")
                                        if processing_status:
                                            # Human-friendly size description
                                            if len(content) > 10000:
                                                size_desc = "quite a bit here"
                                            elif len(content) > 3000:
                                                size_desc = "good amount of content"
                                            else:
                                                size_desc = "got it"
                                            await processing_status.stream_token(f" — {size_desc}!\n")
                                    else:
                                        logger.warning(f"[SMART DOC] All methods failed, using PyPDF2: {smart_result.get('error', 'empty result')}")
                                        if processing_status:
                                            await processing_status.stream_token(" — trying another approach...\n")
                                else:
                                    logger.info(f"[SMART DOC] Not configured, using PyPDF2 for {element.name}")

                            except Exception as smart_err:
                                logger.warning(f"[SMART DOC] Error, falling back to PyPDF2: {smart_err}")

                        # Fallback to standard extraction (PyPDF2 for PDF, python-docx for DOCX, etc.)
                        if not content:
                            if processing_status:
                                # Stream PWS-style thinking tokens while extracting
                                # Creates Claude Code-like "sizzeling..." UX with Larry vocabulary
                                await processing_status.stream_token("\n")
                                content, metadata = await stream_thinking_while_processing(
                                    processing_status,
                                    process_uploaded_file,
                                    element.path, element.name,
                                    interval=0.35  # Slightly faster for responsiveness
                                )
                                # Show completion with human-friendly size description
                                char_count = metadata.get("char_count", len(content) if content else 0)
                                if char_count > 5000:
                                    await processing_status.stream_token("✅ *Finished!* Lots to work with.\n")
                                elif char_count > 1000:
                                    await processing_status.stream_token("✅ *Done!* Got it.\n")
                                else:
                                    await processing_status.stream_token("✅ *Complete!*\n")
                            else:
                                # No status message, just extract
                                content, metadata = process_uploaded_file(element.path, element.name)

                        if metadata.get("error"):
                            file_step.output = f"Error: {metadata['error']}"
                            if processing_status:
                                await processing_status.stream_token(f"\n*Hmm, ran into an issue: {metadata['error'][:40]}...*\n")
                            await cl.Message(content=f"Could not process **{element.name}**: {metadata['error']}").send()
                        else:
                            file_type = metadata.get("type", "file")
                            char_count = metadata.get("char_count", 0)
                            method = metadata.get("method", "standard")

                            # DEBUG: Log extraction results
                            logger.info(f"[PDF EXTRACT] file={element.name}, type={file_type}, method={method}, chars={char_count}")

                            if char_count < 50 and file_type == "pdf":
                                file_step.output = f"Warning: Only extracted {char_count} characters (may be scanned/image PDF)"
                                await cl.Message(
                                    content=f"⚠️ **{element.name}** appears to be a scanned or image-only PDF.\n\n"
                                            f"Only {char_count} characters could be extracted. "
                                            f"Please try:\n"
                                            f"1. Re-uploading a text-based PDF\n"
                                            f"2. Copy-pasting the content directly\n"
                                            f"3. Using a PDF with selectable text"
                                ).send()
                            else:
                                method_label = "📄 Document AI" if method == "document_ai" else "📄 Standard"
                                file_step.output = f"{method_label}: Extracted {char_count:,} characters from {file_type}"

                            # Add to context for LLM (even if small, include it)
                            file_context += format_file_context(element.name, content, metadata)

                            # Notify user with inline PDF display if applicable
                            info_msg = f"**{element.name}** processed"

                            # Show method used
                            if method in ["gemini_flash", "gemini_pro", "claude"]:
                                confidence = metadata.get("confidence", "high")
                                method_label = {
                                    "gemini_flash": "⚡ Gemini Flash",
                                    "gemini_pro": "🚀 Gemini Pro",
                                    "claude": "🤖 Claude"
                                }.get(method, method)
                                info_msg += f" {method_label} ({confidence})"
                                if metadata.get("equations"):
                                    info_msg += f" | {len(metadata['equations'])} equations"
                                if metadata.get("pages_processed"):
                                    info_msg += f" | {metadata['pages_processed']} pages"

                            elements = []

                            if file_type == "pdf":
                                if not method == "document_ai":
                                    info_msg += f" ({metadata.get('pages_extracted')}/{metadata.get('total_pages')} pages)"
                                # Add inline PDF viewer
                                elements.append(cl.Pdf(
                                    name=element.name,
                                    path=element.path,
                                    display="side"
                                ))
                            elif file_type == "docx":
                                info_msg += f" ({metadata.get('paragraphs')} paragraphs)"

                            if metadata.get("truncated"):
                                info_msg += " *(truncated for length)*"

                            await cl.Message(content=info_msg, elements=elements).send()

        # Display uploaded images together
        if image_elements:
            await cl.Message(
                content=f"**{len(image_elements)} image(s) uploaded** - analyzing...",
                elements=image_elements
            ).send()

    # DEBUG: Log file context after processing
    file_context_len = len(file_context) if file_context else 0
    logger.info(f"[FILE PROCESSING DONE] file_context length: {file_context_len} chars, images: {len(image_parts)}")
    print(f"[FILE PROCESSING DONE] file_context={file_context_len} chars, images={len(image_parts)}")

    # USER FEEDBACK: Complete the streaming status message with conversational wrap-up
    processing_status = cl.user_session.get("file_processing_status")
    if element_count > 0 and (file_context_len > 0 or len(image_parts) > 0):
        # Success - conversational completion
        if processing_status:
            import random
            if file_context_len > 10000:
                completion_phrases = [
                    "Okay, there's a lot here — let me think about this...",
                    "Got it all. This is substantial — thinking through it now...",
                    "Finished reading. Quite comprehensive — processing my thoughts...",
                ]
            elif file_context_len > 3000:
                completion_phrases = [
                    "All done reading. Let me gather my thoughts...",
                    "Got it! Thinking through what I've read...",
                    "Finished! Let me put together a response...",
                ]
            else:
                completion_phrases = [
                    "Got it! Let me think about this...",
                    "Okay, I see. Putting together my thoughts...",
                    "All set. Let me respond to this...",
                ]
            await processing_status.stream_token(f"\n✅ *{random.choice(completion_phrases)}*")
            await processing_status.update()
        else:
            # Fallback if no streaming status (shouldn't happen)
            await cl.Message(
                content=f"✅ *Got it! Thinking through this now...*"
            ).send()
    elif element_count > 0 and file_context_len == 0 and len(image_parts) == 0:
        # Files were uploaded but nothing was extracted - conversational warning
        if processing_status:
            await processing_status.stream_token("\n\n⚠️ *Hmm, I couldn't read the content from this file. ")
            await processing_status.stream_token("Could you try a different format, or paste the text directly?*")
            await processing_status.update()
        else:
            await cl.Message(
                content="⚠️ *Hmm, I couldn't read the content from this file. Could you try a different format, or paste the text directly?*"
            ).send()

    # === GRADING BOTS: ONE-SHOT AUTONOMOUS ASSESSMENT ===
    # When using grading or minto bot, automatically run the full modular assessment engine
    # with tool calling (Neo4j, FileSearch, Tavily, LangExtract)
    bot_id = cl.user_session.get("bot_id", "lawrence")
    if bot_id in ["grading", "minto"]:
        grading_content = None

        # Check for uploaded document content
        if file_context and len(file_context) > 200:
            grading_content = file_context

        # Or check for pasted text (substantial content = likely student work)
        elif len(message.content) > 500:  # >500 chars = probably student work, not a question
            grading_content = message.content

        if grading_content:
            # Run the full modular assessment engine with real-time TaskList progress
            try:
                from tools.assessment_engine import run_full_assessment

                session_id = str(cl.user_session.get("id", "anonymous"))
                user_id = session_id

                # === TASKLIST: Real-time progress tracking ===
                if UI_ELEMENTS_ENABLED:
                    task_list = await create_assessment_tasklist()
                    # Send TaskList separately to avoid for_id compatibility issue
                    try:
                        await task_list.send()
                    except TypeError as e:
                        if "for_id" not in str(e):
                            raise
                    progress_msg = cl.Message(
                        content="## 📝 Assessment in Progress\n\nTracking progress in sidebar..."
                    )
                    await progress_msg.send()

                    # Progress callback for assessment engine
                    async def progress_callback(message: str):
                        # Update TaskList based on module progress
                        if "Module 1" in message and "complete" in message:
                            await update_task_status(task_list, 0, cl.TaskStatus.DONE, message.split(":")[-1].strip() if ":" in message else "")
                            await update_task_status(task_list, 1, cl.TaskStatus.RUNNING)
                        elif "Module 2" in message and "complete" in message:
                            await update_task_status(task_list, 1, cl.TaskStatus.DONE, message.split(":")[-1].strip() if ":" in message else "")
                            await update_task_status(task_list, 2, cl.TaskStatus.RUNNING)
                        elif "Module 3" in message and "complete" in message:
                            await update_task_status(task_list, 2, cl.TaskStatus.DONE, message.split(":")[-1].strip() if ":" in message else "")
                            await update_task_status(task_list, 3, cl.TaskStatus.RUNNING)
                        elif "Module 4" in message and "complete" in message:
                            await update_task_status(task_list, 3, cl.TaskStatus.DONE, message.split(":")[-1].strip() if ":" in message else "")
                            await update_task_status(task_list, 4, cl.TaskStatus.RUNNING)
                        elif "Module 5" in message or "report" in message.lower():
                            await update_task_status(task_list, 4, cl.TaskStatus.DONE)
                        elif "Module 1" in message:
                            await update_task_status(task_list, 0, cl.TaskStatus.RUNNING)

                    # Start first module
                    await update_task_status(task_list, 0, cl.TaskStatus.RUNNING)
                else:
                    # Fallback to simple status message
                    progress_msg = cl.Message(content="📝 **Assessment submission received.**\n\n🔄 Running modular assessment engine...")
                    await progress_msg.send()
                    progress_callback = None

                # Run the full assessment with progress callback
                report, assessment_state = await run_full_assessment(
                    content=grading_content,
                    project_name="Student Submission",
                    project_domain="Problem Discovery",
                    student_id=session_id,
                    progress_callback=progress_callback if UI_ELEMENTS_ENABLED else None
                )

                # Mark all tasks complete
                if UI_ELEMENTS_ENABLED:
                    for i in range(5):
                        task_list.tasks[i].status = cl.TaskStatus.DONE
                    await safe_task_list_send(task_list)

                # Extract results for legacy compatibility
                results = {
                    "letter_grade": "See Report",
                    "final_score": 0,
                    "evidence_count": len(assessment_state.evidence_trail),
                    "modules_completed": assessment_state.modules_completed,
                    "phases": {"bias_detection": {"can_proceed": True}}  # Assessment engine doesn't block
                }

                # Extract and store opportunities found in student work
                opps = []
                try:
                    from tools.opportunity_bank import extract_and_store_opportunities

                    opps, opp_summary = await extract_and_store_opportunities(
                        conversation=[{"role": "user", "content": grading_content}],
                        bot_id="grading",
                        methodology="Problem Discovery Assessment",
                        phase="grading",
                        conversation_id=session_id,
                        user_id=user_id
                    )

                    if opps:
                        opp_note = f"\n\n---\n📊 **{len(opps)} opportunity/opportunities extracted** and stored in the Bank of Opportunities."
                        report += opp_note
                except Exception as opp_err:
                    print(f"Opportunity extraction error: {opp_err}")

                # Store assessment results in session for discussion
                cl.user_session.set("last_grading_results", results)
                cl.user_session.set("last_grading_report", report)
                cl.user_session.set("last_graded_content", grading_content[:5000])
                cl.user_session.set("last_assessment_state", assessment_state.to_dict())

                # === UI ELEMENTS: Enhanced display with GradeReveal and downloads ===
                if UI_ELEMENTS_ENABLED:
                    # Parse grade from report (look for grade pattern)
                    import re
                    grade_match = re.search(r'(?:Grade|GRADE)[:\s]*([A-F][+-]?)', report)
                    score_match = re.search(r'(\d{1,3}(?:\.\d+)?)\s*/\s*100', report)
                    grade = grade_match.group(1) if grade_match else "B"
                    score = float(score_match.group(1)) if score_match else 75.0

                    # Extract strengths and growth areas from report
                    strengths = []
                    growth_areas = []

                    # Look for strengths section
                    if "strength" in report.lower() or "well" in report.lower():
                        strength_section = re.search(r'(?:Strengths?|What.*Well|Positives?)[\s\S]*?(?=(?:Growth|Improvement|Missing|Weakness|$))', report, re.IGNORECASE)
                        if strength_section:
                            bullets = re.findall(r'[-•✓]\s*(.+?)(?=\n|$)', strength_section.group(0))
                            strengths = bullets[:5] if bullets else ["Evidence-based analysis attempted"]

                    # Look for growth areas
                    if "growth" in report.lower() or "improve" in report.lower() or "missing" in report.lower():
                        growth_section = re.search(r'(?:Growth|Improvement|Missing|Areas? for)[\s\S]*?(?=(?:Recommendation|Next|Action|$))', report, re.IGNORECASE)
                        if growth_section:
                            bullets = re.findall(r'[-•→]\s*(.+?)(?=\n|$)', growth_section.group(0))
                            growth_areas = bullets[:5] if bullets else ["Continue developing evidence"]

                    # Default values if extraction failed
                    if not strengths:
                        strengths = ["Submitted work for assessment", "Engaged with the grading process"]
                    if not growth_areas:
                        growth_areas = ["Review the detailed report for specific improvements"]

                    # Build components for score breakdown
                    components = []
                    state_dict = assessment_state.to_dict() if hasattr(assessment_state, 'to_dict') else {}
                    module_outputs = state_dict.get("module_outputs", {})

                    if module_outputs:
                        # Graph Analysis
                        graph_data = module_outputs.get("graph_analysis", {}).get("data", {})
                        components.append({
                            "name": "Framework Analysis",
                            "weight": 25,
                            "score": min(10, len(graph_data.get("frameworks", [])) * 2),
                            "assessment": f"Found {len(graph_data.get('frameworks', []))} relevant frameworks",
                            "evidence": [f["name"] if isinstance(f, dict) else str(f) for f in graph_data.get("frameworks", [])[:3]],
                            "missing": ["More framework application needed"] if len(graph_data.get("frameworks", [])) < 3 else []
                        })

                        # Pattern Discovery
                        pattern_data = module_outputs.get("pattern_discovery", {}).get("data", {})
                        components.append({
                            "name": "Pattern Discovery",
                            "weight": 25,
                            "score": min(10, len(pattern_data.get("patterns", [])) * 2),
                            "assessment": f"Discovered {len(pattern_data.get('patterns', []))} patterns",
                            "evidence": pattern_data.get("patterns", [])[:3],
                            "missing": ["More cross-domain patterns needed"] if len(pattern_data.get("patterns", [])) < 3 else []
                        })

                        # External Validation
                        validation_data = module_outputs.get("external_validation", {}).get("data", {})
                        confirmed = len(validation_data.get("confirmed_insights", []))
                        challenged = len(validation_data.get("challenged_insights", []))
                        val_score = min(10, (confirmed * 2) - challenged) if (confirmed + challenged) > 0 else 5
                        components.append({
                            "name": "External Validation",
                            "weight": 25,
                            "score": max(0, val_score),
                            "assessment": f"{confirmed} confirmed, {challenged} challenged insights",
                            "evidence": validation_data.get("confirmed_insights", [])[:3],
                            "missing": validation_data.get("challenged_insights", [])[:2]
                        })

                        # Synthesis
                        synthesis_data = module_outputs.get("synthesis", {}).get("data", {})
                        insights = synthesis_data.get("strategic_insights", [])
                        components.append({
                            "name": "Synthesis Quality",
                            "weight": 25,
                            "score": min(10, len(insights) * 2 + 4),
                            "assessment": f"Generated {len(insights)} strategic insights",
                            "evidence": [i.get("insight", str(i)) if isinstance(i, dict) else str(i) for i in insights[:3]],
                            "missing": []
                        })

                    # Create GradeReveal element (starts at context stage for soft landing)
                    grade_reveal = create_grade_reveal(
                        grade=grade,
                        score=score,
                        verdict=f"Analyzed {results['evidence_count']} evidence items across {len(results['modules_completed'])} modules",
                        strengths=strengths,
                        growth_areas=growth_areas,
                        evidence_count=results['evidence_count'],
                        components=components,
                        stage="context",  # Soft landing - start with context
                        bot_type=bot_id
                    )

                    # Create report download
                    from datetime import datetime
                    report_file = create_report_download(
                        content=report,
                        filename=f"assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.md"
                    )

                    # Create evidence display
                    evidence_items = [
                        {
                            "source_type": ev.get("source_type", "unknown"),
                            "tag_type": ev.get("tag_type", ""),
                            "confidence": ev.get("confidence", 0.5),
                            "content": ev.get("content", "")[:200]
                        }
                        for ev in assessment_state.evidence_trail[:20]
                    ] if hasattr(assessment_state, 'evidence_trail') else []

                    evidence_text = create_evidence_display(evidence_items) if evidence_items else None

                    # Display with custom elements
                    elements = [grade_reveal, report_file]
                    if evidence_text:
                        elements.append(evidence_text)

                    # Add opportunity cards if found
                    if opps:
                        for opp in opps[:3]:  # Show top 3
                            opp_card = create_opportunity_card(
                                opportunity_id=opp.get("id", ""),
                                title=opp.get("title", "Opportunity"),
                                problem=opp.get("description", opp.get("problem", "")),
                                evidence_quality=opp.get("evidence_quality", 3),
                                domain=opp.get("domain", "General"),
                                priority=opp.get("priority", "medium"),
                                source="Assessment",
                                frameworks=opp.get("frameworks", [])
                            )
                            elements.append(opp_card)

                    await cl.Message(
                        content="## Assessment Complete\n\nClick through the stages below to see your results:",
                        elements=elements,
                        actions=[
                            cl.Action(
                                name="discuss_grade",
                                payload={"grade": grade, "score": score, "bot_type": bot_id},
                                label="💬 Discuss with Lawrence",
                                description="Open conversation to discuss, clarify, or argue the assessment"
                            ),
                            cl.Action(
                                name="view_full_report",
                                payload={},
                                label="📄 View Full Report"
                            ),
                            cl.Action(
                                name="grade_student_work",
                                payload={},
                                label="📝 Assess Another"
                            )
                        ]
                    ).send()
                else:
                    # Fallback: Display full assessment report with discussion option (original behavior)
                    await progress_msg.remove()
                    await cl.Message(
                        content=report,
                        actions=[
                            cl.Action(
                                name="discuss_grade",
                                payload={"grade": "Assessment Complete"},
                                label="💬 Discuss Assessment with Lawrence",
                                description="Open conversation to discuss, clarify, or argue the assessment"
                            ),
                            cl.Action(
                                name="grade_student_work",
                                payload={},
                                label="📝 Assess Another Submission"
                            )
                        ]
                    ).send()

                return  # Done - don't continue with normal conversation

            except Exception as e:
                if 'progress_msg' in locals():
                    try:
                        await progress_msg.remove()
                    except:
                        pass
                await cl.Message(content=f"❌ **Grading Error**: {str(e)[:300]}\n\nPlease try again or contact support.").send()
                import traceback
                print(f"[GRADING] Error: {traceback.format_exc()}")
                return

        # If no substantial content, just respond with instructions
        # (handled by normal conversation flow below)

    # === ESCAPE HATCH: Detect "summarize" intent → trigger structured synthesis ===
    msg_lower = message.content.strip().lower()
    summarize_triggers = ["summarize", "summary so far", "sum up", "wrap up",
                          "what have we discussed", "recap the conversation"]
    if any(trigger in msg_lower for trigger in summarize_triggers) and len(history) >= 4:
        action = cl.Action(name="synthesize_conversation", payload={"action": "synthesize"})
        await on_synthesize_conversation(action)
        return

    # Build contents for Gemini
    contents = []
    for msg in history:
        # Support both "content" (standard) and "parts" (legacy) format
        text = msg.get("content") or (msg["parts"][0] if isinstance(msg.get("parts"), list) and msg["parts"] else "")
        # Normalize role: Gemini expects "user" or "model", never "assistant"
        role = msg.get("role", "user")
        if role == "assistant":
            role = "model"
        if text:
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=text)]
            ))

    # Add phase context for workshop bots
    phase_context = ""
    if phases and current_phase < len(phases):
        phase_context = f"\n\n[CURRENT WORKSHOP PHASE: {phases[current_phase]['name']} (Phase {current_phase + 1} of {len(phases)})]"

    # Add settings context
    detail_level = settings.get("response_detail", 1)
    workshop_mode = settings.get("workshop_mode", "guided")
    detail_instruction = ""
    if detail_level <= 3:
        detail_instruction = "\n[USER PREFERENCE: Be concise and brief in your response.]"
    elif detail_level >= 8:
        detail_instruction = "\n[USER PREFERENCE: Provide comprehensive, detailed explanations.]"

    # Combine user message with file context and other context
    full_user_message = message.content
    if file_context:
        full_user_message += f"\n\n{file_context}"
    full_user_message += phase_context + detail_instruction

    # === LangExtract: Instant signal extraction (<5ms) ===
    extraction_signals = None
    try:
        from tools.langextract import instant_extract, get_extraction_hint
        extraction_signals = instant_extract(message.content)
        cl.user_session.set("last_extraction", extraction_signals)
    except Exception:
        pass  # Non-fatal

    # === GraphRAG: Conditional context enrichment ===
    # Only enriches when user asks "what is X", mentions frameworks, or needs grounding
    # Returns hints (not lectures) to help Larry ask better questions
    turn_count = len(history) // 2
    graphrag_hint = None
    if GRAPHRAG_ENABLED and turn_count >= 0:
        try:
            bot_id = cl.user_session.get("bot_id", "lawrence")
            # BUG-001 FIX: Pass excluded topics to filter RAG results
            excluded_topics = cl.user_session.get("excluded_topics", [])
            graphrag_hint = enrich_for_bot(
                message.content, turn_count, bot_id=bot_id, excluded_topics=excluded_topics
            )
            if graphrag_hint:
                print(f"GraphRAG enriched ({bot_id}): {graphrag_hint[:100]}...")
        except Exception as e:
            print(f"GraphRAG error (non-fatal): {e}")

    # === JOURNEY MEMORY: Conductor-style persistent context ===
    # Loads user's PWS journey for cross-session continuity
    journey_context_str = None
    try:
        from memory import JourneyStore
        from memory.user_journey import create_journey_context_injection

        # Get user ID from session
        user_id = cl.user_session.get("user_id") or cl.user_session.get("id", "anonymous")
        journey_id = cl.user_session.get("journey_id")

        # Initialize journey store
        journey_store = JourneyStore(user_id)

        # Get or create journey on first substantial message
        if len(history) <= 2 and len(message.content) > 50:
            # First real message - create journey
            journey = await journey_store.get_or_create_journey(
                problem=message.content[:200],
                journey_id=journey_id
            )
            cl.user_session.set("journey_id", journey.id)
            cl.user_session.set("journey_store", journey_store)
            print(f"[JOURNEY] Created/loaded journey {journey.id}")
        elif journey_id:
            # Existing journey - load context
            journey = await journey_store.get_journey(journey_id)
            if journey:
                journey_store._current_journey = journey
                cl.user_session.set("journey_store", journey_store)

        # Get journey context for context engine
        if journey_store._current_journey:
            jctx = await journey_store.get_journey_context()
            if jctx:
                journey_context_str = create_journey_context_injection(jctx)
                print(f"[JOURNEY] Loaded context from journey {journey_store._current_journey.id}")

    except ImportError:
        pass  # Memory module not available
    except Exception as e:
        print(f"[JOURNEY] Error (non-fatal): {e}")

    # === CONTEXT ENGINE: Budget-aware layered context assembly ===
    # Replaces scattered context injection with unified, priority-based assembly.
    # Implements KG-RAG retrieval patterns: vector-first + graph expansion,
    # definition-aware retrieval, dynamic strategy selection, and session deduplication.
    if CONTEXT_ENGINE_ENABLED:
        try:
            context_result = ce_assemble_context(
                user_message=message.content,
                history=history,
                turn_count=turn_count,
                bot_id=cl.user_session.get("bot_id", "lawrence"),
                excluded_topics=cl.user_session.get("excluded_topics", []),
                graphrag_hint=graphrag_hint,
                extraction_signals=extraction_signals,
                journey_context=journey_context_str,
            )
            # Context engine returns enriched_message = user_message + context layers
            # Extract just the appended context layers
            ce_layers = context_result.enriched_message[len(message.content):]
            # Append context layers to the full_user_message (which already has
            # file_context, phase_context, and detail_instruction from earlier)
            full_user_message += ce_layers
            # Store system addendum for later injection into system_instruction
            cl.user_session.set("_ce_system_addendum", context_result.system_addendum)
            cl.user_session.set("_ce_last_strategy", context_result.retrieval_strategy)
            print(f"[CONTEXT_ENGINE] Assembled: layers={context_result.layers_used}, "
                  f"tokens={context_result.total_tokens_injected}, "
                  f"strategy={context_result.retrieval_strategy}, "
                  f"latency={context_result.latency_ms}ms")
        except Exception as e:
            print(f"[CONTEXT_ENGINE] Error (falling back to direct injection): {e}")
            # Fallback: inject directly as before
            if graphrag_hint:
                full_user_message += f"\n\n{graphrag_hint}"
            if journey_context_str:
                full_user_message += f"\n\n{journey_context_str}"
    else:
        # Legacy path: direct injection without budget management
        if graphrag_hint:
            full_user_message += f"\n\n{graphrag_hint}"
        # Saturation detection
        if turn_count >= 8:
            try:
                from tools.smart_phase_tracker import detect_saturation
                sat = detect_saturation(history)
                if sat.get("saturated"):
                    full_user_message += f"\n\n[System: Conversation saturation detected ({sat['signal']}). Consider suggesting the user press 🎯 Give me your answer if they seem ready for closure.]"
            except Exception:
                pass
        # LangExtract signals
        if extraction_signals and not extraction_signals.get("empty"):
            try:
                extraction_hint = get_extraction_hint(extraction_signals, turn_count)
                if extraction_hint:
                    full_user_message += f"\n\n{extraction_hint}"
            except Exception:
                pass
        # Journey context
        if journey_context_str:
            full_user_message += f"\n\n{journey_context_str}"

    # === AGENTIC VALIDATION WORKFLOW ===
    # When validation bot receives a substantive request, run the full workflow automatically
    bot_id = cl.user_session.get("bot_id", "lawrence")
    if bot_id == "validation" and len(message.content) > 50:
        try:
            from tools.validation_workflow import (
                run_validation_workflow,
                format_validation_report,
                is_validation_request
            )

            # Check if this is a validation request (not just "hello" or button clicks)
            if is_validation_request(message.content):
                # Show workflow starting message
                await cl.Message(
                    content="""## 🎯 Multi-Perspective Validation Starting

**Running autonomous 6-phase validation workflow...**

| Phase | Status |
|-------|--------|
| 0. Domain Resolution | ⏳ Running... |
| 1. Domain Extraction | ⬜ Pending |
| 2. Persona Construction | ⬜ Pending |
| 3. Parallel Research | ⬜ Pending |
| 4. Structured Debate | ⬜ Pending |
| 5. Validation Report | ⬜ Pending |

*This runs automatically - no clicks needed.*"""
                ).send()

                # Run the full agentic workflow
                state = await run_validation_workflow(message.content)

                # Format and deliver the final report
                if state.validation_report and state.validation_report.verdict:
                    report_md = format_validation_report(state)
                    await cl.Message(content=report_md).send()

                    # Update history with bounded sliding window
                    history = add_to_history(history, "user", message.content)
                    history = add_to_history(history, "model", report_md)
                    cl.user_session.set("history", history)

                    # Store validation summary for potential follow-up (avoid storing complex dataclass)
                    cl.user_session.set("validation_result", {
                        "verdict": state.validation_report.verdict,
                        "confidence": state.validation_report.confidence_level,
                        "challenge": state.domain_extraction.challenge_summary if state.domain_extraction else "",
                        "completed_phases": state.current_phase,
                    })
                else:
                    # Workflow failed - show errors
                    error_msg = "## Validation Workflow Error\n\n"
                    if state.errors:
                        error_msg += "\n".join([f"- {e}" for e in state.errors])
                    else:
                        error_msg += "Unknown error occurred during validation."
                    error_msg += f"\n\nCompleted phases: {state.current_phase}/5"
                    await cl.Message(content=error_msg).send()

                return  # Don't continue with normal LLM response

        except ImportError as e:
            print(f"Validation workflow import error: {e}")
            # Fall through to normal response
        except Exception as e:
            print(f"Validation workflow error: {e}")
            await cl.Message(content=f"Validation workflow error: {str(e)}. Falling back to normal response.").send()
            # Fall through to normal response

    # ═══════════════════════════════════════════════════════════════════════════
    # WAVE 5: Orchestration Middleware — Detect multi-agent opportunity
    # ═══════════════════════════════════════════════════════════════════════════
    orchestration_suggestion = None  # Stored for SUGGEST (shown AFTER normal response)
    try:
        from protocols.orchestration_middleware import (
            evaluate_message as _evaluate_orchestration,
            MiddlewareDecision,
            get_recommendation_message,
            get_suggestion_message,
            record_orchestration_dismissed,
        )

        middleware_result = await _evaluate_orchestration(
            message=message.content,
            history=history,
            session_id=str(session_id) if session_id else "",
            bot_id=bot_id,
            turn_count=turn_count,
            has_document=bool(file_context),
        )

        if middleware_result.decision == MiddlewareDecision.RECOMMEND:
            # HIGH confidence — show recommendation BEFORE normal response
            rec_text = get_recommendation_message(middleware_result)
            await cl.Message(
                content=f"🧠 {rec_text}",
                actions=[
                    cl.Action(
                        name="accept_orchestration",
                        payload={
                            "workflow_type": middleware_result.workflow_type,
                            "agents": middleware_result.suggested_agents,
                            "query": message.content,
                        },
                        label="▶ Run Analysis",
                        tooltip=f"Run {middleware_result.workflow_name} (~{max(1, middleware_result.estimated_seconds // 60)} min)",
                    ),
                    cl.Action(
                        name="dismiss_orchestration",
                        payload={},
                        label="Continue normally",
                        tooltip="Skip multi-agent analysis, get a regular response",
                    ),
                ],
            ).send()
            logger.info(f"[MIDDLEWARE] Showed RECOMMEND for {middleware_result.workflow_type} "
                        f"(confidence={middleware_result.confidence:.2f})")

        elif middleware_result.decision == MiddlewareDecision.SUGGEST:
            # MEDIUM confidence — store for showing AFTER normal response
            orchestration_suggestion = middleware_result

    except ImportError:
        pass
    except Exception as mw_err:
        logger.debug(f"[MIDDLEWARE] Evaluation error (non-fatal): {mw_err}")

    # Build multimodal content (supports images + text)
    user_parts = []
    if image_parts:
        # Add image parts first for Gemini multimodal
        user_parts.extend(image_parts)

    # Add text part (or default prompt if only images/files provided)
    # BUG FIX: Check full_user_message (which includes file_context) not just message.content
    # This ensures extracted PDF/document text is passed to the LLM even when user doesn't type anything
    if full_user_message.strip():
        text_content = full_user_message
    elif image_parts:
        # Only fall back to image prompt if there are actual images
        text_content = "Please analyze this image and describe what you see."
    elif file_context:
        # Document was uploaded - use document analysis prompt
        text_content = f"Please analyze this document and provide your thoughts.\n\n{file_context}"
    else:
        text_content = "Hello, how can I help you today?"

    user_parts.append(types.Part(text=text_content))

    contents.append(types.Content(
        role="user",
        parts=user_parts
    ))

    # === Extended Thinking UI ===
    # Show thinking panel for non-simple bots or when explicitly enabled
    settings = cl.user_session.get("settings", {})
    show_thinking = settings.get("show_thinking", True)  # Default to showing thinking
    # BUG FIX: Use chat_profile as source of truth (Chainlit sets this), then fall back to bot_id
    bot_id = cl.user_session.get("chat_profile") or cl.user_session.get("bot_id", "lawrence")

    # QA FIX: Show thinking panel for ALL bots (including simple_mode Lawrence)
    # User feedback: "LETS MAKE IT WORK INSTEAD OF HIDING IT"
    # The thinking panel helps users understand the AI's reasoning process
    if show_thinking:
        # Capture reasoning steps before generating response
        thinking_steps = await capture_reasoning_steps(message.content, bot_id, history)

        # ENHANCEMENT: Use ThinkingPanel custom element for rich visual display
        # This provides a collapsible panel with progress bar, bot-specific colors,
        # and expandable step details - much better UX than raw text
        methodology_map = {
            "tta": "Trending to the Absurd",
            "jtbd": "Jobs to Be Done",
            "scurve": "S-Curve Analysis",
            "redteam": "Red Team Challenge",
            "ackoff": "DIKW Pyramid",
            "scenario": "Scenario Planning",
            "beautiful_question": "Beautiful Questions",
            "nested_hierarchies": "Nested Hierarchies",
            "validation": "Multi-Perspective Validation",
            "bono": "Six Thinking Hats",
            "knowns": "Known Unknowns",
            "domain": "Domain Selection",
            "investment": "Investment Analysis",
        }
        methodology = methodology_map.get(bot_id)

        # Only show thinking panel if we actually have steps to display
        # QA FIX: Don't show empty "0/0 - Waiting for reasoning steps" panels
        if thinking_steps and len(thinking_steps) > 0:
            # Use the helper function to create the thinking panel element
            thinking_element = await show_thinking_panel(
                bot_id=bot_id,
                steps=thinking_steps,
                methodology=methodology
            )

            # Send thinking panel before the response
            await cl.Message(
                content="",
                elements=[thinking_element]
            ).send()

    # Create streaming message with agent attribution (UX-006)
    bot_name = bot.get("name", "Assistant")
    bot_icon = bot.get("icon", "🤖")
    msg = cl.Message(content="", author=f"{bot_icon} {bot_name}")
    await msg.send()

    try:
        # Check for cached context (RAG) for this bot
        bot_id = cl.user_session.get("bot_id", "lawrence")
        cache_name = get_cache_name(bot_id) if RAG_ENABLED else None

        # Build system instruction with context handoff if applicable
        # BUG FIX: Add language enforcement to prevent Chinese/other language responses (Bug 11)
        language_enforcement = "\n\n[LANGUAGE RULE: ALWAYS respond in English regardless of user's browser locale or system settings. Never respond in Chinese, Japanese, or other languages unless explicitly requested.]\n"
        system_instruction = bot["system_prompt"] + language_enforcement

        # === INVISIBLE ROUTING: Detect and inject methodology ===
        routing_result = None
        try:
            from agents.invisible_router import route_and_inject
            mindrian_mode = cl.user_session.get("mindrian_mode", "working")
            turn_count = len(history) // 2
            routing_result = await route_and_inject(
                user_message=message.content,
                conversation_history=history,
                turn_count=turn_count,
                base_bot_id=bot_id,
                mode=mindrian_mode,
                methodology_cooldowns=cl.user_session.get("methodology_cooldowns", {}),
                methodology_history=cl.user_session.get("methodology_history", []),
            )
            # Inject methodology into system prompt
            methodology_injection = routing_result.get("methodology_injection", "")
            if methodology_injection:
                system_instruction += f"\n\n{methodology_injection}\n"
                logger.info(f"[INVISIBLE_ROUTER] Injected: {routing_result.get('detected_methodology')} "
                      f"(confidence: {routing_result.get('methodology_confidence', 0):.2f}, "
                      f"latency: {routing_result.get('router_latency_ms', 0)}ms)")

            # === CONTEXT ENGINE: Inject system-level addendum (KG-RAG patterns) ===
            ce_addendum = cl.user_session.get("_ce_system_addendum", "")
            if ce_addendum:
                system_instruction += ce_addendum
                cl.user_session.set("_ce_system_addendum", "")  # consume once

            # Show subtle methodology attribution as a Step
            attribution_tag = routing_result.get("methodology_attribution_tag", "")
            if attribution_tag:
                async with cl.Step(name="Methodology", type="tool", show_input=False) as step:
                    step.output = f"Drawing on: {attribution_tag}"

            # Persist routing state back to session
            cl.user_session.set("methodology_cooldowns", routing_result.get("methodology_cooldowns", {}))
            cl.user_session.set("methodology_history", routing_result.get("methodology_history", []))

            # Persist routing state to context store
            context_key = get_context_key()
            if context_key and context_key in context_store:
                context_store[context_key]["routing_state"] = {
                    "methodology_cooldowns": routing_result.get("methodology_cooldowns", {}),
                    "methodology_history": routing_result.get("methodology_history", []),
                }
        except ImportError:
            logger.debug("[INVISIBLE_ROUTER] Module not available")
        except (ValueError, KeyError, TypeError) as router_err:
            logger.warning(f"[INVISIBLE_ROUTER] Data error: {type(router_err).__name__}: {router_err}")
        except Exception as router_err:
            logger.error(f"[INVISIBLE_ROUTER] Unexpected error: {type(router_err).__name__}: {router_err}")
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(router_err)
            except ImportError:
                pass

        # === A2A Protocol: Pre-process message for classification ===
        a2a_pre_result = None
        try:
            from protocols import A2A_ORCHESTRATION_ENABLED, pre_process_message
            orchestrator = cl.user_session.get("a2a_orchestrator")
            if A2A_ORCHESTRATION_ENABLED and orchestrator:
                a2a_pre_result = await pre_process_message(
                    message=message.content,
                    orchestrator=orchestrator,
                    bot_id=bot_id,
                )
                # Use enriched system prompt from handoff if available
                enriched_prompt = cl.user_session.get("a2a_enriched_prompt")
                if enriched_prompt:
                    system_instruction = enriched_prompt + language_enforcement
                    cl.user_session.set("a2a_enriched_prompt", None)  # Use once

                # === CONTEXT ENGINE + A2A: Inject A2A classification into context ===
                # Second-pass: A2A classification is now available, feed it back
                if CONTEXT_ENGINE_ENABLED and a2a_pre_result and a2a_pre_result.get("enabled"):
                    a2a_parts = []
                    classification = a2a_pre_result.get("classification", {})
                    if classification:
                        cynefin = classification.get("cynefin", "")
                        pws = classification.get("pws", "")
                        if cynefin or pws:
                            a2a_parts.append(f"[A2A: Cynefin={cynefin}, PWS={pws}]")
                    a2a_phase = a2a_pre_result.get("current_phase", "")
                    if a2a_phase:
                        a2a_parts.append(f"[A2A Phase: {a2a_phase}]")
                    context_hint = a2a_pre_result.get("context_hint", "")
                    if context_hint:
                        a2a_parts.append(context_hint)
                    suggested = a2a_pre_result.get("suggested_agent", "")
                    if suggested and suggested != bot_id:
                        a2a_parts.append(f"[A2A: {suggested} may offer a better lens here]")
                    if a2a_parts:
                        system_instruction += "\n\n" + " ".join(a2a_parts)
                        logger.info(f"[CONTEXT_ENGINE+A2A] Injected classification: {' '.join(a2a_parts)[:100]}")
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"[A2A] Pre-process error (non-fatal): {e}")

        # === QUICK MODE: Append speed-focused instructions ===
        quick_mode = cl.user_session.get("quick_mode", False)
        if quick_mode:
            quick_mode_prompt = """

[QUICK MODE ACTIVE]
The user wants SPEED. Follow these rules:
1. Lead with your key insight in ONE sentence
2. Follow with 3 bullet points maximum
3. Skip Socratic questions - give direct answers
4. Use progressive disclosure format:

**Key Insight:** [one sentence]

<details>
<summary>More details</summary>
[expanded explanation if relevant]
</details>

5. End with: "Want me to go deeper on any of these?"
[END QUICK MODE]
"""
            system_instruction += quick_mode_prompt

        # === BUG-001 FIX: Inject topic exclusions into system prompt ===
        excluded_topics = cl.user_session.get("excluded_topics", [])
        if excluded_topics:
            exclusion_prompt = f"""

[TOPIC EXCLUSIONS]
The user has requested to AVOID these topics: {', '.join(excluded_topics)}

CRITICAL RULES:
1. Do NOT bring up, mention, or reference these topics unprompted
2. If RAG retrieval returns content about these topics, IGNORE that content
3. If the user's question touches on an excluded topic, acknowledge the exclusion politely
4. If a framework or tool is named as excluded, do NOT recommend or explain it
5. Focus on alternative frameworks, tools, or approaches instead
[END EXCLUSIONS]
"""
            system_instruction += exclusion_prompt
            print(f"[EXCLUSIONS] Injected {len(excluded_topics)} exclusions into system prompt")

        # === IDEA CONTEXT: Focus and Avoid from Canvas ===
        # Starred ideas → positive context (focus on these)
        # Pruned ideas → negative context (avoid these)
        idea_focus_context = cl.user_session.get("idea_focus_context", [])
        idea_avoid_context = cl.user_session.get("idea_avoid_context", [])

        if idea_focus_context or idea_avoid_context:
            idea_context_prompt = "\n[IDEA CONTEXT FROM CANVAS]\n"

            if idea_focus_context:
                idea_context_prompt += "\n**FOCUS AREAS** (user-starred ideas — prioritize these):\n"
                for idea in idea_focus_context[:10]:
                    idea_context_prompt += f"- [{idea['type']}] {idea['content']}\n"
                idea_context_prompt += "\nPRIORITIZE responses that address or build upon these starred ideas.\n"

            if idea_avoid_context:
                idea_context_prompt += "\n**AVOID TOPICS** (user-pruned ideas — skip these):\n"
                for idea in idea_avoid_context[:10]:
                    idea_context_prompt += f"- [{idea['type']}] {idea['content']}\n"
                idea_context_prompt += "\nDO NOT bring up or explore these pruned topics unless user explicitly asks.\n"

            idea_context_prompt += "[END IDEA CONTEXT]\n"
            system_instruction += idea_context_prompt
            print(f"[IDEA_CONTEXT] Injected {len(idea_focus_context)} focus + {len(idea_avoid_context)} avoid ideas")

        context_handoff = cl.user_session.get("context_handoff")
        previous_bot = cl.user_session.get("previous_bot")

        if context_handoff and previous_bot:
            previous_bot_name = BOTS.get(previous_bot, {}).get("name", previous_bot)
            handoff_addendum = f"""

[CONTEXT HANDOFF NOTICE]
The user was previously working with {previous_bot_name} and has conversation context available.
Previous context is in history BUT:
- ALWAYS prioritize the user's CURRENT message over historical context
- If the user's new message introduces a NEW topic, ADDRESS THAT TOPIC directly
- Only reference previous context if directly relevant to the user's current question
- Do NOT continue old discussions if the user clearly changed subjects
The user expects you to be responsive to what they JUST said, not to lecture from old context.
[END HANDOFF NOTICE]
"""
            system_instruction = system_instruction + handoff_addendum

        # Build File Search tool for RAG
        file_search_tool = None
        if FILE_SEARCH_ENABLED:
            file_search_tool = types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[FILE_SEARCH_STORE]
                )
            )

        if cache_name:
            # Use cached context with RAG materials + File Search
            config = types.GenerateContentConfig(
                cached_content=cache_name,
                tools=[file_search_tool] if file_search_tool else None,
            )
            print(f"Using RAG cache: {cache_name} + File Search")
        else:
            # Use system instruction + File Search for all bots
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[file_search_tool] if file_search_tool else None,
            )
            if file_search_tool:
                print(f"Using File Search: {FILE_SEARCH_STORE}")

        # Use filesearch_client when FileSearch tool is active (store ownership)
        # FileSearch store requires gemini-2.5-flash (store owner's key)
        if file_search_tool:
            active_client = filesearch_client
            active_model = "gemini-2.5-flash"
        else:
            active_client = client
            active_model = "gemini-3-flash-preview"
        response_stream = active_client.models.generate_content_stream(
            model=active_model,
            contents=contents,
            config=config,
        )

        full_response = ""
        stopped = False

        for chunk in response_stream:
            # Check if user requested stop
            if session_id and session_id in stop_events and stop_events[session_id].is_set():
                full_response += "\n\n*[Response stopped by user]*"
                await msg.stream_token("\n\n*[Response stopped by user]*")
                stopped = True
                break

            if chunk.text:
                full_response += chunk.text
                await msg.stream_token(chunk.text)

        # Add action buttons to EVERY response (key actions always visible)
        actions = []
        if not stopped:
            # Determine if this bot uses simple_mode (Lawrence = clean, fewer buttons)
            is_simple = bot.get("simple_mode", False)

            # Core actions — simple_mode gets fewer buttons
            actions = [
                cl.Action(
                    name="deep_research",
                    payload={"action": "research"},
                    label="🔍 Research",
                    tooltip="Search the web for relevant data and evidence",
                ),
                cl.Action(
                    name="synthesize_conversation",
                    payload={"action": "synthesize"},
                    label="📥 Synthesize",
                    tooltip="Summarize conversation: key insights, breakthroughs, next steps",
                ),
            ]

            # Quick Mode toggle button - show current state
            quick_mode = cl.user_session.get("quick_mode", False)
            quick_mode_label = "Quick Mode: ON" if quick_mode else "Quick Mode: OFF"
            actions.append(cl.Action(
                name="toggle_quick_mode",
                payload={"action": "toggle"},
                label=quick_mode_label,
                tooltip="Toggle between fast direct answers and Socratic exploration",
            ))

            # Think button — all modes, but with clearer tooltip
            actions.append(cl.Action(
                name="think_through",
                payload={"action": "think"},
                label="🧠 Think",
                tooltip="Run a structured analysis: define the problem → list assumptions → find gaps → suggest next steps",
            ))

            # Fork and Ideas buttons (UX-001, UX-002)
            actions.append(cl.Action(
                name="fork_conversation",
                payload={"action": "fork"},
                label="🍴 Fork",
                tooltip="Create a branch to explore an alternative direction",
            ))
            actions.append(cl.Action(
                name="show_idea_canvas",
                payload={"action": "ideas"},
                label="💡 Ideas",
                tooltip="View and manage extracted ideas from this conversation",
            ))

            # Wave 4: Auto-Orchestration - Find the Breakthrough
            actions.append(cl.Action(
                name="find_breakthrough",
                payload={"action": "breakthrough"},
                label="🚀 Breakthrough",
                tooltip="Auto-orchestrated multi-agent analysis to find opportunities",
            ))

            # === Larry Teach Me: Contextual cognitive intervention button ===
            # Appears with special highlight when teachable moment detected
            try:
                from tools.quick_lecture import should_show_larry_button
                turn_count = cl.user_session.get("phase_turn_count", 0) + 1
                cached_analysis = cl.user_session.get("teachable_moment_analysis")

                show_larry, larry_tooltip = should_show_larry_button(
                    history=history,
                    turn_count=turn_count,
                    cached_analysis=cached_analysis
                )

                if show_larry:
                    has_teachable_moment = cached_analysis and cached_analysis.get("should_offer_intervention", False)
                    larry_label = "🎓✨ Larry teach me" if has_teachable_moment else "🎓 Larry teach me"
                    actions.append(cl.Action(
                        name="larry_teach_me",
                        payload={"action": "teach"},
                        label=larry_label,
                        tooltip=larry_tooltip or "Get a cognitive intervention from Larry",
                    ))
            except Exception as larry_err:
                # Fallback: always show button without context
                print(f"[LarryTeachMe] Context check error: {larry_err}")
                actions.append(cl.Action(
                    name="larry_teach_me",
                    payload={"action": "teach"},
                    label="🎓 Larry teach me",
                    tooltip="Get a cognitive intervention from Larry",
                ))

            # Deep Research (Gemini) — only in full/playground mode
            if not is_simple:
                actions.append(cl.Action(
                    name="gemini_deep_research",
                    payload={"action": "gemini_deep_research"},
                    label="🔬 Deep Research",
                    tooltip="Comprehensive AI research (5-15 min) — 50+ sources analyzed autonomously",
                ))

            # Use contextual actions for workshop bots (cleaner, fewer buttons)
            if bot.get("has_phases"):
                # Get phase-aware contextual actions
                turn_count = cl.user_session.get("phase_turn_count", 0)
                actions = get_contextual_actions(
                    bot=bot,
                    phases=phases,
                    current_phase=current_phase,
                    turn_count=turn_count,
                    is_simple=is_simple
                )

                # Increment turn counter (still useful for basic tracking)
                cl.user_session.set("phase_turn_count", turn_count + 1)

                # === SMART PHASE TRACKING ===
                # Use LLM to analyze if we should advance, not just turn count
                if SMART_PHASE_ENABLED and turn_count >= 2 and current_phase < len(phases) - 1:
                    try:
                        # Build conversation history for analysis
                        analysis_history = history + [
                            {"role": "user", "content": message.content},
                            {"role": "model", "content": full_response}
                        ]

                        # Analyze workshop state with LLM
                        workshop_state = await analyze_workshop_state(
                            conversation_history=analysis_history,
                            workshop_type=bot_id,
                            current_phase_index=current_phase,
                            phases=phases
                        )

                        # Save smart context for future reference
                        phase_context = extract_phase_context(workshop_state)
                        cl.user_session.set("smart_phase_context", phase_context)

                        # NOTE: Removed auto-advance prompts per user feedback
                        # User controls ALL navigation - we only track state silently
                        # The should_advance flag is now used for internal tracking only
                        # Users can see their progress with "show progress" button and
                        # explicitly choose to advance with "next_phase" button

                    except Exception as e:
                        print(f"Smart phase tracking error: {e}")
                        # NOTE: Removed turn-based nudges per user feedback
                        # User controls ALL navigation - no auto-prompts to advance

                # NOTE: Removed turn-based nudges per user feedback
                # User controls ALL navigation - no auto-prompts based on turn count
            else:
                # Non-workshop bots get example; multi-agent only for non-simple bots
                actions.append(cl.Action(
                    name="show_example",
                    payload={"action": "example"},
                    label="📖 Example",
                    tooltip="View a real-world example of this methodology",
                ))
                if not is_simple:
                    actions.append(cl.Action(
                        name="multi_agent_analysis",
                        payload={"action": "multi_agent"},
                        label="👥 Multi-Agent",
                        tooltip="Get perspectives from multiple PWS experts",
                    ))

        # === INVISIBLE ROUTING: 3-tier attribution ===
        if routing_result and routing_result.get("detected_methodology"):
            confidence = routing_result.get("methodology_confidence", 0)
            label = routing_result.get("methodology_label", "")
            should_suggest = routing_result.get("should_suggest", False)

            if should_suggest and label:
                # Tier 3: Low confidence (<0.7) — show suggestion button
                actions.append(cl.Action(
                    name="accept_methodology_suggestion",
                    payload={
                        "methodology": routing_result["detected_methodology"],
                        "label": label,
                    },
                    label=f"💡 Want me to try {label}?",
                    tooltip=f"Apply {label} methodology to this conversation",
                ))
            elif confidence >= 0.7 and confidence < 0.85 and label:
                # Tier 2: Medium confidence — subtle footer
                msg.content = full_response + f"\n\n---\n*{label}*"

            # Tier 1: High confidence (>=0.85) — silent, no attribution shown

        # Add dynamic agent suggestions based on conversation context
        if not stopped and len(history) >= 2:
            current_bot_id = cl.user_session.get("bot_id", "lawrence")
            # Include the new messages for analysis
            updated_history = history + [
                {"role": "user", "content": message.content},
                {"role": "model", "content": full_response}
            ]
            agent_suggestions = await suggest_agents_from_context(
                updated_history,
                current_bot_id,
                max_suggestions=2
            )
            if agent_suggestions:
                actions.extend(agent_suggestions)

            # Contextual research tool buttons (graph-driven)
            research_tools = await suggest_research_tools(updated_history, current_bot_id)
            if research_tools:
                actions.extend(research_tools)

            # LangGraph pipeline buttons (bot-specific advanced workflows)
            if LANGGRAPH_PIPELINES_ENABLED:
                pipeline_buttons = get_pipeline_buttons(current_bot_id)
                if pipeline_buttons:
                    actions.extend(pipeline_buttons)

        if actions:
            msg.actions = actions

        await msg.update()

        # === WAVE 5: Show orchestration SUGGESTION after normal response ===
        if orchestration_suggestion:
            try:
                from protocols.orchestration_middleware import get_suggestion_message
                sug_text = get_suggestion_message(orchestration_suggestion)
                await cl.Message(
                    content=f"💡 {sug_text}",
                    actions=[
                        cl.Action(
                            name="accept_orchestration",
                            payload={
                                "workflow_type": orchestration_suggestion.workflow_type,
                                "agents": orchestration_suggestion.suggested_agents,
                                "query": message.content,
                            },
                            label="Run deeper analysis",
                            tooltip=f"Run {orchestration_suggestion.workflow_name}",
                        ),
                    ],
                ).send()
                logger.info(f"[MIDDLEWARE] Showed SUGGEST for {orchestration_suggestion.workflow_type} "
                            f"(confidence={orchestration_suggestion.confidence:.2f})")
            except Exception as sug_err:
                logger.debug(f"[MIDDLEWARE] Suggestion display error: {sug_err}")

        # Update history with bounded sliding window (prevents memory leaks)
        history = add_to_history(history, "user", message.content)
        history = add_to_history(history, "model", full_response)
        cl.user_session.set("history", history)

        # === Per-User LazyGraph Memory: Process turn and extract entities ===
        if SESSION_MEMORY_ENABLED:
            try:
                user_id = cl.user_session.get("memory_user_id")
                if user_id and session_id:
                    phase_name = phases[current_phase]["name"] if phases and current_phase < len(phases) else ""
                    # Run in background (don't block response)
                    asyncio.create_task(session_memory_process(
                        user_id=user_id,
                        session_id=session_id,
                        conversation=history,
                        bot_id=bot_id,
                        phase=phase_name,
                    ))
            except Exception as e:
                print(f"[SESSION_MEMORY] Process error: {e}")

        # BUG FIX: Clear context_handoff after first response to prevent persistent context pollution
        # The handoff notice should only affect the FIRST message after a bot switch
        if cl.user_session.get("context_handoff"):
            cl.user_session.set("context_handoff", None)
            cl.user_session.set("previous_bot", None)

        # === Larry Teach Me: Background teachable moment detection ===
        # Runs every 3-7 turns to detect when Larry can provide valuable intervention
        turn_count = cl.user_session.get("phase_turn_count", 0) + 1
        if turn_count >= 3 and turn_count % 2 == 1:  # Turns 3, 5, 7, 9...
            try:
                from tools.quick_lecture import background_teachable_moment_check
                # Run analysis in background (don't block response)
                async def run_teachable_analysis():
                    analysis = await background_teachable_moment_check(
                        session_id=session_id,
                        history=history,
                        turn_count=turn_count
                    )
                    if analysis:
                        cl.user_session.set("teachable_moment_analysis", analysis)
                        if analysis.get("should_offer_intervention"):
                            print(f"[TeachableMoment] Detected at turn {turn_count}: {analysis.get('larry_might_say', '')[:50]}")

                asyncio.create_task(run_teachable_analysis())
            except Exception as tm_err:
                print(f"[TeachableMoment] Background check error: {tm_err}")

        # === Triple-Mode: Extract topics and check semantic grounding ===
        if TRIPLE_MODE_ENABLED:
            entry_point = cl.user_session.get("entry_point")

            # Extract topics and update progress (uses LangExtract)
            signals = await extract_and_update_progress(message.content)

            # Check for semantic grounding (only in brainstorming, with cooldown)
            if entry_point == "brainstorming" and signals:
                grounding_reason = check_semantic_grounding(signals)
                if grounding_reason:
                    last_grounding = cl.user_session.get("last_grounding_reason")
                    last_grounding_turn = cl.user_session.get("last_grounding_turn", 0)
                    current_turn = len(history) // 2
                    # Don't show same grounding prompt within 3 turns
                    if grounding_reason != last_grounding or current_turn - last_grounding_turn >= 3:
                        cl.user_session.set("last_grounding_reason", grounding_reason)
                        cl.user_session.set("last_grounding_turn", current_turn)
                        await show_grounding_prompt(grounding_reason)

        # === DISABLED: Auto-detect phase progression ===
        # BUG FIX: Removed auto-advancement based on LLM response keywords.
        # This caused unexpected phase jumps without user consent (Bug 8).
        # Users now control ALL phase navigation via explicit "Next Phase" button.
        # The code below is preserved as comment for reference but disabled:
        #
        # if phases and bot.get("has_phases") and current_phase < len(phases) - 1:
        #     # Auto-detect based on transition signals in response
        #     # DISABLED: This caused phases to jump unexpectedly
        #     pass

        # === Phase Insights: Surface AI intelligence to user ===
        if phases and bot.get("has_phases") and PHASE_INSIGHTS_ENABLED and SMART_PHASE_ENABLED:
            try:
                # Track turns for insight frequency control
                turn_count = cl.user_session.get("phase_turn_count", 0) + 1
                last_insight_turn = cl.user_session.get("last_insight_turn", 0)
                insight_preference = settings.get("insight_mode", "balanced")
                cl.user_session.set("phase_turn_count", turn_count)

                bot_id = cl.user_session.get("bot_id", "lawrence")

                # Get intelligent phase insight (async call to smart_phase_tracker)
                insight = await get_phase_insight_for_response(
                    history=history,
                    bot_id=bot_id,
                    current_phase=current_phase,
                    phases=phases,
                    turn_count=turn_count,
                    last_insight_turn=last_insight_turn,
                    preference=insight_preference
                )

                if insight and insight.show:
                    cl.user_session.set("last_insight_turn", turn_count)

                    # Build insight actions as Chainlit Actions
                    insight_actions = []
                    for action_info in get_insight_actions(insight):
                        insight_actions.append(cl.Action(
                            name=action_info["name"],
                            payload={"from_insight": True, "type": insight.type.value},
                            label=action_info["label"],
                            description=action_info.get("tooltip", "")
                        ))

                    # Send insight as follow-up message
                    await cl.Message(
                        content=insight.message,
                        actions=insight_actions if insight_actions else None
                    ).send()

                    print(f"[INSIGHT] Showed {insight.type.value} insight (confidence: {insight.confidence:.2f})")

            except Exception as e:
                print(f"[PHASE INSIGHT] Error (non-critical): {e}")

        # Refresh WorkshopRoadmap for workshop bots (keeps it in sync every message)
        if phases and bot.get("has_phases"):
            try:
                phase_insights = extract_phase_insights(history, phases, current_phase)
                await create_or_update_roadmap(
                    phases=phases,
                    current_phase=current_phase,
                    bot_name=bot.get("name", "Workshop"),
                    bot_icon=bot.get("icon", "🎯"),
                    phase_context=phase_insights
                )
            except Exception:
                pass

        # === A2A Protocol: Post-process response ===
        try:
            from protocols import A2A_ORCHESTRATION_ENABLED, post_process_response
            orchestrator = cl.user_session.get("a2a_orchestrator")
            if A2A_ORCHESTRATION_ENABLED and orchestrator and response_text:
                a2a_post = await post_process_response(
                    response=response_text,
                    orchestrator=orchestrator,
                    bot_id=cl.user_session.get("bot_id", "lawrence"),
                )
                # If A2A suggests a transition, show as subtle suggestion
                suggested = a2a_post.get("suggested_transition") if a2a_post else None
                if suggested and suggested != cl.user_session.get("bot_id"):
                    suggested_name = BOTS.get(suggested, {}).get("name", suggested)
                    logger.info(f"[A2A] Suggested transition to: {suggested_name}")
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"[A2A] Post-process error (non-fatal): {e}")

        # Sync history + phases to context store for preservation across bot switches
        context_key = get_context_key()
        bot_id = cl.user_session.get("bot_id", "lawrence")
        phases = cl.user_session.get("phases", [])
        current_phase = cl.user_session.get("current_phase", 0)

        context_store[context_key] = {
            "bot_id": bot_id,
            "history": history.copy(),
            "phases": [p.copy() for p in phases] if phases else [],
            "current_phase": current_phase,
        }

        # === Thread System: Save to topic-aware thread ===
        if THREAD_SYSTEM_ENABLED:
            try:
                thread_id = cl.user_session.get("current_thread_id")
                if not thread_id:
                    # Get or create thread for this conversation
                    thread_id, _ = get_or_create_thread(context_key, bot_id, history)
                    cl.user_session.set("current_thread_id", thread_id)
                # Update thread with latest context
                save_thread_context(
                    thread_id=thread_id,
                    user_key=context_key,
                    history=history,
                    phases=phases,
                    current_phase=current_phase,
                    bot_id=bot_id
                )
            except Exception as e:
                logger.debug(f"Thread save error: {e}")

        # Persist to Supabase for cross-session survival
        # CRITICAL: Await the save to ensure context survives server restarts/deploys
        # Previously fire-and-forget caused P0 data loss on Render deploys
        from utils.context_persistence import save_cross_bot_context
        try:
            # Update last_checkpoint on each message
            last_checkpoint = datetime.utcnow().isoformat()
            cl.user_session.set("last_checkpoint", last_checkpoint)

            # BUG-001 FIX: Persist excluded_topics on every message
            await save_cross_bot_context(
                user_key=context_key,
                history=history.copy(),
                bot_id=bot_id,
                bot_name=BOTS.get(bot_id, {}).get("name", bot_id),
                phases=[p.copy() for p in phases] if phases else None,
                current_phase=current_phase,
                conversation_id=cl.user_session.get("conversation_id"),
                conversation_name=cl.user_session.get("conversation_name", ""),
                excluded_topics=cl.user_session.get("excluded_topics", [])
            )
        except Exception as e:
            # Log but don't fail the response
            logger.warning(f"Context persistence failed: {e}")

        # Background intelligence: deep extraction + coherence tracking
        if len(history) >= 4 and len(history) % 5 < 2:
            try:
                from tools.langextract import background_intelligence
                asyncio.create_task(background_intelligence(
                    history=history.copy(),
                    bot_id=bot_id,
                    session=cl.user_session,
                ))
            except Exception:
                pass

        # Track usage metrics
        from utils.usage_metrics import track_context_save, track_message
        track_context_save(context_key, bot_id, len(history))
        track_message(session_id or "unknown", context_key, bot_id)

        # Save session metadata for resume (phases, settings, current_phase)
        # Metadata is persisted through the data layer when threads are saved
        chat_profile = cl.user_session.get("chat_profile", "lawrence")
        try:
            # Update thread metadata for resume
            thread_id = cl.context.session.thread_id
            if thread_id and hasattr(cl.context.session, 'thread'):
                # Store in session for persistence
                metadata = {
                    "chat_profile": chat_profile,
                    "current_phase": current_phase,
                    "phases": phases,
                    "settings": settings,
                }
                # Store metadata in user session - will be persisted by data layer
                cl.user_session.set("thread_metadata", metadata)
        except Exception as meta_err:
            print(f"Metadata save warning: {meta_err}")

    except Exception as e:
        print(f"[MAIN_HANDLER] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            if msg:
                msg.content = msg.content + f"\n\nI encountered an issue: {str(e)[:200]}"
                msg.actions = get_core_action_buttons(include_example=True)
                await msg.update()
        except Exception:
            # Last resort: send a NEW message so UI doesn't freeze
            try:
                await cl.Message(
                    content=f"Something went wrong: {str(e)[:200]}\n\nYour conversation is preserved. Please try again.",
                    actions=get_core_action_buttons(include_example=True)
                ).send()
            except Exception:
                pass  # Chainlit will recover on next user message


# === Audio Stream Handlers (Voice Assistant) ===
# Real-time audio processing with ElevenLabs voice responses

@cl.on_audio_start
async def on_audio_start():
    """
    Initialize TRUE real-time voice streaming.

    Opens Deepgram WebSocket immediately - audio streams as it arrives.
    When user stops speaking, LLM+TTS starts INSTANTLY (before on_audio_end).
    """
    import uuid

    print("🎤 [VOICE] Audio started - initializing real-time pipeline")

    # Initialize voice output track
    track_id = str(uuid.uuid4())
    cl.user_session.set("voice_track_id", track_id)
    cl.user_session.set("voice_enabled", True)
    cl.user_session.set("audio_chunks", [])  # Fallback buffer
    cl.user_session.set("audio_mime_type", "audio/pcm")
    cl.user_session.set("utterance_processed", False)

    # Try to open Deepgram WebSocket for TRUE real-time STT
    try:
        from utils.realtime_stt import is_deepgram_enabled, LiveSTTSession

        if is_deepgram_enabled():
            # Create callback that fires when user stops speaking
            async def on_utterance_end(transcript: str):
                """Called IMMEDIATELY when Deepgram detects silence."""
                if cl.user_session.get("utterance_processed"):
                    return  # Already processed

                cl.user_session.set("utterance_processed", True)
                print(f"🎤 [VOICE] Utterance ended, starting LLM immediately: '{transcript[:50]}...'")

                # Process transcript with LLM + TTS
                await process_voice_transcript(transcript, track_id)

            async def on_interim(partial_text: str):
                """Update UI with partial transcript as user speaks."""
                # Could update a live transcript message here
                pass

            # Create and start Deepgram session
            session = LiveSTTSession(
                on_utterance_end=on_utterance_end,
                on_interim=on_interim,
                utterance_end_ms=800,  # Fast detection
            )

            if await session.start():
                cl.user_session.set("stt_session", session)
                cl.user_session.set("use_realtime_stt", True)
                print(f"🎤 [VOICE] Deepgram WebSocket open - TRUE real-time enabled")
            else:
                cl.user_session.set("use_realtime_stt", False)
                print("🎤 [VOICE] Deepgram connection failed, using fallback")
        else:
            cl.user_session.set("use_realtime_stt", False)
            print("🎤 [VOICE] Deepgram not configured, using Gemini fallback")

    except ImportError as e:
        print(f"🎤 [VOICE] Import error: {e}")
        cl.user_session.set("use_realtime_stt", False)

    print(f"🎤 [VOICE] Track ID: {track_id[:8]}...")
    return True


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """
    Stream audio chunk IMMEDIATELY to Deepgram.

    No buffering - each chunk goes to Deepgram as it arrives.
    Deepgram transcribes in real-time while user speaks.
    """
    # Get active STT session
    stt_session = cl.user_session.get("stt_session")

    if stt_session:
        # TRUE REAL-TIME: Send directly to Deepgram (no batching!)
        await stt_session.send_audio(chunk.data)
    else:
        # Fallback: Collect chunks for batch processing
        audio_chunks = cl.user_session.get("audio_chunks", [])
        audio_chunks.append(chunk.data)
        cl.user_session.set("audio_chunks", audio_chunks)

        if len(audio_chunks) == 1:
            print(f"🎤 [VOICE] First chunk (fallback mode): {len(chunk.data)} bytes")

    # Track MIME type for fallback
    if chunk.mimeType:
        raw_mime = chunk.mimeType.lower()
        mime_mapping = {
            "pcm16": "audio/wav",
            "pcm": "audio/wav",
            "audio/pcm": "audio/wav",
            "audio/raw": "audio/wav",
            "audio/l16": "audio/wav",
            "webm": "audio/webm",
            "wav": "audio/wav",
            "mp3": "audio/mp3",
            "ogg": "audio/ogg",
        }
        gemini_mime = mime_mapping.get(raw_mime, raw_mime)
        if not gemini_mime.startswith("audio/"):
            gemini_mime = f"audio/{gemini_mime}"
        cl.user_session.set("audio_mime_type", gemini_mime)


async def process_voice_transcript(transcript: str, track_id: str):
    """
    Process voice transcript with LLM and stream response with TTS.

    Called immediately when Deepgram detects user stopped speaking.
    This is the core of the real-time voice pipeline.
    """
    if not transcript or not transcript.strip():
        return

    # Import voice streaming
    try:
        from utils.voice_streaming import (
            RealtimeVoiceStreamer,
            is_voice_enabled,
        )
        VOICE_AVAILABLE = True
    except ImportError:
        VOICE_AVAILABLE = False

    # Show what user said
    await cl.Message(content=f"**You said:** {transcript}").send()

    # Get conversation context
    bot = cl.user_session.get("bot", BOTS["lawrence"])
    history = cl.user_session.get("history", [])
    current_phase = cl.user_session.get("current_phase", 0)
    phases = cl.user_session.get("phases", [])
    settings = cl.user_session.get("settings", {})  # BUG FIX: Get settings for voice pipeline

    # Build contents for Gemini
    contents = []
    for msg_item in history:
        contents.append(types.Content(
            role=msg_item["role"],
            parts=[types.Part(text=msg_item["content"])]
        ))

    phase_context = ""
    if phases and current_phase < len(phases):
        phase_context = f"\n\n[CURRENT WORKSHOP PHASE: {phases[current_phase]['name']}]"

    # BUG FIX: Apply detail_instruction to voice responses (was missing)
    detail_level = settings.get("response_detail", 1)
    detail_instruction = ""
    if detail_level <= 3:
        detail_instruction = "\n[USER PREFERENCE: Be concise and brief in your response.]"
    elif detail_level >= 8:
        detail_instruction = "\n[USER PREFERENCE: Provide comprehensive, detailed explanations.]"

    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=transcript + phase_context + detail_instruction)]
    ))

    # Create response message
    msg = cl.Message(content="")
    await msg.send()

    response_text = ""

    # Try real-time voice streaming
    if VOICE_AVAILABLE and is_voice_enabled() and track_id:
        print(f"🔊 [VOICE] Starting real-time TTS streaming...")

        try:
            streamer = RealtimeVoiceStreamer()
            text_buffer = ""
            sentence_endings = {'.', '!', '?', '\n', ';', ':'}

            # Start Gemini stream
            response_stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=bot["system_prompt"],
                )
            )

            async def gemini_text_chunks():
                nonlocal response_text, text_buffer

                for chunk in response_stream:
                    if chunk.text:
                        response_text += chunk.text
                        text_buffer += chunk.text
                        await msg.stream_token(chunk.text)

                        # Send complete sentences to TTS
                        if any(end in text_buffer for end in sentence_endings) and len(text_buffer) > 15:
                            yield text_buffer
                            text_buffer = ""

                if text_buffer.strip():
                    yield text_buffer

            # Stream audio to browser
            async for _ in streamer.stream_text_to_browser(gemini_text_chunks(), track_id):
                pass

            print("🔊 [VOICE] Real-time streaming complete")

        except Exception as e:
            print(f"🔊 [VOICE] Streaming error: {e}")
            # Fall through to text-only

    # Fallback: Text only
    if not response_text:
        print("🔊 [VOICE] Using text-only fallback")
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=bot["system_prompt"],
            )
        )

        for chunk in response_stream:
            if chunk.text:
                response_text += chunk.text
                await msg.stream_token(chunk.text)

    await msg.update()

    # Update history
    if response_text:
        history.append({"role": "user", "content": transcript})
        history.append({"role": "model", "content": response_text})
        cl.user_session.set("history", history)

        # Sync context store + persist
        context_key = get_context_key()
        if context_key:
            bot_id = cl.user_session.get("bot_id", "lawrence")
            context_store[context_key] = {
                "bot_id": bot_id,
                "history": history.copy(),
            }
            asyncio.create_task(_persist_context_async(context_key))


def pcm16_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    """
    Convert raw PCM16 audio data to WAV format with proper headers.

    Chainlit 2.0+ sends audio as raw PCM16 at 24kHz.
    Gemini requires proper container format (WAV, WebM, etc.)

    Args:
        pcm_data: Raw PCM 16-bit audio bytes
        sample_rate: Sample rate in Hz (Chainlit default: 24000)
        channels: Number of audio channels (1 = mono)

    Returns:
        WAV file bytes with proper RIFF header
    """
    import struct

    # WAV file parameters
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm_data)
    file_size = 36 + data_size  # Header size (44) - 8 + data

    # Build WAV header
    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',           # ChunkID
        file_size,         # ChunkSize
        b'WAVE',           # Format
        b'fmt ',           # Subchunk1ID
        16,                # Subchunk1Size (PCM)
        1,                 # AudioFormat (1 = PCM)
        channels,          # NumChannels
        sample_rate,       # SampleRate
        byte_rate,         # ByteRate
        block_align,       # BlockAlign
        bits_per_sample,   # BitsPerSample
        b'data',           # Subchunk2ID
        data_size          # Subchunk2Size
    )

    return wav_header + pcm_data


@cl.on_audio_end
async def on_audio_end(elements: list = None):
    """
    Handle end of audio recording.

    For TRUE real-time: LLM+TTS was already triggered by UtteranceEnd callback.
    This just cleans up the Deepgram session.

    For fallback mode: Process the batched audio with Gemini STT.
    """
    print("🎤 [VOICE] Audio ended")

    # === 1. CLOSE DEEPGRAM SESSION ===
    stt_session = cl.user_session.get("stt_session")
    if stt_session:
        await stt_session.stop()
        cl.user_session.set("stt_session", None)
        print("🎤 [VOICE] Deepgram session closed")

    # === 2. CHECK IF ALREADY PROCESSED ===
    # If real-time STT triggered the callback, we're done
    if cl.user_session.get("utterance_processed"):
        print("🎤 [VOICE] Utterance already processed by real-time callback")
        cl.user_session.set("utterance_processed", False)  # Reset for next
        return

    # === 3. FALLBACK: Process batched audio with Gemini STT ===
    audio_chunks = cl.user_session.get("audio_chunks", [])
    if not audio_chunks:
        print("🎤 [VOICE] No audio chunks in fallback buffer")
        # Don't show error - might have been processed by real-time
        return

    audio_data = b"".join(audio_chunks)
    cl.user_session.set("audio_chunks", [])  # Clear buffer
    print(f"🎤 [VOICE] Fallback mode: {len(audio_chunks)} chunks, {len(audio_data)} bytes")

    if len(audio_data) < 1000:
        await cl.Message(content="⚠️ Audio too short. Please try again.").send()
        return

    mime_type = cl.user_session.get("audio_mime_type", "audio/webm")
    track_id = cl.user_session.get("voice_track_id")

    try:
        # Transcribe with Gemini (fallback)
        print("🎤 [VOICE] Transcribing with Gemini (fallback)...")

        # Convert PCM to WAV if needed
        gemini_audio = audio_data
        gemini_mime = mime_type

        if "wav" in mime_type or "pcm" in mime_type.lower():
            if audio_data[:4] != b'RIFF':
                gemini_audio = pcm16_to_wav(audio_data, sample_rate=24000)
                gemini_mime = "audio/wav"

        transcription_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=gemini_audio, mime_type=gemini_mime),
                        types.Part(text="Transcribe this audio exactly. Only output the transcription, nothing else.")
                    ]
                )
            ]
        )
        transcription = transcription_response.text.strip()

        if not transcription:
            await cl.Message(content="No speech detected.").send()
            return

        print(f"🎤 [VOICE] Gemini transcribed: '{transcription[:50]}...'")

        # Process with LLM + TTS
        await process_voice_transcript(transcription, track_id)

    except Exception as e:
        print(f"🎤 [VOICE] Fallback error: {e}")
        await cl.Message(content=f"Audio processing error: {str(e)[:100]}").send()


# =====================================================================
# DOMAIN SELECTION — CV Analysis, Research Analysis, Question Exploration
# =====================================================================

async def _gemini_json_call(prompt_text: str) -> dict:
    """Call Gemini and parse JSON response."""
    import re
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_text,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    text = response.text.strip()
    # Strip markdown fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


async def _get_graph_hints(keywords: list) -> str:
    """Get GraphRAG hints for domain keywords."""
    if not GRAPHRAG_ENABLED:
        return "No graph context available."
    try:
        from tools.graphrag_lite import light_context
        hints = []
        for kw in keywords[:5]:
            hint, _ = light_context(kw, context_type="auto")
            if hint:
                hints.append(hint)
        return "\n".join(hints) if hints else "No graph matches found."
    except Exception:
        return "Graph context unavailable."


async def _get_rag_context(query: str) -> str:
    """Get File Search RAG context."""
    if not FILE_SEARCH_ENABLED:
        return "No RAG context available."
    try:
        response = filesearch_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[FILE_SEARCH_STORE],
                    ),
                )],
                temperature=0.2,
            ),
        )
        return response.text[:2000] if response.text else "No RAG results."
    except Exception:
        return "RAG context unavailable."


async def _run_research_validation(domains: list, max_domains: int = 5) -> str:
    """Run Tavily research validation for top domains."""
    try:
        from tools.tavily_search import search_web
    except ImportError:
        return "Research validation unavailable (Tavily not configured)."

    results = []
    for domain in domains[:max_domains]:
        statement = domain.get("domain_statement", str(domain))
        try:
            r = search_web(f"{statement} research landscape challenges", search_depth="basic", max_results=3)
            results.append(f"**{statement}**: {r[:500] if isinstance(r, str) else str(r)[:500]}")
        except Exception as e:
            results.append(f"**{statement}**: Search failed - {str(e)[:100]}")
    return "\n\n".join(results) if results else "No research results."


_INPUT_TYPE_INDICATORS = {
    "published_paper": ["Abstract", "Introduction", "Methods", "Results", "Discussion", "References"],
    "research_proposal": ["Specific Aims", "Background", "Research Plan", "Budget", "Timeline"],
    "thesis_proposal": ["Problem Statement", "Literature Review", "Methodology", "Expected Contributions"],
    "patent_application": ["Claims", "Description", "Prior Art"],
    "literature_review": ["Search Strategy", "Inclusion Criteria", "Synthesis", "Themes"],
}


def _detect_document_type(text: str) -> str:
    """Auto-detect research document type from section headings."""
    text_upper = text[:5000].upper()
    best_type = "published_paper"
    best_score = 0
    for doc_type, indicators in _INPUT_TYPE_INDICATORS.items():
        score = sum(1 for ind in indicators if ind.upper() in text_upper)
        if score > best_score:
            best_score = score
            best_type = doc_type
    return best_type


@cl.action_callback("analyze_cv")
async def on_analyze_cv(action: cl.Action):
    """CV-based domain discovery pipeline."""
    # Phase 1: File Upload
    files = await cl.AskFileMessage(
        content="Upload your CV or resume (PDF, DOCX, or TXT).",
        accept=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
        max_size_mb=10,
    ).send()

    if not files:
        await cl.Message(content="No file uploaded. You can try again by clicking **Analyze CV**.").send()
        return

    file = files[0]
    status_msg = cl.Message(content="")
    await status_msg.send()

    try:
        # Extract text
        async with cl.Step(name="Extracting CV", type="tool") as step:
            step.input = f"Processing {file.name}"
            from utils.file_processor import process_uploaded_file
            content, metadata = process_uploaded_file(file.path, file.name)
            if not content or len(content.strip()) < 50:
                await cl.Message(content="Could not extract sufficient text from the file. Please try a different format.").send()
                return
            step.output = f"Extracted {len(content)} characters"

        # Phase 2: CV Extraction
        async with cl.Step(name="Analyzing CV Structure", type="llm") as step:
            step.input = "Extracting professional experience, education, skills, and network indicators"
            extraction = await _gemini_json_call(
                CV_EXTRACTION_PROMPT.format(cv_text=content[:15000])
            )
            step.output = f"Found {len(extraction.get('professional_experience', []))} roles, {len(extraction.get('education', []))} degrees"
            cl.user_session.set("cv_extraction", extraction)

        # Phase 3: Domain Generation
        async with cl.Step(name="Generating Domain Candidates", type="llm") as step:
            # Get graph and RAG context
            keywords = extraction.get("skills", {}).get("technical", [])[:5] + \
                       [e.get("field", "") for e in extraction.get("education", [])]
            graph_hints = await _get_graph_hints(keywords)
            rag_context = await _get_rag_context("domain selection methodology PWS criteria")

            step.input = f"Using {len(keywords)} keywords for context enrichment"
            domains_data = await _gemini_json_call(
                DOMAIN_GENERATION_PROMPT.format(
                    cv_extraction=json.dumps(extraction, indent=2),
                    graph_hints=graph_hints,
                    rag_context=rag_context,
                )
            )
            domains = domains_data.get("domains", [])
            step.output = f"Generated {len(domains)} domain candidates"

        # Phase 4: Research Validation
        async with cl.Step(name="Validating with Research", type="tool") as step:
            step.input = f"Researching top {min(5, len(domains))} domains"
            research_results = await _run_research_validation(domains)
            step.output = "Research validation complete"

        # Phase 5: Scoring
        async with cl.Step(name="Scoring Domains", type="llm") as step:
            step.input = "Scoring Interest, Knowledge, Access for each domain"
            scored_data = await _gemini_json_call(
                DOMAIN_SCORING_PROMPT.format(
                    cv_extraction=json.dumps(extraction, indent=2),
                    domain_candidates=json.dumps(domains, indent=2),
                    research_results=research_results,
                )
            )
            scored = scored_data.get("scored_domains", [])
            step.output = f"Scored {len(scored)} domains"

        # Output results
        output_parts = ["## Domain Discovery Results\n"]
        output_parts.append(f"**Source:** {file.name}\n")
        output_parts.append("### Scoring Matrix\n")
        output_parts.append("| # | Domain | Interest | Knowledge | Access | Total |")
        output_parts.append("|---|--------|----------|-----------|--------|-------|")
        for i, d in enumerate(scored, 1):
            interest = d.get("interest", {}).get("score", "?")
            knowledge = d.get("knowledge", {}).get("score", "?")
            access = d.get("access", {}).get("score", "?")
            total = d.get("composite_score", "?")
            output_parts.append(f"| {i} | {d.get('domain_statement', 'N/A')} | {interest} | {knowledge} | {access} | {total} |")

        output_parts.append("\n### Top Domain Details\n")
        for i, d in enumerate(scored[:3], 1):
            output_parts.append(f"**{i}. {d.get('domain_statement', 'N/A')}**")
            output_parts.append(f"- Interest: {d.get('interest', {}).get('score', '?')}/5 — {d.get('interest', {}).get('rationale', '')}")
            output_parts.append(f"- Knowledge: {d.get('knowledge', {}).get('score', '?')}/5 — {d.get('knowledge', {}).get('rationale', '')}")
            output_parts.append(f"- Access: {d.get('access', {}).get('score', '?')}/5 — {d.get('access', {}).get('rationale', '')}")
            next_steps = d.get("recommended_next_steps", [])
            if next_steps:
                output_parts.append(f"- Next steps: {'; '.join(next_steps)}")
            output_parts.append("")

        output_parts.append("\n---\n*These are starting points. Let's evaluate them together using the full Domain Selection methodology. Which domain surprises you? Which did you dismiss too quickly?*")

        # Save to Supabase
        try:
            session_id = cl.user_session.get("id", "unknown")
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                from supabase import create_client
                sb = create_client(supabase_url, supabase_key)
                sb.table("cv_analyses").insert({
                    "session_id": str(session_id),
                    "cv_extraction": json.dumps(extraction),
                    "scored_domains": json.dumps(scored),
                    "research_results": research_results,
                }).execute()
                print(f"[DOMAIN] CV analysis saved for session {session_id}")
        except Exception as e:
            print(f"[DOMAIN] Supabase save failed (non-critical): {e}")

        await status_msg.remove()
        result_msg = cl.Message(content="\n".join(output_parts))

        # Add deep dive buttons for top domains
        for i, d in enumerate(scored[:3]):
            result_msg.actions.append(cl.Action(
                name="domain_deep_dive",
                payload={"domain": d.get("domain_statement", ""), "index": i},
                label=f"Deep Dive: Domain {i+1}",
                description=f"Research {d.get('domain_statement', '')[:50]} in depth",
            ))

        await result_msg.send()

    except Exception as e:
        await status_msg.remove()
        await cl.Message(content=f"CV analysis encountered an error: {str(e)[:200]}. Please try again.").send()
        print(f"[DOMAIN] CV analysis error: {e}")


@cl.action_callback("analyze_research")
async def on_analyze_research(action: cl.Action):
    """Research paper domain discovery pipeline."""
    files = await cl.AskFileMessage(
        content="Upload a research document (paper, patent, proposal, or literature review).",
        accept=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
        max_size_mb=10,
    ).send()

    if not files:
        await cl.Message(content="No file uploaded. You can try again by clicking **Analyze Research**.").send()
        return

    file = files[0]
    await _run_research_pipeline(file.path, file.name)


@cl.action_callback("explore_question")
async def on_explore_question(action: cl.Action):
    """Research question domain discovery — no document needed."""
    response = await cl.AskUserMessage(
        content="Enter your research question or topic. I'll identify potential innovation domains from it.",
    ).send()

    if not response:
        return

    user_input = response.get("output", "") if isinstance(response, dict) else str(response)

    status_msg = cl.Message(content="Analyzing research question...")
    await status_msg.send()

    try:
        # Expand question into research context
        async with cl.Step(name="Expanding Research Question", type="llm") as step:
            step.input = user_input[:200]
            extraction = await _gemini_json_call(
                RESEARCH_QUESTION_EXPANSION_PROMPT.format(user_input=user_input)
            )
            step.output = f"Expanded into {extraction.get('document_metadata', {}).get('field', 'unknown')} field"

        # Continue with shared pipeline
        await _run_research_pipeline_from_extraction(extraction, f"Question: {user_input[:80]}", status_msg)

    except Exception as e:
        await status_msg.remove()
        await cl.Message(content=f"Question analysis error: {str(e)[:200]}").send()
        print(f"[DOMAIN] Question analysis error: {e}")


async def _run_research_pipeline(file_path: str, file_name: str):
    """Shared research pipeline for document-based analysis."""
    status_msg = cl.Message(content="")
    await status_msg.send()

    try:
        # Extract text
        async with cl.Step(name="Extracting Document", type="tool") as step:
            step.input = f"Processing {file_name}"
            from utils.file_processor import process_uploaded_file
            content, metadata = process_uploaded_file(file_path, file_name)
            if not content or len(content.strip()) < 50:
                await cl.Message(content="Could not extract sufficient text. Please try a different format.").send()
                return
            step.output = f"Extracted {len(content)} characters"

        # Detect type and extract
        detected_type = _detect_document_type(content)

        async with cl.Step(name="Analyzing Research", type="llm") as step:
            step.input = f"Detected type: {detected_type}"
            extraction = await _gemini_json_call(
                RESEARCH_EXTRACTION_PROMPT.format(
                    detected_type=detected_type,
                    document_text=content[:15000],
                )
            )
            step.output = f"Extracted research core from {detected_type}"

        await _run_research_pipeline_from_extraction(extraction, file_name, status_msg)

    except Exception as e:
        await status_msg.remove()
        await cl.Message(content=f"Research analysis error: {str(e)[:200]}").send()
        print(f"[DOMAIN] Research analysis error: {e}")


async def _run_research_pipeline_from_extraction(extraction: dict, source_name: str, status_msg):
    """Continue research pipeline from extraction data."""
    try:
        # Domain generation
        async with cl.Step(name="Generating Domains (5 Lenses)", type="llm") as step:
            keywords = extraction.get("domain_seeds", {}).get("keywords", [])
            graph_hints = await _get_graph_hints(keywords)
            rag_context = await _get_rag_context("domain selection research translation innovation")

            step.input = f"Applying gap, application, intersection, frontier, translation lenses"
            domains_data = await _gemini_json_call(
                DOMAIN_GENERATION_FROM_RESEARCH_PROMPT.format(
                    research_extraction=json.dumps(extraction, indent=2),
                    graph_hints=graph_hints,
                    rag_context=rag_context,
                )
            )
            domains = domains_data.get("domains", [])
            step.output = f"Generated {len(domains)} domains across lenses"

        # Research validation
        async with cl.Step(name="Validating with Research", type="tool") as step:
            step.input = f"Researching top {min(5, len(domains))} domains"
            research_results = await _run_research_validation(domains)
            step.output = "Validation complete"

        # Scoring
        async with cl.Step(name="Scoring Domains", type="llm") as step:
            step.input = "Scoring Research Maturity, Translation Readiness, Competitive Position"
            scored_data = await _gemini_json_call(
                RESEARCH_DOMAIN_SCORING_PROMPT.format(
                    research_extraction=json.dumps(extraction, indent=2),
                    domain_candidates=json.dumps(domains, indent=2),
                    research_results=research_results,
                )
            )
            scored = scored_data.get("scored_domains", [])
            step.output = f"Scored {len(scored)} domains"

        # Translation
        async with cl.Step(name="Translating to Practitioner Language", type="llm") as step:
            step.input = "Converting academic domains to actionable opportunities"
            translation_data = await _gemini_json_call(
                RESEARCH_TRANSLATION_PROMPT.format(
                    scored_domains=json.dumps(scored[:5], indent=2),
                    research_extraction=json.dumps(extraction, indent=2),
                )
            )
            translations = translation_data.get("translations", [])
            step.output = f"Translated {len(translations)} domains"

        # Output
        output_parts = ["## Research-Derived Domain Opportunities\n"]
        output_parts.append(f"**Source:** {source_name}\n")

        output_parts.append("### Scoring Matrix\n")
        output_parts.append("| # | Domain | Research | Translation | Competitive | Composite | Horizon |")
        output_parts.append("|---|--------|----------|-------------|-------------|-----------|---------|")
        for i, d in enumerate(scored, 1):
            rm = d.get("research_maturity", {}).get("score", "?")
            tr = d.get("translation_readiness", {}).get("score", "?")
            cp = d.get("competitive_position", {}).get("score", "?")
            cs = d.get("composite_score", "?")
            th = d.get("time_horizon", "?")
            output_parts.append(f"| {i} | {d.get('domain_statement', 'N/A')[:60]} | {rm} | {tr} | {cp} | {cs} | {th} |")

        if translations:
            output_parts.append("\n### Practitioner Translations\n")
            for i, t in enumerate(translations[:3], 1):
                output_parts.append(f"**{i}. {t.get('plain_language', t.get('domain_statement', 'N/A'))}**")
                pf = t.get("problem_frame", {})
                if pf:
                    output_parts.append(f"- **Who has this problem:** {pf.get('who_has_problem', 'N/A')}")
                    output_parts.append(f"- **Current pain:** {pf.get('current_pain', 'N/A')}")
                    output_parts.append(f"- **Solving enables:** {pf.get('solving_enables', 'N/A')}")
                ep = t.get("entry_points", {})
                if ep:
                    output_parts.append(f"- **Startup path:** {ep.get('startup', 'N/A')}")
                rec = t.get("recommended_pws_tool", "")
                if rec:
                    output_parts.append(f"- **Recommended next tool:** {rec} — {t.get('recommended_pws_reason', '')}")
                output_parts.append("")

        output_parts.append("\n---\n*These domains emerge from the research frontier. Which ones align with your capabilities? Let's evaluate them using Interest, Knowledge, and Access.*")

        # Save to Supabase
        try:
            session_id = cl.user_session.get("id", "unknown")
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                from supabase import create_client
                sb = create_client(supabase_url, supabase_key)
                sb.table("cv_analyses").insert({
                    "session_id": str(session_id),
                    "cv_extraction": json.dumps({"type": "research_analysis", "extraction": extraction}),
                    "scored_domains": json.dumps(scored),
                    "research_results": research_results,
                }).execute()
                print(f"[DOMAIN] Research analysis saved for session {session_id}")
        except Exception as e:
            print(f"[DOMAIN] Supabase save failed (non-critical): {e}")

        await status_msg.remove()
        result_msg = cl.Message(content="\n".join(output_parts))

        for i, d in enumerate(scored[:3]):
            result_msg.actions.append(cl.Action(
                name="domain_deep_dive",
                payload={"domain": d.get("domain_statement", ""), "index": i},
                label=f"Deep Dive: Domain {i+1}",
                description=f"Research {d.get('domain_statement', '')[:50]} in depth",
            ))

        await result_msg.send()

    except Exception as e:
        await status_msg.remove()
        await cl.Message(content=f"Research pipeline error: {str(e)[:200]}").send()
        print(f"[DOMAIN] Research pipeline error: {e}")


@cl.action_callback("domain_deep_dive")
async def on_domain_deep_dive(action: cl.Action):
    """Deep dive research into a specific domain."""
    domain = action.payload.get("domain", "")
    if not domain:
        await cl.Message(content="No domain specified for deep dive.").send()
        return

    status_msg = cl.Message(content=f"Researching **{domain}** in depth...")
    await status_msg.send()

    try:
        from tools.tavily_search import search_web

        async with cl.Step(name=f"Deep Dive: {domain[:50]}", type="tool") as step:
            step.input = f"Running 5 targeted searches for: {domain}"

            queries = [
                f"{domain} comprehensive market analysis",
                f"{domain} key stakeholders and decision makers",
                f"{domain} emerging technologies and innovations",
                f"{domain} regulatory landscape and policy",
                f"{domain} unmet needs and pain points",
                f"{domain} investment and funding trends",
                f"{domain} academic research and publications",
            ]

            all_results = []
            for q in queries:
                try:
                    r = search_web(q, search_depth="basic", max_results=3)
                    all_results.append(f"**Query:** {q}\n{r[:400] if isinstance(r, str) else str(r)[:400]}")
                except Exception:
                    all_results.append(f"**Query:** {q}\n(search failed)")

            step.output = f"Completed {len(queries)} searches"

        # Synthesize via Gemini
        async with cl.Step(name="Synthesizing Research", type="llm") as step:
            research_text = "\n\n".join(all_results)
            synthesis_prompt = f"""Synthesize the following research about the domain "{domain}" into actionable insights for someone looking for Problems Worth Solving.

RESEARCH:
{research_text[:10000]}

Structure your response as:
1. Domain Overview (2-3 sentences)
2. Key Stakeholders & Their Pain Points
3. Emerging Trends Creating New Problems
4. Gaps & Underserved Needs
5. Recommended PWS Phase 1 Starting Points (specific problem hypotheses to investigate)"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=synthesis_prompt,
                config=types.GenerateContentConfig(temperature=0.3),
            )
            step.output = "Synthesis complete"

        await status_msg.remove()
        await cl.Message(content=f"## Deep Dive: {domain}\n\n{response.text}").send()

    except Exception as e:
        await status_msg.remove()
        await cl.Message(content=f"Deep dive error: {str(e)[:200]}").send()


# ==============================================================================
# GRADING AGENT ACTION CALLBACKS
# ==============================================================================

@cl.action_callback("grade_student_work")
async def on_grade_student_work(action: cl.Action):
    """Run the full grading pipeline on student work."""
    files = await cl.AskFileMessage(
        content="Upload student work to grade (PDF, DOCX, or TXT).\n\nI'll run the complete grading pipeline including bias detection, domain analysis, framework validation, and evidence quality assessment.",
        accept=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
        max_size_mb=20,
    ).send()

    if not files:
        await cl.Message(content="No file uploaded. You can try again by clicking **Grade Student Work**.").send()
        return

    file = files[0]
    await _run_grading_pipeline(file.path, file.name)


@cl.action_callback("quick_grade")
async def on_quick_grade(action: cl.Action):
    """Run quick grading without the full pipeline."""
    files = await cl.AskFileMessage(
        content="Upload student work for quick grading (PDF, DOCX, or TXT).\n\nThis provides a quick assessment without the full bias detection and quality validation pipeline.",
        accept=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
        max_size_mb=20,
    ).send()

    if not files:
        await cl.Message(content="No file uploaded.").send()
        return

    file = files[0]
    await _run_quick_grading(file.path, file.name)


@cl.action_callback("discuss_grade")
async def on_discuss_grade(action: cl.Action):
    """Switch to Lawrence to discuss the grading results - as if Lawrence did the grading."""
    # Get the grading context
    grading_results = cl.user_session.get("last_grading_results", {})
    grading_report = cl.user_session.get("last_grading_report", "")
    graded_content = cl.user_session.get("last_graded_content", "")
    assessment_state = cl.user_session.get("last_assessment_state", {})
    original_bot = cl.user_session.get("bot_id", "grading")

    if not grading_results:
        await cl.Message(content="No recent grading results found. Please grade a submission first.").send()
        return

    # Switch to Lawrence
    cl.user_session.set("bot_id", "lawrence")
    cl.user_session.set("bot", BOTS["lawrence"])

    # Extract scores from assessment state if available
    grade = grading_results.get("letter_grade", "N/A")
    score = grading_results.get("final_score", 0)

    # Try to extract more detailed info from the report
    verdict = "See report for details"
    limiting_factor = "Review detailed breakdown"
    opportunities_saved = "Check Bank of Opportunities"

    # Build comprehensive context for Lawrence to act as the grader
    discussion_context = f"""## YOU ARE THE GRADER - DISCUSSION MODE

You (Lawrence) have just completed grading this student's work. You have full knowledge of everything in this assessment. Respond as if YOU personally reviewed every detail.

### Your Grading Summary
- **Final Grade:** {grade} ({score}/100 if known)
- **Grading Bot Used:** {original_bot}
- **Modules Completed:** {', '.join(grading_results.get('modules_completed', ['Assessment Complete']))}
- **Evidence Items Collected:** {grading_results.get('evidence_count', 'Multiple')}

### Full Assessment Report
{grading_report[:4000] if grading_report else 'Not available'}

### Student Work (First 2000 chars)
{graded_content[:2000] if graded_content else 'Not available'}...

### Your Role in This Discussion

You ARE the grader. This is not a handoff - you did this grading. Respond accordingly:

1. **Own the Assessment** - Say "I found..." not "The system found..."
2. **Explain Reasoning** - When asked WHY a score, explain based on evidence quality
3. **Reference Their Work** - Point to specific parts of their submission
4. **Be Direct but Constructive** - Help them improve, don't just defend scores
5. **Acknowledge Valid Arguments** - If they present new evidence, consider it

### Common Discussion Points

If they ask "Why did I get X on Problem Reality?":
- Explain what evidence was present vs. missing
- Distinguish validated problems from assumptions
- Reference specific quotes or data they should have had

If they disagree with Framework Integration score:
- Point out which frameworks were used properly vs. superficially
- Reference Neo4j findings on missed frameworks
- Suggest how to better integrate tools

If they want to argue for a higher grade:
- Ask what additional evidence they can provide
- Be open to valid new arguments
- But don't inflate grades without substance

Remember: You read their work, you used the tools, you made these judgments. Own it."""

    # Add to history as system context
    history = cl.user_session.get("history", [])
    history.append({"role": "user", "content": f"[SYSTEM CONTEXT: You just graded this student's work. Grade: {grade}. They want to discuss it with you. Act as the grader who personally reviewed everything.]"})
    cl.user_session.set("history", history)
    cl.user_session.set("grading_discussion_context", discussion_context)

    await cl.Message(
        content=f"""**💬 Grade Discussion Mode**

You received: **{grade}**

I'm Lawrence, and I personally graded your submission. I reviewed your work using our full tool stack - Neo4j for framework validation, FileSearch for course materials, and research validation.

I'm here to discuss your grade. You can:
- Ask me why you received specific scores on any component
- Challenge my assessment with new evidence or arguments
- Get clarification on any feedback
- Understand specifically how to improve

I'll explain my reasoning based on what I found in your work.

What would you like to discuss about your grade?""",
        actions=[
            cl.Action(name="show_full_report", payload={}, label="📄 Show Full Report"),
            cl.Action(name="grade_student_work", payload={}, label="📝 Grade New Submission"),
        ]
    ).send()


@cl.action_callback("show_full_report")
async def on_show_full_report(action: cl.Action):
    """Show the full grading report."""
    report = cl.user_session.get("last_grading_report", "")
    if report:
        await cl.Message(content=report).send()
    else:
        await cl.Message(content="No grading report available.").send()


@cl.action_callback("view_full_report")
async def on_view_full_report(action: cl.Action):
    """View the full grading report with download option."""
    report = cl.user_session.get("last_grading_report", "")
    if report:
        elements = []
        if UI_ELEMENTS_ENABLED:
            from datetime import datetime
            report_file = create_report_download(
                content=report,
                filename=f"assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.md"
            )
            elements.append(report_file)
        await cl.Message(content=report, elements=elements).send()
    else:
        await cl.Message(content="No grading report available.").send()


@cl.action_callback("view_evidence")
async def on_view_evidence(action: cl.Action):
    """View the evidence chain from the assessment."""
    assessment_state = cl.user_session.get("last_assessment_state", {})
    evidence_trail = assessment_state.get("evidence_trail", [])

    if not evidence_trail:
        await cl.Message(content="No evidence chain available.").send()
        return

    elements = []
    if UI_ELEMENTS_ENABLED:
        evidence_text = create_evidence_display(evidence_trail[:30])
        elements.append(evidence_text)

    # Group evidence by source
    by_source = {}
    for ev in evidence_trail:
        source = ev.get("source_type", ev.get("tag_type", "unknown")).split("_")[0]
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(ev)

    summary = "## Evidence Chain\n\n"
    for source, items in by_source.items():
        summary += f"### {source.upper()} ({len(items)} items)\n"
        for item in items[:5]:
            content = item.get("content", "")[:150]
            tag = item.get("tag_type", "")
            summary += f"- **{tag}**: {content}...\n"
        if len(items) > 5:
            summary += f"  *...and {len(items) - 5} more*\n"
        summary += "\n"

    await cl.Message(content=summary, elements=elements).send()


@cl.action_callback("discuss_component")
async def on_discuss_component(action: cl.Action):
    """Discuss a specific grade component with Lawrence."""
    component = action.payload.get("component", "this score")
    score = action.payload.get("score", "")

    # Switch to Lawrence if not already
    current_bot = cl.user_session.get("bot_id", "lawrence")
    if current_bot != "lawrence":
        cl.user_session.set("bot_id", "lawrence")
        cl.user_session.set("bot", BOTS["lawrence"])

    grading_report = cl.user_session.get("last_grading_report", "")

    # Add context to history
    history = cl.user_session.get("history", [])
    history.append({
        "role": "user",
        "content": f"[SYSTEM: The student wants to discuss their {component} score ({score}/10). You are the grader who assigned this score. Explain your reasoning based on the evidence you found.]"
    })
    cl.user_session.set("history", history)

    score_text = f" ({score}/10)" if score else ""

    await cl.Message(
        content=f"""**Discussing: {component}{score_text}**

I assigned this score based on the evidence I found in your submission. Let me explain my reasoning.

What specifically would you like to understand about this component?

- Why did you score me here?
- What evidence was I missing?
- How can I improve this score?""",
        actions=[
            cl.Action(name="show_full_report", payload={}, label="📄 See Full Report"),
        ]
    ).send()


@cl.action_callback("remove_opportunity")
async def on_remove_opportunity(action: cl.Action):
    """Remove an opportunity from the bank."""
    opp_id = action.payload.get("id", "")
    title = action.payload.get("title", "opportunity")

    try:
        from tools.opportunity_bank import remove_opportunity
        session_id = str(cl.user_session.get("id", "anonymous"))
        success = await remove_opportunity(opp_id, session_id)

        if success:
            await cl.Message(content=f"Removed **{title}** from your opportunity bank.").send()
        else:
            await cl.Message(content=f"Could not remove opportunity. It may have already been removed.").send()
    except Exception as e:
        await cl.Message(content=f"Error removing opportunity: {str(e)[:100]}").send()


@cl.action_callback("view_opportunities")
async def on_view_opportunities(action: cl.Action):
    """Display all saved opportunities in the Opportunity Bank."""
    try:
        from tools.opportunity_bank import get_opportunities_from_table, get_opportunity_stats

        session_id = str(cl.user_session.get("id", "anonymous"))
        user_id = session_id

        # Get opportunities for this user
        opportunities = await get_opportunities_from_table(created_by=user_id, limit=20)

        if not opportunities:
            await cl.Message(
                content="🏦 **Your Opportunity Bank is empty.**\n\nOpportunities are automatically extracted when you:\n- Work through workshops\n- Upload documents for grading\n- Discuss problems worth solving\n\nKeep exploring and your bank will grow!",
                actions=[
                    cl.Action(name="switch_to_tta", payload={}, label="🔮 Try TTA Workshop"),
                ]
            ).send()
            return

        # Get stats
        stats = await get_opportunity_stats()

        # Build summary message
        summary = f"""🏦 **Your Opportunity Bank**

**{len(opportunities)} opportunities saved** | Total in system: {stats.get('total_opportunities', 'N/A')}

Click on any opportunity card to explore it further:
"""
        await cl.Message(content=summary).send()

        # Display each opportunity as OpportunityCard
        for opp in opportunities[:10]:  # Limit to 10 to avoid overload
            try:
                card = cl.CustomElement(
                    name="OpportunityCard",
                    props={
                        "id": opp.get("id", ""),
                        "title": opp.get("name", "Untitled Opportunity"),
                        "description": opp.get("description", "")[:200],
                        "domain": opp.get("domain", "General"),
                        "score": opp.get("relevance_score", 0.5),
                        "tags": opp.get("tags", [])[:5],
                        "createdAt": opp.get("created_at", ""),
                    },
                    display="inline"
                )
                await cl.Message(
                    content="",
                    elements=[card],
                    actions=[
                        cl.Action(
                            name="explore_opportunity",
                            payload={"id": opp.get("id"), "title": opp.get("name")},
                            label="🔍 Explore"
                        ),
                        cl.Action(
                            name="remove_opportunity",
                            payload={"id": opp.get("id"), "title": opp.get("name")},
                            label="🗑️ Remove"
                        ),
                    ]
                ).send()
            except Exception as card_err:
                # Fallback to simple text if card fails
                await cl.Message(
                    content=f"**{opp.get('name', 'Opportunity')}**\n{opp.get('description', '')[:150]}...\n*Domain: {opp.get('domain', 'General')}*",
                    actions=[
                        cl.Action(
                            name="explore_opportunity",
                            payload={"id": opp.get("id"), "title": opp.get("name")},
                            label="🔍 Explore"
                        ),
                    ]
                ).send()

    except Exception as e:
        await cl.Message(content=f"Error loading opportunities: {str(e)[:100]}").send()


@cl.action_callback("explore_opportunity")
async def on_explore_opportunity(action: cl.Action):
    """Explore a specific opportunity - continue the conversation about it."""
    opp_id = action.payload.get("id", "")
    title = action.payload.get("title", "this opportunity")

    try:
        from tools.opportunity_bank import get_opportunities_from_table

        # Fetch the full opportunity details
        session_id = str(cl.user_session.get("id", "anonymous"))
        opportunities = await get_opportunities_from_table(created_by=session_id, limit=50)

        # Find the specific opportunity
        opportunity = None
        for opp in opportunities:
            if opp.get("id") == opp_id:
                opportunity = opp
                break

        if not opportunity:
            await cl.Message(content=f"Could not find opportunity '{title}'. It may have been removed.").send()
            return

        # Build exploration context
        exploration_prompt = f"""🔍 **Let's explore: {opportunity.get('name', title)}**

**Description:** {opportunity.get('description', 'No description')}

**Domain:** {opportunity.get('domain', 'General')}
**Problem Statement:** {opportunity.get('problem_statement', 'Not specified')}

**Tags:** {', '.join(opportunity.get('tags', [])[:5]) or 'None'}

---

I'll help you dig deeper into this opportunity. We can:
- Validate the problem exists (Camera Test)
- Explore who has this problem
- Research the market size
- Apply PWS frameworks (TTA, JTBD, etc.)

**What aspect would you like to explore first?**"""

        await cl.Message(
            content=exploration_prompt,
            actions=[
                cl.Action(name="deep_research", payload={"query": f"market research {opportunity.get('domain', '')} {opportunity.get('name', '')}"}, label="🔍 Research This"),
                cl.Action(name="switch_to_redteam", payload={}, label="😈 Red Team It"),
                cl.Action(name="switch_to_jtbd", payload={}, label="🎯 JTBD Analysis"),
            ]
        ).send()

        # Store in session for follow-up context
        cl.user_session.set("exploring_opportunity", opportunity)

    except Exception as e:
        await cl.Message(content=f"Error exploring opportunity: {str(e)[:100]}").send()


async def _run_grading_pipeline(file_path: str, file_name: str):
    """Run the complete grading pipeline."""
    status_msg = cl.Message(content="Starting grading pipeline...")
    await status_msg.send()

    try:
        # Extract text from document
        async with cl.Step(name="Extracting Document", type="tool") as step:
            step.input = f"Processing {file_name}"
            from utils.file_processor import process_uploaded_file
            content, metadata = process_uploaded_file(file_path, file_name)
            if not content or len(content.strip()) < 100:
                await cl.Message(content="Could not extract sufficient text from the file. Please try a different format.").send()
                return
            step.output = f"Extracted {len(content)} characters"

        # Import grading workflow
        from tools.grading_workflow import run_grading_pipeline

        # Update status
        await status_msg.stream_token("\n\nRunning full grading pipeline...")

        # Phase 1: Bias Detection
        async with cl.Step(name="Phase 1: Bias Detection (MANDATORY)", type="llm") as step:
            step.input = "Detecting 7 critical cognitive biases"

        # Run the full pipeline
        report, results = await run_grading_pipeline(
            student_work=content,
            student_id=str(cl.user_session.get("id", "anonymous")),
            document_id=file_name,
        )

        # Display results
        await status_msg.remove()

        # Check if bias detection blocked the grading
        if not results.get("phases", {}).get("bias_detection", {}).get("can_proceed", True):
            await cl.Message(content=report).send()
            return

        # Display the full report
        final_msg = cl.Message(content=report)
        await final_msg.send()

        # Store results in session for follow-up
        cl.user_session.set("last_grading_results", results)

        # Add follow-up actions
        await cl.Message(
            content="Grading complete. What would you like to do next?",
            actions=[
                cl.Action(name="export_grading_json", payload={"action": "export"}, label="Export JSON"),
                cl.Action(name="explain_grade", payload={"action": "explain"}, label="Explain This Grade"),
            ]
        ).send()

    except Exception as e:
        await status_msg.remove()
        await cl.Message(content=f"Grading pipeline error: {str(e)[:300]}").send()
        print(f"[GRADING] Pipeline error: {e}")


async def _run_quick_grading(file_path: str, file_name: str):
    """Run quick grading without the full pipeline."""
    status_msg = cl.Message(content="Running quick grade...")
    await status_msg.send()

    try:
        # Extract text
        from utils.file_processor import process_uploaded_file
        content, metadata = process_uploaded_file(file_path, file_name)
        if not content or len(content.strip()) < 100:
            await cl.Message(content="Could not extract sufficient text.").send()
            return

        # Import quick grade
        from tools.grading_workflow import quick_grade

        # Run quick grade
        verdict, score, letter = await quick_grade(content)

        await status_msg.remove()

        # Display results
        result_msg = f"""## Quick Grade: {file_name}

### GRADE: **{letter}** ({score:.1f}/100)

**Verdict:** {verdict}

---

*This is a quick assessment. For a full evaluation with bias detection, domain analysis, and framework validation, use the **Full Grade** option.*
"""
        await cl.Message(
            content=result_msg,
            actions=[
                cl.Action(name="grade_student_work", payload={}, label="Run Full Grade"),
            ]
        ).send()

    except Exception as e:
        await status_msg.remove()
        await cl.Message(content=f"Quick grading error: {str(e)[:200]}").send()


@cl.action_callback("export_grading_json")
async def on_export_grading_json(action: cl.Action):
    """Export grading results as JSON."""
    results = cl.user_session.get("last_grading_results")
    if not results:
        await cl.Message(content="No grading results available to export.").send()
        return

    import json
    json_output = json.dumps(results, indent=2, default=str)

    # Create downloadable file
    await cl.Message(
        content=f"**Grading Results JSON:**\n```json\n{json_output[:3000]}...\n```\n\n*Full JSON is available in the session data.*"
    ).send()


@cl.action_callback("explain_grade")
async def on_explain_grade(action: cl.Action):
    """Explain the grading rationale in more detail."""
    results = cl.user_session.get("last_grading_results")
    if not results:
        await cl.Message(content="No grading results available to explain.").send()
        return

    scores = results.get("scores", {})
    phases = results.get("phases", {})

    explanation = f"""## Grade Explanation

### Why This Grade?

The grade reflects:

**Problem Reality (35% weight):**
- Students must demonstrate that problems are REAL, not assumed
- Evidence quality matters more than quantity
- Direct user quotes/observations score higher than assumptions

**Problem Discovery (25% weight):**
- How many real problems were identified?
- What was the validation rate?
- Did they explore different problem categories?

**Framework Integration (20% weight):**
- Were PWS frameworks used correctly?
- Which tools were missing?
- How well integrated was the methodology?

**Mindrian Thinking (10% weight):**
- Did they find hidden connections?
- Did they leverage the knowledge graph?

**Can We Win + Is it Worth It (10% combined):**
- Basic capability and market sizing checks

---

**Key Findings from This Assessment:**
{json.dumps(phases.get('problem_extraction', {}), indent=2, default=str)[:1500]}

---

*Want to discuss specific aspects of this grade?*
"""
    await cl.Message(content=explanation).send()


# =============================================================================
# LangGraph Pipeline Action Callbacks
# =============================================================================

@cl.action_callback("run_bono_analysis")
async def on_run_bono_analysis(action: cl.Action):
    """Run BONO Innovation pipeline (Six Thinking Hats + Lateral Thinking)."""
    if not LANGGRAPH_PIPELINES_ENABLED:
        await cl.Message(content="BONO pipeline not available. Please check system configuration.").send()
        return

    history = cl.user_session.get("history", [])
    session_id = str(cl.user_session.get("id", "default"))

    # Extract problem from recent conversation
    recent_context = " ".join([m.get("content", "") for m in history[-6:]])[-2000:]

    if len(recent_context.strip()) < 20:
        await cl.Message(content="Please describe a problem or challenge first, then run the Six Hats analysis.").send()
        return

    # Show progress
    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("## 🎭 Six Thinking Hats Analysis\n\n")
    await msg.stream_token("Running comprehensive BONO Innovation pipeline...\n\n")

    # Progress phases
    phases = [
        "🔍 Classifying problem type",
        "🌐 Discovering relevant domains",
        "👤 Constructing domain personas",
        "🎨 Gathering research context",
        "🎭 Running Six Hats exploration",
        "💡 Generating lateral insights",
        "📊 Synthesizing recommendations"
    ]
    for phase in phases:
        await msg.stream_token(f"- {phase}...\n")

    try:
        # Run the BONO pipeline
        result = await run_bono_session(
            problem=recent_context,
            session_id=session_id,
            context_type="innovation"  # or "strategic", "crisis", "product"
        )

        if "error" in result:
            await msg.stream_token(f"\n\n⚠️ Pipeline error: {result['error']}")
            await msg.update()
            return

        # Format and display results
        await msg.stream_token("\n\n---\n\n")
        report = format_bono_report(result)
        await msg.stream_token(report)
        await msg.update()

        # Add to history
        history.append({"role": "model", "content": f"[BONO Analysis]\n{report[:2000]}"})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n❌ Error: {str(e)[:200]}")
        await msg.update()
        print(f"[BONO] Pipeline error: {e}")


@cl.action_callback("run_rs_discovery")
async def on_run_rs_discovery(action: cl.Action):
    """Run Reverse Salient Discovery pipeline."""
    if not LANGGRAPH_PIPELINES_ENABLED:
        await cl.Message(content="RS Discovery pipeline not available.").send()
        return

    history = cl.user_session.get("history", [])
    session_id = str(cl.user_session.get("id", "default"))

    # Extract context
    recent_context = " ".join([m.get("content", "") for m in history[-6:]])[-2000:]

    if len(recent_context.strip()) < 20:
        await cl.Message(content="Please describe a system, technology, or industry first, then run RS Discovery.").send()
        return

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("## 🔍 Reverse Salient Discovery\n\n")
    await msg.stream_token("Finding constraints that hold back entire system hierarchies...\n\n")

    # Progress phases
    phases = [
        "📊 Mapping system hierarchy",
        "🔗 Identifying component relationships",
        "⚡ Detecting bottlenecks",
        "🎯 Finding reverse salients",
        "💡 Generating innovation opportunities",
        "📋 Prioritizing by leverage"
    ]
    for phase in phases:
        await msg.stream_token(f"- {phase}...\n")

    try:
        result = await run_reverse_salient(
            domain=recent_context,
            session_id=session_id
        )

        if "error" in result:
            await msg.stream_token(f"\n\n⚠️ Error: {result['error']}")
            await msg.update()
            return

        await msg.stream_token("\n\n---\n\n")
        report = format_reverse_salient_result(result)
        await msg.stream_token(report)
        await msg.update()

        history.append({"role": "model", "content": f"[RS Discovery]\n{report[:2000]}"})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n❌ Error: {str(e)[:200]}")
        await msg.update()
        print(f"[RS] Pipeline error: {e}")


@cl.action_callback("run_oracle_prediction")
async def on_run_oracle_prediction(action: cl.Action):
    """Run Oracle Foresight Engine for prediction markets."""
    if not LANGGRAPH_PIPELINES_ENABLED:
        await cl.Message(content="Oracle pipeline not available.").send()
        return

    history = cl.user_session.get("history", [])
    session_id = str(cl.user_session.get("id", "default"))

    recent_context = " ".join([m.get("content", "") for m in history[-6:]])[-2000:]

    if len(recent_context.strip()) < 20:
        await cl.Message(content="Please describe a prediction question or scenario first.").send()
        return

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("## 🔮 Oracle Foresight Engine\n\n")
    await msg.stream_token("Formulating prediction market and research brief...\n\n")

    try:
        result = await run_oracle_formulation(
            question=recent_context,
            session_id=session_id
        )

        if "error" in result:
            await msg.stream_token(f"\n\n⚠️ Error: {result['error']}")
            await msg.update()
            return

        await msg.stream_token("\n\n---\n\n")
        brief = format_research_brief(result)
        await msg.stream_token(brief)
        await msg.update()

        history.append({"role": "model", "content": f"[Oracle Prediction]\n{brief[:2000]}"})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n❌ Error: {str(e)[:200]}")
        await msg.update()
        print(f"[Oracle] Pipeline error: {e}")


@cl.action_callback("run_domain_discovery")
async def on_run_domain_discovery(action: cl.Action):
    """Run Domain Discovery pipeline with LangGraph."""
    if not LANGGRAPH_PIPELINES_ENABLED:
        await cl.Message(content="Domain Discovery pipeline not available.").send()
        return

    history = cl.user_session.get("history", [])
    session_id = str(cl.user_session.get("id", "default"))

    recent_context = " ".join([m.get("content", "") for m in history[-6:]])[-2000:]

    if len(recent_context.strip()) < 20:
        await cl.Message(content="Please describe your background, interests, or research area first.").send()
        return

    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("## 🌐 Domain Discovery Pipeline\n\n")
    await msg.stream_token("Discovering innovation domains from your context...\n\n")

    try:
        result = await run_domain_discovery(
            input_text=recent_context,
            session_id=session_id
        )

        if "error" in result:
            await msg.stream_token(f"\n\n⚠️ Error: {result['error']}")
            await msg.update()
            return

        await msg.stream_token("\n\n---\n\n")
        report = format_domain_discovery_result(result)
        await msg.stream_token(report)
        await msg.update()

        history.append({"role": "model", "content": f"[Domain Discovery]\n{report[:2000]}"})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n❌ Error: {str(e)[:200]}")
        await msg.update()
        print(f"[Domain] Pipeline error: {e}")


@cl.action_callback("run_minto_analysis")
async def on_run_minto_analysis(action: cl.Action):
    """Run Minto Pyramid SCQA pipeline for structured analysis."""
    if not LANGGRAPH_PIPELINES_ENABLED:
        await cl.Message(content="Minto Pyramid pipeline not available. Please check system configuration.").send()
        return

    history = cl.user_session.get("history", [])
    session_id = str(cl.user_session.get("id", "default"))

    # Extract problem from recent conversation
    recent_context = " ".join([m.get("content", "") for m in history[-6:]])[-2000:]

    if len(recent_context.strip()) < 20:
        await cl.Message(content="Please describe a situation or problem first, then run the Minto SCQA analysis.").send()
        return

    # Show progress
    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("## 📊 Minto Pyramid Analysis\n\n")
    await msg.stream_token("Running SCQA structured analysis...\n\n")

    # Progress phases
    phases = [
        "📍 Analyzing current Situation",
        "⚡ Identifying the Complication",
        "❓ Formulating the key Question",
        "💡 Structuring the Answer",
        "🔗 Building supporting arguments",
        "📋 Synthesizing recommendations"
    ]
    for phase in phases:
        await msg.stream_token(f"- {phase}...\n")

    try:
        # Run the Minto pipeline
        result = await run_minto_pipeline(
            query=recent_context,
            session_id=session_id,
            context=""
        )

        if "error" in result:
            await msg.stream_token(f"\n\n⚠️ Pipeline error: {result['error']}")
            await msg.update()
            return

        # Format and display results
        await msg.stream_token("\n\n---\n\n")
        report = format_minto_result(result)
        await msg.stream_token(report)
        await msg.update()

        # Add to history
        history.append({"role": "model", "content": f"[Minto Analysis]\n{report[:2000]}"})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n❌ Error: {str(e)[:200]}")
        await msg.update()
        print(f"[Minto] Pipeline error: {e}")


@cl.action_callback("run_genesis_analysis")
async def on_run_genesis_analysis(action: cl.Action):
    """Run Genesis Expert Breakdown pipeline (multi-domain + BONO Six Hats)."""
    if not LANGGRAPH_PIPELINES_ENABLED:
        await cl.Message(content="Genesis pipeline not available. Please check system configuration.").send()
        return

    history = cl.user_session.get("history", [])
    session_id = str(cl.user_session.get("id", "default"))

    # Extract challenge from recent conversation - Genesis needs 50+ chars
    recent_context = " ".join([m.get("content", "") for m in history[-6:]])[-3000:]

    if len(recent_context.strip()) < 50:
        await cl.Message(content="Please describe a multi-domain challenge first (at least 50 characters), then run Genesis analysis.").send()
        return

    # Show progress
    msg = cl.Message(content="")
    await msg.send()
    await msg.stream_token("## 🧠 Genesis Expert Breakdown\n\n")
    await msg.stream_token("Building cross-domain expert panel with Six Thinking Hats...\n\n")

    # Progress phases (6 stages of Genesis)
    phases = [
        "🔍 Stage 1: Decomposing challenge context",
        "🌐 Stage 2: Identifying relevant domains (24 patterns)",
        "👥 Stage 3: Generating expert personas + Six Hats",
        "📋 Stage 4: Orchestrating research collaboration",
        "🎭 Stage 5: Running expert panel discussion (4 rounds)",
        "💡 Stage 6: Synthesizing breakthroughs & roadmaps"
    ]
    for phase in phases:
        await msg.stream_token(f"- {phase}...\n")

    try:
        # Run the Genesis pipeline
        result = await run_genesis_pipeline(
            challenge=recent_context,
            session_id=session_id
        )

        if result.get("error"):
            await msg.stream_token(f"\n\n⚠️ Pipeline error: {result['error']}")
            await msg.update()
            return

        # Format and display results
        await msg.stream_token("\n\n---\n\n")
        report = format_genesis_report(result)
        await msg.stream_token(report)
        await msg.update()

        # Add to history
        history.append({"role": "model", "content": f"[Genesis Expert Breakdown]\n{report[:2000]}"})
        cl.user_session.set("history", history)

    except Exception as e:
        await msg.stream_token(f"\n\n❌ Error: {str(e)[:200]}")
        await msg.update()
        print(f"[Genesis] Pipeline error: {e}")


# ============================================================
# QA Feedback Form — Interactive In-Chat Testing Survey
# ============================================================

@cl.action_callback("rate_session")
async def on_rate_session(action: cl.Action):
    """Build and display a contextual QA feedback form based on session state."""
    # --- Gather session state ---
    bot_id = cl.user_session.get("bot_id", cl.user_session.get("chat_profile", "unknown"))
    bot = cl.user_session.get("bot", BOTS.get(bot_id, {}))
    history = cl.user_session.get("history", [])
    turn_count = len(history)
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)
    has_phases = bot.get("has_phases", False)

    # Detect orchestration usage — check history for orchestration markers
    orchestration_used = any(
        "[orchestrat" in (m.get("content", "") or "").lower()
        or "multi-agent" in (m.get("content", "") or "").lower()
        or "breakthrough" in (m.get("content", "") or "").lower()
        for m in history if m.get("role") == "model"
    )

    # Detect features used
    features_used = []
    if has_phases:
        features_used.append("phases")
    if any("research" in (m.get("content", "") or "").lower() for m in history if m.get("role") == "model"):
        features_used.append("research")
    if orchestration_used:
        features_used.append("orchestration")

    # Build session info
    session_info = {
        "agent": bot.get("name", bot_id),
        "phases_completed": current_phase if has_phases else None,
        "total_phases": len(phases) if has_phases else None,
        "turn_count": turn_count,
        "orchestration_seen": orchestration_used,
        "features_used": features_used,
    }

    # --- Build contextual sections ---
    yes_somewhat_no = [
        {"value": "yes", "label": "Yes"},
        {"value": "somewhat", "label": "Somewhat"},
        {"value": "no", "label": "No"},
    ]

    sections = []

    # Section 1: General (always shown)
    sections.append({
        "title": "General Experience",
        "visible": True,
        "fields": [
            {"key": "overall_score", "label": "Overall session quality", "type": "rating", "required": True},
            {"key": "agent_helpful", "label": "Was the agent helpful?", "type": "select",
             "options": yes_somewhat_no},
            {"key": "general_comments", "label": "General comments", "type": "textarea", "rows": 3,
             "placeholder": "What stood out? Any suggestions?"},
        ]
    })

    # Section 2: Workshop Experience (only for phase-based bots)
    if has_phases:
        sections.append({
            "title": "Workshop Experience",
            "visible": True,
            "fields": [
                {"key": "workshop_score", "label": "Overall workshop quality", "type": "rating", "required": True},
                {"key": "workshop_structured", "label": "Did the workshop feel structured but not robotic?",
                 "type": "select", "options": yes_somewhat_no},
                {"key": "workshop_socratic", "label": "Were questions Socratic (made you think)?",
                 "type": "select", "options": yes_somewhat_no},
                {"key": "workshop_discovery", "label": "Did you discover something new?",
                 "type": "select", "options": yes_somewhat_no},
                {"key": "workshop_comments", "label": "Workshop comments", "type": "textarea", "rows": 3,
                 "placeholder": "How was the phase progression? Any awkward transitions?"},
            ]
        })

    # Section 3: Orchestration (only if orchestration was triggered)
    if orchestration_used:
        sections.append({
            "title": "Orchestration",
            "visible": True,
            "fields": [
                {"key": "orchestration_score", "label": "Orchestration quality", "type": "rating"},
                {"key": "orchestration_timing", "label": "Was the recommendation well-timed?",
                 "type": "select", "options": yes_somewhat_no},
                {"key": "orchestration_relevant", "label": "Was the orchestration recommendation relevant?",
                 "type": "select", "options": yes_somewhat_no},
                {"key": "orchestration_comments", "label": "Orchestration comments", "type": "textarea", "rows": 2,
                 "placeholder": "Any issues with orchestration flow?"},
            ]
        })

    # Section 4: Bugs & Issues (always shown)
    sections.append({
        "title": "Bugs & Issues",
        "visible": True,
        "fields": [
            {"key": "any_crashes", "label": "Did you experience any crashes or errors?",
             "type": "select", "options": [
                 {"value": "none", "label": "None"},
                 {"value": "minor", "label": "Minor issues"},
                 {"value": "major", "label": "Major issues / crashes"},
             ]},
            {"key": "bug_description", "label": "Describe any bugs encountered", "type": "textarea", "rows": 3,
             "placeholder": "What happened? Steps to reproduce?"},
        ]
    })

    # --- Send the form ---
    form_element = cl.CustomElement(
        name="QAFeedbackForm",
        props={
            "title": "QA Feedback — Feb 11, 2026 Release",
            "description": "Help us improve Mindrian by sharing your testing experience.",
            "sessionInfo": session_info,
            "sections": sections,
            "submitLabel": "Submit Feedback",
            "actionName": "qa_feedback_submit",
        },
        display="inline",
    )
    await cl.Message(content="", elements=[form_element]).send()


@cl.action_callback("qa_feedback_submit")
async def on_qa_feedback_submit(action: cl.Action):
    """Handle QA feedback form submission — save to Supabase Storage + CSV."""
    from pathlib import Path

    form_data = action.payload or {}

    # --- Gather enrichment metadata ---
    session_id = cl.user_session.get("id", "unknown")
    try:
        user = cl.user_session.get("user")
        user_id = user.identifier if user else "anonymous"
    except Exception:
        user_id = "anonymous"

    bot_id = cl.user_session.get("bot_id", cl.user_session.get("chat_profile", "unknown"))
    bot = cl.user_session.get("bot", BOTS.get(bot_id, {}))
    history = cl.user_session.get("history", [])
    turn_count = len(history)
    phases = cl.user_session.get("phases", [])
    current_phase = cl.user_session.get("current_phase", 0)
    has_phases = bot.get("has_phases", False)

    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")

    feedback = {
        "submitted_at": now.isoformat(),
        "session_id": str(session_id),
        "user_id": user_id,
        "bot_id": bot_id,
        "agent_name": bot.get("name", bot_id),
        "turn_count": turn_count,
        "phases_completed": current_phase if has_phases else None,
        "total_phases": len(phases) if has_phases else None,
        "release": "2026-02-11",
        "responses": form_data,
    }

    # --- Save to Supabase Storage ---
    try:
        sb_url = os.getenv("SUPABASE_URL")
        sb_key = os.getenv("SUPABASE_SERVICE_KEY")
        sb_bucket = os.getenv("SUPABASE_BUCKET", "mindrian-files")
        if sb_url and sb_key:
            from supabase import create_client
            sb_client = create_client(sb_url, sb_key)
            file_path = f"qa_feedback/{date_str}/{session_id}.json"
            json_bytes = json.dumps(feedback, indent=2).encode("utf-8")
            try:
                sb_client.storage.from_(sb_bucket).upload(
                    path=file_path,
                    file=json_bytes,
                    file_options={"content-type": "application/json", "upsert": "true"}
                )
            except Exception as upload_err:
                if "Duplicate" in str(upload_err) or "already exists" in str(upload_err).lower():
                    sb_client.storage.from_(sb_bucket).update(
                        path=file_path,
                        file=json_bytes,
                        file_options={"content-type": "application/json"}
                    )
            print(f"[QA_FEEDBACK] Saved to Supabase: {file_path}")
    except Exception as e:
        print(f"[QA_FEEDBACK] Supabase save error: {e}")

    # --- Append to local CSV ---
    try:
        csv_dir = Path("analytics")
        csv_dir.mkdir(exist_ok=True)
        csv_path = csv_dir / "qa_feedback.csv"
        file_exists = csv_path.exists()

        fieldnames = [
            "timestamp", "session_id", "user_id", "bot_id", "agent_name",
            "turn_count", "phases_completed", "overall_score", "workshop_score",
            "orchestration_score", "bugs_reported", "comments",
        ]

        import csv
        row = {
            "timestamp": now.isoformat(),
            "session_id": str(session_id),
            "user_id": user_id,
            "bot_id": bot_id,
            "agent_name": bot.get("name", bot_id),
            "turn_count": turn_count,
            "phases_completed": current_phase if has_phases else "",
            "overall_score": form_data.get("overall_score", ""),
            "workshop_score": form_data.get("workshop_score", ""),
            "orchestration_score": form_data.get("orchestration_score", ""),
            "bugs_reported": form_data.get("any_crashes", "none"),
            "comments": form_data.get("general_comments", ""),
        }

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"[QA_FEEDBACK] Appended to CSV: {csv_path}")
    except Exception as e:
        print(f"[QA_FEEDBACK] CSV save error: {e}")

    # --- Confirmation message ---
    await cl.Message(
        content="**Thank you for your feedback!** Your responses have been recorded and will help improve Mindrian."
    ).send()