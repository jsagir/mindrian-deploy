// =============================================================================
// MINDRIAN NEO4J CYPHER QUERY TEMPLATES
// =============================================================================

// -----------------------------------------------------------------------------
// CONCEPT QUERIES
// -----------------------------------------------------------------------------

// Find concept by name (fuzzy match)
MATCH (c:Concept)
WHERE c.name =~ '(?i).*{search_term}.*'
RETURN c.id, c.name, c.description
LIMIT 10;

// Get concept with all relationships
MATCH (c:Concept {id: $concept_id})
OPTIONAL MATCH (c)-[r]-(related)
RETURN c, type(r) as relationship, related;

// Find related concepts (2-hop)
MATCH (c:Concept {name: $concept_name})-[:RELATED_TO*1..2]-(related:Concept)
WHERE c <> related
RETURN DISTINCT related.name, related.description
LIMIT 20;

// -----------------------------------------------------------------------------
// FRAMEWORK QUERIES
// -----------------------------------------------------------------------------

// List all frameworks
MATCH (f:Framework)
RETURN f.id, f.name, f.domain, f.description
ORDER BY f.name;

// Get framework with steps
MATCH (f:Framework {name: $framework_name})-[:CONTAINS]->(step:ProcessStep)
OPTIONAL MATCH (step)-[:FOLLOWS]->(next:ProcessStep)
RETURN f.name, step.order, step.action, step.description, next.action as next_step
ORDER BY step.order;

// Find frameworks for domain
MATCH (f:Framework)-[:APPLIES_TO]->(d:Domain {name: $domain_name})
RETURN f.name, f.description;

// -----------------------------------------------------------------------------
// CYNEFIN CLASSIFICATION
// -----------------------------------------------------------------------------

// Classify problem
MATCH (p:Problem {id: $problem_id})-[:CLASSIFIED_AS]->(d:CynefinDomain)
RETURN d.name as domain, d.characteristics, d.response_strategy;

// Find problems by domain
MATCH (p:Problem)-[:CLASSIFIED_AS]->(d:CynefinDomain {name: $domain_name})
RETURN p.id, p.description, p.created_at
ORDER BY p.created_at DESC
LIMIT 10;

// Get domain recommendations
MATCH (d:CynefinDomain {name: $domain_name})-[:RECOMMENDS]->(f:Framework)
RETURN f.name, f.description, f.applicability_score
ORDER BY f.applicability_score DESC;

// -----------------------------------------------------------------------------
// PREREQUISITE CHAINS
// -----------------------------------------------------------------------------

// Get all prerequisites for a concept
MATCH path = (c:Concept {name: $concept_name})-[:REQUIRES*]->(prereq:Concept)
RETURN [n IN nodes(path) | n.name] as prerequisite_chain
ORDER BY length(path);

// Find concepts that require this one
MATCH (dependent:Concept)-[:REQUIRES*]->(c:Concept {name: $concept_name})
RETURN dependent.name, dependent.description;

// -----------------------------------------------------------------------------
// LAZY GRAPH RAG
// -----------------------------------------------------------------------------

// Expand from vector search results
UNWIND $candidate_ids AS cid
MATCH (c:Concept {id: cid})
OPTIONAL MATCH (c)-[r:RELATED_TO|REQUIRES|APPLIES_TO]-(related)
RETURN c.id, c.name, type(r) as rel_type, related.id, related.name
LIMIT 50;

// Get context for retrieved chunks
UNWIND $chunk_ids AS chunk_id
MATCH (chunk:KnowledgeChunk {id: chunk_id})-[:PART_OF]->(doc:Document)
OPTIONAL MATCH (doc)-[:COVERS]->(topic:Concept)
RETURN chunk.id, doc.title, collect(topic.name) as topics;

// -----------------------------------------------------------------------------
// WORKFLOW SEQUENCING
// -----------------------------------------------------------------------------

// Get workflow steps in order
MATCH (w:Workflow {name: $workflow_name})-[:STARTS_WITH]->(first:ProcessStep)
MATCH path = (first)-[:FOLLOWS*0..20]->(step)
RETURN [s IN nodes(path) | {order: s.order, action: s.action}] as steps;

// Find dependencies for a step
MATCH (step:ProcessStep {id: $step_id})-[:DEPENDS_ON]->(dep:ProcessStep)
RETURN dep.id, dep.action, dep.status;

// -----------------------------------------------------------------------------
// ENTITY RESOLUTION
// -----------------------------------------------------------------------------

// Find or create canonical entity
MERGE (c:Concept {canonical_name: toLower(trim($name))})
ON CREATE SET 
  c.id = randomUUID(),
  c.name = $name,
  c.created_at = datetime()
ON MATCH SET
  c.aliases = CASE 
    WHEN NOT $name IN coalesce(c.aliases, []) 
    THEN coalesce(c.aliases, []) + $name 
    ELSE c.aliases 
  END
RETURN c.id, c.name, c.aliases;

// Merge duplicate concepts
MATCH (c1:Concept {id: $keep_id})
MATCH (c2:Concept {id: $merge_id})
WHERE c1 <> c2
// Transfer relationships
MATCH (c2)-[r]->(target)
MERGE (c1)-[newR:RELATED_TO]->(target)
// Transfer incoming relationships
MATCH (source)-[r]->(c2)
MERGE (source)-[newR:RELATED_TO]->(c1)
// Delete duplicate
DETACH DELETE c2
RETURN c1;

// -----------------------------------------------------------------------------
// ANALYTICS
// -----------------------------------------------------------------------------

// Most connected concepts
MATCH (c:Concept)
RETURN c.name, size((c)--()) as connection_count
ORDER BY connection_count DESC
LIMIT 10;

// Framework usage statistics
MATCH (f:Framework)<-[:USED]-(s:Session)
RETURN f.name, count(s) as usage_count
ORDER BY usage_count DESC;

// Knowledge graph statistics
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC;
