# Edge Functions Reference

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Function Patterns](#function-patterns)
3. [API Orchestration](#api-orchestration)
4. [Event Handling](#event-handling)
5. [Error Handling](#error-handling)
6. [Performance Optimization](#performance-optimization)

---

## Core Concepts

Edge Functions provide **real-time execution** and **API orchestration** at the edge.

**Primary Functions:**
- Real-time request processing
- External API coordination
- Event-driven workflows
- Async parallel operations
- Custom business logic

**Runtime:** Deno (TypeScript/JavaScript)

---

## Function Patterns

### Basic Edge Function Structure

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from '@supabase/supabase-js'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { query, context } = await req.json()
    
    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )
    
    // Process request
    const result = await processQuery(query, context, supabase)
    
    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500
    })
  }
})
```

### Streaming Response

```typescript
serve(async (req) => {
  const encoder = new TextEncoder()
  
  const stream = new ReadableStream({
    async start(controller) {
      // Stream chunks
      for await (const chunk of generateResponse()) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`))
      }
      controller.close()
    }
  })
  
  return new Response(stream, {
    headers: {
      ...corsHeaders,
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
    }
  })
})
```

---

## API Orchestration

### Multi-Service Coordination

```typescript
async function orchestrateQuery(query: string, userId: string) {
  // Parallel: Get user context and generate embedding
  const [userContext, embedding] = await Promise.all([
    getUserContext(userId),
    generateEmbedding(query)
  ])
  
  // Parallel: Vector search and graph traversal
  const [vectorResults, graphResults] = await Promise.all([
    vectorSearch(embedding),
    graphTraversal(query, vectorResults)
  ])
  
  // Sequential: Generate response with all context
  const response = await generateResponse({
    query,
    userContext,
    vectorResults,
    graphResults
  })
  
  return response
}
```

### External API Integration

```typescript
// Claude API call
async function callClaude(messages: Message[], tools?: Tool[]) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': Deno.env.get('ANTHROPIC_API_KEY')!,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      messages,
      tools
    })
  })
  
  return response.json()
}

// Neo4j API call
async function queryNeo4j(cypher: string, params: Record<string, any>) {
  const response = await fetch(`${Deno.env.get('NEO4J_URL')}/db/neo4j/tx/commit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${btoa(Deno.env.get('NEO4J_AUTH')!)}`
    },
    body: JSON.stringify({
      statements: [{ statement: cypher, parameters: params }]
    })
  })
  
  return response.json()
}
```

---

## Event Handling

### Webhook Handler

```typescript
serve(async (req) => {
  const event = await req.json()
  
  switch (event.type) {
    case 'conversation.started':
      await initializeSession(event.sessionId, event.userId)
      break
    
    case 'message.received':
      await processMessage(event.message, event.sessionId)
      break
    
    case 'conversation.ended':
      await consolidateMemory(event.sessionId)
      break
    
    default:
      console.log('Unknown event type:', event.type)
  }
  
  return new Response('ok', { status: 200 })
})
```

### Database Trigger Handler

```typescript
// Triggered by Supabase database webhook
serve(async (req) => {
  const { type, table, record, old_record } = await req.json()
  
  if (table === 'knowledge_base' && type === 'INSERT') {
    // Generate embedding for new knowledge
    const embedding = await generateEmbedding(record.content)
    
    // Update record with embedding
    await supabase
      .from('knowledge_base')
      .update({ embedding })
      .eq('id', record.id)
    
    // Sync to Neo4j
    await syncToNeo4j(record)
  }
  
  return new Response('ok', { status: 200 })
})
```

---

## Error Handling

### Retry Pattern

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, delay * Math.pow(2, i)))
      }
    }
  }
  
  throw lastError!
}

// Usage
const result = await withRetry(() => callClaude(messages), 3, 1000)
```

### Circuit Breaker

```typescript
class CircuitBreaker {
  private failures = 0
  private lastFailure: number = 0
  private state: 'closed' | 'open' | 'half-open' = 'closed'
  
  constructor(
    private threshold: number = 5,
    private timeout: number = 30000
  ) {}
  
  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.timeout) {
        this.state = 'half-open'
      } else {
        throw new Error('Circuit breaker is open')
      }
    }
    
    try {
      const result = await fn()
      this.onSuccess()
      return result
    } catch (error) {
      this.onFailure()
      throw error
    }
  }
  
  private onSuccess() {
    this.failures = 0
    this.state = 'closed'
  }
  
  private onFailure() {
    this.failures++
    this.lastFailure = Date.now()
    if (this.failures >= this.threshold) {
      this.state = 'open'
    }
  }
}
```

---

## Performance Optimization

### Connection Pooling

```typescript
// Reuse Supabase client across requests
const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
  {
    db: { schema: 'public' },
    auth: { persistSession: false }
  }
)
```

### Caching

```typescript
const cache = new Map<string, { data: any; expires: number }>()

async function cachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = 60000
): Promise<T> {
  const cached = cache.get(key)
  
  if (cached && cached.expires > Date.now()) {
    return cached.data
  }
  
  const data = await fetcher()
  cache.set(key, { data, expires: Date.now() + ttl })
  
  return data
}
```

### Parallel Execution

```typescript
// Good: Parallel independent operations
const [a, b, c] = await Promise.all([
  fetchA(),
  fetchB(),
  fetchC()
])

// Bad: Sequential when parallel is possible
const a = await fetchA()
const b = await fetchB()  // Doesn't depend on a
const c = await fetchC()  // Doesn't depend on a or b
```

---

## Best Practices

1. **Fail fast** - Return errors quickly, don't hang
2. **Use timeouts** - Set reasonable limits on external calls
3. **Log strategically** - Log errors and key events, not everything
4. **Warm connections** - Reuse clients across requests
5. **Parallelize** - Use Promise.all for independent operations
6. **Stream when possible** - Don't buffer large responses
