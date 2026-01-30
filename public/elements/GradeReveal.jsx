/**
 * GradeReveal - Soft Landing Grade Reveal Component
 *
 * Staged emotional reveal: context → strengths → growth → grade
 * Prevents grade shock, improves reception of feedback
 *
 * Props (injected globally by Chainlit):
 * - stage: 'context' | 'strengths' | 'growth' | 'reveal' | 'expanded'
 * - grade: string (e.g., "B+")
 * - score: number (0-100)
 * - verdict: string (e.g., "Found validated problems")
 * - strengths: string[] (what they did well)
 * - growth_areas: string[] (where to improve)
 * - evidence_count: number
 * - components: array of score components for expanded view
 * - bot_type: string (e.g., "minto")
 */

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, ArrowRight, TrendingUp, Award, MessageCircle, ChevronDown, ChevronUp, FileText } from 'lucide-react'

export default function GradeReveal() {
  // === CHAINLIT API ACCESS ===
  // Props are injected globally by Chainlit (not as function arguments)
  // window.Chainlit provides: updateElement, callAction, sendUserMessage, deleteElement
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Destructure props with defaults (props is a global in Chainlit custom elements)
  const {
    stage = 'context',
    grade = 'B',
    score = 75,
    verdict = '',
    strengths = [],
    growth_areas = [],
    evidence_count = 0,
    components = [],
    bot_type = 'minto',
    element_id = null
  } = props || {}

  // === HELPERS ===

  // Grade color mapping
  const gradeColors = {
    'A': { bg: 'bg-green-500', text: 'text-green-500', light: 'bg-green-50', ring: 'ring-green-200' },
    'B': { bg: 'bg-blue-500', text: 'text-blue-500', light: 'bg-blue-50', ring: 'ring-blue-200' },
    'C': { bg: 'bg-yellow-500', text: 'text-yellow-500', light: 'bg-yellow-50', ring: 'ring-yellow-200' },
    'D': { bg: 'bg-orange-500', text: 'text-orange-500', light: 'bg-orange-50', ring: 'ring-orange-200' },
    'F': { bg: 'bg-red-500', text: 'text-red-500', light: 'bg-red-50', ring: 'ring-red-200' }
  }

  const gradeKey = grade?.charAt(0) || 'C'
  const colors = gradeColors[gradeKey] || gradeColors['C']

  // === STAGE TRANSITION HANDLER ===
  const goToStage = (newStage) => {
    if (updateElement) {
      updateElement({ ...props, stage: newStage })
    } else {
      console.warn('Chainlit updateElement not available')
    }
  }

  // === ACTION HANDLERS ===
  const handleDiscuss = () => {
    if (callAction) {
      callAction({
        name: 'discuss_grade',
        payload: { grade, score, verdict, bot_type }
      })
    } else if (sendUserMessage) {
      sendUserMessage(`I'd like to discuss my ${grade} grade (${score}/100). ${verdict}`)
    }
  }

  const handleViewEvidence = () => {
    if (callAction) {
      callAction({
        name: 'view_evidence',
        payload: { element_id }
      })
    }
  }

  const handleViewReport = () => {
    if (callAction) {
      callAction({
        name: 'view_full_report',
        payload: { element_id }
      })
    }
  }

  // === STAGE: CONTEXT ===
  // Prepare the user before showing results
  const ContextStage = () => (
    <div className="text-center p-8 space-y-6">
      <div className="text-5xl mb-4">📊</div>
      <h3 className="text-xl font-semibold text-foreground">Assessment Complete</h3>
      <p className="text-muted-foreground">
        I've analyzed your submission using{' '}
        <span className="font-semibold text-foreground">{evidence_count}</span> pieces of evidence
        from Neo4j knowledge graph, FileSearch RAG, and web research.
      </p>
      <div className="text-sm text-muted-foreground">
        Let's walk through your results together...
      </div>
      <Button
        size="lg"
        onClick={() => goToStage('strengths')}
        className="mt-4"
      >
        What did I do well? <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  )

  // === STAGE: STRENGTHS ===
  // Show positives first (soft landing)
  const StrengthsStage = () => (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2 text-green-600 mb-4">
        <CheckCircle className="h-6 w-6" />
        <h3 className="text-lg font-semibold">What You Did Well</h3>
      </div>
      {strengths.length > 0 ? (
        <ul className="space-y-3">
          {strengths.map((s, i) => (
            <li key={i} className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-100 dark:border-green-900">
              <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
              <span className="text-foreground">{s}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground italic">No specific strengths captured.</p>
      )}
      <div className="pt-4">
        <Button
          onClick={() => goToStage('growth')}
          className="w-full"
        >
          Where can I improve? <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  )

  // === STAGE: GROWTH ===
  // Show areas for improvement
  const GrowthStage = () => (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2 text-amber-600 mb-4">
        <TrendingUp className="h-6 w-6" />
        <h3 className="text-lg font-semibold">Growth Opportunities</h3>
      </div>
      {growth_areas.length > 0 ? (
        <ul className="space-y-3">
          {growth_areas.map((g, i) => (
            <li key={i} className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-100 dark:border-amber-900">
              <span className="text-amber-500 mt-0.5 flex-shrink-0">→</span>
              <span className="text-foreground">{g}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground italic">No specific growth areas identified.</p>
      )}
      <div className="pt-4">
        <Button
          onClick={() => goToStage('reveal')}
          className="w-full"
        >
          Show my grade <Award className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  )

  // === STAGE: REVEAL ===
  // The grade reveal moment
  const RevealStage = () => (
    <div className="text-center p-8 space-y-6">
      {/* Grade Circle with animation-ready class */}
      <div
        className={`inline-flex items-center justify-center w-32 h-32 rounded-full ${colors.bg} text-white shadow-lg ring-4 ${colors.ring} transition-transform hover:scale-105`}
      >
        <span className="text-5xl font-bold">{grade}</span>
      </div>

      {/* Score */}
      <div className="space-y-2">
        <div className="text-3xl font-semibold text-foreground">{score}/100</div>
        {verdict && (
          <Badge variant="secondary" className="text-sm px-3 py-1">
            {verdict}
          </Badge>
        )}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3 justify-center pt-4">
        <Button
          variant="outline"
          onClick={() => goToStage('expanded')}
        >
          <ChevronDown className="mr-2 h-4 w-4" />
          See Details
        </Button>
        <Button onClick={handleDiscuss}>
          <MessageCircle className="mr-2 h-4 w-4" />
          Discuss with Lawrence
        </Button>
      </div>
    </div>
  )

  // === STAGE: EXPANDED ===
  // Full breakdown with all details
  const ExpandedStage = () => (
    <div className="p-6 space-y-6">
      {/* Header with grade */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`${colors.bg} text-white text-3xl font-bold rounded-lg px-4 py-2 shadow-md`}>
            {grade}
          </div>
          <div>
            <div className="text-2xl font-semibold text-foreground">{score}/100</div>
            {verdict && <Badge variant="outline">{verdict}</Badge>}
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => goToStage('reveal')}
          title="Collapse details"
        >
          <ChevronUp className="h-4 w-4" />
        </Button>
      </div>

      {/* Component Scores */}
      {components.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
            Score Breakdown
          </h4>
          {components.map((c, i) => (
            <div key={i} className="space-y-1.5">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-foreground">
                  {c.name} <span className="text-muted-foreground">({c.weight}%)</span>
                </span>
                <span className="font-semibold text-foreground">{c.score}/10</span>
              </div>
              <Progress value={c.score * 10} className="h-2" />
              {c.assessment && (
                <p className="text-xs text-muted-foreground pl-1">{c.assessment}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Evidence count */}
      <div className="text-sm text-muted-foreground text-center">
        Based on {evidence_count} pieces of evidence
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3 pt-2">
        <Button
          variant="outline"
          className="flex-1"
          onClick={handleViewEvidence}
        >
          <FileText className="mr-2 h-4 w-4" />
          View Evidence
        </Button>
        <Button
          variant="outline"
          className="flex-1"
          onClick={handleViewReport}
        >
          Download Report
        </Button>
        <Button
          className="flex-1"
          onClick={handleDiscuss}
        >
          <MessageCircle className="mr-2 h-4 w-4" />
          Discuss
        </Button>
      </div>
    </div>
  )

  // === RENDER ===
  const stages = {
    context: <ContextStage />,
    strengths: <StrengthsStage />,
    growth: <GrowthStage />,
    reveal: <RevealStage />,
    expanded: <ExpandedStage />
  }

  return (
    <Card className="w-full max-w-2xl mx-auto overflow-hidden shadow-lg border">
      {stages[stage] || stages.reveal}
    </Card>
  )
}
