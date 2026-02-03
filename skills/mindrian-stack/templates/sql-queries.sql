-- =============================================================================
-- MINDRIAN SUPABASE SQL QUERY TEMPLATES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- VECTOR SEARCH QUERIES
-- -----------------------------------------------------------------------------

-- Basic semantic search
SELECT 
    id, 
    content, 
    metadata,
    1 - (embedding <=> $1) as similarity
FROM knowledge_base
WHERE 1 - (embedding <=> $1) > 0.7
ORDER BY embedding <=> $1
LIMIT 10;

-- Hybrid search (vector + full-text)
WITH semantic AS (
    SELECT id, content, 
           1 - (embedding <=> $1) as semantic_score
    FROM knowledge_base
    ORDER BY embedding <=> $1
    LIMIT 20
),
keyword AS (
    SELECT id, content,
           ts_rank(to_tsvector('english', content), 
                   plainto_tsquery('english', $2)) as keyword_score
    FROM knowledge_base
    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $2)
    LIMIT 20
)
SELECT 
    COALESCE(s.id, k.id) as id,
    COALESCE(s.content, k.content) as content,
    COALESCE(s.semantic_score, 0) * 0.7 + 
    COALESCE(k.keyword_score, 0) * 0.3 as combined_score
FROM semantic s
FULL OUTER JOIN keyword k ON s.id = k.id
ORDER BY combined_score DESC
LIMIT 10;

-- Search with metadata filter
SELECT 
    id, content, metadata,
    1 - (embedding <=> $1) as similarity
FROM knowledge_base
WHERE 1 - (embedding <=> $1) > 0.7
  AND metadata->>'source' = $2
ORDER BY embedding <=> $1
LIMIT 10;

-- -----------------------------------------------------------------------------
-- KNOWLEDGE BASE MANAGEMENT
-- -----------------------------------------------------------------------------

-- Insert knowledge chunk
INSERT INTO knowledge_base (content, embedding, metadata, source, chunk_index)
VALUES ($1, $2, $3, $4, $5)
RETURNING id;

-- Get chunk with context (surrounding chunks)
WITH target AS (
    SELECT source, chunk_index
    FROM knowledge_base
    WHERE id = $1
)
SELECT kb.id, kb.content, kb.chunk_index
FROM knowledge_base kb
JOIN target t ON kb.source = t.source
WHERE kb.chunk_index BETWEEN t.chunk_index - 1 AND t.chunk_index + 1
ORDER BY kb.chunk_index;

-- Update embedding
UPDATE knowledge_base
SET embedding = $2, updated_at = NOW()
WHERE id = $1;

-- Delete old knowledge
DELETE FROM knowledge_base
WHERE source = $1 AND created_at < NOW() - INTERVAL '30 days';

-- -----------------------------------------------------------------------------
-- CONVERSATION MEMORY
-- -----------------------------------------------------------------------------

-- Store conversation turn
INSERT INTO conversation_memory (session_id, role, content)
VALUES ($1, $2, $3)
RETURNING id;

-- Get recent conversation history
SELECT role, content, created_at
FROM conversation_memory
WHERE session_id = $1
ORDER BY created_at DESC
LIMIT 20;

-- Summarize and consolidate session
INSERT INTO conversation_memory (session_id, role, content, summary)
SELECT 
    session_id,
    'system',
    string_agg(content, E'\n---\n' ORDER BY created_at),
    $2
FROM conversation_memory
WHERE session_id = $1 AND summary IS NULL
GROUP BY session_id;

-- Get session summary
SELECT summary
FROM conversation_memory
WHERE session_id = $1 AND role = 'system' AND summary IS NOT NULL
ORDER BY created_at DESC
LIMIT 1;

-- -----------------------------------------------------------------------------
-- USER PREFERENCES
-- -----------------------------------------------------------------------------

-- Get user preferences
SELECT 
    expertise_level,
    communication_style,
    topic_interests,
    updated_at
FROM user_preferences
WHERE user_id = $1;

-- Update user preferences
INSERT INTO user_preferences (user_id, expertise_level, communication_style, topic_interests)
VALUES ($1, $2, $3, $4)
ON CONFLICT (user_id) DO UPDATE SET
    expertise_level = COALESCE($2, user_preferences.expertise_level),
    communication_style = COALESCE($3, user_preferences.communication_style),
    topic_interests = COALESCE($4, user_preferences.topic_interests),
    updated_at = NOW();

-- Add topic interest
UPDATE user_preferences
SET topic_interests = array_append(topic_interests, $2),
    updated_at = NOW()
WHERE user_id = $1
  AND NOT ($2 = ANY(topic_interests));

-- -----------------------------------------------------------------------------
-- SESSION MANAGEMENT
-- -----------------------------------------------------------------------------

-- Create session
INSERT INTO sessions (user_id, context_summary, workflow_state)
VALUES ($1, $2, $3)
RETURNING id;

-- Update session state
UPDATE sessions
SET 
    workflow_state = $2,
    last_activity = NOW()
WHERE id = $1;

-- Get active sessions for user
SELECT id, context_summary, workflow_state, started_at, last_activity
FROM sessions
WHERE user_id = $1
  AND last_activity > NOW() - INTERVAL '24 hours'
ORDER BY last_activity DESC;

-- Clean up old sessions
DELETE FROM sessions
WHERE last_activity < NOW() - INTERVAL '7 days';

-- -----------------------------------------------------------------------------
-- RPC FUNCTIONS
-- -----------------------------------------------------------------------------

-- Create vector search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.content,
        kb.metadata,
        1 - (kb.embedding <=> query_embedding) as similarity
    FROM knowledge_base kb
    WHERE 1 - (kb.embedding <=> query_embedding) > match_threshold
    ORDER BY kb.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create hybrid search function
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding VECTOR(1536),
    search_text TEXT,
    match_count INT DEFAULT 10,
    semantic_weight FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    combined_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH semantic AS (
        SELECT kb.id, kb.content, 
               1 - (kb.embedding <=> query_embedding) as semantic_score
        FROM knowledge_base kb
        ORDER BY kb.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    keyword AS (
        SELECT kb.id, kb.content,
               ts_rank(to_tsvector('english', kb.content), 
                       plainto_tsquery('english', search_text)) as keyword_score
        FROM knowledge_base kb
        WHERE to_tsvector('english', kb.content) @@ plainto_tsquery('english', search_text)
        LIMIT match_count * 2
    )
    SELECT 
        COALESCE(s.id, k.id),
        COALESCE(s.content, k.content),
        COALESCE(s.semantic_score, 0) * semantic_weight + 
        COALESCE(k.keyword_score, 0) * (1 - semantic_weight)
    FROM semantic s
    FULL OUTER JOIN keyword k ON s.id = k.id
    ORDER BY 3 DESC
    LIMIT match_count;
END;
$$;

-- -----------------------------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------------------------

-- Vector index (IVFFlat - good for large datasets)
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_ivfflat_idx 
ON knowledge_base 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Vector index (HNSW - better recall)
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_hnsw_idx 
ON knowledge_base 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Full-text search index
CREATE INDEX IF NOT EXISTS knowledge_base_content_fts_idx 
ON knowledge_base 
USING gin (to_tsvector('english', content));

-- Metadata index
CREATE INDEX IF NOT EXISTS knowledge_base_metadata_idx 
ON knowledge_base 
USING gin (metadata);

-- Session lookup index
CREATE INDEX IF NOT EXISTS sessions_user_activity_idx 
ON sessions (user_id, last_activity DESC);
