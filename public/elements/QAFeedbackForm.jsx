/**
 * QAFeedbackForm - Interactive QA feedback form for testers
 *
 * Features:
 * - Star rating widget (1-5 clickable stars)
 * - Section grouping with headers
 * - Conditional section visibility
 * - Session metadata display
 * - Based on FormCard.jsx template pattern
 *
 * Usage: cl.CustomElement(name="QAFeedbackForm", props={...})
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Loader2, Send, CheckCircle, AlertCircle, Star, Info } from "lucide-react"
import { useState } from "react"

export default function QAFeedbackForm() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props are global
  const {
    title = "QA Feedback",
    description = "",
    sessionInfo = {},
    sections = [],
    submitLabel = "Submit Feedback",
    actionName = "qa_feedback_submit",
    element_id = null
  } = props || {}

  // === LOCAL STATE ===
  const [formData, setFormData] = useState({})
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // === HANDLERS ===
  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }))
    if (errors[key]) {
      setErrors(prev => ({ ...prev, [key]: null }))
    }
  }

  const validate = () => {
    const newErrors = {}
    sections.forEach(section => {
      if (!section.visible) return
      (section.fields || []).forEach(field => {
        if (field.required && !formData[field.key]) {
          newErrors[field.key] = `${field.label} is required`
        }
      })
    })
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setLoading(true)
    if (callAction) {
      await callAction({ name: actionName, payload: formData })
    }
    setLoading(false)
    setSubmitted(true)
  }

  // === STAR RATING COMPONENT ===
  const StarRating = ({ fieldKey, value = 0 }) => {
    const [hovered, setHovered] = useState(0)
    const currentValue = formData[fieldKey] || value

    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map(star => (
          <button
            key={star}
            type="button"
            className="p-0.5 transition-transform hover:scale-110 focus:outline-none"
            onMouseEnter={() => setHovered(star)}
            onMouseLeave={() => setHovered(0)}
            onClick={() => handleChange(fieldKey, star)}
          >
            <Star
              className={`h-6 w-6 transition-colors ${
                star <= (hovered || currentValue)
                  ? "fill-yellow-400 text-yellow-400"
                  : "fill-none text-muted-foreground/40"
              }`}
            />
          </button>
        ))}
        {currentValue > 0 && (
          <span className="ml-2 text-sm text-muted-foreground">{currentValue}/5</span>
        )}
      </div>
    )
  }

  // === FIELD RENDERER ===
  const renderField = (field) => {
    const value = formData[field.key] || ''

    switch (field.type) {
      case 'rating':
        return <StarRating fieldKey={field.key} />

      case 'textarea':
        return (
          <Textarea
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleChange(field.key, e.target.value)}
            rows={field.rows || 3}
          />
        )

      case 'select':
        return (
          <Select onValueChange={(v) => handleChange(field.key, v)} value={value}>
            <SelectTrigger>
              <SelectValue placeholder={field.placeholder || 'Select...'} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map(opt => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id={field.key}
              checked={value === true}
              onCheckedChange={(checked) => handleChange(field.key, checked)}
            />
            <Label htmlFor={field.key} className="text-sm font-normal">
              {field.checkboxLabel || field.label}
            </Label>
          </div>
        )

      default:
        return (
          <Input
            type={field.type || 'text'}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleChange(field.key, e.target.value)}
          />
        )
    }
  }

  // === SESSION INFO BAR ===
  const SessionInfoBar = () => {
    if (!sessionInfo || Object.keys(sessionInfo).length === 0) return null

    return (
      <div className="rounded-lg border bg-muted/50 p-3 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Info className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Session Info</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {sessionInfo.agent && (
            <Badge variant="secondary">{sessionInfo.agent}</Badge>
          )}
          {sessionInfo.phases_completed != null && sessionInfo.total_phases != null && (
            <Badge variant="outline">
              Phases: {sessionInfo.phases_completed}/{sessionInfo.total_phases}
            </Badge>
          )}
          {sessionInfo.turn_count != null && (
            <Badge variant="outline">
              Turns: {sessionInfo.turn_count}
            </Badge>
          )}
          {sessionInfo.orchestration_seen && (
            <Badge variant="default" className="bg-purple-600">Orchestration Used</Badge>
          )}
          {sessionInfo.features_used && sessionInfo.features_used.length > 0 && (
            sessionInfo.features_used.map(feature => (
              <Badge key={feature} variant="outline" className="text-xs">
                {feature}
              </Badge>
            ))
          )}
        </div>
      </div>
    )
  }

  // === SUCCESS STATE ===
  if (submitted) {
    return (
      <Card className="w-full max-w-lg">
        <CardContent className="pt-6">
          <Alert className="border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-900">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800 dark:text-green-300">
              Thank you for your feedback! Your responses have been recorded.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  // === RENDER ===
  const visibleSections = sections.filter(s => s.visible !== false)

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>

      <CardContent className="space-y-6">
        <SessionInfoBar />

        {visibleSections.map((section, sectionIdx) => (
          <div key={sectionIdx}>
            {sectionIdx > 0 && <Separator className="mb-4" />}
            <h3 className="text-sm font-semibold mb-3 text-foreground/80">
              {section.title}
            </h3>
            <div className="space-y-4">
              {(section.fields || []).map(field => (
                field.type !== 'checkbox' ? (
                  <div key={field.key} className="space-y-2">
                    <Label htmlFor={field.key}>
                      {field.label}
                      {field.required && <span className="text-destructive ml-1">*</span>}
                    </Label>
                    {renderField(field)}
                    {errors[field.key] && (
                      <p className="text-sm text-destructive flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        {errors[field.key]}
                      </p>
                    )}
                  </div>
                ) : (
                  <div key={field.key}>
                    {renderField(field)}
                    {errors[field.key] && (
                      <p className="text-sm text-destructive">{errors[field.key]}</p>
                    )}
                  </div>
                )
              ))}
            </div>
          </div>
        ))}
      </CardContent>

      <CardFooter>
        <Button onClick={handleSubmit} disabled={loading} className="w-full">
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Send className="h-4 w-4 mr-2" />
          )}
          {submitLabel}
        </Button>
      </CardFooter>
    </Card>
  )
}
