# Chainlit Features Reference

This reference covers all Chainlit customization capabilities relevant to Mindrian development.

---

## Custom JSX Elements

Custom elements allow rendering React components within Chainlit messages.

### File Location

Place JSX files in `public/elements/ELEMENT_NAME.jsx`. The element name in Python must match the filename (without extension).

### Component Structure

```jsx
// public/elements/MyComponent.jsx
export default function MyComponent() {
    // props are globally injected - NEVER pass as function argument
    return <div>{props.title}</div>
}
```

### Python Usage

```python
import chainlit as cl

element = cl.CustomElement(name="MyComponent", props={"title": "Hello"})
await cl.Message(content="Here's the component", elements=[element]).send()

# Update props from Python
element.props["title"] = "Updated"
await element.update()
```

### Available APIs (Global in JSX)

| API | Purpose | Example |
|-----|---------|---------|
| `updateElement(nextProps)` | Update element props and re-render | `updateElement({...props, count: props.count + 1})` |
| `deleteElement()` | Remove element from UI | `onClick={deleteElement}` |
| `callAction({name, payload})` | Trigger Python `@cl.action_callback` | `callAction({name: "my_action", payload: {id: 1}})` |
| `sendUserMessage(message)` | Send message as user | `sendUserMessage("Hello from component")` |

### Allowed Imports

**React & State**: `react`, `recoil`, `react-hook-form`, `zod`

**UI Components** (shadcn): `@/components/ui/button`, `@/components/ui/card`, `@/components/ui/dialog`, `@/components/ui/dropdown-menu`, `@/components/ui/input`, `@/components/ui/progress`, `@/components/ui/select`, `@/components/ui/table`, `@/components/ui/tooltip`, and more

**Icons**: `lucide-react`

**Notifications**: `sonner`

### Styling

Uses Tailwind CSS with shadcn theme variables:

```jsx
<div className="bg-primary text-primary-foreground rounded-md p-4">
    <span className="text-muted-foreground">Styled content</span>
</div>
```

---

## TaskList (Sidebar)

TaskList displays a persistent task panel next to the chat UI.

### Basic Usage

```python
import chainlit as cl

task_list = cl.TaskList()
task_list.status = "Running..."
task_list.name = "Workshop Progress"

task1 = cl.Task(title="Phase 1: Introduction", status=cl.TaskStatus.DONE)
task2 = cl.Task(title="Phase 2: Analysis", status=cl.TaskStatus.RUNNING)
task3 = cl.Task(title="Phase 3: Synthesis", status=cl.TaskStatus.READY)

await task_list.add_task(task1)
await task_list.add_task(task2)
await task_list.add_task(task3)

await task_list.send()
```

### Task Statuses

| Status | Visual | Use Case |
|--------|--------|----------|
| `cl.TaskStatus.READY` | Gray/pending | Future tasks |
| `cl.TaskStatus.RUNNING` | Blue/spinning | Current task |
| `cl.TaskStatus.DONE` | Green/check | Completed tasks |
| `cl.TaskStatus.FAILED` | Red/X | Failed tasks |

### Linking Tasks to Messages

```python
message = await cl.Message(content="Starting phase 1").send()
task1.forId = message.id  # Clicking task navigates to this message
await task_list.send()
```

### Safe Send Pattern (Mindrian)

```python
async def safe_task_list_send(task_list):
    """Handle Chainlit version compatibility issues."""
    try:
        await task_list.send()
    except TypeError as e:
        if "for_id" in str(e):
            pass  # Chainlit version compatibility
        else:
            raise
```

---

## React Client (@chainlit/react-client)

Build a completely custom frontend while using Chainlit backend.

### Installation

```bash
npm install @chainlit/react-client
```

### Key Hooks

| Hook | Purpose |
|------|---------|
| `useChatSession` | Manage chat session state |
| `useChatMessages` | Access message history |
| `useChatInteract` | Send messages and actions |
| `useAuth` | Handle authentication |

### Example Setup

```tsx
import { ChainlitAPI, ChainlitContext } from '@chainlit/react-client';

const apiClient = new ChainlitAPI('http://localhost:8000');

function App() {
    return (
        <ChainlitContext.Provider value={apiClient}>
            <YourCustomChat />
        </ChainlitContext.Provider>
    );
}
```

---

## Copilot Widget

Embed Chainlit as a floating assistant widget.

### Embedding

```html
<script src="http://localhost:8000/copilot/index.js"></script>
<script>
    window.mountChainlitWidget({
        chainlitServer: "http://localhost:8000",
        theme: "dark",
        button: {
            imageUrl: "/custom-icon.png",
            className: "my-custom-button"
        }
    });
</script>
```

