# Larry's Sequential Thinking Patterns

When Larry encounters complex problems, he uses the sequential thinking tool to work through them methodically.

## When to Use Sequential Thinking

| Situation | Trigger |
|-----------|---------|
| Complex debugging | Multiple possible causes |
| Feature decisions | Trade-offs and implications |
| Strategic questions | Multiple stakeholders or futures |
| Architecture changes | Ripple effects |
| Problem classification | Ambiguous problem type |

## Core Patterns

### Pattern 1: Problem Definition Sequence

**Use when**: User presents a vague challenge or jumps to solution

```
Thought 1: What did the user literally ask for?
           → Extract the surface-level request

Thought 2: What problem might be behind this request?
           → Hypothesize the underlying need

Thought 3: What assumptions are embedded in their framing?
           → Identify hidden constraints or biases

Thought 4: What would change if those assumptions were wrong?
           → Test the problem definition

Thought 5: What's the real problem worth solving here?
           → Reframe if necessary

Thought 6: Verify: Does this reframe resonate with what user needs?
           → Check alignment before proceeding
```

**Example**:
```
User: "We need better error messages."

Thought 1: User wants improved error messages in Mindrian
Thought 2: Underlying need might be: users confused, debugging hard, trust issues
Thought 3: Assumption: error messages ARE the problem (vs. errors happening at all)
Thought 4: If errors shouldn't happen → fix root cause, not messages
Thought 5: Real problem might be: "Users encounter errors that break their flow"
Thought 6: Ask user: "Are users seeing errors they shouldn't, or just confused by valid errors?"
```

---

### Pattern 2: Debug Diagnosis Sequence

**Use when**: Something isn't working as expected in Mindrian

```
Thought 1: What's the expected behavior?
           → Define the correct state

Thought 2: What's the actual behavior?
           → Define the failure state

Thought 3: What's the delta between expected and actual?
           → Characterize the gap

Thought 4: Where in the code flow would this delta emerge?
           → Locate the divergence point

Thought 5: What are the possible causes at that point?
           → Enumerate hypotheses (3-5 max)

Thought 6: Which cause is most likely given the symptoms?
           → Rank by probability

Thought 7: What evidence would confirm or refute?
           → Define test criteria

Thought 8: Check evidence in codebase or logs
           → Verify hypothesis

Thought 9: If hypothesis wrong, revise and repeat from Thought 5
           → Iterate if needed
```

**Example**:
```
Issue: Bot personality bleeds between sessions

Thought 1: Expected: Each bot has distinct personality throughout session
Thought 2: Actual: Lawrence sometimes responds like Red Team
Thought 3: Delta: Identity not maintained, seems to "remember" previous bot
Thought 4: Divergence point: Bot switch handler or context persistence
Thought 5: Causes: (a) Context not cleared (b) Prompt not switched (c) Model caching
Thought 6: Most likely: (a) Context not cleared - explains "remembering" behavior
Thought 7: Evidence: Check context_store state after bot switch
Thought 8: Found: context_store retains previous bot's context
Thought 9: Confirmed - fix should clear context on switch
```

---

### Pattern 3: Feature Decision Sequence

**Use when**: Evaluating whether to build something

```
Thought 1: What specific problem does this feature solve?
           → Problem statement

Thought 2: Is this problem REAL? What evidence exists?
           → Validation of need

Thought 3: How many users have this problem? How often?
           → Scope and frequency

Thought 4: What do users do today without this feature?
           → Current workaround

Thought 5: Can we WIN? What's our advantage in solving this?
           → Competitive position

Thought 6: Is it WORTH IT? ROI vs. other priorities?
           → Resource allocation

Thought 7: What's the MVP that validates the hypothesis?
           → Minimum viable test

Thought 8: What signal would tell us to kill this feature?
           → Kill criteria

Thought 9: Decision: Build / Don't build / Need more info
           → Clear recommendation
```

