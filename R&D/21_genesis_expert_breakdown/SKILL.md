---
name: expert-breakdown
description: >
  Genesis-powered multi-domain expert breakdown and breakthrough discovery engine. Decomposes
  complex challenges into semantic segments, identifies relevant expertise domains, generates
  expert personas, orchestrates parallel research, conducts structured expert panel discussions,
  synthesizes cross-domain breakthroughs, and produces implementation roadmaps. Use for: strategic
  ventures spanning multiple domains, technology convergence analysis, cross-industry innovation
  discovery, geopolitical-business intersections, complex multi-stakeholder challenges, and any
  problem requiring multi-perspective expert synthesis. Triggers: "expert breakdown", "genesis
  engine", "multi-domain analysis", "expert panel", "breakthrough synthesis", "cross-domain",
  "expert personas", "domain experts", "multi-perspective", "complex challenge", "genesis
  analysis", "breakthrough discovery", "integration architect".
---

# Expert Breakdown Engine

Genesis-powered system that transforms complex multi-domain challenges into structured
expert analysis, cross-domain breakthroughs, and actionable implementation roadmaps.

## What This Skill Does

- **Decomposes complexity**: Breaks challenges into semantic segments and extracts core
  elements (concepts, technologies, methodologies, challenges, opportunities) with
  automated complexity scoring

- **Identifies expertise domains**: Pattern-matches against 24 domain signatures (14
  technical + 10 non-technical) with subdomain discovery and confidence scoring

- **Generates expert personas**: Creates domain-specific experts with competency matrices,
  research strategies, and collaboration styles — using expertise-based naming, never real
  human names

- **Orchestrates parallel research**: Executes targeted searches through each expert's
  lens, building cross-reference maps and collaboration matrices

- **Synthesizes breakthroughs**: Scores opportunities using weighted multi-criteria model,
  validates against evidence and cross-domain gates, and ranks by composite score

## Quick Start

### Full Expert Breakdown (~45-65 min)

1. **Describe your challenge** (2-5 min) — Provide detailed context about your
   multi-domain challenge
2. **Review domain map** (2 min) — Confirm or adjust identified domains at checkpoint
3. **Expert research executes** (15-25 min) — Parallel Tavily searches through each
   expert's lens
4. **Expert panel discussion** (15-20 min) — 4-round structured synthesis with
   opportunity to ask experts
5. **Receive breakthrough report** (5 min) — Ranked opportunities with implementation
   roadmaps

### Minimum Requirements

- Challenge description with 50+ characters
- Challenge should span 2+ distinct domains for best results
- More context = richer expert perspectives

## Step-by-Step Workflow

### Step 1: Context Decomposition

The engine segments your challenge into coherent chunks and extracts core elements.

```bash
python scripts/decompose_context.py challenge.txt decomposition.json
```

**Output**: `decomposition.json` with segments, elements, and complexity score.

### Step 2: Domain Identification

Pattern-matches against domain signatures and discovers subdomains.

```bash
python scripts/identify_domains.py decomposition.json domains.json
```

**Output**: `domains.json` with primary, technical, adjacent, and methodological domains.

**Checkpoint**: You'll confirm or adjust the domain map before proceeding.

### Step 3: Expert Persona Generation

Creates domain experts with full competency profiles and research strategies.

```bash
python scripts/generate_personas.py domains.json decomposition.json personas.json
```

**Output**: `personas.json` with expert profiles including query strategies.

### Step 4: Research Orchestration

Generates execution plan with collaboration matrix and quality controls.

```bash
python scripts/orchestrate_research.py personas.json --context challenge.txt research_plan.json
```

**Output**: `research_plan.json` with phases, interactions, and timeline.

### Step 5: Expert Panel (conducted by agent)

4-round structured discussion:
1. Domain Presentations — each expert presents findings
2. Cross-Domain Connections — identify synergies and conflicts
3. Breakthrough Ideation — collaborative opportunity design
4. Implementation Planning — concrete next steps

**Checkpoint**: You can ask the experts questions during the panel.

### Step 6: Breakthrough Synthesis

Scores, validates, and ranks breakthrough opportunities.

```bash
python scripts/synthesize_breakthroughs.py findings.json synthesis.json --min-score 5.0
```

