# QA Tester Guide — What Changed & What to Test
**Date:** 2026-01-27 (Evening Update)
**Live at:** https://mindrian.onrender.com
**For:** Lawrence, Leah, Edwards, Adam, David

---

## Summary: What's Different When You Open Mindrian Now

### 1. The Main Bot is Now Called "Lawrence"

When you open Mindrian, you'll see **two** versions of the thinking partner:

| Bot | What It Does | Who Should Use It |
|-----|-------------|-------------------|
| **Lawrence** (selected by default) | Clean, focused conversations. Asks questions, keeps responses short. Fewer buttons. | Everyone. Leah, Adam, students, first-time users. |
| **Larry Playground** | Everything turned on — all buttons, research, multi-agent, deep research. | Power users, classroom demos, Lawrence & Sagir testing features. |

**Why we did this:** Lawrence said the buttons are confusing for normal users. Leah only used Synthesize. Edwards agreed feedback should come from a clean version. So now the default is clean, and the playground is for experimentation.

### 2. The "Brain" Got Smarter (Invisible — You Won't See This)

Every message you send now gets scanned in under 5 milliseconds. The system detects patterns and secretly coaches the bot. You'll notice:

- **If you jump to a solution** ("Let's build Uber for plumbing") — Lawrence will push you back to define the problem first
- **If you pile up assumptions** — Red Team gets suggested, and the bot asks you to validate them
- **If you're very confident without evidence** — Academic research button appears
- **If you talk about the future** — Trends data and TTA (Trending to the Absurd) get suggested

None of this is visible. The bot just responds better.

### 3. The Knowledge Graph Now Drives Button Suggestions

The Neo4j graph (the "brain" Sagir mentioned) now decides which research buttons appear based on **relationships between frameworks, tools, and problem types** — not just keywords.

Example: If you mention "S-Curve," the system knows S-Curve relates to patents and adoption timing, so it suggests Patent search and Trends data. This is the hybrid search approach — graph for relationships, file search for content.

### 4. Research Buttons (When They Appear)

Six new buttons can now appear **only when relevant:**

| Button | What It Does | When It Appears |
|--------|-------------|-----------------|
| Academic Evidence | Searches academic papers | When you make claims without citing sources |
| Prior Art & Patents | Searches patent databases | When discussing inventions or innovation |
| Trends | Google Trends data | When talking about the future |
| Gov Data | Government statistics | When discussion needs hard data |
| Find Datasets | Kaggle, data.gov | When analysis needs raw data |
| News Signal | Current news | When assumptions need real-world checking |

**Important:** These only appear when the intelligence layer detects they're useful. They don't clutter the screen otherwise.

---

## What the Team Asked For vs. What's Done

Based on the team conversation:

| Team Request | Status | Notes |
|-------------|--------|-------|
| **Slider on main page (not settings)** | Not yet done | Lawrence wants this badly — keeps forgetting to set it. For now: go to Settings, move slider to 1. |
| **Default slider to 1** | Not yet done | Currently defaults to 5. We agree it should default to 1. |
| **Too many buttons — clean it up** | Partially done | Lawrence bot has fewer buttons by default. Playground keeps everything. |
| **Keep only Synthesize + Research visible** | In progress | Lawrence mode is meant to be simpler. More cleanup coming. |
| **Combine Research + Deep Research into one** | Not yet done | Lawrence prefers just "Research." We'll merge or simplify. |
| **Remove multi-agent from default view** | In progress | Only shows in Playground now, not Lawrence. |
| **Context preserved across bot switches** | Done | Works. When you switch from Lawrence to Red Team, it remembers your conversation. |
| **Links should be clickable** | Partially done | Research results include links. Some are not yet clickable in all views. |
| **What does "Think" button do?** | Needs clarification | It runs a structured analysis workflow. Tooltip exists but isn't clear enough. |

---

## What to Test

### Test A: Open Mindrian Fresh

1. Go to https://mindrian.onrender.com in a new/incognito window
2. Check the dropdown at the top

**You should see:**
- [ ] "Lawrence" is selected (default)
- [ ] "Larry Playground" is available as second option
- [ ] All workshop bots still there (TTA, JTBD, S-Curve, Red Team, Ackoff, etc.)
- [ ] 4 starter buttons appear for Lawrence

