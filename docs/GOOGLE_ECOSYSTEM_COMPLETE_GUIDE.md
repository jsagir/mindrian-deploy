# Going all-in on Google: A complete ecosystem guide for Mindrian

**Google Cloud offers a compelling all-in-one platform for AI-powered educational applications**, with native Gemini integration, enterprise-grade security, and startup credits up to **$350K**. Mindrian can successfully migrate from its current Supabase/Neo4j/LangExtract stack to a unified Google ecosystem while gaining significant AI capabilities—particularly through Vertex AI Agent Builder and the newly available NotebookLM Enterprise API. The migration path is well-defined: start with Cloud Run deployment, adopt ADK for agent orchestration, use AlloyDB for PostgreSQL-compatible vector search, and leverage URL Context Grounding to simplify RAG implementations.

---

## Gemini API: The AI foundation in 2025

Google's Gemini API has matured into a comprehensive AI platform with models optimized for every use case—from **Flash-Lite at $0.10/million tokens** for high-volume classification to **2.5 Pro at $1.25/million** for complex reasoning tasks.

### Model selection strategy for Mindrian

| Model | Context Window | Best Use Case | Input Price (per 1M) |
|-------|---------------|---------------|---------------------|
| **Gemini 2.5 Flash** | 1M tokens | Primary coaching interactions | $0.30 |
| **Gemini 2.5 Pro** | 1M tokens | Complex assessments, reasoning | $1.25-$2.50 |
| **Gemini 2.5 Flash-Lite** | 1M tokens | Classification, quizzes, routing | $0.10 |
| **Gemini 2.5 Flash Live** | 131K tokens | Real-time voice tutoring | $3.00 (audio) |

The **1-million-token context window** across all 2.5 models enables processing entire textbooks or course curricula in a single prompt. For Mindrian, this means an AI coach can reference all prior coaching sessions, user goals, and relevant materials simultaneously.

### Context caching delivers 90% cost savings

Explicit caching allows pre-loading static content—course syllabi, coaching frameworks, assessment rubrics—and reusing them across requests at dramatically reduced cost. Cached input pricing drops to **$0.03-$0.125 per million tokens**, representing up to **90% savings** versus standard input pricing.

```python
# Cache coaching methodology once, reuse across sessions
cache = client.caches.create(
    model="gemini-2.5-flash",
    contents=[coaching_framework, assessment_rubrics, course_materials],
    ttl="3600s"  # 1-hour TTL, configurable
)

# Each user session references cached content
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[user_message],
    config={"cached_content": cache.name}
)
```

**Minimum requirements**: 1,024 tokens for Flash, 2,048 for Pro. TTL defaults to 1 hour with no maximum limit.

### Function calling and MCP support enable tool integration

All Gemini 2.5+ models support **parallel function calling** and the **Model Context Protocol (MCP)**, allowing agents to interact with external systems, databases, and APIs. MCP integration is built into the Python and JavaScript SDKs:

```python
from google import genai
from mcp import ClientSession

# MCP server provides tools automatically
async with mcp_client:
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_query,
        config=genai.types.GenerateContentConfig(
            tools=[mcp_client.session]  # Pass MCP session as tool
        )
    )
```

### Grounding options simplify knowledge retrieval

**Google Search Grounding** provides real-time information with citations at **$35/1,000 prompts** (1,500 free daily). **URL Context Grounding** processes up to **20 URLs per request** (34MB each) for document understanding without traditional RAG infrastructure—supporting PDF, HTML, JSON, CSV, and images.

For Mindrian, URL Context can handle:
- Public coaching resources and research papers
- Shared PDF assessments and reports
- Web-based learning materials

However, **traditional RAG remains necessary** for private documents, proprietary methodologies, and content behind authentication.

### The Live API enables real-time voice coaching

The Live API supports **bidirectional WebSocket streaming** for voice conversations with sub-second latency. Key specifications include 30 HD voices across 24 languages, 10-minute session limits (configurable), and native audio processing without STT→LLM→TTS pipeline overhead.

---

## Vertex AI Platform: Enterprise agent infrastructure

