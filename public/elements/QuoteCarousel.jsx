/**
 * QuoteCarousel - Display customer quotes and research insights
 *
 * Showcases quotes in carousel or grid format with attribution,
 * context, and actions for deeper exploration.
 *
 * Props (injected globally by Chainlit):
 * - quotes: array of {text, attribution, source, context, category, timestamp}
 * - title: optional header text
 * - layout: 'carousel' | 'grid' | 'list'
 * - autoplay: boolean for carousel auto-advance
 * - show_attribution: boolean to show quote sources
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Quote, ChevronLeft, ChevronRight, Play, Pause,
  User, Building, FileText, ExternalLink, BookmarkPlus,
  MessageSquare, Sparkles, Grid3X3, List, LayoutGrid
} from "lucide-react"
import { useState, useEffect, useCallback } from "react"

export default function QuoteCarousel() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults
  const {
    quotes = [],
    title = "Key Quotes",
    layout = "carousel",
    autoplay = false,
    show_attribution = true,
    autoplay_interval = 5000,
    element_id = null
  } = props || {}

  // Local state
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(autoplay)
  const [currentLayout, setCurrentLayout] = useState(layout)
  const [savedQuotes, setSavedQuotes] = useState([])

  // === CATEGORY CONFIGURATION ===
  const categoryConfig = {
    customer: {
      icon: <User className="h-4 w-4" />,
      color: "text-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-950/30",
      label: "Customer"
    },
    expert: {
      icon: <Sparkles className="h-4 w-4" />,
      color: "text-purple-500",
      bgColor: "bg-purple-50 dark:bg-purple-950/30",
      label: "Expert"
    },
    research: {
      icon: <FileText className="h-4 w-4" />,
      color: "text-green-500",
      bgColor: "bg-green-50 dark:bg-green-950/30",
      label: "Research"
    },
    competitor: {
      icon: <Building className="h-4 w-4" />,
      color: "text-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-950/30",
      label: "Competitor"
    },
    internal: {
      icon: <MessageSquare className="h-4 w-4" />,
      color: "text-cyan-500",
      bgColor: "bg-cyan-50 dark:bg-cyan-950/30",
      label: "Internal"
    }
  }

  // === AUTOPLAY ===
  useEffect(() => {
    if (!isPlaying || currentLayout !== "carousel" || quotes.length <= 1) return

    const timer = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % quotes.length)
    }, autoplay_interval)

    return () => clearInterval(timer)
  }, [isPlaying, currentLayout, quotes.length, autoplay_interval])

  // === HANDLERS ===
  const goToNext = useCallback(() => {
    setCurrentIndex(prev => (prev + 1) % quotes.length)
  }, [quotes.length])

  const goToPrev = useCallback(() => {
    setCurrentIndex(prev => (prev - 1 + quotes.length) % quotes.length)
  }, [quotes.length])

  const goToIndex = (index) => {
    setCurrentIndex(index)
    setIsPlaying(false)
  }

  const togglePlay = () => {
    setIsPlaying(prev => !prev)
  }

  const handleSave = (quote, index) => {
    setSavedQuotes(prev => [...prev, index])
    if (callAction) {
      callAction({
        name: "save_quote",
        payload: { quote, index }
      })
    }
  }

  const handleExplore = (quote) => {
    if (callAction) {
      callAction({
        name: "explore_quote",
        payload: { quote }
      })
    } else if (sendUserMessage) {
      sendUserMessage(`Tell me more about this quote: "${quote.text}"`)
    }
  }

  const handleLayoutChange = (newLayout) => {
    setCurrentLayout(newLayout)
    setIsPlaying(false)
    if (updateElement) {
      updateElement({ ...props, layout: newLayout })
    }
  }

  // === RENDER SINGLE QUOTE ===
  const renderQuote = (quote, index, isActive = true) => {
    const category = quote.category || "customer"
    const config = categoryConfig[category] || categoryConfig.customer
    const isSaved = savedQuotes.includes(index)

    return (
      <div
        key={index}
        className={`p-5 rounded-lg border transition-all ${config.bgColor} ${
          isActive ? "border-primary/50" : "border-border/50"
        }`}
      >
        {/* Quote Icon */}
        <div className="flex justify-between items-start mb-3">
          <Quote className={`h-8 w-8 ${config.color} opacity-50`} />
          <Badge variant="outline" className="text-xs flex items-center gap-1">
            {config.icon}
            {config.label}
          </Badge>
        </div>

        {/* Quote Text */}
        <blockquote className="text-base font-medium text-foreground leading-relaxed mb-4 italic">
          "{quote.text}"
        </blockquote>

        {/* Attribution */}
        {show_attribution && quote.attribution && (
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
              <User className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <div className="text-sm font-medium">{quote.attribution}</div>
              {quote.source && (
                <div className="text-xs text-muted-foreground">{quote.source}</div>
              )}
            </div>
          </div>
        )}

        {/* Context */}
        {quote.context && (
          <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded mb-3">
            <span className="font-medium">Context: </span>
            {quote.context}
          </div>
        )}

        {/* Timestamp */}
        {quote.timestamp && (
          <div className="text-xs text-muted-foreground mb-3">
            {quote.timestamp}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={() => handleExplore(quote)}
          >
            <Sparkles className="h-3 w-3 mr-1" />
            Explore
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className={`h-7 text-xs ${isSaved ? "text-green-600" : ""}`}
            onClick={() => handleSave(quote, index)}
            disabled={isSaved}
          >
            <BookmarkPlus className="h-3 w-3 mr-1" />
            {isSaved ? "Saved" : "Save"}
          </Button>
          {quote.source_url && (
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => window.open(quote.source_url, "_blank")}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              Source
            </Button>
          )}
        </div>
      </div>
    )
  }

  // === EMPTY STATE ===
  if (quotes.length === 0) {
    return (
      <Card className="w-full max-w-lg">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <Quote className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No quotes collected yet.</p>
            <p className="text-xs mt-1">Quotes will be extracted from conversation and research.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // === CAROUSEL LAYOUT ===
  const renderCarousel = () => (
    <div className="relative">
      {/* Main Quote */}
      {renderQuote(quotes[currentIndex], currentIndex)}

      {/* Navigation */}
      {quotes.length > 1 && (
        <>
          {/* Arrows */}
          <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 flex justify-between pointer-events-none">
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 -ml-4 pointer-events-auto bg-background/80 backdrop-blur"
              onClick={goToPrev}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 -mr-4 pointer-events-auto bg-background/80 backdrop-blur"
              onClick={goToNext}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Dots */}
          <div className="flex justify-center gap-2 mt-4">
            {quotes.map((_, i) => (
              <button
                key={i}
                onClick={() => goToIndex(i)}
                className={`w-2 h-2 rounded-full transition-all ${
                  i === currentIndex
                    ? "bg-primary w-4"
                    : "bg-muted hover:bg-muted-foreground/50"
                }`}
              />
            ))}
          </div>

          {/* Play/Pause */}
          <div className="flex justify-center mt-2">
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={togglePlay}
            >
              {isPlaying ? (
                <>
                  <Pause className="h-3 w-3 mr-1" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="h-3 w-3 mr-1" />
                  Auto-play
                </>
              )}
            </Button>
          </div>
        </>
      )}
    </div>
  )

  // === GRID LAYOUT ===
  const renderGrid = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {quotes.map((quote, index) => renderQuote(quote, index, false))}
    </div>
  )

  // === LIST LAYOUT ===
  const renderList = () => (
    <ScrollArea className="h-[400px]">
      <div className="space-y-3 pr-2">
        {quotes.map((quote, index) => renderQuote(quote, index, false))}
      </div>
    </ScrollArea>
  )

  // === RENDER ===
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Quote className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {quotes.length} quote{quotes.length !== 1 ? 's' : ''}
            </Badge>
          </div>
        </div>
        <CardDescription>
          Important quotes from research and conversations
        </CardDescription>

        {/* Layout Switcher */}
        <div className="flex gap-1 mt-2">
          <Button
            size="sm"
            variant={currentLayout === "carousel" ? "secondary" : "ghost"}
            className="h-7 px-2"
            onClick={() => handleLayoutChange("carousel")}
          >
            <LayoutGrid className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            variant={currentLayout === "grid" ? "secondary" : "ghost"}
            className="h-7 px-2"
            onClick={() => handleLayoutChange("grid")}
          >
            <Grid3X3 className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            variant={currentLayout === "list" ? "secondary" : "ghost"}
            className="h-7 px-2"
            onClick={() => handleLayoutChange("list")}
          >
            <List className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {currentLayout === "carousel" && renderCarousel()}
        {currentLayout === "grid" && renderGrid()}
        {currentLayout === "list" && renderList()}
      </CardContent>

      <CardFooter>
        <Button
          variant="outline"
          className="w-full"
          onClick={() => callAction && callAction({ name: "find_more_quotes", payload: {} })}
        >
          <MessageSquare className="h-4 w-4 mr-1" />
          Find More Quotes
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
    # Process message for quotes
    context.process_message(message.content, "user")

    # Get AI response...
    context.process_message(ai_response, "assistant")

    # Generate quote carousel props
    quote_props = context.to_props("QuoteCarousel")

    elements = [
        cl.CustomElement(
            name="QuoteCarousel",
            props=quote_props,
            display="inline"
        )
    ]
    await cl.Message(content="Key quotes:", elements=elements).send()

