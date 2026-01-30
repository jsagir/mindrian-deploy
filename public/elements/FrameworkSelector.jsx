/**
 * FrameworkSelector - Guide users to the right PWS methodology
 *
 * Analyzes context and recommends the best framework/bot for their situation.
 * Uses extracted keywords and conversation patterns.
 *
 * Props (injected globally by Chainlit):
 * - recommendations: array of {id, name, score, reasoning}
 * - context_keywords: array of matched keywords
 * - selected_question: current diagnostic question selected
 * - show_all: boolean to show all frameworks
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
  Compass, Target, TrendingUp, Users, Clock, Shield,
  Lightbulb, ChevronRight, Sparkles, Check, HelpCircle
} from "lucide-react"
import { useState } from "react"

export default function FrameworkSelector() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    recommendations = [],
    context_keywords = [],
    selected_question = null,
    show_all = false,
    element_id = null
  } = props || {}

  // Local state for question selection
  const [selectedQ, setSelectedQ] = useState(selected_question)

  // === DIAGNOSTIC QUESTIONS ===
  const questions = [
    {
      id: "validate",
      text: "I have a solution and need to validate it",
      icon: <Target className="h-5 w-5" />,
      framework: "ackoff",
      description: "Use DIKW Pyramid to validate with data"
    },
    {
      id: "future",
      text: "I'm exploring a trend or future scenario",
      icon: <TrendingUp className="h-5 w-5" />,
      framework: "tta",
      description: "Trending to the Absurd for future exploration"
    },
    {
      id: "customer",
      text: "I want to understand customer needs",
      icon: <Users className="h-5 w-5" />,
      framework: "jtbd",
      description: "Jobs to Be Done for customer insight"
    },
    {
      id: "timing",
      text: "I need to time a technology decision",
      icon: <Clock className="h-5 w-5" />,
      framework: "scurve",
      description: "S-Curve Analysis for timing"
    },
    {
      id: "challenge",
      text: "I want to stress-test my assumptions",
      icon: <Shield className="h-5 w-5" />,
      framework: "redteam",
      description: "Red Team to challenge assumptions"
    },
    {
      id: "stuck",
      text: "I'm stuck and need fresh perspective",
      icon: <Lightbulb className="h-5 w-5" />,
      framework: "bono",
      description: "Six Thinking Hats for new perspectives"
    }
  ]

  // === FRAMEWORK DATA ===
  const frameworkDetails = {
    jtbd: {
      name: "Jobs to Be Done",
      icon: <Users className="h-6 w-6" />,
      color: "text-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-950/30",
      description: "Understand what progress customers are trying to make"
    },
    tta: {
      name: "Trending to the Absurd",
      icon: <TrendingUp className="h-6 w-6" />,
      color: "text-purple-500",
      bgColor: "bg-purple-50 dark:bg-purple-950/30",
      description: "Explore future trends and extreme scenarios"
    },
    scurve: {
      name: "S-Curve Analysis",
      icon: <Clock className="h-6 w-6" />,
      color: "text-green-500",
      bgColor: "bg-green-50 dark:bg-green-950/30",
      description: "Analyze technology timing and market readiness"
    },
    redteam: {
      name: "Red Team",
      icon: <Shield className="h-6 w-6" />,
      color: "text-red-500",
      bgColor: "bg-red-50 dark:bg-red-950/30",
      description: "Stress-test assumptions and find weaknesses"
    },
    ackoff: {
      name: "Ackoff's DIKW Pyramid",
      icon: <Target className="h-6 w-6" />,
      color: "text-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-950/30",
      description: "Validate with data, information, knowledge, wisdom"
    },
    bono: {
      name: "Six Thinking Hats",
      icon: <Lightbulb className="h-6 w-6" />,
      color: "text-cyan-500",
      bgColor: "bg-cyan-50 dark:bg-cyan-950/30",
      description: "Explore multiple perspectives systematically"
    }
  }

  // === HANDLERS ===
  const handleQuestionSelect = (questionId) => {
    setSelectedQ(questionId)
    if (updateElement) {
      updateElement({ ...props, selected_question: questionId })
    }
  }

  const handleStartWorkshop = (frameworkId) => {
    if (callAction) {
      callAction({
        name: `switch_to_${frameworkId}`,
        payload: { from_selector: true }
      })
    } else if (sendUserMessage) {
      const name = frameworkDetails[frameworkId]?.name || frameworkId
      sendUserMessage(`I'd like to use the ${name} framework`)
    }
  }

  const handleShowAll = () => {
    if (updateElement) {
      updateElement({ ...props, show_all: true })
    }
  }

  // Get recommendation from selected question
  const getRecommendation = () => {
    if (selectedQ) {
      const q = questions.find(q => q.id === selectedQ)
      if (q) return q.framework
    }
    // Fall back to AI recommendation
    if (recommendations.length > 0) {
      return recommendations[0].id
    }
    return null
  }

  const recommendedFramework = getRecommendation()

  // === RENDER: ALL FRAMEWORKS VIEW ===
  if (show_all) {
    return (
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Compass className="h-5 w-5" />
            All PWS Frameworks
          </CardTitle>
          <CardDescription>
            Choose the methodology that fits your situation
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {Object.entries(frameworkDetails).map(([id, fw]) => (
            <button
              key={id}
              onClick={() => handleStartWorkshop(id)}
              className={`w-full p-4 rounded-lg border text-left transition-all hover:shadow-md ${fw.bgColor}`}
            >
              <div className="flex items-center gap-3">
                <div className={fw.color}>{fw.icon}</div>
                <div className="flex-1">
                  <div className="font-medium text-foreground">{fw.name}</div>
                  <div className="text-sm text-muted-foreground">{fw.description}</div>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              </div>
            </button>
          ))}
        </CardContent>
        <CardFooter>
          <Button
            variant="outline"
            onClick={() => updateElement && updateElement({ ...props, show_all: false })}
            className="w-full"
          >
            Back to Recommendations
          </Button>
        </CardFooter>
      </Card>
    )
  }

  // === RENDER: DIAGNOSTIC VIEW ===
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Compass className="h-5 w-5 text-primary" />
          Which framework fits your situation?
        </CardTitle>
        {context_keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            <span className="text-xs text-muted-foreground mr-1">Context:</span>
            {context_keywords.slice(0, 5).map((kw, i) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {kw}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Diagnostic Questions */}
        <RadioGroup value={selectedQ || ""} onValueChange={handleQuestionSelect}>
          <div className="space-y-2">
            {questions.map((q) => (
              <div
                key={q.id}
                className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedQ === q.id
                    ? 'border-primary bg-primary/5 ring-1 ring-primary'
                    : 'hover:bg-muted/50'
                }`}
                onClick={() => handleQuestionSelect(q.id)}
              >
                <RadioGroupItem value={q.id} id={q.id} />
                <div className="text-muted-foreground">{q.icon}</div>
                <Label htmlFor={q.id} className="flex-1 cursor-pointer font-normal">
                  {q.text}
                </Label>
                {selectedQ === q.id && (
                  <Check className="h-4 w-4 text-primary" />
                )}
              </div>
            ))}
          </div>
        </RadioGroup>

        {/* Recommendation Box */}
        {recommendedFramework && frameworkDetails[recommendedFramework] && (
          <div className={`p-4 rounded-lg border-2 border-primary/50 ${frameworkDetails[recommendedFramework].bgColor}`}>
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-primary mt-0.5" />
              <div className="flex-1">
                <div className="font-medium text-foreground flex items-center gap-2">
                  Recommended: {frameworkDetails[recommendedFramework].name}
                  {recommendations.length > 0 && (
                    <Badge variant="outline" className="text-xs">
                      {Math.round((recommendations[0]?.score || 0.7) * 100)}% match
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  {frameworkDetails[recommendedFramework].description}
                </p>
                {recommendations[0]?.reasoning && (
                  <p className="text-xs text-muted-foreground mt-2 italic">
                    {recommendations[0].reasoning}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Alternative Recommendations */}
        {recommendations.length > 1 && (
          <div className="text-sm text-muted-foreground">
            <span className="font-medium">Also consider: </span>
            {recommendations.slice(1, 3).map((r, i) => (
              <span key={i}>
                {i > 0 && ", "}
                <button
                  className="text-primary hover:underline"
                  onClick={() => handleStartWorkshop(r.id)}
                >
                  {frameworkDetails[r.id]?.name || r.name}
                </button>
              </span>
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2">
        {recommendedFramework && (
          <Button
            onClick={() => handleStartWorkshop(recommendedFramework)}
            className="flex-1"
          >
            Start {frameworkDetails[recommendedFramework]?.name || recommendedFramework}
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
        <Button variant="outline" onClick={handleShowAll}>
          <HelpCircle className="h-4 w-4 mr-1" />
          See All
        </Button>
      </CardFooter>
    </Card>
  )
}