Vertex AI Agent Builder provides the **complete lifecycle** for building, deploying, and governing AI agents—with the Agent Development Kit (ADK) serving as the open-source foundation.

### ADK enables production agents in under 100 lines

ADK is a code-first Python framework (also available in Java, Go, TypeScript) optimized for Gemini but supporting any LLM. It offers hierarchical multi-agent architectures, workflow agents (Sequential, Parallel, Loop), and built-in evaluation tools.

```python
from google.adk.agents import LlmAgent

# Mindrian coaching agent with existing prompts
coach = LlmAgent(
    model="gemini-2.5-flash",
    name="mindrian_coach",
    instruction="""You are an AI coach helping users develop skills...""",
    tools=[assessment_tool, scheduling_tool, feedback_tool]
)

# Deploy locally or to Agent Engine
adk run coach
```

**Migration from custom architecture** is straightforward: wrap existing Gemini prompts in `LlmAgent` classes, convert tools to ADK function tools, then deploy to Agent Engine for managed scaling.

### Agent Engine provides managed runtime

Agent Engine handles infrastructure automatically—**session management** for conversation continuity, **Memory Bank** for long-term personalization, and **auto-scaling** based on workload. Pricing: **$0.0864/vCPU-hour** and **$0.0090/GB-hour**.

Key capabilities for Mindrian:
- **Sessions**: Persist coaching conversations across interactions
- **Memory Bank**: Store user goals, progress, preferences long-term
- **Code Execution**: Secure sandbox for data analysis exercises

### Agent2Agent protocol enables multi-agent systems

The A2A protocol (Linux Foundation, 150+ supporting organizations) allows agents to discover capabilities and collaborate regardless of framework. For Mindrian, specialized agents (assessment, feedback, scheduling, content) can coordinate through standardized interfaces.

### Vertex AI RAG Engine versus Gemini File Search

| Feature | RAG Engine | Gemini File API |
|---------|-----------|-----------------|
| Scale | Enterprise (large corpora) | Small-medium files |
| Persistence | Permanent corpus | Temporary |
| Customization | Full control over chunking, embeddings | Limited |
| Best for | Production knowledge bases | Prototyping, simple use cases |

RAG Engine provides managed corpus creation with automatic chunking, embedding, and retrieval—integrating natively with Gemini for grounded responses. Data connectors include Cloud Storage, BigQuery, Google Drive, Slack, and Jira.

---

## Google Workspace APIs: Collaboration infrastructure

All Workspace APIs are **free to use** beyond the Workspace subscription cost. For an educational platform, this provides document management, meeting integration, and real-time collaboration without per-API charges.

### Drive API enables document management

Core capabilities include programmatic file/folder CRUD, sharing permissions (reader→owner), and **real-time change detection** via watch webhooks. Export formats support converting Google Docs to PDF, DOCX, HTML, and more.

**Watch API** provides push notifications:
- `files.watch`: 24-hour max TTL per subscription
- `changes.watch`: 7-day max TTL
- Event types: add, update, trash, permission changes

### Meet API: Recordings and transcripts

**Pricing**: Free with Workspace Business Standard+ subscription

| Feature | API Access | Limitations |
|---------|-----------|-------------|
| Recordings | Post-meeting via Drive | Cannot start programmatically |
| Transcripts | `conferenceRecords.transcripts.entries` | 5-minute timestamp granularity, 30-day retention |
| Participants | `conferenceRecords.participants` | Join/leave tracking per device |

**Critical limitation**: Recording must be started manually by a meeting participant. For automated recording, consider third-party solutions like Recall.ai.

### Workspace Events API enables real-time sync

Currently in **Developer Preview**, this API delivers events via Pub/Sub for near real-time notifications:

```javascript
// Subscribe to Drive folder changes
const subscription = {
    targetResource: "//drive.googleapis.com/drives/FOLDER_ID",
    eventTypes: [
        "google.workspace.drive.file.v3.created",
        "google.workspace.drive.file.v3.updated"
    ],
    notificationEndpoint: {
        pubsubTopic: "projects/PROJECT_ID/topics/TOPIC"
    }
};
```

