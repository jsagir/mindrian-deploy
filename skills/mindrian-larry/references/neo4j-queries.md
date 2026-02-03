# Larry's Neo4j Query Patterns

Quick-reference queries Larry uses to ground recommendations in the PWS knowledge graph.

## Connection Info
```
Database: my-neo4j
Total Nodes: 5,797+
Key Labels: Framework, Book, Concept, ProblemType, Technique, DictionaryTerm
```

---

## Most Used Queries

### 1. Framework for Problem Type
**When**: User describes a challenge, need to recommend appropriate framework

```cypher
MATCH (f:Framework)-[:ADDRESSES_PROBLEM_TYPE]->(pt:ProblemType)
WHERE pt.name CONTAINS $problemType
RETURN f.name, pt.name
ORDER BY f.name
LIMIT 10
```

**Example usage**:
- `$problemType = "ill-defined"` → JTBD, Four Lenses, Mom Test
- `$problemType = "un-defined"` → Scenario Planning, TTA
- `$problemType = "well-defined"` → Business Model Canvas, Lean Startup
- `$problemType = "wicked"` → Leverage Points, Systems Thinking

---

### 2. Concept Definition
**When**: User asks "what is X?" or uses unfamiliar term

```cypher
MATCH (c:Concept)
WHERE c.name CONTAINS $concept
RETURN c.name, c.description
LIMIT 5
```

**Also try DictionaryTerm**:
```cypher
MATCH (d:DictionaryTerm)
WHERE d.name CONTAINS $term
RETURN d.name, d.definition
```

---

### 3. Related Concepts
**When**: Need to explore connected ideas

```cypher
MATCH (c:Concept)-[r]-(related)
WHERE c.name CONTAINS $concept
RETURN c.name, type(r), labels(related)[0] as type, related.name
LIMIT 20
```

---

### 4. Framework Details
**When**: Need to explain a specific framework

```cypher
MATCH (f:Framework {name: $name})-[r]-(connected)
WHERE NOT connected:__Entity__
RETURN f.name, type(r), labels(connected)[0] as type, connected.name
LIMIT 30
```

---

### 5. Book Recommendation
**When**: User needs reading suggestion

```cypher
// Books teaching a specific framework
MATCH (b:Book)-[:TEACHES|INTRODUCES]->(f:Framework)
WHERE f.name CONTAINS $framework
RETURN b.name, b.author, f.name

// Books for a problem type
MATCH (b:Book)-[:TEACHES]->(f:Framework)-[:ADDRESSES_PROBLEM_TYPE]->(pt:ProblemType)
WHERE pt.name CONTAINS $problemType
RETURN DISTINCT b.name, b.author
LIMIT 5
```

---

### 6. Technique Lookup
**When**: Need specific method or tool

```cypher
MATCH (t:Technique)
WHERE t.name CONTAINS $technique
RETURN t.name, t.description
LIMIT 10
```

---

### 7. Problem Type Overview
**When**: Explaining the taxonomy

```cypher
MATCH (pt:ProblemType)
RETURN pt.name, pt.description
ORDER BY pt.name
```

---

## Exploration Queries

### Discover Unknown Connections
```cypher
MATCH path = shortestPath((a)-[*1..3]-(b))
WHERE a.name CONTAINS $termA AND b.name CONTAINS $termB
RETURN path
```

### Find Everything About a Topic
```cypher
MATCH (n)
WHERE n.name CONTAINS $topic
RETURN labels(n)[0] as type, n.name
LIMIT 20
```

### Explore Node Neighborhood
```cypher
MATCH (n)-[r]-(connected)
WHERE n.name = $nodeName
RETURN n.name, type(r), labels(connected)[0], connected.name
LIMIT 50
```

---

## Query Patterns for Common Questions

| User Question | Query Pattern |
|---------------|---------------|
| "What framework should I use?" | Framework for Problem Type |
| "What does X mean?" | Concept Definition or DictionaryTerm |
| "How does X relate to Y?" | Related Concepts |
| "Tell me about [framework]" | Framework Details |
| "What should I read?" | Book Recommendation |
| "How do I do [method]?" | Technique Lookup |
| "What are the problem types?" | Problem Type Overview |

---

## Larry's Query Workflow

1. **Identify query need** from user question
2. **Select appropriate pattern** from above
3. **Execute query** via Neo4j tools
4. **Interpret results** in context of user's situation
5. **Cite source** in response ("According to the knowledge graph...")

---

## Tips

### Parameter Formatting
- Use `CONTAINS` for partial matching: `WHERE n.name CONTAINS 'JTBD'`
- Case matters sometimes - try both cases
- Use `toLower()` for case-insensitive: `WHERE toLower(n.name) CONTAINS toLower($term)`

### Performance
- Always use `LIMIT` for exploratory queries
- Start with small limits (5-10), expand if needed
- Avoid open-ended traversals: `MATCH ()-[*]->()`

### Common Issues
- Node not found? Try different label (Concept vs DictionaryTerm vs Framework)
- Too many results? Add more specific filters
- No relationships? Check if node has any: `MATCH (n)-[r]-() WHERE n.name = $name RETURN count(r)`
