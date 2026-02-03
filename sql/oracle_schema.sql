-- ═══════════════════════════════════════════════════════════════════════
-- Oracle Agent — Supabase Migration
-- Prediction Markets + Scoring + Research + Gamification
-- Run: supabase db push or paste into SQL Editor
-- ═══════════════════════════════════════════════════════════════════════

-- ─── Markets ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS oracle_markets (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    description TEXT,
    resolution_criteria JSONB NOT NULL DEFAULT '{}'::JSONB,
    category TEXT NOT NULL DEFAULT 'custom'
        CHECK (category IN ('forecast_program', 'validate_idea', 'emerging_trend', 'custom')),
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closes_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '30 days'),
    resolves_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'open', 'closed', 'resolved')),
    resolution_outcome JSONB,
    market_brief JSONB,
    challenge_question TEXT
);

CREATE INDEX IF NOT EXISTS idx_oracle_markets_status ON oracle_markets(status);
CREATE INDEX IF NOT EXISTS idx_oracle_markets_category ON oracle_markets(category);
CREATE INDEX IF NOT EXISTS idx_oracle_markets_closes ON oracle_markets(closes_at);

COMMENT ON TABLE oracle_markets IS 'Oracle prediction market questions with resolution criteria';


-- ─── Predictions ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS oracle_predictions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    market_id TEXT NOT NULL REFERENCES oracle_markets(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    prediction_value FLOAT NOT NULL CHECK (prediction_value BETWEEN 0 AND 1),
    confidence_reasoning TEXT NOT NULL CHECK (length(confidence_reasoning) >= 20),
    key_assumption TEXT,
    confidence_level TEXT DEFAULT 'medium' CHECK (confidence_level IN (
        'very_low', 'low', 'medium', 'high', 'very_high'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    accuracy_brier FLOAT,
    was_crux_call BOOLEAN DEFAULT FALSE,
    UNIQUE(market_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_oracle_predictions_market ON oracle_predictions(market_id);
CREATE INDEX IF NOT EXISTS idx_oracle_predictions_user ON oracle_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_predictions_brier ON oracle_predictions(accuracy_brier);

COMMENT ON TABLE oracle_predictions IS 'Individual predictions with mandatory reasoning and Brier scores';


-- ─── Research ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS oracle_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id TEXT NOT NULL REFERENCES oracle_markets(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL
        CHECK (source_type IN ('web_search', 'neo4j_context', 'hsi_surprise', 'filesearch', 'internal')),
    title TEXT,
    content TEXT,
    url TEXT,
    relevance_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_oracle_research_market ON oracle_research(market_id);
CREATE INDEX IF NOT EXISTS idx_oracle_research_type ON oracle_research(source_type);

COMMENT ON TABLE oracle_research IS 'Intelligence gathered per market: web, Neo4j, HSI surprises';


-- ─── User Scores (Gamification) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS oracle_scores (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    total_predictions INT NOT NULL DEFAULT 0,
    resolved_predictions INT NOT NULL DEFAULT 0,
    markets_created INT NOT NULL DEFAULT 0,
    avg_brier_score FLOAT,
    best_brier_score FLOAT,
    worst_brier_score FLOAT,
    insight_points INT NOT NULL DEFAULT 0,
    analyst_level TEXT NOT NULL DEFAULT 'observer' CHECK (analyst_level IN (
        'observer', 'forecaster', 'analyst', 'strategist', 'oracle'
    )),
    crux_calls INT NOT NULL DEFAULT 0,
    current_streak INT NOT NULL DEFAULT 0,
    best_streak INT NOT NULL DEFAULT 0,
    badges JSONB NOT NULL DEFAULT '[]'::JSONB,
    calibration_buckets JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_oracle_scores_brier ON oracle_scores(avg_brier_score);
CREATE INDEX IF NOT EXISTS idx_oracle_scores_points ON oracle_scores(insight_points DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_scores_level ON oracle_scores(analyst_level);

COMMENT ON TABLE oracle_scores IS 'Oracle gamification: levels, badges, streaks, Brier scores';


-- ─── Retrospectives ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS oracle_retrospectives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id TEXT NOT NULL REFERENCES oracle_markets(id) ON DELETE CASCADE,
    outcome TEXT NOT NULL,
    crowd_accuracy FLOAT,
    outcome_summary TEXT,
    market_accuracy JSONB,
    optimist_themes JSONB DEFAULT '[]',
    skeptic_themes JSONB DEFAULT '[]',
    crux_disagreement TEXT,
    crux_correct_side TEXT CHECK (crux_correct_side IN ('optimists', 'skeptics', 'neither')),
    crux_resolution JSONB,
    signals_missed JSONB DEFAULT '[]'::JSONB,
    lesson_learned TEXT,
    pattern_extracted TEXT,
    forecast_pattern JSONB,
    knowledge_updates JSONB DEFAULT '[]'::JSONB,
    synced_to_neo4j BOOLEAN DEFAULT FALSE,
    neo4j_node_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_oracle_retrospectives_market ON oracle_retrospectives(market_id);

COMMENT ON TABLE oracle_retrospectives IS 'Prediction autopsies with extracted learning patterns';


-- ═══════════════════════════════════════════════════════════════════════
-- RPC Functions — Called by Oracle Agent tools
-- ═══════════════════════════════════════════════════════════════════════

-- Increment prediction count and points
CREATE OR REPLACE FUNCTION oracle_increment_score(
    p_user_id UUID,
    p_points INT,
    p_predictions INT DEFAULT 1
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO oracle_scores (user_id, total_predictions, insight_points)
    VALUES (p_user_id, p_predictions, p_points)
    ON CONFLICT (user_id) DO UPDATE
    SET total_predictions = oracle_scores.total_predictions + p_predictions,
        insight_points = oracle_scores.insight_points + p_points,
        updated_at = now();
END;
$$;


-- Update Brier score after market resolution
CREATE OR REPLACE FUNCTION oracle_update_brier(
    p_user_id UUID,
    p_new_brier FLOAT,
    p_bonus_points INT DEFAULT 0
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_current_resolved INT;
    v_current_avg FLOAT;
    v_new_avg FLOAT;
    v_is_accurate BOOLEAN;
    v_current_streak INT;
BEGIN
    -- Get current stats
    SELECT resolved_predictions, avg_brier_score, current_streak
    INTO v_current_resolved, v_current_avg, v_current_streak
    FROM oracle_scores
    WHERE user_id = p_user_id;

    -- If user doesn't exist yet, create them
    IF NOT FOUND THEN
        INSERT INTO oracle_scores (
            user_id, total_predictions, resolved_predictions,
            avg_brier_score, best_brier_score, insight_points, current_streak
        ) VALUES (
            p_user_id, 1, 1, p_new_brier, p_new_brier, p_bonus_points,
            CASE WHEN p_new_brier < 0.30 THEN 1 ELSE 0 END
        );
        RETURN;
    END IF;

    -- Calculate running average Brier
    IF v_current_avg IS NULL THEN
        v_new_avg := p_new_brier;
    ELSE
        v_new_avg := (v_current_avg * v_current_resolved + p_new_brier)
                     / (v_current_resolved + 1);
    END IF;

    -- Track streak (Brier < 0.30 = accurate)
    v_is_accurate := (p_new_brier < 0.30);

    UPDATE oracle_scores
    SET resolved_predictions = resolved_predictions + 1,
        avg_brier_score = v_new_avg,
        best_brier_score = LEAST(COALESCE(best_brier_score, 1.0), p_new_brier),
        worst_brier_score = GREATEST(COALESCE(worst_brier_score, 0.0), p_new_brier),
        insight_points = insight_points + p_bonus_points,
        current_streak = CASE
            WHEN v_is_accurate THEN current_streak + 1
            ELSE 0
        END,
        best_streak = CASE
            WHEN v_is_accurate AND current_streak + 1 > best_streak
                THEN current_streak + 1
            ELSE best_streak
        END,
        analyst_level = CASE
            WHEN v_new_avg < 0.20 AND resolved_predictions + 1 >= 50 THEN 'oracle'
            WHEN v_new_avg < 0.25 AND resolved_predictions + 1 >= 25 THEN 'strategist'
            WHEN v_new_avg < 0.30 AND resolved_predictions + 1 >= 10 THEN 'analyst'
            WHEN total_predictions >= 5 THEN 'forecaster'
            ELSE 'observer'
        END,
        updated_at = now()
    WHERE user_id = p_user_id;
END;
$$;


-- Auto-close expired markets
CREATE OR REPLACE FUNCTION oracle_close_expired_markets()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE oracle_markets
    SET status = 'closed'
    WHERE status = 'open'
      AND closes_at < now();
END;
$$;


-- Increment crux calls for a user
CREATE OR REPLACE FUNCTION oracle_increment_crux_call(p_user_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE oracle_scores
    SET crux_calls = crux_calls + 1,
        insight_points = insight_points + 100,  -- Bonus for crux call
        updated_at = now()
    WHERE user_id = p_user_id;

    -- Check if user should be promoted to oracle
    UPDATE oracle_scores
    SET analyst_level = 'oracle'
    WHERE user_id = p_user_id
      AND avg_brier_score < 0.20
      AND crux_calls >= 3;
END;
$$;


-- ═══════════════════════════════════════════════════════════════════════
-- Views — Leaderboard and Market Stats
-- ═══════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW oracle_leaderboard AS
SELECT
    user_id,
    analyst_level,
    avg_brier_score,
    resolved_predictions,
    total_predictions,
    insight_points,
    crux_calls,
    current_streak,
    best_streak,
    badges
FROM oracle_scores
WHERE resolved_predictions >= 5
ORDER BY avg_brier_score ASC;


CREATE OR REPLACE VIEW oracle_market_stats AS
SELECT
    m.id,
    m.question,
    m.category,
    m.status,
    m.closes_at,
    COUNT(p.id) AS prediction_count,
    AVG(p.prediction_value) AS avg_prediction,
    STDDEV(p.prediction_value) AS prediction_spread
FROM oracle_markets m
LEFT JOIN oracle_predictions p ON p.market_id = m.id
GROUP BY m.id, m.question, m.category, m.status, m.closes_at;


-- View for recent retrospectives with patterns
CREATE OR REPLACE VIEW oracle_recent_patterns AS
SELECT
    r.id,
    m.question,
    r.outcome,
    r.crowd_accuracy,
    r.lesson_learned,
    r.pattern_extracted,
    r.crux_disagreement,
    r.crux_correct_side,
    r.created_at
FROM oracle_retrospectives r
JOIN oracle_markets m ON m.id = r.market_id
WHERE r.pattern_extracted IS NOT NULL
ORDER BY r.created_at DESC
LIMIT 50;


-- ═══════════════════════════════════════════════════════════════════════
-- Row Level Security (RLS)
-- ═══════════════════════════════════════════════════════════════════════

ALTER TABLE oracle_markets ENABLE ROW LEVEL SECURITY;
ALTER TABLE oracle_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE oracle_research ENABLE ROW LEVEL SECURITY;
ALTER TABLE oracle_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE oracle_retrospectives ENABLE ROW LEVEL SECURITY;

-- Markets: everyone can read, authenticated can create
CREATE POLICY IF NOT EXISTS oracle_markets_read ON oracle_markets
    FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS oracle_markets_insert ON oracle_markets
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY IF NOT EXISTS oracle_markets_update ON oracle_markets
    FOR UPDATE USING (auth.uid() = created_by OR auth.uid() IN (
        SELECT id FROM auth.users WHERE raw_app_meta_data->>'role' = 'admin'
    ));

-- Predictions: own predictions readable, can insert/update own
CREATE POLICY IF NOT EXISTS oracle_predictions_read ON oracle_predictions
    FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS oracle_predictions_insert ON oracle_predictions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY IF NOT EXISTS oracle_predictions_update ON oracle_predictions
    FOR UPDATE USING (auth.uid() = user_id);

-- Research: everyone can read
CREATE POLICY IF NOT EXISTS oracle_research_read ON oracle_research
    FOR SELECT USING (true);

-- Scores: everyone can read, system updates
CREATE POLICY IF NOT EXISTS oracle_scores_read ON oracle_scores
    FOR SELECT USING (true);

-- Retrospectives: everyone can read
CREATE POLICY IF NOT EXISTS oracle_retrospectives_read ON oracle_retrospectives
    FOR SELECT USING (true);
