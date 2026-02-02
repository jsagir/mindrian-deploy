-- Bank of Opportunities - PWS-Compliant Schema
-- =============================================
-- Run this in Supabase SQL Editor to create the opportunity registry
--
-- This creates:
-- 1. opportunity_bank table with full PWS fields
-- 2. opportunity_sources junction table for multi-source tracking
-- 3. Helper functions: register_opportunity, search_opportunities, get_opportunities_by_creator
-- 4. Summary view: opportunity_summary
-- 5. Indexes for performance

-- =============================================================================
-- MAIN TABLE: opportunity_bank
-- =============================================================================
CREATE TABLE IF NOT EXISTS opportunity_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core PWS Fields
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    problem TEXT,                    -- The constraint/reverse salient being addressed
    value_potential TEXT DEFAULT 'medium' CHECK (value_potential IN ('low', 'medium', 'high', 'transformative')),
    solution_direction TEXT,         -- How it could be solved
    validation TEXT,                 -- Evidence it's real
    job_to_be_done TEXT,            -- JTBD framing - what user need is served
    platform_multiplier TEXT,        -- Scalability potential

    -- Classification
    opportunity_type TEXT DEFAULT 'innovation' CHECK (opportunity_type IN (
        'innovation', 'market', 'product', 'movement', 'synthesis',
        'reverse_salient', 'wind', 'strategic',
        'problem_worth_solving', 'unmet_need', 'market_gap',
        'technology_opportunity', 'process_improvement', 'emerging_trend', 'validated_insight'
    )),
    domain TEXT,
    subdomain TEXT,
    tags TEXT[] DEFAULT '{}',

    -- Provenance (Who Created It)
    created_by TEXT NOT NULL DEFAULT 'system',
    created_by_type TEXT DEFAULT 'system' CHECK (created_by_type IN ('user', 'ai_agent', 'framework', 'system')),

    -- Source Tracking
    source_type TEXT CHECK (source_type IN ('conversation', 'document', 'framework', 'analysis', 'external')),
    source_id TEXT,                  -- Unique identifier (conversation_id, document_id, etc.)
    source_name TEXT,                -- Human-readable name
    source_snippet TEXT,             -- Key content excerpt
    source_url TEXT,                 -- External URL if applicable
    source_bot TEXT,                 -- Bot that extracted this (lawrence, tta, etc.)
    source_phase TEXT,               -- Workshop phase
    source_methodology TEXT,         -- Methodology applied (JTBD, TTA, etc.)

    -- LangExtract Integration
    extraction_method TEXT DEFAULT 'ai_synthesis' CHECK (extraction_method IN ('manual', 'langextract', 'ai_synthesis', 'hybrid')),
    extraction_confidence DECIMAL(3,2) DEFAULT 0.50 CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
    extracted_entities JSONB DEFAULT '{}',
    extracted_keywords TEXT[] DEFAULT '{}',

    -- Scoring
    differential_score DECIMAL(3,2) CHECK (differential_score >= 0 AND differential_score <= 1),
    feasibility_score DECIMAL(3,2) CHECK (feasibility_score >= 0 AND feasibility_score <= 1),
    impact_score DECIMAL(3,2) CHECK (impact_score >= 0 AND impact_score <= 1),

    -- Legacy fields for backwards compatibility with opportunity_bank.py
    target_users TEXT[] DEFAULT '{}',
    pain_points TEXT[] DEFAULT '{}',
    evidence TEXT[] DEFAULT '{}',
    frameworks_applied TEXT[] DEFAULT '{}',
    related_opportunities TEXT[] DEFAULT '{}',

    -- Vector for semantic search (optional - requires pgvector extension)
    -- embedding vector(1536),

    -- Status & Sync
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'discovered', 'validated', 'prioritized', 'actioned', 'archived', 'implemented')),
    validation_status TEXT DEFAULT 'unvalidated',
    neo4j_synced BOOLEAN DEFAULT FALSE,
    neo4j_node_id TEXT,

    -- User tracking
    user_id TEXT,
    conversation_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================================================
