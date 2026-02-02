# Shared Folder RAG Architecture - Critical Reference

## Source
Team meeting transcript, Feb 2025 - Verbatim quotes from Jonathan Sagir

**This is a critical architectural decision for team collaboration without real-time sync.**

---

## The Core Concept

**Sagir:** "If this folder is connected to yet another instance of a file search, the folder itself becomes a RAG. As you dump things into it."

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│              SHARED FOLDER → AUTO-INDEXED RAG                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   TEAM MEMBER A              TEAM MEMBER B              TEAM MEMBER C│
│   ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│   │   Private    │          │   Private    │          │   Private    │
│   │   Workspace  │          │   Workspace  │          │   Workspace  │
│   └──────┬───────┘          └──────┬───────┘          └──────┬───────┘
│          │                         │                         │       │
│          │      DUMP FILES         │      DUMP FILES         │       │
│          ▼                         ▼                         ▼       │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                   SHARED GOOGLE DRIVE FOLDER                  │  │
│   │                                                               │  │
│   │   • Files dumped by all team members                         │  │
│   │   • Auto-indexed immediately                                 │  │
│   │   • Becomes its own RAG instance                             │  │
│   │   • Mindrian can query full team context                     │  │
│   │                                                               │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    FILE SEARCH (RAG)                          │  │
│   │                                                               │  │
│   │   Folder indexed as searchable knowledge base                │  │
│   │   Mindrian interacts with full team context                  │  │
│   │                                                               │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Quotes (Verbatim)

### On the Folder Becoming a RAG

**Sagir:** "If this folder is connected to yet another instance of a file search, the folder itself becomes a RAG. As you dump things into it."

**Sagir:** "But this dump I can be a small dump. That you dump things and it get indexed immediately. In this specific world of dump, this little dump becomes a RAG of its own that Mindtree can interact with."

### On Team Collaboration Without Real-Time Sync

**Sagir:** "So it basically interacts with the full teams. But without sharing work. Like, as people dump files, there's more context added to that specific dump. And then this is the way the team works on project together."

**Edwards:** "The hard part of doing that is it needs real time connections, and Supabase charges for that."

**Sagir:** "I agree. So if you have some kind of an integration to a collaborative drive, so all the team members can dump files in that drive. And that's a collaborative effect. That's it."

**Larry:** "That's enough for now."

### On How Teams Actually Work

**Sagir:** "They work separately, but they actually work together. Because they build the dump... It's indexed and it's small."

**Larry:** "Even when they're in the same room and they're sitting next to each other, it's not like they look at one screen. They're each doing their thing and then talking about it."

### On Connecting Multiple Folders

**Sagir:** "You remember the file system that you guys built? Each one is a folder kind of thing. So imagine all the folders are somehow connected, and all the dumping you can talk with all the folders at once."

**Sagir:** "A very similar way, you have one folder in a Google Drive and as you add documents for the cross the team, everybody's dumping. This folder itself becomes like a container to be indexed and interacted with. That Mindrian can interact with the full context of the folder. Without manipulating anything."

---

## Why Not Real-Time Collaboration?

| Reason | Quote |
|--------|-------|
| Cost | "Supabase charges for [socket connections]" - Edwards |
| Complexity | "The hard part of doing that is it needs real time connections" - Edwards |
| User behavior | "They don't you know, this idea of collaborative work, they just don't do it" - Larry |
| Observation | "Even when they're in the same room... they're each doing their thing and then talking about it" - Larry |

**Decision:** Build dump-to-folder collaboration instead of real-time sync.

---

## Workflow: Private → Team

**Sagir:** "Own workspace, and you have your team workspace. Everything you can migrate any out from your private one to the team. But not the other way around. Unless you copy paste. But everything you decide to dump literally, we can have a drag and drop. Like, you dump in that shared folder."

```
PRIVATE WORKSPACE                    TEAM WORKSPACE
┌──────────────────┐                ┌──────────────────┐
│  My explorations │                │  Shared context  │
│  My drafts       │  ──DUMP──►    │  Team insights   │
│  My experiments  │                │  Combined docs   │
└──────────────────┘                └──────────────────┘
        │                                   │
        │                                   │
        ▼                                   ▼
   Private RAG                         Team RAG
   (only I access)                 (whole team accesses)
```

---

## Use Case: Zoom Recording Auto-Index

**Sagir:** "If we're staying in Google's ecosystem, we can potentially connect Meet, Calendar. If you invite people to join you on a session, it can get automatically recorded and automatically dumped in the folder that you want to be indexed."

**Flow:**
1. Team has Zoom/Meet session
2. Recording auto-saved to shared folder
3. Folder auto-indexes the recording
4. Mindrian can now query the meeting content
5. All team members benefit from shared context

---

## Implementation Notes

### What Gets Indexed
- Any file dumped into the shared folder
- PDFs, docs, transcripts, exports from Mindrian
- Meeting recordings (future)
- Any document the team decides to share

### What Doesn't Get Indexed
- Private workspace content (unless explicitly dumped)
- Real-time chat (no socket connections)
- Drafts in progress

### Technical Requirements
1. Google Drive folder integration
2. File Search (Google) connected to folder
3. Auto-indexing on file add/update
4. Query routing to include team context

---

## Why This Matters

**Sagir:** "I'm telling you, I have a hunch that this folder system that we just created now just by thinking is the collaborative effect that we want to achieve anyway. Because they work separately, but they actually work together."

This architecture solves collaboration without:
- Real-time sync complexity
- Socket connection costs
- Changing how users naturally work (separately, then combine)

---

## Related Documents
- `GOOGLE_ECOSYSTEM_STRATEGY.md` - Full Google integration plan
- `MEETING_INSIGHTS_FEB_2025.md` - Complete meeting notes
- `PRODUCT_ROADMAP.md` - Implementation timeline
