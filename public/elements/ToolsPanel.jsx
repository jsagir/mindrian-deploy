/**
 * ToolsPanel - Floating PWS Tools Repository
 *
 * A floating panel (bottom-right) showing available PWS methodology tools
 * with contextual tooltips that explain WHY each tool might help based on
 * the current conversation.
 *
 * Props (injected globally by Chainlit):
 * - conversationContext: string - Summary of current conversation
 * - currentBot: string - Currently active bot
 * - expanded: boolean - Whether panel is expanded
 */

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Unlock,
  Target,
  TrendingUp,
  Skull,
  LineChart,
  Triangle,
  Globe,
  HelpCircle,
  Layers,
  CheckCircle,
  Compass,
  Sparkles,
  ChevronUp,
  ChevronDown,
  Wrench,
  X,
} from "lucide-react"

// PWS Tools with contextual descriptions
const PWS_TOOLS = [
  {
    id: "reverse_salient",
    name: "Reverse Salient",
    icon: Unlock,
    shortDesc: "Find the bottleneck",
    fullDesc: "Identify the ONE constraint holding everything else back. Fix this, and everything improves.",
    contextTriggers: ["stuck", "bottleneck", "constraint", "blocking", "infrastructure", "scaling"],
    contextualHelp: (ctx) => {
      if (ctx.includes("stuck") || ctx.includes("block"))
        return "You seem stuck — this tool finds what's really blocking progress."
      if (ctx.includes("infrastructure") || ctx.includes("scaling"))
        return "Infrastructure problems often have one reverse salient. Let's find it."
      return "Every system has one key constraint. What's holding your space back?"
    },
    action: "switch_to_tta", // or specific action
    color: "text-amber-600 dark:text-amber-400",
  },
  {
    id: "jtbd",
    name: "Jobs to Be Done",
    icon: Target,
    shortDesc: "What job are they hiring?",
    fullDesc: "People don't buy products — they hire them to make progress. What's the real job?",
    contextTriggers: ["customer", "user", "buying", "product", "feature", "want", "need"],
    contextualHelp: (ctx) => {
      if (ctx.includes("customer") || ctx.includes("user"))
        return "Let's dig into what progress your customers are actually trying to make."
      if (ctx.includes("feature") || ctx.includes("product"))
        return "Features serve jobs. What job would this feature be hired for?"
      return "Understanding the job unlocks better solutions."
    },
    action: "switch_to_jtbd",
    color: "text-blue-600 dark:text-blue-400",
  },
  {
    id: "tta",
    name: "Trending to Absurd",
    icon: TrendingUp,
    shortDesc: "Take it to extremes",
    fullDesc: "Extrapolate trends to their logical extreme. What breaks first? That's where opportunity lives.",
    contextTriggers: ["trend", "future", "growing", "changing", "emerging", "AI", "technology"],
    contextualHelp: (ctx) => {
      if (ctx.includes("trend") || ctx.includes("growing"))
        return "Let's push this trend to its extreme and see what breaks."
      if (ctx.includes("AI") || ctx.includes("technology"))
        return "Tech trends have breaking points. What fails first if this continues?"
      return "Extrapolate to find hidden opportunities."
    },
    action: "switch_to_tta",
    color: "text-purple-600 dark:text-purple-400",
  },
  {
    id: "red_team",
    name: "Red Team",
    icon: Skull,
    shortDesc: "Attack your assumptions",
    fullDesc: "Be your own devil's advocate. Find the flaws before the market does.",
    contextTriggers: ["assumption", "believe", "think", "confident", "sure", "risk", "compete"],
    contextualHelp: (ctx) => {
      if (ctx.includes("assumption") || ctx.includes("believe"))
        return "You've made assumptions. Let's stress-test them before reality does."
      if (ctx.includes("confident") || ctx.includes("sure"))
        return "Confidence can be dangerous. What would make this fail?"
      return "Every idea has weaknesses. Better to find them yourself."
    },
    action: "switch_to_redteam",
    color: "text-red-600 dark:text-red-400",
  },
  {
    id: "scurve",
    name: "S-Curve",
    icon: LineChart,
    shortDesc: "Where on the curve?",
    fullDesc: "Every technology follows slow → rapid → plateau. Timing is everything.",
    contextTriggers: ["timing", "market", "adoption", "mature", "early", "late", "invest"],
    contextualHelp: (ctx) => {
      if (ctx.includes("timing") || ctx.includes("invest"))
        return "Let's figure out where this technology is on its lifecycle."
      if (ctx.includes("early") || ctx.includes("mature"))
        return "Timing changes everything. Is this too early, just right, or too late?"
      return "Understanding the S-curve helps you time your entry."
    },
    action: "switch_to_scurve",
    color: "text-green-600 dark:text-green-400",
  },
  {
    id: "ackoff",
    name: "DIKW Pyramid",
    icon: Triangle,
    shortDesc: "Validate understanding",
    fullDesc: "Data → Information → Knowledge → Wisdom. Don't act on incomplete understanding.",
    contextTriggers: ["data", "information", "understand", "decision", "evidence", "know"],
    contextualHelp: (ctx) => {
      if (ctx.includes("data") || ctx.includes("evidence"))
        return "You have data. Let's climb the pyramid to wisdom."
      if (ctx.includes("decision"))
        return "Before deciding, let's validate your understanding level."
      return "Avoid acting on incomplete understanding."
    },
    action: "switch_to_ackoff",
    color: "text-indigo-600 dark:text-indigo-400",
  },
  {
    id: "scenario",
    name: "Scenario Analysis",
    icon: Globe,
    shortDesc: "Multiple futures",
    fullDesc: "The future is uncertain. Explore multiple plausible paths, don't bet on one.",
    contextTriggers: ["future", "uncertain", "might", "could", "planning", "strategy"],
    contextualHelp: (ctx) => {
      if (ctx.includes("uncertain") || ctx.includes("might"))
        return "Uncertainty calls for scenarios, not predictions."
      if (ctx.includes("planning") || ctx.includes("strategy"))
        return "Good strategy accounts for multiple futures."
      return "Don't predict — prepare for multiple possibilities."
    },
    action: "switch_to_scenario",
    color: "text-cyan-600 dark:text-cyan-400",
  },
  {
    id: "beautiful_question",
    name: "Beautiful Question",
    icon: HelpCircle,
    shortDesc: "WHY → WHAT IF → HOW",
    fullDesc: "The quality of your solution depends on the quality of your question.",
    contextTriggers: ["why", "question", "curious", "wonder", "how might"],
    contextualHelp: (ctx) => {
      if (ctx.includes("why"))
        return "Good start with 'why'. Let's deepen the question."
      if (ctx.includes("curious") || ctx.includes("wonder"))
        return "Curiosity is the beginning. Let's turn it into a beautiful question."
      return "Better questions lead to better solutions."
    },
    action: "switch_to_beautiful_question",
    color: "text-pink-600 dark:text-pink-400",
  },
]

