# UI Elements Release Documentation

**Date:** 2026-01-30
**Branch:** `claude/review-codebase-nRTQ3`
**Commit:** `b2a9f9f`

---

## Summary

Added custom UI elements and helper modules for enhanced grading and opportunity tracking experiences.

---

## New Files

### Custom JSX Elements (`public/elements/`)

| File | Purpose | Key Features |
|------|---------|--------------|
| `GradeReveal.jsx` | Soft-landing grade reveal | 5 stages: context → strengths → growth → reveal → expanded |
| `ScoreBreakdown.jsx` | Interactive drill-down | Click components to see evidence + improvement suggestions |
| `OpportunityCard.jsx` | Bank of Opportunities card | Explore/delete with AlertDialog confirmation |

### Helper Module (`utils/ui_elements.py`)

Python helpers for creating UI elements:

```python
from utils.ui_elements import (
    create_assessment_tasklist,   # TaskList for assessment progress
    update_task_status,           # Update task status in TaskList
    create_grade_reveal,          # GradeReveal custom element
    create_score_breakdown,       # ScoreBreakdown custom element
    create_opportunity_card,      # OpportunityCard custom element
    create_report_download,       # File download element
    create_evidence_display,      # JSON evidence viewer
    display_grading_results,      # Composite helper for full grading
    display_opportunities,        # Display opportunity bank
)
```

---

## GradeReveal.jsx

**Emotional Design Pattern:** Prevents "grade shock" by revealing information progressively.

### Stages

| Stage | What User Sees | CTA |
|-------|---------------|-----|
| `context` | Evidence count, preparation | "What did I do well?" |
| `strengths` | Green checklist of positives | "Where can I improve?" |
| `growth` | Amber improvement areas | "Show my grade" |
| `reveal` | Grade circle + score | "See Details" / "Discuss" |
| `expanded` | Full component breakdown | "View Evidence" / "Discuss" |

### Props

```javascript
{
  stage: 'context',           // Current stage
  grade: 'B+',                // Letter grade
  score: 78,                  // Numeric score 0-100
  verdict: 'Found validated problems',
  strengths: ['...', '...'], // What they did well
  growth_areas: ['...'],     // Where to improve
  evidence_count: 12,        // Evidence items analyzed
  components: [...],         // Score breakdown for expanded
  bot_type: 'minto'          // Which grader
}
```

### Actions Emitted

- `discuss_grade` - Triggers Lawrence discussion about the grade

---

## ScoreBreakdown.jsx

**Interactive Drill-Down:** Click any component to see detailed evidence and what's missing.

### Layout

- **Left (1/3):** Component list with score rings
- **Right (2/3):** Detail panel for selected component

### Component Data Structure

```javascript
{
  name: 'Problem Reality',
  weight: 35,                    // Percentage weight
  score: 7,                      // Score out of 10
  assessment: 'Text assessment',
  evidence: ['...', '...'],      // Found evidence
  missing: ['...', '...']        // What would raise score
}
```

### Actions Emitted

- `discuss_component` - Discuss specific component with Lawrence

---

## OpportunityCard.jsx

**Bank of Opportunities:** Track discovered opportunities for future exploration.

### Features

- Priority-based left border (red/yellow/green)
- Evidence quality stars (1-5)
- Framework tags
- Timestamp display
- Explore button → sends message to explore deeper
- Delete button → AlertDialog confirmation

### Props

```javascript
{
  id: 'opp-123',
  title: 'Healthcare AI Gap',
  problem: 'Patients struggle with...',
  evidence_quality: 4,           // 1-5 stars
  domain: 'Healthcare',
  priority: 'high',              // high/medium/low
  source: 'TTA Workshop',
  frameworks: ['JTBD', 'TTA'],
  created_at: '2026-01-30T...'
}
```

### Actions Emitted

- `remove_opportunity` - Remove from bank

---

## Integration Points

### Modified Files

- `mindrian_chat.py` - Added UI Elements import block with feature flag
- Fixed pre-existing indentation bugs in `on_next_phase` function

### Feature Flag

```python
UI_ELEMENTS_ENABLED = True  # Set False if import fails
```

### New Action Callbacks (to be wired)

```python
@cl.action_callback("view_full_report")
@cl.action_callback("view_evidence")
@cl.action_callback("discuss_component")
@cl.action_callback("remove_opportunity")
```

---

## Testing Checklist

- [ ] GradeReveal stages progress correctly (context → strengths → growth → reveal → expanded)
- [ ] GradeReveal "Discuss with Lawrence" triggers action
- [ ] ScoreBreakdown component selection works
- [ ] ScoreBreakdown detail panel shows evidence and missing items
- [ ] OpportunityCard priority colors display correctly
- [ ] OpportunityCard evidence stars render 1-5
- [ ] OpportunityCard delete confirmation dialog works
- [ ] TaskList displays assessment progress
- [ ] File download generates correct markdown

---

## Dependencies

- Chainlit 2.9+ (CustomElement support)
- Shadcn UI components (Button, Card, Badge, Progress, AlertDialog, Tooltip)
- Tailwind CSS
- Lucide React icons

---

## Next Steps

1. Wire action callbacks in `mindrian_chat.py`
2. Integrate with Minto grading agent
3. Add Bank of Opportunities persistence (Supabase)
4. Create assessment TaskList flow

---

*Last Updated: 2026-01-30*
