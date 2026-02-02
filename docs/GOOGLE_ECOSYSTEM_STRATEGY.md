# Mindrian: Google Ecosystem Strategy

## Source
Team meeting Feb 2025 - All quotes from Jonathan Sagir unless noted

---

## 1. The Core Decision

**Sagir:** "If we're staying in Google's ecosystem... everything works using Google's tools. Like, all the tools that I listed now are Google's. Everything."

**The commitment is total** - not partial integration, but full ecosystem dependency.

---

## 2. Current Google Services in Use

| Service | Role in Mindrian | Quote/Context |
|---------|------------------|---------------|
| **Gemini 2.5 Flash** | Primary AI model | "It's Gemini. Two different models." |
| **Gemini 2.5 Pro** | Advanced reasoning | "Two different models" |
| **Gemini Embedding** | Vector embeddings | "Plus embedding by one of the Gemini models" |
| **File Search** | RAG system | "Plus we have file search as the RAG" |
| **LangExtract** | Relationship extraction | "You have LangExtract that everything that you talk here gets indexed immediately on the graph as relationships only" |
| **Google Drive** | Shared folders (proposed) | "It's a Google folder... shared Google Drive" |

---

## 3. User API Key Strategy

### The Proposal

**Sagir:** "If we can require from any user to get their Google API, their own Google API. They put in the system, it's building their own database."

### How It Works

```
USER PROVIDES:
├── Their own Google API key
└── Creates their own private File Search instance

BENEFITS:
├── "I don't use it for anything"
├── "It just saves to their specific key to their specific safe"
├── "I don't know nothing"
└── "We don't even see it"
```

### Data Privacy Benefit

**Sagir:** "Even that will reduce the questions of what do you do with my data, what end this, what that. Don't own it. It's yours. We don't even see it."

### Ease of Use

**Jonathan Edwards:** "How hard is it for a normal user to just get that API?"

**Sagir:** "Extremely easy. There's the Google Workspace console. We can have a direct link when you need to just click it, go immediately there. Use your Gemini or your Google thing, click, and you have an API."

### Cost Implications

**Sagir:** "I think the trick here is to see how we can use their own API. And then reduce cost because when we're using an API, the costs are significant. Like, it ties up."

**Edwards:** "I agree with you 100%."

**Sagir:** "It's a strategic decision because it's a big one. Has implications. But for us... we don't have access to the data anymore. It's a good thing and a bad thing."

---

## 4. Shared Folder / Collaboration Model

### The Concept

**Sagir:** "If this folder is connected to yet another instance of a file search, the folder itself becomes a RAG. As you dump things into it."

### How Teams Would Work

```
TEAM COLLABORATION VIA GOOGLE DRIVE:
─────────────────────────────────────────────────────────────
1. Create shared Google Drive folder
2. Team members dump files into folder
3. Folder auto-indexed as its own RAG
4. Mindrian can query the full team context
5. "As people dump files, there's more context added to that specific dump"
─────────────────────────────────────────────────────────────
```

**Sagir:** "Imagine all the folders are somehow connected, and all the dumping you can talk with all the folders at once."

**Sagir:** "They work separately, but they actually work together. Because they build the dump... It's indexed and it's small."

### Why Not Real-Time Collaboration

**Edwards:** "The hard part of doing that is it needs real time connections, and Supabase charges for that."

**Sagir:** "I agree. So if you have some kind of an integration to a collaborative drive, so all the team members can dump files in that drive. And that's a collaborative effect. That's it."

**Larry:** "That's enough for now."

---

## 5. Future Google Integrations (Proposed)

### Google Meet Integration

**Sagir:** "If we're staying in Google's ecosystem, we can potentially connect Meet... If you invite people to join you on a session, it can get automatically recorded and automatically dumped in the folder that you want to be indexed."

### Google Calendar Integration

**Sagir:** "...team and Meet, Calendar."

### The Vision

**Sagir:** "So imagine all the possibilities there. If you stay in this ecosystem."

---

## 6. Why Google Over Microsoft

### Direct Quote

**Sagir:** "Working in the Microsoft ecosystem, it's like... it's a pain in the ass. Like, it's unbearable."

### Contessa's Concern (User Perspective)

**Contessa:** "If you're trying to market this to different companies that just usually use Microsoft or even educationally only use Microsoft, how might that work?"

### Current Position

**Sagir:** "This confines us pretty much to the Google Workspace, which I don't mind. I'm very okay with working with Gemini and the Google ecosystem because it's really well rounded. It's very easy for me to work with all the tools they have."

---

