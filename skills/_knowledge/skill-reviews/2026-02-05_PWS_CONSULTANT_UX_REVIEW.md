# PWS Consultant: UI/UX Architecture Review

**Date:** 2026-02-05
**Reviewer:** UI/UX Architect
**Artifact Reviewed:** `journals/pws_consultant_simulation.md` (end-to-end simulation)
**Components Reviewed:** `DiagnosticFlow.jsx`, `DiagnosisResult.jsx`, `ExpertPanel.jsx`
**Cross-Referenced:** Final Plan, Chainlit features reference, Mindrian patterns, solution patterns
**Status:** Review complete -- 17 findings, 4 critical

---

## Overall Assessment

The PWS Consultant simulation describes a compelling three-stage structured consulting flow (Intro, Diagnostic, Consulting with Expert Panel) that is architecturally sound and conversationally rich. Larry's voice is excellent -- warm, probing, never robotic. The JTBD breakthrough moment at Turn 9 is genuinely well-paced. However, the UI/UX layer has significant gaps that will undermine the experience in production. The most damaging issues are: (1) a jarring "information dump" when DiagnosisResult and ExpertPanel appear simultaneously with no interpretive bridge, (2) a diagnostic flow that lacks undo/back navigation and provides no feedback on answer selection, (3) an expert panel that gives users no way to understand what each expert actually offers before committing to a consultation, and (4) missing mobile responsiveness in the ExpertPanel's 2-column grid. The conversational design is ahead of the component design -- the Larry voice carries the experience, but the UI components need to match that level of thoughtfulness.

---

## Findings

### CRITICAL

---

#### Finding 1: DiagnosisResult + ExpertPanel Simultaneous Reveal Creates Cognitive Overload

**Severity:** CRITICAL
**Area:** Cognitive Load, Component Sequencing

**What happens:** At timestamp 14:05:42-46, the simulation shows three things appearing within 4 seconds: (1) the DiagnosisResult component (problem type card with icon, name, confidence score, description, key question, 6 framework badges, secondary type note, and complexity/confidence metadata), (2) the ExpertPanel component (5 expert cards in a 2-column grid), and (3) Larry's bridge/transition message. The user goes from answering a simple MCQ to seeing approximately 400 words of structured information plus 5 interactive cards.

**Why it is a problem:** This violates the progressive disclosure principle. The user has just finished a focused, sequential 5-question flow. Their mental model is "one thing at a time." Suddenly dropping two dense components plus prose breaks the pacing rhythm entirely. Users will not read the DiagnosisResult card carefully -- they will skim it, miss the key question (which is the most important element), and immediately see the ExpertPanel without understanding what the diagnosis means for them. The simulation itself flags this as a P1 gap (no interpretive bridge), but even with the bridge, the visual density is excessive.

**Recommended fix:**
1. **Stagger the reveals.** Show DiagnosisResult first. Wait for user acknowledgment (explicit "Got it" button or natural chat response). Then show the bridge message from Larry (Task 6). Then reveal the ExpertPanel as a separate message below.
2. **Collapse the ExpertPanel initially.** Show it as a single line -- "5 domain experts are ready to consult. Expand panel." -- and let the user open it when they are ready. The ExpertPanel component already supports a `loading` state; add a `collapsed` state.
3. **Animate the DiagnosisResult reveal.** A brief 300ms fade-in on the card communicates intentionality. Right now the component has no entry animation.

---

#### Finding 2: ExpertPanel 2-Column Grid Breaks on Mobile (375px)

**Severity:** CRITICAL
**Area:** Mobile UX

**What happens:** The ExpertPanel component uses `gridTemplateColumns: "1fr 1fr"` (line 71 of ExpertPanel.jsx) with no responsive breakpoint. Each expert card has `padding: "14px 12px"` and contains an icon (20px), role text (13px font, 600 weight), and a subdomain label (11px font). On a 375px screen, the Chainlit chat area is approximately 335px wide after padding. A 2-column grid gives each card approximately 160px.

