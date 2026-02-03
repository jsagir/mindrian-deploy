# Reverse Salient Discovery

Discover cross-domain innovation opportunities using dual similarity analysis (LSA + BERT).

**Source:** `/home/jsagi/Mindrian/Cross Domain RS/`

## When to Use

- Finding innovation opportunities between two research domains
- Identifying technology transfer potential
- Detecting structural vs semantic gaps in cross-disciplinary research
- Running dual similarity analysis on academic papers (150-300 docs)

## Quick Start

```bash
# Full pipeline
python run_pipeline.py documents_raw.json ./results --threshold 0.30

# Individual stages
python clean_documents.py raw.json cleaned.json
python compute_lsa.py cleaned.json lsa.npy
python compute_bert.py cleaned.json bert.npy
python detect_reverse_salients.py lsa.npy bert.npy cleaned.json
python visualize_results.py lsa.npy bert.npy results.json ./outputs
```

## Architecture

```
10-Stage Pipeline: INGEST → EXTRACT → GRAPH WRITE → GRAPH QUERY →
                   ENRICH → COMPUTE → DETECT → VALIDATE → STORE → OUTPUT

Detection Formula: |BERT - LSA| ≥ 0.30 (adjustable 0.25-0.40)
Scoring: breakthrough_potential = (differential × 0.7) + (min(LSA,BERT) × 0.3)
```

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `agent_config.py` | Full Mindrian agent config (Components A-N) | 1,158 |
| `run_pipeline.py` | Pipeline orchestrator | 268 |
| `clean_documents.py` | Preprocessing (Stage 1) | 215 |
| `compute_lsa.py` | Structural similarity (Stage 2A) | 259 |
| `compute_bert.py` | Semantic similarity (Stage 2B) | 272 |
| `detect_reverse_salients.py` | Detection & scoring (Stage 3) | 287 |
| `visualize_results.py` | Visualization (Stage 4) | 241 |

## Neo4j Integration

**Reads from:** ReverseSalient, CrossDomainInnovation, BeautifulQuestion, DomainBridge, InnovationTool (14 node types)

**Writes to:** ReverseSalient, CrossDomainInnovation, Innovation, BeautifulQuestion, DomainBridge (via MERGE + tagging)

## Outputs

- `reverse_salients.json` — Ranked opportunities with scores
- `lsa_similarity.npy` — Structural similarity matrix
- `bert_similarity.npy` — Semantic similarity matrix
- `lsa_topics.json` — 80 discovered topics
- 4 PNG visualizations (heatmaps, scatter, distribution)

## Classification

- **Structural Transfer** (LSA > BERT): Domains share methods but not meaning
- **Semantic Implementation** (BERT > LSA): Domains share meaning but not methods

## Quality Thresholds

| Differential | Quality |
|--------------|---------|
| > 0.40 | Exceptional opportunity |
| 0.30-0.40 | Strong opportunity |
| 0.25-0.30 | Moderate (needs validation) |
| < 0.25 | Weak signal |

$ARGUMENTS
