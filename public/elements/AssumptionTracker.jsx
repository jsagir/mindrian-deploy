/**
 * AssumptionTracker - Track and validate assumptions in PWS workshops
 *
 * Displays explicit and implicit assumptions with validation status,
 * risk levels, and actions to challenge or validate them.
 *
 * Props (injected globally by Chainlit):
 * - assumptions: array of {text, type, status, risk_level, evidence, source}
 * - title: optional header text
 * - show_risk: boolean to show risk indicators
 * - allow_actions: boolean to enable validation actions
 * - group_by: 'type' | 'status' | 'risk' | null
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Brain, AlertTriangle, CheckCircle2, XCircle, HelpCircle,
  FlaskConical, Eye, EyeOff, Shield, Target, ChevronRight,
  Sparkles, MessageSquare, RefreshCw, Filter
} from "lucide-react"
import { useState } from "react"

export default function AssumptionTracker() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    assumptions = [],
    title = "Assumption Tracker",
    show_risk = true,
    allow_actions = true,
    group_by = null,
    element_id = null
  } = props || {}

  // Local state
  const [activeTab, setActiveTab] = useState("all")
  const [expandedItems, setExpandedItems] = useState({})

  // === STATUS CONFIGURATION ===
  const statusConfig = {
    untested: {
      icon: <HelpCircle className="h-4 w-4" />,
      color: "text-gray-500",
      bgColor: "bg-gray-100 dark:bg-gray-800",
      label: "Untested"
    },
    testing: {
      icon: <FlaskConical className="h-4 w-4" />,
      color: "text-blue-500",
      bgColor: "bg-blue-100 dark:bg-blue-900/30",
      label: "Testing"
    },
    validated: {
      icon: <CheckCircle2 className="h-4 w-4" />,
      color: "text-green-500",
      bgColor: "bg-green-100 dark:bg-green-900/30",
      label: "Validated"
    },
    invalidated: {
      icon: <XCircle className="h-4 w-4" />,
      color: "text-red-500",
      bgColor: "bg-red-100 dark:bg-red-900/30",
      label: "Invalidated"
    }
  }

  // === TYPE CONFIGURATION ===
  const typeConfig = {
    explicit: {
      icon: <Eye className="h-4 w-4" />,
      label: "Explicit",
      description: "Stated directly in conversation"
    },
    implicit: {
      icon: <EyeOff className="h-4 w-4" />,
      label: "Implicit",
      description: "Hidden or unstated assumption"
    },
    critical: {
      icon: <Target className="h-4 w-4" />,
      label: "Critical",
      description: "Core assumption to the strategy"
    }
  }

  // === RISK CONFIGURATION ===
  const riskConfig = {
    high: {
      color: "text-red-500",
      bgColor: "bg-red-500",
      label: "High Risk"
    },
    medium: {
      color: "text-amber-500",
      bgColor: "bg-amber-500",
      label: "Medium Risk"
    },
    low: {
      color: "text-green-500",
      bgColor: "bg-green-500",
      label: "Low Risk"
    }
  }

  // === HANDLERS ===
  const handleStatusChange = (assumption, index, newStatus) => {
    if (callAction) {
      callAction({
        name: "update_assumption_status",
        payload: { assumption, index, newStatus }
      })
    }
    // Optimistic update
    if (updateElement) {
      const updated = [...assumptions]
      updated[index] = { ...updated[index], status: newStatus }
      updateElement({ ...props, assumptions: updated })
    }
  }

  const handleChallenge = (assumption, index) => {
    if (callAction) {
      callAction({
        name: "challenge_assumption",
        payload: { assumption, index }
      })
    } else if (sendUserMessage) {
      sendUserMessage(`Help me challenge this assumption: "${assumption.text}"`)
    }
  }

  const handleValidate = (assumption, index) => {
    if (callAction) {
      callAction({
        name: "validate_assumption",
        payload: { assumption, index }
      })
    } else if (sendUserMessage) {
      sendUserMessage(`How can I validate this assumption: "${assumption.text}"`)
    }
  }

  const toggleExpand = (index) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  // === FILTERING ===
  const filterAssumptions = () => {
    if (activeTab === "all") return assumptions
    if (activeTab === "untested") return assumptions.filter(a => a.status === "untested" || !a.status)
    if (activeTab === "risky") return assumptions.filter(a => a.risk_level === "high" || a.risk_level === "medium")
    if (activeTab === "validated") return assumptions.filter(a => a.status === "validated")
    return assumptions
  }

  // === STATS ===
  const stats = {
    total: assumptions.length,
    validated: assumptions.filter(a => a.status === "validated").length,
    invalidated: assumptions.filter(a => a.status === "invalidated").length,
    untested: assumptions.filter(a => a.status === "untested" || !a.status).length,
    highRisk: assumptions.filter(a => a.risk_level === "high").length
  }

  const validationProgress = stats.total > 0
    ? Math.round(((stats.validated + stats.invalidated) / stats.total) * 100)
    : 0

  // === RENDER SINGLE ASSUMPTION ===
  const renderAssumption = (assumption, index) => {
    const status = assumption.status || "untested"
    const type = assumption.type || "explicit"
    const risk = assumption.risk_level || "medium"
    const statusCfg = statusConfig[status] || statusConfig.untested
    const typeCfg = typeConfig[type] || typeConfig.explicit
    const riskCfg = riskConfig[risk] || riskConfig.medium
    const isExpanded = expandedItems[index]

    return (
      <div
        key={index}
        className={`p-4 rounded-lg border transition-all ${statusCfg.bgColor} border-border/50`}
      >
        <div className="flex items-start gap-3">
          {/* Status Icon */}
          <div className={`mt-0.5 ${statusCfg.color}`}>
            {statusCfg.icon}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Header Badges */}
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <Badge variant="outline" className="text-xs flex items-center gap-1">
                {typeCfg.icon}
                {typeCfg.label}
              </Badge>
              {show_risk && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Badge variant="outline" className={`text-xs ${riskCfg.color}`}>
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        {riskCfg.label}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Impact if assumption is wrong</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              <Badge variant="secondary" className="text-xs">
                {statusCfg.label}
              </Badge>
            </div>

            {/* Assumption Text */}
            <p className="text-sm text-foreground font-medium leading-relaxed">
              {assumption.text}
            </p>

            {/* Evidence (if any) */}
            {assumption.evidence && (
              <div className="mt-2 p-2 bg-muted/50 rounded text-xs">
                <span className="font-medium">Evidence: </span>
                <span className="text-muted-foreground">{assumption.evidence}</span>
              </div>
            )}

            {/* Source (expandable) */}
            {assumption.source && (
              <button
                onClick={() => toggleExpand(index)}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mt-2 transition-colors"
              >
                <MessageSquare className="h-3 w-3" />
                {isExpanded ? "Hide source" : "Show source"}
              </button>
            )}
            {isExpanded && assumption.source && (
              <div className="mt-2 p-2 bg-muted/30 rounded text-xs text-muted-foreground italic border-l-2 border-primary">
                "{assumption.source}"
              </div>
            )}

            {/* Actions */}
            {allow_actions && (
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                {status === "untested" && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs"
                      onClick={() => handleValidate(assumption, index)}
                    >
                      <FlaskConical className="h-3 w-3 mr-1" />
                      Test
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-xs"
                      onClick={() => handleChallenge(assumption, index)}
                    >
                      <Shield className="h-3 w-3 mr-1" />
                      Challenge
                    </Button>
                  </>
                )}
                {status === "testing" && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs text-green-600 hover:text-green-700"
                      onClick={() => handleStatusChange(assumption, index, "validated")}
                    >
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Mark Valid
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs text-red-600 hover:text-red-700"
                      onClick={() => handleStatusChange(assumption, index, "invalidated")}
                    >
                      <XCircle className="h-3 w-3 mr-1" />
                      Mark Invalid
                    </Button>
                  </>
                )}
                {(status === "validated" || status === "invalidated") && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs"
                    onClick={() => handleStatusChange(assumption, index, "untested")}
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Retest
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // === EMPTY STATE ===
  if (assumptions.length === 0) {
    return (
      <Card className="w-full max-w-lg">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No assumptions tracked yet.</p>
            <p className="text-xs mt-1">Assumptions will be extracted as you discuss your problem.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const filteredAssumptions = filterAssumptions()

  // === RENDER ===
  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Brain className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {stats.total} tracked
          </Badge>
        </div>
        <CardDescription>
          Track and validate your key assumptions
        </CardDescription>

        {/* Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Validation Progress</span>
            <span>{validationProgress}%</span>
          </div>
          <Progress value={validationProgress} className="h-2" />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span className="text-green-500">{stats.validated} validated</span>
            <span className="text-red-500">{stats.invalidated} invalidated</span>
            <span className="text-gray-500">{stats.untested} untested</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Filter Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full grid grid-cols-4 mb-4">
            <TabsTrigger value="all" className="text-xs">
              All ({stats.total})
            </TabsTrigger>
            <TabsTrigger value="untested" className="text-xs">
              Untested ({stats.untested})
            </TabsTrigger>
            <TabsTrigger value="risky" className="text-xs">
              Risky ({stats.highRisk})
            </TabsTrigger>
            <TabsTrigger value="validated" className="text-xs">
              Done ({stats.validated + stats.invalidated})
            </TabsTrigger>
          </TabsList>

          {/* Assumption List */}
          <div className="space-y-3">
            {filteredAssumptions.length === 0 ? (
              <div className="text-center py-4 text-muted-foreground text-sm">
                No assumptions in this category
              </div>
            ) : (
              filteredAssumptions.map((assumption, index) =>
                renderAssumption(assumption, assumptions.indexOf(assumption))
              )
            )}
          </div>
        </Tabs>
      </CardContent>

      {stats.highRisk > 0 && (
        <CardFooter>
          <div className="w-full p-3 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-800">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm font-medium">
                {stats.highRisk} high-risk assumption{stats.highRisk !== 1 ? 's' : ''} need{stats.highRisk === 1 ? 's' : ''} validation
              </span>
            </div>
          </div>
        </CardFooter>
      )}
    </Card>
  )
}

/*
================================================================================
PYTHON USAGE
================================================================================

import chainlit as cl
from utils.context_extraction import ConversationContext

# Initialize context tracker
context = ConversationContext()

@cl.on_message
async def main(message: cl.Message):
    # Process message for assumptions
    context.process_message(message.content, "user")

    # Get AI response...
    context.process_message(ai_response, "assistant")

    # Generate assumption tracker props
    assumption_props = context.to_props("AssumptionTracker")

    elements = [
        cl.CustomElement(
            name="AssumptionTracker",
            props=assumption_props,
            display="inline"
        )
    ]
    await cl.Message(content="Your assumptions:", elements=elements).send()

# Or with manual props:
elements = [
    cl.CustomElement(
        name="AssumptionTracker",
        props={
            "title": "Key Assumptions",
            "show_risk": True,
            "allow_actions": True,
            "assumptions": [
                {
                    "text": "Customers will pay $50/month for this solution",
                    "type": "critical",
                    "status": "untested",
                    "risk_level": "high",
                    "source": "We believe the value proposition justifies..."
                },
                {
                    "text": "Our technology is 10x faster than competitors",
                    "type": "explicit",
                    "status": "validated",
                    "risk_level": "medium",
                    "evidence": "Benchmark tests show 12x improvement"
                },
                {
                    "text": "The market will grow 20% annually",
                    "type": "implicit",
                    "status": "testing",
                    "risk_level": "medium"
                }
            ]
        },
        display="inline"
    )
]

@cl.action_callback("challenge_assumption")
async def handle_challenge(action: cl.Action):
    assumption = action.payload.get("assumption")
    await cl.Message(
        content=f"Let's challenge this assumption using Red Team thinking: '{assumption['text']}'"
    ).send()

@cl.action_callback("validate_assumption")
async def handle_validate(action: cl.Action):
    assumption = action.payload.get("assumption")
    await cl.Message(
        content=f"Here's how you could test this assumption: '{assumption['text']}'"
    ).send()

@cl.action_callback("update_assumption_status")
async def handle_status_update(action: cl.Action):
    # Update in database/session
    new_status = action.payload.get("newStatus")
    await cl.Message(content=f"Assumption marked as {new_status}").send()

================================================================================
*/
