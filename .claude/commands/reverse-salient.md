# Reverse Salient Discovery

Discover cross-domain innovation opportunities using dual similarity analysis (LSA + BERT).

**Source:** `/home/jsagi/Mindrian/Cross Domain RS/`

## Quick Start

```bash
# Full pipeline
python run_pipeline.py documents_raw.json ./results --threshold 0.30
```

## Architecture

```
10-Stage Pipeline: INGEST → EXTRACT → GRAPH WRITE → GRAPH QUERY →
                   ENRICH → COMPUTE → DETECT → VALIDATE → STORE → OUTPUT

Detection: |BERT - LSA| ≥ 0.30
Scoring: breakthrough_potential = (differential × 0.7) + (min(LSA,BERT) × 0.3)
```

## Key Files

- `agent_config.py` - Full Mindrian agent config
- `run_pipeline.py` - Pipeline orchestrator
- `clean_documents.py` - Preprocessing
- `compute_lsa.py` - Structural similarity
- `compute_bert.py` - Semantic similarity
- `detect_reverse_salients.py` - Detection & scoring
- `visualize_results.py` - Visualization

Help with reverse salient discovery: $ARGUMENTS
