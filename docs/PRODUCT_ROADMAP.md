# Mindrian Product Roadmap

Last Updated: February 2, 2026

---

## Vision

A clean, intuitive platform where users explore ideas, review documents, or build ventures - powered by AI that spawns contextual help without requiring users to understand the underlying methodology.

**Key Principle:** "It's not trying to sell you a button. It's an assistant."

---

## Timeline Overview

```
FEB 2026          MARCH 2026         APRIL 2026         MAY 2026
────────────────────────────────────────────────────────────────────
│                 │                  │                  │
│ QA Fixes        │ Budapest Demo    │ MVP Launch       │ Paid Users
│ Triple Mode     │ Login + Paywall  │ Full Features    │ Token Limits
│ A2A Wiring      │ Clean UI         │ Export Formats   │ Team Folders
│                 │                  │                  │
```

---

## Phase 1: Budapest Demo (March 2026)

### Must Have

| Feature | Status | Owner | Notes |
|---------|--------|-------|-------|
| Login page (Supabase Auth) | Not started | Edwards | Google/GitHub/Microsoft |
| Paywall/pricing (Stripe) | Not started | Edwards | Even $0.99 to establish value |
| Token limits | Not started | TBD | Like ChatGPT model |
| Clean UI | In progress | Sagir | Remove clutter, simplify |
| Three entry modes visible | Done | Sagir | Triple Mode architecture |
| Save/recall chats | Partial | Sagir | Left panel needed |

### Nice to Have

| Feature | Status | Owner | Notes |
|---------|--------|-------|-------|
| Workspace concept | Not started | TBD | User's own File Search |
| Team folders (Google Drive) | Not started | TBD | Shared RAG |
| Left panel (previous chats) | Not started | Sagir | Like ChatGPT |
| Progress road map (right panel) | Partial | Sagir | Exists but needs polish |

---

## Phase 2: MVP Launch (April 2026)

### Core Features

| Feature | Status | Priority | Notes |
|---------|--------|----------|-------|
| User-provided API keys | Not started | High | Shifts costs to user |
| .docx/.pdf export | Not started | High | QA-008 fix |
| Hover explanations on buttons | Not started | High | QA-006 fix |
| Red Team default selection | Not started | Critical | QA-001 fix |
| Onboarding flow | Not started | Critical | QA-004, QA-009 fix |
| A2A orchestration wired in | Built, not wired | High | Classification + routing |

### Quality Fixes

| Issue ID | Description | Priority |
|----------|-------------|----------|
| QA-001 | Red Team default selection | Critical |
| QA-002 | Required buttons not marked | Critical |
| QA-003 | Unexpected return to main | High |
| QA-004 | New users don't know what to do | Critical |
| QA-005 | Build Venture hard to find | High |
| QA-006 | Button purpose unclear | High |
| QA-008 | Export format (.md only) | High |
| QA-009 | Non-PWS users can't start | Critical |

---

## Phase 3: Scale (May 2026+)

### Deferred Features

| Feature | Reason for Deferral |
|---------|---------------------|
| Real-time collaboration | Supabase socket costs, users don't need it |
| Microsoft integration | Focus on Google first |
| Google Meet integration | After core is stable |
| Google Calendar integration | After core is stable |
| Full workspace management | After MVP validation |

---

## Data Architecture (Confirmed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MINDRIAN DATA ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   SUPABASE (PostgreSQL)                                             │
│   └── "Just a bucket"                                               │
│   └── User sessions, conversation history, IDs                      │
│   └── Auth: Google/GitHub/Microsoft                                 │
│                                                                      │
│   FILE SEARCH (Google)                                              │
│   └── RAG system                                                    │
│   └── All knowledge, documents, embeddings                          │
│   └── Future: Per-user instances via their API keys                 │
│                                                                      │
│   NEO4J (Lazy Graph)                                                │
│   └── "Intelligence layer"                                          │
│   └── ONLY relationships between nodes                              │
│   └── Content fetched from RAG on demand                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Feature Status Legend

| Status | Meaning |
|--------|---------|
| Done | Fully implemented and tested |
| Built, not wired | Code exists but not integrated |
| Partial | Some functionality working |
| In progress | Currently being developed |
| Not started | Planned but no work begun |

---

## Success Metrics

### Budapest Demo

| Metric | Target |
|--------|--------|
| Demo runs without crashes | 100% |
| User can complete basic flow | < 5 min |
| Three entry points visible | Yes |
| Login/logout works | Yes |

### MVP Launch

| Metric | Target |
|--------|--------|
| Time to first meaningful output | < 2 min |
| Task completion rate | > 90% |
| Feature discovery | < 30 sec |
| User satisfaction | 4/5 |

### Scale

| Metric | Target |
|--------|--------|
| Monthly active users | TBD |
| Paid conversion rate | TBD |
| Average session length | TBD |
| Retention (7-day) | TBD |

---

## Technical Debt

| Item | Impact | Priority |
|------|--------|----------|
| A2A orchestration not wired | Classification not used | High |
| Export only .md | Users can't share easily | High |
| No onboarding | Users bounce | Critical |
| Button hover missing | Users confused | High |
| Right panel sync | Progress unclear | Medium |

---

## Team Responsibilities

| Area | Owner |
|------|-------|
| Backend / AI / RAG | Sagir |
| Auth / Payment | Edwards |
| UX / Design | TBD |
| Content / PWS | Larry |
| QA / Testing | Team |

---

## Open Questions

1. **API Key UX:** How easy is it for users to get a Google API key?
2. **Cost Model:** At scale, what's the per-user cost with their own APIs?
3. **Graph Sync:** How does LangExtract scale with conversation volume?
4. **Pricing:** What's the right price point? ($0.99? Token-based? Subscription?)
5. **Entity:** Need American entity for Stripe payments
