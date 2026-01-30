/**
 * FormCard - Template for interactive forms with validation
 *
 * Copy to: public/elements/YourFormName.jsx
 * Usage: cl.CustomElement(name="YourFormName", props={...})
 *
 * Props:
 * - title: string
 * - description: string (optional)
 * - fields: array of field definitions
 * - submitLabel: string
 * - actionName: string - Python action callback name
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, Send, CheckCircle, AlertCircle } from "lucide-react"
import { useState } from "react"

export default function FormCard() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props are global
  const {
    title = "Form",
    description = "",
    fields = [],
    submitLabel = "Submit",
    actionName = "form_submit",
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
    fields.forEach(field => {
      if (field.required && !formData[field.key]) {
        newErrors[field.key] = `${field.label} is required`
      }
      if (field.type === 'email' && formData[field.key]) {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData[field.key])) {
          newErrors[field.key] = 'Invalid email format'
        }
      }
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

  // === FIELD RENDERER ===
  const renderField = (field) => {
    const value = formData[field.key] || ''

    switch (field.type) {
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

  // === SUCCESS STATE ===
  if (submitted) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <Alert className="border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-900">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800 dark:text-green-300">
              Form submitted successfully!
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  // === RENDER ===
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>

      <CardContent className="space-y-4">
        {fields.map(field => (
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

/*
================================================================================
PYTHON USAGE EXAMPLE
================================================================================

import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="FormCard",
            props={
                "title": "Contact Us",
                "description": "We'll get back to you within 24 hours",
                "fields": [
                    {
                        "key": "name",
                        "label": "Full Name",
                        "type": "text",
                        "placeholder": "John Doe",
                        "required": True
                    },
                    {
                        "key": "email",
                        "label": "Email",
                        "type": "email",
                        "placeholder": "john@example.com",
                        "required": True
                    },
                    {
                        "key": "category",
                        "label": "Category",
                        "type": "select",
                        "options": [
                            {"value": "general", "label": "General Inquiry"},
                            {"value": "support", "label": "Technical Support"},
                            {"value": "sales", "label": "Sales"}
                        ]
                    },
                    {
                        "key": "message",
                        "label": "Message",
                        "type": "textarea",
                        "placeholder": "How can we help?",
                        "rows": 4
                    },
                    {
                        "key": "newsletter",
                        "label": "Newsletter",
                        "type": "checkbox",
                        "checkboxLabel": "Subscribe to newsletter"
                    }
                ],
                "submitLabel": "Send Message",
                "actionName": "contact_form"
            },
            display="inline"
        )
    ]
    await cl.Message(content="Please fill out:", elements=elements).send()

@cl.action_callback("contact_form")
async def handle_form(action: cl.Action):
    data = action.payload
    await cl.Message(content=f"Thanks {data.get('name')}!").send()

================================================================================
*/
