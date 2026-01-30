# Mindrian Use-Case Register

> Every AI feature is listed. Every boundary is explicit.
> Last Updated: 2026-01-30

---

## Bot Registry

| Bot ID | Name | Risk Tier | Owner | Status |
|--------|------|-----------|-------|--------|
| `lawrence` | Lawrence | 1 | @jsagir | Active |
| `larry_playground` | Larry Playground | 2 | @jsagir | Active |
| `tta` | Trending to the Absurd | 2 | @jsagir | Active |
| `jtbd` | Jobs to Be Done | 2 | @jsagir | Active |
| `scurve` | S-Curve Analysis | 2 | @jsagir | Active |
| `redteam` | Red Teaming | 3 | @jsagir | Active |
| `ackoff` | Ackoff's DIKW Pyramid | 3 | @jsagir | Active |
| `bono` | BONO Master | 2 | @jsagir | Active |
| `knowns` | Known-Unknowns | 2 | @jsagir | Active |
| `domain` | Domain Selection | 1 | @jsagir | Active |
| `scenario` | Scenario Analysis | 2 | @jsagir | Active |
| `pws_investment` | PWS Investment | 3 | @jsagir | Active |
| `grading` | Minto Grading | 3 | @jsagir | Active |

---

## Detailed Use Cases

### lawrence (Tier 1 - Low Impact)

**Intended Uses:**
- General PWS thinking partner conversations
- Problem framing and exploration
- Framework introduction and guidance
- Directing users to specialized bots

**Allowed Actions:**
- ✅ Answer questions about PWS methodology
- ✅ Help frame problems
- ✅ Recommend frameworks/bots
- ✅ Basic web research (Tavily)
- ✅ Access PWS knowledge base (FileSearch)

**Forbidden Actions:**
- ❌ Make business decisions for user
- ❌ Provide financial/investment advice
- ❌ Provide legal advice
- ❌ Provide medical advice
- ❌ Grade or score user work (use grading bot)
- ❌ Access user data from other sessions

**Human Oversight:** None required (async feedback only)

---

### larry_playground (Tier 2 - Business Methodology)

**Intended Uses:**
- Full PWS exploration with all tools
- Deep research and multi-agent analysis
- Testing new features
- Power user workflows

**Allowed Actions:**
- ✅ All Lawrence capabilities
- ✅ Deep research (multi-query Tavily)
- ✅ Multi-agent analysis
- ✅ GraphRAG knowledge graph queries
- ✅ LangExtract structured extraction
- ✅ Generate visualizations/charts

**Forbidden Actions:**
- ❌ Make business decisions for user
- ❌ Provide financial/investment advice
- ❌ Provide legal advice
- ❌ Provide medical advice
- ❌ Execute actions outside Mindrian
- ❌ Access external systems without user knowledge

**Human Oversight:** User reviews multi-agent outputs

---

### tta (Tier 2 - Business Methodology)

**Intended Uses:**
- Trend extrapolation workshops
- Future scenario exploration
- Opportunity identification
- Presentism escape exercises

**Allowed Actions:**
- ✅ Guide TTA workshop phases
- ✅ Research trends (Tavily)
- ✅ Generate future scenarios
- ✅ Identify implications and opportunities
- ✅ Track workshop progress

**Forbidden Actions:**
- ❌ Predict specific future events with certainty
- ❌ Provide investment recommendations based on trends
- ❌ Make claims about timeline accuracy
- ❌ Present speculation as fact

**Human Oversight:** User validates scenario relevance

---

### jtbd (Tier 2 - Business Methodology)

**Intended Uses:**
- Customer job discovery
- Functional/emotional/social job mapping
- Competing solutions analysis
- Hiring criteria identification

**Allowed Actions:**
- ✅ Guide JTBD workshop phases
- ✅ Research customer segments
- ✅ Analyze competing solutions
- ✅ Extract job statements
- ✅ Generate interview questions

**Forbidden Actions:**
- ❌ Claim to know what specific customers want
- ❌ Replace actual customer research
- ❌ Make product decisions for user
- ❌ Present hypotheses as validated facts

**Human Oversight:** User validates against real customer data

---

### scurve (Tier 2 - Business Methodology)

**Intended Uses:**
- Technology lifecycle analysis
- Market timing assessment
- Disruption pattern recognition
- Strategic timing decisions

