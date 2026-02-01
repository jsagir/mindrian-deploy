-- Journal Entries Table Schema
-- For Supabase - run this in the SQL Editor
-- Stores structured journal entries for cross-session analytics

-- Create the journal_entries table
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id TEXT,
    turn_number INT NOT NULL DEFAULT 0,
    entry_type TEXT NOT NULL,  -- 'insight', 'decision', 'switch', 'observation', 'reasoning', 'action', 'extraction'
    bot_id TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',  -- For extra data: tool output, evidence, concepts
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_journal_session_id ON journal_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_type ON journal_entries(entry_type);
CREATE INDEX IF NOT EXISTS idx_journal_bot_id ON journal_entries(bot_id);
CREATE INDEX IF NOT EXISTS idx_journal_created_at ON journal_entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_journal_user_id ON journal_entries(user_id);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_journal_session_type ON journal_entries(session_id, entry_type);

-- GIN index for JSONB metadata queries
CREATE INDEX IF NOT EXISTS idx_journal_metadata ON journal_entries USING GIN(metadata);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

-- Policy to allow all operations (adjust based on your auth model)
CREATE POLICY "Allow all journal operations" ON journal_entries
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE journal_entries IS 'Stores AI thinking steps and agent handoffs for conversation transparency';
COMMENT ON COLUMN journal_entries.entry_type IS 'Type: insight, decision, switch, observation, reasoning, action, extraction';
COMMENT ON COLUMN journal_entries.metadata IS 'JSON: concepts[], tool_output, evidence[], handoff_summary{}';
