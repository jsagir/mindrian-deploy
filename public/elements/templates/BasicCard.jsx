/**
 * BasicCard - Template for interactive cards with actions
 *
 * Copy to: public/elements/YourCardName.jsx
 * Usage: cl.CustomElement(name="YourCardName", props={...})
 *
 * Props:
 * - title: string
 * - description: string (optional)
 * - content: string (optional)
 * - status: string (optional) - displayed as badge
 * - actions: array of {label, name, payload, variant}
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function BasicCard() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage, deleteElement } = window.Chainlit || {}

  // Props are global - DO NOT pass as function argument
  const {
    title = "Card Title",
    description = "",
    content = "",
    status = null,
    actions = [],
    element_id = null
  } = props || {}

  // === HANDLERS ===
  const handleAction = (actionName, payload = {}) => {
    if (callAction) {
      callAction({ name: actionName, payload })
    }
  }

  // === RENDER ===
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          {status && <Badge variant="outline">{status}</Badge>}
        </div>
      </CardHeader>

      {content && (
        <CardContent>
          <p className="text-sm text-muted-foreground">{content}</p>
        </CardContent>
      )}

      {actions.length > 0 && (
        <CardFooter className="flex gap-2">
          {actions.map((action, index) => (
            <Button
              key={index}
              variant={action.variant || "default"}
              size="sm"
              onClick={() => handleAction(action.name, action.payload)}
            >
              {action.label}
            </Button>
          ))}
        </CardFooter>
      )}
    </Card>
  )
}

/*
================================================================================
PYTHON USAGE EXAMPLE
================================================================================

import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="BasicCard",  # Match the JSX filename
            props={
                "title": "Task Review",
                "description": "Please review and approve",
                "content": "This task requires your attention.",
                "status": "Pending",
                "actions": [
                    {"label": "Approve", "name": "approve_task", "payload": {"id": 123}},
                    {"label": "Reject", "name": "reject_task", "variant": "destructive", "payload": {"id": 123}}
                ]
            },
            display="inline"
        )
    ]
    await cl.Message(content="Here's a task:", elements=elements).send()

@cl.action_callback("approve_task")
async def handle_approve(action: cl.Action):
    task_id = action.payload.get("id")
    await cl.Message(content=f"Task {task_id} approved!").send()

@cl.action_callback("reject_task")
async def handle_reject(action: cl.Action):
    task_id = action.payload.get("id")
    await cl.Message(content=f"Task {task_id} rejected.").send()

================================================================================
*/