**Why it is a problem:** At 160px width, the role names will truncate or wrap awkwardly. "Cross-Domain Innovator" is 22 characters at 13px/600 weight -- roughly 140px. With icon (20px + 8px gap), that exceeds the column width. The subdomain text will stack below, creating cards of wildly different heights in the same row. With 5 experts, the last card sits alone in a half-empty row, which looks broken. Most critically, the touch target for each card button is only ~160px wide by ~60px tall, which is adequate but tight for the amount of content inside.

**Recommended fix:**
1. Add a responsive rule: `gridTemplateColumns: experts.length <= 3 ? "1fr" : "1fr 1fr"` on desktop, always `"1fr"` on mobile. Use a CSS media query or a React state check for viewport width.
2. Alternatively, switch to a horizontal scrollable row on mobile (like the WorkshopTimeline pattern planned in Task 7). This preserves screen real estate.
3. Truncate role names to 18 characters on mobile with a tooltip for the full name.

---

#### Finding 3: No Back/Undo Mechanism in DiagnosticFlow

**Severity:** CRITICAL
**Area:** Interaction Friction, Error States

**What happens:** The DiagnosticFlow component presents one question at a time with 4 option buttons. Each button click fires `callAction("diagnostic_answer", ...)` immediately. There is no "Back" button, no confirmation step, and no way to change a previous answer. The simulation shows 5 sequential selections (Q1-Q5) at timestamps 14:03:20 through 14:05:40.

**Why it is a problem:** Users regularly misclick, especially on mobile. The option buttons have `height: "auto"` and `padding: "12px 16px"` with full-width layout -- the touch targets are good, but the options are stacked vertically with only 8px gap. A fast-scrolling thumb can easily hit the wrong option. More importantly, users may read a later question that recontextualizes an earlier answer. ("Oh, Q3 makes me realize I should have answered Q1 differently.") Without undo, the user is locked into a potentially inaccurate diagnosis. The simulation's scoring shows cumulative scores -- a single wrong answer on Q1 can skew the final result by 15-20%.

**Recommended fix:**
1. Add a "Back" button below the options (left-aligned, ghost variant) that appears for Q2-Q5. On click, it fires `callAction("diagnostic_back", { questionNumber: questionNumber - 1 })` and the Python handler pops the last answer from `pws_diagnostic_answers`.
2. Show a compact summary of previous answers below the progress bar: "Q1: General area | Q2: Many stakeholders | ..." as clickable links that navigate back.
3. Add a brief 200ms visual confirmation when an option is selected -- the button should flash to a "selected" state (filled background, check icon) before transitioning to the next question. Right now the transition is instant and there is no feedback that the click registered.

---

#### Finding 4: No Selection Feedback on Diagnostic Option Buttons

**Severity:** CRITICAL
**Area:** Missing Affordances, Diagnostic UX

**What happens:** When a user clicks an option in DiagnosticFlow, the `handleAnswer` function calls `callAction` immediately. There is no visual state change on the button -- no active state, no loading indicator, no "selected" style. The next question appears (presumably via a prop update from Python), but the transition between questions has no animation or indication.

**Why it is a problem:** Without immediate visual feedback, users in a low-confidence moment (which is exactly when you are answering diagnostic questions about an ambiguous problem) will wonder: "Did my click register? Did I pick the right one? Which one did I pick?" This is especially problematic because the buttons use `variant="outline"` -- they look identical before and after clicking. On a slow network connection, there could be a 500ms+ delay between the click and the next question appearing, during which the user sees no change and may click again (double-submission).

**Recommended fix:**
1. Add local state to track the selected option index: `const [selected, setSelected] = useState(null)`. On click, set the index, apply a filled/highlighted style to that button, disable all buttons, then call `callAction` after a 250ms delay for visual feedback.
2. Add a brief cross-fade animation between questions. The current question should fade out (150ms) and the next should fade in (150ms). This communicates "you answered, here is the next one."
3. Add a `disabled` state to prevent double-clicks while the action is in flight.