**Allowed Actions:**
- ✅ Guide S-Curve workshop phases
- ✅ Research technology maturity
- ✅ Analyze adoption patterns
- ✅ Identify transition points
- ✅ Generate timing recommendations

**Forbidden Actions:**
- ❌ Predict specific market timing with certainty
- ❌ Provide investment timing advice
- ❌ Claim accuracy on technology predictions
- ❌ Make go/no-go decisions for user

**Human Oversight:** User validates timing assumptions

---

### redteam (Tier 3 - High Stakes)

**Intended Uses:**
- Assumption stress-testing
- Strategy challenge sessions
- Weakness identification
- Pre-mortem analysis

**Allowed Actions:**
- ✅ Challenge user assumptions
- ✅ Identify logical weaknesses
- ✅ Generate counter-arguments
- ✅ Stress-test strategies
- ✅ Surface hidden risks

**Forbidden Actions:**
- ❌ Generate actual attack plans
- ❌ Provide hacking/security exploit guidance
- ❌ Create content that could cause real harm
- ❌ Challenge without constructive purpose
- ❌ Discourage user from pursuing valid ideas

**Human Oversight:** User must acknowledge challenge context

---

### ackoff (Tier 3 - High Stakes)

**Intended Uses:**
- DIKW pyramid validation
- Evidence-based reasoning
- Knowledge synthesis
- Wisdom application guidance

**Allowed Actions:**
- ✅ Guide DIKW workshop phases
- ✅ Assess evidence quality
- ✅ Identify data-to-wisdom gaps
- ✅ Challenge ungrounded claims
- ✅ Generate validation criteria

**Forbidden Actions:**
- ❌ Declare user's knowledge "valid" without evidence
- ❌ Make final business decisions
- ❌ Skip validation steps
- ❌ Present AI synthesis as user's validated knowledge

**Human Oversight:** User must validate evidence sources

---

### grading (Tier 3 - High Stakes)

**Intended Uses:**
- Problem definition quality assessment
- Minto Pyramid structure grading
- Evidence attribution scoring
- Feedback generation

**Allowed Actions:**
- ✅ Score against defined criteria
- ✅ Provide specific feedback
- ✅ Identify improvement areas
- ✅ Generate grade breakdowns
- ✅ Attribute evidence to sources

**Forbidden Actions:**
- ❌ Grade without showing criteria
- ❌ Provide grades without evidence
- ❌ Make pass/fail decisions with consequences
- ❌ Compare users to each other
- ❌ Store grades permanently without consent

**Human Oversight:** User reviews grade justification

---

### pws_investment (Tier 3 - High Stakes)

**Intended Uses:**
- Investment thesis evaluation
- Problem-worth-solving scoring
- Due diligence support
- Opportunity assessment

**Allowed Actions:**
- ✅ Analyze against PWS criteria
- ✅ Score investment opportunities
- ✅ Identify research gaps
- ✅ Generate due diligence questions
- ✅ Synthesize available evidence

**Forbidden Actions:**
- ❌ Provide investment recommendations
- ❌ Predict financial returns
- ❌ Replace professional financial advice
- ❌ Make buy/sell/hold recommendations
- ❌ Claim fiduciary responsibility

**Human Oversight:** Must disclaim "not financial advice"

---

## Tool Access Matrix

| Tool | lawrence | playground | tta | jtbd | scurve | redteam | ackoff | grading |
|------|----------|------------|-----|------|--------|---------|--------|---------|
| Tavily Search | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| FileSearch RAG | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| GraphRAG | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| LangExtract | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Multi-Agent | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Deep Research | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Charts/Viz | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Voice (TTS) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## Data Access Matrix

| Data Source | lawrence | playground | workshops | grading |
|-------------|----------|------------|-----------|---------|
| Neo4j (read) | ❌ | ✅ | ❌ | ✅ |
| Neo4j (write) | ❌ | ❌ | ❌ | ❌ |
| Supabase Storage | ✅ | ✅ | ✅ | ✅ |
| User Files (upload) | ✅ | ✅ | ✅ | ✅ |
| Session History | ✅ | ✅ | ✅ | ✅ |
| Other Users' Data | ❌ | ❌ | ❌ | ❌ |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-30 | Initial register created | Claude |

---

## Review Schedule

- **Monthly**: Review use cases for accuracy
- **Quarterly**: Review risk tier assignments
- **Per-Release**: Update for new bots/features
- **Incident-Driven**: Immediate review if misuse detected
