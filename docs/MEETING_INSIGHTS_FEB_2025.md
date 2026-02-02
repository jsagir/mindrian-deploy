# Mindrian R&D: Meeting Insights (Feb 2025)

## Source
Team meeting with Lawrence Aronhime, Jonathan Sagir, Jonathan Edwards, Contessa St. Clair

---

## 1. Core Product Vision

### Three Use Cases (Confirmed)
These are the **only** three things users do with Mindrian:

| Use Case | Description | Entry Point |
|----------|-------------|-------------|
| **Explore Ideas** | Free-form exploration, take conversation wherever it goes | Sandbox mode |
| **Review Documents** | Upload 1+ documents, get feedback | Document feedback mode |
| **Build a Venture** | Structured startup creation (Problem → Solution → Business Case) | Venture builder mode |

**Key Quote (Larry):** "I can't think of anything else that people use this for."

---

## 2. Architecture Decisions

### 2.1 Data Layer (Confirmed by Sagir)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MINDRIAN DATA ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   SUPABASE (PostgreSQL)                                             │
│   └── Role: "Just a bucket"                                         │
│   └── Stores: User sessions, conversation history, IDs              │
│   └── Auth: Login via Google/GitHub/Microsoft                       │
│   └── Does NOT do reasoning or RAG                                  │
│                                                                      │
│   FILE SEARCH (Google)                                              │
│   └── Role: RAG system                                              │
│   └── Stores: All knowledge, documents, embeddings                  │
│   └── Gemini models for embedding                                   │
│                                                                      │
│   NEO4J (Lazy Graph)                                                │
│   └── Role: "Intelligence layer"                                    │
│   └── Stores: ONLY relationships between nodes                      │
│   └── Actual content fetched from RAG                               │
│   └── LangExtract: Extracts relationships from every interaction    │
│                                                                      │
│   USER'S GOOGLE API (NEW - per user)                                │
│   └── Role: Private workspace                                       │
│   └── Stores: User's own files, outputs                             │
│   └── Benefit: "We don't own their data"                            │
│   └── Cost: Shifts API costs to user                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Technical Decision: User-Provided API Keys

**Rationale:**
1. Reduces our API costs significantly
2. Addresses data privacy concerns ("We don't even see it")
3. Creates natural per-user data isolation
4. Easy for users (direct link to Google Console)

**Implementation:**
- User provides their Google API key at signup
- Key creates their own private File Search instance
- All their files/outputs stored in their own RAG
- We provide platform, they provide compute

### 2.3 Collaboration Architecture (Deferred)

**Decision: NO real-time collaboration for MVP**

**Reasons:**
- Supabase charges for socket connections
- Complex to build
- Users don't actually collaborate real-time (observed behavior)

**Instead: Shared Folder Model**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COLLABORATION VIA SHARED FOLDER                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Team Member A                    Team Member B                     │
│   ┌──────────────┐                ┌──────────────┐                  │
│   │ Private      │                │ Private      │                  │
│   │ Workspace    │                │ Workspace    │                  │
│   └──────┬───────┘                └──────┬───────┘                  │
│          │                               │                          │
│          │  DUMP                   DUMP  │                          │
│          ▼                               ▼                          │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │              SHARED GOOGLE DRIVE FOLDER                       │  │
│   │                                                               │  │
│   │  • Anyone can dump files                                     │  │
│   │  • Folder auto-indexed as RAG                                │  │
│   │  • Mindrian can query full team context                      │  │
│   │  • No real-time sync needed                                  │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   "As you dump things into it, the folder becomes a RAG of its own  │
│    that Mindrian can interact with."                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Quote (Sagir):** "They work separately, but they actually work together."

---

## 3. UI/UX Requirements

### 3.1 MVP User Flow

```
Landing Page
    │
    ▼
Login (Supabase Auth)
    │ Google / GitHub / Microsoft
    ▼
Paywall (Stripe)
    │ Even if $0.99 or token-limited
    ▼
Choose Mode
    │
    ├── Explore Ideas
    ├── Review Documents
    └── Build Venture
    │
    ▼
Main Interface
    │
    ├── LEFT: Previous chats (like ChatGPT)
    ├── CENTER: Chat conversation
    └── RIGHT: Road map / progress indicator
```

### 3.2 Interface Principles (From Larry)

| Principle | Implementation |
|-----------|----------------|
| **Simplicity** | "Cleanliness and simplicity are the way to go" |
| **Road map visible** | When using a tool, show the steps on the right |
| **Persistent buttons** | Research, Summarize always visible |
| **Contextual buttons** | Spawn based on context, but hover explains WHY |
| **Plain English** | "I want to red team this" instead of selecting agent |
| **Save/recall** | Must be able to save work and return to it |

