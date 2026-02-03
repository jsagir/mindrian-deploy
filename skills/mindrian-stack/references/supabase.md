# Supabase PostgreSQL Reference

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Schema Design](#schema-design)
3. [Vector Search (pgvector)](#vector-search-pgvector)
4. [RAG Knowledge Base](#rag-knowledge-base)
5. [Real-time Subscriptions](#real-time-subscriptions)
6. [Edge Function Integration](#edge-function-integration)

---

## Core Concepts

Supabase provides **persistence**, **vector search**, and **structured storage** with ACID compliance.

**Primary Functions:**
- Semantic similarity search via pgvector
- Chunked document storage with embeddings
- Transactional operations with rollback
- Real-time WebSocket subscriptions
- User preference and session state storage

---

## Schema Design

### Core Tables

```sql
-- Knowledge base chunks with embeddings
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    source VARCHAR(255),
    chunk_index INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation memory
CREATE TABLE conversation_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    expertise_level VARCHAR(20) DEFAULT 'intermediate',
    communication_style JSONB,
    topic_interests TEXT[],
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session state
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    context_summary TEXT,
    workflow_state JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);
```

### Indexes

```sql
-- Vector similarity index (IVFFlat for large datasets)
CREATE INDEX ON knowledge_base 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- HNSW index (better recall, slower build)
CREATE INDEX ON knowledge_base 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Text search index
CREATE INDEX ON knowledge_base 
USING gin (to_tsvector('english', content));
```

---

## Vector Search (pgvector)

### Semantic Similarity Search

```sql
-- Find similar documents
SELECT id, content, metadata,
       1 - (embedding <=> $query_embedding) as similarity
FROM knowledge_base
WHERE 1 - (embedding <=> $query_embedding) > 0.7
ORDER BY embedding <=> $query_embedding
LIMIT 10;
```

### Hybrid Search (Vector + Full-text)

```sql
-- Combine semantic and keyword search
WITH semantic AS (
    SELECT id, content, 
           1 - (embedding <=> $query_embedding) as semantic_score
    FROM knowledge_base
    ORDER BY embedding <=> $query_embedding
    LIMIT 20
),
keyword AS (
    SELECT id, content,
           ts_rank(to_tsvector('english', content), 
                   plainto_tsquery('english', $search_text)) as keyword_score
    FROM knowledge_base
    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $search_text)
    LIMIT 20
)
SELECT COALESCE(s.id, k.id) as id,
       COALESCE(s.content, k.content) as content,
       COALESCE(s.semantic_score, 0) * 0.7 + 
       COALESCE(k.keyword_score, 0) * 0.3 as combined_score
FROM semantic s
FULL OUTER JOIN keyword k ON s.id = k.id
ORDER BY combined_score DESC
LIMIT 10;
```

---

## RAG Knowledge Base

### Document Chunking Strategy

| Content Type | Chunk Size | Overlap | Strategy |
|--------------|------------|---------|----------|
| Technical docs | 512 tokens | 50 tokens | Paragraph-aware |
| Conversations | 256 tokens | 25 tokens | Turn-based |
| Code | 1024 tokens | 100 tokens | Function-aware |
| Frameworks | 768 tokens | 75 tokens | Section-based |

### Insert Chunked Document

```sql
INSERT INTO knowledge_base (content, embedding, metadata, source, chunk_index)
VALUES 
    ($chunk_text, $embedding_vector, 
     '{"title": "...", "section": "..."}', 
     $source_name, $chunk_idx);
```

### Retrieve with Context

```sql
-- Get chunk with surrounding context
WITH target AS (
    SELECT id, source, chunk_index
    FROM knowledge_base
    WHERE id = $chunk_id
)
SELECT kb.id, kb.content, kb.chunk_index
FROM knowledge_base kb
JOIN target t ON kb.source = t.source
WHERE kb.chunk_index BETWEEN t.chunk_index - 1 AND t.chunk_index + 1
ORDER BY kb.chunk_index;
```

---

## Real-time Subscriptions

### Enable Real-time on Table

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE sessions;
```

### Client Subscription (JavaScript)

```javascript
const subscription = supabase
  .channel('session-updates')
  .on('postgres_changes', 
      { event: 'UPDATE', schema: 'public', table: 'sessions', filter: `id=eq.${sessionId}` },
      (payload) => handleSessionUpdate(payload.new))
  .subscribe();
```

---

## Edge Function Integration

### Call from Edge Function

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

// Vector search
const { data, error } = await supabase.rpc('match_documents', {
  query_embedding: embedding,
  match_threshold: 0.7,
  match_count: 10
})
```

### RPC Function for Vector Search

```sql
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (id UUID, content TEXT, similarity FLOAT)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT kb.id, kb.content,
         1 - (kb.embedding <=> query_embedding) as similarity
  FROM knowledge_base kb
  WHERE 1 - (kb.embedding <=> query_embedding) > match_threshold
  ORDER BY kb.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

---

## Best Practices

1. **Use RPC functions** - Encapsulate complex queries for Edge Functions
2. **Batch embeddings** - Generate embeddings in batches of 100
3. **Index strategically** - IVFFlat for >100k rows, HNSW for better recall
4. **Partition large tables** - By date or source for better performance
5. **Use connection pooling** - PgBouncer for Edge Function connections