**Output**: `synthesis.json` with ranked breakthroughs and implementation roadmaps.

## Interpreting Results

### Understanding Scores

Each breakthrough is scored on a 0-10 composite scale:

| Score Range | Classification | Meaning |
|-------------|---------------|---------|
| 8.0-10.0 | Exceptional | High-confidence breakthrough with clear implementation |
| 6.5-7.9 | Strong | Solid opportunity, may need additional validation |
| 5.0-6.4 | Promising | Worth investigating, needs more evidence |
| < 5.0 | Below threshold | Filtered out by default |

### Scoring Weights

| Criterion | Weight | What It Measures |
|-----------|--------|-----------------|
| Breakthrough Potential | 35% | How novel and transformative is this? |
| Feasibility | 25% | Can it actually be built/implemented? |
| Cross-Domain Impact | 25% | How many domains benefit? |
| Time to Value | 15% | How quickly does it deliver results? |

### Validation Gates

Every breakthrough must pass three gates:
- **Gate 2 (Evidence)**: Must have supporting research sources
- **Gate 3 (Cross-Domain)**: Must emerge from 2+ domain intersection
- **Gate 4 (Implementation)**: Must include concrete next steps

### Quality Indicators

**Good session**: 3-5 validated breakthroughs with scores > 6.5, clear cross-domain
connections, specific implementation steps, documented expert disagreements.

**Poor session**: All breakthroughs fail validation, no cross-domain connections found,
vague implementation steps, single-domain insights only.

## Script Reference

| Script | Stage | Input | Output |
|--------|-------|-------|--------|
| `decompose_context.py` | 1 | .txt or .json | decomposition.json |
| `identify_domains.py` | 2 | decomposition.json | domains.json |
| `generate_personas.py` | 3 | domains.json + decomposition.json | personas.json |
| `orchestrate_research.py` | 4 | personas.json | research_plan.json |
| `synthesize_breakthroughs.py` | 6 | findings.json | synthesis.json |

### Key Parameters

- `--max-segment 300` (decompose): Max characters per segment
- `--min-score 5.0` (synthesize): Minimum composite score threshold
- `--max-breakthroughs 5` (synthesize): How many top opportunities to return
- `--context challenge.txt` (orchestrate): Original text for reference

## Tips for Success

1. **Provide rich context**: The more detail about your challenge, the better the domain
   identification and expert generation
2. **Confirm domains carefully**: The Stage 2 checkpoint is your chance to steer the
   analysis — add or remove domains here
3. **Ask experts questions**: During the panel checkpoint, engage with specific experts
   to deepen particular angles
4. **Trust cross-domain insights**: The most valuable breakthroughs often come from
   unexpected domain intersections
5. **Use the Neo4j graph**: Existing DomainBridge and CrossDomainInnovation nodes provide
   prior art and inspiration

## Neo4j Integration

### Read Operations
- Find existing domain experts and perspectives
- Discover domain bridges between identified domains
- Retrieve prior cross-domain innovations
- Look up applicable frameworks
- Explore reverse salients in domain intersections

### Write Operations
- Save generated expert personas (DomainExpert)
- Store discovered innovations (CrossDomainInnovation, BreakthroughInnovation)
- Record synthesis results (BreakthroughSynthesis)
- Create domain bridges (DomainBridge)
- All writes use MERGE and are tagged `added_by='expert-breakdown-agent'`

## Output Checklist

- [ ] Context decomposed with complexity scoring
- [ ] Domain map identified and confirmed by user
- [ ] Expert personas generated with query strategies
- [ ] Research executed through each expert's lens
- [ ] 4-round expert panel discussion completed
- [ ] Breakthroughs scored, validated, and ranked
- [ ] Implementation roadmaps with milestones
- [ ] Risk assessment with mitigation strategies
- [ ] Findings written to Neo4j knowledge graph

## Integration with Other Skills

- **Domain Explorer** — Use for single-domain deep dives when Expert Breakdown identifies
  a domain needing more investigation
- **Devil's Advocate** — Run bias check on breakthrough claims
- **Known-Unknowns** — Map uncertainty around top opportunities
- **PWS Investment Analysis** — Deep-dive financial viability of top breakthroughs
- **Reverse Salient Discovery** — Computational cross-domain opportunity detection
