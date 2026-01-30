/**
 * ProblemCanvas - Visual problem definition canvas
 *
 * A structured canvas for defining problems with multiple sections,
 * similar to Business Model Canvas style but focused on PWS methodology.
 *
 * Props (injected globally by Chainlit):
 * - title: optional canvas title
 * - sections: object with section data {problem, who, why, impact, solutions, constraints}
 * - editable: boolean to allow editing sections
 * - completeness: object with section completion status
 * - show_completeness: boolean to show progress indicator
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  AlertTriangle, Users, HelpCircle, TrendingUp, Lightbulb,
  Lock, Edit3, Check, X, Download, Share2, Plus, Trash2,
  Target, Sparkles, ChevronRight, RefreshCw
} from "lucide-react"
import { useState } from "react"

export default function ProblemCanvas() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    title = "Problem Definition Canvas",
    sections = {},
    editable = true,
    completeness = {},
    show_completeness = true,
    element_id = null
  } = props || {}

  // Local state
  const [editingSection, setEditingSection] = useState(null)
  const [editValue, setEditValue] = useState("")
  const [localSections, setLocalSections] = useState(sections)

  // === SECTION CONFIGURATION ===
  const sectionConfig = {
    problem: {
      id: "problem",
      name: "Problem Statement",
      icon: <AlertTriangle className="h-4 w-4" />,
      color: "text-red-500",
      bgColor: "bg-red-50 dark:bg-red-950/30",
      borderColor: "border-red-200 dark:border-red-800",
      placeholder: "What is the core problem you're trying to solve?",
      prompt: "Help me articulate the core problem",
      gridArea: "problem"
    },
    who: {
      id: "who",
      name: "Who Has This Problem",
      icon: <Users className="h-4 w-4" />,
      color: "text-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-950/30",
      borderColor: "border-blue-200 dark:border-blue-800",
      placeholder: "Who experiences this problem? Be specific about the persona.",
      prompt: "Help me identify who has this problem",
      gridArea: "who"
    },
    why: {
      id: "why",
      name: "Why It Matters",
      icon: <HelpCircle className="h-4 w-4" />,
      color: "text-purple-500",
      bgColor: "bg-purple-50 dark:bg-purple-950/30",
      borderColor: "border-purple-200 dark:border-purple-800",
      placeholder: "Why is this problem worth solving? What's at stake?",
      prompt: "Help me understand why this problem matters",
      gridArea: "why"
    },
    impact: {
      id: "impact",
      name: "Impact If Solved",
      icon: <TrendingUp className="h-4 w-4" />,
      color: "text-green-500",
      bgColor: "bg-green-50 dark:bg-green-950/30",
      borderColor: "border-green-200 dark:border-green-800",
      placeholder: "What changes if this problem is solved? Quantify if possible.",
      prompt: "Help me define the impact of solving this",
      gridArea: "impact"
    },
    solutions: {
      id: "solutions",
      name: "Current Solutions",
      icon: <Lightbulb className="h-4 w-4" />,
      color: "text-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-950/30",
      borderColor: "border-amber-200 dark:border-amber-800",
      placeholder: "How do people currently try to solve this? What's being hired?",
      prompt: "Help me map existing solutions",
      gridArea: "solutions"
    },
    constraints: {
      id: "constraints",
      name: "Constraints & Risks",
      icon: <Lock className="h-4 w-4" />,
      color: "text-gray-500",
      bgColor: "bg-gray-50 dark:bg-gray-800/30",
      borderColor: "border-gray-200 dark:border-gray-700",
      placeholder: "What constraints exist? Technical, regulatory, market, or resource limits?",
      prompt: "Help me identify constraints",
      gridArea: "constraints"
    }
  }

  const sectionOrder = ["problem", "who", "why", "impact", "solutions", "constraints"]

  // === CALCULATE COMPLETENESS ===
  const calculateCompleteness = () => {
    let filled = 0
    let total = sectionOrder.length

    sectionOrder.forEach(sectionId => {
      const content = localSections[sectionId]
      if (content && content.trim().length > 20) {
        filled++
      }
    })

    return {
      percent: Math.round((filled / total) * 100),
      filled,
      total
    }
  }

  const progress = calculateCompleteness()

  // === HANDLERS ===
  const handleEdit = (sectionId) => {
    setEditingSection(sectionId)
    setEditValue(localSections[sectionId] || "")
  }

  const handleSave = () => {
    if (!editingSection) return

    const updated = {
      ...localSections,
      [editingSection]: editValue
    }
    setLocalSections(updated)

    if (updateElement) {
      updateElement({ ...props, sections: updated })
    }

    if (callAction) {
      callAction({
        name: "canvas_section_updated",
        payload: { section: editingSection, content: editValue }
      })
    }

    setEditingSection(null)
    setEditValue("")
  }

  const handleCancel = () => {
    setEditingSection(null)
    setEditValue("")
  }

  const handleAskHelp = (sectionId) => {
    const config = sectionConfig[sectionId]
    if (sendUserMessage) {
      sendUserMessage(config.prompt)
    }
  }

  const handleExport = () => {
    if (callAction) {
      callAction({
        name: "export_canvas",
        payload: { title, sections: localSections }
      })
    }
  }

  const handleShare = () => {
    if (callAction) {
      callAction({
        name: "share_canvas",
        payload: { title, sections: localSections }
      })
    }
  }

  const handleRefine = () => {
    if (callAction) {
      callAction({
        name: "refine_canvas",
        payload: { sections: localSections }
      })
    } else if (sendUserMessage) {
      sendUserMessage("Help me refine this problem canvas and identify gaps")
    }
  }

  // === RENDER SECTION ===
  const renderSection = (sectionId) => {
    const config = sectionConfig[sectionId]
    const content = localSections[sectionId]
    const isEditing = editingSection === sectionId
    const hasContent = content && content.trim().length > 0

    return (
      <div
        key={sectionId}
        className={`p-3 rounded-lg border transition-all ${config.bgColor} ${config.borderColor}`}
        style={{ gridArea: config.gridArea }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className={config.color}>{config.icon}</div>
            <span className="text-sm font-medium">{config.name}</span>
          </div>
          <div className="flex items-center gap-1">
            {hasContent && !isEditing && (
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                <Check className="h-2 w-2 mr-0.5" />
              </Badge>
            )}
            {editable && !isEditing && (
              <Button
                size="icon"
                variant="ghost"
                className="h-6 w-6"
                onClick={() => handleEdit(sectionId)}
              >
                <Edit3 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        {/* Content */}
        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              placeholder={config.placeholder}
              className="min-h-[80px] text-sm resize-none"
              autoFocus
            />
            <div className="flex items-center gap-2">
              <Button size="sm" className="h-7 text-xs" onClick={handleSave}>
                <Check className="h-3 w-3 mr-1" />
                Save
              </Button>
              <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={handleCancel}>
                <X className="h-3 w-3 mr-1" />
                Cancel
              </Button>
            </div>
          </div>
        ) : hasContent ? (
          <div className="text-sm text-foreground leading-relaxed">
            {content}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground italic">
            {config.placeholder}
            {editable && (
              <button
                onClick={() => handleAskHelp(sectionId)}
                className="block mt-2 text-xs text-primary hover:underline"
              >
                <Sparkles className="h-3 w-3 inline mr-1" />
                Get AI help
              </button>
            )}
          </div>
        )}
      </div>
    )
  }

  // === RENDER ===
  return (
    <Card className="w-full max-w-4xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Target className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-2">
            {show_completeness && (
              <Badge variant="outline" className="text-xs">
                {progress.filled}/{progress.total} sections
              </Badge>
            )}
          </div>
        </div>
        <CardDescription>
          Define your problem systematically using this canvas
        </CardDescription>

        {/* Completeness Progress */}
        {show_completeness && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Canvas Completeness</span>
              <span className="text-xs font-medium">{progress.percent}%</span>
            </div>
            <Progress value={progress.percent} className="h-1.5" />
          </div>
        )}
      </CardHeader>

      <CardContent>
        {/* Canvas Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {/* Row 1: Problem spans 2 columns */}
          <div className="md:col-span-2 lg:col-span-2">
            {renderSection("problem")}
          </div>
          <div className="md:col-span-1">
            {renderSection("who")}
          </div>

          {/* Row 2 */}
          <div>{renderSection("why")}</div>
          <div>{renderSection("impact")}</div>
          <div>{renderSection("solutions")}</div>

          {/* Row 3: Constraints spans full width on mobile */}
          <div className="md:col-span-2 lg:col-span-3">
            {renderSection("constraints")}
          </div>
        </div>

        {/* Quick Insights */}
        {progress.percent >= 50 && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-start gap-2">
              <Lightbulb className="h-4 w-4 text-green-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-green-700 dark:text-green-400">
                  Canvas {progress.percent >= 80 ? "Nearly Complete!" : "Taking Shape"}
                </p>
                <p className="text-xs text-green-600 dark:text-green-500 mt-1">
                  {progress.percent >= 80
                    ? "Consider refining your problem statement or validating assumptions."
                    : `Complete ${progress.total - progress.filled} more section${progress.total - progress.filled !== 1 ? 's' : ''} to fully define your problem.`
                  }
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button
          variant="outline"
          className="flex-1"
          onClick={handleRefine}
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Refine with AI
        </Button>
        <Button variant="outline" onClick={handleExport}>
          <Download className="h-4 w-4" />
        </Button>
        <Button variant="outline" onClick={handleShare}>
          <Share2 className="h-4 w-4" />
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
from utils.context_extraction import ConversationContext

# Initialize context tracker
context = ConversationContext()

@cl.on_message
async def main(message: cl.Message):
    # Process message for canvas content
    context.process_message(message.content, "user")

    # Generate canvas props
    canvas_props = context.to_props("ProblemCanvas")

    elements = [
        cl.CustomElement(
            name="ProblemCanvas",
            props=canvas_props,
            display="inline"
        )
    ]
    await cl.Message(content="Your problem canvas:", elements=elements).send()

# Or with manual props:
elements = [
    cl.CustomElement(
        name="ProblemCanvas",
        props={
            "title": "Customer Onboarding Problem",
            "editable": True,
            "show_completeness": True,
            "sections": {
                "problem": "Enterprise customers take 90+ days to fully onboard, causing churn risk and delayed time-to-value",
                "who": "IT administrators and business champions at enterprise companies (500+ employees) who are responsible for implementing new SaaS tools",
                "why": "Long onboarding creates frustration, increases churn risk in first 6 months, and delays the ROI that justified the purchase",
                "impact": "Reducing onboarding from 90 to 30 days could improve retention by 25% and increase NRR by $2M annually",
                "solutions": "Current: Manual implementation consultants, self-serve docs, and weekly check-in calls. Competitors offer white-glove service at 2x price.",
                "constraints": "Limited implementation team capacity, complex integrations vary by customer, compliance requirements in regulated industries"
            }
        },
        display="inline"
    )
]

@cl.action_callback("canvas_section_updated")
async def handle_update(action: cl.Action):
    section = action.payload.get("section")
    content = action.payload.get("content")
    await cl.Message(content=f"Updated {section} section!").send()

@cl.action_callback("refine_canvas")
async def handle_refine(action: cl.Action):
    sections = action.payload.get("sections")
    await cl.Message(content="Let me help you refine this problem definition...").send()

@cl.action_callback("export_canvas")
async def handle_export(action: cl.Action):
    # Generate markdown export
    sections = action.payload.get("sections")
    title = action.payload.get("title")
    md = f"# {title}\\n\\n"
    for key, value in sections.items():
        md += f"## {key.title()}\\n{value}\\n\\n"
    await cl.Message(content=f"```markdown\\n{md}```").send()

================================================================================
*/
