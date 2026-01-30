/**
 * SessionSummary - End-of-session summary and learnings
 *
 * Provides comprehensive summary of a PWS session including key insights,
 * assumptions tracked, evidence gathered, and action items.
 *
 * Props (injected globally by Chainlit):
 * - session_title: optional title for the session
 * - duration: session duration string
 * - framework_used: which framework was primary
 * - phases_completed: array of completed phase names
 * - insights: array of key insights
 * - assumptions: array of tracked assumptions
 * - evidence: array of evidence collected
 * - quotes: array of notable quotes
 * - action_items: array of next steps
 * - quality_score: object with scoring breakdown
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import {
  FileText, Clock, Target, Lightbulb, Brain, Microscope,
  Quote, CheckSquare, Download, Share2, Calendar, TrendingUp,
  Award, ChevronRight, ExternalLink, BarChart, CheckCircle,
  AlertTriangle, Star, Sparkles, ArrowRight
} from "lucide-react"
import { useState } from "react"

export default function SessionSummary() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    session_title = "PWS Session Summary",
    duration = "45 min",
    framework_used = null,
    phases_completed = [],
    insights = [],
    assumptions = [],
    evidence = [],
    quotes = [],
    action_items = [],
    quality_score = null,
    timestamp = null,
    element_id = null
  } = props || {}

  // Local state
  const [activeTab, setActiveTab] = useState("overview")

  // === STATS ===
  const stats = {
    insights: insights.length,
    assumptions: assumptions.length,
    assumptionsValidated: assumptions.filter(a => a.status === "validated").length,
    evidence: evidence.length,
    quotes: quotes.length,
    actionItems: action_items.length,
    actionItemsCompleted: action_items.filter(a => a.completed).length,
    phasesCompleted: phases_completed.length
  }

  // === FRAMEWORK CONFIG ===
  const frameworkNames = {
    jtbd: "Jobs to Be Done",
    tta: "Trending to the Absurd",
    scurve: "S-Curve Analysis",
    redteam: "Red Team",
    ackoff: "Ackoff's DIKW",
    bono: "Six Thinking Hats"
  }

  // === HANDLERS ===
  const handleExport = (format = "markdown") => {
    if (callAction) {
      callAction({
        name: "export_session",
        payload: {
          format,
          session_title,
          insights,
          assumptions,
          evidence,
          quotes,
          action_items
        }
      })
    }
  }

  const handleShare = () => {
    if (callAction) {
      callAction({
        name: "share_session",
        payload: { session_title }
      })
    }
  }

  const handleContinue = () => {
    if (sendUserMessage) {
      sendUserMessage("I'd like to continue where we left off")
    }
  }

  const handleScheduleFollowup = () => {
    if (callAction) {
      callAction({
        name: "schedule_followup",
        payload: { action_items }
      })
    }
  }

  // === RENDER OVERVIEW TAB ===
  const renderOverview = () => (
    <div className="space-y-4">
      {/* Session Info */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-sm">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span>{duration}</span>
        </div>
        {framework_used && (
          <div className="flex items-center gap-2 text-sm">
            <Target className="h-4 w-4 text-muted-foreground" />
            <span>{frameworkNames[framework_used] || framework_used}</span>
          </div>
        )}
        {timestamp && (
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span>{timestamp}</span>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-cyan-50 dark:bg-cyan-950/30 rounded-lg border border-cyan-200 dark:border-cyan-800">
          <div className="flex items-center gap-2 mb-1">
            <Lightbulb className="h-4 w-4 text-cyan-500" />
            <span className="text-xs text-muted-foreground">Insights</span>
          </div>
          <div className="text-2xl font-bold text-cyan-600">{stats.insights}</div>
        </div>

        <div className="p-3 bg-purple-50 dark:bg-purple-950/30 rounded-lg border border-purple-200 dark:border-purple-800">
          <div className="flex items-center gap-2 mb-1">
            <Brain className="h-4 w-4 text-purple-500" />
            <span className="text-xs text-muted-foreground">Assumptions</span>
          </div>
          <div className="text-2xl font-bold text-purple-600">
            {stats.assumptionsValidated}/{stats.assumptions}
          </div>
          <div className="text-xs text-muted-foreground">validated</div>
        </div>

        <div className="p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 mb-1">
            <Microscope className="h-4 w-4 text-green-500" />
            <span className="text-xs text-muted-foreground">Evidence</span>
          </div>
          <div className="text-2xl font-bold text-green-600">{stats.evidence}</div>
        </div>

        <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="flex items-center gap-2 mb-1">
            <CheckSquare className="h-4 w-4 text-amber-500" />
            <span className="text-xs text-muted-foreground">Actions</span>
          </div>
          <div className="text-2xl font-bold text-amber-600">
            {stats.actionItemsCompleted}/{stats.actionItems}
          </div>
          <div className="text-xs text-muted-foreground">completed</div>
        </div>
      </div>

      {/* Quality Score */}
      {quality_score && (
        <div className="p-4 bg-muted/30 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-primary" />
              <span className="font-medium">Session Quality Score</span>
            </div>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`h-4 w-4 ${
                    star <= Math.round(quality_score.overall * 5)
                      ? "text-amber-400 fill-amber-400"
                      : "text-muted"
                  }`}
                />
              ))}
              <span className="ml-2 font-bold">{Math.round(quality_score.overall * 100)}%</span>
            </div>
          </div>

          {quality_score.dimensions && (
            <div className="space-y-2">
              {Object.entries(quality_score.dimensions).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-32 capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <Progress value={value * 100} className="flex-1 h-1.5" />
                  <span className="text-xs font-medium w-8">{Math.round(value * 100)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Phases Completed */}
      {phases_completed.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Phases Completed
          </h4>
          <div className="flex flex-wrap gap-2">
            {phases_completed.map((phase, i) => (
              <Badge key={i} variant="secondary" className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3 text-green-500" />
                {phase}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  // === RENDER INSIGHTS TAB ===
  const renderInsights = () => (
    <ScrollArea className="h-[300px]">
      <div className="space-y-3 pr-2">
        {insights.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No insights recorded in this session
          </div>
        ) : (
          insights.map((insight, i) => (
            <div
              key={i}
              className="p-3 bg-cyan-50 dark:bg-cyan-950/30 rounded-lg border border-cyan-200 dark:border-cyan-800"
            >
              <div className="flex items-start gap-2">
                <Lightbulb className="h-4 w-4 text-cyan-500 mt-0.5" />
                <div>
                  <p className="text-sm">{insight.text || insight}</p>
                  {insight.category && (
                    <Badge variant="outline" className="text-xs mt-2">
                      {insight.category}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </ScrollArea>
  )

  // === RENDER ACTIONS TAB ===
  const renderActions = () => (
    <ScrollArea className="h-[300px]">
      <div className="space-y-3 pr-2">
        {action_items.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No action items from this session
          </div>
        ) : (
          action_items.map((item, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg border ${
                item.completed
                  ? "bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800"
                  : item.priority === "high"
                  ? "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800"
                  : "bg-muted/30 border-border"
              }`}
            >
              <div className="flex items-start gap-2">
                {item.completed ? (
                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                ) : item.priority === "high" ? (
                  <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5" />
                )}
                <div className="flex-1">
                  <p className={`text-sm ${item.completed ? "line-through text-muted-foreground" : ""}`}>
                    {item.text || item}
                  </p>
                  {item.due && (
                    <span className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Due: {item.due}
                    </span>
                  )}
                </div>
                {item.priority && !item.completed && (
                  <Badge variant="outline" className={`text-xs ${
                    item.priority === "high" ? "border-red-300 text-red-600" : ""
                  }`}>
                    {item.priority}
                  </Badge>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </ScrollArea>
  )

  // === RENDER EVIDENCE TAB ===
  const renderEvidence = () => (
    <ScrollArea className="h-[300px]">
      <div className="space-y-3 pr-2">
        {evidence.length === 0 && quotes.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No evidence or quotes collected
          </div>
        ) : (
          <>
            {/* Evidence */}
            {evidence.map((item, i) => (
              <div
                key={`e-${i}`}
                className="p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800"
              >
                <div className="flex items-start gap-2">
                  <Microscope className="h-4 w-4 text-green-500 mt-0.5" />
                  <div>
                    <p className="text-sm">{item.text || item}</p>
                    {item.source_type && (
                      <Badge variant="outline" className="text-xs mt-2">
                        {item.source_type}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Quotes */}
            {quotes.map((quote, i) => (
              <div
                key={`q-${i}`}
                className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800"
              >
                <div className="flex items-start gap-2">
                  <Quote className="h-4 w-4 text-blue-500 mt-0.5" />
                  <div>
                    <p className="text-sm italic">"{quote.text || quote}"</p>
                    {quote.attribution && (
                      <p className="text-xs text-muted-foreground mt-1">
                        — {quote.attribution}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </ScrollArea>
  )

  // === RENDER ===
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileText className="h-5 w-5 text-primary" />
            {session_title}
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            Session Complete
          </Badge>
        </div>
        <CardDescription>
          Summary of your problem-solving session
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full grid grid-cols-4 mb-4">
            <TabsTrigger value="overview" className="text-xs">
              <BarChart className="h-3 w-3 mr-1" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="insights" className="text-xs">
              <Lightbulb className="h-3 w-3 mr-1" />
              Insights ({stats.insights})
            </TabsTrigger>
            <TabsTrigger value="actions" className="text-xs">
              <CheckSquare className="h-3 w-3 mr-1" />
              Actions ({stats.actionItems})
            </TabsTrigger>
            <TabsTrigger value="evidence" className="text-xs">
              <Microscope className="h-3 w-3 mr-1" />
              Evidence ({stats.evidence + stats.quotes})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">{renderOverview()}</TabsContent>
          <TabsContent value="insights">{renderInsights()}</TabsContent>
          <TabsContent value="actions">{renderActions()}</TabsContent>
          <TabsContent value="evidence">{renderEvidence()}</TabsContent>
        </Tabs>
      </CardContent>

      <Separator />

      <CardFooter className="flex gap-2 pt-4">
        <Button variant="outline" className="flex-1" onClick={handleContinue}>
          <ArrowRight className="h-4 w-4 mr-1" />
          Continue Session
        </Button>
        <Button variant="outline" onClick={() => handleExport("markdown")}>
          <Download className="h-4 w-4" />
        </Button>
        <Button variant="outline" onClick={handleShare}>
          <Share2 className="h-4 w-4" />
        </Button>
        {stats.actionItems > 0 && (
          <Button variant="outline" onClick={handleScheduleFollowup}>
            <Calendar className="h-4 w-4" />
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}

/*
================================================================================
PYTHON USAGE
================================================================================

import chainlit as cl
from utils.context_extraction import ConversationContext

# At end of session, generate summary
context = ConversationContext()

@cl.action_callback("end_session")
async def handle_end_session(action: cl.Action):
    # Generate comprehensive summary props
    summary_props = context.to_props("SessionSummary")

    # Add session metadata
    summary_props.update({
        "session_title": "Customer Discovery Session",
        "duration": "47 minutes",
        "timestamp": "Jan 30, 2026 3:45 PM"
    })

    elements = [
        cl.CustomElement(
            name="SessionSummary",
            props=summary_props,
            display="inline"
        )
    ]
    await cl.Message(content="Session complete! Here's your summary:", elements=elements).send()

# Or with manual props:
elements = [
    cl.CustomElement(
        name="SessionSummary",
        props={
            "session_title": "Market Analysis Session",
            "duration": "52 minutes",
            "framework_used": "jtbd",
            "timestamp": "Jan 30, 2026",
            "phases_completed": ["Context Setting", "Job Identification", "Competing Solutions"],
            "insights": [
                {"text": "Customers are hiring for peace of mind, not features", "category": "customer"},
                {"text": "Current solutions fail at the emotional job", "category": "opportunity"},
                {"text": "Price sensitivity is lower than assumed", "category": "assumption"}
            ],
            "assumptions": [
                {"text": "Users will pay premium for reliability", "status": "validated"},
                {"text": "Enterprise is our primary market", "status": "untested"}
            ],
            "evidence": [
                {"text": "85% of churned users cited reliability issues", "source_type": "web"},
                {"text": "NPS dropped 40 points after outage", "source_type": "user"}
            ],
            "quotes": [
                {"text": "I just want it to work when I need it", "attribution": "Customer Interview #4"}
            ],
            "action_items": [
                {"text": "Interview 5 more enterprise customers", "priority": "high", "due": "Feb 5"},
                {"text": "Map competitor reliability claims", "priority": "medium"},
                {"text": "Draft value proposition focused on reliability", "completed": True}
            ],
            "quality_score": {
                "overall": 0.78,
                "dimensions": {
                    "problem_clarity": 0.85,
                    "assumption_awareness": 0.72,
                    "evidence_grounding": 0.80,
                    "actionability": 0.75
                }
            }
        },
        display="inline"
    )
]

@cl.action_callback("export_session")
async def handle_export(action: cl.Action):
    format = action.payload.get("format", "markdown")
    # Generate export in requested format
    await cl.Message(content="Exporting session summary...").send()

@cl.action_callback("schedule_followup")
async def handle_schedule(action: cl.Action):
    action_items = action.payload.get("action_items", [])
    pending = [a for a in action_items if not a.get("completed")]
    await cl.Message(content=f"Would you like to schedule follow-up for {len(pending)} pending items?").send()

================================================================================
*/