Enrollment in the Developer Preview Program is required. Subscription TTLs range from 4 hours (with resource data) to 7 days (resource name only).

---

## Document processing and knowledge management

### Document AI processes educational materials

Enterprise Document OCR handles **200+ languages** at **$1.50/1,000 pages**, with add-ons for:
- **Math OCR**: Extracts formulas in LaTeX format ($6/1,000 pages)
- **Checkbox extraction**: Marked/unmarked status detection
- **Layout Parser**: Structured content extraction ($10/1,000 pages)

For course materials containing equations and assessments, the Math OCR add-on is particularly valuable.

### NotebookLM Enterprise API is now available

**Launched September 2025**, the NotebookLM Enterprise API enables programmatic notebook creation, source management, and audio overview generation:

```bash
# Create notebook via API
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/PROJECT/locations/LOCATION/notebooks" \
  -d '{"title": "Coaching Resources"}'

# Add sources
curl -X POST ".../notebooks/ID/sources:batchCreate" \
  -d '{"userContents": [{"googleDriveContent": {"documentId": "DOC_ID"}}]}'
```

**Requirements**: NotebookLM Enterprise license (part of Gemini Enterprise). The API is currently v1alpha.

For Mindrian, this enables:
- Auto-creating study guides from coaching materials
- Generating audio overviews for auditory learners
- Building personalized knowledge hubs per user

### Google's knowledge graph alternatives to Neo4j

**Spanner Graph** (GA August 2024) provides native graph queries with ISO GQL standard, unified relational+graph in one database, and vector search built-in:

```sql
GRAPH CoachingGraph
MATCH (:User {id: $userId})-[:Completed]->(session:Session)
      -[:CoveredTopic]->(topic:Topic)
RETURN topic.name, COUNT(*) as frequency;
```

| Option | Best For | Recommendation |
|--------|----------|----------------|
| **Spanner Graph** | Unified relational+graph, global scale | Long-term if you want single DB |
| **Neo4j Aura on GCP** | Full graph features, Cypher | Keep for now, mature option |
| **Enterprise KG API** | Entity reconciliation | Complement, not replacement |

**Short-term recommendation**: Keep Neo4j running on GCP via Neo4j Aura. **Long-term**: Evaluate Spanner Graph when unifying data infrastructure.

---

## Storage, databases, and compute architecture

### AlloyDB: PostgreSQL with superior AI capabilities

AlloyDB is **4x faster** than standard PostgreSQL for transactions and **100x faster** for analytics, with native vector search using Google's ScaNN technology:

```sql
-- Auto-generate embeddings
CREATE TABLE coaching_content (
  embedding vector(768) GENERATED ALWAYS AS
  (embedding('text-embedding-004', content)) STORED
);

-- ScaNN index for fast similarity search
CREATE INDEX content_idx ON coaching_content
USING scann (embedding cosine);
```

Vector search is **10x faster** than pgvector HNSW indexes. For RAG applications, this provides significant performance improvements over Supabase's pgvector.

**Pricing**: ~$175/month starting (compute + storage).

### Comparison with current Supabase stack

| Feature | Supabase | Google Cloud Equivalent |
|---------|----------|------------------------|
| PostgreSQL | Supabase DB | Cloud SQL or **AlloyDB** |
| Auth | ~12 providers | Firebase Auth (20+ providers) |
| Real-time | PostgreSQL Changes | Firestore listeners (faster) |
| Edge Functions | Deno-based | Cloud Functions 2nd gen |
| Vector Search | pgvector | AlloyDB ScaNN (10x faster) |
| Storage | S3-compatible | Cloud Storage |

**Key advantage**: AlloyDB's AI features (auto-embeddings, ScaNN indexing, inline filtering) exceed what's available in Supabase.

### Cloud Run versus Render for deployment

| Feature | Render | Cloud Run |
|---------|--------|-----------|
| Scale to zero | No (paid) | Yes |
| Cold starts | None | 200ms-2s |
| GPU support | No | Yes (NVIDIA L4) |
| Regions | 3 | 30+ |
| Free tier | Limited | 2M requests/month |
| Light workload cost | ~$25/month fixed | ~$15/month usage |

