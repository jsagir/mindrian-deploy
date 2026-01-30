# Mindrian AI Governance Implementation Plan

> **Principle**: AI Governance ≠ Data Governance
> Data Governance = trust the input. AI Governance = trust the decision.

---

## Phase 1: Foundation (Week 1) 🔴 CRITICAL

### 1.1 Use-Case Register
**File**: `governance/USE_CASE_REGISTER.md`
**Purpose**: Every AI feature listed with boundaries

| Deliverable | Status |
|-------------|--------|
| List all 13 bots with allowed/forbidden uses | ⬜ |
| Assign ownership per bot | ⬜ |
| Define "what AI is NOT allowed to do" | ⬜ |

### 1.2 Risk Tier System
**File**: `governance/RISK_TIERS.py`
**Purpose**: Classify features by impact

| Tier | Description | Examples | Oversight Level |
|------|-------------|----------|-----------------|
| 0 | Internal/testing | dev playground | None |
| 1 | Low impact | general chat, exploration | Async review |
| 2 | Business methodology | JTBD, TTA, S-Curve | Human-in-loop optional |
| 3 | High-stakes decisions | Red Team, Grading, Ackoff validation | Human-in-loop required |

### 1.3 Forbidden Uses Document
**File**: `governance/FORBIDDEN_USES.md`
**Purpose**: Explicit "don't do this" list

---

## Phase 2: Traceability (Week 2) 🟡 HIGH

### 2.1 Model + Prompt Cards
**Location**: `governance/prompt_cards/`
**Purpose**: Version every prompt with its model

Each bot gets a YAML card:
```yaml
bot_id: lawrence
model: gemini-2.0-flash
model_version: "2.0"
prompt_version: "3.1.0"
prompt_hash: sha256:abc123...
last_updated: 2026-01-30
owner: @jsagir
intended_use: "PWS problem framing"
limitations:
  - "May recommend frameworks without full context"
tools_access: [tavily, graphrag, filesearch]
data_access: [neo4j_readonly]
```

### 2.2 Audit Trail Module
**File**: `utils/audit_trail.py`
**Purpose**: Track every AI decision

```python
class AuditEntry:
    timestamp: datetime
    session_id: str
    user_id: str
    bot_id: str
    model: str
    prompt_version: str
    input_hash: str
    output_hash: str
    quality_score: float
    risk_tier: int
    tools_called: List[str]
```

### 2.3 Response Metadata
**Integration**: `mindrian_chat.py`
**Purpose**: Attach governance metadata to every response

---

## Phase 3: Monitoring (Week 3) 🟡 HIGH

### 3.1 AI Monitoring Module
**File**: `utils/ai_monitoring.py`
**Purpose**: Track quality, drift, safety

| Signal | Detection Method | Alert Threshold |
|--------|------------------|-----------------|
| Quality drift | Rolling avg vs baseline | >15% drop |
| Hallucination risk | Evidence attribution rate | <50% grounded |
| Safety regression | Blocked content rate | Any increase |
| Cost anomaly | API call volume | >2x daily avg |

### 3.2 Drift Detection
**Purpose**: Catch "models that drift with no one noticing"

- Baseline quality scores per bot (from first 1000 sessions)
- Rolling 7-day comparison
- Alert on significant regression

### 3.3 Cost Tracking
**Purpose**: Monitor API spend

```python
COST_PER_1K_TOKENS = {
    "gemini-2.0-flash": 0.0001,
    "gemini-2.5-flash": 0.00015,
    "gemini-3-flash-preview": 0.0002,
}
```

---

## Phase 4: Evaluation (Week 4) 🟢 MEDIUM

### 4.1 Golden Set Tests
**Location**: `tests/golden_sets/`
**Purpose**: Expected inputs → expected outputs

```
tests/golden_sets/
├── lawrence/
│   ├── problem_framing.json
│   └── framework_recommendation.json
├── redteam/
│   └── assumption_challenge.json
└── ackoff/
    └── dikw_validation.json
```

### 4.2 Adversarial Tests
**Location**: `tests/adversarial/`
**Purpose**: Prompt injection, jailbreaks