// Advanced LangGraph Pipelines
const ADVANCED_TOOLS = [
  {
    id: "minto",
    name: "Minto Pyramid",
    icon: Layers,
    shortDesc: "SCQA structured analysis",
    fullDesc: "Situation → Complication → Question → Answer. Structure your thinking.",
    contextualHelp: () => "Structure complex analysis with SCQA framework.",
    action: "run_minto_analysis",
    color: "text-orange-600 dark:text-orange-400",
  },
  {
    id: "validation",
    name: "Multi-Validation",
    icon: CheckCircle,
    shortDesc: "6-perspective stress test",
    fullDesc: "Six Thinking Hats + research. Test your idea from every angle.",
    contextualHelp: () => "Get comprehensive validation from multiple perspectives.",
    action: "switch_to_validation",
    color: "text-emerald-600 dark:text-emerald-400",
  },
  {
    id: "domain",
    name: "Domain Discovery",
    icon: Compass,
    shortDesc: "Find your territory",
    fullDesc: "Analyze your background to find where you can uniquely contribute.",
    contextualHelp: () => "Upload your CV or describe your experience to find your domain.",
    action: "switch_to_domain",
    color: "text-teal-600 dark:text-teal-400",
  },
  {
    id: "oracle",
    name: "Oracle Foresight",
    icon: Sparkles,
    shortDesc: "Prediction thinking",
    fullDesc: "Structure predictions with confidence levels and track outcomes.",
    contextualHelp: () => "Make structured predictions and learn from outcomes.",
    action: "run_oracle_prediction",
    color: "text-violet-600 dark:text-violet-400",
  },
]