Cloud Run's **scale-to-zero** and **GPU support** make it significantly more cost-effective for AI workloads with variable traffic patterns.

### Firebase Authentication replaces Supabase Auth

Firebase Auth is **free for unlimited users** with email/password and social providers. Enterprise SSO (SAML/OIDC) costs **$0.015/MAU** after 50 users. MFA, custom claims for RBAC, and anonymous-to-permanent user upgrade are all supported.

---

## Security, compliance, and enterprise features

### VPC Service Controls provide data isolation

VPC-SC creates security perimeters around GCP resources, protecting against data exfiltration and unauthorized access—**at no additional cost**. This is critical for FERPA compliance with student data.

### Compliance certifications for education

| Certification | Status | Notes |
|--------------|--------|-------|
| **FERPA** | Supported | Workspace for Education certified; Cloud requires configuration |
| **HIPAA** | BAA available | 100+ services covered at no extra cost |
| **SOC 2** | Type II certified | Quarterly audits by Ernst & Young |
| **GDPR** | Compliant | EU data residency, SCCs available |

For Mindrian operating in education: use Google Workspace for Education for student-facing features, configure audit logging, implement access controls per school/district, and document data handling procedures.

### Customer-managed encryption keys (CMEK)

For sensitive coaching data: **$0.03/key version/month** with Cloud KMS, or **$1-2.50/key/month** for HSM-backed keys. Supports AlloyDB, Firestore, BigQuery, and Agent Engine.

---

## Pricing analysis and startup credits

### Google for Startups Cloud Program

| Tier | Credits | Requirements |
|------|---------|--------------|
| Start | $2,000 | Pre-funding |
| Scale | $100K Y1 + $100K Y2 | Seed to Series A |
| **AI Track** | **$250K Y1 + $100K Y2** | AI-first startup |

Mindrian qualifies for the **AI Startup tier** with up to **$350K in credits** over two years. Apply at cloud.google.com/startup with GCP billing ID and funding documentation.

### Monthly cost estimates

**Small scale (1,000 users, light AI)**:
- Cloud Run: $15-50
- Gemini API (50K requests): $50-100
- Firestore + AlloyDB: $50
- Cloud Storage: $10
- **Total: ~$125-210/month**

**Medium scale (10,000 users, moderate AI)**:
- Cloud Run: $100-300
- Gemini API (500K requests): $300-800
- AlloyDB: $175
- Pub/Sub + Storage: $50
- **Total: ~$625-1,325/month**

With $350K in startup credits, this covers **2+ years** of infrastructure at medium scale.

### Cost optimization strategies

- **Context caching**: 90% savings on repeated content
- **Batch API**: 50% discount for async processing
- **Model routing**: Flash-Lite for simple tasks, Pro only when needed
- **Disable thinking**: Set `thinking_budget: 0` for simple Q&A
- **Committed use**: 20-55% discounts for predictable workloads

---

## Answers to specific implementation questions

### 1. Can URL Context Grounding replace traditional RAG?

**For many cases, yes.** URL Context handles up to 20 URLs (34MB each) per request—sufficient for public documents, shared PDFs, and web resources. **Still need RAG for**: private documents, large corpora (thousands of files), real-time internal databases, and compliance-restricted content.

**Recommendation**: Hybrid approach—URL Context for public resources, Vertex AI RAG Engine for proprietary coaching frameworks.

### 2. Migration path to Vertex AI Agent Builder?

**Gradual migration via ADK**:
1. Wrap existing prompts in `LlmAgent` classes
2. Convert tools to ADK function tools
3. Add workflow agents (Sequential, Parallel)
4. Deploy to Agent Engine
5. Enable A2A for specialized coaching agents

Existing Gemini prompts port directly—same model identifiers, same API patterns.

### 3. Google equivalent to Neo4j?

**Spanner Graph** is the closest native option—unified relational+graph with GQL queries, vector search, and Vertex AI integration. However, **Neo4j Aura on GCP** is a mature option if you want full Cypher support and graph algorithms.

**Recommendation**: Keep Neo4j Aura short-term; evaluate Spanner Graph when consolidating infrastructure.

