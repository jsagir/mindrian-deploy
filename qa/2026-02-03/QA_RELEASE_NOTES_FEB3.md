# QA Release Notes - February 3, 2026

**To:** User-Side Testers (QA)
**Date:** February 3, 2026
**Branch:** `triple-mode-v1`
**Commits:** 11 commits in the last 12 hours

---

## What This Release Addresses

This release introduces **Recursive Intelligence** - Mindrian now learns from every session. It also upgrades all AI models to Gemini 2.5-flash and includes UI improvements.

---

## Key Changes Ready to Test

### 🧠 Recursive Intelligence (NEW - Major Feature)

The system now **learns from every conversation** to improve over time.

| Component | What It Does |
|-----------|--------------|
| **Session Event Logging** | Tracks agent switches, phase completions, user reactions |
| **Reaction Classification** | Detects if user is positive, negative, confused, or wants to redirect |
| **Knowledge Extraction** | Extracts frameworks used, dead-ends hit, cross-connections made |
| **Adaptive Routing** | Uses learned patterns to suggest better bots for problem types |

**What You Should Notice:**
- The system silently logs events (you won't see this directly)
- Over time (after ~50+ sessions), routing suggestions will improve
- The learning is non-blocking - it never slows down the chat

### ⚡ Gemini 2.5-flash Upgrade (NEW)

All AI operations upgraded from `gemini-2.0-flash` → `gemini-2.5-flash`:

| Tool | What It Affects |
|------|-----------------|
| Presentation Analyzer | PDF/slide analysis, OCR |
| Smart Phase Tracker | Phase detection accuracy |
| Assessment Engine | Grading quality |
| Research Orchestrator | Research depth |
| LangExtract | Data extraction |
| Validation Workflow | Problem validation |
| Multi-Agent Graph | Agent coordination |

**What You Should Notice:**
- Faster responses
- Better quality analysis
- Improved OCR on documents

### 🎨 UI Improvements

| Change | What Happened |
|--------|---------------|
| WorkshopRoadmap | Simplified, cleaner design |
| PhaseProgress | Archived (replaced by WorkshopRoadmap) |

### 🛠️ New Utilities

| Utility | Purpose |
|---------|---------|
| `phase_discovery.py` | Bots can now self-describe their phases |
| `telemetry.py` | Usage tracking for analytics |
| `neo4j-schema-navigator` skill | New skill for graph exploration |

---

## Features Carried Forward (From Previous Release)

These features from the Feb 2 release are still active:

| Feature | Status |
|---------|--------|
| Triple-Mode Architecture | ✅ Active (Brainstorming, Document Review, Build Venture) |
| 4 Venture Stages | ✅ Active |
| A2A Smart Orchestration | ✅ Active |
| Automatic Red Team | ✅ Active |
| Phase Tracking | ✅ Active |
| GraphRAG | ✅ Active |
| Smart Phase Detection | ✅ Active |
| Phase Insights | ✅ Active |

---

## PRIORITY 1: Recursive Intelligence Test (NEW)

The system now logs and learns from your interactions.

### Test 1: Reaction Detection
| Step | Action | Expected |
|------|--------|----------|
| 1 | Start chat, send: "This is really confusing" | System internally classifies as `negative` |
| 2 | Send: "Aha! Now I understand!" | System internally classifies as `positive` |
| 3 | Send: "Let's try a different approach" | System internally classifies as `redirect` |

**Note:** You won't see the classification directly - it's logged to Supabase silently.

### Test 2: Agent Switch Logging
| Step | Action | Expected |
|------|--------|----------|
| 1 | Start with Lawrence | Session start logged |
| 2 | Switch to TTA bot | Agent switch event logged (from: lawrence, to: tta) |
| 3 | Switch to JTBD | Another switch event logged |

**Verification:** Check Supabase `session_events` table for logged events.

### Test 3: Phase Completion Logging
| Step | Action | Expected |
|------|--------|----------|
| 1 | Start TTA workshop | Phase 1 active |
| 2 | Click "Next Phase" | Phase completion event logged |
| 3 | Progress through phases | Each completion logged with phase name |

---

## PRIORITY 2: Gemini 2.5 Quality Test (NEW)

### Test 1: Document Analysis Quality
| Step | Action | Expected |
|------|--------|----------|
| 1 | Upload a PDF with text and images | Should extract text accurately |
| 2 | Upload a slide deck | Should identify key points per slide |
| 3 | Ask questions about the document | Responses should be accurate and fast |

### Test 2: Response Speed
| Step | Action | Expected |
|------|--------|----------|
| 1 | Ask a complex question | Response should start streaming quickly |
| 2 | Request deep research | Should complete faster than before |

### Test 3: OCR Quality
| Step | Action | Expected |
|------|--------|----------|
| 1 | Upload image with text | Text should be extracted accurately |
| 2 | Upload handwritten notes (if possible) | Should attempt to read handwriting |

---

## PRIORITY 3: Workshop Roadmap UI Test (NEW)

### Test 1: Roadmap Display
| Step | Action | Expected |
|------|--------|----------|
| 1 | Start any workshop bot (TTA, JTBD, Ackoff) | Roadmap should appear in sidebar |
| 2 | Check phase display | Current phase highlighted clearly |
| 3 | Progress through phases | Roadmap updates to show progress |

### Test 2: Roadmap vs Old PhaseProgress
| Step | Action | Expected |
|------|--------|----------|
| 1 | Use workshop bot | Should see WorkshopRoadmap (new) |
| 2 | Should NOT see | Old PhaseProgress component (archived) |

---

## PRIORITY 4: Triple-Mode Entry Points (Carried Forward)

### Test Entry Point Detection
| Message | Expected Entry Point |
|---------|---------------------|
| "I want to explore future trends in AI" | 💡 Brainstorming |
| "Here's my pitch deck to review" | 📄 Document Review |
| "I have a startup idea about food delivery" | 🚀 Build Venture |
| "Hi" (vague) | Show Entry Point Selector |

---

## PRIORITY 5: Phase Tracking (Carried Forward)

The system tracks: **Exploring → Framing → Defining → Solving → Validating → Complete/Stuck**

### Test Phase Transitions
| Step | Action | Expected Phase |
|------|--------|----------------|
| 1 | Start exploring domain with TTA | Exploring |
| 2 | Identify a specific opportunity | Framing |
| 3 | Write clear problem statement | Defining |

---

## Quick Test Checklist

| Test Area | What to Check | Priority |
|-----------|---------------|----------|
| Reaction Classification | System detects positive/negative/redirect | P1 |
| Event Logging | Agent switches logged to Supabase | P1 |
| Gemini 2.5 Speed | Responses faster than before | P2 |
| Document OCR | Text extraction works on PDFs/images | P2 |
| Workshop Roadmap | Displays correctly, updates on progress | P3 |
| Entry Points | Auto-detection working | P4 |
| Phase Tracking | Phase indicator updates | P5 |
| Session Persistence | Context survives page refresh | P5 |

---

## Database Tables to Monitor (NEW)

If you have Supabase access, you can verify the Recursive Intelligence is working:

```sql
-- Check session events (agent switches, phases, reactions)
SELECT * FROM session_events ORDER BY created_at DESC LIMIT 20;

-- Check session summaries
SELECT * FROM session_summaries ORDER BY created_at DESC LIMIT 10;

-- Check extracted insights (after batch processing)
SELECT * FROM session_insights ORDER BY created_at DESC LIMIT 10;

-- Check agent effectiveness scores (after enough data)
SELECT * FROM agent_effectiveness ORDER BY effectiveness DESC;
```

---

## Known Limitations

| Limitation | Details |
|------------|---------|
| Learning takes time | Adaptive routing improves after ~50+ sessions |
| Reaction classification | Pattern-based, may miss subtle signals |
| Triple-Mode UX | Entry point selector can interrupt flow on first message |
| Phase transitions | Require clear signals in conversation |

---

## Commits Included in This Release

| Commit | Description |
|--------|-------------|
| `5974ff8` | **Upgrade to Gemini 2.5-flash** + UI improvements + new utilities |
| `0a4f6f3` | **Add Recursive Intelligence** - session learning system (4 phases) |
| `b268be7` | Rename skills to Mindrian-Team-X convention + auto-update knowledge |
| `fe7bfed` | Add Claude Code skills and commands |
| `615603c` | Add Document AI credentials from JSON env var |
| `182162a` | Add sendgrid package for daily summary emails |
| `d579bb6` | QA analysis corrections from team review |

---

## How to Report Issues

For each issue, please include:
1. **What you typed** (exact message)
2. **What you expected** to happen
3. **What actually happened**
4. **Screenshot** if possible
5. **Browser console errors** if any (F12 → Console)

For Recursive Intelligence issues, also include:
- Session ID (if visible)
- Approximate time of the issue

---

**Questions?** Reach out to Jonathan.

🚀 **Session 500 will now route better than Session 1!**
