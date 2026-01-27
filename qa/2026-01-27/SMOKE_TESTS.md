# Smoke Tests — 2026-01-27

## Test 1: New User Journey (Lawrence default)

### Setup
- Fresh browser / incognito session
- Navigate to Mindrian

### Steps
1. App loads — confirm Larry is the default bot (first in dropdown, auto-selected)
2. See 4 conversation starters for Larry
3. Type: "We should build an Uber for plumbing"
4. **Expected (NEW):** Larry should gently redirect to problem definition instead of jumping into solution analysis. Look for questions like "What problem are you trying to solve?" or "Who is struggling with plumbing today?"
5. Confirm buttons appear at bottom of response
6. Confirm response streams normally (no delay from extraction)

### Pass Criteria
- [ ] Default bot is Larry
- [ ] 4 starters visible
- [ ] Response includes problem-definition redirect (coaching hint fired)
- [ ] No perceptible latency increase
- [ ] Buttons render correctly

---

## Test 2: Intelligence Layer — Assumption Detection

### Setup
- Active conversation with any bot

### Steps
1. Send message: "Assuming the market grows 20% annually, and if we suppose millennials prefer mobile-first..."
2. Send follow-up: "Given that our competition won't adapt, we can assume first-mover advantage..."
3. **Expected (NEW):** After message with 2+ assumptions:
   - Red Team agent suggestion should appear (extraction score boost +0.4)
   - Larry should probe which assumptions to validate (coaching hint)
4. **Expected (NEW):** After 3+ assumptions:
   - News Signal button may appear ("Multiple assumptions — news may validate or challenge them")

### Pass Criteria
- [ ] Red Team suggestion appears within first 2 agent suggestions
- [ ] Bot asks about validating assumptions
- [ ] News button appears with reason tooltip

---

## Test 3: Intelligence Layer — Evidence Detection

### Setup
- Active conversation

### Steps
1. Send: "This is definitely the right approach. Clearly AI will replace 80% of jobs."
2. **Expected (NEW):**
   - Academic Evidence (ArXiv) button appears ("Claims need evidence grounding")
   - Bot asks what evidence supports the confidence
3. Send: "By 2030, every company will need to be AI-first. The future is autonomous agents."
4. **Expected (NEW):**
   - Trends button appears ("Forward-looking discussion benefits from trend data")
   - TTA agent suggestion appears (+0.3 score boost)

### Pass Criteria
- [ ] ArXiv button appears on certainty without sources
- [ ] Trends button appears on forward-looking language
- [ ] TTA suggested for future-focused conversation
- [ ] Reason tooltips display correctly on buttons

---

## Test 4: Research Tool Buttons Work

### Setup
- Conversation where research buttons have appeared

### Steps
1. Click "Academic Evidence" button
2. **Expected:** ArXiv search executes, returns formatted papers with links
3. Click "Trends" button
4. **Expected:** Google Trends data displayed
5. Click "Gov Data" button
6. **Expected:** Government statistics returned
7. Click "News Signal" button
8. **Expected:** Current news articles returned

### Pass Criteria
- [ ] Each button executes without error
- [ ] Results show "Why: [reason]" header
- [ ] Results include clickable links
- [ ] Results appended to conversation history

---

## Test 5: Background Intelligence (5+ turns)

### Setup
- Have a 5+ turn conversation

### Steps
1. Continue chatting for 5+ turns
2. Check server logs for "Background intelligence" messages
3. Check Supabase Storage `extractions/` bucket for new `conversation_intelligence_*.json` files
4. After background runs, send a message with weak data grounding
5. **Expected (NEW):** Gov Data and Dataset buttons may appear ("Low data grounding")

### Pass Criteria
- [ ] No visible change to user during background processing
- [ ] Supabase entries created
- [ ] Coherence-driven research suggestions activate after background run

---

## Test 6: Graph Intelligence (Neo4j)

### Setup
- Neo4j is running and accessible

### Steps
1. Type: "I want to analyze this using S-Curve methodology"
2. **Expected:** Research tools appear with graph-driven reasons (e.g., "Framework 'S-Curve' uses patent analysis")
3. Type something mentioning a framework name
4. **Expected:** GraphRAG enrichment fires + extraction signals both contribute to response

### Pass Criteria
- [ ] Graph-driven research buttons show framework-specific reasons
- [ ] Both GraphRAG and extraction hints work together (not conflicting)
- [ ] If Neo4j is down: graceful degradation, extraction-only suggestions still work

---

## Test 7: Failure Recovery / Graceful Degradation

### Setup
- Simulate failures

### Steps
1. If `tools/langextract.py` import fails → app should work exactly as before (all extraction wrapped in try/except)
2. If Neo4j is unreachable → graph scoring returns empty, keyword + extraction scoring still works
3. If Supabase is down → background caching silently fails, everything else works

### Pass Criteria
- [ ] App never crashes from extraction failures
- [ ] No error messages shown to user
- [ ] Features degrade gracefully (less intelligence, not broken)

---

## Test 8: Existing Features — No Regression

### Steps
1. Click "Extract Insights" button → still works as before
2. Click "Synthesize" → produces summary
3. Click "Deep Research" → executes search
4. Switch bots via dropdown → context preserved
5. Switch bots via suggestion button → context preserved
6. Upload a PDF → text extracted, no crash

### Pass Criteria
- [ ] All existing buttons functional
- [ ] Bot switching preserves context
- [ ] File upload works
- [ ] No new error messages in console
