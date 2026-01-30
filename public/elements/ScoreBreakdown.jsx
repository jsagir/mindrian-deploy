/**
 * ScoreBreakdown - Interactive Score Drill-Down Component
 *
 * Click any component to see detailed evidence and what's missing
 * "Discuss this score" button triggers Lawrence conversation
 *
 * Props (injected globally by Chainlit):
 * - components: array of {name, weight, score, assessment, evidence[], missing[]}
 * - selected: number (index of selected component, null for none)
 * - total_score: number
 * - grade: string
 * - element_id: string (for Chainlit updates)
 */

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { MessageCircle, ChevronRight, CheckCircle, AlertCircle, Info, ExternalLink } from 'lucide-react'

export default function ScoreBreakdown() {
  // === CHAINLIT API ACCESS ===
  // Props are injected globally by Chainlit (not as function arguments)
  // window.Chainlit provides: updateElement, callAction, sendUserMessage, deleteElement
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Destructure props with defaults (props is a global in Chainlit custom elements)
  const {
    components = [],
    selected = null,
    total_score = 0,
    grade = 'B',
    element_id = null
  } = props || {}

  // === HANDLERS ===

  // Select/deselect a component
  const handleSelectComponent = (index) => {
    if (updateElement) {
      updateElement({
        ...props,
        selected: selected === index ? null : index
      })
    } else {
      console.warn('Chainlit updateElement not available')
    }
  }

  // Discuss a specific component with Lawrence
  const handleDiscussComponent = (component) => {
    if (callAction) {
      callAction({
        name: 'discuss_component',
        payload: {
          component_name: component.name,
          score: component.score,
          weight: component.weight,
          assessment: component.assessment
        }
      })
    } else if (sendUserMessage) {
      sendUserMessage(
        `I'd like to discuss my ${component.name} score (${component.score}/10). ${component.assessment}`
      )
    }
  }

  // === SCORE RING COMPONENT ===
  // Visual ring showing score out of 10
  const ScoreRing = ({ score, max = 10, size = 48 }) => {
    const percentage = (score / max) * 100
    const color = percentage >= 70 ? '#22c55e' :
                  percentage >= 50 ? '#eab308' : '#ef4444'
    const circumference = 2 * Math.PI * 18
    const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`

    return (
      <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" viewBox="0 0 40 40">
          <circle
            cx="20" cy="20" r="18"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-muted"
          />
          <circle
            cx="20" cy="20" r="18"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-foreground">{score}</span>
        </div>
      </div>
    )
  }

  // === COMPONENT LIST ITEM ===
  const ComponentItem = ({ component, index, isSelected }) => (
    <button
      onClick={() => handleSelectComponent(index)}
      className={`w-full p-4 rounded-lg flex items-center justify-between transition-all duration-200 ${
        isSelected
          ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2'
          : 'bg-muted hover:bg-muted/80 hover:shadow-sm'
      }`}
    >
      <div className="flex items-center gap-3">
        <ScoreRing score={component.score} />
        <div className="text-left">
          <div className="font-medium">{component.name}</div>
          <div className={`text-xs ${isSelected ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
            {component.weight}% weight
          </div>
        </div>
      </div>
      <ChevronRight className={`h-5 w-5 transition-transform duration-200 ${isSelected ? 'rotate-90' : ''}`} />
    </button>
  )

  // === EVIDENCE TAG ===
  // Shows source type badge for evidence items
  const EvidenceTag = ({ source }) => {
    const sourceTypes = {
      'neo4j': { label: 'Graph', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' },
      'filesearch': { label: 'RAG', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
      'tavily': { label: 'Web', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
      'gemini': { label: 'AI', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300' }
    }

    const sourceKey = Object.keys(sourceTypes).find(k => source?.toLowerCase().includes(k))
    const config = sourceTypes[sourceKey] || { label: 'Source', color: 'bg-gray-100 text-gray-700' }

    return (
      <span className={`text-xs px-2 py-0.5 rounded-full ${config.color}`}>
        {config.label}
      </span>
    )
  }

  // === DETAIL PANEL ===
  // Shows full details for selected component
  const DetailPanel = ({ component }) => (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold text-foreground">{component.name}</h3>
          <p className="text-sm text-muted-foreground">{component.weight}% of total grade</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-foreground">{component.score}/10</div>
          <div className="text-sm text-muted-foreground">
            = {(component.score * component.weight / 10).toFixed(1)} points
          </div>
        </div>
      </div>

      {/* Assessment */}
      {component.assessment && (
        <p className="text-muted-foreground leading-relaxed">{component.assessment}</p>
      )}

      {/* Evidence Found */}
      {component.evidence && component.evidence.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400">
            <CheckCircle className="h-4 w-4" />
            Evidence Found ({component.evidence.length})
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {component.evidence.map((ev, i) => {
              const content = typeof ev === 'string' ? ev : ev.content || JSON.stringify(ev)
              const source = typeof ev === 'object' ? ev.source : null

              return (
                <div
                  key={i}
                  className="text-sm p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-100 dark:border-green-900"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-foreground">{content}</span>
                    {source && <EvidenceTag source={source} />}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* What's Missing */}
      {component.missing && component.missing.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-amber-600 dark:text-amber-400">
            <AlertCircle className="h-4 w-4" />
            What Would Raise This Score
          </div>
          <ul className="space-y-2">
            {component.missing.map((m, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-100 dark:border-amber-900"
              >
                <span className="text-amber-500 mt-0.5 flex-shrink-0">→</span>
                <span className="text-foreground">{m}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Discuss Button */}
      <Button
        className="w-full mt-4"
        onClick={() => handleDiscussComponent(component)}
      >
        <MessageCircle className="mr-2 h-4 w-4" />
        Discuss This Score with Lawrence
      </Button>
    </div>
  )

  // === EMPTY STATE ===
  const EmptyState = () => (
    <div className="h-full flex flex-col items-center justify-center text-center p-8 text-muted-foreground">
      <Info className="h-12 w-12 mb-4 opacity-50" />
      <p className="text-lg font-medium">Select a component</p>
      <p className="text-sm">
        Click any score on the left to see detailed evidence and improvement suggestions
      </p>
    </div>
  )

  // === RENDER ===
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
      {/* Component List */}
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
            Components
          </h4>
          <Badge variant="outline" className="font-mono">
            {grade} ({total_score})
          </Badge>
        </div>
        {components.length > 0 ? (
          components.map((c, i) => (
            <ComponentItem
              key={i}
              component={c}
              index={i}
              isSelected={selected === i}
            />
          ))
        ) : (
          <p className="text-sm text-muted-foreground italic p-4">
            No components to display
          </p>
        )}
      </div>

      {/* Detail Panel */}
      <div className="md:col-span-2">
        <Card className="h-full border">
          <CardContent className="p-6">
            {selected !== null && components[selected] ? (
              <DetailPanel component={components[selected]} />
            ) : (
              <EmptyState />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
