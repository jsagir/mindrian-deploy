// =============================================================================
// MINDRIAN EDGE FUNCTION TEMPLATE
// =============================================================================
// Copy and customize this template for new Edge Functions

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient, SupabaseClient } from '@supabase/supabase-js'

// -----------------------------------------------------------------------------
// CONFIGURATION
// -----------------------------------------------------------------------------

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Initialize Supabase client (reused across requests)
const supabase: SupabaseClient = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
  { auth: { persistSession: false } }
)

// -----------------------------------------------------------------------------
// TYPES
// -----------------------------------------------------------------------------

interface RequestPayload {
  query: string
  userId?: string
  sessionId?: string
  options?: {
    maxResults?: number
    includeContext?: boolean
    streamResponse?: boolean
  }
}

interface ResponsePayload {
  success: boolean
  data?: any
  error?: string
  metadata?: {
    processingTime: number
    sources: string[]
  }
}

// -----------------------------------------------------------------------------
// HELPER FUNCTIONS
// -----------------------------------------------------------------------------

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`
    },
    body: JSON.stringify({
      model: 'text-embedding-3-small',
      input: text
    })
  })
  
  const result = await response.json()
  return result.data[0].embedding
}

async function vectorSearch(embedding: number[], limit: number = 10) {
  const { data, error } = await supabase.rpc('match_documents', {
    query_embedding: embedding,
    match_threshold: 0.7,
    match_count: limit
  })
  
  if (error) throw error
  return data
}

async function queryNeo4j(cypher: string, params: Record<string, any> = {}) {
  const response = await fetch(
    `${Deno.env.get('NEO4J_URL')}/db/neo4j/tx/commit`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${btoa(Deno.env.get('NEO4J_AUTH')!)}`
      },
      body: JSON.stringify({
        statements: [{ statement: cypher, parameters: params }]
      })
    }
  )
  
  const result = await response.json()
  if (result.errors?.length) throw new Error(result.errors[0].message)
  return result.results[0]?.data || []
}

async function getUserContext(userId: string) {
  const { data, error } = await supabase
    .from('user_preferences')
    .select('*')
    .eq('user_id', userId)
    .single()
  
  if (error && error.code !== 'PGRST116') throw error
  return data
}

// -----------------------------------------------------------------------------
// RETRY UTILITY
// -----------------------------------------------------------------------------

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
      lastError = error as Error
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, delay * Math.pow(2, i)))
      }
    }
  }
  
  throw lastError!
}

// -----------------------------------------------------------------------------
// MAIN PROCESSING LOGIC
// -----------------------------------------------------------------------------

async function processRequest(payload: RequestPayload): Promise<ResponsePayload> {
  const startTime = Date.now()
  const sources: string[] = []
  
  try {
    // 1. Get user context (if userId provided)
    let userContext = null
    if (payload.userId) {
      userContext = await getUserContext(payload.userId)
      sources.push('user_preferences')
    }
    
    // 2. Generate embedding for query
    const embedding = await generateEmbedding(payload.query)
    
    // 3. Parallel: Vector search + Graph expansion
    const [vectorResults, graphResults] = await Promise.all([
      vectorSearch(embedding, payload.options?.maxResults || 10),
      withRetry(() => queryNeo4j(
        `MATCH (c:Concept)
         WHERE c.name =~ $pattern
         OPTIONAL MATCH (c)-[:RELATED_TO]-(related)
         RETURN c.name, collect(related.name) as related
         LIMIT 5`,
        { pattern: `(?i).*${payload.query.split(' ')[0]}.*` }
      ))
    ])
    
    sources.push('knowledge_base', 'neo4j')
    
    // 4. Combine and return results
    return {
      success: true,
      data: {
        vectorResults,
        graphResults,
        userContext
      },
      metadata: {
        processingTime: Date.now() - startTime,
        sources
      }
    }
  } catch (error) {
    return {
      success: false,
      error: (error as Error).message,
      metadata: {
        processingTime: Date.now() - startTime,
        sources
      }
    }
  }
}

// -----------------------------------------------------------------------------
// REQUEST HANDLER
// -----------------------------------------------------------------------------

serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }
  
  try {
    // Parse request
    const payload: RequestPayload = await req.json()
    
    // Validate required fields
    if (!payload.query) {
      return new Response(
        JSON.stringify({ success: false, error: 'Missing required field: query' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      )
    }
    
    // Process request
    const result = await processRequest(payload)
    
    return new Response(
      JSON.stringify(result),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: result.success ? 200 : 500
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, error: (error as Error).message }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    )
  }
})

// -----------------------------------------------------------------------------
// STREAMING RESPONSE VARIANT
// -----------------------------------------------------------------------------

// Uncomment and use this handler for streaming responses:
/*
serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }
  
  const encoder = new TextEncoder()
  const payload: RequestPayload = await req.json()
  
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Stream progress updates
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'status', message: 'Processing...' })}\n\n`))
        
        // Generate embedding
        const embedding = await generateEmbedding(payload.query)
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'status', message: 'Searching...' })}\n\n`))
        
        // Get results
        const results = await vectorSearch(embedding)
        
        // Stream each result
        for (const result of results) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'result', data: result })}\n\n`))
        }
        
        // Done
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'done' })}\n\n`))
        controller.close()
      } catch (error) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'error', message: (error as Error).message })}\n\n`))
        controller.close()
      }
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
*/