## 7. Technical Architecture with Google

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                 MINDRIAN GOOGLE ECOSYSTEM ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   USER INTERACTION                                                   │
│         │                                                            │
│         ▼                                                            │
│   ┌─────────────┐                                                   │
│   │   GEMINI    │  ←── Primary AI (2.5 Flash + 2.5 Pro)            │
│   │   MODELS    │                                                   │
│   └──────┬──────┘                                                   │
│          │                                                           │
│          ├────────────────────────────────────────┐                 │
│          │                                        │                 │
│          ▼                                        ▼                 │
│   ┌─────────────┐                         ┌─────────────┐          │
│   │   GEMINI    │                         │    FILE     │          │
│   │  EMBEDDING  │                         │   SEARCH    │          │
│   │   MODEL     │                         │    (RAG)    │          │
│   └──────┬──────┘                         └──────┬──────┘          │
│          │                                        │                 │
│          │                                        │                 │
│          ▼                                        ▼                 │
│   ┌─────────────┐                         ┌─────────────┐          │
│   │  LANGEXTRACT│                         │   GOOGLE    │          │
│   │  (Relations)│                         │    DRIVE    │          │
│   └──────┬──────┘                         │  (Folders)  │          │
│          │                                └─────────────┘          │
│          ▼                                                          │
│   ┌─────────────┐                                                   │
│   │   NEO4J     │  ←── Only relationships, not content             │
│   │   (Graph)   │                                                   │
│   └─────────────┘                                                   │
│                                                                      │
│   SUPABASE: Auth + Session storage only (not Google)               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Per-User Architecture

**Sagir:** "Every API that you have can have access to one file search built. So you open up keys, and they just give their own keys. And this credential is Dell specific instance, and that's it."

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PER-USER DATA ISOLATION                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   USER A                          USER B                            │
│   ┌──────────────────┐           ┌──────────────────┐              │
│   │ Google API Key A │           │ Google API Key B │              │
│   └────────┬─────────┘           └────────┬─────────┘              │
│            │                              │                         │
│            ▼                              ▼                         │
│   ┌──────────────────┐           ┌──────────────────┐              │
│   │ File Search      │           │ File Search      │              │
│   │ Instance A       │           │ Instance B       │              │
│   │ (Private RAG)    │           │ (Private RAG)    │              │
│   └──────────────────┘           └──────────────────┘              │
│                                                                      │
│   "It's a fourth layer... private. It is solely yours."            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Strategic Implications

### Pros

| Benefit | Quote |
|---------|-------|
| Cost reduction | "Reduce cost because when we're using an API, the costs are significant" |
| Data privacy | "We don't even see it" |
| Easy integration | "Really well rounded. Very easy for me to work with" |
| Future features | "Connect Meet, Calendar... automatically recorded and dumped" |
| User isolation | "It's solely yours" |

### Cons

| Risk | Quote |
|------|-------|
| Microsoft users excluded | "If you're trying to market to companies that use Microsoft" |
| Ecosystem lock-in | "This confines us pretty much to Google Workspace" |
| No data access | "We don't have access to the data anymore. It's a good thing and a bad thing" |
| User friction | Requires users to get API key (though "extremely easy") |

### Edwards' Caution

**Edwards:** "In theory, you could just do everything in Google. You could technically do that, but I don't wanna commit myself to that before I know how annoying..."

---

## 9. Decision Status

| Aspect | Decision | Confidence |
|--------|----------|------------|
| Use Gemini models | Committed | High |
| Use File Search for RAG | Committed | High |
| Use Google Drive for collab | Proposed | Medium |
| Require user API keys | Proposed | Medium |
| Integrate Meet/Calendar | Future | Low |
| Support Microsoft | Not planned | N/A |

---

## 10. Open Questions

1. **User friction:** Will requiring API keys reduce adoption?
2. **Enterprise sales:** How do we sell to Microsoft-only companies?
3. **Data analytics:** Without access to user data, how do we improve the product?
4. **Pricing model:** If users pay Google directly, what's our value capture?
5. **Meet integration:** Is auto-recording meetings a privacy concern?

---

## 11. Action Items

| Task | Owner | Priority |
|------|-------|----------|
| Document API key acquisition flow | Sagir | High |
| Test shared folder → RAG indexing | Sagir | High |
| Evaluate Microsoft integration effort | Edwards | Medium |
| Design data-less analytics approach | Team | Medium |
| Prototype Meet → folder pipeline | Sagir | Low |

---

## Key Quotes Summary

> "Everything works using Google's tools. Like, all the tools that I listed now are Google's. Everything."

> "Working in the Microsoft ecosystem, it's like... it's a pain in the ass."

> "If we can require from any user to get their Google API... We don't even see it."

> "This confines us pretty much to the Google Workspace, which I don't mind."

> "Imagine all the possibilities there. If you stay in this ecosystem."