export default function ToolsPanel() {
  const { callAction, sendUserMessage } = window.Chainlit || {}
  const {
    conversationContext = "",
    currentBot = "lawrence",
    expanded: initialExpanded = false,
  } = props || {}

  const [isExpanded, setIsExpanded] = useState(initialExpanded)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [hoveredTool, setHoveredTool] = useState(null)

  // Get contextual relevance for a tool
  const getRelevance = (tool) => {
    if (!conversationContext) return false
    const ctx = conversationContext.toLowerCase()
    return tool.contextTriggers?.some((trigger) => ctx.includes(trigger))
  }

  // Handle tool click
  const handleToolClick = (tool) => {
    if (callAction && tool.action) {
      callAction({ name: tool.action, payload: { tool_id: tool.id } })
    } else if (sendUserMessage) {
      sendUserMessage(`Help me use ${tool.name} for my current exploration`)
    }
  }

  // Sort tools by relevance
  const sortedTools = [...PWS_TOOLS].sort((a, b) => {
    const aRelevant = getRelevance(a)
    const bRelevant = getRelevance(b)
    if (aRelevant && !bRelevant) return -1
    if (!aRelevant && bRelevant) return 1
    return 0
  })

  if (!isExpanded) {
    // Collapsed state - just show the toggle button
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={() => setIsExpanded(true)}
          className="rounded-full w-12 h-12 shadow-lg bg-primary hover:bg-primary/90"
          title="Open PWS Tools"
        >
          <Wrench className="w-5 h-5" />
        </Button>
      </div>
    )
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="fixed bottom-4 right-4 z-50 w-72">
        <Card className="shadow-xl border-2 border-primary/20 bg-background/95 backdrop-blur-sm">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/50">
            <div className="flex items-center gap-2">
              <Wrench className="w-4 h-4 text-primary" />
              <span className="font-semibold text-sm">PWS Tools</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setIsExpanded(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <CardContent className="p-2 max-h-96 overflow-y-auto">
            {/* Main Tools Grid */}
            <div className="grid grid-cols-4 gap-1 mb-2">
              {sortedTools.map((tool) => {
                const Icon = tool.icon
                const isRelevant = getRelevance(tool)
                const contextHelp = tool.contextualHelp(conversationContext.toLowerCase())

                return (
                  <Tooltip key={tool.id}>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        className={`h-14 w-full flex flex-col items-center justify-center gap-1 p-1 relative ${
                          isRelevant ? "bg-primary/10 ring-1 ring-primary/30" : ""
                        }`}
                        onClick={() => handleToolClick(tool)}
                        onMouseEnter={() => setHoveredTool(tool.id)}
                        onMouseLeave={() => setHoveredTool(null)}
                      >
                        <Icon className={`w-5 h-5 ${tool.color}`} />
                        <span className="text-[10px] text-center leading-tight truncate w-full">
                          {tool.name.split(" ")[0]}
                        </span>
                        {isRelevant && (
                          <span className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left" className="max-w-xs">
                      <div className="space-y-1">
                        <p className="font-semibold">{tool.name}</p>
                        <p className="text-xs text-muted-foreground">{tool.shortDesc}</p>
                        <hr className="my-1" />
                        <p className="text-xs italic">{contextHelp}</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                )
              })}
            </div>

            {/* Advanced Tools Toggle */}
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs text-muted-foreground"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? <ChevronUp className="w-3 h-3 mr-1" /> : <ChevronDown className="w-3 h-3 mr-1" />}
              {showAdvanced ? "Hide" : "Show"} Advanced Pipelines
            </Button>

            {/* Advanced Tools */}
            {showAdvanced && (
              <div className="grid grid-cols-4 gap-1 mt-2 pt-2 border-t">
                {ADVANCED_TOOLS.map((tool) => {
                  const Icon = tool.icon
                  const contextHelp = tool.contextualHelp(conversationContext.toLowerCase())

                  return (
                    <Tooltip key={tool.id}>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          className="h-14 w-full flex flex-col items-center justify-center gap-1 p-1"
                          onClick={() => handleToolClick(tool)}
                        >
                          <Icon className={`w-5 h-5 ${tool.color}`} />
                          <span className="text-[10px] text-center leading-tight truncate w-full">
                            {tool.name.split(" ")[0]}
                          </span>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="left" className="max-w-xs">
                        <div className="space-y-1">
                          <p className="font-semibold">{tool.name}</p>
                          <p className="text-xs text-muted-foreground">{tool.shortDesc}</p>
                          <hr className="my-1" />
                          <p className="text-xs italic">{contextHelp}</p>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  )
                })}
              </div>
            )}

            {/* Context indicator */}
            {conversationContext && (
              <div className="mt-2 pt-2 border-t">
                <p className="text-[10px] text-muted-foreground text-center">
                  <Sparkles className="w-3 h-3 inline mr-1" />
                  Highlighted tools match your conversation
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  )
}