---

### HIGH

---

#### Finding 5: Expert Panel Cards Lack Sufficient Affordance for Decision-Making

**Severity:** HIGH
**Area:** Expert Panel UX, Missing Affordances

**What happens:** Each expert card in ExpertPanel shows: an emoji icon, a role name (e.g., "Domain Insider"), and a subdomain label (e.g., "Telemedicine"). That is all. The `focus` and `full_title` fields from the expert data are not rendered. The user must decide which expert to consult based on a role name and a one-word subdomain. There is no "Consult" button label -- the entire card is the button.

**Why it is a problem:** Users face a 5-way decision with insufficient information. "Should I click the Skeptical Analyst or the Cross-Domain Innovator?" requires understanding what each expert will do. The `focus` field contains exactly this information ("Challenge every assumption about Healthcare Technology") but it is not displayed. The card's `onClick` handler also provides no tooltip or hover preview. Users will either (a) click randomly, (b) default to the first card, or (c) not click any card because the decision feels overwhelming.

**Recommended fix:**
1. Display the `expert.focus` text on the card. It is currently available in the props but not rendered. Add it as a third line below the subdomain, with `fontSize: 11, opacity: 0.6, lineHeight: 1.3`.
2. Add an explicit "Consult" text label or chevron icon on each card to clarify that it is clickable and what clicking does.
3. Consider adding a hover/press state that expands the card slightly to show the full focus description and an explicit "Start Consultation" button. This two-step interaction reduces accidental clicks and gives users confidence in their choice.

---

#### Finding 6: No Visual Indicator of Expert Mode During Consultation

**Severity:** HIGH
**Area:** Expert Panel UX, Visual Hierarchy

**What happens:** When the user clicks an expert card (Turn 11, End-User Advocate), Larry's voice changes to the expert's perspective. The simulation shows Larry saying "Let me put on a different hat for a moment." When returning (Turn 12), Larry says "Coming back to my own perspective now." The mode transition is conveyed entirely through text.

**Why it is a problem:** In a scrolling chat interface, the user may not notice the textual cue, especially if they scroll up to re-read something and then scroll back down. There is no persistent visual indicator that "you are now in expert consultation mode." If the user sends a message during expert mode, they may not realize Larry is still responding as the expert. The transition back ("Coming back to my own perspective now") is easy to miss in a long conversation.

**Recommended fix:**
1. When expert mode activates, show a colored banner at the top of the chat (or as an inline element) with the expert's icon, role, and subdomain: "Currently consulting: End-User Advocate (Rural Health)". Use the expert's `color` for the banner background.
2. Add a "Return to Larry" button on the banner that fires `callAction("exit_expert_mode", {})`.
3. Apply a subtle left-border color to messages sent during expert mode, matching the expert's color. This creates a visual "lane" in the conversation history that the user can identify when scrolling.
4. The ConsultantBadge.jsx planned in Task 10 partially addresses this, but it is scoped to show the problem type, not the expert mode. Extend it or create a separate ExpertModeBanner component.

---

#### Finding 7: Diagnostic Flow Feels Like a Quiz, Not a Conversation

**Severity:** HIGH
**Area:** Diagnostic UX, Interaction Friction

**What happens:** The DiagnosticFlow component presents a card with a question and 4 buttons. Larry provides commentary between questions (e.g., "Good -- knowing the area is more than most people start with."). However, the MCQ card is a separate UI element from Larry's messages, creating a visual split between the conversational Larry and the clinical diagnostic.

**Why it is a problem:** The simulation's intro phase (Turns 1-2) establishes an intimate, conversational tone. Larry mirrors the user's language, asks probing follow-ups, and builds rapport. Then the diagnostic phase drops a structured card with radio-button-style options. The tonal shift is jarring -- it feels like switching from a therapy session to a standardized test. Larry's between-question comments help, but they appear as separate messages below the card, creating a disjointed visual rhythm: [card] [Larry comment] [card] [Larry comment].

