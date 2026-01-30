---
name: chainlit-components
category: frontend-development
description: Generate custom React JSX components for Chainlit applications using shadcn/ui + Tailwind CSS. Creates interactive UI elements that integrate with Chainlit's Python backend via global props and action APIs.
triggers:
  - "chainlit component"
  - "chainlit custom element"
  - "chainlit jsx"
  - "chainlit ui"
  - "chainlit card"
  - "chainlit form"
  - "chainlit interactive"
  - "create component"
  - "new element"
---

# Chainlit Components Builder Skill

Generate production-ready React JSX components for Chainlit's custom elements system.

## Quick Start

```bash
# Generate new component
python scripts/create_component.py ComponentName
python scripts/create_component.py ComponentName --template card
```

## Overview

Chainlit allows custom React components rendered inline in chat messages:
- Use **shadcn/ui + Tailwind CSS** for styling
- Receive **props globally** (not as function arguments)
- **Interact with backend** via special APIs
- Placed in `public/elements/` directory

---

## Critical Rules (MUST FOLLOW)

### 1. JSX Only - No TypeScript
```jsx
// ✅ CORRECT - .jsx file
export default function MyComponent() { ... }

// ❌ WRONG - No .tsx
export default function MyComponent(): JSX.Element { ... }
```

### 2. Props Are Global
```jsx
// ✅ CORRECT
export default function MyComponent() {
  const { name, count } = props || {};
  return <div>{name}: {count}</div>;
}

// ❌ WRONG - Props as argument
export default function MyComponent({ name, count }) {
  return <div>{name}: {count}</div>;
}
```

### 3. Default Export Required
```jsx
// ✅ CORRECT
export default function ComponentName() { ... }

// ❌ WRONG
export function ComponentName() { ... }
export const ComponentName = () => { ... }
```

### 4. Always Check APIs Exist
```jsx
const { updateElement, callAction } = window.Chainlit || {}

const handleClick = () => {
  if (callAction) {
    callAction({ name: "action", payload: {} })
  }
}
```

---

## Component Template

```jsx
/**
 * ComponentName - Description
 *
 * Props (injected globally by Chainlit):
 * - prop1: type (description)
 */

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function ComponentName() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage, deleteElement } = window.Chainlit || {}

  // Props with defaults
  const { title = "Default", element_id = null } = props || {}

  // === HANDLERS ===
  const handleAction = () => {
    if (callAction) {
      callAction({ name: "component_action", payload: { title } })
    }
  }

  // === RENDER ===
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={handleAction}>Action</Button>
      </CardContent>
    </Card>
  )
}
```

---

## Global Chainlit APIs

| API | Description | Usage |
|-----|-------------|-------|
| `props` | All properties from Python | `const { title } = props \|\| {}` |
| `updateElement(nextProps)` | Update component props | `updateElement({ ...props, count: 1 })` |
| `deleteElement()` | Remove element | `onClick={deleteElement}` |
| `callAction(action)` | Call Python handler | `callAction({ name: "x", payload: {} })` |
| `sendUserMessage(msg)` | Send as user | `sendUserMessage("Hello")` |

---

## Python Integration

### Send Element
```python
import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="ComponentName",  # Must match JSX filename!
            props={"title": "Hello", "data": {}},
            display="inline"  # or "side", "page"
        )
    ]
    await cl.Message(content="Result:", elements=elements).send()
```

### Handle Action
```python
@cl.action_callback("component_action")
async def handle_action(action: cl.Action):
    payload = action.payload
    await cl.Message(content=f"Received: {payload}").send()
```

---

## Available Imports

### shadcn/ui Components
```jsx
// Layout
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion"

// Forms
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"

// Feedback
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

// Overlays
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogAction, AlertDialogCancel } from "@/components/ui/alert-dialog"
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip"

// Data
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
```

### Icons (Lucide React)
```jsx
import {
  Check, X, Plus, Minus, Edit, Trash, Save,
  Search, Settings, Menu, Home, User,
  ChevronLeft, ChevronRight, ChevronUp, ChevronDown,
  ArrowRight, ArrowLeft, ExternalLink,
  AlertCircle, Info, HelpCircle,
  Star, Heart, ThumbsUp, ThumbsDown,
  Clock, Loader2, RefreshCw,
  MessageCircle, Send, Sparkles
} from "lucide-react"
```

### React Hooks
```jsx
import { useState, useEffect, useMemo, useCallback } from "react"
```

---

## Tailwind Quick Reference

### Spacing
```
p-4       padding: 1rem
px-4      padding-left/right
py-2      padding-top/bottom
space-y-4 vertical spacing
gap-4     flex/grid gap
```

### Flexbox
```
flex items-center justify-between
flex-col
flex-1
flex-shrink-0
```

### Colors (Theme-aware)
```
bg-background text-foreground      # main
bg-primary text-primary-foreground # brand
bg-muted text-muted-foreground     # subtle
bg-destructive                     # error
```

### Dark Mode
```
bg-green-50 dark:bg-green-950/30
text-green-600 dark:text-green-400
```

---

## Design Guidelines

### Avoid "AI Slop"
- ❌ Everything centered
- ❌ Purple gradients everywhere
- ❌ Same rounded corners on all
- ✅ Left-align where appropriate
- ✅ Purposeful color choices
- ✅ Varied styling by context

### Best Practices
- Always `props || {}` fallback
- Check APIs before calling
- Use semantic colors not hardcoded
- Support dark mode with `dark:` variants
- Add loading states for async
- Include error handling

---

## Existing Templates

| Template | Location | Use For |
|----------|----------|---------|
| BasicCard | `templates/BasicCard.jsx` | Cards with actions |
| FormCard | `templates/FormCard.jsx` | Forms with validation |
| DataTable | `templates/DataTable.jsx` | Sortable tables |
| StatusTracker | `templates/StatusTracker.jsx` | Progress steps |

## Existing Mindrian Components

| Component | Purpose |
|-----------|---------|
| GradeReveal | Soft-landing grade reveal |
| ScoreBreakdown | Interactive score drill-down |
| OpportunityCard | Bank of opportunities |

---

## Workflow

1. **Identify need** - What data? What interactions?
2. **Choose template** - `python scripts/create_component.py Name --template card`
3. **Customize JSX** - Edit `public/elements/Name.jsx`
4. **Wire Python** - Add `cl.CustomElement()` and action handlers
5. **Test** - Verify props flow and actions work

---

## See Also

- `docs/CHAINLIT_COMPONENTS.md` - Full documentation
- `public/elements/templates/` - Copy-paste templates
- `scripts/create_component.py` - Generator script
- [Chainlit Docs](https://docs.chainlit.io/api-reference/elements/custom)
- [shadcn/ui](https://ui.shadcn.com/docs/components)
- [Lucide Icons](https://lucide.dev/icons)
