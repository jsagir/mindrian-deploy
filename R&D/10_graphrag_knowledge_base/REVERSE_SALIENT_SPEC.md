# Reverse Salient — Cross-Intersectional Innovation Discovery

**Status:** Planned (next phase)
**Depends on:** GraphRAG Lite MVP (complete), Graph cleanup (complete)

---

## What is a Reverse Salient?

A **reverse salient** is a component in an advancing system that has fallen behind or is out of phase with the rest. Originally a military metaphor (Thomas Hughes), it identifies bottlenecks that constrain entire systems.

In PWS methodology: reverse salients reveal **where innovation is most needed** — the gaps that, if closed, unlock disproportionate value.

---

## Current Graph Assets

| Asset | Count | Role |
|-------|-------|------|
| ReverseSalient nodes | 233 | Identified bottlenecks/gaps |
| Domain nodes | 85 | Knowledge domains for cross-pollination |
| InnovationOpportunity | 56 | Identified opportunities |
| BeautifulQuestion | 43 | Powerful inquiry prompts |
| Framework nodes | 267 | Methodologies that address problems |
| ProblemType nodes | 246 | Problem categories |
| ADDRESSES_PROBLEM_TYPE edges | 292 | Framework → ProblemType links |
| ALTERNATIVE_TO edges | 220 | Framework alternatives |
| COMPLEMENTS edges | 148 | Framework synergies |
| SIMILAR edges | 2,366 | Entity similarity |
| LazyGraphRAG communities | 39 | Concept clusters |

---

## Discovery Approach

### 1. Cross-Domain Bridge Detection

Find reverse salients that span multiple domains — these are cross-intersectional innovation hotspots.

```cypher
// ReverseSalients connected to 2+ Domains
MATCH (rs:ReverseSalient)-[:PART_OF|RELATES_TO|SIMILAR*1..2]-(d:Domain)
WITH rs, collect(DISTINCT d.name) AS domains
WHERE size(domains) >= 2
RETURN rs.name, domains
ORDER BY size(domains) DESC;
```

### 2. Community-Bridging Concepts

LazyGraphConcepts that appear in multiple communities act as bridges between idea clusters.

```cypher
// Concepts with CO_OCCURS edges spanning communities
MATCH (a:LazyGraphConcept)-[r:CO_OCCURS]-(b:LazyGraphConcept)
WHERE a.community_id <> b.community_id AND r.weight >= 3
RETURN a.name, a.community_id, b.community_id, r.weight
ORDER BY r.weight DESC LIMIT 50;
```

### 3. Framework Gap Analysis

Find ProblemTypes not addressed by any Framework.

```cypher
MATCH (pt:ProblemType)
WHERE NOT (pt)<-[:ADDRESSES_PROBLEM_TYPE]-(:Framework)
RETURN pt.name AS unaddressed_problem
ORDER BY pt.name;
```

### 4. Innovation Opportunity Clustering

Group InnovationOpportunity nodes by their connected domains and reverse salients.

```cypher
MATCH (io:InnovationOpportunity)-[*1..2]-(rs:ReverseSalient)
MATCH (io)-[*1..2]-(d:Domain)
RETURN io.name, rs.name AS bottleneck, d.name AS domain
ORDER BY io.name;
```

---

## Planned Tool: `reverse_salient_discovery()`

Will be added to `tools/graphrag_lite.py` or as a separate tool.

**Input:** User's problem domain or question
**Output:** Cross-domain insights showing:
- Related reverse salients
- Which domains they bridge
- What frameworks address nearby problems
- Beautiful questions to reframe the problem

---

## Open Questions

1. Should reverse salient discovery be automatic (like current enrichment) or user-triggered?
2. Should results feed into Larry's context or be a standalone tool?
3. What's the minimum ReverseSalient → Domain edge count needed for meaningful cross-domain insights?
