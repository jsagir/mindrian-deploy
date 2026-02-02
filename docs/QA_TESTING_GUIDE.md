# QA Testing Guide - Mindrian Release

To: User-Side Testers (QA)

Date: February 2, 2026

Branch: triple-mode-v1

---

## What This Release Addresses

This guide outlines the key changes in the latest release, which directly addresses Armando's feedback on organizing the user experience.

### Key Changes Ready to Test:

1. **Triple-Mode Architecture**: The workspace is now organized into three clear entry points (Brainstorming, Document Review, and Build Venture).

2. **4 Venture Stages**: The Build Venture mode now guides users through four distinct stages of the startup journey (Pre-Opportunity, Opportunity Identified, Well-Defined Problem, and Ready to Build).

3. **A2A Smart Orchestration (NEW)**: The system now automatically classifies your situation and suggests the right bot based on:
   - How uncertain your situation is (Cynefin: Clear, Complicated, Complex, Chaotic)
   - Where you are in problem-solving (PWS: Un-Defined, Ill-Defined, Well-Defined)

4. **Automatic Red Team Validation (NEW)**: Red Team now runs automatically at key moments to challenge your assumptions - not just when you switch to it manually.

5. **Phase Tracking (NEW)**: The system tracks which phase you're in (Exploring, Framing, Defining, Solving, Validating) and shows your progress.

6. **All Features Enabled**: GraphRAG, Smart Phase Detection, Phase Insights, UI Elements, LangExtract - all now active.

### Features Not Included in This Release (Pending):

- Token limit indicator for free users (requires design spec).
- Document save/creation (requires requirements).

---

## PRIORITY 1: Three Entry Points Test

The system should automatically detect which of the three entry points is needed based on the user's first message.

### The Three Entry Points:

| Entry Point | For Users Who... | Example Message |
|-------------|------------------|-----------------|
| Brainstorming | "Don't have an idea yet" | "I want to explore future trends in AI." |
| Document Review | "Have something to analyze" | "Here's my pitch deck to review." |
| Build Venture | "Are building a startup" | "I have a startup idea about food delivery." |

### Your Tests:

**Test 1:** Start new chat → Type: "I'm curious about opportunities in healthcare"
- Expected Result: Should detect **Brainstorming**

**Test 2:** Start new chat → Type: "Review my business plan"
- Expected Result: Should detect **Document Review**

**Test 3:** Start new chat → Type: "I want to build a company"
- Expected Result: Should detect **Build Venture**

**Test 4:** Start new chat → Type: "Hi" (a vague message)
- Expected Result: Should show the **Entry Point Selector** for the user to choose.

---

## PRIORITY 2: Venture Stage Support Test

When the user selects Build Venture, they must select their current stage. This selection determines the recommended helper bots.

### The Four Stages & Recommended Bots:

| Stage | Helps With | Recommended Bots |
|-------|------------|------------------|
| Pre-Opportunity | Finding problems worth solving | Lawrence, TTA, Scenario, Beautiful Question |
| Opportunity Identified | Deep customer understanding | JTBD, Ackoff, Scenario, Knowns |
| Well-Defined Problem | Business model, timing, positioning | Ackoff, S-Curve, Red Team |
| Ready to Build | Stress-testing, risk mapping | Red Team, Scenario, Knowns |

### Your Tests:

1. Start chat → Type: "I want to start a company but have no idea what to build"
2. Select the **Build Venture** entry point.
3. Select **Pre-Opportunity** stage: Confirm you see exploration bots (Lawrence, TTA, etc.) recommended.
4. Change to **Opportunity Identified**: Confirm recommendations change to validation bots (JTBD, Ackoff, etc.).
5. Change to **Ready to Build**: Confirm recommendations change to execution bots (Red Team, Scenario, etc.).

---

## PRIORITY 3: A2A Smart Orchestration Test (NEW)

The system now classifies your message automatically and routes you to the best bot.

### What You Should See:

When you type a message, the system figures out:
- **How uncertain is your situation?** (Cynefin domain)
- **Where are you in solving your problem?** (PWS stage)

### Your Tests:

**Test 1:** Type: "What opportunities exist in sustainable energy?"
- Expected: Should classify as **Complex / Un-Defined**
- Expected: Should suggest **TTA** (exploration bot)

