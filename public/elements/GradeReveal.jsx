/**
 * GradeReveal - Soft Landing Grade Reveal Component
 *
 * Staged emotional reveal: context → strengths → growth → grade
 * Prevents grade shock, improves reception of feedback
 *
 * Props:
 * - stage: 'context' | 'strengths' | 'growth' | 'reveal' | 'expanded'
 * - grade: string (e.g., "B+")
 * - score: number (0-100)
 * - verdict: string (e.g., "Found validated problems")
 * - strengths: string[] (what they did well)
 * - growth_areas: string[] (where to improve)
 * - evidence_count: number
 * - components: array of score components for expanded view
 */

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, ArrowRight, TrendingUp, Award, MessageCircle, ChevronDown, ChevronUp } from 'lucide-react';

export default function GradeReveal() {
  const {
    stage = 'context',
    grade = 'B',
    score = 75,
    verdict = '',
    strengths = [],
    growth_areas = [],
    evidence_count = 0,
    components = [],
    bot_type = 'minto'
  } = props;

  // Grade color mapping
  const gradeColors = {
    'A': { bg: 'bg-green-500', text: 'text-green-500', light: 'bg-green-50' },
    'B': { bg: 'bg-blue-500', text: 'text-blue-500', light: 'bg-blue-50' },
    'C': { bg: 'bg-yellow-500', text: 'text-yellow-500', light: 'bg-yellow-50' },
    'D': { bg: 'bg-orange-500', text: 'text-orange-500', light: 'bg-orange-50' },
    'F': { bg: 'bg-red-500', text: 'text-red-500', light: 'bg-red-50' }
  };

  const gradeKey = grade.charAt(0);
  const colors = gradeColors[gradeKey] || gradeColors['C'];

  // Stage: Context - Prepare the user
  const ContextStage = () => (
    <div className="text-center p-8 space-y-6">
      <div className="text-5xl mb-4">📊</div>
      <h3 className="text-xl font-semibold">Assessment Complete</h3>
      <p className="text-muted-foreground">
        I've analyzed your submission using <span className="font-semibold">{evidence_count}</span> pieces of evidence
        from Neo4j, FileSearch, and web research...
      </p>
      <Button
        size="lg"
        onClick={() => updateElement({...props, stage: 'strengths'})}
        className="mt-4"
      >
        What did I do well? <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );

  // Stage: Strengths - Show positives first
  const StrengthsStage = () => (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2 text-green-600 mb-4">
        <CheckCircle className="h-6 w-6" />
        <h3 className="text-lg font-semibold">What You Did Well</h3>
      </div>
      <ul className="space-y-3">
        {strengths.map((s, i) => (
          <li key={i} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
            <span className="text-green-500 mt-0.5">✓</span>
            <span>{s}</span>
          </li>
        ))}
      </ul>
      <div className="pt-4">
        <Button
          onClick={() => updateElement({...props, stage: 'growth'})}
          className="w-full"
        >
          Where can I improve? <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );

  // Stage: Growth - Show areas for improvement
  const GrowthStage = () => (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2 text-amber-600 mb-4">
        <TrendingUp className="h-6 w-6" />
        <h3 className="text-lg font-semibold">Growth Opportunities</h3>
      </div>
      <ul className="space-y-3">
        {growth_areas.map((g, i) => (
          <li key={i} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
            <span className="text-amber-500 mt-0.5">→</span>
            <span>{g}</span>
          </li>
        ))}
      </ul>
      <div className="pt-4">
        <Button
          onClick={() => updateElement({...props, stage: 'reveal'})}
          className="w-full"
        >
          Show my grade <Award className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );

  // Stage: Reveal - The grade
  const RevealStage = () => (
    <div className="text-center p-8 space-y-6">
      {/* Grade Circle */}
      <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full ${colors.bg} text-white`}>
        <span className="text-5xl font-bold">{grade}</span>
      </div>

      {/* Score */}
      <div className="space-y-2">
        <div className="text-3xl font-semibold">{score}/100</div>
        <Badge variant="secondary" className="text-sm">{verdict}</Badge>
      </div>

      {/* Actions */}
      <div className="flex gap-3 justify-center pt-4">
        <Button
          variant="outline"
          onClick={() => updateElement({...props, stage: 'expanded'})}
        >
          <ChevronDown className="mr-2 h-4 w-4" />
          See Details
        </Button>
        <Button
          onClick={() => callAction({name: 'discuss_grade', payload: {bot_type}})}
        >
          <MessageCircle className="mr-2 h-4 w-4" />
          Discuss with Lawrence
        </Button>
      </div>
    </div>
  );

  // Stage: Expanded - Full breakdown
  const ExpandedStage = () => (
    <div className="p-6 space-y-6">
      {/* Header with grade */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`${colors.bg} text-white text-3xl font-bold rounded-lg px-4 py-2`}>
            {grade}
          </div>
          <div>
            <div className="text-2xl font-semibold">{score}/100</div>
            <Badge variant="outline">{verdict}</Badge>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => updateElement({...props, stage: 'reveal'})}
        >
          <ChevronUp className="h-4 w-4" />
        </Button>
      </div>

      {/* Component Scores */}
      <div className="space-y-3">
        <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
          Score Breakdown
        </h4>
        {components.map((c, i) => (
          <div key={i} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="font-medium">{c.name} ({c.weight}%)</span>
              <span className="font-semibold">{c.score}/10</span>
            </div>
            <Progress value={c.score * 10} className="h-2" />
            {c.assessment && (
              <p className="text-xs text-muted-foreground">{c.assessment}</p>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => callAction({name: 'view_evidence', payload: {}})}
        >
          View Evidence
        </Button>
        <Button
          className="flex-1"
          onClick={() => callAction({name: 'discuss_grade', payload: {bot_type}})}
        >
          <MessageCircle className="mr-2 h-4 w-4" />
          Discuss
        </Button>
      </div>
    </div>
  );

  // Render based on stage
  const stages = {
    context: <ContextStage />,
    strengths: <StrengthsStage />,
    growth: <GrowthStage />,
    reveal: <RevealStage />,
    expanded: <ExpandedStage />
  };

  return (
    <Card className="w-full max-w-2xl mx-auto overflow-hidden shadow-lg">
      {stages[stage] || stages.reveal}
    </Card>
  );
}