### 4. Workspace Events API for real-time folder sync?

Delivers Drive change events via Pub/Sub in near real-time. **Currently Developer Preview**—requires enrollment. Supports file created/updated/trashed events with subscription TTLs of 4 hours to 7 days.

### 5. Meet API recording/transcript limits?

**Free** with Business Standard+ subscription. Transcripts have **5-minute timestamp granularity** and **30-day retention**. Cannot programmatically start recordings—requires manual click.

### 6. NotebookLM API integration?

**Yes—NotebookLM Enterprise API** launched September 2025. Requires Gemini Enterprise license. API is v1alpha. No API for consumer NotebookLM.

### 7. Best Google stack for startups?

- **Compute**: Cloud Run (scale-to-zero)
- **Auth**: Firebase Authentication
- **Database**: Firestore + AlloyDB (or Cloud SQL)
- **AI**: Gemini API + ADK agents
- **Knowledge**: Vertex AI RAG Engine + NotebookLM Enterprise
- **Apply for**: AI Startup tier ($350K credits)

### 8. User-provided API keys for multi-tenant apps?

**Options**:
- **Platform keys**: You pay, bill customers based on token counting from `usage_metadata`
- **User keys**: Pass-through (user's project billed)
- **OAuth**: For Workspace APIs with user credentials

Store keys in Secret Manager, never log them, track usage internally for billing since Google doesn't provide per-key reports.

---

## Recommended migration roadmap

### Phase 1: Foundation (Month 1-2)
- [ ] Apply for Google Cloud startup credits (AI track)
- [ ] Deploy existing application to Cloud Run (replace Render)
- [ ] Set up Firebase Authentication (migrate from Supabase Auth)
- [ ] Configure VPC Service Controls for data isolation

### Phase 2: Database migration (Month 2-3)
- [ ] Provision Cloud SQL PostgreSQL (direct migration from Supabase)
- [ ] Evaluate AlloyDB for vector search (replace pgvector)
- [ ] Keep Neo4j Aura on GCP (knowledge graph)
- [ ] Set up Firestore for real-time features

### Phase 3: AI platform (Month 3-4)
- [ ] Migrate agents to ADK framework
- [ ] Implement context caching for coaching materials
- [ ] Add URL Context Grounding for document analysis
- [ ] Deploy to Agent Engine with sessions/memory

### Phase 4: Workspace integration (Month 4-5)
- [ ] Integrate Drive API for document management
- [ ] Set up Meet API for session recordings
- [ ] Enroll in Developer Preview for Workspace Events API
- [ ] Evaluate NotebookLM Enterprise for study guides

### Phase 5: Enterprise features (Month 5-6)
- [ ] Configure CMEK for sensitive data
- [ ] Implement DLP API for PII detection
- [ ] Set up Security Command Center monitoring
- [ ] Document FERPA compliance procedures

---

## Conclusion

The Google Cloud ecosystem provides a **comprehensive, integrated platform** that can replace Mindrian's current multi-vendor stack while adding significant AI capabilities. The key advantages are native Gemini integration across all services, enterprise security controls, generous startup credits, and reduced operational complexity from unified infrastructure.

**Three critical actions** for Mindrian:
1. **Apply immediately** for Google for Startups AI track ($350K credits)
2. **Start with Cloud Run** migration—lowest risk, immediate cost savings
3. **Adopt ADK gradually**—existing prompts work directly, enables future Agent Engine deployment

The most significant capability gain comes from **AlloyDB's AI features** (10x faster vector search than pgvector), **NotebookLM Enterprise API** (programmatic study guide generation), and **Agent Engine** (managed agent infrastructure with memory). Combined with **90% cost savings** from context caching and **50% from batch processing**, the all-Google approach is both technically superior and economically compelling for an AI-first educational platform.

---

## Related Documents

- `GOOGLE_ECOSYSTEM_STRATEGY.md` - Team meeting decisions on Google commitment
- `SHARED_FOLDER_RAG_ARCHITECTURE.md` - Google Drive folder-as-RAG design
- `MEETING_INSIGHTS_FEB_2025.md` - Architecture discussions and decisions