### Widget Configuration

| Option | Type | Description |
|--------|------|-------------|
| `chainlitServer` | string | Backend URL |
| `accessToken` | string | Auth token if enabled |
| `theme` | "light" \| "dark" | Widget theme |
| `button.containerId` | string | Mount button to specific element |
| `button.imageUrl` | string | Custom button icon |
| `customCssUrl` | string | Custom CSS file URL |
| `expanded` | boolean | Start expanded |
| `language` | string | UI language |

### Function Calling (Python → Widget)

```python
# Python
fn = cl.CopilotFunction(name="highlight_cell", args={"row": 1, "col": "A"})
result = await fn.acall()
```

```javascript
// JavaScript
window.addEventListener("chainlit-call-fn", (e) => {
    const { name, args, callback } = e.detail;
    if (name === "highlight_cell") {
        highlightCell(args.row, args.col);
        callback("Cell highlighted");
    }
});
```

### Send Message (Widget → Python)

```javascript
window.sendChainlitMessage({
    type: "system_message",
    output: "User selected cells A1:B5"
});
```

```python
@cl.on_message
async def on_message(msg: cl.Message):
    if msg.type == "system_message":
        # Handle system message from widget
        pass
```

---

## Window Messaging (iframe)

Communicate between Chainlit iframe and parent window.

### Python Handler

```python
@cl.on_window_message
async def handle_window_message(message):
    """Handle messages from parent window."""
    if message.get("type") == "context_update":
        # Update context based on parent window state
        pass
```

### Parent Window

```javascript
const iframe = document.getElementById('chainlit-iframe');
iframe.contentWindow.postMessage({
    type: "context_update",
    data: { currentPage: "dashboard" }
}, "*");
```

---

## Custom CSS

### Configuration

In `.chainlit/config.toml`:

```toml
[UI]
custom_css = "/public/custom.css"
```

### Example CSS

```css
/* public/custom.css */
:root {
    --primary: 220 90% 56%;
    --primary-foreground: 0 0% 100%;
}

.cl-message {
    border-radius: 12px;
}

.cl-task-list {
    background: var(--background);
}
```

---

## Actions

Interactive buttons attached to messages.

### Creating Actions

```python
actions = [
    cl.Action(
        name="next_phase",
        payload={"phase": 2},
        label="→ Next Phase",
        tooltip="Move to the next workshop phase"
    ),
    cl.Action(
        name="show_example",
        payload={},
        label="📖 Example"
    )
]

await cl.Message(content="Ready to proceed?", actions=actions).send()
```

### Handling Actions

```python
@cl.action_callback("next_phase")
async def on_next_phase(action: cl.Action):
    phase = action.payload.get("phase")
    # Handle phase transition
    await cl.Message(content=f"Moving to phase {phase}").send()
```

---

## Chat Profiles

Different bot personalities/modes.

```python
@cl.set_chat_profiles
async def chat_profiles():
    return [
        cl.ChatProfile(
            name="Lawrence",
            markdown_description="Conversational PWS guide",
            icon="/avatars/lawrence.png"
        ),
        cl.ChatProfile(
            name="Red Team",
            markdown_description="Challenge your assumptions",
            icon="/avatars/redteam.png"
        )
    ]

@cl.on_chat_start
async def start():
    profile = cl.user_session.get("chat_profile")
    # Configure bot based on profile
```

---

## Steps (Thinking/Tool Display)

Show intermediate processing steps.

```python
async with cl.Step(name="Researching", type="tool") as step:
    step.input = "Searching for relevant information..."
    result = await do_research()
    step.output = f"Found {len(result)} results"
```

### Step Types

| Type | Display |
|------|---------|
| `"tool"` | Tool icon, collapsible |
| `"llm"` | AI icon |
| `"run"` | Generic step |

### Hide Input (Mindrian Pattern)

```python
async with cl.Step(name="Processing", show_input=False) as step:
    # Input won't be shown to user
    result = await process()
```

---

## Experimental Features

### Recoil State (in Custom Elements)

```jsx
import { useRecoilValue } from 'recoil';
import { callFnState } from '@chainlit/react-client';

export default function MyComponent() {
    const callFn = useRecoilValue(callFnState);
    
    useEffect(() => {
        if (callFn?.name === "my_function") {
            // Handle function call from Python
            callFn.callback("result");
        }
    }, [callFn]);
    
    return null;
}
```

### Thread Persistence (Copilot)

```javascript
// Get current thread ID
const threadId = window.getChainlitCopilotThreadId();

// Clear and optionally set new thread
window.clearChainlitCopilotThreadId(newThreadId);
```