-- JUNCTION TABLE: opportunity_sources (for multi-source tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS opportunity_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunity_bank(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    source_id TEXT,
    source_name TEXT,
    source_snippet TEXT,
    source_url TEXT,
    relevance_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_opp_created_by ON opportunity_bank(created_by);
CREATE INDEX IF NOT EXISTS idx_opp_created_at ON opportunity_bank(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_opp_domain ON opportunity_bank(domain);
CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunity_bank(status);
CREATE INDEX IF NOT EXISTS idx_opp_type ON opportunity_bank(opportunity_type);
CREATE INDEX IF NOT EXISTS idx_opp_value_potential ON opportunity_bank(value_potential);
CREATE INDEX IF NOT EXISTS idx_opp_user_id ON opportunity_bank(user_id);
CREATE INDEX IF NOT EXISTS idx_opp_conversation_id ON opportunity_bank(conversation_id);
CREATE INDEX IF NOT EXISTS idx_opp_source_bot ON opportunity_bank(source_bot);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_opp_fts ON opportunity_bank
USING GIN(to_tsvector('english',
    COALESCE(name, '') || ' ' ||
    COALESCE(description, '') || ' ' ||
    COALESCE(problem, '') || ' ' ||
    COALESCE(job_to_be_done, '')
));

-- Junction table indexes
CREATE INDEX IF NOT EXISTS idx_opp_sources_opp_id ON opportunity_sources(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_opp_sources_type ON opportunity_sources(source_type);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Register a new opportunity
CREATE OR REPLACE FUNCTION register_opportunity(
    p_name TEXT,
    p_description TEXT,
    p_problem TEXT DEFAULT NULL,
    p_value_potential TEXT DEFAULT 'medium',
    p_solution_direction TEXT DEFAULT NULL,
    p_job_to_be_done TEXT DEFAULT NULL,
    p_created_by TEXT DEFAULT 'system',
    p_created_by_type TEXT DEFAULT 'system',
    p_source_type TEXT DEFAULT NULL,
    p_source_snippet TEXT DEFAULT NULL,
    p_domain TEXT DEFAULT NULL,
    p_opportunity_type TEXT DEFAULT 'innovation',
    p_tags TEXT[] DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO opportunity_bank (
        name, description, problem, value_potential, solution_direction,
        job_to_be_done, created_by, created_by_type, source_type,
        source_snippet, domain, opportunity_type, tags
    ) VALUES (
        p_name, p_description, p_problem, p_value_potential, p_solution_direction,
        p_job_to_be_done, p_created_by, p_created_by_type, p_source_type,
        p_source_snippet, p_domain, p_opportunity_type, p_tags
    )
    RETURNING id INTO new_id;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- Search opportunities (full-text)
CREATE OR REPLACE FUNCTION search_opportunities(
    query_text TEXT,
    limit_count INT DEFAULT 10
) RETURNS SETOF opportunity_bank AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM opportunity_bank
    WHERE to_tsvector('english',
        COALESCE(name, '') || ' ' ||
        COALESCE(description, '') || ' ' ||
        COALESCE(problem, '') || ' ' ||
        COALESCE(job_to_be_done, '')
    ) @@ plainto_tsquery('english', query_text)
    ORDER BY ts_rank(
        to_tsvector('english',
            COALESCE(name, '') || ' ' ||
            COALESCE(description, '') || ' ' ||
            COALESCE(problem, '') || ' ' ||
            COALESCE(job_to_be_done, '')
        ),
        plainto_tsquery('english', query_text)
    ) DESC, created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Get opportunities by creator
CREATE OR REPLACE FUNCTION get_opportunities_by_creator(
    p_created_by TEXT,
    limit_count INT DEFAULT 50
) RETURNS SETOF opportunity_bank AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM opportunity_bank
    WHERE created_by = p_created_by
    ORDER BY created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Get opportunities by date range
CREATE OR REPLACE FUNCTION get_opportunities_by_date(
    p_start_date TIMESTAMPTZ,
    p_end_date TIMESTAMPTZ DEFAULT now(),
    limit_count INT DEFAULT 100
) RETURNS SETOF opportunity_bank AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM opportunity_bank
    WHERE created_at >= p_start_date AND created_at <= p_end_date
    ORDER BY created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SUMMARY VIEW
-- =============================================================================
CREATE OR REPLACE VIEW opportunity_summary AS
SELECT
    id,
    name,
    CASE WHEN LENGTH(description) > 100 THEN SUBSTRING(description, 1, 100) || '...' ELSE description END as description_preview,
    problem,
    value_potential,
    opportunity_type,
    domain,
    created_by,
    created_by_type,
    source_bot,
    extraction_confidence,
    status,
    created_at
FROM opportunity_bank
ORDER BY created_at DESC;

-- =============================================================================
-- ROW LEVEL SECURITY (Optional)
-- =============================================================================
ALTER TABLE opportunity_bank ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations (adjust based on your auth model)
CREATE POLICY "Allow all opportunity operations" ON opportunity_bank
    FOR ALL
    USING (true)
    WITH CHECK (true);

ALTER TABLE opportunity_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all source operations" ON opportunity_sources
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- =============================================================================
-- TRIGGER: Update updated_at timestamp
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_opportunity_bank_updated_at
    BEFORE UPDATE ON opportunity_bank
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE opportunity_bank IS 'PWS-compliant opportunity registry with dual-storage support (Supabase + Neo4j)';
COMMENT ON COLUMN opportunity_bank.name IS 'Clear, descriptive title for the opportunity';
COMMENT ON COLUMN opportunity_bank.problem IS 'The constraint/reverse salient being addressed';
COMMENT ON COLUMN opportunity_bank.value_potential IS 'Assessment: low, medium, high, transformative';
COMMENT ON COLUMN opportunity_bank.job_to_be_done IS 'JTBD framing - what user need is served';
COMMENT ON COLUMN opportunity_bank.platform_multiplier IS 'Scalability potential assessment';
COMMENT ON COLUMN opportunity_bank.source_snippet IS 'Key content excerpt from the source';
COMMENT ON COLUMN opportunity_bank.created_by IS 'Person, AI, or system that identified this opportunity';
COMMENT ON COLUMN opportunity_bank.extraction_confidence IS 'LangExtract confidence score (0.00-1.00)';
