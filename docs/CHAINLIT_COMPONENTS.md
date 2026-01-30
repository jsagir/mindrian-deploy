# Chainlit Custom Components Guide

> **Quick Start:** Use `python scripts/create_component.py ComponentName` to generate a new component with boilerplate.

## Overview

Chainlit allows custom React components to be rendered inline in chat messages. These components:
- Use **shadcn/ui + Tailwind CSS** for styling
- Receive **props globally** (not as function arguments)
- Can **interact with the backend** via special APIs
- Are placed in `public/elements/` directory

---

## File Structure

```
mindrian-deploy/
├── public/
│   └── elements/
│       ├── GradeReveal.jsx       # Existing components
│       ├── ScoreBreakdown.jsx
│       ├── OpportunityCard.jsx
│       └── templates/            # Copy-paste templates
│           ├── BasicCard.jsx
│           ├── FormCard.jsx
│           ├── DataTable.jsx
│           └── StatusTracker.jsx
├── scripts/
│   └── create_component.py       # Component generator
└── docs/
    └── CHAINLIT_COMPONENTS.md    # This file
```

---

## Critical Rules

### 1. JSX Only (No TypeScript)
```jsx
// ✅ CORRECT - .jsx file
export default function MyComponent() { ... }

// ❌ WRONG - No .tsx files
export default function MyComponent(): JSX.Element { ... }
```

### 2. Props Are Global
```jsx
// ✅ CORRECT - Access props globally
export default function MyComponent() {
  const { name, count } = props || {};
  return <div>{name}: {count}</div>;
}

// ❌ WRONG - Props as function argument
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

---

## Global Chainlit APIs

These are injected globally in your components:

### `props`
Object containing all properties passed from Python:
```jsx
const { title, data, count } = props || {};
```

### `updateElement(nextProps)`
Update the component's props (triggers re-render):
```jsx
const handleIncrement = () => {
  updateElement({ ...props, count: props.count + 1 });
};
```

### `deleteElement()`
Remove the element from the message:
```jsx
<Button onClick={deleteElement}>Remove</Button>
```

### `callAction(action)`
Call a Python action handler:
```jsx
<Button onClick={() => callAction({
  name: "submit_form",
  payload: { formData: props.data }
})}>
  Submit
</Button>
```

### `sendUserMessage(message)`
Send a message as the user:
```jsx
<Button onClick={() => sendUserMessage("Show me more details")}>
  Get Details
</Button>
```

---

## Component Template

```jsx
/**
 * ComponentName - Description of what this component does
 *
 * Props (injected globally by Chainlit):
 * - prop1: type (description)
 * - prop2: type (description)
 */

import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { IconName } from "lucide-react"

export default function ComponentName() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage, deleteElement } = window.Chainlit || {}

  // Destructure props with defaults
  const {
    prop1 = "default",
    prop2 = 0,
    element_id = null
  } = props || {}

  // === HANDLERS ===
  const handleAction = () => {
    if (callAction) {
      callAction({ name: "action_name", payload: { prop1, prop2 } })
    }
  }

  const handleUpdate = (newValue) => {
    if (updateElement) {
      updateElement({ ...props, prop2: newValue })
    }
  }

  // === RENDER ===
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{prop1}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>Value: {prop2}</p>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button onClick={handleAction}>Action</Button>
        <Button variant="outline" onClick={() => handleUpdate(prop2 + 1)}>
          Increment
        </Button>
      </CardFooter>
    </Card>
  )
}
```

---

## Python Integration

### Sending a Custom Element
```python
import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="ComponentName",  # Must match JSX filename!
            props={
                "prop1": "Hello",
                "prop2": 42,
                "element_id": "unique-id-123"
            },
            display="inline"  # or "side", "page"
        )
    ]
    await cl.Message(
        content="Here's your component:",
        elements=elements
    ).send()
```

### Handling Actions
```python
@cl.action_callback("action_name")
async def handle_action(action: cl.Action):
    payload = action.payload
    prop1 = payload.get("prop1")
    prop2 = payload.get("prop2")

    await cl.Message(
        content=f"Action received: {prop1}, {prop2}"
    ).send()
```

---

## Available Imports

### shadcn/ui Components
```jsx
// Layout
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

// Forms
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"

// Feedback
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"

// Overlays
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogAction, AlertDialogCancel } from "@/components/ui/alert-dialog"
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover"
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip"
import { Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"

// Data Display
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"

// Navigation
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
```

### Icons (Lucide React)
```jsx
import {
  Check, X, Plus, Minus, Edit, Trash, Save,
  Search, Filter, Settings, Menu, Home,
  User, Users, Mail, Phone, Calendar,
  File, Folder, Download, Upload, Share,
  ChevronLeft, ChevronRight, ChevronUp, ChevronDown,
  ArrowLeft, ArrowRight, ArrowUp, ArrowDown,
  AlertCircle, AlertTriangle, Info, HelpCircle,
  Eye, EyeOff, Lock, Unlock, Key,
  Star, Heart, ThumbsUp, ThumbsDown,
  Clock, Timer, Loader2, RefreshCw,
  Copy, Clipboard, ExternalLink, Link,
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
px-4      padding-left/right: 1rem
py-2      padding-top/bottom: 0.5rem
m-4       margin: 1rem
space-y-4 vertical spacing between children
gap-4     gap in flex/grid
```

### Flexbox
```
flex              display: flex
flex-col          flex-direction: column
items-center      align-items: center
justify-between   justify-content: space-between
justify-center    justify-content: center
flex-1            flex: 1
flex-shrink-0     don't shrink
```

### Width/Height
```
w-full    width: 100%
w-1/2     width: 50%
max-w-md  max-width: 28rem
max-w-lg  max-width: 32rem
max-w-xl  max-width: 36rem
h-4       height: 1rem
h-full    height: 100%
```

### Colors (Theme-aware)
```
bg-background         main background
text-foreground       main text
bg-primary            primary brand
text-primary-foreground  text on primary
bg-muted              subtle background
text-muted-foreground subdued text
bg-destructive        error/danger
border                default border color
```

### Dark Mode
```
bg-green-50 dark:bg-green-950/30    light/dark backgrounds
text-green-600 dark:text-green-400  light/dark text
```

### States
```
hover:bg-muted        on hover
focus:ring-2          on focus
disabled:opacity-50   when disabled
transition-all        smooth transitions
```

---

## Design Guidelines

### Avoid "AI Slop"
- ❌ Excessive centered layouts
- ❌ Purple/violet gradients everywhere
- ❌ Uniform rounded corners on everything
- ✅ Left-aligned content where appropriate
- ✅ Purposeful color choices
- ✅ Varied styling based on context

### Best Practices
- Always provide fallback for `props || {}`
- Check if Chainlit APIs exist before calling
- Use semantic colors (`text-muted-foreground` not `text-gray-500`)
- Support dark mode with `dark:` variants
- Add loading states for async actions
- Include error handling

---

## Existing Mindrian Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `GradeReveal.jsx` | Soft-landing grade reveal | 5 stages, emotion-aware progression |
| `ScoreBreakdown.jsx` | Interactive score drill-down | Click components to see evidence |
| `OpportunityCard.jsx` | Bank of Opportunities | Priority colors, delete confirmation |

---

## See Also

- `public/elements/templates/` - Copy-paste templates
- `scripts/create_component.py` - Component generator
- [Chainlit Custom Elements Docs](https://docs.chainlit.io/api-reference/elements/custom)
- [shadcn/ui Components](https://ui.shadcn.com/docs/components)
- [Lucide Icons](https://lucide.dev/icons)

---

*Last Updated: 2026-01-30*
