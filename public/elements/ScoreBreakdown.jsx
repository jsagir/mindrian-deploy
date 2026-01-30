/**
 * ScoreBreakdown - Interactive Score Drill-Down Component
 *
 * Click any component to see detailed evidence and what's missing
 * "Discuss this score" button triggers Lawrence conversation
 *
 * Props:
 * - components: array of {name, weight, score, assessment, evidence[], missing[]}
 * - selected: number (index of selected component, null for none)
 * - total_score: number
 * - grade: string
 */

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { MessageCircle, ChevronRight, CheckCircle, AlertCircle, Info } from 'lucide-react';

export default function ScoreBreakdown() {
  const {
    components = [],
    selected = null,
    total_score = 0,
    grade = 'B'
  } = props;

  // Score ring component
  const ScoreRing = ({ score, max = 10, size = 48 }) => {
    const percentage = (score / max) * 100;
    const color = percentage >= 70 ? '#22c55e' :
                  percentage >= 50 ? '#eab308' : '#ef4444';
    const circumference = 2 * Math.PI * 18;
    const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" viewBox="0 0 40 40">
          <circle
            cx="20" cy="20" r="18"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="3"
          />
          <circle
            cx="20" cy="20" r="18"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold">{score}</span>
        </div>
      </div>
    );
  };

  // Component list item
  const ComponentItem = ({ component, index, isSelected }) => (
    <button
      onClick={() => updateElement({...props, selected: isSelected ? null : index})}
      className={`w-full p-4 rounded-lg flex items-center justify-between transition-all ${
        isSelected
          ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2'
          : 'bg-muted hover:bg-muted/80'
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
      <ChevronRight className={`h-5 w-5 transition-transform ${isSelected ? 'rotate-90' : ''}`} />
    </button>
  );

  // Detail panel for selected component
  const DetailPanel = ({ component }) => (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold">{component.name}</h3>
          <p className="text-sm text-muted-foreground">{component.weight}% of total grade</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold">{component.score}/10</div>
          <div className="text-sm text-muted-foreground">
            = {(component.score * component.weight / 10).toFixed(1)} points
          </div>
        </div>
      </div>

      {/* Assessment */}
      <p className="text-muted-foreground">{component.assessment}</p>

      {/* Evidence Found */}
      {component.evidence && component.evidence.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-green-600">
            <CheckCircle className="h-4 w-4" />
            Evidence Found ({component.evidence.length})
          </div>
          <div className="space-y-2">
            {component.evidence.map((ev, i) => (
              <div key={i} className="text-sm p-3 bg-green-50 rounded-lg border border-green-100">
                {typeof ev === 'string' ? ev : ev.content || JSON.stringify(ev)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* What's Missing */}
      {component.missing && component.missing.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-amber-600">
            <AlertCircle className="h-4 w-4" />
            What Would Raise This Score
          </div>
          <ul className="space-y-2">
            {component.missing.map((m, i) => (
              <li key={i} className="flex items-start gap-2 text-sm p-3 bg-amber-50 rounded-lg border border-amber-100">
                <span className="text-amber-500 mt-0.5">→</span>
                <span>{m}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Discuss Button */}
      <Button
        className="w-full mt-4"
        onClick={() => callAction({
          name: 'discuss_component',
          payload: { component: component.name, score: component.score }
        })}
      >
        <MessageCircle className="mr-2 h-4 w-4" />
        Discuss This Score with Lawrence
      </Button>
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
      {/* Component List */}
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
            Components
          </h4>
          <Badge variant="outline">{grade} ({total_score})</Badge>
        </div>
        {components.map((c, i) => (
          <ComponentItem
            key={i}
            component={c}
            index={i}
            isSelected={selected === i}
          />
        ))}
      </div>

      {/* Detail Panel */}
      <div className="md:col-span-2">
        <Card className="h-full">
          <CardContent className="p-6">
            {selected !== null && components[selected] ? (
              <DetailPanel component={components[selected]} />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-muted-foreground">
                <Info className="h-12 w-12 mb-4 opacity-50" />
                <p className="text-lg font-medium">Select a component</p>
                <p className="text-sm">Click any score on the left to see detailed evidence and improvement suggestions</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
