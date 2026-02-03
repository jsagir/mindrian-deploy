-- Recursive Intelligence Tables
-- Phase 1: Event Logging for Learning Loop
-- Run this in Supabase SQL Editor

-- ============================================
-- TABLE: session_events
-- Logs individual events during a session
-- ============================================
CREATE TABLE IF NOT EXISTS session_events (
    id              BIGSERIAL PRIMARY KEY,
    session_id      UUID NOT NULL,
    event_type      TEXT NOT NULL,          -- 'agent_switch' | 'phase_completion' | 'reaction'
    agent           TEXT,                   -- current bot
    from_agent      TEXT,                   -- for agent_switch: which bot they left
    to_agent        TEXT,                   -- for agent_switch: which bot they switched to
    phase_name      TEXT,                   -- for phase_completion
    signal_type     TEXT,                   -- 'positive' | 'negative' | 'redirect' | 'neutral'
    user_initiated  BOOLEAN,                -- did the user manually switch, or did the router?
    turn_count      INTEGER,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_events_session ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_agent ON session_events(agent);
CREATE INDEX IF NOT EXISTS idx_events_type ON session_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON session_events(created_at);

-- ============================================
-- TABLE: session_summaries
-- One row per completed session
-- ============================================
CREATE TABLE IF NOT EXISTS session_summaries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL UNIQUE,
    agents_used         TEXT[] NOT NULL DEFAULT '{}',
    frameworks_applied  TEXT[] DEFAULT '{}',
    problem_type        TEXT,
    total_turns         INTEGER,
    completed           BOOLEAN DEFAULT false,
    venture_id          UUID,
    user_id             TEXT,                -- for cross-session pattern detection
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_summaries_session ON session_summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_summaries_problem ON session_summaries(problem_type);
CREATE INDEX IF NOT EXISTS idx_summaries_user ON session_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_summaries_created ON session_summaries(created_at);

-- ============================================
-- TABLE: session_insights (Phase 3)
-- Staging table for extracted knowledge
-- ============================================
CREATE TABLE IF NOT EXISTS session_insights (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL,
    insight_type        TEXT NOT NULL,      -- 'insight' | 'framework_application' | 'cross_connection' | 'reframing' | 'dead_end'
    content             TEXT NOT NULL,      -- what was discovered
    confidence          TEXT NOT NULL,      -- 'high' | 'medium' | 'low'
    source_agent        TEXT,               -- which bot was active
    entities_mentioned  TEXT[] DEFAULT '{}',-- entity names from extraction
    neo4j_entities_found TEXT[] DEFAULT '{}',-- which exist in Neo4j
    source_positions    JSONB DEFAULT '{}', -- character offsets for audit trail
    status              TEXT DEFAULT 'pending',  -- 'pending' | 'approved' | 'rejected' | 'auto_ingested' | 'archived'
    reviewed_by         TEXT,
    reviewed_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT valid_insight_type CHECK (insight_type IN ('insight', 'framework_application', 'cross_connection', 'reframing', 'dead_end')),
    CONSTRAINT valid_confidence CHECK (confidence IN ('high', 'medium', 'low')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected', 'auto_ingested', 'archived'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_insights_status ON session_insights(status);
CREATE INDEX IF NOT EXISTS idx_insights_type ON session_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_session ON session_insights(session_id);
CREATE INDEX IF NOT EXISTS idx_insights_confidence ON session_insights(confidence);

-- ============================================
-- TABLE: agent_effectiveness (Phase 4B)
-- Learned routing effectiveness scores
-- ============================================
CREATE TABLE IF NOT EXISTS agent_effectiveness (
    agent           TEXT NOT NULL,
    problem_type    TEXT NOT NULL,
    effectiveness   FLOAT NOT NULL DEFAULT 0.5,
    sample_size     INTEGER NOT NULL DEFAULT 0,
    last_updated    TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (agent, problem_type)
);

-- Index for agent lookup
CREATE INDEX IF NOT EXISTS idx_effectiveness_agent ON agent_effectiveness(agent);

-- ============================================
-- FUNCTION: Decay effectiveness scores
-- Monthly decay to prevent stale data
-- ============================================
CREATE OR REPLACE FUNCTION decay_effectiveness(factor FLOAT DEFAULT 0.95)
RETURNS void AS $$
BEGIN
    UPDATE agent_effectiveness
    SET effectiveness = 0.5 + (effectiveness - 0.5) * factor,
        last_updated = now();
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FUNCTION: Rebuild effectiveness from events
-- Weekly batch job
-- ============================================
CREATE OR REPLACE FUNCTION rebuild_agent_effectiveness()
RETURNS void AS $$
BEGIN
    INSERT INTO agent_effectiveness (agent, problem_type, effectiveness, sample_size, last_updated)
    SELECT
        se.agent,
        ss.problem_type,
        AVG(CASE
            WHEN se.signal_type = 'positive' THEN 1.0
            WHEN se.signal_type = 'negative' THEN 0.0
            ELSE 0.5
        END) as effectiveness,
        COUNT(*) as sample_size,
        now() as last_updated
    FROM session_events se
    JOIN session_summaries ss ON se.session_id = ss.session_id
    WHERE se.event_type = 'reaction'
      AND se.signal_type IN ('positive', 'negative')
      AND ss.problem_type IS NOT NULL
    GROUP BY se.agent, ss.problem_type
    HAVING COUNT(*) >= 10
    ON CONFLICT (agent, problem_type) DO UPDATE SET
        effectiveness = EXCLUDED.effectiveness,
        sample_size = EXCLUDED.sample_size,
        last_updated = now();
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMMENTS
-- ============================================
COMMENT ON TABLE session_events IS 'Recursive Intelligence: Individual session events for learning loop';
COMMENT ON TABLE session_summaries IS 'Recursive Intelligence: Session-level summaries for pattern detection';
COMMENT ON TABLE session_insights IS 'Recursive Intelligence: Extracted knowledge staging table';
COMMENT ON TABLE agent_effectiveness IS 'Recursive Intelligence: Learned routing effectiveness scores';
