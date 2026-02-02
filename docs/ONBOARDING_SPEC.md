# Mindrian Onboarding Specification

## Problem Statement

Users who haven't taken PWS classes don't know:
- What the workshops are
- Where to start
- What buttons to press

**Key Quote:** "For someone who hasn't been in any of professor Aronhime's classes, doesn't know what these different workshops are... they don't know what the content is and if they were shown this, how would they know where to start?"

---

## Design Principles

1. **Don't assume PWS knowledge** - Explain in plain terms
2. **Ask, don't show everything** - "What brings you here today?"
3. **One choice at a time** - Don't overwhelm
4. **Show, then explain** - Visual first, details on hover
5. **Progressive disclosure** - More options as needed

---

## Onboarding Flow

### Step 1: Welcome Screen

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                         Welcome to Mindrian                          │
│                                                                      │
│              What brings you here today?                             │
│                                                                      │
│   ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│   │                   │  │                   │  │                   │
│   │    🔍 EXPLORE     │  │    📄 REVIEW      │  │    🚀 BUILD       │
│   │                   │  │                   │  │                   │
│   │  I want to        │  │  I have documents │  │  I want to        │
│   │  explore ideas    │  │  to get feedback  │  │  build a startup  │
│   │                   │  │  on               │  │                   │
│   └───────────────────┘  └───────────────────┘  └───────────────────┘
│                                                                      │
│   These are the only three things users do with Mindrian.            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Copy for each card:**

| Card | Title | Subtitle | Description on hover |
|------|-------|----------|---------------------|
| Explore | Explore Ideas | "I want to explore ideas" | "Free-form brainstorming. Take the conversation wherever it goes. Great for early-stage thinking." |
| Review | Review Documents | "I have documents to get feedback on" | "Upload pitch decks, business plans, or research papers. Get structured feedback and challenges." |
| Build | Build a Startup | "I want to build a startup" | "Structured journey from problem discovery to business case. Step-by-step guidance." |

### Step 2a: Explore Path

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                    Let's explore together                            │
│                                                                      │
│   Tell me what's on your mind. It could be:                         │
│                                                                      │
│   • A trend you're curious about                                    │
│   • An industry you want to understand                              │
│   • A problem you've noticed                                        │
│   • Just a vague idea                                               │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ What are you curious about?                                  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   [Start Exploring →]                                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 2b: Review Path

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                    Let's review your document                        │
│                                                                      │
│   What kind of document do you have?                                │
│                                                                      │
│   ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│   │   📊 Pitch Deck   │  │   📋 Business     │  │   📝 Research     │
│   │                   │  │      Plan         │  │      Paper        │
│   └───────────────────┘  └───────────────────┘  └───────────────────┘
│                                                                      │
│   ┌───────────────────┐  ┌───────────────────┐                      │
│   │   💡 One-Pager    │  │   📄 Other        │                      │
│   └───────────────────┘  └───────────────────┘                      │
│                                                                      │
│   [Upload Document →]                                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 2c: Build Path

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                    Where are you in your journey?                    │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  🌱  PRE-OPPORTUNITY                                        │   │
│   │      "I don't have an idea yet"                             │   │
│   │      We'll help you find problems worth solving             │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  🎯  OPPORTUNITY IDENTIFIED                                 │   │
│   │      "I see a problem but need to understand it deeper"     │   │
│   │      We'll help you validate and refine                     │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  📋  WELL-DEFINED PROBLEM                                   │   │
│   │      "I know the problem, need a business model"            │   │
│   │      We'll help you build the business case                 │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  🚀  READY TO BUILD                                         │   │
│   │      "I have a plan, need to stress-test it"                │   │
│   │      We'll challenge your assumptions                       │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Button Hover Explanations

When contextual buttons spawn, hover should explain WHY:

### Example: Red Team Button

```
┌──────────────────────────────────────────────────────────────────┐
│  [🔴 Challenge This] ←── HOVER                                   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                             │  │
│  │  Why this appeared:                                        │  │
│  │  You made a claim about market size. Let me play devil's   │  │
│  │  advocate and challenge your assumptions.                  │  │
│  │                                                             │  │
│  │  What I'll do:                                             │  │
│  │  Ask hard questions about your evidence and reasoning.     │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Example: Research Button

```
┌──────────────────────────────────────────────────────────────────┐
│  [🔍 Research This] ←── HOVER                                    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                             │  │
│  │  Why this appeared:                                        │  │
│  │  You mentioned "sustainable energy" - I can find current   │  │
│  │  trends, market data, and recent developments.             │  │
│  │                                                             │  │
│  │  What I'll do:                                             │  │
│  │  Search the web and summarize what I find.                 │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Example: Example Button

```
┌──────────────────────────────────────────────────────────────────┐
│  [💡 Show Example] ←── HOVER                                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                             │  │
│  │  Why this appeared:                                        │  │
│  │  You're working on customer discovery. I can show you      │  │
│  │  how other founders approached this.                       │  │
│  │                                                             │  │
│  │  What I'll do:                                             │  │
│  │  Share a real-world case study with credible sources.      │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Error States

### Missing Required Selection

Instead of silently returning to main screen:

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  ⚠️  One more thing needed                                       │
│                                                                   │
│  Please select what you'd like me to analyze:                    │
│                                                                   │
│  ○ Your recent opportunity idea                                  │
│  ○ The market assumption you mentioned                           │
│  ○ Your business model                                           │
│                                                                   │
│  [Continue →]                                                    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Progressive Disclosure

### Level 1: Main Interface
- Three entry points
- Chat area
- Basic action buttons

### Level 2: After First Interaction
- Contextual buttons spawn
- Progress indicator appears
- Right panel activates

### Level 3: Power User Features
- Agent selection (hidden by default)
- Advanced settings
- Export options

---

## Copy Guidelines

### Do
- Use plain English ("challenge your thinking" not "red team")
- Explain WHY, not just WHAT
- Give examples of what will happen
- Use second person ("You mentioned..." not "The user mentioned...")

### Don't
- Assume PWS knowledge
- Use jargon (JTBD, TTA, Cynefin without explanation)
- Show all options at once
- Leave buttons unexplained

---

## Implementation Priority

| Component | Priority | Complexity |
|-----------|----------|------------|
| Welcome screen with 3 cards | Critical | Low |
| Hover explanations on buttons | Critical | Medium |
| Error states instead of silent failure | Critical | Low |
| Venture stage selection | High | Medium |
| Document type selection | High | Low |
| Progressive disclosure | Medium | High |

---

## Testing Checklist

- [ ] User with no PWS knowledge can start within 30 seconds
- [ ] All required selections have visual indicators
- [ ] Hover explanations appear on all spawned buttons
- [ ] Error states show instead of silent failures
- [ ] User can always get back to the start
- [ ] No dead ends
