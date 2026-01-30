/**
 * StatusTracker - Template for progress/status visualization
 *
 * Copy to: public/elements/YourTrackerName.jsx
 * Usage: cl.CustomElement(name="YourTrackerName", props={...})
 *
 * Props:
 * - title: string
 * - steps: array of {title, description?, timestamp?, status?}
 * - currentStep: number (0-indexed)
 * - orientation: 'vertical' | 'horizontal'
 */

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Check, Circle, Clock, AlertCircle, Loader2 } from "lucide-react"

export default function StatusTracker() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction } = window.Chainlit || {}

  // Props are global
  const {
    title = "Progress",
    steps = [],
    currentStep = 0,
    orientation = 'vertical',
    element_id = null
  } = props || {}

  // === HELPERS ===
  const getStepIcon = (index, step) => {
    if (step.status === 'error') {
      return <AlertCircle className="h-5 w-5 text-destructive" />
    }
    if (step.status === 'loading' || (index === currentStep && !step.status)) {
      return <Loader2 className="h-5 w-5 text-primary animate-spin" />
    }
    if (index < currentStep || step.status === 'completed') {
      return <Check className="h-5 w-5 text-green-600" />
    }
    if (index === currentStep) {
      return <Clock className="h-5 w-5 text-primary" />
    }
    return <Circle className="h-5 w-5 text-muted-foreground" />
  }

  const getStepState = (index, step) => {
    if (step.status === 'error') return 'error'
    if (index < currentStep || step.status === 'completed') return 'completed'
    if (index === currentStep) return 'current'
    return 'pending'
  }

  // === VERTICAL LAYOUT ===
  const VerticalTracker = () => (
    <div className="space-y-0">
      {steps.map((step, index) => {
        const state = getStepState(index, step)
        const isLast = index === steps.length - 1

        return (
          <div key={index} className="flex">
            {/* Icon Column */}
            <div className="flex flex-col items-center mr-4">
              <div className={`
                flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors
                ${state === 'completed' ? 'border-green-600 bg-green-50 dark:bg-green-950/30' : ''}
                ${state === 'current' ? 'border-primary bg-primary/10' : ''}
                ${state === 'pending' ? 'border-muted bg-muted/50' : ''}
                ${state === 'error' ? 'border-destructive bg-destructive/10' : ''}
              `}>
                {getStepIcon(index, step)}
              </div>
              {/* Connecting line */}
              {!isLast && (
                <div className={`w-0.5 h-12 transition-colors ${
                  index < currentStep ? 'bg-green-600' : 'bg-muted'
                }`} />
              )}
            </div>

            {/* Content Column */}
            <div className={`flex-1 ${!isLast ? 'pb-8' : ''}`}>
              <h4 className={`font-medium ${
                state === 'pending' ? 'text-muted-foreground' : 'text-foreground'
              }`}>
                {step.title}
              </h4>
              {step.description && (
                <p className="text-sm text-muted-foreground mt-1">
                  {step.description}
                </p>
              )}
              {step.timestamp && (
                <p className="text-xs text-muted-foreground mt-1">
                  {step.timestamp}
                </p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )

  // === HORIZONTAL LAYOUT ===
  const HorizontalTracker = () => (
    <div className="flex items-start">
      {steps.map((step, index) => {
        const state = getStepState(index, step)
        const isLast = index === steps.length - 1

        return (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div className="flex items-center w-full">
              {/* Line before */}
              {index > 0 && (
                <div className={`flex-1 h-0.5 ${
                  index <= currentStep ? 'bg-green-600' : 'bg-muted'
                }`} />
              )}

              {/* Icon */}
              <div className={`
                flex items-center justify-center w-8 h-8 rounded-full border-2 mx-2 transition-colors
                ${state === 'completed' ? 'border-green-600 bg-green-50 dark:bg-green-950/30' : ''}
                ${state === 'current' ? 'border-primary bg-primary/10' : ''}
                ${state === 'pending' ? 'border-muted bg-muted/50' : ''}
                ${state === 'error' ? 'border-destructive bg-destructive/10' : ''}
              `}>
                {getStepIcon(index, step)}
              </div>

              {/* Line after */}
              {!isLast && (
                <div className={`flex-1 h-0.5 ${
                  index < currentStep ? 'bg-green-600' : 'bg-muted'
                }`} />
              )}
            </div>

            {/* Label */}
            <div className="text-center mt-2 px-2">
              <p className={`text-sm font-medium ${
                state === 'pending' ? 'text-muted-foreground' : 'text-foreground'
              }`}>
                {step.title}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )

  // === RENDER ===
  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {orientation === 'horizontal' ? <HorizontalTracker /> : <VerticalTracker />}
      </CardContent>
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
            name="StatusTracker",
            props={
                "title": "Order Status",
                "currentStep": 2,
                "orientation": "vertical",
                "steps": [
                    {
                        "title": "Order Placed",
                        "description": "Your order has been received",
                        "timestamp": "Jan 28, 10:30 AM",
                        "status": "completed"
                    },
                    {
                        "title": "Processing",
                        "description": "We're preparing your order",
                        "timestamp": "Jan 28, 11:00 AM",
                        "status": "completed"
                    },
                    {
                        "title": "Shipped",
                        "description": "On its way to you",
                        "timestamp": "Jan 29, 2:00 PM"
                    },
                    {
                        "title": "Delivered",
                        "description": "Package delivered"
                    }
                ]
            },
            display="inline"
        )
    ]
    await cl.Message(content="Order status:", elements=elements).send()

# For horizontal layout:
# "orientation": "horizontal"

# For error state:
# {"title": "Payment", "status": "error", "description": "Payment failed"}

# For loading state:
# {"title": "Processing", "status": "loading"}

================================================================================
*/