**Example**:
```
Feature: Add voice input to Mindrian

Thought 1: Problem: "Users want hands-free interaction during workshops"
Thought 2: Evidence: 2 user requests, no usage data. WEAK evidence.
Thought 3: Scope: Unknown - need to survey
Thought 4: Workaround: Users type. Not mentioned as painful.
Thought 5: Advantage: None special - many tools have voice
Thought 6: Worth it: Engineering cost high, unclear benefit
Thought 7: MVP: Could add browser speech-to-text in 2 days
Thought 8: Kill signal: <5% usage after 2 weeks
Thought 9: Decision: NEED MORE INFO - survey users first
```

---

### Pattern 4: Architecture Impact Sequence

**Use when**: Considering a change that affects multiple components

```
Thought 1: What change is being proposed?
           → Define the modification

Thought 2: What components directly touch this code?
           → First-order dependencies

Thought 3: What components depend on those components?
           → Second-order effects

Thought 4: What data flows through this path?
           → Information dependencies

Thought 5: What could break if we make this change?
           → Risk inventory

Thought 6: How would we know if something broke?
           → Detection mechanisms

Thought 7: What's the rollback plan?
           → Recovery strategy

Thought 8: Is the change worth the risk?
           → Final assessment
```

---

### Pattern 5: Strategic Analysis Sequence

**Use when**: Long-term direction questions

```
Thought 1: What decision are we actually making?
           → Clarify the choice

Thought 2: What are the critical uncertainties?
           → Unknowns that matter

Thought 3: What are the possible futures for each uncertainty?
           → Scenario building

Thought 4: What would we do in each future?
           → Strategy per scenario

Thought 5: What's robust across all futures?
           → No-regret moves

Thought 6: What's the decision we need to make NOW?
           → Immediate action

Thought 7: What would make us revisit this decision?
           → Review triggers
```

---

### Pattern 6: Hypothesis Refinement Sequence

**Use when**: Initial understanding might be wrong

```
Thought 1: State initial hypothesis clearly
           → H1: [statement]

Thought 2: What would confirm this hypothesis?
           → Confirming evidence

Thought 3: What would refute this hypothesis?
           → Disconfirming evidence

Thought 4: Seek evidence (query, check code, ask user)
           → Gather data

Thought 5: Does evidence support or refute?
           → Evaluate

Thought 6: If supported, proceed with confidence
           If refuted, generate alternative hypothesis
           → Branch

Thought 7: (If refuted) H2: [new statement]
           → Revised hypothesis

Thought 8: Repeat from Thought 2 with H2
           → Iterate until confident
```

---

## Sequential Thinking Tool Parameters

When Larry uses the sequential thinking tool:

```json
{
  "thought": "Current thinking step - analysis or observation",
  "thoughtNumber": 1,
  "totalThoughts": 5,
  "nextThoughtNeeded": true,
  "isRevision": false,
  "needsMoreThoughts": false
}
```

**Key Parameters**:
- `thought`: The actual reasoning step
- `thoughtNumber`: Current step (1-indexed)
- `totalThoughts`: Estimated total (can be revised)
- `nextThoughtNeeded`: Continue thinking?
- `isRevision`: Is this revising earlier thinking?
- `revisesThought`: Which thought number being revised
- `needsMoreThoughts`: Extend beyond initial estimate?

---

## Anti-Patterns (What Larry Avoids)

### Don't: Jump to conclusions
```
❌ Thought 1: User wants X. Build X.
```

### Don't: Skip evidence gathering
```
❌ Thought 1: Hypothesis
❌ Thought 2: Assume hypothesis is true
❌ Thought 3: Proceed based on assumption
```

### Don't: Ignore disconfirming evidence
```
❌ Thought 4: Found evidence against hypothesis
❌ Thought 5: But I'll proceed anyway because...
```

### Don't: Get stuck in analysis paralysis
```
❌ Thought 15: Still not sure...
❌ Thought 16: Let me think more...
❌ Thought 17: Maybe if I consider...
→ After ~8-10 thoughts, make a decision or identify what info is needed
```

---

## Integration with Neo4j

Larry often combines sequential thinking with Neo4j queries:

```
Thought 3: I need to check what frameworks apply to this problem type
           → [Query Neo4j]
           
Thought 4: Based on the query results, the relevant framework is X
           → [Continue reasoning]
```

This grounds the thinking in actual methodology rather than assumptions.
