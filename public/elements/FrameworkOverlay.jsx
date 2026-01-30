/**
 * FrameworkOverlay - Context-aware framework guidance panel
 *
 * Displays current framework, phase progress, key concepts, and tips.
 * Provides quick actions and mini-visualizations for active methodology.
 *
 * Props (injected globally by Chainlit):
 * - framework_id: string (jtbd, tta, scurve, redteam, ackoff, bono)
 * - current_phase: number (0-indexed)
 * - phase_progress: array of {name, status, description}
 * - tips: array of tip strings for current context
 * - key_concepts: array of {term, definition}
 * - show_visualization: boolean to show mini-framework viz
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Compass, Target, TrendingUp, Users, Clock, Shield,
  Lightbulb, BookOpen, ChevronRight, ChevronDown, ChevronUp,
  Info, Play, CheckCircle, Circle, ArrowRight, Sparkles,
  Video, HelpCircle, Layers, Brain, Zap
} from "lucide-react"
import { useState } from "react"

export default function FrameworkOverlay() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    framework_id = "jtbd",
    current_phase = 0,
    phase_progress = [],
    tips = [],
    key_concepts = [],
    show_visualization = true,
    collapsed = false,
    element_id = null
  } = props || {}

  // Local state
  const [isCollapsed, setIsCollapsed] = useState(collapsed)
  const [showConcepts, setShowConcepts] = useState(false)

  // === FRAMEWORK CONFIGURATION ===
  const frameworkConfig = {
    jtbd: {
      name: "Jobs to Be Done",
      icon: <Users className="h-5 w-5" />,
      color: "text-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-950/30",
      borderColor: "border-blue-200 dark:border-blue-800",
      description: "Understand customer progress and hiring criteria",
      defaultPhases: [
        { name: "Context", description: "Understand the situation" },
        { name: "Job Identification", description: "Find the functional/emotional job" },
        { name: "Competing Solutions", description: "Map current alternatives" },
        { name: "Success Criteria", description: "Define hiring criteria" }
      ],
      visualization: "jobs-wheel"
    },
    tta: {
      name: "Trending to the Absurd",
      icon: <TrendingUp className="h-5 w-5" />,
      color: "text-purple-500",
      bgColor: "bg-purple-50 dark:bg-purple-950/30",
      borderColor: "border-purple-200 dark:border-purple-800",
      description: "Extrapolate trends to extreme futures",
      defaultPhases: [
        { name: "Identify Trends", description: "Find relevant trends" },
        { name: "Extrapolate", description: "Push to extremes" },
        { name: "Implications", description: "What if this happens?" },
        { name: "Opportunities", description: "Where are the gaps?" }
      ],
      visualization: "trend-arrow"
    },
    scurve: {
      name: "S-Curve Analysis",
      icon: <Clock className="h-5 w-5" />,
      color: "text-green-500",
      bgColor: "bg-green-50 dark:bg-green-950/30",
      borderColor: "border-green-200 dark:border-green-800",
      description: "Time technology adoption and transitions",
      defaultPhases: [
        { name: "Technology Mapping", description: "Plot current position" },
        { name: "Maturity Assessment", description: "Where on the curve?" },
        { name: "Transition Points", description: "When to jump?" },
        { name: "Strategy", description: "Timing decisions" }
      ],
      visualization: "scurve"
    },
    redteam: {
      name: "Red Team",
      icon: <Shield className="h-5 w-5" />,
      color: "text-red-500",
      bgColor: "bg-red-50 dark:bg-red-950/30",
      borderColor: "border-red-200 dark:border-red-800",
      description: "Challenge assumptions and find weaknesses",
      defaultPhases: [
        { name: "Define Position", description: "What are we defending?" },
        { name: "Attack Vectors", description: "How could this fail?" },
        { name: "Stress Test", description: "Push the limits" },
        { name: "Fortify", description: "Strengthen weaknesses" }
      ],
      visualization: "shield"
    },
    ackoff: {
      name: "Ackoff's DIKW Pyramid",
      icon: <Target className="h-5 w-5" />,
      color: "text-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-950/30",
      borderColor: "border-amber-200 dark:border-amber-800",
      description: "Transform data into wisdom",
      defaultPhases: [
        { name: "Data", description: "Raw facts and figures" },
        { name: "Information", description: "Processed data" },
        { name: "Knowledge", description: "Actionable understanding" },
        { name: "Wisdom", description: "Applied judgment" }
      ],
      visualization: "pyramid"
    },
    bono: {
      name: "Six Thinking Hats",
      icon: <Lightbulb className="h-5 w-5" />,
      color: "text-cyan-500",
      bgColor: "bg-cyan-50 dark:bg-cyan-950/30",
      borderColor: "border-cyan-200 dark:border-cyan-800",
      description: "Explore multiple perspectives systematically",
      defaultPhases: [
        { name: "White Hat", description: "Facts and data" },
        { name: "Red Hat", description: "Emotions and intuition" },
        { name: "Black Hat", description: "Caution and risks" },
        { name: "Yellow Hat", description: "Benefits and optimism" },
        { name: "Green Hat", description: "Creativity and alternatives" },
        { name: "Blue Hat", description: "Process and summary" }
      ],
      visualization: "hats"
    }
  }

  const config = frameworkConfig[framework_id] || frameworkConfig.jtbd
  const phases = phase_progress.length > 0 ? phase_progress : config.defaultPhases

  // === HANDLERS ===
  const handlePhaseClick = (phaseIndex) => {
    if (callAction) {
      callAction({
        name: "go_to_phase",
        payload: { framework_id, phase_index: phaseIndex }
      })
    }
  }

  const handleShowVideo = () => {
    if (callAction) {
      callAction({
        name: "show_framework_video",
        payload: { framework_id, phase: current_phase }
      })
    }
  }

  const handleAskHelp = () => {
    if (sendUserMessage) {
      sendUserMessage(`Help me understand how to apply ${config.name} to my problem`)
    }
  }

  const handleNextPhase = () => {
    if (callAction) {
      callAction({
        name: "advance_phase",
        payload: { framework_id, current_phase }
      })
    } else if (sendUserMessage) {
      const nextPhase = phases[current_phase + 1]
      if (nextPhase) {
        sendUserMessage(`I'm ready to move to ${nextPhase.name}`)
      }
    }
  }

  // === MINI VISUALIZATIONS ===
  const renderVisualization = () => {
    switch (config.visualization) {
      case "pyramid":
        return (
          <div className="relative h-24 flex items-end justify-center">
            {["Wisdom", "Knowledge", "Information", "Data"].map((level, i) => {
              const width = 40 + (i * 20)
              const isActive = (3 - i) <= current_phase
              return (
                <div
                  key={level}
                  className={`absolute bottom-0 h-5 rounded-t transition-all ${
                    isActive ? "bg-amber-500" : "bg-muted"
                  }`}
                  style={{
                    width: `${width}%`,
                    bottom: `${i * 22}px`,
                    zIndex: 4 - i
                  }}
                >
                  <span className="text-[8px] text-white font-medium absolute inset-0 flex items-center justify-center">
                    {level}
                  </span>
                </div>
              )
            })}
          </div>
        )

      case "scurve":
        return (
          <svg viewBox="0 0 100 50" className="w-full h-20">
            <path
              d="M 5 45 Q 25 45, 35 40 Q 50 30, 60 15 Q 70 5, 95 5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-muted"
            />
            <circle
              cx={15 + (current_phase * 25)}
              cy={45 - (current_phase * 12)}
              r="4"
              className="fill-green-500"
            />
            <text x="10" y="50" className="text-[6px] fill-muted-foreground">Intro</text>
            <text x="40" y="35" className="text-[6px] fill-muted-foreground">Growth</text>
            <text x="75" y="15" className="text-[6px] fill-muted-foreground">Maturity</text>
          </svg>
        )

      case "hats":
        const hatColors = ["white", "red", "black", "yellow", "green", "blue"]
        return (
          <div className="flex justify-center gap-1">
            {hatColors.map((color, i) => (
              <div
                key={color}
                className={`w-6 h-8 rounded-t-full border-2 transition-all ${
                  i === current_phase
                    ? "scale-125 ring-2 ring-primary"
                    : i < current_phase
                    ? "opacity-50"
                    : "opacity-30"
                }`}
                style={{
                  backgroundColor: color === "white" ? "#f5f5f5" : color,
                  borderColor: color === "white" ? "#ccc" : color
                }}
              />
            ))}
          </div>
        )

      default:
        return null
    }
  }

  // === PHASE PROGRESS BAR ===
  const progressPercent = phases.length > 0
    ? Math.round(((current_phase + 1) / phases.length) * 100)
    : 0

  // === COLLAPSED VIEW ===
  if (isCollapsed) {
    return (
      <Card className={`w-full max-w-sm ${config.bgColor} ${config.borderColor} border`}>
        <button
          onClick={() => setIsCollapsed(false)}
          className="w-full p-3 flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <div className={config.color}>{config.icon}</div>
            <span className="text-sm font-medium">{config.name}</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              Phase {current_phase + 1}/{phases.length}
            </Badge>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </div>
        </button>
      </Card>
    )
  }

  // === FULL VIEW ===
  return (
    <Card className={`w-full max-w-sm ${config.bgColor} ${config.borderColor} border`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <div className={config.color}>{config.icon}</div>
            {config.name}
          </CardTitle>
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6"
            onClick={() => setIsCollapsed(true)}
          >
            <ChevronUp className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription className="text-xs">
          {config.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Visualization */}
        {show_visualization && (
          <div className="p-2 bg-background/50 rounded-lg">
            {renderVisualization()}
          </div>
        )}

        {/* Phase Progress */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium">Progress</span>
            <span className="text-xs text-muted-foreground">
              Phase {current_phase + 1} of {phases.length}
            </span>
          </div>
          <Progress value={progressPercent} className="h-1.5" />
        </div>

        {/* Current Phase */}
        <div className="p-2 bg-primary/10 rounded-lg border border-primary/20">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
              <span className="text-xs font-bold text-primary-foreground">{current_phase + 1}</span>
            </div>
            <div>
              <div className="text-sm font-medium">{phases[current_phase]?.name}</div>
              <div className="text-xs text-muted-foreground">
                {phases[current_phase]?.description}
              </div>
            </div>
          </div>
        </div>

        {/* Phase List */}
        <div className="space-y-1">
          {phases.map((phase, i) => {
            const isComplete = i < current_phase
            const isCurrent = i === current_phase
            const isPending = i > current_phase

            return (
              <button
                key={i}
                onClick={() => handlePhaseClick(i)}
                className={`w-full flex items-center gap-2 p-1.5 rounded text-left transition-all ${
                  isCurrent
                    ? "bg-primary/20"
                    : "hover:bg-muted/50"
                }`}
              >
                {isComplete && <CheckCircle className="h-3 w-3 text-green-500" />}
                {isCurrent && <Circle className="h-3 w-3 text-primary fill-primary" />}
                {isPending && <Circle className="h-3 w-3 text-muted-foreground" />}
                <span className={`text-xs ${isPending ? "text-muted-foreground" : ""}`}>
                  {phase.name}
                </span>
              </button>
            )
          })}
        </div>

        {/* Tips */}
        {tips.length > 0 && (
          <div className="p-2 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
            <div className="flex items-start gap-2">
              <Lightbulb className="h-3 w-3 text-amber-500 mt-0.5" />
              <div className="text-xs text-amber-800 dark:text-amber-300">
                {tips[0]}
              </div>
            </div>
          </div>
        )}

        {/* Key Concepts */}
        {key_concepts.length > 0 && (
          <Collapsible open={showConcepts} onOpenChange={setShowConcepts}>
            <CollapsibleTrigger asChild>
              <button className="w-full flex items-center justify-between text-xs text-muted-foreground hover:text-foreground">
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  Key Concepts
                </span>
                {showConcepts ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-2 space-y-1">
                {key_concepts.map((concept, i) => (
                  <div key={i} className="text-xs p-1.5 bg-muted/50 rounded">
                    <span className="font-medium">{concept.term}:</span>{" "}
                    <span className="text-muted-foreground">{concept.definition}</span>
                  </div>
                ))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>

      <CardFooter className="flex gap-2 pt-2">
        {current_phase < phases.length - 1 && (
          <Button size="sm" className="flex-1 h-7 text-xs" onClick={handleNextPhase}>
            Next Phase
            <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        )}
        <Button size="sm" variant="outline" className="h-7 text-xs px-2" onClick={handleShowVideo}>
          <Video className="h-3 w-3" />
        </Button>
        <Button size="sm" variant="outline" className="h-7 text-xs px-2" onClick={handleAskHelp}>
          <HelpCircle className="h-3 w-3" />
        </Button>
      </CardFooter>
    </Card>
  )
}

/*
================================================================================
PYTHON USAGE
================================================================================

import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="FrameworkOverlay",
            props={
                "framework_id": "ackoff",
                "current_phase": 1,
                "show_visualization": True,
                "phase_progress": [
                    {"name": "Data Collection", "status": "completed", "description": "Gather raw facts"},
                    {"name": "Information Analysis", "status": "current", "description": "Process into meaning"},
                    {"name": "Knowledge Synthesis", "status": "pending", "description": "Extract patterns"},
                    {"name": "Wisdom Application", "status": "pending", "description": "Make decisions"}
                ],
                "tips": [
                    "Focus on understanding relationships between data points before moving to knowledge"
                ],
                "key_concepts": [
                    {"term": "Data", "definition": "Raw symbols without context"},
                    {"term": "Information", "definition": "Data with meaning"},
                    {"term": "Knowledge", "definition": "Information applied"},
                    {"term": "Wisdom", "definition": "Knowledge with judgment"}
                ]
            },
            display="side"  # Show as sidebar
        )
    ]
    await cl.Message(content="Let's continue with DIKW analysis:", elements=elements).send()

@cl.action_callback("go_to_phase")
async def handle_go_to_phase(action: cl.Action):
    phase = action.payload.get("phase_index")
    await cl.Message(content=f"Moving to phase {phase + 1}...").send()

@cl.action_callback("advance_phase")
async def handle_advance(action: cl.Action):
    current = action.payload.get("current_phase")
    await cl.Message(content=f"Great progress! Let's move to the next phase.").send()

@cl.action_callback("show_framework_video")
async def handle_video(action: cl.Action):
    framework = action.payload.get("framework_id")
    await cl.Message(content=f"Loading {framework} tutorial video...").send()

================================================================================
*/
