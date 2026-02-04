# Conversation Sampler & Admin Dashboard

**Priority:** Medium-High
**Status:** Proposed
**Date:** 2026-02-04

## Problem Statement

Mindrian has extensive interaction logging across multiple systems (PostgreSQL, Supabase, CSV, Neo4j), but no unified interface to:
- Sample and review actual conversations
- Identify quality issues and patterns
- Analyze usage across bots
- Debug user-reported problems

## Existing Data Sources

| System | Data | Location |
|--------|------|----------|
| PostgreSQL | Full conversation history | Chainlit native DB |
| Supabase | Audit trail, metrics, events | `audit/`, `metrics/`, `session_events` |
| CSV | Feedback analytics | `analytics/feedback_analytics.csv` |
| Neo4j | User journeys, insights | `UserJourney` nodes |
| In-Memory | Real-time events | `_event_buffer`, `feedback_cache` |

## Proposed Features

### 1. Conversation Sampler
- Browse recent conversations by user, bot, date
- Filter by: feedback score, bot switches, phase completions
- Full transcript view with thinking steps
- Flag conversations for review

### 2. Quality Dashboard
- Satisfaction rate trends (thumbs up/down)
- Bot performance comparison
- Common failure patterns
- AI-generated quality insights (via Gemini)

### 3. Usage Analytics
- Daily/weekly active users
- Bot usage distribution
- Peak hours heatmap
- Session length distribution

### 4. Debug Tools
- Search conversations by content
- View audit trail for specific sessions
- Replay conversation state
- Export for offline analysis

## Technical Approach Options

### Option A: Chainlit Custom Page
- Add `/admin` route to mindrian_chat.py
- Use Chainlit's custom element system
- Pros: Integrated, no new deployment
- Cons: Limited to Chainlit's UI constraints

### Option B: Standalone Streamlit Dashboard
- Separate `admin_dashboard.py`
- Connect to same PostgreSQL/Supabase
- Pros: Full UI flexibility, charts, tables
- Cons: Separate deployment, auth needed

### Option C: CLI Tool
- `python scripts/conversation_sampler.py`
- Interactive terminal interface
- Pros: Quick to build, no UI work
- Cons: Not accessible to non-technical users

## Recommendation

Start with **Option C (CLI Tool)** for immediate debugging needs, then build **Option B (Streamlit)** for the full dashboard.

## Related Files

- `utils/data_layer.py` - MindrianDataLayer with feedback methods
- `governance/audit_trail.py` - Audit log access
- `utils/session_logger.py` - Session events
- `utils/usage_metrics.py` - Usage tracking
- `scripts/daily_summary.py` - Email reports (already has AI insights)

## Next Steps

1. [ ] Build CLI conversation sampler (`scripts/conversation_sampler.py`)
2. [ ] Add conversation export to daily_summary.py
3. [ ] Prototype Streamlit dashboard
4. [ ] Add authentication for admin access