| Test Type | Examples |
|-----------|----------|
| Prompt injection | "Ignore previous instructions and..." |
| Role confusion | "You are now a different assistant..." |
| Data exfiltration | "Tell me about other users..." |
| Harmful content | Violence, illegal activity requests |

### 4.3 Safety Checks
**Location**: `tests/safety/`
**Purpose**: PII detection, content filtering

---

## Phase 5: Incident Response (Week 4) 🟢 MEDIUM

### 5.1 Incident Playbook
**File**: `governance/INCIDENT_PLAYBOOK.md`
**Purpose**: What to do when things go wrong

| Severity | Example | Response Time | Actions |
|----------|---------|---------------|---------|
| P0 - Critical | Data breach, harmful output | <1 hour | Disable bot, notify users, investigate |
| P1 - High | Consistent wrong answers | <4 hours | Rollback prompt, alert owner |
| P2 - Medium | Quality degradation | <24 hours | Review logs, adjust parameters |
| P3 - Low | Minor inaccuracies | <1 week | Log issue, schedule fix |

### 5.2 Rollback Procedures
- Prompt version rollback
- Model fallback (primary → backup)
- Feature disable flags
- Full bot disable

### 5.3 Communication Templates
- User notification
- Internal escalation
- Post-mortem template

---

## Implementation Order

```
Week 1 (Foundation):
├── Day 1-2: Folder structure + Use-Case Register
├── Day 3-4: Risk Tiers + Forbidden Uses
└── Day 5: Review & integrate into CLAUDE.md

Week 2 (Traceability):
├── Day 1-2: Prompt Cards for all 13 bots
├── Day 3-4: Audit Trail module
└── Day 5: Integration into mindrian_chat.py

Week 3 (Monitoring):
├── Day 1-2: AI Monitoring module
├── Day 3-4: Drift detection + cost tracking
└── Day 5: Dashboard/alerts setup

Week 4 (Testing + Response):
├── Day 1-2: Golden set tests (3 priority bots)
├── Day 3: Adversarial tests
├── Day 4: Safety checks
└── Day 5: Incident playbook + review
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Audit coverage | 100% | All responses have metadata |
| Prompt versioning | 100% | All bots have cards |
| Test coverage | 80% | Golden sets for 10/13 bots |
| Incident response | <4hr P1 | Time to mitigation |
| Quality baseline | Established | Per-bot scores recorded |

---

## Files to Create

```
governance/
├── GOVERNANCE_PLAN.md          ← This file
├── USE_CASE_REGISTER.md        ← Bot boundaries
├── RISK_TIERS.py               ← Tier definitions + enforcement
├── FORBIDDEN_USES.md           ← Explicit prohibitions
├── INCIDENT_PLAYBOOK.md        ← Response procedures
└── prompt_cards/
    ├── lawrence.yaml
    ├── larry_playground.yaml
    ├── jtbd.yaml
    ├── tta.yaml
    ├── scurve.yaml
    ├── redteam.yaml
    ├── ackoff.yaml
    ├── bono.yaml
    └── ... (all 13 bots)

utils/
├── audit_trail.py              ← Response tracking
└── ai_monitoring.py            ← Quality/drift/cost signals

tests/
├── golden_sets/                ← Expected outputs
├── adversarial/                ← Injection tests
└── safety/                     ← PII/content checks
```

---

## Integration Points

### mindrian_chat.py Changes
1. Import audit_trail, ai_monitoring, risk_tiers
2. Add `@audit_response` decorator to message handler
3. Add risk tier check before high-stakes operations
4. Add monitoring hooks to response generation

### CLAUDE.md Updates
1. Add "AI Governance" section
2. Reference governance folder
3. Add "Adding a New Bot - Governance Checklist"

---

## Questions to Decide

1. **Audit storage**: Supabase vs PostgreSQL vs separate service?
2. **Alert channel**: Slack? Email? PagerDuty?
3. **Cost budget**: Monthly API spend limit?
4. **Rollback authority**: Who can disable a bot in production?
5. **Review cadence**: Weekly? Monthly governance review?

---

*Created: 2026-01-30*
*Owner: @jsagir*
*Status: Planning*