### Test B: Lawrence Keeps It Simple (Leah's Test)

1. Stay on Lawrence (default)
2. Type a real problem you're working on
3. Have a 3-4 message conversation

**You should see:**
- [ ] Short, focused responses (not walls of text)
- [ ] Lawrence asks questions instead of giving answers
- [ ] Fewer buttons than before
- [ ] If it suggests switching to another agent, it's only 1-2 suggestions (not five)

### Test C: Solution-Jumping Gets Redirected

1. Type: **"We should build an app for plant therapy for elderly people"**

**You should see:**
- [ ] Lawrence does NOT start building the idea
- [ ] Lawrence asks "What problem are you seeing?" or "Who is struggling?"
- [ ] Feels like a real conversation, not a formulaic redirect

### Test D: Research Buttons Appear When Relevant

1. Type: **"I'm certain AI will replace most jobs by 2030"**

**You should see:**
- [ ] An "Academic Evidence" or "Trends" button appears
- [ ] The bot asks what evidence supports this
- [ ] Clicking the button returns actual results with sources

### Test E: Synthesize & Download Still Works

1. Have a conversation (3+ messages)
2. Click "Synthesize"

**You should see:**
- [ ] A clean summary of your conversation
- [ ] A downloadable file
- [ ] This is the feature Leah used and liked — make sure it still works

### Test F: Switch Between Bots

1. Start in Lawrence
2. Switch to Red Team (from dropdown)
3. Send a message

**You should see:**
- [ ] Red Team knows what you were talking about (context preserved)
- [ ] Buttons change to Red Team's buttons
- [ ] Workshop phases appear on the right side

### Test G: Larry Playground Has Everything

1. Switch to "Larry Playground"
2. Start a conversation

**You should see:**
- [ ] All buttons visible (Research, Think, Deep Research, Synthesize, Multi-Agent, etc.)
- [ ] This is the "everything on" mode for power users and demos

### Test H: Slider Still Works

1. Go to Settings (gear icon)
2. Move slider to 1

**You should see:**
- [ ] Responses become short and focused
- [ ] Much faster, easier to follow
- [ ] This is what Lawrence recommends for everyone

---

## For Edwards: Looking at the Code

The repo is at: https://github.com/jsagir/mindrian-deploy

Key things to know:
- **CLAUDE.md** at the root is the living document that explains everything — start there
- **R&D/** folder has all experiments tried and their status
- **qa/** folder has this guide and test records
- The repo is built so any coding AI (Claude Code, Cursor, etc.) can pick up where Sagir left off
- Everything is in one main file: `mindrian_chat.py` (~4900 lines) + modular `prompts/`, `tools/`, `utils/`

### The "Brain" (for Edwards)

The intelligence layer works in 4 layers:

```
Layer 0: Regex extraction (<5ms) — detects assumptions, certainty, solutions, etc.
Layer 1: Neo4j graph (~50ms) — maps frameworks to research tools via relationships
Layer 2: Problem classification (~50ms) — classifies problem type, suggests approach
Layer 3: Bot-specific hints (<1ms) — hardcoded fallback suggestions per bot
```

All layers run on every message. Results merge together to decide which buttons appear and which agents get suggested. If any layer fails (e.g., Neo4j is down), the others still work.

---

## Known Issues (Don't Report These)

- Slider is still in Settings, not on the main page (known, pending)
- Some API keys may not be configured (buttons will show errors for missing keys — that's expected)
- Voice input is experimental and may not work on all browsers
- PDF images are not extracted (text-only for now)
- Multi-agent analysis can produce very long output (known — that's why it's in Playground, not Lawrence)

---

## How to Give Feedback

Just note:
1. **Which bot** (Lawrence, Playground, Red Team, etc.)
2. **What you did** (what you typed, what you clicked)
3. **What happened** vs **what you expected**
4. **Screenshot** if you can

Send to Sagir or drop in the group chat.

---

*Last updated: 2026-01-27 evening. Covers all commits from the last 12 hours including the Lawrence rename, intelligence layer, research buttons, and graph orchestration changes.*
