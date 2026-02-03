---
description: Discover cross-domain innovation using dual similarity (LSA + BERT). Use for technology transfer, research gaps, breakthrough opportunities.
---

# Reverse Salient Discovery

Source: `/home/jsagi/Mindrian/Cross Domain RS/`

## Quick Start

```bash
python run_pipeline.py documents_raw.json ./results --threshold 0.30
```

## Pipeline

```
INGEST → EXTRACT → GRAPH → COMPUTE (LSA+BERT) → DETECT → VALIDATE → OUTPUT
```

## Detection Formula

- Differential: |BERT - LSA| ≥ 0.30
- Both matrices must be ≥ 0.20
- Breakthrough potential = (differential × 0.7) + (min × 0.3)

## Scripts

- `clean_documents.py` - Preprocess
- `compute_lsa.py` - Structural similarity
- `compute_bert.py` - Semantic similarity
- `detect_reverse_salients.py` - Find opportunities
- `visualize_results.py` - Generate charts

$ARGUMENTS
