/**
 * ResearchOrganizer - Organize and track research activities
 *
 * Manages research tasks by category, tracks progress, and identifies gaps.
 * Integrates with Tavily for web research automation.
 *
 * Props (injected globally by Chainlit):
 * - research_items: array of {id, title, description, category, status, findings, sources, priority}
 * - title: optional header text
 * - show_gaps: boolean to highlight research gaps
 * - categories: array of category definitions (or use defaults)
 * - editable: boolean to allow adding/editing items
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import {
  Search, FileSearch, Users, Building, Cpu, TrendingUp,
  CheckCircle2, Clock, AlertCircle, Plus, Play, Pause,
  ChevronDown, ChevronUp, ExternalLink, Sparkles, Target,
  BarChart, ArrowRight, RefreshCw, Lightbulb
} from "lucide-react"
import { useState } from "react"

export default function ResearchOrganizer() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    research_items = [],
    title = "Research Organizer",
    show_gaps = true,
    categories = null,
    editable = true,
    element_id = null
  } = props || {}

  // Local state
  const [activeCategory, setActiveCategory] = useState("all")
  const [expandedItems, setExpandedItems] = useState({})

  // === DEFAULT CATEGORIES ===
  const defaultCategories = {
    market: {
      id: "market",
      name: "Market Research",
      icon: <TrendingUp className="h-4 w-4" />,
      color: "text-green-500",
      bgColor: "bg-green-100 dark:bg-green-900/30",
      description: "Market size, trends, and dynamics"
    },
    customer: {
      id: "customer",
      name: "Customer Research",
      icon: <Users className="h-4 w-4" />,
      color: "text-blue-500",
      bgColor: "bg-blue-100 dark:bg-blue-900/30",
      description: "Jobs, pains, gains, and behaviors"
    },
    competitor: {
      id: "competitor",
      name: "Competitive Analysis",
      icon: <Building className="h-4 w-4" />,
      color: "text-amber-500",
      bgColor: "bg-amber-100 dark:bg-amber-900/30",
      description: "Competitor landscape and strategies"
    },
    technology: {
      id: "technology",
      name: "Technology Research",
      icon: <Cpu className="h-4 w-4" />,
      color: "text-purple-500",
      bgColor: "bg-purple-100 dark:bg-purple-900/30",
      description: "Technical feasibility and trends"
    },
    validation: {
      id: "validation",
      name: "Validation Research",
      icon: <Target className="h-4 w-4" />,
      color: "text-red-500",
      bgColor: "bg-red-100 dark:bg-red-900/30",
      description: "Testing assumptions and hypotheses"
    }
  }

  const categoryConfig = categories || defaultCategories

  // === STATUS CONFIGURATION ===
  const statusConfig = {
    planned: {
      icon: <Clock className="h-3 w-3" />,
      color: "text-gray-500",
      bgColor: "bg-gray-100 dark:bg-gray-800",
      label: "Planned"
    },
    in_progress: {
      icon: <RefreshCw className="h-3 w-3 animate-spin" />,
      color: "text-blue-500",
      bgColor: "bg-blue-100 dark:bg-blue-900/30",
      label: "In Progress"
    },
    completed: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      color: "text-green-500",
      bgColor: "bg-green-100 dark:bg-green-900/30",
      label: "Completed"
    },
    blocked: {
      icon: <AlertCircle className="h-3 w-3" />,
      color: "text-red-500",
      bgColor: "bg-red-100 dark:bg-red-900/30",
      label: "Blocked"
    }
  }

  // === STATS CALCULATION ===
  const calculateStats = () => {
    const stats = {
      total: research_items.length,
      byCategory: {},
      byStatus: { planned: 0, in_progress: 0, completed: 0, blocked: 0 },
      completionRate: 0,
      gaps: []
    }

    research_items.forEach(item => {
      const category = item.category || "market"
      stats.byCategory[category] = (stats.byCategory[category] || 0) + 1

      const status = item.status || "planned"
      stats.byStatus[status]++
    })

    // Completion rate
    stats.completionRate = stats.total > 0
      ? Math.round((stats.byStatus.completed / stats.total) * 100)
      : 0

    // Find gaps (categories with no research)
    Object.keys(categoryConfig).forEach(catId => {
      if (!stats.byCategory[catId]) {
        stats.gaps.push(catId)
      }
    })

    return stats
  }

  const stats = calculateStats()

  // === HANDLERS ===
  const handleStartResearch = (item) => {
    if (callAction) {
      callAction({
        name: "start_research",
        payload: { item }
      })
    } else if (sendUserMessage) {
      sendUserMessage(`Research this topic: ${item.title}`)
    }
  }

  const handleAddResearch = (categoryId = null) => {
    if (callAction) {
      callAction({
        name: "add_research",
        payload: { category: categoryId }
      })
    } else if (sendUserMessage) {
      const catName = categoryId ? categoryConfig[categoryId]?.name : "new research task"
      sendUserMessage(`Add a ${catName} item to track`)
    }
  }

  const handleViewFindings = (item) => {
    if (callAction) {
      callAction({
        name: "view_findings",
        payload: { item }
      })
    }
  }

  const handleFillGap = (categoryId) => {
    if (callAction) {
      callAction({
        name: "fill_research_gap",
        payload: { category: categoryId }
      })
    } else if (sendUserMessage) {
      const catName = categoryConfig[categoryId]?.name
      sendUserMessage(`What ${catName} should I conduct for this problem?`)
    }
  }

  const toggleExpand = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }))
  }

  // === FILTERING ===
  const filteredItems = activeCategory === "all"
    ? research_items
    : research_items.filter(item => item.category === activeCategory)

  // === RENDER PROGRESS OVERVIEW ===
  const renderProgressOverview = () => (
    <div className="mb-4 p-3 bg-muted/30 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium flex items-center gap-1">
          <BarChart className="h-3 w-3" />
          Research Progress
        </span>
        <span className="text-xs text-muted-foreground">
          {stats.completionRate}% complete
        </span>
      </div>
      <Progress value={stats.completionRate} className="h-2" />
      <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
        <span>Planned: {stats.byStatus.planned}</span>
        <span>In Progress: {stats.byStatus.in_progress}</span>
        <span>Completed: {stats.byStatus.completed}</span>
        {stats.byStatus.blocked > 0 && <span className="text-red-500">Blocked: {stats.byStatus.blocked}</span>}
      </div>
    </div>
  )

  // === RENDER GAPS ALERT ===
  const renderGapsAlert = () => {
    if (!show_gaps || stats.gaps.length === 0) return null

    return (
      <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
        <div className="flex items-start gap-2">
          <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-700 dark:text-amber-400">
              Research Gaps Detected
            </p>
            <p className="text-xs text-amber-600 dark:text-amber-500 mt-1">
              No research planned for: {stats.gaps.map(g => categoryConfig[g]?.name).join(", ")}
            </p>
            <div className="flex flex-wrap gap-1 mt-2">
              {stats.gaps.map(gapId => (
                <Button
                  key={gapId}
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs border-amber-300"
                  onClick={() => handleFillGap(gapId)}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add {categoryConfig[gapId]?.name}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // === RENDER SINGLE RESEARCH ITEM ===
  const renderResearchItem = (item) => {
    const category = item.category || "market"
    const status = item.status || "planned"
    const catConfig = categoryConfig[category] || categoryConfig.market
    const statConfig = statusConfig[status] || statusConfig.planned
    const isExpanded = expandedItems[item.id]
    const hasFindings = item.findings && item.findings.length > 0

    return (
      <div
        key={item.id}
        className={`p-3 rounded-lg border transition-all ${catConfig.bgColor} border-border/50`}
      >
        <div className="flex items-start gap-3">
          {/* Category Icon */}
          <div className={`mt-0.5 ${catConfig.color}`}>
            {catConfig.icon}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center justify-between gap-2 mb-1">
              <h4 className="text-sm font-medium text-foreground">
                {item.title}
              </h4>
              <Badge variant="secondary" className={`text-xs flex items-center gap-1 ${statConfig.color}`}>
                {statConfig.icon}
                {statConfig.label}
              </Badge>
            </div>

            {/* Description */}
            {item.description && (
              <p className="text-xs text-muted-foreground mb-2">
                {item.description}
              </p>
            )}

            {/* Priority */}
            {item.priority && (
              <Badge variant="outline" className="text-xs mb-2">
                {item.priority} priority
              </Badge>
            )}

            {/* Findings Preview */}
            {hasFindings && (
              <Collapsible open={isExpanded} onOpenChange={() => toggleExpand(item.id)}>
                <CollapsibleTrigger asChild>
                  <button className="flex items-center gap-1 text-xs text-primary hover:underline">
                    <FileSearch className="h-3 w-3" />
                    {item.findings.length} finding{item.findings.length !== 1 ? 's' : ''}
                    {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="mt-2 space-y-1">
                    {item.findings.slice(0, 3).map((finding, i) => (
                      <div key={i} className="text-xs text-muted-foreground pl-2 border-l-2 border-primary/30">
                        {finding}
                      </div>
                    ))}
                    {item.findings.length > 3 && (
                      <button
                        className="text-xs text-primary hover:underline"
                        onClick={() => handleViewFindings(item)}
                      >
                        +{item.findings.length - 3} more findings
                      </button>
                    )}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )}

            {/* Sources */}
            {item.sources && item.sources.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {item.sources.slice(0, 3).map((source, i) => (
                  <Badge key={i} variant="outline" className="text-[10px] px-1.5 py-0">
                    {source.name || source}
                  </Badge>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-3">
              {status === "planned" && (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs"
                  onClick={() => handleStartResearch(item)}
                >
                  <Play className="h-3 w-3 mr-1" />
                  Start Research
                </Button>
              )}
              {status === "in_progress" && (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs"
                  onClick={() => handleStartResearch(item)}
                >
                  <Sparkles className="h-3 w-3 mr-1" />
                  Continue
                </Button>
              )}
              {hasFindings && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 text-xs"
                  onClick={() => handleViewFindings(item)}
                >
                  <ArrowRight className="h-3 w-3 mr-1" />
                  View Details
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // === EMPTY STATE ===
  if (research_items.length === 0) {
    return (
      <Card className="w-full max-w-lg">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No research items tracked yet.</p>
            <p className="text-xs mt-1">Add research tasks to organize your investigation.</p>
            {editable && (
              <Button
                size="sm"
                variant="outline"
                className="mt-4"
                onClick={() => handleAddResearch()}
              >
                <Plus className="h-3 w-3 mr-1" />
                Add Research Task
              </Button>
            )}
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
            <Search className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {stats.total} task{stats.total !== 1 ? 's' : ''}
          </Badge>
        </div>
        <CardDescription>
          Organize and track research activities
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Progress Overview */}
        {renderProgressOverview()}

        {/* Gaps Alert */}
        {renderGapsAlert()}

        {/* Category Tabs */}
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="w-full flex-wrap h-auto gap-1 mb-4">
            <TabsTrigger value="all" className="text-xs">
              All ({stats.total})
            </TabsTrigger>
            {Object.entries(categoryConfig).map(([id, cat]) => (
              <TabsTrigger key={id} value={id} className="text-xs">
                {cat.icon}
                <span className="ml-1 hidden sm:inline">{stats.byCategory[id] || 0}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <ScrollArea className="h-[350px]">
            <div className="space-y-3 pr-2">
              {filteredItems.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No research in this category
                </div>
              ) : (
                filteredItems.map(item => renderResearchItem(item))
              )}
            </div>
          </ScrollArea>
        </Tabs>
      </CardContent>

      <CardFooter className="flex gap-2">
        {editable && (
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => handleAddResearch(activeCategory !== "all" ? activeCategory : null)}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Research
          </Button>
        )}
        <Button
          variant="outline"
          onClick={() => callAction && callAction({ name: "auto_research", payload: {} })}
        >
          <Sparkles className="h-4 w-4 mr-1" />
          Auto-Research
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
            name="ResearchOrganizer",
            props={
                "title": "Problem Research",
                "show_gaps": True,
                "editable": True,
                "research_items": [
                    {
                        "id": "r1",
                        "title": "Market Size Analysis",
                        "description": "Estimate TAM, SAM, SOM for the solution",
                        "category": "market",
                        "status": "completed",
                        "priority": "high",
                        "findings": [
                            "TAM estimated at $50B globally",
                            "SAM is $12B in target regions",
                            "Growing at 15% CAGR"
                        ],
                        "sources": [{"name": "Gartner"}, {"name": "IDC"}]
                    },
                    {
                        "id": "r2",
                        "title": "Customer Interviews",
                        "description": "Interview 10 potential customers",
                        "category": "customer",
                        "status": "in_progress",
                        "priority": "high",
                        "findings": [
                            "7/10 interviews completed",
                            "Pain point: manual data entry"
                        ]
                    },
                    {
                        "id": "r3",
                        "title": "Competitor Feature Matrix",
                        "description": "Map competitor features and pricing",
                        "category": "competitor",
                        "status": "planned",
                        "priority": "medium"
                    },
                    {
                        "id": "r4",
                        "title": "API Feasibility Study",
                        "description": "Evaluate technical integration options",
                        "category": "technology",
                        "status": "planned",
                        "priority": "low"
                    }
                ]
            },
            display="inline"
        )
    ]
    await cl.Message(content="Research tracker:", elements=elements).send()

@cl.action_callback("start_research")
async def handle_start(action: cl.Action):
    item = action.payload.get("item")
    await cl.Message(content=f"Starting research: {item['title']}...").send()
    # Call Tavily or other research tools

@cl.action_callback("add_research")
async def handle_add(action: cl.Action):
    category = action.payload.get("category")
    await cl.Message(content=f"What research would you like to add?").send()

@cl.action_callback("auto_research")
async def handle_auto(action: cl.Action):
    await cl.Message(content="Automatically researching based on your problem...").send()

================================================================================
*/
