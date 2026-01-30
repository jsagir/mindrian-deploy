/**
 * InsightCard - Display AI-extracted insights from conversation
 *
 * Shows insights with confidence levels, categories, and action buttons.
 * Integrates with context extraction for intelligent surfacing.
 *
 * Props (injected globally by Chainlit):
 * - insights: array of {text, category, confidence, source_message, timestamp}
 * - title: optional header text
 * - show_confidence: boolean to show confidence badges
 * - expandable: boolean to allow expanding cards
 * - max_display: number of insights to show initially
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import {
  Lightbulb, TrendingUp, AlertTriangle, Target, Users, Brain,
  ChevronDown, ChevronUp, MessageSquare, BookmarkPlus, Share2,
  Sparkles, Clock, CheckCircle2
} from "lucide-react"
import { useState } from "react"

export default function InsightCard() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    insights = [],
    title = "Key Insights",
    show_confidence = true,
    expandable = true,
    max_display = 3,
    element_id = null
  } = props || {}

  // Local state
  const [expandedCards, setExpandedCards] = useState({})
  const [showAll, setShowAll] = useState(false)
  const [savedInsights, setSavedInsights] = useState([])

  // === CATEGORY CONFIGURATION ===
  const categoryConfig = {
    opportunity: {
      icon: <TrendingUp className="h-4 w-4" />,
      color: "text-green-600 dark:text-green-400",
      bgColor: "bg-green-50 dark:bg-green-950/30",
      borderColor: "border-green-200 dark:border-green-800",
      label: "Opportunity"
    },
    risk: {
      icon: <AlertTriangle className="h-4 w-4" />,
      color: "text-amber-600 dark:text-amber-400",
      bgColor: "bg-amber-50 dark:bg-amber-950/30",
      borderColor: "border-amber-200 dark:border-amber-800",
      label: "Risk"
    },
    assumption: {
      icon: <Brain className="h-4 w-4" />,
      color: "text-purple-600 dark:text-purple-400",
      bgColor: "bg-purple-50 dark:bg-purple-950/30",
      borderColor: "border-purple-200 dark:border-purple-800",
      label: "Assumption"
    },
    customer: {
      icon: <Users className="h-4 w-4" />,
      color: "text-blue-600 dark:text-blue-400",
      bgColor: "bg-blue-50 dark:bg-blue-950/30",
      borderColor: "border-blue-200 dark:border-blue-800",
      label: "Customer"
    },
    strategic: {
      icon: <Target className="h-4 w-4" />,
      color: "text-red-600 dark:text-red-400",
      bgColor: "bg-red-50 dark:bg-red-950/30",
      borderColor: "border-red-200 dark:border-red-800",
      label: "Strategic"
    },
    general: {
      icon: <Lightbulb className="h-4 w-4" />,
      color: "text-cyan-600 dark:text-cyan-400",
      bgColor: "bg-cyan-50 dark:bg-cyan-950/30",
      borderColor: "border-cyan-200 dark:border-cyan-800",
      label: "Insight"
    }
  }

  // === HANDLERS ===
  const toggleExpand = (index) => {
    setExpandedCards(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const handleExplore = (insight, index) => {
    if (callAction) {
      callAction({
        name: "explore_insight",
        payload: { insight, index }
      })
    } else if (sendUserMessage) {
      sendUserMessage(`Tell me more about this insight: "${insight.text}"`)
    }
  }

  const handleSave = (insight, index) => {
    setSavedInsights(prev => [...prev, index])
    if (callAction) {
      callAction({
        name: "save_insight",
        payload: { insight, index }
      })
    }
  }

  const handleShare = (insight) => {
    if (callAction) {
      callAction({
        name: "share_insight",
        payload: { insight }
      })
    }
  }

  const handleShowAll = () => {
    setShowAll(true)
    if (updateElement) {
      updateElement({ ...props, max_display: insights.length })
    }
  }

  // === CONFIDENCE INDICATOR ===
  const ConfidenceIndicator = ({ confidence }) => {
    const percent = Math.round(confidence * 100)
    let colorClass = "bg-green-500"
    let label = "High"

    if (percent < 50) {
      colorClass = "bg-red-500"
      label = "Low"
    } else if (percent < 75) {
      colorClass = "bg-amber-500"
      label = "Medium"
    }

    return (
      <div className="flex items-center gap-2">
        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full ${colorClass} rounded-full transition-all`}
            style={{ width: `${percent}%` }}
          />
        </div>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    )
  }

  // === RENDER SINGLE INSIGHT ===
  const renderInsight = (insight, index) => {
    const category = insight.category || "general"
    const config = categoryConfig[category] || categoryConfig.general
    const isExpanded = expandedCards[index]
    const isSaved = savedInsights.includes(index)

    return (
      <div
        key={index}
        className={`p-4 rounded-lg border transition-all ${config.bgColor} ${config.borderColor}`}
      >
        <div className="flex items-start gap-3">
          {/* Category Icon */}
          <div className={`mt-0.5 ${config.color}`}>
            {config.icon}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Header Row */}
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <Badge variant="secondary" className="text-xs">
                {config.label}
              </Badge>
              {show_confidence && insight.confidence && (
                <ConfidenceIndicator confidence={insight.confidence} />
              )}
              {insight.timestamp && (
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {insight.timestamp}
                </span>
              )}
            </div>

            {/* Insight Text */}
            <p className="text-sm text-foreground font-medium leading-relaxed">
              {insight.text}
            </p>

            {/* Expandable Source */}
            {expandable && insight.source_message && (
              <Collapsible open={isExpanded} onOpenChange={() => toggleExpand(index)}>
                <CollapsibleTrigger asChild>
                  <button className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mt-2 transition-colors">
                    <MessageSquare className="h-3 w-3" />
                    View source context
                    {isExpanded ? (
                      <ChevronUp className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="mt-2 p-2 bg-muted/50 rounded text-xs text-muted-foreground italic">
                    "{insight.source_message}"
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-2 mt-3">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                onClick={() => handleExplore(insight, index)}
              >
                <Sparkles className="h-3 w-3 mr-1" />
                Explore
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className={`h-7 text-xs ${isSaved ? 'text-green-600' : ''}`}
                onClick={() => handleSave(insight, index)}
                disabled={isSaved}
              >
                {isSaved ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Saved
                  </>
                ) : (
                  <>
                    <BookmarkPlus className="h-3 w-3 mr-1" />
                    Save
                  </>
                )}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                onClick={() => handleShare(insight)}
              >
                <Share2 className="h-3 w-3 mr-1" />
                Share
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // === EMPTY STATE ===
  if (insights.length === 0) {
    return (
      <Card className="w-full max-w-lg">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <Lightbulb className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No insights extracted yet.</p>
            <p className="text-xs mt-1">Continue the conversation to surface key insights.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Determine which insights to display
  const displayInsights = showAll ? insights : insights.slice(0, max_display)
  const hasMore = insights.length > max_display && !showAll

  // === RENDER ===
  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Lightbulb className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {insights.length} insight{insights.length !== 1 ? 's' : ''}
          </Badge>
        </div>
        <CardDescription>
          AI-extracted insights from your conversation
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-3">
        {displayInsights.map((insight, index) => renderInsight(insight, index))}
      </CardContent>

      {hasMore && (
        <CardFooter>
          <Button
            variant="outline"
            className="w-full"
            onClick={handleShowAll}
          >
            Show {insights.length - max_display} more insight{insights.length - max_display !== 1 ? 's' : ''}
            <ChevronDown className="h-4 w-4 ml-1" />
          </Button>
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
    # Process message for insights
    context.process_message(message.content, "user")

    # Get AI response...
    context.process_message(ai_response, "assistant")

    # Generate insight card props
    insight_props = context.to_props("InsightCard")

    elements = [
        cl.CustomElement(
            name="InsightCard",
            props=insight_props,
            display="inline"
        )
    ]
    await cl.Message(content="Here are the key insights:", elements=elements).send()

# Or with manual props:
elements = [
    cl.CustomElement(
        name="InsightCard",
        props={
            "title": "Key Insights",
            "show_confidence": True,
            "expandable": True,
            "max_display": 3,
            "insights": [
                {
                    "text": "Customers are hiring the product to feel productive, not to complete tasks",
                    "category": "customer",
                    "confidence": 0.85,
                    "source_message": "They said they feel accomplished when...",
                    "timestamp": "2 min ago"
                },
                {
                    "text": "The assumption that users want more features may be incorrect",
                    "category": "assumption",
                    "confidence": 0.72,
                    "source_message": "Most users only use 3 features..."
                },
                {
                    "text": "Market timing could be a risk if competitor launches first",
                    "category": "risk",
                    "confidence": 0.68
                }
            ]
        },
        display="inline"
    )
]

@cl.action_callback("explore_insight")
async def handle_explore(action: cl.Action):
    insight = action.payload.get("insight")
    await cl.Message(content=f"Let's explore: {insight['text']}").send()

@cl.action_callback("save_insight")
async def handle_save(action: cl.Action):
    insight = action.payload.get("insight")
    # Save to session or database
    await cl.Message(content="Insight saved to your notes!").send()

================================================================================
*/
