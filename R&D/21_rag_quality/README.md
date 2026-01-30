# R&D 21: RAG Quality Improvements

## Status: Research

## What Is This?

Techniques to improve retrieval accuracy and context relevance in the RAG pipeline.

## Why Implement This?

### Current State
- Basic vector similarity search
- Fixed chunk sizes
- No reranking
- Limited query expansion

### Solution: Advanced RAG
- Hybrid search (BM25 + vector)
- Cross-encoder reranking
- Query expansion and reformulation
- Optimized chunking strategies

## Improvement Areas

### 1. Hybrid Search
```python
# Combine keyword (BM25) and semantic (vector) search
def hybrid_search(query: str, k: int = 10):
    bm25_results = bm25_index.search(query, k=k*2)
    vector_results = vector_index.search(embed(query), k=k*2)

    # Reciprocal Rank Fusion
    return reciprocal_rank_fusion(bm25_results, vector_results, k=k)
```

### 2. Reranking
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, documents: list[str], top_k: int = 5):
    pairs = [(query, doc) for doc in documents]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:top_k]]
```

### 3. Query Expansion
```python
async def expand_query(query: str) -> list[str]:
    """Generate multiple query variations for better recall."""
    prompt = f"""
    Original query: {query}

    Generate 3 alternative phrasings that would retrieve relevant documents:
    1. More specific version
    2. More general version
    3. Synonym-based version
    """
    return await llm.generate(prompt)
```

### 4. Chunking Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| Fixed size (512 tokens) | Simple, consistent | May split context |
| Sentence-based | Natural boundaries | Variable sizes |
| Semantic (topic shifts) | Context-aware | Expensive to compute |
| Sliding window + overlap | Good recall | Redundancy |

### 5. Context Compression
```python
async def compress_context(documents: list[str], query: str) -> str:
    """Compress retrieved documents to most relevant parts."""
    prompt = f"""
    Query: {query}

    Documents:
    {documents}

    Extract only the sentences directly relevant to answering the query.
    """
    return await llm.generate(prompt)
```

## Current RAG Pipeline

1. User query → `tools/graphrag_lite.py`
2. Vector search in FileSearch
3. Neo4j framework discovery
4. Context assembly
5. LLM generation

## Research Resources

- [Advanced RAG Techniques](https://www.pinecone.io/learn/advanced-rag-techniques/)
- [RAG Fusion](https://github.com/Raudaschl/rag-fusion)
- [RAGAS](https://github.com/explodinggradients/ragas) - RAG evaluation
- [LlamaIndex](https://www.llamaindex.ai/) - Advanced RAG patterns
- [Cohere Rerank](https://cohere.com/rerank)

## Evaluation Metrics

| Metric | What It Measures |
|--------|------------------|
| Recall@K | Retrieved relevant docs in top K |
| MRR | Mean Reciprocal Rank |
| NDCG | Normalized Discounted Cumulative Gain |
| Faithfulness | LLM answer grounded in context |
| Relevance | Context relevance to query |

## Estimated Effort

- Research: 8-12 hours
- Implementation: 20-30 hours
- Evaluation: 10-15 hours

## Status Checklist

- [ ] Benchmark current RAG quality
- [ ] Implement hybrid search
- [ ] Add reranking layer
- [ ] Query expansion
- [ ] Chunking optimization
- [ ] Context compression
- [ ] Evaluation with RAGAS
- [ ] A/B testing

---

*Created: 2026-01-30*