**Test 2:** Type: "People are frustrated with banking apps, how can we help?"
- Expected: Should classify as **Complex / Ill-Defined**
- Expected: Should suggest **JTBD** (refinement bot)

**Test 3:** Type: "How can we reduce patient wait times from 45 min to 15 min?"
- Expected: Should classify as **Complicated / Well-Defined**
- Expected: Should suggest **Validation** or **Solution Design**

**Test 4:** Type: "We have 2 weeks of runway left"
- Expected: Should classify as **Chaotic**
- Expected: Should suggest stabilization first

---

## PRIORITY 4: Automatic Red Team Test (NEW)

Red Team now challenges your assumptions automatically at key moments.

### What You Should See:

After generating ideas with TTA or JTBD, you may see a red message appear that challenges your thinking with questions like:
- "Is this real?"
- "What assumptions are you making?"
- "What could go wrong?"

### Your Tests:

1. Start with TTA → Generate 2-3 opportunity ideas
2. **Watch for**: A Red Team challenge message appearing automatically
3. The challenge should ask probing questions about your assumptions
4. You should NOT need to manually switch to Red Team bot

---

## PRIORITY 5: Phase Tracking Test (NEW)

The system tracks which phase you're in.

### The Phases:

```
Exploring → Framing → Defining → Solving → Validating → Complete
                                              ↓
                                            Stuck
```

### What You Should See:

- A phase indicator showing your current phase
- Phase changes as you progress through your problem-solving journey
- If you go backwards (regression), the system notices

### Your Tests:

1. Start exploring a new domain with TTA
2. **Watch for**: Phase should show "Exploring"
3. When you identify a specific opportunity, phase should change to "Framing"
4. When you write a clear problem statement, phase should change to "Defining"

---

## Supporting Features Test

### Entry Point Auto-Detection Keywords:

| Entry Point | Test Keywords |
|-------------|---------------|
| Brainstorming | "explore," "trends," "brainstorm," "future," "curious" |
| Document Review | "review," "pitch deck," "document," "analyze," "feedback" |
| Build Venture | "startup," "venture," "build," "company," "business," "idea," "product" |

### Mode Toggle (Sandbox vs Workshop):

1. Select any entry point.
2. Find the Mode Toggle and switch between **Sandbox** (free exploration) and **Workshop** (guided phases).
3. Confirm the UI changes correctly.

### Session Persistence (Page Refresh):

1. Select Build Venture → Opportunity Identified stage.
2. Send 3-4 messages.
3. Refresh the page (F5).
4. Confirm your entry point, venture stage, and conversation history are all intact.

### GraphRAG Context (NEW - Now Active):

1. Ask about a PWS concept: "What is Jobs to Be Done?"
2. **Watch for**: Response should include relevant frameworks and connections from the knowledge graph.
3. Ask a follow-up: "How does it relate to process mapping?"
4. **Watch for**: Should show relationships between concepts.

### Phase Insights (NEW - Now Active):

1. Work through 4-5 turns in a workshop bot (TTA, JTBD, etc.)
2. **Watch for**: Progress insights appearing that show what you've covered
3. **Watch for**: Suggestions for what to explore next

---

## Quick Test Checklist Summary

| Test Area | What to Check |
|-----------|---------------|
| Entry Points | Auto-detection for keywords, selector for vague messages |
| Venture Stages | Recommended bots change correctly for each stage |
| A2A Classification | Message classified on Cynefin + PWS dimensions |
| Auto Red Team | Challenges appear automatically after generating ideas |
| Phase Tracking | Phase indicator shows and updates |
| Persistence | Session context survives page refresh |
| GraphRAG | Knowledge graph enriches responses |
| Phase Insights | Progress shown after several turns |

---

## Known Limitations

1. **Classification accuracy**: The classifier is new - some messages may be misclassified. Report any consistent errors.

2. **Red Team timing**: Auto Red Team may not fire on every output - it's designed to fire at key moments, not constantly.

3. **Phase transitions**: Phase changes require clear signals in the conversation. Subtle shifts may not be detected.

---

## How to Report Issues

For each issue, please include:
1. What you typed (exact message)
2. What you expected to happen
3. What actually happened
4. Screenshot if possible

---

Let me know what works and what doesn't!

Jonathan