### 3.3 Button Philosophy

**Problem:** Too many buttons, users don't know what to press

**Solution (Sagir's approach):**
```
Instead of: Click "Red Team" from menu
Do: Say "challenge this" or "devil's advocate"

Instead of: Select agent manually
Do: System spawns relevant button based on context

When button spawns:
- Hover explains: "I can help you with X because of Y"
- It's not just a button, it's a contextual assistant
```

**Quote:** "It's not trying to sell you a button. It's an assistant."

---

## 4. Agent Architecture Decisions

### 4.1 Single Entry Point (Future Direction)

**Current:** Multiple agent toggles on the left
**Future:** One main agent that spawns sub-agents

**Quote (Sagir):** "What I want to end up doing for the software thing is to have no agent other than the main one and everything else will be spawned in the main one. Without moving."

### 4.2 Workflow Orchestration

Observed in the demo:
- System detected investment context → spawned "PWS Investment" button
- System detected need for validation → spawned "Red Team" button
- System detected research need → spawned "Trends" and "Example" buttons

**Key insight:** Buttons spawn based on conversation context, not user selection.

### 4.3 Thinking Process Visibility

**Debate:** Should users see the thinking process?

| For (Sagir) | Against (Larry) |
|-------------|-----------------|
| Builds trust | Clutters interface |
| Shows it's "alive" | Exposes methodology |
| Psychological safety | Overwhelming for new users |

**Resolution:** Keep as collapsible dropdown (hidden by default)

---

## 5. Integration Points

### 5.1 Google Ecosystem (Committed)

| Google Service | Use Case |
|----------------|----------|
| Gemini 2.5 Flash | Primary model |
| Gemini 2.5 Pro | Advanced reasoning |
| Gemini Embedding | Vector embeddings |
| File Search | RAG system |
| Google Drive | Shared folders |
| Google Meet | (Future) Auto-record and index |
| Google Calendar | (Future) Session scheduling |

**Quote (Sagir):** "If we're staying in Google's ecosystem, we can potentially connect Meet, Calendar... everything auto-recorded and dumped in the folder to be indexed."

### 5.2 Payment (Stripe)

- Need American entity to receive payments
- Initial: $0.99 to establish "this is not free"
- Token limits like ChatGPT
- Time-limited access (e.g., through May 31)

---

## 6. Build vs Buy Decisions

| Feature | Decision | Reason |
|---------|----------|--------|
| Auth | Use Supabase | Already built, works |
| Payment | Use Stripe | David built prototype |
| Real-time collab | Don't build | Too complex, users don't need |
| File panel | Build simple | Export/import files |
| Full workspace | Later | After MVP validation |

---

## 7. Immediate Priorities

### For Budapest Presentation (March)

| Must Have | Nice to Have | Later |
|-----------|--------------|-------|
| Login page | Workspace concept | Real-time collab |
| Paywall/pricing | Team folders | Microsoft integration |
| Token limits | Left panel (prev chats) | Meet integration |
| Clean UI | Progress road map | |
| Three entry modes | | |
| Save/recall chats | | |

---

## 8. Open Technical Questions

1. **API Key UX:** How easy is it really for users to get a Google API key?
2. **Cost Model:** At scale, what's the per-user cost with their own APIs?
3. **Graph Sync:** How does LangExtract scale with conversation volume?
4. **File Formats:** Users want .docx/.pdf, currently exports .md
5. **State Management:** How to persist workflow state across sessions?

---

## 9. Action Items (Technical)

| Owner | Task | Priority |
|-------|------|----------|
| Edwards + Sagir | Meet to review codebase architecture | Immediate |
| Edwards | Implement Supabase login | High |
| Edwards | Implement Stripe paywall | High |
| Sagir | Deploy latest commit with contextual buttons | Immediate |
| Sagir | Add previous chats to left panel | High |
| Both | Decide on user API key approach | Medium |

---

## Appendix: Technical Quotes

**On the lazy graph:**
> "Instead of using it to keep all the knowledge base, it interacts only with the relationships between nodes. And the actual nodes sit on the RAG."

**On LangExtract:**
> "Everything that you talk here gets indexed immediately on the graph as relationships only. Just the relationships."

**On building Mindrian:**
> "I built a set of agents. One is Chainlit. One is knowledge graph expert. Everything works together. I go to Claude Code, say 'this is what I wanna do', and then I consult with all of them. They have a discussion between them."
