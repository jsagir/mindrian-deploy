-- API Health Log Table
-- ====================
-- Stores historical API health check results for monitoring and dashboards.
--
-- Run this in Supabase SQL Editor to create the table.

-- Create table
CREATE TABLE IF NOT EXISTS api_health_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    response_time_ms INTEGER,
    message TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_api_health_api_name ON api_health_log(api_name);
CREATE INDEX IF NOT EXISTS idx_api_health_created_at ON api_health_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_health_status ON api_health_log(status);
CREATE INDEX IF NOT EXISTS idx_api_health_api_time ON api_health_log(api_name, created_at DESC);

-- Enable Row Level Security
ALTER TABLE api_health_log ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access" ON api_health_log
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Useful views for dashboards

-- View: Recent health status by API
CREATE OR REPLACE VIEW api_health_recent AS
SELECT DISTINCT ON (api_name)
    api_name,
    status,
    response_time_ms,
    message,
    created_at
FROM api_health_log
ORDER BY api_name, created_at DESC;

-- View: Daily uptime summary
CREATE OR REPLACE VIEW api_health_daily_summary AS
SELECT
    api_name,
    DATE(created_at) as date,
    COUNT(*) as total_checks,
    SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
    SUM(CASE WHEN status = 'degraded' THEN 1 ELSE 0 END) as degraded_count,
    SUM(CASE WHEN status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy_count,
    ROUND(
        SUM(CASE WHEN status IN ('healthy', 'degraded') THEN 1 ELSE 0 END)::numeric /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as uptime_percent,
    ROUND(AVG(response_time_ms), 0) as avg_response_ms
FROM api_health_log
GROUP BY api_name, DATE(created_at)
ORDER BY date DESC, api_name;

-- Function: Get uptime for a specific API over N days
CREATE OR REPLACE FUNCTION get_api_uptime(
    p_api_name TEXT,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    api_name TEXT,
    period_days INTEGER,
    total_checks BIGINT,
    uptime_percent NUMERIC,
    avg_response_ms NUMERIC,
    degraded_count BIGINT,
    unhealthy_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ahl.api_name,
        p_days as period_days,
        COUNT(*) as total_checks,
        ROUND(
            SUM(CASE WHEN ahl.status IN ('healthy', 'degraded') THEN 1 ELSE 0 END)::numeric /
            NULLIF(COUNT(*), 0) * 100,
            2
        ) as uptime_percent,
        ROUND(AVG(ahl.response_time_ms), 0) as avg_response_ms,
        SUM(CASE WHEN ahl.status = 'degraded' THEN 1 ELSE 0 END) as degraded_count,
        SUM(CASE WHEN ahl.status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy_count
    FROM api_health_log ahl
    WHERE ahl.api_name = p_api_name
      AND ahl.created_at >= NOW() - (p_days || ' days')::interval
    GROUP BY ahl.api_name;
END;
$$ LANGUAGE plpgsql;

-- Comment: Retention policy (run periodically)
-- DELETE FROM api_health_log WHERE created_at < NOW() - INTERVAL '30 days';

-- Grant permissions
GRANT SELECT ON api_health_recent TO authenticated;
GRANT SELECT ON api_health_daily_summary TO authenticated;
