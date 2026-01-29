# Custom JSX Elements & AskElementMessage Forms

## What Is This?

Custom JSX elements and form-based user input using Chainlit's `CustomElement` and `AskElementMessage` APIs. These provide rich, interactive UI components beyond standard chat messages.

## Status: **DONE** (2026-01-29)

## Why Implement This?

### Problems Solved

1. **Static Progress Display**: Workshop progress was just text checkmarks
2. **Non-Interactive Visualizations**: DIKW pyramid was a static Plotly chart
3. **Unstructured Input**: Users had to describe problems in free text
4. **No Form Validation**: No way to ensure required fields were provided

### Benefits

- Interactive, clickable UI components
- Form validation before submission
- Structured data capture for better AI context
- Visual feedback (progress bars, status indicators)

## Implementation

### Custom Elements Created

| Element | Location | Purpose |
|---------|----------|---------|
| `PhaseProgress.jsx` | `public/elements/` | Interactive workshop progress with phase navigation |
| `DIKWPyramid.jsx` | `public/elements/` | Clickable Ackoff's pyramid levels |
| `ResearchMatrix.jsx` | `public/elements/` | Research results by category |
| `ScenarioSetupForm.jsx` | `public/elements/` | Scenario Analysis structured setup |
| `ProblemDefinitionForm.jsx` | `public/elements/` | PWS problem definition with Camera Test |

### Python Callbacks

| Callback | Location | Purpose |
|----------|----------|---------|
| `explore_dikw_level` | `mindrian_chat.py:3609` | Handle DIKW level click |
| `form_submit` | `mindrian_chat.py:2754` | Generic form submission handler |
| `show_problem_form` | `mindrian_chat.py:2876` | Display problem definition form |
| `show_scenario_form` | `mindrian_chat.py:2896` | Display scenario setup form |

### Helper Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `show_phase_progress_element()` | `mindrian_chat.py:863` | Display PhaseProgress element |
| `show_dikw_pyramid_element()` | `mindrian_chat.py:895` | Display DIKWPyramid element |
| `show_research_matrix_element()` | `mindrian_chat.py:916` | Display ResearchMatrix element |
| `setup_workshop_sidebar()` | `mindrian_chat.py:941` | Initialize ElementSidebar |
| `update_sidebar_phase()` | `mindrian_chat.py:1004` | Update sidebar on phase change |

## Usage Examples

### Display Interactive Progress

```python
# In action callback or message handler
await show_phase_progress_element()
```

### Show DIKW Pyramid with Highlight

```python
await show_dikw_pyramid_element(
    highlight_level="knowledge",
    scores={"data": 8, "information": 6, "knowledge": 4, "wisdom": 2}
)
```

### Display Form for Structured Input

```python
# Show problem definition form
element = cl.CustomElement(
    name="ProblemDefinitionForm",
    props={"showCameraTest": True, "initialValues": {}}
)
await cl.Message(content="Define your problem:", elements=[element]).send()

# Form data comes back via form_submit callback
```

### Handle Form Submission

```python
@cl.action_callback("form_submit")
async def on_form_submit(action: cl.Action):
    form_type = action.payload.get("formType")
    form_data = action.payload.get("data")

    if form_type == "problem_definition":
        # Process structured problem data
        problem = form_data.get("problemStatement")
        who = form_data.get("whoExperiences")
        # ... use in conversation context
```

## Custom Element Structure

All JSX elements follow this pattern:

```jsx
export default function MyElement() {
    // Access props passed from Python
    const { prop1, prop2 } = props;

    // Call Python callbacks
    const handleClick = () => {
        callAction({
            name: 'my_callback',
            payload: { key: 'value' }
        });
    };

    return (
        <Card>
            {/* Shadcn UI components */}
        </Card>
    );
}
```

### Available Shadcn Components

- `Button`, `Input`, `Textarea`, `Label`
- `Card`, `CardHeader`, `CardContent`, `CardTitle`, `CardDescription`
- `Select`, `SelectContent`, `SelectItem`, `SelectTrigger`, `SelectValue`
- `Progress`, `Badge`
- Lucide icons (imported individually)

## ElementSidebar Integration

The sidebar shows reference materials and phase checklist:

```python
# Called in on_chat_start for workshop bots
await setup_workshop_sidebar(bot_id)

# Called when phases advance
await update_sidebar_phase(current_phase_idx)
```

Sidebar contents:
- Methodology quick reference (TTA, JTBD, DIKW, etc.)
- Phase checklist with ✅/🔵 indicators
- Uploaded documents (PDF, files)

## Files Modified

| File | Changes |
|------|---------|
| `mindrian_chat.py` | Added callbacks, helpers, sidebar integration |
| `public/elements/*.jsx` | NEW - 5 custom elements |

## Testing

1. **PhaseProgress**: Click "Show Progress" in any workshop bot
2. **DIKWPyramid**: Click "Show DIKW Pyramid" in Ackoff bot
3. **Forms**: Call `show_problem_form` or `show_scenario_form` actions
4. **Sidebar**: Start any workshop bot, check sidebar appears

## Future Enhancements

- [ ] More form types (JTBD setup, S-Curve analysis)
- [ ] Form state persistence across sessions
- [ ] Conditional form fields based on selections
- [ ] Form analytics (completion rates, drop-off points)

---

*Implemented: 2026-01-29*
*Commit: f8f3909*