**Recommended fix:**
1. Embed Larry's commentary inside the DiagnosticFlow card itself. Add a `commentary` prop that appears as a quote block above the question text, styled in Larry's voice. This keeps everything in one visual container.
2. Consider a more conversational framing for the questions. Instead of "How clearly can you describe the problem?" try Larry's voice: "If I asked you to explain this problem to a stranger in 30 seconds -- how confident would you feel?" The scoring stays the same, but the tone matches.
3. Add a brief intro line at the top of the first diagnostic card: "I'm going to ask you 5 quick questions. These aren't a test -- they help me figure out what kind of thinking tools will help you most."

---

#### Finding 8: No Way to Dismiss or Minimize Completed Components

**Severity:** HIGH
**Area:** Interaction Friction, Visual Hierarchy

**What happens:** Once the DiagnosticFlow is complete, the DiagnosisResult and ExpertPanel components appear inline in the chat. As the consulting conversation continues (Turns 8-13), these components remain visible in the scroll history. The user scrolling up sees: [DiagnosticFlow Q5 card] [DiagnosisResult card] [ExpertPanel card] [Larry's bridge message] [consulting messages...].

**Why it is a problem:** The inline components create visual clutter in the conversation history. The DiagnosticFlow card for Q5 is no longer interactive but still looks like it is. The DiagnosisResult card contains information the user may want to reference, but it occupies significant vertical space. On mobile, scrolling past three full-width cards to find a specific Larry message is tedious. The ExpertPanel card remains at its original scroll position, so after 6+ consulting messages, the user must scroll up significantly to consult another expert.

**Recommended fix:**
1. After diagnostic completion, collapse the DiagnosticFlow card into a single-line summary: "Diagnostic complete: 5/5 answered." Use `updateElement()` or `deleteElement()` from the Chainlit JSX API.
2. Pin the ExpertPanel to a persistent location. Options: (a) use `display="side"` to put it in the sidebar (following the Persistent Sidebar pattern from solution-patterns.md), or (b) re-send the ExpertPanel as part of each consulting-phase message (lightweight -- just update the element reference).
3. Add a "minimize" toggle to DiagnosisResult that collapses it to a single-line badge showing the icon + type name + confidence. The full card can be expanded on click.

---

### MEDIUM

---

#### Finding 9: Progress Bar in DiagnosticFlow Is Nearly Invisible

**Severity:** MEDIUM
**Area:** Visual Hierarchy, Missing Affordances

**What happens:** The DiagnosticFlow progress bar is 2px tall (`height: 2`) with a background of `rgba(255,255,255,0.08)` and a gradient fill. The question counter shows "1/5" in monospace at 12px with 0.5 opacity.

**Why it is a problem:** At 2px, the progress bar is more of a decorative line than a functional indicator. Users scanning the card will see the question text and the option buttons but may not notice the progress bar or the counter. For a 5-question flow, progress awareness is important for managing expectations ("How much longer?"). The 0.5 opacity on the counter further reduces its visibility.

**Recommended fix:**
1. Increase progress bar height to 4-6px.
2. Increase counter opacity to 0.7 and add a label: "Question 1 of 5" instead of just "1/5".
3. Consider a step indicator (5 dots or circles) instead of a continuous bar, as discrete steps better communicate the finite number of questions.

---

#### Finding 10: No Loading State Between Diagnostic Completion and Component Appearance

**Severity:** MEDIUM
**Area:** Timing & Pacing

**What happens:** The simulation shows diagnostic scoring at 14:05:41, DiagnosisResult at 14:05:42, and ExpertPanel at 14:05:46. In production, the scoring computation, expert panel collection, and component rendering may take 1-5 seconds depending on network latency and the async `build_expert_panel()` completion.

**Why it is a problem:** After answering Q5, the user expects something to happen. If there is a delay with no visual feedback, they may think the system is stuck. The ExpertPanel component does have a `loading` state with a pulsing dot and "Building your expert panel..." text, but the simulation does not indicate whether this state is actually shown during the gap between Q5 answer and panel display.

**Recommended fix:**
1. Immediately after Q5 is answered, show a transitional message: "Analyzing your answers..." with a typing indicator or Step element.
2. Show the ExpertPanel in its `loading` state immediately, then update it with expert data when the `build_expert_panel()` task completes.
3. Show DiagnosisResult with a brief "reveal" animation -- perhaps the confidence score counts up from 0% to 76% over 1 second. This creates a sense of computation happening.

---

#### Finding 11: DiagnosisResult Confidence Score and Complexity Lack Context

**Severity:** MEDIUM
**Area:** Cognitive Load, Missing Affordances

**What happens:** The DiagnosisResult card shows "Complexity: high" and "Confidence: 76%" at `fontSize: 12` with `opacity: 0.5`. These metrics appear as raw numbers without explanation.

**Why it is a problem:** "Confidence: 76%" is ambiguous. Does it mean the system is 76% sure this is an ill-defined problem? Or 76% of the answers pointed to ill-defined? Or 76% is the probability the diagnosis is correct? Without context, the number either confuses users or is ignored entirely. "Complexity: high" suffers the same problem -- high relative to what? The low opacity suggests these are secondary information, but they influence user trust in the diagnosis.

**Recommended fix:**
1. Add a tooltip (using shadcn's `Tooltip` component) on the confidence value explaining: "76% of your answers align with Ill-Defined Problem characteristics."
2. Replace "Complexity: high" with a more descriptive label: "Typical complexity: High -- multiple stakeholders, competing needs" (derived from the characteristics list).
3. Alternatively, remove these raw metrics from the card and incorporate them into Larry's bridge message where he can explain them in context.

---

#### Finding 12: No Confirmation Before Expert Consultation Starts

**Severity:** MEDIUM
**Area:** Interaction Friction, Expert Panel UX

**What happens:** Clicking an expert card immediately fires `callAction("consult_expert", ...)`. The expert consultation begins in the next message. There is no "Are you sure?" or preview of what the expert will focus on.

**Why it is a problem:** Expert consultations change Larry's voice and perspective. This is a meaningful mode shift. An accidental click (especially on mobile with the tight 2-column grid) starts a consultation the user did not intend. There is also no indication of how long the consultation will last or what it will cover. Users who clicked out of curiosity may feel trapped.

**Recommended fix:**
1. On first click, expand the card to show the expert's full focus description and approach, with an explicit "Start Consultation" button. Second click (the button) fires the action.
2. Alternatively, show a brief inline preview: "The End-User Advocate will analyze your problem from the patient's perspective, using Jobs to Be Done and struggling moments. Start consultation?" with a confirm button.
3. Add a persistent "Exit Consultation" button during expert mode (see also Finding 6).

---

#### Finding 13: Conversation Starters Do Not Map to the Structured Process

**Severity:** MEDIUM
**Area:** Component Sequencing

**What happens:** The welcome message shows 4 starters: "I have a problem I need help thinking through," "I'm not sure what kind of problem I have," "I have a specific hypothesis to validate," and "I'm exploring a broad opportunity space." These are all free-text conversation initiators.

**Why it is a problem:** The starters do not align with the structured process that follows. The third option ("I have a specific hypothesis to validate") implies the user already has a well-defined problem, which should potentially skip the diagnostic or bias it. The fourth option ("I'm exploring a broad opportunity space") implies an undefined problem. But the system treats all of these identically -- the user types or clicks, Larry responds, and eventually the diagnostic appears. The starters create expectations of differentiation that the system does not deliver.

**Recommended fix:**
1. Map starters to process shortcuts: (a) the first two go to the standard intro-then-diagnostic flow, (b) the third ("hypothesis to validate") could pre-select "well_defined" or jump to a shortened diagnostic, (c) the fourth ("broad exploration") could pre-select "undefined" and surface exploration-specific frameworks.
2. At minimum, ensure Larry's first response acknowledges the specific starter chosen and adjusts his probing accordingly. The current simulation shows the same intro flow regardless of which starter is clicked.

---

#### Finding 14: No Session Recovery for Diagnostic Interruption

**Severity:** MEDIUM
**Area:** Error States & Edge Cases

**What happens:** The simulation's QA test case TC-04 mentions: "Complete Q3, refresh browser -> Resume at Q4 (diagnostic answers preserved)." However, the simulation also notes that `cl.user_session` is lost on browser refresh unless using data persistence.

**Why it is a problem:** If a user is on Q3 of 5 and their browser refreshes (network hiccup, accidental navigation, mobile app switch), they lose their diagnostic progress. The DiagnosticFlow component receives `currentQuestion` and `answers` as props from the Python session -- if the session is gone, these are reset. The user must start the diagnostic over. For a flow that takes 2.5 minutes, this is frustrating but not catastrophic. However, if they lose the diagnosis result AND the expert panel (which took background time to build), that is a significant loss.

**Recommended fix:**
1. Persist `pws_diagnostic_answers` and `pws_stage` to the Supabase-backed context store (not just `cl.user_session`). The existing `context_store` pattern in mindrian_chat.py handles this for conversation history; extend it for diagnostic state.
2. On `on_chat_resume`, check for persisted diagnostic state and restore it: show the DiagnosticFlow at the correct question, or show DiagnosisResult if the diagnostic was complete.
3. Add a brief "Welcome back -- I remember where we left off" message on resume.

---

### LOW

---

#### Finding 15: Framework Badges in DiagnosisResult Are Not Actionable

**Severity:** LOW
**Area:** Missing Affordances

**What happens:** The DiagnosisResult card shows framework badges like "Jobs to Be Done (JTBD)", "Process Mapping for Innovation", etc. These are rendered as `Badge` components with `variant="outline"`. They are not clickable.

**Why it is a problem:** Badges that look like tags invite clicking. Users familiar with tag-based interfaces (LinkedIn, Notion, Jira) will instinctively click a framework badge expecting it to do something -- show a description, filter experts by that framework, or start a framework-specific exercise. The non-response to a click creates a small moment of disappointment.

**Recommended fix:**
1. Make badges clickable. On click, show a tooltip or popover with a 1-sentence description of the framework and a "Use this framework" action that injects it into Larry's consulting context.
2. Alternatively, link each badge to the relevant PWS workshop bot. Clicking "Jobs to Be Done (JTBD)" could show: "This framework is covered in depth in the JTBD Workshop. Switch to JTBD Workshop?"

---

#### Finding 16: "Also shows characteristics of: Wicked Problem" Is Easily Missed

**Severity:** LOW
**Area:** Visual Hierarchy

**What happens:** The secondary problem type indicator at the bottom of DiagnosisResult uses `fontSize: 12, opacity: 0.6` with a `borderTop: "1px solid rgba(255,255,255,0.08)"` separator. It says "Also shows characteristics of: Wicked Problem."

**Why it is a problem:** For this simulation, the wicked secondary (18% score, multiple stakeholder groups with conflicting needs) is clinically important -- it explains why the user has three different groups telling her three different things. But the visual treatment makes it look like a footnote. Users who process the card top-to-bottom will absorb the primary type and may stop reading before the secondary indicator.

**Recommended fix:**
1. Increase opacity to 0.8 and add the secondary type's icon and color more prominently.
2. Move the secondary indicator up, directly below the primary type header, as a smaller companion badge: "Primary: Ill-Defined | Secondary: Wicked".
3. Add a brief explanation: "Wicked characteristics detected: multiple stakeholder groups with conflicting needs" (this text is available in the `secondary.note` prop but not rendered in the current component).

---

#### Finding 17: Larry's Between-Question Commentary Timing Is Unclear

**Severity:** LOW
**Area:** Timing & Pacing

**What happens:** After each diagnostic answer, Larry sends a brief commentary message (e.g., "Good -- knowing the area is more than most people start with."). The simulation shows these between Q1-Q2, Q2-Q3, etc. The timing relationship between the commentary message and the next diagnostic question card is not specified.

**Why it is a problem:** If the commentary appears simultaneously with the next question, the user may miss it. If it appears first with a delay before the next question, it slows down a flow that should feel brisk (the simulation targets 2.5 minutes for 5 questions). The ideal pacing is: answer click -> brief visual confirmation -> next question appears -> commentary fades in alongside or above the question.

**Recommended fix:**
1. Embed commentary inside the DiagnosticFlow card (see Finding 7) so the pacing is controlled by one component.
2. If keeping it as a separate message, add a 400ms delay after the commentary before showing the next question. This gives the user time to read Larry's comment without feeling like the flow has stalled.

---

## Summary Table

| # | Finding | Severity | Area | Planned Fix? |
|---|---------|----------|------|-------------|
| 1 | DiagnosisResult + ExpertPanel simultaneous reveal | CRITICAL | Cognitive Load, Sequencing | Partial (Task 6 bridge) |
| 2 | ExpertPanel 2-column grid breaks on 375px mobile | CRITICAL | Mobile UX | No |
| 3 | No back/undo in DiagnosticFlow | CRITICAL | Interaction Friction, Errors | No |
| 4 | No selection feedback on diagnostic buttons | CRITICAL | Missing Affordances, Diagnostic UX | No |
| 5 | Expert cards lack sufficient info for decision-making | HIGH | Expert Panel UX | No |
| 6 | No visual indicator of expert consultation mode | HIGH | Expert Panel UX, Visual Hierarchy | Partial (Task 10 badge) |
| 7 | Diagnostic feels like quiz, not conversation | HIGH | Diagnostic UX | No |
| 8 | No way to dismiss/minimize completed components | HIGH | Interaction Friction, Visual Hierarchy | No |
| 9 | Progress bar nearly invisible (2px) | MEDIUM | Visual Hierarchy | No |
| 10 | No loading state between diagnostic end and component reveal | MEDIUM | Timing & Pacing | Partial (ExpertPanel has loading prop) |
| 11 | Confidence/complexity scores lack context | MEDIUM | Cognitive Load | Partial (Task 6 bridge) |
| 12 | No confirmation before expert consultation starts | MEDIUM | Interaction Friction | No |
| 13 | Conversation starters do not map to structured process | MEDIUM | Component Sequencing | Partial (Task 3 ChallengeIntro) |
| 14 | No session recovery for diagnostic interruption | MEDIUM | Error States | No |
| 15 | Framework badges are not actionable | LOW | Missing Affordances | No |
| 16 | Secondary problem type indicator easily missed | LOW | Visual Hierarchy | No |
| 17 | Larry's between-question commentary timing unclear | LOW | Timing & Pacing | No |

---

## What Is Working Well

These aspects of the design deserve recognition -- they represent strong UX decisions that should be preserved and built upon.

### 1. Larry's Conversational Voice Is Outstanding

The intro phase (Turns 1-2) demonstrates exceptional conversational design. Larry mirrors the user's language ("not opposed, but not engaged either"), validates emotional moments ("that takes courage"), and probes with genuine curiosity rather than formulaic follow-ups. The JTBD breakthrough at Turn 9 ("Yes. That makes complete sense -- and I want you to hear what you just said") is a masterclass in coaching-through-conversation. This voice should be the benchmark for all Mindrian bots.

### 2. The Three-Stage State Machine Is Architecturally Correct

The decision to use a deterministic stage machine (intro -> diagnostic -> consulting) instead of loose workshop phases is exactly right. The Final Plan's LangGraph analysis validates this: each stage has a fundamentally different interaction pattern. The architecture matches the UX intent.

### 3. Background Pipeline Timing Is Well-Designed

Launching `build_expert_panel()` and `discover_domain_and_subdomains()` during the intro phase -- so they complete during the diagnostic -- is smart async design. The user never waits for these operations because they happen while the user is engaged with the MCQ flow. The ExpertPanel's `loading` state with the pulsing dot provides a graceful fallback if the pipeline runs long.

### 4. The Camera Test as a UX Device

Using the Camera Test not just as a framework but as a literal UX prompt ("What would a camera literally see?") is brilliant. It transforms an abstract methodology into a concrete, visual exercise. Sarah's response (Turn 13) -- describing the elderly woman, the messaging app, the warm colors, the 30-second response -- is exactly the kind of vivid output this technique should produce.

### 5. Expert Panel Domain Grounding

Building experts from discovered subdomains (Telemedicine, Rural Health, Patient Engagement, Clinic Operations) rather than generic archetypes makes the panel feel relevant and earned. The End-User Advocate's Turn 11 response -- splitting "patients" into two distinct jobs with two distinct competitors -- demonstrates the value of domain-specific expert construction.

### 6. Problem Evolution Tracking

The simulation's documentation of problem evolution from "Improve healthcare access in rural communities" (un-testable) to "Triage confidence for elderly worried-well patients" (testable, specific) is itself a UX artifact. If this evolution could be surfaced to the user as a visual progression (perhaps a collapsible timeline), it would powerfully demonstrate the value of the consulting session.

### 7. DiagnosticFlow Component Simplicity

Despite the critique above about missing states, the DiagnosticFlow component is admirably simple: one card, one question, four buttons, a progress bar. It avoids overengineering. The improvements needed (back button, selection feedback, animation) are additive, not structural. The core interaction pattern is sound.

### 8. Simulation Quality as a Design Artifact

The simulation document itself is an exemplary UX specification. It includes timestamps, behind-the-scenes system actions, reasoning traces, signal detection, and gap annotations. This level of detail makes it possible to review the experience without building it first -- which is exactly what good UX documentation should enable.

---

## Recommendations Priority Map

For implementation planning, the findings map to the existing task structure as follows:

| Finding | Suggested Task Alignment | Effort |
|---------|-------------------------|--------|
| 1 (simultaneous reveal) | Extend Task 6 (bridge message) with staggered UI | Medium |
| 2 (mobile grid) | New task or extend ExpertPanel.jsx in Task 9 | Low |
| 3 (diagnostic back button) | New task: DiagnosticFlow v2 | Medium |
| 4 (selection feedback) | Same task as Finding 3 | Low |
| 5 (expert card info) | Extend ExpertPanel.jsx in Task 9 | Low |
| 6 (expert mode indicator) | Extend Task 10 (ConsultantBadge) or new ExpertModeBanner | Medium |
| 7 (quiz vs conversation) | New task: DiagnosticFlow voice pass | Low-Medium |
| 8 (dismiss/minimize) | New task: component lifecycle management | Medium |
| 9 (progress bar) | Include in Finding 3/4 task | Low |
| 10 (loading state) | Extend Task 1 (_complete_pws_diagnosis) | Low |
| 11 (confidence context) | Include in Task 6 (bridge message) | Low |
| 12 (expert confirmation) | Include in Finding 5 task | Low |
| 13 (starters mapping) | Extend Task 3 (ChallengeIntro) | Low |
| 14 (session recovery) | New task: PWS state persistence | Medium |
| 15 (framework badges) | Future enhancement | Low |
| 16 (secondary type) | Include in Task 5 (reclassify) DiagnosisResult update | Low |
| 17 (commentary timing) | Include in Finding 7 task | Low |

---

*Review generated: 2026-02-05. Based on simulation sim-pws-consul-001, component source code, Final Plan architecture, and Chainlit feature constraints.*
