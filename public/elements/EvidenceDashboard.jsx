/**
 * EvidenceDashboard - Visualize collected evidence from multiple sources
 *
 * Displays evidence with source types, strength indicators, and filtering.
 * Integrates with Neo4j graph, RAG, web research, and user inputs.
 *
 * Props (injected globally by Chainlit):
 * - evidence: array of {text, source_type, strength, url, timestamp, tags, related_to}
 * - title: optional header text
 * - show_sources: boolean to show source breakdown
 * - filterable: boolean to enable source filtering
 * - group_by: 'source' | 'strength' | 'tag' | null
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Database, Globe, FileText, MessageSquare, User,
  BookOpen, Microscope, TrendingUp, Link2, ExternalLink,
  ChevronRight, Search, Filter, Sparkles, Shield,
  CheckCircle, AlertCircle, HelpCircle, BarChart3
} from "lucide-react"
import { useState } from "react"

export default function EvidenceDashboard() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    evidence = [],
    title = "Evidence Dashboard",
    show_sources = true,
    filterable = true,
    group_by = null,
    element_id = null
  } = props || {}

  // Local state
  const [activeFilter, setActiveFilter] = useState("all")
  const [expandedEvidence, setExpandedEvidence] = useState({})

  // === SOURCE CONFIGURATION ===
  const sourceConfig = {
    graph: {
      icon: <Database className="h-4 w-4" />,
      label: "Knowledge Graph",
      color: "text-purple-500",
      bgColor: "bg-purple-100 dark:bg-purple-900/30",
      description: "From Neo4j knowledge base"
    },
    rag: {
      icon: <BookOpen className="h-4 w-4" />,
      label: "RAG / Documents",
      color: "text-blue-500",
      bgColor: "bg-blue-100 dark:bg-blue-900/30",
      description: "Retrieved from document corpus"
    },
    web: {
      icon: <Globe className="h-4 w-4" />,
      label: "Web Research",
      color: "text-green-500",
      bgColor: "bg-green-100 dark:bg-green-900/30",
      description: "From web search (Tavily)"
    },
    user: {
      icon: <User className="h-4 w-4" />,
      label: "User Provided",
      color: "text-amber-500",
      bgColor: "bg-amber-100 dark:bg-amber-900/30",
      description: "Stated by user in conversation"
    },
    ai: {
      icon: <Sparkles className="h-4 w-4" />,
      label: "AI Analysis",
      color: "text-cyan-500",
      bgColor: "bg-cyan-100 dark:bg-cyan-900/30",
      description: "Inferred by AI assistant"
    },
    external: {
      icon: <ExternalLink className="h-4 w-4" />,
      label: "External Source",
      color: "text-gray-500",
      bgColor: "bg-gray-100 dark:bg-gray-800",
      description: "Linked external reference"
    }
  }

  // === STRENGTH CONFIGURATION ===
  const strengthConfig = {
    strong: {
      icon: <CheckCircle className="h-3 w-3" />,
      label: "Strong",
      color: "text-green-500",
      bar: "bg-green-500"
    },
    moderate: {
      icon: <AlertCircle className="h-3 w-3" />,
      label: "Moderate",
      color: "text-amber-500",
      bar: "bg-amber-500"
    },
    weak: {
      icon: <HelpCircle className="h-3 w-3" />,
      label: "Weak",
      color: "text-red-500",
      bar: "bg-red-500"
    }
  }

  // === STATS CALCULATION ===
  const calculateStats = () => {
    const stats = {
      total: evidence.length,
      bySource: {},
      byStrength: { strong: 0, moderate: 0, weak: 0 },
      avgStrength: 0
    }

    let strengthSum = 0
    evidence.forEach(e => {
      // By source
      const source = e.source_type || "external"
      stats.bySource[source] = (stats.bySource[source] || 0) + 1

      // By strength
      const strength = e.strength || "moderate"
      stats.byStrength[strength]++

      // For average
      const strengthValue = strength === "strong" ? 3 : strength === "moderate" ? 2 : 1
      strengthSum += strengthValue
    })

    stats.avgStrength = evidence.length > 0 ? (strengthSum / evidence.length / 3) * 100 : 0

    return stats
  }

  const stats = calculateStats()

  // === HANDLERS ===
  const handleFilter = (source) => {
    setActiveFilter(source)
  }

  const handleExpand = (index) => {
    setExpandedEvidence(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const handleExplore = (item) => {
    if (callAction) {
      callAction({
        name: "explore_evidence",
        payload: { evidence: item }
      })
    } else if (sendUserMessage) {
      sendUserMessage(`Tell me more about this evidence: "${item.text}"`)
    }
  }

  const handleValidate = (item) => {
    if (callAction) {
      callAction({
        name: "validate_evidence",
        payload: { evidence: item }
      })
    }
  }

  const handleOpenLink = (url) => {
    window.open(url, "_blank", "noopener,noreferrer")
  }

  // === FILTERING ===
  const filteredEvidence = activeFilter === "all"
    ? evidence
    : evidence.filter(e => (e.source_type || "external") === activeFilter)

  // === RENDER SOURCE BREAKDOWN ===
  const renderSourceBreakdown = () => {
    const sources = Object.entries(stats.bySource)
    if (sources.length === 0) return null

    return (
      <div className="grid grid-cols-3 gap-2 mb-4">
        {sources.map(([source, count]) => {
          const config = sourceConfig[source] || sourceConfig.external
          const percentage = Math.round((count / stats.total) * 100)

          return (
            <button
              key={source}
              onClick={() => filterable && handleFilter(source)}
              className={`p-2 rounded-lg border transition-all text-left ${
                activeFilter === source
                  ? `${config.bgColor} border-primary`
                  : "bg-muted/50 hover:bg-muted border-transparent"
              }`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span className={config.color}>{config.icon}</span>
                <span className="text-xs font-medium">{count}</span>
              </div>
              <div className="text-[10px] text-muted-foreground truncate">
                {config.label}
              </div>
            </button>
          )
        })}
      </div>
    )
  }

  // === RENDER STRENGTH METER ===
  const renderStrengthMeter = () => (
    <div className="mb-4 p-3 bg-muted/30 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium flex items-center gap-1">
          <BarChart3 className="h-3 w-3" />
          Evidence Strength
        </span>
        <span className="text-xs text-muted-foreground">
          {Math.round(stats.avgStrength)}% average
        </span>
      </div>
      <div className="flex gap-1 h-2">
        {stats.byStrength.strong > 0 && (
          <div
            className="bg-green-500 rounded-l"
            style={{ width: `${(stats.byStrength.strong / stats.total) * 100}%` }}
          />
        )}
        {stats.byStrength.moderate > 0 && (
          <div
            className="bg-amber-500"
            style={{ width: `${(stats.byStrength.moderate / stats.total) * 100}%` }}
          />
        )}
        {stats.byStrength.weak > 0 && (
          <div
            className="bg-red-500 rounded-r"
            style={{ width: `${(stats.byStrength.weak / stats.total) * 100}%` }}
          />
        )}
      </div>
      <div className="flex justify-between mt-1 text-[10px] text-muted-foreground">
        <span>Strong: {stats.byStrength.strong}</span>
        <span>Moderate: {stats.byStrength.moderate}</span>
        <span>Weak: {stats.byStrength.weak}</span>
      </div>
    </div>
  )

  // === RENDER SINGLE EVIDENCE ===
  const renderEvidence = (item, index) => {
    const source = item.source_type || "external"
    const strength = item.strength || "moderate"
    const sourceCfg = sourceConfig[source] || sourceConfig.external
    const strengthCfg = strengthConfig[strength] || strengthConfig.moderate
    const isExpanded = expandedEvidence[index]

    return (
      <div
        key={index}
        className={`p-3 rounded-lg border transition-all ${sourceCfg.bgColor} border-border/50`}
      >
        <div className="flex items-start gap-3">
          {/* Source Icon */}
          <div className={`mt-0.5 ${sourceCfg.color}`}>
            {sourceCfg.icon}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Badges Row */}
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <Badge variant="outline" className="text-xs">
                {sourceCfg.label}
              </Badge>
              <Badge variant="secondary" className={`text-xs flex items-center gap-1 ${strengthCfg.color}`}>
                {strengthCfg.icon}
                {strengthCfg.label}
              </Badge>
              {item.timestamp && (
                <span className="text-xs text-muted-foreground">
                  {item.timestamp}
                </span>
              )}
            </div>

            {/* Evidence Text */}
            <p className={`text-sm text-foreground leading-relaxed ${isExpanded ? "" : "line-clamp-2"}`}>
              {item.text}
            </p>

            {/* Tags */}
            {item.tags && item.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {item.tags.map((tag, i) => (
                  <Badge key={i} variant="secondary" className="text-[10px] px-1.5 py-0">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            {/* Related To */}
            {item.related_to && (
              <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
                <Link2 className="h-3 w-3" />
                Related: {item.related_to}
              </div>
            )}

            {/* URL */}
            {item.url && (
              <button
                onClick={() => handleOpenLink(item.url)}
                className="mt-2 text-xs text-primary hover:underline flex items-center gap-1"
              >
                <ExternalLink className="h-3 w-3" />
                View source
              </button>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-3">
              {item.text.length > 150 && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 text-xs px-2"
                  onClick={() => handleExpand(index)}
                >
                  {isExpanded ? "Show less" : "Show more"}
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                className="h-6 text-xs px-2"
                onClick={() => handleExplore(item)}
              >
                <Search className="h-3 w-3 mr-1" />
                Explore
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-6 text-xs px-2"
                onClick={() => handleValidate(item)}
              >
                <Shield className="h-3 w-3 mr-1" />
                Validate
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // === EMPTY STATE ===
  if (evidence.length === 0) {
    return (
      <Card className="w-full max-w-lg">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <Microscope className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No evidence collected yet.</p>
            <p className="text-xs mt-1">Evidence will be gathered from research and conversation.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // === RENDER ===
  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Microscope className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {stats.total} piece{stats.total !== 1 ? 's' : ''}
          </Badge>
        </div>
        <CardDescription>
          Evidence collected from multiple sources
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Source Breakdown */}
        {show_sources && renderSourceBreakdown()}

        {/* Strength Meter */}
        {renderStrengthMeter()}

        {/* Filter Reset */}
        {activeFilter !== "all" && (
          <div className="flex items-center justify-between mb-3">
            <Badge variant="secondary" className="flex items-center gap-1">
              <Filter className="h-3 w-3" />
              Showing: {sourceConfig[activeFilter]?.label || activeFilter}
            </Badge>
            <Button
              size="sm"
              variant="ghost"
              className="h-6 text-xs"
              onClick={() => setActiveFilter("all")}
            >
              Show all
            </Button>
          </div>
        )}

        {/* Evidence List */}
        <ScrollArea className="h-[400px] pr-2">
          <div className="space-y-3">
            {filteredEvidence.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No evidence from this source
              </div>
            ) : (
              filteredEvidence.map((item, index) =>
                renderEvidence(item, evidence.indexOf(item))
              )
            )}
          </div>
        </ScrollArea>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => callAction && callAction({ name: "research_more", payload: {} })}
        >
          <Search className="h-4 w-4 mr-1" />
          Find More Evidence
        </Button>
        <Button
          variant="outline"
          onClick={() => callAction && callAction({ name: "export_evidence", payload: { evidence } })}
        >
          <FileText className="h-4 w-4" />
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
    # Process message for evidence
    context.process_message(message.content, "user")

    # Get AI response...
    context.process_message(ai_response, "assistant")

    # Generate evidence dashboard props
    evidence_props = context.to_props("EvidenceDashboard")

    elements = [
        cl.CustomElement(
            name="EvidenceDashboard",
            props=evidence_props,
            display="inline"
        )
    ]
    await cl.Message(content="Evidence collected:", elements=elements).send()

# Or with manual props:
elements = [
    cl.CustomElement(
        name="EvidenceDashboard",
        props={
            "title": "Research Evidence",
            "show_sources": True,
            "filterable": True,
            "evidence": [
                {
                    "text": "Market size estimated at $5.2B with 15% CAGR through 2030",
                    "source_type": "web",
                    "strength": "strong",
                    "url": "https://example.com/report",
                    "timestamp": "2 min ago",
                    "tags": ["market size", "growth"],
                    "related_to": "Market Opportunity"
                },
                {
                    "text": "JTBD framework suggests customers hire products for progress",
                    "source_type": "graph",
                    "strength": "strong",
                    "related_to": "Customer Research"
                },
                {
                    "text": "Similar approach tried by Competitor X but failed due to timing",
                    "source_type": "rag",
                    "strength": "moderate",
                    "tags": ["competitor", "timing"]
                },
                {
                    "text": "We've seen 40% increase in customer complaints this quarter",
                    "source_type": "user",
                    "strength": "strong"
                }
            ]
        },
        display="inline"
    )
]

@cl.action_callback("explore_evidence")
async def handle_explore(action: cl.Action):
    evidence = action.payload.get("evidence")
    await cl.Message(content=f"Exploring: {evidence['text'][:100]}...").send()

@cl.action_callback("validate_evidence")
async def handle_validate(action: cl.Action):
    evidence = action.payload.get("evidence")
    await cl.Message(content=f"Validating evidence from {evidence.get('source_type', 'unknown')} source...").send()

@cl.action_callback("research_more")
async def handle_research(action: cl.Action):
    await cl.Message(content="Starting web research to find more evidence...").send()

================================================================================
*/
