/**
 * DecisionMatrix - Interactive decision-making matrix
 *
 * Displays options vs criteria with weighted scoring, helping users
 * make structured decisions based on PWS methodology.
 *
 * Props (injected globally by Chainlit):
 * - title: optional header text
 * - options: array of {id, name, description}
 * - criteria: array of {id, name, weight, description}
 * - scores: object {optionId: {criterionId: score}} (1-5 scale)
 * - editable: boolean to allow editing weights/scores
 * - highlight_winner: boolean to highlight best option
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Scale, Trophy, TrendingUp, Edit3, Check, X,
  Plus, Trash2, Info, Download, RefreshCw, Sparkles,
  ChevronUp, ChevronDown, BarChart
} from "lucide-react"
import { useState, useMemo } from "react"

export default function DecisionMatrix() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    title = "Decision Matrix",
    options = [],
    criteria = [],
    scores = {},
    editable = true,
    highlight_winner = true,
    element_id = null
  } = props || {}

  // Local state
  const [editingScore, setEditingScore] = useState(null) // {optionId, criterionId}
  const [editingWeight, setEditingWeight] = useState(null) // criterionId
  const [localScores, setLocalScores] = useState(scores)
  const [localCriteria, setLocalCriteria] = useState(criteria)

  // === CALCULATIONS ===
  const calculations = useMemo(() => {
    const results = {}
    let maxScore = 0
    let winnerId = null

    options.forEach(option => {
      let totalWeightedScore = 0
      let totalWeight = 0

      localCriteria.forEach(criterion => {
        const score = localScores[option.id]?.[criterion.id] || 0
        const weight = criterion.weight || 1
        totalWeightedScore += score * weight
        totalWeight += weight
      })

      const normalizedScore = totalWeight > 0
        ? (totalWeightedScore / (totalWeight * 5)) * 100 // 5 is max score
        : 0

      results[option.id] = {
        totalWeightedScore,
        normalizedScore: Math.round(normalizedScore),
        rank: 0
      }

      if (normalizedScore > maxScore) {
        maxScore = normalizedScore
        winnerId = option.id
      }
    })

    // Calculate ranks
    const sorted = Object.entries(results)
      .sort(([, a], [, b]) => b.normalizedScore - a.normalizedScore)

    sorted.forEach(([id], index) => {
      results[id].rank = index + 1
    })

    return { results, winnerId }
  }, [options, localCriteria, localScores])

  // === HANDLERS ===
  const handleScoreChange = (optionId, criterionId, newScore) => {
    const updated = {
      ...localScores,
      [optionId]: {
        ...localScores[optionId],
        [criterionId]: newScore
      }
    }
    setLocalScores(updated)

    if (updateElement) {
      updateElement({ ...props, scores: updated })
    }
  }

  const handleWeightChange = (criterionId, newWeight) => {
    const updated = localCriteria.map(c =>
      c.id === criterionId ? { ...c, weight: newWeight } : c
    )
    setLocalCriteria(updated)

    if (updateElement) {
      updateElement({ ...props, criteria: updated })
    }
  }

  const handleAddCriterion = () => {
    if (callAction) {
      callAction({ name: "add_criterion", payload: {} })
    } else if (sendUserMessage) {
      sendUserMessage("Add a new criterion to the decision matrix")
    }
  }

  const handleAddOption = () => {
    if (callAction) {
      callAction({ name: "add_option", payload: {} })
    } else if (sendUserMessage) {
      sendUserMessage("Add a new option to the decision matrix")
    }
  }

  const handleAnalyze = () => {
    if (callAction) {
      callAction({
        name: "analyze_decision",
        payload: {
          options,
          criteria: localCriteria,
          scores: localScores,
          results: calculations.results
        }
      })
    }
  }

  const handleExport = () => {
    if (callAction) {
      callAction({
        name: "export_matrix",
        payload: {
          title,
          options,
          criteria: localCriteria,
          scores: localScores,
          results: calculations.results
        }
      })
    }
  }

  // === SCORE CELL RENDERER ===
  const renderScoreCell = (option, criterion) => {
    const score = localScores[option.id]?.[criterion.id] || 0
    const isEditing = editingScore?.optionId === option.id && editingScore?.criterionId === criterion.id

    // Color based on score
    const getScoreColor = (s) => {
      if (s >= 4) return "bg-green-500"
      if (s >= 3) return "bg-amber-500"
      if (s >= 2) return "bg-orange-500"
      if (s >= 1) return "bg-red-500"
      return "bg-gray-300"
    }

    if (isEditing && editable) {
      return (
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4, 5].map(s => (
            <button
              key={s}
              onClick={() => {
                handleScoreChange(option.id, criterion.id, s)
                setEditingScore(null)
              }}
              className={`w-6 h-6 rounded text-xs font-medium transition-all ${
                s === score
                  ? `${getScoreColor(s)} text-white`
                  : "bg-muted hover:bg-muted/80"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      )
    }

    return (
      <button
        onClick={() => editable && setEditingScore({ optionId: option.id, criterionId: criterion.id })}
        className={`w-8 h-8 rounded-lg ${getScoreColor(score)} text-white font-medium text-sm flex items-center justify-center transition-all ${
          editable ? "hover:ring-2 hover:ring-primary cursor-pointer" : ""
        }`}
      >
        {score || "-"}
      </button>
    )
  }

  // === WEIGHT CELL RENDERER ===
  const renderWeightCell = (criterion) => {
    const weight = criterion.weight || 1
    const isEditing = editingWeight === criterion.id

    if (isEditing && editable) {
      return (
        <div className="flex items-center gap-2 min-w-[120px]">
          <Slider
            value={[weight]}
            min={1}
            max={5}
            step={1}
            onValueChange={([v]) => handleWeightChange(criterion.id, v)}
            className="flex-1"
          />
          <span className="text-xs w-4">{weight}</span>
          <button
            onClick={() => setEditingWeight(null)}
            className="text-primary"
          >
            <Check className="h-3 w-3" />
          </button>
        </div>
      )
    }

    return (
      <button
        onClick={() => editable && setEditingWeight(criterion.id)}
        className={`flex items-center gap-1 ${editable ? "cursor-pointer hover:text-primary" : ""}`}
      >
        <span className="text-xs text-muted-foreground">×{weight}</span>
        {editable && <Edit3 className="h-2.5 w-2.5 text-muted-foreground" />}
      </button>
    )
  }

  // === EMPTY STATE ===
  if (options.length === 0 || criteria.length === 0) {
    return (
      <Card className="w-full max-w-2xl">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <Scale className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Decision matrix needs options and criteria.</p>
            <div className="flex gap-2 justify-center mt-4">
              <Button size="sm" variant="outline" onClick={handleAddOption}>
                <Plus className="h-3 w-3 mr-1" /> Add Option
              </Button>
              <Button size="sm" variant="outline" onClick={handleAddCriterion}>
                <Plus className="h-3 w-3 mr-1" /> Add Criterion
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // === RENDER ===
  return (
    <Card className="w-full max-w-3xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Scale className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {options.length} options × {criteria.length} criteria
            </Badge>
          </div>
        </div>
        <CardDescription>
          Score each option (1-5) against weighted criteria
        </CardDescription>
      </CardHeader>

      <CardContent>
        <ScrollArea className="w-full">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">Option</TableHead>
                {localCriteria.map(criterion => (
                  <TableHead key={criterion.id} className="text-center min-w-[100px]">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex flex-col items-center gap-1">
                            <span className="text-xs font-medium">{criterion.name}</span>
                            {renderWeightCell(criterion)}
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="text-xs">{criterion.description || criterion.name}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </TableHead>
                ))}
                <TableHead className="text-center w-[100px]">Score</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {options.map(option => {
                const result = calculations.results[option.id]
                const isWinner = highlight_winner && calculations.winnerId === option.id

                return (
                  <TableRow
                    key={option.id}
                    className={isWinner ? "bg-green-50 dark:bg-green-950/30" : ""}
                  >
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {isWinner && (
                          <Trophy className="h-4 w-4 text-amber-500" />
                        )}
                        <div>
                          <div className="text-sm">{option.name}</div>
                          {option.description && (
                            <div className="text-xs text-muted-foreground">
                              {option.description}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>

                    {localCriteria.map(criterion => (
                      <TableCell key={criterion.id} className="text-center">
                        {renderScoreCell(option, criterion)}
                      </TableCell>
                    ))}

                    <TableCell className="text-center">
                      <div className="flex flex-col items-center gap-1">
                        <div className={`text-lg font-bold ${
                          isWinner ? "text-green-600" : "text-foreground"
                        }`}>
                          {result.normalizedScore}%
                        </div>
                        <Badge variant="secondary" className="text-[10px]">
                          #{result.rank}
                        </Badge>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </ScrollArea>

        {/* Winner Summary */}
        {highlight_winner && calculations.winnerId && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-500" />
              <div>
                <span className="font-medium text-green-700 dark:text-green-400">
                  Recommended:{" "}
                </span>
                <span className="text-foreground">
                  {options.find(o => o.id === calculations.winnerId)?.name}
                </span>
                <span className="text-sm text-muted-foreground ml-2">
                  ({calculations.results[calculations.winnerId].normalizedScore}% score)
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
          <span className="font-medium">Score Legend:</span>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-500 rounded" />
            <span>1-2 Poor</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-amber-500 rounded" />
            <span>3 Fair</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-green-500 rounded" />
            <span>4-5 Good</span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        {editable && (
          <>
            <Button size="sm" variant="outline" onClick={handleAddOption}>
              <Plus className="h-3 w-3 mr-1" /> Option
            </Button>
            <Button size="sm" variant="outline" onClick={handleAddCriterion}>
              <Plus className="h-3 w-3 mr-1" /> Criterion
            </Button>
          </>
        )}
        <div className="flex-1" />
        <Button size="sm" variant="outline" onClick={handleAnalyze}>
          <Sparkles className="h-3 w-3 mr-1" /> Analyze
        </Button>
        <Button size="sm" variant="outline" onClick={handleExport}>
          <Download className="h-3 w-3 mr-1" /> Export
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
            name="DecisionMatrix",
            props={
                "title": "Platform Decision",
                "editable": True,
                "highlight_winner": True,
                "options": [
                    {"id": "opt1", "name": "Build In-House", "description": "Custom development"},
                    {"id": "opt2", "name": "Buy SaaS", "description": "Subscribe to existing"},
                    {"id": "opt3", "name": "Partner", "description": "White-label solution"}
                ],
                "criteria": [
                    {"id": "cost", "name": "Cost", "weight": 4, "description": "Total cost of ownership"},
                    {"id": "time", "name": "Time to Market", "weight": 5, "description": "Speed of implementation"},
                    {"id": "control", "name": "Control", "weight": 3, "description": "Customization ability"},
                    {"id": "risk", "name": "Risk", "weight": 4, "description": "Implementation risk"},
                    {"id": "scale", "name": "Scalability", "weight": 3, "description": "Growth potential"}
                ],
                "scores": {
                    "opt1": {"cost": 2, "time": 2, "control": 5, "risk": 3, "scale": 4},
                    "opt2": {"cost": 4, "time": 5, "control": 2, "risk": 4, "scale": 3},
                    "opt3": {"cost": 3, "time": 4, "control": 3, "risk": 3, "scale": 4}
                }
            },
            display="inline"
        )
    ]
    await cl.Message(content="Decision matrix:", elements=elements).send()

@cl.action_callback("analyze_decision")
async def handle_analyze(action: cl.Action):
    results = action.payload.get("results")
    options = action.payload.get("options")
    winner_id = max(results, key=lambda x: results[x]["normalizedScore"])
    winner = next(o for o in options if o["id"] == winner_id)
    await cl.Message(
        content=f"Analysis: '{winner['name']}' scores highest at {results[winner_id]['normalizedScore']}%"
    ).send()

@cl.action_callback("add_option")
async def handle_add_option(action: cl.Action):
    await cl.Message(content="What option would you like to add?").send()

@cl.action_callback("add_criterion")
async def handle_add_criterion(action: cl.Action):
    await cl.Message(content="What criterion should we evaluate options against?").send()

================================================================================
*/