# Or with manual props:
elements = [
    cl.CustomElement(
        name="QuoteCarousel",
        props={
            "title": "Customer Insights",
            "layout": "carousel",
            "autoplay": True,
            "autoplay_interval": 5000,
            "show_attribution": True,
            "quotes": [
                {
                    "text": "I don't want more features, I want the current ones to work reliably",
                    "attribution": "Sarah Chen",
                    "source": "Product Manager, TechCorp",
                    "category": "customer",
                    "context": "User interview about product complexity",
                    "timestamp": "Jan 28, 2026"
                },
                {
                    "text": "The market will shift to AI-first solutions within 18 months",
                    "attribution": "Industry Report",
                    "source": "Gartner 2026",
                    "category": "research",
                    "source_url": "https://example.com/report"
                },
                {
                    "text": "Our biggest fear is that a startup will move faster than us",
                    "attribution": "Anonymous Executive",
                    "source": "Fortune 500 Company",
                    "category": "competitor"
                },
                {
                    "text": "Users spend 60% of their time on data prep, not analysis",
                    "attribution": "Dr. Jane Smith",
                    "source": "MIT Research",
                    "category": "expert"
                }
            ]
        },
        display="inline"
    )
]

@cl.action_callback("save_quote")
async def handle_save(action: cl.Action):
    quote = action.payload.get("quote")
    await cl.Message(content=f"Quote saved: '{quote['text'][:50]}...'").send()

@cl.action_callback("explore_quote")
async def handle_explore(action: cl.Action):
    quote = action.payload.get("quote")
    await cl.Message(content=f"Let's explore this insight: '{quote['text']}'").send()

@cl.action_callback("find_more_quotes")
async def handle_find_more(action: cl.Action):
    await cl.Message(content="Searching for more relevant quotes...").send()

================================================================================
*/
